---
title: "ARRP External and International Review"
status: active
dependencies: "../audits/AUDIT_CORE.md; ../audits/VERIFICATION_PROTOCOL.md; PROPOSAL_QUALITY_AND_RUBRIC.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# External and International Review

## Authority, Loading, and Dependencies

**Authority.** This module is authoritative for external-review status, qualified-reviewer credit, reviewer-scope evidence, conditional professional-review points, and the International Support and Relations component.

**Load when.** Load this module only when external professional review is sought, received, represented, or scored; when T3 or T4 must determine whether qualified review remains necessary; or when international, diplomatic, comparative, treaty, alliance, human-rights, or foreign-relations effects are materially applicable.

**Dependencies.** Load the [Framework kernel](../FRAMEWORK.md), [Audit Core](../audits/AUDIT_CORE.md), [Verification Protocol](../audits/VERIFICATION_PROTOCOL.md), and [Proposal Quality and Rubric Governance](PROPOSAL_QUALITY_AND_RUBRIC.md). Load the legal-review or adoption module when the external or international record affects those subjects.

## External Review Status and Qualified Reviewers

External Review Score credit may be awarded only when the project record identifies the reviewer category, review date, review scope, reviewer domain, material comments or approval status, and how the review changed or validated the proposal. The project should not identify a reviewer by name, quote private feedback, or imply endorsement unless the reviewer has given permission.

Use careful language. Prefer `reviewed by a qualified reviewer`, `reviewed with comments incorporated`, `reviewed without unresolved material objection within the reviewer's domain`, or `approved for circulation by reviewer within stated scope`. Do not say that proposed legislation is legally approved, professionally certified, final, or guaranteed valid unless that exact characterization is supported by the reviewer's written authorization.

A **qualified reviewer** is a person whose professional role, training, or institutional experience is relevant to the specific part of the proposal being credited. Qualified reviewers may include:

1. a licensed attorney who is not reviewing only as a legislator or political advocate and whose practice, public-law experience, litigation experience, compliance work, or drafting experience is relevant to the proposal;
2. legislative counsel, a professional bill drafter, or a legislative attorney;
3. a legislator, committee staff member, or legislative staff member with jurisdictional, drafting, oversight, or implementation experience relevant to the proposal, with legal-credit limited to the person's actual expertise unless the person is also acting as a lawyer;
4. a law professor, legal scholar, public-administration scholar, political scientist, economist, historian, or other academic whose field directly bears on the legal, institutional, fiscal, empirical, or implementation claim being reviewed;
5. a current or former government official, inspector general staff member, agency counsel, ethics official, election administrator, prosecutor, defender, judge, court administrator, or comparable practitioner with direct institutional knowledge relevant to the proposal;
6. a civil-rights, civil-liberties, good-government, transparency, election, budget, national-security, labor, procurement, privacy, or other subject-matter professional whose expertise directly bears on the proposal's operation; or
7. an affected institutional stakeholder with implementation knowledge, where the credit is limited to implementation feasibility, burden, practical effect, or stakeholder response.

The following do not qualify by themselves for External Review Score credit: general reader approval, ordinary political agreement, media praise, social-media engagement, anonymous comments without verifiable credentials, LLM output, reviewer status outside the relevant domain, or review that cannot be documented in the project record.

External Review Status should use one of these values:

| Status | Meaning |
| --- | --- |
| `not-reviewed` | No qualified external review has been incorporated. |
| `informal-review` | A qualified reviewer gave limited or conversational feedback; comments are documented at a high level. |
| `substantive-review` | A qualified reviewer reviewed the relevant proposal and material comments were incorporated or documented. |
| `reviewed-with-caveats` | A qualified reviewer found the proposal supportable within scope but identified caveats, limits, or unresolved risks that remain disclosed. |
| `reviewed-no-material-objection` | A qualified reviewer raised no unresolved material objection within the stated review domain. |
| `approved-for-circulation` | A qualified reviewer affirmatively approved circulation within the stated scope, with permission to describe the review that way. |

External Review Score should be awarded conservatively:

| External Review Score | Required showing |
| ---: | --- |
| 0 | No qualified external professional review incorporated, or review is undocumented, outside the reviewer's domain, or unresolved. |
| 1 | Informal qualified review with limited notes, no major contradiction, and no claim of approval. |
| 2 | Substantive qualified review with comments incorporated or documented, but material caveats or limited scope remain. |
| 3 | Substantive review by a highly relevant attorney, legislative counsel, legislative staffer, legal scholar, practitioner, former official, or subject-matter expert, with material issues resolved or clearly disclosed. |
| 4 | Multiple relevant qualified reviewers, or formal written review by a highly relevant reviewer, with no unresolved material objection within the reviewed domain or with objections fully documented and addressed. |

External review increases the Proposal Quality Score only through the External-Review Score component unless the review actually improves another component, such as Legal Fit, Drafting, Implementation, Remedy, Abuse Resistance, or Adoption. A professional title alone never increases the score. The audit must identify what changed, what was validated, and what remains unresolved.

## International Support and Relations Score

Each developed proposal should receive a separate **International Support and Relations Score** from 0-10 where international effects are materially relevant. This score is a companion metric, not part of the 100-point Proposal Quality Score, because some strong domestic institutional repairs may have little direct international dimension.

Use this formula:

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

Do not assign international-support points without current, cited, and properly characterized evidence. International commentary, foreign media, or foreign-government statements may show salience or perception, but they should not be treated as proof of domestic legal adequacy.

If a proposal has no material international-relations dimension, record the score as `N/A` with a short explanation. If the proposal may materially affect foreign relations but the audit has not checked current international sources, record `0` and identify the source-refresh task.
