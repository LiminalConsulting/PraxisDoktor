"""
EBM-specific rules. The GOP-constraint table below is hand-curated from
public sources (G-BA Krebsfrüherkennungs-RL §25, KBV-EBM Chapter 26 preamble,
reimbursement.info, monkeymed.de). It covers the highest-leverage urology
GOPs per the research brief — extending it beyond the top-30 needs the
next research pass (quarterly scrape of ebm.kbv.de Excel-export per Kapitel).

When that scrape lands, replace `_GOP_CONSTRAINTS` with the parsed dataset
and add a quarterly-update CI step.

Citations:
- KFE-RL §25 (G-BA): age + gender for the 01730er Vorsorge-Reihe
- EBM Kapitel III.b 26 preamble: Fachgruppen-Restriktion + age bands
- EBA-Beschluss: Orientierungswert 2026 = 12,7404 ct
- §106d Abs. 6 SGB V: Tagesprofil-Aufgreifkriterium
"""
from __future__ import annotations
from datetime import date
from dataclasses import dataclass
from typing import Literal, Optional

from ..medical_office.schema import AbrechnungPosition, Patient
from .engine import Rule, RuleIssue


# Orientierungswert (€ per Punkt) for 2026 (Beschluss EBA 2025-09).
# https://www.kbv.de/praxis/abrechnung/ebm  +  https://www.psyprax.de/orientierungswert2026/
ORIENTIERUNGSWERT_2026_EUR = 0.127404


@dataclass
class GOPConstraint:
    """Constraints for a specific EBM GOP. Optional fields = no constraint."""
    code: str
    label: str
    min_age: Optional[int] = None         # inclusive
    max_age: Optional[int] = None         # inclusive
    sex: Optional[Literal["M", "W"]] = None  # restrict to one sex
    max_per_quarter: Optional[int] = None
    max_per_year: Optional[int] = None
    max_per_behandlungsfall: Optional[int] = None
    fachgruppe: Optional[str] = None       # e.g. "26" (Urologe)
    source: Optional[str] = None


# Top-30-ish urology GOPs. Hand-curated; extend from quarterly scrape.
_GOP_CONSTRAINTS: dict[str, GOPConstraint] = {
    # --- Vorsorge / Krebsfrüherkennung (G-BA KFE-RL §25) ---
    "01731": GOPConstraint(
        code="01731", label="Krebsfrüherkennung Mann (Prostata, Genitale)",
        min_age=45, sex="M", max_per_year=1,
        source="G-BA KFE-RL §25",
    ),
    "01730": GOPConstraint(
        code="01730", label="Krebsfrüherkennung Frau",
        min_age=20, sex="W", max_per_year=1,
        source="G-BA KFE-RL §25",
    ),
    "01732": GOPConstraint(
        code="01732", label="Gesundheitsuntersuchung (Check-Up)",
        min_age=35, max_per_year=1,
        source="G-BA Gesundheitsuntersuchungs-RL",
    ),

    # --- Urologische Grundpauschalen (EBM Kapitel 26) ---
    "26210": GOPConstraint(
        code="26210", label="Urologische Grundpauschale ≤5 LJ",
        max_age=5, fachgruppe="26", max_per_behandlungsfall=1,
        source="EBM Kap. III.b 26",
    ),
    "26211": GOPConstraint(
        code="26211", label="Urologische Grundpauschale 6–59 LJ",
        min_age=6, max_age=59, fachgruppe="26", max_per_behandlungsfall=1,
        source="EBM Kap. III.b 26",
    ),
    "26212": GOPConstraint(
        code="26212", label="Urologische Grundpauschale ≥60 LJ",
        min_age=60, fachgruppe="26", max_per_behandlungsfall=1,
        source="EBM Kap. III.b 26",
    ),
    "26310": GOPConstraint(
        code="26310", label="Urethro(zysto)skopie Mann",
        sex="M", fachgruppe="26", max_per_behandlungsfall=1,
        source="EBM Kap. III.b 26.3 (KVSH/KVWL urology summary)",
    ),
    "26311": GOPConstraint(
        code="26311", label="Urethro(zysto)skopie Frau",
        sex="W", fachgruppe="26", max_per_behandlungsfall=1,
        source="EBM 26311 (KBV)",
    ),

    # --- Sonografie (general; not Fachgruppe-restricted) ---
    "33042": GOPConstraint(
        code="33042", label="Sonografie Abdomen (1+ Organe)",
        max_per_behandlungsfall=2,
        source="EBM 33042 (monkeymed.de)",
    ),
    "33043": GOPConstraint(
        code="33043", label="Sonografie Urogenitalsystem",
        max_per_behandlungsfall=1,
        source="EBM 33043; KV Berlin Ausschlüsse pn231218-3",
    ),

    # --- Brief-Workflow (Erstellung + KIM-Versand/Empfang) ---
    "01601": GOPConstraint(
        code="01601", label="Individueller Arztbrief",
        source="EBM 01601 (reimbursement.info)",
    ),
    "86900": GOPConstraint(
        code="86900", label="Versandpauschale eArztbrief via KIM",
        source="EBM 86900; KV Hessen — Quartals-Cap 23,40 € / Arzt zusammen mit 86901",
    ),
    "86901": GOPConstraint(
        code="86901", label="Empfangspauschale eArztbrief via KIM",
        source="EBM 86901; KV Hessen — Quartals-Cap 23,40 € / Arzt zusammen mit 86900",
    ),

    # --- ePA-Befüllung (extrabudgetär bis 30.06.2026) ---
    "01647": GOPConstraint(
        code="01647", label="ePA — weitere Befüllung im Behandlungsfall (mit AP-Kontakt)",
        max_per_behandlungsfall=1,
        source="EBM 01647 (KV Hessen ePA abrechnen) — 1,91 € / 15 P",
    ),
    "01648": GOPConstraint(
        code="01648", label="ePA-Erstbefüllung (sektorenübergreifend einmalig)",
        source="EBM 01648 (KBV PraxisNachricht 2025-11-27) — 11,34 € / 89 P, befristet bis 30.06.2026",
    ),
    "01431": GOPConstraint(
        code="01431", label="ePA — Befüllung ohne AP-Kontakt",
        source="EBM 01431 (KV Hessen)",
    ),

    # --- Wegfallene GOP — sentinel for legacy templates ---
    # GOP 01660 (Förderzuschlag eArztbrief) WEGGEFALLEN 30.06.2023.
    # Not added as a constraint; instead, see legacy_codes_check below.

    # --- Telekonsultation / Bereitschaft (general) ---
    "01434": GOPConstraint(
        code="01434", label="Telefonkonsultation",
        max_per_behandlungsfall=5,
        source="EBM 01434",
    ),
    "01435": GOPConstraint(
        code="01435", label="Bereitschaftspauschale",
        max_per_behandlungsfall=1,
        source="EBM 01435",
    ),

    # --- Versichertenpauschale (Hausarzt-Kontext, manchmal von Urologen
    #     mitgebraucht) ---
    "03000": GOPConstraint(
        code="03000", label="Versichertenpauschale Hausarzt",
        max_per_behandlungsfall=1,
        source="EBM 03000",
    ),
}


def _calc_age_on(d: Optional[date], dob: Optional[date]) -> Optional[int]:
    if d is None or dob is None:
        return None
    age = d.year - dob.year - ((d.month, d.day) < (dob.month, dob.day))
    return age


def _quartal_of(d: Optional[date]) -> Optional[str]:
    if d is None:
        return None
    return f"{d.year}Q{(d.month - 1) // 3 + 1}"


# ---------------------------------------------------------------------------
# Age + gender restrictions
# ---------------------------------------------------------------------------
def _age_gender_restrictions(
    positions: list[AbrechnungPosition], patient: Patient
) -> list[RuleIssue]:
    issues: list[RuleIssue] = []
    for p in positions:
        if p.katalog != "EBM":
            continue
        c = _GOP_CONSTRAINTS.get(p.code)
        if c is None:
            continue

        if c.sex and patient.geschlecht and patient.geschlecht != c.sex:
            sex_label = "männliche" if c.sex == "M" else "weibliche"
            issues.append(RuleIssue(
                severity="error",
                rule_id="ebm.sex_restriction",
                rule_name="GOP geschlechtsbeschränkt",
                position_ids=[p.id],
                message=(
                    f"GOP {p.code} ({c.label}) ist nur für {sex_label} Patienten "
                    f"abrechenbar; Patient ist {('männlich' if patient.geschlecht == 'M' else 'weiblich')}."
                ),
                source=c.source,
            ))

        age = _calc_age_on(p.leistungsdatum, patient.geburtsdatum)
        if age is not None:
            if c.min_age is not None and age < c.min_age:
                issues.append(RuleIssue(
                    severity="error",
                    rule_id="ebm.age_below_min",
                    rule_name="GOP unterhalb Mindestalter",
                    position_ids=[p.id],
                    message=(
                        f"GOP {p.code} ({c.label}) ist erst ab {c.min_age} Jahren "
                        f"abrechenbar; Patient war am Leistungstag {age} Jahre alt."
                    ),
                    source=c.source,
                ))
            if c.max_age is not None and age > c.max_age:
                issues.append(RuleIssue(
                    severity="error",
                    rule_id="ebm.age_above_max",
                    rule_name="GOP oberhalb Höchstalter",
                    position_ids=[p.id],
                    message=(
                        f"GOP {p.code} ({c.label}) ist nur bis {c.max_age} Jahre "
                        f"abrechenbar; Patient war am Leistungstag {age} Jahre alt."
                    ),
                    source=c.source,
                ))
    return issues


# ---------------------------------------------------------------------------
# Frequency limits within the loaded position set
# (per_quarter, per_year, per_behandlungsfall — the latter scoped to the
# positions passed in, which is one Fall when called from the rechnungspruefung
# router).
# ---------------------------------------------------------------------------
def _frequency_limits(
    positions: list[AbrechnungPosition], patient: Patient
) -> list[RuleIssue]:
    issues: list[RuleIssue] = []
    by_code: dict[str, list[AbrechnungPosition]] = {}
    for p in positions:
        if p.katalog != "EBM":
            continue
        by_code.setdefault(p.code, []).append(p)
    for code, group in by_code.items():
        c = _GOP_CONSTRAINTS.get(code)
        if c is None:
            continue
        if c.max_per_behandlungsfall is not None and len(group) > c.max_per_behandlungsfall:
            issues.append(RuleIssue(
                severity="warning",
                rule_id="ebm.frequency_per_behandlungsfall",
                rule_name="Häufigkeit pro Behandlungsfall überschritten",
                position_ids=[p.id for p in group],
                message=(
                    f"GOP {code} ({c.label}) {len(group)}× im Behandlungsfall — "
                    f"erlaubt sind {c.max_per_behandlungsfall}×."
                ),
                source=c.source,
            ))
        # Quartal limit — count occurrences in same quarter
        if c.max_per_quarter is not None:
            by_q: dict[str, int] = {}
            for p in group:
                q = _quartal_of(p.leistungsdatum)
                if q:
                    by_q[q] = by_q.get(q, 0) + 1
            for q, n in by_q.items():
                if n > c.max_per_quarter:
                    issues.append(RuleIssue(
                        severity="warning",
                        rule_id="ebm.frequency_per_quarter",
                        rule_name="Häufigkeit pro Quartal überschritten",
                        position_ids=[p.id for p in group if _quartal_of(p.leistungsdatum) == q],
                        message=f"GOP {code} ({c.label}) im {q} {n}× — erlaubt sind {c.max_per_quarter}×.",
                        source=c.source,
                    ))
        if c.max_per_year is not None:
            by_y: dict[int, int] = {}
            for p in group:
                if p.leistungsdatum:
                    y = p.leistungsdatum.year
                    by_y[y] = by_y.get(y, 0) + 1
            for y, n in by_y.items():
                if n > c.max_per_year:
                    issues.append(RuleIssue(
                        severity="warning",
                        rule_id="ebm.frequency_per_year",
                        rule_name="Häufigkeit pro Kalenderjahr überschritten",
                        position_ids=[p.id for p in group if p.leistungsdatum and p.leistungsdatum.year == y],
                        message=f"GOP {code} ({c.label}) im Jahr {y} {n}× — erlaubt ist {c.max_per_year}×.",
                        source=c.source,
                    ))
    return issues


# ---------------------------------------------------------------------------
# Bewertung × Orientierungswert sanity check
# ---------------------------------------------------------------------------
def _ow_calc_sanity(
    positions: list[AbrechnungPosition], patient: Patient
) -> list[RuleIssue]:
    out = []
    for p in positions:
        if p.katalog != "EBM" or p.punkte is None or p.betrag_eur is None:
            continue
        expected = round(p.punkte * ORIENTIERUNGSWERT_2026_EUR, 2)
        if abs(expected - p.betrag_eur) > 0.05:  # 5-cent tolerance
            out.append(RuleIssue(
                severity="info",
                rule_id="ebm.ow_calc_mismatch",
                rule_name="Punktzahl × Orientierungswert weicht ab",
                position_ids=[p.id],
                message=(
                    f"GOP {p.code}: {p.punkte} Pkt × {ORIENTIERUNGSWERT_2026_EUR:.6f} € "
                    f"= {expected:.2f} €; gespeichert: {p.betrag_eur:.2f} €."
                ),
                suggestion="Quartals-Punktwert prüfen (kann sich mit jedem EBA-Beschluss ändern).",
                source="EBA-Beschluss Q1/2026: OW = 12,7404 ct",
            ))
    return out


# ---------------------------------------------------------------------------
# KIM Strukturpauschalen: 86900 + 86901 zusammen gedeckelt 23,40 € / Quartal /
# Arzt. Without per-Arzt attribution we still catch egregious overruns within
# the position set passed in.
# ---------------------------------------------------------------------------
_KIM_QUARTAL_CAP_EUR = 23.40

def _kim_quartal_cap(
    positions: list[AbrechnungPosition], patient: Patient
) -> list[RuleIssue]:
    by_q: dict[str, list[AbrechnungPosition]] = {}
    for p in positions:
        if p.katalog != "EBM" or p.code not in ("86900", "86901"):
            continue
        q = _quartal_of(p.leistungsdatum)
        if q is None:
            continue
        by_q.setdefault(q, []).append(p)

    out: list[RuleIssue] = []
    for q, group in by_q.items():
        total = sum((p.betrag_eur or 0.0) for p in group)
        if total > _KIM_QUARTAL_CAP_EUR + 0.001:
            out.append(RuleIssue(
                severity="warning",
                rule_id="ebm.kim_quartal_cap",
                rule_name="KIM-Strukturpauschalen Quartals-Cap überschritten",
                position_ids=[p.id for p in group],
                message=(
                    f"86900 + 86901 im {q}: {total:.2f} € — Höchstwert "
                    f"{_KIM_QUARTAL_CAP_EUR:.2f} € pro Arzt/Quartal."
                ),
                suggestion="Im Per-Arzt-Kontext prüfen: gilt der Cap pro LANR.",
                source="KV Hessen: eArztbrief, Porto, Faxe abrechnen",
            ))
    return out


# ---------------------------------------------------------------------------
# Legacy / abolished GOPs — sentinel check.
# 01660 (Förderzuschlag eArztbrief) abolished 30.06.2023; many PVS templates
# still emit it. Caught early before KV streichung.
# ---------------------------------------------------------------------------
_ABOLISHED_GOPS: dict[str, str] = {
    "01660": (
        "GOP 01660 (Förderzuschlag eArztbrief) ist seit 30.06.2023 weggefallen. "
        "Stattdessen 01601 (Brief-Erstellung) + 86900 (KIM-Versand) ansetzen."
    ),
}

def _abolished_gops(
    positions: list[AbrechnungPosition], patient: Patient
) -> list[RuleIssue]:
    out: list[RuleIssue] = []
    for p in positions:
        if p.katalog != "EBM":
            continue
        msg = _ABOLISHED_GOPS.get(p.code)
        if msg:
            out.append(RuleIssue(
                severity="error",
                rule_id="ebm.abolished_gop",
                rule_name="Weggefallene GOP",
                position_ids=[p.id],
                message=msg,
                source="IWW: 01660 weggefallen 30.06.2023",
            ))
    return out


RULES: list[Rule] = [
    Rule(id="ebm.age_gender_restrictions",
         name="Alters- und Geschlechtsbeschränkungen",
         catalog="EBM", fn=_age_gender_restrictions,
         source="G-BA KFE-RL §25; EBM Kap. 26"),
    Rule(id="ebm.frequency_limits",
         name="Häufigkeitsbeschränkungen",
         catalog="EBM", fn=_frequency_limits,
         source="EBM Anhang 1"),
    Rule(id="ebm.ow_calc_sanity",
         name="Bewertung × Orientierungswert",
         catalog="EBM", fn=_ow_calc_sanity,
         source="EBA-Beschluss"),
    Rule(id="ebm.kim_quartal_cap",
         name="KIM-Strukturpauschalen Quartals-Cap (86900+86901)",
         catalog="EBM", fn=_kim_quartal_cap,
         source="KV Hessen eArztbrief"),
    Rule(id="ebm.abolished_gops",
         name="Weggefallene GOPs (01660 etc.)",
         catalog="EBM", fn=_abolished_gops,
         source="IWW 30.06.2023"),
]
