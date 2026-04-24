# Handoff — what only David can do

Everything else has been completed and pushed. This is the short list of
things that genuinely require your hands or your accounts.

> Status as of this checkpoint: rc2 tag pushed, CI building in background.
> Public site live at https://praxisdoktor-uro-karlsruhe.pages.dev/
> Cloudflare Pages project + Tunnel created in your Liminal Consulting account.

---

## 1. Domain migration — Papa-dependent, not urgent

**What:** Move `uro-karlsruhe.de` nameservers from current registrar to Cloudflare.

**Why blocking:** The `app.uro-karlsruhe.de` DNS CNAME → tunnel can't be created
until the zone lives in your CF account. Without it, the public site can't
talk to the practice server (forms will fail with 401 or DNS error).

**Until then:** the public site lives at `https://praxisdoktor-uro-karlsruhe.pages.dev/`
and the booking/anamnese forms simply won't reach a real backend (acceptable
for showcasing the visual design + structure).

**How:**
1. In Cloudflare dashboard: **Add a Site** → enter `uro-karlsruhe.de` → pick Free plan.
2. CF gives you 2 nameservers (e.g. `xxx.ns.cloudflare.com`).
3. Coordinate with Papa to update those at his current registrar (he may need
   to ask his current host where the domain is registered — likely the same
   place that hosts the WordPress site).
4. Once the zone shows "Active" in CF: **re-run** `./tooling/new-client.sh uro-karlsruhe uro-karlsruhe.de`
   — it'll detect the zone now exists and create the DNS record automatically.

---

## 2. Verify the rc2 installer build (when CI finishes)

CI is running now. When it completes:
- ✅ green: download `installer/output/PraxisDoktorSetup-2.0.0-rc2.exe` from
  the Actions artifact, ready for Papa's machine
- ❌ red: open the run, look at the failed step. Most likely culprit if it
  fails: cloudflared download URL changed, or the smoke test's new public-API
  probe failed for some reason

```bash
gh run view --log-failed   # if it fails
gh run download <run-id>   # if it succeeds
```

---

## 3. On-site at Papa's practice (whenever the visit happens)

Bring with you:
- The `.exe` from the rc2 release (or rc3 if you've shipped fixes since)
- The tunnel token from `tooling/clients/uro-karlsruhe/cloudflare.env`
  (line `TUNNEL_TOKEN=...`)
- The PUBLIC_API_KEY from the same file

On the practice server:
1. Run the installer. At the "Cloudflare-Tunnel" wizard page, paste the
   tunnel token. (Or run silently: `PraxisDoktorSetup-2.0.0-rc2.exe /VERYSILENT /TUNNEL_TOKEN=eyJh...`)
2. After install, edit `C:\Program Files\PraxisDoktor\var\public_api_key.txt`
   to contain the PUBLIC_API_KEY value (overwriting the auto-generated one),
   then restart the App service: `Restart-Service PraxisDoktor-App`.
3. Verify all four services running: `Get-Service PraxisDoktor-*`

---

## 4. Optional polish before showing Papa

The public site has placeholder content where Papa-confirmed real data should
go. To find them: `grep -rn TODO public/src/lib/practice.ts`

- Address (street + ZIP)
- Phone, fax, email
- Dr. Bruckschen's full first name
- Hero / team photos (likely already have rights to MG_1548 + MG_1796 from
  `_reference/old-site/assets/`; confirm with Papa, then move into `public/static/`)

This is fine to do incrementally — public site is already presentable enough
to show as proof-of-concept right now.

---

## 5. Things that are explicitly NOT blocking

- ❎ Cloudflare R2 — activated, unused (no use case yet)
- ❎ `cloudflared tunnel login` — the new-client.sh script uses the API
  directly, no browser auth needed
- ❎ Manual DNS records in CF — script handles them once zone is added
- ❎ Email Routing setup — deferred until we actually do email-triage
- ❎ Build pipeline for the public site — `bun run deploy` from `public/`
  works with the per-client `.env` already in place
