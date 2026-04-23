# uninstall-services.ps1 — called by the Inno Setup uninstaller.
param(
	[Parameter(Mandatory=$true)] [string] $InstallRoot
)
$Nssm = Join-Path $InstallRoot "nssm\nssm.exe"
foreach ($svc in @("PraxisDoktor-App", "PraxisDoktor-Ollama", "PraxisDoktor-Postgres")) {
	if (Get-Service $svc -ErrorAction SilentlyContinue) {
		try { Stop-Service $svc -Force } catch {}
		& $Nssm remove $svc confirm 2>$null | Out-Null
	}
}
