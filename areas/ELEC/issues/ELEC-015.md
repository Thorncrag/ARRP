---
issue_id: ELEC-015
area_id: A-02
title: "Ranked-Choice Voting and Majority-Choice Election Methods"
status: deferred
priority: high
remedy_type: election-method-reform
audit_score: 0
audit_status: "Deferred pending additional certified election-outcome data and additional election-method, ballot-access, party-system, and implementation input; fixed-zero preserved until remedy value and fit can be reassessed"
audit_last_type: "Deferred status update"
audit_last_date: "2026-07-10"
audit_next: "After the next midterm election cycle, update certified outcome data for RCV jurisdictions and obtain additional expert or stakeholder input; then reassess whether ELEC-015 should remain deferred, become an implementation-safeguards issue, or be retired in favor of upstream competition reforms"
audit_rubric_version: "2026-06-27.2"
audit_rebaseline_status: "current-fixed-status"
change_audit_needed: false
change_audit_reason: null
print_levels:
  - public-proposal
  - full-technical
audit_history: "ELEC-015.audit.md"
---

# ELEC-015 — Ranked-Choice Voting and Majority-Choice Election Methods

> ## Issue Snapshot
> **Problem:** Plurality rules can turn voter choice and candidate entry into strategic pressure.<br />**Repair:** Deferred pending additional election-outcome data and outside input before any remedy selection.<br />**Vehicle:** Pending later reassessment.
>

## Institutional Anomaly

Single-winner plurality elections can make elections feel binary even where voters hold more varied preferences. A voter may prefer a third candidate, independent candidate, minor-party candidate, or factional challenger, but avoid that vote because the preferred candidate is perceived as unable to win. The result is a recurring "spoiler" or "wasted vote" dynamic that can suppress candidacies, discourage coalition-building, and make winners in crowded fields appear less broadly legitimate.

Ranked-choice voting, instant-runoff voting, traditional runoffs, and related majority-choice election methods are attempts to repair that defect. Their shared premise is that election rules should let voters express broader preferences while preserving administrability, voter comprehension, ballot access, finality, recountability, and trust.

The institutional defect is not that every election must use ranked ballots. The defect is that plurality-default election systems often fail to ask whether a winner has majority support, whether voters can safely express backup preferences, and whether the tabulation process is transparent enough to maintain legitimacy.

## Manifestations of the Failure

### Spoiler pressure in single-winner elections

Plurality elections can penalize voters for supporting their first-choice candidate when that candidate is unlikely to finish first. This pressure may deter independent candidates, minor-party candidates, and intra-party challengers even before a campaign begins.

Ranked-choice voting is designed to reduce that pressure by allowing voters to rank candidates and by transferring votes under defined rules if no candidate has enough support to win initially. The mechanism can reduce first-round spoiler fears, but it also introduces implementation demands that ordinary plurality systems do not have.

The current research is mixed rather than conclusive. See MIT Election Data + Science Lab, [*Ranked Choice Voting: Instant Runoff Voting Use in the United States*](https://electionlab.mit.edu/research/ranked-choice-voting-instant-runoff-voting-use-united-states), and New America, [*What We Know About Ranked-Choice Voting*](https://www.newamerica.org/political-reform/reports/what-we-know-about-ranked-choice-voting/). ELEC-015 therefore treats reduced spoiler pressure as a proposition for continued testing, not a proven universal effect.

### Implementation complexity and voter comprehension

RCV and other majority-choice systems are not self-executing. Voters need clear ballot instructions, accessible materials, examples, error-prevention design, language assistance, and public education before Election Day. Election officials need tabulation rules, software or central-count procedures, public reporting formats, recount rules, and a way to explain exhausted ballots and transfer rounds without making the result appear opaque.

Maine supplies an important implementation source base because the Secretary of State maintains official ranked-choice voter information, rules, voter-instruction materials, tabulation glossaries, recount rules, and election-results/data pages with RCV summaries and cast-vote-record files. Maine's official FAQ states that the state uses ranked-choice voting for all state-level primary elections and, in general elections, only for federal offices, including President; the ranked-choice rounds apply only when a race has more than two candidates. See Maine Secretary of State, [Ranked Choice Voting Information and Rules](https://www.maine.gov/sos/elections-voting/upcoming/ranked-choice-voting-tabs), [Ranked-Choice Voting Frequently Asked Questions](https://www.maine.gov/sos/elections-voting/ranked-choice-voting-frequently-asked-questions), and [Election Results/Data](https://www.maine.gov/sos/elections-voting/election-results-data).

### Adoption, repeal pressure, and state-law fragmentation

State experimentation is moving in conflicting directions. NCSL's March 2026 ranked-choice voting brief identifies Alaska and Maine as statewide RCV users and also reports that 19 states prohibit ranked-choice voting in at least some elections. Alaska's nonpartisan-primary and ranked-choice general-election model has faced repeal pressure, while D.C. voters approved Initiative 83 in 2024, combining ranked-choice voting with unaffiliated-voter primary access. See NCSL, [Ranked Choice Voting](https://www.ncsl.org/elections-and-campaigns/ranked-choice-voting); Alaska Division of Elections, [2024 General Election Results](https://www.elections.alaska.gov/results/24GENR/); D.C. Council, [B25-1075 / Initiative 83 introduction PDF](https://lims.dccouncil.gov/downloads/LIMS/56767/Introduction/B25-1075-Introduction.pdf); and D.C. Board of Elections, [2024 General Election Results](https://electionresults.dcboe.org/election_results/2024-General-Election).

This mixed environment suggests that a model-state or voluntary-pilot path may be more realistic than an immediate national mandate. Reform durability depends on public understanding, transparent administration, cost realism, and local legal fit.

## Resulting Damage

Plurality-default and poorly implemented majority-choice systems can:

1. discourage voters from supporting their genuine first choice;
2. deter independent, minor-party, and challenger candidacies;
3. make crowded-field winners appear less legitimate;
4. intensify negative campaigning by preserving binary contest structure;
5. encourage strategic voting rather than sincere voting;
6. create public suspicion if tabulation rounds are hard to observe or explain;
7. increase administrative burden without adequate funding or training; and
8. trigger repeal backlash if reforms are adopted faster than voters and election officials can absorb them.

The issue should not assume that ranked-choice voting is always superior to plurality voting or traditional runoffs. It should ask when a majority-choice method is justified, which method is least complex for the election type, and which transparency safeguards are necessary before adoption.

## Underlying Weakness

Election-method design is fragmented across state constitutions, state statutes, local charters, party rules, ballot-design rules, election-equipment constraints, voter-education practices, and federal election-support programs. No single institution owns the problem of majority legitimacy, spoiler pressure, and tabulation trust.

Because election-method reforms affect both political incentives and election administration, they can be attacked from both directions: as partisan manipulation by opponents and as needless technical complexity by administrators or voters. A durable remedy therefore needs both democratic theory and implementation discipline.

## Current Evidence Synthesis

ELEC-015 should remain analysis-first rather than pro-RCV by default. The current Maine extraction does not show that RCV has produced a clear increase in candidate participation, alternative vote expression, or third-party/independent electoral success. The regular-primary turnout series shows a possible post-2018 increase, but 2018 was both Maine's first RCV-use cycle and the first midterm election of the Trump era, making that signal highly confounded. The absence of third-party or independent winners in the gathered Maine RCV record is relevant evidence against the strongest claim that RCV meaningfully disrupts two-party dominance, though it does not resolve narrower claims about backup-preference expression, voter experience, or implementation safeguards. The working Maine extraction table is maintained in [ELEC-015 Maine RCV Participation Data](../../../research/ELEC-015-maine-rcv-participation-data.md) through [GitHub sub-issue #244](https://github.com/Thorncrag/ARRP/issues/244).

This working read is consistent with the broader research landscape. The MIT Election Lab's 2026 explainer describes IRV effects as contested and concludes that most evidence remains inconclusive, especially outside local elections. See MIT Election Data + Science Lab, [Ranked Choice Voting: Instant Runoff Voting Use in the United States](https://electionlab.mit.edu/research/ranked-choice-voting-instant-runoff-voting-use-united-states). FairVote's research summary collects more favorable turnout, ranking-use, voter-understanding, and representation evidence, but it also acknowledges that RCV's full turnout impact is not yet known and that competitiveness and election timing are hard to separate from method effects. See FairVote, [Research and data on RCV in practice](https://fairvote.org/resources/data-on-rcv/). New America's synthesis similarly supports continued study while warning against overclaiming from incomplete evidence. See Lee Drutman and Maresa Strano, [What We Know About Ranked-Choice Voting](https://www.newamerica.org/political-reform/reports/what-we-know-about-ranked-choice-voting/). Recent academic work on turnout, mobilization, candidate entry, and real-world RCV performance supplies useful testable claims, but it does not by itself establish that a Maine-style RCV remedy is worth ARRP advocacy without a clearer institutional benefit. See Elisabeth Dowling, Caroline Tolbert, Nicholas Micatka, and Todd Donovan, [*Does ranked choice voting increase voter turnout and mobilization?*](https://doi.org/10.1016/j.electstud.2024.102816); Jonathan Colner, [*Running toward Rankings: Ranked Choice Voting's Impact on Candidate Entry and Descriptive Representation*](https://doi.org/10.1111/ajps.12908); and Adam Graham-Squire and David McCune, [*An Examination of Ranked Choice Voting in the United States, 2004-2022*](https://arxiv.org/abs/2301.12075).

The current synthesis is therefore: RCV may reduce some spoiler pressure and may support expressive backup voting, but the evidence gathered so far does not justify treating RCV as a proven fix for two-party dominance, candidate competition, or participation. If the institutional goal is to increase non-D/R viability, the primary repair likely occurs before tabulation: ballot access, debate access, party-recognition rules, fundraising, media visibility, primary structure, voter beliefs about viability, and district design. ELEC-015 should therefore own the downstream question of how votes are counted once voters have real choices, while upstream candidate-competition reforms remain primarily with [ELEC-013](ELEC-013.md) and representation-structure questions remain with [ELEC-011](ELEC-011.md). ELEC-015 should proceed only if later source development identifies a narrower defensible remedy, such as implementation safeguards for jurisdictions that independently adopt RCV, a voluntary pilot with rigorous reporting, or a comparative election-method standard that includes non-RCV alternatives.

## Proposal Survey

Future review should compare election-method tools rather than assume one. The key source-development question is whether Maine, Alaska, D.C., or other jurisdictions show measurable changes in candidate participation, voter participation, turnout, ballot completion, voter adaptation, candidate-field structure, or repeal pressure after majority-choice adoption, implementation, or attempted implementation.

**Maine operational record.** Maine remains the best initial comparator for operational maturity because it provides official ranked-choice voter materials, tabulation rules, result files, and cast-vote-record or summary data. Its current evidentiary value is mostly cautionary: the record can test claims about participation, alternative vote expression, ballot completion, and third-party viability, but the gathered data does not yet support a transformative RCV claim.

**Alaska top-four plus RCV record.** Alaska is the best comparator for political-system interaction because its reform combines a nonpartisan primary with RCV in the general election and has faced repeal pressure. Source development should separate participation effects from candidate-field structure, party strategy, repeal campaigns, and statewide political salience.

**D.C. adoption and implementation transition.** D.C. is the best comparator for adoption and transition because voters approved Initiative 83 in 2024, combining ranked-choice voting with unaffiliated-voter primary access. Source development should track certified initiative results, funding, implementation schedule, primary-turnout baseline, unaffiliated-voter participation, and any Council, Board of Elections, litigation, or delay materials.

**Ranked-choice voting / instant-runoff voting.** RCV lets voters rank candidates and uses transfer rounds if no candidate wins initially. It is most directly responsive to spoiler pressure in single-winner elections, but requires careful ballot design, voter education, accessible instructions, tabulation transparency, and recount rules.

**Traditional runoff elections.** Runoffs are familiar and may be easier to explain than ranked ballots. They can identify a majority winner after a second election, but they increase cost, delay finality, often produce lower-turnout second rounds, and do not eliminate first-round spoiler pressure.

**Nonpartisan, open, top-four, or top-five primary models.** Primary reforms can interact with RCV or runoffs by changing who advances to the general election. Alaska and D.C. are source-development leads, but these structures should be evaluated carefully because they may alter party associational interests and can disadvantage smaller parties if the general election is limited to top finishers.

**Federal pilot grants and technical standards.** Congress may be able to support voluntary state or local pilots through election-administration grants, technical assistance, reporting requirements, or HAVA-adjacent equipment and accessibility standards. A pilot-grant model would likely be less constitutionally aggressive than a national voting-method mandate.

**Model-state legislation.** A model-state act could specify election types eligible for RCV or runoffs, voter-instruction requirements, ballot-design standards, tabulation publication, cast-vote-record or equivalent transparency, recount rules, audit procedures, implementation timelines, and repeal or sunset-review procedures.

**Prior federal proposal families.** The Fair Representation Act, introduced in the 119th Congress as H.R. 4632, is a broad comparator because it proposes ranked-choice voting for congressional elections together with multi-member district and redistricting reforms. H.Res. 20, 119th Congress, is a process comparator because it would create a House Select Committee on Electoral Reform to study alternative congressional election methods. These are useful source leads, but ELEC-015 should not automatically adopt their full structural scope.

## Least-Complex Adequate Remedy

The least-complex adequate remedy is not yet selected. ELEC-015 is deferred pending additional certified election-outcome data and additional election-method, ballot-access, party-system, and implementation input. The current record does not justify treating RCV as a primary competition remedy; later review should decide whether ELEC-015 should remain deferred, become a narrow implementation-safeguards issue, or be retired in favor of upstream candidate-access and representation-structure reforms.

A plausible later path may be a model-state majority-choice election-method act, paired with an optional federal pilot-grant and technical-assistance framework. That approach would allow structured experimentation without immediately requiring a national RCV mandate for all federal elections, but it should not be selected until the participation record, implementation costs, transparency record, accessibility record, and repeal/durability evidence are source-developed.

The first remedy-selection pass should decide whether ELEC-015 should draft:

1. a model-state RCV/runoff implementation act;
2. a federal voluntary-pilot grant and technical-standards bill;
3. a combined model-state plus federal-support package; or
4. a narrower source-development memorandum before drafting.

## Repair and Prevention

Future drafting should evaluate whether reform text should require:

1. clear eligibility rules for which elections may use ranked-choice, runoff, or other majority-choice methods;
2. plain-language ballot instructions and sample ballots;
3. accessibility, language-access, and voter-error testing;
4. public tabulation rules and round-by-round result publication;
5. cast-vote-record publication or equivalent transparency with privacy safeguards;
6. recount and contest procedures tailored to transfer rounds or runoff elections;
7. election-equipment certification and cybersecurity review;
8. implementation grants, training, and voter-education funding;
9. cost reporting and post-election performance reports;
10. sunset, review, or repeal procedures that preserve voter confidence; and
11. clear boundaries with adjacent reforms owned by [ELEC-013](ELEC-013.md), [ELEC-011](ELEC-011.md), and [ELEC-009](ELEC-009.md).

## Proposed Legislation

- Pending development.

## Relationship to Adjacent Proposals

[ELEC-013](ELEC-013.md) concerns federal candidate access, debate gatekeeping, ballot-access floors, and FEC-facing competition rules. ELEC-015 now owns ranked-choice voting, runoffs, majority-choice election-method design, and implementation safeguards.

[ELEC-009](ELEC-009.md) concerns whether the Electoral College itself should be restructured or replaced by a national popular-vote system. ELEC-015 may supply election-method options, but it does not own the presidential-selection structure question.

[ELEC-011](ELEC-011.md) concerns representation safeguards, redistricting, district structure, and algorithmic map generation. ELEC-015 may cite multi-member or proportional-representation comparators only where they bear on election-method design; broader districting and representation remedies remain in ELEC-011.

## Budgetary Impact Statement

Budget authority may be required for voter education, ballot redesign, election-equipment updates, tabulation software, accessibility testing, training, recount administration, technical assistance, and state or local pilot grants; no dollar estimate is assigned pending source-backed cost data.

*Note: Preliminary ARRP assessment only; not a CBO, OMB, agency, or legislative-counsel score.*

## Proposal Scoring

> **Proposal Quality Score:** **[0 / 100](ELEC-015.audit.md)** (Not Scored; deferred pending additional data and input)<br />**Adoption Friction:** `N/A`<br />**Required Electoral Environment:** `N/A`<br />**Development Priority:** `N/A`
>
> —
>
> **Audit Status:** Deferred pending additional certified election-outcome data and additional election-method, ballot-access, party-system, and implementation input; fixed-zero preserved until remedy value and fit can be reassessed<br />**Last Audit:** Deferred status update<br />**Rubric Version:** `2026-06-27.2`; **Rebaseline:** `current-fixed-status`; **Change Audit Needed:** no<br />**Next Audit:** After the next midterm election cycle, update certified outcome data for RCV jurisdictions and obtain additional expert or stakeholder input; then reassess whether ELEC-015 should remain deferred, become an implementation-safeguards issue, or be retired in favor of upstream competition reforms<br />**Full Audit History:** [ELEC-015 audit history](ELEC-015.audit.md)

## Annotation

**Branch-Off Status.** ELEC-015 was created on July 6, 2026 to receive the ranked-choice voting, runoff, and majority-choice election-method material previously carried inside ELEC-013. The split keeps ELEC-013 focused on federal candidate-access, debate, and ballot-access rules while allowing ELEC-015 to develop election-method design on its own terms.

**Deferred Status.** ELEC-015 is deferred at 0/100 because the evidence gathered so far does not justify remedy selection. Additional certified outcome data and additional expert or stakeholder input are needed before deciding whether to draft a narrow implementation-safeguards proposal, preserve the issue as research-only, or retire it in favor of upstream competition reforms.

**Analysis-First Posture.** ELEC-015 should begin as comparative analysis rather than immediate remedy drafting. The first source-development question is whether Maine, Alaska, and D.C. show measurable changes in candidate participation, voter participation, turnout, ballot completion, voter adaptation, candidate-field structure, or repeal pressure after majority-choice adoption, implementation, or attempted implementation.

**Future Data Checkpoint.** Revisit ELEC-015 after the next midterm election cycle with certified outcome data. The update should specifically test whether RCV jurisdictions produced third-party or independent winners, materially changed alternative vote expression, or otherwise supplied evidence that the major bottleneck is not upstream ballot access, debate access, primary structure, fundraising, media visibility, or district design.

**Preflight Notice.** Any future audit should begin by notifying the user that ELEC-015 has no proposed legislation yet unless a draft has been added before that audit. Without drafting, the audit should be limited to source development, issue admission, remedy selection, and fixed-zero candidate review.

**Implementation Caution.** RCV and related election-method reforms can lose legitimacy if voters experience them as confusing, opaque, expensive, or imposed. The source-development priority is therefore not simply whether RCV is desirable; it is whether a specific implementation model can be explained, audited, recounted, funded, and administered.

**Legal Caution.** Future drafting should map state constitutional constraints, state election-code provisions, party-association concerns, Elections Clause authority, Article II implications for presidential elections, HAVA and EAC equipment issues, accessibility requirements, equal-protection arguments, and any state-law prohibitions on ranked-choice voting.

## Source Notes

- Maine Secretary of State, [Resources for Ranked-Choice Voting](https://www.maine.gov/sos/elections-voting/resources-for-ranked-choice-voting).
- Maine Secretary of State, [Ranked Choice Voting Information and Rules](https://www.maine.gov/sos/elections-voting/upcoming/ranked-choice-voting-tabs).
- Maine Secretary of State, [Ranked-Choice Voting Frequently Asked Questions](https://www.maine.gov/sos/elections-voting/ranked-choice-voting-frequently-asked-questions).
- Maine Secretary of State, [Election Results/Data](https://www.maine.gov/sos/elections-voting/election-results-data).
- Maine source-development table, [ELEC-015 Maine RCV Participation Data](../../../research/ELEC-015-maine-rcv-participation-data.md).
- NCSL, [Ranked Choice Voting](https://www.ncsl.org/elections-and-campaigns/ranked-choice-voting) (updated Mar. 23, 2026).
- MIT Election Data + Science Lab, [Ranked Choice Voting: Instant Runoff Voting Use in the United States](https://electionlab.mit.edu/research/ranked-choice-voting-instant-runoff-voting-use-united-states) (updated June 24, 2026).
- FairVote, [Research and data on RCV in practice](https://fairvote.org/resources/data-on-rcv/).
- Lee Drutman and Maresa Strano, New America, [What We Know About Ranked-Choice Voting](https://www.newamerica.org/political-reform/reports/what-we-know-about-ranked-choice-voting/) (Nov. 10, 2021).
- Elisabeth Dowling, Caroline Tolbert, Nicholas Micatka, and Todd Donovan, [*Does ranked choice voting increase voter turnout and mobilization?*](https://doi.org/10.1016/j.electstud.2024.102816), *Electoral Studies* 90 (2024).
- Jonathan Colner, [*Running toward Rankings: Ranked Choice Voting's Impact on Candidate Entry and Descriptive Representation*](https://doi.org/10.1111/ajps.12908), *American Journal of Political Science* 69:3 (2025).
- Adam Graham-Squire and David McCune, [*An Examination of Ranked Choice Voting in the United States, 2004-2022*](https://arxiv.org/abs/2301.12075) (2023).
- D.C. Council, [B25-1075 / Initiative 83 introduction PDF](https://lims.dccouncil.gov/downloads/LIMS/56767/Introduction/B25-1075-Introduction.pdf).
- D.C. Board of Elections, [2024 General Election Results](https://electionresults.dcboe.org/election_results/2024-General-Election).
- Alaska Division of Elections, [2024 General Election Results](https://www.elections.alaska.gov/results/24GENR/).
- Congress.gov, [H.R. 4632, 119th Congress, Fair Representation Act](https://www.congress.gov/bill/119th-congress/house-bill/4632).
- GovInfo, [H.R. 4632, 119th Congress, Fair Representation Act](https://www.govinfo.gov/content/pkg/BILLS-119hr4632ih/html/BILLS-119hr4632ih.htm).
- Congress.gov, [H.Res. 20, 119th Congress, Establishing the Select Committee on Electoral Reform](https://www.congress.gov/bill/119th-congress/house-resolution/20).
- GovInfo, [H.Res. 20, 119th Congress, Establishing the Select Committee on Electoral Reform](https://www.govinfo.gov/content/pkg/BILLS-119hres20ih/html/BILLS-119hres20ih.htm).
- Associated Press, [*Maine counts ranked choice ballots to determine nominees for governor and a US House race*](https://apnews.com/article/b45f3a07e354d0b66fb64ac02ab928a0) (June 2026).
- Axios, [*D.C. approves Initiative 83 for ranked-choice voting*](https://www.axios.com/local/washington-dc/2024/11/06/initiative-83-ranked-choice-voting-open-primaries-dc-council) (Nov. 6, 2024).
- Associated Press, [*Measure aimed at repealing Alaska's ranked choice voting system scores early, partial win in court*](https://apnews.com/article/eb3b45477ce41b654072bb28699f4b84) (June 2024).
