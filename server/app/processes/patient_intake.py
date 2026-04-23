from __future__ import annotations
from .registry import ProcessSpec, register

PATIENT_INTAKE = register(ProcessSpec(
    id="patient_intake",
    display_name="Patientenaufnahme",
    icon="user-plus",
    surface="tool",
    phase="co_pilot",
    roles=["praxisinhaber", "arzt", "mfa_empfang", "mfa_behandlung"],
    inputs=["audio", "image", "text"],
    outputs=["structured_record", "clipboard"],
    chat_attached=True,
    transition_types={
        "session_started":      {"feeds_back": False},
        "audio_uploaded":       {"feeds_back": False},
        "form_uploaded":        {"feeds_back": False},
        "transcript_ready":     {"feeds_back": False},
        "extraction_ready":     {"feeds_back": False},
        "field_accepted":       {"feeds_back": True},
        "field_rejected":       {"feeds_back": True},
        "field_corrected":      {"feeds_back": True},
        "session_marked_done":  {"feeds_back": False},
        "undo":                 {"feeds_back": False},
    },
    sort_order=10,
))
