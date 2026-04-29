#!/usr/bin/env bash
# new-client-rdp.sh — provision Cloudflare RDP tunnel for a PraxisDoktor client.
#
# Run this just before your first on-site visit. Complements new-client.sh
# (public stack) but is intentionally separate — not every client needs RDP
# access, and this tunnel is meaningfully more sensitive (§203-protected server).
#
# Idempotent: re-running picks up existing resources where possible.
# Uses ~/.config/liminality/cf-api-token (scoped token with Tunnel+DNS+Access
# edit rights). Does NOT use wrangler's OAuth token — wrong scopes.
#
# Creates / verifies:
#   1. Cloudflare Tunnel          praxisdoktor-<slug>-rdp
#   2. Tunnel ingress             rdp-<slug>.<domain> → rdp://localhost:3389
#   3. DNS CNAME                  rdp-<slug>.<domain> → <tunnel-id>.cfargotunnel.com
#   4. Cloudflare Access app      praxis-rdp-<slug> gating to DAVID_EMAIL
#   5. Cloudflare Access policy   Allow · Emails · DAVID_EMAIL
#
# Emits:
#   tooling/clients/<slug>/cloudflare-rdp.env  (gitignored)
#
# Prints two ready-to-paste PowerShell snippets for the on-site Windows steps.
#
# Usage:
#   ./tooling/new-client-rdp.sh <slug> <domain>
#
# Examples:
#   ./tooling/new-client-rdp.sh uro-karlsruhe liminality.space
#   ./tooling/new-client-rdp.sh barbara-freiburg liminality.space

set -euo pipefail

SLUG="${1:-}"
DOMAIN="${2:-}"

if [[ -z "$SLUG" || -z "$DOMAIN" ]]; then
	echo "usage: $0 <slug> <domain>" >&2
	exit 1
fi

# --- Config ---
DAVID_EMAIL="david.rug98@icloud.com"
TUNNEL_NAME="praxisdoktor-${SLUG}-rdp"
RDP_HOSTNAME="rdp-${SLUG}.${DOMAIN}"
TOKEN_FILE="${CF_TOKEN_FILE:-$HOME/.config/liminality/cf-api-token}"
API="https://api.cloudflare.com/client/v4"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT_DIR="$SCRIPT_DIR/clients/$SLUG"

# --- Auth ---
if [[ ! -f "$TOKEN_FILE" ]]; then
	echo "✘ CF API token not found at $TOKEN_FILE" >&2
	echo "  Create one at https://dash.cloudflare.com/profile/api-tokens" >&2
	echo "  Required permissions: Cloudflare Tunnel:Edit, Access:Edit, DNS:Edit" >&2
	exit 1
fi
CF_TOKEN=$(cat "$TOKEN_FILE")

api() {
	local method="$1"; shift
	local path="$1"; shift
	curl -sS -X "$method" \
		-H "Authorization: Bearer $CF_TOKEN" \
		-H "Content-Type: application/json" \
		"$API$path" "$@"
}

ok() { python3 -c "import sys,json; r=json.load(sys.stdin); sys.exit(0 if r.get('success') else 1)"; }

# --- Resolve account ID ---
echo "→ Verifying Cloudflare auth…"
ACCOUNT_ID=$(api GET "/user/tokens/verify" \
	| python3 -c "
import sys, json
r = json.load(sys.stdin)
if not r.get('success'):
    sys.stderr.write('Token verification failed: ' + str(r.get('errors')) + '\n')
    sys.exit(1)
print(r['result'].get('not_before', ''))  # just proves it works
" >/dev/null 2>&1 || true)

# Get account ID from the zones list (most reliable)
ACCOUNT_ID=$(api GET "/zones?name=$DOMAIN" \
	| python3 -c "
import sys, json
r = json.load(sys.stdin)
res = r.get('result', [])
if not res:
    sys.stderr.write('Zone $DOMAIN not found in this account\n')
    sys.exit(1)
print(res[0]['account']['id'])
")

ZONE_ID=$(api GET "/zones?name=$DOMAIN" \
	| python3 -c "
import sys, json
r = json.load(sys.stdin)
print(r['result'][0]['id'])
")

echo ""
echo "================================================================"
echo "  Client:    $SLUG"
echo "  Domain:    $DOMAIN"
echo "  Account:   $ACCOUNT_ID"
echo "  Tunnel:    $TUNNEL_NAME"
echo "  Hostname:  $RDP_HOSTNAME"
echo "  Gate:      $DAVID_EMAIL only"
echo "================================================================"
echo ""

# --- 1. Tunnel ---
echo "→ RDP tunnel…"
TUNNEL_ID=$(api GET "/accounts/$ACCOUNT_ID/cfd_tunnel?is_deleted=false&per_page=50" \
	| python3 -c "
import sys, json
r = json.load(sys.stdin)
for t in r.get('result', []):
    if t['name'] == '$TUNNEL_NAME':
        print(t['id'])
        break
")

if [[ -n "$TUNNEL_ID" ]]; then
	echo "  ✓ already exists: $TUNNEL_NAME ($TUNNEL_ID)"
else
	RESP=$(api POST "/accounts/$ACCOUNT_ID/cfd_tunnel" \
		--data "{\"name\":\"$TUNNEL_NAME\",\"config_src\":\"cloudflare\"}")
	TUNNEL_ID=$(echo "$RESP" | python3 -c "
import sys, json
r = json.load(sys.stdin)
if not r.get('success'):
    sys.stderr.write(json.dumps(r, indent=2) + '\n')
    sys.exit(1)
print(r['result']['id'])
")
	echo "  ✓ created: $TUNNEL_NAME ($TUNNEL_ID)"
fi

# --- 2. Ingress config ---
echo "→ Ingress rule…"
RESP=$(api PUT "/accounts/$ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/configurations" \
	--data "{
  \"config\": {
    \"ingress\": [
      {\"hostname\": \"$RDP_HOSTNAME\", \"service\": \"rdp://localhost:3389\"},
      {\"service\": \"http_status:404\"}
    ]
  }
}")
if echo "$RESP" | ok; then
	echo "  ✓ ingress: $RDP_HOSTNAME → rdp://localhost:3389"
else
	echo "  ⚠ ingress update warning:"; echo "$RESP" | python3 -m json.tool
fi

# --- 3. Connector token ---
echo "→ Connector token…"
TUNNEL_TOKEN=$(api GET "/accounts/$ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/token" \
	| python3 -c "
import sys, json
r = json.load(sys.stdin)
if not r.get('success'):
    sys.stderr.write('Token fetch failed: ' + str(r.get('errors')) + '\n')
    sys.exit(1)
print(r['result'])
")
echo "  ✓ token fetched"

# --- 4. DNS CNAME ---
echo "→ DNS CNAME…"
CNAME_TARGET="${TUNNEL_ID}.cfargotunnel.com"
EXISTING_DNS=$(api GET "/zones/$ZONE_ID/dns_records?name=$RDP_HOSTNAME&type=CNAME")
DNS_ID=$(echo "$EXISTING_DNS" | python3 -c "
import sys, json
r = json.load(sys.stdin)
res = r.get('result', [])
print(res[0]['id'] if res else '')
")
BODY="{\"type\":\"CNAME\",\"name\":\"$RDP_HOSTNAME\",\"content\":\"$CNAME_TARGET\",\"proxied\":true,\"ttl\":1}"
if [[ -n "$DNS_ID" ]]; then
	api PUT "/zones/$ZONE_ID/dns_records/$DNS_ID" --data "$BODY" >/dev/null
	echo "  ✓ DNS updated: $RDP_HOSTNAME → $CNAME_TARGET (proxied)"
else
	api POST "/zones/$ZONE_ID/dns_records" --data "$BODY" >/dev/null
	echo "  ✓ DNS created: $RDP_HOSTNAME → $CNAME_TARGET (proxied)"
fi

# --- 5. Cloudflare Access app + policy ---
echo "→ Cloudflare Access app…"
APP_NAME="praxis-rdp-${SLUG}"
EXISTING_APP=$(api GET "/accounts/$ACCOUNT_ID/access/apps" \
	| python3 -c "
import sys, json
r = json.load(sys.stdin)
for app in r.get('result', []):
    if app.get('domain') == '$RDP_HOSTNAME':
        print(app['id'])
        break
")

if [[ -n "$EXISTING_APP" ]]; then
	echo "  ✓ Access app already exists (id: $EXISTING_APP)"
	APP_ID="$EXISTING_APP"
else
	RESP=$(api POST "/accounts/$ACCOUNT_ID/access/apps" \
		--data "{
  \"name\": \"$APP_NAME\",
  \"domain\": \"$RDP_HOSTNAME\",
  \"type\": \"self_hosted\",
  \"session_duration\": \"168h\",
  \"allowed_idps\": [],
  \"auto_redirect_to_identity\": false
}")
	APP_ID=$(echo "$RESP" | python3 -c "
import sys, json
r = json.load(sys.stdin)
if not r.get('success'):
    sys.stderr.write(json.dumps(r, indent=2) + '\n')
    sys.exit(1)
print(r['result']['id'])
")
	echo "  ✓ created: $APP_NAME (session: 7 days)"
fi

# --- 5b. Access policy ---
echo "→ Access policy…"
EXISTING_POLICY=$(api GET "/accounts/$ACCOUNT_ID/access/apps/$APP_ID/policies" \
	| python3 -c "
import sys, json
r = json.load(sys.stdin)
for p in r.get('result', []):
    if p.get('name') == 'David only':
        print(p['id'])
        break
")

if [[ -n "$EXISTING_POLICY" ]]; then
	echo "  ✓ policy already exists"
else
	RESP=$(api POST "/accounts/$ACCOUNT_ID/access/apps/$APP_ID/policies" \
		--data "{
  \"name\": \"David only\",
  \"decision\": \"allow\",
  \"include\": [{\"email\": {\"email\": \"$DAVID_EMAIL\"}}],
  \"require\": [],
  \"exclude\": [],
  \"precedence\": 1
}")
	if echo "$RESP" | ok; then
		echo "  ✓ policy created: Allow · $DAVID_EMAIL"
	else
		echo "  ⚠ policy creation warning:"; echo "$RESP" | python3 -m json.tool
	fi
fi

# --- 6. Write cloudflare-rdp.env ---
mkdir -p "$CLIENT_DIR"
cat > "$CLIENT_DIR/cloudflare-rdp.env" <<EOF
# Generated by tooling/new-client-rdp.sh on $(date +%Y-%m-%d)
# DO NOT COMMIT — gitignored via tooling/clients/.
CF_TUNNEL_NAME=$TUNNEL_NAME
CF_TUNNEL_ID=$TUNNEL_ID
CF_RDP_HOSTNAME=$RDP_HOSTNAME
CF_ZONE_ID=$ZONE_ID
CF_ACCOUNT_ID=$ACCOUNT_ID
CF_ACCESS_APP_ID=$APP_ID
TUNNEL_TOKEN=$TUNNEL_TOKEN
EOF
chmod 600 "$CLIENT_DIR/cloudflare-rdp.env"
echo "  ✓ cloudflare-rdp.env written"

# --- 7. Print on-site PowerShell snippets ---
echo ""
echo "================================================================"
echo "  ✓ Cloudflare side complete — all resources provisioned"
echo "================================================================"
echo ""
echo "  Two PowerShell snippets to paste on the Windows server."
echo "  Run both as Administrator."
echo ""
echo "────────────────────────────────────────────────────────────────"
echo "  SNIPPET 1 — Install cloudflared as a Windows service"
echo "────────────────────────────────────────────────────────────────"
cat <<POWERSHELL
\$url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
\$dest = "C:\Program Files\cloudflared\cloudflared.exe"
New-Item -ItemType Directory -Force -Path "C:\Program Files\cloudflared" | Out-Null
Invoke-WebRequest -Uri \$url -OutFile \$dest
& "C:\Program Files\cloudflared\cloudflared.exe" service install "$TUNNEL_TOKEN"
Get-Service cloudflared
POWERSHELL
echo ""
echo "────────────────────────────────────────────────────────────────"
echo "  SNIPPET 2 — Create david-consult Windows user"
echo "  (language-portable: uses SIDs, works on German + English Windows)"
echo "────────────────────────────────────────────────────────────────"
cat <<'POWERSHELL'
$pw = Read-Host -AsSecureString "Set password for david-consult"
New-LocalUser -Name "david-consult" -Password $pw -FullName "David Rug (Consulting)" -Description "Liminal Consulting RDP user"
$admins = (Get-LocalGroup | Where-Object { $_.SID -eq "S-1-5-32-544" }).Name
$rdp    = (Get-LocalGroup | Where-Object { $_.SID -eq "S-1-5-32-555" }).Name
Add-LocalGroupMember -Group $admins -Member "david-consult"
Add-LocalGroupMember -Group $rdp    -Member "david-consult"
Get-LocalGroupMember -Group $admins | Select-String david-consult
Get-LocalGroupMember -Group $rdp    | Select-String david-consult
POWERSHELL
echo ""
echo "────────────────────────────────────────────────────────────────"
echo "  Mac side — after snippets are done"
echo "────────────────────────────────────────────────────────────────"
echo "  1. Add alias to ~/.zshrc:"
echo "       alias rdp-${SLUG}='cloudflared access rdp --hostname $RDP_HOSTNAME --url localhost:23389'"
echo ""
echo "  2. Connect:"
echo "       rdp-${SLUG}"
echo "       Windows App → localhost:23389 → david-consult"
echo ""
echo "  3. Save david-consult password to Keychain + tooling/clients/$SLUG/practice-server.env"
echo ""
