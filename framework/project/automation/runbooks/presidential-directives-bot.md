---
title: "Presidential Directives Bot Runbook"
agent_id: presidential-directives-bot
display_name: Presidential Directives Bot
agent_type: deterministic-bot
status: enabled
trigger: run-chain-or-manual
schedule: "Due every 24 hours in the Run Coordinator chain; no independent schedule"
runtime_id: .github/workflows/presidential-directives-bot.yml
execution_environment: github-actions
runtime_config: .github/presidential-directives-bot.json
log_path: framework/records/automation/agent-audit-log.md
domain_event_log: framework/records/sources/source-monitor-log.md
domain_event_schema: .github/source-domain-event.schema.json
domain_event_data: project-console-data:source-domain-events/
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Presidential Directives Bot Runbook

The Presidential Directives Bot compares the accepted presidential-directive registry metadata with the official Federal Register API. It validates the configured administration coverage, response structure, identity, fingerprints, and last-changed values.

On a material deterministic change it may update only authorized registry metadata on `automation/presidential-directives-monitor`, record the domain event, and create or update the owner-assigned review pull request. It may not decide project relevance, route evidence, revise prose, change Project fields, create a candidate, or change a proposal's score, audit count, foundation, or remedy. Failures are closed; no-change runs create no commit.

The JSON manifest and callable GitHub workflow are deployed projections of
this runbook and must match its identity, status, due interval, branch, and
log destinations. The bot does not edit shared Markdown logs from its proposal
branch. It emits immutable structured stage and domain events to the Run
Coordinator; accepted material changes are rendered or recorded in the shared
Agent Audit Log and Source Monitor Log under the common provenance rule.

## Inputs and permitted writes

The bot reads `inventory/presidential-directives.csv`, its accepted fingerprints and last-changed values, the configured Trump I, Biden, and Trump II date scopes, and official Federal Register presidential-document API results. It may update only authorized deterministic registry metadata and emit the related structured source-domain and stage events. It may not decide relevance, characterize legal or political significance, route a directive to an issue, alter project prose, create a candidate, or change Project or audit/scoring fields.

## Publication and review

Material changes are committed only to the dedicated
`automation/presidential-directives-monitor` proposal branch and presented
through an owner-assigned pull request. The branch is not a shared substantive
branch. The pull request must itemize each affected directive by its stable
registry identity, the observed fingerprint, `Last Changed`, or other
authorized metadata delta, and the originating Actions run across the complete
unresolved exact-head delta; a latest-run summary may not conceal changes
retained from an earlier run. The proposal first enters Elim's source-domain
review queue. Elim verifies the primary directives, determines relevance and
routing, and records an exact-head disposition recommendation in the Source
Monitor Log. Only an expressly reserved or owner-gated choice then enters
human Action Items with the exact question. Merging remains human-owner gated
and accepts the proposed registry baseline and other itemized changes.
No-change runs create no commit, and every proposed registry change requires
human review before merge.

The workflow emits one schema-versioned, minimized `proposed` source-domain
event for the complete pending branch delta. Its stable idempotency key binds
the Chain and Actions run as correlation fields, source revision, pull
request, delta-derived semantic projection, and proposal-delta hash. The JSON
event contains only stable directive IDs and counts reproducible from the
exact Git delta, plus output file hashes; the full diagnostic report remains
in its retained artifact. The event contains no Federal Register response body, title,
directive text, or private data. It is retained as an Actions artifact,
projected immutably under
`source-domain-events/proposed/presidential-directives-bot/` on
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

Before publication, the bot validates the configured administration coverage,
Federal Register host and response structure, document identity, pagination
bounds, fingerprints, last-changed values, and its authorized file boundary.
Missing or malformed inputs, provider/schema failure, identity ambiguity,
boundary violations, commit/push failure, or validation failure stop the run
without publishing a misleading update. Every run reports new, changed,
unchanged, and not-seen registry records in the Actions summary and retained
diagnostic artifact. Outputs are the proposed registry delta, immutable
structured stage and source-domain events, Actions summary, and retained
diagnostic artifact. Workflow failures enter the Run Coordinator failure state
and notification path; routed content changes rely on the assigned pull
request.
