from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(
    connect=5.0,
    read=settings.gateway_timeout,
    write=settings.gateway_timeout,
    pool=5.0,
)


async def get_tools(access_token: str) -> list[dict[str, Any]]:
    """Fetch tool catalog from MCP Gateway."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.get(
                f"{settings.mcp_gateway_url}/v1/tools",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            return resp.json().get("tools", [])
        except httpx.RequestError as exc:
            logger.error("gateway get_tools error: %s", type(exc).__name__)
            return []


async def call_tool(
    tool_name: str,
    arguments: dict[str, Any],
    access_token: str,
) -> dict[str, Any]:
    """Execute a tool via MCP Gateway."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{settings.mcp_gateway_url}/v1/tools/call",
            json={"tool": tool_name, "arguments": arguments},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )
    return {"status_code": resp.status_code, "body": resp.json()}
