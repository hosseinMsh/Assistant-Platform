from __future__ import annotations

from fastapi import Cookie, HTTPException, status

from app.auth.session import get_session, get_token
from app.core.config import settings


async def require_session(
    session_id: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> str:
    """Return session_id if valid, else 401."""
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    session = await get_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")
    return session_id


async def require_token(
    session_id: str = Cookie(default=None, alias=settings.session_cookie_name),  # type: ignore[assignment]
) -> str:
    """Return the access token from the session."""
    session_id = await require_session(session_id)  # type: ignore[arg-type]
    token = await get_token(session_id)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not found in session")
    return token
