# Installer — PraxisDoktor v2+

This directory holds everything needed to produce a single `PraxisDoktorSetup-<version>.exe` for Windows.

## What the installer does

On a fresh Windows 10/11 machine:

1. **Copies the full stack** to `C:\Program Files\PraxisDoktor\`:
   - `pgsql/` — Portable Postgres 16 binaries
   - `python/` — Embedded Python 3.11 with all backend deps pre-installed
   - `app/server/` — The FastAPI backend
   - `app/web_build/` — The built SvelteKit frontend (static)
   - `nssm/` — Non-Sucking Service Manager for registering Windows services
   - `runtime/` — PowerShell scripts used at install time and uninstall time
   - `var/` — Runtime data: Postgres data dir, audio files, logs, session secret
2. **Initializes Postgres** in `var/pgdata/`, bound to `127.0.0.1:54329` (never exposed).
3. **Installs Ollama** (if missing) by running the bundled `OllamaSetup.exe` — user completes that interactive step.
4. **Pulls the LLM** (`llama3.1:8b`, ~4.7 GB).
5. **Applies migrations + seeds** the placeholder roles/users/processes.
6. **Registers three Windows services** via NSSM:
   - `PraxisDoktor-Postgres` → starts on boot, auto-restart
   - `PraxisDoktor-Ollama` → same
   - `PraxisDoktor-App` → FastAPI + static frontend on port 8080
7. **Opens the browser** at `http://localhost:8080`.

No black terminal windows. No manual commands. No dev tooling on the practice machine.

## Uninstall

Removes the three services via NSSM, deletes the install dir and `var/`. Ollama itself is *not* removed (user chose to install it via its own installer).

## Build it locally (won't work from Mac — must be Windows)

The build is hermetic and only runs on `windows-latest` in CI. To trigger:

```bash
# Tag triggers the release workflow
git tag v2.0.0
git push origin v2.0.0

# Or trigger a dev build without a tag via the GitHub Actions UI
# (workflow_dispatch on release-v2.yml)
```

Artifact `PraxisDoktorSetup-2.0.0.exe` lands as a workflow artifact and
(for tagged builds) on the GitHub Release page.

## Limits (honestly acknowledged)

- **Installer size** is ~500 MB–1 GB (Postgres + Python + torch + faster-whisper + easyocr weights).
- **First run** downloads the Ollama model (~4.7 GB).
- **Not code-signed** (yet) — Windows SmartScreen will warn on first run; user clicks "More info → Run anyway". Code signing needs an EV certificate (~€300/year) and is deferred.
- **End-to-end verification on a real Windows box** is not possible from the Mac dev environment — first install at the Praxis is the true smoke test. The installer is structured to be idempotent and re-runnable so partial-success recovery is easy.

## Service management (post-install, on the Windows box)

```powershell
# Check status
Get-Service PraxisDoktor-*

# Stop / start / restart
Stop-Service  PraxisDoktor-App
Start-Service PraxisDoktor-App
Restart-Service PraxisDoktor-*

# View logs
Get-Content "C:\Program Files\PraxisDoktor\var\logs\PraxisDoktor-App.log" -Tail 50 -Wait
```
