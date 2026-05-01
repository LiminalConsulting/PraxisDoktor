# MO Schema Inventory — `medoff` database, uro-karlsruhe

Stage 1 of the deep-work pipeline. Schema-only inspection (no PII, no row content) of the 153 tables in Papa's Medical Office MariaDB, dumped 2026-04-29.

Source artifacts (gitignored, in `tooling/clients/uro-karlsruhe/mo_schema_2026-04-29/`):
- `medoff_schema.sql` — DDL for all 153 tables
- `table_sizes.tsv` — row counts + byte sizes
- `mostat_schema.sql` — empty (deprecated/unused namespace, ignore)

This document is the bridge from raw schema → Stage 2 query design.

---

## The architectural finding: `dbsprot` is the workflow ground truth

**`dbsprot` is the central audit/replication log.** 10.9M rows, 4.8 GB. By far the largest table. Schema:

```
FSurogat       bigint    -- log entry ID
FPrimarykey    varchar(35)  -- the affected row's PK in another table
FTablename     varchar(20)  -- which table was touched
FTyp           smallint  -- INSERT / UPDATE / DELETE marker
FDatum         int       -- date of write (YYYYMMDD)
FUhrzeit       int       -- time of write (HHMMSS)
FServersrcid   int       -- which MO instance wrote it
FUserid        int       -- which user (FK → nutzerneu)
FVersion       smallint  -- row version
FPatnr         int       -- patient affected (FK → patstamm)
FXmlinhalt     longtext  -- *** the full XML of the changed row ***
FEpoch         bigint    -- replication ordering
FEpochtime     datetime  -- wall-clock timestamp
```

**This is not a "_history" parallel-tables pattern, not a trigger-based shadow.** This is a single, append-only, central change-log. Every meaningful write to any table in MO ends up here as `(table, primary_key, user, time, patient, action_type, full_xml_payload)`.

**Implications:**

1. **§630f compliance is implemented exactly as the law assumes** — append-only, content-addressable, attributable. We can document this directly in QM-Handbuch §3 Nr. 5 (Informationssicherheit).
2. **Workflow mining is one query** — `SELECT FTablename, FTyp, FUserid, FEpochtime FROM dbsprot WHERE FEpochtime BETWEEN ...` gives the entire stream of "who did what when" without ever pulling `FXmlinhalt`.
3. **The full XML payload is the "second pass" capability** — once we know the patterns from metadata-only mining, we can selectively pull `FXmlinhalt` for specific event types to see what the actual content shape looks like. Fully PII-bearing — handle with extreme discipline.
4. **`FPatnr` is the foreign key that lets us hash and join** — every dbsprot row is patient-attributed. One-way hash on `FPatnr` at extract time keeps rows correlatable across the stream while making re-identification impossible without server access.

The §630f-mandated audit trail and the workflow-mining substrate are the same thing. Architecturally elegant; legally clean; compliance and analysis are unified.

---

## The MO column-naming convention

Every table prefixes columns with `F` (probably "Field"), suffix-cased. PKs are always `FSurogat` (surrogate key). German abbreviations dominate. A table with `FPatnr` joins to `patstamm.FSurogat`. A table with `FArztnr` joins to either `nutzerneu` (in-house users) or `earzt` (external doctors). A table with `FBehgrundnr` joins to `behgrund` (Behandlungsgrund).

Dates are stored as `int` in YYYYMMDD form (`FDatum`). Times as `int` in HHMMSS form (`FZeit`). This is a Firebird-era convention — when MO migrated to MariaDB they kept the integer encoding rather than converting to native DATE/TIME types. Worth noting because we'll need to convert at query time.

`_fsurogat_seq` tables are sequence/counter tables — ignore, they hold one row each tracking the next surrogate ID for each main table. ~80 of the 153 are these. The actual signal is in ~70 real tables.

---

## Table classification

### TIER A — Workflow ground truth (what we mine)

| Table | Rows | Size | Role |
|---|---|---|---|
| `dbsprot` | 10.9M | 4.8 GB | **The central audit log.** Mine this for everything. |
| `ltag` | 3.3M | 1.6 GB | "Leistungstag" — every clinical event entry per patient per day. Clinical surface. |
| `leistung` | 896K | 235 MB | Lab/measurement results (with values + units + free-text result). Diagnostic surface. |
| `leistltagid` | 852K | 34 MB | Join: which Leistung came from which ltag. |
| `behgrund` | 571K | 58 MB | "Behandlungsgrund" — diagnosis chains, ICD codes, encounter reasons. |
| `schdiag` | 446K | 15 MB | Schein × Diagnosis many-to-many. The billing-relevant diagnosis attachment. |
| `termin` | 231K | 60 MB | Appointments (full lifecycle: Terminiert → Komm → Behandlung → Erledigt). |
| `patfall` | 153K | 114 MB | **Patient × Fall**. Every patient-quarter-billing-context. |
| `beschein` | 107K | 31 MB | Bescheinigungen (AU, etc). |
| `gebuehrzeit` | 90K | 6 MB | GOP/billing-position time-tracking. |
| `d2dmail` | 82K | 23 MB | **KIM/eArztbrief corpus** — incoming + outgoing. Full text in `FText`. |

### TIER B — Patient & participant master records (small, high PII density per row)

| Table | Rows | Notes |
|---|---|---|
| `patstamm` | 59K | Patient master — name, DOB, address, insurance #, IK. **Maximum PII per row.** Never extract content. |
| `patdetail` | 9K | Auxiliary patient details. |
| `patrelation` | 14K | Patient family/contact relationships. |
| `patmark` | 1K | Patient flags/markers. |
| `earzt` | 7.6K | External doctor directory (Hausärzte, Fachärzte you communicate with). |
| `nutzerneu` | 19 | **In-house users** (Papa, MFAs, Helferinnen) — usernames + hashed passwords. The `FUserid` foreign key in dbsprot points here. |
| `arbeitg` | 0 | Employer directory (unused). |

### TIER C — Practice IP / configuration goldmines (no patient PII)

These hold the practice-specific automation logic that distinguishes Papa's practice from a vanilla MO install. **These are safe to extract in full** — no patient data, structural only.

| Table | Rows | Role |
|---|---|---|
| `vorlage` | 30 | **Schablonen / templates** — Befund templates, Brief templates with their full programs (`FProgramm` longtext). Practice IP. |
| `formular` | 204 | Forms (KBV-form definitions + practice-modified). |
| `textbaustein` | 73 | Text snippets (canned phrases, abbreviations). |
| `makrobut` | 150 | Macro buttons. |
| `medfavorit` | 27K | Medication favorites — what Papa actually prescribes. Practice-IP-as-data. |
| `favorit` | 0 | (empty) |
| `ebmverknt` | 2.4K | EBM Ziffern-Verknüpfungen — billing-code linkage rules. |
| `goaverknt` | 1 | GOÄ linkage rules. |
| `ebmgebordt` | 22 | EBM-Gebührenordnung references. |
| `goagebordt` | 4 | GOÄ refs. |
| `aevgverknt` | 955 | AEV (Selektivverträge) Ziffern-Verknüpfungen. |
| `uvverknt` | 0 | UV-GOÄ rules (unused). |
| `drgverknt` | 0 | Hybrid-DRG rules (unused — confirms Papa's "nicht eingerichtet"). |
| `haevgdiagregel` | 4.3K | HÄVG (Hausarzt-zentrierte Versorgung) diagnosis rules. |

### TIER D — KIM / TI / ePA infrastructure (operational metadata)

| Table | Rows | Role |
|---|---|---|
| `epaakteninfo` | 5.2K | ePA-Akten state per patient. |
| `epaaktenprot` | 4.9K | ePA access log (per-patient, per-document). |
| `epaentitlements` | 7.3K | ePA access permissions. |
| `epaeml` | 2.6K | ePA EML exports (24 MB — has document blobs). |
| `epaikprovider` | 91 | ePA provider directory. |
| `epadocumentinfo` | 0 | (empty — possibly newer feature unused) |
| `epaerrorprot` | 9 | ePA errors. |
| `epavauinfo` | 4 | ePA VAU info. |
| `epaautvaucert` | 2 | ePA cert. |
| `kvconnectabr` | 32 | KV-Connect billing transmissions. |
| `chipcard` | 0 | (empty — eGK reads not persisted, makes sense) |

### TIER E — Workflow / system tables (internal, non-PII)

| Table | Rows | Role |
|---|---|---|
| `mosystem` | 1 | System config row. |
| `mosystemdetail` | 2 | System config. |
| `mandant` | 1 | Practice/tenant ID. |
| `regkt` | 225 | Registrierkasse (cash-register entries). |
| `kassenbuch` | 3.5K | Practice cash book. |
| `barkasse` | 1 | Cash-drawer state. |
| `tempkasse` | 1 | Cash-staging. |
| `terminzone`, `tzone`, `tzonesync`, `wzone`, `zone` | 0–31 | Appointment-zone configuration. |
| `nutzerzugriff` | 3.7K | User-access log (auth events). |
| `dbserror`, `dbsluecke`, `dbssvrluecke`, `dbssyncfail`, `dbssparam`, `dbsid`, `dbsidepoch`, `dbstransaction*` | 0 | DB-replication infrastructure (mostly empty). |
| `dienst` | 0 | Service-shifts (empty). |
| `nettest`, `tcpunreachable` | 0 | Network diagnostics. |
| `geraet` | 0 | Devices (empty). |
| `archiv` | 4 | Archive entries. |

### TIER F — Specialized / mostly-empty (decline scope)

| Table | Rows | Note |
|---|---|---|
| `morbirsa` | 13K | Morbi-RSA-Risikoadjustierung (statutory health-insurance scoring). |
| `recall`, `erinnerung`, `erinnerungansicht` | 0–14 | Recall/reminder system (mostly unused). |
| `impfdoc`, `dosisbarcode`, `meddosis` | 19–411 | Medication / vaccination admin. |
| `extauftr`, `nauftrag`, `liefernt` | 0–363 | External orders. |
| `kbanhang` | 17 | KB attachments. |
| `apotheke` | 3 | Pharmacy directory. |
| `ldtarc` | 70 | LDT (Labor-Datenträger) archive. |
| `hl7prot` | 0 | HL7 communication (unused). |
| `hbauserid`, `idpauth`, `weblogin`, `zertifikat` | 2–168 | Identity / cert plumbing. |
| `mailkonto`, `mail`, `comdoxx` | 0–8 | Email accounts (D2D channel separate). |
| `addondb`, `globalitems`, `eigmed`, `markier` | 1–1.7K | Misc config. |
| `haevgmed*`, `haevgmv*`, `haevgpatvertrag*`, `haevgvertpartner` | 0–69K | Hausarzt-zentrierte Versorgung — Papa's HÄVG participation. |
| `tsstermin*`, `terminsync*`, `terminerror`, `terminzchanged` | 0–6.9K | Appointment sync (TSS = Terminservicestelle integration). |
| `erezeptidpool` | 31 | E-Rezept ID pool. |
| `ptvprot`, `ptvcode` | 0 | Psychotherapie-Verfahren (unused — Papa's not psych). |
| `awsprovenienz` | 0 | (empty) |
| `gevkoamdisabled`, `gevkoammhist`, `gevkodatahist`, `vov_disabled` | 0 | Disabled/historical markers. |
| `sumprot` | 0 | (empty) |
| `sdkrwconfig` | 0 | (empty) |
| `tnegtag` | 22 | "Negative Tage" (closed-day markers). |

---

## What the table sizes tell us about Papa's practice

- **59,035 patients in the master record.** That's the lifetime patient count. Not all active.
- **153K Fälle** (patient × quarter × billing-context) — averaging ~2.6 Fälle per patient lifetime.
- **3.3M Leistungstag entries** — ~22 ltag entries per Fall, ~56 per patient. Reasonable for a urology practice.
- **231K Termine** appointed, of which appointment outcomes are tracked through the lifecycle (Terminiert / Komm / Behandlung / Erledigt — four timestamps per row).
- **82K KIM/D2D mails** — that's the eArztbrief corpus. Big enough for routing-pattern analysis.
- **3.5K Kassenbuch entries** — light, suggests most billing flows through KV not direct cash.
- **30 Vorlagen** — the practice has 30 active Schablonen. Very tight — these 30 templates encode most of Papa's clinical IP.
- **27K Med-Favoriten** — Papa's prescribing fingerprint is rich and well-encoded.
- **0 rows in `drgverknt`** confirms Papa hasn't activated Hybrid-DRG inside MO. Sanakey lives outside.

---

## What's missing / confirmed-not-here

- **No `kim_eingang` table by name** — incoming KIM-Briefe arrive into `d2dmail` (typed via `FTyp` + `FStatus`). Single corpus, both directions. Filter on those columns at query time.
- **No `briefe_arzt` table by name** — outgoing Briefe land in `d2dmail` too. Same conclusion.
- **No `aufgaben*` tables visible.** The To-Do-Liste from §2 of the transcript may live as a typed view over `ltag` (`FEintragsart` discriminator) or `dbsprot` (entry type). **One of the first things to validate** in Stage 2 design.
- **No `_history` tables.** Confirmed: history is centralized in `dbsprot`.
- **No raw S/MIME storage table.** The KIM crypto-original is probably not retained — only decoded content lands in `d2dmail`. Worth raising as a §630f gap if Papa cares about court-grade evidence.

---

## PII column classification (for Stage 2 extraction)

For every Tier A/B table, this is the per-column hygiene policy:

### `dbsprot` — the central log
- **Extract:** `FSurogat`, `FTablename`, `FTyp`, `FDatum`, `FUhrzeit`, `FUserid` (small int — **hash**), `FEpoch`, `FEpochtime`, `FVersion`, `FPrio`
- **Hash:** `FPatnr` (one-way SHA-256 with server-side salt → 16-char hex prefix), `FPrimarykey` (only if joining; otherwise drop)
- **Drop entirely:** `FXmlinhalt` (this is the full row content — never extract in bulk)

### `patstamm` — patient master
- **Never extract row content.** Only mine via `dbsprot` (which records who/when/which-patient touched, never the names).
- For Stage 2, the only thing we need from `patstamm` is `COUNT(*)` per filter (e.g. age distributions via aggregated `FGeburtsdatum`-derived buckets — but bucketed, not raw).

### `patfall` — Fall records
- **Extract:** `FSurogat` (hash), `FVon`, `FBis`, `FAbgerechnet`, `FScheintyp`, `FScheinart`, `FBearbeitungsstatus`, `FTarif`, `FAmbulstat`, `FBezahltdatum`, `FAufnahmezeit`, `FGebuehrenordnung`
- **Hash:** `FPatnr`, `FArztnr`
- **Drop:** `FProbennr` (sample IDs — practice-internal but link to lab refs), `FRechnungsnummer`, `FMemo` (free text), `FVersichertennummer`, `FIk`

### `ltag` — clinical entries
- **Extract:** `FSurogat` (hash), `FDatum`, `FZeit`, `FEintragsart` (the *type* of entry — discriminator), `FStatus`, `FFLAGS`, `FIcdcode` (clinical content but coded — see note), `FAnordnutzernr`/`FDurchfnutzernr`/`FAusfnutzernr` (hash all three — they're the workflow chain "ordered by → executed by → reported by")
- **Hash:** `FPatnr`, `FArztnr`, `FBehgrundnr`, `FScheinnr`, `FLstgerbnr`, `FBetriebsnr`
- **Drop:** `FText` (varchar 80 — free-text annotation), `FDetails` (longtext — everything)

**ICD codes deserve a note**: ICD-10 codes are clinical content but they're a closed vocabulary, not free text. For the workflow analysis they're hugely valuable (they're the "what *kind* of patient is this" signal). They're not direct PII alone but, in combination with date + practice context, can be re-identifying for rare diagnoses. **Default policy: extract them.** They're the analytical core. The privacy gain from dropping them is small; the analytical loss is enormous.

### `leistung` — measurement results
- **Extract:** structural cols, `FSchluessel` (the lab/measurement code — closed vocabulary), `FErgebnis` (numeric value — clinical fact, not PII), `FEinheit` (unit), `FStatus`
- **Hash:** `FPatnr`, `FArztnr`, `FBehgrundnr`, `FScheinnr`, all `*nutzernr` cols
- **Drop:** `FErgebnistext` (free text), `FText`, `FMemo`, `FIdliste`

### `behgrund` — diagnoses
- **Extract:** `FSurogat` (hash), `FDatum`, `FZeit`, `F4201` (Behandlungs-art per KBV §4201), `FKlasse`, **`FIcdcode`** (the actual diagnosis), `FStatus`, `FId`
- **Hash:** `FPatnr`, `FNutzernr`
- **Drop:** `FText` (free-text annotation), `FErlaeuterung`, `FAusnahme` (all longtext free fields)

### `d2dmail` — KIM/Briefe corpus
- **Extract:** `FSurogat` (hash), `FStatus`, `FTyp` (discriminates: Brief out/in/Befund-in/etc.), `FErstelldatum`, `FErstellzeit`, `FAccount`, `FAccounttyp`, `FMailaccounttyp`, `FGelesen`, `FSymbol`
- **Hash:** `FArztnr`, `FNutzernr`, `FEmpfaengerid` (the receiving doctor's ID — preserves "same recipient across messages" signal), `FReferenznr`
- **Drop:** `FEmpfaenger` (full email/KIM address — drop, hashed `FEmpfaengerid` is sufficient), `FBetreff` (subject — free text PII), `FText` (the full Briefe content — strict drop), `FDatei` (BLOB attachment), `FSchluessel`, `FMemo`

### `termin` — appointments
- **Extract:** `FSurogat` (hash), `FZonenid`, four-stage timestamps (`FDatumvon/Zeitvon`, `FKommdatum/Zeit`, `FBehandlungsdatum/Zeit`, `FErledigtdatum/Zeit`), `FAttribute`, `FTerminiert`
- **Hash:** `FPatnr`, `FAnordnutzernr`, `FAusfnutzernr`
- **Drop:** `FText`, `FBemerkung` (free-text reason fields)

### `vorlage`, `formular`, `textbaustein`, `medfavorit` — practice IP
- **Extract everything.** These have zero patient PII. They're how Papa configured his practice.
- The `FProgramm` longtext in `vorlage` is the actual template logic (probably MO's macro language). Worth reading directly.

### `nutzerneu` — internal users
- **Extract:** `FSurogat` (hash), `FTyp`, `FInitialen`, `FBeschreibung`
- **Drop:** `FUsername`, `FKennwort` (passwords — even though they're hashed by MO), `FHbaiccsen`, `FiPadID`

The 19 nutzer rows = Papa + MFAs. We want to *count* and *attribute*, not identify. Hashed user IDs let us see "user X did this 47 times Mon-Wed" without knowing who user X is.

---

## Stage 2 query design — concrete proposal

The first analytical pass should be **a single query against `dbsprot`** that produces a fully pseudonymized event stream over a meaningful time window (proposed: 1 quarter ≈ 800K-1M rows, manageable on Mac).

```sql
SELECT
  FSurogat                                         AS event_id,
  FEpochtime                                       AS ts,
  FTablename                                       AS entity_type,
  FTyp                                             AS action,
  SUBSTRING(SHA2(CONCAT('<SALT>', FUserid),  256), 1, 16) AS user_h,
  SUBSTRING(SHA2(CONCAT('<SALT>', FPatnr),   256), 1, 16) AS patient_h,
  FVersion                                         AS version
FROM dbsprot
WHERE FEpochtime >= '2026-01-01' AND FEpochtime < '2026-04-01'
ORDER BY FEpochtime
```

**Properties:**
- 1 row = 1 write event in MO. ~800K-1M rows for one quarter.
- Hashes break re-identification but preserve correlation. Papa can re-hash any (patient_id, user_id) on his side to find a specific row when we point at an anomaly.
- `FXmlinhalt` is **not** extracted. We see *what type of action happened to whom by whom when*, never *what was changed*.
- This single CSV (~50-100 MB) is the input for the first Opus 4.7 analysis pass.

**What Opus can find from this alone:**
- Workflow patterns: "after a `behgrund` insert by user X, a `ltag` insert follows within Y minutes 87% of the time"
- User specialization: which user_h does which entity_types most often
- Time-of-day rhythms: when does each workflow type spike
- Quarterly rhythms: which entity_types cluster at quarter-end (Quartalsabschluss patterns)
- Co-occurrence patterns: "Befund inserts cluster with leistung inserts and ePA-uploads"
- Anomalies: missing follow-ups, broken cascades, stuck states

**What Opus can NOT find from this alone (needs Stage 3):**
- The *content* of any specific row (fine — that's the point).
- ICD-code or GOP-code distributions (those need extracting from the targeted spine tables, not dbsprot).
- The shape of free-text patterns.

For **Stage 3**, we extract *narrowly* — e.g. for the Briefe-Workflow (P1), pull from `d2dmail` only the structural fields + hashed IDs over the same window, never the body. For Rechnungsprüfung (extending P4), pull from `behgrund` + `ltag` + `leistung` + `schdiag` the structural cols + ICD codes + measurement codes, hashed where appropriate.

---

## Open questions to validate during Stage 2 design

1. **What does `FEintragsart` discriminate in `ltag`?** Probably the To-Do-Liste vs. real clinical entries vs. KIM-Eingang signals. Need a lookup table or a sample of distinct values to know.
2. **What does `FTyp` discriminate in `d2dmail`?** Incoming vs outgoing × KIM vs other. Without this we can't separate Briefe-from-others.
3. **What's `FStatus` semantics in `ltag`/`leistung`/`d2dmail`?** State machine progression — but with what states?
4. **Is `dbsprot.FUhrzeit` reliable enough for sub-quarter timing analysis?** (Probably yes — it's there, it's per-event.)
5. **The `FEpochtime` datetime vs. `FDatum`+`FUhrzeit` int pair** — which is authoritative? Almost certainly `FEpochtime` (MariaDB-native), but worth confirming.

These get answered with very small targeted SELECT-DISTINCT queries — a few hundred rows of metadata, fully pseudonymized, on the next RDP session.

---

## QM-Handbuch anchors this directly enables

- **§3 Nr. 5 (Informationssicherheit):** "Alle Schreibvorgänge in der Praxisverwaltungssoftware werden in der zentralen Tabelle `dbsprot` revisionssicher protokolliert (10,9 Mio Einträge per 2026-04-29). Inhaltsspeicherung als XML-Snapshot pro Schreibvorgang. Append-only-Pattern."
- **§3 Nr. 3 (Prozessorientierung):** Once Stage 2 runs, the observed-process map IS the Prozess-Dokumentation. Each Workflow-Pattern that emerges is one SOP-Eintrag.
- **§4 Schnittstellenmanagement:** The `d2dmail` + `epa*` + `kvconnectabr` + `ldtarc` tables are the data-flow boundary inventory. We can document each as "Schnittstelle nach extern" with its protocol + transport.
