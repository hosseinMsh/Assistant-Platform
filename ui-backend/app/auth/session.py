"""Server-side session management using Redis.
Tokens are stored server-side only and never exposed to clients.
"""
from __future__ import annotations

import hashlib
import json
import logging
import secrets
import uuid
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


# ── Session ────────────────────────────────────────────────────────────────────

def _session_key(session_id: str) -> str:
    return f"session:{session_id}"


def _confirmation_key(confirmation_id: str) -> str:
    return f"confirm:{confirmation_id}"


async def create_session(access_token: str) -> str:
    """Store token server-side; return opaque session_id cookie value."""
    session_id = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(access_token.encode()).hexdigest()
    payload = {
        "token": access_token,
        "token_hash": token_hash,  # for audit logs — never log the raw token
    }
    r = get_redis()
    await r.setex(_session_key(session_id), settings.session_ttl_seconds, json.dumps(payload))
    logger.info("session_created hash=%s", token_hash[:12])
    return session_id


async def get_session(session_id: str) -> dict[str, Any] | None:
    r = get_redis()
    raw = await r.get(_session_key(session_id))
    if raw is None:
        return None
    return json.loads(raw)


async def delete_session(session_id: str) -> None:
    r = get_redis()
    await r.delete(_session_key(session_id))
    logger.info("session_deleted session=%s", session_id[:8])


async def get_token(session_id: str) -> str | None:
    session = await get_session(session_id)
    if session is None:
        return None
    return session.get("token")


# ── Confirmations ──────────────────────────────────────────────────────────────

async def create_confirmation(
    session_id: str,
    tool: str,
    arguments: dict[str, Any],
    execution_id: str = "",
    conversation_id: str = "",
) -> str:
    confirmation_id = str(uuid.uuid4())
    payload = {
        "session_id": session_id,
        "tool": tool,
        "arguments": arguments,
        "execution_id": execution_id,
        "conversation_id": conversation_id,
        "claimed": False,
    }
    r = get_redis()
    await r.setex(
        _confirmation_key(confirmation_id),
        settings.confirmation_ttl_seconds,
        json.dumps(payload),
    )
    return confirmation_id


async def atomic_claim_confirmation(confirmation_id: str) -> dict[str, Any] | None:
    """Atomically read and mark a confirmation as claimed.
    Returns the payload if it was unclaimed, None if already claimed/missing.
    Uses a Redis Lua script for atomicity — prevents double execution.
    """
    r = get_redis()
    key = _confirmation_key(confirmation_id)

    # Lua: read, check claimed, set claimed atomically
    lua_script = """
local val = redis.call('GET', KEYS[1])
if val == false then return nil end
local data = cjson.decode(val)
if data['claimed'] then return nil end
data['claimed'] = true
redis.call('SET', KEYS[1], cjson.encode(data), 'KEEPTTL')
return val
"""
    result = await r.eval(lua_script, 1, key)  # type: ignore[attr-defined]
    if result is None:
        return None
    return json.loads(result)


async def get_confirmation(confirmation_id: str) -> dict[str, Any] | None:
    r = get_redis()
    raw = await r.get(_confirmation_key(confirmation_id))
    if raw is None:
        return None
    return json.loads(raw)


async def delete_confirmation(confirmation_id: str) -> None:
    r = get_redis()
    await r.delete(_confirmation_key(confirmation_id))
