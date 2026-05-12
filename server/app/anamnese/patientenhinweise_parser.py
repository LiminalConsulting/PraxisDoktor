"""Parse the Patientenhinweise window content (already structured as
`Label: Antwort` lines by MO's GDT importer) into our answers schema.

Strategy: the user uploads a screenshot of the MO Patientenhinweise window
(working around the known UI bug where the content can't be selected/copied).
We OCR the image and pattern-match the `Label: Value` lines against known
GDT field names.

The OCR output is high-quality because:
- Uniform font, black-on-white, single column
- No checkboxes — only structured text
- MO has already done the heavy lifting of parsing the GDT file

So this approach yields effectively the same data MO sees internally,
without depending on either the broken-copy bug or the lossy form-PDF.
"""
from __future__ import annotations
import re
from typing import Any


# ============================================================================
# Mapping from MO Patientenhinweise label → our internal answers schema
#
# MO emits both an "indicator" line (e.g. "Hoher Blutdruck: Ja") AND a
# "detail" line (e.g. "Herzinfarkt-wann: letztes Jahr"). We use both:
# - indicators set the boolean / categorical answer
# - details enrich the prose with the patient-typed context
# ============================================================================

# (label substring, dotted answer key, value transform from MO value)
# Order matters: longer/more specific labels first so they match before
# shorter generic ones.
INDICATOR_RULES: list[tuple[str, str, callable]] = [
    # Rauchen / Tabakkonsum (special: must come before "Rauchen: Ja")
    ("Ehemaliger Raucher", "rauchen", lambda v: "frueher" if v.lower().startswith("ja") else None),
    ("Rauchen über 10 Zigaretten", "rauchen_starker_konsum", lambda v: v.lower().startswith("ja")),
    ("Rauchen", "rauchen", lambda v: "aktuell" if v.lower().startswith("ja") else "nie"),

    # Alkohol
    ("Alkohol", "alkohol", lambda v: "regelmaessig" if v.lower().startswith("ja") else None),

    # Operationen
    ("Frühere Operationen", "vor_op", lambda v: v.lower().startswith("ja")),

    # Medikamente
    ("Medikamente", "medikamente_ja", lambda v: v.lower().startswith("ja")),

    # Herz-Kreislauf
    ("Hoher Blutdruck", "vorerkrankungen.bluthochdruck", lambda v: v.lower().startswith("ja")),
    ("Herzinfarkt", "vorerkrankungen.herzinfarkt", lambda v: v.lower().startswith("ja")),
    ("Herzschrittmacher", "vorerkrankungen.schrittmacher", lambda v: v.lower().startswith("ja")),
    ("Thrombose-Embolie", "vorerkrankungen.thrombose", lambda v: v.lower().startswith("ja")),
    ("Thrombose/Embolie", "vorerkrankungen.thrombose", lambda v: v.lower().startswith("ja")),
    ("Durchblutungsstörungen", "vorerkrankungen.durchblutung", lambda v: v.lower().startswith("ja")),
    ("Herz-Kreislauferkrankungen-Andere", "vorerkrankungen.herz_kreislauf_andere", lambda v: v.lower().startswith("ja")),

    # Allergien (Schmerzmittel / Antibiotika / etc.) — only indicator form here
    ("Allergie Unverträglichkeit: Schmerzmittel", "allergien.schmerzmittel", lambda v: v.lower().startswith("ja")),
    ("Allergie Unverträglichkeit: Antibiotika", "allergien.antibiotika", lambda v: v.lower().startswith("ja")),
    ("Allergie Unverträglichkeit: Lokalanästhesie", "allergien.lokalanaesthesie", lambda v: v.lower().startswith("ja")),
    ("Allergie Unverträglichkeit: Jod", "allergien.jod", lambda v: v.lower().startswith("ja")),
    ("Allergie Unverträglichkeit: Kontrastmittel", "allergien.kontrastmittel", lambda v: v.lower().startswith("ja")),
    ("Allergien Unverträglichkeiten-Andere", "allergien.andere_marker", lambda v: v.lower().startswith("ja")),

    # Stoffwechsel
    ("Diabetes mellitus Typ 1", "vorerkrankungen.diabetes_typ1", lambda v: v.lower().startswith("ja")),
    ("Diabetes mellitus Typ 2", "vorerkrankungen.diabetes_typ2", lambda v: v.lower().startswith("ja")),
    ("Diabetes mellitus", "vorerkrankungen.diabetes", lambda v: v.lower().startswith("ja")),
    ("Osteoporose", "vorerkrankungen.osteoporose", lambda v: v.lower().startswith("ja")),

    # Weitere Erkrankungen
    ("Schilddrüsenerkrankung", "vorerkrankungen.schilddruese", lambda v: v.lower().startswith("ja")),
    ("Lungenerkrankung", "vorerkrankungen.lunge", lambda v: v.lower().startswith("ja")),
    ("Asthma", "vorerkrankungen.asthma", lambda v: v.lower().startswith("ja")),
    ("Krebserkrankung familiär", "familie_krebs", lambda v: v.lower().startswith("ja")),
    ("Krebserkrankungen", "vorerkrankungen.krebs", lambda v: v.lower().startswith("ja")),
    ("Epilepsie", "vorerkrankungen.epilepsie", lambda v: v.lower().startswith("ja")),
    ("Magen-Darm-Erkrankungen", "vorerkrankungen.magen_darm", lambda v: v.lower().startswith("ja")),
    ("Nierenerkrankungen", "vorerkrankungen.niere", lambda v: v.lower().startswith("ja")),
    ("Augenerkrankung", "vorerkrankungen.augen", lambda v: v.lower().startswith("ja")),
    ("Weitere Erkrankungen", "vorerkrankungen.weitere_marker", lambda v: v.lower().startswith("ja")),
]

# (label substring with "-welche:" or "-wann:" suffix, output key, transform)
DETAIL_RULES: list[tuple[str, str, callable]] = [
    ("Frühere Operationen-welche", "vor_op_text", lambda v: v),
    ("Alkohol-Wieviel", "alkohol_wieviel", lambda v: v),
    ("Rauchen-Seit", "rauchen_seit", lambda v: v),
    ("Ehemaliger Raucher", "rauchen_ehemals_text", lambda v: v),  # could match indicator too
    ("Medikamente-welche", "medikamente_text", lambda v: v),

    ("Herzinfarkt-wann", "herzinfarkt_wann", lambda v: v),
    ("Herzschrittmacher-wann", "herzschrittmacher_wann", lambda v: v),
    ("Herz-Kreislauferkrankungen-Andere", "herz_kreislauf_andere_text", lambda v: v),

    ("Allergie Unverträglichkeit: Schmerzmittel", "allergien.schmerzmittel_text", lambda v: v),
    ("Allergie Unverträglichkeit: Antibiotika", "allergien.antibiotika_text", lambda v: v),
    ("Allergien Unverträglichkeiten-Andere", "allergien.weitere_text", lambda v: v),

    ("Schilddrüsenerkrankung-welche", "schilddruese_welche", lambda v: v),
    ("Lungenerkrankung-welche", "lunge_welche", lambda v: v),
    ("Krebserkrankungen-welche", "krebs_welche", lambda v: v),
    ("Magen-Darm-Erkrankungen-welche", "magen_darm_welche", lambda v: v),
    ("Nierenerkrankungen-welche", "nieren_welche", lambda v: v),
    ("Augenerkrankung-welche", "augen_welche", lambda v: v),
    ("Weitere Erkrankungen-welche", "weitere_erkrankungen_welche", lambda v: v),
]


def _set_nested(d: dict, dotted_key: str, value: Any) -> None:
    parts = dotted_key.split(".")
    cur = d
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


# Regex to split each line into (label, value)
LINE_PATTERN = re.compile(r"^(.+?):\s*(.+)$")


def parse_patientenhinweise_text(text: str) -> dict[str, Any]:
    """Parse the OCR'd Patientenhinweise window text into our answers schema."""
    answers: dict[str, Any] = {}

    # Split into lines, strip whitespace, drop empties + window-chrome lines
    chrome = {
        "Anamnese", "Datei", "Einstellungen", "Aktion",
        "Dokumenteneingang", "OK", "Schliessen", "Schließen",
        "Alle markierten Meldungen entfernen",
    }
    lines = [
        ln.strip() for ln in text.splitlines()
        if ln.strip() and ln.strip() not in chrome
        and not ln.strip().startswith("Patientenhinweise")
    ]

    # Two-pass: first detail rules (more specific labels with "-welche/-wann"),
    # then indicator rules (boolean markers).
    matched_lines: set[int] = set()

    # Detail rules first
    for idx, line in enumerate(lines):
        if idx in matched_lines:
            continue
        m = LINE_PATTERN.match(line)
        if not m:
            continue
        label_text, value = m.group(1).strip(), m.group(2).strip()
        # Some entries have nested colons (e.g. "Allergie Unverträglichkeit: Schmerzmittel: Xanax")
        # In that case the label includes the first colon-segment too.
        full_label_options = [label_text, label_text + ": " + value.split(":")[0].strip() if ":" in value else label_text]

        for label, out_key, transform in DETAIL_RULES:
            # Match either by substring of the full line or by label prefix
            check_text = line
            if label in check_text:
                # Extract the value AFTER the label
                after = check_text.split(label, 1)[1].lstrip(":").strip()
                # For lines like "Allergie Unverträglichkeit: Schmerzmittel: Xanax", the value
                # is after the SECOND colon
                if ":" in after and label != after.split(":")[0].strip():
                    after = after.split(":", 1)[1].strip()
                if after and not after.lower().startswith("ja") and not after.lower().startswith("nein"):
                    transformed = transform(after)
                    if transformed:
                        _set_nested(answers, out_key, transformed)
                        matched_lines.add(idx)
                        break

    # Indicator rules
    for idx, line in enumerate(lines):
        if idx in matched_lines:
            continue
        for label, out_key, transform in INDICATOR_RULES:
            if label in line:
                after = line.split(label, 1)[1].lstrip(":").strip()
                # If there's a colon left (e.g. "Schmerzmittel: Ja"), grab the rightmost ja/nein
                value = after.rsplit(":", 1)[-1].strip() if ":" in after else after
                transformed = transform(value)
                if transformed is not None:
                    _set_nested(answers, out_key, transformed)
                    matched_lines.add(idx)
                    break

    return answers


def parse_patientenhinweise_image(image_path: str) -> tuple[dict[str, Any], str]:
    """OCR an image of the Patientenhinweise window and parse into answers.
    Returns (answers, raw_text)."""
    import easyocr
    reader = easyocr.Reader(["de", "en"], gpu=False, verbose=False)
    results = reader.readtext(image_path, detail=0, paragraph=False)
    raw_text = "\n".join(results)
    answers = parse_patientenhinweise_text(raw_text)
    return answers, raw_text
