# Skeleton Plan

What gets built in this first end-to-end pass. This is the *container* — the role-aware dashboard with draggable cards, full-screen tool layout with vertical tab bar and slide-in chat panel, identity + auth, transition log, and one real tool inhabitant (Patientenaufnahme ported in). Everything else is empty placeholder cards.

## Repository Layout

```
PraxisDoktor/
├── docs/                          # process_ontology, roles_and_processes, stack, skeleton_plan
├── server/                        # NEW — the FastAPI backend, restructured
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI app, mounts routers
│   │   ├── config.py              # env-driven settings
│   │   ├── db.py                  # SQLAlchemy engine + session
│   │   ├── models/                # SQLAlchemy 2.0 typed models
│   │   │   ├── user.py            # users, roles, user_roles
│   │   │   ├── process.py         # processes, process_role_access, process_instances
│   │   │   ├── transition.py      # transitions, append-only
│   │   │   ├── chat.py            # chat_messages
│   │   │   └── layout.py          # dashboard_layouts (per-user card order)
│   │   ├── auth.py                # password hashing, session cookies, role decorators
│   │   ├── routers/
│   │   │   ├── auth.py            # /login, /logout, /me
│   │   │   ├── dashboard.py       # /dashboard — role-filtered processes
│   │   │   ├── processes.py       # /processes/{id}/instances, transitions
│   │   │   ├── chat.py            # /chat/{process_id}/messages, WS
│   │   │   ├── intake.py          # /intake/* — patient-intake-specific endpoints
│   │   │   └── admin.py           # /admin/users, /admin/roles
│   │   ├── ws.py                  # single WebSocket endpoint, multiplexes channels
│   │   ├── processes/             # registered process modules
│   │   │   ├── registry.py        # the process registry (declarative)
│   │   │   ├── patient_intake.py  # full implementation
│   │   │   └── placeholders.py    # all other processes, declared only
│   │   └── intake/                # ported v1 intake logic
│   │       ├── transcribe.py
│   │       ├── ocr.py
│   │       ├── llm.py
│   │       ├── diarize.py
│   │       └── vocab.py
│   ├── alembic/                   # migrations
│   ├── alembic.ini
│   ├── seed.py                    # placeholder users + roles + processes
│   ├── pyproject.toml             # uv-managed
│   └── .env.example
├── web/                           # NEW — SvelteKit frontend
│   ├── src/
│   │   ├── app.html
│   │   ├── app.css                # Tailwind base
│   │   ├── lib/
│   │   │   ├── api.ts             # typed fetch wrappers
│   │   │   ├── ws.ts              # WebSocket client
│   │   │   ├── stores/            # svelte stores (auth, dashboard, transitions)
│   │   │   ├── undo.ts            # Tier 2 undo/redo client
│   │   │   └── components/
│   │   │       ├── ui/            # shadcn-svelte (copied in)
│   │   │       ├── DashboardCard.svelte
│   │   │       ├── ToolLayout.svelte    # vertical tab bar + main + slide-in chat
│   │   │       ├── ChatPanel.svelte
│   │   │       └── ProcessTabs.svelte
│   │   └── routes/
│   │       ├── +layout.svelte     # auth gate
│   │       ├── +layout.server.ts  # session check
│   │       ├── login/+page.svelte
│   │       ├── dashboard/+page.svelte
│   │       ├── tool/[process_id]/+page.svelte    # full-screen tool
│   │       ├── tool/[process_id]/intake/+page.svelte  # patient intake UI
│   │       └── admin/+page.svelte
│   ├── static/
│   ├── llms/                      # llms.txt files for sveltekit, svelte5, shadcn-svelte, dnd-action
│   ├── package.json
│   ├── svelte.config.js
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── README.md                      # updated with new dev quickstart
├── ANLEITUNG.txt                  # legacy production docs, kept until production rework
└── (legacy v1 files: main.py, db.py, transcribe.py, etc. — kept until ported, then removed)
```

## Build Order (each is one commit minimum)

### Step 1 — Backend skeleton boots
1. Create `server/` structure
2. `pyproject.toml` with FastAPI, SQLAlchemy 2.0, Alembic, asyncpg, fastapi-users, argon2-cffi, uvicorn, websockets, plus existing intake deps
3. `db.py` async engine to local Postgres
4. Models: User, Role, UserRole, Process, ProcessRoleAccess, ProcessInstance, Transition, ChatMessage, DashboardLayout
5. Initial Alembic migration
6. `seed.py` inserts roles, placeholder users (argon2-hashed), processes from registry, access matrix
7. `python -m server.seed` runs clean, `uvicorn server.app.main:app` boots, `/health` returns 200

### Step 2 — Auth works
1. `auth.py` — password verify, session cookie issuance, `current_user` dependency, `require_role(role_id)` dependency factory
2. `routers/auth.py` — POST `/login`, POST `/logout`, GET `/me`
3. Smoke test: curl login as each placeholder account, verify cookie issued, verify `/me` returns user + roles

### Step 3 — Dashboard endpoint works
1. `routers/dashboard.py` — GET `/dashboard` returns processes filtered by current user's roles, ordered by saved layout
2. `routers/dashboard.py` — POST `/dashboard/layout` saves user's card order
3. Smoke test: login as `mfa_anna`, verify only her accessible processes return; login as `dr_inhaber`, verify all return

### Step 4 — Process registry + placeholders
1. `processes/registry.py` — `register_process(...)` decorator-style API
2. `processes/patient_intake.py` — registered with full metadata, transition types
3. `processes/placeholders.py` — all eight other processes registered with metadata only, no handlers
4. On startup, registry syncs to DB

### Step 5 — Transition log
1. `models/transition.py` — append-only table with retracted_by
2. `routers/processes.py` — POST `/processes/{id}/instances/{iid}/transitions`, GET history
3. Undo endpoint: POST `/processes/{id}/instances/{iid}/undo` appends an `undo` transition
4. Feedback view: SQL view `feedback_signals` over transitions where `feeds_back = true AND retracted_by IS NULL`

### Step 6 — WebSocket layer
1. `ws.py` — single endpoint `/ws`, authenticates via session cookie, multiplexes channels: `chat:{process_id}`, `dashboard:user:{user_id}`, `process:{process_id}:{instance_id}`
2. Postgres `LISTEN/NOTIFY` bridge for cross-process broadcast
3. Smoke test: open two browser tabs, send chat in one, see it appear in the other

### Step 7 — SvelteKit frontend boots
1. `bun create svelte@latest web` — TypeScript, Tailwind
2. shadcn-svelte init, copy in initial components (Button, Card, Input, Dialog, Tabs)
3. svelte-dnd-action installed
4. `llms/` directory with `sveltekit.txt`, `svelte5.txt`, `shadcn-svelte.txt`, `dnd-action.txt` (downloaded from official sources)
5. `vite.config.ts` proxies `/api` and `/ws` to `http://localhost:8080`
6. `bun run dev` boots on `:5173`

### Step 8 — Login page
1. `routes/login/+page.svelte` — username + password form, posts to `/api/auth/login`
2. `+layout.server.ts` — checks session, redirects to `/login` if missing
3. Visual polish via shadcn Card + Input + Button
4. Smoke test: login as each role, redirected to `/dashboard`

### Step 9 — Dashboard with draggable cards
1. `routes/dashboard/+page.svelte` — fetches `/api/dashboard`, renders one `DashboardCard` per process
2. svelte-dnd-action wires drag-rearrange; on drop, POST to `/api/dashboard/layout`
3. `DashboardCard.svelte` — process icon, name, phase badge, activity indicator dot, double-click → navigate to `/tool/{process_id}`
4. Smoke test: login as different users, see filtered cards, rearrange persists across reload

### Step 10 — Full-screen tool layout
1. `routes/tool/[process_id]/+page.svelte` — server-loads the process metadata, lays out:
   - Left: vertical tab bar with icons of all other processes the user can access (click → navigate)
   - Center: `<slot />` for the process's own UI
   - Right edge: chat trigger button
2. `ChatPanel.svelte` — slides in from the right (1/4 viewport width), shows messages for `chat:{process_id}`, input at bottom
3. Home button top-left returns to `/dashboard`
4. Smoke test: navigate between tools via the left rail, open chat panel, send a message, see it persist

### Step 11 — Patient intake ported into the new shell
1. `routes/tool/patient_intake/+page.svelte` — replaces the v1 standalone HTML
2. Reuses the existing intake logic on the backend (now under `server/app/intake/`)
3. Each field becomes a native `<input>` with two affordances: native typing (Tier 1 history) and an explicit "✗" reject button
4. Accepting a field (clicking copy or pressing the accept icon) emits a `field_accepted` transition
5. Editing the value and committing on blur/Enter emits `field_corrected`
6. Rejecting emits `field_rejected`
7. Tier 2 undo button on the tool chrome appends `undo` transitions
8. Smoke test: upload an audio file from the demo, see extraction populate fields, accept some, correct others, undo a correction, verify the transition log reflects everything cleanly

### Step 12 — Admin surface
1. `routes/admin/+page.svelte` — list users, add user, assign/unassign roles
2. Only accessible to `praxisinhaber`
3. Plain table UI, no fanciness — Papa visits this twice a year

### Step 13 — Verification + cleanup
1. End-to-end manual run-through with each placeholder account
2. Type-check passes (`tsc --noEmit`, `mypy server/` if configured)
3. Update root `README.md` with new dev quickstart
4. Mark legacy v1 files for removal in a follow-up commit (do not delete in this pass — let the new shell prove itself first)
5. Final commit, then bump LiminalConsulting submodule pin

## What's Explicitly Out of Scope

- Cloudflare DNS / Tunnel configuration (needs your Cloudflare login)
- NSSM / Caddy / Windows-service packaging (needs the practice machine)
- Production deployment (dev runs against local Postgres on this Mac; production is a future step)
- Real role assignments to real people
- Each placeholder process beyond the empty tool view
- Mobile-PWA install flow polish (works by default; deeper polish later)
- Voice-enrollment UI rework
- Anamnesebogen scan flow rework

## Definition of Done for This Pass

- `bun run dev` (in `web/`) and `uv run uvicorn server.app.main:app --reload` (in `server/`) both run cleanly
- Open `http://localhost:5173`, log in as any of seven placeholder accounts
- See a personalized dashboard with role-filtered draggable cards
- Double-click any card → full-screen tool view with vertical tab bar + slide-in chat
- Patient intake works end-to-end: upload audio → see extraction → accept/correct/reject → transitions logged → undo works
- Activity indicator on a card lights up when a chat message arrives in another tab
- Admin can add a user and assign roles
- All commits land in PraxisDoktor sovereign; LiminalConsulting submodule pin bumped to capture them
