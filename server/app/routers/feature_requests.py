"""Feature-Request board — team-wide tool to collect pain points and wishes.

Each request is a ProcessInstance with:
- title: the short version of the wish ("KIM-Versand-Bestätigung fehlt")
- current_state.body: longer description
- current_state.category: optional grouping
- current_state.submitted_by_role: for filtering
- transitions of type `request_upvoted` from distinct actors = vote count
"""
from __future__ import annotations
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, get_current_user_roles
from ..db import get_db
from ..models import ProcessInstance, Transition, User
from .processes import _check_access

router = APIRouter(prefix="/api/feature-requests", tags=["feature-requests"])

PID = "feature_requests"


@router.get("")
async def list_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    """List all feature requests with vote counts + whether current user voted."""
    await _check_access(db, PID, roles)
    res = await db.execute(
        select(ProcessInstance)
        .where(ProcessInstance.process_id == PID)
        .order_by(ProcessInstance.created_at.desc())
    )
    instances = list(res.scalars().all())

    out = []
    for inst in instances:
        # Count distinct actors who upvoted
        votes_res = await db.execute(
            select(func.count(func.distinct(Transition.actor)))
            .where(Transition.process_instance_id == inst.id)
            .where(Transition.type == "request_upvoted")
        )
        vote_count = votes_res.scalar() or 0

        # Did current user vote?
        user_voted_res = await db.execute(
            select(Transition)
            .where(Transition.process_instance_id == inst.id)
            .where(Transition.type == "request_upvoted")
            .where(Transition.actor == user.id)
            .limit(1)
        )
        user_voted = user_voted_res.scalar_one_or_none() is not None

        state = inst.current_state or {}
        out.append({
            "id": inst.id,
            "title": inst.title,
            "body": state.get("body", ""),
            "category": state.get("category", ""),
            "status": state.get("status", "open"),
            "submitted_by": state.get("submitted_by_name", ""),
            "submitted_by_role": state.get("submitted_by_role", ""),
            "created_at": inst.created_at.isoformat(),
            "vote_count": vote_count,
            "user_voted": user_voted,
        })
    # Sort by votes desc, then created_at desc
    out.sort(key=lambda r: (-r["vote_count"], r["created_at"]), reverse=False)
    out.sort(key=lambda r: -r["vote_count"])
    return out


@router.post("", status_code=201)
async def submit_request(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    body: Annotated[dict[str, Any], Body()] = ...,
):
    """Submit a new feature request / pain point."""
    await _check_access(db, PID, roles)
    title = (body.get("title") or "").strip()
    description = (body.get("body") or "").strip()
    category = (body.get("category") or "").strip()
    if not title:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Titel benötigt")

    iid = uuid.uuid4().hex
    state = {
        "body": description,
        "category": category,
        "status": "open",
        "submitted_by_name": user.display_name or user.id,
        "submitted_by_role": roles[0] if roles else "",
    }
    inst = ProcessInstance(
        id=iid,
        process_id=PID,
        title=title,
        created_by=user.id,
        status="open",
        current_state=state,
    )
    db.add(inst)
    db.add(Transition(
        id=uuid.uuid4().hex,
        process_instance_id=iid,
        actor=user.id,
        type="request_submitted",
        payload={"title": title},
        feeds_back=False,
    ))
    # Submitter auto-upvotes their own
    db.add(Transition(
        id=uuid.uuid4().hex,
        process_instance_id=iid,
        actor=user.id,
        type="request_upvoted",
        payload={},
        feeds_back=True,
    ))
    await db.commit()
    return {"id": iid}


@router.post("/{request_id}/vote")
async def toggle_vote(
    request_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    """Toggle the current user's vote on a request. Returns the new vote state."""
    await _check_access(db, PID, roles)
    inst = await db.get(ProcessInstance, request_id)
    if not inst or inst.process_id != PID:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verbesserungs-Wunsch nicht gefunden")

    # Has the user already voted?
    existing = await db.execute(
        select(Transition)
        .where(Transition.process_instance_id == request_id)
        .where(Transition.type == "request_upvoted")
        .where(Transition.actor == user.id)
    )
    rows = list(existing.scalars().all())

    if rows:
        # Remove the vote (delete the transitions)
        for row in rows:
            await db.delete(row)
        await db.commit()
        return {"voted": False}
    else:
        db.add(Transition(
            id=uuid.uuid4().hex,
            process_instance_id=request_id,
            actor=user.id,
            type="request_upvoted",
            payload={},
            feeds_back=True,
        ))
        await db.commit()
        return {"voted": True}


@router.post("/{request_id}/status")
async def change_status(
    request_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    new_status: Annotated[str, Body(embed=True)] = "open",
):
    """Change request status. Limited to praxisinhaber/praxismanager."""
    await _check_access(db, PID, roles)
    if "praxisinhaber" not in roles and "praxismanager" not in roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Nur Praxisinhaber/-manager")
    inst = await db.get(ProcessInstance, request_id)
    if not inst or inst.process_id != PID:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "nicht gefunden")
    valid = {"open", "planned", "in_progress", "done", "declined"}
    if new_status not in valid:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"status muss in {valid} sein")
    state = dict(inst.current_state or {})
    state["status"] = new_status
    inst.current_state = state
    db.add(Transition(
        id=uuid.uuid4().hex,
        process_instance_id=request_id,
        actor=user.id,
        type="request_status_changed",
        payload={"new_status": new_status},
        feeds_back=True,
    ))
    await db.commit()
    return {"status": new_status}
