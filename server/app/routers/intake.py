"""Patient intake endpoints — audio upload, OCR upload, run extraction.
Uses the persistent jobs queue so in-flight work survives restarts."""
from __future__ import annotations
import uuid
from pathlib import Path
from typing import Annotated

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import jobs
from ..auth import get_current_user, get_current_user_roles
from ..config import get_settings
from ..db import get_db
from ..intake.health import ollama_status
from ..models import ProcessInstance, Transition, User
from ..routers.processes import _check_access
from ..ws import broadcast

router = APIRouter(prefix="/api/intake", tags=["intake"])
_settings = get_settings()


def _audio_path_for(instance_id: str, suffix: str) -> Path:
    return _settings.audio_path / f"{instance_id}{suffix}"


async def _emit_transition(
    db: AsyncSession, instance_id: str, actor: str, ttype: str, payload: dict, feeds_back: bool = False
) -> str:
    tid = uuid.uuid4().hex
    db.add(Transition(
        id=tid,
        process_instance_id=instance_id,
        actor=actor,
        type=ttype,
        payload=payload,
        feeds_back=feeds_back,
    ))
    await db.commit()
    await broadcast(f"process:patient_intake:{instance_id}", {
        "type": "transition",
        "transition": {"id": tid, "type": ttype, "payload": payload, "actor": actor},
    })
    return tid


async def _save_upload(file: UploadFile, dest: Path) -> None:
    async with aiofiles.open(dest, "wb") as out:
        while chunk := await file.read(64 * 1024):
            await out.write(chunk)


@router.get("/health")
async def health(_: Annotated[User, Depends(get_current_user)]):
    return {"ollama": ollama_status()}


@router.post("/{instance_id}/audio")
async def upload_audio(
    instance_id: str,
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    await _check_access(db, "patient_intake", roles)
    inst = await db.get(ProcessInstance, instance_id)
    if not inst or inst.process_id != "patient_intake":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "instance not found")

    suffix = Path(file.filename or "").suffix or ".webm"
    audio_path = _audio_path_for(instance_id, suffix)
    await _save_upload(file, audio_path)

    state = dict(inst.current_state or {})
    state["audio_path"] = str(audio_path)
    state["status"] = "transcribing"
    state.pop("error", None)
    inst.current_state = state
    inst.status = "processing"
    await db.commit()

    await _emit_transition(db, instance_id, user.id, "audio_uploaded", {"path": str(audio_path)})
    await jobs.enqueue(
        "intake_pipeline",
        {"instance_id": instance_id, "audio_path": str(audio_path), "actor": user.id},
        process_instance_id=instance_id,
    )
    return {"ok": True}


@router.post("/{instance_id}/form")
async def upload_form(
    instance_id: str,
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    roles: Annotated[list[str], Depends(get_current_user_roles)],
):
    await _check_access(db, "patient_intake", roles)
    inst = await db.get(ProcessInstance, instance_id)
    if not inst or inst.process_id != "patient_intake":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "instance not found")

    suffix = Path(file.filename or "").suffix or ".png"
    form_path = _audio_path_for(instance_id, f"_form{suffix}")
    await _save_upload(file, form_path)

    state = dict(inst.current_state or {})
    state["form_path"] = str(form_path)
    inst.current_state = state
    await db.commit()

    await _emit_transition(db, instance_id, user.id, "form_uploaded", {"path": str(form_path)})
    await jobs.enqueue(
        "intake_ocr",
        {"instance_id": instance_id, "form_path": str(form_path), "actor": user.id},
        process_instance_id=instance_id,
    )
    return {"ok": True}
