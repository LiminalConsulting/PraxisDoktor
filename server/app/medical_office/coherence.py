"""
Data-coherence checks over MO records.

Each rule takes a single record (and optionally a context dict for
cross-record rules) and returns 0..n CoherenceIssues. Rules are pure
functions — easy to add, easy to test.

Rules that depend on data not yet grounded (Fall, Befund, Abrechnung)
are marked clearly and only run when the adapter says those kinds are
grounded.
"""
from __future__ import annotations
import re
from datetime import date

from .adapter import MedicalOfficeAdapter
from .schema import Patient, CoherenceIssue


_PHONE_RE = re.compile(r"^[\d\s\-\+\(\)/]+$")
_PLZ_RE = re.compile(r"^\d{5}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def check_patient(p: Patient) -> list[CoherenceIssue]:
    issues: list[CoherenceIssue] = []

    # Required fields
    for field, label in [
        ("nachname", "Nachname"),
        ("vorname", "Vorname"),
        ("geburtsdatum", "Geburtsdatum"),
    ]:
        if not getattr(p, field):
            issues.append(CoherenceIssue(
                severity="error", record_kind="patient", record_id=p.id,
                rule="required_field_missing",
                message=f"Pflichtfeld fehlt: {label}.",
            ))

    # PLZ format
    if p.plz and not _PLZ_RE.match(p.plz):
        issues.append(CoherenceIssue(
            severity="warning", record_kind="patient", record_id=p.id,
            rule="plz_format",
            message=f"PLZ '{p.plz}' hat kein 5-stelliges Format.",
            suggestion="PLZ prüfen und korrigieren.",
        ))
    elif not p.plz:
        issues.append(CoherenceIssue(
            severity="warning", record_kind="patient", record_id=p.id,
            rule="address_incomplete",
            message="PLZ fehlt — Adresse unvollständig.",
        ))

    # Phone format (loose: only chars + digits/spaces/-/+/() allowed)
    for f, label in [("telefon_privat", "Telefon privat"),
                     ("telefon_mobil",  "Telefon mobil")]:
        v = getattr(p, f)
        if v and not _PHONE_RE.match(v):
            issues.append(CoherenceIssue(
                severity="warning", record_kind="patient", record_id=p.id,
                rule="phone_format",
                message=f"{label} enthält ungültige Zeichen: '{v}'.",
            ))

    # Email format
    if p.email and not _EMAIL_RE.match(p.email):
        issues.append(CoherenceIssue(
            severity="warning", record_kind="patient", record_id=p.id,
            rule="email_format",
            message=f"E-Mail '{p.email}' hat kein gültiges Format.",
        ))

    # Age sanity
    if p.geburtsdatum:
        today = date.today()
        age = today.year - p.geburtsdatum.year - (
            (today.month, today.day) < (p.geburtsdatum.month, p.geburtsdatum.day)
        )
        if age < 0 or age > 120:
            issues.append(CoherenceIssue(
                severity="error", record_kind="patient", record_id=p.id,
                rule="age_sanity",
                message=f"Geburtsdatum ergibt Alter {age} Jahre — bitte prüfen.",
            ))

    # No contact at all = unreachable
    if not (p.telefon_privat or p.telefon_mobil or p.email):
        issues.append(CoherenceIssue(
            severity="warning", record_kind="patient", record_id=p.id,
            rule="no_contact",
            message="Keine Kontaktdaten hinterlegt (kein Telefon, keine E-Mail).",
            suggestion="Mindestens eine Kontaktmöglichkeit ergänzen.",
        ))

    return issues


def check_coherence(adapter: MedicalOfficeAdapter,
                    limit_patients: int = 200) -> list[CoherenceIssue]:
    """Run all applicable checks across the dataset.
    Currently scopes to Patient-level checks since that's what's grounded."""
    issues: list[CoherenceIssue] = []
    for p in adapter.list_patients(limit=limit_patients):
        issues.extend(check_patient(p))
    return issues
