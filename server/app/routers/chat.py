from __future__ import annotations
import uuid
from typing import Annotated
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, get_current_user_roles
from ..db import get_db
from ..models import ChatMessage, Process, ProcessRoleAccess, User
from ..ws import broadcast

router = APIRouter(prefix="/api/chat", tags=["chat"])


async def _ensure_access(db: AsyncSession, process_id: str, roles: list[str]) -> None:
    proc = await db.get(Process, process_id)
    if proc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "process not found")
    res = await db.execute(
        select(ProcessRoleAccess).where(
            ProcessRoleAccess.process_id == process_id,
            ProcessRoleAccess.role_id.in_(roles),
        )
    )
    if res.first() is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "no access")


@router.get("/{process_id}/messages")
async def list_messages(
    process_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    await _ensure_access(db, process_id, roles)
    res = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.process_id == process_id)
        .order_by(desc(ChatMessage.created_at))
        .limit(200)
    )
    msgs = list(res.scalars().all())
    msgs.reverse()
    return [
        {
            "id": m.id,
            "process_id": m.process_id,
            "user_id": m.user_id,
            "body": m.body,
            "created_at": m.created_at.isoformat(),
        }
        for m in msgs
    ]


@router.post("/{process_id}/messages", status_code=201)
async def send_message(
    process_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    body: Annotated[str, Body(embed=True)] = ...,
):
    await _ensure_access(db, process_id, roles)
    if not body.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty message")
    msg = ChatMessage(id=uuid.uuid4().hex, process_id=process_id, user_id=user.id, body=body.strip())
    db.add(msg)
    await db.commit()
    payload = {
        "id": msg.id,
        "process_id": msg.process_id,
        "user_id": msg.user_id,
        "body": msg.body,
        "created_at": msg.created_at.isoformat(),
    }
    await broadcast(f"chat:{process_id}", {"type": "chat_message", "message": payload})
    return payload
