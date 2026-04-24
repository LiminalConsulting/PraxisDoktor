# init-tunnel.ps1
# Persists the Cloudflare Tunnel token to var/cloudflared.token so the service
# can pick it up. The token is the only client-specific secret; everything else
# (DNS, routing, Pages project) is provisioned in advance by tooling/new-client.sh
# and lives on Cloudflare's side.
#
# Token can come from three places, in priority order:
#   1. -Token CLI argument (silent install via /TUNNEL_TOKEN= flag in Inno Setup)
#   2. environment variable PRAXISDOKTOR_TUNNEL_TOKEN (CI smoke tests)
#   3. existing token file at var/cloudflared.token (re-runs / upgrades)
# If none are available, we skip — the App still runs locally; only the public
# website integration is dormant. Re-run init-tunnel.ps1 later to enable.

param(
	[Parameter(Mandatory=$true)] [string] $InstallRoot,
	[string] $Token = ""
)

$ErrorActionPreference = "Stop"

$VarDir     = Join-Path $InstallRoot "var"
$TokenFile  = Join-Path $VarDir "cloudflared.token"

New-Item -ItemType Directory -Force -Path $VarDir | Out-Null

if (-not $Token) { $Token = $env:PRAXISDOKTOR_TUNNEL_TOKEN }

if ($Token) {
	Set-Content -Path $TokenFile -Value $Token.Trim() -NoNewline -Encoding ASCII
	# Best-effort ACL tighten: SYSTEM + Administrators only
	try {
		$acl = Get-Acl $TokenFile
		$acl.SetAccessRuleProtection($true, $false)
		$rules = @(
			New-Object System.Security.AccessControl.FileSystemAccessRule("NT AUTHORITY\SYSTEM", "FullControl", "Allow"),
			New-Object System.Security.AccessControl.FileSystemAccessRule("BUILTIN\Administrators", "FullControl", "Allow")
		)
		foreach ($r in $rules) { $acl.AddAccessRule($r) }
		Set-Acl -Path $TokenFile -AclObject $acl
	} catch {
		Write-Warning "Konnte ACLs auf $TokenFile nicht setzen: $_"
	}
	Write-Host "✓ Cloudflare-Tunnel-Token gespeichert."
} elseif (Test-Path $TokenFile) {
	Write-Host "  (Bestehender Tunnel-Token wird wiederverwendet.)"
} else {
	Write-Host "  (Kein Tunnel-Token angegeben — öffentliche Website bleibt deaktiviert.)"
	Write-Host "  Zum nachträglichen Aktivieren: init-tunnel.ps1 -Token <token> erneut ausführen."
}
