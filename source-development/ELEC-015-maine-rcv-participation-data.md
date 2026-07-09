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

## 2026 Primary: Ranked-Choice Office Inventory

Maine's 2026 Election Results/Data page identifies the June 9, 2026 primary ranked-choice offices and provides first-choice, summary-report, and cast-vote-record files for each office where posted.

| Date | Election | Office / contest | Party | Data files posted by Maine SOS | Candidate-participation use | Voter-participation use |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-06-09 | Primary | Representative to Congress, District 2 | Democratic | First-choice Excel; RCV Summary Report PDF; cast-vote-record Excel files | Field size and withdrawal/replacement context | First-choice totals, round transfers, exhausted ballots, ballot-completion analysis from CVRs |
| 2026-06-09 | Primary | Governor | Democratic | First-choice Excel; RCV Summary Report PDF; cast-vote-record Excel files | Field size and withdrawal/replacement context | First-choice totals, round transfers, exhausted ballots, ballot-completion analysis from CVRs |
| 2026-06-09 | Primary | Governor | Republican | First-choice Excel; RCV Summary Report PDF; cast-vote-record Excel files | Field size and withdrawal/replacement context | First-choice totals, round transfers, exhausted ballots, ballot-completion analysis from CVRs |
| 2026-06-09 | Primary | Senate District 4 | Republican | First-choice Excel; RCV Summary Report PDF; cast-vote-record Excel files | Field size and withdrawal/replacement context | First-choice totals, round transfers, exhausted ballots, ballot-completion analysis from CVRs |
| 2026-06-09 | Primary | House District 58 | Republican | First-choice Excel; RCV Summary Report PDF; cast-vote-record Excel files | Field size and withdrawal/replacement context | First-choice totals, round transfers, exhausted ballots, ballot-completion analysis from CVRs |

Maine's same 2026 page separately lists non-ranked-choice primary offices, including U.S. Senate, Representative to Congress District 1, Republican Representative to Congress District 2, State Senate, Representative to the Legislature, and county offices. Those files are useful as same-election non-RCV comparators, but they should be handled carefully because contest salience, district geography, candidate field size, and office type differ.

## Extracted 2026 RCV Summary Measures

These entries are initial extraction notes from official Maine RCV summary reports. They are not yet a full turnout model because CVR and non-RCV comparator files have not been parsed.

| Date | Contest | Candidates shown in summary | Rounds | Winner | Summary threshold | Round 1 candidate votes | Round 1 exhausted ballots | Final-round exhausted ballots | Initial extraction notes |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |
| 2026-06-09 | Democratic Representative to Congress, District 2 | 4 | 3 | Matthew G. Dunlap | 34,240 | 78,805 | 4,675 | 15,001 | Final round: Dunlap 35,924; Joseph M. Baldacci 32,555. Eliminated candidates: Paige Loud; Jordan Wood. |
| 2026-06-09 | Democratic Governor | 5 | 4 | Hannah M. Pingree | 99,351 | 217,747 | 4,658 | 23,705 | Final round: Pingree 111,750; Nirav D. Shah 86,950. Eliminated candidates: Angus King III; Shenna Bellows; Troy Dale Jackson. |
| 2026-06-09 | Republican Governor | 8 | 7 | Robert B. Charles | 49,687 | 129,407 | 8,574 | 38,609 | Final round: Charles 59,873; Benjamin T. Midgley 39,499. Eliminated candidates: James D. Libby; Robert J. Wessels; David J. Jones; Owen Z. McCarthy; Garrett Paul Mason; Jonathan J. Bush. |

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
