from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ServerInfo(BaseModel):
    name: str
    url: str


class ServerListResponse(BaseModel):
    servers: list[ServerInfo]


class ToolInfo(BaseModel):
    name: str
    server: str
    description: str
    input_schema: dict[str, Any]
    requires_confirmation: bool = False


class ToolListResponse(BaseModel):
    tools: list[ToolInfo]


class ToolCallRequest(BaseModel):
    tool: str
    arguments: dict[str, Any]
