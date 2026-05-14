---
name: MariaDB-Beobachtungs-Strategie für Praxis-Workflow-Inferenz
description: Warum DB-Layer (binlog + history tables) das richtige Observation-Tool ist — nicht UI-click-capture / screen-recording — und was MO-MariaDB by default liefert
type: project
originSessionId: f5bdb875-89ff-475c-b6fa-6c94427cf63b
---
# DB-Layer als Observation-Pipeline (statt UI-Click-Capture)

**Kontext (2026-04-26 Sunday session)**: Wir brauchen eine Pipeline die Praxis-Workflows aus laufenden MO-Sessions extrahiert (für Process-Inferenz + automatische QM-Doku-Generierung). Die naheliegende Antwort wäre Windows-UI-Automation oder Screen-Recording — aber DB-Layer ist überlegen.

## Warum DB-Layer statt Click-Capture

- **Signal sitzt im DB-Write, nicht im Click.** Jede meaningful Aktion (Befund saved, Brief sent, Ziffer added, ePA upload, KIM-Versand) terminiert in einem DB-Write. Clicks sind ein noisy proxy.
- **UI-Automation (UIA) auf Windows-third-party-Apps ist brittle**, bricht bei jedem MO-Update, surfaces opaque control IDs.
- **Screen-Recording + OCR**: noch schlechteres Signal/Rausch.
- **§203/DSGVO-Frame**: DB-binlog-tail sieht nur Daten die die Praxis ohnehin hat. UIA/Screen-Recording wirft schwierigere Schweigepflichts-Fragen auf.

## Was MariaDB by default liefert

**Binlog: OFF by default.** Muss explizit aktiviert werden (`log_bin` in `my.ini` + Restart). General-Log: OFF by default. Auf einer typischen MO-Installation also: keine.

**Aber**: für *what people did* gibt es zwei komplementäre Quellen:

1. **History/Audit-Tabellen (retroaktiv, schon da)**. §630f BGB verlangt revisionssichere Speicherung — jede zertifizierte PVS *muss* das implementieren. Vermutlich als parallele `_history`-Tabellen oder zentrale `aenderung`-Tabelle. **Stretch potentially 5+ years backward.** Liefert das Korpus für Process-Inferenz.
2. **Binlog (forward, sobald aktiviert)**. ROW-Format → vollständige before/after-row-images, Transaction-Grouping (= "was zu einer logischen Aktion gehört"), per-Connection-Attribution. Eine Config-Zeile + Restart.

**They're complementary**: History-Tables = Process-Catalogue-Inferenz aus Vergangenheit; binlog = high-fidelity-Confirmation forward + neue Variants.

## Was DB-Layer NICHT sieht
- Pure reads (Akte nur angeschaut, nichts geändert) — general_log würde es catchen, aber 5-10× Storage-Cost
- UI-only state (welcher Tab, welches Layout)
- Print/Fax/KIM-Versand *falls* MO keine "versand done"-Row schreibt — fast sicher tut sie es (audit trail / Abrechnung)

## Sunday's extract-mo-schema.sh — was es jetzt unbedingt erfassen muss

Nicht nur Patientendaten-Tabellen. **Auch:**
- History/Audit-Tabellen-Konvention (welche Form? `_history` parallel? zentrale `aenderung`-Tabelle?)
- Schablonen-Config-Tabellen (Befund-Typen, Ziffer-Vorschlag-Logik) — dort lebt die Praxis-spezifische Abrechnungs-IP
- Timestamp-Spalten-Konvention auf jeder Haupttabelle (`erstellt_am`, `geändert_am`, etc.)
- KIM-Eingang-Tabellen (KIM-Inhalte werden lokal im PVS gespeichert; KIM-Fachdienst nur transient)

## How to apply

- Wenn David nach Observation-Pipeline-Optionen fragt: defaultmäßig DB-Layer empfehlen, nicht UI/Screen.
- Voice-Commentary-Layer ist optional opt-in für Calibration-Sessions (David sitzt mit Mic neben Papa für 90 min) — nicht Daily-Asks an Staff.
- Sobald Sunday-Schema-Dump da ist: Architektur des Beobachtungs-Layers klären (binlog-tail + history-mining + Schablonen-Config-Map).
