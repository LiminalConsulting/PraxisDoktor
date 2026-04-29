# Handoff — current state + what only David can do

> Status as of 2026-04-29:
> - **Cloudflare RDP tunnel fully validated end-to-end** — David can now RDP
>   into Papa's practice server (`SERVERMO`) from anywhere via Windows App.
>   Tunnel `praxisdoktor-uro-karlsruhe-rdp` healthy, DNS CNAME live, Access
>   app gating to david.rug98@icloud.com, cloudflared service running on
>   server, dedicated `david-consult` Windows user (Administratoren +
>   Remotedesktopbenutzer). Clipboard + folder redirect tested. See
>   `docs/remote_access.md` for the validated playbook + per-client scaling
>   instructions.
>
> Status as of 2026-04-28 (still current):
> - **Stream A complete (2026-04-26)** — Sunday Briefe-Workflow walkthrough
>   transcript extracted + grounded across 6 canonical research streams
>   (KIM/eArztbrief, ePA, Hybrid-DRG/Sanakey, Krebsregister/Tumorscout,
>   QM-Richtlinie, EBM/GOÄ Brief-Ziffern). See `docs/transcript_2026-04-26.md`,
>   `docs/processes_observed.md`, `docs/regulatory_landscape.md` §§ 12–17.
> - **Billing rules updated** — GOP 26310 typo fixed, 8 new GOPs added
>   (26311, 33042, 33043, 01601, 86900, 86901, 01647, 01648, 01431),
>   2 new rule functions (`kim_quartal_cap` for the 23,40 €/Q cap;
>   `abolished_gops` flagging GOP 01660 since 30.06.2023).
>
> Status as of 2026-04-24 (still current):
> - **Public site live** at https://praxisdoktor-uro-karlsruhe.pages.dev/
>   (Cloudflare Pages; brand-coherent dark-forest palette; mobile-first)
> - **Cloudflare:** Pages project + Tunnel + ingress config provisioned in
>   the `consulting@liminality.space` account. Tunnel token + PUBLIC_API_KEY
>   sit in `tooling/clients/uro-karlsruhe/cloudflare.env` (gitignored).
> - **rc2 installer artifact built** (`PraxisDoktorSetup-2.0.0-rc2.exe` on
>   the GitHub Actions run). CI smoke test fails at the same NSSM
>   service-registration issue as rc1 — known, doesn't affect the binary.
> - **Internal app: 5 real co_pilot tools wired** — patient_intake (live
>   from v1), termin_uebersicht (booking ingest), anamnesebogen (form
>   ingest), patientenakte (read-only MO mirror via mock adapter),
>   rechnungspruefung (Plausibilitätsprüfung engine, now 13 sourced rules).

This document captures only the items that genuinely require your hands
or your accounts. Everything else is automated, documented, or in a state
where a future Claude session can pick it up from the docs alone.

---

## 1. Domain migration — Papa-dependent, not urgent

**What:** Move `uro-karlsruhe.de` nameservers from current registrar to Cloudflare.

**Why blocking:** The `app.uro-karlsruhe.de` DNS CNAME → tunnel can't be created
until the zone lives in your CF account. Without it, the public site can't
talk to the practice server (forms will fail with DNS error).

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

## 2. On-site at Papa's practice (whenever the visit happens)

### 2a. Run the Windows installer

Bring with you:
- The `.exe` from the rc2 release (or rc3 if shipped). Download via
  `gh run download <run-id>` from the Actions UI; latest is
  `PraxisDoktorSetup-2.0.0-rc2`.
- The tunnel token from `tooling/clients/uro-karlsruhe/cloudflare.env`
  (line `TUNNEL_TOKEN=...`)
- The PUBLIC_API_KEY from the same file

On the practice server:
1. Run the installer. At the "Cloudflare-Tunnel" wizard page, paste the
   tunnel token. (Or run silently:
   `PraxisDoktorSetup-2.0.0-rc2.exe /VERYSILENT /TUNNEL_TOKEN=eyJh...`)
2. After install, edit `C:\Program Files\PraxisDoktor\var\public_api_key.txt`
   to contain the PUBLIC_API_KEY value (overwriting the auto-generated one),
   then restart the App service: `Restart-Service PraxisDoktor-App`.
3. Verify all four services running: `Get-Service PraxisDoktor-*`

### 2b. Extract the Medical Office schema

Run `tooling/extract-mo-schema.sh` on the practice server with credentials
to the MO MariaDB database. Produces `mo_schema_YYYYMMDD.json`. **USB it back
to your machine** — never goes over the network.

When the JSON lands, mapping its column names into
`server/app/medical_office/mariadb.py` is the single edit that switches
**both Patientenakte and Rechnungsprüfung** from mock to live data
simultaneously. The interface is already stable.

### 2c. Walk through one Rechnungsprüfung session with Papa

Capture: which positions does he commonly bill, which Beanstandungen does
the PVS-Verrechnungsstelle send back, which rules from `docs/billing_rules.md`
"blocked on data extension" tier matter most. The rule engine architecture
in `server/app/billing_rules/` is built for adding rules cheaply — the
session output becomes new `rules_*.py` modules.

### 2d. ✅ Cloudflare RDP tunnel — DONE (2026-04-29)

Validated end-to-end. David can RDP into `SERVERMO` from anywhere via:
1. Mac terminal: `cloudflared access rdp --hostname rdp-uro-karlsruhe.liminality.space --url localhost:23389`
2. Windows App → `localhost:23389` → `david-consult` / password (in Keychain)

Full validated playbook + per-client scaling instructions for client #2
(Barbara) in `docs/remote_access.md`. No further on-site work needed for
remote-access setup.

---

## 3. Optional polish before showing Papa

The public site has placeholder content where Papa-confirmed real data should
go. Find them: `grep -rn TODO public/src/lib/practice.ts`

- Address (street + ZIP)
- Phone, fax, email
- Dr. Bruckschen's full first name
- Hero / team photos (likely already have rights to MG_1548 + MG_1796 from
  `_reference/old-site/assets/`; confirm with Papa, then move into `public/static/`
  and reference them from `+page.svelte` / `team/+page.svelte`)

The site is presentable as proof-of-concept right now.

---

## 4. Things that are explicitly NOT blocking

- ❎ Cloudflare R2 — activated, unused (no use case yet)
- ❎ `cloudflared tunnel login` — the new-client.sh script uses the CF API
  directly via wrangler's stored OAuth token, no browser auth needed
- ❎ Manual DNS records in CF — script handles them once zone is added
- ❎ Email Routing setup — deferred until we actually build email-triage
- ❎ Build pipeline for the public site — `bun run deploy` from `public/`
  works with the per-client `.env` already in place
- ❎ Fixing the CI smoke-test NSSM-services-not-registering issue — the
  installer artifact builds fine; only the post-install probe step fails.
  Investigate when convenient; not urgent because real-Windows-box install
  is the true smoke test anyway.
- ❎ Updating EBM rules quarterly — current set is sourced for Q1/Q2 2026;
  next research pass before Q3 2026.
