---
title: "Case Monitor Bot Runbook"
agent_id: case-monitor-bot
display_name: Case Monitor Bot
agent_type: deterministic-bot
status: enabled
trigger: run-chain-or-manual
schedule: "Due every 24 hours in the Run Coordinator chain; no independent schedule"
runtime_id: .github/workflows/case-monitor-bot.yml
execution_environment: github-actions
runtime_config: .github/case-monitor-bot.json
log_path: framework/logs/AGENT_AUDIT_LOG.md
domain_event_log: framework/logs/SOURCE_MONITOR_LOG.md
domain_event_schema: .github/source-domain-event.schema.json
domain_event_data: project-console-data:source-domain-events/
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Case Monitor Bot Runbook

The Case Monitor Bot performs one respectful comparison when its 24-hour
Run Coordinator interval is due, or when manually requested, for cataloged
`Monitoring = Yes` sources mapped to stable entries in the Just Security
litigation tracker. It validates tracker structure and accepted baselines
before comparing fingerprints. The accepted fingerprint for each covered
source is stored in that source row's `Monitoring Baseline` field. For a
changed mapped CourtListener docket it may perform the configured narrow,
paced metadata verification. It also evaluates explicitly configured
source-development modules against the same validated tracker snapshot. A
module may project high-recall, machine-observed leads into the existing
source-development record for its named candidate or issue.

It may update only authorized machine-observed source fields and bounded generated lead sections on `bot/case-monitor-updates`, record the domain event, and create or update the owner-assigned review pull request. A lead states only the matched signal, docket identity, source links, tracker posture, observation fingerprint, and unreviewed status. The bot does not create a source-catalog record merely because a textual signal matched. It may not discover every new case, interpret legal significance, characterize review evasion, revise project-authored analysis, change Project fields, create or admit a candidate, remove monitoring, or change a score, audit count, foundation, remedy, or disposition. Failures are closed; no-change runs create no commit.

The JSON manifest and callable GitHub workflow are deployed projections of
this runbook and must match its identity, status, due interval, branch, and
log destinations. The bot does not edit shared Markdown logs from its proposal
branch. It emits immutable structured stage and domain events to the Run
Coordinator; accepted material changes are rendered or recorded in the shared
Agent Audit Log and Source Monitor Log under the common provenance rule.

## Inputs and permitted writes

The bot reads the two canonical source catalogs, rows expressly marked `Monitoring = Yes`, accepted monitoring baselines, the configured Just Security tracker table, at most the configured number of eligible CourtListener dockets, and the existing source-development records named by enabled modules. It may change only authorized machine-observed fields in `inventory/sources.csv` or `inventory/sources-pending.csv`, the marker-bounded generated lead sections in those configured source-development records, and the resulting event and provenance entries.

The bot must preserve stable case identity independently of table order and
publisher action-cluster labels, distinguish primary case rows from related
appeals, and retain the source's exact status and status-date fields. The
tracker is a curated discovery and status source rather than a complete docket
feed. Its exclusions, consolidated matters, selective case families,
editorial lag, and missing narratives remain express limits on automated
coverage. The comparison does not claim to discover every newly filed case or
every new tracker entry. Separate source-intake and project-wide monitoring
scans remain responsible for unmatched cases, new sources, and active search
obligations. Every source or search obligation outside the bot's verified
coverage must remain visible for human or LLM-assisted review; it may not
disappear from the monitoring pass merely because the bot did not cover it.

CourtListener verification is targeted rather than corpus-wide. When a
changed mapped tracker row identifies a supported CourtListener docket, the
bot may compare only the configured REST v4 docket fields and must honor the
configured request ceiling and pacing. A CourtListener API token is optional.
Without one, the tracker comparison still completes, and the changed source is
reported as awaiting primary-docket verification. An unmatched, grouped, or
unverified tracker entry may not be admitted, routed, or characterized
automatically.

An enabled module must name one established source-development path: `research/horizon-source-records/HOR-###-source-development.md` for a formal candidate or `areas/AREA/research/AREA-###-source-development.md` for an admitted issue. The target must already exist. The generated section is a queue projection inside that authoritative record, not a separate substantive queue. Each entry remains an **Unreviewed machine lead** until Elim or an interactive agent verifies the primary record and records the complete `CASELEAD-…@fingerprint` disposition token and source-development disposition outside the bot-owned markers. On the next run, the bot removes that observation from the unreviewed projection while preserving the agent-authored disposition. A later material change creates a new fingerprint and re-queues the lead. The bot may not rewrite material outside its exact markers, add a source-catalog row, change source meaning, or alter project prose, issue disposition, Project fields, or audit/scoring records.

## Publication and review

Material changes are committed only to the dedicated `bot/case-monitor-updates` proposal branch and presented through an owner-assigned pull request. The branch is replaceable only with lease protection under the shared branch-safety rule. The pull request must itemize the complete unresolved exact-head delta, including every affected `SRC-####`, generated record, and originating Actions run; a latest-run summary may not conceal changes retained from an earlier run. The proposal first enters Elim's source-domain review queue. Elim verifies the primary records, determines relevance and routing, and records an exact-head disposition recommendation in the Source Monitor Log. Only an expressly reserved or owner-gated choice then enters human Action Items with the exact question. Merging remains human-owner gated and accepts the proposed monitoring baseline and other itemized changes. No-change runs create no commit. Every proposed catalog or source-development lead change requires human review before merge.

The workflow emits one schema-versioned, minimized `proposed` source-domain
event for the complete pending branch delta. Its stable idempotency key binds
the Chain and Actions run as correlation fields, source revision, pull
request, delta-derived semantic projection, and proposal-delta hash. The JSON
event contains only stable affected-record IDs and counts reproducible from
the exact Git delta, plus output file hashes; the full diagnostic report
remains in its retained artifact. The event contains no response body, title, case
narrative, or private data. It is retained as an Actions artifact, projected
immutably under `source-domain-events/proposed/case-monitor-bot/` on
`project-console-data`, exposed through the reusable-workflow outputs, and
bound to the review pull request by its event ID and content hash.
The same complete projection is embedded in the retained current-run report
for Elim and rendered as a human-readable, marker-bounded pull-request
section. The current-run work count uses the complete unresolved affected
record count rather than only changes first observed during that run.

Only a same-repository merge of the exact bot-branch revision into `main` by
the allowlisted human project owner establishes acceptance. The acceptance workflow must verify the
pull-request number and branch, proposed-event hash, exact PR head revision,
source-revision ancestry, complete proposal file set and patch hash,
delta-derived semantic projection, supported merge topology, exact
first-parent accepted delta, and every accepted file hash before creating the
corresponding immutable `accepted` event. It then opens a separate,
event-specific pull request that renders the accepted event exactly once into
the Source Monitor Log and Agent Audit Log using stable hidden markers. It
never merges that pull request or pushes either shared log directly to
`main`. A closed-unmerged, altered, bot-merged, stale, or hash-mismatched
proposal remains proposed and receives no accepted log entry.

## Validation, stop, and output

Before publication, the bot validates tracker structure and bounds, required
table identity and headers, source eligibility, accepted baselines, allowed
hosts, stable docket identity, primary-row and related-appeal distinctions,
exact status and status-date retention, configured module IDs and signal
groups, established target-path convention, exact marker ownership,
configured lead ceilings, the 20-docket verification ceiling, 13-second
CourtListener pacing, and the authorized change boundary. Missing required
headers, duplicate identities, malformed rows or markers, an implausibly
incomplete tracker response, a covered source without an accepted baseline
during an ordinary run, an unsafe or absent target, signal volume above the
configured ceiling, network/provider failure, boundary violations,
commit/push failure, or validation failure stop the run without a misleading
update. Outputs are the proposed catalog delta, generated source-development
lead section, immutable structured stage and source-domain events, Actions
summary, and retained diagnostic artifact. Workflow failures enter the Run
Coordinator failure state and notification path; routed content changes rely
on the assigned pull request.
