from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import require_session
from app.models.models import Conversation, Message
from app.schemas.chat import ConversationDetail, ConversationSummary, MessageOut

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    session_id: str = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationSummary]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.session_id == session_id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
    )
    convs = result.scalars().all()
    return [ConversationSummary(id=c.id, title=c.title, created_at=c.created_at, updated_at=c.updated_at) for c in convs]


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: uuid.UUID,
    session_id: str = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetail:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.session_id == session_id)
        .options(selectinload(Conversation.messages))
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[
            MessageOut(id=m.id, role=m.role, content=m.content, created_at=m.created_at)
            for m in conv.messages
        ],
    )
