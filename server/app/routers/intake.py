"""Patient intake endpoints — audio upload, OCR upload, run extraction.
Bridges the new ProcessInstance/Transition model with the v1 ML pipeline."""
from __future__ import annotations
import asyncio
import json
import uuid
from pathlib import Path
from typing import Annotated

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, get_current_user_roles
from ..config import get_settings
from ..db import get_db
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
    inst.current_state = state
    inst.status = "processing"
    await db.commit()

    await _emit_transition(db, instance_id, user.id, "audio_uploaded", {"path": str(audio_path)})

    asyncio.create_task(_run_pipeline(instance_id, str(audio_path), user.id))
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

    asyncio.create_task(_run_ocr(instance_id, str(form_path), user.id))
    return {"ok": True}


# --- background work ---

async def _run_pipeline(instance_id: str, audio_path: str, actor: str) -> None:
    """Transcribe → extract. Heavy lifting offloaded to thread executor."""
    from ..db import SessionLocal
    from ..intake import transcribe as t_mod, llm as l_mod, vocab as v_mod

    loop = asyncio.get_event_loop()
    try:
        async with SessionLocal() as db:
            inst = await db.get(ProcessInstance, instance_id)
            if not inst:
                return
            patient_ref = (inst.current_state or {}).get("patient_ref", "") or inst.title
            doctor_name = (inst.current_state or {}).get("doctor_name", "")

        vocab_terms = v_mod.get_all()
        for n in [patient_ref, doctor_name]:
            if n:
                for part in n.replace(",", " ").split():
                    part = part.strip()
                    if part and len(part) > 1 and part not in vocab_terms:
                        vocab_terms.append(part)

        transcript = await loop.run_in_executor(None, t_mod.transcribe, audio_path, vocab_terms)

        async with SessionLocal() as db:
            inst = await db.get(ProcessInstance, instance_id)
            state = dict(inst.current_state or {})
            state["transcript"] = transcript
            state["status"] = "extracting"
            inst.current_state = state
            await db.commit()
            await _emit_transition(db, instance_id, "system", "transcript_ready", {"transcript": transcript})

        ocr_text = (state.get("ocr_text") or "")
        extracted = await loop.run_in_executor(
            None, l_mod.extract_fields, transcript, ocr_text, patient_ref, doctor_name
        )

        async with SessionLocal() as db:
            inst = await db.get(ProcessInstance, instance_id)
            state = dict(inst.current_state or {})
            state["extracted"] = extracted
            state["status"] = "ready"
            # initial fields-projection from extraction (status: pending until accepted/corrected/rejected)
            fields = {k: {"value": v, "status": "pending"} for k, v in extracted.items() if v is not None}
            state["fields"] = fields
            inst.current_state = state
            inst.status = "ready"
            await db.commit()
            await _emit_transition(db, instance_id, "system", "extraction_ready", {"extracted": extracted})

    except Exception as e:
        async with SessionLocal() as db:
            inst = await db.get(ProcessInstance, instance_id)
            if inst:
                state = dict(inst.current_state or {})
                state["error"] = str(e)
                state["status"] = "error"
                inst.current_state = state
                inst.status = "error"
                await db.commit()
                await broadcast(f"process:patient_intake:{instance_id}", {
                    "type": "error", "message": str(e),
                })


async def _run_ocr(instance_id: str, form_path: str, actor: str) -> None:
    from ..db import SessionLocal
    from ..intake import ocr as o_mod

    loop = asyncio.get_event_loop()
    try:
        ocr_text = await loop.run_in_executor(None, o_mod.extract_text, form_path)
        async with SessionLocal() as db:
            inst = await db.get(ProcessInstance, instance_id)
            state = dict(inst.current_state or {})
            state["ocr_text"] = ocr_text
            inst.current_state = state
            await db.commit()
            await broadcast(f"process:patient_intake:{instance_id}", {
                "type": "ocr_ready", "ocr_text": ocr_text,
            })
    except Exception as e:
        await broadcast(f"process:patient_intake:{instance_id}", {
            "type": "error", "message": f"OCR Fehler: {e}",
        })
