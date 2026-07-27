---
title: "Governing Context Routing"
status: active
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Governing Context Routing

This file governs how agents and bots assemble shared ARRP context from the independently loadable framework modules. The machine-readable registry is [`context-routes.json`](project/automation/context-routes.json). The registry is a router and freshness control, not a substitute for any authority it identifies.

## Required Floor

Every routed context packet begins with:

1. the constitutional and methodological kernel in [`FRAMEWORK.md`](FRAMEWORK.md);
2. the universal execution kernel in [`AGENT_OPERATING_RULES.md`](AGENT_OPERATING_RULES.md); and
3. the live continuation state in
   [`records/handoffs/current-task.md`](records/handoffs/current-task.md).

The first two are stable governing records whose integration-pinned hashes must match the registry. [`records/handoffs/current-task.md`](records/handoffs/current-task.md) is intentionally mutable and is read and hashed at packet-build time. Its runtime hash is preserved in packet provenance, but an ordinary checkpoint update does not require editing the registry.

These records are a floor. They do not by themselves supply all context required for an operation.

## Additive Routing

Context routing uses a union, not a first-match rule:

1. select the profile for the primary operation;
2. add every capability implicated by the requested work;
3. resolve the complete dependency closure of all selected modules;
4. add the applicable persistent-agent runbook sections and task-specific records; and
5. expand again before performing any newly implicated operation.

Selecting one profile never excludes a second applicable capability. For example, substantive issue work that changes a GitHub lifecycle field requires both the issue-development and GitHub-lifecycle context. Issue work that becomes a Change Audit also requires the change-control context before the dependent change is made.

Dependencies are directional prerequisites. They guarantee that a selected module brings its minimum shared authorities with it; they do not imply that every file linked from the module is always required. Circular subject relationships are represented by capabilities and task-time expansion rather than circular machine dependencies.

## Profiles and Capabilities

Profiles provide deliberately narrow starting sets for recurring Elim operations:

| Profile | Primary use |
| --- | --- |
| `integrity_reconciliation` | Investigating and resolving the integrity queue before other Elim work. |
| `issue_development` | Developing an admitted issue after its governing foundation is sufficient. |
| `candidate_research` | Investigating a formal Horizon candidate within Elim's recommendation-only boundary. |
| `issue_audit` | Running and closing T0–T4 issue-quality audits. |
| `change_audit` | Reviewing and propagating a governing or substantive change. |
| `public_intake` | Assessing, routing, and acting within the limited public-intake authority. |
| `github_sync` | Reconciling repository records with GitHub Issues and Project fields. |
| `comprehensive_review` | Periodic or off-cycle review of every registered governing module. |

Ordinary profiles contain the minimum modules needed to identify the work, obey universal safeguards, and begin the named operation. They intentionally do not pre-load every module that might become relevant later. A profile's `max_bytes` is a fail-closed ceiling for the packet after additive routing, not a preload target; increasing that ceiling does not add any module or capability. Capabilities are additive subject bundles such as issue development, evidence and sources, navigation, audit execution, scoring, publication, interface governance, multi-agent execution, and autonomous execution. They may be added to a profile at packet-build time without defining a new profile for every combination. A task-specific issue page, proposal, audit history, source record, queue, or current external source is not shared governing context and must still be loaded when the operation requires it. An issue dossier may carry a compact, hash-attributed source-catalog projection for routing; the complete canonical row and any current external source must be loaded before evidentiary reliance, source modification, or audit credit.

The stable document IDs in the registry are logical identities. Moving a file does not require renaming its ID. Renaming an ID is a compatibility change and requires a Change Audit of callers, tests, and any persisted route references.

## Dynamic Expansion

Routing is reevaluated when the task changes or the selected context exposes:

- an unfamiliar issue class or operation;
- conflicting or ambiguous authority;
- a human-reserved decision;
- an implicated scoring, publication, interface, source, GitHub, or navigation rule;
- stale, contradictory, or incomplete records; or
- a validation result that points outside the loaded modules.

Load the newly implicated module or capability before taking the action that depends on it. This includes adding the multi-agent capability before delegation and adding candidate, source, evidence, scoring, publication, interface, or GitHub capabilities when the work crosses those boundaries. Preserve provenance for the expanded packet or added source. Bounded context is permission to defer irrelevant material, never permission to ignore a material rule.

## Interactive and Automated Use

For an interactive Codex agent working directly with the user, a route is the minimum complete starting context, not a ceiling. Interactive work remains comprehensive: the agent should inspect additional canonical records, pursue connected questions, and use independent review whenever that improves the requested result.

An automated LLM agent must use a validated bounded packet for the selected operation and may expand only through registered documents, capabilities, task-specific canonical records, and current verified sources. Deterministic bots ordinarily consume the authoritative structured inputs named in their runbooks rather than an LLM context packet, but the same dependency and fail-closed principles govern any shared-rule projection they use.

## Fail-Closed Rules

Automated execution stops before substantive action when:

- a required document, profile, capability, dependency, or exact routed section is missing or unknown;
- an integration-pinned governing hash is absent or stale;
- a runtime-hashed record cannot be read and hashed;
- dependency resolution produces a cycle;
- a route includes a generated or excluded artifact as authority;
- an exact section is duplicated or no longer matches its recorded heading;
- a section or complete packet exceeds its declared byte limit; or
- selected context reveals a material governing gap that cannot be resolved from canonical records.

The run should report the routing failure and preserve completed nonconflicting work. It must not silently omit the failed record, substitute a summary, use an earlier packet, or infer permission from a missing rule.

## Hashes, Generated Artifacts, and Updates

Stable governing documents use integration-pinned SHA-256 values. After an authorized governing edit, update the affected registry hashes in the same reviewed change and validate every impacted profile. The manifest itself is covered by packet provenance rather than registering its own hash, which would create a self-reference.

Generated site output, Console projections, dependency trees, caches, temporary
files, exports, and other rebuildable artifacts are excluded from the registry.
A generated view may be inspected as a validation target, but it does not
become governing context. Records are likewise not shared governing modules;
`records/handoffs/current-task.md` is the narrow required exception because it
supplies live continuation state.

When a new authoritative module is added:

1. give it one stable registry ID and one canonical path;
2. classify whether it is governing;
3. record only acyclic minimum dependencies;
4. add it to every applicable capability or profile;
5. confirm that `comprehensive_review` includes it through `governing: true`; and
6. pin its hash and validate the registry before closeout.

## Comprehensive Review Boundary

The `comprehensive_review` profile automatically includes every document marked `governing: true`, together with dependency closure. It is required for the periodic Review Epoch defined by the autonomous-execution rules. Automated off-cycle detection is deliberately stricter than a bot's materiality judgment: construct the current registered governing boundary from the exact `governing: true` membership, paths, and integration-pinned hashes, add the current `context-routes.json` hash, and compare that complete result with the latest completed epoch. Any difference marks an off-cycle review due. A governing document that differs from its pinned hash, or other runtime-only governing drift that does not form a valid registered boundary, is an integrity failure and must fail closed rather than becoming a silently accepted boundary; intentionally runtime-hashed non-governing records are excluded.

A completed Review Epoch records `epoch_id`, `triggering_run_id`, `baseline_commit`, `completion_commit`, `governing_hashes` including the registry hash, `project_snapshot`, `registry_snapshot`, `reviewed_domains`, `resolved_findings`, `unresolved_findings`, `automation_health`, `sampling_record`, `completed_at`, `next_due_at`, `cadence_status`, `stability_status`, and `triggering_reason`. The recorder must validate the complete comprehensive packet against the current registry and require exact hashes for every governing document plus the registry itself; it must reject a partial, stale, extra, or altered boundary. Every previously unresolved finding remains in `unresolved_findings` until a later epoch explicitly records it in `resolved_findings`; advancing the boundary may not erase it. The next comprehensive review begins from that boundary and investigates changes and carried-forward unresolved items without treating unchanged material as new work. This boundary improves efficiency; it does not authorize omission of any governing module from the review or prevent a look-back when a conflict, omission, or pattern warrants one.
