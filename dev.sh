#!/usr/bin/env bash
# One-command dev launcher: starts the FastAPI backend and the SvelteKit dev
# server in parallel, with clean cleanup on Ctrl-C.
#
# Usage: ./dev.sh
# Prereqs: postgres@16 running, ollama running (optional, for extraction),
#          uv installed, bun installed.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$ROOT/server"
WEB_DIR="$ROOT/web"

cleanup() {
	echo
	echo "→ Stopping…"
	# Kill any child processes in this script's process group
	pkill -P $$ || true
	# Belt-and-suspenders: kill anything still holding our ports
	for port in 8080 5173; do
		lsof -ti tcp:$port 2>/dev/null | xargs -r kill -TERM 2>/dev/null || true
	done
	exit 0
}
trap cleanup INT TERM

# pre-flight
if ! command -v uv >/dev/null; then echo "uv not found"; exit 1; fi
if ! command -v bun >/dev/null; then echo "bun not found in PATH; try: export PATH=\"\$HOME/.bun/bin:\$PATH\""; exit 1; fi
if ! command -v psql >/dev/null; then echo "psql not found; brew install postgresql@16 && brew services start postgresql@16"; exit 1; fi

# ensure DB exists
if ! psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw praxisdoktor_dev; then
	echo "→ Creating praxisdoktor_dev database…"
	createdb praxisdoktor_dev
fi

# migrate + seed if empty
echo "→ Running migrations…"
( cd "$SERVER_DIR" && uv run alembic upgrade head ) >/dev/null

if ! psql -d praxisdoktor_dev -tc "SELECT COUNT(*) FROM users" 2>/dev/null | grep -q '[1-9]'; then
	echo "→ Seeding placeholder users + processes…"
	( cd "$SERVER_DIR" && uv run python seed.py ) >/dev/null
fi

echo "→ Starting backend on http://127.0.0.1:8080 …"
( cd "$SERVER_DIR" && exec uv run uvicorn app.main:app --host 127.0.0.1 --port 8080 ) &
BACK_PID=$!

echo "→ Starting frontend on http://127.0.0.1:5173 …"
( cd "$WEB_DIR" && exec bun run dev --host 127.0.0.1 ) &
FRONT_PID=$!

sleep 2
echo
echo "  ┌─ PraxisDoktor dev ─────────────────────────────────────"
echo "  │ Frontend:  http://localhost:5173"
echo "  │ Backend:   http://localhost:8080"
echo "  │ Login:     dr_inhaber / praxis123  (or admin / praxis123)"
echo "  │ Stop:      Ctrl-C"
echo "  └────────────────────────────────────────────────────────"
echo

# Wait on either child; if one dies we tear down everything.
wait -n "$BACK_PID" "$FRONT_PID" || true
cleanup
