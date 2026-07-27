---
title: "Audit Execution Standard"
dependencies:
  - "../../AGENT_OPERATING_RULES.md"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Audit Execution Standard

Load this module before beginning, selecting, advancing, batching, or resuming
a tiered or other issue-quality audit unit. Load the substantive audit,
monitoring, source, candidate, and project-implementation modules implicated by
the operation in addition to this reusable execution standard.

## Single-Issue Default

Issue-quality audits are single-record workflows by default. An agent should
not audit multiple records in one pass unless the user expressly requests batch
mode or a project-wide Change Audit.

Before beginning an audit, identify:

1. the stable record identifier;
2. the requested tier or the next tier shown by the project's authoritative
   lifecycle surfaces;
3. the canonical issue or content record;
4. every linked proposal vehicle;
5. the preserved audit-history record;
6. the authoritative hosted work item, when the project uses one;
7. all retained-source catalog rows and source-development records owned by or
   cross-referenced to the issue;
8. any genuinely unresolved source record that identifies the issue as a
   plausible destination;
9. unresolved findings from the latest audit; and
10. every project-configured monitoring designation, watched matter,
    reassessment trigger, checking method, source-level monitoring value,
    accepted baseline, and deterministic watcher relevant to the issue.

Apply the tier-scaled source-reconciliation rule in the substantive audit
method. Early tiers may inventory applicable work; development and deeper
tiers should resolve applicable tasks through verification, route and
remedy-fit review, qualitative reader-facing placement, a documented
no-additional-value disposition, or a precise continuing predicate. Reconcile
and read back every authoritative surface required by the project's
implementation. This reconciliation does not create a separate audit run.

Project-wide monitoring and specialized discovery review are distinct
non-scoring workflows. Their project configuration must identify the
authoritative starting surface, inputs, outputs, review boundary, and
readback. Deterministic results are routing aids unless an applicable rule
expressly gives them greater authority.

A deterministic monitoring bot may place high-recall leads only in a
configured marker-bounded destination authorized by its runbook. Each lead
must be labeled unreviewed and preserve stable identity and provenance. It is
not a source-catalog admission, verified manifestation, legal conclusion,
issue disposition, or substitute for authorized agent and human review.

Before substantive scoring work, apply the concrete-vehicle preflight in
[`../audits/levels.md`](../audits/levels.md#audit-depth-tiers). Honor its notice
and confirmation boundary. Do not assign formula-based quality credit until
the required concrete draft exists.

If the record identifier is unclear, ask the user before running the audit.

## Tier Progression

For each record:

1. read the latest canonical page, linked vehicles, audit history,
   authoritative work item, and relevant source records;
2. determine the next required audit tier;
3. follow the tier-progression strategy authorized by the applicable runbook
   or the user's instruction while completing and memorializing every tier
   separately;
4. stop tier progression for that record if a material unresolved finding
   requires human review;
5. update every affected canonical content, audit-history, hosted-workflow, and
   source record;
6. validate the changed files;
7. preserve and synchronize the completed unit through the project's reviewed
   publication boundary;
8. refresh and read back every configured generated completion surface when
   its authoritative inputs changed; and
9. move to the next eligible record.

Complete the selected tier for one record before proceeding. If a record
reaches a genuine evidentiary, access, external-review, or human-review
blocker, document and preserve it before proceeding.

When substantive work changes a developed record without the required targeted
Change Audit, set every project-configured change-audit marker before treating
the prior score or review posture as current. Reader-facing wording should
follow the project's terminology convention while technical records preserve
the exact audit terms.

## Audit Completion and Batch Boundaries

Audit tiers are defined by required depth and output, not by elapsed-time ceilings, token allowances, account-usage limits, or subscription-driven resource budgets. Complete the selected tier before moving to the next issue unless a genuine evidentiary, access, external-review, human-review, or user-defined boundary prevents completion.

For a batch window expressly defined by the user, do not begin a new audit unit
that cannot reasonably be completed, validated, preserved, synchronized, and
logged inside the remaining user-defined window. If a unit is already near
completion when that window ends, preserve the work and follow the user's
stated stopping instruction; absent an express window, no default time boundary
applies.

When deciding whether to continue research, ask:

1. Will this likely change the score, remedy, source reliability, or next-audit need?
2. Is there a primary source likely to answer the question reliably?
3. Has the issue already hit a human-review stop condition?
4. Has further research become duplicative, or has the question reached a genuine blocker that should be documented?

If the answer favors stopping, stop.
