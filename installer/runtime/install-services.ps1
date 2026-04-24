# install-services.ps1
# Register Postgres, Ollama, and FastAPI as Windows services using NSSM.
# Auto-start on boot, auto-restart on crash. Idempotent.
param(
	[Parameter(Mandatory=$true)] [string] $InstallRoot
)

$ErrorActionPreference = "Stop"

$Nssm        = Join-Path $InstallRoot "nssm\nssm.exe"
$PgRoot      = Join-Path $InstallRoot "pgsql"
$AppDir      = Join-Path $InstallRoot "app"
$ServerDir   = Join-Path $AppDir "server"
$PythonDir   = Join-Path $InstallRoot "python"
$PythonExe   = Join-Path $PythonDir "python.exe"
$DataDir     = Join-Path $InstallRoot "var\pgdata"
$LogDir      = Join-Path $InstallRoot "var\logs"
$AudioDir    = Join-Path $InstallRoot "var\audio"
$AppDataDir  = Join-Path $InstallRoot "var\data"
$pgctl       = Join-Path $PgRoot "bin\pg_ctl.exe"
$pgPostgres  = Join-Path $PgRoot "bin\postgres.exe"
$ollamaExe   = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
$CloudflaredExe = Join-Path $InstallRoot "cloudflared\cloudflared.exe"
$TunnelTokenFile = Join-Path $InstallRoot "var\cloudflared.token"

New-Item -ItemType Directory -Force -Path $LogDir, $AudioDir, $AppDataDir | Out-Null

function Install-Service {
	param([string]$Name, [string]$Exe, [string]$Args, [hashtable]$Env)
	# Stop + remove if exists, so we can update params idempotently
	$existing = & $Nssm status $Name 2>$null
	if ($existing) {
		& $Nssm stop $Name 2>$null | Out-Null
		& $Nssm remove $Name confirm 2>$null | Out-Null
	}
	& $Nssm install $Name $Exe $Args
	& $Nssm set $Name DisplayName "PraxisDoktor — $Name"
	& $Nssm set $Name Description "Teil der PraxisDoktor-Installation."
	& $Nssm set $Name Start SERVICE_AUTO_START
	& $Nssm set $Name AppStdout (Join-Path $LogDir "$Name.log")
	& $Nssm set $Name AppStderr (Join-Path $LogDir "$Name.log")
	& $Nssm set $Name AppRotateFiles 1
	& $Nssm set $Name AppRotateBytes 10485760
	& $Nssm set $Name AppExit Default Restart
	if ($Env) {
		$envBlock = ($Env.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "`n"
		& $Nssm set $Name AppEnvironmentExtra $envBlock
	}
}

# 1. Postgres
Write-Host "→ Service: PraxisDoktor-Postgres"
Install-Service -Name "PraxisDoktor-Postgres" `
	-Exe $pgPostgres `
	-Args "-D `"$DataDir`" -p 54329"

# 2. Ollama (only if installed)
if (Test-Path $ollamaExe) {
	Write-Host "→ Service: PraxisDoktor-Ollama"
	Install-Service -Name "PraxisDoktor-Ollama" `
		-Exe $ollamaExe `
		-Args "serve" `
		-Env @{ "OLLAMA_HOST" = "127.0.0.1:11434" }
}

# 3. FastAPI
Write-Host "→ Service: PraxisDoktor-App"
$uvicornArgs = "-m uvicorn app.main:app --host 0.0.0.0 --port 8080"
Install-Service -Name "PraxisDoktor-App" `
	-Exe $PythonExe `
	-Args $uvicornArgs `
	-Env @{
		"DATABASE_URL"    = "postgresql+asyncpg://praxisdoktor@127.0.0.1:54329/praxisdoktor"
		"ENVIRONMENT"     = "production"
		"AUDIO_DIR"       = $AudioDir
		"DATA_DIR"        = $AppDataDir
		"OLLAMA_HOST"     = "http://127.0.0.1:11434"
		"PYTHONUNBUFFERED" = "1"
	}
& $Nssm set "PraxisDoktor-App" AppDirectory $ServerDir

# 4. Cloudflare Tunnel — only if a token file exists (skipped on dev/CI without one)
if ((Test-Path $CloudflaredExe) -and (Test-Path $TunnelTokenFile)) {
	$token = (Get-Content $TunnelTokenFile -Raw).Trim()
	if ($token) {
		Write-Host "→ Service: PraxisDoktor-Tunnel"
		Install-Service -Name "PraxisDoktor-Tunnel" `
			-Exe $CloudflaredExe `
			-Args "tunnel --no-autoupdate run --token $token"
	} else {
		Write-Host "  (Tunnel-Token leer — überspringe Cloudflare-Tunnel-Service.)"
	}
} else {
	Write-Host "  (Kein Cloudflare-Tunnel konfiguriert — öffentliche Website-Anbindung deaktiviert.)"
}

# Start them in dependency order
Write-Host "→ Starte Dienste…"
Start-Service "PraxisDoktor-Postgres"
Start-Sleep -Seconds 3
if (Get-Service "PraxisDoktor-Ollama" -ErrorAction SilentlyContinue) {
	Start-Service "PraxisDoktor-Ollama"
	Start-Sleep -Seconds 2
}
Start-Service "PraxisDoktor-App"
if (Get-Service "PraxisDoktor-Tunnel" -ErrorAction SilentlyContinue) {
	Start-Service "PraxisDoktor-Tunnel"
}

Write-Host "✓ Dienste registriert und gestartet."
Write-Host ""
Write-Host "PraxisDoktor läuft unter http://localhost:8080"
if (Get-Service "PraxisDoktor-Tunnel" -ErrorAction SilentlyContinue) {
	Write-Host "Öffentliche Website ist über den Cloudflare-Tunnel verbunden."
}
