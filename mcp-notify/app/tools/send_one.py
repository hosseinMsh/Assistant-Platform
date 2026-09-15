from __future__ import annotations
from typing import Any
from pydantic import ValidationError
from app.clients.notify_client import NotifyClientError, send_one as _send_one
from app.schemas.notify import SendOneArguments

TOOL_SCHEMA: dict[str, Any] = {
    "name": "notify.send_one",
    "description": "Send one notification to a single user",
    "requires_confirmation": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "subject": {"type": "string"},
            "priority": {"type": "integer"},
            "providerType": {"type": "integer", "enum": [1, 2, 3]},
            "sendingDate": {"type": "string", "format": "date-time"},
            "userName": {"type": "string"},
        },
        "required": ["message", "userName", "providerType"],
    },
}

async def execute(arguments: dict[str, Any], authorization: str) -> dict[str, Any]:
    try:
        args = SendOneArguments.model_validate(arguments)
    except ValidationError as exc:
        raise ToolValidationError(str(exc)) from exc
    return await _send_one(args, authorization)

class ToolValidationError(Exception):
    pass
