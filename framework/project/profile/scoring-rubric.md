---
title: "ARRP Proposal Quality Scoring Profile"
status: active
dependencies:
  - "../../standards/audits/core.md"
  - "../../standards/audits/levels.md"
  - "../../standards/audits/verification.md"
  - "public-actor-conventions.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# ARRP Proposal Quality Scoring Profile

## Authority, Loading, and Dependencies

**Authority.** This module is authoritative for the 100-point Proposal Quality Score, component weights, penalties, score bands, rubric-change restrictions, conservative scoring, fixed-zero treatment, and score consistency. Release-candidate eligibility, including its minimum and preferred standards, belongs to the [Post-Admission Development Gates](maturity-profile.md#post-admission-development-gates).

**Load when.** Load this module whenever a Proposal Quality Score is assigned, recalculated, compared, displayed, challenged, or changed; whenever a scoring component, penalty, band, threshold, or rubric rule is interpreted or proposed for revision; and whenever fixed-zero treatment is evaluated. When a score is being considered as part of Release-candidate classification, load the lifecycle gate alongside this module; this module interprets the score but does not assign the maturity level.

**Dependencies.** Load the [Framework kernel](../../FRAMEWORK.md), [Audit Core](../../standards/audits/core.md), [Tiered Audit and Formatting Requirements](../../standards/audits/levels.md), and [Verification Protocol](../../standards/audits/verification.md). Load [Change Audits](../../standards/audits/change-audits.md) before any rubric change or rebaseline action. Load the adoption and external-review modules when those components are assessed.

## Rubric Version and Rebaseline Configuration

The current ARRP audit rubric version is **2026-06-27.2**.

| Version | Change | Rebaseline effect |
| --- | --- | --- |
| `2026-06-26.1` | First explicit rubric-version and rebaseline-tracking system. | Marked prior developed scores for rebaseline and fixed-status zero scores as current fixed-status values. |
| `2026-06-26.2` | Added Adoption Friction Score as a companion metric outside the 100-point Proposal Quality Score. | Soft rebaseline for otherwise-current developed proposals; hard rebaseline remains for developed proposals already awaiting formula rebaseline. |
| `2026-06-27.1` | Added the required T1 Enactment Pathway Check, including Required Electoral Environment, Pathway Viability, Development Priority, and Pathway Adjustment. The check is evidence-bound and feeds Adoption and Implementation scoring rather than creating a standalone score. | Hard rebaseline for developed proposals because the new required check can materially change Adoption and Implementation component credit. Fixed-status zero scores remain current fixed-status values. |
| `2026-06-27.2` | Clarified that legal availability is not adoption viability where a proposal depends on voluntary self-limitation by the same institutional actor whose discretion the proposal constrains. Added `conditional-current` Pathway Viability and required Adoption Score and Adoption Friction treatment for institutionally adverse adopters. | Hard rebaseline for developed proposals whose pathway depends on discretionary adoption by an institution or officer materially adverse to the reform, especially current-law or internal-policy vehicles. No rebaseline is required for proposals whose adoption path does not depend on that condition. |

Every proposal-quality score must identify the rubric version used. Use these
front-matter fields for developed issues when the page is next audited or
materially revised:

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

Use these exact labels in issue technical records when applicable: `Audit
Rubric Version`, `Rebaseline Status`, `Rebaseline Notes`, `Adoption Friction
Score`, `Adoption Friction Band`, `Adoption Friction Notes`, `Required
Electoral Environment`, `Pathway Viability`, `Development Priority`, `Pathway
Adjustment`, and `Enactment Pathway Notes`.

Rebaseline statuses have these exact meanings:

| Status | Meaning |
| --- | --- |
| `current` | The score was calculated under the current rubric version and may be compared with other current scores. |
| `current-fixed-status` | The issue has a fixed non-formula status, usually candidate, paused, retired, merged, pending controlling finding, or reliably moot; the zero score is current until the status changes. |
| `soft-rebaseline-needed` | The rubric added context or a non-score field, but the existing score remains usable with a caveat until the next audit. |
| `hard-rebaseline-needed` | The rubric could materially change the score; treat the existing score as provisional until a substantive audit recalculates it. |
| `rebaseline-complete` | A rebaseline audit was completed; normally convert this to `current` after repository and GitHub Project records are synchronized. |

Classify an ARRP rubric change before applying it:

| Change type | Required action |
| --- | --- |
| Wording clarification, formatting, or examples only | No rebaseline required. |
| New metadata, GitHub Project field, or non-score tracking category | Soft rebaseline unless the change exposes a score-affecting defect. |
| New required check, source rule, penalty, scoring component, component weight, baseline rule, or current-status gate | Hard rebaseline for already scored developed proposals unless already audited under the new rule. |
| Change to fixed zero-score categories | Rebaseline affected candidate, retired, merged, pending-finding, or moot rows. |

## Proposal Quality Score

The **Proposal Quality Score** is a provisional 0-100 planning value. It measures how ready the proposal is for reliance, external review, legislative outreach, or publication as a mature recommendation. It is not a measure of how important the underlying problem is.

Scores must be calculated consistently. A repeated audit using the same record, same rubric, and same findings should produce the same score. Audit count may inform the score only through the formula below; repetition alone must not increase the value. A score should increase only when an audit meaningfully broadens review, resolves findings, verifies sources, improves legal fit, strengthens drafting, reduces implementation risk, or improves adoption prospects without weakening the least-complex adequate remedy.

Use this mathematical formulation only after a proposal satisfies the single Developed-proposal package-completeness threshold in [Post-Admission Development Gates](maturity-profile.md#post-admission-development-gates). Candidate inventory entries, area-page issue bullets, source-development notes, and in-development proposals whose initial package remains incomplete receive no proposal-quality score.

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

For non-developed issues, use the fixed scores below. Retired, merged, reliably moot, candidate-inventory, and non-developed `Deferred` or `Blocked` issues are fixed at `0` and should not receive a formula-based proposal-quality score while that posture remains in effect. A Deferred or Blocked fixed-zero issue should receive only the applicable hold-predicate check until the recorded reconsideration condition, date, or indispensable prerequisite changes, unless the user expressly directs exploratory work consistent with the hold. A candidate issue may receive a formula-based score only after it satisfies the `Development level: Developed proposal` package-completeness gate in [Post-Admission Development Gates](maturity-profile.md#post-admission-development-gates). `Deferred` or `Blocked` does not by itself erase an established score or reduce an established `Development level`; preserve those independent fields unless the substantive scoring rules require a change.

| Issue status | Baseline score |
| --- | ---: |
| Retired or merged | 0 |
| Pending judicial finding, merits adjudication, or other controlling external finding | 0 |
| Reliably moot as a standalone proposal | 0 |
| Candidate inventory entry only | 0 |
| Candidate with source-development notes but no basic proposal framework | 0 |

## Adoption and Enactment-Pathway Configuration

ARRP's **Adoption Score** is the 12-point component of the Proposal Quality
Score. Apply the reusable
[Adoption and Enactment Pathway Analysis](../../standards/audits/adoption-and-pathways.md)
using these exact weights:

| Adoption subcomponent | Points |
| --- | ---: |
| Audience segmentation and audience-specific value proposition | 1.5 |
| Good-faith objection handling across partisan, independent, federalism, civil-liberties, administrative, and constitutional perspectives | 1.5 |
| Adoption vehicle, required electoral environment, and plausible sponsor, validator, or coalition map | 1.5 |
| Public-trust and reciprocity showing the proposal applies fairly across parties and administrations | 1.5 |
| Current, methodologically credible national polling or survey evidence supports the underlying reform principle | 1.5 |
| Current, methodologically credible state-level polling, referendum results, enacted-state practice, or comparable state evidence supports the underlying reform principle | 1.5 |
| The cited public-support evidence is specific to the proposal's actual mechanism rather than only a vague adjacent value | 1.5 |
| The proposal explains how popular support can be used without compromising legality, rights, minority protections, institutional independence, or remedy adequacy | 1.5 |
| **Total** | **12** |

| Score | Descriptor | Meaning |
| --- | --- | --- |
| 0 | Unassessed | Adoption path has not been scored. |
| 1-3 | Weak Adoption Basis | Adoption path is mostly undeveloped or unsupported. |
| 4-6 | Limited Adoption Basis | Some adoption logic exists, but key evidence is missing. |
| 7-9 | Credible Adoption Basis | Adoption path is reasonably developed and partly evidenced. |
| 10-11 | Strong Adoption Basis | Adoption path is well developed and well supported. |
| 12 | Exceptional Adoption Basis | Adoption path is unusually complete and strongly evidenced. |

When displayed, append the descriptor in parentheses, for example:
`5 / 12 (Limited Adoption Basis)`.

The Enactment Pathway Check begins at T1 and uses these exact values:

| Field | Allowed values |
| --- | --- |
| Required Electoral Environment | `current-law-available`; `house-oversight-majority`; `narrow-unified-government`; `filibuster-constrained-unified-government`; `sixty-vote-senate`; `filibuster-reform-or-exception`; `wave-election-mandate`; `post-crisis-repair-mandate`; `constitutional-amendment-environment`; `state-level-pathway`; `not-electorally-dependent`; `unassessed` |
| Pathway Viability | `current`; `conditional-current`; `plausible-after-wave`; `post-crisis-only`; `currently-dead-on-arrival`; `unassessed` |
| Development Priority | `immediate`; `active`; `conditional`; `reserve`; `deprioritized`; `unassessed` |
| Pathway Adjustment | `proceed`; `narrow`; `reframe`; `split`; `stage`; `convert-to-oversight`; `convert-to-state-model`; `reserve`; `unassessed` |

Do not award full adoption-vehicle credit unless Required Electoral Environment
and Pathway Viability are assessed. A `currently-dead-on-arrival` pathway
requires a credible narrowing, staging, oversight, state-model, or reserve
strategy for full credit; `unassessed` receives zero adoption-vehicle credit.
Speculative election modeling cannot raise the score.

Where the same institution or officer whose authority the reform constrains
must voluntarily adopt it, legal availability does not establish adoption
viability. Keep `current-law-available` only as the legal-vehicle
classification; use `conditional-current` unless reliable evidence shows
present willingness; award low or zero adoption-vehicle credit absent
leadership support, binding external mandate, enforceable statutory fallback,
appropriations condition, court order, settlement, or comparable pressure;
reflect the resistance in Adoption Friction; consider `stage`,
`convert-to-oversight`, `convert-to-state-model`, or `reserve`; and document the
distinction in visible Adoption Score, Adoption Friction, and Required
Electoral Environment annotations.

## Adoption Friction Configuration

ARRP's separate **Adoption Friction Score** is a 0-100 companion metric, not
part of the Proposal Quality Score:

| Friction subcomponent | Points |
| --- | ---: |
| Partisan salience: the proposal is likely to be treated as helping or harming a party, administration, movement, candidate, or named political figure | 0-15 |
| Constitutional or doctrinal controversy: the proposal depends on contested constitutional doctrine, uncertain judicial review, or significant statutory interpretation | 0-15 |
| Institutional disruption: the proposal changes authority, procedure, tenure, jurisdiction, funding, enforcement, or decision rights of powerful institutions | 0-15 |
| Rights or identity sensitivity: the proposal touches voting, speech, religion, equal protection, criminal process, immigration, privacy, bodily autonomy, or comparable high-salience rights | 0-10 |
| Stakeholder opposition intensity: concentrated or well-resourced actors are likely to oppose implementation | 0-15 |
| Public-understanding burden: opponents can plausibly caricature the proposal or the proposal requires substantial explanation to avoid misunderstanding | 0-10 |
| Implementation friction: the proposal requires new systems, appropriations, intergovernmental coordination, agency capacity, data-sharing, or complex administration | 0-10 |
| Litigation likelihood: prompt facial, as-applied, emergency, or strategic litigation is likely | 0-10 |
| **Total** | **100** |

| Score range | Band |
| --- | --- |
| `0-20` | Low Resistance |
| `21-40` | Manageable Resistance |
| `41-60` | Significant Resistance |
| `61-80` | High Resistance |
| `81-100` | Extreme Resistance |
| Unscored | Unassessed |

Record the score basis in the issue page, audit-history file, or both. Do not
infer it from general political intuition, treat it as a merits judgment, or
subtract it from the Proposal Quality Score. An unreviewed proposal uses blank
or `N/A` and `Unassessed`; fixed-zero rows use `N/A` unless they become
developed. A current developed proposal missing this score after rubric
version `2026-06-26.2` is `soft-rebaseline-needed`, unless a later
score-affecting change already requires hard rebaseline. Display an assessed
score with its band, for example `72 / 100 (High Resistance)`.

## External and International Review Configuration

Apply the reusable
[External and International Review](../../standards/audits/external-review.md)
using these exact ARRP external-review values:

| Status | Meaning |
| --- | --- |
| `not-reviewed` | No qualified external review has been incorporated. |
| `informal-review` | A qualified reviewer gave limited or conversational feedback documented at a high level. |
| `substantive-review` | A qualified reviewer reviewed the relevant proposal and material comments were incorporated or documented. |
| `reviewed-with-caveats` | A qualified reviewer found the proposal supportable within scope but identified disclosed caveats, limits, or unresolved risks. |
| `reviewed-no-material-objection` | A qualified reviewer raised no unresolved material objection within the stated review domain. |
| `approved-for-circulation` | A qualified reviewer affirmatively approved circulation within the stated scope, with permission to describe the review that way. |

| External Review Score | Required showing |
| ---: | --- |
| 0 | No qualified external professional review incorporated, or review is undocumented, outside the reviewer's domain, or unresolved. |
| 1 | Informal qualified review with limited notes, no major contradiction, and no claim of approval. |
| 2 | Substantive qualified review with comments incorporated or documented, but material caveats or limited scope remain. |
| 3 | Substantive review by a highly relevant attorney, legislative counsel, legislative staffer, legal scholar, practitioner, former official, or subject-matter expert, with material issues resolved or clearly disclosed. |
| 4 | Multiple relevant qualified reviewers, or formal written review by a highly relevant reviewer, with no unresolved material objection within the reviewed domain or with objections fully documented and addressed. |

External review increases the Proposal Quality Score only through this
component unless it actually improves another component. The record must state
what changed, what was validated, and what remains unresolved.

When international effects are materially relevant, use the separate 0-10
**International Support and Relations Score**:

| International subcomponent | Points |
| --- | ---: |
| Comparative democratic practice, foreign constitutional practice, or international institutional precedent supports the reform principle | 1 |
| Foreign governments, multilateral institutions, treaty bodies, democracy organizations, human-rights institutions, or allied policy communities have expressed support for similar institutional safeguards | 1 |
| The proposal would likely improve rule-of-law, democratic-resilience, anti-corruption, human-rights, or institutional-stability perceptions of the United States | 1 |
| The proposal would likely strengthen allied trust, treaty reliability, diplomatic credibility, or U.S. soft power | 1 |
| The proposal is unlikely to create serious adverse foreign-policy, national-security, treaty, intelligence-sharing, or alliance-management consequences | 1 |
| Public international, comparative-law, or allied-government sources identify the reform as consistent with democratic or rule-of-law practice | 1 |
| International legal, comparative-law, diplomatic, or policy scholarship supports the reform or identifies manageable concerns | 1 |
| The proposal accounts for likely international criticism or misunderstanding without distorting the remedy | 1 |
| The proposal distinguishes domestic constitutional necessity from international preference and does not rely on foreign or international support as a substitute for U.S. legal authority | 1 |
| The international assessment is current, sourced, balanced, and includes adverse evidence or unresolved uncertainty | 1 |

Use `N/A` with a short explanation when no material international dimension
exists. Use `0` and identify the source-refresh task when foreign-relations
effects may be material but current international sources have not been
checked.

## ARRP Audit Display and Technical Records

The visible **Proposal Scoring** summary groups the Proposal Quality Score,
Adoption Score when reported, Coalition Support Estimates when assessed,
Required Electoral Environment, Development Priority, External Review Status
when assessed, Adoption Friction, and any companion score or viability
indicator at the top. Follow that group with an em dash divider, then internal
review metadata using **Internal Review Status**, **Last Internal Review**,
**Scoring Standard**, **Scoring Basis**, **Revision Review** or **Revision
Review Needed**, **Next Review**, and **Full Review History** as applicable.
Translate technical status codes into plain language.

When Coalition Support Estimates appear, use one label followed by indented
inline-break rows:

```markdown
> **Coalition Support Estimates:**<br />&nbsp;&nbsp;&nbsp;&nbsp;Democratic 80%<br />&nbsp;&nbsp;&nbsp;&nbsp;Independent 60%<br />&nbsp;&nbsp;&nbsp;&nbsp;Republican 40%<br />&nbsp;&nbsp;&nbsp;&nbsp;Bipartisan viability 55%
```

Keep evidentiary caveats in the matching annotation segment. Mirror visible
labels in annotations where practical: **Quality Score**, **Adoption Score**,
**Coalition Support Estimates**, **External Review Status**, **Adoption
Friction**, **Required Electoral Environment**, and **Development Priority**.
Coalition estimates should not appear as a standalone `Support Appeal`
annotation unless the issue also needs a non-scoring substantive support
discussion. Superseded or withdrawn estimates do not remain in the compact
scoring group.

Each scored issue uses a sibling `ISSUE-ID.audit.md` file beside its issue
page. For example, `areas/DOJ/issues/DOJ-001.md` links to
`areas/DOJ/issues/DOJ-001.audit.md`. The sidecar is append-only, ordinarily
newest-first, and retains prior entries. Older entries may be corrected only
for clerical errors, broken links, stale line references, or clearly
identified inaccuracies. Compiled editions may omit or trim sidecars, but
source control retains the complete technical history.

Scored issue front matter uses `audit_status`, `audit_score`,
`audit_last_type`, `audit_last_date`, `audit_next`, `audit_rubric_version`,
`audit_rebaseline_status`, `change_audit_needed`, `change_audit_reason`, and
`audit_history` where applicable. External review adds
`external_review_status`, `external_review_type`, `external_review_date`,
`external_review_reviewer_role`, and `external_review_notes` when practical.
These fields must agree with the visible scoring summary and audit sidecar.


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

When an issue page displays a Proposal Quality Score, the threshold status should appear in parentheses immediately after the score, for example: `82 / 100 (Review Ready)`. Assign the GitHub Project `Development level` under [Post-Admission Development Gates](maturity-profile.md#post-admission-development-gates) and the [`ARRP GitHub Workflow`](../github/workflow.md#issue-development-lifecycle), not by copying every descriptive score-band label into the Project field; `Status` separately records the next workflow action or hold. A Status change does not independently alter the score or development level. Every canonical issue using `Deferred` must include a nonblank machine-readable `workflow_hold_reason` stating both why further development is affirmatively postponed and the condition or date for reconsideration. Every canonical issue using `Blocked` must use the same field to identify the blocked action, the concrete indispensable prerequisite, and the unblock trigger. Explanatory prose or a next-review note may supplement but does not replace that field. The Project Integrity Bot reports an omission or lifecycle-coherence problem rather than inventing, reclassifying, or repairing it. When a closed record has no active obligation, remove it from the active Project instead of assigning a terminal completion Status.

The score bands do not independently establish `Development level: Release candidate`; apply the separate gate in [Post-Admission Development Gates](maturity-profile.md#post-admission-development-gates).

Scores should remain conservative. When in doubt, record the lower score and identify the next audit needed to justify advancement.

Audit rows created before adoption of the component formula should be treated as provisional status scores. They should be recalculated under the formula when the next T2, T3, or T4 audit is performed.
