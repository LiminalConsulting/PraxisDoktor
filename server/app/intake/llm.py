from __future__ import annotations
import json
from dataclasses import dataclass
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma4:e4b"


class OllamaUnavailable(Exception):
    pass


@dataclass
class Profile:
    id: str
    label: str
    description: str
    fields: list[str]
    labels: dict[str, str]
    prompt: str  # uses {transcript}, {ocr_text}, {known_names_block} placeholders


KNOWN_NAMES_TEMPLATE = """
WICHTIG – Bekannte Namen: Die folgenden Namen sind bereits bekannt und korrekt geschrieben. \
Falls im Transkript ähnlich klingende, falsch transkribierte Varianten erscheinen \
(z.B. Tippfehler, phonetische Fehler der Spracherkennung), verwende stattdessen die korrekte Schreibweise:
{names_list}
"""

# ============================================================================
# Profile A: STAMMDATEN — Patient master data (front-desk MFA workflow)
# ============================================================================

STAMMDATEN = Profile(
    id="stammdaten",
    label="Patientenaufnahme — Stammdaten",
    description=(
        "Extrahiert Patienten-Stammdaten aus Aufnahmegespräch oder Anamnesebogen. "
        "Mappt 1:1 auf die `patstamm`-Tabelle in Medical Office."
    ),
    fields=[
        "nachname", "vorname", "geburtsdatum", "geschlecht",
        "titel", "anrede", "strasse", "hausnr", "plz", "ort",
        "telefon_privat", "telefon_mobil", "email", "muttersprache",
    ],
    labels={
        "nachname": "Nachname",
        "vorname": "Vorname",
        "geburtsdatum": "Geburtsdatum",
        "geschlecht": "Geschlecht",
        "titel": "Titel",
        "anrede": "Anrede",
        "strasse": "Straße",
        "hausnr": "Hausnr.",
        "plz": "PLZ",
        "ort": "Ort",
        "telefon_privat": "Telefon (privat)",
        "telefon_mobil": "Telefon (mobil)",
        "email": "E-Mail",
        "muttersprache": "Muttersprache",
    },
    prompt="""Du bist ein medizinischer Assistent. Extrahiere aus dem folgenden Transkript \
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
""",
)

# ============================================================================
# Profile B: KLINISCH — Clinical Anamnese extraction (doctor in Sprechzimmer)
# ============================================================================

KLINISCH = Profile(
    id="klinisch",
    label="Anamnese / Befund — Klinisch",
    description=(
        "Extrahiert klinische Daten aus einem Anamnesegespräch zwischen Arzt und Patient. "
        "Schlägt Verdachtsdiagnose, ICD-10-Code und passende EBM-Ziffern vor."
    ),
    fields=[
        "hauptsymptom", "dauer", "lokalisation",
        "begleitsymptome", "fieber", "haematurie",
        "verdachtsdiagnose", "icd10_vorschlag",
        "empfohlene_diagnostik", "empfohlene_gops",
    ],
    labels={
        "hauptsymptom": "Hauptsymptom",
        "dauer": "Dauer",
        "lokalisation": "Lokalisation",
        "begleitsymptome": "Begleitsymptome",
        "fieber": "Fieber",
        "haematurie": "Hämaturie (Blut im Urin)",
        "verdachtsdiagnose": "Verdachtsdiagnose",
        "icd10_vorschlag": "ICD-10 Vorschlag",
        "empfohlene_diagnostik": "Empfohlene Diagnostik",
        "empfohlene_gops": "Empfohlene EBM-Ziffern",
    },
    prompt="""Du bist ein medizinischer Assistent in einer urologischen Praxis.
Extrahiere aus dem folgenden Transkript eines Anamnesegesprächs strukturierte klinische Daten.

Antworte NUR mit einem JSON-Objekt mit diesen Feldern:
- hauptsymptom: Das wichtigste Symptom in 3-6 Wörtern
- dauer: Wie lange besteht das Symptom (z.B. "3 Wochen")
- lokalisation: Wo am Körper (z.B. "Harnröhre", "Bauch")
- begleitsymptome: Liste anderer Symptome (als Array von Strings)
- fieber: "ja", "nein" oder "unklar"
- haematurie: "ja", "nein" oder "unklar" (Blut im Urin)
- verdachtsdiagnose: Wahrscheinliche Diagnose in Worten
- icd10_vorschlag: Passender ICD-10 Code (nur Code, z.B. "N30.0")
- empfohlene_diagnostik: Liste empfohlener nächster Schritte (Array)
- empfohlene_gops: Liste passender EBM-Ziffern (Array von Strings, z.B. ["32030", "32125"])

Wenn ein Feld nicht ableitbar ist, setze es auf null oder leere Liste.
Keine Erklärungen, kein Markdown – nur das JSON-Objekt.
{known_names_block}
Transkript:
{transcript}

Anamnesebogen (OCR):
{ocr_text}
""",
)


PROFILES: dict[str, Profile] = {
    STAMMDATEN.id: STAMMDATEN,
    KLINISCH.id: KLINISCH,
}

DEFAULT_PROFILE = STAMMDATEN.id

# Backward-compatible exports for callers using the old API
FIELDS = STAMMDATEN.fields


def get_profile(profile_id: str | None) -> Profile:
    if profile_id and profile_id in PROFILES:
        return PROFILES[profile_id]
    return PROFILES[DEFAULT_PROFILE]


def extract_fields(
    transcript: str,
    ocr_text: str,
    patient_ref: str = "",
    doctor_name: str = "",
    profile_id: str | None = None,
) -> dict:
    """Extract structured fields from a transcript using the chosen profile.

    Raises OllamaUnavailable if the Ollama HTTP endpoint is unreachable or
    returns an error status. Returns a dict with one key per profile field;
    missing values are None / [].
    """
    profile = get_profile(profile_id)

    known_names_block = ""
    names = [n.strip() for n in [patient_ref, doctor_name] if n and n.strip()]
    if names:
        names_list = "\n".join(f"- {n}" for n in names)
        known_names_block = KNOWN_NAMES_TEMPLATE.format(names_list=names_list)

    prompt = profile.prompt.format(
        transcript=transcript or "(keine Aufnahme)",
        ocr_text=ocr_text or "(kein Formular)",
        known_names_block=known_names_block,
    )

    try:
        resp = httpx.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=180.0,
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise OllamaUnavailable(f"Ollama nicht erreichbar: {e}") from e

    raw = resp.json().get("response", "").strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError:
        # Recover by returning empty fields rather than crashing the pipeline
        data = {}

    # Normalize: ensure every profile field is present, even if null/empty
    result = {}
    for f in profile.fields:
        v = data.get(f)
        # Handle the gemma4 typo case ("begleitymptome" missing 's')
        if v is None and f == "begleitsymptome":
            v = data.get("begleitymptome")
        result[f] = v
    return result
