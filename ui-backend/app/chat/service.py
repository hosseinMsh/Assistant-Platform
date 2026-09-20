"""Chat service — the core business logic layer.

State machine for tool execution:
  pending → confirmed → executing → success | failed
  pending → cancelled

Real-time transparency:
  At each stage, a ProcessingStatusEvent is sent via WebSocket so the UI
  can display exactly what is happening while the user waits.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent import agent as llm_agent
from app.auth.session import (
    atomic_claim_confirmation,
    create_confirmation,
    delete_confirmation,
    get_confirmation,
)
from app.core.logging import get_request_id
from app.gateway import client as gateway_client
from app.models.models import Conversation, Message, ToolExecution
from app.schemas.chat import (
    ChatRequest,
    ConfirmationRequiredResponse,
    MessageResponse,
    ToolResultResponse,
)
from app.ws.events import (
    AssistantResponseCreatedEvent,
    ConfirmationCompletedEvent,
    ConfirmationCreatedEvent,
    ErrorEvent,
    MessageCreatedEvent,
    ProcessingStatusEvent,
    ToolExecutionCreatedEvent,
    ToolExecutionUpdatedEvent,
)
from app.ws.manager import manager as ws_manager

logger = logging.getLogger(__name__)

# ── Processing status labels (Persian) ────────────────────────────────────────

STAGE_LABELS: dict[str, str] = {
    "thinking":      "در حال پردازش درخواست…",
    "fetching_tools": "دریافت ابزارهای موجود…",
    "calling_llm":   "ارتباط با هوش مصنوعی…",
    "tool_selected": "ابزار انتخاب شد",
    "confirming":    "در انتظار تأیید کاربر…",
    "executing":     "در حال اجرای عملیات…",
    "done":          "عملیات انجام شد",
    "error":         "خطا در پردازش",
}


async def _emit_status(
    session_id: str,
    conversation_id: str,
    stage: str,
    detail: str | None = None,
) -> None:
    """Send a real-time processing status update to the client."""
    await ws_manager.send_event(
        session_id,
        ProcessingStatusEvent(
            conversation_id=conversation_id,
            stage=stage,
            label=STAGE_LABELS.get(stage, stage),
            detail=detail,
        ),
    )


# ── Conversation helpers ───────────────────────────────────────────────────────

async def _get_or_create_conversation(
    db: AsyncSession,
    session_id: str,
    conversation_id: uuid.UUID | None,
) -> Conversation:
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.session_id == session_id,
            )
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv

    conv = Conversation(session_id=session_id)
    db.add(conv)
    await db.flush()
    logger.info("conversation_created id=%s session=%s", conv.id, session_id[:8])
    return conv


async def _touch_conversation(db: AsyncSession, conversation_id: uuid.UUID) -> None:
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(updated_at=datetime.now(timezone.utc))
    )


async def _load_history(
    db: AsyncSession, conversation_id: uuid.UUID
) -> list[dict[str, str]]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    msgs = list(reversed(result.scalars().all()))
    return [{"role": m.role, "content": m.content} for m in msgs]


def _make_title(text: str) -> str:
    clean = text.strip()
    return clean[:60] + ("…" if len(clean) > 60 else "")


# ── Preview builder — generic, tool-agnostic ──────────────────────────────────

def _build_preview(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Build a generic preview dict from any tool call arguments.

    This is intentionally tool-agnostic: it returns whatever fields are in
    `arguments` plus tool metadata, so the UI preview card can render any
    future tool without backend changes.
    """
    return {
        "tool": tool_name,
        "tool_label": tool_name.replace(".", " › ").replace("_", " "),
        "arguments": arguments,
        # Flatten top-level scalar fields for easy display in UI
        **{k: v for k, v in arguments.items() if isinstance(v, (str, int, float, bool))},
    }


def _build_action_title(tool_name: str) -> str:
    """Human-readable title for the confirmation dialog."""
    # Extensible: add more tool → title mappings here
    titles: dict[str, str] = {
        "notify.send_one": "تأیید ارسال اعلان",
        "notify.send_bulk": "تأیید ارسال اعلان گروهی",
        "email.send": "تأیید ارسال ایمیل",
        "calendar.create_event": "تأیید ایجاد رویداد",
        "document.publish": "تأیید انتشار سند",
    }
    # Fallback: derive from tool name
    return titles.get(tool_name, f"تأیید عملیات: {tool_name.split('.')[-1].replace('_', ' ')}")


# ── Main chat handler ──────────────────────────────────────────────────────────

async def handle_chat(
    request: ChatRequest,
    session_id: str,
    access_token: str,
    db: AsyncSession,
) -> MessageResponse | ConfirmationRequiredResponse:
    request_id = get_request_id()
    logger.info(
        "chat_request request_id=%s session=%s conv=%s",
        request_id, session_id[:8], request.conversation_id,
    )

    conv = await _get_or_create_conversation(db, session_id, request.conversation_id)
    conv_id_str = str(conv.id)

    # Stage 1: thinking
    await _emit_status(session_id, conv_id_str, "thinking")

    if conv.title is None:
        conv.title = _make_title(request.message)
        await db.flush()

    history = await _load_history(db, conv.id)

    # Persist user message
    user_msg = Message(conversation_id=conv.id, role="user", content=request.message)
    db.add(user_msg)
    await db.flush()
    await _touch_conversation(db, conv.id)

    # Broadcast user message via WS
    await ws_manager.send_event(
        session_id,
        MessageCreatedEvent(
            conversation_id=conv_id_str,
            message_id=str(user_msg.id),
            role="user",
            content=request.message,
        ),
    )

    # Stage 2: fetching tools
    await _emit_status(session_id, conv_id_str, "fetching_tools")
    logger.info("fetching_tools request_id=%s", request_id)
    tools = await gateway_client.get_tools(access_token)
    if not tools:
        logger.warning("no_tools_available request_id=%s", request_id)

    # Stage 3: calling LLM
    await _emit_status(session_id, conv_id_str, "calling_llm")
    logger.info("agent_processing request_id=%s conv=%s", request_id, conv.id)

    try:
        agent_resp = await llm_agent.run(request.message, history, tools)
    except Exception as exc:
        logger.error("agent_failed request_id=%s error=%s", request_id, type(exc).__name__)
        await _emit_status(session_id, conv_id_str, "error")
        await ws_manager.send_event(session_id, ErrorEvent(
            code="AGENT_ERROR",
            message="خطا در پردازش درخواست",
            conversation_id=conv_id_str,
        ))
        raise

    # ── Plain text response ───────────────────────────────────────────────────
    if not agent_resp.needs_tool:
        text = agent_resp.text or ""
        assistant_msg = Message(conversation_id=conv.id, role="assistant", content=text)
        db.add(assistant_msg)
        await db.flush()
        await _touch_conversation(db, conv.id)

        await ws_manager.send_event(
            session_id,
            AssistantResponseCreatedEvent(
                conversation_id=conv_id_str,
                message_id=str(assistant_msg.id),
                content=text,
            ),
        )
        await _emit_status(session_id, conv_id_str, "done")
        logger.info("agent_text_response request_id=%s conv=%s", request_id, conv.id)
        return MessageResponse(conversation_id=conv.id, message=text)

    # ── Tool call path ────────────────────────────────────────────────────────
    tool_call = agent_resp.tool_call
    tool_name: str = tool_call["tool"]        # type: ignore[index]
    arguments: dict[str, Any] = tool_call.get("arguments", {})  # type: ignore[index]

    # Fallback for lookup: if arguments are empty, use user message as keyword
    if tool_name == "university_knowledge_lookup" and not arguments:
        arguments = {"keyword": request.message, "domain": "university"}
    elif tool_name == "university_knowledge_lookup" and not arguments.get("keyword"):
        if request.message:
            arguments["keyword"] = request.message

    # Stage 4: tool selected
    await _emit_status(session_id, conv_id_str, "tool_selected", detail=tool_name)
    logger.info("tool_selected request_id=%s tool=%s conv=%s", request_id, tool_name, conv.id)

    # Check if tool requires confirmation
    tool_info = next((t for t in tools if t.get("name") == tool_name), None)
    requires_confirm = bool(tool_info.get("requires_confirmation", False)) if tool_info else False

    # Create DB execution record (pending or confirmed directly)
    execution = ToolExecution(
        conversation_id=conv.id,
        tool_name=tool_name,
        arguments=json.dumps(arguments),
        status="pending" if requires_confirm else "confirmed",
        request_id=request_id,
    )
    db.add(execution)
    await db.flush()

    # If no confirmation needed, execute directly
    if not requires_confirm:
        execution.confirmation_id = None
        await db.flush()
        await _touch_conversation(db, conv.id)

        await ws_manager.send_event(
            session_id,
            ToolExecutionCreatedEvent(
                conversation_id=conv_id_str,
                execution_id=str(execution.id),
                tool=tool_name,
                status="confirmed",
            ),
        )
        await _emit_status(session_id, conv_id_str, "executing", detail=tool_name)

        # Direct execution via gateway
        t0 = time.monotonic()
        result = await gateway_client.call_tool(tool_name, arguments, access_token)
        duration_ms = (time.monotonic() - t0) * 1000
        status_code = result["status_code"]
        body = result["body"]
        finished_at = datetime.now(timezone.utc)

        if status_code == 200 and body.get("success"):
            await db.execute(
                update(ToolExecution)
                .where(ToolExecution.id == execution.id)
                .values(
                    status="success",
                    result=json.dumps(body),
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                )
            )
            await db.flush()
            await ws_manager.send_event(
                session_id,
                ToolExecutionUpdatedEvent(
                    conversation_id=conv_id_str,
                    execution_id=str(execution.id),
                    status="success",
                    duration_ms=duration_ms,
                ),
            )
            await _emit_status(session_id, conv_id_str, "done")
            return ToolResultResponse(success=True, message="عملیات با موفقیت انجام شد.")

        # Failure path for direct execution
        error_msg = body.get("error", {}).get("message", "عملیات ناموفق بود")
        error_code = body.get("error", {}).get("code", "UNKNOWN_ERROR")
        await db.execute(
            update(ToolExecution)
            .where(ToolExecution.id == execution.id)
            .values(
                status="failed",
                error=json.dumps({"code": error_code, "message": error_msg}),
                finished_at=finished_at,
                duration_ms=duration_ms,
            )
        )
        await db.flush()
        await ws_manager.send_event(
            session_id,
            ToolExecutionUpdatedEvent(
                conversation_id=conv_id_str,
                execution_id=str(execution.id),
                status="failed",
                error=error_msg,
                duration_ms=duration_ms,
            ),
        )
        await _emit_status(session_id, conv_id_str, "error")
        return ToolResultResponse(success=False, message=error_msg)

    # Create confirmation in Redis
    confirmation_id = await create_confirmation(
        session_id=session_id,
        tool=tool_name,
        arguments=arguments,
        execution_id=str(execution.id),
        conversation_id=conv_id_str,
    )

    execution.confirmation_id = confirmation_id
    await db.flush()
    await _touch_conversation(db, conv.id)

    # Build generic preview and action title
    preview = _build_preview(tool_name, arguments)
    action_title = _build_action_title(tool_name)

    # Broadcast events
    await ws_manager.send_event(
        session_id,
        ToolExecutionCreatedEvent(
            conversation_id=conv_id_str,
            execution_id=str(execution.id),
            tool=tool_name,
            status="pending",
        ),
    )
    await ws_manager.send_event(
        session_id,
        ConfirmationCreatedEvent(
            conversation_id=conv_id_str,
            execution_id=str(execution.id),
            confirmation_id=confirmation_id,
            tool=tool_name,
            preview=preview,
            action_title=action_title,
        ),
    )

    # Stage 5: waiting for confirmation
    await _emit_status(session_id, conv_id_str, "confirming")

    logger.info(
        "confirmation_requested request_id=%s tool=%s exec=%s confirm=%s",
        request_id, tool_name, execution.id, confirmation_id[:8],
    )

    # Build a ConfirmationRequiredResponse with a generic preview
    # The UI gets the full preview dict and can render any tool
    from app.schemas.chat import ConfirmationRequiredResponse as CRR
    return CRR(
        conversation_id=conv.id,
        confirmation_id=confirmation_id,
        tool=tool_name,
        preview=preview,
        action_title=action_title,
        execution_id=str(execution.id),
    )


# ── Confirm ────────────────────────────────────────────────────────────────────

async def handle_confirm(
    confirmation_id: str,
    session_id: str,
    access_token: str,
    db: AsyncSession,
) -> ToolResultResponse:
    request_id = get_request_id()
    logger.info(
        "confirm_request request_id=%s confirm=%s session=%s",
        request_id, confirmation_id[:8], session_id[:8],
    )

    pending = await atomic_claim_confirmation(confirmation_id)
    if pending is None:
        raise ConfirmationError("Confirmation not found, expired, or already used")

    if pending["session_id"] != session_id:
        raise ConfirmationError("Confirmation does not belong to this session")

    tool_name: str = pending["tool"]
    arguments: dict[str, Any] = pending["arguments"]
    execution_id: str = pending.get("execution_id", "")
    conversation_id: str = pending.get("conversation_id", "")

    logger.info(
        "confirmation_received request_id=%s tool=%s exec=%s",
        request_id, tool_name, execution_id,
    )

    # Update DB: confirmed
    if execution_id:
        await db.execute(
            update(ToolExecution)
            .where(ToolExecution.id == uuid.UUID(execution_id))
            .values(status="confirmed")
        )
        await db.flush()

    await ws_manager.send_event(
        session_id,
        ConfirmationCompletedEvent(
            conversation_id=conversation_id,
            execution_id=execution_id,
            confirmation_id=confirmation_id,
            action="confirmed",
        ),
    )
    await ws_manager.send_event(
        session_id,
        ToolExecutionUpdatedEvent(
            conversation_id=conversation_id,
            execution_id=execution_id,
            status="executing",
        ),
    )

    # Stage: executing
    await _emit_status(session_id, conversation_id, "executing", detail=tool_name)

    if execution_id:
        await db.execute(
            update(ToolExecution)
            .where(ToolExecution.id == uuid.UUID(execution_id))
            .values(status="executing", started_at=datetime.now(timezone.utc))
        )
        await db.flush()

    # Execute via gateway
    logger.info(
        "execution_started request_id=%s tool=%s exec=%s",
        request_id, tool_name, execution_id,
    )
    t0 = time.monotonic()
    result = await gateway_client.call_tool(tool_name, arguments, access_token)
    duration_ms = (time.monotonic() - t0) * 1000

    status_code: int = result["status_code"]
    body: dict[str, Any] = result["body"]
    finished_at = datetime.now(timezone.utc)

    if status_code == 200 and body.get("success"):
        if execution_id:
            await db.execute(
                update(ToolExecution)
                .where(ToolExecution.id == uuid.UUID(execution_id))
                .values(
                    status="success",
                    result=json.dumps(body),
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                )
            )
            await db.flush()

        if conversation_id:
            await _touch_conversation(db, uuid.UUID(conversation_id))

        await ws_manager.send_event(
            session_id,
            ToolExecutionUpdatedEvent(
                conversation_id=conversation_id,
                execution_id=execution_id,
                status="success",
                duration_ms=duration_ms,
            ),
        )
        await _emit_status(session_id, conversation_id, "done")
        logger.info(
            "execution_success request_id=%s tool=%s exec=%s duration_ms=%.0f",
            request_id, tool_name, execution_id, duration_ms,
        )
        return ToolResultResponse(success=True, message="عملیات با موفقیت انجام شد.")

    # Failure
    error_msg = body.get("error", {}).get("message", "عملیات ناموفق بود")
    error_code = body.get("error", {}).get("code", "UNKNOWN_ERROR")

    if execution_id:
        await db.execute(
            update(ToolExecution)
            .where(ToolExecution.id == uuid.UUID(execution_id))
            .values(
                status="failed",
                error=json.dumps({"code": error_code, "message": error_msg}),
                finished_at=finished_at,
                duration_ms=duration_ms,
            )
        )
        await db.flush()

    await ws_manager.send_event(
        session_id,
        ToolExecutionUpdatedEvent(
            conversation_id=conversation_id,
            execution_id=execution_id,
            status="failed",
            error=error_msg,
            duration_ms=duration_ms,
        ),
    )
    await _emit_status(session_id, conversation_id, "error")
    logger.warning(
        "execution_failed request_id=%s tool=%s exec=%s code=%s duration_ms=%.0f",
        request_id, tool_name, execution_id, error_code, duration_ms,
    )
    return ToolResultResponse(success=False, message=error_msg)


# ── Cancel ─────────────────────────────────────────────────────────────────────

async def handle_cancel(
    confirmation_id: str,
    session_id: str,
    db: AsyncSession,
) -> None:
    request_id = get_request_id()
    pending = await get_confirmation(confirmation_id)
    if pending is None:
        return
    if pending["session_id"] != session_id:
        raise ConfirmationError("Confirmation does not belong to this session")

    execution_id = pending.get("execution_id", "")
    conversation_id = pending.get("conversation_id", "")

    await delete_confirmation(confirmation_id)

    if execution_id:
        await db.execute(
            update(ToolExecution)
            .where(ToolExecution.id == uuid.UUID(execution_id))
            .values(status="cancelled")
        )
        await db.flush()

    await ws_manager.send_event(
        session_id,
        ConfirmationCompletedEvent(
            conversation_id=conversation_id,
            execution_id=execution_id,
            confirmation_id=confirmation_id,
            action="cancelled",
        ),
    )
    await ws_manager.send_event(
        session_id,
        ToolExecutionUpdatedEvent(
            conversation_id=conversation_id,
            execution_id=execution_id,
            status="cancelled",
        ),
    )
    logger.info(
        "confirmation_cancelled request_id=%s confirm=%s",
        request_id, confirmation_id[:8],
    )


# ── Errors ─────────────────────────────────────────────────────────────────────

class ConfirmationError(Exception):
    pass
