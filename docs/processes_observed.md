# Processes Observed (transcript 2026-04-26 × canonical sources)

The bridge document. Every observed workflow from [`transcript_2026-04-26.md`](./transcript_2026-04-26.md) mapped to its canonical regulatory + technical anchors. This is the layer that turns "Papa told me" into "we know, with citations, what this is."

Companion to [`process_ontology.md`](./process_ontology.md) (the grammar) and [`roles_and_processes.md`](./roles_and_processes.md) (the inventory). Where this doc identifies a new process, the inventory should follow.

---

## P1 · Briefe-Workflow (outgoing Arztbriefe via KIM)

**Observed:** §1 of transcript. Papa works through his Brief-Liste, generates Arztbriefe from Akten-Inhalt via MO templates, attaches Befunde, sends via KIM to Hausarzt + optional Kopie an Patient, uploads to ePA.

**Canonical anchors:**

| Aspect | Grounded fact | Source |
|---|---|---|
| KIM transport | S/MIME-verschlüsselte E-Mail über SMTP/POP3 durch TI; KIM-Clientmodul + TI-Konnektor (PTV2+); KAS für große Anhänge | [gematik KIM](https://www.gematik.de/anwendungen/kim) |
| Adressverzeichnis | **VZD** (Verzeichnisdienst der TI), LDAP + REST, gematik-betrieben | [gematik VZD](https://fachportal.gematik.de/anwendungen/kommunikation-im-medizinwesen) |
| eArztbrief format | **Nicht** PDF-Anhang. **CDA Release 2 (Arztbrief Plus / VHitG)** im **IHE XDM-Container** mit `KBV_CS_AW_Anlagetyp`-Metadaten. PDF darf *innerhalb* der CDA-Anlage transportiert werden. | [KBV-RL eArztbrief 17.05.2024](https://www.kbv.de/documents/infothek/rechtsquellen/weitere-vertraege/praxen/telemedizin/rl-earztbrief.pdf), [HL7 DE Arztbrief Plus](https://wiki.hl7.de/index.php?title=IG:Arztbrief_Plus) |
| Pflicht-eHBA-Signatur | Komfortsignatur erlaubt bis 250 Sig./Tag mit einer PIN-Eingabe — sonst pro Brief PIN | gematik HBA-Spec |
| Routing zur richtigen Praxis-Person | (a) KIM-Zieladresse, (b) CDA-Header-Empfänger (BSNR + LANR), (c) implizit über Patienten-Behandelarzt-Mapping. **Mis-Routing bei reinem BSNR-Header ist häufig** — der Befund landete bei Papa statt Nikola, vermutlich weil Sender nur BSNR ohne LANR im CDA hatte. Realer Pain-Point, nicht Edge-Case. | INDAMED-Forum Threads, [DKTIG VZD](https://dktig.de/verzeichnisdienst/) |
| Abrechnung der Brief-Erstellung | **GOP 01601** "Individueller Arztbrief" (~60 P / **7,72 €**). Nicht neben Versicherten-/Grund-/Konsiliarpauschale — Ausnahme: Konsiliarpauschale 01436 erlaubt. | [reimbursement.info 01601](https://app.reimbursement.info/gops/01601) |
| Abrechnung KIM-Versand | **GOP 86900 / 86901** (Versand 0,28 € / Empfang 0,27 €), zusammen **gedeckelt 23,40 € / Quartal / Arzt** | [KV Hessen eArztbrief abrechnen](https://www.kvhessen.de/abrechnung-ebm/earztbrief-porto-und-faxe-abrechnen) |
| **GOP 01660 (Förderzuschlag)** | **WEGGEFALLEN seit 30.06.2023.** Häufiger Fehler in alten PVS-Templates → Streichung durch KV. | [IWW: 01660 weggefallen](https://www.iww.de/aaa/kassenabrechnung/elektronischer-arztbrief-weggefallen-mit-dem-30062023-ebm-nr-01660-fuer-earztbriefe-f155239) |
| Papa's "01601 + 8690" | "8690" ist mit hoher Wahrscheinlichkeit **86900** (Versand). Beim Implementieren beide GOPs (86900/86901) mappen. | Triangulation aus IWW + KV Hessen |
| Fax-Versand statt KIM | **GOP 40111** (0,05 €) statt 86900 | KV Hessen |
| Postversand statt KIM | **GOP 40110** (0,86 € — KV-regional schwankend) statt 86900 | KV Hessen |
| §630f-Aufbewahrung | **10 Jahre** Aufbewahrungsfrist; Briefe als Teil der Patientenakte; revisionssichere Speicherung — append-only, nie überschreiben. Rohe S/MIME-Originalnachricht ist *kryptographisches* Beweismittel und sollte separat persistiert werden. | [§630f BGB](https://www.gesetze-im-internet.de/bgb/__630f.html), [PVS-Reiss BGH-Urteil](https://www.pvs-reiss.de/magazin/rechtssichere-behandlungsdokumentation-im-lichte-des-bgh-urteils-vom-27-4-2021-haftungsfalle-praxissoftware/) |

**Process spec implication:** Add new process `briefe_arzt` to the inventory (currently missing). Surface = `tool`, phase = `co_pilot` once we wire it. Inputs include `text` (annotation) + `db_write` (auto-import from KIM-Eingang). Outputs include `notification` (z.K. an Empfänger-MFA) + `db_write` (Brief-Eintrag in MO + ePA-Upload).

**Co-pilot-target backlog (from §11 of transcript):**
- Auto-Vorschlag Versandweg E-Mail wenn Patient eine eigene E-Mail-Adresse hinterlegt hat
- Auto-Vorschlag "letzter Brief war am … — schreibe ab dann"
- Auto-Vorschlag Sonografie-Ziffer-Bündel aus Befund-Body (siehe P4)

---

## P2 · To-Do-Liste (personal coordination queue)

**Observed:** §2 of transcript. Papa's central work-coordination surface. Per-Mitarbeiter-konfigurierbare Listen, MFAs teilen eine, Patient-bound by default.

**Canonical anchors:** None. **This is purely MO-internal product design** — there is no regulatory layer that defines or constrains To-Do-Listen. That makes this surface entirely available for our own re-design without compliance risk.

**Architectural confirmation:** Papa's offhand "could all be one DB filtered per role" is **exactly** the spine of `process_ontology.md`: one transition stream per Patient/Process, role-scoped views by filter, not by separate stores.

**Process spec implication:** Add new process `aufgaben_persoenlich` (the personal queue) and `aufgaben_team` (the shared MFA queue) to the inventory. These are *not* `email_triage` — that placeholder should be retired and replaced by these two more accurate processes.

---

## P3 · KIM-Eingang (incoming Befunde)

**Observed:** §3 of transcript. Radiologie/Pathologie-Befunde landen automatisch in MO-To-Do-Liste, automatisch dem Patienten zugeordnet, manchmal an die falsche Person geroutet.

**Canonical anchors:**

| Aspect | Grounded fact | Source |
|---|---|---|
| KIM-Empfangs-Vergütung | **GOP 86901**, 0,27 € pro empfangenem eArztbrief, Cap 23,40 €/Quartal/Arzt (gemeinsam mit 86900) | KV Hessen |
| Wer darf KIM-Adresse halten | TI-angebundene Leistungserbringer/Einrichtungen: Vertragsärzte, Vertragszahnärzte, Krankenhäuser, Apotheken, MVZ, Reha, **Pflegeeinrichtungen (Pflicht ab 1.7.2025)**, **Heilmittelerbringer (Pflicht ab 1.1.2026)**, ÖGD, Hebammen, Krankenkassen, UVT, Kammern | gematik KIM |
| Storage in TI | KIM-Fachdienst speichert Mail nur **transient** bis POP3-Abruf — kein zentrales Postfach in der Cloud | gematik |
| Storage lokal | Inhalte werden im PVS lokal gespeichert (MO-MariaDB) → **wir können sie via DB-Read beobachten ohne KIM-Schicht zu berühren** | inferiert |
| §203/DSGVO bei Beobachtung | **Metadaten-Beobachtung** (z.B. "eArztbrief um Zeitpunkt T eingegangen") **ist bereits Verarbeitung von Patientendaten besonderer Kategorien** — nicht "nur Metadaten". Erfordert AVV (Art. 28 DSGVO) + schriftliche Verpflichtung nach §203 Abs. 4 StGB + Zweckbestimmung. | [Bitkom Muster §203](https://www.bitkom.org/sites/main/files/file/import/20180718-Muster-203StGB-final.pdf) |

**Process spec implication:** No new process — the KIM-Eingang is a *signal source* for `briefe_arzt` (incoming triggers outgoing) and `aufgaben_persoenlich` (Befund landet in personal queue). Worth a `kim_eingang_observed` transition type in the schema.

**Routing-Mis-Pattern as a feature:** Detecting "Befund landet bei Arzt X aber gehört zu Patient von Arzt Y" is a high-value coherence-check our system can run that MO doesn't.

---

## P4 · Befunde dokumentieren via Schablonen (Sonografie example)

**Observed:** §4 of transcript. Befund-Schablonen mit typed fields, Auto-Ziffer-Vorschlag bei Save, Schablonen-Geltungsbereich (Privat/EBM/Selektivvertrag/UV-GOÄ).

**Canonical anchors:**

| Aspect | Grounded fact | Source |
|---|---|---|
| Sonografie Abdomen | **GOP 33042** (~163 P / 20,77 €), max. 2× pro Behandlungsfall | [monkeymed 33042](https://monkeymed.de/leistungskataloge/ebm/33042) |
| Sonografie Urogenitalsystem | **GOP 33043** (~83 P / 10,57 €), 1× pro Fall, nicht neben 33042/44/81 | [monkeymed 33043](https://monkeymed.de/leistungskataloge/ebm/33043), [KV Berlin Ausschlüsse](https://www.kvberlin.de/fuer-praxen/aktuelles/praxis-news/detailansicht/pn231218-3) |
| GOÄ Sonografie 1. Organ | **GOÄ 410** | [DGPAR](https://www.dgpar.de/blog/ultraschalluntersuchungen-abrechnen-goae-410-und-420/) |
| GOÄ Sonografie weiteres Organ | **GOÄ 420**, **max. 3× pro Sitzung** | [PVS-SE](https://www.pvs-se.de/infothek/goae/goae-tipp-multiorgansonografie-mithilfe-der-goae-420-abrechnen/) |
| GOÄ-Steigerung > 2,3 | **Schriftliche Begründung pro Befundzeile** Pflicht. Floskel-Blacklist ("erhöhter Zeitaufwand", "technisch schwierig", "besondere Qualifikation", "Inflation") wird gestrichen. | §12 Abs. 3 GOÄ; [Virchowbund](https://www.virchowbund.de/praxisaerzte-blog/goae-sonographie-abrechnung-ultraschall) |
| GOÄ-Steigerung > 3,5 | Schriftliche Honorarvereinbarung erforderlich (§2 Abs. 1, 2 GOÄ); ohne: plafondiert | §2 GOÄ |

**Co-pilot-target (§11.2 of transcript):** Papa explicitly wants "auto-recognize from Befund-Body, propose right Sonografie-Ziffer". Concrete rule shape:
- If Befund-Schablone-Typ = `sono_urogenital` AND Body lacks Leber/Nieren-Erwähnung → propose `33043` only.
- If Body contains Leber/Nieren/Pankreas/Milz → propose `33042` (Abdomen) instead.
- If Body contains Hoden + Doppler-Erwähnung → propose `33043` + Doppler-Add-on.

This is **encodable today** as a new rule in `app/billing_rules/rules_ebm.py` extension or a new `rules_sonografie.py`. Source corpus: KV-Saarland Allgemeine Abrechnungsbestimmungen + per-GOP HTML pages on `ebm.kbv.de`.

**Process spec implication:** No new process. Extends `rechnungspruefung` rule library + creates a *suggestion* surface in the Patientenakte view (when a Befund is saved, propose Ziffer-Bündel as a co-pilot pop-up — same pattern as MO does today, but driven by our richer rule corpus).

---

## P5 · ePA-Upload

**Observed:** §5 of transcript. Lokale Akte ≠ ePA. Papa lädt Befundberichte als PDF hoch (gebündelt nach Zeitraum), psychosomatische Daten mit explizitem Konsens, Labor-Daten kommen automatisch.

**Canonical anchors:**

| Aspect | Grounded fact | Source |
|---|---|---|
| ePA-Pflicht-Stand | Opt-out-ePA "für alle" seit **15.01.2025** (Modellregionen), bundesweit ab **29.04.2025**, **verpflichtende Nutzung für Vertragsärzte seit 01.10.2025** | [BMG ePA für alle](https://www.bundesgesundheitsministerium.de/epa-na-sicher/) |
| Sanktionen scharf | **seit 01.01.2026**: 1 % Honorarkürzung + Halbierung TI-Pauschale (Krankenhäuser Schonfrist bis 01.04.2026) | [AOK Sanktionen 2026](https://www.aok.de/gp/news-allgemein/newsdetail/sanktionen-nicht-nutzung-epa-2026), §341 Abs. 6 SGB V |
| GOP Erstbefüllung | **01648** — **11,34 € / 89 P**. Einmal je Versicherten **sektorenübergreifend** — nur wenn noch kein anderer LE Dokumente eingestellt hat. Extrabudgetär bis 30.06.2026. | [KBV PraxisNachricht 27.11.2025](https://www.kbv.de/praxis/tools-und-services/praxisnachrichten/2025/11-27/ab-januar-weiterhin-mehr-als-elf-euro-fuer-epa-erstbefuellung) |
| GOP Folge-Befüllung | **01647** — **1,91 € / 15 P**. Einmal **je Behandlungsfall (Quartal)**, AP-Kontakt erforderlich. **NICHT pro Dokument** (häufige Fehlannahme; Papa's "~1 €" ist diese GOP). | [KV Hessen ePA abrechnen](https://www.kvhessen.de/abrechnung-ebm/epa-abrechnen) |
| GOP ohne AP-Kontakt | **01431** — 0,38 €, falls nur Hochladen ohne Patient anwesend | KV Hessen |
| Pflicht-Inhalte | Befundberichte invasiver/operativer/non-invasiver Diagnostik (z.B. Ultraschall, OP-Bericht); bildgebende Diagnostik; Laborbefunde; eArztbrief; eMP (MIO Pilot Juli 2026, bundesweit Okt 2026) | [KBV — welche Dokumente](https://www.kbv.de/praxis/tools-und-services/praxisnachrichten/2025/07-31/neue-serie-alles-nur-eine-frage-welche-dokumente-stellen-praxen-in-die-epa-ein) |
| Sensible-Daten-Carve-out (§342 Abs. 1a / §343 Abs. 13 SGB V) | Vor Einstellung **dokumentierte Aufklärung über Widerspruchsrecht** Pflicht. Umfasst kanonisch: psychische/psychosomatische Erkrankungen, sexuell übertragbare Infektionen (HIV, Lues, Hepatitis B/C), Schwangerschaftsabbrüche. | [KBV ePA-Rechtsfragen PDF](https://www.kbv.de/documents/infothek/publikationen/praxisinfo/praxisinfospezial-epa-rechtsfragen.pdf), [Praxis Bohnet PDF](https://www.praxis-drbohnet.de/media/files/epa-hinweispflicht-auf-das-widerspruchsrecht-bei-speicherung-von-potenziell-diskriminierenden-oder-stigamtisierenden-daten1-01.pdf) |
| Schriftliche Einwilligung | **Gesetzlich nicht zwingend** — die *Aufklärung* muss dokumentiert sein. Papa's defensive "schriftliche Einwilligung" geht über das Minimum hinaus, ist aber beweissicherer und korrekt. | KBV PraxisInfo |
| Patient-Widerspruch | Granular: ePA gesamt / einzelne Leistungserbringer / einzelne Dokumente / einzelne Anwendungen. Steuerung über **ePA-App der KK** oder **Ombudsstelle**. **Praxis sieht Widerspruch nicht explizit** — Zugriff scheitert technisch im Aktensystem. | [BfDI Widerspruch](https://www.bfdi.bund.de/DE/Buerger/Inhalte/GesundheitSoziales/eHealth/WiderspruchgegendieePA.html) |
| Papa's "Krankenkasse bietet ePA noch nicht an"-Fall | Real selten; viel häufiger ist globaler Patienten-Widerspruch. | [KBV PraxisInfo]() |
| Format heute | **PDF/A** ist faktisch die einzige produktive Form. Strukturierte MIO-Roadmap (FHIR-basiert) ist offizielle gematik-Roadmap, Zeithorizont 2027+ für die meisten klinischen MIOs. Papa's Wunsch nach "Sektionen wie Ultraschall" = die offizielle Roadmap. | [INA gematik MIO](https://www.ina.gematik.de/themenbereiche/medizinische-informationsobjekte) |
| Krypto | Ende-zu-Ende in **VAU (Vertrauenswürdige Ausführungsumgebung)**; zwei unabhängige **Schlüsselgenerierungsdienste**; nur Versicherter via eGK/ePA-App hat Master-Decrypt. KK als Anbieter sieht Klartext nicht. | [gematik SGD ePA](https://fachportal.gematik.de/telematikinfrastruktur/komponenten-dienste/schluesselgenerierungsdienst-epa) |
| Lokale Akte bleibt | §630f-Pflicht erfordert lokale Persistierung **unverändert**. ePA ist eine **Kopie**, nicht Ersatz. | inferiert |
| §203-Rechtsgrundlage | **§342 Abs. 2 SGB V** als lex specialis; Patient via Nicht-Widerspruch konkludent eingewilligt; KK als Anbieter ist kein §203-Empfänger weil VAU-architektur. DSGVO: Art. 9 Abs. 2 lit. h + §22 BDSG. | gematik + BAS |

**Process spec implication:** ePA-Upload ist eine **Transition** im `briefe_arzt`-Process (Brief generated → optional ePA-Upload), nicht ein eigener Process. Add `epa_uploaded` transition type with payload `{document_type, zeitraum, sensible_data: bool, aufklaerung_dokumentiert: bool}`.

**Coherence-check the AmbiguityBanner pattern can surface:** "Sensibler Befund hochgeladen, aber Aufklärungs-Dokumentation fehlt im Akten-Eintrag" → high-value warning, regulatorisch load-bearing.

---

## P6 · KV-Fall-State-Machine

**Observed:** §6 of transcript. Patient × Quartal → KV-Fall mit States offen / abgerechnet / hybrid_drg / selektivvertrag / privat.

**Canonical anchors:** This is partly MO-internal product design and partly canonical billing-system structure. The Fall-Typen mirror real Abrechnungs-Pfade:

- `offen` / `abgerechnet` — KV-Quartalsrhythmus (KVDT, §295 SGB V)
- `hybrid_drg` — §115f SGB V (siehe P7)
- `selektivvertrag` — §140a SGB V (bilateraler Vertrag KK ↔ LE-Gruppe)
- `privat` — GOÄ, §6a für stationäre Minderung

**Process spec implication:** Add `kv_fall_status` field to `Fall` schema (`app/medical_office/schema.py`). Currently `Fall` is `_grounded=False` — this transcript adds enough to start grounding. Sunday's `extract-mo-schema.sh` will tell us the exact column shape.

---

## P7 · Hybrid-DRG via Sanakey

**Observed:** §7 of transcript. Manual entry per Fall im Sanakey-Portal mit 2FA. Papa: "wäre nicht klug zu automatisieren — das ist ja wieder zertifiziert." Could also go via KV.

**Canonical anchors — significant corrections to prior assumptions:**

| Aspect | Grounded fact | Source |
|---|---|---|
| **Sanakey Eigentum** | **100% SpiFa-Tochter** (Spitzenverband Fachärztinnen und Fachärzte Deutschlands), **NICHT BvDU**. BvDU/SpiFa-Mitglieder bekommen ~0,5pp Rabatt. BvDU's eigene Vertrags-Tochter ist **VgURO GmbH**. | [BVOU Partner Sanakey](https://www.bvou.net/partner/sanakey-contract-gmbh/), [Sanakey](https://www.sanakey.de/) |
| Datenformat | **§301 SGB V Datensatz** (Krankenhaus-Format, mit Grouper-Output: DRG, Schweregrad), **NICHT KVDT/CON-Datei**. CON-Datei-Route existiert nicht. | [GKV-SV §301](https://www.gkv-spitzenverband.de/krankenversicherung/krankenhaeuser/krankenhaeuser_abrechnung/krankenhaeuser_abrechnung_datenaustausch_dta/datenaustausch_dta.jsp) |
| Tech-Stack | **Webportal-only** (cloud.sanakey-portal.de). 2FA via **Google Authenticator TOTP** — nicht gematik, nicht eHBA, nicht TI. **Kein public REST API** für Fall-Submission. | [Sanakey-Portal FAQ](https://www.sanakey.de/sanakey-portal-info/faq/) |
| Pricing | 2,08 % brutto / 1,75 % netto vom Honorar; mit SpiFa/BvDU-Rabatt günstiger | BVOU |
| Zertifizierungs-Pflicht | **Nur Grouper muss InEK-zertifiziert sein**. Submitting software für §301 braucht **keine KBV/gematik-Zertifizierung**, weil Hybrid-DRG außerhalb §295/KV-System liegt. **Das ist eine meaningful unregulated surface.** | InEK |
| 2026 Katalog-Expansion | **904 OPS-Codes** im Katalog 2026 (von ~22 Eingriffe / vielleicht 30 Codes vorher). Urologie gut vertreten. | [Hybrid-DRG-Katalog 2026](https://www.hybrid-drg-katalog.de/katalog/aktueller-hybrid-drgkatalog-2026.html) |
| Urologie in 2026-Katalog | **IN**: Ureterstein-Entfernung (5-562.4) + Lithotripsie, Hydrozele (5-611), Hydrocele funiculi spermatici / Varikozele (5-630.5), Orchidopexie (5-624.4), Hoden/Nebenhoden/Penis-OPs, transurethrale Inzision/Exzision (5-573.20). **NEU 2026**: 5-569.x2 (sonstige Op. am Ureter, transurethral). | [InEK 2026 OPS-Anlage PDF](https://kaysers-consilium.de/wp-content/uploads/2025/11/Die-endgueltige-OPS-Liste-ergBA.pdf) |
| Urologie NICHT im Katalog | Plain diagnostische Zystoskopie (= normales EBM). Vasektomie. **TUR-P/TUR-B Status uncertain — beim Implementieren cross-checken.** | reimbursement.institute |
| KV-Pfad als Alternative | Real: KVWL/KVB/KVBerlin/KVBaWue bieten "Submit Hybrid-DRG via KV" als Service mit Vollmacht. Praxis-Vorteil: einheitliche Auszahlung. Nachteile: breite Vollmacht, langsamerer Cash-Cycle. | [KVWL Hybrid-DRG](https://www.kvwl.de/hybrid-drg) |
| Wettbewerber zu Sanakey | Helmsauer (1,49 % brutto, billigster) · medicalnetworks (1,73 %) · MEDIVERBUND AG · PVS Südwest (operative Tech-Partner von Sanakey). Sanakey ist **nicht Marktführer per Preis**, aber default für SpiFa-affiliated Fachärzte. | [BVOU Übersicht](https://www.bvou.net/uebersicht-abrechnungsdienstleister-hybrid-drg-3/) |

**Architectural verdict (neu):** Drei Pfade für Auto-Submission:
1. **Eigene §301-Pipeline mit InEK-Grouper** — sauber, aber meaningful build (Grouper-Lizenz-Kosten); umgeht Sanakey-Gebühr komplett.
2. **RPA gegen Sanakey-Portal mit TOTP-Automation** — fast to ship, **ToS-fragile** wenn Sanakey objects.
3. **Status quo manuell** — Papa's current default. Honor "wäre nicht klug zu automatisieren" als consulting-modal-restraint, aber: wir können Daten *aufbereiten* + Submit-fertig anzeigen, finalsubmit bleibt manuell. Das ist die `decline`/`co_pilot`-Phase.

**Process spec implication:** Promote `hybrid_drg_abrechnung` from implicit to explicit `dashboard_only` process initially. Phase = `decline` regarding actual submission (consistent with the existing `krankenkassen_abrechnung` boundary). We *can* prepare and pre-validate the §301-Datensatz; we *do not* automate the submit-click.

**Concrete value-prop wir Papa zeigen können:** "Sie zahlen ~2 % Sanakey-Gebühr. Bei € X Hybrid-DRG-Volumen / Quartal sind das € Y / Jahr. Eigene §301-Pipeline kostet einmalig € Z." Zahlen-Argument fürs Abwägen.

---

## P8 · Krebsregister-Meldung via Tumorscout (= unser Vorbild)

**Observed:** §8 of transcript. Tumorscout zieht Grunddaten + Behandlungsdaten + Diagnosen aus der Patientenakte; Papa füllt nur fehlende Felder aus.

**Canonical anchors:**

| Aspect | Grounded fact | Source |
|---|---|---|
| Rechtsbasis | KFRG (April 2013), **§65c SGB V** (Förderung, Datensatz, Vergütung), **LKrebsRG BW** (gilt seit Oktober 2011 für alle niedergelassenen Ärzte) | [§65c SGB V](https://www.gesetze-im-internet.de/sgb_5/__65c.html), [LKrebsRG BW](https://www.landesrecht-bw.de/jportal/?quelle=jlink&query=KrebsRegG+BW) |
| Zuständiges Register Karlsruhe | **KKR-BW (Krebsregister Baden-Württemberg)** — gemeinsame Einrichtung über DRV BW als Vertrauensstelle, klinische + epidemiologische Registerstelle. Annahme über **WebUpload** der oBDS-XML. | [KKR-BW](https://krebsregister-bw.de/) |
| Vergütung (BW, ab 01.02.2024) | **Diagnose 19,50 €**, Therapie 9,00 €, Verlauf 9,00 €, Tod 9,00 €, Pathologie 4,50 €. Bundesweit einheitlich (Schiedsspruch 24.02.2015 nach §65c Abs. 6 S. 8 SGB V). Nicht USt-pflichtig. **Privat ohne IK-Nummer: keine Vergütung.** | [KKR-BW Meldevergütung](https://krebsregister-bw.de/meldende/meldeverguetung/) |
| Datenmodell | **oBDS (onkologischer Basisdatensatz) Version 3.0.0** (freigegeben 01.03.2022). XML-Schema. **Kein FHIR.** Vier organspezifische Module: Mamma, Kolorektal, **Prostata**, Melanom. Blasen-Ca läuft über Basisdatensatz ohne eigenes Modul. | [KKR-MV oBDS 3.0.0](https://www.kkr-mv.de/das-neue-adt-gekid-xml-schema-version-3-0-0/), [GEKID](https://www.gekid.de/adt-gekid-basisdatensatz) |
| Tumorscout-Architektur | **tumorscout GmbH (Berlin, gegr. 2021)** = Web-UI für Erfassung/Validierung/Export. **axaris extrax-Plugin** liest **direkt MO-MariaDB read-only, täglich automatisch**. **Nicht xDT, nicht KBV-Schnittstelle.** Daten verbleiben lokal. | [Tumorscout](https://tumorscout.de/), [axaris extrax](https://www.axaris.de/index.php/extrax/) |
| **Medical Office in extrax-PVS-Liste** | **Explizit unterstützt**. Mechanismus = direkter DB-Read. Marktbestätigung dass dieser Pfad ToS-konform und etabliert ist. | [axaris Tumorscout Success Story PDF](https://www.axaris.de/wp-content/uploads/success_story_extrax_tumorscout.pdf) |
| §203 vs Meldung | **§65c SGB V hebt §203 auf** — gesetzlich erlaubt + gefordert. Patient muss informiert werden (mündlich oder Infoblatt), Information ist dokumentationspflichtig. **Patient kann Meldung NICHT widersprechen** (auch nicht epidemiologisch); kann nur dauerhafter personenidentifizierter Speicherung der Identitätsdaten im klinischen Teil widersprechen. | [Krebsregister RLP FAQ](https://www.krebsregister-rlp.de/fuer-melder/faq-haeufig-gestellte-fragen/1-allgemeine-fragen-und-meldepflicht/aufklaerung-von-patienten-und-patientenrechte/kann-der-patient-der-meldung-an-das-krebsregister-widersprechen) |
| Sanktionen | **Ordnungswidrigkeit, bis 50.000 € Bußgeld**. Bisher selten praktiziert, aber **2024/2025 verschicken Register erste Mahnbescheide** (teils Einschreiben). Trend zur Durchsetzung. | [Tumorscout Mahnbescheide-Artikel Mai 2025](https://tumorscout.de/2025/05/16/krebsregister-mahnbescheide-was-aerzte-jetzt-zur-meldepflicht-wissen-muessen/) |
| Wettbewerber | **d-uo Tumordokumentations-System** — Berufsverband Deutsche Uro-Onkologen, web-basiert, **für Mitglieder kostenlos**. Direktester Konkurrent in der Urologie-Niche — **bei Papa abklären ob er d-uo-Mitglied ist**. Sonst: gevko S3C, ONKOSTAR, ODSeasyNet. | [d-uo](https://d-uo.de/tumordokumentations-system/) |

**Strategic insight:** **axaris/extrax ist der lebende Beweis** dass direkter DB-Read auf Medical Office ein etabliertes, vom Markt akzeptiertes, vertraglich sauberes Pattern ist. Das stützt unsere eigene Architektur stark — wir brauchen Sunday's Schema-Dump nicht zu rechtfertigen, sondern können auf den axaris-Präzedenzfall verweisen.

**Tumorscout's Geschäftsmodell ist exakt unseres**: lokales Plugin liest PVS, Web-UI orchestriert, Datenexport bleibt beim Arzt. Unterschied: Tumorscout serviced eine extrem spezifische Niche (Krebsregister-Meldungen), wir wollen breiter (alle Workflows).

**Process spec implication:** Add new process `krebsregister_meldung` to inventory. Surface = `tool`, phase = `co_pilot` (oder zunächst `dashboard_only` bis wir die Tumorscout-Konkurrenz-Frage geklärt haben). Roles: `arzt`, `praxismanager`. Inputs: `db_write` (auto-extract from Akte). Outputs: `clipboard` / `file` (oBDS-XML zur Submission ans KKR-BW).

**Pre-Sunday-Frage an Papa hinzufügen:** "Bist du d-uo-Mitglied? Falls ja, nutzt du deren Tumordokumentations-System? Falls nein — was nutzt du derzeit?"

---

## P9 · Schablonen-Architektur (the universal pattern)

**Observed:** §9 of transcript. Every typed field in der Akte ist eine practice-konfigurierbare Schablone mit typed Schemas. Schemas existieren für inter-PVS-Portabilität.

**Canonical anchors:**

| Aspect | Grounded fact | Source |
|---|---|---|
| Inter-PVS-Portabilitäts-Anforderung | Existiert über **xDT-Familie** (BDT/GDT/LDT/KVDT) — Standards der KBV für Datenaustausch zwischen PVS und externen Quellen (Geräte, Labor) | KBV |
| MIO (Medizinische Informationsobjekte) | **Die FHIR-basierte Modernisierung** der xDT-Welt. KBV/gematik-definiert. Roadmap: eMP zuerst (Pilot Juli 2026), dann eImpfpass, Mutterpass, U-Heft, Zahnbonusheft, Laborbefunde, eArztbrief perspektivisch. **Klinische MIOs: 2027+ erwartet.** | [INA gematik MIO](https://www.ina.gematik.de/themenbereiche/medizinische-informationsobjekte) |
| Schablonen sind practice-modifiable | Bestätigt durch Papa's "ich habe die selber angelegt" — was bedeutet die Schablone-Definitions liegen in MO-Config-Tabellen (vermutlich `schablone`, `feld`, `ziffer_vorschlag`-Tabellen) | inferiert + Sunday-Schema-Dump confirms |

**Strategic insight:** **Practice-konfigurierte Ziffer-Vorschlag-Logik in MO ist ein Goldminen-Korpus.** Wenn wir die Schablonen-Tabellen mappen, sehen wir genau:
- Welche Befund-Typen die Praxis dokumentiert (vollständiger Befund-Katalog)
- Welche Ziffern pro Befund-Typ vorgeschlagen werden (= praktiziertes Abrechnungs-Wissen)
- Wo die Praxis-spezifische Optimierung liegt (vs. PVS-Hersteller-Defaults)

Das ist der direkteste Weg zu einer kompletten Abbildung des **internen Regelwerks** — komplementär zur public Recherche der **externen Regelwerks** (EBM/GOÄ/KBV/gematik).

**Process spec implication:** Sunday's `extract-mo-schema.sh` muss explizit die Config-Tabellen mit erfassen, nicht nur Patientendaten-Tabellen. Add to the script if not already there.

---

## P10 · QM-Handbuch (the consulting-modal hook)

**Observed:** Brief mention. Practice has a QM-Handbuch for onboarding. Strategic hook.

**Canonical anchors:**

| Aspect | Grounded fact | Source |
|---|---|---|
| Rechtsbasis | **§135a SGB V**: Vertragsärzte / MVZ / Vertragszahnärzte / Vertragspsychotherapeuten / zugelassene Krankenhäuser sind verpflichtet, einrichtungsintern QM einzuführen. Privatärzte rein per §135a nicht — aber faktisch über §5 MBO-Ä parallel. | [§135a SGB V](https://www.gesetze-im-internet.de/sgb_5/__135a.html) |
| Geltende RL | **G-BA QM-Richtlinie** Beschluss 18.01.2024, **in Kraft 20.04.2024**. Sektorübergreifend (Teil A), sektorspezifisch (Teil B1 vertragsärztlich). | [G-BA QM-RL Übersicht](https://www.g-ba.de/richtlinien/87/), [QM-RL PDF](https://www.g-ba.de/downloads/62-492-3427/QM-RL_2024-01-18_iK-2024-04-20.pdf) |
| §3 Grundelemente (5) | Patientenorientierung, Mitarbeiterorientierung, **Prozessorientierung**, Kommunikation+Kooperation, **Informationssicherheit+Datenschutz** | G-BA QM-RL §3 |
| §4 Methoden+Instrumente (14) | Inkl. **Prozess-/Ablaufbeschreibungen (SOPs)**, **Schnittstellenmanagement**, Checklisten, Risikomanagement, CIRS, Beschwerdemanagement | G-BA QM-RL §4 |
| Granularitäts-Vorgabe | **Keine.** "Einheitlich geregelt, nachvollziehbar dokumentiert, bei Bedarf angepasst" — Form frei (Flussdiagramm/Text/Checkliste). Praxis-üblich: jährliche Review + bei Änderungen. | G-BA QM-RL |
| Audit-Rhythmus | **Keine externe Audit-Pflicht** für niedergelassene Ärzte. KV-Stichprobe alle 2 Jahre, ~4 % der Praxen, **beratend** (nicht sanktionierend). | KV BW |
| Sanktionen | **Praktisch keine.** Bei Defizit: Beratung + Frist. Zulassungsverlust wegen QM-Mängeln nicht dokumentiert. **Das macht "QM-Compliance" allein zum schwachen Verkaufsargument** — stark wird es als "ohnehin existierende Pflicht, die wir gratis miterledigen". | KV-Materialien |
| QEP (KBV-eigenes System) | ~40 % Marktanteil. **Nicht Pflicht** — Praxis darf frei wählen (KTQ, DIN EN ISO 9001, EN 15224, EPA, EQUAM, HÄQM, eigenes). RL ist system-agnostisch. | [KBV QEP](https://www.kbv.de/praxis/tools-und-services/qep) |
| Existing QM-Software | QEP-Manager (KBV-eigen), roXtra, QM-Assist, CGM-Module. **Alle sind statische Doku-Verwaltung** (Vorlagen + Versionierung). Keiner generiert QM-Doku als Nebenprodukt eines aktiven Praxis-Tools. **→ Unsere Differenzierung.** | [systemhaus.com Vergleich 2025](https://systemhaus.com/qualitaetsmanagement-arztpraxis) |
| IT-/Datenfluss-Doku-Pflicht | QM-RL fordert es **nicht namentlich**, aber **funktional zwingend** über §3 Nr. 5 (Informationssicherheit+Datenschutz) + §3 Nr. 3 (Prozessorientierung) + §4 Schnittstellenmanagement. Standard-QM-Handbücher behandeln patientenbezogene Datenflüsse als selbstverständlich dokumentationspflichtig. | KV-Materialien |

**The hook for our offer:** "Sobald die Software einen Datenfluss ausführt, muss die Praxis ihn ohnehin im QM-Handbuch beschreiben. Wir liefern die Beschreibung als Export aus dem laufenden System — versioniert, immer aktuell, KV-stichproben-fest." Das ist sauber, weil es nichts erfindet, was die Praxis nicht ohnehin schuldet.

**Process spec implication:** Not a Process. It's a **deliverable type** — the QM-Handbuch-Export is a PDF/structured-document we generate from the transition log. Should be a documented capability of the system, not a tracked process.

---

## Summary — what changes in the codebase

| Existing | Action |
|---|---|
| `email_triage` (placeholder) | **Retire.** Replace with `aufgaben_persoenlich` + `aufgaben_team`. |
| `materialverwaltung` (placeholder) | Untouched — defer. |
| `krankenkassen_abrechnung` (decline) | Confirmed. Stays decline. Document `hybrid_drg_abrechnung` parallel — separate process, also `decline` for submit. |
| `patientenakte` (co_pilot, mock) | Schema-Erweiterung: KV-Fall-Status, Schablonen-Verknüpfung, ePA-Upload-Marker, KIM-Eingang-Marker. |
| `rechnungspruefung` (11 rules) | Add: Sonografie-Bündelungsregeln, Brief-Strukturpauschalen-Checks (86900/86901 Cap, 01660-Wegfall), ePA-GOPs (01647/01648), correct GOP 26310 typo. |
| Process inventory | Add: `briefe_arzt`, `aufgaben_persoenlich`, `aufgaben_team`, `krebsregister_meldung`, `hybrid_drg_abrechnung`. |
| `Fall` schema | Start grounding KV-Fall-State-Machine (offen / abgerechnet / hybrid_drg / selektivvertrag / privat). |
| `extract-mo-schema.sh` (Sunday) | Confirm script captures Schablonen + Ziffer-Vorschlag config tables, not just Patientendaten. |

## Questions for Papa (compiled-and-prioritized)

Critical (must-ask before significant build):

1. **Bist du d-uo-Mitglied** (Berufsverband Deutscher Uro-Onkologen)? Falls ja: nutzt du das d-uo Tumordokumentations-System? — Determines whether `krebsregister_meldung` makes sense as a target or whether they have a kostenlose Lösung.
2. **Welche Hybrid-DRG-OPS-Codes machst du tatsächlich** vs. welche gehören "wäre denkbar"? (TUR-P, TUR-B insbesondere — die sind im 2026-Katalog uncertain.)
3. **Ist deine Praxis BvDU/SpiFa-Mitglied?** Determines Sanakey-Konditionen + politische Anschlussfähigkeit für ein Roll-out auf Schwesterpraxen.
4. **Was kostet euch Sanakey/Quartal in Euro?** Konkrete Größenordnung für die Eigene-Pipeline-vs-RPA-Entscheidung.
5. **Speichert MO die rohe S/MIME-eArztbrief-Originalnachricht** revisionssicher, oder nur den dekodierten Inhalt? — Relevant für gerichtsfeste Nachweise. Wird sich im Sunday-Schema-Dump zeigen.

Non-blocking aber wichtig:

6. **Bist du d-uo-Mitglied** sehe oben.
7. **Hast du das aktuelle QM-Handbuch greifbar** für eine Baseline-Vergleich gegen das, was wir aus DB-Beobachtung extrahieren?
8. **Welche Schablonen** in MO sind Hersteller-Defaults und welche hast du selbst angelegt? (Wahrscheinlich erst nach Schema-Dump beantwortbar.)

---

## Outstanding gaps (could not be resolved by web research)

- **Genaue interne MO-Routing-Logik für eingehende KIM** (BSNR/LANR-Mapping zur Praxis-internen Arzt-ID) — nicht öffentlich dokumentiert; müssen wir aus DB-Tabellen-Inspektion am Sonntag rekonstruieren.
- **Ob MO §301-Datensätze emittieren kann** (für eigene Hybrid-DRG-Pipeline ohne Sanakey) — Hersteller-spezifisch, nicht öffentlich. Beim Doktor erfragen.
- **Konkrete Bußgeld-Praxis pro Bundesland für Krebsregister-Nichtmeldung** (Trend bekannt, Zahlen nicht).
- **Genaue extrax-Kompatibilität mit aktueller MO-DB-Version** (CGM ändert das Schema gelegentlich) — nur per Vendor-Kontakt verifizierbar.
