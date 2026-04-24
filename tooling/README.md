# tooling/

Operator scripts for Liminal Consulting. Per-client setup automation.

## `new-client.sh`

Provisions Cloudflare resources for a new PraxisDoktor client:
- Cloudflare Pages project (the public marketing site)
- Cloudflare Tunnel (the bridge from Pages → practice server)
- DNS routing for `app.<client-domain>` (if the zone is in Cloudflare)
- Generates the tunnel token + the shared `PUBLIC_API_KEY`

```bash
./tooling/new-client.sh uro-karlsruhe uro-karlsruhe.de
```

Per-client config lands in `tooling/clients/<slug>/` (gitignored).

### Prerequisites

- `bun add -g wrangler` (Cloudflare CLI for Pages/Workers)
- `brew install cloudflared` (Cloudflare CLI for Tunnels — separate tool)
- One-time login: `wrangler login` and `cloudflared tunnel login`

### Idempotent

Re-running the script picks up existing Pages projects + tunnels. Safe to use
to refresh tokens or check state.

## Per-client convention

All resources for a client share the slug:

| Resource type | Name pattern | Example |
|---|---|---|
| Pages project | `praxisdoktor-<slug>` | `praxisdoktor-uro-karlsruhe` |
| Tunnel | `praxisdoktor-<slug>` | `praxisdoktor-uro-karlsruhe` |
| Public site host | `<client-domain>` | `uro-karlsruhe.de` |
| API tunnel host | `app.<client-domain>` | `app.uro-karlsruhe.de` |
| Local config dir | `tooling/clients/<slug>/` | `tooling/clients/uro-karlsruhe/` |
