"""Demo-reset endpoints — wipe submissions from selected tools so the demo
starts from a clean state. Restricted to praxisinhaber role only.

Resets:
- anamnesebogen: deletes all instances + their transitions + their chat messages
- feature_requests: same
- patient_intake: same

The processes themselves (registry, dashboard cards) remain. Only the
instances vanish.
"""
from __future__ import annotations
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, get_current_user_roles
from ..db import get_db
from ..models import ProcessInstance, Transition, ChatMessage, User

router = APIRouter(prefix="/api/demo", tags=["demo"])


_RESETTABLE = {"anamnesebogen", "feature_requests", "patient_intake"}


@router.post("/reset")
async def reset_demo(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    """Reset demo tools — wipe instances + transitions + chat for the three
    demo-relevant tools. Restricted to praxisinhaber."""
    if "praxisinhaber" not in roles and "praxismanager" not in roles:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Nur Praxisinhaber/-manager dürfen die Demo zurücksetzen",
        )

    summary: dict[str, int] = {}

    for pid in _RESETTABLE:
        # Collect instance IDs for this process
        res = await db.execute(select(ProcessInstance.id).where(ProcessInstance.process_id == pid))
        iids = [row[0] for row in res.all()]
        if not iids:
            summary[pid] = 0
            continue

        # Delete all transitions for those instances
        await db.execute(
            delete(Transition).where(Transition.process_instance_id.in_(iids))
        )
        # Delete instances
        await db.execute(
            delete(ProcessInstance).where(ProcessInstance.id.in_(iids))
        )
        summary[pid] = len(iids)

    # Also wipe chat messages for the demo tools so threads start clean
    for pid in _RESETTABLE:
        await db.execute(
            delete(ChatMessage).where(ChatMessage.process_id == pid)
        )

    await db.commit()
    return {"ok": True, "wiped_instances": summary}
