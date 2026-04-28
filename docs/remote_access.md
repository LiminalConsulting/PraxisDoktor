# Remote access — Mac → Praxis-Server

How David (anywhere in the world) reaches the practice server's Windows desktop. Designed once for `uro-karlsruhe`, the pattern reused for every future client.

## Architecture decision

**Cloudflare Tunnel + RDP + Microsoft Windows App.** OpenVPN is explicitly *not* the path going forward.

Reasoning:

- **You own the path.** OpenVPN tenants you under Papa's IT-guy. Cloudflare Tunnel runs on your own CF account, you control DNS / Access policy / revocation.
- **Survives IT-guy turnover.** Same path works regardless of who manages the practice's networking.
- **Replicates trivially to client #2 (Barbara) and beyond.** The pattern is a per-client `praxisdoktor-<slug>-rdp` tunnel + `rdp-<slug>.liminality.space` hostname.
- **No inbound firewall changes** at the practice — `cloudflared.exe` makes outbound connections only.
- **§203 / DSGVO posture is clean.** Cloudflare DPA covers the transport layer; no third-party relay sees session contents (RDP is end-to-end encrypted inside the tunnel).

## Per-client convention (canonical naming)

| Resource | Pattern | Example (uro-karlsruhe) |
|---|---|---|
| RDP tunnel name | `praxisdoktor-<slug>-rdp` | `praxisdoktor-uro-karlsruhe-rdp` |
| RDP hostname | `rdp-<slug>.liminality.space` | `rdp-uro-karlsruhe.liminality.space` |
| Windows user | `david-consult` | `david-consult` (same on every server) |
| Per-client config dir | `tooling/clients/<slug>/cloudflare-rdp.env` | already exists |

The RDP tunnel is **separate** from the public-API tunnel (`praxisdoktor-<slug>` for `app.<domain>`). Reasoning: RDP into a §203-protected medical server is meaningfully more sensitive than the public-API ingress; isolation pays for itself (revocability, audit, blast-radius).

## Architecture diagram

```
Your Mac (anywhere)              Cloudflare edge              Practice server (Windows)
┌────────────────┐               ┌──────────┐                ┌──────────────────┐
│  Windows App   │               │          │                │  cloudflared.exe │
│   (RDP client) │ ───TLS────►   │ Tunnel   │ ◄───TLS────────│  (outbound only, │
│                │               │          │                │   Windows svc)   │
│ ⬇                                                          │                  │
│ cloudflared    │                                            │  ⬇               │
│ access rdp     │                                            │  Localhost:3389  │
└────────────────┘               └──────────┘                 └──────────────────┘
                                       ▲
                                  Cloudflare Access
                                  (only david.rug98@icloud.com
                                  can authenticate)
```

Four layers, each doing one job:

1. **Network** — Cloudflare Tunnel gets bytes from Mac to server.
2. **Protocol** — RDP translates "show desktop" + "type this" + "copy this".
3. **Client** — Windows App on Mac renders the desktop, captures input.
4. **Auth** — Two gates: Cloudflare Access (verify identity) + Windows login (verify Windows account).

---

## Setup checklist (one-time, on-site at Papa's home or practice)

### Cloudflare side — already done from Mac (2026-04-28)

- ✅ Tunnel `praxisdoktor-uro-karlsruhe-rdp` created (ID `5a1abd8a-2ba5-4f3e-a366-c0c043c001cc`)
- ✅ Ingress rule: `rdp-uro-karlsruhe.liminality.space` → `rdp://localhost:3389`
- ⚠️ DNS CNAME for `rdp-uro-karlsruhe.liminality.space` — **needs manual creation** (wrangler OAuth lacks `dns_records:edit` scope). Do via dashboard:
  - https://dash.cloudflare.com/ → liminality.space → DNS → Records → Add record
  - Type: CNAME · Name: `rdp-uro-karlsruhe` · Target: `5a1abd8a-2ba5-4f3e-a366-c0c043c001cc.cfargotunnel.com` · Proxy: Proxied (orange cloud) · TTL: Auto
- ⚠️ Cloudflare Access policy gating to `david.rug98@icloud.com` — **needs creation**:
  - https://one.dash.cloudflare.com/ → Access → Applications → Add → Self-hosted
  - Application name: `praxis-rdp-uro-karlsruhe`
  - Application domain: `rdp-uro-karlsruhe.liminality.space`
  - Identity providers: One-time PIN (or Google/GitHub if configured)
  - Policy: Allow · Include: Emails · `david.rug98@icloud.com`

### Windows side — on-site at the practice server

When physically at Papa's home (RDP'd into the server) or at the practice:

**1. Download cloudflared.exe**

PowerShell as Administrator:
```powershell
$url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
$dest = "C:\Program Files\cloudflared\cloudflared.exe"
New-Item -ItemType Directory -Force -Path "C:\Program Files\cloudflared" | Out-Null
Invoke-WebRequest -Uri $url -OutFile $dest
```

**2. Install as a Windows service with the tunnel token**

Get `TUNNEL_TOKEN` from `tooling/clients/uro-karlsruhe/cloudflare-rdp.env` on your Mac. Type it into the Windows server (don't copy through clipboard if RDP isn't yet established — paste later, or USB-transfer):

```powershell
& "C:\Program Files\cloudflared\cloudflared.exe" service install <TUNNEL_TOKEN>
```

The service will be named `cloudflared` and starts automatically. Verify:
```powershell
Get-Service cloudflared
```

**3. Verify connector check-in**

On Mac:
```bash
CF_TOKEN=$(grep '^oauth_token' ~/Library/Preferences/.wrangler/config/default.toml | head -1 | cut -d'"' -f2)
ACCOUNT_ID="e88634195fd77ebed356aceee1427568"
TUNNEL_ID="5a1abd8a-2ba5-4f3e-a366-c0c043c001cc"
curl -sS -H "Authorization: Bearer $CF_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/cfd_tunnel/$TUNNEL_ID" \
  | python3 -m json.tool | grep -E "status|conns_active"
```
Expect `"status": "healthy"` once cloudflared.exe is running.

**4. Create dedicated `david-consult` Windows user (separate from Papa's)**

PowerShell as Administrator:
```powershell
$pw = Read-Host -AsSecureString "Set password for david-consult"
New-LocalUser -Name "david-consult" -Password $pw -FullName "David Rug (Consulting)" -Description "Liminal Consulting RDP user"
Add-LocalGroupMember -Group "Administrators" -Member "david-consult"
Add-LocalGroupMember -Group "Remote Desktop Users" -Member "david-consult"
```

Save the password into your Mac Keychain + into `tooling/clients/uro-karlsruhe/practice-server.env` under `PRACTICE_SERVER_RDP_USER=david-consult` and `PRACTICE_SERVER_RDP_PASSWORD=<...>`.

**Why a separate user**:
- Audit trail (Windows event log shows your actions distinct from Papa's)
- Session isolation (his open documents don't get clobbered if you connect)
- §203 hygiene (your access is named, separable, revokable)
- Cleaner story to tell IT auditors

### Mac side — daily usage

Once tunnel + Access policy + Windows user exist:

**1. Open the RDP path through Cloudflare**

From Mac terminal (one tab kept open during the session):
```bash
cloudflared access rdp --hostname rdp-uro-karlsruhe.liminality.space --url localhost:23389
```

First time: a browser tab opens for Cloudflare Access auth (your one-time PIN to your email). Subsequent connections within the session-token TTL skip this.

**2. Connect Windows App to localhost:23389**

Open Windows App → Add PC → PC Name: `localhost:23389` → User account: `david-consult` / your password. Save. Connect.

**3. Enable in the PC's Edit settings**:
- **Devices & Audio → Redirect**: ✅ Clipboard
- **Folders → Add**: `~/Downloads` (so schema dumps land directly in your Mac filesystem)

That's it. From any network, anywhere — the same three steps.

---

## Files this depends on

- `tooling/clients/uro-karlsruhe/cloudflare-rdp.env` (gitignored) — tunnel token + IDs
- `tooling/clients/uro-karlsruhe/practice-server.env` (gitignored) — RDP credentials
- `tooling/clients/uro-karlsruhe/README.md` — convention docs

## Roll-out to client #2

The script `tooling/new-client.sh` currently provisions the *public-API* tunnel. To roll RDP-from-anywhere into the per-client onboarding, extend it with a parallel `cfd_tunnel` create + ingress + DNS CNAME for the `-rdp` variant. Same Cloudflare API calls, same gitignored env file convention, just `_RDP` suffixed.
