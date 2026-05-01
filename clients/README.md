# clients/

Per-practice discovery material: raw transcripts, links, observations, and
anything else worth tracking in git as we map a new practice's workflow.

This is **separate** from `tooling/clients/<slug>/`, which is gitignored and
holds Cloudflare/secret config. Same slug per practice; different purposes:

| Path | Tracked? | Holds |
|---|---|---|
| `clients/<slug>/` | yes | transcripts, contact, observations, plans |
| `tooling/clients/<slug>/` | no (gitignored) | env files, tunnel tokens, DB extracts |

## Slug convention

`<firstname>-<lastname>` for solo/named practices (e.g. `barbara-kochendoerfer`),
or the practice's own short name where it has one (e.g. `uro-karlsruhe` —
Papa's practice, which predates this folder and currently lives only under
`tooling/clients/`).

## What goes inside `<slug>/`

Whatever helps. No fixed schema yet — the structure will firm up after a few
practices. Typical files: `interview-YYYY-MM-DD.md`, `links.md`, `notes.md`.
