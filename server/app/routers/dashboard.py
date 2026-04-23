from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Body, Depends
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, get_current_user_roles
from ..db import get_db
from ..models import (
    ChatMessage,
    DashboardLayout,
    Process,
    ProcessRoleAccess,
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

    # processes accessible via role
    accessible_q = (
        select(ProcessRoleAccess.process_id)
        .where(ProcessRoleAccess.role_id.in_(roles))
        .distinct()
    )
    accessible_ids = [r[0] for r in (await db.execute(accessible_q)).all()]
    if not accessible_ids:
        return {"processes": []}
    procs = (await db.execute(select(Process).where(Process.id.in_(accessible_ids)))).scalars().all()

    # layout for ordering
    layout_q = select(DashboardLayout).where(DashboardLayout.user_id == user.id)
    layouts = {l.process_id: l.position for l in (await db.execute(layout_q)).scalars().all()}

    # activity counts: chat messages newer than something — for now, total count as a proxy
    # (per-user "last seen" tracking is a later refinement)
    chat_count_q = select(ChatMessage.process_id, func.count()).group_by(ChatMessage.process_id)
    chat_counts = {pid: cnt for pid, cnt in (await db.execute(chat_count_q)).all()}

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
            "chat_count": chat_counts.get(p.id, 0),
        })
    items.sort(key=lambda i: (i["position"], i["id"]))
    return {"processes": items}


@router.post("/layout")
async def save_layout(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    order: Annotated[list[str], Body(embed=True)],
):
    """`order` is an array of process_ids in the desired display order."""
    await db.execute(delete(DashboardLayout).where(DashboardLayout.user_id == user.id))
    for pos, pid in enumerate(order):
        db.add(DashboardLayout(user_id=user.id, process_id=pid, position=pos))
    await db.commit()
    return {"ok": True}
