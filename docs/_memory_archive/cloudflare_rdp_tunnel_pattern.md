---
name: Cloudflare RDP tunnel — per-client convention (replaces OpenVPN)
description: David reaches each client's Windows server via dedicated CF Tunnel + Windows App; OpenVPN is explicitly NOT the path going forward
type: project
originSessionId: f5bdb875-89ff-475c-b6fa-6c94427cf63b
---
# Cloudflare RDP tunnel pattern (per-client)

**Decision (2026-04-28)**: Cloudflare Tunnel + RDP + Microsoft Windows App is the canonical path for David to reach any client's Windows practice server from his Mac. **OpenVPN is NOT the path going forward** — was tried, deprioritized, headaches in past + makes David tenant of client's IT-guy.

## Why CF Tunnel beats OpenVPN here

- **David owns the path**: own CF account, own DNS, own Access policy, own revocation. Not borrowed credentials in someone else's domain.
- **Survives IT-guy turnover** at the practice.
- **No inbound firewall changes** at the client — `cloudflared.exe` makes outbound connections only.
- **Replicates trivially to client #2+** via per-client naming convention.
- **§203/DSGVO clean**: Cloudflare DPA covers transport; RDP end-to-end encrypted inside the tunnel; no third-party relay sees session contents.
- **Speed of iteration**: David doesn't wait for IT-guy to provision/change anything.

## Per-client naming convention (canonical)

| Resource | Pattern | Example (uro-karlsruhe) |
|---|---|---|
| RDP tunnel name | `praxisdoktor-<slug>-rdp` | `praxisdoktor-uro-karlsruhe-rdp` |
| RDP hostname | `rdp-<slug>.liminality.space` | `rdp-uro-karlsruhe.liminality.space` |
| Windows user (per server) | `david-consult` (uniform) | same on every server |
| Per-client config dir | `tooling/clients/<slug>/cloudflare-rdp.env` | gitignored |

The RDP tunnel is **separate** from the public-API tunnel (`praxisdoktor-<slug>` for `app.<domain>`). Reasoning: RDP into a §203-protected medical server is meaningfully more sensitive than the public-API ingress; isolation pays for itself (revocability, audit, blast-radius).

## How to apply

- When asked about remote access for a new client: propose this pattern by default. Don't propose OpenVPN unless there's a specific reason (e.g. client mandates it).
- For a new client `<slug>`:
  1. Create `praxisdoktor-<slug>-rdp` tunnel via CF API
  2. Configure ingress: `rdp-<slug>.liminality.space` → `rdp://localhost:3389`
  3. Create DNS CNAME (currently manual — wrangler OAuth lacks `dns_records:edit` scope; use dashboard or scoped API token)
  4. Create Cloudflare Access policy gating to `consulting@liminality.space`
  5. On client's Windows server: install cloudflared.exe as service with the token, create `david-consult` local admin user
  6. Test from Mac with `cloudflared access rdp --hostname rdp-<slug>.liminality.space --url localhost:23389` + Windows App → `localhost:23389`
- Detailed steps in `PraxisDoktor/docs/remote_access.md` (auto-loaded into PraxisDoktor sessions).

## Automation — fully resolved (2026-04-29)

Scoped CF API token created, stored at `~/.config/liminality/cf-api-token` (chmod 600, off-repo).
Permissions: Tunnel:Edit + Access:Edit + DNS:Edit. Validated against all three scopes.
`tooling/new-client-rdp.sh` reads from this token and fully automates the Cloudflare side
(tunnel + ingress + token fetch + DNS CNAME + Access app + policy) in one command.
Prints two ready-to-paste PowerShell snippets for the on-site Windows steps.

## RDP access strategy — revised (2026-04-29)

**Rule: use IT guy's infrastructure where it exists, own it where it doesn't.**

| Situation | Approach |
|---|---|
| Practice has IT guy, VPN available | Use their VPN. No tunnel needed. |
| Practice has IT guy, VPN not ready yet | Tunnel as temporary bridge. Clean up when VPN arrives. |
| No IT guy | Cloudflare tunnel as permanent sovereign access. |

For uro-karlsruhe specifically: tunnel is temporary. Papa's IT guy was asked to set up a VPN
account for David. Once that's ready, switch to VPN + uninstall cloudflared + remove david-consult
if IT guy prefers. This minimises coordination surface with existing IT vendors.

## IT vendor communication pattern (standard per-client procedure)

1. Ask doctor about IT vendor during intake — get name + email
2. Call IT guy within 48h of on-site visit — introduce yourself, explain what you installed,
   invite conversation about his security principles, offer to comply with them
3. Send PDF briefing same day as follow-up protocol (subject: "wie besprochen")
4. Template: `PraxisDoktor/docs/it_briefing_template.md`
5. Store IT contact in `tooling/clients/<slug>/contacts.md` (gitignored)

Key framing on the call: "Ich bin für die Software-Automatisierungsschicht zuständig —
Datenauswertung, Prozessoptimierung. Die IT-Infrastruktur bleibt vollständig in Ihrem Bereich."

## Status of uro-karlsruhe (the first client)

As of 2026-04-29 — **fully validated end-to-end**:
- ✅ Tunnel created (ID `5a1abd8a-2ba5-4f3e-a366-c0c043c001cc`)
- ✅ Ingress rule configured
- ✅ DNS CNAME live (`rdp-uro-karlsruhe.liminality.space`)
- ✅ Cloudflare Access app `praxis-rdp-uro-karlsruhe` gating to consulting@liminality.space
- ✅ cloudflared.exe service running on `SERVERMO` (Papa's practice server hostname)
- ✅ `david-consult` Windows local admin user (in Administratoren + Remotedesktopbenutzer)
- ✅ Connection verified from Mac (clipboard + folder redirect both tested)

## Real-world fixes baked into docs/remote_access.md

1. **PowerShell quoting**: must wrap tunnel token in double quotes AND use `&` call operator. `& "C:\...\cloudflared.exe" service install "<TOKEN>"`. Without quotes the token's `.` separators trip the parser → `Unexpected Token "service"`.
2. **German Windows group names**: "Administrators" doesn't exist on German Windows (it's "Administratoren") and "Remote Desktop Users" is "Remotedesktopbenutzer". Use SID-based lookup for language-portability: S-1-5-32-544 (Admins), S-1-5-32-555 (RDP Users).
3. **Token from dashboard, not API**: wrangler OAuth lacks the scope to fetch the connector token via API. The token field in cloudflare-rdp.env may contain "None" — get fresh token from dashboard → Networks → Tunnels → Configure → Install connector → Windows.
4. **Access app "Text controls"**: in the policy "Connection settings" section, this only affects browser-based RDP (which we're not using). Set to Enable copying/pasting on principle.
