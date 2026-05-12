"""Pre-canned realistic Infoskop submission examples for demo purposes.

The Infoskop form's structure is well-known (see the 16 screenshots in
_raw_research/infoskop_anamnesebogen_screenshots/). These dict examples
mirror what a real Infoskop PDF import would yield once the OCR/pypdf
pipeline is wired against a sample PDF — without requiring patient PII
for the demo.

The narrative point this serves: even when Infoskop is fully filled,
the generated anamnesis prose covers ~30% of what the doctor needs.
This shows the limitation of Infoskop concretely.
"""
from __future__ import annotations
import random


INFOSKOP_DEMO_SUBMISSIONS = [
    {
        "name": "Demo-Patient A (Infoskop-Import)",
        "dob": "12.04.1958",
        "answers": {
            # Infoskop captures only these — no anliegen_heute, no Miktionsbeschwerden detail
            "krankenkasse": "AOK Baden-Württemberg",
            "vers_gesetzlich": True,
            "vers_privat": False,
            "vers_zusatz": False,
            "pflegegrad": False,
            "vorerkrankungen": {
                "bluthochdruck": True,
                "diabetes": True,
                "schilddruese": True,
                "asthma": False,
            },
            "vor_op": True,
            "vor_op_text": "(in Infoskop nicht spezifiziert)",
            "medikamente_ja": True,
            "medikamente_text": "(Liste nicht in Infoskop erfasst)",
            "allergien": {
                "schmerzmittel": False,
                "antibiotika": False,
                "lokalanaesthesie": False,
                "jod": False,
                "kontrastmittel": False,
            },
            "rauchen": "frueher",
            "alkohol": "kein",
            "beruf": "Lehrer im Ruhestand",
            "familie_krebs": True,
            "hausarzt_name": "Dr. Beispielarzt",
            "groesse": 175,
            "gewicht": 82,
        },
        "infoskop_coverage_note": (
            "Anliegen heute, Symptomatik, Verlauf und Konkretisierung "
            "der Vorerkrankungen/Medikamente werden vom Infoskop-Formular "
            "nicht erfasst — diese Information muss im Gespräch erhoben werden."
        ),
    },
    {
        "name": "Demo-Patient B (Infoskop-Import)",
        "dob": "23.09.1972",
        "answers": {
            "krankenkasse": "BKK R+V",
            "vers_gesetzlich": True,
            "vers_privat": False,
            "pflegegrad": False,
            "vorerkrankungen": {
                "bluthochdruck": False,
            },
            "vor_op": False,
            "medikamente_ja": False,
            "allergien": {
                "schmerzmittel": False,
                "antibiotika": False,
                "lokalanaesthesie": False,
                "jod": False,
                "kontrastmittel": False,
            },
            "rauchen": "nie",
            "alkohol": "kein",
            "beruf": "Softwareentwickler",
            "hausarzt_name": "Christine Stiepak",
            "groesse": 184,
            "gewicht": 78,
        },
        "infoskop_coverage_note": (
            "Patient hat im Infoskop alle Krankheits-Kategorien verneint. "
            "Das aktuelle Anliegen (Symptomatik, Beschwerdedauer, Vorbefunde) "
            "wird im Formular nicht abgefragt — muss im Gespräch erhoben werden."
        ),
    },
]


def pick_infoskop_demo() -> dict:
    return random.choice(INFOSKOP_DEMO_SUBMISSIONS)


PRAXIS_EIGEN_DEMO_SUBMISSIONS = [
    {
        "name": "Demo-Patient (Praxis-Bogen)",
        "dob": "08.11.1955",
        "answers": {
            # The richer set the urology-specific form captures:
            "anliegen_heute": "Beschwerden beim Wasserlassen seit ca. 4 Monaten, zunehmender Harndrang besonders nachts",
            "miktionsbeschwerden": {
                "haeufiger_drang": True,
                "imperativ": True,
                "nykturie": True,
                "schwacher_strahl": True,
                "nachtraeufeln": True,
                "schmerzen_unterbauch": False,
                "haematurie": False,
                "dauer": "ca. 4 Monate, langsam progredient",
            },
            "krankenkasse": "AOK Baden-Württemberg",
            "vers_gesetzlich": True,
            "vorerkrankungen": {
                "bluthochdruck": True,
                "diabetes": True,
            },
            "vor_op": True,
            "vor_op_text": "Appendektomie (1985), Leistenhernien-OP (2003)",
            "medikamente_ja": True,
            "medikamente_text": "Metformin 1000 mg 1-0-1, Ramipril 10 mg, ASS 100",
            "allergien": {
                "schmerzmittel": False,
                "weitere_text": "",
            },
            "rauchen": "frueher",
            "alkohol": "regelmaessig",
            "beruf": "Bäckermeister im Ruhestand",
            "familie_krebs": True,
            "familie_krebs_text": "Vater Prostatakarzinom mit ca. 70 Jahren",
            "hausarzt_name": "Dr. Beispielarzt",
            "groesse": 172,
            "gewicht": 88,
        },
    },
    {
        "name": "Demo-Patient (Praxis-Bogen, Hodenschmerzen)",
        "dob": "22.07.1989",
        "answers": {
            "anliegen_heute": "Seit 2 Wochen ziehende Schmerzen im linken Hoden, nach körperlicher Belastung verstärkt",
            "miktionsbeschwerden": {},
            "vorerkrankungen": {"asthma": True},
            "vor_op": False,
            "medikamente_ja": True,
            "medikamente_text": "Salbutamol bei Bedarf",
            "allergien": {"weitere_text": "Hausstaubmilben"},
            "rauchen": "nie",
            "alkohol": "kein",
            "beruf": "Softwareentwickler",
            "groesse": 184,
            "gewicht": 78,
        },
    },
]


def pick_praxis_demo() -> dict:
    return random.choice(PRAXIS_EIGEN_DEMO_SUBMISSIONS)
