from __future__ import annotations

import logging

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse

from app.schemas.notify import ToolCallRequest, ToolListResponse, ToolSchema
from app.tools import send_one as send_one_tool
from app.tools.send_one import ToolValidationError
from app.clients.notify_client import NotifyClientError

logger = logging.getLogger(__name__)

router = APIRouter()

_TOOL_REGISTRY: dict[str, object] = {
    "notify.send_one": send_one_tool,
}


@router.get("/v1/tools", response_model=ToolListResponse)
async def list_tools() -> ToolListResponse:
    return ToolListResponse(
        tools=[ToolSchema(**send_one_tool.TOOL_SCHEMA)]
    )


@router.post("/v1/tools/call")
async def call_tool(
    body: ToolCallRequest,
    authorization: str = Header(..., alias="Authorization"),
) -> JSONResponse:
    tool_module = _TOOL_REGISTRY.get(body.tool)
    if tool_module is None:
        raise HTTPException(status_code=404, detail=f"Tool '{body.tool}' not found")

    try:
        result = await tool_module.execute(body.arguments, authorization)  # type: ignore[attr-defined]
    except ToolValidationError as exc:
        return JSONResponse(
            status_code=422,
            content={"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(exc)}},
        )
    except NotifyClientError as exc:
        return JSONResponse(
            status_code=exc.http_status,
            content={"success": False, "error": {"code": exc.code, "message": exc.message}},
        )
    except Exception:
        logger.exception("unexpected error executing tool %s", body.tool)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred"}},
        )

    return JSONResponse(
        status_code=200,
        content={"success": True, "tool": body.tool, "data": result},
    )
