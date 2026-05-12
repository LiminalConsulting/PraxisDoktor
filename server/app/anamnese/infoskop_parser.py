"""Parse a filled-in Infoskop Anamnesebogen PDF or image into the same
`answers` dict shape our custom form produces. The output then feeds the
same prose generator, so both paths share the same pipeline.

Approach:
- For PDFs with extractable text (pypdf): pattern-match labels + checkbox glyphs
- For images / scanned PDFs: easyocr fallback to get a text stream
- Same downstream label-recognition logic for both
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any


# Filled-checkbox indicators that Infoskop's PDF uses (and that OCR tends to misread as)
_FILLED_MARKS = {"X", "x", "☒", "✓", "✔", "✗"}
_EMPTY_MARKS = {"☐", "▢", "□", "◻"}


def _try_pdf_text(pdf_path: str) -> str | None:
    """Try extracting selectable text from a PDF using pypdf. Returns None
    if pypdf isn't installed or the PDF has no text layer."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        reader = PdfReader(pdf_path)
        out = []
        for page in reader.pages:
            t = page.extract_text() or ""
            out.append(t)
        joined = "\n".join(out).strip()
        return joined if joined else None
    except Exception:
        return None


def _try_ocr(image_or_pdf_path: str) -> str | None:
    """Fallback OCR using easyocr. Slower but works on scanned PDFs and image
    uploads. Returns None if easyocr fails."""
    try:
        import easyocr
    except ImportError:
        return None
    try:
        reader = easyocr.Reader(["de", "en"], gpu=False, verbose=False)
        results = reader.readtext(image_or_pdf_path, detail=0, paragraph=True)
        return "\n".join(results) if results else None
    except Exception:
        return None


def extract_raw_text(path: str) -> str:
    """Get text from a PDF or image, trying pypdf first then OCR."""
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        text = _try_pdf_text(path)
        if text and len(text) > 200:  # text layer exists
            return text
    # Fall through to OCR for images or text-less PDFs
    ocr_text = _try_ocr(path) or ""
    return ocr_text


# ============================================================================
# Label-based parsing rules — given a text stream, find values
# ============================================================================

# Patterns of form: header label, list of (output_key, regex to detect "ja")
# The regex looks for the label text immediately followed by either:
#   - J<X>  N<empty>  (filled J)
#   - JX  N☐  (filled J)
#   - JX written in any of several ways
# The simplest reliable heuristic: find the label, look at the few chars after
# it, see if the J variant has a filled mark before the N variant does.


def _is_marked(s: str) -> bool:
    """Does this string contain an Infoskop-style filled mark?"""
    return any(m in s for m in _FILLED_MARKS)


def _ja_nein_after(text: str, label: str) -> str | None:
    """For a yes/no label, find the answer based on which column gets the mark.
    Returns 'ja' / 'nein' / None.
    """
    idx = text.find(label)
    if idx < 0:
        return None
    # Look at the next ~60 chars after the label (enough to capture J and N)
    window = text[idx + len(label):idx + len(label) + 80]

    # Strategy: look for 'J' followed by mark, and 'N' followed by mark.
    # Whichever has the filled mark immediately after wins.
    j_match = re.search(r"J\s*([^\s])", window)
    n_match = re.search(r"N\s*([^\s])", window)

    j_filled = j_match and j_match.group(1) in _FILLED_MARKS
    n_filled = n_match and n_match.group(1) in _FILLED_MARKS

    if j_filled and not n_filled:
        return "ja"
    if n_filled and not j_filled:
        return "nein"
    # If neither or both are detected, we leave it as None (unklar)
    return None


def _text_after(text: str, label: str, max_chars: int = 200) -> str | None:
    """Get free-text content immediately after a label (until next blank line
    or known next-label keyword)."""
    idx = text.find(label)
    if idx < 0:
        return None
    after = text[idx + len(label):idx + len(label) + max_chars]
    # Strip the colon, take until first double-newline or next bold-label-pattern
    after = after.lstrip(":").lstrip()
    # Cut at next likely section header (bold capitalized word at line start)
    stop_idx = re.search(r"\n\s*[A-ZÄÖÜ][a-zäöüß]+(?:\s|/|\-)", after)
    if stop_idx:
        after = after[:stop_idx.start()]
    cleaned = after.strip()
    # Filter empty / placeholder
    if cleaned.lower() in ("", "bitte eingeben", "bitte nachname eingeben",
                          "bitte vornamen eingeben", "tt.mm.jjjj", "cm", "kg"):
        return None
    return cleaned[:max_chars] if cleaned else None


# Map from Infoskop label → our answers schema key
YES_NO_RULES = {
    "Rauchen Sie?": ("rauchen", lambda v: "aktuell" if v == "ja" else None),
    "Haben Sie jemals geraucht?": ("rauchen_jemals", lambda v: v),
    "Wird Alkohol regelmäßig konsumiert?": ("alkohol", lambda v: "regelmaessig" if v == "ja" else "kein"),
    "Wurden Sie in der Vergangenheit schon einmal operiert?": ("vor_op", lambda v: v == "ja"),
    "Nehmen Sie regelmäßig oder zurzeit Medikamente ein?": ("medikamente_ja", lambda v: v == "ja"),
    # Versicherung
    "gesetzlich versichert": ("vers_gesetzlich", lambda v: v == "ja"),
    "privat versichert": ("vers_privat", lambda v: v == "ja"),
    "Ich habe eine Zusatzversicherung.": ("vers_zusatz", lambda v: v == "ja"),
    "Besteht ein Pflegegrad?": ("pflegegrad", lambda v: v == "ja"),
    # Herz-Kreislauf
    "Hoher Blutdruck": ("vorerkrankungen.bluthochdruck", lambda v: v == "ja"),
    "Herzinfarkt": ("vorerkrankungen.herzinfarkt", lambda v: v == "ja"),
    "Herzschrittmacher": ("vorerkrankungen.schrittmacher", lambda v: v == "ja"),
    "Durchblutungsstörungen": ("vorerkrankungen.durchblutung", lambda v: v == "ja"),
    "Thrombose/Embolie": ("vorerkrankungen.thrombose", lambda v: v == "ja"),
    # Allergien
    "Schmerzmittel": ("allergien.schmerzmittel", lambda v: v == "ja"),
    "Antibiotika": ("allergien.antibiotika", lambda v: v == "ja"),
    "Lokalanästhesie": ("allergien.lokalanaesthesie", lambda v: v == "ja"),
    "Jod": ("allergien.jod", lambda v: v == "ja"),
    "Kontrastmittel": ("allergien.kontrastmittel", lambda v: v == "ja"),
    # Stoffwechsel
    "Diabetes mellitus": ("vorerkrankungen.diabetes", lambda v: v == "ja"),
    "Osteoporose": ("vorerkrankungen.osteoporose", lambda v: v == "ja"),
    # Weitere
    "Schilddrüsenerkrankung": ("vorerkrankungen.schilddruese", lambda v: v == "ja"),
    "Lungenerkrankung": ("vorerkrankungen.lunge", lambda v: v == "ja"),
    "Asthma": ("vorerkrankungen.asthma", lambda v: v == "ja"),
    "Krebserkrankungen": ("vorerkrankungen.krebs", lambda v: v == "ja"),
    "Gibt es in Ihrer Familie Angehörige mit einer Krebserkrankung?": ("familie_krebs", lambda v: v == "ja"),
    "Epilepsie": ("vorerkrankungen.epilepsie", lambda v: v == "ja"),
    "Magen-Darm-Erkrankungen": ("vorerkrankungen.magen_darm", lambda v: v == "ja"),
    "Nierenerkrankungen": ("vorerkrankungen.niere", lambda v: v == "ja"),
}

TEXT_RULES = {
    "Name:": "nachname",
    "Vorname:": "vorname",
    "Geburtsdatum:": "geburtsdatum",
    "Straße, Hausnummer:": "strasse_hausnr",
    "PLZ, Ort:": "plz_ort",
    "Größe:": "groesse",
    "Gewicht:": "gewicht",
    "Berufliche Tätigkeit": "beruf",
    "Name der Krankenkasse:": "krankenkasse",
    "Name des Hausarztes:": "hausarzt_name",
    "Anschrift und Telefonnummer des Hausarztes:": "hausarzt_anschrift",
}


def _set_nested(d: dict, dotted_key: str, value: Any) -> None:
    """Set d['a.b.c'] = v as d['a']['b']['c'] = v."""
    parts = dotted_key.split(".")
    cur = d
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


def parse_infoskop_text(text: str) -> dict[str, Any]:
    """Parse extracted Infoskop text into the same answers schema our
    custom form produces. Unfilled fields just don't appear in the dict.
    """
    answers: dict[str, Any] = {}

    # Yes/no rules
    for label, (out_key, transform) in YES_NO_RULES.items():
        v = _ja_nein_after(text, label)
        if v is not None:
            transformed = transform(v)
            if transformed is not None:
                _set_nested(answers, out_key, transformed)

    # Text rules
    for label, out_key in TEXT_RULES.items():
        v = _text_after(text, label)
        if v:
            answers[out_key] = v

    # Special: post-process strasse_hausnr → strasse + hausnr split
    if "strasse_hausnr" in answers:
        sh = answers.pop("strasse_hausnr")
        m = re.match(r"^(.+?)[,\s]+(\d+\w*)$", sh.strip())
        if m:
            answers["strasse"] = m.group(1).strip()
            answers["hausnr"] = m.group(2).strip()
        else:
            answers["strasse"] = sh

    # Special: plz_ort split
    if "plz_ort" in answers:
        po = answers.pop("plz_ort")
        m = re.match(r"^(\d{5})[,\s]+(.+)$", po.strip())
        if m:
            answers["plz"] = m.group(1)
            answers["ort"] = m.group(2).strip()
        else:
            answers["ort"] = po

    # Special: Geschlecht (W/M/D checkboxes inline)
    gen_idx = text.find("Geschlecht:")
    if gen_idx >= 0:
        gen_window = text[gen_idx:gen_idx + 100]
        for ch, code in [("W", "W"), ("M", "M"), ("D", "D")]:
            # Look for marked checkbox just before letter, or letter followed by mark
            pattern = rf"[{''.join(_FILLED_MARKS)}]\s*{ch}\b"
            if re.search(pattern, gen_window):
                answers["geschlecht"] = code
                break

    # Special: anliegen_heute is not in Infoskop — set placeholder marker
    # (so the MFA knows to ask the patient verbally what brought them in)
    # We don't set it here.

    return answers


def parse_infoskop_file(path: str) -> tuple[dict[str, Any], str]:
    """Top-level entry: parse a PDF or image, return (answers, raw_text).
    Raw text is returned for debugging/preview in the UI."""
    text = extract_raw_text(path)
    if not text:
        return {}, ""
    answers = parse_infoskop_text(text)
    return answers, text
