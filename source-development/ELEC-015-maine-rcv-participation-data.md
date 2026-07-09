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
- For trend analysis, treat 2018 as the operational launch/transition year because Maine first used RCV in the June 12, 2018 primary election. Use 2010-2017 as the eight-year pre-RCV baseline and 2019-2026 as the eight-year post-launch/current comparison window.

## Official Data Sources

| Source | Use for ELEC-015 | Notes |
| --- | --- | --- |
| Maine Secretary of State, [Ranked-Choice Voting Frequently Asked Questions](https://www.maine.gov/sos/elections-voting/ranked-choice-voting-frequently-asked-questions) | Election-type scope; implementation baseline | Confirms state-level primaries and federal-office general elections; confirms RCV tabulation only for races with more than two candidates. |
| Maine Secretary of State, [Election Results/Data](https://www.maine.gov/sos/elections-voting/election-results-data) | Current official result-file inventory | Lists 2026 primary ranked-choice offices, first-choice files, summary reports, cast-vote records, non-RCV offices, and candidate/withdrawal files. |
| Maine Secretary of State, [Previous Election Year Results](https://www.maine.gov/sos/elections-voting/election-results-data/previous-election-results) | Before/after and longer-run comparison inventory | Lists prior RCV and non-RCV result groups for 2018, 2020, 2022, 2024, and other years. |

## Pre-RCV Archive Feasibility

Maine's official previous-results page appears sufficient for a usable pre-RCV baseline, but file depth and format vary by year. The first extraction priority should be even-year regular elections because they provide the strongest comparisons to post-launch federal and state cycles.

| Year | Window role | Official archive coverage observed | Usefulness for ELEC-015 |
| --- | --- | --- | --- |
| 2010 | Pre-RCV baseline | General and referendum election files; U.S. Congress TXT, Governor PDF, State Senate TXT, State Representative TXT, county-office TXT files. | Useful for general-election candidate-count and vote-total baseline; primary baseline is not as visible on the current archive page. |
| 2011 | Pre-RCV baseline | Referendum, special election, county referendum, and county-office Excel files. | Context only; not a regular statewide candidate-participation comparator. |
| 2012 | Pre-RCV baseline | Strongest old-cycle primary archive found so far: primary total-votes files by party plus TXT/XLS tabulations for U.S. Senate, U.S. House, State Senate, State Representative, and county offices; general-election federal/state/county files also posted. | High-value baseline year. Candidate counts and ballots cast are extractable from official pipe-delimited TXT files without spreadsheet tooling. |
| 2013 | Pre-RCV baseline | Referendum and special-election files. | Context only; not a regular statewide candidate-participation comparator. |
| 2014 | Pre-RCV baseline | General/referendum and primary-election result groups listed. | High-value baseline year; extraction pending. |
| 2015 | Pre-RCV baseline | Referendum and special-election files. | Context only; not a regular statewide candidate-participation comparator. |
| 2016 | Pre-RCV baseline | General/referendum and primary-election result groups listed. | High-value baseline year; extraction pending. |
| 2017 | Pre-RCV baseline | Referendum and special-election files. | Context only; not a regular statewide candidate-participation comparator. |

## Core Comparison Model

ELEC-015 should start with a narrow participation comparison rather than an outcome analysis. The core table should identify the election, whether it used ranked-choice voting, the number of candidates, and voter turnout or ballots cast. Party is part of the election description when the contest is a primary, but the first-pass comparison does not need a separate party-by-party analytic breakdown.

Outcome should not be a core field. It should be added only where it explains comparability, salience, or whether ranked-choice tabulation actually affected the voter experience.

| Election referenced | Timeframe role | Office / contest | RCV status | Number of candidates | Voter turnout / ballots cast | Comparator note |
| --- | --- | --- | --- | ---: | ---: | --- |
| 2012-06-12 primary | Pre-RCV baseline | Democratic U.S. Senate | Non-RCV | 4 | 60,412 | Extracted from Maine SOS pipe-delimited TXT; candidate count excludes BLANK. Strong pre-RCV federal primary baseline. |
| 2012-06-12 primary | Pre-RCV baseline | Republican U.S. Senate | Non-RCV | 7 | 73,503 | Extracted from Maine SOS pipe-delimited TXT; candidate count excludes BLANK. Strong pre-RCV federal primary baseline. |
| 2012-06-12 primary | Pre-RCV baseline | Democratic Representative to Congress, District 1 | Non-RCV | 1 | 60,515 | Extracted from Maine SOS pipe-delimited TXT; candidate count excludes BLANK. Useful uncontested/incumbent-style baseline. |
| 2012-06-12 primary | Pre-RCV baseline | Republican Representative to Congress, District 1 | Non-RCV | 2 | 37,174 | Extracted from Maine SOS pipe-delimited TXT; candidate count excludes BLANK. |
| 2012-06-12 primary | Pre-RCV baseline | Democratic Representative to Congress, District 2 | Non-RCV | 1 | 24,712 | Extracted from Maine SOS pipe-delimited TXT; candidate count excludes BLANK. Useful uncontested/incumbent-style baseline. |
| 2012-06-12 primary | Pre-RCV baseline | Republican Representative to Congress, District 2 | Non-RCV | 2 | 36,392 | Extracted from Maine SOS pipe-delimited TXT; candidate count excludes BLANK. |
| 2026-06-09 primary | Post-launch/current window | Democratic Representative to Congress, District 2 | RCV | 4 | 83,480 | Same-cycle federal primary; compare cautiously to non-RCV U.S. House contests because only the Democratic CD-2 primary required RCV tabulation. |
| 2026-06-09 primary | Post-launch/current window | Democratic Governor | RCV | 5 | 222,405 | Statewide primary; useful for candidate-field and voter-participation comparison against Republican Governor and prior gubernatorial primaries. |
| 2026-06-09 primary | Post-launch/current window | Republican Governor | RCV | 8 | 137,981 | Statewide primary; useful for candidate-field comparison and for testing whether large fields correlate with ballot exhaustion or completion problems. |
| 2026-06-09 primary | Post-launch/current window | Republican Senate District 4 | RCV | TBD | TBD | Maine SOS posts summary/CVR files; extraction pending. District-level comparability limits should be noted. |
| 2026-06-09 primary | Post-launch/current window | Republican House District 58 | RCV | TBD | TBD | Maine SOS posts summary/CVR files; extraction pending. District-level comparability limits should be noted. |
| 2026-06-09 primary | Same-cycle non-RCV comparator | U.S. Senate primaries | Non-RCV | TBD | TBD | Same-election non-RCV comparator; parse candidate and turnout fields from Maine SOS Excel files. |
| 2026-06-09 primary | Same-cycle non-RCV comparator | Representative to Congress, District 1 primaries | Non-RCV | TBD | TBD | Same-election non-RCV comparator for federal House primary participation. |
| 2026-06-09 primary | Same-cycle non-RCV comparator | Republican Representative to Congress, District 2 | Non-RCV | TBD | TBD | Same district and election date as Democratic CD-2 RCV contest, but party and competitiveness may differ. |
| 2026-06-09 primary | Same-cycle non-RCV comparator | State Senate primaries | Non-RCV | TBD | TBD | Same-election state-legislative comparator group; should be normalized by district and contest status. |
| 2026-06-09 primary | Same-cycle non-RCV comparator | Representative to the Legislature primaries | Non-RCV | TBD | TBD | Same-election state-legislative comparator group; useful for uncontested-race and field-size baselines. |

## Trend and Comparator Windows

| Window | Years | Role in ELEC-015 | Notes |
| --- | --- | --- | --- |
| Pre-RCV baseline | 2010-2017 | Establish candidate-count and turnout trends before Maine's operational RCV launch. | The eight-year window precedes first operational use in 2018. Rows should be grouped by comparable office class rather than blended into one statewide trend. |
| Launch / transition year | 2018 | Keep separate from the main before/after comparison. | Maine first used RCV in the June 12, 2018 primary election; early implementation effects may differ from mature-use effects. |
| Post-launch/current window | 2019-2026 | Compare against the eight-year pre-RCV baseline. | This window captures current RCV-era practice while avoiding the launch year as the starting point. |
| Same-cycle comparator | Any year in scope | Compare RCV contests against non-RCV contests held in the same election cycle. | Useful for controlling broad turnout environment, but still requires office, district, salience, candidate-field, and competitiveness cautions. |

Maine's 2026 Election Results/Data page separately lists non-ranked-choice primary offices, including U.S. Senate, Representative to Congress District 1, Republican Representative to Congress District 2, State Senate, Representative to the Legislature, and county offices. Those files are useful as same-election non-RCV comparators, but they should be handled carefully because contest salience, district geography, candidate field size, and office type differ.

## Per-Election Profile Values

The core comparison unit should be one election profile, not every municipal row, candidate subtotal, or cast-vote-record line. The raw files support the profile; the profile is what ELEC-015 should compare.

### Profile Band Rules

These bands are deliberately simple and provisional. They should be revised only if later extraction shows they distort the Maine record.

| Field | Values | Rule |
| --- | --- | --- |
| Competition band | Uncontested; Contested; Crowded; Very crowded | 1 candidate = Uncontested; 2 candidates = Contested; 3-5 candidates = Crowded; 6+ candidates = Very crowded. |
| Participation band | Unknown; Low; Typical; High | Assign only within a comparable office class after enough rows exist. Until then use Unknown. |
| RCV experience band | Non-RCV; RCV not activated; RCV activated; RCV high-exhaustion | Non-RCV for plurality contests; RCV activated when transfer rounds occur; high-exhaustion when final exhausted ballots appear material enough to require explanation. |
| Comparability confidence | Low; Medium; High | Low until the same office class has multiple pre/post rows or a same-cycle comparator; Medium when a plausible comparator exists; High only after comparable pre/post and same-cycle rows are extracted. |

### Current Election Profiles

| Election profile | Window | Office class | RCV status | Candidates | Ballots cast | Competition band | Participation band | RCV experience band | Comparability confidence | Profile note |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 2012 Democratic U.S. Senate primary | Pre-RCV baseline | Federal statewide primary | Non-RCV | 4 | 60,412 | Crowded | Unknown | Non-RCV | Low | Useful baseline row, but needs 2014/2016 and post-launch Senate-primary comparators. |
| 2012 Republican U.S. Senate primary | Pre-RCV baseline | Federal statewide primary | Non-RCV | 7 | 73,503 | Very crowded | Unknown | Non-RCV | Low | Useful large-field baseline row before RCV. |
| 2012 Democratic CD-1 primary | Pre-RCV baseline | Federal House primary | Non-RCV | 1 | 60,515 | Uncontested | Unknown | Non-RCV | Low | Useful uncontested federal House primary baseline. |
| 2012 Republican CD-1 primary | Pre-RCV baseline | Federal House primary | Non-RCV | 2 | 37,174 | Contested | Unknown | Non-RCV | Low | Useful contested federal House primary baseline. |
| 2012 Democratic CD-2 primary | Pre-RCV baseline | Federal House primary | Non-RCV | 1 | 24,712 | Uncontested | Unknown | Non-RCV | Medium | Closest extracted pre-RCV comparator to the 2026 Democratic CD-2 RCV row, but more years are needed. |
| 2012 Republican CD-2 primary | Pre-RCV baseline | Federal House primary | Non-RCV | 2 | 36,392 | Contested | Unknown | Non-RCV | Low | Useful same-district pre-RCV baseline row. |
| 2026 Democratic CD-2 primary | Post-launch/current window | Federal House primary | RCV | 4 | 83,480 | Crowded | Unknown | RCV high-exhaustion | Medium | Same district as extracted 2012 CD-2 rows; comparison remains incomplete until intervening cycles and same-cycle non-RCV rows are extracted. |
| 2026 Democratic Governor primary | Post-launch/current window | Statewide primary | RCV | 5 | 222,405 | Crowded | Unknown | RCV activated | Low | Statewide RCV row; needs gubernatorial primary pre-RCV and same-cycle Republican/non-RCV context. |
| 2026 Republican Governor primary | Post-launch/current window | Statewide primary | RCV | 8 | 137,981 | Very crowded | Unknown | RCV high-exhaustion | Low | Large-field statewide RCV row; useful stress test, but not yet comparable enough for participation claims. |

## Reader-Facing Presentation Plan

The public-facing ELEC-015 discussion should not reproduce every municipal or CVR row. Use a three-layer presentation:

1. **Summary finding table:** one row per comparable office class and timeframe window, showing the range or average of candidate counts and ballots cast once enough rows are extracted.
2. **Representative examples:** a small table of named elections that illustrate the pattern without claiming causation.
3. **Technical appendix:** the core comparison table in this file, plus extraction notes and source-file links.

For now, the safest reader-facing display is a "coverage and examples" table rather than a conclusion table. It should show that Maine's data can support the comparison, while making clear that extraction is incomplete.

| Display question | Simple presentation | Current status |
| --- | --- | --- |
| Do we have pre-RCV data? | Coverage table by year, with strong/partial/context labels. | Started in the Pre-RCV Archive Feasibility table. |
| Did candidate fields change? | Compare candidate-count ranges by office class: federal primaries, state primaries, federal general elections, and same-cycle non-RCV contests. | Started with 2012 federal primary baseline and 2026 RCV primary examples. |
| Did voter participation change? | Compare ballots cast by comparable office class and cycle type, not one blended statewide line. | Started with 2012 federal primary baseline and 2026 RCV primary examples. |
| Did RCV change the voter experience? | Separate ballot-experience table: RCV activated, rounds, exhausted ballots, and later ranking-depth/CVR measures. | Started for three 2026 RCV summaries; CVR parsing pending. |

## First Reader-Facing Snapshot

This table is a presentation scaffold only. It should not be treated as a conclusion until 2014, 2016, 2020, 2022, and 2024 rows are added and comparable office classes are separated.

| Window | Example elections currently extracted | Candidate-count signal | Ballots-cast signal | What the reader can take from this now |
| --- | --- | --- | --- | --- |
| Pre-RCV baseline | 2012 Democratic/Republican U.S. Senate primaries; 2012 Democratic/Republican CD-1 and CD-2 primaries | 1 to 7 candidates across extracted federal primaries | 24,712 to 73,503 ballots cast across extracted federal primaries | Maine's pre-RCV archive can support candidate-count and ballots-cast comparisons, at least for 2012 federal primaries. |
| Launch / transition | 2018 RCV and non-RCV result groups identified, not yet extracted | TBD | TBD | Keep 2018 separate until early implementation effects are understood. |
| Post-launch/current | 2026 Democratic CD-2, Democratic Governor, Republican Governor RCV primaries | 4 to 8 candidates across extracted RCV primaries | 83,480 to 222,405 ballots cast across extracted RCV primaries | Current RCV summaries provide candidate counts and ballots-cast measures, but comparisons need office-class controls. |
| Same-cycle comparator | 2026 non-RCV primary groups identified, not yet extracted | TBD | TBD | Same-cycle non-RCV rows are needed before any participation claim is responsible. |

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
6. Extend backward through 2024, 2022, 2020, and 2018 prior-year result pages for post-launch candidate-field and participation comparisons.
7. Extract the high-value pre-RCV baseline years 2016, 2014, 2012, and 2010, prioritizing regular even-year primary and general elections over odd-year special or referendum elections.
8. Treat odd-year files from 2011, 2013, 2015, and 2017 as context unless a specific special-election comparison becomes useful.

## Current Limits

- This file does not yet determine whether RCV increased or decreased candidate participation or voter participation.
- The extracted summary-report values should be treated as official initial observations, not as a causal conclusion.
- Same-election and prior-cycle comparisons need normalization by office type, district, party, competitiveness, presidential-cycle effects, ballot questions, and candidate salience.
- Old Maine result formats vary. TXT files are immediately parseable; XLS/PDF files may require additional tooling or manual verification.
