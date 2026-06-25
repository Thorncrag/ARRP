# Audit Dashboard

This dashboard is the compact project-wide audit tracker. It is for meta-analysis, triage, and audit planning only; detailed audit findings belong on the relevant issue page and compact tracking data belongs in [`inventory/audits.csv`](inventory/audits.csv).

Update this page whenever an audit changes an issue score, audit status, last audit type, next audit need, issue link, legislation link, development status, or other dashboard field.

## Snapshot

- Issues tracked: 205
- Issues with proposed legislation links: 19
- Developed issues: 20
- Candidate issues: 171
- Retired or merged issues: 13
- Paused for controlling finding: 1

## Score Bands

| Band | Count |
| --- | ---: |
| Retired/merged | 13 |
| Paused | 1 |
| Inventory | 171 |
| Developed draft | 19 |
| Audit in progress | 1 |

## Next Audit Queue

| Next audit indicator | Count |
| --- | ---: |
| Advanced audit | 17 |
| Cross-reference check | 13 |
| Development audit | 1 |
| Issue-admission test | 171 |
| Reassess predicate | 1 |
| T2 | 1 |
| T3 | 1 |

## Horizon Scan Reports

Horizon Scan audits identify possible new, emerging, or newly salient concerns within the project's goals. They are project-wide discovery reports, not direct implementation passes. Each scan should apply the Issue-Admission Test, cross-check existing issues and legislation for duplication or overlap, and recommend whether to expand, adapt, amend, cross-reference, source-develop, create a new candidate, or decline the concern.

### 2026-06-25 Horizon Scan

**Scope.** Project-wide scan for new, emerging, or newly salient institutional-risk concerns based on current public reporting and official materials available on June 25, 2026.

**Source categories checked.** Current news reporting; federal court reporting; Federal Register executive-order materials; public legislative context; existing ARRP issue inventory; existing ARRP contents index; existing proposed legislation list.

**Implementation status.** Report only. No issue pages, legislation files, inventory rows, audit scores, or source records were changed by this scan.

| Date | Concern | Existing overlap | Issue-admission result | Recommended disposition | Sources / next source need | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-06-25 | Federal election-control escalation through proof-of-citizenship rules, mail-ballot restrictions, voter-data demands, and federal voter-list construction. | [ELEC-001](areas/a-02-election-integrity/issues/ELEC-001.md), [ELEC-004](areas/a-02-election-integrity/issues/ELEC-004.md), [ELEC-010](areas/a-02-election-integrity/issues/ELEC-010.md), FED-006. | Mostly covered, but the voter-data and federal-list architecture may be distinct enough for source development. | Expand ELEC-001 and ELEC-010; consider a separate candidate only if the voter-data architecture cannot be cleanly handled there. | [AP on permanent injunction](https://apnews.com/article/trump-elections-judge-358912bcb6c7223b3d2d36465156fde9); [AP on Michigan voter-data appeal](https://apnews.com/article/b73d510dddaf9c96088904b6c44f919a); [AP on Maryland voter-data lawsuit](https://apnews.com/article/67c94fb8af9cbcf2a0947ad81de5eab4); [Federal Register EO 14399](https://www.federalregister.gov/documents/2026/04/03/2026-06601/ensuring-citizenship-verification-and-integrity-in-federal-elections). | High |
| 2026-06-25 | Immigration-enforcement surveillance expansion through AI tools, data brokers, facial recognition, drones, device extraction, and contractor-driven systems. | CIV-009, DOM-007, FACT-002, REC-006; no developed legislation appears to address law-enforcement surveillance procurement directly. | Likely passes as a distinct candidate if framed as federal law-enforcement surveillance infrastructure rather than immigration policy. | Source-develop a possible A-14 or A-18 candidate; cross-link to civil-service/DOGE data-access concerns and records/privacy safeguards. | [Guardian report on ICE surveillance contracts](https://www.theguardian.com/us-news/2026/jun/24/ice-tech-surveillance-arsenal). Next source need: underlying Mijente / Just Futures Law / Surveillance Resistance Lab report and DHS procurement records. | Medium-high |
| 2026-06-25 | Executive or agency obstruction of court-ordered civic-property restoration, illustrated by the Kennedy Center tarp after removal of Trump naming. | HER-001 through HER-008; [JUD-001](areas/a-04-judicial-independence-and-enforcement/issues/JUD-001.md). | Does not require a new issue; it is a manifestation of existing civic-heritage and judicial-compliance issues. | Expand A-23 source-development notes and consider adding the event as a JUD-001 manifestation if primary court filings confirm the compliance-evasion theory. | [Guardian on Kennedy Center order](https://www.theguardian.com/us-news/2026/jun/24/judge-kennedy-center-tarp). Next source need: district-court order and relevant appellate filings. | Medium |
| 2026-06-25 | Presidential use of presentment/signature delay to hold unrelated bipartisan legislation hostage for election-law demands. | CONG-008, FUND-002, FUND-003, FUND-008; no exact issue on presentment leverage or presidential refusal to sign unrelated bills as coercion. | Research-inventory candidate; may pass if framed as abuse of presentment/signature timing to coerce Congress, but ordinary veto/signing discretion makes the legal weakness uncertain. | Add to source-development queue under A-15; do not promote until pattern, legal hook, and least-complex remedy are clearer. | [AP on housing bill delay](https://apnews.com/article/85db7cc9fead2730dda9cfa7706f8189); [Axios on SAVE Act linkage](https://www.axios.com/2026/06/24/trump-delays-housing-bill-save-act). | Medium |
| 2026-06-25 | Unilateral agency-name or statutory-title rebranding, including Department of Defense / Department of War secondary-title use without formal statutory renaming. | WAR-001; APPT-006; HER/civic-branding concerns by analogy. | Possible candidate, but not yet clearly distinct from broader statutory-evasion and war-powers messaging issues. | Source-develop under A-03 and A-12; consider a candidate only if the scan confirms legal, appropriations, records, seal, website, procurement, or public-notice consequences beyond symbolism. | [Federal Register EO 14347](https://www.federalregister.gov/documents/2025/09/10/2025-17508/restoring-the-united-states-department-of-war); [Washington Post report](https://www.washingtonpost.com/national-security/2025/09/05/war-department-trump-hegseth/). Next source need: 10 U.S.C. statutory-name review and CBO cost estimate. | Medium |
| 2026-06-25 | Federal Reserve independence pressure through removal threats, investigations, and personal/legal/security burdens on governors. | FRB-001, FRB-002, FRB-006, FRB-007. | Already covered by A-21 candidates; no new issue needed. | Prioritize source development for FRB-002 and FRB-006; use current litigation and ethics-disclosure reporting as manifestations. | [Guardian on Lisa Cook legal/security fees](https://www.theguardian.com/business/2026/jun/18/lisa-cook-legal-security-fees-trump-fed); [Guardian on Powell pressure](https://www.theguardian.com/business/2026/jan/28/federal-reserve-holds-rates-powell-trump). | Medium-high |
| 2026-06-25 | Iran-war escalation and supplemental funding request after Senate war-powers pushback. | [WAR-001](areas/a-03-war-powers-and-military-force/issues/WAR-001.md), WAR-002 through WAR-008 retired into WAR-001. | Already covered by WAR-001; no new issue needed. | Add source-development notes to WAR-001 in a later implementation pass; use as current manifestation and bipartisan-support evidence for war-powers reform. | [Guardian on Senate war-powers resolution](https://www.theguardian.com/us-news/2026/jun/23/trump-iran-war-powers-resolution); [Axios on supplemental request](https://www.axios.com/2026/06/25/trump-white-house-congress-request-iran-war-us-farmers-ebola). | Medium-high |

**Scan assessment.** No finding in this scan should be implemented automatically. The strongest immediate implementation candidates are expansion of ELEC-001/ELEC-010 for federal voter-data and mail-ballot control, source development for a federal law-enforcement surveillance candidate, and source development for A-21 Federal Reserve independence. The Kennedy Center and Iran-war findings appear better treated as current manifestations of existing issues. The presentment/signature leverage and Department of War findings require more legal-hook analysis before promotion.

## Issue Audit Index

| Issue | Area | Priority | Status | Score | Band | Runs | Last audit | Last date | Next | Issue page | Legislation |
| --- | --- | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| DOJ-001 | A-01 | High | Developed | 73 | Audit in progress | 6 | Targeted T2 follow-up | 2026-06-25 | T3 | [Issue](areas/a-01-department-of-justice/issues/DOJ-001.md) | [Bill](legislation/DOJ-001.md) |
| DOJ-002 | A-01 | High | Developed | 62 | Developed draft | 2 | T1 framework check | 2026-06-25 | T2 | [Issue](areas/a-01-department-of-justice/issues/DOJ-002.md) | [Bill](legislation/DOJ-002.md) |
| DOJ-003 | A-01 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-01-department-of-justice/issues/DOJ-003.md) | [Bill](legislation/DOJ-003.md) |
| DOJ-004 | A-01 | High | Awaiting merits adjudication | 0 | Paused | 1 | Initial inventory audit | 2026-06-24 | Reassess predicate | [Issue](areas/a-01-department-of-justice/issues/DOJ-004.md) | — |
| DOJ-005 | A-01 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-01-department-of-justice/issues/DOJ-005.md) | [Bill](legislation/DOJ-005.md) |
| DOJ-006 | A-01 | High | Retired—merged into DOJ-002 and DOJ-007 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/a-01-department-of-justice/README.md) | — |
| DOJ-007 | A-01 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-01-department-of-justice/issues/DOJ-007.md) | [Bill](legislation/DOJ-007.md) |
| DOJ-008 | A-01 | High | Retired—merged into DOJ-003 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/a-01-department-of-justice/README.md) | — |
| DOJ-009 | A-01 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-01-department-of-justice/issues/DOJ-009.md) | [Bill](legislation/DOJ-009.md) |
| ELEC-001 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-02-election-integrity/issues/ELEC-001.md) | [Bill](legislation/ELEC-001.md) |
| ELEC-002 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-02-election-integrity/issues/ELEC-002.md) | [Bill](legislation/ELEC-002-state.md) |
| ELEC-003 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-02-election-integrity/issues/ELEC-003.md) | [Bill 1](legislation/ELEC-003-state.md)<br />[Bill 2](legislation/ELEC-003.md) |
| ELEC-004 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-02-election-integrity/issues/ELEC-004.md) | [Bill 1](legislation/ELEC-004-state.md)<br />[Bill 2](legislation/ELEC-004.md) |
| ELEC-005 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-02-election-integrity/issues/ELEC-005.md) | [Bill](legislation/ELEC-005.md) |
| ELEC-006 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-02-election-integrity/issues/ELEC-006.md) | [Bill](legislation/ELEC-006.md) |
| ELEC-007 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-02-election-integrity/issues/ELEC-007.md) | [Bill](legislation/ELEC-007.md) |
| ELEC-008 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-02-election-integrity/issues/ELEC-008.md) | [Bill](legislation/ELEC-008.md) |
| ELEC-009 | A-02 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-02-election-integrity/issues/ELEC-009.md) | [Bill](legislation/ELEC-009.md) |
| ELEC-010 | A-02 | High | Developed | 55 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Development audit | [Issue](areas/a-02-election-integrity/issues/ELEC-010.md) | — |
| WAR-001 | A-03 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-03-war-powers-and-military-force/issues/WAR-001.md) | [Bill](legislation/WAR-001.md) |
| WAR-002 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/a-03-war-powers-and-military-force/README.md) | — |
| WAR-003 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/a-03-war-powers-and-military-force/README.md) | — |
| WAR-004 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/a-03-war-powers-and-military-force/README.md) | — |
| WAR-005 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/a-03-war-powers-and-military-force/README.md) | — |
| WAR-006 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/a-03-war-powers-and-military-force/README.md) | — |
| WAR-007 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/a-03-war-powers-and-military-force/README.md) | — |
| WAR-008 | A-03 | High | Retired—merged into WAR-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/a-03-war-powers-and-military-force/README.md) | — |
| JUD-001 | A-04 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-04-judicial-independence-and-enforcement/issues/JUD-001.md) | [Bill](legislation/JUD-001.md) |
| JUD-002 | A-04 | High | Retired—merged into JUD-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/a-04-judicial-independence-and-enforcement/README.md) | — |
| JUD-003 | A-04 | High | Retired—merged into JUD-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/a-04-judicial-independence-and-enforcement/README.md) | — |
| JUD-004 | A-04 | High | Retired—merged into JUD-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/a-04-judicial-independence-and-enforcement/README.md) | — |
| JUD-005 | A-04 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-04-judicial-independence-and-enforcement/README.md) | — |
| JUD-006 | A-04 | High | Retired—merged into JUD-001 | 0 | Retired/merged | 1 | Initial inventory audit | 2026-06-24 | Cross-reference check | [Issue](areas/a-04-judicial-independence-and-enforcement/README.md) | — |
| JUD-007 | A-04 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-04-judicial-independence-and-enforcement/README.md) | — |
| JUD-008 | A-04 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-04-judicial-independence-and-enforcement/README.md) | — |
| JUD-009 | A-04 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-04-judicial-independence-and-enforcement/issues/JUD-009.md) | [Bill](legislation/JUD-009.md) |
| PAR-001 | A-05 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-05-presidential-clemency-and-pardon-power/README.md) | — |
| PAR-002 | A-05 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-05-presidential-clemency-and-pardon-power/README.md) | — |
| PAR-003 | A-05 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-05-presidential-clemency-and-pardon-power/README.md) | — |
| PAR-004 | A-05 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-05-presidential-clemency-and-pardon-power/README.md) | — |
| PAR-005 | A-05 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-05-presidential-clemency-and-pardon-power/README.md) | — |
| PAR-006 | A-05 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-05-presidential-clemency-and-pardon-power/README.md) | — |
| PAR-007 | A-05 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-05-presidential-clemency-and-pardon-power/README.md) | — |
| PAR-008 | A-05 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-05-presidential-clemency-and-pardon-power/README.md) | — |
| PAR-009 | A-05 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-05-presidential-clemency-and-pardon-power/README.md) | — |
| PAR-010 | A-05 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-05-presidential-clemency-and-pardon-power/README.md) | — |
| EMOL-001 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| EMOL-002 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| EMOL-003 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| EMOL-004 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| EMOL-005 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| EMOL-006 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| EMOL-007 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| EMOL-008 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| EMOL-009 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| EMOL-010 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| EMOL-011 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| EMOL-012 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| EMOL-013 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| EMOL-014 | A-06 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-06-presidential-conflicts-of-interest-and-emoluments/README.md) | — |
| CLASS-001 | A-07 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-07-classification-declassification-and-national-security-information/README.md) | — |
| CLASS-002 | A-07 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-07-classification-declassification-and-national-security-information/README.md) | — |
| CLASS-003 | A-07 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-07-classification-declassification-and-national-security-information/README.md) | — |
| CLASS-004 | A-07 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-07-classification-declassification-and-national-security-information/README.md) | — |
| CLASS-005 | A-07 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-07-classification-declassification-and-national-security-information/README.md) | — |
| CLASS-006 | A-07 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-07-classification-declassification-and-national-security-information/README.md) | — |
| CLASS-007 | A-07 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-07-classification-declassification-and-national-security-information/README.md) | — |
| CLASS-008 | A-07 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-07-classification-declassification-and-national-security-information/README.md) | — |
| CLASS-009 | A-07 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-07-classification-declassification-and-national-security-information/README.md) | — |
| CLASS-010 | A-07 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-07-classification-declassification-and-national-security-information/README.md) | — |
| CLASS-011 | A-07 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-07-classification-declassification-and-national-security-information/README.md) | — |
| CLASS-012 | A-07 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-07-classification-declassification-and-national-security-information/README.md) | — |
| CIV-001 | A-08 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-08-civil-service-and-professional-administration/README.md) | — |
| CIV-002 | A-08 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-08-civil-service-and-professional-administration/README.md) | — |
| CIV-003 | A-08 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-08-civil-service-and-professional-administration/README.md) | — |
| CIV-004 | A-08 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-08-civil-service-and-professional-administration/README.md) | — |
| CIV-005 | A-08 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-08-civil-service-and-professional-administration/README.md) | — |
| CIV-006 | A-08 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-08-civil-service-and-professional-administration/README.md) | — |
| CIV-007 | A-08 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-08-civil-service-and-professional-administration/README.md) | — |
| CIV-008 | A-08 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-08-civil-service-and-professional-administration/README.md) | — |
| CIV-009 | A-08 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-08-civil-service-and-professional-administration/README.md) | — |
| OVS-001 | A-09 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-09-inspectors-general-whistleblowers-and-internal-oversight/README.md) | — |
| OVS-002 | A-09 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-09-inspectors-general-whistleblowers-and-internal-oversight/README.md) | — |
| OVS-003 | A-09 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-09-inspectors-general-whistleblowers-and-internal-oversight/README.md) | — |
| OVS-004 | A-09 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-09-inspectors-general-whistleblowers-and-internal-oversight/README.md) | — |
| OVS-005 | A-09 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-09-inspectors-general-whistleblowers-and-internal-oversight/README.md) | — |
| OVS-006 | A-09 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-09-inspectors-general-whistleblowers-and-internal-oversight/README.md) | — |
| OVS-007 | A-09 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-09-inspectors-general-whistleblowers-and-internal-oversight/README.md) | — |
| OVS-008 | A-09 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-09-inspectors-general-whistleblowers-and-internal-oversight/README.md) | — |
| EMERG-001 | A-10 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-10-emergency-powers-and-domestic-executive-authority/README.md) | — |
| EMERG-002 | A-10 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-10-emergency-powers-and-domestic-executive-authority/README.md) | — |
| EMERG-003 | A-10 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-10-emergency-powers-and-domestic-executive-authority/README.md) | — |
| EMERG-004 | A-10 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-10-emergency-powers-and-domestic-executive-authority/README.md) | — |
| EMERG-005 | A-10 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-10-emergency-powers-and-domestic-executive-authority/README.md) | — |
| EMERG-006 | A-10 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-10-emergency-powers-and-domestic-executive-authority/README.md) | — |
| EMERG-007 | A-10 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-10-emergency-powers-and-domestic-executive-authority/README.md) | — |
| EMERG-008 | A-10 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-10-emergency-powers-and-domestic-executive-authority/README.md) | — |
| FUND-001 | A-11 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-11-congressional-power-of-the-purse-and-impoundment/README.md) | — |
| FUND-002 | A-11 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-11-congressional-power-of-the-purse-and-impoundment/README.md) | — |
| FUND-003 | A-11 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-11-congressional-power-of-the-purse-and-impoundment/README.md) | — |
| FUND-004 | A-11 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-11-congressional-power-of-the-purse-and-impoundment/README.md) | — |
| FUND-005 | A-11 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-11-congressional-power-of-the-purse-and-impoundment/README.md) | — |
| FUND-006 | A-11 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-11-congressional-power-of-the-purse-and-impoundment/README.md) | — |
| FUND-007 | A-11 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-11-congressional-power-of-the-purse-and-impoundment/README.md) | — |
| FUND-008 | A-11 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-11-congressional-power-of-the-purse-and-impoundment/README.md) | — |
| APPT-001 | A-12 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-12-appointments-acting-officials-and-senate-confirmation/README.md) | — |
| APPT-002 | A-12 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-12-appointments-acting-officials-and-senate-confirmation/README.md) | — |
| APPT-003 | A-12 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-12-appointments-acting-officials-and-senate-confirmation/README.md) | — |
| APPT-004 | A-12 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-12-appointments-acting-officials-and-senate-confirmation/README.md) | — |
| APPT-005 | A-12 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-12-appointments-acting-officials-and-senate-confirmation/README.md) | — |
| APPT-006 | A-12 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-12-appointments-acting-officials-and-senate-confirmation/README.md) | — |
| APPT-007 | A-12 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-12-appointments-acting-officials-and-senate-confirmation/README.md) | — |
| APPT-008 | A-12 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-12-appointments-acting-officials-and-senate-confirmation/README.md) | — |
| REC-001 | A-13 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-13-presidential-records-archives-and-government-information/README.md) | — |
| REC-002 | A-13 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-13-presidential-records-archives-and-government-information/README.md) | — |
| REC-003 | A-13 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-13-presidential-records-archives-and-government-information/README.md) | — |
| REC-004 | A-13 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-13-presidential-records-archives-and-government-information/README.md) | — |
| REC-005 | A-13 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-13-presidential-records-archives-and-government-information/README.md) | — |
| REC-006 | A-13 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-13-presidential-records-archives-and-government-information/README.md) | — |
| REC-007 | A-13 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-13-presidential-records-archives-and-government-information/README.md) | — |
| REC-008 | A-13 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-13-presidential-records-archives-and-government-information/README.md) | — |
| DOM-001 | A-14 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-14-federal-law-enforcement-and-military-use-inside-the-united-states/README.md) | — |
| DOM-002 | A-14 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-14-federal-law-enforcement-and-military-use-inside-the-united-states/README.md) | — |
| DOM-003 | A-14 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-14-federal-law-enforcement-and-military-use-inside-the-united-states/README.md) | — |
| DOM-004 | A-14 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-14-federal-law-enforcement-and-military-use-inside-the-united-states/README.md) | — |
| DOM-005 | A-14 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-14-federal-law-enforcement-and-military-use-inside-the-united-states/README.md) | — |
| DOM-006 | A-14 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-14-federal-law-enforcement-and-military-use-inside-the-united-states/README.md) | — |
| DOM-007 | A-14 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-14-federal-law-enforcement-and-military-use-inside-the-united-states/README.md) | — |
| DOM-008 | A-14 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-14-federal-law-enforcement-and-military-use-inside-the-united-states/README.md) | — |
| CONG-001 | A-15 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-15-congressional-oversight-and-executive-accountability/README.md) | — |
| CONG-002 | A-15 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-15-congressional-oversight-and-executive-accountability/README.md) | — |
| CONG-003 | A-15 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-15-congressional-oversight-and-executive-accountability/README.md) | — |
| CONG-004 | A-15 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-15-congressional-oversight-and-executive-accountability/README.md) | — |
| CONG-005 | A-15 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-15-congressional-oversight-and-executive-accountability/README.md) | — |
| CONG-006 | A-15 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-15-congressional-oversight-and-executive-accountability/README.md) | — |
| CONG-007 | A-15 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-15-congressional-oversight-and-executive-accountability/README.md) | — |
| CONG-008 | A-15 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-15-congressional-oversight-and-executive-accountability/README.md) | — |
| IMM-001 | A-16 | High | Developed | 60 | Developed draft | 1 | Initial inventory audit | 2026-06-24 | Advanced audit | [Issue](areas/a-16-presidential-immunity-and-accountability-for-official-misconduct/issues/IMM-001.md) | [Bill](legislation/IMM-001.md) |
| IMM-002 | A-16 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-16-presidential-immunity-and-accountability-for-official-misconduct/README.md) | — |
| IMM-003 | A-16 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-16-presidential-immunity-and-accountability-for-official-misconduct/README.md) | — |
| IMM-004 | A-16 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-16-presidential-immunity-and-accountability-for-official-misconduct/README.md) | — |
| IMM-005 | A-16 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-16-presidential-immunity-and-accountability-for-official-misconduct/README.md) | — |
| IMM-006 | A-16 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-16-presidential-immunity-and-accountability-for-official-misconduct/README.md) | — |
| IMM-007 | A-16 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-16-presidential-immunity-and-accountability-for-official-misconduct/README.md) | — |
| IMM-008 | A-16 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-16-presidential-immunity-and-accountability-for-official-misconduct/README.md) | — |
| REG-001 | A-17 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-17-independent-agencies-and-regulatory-neutrality/README.md) | — |
| REG-002 | A-17 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-17-independent-agencies-and-regulatory-neutrality/README.md) | — |
| REG-003 | A-17 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-17-independent-agencies-and-regulatory-neutrality/README.md) | — |
| REG-004 | A-17 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-17-independent-agencies-and-regulatory-neutrality/README.md) | — |
| REG-005 | A-17 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-17-independent-agencies-and-regulatory-neutrality/README.md) | — |
| REG-006 | A-17 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-17-independent-agencies-and-regulatory-neutrality/README.md) | — |
| REG-007 | A-17 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-17-independent-agencies-and-regulatory-neutrality/README.md) | — |
| REG-008 | A-17 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-17-independent-agencies-and-regulatory-neutrality/README.md) | — |
| FACT-001 | A-18 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-18-government-scientific-statistical-and-factual-integrity/README.md) | — |
| FACT-002 | A-18 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-18-government-scientific-statistical-and-factual-integrity/README.md) | — |
| FACT-003 | A-18 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-18-government-scientific-statistical-and-factual-integrity/README.md) | — |
| FACT-004 | A-18 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-18-government-scientific-statistical-and-factual-integrity/README.md) | — |
| FACT-005 | A-18 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-18-government-scientific-statistical-and-factual-integrity/README.md) | — |
| FACT-006 | A-18 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-18-government-scientific-statistical-and-factual-integrity/README.md) | — |
| FACT-007 | A-18 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-18-government-scientific-statistical-and-factual-integrity/README.md) | — |
| FACT-008 | A-18 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-18-government-scientific-statistical-and-factual-integrity/README.md) | — |
| RET-001 | A-19 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-19-federal-contracting-grants-licensing-and-regulatory-retaliation/README.md) | — |
| RET-002 | A-19 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-19-federal-contracting-grants-licensing-and-regulatory-retaliation/README.md) | — |
| RET-003 | A-19 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-19-federal-contracting-grants-licensing-and-regulatory-retaliation/README.md) | — |
| RET-004 | A-19 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-19-federal-contracting-grants-licensing-and-regulatory-retaliation/README.md) | — |
| RET-005 | A-19 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-19-federal-contracting-grants-licensing-and-regulatory-retaliation/README.md) | — |
| RET-006 | A-19 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-19-federal-contracting-grants-licensing-and-regulatory-retaliation/README.md) | — |
| RET-007 | A-19 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-19-federal-contracting-grants-licensing-and-regulatory-retaliation/README.md) | — |
| RET-008 | A-19 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-19-federal-contracting-grants-licensing-and-regulatory-retaliation/README.md) | — |
| FED-001 | A-20 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-20-federalism-and-presidential-coercion-of-states/README.md) | — |
| FED-002 | A-20 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-20-federalism-and-presidential-coercion-of-states/README.md) | — |
| FED-003 | A-20 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-20-federalism-and-presidential-coercion-of-states/README.md) | — |
| FED-004 | A-20 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-20-federalism-and-presidential-coercion-of-states/README.md) | — |
| FED-005 | A-20 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-20-federalism-and-presidential-coercion-of-states/README.md) | — |
| FED-006 | A-20 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-20-federalism-and-presidential-coercion-of-states/README.md) | — |
| FED-007 | A-20 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-20-federalism-and-presidential-coercion-of-states/README.md) | — |
| FED-008 | A-20 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-20-federalism-and-presidential-coercion-of-states/README.md) | — |
| FRB-001 | A-21 | Critical | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-21-federal-reserve-independence-and-monetary-policy/README.md) | — |
| FRB-002 | A-21 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-21-federal-reserve-independence-and-monetary-policy/README.md) | — |
| FRB-003 | A-21 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-21-federal-reserve-independence-and-monetary-policy/README.md) | — |
| FRB-004 | A-21 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-21-federal-reserve-independence-and-monetary-policy/README.md) | — |
| FRB-005 | A-21 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-21-federal-reserve-independence-and-monetary-policy/README.md) | — |
| FRB-006 | A-21 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-21-federal-reserve-independence-and-monetary-policy/README.md) | — |
| FRB-007 | A-21 | Critical | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-21-federal-reserve-independence-and-monetary-policy/README.md) | — |
| FRB-008 | A-21 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-21-federal-reserve-independence-and-monetary-policy/README.md) | — |
| PRESS-001 | A-22 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-22-freedom-and-independence-of-the-press/README.md) | — |
| PRESS-002 | A-22 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-22-freedom-and-independence-of-the-press/README.md) | — |
| PRESS-003 | A-22 | Critical | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-22-freedom-and-independence-of-the-press/README.md) | — |
| PRESS-004 | A-22 | Critical | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-22-freedom-and-independence-of-the-press/README.md) | — |
| PRESS-005 | A-22 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-22-freedom-and-independence-of-the-press/README.md) | — |
| PRESS-006 | A-22 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-22-freedom-and-independence-of-the-press/README.md) | — |
| PRESS-007 | A-22 | Critical | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-22-freedom-and-independence-of-the-press/README.md) | — |
| PRESS-008 | A-22 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-22-freedom-and-independence-of-the-press/README.md) | — |
| PRESS-009 | A-22 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-22-freedom-and-independence-of-the-press/README.md) | — |
| PRESS-010 | A-22 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-22-freedom-and-independence-of-the-press/README.md) | — |
| PRESS-011 | A-22 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-22-freedom-and-independence-of-the-press/README.md) | — |
| PRESS-012 | A-22 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-22-freedom-and-independence-of-the-press/README.md) | — |
| HER-001 | A-23 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-23-federal-historic-property-and-civic-heritage/README.md) | — |
| HER-002 | A-23 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-23-federal-historic-property-and-civic-heritage/README.md) | — |
| HER-003 | A-23 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-23-federal-historic-property-and-civic-heritage/README.md) | — |
| HER-004 | A-23 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-23-federal-historic-property-and-civic-heritage/README.md) | — |
| HER-005 | A-23 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-23-federal-historic-property-and-civic-heritage/README.md) | — |
| HER-006 | A-23 | Medium | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-23-federal-historic-property-and-civic-heritage/README.md) | — |
| HER-007 | A-23 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-23-federal-historic-property-and-civic-heritage/README.md) | — |
| HER-008 | A-23 | High | Candidate | 10 | Inventory | 1 | Initial inventory audit | 2026-06-24 | Issue-admission test | [Issue](areas/a-23-federal-historic-property-and-civic-heritage/README.md) | — |
