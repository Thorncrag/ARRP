---
title: "Source Monitor Log"
print_status: excluded
print_exclusion_reason: "Internal operational log."
---

# Source Monitor Log

This log records material source or presidential-directive metadata changes proposed by deterministic project watchers and the exact-revision disposition recommendations produced by Elim or an interactive Codex reviewer. Routine no-change checks remain in GitHub Actions and do not create repository commits or log entries.

Each watcher entry must identify the watcher, a stable activity code, the affected source or directive identifiers, the originating workflow run, the machine-observed change, and the automation boundary. A watcher entry does not establish legal significance, project relevance, or a substantive disposition.

Each repository-review recommendation must identify the recommendation ID, recorded time, reviewer, pull-request number and URL, exact head revision, proposal event ID, recommended disposition, rationale, affected records, confidence and uncertainty, action owner, exact human question or `None`, and the reassessment trigger. The recommendation is valid only for the recorded head revision. An open pull request remains Elim-owned until this review exists; it enters human Action Items only when `Action owner: Human` states a genuinely reserved or owner-gated question. Merging a watcher pull request remains human-owner gated and accepts its proposed baseline.

## 2026-07-21T19:25:58+00:00 — Case monitor bot

- Activity code: `CASE-20260721192558-9736B480`
- Originating workflow run: [29861467767](https://github.com/Thorncrag/ARRP/actions/runs/29861467767)
- Result: `changes_detected`
- Affected source IDs: SRC-2009
- Tracker changes: 1 added; 0 changed; 1 removed
- Case baselines updated: 1
- Coverage: 493 mapped monitored CourtListener rows; 7 monitored CourtListener rows outside tracker coverage
- Targeted CourtListener checks: 0 queried; 0 failed; 1 unverified
- Interpretation: source-change signal only; no legal significance or project disposition determined.

| Change | Case | Docket | Previous observation | Current observation | Catalog match |
| --- | --- | --- | --- | --- | --- |
| Added | State of California v\. Zeldin \(N\.D\. Cal\.\) | 4:26\-cv\-03500 | Not present | Case Pending; 2026\-04\-24 | SRC\-2009 |
| Removed | State of California v\. Zeldin \(N\.D\. Cal\.\) | 3:26\-cv\-03500 | Case Pending; 2026\-04\-24 | Not present | SRC\-2009 |
## 2026-07-22T06:42:26+00:00 — Case monitor bot

- Activity code: `CASE-20260722064226-33462621`
- Originating workflow run: [29897609217](https://github.com/Thorncrag/ARRP/actions/runs/29897609217)
- Result: `changes_detected`
- Affected source IDs: SRC-1952, SRC-2017, SRC-2038, SRC-2039, SRC-2235
- Tracker changes: 0 added; 5 changed; 0 removed
- Case baselines updated: 5
- Coverage: 493 mapped monitored CourtListener rows; 7 monitored CourtListener rows outside tracker coverage
- Targeted CourtListener checks: 0 queried; 0 failed; 5 unverified
- Interpretation: source-change signal only; no legal significance or project disposition determined.

| Change | Case | Docket | Previous observation | Current observation | Catalog match |
| --- | --- | --- | --- | --- | --- |
| Changed | Mahdawi v\. Trump \(D\. Vt\.\) | 2:25\-cv\-00389 | Government Action Blocked Pending Appeal; 2025\-09\-29 | Government Action Not Blocked \(Pending Appeal\); 2026\-07\-21 | SRC\-2235 |
| Changed | Doe v\. Noem \(S\.D\.N\.Y\.\) | 1:26\-cv\-02103 | Government Action Temporarily Blocked; 2026\-05\-01 | Government Action Not Blocked \(Pending Appeal\); 2026\-07\-20 | SRC\-2038 |
| Changed | Doe v\. Noem \(S\.D\.N\.Y\.\) | 1:26\-cv\-02280 | Government Action Temporarily Blocked; 2026\-05\-01 | Government Action Not Blocked \(Pending Appeal\); 2026\-07\-20 | SRC\-2039 |
| Changed | National Parks Conservation Association v\. Burgum \(D\.D\.C\.\) | 1:26\-cv\-02103 | Case Pending; 2026\-06\-15 | Case Pending; 2026\-07\-20 | SRC\-2017 |
| Changed | Venezuelan Association of Massachusetts v\. United States Citizenship and Immigration Services \(D\. Mass\.\) | 1:26\-cv\-13038 | Case Pending; 2026\-07\-01 | Case Pending; 2026\-07\-21 | SRC\-1952 |

## 2026-07-23T17:06:07+00:00 — Case monitor bot

- Activity code: `CASE-20260723170607-BF336059`
- Originating workflow run: Local or manually invoked run
- Result: `changes_detected`
- Affected source IDs: None
- Tracker changes: 0 added; 0 changed; 0 removed
- Case baselines updated: 0
- Coverage: 0 mapped monitored CourtListener rows; 0 monitored CourtListener rows outside tracker coverage
- Targeted CourtListener checks: 0 queried; 0 failed; 0 unverified
- Source-development modules changed: 1
- Interpretation: source-change signal only; no legal significance or project disposition determined.
- `judicial-review-disposition-signals` → `research/horizon-source-records/HOR-035-source-development.md`: 213 current unreviewed leads; 213 added; 0 removed.
- Review handoff: each disposition token binds the stable lead ID to the observed fingerprint so later material changes re-queue the case.

## 2026-07-25T22:17:39Z — Repository review recommendation SMR-20260725-PR380

- Recommendation ID: `SMR-20260725-PR380`
- Recorded at: `2026-07-25T22:17:39Z`
- Reviewer: Interactive Codex
- Pull request number: `380`
- Pull request URL: `https://github.com/Thorncrag/ARRP/pull/380`
- Head revision: `ba3dc636710633c25c1f4776cc67059e96d02478`
- Proposal event ID: `SDE-93345EDC1D1AC55F8CFA3E44`
- Recommended disposition: Close without merge; after the complete-delta correction reaches `main`, rerun Case Monitor from current `main` and review the regenerated, fully itemized proposal. Separately route the July 23 Suri appellate decision to RIGHTS-002 and assess it as a possible control example for HOR-035.
- Rationale: The pull-request narrative reports one changed source, SRC-2238, while the exact pending head changes 42 source records plus the HOR-035 generated lead set. The July 23 Suri opinion preserves habeas jurisdiction and identifies disagreement among circuits; the watcher's settlement-token match does not describe that holding. The present narrative therefore cannot support informed acceptance of the complete branch.
- Affected records: 43 records in the bound event: HOR-035 and 42 source records, including SRC-2238.
- Confidence and uncertainty: High confidence that the pull-request narrative materially underreports its exact-head delta and that Suri requires substantive review; the final project characterization and any source integration remain subject to ordinary issue-development review.
- Action owner: Human
- Human question: Approve closing PR #380 without merge so the corrected watcher can regenerate a complete proposal from current `main`?
- Reassessment trigger: Any change to the pull-request head invalidates this recommendation and returns the complete proposal to Elim review.
- Primary record checked: [Suri v. Trump, No. 25-1560 (4th Cir. July 23, 2026)](https://www.ca4.uscourts.gov/opinions/251560.P.pdf).
- Result: `recommendation_recorded`

## 2026-07-25T22:17:40Z — Repository review recommendation SMR-20260725-PR381

- Recommendation ID: `SMR-20260725-PR381`
- Recorded at: `2026-07-25T22:17:40Z`
- Reviewer: Interactive Codex
- Pull request number: `381`
- Pull request URL: `https://github.com/Thorncrag/ARRP/pull/381`
- Head revision: `71525e1d2bc27c31a5c1b455243259b1b541adff`
- Proposal event ID: `SDE-578F200E8E9344ADF613CA76`
- Recommended disposition: Close without merge; after the complete-delta correction reaches `main`, rerun the Presidential Directives Bot and screen the regenerated full proposal. Route the four trade proclamations to HOR-040 source development, route Executive Order 14415 to FACT-009 source development, and record no separate project action for the two ceremonial proclamations, the Mali continuation, or the two relationship-only metadata updates unless later evidence changes that assessment.
- Rationale: The pull-request narrative says `New: 0` and `Changed: 2`, while the exact pending head contains eight new directives and two changed relationship fields. Four new proclamations invoke tariff authorities already owned by HOR-040, and Executive Order 14415 repeatedly uses the disputed Department of War terminology already owned by FACT-009. The other records are ceremonial or continuation metadata on the presently reviewed evidence. The current narrative omits most of the actual acceptance boundary.
- Affected records: 10 directives in the bound event: 2019-05370, 2019-16383, 2026-14990, 2026-14991, 2026-14992, 2026-14997, 2026-14998, 2026-14999, 2026-15003, and 2026-15024.
- Confidence and uncertainty: High confidence in the incomplete-delta diagnosis and the existing HOR-040 and FACT-009 routes; ordinary source-development review must still determine what propositions, if any, warrant integration.
- Action owner: Human
- Human question: Approve closing PR #381 without merge so the corrected watcher can regenerate and itemize all ten pending directives from current `main`?
- Reassessment trigger: Any change to the pull-request head invalidates this recommendation and returns the complete proposal to Elim review.
- Primary records checked: [Proclamation 11045](https://www.federalregister.gov/d/2026-14990), [Proclamation 11046](https://www.federalregister.gov/d/2026-14991), [Proclamation 11048](https://www.federalregister.gov/d/2026-14997), [Executive Order 14415](https://www.federalregister.gov/d/2026-15003), and [Mali emergency continuation](https://www.federalregister.gov/d/2026-15024).
- Result: `recommendation_recorded`
## 2026-07-28T02:07:41+00:00 — Case monitor bot

- Activity code: `CASE-20260728020741-97DEA4A0`
- Originating workflow run: Local or manually invoked run
- Result: `changes_detected`
- Affected source IDs: SRC-0945, SRC-0965, SRC-0982, SRC-1004, SRC-1052, SRC-1056, SRC-1093, SRC-1929, SRC-1930, SRC-1932, SRC-1933, SRC-1934, SRC-1940, SRC-1941, SRC-1942, SRC-1943, SRC-1946, SRC-1952, SRC-1957, SRC-1973, SRC-1979, SRC-1982, SRC-2042, SRC-2080, SRC-2081, SRC-2105, SRC-2110, SRC-2136, SRC-2149, SRC-2183, SRC-2190, SRC-2192, SRC-2216, SRC-2221, SRC-2235, SRC-2238, SRC-2261, SRC-2351, SRC-2591
- Tracker changes: 0 added; 39 changed; 0 removed
- Case baselines updated: 39
- Coverage: 490 mapped monitored CourtListener rows; 7 monitored CourtListener rows outside tracker coverage
- Targeted CourtListener checks: 0 queried; 0 failed; 39 unverified
- Source-development modules changed: 1
- Interpretation: source-change signal only; no legal significance or project disposition determined.
- `judicial-review-disposition-signals` → `research/horizon-source-records/HOR-035-source-development.md`: 215 current unreviewed leads; 2 added; 0 removed.

| Change | Case | Docket | Previous observation | Current observation | Catalog match |
| --- | --- | --- | --- | --- | --- |
| Changed | National Association for the Advancement of Colored People v\. United States Postal Service \(D\.D\.C\.\) | 1:20\-cv\-02295 | Government Action Blocked Pending Appeal; 2026\-07\-17 | Government Action Not Blocked \(Pending Appeal\); 2026\-07\-17 | SRC\-2190 |
| Changed | Refugee and Immigrant Center for Education and Legal Services v\. Noem \(D\.D\.C\.\) | 1:25\-cv\-00306 | Government Action Blocked; 2026\-04\-24 | Government Action Blocked; 2026\-07\-23 | SRC\-1052 |
| Changed | American Federation of Government Employees v\. Trump \(D\.D\.C\.\) | 1:25\-cv\-00352 | Government Action Not Blocked \(Pending Appeal\); 2025\-08\-05 | Government Action Not Blocked \(Pending Appeal\); 2025\-08\-05 | SRC\-0982 |
| Changed | Center for Taxpayer Rights v\. IRS \(D\.D\.C\.\) | 1:25\-cv\-00457 | Government Action Temporarily Blocked; 2026\-04\-01 | Government Action Temporarily Blocked; 2026\-04\-01 | SRC\-2149 |
| Changed | American Association of Colleges for Teacher Education v\. Carter \(D\. Md\.\) | 1:25\-cv\-00702 | Government Action Not Blocked \(Pending Appeal\); 2025\-10\-08 | Case Closed; 2026\-03\-17 | SRC\-1957 |
| Changed | National Endowment for Democracy v\. United States \(D\.D\.C\.\) | 1:25\-cv\-00648 | Government Action Temporarily Blocked; 2026\-01\-15 | Government Action Temporarily Blocked; 2026\-01\-15 | SRC\-0965 |
| Changed | Rhode Island Latino Arts v\. National Endowment for the Arts \(D\.R\.I\.\) | 1:25\-cv\-00079 | Government Action Blocked; 2025\-11\-17 | Government Action Blocked; 2025\-11\-17 | SRC\-1973 |
| Changed | Woonasquatucket River Watershed Council v\. Department of Agriculture \(D\.R\.I\.\) | 1:25\-cv\-00097 | Government Action Temporarily Blocked; 2025\-11\-04 | Government Action Temporarily Blocked; 2025\-11\-04 | SRC\-2591 |
| Changed | Suri v\. Trump \(E\.D\. Va\.\) | 1:25\-cv\-00480 | Government Action Blocked; 2025\-08\-05 | Government Action Blocked; 2026\-07\-23 | SRC\-2238 |
| Changed | Radio Free Asia v\. United States \(D\.D\.C\.\) | 1:25\-cv\-00907 | Government Action Blocked Pending Appeal; 2025\-09\-22 | Government Action Blocked Pending Appeal; 2025\-09\-22 | SRC\-2221 |
| Changed | Middle East Broadcasting Networks v\. United States \(D\.D\.C\.\) | 1:25\-cv\-00966 | Government Action Blocked Pending Appeal; 2025\-09\-22 | Government Action Blocked Pending Appeal; 2025\-09\-22 | SRC\-2216 |
| Changed | G\.F\.F\. v\. Trump \(S\.D\.N\.Y\.\) | 1:25\-cv\-02886 | Government Action Temporarily Blocked; 2025\-07\-29 | Government Action Temporarily Blocked; 2025\-07\-29 | SRC\-1942 |
| Changed | J\.A\.V\. v\. Trump \(S\.D\. Tex\.\) | 1:25\-cv\-00072 | Government Action Blocked; 2025\-07\-14 | Government Action Blocked; 2025\-07\-14 | SRC\-1943 |
| Changed | American Association of University Professors \- Harvard Faculty Chapter v\. Department of Justice \(D\. Mass\.\) | 1:25\-cv\-10910 | Government Action Blocked; 2025\-12\-18 | Government Action Blocked; 2025\-12\-18 | SRC\-1929 |
| Changed | D\.B\.U\. v\. Trump \(D\. Colo\.\) | 1:25\-cv\-01163 | Government Action Temporarily Blocked; 2025\-12\-09 | Government Action Temporarily Blocked; 2025\-12\-09 | SRC\-1940 |
| Changed | Mahdawi v\. Trump \(D\. Vt\.\) | 2:25\-cv\-00389 | Government Action Not Blocked \(Pending Appeal\); 2026\-07\-21 | Government Action Not Blocked \(Pending Appeal\); 2026\-07\-21 | SRC\-2235 |
| Changed | President and Fellows of Harvard College v\. US Department of Health and Human Services \(D\. Mass\.\) | 1:25\-cv\-11048 | Government Action Blocked; 2025\-10\-20 | Government Action Blocked; 2025\-07\-22 | SRC\-1933 |
| Changed | M\.A\.P\.S\. v\. Garite \(W\.D\. Tex\.\) | 3:25\-cv\-00171 | Government Action Blocked; 2025\-08\-05 | Government Action Blocked; 2025\-08\-05 | SRC\-1946 |
| Changed | State of Illinois v\. Federal Emergency Management Agency \(D\.R\.I\.\) | 1:25\-cv\-00206 | Government Action Blocked; 2025\-10\-14 | Government Action Blocked; 2025\-11\-21 | SRC\-2110 |
| Changed | Darwin Antonio Arevalo Millan v\. Trump \(C\.D\. Cal\.\) | 5:25\-cv\-01207 | Government Action Temporarily Blocked; 2025\-10\-21 | Government Action Temporarily Blocked; 2025\-10\-21 | SRC\-1941 |
| Changed | VERA Institute of Justice v\. U\.S\. Department of Justice \(D\.D\.C\.\) | 1:25\-cv\-01643 | Government Action Temporarily Blocked in Part; Temporary Block Denied in Part; 2025\-11\-25 | Government Action Temporarily Blocked in Part; Temporary Block Denied in Part; 2025\-11\-25 | SRC\-2136 |
| Changed | President and Fellows of Harvard College v\. Department of Homeland Security \(D\. Mass\.\) | 1:25\-cv\-11472 | Government Action Temporarily Blocked; 2026\-03\-31 | Government Action Temporarily Blocked; 2026\-03\-31 | SRC\-1932 |
| Changed | Shapiro v\. Department of Agriculture \(M\.D\. Pa\.\) | 1:25\-cv\-00998 | Government Action Not Blocked \(Pending Appeal\); 2026\-01\-02 | Government Action Not Blocked \(Pending Appeal\); 2026\-01\-02 | SRC\-2105 |
| Changed | Thakur v\. Trump \(N\.D\. Cal\.\) | 3:25\-cv\-04737 | Government Action Blocked Pending Appeal; 2025\-12\-23 | Government Action Blocked Pending Appeal; 2025\-12\-23 | SRC\-1934 |
| Changed | Newsom v\. Trump \(N\.D\. Cal\.\) | 3:25\-cv\-04870 | Government Action Temporarily Blocked; 2026\-01\-12 | Government Action Temporarily Blocked; 2026\-01\-12 | SRC\-1004 |
| Changed | Appalachian Voices v\. United States Environmental Protection Agency \(D\.D\.C\.\) | 1:25\-cv\-01982 | Temporary Block of Government Action Denied; 2025\-09\-25 | Temporary Block of Government Action Denied; 2025\-09\-25 | SRC\-1093 |
| Changed | American Academy of Pediatrics v\. Robert F\. Kennedy Jr\. \(D\. Mass\.\) | 1:25\-cv\-11916 | Government Action Temporarily Blocked; 2026\-03\-16 | Government Action Temporarily Blocked; 2026\-07\-23 | SRC\-0945 |
| Changed | Neguse v\. U\.S\. Immigration and Customs Enforcement \(D\.D\.C\.\) | 1:25\-cv\-02463 | Government Action Blocked Pending Appeal; 2026\-05\-08 | Government Action Temporarily Blocked; 2026\-07\-27 | SRC\-2261 |
| Changed | Lesly Miot v\. Trump \(D\.D\.C\.\) | 1:25\-cv\-02471 | Government Action Not Blocked \(Pending Appeal\); 2026\-06\-25 | Government Action Not Blocked \(Pending Appeal\); 2026\-07\-22 | SRC\-2042 |
| Changed | American Association of University Professors v\. Trump \(N\.D\. Cal\.\) | 3:25\-cv\-07864 | Government Action Temporarily Blocked; 2026\-02\-06 | Government Action Temporarily Blocked; 2026\-02\-06 | SRC\-1930 |
| Changed | State of Washington v\. Health and Human Services \(D\. Or\.\) | 6:25\-cv\-01748 | Government Action Temporarily Blocked; 2025\-10\-27 | Government Action Temporarily Blocked; 2025\-12\-26 | SRC\-1979 |
| Changed | Housing Authority of the County of San Diego v\. Turner \(N\.D\. Cal\.\) | 4:25\-cv\-08859 | Government Action Temporarily Blocked; 2026\-01\-20 | Government Action Temporarily Blocked; 2026\-01\-20 | SRC\-2080 |
| Changed | Jorge Lujan v\. FMCSA \(D\.C\. Cir\.\) | 26\-1032 | Case Pending; 2026\-02\-20 | Case Pending; 2026\-07\-22 | SRC\-1056 |
| Changed | Institute for Applied Ecology v\. Burgum \(D\. Or\.\) | 6:25\-cv\-02364 | Government Action Blocked Pending Appeal; 2026\-05\-11 | Government Action Blocked Pending Appeal; 2026\-05\-11 | SRC\-2081 |
| Changed | N\. v\. U\.S\. Department of Health and Human Services \(D\.D\.C\.\) | 1:26\-cv\-00577 | Temporary Block of Government Action Denied; 2026\-05\-08 | Temporary Block of Government Action Denied; 2026\-05\-08 | SRC\-2351 |
| Changed | DSCC v\. Trump \(D\.D\.C\.\) | 1:26\-cv\-01114 | Government Action Not Blocked \(Pending Appeal\); 2026\-06\-01 | Government Action Not Blocked \(Pending Appeal\); 2026\-06\-01 | SRC\-2183 |
| Changed | State of California v\. Trump \(D\. Mass\.\) | 1:26\-cv\-11581 | Government Action Blocked Pending Appeal; 2026\-07\-07 | Government Action Blocked Pending Appeal; 2026\-07\-25 | SRC\-2192 |
| Changed | Coe v\. Blanche \(S\.D\.N\.Y\.\) | 1:26\-cv\-04641 | Government Action Temporarily Blocked; 2026\-07\-09 | Government Action Temporarily Blocked; 2026\-07\-17 | SRC\-1982 |
| Changed | Venezuelan Association of Massachusetts v\. United States Citizenship and Immigration Services \(D\. Mass\.\) | 1:26\-cv\-13038 | Case Pending; 2026\-07\-21 | Government Action Temporarily Blocked in Part; Temporary Block Denied in Part; 2026\-07\-21 | SRC\-1952 |

## 2026-07-28T02:07:43+00:00 — Presidential directives watcher (PDM-A44F0C0C8B)

- Added directives: **8**
- Changed directives: **2**
- Added IDs: 2026\-14990, 2026\-14991, 2026\-14992, 2026\-14997, 2026\-14998, 2026\-14999, 2026\-15003, 2026\-15024
- Changed IDs: 2019\-05370, 2019\-16383
- Result: catalog_updated
- Action: Updated machine-observed Federal Register metadata and per-row baselines for human review.
- Boundary: No substantive ARRP classification or disposition was performed.
