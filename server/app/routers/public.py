"""Public-facing endpoints called by the Cloudflare Pages site over the tunnel.
Authenticated by a single shared secret (env PUBLIC_API_KEY or auto-persisted file).
Each call writes a new ProcessInstance + initial Transition into the corresponding
process. Staff then act on it via the normal dashboard tools.

These are the only endpoints the public internet can reach. Everything else is
session-cookie protected and reachable only by authenticated practice staff."""
from __future__ import annotations
import time
import uuid
from collections import deque
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_db
from ..models import ProcessInstance, Transition

router = APIRouter(prefix="/api/public", tags=["public"])


# Tiny in-process rate limiter. 30 reqs / IP / minute is plenty for a public form.
# Survives only as long as the process — fine; abuse beyond this gets a 429 and the
# tunnel/CF Access layer can take over if it ever matters.
_RATE_WINDOW_SEC = 60
_RATE_MAX = 30
_recent: dict[str, deque[float]] = {}


def _check_rate(ip: str) -> None:
    now = time.monotonic()
    bucket = _recent.setdefault(ip, deque())
    while bucket and bucket[0] < now - _RATE_WINDOW_SEC:
        bucket.popleft()
    if len(bucket) >= _RATE_MAX:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "rate limit")
    bucket.append(now)


def _require_public_key(
    request: Request,
    x_public_key: Annotated[str | None, Header(alias="X-Public-Key")] = None,
) -> None:
    expected = get_settings().public_api_key
    if not expected or x_public_key != expected:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid public key")
    client_ip = request.client.host if request.client else "unknown"
    _check_rate(client_ip)


async def _open_instance(
    db: AsyncSession,
    process_id: str,
    title: str,
    initial_transition_type: str,
    payload: dict[str, Any],
) -> str:
    iid = uuid.uuid4().hex
    db.add(ProcessInstance(
        id=iid,
        process_id=process_id,
        title=title,
        created_by=None,  # public submission, no internal user
        status="open",
        current_state={"source": "public_site", **payload},
    ))
    db.add(Transition(
        id=uuid.uuid4().hex,
        process_instance_id=iid,
        actor="public_site",
        type=initial_transition_type,
        payload=payload,
        feeds_back=False,
    ))
    await db.commit()
    return iid


@router.post("/booking-request", status_code=201, dependencies=[Depends(_require_public_key)])
async def booking_request(
    db: Annotated[AsyncSession, Depends(get_db)],
    body: Annotated[dict[str, Any], Body()] = ...,
):
    """Patient (or prospective patient) requests an appointment via the public site.
    Staff confirm/reschedule/decline via the Terminverwaltung tool."""
    name = (body.get("name") or "").strip()
    contact = (body.get("contact") or "").strip()  # phone or email
    reason = (body.get("reason") or "").strip()
    desired = (body.get("desired_slot") or "").strip()  # free-text / ISO / range
    is_new = bool(body.get("is_new_patient", False))

    if not name or not contact:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "name and contact required")

    title = f"Termin: {name}"
    iid = await _open_instance(
        db, "termin_uebersicht", title, "booking_requested",
        {"name": name, "contact": contact, "reason": reason,
         "desired_slot": desired, "is_new_patient": is_new},
    )
    return {"id": iid, "ok": True}


@router.post("/anamnese-submit", status_code=201, dependencies=[Depends(_require_public_key)])
async def anamnese_submit(
    db: Annotated[AsyncSession, Depends(get_db)],
    body: Annotated[dict[str, Any], Body()] = ...,
):
    """Patient submits a filled-in anamnesis form from the public site.
    Staff review and attach to the patient record via the Anamnesebögen tool."""
    name = (body.get("name") or "").strip()
    dob = (body.get("dob") or "").strip()
    answers = body.get("answers") or {}

    if not name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "name required")
    if not isinstance(answers, dict):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "answers must be object")

    title = f"Anamnese: {name}"
    iid = await _open_instance(
        db, "anamnesebogen", title, "form_submitted",
        {"name": name, "dob": dob, "answers": answers},
    )
    return {"id": iid, "ok": True}


@router.post("/anamnese-start", status_code=201, dependencies=[Depends(_require_public_key)])
async def anamnese_start(
    db: Annotated[AsyncSession, Depends(get_db)],
    body: Annotated[dict[str, Any], Body()] = ...,
):
    """Optional ping: patient opened the form link. Lets staff see in-progress forms."""
    name = (body.get("name") or "anonym").strip()
    title = f"Anamnese: {name} (offen)"
    iid = await _open_instance(
        db, "anamnesebogen", title, "form_started",
        {"name": name},
    )
    return {"id": iid, "ok": True}
