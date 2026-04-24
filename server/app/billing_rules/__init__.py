"""
Plausibility / consistency rules for German EBM (statutory) and GOÄ (private)
invoice positions. Each rule is a pure function:

    rule(positions: list[AbrechnungPosition], patient: Patient) -> list[Issue]

Adding a new rule = adding a new function and registering it in `RULES`.
The engine runs all applicable rules per (patient, fall, positions) and
aggregates the issues.

## Rule sources

- Generic / always-true (no source needed): duplicate detection, faktor sanity
- GOÄ §5: Schwellenwert + Begründungspflicht (publicly available in the
  Gebührenordnung text, §5 Abs. 2)
- Sex-restricted GOPs: derived from EBM Chapter 26 (urology) — pending
  research-agent validation
- EBM Ausschlüsse + frequency limits: pending research-agent validation
  (likely Hersteller-key-only at full coverage)

When the research brief lands at docs/billing_rules.md, drop in the new
rule modules under server/app/billing_rules/rules_*.py and register them
in the RULES list below.
"""
from __future__ import annotations

from .engine import (
    RuleIssue,
    RuleSeverity,
    Rule,
    run_rules,
    RULES,
)

__all__ = ["RuleIssue", "RuleSeverity", "Rule", "run_rules", "RULES"]
