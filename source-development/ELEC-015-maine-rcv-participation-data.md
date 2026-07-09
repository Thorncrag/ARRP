---
title: "ELEC-015 Maine RCV Participation Data"
source_issue: "../areas/ELEC/issues/ELEC-015.md"
jurisdiction: Maine
print_levels:
  - full-technical
---

# ELEC-015 Maine RCV Participation Data

This file is the working source-development table for Maine candidate-participation and voter-participation evidence relevant to [ELEC-015](../areas/ELEC/issues/ELEC-015.md). It should collect official Maine Secretary of State data before any remedy is selected.

## Scope Notes

- Maine's Secretary of State states that Maine uses ranked-choice voting for all state-level primary elections and, in general elections, only for federal offices, including President.
- Maine's Secretary of State also states that ranked-choice rounds are used only in races with more than two candidates.
- Maine therefore provides two distinct comparison surfaces for ELEC-015: state-level RCV primaries and federal-office RCV general elections.
- This file starts with official 2026 primary materials because they are the current official dataset visible on Maine's Election Results/Data page.

## Official Data Sources

| Source | Use for ELEC-015 | Notes |
| --- | --- | --- |
| Maine Secretary of State, [Ranked-Choice Voting Frequently Asked Questions](https://www.maine.gov/sos/elections-voting/ranked-choice-voting-frequently-asked-questions) | Election-type scope; implementation baseline | Confirms state-level primaries and federal-office general elections; confirms RCV tabulation only for races with more than two candidates. |
| Maine Secretary of State, [Election Results/Data](https://www.maine.gov/sos/elections-voting/election-results-data) | Current official result-file inventory | Lists 2026 primary ranked-choice offices, first-choice files, summary reports, cast-vote records, non-RCV offices, and candidate/withdrawal files. |
| Maine Secretary of State, [Previous Election Year Results](https://www.maine.gov/sos/elections-voting/election-results-data/previous-election-results) | Before/after and longer-run comparison inventory | Lists prior RCV and non-RCV result groups for 2018, 2020, 2022, 2024, and other years. |

## Core Comparison Model

ELEC-015 should start with a narrow participation comparison rather than an outcome analysis. The core table should identify the election, whether it used ranked-choice voting, the number of candidates, and voter turnout or ballots cast. Party is part of the election description when the contest is a primary, but the first-pass comparison does not need a separate party-by-party analytic breakdown.

Outcome should not be a core field. It should be added only where it explains comparability, salience, or whether ranked-choice tabulation actually affected the voter experience.

| Election referenced | Office / contest | RCV status | Number of candidates | Voter turnout / ballots cast | Comparator note |
| --- | --- | --- | ---: | ---: | --- |
| 2026-06-09 primary | Democratic Representative to Congress, District 2 | RCV | 4 | 83,480 | Same-cycle federal primary; compare cautiously to non-RCV U.S. House contests because only the Democratic CD-2 primary required RCV tabulation. |
| 2026-06-09 primary | Democratic Governor | RCV | 5 | 222,405 | Statewide primary; useful for candidate-field and voter-participation comparison against Republican Governor and prior gubernatorial primaries. |
| 2026-06-09 primary | Republican Governor | RCV | 8 | 137,981 | Statewide primary; useful for candidate-field comparison and for testing whether large fields correlate with ballot exhaustion or completion problems. |
| 2026-06-09 primary | Republican Senate District 4 | RCV | TBD | TBD | Maine SOS posts summary/CVR files; extraction pending. District-level comparability limits should be noted. |
| 2026-06-09 primary | Republican House District 58 | RCV | TBD | TBD | Maine SOS posts summary/CVR files; extraction pending. District-level comparability limits should be noted. |
| 2026-06-09 primary | U.S. Senate primaries | Non-RCV | TBD | TBD | Same-election non-RCV comparator; parse candidate and turnout fields from Maine SOS Excel files. |
| 2026-06-09 primary | Representative to Congress, District 1 primaries | Non-RCV | TBD | TBD | Same-election non-RCV comparator for federal House primary participation. |
| 2026-06-09 primary | Republican Representative to Congress, District 2 | Non-RCV | TBD | TBD | Same district and election date as Democratic CD-2 RCV contest, but party and competitiveness may differ. |
| 2026-06-09 primary | State Senate primaries | Non-RCV | TBD | TBD | Same-election state-legislative comparator group; should be normalized by district and contest status. |
| 2026-06-09 primary | Representative to the Legislature primaries | Non-RCV | TBD | TBD | Same-election state-legislative comparator group; useful for uncontested-race and field-size baselines. |

Maine's 2026 Election Results/Data page separately lists non-ranked-choice primary offices, including U.S. Senate, Representative to Congress District 1, Republican Representative to Congress District 2, State Senate, Representative to the Legislature, and county offices. Those files are useful as same-election non-RCV comparators, but they should be handled carefully because contest salience, district geography, candidate field size, and office type differ.

## RCV Activation and Ballot-Experience Context

This secondary table is for voter-experience context only. It should not displace the main participation comparison. Rounds and exhaustion matter because an RCV election with no transfer rounds is different from an RCV election where voters experience multiple elimination rounds.

| Election referenced | RCV tabulation activated? | Rounds | Exhausted ballots in first reported RCV round | Final-round exhausted ballots | Why it matters |
| --- | --- | ---: | ---: | ---: | --- |
| 2026-06-09 Democratic Representative to Congress, District 2 primary | Yes | 3 | 4,675 | 15,001 | Shows a four-candidate federal primary where ballot exhaustion becomes material by the final round. |
| 2026-06-09 Democratic Governor primary | Yes | 4 | 4,658 | 23,705 | Shows a five-candidate statewide primary where multiple rounds were needed. |
| 2026-06-09 Republican Governor primary | Yes | 7 | 8,574 | 38,609 | Shows a large-field statewide primary and therefore a useful stress test for ranking depth and ballot completion. |
| 2026-06-09 Republican Senate District 4 primary | TBD | TBD | TBD | TBD | Maine SOS posts summary/CVR files; extraction pending. |
| 2026-06-09 Republican House District 58 primary | TBD | TBD | TBD | TBD | Maine SOS posts summary/CVR files; extraction pending. |

## Candidate-Participation Variables To Extract

| Variable | Maine source path | Extraction status |
| --- | --- | --- |
| Candidate list by office and party | 2026 Primary Candidate List on Maine SOS Election Results/Data page | Not yet parsed. |
| Withdrawals and replacement nominations | 2026 Primary Candidate Withdrawals and Replacement Candidate Nominations on Maine SOS Election Results/Data page | Not yet parsed. |
| RCV contest field size | RCV summary reports and candidate list | Partially extracted for three statewide/congressional summaries; legislative-district summaries still need extraction. |
| Non-RCV comparator field size | 2026 non-ranked-choice office result files | Not yet parsed. |
| Prior-cycle field size | Previous Election Year Results page and linked prior-year files | Inventory identified; not yet parsed. |

## Voter-Participation Variables To Extract

| Variable | Maine source path | Extraction status |
| --- | --- | --- |
| First-choice votes by contest and candidate | RCV Central Count first-choice Excel files | Not yet parsed from Excel; summary PDFs provide candidate vote totals for initial tranche. |
| Round-by-round continuing votes | RCV Summary Report PDFs | Partially extracted for three summaries. |
| Exhausted ballots by round | RCV Summary Report PDFs | Partially extracted for three summaries. |
| Ballot completion / ranking depth | Cast Vote Record Excel files | Not yet parsed. |
| Overvotes, undervotes, invalid/spoiled patterns | CVRs and RCV glossary/rules where available | Not yet parsed; source definitions available. |
| Same-election non-RCV turnout comparator | Non-ranked-choice office Excel files | Not yet parsed. |
| Prior-cycle turnout comparator | Previous Election Year Results page and linked prior-year files | Inventory identified; not yet parsed. |

## Next Extraction Pass

1. Download and parse the 2026 Primary Candidate List and withdrawal/replacement file.
2. Extract all five 2026 RCV summary reports, including Senate District 4 and House District 58.
3. Parse first-choice Excel files and reconcile them to the summary PDFs.
4. Parse CVR files for ranking-depth, undervote/overvote, and ballot-exhaustion patterns.
5. Build same-election non-RCV comparator tables from the 2026 non-ranked-choice office files.
6. Extend backward through 2024, 2022, 2020, and 2018 prior-year result pages for before/after candidate-field and participation comparisons.

## Current Limits

- This file does not yet determine whether RCV increased or decreased candidate participation or voter participation.
- The extracted summary-report values should be treated as official initial observations, not as a causal conclusion.
- Same-election and prior-cycle comparisons need normalization by office type, district, party, competitiveness, presidential-cycle effects, ballot questions, and candidate salience.
