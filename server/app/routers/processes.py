from __future__ import annotations
import uuid
from typing import Annotated, Any
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, get_current_user_roles
from ..db import get_db
from ..models import Process, ProcessInstance, ProcessRoleAccess, Transition, User
from ..processes import get_process

router = APIRouter(prefix="/api/processes", tags=["processes"])


async def _check_access(db: AsyncSession, process_id: str, roles: list[str]) -> Process:
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
        raise HTTPException(status.HTTP_403_FORBIDDEN, "no access to this process")
    return proc


@router.get("/{process_id}")
async def get_process_meta(
    process_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    proc = await _check_access(db, process_id, roles)
    return {
        "id": proc.id,
        "display_name": proc.display_name,
        "icon": proc.icon,
        "surface": proc.surface,
        "phase": proc.phase,
        "chat_attached": proc.chat_attached,
        "inputs": proc.inputs,
        "outputs": proc.outputs,
        "transition_types": proc.transition_types,
    }


@router.get("/{process_id}/instances")
async def list_instances(
    process_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    await _check_access(db, process_id, roles)
    res = await db.execute(
        select(ProcessInstance)
        .where(ProcessInstance.process_id == process_id)
        .order_by(desc(ProcessInstance.created_at))
        .limit(50)
    )
    return [
        {
            "id": i.id,
            "title": i.title,
            "status": i.status,
            "created_at": i.created_at.isoformat(),
            "updated_at": i.updated_at.isoformat(),
            "current_state": i.current_state,
        }
        for i in res.scalars().all()
    ]


@router.post("/{process_id}/instances", status_code=201)
async def create_instance(
    process_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    title: Annotated[str, Body(embed=True)] = "",
):
    await _check_access(db, process_id, roles)
    iid = uuid.uuid4().hex
    inst = ProcessInstance(
        id=iid,
        process_id=process_id,
        title=title,
        created_by=user.id,
        status="open",
        current_state={},
    )
    db.add(inst)
    db.add(Transition(
        id=uuid.uuid4().hex,
        process_instance_id=iid,
        actor=user.id,
        type="session_started",
        payload={"title": title},
        feeds_back=False,
    ))
    await db.commit()
    return {"id": iid, "process_id": process_id, "title": title, "status": "open", "current_state": {}}


@router.get("/{process_id}/instances/{instance_id}")
async def get_instance(
    process_id: str,
    instance_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    await _check_access(db, process_id, roles)
    inst = await db.get(ProcessInstance, instance_id)
    if not inst or inst.process_id != process_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "instance not found")
    return {
        "id": inst.id,
        "process_id": inst.process_id,
        "title": inst.title,
        "status": inst.status,
        "created_at": inst.created_at.isoformat(),
        "updated_at": inst.updated_at.isoformat(),
        "current_state": inst.current_state,
    }


@router.get("/{process_id}/instances/{instance_id}/transitions")
async def list_transitions(
    process_id: str,
    instance_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    await _check_access(db, process_id, roles)
    res = await db.execute(
        select(Transition)
        .where(Transition.process_instance_id == instance_id)
        .order_by(Transition.timestamp)
    )
    return [
        {
            "id": t.id,
            "actor": t.actor,
            "type": t.type,
            "payload": t.payload,
            "feeds_back": t.feeds_back,
            "retracted_by": t.retracted_by,
            "timestamp": t.timestamp.isoformat(),
        }
        for t in res.scalars().all()
    ]


@router.post("/{process_id}/instances/{instance_id}/transitions", status_code=201)
async def append_transition(
    process_id: str,
    instance_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    body: Annotated[dict[str, Any], Body()] = ...,
):
    proc = await _check_access(db, process_id, roles)
    inst = await db.get(ProcessInstance, instance_id)
    if not inst or inst.process_id != process_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "instance not found")

    ttype = body.get("type")
    if ttype not in proc.transition_types:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"unknown transition type: {ttype}")

    spec = proc.transition_types[ttype]
    feeds_back = bool(spec.get("feeds_back", False))
    payload = body.get("payload") or {}

    tid = uuid.uuid4().hex
    db.add(Transition(
        id=tid,
        process_instance_id=instance_id,
        actor=user.id,
        type=ttype,
        payload=payload,
        feeds_back=feeds_back,
    ))

    # Update current_state for known transition types (intake-specific projections)
    state = dict(inst.current_state or {})
    if ttype == "field_corrected":
        fields = dict(state.get("fields", {}))
        f = body["payload"]["field"]
        fields[f] = {"value": body["payload"]["to"], "status": "corrected"}
        state["fields"] = fields
    elif ttype == "field_accepted":
        fields = dict(state.get("fields", {}))
        f = body["payload"]["field"]
        fields[f] = {"value": body["payload"].get("value"), "status": "accepted"}
        state["fields"] = fields
    elif ttype == "field_rejected":
        fields = dict(state.get("fields", {}))
        f = body["payload"]["field"]
        fields[f] = {"value": None, "status": "rejected"}
        state["fields"] = fields
    elif ttype == "session_marked_done":
        state["done"] = True

    inst.current_state = state
    await db.commit()
    return {"id": tid}


@router.post("/{process_id}/instances/{instance_id}/undo", status_code=201)
async def undo(
    process_id: str,
    instance_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    """Tier 2 undo. Find the most recent un-retracted, non-undo transition by this user
    (or any user — keep simple here) and append an `undo` transition referencing it."""
    await _check_access(db, process_id, roles)

    res = await db.execute(
        select(Transition)
        .where(
            Transition.process_instance_id == instance_id,
            Transition.retracted_by.is_(None),
            Transition.type != "undo",
            Transition.type != "session_started",
        )
        .order_by(desc(Transition.timestamp))
        .limit(1)
    )
    target = res.scalar_one_or_none()
    if not target:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "nothing to undo")

    undo_id = uuid.uuid4().hex
    db.add(Transition(
        id=undo_id,
        process_instance_id=instance_id,
        actor=user.id,
        type="undo",
        payload={"undid": target.id, "undid_type": target.type, "undid_payload": target.payload},
        feeds_back=False,
    ))
    await db.flush()
    target.retracted_by = undo_id

    # naive state-projection: recompute fields from full transition history
    inst = await db.get(ProcessInstance, instance_id)
    if inst:
        all_t = (await db.execute(
            select(Transition)
            .where(Transition.process_instance_id == instance_id)
            .order_by(Transition.timestamp)
        )).scalars().all()
        fields: dict[str, Any] = {}
        done = False
        for t in all_t:
            if t.id == target.id:  # the one being undone now
                continue
            if t.retracted_by is not None and t.id != undo_id:
                continue
            if t.type == "field_corrected":
                fields[t.payload["field"]] = {"value": t.payload["to"], "status": "corrected"}
            elif t.type == "field_accepted":
                fields[t.payload["field"]] = {"value": t.payload.get("value"), "status": "accepted"}
            elif t.type == "field_rejected":
                fields[t.payload["field"]] = {"value": None, "status": "rejected"}
            elif t.type == "session_marked_done":
                done = True
        state = dict(inst.current_state or {})
        state["fields"] = fields
        if done:
            state["done"] = True
        else:
            state.pop("done", None)
        inst.current_state = state

    await db.commit()
    return {"id": undo_id, "undid": target.id, "undid_type": target.type}
