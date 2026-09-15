"""Chat service — the core business logic layer.

State machine for tool execution:
  pending → confirmed → executing → success | failed
  pending → cancelled
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
    NotificationPreview,
    ToolResultResponse,
)
from app.ws.events import (
    AssistantResponseCreatedEvent,
    ConfirmationCompletedEvent,
    ConfirmationCreatedEvent,
    ErrorEvent,
    MessageCreatedEvent,
    ToolExecutionCreatedEvent,
    ToolExecutionUpdatedEvent,
)
from app.ws.manager import manager as ws_manager

logger = logging.getLogger(__name__)

_PROVIDER_CHANNEL = {1: "SMS", 2: "Bale", 3: "Email"}


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
    """Update updated_at so the sidebar sorts correctly."""
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


# ── Auto-title ─────────────────────────────────────────────────────────────────

def _make_title(text: str) -> str:
    """Generate a conversation title from the first user message."""
    clean = text.strip()
    return clean[:60] + ("…" if len(clean) > 60 else "")


# ── Main chat handler ──────────────────────────────────────────────────────────

async def handle_chat(
    request: ChatRequest,
    session_id: str,
    access_token: str,
    db: AsyncSession,
) -> MessageResponse | ConfirmationRequiredResponse:
    request_id = get_request_id()
    logger.info("chat_request request_id=%s session=%s conv=%s", request_id, session_id[:8], request.conversation_id)

    conv = await _get_or_create_conversation(db, session_id, request.conversation_id)

    # Set title on first message
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
            conversation_id=str(conv.id),
            message_id=str(user_msg.id),
            role="user",
            content=request.message,
        ),
    )

    # Get tools from gateway
    logger.info("fetching_tools request_id=%s", request_id)
    tools = await gateway_client.get_tools(access_token)
    if not tools:
        logger.warning("no_tools_available request_id=%s", request_id)

    # Run LLM agent
    logger.info("agent_processing request_id=%s conv=%s", request_id, conv.id)
    try:
        agent_resp = await llm_agent.run(request.message, history, tools)
    except Exception as exc:
        logger.error("agent_failed request_id=%s error=%s", request_id, type(exc).__name__)
        await ws_manager.send_event(session_id, ErrorEvent(
            code="AGENT_ERROR",
            message="خطا در پردازش درخواست",
            conversation_id=str(conv.id),
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
                conversation_id=str(conv.id),
                message_id=str(assistant_msg.id),
                content=text,
            ),
        )
        logger.info("agent_text_response request_id=%s conv=%s", request_id, conv.id)
        return MessageResponse(conversation_id=conv.id, message=text)

    # ── Tool call path ────────────────────────────────────────────────────────
    tool_call = agent_resp.tool_call
    tool_name: str = tool_call["tool"]  # type: ignore[index]
    arguments: dict[str, Any] = tool_call["arguments"]  # type: ignore[index]

    logger.info("tool_selected request_id=%s tool=%s conv=%s", request_id, tool_name, conv.id)

    # Create DB execution record (pending)
    execution = ToolExecution(
        conversation_id=conv.id,
        tool_name=tool_name,
        arguments=json.dumps(arguments),
        status="pending",
        request_id=request_id,
    )
    db.add(execution)
    await db.flush()

    # Create confirmation in Redis
    confirmation_id = await create_confirmation(
        session_id=session_id,
        tool=tool_name,
        arguments=arguments,
        execution_id=str(execution.id),
    )

    # Update execution with confirmation_id
    execution.confirmation_id = confirmation_id
    await db.flush()
    await _touch_conversation(db, conv.id)

    preview = _build_preview(arguments)

    # Broadcast events
    await ws_manager.send_event(
        session_id,
        ToolExecutionCreatedEvent(
            conversation_id=str(conv.id),
            execution_id=str(execution.id),
            tool=tool_name,
            status="pending",
        ),
    )
    await ws_manager.send_event(
        session_id,
        ConfirmationCreatedEvent(
            conversation_id=str(conv.id),
            execution_id=str(execution.id),
            confirmation_id=confirmation_id,
            tool=tool_name,
            preview=preview.model_dump(),
        ),
    )

    logger.info(
        "confirmation_requested request_id=%s tool=%s exec=%s confirm=%s",
        request_id, tool_name, execution.id, confirmation_id[:8],
    )

    return ConfirmationRequiredResponse(
        conversation_id=conv.id,
        confirmation_id=confirmation_id,
        tool=tool_name,
        preview=preview,
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
    logger.info("confirm_request request_id=%s confirm=%s session=%s", request_id, confirmation_id[:8], session_id[:8])

    # Atomic claim — prevents double execution
    pending = await atomic_claim_confirmation(confirmation_id)
    if pending is None:
        raise ConfirmationError("Confirmation not found, expired, or already used")

    if pending["session_id"] != session_id:
        raise ConfirmationError("Confirmation does not belong to this session")

    tool_name: str = pending["tool"]
    arguments: dict[str, Any] = pending["arguments"]
    execution_id: str = pending.get("execution_id", "")
    conversation_id: str = pending.get("conversation_id", "")

    logger.info("confirmation_received request_id=%s tool=%s exec=%s", request_id, tool_name, execution_id)

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

    # Update DB: executing
    started_at = datetime.now(timezone.utc)
    if execution_id:
        await db.execute(
            update(ToolExecution)
            .where(ToolExecution.id == uuid.UUID(execution_id))
            .values(status="executing", started_at=started_at)
        )
        await db.flush()

    # Execute via gateway
    logger.info("execution_started request_id=%s tool=%s exec=%s", request_id, tool_name, execution_id)
    t0 = time.monotonic()
    result = await gateway_client.call_tool(tool_name, arguments, access_token)
    duration_ms = (time.monotonic() - t0) * 1000

    status_code: int = result["status_code"]
    body: dict[str, Any] = result["body"]
    finished_at = datetime.now(timezone.utc)

    if status_code == 200 and body.get("success"):
        # Success
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
        logger.info(
            "execution_success request_id=%s tool=%s exec=%s duration_ms=%.0f",
            request_id, tool_name, execution_id, duration_ms,
        )
        return ToolResultResponse(success=True, message="اعلان با موفقیت ارسال شد.")

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
    logger.info("confirmation_cancelled request_id=%s confirm=%s", request_id, confirmation_id[:8])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_preview(arguments: dict[str, Any]) -> NotificationPreview:
    provider_type = arguments.get("providerType", 1)
    sending_date = arguments.get("sendingDate")
    if isinstance(sending_date, datetime):
        sending_date = sending_date.isoformat()
    return NotificationPreview(
        userName=arguments.get("userName", ""),
        providerType=provider_type,
        channel=_PROVIDER_CHANNEL.get(provider_type, "Unknown"),
        subject=arguments.get("subject"),
        message=arguments.get("message", ""),
        sendingDate=sending_date,
    )


class ConfirmationError(Exception):
    pass
