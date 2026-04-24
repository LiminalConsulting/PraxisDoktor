# Stack

The locked technology choices for PraxisDoktor, with the reasoning behind each. Future-you (and any subagent reading this repo) should be able to defend or revise any choice from these notes alone, without re-deriving it from scratch.

## Principles That Shaped This Stack

1. **One vendor for production hosting** — Cloudflare for everything network-edge (when we move beyond LAN).
2. **Minimum tool count** — every additional library is a maintenance and security surface. Add one only if removing it would mean reimplementing something genuinely hard (cryptography, TLS, real-time, ML).
3. **Sovereignty bias** — when two libraries are equivalent, pick the one we own the source of (shadcn pattern: copy-into-repo, not import-from-CDN).
4. **Professional-grade, not bleeding-edge** — choose the stack a serious independent shop would pick today, not the most novel option.
5. **Three languages floor** — Python (server), TypeScript (frontend), SQL (database). Anything more requires explicit justification.
6. **No bloatware over solvable gaps** — given AI leverage, writing 200 lines of well-understood code is cheaper than absorbing a 50k-LOC framework whose abstractions we use 5% of.

## Layer-by-Layer

### Server language: Python
Already in place. faster-whisper, easyocr, speechbrain, Ollama all native here. Switching would be self-harm with no upside.

### Web framework: FastAPI
Already in place. Async, OpenAPI built-in, dependency-injection model maps cleanly to "requires login" / "requires role" decorators. Industry standard for new Python web services.

### Database (production): Postgres 16
Replaces the SQLite that powered the v1 patient-intake tool. Reasons:

- Multi-process, multi-user, real concurrency
- `LISTEN / NOTIFY` covers the small amount of pub/sub we need without standing up Redis
- JSONB columns let `current_state` live as flexible JSON while transitions stay strictly typed
- Standard target across all future Liminal Consulting clients (parameterization, not rebuild)

### Database (development): Postgres 16 (Homebrew, local)
Same engine as production. Local instance via `brew install postgresql@16` running as a `brew services` background service. Database name `praxisdoktor_dev`. SQLAlchemy + Alembic point at `postgresql://localhost/praxisdoktor_dev` by default. No SQLite anywhere — dev/prod parity from day one.

### ORM + migrations: SQLAlchemy 2.0 + Alembic
The professional Python default. SQLAlchemy 2.0's typed declarative models give us static type-checking on queries; Alembic gives us reversible migrations. Migrations are non-negotiable once schema serves real users.

### Auth: roll our own with `fastapi-users` + argon2
Considered Authentik. Rejected because:

- Whole separate Django app + Redis + worker = three extra processes and three more attack surfaces
- Generic admin UI breaks the single-surface promise (employees would see a Liminal-app screen and a separate Authentik screen)
- OIDC solves a multi-app problem we don't have
- For ≤20 users, the "user management UI" is a screen Papa visits twice a year — building it ourselves is one afternoon

Implementation: `fastapi-users` provides the password hashing (argon2), session cookies, and dependency primitives. We write our own admin UI that matches the dashboard's look. Total surface ~200 lines of Python.

**MFA / WebAuthn / SSO** is on us to build if a future Tier-2 client needs it. For PraxisDoktor specifically, LAN-only access means physical presence in the practice is already a second factor.

### Frontend framework: SvelteKit + Svelte 5 (runes)
Considered React/Next, Vue/Nuxt, HTMX-only. Picked SvelteKit because:

- Smallest mental model among the serious choices — compiles to vanilla JS, no runtime overhead, fewer UI bugs
- One idiomatic answer per question (state, fetching, forms, routing) versus React's five — less decision fatigue for a sole operator
- Excellent PWA story built in
- TypeScript first-class
- The framework-size win compounds because relevant context fits in a smaller window

**Training-data concern (acknowledged):** Svelte historically had less AI training coverage than React. As of 2026 with frontier models, Svelte 5 + runes are solidly in training data. We mitigate the residual lag by committing `llms.txt` files for SvelteKit, Svelte 5, shadcn-svelte, and svelte-dnd-action into the repo, so any Claude Code session has authoritative current docs in working context.

### UI component library: shadcn-svelte + Tailwind CSS
Headless primitives (built on Bits UI) that are *copied into* our `lib/components/ui/` directory rather than imported. We own the source. Industry-standard look, professional grade, no lock-in. Tailwind for utility-first styling.

### Drag-rearrangeable cards: svelte-dnd-action
The well-maintained standard for Svelte. Handles the "drag dashboard cards to rearrange" pattern natively with sensible accessibility defaults.

### Realtime: WebSockets via FastAPI
One bidirectional channel for chat messages, dashboard activity pings, and live job status updates (transcription progress, extraction-complete signals). Replaces the v1 SSE because we need bidirectional traffic and don't want to maintain SSE *and* a separate chat path.

### Editing surface: native browser inputs
No TipTap / Lexical / CodeMirror. The patient-intake fields are short structured strings that don't need rich text. Native `<input>` and `<textarea>` provide Tier 1 (per-field) undo for free. We re-evaluate only if a process emerges that needs formatted text.

### Two-tier undo/redo
Defined in `process_ontology.md`. Implementation:

- **Tier 1**: native browser per-field history. Free, no code.
- **Tier 2**: per-process transition log in the database. Cmd-Z when no field is focused, or via an explicit ↶ button, appends an `undo` transition referencing the most recent un-retracted transition.

Feedback signals are a SQL view over Tier 2 transitions where `feeds_back = true`, automatically excluding retracted ones. One source of truth for "what did the user mean?", two consumers (UI state, feedback table).

### LLM inference
- **PII path**: Ollama on the practice server (already in place). Model: `llama3.1:8b`.
- **Non-PII path**: Anthropic API via per-process opt-in flag. Not used in PraxisDoktor's current scope (everything PraxisDoktor handles is PII), but the flag exists in the process registry for future processes that don't touch patient data.

### Speech-to-text: faster-whisper
Already in place. CPU, int8, German vocabulary. Ports as-is.

### OCR: easyocr
Already in place. Ports as-is.

### Speaker diarization: speechbrain ECAPA-TDNN + KMeans
Already in place. Voice-enrollment-based speaker identification. Ports as-is.

### Process supervisor (production, Windows): NSSM
Wraps FastAPI + Postgres + Ollama + cloudflared as Windows services. No more "leave the black cmd window open." Four NSSM-managed services on the practice box: `PraxisDoktor-Postgres`, `PraxisDoktor-Ollama`, `PraxisDoktor-App`, `PraxisDoktor-Tunnel`.

### Public website + tunnel: SvelteKit on Cloudflare Pages + Cloudflare Tunnel
Replaces both the old WordPress (`uro-karlsruhe.de`) and the third-party booking/intake widgets (TerMed, Infoskop). Lives in `public/` in this repo. Same SvelteKit + Tailwind + brand-token stack as the internal app — single source of truth for the visual language via `shared/brand.css`.

- **Public site** is statically built and deployed to **Cloudflare Pages** (free tier, edge-cached). Zero Workers in the data path. No patient data ever sees Cloudflare's compute.
- **Booking + Anamnese forms** POST to `https://app.{domain}/api/public/*` (e.g. `app.uro-karlsruhe.de`).
- **`app.{domain}`** is a Cloudflare Tunnel hostname routed through `cloudflared` running as a Windows service on the practice server. Tunnel is **outbound-only** — no port opened on the practice firewall, no public IP, no static-IP rental.
- **Auth on `/api/public/*`** is a shared friction-reducer key (`X-Public-Key` header, generated and persisted as `var/public_api_key.txt` on first server start) plus an in-process rate limit. The real security boundary is the tunnel + (optionally) Cloudflare Access in front of the public origin.
- **Drittlandtransfer status:** form submissions transit Cloudflare's network (US-incorporated). Patient data terminates on the practice server; nothing is stored at the edge. Documented in `regulatory_landscape.md` §4. The alternative if it ever becomes an issue is a tiny EU VPS running an nginx proxy + WireGuard; the architecture is portable.

### Per-client provisioning: `tooling/new-client.sh`
One Bash script using `wrangler` + `cloudflared` to create the four Cloudflare objects per client (Pages project, Tunnel, DNS routing, generated tunnel token + shared key). Idempotent. Per-client config lands in `tooling/clients/<slug>/` (gitignored). Convention is `praxisdoktor-<slug>` for both Pages project and tunnel name.

### Reverse proxy
**Removed.** No Caddy needed. The Cloudflare Tunnel handles TLS termination at the edge. Inside the LAN, FastAPI on `:8080` is reached directly (HTTP). Simpler stack, one fewer service.

## Network Posture

**LAN-only-for-everyone for internal tools**, with VPN for Papa as the staff exception. **Cloudflare Tunnel for one-way public form ingestion.** Rationale:

- All authenticated practice work happens on the LAN — staff log in only from inside the building (or Papa via VPN)
- The public website is genuinely public (it has to be — patients reach it from anywhere) and lives at the edge with no patient data
- Public form submissions (booking requests, Anamnesebogen) flow **inbound** through the Cloudflare Tunnel into the practice server's `/api/public/*` endpoints. Data terminates locally; CF is the tube, not the destination
- The internal `/api/*` (everything else) is unreachable from the public internet — the tunnel exposes only the `/api/public/*` namespace (via tunnel routing config)
- One identity stack, one origin server, no split between "chat over Cloudflare" and "patient data via VPN" inside the *internal* tool

**Topology summary:**
- `uro-karlsruhe.de` → Cloudflare Pages (public marketing site, static)
- `app.uro-karlsruhe.de` → Cloudflare Tunnel → practice server `:8080` (only `/api/public/*` exposed)
- Internal `app.uro-karlsruhe.de` (split-horizon DNS, future): same hostname resolving to LAN IP from inside the practice, for staff-side access without traversing Cloudflare. Optional, deferred until measurably useful.

## Languages We Have to Think In

- **Python** — server, ML, jobs
- **TypeScript** — frontend, type-shared interfaces with backend
- **SQL** — schema, migrations, queries (via SQLAlchemy)

That is the floor. Anything else (e.g. a build script in Bash, a YAML config) is a small auxiliary, not a "language we work in."

## Four Processes on the Production Box

1. **FastAPI** (Uvicorn) — the app server, serves the internal SvelteKit build + all APIs
2. **Postgres** — state
3. **Ollama** — local LLM
4. **cloudflared** — Cloudflare Tunnel client, exposes `/api/public/*` to the public Cloudflare Pages site (no inbound firewall hole)

All NSSM-managed (`PraxisDoktor-App`, `PraxisDoktor-Postgres`, `PraxisDoktor-Ollama`, `PraxisDoktor-Tunnel`). All on the practice Windows server, no containerization. Restart-on-failure. Auto-start on boot. The tunnel service is skipped automatically if no token is provided (single-machine offline mode).

**Removed by decision:** Authentik (auth lives inside FastAPI), Caddy (Cloudflare Tunnel terminates TLS at the edge; LAN traffic stays HTTP).

## Explicitly Rejected

- React / Next.js — too much ecosystem fatigue for a sole operator on a 10-person tool
- Redux / Zustand / Jotai — Svelte stores are the answer
- React Query / SWR — SvelteKit `load` functions are the answer
- Authentik — bloat for our user count; we own the auth UI
- Redis — Postgres `LISTEN/NOTIFY` is enough
- Celery / RQ / external job queue — FastAPI BackgroundTasks + a Postgres jobs table is enough at this scale
- Docker / Docker Compose / Kubernetes — five services on one Windows box, NSSM is the right tool
- Microservices — one Python process serves the entire app, one repo, one deploy
- TipTap / Lexical / CodeMirror — no rich text need
- Resend / SendGrid / external SMTP — Cloudflare Email Routing when we get there
- Separate "feedback portal" — feedback is a view over the transition log
- Caddy — Cloudflare Tunnel handles edge TLS, LAN traffic is plain HTTP
- Doctolib / TerMed / Infoskop / external booking & intake — replaced by the public site → tunnel → `/api/public/*` flow
- Cloudflare Workers (in the practice path) — patient data must stay on-prem; Workers are a track-B primitive (BeatNonstop, festivals, non-sensitive clients)

## When to Revisit Each Decision

- **Roll-our-own auth → Authentik**: switch only if we need MFA across a Tier-3 client and reimplementing it ourselves becomes obviously slower than adopting Authentik.
- **No TipTap → TipTap**: switch when a process genuinely needs formatted notes (clinical free-text notes might trigger this; the patient-intake fields do not).
- **No Redis → Redis**: switch only if we hit Postgres LISTEN/NOTIFY scale limits, which we won't at this user count.
- **Native browser inputs → controlled-component editor library**: same trigger as TipTap.

If a future maintainer is reading this and considering a swap, the answer is almost always *no, the cost outweighs the win*. The exceptions are listed above. Anything else needs a written justification at least as long as this section.
