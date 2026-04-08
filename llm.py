from __future__ import annotations
import json
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"

FIELDS = [
    "nachname", "vorname", "geburtsdatum", "geschlecht",
    "titel", "anrede", "strasse", "hausnr", "plz", "ort",
    "telefon_privat", "telefon_mobil", "email", "muttersprache",
]

PROMPT_TEMPLATE = """\
Du bist ein medizinischer Assistent. Extrahiere aus dem folgenden Transkript \
eines Erstgesprächs in einer urologischen Praxis die Patientendaten.
Antworte NUR mit einem JSON-Objekt mit diesen Feldern:
nachname, vorname, geburtsdatum (Format TTMMJJJJ), geschlecht (M oder W),
titel, anrede, strasse, hausnr, plz, ort, telefon_privat, telefon_mobil, email, muttersprache

Wenn ein Feld nicht gefunden werden kann, setze es auf null.
Keine Erklärungen, kein Markdown – nur das JSON-Objekt.

Transkript:
{transcript}

Anamnesebogen (OCR):
{ocr_text}
"""


def extract_fields(transcript: str, ocr_text: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        transcript=transcript or "(keine Aufnahme)",
        ocr_text=ocr_text or "(kein Formular)",
    )
    try:
        resp = httpx.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=120.0,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "")
        # Strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
    except Exception:
        data = {}

    # Normalise: ensure all expected fields present, fill missing with None
    return {f: data.get(f) for f in FIELDS}
