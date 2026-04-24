"""
GOÄ-specific rules. These come from publicly-readable text of the
Gebührenordnung für Ärzte and don't require KBV-Hersteller access.

Citations refer to GOÄ paragraph numbers — the canonical reference is at
https://www.gesetze-im-internet.de/gebuehro/.
"""
from __future__ import annotations

from ..medical_office.schema import AbrechnungPosition, Patient
from .engine import Rule, RuleIssue


# GOÄ §5 Abs. 2: Steigerungs-Schwellenwerte. Above these, written
# Begründung is mandatory. Default for most positions: 2,3-fach
# Schwellenwert; allowable up to 3,5-fach with Begründung; above 3,5-fach
# only on individual contractual basis with the patient (§2 GOÄ).
_DEFAULT_SCHWELLENWERT = 2.3
_DEFAULT_HOECHSTSATZ = 3.5

# Per GOÄ §5: three Schwellenwert classes by Leistungsklasse (verified
# against gesetze-im-internet.de/go__1982/__5.html and Virchowbund/medas/
# AEK-NO summaries):
#
#   Persönlich-ärztliche Leistungen (Sections B,C,D,F,G,H,I,J,K,L,N,P):
#       Schwellenwert 2,3 / Höchstsatz 3,5
#   Medizinisch-technische Leistungen (Sections A, E, O):
#       Schwellenwert 1,8 / Höchstsatz 2,5
#   Laborleistungen (Section M):
#       Schwellenwert 1,15 / Höchstsatz 1,3
#
# Below: per-code overrides for the most-frequent Section A/E/O/M positions.
# Anything not in the table falls back to (2.3, 3.5) — the persönlich-ärztlich
# default. Extend over time from BÄK Abrechnungsempfehlungen / GOÄ-Verzeichnis.
_DEFAULT_SCHWELLENWERT = 2.3
_DEFAULT_HOECHSTSATZ = 3.5

# Schwellenwert / Höchstsatz overrides for technical and lab positions.
# Tuple = (Schwellenwert, Höchstsatz).
_SCHWELLENWERTE: dict[str, tuple[float, float]] = {
    # ---- Section A (Sonographie / Bildgebung — 1,8 / 2,5) ----
    "401": (1.8, 2.5),  # Sonographie weiterer Organe
    "410": (1.8, 2.5),  # Sonographie eines Organs
    "420": (1.8, 2.5),  # Duplex-Sonographie
    "424": (1.8, 2.5),  # Doppler-Sonographie der Penisgefäße (urology)
    # ---- Section E (Anaesthesie / physikalische Therapie — 1,8 / 2,5) ----
    "265": (1.8, 2.5),  # Lokalanästhesie
    # ---- Section O (Strahlendiagnostik — 1,8 / 2,5) ----
    "5060": (1.8, 2.5),
    "5070": (1.8, 2.5),
    # ---- Section M (Labor — 1,15 / 1,3) ----
    # Ranges 3500–3914 (Section M). Hard to enumerate exhaustively,
    # so we add the most common per the urology workflow:
    "3550": (1.15, 1.3),  # PSA
    "3580": (1.15, 1.3),  # Testosteron
    "3650": (1.15, 1.3),  # Urin-Stix / Sediment
    "3712": (1.15, 1.3),  # Mikroalbumin
}

# Begründungs-Floskeln per BGH/OLG-Linie + Virchowbund/AEK-NO/Medas: any of
# these alone is insufficient as Schwellenwert-Begründung — they must contain
# patient-specific, individuelle Zusatzangaben.
_FLOSKEL_BLACKLIST = (
    "erhöhter zeitaufwand",
    "erhoehter zeitaufwand",
    "technisch schwierig",
    "besondere qualifikation",
    "besonders aufwendig",
    "besonders aufwändig",
    "besonders aufwendige untersuchung",
    "inflation",
    "kostensteigerung",
)


def _faktor_over_schwellenwert(
    positions: list[AbrechnungPosition], patient: Patient
) -> list[RuleIssue]:
    issues: list[RuleIssue] = []
    for p in positions:
        if p.katalog != "GOÄ" or p.faktor is None:
            continue
        schwelle, hoechst = _SCHWELLENWERTE.get(p.code, (_DEFAULT_SCHWELLENWERT, _DEFAULT_HOECHSTSATZ))
        if p.faktor > hoechst:
            issues.append(RuleIssue(
                severity="error",
                rule_id="goae.faktor_above_hoechstsatz",
                rule_name="Faktor über Höchstsatz",
                position_ids=[p.id],
                message=(
                    f"Position {p.code} mit Faktor {p.faktor:g} überschreitet "
                    f"den Höchstsatz {hoechst:g}-fach."
                ),
                suggestion=(
                    "Über dem Höchstsatz ist eine schriftliche Honorarvereinbarung "
                    "nach §2 GOÄ erforderlich (vor Behandlungsbeginn mit dem Patienten)."
                ),
                source="GOÄ §5 Abs. 2 i.V.m. §2",
            ))
        elif p.faktor > schwelle:
            begruendung = (p.begruendung or "").strip()
            if not begruendung:
                issues.append(RuleIssue(
                    severity="warning",
                    rule_id="goae.faktor_over_schwellenwert_no_begruendung",
                    rule_name="Schwellenwert überschritten ohne Begründung",
                    position_ids=[p.id],
                    message=(
                        f"Position {p.code} mit Faktor {p.faktor:g} liegt über "
                        f"dem Schwellenwert {schwelle:g}-fach, ohne schriftliche Begründung."
                    ),
                    suggestion=(
                        "Schriftliche, patientenbezogene Begründung in der "
                        "Rechnung ergänzen (GOÄ §12 Abs. 3 schreibt sie vor)."
                    ),
                    source="GOÄ §5 Abs. 2 + §12 Abs. 3",
                ))
            else:
                # Floskel-check: begruendung must NOT consist only of standard phrases
                low = begruendung.lower()
                if any(low.startswith(f) and len(low) < len(f) + 15 for f in _FLOSKEL_BLACKLIST):
                    issues.append(RuleIssue(
                        severity="warning",
                        rule_id="goae.faktor_begruendung_floskel",
                        rule_name="Begründung wirkt floskelhaft",
                        position_ids=[p.id],
                        message=(
                            f"Begründung für Position {p.code} ('{begruendung}') "
                            "wirkt nach BGH-Rechtsprechung wie eine reine Standardfloskel."
                        ),
                        suggestion=(
                            "Patientenbezogenen Zusatz ergänzen "
                            "(z.B. 'wegen multimorbidem Krankheitsbild bei …')."
                        ),
                        source="BGH; Virchowbund Praxisärzte-Blog",
                    ))
    return issues


# ---------------------------------------------------------------------------
# GOÄ-R5: Analogabrechnung-Kennzeichnung (§6 Abs. 2 GOÄ).
# Most-cited GOÄ formal error per Virchowbund. We can't determine WHICH lines
# should be analog without a reference table; instead we check: any line
# whose Bezeichnung explicitly says "analog" must include the base GOÄ-Nr.
# ---------------------------------------------------------------------------
def _analog_kennzeichnung(
    positions: list[AbrechnungPosition], patient: Patient
) -> list[RuleIssue]:
    issues = []
    for p in positions:
        if p.katalog != "GOÄ" or not p.bezeichnung:
            continue
        bez = p.bezeichnung.lower()
        if "analog" in bez:
            # must reference a base Nr. like "analog Nr. 1234" or "analog 1234"
            import re
            if not re.search(r"analog\s*(nr\.?\s*)?\d{1,4}", bez):
                issues.append(RuleIssue(
                    severity="error",
                    rule_id="goae.analog_without_base_nr",
                    rule_name="Analog-Position ohne Basis-Nr.",
                    position_ids=[p.id],
                    message=(
                        f"Position {p.code} ist als analog markiert, aber die "
                        "Basis-GOÄ-Nr. fehlt in der Bezeichnung."
                    ),
                    suggestion=(
                        "Bezeichnung ergänzen (Format: 'Leistung X analog Nr. 1234')."
                    ),
                    source="GOÄ §6 Abs. 2 + §12 Abs. 2",
                ))
    return issues


# ---------------------------------------------------------------------------
# GOÄ-R7: §6a stationäre Minderung. If the leistungsdatum context indicates
# stationary treatment, Sections A/E/O/M lines must be reduced by 25%.
# We don't yet capture stationary-vs-ambulatory at the line level, so this
# is implemented as a *flag*: when the bezeichnung mentions "stationär" or
# the practice marks a Fall as stationary, prompt the user to verify reduction.
# Full implementation deferred until Fall.kontext field exists.
# ---------------------------------------------------------------------------
def _stationaere_minderung_check(
    positions: list[AbrechnungPosition], patient: Patient
) -> list[RuleIssue]:
    issues = []
    for p in positions:
        if p.katalog != "GOÄ" or not p.bezeichnung:
            continue
        if "stationär" in p.bezeichnung.lower():
            issues.append(RuleIssue(
                severity="info",
                rule_id="goae.stationaere_minderung_check",
                rule_name="§6a-Minderung prüfen (stationär)",
                position_ids=[p.id],
                message=(
                    f"Position {p.code} ist als stationär gekennzeichnet — "
                    "Minderung um 25% nach §6a GOÄ prüfen (15% bei belegärztlicher "
                    "Behandlung)."
                ),
                source="GOÄ §6a",
            ))
    return issues


def _faktor_below_minimum(
    positions: list[AbrechnungPosition], patient: Patient
) -> list[RuleIssue]:
    """GOÄ § 5 Abs. 1: Mindestsatz ist 1,0-fach. Faktor < 1,0 ist nicht zulässig."""
    issues: list[RuleIssue] = []
    for p in positions:
        if p.katalog != "GOÄ" or p.faktor is None:
            continue
        if p.faktor < 1.0:
            issues.append(RuleIssue(
                severity="error",
                rule_id="goae.faktor_below_minimum",
                rule_name="Faktor unter Mindestsatz",
                position_ids=[p.id],
                message=f"Position {p.code} mit Faktor {p.faktor:g} liegt unter Mindestsatz 1,0.",
                source="GOÄ §5 Abs. 1",
            ))
    return issues


def _missing_faktor(
    positions: list[AbrechnungPosition], patient: Patient
) -> list[RuleIssue]:
    out = []
    for p in positions:
        if p.katalog == "GOÄ" and p.faktor is None:
            out.append(RuleIssue(
                severity="error",
                rule_id="goae.missing_faktor",
                rule_name="Steigerungsfaktor fehlt",
                position_ids=[p.id],
                message=f"GOÄ-Position {p.code} ohne Steigerungsfaktor.",
                suggestion="Faktor zwischen 1,0 und 3,5 setzen.",
            ))
    return out


RULES: list[Rule] = [
    Rule(id="goae.faktor_schwellenwert_complex",
         name="Schwellenwert / Höchstsatz / Begründungsfloskel",
         catalog="GOÄ", fn=_faktor_over_schwellenwert,
         source="GOÄ §5 Abs. 2 + §12 Abs. 3"),
    Rule(id="goae.faktor_below_minimum",
         name="Faktor unter Mindestsatz",
         catalog="GOÄ", fn=_faktor_below_minimum,
         source="GOÄ §5 Abs. 1"),
    Rule(id="goae.missing_faktor",
         name="Steigerungsfaktor fehlt",
         catalog="GOÄ", fn=_missing_faktor),
    Rule(id="goae.analog_without_base_nr",
         name="Analog-Position ohne Basis-Nr.",
         catalog="GOÄ", fn=_analog_kennzeichnung,
         source="GOÄ §6 Abs. 2"),
    Rule(id="goae.stationaere_minderung_check",
         name="§6a-Minderung prüfen (stationär)",
         catalog="GOÄ", fn=_stationaere_minderung_check,
         source="GOÄ §6a"),
]
