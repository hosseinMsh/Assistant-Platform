"""WebSocket endpoint for real-time state synchronization."""
from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, Cookie, WebSocket, WebSocketDisconnect

from app.auth.session import get_session, get_token
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.models import Conversation, Message, ToolExecution
from app.ws.events import ConnectionStateEvent, ErrorEvent
from app.ws.manager import manager

from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_pending_execution(session_id: str, conversation_id: str | None) -> dict | None:
    """Return the most recent pending/confirmed execution for recovery on reconnect."""
    if not conversation_id:
        return None
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ToolExecution)
                .join(Conversation)
                .where(
                    Conversation.session_id == session_id,
                    ToolExecution.conversation_id == uuid.UUID(conversation_id),
                    ToolExecution.status.in_(["pending", "confirmed", "executing"]),
                )
                .order_by(ToolExecution.created_at.desc())
                .limit(1)
            )
            ex = result.scalar_one_or_none()
            if ex:
                return {
                    "execution_id": str(ex.id),
                    "tool": ex.tool_name,
                    "status": ex.status,
                    "confirmation_id": ex.confirmation_id,
                }
    except Exception:
        logger.exception("ws_recovery_error")
    return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str | None = None,
    session_id: str | None = Cookie(default=None, alias=settings.session_cookie_name),
):
    # Authenticate
    if not session_id:
        await websocket.close(code=4001, reason="Not authenticated")
        return

    session = await get_session(session_id)
    if session is None:
        await websocket.close(code=4001, reason="Session expired")
        return

    await manager.connect(websocket, session_id)

    # Send current state for reconnect recovery
    pending = await _get_pending_execution(session_id, conversation_id)
    await manager.send_event(
        session_id,
        ConnectionStateEvent(
            status="connected",
            conversation_id=conversation_id,
            pending_execution=pending,
        ),
    )

    try:
        while True:
            # Keep connection alive; client sends pings as needed
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        logger.info("ws_disconnected session=%s", session_id[:8])
    finally:
        manager.disconnect(websocket, session_id)
