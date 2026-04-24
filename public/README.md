# public/ — PraxisDoktor public marketing site

SvelteKit + Cloudflare Pages. Companion to the internal app in `../web/`.

Both apps share brand tokens via `../shared/brand.css` — single source of truth.

## Local dev

```bash
cd public
bun install
cp .env.example .env  # edit if needed
bun run dev           # http://127.0.0.1:5174
```

You'll need the practice server running on `:8080` to test form submissions
(see `../server/README.md`).

## Deploy

Deployment is handled by the `tooling/new-client.sh` script (one-shot per
client) plus `bun run deploy` on subsequent updates. The per-client tunnel
token + `VITE_PUBLIC_API_KEY` come from the practice server's
`var/public_api_key.txt` — same secret on both sides.

## Architecture

- **Static build → Cloudflare Pages** (free tier, edge-cached, no Workers).
- Forms POST to `https://app.{practice-domain}/api/public/*` over a
  **Cloudflare Tunnel** to the practice's on-prem FastAPI server.
- No patient data ever lives on Cloudflare. Tunnel is a tube; data terminates
  at the practice server.

See `../docs/stack.md` for the full picture.
