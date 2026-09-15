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


class MessageCreatedEvent(BaseEvent):
    type: Literal["conversation.message.created"] = "conversation.message.created"
    conversation_id: str
    message_id: str
    role: str
    content: str


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


class ConfirmationCreatedEvent(BaseEvent):
    type: Literal["confirmation.created"] = "confirmation.created"
    conversation_id: str
    execution_id: str
    confirmation_id: str
    tool: str
    preview: dict[str, Any]


class ConfirmationCompletedEvent(BaseEvent):
    type: Literal["confirmation.completed"] = "confirmation.completed"
    conversation_id: str
    execution_id: str
    confirmation_id: str
    action: str  # confirmed | cancelled


class AssistantResponseCreatedEvent(BaseEvent):
    type: Literal["assistant.response.created"] = "assistant.response.created"
    conversation_id: str
    message_id: str
    content: str


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
    | ToolExecutionCreatedEvent
    | ToolExecutionUpdatedEvent
    | ConfirmationCreatedEvent
    | ConfirmationCompletedEvent
    | AssistantResponseCreatedEvent
    | ErrorEvent
    | ConnectionStateEvent
)
