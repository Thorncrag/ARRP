---
issue_id: ELEC-011
title: "Algorithmic Redistricting Baseline and Representation Safeguards — Audit History"
source_issue: "ELEC-011.md"
print_levels:
  - full-technical
---

# ELEC-011 — Audit History

This file preserves the full audit history for [ELEC-011](ELEC-011.md). The issue page keeps only the compact Proposal Scoring summary.

## Audit History

### 2026-07-04 — T2 development audit

**Audit tier:** T2: Development audit

**Audit status:** T2 development audit complete; doctrinal, algorithmic, implementation, adoption, and external-review work still needed

**Proposal-quality score:** 70/100 (Substantially Developed Draft)

**Component score under rubric 2026-06-27.2:** Structural 8/8; Evidence 8/12; Legal Fit 7/10; Prior-Proposal 6/8; Remedy 9/12; Implementation 6/8; Abuse Resistance 7/8; Drafting 6/8; Cogency 6/6; Adoption 3/12; Project Integration 4/4; External Review 0/4; Penalties 0.

**Audit scope:** Reviewed ELEC-011 issue page, audit history, model State act, reserve constitutional amendment, reserve Federal enabling act, source inventory, current audit tracker, and current public sources for Iowa redistricting law, redistricting doctrine, state voting-rights-law comparators, and algorithmic redistricting research. This was not a qualified legal review, legislative-counsel review, technical implementation review, or budget score.

**Primary-law verification:** T2 verified Iowa Code chapter 42 as the strongest public state-law analogue for ELEC-011's least-complex model-law path. Iowa law assigns plan preparation to the Legislative Services Agency, uses census data, requires public bill/map/population-deviation information, contemplates up-or-down votes with only corrective amendments for the first two plans, sets population, political-subdivision, contiguity, and compactness standards, and prohibits drawing districts to favor a party, incumbent, person, group, or to augment or dilute language-minority or racial-minority voting strength. Iowa Code section 42.4 also bars use of incumbent addresses, party-registration data, previous election results, and demographic information beyond population head counts except as required by federal law.

**Doctrine verification:** T2 verified official Supreme Court sources for the main doctrinal frame. *Rucho v. Common Cause* makes federal partisan-gerrymandering claims nonjusticiable while recognizing that state law, independent commissions, and Congress remain possible reform paths. *Arizona State Legislature v. Arizona Independent Redistricting Commission* supports state-law use of independent redistricting institutions for congressional redistricting. *Allen v. Milligan* and *Louisiana v. Callais* together require ELEC-011 to preserve lawful representation safeguards while avoiding race-predominant or insufficiently tailored districting rationales.

**State voting-rights-law comparator finding:** T2 verified official California, New York, and Washington statutory comparators. California Elections Code sections 14025-14032 supplies an at-large vote-dilution model with district-based remedies. New York Election Law section 17-206 supplies broader voter-suppression, vote-dilution, redistricting-remedy, public-hearing, and court-retention provisions. Washington chapter 29A.92 RCW supplies protected-class equal-opportunity standards and court-supervised district-based remedies. These sources support preserving state voting-rights laws as protective floors, but they also confirm why ELEC-011 needs careful language preventing state-law remedies from becoming a broad bypass around the neutral-baseline requirement.

**Algorithmic evidence finding:** T2 added Wang and Merrill's 2025 Iowa computational-redistricting paper as a current technical source lead. The paper supports transparent, nonpartisan computational baselines and simulation-based review, but it does not validate any single deterministic algorithm as a ready statutory default. The 2007 shortest-splitline paper remains a source-development lead only.

**Drafting defect corrected:** Corrected duplicate subsection lettering in the model State act's permissible-deviation section by changing the second subsection (e), Burden of explanation, to subsection (f).

**Score effect:** Score increased from 60 to 70. Evidence increased because T2 replaced several T1 source leads with reviewed primary or official sources. Legal Fit increased because the doctrine frame is now directly grounded in official Supreme Court opinions. Prior-Proposal and Implementation increased because Iowa, California, New York, and Washington provide direct or functional state-law analogues. Drafting remains below full credit because the algorithm-selection standard, review-body adaptation provisions, judicial fallback details, and state constitutional fit still need state-by-state legal drafting.

**Remaining limits:** ELEC-011 remains below Review Ready. It still needs a T3 legal-durability and implementation audit; stronger algorithm-selection and technical-governance sources; representative state implementation comparison beyond Iowa, California, New York, and Washington; state constitutional adaptation notes; court-remedy and standing refinement; public-records and open-meetings review; cost/workload data; proposal-specific adoption evidence; and qualified election-law, voting-rights, state-legislative, technical, and legislative-counsel review.

**Next audit need:** Run T3 legal-durability and implementation audit focused on algorithm selection, VRA/state-VRA tailoring, state constitutional fit, judicial fallback, costs, adoption evidence, and whether the model State act should include optional state-specific drafting brackets.

**Audit process feedback:** This T2 audit usefully moved ELEC-011 out of purely structural status, but the proposal should not be treated as publication-ready. Future work should resist overclaiming algorithmic neutrality and should document exactly which data, criteria, and review body a State would use.

### 2026-06-29 — T1 framework check

**Audit tier:** T1: Framework check

**Audit status:** T1 framework check complete; T2 development audit needed

**Proposal-quality score:** 60/100 (Developed Draft); rebaseline status changed from `hard-rebaseline-needed` to `current`

**Component score:** Structural 8/8; Evidence 6/12; Legal Fit 5/10; Prior Proposal 4/8; Remedy 8/12; Implementation 5/8; Abuse Resistance 6/8; Drafting 5/8; Cogency 6/6; Adoption 3/12; Project Integration 4/4; External Review 0/4; Penalties 0.

**Audit scope:** Reviewed `framework/FRAMEWORK.md`, `framework/METHODOLOGY.md`, `framework/REMEDY_FRAMEWORK.md`, ELEC-011 issue page, model State act, reserve constitutional amendment, reserve enabling act, sibling audit history, audit dashboard, contents inventory, audit inventory, issue inventory, source inventory, and focused local links. Conducted a T1-level current-source refresh for obvious mootness, material reframing, pending judicial vulnerability, and current source leads.

**Framework compliance:** ELEC-011 has the required developed-issue architecture, Issue Snapshot, titled manifestations, proposal survey, least-complex adequate remedy, repair/prevention section, linked model State act, linked reserve amendment, linked reserve enabling act, Budgetary Impact Statement, Proposal Scoring box, annotation, source notes, print metadata, audit sidecar, inventory rows, and dashboard row.

**Issue-to-vehicle alignment:** No material discrepancy was found at T1. The issue page, model State act, amendment, and enabling act are aligned on the core structure: neutral algorithmic first-draft map, public and narrowly tailored deviations, prohibited political data, representation-safeguard review, public comment, judicial fallback, mid-decade redistricting limits, and reserve amendment/enabling-act posture.

**Defects corrected during audit:** Fixed the ELEC-011 `contents.csv` row by quoting the notes field so commas do not split the row into extra CSV fields. Updated issue-page audit metadata, Proposal Scoring, `audits.csv`, and the dashboard to reflect a completed T1 audit rather than a placeholder score.

**Current-status and mootness check:** No obvious T1-level source found that makes ELEC-011 moot or materially obsolete as a standalone proposal. The proposal remains live because redistricting discretion, Voting Rights Act interaction, racial-gerrymandering doctrine, partisan-gerrymandering justiciability, and state-by-state redistricting design remain active structural issues.

**Pending judicial vulnerability check:** T1 did not identify a dispositive pending case that requires pausing ELEC-011, but the check remains incomplete at T1. T2 should specifically verify current Supreme Court and lower-court redistricting dockets, any post-*Louisiana v. Callais* remedial litigation, and pending cases affecting racial-gerrymandering, Voting Rights Act Section 2, independent commission authority, and state legislative districting.

**Source record reviewed:** Existing source-inventory rows include *Louisiana v. Callais* as a primary Supreme Court source, NCSL's redistricting-commission summary as a partial policy reference, the 2007 shortest-splitline paper as a technical source-development lead, and secondary reporting on public and state-response salience. T1 did not add new source rows because no new source was relied on for audit credit.

**Unresolved source findings:** T2 should verify Iowa statutory mechanics from primary Iowa law; compare independent and advisory commission models; locate current state voting-rights act examples; source anti-mid-decade redistricting rules; verify judicial fallback authority and three-judge-court routing; locate stronger algorithmic redistricting scholarship; and check state public-records/open-meetings fit.

**Legal-fit risks:** The reserve constitutional amendment is directionally justified only as a reserve pathway. T2 must test Article I, Section 2; Article I, Section 4; Article V; the Fourteenth and Fifteenth Amendments; *Rucho*; *Arizona State Legislature*; *Reynolds*; *Allen*; *Callais*; anti-commandeering doctrine; state-legislative-district reach; and whether the constitutional-consistency clause is precise enough.

**Remedy and drafting risks:** The model State act remains the least-complex adequate remedy at T1. The reserve amendment and enabling act should remain secondary unless later source and legal review show state-by-state reform is inadequate. Drafting issues for T2 include algorithm selection standards, standing, judicial fallback, State voting-rights law limits, transition timing, rulemaking assignments, certification repositories, and whether the constitutional amendment should mention any additional existing constitutional provisions.

**Adoption and friction finding:** Required Electoral Environment remains `state-level-pathway`; Pathway Viability remains `state-by-state`; Development Priority remains `active`; Pathway Adjustment remains `model-law-with-reserve-amendment`. Adoption Score is 3/12 (Weak Adoption Basis) because T1 found a plausible model-law pathway but no verified proposal-specific polling, state enactment momentum, sponsor coalition, referendum evidence, or stakeholder support. Adoption Friction remains 80/100 (High Resistance).

**International-support and foreign-relations score:** `N/A` at T1. ELEC-011 concerns domestic redistricting structure; comparative democratic practice may be useful at T2/T3, but no current international assessment was performed or credited at T1.

**Next audit need:** Run T2 development audit focused on authoritative source verification, existing-law fit, direct and functional prior-proposal review, legal and judicial-scrutiny analysis, state implementation feasibility, algorithmic-method evidence, adoption/support evidence, and budget/workload analogues.

**Audit process feedback:** T1 was sufficient to convert the placeholder score into a current formula score and catch an inventory formatting defect. It was not sufficient for meaningful legal verification or adoption scoring. The next audit should spend less time on structure and more time on primary state-law sources, redistricting doctrine, and current proposal/support evidence.

### 2026-06-29 — Constitutional-consistency clause added

**Audit status:** Initial developed draft; T1 framework check pending

**Proposal-quality score:** 60; unchanged

**Scope:** Added a relation-to-existing-constitutional-provisions section to the reserve constitutional amendment and mirrored the construction rule in the reserve enabling act and issue-page annotation.

**Score effect:** No score change because no T1 framework check has been run. The change improves constitutional drafting clarity but requires legal review.

**Substantive note:** The amendment now states that it supersedes inconsistent redistricting authority, including authority otherwise exercised under article I, section 4, only to the extent of inconsistency. It also preserves unrelated constitutional structures, including apportionment of Representatives among States, Representative qualifications, Senate composition and equal suffrage, and other constitutional provisions except where enforcement of the neutral-baseline article expressly requires otherwise.

**Next audit need:** T1/T2 should test whether the relation clause is sufficiently precise, whether it should expressly mention Article I, Section 2 or the Fourteenth Amendment, and whether the state-legislative-district reach is best justified through the amendment's own text, the Fourteenth Amendment background, or both.

### 2026-06-29 — Transition-delay loophole tightening

**Audit status:** Initial developed draft; T1 framework check pending

**Proposal-quality score:** 60; unchanged

**Scope:** Tightened the reserve constitutional amendment, reserve enabling act, and issue-page annotation to prevent Congress from using an election-underway transition clause as an indefinite postponement device.

**Score effect:** No score change because no T1 framework check has been run. The change improves abuse resistance and implementation clarity but remains pending source verification and legal review.

**Substantive note:** The drafts now allow transition delay only for an active election cycle where implementation would materially disrupt election administration. The enabling act requires written findings, and both the amendment and enabling act bar repeated, indefinite, or next-cycle deferral.

**Next audit need:** T1/T2 should test whether the transition language is administrable, sufficiently protective of election continuity, and tight enough to prevent Congress from delaying the neutral-baseline requirement beyond the intended transition window.

### 2026-06-29 — State voting-rights law loophole tightening

**Audit status:** Initial developed draft; T1 framework check pending

**Proposal-quality score:** 60; unchanged

**Scope:** Tightened the reserve constitutional amendment, reserve enabling act, model State act, and issue-page annotation to prevent State voting-rights laws from operating as a nullification device for the neutral-baseline requirement.

**Score effect:** No score change because no T1 framework check has been run. The change improves abuse resistance and internal coherence but remains pending source verification and legal review.

**Substantive note:** The drafts now preserve State voting-rights laws as protective floors while requiring any State-law deviation to be consistent with the neutrality framework, public, evidence-based, narrowly tailored, and no broader than necessary to remedy an identified legal or representational injury.

**Next audit need:** T1/T2 should test whether this language properly preserves stronger State voting-rights protections without allowing States to evade the amendment through broad, discretionary, or partisan state-law deviation rules.

### 2026-06-29 — Initial enabling legislation drafting

**Audit status:** Initial developed draft; T1 framework check pending

**Proposal-quality score:** 60; unchanged

**Scope:** Drafted `legislation/ELEC-011.md`, the Neutral Redistricting Baseline Enforcement Act, as reserve Federal enabling legislation tied to the Neutral Redistricting Baseline Amendment. Updated the issue page to distinguish three vehicles: model State legislation as the least-complex path, reserve constitutional amendment, and reserve Federal enabling legislation.

**Score effect:** No score change. The enabling act clarifies the reserve constitutional pathway but does not resolve T1 source verification, proposal-to-legislation alignment, Article V feasibility, Federal enforcement design, rulemaking placement, jurisdiction, standing, or State implementation concerns.

**Substantive note:** The enabling act closely follows the State model's architecture while making its operative authority amendment-dependent. It includes neutral baseline maps, prohibited-data rules, public deviation findings, representation-safeguard review, certification, judicial fallback, mid-decade redistricting limits, Attorney General enforcement, affected-person standing, and a no-waiver rule for the amendment's mandatory neutrality floor.

**Next audit need:** T1 must compare the issue page, State model act, reserve constitutional amendment, and enabling act for alignment. T2 should test Federal jurisdiction, standing, three-judge-court routing, rulemaking assignments, Article V transition rules, Voting Rights Act interaction, independent commission doctrine, anti-commandeering concerns, and whether the amendment and enabling act preserve a genuinely mandatory neutrality floor.

### 2026-06-29 — Initial state legislation drafting

**Audit status:** Initial developed draft; T1 framework check pending

**Proposal-quality score:** 60

**Score basis:** ELEC-011 now has a basic issue framework and linked model state legislation. The initial 60/100 score is a developed-draft placeholder pending T1 and formula rebaseline. It should not be treated as comparable to audited developed proposals until source verification, existing-law fit, proposal-to-legislation alignment, adoption analysis, and implementation review are completed.

**Scope:** Drafted `legislation/ELEC-011-state.md`, the Model State Algorithmic Redistricting Baseline and Public Deviation Act. The draft requires a neutral algorithmic baseline map, bans prohibited political data in baseline generation, requires public findings for departures, preserves representation-safeguard review, provides public comment, legislative approval, judicial fallback, mid-decade redistricting limits, and source-conscious rulemaking.

**Status change:** ELEC-011 moves from candidate/source-development posture toward developed draft posture because a concrete model state vehicle now exists. The audit rebaseline status is `hard-rebaseline-needed` until T1 confirms framework compliance and assigns or confirms current rubric fields.

**Adoption and friction:** Required Electoral Environment is provisionally `state-level-pathway`; Pathway Viability is `state-by-state`; Development Priority is `active`; Pathway Adjustment is `model-law`; Adoption Friction is provisionally 80/100 (High Resistance). Redistricting reform is state-adoptable but will face major incumbent, party, technical, judicial, VRA, and state constitutional resistance.

**Unresolved findings:** T1 must verify source support for Iowa's statutory mechanics, state commission models, state voting-rights acts, algorithmic districting literature, shortest-splitline implementation, anti-mid-decade redistricting rules, judicial fallback authority, state public-records/open-meetings fit, and interaction with federal and state constitutional constraints. T1 should also compare the issue page to the model act for alignment.

**Next audit need:** Run T1 framework check.

### 2026-06-29 — Reserve constitutional amendment drafting

**Audit status:** Initial developed draft; T1 framework check pending

**Proposal-quality score:** 60; unchanged

**Scope:** Drafted `legislation/ELEC-011-amendment.md`, the Neutral Redistricting Baseline Amendment, as a reserve nationwide constitutional vehicle. Updated the issue page to link both the model state act and reserve amendment.

**Score effect:** No score change. The amendment expands the issue's future-facing pathway but does not resolve T1 source verification, existing-law fit, state implementation, Article V feasibility, federalism, judicial-review, or proposal-to-legislation alignment issues.

**Substantive note:** The amendment gives Congress enforcement and implementation power while placing the mandatory neutrality floor in constitutional text. Congress may prescribe procedures and remedies, but the draft states that Congress may not authorize partisan, incumbent-protective, candidate-protective, donor-protective, campaign-protective, or election-performance-based manipulation prohibited by the amendment.

**Next audit need:** T1 must compare the state model act, reserve amendment, issue page, and framework requirements. T2 should test Article I, Section 4; Fourteenth and Fifteenth Amendment authority; state legislative districting reach; *Rucho*; independent commission doctrine; voting-rights doctrine; anti-commandeering concerns; standing; and whether the amendment's neutrality floor is drafted tightly enough.

### 2026-06-29 — Initial issue development

**Audit status:** Pending development; initial issue framework drafted; constitutional reserve option noted

**Proposal-quality score:** 0

**Score basis:** ELEC-011 remains fixed-zero and unscored because no model legislation or constitutional amendment text has been drafted and no T1 framework check has been run. The issue page now contains an initial framework built around an algorithmic redistricting baseline, public deviation findings, commission or nonpartisan review, legislative approval, judicial fallback, and a reserved nationwide constitutional-amendment option.

**Scope:** Converted ELEC-011 from a dashboard-only candidate into a readable issue page. Added source posture for *Louisiana v. Callais*, NCSL's redistricting-commission summary and Iowa model discussion, shortest-splitline source development, and a constitutional-amendment reserve option.

**Next audit need:** Run T1 framework check / issue-admission confirmation. Decide whether ELEC-011 should remain a model state act only, add a federal incentive or transparency component, eventually include paired state/federal legislation, or preserve a constitutional amendment only as a reserve concept. Verify the Callais legal posture in detail before drafting. Source-develop state voting-rights acts, independent commissions, Iowa statutory mechanics, algorithmic districting literature, anti-mid-decade redistricting rules, public-comment requirements, judicial fallback models, and any historical or modern constitutional-amendment analogues for nationwide districting standards.

**Audit process feedback:** The initial issue page is useful for preserving the user's preferred framing, but it should not be scored until T1 confirms remedy fit and source sufficiency.

### 2026-06-25 — Horizon integration decision

**Audit status:** Pending development

**Proposal-quality score:** 0

**Score basis:** Admitted from HOR-009 as a distinct A-02 candidate after *Louisiana v. Callais* because redistricting, vote dilution, majority-minority representation, racial-gerrymandering doctrine, state voting-rights acts, independent districting institutions, and mid-decade redistricting safeguards are not owned by existing developed election proposals. No proposal-quality score assigned because no basic proposal framework existed at the time.

**Next audit need:** Run issue-admission/source-development pass focused on *Callais*, state responses, Section 2/VRA constraints, state voting-rights acts, independent commissions, anti-mid-decade-redistricting rules, and constitutionally durable representation safeguards.
