from __future__ import annotations
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.session import get_token
from app.chat.service import ConfirmationError, handle_cancel, handle_chat, handle_confirm
from app.core.database import get_db
from app.core.dependencies import require_session
from app.core.logging import new_request_id
from app.stt_client import transcribe_audio
from app.schemas.chat import CancelRequest, ChatRequest, ConfirmRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["chat"])


async def _get_token_or_401(session_id: str) -> str:
    token = await get_token(session_id)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalid")
    return token


@router.post("/chat")
async def chat(
    body: ChatRequest,
    session_id: str = Depends(require_session),
    db: AsyncSession = Depends(get_db),
):
    new_request_id()
    token = await _get_token_or_401(session_id)
    try:
        return await handle_chat(body, session_id, token, db)
    except ConfirmationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("chat_unhandled_error")
        raise HTTPException(status_code=500, detail="خطای داخلی سرور")


@router.post("/chat/confirm")
async def confirm(
    body: ConfirmRequest,
    session_id: str = Depends(require_session),
    db: AsyncSession = Depends(get_db),
):
    new_request_id()
    token = await _get_token_or_401(session_id)
    try:
        return await handle_confirm(body.confirmation_id, session_id, token, db)
    except ConfirmationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception:
        logger.exception("confirm_unhandled_error")
        raise HTTPException(status_code=500, detail="خطای داخلی سرور")


@router.post("/stt")
async def stt(
    file: UploadFile = File(...),
    session_id: str = Depends(require_session),
):
    new_request_id()
    try:
        contents = await file.read()
        text = await transcribe_audio(contents, file.filename or "audio.webm", file.content_type or "audio/webm")
        return {"text": text}
    except Exception as exc:
        logger.exception("stt_error")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/chat/cancel")
async def cancel(
    body: CancelRequest,
    session_id: str = Depends(require_session),
    db: AsyncSession = Depends(get_db),
):
    new_request_id()
    try:
        await handle_cancel(body.confirmation_id, session_id, db)
    except ConfirmationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return {"cancelled": True}
