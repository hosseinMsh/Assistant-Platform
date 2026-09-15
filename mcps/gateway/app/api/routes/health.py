from __future__ import annotations

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.registry.registry import registry

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/servers")
async def health_servers() -> JSONResponse:
    results: dict[str, str] = {}
    timeout = httpx.Timeout(connect=settings.mcp_connect_timeout, read=5.0, write=5.0, pool=2.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for server in registry.get_servers():
            try:
                resp = await client.get(f"{server.url}/health")
                results[server.name] = "ok" if resp.status_code == 200 else "degraded"
            except Exception:
                results[server.name] = "unreachable"
    overall = "ok" if all(v == "ok" for v in results.values()) else "degraded"
    return JSONResponse({"status": overall, "servers": results})
