---
title: "ARRP Project Console"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# ARRP Project Console

The Project Console is a read-only, nonauthoritative management and
verification interface for ARRP. Its complete product and information-
architecture contract is
[`framework/project/interfaces/project-console/specification.md`](specification.md).
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
   Capacity, Platform, Data, Component Registry, and the compact
   horizontal-menu Logs workspace.

Logs defaults to Operational Incidents, followed by the retained specialist
histories in one bounded newest-first master/detail surface. Incident view
defaults to unresolved and retains complete history when its owner projection
is complete; public shells retain the route but show incident feeds and counts
as unavailable. The newest matching record is selected automatically. Source
and action workflows use the same
compact-list/adjacent-preview model where individual inspection is required.
Those public shells use one concise explanation:
`Data unavailable outside the bound owner-local Console.` Detailed feed
diagnostics remain confined to a valid owner Console.
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

The brief and Operations chain consume one versioned occurrence directory.
Each occurrence keeps its trigger, schedule identity, status, revision,
timestamps, blockers, and seven ordered stage results together. The current
scheduled occurrence is never combined with an older push run, and `Not due
this chain` never becomes `Succeeded` merely because a prior run succeeded.
Next-run, full-Review-Epoch, valid-until, and trustworthy-through facts are
producer supplied.

Operations > Component Registry follows Data and precedes Logs. It has
Documents, Directories, Routing, and Terminology modes, all rendered from one
typed snapshot produced from the exact candidate accepted by
`scripts/component_registry.py`. The browser formats supplied facts only; it
does not invent taxonomy, directory membership, context routes, identities, or
remediation. Routing includes the producer-rendered Stage 1 catalog: schema
version 2, catalog version 1, and 64 stable rules divided across Invariants
(7), Selection (17), Validation (10), Failure rules (10), Currentness (6),
Budgets (4), and Comprehensive review (10). Historical rule provenance remains
bound to the frozen predecessor digest
`246a2bc927fa232507ac733192c42f42e469557b3b25cd92d74c111ef6d5e4a7`.
Candidate configuration remains explicitly predecessor-bound; after
activation, the embedded Component Registry route is the sole current routing
authority. Artifact classification and lifecycle enforcement
remain deferred, so the feature displays
`Classification pending — enforcement not active` and treats empty deferred
namespaces as unavailable rather than zero. The feature has no Overview
portlet. Its `component-registry.js` shell module and generated
`data/component-registry.js` domain are both lazy; the owner builder copies
both for direct `file://` use. Legacy
`operations:component-registry:*` document routes normalize one way to the
canonical `automation:component-registry:*` destinations.

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

## Authenticated owner refresh

From a clean canonical checkout, refresh current GitHub Project, Integrity,
repository, and Console projections with:

```text
python3 scripts/refresh_project_console.py
```

The command reads the separate Project-only credential from its fixed macOS
Keychain entry and injects it only into the exact read-only producer
subprocesses. It does not expose the credential to the Console, broaden the
ordinary GitHub CLI credential, or mutate GitHub. It fails before Keychain
access when tracked files are already modified. Any generated tracked changes
must still be committed, regenerated against the exact source revision, passed
through the disclosure gate, and reviewed normally.

Repository gates are produced once for both authenticated Console refresh and
coordinator enforcement from the append-only typed gate declarations and a
complete paginated live pull-request readback. Current future-run gates do not
rewrite the historical latest attempt. Security is a separate minimized
assurance surface and generic Action Items cross-index; provider-native and
owner-local details remain at their protected sources and are not folded into
the exact Project Integrity report.

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
logs are written afterward to `data/private-operations.js`; minimized
security-assurance state is written to
`data/private-security-assurance.js`; and the strict minimized Codex usage
projection is written to `data/private-codex-usage.js`. Provider-native alert content,
credential metadata, affected locations, and remediation evidence never enter
that Console projection. Those files and the local automation-status projection
are Git-ignored and secret-scanned before
persistence, loaded only by the local Console origin, and excluded from the
public generation manifest. The public bundle therefore remains useful
without using browser hiding as a privacy boundary.

The generated Overview also carries a registered queue directory, one public
Action snapshot, a typed Operations Data directory, typed artifact-change
events, and typed capacity points. The bound private Operations projection may
replace the public Action snapshot only with an exact-generation,
exact-revision owner-local join containing generic protected Security actions.
The browser filters and formats these records; it does not invent queues,
categories, identities, owners, routes, activity, or capacity from prose.

Operations > Logs keeps **Governance changes** separate from historical
**Change audits** and **Console development**. Governance Change Log entries
remain public-safe in every Console mode. Only the exact-bound owner-file
Console may join an optional allowlisted safe summary from a matching
owner-local supplement for a selected entry; absent or mismatched supplements
remain unavailable and do not alter or conceal the public entry.

The supported owner mode is an immutable, generation-bound Console copy in the
verified companion workspace's protected owner-Console role, opened directly
with `file://`; no local web server is required. Its exact
`project-console.html` path is bound to one public Console generation and one
source revision. Its binding
also records each copied private projection's SHA-256 digest, availability,
completeness, and exact per-feed relative path, and the loader verifies that
exact envelope before joining the data. A requested feed cannot load through
another registered feed's path, including when two binding entries are
swapped. Only that entrypoint may load the copied, individually enveloped
Security assurance, private Operations, Codex usage, and local automation-status
projections. The Codex usage projection contains only percentages, reset
identity, typed material history, independently available budget and burn-rate
estimates, and explicit coverage and confidence. It contains no absolute
allowance, account identity, prompts, task content, credentials, raw logs, or
owner-local paths. Its schema fixes an opaque producer identity and 30-minute
sampling cadence, treats the earlier of the next sample boundary or reset as
the trustworthy-through limit, and fails unavailable after that instant.
Production staging accepts no caller-selected usage source; it reads the fixed
approved owner-local producer projection and never emits that path. The owner
envelope and browser both verify one canonical semantic payload digest, so
JSON formatting differences do not change identity while a payload change
does. The strict validator, digest implementation, graph, and detailed
Capacity renderer are deferred in public `capacity.js`. It is copied into the
immutable owner snapshot but is not a static entrypoint script, preserving the
655 KiB synchronous startup ceiling and direct `file://` support. The
repository source Console remains public-only even when it is
opened from disk. Loopback HTTP(S) is supported for public-shell and fixture
development, but it does not load owner projections. Hosted/public HTTPS
likewise never requests those files. A future hosted private Console would
require a separate authenticated, deny-by-default service; authentication does
not place private operational state in GitHub.

Operational Incidents and Security Incidents have separate immutable event
authorities and separate deterministic projections. `INC-…` owns operational
impact and recovery; `SEC-…` owns protected security investigation,
containment, remediation, verification, and closure. A typed owner-local
relation journal may connect them for navigation but cannot merge their
identity, lifecycle, counts, evidence, or closure. The owner-file Console
can render each active, complete history in its own Logs view. Public,
repository-source, loopback, and hosted modes show both incident feeds as
unavailable rather than zero. The Security Incident and relation contracts are
currently inactive, so those owner-file feeds also remain unavailable until a
separately activated, complete compatible projection exists. Every unresolved
incident from a complete owner projection enters Action Items, but only
incidents with explicit human ownership enter My items or the Human Action
Items count; non-human and unassigned incidents remain under Oversight.
The public-shell message is
`Data unavailable outside the bound owner-local Console.` It describes the
delivery boundary rather than a remote-service error.

## Authority

Every view is an assembled projection:

- GitHub Issues and the ARRP Project own lifecycle and workflow fields.
- Candidate workflows and the Horizon Scan Log own intake and disposition.
- Source inventories own bibliographic records.
- Project Integrity output owns Integrity findings.
- The validated Component Registry candidate owns its registered documents,
  directory scopes, context-routing import, and explicit deferred namespaces.
- Automation runbooks and typed run records own execution meaning.
- The [ARRP Owner-Local Runtime
  Authority](../../automation/owner-local-runtime.md) owns
  current and staged path resolution, artifact classes, and cutover meaning.
- The Operational Incident event record owns operational identity,
  occurrences, impact, recovery evidence, and operational closure.
- The Security Incident event record owns security identity, investigation,
  containment, remediation, verification, and security closure.
- The incident-relation journal owns only typed reciprocal `INC`/`SEC`
  navigation.
- Canonical Markdown logs own retained histories.
- Page front matter and print assembly configuration own publication.
- The Console Development Log owns the human-readable index of material
  Console product changes; Git owns exact diffs.

Correct a discrepancy at its owning record or producer and rebuild. Do not edit
generated JavaScript by hand.

## Data loading

The interface is Overview-first and works from `file://`. The repository
source opened that way remains a public shell; only an immutable owner version
at its exact bound entrypoint is owner mode. The shell loads a bounded
compatibility catalog and application script, then lazily injects
`data/overview.js`. Opening a specialist screen loads only its required domain
files. Opening the Component Registry subtab first loads its public shell
module and then its separately generated domain; the non-data module is not
treated as a generated domain, while the data file must match the catalog
generation manifest.

All generated domains declare a shared generation identity and are validated
against `data/generation-manifest.json`. Required feeds fail closed on
incompatible structure, mixed generations, hash mismatch, or declared
incompleteness. Unavailable values remain unavailable rather than becoming
zero. Component Registry production generation additionally fails closed when
its validated candidate is stale, when embedded and imported routing differ,
or when the complete directory-scope inventory cannot be established.

The normal initial budgets are:

- no more than 655 KiB of synchronous JavaScript;
- no more than 1,500 initial DOM elements;
- at most 50 Source Checker rows rendered at once;
- no specialist catalog, dossier, log, or publication rows before activation.

## Rebuilding

Rebuild the complete projection:

```sh
python3 scripts/build_project_console.py
```

Refresh the authenticated GitHub snapshot only in the approved host context:

```sh
python3 scripts/build_project_console.py --refresh-github
```

For Console-only presentation changes that must not rewrite the separately
deployed public-input lookup:

```sh
python3 scripts/build_project_console.py --console-only
```

Rebuild only the tracked public Console output without opening, restoring, or
authorizing ignored owner-only projections:

```sh
python3 scripts/build_project_console.py --public-only
```

This mode leaves every owner-only feed explicitly unavailable and cannot be
used as the source for owner Console staging. Stage a new immutable owner
Console version only after an authorized normal owner-bound generation has
separately restored and validated the exact generation-bound owner-only
projections:

```sh
python3 scripts/build_owner_console.py
```

The staging command never overwrites an existing owner version or activates a
host service. Production has no usage-source argument: the builder resolves
only the approved owner-local sampler projection and rejects source
substitution. Test fixtures may inject an explicitly bounded source without
creating a production authority. The command's JSON result identifies the new
version directory; open that directory's `project-console.html` directly.
Missing, malformed, stale, partial, or generation-incompatible private feeds
fail closed and remain visibly unavailable.

The production transaction performs its final Project Integrity validation and
feed generation after Elim, then builds the Console from that same final
state. Prior bounded Integrity history is retained from the trusted generated
local feed.

## Local-only status and preferences

The runner may write ignored `data/local-automation-status.js`. It preserves
the latest occurrence outcome while refreshing the current binary `Run /
Paused` posture from the authoritative owner-only marker. Its absence is shown
as `Unavailable`, never as healthy. It is an owner-staging input, not
repository authority and not a private-data entitlement for the repository
source Console.

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
[`console-development-log.md`](../../../logs/automation/console-development-log.md).
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

Open [`project-console.html`](project-console.html) directly or through a
temporary local static server for browser verification. Before accepting a
material Console change,
run the focused frontend/data-contract checks, deterministic Console build,
full repository suite, consistency audit, diff validation, route checks,
keyboard/focus checks, and desktop/mobile visual review required by the
governing product contract.
