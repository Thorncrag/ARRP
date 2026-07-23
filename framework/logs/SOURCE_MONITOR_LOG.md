---
title: "Source Monitor Log"
print_status: excluded
print_exclusion_reason: "Internal operational log."
---

# Source Monitor Log

This log records material source or presidential-directive metadata changes proposed by deterministic project watchers. Routine no-change checks remain in GitHub Actions and do not create repository commits or log entries.

Each entry must identify the watcher, a stable activity code, the affected source or directive identifiers, the originating workflow run, the machine-observed change, and the automation boundary. The corresponding pull request is the unresolved review task; merging it accepts the proposed per-row baseline. No entry establishes legal significance, project relevance, or a substantive disposition.

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
## 2026-07-23T17:29:51+00:00 — Case monitor bot

- Activity code: `CASE-20260723172951-25CB64A0`
- Originating workflow run: [30029637867](https://github.com/Thorncrag/ARRP/actions/runs/30029637867)
- Result: `changes_detected`
- Affected source IDs: SRC-1004, SRC-1093, SRC-1929, SRC-1930, SRC-1932, SRC-1933, SRC-1934, SRC-1940, SRC-1941, SRC-1942, SRC-1943, SRC-1946, SRC-1952, SRC-1957, SRC-1973, SRC-1979, SRC-1982, SRC-2080, SRC-2081, SRC-2105, SRC-2110, SRC-2136, SRC-2216, SRC-2221, SRC-2235, SRC-2351, SRC-2591
- Tracker changes: 0 added; 27 changed; 0 removed
- Case baselines updated: 27
- Coverage: 490 mapped monitored CourtListener rows; 7 monitored CourtListener rows outside tracker coverage
- Targeted CourtListener checks: 0 queried; 0 failed; 27 unverified
- Source-development modules changed: 0
- Interpretation: source-change signal only; no legal significance or project disposition determined.

| Change | Case | Docket | Previous observation | Current observation | Catalog match |
| --- | --- | --- | --- | --- | --- |
| Changed | American Association of Colleges for Teacher Education v\. Carter \(D\. Md\.\) | 1:25\-cv\-00702 | Government Action Not Blocked \(Pending Appeal\); 2025\-10\-08 | Case Closed; 2026\-03\-17 | SRC\-1957 |
| Changed | Rhode Island Latino Arts v\. National Endowment for the Arts \(D\.R\.I\.\) | 1:25\-cv\-00079 | Government Action Blocked; 2025\-11\-17 | Government Action Blocked; 2025\-11\-17 | SRC\-1973 |
| Changed | Woonasquatucket River Watershed Council v\. Department of Agriculture \(D\.R\.I\.\) | 1:25\-cv\-00097 | Government Action Temporarily Blocked; 2025\-11\-04 | Government Action Temporarily Blocked; 2025\-11\-04 | SRC\-2591 |
| Changed | Radio Free Asia v\. United States \(D\.D\.C\.\) | 1:25\-cv\-00907 | Government Action Blocked Pending Appeal; 2025\-09\-22 | Government Action Blocked Pending Appeal; 2025\-09\-22 | SRC\-2221 |
| Changed | Middle East Broadcasting Networks v\. United States \(D\.D\.C\.\) | 1:25\-cv\-00966 | Government Action Blocked Pending Appeal; 2025\-09\-22 | Government Action Blocked Pending Appeal; 2025\-09\-22 | SRC\-2216 |
| Changed | G\.F\.F\. v\. Trump \(S\.D\.N\.Y\.\) | 1:25\-cv\-02886 | Government Action Temporarily Blocked; 2025\-07\-29 | Government Action Temporarily Blocked; 2025\-07\-29 | SRC\-1942 |
| Changed | J\.A\.V\. v\. Trump \(S\.D\. Tex\.\) | 1:25\-cv\-00072 | Government Action Blocked; 2025\-07\-14 | Government Action Blocked; 2025\-07\-14 | SRC\-1943 |
| Changed | American Association of University Professors \- Harvard Faculty Chapter v\. Department of Justice \(D\. Mass\.\) | 1:25\-cv\-10910 | Government Action Blocked; 2025\-12\-18 | Government Action Blocked; 2025\-12\-18 | SRC\-1929 |
| Changed | D\.B\.U\. v\. Trump \(D\. Colo\.\) | 1:25\-cv\-01163 | Government Action Temporarily Blocked; 2025\-12\-09 | Government Action Temporarily Blocked; 2025\-12\-09 | SRC\-1940 |
| Changed | Mahdawi v\. Trump \(D\. Vt\.\) | 2:25\-cv\-00389 | Government Action Not Blocked \(Pending Appeal\); 2026\-07\-21 | Government Action Not Blocked \(Pending Appeal\); 2026\-07\-21 | SRC\-2235 |
| Changed | President and Fellows of Harvard College v\. US Department of Health and Human Services \(D\. Mass\.\) | 1:25\-cv\-11048 | Government Action Blocked; 2025\-10\-20 | Government Action Blocked; 2025\-12\-18 | SRC\-1933 |
| Changed | M\.A\.P\.S\. v\. Garite \(W\.D\. Tex\.\) | 3:25\-cv\-00171 | Government Action Blocked; 2025\-08\-05 | Government Action Blocked; 2025\-08\-05 | SRC\-1946 |
| Changed | State of Illinois v\. Federal Emergency Management Agency \(D\.R\.I\.\) | 1:25\-cv\-00206 | Government Action Blocked; 2025\-10\-14 | Government Action Blocked; 2025\-11\-21 | SRC\-2110 |
| Changed | Darwin Antonio Arevalo Millan v\. Trump \(C\.D\. Cal\.\) | 5:25\-cv\-01207 | Government Action Temporarily Blocked; 2025\-10\-21 | Government Action Temporarily Blocked; 2025\-10\-21 | SRC\-1941 |
| Changed | VERA Institute of Justice v\. U\.S\. Department of Justice \(D\.D\.C\.\) | 1:25\-cv\-01643 | Government Action Temporarily Blocked in Part; Temporary Block Denied in Part; 2025\-11\-25 | Government Action Temporarily Blocked in Part; Temporary Block Denied in Part; 2025\-11\-25 | SRC\-2136 |
| Changed | President and Fellows of Harvard College v\. Department of Homeland Security \(D\. Mass\.\) | 1:25\-cv\-11472 | Government Action Temporarily Blocked; 2026\-03\-31 | Government Action Temporarily Blocked; 2026\-03\-31 | SRC\-1932 |
| Changed | Shapiro v\. Department of Agriculture \(M\.D\. Pa\.\) | 1:25\-cv\-00998 | Government Action Not Blocked \(Pending Appeal\); 2026\-01\-02 | Government Action Not Blocked \(Pending Appeal\); 2026\-01\-02 | SRC\-2105 |
| Changed | Thakur v\. Trump \(N\.D\. Cal\.\) | 3:25\-cv\-04737 | Government Action Blocked Pending Appeal; 2025\-12\-23 | Government Action Blocked Pending Appeal; 2025\-12\-23 | SRC\-1934 |
| Changed | Newsom v\. Trump \(N\.D\. Cal\.\) | 3:25\-cv\-04870 | Government Action Temporarily Blocked; 2026\-01\-12 | Government Action Temporarily Blocked; 2026\-01\-12 | SRC\-1004 |
| Changed | Appalachian Voices v\. United States Environmental Protection Agency \(D\.D\.C\.\) | 1:25\-cv\-01982 | Temporary Block of Government Action Denied; 2025\-09\-25 | Temporary Block of Government Action Denied; 2025\-09\-25 | SRC\-1093 |
| Changed | American Association of University Professors v\. Trump \(N\.D\. Cal\.\) | 3:25\-cv\-07864 | Government Action Temporarily Blocked; 2026\-02\-06 | Government Action Temporarily Blocked; 2026\-02\-06 | SRC\-1930 |
| Changed | State of Washington v\. Health and Human Services \(D\. Or\.\) | 6:25\-cv\-01748 | Government Action Temporarily Blocked; 2025\-10\-27 | Government Action Temporarily Blocked; 2025\-12\-26 | SRC\-1979 |
| Changed | Housing Authority of the County of San Diego v\. Turner \(N\.D\. Cal\.\) | 4:25\-cv\-08859 | Government Action Temporarily Blocked; 2026\-01\-20 | Government Action Temporarily Blocked; 2026\-01\-20 | SRC\-2080 |
| Changed | Institute for Applied Ecology v\. Burgum \(D\. Or\.\) | 6:25\-cv\-02364 | Government Action Blocked Pending Appeal; 2026\-05\-11 | Government Action Blocked Pending Appeal; 2026\-05\-11 | SRC\-2081 |
| Changed | N\. v\. U\.S\. Department of Health and Human Services \(D\.D\.C\.\) | 1:26\-cv\-00577 | Temporary Block of Government Action Denied; 2026\-05\-08 | Temporary Block of Government Action Denied; 2026\-05\-08 | SRC\-2351 |
| Changed | Coe v\. Blanche \(S\.D\.N\.Y\.\) | 1:26\-cv\-04641 | Government Action Temporarily Blocked; 2026\-07\-09 | Government Action Temporarily Blocked; 2026\-07\-17 | SRC\-1982 |
| Changed | Venezuelan Association of Massachusetts v\. United States Citizenship and Immigration Services \(D\. Mass\.\) | 1:26\-cv\-13038 | Case Pending; 2026\-07\-21 | Government Action Temporarily Blocked in Part; Temporary Block Denied in Part; 2026\-07\-21 | SRC\-1952 |

