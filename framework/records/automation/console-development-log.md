---
title: "ARRP Console Development Log"
status: active
print_status: excluded
print_exclusion_reason: "Internal interface-development history."
---

# ARRP Console Development Log

This append-only record indexes material changes to the Project Console as a
product. Git remains the exact diff authority; this log explains introductions,
changes, moves, renames, retirements, restorations, and reversions across
commits. Routine data refreshes and ordinary operational state changes do not
belong here.

Every material Console change receives a stable `CONSOLE-YYYY-NNN` identity.
Semantic implementation commits use the trailer
`Console-Change-ID: CONSOLE-YYYY-NNN`. A change that has not yet been committed
or accepted on canonical `main` is explicitly labeled `Proposed / unmerged`.
Full 40-character Git identities are retained; the interface may abbreviate
them for display.

As a general rule, same-day Console work in the same change area is collapsed
into one entry. This includes rapid edits, review refinements, and related
technical repairs; do not create an entry for each message, file save, or
commit. Begin a separate change ID only when the work has a materially distinct
purpose, review decision, or rollback boundary.

## CONSOLE-2026-001 — Adopt holistic Console design and operational information architecture

- Recorded: 2026-07-28
- Lifecycle: Changed
- Feature or component: Whole Console
- State: Committed / pending canonical synchronization
- Implementation commits: `3f0f1d3d48b4aea148de9da92c946fe36f2c8a35` (`Console-Change-ID: CONSOLE-2026-001`)
- Rollback baseline: `a47082d0a684de38626c68fec325337765f35b9a`

### User-visible change

Establishes a compact dated Overview, seven-stage chain, five operational
indicators with specialist homes, work-only queue counters, bounded
master/detail logs, exact Integrity ownership, and a Console Development
sub-tab under Logs.

Same-day Overview refinements keep the five brief facts and eight work queues
compact, pair Work queues with Recent material activity, use narrower
at-a-glance Platform and Project data indicators, separate the
latest-scheduled `Current`/`Paused`/`Failed`/`Unknown` badge from strict
loaded-snapshot verification, expose the verification basis on every access,
and use `Notice` rather than `Warning` for ordinary unresolved human work. The
former Current Attention region moves to a deterministic, human-owned Priority
attention lead-in above the complete Action Inbox.

Latest-attempt blockers and future repository gates now share one typed
automation-readiness projection inside the seven-stage chain. The separate
Automation blockers Overview indicator and duplicate top-level failure alert
are retired; affected gates appear on their typed stage and the chain links to
the complete Repository gates ledger.

Console-wide Design mode adds safe grid widths and reordering where cards or
sections can resize without breaking a specialist interaction. Experimental
layouts remain browser-local until a later explicit reviewed change adopts one
as the project or public default. Design controls are mounted only while Design
mode is active so ordinary Console use stays within its initial page-complexity
budget. The exit control remains fixed while scrolling, and compatible
Overview portlets can move among the main flow, Operational indicators, and
the lower row with browser-local placement persistence.

Main navigation is consolidated to Overview, Action Items, Progress, Planning,
Integrity, and Operations. Planning defaults to Workbench, followed by
Preliminary Candidates, Candidates, Sources, and Publication, without creating
a combined ledger. Workbench uses Pipeline as its default category and replaces
the incident-style Next Work view with a
typed, deterministic, bounded master/detail work-sequencing projection.
Progress retains current-state measurement, trajectory, and monitoring, with
compact hold counts linking to Workbench instead of a duplicate detailed hold
inventory. Blocked and Deferred records use dedicated hold facts and audit
transition provenance; candidate Horizon rationale and generic issue update
dates no longer stand in for hold evidence. Operations owns Logs through one
compact horizontal menu above the existing bounded master/detail workspace.
Navigation numbers are reserved for actionable queues owned by their
destination. Accessible fixed-size red dots independently mark typed blockers,
excluding records whose only condition is Blocked or Deferred workflow Status.
Legacy routes semantically redirect to their new destinations and filters.

Agents & Bots now uses single-row card headers without repeated machine names,
one concise producer-authored purpose statement, no embedded complete-runbook
transcript, and an editable non-secret configuration control panel that exports
the canonical JSON for review without mutating repository or host state.
Compact portal groups prefer one deliberate desktop row; the Local nightly
transaction metrics no longer spill into an accidental second row.

Operations now defaults to a compact manager Overview rather than a long Run
chain page. It separates the latest seven-stage serialized run from seven
cadence-aware persistent-role cards, retains only current exceptions, and moves
governance discovery to Elim detail. Agents & Bots uses the shared compact
horizontal specialist menu and one role workspace at a time; staged
configuration remains browser-local for the current session. Source Checker
crawl-specific configuration remains intentionally deferred.

Security remediation now has one private authenticated Operations ledger and
separate human-versus-Elim Action Items cross-indexes without altering the
exact Integrity report. The Overview queue counts typed remediation work units
and preserves raw-alert count in detail. Repository gates now have an
append-only declaration authority and one reusable fail-closed producer used by
both authenticated Console refresh and scheduled/manual coordinator
enforcement. Exact-head changes and incomplete pagination cannot become zero;
last-good evidence is labeled as retained, and latest-attempt blockers remain
separate from current future-run gates.

Each Current project brief date now has an accessible green, yellow, red, or
gray status dot driven by its own predicate. Latest scheduled attempt and the
general Current badge share one authoritative helper; intentional Pause is
yellow, confirmed failure or blocker is red, and upcoming ordinary/full-review
readiness uses separately scoped blocker predicates.

The existing Platform status indicator now uses one provider-neutral typed
projection shared with Operations > Platform. Its compact divided row contains
GPTs, Codex, API platform, the registered Vercel dependencies for ARRP public
intake, and the exact Cloudflare Turnstile component. Provider refreshes fail
independently; mismatched or missing registrations remain gray, last-valid
observations retain their own times, and unrelated provider incidents are
excluded. Advisory provider status does not create an ARRP incident without
independently established project impact.

Operational Incidents is now the first/default Logs ledger and the persistent
cross-domain recovery roll-up. One immutable typed event record preserves
stable incident identity, exact occurrences, lifecycle, recovery evidence, and
closure; the Console consumes one deterministic projection rather than
inventing incidents in browser code. The Operations badge, Incidents log
badge, and Overview queue reuse the exact unresolved count. Action Items
includes every unresolved incident while preserving human-only My items,
Priority attention, and Human Action Items counts. Typed incident IDs connect
run stages, roles, repository gates, security, platform, and data without
duplicating lifecycle calculations. Unavailable or incomplete incident data
remains unknown rather than zero or healthy.

The repository-visible Console generation is now explicitly public-safe.
Allowlisted role summaries and public project-history logs remain in the
checked-in bundle, while complete runtime configuration, authenticated
security observations, and raw operational histories are written only after a
successful disclosure-gated build to secret-scanned, Git-ignored owner-local
projections. The public manifest and browser DOM never contain those local
details. The disclosure gate's initial prevention of an unsafe mixed bundle is
retained as resolved near-miss incident `INC-2026-001`.

The outbound boundary now uses a portable public enforcement core plus a
required versioned owner-local control pack. Portable credential-free source,
tests, workflows, repository administration, and high-level governance are
public operational material; exact environment-specific detectors, sensitive
runtime topology, full operational journals, active handoff detail, and raw
incident, repository-gate, review-epoch, and agent-audit authorities remain
owner-local. Default disclosure grouping is per artifact, with coupling only
through registered group identities. The empty participation environment
template is a distinct public family; live environment files remain private.
Missing or incompatible local controls, unknown families, incomplete evidence,
or any secret finding stop before a project-operated GitHub mutation. The
complete public tree and exact outgoing change set are both classified, while
restricted originals are preserved locally and replaced only by minimized
public contracts or summaries.

### Implementation and producer effects

Establishes same-run final Integrity generation, atomic Overview projections,
specialist Operations ledgers, a shared record-inspection pattern, a
comprehensive governing Console contract, typed automation-readiness
projection, typed Workbench Pipeline projection, typed Operational Incident
event/projection contracts, browser-local grid layout preferences, and
Git-backed product traceability.

### Validation

Validation includes 537 Python tests with 15 environment-dependent skips, 72
Console and public-intake frontend tests, deterministic Console and compiled
PDF builds, data-contract, accessibility, route, disclosure, incident,
repository-gate, coordinator, and responsive-interface checks, plus a complete
repository consistency pass with zero local errors. The candidate disclosure
controls approve all 568 intended repository files and the exact outgoing
change set with zero restricted or secret findings.

### Known limitations and follow-up

Configuration exports are staged only. Applying them to the repository or host
requires the ordinary reviewed change and immediate approval for persistent
host state. The full semantic implementation commit is recorded above.
Synchronize this entry on canonical `main`; any later host-configuration
application remains a separately approved change.

## Record requirements

Each entry is an `##` heading containing the stable change ID and title,
followed by the fixed metadata list shown above. Narrative `###` sections
preserve the user-visible effect, implementation or producer effects,
validation/readback, governing references where useful, and known limitations
or follow-up. A retirement names its replacement or states that no replacement
exists. A restoration or reversion identifies its related change IDs. History
is never rewritten.

Historical reconstruction before `CONSOLE-2026-001` is permitted only from
verified diffs and records. Reconstructed entries must say so and state their
confidence; commit subjects alone are insufficient evidence.
