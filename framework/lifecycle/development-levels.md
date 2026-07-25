---
title: "Development Levels and Lifecycle"
status: active
authority_scope: "The six substantive maturity levels, intake states before them, and the high-level relationship between maturity and repeatable workflows."
load_when: "Classifying proposal maturity; promoting a preliminary candidate; admitting or disposing of a formal candidate; or determining whether work has reached In development, Developed proposal, Review ready, or Release candidate."
dependencies: "../FRAMEWORK.md; ../methodology/scope-and-admission.md; ../GITHUB_WORKFLOW.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Development Levels and Lifecycle

## Authority and Dependencies

This file is the authoritative detailed definition of ARRP's substantive maturity lifecycle. The governing principles and human-reserved decisions in [`../FRAMEWORK.md`](../FRAMEWORK.md) control. Apply the substantive gates in [`foundation-and-development-gates.md`](foundation-and-development-gates.md) and the admission rule in [`../methodology/scope-and-admission.md`](../methodology/scope-and-admission.md). GitHub Project field values, workflow Status definitions, synchronization, and transition mechanics are owned by [`../GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md), not by this file.

## Load When

Load this file when classifying proposal maturity; promoting a preliminary candidate; implementing a human decision on a formal candidate; determining whether an admitted issue has entered development; or evaluating whether a package is Developed, Review ready, or a Release candidate.

## Issue Lifecycle: Discovery Through Publication and Maintenance

ARRP separates **development level** from **workflow status**. Development level records the proposal's substantive maturity and is the six-column lifecycle shown on the Project Console. It ordinarily advances as maturity is earned and does not move backward merely because further research, revision, audit, external review, or maintenance is underway. Correct an unsupported level when the underlying record does not actually satisfy its gate. Workflow status, audit controls, and monitoring separately identify repeatable work, holds, and observation; they may change many times without creating a new development stage.

## Development-Level Lifecycle

1. **Candidate.** An approved preliminary becomes a formal `HOR-###` candidate and GitHub issue. Its substantive maturity remains `Candidate` until the human author records admission or another permanent disposition. Candidate adjudication verifies the premise and existing coverage, applies the canonical [Issue-Admission Test](../methodology/scope-and-admission.md#issue-admission-test), prepares any material reversed-control analysis, and recommends admission, integration, deferral, source retention, retirement, or rejection.
2. **Admitted / undeveloped.** Independent human admission converts the existing Horizon issue into a stable area-specific issue while preserving its Horizon provenance. Its maturity remains `Admitted / undeveloped` until the four-part foundation in [`foundation-and-development-gates.md`](foundation-and-development-gates.md) is established. The admitted issue receives the canonical records required by the [Horizon Candidate Adjudication Workflow](../candidates/candidate-adjudication.md#horizon-candidate-adjudication-workflow).
3. **In development.** The admitted issue reaches `In development` once the four criteria in [Human-Governed Foundation and Delegated Development](foundation-and-development-gates.md#human-governed-foundation-and-delegated-development) have been established and recorded. This maturity level authorizes broad development within the approved foundation; it is not proof that a person or agent is presently working and does not imply that the issue page, vehicle, evidence, or implementation analysis is complete.
4. **Developed proposal.** Apply the package-completeness gate in [Post-Admission Development Gates](foundation-and-development-gates.md#post-admission-development-gates). This level makes the proposal eligible for formula scoring but does not itself assign a score or make a T-audit the next workflow.
5. **Review ready.** Apply the internal-reviewability gate in [Post-Admission Development Gates](foundation-and-development-gates.md#post-admission-development-gates). Review Ready means the proposal is sufficiently mature for knowledgeable external critique, not permanently complete and not immune from later research, revision, or Change Audit.
6. **Release candidate.** Apply the single release-candidate gate in [Post-Admission Development Gates](foundation-and-development-gates.md#post-admission-development-gates). This level means the proposal is ready for the human publication decision; it does not authorize circulation or publication.

## Intake Before the Development-Level Lifecycle

- **Discovery.** A public submission, source review, Horizon Scan, directive review, litigation development, or other project work identifies a possible institutional weakness. Evidence belonging to existing work is routed there; otherwise-unowned evidence may be synthesized into a preliminary candidate.
- **Preliminary candidate.** The internal preliminary queue presents a concise potential weakness for human review. It has no `HOR-###` identifier and no Project development level. Human review may decline it, combine it with another preliminary, route it to existing work, defer it, or approve promotion to `Candidate`.

## Repeatable Workflows Around the Lifecycle

- **Candidate research and adjudication.** Evidence gathering, source development, empirical investigation, or candidate testing may occur while maturity remains `Candidate`. When the record is ready, the next action is the human-reserved admission or disposition decision.
- **Development and revision.** Within an approved foundation, agents may research, draft, expand, reorganize, test, and improve the issue page, proposal vehicle, supporting evidence, implementation design, budget treatment, and connected records.
- **Audit.** T0 through T4 audits progressively test triage, framework compliance, substantive development, external-circulation readiness, and publication readiness. They are repeatable reviews, not development levels. Only completed and separately recorded T-audits increment `Runs`.
- **External review and publication preparation.** Qualified review and resulting legal, drafting, fiscal, implementation, adoption, or stakeholder work may return the workflow to research, development, audit, or human decision without automatically reducing the established development level.
- **Maintenance and monitoring.** Published, release-candidate, or review-ready work remains subject to new evidence, legal developments, implementation experience, material revision, and independent monitoring. A material revision triggers the ordinary Change Audit rules without automatically erasing the prior score or development level; monitoring remains independent of both.

The exact workflow Status vocabulary and hold requirements are defined in [`../GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md).

Merged, integrated, rejected, retired, or otherwise finally adjudicated records follow the disposition and preservation rules applicable to their stage. When no active obligation remains, close the GitHub issue and remove its card from the active Project while preserving the canonical disposition record; do not retain a terminal completion Status. A deferred or blocked record remains active only while its documented hold remains meaningful. A monitored record retains its ordinary workflow status and development level.
