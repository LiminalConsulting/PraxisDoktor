"""
Rule engine for invoice plausibility checks.

A Rule is a pure function. The engine runs all rules and collects issues.
Severity drives UI ordering (errors first, then warnings, then info).

Rule signature is intentionally minimal — passing only what's needed
keeps each rule unit-testable. When a rule needs more context (ICD-10
codes, treatment dates from another fall, …), extend the dataclass
that gets passed in, not the function signature.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Callable, Literal, Optional, Iterable

from ..medical_office.schema import AbrechnungPosition, Patient


RuleSeverity = Literal["info", "warning", "error"]


@dataclass
class RuleIssue:
    severity: RuleSeverity
    rule_id: str            # short stable id, e.g. "ebm.duplicate"
    rule_name: str          # human-readable
    position_ids: list[str] # AbrechnungPosition ids the issue concerns
    message: str            # German, user-facing
    suggestion: Optional[str] = None
    source: Optional[str] = None  # citation: "GOÄ §5 Abs. 2", "EBM-Anhang 4", …


@dataclass
class Rule:
    id: str
    name: str
    catalog: Literal["EBM", "GOÄ", "*"]    # which catalog it applies to
    fn: Callable[[list[AbrechnungPosition], Patient], list[RuleIssue]]
    source: Optional[str] = None           # documentation citation


def run_rules(
    positions: list[AbrechnungPosition],
    patient: Patient,
    rules: Optional[Iterable[Rule]] = None,
) -> list[RuleIssue]:
    rules = rules if rules is not None else RULES
    issues: list[RuleIssue] = []
    catalogs = {p.katalog for p in positions}
    for r in rules:
        if r.catalog != "*" and r.catalog not in catalogs:
            continue
        try:
            issues.extend(r.fn(positions, patient))
        except Exception as e:
            issues.append(RuleIssue(
                severity="warning",
                rule_id=f"engine.rule_failed.{r.id}",
                rule_name=f"Regel-Fehler: {r.name}",
                position_ids=[],
                message=f"Regel '{r.name}' konnte nicht ausgeführt werden: {e}",
            ))
    issues.sort(key=lambda i: {"error": 0, "warning": 1, "info": 2}[i.severity])
    return issues


# ---------------------------------------------------------------------------
# Built-in rule set — universal rules that don't require KBV-key data.
# Domain-specific EBM/GOÄ rules land in rules_*.py modules and are imported below.
# ---------------------------------------------------------------------------
from .rules_universal import RULES as _UNIVERSAL_RULES
from .rules_goae import RULES as _GOAE_RULES
from .rules_ebm import RULES as _EBM_RULES

RULES: list[Rule] = [*_UNIVERSAL_RULES, *_GOAE_RULES, *_EBM_RULES]
