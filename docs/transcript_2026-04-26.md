# Transcript Extract — 2026-04-26 (Papa weekend Briefe + Abrechnung walkthrough)

> Captured from a ~60-minute walkthrough where Papa worked through his Saturday To-Do list at home and narrated what he was doing in Medical Office (MO).
>
> This document has two layers:
> 1. **Observed signal** — what was said + shown, organized by workflow.
> 2. **Gaps** — explicit unknowns that need either canonical-source grounding (web research) or a follow-up question to Papa / staff.
>
> Where a claim is sourced to a canonical reference, see [`regulatory_landscape.md`](./regulatory_landscape.md), [`billing_rules.md`](./billing_rules.md), or the per-topic research briefs being generated alongside this file.
>
> Vocabulary anchored in [`process_ontology.md`](./process_ontology.md) — every observed activity is tagged to a process ID where one already exists, or marked `[NEW PROCESS CANDIDATE]` where it doesn't.

---

## 1. The Saturday Briefe-Workflow (the spine of the session)

The dominant pattern Papa was performing the entire time. **Everything happens out of one central queue: the personal Brief-Liste.**

### 1.1 The Brief-Liste itself

- Papa keeps a personal **Brief-Liste** in MO that accumulates "Briefe I still need to write." Different list from his **To-Do-Liste** (see §2).
- Entries land here in three ways observed:
  1. **Frau Bischoff (Empfang) writes them in** when a patient comes in with Überweisung or Privatvertrag → "der braucht einen Brief".
  2. **Papa writes them himself** when finishing a Behandlung that needs a Brief later (e.g. waiting on a Urin-Befund first).
  3. **Auto-population from incoming KIM messages** (eArztbriefe from Radiologie / Pathologie) — these land directly in his personal To-Do, *not* the Brief-Liste. The Brief-Liste is only for *outgoing* Briefe.
- Each entry shows a **Wartezeit** ("seit wann eingetragen") — used to triage stale ones first.
- Per entry, Papa annotates: planned date the patient comes back (e.g. "7.5."), follow-up actions, optional notes ("Kopie an Patient", "Zytologie anhängen"). Annotations are free-text fields on the Brief-Listen-Eintrag.

> **Process tag:** This is currently *not* modeled. Closest existing process is `email_triage` (placeholder) but the Brief-Liste is much more specific and load-bearing. **[NEW PROCESS CANDIDATE: `briefe_arzt`]**

### 1.2 Producing one Brief

The motion Papa repeated dozens of times:

1. Open Brief-Listen-Eintrag → opens Patientenakte in context.
2. Choose template: **`Briefarzt` → `Briefruh`** (= Arztbrief unter Papa's Unterschrift).
3. MO **auto-generates the body** from what's been documented in the Akte since a chosen start date. Default: current Quartal. Papa can override (e.g. "ab Januar" if Tumorpatient who needs full history).
4. Papa **edits for prettiness**: removes Abrechnungs-technische Sachen, sortiert die Akten-Einträge, ergänzt Wiedervorstellungs-Empfehlung ("Wiedervorstellung zur Verlaufskontrolle in 6 Monaten").
5. **Anhängen** of related artifacts via Karteikarte right-click: CT-Befund, Zytologie-Befund vom Pathologen, etc. → attached as PDFs.
6. **Adressieren**: primary recipient (Hausarzt via KIM-Adressregister-lookup), optional Kopie an Patient (own E-Mail).
7. **Versenden**: right-click → versenden → MO routes via the per-Adressat configured Versandweg (KIM / Fax / Druck).
   - Default-Versandweg per Arzt is configured once in the Hausarzt-Adressbuch entry.
   - Empfangsbestätigung: voreingestellt ausgeschaltet ("möchte ich nicht").
8. **Hochladen in ePA**: separate explicit click. Papa generates an `ePAR-Befundbericht` (different template — strips the Anschrift, keeps just the Befund-Body) and uploads. Mostly bundles a Zeitraum-Range; sometimes individual Befunde.

### 1.3 Abrechnungs-Konsequenzen of one Brief

- If patient has an offen-KV-Fall in current Quartal → **Ziffern automatically added**.
- If no offen-Fall → Papa must **manually anlegen** ("Schein anlegen"), übernehme Diagnosen, then add Ziffern.
- Ziffern Papa named for one specific Brief: **`01601`** + **`8690`** (one for "Brief schreiben", one for "Brief verschicken").
- ePA-Upload also adds an Abrechnungs-Ziffer (~1 €).

> **Grounded** ([processes_observed.md P1](./processes_observed.md), [billing_rules.md update 2026-04-26](./billing_rules.md)): `01601` = Individueller Arztbrief (~7,72 €). `8690` ≈ `86900` (KIM-Versand 0,28 €) — paaren mit `86901` (Empfang 0,27 €), Quartals-Cap 23,40 €/Arzt. ePA-Upload-Ziffer = `01647` (1,91 € pro Behandlungsfall, *nicht* pro Dokument) oder `01648` (Erstbefüllung 11,34 € einmal sektorenübergreifend). **GOP `01660` (Förderzuschlag) ist seit 30.06.2023 weggefallen** — `rules_ebm.py` checkt jetzt darauf.

### 1.4 Edge cases observed in the Briefe-Workflow

- **Patient nicht erschienen** to scheduled Termin → no Brief, just close the Akten-Eintrag (no automated handling).
- **Patient hat ePA deaktiviert** (Widerspruch) → Papa skips upload, no error. MO surfaces this as "kein Hochladen möglich".
- **Patient mit eigener E-Mail-Adresse** → Papa noted as a wish: "I want this to auto-activate Versandweg E-Mail when the patient's E-Mail is in the Akte". Currently manual click each time.
- **Wiedervorlage-Pattern**: when a patient is scheduled to return, Papa annotates the Brief-Listen-Eintrag with the date → list-sort means "dieses Datum ist noch in der Zukunft" rows get triaged later.
- **Brief at all needed?** Papa's heuristic: yes if Hausarzt-Überweisung exists, yes if Privatvertrag, yes for Tumor-Verlaufspatienten. Otherwise optional — he uses judgment.

---

## 2. The To-Do-Liste (personal queue)

Distinct from Brief-Liste. Papa's central coordination surface for *everything that requires his action*.

### 2.1 What lands in Papa's To-Do

- **Incoming eArztbriefe via KIM** (Radiologie, Pathologie reports) — auto-routed by KIM-Adresse-of-recipient.
  - Edge: Papa showed one that landed in his queue but was Nikola's patient → likely the sender's KIM-address-mapping is configured to him as default.
- **Selbstgeschriebene Einträge**: Abrechnungs-Sachen Papa has to handle, Bescheinigungs-Anfragen ("Toilettenschlüssel-Bescheinigung"), Vertreter-Anfragen.
- **Einträge von anderen Mitarbeitern**: Frau Bischoff or another MFA can send a To-Do to him manually.
- **Markup**: Papa types "z.K." (zur Kenntnis) into the body so others can see he's seen it.

### 2.2 To-Do-Listen-Architektur in MO

- **Per-Mitarbeiter-Liste** is configurable — Papa has his own, Nikola has her own.
- MFAs share a **gemeinsame Liste** ("die Helferinnen haben zusammen eine") — Gabi-Einträge land there.
- Each Mitarbeiter can self-create new lists ("der Winsend hat sich jetzt selber eine angelegt").
- Briefe-Liste is *one such filtered list* with `Bereich Briefe Dr. Ruh` filter.

### 2.3 Per-To-Do-Eintrag binding

- **Most To-Dos are patient-bound** (FK to Patientenakte). The exception: free-form anfragen from Vertreter etc.
- For Briefe-To-Dos, the patient-binding is **always present** ("im Normalfall ist es beinahe so eine Art Anhängsel zur Patientenakte").

> **Architectural insight Papa surfaced:** "Eigentlich könnte das alles eine einzige Datenbank sein, dann filtert die To-Do-Liste raus, was für mich relevant ist." → This is exactly the spine of `process_ontology.md`: one transition stream per patient/process, filtered per role into role-scoped views. Confirms our architecture.

---

## 3. Incoming Befunde via KIM

Concrete KIM-Workflow observed:

1. External Praxis (Radiologie, Pathologie, etc.) sends eArztbrief via **KIM (Kommunikation im Medizinwesen)**.
2. KIM-Adresse-Lookup in a **globales Register** ("Kim-Verzeichnis"). Papa: "Kommunikation im Medizinwesen — eine extra Adresse, kriegst du nur als Arzt/Apotheker/Krankenhaus."
3. Eingehende Befunde landen automatisch in der konfigurierten Empfänger-To-Do-Liste in MO.
4. Befund wird automatisch in die Patientenakte einsortiert (Patientenzuordnung passiert über Versicherten-/Stamm-Daten im KIM-Payload).
5. Papa's Default-Action: "Z.K." reinschreiben + ggf. zum nächsten Brief verarbeiten.

> **Grounded** ([processes_observed.md P3](./processes_observed.md), [regulatory_landscape.md §12](./regulatory_landscape.md)): (a) S/MIME über SMTP/POP3 in der TI, KAS für große Anhänge. (b) eArztbrief = strukturiertes **CDA Release 2 (Arztbrief Plus / VHitG)** im IHE-XDM-Container — *nicht* PDF-Anhang. PDF darf innerhalb der CDA-Anlage transportiert werden. (c) Bestätigt: Vertragsärzte/-zahnärzte, Krankenhäuser, Apotheken, MVZ, Reha, Pflegeeinrichtungen (Pflicht 1.7.2025), Heilmittelerbringer (Pflicht 1.1.2026), ÖGD, Hebammen, KK, UVT, Kammern. (d) Routing in MO basiert auf KIM-Zieladresse + CDA-Header BSNR/LANR — bei reinem BSNR-Header ohne LANR landen Befunde häufig falsch (= unsere Coherence-Check-Chance).

> **Grounded**: KIM-Inhalte werden lokal im PVS gespeichert (KIM-Fachdienst nur transient bis POP3-Abruf). DB-Read-basierte Beobachtung ist möglich. **Aber:** auch reine Metadaten-Beobachtung ist Verarbeitung von Patientendaten besonderer Kategorien — erfordert AVV + §203-Verpflichtung + saubere Zweckbestimmung. Sovereign-Track-Architektur ist die einzig konsistente Antwort.

---

## 4. Documenting Befunde (the Sonografie example)

Papa walked through how a Befund actually gets into the Akte, using Sonografie as the concrete case.

### 4.1 Befund-Schablonen

- MO ships with **Datenpflegesystem** containing Schablonen for each Befund-Typ (Sonografie urogenital, Sonografie Abdomen, Zystoskopie, Uroflowmetrie, …).
- Each Schablone has **typed fields** (Organ, Größe, Auffälligkeiten, etc.) — not free text.
- Schablonen are **practice-modifiable**: Papa has customized some himself ("hab ich glaube ich selber mal angelegt").
- Schablone-Typ determines what gets shown back in filter-views (e.g. "show me all Sonografie-Befunde for this patient").

### 4.2 Auto-Abrechnung from Befund

- On saving a Befund-Schablone, MO **opens a Ziffer-Vorschlag-Popup** showing which Abrechnungs-Ziffern can be billed for that Befund-Typ.
- Papa tickt an, was tatsächlich gemacht wurde → übernehmen → Ziffer wird zum offenen KV-Fall hinzugefügt.
- Schablonen are linked to a **Geltungsbereich** (Privat / EBM / Selektivvertrag / UV-GOÄ) — same Befund-Schablone, different Ziffern depending on Versichertenstatus.

### 4.3 Ziffer-Auswahl-Logik (manual today, automatable)

- Papa: "wenn ich nur Niere und Blase gemacht habe → urogenital-Sonografie. Wenn auch Leber → Abdomen-Komplett. Wenn Hoden mit Doppler → zusätzliche Doppler-Ziffer."
- This is **deducible from the Befund-Body** — Papa actively wished for this to be automated ("man könnte aus dem Befund rauslesen").
- ✨ **High-leverage automation candidate**: rule-based mapping of Befund-Body → Ziffer-Set, surfaced as a check at save-time.

> **Grounded** ([processes_observed.md P4](./processes_observed.md)): EBM **33042** Abdomen (~20,77 €, max. 2×/Fall), **33043** Urogenitalsystem (~10,57 €, 1×/Fall, nicht neben 33042/44/81). GOÄ **410** (1. Organ) + **420** (max. 3× pro Sitzung; ab 5+ Organe Steigerung statt Doppelabrechnung). Steigerung > 2,3 = schriftliche Begründung Pflicht; Floskel-Blacklist wird gestrichen.

---

## 5. ePA (elektronische Patientenakte) interaction

### 5.1 Two distinct artifacts

- **Lokale Akte in MO** = Papa's working surface. Contains everything (Befunde as PDFs, Briefe als PDFs, Notes, Ziffern, KV-Fall-State, …).
- **ePA on TI-Server** = Patientenzentrale Cloud. Contains only what Papa explicitly uploads. Papa: "es ist dann da drin *und* in meiner Akte."

### 5.2 Was hochgeladen wird

- "Eigentlich alle relevanten Befunde."
- **Carve-out: psychosomatische Diagnosen** — only with schriftlichem Einverständnis.
- Papa pragmatic: "schreibe meistens nichts rein bei Erektionsproblemen."

### 5.3 Was schon automatisch in ePA landet

- **Labor-Daten** vom Labor "Du-Gesundheit-Direkt" — automatisch von MO ePA-seitig abgelegt.
- **Erhobene Untersuchungsbefunde** (Sonografie etc.) gehen *nicht* automatisch — Papa muss manuell hochladen.

### 5.4 Hochlade-Mechanik

- Klicke `ePAR-Befundbericht` Template → strippt Anschrift, baut Befundtext nur aus Akteninhalt ab gewähltem Datum → PDF-Generierung → Upload.
- Granularität: Papa lädt meistens **gebündelt einen Zeitraum** hoch, kann aber auch einzeln.
- Format: alles als PDF derzeit ("egal was anklickst, es wird PDF erstellt").
- Papa-Wunsch: "Irgendwann sollte das so sein, dass die Felder wie Ultraschall-Sektionen strukturiert in der ePA sind, dass man sie dort wiederfindet."
- Auch: theoretisches Bild-Upload möglich (Ultraschall-Bilder → vermutlich auch als PDF).

### 5.5 Patient-Widerspruch & Kassen-Status

- Papa zeigt einen Patienten ohne ePA-Hochlade-Möglichkeit → "der hat seine Akte deaktiviert" (Widerspruch).
- Anderer Fall: "vielleicht bietet seine Kasse das noch nicht an" (selten).

> **Grounded** ([processes_observed.md P5](./processes_observed.md), [regulatory_landscape.md §13](./regulatory_landscape.md)): (a) Pflicht seit 01.10.2025; **Sanktionen scharf seit 01.01.2026**: 1 % Honorarkürzung + halbierte TI-Pauschale. (b) **01648** Erstbefüllung 11,34 € (einmal sektorenübergreifend); **01647** Folge-Befüllung 1,91 € **pro Behandlungsfall — nicht pro Dokument**; **01431** ohne AP-Kontakt 0,38 €. (c) Granular: ePA gesamt / einzelne LE / einzelne Dokumente / einzelne Anwendungen. **Praxis sieht Widerspruch nicht explizit** — Zugriff scheitert technisch im Aktensystem. (d) FHIR-basierte MIO-Roadmap offiziell, aber Zeithorizont 2027+ für meiste klinische MIOs (eMP zuerst, Pilot Juli 2026). **Sensible-Daten-Carve-out** (psych./STI/Schwangerschaftsabbruch): dokumentierte *Aufklärung* Pflicht, schriftliche Einwilligung gesetzlich nicht zwingend (Papa's defensives Vorgehen geht über Minimum hinaus, ist aber beweissicherer).

---

## 6. KV-Fall-State-Machine

Concrete: every Patient × Quartal kombination has a **KV-Fall** entity. Observed states:

- **`offen`** — Quartal läuft, Ziffern können hinzugefügt werden.
- **`abgerechnet`** — Quartal abgeschlossen + an KV gemeldet. Neue Ziffern → Papa muss explizit "Schein neu anlegen", übernimmt Diagnosen.
- **`hybrid_drg`** — eigener Fall-Typ (separate Datenstruktur). Geht nicht über KV. Siehe §7.
- **`selektivvertrag`** — eigener Fall-Typ. Eigene Ziffern (z.B. AOK-Avocado-Vertrag). Geht über die KV-Software, aber mit anderem Ziffern-Mapping.
- **`privat`** — GOÄ-Abrechnung. Geht an PVS Südwest.

Papa observed Reibung: "wenn der Fall schon abgerechnet war, hätte er die Ziffer praktisch zugerechnet — aber so muss ich neuen Fall anlegen."

> **Architecture note:** This state-machine should be exposed in the Patientenakte view (Datenqualität tab? new "KV-Fall-Status" tab?). Currently `app/medical_office/schema.py` has `Fall` as `_grounded=False` — this transcript adds enough detail to start grounding the Fall-Schema.

---

## 7. Hybrid-DRG via Sanaki

The "complicated" workflow Papa explicitly **did not want to demo today** because it requires 2-Faktor-Auth. But surfaced detail:

- **Sanaki** = portal of an Abrechnungs-Dienstleister that handles Hybrid-DRG-Cases (former-stationary procedures jetzt ambulant, e.g. some urological OPs).
- Eigentumsstruktur: "Tochtergesellschaft, Berufsverband ist mit drin" — likely BvDU-Tochter.
- Papa zahlt sie für die Abwicklung; preisstruktur unklar (% of Honorar?).
- **Login**: 2FA mit Handy. Per-Eingriff Manueller Daten-Eintrag.
- **Could automate via KV-Software** ("über die KV kannst du auch automatisiert schicken") — Papa wählt manuell weil mehr Kontrolle.
- **Datenformat-Frage**: könnte CON-Datei (KVDT) helfen? Papa: "wenn alles als Hybrid-DRG-Fall angelegt wäre, könnte importiert werden." Aber er macht's händisch.
- **Compliance-Concern Papa raised**: "wäre nicht klug das zu automatisieren — das ist ja wieder zertifiziert." → Important caveat for our offer's scope. Probably means: *we observe + prepare data, but the final submission stays through MO/Sanaki UI*. Same pattern as our existing Krankenkassen-Abrechnung `decline` phase.

> **Grounded** ([processes_observed.md P7](./processes_observed.md), [regulatory_landscape.md §14](./regulatory_landscape.md)): (a) §115f SGB V seit 01.01.2024; **2026-Katalog 904 OPS-Codes** (von ~22 vorher). (b) Urologie IN: Ureterstein 5-562.4 + Lithotripsie, Hydrozele 5-611, Hydrocele/Varikozele 5-630.5, Orchidopexie 5-624.4, Hoden/Nebenhoden/Penis-OPs, transurethrale Inzision/Exzision 5-573.20, neu **5-569.x2**. NICHT im Katalog: plain diagnostische Zystoskopie, Vasektomie. TUR-P/TUR-B uncertain — cross-checken. (c) **Sanakey = SpiFa-Tochter** (NICHT BvDU); webportal-only, 2FA via Google Authenticator TOTP, **kein public REST API**, kein CON-Datei-Import (Format ist **§301 SGB V**, nicht KVDT). (d) **Nur Grouper muss InEK-zertifiziert sein** — Submitting-Software für §301 braucht keine KBV/gematik-Zertifizierung. Meaningful unregulated surface. Drei Pfade: eigene §301-Pipeline (sauber, Grouper-Lizenz-Kosten), RPA gegen Sanakey (ToS-fragile), oder co_pilot+manual-submit (Papa's bevorzugte Linie).

---

## 8. Krebsregister via Tumorscout

Surfaced as a *positive comparison* to the Sanaki-pain:

- **Tumorscout** = software die automatisch aus der Patientenakte die Grunddaten + Behandlungsdaten + Tumor-Diagnosen rauszieht.
- Papa muss nur die fehlenden Felder ausfüllen ("damit du Geld kriegst, damit es vollständig ist").
- Vergütung pro Meldung — Papa namet keine konkrete Summe.
- **Pro Meldungstyp**: Erstdiagnose, Verlauf, Tod (impliziert).

> **Architectural insight:** Tumorscout is **already doing exactly what we want to do** — read MariaDB, extract structured data, present a co-pilot interface for the residual manual work. This is *the* template for our entire offer's UX.

> **Grounded** ([processes_observed.md P8](./processes_observed.md), [regulatory_landscape.md §15](./regulatory_landscape.md)): (a) KFRG, **§65c SGB V**, **LKrebsRG BW** (gilt seit Okt 2011 für niedergelassene Ärzte). (b) **KKR-BW** (Krebsregister Baden-Württemberg) via DRV BW als Vertrauensstelle. (c) Diagnose **19,50 €**, Therapie/Verlauf/Tod je 9,00 €, Pathologie 4,50 € — bundesweit einheitlich. Privat ohne IK: keine Vergütung. (d) **tumorscout GmbH** (Berlin, gegr. 2021); axaris **extrax**-Plugin liest **direkt MO-MariaDB read-only, täglich automatisch** — nicht xDT, nicht KBV-Schnittstelle. **MO ist explizit in der extrax-PVS-Liste** = Marktbestätigung dass DB-Direct-Read sauberes etabliertes Pattern ist. (e) **oBDS Version 3.0.0** XML-Schema (nicht FHIR), organspezifische Module inkl. **Prostata**. (f) **d-uo Tumordokumentations-System** (Berufsverband Deutsche Uro-Onkologen) ist direktester Konkurrent — **für Mitglieder kostenlos**. → Bei Papa abklären ob er d-uo-Mitglied ist.

---

## 9. Schablonen-Architektur (the universal pattern under everything)

This emerged across multiple workflows and is **the most important architectural insight from the transcript**:

> Every typed field in the Akte (Befund-Schablone, Brief-Template, Ziffer-Vorschlag, To-Do-Eintrag) is a **practice-configurable mapping** between Akten-Inhalt and structured Schemas. The Schemas exist for inter-PVS portability (regulatory: gleiche Felder über Hersteller hinweg, damit Migration möglich). The mapping-rules are practice-local.

Implications:

- **Database schema** in MO is *much* more structured than the Briefe-as-PDF surface suggests. The PDFs are derived artifacts; the DB has typed fields per Befund-Typ.
- **Practice-configured Ziffer-Vorschlag-Logik** lives in MO config tables. This is exactly the rule corpus we want to extract — practice-local Abrechnungs-Optimierung emerges from how these are configured.
- **Inter-PVS-Portabilitäts-Anforderung** (Papa: "damit man wechseln kann") = there must be a canonical Schema-Definition per Befund-Typ at some regulatory layer. Likely **xDT (BDT/KVDT)** or **MIO (Medizinische Informations-Objekte) by KBV/gematik**.

> **Grounded** ([processes_observed.md P9](./processes_observed.md)): xDT-Familie (BDT/GDT/LDT/KVDT) ist die historische Standard-Schicht für Inter-PVS-Datenaustausch. **MIO** (Medizinische Informationsobjekte) ist die FHIR-basierte Modernisierung, KBV/gematik-definiert. Roadmap: eMP zuerst (Pilot Juli 2026), dann eImpfpass/Mutterpass/U-Heft/Zahnbonusheft/Laborbefunde, eArztbrief perspektivisch — **klinische MIOs für Befund-Schemas: 2027+**. Heute lebt der "common subset" zwischen Herstellern faktisch in xDT + lokaler Schablonen-Konfiguration. → Sunday's `extract-mo-schema.sh` muss explizit Schablonen-Tabellen mit erfassen.

---

## 10. The QM-Handbuch reference

Brief mention by Papa (in earlier session) — "we have a QM document for onboarding new employees, covers the basics."

> **Strategic hook:** Per `feedback_consulting_not_product.md` and the consulting-modality framing, our offer's "process documentation as side-effect" deliverable maps directly onto the **§135a SGB V QM-Verpflichtung** every Praxis already has. Reframing as "we maintain your digitales QM-Handbuch as a side-effect of running our software" is regulatorily clean and a real value prop the incumbents don't have.
>
> **Grounded** ([processes_observed.md P10](./processes_observed.md), [regulatory_landscape.md §16](./regulatory_landscape.md)): (a) **G-BA QM-RL** Beschluss 18.01.2024, in Kraft 20.04.2024; **§3 Grundelemente** = Patientenorientierung / Mitarbeiterorientierung / **Prozessorientierung** / Kommunikation+Kooperation / **Informationssicherheit+Datenschutz**; **§4 Methoden+Instrumente** (14, alle Mindeststandards) inkl. **Prozess-/Ablaufbeschreibungen (SOPs)** + **Schnittstellenmanagement**. Granularität: keine Vorgabe. (b) Nicht namentlich, **aber funktional zwingend** über §3 Nr. 5 + §3 Nr. 3 + §4 Schnittstellenmanagement. (c) Keine externe Audit-Pflicht; KV-Stichprobe alle 2J., ~4 % der Praxen, **beratend**. **Sanktionen praktisch keine** — Zulassungsverlust wegen QM-Mängeln nicht dokumentiert. (d) QEP-Manager (KBV-eigen, ~40 % Marktanteil), roXtra, QM-Assist, CGM-Module — **alle statische Doku-Verwaltung. Keiner generiert QM-Doku als Side-Effect eines aktiven Tools — unsere Differenzierung.**

---

## 11. Wishes Papa explicitly voiced (automation backlog)

Direct quotes / paraphrases of "would be nice":

1. **Auto-Versandweg E-Mail** when patient has E-Mail in Stammdaten.
2. **Ziffer-Auswahl aus Befund-Body** — auto-recognize "nur Niere+Blase" vs "auch Leber" → propose right Sonografie-Ziffer.
3. **Letzter-Brief-Datum-Auto-Vorschlag** — when re-issuing a Brief, auto-pre-fill "since last Brief" instead of Papa manually re-thinking each time.
4. **Strukturierte Felder in ePA** — Sonografie als Sektionen, nicht als PDF-Blob. (This is *not* on us — it's a gematik/ePA roadmap item.)
5. **Optimierungs-Tipps** ("PVS könnte auch noch X abrechnen") — explicit ask to surface Abrechnungs-Optimierungs-Möglichkeiten in-flow, not after-the-fact via PVS Südwest's Beanstandungen.
6. **Hybrid-DRG-Daten-Import via CON-Datei** — instead of manuelle Eingabe in Sanaki-Portal.

These map cleanly to **rule additions in `app/billing_rules/`** + new co-pilot tools. None require regulatory permission to do *as suggestions*; only the actual submission stays manual.

---

## 12. Things explicitly out-of-scope for our offer (Papa-confirmed)

- **Direkte Submission an KV / Sanaki / Krebsregister** — bleibt zertifizierte-Software-Aufgabe (MO + Sanaki + Tumorscout).
- **2FA-bypassing für Sanaki** — Papa: "wäre nicht klug, das ist zertifiziert."
- **KIM-Adressregister-Modifikation** — gematik-Hoheit.
- **Kartenleser / SMC-B / TI-Connector-Pfad** — sealed gematik-Pipeline, never touched.

These are the **boundaries** of the consulting offer. Our value lives strictly *upstream* of these submission interfaces.

---

## 13. Summary — what the transcript adds to our existing model

| Existing model | What this transcript changes / extends |
|---|---|
| `email_triage` placeholder | Should be replaced or supplemented by `briefe_arzt` (outgoing Briefe queue) and the To-Do-Liste pattern (which is way more central than email triage). |
| `patientenakte` (read-only Mock) | Schema needs Schablonen, KV-Fall-State, ePA-Upload-Status, KIM-Eingang-Markers, To-Do-Verknüpfung. |
| `rechnungspruefung` (11 rules) | Add Sonografie-Bündelungsregeln, Brief-Strukturpauschalen-Checks, Hybrid-DRG-Detection, ePA-Upload-Vergütungs-Checks. |
| `krankenkassen_abrechnung` (decline) | Stays decline. Confirmed boundary. |
| `materialverwaltung` (placeholder) | Not touched in this transcript — defer. |
| Process ontology | **Validated**: Papa's "could be one DB, filtered per role" matches the ontology's transition-stream + role-scoped-view design. |

---

## 14. Open follow-up questions for Papa (next session)

Compiled high-signal-only — questions whose answers materially change architecture or scope:

1. **Brief-Liste vs To-Do-Liste**: confirm these are separate MO entities or one with filters.
2. **KIM-Routing-to-staff inside MO**: how is the "this Befund goes to Dr. Ruh's queue" routing actually configured? Per KIM-address-mapping or per-Patient-Behandelarzt?
3. **Schablonen-Editor**: who can modify Befund-Schablonen in your MO instance — only Papa, or every user?
4. **Sanaki commercials**: % of Honorar? Flat fee? Per-Fall fee?
5. **Tumorscout vendor name** — confirmation. Is it "Tumorscout" verbatim or a different product name?
6. **ePA-Vergütungs-Ziffer**: confirm exact GOP and ~Euro-Wert.
7. **Practice's QM-Handbuch**: ist es greifbar? Wäre ein nützlicher Baseline-Vergleich gegen das, was wir aus DB-Beobachtung extrahieren werden.
8. **Schablonen-Konfiguration für Ziffer-Vorschläge**: ist die per-Praxis konfiguriert oder Hersteller-default? (Determines whether config tables in MO carry practice-IP we should export.)

---

## 15. What this transcript does *not* contain (gaps the next session should fill)

- **Phone-call workflow** (Frau Bischoff am Telefon) — not observed at all. Likely high-volume + high-leverage.
- **MFA-Behandlung-side workflow** — Vorbereitung, Lagerung, Materialbedarf — black box still.
- **Quartals-Abrechnung** — the actual end-of-quarter event was explicitly skipped ("zu kompliziert für heute").
- **Fehler-Beanstandungen von KV / PVS Südwest** — the feedback-loop where rejected Ziffern come back with reasons. Our Plausibilitätsprüfung would be most powerful with examples from this corpus.
- **Personal-Schichtplan / Urlaubsverwaltung** — never touched.
- **Materialbestellungen** — never touched.
- **Privat-Abrechnung (GOÄ end-to-end)** — Papa explicitly skipped, said "das machen wir heute nicht."
- **Notfall-Workflows** — z.B. Patient mit akuten Symptomen, Krankenhaus-Einweisung, …
