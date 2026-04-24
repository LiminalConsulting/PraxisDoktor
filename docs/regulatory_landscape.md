# Regulatory & Vendor Landscape — Karlsruhe Urology Build

Grounded brief from the dad-conversation of 2026-04-23. Verifies (or corrects) the leads that surfaced and turns them into hard architectural boundaries.

All claims sourced; ambiguities flagged explicitly.

---

## 0. The one-paragraph version

**Medical Office stays in place as the certified billing engine. The custom system never produces KVDT, never speaks TI protocols directly, and writes its own Zweckbestimmung as "Dokumentationsassistenz, keine Diagnose."** That single posture sidesteps three certification regimes (KBV-Zulassung, gematik KOB, MDR Class IIa) and keeps the build at freelance scale. Sit-on-top-of, never replace-from-underneath. The leverage zone — Infoskop replacement, ambient transcription, GOÄ pre-staging, Privatabrechnung export, dashboard unification — is entirely outside any certification regime.

---

## 1. Two certification regimes, not one

Papa was right that "Zertifikat" matters. He was conflating two distinct ones, both of which the certified PVS holds and which we explicitly do *not* want to inherit.

### 1a. KBV-Zulassung (Anforderungskataloge)
- **Issuer:** Kassenärztliche Bundesvereinigung.
- **Scope:** EBM rules, KVDT file format (the quarterly billing submission to the KV), Formularbedruckung, eArztbrief, eDMP, ICD-10-GM coding.
- **Mechanism:** Hersteller signs the *Rahmenvereinbarung für Praxissoftware* with KBV, implements the published Anforderungskataloge (e.g. `KBV_ITA_VGEX_Anforderungskatalog_KVDT.pdf`), submits to the KBV's IT-in-der-Arztpraxis Prüfverfahren. Without a Zulassungsnummer, the KV refuses the quarterly submission.
- **Update cadence:** **Quarterly.** GOPs, Punktwerte, rule changes published on `update.kbv.de` for the next quarter. Papa is correct — this is a treadmill that justifies entire engineering teams at incumbents.
- **New-entrant cost:** Not publicly priced. Realistically multi-FTE-years. KVDT spec alone is hundreds of pages plus continuous re-testing. **This is the bigger of the two barriers.**

### 1b. KOB (Konformitätsbewertung) by gematik — **the new 2026 hurdle**
- **Legal basis:** Digital-Gesetz (DigiG, March 2024).
- **Issuer:** gematik (Bund-controlled; becoming "Digitalagentur Gesundheit" via the GDAG).
- **Scope:** Correct integration of TI Fachanwendungen — ePA für alle, e-Rezept, KIM, eAU, eHBA/SMC-B handling.
- **Cliff:** **From 01.01.2026** PVS must have passed KOB to remain KV-Abrechnung-eligible. KBV granted a 9-month grace (effective Q4 2026 hard stop) and an 18-month exception for retiring/ill/parental-leave doctors (Praxisnachrichten 04.12.2025).
- **Indicative fee:** ~€600 + VAT per Fachanwendung (administrative only — engineering work to pass test suite is the real cost).
- **As of mid-2025: only 141 systems passed KOB across all categories.** The existing oligopoly barely cleared it. New entrants are not arriving — this is the moat for the next 2–3 years.

### 1c. ECC migration (parallel hard date)
From 01.01.2026 all TI components (Konnektor, SMC-B, eHBA, SMC-KT) must be ECC-capable. Old RSA-only Konnektoren must be physically replaced. Card-issuance grace runs to mid-2026.

---

## 2. MDR boundary — exactly where to stand

EU Regulation 2017/745 (Medical Device Regulation). The decision tree lives in **MDCG 2019-11 Rev.1 (June 2025)**.

Software is a medical device **only if the manufacturer's intended purpose** is one of: diagnosis, prevention, monitoring, prediction, prognosis, treatment, alleviation. MDCG 2019-11 Rev.1 explicitly excludes:
- administrative software (booking, billing, simple records),
- communication / lossless storage of medical info,
- general well-being.

### Concrete mapping for the build

| What we ship | MDR status |
|---|---|
| Praxisverwaltung (calendar, billing, master data, EBM/GOÄ posting) | **Not a medical device.** Out of scope. |
| Whisper transcription as scribe — doctor edits and signs | **Not MDSW.** Office automation, like Dragon Medical. |
| AI suggests diagnoses / triages / flags abnormalities / extracts billable codes that drive treatment decisions | **MDSW, almost certainly Class IIa under MDR Rule 11.** Notified Body required, not self-certifiable. |
| EBM/GOÄ code suggestion from transcript | Treated as billing automation by current case practice — billing optimization is not a "medical purpose". Stay clearly here. |

### The single sentence that protects the project

The Zweckbestimmung must be filed in writing as:

> *Ärztliche Dokumentationsassistenz und Praxisorganisation, keine Diagnose-, Therapie- oder Überwachungsfunktion.*

Plus: every AI output is logged as a "Vorschlag zur ärztlichen Prüfung", and no UI affordance allows the doctor to accept AI text without conscious confirmation (the Phase-2 co-pilot pattern in the README already satisfies this).

### Open ambiguity — flag back to Papa
MDCG 2019-11 Rev.1 tightened language around AI-assisted clinical documentation but did **not** publish a bright-line carve-out for ambient scribes. BfArM has not issued specific guidance. If the product ever gets positioned as "the AI tells me what's wrong with the patient" — in marketing or in the doctor's own framing — we've crossed into Class IIa. **Keep the framing rigorously: the doctor diagnoses; the system writes faster.**

---

## 3. The "1% Umsatzabzug" — verified, with the actual paragraph

Papa was correct on both the percentage and the trigger.

- **Legal basis:** **§ 341 Abs. 6 SGB V** (Elektronische Patientenakte). Practice must demonstrate possession of the components/services necessary to use the ePA.
- **Sanction:** **pauschal 1 % Honorarkürzung** of the entire contract-medical Vergütung until Nachweis is provided.
- **Plus:** TI-Pauschale **halved** (also under § 341 Abs. 6) if ePA module missing.
- **Plus:** additional **2,5 % Kürzung** if no proven TI-Anbindung at the place of service.
- **Timeline:** ePA-Pflicht active since **01.10.2025**. Sanktionen suspended through 2025 as transition; **fully active from Q1 2026.** From Q4 2025 practices must already prove technical readiness in the Abrechnung.

**The sanction is on the doctor, not on the software vendor** — but the doctor cannot satisfy it without a KOB-zertifiziertes PVS that talks ePA. As long as Medical Office stays the system of record, this is INDAMED's problem to keep certified, not ours.

---

## 4. Telematikinfrastruktur — the coexistence path

This is the single most important architectural finding for the build.

### Components Papa mentioned (verified)
- **gematik GmbH** — Bund-majority-owned (51%), defines specs, runs Zulassung + KOB. Becoming "Digitalagentur Gesundheit".
- **Konnektor** — on-prem hardware VPN endpoint into TI. **Being phased out** under TI 2.0 in favour of software TI-Gateway + ZETA (Zero Trust Access). Transition runs 2026–2028.
- **SMC-B** (Praxisausweis) — institutional smartcard. ECC-only from 01.01.2026.
- **eHBA** — physician's personal smartcard for QES.
- **eGK** — patient insurance card → triggers VSDM (Versichertenstammdaten-Management) at reception.
- **KIM** (Kommunikation im Medizinwesen) — secure-email transport for eAU, eArztbrief, lab. Each KIM Fachanwendung needs gematik confirmation.
- **TI 2.0 / 4.0** — identity-based, federated, retires hardware tokens gradually. Mid-2026 milestone: **PoPP** (Proof of Patient Presence) for house calls.

### The architectural seam

A third-party app **does not need to re-implement TI plumbing** to operate alongside a certified PVS. Realistic seams:

1. **Read-only export from the PVS.** Most German PVS (incl. Medical Office) expose **BDT/GDT** or proprietary exports; some support FHIR. Custom app ingests these.
2. **PVS owns KVDT generation.** Quarterly KV-Abrechnung stays 100% inside the certified PVS. Custom app never produces KVDT.
3. **GDT (Gerätedatentransfer)** for instrument-style integration — the historic interface for ultrasound, ECG, lab analyzers feeding into the PVS. Custom app can pose as a GDT client, which is exactly the right semantic for "ambient scribe pushes structured fields".
4. **No direct TI calls from the custom app.** KIM, ePA, e-Rezept stay inside Medical Office. We are an "in front of" or "alongside" workspace, never a replacement.

This pattern keeps the custom app **outside the scope of KBV-Zulassung and KOB entirely** because it never authors KV-bound data and never speaks TI protocols.

### Card-reader pipeline — sealed
Papa raised this. The full picture: all eGK card terminals must be gematik-zugelassen (Cherry ST-1506, Worldline/Ingenico ORGA, ZEMO VML-GK2). The card reader → Konnektor → PVS pipeline is sealed end-to-end by gematik specs. The eGK insurance master data lands inside the PVS database after the Konnektor decrypts and validates.

**Read VSDM downstream from the PVS database, not from the card.** Bypassing the Konnektor would void the practice's TI certification and likely violate § 291 SGB V.

### Public-site → tunnel → practice server (Drittlandtransfer scope)

The public marketing site lives on **Cloudflare Pages** (US-incorporated company); booking + Anamnesebogen submissions transit Cloudflare's network via **Cloudflare Tunnel** before terminating on the practice server. This is a Drittlandtransfer in the strict DSGVO sense.

What's transmitted:
- **Booking request** — name, contact (phone/email), free-text reason, desired slot.
- **Anamnesebogen submission** — name, DOB, free-text answers (medical history).

Why this is acceptable for a small practice today:
- **Patient gives explicit consent** by submitting a form on the practice's own website (Art. 9 Abs. 2 lit. a DSGVO — Einwilligung). The submission flow includes a clear DSGVO consent checkbox + privacy notice (`/datenschutz` page).
- **No data is stored at the edge.** Cloudflare is a tube; the only persistence is on the practice server inside the LAN.
- **Patients have alternatives.** Anyone uncomfortable can phone the practice instead — the form is a convenience, not a gate.
- **Comparable to the displaced status quo.** Infoskop (synMedico) and TerMed (INDAMED) routed the same data through their own SaaS infrastructure; we are upgrading sovereignty (data terminates on practice hardware, not in a vendor's cloud), not regressing.

If the volume scales or a Datenschutzbehörde audit raises the bar:
- Switch to **Cloudflare's EU Data Localisation Suite** (paid, but EU-only data plane with cleaner DPA story).
- Or migrate the tunnel to a **tiny EU VPS running nginx + WireGuard** to the practice — same architecture, no US-incorporated provider in the path. The custom app is portable to either.

**Sign with Cloudflare:** standard Cloudflare DPA (auto-accepted at signup) + their SCCs (Standard Contractual Clauses) module covers the Drittlandtransfer per Art. 46 DSGVO. No additional paperwork required for the free-tier Pages + Tunnel.

---

## 5. § 203 StGB + DSGVO — what the freelance dev actually has to sign

### The legal frame
- **§ 203 Abs. 3 S. 2 StGB** (since the 2017 reform): the physician may disclose patient information to "sonstige mitwirkende Personen" — explicitly named in legislative materials as IT-Wartung, Hosting, Software-Entwicklung — **provided** they are contractually bound to Verschwiegenheit.
- **DSGVO Art. 9 Abs. 1**: health data is special category, default-prohibited; processed only under Art. 9 Abs. 2 lit. h (Behandlungszweck) + Art. 9 Abs. 3 (professional secrecy).
- **DSGVO Art. 28 AVV** (Auftragsverarbeitungsvertrag): mandatory.
- **§ 22 BDSG** mirrors Art. 9 with German specifics on TOMs.

### What I actually have to sign with Papa

1. **Two papers, not one:**
   - AVV under Art. 28 DSGVO, **and**
   - separate **Verschwiegenheitsverpflichtung nach § 203 Abs. 4 StGB**, with explicit Strafbarkeitshinweis (the developer becomes himself strafbar nach § 203 if he leaks).
2. **On-prem actually helps a lot.** No Drittlandtransfer (cleanly avoids US-CLOUD-Act / Schrems-II swamp), and Papa remains the sole "Verantwortlicher".
3. **Sub-processors:** every cloud LLM/STT call is a sub-processor. Anthropic/OpenAI Whisper API for clinical text is **not § 203-clean** without enterprise BAA-equivalent contracts and EU residency. **Local Whisper (faster-whisper / whisper.cpp) on practice hardware keeps the chain short.** This is what we're already doing — confirms the architectural choice was not just an aesthetic preference.
4. **TOMs the LfDI Baden-Württemberg will ask about if audited:**
   - disk encryption at rest
   - backup encryption
   - access control with named accounts
   - audit log of admin access
   - documented Löschkonzept
   - written incident-response plan
5. **The family relationship doesn't relax any of this.** KBV's own Hinweise zur Schweigepflicht warn explicitly against informal Familienarrangements.

---

## 6. EBM vs. GOÄ — the rule sources

|  | **EBM** | **GOÄ** |
|---|---|---|
| Full name | Einheitlicher Bewertungsmaßstab | Gebührenordnung für Ärzte |
| Domain | GKV (~90% of patients) | PKV + self-pay + IGeL |
| Publisher | KBV + GKV-Spitzenverband (Bewertungsausschuss, § 87 SGB V) | BMG by Verordnung; content drafted by Bundesärztekammer |
| Cadence | **Quarterly** Q1/Q2/Q3/Q4 | Frozen since 1996 (with Punktwert tweaks). **GOÄneu** draft published by BÄK Jan 2026 (~948 pp); Verordnungsentwurf expected mid-2026 |
| Programmatic access | `ebm.kbv.de` (HTML); structured KBV stamm-data via `update.kbv.de` (XML/CSV/PDF mix, **Hersteller-only access keys**); KBV2Go app | No official API; PDF + GOÄneu envisages a maschinenlesbare Rechnungs-Vorlage |
| Urology-specific | Chapter 26 EBM | Sections L (Chirurgie/Urologie) and M (Labor) |

**Implication:** EBM updating is a structural commitment — take it on or don't. GOÄ today is stable enough to vendor as a static dataset. GOÄneu changes that within 12–18 months.

The "Tipps" Papa's Verrechnungsstelle gives him are GOÄ-optimization heuristics — **explicitly within scope** for the custom system to learn and codify, since GOÄ is not under KOB and the optimization is administrative, not clinical.

---

## 7. Vendor landscape — the "Kartell" claim, verified

### CGM dominance
Top-9-PVS in Allgemeinmedizin (KBV ADT-Statistik Q1/2025, ~13,690 installations):
- **CGM brands** — TURBOMED (2,060), CGM MEDISTAR BLACK PRO (1,942), ALBIS, CGM M1 PRO → **~5,135 installations, ~37%**
- **medatixx brands** — medatixx, x.isynet, x.concept → **~4,485 installations, ~33%**
- **Together: ~65% of the top-9 footprint.** Effective duopoly, CGM the larger half.

### CGM ownership
- **CVC Capital Partners (PE) closed voluntary takeover Q1 2025**, ~22% of free float.
- Founding family Gotthardt + Koop retain 50.1%.
- **Delisted 24.06.2025.** Now PE-controlled, founder-anchored — meaningful for product roadmap inertia.

### Founder politics — correction to Papa's claim
Papa said the CGM CEO is "an AfD-A-Schluch". **The evidence does not support this**:
- Founder/chairman **Frank Gotthardt** donated **~€180,020 to CDU and ~€200,000 to FDP in January 2025** (~€380k total before the Feb 2025 federal election).
- **No documented donations to AfD** in any source reviewed (Correctiv, Apotheke Adhoc, Handelsblatt, t-online).
- The likely confusion source: **Gotthardt finances "Nius"**, the right-wing news portal run by Julian Reichelt, which has rhetorical overlap with AfD positions. But Gotthardt's own party affiliation is **CDU**, not AfD.

**Be precise with Papa about this** — it's a meaningful distinction; conflating them is defamatory and undermines the credibility of the broader (correct) "Kartell-strukturen + politicized media bets" critique.

### Challengers
- **T2med (Praxis Projekt KG, Kiel)** — only system with positive growth Q4/2024 → Q1/2025 (+93 installations); ~4,100 practice teams. Doctor-built (Dr. med. Hans Joachim von der Burchard), modern stack, rising. **Pricing correction:** €1,900 net one-time license + **€115 net/mo** maintenance per practice. Papa's "~500/mo" memory is significantly off.
- **Tomedo (zollsoft)** — ~748 installations Q1/2025 (rank 11). Mac-native, popular with younger Praxen.
- **INDAMED Medical Office** (Papa's current system) — mid-tier, distributed via reseller network — typical of the long tail outside the top-9.

### User satisfaction
Independent surveys (Zi 2024, Virchowbund 2024/2026) consistently rank **CGM products near the bottom; T2med and Tomedo near the top.** The "Kartell" framing is colloquial but the market structure (high switching costs, KOB barrier protecting incumbents, 65% duopoly) supports the sentiment.

---

## 8. The other "PVS" — Privatärztliche Verrechnungsstelle

Yes, "PVS" in Papa's usage = **Privatärztliche Verrechnungsstelle**. Distinct from Praxisverwaltungssystem (also "PVS"). Confusing but standard.

- **PVS-Verband** is a federation: 12 regional/professional member organisations, ~25,000–50,000 physician members, >100 years of history.
- **Almost certainly Papa's provider: PVS Südwest** (Mannheim, covers Baden-Württemberg) — explicit market leader for GOÄ / UV-GOÄ / Hybrid-DRG.
- **Service models:**
  1. **Honorar-Vorstreckung** — PVS advances the fee, doctor remains liable for default.
  2. **Echtes Factoring** — PVS buys the claim, assumes default risk; payment in 24–48h. Some regulated by BaFin.
- **Typical commission:** 3–8% of collected GOÄ-Honorar.
- **Services beyond invoicing:** GOÄ optimization tips, Mahnwesen, court collection, statistical benchmarking against peer practices. **The "Tipps" Papa's PVS gives him are codifiable.**
- **Patient consent:** Schweigepflichtentbindung required before patient data leaves the practice for the PVS — usually obtained via Anmeldebogen.

**Touchpoint with the build:** clean export path (structured invoice file — proprietary format per Verrechnungsstelle, often CSV or thin XML). Administrative integration, not regulated.

---

## 9. The current tools landscape — replace / coexist / ignore matrix

| Tool | Vendor / what | Verdict | Reasoning |
|---|---|---|---|
| **Medical Office** | INDAMED (Esslingen). MariaDB-backed PVS, ~€140–250/mo all-in. Standards-only integration (GDT/LDT/HL7/KIM/KVDT/DICOM). No public REST API. | **Coexist (read-only mirror) v1, replace long-term** | KBV certification is the show-stopper. Read MariaDB directly (Papa has the schema), build dashboard on top, MO stays the certified billing engine. |
| **Infoskop** | synMedico GmbH, Kassel. Digital Anamnese on iPad/web. Outputs PDF/A into the Akte, not structured fields. Pricing not published, comparable products €80–200/mo. | **Replace** | High-value target. PDF-only flow into MO means we can build a better intake form (structured fields, conditional logic, voice input) and just generate the same PDF for archival. No certification entanglement. |
| **"Hermit" (online Terminplaner)** | **Product name doesn't exist.** Likely TerMed (INDAMED's own), Terminico, or samedi. Doctolib dominates the wider market (~70% of online-booked appointments). | **Verify first**, then probably replace if it's TerMed/Terminico; coexist if Doctolib (patient-facing brand value as funnel) | Ask Papa to check the invoice header for the actual product name. |
| **MediVoice** | Mediform GmbH. KI-Telefondame. **€90 net/mo + €0.18/min above 500 included minutes.** German-tuned, C5-zertifiziert, EU-resident. | **Coexist initially, replace later** | Voice AI is a serious build. Mirror their booking events into our calendar layer. Revisit when we have voice infra. **Note Papa's reservation:** he sees value in human warmth at first patient contact (Frau Bischoff > KI-Stimme for "Blut im Stuhl" calls). Worth honoring this design principle. |
| **T2med** | T2med GmbH, Kiel. Doctor-built, KBV-zertifiziert, growing. **€1,900 one-time + €115/mo** (Papa's "~500/mo" was wrong). | **Strategic backup option** | If INDAMED relationship becomes unworkable, T2med is the cleanest migration target. Worth a discovery call independently. |
| **PVS-Abrechnungsstelle (PVS Südwest)** | Privatärztliche Verrechnungsstelle. Mails private invoices, chases payment, GOÄ tips. 3–8% commission. | **Ignore / coexist** | One-way batched export. Don't touch. Mirror invoice state into dashboard for visibility, nothing more. |
| **Kartenleser + SMC-B** | Cherry ST-1506 / Worldline ORGA / ZEMO VML-GK2. gematik-sealed pipeline. | **Ignore (do not touch)** | Read VSDM data downstream from PVS database. Bypassing Konnektor = certification violation + § 291 SGB V exposure. |
| **CGM ecosystem** | Frank Gotthardt + CVC. ~50% combined market share. Delisted Q2 2025. | **Avoid as vendor; useful as competitive reference** | When pitching other practices later: market structure, price hikes, Gotthardt's politicized media bets are credible "why switch" narratives — **but stay factual on Gotthardt: CDU/FDP donor + Nius financier, not AfD.** |

---

## 10. Architectural boundaries — what this changes in the build

### Hard boundaries (do not cross)
1. **Never produce the KVDT quarterly file.** That's the firewall between "tool" and "PVS". Once we ship KVDT we owe KBV-Zulassung, KOB, and quarterly EBM updates forever.
2. **Never speak TI protocols directly** (no own KIM client, no own ePA-FdV integration, no own Konnektor calls) for at least v1. KOB barrier is intentionally high — only 141 systems passed in all of Germany.
3. **File the Zweckbestimmung in writing** — the conservative one-sentence framing in §2 above.
4. **Sign AVV + § 203 Verschwiegenheitsverpflichtung** before touching real Patientendaten. Non-negotiable, even for family.
5. **Local Whisper, not cloud Whisper.** Once audio leaves the LAN we've imported a Schrems-II problem. (Already our architecture — confirms the choice.)

### Sit-on-top-of (the leverage zone)
1. Medical Office stays in place as certified Abrechnungs-PVS. Owns: KVDT, ePA, e-Rezept, KIM, eAU, GDT receipt from devices, formal patient master record.
2. Custom system **reads** from MO (BDT/GDT/proprietary export over MariaDB) and **writes back** documentation drafts that the doctor pastes/imports — never auto-pushes to billing.
3. Real value layers, all outside any certification regime:
   - Ambient transcription + structured intake (local Whisper) — replaces Infoskop
   - GOÄ assistance / private-billing draft preparation (GOÄ is not under KOB)
   - Doctor's personal knowledge base / Befund-templates
   - Patient-facing letter generation
   - Privatabrechnung pre-staging for the Verrechnungsstelle
   - E-Mail triage + draft preparation
   - Rechnungsprüfung automation (Phase 1 in deployment strategy — purest leverage, zero operational coupling)
4. **The 1% SGB V sanction is Medical Office's problem, not ours** — as long as MO stays the system of record for Abrechnung.

### Can be ignored at single-practice freelance scale
1. CE-marking the custom system as a medical device (provided Zweckbestimmung holds).
2. Becoming a KBV-Vertragspartner / signing the Rahmenvereinbarung Praxissoftware.
3. gematik Hersteller-Listung.
4. GOÄneu engineering until the Verordnung is enacted (mid/late 2026 earliest).
5. TI 2.0 / ZETA migration plumbing.

---

## 11. Open questions for the next dad-conversation (Sunday)

1. **Verify the online-Terminplaner product name** (check invoice header — "Hermit" doesn't exist as a product).
2. **Confirm Privatärztliche Verrechnungsstelle is PVS Südwest** (Baden-Württemberg geography makes this overwhelmingly likely).
3. **Ask whether INDAMED's contract has any clause restricting third-party DB access** to the on-prem MariaDB. INDAMED has no published posture; most likely silence = grey-zone-permissible since Papa controls the server.
4. **Walk through one Rechnungsprüfung session together** — this is the Phase-1 leverage point; the algorithmic structure (EBM Chapter 26 + GOÄ Sections L/M + PVS Verrechnungsstelle Tipps) is fully extractable.
5. **Inventory the full subscription stack** (the "Wrap-up" Papa committed to) — especially anything not yet named: backup service, IT-Support-Hotline (~€200/mo currently), DMS, lab-result handlers, Quartalsupdate-Service.

---

## Sources

### Regulatory
- [KBV — Praxisverwaltungssystem](https://www.kbv.de/praxis/digitalisierung/praxisverwaltungssystem)
- [KBV — Rahmenvereinbarung für Praxissoftware](https://www.kbv.de/infothek/ita/rahmenvereinbarung-pvs-anbieter)
- [KBV — Anforderungskatalog KVDT (PDF)](https://update.kbv.de/ita-update/Abrechnung/KBV_ITA_VGEX_Anforderungskatalog_KVDT.pdf)
- [KBV — Abrechnung mit Praxissoftware ohne KOB-Zertifikat (04.12.2025)](https://www.kbv.de/praxis/tools-und-services/praxisnachrichten/2025/12-04/abrechnung-mit-praxissoftware-ohne-kob-zertifikat-kbv-verhindert-unfaire-haerten)
- [KBV — EBM-Online (Q1/2026)](https://ebm.kbv.de/)
- [KBV — Hinweise zur Schweigepflicht und Datenschutz (PDF)](https://www.kbv.de/documents/infothek/rechtsquellen/weitere-vertraege/praxen/datenschutz-schweigepflicht/hinweise-empfehlungen-schweigepflicht-datenschutz-datenverarbeitung.pdf)
- [gematik — Konformitätsbewertung (KOB)](https://www.ina.gematik.de/kig/konformitaetsbewertung)
- [gematik — Newsroom: 141 Systeme bestanden KOB](https://www.gematik.de/newsroom/news-detail/kob-sorgt-mit-standards-fuer-transparenz-141-systeme-bereits-erfolgreich-bewertet)
- [gematik — TI 2.0](https://www.gematik.de/telematikinfrastruktur/ti-2-0)
- [gematik — RSA → ECC Migration](https://www.gematik.de/telematikinfrastruktur/rsa2ecc-migration)
- [§ 341 SGB V (gesetze-im-internet.de)](https://www.gesetze-im-internet.de/sgb_5/__341.html)
- [Bundesamt für Soziale Sicherung — ePA nach § 343 SGB V](https://www.bundesamtsozialesicherung.de/de/themen/digitalausschuss/elektronische-gesundheitsakten-und-telematikinfrastruktur/elektronische-patientenakte-epa-nach-343-sgb-v/)
- [KV Baden-Württemberg — Pauschalen, Auszahlung, Sanktionen](https://www.kvbawue.de/praxis/unternehmen-praxis/it-online-dienste/telematikinfrastruktur-ti-e-health/pauschalen-auszahlung-sanktionen)
- [European Commission — MDCG 2019-11 Rev.1 (June 2025)](https://health.ec.europa.eu/latest-updates/update-mdcg-2019-11-rev1-qualification-and-classification-software-regulation-eu-2017745-and-2025-06-17_en)
- [Bundesärztekammer — GOÄ-Novellierung](https://www.bundesaerztekammer.de/themen/aerzte/honorar/goae-novellierung)
- [Deutsches Ärzteblatt — § 203 StGB Verschwiegenheitspflicht externe Dienstleister](https://www.aerzteblatt.de/archiv/204240/Verschwiegenheitspflicht-Gesetzgeber-regelt-Einbindung-externer-Dienstleister)
- [activeMind AG — Auftragsverarbeitung für Berufsgeheimnisträger](https://www.activemind.de/magazin/dsgvo-berufsgeheimnistraeger-auftragsverarbeitung/)
- [Kleiboldt — § 203 StGB und Cloud-KI in der Arztpraxis](https://kleiboldt.de/blog/203-stgb-cloud-ki/)

### Vendor / market
- [INDAMED Medical Office Schnittstellen](https://www.indamed.de/module/medical-office-schnittstellen/)
- [INDAMED Preise](https://www.indamed.de/preise/)
- [INDAMED Forum: synMedico/Infoskop integration](https://forum.indamed.de/index.php?page=Thread&postID=47461)
- [synMedico (Infoskop)](https://synmedico.de/)
- [Mediform MediVoice](https://mediform.io/medivoice) and [pricing](https://mediform.io/pricing)
- [T2med homepage & pricing](https://t2med.de/) and [KBV market growth statistic](https://t2med.de/kbv-statistik/)
- [PVS-Verband Mitglieder](https://www.pvs-verband.de/verband/mitglieder/)
- [PVS Südwest](https://www.pvs-suedwest.de/)
- [gematik Zulassungsübersicht (Kartenterminals)](https://fachportal.gematik.de/zulassungs-bestaetigungsuebersichten)
- [Cherry ST-1506](https://www.cherry.de/en-us/product/ehealth-terminal-st-1506)
- [Doctolib market criticism (vzbv, April 2025)](https://www.zdfheute.de/ratgeber/patientenportal-doctolib-jameda-arzttermin-online-buchen-kritik-100.html)
- [CGM — CVC takeover final results (Feb 2025)](https://www.cgm.com/corp_en/magazine/articles/press-releases/2025/final-results-of-voluntary-public-takeover-offer-cvc-has-secured-21-85-of-total-share-capital-and-voting-rights-of-compugroup-medical.html)
- [MedEcon Ruhr — CompuGroup + CVC Delisting](https://medecon.ruhr/2025/05/compugroup-medical-und-cvc-planen-delisting/)
- [Correctiv: Gotthardt / Nius / Spahn (Jul 2025)](https://correctiv.org/aktuelles/lobbyismus/2025/07/25/medien-und-medizinsoftware-der-profiteur-von-spahns-politik-nius-gotthardt/)
- [Apotheke Adhoc — Gotthardt/Theiss CDU+FDP donations](https://www.apotheke-adhoc.de/nachrichten/detail/politik/hohe-parteispenden-von-theiss-und-cgm-gruender/)
- [KVBW ITP April 2025 — Top-9 PVS-Installationszahlen](https://www.kvbawue.de/api-file-fetcher?fid=4958)
- [Virchowbund — Praxissoftware-Vergleich 2026](https://www.virchowbund.de/praxisaerzte-blog/praxissoftware-vergleich-wer-ist-der-beste-anbieter-2026)
- [Wikipedia — Privatärztliche Verrechnungsstelle](https://de.wikipedia.org/wiki/Privat%C3%A4rztliche_Verrechnungsstelle)
