"""
Rechnungsprüfung router. Pulls AbrechnungPositionen from the MO adapter,
runs the rule engine, surfaces issues per Fall.

Read-only relative to MO. Issue dismissal + acknowledgment are writes
into our own DB (transition log on the rechnungspruefung process).
"""
from __future__ import annotations
import uuid
from dataclasses import asdict
from datetime import date, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, get_current_user_roles
from ..billing_rules import RULES, run_rules
from ..db import get_db
from ..medical_office import get_adapter
from ..models import Process, ProcessRoleAccess, ProcessInstance, Transition, User

router = APIRouter(prefix="/api/rechnungspruefung", tags=["rechnungspruefung"])
PROCESS_ID = "rechnungspruefung"


def _serialize(o: Any) -> Any:
    if hasattr(o, "__dataclass_fields__"):
        return {k: _serialize(v) for k, v in asdict(o).items()}
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    if isinstance(o, list):
        return [_serialize(x) for x in o]
    if isinstance(o, dict):
        return {k: _serialize(v) for k, v in o.items()}
    return o


async def _ensure_access(db: AsyncSession, roles: list[str]) -> None:
    proc = await db.get(Process, PROCESS_ID)
    if proc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "rechnungspruefung not registered")
    from sqlalchemy import select
    res = await db.execute(
        select(ProcessRoleAccess).where(
            ProcessRoleAccess.process_id == PROCESS_ID,
            ProcessRoleAccess.role_id.in_(roles),
        )
    )
    if res.first() is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "no access")


@router.get("/_meta")
async def meta(
    db: Annotated[AsyncSession, Depends(get_db)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    await _ensure_access(db, roles)
    a = get_adapter()
    return {
        "adapter": a.name,
        "grounded_kinds": list(a.grounded_kinds),
        "ungrounded_kinds": [k for k in ("patient", "fall", "befund", "abrechnung")
                              if k not in a.grounded_kinds],
        "rule_count": len(RULES),
        "rules": [
            {"id": r.id, "name": r.name, "catalog": r.catalog, "source": r.source}
            for r in RULES
        ],
    }


@router.get("/quartal/{quartal}")
async def list_quartal(
    quartal: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    """Group positions for a quartal by Fall, run rules per Fall, return summary.
    Quartal format: e.g. '2026Q1'."""
    await _ensure_access(db, roles)
    a = get_adapter()
    positions = a.list_positions_for_quartal(quartal)
    # Group by fall_id
    by_fall: dict[str, list] = {}
    for p in positions:
        if p.fall_id:
            by_fall.setdefault(p.fall_id, []).append(p)

    fall_summaries = []
    total_issues = 0
    total_errors = 0
    for fall_id, pos_list in by_fall.items():
        # Need patient — fetch from first position
        patient = a.get_patient(pos_list[0].patient_id)
        if patient is None:
            continue
        issues = run_rules(pos_list, patient)
        total_issues += len(issues)
        total_errors += sum(1 for i in issues if i.severity == "error")
        fall_summaries.append({
            "fall_id": fall_id,
            "patient_id": patient.id,
            "patient_name": f"{patient.vorname} {patient.nachname}",
            "position_count": len(pos_list),
            "issue_count": len(issues),
            "error_count": sum(1 for i in issues if i.severity == "error"),
            "warning_count": sum(1 for i in issues if i.severity == "warning"),
            "katalog": list({p.katalog for p in pos_list}),
        })
    fall_summaries.sort(key=lambda s: (-s["error_count"], -s["issue_count"]))

    return {
        "quartal": quartal,
        "fall_count": len(by_fall),
        "position_count": len(positions),
        "issue_count": total_issues,
        "error_count": total_errors,
        "faelle": fall_summaries,
    }


@router.get("/fall/{fall_id}")
async def get_fall(
    fall_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    await _ensure_access(db, roles)
    a = get_adapter()
    positions = a.list_positions_for_fall(fall_id)
    if not positions:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "fall not found or has no positions")
    patient = a.get_patient(positions[0].patient_id)
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "patient not found")

    issues = run_rules(positions, patient)

    # Filter out previously-dismissed issues (look up transition log)
    inst = await _get_or_create_fall_instance(db, fall_id)
    from sqlalchemy import select
    dismissed_keys = set()
    res = await db.execute(
        select(Transition)
        .where(
            Transition.process_instance_id == inst.id,
            Transition.type == "issue_dismissed_false_positive",
            Transition.retracted_by.is_(None),
        )
    )
    for t in res.scalars().all():
        rid = t.payload.get("rule_id")
        pids = tuple(sorted(t.payload.get("position_ids") or []))
        dismissed_keys.add((rid, pids))

    visible_issues = []
    dismissed = []
    for i in issues:
        key = (i.rule_id, tuple(sorted(i.position_ids)))
        if key in dismissed_keys:
            dismissed.append(_serialize(i))
        else:
            visible_issues.append(_serialize(i))

    return {
        "fall_id": fall_id,
        "patient": _serialize(patient),
        "positions": [_serialize(p) for p in positions],
        "issues": visible_issues,
        "dismissed_issues": dismissed,
        "instance_id": inst.id,
    }


@router.post("/fall/{fall_id}/dismiss")
async def dismiss(
    fall_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    body: dict[str, Any] = Body(...),
):
    await _ensure_access(db, roles)
    rule_id = body.get("rule_id")
    position_ids = body.get("position_ids") or []
    note = (body.get("note") or "").strip()
    if not rule_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "rule_id required")

    inst = await _get_or_create_fall_instance(db, fall_id)
    tid = uuid.uuid4().hex
    db.add(Transition(
        id=tid, process_instance_id=inst.id, actor=user.id,
        type="issue_dismissed_false_positive",
        payload={"rule_id": rule_id, "position_ids": position_ids, "note": note},
        feeds_back=True,
    ))
    await db.commit()
    return {"id": tid}


@router.post("/fall/{fall_id}/mark-ready")
async def mark_ready(
    fall_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    await _ensure_access(db, roles)
    inst = await _get_or_create_fall_instance(db, fall_id)
    tid = uuid.uuid4().hex
    db.add(Transition(
        id=tid, process_instance_id=inst.id, actor=user.id,
        type="fall_marked_ready_for_billing", payload={"fall_id": fall_id},
        feeds_back=True,
    ))
    inst.status = "done"
    await db.commit()
    return {"id": tid}


async def _get_or_create_fall_instance(db: AsyncSession, fall_id: str) -> ProcessInstance:
    iid = f"rp-{fall_id}"
    inst = await db.get(ProcessInstance, iid)
    if inst is None:
        inst = ProcessInstance(
            id=iid, process_id=PROCESS_ID, title=f"Prüfung: {fall_id}",
            created_by=None, status="open",
            current_state={"fall_id": fall_id},
        )
        db.add(inst)
        await db.flush()
    return inst
