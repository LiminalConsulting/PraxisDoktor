#!/usr/bin/env bash
# new-client.sh — provision Cloudflare resources for a new PraxisDoktor client.
#
# Idempotent: re-running picks up existing resources where possible.
# Uses the Cloudflare API directly (with wrangler's OAuth token), so no
# `cloudflared tunnel login` browser step is required.
#
# Creates / verifies:
#   1. Cloudflare Pages project   <slug>
#   2. Cloudflare Tunnel          <slug>
#   3. DNS routing                app.<domain> → tunnel  (only if zone is in CF)
#
# Emits per-client config under tooling/clients/<slug>/ (gitignored):
#   - cloudflare.env  — tunnel token + PUBLIC_API_KEY (secret)
#   - pages.env       — for the public site build
#   - ingress.yml     — the cloudflared ingress config (for reference)
#
# Usage:
#   ./tooling/new-client.sh <slug> <domain> [public-api-key]

set -euo pipefail

SLUG="${1:-}"
DOMAIN="${2:-}"
PUBLIC_API_KEY="${3:-}"

if [[ -z "$SLUG" || -z "$DOMAIN" ]]; then
	echo "usage: $0 <slug> <domain> [public-api-key]" >&2
	exit 1
fi

PROJECT_NAME="praxisdoktor-${SLUG}"
TUNNEL_NAME="praxisdoktor-${SLUG}"
APP_SUBDOMAIN="app.${DOMAIN}"
WRANGLER="${WRANGLER:-$HOME/.bun/bin/wrangler}"

if [[ ! -x "$WRANGLER" ]] && ! command -v "$WRANGLER" >/dev/null 2>&1; then
	echo "✘ wrangler not found at $WRANGLER. Install with: bun add -g wrangler" >&2
	exit 1
fi

# Pull auth token + account ID from wrangler's stored OAuth config
WRANGLER_CFG="$HOME/Library/Preferences/.wrangler/config/default.toml"
if [[ ! -f "$WRANGLER_CFG" ]]; then
	# Linux fallback
	WRANGLER_CFG="$HOME/.config/.wrangler/config/default.toml"
fi
if [[ ! -f "$WRANGLER_CFG" ]]; then
	echo "✘ wrangler config not found. Run: wrangler login" >&2
	exit 1
fi

CF_TOKEN=$(grep '^oauth_token' "$WRANGLER_CFG" | head -1 | cut -d'"' -f2)
if [[ -z "$CF_TOKEN" ]]; then
	echo "✘ no oauth_token in wrangler config. Run: wrangler login" >&2
	exit 1
fi

echo "→ Verifying Cloudflare auth…"
WHOAMI=$("$WRANGLER" whoami 2>&1)
ACCOUNT_ID=$(echo "$WHOAMI" | grep -oE '[a-f0-9]{32}' | head -1)
if [[ -z "$ACCOUNT_ID" ]]; then
	echo "✘ could not detect account ID from wrangler whoami output" >&2
	exit 1
fi

API="https://api.cloudflare.com/client/v4"
api() {
	local method="$1"; shift
	local path="$1"; shift
	curl -sS -X "$method" -H "Authorization: Bearer $CF_TOKEN" \
		-H "Content-Type: application/json" "$API$path" "$@"
}

echo ""
echo "================================================================"
echo "  Client:     $SLUG"
echo "  Domain:     $DOMAIN"
echo "  Account:    $ACCOUNT_ID"
echo "  Project:    $PROJECT_NAME"
echo "  Tunnel:     $TUNNEL_NAME"
echo "  API host:   $APP_SUBDOMAIN"
echo "================================================================"
echo ""

# ----------------------------------------------------------------------
# 1. Pages project
# ----------------------------------------------------------------------
echo "→ Pages project…"
EXISTING=$(api GET "/accounts/$ACCOUNT_ID/pages/projects" \
	| python3 -c "import sys,json; r=json.load(sys.stdin); print(','.join(p['name'] for p in r.get('result',[])))")
if echo ",$EXISTING," | grep -q ",${PROJECT_NAME},"; then
	echo "  ✓ already exists: $PROJECT_NAME"
else
	RESP=$(api POST "/accounts/$ACCOUNT_ID/pages/projects" \
		--data "{\"name\":\"$PROJECT_NAME\",\"production_branch\":\"main\"}")
	if ! echo "$RESP" | python3 -c "import sys,json; r=json.load(sys.stdin); sys.exit(0 if r.get('success') else 1)"; then
		echo "✘ Pages project creation failed:"; echo "$RESP"; exit 1
	fi
	echo "  ✓ created: $PROJECT_NAME"
fi

# ----------------------------------------------------------------------
# 2. Tunnel — created via API; secret is generated locally and also stored CF-side
# ----------------------------------------------------------------------
echo "→ Tunnel…"
EXISTING_TUNNELS=$(api GET "/accounts/$ACCOUNT_ID/cfd_tunnel?is_deleted=false&per_page=50")
TUNNEL_ID=$(echo "$EXISTING_TUNNELS" | python3 -c "
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
	# Tunnel secret = 32 random bytes, base64. Stored on CF side too.
	TUNNEL_SECRET=$(openssl rand -base64 32 | tr -d '\n')
	RESP=$(api POST "/accounts/$ACCOUNT_ID/cfd_tunnel" \
		--data "{\"name\":\"$TUNNEL_NAME\",\"tunnel_secret\":\"$TUNNEL_SECRET\",\"config_src\":\"cloudflare\"}")
	TUNNEL_ID=$(echo "$RESP" | python3 -c "
import sys, json
r = json.load(sys.stdin)
if not r.get('success'):
    sys.stderr.write(json.dumps(r, indent=2) + '\n')
    sys.exit(1)
print(r['result']['id'])
")
	if [[ -z "$TUNNEL_ID" ]]; then echo "✘ tunnel creation failed"; exit 1; fi
	echo "  ✓ created: $TUNNEL_NAME ($TUNNEL_ID)"
fi

# Get the connector token (what cloudflared uses to authenticate)
TUNNEL_TOKEN=$(api GET "/accounts/$ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/token" \
	| python3 -c "import sys,json; r=json.load(sys.stdin); print(r['result'])")
if [[ -z "$TUNNEL_TOKEN" ]]; then
	echo "✘ failed to fetch tunnel connector token"; exit 1
fi

# ----------------------------------------------------------------------
# 3. Tunnel ingress config — route app.<domain> → http://localhost:8080
#    For config_src=cloudflare, the ingress lives in CF's dashboard / API.
#    The catch-all (last entry) is mandatory.
# ----------------------------------------------------------------------
echo "→ Tunnel ingress config…"
INGRESS=$(cat <<EOF
{
  "config": {
    "ingress": [
      {
        "hostname": "$APP_SUBDOMAIN",
        "service": "http://localhost:8080",
        "originRequest": {
          "noTLSVerify": true
        }
      },
      {
        "service": "http_status:404"
      }
    ]
  }
}
EOF
)
RESP=$(api PUT "/accounts/$ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID/configurations" --data "$INGRESS")
if ! echo "$RESP" | python3 -c "import sys,json; sys.exit(0 if json.load(sys.stdin).get('success') else 1)"; then
	echo "  ⚠ ingress config update returned a warning:"
	echo "$RESP" | python3 -m json.tool
else
	echo "  ✓ ingress: $APP_SUBDOMAIN → http://localhost:8080 (catch-all 404)"
fi

# ----------------------------------------------------------------------
# 4. DNS routing — only attempt if the zone is in this Cloudflare account
# ----------------------------------------------------------------------
echo "→ DNS route $APP_SUBDOMAIN → tunnel…"
ZONE_RESP=$(api GET "/zones?name=$DOMAIN&account.id=$ACCOUNT_ID")
ZONE_ID=$(echo "$ZONE_RESP" | python3 -c "
import sys, json
r = json.load(sys.stdin)
res = r.get('result', [])
print(res[0]['id'] if res else '')
")

if [[ -z "$ZONE_ID" ]]; then
	echo "  ⚠ Zone $DOMAIN is not in Cloudflare (yet)."
	echo "    Add the zone in the dashboard, update the registrar nameservers,"
	echo "    then re-run this script — it'll pick up where it left off."
else
	# CNAME app.<domain> -> <tunnel-id>.cfargotunnel.com, proxied
	CNAME_TARGET="${TUNNEL_ID}.cfargotunnel.com"
	# Check existing record first
	EXISTING_DNS=$(api GET "/zones/$ZONE_ID/dns_records?name=$APP_SUBDOMAIN&type=CNAME")
	DNS_ID=$(echo "$EXISTING_DNS" | python3 -c "
import sys, json
r = json.load(sys.stdin)
res = r.get('result', [])
print(res[0]['id'] if res else '')
")
	BODY="{\"type\":\"CNAME\",\"name\":\"$APP_SUBDOMAIN\",\"content\":\"$CNAME_TARGET\",\"proxied\":true,\"ttl\":1}"
	if [[ -n "$DNS_ID" ]]; then
		api PUT "/zones/$ZONE_ID/dns_records/$DNS_ID" --data "$BODY" >/dev/null
		echo "  ✓ DNS updated: $APP_SUBDOMAIN → $CNAME_TARGET (proxied)"
	else
		api POST "/zones/$ZONE_ID/dns_records" --data "$BODY" >/dev/null
		echo "  ✓ DNS created: $APP_SUBDOMAIN → $CNAME_TARGET (proxied)"
	fi
fi

# ----------------------------------------------------------------------
# 5. Generate the public API key if not provided
# ----------------------------------------------------------------------
if [[ -z "$PUBLIC_API_KEY" ]]; then
	PUBLIC_API_KEY=$(openssl rand -hex 32)
	echo "  (generated new PUBLIC_API_KEY)"
fi

# ----------------------------------------------------------------------
# 6. Write per-client config files (gitignored)
# ----------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT_DIR="$SCRIPT_DIR/clients/$SLUG"
mkdir -p "$CLIENT_DIR"

cat > "$CLIENT_DIR/cloudflare.env" <<EOF
# Generated by tooling/new-client.sh on $(date +%Y-%m-%d)
# DO NOT COMMIT — this file holds the tunnel token + shared API key.

CF_PAGES_PROJECT=$PROJECT_NAME
CF_TUNNEL_NAME=$TUNNEL_NAME
CF_TUNNEL_ID=$TUNNEL_ID
CF_API_SUBDOMAIN=$APP_SUBDOMAIN

# Bake into the Windows installer (silent flag) or paste into the wizard prompt:
TUNNEL_TOKEN=$TUNNEL_TOKEN

# Bake into the public/ build (.env when running 'bun run build') AND set as
# the practice server's public_api_key.txt:
PUBLIC_API_KEY=$PUBLIC_API_KEY
EOF
chmod 600 "$CLIENT_DIR/cloudflare.env"

# Pages-deploy .env for the public site build
cat > "$CLIENT_DIR/pages.env" <<EOF
VITE_PRACTICE_API=https://$APP_SUBDOMAIN
VITE_PUBLIC_API_KEY=$PUBLIC_API_KEY
EOF

echo ""
echo "================================================================"
echo "  ✓ Provisioning complete"
echo "================================================================"
echo ""
echo "  Per-client config saved to: $CLIENT_DIR/"
echo "    - cloudflare.env   (tunnel token + API key — keep secret)"
echo "    - pages.env        (public site build env)"
echo ""
echo "  Next steps:"
echo "    1. Build + deploy the public site:"
echo "         cd public && cp ../$CLIENT_DIR/pages.env .env && bun run build"
echo "         wrangler pages deploy build --project-name $PROJECT_NAME"
echo ""
echo "    2. Build the Windows installer with this tunnel token baked in"
echo "       (silent: PraxisDoktorSetup.exe /TUNNEL_TOKEN=<token>),"
echo "       OR install interactively and paste the token at the prompt."
echo ""
echo "    3. Set the practice server's public_api_key.txt to match:"
echo "         (Windows) C:\\Program Files\\PraxisDoktor\\var\\public_api_key.txt"
echo "         The same PUBLIC_API_KEY value as in pages.env"
echo ""
