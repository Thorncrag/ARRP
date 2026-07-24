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
log_path: framework/logs/AGENT_AUDIT_LOG.md
domain_event_log: framework/logs/SOURCE_MONITOR_LOG.md
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

Material changes are committed only to the dedicated `automation/presidential-directives-monitor` proposal branch and presented through an owner-assigned pull request. The branch is not a shared substantive branch. No-change runs create no commit, and every proposed registry change requires human review before merge.

## Validation, stop, and output

Before publication, the bot validates the configured administration coverage, Federal Register host and response structure, document identity, pagination bounds, fingerprints, last-changed values, and its authorized file boundary. Missing or malformed inputs, provider/schema failure, identity ambiguity, boundary violations, commit/push failure, or validation failure stop the run without publishing a misleading update. Outputs are the proposed registry delta, immutable structured stage and source-domain events, Actions summary, and retained diagnostic artifact. Workflow failures enter the Run Coordinator failure state and notification path; routed content changes rely on the assigned pull request.
