"""Authenticated endpoints for the Anamnesebogen tool — used by MFAs to
review/edit submitted forms and trigger prose regeneration.
"""
from __future__ import annotations
import uuid
from pathlib import Path
from typing import Annotated, Any

import aiofiles
from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..anamnese.prose import generate_anamnese_prose
from ..anamnese.patientenhinweise_parser import parse_patientenhinweise_image
from ..auth import get_current_user, get_current_user_roles
from ..config import get_settings
from ..db import get_db
from ..models import ProcessInstance, Transition, User
from .processes import _check_access

router = APIRouter(prefix="/api/anamnese", tags=["anamnese"])
_settings = get_settings()


@router.post("/upload-patientenhinweise", status_code=201)
async def upload_patientenhinweise(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    file: UploadFile = File(...),
):
    """Upload a screenshot of MO's Patientenhinweise window. OCR + parse to
    structured answers + generate anamnesis prose. The workaround for MO's
    broken text-selection in that window."""
    await _check_access(db, "anamnesebogen", roles)

    # Save to a scratch path
    ext = Path(file.filename or "shot.png").suffix or ".png"
    scratch = _settings.audio_path / f"phinweise_{uuid.uuid4().hex}{ext}"
    async with aiofiles.open(scratch, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            await f.write(chunk)

    try:
        answers, raw_text = parse_patientenhinweise_image(str(scratch))
    finally:
        try:
            scratch.unlink()
        except Exception:
            pass

    if not answers:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Aus dem Screenshot konnten keine Felder extrahiert werden — bitte "
            "klare Aufnahme des Patientenhinweise-Fensters verwenden.",
        )

    prose = generate_anamnese_prose(answers)
    iid = uuid.uuid4().hex
    inst = ProcessInstance(
        id=iid,
        process_id="anamnesebogen",
        title=f"Anamnese: Patientenhinweise-Import {iid[:6]}",
        created_by=user.id,
        status="open",
        current_state={
            "name": "Patientenhinweise-Import",
            "answers": answers,
            "anamnese_prose": prose,
            "source": "patientenhinweise_screenshot",
            "raw_ocr": raw_text,
        },
    )
    db.add(inst)
    db.add(Transition(
        id=uuid.uuid4().hex,
        process_instance_id=iid,
        actor=user.id,
        type="form_submitted",
        payload={"source": "patientenhinweise_screenshot"},
        feeds_back=False,
    ))
    await db.commit()
    return {"id": iid, "anamnese_prose": prose, "n_fields": len(answers)}


@router.post("/regenerate-prose/{instance_id}")
async def regenerate_prose(
    instance_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    answers: Annotated[dict[str, Any] | None, Body(embed=True)] = None,
):
    """Re-generate the anamnesis prose. If `answers` is provided, replaces
    the stored answers and regenerates; otherwise re-uses stored answers.
    Useful when the MFA edits a checkbox or adds context before copying to MO.
    """
    await _check_access(db, "anamnesebogen", roles)
    inst = await db.get(ProcessInstance, instance_id)
    if not inst or inst.process_id != "anamnesebogen":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "anamnese instance not found")
    state = dict(inst.current_state or {})
    if answers is not None:
        state["answers"] = answers
    use_answers = state.get("answers") or {}
    prose = generate_anamnese_prose(use_answers)
    state["anamnese_prose"] = prose
    inst.current_state = state
    db.add(Transition(
        id=uuid.uuid4().hex,
        process_instance_id=instance_id,
        actor=user.id,
        type="form_reviewed",
        payload={"regenerated": True},
        feeds_back=True,
    ))
    await db.commit()
    return {"anamnese_prose": prose}


@router.post("/seed-demo", status_code=201)
async def seed_demo_submission(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
    mode: Annotated[str, Body(embed=True)] = "praxis_eigen",
):
    """Create a demo anamnesebogen submission.

    Two modes:
    - `infoskop`: simulates a parsed Infoskop PDF — limited coverage, mostly
      Y/N categorical data, no current symptom narrative, no Miktionsbeschwerden
      detail. Shows the value-ceiling of the third-party Infoskop integration.
    - `praxis_eigen`: simulates a submission from the practice's own urology-
      customized form — much richer, includes Anliegen heute + Miktionsbeschwerden
      module. Shows what a custom Anamnesebogen can capture.
    """
    from ..anamnese.infoskop_demo import pick_infoskop_demo, pick_praxis_demo

    await _check_access(db, "anamnesebogen", roles)

    if mode == "infoskop":
        chosen = pick_infoskop_demo()
        source = "infoskop_demo"
    else:
        chosen = pick_praxis_demo()
        source = "praxis_eigen_demo"

    answers = chosen["answers"]
    prose = generate_anamnese_prose(answers)
    iid = uuid.uuid4().hex
    state = {
        "name": chosen["name"],
        "dob": chosen["dob"],
        "answers": answers,
        "anamnese_prose": prose,
        "source": source,
        "infoskop_coverage_note": chosen.get("infoskop_coverage_note", ""),
    }
    inst = ProcessInstance(
        id=iid,
        process_id="anamnesebogen",
        title=f"Anamnese: {chosen['name']}",
        created_by=user.id,
        status="open",
        current_state=state,
    )
    db.add(inst)
    db.add(Transition(
        id=uuid.uuid4().hex,
        process_instance_id=iid,
        actor=user.id,
        type="form_submitted",
        payload={"source": source},
        feeds_back=False,
    ))
    await db.commit()
    return {"id": iid, "anamnese_prose": prose, "name": chosen["name"], "source": source}
