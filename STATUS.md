---
client: PraxisDoktor
status: pilot_concluded
phase: family_help_mode
last_updated: 2026-05-13
last_activity: 2026-05-12 Team-Demo
operator: David Rug
contact_owner: Dr. Michael Rug (Papa) + Dr. Nicola Bruckschen
practice: urologische Praxis uro-karlsruhe
---

# PraxisDoktor — Status

## Die fundamentale Erkenntnis aus dieser Phase

PraxisDoktor wurde ursprünglich als skalierbares Pilot-Modell für die
medizinische Praxis-Automatisierung konzipiert. Während der Arbeit
(April–Mai 2026) ist klar geworden: **ein professioneller, skalierbarer
Rahmen für medizinische Praxis-Automatisierung ist mit der bestehenden
Vendor-Landschaft kommerziell unrealistisch** — zumindest auf einem
Solo-Freelance-Skalen-Niveau und ohne tiefe Vendor-Partnerschaften.

Die zentrale Blockade ist nicht technisch und nicht regulatorisch im
engeren Sinn — sie ist **vertraglich-kommerziell**: die direkte
Medical-Office-Datenbank-Schnittstelle ist durch das INDAMED-
Vendor-Modell verschlossen, die offiziellen Integrations-Pfade
(GDT/BDT/HL7/COM) sind kostenpflichtig und erfordern eine
INDAMED-Partnerschaft, die ein Solo-Operator nicht schnell genug
aufbauen kann, um damit eine Beratungspraxis zu finanzieren.

Konsequenz: **PraxisDoktor wechselt vom "Skalierungs-Pilot" in den
"persönlichen Helfer für Papa"-Modus.** Die Arbeit bleibt wertvoll, aber
nicht mehr als kommerzielles Vehikel.

## Was während dieser Phase entstanden ist

### Werkzeuge (live demonstrierbar)

- **Anamnesebögen-Werkzeug** mit Zwei-Modus-UI:
  - Patientenhinweise-Import: umgeht den MO/Infoskop-Kopier-Bug per
    Screenshot-OCR; generiert klinische Anamnese-Prosa in Papas
    kompressivem Telegraph-Stil. Validiert gegen echten Infoskop-Output
    (22 Felder, ~100% Genauigkeit).
  - Praxis-eigener Bogen: konfigurierbarer Anamnesebogen, der die
    Infoskop-Lücken schließt (Anliegen heute, Miktionsbeschwerden-Modul,
    klinisches Fachvokabular).
- **Verbesserungs-Wünsche-Werkzeug**: Linear-Style-Backlog mit Upvotes,
  Status-Wechsel für Praxisinhaber. Co-Creation-Kanal.
- **Patientenintake-Pipeline**: Audio → Whisper (Transkription) →
  gemma4 (Extraktion) → strukturierte Felder mit Validierungs-UI.
  Zwei Extraktionsprofile (Stammdaten, Klinisch).
- **Demo-Reset-Werkzeug** (für Praxisinhaber/-manager): wischt
  Testeinträge in Anamnesebögen, Verbesserungs-Wünsche,
  Patientenaufnahme.

### Infrastruktur und Architektur

- FastAPI-Backend + SvelteKit-Frontend auf lokalem Praxis-Server-Profil
  (kein Cloud-Hosting für Patientendaten)
- Cloudflare RDP-Tunnel für sichere Fern-Administration validiert
  (`new-client-rdp.sh` automatisiert den Cloudflare-seitigen Setup)
- Cloudflare Pages für die öffentliche Praxis-Website
- Rollen-/Prozess-Ontologie als wiederverwendbares Pattern
  (`docs/process_ontology.md`)
- Daten-Extraktions-Compliance-Log (`docs/data_extraction_log.md`) —
  dokumentiert lückenlos jede Extraktion und ihre DSGVO/§203-Begründung

### Datenarbeit (anonymisiert, im Compliance-Log dokumentiert)

- Vollständiger MO-Schema-Dump (153 Tabellen) — verstanden, dokumentiert
- 7 Jahre `dbsprot`-Audit-Log mit konsistenter Salt-Hashing extrahiert
- Tier-1-Erweiterungen (Nutzer-Rollen, externe Ärzte mit Fachgruppen)
- Erkenntnis-Korpus zu Praxis-Workflows, Briefe-Workflow, KIM-Routing,
  Hybrid-DRG, ePA, QM-Handbuch-Anschlussfähigkeit
- Live-Test der Klinisch-Extraktionspipeline auf einem Demo-Audio
  (`PatientenGesprächTest.opus`) — funktioniert end-to-end

### Strategische Outputs

- `docs/regulatory_landscape.md` — Karte der deutschen medizinischen
  Regulierungslandschaft (KBV/gematik/MDR/§203, EBM/GOÄ,
  Hybrid-DRG/Sanakey, ePA-Sanktionsregime, QM-Richtlinie)
- `docs/processes_observed.md` — 10 Praxis-Workflows mit kanonischen
  regulatorischen Anker pro Workflow
- `docs/mo_schema_inventory.md` — Datenmodell-Übersicht für künftige
  Arbeit
- `docs/it_briefing_template.md` — Vorlage für die Kommunikation mit
  IT-Dienstleistern bei Bestandspraxen

## Strategische Neupositionierung

### Was bleibt aktiv

**Persönliche Hilfe für Papa (Familien-Kontext, kein Vertrag)**:

- **Rechnungsprüfungs-Werkzeug** als nächstes Haupt-Tool — das ist das
  Werkzeug, mit dem die größte Zeitersparnis für Papa erzielbar ist.
  Plausibilitätsprüfung gegen die kuratierten EBM/GOÄ-Regeln, die wir
  während der Phase 1 zusammengestellt haben (`docs/billing_rules.md`,
  13 sourced rules). Bauen, wenn ich die Bandbreite habe — primär als
  Geschenk an Papa.
- **Anamnesebögen-Werkzeug** weiter pflegen, wenn das Team Wünsche
  über den Verbesserungs-Wünsche-Kanal äußert. Niedriger Aufwand,
  hoher Wert je gefixtem Pain-Point.

### Was explizit nicht weiter verfolgt wird

- **Direkter MO-Datenbankzugriff** für die uro-karlsruhe-Praxis: kein
  Auftragsverarbeitungs-Vertrag mit Papa. Aktueller Stand (Mai 2026):
  bleibt beim "neben-MO"-Pattern. Diese Entscheidung kann später
  revidiert werden, wenn sich der Kontext ändert.
- **Skalierung auf andere medizinische Praxen** mit ähnlichem
  PVS-Lock-In. Barbara (Praxiskochendoerfer) bleibt warmer
  Discovery-Kontakt, aber kein aktives Bauen.
- **PVS-Übergreifende Plattform-Strategie**. Bedingt eine
  Geschäftsentwicklung mit INDAMED/CGM, die diesem Pilot-Rahmen
  überdimensioniert ist.

### Wo die Energie hingeht

Auf andere Klienten ohne PVS-Lock-In:

- **OMundoSomosNos** als zahlender Hauptklient (siehe
  `../OMundoSomosNos/STATUS.md` und `../STATUS.md`).
- **Preventis** als sauberer Tier-C-Fall (standalone, kein PVS-Touch,
  siehe `../Preventis/STATUS.md`).
- **Auxell-Coaching-Dashboard** wenn die Zeit reif ist (nach OMSN-
  Milestone-1).

## Was im Repo als Folge-Aufgaben sichtbar bleibt

### `tooling/clients/uro-karlsruhe/` (lokal, gitignored)

- Cloudflare-Tunnel-Token und -Konfigurationen
- DB-Extraktions-Output (`mo_extract_v2_2026-04-30/`, etwa 1.5 GB,
  konsistent gehashed, anonymisiert)
- MO-Schema-Snapshots
- Praxis-Server-Credentials (in Keychain primär, in
  `practice-server.env` operativ)

### `_raw_research/` (lokal, gitignored)

- Infoskop-PDF-Beispiel (`sample_infoskop.pdf`)
- Patientenhinweise-Window-Screenshot
- Papa-Geschenk-2026 Interview-Transkripte und Screenshots
- Infoskop-Anamnese-Screenshots

### `docs/` (committed, Wissens-Substrat)

Die Doku unter `docs/` bleibt wertvoll als Wissens-Korpus:

- `regulatory_landscape.md` — übertragbar auf andere medizinische
  Klienten, falls je nötig
- `processes_observed.md` + `process_ontology.md` — das Pattern für
  Klienten-Prozess-Mapping, übertragbar auf nicht-medizinische
  Klienten
- `data_extraction_log.md` — Schablone für DSGVO-konforme
  Daten-Extraktion bei anderen Klienten

Die Datei `_HANDOFF.md` ist veraltet (vor-Phase-1-Stand); kann in einer
Aufräum-Session entfernt werden.

## Nächste konkrete Schritte (in absteigender Priorität)

1. **Demo-Feedback verarbeiten**: Verbesserungs-Wünsche, die im Team
   nach der 2026-05-12-Demo eintrudeln, sammeln. Wenn Papa welche
   eintragen lässt: umsetzen.
2. **Rechnungsprüfungs-Werkzeug bauen**, wenn die Bandbreite zwischen
   OMSN-Arbeit reicht. Architektur ist bereits skizziert
   (`docs/billing_rules.md`, `server/app/billing_rules/`).
3. **Patientenintake-Audio-Pipeline** mit Papa zusammen iterieren —
   er sammelt private Aufnahme-Beispiele, dann kalibrieren wir die
   Extraktion gegen seinen echten Stil.
4. **Repo-Aufräumen** in einer ruhigen Session: veraltete Dokumente
   entfernen (`_HANDOFF.md`, `docs/skeleton_plan.md` evtl., `clients/`-Ordner
   ggf. ganz), redundante Dateien zwischen `docs/` und Memory
   konsolidieren.

## Verbindung zum übergeordneten Liminal-Consulting-Kontext

PraxisDoktor war der erste und tiefste Pilot. Was hier entstanden ist —
die Prozess-Ontologie, das Rollen-Konzept, das Werkzeug-mit-Chat-
Pattern, der Cloudflare-Sovereign-Track, das Daten-Extraktions-
Compliance-Framework — ist in `CRYSTALLIZATION.md` als universelle
Vorlage destilliert worden. Anders gesagt: **PraxisDoktor hat seinen
Hauptzweck erfüllt, indem es die wiederverwendbare Architektur
hervorgebracht hat**, die jetzt auf andere Klienten angewandt wird.

Das Werkzeug für Papa zu sein, ist gleichzeitig wertvoll und beendet
die "Skalierungs-Geschichte". Das ist OK so.
