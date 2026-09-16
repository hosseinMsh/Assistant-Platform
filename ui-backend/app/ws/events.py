"""WebSocket event definitions.
All events sent from backend → frontend are defined here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, field_serializer


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BaseEvent(BaseModel):
    timestamp: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.timestamp:
            self.timestamp = _now()

    @field_serializer("*")
    def serialize_uuid(self, v: Any, _info: Any) -> Any:
        if isinstance(v, UUID):
            return str(v)
        return v


# ── Conversation / Message ─────────────────────────────────────────────────────

class MessageCreatedEvent(BaseEvent):
    type: Literal["conversation.message.created"] = "conversation.message.created"
    conversation_id: str
    message_id: str
    role: str
    content: str


class AssistantResponseCreatedEvent(BaseEvent):
    type: Literal["assistant.response.created"] = "assistant.response.created"
    conversation_id: str
    message_id: str
    content: str


# ── Processing Status (Real-time transparency) ─────────────────────────────────
# These events show the user what is happening step by step while they wait.

class ProcessingStatusEvent(BaseEvent):
    """Sent at each stage of request processing so the UI can show live status."""
    type: Literal["processing.status"] = "processing.status"
    conversation_id: str
    # stage: one of: thinking | fetching_tools | calling_llm | tool_selected | confirming | executing | done | error
    stage: str
    # Human-readable label shown in the UI (Persian)
    label: str
    # Optional detail, e.g. tool name selected
    detail: str | None = None


# ── Tool Execution ─────────────────────────────────────────────────────────────

class ToolExecutionCreatedEvent(BaseEvent):
    type: Literal["tool_execution.created"] = "tool_execution.created"
    conversation_id: str
    execution_id: str
    tool: str
    status: str  # pending


class ToolExecutionUpdatedEvent(BaseEvent):
    type: Literal["tool_execution.updated"] = "tool_execution.updated"
    conversation_id: str
    execution_id: str
    status: str
    result: str | None = None
    error: str | None = None
    duration_ms: float | None = None


# ── Confirmation ───────────────────────────────────────────────────────────────

class ConfirmationCreatedEvent(BaseEvent):
    type: Literal["confirmation.created"] = "confirmation.created"
    conversation_id: str
    execution_id: str
    confirmation_id: str
    tool: str
    # Generic preview dict — supports any tool, not just notify
    preview: dict[str, Any]
    # Human-readable title for what is being confirmed
    action_title: str = "تأیید عملیات"


class ConfirmationCompletedEvent(BaseEvent):
    type: Literal["confirmation.completed"] = "confirmation.completed"
    conversation_id: str
    execution_id: str
    confirmation_id: str
    action: str  # confirmed | cancelled


# ── Connection ─────────────────────────────────────────────────────────────────

class ErrorEvent(BaseEvent):
    type: Literal["error"] = "error"
    code: str
    message: str
    conversation_id: str | None = None


class ConnectionStateEvent(BaseEvent):
    type: Literal["connection.state"] = "connection.state"
    status: str  # connected
    conversation_id: str | None = None
    pending_execution: dict[str, Any] | None = None


AnyEvent = (
    MessageCreatedEvent
    | AssistantResponseCreatedEvent
    | ProcessingStatusEvent
    | ToolExecutionCreatedEvent
    | ToolExecutionUpdatedEvent
    | ConfirmationCreatedEvent
    | ConfirmationCompletedEvent
    | ErrorEvent
    | ConnectionStateEvent
)
