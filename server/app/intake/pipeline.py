"""Intake job handlers — registered with the jobs dispatcher.

These replace the old fire-and-forget asyncio.create_task pattern, so
in-flight transcription/extraction/OCR survives a server restart."""
from __future__ import annotations
import asyncio
from typing import Any

from ..db import SessionLocal
from ..models import ProcessInstance
from ..ws import broadcast
from . import transcribe as t_mod
from . import ocr as o_mod
from . import llm as l_mod
from . import vocab as v_mod


async def run_intake_pipeline(payload: dict[str, Any]) -> None:
    instance_id = payload["instance_id"]
    audio_path = payload["audio_path"]
    loop = asyncio.get_event_loop()

    async with SessionLocal() as db:
        inst = await db.get(ProcessInstance, instance_id)
        if not inst:
            return
        patient_ref = (inst.current_state or {}).get("patient_ref", "") or inst.title
        doctor_name = (inst.current_state or {}).get("doctor_name", "")
        prior_ocr = (inst.current_state or {}).get("ocr_text", "")

    # build vocab
    vocab_terms = v_mod.get_all()
    for n in [patient_ref, doctor_name]:
        if n:
            for part in n.replace(",", " ").split():
                part = part.strip()
                if part and len(part) > 1 and part not in vocab_terms:
                    vocab_terms.append(part)

    # transcribe
    transcript = await loop.run_in_executor(None, t_mod.transcribe, audio_path, vocab_terms)
    async with SessionLocal() as db:
        inst = await db.get(ProcessInstance, instance_id)
        if inst:
            state = dict(inst.current_state or {})
            state["transcript"] = transcript
            state["status"] = "extracting"
            inst.current_state = state
            await db.commit()
            await broadcast(f"process:patient_intake:{instance_id}", {
                "type": "transcript_ready",
                "transcript": transcript,
            })

    # extract
    try:
        extracted = await loop.run_in_executor(
            None, l_mod.extract_fields, transcript, prior_ocr, patient_ref, doctor_name
        )
        extraction_error = None
    except l_mod.OllamaUnavailable as e:
        extracted = {}
        extraction_error = str(e)

    async with SessionLocal() as db:
        inst = await db.get(ProcessInstance, instance_id)
        if not inst:
            return
        state = dict(inst.current_state or {})
        if extraction_error:
            state["error"] = extraction_error
            state["status"] = "error"
            inst.status = "error"
        else:
            state["extracted"] = extracted
            state["status"] = "ready"
            fields = {
                k: {"value": v, "status": "pending"}
                for k, v in extracted.items()
                if v is not None
            }
            # preserve any user-edited fields from an earlier run
            existing_fields = state.get("fields") or {}
            for k, v in fields.items():
                if k not in existing_fields:
                    existing_fields[k] = v
            state["fields"] = existing_fields
            inst.status = "ready"
        inst.current_state = state
        await db.commit()
        await broadcast(f"process:patient_intake:{instance_id}", {
            "type": "extraction_ready" if not extraction_error else "extraction_error",
            "extracted": extracted,
            "error": extraction_error,
        })


async def run_intake_ocr(payload: dict[str, Any]) -> None:
    instance_id = payload["instance_id"]
    form_path = payload["form_path"]
    loop = asyncio.get_event_loop()

    ocr_text = await loop.run_in_executor(None, o_mod.extract_text, form_path)
    async with SessionLocal() as db:
        inst = await db.get(ProcessInstance, instance_id)
        if not inst:
            return
        state = dict(inst.current_state or {})
        state["ocr_text"] = ocr_text
        inst.current_state = state
        await db.commit()
        await broadcast(f"process:patient_intake:{instance_id}", {
            "type": "ocr_ready",
            "ocr_text": ocr_text,
        })
