from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.core.config import settings
from app.registry.registry import registry

logger = logging.getLogger(__name__)


class GatewayRouter:
    def __init__(self) -> None:
        self._timeout = httpx.Timeout(
            connect=settings.mcp_connect_timeout,
            read=settings.mcp_read_timeout,
            write=settings.mcp_read_timeout,
            pool=settings.mcp_connect_timeout,
        )

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        authorization: str,
        request_id: str,
    ) -> tuple[int, dict[str, Any]]:
        tool = await registry.find_tool(tool_name)
        if tool is None:
            logger.warning("request_id=%s tool=%s not_found", request_id, tool_name)
            return 404, {"success": False, "error": {"code": "TOOL_NOT_FOUND", "message": f"Tool '{tool_name}' not found"}}

        base_url = registry.get_base_url(tool.server)
        if base_url is None:
            logger.error("request_id=%s server=%s not_in_registry", request_id, tool.server)
            return 503, {"success": False, "error": {"code": "SERVER_UNAVAILABLE", "message": "MCP server not available"}}

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    f"{base_url}/v1/tools/call",
                    json={"tool": tool_name, "arguments": arguments},
                    headers={"Authorization": authorization, "Content-Type": "application/json"},
                )
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info(
                "request_id=%s tool=%s server=%s status=%d latency_ms=%d",
                request_id, tool_name, tool.server, resp.status_code, latency_ms,
            )
            return resp.status_code, resp.json()

        except httpx.ConnectTimeout:
            logger.error("request_id=%s tool=%s server=%s connect_timeout", request_id, tool_name, tool.server)
            return 504, {"success": False, "error": {"code": "UPSTREAM_TIMEOUT", "message": "MCP server connection timed out"}}
        except httpx.ReadTimeout:
            logger.error("request_id=%s tool=%s server=%s read_timeout", request_id, tool_name, tool.server)
            return 504, {"success": False, "error": {"code": "UPSTREAM_TIMEOUT", "message": "MCP server did not respond in time"}}
        except httpx.RequestError as exc:
            logger.error("request_id=%s tool=%s server=%s error=%s", request_id, tool_name, tool.server, type(exc).__name__)
            return 502, {"success": False, "error": {"code": "UPSTREAM_ERROR", "message": "Could not reach MCP server"}}


router = GatewayRouter()
