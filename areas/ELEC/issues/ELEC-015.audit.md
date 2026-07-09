---
issue_id: ELEC-015
title: "Ranked-Choice Voting and Majority-Choice Election Methods — Audit History"
source_issue: "ELEC-015.md"
print_levels:
  - full-technical
---

# ELEC-015 — Audit History

This file preserves the full audit history for [ELEC-015](ELEC-015.md). The issue page keeps only the compact Proposal Scoring summary.

## Audit History

The entries below preserve issue-specific audit history and source-development checkpoints.

### 2026-07-09 — Development Note: Maine RCV Participation Source File

**Status:** Development note only; no audit run.

**Scope:** Created a dedicated Maine source-development file at [ELEC-015 Maine RCV Participation Data](../../../source-development/ELEC-015-maine-rcv-participation-data.md) and linked it from the issue page. The file starts the Maine candidate-participation and voter-participation extraction with official Secretary of State sources. Its core comparison model tracks the election referenced, timeframe role, office or contest, RCV status, number of candidates, voter turnout or ballots cast, and comparability notes. Election outcome is not treated as a core field; RCV activation, round count, and exhausted ballots are preserved only as secondary ballot-experience context. The trend frame uses 2010-2017 as the eight-year pre-RCV baseline, keeps 2018 separate as the operational launch/transition year, and uses 2019-2026 as the eight-year post-launch/current comparison window. The next extraction checklist covers candidate lists, withdrawals, first-choice files, cast-vote records, non-RCV comparators, and prior-cycle results.

**Archive feasibility update:** Maine's official archive appears sufficient for a usable pre-RCV baseline, especially even-year cycles. A first 2012 extraction from official pipe-delimited TXT files produced candidate counts and ballots-cast values for Democratic and Republican U.S. Senate primaries and U.S. House District 1 and District 2 primaries. The source file now distinguishes strong baseline years from odd-year referendum/special-election context years and flags old XLS/PDF formats for later tooling or manual verification.

**Presentation update:** Added a reader-facing presentation plan to the Maine source file. The planned display separates a simple summary-finding table, representative examples, and the technical appendix. The current snapshot is framed as coverage and examples only, not a causal or merits conclusion, because same-cycle non-RCV rows and additional pre/post cycle rows remain unextracted.

**Profile-value update:** Added a per-election profile layer so ELEC-015 can compare elections rather than every municipal row or source-file datapoint. The profile layer defines provisional bands for competition, participation, RCV experience, and comparability confidence, then applies them to the extracted 2012 federal-primary baseline rows and 2026 RCV-primary rows.

**Event-table cleanup update:** Reorganized the Maine source file around the user's stated goal: a user-friendly table comparing candidate participation, voter turnout, and directly relevant RCV experience values for every election event since 2012. The comparison unit is now the election event, not individual primaries. Technical contest profiles, RCV activation notes, archive coverage, extraction roadmap, and current limits are separated into purpose-labeled sections below the event table.

**Maine data-harvest update:** Harvested official Maine Secretary of State result-file values for the principal regular primary and RCV general-election comparator events now visible in the source table. The event table now includes reduced candidate-count and ballots-cast ranges for 2014, 2016, 2018, 2020, 2022, 2024, and 2026, plus a harvested-values table preserving the extracted contest set behind each event. RCV activation/ballot-exhaustion values were added for 2018 Democratic Governor, 2018 Democratic CD-2 primary, 2018 CD-2 general, 2020 Republican CD-2 primary, 2022 State Senate District 16 primary, 2022 CD-2 general, and the 2026 CD-2/Governor/State Senate District 4/House District 58 RCV contests. The 2024 CD-2 general first-choice workbook is extracted, but the summary PDF still needs OCR or manual verification before round/exhaustion values are added.

**Presentation correction:** Reduced the Maine source-development page to the user's requested four-column table only: election name, RCV status, candidate participation, and voter turnout. Removed the extra reader-facing scaffolding, harvested-values table, RCV-experience table, archive notes, roadmap, and limits from the page because they obscured the intended comparison.

**Score effect:** No score change and no audit-count increment. ELEC-015 remains a candidate fixed at 0/100 pending broader Maine/Alaska/D.C. source development, remedy selection, and draft proposal text.

### 2026-07-09 — Development Note: Candidate-and-Voter-Participation Comparative Analysis

**Status:** Development note only; no audit run.

**Scope:** Reoriented ELEC-015 from immediate remedy selection toward candidate-and-voter-participation comparative analysis of Maine, Alaska, and D.C. before any model act, federal pilot bill, technical standard, or other proposal vehicle is selected.

**Source-development effect:** The next source-development pass should first examine candidate participation and voter participation as separate but related measures. Candidate measures should include field size, independent or minor-party candidates, intra-party challengers, uncontested races, withdrawals or consolidation, and campaign incentives where official records permit. Voter measures should include turnout, primary participation, ballot completion, ballot exhaustion, invalid or spoiled ballots, and comparable before/after participation measures where official data permits. Maine should be used for operational maturity, with separate attention to state-level RCV primaries and federal-office RCV general elections; Alaska should be used for top-four/RCV political-system interaction and repeal pressure; and D.C. should be used for voter-approved adoption and implementation-transition analysis.

**Score effect:** No score change and no audit-count increment. ELEC-015 remains a candidate fixed at 0/100 pending source development, remedy selection, and draft proposal text.

### 2026-07-06 — Boundary split / issue creation

**Audit tier:** Boundary split and issue-scope refinement

**Audit status:** Initial branch-off complete; candidate fixed-zero pending remedy selection and draft proposal

**Proposal-quality score:** 0/100 (Fixed-zero; drafting pending)

**Scope:** Created ELEC-015 to receive ranked-choice voting, runoff, and majority-choice election-method material previously carried inside ELEC-013. Reviewed ELEC-013's T1/T2 audit history, Election area boundary note, source inventory rows for HOR-014/ELEC-013, and the existing source base for Maine RCV implementation, NCSL RCV state-law mapping, D.C. Initiative 83, Alaska repeal-pressure routing, H.R. 4632, and H.Res. 20.

**Boundary finding:** The RCV and majority-choice material is distinct enough to warrant its own ELEC issue. ELEC-013 should focus on federal candidate-access, debate, ballot-access, and FEC-facing election-competition rules. ELEC-015 should own ranked-choice voting, runoffs, majority-choice election-method design, implementation safeguards, transparency, recounts, costs, and state-law adoption or prohibition trends.

**Source-development finding:** The inherited source base is adequate for candidate admission and initial issue framing, but not for a scored proposal. Future development should replace or supplement broad routing sources with state statutory text, official implementation reports, cost data, equipment-certification materials, accessibility records, official certified result files, recount records, repeal-measure records, litigation materials, and stakeholder or election-administrator evidence.

**Remedy-status finding:** No least-complex adequate remedy is selected yet. Plausible vehicles include a model-state RCV/runoff implementation act, optional federal pilot grants and technical assistance, a combined model-state/federal-support package, or a narrower source-development memorandum before drafting.

**Score effect:** Score is fixed at 0/100. ELEC-015 has no legislative text, model-state act, technical standard, federal pilot-grant bill, cost estimate, constitutional authority map, or implementation record sufficient for formula scoring.

**Corrections made:** Created the ELEC-015 issue page and audit sidecar; assigned RCV and majority-choice ownership to ELEC-015; preserved adjacent links to ELEC-013, ELEC-009, and ELEC-011; marked the issue as candidate fixed-zero; and set the next audit to begin with the no-draft preflight notice before any source-development or remedy-selection work.

**Unresolved findings:** T1 should source-develop state statutory text; current state-law prohibitions and pending repeal measures; Maine implementation, cost, tabulation, recount, accessibility, and results records; D.C. Initiative 83 official text, certified result records, funding, implementation schedule, and litigation or Council materials; Alaska final official repeal-result details, recount materials, and 2026 repeal-measure materials; federal authority for pilot grants and technical assistance; HAVA/EAC equipment implications; voter-comprehension evidence; and administrative cost analogues.

**Audit process feedback:** This entry is a boundary split, not a merits audit. The score should remain fixed-zero until the project drafts a concrete vehicle and then audits that text under the current rubric.
