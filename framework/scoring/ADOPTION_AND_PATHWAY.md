---
title: "ARRP Adoption and Enactment Pathway Analysis"
status: active
dependencies: "../audits/AUDIT_CORE.md; ../audits/VERIFICATION_PROTOCOL.md; PROPOSAL_QUALITY_AND_RUBRIC.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Adoption and Enactment Pathway Analysis

## Authority, Loading, and Dependencies

**Authority.** This module is authoritative for the Adoption Score, Required Electoral Environment, Pathway Viability, Development Priority, Pathway Adjustment, Adoption Friction, support and opposition analysis, coalition-support estimates, and political-language review.

**Load when.** Load this module beginning at T1 for enactment-pathway classification; whenever adoption, implementation, coalition support, political feasibility, development priority, opposition, or institutional self-limitation is analyzed; and whenever an Adoption Score or Adoption Friction score is assigned or changed.

**Dependencies.** Load the [Framework kernel](../FRAMEWORK.md), [Audit Core](../audits/AUDIT_CORE.md), [Verification Protocol](../audits/VERIFICATION_PROTOCOL.md), and [Proposal Quality and Rubric Governance](PROPOSAL_QUALITY_AND_RUBRIC.md). Public-support evidence must satisfy the verification protocol and may not be inferred from intuition or partisan stereotypes.

## Adoption Score Formula

The **Adoption Score** is part of the 100-point proposal-quality score and is capped at 12 points. It should be calculated the same way in each audit:

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

Adoption score bands are interpreted as follows:

| Score | Descriptor | Meaning |
| --- | --- | --- |
| 0 | Unassessed | Adoption path has not been scored. |
| 1-3 | Weak Adoption Basis | Adoption path is mostly undeveloped or unsupported. |
| 4-6 | Limited Adoption Basis | Some adoption logic exists, but key evidence is missing. |
| 7-9 | Credible Adoption Basis | Adoption path is reasonably developed and partly evidenced. |
| 10-11 | Strong Adoption Basis | Adoption path is well developed and well supported. |
| 12 | Exceptional Adoption Basis | Adoption path is unusually complete and strongly evidenced. |

Do not award polling or public-support points unless the evidence is cited, current enough for the claim being made, methodologically credible, and captured in [`sources.csv`](../../inventory/sources.csv). For volatile political questions, polling should normally be treated as current only if it was released within the last two years or if the audit explains why older evidence remains probative. For durable structural preferences, older evidence may be used only with a qualification.

State-level and federal-level support should be evaluated separately. National polling may show broad federal salience; state polling, referendum results, enacted-state practice, or bipartisan state adoption may show practical political viability. Neither should be substituted for the other without explanation.

Public support should increase only the Adoption Score. It should not override legal defects, source weaknesses, abuse risks, or an inadequate remedy. A popular proposal can still receive a low overall score if it is legally vulnerable, poorly drafted, unsupported by sources, or unlikely to survive implementation.

Do not award full adoption-vehicle credit unless the proposal identifies its Required Electoral Environment and Pathway Viability using the Enactment Pathway Check. If the pathway is `currently-dead-on-arrival`, full Adoption Score credit requires a credible narrowing, staging, oversight, state-model, or reserve strategy. If the pathway is `unassessed`, adoption-vehicle credit is zero until assessed.

## Enactment Pathway Check

Every developed proposal should receive an early **Enactment Pathway Check** beginning at T1. The check asks: **what kind of electoral environment is required to make this proposal seriously actionable, and can the proposal be adjusted to fit a more realistic environment without weakening the remedy below adequacy?**

This check is not a standalone score. It feeds the **Adoption Score** and **Implementation Score**:

- Adoption credit requires a realistic political pathway, coalition threshold, and evidence-supported account of the electoral or institutional conditions needed for passage.
- Implementation credit requires a vehicle that matches the pathway, such as oversight, statute, appropriations rider, rules reform, agency action, omnibus package, state model, or constitutional amendment.

Use these required values:

| Field | Allowed values |
| --- | --- |
| Required Electoral Environment | `current-law-available`; `house-oversight-majority`; `narrow-unified-government`; `filibuster-constrained-unified-government`; `sixty-vote-senate`; `filibuster-reform-or-exception`; `wave-election-mandate`; `post-crisis-repair-mandate`; `constitutional-amendment-environment`; `state-level-pathway`; `not-electorally-dependent`; `unassessed` |
| Pathway Viability | `current`; `conditional-current`; `plausible-after-wave`; `post-crisis-only`; `currently-dead-on-arrival`; `unassessed` |
| Development Priority | `immediate`; `active`; `conditional`; `reserve`; `deprioritized`; `unassessed` |
| Pathway Adjustment | `proceed`; `narrow`; `reframe`; `split`; `stage`; `convert-to-oversight`; `convert-to-state-model`; `reserve`; `unassessed` |

The pathway finding must be source-based and reproducible. Do not assign a favorable pathway value from intuition, hope, a single speculative scenario, or assumed partisan advantage. Use the most concrete reliable evidence available for the tier, including:

- current chamber control, seat margins, committee control, veto posture, and filibuster or cloture constraints;
- recent relevant votes, sponsor and co-sponsor patterns, bipartisan sponsorship, committee action, discharge attempts, vetoes, overrides, and enacted analogues;
- current and recent polling on the underlying reform principle, with method, date, sample, and source recorded when relied upon;
- historical wave or collapse-election data only when used as scenario context, not as proof that a future wave will occur;
- recent ballot-measure, referendum, state-enactment, or local-enactment results where the proposal has state or local analogues;
- recent judicial decisions, pending cases, injunctions, agency actions, executive orders, regulations, and enforcement developments that change viability;
- credible voter-sentiment, trust, legitimacy, or institutional-confidence data where directly relevant and properly sourced;
- public statements, platform commitments, leadership positions, or committee agendas from relevant lawmakers or institutional actors, characterized cautiously.

At T1, the check may be preliminary, but it must still be evidence-bound. If sufficient evidence is not available within T1, record `unassessed` or the least favorable supported pathway and identify the source work needed for T2. At T2 or higher, do not award full Adoption or Implementation credit unless the pathway is supported by cited evidence and the proposal explains whether narrowing, staging, reframing, oversight conversion, state-model conversion, or reserve status would improve viability without sacrificing remedy adequacy.

Speculative election-scenario modeling may inform planning but must not itself increase the Proposal Quality Score. A proposal receives credit for correctly identifying its minimum required environment and adjusting the vehicle realistically, not for assuming that a favorable election environment will occur.

### Institutional Self-Limitation Rule

Legal availability and adoption viability are distinct. A proposal may be `current-law-available` because an agency, officer, court, chamber, committee, or other institution already has authority to adopt it, while still having little or no realistic adoption potential because the required adopter is the same actor whose discretion, power, secrecy, flexibility, or political advantage the proposal would constrain.

When adoption depends on voluntary self-limitation by an institution or officer that is materially adverse to the reform, the audit must:

1. keep `current-law-available` only as a statement of legal vehicle availability, not as proof of adoption likelihood;
2. use `conditional-current` for Pathway Viability unless reliable evidence shows the required adopter is presently willing to adopt the reform;
3. award low or zero Adoption Score credit for the adoption-vehicle subcomponent absent evidence of leadership support, binding external mandate, enforceable statutory fallback, appropriations condition, court order, settlement, or comparable adoption pressure;
4. reflect institutional self-limitation resistance in Adoption Friction, including stakeholder opposition, institutional disruption, public-understanding burden, and implementation friction where applicable;
5. consider `stage`, `convert-to-oversight`, `convert-to-state-model`, or `reserve` as Pathway Adjustment values when the internal or current-law path is formally available but practically nonviable under current leadership; and
6. document the distinction in the issue-page **Adoption Score**, **Adoption Friction**, and **Required Electoral Environment** annotations when those fields are visible.

This rule is a hallucination-resistance guardrail: do not treat a formally available vehicle as realistically adoptable merely because the project can write the rule text.

## Adoption Friction Score

Each developed proposal should receive a separate **Adoption Friction Score** from 0-100. This is a companion metric, not part of the 100-point Proposal Quality Score. It measures the expected intensity of organized opposition, litigation, procedural blockade, public misunderstanding, or institutional resistance. Higher friction does not mean lower quality; a proposal can be high-quality and high-friction.

Use this formula:

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

Bands:

| Score range | Band |
| --- | --- |
| `0-20` | Low Resistance |
| `21-40` | Manageable Resistance |
| `41-60` | Significant Resistance |
| `61-80` | High Resistance |
| `81-100` | Extreme Resistance |
| Unscored | Unassessed |

Apply the score conservatively:

1. Do not infer a friction score from general political intuition alone; record the basis in the issue page, sibling audit-history file, or both.
2. Do not treat friction as opposition to the proposal's merits. Friction is about expected resistance and adoption difficulty.
3. Do not subtract friction from Proposal Quality Score. Use it to prioritize framing, coalition work, litigation preparation, implementation planning, and public explanation.
4. If the proposal has not yet received an adoption-friction review, record the score as blank or `N/A` and the band as `Unassessed`.
5. If a developed proposal is otherwise current but lacks an adoption-friction score after version `2026-06-26.2`, mark it `soft-rebaseline-needed` until the next audit assigns or expressly defers the score. If the proposal already has `hard-rebaseline-needed` status for a later score-affecting rubric change, keep the hard-rebaseline status rather than downgrading it to soft.
6. Fixed zero-status rows should use `N/A` unless and until the issue becomes developed.
7. When an issue page displays an assessed Adoption Friction Score, the band should appear in parentheses immediately after the score, for example: `72 / 100 (High Resistance)`.


## Support and Adoption Audit

Each developed proposal should be reviewed for support and adoption prospects among the audiences most likely to affect adoption, implementation, public legitimacy, and long-term durability.

Support estimates, audience-appeal percentages, coalition viability estimates, and similar scoring judgments should be consolidated here, in the issue's `Proposal Scoring` summary, or in the issue's audit-history sidecar. When an audit has assigned audience-class percentage estimates, the issue-page `Proposal Scoring` summary should display them in the top score group as **Coalition Support Estimates** unless the estimate has been superseded or withdrawn. They should not appear as standalone `Support Appeal` annotations unless the issue also needs a non-scoring substantive support discussion. When estimates are not based on polling or comparable evidence, label them as provisional planning judgments in the matching **Coalition Support Estimates** annotation segment or audit-history sidecar, not necessarily in the compact scoring box, and do not award polling or public-support score credit for them.

The audit should include:

1. **Audience segmentation.** Identify the proposal's likely audiences, including lawmakers, legislative staff, policy organizations, good-government groups, civil-liberties groups, independents, institutional conservatives, libertarians, federalism advocates, politically cross-pressured Republicans or conservatives, former supporters of the conduct or movements examined, election administrators, legal academics, journalists, affected administrators, practitioners, and informed citizens where relevant. Do not assume receptiveness or non-receptiveness solely from political identity.
2. **Audience-specific value proposition.** Confirm that each important receptive audience can quickly see why the proposal matters to its own concerns, duties, incentives, or institutional commitments. This does not require the proposal to relitigate ARRP's foundational premise for readers who categorically reject it.
3. **Objection handling.** Identify the strongest good-faith objections from Democratic, Republican, independent, bipartisan, federalism, civil-libertarian, constitutional, administrative-burden, cost, implementation, and separation-of-powers perspectives, and determine whether the proposal answers them.
4. **Bad-faith misuse and caricature.** Identify how opponents could misstate, weaponize, or caricature the proposal, then revise framing or drafting to reduce avoidable misreading without weakening the remedy below adequacy.
5. **Institutional-conservative appeal.** Test whether the proposal can be defended in terms of restraint, rule of law, separation of powers, federalism, anti-corruption, predictability, reciprocity, and protection against future abuse by either party.
6. **Civil-liberties appeal.** Test whether the proposal protects due process, speech, association, equal treatment, privacy, fair notice, neutral enforcement, and limits on coercive state power.
7. **Administrative burden.** Determine whether the proposal is too complex, costly, paperwork-heavy, litigation-dependent, or agency-dependent, and whether a simpler implementation design would preserve adequacy.
8. **Lawyer and legislative-counsel seriousness.** Test whether a legally trained reader would see clear authority, precise terms, correct statutory hooks, clean definitions, appropriate severability, enforceable procedures, and no avoidable overclaiming.
9. **Staffer one-page test.** Confirm that a congressional staffer or policy aide can understand the problem, proposed repair, legal authority, cost or burden, likely opposition, and core talking point in under five minutes.
10. **Neutrality versus candor.** Confirm that the proposal avoids partisan framing while still naming objectively documented misconduct, institutional damage, and constitutional stakes where the record supports doing so. As part of that existing review, distinguish fact, law, disputed interpretation, and ARRP's position; acknowledge material partisan perception or present political alignment; and explain the party-neutral institutional principle and how the design operates under materially different political control. Apply any recorded human reversed-control decision without answering or inferring it.
11. **Adoption path.** Identify the most realistic vehicle, such as standalone legislation, amendment to a moving bill, appropriations rider, oversight hearing, committee report language, agency rule, state model law, court rule, professional standard, or constitutional amendment.
12. **Coalition sponsor map.** Identify plausible champions, co-sponsors, validators, and unusual coalitions, including civil-liberties groups, institutional conservatives, election officials, veterans' organizations, former officials, inspectors general, state administrators, legal scholars, policy centers, or professional associations where relevant.
13. **Current public-support evidence.** Identify whether credible current polling, survey evidence, referendum results, state practice, federal legislative support, or bipartisan adoption evidence supports the proposal's actual mechanism at the federal level, state level, or both.
14. **Public trust.** Confirm that an ordinary reader would see the proposal as fair, reciprocal, and applicable to future officeholders of either party.

The audit should produce a concise support plan identifying likely supporters, likely skeptics, likely opposition arguments, possible validators, preferred adoption vehicle, public-support evidence, and changes that could increase support without weakening the least-complex adequate remedy.

## Political-Language and Coalition-Appeal Audit

Each developed proposal should be reviewed for political-language neutrality and potential appeal across the likely adoption coalition.

The audit should check whether the proposal:

1. uses institution-focused language rather than partisan slogans, unnecessary personal attacks, or avoidably factional framing;
2. states concrete misconduct or institutional damage directly where supported by evidence, without diluting the project's truth-telling function, while distinguishing established facts, governing law, disputed interpretation or uncertainty, and ARRP's own position;
3. explains why the safeguard should appeal to Democrats, Republicans, independents, institutionalists, civil libertarians, federalists, good-government advocates, politically cross-pressured conservatives, former supporters who remain open to evidence, and other plausible receptive constituencies;
4. identifies likely objections from Democratic, Republican, independent, bipartisan, institutional, civil-libertarian, federalism, administrative, and implementation perspectives;
5. distinguishes objections to the proposal's policy merits from objections arising from partisan loyalty, short-term advantage, or bad-faith opposition;
6. considers whether neutral wording, narrower triggers, safer enforcement procedures, sunset review, reporting requirements, or clearer safe harbors could increase support without weakening the remedy below adequacy; and
7. identifies risks that the proposal could be captured, selectively enforced, or rhetorically reframed as a partisan weapon and, where ARRP's own position has materially uneven present political implications, provides the disclosure required by the [Substantive Positions and Partisan Perception](../FRAMEWORK.md#substantive-positions-and-partisan-perception) rule.

The audit should include provisional percentage estimates of likely support or appeal for at least the following audience classes:

| Audience class | Required estimate |
| --- | --- |
| Bipartisan / cross-party institutionalist support | Estimated percentage likely to find the proposal supportable in principle |
| Independent support | Estimated percentage likely to find the proposal reasonable or confidence-building |
| Democratic support | Estimated percentage likely to support the proposal as framed |
| Republican support | Estimated percentage likely to support the proposal as framed |

Percentage estimates are not polling claims. They are disciplined planning judgments that should be stated as provisional, briefly justified, and revised as better evidence, stakeholder feedback, polling, legislative behavior, expert review, or coalition analysis becomes available.

Each estimate should identify the principal reason for support, the principal reason for resistance, and any framing or design change that could increase adoption prospects without compromising the least-complex adequate remedy.
