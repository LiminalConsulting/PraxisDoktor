# PraxisDoktor — Patientenaufnahme-Assistent

Automatisierte Patientenaufnahme für die urologische Praxis Dr. Rug.

Nimmt das Erstgespräch auf, transkribiert es mit Whisper (lokal, Deutsch), liest den Anamnesebogen per OCR ein und extrahiert mit einem lokalen LLM (Ollama) die Patientenstammdaten — bereit zum Einfügen in MediOffice.

## Features

- **Aufnahme im Browser** — kein extra Mikrofon-Setup
- **Whisper (faster-whisper)** — Deutsch, urologisches Vokabular, läuft auf CPU
- **OCR** — Anamnesebogen per Drag & Drop einlesen (easyocr, kein Tesseract nötig)
- **Lokales LLM** — Ollama extrahiert strukturierte Felder, kein Cloud-Zugriff
- **Kopierschaltflächen** — ein Klick je Feld, dann in MediOffice einfügen
- **Sitzungsverlauf** — SQLite, alle Maschinen im LAN sehen dieselben Daten
- **Vokabular-Editor** — Begriffe im Browser hinzufügen/entfernen

## Schnellstart (Entwicklung)

```bash
# Abhängigkeiten installieren (uv erforderlich)
uv sync

# Ollama-Modell laden (einmalig)
ollama pull llama3.1:8b

# Server starten
uv run python main.py
# → http://localhost:8080
```

## Produktion (Windows)

Siehe `ANLEITUNG.txt` im Release-ZIP.

Release erstellen:
```bash
git tag v1.0.0
git push origin v1.0.0
```
GitHub Actions baut automatisch `PraxisDoktor-v1.0.0.zip` mit EXE + Ollama-Installer.

## Architektur

```
main.py          FastAPI — API-Endpunkte, Hintergrundaufgaben, SSE
transcribe.py    faster-whisper (medium, CPU, int8)
ocr.py           easyocr (Deutsch, CPU)
llm.py           Ollama-Client, Extraktions-Prompt
db.py            SQLite — Sitzungen + Vokabular
vocab.py         Vokabular-Verwaltung
static/          HTML/CSS/JS Frontend
```

## Datenschutz

- Alle Verarbeitung erfolgt lokal (kein Cloud-Zugriff)
- Audiodateien bleiben auf dem Server
- SQLite-Datenbank liegt neben der EXE

## Deployment Strategy

The product works technically. The open question is how it enters a running practice without disrupting it. The general shape: **parallel augmentation first, autonomous replacement never before earned.**

### Phase 1 — lowest-hanging asynchronous fruit

Start with what has no synchronous coupling to the live patient flow. The clearest target: **Rechnungsprüfung** — Papa currently spends ~3 hours of manual copy/paste to verify outgoing invoices against records. The tool produces what *it* thinks the verified output should be; Papa just compares. No database write, no operational surface area. Pure predicted-vs-actual signal.

This phase does two things: (1) delivers real time back to Papa immediately, (2) generates a stream of labelled data about how well the tool tracks what Papa actually does.

### Phase 2 — co-pilot in the live loop

Patientenaufnahme and other live workflows get a co-pilot window next to the existing workflow. The extractor produces its best guess at each field. Two buttons per field:

- **Korrekt & kopieren** — validates that the extraction matches, copies to clipboard. The copy *is* the approval signal — no separate feedback UI.
- **Falsch** — flags the field as wrong and falls back to manual entry.

Design principle: *infer feedback from the natural workflow rather than asking for it.* Every time an employee would normally move data, the tool is either helpful (approved + copied) or stays out of the way (fallback). The worst case is their existing workflow.

### Phase 3 — autonomy once earned

Only when per-process accuracy crosses and sustains a defined threshold (target: 100% for database writes — automation-introduced errors are unacceptable), the copy-paste seam is removed and the tool writes directly. The **same observability UI remains** — employees still see exactly what happened and can intervene, but no longer have to be in the loop for correctness.

Parallel thread: the coherence-check workflow (one employee currently audits patient files for inconsistencies) is itself automatable. Since human error exists on both sides, cross-auditing — the tool catches human mistakes, humans catch tool mistakes — closes the quality gap faster than either alone.

### In-person vs. remote work

- **Build phase** — remote, from data already collected in March 2026 at the practice.
- **Papa-feedback phase** — evenings at home during the Karlsruhe trip. Papa is saturated during practice hours; home is where he has bandwidth to actually use the tool and say what's off.
- **Deployment at the practice** — one visit, ideally weekend or closed hours, to verify the tool is reachable from every relevant computer in the LAN and walk the team through the co-pilot pattern.
- **Post-deployment refinement** — fully remote. Once the team is familiar with the observability UI, written feedback in the team chat + behavior signals are sufficient.

### Why this never replaces the existing UI outright

The current practice software is bad, but it's running a real business. The co-pilot pattern is the only way to honor the Fallback-First principle at deployment time, not just at design time: if the tool vanishes, the old flow still works, because the old flow is still what's running. What the tool adds is a parallel stream of either-accepted-or-ignored suggestions. No risk until accuracy earns it.
