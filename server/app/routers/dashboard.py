from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, get_current_user_roles
from ..db import get_db
from ..models import (
    ChatMessage,
    DashboardLayout,
    Process,
    ProcessRoleAccess,
    ProcessSeen,
    User,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    if not roles:
        return {"processes": []}

    accessible_q = (
        select(ProcessRoleAccess.process_id)
        .where(ProcessRoleAccess.role_id.in_(roles))
        .distinct()
    )
    accessible_ids = [r[0] for r in (await db.execute(accessible_q)).all()]
    if not accessible_ids:
        return {"processes": []}
    procs = (await db.execute(select(Process).where(Process.id.in_(accessible_ids)))).scalars().all()

    layout_q = select(DashboardLayout).where(DashboardLayout.user_id == user.id)
    layouts = {l.process_id: l.position for l in (await db.execute(layout_q)).scalars().all()}

    seen_q = select(ProcessSeen).where(ProcessSeen.user_id == user.id)
    last_seen = {s.process_id: s.last_seen_at for s in (await db.execute(seen_q)).scalars().all()}

    # For each process, count chat messages newer than last_seen (unseen count).
    unseen_counts: dict[str, int] = {}
    for pid in accessible_ids:
        cond = ChatMessage.process_id == pid
        if pid in last_seen:
            cond = and_(cond, ChatMessage.created_at > last_seen[pid])
        res = await db.execute(select(func.count()).where(cond))
        unseen_counts[pid] = int(res.scalar() or 0)

    items = []
    for p in procs:
        items.append({
            "id": p.id,
            "display_name": p.display_name,
            "icon": p.icon,
            "surface": p.surface,
            "phase": p.phase,
            "chat_attached": p.chat_attached,
            "inputs": p.inputs,
            "outputs": p.outputs,
            "position": layouts.get(p.id, p.sort_order),
            "chat_count": unseen_counts.get(p.id, 0),
        })
    items.sort(key=lambda i: (i["position"], i["id"]))
    return {"processes": items}


@router.post("/layout")
async def save_layout(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    order: Annotated[list[str], Body(embed=True)],
):
    await db.execute(delete(DashboardLayout).where(DashboardLayout.user_id == user.id))
    for pos, pid in enumerate(order):
        db.add(DashboardLayout(user_id=user.id, process_id=pid, position=pos))
    await db.commit()
    return {"ok": True}


@router.post("/seen/{process_id}")
async def mark_seen(
    process_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    """Mark a process as 'seen' by this user — resets the unseen-activity counter."""
    # access check
    res = await db.execute(
        select(ProcessRoleAccess).where(
            ProcessRoleAccess.process_id == process_id,
            ProcessRoleAccess.role_id.in_(roles),
        )
    )
    if res.first() is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "no access")

    existing = await db.get(ProcessSeen, (user.id, process_id))
    now = datetime.now(timezone.utc)
    if existing is None:
        db.add(ProcessSeen(user_id=user.id, process_id=process_id, last_seen_at=now))
    else:
        existing.last_seen_at = now
    await db.commit()
    return {"ok": True, "last_seen_at": now.isoformat()}
