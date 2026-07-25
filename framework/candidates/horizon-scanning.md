---
title: "Horizon Scanning"
status: active
authority_scope: "Project-wide discovery of new or newly salient institutional concerns, duplicate and admission screening, Project 2025 discovery treatment, Horizon identifiers, and scan outputs."
load_when: "Running or reviewing a Horizon Scan, conducting project-wide issue discovery, or converting a discovered concern into a formal Horizon candidate recommendation."
dependencies: "../FRAMEWORK.md; ../methodology/scope-and-admission.md; ../methodology/partisan-perception-and-public-actors.md; ../sources/automated-source-adjudication.md; candidate-adjudication.md; ../GITHUB_WORKFLOW.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Horizon Scanning

## Authority and Dependencies

This file is the authoritative substantive method for project-wide Horizon discovery. Apply the admission test and political-failure boundary in [`../methodology/scope-and-admission.md`](../methodology/scope-and-admission.md), the Project 2025 characterization rule in [`../methodology/partisan-perception-and-public-actors.md`](../methodology/partisan-perception-and-public-actors.md), route-centered intake rules in [`../sources/automated-source-adjudication.md`](../sources/automated-source-adjudication.md), and formal-candidate handling in [`candidate-adjudication.md`](candidate-adjudication.md). GitHub queue mechanics belong to [`../GITHUB_WORKFLOW.md`](../GITHUB_WORKFLOW.md).

## Load When

Load this file when running or reviewing a Horizon Scan, conducting project-wide issue discovery, screening a newly salient institutional concern against existing work, or converting a discovery result into a formal Horizon candidate recommendation.

## Horizon Scan

The **Horizon Scan** is a special project-wide audit flavor for identifying new, emerging, or newly salient issues of concern within the project's goals, including threats to democracy, rule-of-law failure, personalist capture, institutional damage, evasion of checks and balances, or comparable structural risks. It is a discovery and recommendation workflow, not an issue-quality scoring tier.

A Horizon Scan should:

1. perform a current-source discovery pass using recent reliable public sources, including current news, official records, court activity, legislation, agency action, government reports, public legal-research sources, watchdog materials, expert commentary, and other relevant sources;
2. identify possible new concerns, emerging manifestations, or changed factual or legal conditions that may matter to the project;
3. cross-check each concern against existing areas, issue pages, proposals, proposed legislation, source-development notes, active GitHub horizon issues, GitHub Project fields, and the Horizon Scan Log;
4. apply the ordinary Issue-Admission Test rather than bypassing it;
5. determine whether the concern is substantially duplicative, a manifestation of an existing issue, a reason to expand or amend an existing issue, a reason to reformulate existing proposed legislation, a candidate for a new standalone issue, or outside current ARRP scope;
6. make an explicit new-issue or existing-issue recommendation for each finding, stating whether to create a new issue, merge into an existing issue, expand or amend an existing issue, retain only as source development, or decline as duplicative or out of scope;
7. recommend whether to expand, adapt, amend, merge, cross-reference, source-develop, or decline the concern; and
8. document sources, uncertainty, duplicate checks, and the basis for each recommendation.

## Project 2025 Discovery Treatment

Project 2025 crossover analysis should treat Project 2025 as both an implementation-tracking source and a weakness-discovery source. A Project 2025 initiative does not need to have been enacted, attempted, litigated, or adopted to remain relevant to ARRP. If the initiative identifies a legal, statutory, administrative, procedural, personnel, funding, records, enforcement, or institutional vehicle that could be used for personalist capture, retaliation, civil-rights erosion, factual suppression, congressional evasion, or other structural abuse, the audit should still evaluate whether ARRP should cure that vulnerability. Current implementation status affects urgency, source confidence, and manifestation evidence; it should not by itself be used to dismiss the weakness or mark it out of scope.

Project 2025 source verification should follow a strict source hierarchy. First, prefer official Heritage-controlled sources when available: Heritage Foundation pages, `project2025.org` pages, `mandateforleadership.org`, and official Project 2025 or Heritage publications. Second, use stable mirrors such as DocumentCloud only to locate text, preserve access, or identify search terms, and record both the official source and the mirror used for retrieval. Third, use the local fallback copy at [`../../sources/project-2025-mandate-for-leadership-2023-documentcloud-backup.pdf`](../../sources/project-2025-mandate-for-leadership-2023-documentcloud-backup.pdf) only if official sources and stable online mirrors become unavailable, changed, or insufficient for the needed text. News summaries and advocacy summaries may identify leads or public salience but should not replace the official source, stable mirror, or local fallback in the citation record.

## Scan Boundary and Output

A Horizon Scan should not directly create new issue pages, modify existing issue pages, revise legislation, change scores, update inventories, or change source records unless the user separately approves implementation after reviewing the scan. Its active output should be captured in GitHub Issues and the GitHub Project horizon queue, with a concise and easily readable listing of each flagged concern and recommendation. [`../logs/HORIZON_SCAN_LOG.md`](../logs/HORIZON_SCAN_LOG.md) should be updated when a candidate is admitted, merged, deferred, retired, or otherwise adjudicated. If the scan identifies urgent or high-confidence concerns, present them prominently to the user before implementation work begins.

Large source-intake collections must be synthesized before they become a user review queue. Follow [`../sources/automated-source-adjudication.md`](../sources/automated-source-adjudication.md): preserve provenance while review remains open; route evidence relevant to an existing proposal or active Horizon record; consolidate otherwise-unowned institutional weaknesses into preliminary candidates; and retain uncertain or open material for defined review or monitoring. Do not require the user to adjudicate raw articles, tracker rows, cases, or agency actions individually. Only unresolved synthesized preliminary candidates appear in that Console view. A preliminary candidate has no `HOR-###` identifier or GitHub issue. On approved promotion through Codex, create the formal proposed candidate, reroute its supporting evidence, and remove the preliminary row; promotion starts the ordinary duplicate, legal, political-failure, and issue-admission workflow and does not itself admit an area-specific proposal.

Each Horizon Scan finding should receive a stable **Horizon ID** in the form `HOR-###`, assigned sequentially in the cumulative Horizon Scan list. The Horizon ID is a temporary intake reference, not a formal issue ID. If a finding is later developed into a proposal, the new issue should receive the ordinary area-specific issue ID, and the Horizon ID should remain in the Horizon Integration Log as the intake reference.

Each Horizon Scan list update should normally include:

1. Horizon ID;
2. scan date and scope;
3. source categories checked;
4. search terms or discovery routes used where practical;
5. concise list of flagged concerns;
6. duplicate or overlap check against existing issues and legislation;
7. issue-admission result;
8. explicit new-issue or existing-issue recommendation;
9. recommended disposition;
10. suggested existing issue or area link;
11. source links or source-development needs;
12. confidence level and unresolved questions; and
13. recommended next action.
