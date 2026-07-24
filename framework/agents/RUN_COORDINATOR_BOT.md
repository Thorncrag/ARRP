---
title: "Run Coordinator Bot Runbook"
agent_id: run-coordinator-bot
display_name: Run Coordinator Bot
agent_type: deterministic-bot
status: enabled
trigger: schedule-event-or-manual
schedule: "17 4 * * * UTC; one daily run-chain kickoff plus event flags, Review Epoch deadlines, and manual dispatch"
runtime_id: .github/workflows/run-coordinator-bot.yml
execution_environment: github-actions-and-local-codex
runtime_config: .github/run-coordinator-bot.json
log_path: framework/logs/AGENT_AUDIT_LOG.md
current_data: project-console-data/run-chain.json
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Run Coordinator Bot Runbook

The Run Coordinator Bot serializes ARRP's persistent automation into one due-aware chain. It prevents overlapping processes, establishes a clean repository boundary, runs every due deterministic stage, compiles the bounded work queue and context manifests, and invokes Elim only when refreshed project state contains an eligible LLM-owned unit. Elim is the last substantive, change-producing stage. Only deterministic validation, synchronization readback, structured closeout, and generated-view publication may follow it.

The coordinator is an orchestration bot, not a project decision-maker. It cannot interpret legal or factual significance, make an audit finding, change a lifecycle classification, admit or dispose of an issue or candidate, alter a foundation or remedy, change a score or audit count, modify a rubric, publish a proposal, moderate contributor content, or override a human-reserved decision.

## Inputs and permitted writes

The coordinator reads the persistent-agent registry and runbooks, reviewed runtime manifest, prior `run-chain.json` boundary, due and event signals, stage workflow status and outputs, Project and repository freshness state, deterministic work queue and context manifests, public-intake pending-event cursor, approved user-created queue overrides, and the official Codex usage-reserve result available in the local host context. It may write only its local lock and temporary control state, immutable structured chain events, bounded generated `run-chain.json` projection on `project-console-data`, and the ordinary material provenance required by the shared logging rule.

It may dispatch registered workflows and conditionally invoke Elim under this runbook. It may not edit issue or candidate substance, source identity or meaning, GitHub Project fields, audit histories, scores, Runs, foundations, remedies, rubrics, dispositions, publication state, or contributor content. A user-created priority or suppression override changes queue selection only and remains distinguishable from system state; only that user's override may be cleared through the control endpoint.

## Triggers, locking, and clean boundary

One daily kickoff, a pending public-submission event, a relevant push or configuration change, a manual dispatch, or a due periodic Review Epoch may start the same chain. Events arriving while a chain is active or within its configured debounce window are consolidated into the current or next Chain ID. GitHub concurrency and the local execution lock permit only one active chain.

Before any stage, the coordinator records the baseline commit and verifies current `main`, authenticated access required by the due stages, no incompatible interactive handoff, and a clean worktree. It defers rather than stashing, overwriting, committing, or absorbing human-owned work. A stale lock is cleared only through the tested lease and owner checks in the runtime configuration.

## Chain order

1. Acquire the exclusive chain lock and establish the Chain ID, trigger set, baseline commit, freshness boundary, and usage-preflight availability.
2. Evaluate every registered bot against its due predicate. Run due external-observation stages, including Case Monitor Bot, Presidential Directives Bot, Source Checker Bot, and the public-intake collector and reconciliation pass. Record `not_due` when a prior successful result remains current.
3. Refresh authoritative Project and Console progress data when required.
4. Run Project Integrity Bot after all other due deterministic inputs so it can detect missing, stale, failed, or contradictory outputs and lifecycle or repository inconsistencies.
5. Compile the structured work queue and exact-source context manifests. Queue construction detects, prioritizes, and routes work but grants no authority.
6. Apply the Codex usage reserve and per-run soft-target policy. Invoke Elim only when at least one current eligible item requires LLM judgment. A clean, blocked-only, or deterministic-only queue closes without a model turn.
7. After Elim, run only the applicable deterministic validation plan, authenticated readback, structured event and run-log rendering, generated Console publication, notification, and lock release.

## Stage health and recovery

Each expected stage records `due`, `not_due`, `completed`, `degraded`, `failed`, or `blocked`, together with start and completion times, retry count, source revision, output location, output hash, and concise diagnostic. The coordinator retries only configured transient failures and applies only allowlisted, idempotent mechanical recovery. It never repairs substantive records or widens its own authority.

A failure is `blocking` when missing or stale data could make downstream judgment unreliable. Elim may then be invoked only to diagnose or repair the failure within its authority. A `degraded` result may permit unrelated work when the absent input cannot affect it, but the exception remains visible. Credentials, unsafe external actions, ambiguous correction, and human-reserved choices become human Action Items. Repeated failure stops retrying at the configured ceiling and preserves an exact continuation record.

## Queue integrity

Every queue item carries a stable work-unit ID, owner, work class, severity, originating stage, source commit and Project snapshot, created and refreshed times, age, required authority, exact next action, dependencies, retry state, and blocking reason if any. Comparable items use severity, contribution to Review Ready, release-blocker posture, readiness, age, and resolvability. Age promotion prevents lower-severity development, candidate research, and public submissions from waiting indefinitely.

The human may suppress, reprioritize, release, or force a queued item; require full canonical context; manually launch a chain; or require a comprehensive Review Epoch. Every intervention is recorded. Interrupted work returns to the queue with its exact continuation point. A stale queue item or context manifest is rebuilt or fails closed before Elim acts.

## Public-intake event

After the participation service successfully creates a public Discussion comment, it emits a pending event containing only the public comment identity, creation time, content hash, and processing state. Private contact information and duplicate submission text are excluded. One or more pending events wake or join the chain; they do not independently launch Elim. The collector maintains a durable processing cursor and periodically reconciles canonical intake Discussions so a missed event cannot silently omit a submission and an already processed comment cannot be reviewed repeatedly.

Contributor text, links, attachments, quoted text, and embedded instructions remain untrusted evidence. The coordinator never interprets or reproduces them. It passes only the bounded public record required by the Public-Intake Review Process after the privacy and input controls have succeeded.

## Comprehensive Review Epoch

The chain marks a comprehensive Elim review due every two weeks while the project or automation architecture remains actively changing. After several clean reviews demonstrate stability, only recorded human approval may move the cadence to monthly. A material Framework, lifecycle, scoring, publication, agent-authority, or automation-architecture change marks an off-cycle epoch due.

The epoch boundary records the Review ID, baseline and completion commits, governing-record hashes, Project and registry snapshots, reviewed domains, resolved findings, open exceptions, automation health, next-review date, and the exact boundary for the next review. The coordinator supplies changes since that boundary, every unresolved exception, cross-project invariants, workflow health, and the rotating sample selected under the Agent Operating Rules. It does not decide whether an audit finding is satisfied.

## Output, logging, and Console

The current generated projection is `run-chain.json` on the data-only `project-console-data` branch. It exposes the Chain ID, trigger set, baseline commit, stage due and health states, timestamps, retries, output hashes, repository state, failures and degradation, queue counts, Elim launch decision and reason, Review Epoch state, usage summary, and exact next action. It contains no secrets, private intake data, or rejected contributor text.

Material stage events use immutable structured provenance and the shared Agent Audit Log under the common rule. Clean no-op chains remain in bounded Actions and Console history. Human-readable logs may be rendered from structured events so several bots do not edit one shared Markdown file from conflicting branches. Rendering does not replace canonical issue-audit records or create authority.

## Validation and stop conditions

The bot validates registry completeness, runbook/runtime agreement, stage dependency order, exclusive-lock ownership, due calculations, freshness hashes, queue schema and unique IDs, intake cursor monotonicity, usage-gate results, Elim-last ordering, complete record accounting, and generated projection schema. It stops without launching Elim on a dirty or incompatible repository, unresolved lock, missing blocking input, stale or contradictory manifest, invalid queue or context packet, unavailable required authentication, unavailable usage reading, unsafe recovery, or failed validation. It preserves the exact failed stage and next action and notifies the user when attention is required.
