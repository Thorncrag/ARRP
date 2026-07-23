---
title: "Case Monitor Bot Runbook"
agent_id: case-monitor-bot
display_name: Case Monitor Bot
agent_type: deterministic-bot
status: enabled
trigger: schedule-or-manual
schedule: "17 4 * * * UTC; approximately midnight Eastern"
runtime_id: .github/workflows/case-monitor-bot.yml
execution_environment: github-actions
runtime_config: .github/case-monitor-bot.json
log_path: framework/logs/AGENT_AUDIT_LOG.md
domain_event_log: framework/logs/SOURCE_MONITOR_LOG.md
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Case Monitor Bot Runbook

The Case Monitor Bot performs one respectful daily comparison for cataloged `Monitoring = Yes` sources mapped to stable entries in the Just Security litigation tracker. It validates tracker structure and accepted baselines before comparing fingerprints. For a changed mapped CourtListener docket it may perform the configured narrow, paced metadata verification. It also evaluates explicitly configured source-development modules against the same validated tracker snapshot. A module may project high-recall, machine-observed leads into the existing source-development record for its named candidate or issue.

It may update only authorized machine-observed source fields and bounded generated lead sections on `bot/case-monitor-updates`, record the domain event, and create or update the owner-assigned review pull request. A lead states only the matched signal, docket identity, source links, tracker posture, observation fingerprint, and unreviewed status. The bot does not create a source-catalog record merely because a textual signal matched. It may not discover every new case, interpret legal significance, characterize review evasion, revise project-authored analysis, change Project fields, create or admit a candidate, remove monitoring, or change a score, audit count, foundation, remedy, or disposition. Failures are closed; no-change runs create no commit.

The JSON manifest and GitHub workflow are deployed projections of this runbook and must match its identity, status, cadence, branch, and log locations. Material actions use the shared Agent Audit Log in addition to any source-domain event required for evidentiary traceability.

## Inputs and permitted writes

The bot reads the two canonical source catalogs, rows expressly marked `Monitoring = Yes`, accepted monitoring baselines, the configured Just Security tracker table, at most the configured number of eligible CourtListener dockets, and the existing source-development records named by enabled modules. It may change only authorized machine-observed fields in `inventory/sources.csv` or `inventory/sources-pending.csv`, the marker-bounded generated lead sections in those configured source-development records, and the resulting event and provenance entries.

An enabled module must name one established source-development path: `research/horizon-source-records/HOR-###-source-development.md` for a formal candidate or `areas/AREA/research/AREA-###-source-development.md` for an admitted issue. The target must already exist. The generated section is a queue projection inside that authoritative record, not a separate substantive queue. Each entry remains an **Unreviewed machine lead** until Elim or an interactive agent verifies the primary record and records the complete `CASELEAD-…@fingerprint` disposition token and source-development disposition outside the bot-owned markers. On the next run, the bot removes that observation from the unreviewed projection while preserving the agent-authored disposition. A later material change creates a new fingerprint and re-queues the lead. The bot may not rewrite material outside its exact markers, add a source-catalog row, change source meaning, or alter project prose, issue disposition, Project fields, or audit/scoring records.

## Publication and review

Material changes are committed only to the dedicated `bot/case-monitor-updates` proposal branch and presented through an owner-assigned pull request. The branch is replaceable only with lease protection under the shared branch-safety rule. No-change runs create no commit. Every proposed catalog or source-development lead change requires human review before merge.

## Validation, stop, and output

Before publication, the bot validates tracker structure and bounds, source eligibility, accepted baselines, allowed hosts, docket identity, configured module IDs and signal groups, established target-path convention, exact marker ownership, configured lead ceilings, the 20-docket verification ceiling, 13-second CourtListener pacing, and the authorized change boundary. Missing or malformed inputs, identity ambiguity, malformed markers, an unsafe or absent target, signal volume above the configured ceiling, network/provider failure, boundary violations, commit/push failure, or validation failure stop the run without a misleading update. Outputs are the proposed catalog delta, generated source-development lead section, Source Monitor event, shared Agent Audit Log entry, Actions summary, and retained diagnostic artifact. Workflow failures use the configured GitHub failure notification; routed content changes rely on the assigned pull request.
