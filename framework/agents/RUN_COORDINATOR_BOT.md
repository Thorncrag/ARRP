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

One daily kickoff, a pending public-submission event, a manual dispatch, or a due periodic Review Epoch may authorize the complete chain, including a conditional Elim launch. A push to `main` starts only the deterministic refresh portion: it may update integrity and progress inputs, but it must set `launch_recommended: false` even when the refreshed queue contains LLM-owned work. That work waits for the daily schedule, an eligible event, or explicit manual dispatch. Events arriving while a chain is active or within its configured debounce window are consolidated into the current or next Chain ID. GitHub concurrency serializes cloud workflow runs. The sole host-side liveness authority is one operating-system-held dispatcher lease, which serializes local dispatch and Elim execution and is automatically released if its owning process terminates.

Before any stage, the coordinator records the baseline commit and verifies current `main`, authenticated access required by the due stages, and a clean worktree. It must not overlap a queued unit with an expressly active interactive task affecting the same issue or files; an unrelated or abandoned non-Inactive handoff is not a global liveness lock. `CURRENT_AUDIT.md` identifies unfinished continuation state only and never proves that an agent, bot, chain, task, or process is live. The dispatcher lease is the host-liveness authority. Its acquisition-specific owner record stores the dispatcher process, current Chain ID, invocation, Elim task when known, preserved output path, and a continuously refreshed heartbeat for diagnosis and Console display; the owner record is not a second lock. Every owner update and release must present the same acquisition token. Legacy directory locks use only the tested dead-owner or expired-ownerless migration path. An abandoned operating-system lease is available automatically to the next dispatcher. Recovery before Elim begins records a coordinator failure without fabricating an Elim run; recovery after Elim begins marks Elim failed, preserves the task and JSONL output as incomplete evidence, creates a human Action Item and notification, projects the error to the Console, and requires a fresh current chain before substantive work resumes.

## Chain order

1. Acquire the exclusive chain lock and establish the Chain ID, trigger set, baseline commit, freshness boundary, and usage-preflight availability.
2. Evaluate every registered bot against its due predicate. Run due external-observation stages, including Case Monitor Bot, Presidential Directives Bot, Source Checker Bot, and the public-intake collector and reconciliation pass. Record `not_due` when a prior successful result remains current.
3. Refresh authoritative Project and Console progress data when required.
4. Run Project Integrity Bot after all other due deterministic inputs so it can detect missing, stale, failed, or contradictory outputs and lifecycle or repository inconsistencies.
5. Compile the structured work queue and exact-source context manifests. Queue construction detects, prioritizes, and routes work but grants no authority.
6. Apply the Codex usage reserve and per-run soft-target policy. Each Elim invocation receives a unique host-owned baseline and a host-attested snapshot refreshed every 60 seconds; the dispatcher records the path and freshness limit in the local Chain Manifest, and Elim must consume that snapshot rather than launch a sandbox probe. Invoke Elim only when at least one current eligible item requires LLM judgment. A clean, blocked-only, or deterministic-only queue closes without a model turn.
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

The chain marks a comprehensive Elim review due every two weeks while the project or automation architecture remains actively changing. After several clean reviews demonstrate stability, only recorded human approval may move the cadence to monthly. For deterministic off-cycle detection, the coordinator constructs the current registered governing boundary from every `governing: true` document and its integration-pinned hash, adds the current `context-routes.json` hash, and compares the exact result with the latest completed Review Epoch. Any difference in registered membership, path, governing hash, or registry hash marks an off-cycle epoch due because the bot cannot judge materiality. A governing file that no longer matches its pinned registry hash, or other runtime-only governing drift that does not form a valid registered boundary, is an integrity failure and stops safely rather than being accepted as an epoch trigger; intentionally runtime-hashed non-governing records are outside the comparison.

The epoch record, look-back scope, and boundary schema are governed by the Agent Operating Rules' [Comprehensive review epochs](../agent-rules/autonomous-execution.md#comprehensive-review-epochs). The coordinator supplies `epoch_id`, `triggering_run_id`, `baseline_commit`, `completion_commit`, `governing_hashes` including the registry hash, `project_snapshot`, `registry_snapshot`, `reviewed_domains`, `resolved_findings`, `unresolved_findings`, `automation_health`, `sampling_record`, `completed_at`, `next_due_at`, `cadence_status`, `stability_status`, and `triggering_reason`. It also supplies changes since the prior boundary, cross-project invariants, workflow health, and the rotating sample. Every prior unresolved finding must be copied forward into `unresolved_findings` until the reviewing agent records its resolution in `resolved_findings`; the coordinator may verify continuity but does not decide whether a finding is satisfied. When the epoch is due, the comprehensive work unit overrides ordinary queue ordering for context selection, and the manifest attachment step rejects a non-comprehensive packet.

## Output, logging, and Console

The current generated projection is `run-chain.json` on the data-only `project-console-data` branch. It exposes the Chain ID, trigger set, baseline commit, stage due and health states, timestamps, retries, output hashes, repository state, failures and degradation, queue counts, Elim launch decision and reason, Review Epoch state, usage summary, and exact next action. It contains no secrets, private intake data, or rejected contributor text.

Material stage events use immutable structured provenance and the shared Agent Audit Log under the common rule. Clean no-op chains remain in bounded Actions and Console history. Human-readable logs may be rendered from structured events so several bots do not edit one shared Markdown file from conflicting branches. Rendering does not replace canonical issue-audit records or create authority.

## Validation and stop conditions

The bot validates registry completeness, runbook/runtime agreement, stage dependency order, exclusive-lock ownership and lease recovery, due calculations, freshness hashes, queue schema and unique IDs, intake cursor monotonicity, usage-gate results, Elim-last ordering, complete record accounting, generated projection schema, and the final `CURRENT_AUDIT.md` handoff state when Elim participated. It stops without launching Elim on a dirty or incompatible repository, live or unsafe lock, missing blocking input, stale or contradictory manifest, invalid queue or context packet, unavailable required authentication, unavailable usage reading, unsafe recovery, or failed validation. It preserves the exact failed stage and next action and notifies the user when attention is required. Dispatcher or Codex termination before verified closeout is a failed run, never a silent open handoff or a successful completion. A successfully completed task requires an `Inactive` handoff verified on clean, synchronized `main`; an unfinished failed, blocked, or intentionally suspended task requires an exact `Paused` or `Blocked` checkpoint.
