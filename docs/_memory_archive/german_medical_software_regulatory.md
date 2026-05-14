---
name: German Medical Software — Regulatory & Vendor Landscape
description: Hard architectural boundaries (KBV, gematik KOB, MDR, §203 StGB) for any AI tool sitting alongside a German PVS — verified 2026-04-24
type: project
originSessionId: f5bdb875-89ff-475c-b6fa-6c94427cf63b
---
# German Praxis Software — Regulatory Landscape (verified 2026-04-24)

Full grounded brief at `PraxisDoktor/docs/regulatory_landscape.md`. This memory is the operational summary.

## The architectural posture that protects the build

**The certified PVS (Medical Office / CGM / T2med / etc.) stays in place as the system of record. The custom system never produces KVDT, never speaks TI protocols directly, and writes its Zweckbestimmung as "Dokumentationsassistenz, keine Diagnose."** That single posture sidesteps three certification regimes and keeps the build at freelance scale.

**Why:** Three regimes will end the project if crossed:
1. **KBV-Zulassung** for KVDT generation (quarterly EBM update treadmill, multi-FTE-year barrier)
2. **gematik KOB** (DigiG, mandatory from 01.01.2026 for any TI-touching PVS — only 141 systems passed across all of Germany as of mid-2025)
3. **MDR Class IIa** under Rule 11 (triggered if AI is positioned as decision-support for diagnosis/therapy — Notified Body required, not self-certifiable)

**How to apply:** For any German medical-practice client, default to the coexistence pattern: read from the PVS database (BDT/GDT/proprietary export), write back drafts the doctor confirms, never auto-push to billing, never call TI services directly. The leverage zone (Infoskop replacement, ambient transcription, GOÄ pre-staging, Privatabrechnung export, dashboard unification) is entirely outside any certification regime.

## The protective Zweckbestimmung sentence (file in writing, every project)

> *Ärztliche Dokumentationsassistenz und Praxisorganisation, keine Diagnose-, Therapie- oder Überwachungsfunktion.*

Plus: every AI output logged as "Vorschlag zur ärztlichen Prüfung", no UI affordance to accept AI text without conscious confirmation.

## Two papers must be signed before touching real Patientendaten

1. **AVV under Art. 28 DSGVO** (Auftragsverarbeitungsvertrag)
2. **Verschwiegenheitsverpflichtung nach § 203 Abs. 4 StGB** with explicit Strafbarkeitshinweis (developer himself becomes strafbar if he leaks)

KBV's own Hinweise warn explicitly against informal Familienarrangements — the family relationship doesn't relax this.

## Cloud LLM/STT calls for clinical text are not § 203-clean

Local Whisper (faster-whisper / whisper.cpp) on practice hardware keeps the chain short and avoids Schrems-II / US-CLOUD-Act exposure. Anthropic/OpenAI Whisper API for clinical text requires enterprise BAA-equivalent contracts with EU residency — practically out of reach.

## The "1% Honorarkürzung" — verified

§ 341 Abs. 6 SGB V. Pauschal 1% Honorarkürzung if practice can't demonstrate ePA-readiness. TI-Pauschale halved if ePA module missing. Additional 2.5% Kürzung if no proven TI-Anbindung. Active Q1 2026.

**The sanction is on the doctor, not the vendor — but only a KOB-zertifiziertes PVS satisfies it.** As long as the certified PVS stays the system of record, this is the incumbent's problem to keep certified.

## Vendor landscape headlines

- **CGM + medatixx duopoly:** ~65% of top-9 PVS in Allgemeinmedizin (KBV ADT-Statistik Q1/2025)
- **CGM ownership:** CVC Capital Partners closed voluntary takeover Q1 2025; founding family Gotthardt + Koop retain 50.1%; **delisted 24.06.2025**
- **CGM founder politics — be precise:** Frank Gotthardt donated ~€180k to CDU + ~€200k to FDP in Jan 2025; **no documented AfD donations**. He finances Nius (Reichelt's right-wing portal). Conflating CDU-donor + Nius-financier with "AfD" is defamatory and undermines the (correct) "Kartell-strukturen" critique.
- **T2med (Kiel):** doctor-built, KBV-zertifiziert, only growing system; **€1,900 one-time + €115/mo** (much cheaper than commonly remembered). Cleanest "if we have to live with a certified PVS, it should be this one" option.
- **User satisfaction:** CGM consistently ranks near the bottom; T2med + Tomedo near the top (Zi 2024, Virchowbund 2024/2026).

## Card-reader pipeline is sealed

eGK card terminals (Cherry ST-1506, Worldline ORGA, ZEMO VML-GK2) → Konnektor → PVS is sealed end-to-end by gematik. **Read VSDM downstream from the PVS database, not from the card.** Bypassing the Konnektor would void TI certification and likely violate § 291 SGB V.

## EBM vs GOÄ — what's vendorable

- **EBM:** Quarterly updates published on `update.kbv.de` (Hersteller-only access keys). Structural commitment — take it on or don't.
- **GOÄ:** Frozen since 1996. Stable enough to vendor as static dataset. **GOÄneu** draft Jan 2026 (~948pp), Verordnungsentwurf expected mid-2026 — changes this within 12–18 months.
- The "GOÄ-Tipps" Privatärztliche Verrechnungsstellen give doctors are codifiable — explicitly within scope (administrative, not under KOB).

## "PVS" name collision

In doctor-talk, "PVS" can mean:
- **Praxisverwaltungssystem** (the software running the practice)
- **Privatärztliche Verrechnungsstelle** (external billing service for private invoices, 3–8% commission, e.g. PVS Südwest in BW)

Disambiguate from context every time.
