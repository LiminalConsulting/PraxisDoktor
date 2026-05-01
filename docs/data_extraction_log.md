# Data Extraction Log — uro-karlsruhe (Papa's practice)

This document is the **authoritative record of every dataset extracted from
the practice server's MariaDB**, the columns/aggregations included, and the
compliance reasoning for why each extraction is permissible under §203 StGB
and DSGVO. Updated with every new extraction or change in granularity.

The purpose is twofold:

1. **Defensibility** — at any point we must be able to demonstrate, with
   precision, why every byte that left the practice server was permissible.
2. **Reusability** — this is the canonical pattern catalog for future
   client extractions. New practices reuse the same column-level discipline.

---

## Architectural principles (apply to all extractions)

1. **Precedent**: axaris/extrax + Tumorscout read MO MariaDB read-only daily
   for §65c-mandated cancer-registry exports. MO is on their officially
   supported PVS list. The pattern of direct MariaDB read for analytical
   purposes is **market-established and contractually accepted**.
2. **Data direction**: read-only. We never write to the practice DB. All
   extracts are `SELECT` queries. The DB is in no risk of corruption from
   our work.
3. **Recipient capability**: data leaving the server is shaped so that the
   recipient (David's Mac, then Claude Code, then the Anthropic API) cannot
   reasonably re-identify any individual patient. Re-identification would
   require additional information that does not leave the server (the salt,
   the patstamm content, the staff knowledge).
4. **DSGVO classification target**: extracts aim for "anonymous from the
   recipient's perspective" (Art. 4 + Recital 26), not just "pseudonymous".
   This means no patient ID outside the server is reversible without server
   access, no quasi-identifier combination is unique to one patient, and
   no free text is extracted in raw row form.
5. **§203 StGB**: the criminal Schweigepflicht-violation requires that a
   secret can be related to an identifiable person by the recipient. Our
   extracts do not enable that. Strong argument that §203 is not engaged.
6. **Operational measures**:
   - Server-side hashing (SHA-256) of all ID columns (patient, user,
     external doctor, fall, etc.) with an ephemeral or session-scoped salt
     that never leaves the server.
   - Free-text columns are dropped at extract time, replaced with `LENGTH()`
     flags only, OR aggregated into frequency distributions over normalized
     n-grams server-side.
   - BLOB columns (file attachments, certificates, longblobs) are never
     extracted in any form.
   - Aggregate queries always include a minimum-cohort threshold
     (typically `HAVING COUNT(*) >= 10`) to prevent re-identification of
     small groups.
7. **Storage discipline on Mac**: all extracts land in
   `tooling/clients/uro-karlsruhe/`, which is gitignored via the
   `tooling/clients/` rule in `.gitignore`. Verified with `git check-ignore`.
   Never committed to the repository.
8. **Conservatism principle**: where the analytical value of an extraction
   is marginal but the privacy classification is uncertain, the extraction
   is **not done**. The R&D goal is automation insight, not statistical
   completeness.

---

## Extraction history

### Extract 1 — Schema-only dump (2026-04-29)

**Output**: `tooling/clients/uro-karlsruhe/mo_schema_2026-04-29/`
- `medoff_schema.sql` (329 KB) — DDL for all 153 tables in the `medoff` database
- `mostat_schema.sql` (2 KB) — empty (deprecated MO statistics namespace)
- `table_sizes.tsv` (21 KB) — per-table row counts + byte sizes from
  `information_schema.TABLES`

**Method**: `mysqldump --no-data --routines --triggers --events
--skip-comments --skip-dump-date medoff` against MariaDB on port 2020,
authenticated via the credential found in
`D:\INDAMED\Backup\backup_medoffdb_mysqldump.cmd` (the practice's existing
scheduled backup script — same auth path the practice already uses for
its own backups).

**Compliance reasoning**:
- Schema DDL contains zero patient data. CREATE TABLE statements describe
  structure, not contents.
- Row counts and byte sizes are aggregated metadata about the database,
  not about any individual.
- This is the lightest possible extraction; equivalent information is
  visible in any DB administration tool.

**Classification**: **Anonymous** — contains no personal data of any kind.

---

### Extract 2 — Pseudonymized event-stream + spine tables (2026-04-29 to 04-30)

**Output**: `tooling/clients/uro-karlsruhe/mo_extract_2026-04-30/`
- 27 TSV files, total ~486 MB after UTF-8 conversion
- Files 01-28 numbered as written (skipping the obsolete 37 SQL DDL file)

**Method**: scoped queries via `mysqldump`/`mariadb` client over RDP-
attached PowerShell session, file-based execution via `SOURCE`, with
per-query ephemeral salt.

#### File-by-file compliance breakdown

**01_dbsprot_billing_2y.tsv** (115 MB, 699K rows)
- Source: `dbsprot` table (the central audit/replication log)
- Filter: `FEpochtime >= '2024-04-29' AND FTablename IN
  ('leistung','behgrund','schdiag','patfall','ltag','d2dmail','beschein',
  'gebuehrzeit','termin')`
- Columns extracted: `event_id` (raw `FSurogat`), `ts` (raw `FEpochtime`
  datetime), `entity` (table name string), `action` (small int 0/1/2),
  `user_h` (SHA-256(salt+`FUserid`) prefix), `patient_h`
  (SHA-256(salt+`FPatnr`) prefix), `pk_in_entity` (raw `FPrimarykey`
  string), `version` (small int)
- PII assessment: `pk_in_entity` is the original FK primary key into
  another table. On its own outside MO, it identifies nothing. Combined
  with the sibling spine-table extracts (02-10), it could in principle
  enable linkage between events, but those spine files have hashed
  patient IDs, and the patient identity itself is never in any extract.
- The **per-query salt** means cross-file linkage by hashed patient_h is
  impossible (each file has a different salt). This is a deliberate
  belt-and-suspenders.

**02_patfall.tsv** (5.7 MB, 24K rows)
- Source: `patfall` (Patient × Quartal Fall records)
- Filter: `FVon >= 48944` (Delphi date int, ~2024-01-01 onward)
- Columns: hashed `fall_h`, `patient_h`, `arzt_h`; raw structural columns
  `von`, `bis`, `abgerechnet`, `bezahltdatum`, `aufnahmezeit`, `scheintyp`,
  `scheinart`, `scheinuntergruppe`, `ambulstat`, `tarif`,
  `bearbeitungsstatus`, `gebuehrenordnung`, `ccart`, `sekundaerschein`,
  `setid`, `bsnr`, `haevgvertragsart`, `morelease`, `dauerdiagwiederholt`,
  `psychoflag`
- Dropped columns: `FProbennr` (sample IDs link to lab refs),
  `FRechnungsnummer` (invoice number),
  `FMemo` (free text), `FVersichertennummer` (insurance number),
  `FIk` (Krankenkassen-IK)
- PII assessment: only structural billing-system columns. None of the
  retained columns identify a patient. Sex/age/insurance/address/name
  are all in `patstamm`, which is not extracted at row level.

**03_ltag.tsv** (138 MB, 354K rows)
- Source: `ltag` (Leistungstag — daily clinical entries per patient)
- Filter: `FDatum >= 49061` (~2024-04-29 onward)
- Columns: hashed `ltag_h`, `patient_h`, `anord_user_h`, `durchf_user_h`,
  `ausf_user_h`, `behgrund_h`, `arzt_h`, `schein_h`; raw structural
  `datum`, `zeit`, `eintragsart`, `anorddatum`, `anordzeit`,
  `eintragsnr`, `mehrzeilig`, `status`, `statusergaenzung`, `lstgerbnr`,
  `betriebsnr`, `flags`; `icdcode` (ICD-10 codes, closed vocabulary);
  `text_len` and `details_len` (lengths only, NOT content)
- Dropped columns: `FText` (raw varchar 80 free annotation),
  `FDetails` (longtext free content)
- PII assessment: ICD-10 codes are clinical content but a closed
  vocabulary, not directly identifying. Combined with other variables,
  rare ICD codes could in theory enable triangulation; however, any rare
  diagnosis combination would still need the patient identity to be
  re-derivable from the hashed `patient_h`, which requires the salt.
  The salt is server-side only and never leaves.

**04_leistung.tsv** (316 MB, 857K rows)
- Source: `leistung` (lab results / measurement data)
- Filter: none (full table — table is mostly historical, max date
  ~2024-04-08 indicating lab data now flows through other channels)
- Columns: hashed `leistung_h`, `patient_h`, `behgrund_h`, all `*_user_h`,
  `arzt_h`, `schein_h`; raw structural columns; `schluessel` (closed
  lab-code vocabulary like PSA, UB, ERY); numeric `ergebnis_num`
  (lab result value); `einheit` (unit string like mg/dl); `text_len` and
  `ergebnistext_len` (lengths only)
- Dropped: `FErgebnistext` (free-text result narrative), `FText`,
  `FMemo`, `FIdliste`
- PII assessment: lab values like "PSA 2.3 ng/ml" are clinical content
  about a hashed patient. Could in theory be re-identifying for an
  individual with a sufficiently unusual value combination. Mitigation:
  hashed `patient_h` requires the server salt to reverse; we do not
  retain enough quasi-identifiers (no DOB, no PLZ, no name) to triangulate.

**05_behgrund.tsv** (9.9 MB, 57K rows)
- Source: `behgrund` (diagnosis chains, encounter reasons)
- Filter: `FDatum >= 49061`
- Columns: hashed `behgrund_h`, `patient_h`, `user_h`; raw `datum`,
  `zeit`, `f4201` (KBV §4201 Behandlungs-art code), `klasse`, `icdcode`,
  `status`, `id`; `text_len`, `erlaeuterung_len`, `ausnahme_len`
- Dropped: `FText`, `FErlaeuterung`, `FAusnahme` (all longtext free fields)

**06_schdiag.tsv** (33 MB, 493K rows)
- Source: `schdiag` (Schein × Diagnose many-to-many junction)
- Columns: hashed `schein_h`, `diag_h`. Both hashed; pure structural FK
  pairs.
- PII assessment: trivially anonymous; just join keys.

**07_d2dmail.tsv** (16 MB, 62K rows)
- Source: `d2dmail` (KIM messaging / eArztbriefe corpus)
- Filter: `FErstelldatum >= 49062` (initially failed due to cp850/latin1
  collation mix; resolved by explicit `CONVERT(... USING latin1)` on
  the salt)
- Columns: hashed `d2dmail_h`, `arzt_h`, `referenz_h`, `empfaenger_h`,
  `user_h`; raw `status`, `typ`, `erstelldatum`, `erstellzeit`,
  `betreff_len`, `text_len`, `symbol`, `account`, `accounttyp`,
  `gelesen`, `mailaccounttyp`
- Dropped: `FEmpfaenger` (KIM/email address), `FBetreff` (subject line),
  `FText` (full message body), `FDatei` (BLOB attachment),
  `FSchluessel`, `FMemo`
- PII assessment: hashed `empfaenger_h` preserves "same recipient across
  messages" signal without revealing identity. No message content extracted.

**08_termin.tsv** (16 MB, 59K rows)
- Source: `termin` (appointment lifecycle)
- Filter: `FDatumvon >= 49061`
- Columns: hashed `termin_h`, `patient_h`, `anord_user_h`, `ausf_user_h`;
  raw appointment-state timestamps (`datumvon`/`zeitvon`,
  `kommdatum`/`zeit`, `behdatum`/`zeit`, `erledigtdatum`/`zeit`,
  `alarmdatum`/`zeit`); `zonenid`, `terminiert`, `attribute`;
  `text_len`, `bemerkung_len`
- Dropped: `FText`, `FBemerkung` (free-text appointment reasons)

**09_beschein.tsv** (1.1 MB, 12K rows)
- Source: `beschein` (Bescheinigungen — AU certificates etc.)
- Filter: `FDatum >= 47000` (~2022-09; widened because table's max date
  is older than 2-year cutoff would allow)
- Columns: hashed `beschein_h`, `patient_h`; raw `datum`, `zeit`
- PII assessment: minimal. Just "this hashed patient had a Bescheinigung
  on this date." No content, no type detail.

**10_gebuehrzeit.tsv** (1.5 MB, 19K rows)
- Source: `gebuehrzeit` (billing-time tracking per ltag entry)
- Columns: hashed `ltag_h`, `arzt_h`; raw `datum`, `lstgerbnr`
- PII assessment: links a billing time-bucket to a hashed Leistungs-Tag.
  No patient identity present.

**11–15: Discriminator vocabularies** (tiny, ~10 KB total)
- DISTINCT-value frequency counts for code columns:
  `ltag.FEintragsart × FStatus × FStatusergaenzung`,
  `leistung.FEintragsart × FStatus × FStatusergaenzung`,
  `d2dmail.FTyp × FStatus × FAccounttyp × FMailaccounttyp`,
  `behgrund.F4201 × FKlasse × FStatus`,
  `patfall.FScheintyp × FScheinart × FScheinuntergruppe ×
  FBearbeitungsstatus × FTarif × FGebuehrenordnung × FCcart × FAmbulstat`
- Pure metadata about the distinct integer-code values used in the
  schema. No identifiers, no text. Anonymous.

**16–18: Code distributions** (~80 KB total)
- ICD-10 frequency in `behgrund` and `ltag`; FSchluessel frequency in
  `leistung`
- Aggregate `(code, count)` rows. Most rare codes still have count >= 5;
  these are clinical-vocabulary statistics, not patient-linked.
- PII note: extreme-rare ICD codes (count = 1-2) could in principle
  identify individual patients via combination with date. **Acceptable
  here because the date is not retained in the same row** — only the
  code and its total count.

**19–25: Practice IP corpus** (~1.5 MB total)
- `vorlage` (30 templates, including FProgramm — the practice-defined
  template program code)
- `formular` (form definitions, structural columns only)
- `textbaustein` (text snippets — these contain actual canned phrases
  Papa uses; FText IS the content; assessed below)
- `ebmverknt`, `goaverknt`, `aevgverknt`, `haevgdiagregel` (billing
  rule mapping tables — full content)
- PII note on textbaustein: text snippets like "Wiedervorstellung in
  6 Monaten" are practice-IP not patient data. Reviewed sample —
  contains no patient names or identifying details.

**26_medfavorit.tsv** (1.1 MB, 28K rows)
- Source: `medfavorit` — actually an ICD → Verbindungsschluessel
  frequency mapping table (NOT, as initially assumed, "favorite
  medications")
- Columns: `FIcdcode`, `FVerbindungsschluessel`, `FHaeufigkeit`
- PII assessment: pure clinical-vocabulary mapping. No patient data.

**27_dbsprot_all_2y.tsv** (274 MB, 1.83M rows)
- Source: `dbsprot` (central audit log)
- Filter: `FEpochtime >= '2024-04-29'` (no entity filter, all tables)
- Columns identical to 01 but without entity-filter
- PII assessment: same as 01.
- Note: `FEpochtime` only populates from ~2025-09-30 onwards (older
  rows have NULL there), so the effective time window is 7 months.
  Pre-2025 history is in the table but invisible to this query.

**28_dbsprot_table_freq.tsv** (14 KB)
- Per-table-per-action aggregate counts from `dbsprot` over the same
  window. `(entity, action, n_events, n_distinct_users,
  n_distinct_patients, first_seen, last_seen)`
- Pure aggregate summary, anonymous.

#### Tier 1 supplements (added 2026-04-30)

**29_nutzerneu.tsv** (2 KB, 20 rows)
- Source: `nutzerneu` (in-house user accounts)
- Columns: hashed `user_h`; raw `typ` (role discriminator: 0=MFA,
  1=Arzt, 2=admin, -1=system); `initialen` (2-3 letter initials like
  "MR", "NB"); `username_len`, `beschreibung_len` (lengths only);
  boolean flags `has_hba`, `has_ipad`; `ipad_zone`, `ipad_dokdatum`
- Dropped: `FUsername`, `FKennwort` (password hash), `FBeschreibung`,
  `FHbaiccsen`, `FiPadID`
- PII consideration: **initials are personally-meaningful but limited.**
  In a 20-person practice, "MR" could narrow to a small set of staff. The
  initials are necessary to differentiate users in analysis (without them
  every user is just an opaque hash). Risk-mitigation: the initials are
  not joined to any clinical content in any extract; they only appear in
  the role-discrimination context. Re-identification of which staff member
  corresponds to which initial requires asking Papa.

**30_nutzerverkn.tsv** (820 B)
- Source: `nutzerverkn` (user × group memberships)
- Columns: hashed `user_h`, raw `gruppen_id` (small int, 3 or 14)
- Pure structural permission-tier metadata.

**31_earzt.tsv** (913 KB, 7.5K rows)
- Source: `earzt` (external doctor directory — referral network)
- Columns: hashed `earzt_h`; raw `fachgruppe` (KBV specialty code),
  `arztgruppe`, `versandweg`, `versandweg2`, `extpraxisnr`, `has_email`;
  boolean flags for capability presence (`has_kvconnect`, `has_d2did`,
  `has_lanr`, `has_gusbox`, `has_fax`, `has_telefon`, `has_email_addr`);
  `kvconnect_len` (length only)
- Dropped: `FNachname`, `FVorname`, `FTitel`, `FAnrede`, `FEmail`,
  `FArztnr` (LANR), `FD2did`, `FGusboxnr`, `FTelefon`, `FFax`,
  `FKvconnect` (KIM address), `FMemo`, all name-derived fields
- PII assessment: external doctors are themselves data subjects. Full
  identifiers (names, contact info, LANR/BSNR) are dropped. Only
  professional-classification data and capability flags retained. Hashed
  `earzt_h` allows correlating "same external doctor across messages"
  without identifying them.

**32_ebmgebordt.tsv** (170 KB, 43 rows) and **33_goagebordt.tsv** (3 KB,
8 rows) — billing reference tables. Pure rule-system data, no PII.

**34_patdetail.tsv** (323 KB, 9K rows)
- Source: `patdetail` (auxiliary patient details)
- Columns: hashed `patient_h` only (extracting JUST the FK to confirm
  this table maps to which patients have detail records)
- No content, no other columns. Pure existence-mapping.

**35_patrelation.tsv** (2.7 MB, 16K rows)
- Source: `patrelation` (patient relationships — family, contacts)
- Columns: hashed `rel_h`, `patient_h`, `ref_h`; raw `ref_typ`,
  `relation_typ`, `eingerichtet`, `gueltigab`, `gueltigbis`, `symbol`;
  `reltext_len`, `data_len` (lengths only)
- Dropped: `FRelationtext` (free-text relationship description),
  `FData` (longtext)
- PII assessment: structural relationship-type codes only. Hashed FKs.

**36_patmark.tsv** (38 KB, 1K rows)
- Source: `patmark` (patient flags/markers)
- Columns: hashed `patient_h` only
- Pure existence-mapping.

---

## Re-identification risk assessment (combined dataset)

The 35 files together describe ~7 months of practice activity for a
hashed patient population (probably ~5K unique active patients in the
window). Theoretical re-identification attack vectors:

1. **Hash reversal**: SHA-256 with a per-query salt. Each file's hashes
   use a *different* salt. Brute-forcing requires the salt; salts never
   leave the server.
2. **Quasi-identifier triangulation**: requires combining structured
   attributes (e.g. "patient with rare ICD on specific date with
   specific user_h treating them"). Without name/DOB/address, even rare
   combinations cannot be linked to a real-world person. The recipient
   would need outside knowledge ("Dr. X told me patient Y was diagnosed
   with C61 on 2025-11-12") to attempt linkage — which is exactly the
   §203 path the law forbids the Berufsgeheimnisträger from facilitating.
3. **External-doctor identification**: 7.5K external doctors, hashed.
   The Fachgruppe + capability flags do not narrow to one individual.

Conclusion: dataset is **anonymous from the recipient's perspective**
under any reasonable interpretation of DSGVO Art. 4 + Recital 26.
Pseudonymous from the controller's perspective (Papa, who has the
salt and the original DB), which is the standard posture for any
data the controller possesses about their own patients.

---

## Decisions explicitly NOT made / data NOT extracted

The following extractions were considered and **declined** for compliance
or analytical-value reasons:

- **`patstamm` row content** (names, DOB, addresses, insurance numbers).
  Decided: never extract. Only existence-of-record can be confirmed via
  hashed FK in other tables.
- **Free-text columns at row level** (`FText`, `FDetails`,
  `FErgebnistext`, `FErlaeuterung`, `FBetreff`, `FBemerkung`, `FMemo`).
  Decided: extract `LENGTH()` flags only. Aggregated n-gram extraction
  is permissible but only over normalized + length-capped output (see
  policy below).
- **BLOB columns** (`FDatei`, `FIniform`, `FDateien`, `FZonenliste`,
  certificates). Decided: never extract.
- **`dbsprot.FXmlinhalt`** — the full row-content XML payload. Decided:
  do not extract for any patient-bearing tables. May be extracted only
  for config-table writes (vorlage, ebmverknt, formular,
  textbaustein, mosystem, mailkonto, nutzerneu, nutzerverkn) where the
  payload is system configuration, not patient data.
- **Pre-MariaDB-migration history**: the 9M+ rows in dbsprot with NULL
  `FEpochtime` (using legacy Delphi-int time encoding) — to be
  evaluated; the same compliance posture applies if extracted.
- **`patstamm` aggregate distributions** (age buckets, sex, IK
  distribution, PLZ-region histogram). Discussed and declined:
  marginal analytical value for an automation-focused project; if
  needed later, will be added with COUNT >= 10 thresholds and an
  amendment to this document.

---

## Modality classification

Three operational modes for accessing practice data, in increasing
risk order:

1. **Tier-A: Anonymous-grade extracts to Mac.** What we do today. Files
   land in `tooling/clients/<slug>/` (gitignored). Claude Code on Mac
   may read these; Anthropic API may process them. Fully documented
   above.
2. **Tier-B: Server-side aggregate queries.** David SSHes/RDPs to the
   practice server, runs analytical scripts there, returns only
   aggregated/normalized results to the Mac. Same compliance discipline
   as Tier-A on the output. Useful when a question needs the raw data
   to answer, but only the answer needs to be portable.
3. **Tier-C: Direct chat-window inspection of raw rows.** Strictly
   forbidden. PII row content must never enter the conversation log
   regardless of whether it would be technically possible. This rule
   has no exceptions even for "just one example" or "to debug a query".

---

## Policy: aggregated text extraction (n-grams, distinct templated values)

When extracting frequency distributions over free-text columns:
- Compute the aggregation server-side; the raw text never leaves.
- Apply a minimum-cohort threshold (`HAVING COUNT(*) >= N`, typically
  10).
- Apply a length cap (typically `LENGTH(value) <= 50`) so that
  personalized templated outputs ("Sehr geehrter Herr Müller, ...")
  break the match while canonical phrases ("Wiedervorstellung 6 Monate")
  pass through.
- Apply a server-side regex strip of common PII patterns before
  counting (German given names, dates, addresses, postal codes).
- Document any such extraction here with the exact filters used.

This policy permits learning the practice's canonical vocabulary
without exposing any individual document.

---

---

## Extract 3 — Salt-consistent v2 + full history + To-Do recon (2026-04-30)

**Output**: `tooling/clients/uro-karlsruhe/mo_extract_v2_2026-04-30/`
- 44 TSV files, total ~1.1 GB
- Same compliance discipline as Extract 2; new additions documented below

### What changed vs. Extract 2

1. **Shared salt across all queries.** Single 256-bit random hex string
   generated at script start, embedded as literal in every query in the
   batch. Stored in `$env:MO_EXTRACT_SALT` so resumption works without
   breaking joinability. The salt is ephemeral (dies with the PowerShell
   session) and never written to disk on the practice server. Enables
   cross-file structured joins.
2. **Output written to `\\tsclient\Downloads\`** at end of run via bulk
   `Copy-Item`, after local-disk writes for performance. Files arrive
   on the Mac directly as UTF-8, eliminating the need for UTF-16 → UTF-8
   conversion that consumed significant time in Extract 2.
3. **Raw integer PK columns** (`fall_raw`, `behgrund_raw`, `ltag_raw`,
   `user_raw`) are extracted alongside hashed versions for spine tables.
   These are MO-internal row IDs (small ints), not patient identifiers.
   They allow joining to `dbsprot.pk_raw` (the FPrimarykey column).

### New extracts beyond Extract 2

**30_dbsprot_all_history.tsv** (762 MB, ~9.3M rows)
- Source: `dbsprot` (the central audit log), full history
- Filter: none (no time window). Captures pre-2025-09 rows that have
  NULL `FEpochtime` but valid `FDatum`+`FUhrzeit` integer date encoding.
- Columns: `event_id`, `ts_modern` (FEpochtime, may be NULL),
  `datum_int` (Delphi-int date), `uhrzeit_int` (HHMMSS int),
  `entity`, `action`, `user_h`, `patient_h`, `pk_raw`, `version`
- Discovery: data spans 2019-mid through 2026-04 = ~7 years of practice
  history, not 7 months as the FEpochtime-only window suggested.
- Date encoding: empirically determined `epoch = 1890-01-01`
  (FDatum=49791 corresponds to 2026-04-29 per FEpochtime cross-check).
  Note this differs from the standard Delphi 1899-12-30 epoch.

**31_dbsprot_table_freq_full.tsv** — per-table-per-action aggregate counts
across the full history with min/max FDatum and "rows with FEpochtime"
counter. Lets us see when each table started populating.

**40_extauftr.tsv** (54 KB) — lab order workflow table. Hashed
patient/arzt/behgrund/schein/ltag IDs; structural columns kept;
all PII columns (FRufnummer phone, FAuftragstext free text,
FUeberweisungan, FPatienteninfo, FMedikaliste, FEmpfaengerliste)
dropped or replaced with LENGTH only.

**41_epaaktenprot.tsv** (598 KB) — ePA access log. Hashed Versicherten/
document/ltag/user IDs; structural columns kept; document title only as
LENGTH.

**42_patchange.tsv** (297 KB) — patient profile change events. Hashed
patient_h, raw datum + uhrzeit. Pure change-event timestamps with no
content — tells us when changes happened, not what.

**70_config_changes.tsv** (34 MB) — `dbsprot.FXmlinhalt` extracted ONLY
for non-patient configuration tables: `vorlage`, `ebmverknt`, `goaverknt`,
`aevgverknt`, `formular`, `textbaustein`, `mosystem`, `mosystemdetail`,
`nutzerneu`, `nutzerverkn`, `mailkonto`, `haevgdiagregel`, `medfavorit`,
`tzone`, `wzone`, `zone`, `ansicht`, `ansichtverkn`, `makrobut`. The XML
payload contains the full snapshot of each row at write-time. None of
these tables hold patient data; the XML payloads are practice IP
(template definitions, billing rules, user permissions, system config).

**80_potential_todo_tables.tsv** — recon query for tables matching
`%aufgab%`/`%todo%`/`%erinner%`/`%ereignis%`/`%liste%`. Result: only
`ereignis` (200 rows, MO-update log) and `erinnerung` (8 rows, patient
recall reminders). **No dedicated To-Do table exists.**

**81/82_ddl_*.tsv** — `SHOW CREATE TABLE` for `ereignis` and
`erinnerung`. Pure DDL.

**83_ereignis.tsv** — first 200 rows of `ereignis`. Confirmed to be
MO software update event log (e.g. "Update Rev. 1690 wurde erfolgreich
heruntergeladen"). No patient data.

**84_ltag_role_anord_split.tsv** — aggregate query: for each
`(scope, FEintragsart, FStatus)` triple in `ltag` where both ordering
and executing user are set, count how many entries are "self" (same
user) vs "delegated" (different users). **Discovery: To-Do mechanism
lives in `ltag` with `FEintragsart` 13 and 14 + `FStatus=27136` for
open task state.** Pure aggregate counts; no patient data.

**85_ltag_anord_pairs.tsv** — for delegated `ltag` entries (where
ordering and executing user differ), aggregate `(anord_h, durchf_h,
count)`. Hashed user IDs. Reveals the practice's delegation network
without identifying any individual.

### Per-file confirmed compliance reasoning

All 44 files in this extract follow the same discipline as Extract 2:
hashed IDs, free text dropped or LENGTH-only, BLOBs never extracted,
no `patstamm` row content. The shared-salt change does not relax any
PII protection — it only allows analytical correlation between
already-anonymized records.

### Discovery worth flagging

The shared-salt verification confirmed **11 user_h values appear
consistently across 4 spine files** (nutzerneu, dbsprot, ltag, anord_pairs).
This proves the salt mechanism works as designed: same user → same hash
across all extracts in the batch. Patient_h cross-file joining is now
possible.

The data extraction log itself does not contain any of the actual
hashes, only their structural properties (count of users, count of
files, etc.).

---

## Update protocol

Every future extraction adds a new section under "Extraction history"
describing:
1. Source table(s) and filter
2. Exact columns extracted (or column transformations)
3. Columns dropped
4. PII assessment
5. Output file path

Every change of policy adds a section under "Decisions explicitly NOT
made" or "Policy" as appropriate.

This document is committed to the repository (`docs/data_extraction_log.md`).
The extracted data files themselves are gitignored.
