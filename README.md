# PraxisDoktor

Digitale Zentrale für die urologische Praxis Dr. Rug & Dr. Bruckschen.

Eine identitäts-bewusste Anwendung, die jeden Praxisprozess unter einer einheitlichen Grammatik abbildet: Anmeldung → personalisiertes Dashboard → Werkzeug pro Prozess → angeheftete Chats — alles lokal in der Praxis, kein Cloud-Zugriff auf Patientendaten.

Das **Patientenaufnahme**-Werkzeug ist die erste lebendige Implementierung; alle anderen Prozesse (Rechnungsprüfung, Termin-Übersicht, Materialverwaltung, etc.) existieren als Platzhalter und werden iterativ ausgebaut.

## Architektur

Zwei Verzeichnisse, eine Anwendung:

```
docs/        Konzeptuelle Grundlage — Ontologie, Rollen, Stack, Bauplan
server/      FastAPI + Postgres + ML-Pipeline (Whisper / OCR / Ollama)
web/         SvelteKit + Tailwind PWA (Login, Dashboard, Werkzeuge, Chat, Admin)
```

Detaillierte Begründung jeder Wahl: [`docs/stack.md`](docs/stack.md)
Grammatik aller Prozesse: [`docs/process_ontology.md`](docs/process_ontology.md)
Rollen × Prozess-Matrix: [`docs/roles_and_processes.md`](docs/roles_and_processes.md)
Bau-Reihenfolge: [`docs/skeleton_plan.md`](docs/skeleton_plan.md)

## Schnellstart (lokale Entwicklung)

Voraussetzungen: macOS oder Linux mit Postgres 16, Python 3.11+, Bun, Ollama mit `llama3.1:8b`.

```bash
# 1. Postgres-Datenbank
createdb praxisdoktor_dev

# 2. Backend
cd server
uv sync
uv run alembic upgrade head
uv run python seed.py        # legt Rollen, Test-Benutzer, Prozesse an
uv run uvicorn app.main:app --host 127.0.0.1 --port 8080

# 3. Frontend (in einem zweiten Terminal)
cd web
bun install
bun run dev                  # → http://localhost:5173
```

Test-Zugänge (alle Passwörter `praxis123`):

| Benutzer | Rolle(n) |
|---|---|
| `admin` | Praxisinhaber |
| `dr_inhaber` | Praxisinhaber + Arzt |
| `dr_angestellt` | Arzt |
| `mfa_anna` | Empfang |
| `mfa_bea` | Behandlung |
| `mfa_clara` | Abrechnung |
| `manager_dora` | Praxismanager + Abrechnung |

## Datenschutz

- Alle Patientendaten verbleiben auf der Praxis-Hardware (LAN-only Zugriff)
- LLM-Inferenz lokal via Ollama, kein Cloud-Aufruf für PII
- Postgres-Datenbank lokal; Audio-Dateien lokal im `audio/`-Verzeichnis
- Dr. Rug erreicht das System auch von außen via vorhandener Praxis-VPN
- Mitarbeiterinnen sehen die Anwendung ausschließlich aus dem Praxis-WLAN

## Produktion (Windows)

Aktuell als Entwicklungs-Skelett auf macOS gebaut. Produktiv-Setup auf dem Praxis-Server (NSSM-gemanagte Dienste für FastAPI + Postgres + Ollama + Caddy, Cloudflare Tunnel mit split-horizon DNS für `app.uro-karlsruhe.de`) folgt im nächsten Schritt vor Ort.

Das Legacy-`v1.0.x`-Standalone-EXE-Setup (siehe `ANLEITUNG.txt`) bleibt vorerst als Fallback verfügbar.

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
