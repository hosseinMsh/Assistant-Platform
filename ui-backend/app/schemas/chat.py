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


class NotificationPreview(BaseModel):
    userName: str
    providerType: int
    channel: str
    subject: str | None = None
    message: str
    sendingDate: str | None = None


class MessageResponse(BaseModel):
    type: Literal["message"] = "message"
    conversation_id: uuid.UUID
    message: str


class ConfirmationRequiredResponse(BaseModel):
    type: Literal["confirmation_required"] = "confirmation_required"
    conversation_id: uuid.UUID
    confirmation_id: str
    execution_id: str
    tool: str
    preview: NotificationPreview


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
