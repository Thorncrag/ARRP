---
title: "ARRP Agent Authority Policy"
dependencies:
  - "../../AGENT_OPERATING_RULES.md"
  - "../../standards/automation/task-handoffs.md"
  - "../../standards/automation/provenance-and-recovery.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# ARRP Agent Authority Policy

Load this module before an agent performs substantive issue development,
candidate investigation, source development tied to an issue or candidate,
reader-facing characterization, or an autonomous correction that could affect
issue or candidate records. Also load it for ARRP human-decision routing,
current-task handoff state, persistent-agent provenance, or log ownership. It
supplements the universal rules in
[`AGENT_OPERATING_RULES.md`](../../AGENT_OPERATING_RULES.md) and does not
replace the substantive [`FRAMEWORK.md`](../../FRAMEWORK.md), GitHub mechanics
in [`workflow.md`](../github/workflow.md), or a persistent agent's narrower
runbook.

## Issue-Development Lifecycle Trigger

Any request to focus on, research, develop, draft, revise, or otherwise work substantively on an issue invokes the issue-development lifecycle workflow even when the user does not mention an audit or status update. Before editing, read the canonical issue page, linked vehicle, latest audit entry, next step, and authoritative GitHub Project row.

Do not change `Status` merely because a work session starts or stops. Use `Status: Research` when a defined evidence, source, empirical, or candidate-testing investigation is the primary next action; use `Status: Development` when framing, drafting, structural, remedy-design, implementation, or revision work is next. Either Status covers work waiting to begin and work already underway. At closeout, classify maturity under the Framework's [`Post-Admission Development Gates`](../../FRAMEWORK.md#post-admission-development-gates), then synchronize the independent `Development level` and Project `Status` fields through the [`ARRP GitHub Workflow`](../github/workflow.md#issue-development-lifecycle). Do not change `Score` or `Runs` merely because research, drafting, or source work occurred. Do not reduce an established development level when revision begins; preserve it and use `Change audit needed` plus the Status identifying the actual next action or hold until the required targeted review is complete. Separately, confirm that every canonical issue page retains a nonblank lowercase front-matter `status` from the issue-page metadata vocabulary; that field is not the GitHub Project workflow Status.

Apply the canonical [`Issue-Admission Test`](../../FRAMEWORK.md#issue-admission-test) during candidate investigation, the [`Human-Governed Foundation and Delegated Development`](../../FRAMEWORK.md#human-governed-foundation-and-delegated-development) rule before developing an admitted proposal, and the [`Post-Admission Development Gates`](../../FRAMEWORK.md#post-admission-development-gates) when classifying later maturity. Do not replace those canonical gates with a runbook summary or inferred substitute. Elim during an authorized recurring run and an interactive Codex agent working directly with the user may determine from the canonical record that the approved four-part foundation is substantively present and synchronize the lifecycle classification without a separate confirmation. Other scheduled agents may not infer approval. No agent may invent a missing foundation or make a reserved foundational or materially consequential departure.

Candidate work remains recommendation-only. When its runbook expressly authorizes the work, an agent may source-develop a formal `HOR-###` candidate, investigate the canonical admission conclusions, reconcile evidence, examine existing legal remedies and project overlap, prepare neutral alternative-control analysis, and recommend a disposition while preserving `Development level: Candidate`. It may not answer the human reversed-control question, admit, reject, merge, split, defer, retain only as source development, retire, materially reclassify, score, select a proposal foundation, create a formal proposal vehicle, or implement another permanent disposition as part of candidate investigation. A completed investigation is routed to `Human decision needed` with the exact recommendation, any material missing human answer, and remaining uncertainty.

When uncertain, document the question, skip only the disputed action or issue, request human review, preserve completed work, and continue other eligible batch work. Use the [`Post-Admission Development Gates`](../../FRAMEWORK.md#post-admission-development-gates) and consolidated tier-selection indicators under [`Audit Depth Tiers`](../../FRAMEWORK.md#audit-depth-tiers) to determine whether a proposal should move to `Audit needed` or undergo its next expressly authorized T-audit. A persistent agent must follow its authoritative [registered runbook](registry.md); a runbook may narrow but may not enlarge these rules.

## Guiding-Principle Check

Apply the Framework's [Guiding Principle](../../FRAMEWORK.md#guiding-principle) to substantive candidate investigation, issue development, remedy design, and audits. Treat grave arbitrary human harm caused or enabled by public authority as the human manifestation and diagnostic symptom of institutional failure—not as a free-floating policy preference and not as a reason to stop at the harm itself. Establish the evidence for arbitrariness, identify the legal, structural, administrative, procedural, or remedial defect that permitted or failed to correct it, and make the causal connection between defect, public power, human harm, and proposed repair explicit.

Do not label an outcome arbitrary merely because it is harmful, unjust, politically disfavored, or contrary to the user's preferred policy. If the record establishes harm but no independently repairable institutional defect, apply the Political-Failure Boundary. If the record establishes arbitrary harm in the Framework's institutional sense, do not dismiss it as ordinary political disagreement; locate the enabling defect and determine whether ARRP can supply a neutral repair.

Test every proposed remedy recursively: determine whether it could itself become personalized, selectively enforced, inadequately constrained, or insulated from meaningful review and correction. Preserve legitimate governmental discretion and prefer the least-complex adequate intervention. This check does not create a separate score, audit tier, or required reader-facing heading and does not authorize an agent to alter a human-approved rubric, proposal foundation, or candidate disposition.

During every substantive issue-development pass and audit, an agent may and must answer the Framework's causal question: **Does this reform materially reduce the probability that lawful governmental authority can be converted into arbitrary injury against individuals?** Record the reasoning in the appropriate development or audit record when it materially affects scope, characterization, remedy design, or outcome; do not mechanically repeat the question on every public issue page.

The Framework's reversed-control question is a human-only judgment. An LLM agent may prepare a neutral analysis of how the existing arrangement and proposed repair would operate under materially different political control, including overcorrection and misuse risks, but it may not answer the question, record it as satisfied, or infer the human's answer. A deterministic bot may verify only whether a record-specific human answer exists; it may not prepare or infer the substantive answer. An agent may apply an already recorded human answer to the affected record. When that answer is material and absent, use `Status: Human decision needed`, state the exact question, and do not take the dependent action.

When subjective intent is unproved or unnecessary to the institutional conclusion, agents may use or adapt the Framework's approved neutral formulation: **“Regardless of intent, this institutional arrangement predictably allows arbitrary human harm, and here is a neutral reform that would reduce that risk under any future administration.”** Do not use that formulation to evade contrary evidence, an applicable intent element, or a required distinction between allegation and established fact.

## User-Framing Neutrality Check

Treat a user's candid political judgment as context or an analytical hypothesis, not automatically as project-ready language or an established factual premise. If an instruction appears to rest on partisan preference, collective blame, unsupported motive attribution, a loaded characterization, or a standard that may operate differently under changed political control, identify the concern before implementing it and prepare neutral alternative-control analysis, a narrower institutional question, a stronger evidentiary requirement, or a political-failure recommendation. Apply only an already recorded human reversed-control answer. Push back when the requested framing would violate the Framework even if the requested substantive outcome is understandable or consistent with the user's stated views.

This check does not require false equivalence. When authoritative evidence establishes material asymmetry, identify the responsible actors, conduct, dates, decisions, and consequences accurately rather than manufacturing equal blame. Distinguish supported descriptions of who sponsored, opposed, blocked, abandoned, implemented, or benefited from an action from claims about collective motive or intent. Attribute motive only when supported by statements, records, findings, or other evidence adequate for that proposition. Apply the same evidentiary, legal, admission, and remedial standards regardless of which party or coalition would benefit from the conclusion.

Do not treat informal language used during discussion as approved reader-facing prose merely because the user used it candidly. Preserve the substance of the concern, explain any neutrality problem, and obtain or reasonably infer approval for the compliant formulation before committing it to the project record.

## Substantive-Position and Partisan-Perception Check

Before finalizing reader-facing prose, distinguish material statements of fact, governing law, disputed interpretation or uncertainty, and ARRP's own institutional analysis or policy position. Do not present a project judgment as though it were a legally or factually compelled conclusion.

When ARRP takes a substantive position, or when a reasonable reader could materially perceive the analysis as aligned with or against a current party, movement, administration, or ideological program, apply the Framework's disclosure rule. State the position candidly, acknowledge its present political alignment or likely partisan perception where material, explain the independent institutional principle supporting it, prepare neutral alternative-control analysis, and apply the recorded human reversed-control answer where material. Do not use the label `nonpartisan` as a substitute for that explanation.

On a standalone reader-facing page, add a concise qualifier when introductory text first presents President Trump as a central case-study subject or first substantively introduces Project 2025. Do not repeat the qualifier for later references on the same page or attach it mechanically to citations, case names, source titles, quotations, chronology, navigation labels, metadata, or technical records. When the fuller explanation already exists on an owning public page, a short statement with a clear link is sufficient.

## Permitted Autonomous Corrections

In batch mode, agents may autonomously fix defects that are mechanical, framework-governed, or directly supported by existing project records, including:

1. broken internal links, including stale repository paths embedded in GitHub issue bodies;
2. missing audit metadata;
3. GitHub Project field and retained source-inventory inconsistencies;
4. missing or stale source-inventory capture;
5. missing Proposal Scoring fields required by the current template;
6. missing audit-history entries;
7. obvious primary-source substitutions for secondary legal references;
8. citation placement and source-note cleanup;
9. budgetary-impact placeholder formatting where no substantive estimate is added; and
10. spelling, heading, metadata, and template conformance fixes.

## Human-Review Stop Conditions

In batch mode, agents must document and stop work on the affected issue before making any of the following changes unless an applicable governing rule permits the action or, for a non-disposition item, the user has expressly pre-authorized that class of change:

1. admitting, rejecting, retiring, retaining only as source development, merging or integrating in a way that ends independent treatment, splitting, removing from active scope, permanently disposing of, or materially reclassifying a candidate or issue;
2. changing the core institutional diagnosis;
3. changing the least-complex adequate remedy;
4. rewriting proposed legislation into a materially different legal vehicle;
5. converting a freestanding bill into amendments to existing law;
6. adding a constitutional amendment or removing one;
7. resolving a substantive discrepancy between an issue page and proposed legislation when the correction would change a reserved foundation, materially contract the approved proposal, or make another human-reserved change;
8. clearing a `change_audit_needed` marker without performing the targeted Change Audit and Internal Remedy-Fit Audit required by the methodology;
9. making unsupported claims about real-world events, motives, legal effect, polling, or public support;
10. increasing a score based on judgment rather than documented audit findings; or
11. marking a proposal as proposal-ready, publication-ready, or externally validated without the required record.

Every terminal or permanent candidate or issue disposition requires a recorded human decision that identifies the specific record and approved disposition. Blanket authority, standing authority, or class-level preauthorization is insufficient. Candidate investigation remains recommendation-only until that decision is recorded. An agent may then implement the recorded record-specific decision as a distinct implementation action, preserving the original identifier, provenance, decision rationale, and disposition history under the Framework's adjudication rules.

When a stop condition appears, record the finding in the issue's audit-history file, update the issue-page audit status, next-audit need, and GitHub Project fields, commit and push if files changed, and move on. Use `Status: Human decision needed` for a specific reserved choice, including a materially missing human reversed-control answer, not `Blocked`; reserve `Blocked` for an unavailable concrete indispensable prerequisite and `Deferred` for an affirmative project decision to postpone work that could proceed.

## ARRP Human-Decision Route

The exact ARRP workflow-status definitions are owned by
[`workflow.md`](../github/workflow.md#issue-development-lifecycle). An agent uses
`Status: Human decision needed` only when a specific human-reserved choice is
the next action. State the exact question, the reason it is reserved, the
agent's reasoned recommendation, material alternatives and consequences, and
important uncertainty. Do not substitute `Blocked` for a missing human choice;
that status is reserved for an unavailable indispensable prerequisite.
`Deferred` requires an affirmative project decision to postpone work that
could proceed.

A human-decision item appears in the owning GitHub record and the Console
Action Items projection. It is not resolved by a clean later scan, a newer
healthy automation run, or silence. Resolution requires the recorded
record-specific human decision and any authorized implementation and readback.

## ARRP Task Handoff

ARRP's durable continuation checkpoint is
[`current-task.md`](../../records/handoffs/current-task.md). Use it for any
audit, drafting pass, source-development task, batch run, or other substantial
work likely to span interruptions, context compaction, or a new task.

Before beginning, record the active issue or task, audit type or tier, user
request, scope, expected files, and first next step. Refresh the checkpoint
after every major phase, before broad edits, before risky or hard-to-reverse
decisions, and before a likely handoff. It records:

1. active issue or task;
2. audit type or tier;
3. user request;
4. scope and files in play;
5. completed steps;
6. exact next step;
7. blockers or open questions;
8. validation status; and
9. one continuation state.

`Open` means unfinished work has an exact continuation point. `Paused` means
the same unfinished work was deliberately suspended and identifies who or what
will resume it and under what condition. `Blocked` means a concrete
indispensable prerequisite prevents continuation and records the blocked
action, prerequisite, and unblock trigger. `Inactive` means no unfinished task
handoff exists. These states describe continuation only. ARRP dispatcher
liveness is governed separately by
[`autonomous-execution.md`](autonomous-execution.md#dispatcher-liveness-authority).

For a vague request such as `continue`, `follow up`, or `resume the audit`,
read the checkpoint before recent commits or GitHub Project rows. Do not infer
the active task from the newest commit, nearby markers, unrelated uncommitted
changes, or a checkpoint that is inactive, stale, missing, or inconsistent
with the latest user instruction.

Successful closeout requires `Inactive` and the inactive sentinels defined in
the checkpoint. The cleared checkpoint must be included in the final committed
and synchronized change. If a required commit, push, review or merge,
synchronization, publication, validation, or human-reserved decision remains
part of the same task, retain `Paused` or `Blocked` with the exact continuation
point. Reopen the checkpoint if a required external step fails after intended
closeout. A separate future human-review question belongs in Action Items and
the owning workflow status; it does not keep otherwise completed work open.

## ARRP Provenance and Log Ownership

All persistent ARRP agents and bots use
[`agent-audit-log.md`](../../records/automation/agent-audit-log.md) for material
operational provenance and rollback planning. Every material autonomous unit
records its action under a stable Agent ID, Run ID, and Unit ID where
applicable, using the fields required by the reusable
[`provenance-and-recovery.md`](../../standards/automation/provenance-and-recovery.md)
standard and the canonical prospective template maintained in the log.
Ordinary human-invoked work does not append there unless the user expressly
converts it into an autonomous, batched, or scheduled run.

A clean no-change run remains in bounded GitHub Actions or Console history and
does not append a material-work entry. A material finding, repository change,
or external-state change must be logged. A source-changing pull request appends
its source IDs, action and reason, accountable destination and proposition,
originating run, validation, commit and push status, and rollback reference in
that same change. The log is append-only; a revert adds a new entry identifying
the original and reversing commits rather than erasing history. Preserve
historical generic labels and schemas, and do not retroactively attribute an
older run to a newly named agent without reliable evidence.

A persistent scheduled LLM agent may also have the dedicated `run_log_path`
registered by its authoritative runbook. That run log accounts for every
invocation, but it does not replace the shared Agent Audit Log, issue
audit-history sidecars, domain event records, source catalogs, GitHub Project
state, handoff checkpoint, or final report. Sensitive intake remains governed
by its narrower privacy rules.

ARRP branch protection, checked publication, and exact readback are governed by
[`workflow.md`](../github/workflow.md) and the applicable registered runbook;
this policy does not duplicate or enlarge those authorities.
