"""
Typed records returned by the MO adapter.

**Grounding status per record:**
- `Patient`        — VERIFIED from v1 intake schema (14 fields).
- `Fall`           — domain-shaped, not MO-grounded yet (`grounded=False`).
- `Befund`         — domain-shaped, not MO-grounded yet (`grounded=False`).
- `AbrechnungPos`  — domain-shaped, not MO-grounded yet (`grounded=False`).

Records carry a `_source` marker so the UI can render a "this is mock data"
banner where applicable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal, Optional


class SchemaNotGrounded(Exception):
    """Raised by adapters when asked for a record kind whose MO schema we
    haven't yet extracted. Caught by the router → renders the gap banner."""


# ---------------------------------------------------------------------------
# Patient master record — VERIFIED from v1 intake (server/app/intake/llm.py)
# ---------------------------------------------------------------------------
@dataclass
class Patient:
    # MO-derived fields (all 14 from the v1 extraction prompt)
    id: str                                  # MO patient_id (string for portability)
    nachname: str
    vorname: str
    geburtsdatum: Optional[date]
    geschlecht: Optional[Literal["M", "W", "D"]]  # MO uses M/W historically; D for divers
    titel: Optional[str]
    anrede: Optional[str]
    strasse: Optional[str]
    hausnr: Optional[str]
    plz: Optional[str]
    ort: Optional[str]
    telefon_privat: Optional[str]
    telefon_mobil: Optional[str]
    email: Optional[str]
    muttersprache: Optional[str]

    # Provenance
    _source: Literal["mock", "mariadb"] = "mock"
    _grounded: bool = True   # this record IS grounded — fields verified

    @property
    def display_name(self) -> str:
        parts = []
        if self.titel: parts.append(self.titel)
        parts.append(self.vorname or "")
        parts.append(self.nachname or "")
        return " ".join(p for p in parts if p).strip()


# ---------------------------------------------------------------------------
# Fall (case / encounter) — DOMAIN-SHAPED, not MO-verified yet
# ---------------------------------------------------------------------------
@dataclass
class Fall:
    """A treatment case — typically one quarter of GKV billing or one private
    treatment episode. Real MO has more columns; this is the minimum we need."""
    id: str
    patient_id: str
    quartal: str             # e.g. "2026Q1"
    fallart: Literal["GKV", "Privat", "BG", "Selbstzahler", "Unbekannt"]
    diagnose_codes: list[str] = field(default_factory=list)  # ICD-10-GM
    eroeffnet_am: Optional[date] = None
    geschlossen_am: Optional[date] = None

    _source: Literal["mock", "mariadb"] = "mock"
    _grounded: bool = False  # NOT verified against MO schema


# ---------------------------------------------------------------------------
# Befund (finding / examination result) — DOMAIN-SHAPED
# ---------------------------------------------------------------------------
@dataclass
class Befund:
    id: str
    patient_id: str
    fall_id: Optional[str]
    erstellt_am: Optional[datetime]
    ersteller: Optional[str]   # doctor/MFA name
    typ: Optional[str]         # "Sono", "PSA-Wert", "Urin-Status", …
    inhalt: str = ""           # free-text or structured payload depending on typ

    _source: Literal["mock", "mariadb"] = "mock"
    _grounded: bool = False


# ---------------------------------------------------------------------------
# Abrechnungs-Position (billing item) — DOMAIN-SHAPED, GOÄ + EBM
# ---------------------------------------------------------------------------
@dataclass
class AbrechnungPosition:
    id: str
    patient_id: str
    fall_id: Optional[str]
    leistungsdatum: Optional[date]
    katalog: Literal["EBM", "GOÄ", "UV-GOÄ", "BEMA", "Unbekannt"]
    code: str                  # GOP (EBM) or GOÄ-Ziffer
    bezeichnung: Optional[str] = None
    anzahl: int = 1
    faktor: Optional[float] = None    # GOÄ Steigerungsfaktor (1.0 / 1.8 / 2.3 / 3.5 …)
    begruendung: Optional[str] = None # required when faktor > Schwellenwert (GOÄ §5)
    punkte: Optional[int] = None      # EBM Punktwert
    betrag_eur: Optional[float] = None

    _source: Literal["mock", "mariadb"] = "mock"
    _grounded: bool = False


# ---------------------------------------------------------------------------
# Coherence-check finding
# ---------------------------------------------------------------------------
@dataclass
class CoherenceIssue:
    """A data-quality finding produced by the integrity checker."""
    severity: Literal["info", "warning", "error"]
    record_kind: Literal["patient", "fall", "befund", "abrechnung"]
    record_id: str
    rule: str            # short rule name
    message: str         # human-readable, German
    suggestion: Optional[str] = None
