---
title: "Run Coordinator Bot Runbook"
agent_id: run-coordinator-bot
display_name: Run Coordinator Bot
agent_type: deterministic-bot
status: disabled
trigger: fixture-or-manual-dry-run
schedule: "Intended 17 4 * * * UTC after separately authorized cutover; not installed in P2"
runtime_id: scripts/arrp_nightly.py
execution_environment: local-transaction-source-only
runtime_config: .github/run-coordinator-bot.json
log_path: framework/records/automation/agent-audit-log.md
print_status: excluded
print_exclusion_reason: "Internal automation configuration."
---

# Run Coordinator Bot Runbook

## Inputs and permitted writes

The coordinator reads the canonical repository, exact fetched remote state,
reviewed runtime, prior typed success state, and runner-supplied fixture or
credential-scoped inputs. It writes only the checkpoint branch, linked
transaction worktree, owner-only run state, and declared run outputs.
Validation is fail-closed. Canonical publication remains disabled through P4;
only expressly approved fixtures may use the P4 broker. Any authority,
identity, lock, path, credential, or schema failure is an explicit stop.

The Run Coordinator is the only authoritative ARRP chain orchestrator. In P2
it is disabled for canonical and unattended execution. Fixture runs may prove
the local transaction, retained deterministic stages, queue and context
construction, and one sealed fixture Elim turn without publication.

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
deterministic Project snapshot, context registry, strict Elim result schema,
and the exact transaction worktree delta.

It writes owner-only atomic status and cadence state, one bounded run
directory, typed stage outputs, queue/route/context artifacts, Elim JSONL and
result, and preservation metadata. It may checkpoint authorized daytime work
and create the transaction branch/worktree through the P1 boundary. P2 does
not authorize a remote branch, pull request, merge, Project mutation,
Discussion reply, workflow dispatch, deployment, or service change outside an
expressly approved P4 fixture.

## Ordered work

After lock, repository preflight, fetch, inventory, checkpoint, and transaction
worktree creation, the coordinator runs the due deterministic stages in the
order declared in `.github/run-coordinator-bot.json`. `not_due` requires a
present, valid, hashable, in-cadence prior typed output; otherwise the stage is
due. Blocking failure stops dependent work. A degraded stage may permit
independent work, but becomes blocking when the selected unit depends on it.

The coordinator then builds the integrity feed, current queue, selected
context route, and hash-bound context packet. At most one work unit is
selected. If no ordinary unit exists, one bounded governance-discovery unit
may be selected when due.

Before Elim, it performs the official usage-reserve check once. A launch uses
one fresh ephemeral isolated Codex process with no inherited configuration,
rules, memories, hooks, plugins, MCP servers, subagents, credentials, web
search, or shell network. The coordinator validates the strict result and
exact Elim-created path delta. P2 requires `github_action_requests` to be an
empty array.

## Stop and preservation rules

Unknown repository state, protected runtime drift, stale or malformed stage
evidence, route/hash failure, source-commit mismatch, network or credential
exposure, Git metadata mutation, protected Elim writes, strict-result failure,
timeout, or post-lock canonical change fails closed. Preserve the branch,
worktree, run directory, completed nonconflicting outputs, exact path-only
evidence, and next action. Release all descriptors and the operating-system
lock in `finally`. Never rerun Elim automatically.

The P4 success boundary adds exact App-authored ordinary/protected PR,
workflow-file exception, reversible Project-field, credential-failure, and
normal-Actions-trigger fixtures. A successful fixture does not enable,
install, schedule, or broadly publish the bot.
