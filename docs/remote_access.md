# Remote access — Mac → Praxis-Server

How David (anywhere in the world) reaches a client's practice server's Windows desktop. Validated end-to-end on `uro-karlsruhe` 2026-04-29; the same pattern reused for every future client.

## Architecture decision

**Cloudflare Tunnel + RDP + Microsoft Windows App.** OpenVPN is explicitly *retired*.

Reasoning:

- **You own the path.** OpenVPN tenants you under the practice's IT-guy. Cloudflare Tunnel runs on your own CF account — you control DNS, Access policy, revocation.
- **Survives IT-guy turnover.** Same path works regardless of who manages the practice's networking.
- **Replicates trivially to client #2 and beyond** via the per-client convention below.
- **No inbound firewall changes** at the practice — `cloudflared.exe` makes outbound connections only.
- **§203 / DSGVO posture is clean.** Cloudflare DPA covers transport; RDP is end-to-end encrypted inside the tunnel; no third-party relay sees session contents.
- **Speed of iteration.** No coordination with anyone to provision/change.

## Per-client convention (canonical naming)

| Resource | Pattern | Example (uro-karlsruhe) |
|---|---|---|
| RDP tunnel name | `praxisdoktor-<slug>-rdp` | `praxisdoktor-uro-karlsruhe-rdp` |
| RDP hostname | `rdp-<slug>.liminality.space` | `rdp-uro-karlsruhe.liminality.space` |
| Cloudflare Access app | `praxis-rdp-<slug>` | `praxis-rdp-uro-karlsruhe` |
| Windows user | `david-consult` (uniform) | same on every server |
| Per-client config dir | `tooling/clients/<slug>/cloudflare-rdp.env` | gitignored |

The RDP tunnel is **separate** from the public-API tunnel (`praxisdoktor-<slug>` for `app.<domain>`). Reasoning: RDP into a §203-protected medical server is meaningfully more sensitive than the public-API ingress; isolation pays for itself (revocability, audit, blast-radius).

## Architecture diagram

```
Your Mac (anywhere)              Cloudflare edge              Practice server (Windows)
┌────────────────┐               ┌──────────┐                ┌──────────────────┐
│  Windows App   │               │          │                │  cloudflared.exe │
│   (RDP client) │ ───TLS────►   │ Tunnel   │ ◄───TLS────────│  (outbound only, │
│       ▲        │               │          │                │   Windows svc)   │
│       │        │               └──────────┘                │       │          │
│ cloudflared    │                    ▲                      │       ▼          │
│ access rdp     │               Cloudflare Access           │  localhost:3389  │
└────────────────┘               (only david's email         └──────────────────┘
                                  can authenticate)
```

Four layers, each doing one job:

1. **Network** — Cloudflare Tunnel gets bytes from Mac to server.
2. **Protocol** — RDP translates "show desktop" + "type this" + "copy this".
3. **Client** — Windows App on Mac renders the desktop, captures input.
4. **Auth** — Two gates: Cloudflare Access (verify identity) + Windows login (verify Windows account).

---

## Setup checklist (one-time per client)

### Cloudflare side — from your Mac

**1. Create the tunnel via API**

Wrangler-OAuth scope is enough to create the tunnel + ingress (but not DNS / Access — see "Known wrangler-OAuth gap" below):

```bash
CF_TOKEN=$(grep '^oauth_token' ~/Library/Preferences/.wrangler/config/default.toml | head -1 | cut -d'"' -f2)
ACCOUNT_ID="e88634195fd77ebed356aceee1427568"
SLUG="<client-slug>"
TUNNEL_NAME="praxisdoktor-${SLUG}-rdp"

# Create tunnel — returns tunnel ID, but no token (need to fetch separately)
curl -sS -X POST -H "Authorization: Bearer $CF_TOKEN" -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel" \
  -d "{\"name\":\"$TUNNEL_NAME\",\"config_src\":\"cloudflare\"}"
```

**2. Configure ingress** (set `<TUNNEL_ID>` from the previous response):

```bash
curl -sS -X PUT -H "Authorization: Bearer $CF_TOKEN" -H "Content-Type: application/json" \
  "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel/<TUNNEL_ID>/configurations" \
  -d "{\"config\":{\"ingress\":[{\"hostname\":\"rdp-${SLUG}.liminality.space\",\"service\":\"rdp://localhost:3389\"},{\"service\":\"http_status:404\"}]}}"
```

**3. Get the connector token from the dashboard** (wrangler OAuth can't fetch this — see gap below):

- https://one.dash.cloudflare.com/ → **Networks → Tunnels** → click `praxisdoktor-<slug>-rdp` → **Configure** → **Install connector** tab → choose **Windows / 64-bit**
- Copy the token from the install command (the long `eyJ...` string)

**4. DNS CNAME** (manual, dashboard):

- https://dash.cloudflare.com/ → liminality.space → DNS → Records → Add record
- Type: `CNAME` · Name: `rdp-<slug>` · Target: `<TUNNEL_ID>.cfargotunnel.com` · Proxy: **Proxied** (orange cloud) · TTL: Auto

**5. Cloudflare Access application** (manual, dashboard):

- https://one.dash.cloudflare.com/ → **Access → Applications → Add** → **Self-hosted**
- **Application name**: `praxis-rdp-<slug>`
- **Destinations → Public hostnames**: subdomain `rdp-<slug>`, domain `liminality.space`
- **Allow browser-based RDP/SSH/VNC**: leave **OFF** (you're using native Windows App, not browser-based)
- **Add policy**:
  - Policy name: `David only`
  - Action: `Allow`
  - Include rule → Selector: `Emails` → Value: `david.rug98@icloud.com`
  - **Text controls** (under Connection settings): set to `Enable copying/pasting` (only matters for browser-based, but flip on principle)
- **Identity provider**: One-time PIN (default; no extra setup)
- Save

### Windows side — at the practice server (or RDP'd in via existing access)

**1. Download cloudflared.exe** — Administrator PowerShell:

```powershell
$url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
$dest = "C:\Program Files\cloudflared\cloudflared.exe"
New-Item -ItemType Directory -Force -Path "C:\Program Files\cloudflared" | Out-Null
Invoke-WebRequest -Uri $url -OutFile $dest
```

**2. Install as a Windows service with the tunnel token** — Administrator PowerShell:

⚠️ **Critical: wrap the token in double quotes**, and use `&` (call operator). Without quotes PowerShell parses the token as multiple expressions (the `.` separators in the JWT trip up the parser) and throws `Unexpected Token "service"`.

```powershell
& "C:\Program Files\cloudflared\cloudflared.exe" service install "<PASTE_TOKEN_HERE>"
```

If you cd'd into the cloudflared dir first, this also works:

```powershell
& .\cloudflared.exe service install "<PASTE_TOKEN_HERE>"
```

Verify the service is running:

```powershell
Get-Service cloudflared
```

Expect `Status: Running`. Confirm in the Cloudflare dashboard: **Networks → Tunnels** → tunnel should show **HEALTHY** with 1 active connector.

**3. Create the `david-consult` Windows user** — Administrator PowerShell.

⚠️ **Use language-portable SIDs for the group names.** German Windows uses "Administratoren" + "Remotedesktopbenutzer", English uses "Administrators" + "Remote Desktop Users". The SIDs are universal:

```powershell
$pw = Read-Host -AsSecureString "Set password for david-consult"
New-LocalUser -Name "david-consult" -Password $pw -FullName "David Rug (Consulting)" -Description "Liminal Consulting RDP user"

# Language-portable group lookup via SID
$admins = (Get-LocalGroup | Where-Object { $_.SID -eq "S-1-5-32-544" }).Name
$rdp = (Get-LocalGroup | Where-Object { $_.SID -eq "S-1-5-32-555" }).Name
Add-LocalGroupMember -Group $admins -Member "david-consult"
Add-LocalGroupMember -Group $rdp -Member "david-consult"
```

Verify:

```powershell
Get-LocalGroupMember -Group $admins | Select-String david-consult
Get-LocalGroupMember -Group $rdp | Select-String david-consult
```

Save the password into:
- macOS Keychain (Passwörter app)
- `tooling/clients/<slug>/practice-server.env` line `PRACTICE_SERVER_RDP_PASSWORD=...`

**Why a separate user (not just sharing Administrator)**:
- Audit trail (Windows event log shows your actions distinct from the practice owner's)
- Session isolation (their open documents don't get clobbered if you connect)
- §203 hygiene (your access is named, separable, revokable)
- Cleaner story to tell IT auditors

### Mac side — daily usage

**1. Open the RDP path through Cloudflare** — Mac terminal (one tab kept open during the session).

For uro-karlsruhe, a shell alias `praxis-rdp` is defined in `~/.zshrc` — just run:

```bash
praxis-rdp
```

(Equivalent to `cloudflared access rdp --hostname rdp-uro-karlsruhe.liminality.space --url localhost:23389`.)

For other clients, the canonical form is:

```bash
cloudflared access rdp --hostname rdp-<slug>.liminality.space --url localhost:23389
```

First connection: browser tab opens for Cloudflare Access auth → enter `david.rug98@icloud.com` → check email for PIN → paste back. Subsequent connections within the session-token TTL skip this.

**2. Connect Windows App to `localhost:23389`**

- **+ Add PC** → PC name: `localhost:23389`
- **User account → Add User Account...** → username: `david-consult` / password (from Keychain)
- Save → double-click to connect
- Accept the certificate warning (RDP self-signs)

**3. Enable in the PC's Edit settings**:
- **Devices & Audio → Redirect**: ✅ Clipboard
- **Folders → Add**: `~/Downloads` (so schema dumps + extracts land directly on your Mac)

That's it. From any network, anywhere — the same three steps.

### Mac ↔ Windows clipboard mappings (Windows App)

| You want to... | Press on Mac | Sent to Windows as |
|---|---|---|
| Copy / paste | **⌘ C** / **⌘ V** | Ctrl+C / Ctrl+V |
| Select all | **⌘ A** | Ctrl+A |
| Switch app on Windows | **⌥ Tab** | Alt+Tab |
| Ctrl+Alt+Del | **Fn + ⌃ + ⌥ + ⌫** | Ctrl+Alt+Del |
| Right-click | **⌃ click** or two-finger trackpad | Right-click |

Use ⌘ (not Ctrl) for clipboard inside the RDP session — Windows App auto-translates ⌘→Ctrl.

---

## Known wrangler-OAuth gap (worth fixing once)

`wrangler login` token has `account/user/workers*/d1` scopes but NOT `dns_records:edit`, `access:edit`, or `cfd_tunnel:read` (sufficient for create-tunnel, not for fetch-token or fetch-status). So API automation of these fails — must use the dashboard.

Two clean fixes:

1. Re-run `wrangler login` and accept the broader OAuth consent (if CF surfaces it).
2. Create a scoped API token at dash.cloudflare.com → Profile → API Tokens with:
   - `Account → Cloudflare Tunnel: Edit`
   - `Zone → DNS: Edit`
   - `Account → Access: Apps and Policies: Edit`
   Store in `~/.config/cf-token` or env.

Either fix unblocks `tooling/new-client.sh` from doing the full per-client setup hands-off (see "Roll-out to client #2" below).

---

## Files this depends on

- `tooling/clients/<slug>/cloudflare-rdp.env` (gitignored) — tunnel name, ID, hostname, token
- `tooling/clients/<slug>/practice-server.env` (gitignored) — RDP credentials, MO DB info
- `tooling/clients/<slug>/README.md` — convention docs

---

## Roll-out to client #2 (Barbara onboarding playbook)

Once the wrangler-OAuth gap is closed, the entire flow above collapses to:

```bash
./tooling/new-client.sh <slug> <domain>          # public-API tunnel + Pages
./tooling/new-client-rdp.sh <slug>               # RDP tunnel + DNS + Access app
# → produces tooling/clients/<slug>/cloudflare-rdp.env with token
# → outputs the PowerShell snippet to paste on the Windows server
```

**Three on-site steps remain** (necessarily manual since they're physical-machine actions):

1. Run the cloudflared install PowerShell snippet on the practice server (paste from `cloudflare-rdp.env`)
2. Run the david-consult creation PowerShell snippet (use SID-based group lookup — it's already language-portable)
3. From your Mac: `cloudflared access rdp --hostname rdp-<slug>.liminality.space --url localhost:23389` + Windows App → connect

Total time per new client (excluding any IT-guy coordination, which is now zero): **~15 min Mac side + ~5 min on-site**.

### Status of `uro-karlsruhe` (the first client)

As of 2026-04-29:
- ✅ Tunnel created (ID `5a1abd8a-2ba5-4f3e-a366-c0c043c001cc`)
- ✅ Ingress rule configured
- ✅ DNS CNAME live (`rdp-uro-karlsruhe.liminality.space`)
- ✅ Cloudflare Access app `praxis-rdp-uro-karlsruhe` with policy gating to `david.rug98@icloud.com`
- ✅ cloudflared.exe service running on `SERVERMO`
- ✅ `david-consult` Windows local admin user created (in Administratoren + Remotedesktopbenutzer)
- ✅ Connection verified end-to-end from Mac (clipboard + folder redirect tested)
