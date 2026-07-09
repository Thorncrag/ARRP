---
title: "ELEC-015 Maine RCV Participation Data"
source_issue: "../areas/ELEC/issues/ELEC-015.md"
jurisdiction: Maine
print_levels:
  - full-technical
---

# ELEC-015 Maine RCV Participation Data

This file is the working source-development table for Maine candidate-participation and voter-participation evidence relevant to [ELEC-015](../areas/ELEC/issues/ELEC-015.md). It uses official Maine Secretary of State data to compare election events over time before selecting any remedy.

## Purpose and Reader Guide

This page has three jobs:

1. present a user-friendly election-event trend table from 2012 forward;
2. preserve the simple per-election values used for comparison; and
3. keep technical source and extraction notes separate from the reader-facing summary.

The comparison unit is the **election event**, not each individual primary, town, candidate subtotal, or cast-vote-record line. Individual contests remain in the technical profile table because they explain how each event-level value was built.

## Scope Notes

- Maine's Secretary of State states that Maine uses ranked-choice voting for all state-level primary elections and, in general elections, only for federal offices, including President.
- Maine's Secretary of State also states that ranked-choice rounds are used only in races with more than two candidates.
- Maine therefore provides two distinct comparison surfaces for ELEC-015: state-level RCV primaries and federal-office RCV general elections.
- For trend analysis, treat 2018 as the operational launch/transition year because Maine first used RCV in the June 12, 2018 primary election. Use 2010-2017 as the pre-RCV baseline and 2019-2026 as the post-launch/current comparison window.

## Official Data Sources

This section lists the official sources used to build the event table and technical profiles.

| Source | Use for ELEC-015 | Notes |
| --- | --- | --- |
| Maine Secretary of State, [Ranked-Choice Voting Frequently Asked Questions](https://www.maine.gov/sos/elections-voting/ranked-choice-voting-frequently-asked-questions) | Election-type scope; implementation baseline | Confirms state-level primaries and federal-office general elections; confirms RCV tabulation only for races with more than two candidates. |
| Maine Secretary of State, [Election Results/Data](https://www.maine.gov/sos/elections-voting/election-results-data) | Current official result-file inventory | Lists 2026 primary ranked-choice offices, first-choice files, summary reports, cast-vote records, non-RCV offices, and candidate/withdrawal files. |
| Maine Secretary of State, [Previous Election Year Results](https://www.maine.gov/sos/elections-voting/election-results-data/previous-election-results) | Trend inventory from 2012 forward | Lists prior election result groups and older TXT/XLS/PDF files used to build the baseline and post-launch windows. |

## Election-Event Trend Table

This is the main reader-facing table. It should eventually contain one row for every Maine election event from 2012 forward that is relevant to candidate participation, voter turnout, or RCV implementation. The current values are partial and should not be treated as conclusions.

| Election event | Window | RCV posture | Candidate-participation value | Voter-turnout value | Other directly relevant value | Extraction status | Reader note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2012-06-12 Primary Election | Pre-RCV baseline | Non-RCV | Federal primary contests extracted so far range from 1 to 7 candidates. | Extracted federal primary contests range from 24,712 to 73,503 ballots cast. | Official pipe-delimited TXT files support candidate counts and ballots-cast extraction without spreadsheet tooling. | Partial: federal U.S. Senate and U.S. House primary contests extracted; state-legislative and county files pending. | Strong baseline event. Use as proof that older Maine data can support trend analysis. |
| 2012-11-06 General Election | Pre-RCV baseline | Non-RCV | TBD | TBD | Official general-election files listed for federal, state, and county offices. | Inventory only. | Useful pre-RCV general-election baseline after extraction. |
| 2013 election events | Pre-RCV baseline context | Non-RCV | TBD | TBD | Mostly referendum and special-election files. | Inventory only. | Context only unless a special-election comparison becomes useful. |
| 2014 Primary Election | Pre-RCV baseline | Non-RCV | TBD | TBD | Official primary-election result group listed. | Inventory only. | High-value baseline event; extract next for regular-cycle trend. |
| 2014 General and Referendum Election | Pre-RCV baseline | Non-RCV | TBD | TBD | Official general/referendum result group listed. | Inventory only. | High-value general-election baseline event. |
| 2015 election events | Pre-RCV baseline context | Non-RCV | TBD | TBD | Mostly referendum and special-election files. | Inventory only. | Context only unless a special-election comparison becomes useful. |
| 2016 Primary Election | Pre-RCV baseline | Non-RCV | TBD | TBD | Official primary-election result group listed. | Inventory only. | High-value baseline event immediately before voter adoption and operational launch. |
| 2016 General and Referendum Election | Pre-RCV baseline | Non-RCV | TBD | TBD | Official general/referendum result group listed. | Inventory only. | High-value general-election baseline event. |
| 2017 election events | Pre-RCV baseline context | Non-RCV | TBD | TBD | Mostly referendum and special-election files. | Inventory only. | Context only unless a special-election comparison becomes useful. |
| 2018-06-12 Primary Election | Launch / transition | RCV and non-RCV | TBD | TBD | First operational RCV election in Maine; ranked-choice and non-ranked-choice primary result groups are listed. | Inventory only. | Keep separate from main before/after trend because it is the launch year. |
| 2018-11-06 General Election | Launch / transition | RCV and non-RCV | TBD | TBD | General-election ranked-choice and non-ranked-choice result groups are listed. | Inventory only. | Useful for launch-year implementation, but not the clean post-launch baseline. |
| 2019 election events | Post-launch/current context | Mostly non-RCV context | TBD | TBD | Referendum and special-election files. | Inventory only. | Context only unless a special-election comparison becomes useful. |
| 2020 Primary Election | Post-launch/current window | RCV and non-RCV | TBD | TBD | Ranked-choice and non-ranked-choice primary result groups listed. | Inventory only. | High-value post-launch primary event. |
| 2020 General Election | Post-launch/current window | RCV for federal offices; non-RCV for others | TBD | TBD | Presidential race included in RCV era after 2019 law. | Inventory only. | High-value post-launch general-election event. |
| 2021 election events | Post-launch/current context | Mostly non-RCV context | TBD | TBD | Referendum and special-election files. | Inventory only. | Context only unless a special-election comparison becomes useful. |
| 2022-06-14 Primary Election | Post-launch/current window | RCV and non-RCV | TBD | TBD | Ranked-choice State Senate District 16 and non-ranked-choice primary result groups listed. | Inventory only. | High-value post-launch primary event. |
| 2022-11-08 General Election | Post-launch/current window | RCV for CD-2; non-RCV for others | TBD | TBD | General-election ranked-choice CD-2 and non-ranked-choice result groups listed. | Inventory only. | High-value post-launch general-election event. |
| 2023 election events | Post-launch/current context | Mostly non-RCV context | TBD | TBD | Referendum election listed. | Inventory only. | Context only. |
| 2024 Primary Election | Post-launch/current window | RCV and non-RCV | TBD | TBD | State primary result group listed. | Inventory only. | High-value post-launch primary event. |
| 2024 General Election | Post-launch/current window | RCV for CD-2; non-RCV for others | TBD | TBD | General-election ranked-choice CD-2 and non-ranked-choice result groups listed. | Inventory only. | High-value post-launch general-election event. |
| 2025 election events | Post-launch/current context | Mostly non-RCV context | TBD | TBD | Referendum and special-election files. | Inventory only. | Context only. |
| 2026-06-09 Primary Election | Post-launch/current window | RCV and non-RCV | Extracted RCV contests currently range from 4 to 8 candidates. | Extracted RCV contests currently range from 83,480 to 222,405 ballots cast. | Three extracted RCV contests activated transfer rounds; two currently show high final exhausted-ballot counts. | Partial: Democratic CD-2, Democratic Governor, and Republican Governor RCV summaries extracted; legislative RCV and non-RCV comparators pending. | Current-cycle event that shows the type of post-launch data Maine publishes. |

## Event-Profile Method

This section explains how the election-event table turns contest-level source files into a readable comparison. The goal is to assign a few values to each election event without pretending that every contest is directly comparable.

| Field | Values | Rule |
| --- | --- | --- |
| Candidate participation value | Range, average, or narrative summary | Use candidate counts from extracted contests within the event. Do not blend office classes without saying so. |
| Voter-turnout value | Range, average, total, or narrative summary | Use ballots cast or turnout files from extracted contests. Prefer comparable office classes when available. |
| Competition band | Uncontested; Contested; Crowded; Very crowded | Contest-level band: 1 candidate = Uncontested; 2 candidates = Contested; 3-5 candidates = Crowded; 6+ candidates = Very crowded. |
| Participation band | Unknown; Low; Typical; High | Assign only after enough comparable events exist. Until then use Unknown. |
| RCV experience band | Non-RCV; RCV not activated; RCV activated; RCV high-exhaustion | Use only as a separate implementation/voter-experience value, not as a candidate-participation measure. |
| Comparability confidence | Low; Medium; High | Low until the same office class has multiple pre/post rows or a same-cycle comparator; Medium when a plausible comparator exists; High only after comparable pre/post and same-cycle rows are extracted. |

## Current Contest Profiles

This technical table preserves the contest-level profiles already extracted. These rows support the election-event trend table above.

| Election profile | Parent election event | Window | Office class | RCV status | Candidates | Ballots cast | Competition band | Participation band | RCV experience band | Comparability confidence | Profile note |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 2012 Democratic U.S. Senate primary | 2012-06-12 Primary Election | Pre-RCV baseline | Federal statewide primary | Non-RCV | 4 | 60,412 | Crowded | Unknown | Non-RCV | Low | Useful baseline row, but needs 2014/2016 and post-launch Senate-primary comparators. |
| 2012 Republican U.S. Senate primary | 2012-06-12 Primary Election | Pre-RCV baseline | Federal statewide primary | Non-RCV | 7 | 73,503 | Very crowded | Unknown | Non-RCV | Low | Useful large-field baseline row before RCV. |
| 2012 Democratic CD-1 primary | 2012-06-12 Primary Election | Pre-RCV baseline | Federal House primary | Non-RCV | 1 | 60,515 | Uncontested | Unknown | Non-RCV | Low | Useful uncontested federal House primary baseline. |
| 2012 Republican CD-1 primary | 2012-06-12 Primary Election | Pre-RCV baseline | Federal House primary | Non-RCV | 2 | 37,174 | Contested | Unknown | Non-RCV | Low | Useful contested federal House primary baseline. |
| 2012 Democratic CD-2 primary | 2012-06-12 Primary Election | Pre-RCV baseline | Federal House primary | Non-RCV | 1 | 24,712 | Uncontested | Unknown | Non-RCV | Medium | Closest extracted pre-RCV comparator to the 2026 Democratic CD-2 RCV row, but more years are needed. |
| 2012 Republican CD-2 primary | 2012-06-12 Primary Election | Pre-RCV baseline | Federal House primary | Non-RCV | 2 | 36,392 | Contested | Unknown | Non-RCV | Low | Useful same-district pre-RCV baseline row. |
| 2026 Democratic CD-2 primary | 2026-06-09 Primary Election | Post-launch/current window | Federal House primary | RCV | 4 | 83,480 | Crowded | Unknown | RCV high-exhaustion | Medium | Same district as extracted 2012 CD-2 rows; comparison remains incomplete until intervening cycles and same-cycle non-RCV rows are extracted. |
| 2026 Democratic Governor primary | 2026-06-09 Primary Election | Post-launch/current window | Statewide primary | RCV | 5 | 222,405 | Crowded | Unknown | RCV activated | Low | Statewide RCV row; needs gubernatorial primary pre-RCV and same-cycle Republican/non-RCV context. |
| 2026 Republican Governor primary | 2026-06-09 Primary Election | Post-launch/current window | Statewide primary | RCV | 8 | 137,981 | Very crowded | Unknown | RCV high-exhaustion | Low | Large-field statewide RCV row; useful stress test, but not yet comparable enough for participation claims. |

## RCV Activation and Ballot-Experience Context

This section exists only to track whether ranked-choice tabulation affected the voter experience. It should not be used as a substitute for candidate participation or turnout.

| Election referenced | Parent election event | RCV tabulation activated? | Rounds | Exhausted ballots in first reported RCV round | Final-round exhausted ballots | Why it matters |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 2026-06-09 Democratic Representative to Congress, District 2 primary | 2026-06-09 Primary Election | Yes | 3 | 4,675 | 15,001 | Shows a four-candidate federal primary where ballot exhaustion becomes material by the final round. |
| 2026-06-09 Democratic Governor primary | 2026-06-09 Primary Election | Yes | 4 | 4,658 | 23,705 | Shows a five-candidate statewide primary where multiple rounds were needed. |
| 2026-06-09 Republican Governor primary | 2026-06-09 Primary Election | Yes | 7 | 8,574 | 38,609 | Shows a large-field statewide primary and therefore a useful stress test for ranking depth and ballot completion. |
| 2026-06-09 Republican Senate District 4 primary | 2026-06-09 Primary Election | TBD | TBD | TBD | TBD | Maine SOS posts summary/CVR files; extraction pending. |
| 2026-06-09 Republican House District 58 primary | 2026-06-09 Primary Election | TBD | TBD | TBD | TBD | Maine SOS posts summary/CVR files; extraction pending. |

## Archive Coverage Notes

This section explains how much source coverage exists before deeper extraction. It is a routing table, not an analytical conclusion.

| Year | Window role | Official archive coverage observed | Usefulness for ELEC-015 |
| --- | --- | --- | --- |
| 2010 | Pre-RCV baseline | General and referendum election files; U.S. Congress TXT, Governor PDF, State Senate TXT, State Representative TXT, county-office TXT files. | Useful for general-election candidate-count and vote-total baseline; primary baseline is not as visible on the current archive page. |
| 2011 | Pre-RCV baseline | Referendum, special election, county referendum, and county-office Excel files. | Context only; not a regular statewide candidate-participation comparator. |
| 2012 | Pre-RCV baseline | Primary total-votes files by party plus TXT/XLS tabulations for U.S. Senate, U.S. House, State Senate, State Representative, and county offices; general-election federal/state/county files also posted. | High-value baseline year. Candidate counts and ballots cast are extractable from official pipe-delimited TXT files without spreadsheet tooling. |
| 2013 | Pre-RCV baseline | Referendum and special-election files. | Context only; not a regular statewide candidate-participation comparator. |
| 2014 | Pre-RCV baseline | General/referendum and primary-election result groups listed. | High-value baseline year; extraction pending. |
| 2015 | Pre-RCV baseline | Referendum and special-election files. | Context only; not a regular statewide candidate-participation comparator. |
| 2016 | Pre-RCV baseline | General/referendum and primary-election result groups listed. | High-value baseline year; extraction pending. |
| 2017 | Pre-RCV baseline | Referendum and special-election files. | Context only; not a regular statewide candidate-participation comparator. |

## Extraction Roadmap

This section lists the next work needed to fill the event-level trend table.

1. Extract 2014 and 2016 primary-election event values, prioritizing federal and statewide contests.
2. Extract 2018 launch-year values but keep them separate from the before/after comparison.
3. Extract 2020, 2022, and 2024 post-launch values for comparable federal and statewide election events.
4. Parse the 2026 non-RCV primary comparator groups so the 2026 event row does not rely only on RCV contests.
5. Parse 2026 legislative RCV summary reports for Senate District 4 and House District 58.
6. Add CVR-derived ranking-depth and ballot-completion measures only after event-level candidate/turnout values are stable.
7. Treat odd-year files from 2011, 2013, 2015, 2017, 2019, 2021, 2023, and 2025 as context unless a specific special-election comparison becomes useful.

## Current Limits

This section prevents the page from being over-read.

- This file does not yet determine whether RCV increased or decreased candidate participation or voter participation.
- The event-level values are incomplete and should be treated as a source-development scaffold.
- Same-election and prior-cycle comparisons need normalization by office type, district, party, competitiveness, presidential-cycle effects, ballot questions, and candidate salience.
- Old Maine result formats vary. TXT files are immediately parseable; XLS/PDF files may require additional tooling or manual verification.
