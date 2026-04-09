from __future__ import annotations
import asyncio
import json
import uuid
from pathlib import Path
from typing import AsyncGenerator

import aiofiles
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

import db
import vocab as vocab_mod
import transcribe
import ocr
import llm

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

app = FastAPI(title="PraxisDoktor")

# SSE subscribers: session_id -> list of asyncio.Queue
_sse_subscribers: dict[str, list[asyncio.Queue]] = {}


def _notify(sid: str, event: dict):
    for q in _sse_subscribers.get(sid, []):
        q.put_nowait(event)


@app.on_event("startup")
def on_startup():
    db.init_db()
    vocab_mod.ensure_vocab_seeded()


# --- Static files ---
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    async with aiofiles.open(BASE_DIR / "static" / "index.html", encoding="utf-8") as f:
        return await f.read()


# --- Sessions ---

@app.get("/sessions")
def list_sessions():
    return db.list_sessions()


@app.get("/sessions/{sid}")
def get_session(sid: str):
    session = db.get_session(sid)
    if session is None:
        raise HTTPException(404, "Session not found")
    return session


@app.post("/sessions", status_code=201)
def create_session(
    patient_ref: str = Form(...),
    doctor_name: str = Form(default=""),
):
    return db.create_session(patient_ref, doctor_name or None)


@app.post("/sessions/{sid}/audio")
async def upload_audio(sid: str, file: UploadFile = File(...)):
    session = db.get_session(sid)
    if session is None:
        raise HTTPException(404, "Session not found")

    suffix = Path(file.filename).suffix if file.filename else ".webm"
    audio_path = AUDIO_DIR / f"{sid}{suffix}"
    async with aiofiles.open(audio_path, "wb") as out:
        while chunk := await file.read(1024 * 64):
            await out.write(chunk)

    db.update_session(sid, audio_path=str(audio_path), status="processing")
    _notify(sid, {"type": "status", "status": "processing", "message": "Transkription läuft..."})

    asyncio.create_task(_process_audio(sid, str(audio_path)))
    return {"ok": True}


@app.post("/sessions/{sid}/form")
async def upload_form(sid: str, file: UploadFile = File(...)):
    session = db.get_session(sid)
    if session is None:
        raise HTTPException(404, "Session not found")

    suffix = Path(file.filename).suffix if file.filename else ".png"
    form_path = AUDIO_DIR / f"{sid}_form{suffix}"
    async with aiofiles.open(form_path, "wb") as out:
        while chunk := await file.read(1024 * 64):
            await out.write(chunk)

    _notify(sid, {"type": "status", "status": "processing", "message": "OCR läuft..."})
    asyncio.create_task(_process_form(sid, str(form_path)))
    return {"ok": True}


@app.post("/sessions/{sid}/done")
def mark_done(sid: str):
    session = db.get_session(sid)
    if session is None:
        raise HTTPException(404, "Session not found")
    db.mark_done(sid)
    _notify(sid, {"type": "status", "status": "done", "message": "In MediOffice übertragen"})
    return {"ok": True}


@app.get("/sessions/{sid}/stream")
async def stream(sid: str):
    queue: asyncio.Queue = asyncio.Queue()
    _sse_subscribers.setdefault(sid, []).append(queue)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            session = db.get_session(sid)
            if session:
                yield _sse_fmt({"type": "snapshot", "session": session})
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield _sse_fmt(event)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            _sse_subscribers.get(sid, []).remove(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _sse_fmt(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# --- Background jobs ---

async def _process_audio(sid: str, audio_path: str):
    loop = asyncio.get_event_loop()
    try:
        session = db.get_session(sid)
        patient_ref = session.get("patient_ref") or ""
        doctor_name = session.get("doctor_name") or ""

        # Build vocab: base terms + any names present in UI
        vocab_terms = vocab_mod.get_all()
        name_terms = _extract_name_terms(patient_ref, doctor_name)
        all_terms = vocab_terms + [t for t in name_terms if t not in vocab_terms]

        transcript = await loop.run_in_executor(
            None, transcribe.transcribe, audio_path, all_terms
        )
        db.update_session(sid, transcript=transcript)
        _notify(sid, {"type": "transcript", "transcript": transcript, "message": "Auswertung läuft..."})

        # Field extraction
        ocr_text = session.get("ocr_text") or ""
        extracted = await loop.run_in_executor(
            None, llm.extract_fields, transcript, ocr_text, patient_ref, doctor_name
        )
        extracted_json = json.dumps(extracted, ensure_ascii=False)
        db.update_session(sid, extracted=extracted_json, status="ready")
        _notify(sid, {
            "type": "extracted",
            "extracted": extracted,
            "status": "ready",
            "message": "Bereit",
        })

        # Speaker diarization (if enabled) — runs after user sees results
        diarization_enabled = db.get_setting("diarization_enabled", "true") == "true"
        if diarization_enabled:
            _notify(sid, {"type": "status", "status": "ready", "message": "Sprecher werden erkannt..."})
            try:
                import diarize
                doctor_embedding = db.get_doctor_embedding(doctor_name) if doctor_name else None
                diarized = await loop.run_in_executor(
                    None, diarize.diarize, audio_path, transcript, patient_ref, doctor_name, doctor_embedding
                )
                db.update_session(sid, diarized=diarized)
                _notify(sid, {"type": "diarized", "diarized": diarized, "message": "Bereit"})
            except Exception as e:
                # Diarization failure is non-fatal
                _notify(sid, {"type": "status", "status": "ready", "message": f"Bereit (Sprechererkennung fehlgeschlagen: {e})"})

    except Exception as e:
        db.update_session(sid, status="error")
        _notify(sid, {"type": "error", "message": str(e)})


async def _process_form(sid: str, form_path: str):
    loop = asyncio.get_event_loop()
    try:
        ocr_text = await loop.run_in_executor(None, ocr.extract_text, form_path)
        db.update_session(sid, ocr_text=ocr_text)
        _notify(sid, {"type": "ocr", "ocr_text": ocr_text, "message": "OCR abgeschlossen"})

        session = db.get_session(sid)
        if session.get("transcript"):
            patient_ref = session.get("patient_ref") or ""
            doctor_name = session.get("doctor_name") or ""
            extracted = await loop.run_in_executor(
                None, llm.extract_fields, session["transcript"], ocr_text, patient_ref, doctor_name
            )
            extracted_json = json.dumps(extracted, ensure_ascii=False)
            db.update_session(sid, extracted=extracted_json, status="ready")
            _notify(sid, {
                "type": "extracted",
                "extracted": extracted,
                "status": "ready",
                "message": "Bereit",
            })
    except Exception as e:
        _notify(sid, {"type": "error", "message": f"OCR Fehler: {e}"})


def _extract_name_terms(patient_ref: str, doctor_name: str) -> list[str]:
    """Split full names into individual tokens for Whisper vocab injection."""
    terms = []
    for name in [patient_ref, doctor_name]:
        if name:
            for part in name.replace(",", " ").split():
                part = part.strip()
                if part and len(part) > 1:
                    terms.append(part)
    return terms


# --- Vocab ---

@app.get("/vocab")
def get_vocab():
    return vocab_mod.get_all()


@app.post("/vocab", status_code=201)
def add_vocab(term: str = Form(...)):
    vocab_mod.add(term)
    return {"ok": True}


@app.delete("/vocab/{term}")
def delete_vocab(term: str):
    vocab_mod.remove(term)
    return {"ok": True}


# --- Doctors ---

@app.get("/doctors")
def get_doctors():
    return db.get_doctors()


@app.post("/doctors", status_code=201)
def add_doctor(name: str = Form(...)):
    db.add_doctor(name)
    return {"ok": True}


@app.delete("/doctors/{name}")
def delete_doctor(name: str):
    db.remove_doctor(name)
    return {"ok": True}


@app.post("/doctors/{name}/enroll")
async def enroll_doctor(name: str, file: UploadFile = File(...)):
    """Receive a voice sample, compute speaker embedding, store it."""
    import tempfile, os
    doctors = [d["name"] for d in db.get_doctors()]
    if name not in doctors:
        raise HTTPException(404, "Arzt nicht gefunden")

    suffix = Path(file.filename).suffix if file.filename else ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
        while chunk := await file.read(1024 * 64):
            tmp.write(chunk)

    loop = asyncio.get_event_loop()
    try:
        embedding = await loop.run_in_executor(None, _compute_embedding, tmp_path)
    finally:
        os.unlink(tmp_path)

    db.set_doctor_embedding(name, json.dumps(embedding))
    return {"ok": True}


def _compute_embedding(audio_path: str) -> list[float]:
    import torch, torchaudio
    from speechbrain.inference.speaker import EncoderClassifier

    classifier = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        run_opts={"device": "cpu"},
        savedir=str(Path.home() / ".cache" / "speechbrain" / "spkrec-ecapa"),
    )
    waveform, sr = torchaudio.load(audio_path)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    if sr != 16000:
        waveform = torchaudio.transforms.Resample(sr, 16000)(waveform)
    with torch.no_grad():
        emb = classifier.encode_batch(waveform)
    return emb.squeeze().tolist()


# --- Settings ---

@app.get("/settings/{key}")
def get_setting(key: str):
    return {"key": key, "value": db.get_setting(key)}


@app.post("/settings/{key}")
def set_setting(key: str, value: str = Form(...)):
    db.set_setting(key, value)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
