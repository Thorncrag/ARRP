---
title: "Source Checker Bot Runbook"
agent_id: source-checker-bot
display_name: Source Checker Bot
agent_type: deterministic-bot
status: report-only-pilot
trigger: schedule-or-manual
schedule: "23 6 * * 0 UTC; weekly Sunday near 2:23 a.m. EDT / 1:23 a.m. EST"
runtime_id: .github/workflows/source-checker-bot.yml
execution_environment: github-actions
runtime_config: .github/source-checker-bot.json
log_path: framework/logs/AGENT_AUDIT_LOG.md
current_report: framework/reports/SOURCE_CHECKER_REPORT.md
current_data: project-console-data/source-checker.json
exception_review: human-or-llm
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Source Checker Bot runbook

The Source Checker Bot follows the project Framework and Agent Operating Rules. This runbook is its authoritative identity, narrower authority, and operational configuration.

## Purpose and success criterion

Systematically check every nonblank URL in the designated source catalogs and report whether it remains reachable and identifies the source the catalog describes. A successful run accounts for every eligible catalog row, retains bounded machine-readable history, and makes no substantive citation substitution.

## Operation

The bot runs weekly and may be dispatched manually. It uses paced HTTP `GET` requests, follows redirects, retries transient failures with backoff, records final URLs and content types, and compares stable identifiers and available HTML title text with catalog metadata. It classifies each row as `verified`, `identity-preserving redirect`, `access restricted`, `transient failure`, `broken`, `identity mismatch`, or `review required`.

The configured mode is **report-only**. The bot may refresh its current Markdown and JSON reports and publish bounded Console-ready data. It must not edit a source row, replace a citation, alter a supported proposition, or infer that a merely similar document is an acceptable substitute. Ambiguity, access controls, identity changes, and possible replacements are routed for human or LLM review.

When the current Markdown report changes, the bot may replace only its dedicated disposable `bot/source-checker-report` proposal branch using lease-protected replacement and may open or refresh the corresponding pull request. It may never force-push `main`, a protected branch, a human-owned branch, or a shared working branch.

## Failure and escalation rules

- A failed `HEAD` request is never treated as proof of breakage; the scanner uses `GET`.
- `401`, `403`, `407`, `429`, and bot/challenge responses are access restrictions, not broken links.
- Timeouts, DNS failures, and `5xx` responses remain transient until configured retries are exhausted.
- Repeated `404` or `410` responses are broken; other unexpected `4xx` responses require review.
- A redirect is identity-preserving only when stable identifiers remain present or the observed title remains compatible with catalog metadata. Otherwise it requires review.
- A stable identifier contradiction is an identity mismatch. The bot never resolves that mismatch by changing the catalog.
- Scanner or catalog-structure failure fails the run without publishing a misleading partial success.

The reports contain no response bodies and store only bounded diagnostic text. Material remediation, if later approved, is a separate reviewed work unit recorded through the shared agent provenance process.

## Inputs and permitted writes

The bot reads every nonblank URL and its stable source metadata from `inventory/sources.csv` and `inventory/sources-pending.csv`, plus up to 12 prior run summaries from the data branch. It may write only the generated JSON feed/history, replaceable Markdown report, and shared provenance entry. It may not edit either source catalog, substitute a source, alter a proposition, or decide that a different document is equivalent.

## Publication and review

The structured feed publishes to `project-console-data`. A changed Markdown report is proposed only on `bot/source-checker-report`, using lease-protected replacement, and requires review before merge. Broken, identity-mismatch, and review-required results also appear in the unified Integrity queue; remediation is performed separately by an authorized human or LLM agent.

## Validation, stop, and output

The bot validates catalog schemas, complete URL accounting, allowed classification values, request bounds, per-domain pacing, retry behavior, final identity signals, output schema, bounded history, and the no-catalog-mutation boundary. Catalog/schema failure, incomplete accounting, scanner exception, output/publication failure, unauthorized file changes, or validation failure stops the run without publishing partial success. Outputs are the current JSON results, 12-run bounded history, current Markdown report proposal when changed, Integrity findings, Agent Audit Log entry for material routing, Actions summary, and retained artifact. Workflow failures use the configured GitHub failure notification; findings route through the Console and report pull request.
