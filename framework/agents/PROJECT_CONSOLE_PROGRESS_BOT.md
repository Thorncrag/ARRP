---
title: "Project Console Progress Bot Runbook"
agent_id: project-console-progress-bot
display_name: Project Console Progress Bot
agent_type: deterministic-bot
status: enabled
trigger: schedule-manual-and-config-push
schedule: "17 10 * * * UTC"
runtime_id: .github/workflows/project-console-progress.yml
execution_environment: github-actions
runtime_config: .github/project-console-progress.json
log_path: framework/logs/AGENT_AUDIT_LOG.md
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Project Console Progress Bot Runbook

The Project Console Progress Bot reads the authoritative GitHub Project and issue registry, calculates the configured Review Ready progress metrics and six-stage board, and publishes generated data and bounded history to `project-console-data`. It does not mutate Project fields or substantive records and never edits the generated data branch by hand.

A missing Project credential leaves the scheduled refresh inactive with an explicit notice. Schema, registry, identity, completeness, and publication failures fail closed. Material publication or routed failures use the shared Agent Audit Log; a clean refresh remains in Actions and bounded Console history.

The JSON manifest and GitHub workflow are deployed projections of this runbook and must match its identity, status, cadence, data branch, and source paths.

## Inputs and permitted writes

The bot reads GitHub Project 2, `inventory/github_issue_registry.csv`, the configured field mappings, readiness rule, baseline, target, and bounded history seed. It is read-only with respect to GitHub Issues, Project fields, canonical records, scores, and lifecycle decisions. Its only write is generated progress data and bounded history on `project-console-data`; it never writes a progress dashboard to `main`.

## Publication and review

Successful generated output is published directly to the dedicated data-only branch because it is a deterministic projection, not a substantive decision. Human review is required for changes to eligibility, readiness definitions, baseline, target, or field mappings; those changes occur through ordinary review of the manifest and governing records on `main`, not by editing generated data.

## Validation, stop, and output

The bot validates Project authentication, registry joins, unique identifiers, recognized six-stage development levels, score/readiness consistency, complete record accounting, schema, and bounded history before publication. A missing Project credential leaves the refresh inactive with an explicit notice; malformed inputs, unmatched or ambiguous authority records, publication failure, or validation failure stop or visibly flag the run rather than repairing Project state. Outputs are `progress.json`, bounded history, and the Console progress projection. Failures use the configured GitHub workflow notification path.
