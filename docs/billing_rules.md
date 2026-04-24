# Billing Rules — Research Brief (EBM + GOÄ, Q1/Q2 2026)

Source for what `server/app/billing_rules/` implements.

## Three structural realities

1. **The rule corpus itself is public.** EBM is a federal regulation; GOÄ is a federal ordinance. Both downloadable as PDF; EBM also browsable as HTML at `ebm.kbv.de`.
2. **The structured machine-readable corpus is largely Hersteller-only.** KBV's `update.kbv.de` Stamm-data and the KVDT Anforderungskatalog are gated behind the §332b SGB V Rahmenvereinbarung. Without that, scrape `ebm.kbv.de` HTML or parse the quarterly PDF.
3. **There is essentially no open-source EBM/GOÄ rule library.** GitHub-wide search returns exactly **one** small unmaintained Java tool (`gitterrost4/ebmcrawler`, 1 star, last commit 2023). The rule database is something we build ourselves from public sources.

---

## Encodable now (no Hersteller key)

### EBM rules

| ID | Rule | Source |
|---|---|---|
| EBM-R1 | "in derselben Sitzung nicht neben" — exclusion within session | KV-Saarland Allgemeine Abrechnungsbestimmungen |
| EBM-R2 | "am Behandlungstag nicht neben" — exclusion within calendar day | EBM general provisions |
| EBM-R3 | "im Behandlungsfall nicht neben" — exclusion within practice/patient/insurance/quarter | §21 Abs. 1 BMV-Ä |
| EBM-R4 | "im Krankheitsfall nicht neben" — current quarter + 3 subsequent | §21 Abs. 1 BMV-Ä — **needs longitudinal data** |
| EBM-R5 | "im Arztfall nicht neben" — same Arzt + patient + quarter | §21 Abs. 1b BMV-Ä |
| EBM-R6 | Frequency limits (`höchstens X-mal im [Zeitkontext]`) — e.g. GOP 01731 1× im Kalenderjahr | reimbursement.info, monkeymed.de, KFE-RL |
| EBM-R7 | Age restrictions (e.g. 26210 ≤ 5 LJ; 26212 ≥ 60 LJ; 01731 ≥ 45 LJ) | EBM Kapitel III.b 26 preamble |
| EBM-R8 | Gender restrictions (e.g. GOP 01731 nur Männer) | G-BA Krebsfrüherkennungs-RL §25 |
| EBM-R9 | Fachgruppen-Restriktion (Chapter 26 only Urologen) | EBM Kapitel III.b 26 preamble |
| EBM-R10 | Bewertung × Orientierungswert calculation (€ = Punktzahl × 0,127404 € im Jahr 2026) | EBA-Beschluss |
| EBM-R11 | Tagesprofil Aufgreifkriterium (>720 min an ≥3 Tagen/Quartal) | §106d Abs. 6 SGB V; KBV/GKV-SV-Richtlinie; Anhang 3 EBM |
| EBM-R12 | Quartalsprofil Aufgreifkriterium (>780 h Vollzulassung / >390 h halbe) | same as R11 |
| EBM-R13 | Mindestzeit-GOPs ("mindestens 10 Min") — z.B. 03230, 35110 | EBM Legenden |

### GOÄ rules

| ID | Rule | Source |
|---|---|---|
| GOÄ-R1 | Schwellenwert per Leistungsklasse (§5 GOÄ): 2,3/3,5 (B/C/D/F/G/H/I/J/K/L/N/P), 1,8/2,5 (A/E/O), 1,15/1,3 (M-Labor) | gesetze-im-internet.de §5 GOÄ |
| GOÄ-R2 | Begründungspflicht bei Schwellenwert-Überschreitung; floskel-blacklist ("erhöhter Zeitaufwand", "technisch schwierig", "besondere Qualifikation", "Inflation") | §12 Abs. 3 GOÄ; Virchowbund |
| GOÄ-R3 | Schriftliche Vereinbarung > 3,5 (resp. > 2,5 für technisch, > 1,3 für Labor); ohne sie plafondiert auf Höchstsatz | §2 Abs. 1, 2 GOÄ |
| GOÄ-R4 | §12 Abs. 2 Pflichtangaben pro Zeile (Datum, Nr., Beschreibung, Faktor, Betrag, ggf. "analog Nr. xxxx") | §12 GOÄ |
| GOÄ-R5 | Analogabrechnung-Kennzeichnung — most-cited GOÄ formal error | §6 Abs. 2 GOÄ |
| GOÄ-R6 | Zielleistungsprinzip — absorption pairs | §4 Abs. 2a GOÄ; BÄK Abrechnungsempfehlungen |
| GOÄ-R7 | §6a stationäre Minderung (25% / 15% Beleg) | §6a GOÄ |
| GOÄ-R8 | Auslagen / §10 — only patient-keepable or single-use consumed | §10 GOÄ |

## Blocked on data extension (encodable later)

- **EBM-D1** Diagnose-Pflicht — needs ICD-10-GM extraction
- **EBM-D2** Krankheitsfall frequencies — needs 4-quarter longitudinal store
- **EBM-D3** Sitzung vs Behandlungstag granularity — session-level marker
- **EBM-D4** Anhang-1 absorption (kleine Leistungen in Grundpauschale enthalten)
- **EBM-D5** Genehmigungspflichtige Leistungen — per-Arzt Genehmigungsregister
- **EBM-D6** Zuschläge an Tageszeit / Wochentag — uhrzeitgenaue Erbringungszeit needed
- **GOÄ-D1** Faktorbegründung mit Patientenbezug — LLM grading against floskel-blacklist
- **GOÄ-D2** §4 Abs. 5 Vertretung / Assistenten — Erbringer-Feld per line

## Out of scope (Hersteller-key)

- KVDT-Datensatz grammar (paywall)
- Stamm-XML quarterly distribution
- eGK / TI-Plausi (requires Konnektor)
- Schein-Logik
- Regional KV-Honorarverteilungsmaßstab (HVM)

## Highest-leverage rules to implement first (per Virchowbund + KV-Merkblätter)

1. **GOÄ-R2** Begründungspflicht > 2,3 / 1,8 / 1,15 — single most-cited PKV-Beanstandung
2. **GOÄ-R5** Analog-Kennzeichnung — second-most-cited formal error
3. **GOÄ-R1** Schwellenwert-Korrektheit
4. **EBM-R7/R8** Alter & Geschlecht — eliminates whole class of "Schein zurückgeschickt"
5. **EBM-R6** Frequenzlimits (1× im Behandlungsfall / Quartal)
6. **EBM-R10** Punktzahl × OW
7. **EBM-R1/R2** Sitzung / Behandlungstag exclusions for top-30 urology GOPs (26210–26228, 26310–26330, 33043, 01731, 01430–01435)
8. **GOÄ-R6** Zielleistung for top-15 urology OPs (Zystoskopie 1785/1786, Stanzbiopsie etc.) — seed from BÄK Abrechnungsempfehlungen
9. **EBM-R11** Tagesprofil >12 h
10. **GOÄ-R7** §6a stationäre Minderung — trivial, near-zero false-positive

## Public data sources (no key required)

- **EBM HTML browser:** https://ebm.kbv.de/ — Excel/CSV export per Kapitel
- **EBM Quartals-PDF:** https://www.kbv.de/documents/praxis/abrechnung/ebm/2026-2-ebm.pdf
- **EBM Anhang 3 (Prüfzeiten):** included in quarterly PDF
- **GOÄ Volltext:** https://www.gesetze-im-internet.de/go__1982/
- **GOÄ Abrechnungsempfehlungen + Analogbewertungen:** https://www.bundesaerztekammer.de/themen/aerzte/honorar/goae
- **G-BA Krebsfrüherkennungs-RL:** https://www.g-ba.de/richtlinien/17/
- **BMV-Ä:** https://www.gkv-spitzenverband.de/krankenversicherung/aerztliche_versorgung/bundesmantelvertrag/anlagen_zum_bundesmantelvertrag/anlagen_zum_bundesmantelvertrag.jsp
- **§106d SGB V:** https://www.gesetze-im-internet.de/sgb_5/__106d.html

## Honest assessment

Three realistic options:
- **Thin GOÄ-only checker** — possible today purely from gesetze-im-internet.de + BÄK Abrechnungsempfehlungen. Catches the bulk of PKV-Beanstandungen.
- **EBM+GOÄ pre-checker with self-built rule database** — feasible by quarterly scraping of `ebm.kbv.de` (Excel/CSV export per Kapitel) + Anhang-3 Prüfzeiten parsing. ~1–2 days/quarter ongoing maintenance.
- **Full PVS-Plausi parity** — requires §332b SGB V Rahmenvereinbarung. Out of scope for a single-practice consulting tool.

**Recommendation for the urology pilot:** Options 1+2 limited to Chapter 26 + cross-cutting Verwaltungs-/Vorsorge-GOPs. Covers ≥80% of practice invoice volume with ≤5% of the rule-engine surface.
