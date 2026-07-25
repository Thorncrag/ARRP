---
title: "ARRP Change Audits"
status: active
dependencies: "AUDIT_CORE.md; PROJECT_CONSISTENCY_AUDITS.md; ../scoring/PROPOSAL_QUALITY_AND_RUBRIC.md; ../GITHUB_WORKFLOW.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Change Audits

## Authority, Loading, and Dependencies

**Authority.** This module is authoritative for project-wide and proposal-specific Change Audits, rebaseline classification, targeted Internal Remedy-Fit Audits, rubric-version changes, and propagation of changed governing or substantive records.

**Load when.** Load this module whenever a governing rule, audit or scoring rubric, template, schema, substantive developed proposal, or proposal vehicle changes; whenever `change_audit_needed` is set or considered for clearing; and whenever a prior score or synchronized project surface may have become stale because of a change.

**Dependencies.** Load the [Framework kernel](../FRAMEWORK.md), [Audit Core](AUDIT_CORE.md), [Project Consistency Audits](PROJECT_CONSISTENCY_AUDITS.md), [Proposal Quality and Rubric Governance](../scoring/PROPOSAL_QUALITY_AND_RUBRIC.md), and [GitHub Workflow](../GITHUB_WORKFLOW.md). Load the [Remedy Framework](../REMEDY_FRAMEWORK.md) and other specialized authorities when the change affects their subject.

## Change Audit

A **Change Audit** is the consistency check run when the audit framework, scoring rubric, issue-page template, GitHub Project field schema, inventory schema, audit sidecar structure, other governing project rule, or a substantive developed proposal changes. It must begin with project-level consistency when the change affects governing rules or cross-project conventions, and may be targeted to a single proposal when the change is limited to that proposal's issue page, linked proposal vehicle, source basis, remedy design, implementation design, or scoring-relevant analysis. Its purpose is to prevent newer rules or substantive proposal revisions from leaving older scores, metadata, GitHub Project fields, audit histories, issue-page summaries, or proposal-to-legislation alignment silently stale.

Proposal-specific Change Audits are recorded in the affected proposal's sibling audit-history file. A project-wide Change Audit incorporates each durable finding in the governing file, script, or test that owns it; the related committed change preserves transaction history. Do not create or append a cumulative project-wide Change Audit ledger or a stand-alone consistency-audit report. Existing historical records are retained read-only for provenance.

When several related substantive edits or Change Audit clarifications occur in rapid succession, they may be consolidated into one coherent proposal-sidecar entry or one clearly bounded governing-file change. Consolidation is acceptable only if the canonical record and committed change still preserve the material changes made, the affected files or proposal, the score or rebaseline effect, unresolved findings, and the reason the edits are treated as one change set.

**Admission and post-admission consolidation — 2026-07-24.** The human author approved consolidation of the Issue-Admission Test, post-admission foundation, and development gates around the Guiding Principle; reserved terminal candidate and issue dispositions and the reversed-control acceptability decision to the human author; and defined the Release-candidate gate. This change preserves the existing Political-Failure Boundary, Proposal Quality Score formula, component weights, penalties, score bands, T-audit depths, and Runs rule. It requires no proposal-score rebaseline. Any proposal already classified `Release candidate` must be checked against the new gate; no other development level or score changes solely because of this clarification.

When a developed issue page, proposed legislation page, rule text, constitutional amendment text, or other proposal vehicle receives a substantive update that could affect legal fit, prior-proposal grounding, remedy design, implementation design, abuse resistance, drafting quality, adoption posture, source support, budgetary impact, or proposal-to-legislation alignment, the assistant should remind the user to consider a Change Audit before treating the proposal score as current. Do not run the Change Audit automatically unless the user asks or has expressly authorized a recurring run whose stated order includes flagged Change Audits; that recurring authorization is advance authorization to resolve eligible Change Audits within the human-approved foundation. Formatting-only edits, typo fixes, link repairs, and other non-substantive maintenance do not require this reminder unless they reveal a score-affecting defect.

If a developed issue receives a new source, manifestation, institutional-anomaly framing, damage theory, underlying-weakness theory, remedy description, repair/prevention language, or proposal-vehicle change without a contemporaneous Change Audit, mark the issue as needing a targeted Change Audit. This marker is required even when the score does not change. At minimum, update the issue front matter with `change_audit_needed: true`, add a concise `change_audit_reason`, update the visible **Proposal Scoring** summary or **Next Review** line, update the GitHub Project item if a relevant field exists, and append a no-score entry to the sibling audit-history file explaining the update and the unresolved consistency check. Candidate or source-development-only issues may use ordinary source-development notes instead of this marker unless they already have a developed proposal and score.

The targeted Change Audit should include an **Internal Remedy-Fit Audit**. It must confirm that the issue's Institutional Anomaly, Manifestations of the Failure, Resulting Damage, Underlying Weakness, Proposal Survey, Least-Complex Adequate Remedy, Repair and Prevention, proposed legislation or other proposal vehicle, and Annotation still describe the same institutional defect and that the proposed remedy still addresses the defect as reframed. If a new manifestation or source expands, narrows, or changes the issue's theory, the audit should document whether the remedy still fits, whether the issue should be narrowed, whether the manifestation belongs in another issue, whether the proposed legislation should be revised, or whether human review is required before further score reliance.

The current audit rubric version is **2026-06-27.2**.

Rubric version log:

| Version | Change | Rebaseline effect |
| --- | --- | --- |
| `2026-06-26.1` | First explicit rubric-version and rebaseline-tracking system. | Marked prior developed scores for rebaseline and fixed-status zero scores as current fixed-status values. |
| `2026-06-26.2` | Added Adoption Friction Score as a companion metric outside the 100-point Proposal Quality Score. | Soft rebaseline for otherwise-current developed proposals; hard rebaseline remains for developed proposals already awaiting formula rebaseline. |
| `2026-06-27.1` | Added required T1 Enactment Pathway Check, including Required Electoral Environment, Pathway Viability, Development Priority, and Pathway Adjustment. The check is evidence-bound and feeds Adoption and Implementation scoring rather than creating a standalone score. | Hard rebaseline for developed proposals because the new required check can materially change Adoption and Implementation component credit. Fixed-status zero scores remain current fixed-status values. |
| `2026-06-27.2` | Clarified that legal availability is not adoption viability where a proposal depends on voluntary self-limitation by the same institutional actor whose discretion the proposal constrains. Added `conditional-current` Pathway Viability value and required Adoption Score and Adoption Friction treatment for institutionally adverse adopters. | Hard rebaseline for developed proposals whose pathway depends on discretionary adoption by an institution or officer materially adverse to the reform, especially current-law or internal-policy vehicles. No rebaseline is required for proposals whose adoption path does not depend on that condition. |

Every proposal-quality score must be tied to the audit rubric version used to produce it. This prevents older scores from appearing directly comparable to newer scores after the project changes scoring weights, required filters, current-status checks, source rules, or audit-output requirements.

Use these fields in issue-page front matter for developed issues when the page is next audited or materially revised:

```yaml
audit_rubric_version: 2026-06-27.2
audit_rebaseline_status: current
change_audit_needed: false
change_audit_reason: null
adoption_friction_score: null
adoption_friction_band: unassessed
required_electoral_environment: unassessed
pathway_viability: unassessed
development_priority: unassessed
pathway_adjustment: unassessed
```

Use these exact fields in issue front matter and technical audit records when applicable:

- `Audit Rubric Version`
- `Rebaseline Status`
- `Rebaseline Notes`
- `Adoption Friction Score`
- `Adoption Friction Band`
- `Adoption Friction Notes`
- `Required Electoral Environment`
- `Pathway Viability`
- `Development Priority`
- `Pathway Adjustment`
- `Enactment Pathway Notes`

The visible **Proposal Scoring** summary should translate technical audit fields into reader-facing labels and values. Use **Internal Review Status**, **Last Internal Review**, **Scoring Standard**, **Scoring Basis**, **Revision Review** or **Revision Review Needed**, **Next Review**, and **Full Review History** as applicable. Do not expose codes such as `current-fixed-status`, `soft-rebaseline-needed`, or `hard-rebaseline-needed` as unexplained visible prose; express their meaning directly while preserving the exact value in front matter, the audit sidecar, and GitHub Project fields.

Rebaseline statuses:

| Status | Meaning |
| --- | --- |
| `current` | The score was calculated under the current rubric version and may be compared to other current scores. |
| `current-fixed-status` | The issue has a fixed non-formula status, usually candidate, paused, retired, merged, pending controlling finding, or reliably moot; the zero score is current until the status changes. |
| `soft-rebaseline-needed` | The rubric changed in a way that adds useful context or a new non-score field, but the existing score remains usable with a caveat until the next audit. |
| `hard-rebaseline-needed` | The rubric changed in a way that could materially change the score; treat the existing score as provisional until the next substantive audit recalculates it. |
| `rebaseline-complete` | A rebaseline audit was completed; this status should normally be converted to `current` after the GitHub Project fields and issue metadata are updated. |

Map issue-page rebaseline metadata to the GitHub Project `Rebaseline status` field as follows:

| Issue-page value | GitHub Project value |
| --- | --- |
| `current` | `Current` |
| `current-fixed-status` | `Current fixed status` |
| `soft-rebaseline-needed` | `Soft rebaseline needed` |
| `hard-rebaseline-needed` | `Hard rebaseline needed` |
| `rebaseline-complete` | `Rebaseline complete` |
| Not applicable to the item | `Not applicable` |
| Unknown or not yet reviewed | `Unknown` |

Map issue-page `change_audit_needed` metadata to the GitHub Project `Change audit needed` field as follows: `false` maps to `No`; `true` maps to `Yes`; unresolved intake or unclear cases map to `Pending review`; blocked audit-resolution cases map to `Blocked`.

When the audit framework or scoring system changes, classify the change before applying it:

| Change type | Required action |
| --- | --- |
| Wording clarification, formatting, or examples only | No rebaseline required. |
| New metadata, GitHub Project field, or non-score tracking category | Soft rebaseline unless the change exposes a score-affecting defect. |
| New required check, source rule, penalty, scoring component, component weight, baseline rule, or current-status gate | Hard rebaseline for already scored developed proposals unless the issue was already audited under the new rule. |
| Change to fixed zero-score categories | Rebaseline affected candidate, retired, merged, pending-finding, or moot rows. |

Change Audit workflow:

1. Assign a new rubric version before changing scoring rules or required audit filters.
2. Record governing-rule changes in the governing file that owns them. For proposal-specific Change Audits that do not alter governing rules or cross-project conventions, record the audit in the affected issue's sibling audit-history file and update the issue page and GitHub Project fields where applicable. Do not add a separate cumulative audit-log entry; historical project-wide logs remain read-only provenance records.
3. Conduct a systematic internal-consistency review of governing project materials before applying the change to any individual proposal. This review should be deep enough to catch the kinds of drift that arise from repeated structural edits rather than only obvious formatting errors. The following checks are a required floor, not an exhaustive ceiling; the auditor should follow any additional inconsistency, ambiguity, broken reference, stale convention, or implementation defect discovered during the review. At minimum, check the Framework kernel and every authoritative module implicated by the change, [`PRINT_ASSEMBLY.md`](../PRINT_ASSEMBLY.md), [`GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md), retained source-inventory headers, issue-page templates as reflected in developed pages, audit sidecar conventions, and Horizon Scan rules for:
   - misplaced ownership between Framework, Methodology, print assembly, GitHub Project, source inventory, issue pages, legislation pages, and Horizon Scan;
   - duplicated rules, conflicting instructions, obsolete rubric versions, stale terminology, inconsistent section names, and dead conventions;
   - broken or stale internal links, heading anchors, file paths, issue IDs, legislation paths, GitHub Project canonical-page links, audit-history links, and cross-references;
   - metadata/front-matter drift, including `issue_id`, `area_id`, `status`, `remedy_type`, `legislative_proposal`, `constitutional_proposal`, `audit_*` fields, publication disposition (`print_levels` or documented exclusion), and audit-history paths, together with coherence among GitHub `Development level`, `Status`, `needs: monitoring`, and any required workflow explanation;
   - tracking drift between GitHub Project items/fields, `sources.csv`, area README files, issue pages, legislation pages, and Horizon Scan;
   - language-rule drift, including neutrality conventions, title conventions, President/public-actor references, Project 2025 framing, and unsupported partisan or advocacy wording;
   - source-rule drift, including missing nearby citations, uncaptured cited sources, stale source line references, overconfident source characterization, and source claims that no longer match the page text;
   - proposal-to-legislation alignment risks that should be documented and reported for human review rather than automatically corrected; and
   - rule changes, inconsistencies, or factual/legal uncertainties that require human review before correction.
4. If the consistency review finds a governing-rule defect, correct the governing file that properly owns the rule when the correction is mechanical. If the defect requires a substantive judgment, document the discrepancy as an unresolved Change Audit finding and report it to the user before updating downstream pages.
5. Mark affected already-audited proposals as `soft-rebaseline-needed` or `hard-rebaseline-needed` in issue front matter and the GitHub Project `Rebaseline status` field, and state the corresponding meaning in plain language under **Scoring Basis** in the visible **Proposal Scoring** summary.
6. Preserve old scores, but treat non-current scores as provisional in summaries, comparisons, and prioritization.
7. During the next targeted Change Audit, T2, T3, or T4 audit of an affected developed proposal, resolve any `change_audit_needed` marker by performing the Internal Remedy-Fit Audit and any other affected checks. If the remedy, source basis, and scoring remain valid, clear `change_audit_needed`, update the issue-page metadata, update the issue-page **Proposal Scoring** summary, append the full audit entry to the sibling `ISSUE-ID.audit.md` file, and update GitHub Project fields where applicable. If the check changes the score, recalculate under the current rubric and set the rebaseline status to `current`. In GitHub Project fields, update `Change audit needed` to `No` and `Rebaseline status` to `Current` once the relevant checks are resolved.
8. Do not compare scores across rubric versions without noting the mismatch.
9. Do not rerun every proposal immediately unless the user asks; use the rebaseline status to queue the work responsibly.

Formatting-only or template-only changes may require a Change Audit even when they do not require score rebaseline. In that case, update affected pages, metadata, sidecars, GitHub Project fields, and source records as needed, but leave proposal-quality scores unchanged unless the change reveals a substantive scoring defect.
