# Process Ontology

The grammar of the system. Every tool, chat, dashboard view, and feedback signal is an instance of the primitives defined here. If a new feature can't be expressed in this vocabulary, the vocabulary is wrong — not the feature.

## Core idea

A practice is a set of **processes** carried out by **people in roles**. Each process has a **surface** through which it is enacted, and each enactment produces a **transition** in that process's state. A subset of those transitions are **feedback signals** that improve the system over time.

There is no separate "team chat infrastructure" or "tooling infrastructure" — both are processes with different surfaces. This is the deduplication that lets the system stay small as it grows.

## Primitives

### Process

A unit of organizational work that can be named, scoped to specific roles, and meaningfully tracked over time.

| Field | Meaning |
|---|---|
| `id` | Stable string key, e.g. `patient_intake`, `team_chat`, `rechnungspruefung` |
| `display_name` | Human-readable, German |
| `icon` | Symbol shown on the dashboard card |
| `surface` | One of: `tool`, `conversation`, `dashboard_only` |
| `roles` | List of role IDs allowed to see/use this process |
| `chat_attached` | Boolean — does this process have its own thread (almost always yes) |
| `inputs` | Typed list of accepted input kinds (see Input/Output Types) |
| `outputs` | Typed list of produced output kinds |
| `phase` | One of: `decline`, `dashboard_only`, `co_pilot`, `autonomous` |
| `activity_signal` | What counts as "new activity" for the dashboard indicator (see Activity Signals) |

A process is **declared once** in code; instances of that process (a specific patient intake session, a specific Rechnungsprüfung run) are rows in the database carrying state.

### Role

An abstract function in the practice. Roles are not people — people are assigned one or more roles via their account.

| Field | Meaning |
|---|---|
| `id` | Stable string key, e.g. `arzt`, `mfa_empfang`, `praxisinhaber` |
| `display_name` | German label shown in the admin UI |
| `description` | One sentence describing the function |

Real role assignments to real people are configured by the admin (initially Papa) through the admin surface. Until the practice is onboarded with real names, placeholder accounts are used.

### Surface

How a process is rendered to a user. Three kinds, no more:

- **`tool`** — Specialized UI for doing the work. Has inputs, outputs, a current state, and an editable region. Patientenaufnahme, Rechnungsprüfung. Each tool is a card on the dashboard and a full-screen view when entered.
- **`conversation`** — Append-only message log with an input box. The team chat is the canonical example, but each `tool` process *also* has a conversation surface attached (the "chat panel" that slides in from the right). A standalone `conversation` process is one whose primary surface is the chat itself.
- **`dashboard_only`** — Read-only summary visible on the dashboard but with no full-screen tool yet. Used for processes that are observed but not yet automated. A `dashboard_only` process becomes a `tool` process by promotion, not by replacement.

### Input/Output Types

The closed set of kinds of data flowing into and out of processes. Adding a new type is a deliberate vocabulary change, not a per-process invention.

| Type | Examples |
|---|---|
| `audio` | Patient conversation recording, voice message in chat |
| `image` | Anamnesebogen scan, ID photo |
| `text` | Manually entered field, chat message body |
| `file` | PDF invoice, lab result attachment |
| `structured_record` | Extracted patient stammdaten, validated invoice |
| `db_write` | Direct write to the practice's MediOffice or other system of record |
| `clipboard` | Copy-to-clipboard for human-mediated transfer (the co-pilot pattern) |
| `notification` | A message surfaced to a role, e.g. "review needed" |

### Transition

The atomic unit of meaningful change in a process instance. Append-only. Every Tier 2 undo/redo and every feedback signal derives from this stream.

| Field | Meaning |
|---|---|
| `id` | UUID |
| `process_instance_id` | Which instance this transition applies to |
| `actor` | User account that triggered it (or `system` for automated) |
| `timestamp` | When |
| `type` | A symbol from the closed set per process (see below) |
| `payload` | JSON describing what changed |
| `feeds_back` | Boolean — should the feedback subscriber consume this? |
| `retracted_by` | Optional UUID of a later transition that undoes this one |

Transitions are **immutable**. An undo does not modify or delete a transition — it appends a new transition of type `undo` whose payload references the one being undone. Redo appends a new transition referencing the undo. This gives perfect history, perfect audit, and perfect retraction of feedback signals (a retracted positive becomes a non-signal; the original event is preserved for forensics).

### Process state (current)

Every process instance has a `current_state` JSON column for fast UI rendering. It is **derivable** from replaying the transitions, but cached for performance. Invariant: the state cache must always equal the replay result. Any divergence is a bug, not a tolerated drift.

## Activity Signals

What lights up the "new activity" indicator on a dashboard card. Per-process declaration of which transition types count:

| Process kind | Default activity signal |
|---|---|
| `tool` | New chat message in attached chat OR new system event needing role attention (e.g. extraction complete) |
| `conversation` | New message since user last viewed |
| `dashboard_only` | New entry in the underlying observed feed |

When a card has an activity indicator and the user double-clicks it, the relevant pane opens immediately to the source of the indicator (e.g. the chat panel auto-opens if the indicator was a chat message).

## Feedback as a Subset of Transitions

The feedback subsystem is **not a separate data path.** It is a subscriber to the transition log filtering for `feeds_back: true`.

```
Tier 2 transitions  ⊇  Feedback signals
```

This means:

- A user correcting a wrongly-extracted field produces one transition. That transition is `feeds_back: true`. The feedback table is a view over such transitions.
- A user undoing that correction appends a new `undo` transition. The original transition's `retracted_by` is set. The feedback view automatically excludes retracted positives/negatives.
- No double-bookkeeping. No risk of feedback and UI state ever disagreeing.

The specific transition types that are `feeds_back: true` are declared per process. For Patientenaufnahme:

| Transition type | feeds_back |
|---|---|
| `field_accepted` | yes (positive: the extraction matched what the user wanted) |
| `field_rejected` | yes (negative: the extraction was wrong, no better answer given) |
| `field_corrected` | yes (negative + corrective: extraction was wrong, here is the right value) |
| `session_started` | no |
| `session_marked_done` | no |
| `chat_message_sent` | no (chat has its own model, see below) |

## Chat as a Process Surface

Every process has a chat attached, scoped to that process. The team-wide general chat is itself a process (`team_chat`) whose surface is `conversation` and whose roles include everyone.

Chat messages are transitions of type `chat_message_sent` with payload `{body, attachments, mentions}`. Chat does not participate in the Tier 2 undo/redo model — once sent, a message is sent (with optional edit history if needed later). This is intentional: chat is communication, not state mutation.

The agent reads chat transitions across all processes to surface coherence gaps ("this question keeps being asked — the UI should have answered it"), as established in the Liminal Consulting deployment-method principles.

## Two-Tier Undo/Redo Model

**Tier 1 — Per-input native history.** Each text/number/select input owns its own keystroke-level history via the browser. `Cmd-Z` while focused undoes typing within that field. We do not augment or merge this.

**Tier 2 — Per-process transition history.** When no field is focused, or via an explicit ↶ button on the tool's chrome, `Cmd-Z` pops the most recent transition for the current process instance and appends an `undo` transition.

The two tiers do not interact. A keystroke is never a Tier 2 transition; a Tier 2 transition is never a keystroke.

A field replacement (user types over an extracted value) is committed as a single Tier 2 transition of type `field_corrected` on `blur` or `Enter`, with payload `{from, to}`. Mid-typing keystrokes stay in Tier 1.

## What Is Out of Scope of This Ontology

- The wire format of API calls — implementation detail
- The schema of `current_state` JSON for each specific process — declared per process
- The visual styling of cards / tools — design layer, not grammar
- Cross-process workflows ("when X happens in process A, do Y in process B") — handled later by an agent layer reading transitions; the ontology supports it but does not encode specific rules

## Adding a New Process

To add a process to the system:

1. Choose an `id`, `display_name`, `icon`, `surface`
2. Declare its `roles`, `inputs`, `outputs`, `phase`, `activity_signal`
3. Declare its set of transition types and which are `feeds_back: true`
4. Implement the surface (a Svelte component for `tool` or `conversation`; nothing for `dashboard_only` beyond the card)
5. Implement the state-cache projection from transitions

No changes to the dashboard, auth, chat, or feedback subsystems are required. That is the whole point.
