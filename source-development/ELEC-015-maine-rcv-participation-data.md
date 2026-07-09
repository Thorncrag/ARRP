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
| 2014-06-10 Primary Election | Pre-RCV baseline | Non-RCV | Extracted federal/statewide primary contests range from 1 to 2 candidates. | Extracted federal/statewide primary contests range from 25,416 to 65,085 ballots cast. | Official U.S. Senate, Governor, and U.S. House party-primary files provide a strong pre-RCV comparison set. | Extracted: federal/statewide primary set. | High-value baseline event; candidate fields were mostly uncontested or two-candidate contests in the extracted offices. |
| 2014 General and Referendum Election | Pre-RCV baseline | Non-RCV | TBD | TBD | Official general/referendum result group listed. | Inventory only. | High-value general-election baseline event. |
| 2015 election events | Pre-RCV baseline context | Non-RCV | TBD | TBD | Mostly referendum and special-election files. | Inventory only. | Context only unless a special-election comparison becomes useful. |
| 2016-06-14 Primary Election | Pre-RCV baseline | Non-RCV | Extracted U.S. House primary contests range from 1 to 2 candidates. | Extracted U.S. House primary contests range from 21,892 to 31,052 ballots cast. | Official CD-1 and CD-2 Democratic/Republican files provide the immediate pre-launch congressional baseline. | Extracted: federal House primary set. | High-value baseline event immediately before voter adoption and operational launch; no statewide Governor/U.S. Senate primary comparator existed in this extraction set. |
| 2016 General and Referendum Election | Pre-RCV baseline | Non-RCV | TBD | TBD | Official general/referendum result group listed. | Inventory only. | High-value general-election baseline event. |
| 2017 election events | Pre-RCV baseline context | Non-RCV | TBD | TBD | Mostly referendum and special-election files. | Inventory only. | Context only unless a special-election comparison becomes useful. |
| 2018-06-12 Primary Election | Launch / transition | RCV and non-RCV | Extracted federal/statewide primary contests range from 1 to 8 candidates. | Extracted federal/statewide primary contests range from 50,260 to 132,795 ballots cast. | First operational RCV election. Extracted RCV summaries show Democratic Governor and Democratic CD-2 activated transfers; final exhausted ballots were 15,000 and 7,381 respectively. | Extracted: federal/statewide primary set plus two RCV summaries. | Keep separate from main before/after trend because it is the launch year. |
| 2018-11-06 General Election | Launch / transition | RCV for CD-2; non-RCV for others | Extracted CD-2 RCV general had 4 candidates. | Extracted CD-2 RCV general had 296,077 ballots cast. | CD-2 RCV summary activated transfers over 2 rounds; final exhausted ballots were 14,706. | Partial: CD-2 RCV summary extracted; broader non-RCV general comparator files not yet reduced to event range. | Useful for launch-year federal-general implementation, but not the clean post-launch baseline. |
| 2019 election events | Post-launch/current context | Mostly non-RCV context | TBD | TBD | Referendum and special-election files. | Inventory only. | Context only unless a special-election comparison becomes useful. |
| 2020-07-14 Primary Election | Post-launch/current window | RCV and non-RCV | Extracted federal primary contests range from 1 to 3 candidates. | Extracted federal primary contests range from 40,493 to 173,292 ballots cast. | Republican CD-2 RCV summary activated transfers over 2 rounds; final exhausted ballots were 10,192. | Extracted: federal primary set plus CD-2 Republican RCV summary. | High-value post-launch primary event with both RCV and same-cycle non-RCV federal comparators. |
| 2020-11-03 General Election | Post-launch/current window | RCV for federal offices; non-RCV for others | Extracted presidential general file has 5 named candidates. | Extracted presidential general file has 828,305 ballots cast statewide; congressional-district subtotals are 447,981 in CD-1 and 380,324 in CD-2. | Presidential race included in RCV era after 2019 law; first-choice result files extracted, but round summary not yet reduced. | Partial: presidential first-choice files extracted; other federal general files pending. | High-value post-launch general-election event; distinguish first-choice turnout from RCV round experience until summary data is reduced. |
| 2021 election events | Post-launch/current context | Mostly non-RCV context | TBD | TBD | Referendum and special-election files. | Inventory only. | Context only unless a special-election comparison becomes useful. |
| 2022-06-14 Primary Election | Post-launch/current window | RCV and non-RCV | Extracted federal/statewide primary contests range from 1 to 2 candidates; extracted State Senate District 16 RCV contest had 3 candidates. | Extracted federal/statewide primary contests range from 27,231 to 74,311 ballots cast; extracted State Senate District 16 RCV contest had 1,979 ballots cast. | State Senate District 16 RCV summary activated transfers over 2 rounds; final exhausted ballots were 212. | Extracted: federal/statewide primary set plus State Senate District 16 RCV summary. | High-value post-launch primary event; district-level RCV row should be compared separately from statewide/federal contests. |
| 2022-11-08 General Election | Post-launch/current window | RCV for CD-2; non-RCV for others | Extracted CD-2 RCV general had 4 candidates, including write-in. | Extracted CD-2 RCV general had 322,778 ballots cast in the RCV summary. | CD-2 RCV summary activated transfers over 2 rounds; final exhausted ballots were 11,500. | Partial: CD-2 RCV summary extracted; broader non-RCV general comparator files not yet reduced to event range. | High-value post-launch general-election event for federal RCV voter-experience comparison. |
| 2023 election events | Post-launch/current context | Mostly non-RCV context | TBD | TBD | Referendum election listed. | Inventory only. | Context only. |
| 2024-03-05 Presidential Primary Election | Post-launch/current window | Non-RCV primary event | Extracted presidential party primaries range from 2 to 5 named candidates. | Extracted presidential party primaries range from 72,480 to 109,898 ballots cast. | Presidential-primary files provide a high-salience participation comparator, but not an RCV primary comparator. | Extracted: Democratic and Republican presidential-primary files. | Useful for turnout context; do not blend with June state primary without noting election type. |
| 2024-06-11 State Primary Election | Post-launch/current window | RCV and non-RCV | Extracted federal primary contests range from 1 to 2 candidates. | Extracted federal primary contests range from 25,131 to 74,872 ballots cast. | Official U.S. Senate and U.S. House party-primary files extracted. | Extracted: federal primary set. | High-value post-launch primary event; no extracted federal primary contest required RCV tabulation in this pass. |
| 2024-11-05 General Election | Post-launch/current window | RCV for federal offices; non-RCV for others | Extracted federal RCV-era general files show 5 presidential candidates statewide and 2 CD-2 candidates. | Extracted presidential general file has 842,447 ballots cast statewide; extracted CD-2 first-choice file has 402,936 ballots cast. | CD-2 RCV summary PDF is image-like in this pass; first-choice workbook is extracted, but round/exhaustion values need OCR or manual verification. | Partial: presidential first-choice and CD-2 first-choice files extracted. | High-value post-launch general-election event; keep first-choice participation separate from unresolved RCV round experience. |
| 2025 election events | Post-launch/current context | Mostly non-RCV context | TBD | TBD | Referendum and special-election files. | Inventory only. | Context only. |
| 2026-06-09 Primary Election | Post-launch/current window | RCV and non-RCV | Extracted federal/statewide and RCV district contests range from 1 to 8 candidates; extracted federal/statewide contests alone range from 1 to 8 candidates. | Extracted federal/statewide contests range from 61,270 to 222,405 ballots cast; extracted RCV district contests had 1,407 and 6,399 ballots cast. | Five extracted RCV summaries activated transfer rounds; final exhausted ballots range from 379 in House District 58 to 38,609 in the Republican Governor primary. | Extracted: five RCV summaries, federal non-RCV comparators, and core statewide/federal first-choice result files. | Current-cycle event now supports same-cycle RCV/non-RCV comparison, with district-level RCV contests kept separate from federal/statewide comparisons. |

## Harvested Event Values

This table summarizes what has been reduced from official result files so far. The values are event-level ranges, not conclusions about causation.

| Election event | Extracted contest set | Candidate-count range | Ballots-cast range | RCV experience captured | Source-file note |
| --- | --- | ---: | ---: | --- | --- |
| 2012-06-12 Primary Election | Federal primary contests: U.S. Senate and U.S. House party primaries | 1-7 | 24,712-73,503 | Non-RCV | Official pipe-delimited TXT files previously extracted. |
| 2014-06-10 Primary Election | U.S. Senate, Governor, and U.S. House party primaries | 1-2 | 25,416-65,085 | Non-RCV | Official XLS files; declared-write-in/other columns treated conservatively in event range. |
| 2016-06-14 Primary Election | U.S. House CD-1 and CD-2 party primaries | 1-2 | 21,892-31,052 | Non-RCV | Official XLSX files. |
| 2018-06-12 Primary Election | U.S. Senate, Governor, U.S. House, and RCV summaries for Democratic Governor and Democratic CD-2 | 1-8 | 50,260-132,795 | RCV activated in 2 extracted contests; final exhausted ballots 7,381 and 15,000 | Official XLS/XLSX summary and result files. |
| 2018-11-06 General Election | CD-2 RCV general summary | 4 | 296,077 | RCV activated; 2 rounds; final exhausted ballots 14,706 | Official XLS summary. |
| 2020-07-14 Primary Election | U.S. Senate, U.S. House, and Republican CD-2 RCV summary | 1-3 | 40,493-173,292 | RCV activated in Republican CD-2; final exhausted ballots 10,192 | Official XLS/XLSX summary and result files. |
| 2020-11-03 General Election | Presidential first-choice files | 5 | 828,305 statewide; 447,981 CD-1; 380,324 CD-2 | First-choice values extracted; round experience not yet reduced | Official XLSX files. |
| 2022-06-14 Primary Election | Governor, U.S. House, and State Senate District 16 RCV summary | 1-3 | 1,979-74,311 | RCV activated in State Senate District 16; final exhausted ballots 212 | Official XLS/XLSX summary and result files. |
| 2022-11-08 General Election | CD-2 RCV general summary | 4 | 322,778 | RCV activated; 2 rounds; final exhausted ballots 11,500 | Official PDF summary text extracted. |
| 2024-03-05 Presidential Primary Election | Democratic and Republican presidential primaries | 2-5 | 72,480-109,898 | Non-RCV primary event | Official XLSX files. |
| 2024-06-11 State Primary Election | U.S. Senate and U.S. House party primaries | 1-2 | 25,131-74,872 | No extracted RCV activation in federal primary set | Official XLSX files. |
| 2024-11-05 General Election | Presidential first-choice file and CD-2 first-choice workbook | 2-5 | 402,936-842,447 | CD-2 RCV summary not yet reduced; first-choice values extracted | Official XLSX first-choice files; CD-2 summary PDF needs OCR/manual verification. |
| 2026-06-09 Primary Election | U.S. Senate, U.S. House, Governor, CD-2 RCV, State Senate District 4 RCV, and House District 58 RCV | 1-8 | 1,407-222,405 | RCV activated in 5 extracted contests; final exhausted ballots 379-38,609 | Official XLSX/PDF summary and result files. |

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

This technical table preserves representative contest-level profiles. The harvested event table above is the controlling summary for the broader 2014-2026 extraction pass; not every harvested contest is expanded here.

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
| 2018-06-12 Democratic Governor primary | 2018-06-12 Primary Election | Yes | 4 | 6,111 | 15,000 | First operational statewide RCV primary in the harvested set; useful launch-year stress test. |
| 2018-06-12 Democratic Representative to Congress, District 2 primary | 2018-06-12 Primary Election | Yes | 2 | 5,634 | 7,381 | First operational federal-primary RCV comparator in the harvested set. |
| 2018-11-06 Representative to Congress, District 2 general | 2018-11-06 General Election | Yes | 2 | 6,453 | 14,706 | First federal general-election CD-2 RCV comparator in the harvested set. |
| 2020-07-14 Republican Representative to Congress, District 2 primary | 2020-07-14 Primary Election | Yes | 2 | 5,945 | 10,192 | Post-launch federal primary RCV comparator with same-election non-RCV federal-primary files. |
| 2022-06-14 Republican State Senate District 16 primary | 2022-06-14 Primary Election | Yes | 2 | 65 | 212 | District-level RCV primary; useful for implementation but not directly comparable to statewide/federal turnout. |
| 2022-11-08 Representative to Congress, District 2 general | 2022-11-08 General Election | Yes | 2 | 6,396 | 11,500 | Post-launch federal general-election CD-2 RCV comparator. |
| 2024-11-05 Representative to Congress, District 2 general | 2024-11-05 General Election | Pending verification | TBD | TBD | TBD | First-choice workbook extracted, but the summary PDF requires OCR or manual verification for round/exhaustion values. |
| 2026-06-09 Democratic Representative to Congress, District 2 primary | 2026-06-09 Primary Election | Yes | 3 | 4,675 | 15,001 | Shows a four-candidate federal primary where ballot exhaustion becomes material by the final round. |
| 2026-06-09 Democratic Governor primary | 2026-06-09 Primary Election | Yes | 4 | 4,658 | 23,705 | Shows a five-candidate statewide primary where multiple rounds were needed. |
| 2026-06-09 Republican Governor primary | 2026-06-09 Primary Election | Yes | 7 | 8,574 | 38,609 | Shows a large-field statewide primary and therefore a useful stress test for ranking depth and ballot completion. |
| 2026-06-09 Republican Senate District 4 primary | 2026-06-09 Primary Election | Yes | 3 | 526 | 1,287 | District-level RCV primary; useful for implementation but not directly comparable to statewide/federal turnout. |
| 2026-06-09 Republican House District 58 primary | 2026-06-09 Primary Election | Yes | 2 | 174 | 379 | District-level RCV primary with small-ballot-count exhaustion context. |

## Archive Coverage Notes

This section explains how much source coverage exists before deeper extraction. It is a routing table, not an analytical conclusion.

| Year | Window role | Official archive coverage observed | Usefulness for ELEC-015 |
| --- | --- | --- | --- |
| 2010 | Pre-RCV baseline | General and referendum election files; U.S. Congress TXT, Governor PDF, State Senate TXT, State Representative TXT, county-office TXT files. | Useful for general-election candidate-count and vote-total baseline; primary baseline is not as visible on the current archive page. |
| 2011 | Pre-RCV baseline | Referendum, special election, county referendum, and county-office Excel files. | Context only; not a regular statewide candidate-participation comparator. |
| 2012 | Pre-RCV baseline | Primary total-votes files by party plus TXT/XLS tabulations for U.S. Senate, U.S. House, State Senate, State Representative, and county offices; general-election federal/state/county files also posted. | High-value baseline year. Candidate counts and ballots cast are extractable from official pipe-delimited TXT files without spreadsheet tooling. |
| 2013 | Pre-RCV baseline | Referendum and special-election files. | Context only; not a regular statewide candidate-participation comparator. |
| 2014 | Pre-RCV baseline | General/referendum and primary-election result groups listed. | High-value baseline year; federal/statewide primary extraction complete for this pass, general-election extraction pending. |
| 2015 | Pre-RCV baseline | Referendum and special-election files. | Context only; not a regular statewide candidate-participation comparator. |
| 2016 | Pre-RCV baseline | General/referendum and primary-election result groups listed. | High-value baseline year; U.S. House primary extraction complete for this pass, general-election extraction pending. |
| 2017 | Pre-RCV baseline | Referendum and special-election files. | Context only; not a regular statewide candidate-participation comparator. |

## Extraction Roadmap

This section lists the next work needed to fill the event-level trend table.

1. Reduce 2012, 2014, and 2016 general-election files if pre-RCV general-election comparators become necessary.
2. Reduce broader non-RCV general-election comparator files for 2018, 2020, 2022, and 2024 so federal RCV general elections can be compared against same-cycle non-RCV offices.
3. OCR or manually verify the 2024 CD-2 RCV summary PDF so round count and exhausted-ballot values can be added.
4. Decide whether to reduce 2026 legislative non-RCV aggregate files beyond the two RCV district summaries; if so, normalize by district and office before comparing.
5. Add CVR-derived ranking-depth and ballot-completion measures only after event-level candidate/turnout values are stable.
6. Treat odd-year files from 2011, 2013, 2015, 2017, 2019, 2021, 2023, and 2025 as context unless a specific special-election comparison becomes useful.

## Current Limits

This section prevents the page from being over-read.

- This file does not yet determine whether RCV increased or decreased candidate participation or voter participation.
- The event-level values now cover the principal regular primary and RCV general-election comparator events, but they remain a source-development scaffold rather than a conclusion.
- Same-election and prior-cycle comparisons need normalization by office type, district, party, competitiveness, presidential-cycle effects, ballot questions, and candidate salience.
- Old Maine result formats vary. TXT files are immediately parseable; XLS/PDF files may require additional tooling or manual verification.
