---
title: "Change Audits"
status: active
dependencies:
  - "core.md"
  - "project-consistency.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Change Audits

## Authority, Loading, and Dependencies

**Authority.** This module governs reusable project-wide and
proposal-specific Change Audits, rebaseline classification, targeted Internal
Remedy-Fit Audits, rubric-version changes, and propagation of changed governing
or substantive records.

**Load when.** Load it whenever a governing rule, audit or scoring rubric,
template, schema, substantive developed proposal, or proposal vehicle changes;
whenever a change-audit marker is set or considered for clearing; or whenever a
prior score or synchronized surface may have become stale.

**Dependencies.** Load the [Framework kernel](../../FRAMEWORK.md),
[Audit Core](core.md), [Project Consistency Audits](project-consistency.md),
and [Scoring Standard](scoring.md). Load the project's scoring profile and
hosted-platform workflow when scores or hosted state may change. Load the
[Remedy Standard](../content/remedies.md) and other specialized authorities
when their subject is affected.

## Change Audit

A Change Audit is the consistency check run when an audit framework, scoring
rubric, content template, hosted-workflow field schema, inventory schema, audit
sidecar structure, other governing rule, or substantive developed proposal
changes. Begin with project-level consistency when the change affects
cross-project rules or conventions. A change limited to one proposal's page,
vehicle, source basis, remedy, implementation, or scoring-relevant analysis
may use a targeted proposal-specific audit.

The purpose is to prevent newer rules or substantive revisions from leaving
older scores, metadata, hosted workflow fields, audit histories, visible
summaries, or proposal-to-vehicle alignment silently stale.

Record a proposal-specific Change Audit in that proposal's audit-history
record. A project-wide Change Audit incorporates each durable finding in the
governing file, script, or test that owns it; the committed change preserves
transaction history. Do not create or append a cumulative project-wide Change
Audit ledger merely for a new live review. Preserve existing historical
records read-only for provenance.

The public-safe Governance Change Log may separately record the provenance of
a material governance decision, its exact Git evidence, supersession,
validation, and activation posture. It is not a Change Audit, does not create
an audit run, and may not alter a score, rubric, rebaseline marker, or the
historical Change Audit Log. Use its project workflow only after the governing
authority and any required Change Audit have been determined.

Related substantive edits or clarifications made in rapid succession may be
consolidated into one coherent proposal-sidecar entry or one bounded governing
change only when the canonical record and committed change still preserve the
material changes, affected scope, score or rebaseline effect, unresolved
findings, and reason for consolidation.

When a developed content record or linked proposal vehicle receives a
substantive update that could affect legal fit, prior-work grounding, remedy
design, implementation, abuse resistance, drafting quality, adoption posture,
source support, budgetary impact, or alignment, remind the user to consider a
Change Audit before treating the score as current. Do not run it automatically
unless requested or included in an expressly authorized recurring sequence.
Formatting-only edits, typo fixes, and link repairs do not require the reminder
unless they reveal a score-affecting defect.

If substantive content changes without a contemporaneous Change Audit, mark the
developed record for a targeted Change Audit even when the score does not
change. Record the reason, make the unresolved review visible, synchronize any
configured hosted marker, and add a no-score audit-history entry. A
candidate-only or source-development-only record may use ordinary development
notes unless it already carries a developed proposal and score.

## Internal Remedy-Fit Audit

A targeted Change Audit includes an Internal Remedy-Fit Audit. Confirm that the
record's anomaly, manifestations, resulting damage, underlying weakness,
proposal survey, least-complex adequate remedy, repair and prevention,
proposal vehicle, and annotation still describe the same institutional defect
and that the remedy still answers the defect as reframed.

When a new manifestation or source expands, narrows, or changes the theory,
record whether the remedy still fits, the issue should be narrowed, the
manifestation belongs elsewhere, the vehicle should change, or human review is
required before further score reliance.

## Rebaseline Method

Every score must identify the rubric version that produced it. When the audit
or scoring system changes, classify the change before applying it:

| Change type | Rebaseline treatment |
| --- | --- |
| Wording clarification, formatting, or examples only | No rebaseline. |
| New metadata, hosted field, or non-score category | Soft rebaseline unless it exposes a score-affecting defect. |
| New required check, source rule, penalty, scoring component, weight, baseline rule, or current-status gate | Hard rebaseline for already scored developed proposals unless already audited under the new rule. |
| Change to a fixed baseline category | Rebaseline the affected category. |

Preserve old scores, but treat non-current scores as provisional in summaries,
comparisons, and prioritization. Do not compare scores from different rubric
versions without disclosing the mismatch. Do not rerun every proposal
immediately unless requested; use the project's configured rebaseline status
to queue work responsibly.

## Workflow

1. Assign a new rubric version before changing a scoring rule or required
   audit filter.
2. Record the governing change in the authority that owns it. Record a
   proposal-specific audit in the affected sidecar and synchronize the
   proposal page and hosted fields where applicable.
3. Before applying a cross-project change downstream, review every implicated
   governing authority, template, schema, inventory, content record, vehicle,
   audit convention, and hosted workflow for duplicated rules, stale
   terminology, broken links, metadata drift, source-rule drift, tracking
   drift, language-rule drift, and content-to-vehicle misalignment.
4. Correct a mechanical governing defect in its authoritative home. Preserve
   and report a substantive discrepancy that requires human judgment before
   changing dependent records.
5. Mark every affected already-audited proposal with the appropriate configured
   rebaseline status and explain the effect in plain language.
6. During the next targeted Change Audit or sufficiently deep issue-quality
   audit, resolve the change marker through the Internal Remedy-Fit Audit and
   every other affected check. Clear it only after the issue, audit history,
   score, rebaseline state, and hosted fields are synchronized.
7. If the score changes, recalculate it under the current rubric and explain
   which component, penalty, or baseline changed.

Formatting-only or template-only changes may require a Change Audit without
requiring score rebaseline. Synchronize affected pages, metadata, sidecars,
hosted fields, and source records, but do not change scores unless the review
finds a substantive scoring defect.
