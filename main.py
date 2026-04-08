from __future__ import annotations
import asyncio
import json
import shutil
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
def create_session(patient_ref: str = Form(...)):
    return db.create_session(patient_ref)


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
            # Send current state immediately
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
        vocab_terms = vocab_mod.get_all()
        transcript = await loop.run_in_executor(
            None, transcribe.transcribe, audio_path, vocab_terms
        )
        db.update_session(sid, transcript=transcript)
        _notify(sid, {"type": "transcript", "transcript": transcript, "message": "Auswertung läuft..."})

        session = db.get_session(sid)
        ocr_text = session.get("ocr_text") or ""
        extracted = await loop.run_in_executor(
            None, llm.extract_fields, transcript, ocr_text
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
        db.update_session(sid, status="error")
        _notify(sid, {"type": "error", "message": str(e)})


async def _process_form(sid: str, form_path: str):
    loop = asyncio.get_event_loop()
    try:
        ocr_text = await loop.run_in_executor(None, ocr.extract_text, form_path)
        db.update_session(sid, ocr_text=ocr_text)
        _notify(sid, {"type": "ocr", "ocr_text": ocr_text, "message": "OCR abgeschlossen"})

        # If transcript already present, re-run extraction with OCR data
        session = db.get_session(sid)
        if session.get("transcript"):
            extracted = await loop.run_in_executor(
                None, llm.extract_fields, session["transcript"], ocr_text
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
