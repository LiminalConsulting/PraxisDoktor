"""All other processes — registered with metadata, no implementation yet.
Each becomes a card on the dashboard and an empty tool view. Built out one
at a time as real practice needs are confirmed."""
from __future__ import annotations
from .registry import ProcessSpec, register

register(ProcessSpec(
    id="rechnungspruefung",
    display_name="Rechnungsprüfung",
    icon="receipt",
    surface="tool",
    phase="co_pilot",
    roles=["praxisinhaber", "mfa_abrechnung", "praxismanager"],
    inputs=["text", "structured_record"],
    outputs=["structured_record", "clipboard", "notification"],
    transition_types={
        # Engine-driven workflow: pull positions from MO, run rules, surface
        # issues, accept/correct/dismiss them per Fall.
        "fall_reviewed": {"feeds_back": False},
        "issue_acknowledged": {"feeds_back": True},
        "issue_corrected": {"feeds_back": True},
        "issue_dismissed_false_positive": {"feeds_back": True},
        "fall_marked_ready_for_billing": {"feeds_back": True},
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

# Termin-Übersicht: was placeholder/dashboard_only when external scheduler (TerMed)
# owned bookings. Now the public site posts booking_requested transitions directly
# into our DB; staff confirm/reschedule/decline from the dashboard.
register(ProcessSpec(
    id="termin_uebersicht",
    display_name="Terminverwaltung",
    icon="calendar",
    surface="tool",
    phase="co_pilot",
    roles=["praxisinhaber", "arzt", "mfa_empfang", "mfa_behandlung", "praxismanager"],
    inputs=["text", "structured_record"],
    outputs=["structured_record", "notification"],
    transition_types={
        "booking_requested": {"feeds_back": False},   # from public site
        "booking_confirmed": {"feeds_back": True},
        "booking_rescheduled": {"feeds_back": True},
        "booking_declined": {"feeds_back": True},
        "undo": {"feeds_back": False},
    },
    sort_order=30,
))

# Anamnesebogen: was placeholder when Infoskop owned the form. Now the public site
# hosts the form; submissions land here as form_submitted; staff review and attach
# to the patient record.
register(ProcessSpec(
    id="anamnesebogen",
    display_name="Anamnesebögen",
    icon="clipboard-list",
    surface="tool",
    phase="co_pilot",
    roles=["praxisinhaber", "arzt", "mfa_empfang"],
    inputs=["text", "structured_record", "file"],
    outputs=["structured_record", "notification"],
    transition_types={
        "form_started": {"feeds_back": False},          # patient opened the link
        "form_submitted": {"feeds_back": False},        # patient finished + sent
        "form_reviewed": {"feeds_back": True},          # MFA looked at it
        "form_attached_to_patient": {"feeds_back": True},  # MFA linked to patient
        "undo": {"feeds_back": False},
    },
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
