---
issue_id: FUND-001
area_id: A-11
title: "Addressing Executive Order Abuse"
status: developed
priority: medium
remedy_type: federal-legislation
legislative_status: working-draft
legislative_proposal: "../../../legislation/JUD-011.md"
alternative_legislative_proposal: "../../../legislation/FUND-001.md"
audit_status: "T1 complete; JUD-011 cross-issue consistency Change Audit complete; full T2 development audit pending"
audit_score: 60
audit_last_type: "JUD-011 cross-issue consistency Change Audit"
audit_last_date: "2026-07-13"
audit_next: "Full T2 development audit"
audit_rubric_version: "2026-06-27.2"
audit_rebaseline_status: "current"
change_audit_needed: false
change_audit_reason: null
adoption_score: 3
adoption_friction_score: 82
adoption_friction_band: "Extreme Resistance"
required_electoral_environment: "sixty-vote-senate"
pathway_viability: "plausible-after-wave"
development_priority: "active"
pathway_adjustment: "stage"
print_levels:
  - public-proposal
  - full-technical
audit_history: "FUND-001.audit.md"
---

# FUND-001 — Addressing Executive Order Abuse

> ## Issue Snapshot
> **Problem:** Executive orders can convert unlawful nonexecution into facts on the ground.<br />**Repair:** Enforce enacted mandates before unlawful directives create irreversible facts.<br />**Vehicle:** [Interbranch Review Framework Act (JUD-011)](../../../legislation/JUD-011.md) alone (preferred); standalone [FUND-001](../../../legislation/FUND-001.md) (independent alternative).
>

## Institutional Anomaly

Executive orders and presidential memoranda can be lawful tools for supervising the executive branch, coordinating agency action, and implementing statutes. The structural danger arises when executive directives are used to evade Congress, suspend statutory programs, redirect or withhold appropriated funds, condition grants for partisan or ideological purposes, or create operational facts before courts or Congress can respond.

Direct regulation of the President's issuance of executive orders would raise serious Article II and separation-of-powers questions. The more durable statutory hook is Congress's power of the purse. A presidential directive may exist as an internal instruction, but agencies should not be able to use appropriated funds, apportionment authority, grant administration, program execution, or nonspending to implement a pattern of directives that courts or the Comptroller General have already identified as unlawful.

FUND-001 therefore treats repeated unlawful covered executive directives as an appropriations-control problem. The proposal does not nullify executive orders as presidential speech or internal management documents. It makes new covered directives and continuing implementation of lookback-period covered directives temporarily fiscally inert after an objective trigger, unless the implementing agency and OMB identify lawful statutory authority and survive an expedited review path.

## Manifestations of the Failure

### Executive-order implementation as de facto lawmaking

An executive order may purport to reorder spending, program eligibility, enforcement capacity, or grant conditions in ways Congress did not authorize. Even if the order is later held unlawful, agencies may have already frozen funds, delayed benefits, redirected personnel, closed programs, or coerced recipients.

### Impoundment by directive rather than by formal rescission or deferral

The Impoundment Control Act already regulates rescissions and deferrals, but a President may try to achieve similar effects through directives framed as policy review, apportionment management, grant-condition revision, emergency implementation, legal-position review, or agency reorganization. This can turn nonspending into a practical veto of statutory programs.

### Repeated unlawful directives without escalating consequence

Ordinary litigation can stop a single unlawful action, but it may not address a pattern. If several covered executive directives are found unlawful, the legal system has identified a repeat institutional failure. A repeated-failure trigger should not require impeachment before Congress can protect later appropriations from similar abuse.

### First-day directives and continuing implementation

Presidents often issue numerous executive orders at the beginning of a term. A purely prospective trigger would leave first-day directives untouched even if later legal findings reveal a pattern of unlawful directive-based implementation. FUND-001 therefore requires a lookback review for covered directives issued earlier in the same presidential term that continue to affect appropriated funds, statutory programs, grants, benefits, apportionments, or agency operations after the trigger. The lookback mechanism does not retroactively void executive orders or unwind completed actions automatically; it requires continued implementation to be certified, narrowed, paused, or reviewed.

### Executive-order volume and judicial-review comparator

**Important note:** The project would strongly prefer to include metrics evenly across all administrations. This would be an incredibly useful comparison in investigating abuse of executive orders. However, no public-facing source has yet been identified that directly tabulates executive-order-specific unlawfulness across administrations. The currently identified sources instead support narrower comparator tracks: CRS provides nationwide-injunction counts for the first Trump and Biden administrations, AttorneysGeneral.org provides a structured multistate-litigation database with administration and injunction fields, Ballotpedia provides a Biden-era multistate-litigation routing source, and the AP figure provides a second-Trump-administration court-blocking proxy.

The project was able to locate some reliable data tracking nationwide injunctions issued in response to orders across administrations going back to George W. Bush. Therefore, the project provisionally offers nationwide injunctions as a potentially useful analog in analyzing the lawfulness of issued orders.

Injunctions issued during the second Trump administration were not specifically tabulated from available sources. The project intends to tabulate this so that a direct comparison can be made. Until such time, the project treats the data presented as still useful in analyzing this issue. The project will continue to present data for the Trump administration regardless because it still serves as a concrete manifestation of the problem described.

| President | EO count | Injunction count | Unlawful |
| --- | ---: | ---: | ---: |
| Clinton | 364 | TBD | TBD |
| George W. Bush | 291 | 12† | TBD |
| Obama | 277 | 19† | TBD |
| Trump, first term | 220 | 86 | TBD |
| Biden | 162 | 28 | TBD |
| Trump, second term* | 267 | TBD | 70 |

#### Sources and notes ####
* *_Accessed June 29, 2026; AP proxy as of May 1, 2025_
* †_For George W. Bush and Obama, CRS does not provide appendix counts in the reviewed report; the table uses the higher DOJ-cited count reported by CRS. CRS also cites lower Harvard Law Review counts for those administrations._
* EO counts come from the [Federal Register executive-order disposition tables](https://www.federalregister.gov/presidential-documents/executive-orders). 
* Injunction counts use CRS appendix counts from [Nationwide Injunctions Under the First Trump Administration and the Biden Administration](https://www.congress.gov/crs-product/R48467) where available. AttorneysGeneral.org's [State Lawsuits Database](https://attorneysgeneral.org/multistate-lawsuits-vs-the-federal-government/list-of-lawsuits-1980-present/) is retained as a structured case-level audit source, with [data-collection methods](https://attorneysgeneral.org/data-collection-methods/) defining the multistate-lawsuit dataset. A June 29, 2026 quick scan of the May 25, 2025 table data identified, among multistate Biden-administration rows, 23 national injunctions issued, 23 local injunctions issued, and 2 pending injunction motions. That figure is not substituted into the table because it is broader than the CRS nationwide-injunction count and still requires case-level normalization. Ballotpedia's [Biden multistate-lawsuit tracker](https://ballotpedia.org/Multistate_lawsuits_against_the_federal_government_during_the_Biden_administration) is retained as an additional routing source for checking Biden-era injunction and status coding, but it has not yet been normalized into an EO-specific numerator.
* The Trump second-term proxy comes from the Associated Press report [Trump's agenda faces courtroom setbacks as Justice Department lawyers struggle to win over judges](https://apnews.com/article/5522245bc2140579d39a0a825b6db7af).

### Unified-government oversight collapse

If the President's party controls Congress or key committees, oversight, appropriations riders, subpoena enforcement, contempt, and impeachment may fail as practical checks. The absence of political enforcement makes neutral, rule-bound, court-accessible appropriations safeguards more important.

### Emergency and federalism spillovers

Emergency powers, disaster aid, infrastructure funds, civil-rights grants, and state-administered programs can be vulnerable to directive-based conditions, delays, or redirections. The same impoundment mechanism can become a tool for coercing states, local governments, universities, contractors, or beneficiaries.

## Resulting Damage

Executive-order abuse through impoundment damages Congress's power of the purse, statutory program reliability, federalism, equal administration, and democratic accountability. It lets the executive branch obtain time-sensitive policy results before legality is resolved, burdens states and private parties with emergency litigation, and can make judicial victory incomplete because funding, staffing, deadlines, or institutional capacity have already been disrupted.

## Underlying Weakness

Existing law may lack:

- a pattern-based trigger for repeated unlawful executive directives;
- a clear rule that covered directives become fiscally inert as to their scope after the trigger;
- a lookback rule for continuing implementation of earlier covered directives issued in the same presidential term;
- a prohibition on spending, withholding, delaying, apportioning, reprogramming, or conditioning funds to implement a covered directive during the review period;
- OMB-specific duties for apportionment, deferral, and legal-authority certification;
- expedited review for states, congressional institutional plaintiffs, affected recipients, and program beneficiaries;
- a remedy that prevents both spending to implement unlawful directives and nonspending to effectuate them;
- safe-harbor protection for officials who refuse to implement directives that lack statutory authority during the review period.

## Proposal Survey

The existing statutory foundation is the Impoundment Control Act of 1974. Rescission proposals are governed by [2 U.S.C. § 683](https://www.law.cornell.edu/uscode/text/2/683), and deferrals are governed by [2 U.S.C. § 684](https://www.law.cornell.edu/uscode/text/2/684). The Comptroller General may bring a civil action to enforce release of budget authority under [2 U.S.C. § 687](https://www.law.cornell.edu/uscode/text/2/687).

The Supreme Court has rejected presidential nonspending where Congress directed funds to be allotted. In [*Train v. City of New York*](https://supreme.justia.com/cases/federal/us/420/35/), the Court held that the executive could not frustrate the will of Congress by allotting less than the statutory formula required. In [*Youngstown Sheet & Tube Co. v. Sawyer*](https://supreme.justia.com/cases/federal/us/343/579/), the Court rejected an executive order that lacked statutory or constitutional authority and conflicted with Congress's allocation of power.

The proposal draws from those sources but adds a new pattern-response mechanism. The closest functional analogue is not a legislative veto of executive orders. It is an appropriations rule: after repeated unlawful covered directives, new covered directives and continuing implementation of lookback-period covered directives may not be funded, used to withhold funds, or implemented through apportionment unless lawful authority is publicly certified or expedited review permits implementation.

Lisa Manheim and Kathryn A. Watts's article [Reviewing Presidential Orders](https://lawreview.uchicago.edu/print-archive/reviewing-presidential-orders) provides an important scholarly frame for this proposal. The article explains that presidents increasingly rely on executive orders and other unilateral written directives to influence agency policymaking, while courts lack a coherent framework for direct review of presidential orders. It also distinguishes the traditional route of challenging agency implementation under administrative-law doctrines from newer direct challenges to presidential orders. FUND-001 uses that distinction by regulating agency implementation and appropriated funds rather than attempting to invalidate presidential orders directly.

## Least-Complex Adequate Remedy

The preferred remedy is the [Interbranch Review Framework Act (JUD-011)](../../../legislation/JUD-011.md) alone because its generally applicable anti-nullification claim reaches substantial and sustained executive displacement of enacted appropriations and program mandates without a subject-matter opt-in. If Congress rejects that general framework, the least-complex independent alternative is FUND-001: federal legislation amending the Impoundment Control Act and related appropriations-enforcement rules. A constitutional amendment should be reserved only if Congress seeks to directly invalidate executive orders, impose presidential disabilities, or regulate the President's issuance authority rather than agency implementation and appropriated funds.

## Repair and Prevention

Congress should create an **Executive Directive Impoundment Review** regime.

The statute should:

1. define covered executive directives to include executive orders, presidential memoranda, OMB directives, and other presidential or Executive Office instructions that materially affect appropriated funds, statutory program execution, grants, benefits, apportionment, reprogramming, enforcement capacity, or state-administered programs;
2. define trigger findings to include final court judgments, three-judge-court determinations, and Comptroller General findings that a covered directive or covered implementation action was unlawful;
3. activate a temporary review period after a specified number of trigger findings within a defined time window;
4. make new covered directives fiscally inert as to their covered scope during the review period;
5. require lookback review of continuing implementation actions under earlier covered directives issued in the same presidential term;
6. prohibit agencies and OMB from obligating, expending, withholding, delaying, deferring, apportioning, reprogramming, or conditioning funds to implement a covered directive unless the statutory process is satisfied;
7. require a public legal-authority certification from OMB and the implementing agency;
8. provide expedited three-judge review with D.C. Circuit appeal and certiorari review;
9. preserve emergency implementation only for narrow, time-limited, certified circumstances;
10. protect officials who decline implementation where the directive lacks required certification or review clearance;
11. preserve ordinary executive orders that do not affect appropriations, statutory program execution, or covered democratic/federalism structures.

## Proposed Legislation

### Primary remedy — enact the Interbranch Review Framework Act (JUD-011) alone

- [Interbranch Review Framework Act (JUD-011)](../../../legislation/JUD-011.md)

The Interbranch Review Framework Act (JUD-011) itself supplies the cause of action, eligible-plaintiff rules, anti-nullification threshold, D.D.C. forum, relief, and appellate procedure. It applies because the alleged executive conduct meets that general statutory test, not because FUND-001 opts in or is enacted.

### Independent legislative alternative — enact FUND-001 alone

- [FUND-001 — Executive-Order Abuse Impoundment Control Act](../../../legislation/FUND-001.md)

FUND-001 is a complete appropriations-specific remedy Congress may enact if it rejects the Interbranch Review Framework Act (JUD-011). It independently supplies the trigger, fiscal-inertness rules, certification process, cause of action, plaintiffs, relief, three-judge D.D.C. procedure, and D.C. Circuit review. It does not rely on JUD-011 or another ARRP proposal.

## Interbranch Review Pathways

> **Preferred remedy:** Enact the Interbranch Review Framework Act (JUD-011) alone. Its coverage is automatic across subject matters when executive conduct substantially and sustainably nullifies an enacted mandate.<br />**Independent alternative:** Enact FUND-001 alone. Section 1026 supplies its own three-judge D.D.C. panel, temporary relief, expedition, remedies, and D.C. Circuit review.<br />**Congressional choice:** These are separate enactment choices, not two modes of FUND-001. Neither bill activates or depends on the other.

## Relationship to Adjacent Proposals

- **FUND-002** concerns pocket rescissions and strategic delay. FUND-001 owns the repeated-unlawful-directive trigger and fiscal-inertness mechanism.
- **FUND-003** concerns agency closure or program nullification through nonspending.
- **FUND-004** concerns politically selective withholding of grants or aid.
- **EMERG-002** concerns emergency authority used to redirect appropriated funds.
- **CONG-008** concerns partisan collapse of oversight under unified government.
- **FED-003** concerns coercive grant conditions imposed on states or local governments.
- **JUD-001** concerns judicial enforcement after a court has issued an order requiring executive compliance.
- The **Interbranch Review Framework Act (JUD-011)** is the preferred general anti-nullification remedy and applies without subject-matter designation. FUND-001 is a separate, complete appropriations-specific alternative.

## Budgetary Impact Statements

### Preferred remedy — Interbranch Review Framework Act (JUD-011)

The Interbranch Review Framework Act (JUD-011) carries the two additional D.D.C. judgeships and the startup, national-roster, clerk, facilities, technology, secure-record, special-master, emergency-administration, and operating costs of the preferred general remedy. FUND-001 adds no separate judicial apparatus under this path. OMB, agency, GAO, fiscal-release, compliance, and program-restoration costs depend on the underlying dispute and are not included in the Act's judicial appropriation.

### Independent alternative — standalone FUND-001

The independent FUND-001 bill must separately account for OMB, agency, GAO, congressional-notice, compliance-monitoring, fiscal-release, and three-judge-court costs. It does not create a new benefits program or presently specify a standing appropriation; T2 should determine whether a protected judicial-administration appropriation is required.

*Note: Preliminary ARRP assessment only; not a CBO, OMB, agency, or legislative-counsel score.*

## Proposal Scoring

> **Proposal Quality Score:** **[60 / 100](FUND-001.audit.md)** (Developed Draft)<br />**Adoption Score:** 3 / 12 (Weak Adoption Basis)<br />**Adoption Friction:** 82 / 100 (Extreme Resistance)<br />**Required Electoral Environment:** `sixty-vote-senate`<br />**Development Priority:** `active`
>
> —
>
> **Audit Status:** T1 complete; JUD-011 cross-issue consistency Change Audit complete; full T2 development audit pending<br />**Last Audit:** JUD-011 cross-issue consistency Change Audit (2026-07-13)<br />**Rubric Version:** `2026-06-27.2`; **Rebaseline:** `current`<br />**Change Audit:** Current for JUD-011 coverage, the standalone alternative, and both budget pathways<br />**Next Audit:** Full T2 development audit<br />**Full Audit History:** [FUND-001 audit history](FUND-001.audit.md)

## Annotation

**Naming.** The issue is named for executive-order abuse, not merely impoundment, because the institutional defect is directive-based executive circumvention. The legal hook remains appropriations and impoundment because direct statutory nullification of executive orders would raise harder constitutional questions.

**No Blanket Nullification.** The proposal does not declare executive orders void. It makes new covered directives, and continuing implementation of lookback-period covered directives, fiscally inert as to their covered scope during a review period. The President may still issue orders; agencies may not use or withhold appropriated funds to implement covered directives without satisfying the statutory process.

**Lookback Review.** The lookback rule addresses first-day or early-term executive orders that are already in force when the trigger occurs. It should apply only to ongoing or future covered implementation actions, not automatically unwind completed acts or vested third-party rights. The draft uses a 30-day inventory deadline, 90-day certification deadline, and 180-day fiscal-inertness backstop for continuing implementation, while blocking new covered implementation under lookback directives unless certified. T2 should test whether those periods are sufficient for agency review, state and grantee reliance interests, expedited litigation, and judicial capacity.

**Objective Trigger.** The trigger should rest on external legal findings, not partisan congressional accusation alone. T2 should test whether final judgments, three-judge-court determinations, preliminary injunctions after merits findings, Comptroller General decisions, or combinations of those findings are the right trigger inputs.

**Appropriations Hook.** The strongest statutory authority is Congress's control over appropriated funds, program terms, apportionment conditions, and agency implementation. The draft should avoid overclaiming Congress's ability to regulate the President's issuance of executive orders directly.

**Emergency Exception Risk.** Any emergency exception must be narrow. A broad exception could swallow the rule by allowing the same administration that triggered review to recast covered directives as urgent program-management decisions.

**Standing and Review.** T2 should test who may sue, whether GAO may initiate enforcement, whether either House or designated congressional officers may sue, and whether states, grantees, beneficiaries, contractors, and program administrators have adequate causes of action.

**Preferred and Independent Remedies.** The Interbranch Review Framework Act (JUD-011) alone is the preferred general remedy; it does not require FUND-001 to opt in. FUND-001 is the independent alternative and now contains no JUD-011 routing or dependency. Its own cause of action, plaintiff categories, trigger, fiscal-inertness rules, emergency exception, three-judge D.D.C. procedure, relief, and expedited D.C. Circuit review operate if Congress enacts FUND-001 by itself.

**Quality Score.** The 60/100 score is an initial development score under rubric `2026-06-27.2`: Structural 8/8; Evidence 6/12; Legal Fit 6/10; Prior-Proposal 4/8; Remedy 8/12; Implementation 5/8; Abuse Resistance 6/8; Drafting 5/8; Cogency 6/6; Adoption 3/12; Project Integration 4/4; External Review 0/4; Penalties 0. The issue has a coherent statutory hook, issue framework, draft vehicle, neutral executive-order-volume manifestation, a judicial-review comparator scaffold, and a strong scholarly source for the presidential-order review gap, but T2 must verify existing-law fit, GAO enforcement mechanics, statutory standing, Youngstown/Train doctrine, Chadha constraints, OMB apportionment practice, emergency exceptions, implementation burden, public-support evidence, and prior legislative analogues.

**Adoption Friction.** The 82/100 score is Extreme Resistance because the proposal responds to presidential abuse of executive orders, constrains OMB and agency implementation after repeated unlawful conduct, may be opposed by presidents of both parties, and would likely draw separation-of-powers, standing, expedited-review, emergency-authority, and appropriations-process objections.

**Required Electoral Environment.** The required environment is `sixty-vote-senate`, with Pathway Viability `plausible-after-wave` and Pathway Adjustment `stage`. A narrower first stage could focus on appropriations, grant conditions, OMB apportionment, GAO reporting, and expedited review without activating the full pattern-trigger regime.
