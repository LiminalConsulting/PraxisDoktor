"""
Read-only Patientenakte router. Wraps the MO adapter; never writes.

The /api/patientenakte/* endpoints are session-cookie protected (every staff
role can read; access enforced by `get_current_user_roles` + the process's
ProcessRoleAccess entries).

Coherence-issue dismissal IS a write — but a write into our own DB
(transition log on the patientenakte process), not into MO.
"""
from __future__ import annotations
import uuid
from typing import Annotated, Any
from dataclasses import asdict
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, get_current_user_roles
from ..db import get_db
from ..medical_office import (
    get_adapter, check_coherence,
    SchemaNotGrounded,
)
from ..medical_office.coherence import check_patient
from ..models import Process, ProcessRoleAccess, ProcessInstance, Transition, User

router = APIRouter(prefix="/api/patientenakte", tags=["patientenakte"])

PROCESS_ID = "patientenakte"


def _serialize(obj: Any) -> Any:
    """dataclass → dict, with date/datetime ISO."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _serialize(v) for k, v in asdict(obj).items()}
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, list):
        return [_serialize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


async def _ensure_access(db: AsyncSession, roles: list[str]) -> None:
    proc = await db.get(Process, PROCESS_ID)
    if proc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "patientenakte process not registered")
    from sqlalchemy import select
    res = await db.execute(
        select(ProcessRoleAccess).where(
            ProcessRoleAccess.process_id == PROCESS_ID,
            ProcessRoleAccess.role_id.in_(roles),
        )
    )
    if res.first() is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "no access to patientenakte")


@router.get("/_meta")
async def meta(
    db: Annotated[AsyncSession, Depends(get_db)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    """Returns the active adapter + which record kinds are grounded.
    The frontend renders the AmbiguityBanner from this."""
    await _ensure_access(db, roles)
    a = get_adapter()
    return {
        "adapter": a.name,
        "grounded_kinds": list(a.grounded_kinds),
        "ungrounded_kinds": [k for k in ("patient", "fall", "befund", "abrechnung")
                              if k not in a.grounded_kinds],
    }


@router.get("/patients")
async def list_patients(
    db: Annotated[AsyncSession, Depends(get_db)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    q: str = Query("", description="Search by name / id / PLZ"),
    limit: int = Query(50, le=200),
):
    await _ensure_access(db, roles)
    a = get_adapter()
    patients = a.search_patients(q, limit=limit) if q else a.list_patients(limit=limit)
    return {"adapter": a.name, "patients": [_serialize(p) for p in patients]}


@router.get("/patients/{patient_id}")
async def get_patient(
    patient_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    await _ensure_access(db, roles)
    a = get_adapter()
    p = a.get_patient(patient_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "patient not found")

    # Pull related records, swallowing SchemaNotGrounded into structured "blocked" markers
    def _try(fn, *args):
        try:
            return {"grounded": True, "data": [_serialize(x) for x in fn(*args)]}
        except SchemaNotGrounded as e:
            return {"grounded": False, "reason": str(e), "data": []}

    faelle = _try(a.list_faelle_for_patient, patient_id)
    befunde = _try(a.list_befunde_for_patient, patient_id)

    # Log the view (privacy-relevant: who looked at whom and when)
    iid = await _record_view_transition(db, user.id, patient_id)

    issues = [_serialize(i) for i in check_patient(p)]

    return {
        "adapter": a.name,
        "patient": _serialize(p),
        "faelle": faelle,
        "befunde": befunde,
        "coherence_issues": issues,
        "view_transition_id": iid,
    }


@router.get("/coherence")
async def coherence_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    limit: int = Query(200, le=1000),
):
    """Run the integrity checker over the dataset and return all issues."""
    await _ensure_access(db, roles)
    a = get_adapter()
    issues = check_coherence(a, limit_patients=limit)
    return {
        "adapter": a.name,
        "scanned_patients": min(limit, len(a.list_patients(limit=limit))),
        "issue_count": len(issues),
        "issues": [_serialize(i) for i in issues],
    }


@router.post("/coherence/dismiss")
async def dismiss_issue(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    body: dict[str, Any] = ...,
):
    """Mark a coherence issue as dismissed (e.g. 'known false-positive').
    Stored as a transition on a per-patient process instance."""
    await _ensure_access(db, roles)
    record_id = (body.get("record_id") or "").strip()
    rule = (body.get("rule") or "").strip()
    note = (body.get("note") or "").strip()
    if not record_id or not rule:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "record_id and rule required")

    inst = await _get_or_create_patient_instance(db, record_id)
    tid = uuid.uuid4().hex
    db.add(Transition(
        id=tid, process_instance_id=inst.id, actor=user.id,
        type="coherence_issue_dismissed",
        payload={"record_id": record_id, "rule": rule, "note": note},
        feeds_back=True,
    ))
    await db.commit()
    return {"id": tid}


# ---------------------------------------------------------------------------
# Internal helpers — manage one ProcessInstance per viewed patient.
# ---------------------------------------------------------------------------

async def _get_or_create_patient_instance(db: AsyncSession, patient_id: str) -> ProcessInstance:
    """One ProcessInstance per patient — viewing-session events live there."""
    from sqlalchemy import select
    iid = f"pakte-{patient_id}"
    inst = await db.get(ProcessInstance, iid)
    if inst is None:
        inst = ProcessInstance(
            id=iid, process_id=PROCESS_ID, title=f"Akte: {patient_id}",
            created_by=None, status="open",
            current_state={"patient_id": patient_id, "source": "medical_office"},
        )
        db.add(inst)
        await db.flush()
    return inst


async def _record_view_transition(db: AsyncSession, actor: str, patient_id: str) -> str:
    inst = await _get_or_create_patient_instance(db, patient_id)
    tid = uuid.uuid4().hex
    db.add(Transition(
        id=tid, process_instance_id=inst.id, actor=actor,
        type="patient_viewed", payload={"patient_id": patient_id}, feeds_back=False,
    ))
    await db.commit()
    return tid
