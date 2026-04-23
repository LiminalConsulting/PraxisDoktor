# Roles and Processes

The abstract role taxonomy used to scaffold the system before real people are assigned, plus the initial process inventory and the access matrix between them.

This document is **deliberately abstract**. Real names, real headcounts, and final phase decisions get filled in during the in-person discovery with Papa and Dr. Bruckschen. Until then, the system is built against this abstraction so that mapping real people onto it later is configuration, not code.

## Role Taxonomy

Estimated for a German urology Praxis with two Inhaber and ~8–10 total staff. Roles are functions, not people — one person may hold multiple roles (typical: a Praxismanager who also handles Abrechnung).

| Role ID | Display name | Function | Estimated headcount |
|---|---|---|---|
| `praxisinhaber` | Praxisinhaber | Owner-operator. Sees everything. Final authority on financials, personnel, clinical strategy. | 1–2 |
| `arzt` | Arzt | Practicing physician (may or may not be Inhaber). Sees clinical workflows, no financial admin. | 1–3 |
| `mfa_empfang` | MFA Empfang | Front desk: phone, check-in, appointment booking, intake handoff. | 2–3 |
| `mfa_behandlung` | MFA Behandlung | Treatment-room assistant: prep, materials, point-of-care support during exams. | 2–3 |
| `mfa_abrechnung` | MFA Abrechnung | Billing, Krankenkassen communication, invoice generation. | 1 |
| `praxismanager` | Praxismanager | Operations: scheduling, personnel, supplier relationships, often combined with Abrechnung in this size. | 0–1 |

Six abstract roles. A real person may hold any subset (e.g. an MFA who covers both Empfang and Behandlung gets both role IDs assigned to their account).

## Placeholder Accounts (for development)

The seed script creates one account per role with a memorable password, so each role's view can be exercised end-to-end during the build. These are replaced before any production deployment.

| Username | Roles | Password (dev only) |
|---|---|---|
| `dr_inhaber` | `praxisinhaber`, `arzt` | `praxis123` |
| `dr_angestellt` | `arzt` | `praxis123` |
| `mfa_anna` | `mfa_empfang` | `praxis123` |
| `mfa_bea` | `mfa_behandlung` | `praxis123` |
| `mfa_clara` | `mfa_abrechnung` | `praxis123` |
| `manager_dora` | `praxismanager`, `mfa_abrechnung` | `praxis123` |

A 7th account `admin` with role `praxisinhaber` exists with the same password for system administration during dev. All passwords are forced-rotated at first real deployment.

## Process Inventory

The initial set of processes the system tracks. Each appears as a card on the dashboards of the listed roles. Phase indicates how far along the deployment curve each process is.

| Process ID | Display name | Surface | Phase | Inputs | Outputs |
|---|---|---|---|---|---|
| `patient_intake` | Patientenaufnahme | tool | co_pilot | audio, image, text | structured_record, clipboard |
| `rechnungspruefung` | Rechnungsprüfung | tool | co_pilot (planned) | file, text | structured_record, clipboard |
| `team_chat` | Team-Chat | conversation | co_pilot (live day-1) | text, audio, file | notification |
| `termin_uebersicht` | Termin-Übersicht | dashboard_only | dashboard_only | (read from existing scheduler) | notification |
| `anamnesebogen` | Anamnesebogen-Verwaltung | dashboard_only | dashboard_only | image, file | structured_record |
| `krankenkassen_abrechnung` | Krankenkassen-Abrechnung | dashboard_only | decline (initially) | (observed only) | notification |
| `materialverwaltung` | Materialverwaltung | tool | placeholder | text, structured_record | structured_record, notification |
| `personal_schichtplan` | Personal & Schichtplan | tool | placeholder | text, structured_record | structured_record, notification |
| `email_triage` | E-Mail-Triage | tool | placeholder | text, file | notification, clipboard |

"Placeholder" means the card exists, the route exists, the empty tool view renders, but no functionality is built yet. They will be built one at a time as real needs are confirmed with the practice.

"Decline (initially)" for Krankenkassen-Abrechnung means: we observe and surface state, but do not attempt to automate the actual billing submission. This protects the offer from scope-creep into a regulated process where the cost of error is high and the benefit unclear at this stage.

## Access Matrix

Which roles see which processes on their dashboard.

| Process ↓ / Role → | praxisinhaber | arzt | mfa_empfang | mfa_behandlung | mfa_abrechnung | praxismanager |
|---|---|---|---|---|---|---|
| `patient_intake` | ✅ | ✅ | ✅ | ✅ | — | — |
| `rechnungspruefung` | ✅ | — | — | — | — | — |
| `team_chat` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `termin_uebersicht` | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| `anamnesebogen` | ✅ | ✅ | ✅ | — | — | — |
| `krankenkassen_abrechnung` | ✅ | — | — | — | ✅ | ✅ |
| `materialverwaltung` | ✅ | — | — | ✅ | — | ✅ |
| `personal_schichtplan` | ✅ | — | — | — | — | ✅ |
| `email_triage` | ✅ | — | ✅ | — | — | ✅ |

Reading principle: a cell is `✅` if a person in that role would *naturally interact with* that process during normal duties. `praxisinhaber` sees everything as a baseline (single point of accountability). Other roles see only what is directly relevant — this is the "identity-scoped lens" principle from the Liminal Consulting deployment method, not a security model. (Security is enforced at the API layer; the matrix governs visibility.)

## How This Drives the Code

The seed script:

1. Inserts the six roles into the `roles` table.
2. Inserts the six placeholder users into `users`, hashed with argon2.
3. Inserts the user-role assignments into `user_roles`.
4. Inserts the nine processes into `processes` with their declared metadata.
5. Inserts the access matrix into `process_role_access`.

The dashboard query for a logged-in user is then:

```sql
SELECT p.* FROM processes p
JOIN process_role_access pra ON pra.process_id = p.id
JOIN user_roles ur ON ur.role_id = pra.role_id
WHERE ur.user_id = :current_user
ORDER BY (user's saved layout)
```

Adding a person to a role, removing a role from a process, or onboarding a real new employee are all data changes. No code change required. This is the "configuration, not code" property the abstraction was designed for.

## Real-People Mapping (deferred)

When the practice is onboarded, an admin session with Papa fills in:

- Real names → which placeholder account each replaces (or new accounts created)
- Confirmation of who holds which role(s)
- Confirmation or correction of the access matrix above based on actual practice flow
- Phase transitions for any process where Papa wants to upgrade or downgrade the default

This is a 30-minute conversation, not a development task.
