---
name: Papa's Praxis — Workflow-Corpus + Stream A Grounding (2026-04-26)
description: Was wir aus dem Sunday Briefe-Workflow walkthrough gelernt haben + neue Process-Inventory-Implikationen + offene Papa-Fragen
type: project
originSessionId: f5bdb875-89ff-475c-b6fa-6c94427cf63b
---
# Papa's Praxis — Workflow-Corpus aus 2026-04-26 Briefe-Walkthrough

Stand: 2026-04-26 nach Stream A Synthese. Vollständige Details in:
- `PraxisDoktor/docs/transcript_2026-04-26.md` — der raw extract
- `PraxisDoktor/docs/processes_observed.md` — Workflows × kanonische Quellen
- `PraxisDoktor/docs/regulatory_landscape.md` §§ 12–17 — die neuen kanonischen Findings

## Kern-Erkenntnisse (cross-conversation relevant)

### Architektur

- **MO ist das Herz** — viel mehr Workflows leben dort als initial angenommen. To-Do-Liste, Brief-Liste, KIM-Eingang, Schablonen, Schein-Logik, ePA-Upload — alles in MO. → Wer MO-DB-Layer beobachten kann, beobachtet 95 % der Praxis-Information-Flows.
- **Schablonen-Architektur unter allem**: jeder typed Field (Befund-Schablone, Brief-Template, Ziffer-Vorschlag, To-Do-Entry) ist practice-konfigurierbares Mapping zwischen Akten-Inhalt und structured Schemas. Schemas existieren für Inter-PVS-Portabilität (xDT heute, MIO/FHIR perspektivisch). **Practice-konfigurierte Ziffer-Vorschlag-Logik in MO Config-Tables = Goldminen-Korpus** — wenn wir diese Tabellen mappen, sehen wir die praktizierte Abrechnungs-IP der Praxis.
- **Papa's "alles könnte eine Datenbank sein, gefiltert per Rolle"** validiert exakt die `process_ontology.md`-Spine (transition-stream + role-scoped-views). Kein Re-Design notwendig.

### Korrekturen / Updates für Process Inventory

| Existing | Action |
|---|---|
| `email_triage` placeholder | **Retire.** Replace mit `aufgaben_persoenlich` + `aufgaben_team` (genauere Abbildung der observierten MO-Strukturen). |
| `materialverwaltung` placeholder | Untouched — defer. |
| `krankenkassen_abrechnung` decline | Confirmed boundary. Stays. |
| `rechnungspruefung` 11 rules | **Erweitert in `rules_ebm.py`**: GOP 26310 typo-fix (war "Versichertenkonsultation" — ist Urethrozystoskopie Mann), 8 neue GOPs (26311, 33042, 33043, 01601, 86900, 86901, 01647, 01648, 01431), 2 neue Rules (`kim_quartal_cap`, `abolished_gops` für 01660-Wegfall). |
| Add `briefe_arzt` | Outgoing Briefe-Workflow als eigener Process. |
| Add `aufgaben_persoenlich`, `aufgaben_team` | Die observierten To-Do-Listen-Strukturen. |
| Add `krebsregister_meldung` | Wenn Papa nicht d-uo-Mitglied. |
| Add `hybrid_drg_abrechnung` | dashboard_only initial; phase=decline für Submit. |

### Sunday-Plan-Updates (extract-mo-schema.sh)

Muss zusätzlich erfassen:
- History/Audit-Tabellen (für §630f-Compliance, vermutlich `_history`-Pattern oder zentrale `aenderung`-Tabelle)
- Schablonen-Config-Tabellen (Befund-Typen, Ziffer-Vorschlag-Mapping)
- KIM-Eingang-Tabellen
- Timestamp-Konventionen (`erstellt_am`, `geändert_am`)

## Offene Fragen für Papa (priorisiert)

**Critical (vor signifikantem Build)**:
1. **Bist du d-uo-Mitglied** (Berufsverband Deutscher Uro-Onkologen)? Falls ja, nutzt du d-uo's Tumordokumentations-System? → Determines whether `krebsregister_meldung` als Target sinnvoll.
2. **Welche Hybrid-DRG-OPS-Codes machst du tatsächlich**? (TUR-P/TUR-B-Status im 2026-Katalog uncertain.)
3. **BvDU/SpiFa-Mitglied?** Determines Sanakey-Konditionen + Roll-out auf Schwesterpraxen.
4. **Was kostet dich Sanakey/Quartal in Euro?** Konkrete Größenordnung für Eigene-§301-Pipeline-vs-RPA-Entscheidung.
5. **Speichert MO die rohe S/MIME-eArztbrief-Originalnachricht** revisionssicher, oder nur den dekodierten Inhalt? — Wird sich im Sunday-Schema-Dump zeigen.

**Non-blocking aber wichtig**:
6. Hast du das aktuelle QM-Handbuch greifbar (Baseline-Vergleich)?
7. Welche Schablonen sind Hersteller-Defaults vs. selbst angelegt? (Vermutlich erst nach Schema-Dump beantwortbar.)

## Wichtige Korrekturen zu vorherigen Annahmen

- **Sanakey ist 100% SpiFa-Tochter, NICHT BvDU**. BvDU's eigene Tochter ist VgURO. SpiFa = Spitzenverband Fachärztinnen und Fachärzte Deutschlands.
- **GOP 01660 (Förderzuschlag eArztbrief) ist seit 30.06.2023 weggefallen**. Alte PVS-Templates emittieren sie noch → KV-Streichung. Jetzt im `abolished_gops`-Rule.
- **GOP 01647 (ePA-Folge-Befüllung) ist 1× pro Behandlungsfall, NICHT pro Dokument**. Häufige Fehlannahme.
- **KIM-Strukturpauschalen 86900+86901 sind gemeinsam gedeckelt 23,40 €/Quartal/Arzt**. Jetzt im `kim_quartal_cap`-Rule.
- **eArztbrief ≠ PDF in KIM**: Strukturierte CDA Release 2 (Arztbrief Plus / VHitG) im IHE-XDM-Container. PDF darf innerhalb der CDA-Anlage transportiert werden.
- **§115f Hybrid-DRG-Datenformat ist §301 SGB V**, NICHT KVDT/CON-Datei. CON-Datei-Route existiert nicht.

## Strategic hooks neu verfügbar

- **QM-Handbuch-Hook**: §135a SGB V + G-BA QM-RL (Beschluss 18.01.2024, in Kraft 20.04.2024). Process-Doku ist functional Pflicht über §3 Nr.5 (Informationssicherheit) + §3 Nr.3 (Prozessorientierung) + §4 Schnittstellenmanagement. **Existing QM-Software ist ausschließlich statische Doku-Verwaltung — keiner generiert QM-Doku als Side-Effect eines aktiven Tools. Das ist unsere Differenzierung.**
- **§301-Pipeline mit InEK-Grouper** als Auto-Submit-Pfad für Hybrid-DRG: meaningful unregulated surface, KEIN KBV/gematik-Cert nötig. Nur Grouper muss zertifiziert sein.
