---
name: IT vendor communication pattern
description: How David handles existing IT guys at client practices — call first, PDF after, play by their rules where possible
type: project
originSessionId: f5bdb875-89ff-475c-b6fa-6c94427cf63b
---
# IT vendor communication pattern

**Core principle**: Use the IT guy's infrastructure where it exists, own it where it doesn't.
David's role is the software-automation layer — data extraction, process optimisation, web tools.
IT infrastructure, network security, and system maintenance stays in the IT guy's domain.

**Why this matters**: German medical practices almost always have an external IT-Dienstleister
on a service contract. He feels responsible for server security and has the power to undo David's
work or poison the client relationship. Treat him as a professional peer, not an obstacle.

## Three archetypes

- **Typ A (Territorial)**: Sees David as a threat to his contract. Needs formal written
  communication with the doctor CC'd so he can't quietly block. Doctor CC is protective.
- **Typ B (Pragmatisch)**: Busy, doesn't care as long as nothing breaks. Two-minute read max.
- **Typ C (Kollaborativ)**: Technically curious, will ask good questions. Rare but valuable —
  may become a referral source (works with 10-20 practices).

## Standard per-client procedure

1. **During intake**: ask doctor "Hat Ihre Praxis einen IT-Dienstleister? Ich bräuchte kurz
   seinen Namen und E-Mail-Adresse." Normalise this — it signals professionalism before arrival.
2. **Call Papa/doctor first**: align on what was told to the IT guy, get IT contact details,
   confirm doctor is fully on board before you explain anything to anyone else.
3. **Call IT guy within 48h of on-site visit** — phone first, email after. Structure:
   - Beat 1: introduce yourself, explain you're calling directly out of respect
   - Beat 2: one sentence on what you installed, then pause and let him respond
   - Beat 3: "Ich möchte konform mit Ihren Sicherheitsprinzipien bleiben — gibt es etwas,
     das ich beachten sollte?" — invite him into the conversation
4. **Send PDF briefing same day** — subject: "Information zum Fernzugriff — wie besprochen"
   Template: `PraxisDoktor/docs/it_briefing_template.md`
5. **Store contact** in `tooling/clients/<slug>/contacts.md` (gitignored) with any specific
   security requirements he mentions.

## On VPN vs. Cloudflare tunnel

If the IT guy manages VPN access: use his VPN once it's available, remove the Cloudflare tunnel.
Tunnel is a temporary bridge, not a parallel permanent infrastructure. This minimises his
coordination surface and keeps the relationship clean.

**Why:** "Ich möchte keine parallele Sicherheitsinfrastruktur aufbauen, die Ihrer Arbeit
widerspricht. Sobald Sie mir den VPN-Zugang geben, deinstalliere ich meine Lösung."

## Key German phrases

- Role framing: "Ich bin für die Software-Automatisierungsschicht zuständig — Datenauswertung,
  Prozessoptimierung. Die IT-Infrastruktur bleibt vollständig in Ihrem Bereich."
- Invitation: "Gibt es Sicherheitsprinzipien, die ich beachten sollte?"
- VPN handover: "Sobald Sie mir den VPN-Zugang geben, deinstalliere ich meine Lösung."
- Email subject after call: "[Thema] — wie besprochen" (anchors written doc to human conversation)

## Current status — uro-karlsruhe (Papa's practice)

- IT guy contact: pending (waiting for Papa to provide name + email)
- VPN account: IT guy was tasked with setting one up — status unknown
- Plan: call Papa → call IT guy → send PDF → switch to VPN when ready → clean up tunnel
