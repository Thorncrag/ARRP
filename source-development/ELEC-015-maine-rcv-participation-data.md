---
title: "ELEC-015 Maine RCV Participation Data"
source_issue: "../areas/ELEC/issues/ELEC-015.md"
jurisdiction: Maine
print_levels:
  - full-technical
---

# ELEC-015 Maine RCV Participation Data

This file compares Maine election events using official Maine Secretary of State result data. The comparison unit is the election event, not each individual primary, town, candidate subtotal, or cast-vote-record line.

## Election Comparison Table

| Election name | RCV or not | Candidate participation | Voter turnout |
| --- | --- | --- | --- |
| 2012-06-12 Primary Election | No | 17 total candidates across 6 extracted federal primary contests | 133,915 party-primary ballots using extracted statewide U.S. Senate Democratic and Republican ballot totals |
| 2012-11-06 General Election | No | 4 ballot candidates in extracted presidential general file, excluding declared write-ins | 724,758 ballots cast statewide in extracted presidential general file |
| 2014-06-10 Primary Election | No | 10 total candidates across 8 extracted federal/statewide primary contests, excluding write-in/other columns | 127,398 party-primary ballots using extracted statewide Democratic and Republican ballot totals |
| 2014-11-04 General Election | No | 3 total candidates in extracted CD-2 general | 294,980 ballots cast in extracted CD-2 general |
| 2016-06-14 Primary Election | No | 5 total candidates across 4 extracted U.S. House primary contests | 98,776 party-primary ballots across extracted U.S. House district/party contests |
| 2016-11-08 General Election | No | 4 ballot candidates in extracted presidential general file, excluding write-ins/unprinted vote-receiving names | 771,892 ballots cast statewide in extracted presidential general file |
| 2018-06-12 Primary Election | Yes, mixed with non-RCV contests | 21 total candidates across 8 extracted federal/statewide primary contests | 234,380 party-primary ballots using extracted statewide Democratic and Republican ballot totals |
| 2018-11-06 General Election | Yes for CD-2 | 4 total candidates in extracted CD-2 RCV general | 296,077 ballots cast in extracted CD-2 RCV general |
| 2020-07-14 Primary Election | Yes, mixed with non-RCV contests | 10 total candidates across 6 extracted federal primary contests | 272,325 party-primary ballots using extracted statewide Democratic and Republican ballot totals |
| 2020-11-03 General Election | Yes for federal offices | 5 total candidates in extracted presidential general file | 828,305 ballots cast statewide in extracted presidential general file |
| 2022-06-14 Primary Election | Yes, mixed with non-RCV contests | 10 total candidates across 7 extracted federal/statewide and State Senate District 16 contests | 139,995 party-primary ballots using extracted statewide Democratic and Republican ballot totals |
| 2022-11-08 General Election | Yes for CD-2 | 3 ballot candidates in extracted CD-2 RCV general, excluding write-in | 322,778 ballots cast in extracted CD-2 RCV general |
| 2024-03-05 Presidential Primary Election | No | 7 total candidates across extracted Democratic and Republican presidential primaries | 182,378 party-primary ballots across extracted Democratic and Republican presidential primaries |
| 2024-06-11 State Primary Election | No in extracted federal primary contests | 8 total candidates across 6 extracted federal primary contests | 149,165 party-primary ballots using extracted statewide Democratic and Republican U.S. Senate ballot totals |
| 2024-11-05 General Election | Yes for federal offices | 7 total candidates across extracted presidential and CD-2 first-choice files | 842,447 ballots cast statewide in extracted presidential general file |
| 2026-06-09 Primary Election | Yes, mixed with non-RCV contests | 33 total candidates across 10 extracted federal/statewide and RCV district contests | 360,386 party-primary ballots using extracted statewide Democratic and Republican ballot totals |

## Normalized Trend Table

| Election event | Trend series | Office bucket | RCV exposure | Extracted contests | Total candidates | Candidates per contest | Turnout measure |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2012-06-12 Primary Election | Regular primary | Federal primary contests | Non-RCV | 6 | 17 | 2.83 | 133,915 |
| 2012-11-06 General Election | Presidential-year general | Presidential general contest | Non-RCV | 1 | 4 | 4.00 | 724,758 |
| 2014-06-10 Primary Election | Regular primary | Federal/statewide primary contests | Non-RCV | 8 | 10 | 1.25 | 127,398 |
| 2014-11-04 General Election | Midterm general | CD-2 general contest | Non-RCV | 1 | 3 | 3.00 | 294,980 |
| 2016-06-14 Primary Election | Regular primary | U.S. House primary contests | Non-RCV | 4 | 5 | 1.25 | 98,776 |
| 2016-11-08 General Election | Presidential-year general | Presidential general contest | Non-RCV | 1 | 4 | 4.00 | 771,892 |
| 2018-06-12 Primary Election | Regular primary | Federal/statewide primary contests | RCV mixed | 8 | 21 | 2.63 | 234,380 |
| 2018-11-06 General Election | Midterm general | CD-2 general contest | RCV activated | 1 | 4 | 4.00 | 296,077 |
| 2020-07-14 Primary Election | Regular primary | Federal primary contests | RCV mixed | 6 | 10 | 1.67 | 272,325 |
| 2020-11-03 General Election | Presidential-year general | Presidential general contest | RCV available for federal offices | 1 | 5 | 5.00 | 828,305 |
| 2022-06-14 Primary Election | Regular primary | Federal/statewide and State Senate District 16 contests | RCV mixed | 7 | 10 | 1.43 | 139,995 |
| 2022-11-08 General Election | Midterm general | CD-2 general contest | RCV activated | 1 | 3 | 3.00 | 322,778 |
| 2024-03-05 Presidential Primary Election | Presidential primary | Presidential party primaries | Non-RCV | 2 | 7 | 3.50 | 182,378 |
| 2024-06-11 State Primary Election | Regular primary | Federal primary contests | Non-RCV in extracted contests | 6 | 8 | 1.33 | 149,165 |
| 2024-11-05 General Election | Presidential-year general | Presidential and CD-2 first-choice files | RCV available for federal offices | 2 | 7 | 3.50 | 842,447 |
| 2026-06-09 Primary Election | Regular primary | Federal/statewide and RCV district contests | RCV mixed | 10 | 33 | 3.30 | 360,386 |

The graph separates regular primaries, midterm general elections, presidential-year general elections, and the presidential primary so unlike election environments are not connected into one trend line.

![Maine RCV participation trend](ELEC-015-maine-rcv-trend.svg)

Sources: Maine Secretary of State [Election Results/Data](https://www.maine.gov/sos/elections-voting/election-results-data), [Previous Election Year Results](https://www.maine.gov/sos/elections-voting/election-results-data/previous-election-results), and [Ranked-Choice Voting FAQ](https://www.maine.gov/sos/elections-voting/ranked-choice-voting-frequently-asked-questions).
