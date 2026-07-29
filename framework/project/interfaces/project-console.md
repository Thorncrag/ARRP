---
title: "ARRP Project Console and Interface Configuration"
status: active
print_status: excluded
print_exclusion_reason: "Internal interface-governance documentation."
module_id: project_interface
load_when:
  - "Designing, changing, or reviewing an ARRP dashboard, console, form, or other application-like interface."
dependencies:
  - "../../standards/interfaces/standard.md"
  - "../../standards/interfaces/progress-views.md"
  - "visual-identity.md"
  - "project-console-progress.md"
  - "../workflows/candidate-review.md"
  - "../workflows/source-adjudication.md"
---

# ARRP Project Console and Interface Configuration

This file configures the ARRP Project Console under the reusable
[Project Interface Standard](../../standards/interfaces/standard.md), the
[Progress View Standard](../../standards/interfaces/progress-views.md), and
ARRP's [tool visual identity](visual-identity.md).

## Project Console Information Architecture

Candidate terminology and identifiers are governed by the
[ARRP candidate workflow](../workflows/candidate-review.md#preliminary-candidate-synthesis-and-promotion),
and the exact source catalogs and routing fields are governed by the
[ARRP source workflow](../workflows/source-adjudication.md). This file governs
where and how those records are presented in project-operated interfaces.

The ARRP Project Console has six primary tabs in this order: **Overview**, a
compact project-wide orientation; **Action Items**, the central linked inbox
for matters requiring human review or intervention; **Progress**, containing
current development status, trajectory, compact hold counts, and monitoring;
**Planning**, a navigation category containing Workbench, Preliminary
Candidates, Candidates, Sources, and Publication; **Integrity**, containing the exact current Project
Integrity report and its findings; and **Operations**, containing Overview,
Agents & Bots, Repository gates, Security, Capacity, Platform, Data, and Logs.

Planning defaults to Workbench and has no aggregate main-tab count. It groups
existing specialist ledgers without creating a new authority or duplicated
record. Public-input records route to Candidates after formal lifecycle
admission and to Preliminary Candidates while no formal candidate exists.
Workbench is the shared contextual planning surface; Pipeline is its default
ordered category. Preliminary Candidates
and Candidates remain the complete dossiers. Sources and Publication use
sections, disclosures, and bounded workspaces rather than additional nested
tab rows. Legacy Candidates, Sources, Publication, Planning > Next Work,
Progress > Next Work, and their deep routes remain supported as semantic
aliases to the corresponding Planning destination and meaningful filter.

Operations > Logs uses one compact horizontal log menu immediately above the
shared bounded newest-first master/detail workspace. It defaults to Operational
Incidents, then retains Horizon, Elim, Bots, Sources, Integrity history, Change
audits, and Console development. Logs is not a main tab and does not introduce
another nested full tab hierarchy.
Legacy log routes
redirect to Operations > Logs. Integrity remains the exact current report;
Integrity under Logs remains retained history.

Those views are nonauthoritative projections: lifecycle and candidate authority remains in GitHub, bibliographic authority remains in the two source catalogs, canonical Markdown logs remain authoritative for their named histories, and the immutable validated Operational Incident event record is the sole authority for incident identity, occurrence history, lifecycle, recovery evidence, and closure. Committed Elim Run Log discovery markers remain the durable gap-reconstruction authority, presidential-directive identity and review history remains in the directive registry, and print disposition and assembly authority remain in page front matter and [`print-assembly.json`](../publication/print-assembly.json). The Publication assignment view must make included, explicitly excluded, unclassified, and conflicting outcomes independently visible. Routine issue monitoring remains in Progress and does not count as a human Action Item unless it produces an exception or decision requiring attention; automated watcher and source-bot operations remain in Sources. Routine Elim-owned gap review, and retained `forbidden`, `unsafe`, `out_of_scope`, or `uncertain` observations that do not require a human act, remain in Integrity or Agents & Bots. They enter Action Items only when an exact human judgment, credential, unsafe external action, owner-gated decision, or intervention is required. Locally staged publication changes remain in Publication and likewise do not count as Action Items. The Action Items view must route each count to its complete owning view and must not duplicate narrative workflow records. The Logs view is read-only, retains complete entries without pagination, and links to each authoritative log or retained bounded feed; it must not become a separately maintained ledger. Publication controls may stage and export instruction lists for Codex, but do not persist drafts or edit canonical files.

### Governance discovery and gap obligations

The Console presents closed-loop governance discovery without creating another backlog or narrative ledger. The primary manager view must distinguish: current governance-discovery mode; the last committed review outcome and time; its next-due time under the 168-hour minimum interval; open, investigating, blocked, human-required, resolved, and human-disposition obligation states; severity; owner; authority classification; separate `permitted`, `human_reserved`, `forbidden`, `unsafe`, `out_of_scope`, or `uncertain` disposition; first seen; last checked; occurrence count; age; exact next action; next trigger; and a canonical-detail link. A current `no_material_finding` review remains visible but must not imply that Elim will relaunch on every poll. Repeated observations remain one stable obligation. A missing later observation, clean aggregate, rebuilt feed, merge, or report-only result must not appear as resolution. Closed rows require visible verified-repair or recorded-human-disposition evidence.

Compact cards and queue rows must link to full canonical detail rather than copy evidence, reasoning, uncertainty, consequence, affected records or surfaces, validation, and provenance. The full record remains available through the Logs projection of the committed Elim Run Log. If the temporary gap cache is missing, stale, or inconsistent with reconstructible committed markers, show the cache as unavailable or rebuilding; never present cache absence as zero gaps. An outside-contribution review must expose the exact reviewed revision and separate results for identity, classification, required fields, canonical linkage, evidence and provenance, lifecycle and authority, generated views, tests, and documentation; a changed head invalidates the earlier ready posture.

Compact portal and metric groups occupy one deliberate desktop row whenever
their labels remain legible. The interface tightens copy, uses smaller spans,
or permits bounded horizontal overflow before allowing an accidental second
row. Multiple rows or stacking are reserved for intentional narrow-screen
layouts. This is a Console-wide rule, not an Overview-only exception: every
portal, metric, role, and compact status group must prefer one intentional
line before wrapping into a second row.

Each proposed-candidate view should be a decision dossier assembled from existing authoritative records: GitHub supplies issue and lifecycle data; the Horizon Scan Log supplies intake history, overlap, rationale, and follow-up; the two source inventories supply evidentiary records; and identifier-linked research supplies project analysis. Display missing inputs as record gaps rather than filling them with generated conclusions. The console may cache this derived presentation data, but it must not become a manually maintained narrative ledger or override its inputs; corrections belong in the record that owns the information. Canonical records and automation status remain read-only to the Console. The retired localhost coordinator control plane has no current authority and must not be exposed as an interface dependency. Manual runs use the owner-controlled installed bootstrap, and the Console may display only the checked-in local-first status projection. A local print-level draft and export is not an implementation; Codex must validate and apply it separately. Conduct every formal candidate decision within Codex under the full Horizon Candidate Adjudication Workflow.

## Monitoring and Source Inspection

GitHub Issues and the Project Monitoring view are the issue-level monitoring-workflow authority. The Console separates issue workflow from source inspection: **Progress** contains the read-only **Issues being monitored** group, while **Sources** contains Court Cases, Presidential Directives, and Source Checks. The Progress group organizes monitored matters by accountable ARRP owner and, where useful, by a named case family, executive-action episode, or other factual matter.

Every view must distinguish: (1) the external matter being watched; (2) why it is materially relevant to future issue development; (3) what development triggers reassessment; (4) whether a deterministic watcher, an LLM-assisted pass, or another stated checking method covers it; and (5) its latest known posture. Routine issue monitoring is intended for automated LLM-assisted review and is not itself a human Action Item merely because `needs: monitoring` remains present. Only a detected development, exception, or resulting decision that requires human attention enters Action Items. The console does not create, close, edit, or adjudicate an issue.

The **Sources** and **Pending sources** subviews expose each source's `Monitoring` value so a changing docket or similar record remains identifiable even when the owning issue is not currently in an issue-wide monitoring pass. Ordinary badges state the complete queue size. A visually distinct update badge states only a genuinely new or changed record awaiting review, using the directive registry status or an unresolved deterministic-watcher pull request; do not use the update color merely to restate a queue total. The substantive distinctions among issue monitoring, source monitoring, deferral, and blockage remain governed by [`monitoring.md`](../../standards/sources/monitoring.md), [`source-records.md`](../../standards/sources/source-records.md), and the [ARRP GitHub workflow](../github/workflow.md).

## Source Projection Refresh

Rebuild the ARRP Project Console whenever candidate data, either canonical
source catalog, a source-monitoring designation, an issue-level monitoring
label, the presidential-directive registry, watcher configuration, a canonical
project log, page-level publication-disposition metadata, or
[`print-assembly.json`](../publication/print-assembly.json) changes.

The Console's progress, source, pending, watcher, integrity, log, and
publication presentations are generated views. A rebuild refreshes those views
but does not create another workflow, source, candidate, log, or publication
authority.

An owner-initiated authenticated refresh uses
`scripts/refresh_horizon_review_console.py`. That entry point has no
caller-selected root or credential: it requires the clean canonical checkout,
reads the dedicated Project-only credential from the fixed macOS Keychain
authority, removes inherited GitHub-token variables, and supplies
`ARRP_PROJECT_TOKEN` only to the exact read-only Progress, Integrity, feed, and
Console producer subprocesses. It performs no GitHub mutation. Missing,
expired, or insufficient Project access fails closed without printing provider
diagnostics or credential material. The ordinary GitHub CLI credential must
not be broadened to satisfy this route. Generated tracked changes still follow
the normal exact-revision commit, regeneration, disclosure, and review
workflow.

## Pending Source Presentation

The **Pending** tab is a small routing-decision view, not a development or monitoring backlog. Each retained row must identify the plausible competing destinations, explain why the project cannot yet choose among them, and state the exact source-specific review needed to decide ownership. Do not group pending records as citation-ready, litigation, monitoring, or general project development: once any one of those records has a clear owner, it belongs in that owner's source-development record and `sources.csv`. The tab projects `sources-pending.csv`; it does not duplicate or supersede the underlying record.

## Whole-Console Product Contract

### Product purpose

The Console is an internal, nonauthoritative management, verification, and
navigation surface. It must let the manager determine:

1. what project data is trustworthy and through what time;
2. whether the latest complete automation chain succeeded;
3. what requires human attention;
4. what changed materially;
5. where the complete specialist record for each summary lives; and
6. which Console revision introduced, changed, moved, or retired a behavior.

It is not a second project-management system, a source of research or
governance authority, a generic portal directory, or an autonomous decision
maker. A projection disagreement is repaired at the earliest owning or
producing layer. The browser must not guess away a contradiction.

### Governing product principles

- **One primary home.** Every complete inventory, history, or diagnostic
  domain has one specialist home. Other screens may summarize and route to it.
- **Assertion plus provenance.** Each changing assertion carries the date and
  identity that qualify it. Interface generation time never substitutes for
  data currentness.
- **Explicit uncertainty.** Use `Last valid retained`, `Stale`, `Incomplete`,
  `Unavailable`, or `Rebuilding` when appropriate. Unavailable never renders
  as zero.
- **Calm by default.** The default emphasizes current truth, human decisions,
  and exceptions. Repetition does not substitute for priority.
- **Shared behavior.** Common dates, states, list selection, master/detail
  interaction, routes, provenance, and responsive behavior are implemented
  consistently.
- **Complete records, bounded rendering.** Logical histories remain complete,
  while long lists scroll or render incrementally inside contained working
  surfaces.
- **Root-cause correction.** A verified flaw in producer order, schema,
  identity, routing, taxonomy, or authority that makes the Console untruthful
  is corrected within the owning project layer.

### Automation occurrence and immutable Overview authority

One versioned automation-occurrence projection binds each exact run identity
to its trigger, schedule identity, status, source revision, generation,
timestamps, blockers, and the seven producer-declared stages in configured
order, including Elim. Compact and detailed chain views consume that same
array. A stage that was not due in the current occurrence remains `not_due`;
an older success may appear only as separately dated history and never changes
the current result to `succeeded`. The producer supplies the exact latest
attempt, latest scheduled attempt, last fully successful occurrence, next
ordinary run, next full Review Epoch, role valid-until, and trustworthy-through
facts. Missing or expired facts are unavailable or stale; browser date
arithmetic and nearest-date substitution are prohibited.

Overview is one immutable, validated projection bound to an exact Console
generation. It owns its generated occurrence summary, queue directory, Action
snapshot, data directory, typed artifact-change activity, and typed capacity
history. Later specialist loads, private joins, live GitHub observations, and
provider-status refreshes may render explicitly labeled current observations,
but may not rewrite those generated facts. `Data current through` is a
producer-declared boundary, not the browser minimum of unrelated generation
timestamps.

### Shared work and queue snapshot

The builder publishes one registered `queue_directory`. Each queue carries a
stable ID and label, count, availability and completeness, exact inclusion
predicate, authoritative source, lifecycle owner, detail route, problem route,
and generation identity. The builder also publishes one typed Action snapshot
used by Overview counts, Action Items groups, Workbench cross-indexes, and
navigation badges. Owner-local Security actions may join only in the
generation-and-revision-bound private Operations projection; the join emits
generic registered Action records and never vulnerability detail. Partial or
missing inputs make the relevant count unavailable rather than zero.

`next_action_missing` and `workflow_status_invalid` are separate registered
conditions. The former alone supplies the Workbench `Next steps not recorded`
count and filter; the latter routes to Integrity while the affected artifact
remains visibly unclassified. Recent material activity consists only of typed
artifact-change events. Capacity history consists only of typed usage points
and explicit Review Epoch identities. Narrative logs, unresolved membership,
or browser regular expressions cannot supply these classifications.

### Console Development Log classification

Each calendar date uses one ISO-date `##` umbrella heading in the Console
Development Log; a Console Change ID or commit subject may not replace the date
as that heading. The umbrella metadata retains every applicable Console Change
ID, title, and relevant implementation commit. Within it, every material change
has exactly one primary `###` category drawn from the registered
`console_development_category` namespace in
[`project-console-classifications.json`](project-console-classifications.json):
Interface & information architecture; Planning & work management; Operations &
automation; Data, provenance & integrity; Security, privacy & disclosure;
Reliability, accessibility & performance; and Governance & documentation.
Only categories changed on that date appear.

Rapid-fire revisions collapse only when they belong to the same coherent
category and change set. Independent architectural, security, operational,
data-contract, or user-facing work remains separately traceable under its
registered category even when completed on the same day. Each category section
records its stable category ID, applicable Console Change ID, applicable commit
IDs, a concise material-change account, and validation. UI or log code may not
invent an additional category or use a display heading as a new classification.
Cross-references do not duplicate a change or its count. GitHub-bound
development records remain public operational summaries and never contain
vulnerability evidence, credential detail, or restricted operational
diagnostics.

The canonical Markdown retains one dated umbrella so shared provenance is
recorded once. The Console projects each materially changed registered category
under that date as a separate selectable log entry and preview, using a stable
date-plus-category identity. It does not collapse the date into one interface
row, duplicate the umbrella metadata into new canonical records, or create one
entry per commit. Category entries retain the date, applicable Change ID,
category-specific commits, lifecycle, state, material change, and validation.

### Typed classification and projection authority

The Console implements the reusable Interface Standard through
[`project-console-classifications.json`](project-console-classifications.json).
The registry has distinct namespaces for work kinds, finding codes, queue IDs,
workflow views, Security tools, and Console-development categories. A builder
must validate every emitted queue, finding, action item, work class, and
cross-screen category before writing a generation. Every actionable record
carries a stable typed identity, registered code, status, owner and attention
class, authority and provenance, canonical destination, generation identity,
exact next action, and resolution predicate. An unknown or incomplete record
fails generation or becomes a registered producer-contract exception routed to
Integrity; the browser cannot coin a fallback.

A classification introduction, semantic rename, merge, alias, or retirement
changes its registry entry, producer schema, consumer and whole-bundle tests,
and the Console Development Log under the same Console Change ID. Stable IDs
are preserved across display renames; an actual semantic replacement records
an explicit migration. The whole-generated-bundle validation enumerates every
classification and destination and proves each displayed count is generated by
the exact destination predicate. Negative fixtures prohibit message-keyword
classification, prose-derived or list-order identity, unregistered category
literals, browser-created queues, and missing-feed zero substitution.

## Overview Contract

An item belongs on Overview only when it materially improves current
whole-project orientation, can be stated compactly without misleading
compression, has a known source/count/date, routes to one complete specialist
home, and does not duplicate another Overview region. Publication posture and
specialist diagnostic inventories remain off Overview.

Overview contains exactly five functional regions:

1. **Current project brief.** One dated assertion beginning with a weekday,
   overall status, `Data current through`, `Latest scheduled attempt`, `Last fully
   successful`, `Next scheduled run`, and `Next full Review Epoch`. A degraded
   state explains `Affected`, `Why`, `Still trustworthy`, and `Next action`.
   The five fact cells occupy one desktop row. The separate loaded-snapshot
   verification may report `Verified` only when Progress, Integrity, Source
   checks, and Run chain are
   producer-declared current, structurally complete, timestamped, and
   generation-compatible. The brief always states the access-time verification
   result and makes clear that loaded-snapshot validation is not a live reread
   of every external authority. Each fact date has its own accessible colored
   dot. Green means healthy/current/successful/ready, yellow means an
   authoritative intentional Pause or suppression, red means confirmed
   failure or applicable blocker, and gray means the determination is not
   reliable. Red takes precedence over yellow. Data currentness follows each
   feed's cadence and may remain green while still fresh after a pause. Latest
   scheduled attempt uses the chronologically newest scheduled occurrence,
   never the newest historical success. Last fully successful mirrors the
   relationship to that occurrence. The next ordinary run and next full Review
   Epoch use separate blocker scopes plus the exact binary Run/Paused control;
   absence of a run never implies Paused. The general badge and Latest
   scheduled attempt dot derive from the same helper and cannot drift:
   `Current` is green, `Paused` is yellow, `Failed` is red, and an
   indeterminate latest outcome is gray. Unhealthy dates link to their
   specialist evidence where available.
2. **Latest automation chain.** Exactly seven ordered operational stages:
   Cases, Presidential directives, Sources, Public input, Progress, Integrity,
   and Elim. Each shows typed outcome and completed or checked time. The
   component also shows one compact future-run-gate line linked to Operations
   > Repository gates. Latest-attempt blockers and future repository gates
   derive from one typed automation-readiness projection; an affected gate is
   identified on its typed stage rather than repeated as another Overview
   card. Host closeout, publication, and planning remain chain metadata.
3. **Operational indicators.** Five peer summaries: Public intake, Human
   action items, Codex capacity, Platform status, and Project data. Each routes
   to its complete specialist ledger. Platform and Project data may use
   compact half-width treatment when their at-a-glance cells remain legible.
4. **Work queues.** Small work-only portlets containing queue name, unresolved
   count, and detail route. If the queue feed or processing path is unhealthy,
   add a text `Problem` flag and exact log route. Healthy queues do not show
   decorative status text. The ordinary queue portlets use a compact
   grid. Publication, Integrity, monitoring, and deferred inventories are not
   work queues merely because they contain records.
5. **Recent material activity.** A short chronological list of touched
   artifacts and score changes or concise change descriptors. The producer
   supplies typed artifact-change records; the browser does not infer them
   from narrative prose. Work queues and Recent material activity share one
   balanced desktop row and stack when space is constrained.

Platform and data at-a-glance cells place each service or feed inside a lightly
divided grid cell. Platform status contains five peer cells—GPTs, Codex, API
platform, Vercel, and Cloudflare Turnstile—in one deliberate row where
legible, using bounded horizontal overflow before accidental wrapping. A
green, yellow, red, or neutral dot supplies the compact visual; the cell text
is only the service/feed name. Accessible labels and the portlet-level problem
route retain meaning without relying on color alone.

## Specialist Screen Contracts

### Operations

Operations owns:

1. Overview — authoritative global Run/Paused state, scheduling and
   currentness; one compact seven-stage latest-run strip; seven persistent-role
   status cards; and current exceptions only. The strip describes one
   serialized run. Role cards instead use each role's latest applicable
   scheduled occurrence across its own cadence.
2. Agents & Bots — one role detail at a time behind the shared compact
   horizontal specialist menu. The stable role order is Coordinator, Case
   Monitor, Directives, Source Checker, Progress, Integrity, and Elim. Role
   detail owns purpose and authority, trigger, cadence, eligibility,
   environment/runtime, current recovery, runbook/report/log routes, and a
   collapsed browser-local `Staged configuration` workspace. Direct entry
   selects Coordinator; unknown or retired role routes remain explicitly
   unavailable rather than silently selecting another role. Global Run/Paused
   belongs only to Operations Overview, and no independent per-role pause
   control exists.
3. Repository gates — only pull requests explicitly typed by the complete
   reusable repository-gate producer as blocking future automation. The
   append-only declaration authority is the owner-local path
   `records/automation/repository-gates.jsonl` under the governed
   [repository-gate policy](../automation/repository-gates.json). Authenticated
   Console refresh and scheduled/manual coordinator execution consume the same
   schema. A current future-run snapshot never rewrites historical run state;
   a gate counts against the latest attempt only when the coordinator applied
   its exact gate ID to that attempt.
4. Security — a safe operational-assurance and protective-action surface. Its
   compact status row shows public-intake `Live`, `Paused`, or `Unverified`;
   completed registered-check coverage; private attention as `None reported`,
   `Required`, or `Unavailable`; and a typed active-incident indicator. Its
   bounded master/detail workspace contains exactly the seven registered tool
   identities in
   [`project-console-classifications.json`](project-console-classifications.json):
   Public-intake protection, Repository change protection, Protected-surface
   change review, Automation isolation, Credential and access review,
   Disclosure-boundary verification, and Recovery readiness. Previews explain
   purpose and scope only. Provider-native alert contents, credential
   metadata, affected paths or components, rule identities, detector details,
   evidence, and remediation analysis remain at GitHub Security or in the
   owner-local Security Control Profile and never enter the Console projection
   or DOM. Unknown, stale, or incomplete private evidence renders unavailable,
   never zero or healthy. A successful check means completed coverage, not
   `secure` or `no vulnerabilities`.
5. Capacity — typed usage windows, reserve posture, historical consumption,
   and explicit Review Epoch identity/markers.
6. Platform — one provider-neutral typed projection grouping OpenAI, Vercel,
   and Cloudflare observations with provider source, exact checked time,
   registered relevant components, relevant provider incident references, and
   last-valid behavior. OpenAI retains GPTs, Codex, and API-platform
   aggregation. Vercel is limited to the registered ARRP intake dependencies:
   CDN, Functions, Firewall, TLS Certificates, Builds, and Git Integrations.
   Cloudflare is limited to the exact registered Turnstile component; unrelated
   provider components and incidents do not affect its cell. Missing or
   mismatched registered components fail gray, and one provider failure does
   not erase valid observations from another.
7. Data — one row per principal feed with availability, completeness, reason,
   trustworthy-through boundary, producer, and recovery route.
8. Logs — one compact horizontal menu defaulting to Operational Incidents,
   followed by Horizon, Elim, Bots, Sources, retained Integrity history, Change
   audits, and Console development above the shared bounded master/detail
   workspace.

Operational Incidents is the persistent cross-domain recovery ledger for
genuine disruption, blockage, degradation, untrustworthy data, protective
halts, and material near misses. Its immutable structured events and
deterministic projection own stable incident identity, exact occurrences,
status, recovery evidence, and closure. The lifecycle is `Open`,
`Investigating`, `Mitigated`, `Monitoring`, and `Resolved`; the first four
states are unresolved. Repeated occurrences of the same typed component,
prerequisite, and failure class attach to one unresolved incident while
preserving exact run and occurrence identity. A recurrence after verified
resolution creates a new linked incident. A generally healthy later run never
closes an unrelated incident; `Resolved` requires exact typed closure proof.

An intentional Pause, an ordinary Integrity finding, proposal
Blocked/Deferred status, routine security remediation, or a declared
repository gate is not itself an incident. It becomes incident-linked only
when it disrupts expected operation, forces a protective halt, makes data
untrustworthy, or qualifies as a material near miss. Domain ledgers retain
their ownership and link through producer-supplied `active_incident_ids`; the
browser never infers incident linkage or lifecycle from narrative text.
Provider advisories are likewise explanatory observations rather than proof
that ARRP intake or automation failed. They create no Operational Incident
unless independent ARRP impact satisfies the incident admission contract.

The Overview role cards, role-menu exception markers, and role detail consume
one typed role-status projection containing stable identity/order, latest
scheduled occurrence and outcome, last successful occurrence, next due/cadence,
authoritative pause state, current blocker, data currentness, and checked time.
Browser code may join the exact owner-only local status record but must not
infer missing role health from narrative logs or an older successful chain.
Project governance discovery belongs to the Elim role detail and appears on
Operations Overview only when due, blocked, or otherwise exceptional.

Automation status remains read-only. Non-secret runtime configuration may be
edited only as a browser-local staged value and exported in its canonical
structured format. Export does not alter the repository, installed scheduler,
or host state; application requires the ordinary reviewed repository path and
immediate host approval where persistent host configuration is affected.
Embedded complete runbook transcripts and bare runtime-configuration links are
not Console controls and are not reproduced.

The repository-visible Console generation is a public operational summary, not
an owner-only data store. It contains only allowlisted role summaries and
public project-history ledgers. Complete runtime configuration, authenticated
security observations, and raw automation, integrity, source-monitor,
incident-evidence, and Console-development history remain in separately
secret-scanned, Git-ignored local projections. Those local files are restored
only after the public generation passes the project-wide disclosure gate and
are absent from its manifest, catalog, DOM, exports, and GitHub-bound bundle.
Unavailable local detail is never represented as a public zero or healthy
state.

The Console supports three explicit delivery modes. The ordinary owner-local
mode is the canonical `research/horizon-review-console/index.html` opened
directly with `file://`; it may load the ignored sibling Security assurance,
private Operations, and local automation-status scripts. Loopback HTTP(S) on
`localhost`, `127.0.0.1`, or the IPv6 loopback is the development mode and may
load the same ignored files. Hosted/public HTTPS is public-only and must not
request any local projection. A future hosted private mode requires a
separately designed authenticated service with deny-by-default field
allowlists; authentication never means storing private operational data in
GitHub. The direct-disk gate requires an empty file hostname and the canonical
Console entrypoint suffix. Missing or malformed files remain unavailable.
Private Operations additionally requires an exact schema, Console generation,
and source-revision binding before its records can join the public shell. Its
owner-only Action snapshot is part of that same binding, so private Security
attention cannot alter one surface without reconciling all shared Action
counts.

Opening the static `file://` Console never reads a credential or initiates a
network request. Authenticated refresh is a separate owner-invoked local
operation completed before the static files are opened or reloaded.

Security accepts only `Open protected source`, `Refresh authenticated status`,
`Prepare read-only review`, and the separately reviewed public-intake
`Live / Paused` action class. The static Console executes no arbitrary command
or security mutation. Until an authenticated owner-only server control is
separately reviewed, intake-state changes remain exported requests. Any future
direct control must cover the form, both APIs, collector, Elim intake review,
and replies; require exact authorization and immediate readback; and create an
Operational Incident when those surfaces disagree. A form-endpoint pause alone
never establishes that intake collection and review are paused.

The minimized security projection permits only registered tool ID and safe
label, availability, last checked, next due, safe source revision, coverage
state, private-attention value, owner class, destination class,
active-incident boolean, and public-intake state. Safe tool-purpose text comes
from the checked-in classification registry, not the private feed. Unknown
tool IDs or fields invalidate the private projection. Human-required work
cross-indexes into Action Items only as a generic protected action; Elim-owned
work may contribute a private authenticated work-unit signal but no public
count or details. Provider-native CodeQL, Dependabot, secret-scanning, and
private-advisory systems remain the detailed authorities and are never copied
into project-authored GitHub records.

The ordinary
user-facing control vocabulary is binary `Run / Paused`; `Disabled` is not a
second state. Exposing or changing the owner-controlled pause mechanism
requires a separate authority, security, audit, and host-state review. The
Console must not disable a background service as a substitute for pausing the
chain. A separate Elim-only safeguard may be designed later; a Bots-only pause
that leaves Elim eligible is not an ordinary safe state.

### Integrity

Integrity means the exact Project Integrity report: report identity,
availability, generated time, revision, counts, and complete findings. Stage
execution belongs in Operations and retained run history belongs in Logs.
Cross-domain health cards are not combined into an apparent Integrity total.

### Action Items, Progress, Planning, Candidates, and Sources

These established workflows remain stable unless a change has high-confidence
usability or technical justification. Action Items is the model for a compact
selectable list with adjacent preview. Sources and other large record lists use
the same pattern where individual inspection is required: one concise row per
record, detail in the preview, bounded list height, and explicit empty,
unavailable, stale, or incomplete states.

Every unresolved Operational Incident appears in Action Items. Explicitly
human-owned incidents appear under My items and contribute to Human Action
Items; non-human-owned and unassigned incidents appear only under Oversight.
All open is their union. Main-tab and Overview Human Action Items counts remain
human-only, and unassigned incident ownership is itself an oversight problem.

Action Items begins with a compact **Priority attention** lead-in only when at
least one deterministically elevated human-owned record exists. It contains at
most five records and may elevate only an explicit blocking effect, Critical or
High priority, due or overdue timing, or a recorded consequential decision.
The browser does not invent a priority score. Ordinary unresolved human work
remains only in the complete Action Inbox, and non-human technical exceptions
remain in Automation blockers, Platform, or Data.

Progress is the portfolio measurement and current-state surface. It owns the
development-level board, Review Ready coverage, trajectory and history, and
routine issue monitoring. It may show compact Blocked and Deferred counts that
link to Workbench, but it must not repeat the complete hold inventory.

Planning > **Workbench** is the sole detailed contextual work-sequencing
surface. **Pipeline** is its default category. Its subtitle
is: `A read-only planning view of candidate intake and proposal development
toward Review Ready.` The default **Active pipeline** mode is paired with one
alternate **Blocked & deferred (N)** mode. The active view exposes Search,
Work class, Scope, and Sort, with Status, Development level, Area, Owner,
Priority, and related facets under Advanced filters. Scope defaults to Active
development; Review Ready+ and All remain explicit alternatives. Reset is
mode-specific.

Workbench > Pipeline uses the shared bounded master/detail interface: a compact selectable
list, complete adjacent preview, independent scrolling, responsive stacking,
keyboard selection, automatic first matching selection, and stable deep-linked
selection. Rows use no more than two lines and show identifier/title, work
class, status, score when applicable, and a clipped exact next action. Owner,
workstream, complete rationale, position explanation, readiness gaps, missing
inputs, and canonical links belong in the preview. The browser must not
synthesize work remaining before Review Ready unless the producer supplies
typed readiness gaps.

The typed Pipeline producer applies this precedence: exact human-decision
records route to Action Items; exact `Blocked` or `Deferred` Status routes to
the alternate Pipeline mode; reliably Review Ready or Release Candidate
records are hidden only from the default active scope; preliminary candidates,
formal candidates, and below-ready proposals remain active; contradictory or
unrecognized records remain visible as data or Integrity exceptions rather
than being silently classified. Publication approval belongs in Publication
and, when human-actionable, Action Items.

Default Active Pipeline order is deterministic: preliminary candidates,
formal candidates, then proposals by valid Development Score descending.
Within a class, exact-next-step completeness precedes recorded priority, due
date, and stable identifier. Candidate score is not applicable. Proposal score
`0` is valid and distinct from missing. Missing exact next action does not
remove an otherwise eligible record; it renders `Next step not recorded`,
sorts after complete peers in its class, and contributes to a compact
planning-data-gap count. Review Ready exclusion uses the complete typed
readiness predicate, not score or level alone, and maturity/score conflicts
remain visible.

Blocked & deferred contains only exact authoritative `Blocked` or `Deferred`
statuses at every maturity, preserving the two labels. It foregrounds the
dedicated hold reason, blocked action or missing prerequisite, unblock or
reconsideration trigger, hold transition date, last hold review, explicit
review date, owner, and audit/canonical links. The audit entry recording the
Status transition supplies `Hold since`; a later hold-review entry supplies
`Last reviewed`; an explicit reconsideration date supplies `Review due`.
Project Status without matching audit transition provenance is an Integrity
finding and Warning. Generic issue `updated_at` and candidate discovery or
admission rationale never substitute for hold facts.

The browser renders the small typed Pipeline projection and does not infer
planning membership from narrative text, monitoring incidents, or browser-only
cohorts. Overview queue counts and Pipeline filters share the same producer
predicates; an External review Overview route opens Review Ready+ scope. Fired
monitoring enters Pipeline only after its authoritative resulting workflow
Status or action does. Human decisions route to Action Items, and all Pipeline
records route to their single complete dossier or canonical ledger.

## Personal layout design

Every Console screen supports grid-based personal layout design wherever a
section or card can safely resize. Design mode offers bounded widths such as
full, half, third, quarter, and compact, plus reordering and reset. Responsive
rules may widen a chosen size on smaller screens to prevent clipping,
unreadable text, inaccessible controls, or page overflow. Master/detail lists,
tables, and other interaction-specific workspaces retain their own internal
layout controls. Editing controls are mounted only while Design mode is active;
the saved layout continues to apply without hidden editing controls in the
ordinary page.

Personal layout drafts are stored only in that browser and are not project
authority, repository state, or a public default. Converting a settled personal
layout into the project default requires an explicit reviewed repository
change; it must not occur merely because a browser preference exists.

While Design mode is active, its exit button remains fixed at the top of the
viewport. Compatible Overview portlets may move among Operational indicators,
the Overview main flow, and the Overview lower row; placement is browser-local,
persists across rendering and reloads, and resets with the rest of that view.
Portlets do not move across main screens or into specialist ledgers.

### Logs

Every log uses the shared newest-first master/detail surface. Operational
Incidents is the first and default log and defaults to unresolved incidents,
with complete retained history available. Its list has one row per incident;
the preview preserves the exact occurrence timeline and recovery evidence.
Every other log uses the same surface. The newest
matching entry is selected automatically; filtering that removes it selects
the first remaining entry. The list and preview scroll independently inside a
bounded workspace and stack on narrow screens. There is no duplicate
`Latest entry` card. Logs remain projections of their canonical records and do
not become independently edited ledgers.

Every log producer declares availability, completeness, schema errors, and
current-through independently. Owner-only histories in public mode render an
explicit unavailable state and dash count, never a blank list or zero. The
shared selection controller supports Arrow Up, Arrow Down, Home, and End.
Navigation applies complete route state only after required domain data is
ready, including initial load, reload, same-hash activation, aliases, filters,
and stable selected-record deep links.

Logs distinguish historical project **Change audits** from **Console
development**. Console development records product feature lifecycle and exact
Git traceability; it does not contain ordinary data refreshes or operational
state transitions.

The Operations main-tab badge, Logs > Incidents badge, and Overview
Operational incidents queue are the same typed unresolved count, deduplicated
by incident ID. They are navigation cues, not separate calculations. Red means
an unresolved incident currently blocks or disrupts operation; yellow means
the unresolved set is degraded, mitigated, or monitoring only; green requires
zero unresolved incidents and a complete feed; gray means the feed is
unavailable or incomplete. An unavailable feed is never rendered as zero or
green.

## Dates, Counts, and State

Operational dates use producer-normalized ISO timestamps and render weekday,
month, day, year, local time, and time-zone abbreviation where they qualify a
current-state assertion. Use terms precisely:

- `Generated` for output creation;
- `Current through` for the last authoritative event included;
- `Checked` for an external observation;
- `Latest scheduled attempt` and `Last successful` for execution history;
- `Next scheduled run` for the next ordinary coordinator evaluation;
- `Next full Review Epoch` for the first scheduled evaluation at or after the
  recorded biweekly due boundary.

Every count has a canonical owner, exact inclusion predicate, open/resolved
scope, completeness declaration, and generated/checked identity. A navigation
button shows a number only when that number is an actionable queue owned by
the destination; it never shows inventory size, history length, role count, or
the number of records merely visible there. An accessible fixed-size red dot
is independent of counts and appears when a typed current blocker is
represented in that screen. A workflow record whose only condition is exact
`Blocked` or `Deferred` Status does not trigger that dot. Color never carries
meaning alone, and a status is not styled as an action.

`Notice` identifies expected unresolved work such as human action items or
public intake. `Warning` is reserved for degraded, stale, serious, or blocking
conditions; `Error` identifies a failed or invalid condition.

## Atomic Data and Generation

The production transaction must materialize and hash-bind the final Console
inputs after the last mutable stage. Final Project Integrity validation and
feed generation occur after Elim and before Console generation, so execution
status and report content describe the same final state. A bounded Integrity
history is retained from the prior trusted local generated feed.

The builder fails closed on a missing, mixed-run, hash-mismatched, incomplete,
or structurally invalid required feed. A newer incomplete projection cannot
silently replace a valid complete one. Any retained last-valid value states its
trustworthy-through boundary and why the current value is unavailable.

Overview is generated as one immutable atomic projection. Loading a specialist
screen must not change a prior Overview assertion, count, status, or selection.

## Console Product Traceability

Material Console changes use stable IDs in the form `CONSOLE-YYYY-NNN` and are
recorded in
[`console-development-log.md`](../../records/automation/console-development-log.md).
Each semantic implementation commit carries exactly one applicable trailer:

`Console-Change-ID: CONSOLE-YYYY-NNN`

The log preserves the lifecycle action, user-visible effect, full
40-character implementation commit or commits, accepted/proposed state,
governing references, affected features and producers, validation/readback,
known limitations, and full rollback baseline. A rename or move retains its
feature identity; a replacement records supersession. Retirements, restorations,
and reversions append history rather than rewriting it. Git remains the exact
diff authority.

Each change is a heading-based structured record rather than a table row. The
dated umbrella and category-specific entry rules are defined once under
**Console Development Log classification** above. Rapid-fire work collapses
only within one coherent registered category and change set; separate material
categories remain separate selectable Console log entries. A new change ID is
required only for a materially distinct purpose, review decision, or rollback
boundary; commits and conversational turns do not independently define entries.

Routine generated feed refreshes, new domain records, and ordinary automation
state changes are excluded. Historical reconstruction is allowed only from
verified diffs and records and must state its confidence.

## Accessibility, Responsiveness, and Validation

Interactive rows are keyboard operable, visibly focused, and expose selection
semantics. Status meaning is available to assistive technology. Long text wraps
or is available in the preview; narrow layouts stack without horizontal page
overflow.

A material Console change is complete only when:

- every Overview summary resolves to one detailed home;
- primary and deep routes open the intended view;
- state/count/date semantics pass deterministic tests;
- generated domains are complete and mutually bound;
- newest-first selection and filtering work;
- keyboard, focus, contrast, and responsive behavior are checked;
- the Console Development Log and governing contract agree;
- the deterministic build and repository consistency validation pass.
