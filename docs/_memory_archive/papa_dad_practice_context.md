---
name: Papa's Practice — Tool Stack & Strategic Context
description: What Papa's urology practice actually runs, what to research before Sunday, what Papa committed to provide
type: project
originSessionId: f5bdb875-89ff-475c-b6fa-6c94427cf63b
---
# Papa's Karlsruhe Urology Practice — Operational Context

Captured from the demo conversation 2026-04-23.

## Current paid software stack (what to displace or coexist with)

- **Medical Office (INDAMED)** — core PVS, MariaDB-backed (migrated from Firebird). ~€140–250/mo all-in. Reseller model — Papa's reseller is between him and INDAMED; calls to INDAMED engineers themselves are nearly impossible ("if at all, three-way calls, no callback").
  - **Schema status (2026-04-24 detective work):** the only MO-derived schema *in the repo* is the 14 patient-master fields (`nachname, vorname, geburtsdatum, geschlecht, titel, anrede, strasse, hausnr, plz, ort, telefon_privat, telefon_mobil, email, muttersprache`) inherited from v1 PatientIntake. Fall / Befund / AbrechnungPosition tables are **domain-shaped only** — Papa's "I have the schema" was likely a different artifact than what shipped. **Sunday plan:** run `tooling/extract-mo-schema.sh` on the practice server → SHOW CREATE TABLE for every table → JSON to USB. Then map columns into `server/app/medical_office/mariadb.py`; one edit switches Patientenakte + Rechnungsprüfung from mock to live.
- **Infoskop (synMedico)** — patient anamnesis tablet/web app. Outputs PDF/A into the Akte. **Highest-leverage replacement target** (no certification entanglement).
- **"Hermit" online Terminplaner** — product name doesn't exist as stated; verify on next visit (likely TerMed/Terminico/samedi).
- **MediVoice (Mediform)** — KI-Telefondame, €90/mo + €0.18/min. Papa has reservations about KI at first patient contact ("Frau Bischoff > KI-Stimme for 'Blut im Stuhl' calls"). Honor this design principle.
- **PVS-Abrechnungsstelle** — almost certainly **PVS Südwest** (Mannheim, covers BW). Mails private invoices, chases payment, gives GOÄ-Optimierung "Tipps". Papa pays them ~3–8% of GOÄ-Honorar.
- **IT-Support-Hotline** — ~€200/mo for the reseller's hotline + server monitoring + update installation. **Cancellable once we automate the update path.**
- **Kartenleser + SMC-B** — sealed gematik pipeline, cannot touch.

## What Papa committed to provide on Sunday

1. Walk-through of one **Rechnungsprüfung** session — the Phase-1 leverage point.
2. Full **subscription stack inventory** — beyond the named tools: backup service, DMS, lab handlers, Quartalsupdate-Service, anything monthly.
3. Database access to Medical Office's MariaDB (Papa controls the server).

## Strategic frame Papa surfaced unprompted

- **"Du bist ein Freelancer, du kannst die kategorisch unterbieten"** — Papa explicitly noted the cost-structure asymmetry vs. the bureaucratic incumbents. He gets the leverage point I've been articulating.
- **"Was machst du mit der Zeit?"** — Papa's frame for evaluating automation: not "can it be automated" but "what does the human do with the freed time, and is that direction good?" His MediVoice reservation comes from this. Build with this frame, not pure efficiency-maximization.
- **"Wenn das wirklich läuft" → MD VIP US connection** — Papa mentioned his Owen Mead-Robins / OMEA contact has a connection to MD VIP (1,400 high-end physician network in the US). The Karlsruhe pilot is potentially product-shaped, not just service-shaped. Don't treat it as a one-off.
- **Barbara visit** — Papa already arranged that I look at Barbara's (his sister, also a doctor) Datenstrukturen toward end of stay. **Second reference practice already lined up.**

## Architectural validation from the conversation

Papa independently arrived at the same **rein/raus + intern Kommunikation** decomposition that's already the spine of the docs:
> "Du hast interne Kommunikation, interne Prozesse und dann fließt Kommunikation nach außen [...] Kommunikation fließt rein, Kommunikation fließt raus und Kommunikation ist intern. Und dann muss man es halt unterteilen in diese Prozesse. Jeder hat verschiedene Zugangsrechte auf diese Prozesse."

This is the existing process_ontology.md spine. **Don't re-explain it — use it as the agreed substrate.**

## Things Papa was wrong about (correct gently when relevant)

- **T2med pricing** — he remembered ~€500/mo; actual is €1,900 one-time + €115/mo. Real but smaller delta to displace.
- **CGM-Chef "AfD-A-Schluch"** — Frank Gotthardt is a CDU/FDP donor (~€380k Jan 2025) and Nius financier, not AfD. Real critique exists; precision matters.
- **"Hermit"** — no such product. Check the invoice.
