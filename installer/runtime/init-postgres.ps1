# init-postgres.ps1
# First-run initialization for the bundled Postgres 16.
# Idempotent: safe to re-run. Sets up a self-contained data dir under
# the install root so we never touch any global Postgres install.
param(
	[Parameter(Mandatory=$true)] [string] $InstallRoot
)

$ErrorActionPreference = "Stop"

$PgRoot   = Join-Path $InstallRoot "pgsql"
$DataDir  = Join-Path $InstallRoot "var\pgdata"
$LogDir   = Join-Path $InstallRoot "var\logs"
$initdb   = Join-Path $PgRoot "bin\initdb.exe"
$pgctl    = Join-Path $PgRoot "bin\pg_ctl.exe"
$psql     = Join-Path $PgRoot "bin\psql.exe"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $DataDir) | Out-Null

if (-not (Test-Path (Join-Path $DataDir "PG_VERSION"))) {
	Write-Host "→ Initialisiere Postgres-Datenverzeichnis…"
	# Trust local IPv4/IPv6; the service binds 127.0.0.1 only, so this is safe
	& $initdb -D $DataDir -U praxisdoktor --auth-host=trust --auth-local=trust --encoding=UTF8 --locale=C
	if ($LASTEXITCODE -ne 0) { throw "initdb failed" }

	# Override postgresql.conf to bind localhost only on a non-default port
	$confPath = Join-Path $DataDir "postgresql.conf"
	Add-Content $confPath ""
	Add-Content $confPath "# PraxisDoktor"
	Add-Content $confPath "listen_addresses = '127.0.0.1'"
	Add-Content $confPath "port = 54329"
	Add-Content $confPath "unix_socket_directories = ''"
	Add-Content $confPath "log_destination = 'stderr'"
	Add-Content $confPath "logging_collector = on"
	Add-Content $confPath "log_directory = '$($LogDir -replace '\\','/')'"
	Add-Content $confPath "log_filename = 'postgres.log'"
	Add-Content $confPath "log_rotation_size = 10MB"
}

# Start temporarily to create the database if needed
Write-Host "→ Starte Postgres temporär für DB-Initialisierung…"
& $pgctl -D $DataDir -l (Join-Path $LogDir "postgres-init.log") -o "-p 54329" start
Start-Sleep -Seconds 3

# Create database if missing
$exists = & $psql -h 127.0.0.1 -p 54329 -U praxisdoktor -tAc "SELECT 1 FROM pg_database WHERE datname='praxisdoktor'" 2>$null
if (-not $exists) {
	Write-Host "→ Lege Datenbank 'praxisdoktor' an…"
	& $psql -h 127.0.0.1 -p 54329 -U praxisdoktor -c "CREATE DATABASE praxisdoktor"
}

& $pgctl -D $DataDir stop -m fast | Out-Null
Write-Host "✓ Postgres bereit."
