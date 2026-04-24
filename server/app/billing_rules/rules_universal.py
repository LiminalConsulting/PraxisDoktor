"""
Catalog-independent rules — apply to any abrechnung positions regardless of
EBM vs GOÄ. These are "obviously true" rules that need no external citation.
"""
from __future__ import annotations
from collections import Counter

from ..medical_office.schema import AbrechnungPosition, Patient
from .engine import Rule, RuleIssue


def _duplicates_within_day(
    positions: list[AbrechnungPosition], patient: Patient
) -> list[RuleIssue]:
    """Same code billed multiple times on the same day → likely a copy/paste
    error. Some codes are legitimately billable >1× (Beratung, Quartalspauschalen),
    so this is a *warning*, not an error."""
    by_day: dict[tuple[str, str | None], list[AbrechnungPosition]] = {}
    for p in positions:
        key = (p.code, p.leistungsdatum.isoformat() if p.leistungsdatum else None)
        by_day.setdefault(key, []).append(p)
    issues: list[RuleIssue] = []
    for (code, day), group in by_day.items():
        if len(group) > 1:
            issues.append(RuleIssue(
                severity="warning",
                rule_id="universal.duplicate_same_day",
                rule_name="Doppelter Code am gleichen Tag",
                position_ids=[p.id for p in group],
                message=(
                    f"Position {code} ({group[0].bezeichnung or '–'}) wurde "
                    f"am {day or '?'} {len(group)}× abgerechnet."
                ),
                suggestion="Prüfen, ob die Mehrfach-Abrechnung beabsichtigt ist.",
            ))
    return issues


def _missing_leistungsdatum(
    positions: list[AbrechnungPosition], patient: Patient
) -> list[RuleIssue]:
    out = []
    for p in positions:
        if p.leistungsdatum is None:
            out.append(RuleIssue(
                severity="error",
                rule_id="universal.missing_leistungsdatum",
                rule_name="Leistungsdatum fehlt",
                position_ids=[p.id],
                message=f"Position {p.code} hat kein Leistungsdatum.",
            ))
    return out


def _unknown_catalog(
    positions: list[AbrechnungPosition], patient: Patient
) -> list[RuleIssue]:
    out = []
    for p in positions:
        if p.katalog == "Unbekannt":
            out.append(RuleIssue(
                severity="warning",
                rule_id="universal.unknown_catalog",
                rule_name="Unbekannter Gebührenkatalog",
                position_ids=[p.id],
                message=f"Position {p.code} hat keinen zugeordneten Katalog (EBM/GOÄ/…).",
                suggestion="Vor Versand klären, gegen welchen Katalog abgerechnet wird.",
            ))
    return out


RULES: list[Rule] = [
    Rule(id="universal.duplicate_same_day",   name="Doppelter Code am gleichen Tag",
         catalog="*", fn=_duplicates_within_day),
    Rule(id="universal.missing_leistungsdatum", name="Leistungsdatum fehlt",
         catalog="*", fn=_missing_leistungsdatum),
    Rule(id="universal.unknown_catalog",      name="Unbekannter Gebührenkatalog",
         catalog="*", fn=_unknown_catalog),
]
