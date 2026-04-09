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
{known_names_block}
Transkript:
{transcript}

Anamnesebogen (OCR):
{ocr_text}
"""

KNOWN_NAMES_TEMPLATE = """\

WICHTIG – Bekannte Namen: Die folgenden Namen sind bereits bekannt und korrekt geschrieben. \
Falls im Transkript ähnlich klingende, falsch transkribierte Varianten erscheinen \
(z.B. Tippfehler, phonetische Fehler der Spracherkennung), verwende stattdessen die korrekte Schreibweise:
{names_list}
"""


def extract_fields(
    transcript: str,
    ocr_text: str,
    patient_ref: str = "",
    doctor_name: str = "",
) -> dict:
    known_names_block = ""
    names = [n.strip() for n in [patient_ref, doctor_name] if n and n.strip()]
    if names:
        names_list = "\n".join(f"- {n}" for n in names)
        known_names_block = KNOWN_NAMES_TEMPLATE.format(names_list=names_list)

    prompt = PROMPT_TEMPLATE.format(
        transcript=transcript or "(keine Aufnahme)",
        ocr_text=ocr_text or "(kein Formular)",
        known_names_block=known_names_block,
    )
    try:
        resp = httpx.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=120.0,
        )
        resp.raise_for_status()
        raw = resp.json().get("response", "")
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
    except Exception:
        data = {}

    return {f: data.get(f) for f in FIELDS}
