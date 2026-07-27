---
title: "ARRP Maturity Profile"
status: active
authority_scope: "ARRP-specific maturity values, classifiers, thresholds, and foundation-sufficiency authority."
load_when: "Classifying or changing an ARRP proposal's Development level or foundation status."
dependencies:
  - "../../standards/content/maturity-and-gates.md"
  - "../github/workflow.md"
print_status: excluded
print_exclusion_reason: "Internal project configuration."
---

# ARRP Maturity Profile

This file configures the reusable
[Content Maturity and Development Gates](../../standards/content/maturity-and-gates.md)
for ARRP. It is the authoritative home for ARRP's exact maturity values,
foundation-classification authority, thresholds, and mappings to GitHub
workflow fields. When candidate admission or disposition is implicated, also
load the
[candidate-review workflow](../workflows/candidate-review.md). When an agent
would implement substantive issue or candidate work, also load the
[ARRP agent policy](../automation/agent-policy.md).
When classifying `Review ready` or `Release candidate`, also load the
[ARRP scoring rubric](scoring-rubric.md); earlier maturity classifications do
not require the full scoring authority.

## Issue Lifecycle: Discovery Through Publication and Maintenance

The sections below define ARRP's exact maturity path from formal candidacy
through the human publication decision, together with the repeatable work that
may occur around it.

## Maturity and workflow separation

ARRP separates **Development level** from **Status**. `Development level`
records substantive maturity and supplies the six-column lifecycle projected
by the Project Console. It ordinarily advances as maturity is earned and does
not move backward merely because further research, revision, audit, external
review, or maintenance is underway. Correct an unsupported level when the
underlying record does not actually satisfy its gate.

GitHub `Status` records the current workflow action or hold. Audit controls and
monitoring are separate. They may change many times without creating a new
development level, and none substitutes for another.

## Development-Level Lifecycle

ARRP uses six values:

1. **Candidate.** An approved preliminary becomes a formal `HOR-###`
   candidate and GitHub issue. Its Development level remains `Candidate` until
   the human author records admission or another permanent disposition.
   Candidate adjudication verifies the premise and existing coverage, applies
   the canonical
   [Issue-Admission Test](../../standards/content/scope-and-admission.md#issue-admission-test),
   prepares any material reversed-control analysis, and recommends admission,
   integration, deferral, source retention, retirement, or rejection.
2. **Admitted / undeveloped.** Independent human admission converts the
   existing Horizon issue into a stable area-specific issue while preserving
   its Horizon provenance. Its Development level remains
   `Admitted / undeveloped` until the four-part foundation below is
   established. The admitted issue receives the canonical records required by
   the
   [Horizon Candidate Adjudication Workflow](../workflows/candidate-review.md#horizon-candidate-adjudication-workflow).
3. **In development.** The issue reaches `In development` once all four
   foundation criteria have been established and recorded. This level
   authorizes broad development within the approved foundation; it is not
   proof that a person or agent is presently working and does not imply that
   the issue page, vehicle, evidence, or implementation analysis is complete.
4. **Developed proposal.** Apply the package-completeness gate below. This
   level makes the proposal eligible for formula scoring but does not itself
   assign a score or make a T-audit the next workflow.
5. **Review ready.** Apply the internal-reviewability gate below. Review
   ready means the proposal is sufficiently mature for knowledgeable external
   critique, not permanently complete and not immune from later research,
   revision, or Change Audit.
6. **Release candidate.** Apply the single Release-candidate gate below.
   This level means the proposal is ready for the human publication decision;
   it does not authorize circulation or publication.

## Intake Before the Development-Level Lifecycle

- **Discovery.** A public submission, source review, Horizon Scan, directive
  review, litigation development, or other project work identifies a possible
  institutional weakness. Evidence belonging to existing work is routed
  there; otherwise-unowned evidence may be synthesized into a preliminary
  candidate.
- **Preliminary candidate.** The internal preliminary queue presents a concise
  potential weakness for human review. It has no `HOR-###` identifier and no
  Project Development level. Human review may decline it, combine it with
  another preliminary, route it to existing work, defer it, or approve
  promotion to `Candidate`.

## Human-Governed Foundation and Delegated Development

An admitted issue enters `In development`, and substantive delegated
development begins, after four foundations have been established:

1. **Institutional defect:** the independently repairable weakness, its
   essential boundaries, and its causal relationship to grave arbitrary harm
   or a material risk of it;
2. **Manifestation or risk pathway:** at least one evidence-backed event,
   observable condition, near miss, or concrete mechanism showing how public
   authority operates through the defect and produces—or could predictably
   produce—the relevant injury;
3. **Remedy:** the selected neutral institutional correction or safeguard and
   the reason it should reduce the harm or risk without becoming a new
   arbitrary instrument of power; and
4. **Remedy vehicle:** the selected legal or institutional form, defined
   sufficiently to guide development but not necessarily already drafted.

The human author ordinarily establishes the four-part foundation. During an
authorized recurring run, Elim may record that the existing canonical issue
already states all four criteria. An interactive Codex agent working directly
with the user may make the same evidentiary classification during ordinary
project work. Neither may invent, choose, or materially revise a missing
foundation.

For an unscored proposal, record:

- `foundation_status: approved` or `foundation_status: pending`;
- `foundation_approved_date: YYYY-MM-DD` when approved; and
- a concise `foundation_approval_note` identifying the human decision or
  authorized sufficiency determination and where all four criteria appear.

Absence of the field is not permission for another scheduled agent to infer
approval. A proposal already scored through a completed T-audit is treated as a
legacy-established foundation unless its current record identifies a
foundational question; add the metadata when it is next materially revised.

Candidate investigation remains upstream of this threshold. It may verify a
premise, build a source dossier, apply the admission test, analyze legal
adequacy and overlap, identify possible remedy classes, and prepare a neutral
recommendation. It may not answer a reserved human question, admit the
candidate, establish its foundation, create a formal remedy vehicle, score it,
or implement a permanent disposition.

Once all four foundations exist, authorized development may improve, expand,
organize, research, draft, test, and correct the issue and proposal within the
approved diagnosis, remedy, vehicle, scope, and essential boundaries. Human
approval remains required to:

- admit, reject, merge, split, retire, remove, or materially rescope an issue;
- define or materially change the institutional failure;
- replace the approved remedy or remedy vehicle;
- materially shift a foundational legal, factual, or analytical conclusion;
- materially contract or expand approved coverage;
- make a major change to institutional architecture, staffing, funding
  duration, appropriations, or fiscal responsibility;
- remove important evidence in a way that changes the demonstrated pattern or
  strength of the proposal;
- answer or revise a reserved reversed-control question;
- authorize final circulation or publication; or
- change governing scope, methodology, audit, or scoring rules.

These reservations limit decision and implementation authority; they do not
remove the subject from the agent's duty of review. An agent must still examine
a relevant reserved matter, identify options and consequences, state its
reasoned recommendation and any important uncertainty, formulate the exact
human decision, preserve nonconflicting work, and continue while withholding
only the reserved decision and actions that depend upon it.

## Post-Admission Development Gates

Admission establishes only that an issue belongs in ARRP as an independent
record. Later maturity follows separate gates:

1. **Foundation established — In development.** Apply the four-part foundation
   above.
2. **Package complete — Developed proposal.** The issue-and-vehicle package
   performs the mandatory content architecture, makes the governing causal
   chain visible, and contains enough substance for proposal-quality review.
3. **Audit ready — Audit needed.** A selected audit can produce meaningful
   evaluative findings rather than merely repeat that the foundation or
   package is missing.
4. **Internally reviewable — Review ready.** The current Proposal Quality Score
   is at least 75. This level does not establish finality, external validation,
   or publication readiness.
5. **Ready for the human publication decision — Release candidate.** Apply the
   exact Release-candidate threshold below. Classification does not authorize
   publication.

## ARRP Thresholds

- `Developed proposal` establishes eligibility for formula scoring but does not
  assign a score.
- `Review ready` requires a current score of at least 75 under the
  [ARRP scoring rubric](scoring-rubric.md).
- `Release candidate` requires a current score of at least 75, a current
  cumulative T4 with no later unresolved material change, no unresolved
  publication blocker, and current alignment among governing law and sources,
  the issue page, proposal vehicle, audit record, Project metadata, and
  intended publication surfaces.
- The preferred standard is a total score of at least 79 that includes
  `External Review Score: 4 / 4`; a score of 79 or higher without those four
  points does not satisfy the preferred standard. Whenever the preferred
  standard is not met, the human author must record acceptance of the
  departure before assigning `Release candidate`.

Release-candidate classification does not authorize circulation or
publication.

## Repeatable Workflows Around the Lifecycle

- **Candidate research and adjudication.** Evidence gathering, source
  development, empirical investigation, or candidate testing may occur while
  Development level remains `Candidate`. When the record is ready, the next
  action is the human-reserved admission or disposition decision.
- **Development and revision.** Within an approved foundation, agents may
  research, draft, expand, reorganize, test, and improve the issue page,
  proposal vehicle, supporting evidence, implementation design, budget
  treatment, and connected records.
- **Audit.** T0 through T4 audits progressively test triage, framework
  compliance, substantive development, external-circulation readiness, and
  publication readiness. They are repeatable reviews, not Development levels.
  Only completed and separately recorded T-audits increment `Runs`.
- **External review and publication preparation.** Qualified review and
  resulting legal, drafting, fiscal, implementation, adoption, or stakeholder
  work may return Status to research, development, audit, or human decision
  without automatically reducing the established Development level.
- **Maintenance and monitoring.** Published, Release-candidate, or Review-ready
  work remains subject to new evidence, legal developments, implementation
  experience, material revision, and independent monitoring. A material
  revision triggers the ordinary Change Audit rules without automatically
  erasing the prior score or Development level; monitoring remains independent
  of both.

The exact Status vocabulary and hold requirements are defined in the
[ARRP GitHub workflow](../github/workflow.md). Merged, integrated, rejected,
retired, or otherwise finally adjudicated records follow the disposition and
preservation rules applicable to their stage. When no active obligation
remains, close the GitHub issue and remove its card from the active Project
while preserving the canonical disposition record; do not retain a terminal
completion Status. A deferred or blocked record remains active only while its
documented hold remains meaningful. A monitored record retains its ordinary
Status and Development level.

## Recurring triage vocabulary

Automated triage may classify a proposal as:

- `Ready for T-audit`
- `Development needed first`
- `Change Audit needed first`
- `Deferred by project decision`
- `Blocked by an indispensable prerequisite`
- `Human decision required`

Monitoring remains separate. When tier selection is authorized, choose the
lowest useful next tier.

## Required Lifecycle Check

Before substantive issue work, read the canonical issue, concrete vehicle if
any, latest audit entry, next step, and authoritative GitHub Project record.
Do not change Status merely because a session starts or stops, and do not
reduce Development level merely because further research or revision begins.

At closeout, classify the actual Development level, next Status or hold, and
monitoring state separately. Research, drafting, source development, lifecycle
checks, Change Audits, and other non-tiered review do not independently assign
a formula score or increment `Runs`.
