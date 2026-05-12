"""Generate anamnesis-style prose from a structured questionnaire submission.

The output mirrors the compressed clinical-telegraph style observed in real
anamnesis entries from Papa's practice:
- Semicolon-separated clauses
- Medical-vocabulary preserved (Pollakiurie, Dysurie, etc.)
- Abbreviations where appropriate (HA = Hausarzt, Z.n. = Zustand nach)
- No preamble, no closing

The generator is deterministic (no LLM) for v1. Later versions can layer an
LLM refinement step that imitates the doctor's writing voice from a corpus
of past entries.
"""
from __future__ import annotations
from typing import Any


# Map from form-field keys to clinical prose fragments
MIKTION_LABELS = {
    "brennen": "Brennen beim Wasserlassen",
    "haeufiger_drang": "Pollakiurie",
    "imperativ": "imperativer Harndrang",
    "nykturie": "Nykturie",
    "haematurie": "sichtbare Hämaturie",
    "schwacher_strahl": "abgeschwächter Harnstrahl",
    "nachtraeufeln": "Nachträufeln",
    "inkontinenz": "unfreiwilliger Urinverlust",
    "trueber_urin": "trüber Urin",
    "schmerzen_unterbauch": "Schmerzen im Unterbauch",
    "schmerzen_damm": "Druckgefühl im Dammbereich",
    "schmerzen_flanke": "Flankenschmerzen",
}

KOMORBID_LABELS = {
    "bluthochdruck": "art. Hypertonie",
    "diabetes": "Diabetes mellitus",
    "diabetes_typ1": "Diabetes mellitus Typ 1",
    "diabetes_typ2": "Diabetes mellitus Typ 2",
    "herzinfarkt": "Z.n. Myokardinfarkt",
    "schrittmacher": "Herzschrittmacher",
    "durchblutung": "Durchblutungsstörungen",
    "thrombose": "Z.n. Thrombose/Embolie",
    "asthma": "Asthma bronchiale",
    "lunge": "Lungenerkrankung",
    "schilddruese": "Schilddrüsenerkrankung",
    "krebs": "Z.n. Tumorerkrankung",
    "epilepsie": "Epilepsie",
    "magen_darm": "Magen-Darm-Erkrankung",
    "niere": "Nierenerkrankung",
    "augen": "Augenerkrankung",
    "osteoporose": "Osteoporose",
}

ALLERGIE_LABELS = {
    "schmerzmittel": "Schmerzmittel",
    "antibiotika": "Antibiotika",
    "lokalanaesthesie": "Lokalanästhesie",
    "jod": "Jod",
    "kontrastmittel": "Kontrastmittel",
}


def _fmt_list(items: list[str], sep: str = ", ") -> str:
    return sep.join(i for i in items if i)


def _filter_yes(labels: dict[str, str], answers: dict[str, Any]) -> list[str]:
    """Return labels for boolean-true answers."""
    return [labels[k] for k in labels if answers.get(k) is True]


def _filter_yes_strings(labels: dict[str, str], answers: dict[str, Any]) -> list[str]:
    """Return labels for answers that equal 'ja' or True."""
    out = []
    for k, label in labels.items():
        v = answers.get(k)
        if v is True or (isinstance(v, str) and v.lower() in ("ja", "j", "yes", "true", "1")):
            out.append(label)
    return out


def generate_anamnese_prose(answers: dict[str, Any]) -> str:
    """Generate a clinical-style prose paragraph from the questionnaire answers.

    Returns a single-paragraph string suitable for pasting into the
    `Text-Anamnese` (FEintragsart='ta') field in Medical Office.

    Empty or absent sections are simply omitted.
    """
    parts: list[str] = []

    # 1. Anliegen heute / Hauptsymptom
    anliegen = (answers.get("anliegen_heute") or "").strip()
    if anliegen:
        parts.append(anliegen.rstrip(". "))

    # 2. Miktionsbeschwerden (the urology-specific module)
    miktion = answers.get("miktionsbeschwerden") or {}
    if isinstance(miktion, dict):
        yes = _filter_yes_strings(MIKTION_LABELS, miktion)
        if yes:
            dauer = (miktion.get("dauer") or "").strip()
            seg = _fmt_list(yes)
            if dauer:
                seg = f"{seg} seit {dauer}"
            parts.append(seg)

    # 3. Vorerkrankungen — combine Y/N markers with "-welche" specifics
    vor = answers.get("vorerkrankungen") or {}
    welche_map = {
        "schilddruese": answers.get("schilddruese_welche"),
        "lunge": answers.get("lunge_welche"),
        "krebs": answers.get("krebs_welche"),
        "magen_darm": answers.get("magen_darm_welche"),
        "niere": answers.get("nieren_welche"),
        "augen": answers.get("augen_welche"),
        "herzinfarkt": answers.get("herzinfarkt_wann"),
        "schrittmacher": answers.get("herzschrittmacher_wann"),
    }
    if isinstance(vor, dict):
        ve_parts = []
        for key, label in KOMORBID_LABELS.items():
            v = vor.get(key)
            is_yes = (v is True) or (isinstance(v, str) and v.lower() in ("ja", "j", "yes"))
            if is_yes:
                detail = welche_map.get(key)
                if detail and isinstance(detail, str) and detail.strip():
                    ve_parts.append(f"{label} ({detail.strip()})")
                else:
                    ve_parts.append(label)
        # Also pick up the doctor-typed "weitere Erkrankungen welche"
        weitere = answers.get("weitere_erkrankungen_welche")
        if weitere and isinstance(weitere, str) and weitere.strip():
            ve_parts.append(weitere.strip())
        # And the doctor-typed "Herz-Kreislauf-Andere" free text
        hka = answers.get("herz_kreislauf_andere_text")
        if hka and isinstance(hka, str) and hka.strip() and hka.strip().lower() not in ("ja", "nein"):
            # only include if not already covered by an indicator
            if hka.strip() not in ve_parts:
                ve_parts.append(hka.strip())
        if ve_parts:
            parts.append(f"VE: {_fmt_list(ve_parts)}")

    # 4. Vor-OPs
    if answers.get("vor_op") is True:
        op_text = (answers.get("vor_op_text") or "").strip()
        if op_text:
            parts.append(f"Vor-OPs: {op_text}")
        else:
            parts.append("Vor-OPs vorhanden (nicht näher spezifiziert)")

    # 5. Medikamente
    medikamente = (answers.get("medikamente_text") or "").strip()
    if answers.get("medikamente_ja") is True and medikamente:
        parts.append(f"Medikation: {medikamente}")
    elif answers.get("medikamente_ja") is True:
        parts.append("Medikation vorhanden (nicht näher spezifiziert)")
    elif answers.get("medikamente_ja") is False:
        parts.append("keine Dauermedikation")

    # 6. Allergien (with detail texts where available)
    allergien = answers.get("allergien") or {}
    if isinstance(allergien, dict):
        all_parts = []
        for key, label in ALLERGIE_LABELS.items():
            v = allergien.get(key)
            is_yes = (v is True) or (isinstance(v, str) and v.lower() in ("ja", "j", "yes"))
            if is_yes:
                detail = allergien.get(f"{key}_text")
                if detail and isinstance(detail, str) and detail.strip():
                    all_parts.append(f"{label} ({detail.strip()})")
                else:
                    all_parts.append(label)
        weitere = (allergien.get("weitere_text") or "").strip()
        if weitere:
            all_parts.append(weitere)
        if all_parts:
            parts.append(f"Allergien: {_fmt_list(all_parts)}")
        elif allergien.get("keine") is True:
            parts.append("keine Allergien bekannt")

    # 7. Sozialanamnese
    soz_parts = []
    rauchen = answers.get("rauchen")
    if rauchen == "aktuell":
        soz_parts.append("Raucher")
    elif rauchen == "frueher":
        soz_parts.append("Z.n. Nikotinabusus")
    elif rauchen == "nie":
        soz_parts.append("Nichtraucher")
    alkohol = answers.get("alkohol")
    if alkohol == "regelmaessig":
        soz_parts.append("regelmäßiger Alkoholkonsum")
    elif alkohol == "kein":
        soz_parts.append("kein Alkoholkonsum")
    beruf = (answers.get("beruf") or "").strip()
    if beruf:
        soz_parts.append(beruf)
    if soz_parts:
        parts.append(_fmt_list(soz_parts))

    # 8. Familienanamnese
    fam_krebs = answers.get("familie_krebs") is True
    if fam_krebs:
        fam_detail = (answers.get("familie_krebs_text") or "").strip()
        parts.append(f"FA: Krebserkrankung{' (' + fam_detail + ')' if fam_detail else ''}")

    # 9. Hausarzt (only if not already in MO)
    hausarzt_name = (answers.get("hausarzt_name") or "").strip()
    if hausarzt_name:
        parts.append(f"HA: {hausarzt_name}")

    # 10. Körperdaten (Größe/Gewicht)
    groesse = answers.get("groesse")
    gewicht = answers.get("gewicht")
    if groesse or gewicht:
        body = []
        if groesse:
            body.append(f"{groesse} cm")
        if gewicht:
            body.append(f"{gewicht} kg")
        parts.append(", ".join(body))

    if not parts:
        return ""

    # Join all parts with periods + space (matching observed style)
    text = ". ".join(parts).rstrip(".") + "."
    return text
