---
title: "Autonomous and Scheduled Execution Standard"
dependencies:
  - "../../AGENT_OPERATING_RULES.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Autonomous and Scheduled Execution Standard

Load this standard for every autonomous, scheduled, event-triggered, batched,
or persistent-agent run. A project-specific automation policy and the
applicable runbook must define the exact implementation. Neither may enlarge
the Framework, common agent rules, or authority granted by the human owner.

## Authorization and bounded purpose

Autonomous execution requires express human authorization or an enabled,
approved persistent-agent configuration. The authorization must identify the
permitted objective, actors, inputs, outputs, external systems, publication
boundary, and human-reserved decisions. A schedule, detector, queue, generated
context packet, or successful validation result never creates authority.

## One coordinated chain

Use one authoritative coordinator for related scheduled, event-triggered, and
manual automation. Deduplicate overlapping triggers, assign one durable run
identity, serialize the ordered stages, and retain exact stage outcomes.
Independent clocks may observe or notify, but they must not launch competing
change-producing chains.

## Locking and human-work deferral

Acquire one operating-system-enforced exclusive lease before changing shared
state. Bind owner and run identity to the acquisition, maintain diagnostic
status without treating a heartbeat as a second lock, and release the lease
automatically when the owner terminates. Recover stale state only from
verifiable dead-owner or expired-ownerless evidence.

Automation must defer when a human owns the workspace or when the repository
contains unexplained work. It must not stash, reset, overwrite, absorb, rebase,
or discard human changes.

## Clean preflight and isolation

Before substantive execution, verify the authoritative repository identity,
branch, exact reviewed remote revision, clean state, runtime identity,
configuration, dependencies, and required inputs. Dirty, ahead, divergent,
stale, contradictory, or inconclusive state fails closed.

Run an LLM worker in a fresh bounded environment when isolation is materially
useful. Keep canonical Git metadata, credentials, publication, and other
privileged controls outside the model-writable boundary. Temporary clones or
worktrees are execution surfaces, not competing authoritative repositories.

## Deterministic and LLM responsibilities

Keep scheduling, locking, repository preflight, exact refresh, queue
construction, schema and path checks, validation, secret detection, commit-tree
verification, credential handling, publication, readback, timestamps, and
provenance deterministic. Use an LLM for contextual research, interpretation,
drafting, prioritization, and discovery within its granted authority.

The LLM must declare a structured result and exact changed-path boundary. A
trusted deterministic process independently verifies that result before any
commit, external write, merge, or publication.

## Bounded work queues

A deterministic queue identifies work but does not authorize it. Each item
must have stable identity, owner, class, source revision, freshness, required
authority, exact next action, retry state, and any blocker. Queue and context
inputs must be rebuilt or rejected when stale, missing, or contradictory.

Enumerated work is a minimum coverage floor, not a ceiling on relevant
discovery. A connected finding may become a separate bounded work unit, but
discovery never enlarges implementation authority. Preserve unresolved
findings with provenance, owner, disposition, next action, and next trigger;
absence from a later scan is not closure.

## Independent failure observability

Write a minimal local `run started` record before the ordinary chain and update
it through an independent finalizer or equivalent failure path. The failure
signal must not depend on reaching the normal generated-view or publication
stage.

Where remote health or a management interface is retained, accept its
independent feeds separately. One missing projection must not erase valid
evidence from another. Consolidate repeated instances of the same prerequisite
failure while preserving occurrence history and affected run identities.

## Review epochs

Supplement bounded ordinary runs with periodic comprehensive review of the
registered governing boundary and carried-forward unresolved findings.
Material governing-boundary change makes an off-cycle review due. Record the
exact baseline and completion revisions, governing hashes, reviewed domains,
resolved and unresolved findings, health evidence, sampling, completion time,
next due time, and trigger.

A review epoch may focus later work on intervening change, but it must not
erase unresolved findings, silently omit a governing module, decide a
human-reserved question, or substitute for any required substantive audit.

## Preservation and fail-closed recovery

Preserve completed work, structured output, logs, exact inputs, and rollback
provenance when any stage fails. Recovery must start from a newly verified
current boundary or a narrowly recognized preserved state whose identity,
parent, paths, validation, and external status can all be proved.

Unexpected paths, unknown artifacts, invalid locks, stale baselines,
authentication failures, usage-limit stops, failed or timed-out validation,
remote races, interrupted publication, and readback mismatches fail closed.
Never bypass protection, force-push shared history, perform destructive
cleanup, or infer success from a partial result. Route any credential,
unsafe-external-action, or human-reserved requirement to the human owner while
continuing only independent nonconflicting work.
