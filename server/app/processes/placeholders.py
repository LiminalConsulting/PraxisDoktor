"""All other processes — registered with metadata, no implementation yet.
Each becomes a card on the dashboard and an empty tool view. Built out one
at a time as real practice needs are confirmed."""
from __future__ import annotations
from .registry import ProcessSpec, register

# Tier-2 priority — first new tool to build after intake
register(ProcessSpec(
    id="rechnungspruefung",
    display_name="Rechnungsprüfung",
    icon="receipt",
    surface="tool",
    phase="placeholder",
    roles=["praxisinhaber"],
    inputs=["file", "text"],
    outputs=["structured_record", "clipboard"],
    transition_types={
        "session_started": {"feeds_back": False},
        "invoice_uploaded": {"feeds_back": False},
        "field_accepted": {"feeds_back": True},
        "field_rejected": {"feeds_back": True},
        "field_corrected": {"feeds_back": True},
        "undo": {"feeds_back": False},
    },
    sort_order=20,
))

# Live day-1: every process has chat attached, but team_chat is the global one
register(ProcessSpec(
    id="team_chat",
    display_name="Team-Chat",
    icon="message-square",
    surface="conversation",
    phase="co_pilot",
    roles=["praxisinhaber", "arzt", "mfa_empfang", "mfa_behandlung", "mfa_abrechnung", "praxismanager"],
    inputs=["text", "audio", "file"],
    outputs=["notification"],
    chat_attached=False,  # the conversation IS the surface; no second chat panel
    transition_types={
        "chat_message_sent": {"feeds_back": False},
    },
    sort_order=5,
))

register(ProcessSpec(
    id="termin_uebersicht",
    display_name="Termin-Übersicht",
    icon="calendar",
    surface="dashboard_only",
    phase="dashboard_only",
    roles=["praxisinhaber", "arzt", "mfa_empfang", "mfa_behandlung", "praxismanager"],
    transition_types={"appointment_observed": {"feeds_back": False}},
    sort_order=30,
))

register(ProcessSpec(
    id="anamnesebogen",
    display_name="Anamnesebogen-Verwaltung",
    icon="clipboard-list",
    surface="dashboard_only",
    phase="dashboard_only",
    roles=["praxisinhaber", "arzt", "mfa_empfang"],
    inputs=["image", "file"],
    outputs=["structured_record"],
    transition_types={"form_observed": {"feeds_back": False}},
    sort_order=40,
))

register(ProcessSpec(
    id="krankenkassen_abrechnung",
    display_name="Krankenkassen-Abrechnung",
    icon="file-text",
    surface="dashboard_only",
    phase="decline",  # explicit non-goal initially
    roles=["praxisinhaber", "mfa_abrechnung", "praxismanager"],
    transition_types={"observation": {"feeds_back": False}},
    sort_order=50,
))

register(ProcessSpec(
    id="materialverwaltung",
    display_name="Materialverwaltung",
    icon="package",
    surface="tool",
    phase="placeholder",
    roles=["praxisinhaber", "mfa_behandlung", "praxismanager"],
    inputs=["text", "structured_record"],
    outputs=["structured_record", "notification"],
    transition_types={"placeholder": {"feeds_back": False}},
    sort_order=60,
))

register(ProcessSpec(
    id="personal_schichtplan",
    display_name="Personal & Schichtplan",
    icon="users",
    surface="tool",
    phase="placeholder",
    roles=["praxisinhaber", "praxismanager"],
    inputs=["text", "structured_record"],
    outputs=["structured_record", "notification"],
    transition_types={"placeholder": {"feeds_back": False}},
    sort_order=70,
))

register(ProcessSpec(
    id="email_triage",
    display_name="E-Mail-Triage",
    icon="mail",
    surface="tool",
    phase="placeholder",
    roles=["praxisinhaber", "mfa_empfang", "praxismanager"],
    inputs=["text", "file"],
    outputs=["notification", "clipboard"],
    transition_types={"placeholder": {"feeds_back": False}},
    sort_order=80,
))
