"""API schemas for the chat/auth endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


# ── Requests ───────────────────────────────────────────────────────────────────

class SessionCreateRequest(BaseModel):
    access_token: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: uuid.UUID | None = None


class ConfirmRequest(BaseModel):
    confirmation_id: str


class CancelRequest(BaseModel):
    confirmation_id: str


# ── Responses ──────────────────────────────────────────────────────────────────

class SessionCreateResponse(BaseModel):
    authenticated: bool
    user: dict[str, str]


class MessageResponse(BaseModel):
    type: Literal["message"] = "message"
    conversation_id: uuid.UUID
    message: str


class ConfirmationRequiredResponse(BaseModel):
    """Returned when the agent selects a tool that requires user confirmation.

    The `preview` field is a generic dict that can hold any tool's arguments.
    This design ensures forward-compatibility: adding new tools requires no
    schema changes here.

    The UI receives:
      - tool: the exact tool name (e.g. "notify.send_one")
      - action_title: human-readable Persian title for the dialog header
      - preview: flat dict with tool name + all arguments for display
    """
    type: Literal["confirmation_required"] = "confirmation_required"
    conversation_id: uuid.UUID
    confirmation_id: str
    execution_id: str
    tool: str
    # Generic preview — works for any tool
    preview: dict[str, Any]
    # Human-readable title for the confirmation dialog
    action_title: str = "تأیید عملیات"


class ToolResultResponse(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    success: bool
    message: str


# ── Error response ─────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ── Conversations ──────────────────────────────────────────────────────────────

class ConversationSummary(BaseModel):
    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class ConversationDetail(ConversationSummary):
    messages: list[MessageOut]
