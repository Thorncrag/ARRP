---
title: "ARRP Proposal Quality and Rubric Governance"
status: active
dependencies: "../audits/AUDIT_CORE.md; ../audits/TIERED_AUDITS.md; ../audits/VERIFICATION_PROTOCOL.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Proposal Quality and Rubric Governance

## Authority, Loading, and Dependencies

**Authority.** This module is authoritative for the 100-point Proposal Quality Score, component weights, penalties, score bands, rubric-change restrictions, conservative scoring, fixed-zero treatment, and score consistency. Release-candidate eligibility, including its minimum and preferred standards, belongs to the [Post-Admission Development Gates](../lifecycle/foundation-and-development-gates.md#post-admission-development-gates).

**Load when.** Load this module whenever a Proposal Quality Score is assigned, recalculated, compared, displayed, challenged, or changed; whenever a scoring component, penalty, band, threshold, or rubric rule is interpreted or proposed for revision; and whenever fixed-zero treatment is evaluated. When a score is being considered as part of Release-candidate classification, load the lifecycle gate alongside this module; this module interprets the score but does not assign the maturity level.

**Dependencies.** Load the [Framework kernel](../FRAMEWORK.md), [Audit Core](../audits/AUDIT_CORE.md), [Tiered Audit and Formatting Requirements](../audits/TIERED_AUDITS.md), and [Verification Protocol](../audits/VERIFICATION_PROTOCOL.md). Load [Change Audits](../audits/CHANGE_AUDITS.md) before any rubric change or rebaseline action. Load the adoption and external-review modules when those components are assessed.

## Proposal Quality Score

The **Proposal Quality Score** is a provisional 0-100 planning value. It measures how ready the proposal is for reliance, external review, legislative outreach, or publication as a mature recommendation. It is not a measure of how important the underlying problem is.

Scores must be calculated consistently. A repeated audit using the same record, same rubric, and same findings should produce the same score. Audit count may inform the score only through the formula below; repetition alone must not increase the value. A score should increase only when an audit meaningfully broadens review, resolves findings, verifies sources, improves legal fit, strengthens drafting, reduces implementation risk, or improves adoption prospects without weakening the least-complex adequate remedy.

Use this mathematical formulation only after a proposal satisfies the single Developed-proposal package-completeness threshold in [Post-Admission Development Gates](../FRAMEWORK.md#post-admission-development-gates). Candidate inventory entries, area-page issue bullets, source-development notes, and in-development proposals whose initial package remains incomplete receive no proposal-quality score.

```
Proposal Quality Score =
  Structural Score
+ Evidence Score
+ Legal Fit Score
+ Prior-Proposal Score
+ Remedy Score
+ Implementation Score
+ Abuse-Resistance Score
+ Drafting Score
+ Cogency Score
+ Adoption Score
+ Project-Integration Score
+ External-Review Score
- Penalties
```

| Component | Maximum points |
| --- | ---: |
| Structural Score | 8 |
| Evidence Score | 12 |
| Legal Fit Score | 10 |
| Prior-Proposal Score | 8 |
| Remedy Score | 12 |
| Implementation Score | 8 |
| Abuse-Resistance Score | 8 |
| Drafting Score | 8 |
| Cogency Score | 6 |
| Adoption Score | 12 |
| Project-Integration Score | 4 |
| External-Review Score | 4 |
| **Total before penalties** | **100** |

For consistent application, use these component definitions:

| Component | Full-score standard |
| --- | --- |
| Structural Score | The issue has the required architecture, correct issue ownership, accurate status, and no unresolved duplication. |
| Evidence Score | Material factual, legal, causal, and real-world-example claims have nearby citations and source-inventory coverage. |
| Legal Fit Score | The proposal identifies verified authority, limits, doctrines, vulnerabilities, and judicial-scrutiny issues. |
| Prior-Proposal Score | Existing law, direct analogues, functional analogues, budget analogues where relevant, and prior models have been checked against authoritative records and weighted by enacted use, institutional review, sponsorship, co-sponsorship, bipartisan support, and legislative progress. |
| Remedy Score | The remedy is the least-complex adequate remedy and addresses repair, prevention, fallback options, and remedy mismatch risk. |
| Implementation Score | The proposal can be administered, funded, enforced, reviewed, updated, and moved through a vehicle that matches its required electoral environment without unrealistic institutional assumptions. |
| Abuse-Resistance Score | Capture, evasion, delay, retaliation, pretext, selective enforcement, and partisan conversion risks are identified and mitigated. |
| Drafting Score | Legislative or rule text uses proper vehicle, conventions, definitions, responsible actors, procedures, remedies, deadlines, review, and severability. |
| Cogency Score | The problem, weakness, damage, remedy, and implementation logic follow from each other without hidden premises or overclaiming. |
| Adoption Score | Support and adoption analysis, public-support evidence, audience fit, objection handling, adoption vehicle, coalition strategy, and required electoral environment are documented with evidence. |
| Project-Integration Score | Internal links, legislation links, issue status, remedy type, source inventory, audit metadata, audit-history sidecar, GitHub Project canonical-page links, area page, and compiled-document placement are consistent. |
| External-Review Score | Qualified expert, practitioner, legislative, stakeholder, judicial-scrutiny, or scholarly review has been documented, incorporated, and matched to the reviewer's domain. |

Apply each component as follows:

1. Award full points only when the relevant audit is complete and no material unresolved finding remains.
2. Award half points when the element is substantially present but has unresolved nonfatal findings.
3. Award zero points when the element is missing, materially unsupported, internally inconsistent, or not yet audited.
4. Do not estimate a component from general confidence. If evidence is unavailable, score the component as zero and record the missing work as the next audit need.
5. Do not award component credit based on memory, assumed expertise, model-generated assertions, or uncited background knowledge where verification is feasible.
6. Round only the final score, using ordinary whole-number rounding. If the result is exactly halfway between two whole numbers, round down.
7. If two auditors applying the same record would plausibly differ, use the lower score and record the ambiguity.

Apply penalties after adding component scores:

| Penalty | Points |
| --- | ---: |
| Unsupported material factual claim | -5 each |
| Unsupported material legal claim | -5 each |
| Missing nearby citation for a named real-world event | -3 each |
| Missing source inventory row for an external source | -2 each |
| Citation does not support the proposition for which it is used | -5 each |
| Invented or unverified case, statute, bill, poll, report, scholar, official action, quotation, sponsor count, or vote count | -10 each |
| Current-law, pending-legislation, pending-judicial-matter, polling, or public-support claim not checked for currency | -5 each |
| Internal project link missing where target exists | -1 each |
| Remedy depends on the same failed institution without fallback | -8 |
| Serious abuse, evasion, or selective-enforcement risk unaddressed | -8 |
| Proposed legislation departs from legislative conventions without justification | -5 |
| Judicial-scrutiny risk not identified for a legally vulnerable proposal | -5 |
| Pending judicial opinion or pending controlling case not checked where it could materially affect the proposal | -5 |
| Existing-law amendment path not checked before new architecture | -5 |
| Duplicative issue ownership unresolved | -5 |
| Required current-status, mootness, or material-reframing check not completed at the selected tier | -5 |
| Reliable current source shows material reframing, partial mootness, or superseding development not reflected in the issue page | -10 |

The final score may not be lower than 0 or higher than 100. Penalties should be recorded as findings so a later audit can reproduce the same calculation and remove the penalty only when the defect has been corrected.

For non-developed issues, use the fixed scores below. Retired, merged, reliably moot, candidate-inventory, and non-developed `Deferred` or `Blocked` issues are fixed at `0` and should not receive a formula-based proposal-quality score while that posture remains in effect. A Deferred or Blocked fixed-zero issue should receive only the applicable hold-predicate check until the recorded reconsideration condition, date, or indispensable prerequisite changes, unless the user expressly directs exploratory work consistent with the hold. A candidate issue may receive a formula-based score only after it satisfies the `Development level: Developed proposal` package-completeness gate in [Post-Admission Development Gates](../FRAMEWORK.md#post-admission-development-gates). `Deferred` or `Blocked` does not by itself erase an established score or reduce an established `Development level`; preserve those independent fields unless the substantive scoring rules require a change.

| Issue status | Baseline score |
| --- | ---: |
| Retired or merged | 0 |
| Pending judicial finding, merits adjudication, or other controlling external finding | 0 |
| Reliably moot as a standalone proposal | 0 |
| Candidate inventory entry only | 0 |
| Candidate with source-development notes but no basic proposal framework | 0 |


## Score Consistency Rules

To keep scoring reproducible across audits:

1. Record the component scores, penalties, audit date, audit scope, and source record used to calculate the final score.
2. Record whether each component received full, half, or zero credit and identify the evidence supporting that choice.
3. Do not change a score unless at least one component score, penalty, public-support input, or baseline status changes.
4. Do not award points for intended future work, uncited knowledge, informal confidence, assumed public opinion, or repeated review of unchanged material.
5. Treat unknown, unavailable, stale, methodologically weak, uncited, or unreviewed inputs as unresolved rather than favorable.
6. Use the lower score where a component sits between two values.
7. If separate reviewers would assign different scores, require them to identify the disputed component, cited evidence, and specific rule causing disagreement; absent resolution, use the lower score.
8. Keep prior audit scores visible in the audit record where practical so score movement can be explained.
9. If the scoring formula is later amended, assign a new audit rubric version, record the version used for the audit, and update the rebaseline status of affected proposals.
10. A higher score should reflect stronger reliability, not merely a longer or more elaborate proposal.
11. A scoring rubric, formula, component, weight, penalty, threshold, or score band may change only with recorded human approval through a project-level Change Audit. The change must have a methodological justification independent of any desired issue or portfolio result, assign a new rubric version, analyze effects across all affected proposals, and apply the appropriate rebaseline treatment.
12. Never modify a scoring rule to raise, lower, preserve, or otherwise engineer a desired proposal score, Review Ready count, portfolio trajectory, or other reported result.

Use the following bands to interpret formula-based scores. These bands do not replace the scoring formula and should not be used to award points independently:

| Score range | Threshold status | Meaning |
| --- | --- | --- |
| 0 | Not Scored | Retired, merged, non-developed and blocked by a controlling prerequisite, reliably moot, still a candidate, or lacking a standalone proposal-quality score. |
| 1-24 | Early/Partial Draft | Developed proposal with severe unresolved defects or only minimal audit support. |
| 25-49 | Early/Partial Draft | Partial draft or early development with significant unresolved source, legal, remedy, or structure issues. |
| 50-64 | Developed Draft | Developed draft with meaningful framework structure but incomplete source, legal-fit, prior-proposal, adoption, or implementation review. |
| 65-74 | Substantially Developed Draft | Substantially developed proposal with several audit components complete; useful internally but still carrying material unresolved issues. |
| 75-84 | Review Ready | Strong enough for knowledgeable external critique, with source verification, existing-law fit, prior-proposal review, and remedy analysis substantially complete. |
| 85-89 | Advanced Review Ready | Most internal checks are complete, but key external validation, adoption evidence, judicial-risk resolution, or implementation support remains incomplete. |
| 90-94 | Proposal Ready | Mature enough for serious proposal packets or stakeholder circulation, with any remaining caveats clearly disclosed. |
| 95-99 | Publication Ready | Publication-ready or near-publication-ready proposal with external expert, practitioner, legislative, stakeholder, or comparable review incorporated. |
| 100 | Fully Validated | Fully validated under the current rubric; theoretically possible, but not expected for most institutional-reform proposals. |

When an issue page displays a Proposal Quality Score, the threshold status should appear in parentheses immediately after the score, for example: `82 / 100 (Review Ready)`. Assign the GitHub Project `Development level` under [Post-Admission Development Gates](../FRAMEWORK.md#post-admission-development-gates) and [`GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md#issue-development-lifecycle), not by copying every descriptive score-band label into the Project field; `Status` separately records the next workflow action or hold. A Status change does not independently alter the score or development level. Every canonical issue using `Deferred` must include a nonblank machine-readable `workflow_hold_reason` stating both why further development is affirmatively postponed and the condition or date for reconsideration. Every canonical issue using `Blocked` must use the same field to identify the blocked action, the concrete indispensable prerequisite, and the unblock trigger. Explanatory prose or a next-review note may supplement but does not replace that field. The Project Integrity Bot reports an omission or lifecycle-coherence problem rather than inventing, reclassifying, or repairing it. When a closed record has no active obligation, remove it from the active Project instead of assigning a terminal completion Status.

The score bands do not independently establish `Development level: Release candidate`; apply the separate gate in [Post-Admission Development Gates](../FRAMEWORK.md#post-admission-development-gates).

Scores should remain conservative. When in doubt, record the lower score and identify the next audit needed to justify advancement.

Audit rows created before adoption of the component formula should be treated as provisional status scores. They should be recalculated under the formula when the next T2, T3, or T4 audit is performed.
