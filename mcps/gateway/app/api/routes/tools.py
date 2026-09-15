from __future__ import annotations

import uuid

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from app.registry.registry import registry
from app.routing.router import router as gw_router
from app.schemas.gateway import ServerListResponse, ToolCallRequest, ToolListResponse

router = APIRouter()


@router.get("/v1/servers", response_model=ServerListResponse)
async def list_servers() -> ServerListResponse:
    return ServerListResponse(servers=registry.get_servers())


@router.get("/v1/tools", response_model=ToolListResponse)
async def list_tools() -> ToolListResponse:
    tools = await registry.get_tools()
    return ToolListResponse(tools=tools)


@router.post("/v1/tools/call")
async def call_tool(
    body: ToolCallRequest,
    authorization: str = Header(..., alias="Authorization"),
) -> JSONResponse:
    request_id = str(uuid.uuid4())
    status, result = await gw_router.call_tool(
        tool_name=body.tool,
        arguments=body.arguments,
        authorization=authorization,
        request_id=request_id,
    )
    return JSONResponse(status_code=status, content=result)
