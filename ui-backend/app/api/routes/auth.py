from __future__ import annotations
import logging

from fastapi import APIRouter, Cookie, HTTPException, Response, status

from app.auth.session import create_session, delete_session
from app.core.config import settings
from app.core.token import normalize_token
from app.schemas.chat import SessionCreateRequest, SessionCreateResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/session", response_model=SessionCreateResponse)
async def create_session_endpoint(body: SessionCreateRequest, response: Response) -> SessionCreateResponse:
    try:
        token = normalize_token(body.access_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid access token")

    if len(token) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid access token")

    session_id = await create_session(token)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.session_ttl_seconds,
        path="/",
    )
    return SessionCreateResponse(authenticated=True, user={"username": "authenticated"})


@router.post("/logout")
async def logout(
    response: Response,
    session_id: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> dict[str, str]:
    if session_id:
        await delete_session(session_id)
    response.delete_cookie(key=settings.session_cookie_name, path="/")
    return {"message": "Logged out"}
