---
title: "ARRP Project Console"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# ARRP Project Console

The Project Console is a read-only, nonauthoritative management and
verification interface for ARRP. Its complete product and information-
architecture contract is
[`framework/project/interfaces/project-console.md`](../../framework/project/interfaces/project-console.md).
This README is limited to implementation and operator guidance; it does not
independently define screen meaning, authority, status, or data ownership.

## Current interface map

The six primary screens are:

1. **Overview** — dated current project brief, seven-stage automation chain,
   five operational indicators, work-only queue counters, and recent material
   artifact changes.
2. **Action Items** — deterministic Priority attention followed by the
   complete unresolved human-owned decision and intervention inbox.
3. **Progress** — current Review Ready measurement, development-level board,
   trajectory, compact hold counts, and routine monitoring.
4. **Planning** — Workbench, Preliminary Candidates, Candidates, Sources, and
   Publication, without an aggregate main-tab count or new planning authority.
5. **Integrity** — the exact current Project Integrity report and findings.
6. **Operations** — Overview, Agents & Bots, Repository gates, Security,
   Capacity, Platform, Data, and the compact horizontal-menu Logs workspace.

Logs defaults to Operational Incidents, followed by the retained specialist
histories in one bounded newest-first master/detail surface. Incident view
defaults to unresolved and retains complete history; the newest matching record
is selected automatically. Source and action workflows use the same
compact-list/adjacent-preview model where individual inspection is required.
Publication concerns remain in Planning > Publication. Old
Candidates, Sources, Publication, Planning > Next Work, Progress > Next Work,
and Logs routes redirect semantically to their consolidated destinations.

Planning > Workbench is the shared contextual action surface, with Pipeline as
its default typed, read-only work-sequencing category. Active
Pipeline orders preliminary candidates, formal candidates, and below-ready
proposals deterministically; its alternate mode contains exact Blocked and
Deferred records with audit-derived hold provenance. The browser does not
invent membership, readiness gaps, hold facts, or dates from narrative text.

Design mode keeps its exit control in view while scrolling and lets compatible
Overview portlets move among the main flow, Operational indicators, and the
lower row. Navigation status conditions use fixed-size accessible colored dots
instead of variable-width status text. A number appears only for an actionable
queue owned by that destination; inventory, history, and role totals do not
become navigation badges. Exact Blocked or Deferred workflow Status alone does
not trigger the red blocker dot.

The five Current Project Brief dates each carry their own accessible health
dot. Green is healthy or ready, yellow is an exact intentional Pause, red is a
confirmed failure or applicable blocker, and gray means the determination
cannot be made reliably. The latest scheduled occurrence controls both its
date dot and the general Current/Paused/Failed/Unknown badge; the Console never
infers Paused merely because no run appeared.

The Console reports automation state but does not directly control the runner.
Operations Overview combines owner-only Run/Paused state, one compact
seven-stage run strip, seven cadence-aware persistent-role cards, and current
exceptions. Agents & Bots shows one role at a time through a compact horizontal
menu and exposes concise purpose, execution, recovery, and
browser-local non-secret configuration controls. Edited configuration is
exported for review; it does not silently replace repository or installed host
state. The
ordinary user-facing vocabulary is `Run / Paused`; no user-facing `Disabled`
state is defined. Any future control requires a separate authority and
host-state implementation review.

Repository gates are produced once for both authenticated Console refresh and
coordinator enforcement from the append-only typed gate declarations and a
complete paginated live pull-request readback. Current future-run gates do not
rewrite the historical latest attempt. Security remediation is a separate
private authenticated Operations ledger and Action Items cross-index; it is
not folded into the exact Project Integrity report.

Platform status uses one shared provider-neutral projection on Overview and
Operations. Its five compact cells cover GPTs, Codex, API platform, the
registered Vercel dependencies for ARRP intake, and the exact Cloudflare
Turnstile component. Each official provider refresh fails independently;
missing registered components remain gray and retained observations are dated
as last-valid rather than presented as current. Provider advisories do not by
themselves establish an ARRP outage or Operational Incident.

The checked-in Console data is a minimized public operational summary. The
builder gates the complete catalog and every domain file as one exact
generation before replacement. Full runtime configuration and raw operational
logs are written afterward to `data/private-operations.js`; authenticated
GitHub security state remains in `data/private-github-security.js`. Both files
are Git-ignored, secret-scanned before persistence, loaded only by the local
Console origin, and excluded from the public generation manifest. The public
bundle therefore remains useful without using browser hiding as a privacy
boundary.

Operational Incidents has one immutable structured event authority and one
deterministic current projection. Operations, Logs, and Overview repeat the
same deduplicated unresolved count as navigation cues. Every unresolved
incident enters Action Items, but only incidents with explicit human ownership
enter My items or the Human Action Items count; non-human and unassigned
incidents remain under Oversight. Specialist links use producer-supplied typed
incident IDs. Unavailable or incomplete incident data renders unknown, never
zero or healthy.

## Authority

Every view is an assembled projection:

- GitHub Issues and the ARRP Project own lifecycle and workflow fields.
- Candidate workflows and the Horizon Scan Log own intake and disposition.
- Source inventories own bibliographic records.
- Project Integrity output owns Integrity findings.
- Automation runbooks and typed run records own execution meaning.
- The Operational Incident event record owns incident identity, occurrences,
  lifecycle, recovery evidence, and closure.
- Canonical Markdown logs own retained histories.
- Page front matter and print assembly configuration own publication.
- The Console Development Log owns the human-readable index of material
  Console product changes; Git owns exact diffs.

Correct a discrepancy at its owning record or producer and rebuild. Do not edit
generated JavaScript by hand.

## Data loading

The interface is Overview-first and works from `file://`. The shell loads a
bounded compatibility catalog and application script, then lazily injects
`data/overview.js`. Opening a specialist screen loads only its required domain
files.

All generated domains declare a shared generation identity and are validated
against `data/generation-manifest.json`. Required feeds fail closed on
incompatible structure, mixed generations, hash mismatch, or declared
incompleteness. Unavailable values remain unavailable rather than becoming
zero.

The normal initial budgets are:

- no more than 520 KiB of synchronous JavaScript;
- no more than 1,500 initial DOM elements;
- at most 50 Source Checker rows rendered at once;
- no specialist catalog, dossier, log, or publication rows before activation.

## Rebuilding

Rebuild the complete projection:

```sh
python3 scripts/build_horizon_review_console.py
```

Refresh the authenticated GitHub snapshot only in the approved host context:

```sh
python3 scripts/build_horizon_review_console.py --refresh-github
```

For Console-only presentation changes that must not rewrite the separately
deployed public-input lookup:

```sh
python3 scripts/build_horizon_review_console.py --console-only
```

The production transaction performs its final Project Integrity validation and
feed generation after Elim, then builds the Console from that same final
state. Prior bounded Integrity history is retained from the trusted generated
local feed.

## Local-only status and preferences

The runner may write ignored `data/local-automation-status.js`. Its absence is
shown as `Unavailable`, never as healthy. It is an independent status
projection, not repository authority.

Grid width and ordering, disclosure defaults, inbox pane placement, and intro
visibility are device-local browser preferences. Design mode offers safe full,
half, third, quarter, and compact widths where a section or card can resize
without breaking its interaction model. Responsive safeguards may widen a
personal choice on smaller screens. These preferences never alter canonical
records or another user's Console; adopting a settled layout as the project or
future public default requires a separate reviewed repository update.

## Product change traceability

Material Console changes receive a stable `CONSOLE-YYYY-NNN` ID and are
recorded in
[`console-development-log.md`](../../framework/records/automation/console-development-log.md).
Semantic implementation commits use:

```text
Console-Change-ID: CONSOLE-YYYY-NNN
```

The log records full implementation commits, accepted/proposed state,
validation, and rollback baseline. Routine generated data refreshes and
ordinary operational status changes are excluded. Its source uses structured
heading entries; same-day work in one change area is ordinarily consolidated
unless it has a distinct review or rollback boundary.

## Opening and validation

Open [`index.html`](index.html) directly or through a temporary local static
server for browser verification. Before accepting a material Console change,
run the focused frontend/data-contract checks, deterministic Console build,
full repository suite, consistency audit, diff validation, route checks,
keyboard/focus checks, and desktop/mobile visual review required by the
governing product contract.
