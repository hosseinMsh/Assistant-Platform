"""WebSocket connection manager.
Manages per-session WebSocket connections and broadcasts events.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        # session_id -> list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        self._connections.setdefault(session_id, []).append(websocket)
        logger.info("ws_connect session=%s total=%d", session_id[:8], len(self._connections.get(session_id, [])))

    def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        conns = self._connections.get(session_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(session_id, None)
        logger.info("ws_disconnect session=%s remaining=%d", session_id[:8], len(conns))

    async def send_event(self, session_id: str, event: Any) -> None:
        """Send a Pydantic event to all connections for a session."""
        if hasattr(event, "model_dump"):
            data = event.model_dump()
        else:
            data = event

        # Serialize UUIDs
        payload = json.dumps(data, default=str)
        dead: list[WebSocket] = []

        for ws in list(self._connections.get(session_id, [])):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws, session_id)

    async def broadcast_json(self, session_id: str, data: dict[str, Any]) -> None:
        payload = json.dumps(data, default=str)
        dead: list[WebSocket] = []
        for ws in list(self._connections.get(session_id, [])):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, session_id)


# Singleton shared across the app
manager = ConnectionManager()
