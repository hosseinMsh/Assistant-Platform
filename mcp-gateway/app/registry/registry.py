from __future__ import annotations

import logging
import time
from typing import Any

import httpx
import yaml

from app.core.config import settings
from app.schemas.gateway import ServerInfo, ToolInfo

logger = logging.getLogger(__name__)


class ServerRegistry:
    def __init__(self) -> None:
        self._servers: dict[str, str] = {}  # name -> base_url
        self._tool_cache: list[ToolInfo] = []
        self._cache_time: float = 0.0
        self._load_servers()

    def _load_servers(self) -> None:
        try:
            with open(settings.servers_config_path) as f:
                data = yaml.safe_load(f)
            for name, cfg in data.get("servers", {}).items():
                self._servers[name] = cfg["base_url"]
            logger.info("Loaded %d MCP servers from registry", len(self._servers))
        except FileNotFoundError:
            logger.warning("servers.yml not found at %s, starting with empty registry", settings.servers_config_path)
        except Exception:
            logger.exception("Failed to load server registry")

    def get_servers(self) -> list[ServerInfo]:
        return [ServerInfo(name=n, url=u) for n, u in self._servers.items()]

    def get_base_url(self, server_name: str) -> str | None:
        return self._servers.get(server_name)

    def _cache_valid(self) -> bool:
        if settings.tool_cache_ttl == 0:
            return False
        return (time.monotonic() - self._cache_time) < settings.tool_cache_ttl

    async def get_tools(self) -> list[ToolInfo]:
        if self._cache_valid():
            return self._tool_cache

        tools: list[ToolInfo] = []
        timeout = httpx.Timeout(
            connect=settings.mcp_connect_timeout,
            read=settings.mcp_read_timeout,
            write=settings.mcp_read_timeout,
            pool=settings.mcp_connect_timeout,
        )
        async with httpx.AsyncClient(timeout=timeout) as client:
            for server_name, base_url in self._servers.items():
                try:
                    resp = await client.get(f"{base_url}/v1/tools")
                    resp.raise_for_status()
                    data = resp.json()
                    for t in data.get("tools", []):
                        tools.append(
                            ToolInfo(
                                name=t["name"],
                                server=server_name,
                                description=t.get("description", ""),
                                input_schema=t.get("input_schema", {}),
                            )
                        )
                except Exception:
                    logger.warning("Could not reach MCP server '%s' at %s", server_name, base_url)

        self._tool_cache = tools
        self._cache_time = time.monotonic()
        return tools

    async def find_tool(self, tool_name: str) -> ToolInfo | None:
        tools = await self.get_tools()
        return next((t for t in tools if t.name == tool_name), None)


registry = ServerRegistry()
