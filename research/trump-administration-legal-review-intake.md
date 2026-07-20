---
title: "Trump Administration Legal-Review Intake"
print_levels:
  - full-technical
---

# Trump Administration Legal-Review Intake

## Purpose and Status

This is a source-development intake for locating potentially repairable institutional weaknesses illustrated by actions of the first and second Trump administrations. It is deliberately broader than the active Horizon queue. It does **not automatically** assign Horizon IDs, determine that an action was unlawful, admit a new ARRP issue, or treat political controversy as an institutional defect. When the user approves promotion, the ordinary Horizon workflow creates a separate formal proposed-candidate record and removes the preliminary row.

The first machine-normalized baseline contains **1,322 source records**: **776 first-term records** and **546 second-term records**. They come from seven differently structured trackers and therefore are not yet 1,322 unique government actions. Cross-source duplicates remain visible until the record, challenged action, and final judicial posture can be reconciled without losing provenance.

- [Candidate Issue Intake](horizon-review-console/index.html), the read-only view of preliminary and formal proposed candidates
- [Action-level legal-review catalog](trump-administration-legal-review-catalog.csv), presently containing only presidential-directive evidence owned by formal Horizon candidates
- [Priority-disposition staging schema](trump-administration-priority-disposition-review.csv) (empty after adjudication but retained for repeatable tooling)
- [Media-supported episode intake](trump-administration-media-review-intake.csv)
- [Source-universe and completeness ledger](trump-administration-source-universe.csv)
- [Evidence-routing records](trump-administration-evidence-routing.csv), reconciled one-to-one with the remaining candidate-owned catalog records
- [Existing-issue evidence integration queue](existing-issue-evidence-integration.csv)
- [Defined-predicate source-and-posture ledger](trump-administration-litigation-monitoring.csv); GitHub monitor issues and the Project Monitoring view own workflow status
- [Preliminary candidate queue](trump-administration-preliminary-candidates.csv)
- [Preliminary candidate review console](horizon-review-console/README.md)
- [Completed source-adjudication report](trump-administration-source-adjudication-report.md)
- [Rebuild script](../scripts/build_trump_legal_review_catalog.py)

## Completed Route-Centered Adjudication

On July 16, 2026, the project completed qualitative route-centered review of all **1,266** records remaining after the priority batch. The review conservatively clustered them into **1,250** episodes, retained **160** records for qualitative integration, retained **178** records as **174** defined-predicate monitoring episodes, and removed **928** records as cumulative, topical-only, ordinary-policy, or insufficiently specific material. All tracker records left the catalog and routing staging files; retained work moved to the canonical source inventories, issue-owned integration records, and the source-and-posture ledger linked above, with monitoring workflow maintained in GitHub. The catalog and routing files now contain only **111** later-added presidential-directive records owned by five formal Horizon candidates. See the [completed report](trump-administration-source-adjudication-report.md) for the reconciliation and source-family results.

The downstream records are not a second raw review burden for the user and do not appear as separate console queues. Integration rows identify representative episodes that still require primary verification or reader-facing placement when the receiving proposal is developed. Source-and-posture rows support issue-linked GitHub monitors, which reopen work only upon a final merits ruling, controlling threshold decision, dismissal, settlement or withdrawal, or another material posture change. A future source that plausibly identifies a distinct unowned institutional weakness must create or update one clustered preliminary candidate rather than remain an orphaned source. No new preliminary Horizon candidate resulted from this batch.

## Inclusion Standard

An action may enter this research intake when at least one reliable source supplies one of the following predicates:

1. litigation alleging a statutory, constitutional, procedural, jurisdictional, or remedial defect;
2. a court ruling, official legal finding, inspector-general finding, Government Accountability Office decision, Office of Special Counsel finding, or comparable official record;
3. a serious and source-supported dispute about legal authority, required process, official retaliation, conflicts of interest, records preservation, use of public resources, or institutional compliance; or
4. a specialist tracker identifying conduct that warrants primary-source verification under one of those legal or institutional categories.

Inclusion means only that review is warranted. Policy reversal, severity of harm, partisan disagreement, or inconsistency with prior practice does not by itself establish a legal question or ARRP issue.

## Media-Corroboration Standard

The media lane supplements litigation and specialist trackers with episodes that may never produce a lawsuit or that are easier to identify through contemporaneous reporting. It is episode-based rather than article-based. An episode enters this lane only when at least two independent reliable news organizations report the same underlying government conduct.

Primary records receive greater evidentiary weight than the reports. Each entry therefore links an executive order, proclamation, presidential memorandum, demand letter, agency directive, court filing, official report, corporate filing, contract record, or comparable instrument when one has been located. The ledger expressly distinguishes a verified primary record from an instrument merely described by both reports or a record still requiring retrieval. Two-source reporting can qualify an episode for research review; it cannot substitute for an obtainable primary record in a publication-ready proposal.

The media intake presently contains **33 corroborated episodes**: **25 from the second term** and **8 from the first term**. Most are already manifestations of existing proposals or Horizon dispositions. Their inclusion does not imply that 33 new issues should be created.

## Litigation-Outcome Screening Rule

The catalog uses judicial posture to decide what should be reviewed first:

| Posture | Presumptive intake treatment |
| --- | --- |
| Action finally permitted, challenge dismissed on standing or jurisdiction, merits review unavailable, or relief legally foreclosed | High-priority institutional-gap review. Determine whether the result exposes a repairable authority, reviewability, standing, remedy, or enforcement weakness. |
| Open litigation, temporary relief, appeal pending, or materially mixed posture | Monitor. Preserve sources and revisit after a merits or controlling threshold ruling. |
| Action held unlawful and effectively stopped | Lower priority unless the action is readily repeatable, relief arrived too late, officials resisted compliance, the judgment was nonuniform, or the government avoided durable precedent. |
| Voluntary cessation, withdrawal, replacement, settlement, or tactical concession | Preserve for review. Determine whether the government mooted the case or avoided precedent without repairing the underlying weakness. |
| Human-rights, ethics, retaliation, or policy-tracker lead without a normalized legal posture | Verify the legal predicate and institutional defect before Horizon screening. |

This rule produced the initial screening distribution before route-centered adjudication:

- **56** records: action permitted or challenge dismissed — priority review;
- **181** records: open, interlocutory, or ongoing — monitoring;
- **197** records: action blocked or withdrawn — recurrence, delayed-relief, or incomplete-remedy review;
- **888** records: mixed, completed-but-unclassified, or legal-threshold normalization required.

The totals are source records, not deduplicated actions.

The initial priority worksheet applied provisional text classifications to 56 high-priority records. It was a temporary work queue, not a permanent evidence ledger, and is now empty after adjudication. The review confirmed that outcome labels alone do not establish an institutional defect: most records reflected ordinary policy adjudication, preliminary-relief decisions, later-modified outcomes, or topical overlap without additional reader-facing value. The permanent results now reside in the canonical cited-source inventory, on relevant issue pages, in formal Horizon records, in the [existing-record integration queue](existing-issue-evidence-integration.csv), or in the [defined-predicate source-and-posture ledger](trump-administration-litigation-monitoring.csv) supporting GitHub monitoring records.

## Present Source Coverage

The initial extraction normalizes:

- 154 second-term action clusters from the [Just Security Litigation Tracker](https://www.justsecurity.org/107087/tracker-litigation-legal-challenges-trump-administration/), consolidated from 898 case rows under the tracker's own executive-action labels;
- 246 first-term agency-action records from the [Institute for Policy Integrity Trump Court Roundup](https://policyintegrity.org/trump-court-roundup), including 54 actions for which the administration prevailed without withdrawing the challenged action;
- 263 actions marked as litigated by the [Immigration Policy Tracking Project](https://immpolicytracking.org/policies/?status=in-litigation), spanning both terms;
- 73 first-term discovery leads from the [Columbia Trump Administration Human Rights Tracker](https://trumphumanrightstracker.law.columbia.edu/);
- 24 second-term targets or enforcement episodes from the [Protect Democracy Retaliatory Actions Tracker](https://protectdemocracy.org/work/retaliatory-action-tracker/); and
- 45 second-term case and action records from the [Public Citizen Trump Administration 2.0 Lawsuit Tracker](https://www.citizen.org/article/trump-administration-2-0-lawsuit-tracker/); and
- 517 first- and second-term entries from the [Silencing Science Tracker](https://silencingscience.org/), retained as science-integrity discovery leads requiring independent legal and institutional screening.

The [source-universe ledger](trump-administration-source-universe.csv) separately records official corpora, specialist trackers, oversight portals, and comparison sources that remain to be ingested. A source is not considered covered merely because it has been bookmarked.

The separate [media-supported episode intake](trump-administration-media-review-intake.csv) presently records 33 independently corroborated episodes for the same evidence-routing process. It is not a separate user review queue. Two entries retain a primary-document retrieval flag: the Pentagon press-rotation memorandum and the FEMA grant instrument conditioning counterterrorism funding on state election practices.

## Official Presidential-Directive Completeness Pass

On July 18, 2026, the project implemented a signing-date-based [Federal Register presidential-directive gap scanner](../scripts/build_presidential_directive_gap_scan.py). It covers executive orders, proclamations, determinations, memoranda, notices, presidential orders, other presidential documents, and corrections. Federal Register document number is the primary identity key; numbered-instrument identity, normalized Federal Register or GovInfo URL, and signing date plus normalized title provide secondary matching. Corrections are attached to the corrected instrument rather than counted as new directives.

The non-mutating workload pilots produced:

| Term | Official documents | Exact active-project matches | Presumptively ceremonial | Corrections | Unmatched for substantive review |
| --- | ---: | ---: | ---: | ---: | ---: |
| First term | 1,125 | 3 | 479 | 1 | 642 |
| Second term through July 18, 2026 | 579 | 46 | 105 | 1 | 427 |

These are workload measurements, not issue counts or findings of illegality. An exact match means that the active project corpus already contains the official document identity; it does not establish that the current placement is sufficient. An unmatched record means only that the directive requires the first substantive and independent challenge passes. The review must route it to an existing issue, evidence record, or defined GitHub monitor; create or update one clustered preliminary candidate when a plausible distinct unowned institutional weakness remains; or document why no project action is warranted. The scanner writes only to the existing temporary catalog and routing schemas when `--apply` is deliberately supplied. Normal batch reconciliation removes existing-route and no-action rows while retaining candidate evidence only under an accountable candidate owner.

The substantive and independent challenge passes for both Federal Register batches were completed on July 18. The first-term pass routed **315** records to existing project mechanisms, found **243** warranting no further project action, and retained **84** as evidence for four clustered candidate questions. Together with the completed second-term pass, the reconciliation is:

| Term | Existing project mechanism | No project action | Candidate evidence | Unmatched records reviewed |
| --- | ---: | ---: | ---: | ---: |
| First term | 315 | 243 | 84 | 642 |
| Second term through July 18, 2026 | 219 | 181 | 27 | 427 |
| **Both terms** | **534** | **424** | **111** | **1,069** |

Existing-route and no-action records were not copied into a permanent directive queue. The user promoted all five clustered questions to formal Horizon candidates on July 18, 2026. The 111 supporting directives remain in the canonical catalog and routing files under those formal candidates so the evidence is not orphaned or duplicated:

| Formal Horizon candidate | Supporting directives | Threshold question |
| --- | ---: | --- |
| [`HOR-040`](https://github.com/Thorncrag/ARRP/issues/302) — Safeguards for Broad Presidential Tariff Delegations | 51 | Whether non-IEEPA trade delegations require safeguards beyond those already supplied by trade statutes and review doctrine. |
| [`HOR-041`](https://github.com/Thorncrag/ARRP/issues/303) — Safeguards for Class-Based Presidential Entry Suspensions | 21 | Whether INA section 212(f) contains durable, reviewable safeguards adequate for broad class-entry suspensions. |
| [`HOR-042`](https://github.com/Thorncrag/ARRP/issues/304) — Minimum Safeguards for Presidential Statutory Waivers | 26 | Whether any cross-statutory minimum is justified after comparing each waiver provision's existing safeguards. |
| [`HOR-043`](https://github.com/Thorncrag/ARRP/issues/305) — Presidential Recognition of International Bodies With Domestic Legal Privileges | 1 | Whether executive recognition, participation, and IOIA designation expose an unowned authorization or accountability gap. |
| [`HOR-044`](https://github.com/Thorncrag/ARRP/issues/306) — Statutory Framework for Presidential Cross-Border Infrastructure Permits | 12 | Whether facility types lacking express statutory authority require uniform criteria, procedures, consultation, and review. |

Representative sources retained in the cited-source registry are:

- `HOR-040`: [SRC-1198](https://www.govinfo.gov/content/pkg/FR-2025-02-18/pdf/2025-02832.pdf); [SRC-1199](https://www.govinfo.gov/content/pkg/FR-2025-08-05/pdf/2025-14893.pdf); [SRC-1205](https://www.govinfo.gov/content/pkg/FR-2018-01-25/pdf/2018-01592.pdf); [SRC-1206](https://www.govinfo.gov/content/pkg/FR-2018-03-15/pdf/2018-05478.pdf); [SRC-1207](https://www.govinfo.gov/content/pkg/FR-2018-03-27/pdf/2018-06304.pdf).
- `HOR-041`: [SRC-0909](https://immpolicytracking.org/policies/president-trump-and-uscis-announce-100000-h-1b-fee/); [SRC-1095](https://www.whitehouse.gov/presidential-actions/2025/09/restriction-on-entry-of-certain-nonimmigrant-workers/); [SRC-1096](https://www.courtlistener.com/docket/71541425/global-nurse-force-v-trump/); [SRC-1200](https://www.govinfo.gov/content/pkg/FR-2025-06-10/pdf/2025-10669.pdf); [SRC-1208](https://www.govinfo.gov/content/pkg/FR-2017-02-01/pdf/2017-02281.pdf); [SRC-1209](https://www.govinfo.gov/content/pkg/FR-2019-10-09/pdf/2019-22225.pdf); [SRC-1210](https://www.govinfo.gov/content/pkg/FR-2020-06-04/pdf/2020-12217.pdf).
- `HOR-042`: [SRC-0871](https://immpolicytracking.org/policies/dhs-waives-statutory-requirements-to-expedite-border-wall-projects-in-san-diego-california/); [SRC-0877](https://immpolicytracking.org/policies/dhs-waives-statutory-requirements-to-expedite-border-wall-projects-in-big-bend-sector/); [SRC-0889](https://immpolicytracking.org/policies/dhs-waives-statutory-requirements-to-expedite-border-wall-projects-in-el-paso-yuma-and-tucscon/); [SRC-0943](https://www.federalregister.gov/documents/2026/02/17/2026-02994/determination-pursuant-to-section-102-of-the-illegal-immigration-reform-and-immigrant-responsibility); [SRC-0944](https://www.courtlistener.com/docket/73199706/friends-of-the-ruidosa-church-v-mullin-etal/); [SRC-0995](https://www.whitehouse.gov/presidential-actions/2025/07/regulatory-relief-for-certain-stationary-sources-to-promote-american-security-with-respect-to-sterile-medical-equipment/); [SRC-0996](https://www.courtlistener.com/docket/72197186/cleanaire-nc-v-trump/); [SRC-1201](https://www.govinfo.gov/content/pkg/FR-2025-06-04/pdf/2025-10322.pdf); [SRC-1202](https://www.govinfo.gov/content/pkg/FR-2026-04-23/pdf/2026-08009.pdf); [SRC-1203](https://www.govinfo.gov/content/pkg/FR-2026-07-01/pdf/2026-13408.pdf); [SRC-1211](https://www.govinfo.gov/content/pkg/FR-2017-06-21/pdf/2017-13115.pdf); [SRC-1212](https://www.govinfo.gov/content/pkg/FR-2017-10-23/pdf/2017-23145.pdf); [SRC-1213](https://www.govinfo.gov/content/pkg/FR-2020-02-06/pdf/2020-02473.pdf); [SRC-1214](https://www.govinfo.gov/content/pkg/FR-2017-08-28/pdf/2017-18291.pdf).
- `HOR-043`: [SRC-1204](https://www.govinfo.gov/content/pkg/FR-2026-01-22/pdf/2026-01271.pdf).
- `HOR-044`: [SRC-0931](https://www.courtlistener.com/docket/72241676/state-of-california-v-pipeline-and-hazardous-materials-safety/); [SRC-1215](https://www.govinfo.gov/content/pkg/FR-2019-04-15/pdf/2019-07645.pdf); [SRC-1216](https://www.govinfo.gov/content/pkg/FR-2019-04-03/pdf/2019-06654.pdf); [SRC-1217](https://www.govinfo.gov/content/pkg/FR-2020-08-03/pdf/2020-17040.pdf); [SRC-1218](https://www.congress.gov/crs_external_products/R/PDF/R43261/R43261.11.pdf).

This remains five questions, not 111 proposed issues, and promotion does not admit any area-specific proposal. The first-term material expanded the questions now carried by `HOR-040`, `HOR-041`, and `HOR-042`; it did not add evidence to the second-term-only `HOR-043`; and it created the narrow cross-border-permit question now carried by `HOR-044`. The representative official and congressional sources reside in `sources.csv`, and every supporting directive remains associated with its formal candidate through the catalog and routing records. The preliminary queue and `sources-pending.csv` are empty. REG-003 receives the Ambler Road presidential appellate decision as existing administrative-adjudication coverage rather than a separate candidate. The Federal Register batches are complete; the White House and GovInfo completeness cross-check remains open.

The Federal Register remains the structured discovery backbone and supplies links to official GovInfo PDFs. After the Federal Register batches close, compare the current White House presidential-action collection, the archived first-term White House collection, and GovInfo's Compilation of Presidential Documents for unnumbered or otherwise omitted official actions. Do not create a second directive queue for those sources; route any gap through the same process.

## Preliminary Intake Dispositions

These originated as synthesized preliminary research questions, not Horizon findings. Raw source records did not enter the user console. Each preliminary question stated the possible institutional defect, existing coverage considered, the distinctness rationale, the best counterargument, unresolved questions, and supporting evidence. On July 16, 2026, the user approved all six questions for promotion. They now carry `HOR-032` through `HOR-037` and enter the formal Horizon duplicate, legal, political-failure, and issue-admission workflow; promotion does not admit an area-specific proposal.

### Senior-official Hatch Act enforcement and use of official resources for campaigns

The current inventory has adjacent homes in A-08, OVS-008, and ELEC-012, but no issue expressly owns the enforcement gap when senior White House officials use official authority, personnel, property, communications, or events for campaign activity and ordinary discipline depends on presidential action. The Office of Special Counsel's [report concerning thirteen senior officials and the 2020 Republican National Convention](https://www.osc.gov/news/2021-11-09/osc-issues-hatch-act-report-documenting-violations-by-13-senior-trump-administration-officials-including-at-the-2020-republican-national-convention/) expressly identified violations and enforcement difficulties. This is presently the strongest apparently unowned first-term candidate.

**Next review:** compare the president and vice president exclusions, OSC referral and adjudication authority, post-employment limits, appropriations restrictions, and existing proposals for independent civil enforcement.

**Current treatment:** admitted as [OVS-009](../areas/OVS/issues/OVS-009.md) after cross-administration review showed a distinct senior-official enforcement gap. The fact that covered actors may be presidential appointees does not make this an APPT issue; the asserted defect is the oversight and enforcement route for political-activity restrictions. ELEC-012 and OVS-008 retain campaign-finance and internal-ethics-office questions respectively.

### Accessible presidential and executive communications

The underlying legal duty already exists. [Section 504 of the Rehabilitation Act](https://uscode.house.gov/view.xhtml?edition=prelim&req=granuleid:USC-prelim-title29-section794) prohibits disability-based exclusion from a program or activity conducted by an Executive agency, and Executive Office regulations expressly apply that obligation to the White House Office. In [2020](https://law.justia.com/cases/federal/district-courts/district-of-columbia/dcdce/1%3A2020cv02107/220596/18/) and again in [November 2025](https://clearinghouse-umich-production.s3.amazonaws.com/media/doc/164821.pdf), the U.S. District Court for the District of Columbia found the plaintiffs likely to succeed under that duty and ordered ASL access for specified White House briefings. The renewed dispute is narrower: the government has appealed while arguing that section 504 does not supply an enforceable private cause of action. The [ACLU of D.C. case page](https://www.acludc.org/cases/national-association-of-the-deaf-v-trump-asl-interpretation-during-white-house-press-briefings-protecting-the-rule-of-law-and-separation-of-powers-by-urging-the-d-c-circuit-to-apply-the/) describes that pending appellate question.

**Current treatment:** promoted as [HOR-033](../framework/logs/HORIZON_SCAN_LOG.md) and monitor the appeal. Cross-check HOR-027 because social media or another nontraditional channel may also carry covered presidential communications. Do not treat simple violation of the existing duty as a new institutional defect. Consider admission only if the litigation exposes a recurring enforcement gap, such as the absence of a clear cause of action, materially delayed prospective relief, or unresolved statutory coverage of particular presidential communications.

### Cross-agency repurposing of protected personal data

CIV-009 owns DOGE or another repurposed technical unit's cross-agency systems access; DOM-009 owns law-enforcement surveillance procurement; A-24 owns rights-bearing records and personal privacy. The source catalog also contains data-sharing arrangements that do not necessarily depend on DOGE or surveillance procurement, including administrative records repurposed for immigration or election enforcement. The Horizon log already recognizes that a broader personal-data regime may exceed those homes.

**Next review:** test whether the recurring defect is unauthorized secondary use, purpose incompatibility, interagency matching, bulk disclosure, political use, or absence of an independent approval and audit mechanism. If the defect is merely a DOGE access method, immigration policy, or election manifestation, merge it into the existing homes rather than creating a new issue.

**Current treatment:** promoted as high-priority [HOR-034](../framework/logs/HORIZON_SCAN_LOG.md) for formal duplicate and scope review, with a presumption in favor of expanding CIV-009 or an existing privacy home unless the evidence establishes a broader recurring defect. The danger of personal-information abuse supplies urgency but does not itself establish a separate proposal. This is not principally an appointments issue.

### Review evasion through withdrawal, replacement, settlement, or mootness

The first-term court roundup treats agency withdrawal after suit as an unsuccessful outcome, but a government loss on that coding does not necessarily produce a durable merits precedent or prevent reissuance. The recurring institutional question is whether executive defendants can repeatedly withdraw, replace, narrow, or settle a challenged action after imposing harm and thereby evade merits review.

**Next review:** isolate the catalog's withdrawal and mootness cases, identify whether the voluntary-cessation doctrine supplied review, and check whether JUD-001, JUD-011, REG-006, or a subject-specific remedy already addresses the problem. Admit a separate judicial-review issue only if the pattern is general, repeatable, and not adequately covered.

**Current treatment:** promoted as [HOR-035](../framework/logs/HORIZON_SCAN_LOG.md). Litigation strategy is not inherently an institutional defect; admission requires evidence that review evasion became an egregious or standard practice rather than an isolated litigation choice or lawful correction.

### Executive action that may operate without timely merits review

This candidate concerns a possible sequence rather than a conclusion about the legality of any policy. The executive takes consequential action; an affected party sues; but the court either cannot reach the legality of the action because of standing, jurisdiction, waiver, ripeness, reviewability, or mootness, or declines emergency relief while the merits remain unresolved. The action may then operate long enough to cause harm that a later judgment cannot fully repair.

The present source set illustrates why controlling-opinion review is necessary. *Ramos v. Nielsen* held one Administrative Procedure Act claim unreviewable while rejecting a separate equal-protection claim. *Northern Alaska Environmental Center v. Department of the Interior* included a waiver holding but also some merits analysis. Four other retained records concern denials of a stay or preliminary injunction rather than final approval of executive authority. These are research leads, not proof of one general institutional defect. Records that plainly included merits determinations or had only been placed in broad “manual” or “mixed” text-classification groups have been returned to their subject-specific proposal queues.

**Next review:** read the controlling opinions and determine, case by case, what claim remained untested, what rule prevented a timely merits decision, whether concrete and difficult-to-reverse harm occurred before final review, and whether later merits review supplied an adequate remedy. Only then decide whether any recurring gap belongs in an existing subject proposal, a general judicial-review proposal, or no ARRP proposal at all.

**Current treatment:** promoted as [HOR-036](../framework/logs/HORIZON_SCAN_LOG.md) for controlling-opinion and duplicate review. The six attached cases remain research leads rather than findings that executive conduct was unlawful or wholly unreviewed.

### Immigration detention, removal-process, and access safeguards

The combined immigration sources identify a possible process gap broader than any one substantive immigration policy: civil detention and removal may proceed without uniform access to counsel, prompt custody review, accurate hearing notice, preservation and disclosure of detention evidence, reliable access to adjudication, or sufficiently effective relief when officials disregard judicial commands. RIGHTS-002 owns TPS, asylum access, and humanitarian reviewability; DOM-001 owns domestic deployment authority; REG-003 owns administrative-adjudication control; JUD-001 owns enforcement of judicial commands; and HOR-010 owns courthouse-access chilling.

The constitutional inquiry begins from personhood, not citizenship. The Fifth and Fourteenth Amendments protect “persons,” and [*Plyler v. Doe*](https://www.govinfo.gov/content/pkg/USREPORTS-457/pdf/USREPORTS-457-202.pdf) recognizes that people physically present within a state, including people unlawfully present, are protected by due process and equal protection. The Court connected protection to obligation under the civil and criminal laws. The remaining work is to identify the precise scope of each protection and any claim-specific distinction involving citizenship, initial admission, territory, custody, or status—not to entertain a general theory that noncitizens lack constitutional rights.

**Next review:** determine whether those existing homes can collectively address the problem without fragmentation, or whether a narrow minimum-process and detention-accountability proposal is needed. Begin with person-based due-process and equal-protection guarantees; identify any limited doctrinal distinction claim by claim; and do not treat disagreement with immigration enforcement policy itself as an institutional defect.

**Current treatment:** promoted as high-priority [HOR-037](../framework/logs/HORIZON_SCAN_LOG.md) for constitutional, statutory, duplicate, and scope review.

## Existing Coverage That Should Not Be Recreated

The first scan already shows substantial overlap with developed or inventoried ARRP work. Examples include:

- independent-agency control and functional dismantling — REG-001 and related REG issues;
- spending freezes, grant conditions, and congressional-mandate nullification — A-11, FED-003, A-19, and JUD-011;
- election interference and voter-data demands — A-02;
- immigration status, asylum, birthright citizenship, removal process, and records — RIGHTS-002, RIGHTS-003, A-14, and A-20;
- retaliatory investigations, prosecutions, grants, contracts, access, or clearances — A-01 and A-19;
- civil-service reclassification, agency hollowing, and DOGE-style operational control — A-08;
- records deletion, website removal, scientific suppression, and misleading official information — A-13 and A-18;
- press access, compulsory process, regulatory coercion, and public-media funding — A-22;
- domestic deployments, enforcement evidence, and surveillance systems — A-14;
- emergency tariffs and sanctions used as substitutes for legislation — EMERG-003;
- conflicts of interest, government patronage, foreign benefits, and affiliated entities — A-06; and
- court-order enforcement and public notice of executive noncompliance — JUD-001 and JUD-005.
- unofficial or inadequately supervised governmental representatives — APPT-004, including the integrated HOR-028 source record.

An action that fits one of these lanes should normally become a manifestation, source lead, litigation-status update, or reason to refine an existing remedy—not a new issue.

## Next Source-Universe Pass

1. Cross-check the completed Federal Register presidential-directive batches against the current White House presidential-action collection, the archived first-term White House collection, and GovInfo's Compilation of Presidential Documents. Deduplicate any omissions against existing project records before substantive review. An unmatched operative directive that plausibly exposes a distinct unowned institutional weakness creates or updates one clustered preliminary candidate; ceremonial, routine, political-only, duplicative, and no-additional-value material leaves no retained directive queue.
2. Work retained sources by their accountable owner: verify primary materials, strengthen an issue page when a material premise needs better support, route corroborated media episodes to the appropriate issue or evidence record, and attach external predicates to the owning GitHub monitor. A genuinely unowned institutional weakness creates or updates one preliminary candidate rather than an orphaned source record.
3. Begin recurring review from the GitHub Project Monitoring view and each issue-linked monitor. When its defined posture predicate occurs, update the [source-and-posture ledger](trump-administration-litigation-monitoring.csv) and the owning issue or evidence record; do not treat open allegations or preliminary relief as final manifestations.
4. Ingest official findings from GAO, OSC, inspectors general, congressional reports, and published judicial noncompliance records so the source universe is not litigation-plaintiff biased.
5. Ingest specialist ethics, conflicts, records, environmental, civil-rights, election, appointments, and war-powers sources from the completeness ledger, and continue the two-source media lane across both terms.
6. Apply the full ARRP duplicate and issue-admission tests only after source and posture normalization. No catalog, media, or directive record should become a formal proposed candidate automatically; a source-supported preliminary candidate remains subject to human review and the ordinary promotion workflow.

## Maintenance Rule

Future catalog refreshes should retain a dated `last_checked` field and source-family identifier. Add or update source-normalized records first, then complete route-centered adjudication before treating the refresh as integrated. Preserve independently useful source URLs when several reports are consolidated into one action; remove cumulative records only after the canonical source and qualitative placement decision are documented.
