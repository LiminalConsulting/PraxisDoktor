# init-app.ps1
# Runs migrations + seeds placeholder users, then pulls the Ollama model.
# Idempotent — Alembic and the seed script both no-op if state already exists.
param(
	[Parameter(Mandatory=$true)] [string] $InstallRoot
)

$ErrorActionPreference = "Stop"

$PgRoot      = Join-Path $InstallRoot "pgsql"
$AppDir      = Join-Path $InstallRoot "app"
$ServerDir   = Join-Path $AppDir "server"
$PythonExe   = Join-Path $InstallRoot "python\python.exe"
$DataDir     = Join-Path $InstallRoot "var\pgdata"
$LogDir      = Join-Path $InstallRoot "var\logs"
$pgctl       = Join-Path $PgRoot "bin\pg_ctl.exe"
$ollamaExe   = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"

# Make sure Postgres is running for the duration of this script
Write-Host "→ Starte Postgres für Setup…"
& $pgctl -D $DataDir -l (Join-Path $LogDir "postgres-init.log") -o "-p 54329" start
Start-Sleep -Seconds 3

try {
	$env:DATABASE_URL = "postgresql+asyncpg://praxisdoktor@127.0.0.1:54329/praxisdoktor"
	$env:ENVIRONMENT  = "production"
	$env:AUDIO_DIR    = Join-Path $InstallRoot "var\audio"
	$env:DATA_DIR     = Join-Path $InstallRoot "var\data"

	Push-Location $ServerDir
	Write-Host "→ Datenbank-Migrationen…"
	& $PythonExe -m alembic upgrade head
	if ($LASTEXITCODE -ne 0) { throw "alembic failed" }

	Write-Host "→ Platzhalter-Konten + Prozesse anlegen…"
	& $PythonExe seed.py
	if ($LASTEXITCODE -ne 0) { throw "seed failed" }
	Pop-Location
} finally {
	& $pgctl -D $DataDir stop -m fast | Out-Null
}

# Pull Ollama model (only if Ollama is installed)
if (Test-Path $ollamaExe) {
	Write-Host "→ Lade KI-Modell llama3.1:8b (~4.7 GB, kann dauern)…"
	& $ollamaExe pull llama3.1:8b
	if ($LASTEXITCODE -ne 0) {
		Write-Warning "Ollama-Pull fehlgeschlagen — kann nach der Installation manuell wiederholt werden."
	}
} else {
	Write-Warning "Ollama nicht gefunden. Bitte separat installieren von https://ollama.com"
}

Write-Host "✓ App initialisiert."
