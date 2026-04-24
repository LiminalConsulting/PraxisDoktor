"""
Patientenakte process — read-only view of the practice's MO patient records.

Foundational integration: this is where the Medical Office adapter is
exercised. Other processes (rechnungspruefung, …) reuse the same adapter.

Surface = tool, phase = co_pilot (with visible gap banner since the MO
adapter is currently mock; adapter switches to real MariaDB once Papa's
schema extraction lands).

Roles: every staff member can look up a patient — Empfang for check-in,
Behandlung for prep, Abrechnung for invoice context, etc.
"""
from __future__ import annotations
from .registry import ProcessSpec, register


PATIENTENAKTE = register(ProcessSpec(
    id="patientenakte",
    display_name="Patientenakte",
    icon="folder-open",
    surface="tool",
    phase="co_pilot",
    roles=[
        "praxisinhaber", "arzt",
        "mfa_empfang", "mfa_behandlung", "mfa_abrechnung",
        "praxismanager",
    ],
    inputs=["text"],                       # search query
    outputs=["structured_record"],         # patient + related records
    transition_types={
        "patient_viewed": {"feeds_back": False},
        "coherence_issue_flagged": {"feeds_back": True},
        "coherence_issue_dismissed": {"feeds_back": True},
        "undo": {"feeds_back": False},
    },
    sort_order=15,  # right after team_chat, before terminverwaltung
))
