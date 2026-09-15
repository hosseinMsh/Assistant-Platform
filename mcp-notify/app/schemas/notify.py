from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Any

from pydantic import BaseModel, field_validator


class ProviderType(IntEnum):
    SMS = 1
    BALE = 2
    EMAIL = 3


class SendOneArguments(BaseModel):
    message: str
    userName: str
    providerType: ProviderType
    subject: str | None = None
    priority: int = 1
    sendingDate: datetime | None = None

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be empty")
        return v

    @field_validator("userName")
    @classmethod
    def validate_national_id(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 10:
            raise ValueError("userName must be exactly 10 digits (National ID)")
        return v

    @field_validator("priority")
    @classmethod
    def priority_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("priority must be >= 1")
        return v


class ToolCallRequest(BaseModel):
    tool: str
    arguments: dict[str, Any]


class ToolCallSuccess(BaseModel):
    success: bool = True
    tool: str
    data: dict[str, Any]


class ToolCallError(BaseModel):
    success: bool = False
    error: dict[str, str]


class ToolSchema(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class ToolListResponse(BaseModel):
    tools: list[ToolSchema]
