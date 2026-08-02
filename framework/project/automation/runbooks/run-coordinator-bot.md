---
title: "Run Coordinator Bot Runbook"
agent_id: run-coordinator-bot
display_name: Run Coordinator Bot
console_purpose: "Orchestrates the local automation chain and its reviewed publication transaction."
agent_type: deterministic-bot
status: enabled
trigger: scheduled-local-chain-or-owner-manual
schedule: "02:00 America/New_York through com.thorncrag.arrp-nightly, with RunAtLoad due evaluation"
runtime_id: scripts/arrp_nightly.py
execution_environment: reviewed-local-runtime-and-transaction-worktree
runtime_config: framework/project/automation/configuration/bots/run-coordinator-bot.json
log_path: owner-local:records/automation/agent-audit-log.md
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Run Coordinator Bot Runbook

## Inputs and permitted writes

The coordinator reads the canonical repository, exact fetched remote state,
reviewed runtime, prior typed success state, and runner-supplied
credential-scoped inputs. It writes only the checkpoint branch, linked
transaction worktree, owner-only run state, declared run outputs, and the
exact reviewed publication transaction. Validation is fail-closed. Any
authority, identity, lock, path, credential, or schema failure is an explicit
stop.

The Run Coordinator is the only authoritative ARRP chain orchestrator. P6
enables one scheduled local chain at 02:00 `America/New_York`, with
`RunAtLoad` performing only the runner's due and idempotency evaluation.
Fixture and explicit dry-run modes remain available for validation, but do not
create a second scheduler or runtime.

A handoff identifies unfinished continuation state only; it does not establish
runtime liveness. A successfully completed task requires an `Inactive` handoff,
while unfinished work retains the exact `Paused` or `Blocked` checkpoint.

## Authority

The coordinator may make deterministic decisions about locks, repository and
runtime identity, exact manifests, cadence, stage ordering, queue selection,
context routing, schema validation, path boundaries, preservation, exact App
token downscoping, pull-request head/base/check readback, and registered
semantic intents. It cannot interpret legal or factual significance, answer a
human-reserved question, give Elim credentials, or bypass protected review.

The local configuration and [ARRP autonomous-execution
policy](../autonomous-execution.md) define the exact chain. Former GitHub
workflows, dispatcher controls, data branches, workflow events, and Actions
artifacts are retired implementation history and are not runtime inputs.

## Inputs, state, and outputs

The coordinator reads the canonical repository and remote identity, fetched
`origin/main`, current handoff, reviewed runtime manifest, stage
configurations, prior `last-success.json`, current canonical records,
deterministic Project snapshot, governed append-only repository-gate
declarations, a complete authenticated open-pull-request inventory, context
registry, strict Elim result schema, and the exact transaction worktree delta.
Every `owner-local:` input and output resolves through the [ARRP Owner-Local
Runtime Authority](../owner-local-runtime.md); neither a runbook value nor a
caller-selected path can redefine the production state root.

It writes owner-only atomic status and cadence state, one bounded run
directory, typed stage outputs, queue/route/context artifacts, Elim JSONL and
result, and preservation metadata. It may checkpoint authorized daytime work
and create the transaction branch/worktree. Only deterministic broker code may
mint a downscoped credential, publish the exact run branch, open or merge the
exact pull request, perform a registered semantic action, or read back Pages
and synchronization state. Retired workflow dispatch, data-branch
publication, bot branches, and persistent control services have no authority.

The reviewed runtime binds context generation to the exact matching
`worktrees/<run-id>` and `runs/<run-id>` pair beneath the fixed owner-local
state root. It does not pass a configurable production root through the
environment. Repository, run, state, and fixture paths are distinct typed
authorities; a mismatch, symlink, escape, unsafe owner-local mode, or fixture
overlap fails before context or disclosure-sensitive state is read.
The named companion workspace remains protected inactive staging and is not a production
fallback.

## Ordered work

After lock, repository preflight, fetch, inventory, checkpoint, and transaction
worktree creation, the coordinator uses the shared repository-gates producer
to reconcile the complete live pull-request inventory with the governed
declaration log. The current snapshot is schema-validated and hash-bound to the
run manifest before any dependent stage begins. An incomplete inventory,
invalid declaration, changed declared head, unavailable required check or
review state, or other inability to prove completeness fails closed. A
retained last-good snapshot may explain the prior trustworthy state, but it
cannot supply a current zero or authorize execution.

An active gate applies only to its declared run scope and affected stages.
Applicable stages are stopped or skipped, and the exact gate ID is recorded in
the attempt outcome. A gate affects the latest-attempt blocker count only when
the coordinator actually applied it to that attempt; other active gates remain
forward-looking repository gates. The historical run snapshot is immutable
after the attempt. Later Console refreshes publish a separate current
repository-gates snapshot and do not rewrite that historical outcome.

The coordinator then runs the due deterministic stages in the order declared
in `framework/project/automation/configuration/bots/run-coordinator-bot.json`. `not_due` requires a present, valid,
hashable, in-cadence prior typed output; otherwise the stage is due. Blocking
failure stops dependent work. A degraded stage may permit independent work,
but becomes blocking when the selected unit depends on it.

The coordinator then builds the integrity feed, current queue, selected
context route, and hash-bound context packet. At most one work unit is
selected. If no ordinary unit exists, one bounded governance-discovery unit
may be selected when due.

Before Elim, it performs the official usage-reserve check once. A launch uses
one fresh ephemeral Codex process with bounded per-run state. Reviewed
owner-local controls isolate authentication, execution, tools, network, and
host capabilities; Elim receives no GitHub credential or hosted mutation
authority. The coordinator preserves result evidence before returning a
process failure or timeout, terminates the timed-out process group, validates
the strict result, and verifies the exact Elim-created path delta. Any
`github_action_requests` entry must match the
registered broker schema and remains subject to deterministic authorization,
prior-state verification, execution, and exact readback.

The strict Elim result also carries a required bounded `incident_reports`
array. Elim reports are advisory; the coordinator independently validates,
sanitizes, deduplicates, and appends accepted occurrences to the immutable
Operational Incident event record. Typed failed or degraded run stages are
recorded independently from the finalized run chain, preserving their exact
run and role identities. A repeated typed failure joins an existing unresolved
incident; it does not erase or replace the earlier occurrence.

## Stop and preservation rules

Unknown repository state, protected runtime drift, stale or malformed stage
evidence, route/hash failure, source-commit mismatch, network or credential
exposure, Git metadata mutation, protected Elim writes, strict-result failure,
timeout, or post-lock canonical change fails closed. Preserve the branch,
worktree, run directory, completed nonconflicting outputs, exact path-only
evidence, and next action. Release all descriptors and the operating-system
lock in `finally`. Never rerun Elim automatically. Elim timeout, crash, or
invalid-result evidence is written in sanitized form to the owner-only
failure-safe incident spool before the transaction returns. A later valid
transaction reconciles that spool into the canonical incident record, so the
signal does not depend on Elim producing a report or on generated-view
completion.

P4 and P5 proved the exact App-authored ordinary/protected PR,
workflow-file exception, reversible Project-field, credential-failure, and
normal-Actions boundaries. The production coordinator retains the one lock
through dynamic governing-path classification, reviewed-runtime execution,
App push, bounded post-push PR metadata and head/base readback, registered
Project synchronization, exact-head merge, exact-SHA Pages success, canonical
fast-forward, and bounded successful-worktree removal. The terminal status
preserves the sealed Elim unit and outcome. Any failure preserves the branch,
worktree, run directory, and independent status.
