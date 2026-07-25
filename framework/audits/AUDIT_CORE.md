---
title: "ARRP Audit Core"
status: active
dependencies: "../FRAMEWORK.md; ../AGENT_OPERATING_RULES.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Audit Core

## Authority, Loading, and Dependencies

**Authority.** This module is the authoritative detailed rule set for audit orientation, the common audit workflow, issue-quality run counting, audit autonomy, preservation, and audit output. The [Framework kernel](../FRAMEWORK.md) remains controlling for cross-cutting project principles and reserved human authority.

**Load when.** Load this module for every T0–T4 audit, Change Audit, Project Consistency Audit, or other formal project audit, and whenever an audit result, run count, preservation state, or audit output is created or changed.

**Dependencies.** Always load the [Framework kernel](../FRAMEWORK.md) and [Agent Operating Rules](../AGENT_OPERATING_RULES.md). Load [GitHub Workflow](../GITHUB_WORKFLOW.md) whenever human-facing or machine-readable status may change. Then load the tier, Change Audit, consistency, verification, legal-review, scoring, adoption, or external-review module implicated by the selected scope. This module does not enlarge the authority granted by those records.

## Audit Rules and Proposal Quality Scoring

Before an issue or proposal is treated as ready for external circulation, it should undergo a quality audit assessing issue definition, legal authority, source support, proposal survey, remedy adequacy, abuse resistance, political adoption prospects, drafting clarity, and integration with the project inventory.

The audit should identify unresolved legal, factual, remedial, implementation, and adoption risks rather than treating completion of a draft as evidence of readiness.

Every developed issue should have audit front matter, a visible **Proposal Scoring** summary, and a sibling audit-history file. Current proposal-quality score, audit status, next audit need, audit-rubric version, rebaseline status, Required Electoral Environment, Development Priority, Adoption Friction, and related score-basis narrative belong on the issue page and in the audit-history sidecar. Cross-project routing, audit-control, and release-triage fields belong in the GitHub Project.

### Pre-Audit Orientation

Every audit should begin with the Framework kernel and this Audit Core, then follow the linked governing files relevant to the audit's scope before applying the audit to an issue, proposal, GitHub Project item, inventory, horizon candidate, or export product. The auditor need not reread every project file for every audit, but must consult enough governing material to avoid applying stale rules.

At minimum:

- all audits should consult the Framework kernel for the project's governing structure, then load the authoritative modules implicated by the audit's scope for issue architecture, drafting method, neutrality rules, source standards, Issue Snapshot format, Proposal Survey requirements, annotation conventions, cross-reference rules, audit procedure, scoring rules, tier requirements, current-status checks, output requirements, and proposal-page alignment and audit-preservation rules;
- remedy-type, least-complex-remedy, or remedial-adequacy audits should consult [`REMEDY_FRAMEWORK.md`](../REMEDY_FRAMEWORK.md);
- print, appendix, compiled-document, PDF, DOCX, public-release, or export-placement audits should consult [`PRINT_ASSEMBLY.md`](../PRINT_ASSEMBLY.md);
- Change Audits should consult every governing project material listed in the Change Audit workflow before updating individual proposal pages; and
- audits that update human-facing or machine-readable status should consult the affected issue page, sibling audit-history file, GitHub Project item, and relevant retained source records before finalizing changes.

If linked governing records appear inconsistent, document the inconsistency as a Change Audit issue and resolve or report it before relying on either rule for downstream scoring or page updates.


### Audit Workflow

Each developed proposal should be audited through the following sequence. The sequence may be run as a full review or as a targeted review, but the audit record should identify which parts were completed.

1. **Style, section-fit, concision, and reader-language audit.** Begin with the [Formatting Preflight](TIERED_AUDITS.md#formatting-preflight). Confirm that the issue follows the project's style and architecture conventions, that each main section contains material appropriate to its function, and that the main narrative is as concise as reasonably possible while still establishing the issue and proposed remedy. On reader-facing surfaces, identify unexplained project shorthand and loaded, conclusory, pejorative, or imprecise labels; replace them with direct descriptions of the conduct, basis, legal defect, or review result unless exact quoted, attributed, legally operative, or source terminology is necessary. As part of the existing neutrality and claim-status review, distinguish fact, law, disputed interpretation or uncertainty, and ARRP's own institutional analysis or policy position. Where the project takes a substantive position or a reasonable reader could materially perceive partisan alignment, apply the [Substantive Positions and Partisan Perception](../FRAMEWORK.md#substantive-positions-and-partisan-perception) rule, including its first-reference treatment of President Trump and Project 2025. Preserve exact technical terminology in internal audit and workflow records. Apply this as an editorial guideline rather than a hard word-count or section-length rule. At audit closeout, repeat the check briefly so material added during the audit does not introduce new style, section-placement, concision, neutrality, position-disclosure, or reader-comprehension problems.
2. **Issue-identification audit.** Confirm that the issue identifies a distinct institutional weakness, has the correct primary area home, is not duplicative of another issue, and is framed as a structural defect rather than as a narrative about one person or episode.
3. **Framework-compliance audit.** Confirm that the issue performs the required analytical functions: Issue Snapshot, Institutional Anomaly, Manifestation of the Failure with evidence-backed titled instances or observable categories, Resulting Damage, Underlying Weakness, Proposal Survey, Least-Complex Adequate Remedy, Repair and Prevention, Proposed Legislation where applicable, Proposed Constitutional Amendment and Proposed Enabling Legislation where applicable, Relationship to Adjacent Proposals where overlap would otherwise cause confusion, and Annotation.
4. **Enactment-pathway audit.** Confirm the minimum electoral environment required for the proposal to become seriously actionable, whether the proposal can be narrowed or staged to fit a more realistic environment, and whether further development is immediate, active, conditional, reserve, or deprioritized. This check begins at T1 and must be evidence-bound rather than speculative.
5. **Evidence and citation audit.** Confirm that factual, legal, and causal claims are supported by nearby citations, that real-world examples link to source material, and that all cited external sources are captured in [`sources.csv`](../../inventory/sources.csv).
6. **Legal-support audit.** Confirm that the proposal accurately identifies the constitutional, statutory, regulatory, procedural, or institutional authority on which it depends and discloses material uncertainty, doctrine, limits, or litigation risk.
7. **Existing-law and prior-proposal audit.** Confirm that the proposal checks existing law first, prefers amendment of existing vehicles where adequate, searches direct and functional analogues, and weighs prior proposals according to enacted use, institutional review, sponsorship, co-sponsorship, bipartisan support, and legislative progress.
8. **Remedy-adequacy audit.** Confirm that the proposed remedy is the least-complex adequate remedy, addresses both repair and prevention where relevant, identifies why simpler options are insufficient, preserves more complex fallback options where necessary, and materially reduces the probability that public authority can be converted into arbitrary injury.
9. **Internal remedy-fit audit.** Confirm that the issue's anomaly, manifestations, resulting damage, underlying weakness, least-complex adequate remedy, repair/prevention language, proposed legislation or other vehicle, and scoring annotations still address the same institutional defect. If recent source-development or framing updates create a mismatch, document and reconcile it when the correction remains within the human-approved foundation. Do not treat the proposal score as current while a mismatch remains unresolved; request human review when resolution would require a reserved foundational, contraction, or other materially consequential change.
10. **Implementation and enforcement audit.** Confirm that the remedy can be administered, enforced, funded, reviewed, and updated without relying on the same failed institution or norm that created the problem.
11. **Budgetary-impact audit.** Confirm that the issue page and proposal page contain the required preliminary **Budgetary Impact Statement** and that any fiscal characterization is appropriately sourced, caveated, tier-scaled, and checked against available budget or appropriations analogues. If the issue presents a preferred JUD-011 path and an independent alternative, confirm that the page contains two separately labeled budget statements and distinguishes shared, incremental, function-specific, and fully standalone costs.
12. **Abuse-resistance audit.** Confirm that the remedy includes safeguards against capture, selective enforcement, evasion, delay, retaliation, pretextual use, or partisan conversion. Prepare a neutral analysis of how the existing arrangement and proposed repair would operate under materially different political control. Record and apply any existing human reversed-control decision; if that decision is material and missing, route it for human review rather than answering it.
13. **Drafting-quality audit.** Confirm that proposed legislation or rules use the appropriate legal vehicle, maintain legislative drafting conventions, define operative terms, assign responsible actors, specify procedures, and include remedies, deadlines, reporting, review, and severability where appropriate.
14. **Proposal-to-legislation consistency audit.** Where an issue page links to proposed legislation, proposed constitutional amendment text, proposed enabling legislation, or another proposal vehicle, compare the Issue Snapshot vehicle, Least-Complex Adequate Remedy, Repair and Prevention section, Proposed Legislation or amendment/enabling sections, Annotation, and scoring/audit summary against the linked bill, rule, constitutional amendment, or procedural text. Confirm that the issue page still accurately describes the operative vehicle, covered actors, legal hook, remedy type, enforcement mechanism, deadlines, responsible institutions, scope limits, and any material drafting notes. If the audit discovers a substantive discrepancy, document it and reconcile the records when the correction remains within the human-approved foundation. Leave it unresolved and request human approval only when the correction would change a reserved foundation, materially contract the proposal, or make another reserved change.
15. **Hallucination-resistance and verification audit.** Confirm that the issue contains no invented, uncited, stale, unverifiable, or overconfident claims, and that every material factual, legal, polling, legislative-history, scholarly, real-world-example, or fiscal-impact assertion is traceable to reliable source material.
16. **Judicial and scholarly scrutiny audit.** Confirm that the proposal has been tested against likely Supreme Court, relevant lower-court, and serious legal-scholar objections, and that the issue records deeply researched recommendations for increasing the likelihood that the proposal would be upheld.
17. **Argument and cogency audit.** Confirm that the page makes the complete chain from human harm or material risk, through the institutional defect and operation of public authority, to the proposed repair and its anti-arbitrariness safeguards visible without hidden premises, overclaiming, unsupported causation, or remedy mismatch.
18. **Support and adoption audit.** Confirm that the issue can be explained to likely supporters, skeptics, lawmakers, staff, experts, and the public in terms of institutional repair rather than partisan advantage.
19. **Political-language and coalition-appeal audit.** Confirm that the proposal remains candid about misconduct while using institution-focused language and estimating likely support from bipartisan, independent, Democratic, and Republican audiences.
20. **Project-integration audit.** Confirm that internal links, legislation links, issue status, remedy type, source inventory, audit metadata, audit-history sidecar, GitHub Project canonical-page links, the project-area and area-level contents surfaces, the Subject and Institution Index, the GitHub issue registry, and compiled-document placement remain consistent. At T1 and above, perform the Navigation Synchronization Check when the issue has a stable reader-facing record.


### Audit Run Counting Rule

The GitHub Project **Runs** field counts only completed, separately recorded issue-quality audits expressly conducted as **T0, T1, T2, T3, or T4**. Each completed tier counts once. A cumulative T4 counts as one T4 run unless T1, T2, and T3 were separately performed, completed, and recorded as distinct audit events. A successive T1-through-T4 sequence counts each tier actually completed and separately memorialized.

Change Audits, Internal Remedy-Fit Audits, Project Consistency Audits, Horizon Scans, source-development passes, drafting or redrafting sessions, formatting or section-placement reviews, hold-predicate checks, external-review intake, validation reruns, dashboard refreshes, bookkeeping corrections, and continuations or corrections of the same still-open T-audit do **not** increment **Runs**. If one of those checks occurs inside a T0–T4 audit, it remains part of that single tier run and receives no additional count. An abandoned, interrupted, or blocked tier does not count until the tier is completed and its audit record is closed.

The run count is procedural history, not a quality score. T0 and T1 may increment **Runs** even when they do not produce a formula-based score; conversely, a score-changing Change Audit does not increment **Runs** unless a distinct T0–T4 audit was also completed. When historical reconciliation reveals that a non-tier activity was counted, correct the Project field and relevant compact summaries without inventing a tier label or rewriting the substantive historical entry.

Issue-quality audits should be run on exactly one issue at a time. Before starting, identify the target issue by issue ID and page path. If the request could refer to more than one issue, or if the issue ID is missing or unclear, ask the user to identify the issue before beginning the audit. Project-wide Horizon Scan and Project Consistency Audits are standing non-scoring exceptions; neither may be used as a substitute for scoring or substantively revising an individual issue.


### Audit Autonomy and Unknowns

Audits should be conducted with the assumption that the user wants as few questions as possible. The auditor should attempt to resolve uncertainties through the project record, current-source refresh, primary-source checks, reasonable inference from documented framework rules, and conservative scoring before asking the user.

If an unknown cannot be resolved without user input, do not block the entire audit. Instead:

1. skip only the unresolved portion of the audit;
2. mark the skipped portion as `Unresolved`, `Source needed`, `Verification pending`, or `User input needed`;
3. record why the issue could not be resolved;
4. record what source, fact, preference, or decision is needed;
5. continue and complete every other audit portion that can be handled responsibly; and
6. notify the user immediately and concisely that the portion was skipped and what is needed to complete it.

When uncertainty affects scoring, assign no favorable credit for the unresolved portion, apply any required penalty, and identify the next audit need. Do not ask the user to resolve matters that can be answered through reliable sources or the project's existing framework.

When a defect can be corrected without user input, correct it rather than only noting it. Examples include broken links, missing internal links, stale source rows or GitHub Project fields, missing source-inventory capture, obvious citation-placement defects, metadata inconsistencies, formatting defects, issue-status inconsistencies, and framework-compliance gaps that can be fixed from the existing record. Do not make substantive policy choices, legal judgments, or factual claims that require unresolved source support; mark those unresolved and notify the user.

### Audit Preservation and GitHub Storage

After an audit is completed, or if an audit is interrupted after changes have been made, preserve the work promptly. Where the repository and remote are available, create the necessary non-interactive commit or commits and push them to the configured GitHub remote without asking the user additional process questions, unless approval is required by the working environment or by this method.

Audit closeout must include the GitHub tracking surfaces that would otherwise drift from the repository. Before treating an audited issue as complete, update the related GitHub issue wrapper and GitHub Project item when the audit changes the issue's status, score, run count, last audit, next audit, rebaseline status, change-audit flag, canonical page, release-blocker posture, or other Project-controlled field. After updating those GitHub surfaces, read them back and confirm the issue wrapper and Project row match the repository issue metadata for all in-scope workflow fields. The issue wrapper should remain a concise public workflow surface and should link to the canonical issue page, audit-history sidecar, legislation or vehicle page when one exists, and area page. Do not duplicate detailed audit-history entries as GitHub issue comments unless the user specifically asks for that comment; the audit-history sidecar is the memorialized substantive record.

If an audit changes an eligible proposal's Project `Development level`, `Status`, `Score`, or goal eligibility, closeout must also refresh the Project Console progress data. After the authoritative Project update has been read back and the audit commit has been pushed, manually dispatch the `Project Console Progress Bot` workflow, wait for it to complete, and verify `project-console-data/progress.json` reflects the new portfolio count, development-board placement, workflow status, score movement, or area result as applicable. The daily schedule is a recovery backstop and does not replace same-session verification. An expressly authorized multi-issue or successive-tier batch may use one final refresh after all included Project changes and pushes, provided the data readback confirms the complete batch. Never edit the generated data branch by hand.

Before finalizing an audit with repository changes, verify the preservation state: local validation or documented skipped validation, clean or intentionally described working tree, commit created, push attempted when a remote is available, GitHub issue/Project fields updated and read back when they are in scope, and any required Project Console progress-data refresh completed and read back. If an environmental approval, authentication, network, remote, workflow, or publication error prevents GitHub issue updates, Project updates, progress refresh, readback verification, or push, record the failure in the final audit note and keep `CURRENT_AUDIT.md` `Paused` or `Blocked` with the exact remaining sync step and, when blocked, the indispensable prerequisite and unblock trigger. Do not mark the handoff `Inactive` until every completion-critical step within the task is finished.

If local validation, formatting, pre-commit hooks, or optional checks cannot be completed in the interruption context, they may be bypassed solely to preserve audit work. Record any skipped local check in the audit output or final note. This preservation rule does not permit bypassing source-verification requirements, citation requirements, scoring rules, unresolved-claim treatment, T4 scope warnings, or any other substantive audit safeguard.

If the push cannot be completed, preserve a local commit where possible, record the failure, and notify the user immediately.

### Audit Output

Audits are corrective workflows, not documentation-only reviews. When an audit identifies a defect that can be fixed within the selected tier, within the project's framework, and without requiring unresolved user judgment, the auditor should make the correction as part of the audit. The audit record should distinguish issues fixed during the audit from issues left unresolved for later work.

Human-relevant audit results should be visible without making issue pages unwieldy. GitHub Project fields are for tracking, filtering, triage, and machine-readable maintenance; they are not a substitute for human-facing disclosure. The retained CSV inventory is limited to source tracking. Each issue page should contain a succinct but usable **Proposal Scoring** section with the at-a-glance proposal-quality score, Adoption Score when separately reported, Coalition Support Estimates when assessed, Required Electoral Environment, Development Priority, External Review Status when assessed, Adoption Friction, and any other companion score or viability indicator grouped at the top, followed by an em dash divider, then audit status, last audit, rubric version, rebaseline status, next audit need, and a visible link to the full audit-history page. When an Adoption Score is displayed, it should include the consistent descriptor in parentheses after the score, for example: `5 / 12 (Limited Adoption Basis)`. If the compact scoring box includes Coalition Support Estimates, put the label on its own line, then list each audience estimate on indented lines using inline `<br />` breaks and `&nbsp;` spacing. Keep the compact box free of evidentiary caveats when those caveats are explained in the matching annotation segment. If visible scores or descriptors require explanation, place that explanation in annotation segments after any **Budgetary Impact** annotation segment, using labels that mirror the scoring box where practical: **Quality Score**, **Adoption Score**, **Coalition Support Estimates**, **External Review Status**, **Adoption Friction**, **Required Electoral Environment**, and **Development Priority**.

Use this compact format when coalition estimates are displayed:

```markdown
> **Coalition Support Estimates:**<br />&nbsp;&nbsp;&nbsp;&nbsp;Democratic 80%<br />&nbsp;&nbsp;&nbsp;&nbsp;Independent 60%<br />&nbsp;&nbsp;&nbsp;&nbsp;Republican 40%<br />&nbsp;&nbsp;&nbsp;&nbsp;Bipartisan viability 55%
```

The full audit history should live in a sibling file named `ISSUE-ID.audit.md` beside the issue page. For example, `areas/DOJ/issues/DOJ-001.md` should link to `areas/DOJ/issues/DOJ-001.audit.md`. The sibling audit file is the append-only technical record. New audits should add a new dated entry under **Audit History** rather than replacing, deleting, or compressing prior audit entries. Use newest-first ordering unless a page already uses another clear chronological convention. Older audit entries may be corrected only to fix clerical errors, broken links, stale line references, or clearly identified inaccuracies; do not remove them merely because the audit file becomes long. Public-facing compiled editions may omit or trim audit-history files, but source control should retain the complete technical audit history.

Each issue page with a **Proposal Scoring** section should also carry compact audit metadata in front matter: `audit_status`, `audit_score`, `audit_last_type`, `audit_last_date`, `audit_next`, `audit_rubric_version`, `audit_rebaseline_status`, `change_audit_needed`, `change_audit_reason`, and `audit_history` where applicable. Where external professional review has occurred, the page should also carry compact external-review metadata when practical: `external_review_status`, `external_review_type`, `external_review_date`, `external_review_reviewer_role`, and `external_review_notes`. These fields are for tooling and quick scanning only. They should match the issue-page **Proposal Scoring** section and sibling audit-history file. The metadata should not replace the human-readable scoring summary or audit explanation.

Each completed audit should leave a detailed sibling audit-history record that identifies:

1. audit scope;
2. audit date;
3. source record reviewed;
4. material claims verified;
5. claims left unresolved or marked for source development;
6. defects corrected during the audit;
7. unresolved findings;
8. source, legal, judicial-scrutiny, remedial, drafting, implementation, adoption, and political-language risks;
9. international-support and foreign-relations score, or why it is not applicable;
10. recommended next audit or revision;
11. whether issue-page audit front matter and Proposal Scoring were updated;
12. whether the proposal-quality score changed; and
13. why any score change is justified.

For higher-tier audits, successive audits, or audits that change the proposal-quality score, the sibling audit-history record should normally include a short narrative of the audit's major findings, a list or paragraph of sources and source categories checked, a clear distinction between verified findings and unresolved claims, a score explanation tied to the scoring rubric, and enough detail on corrected defects that a future reader can see why the proposal improved. The issue page should keep only the compact Proposal Scoring summary plus any cumulative audit findings that are genuinely useful to a reader evaluating the proposal itself.

Each completed audit should also include a brief **Audit Process Feedback** note. The note should identify whether the selected tier was adequate, what impeded or improved completion, what recurring defect or workflow friction appeared, and whether the audit framework, inventory method, source rules, scoring rules, or issue-page template should be revised before future audits. If a rule change is recommended, record the reason and apply the change only when it improves consistency, completeness, source reliability, transparency, or implementation quality.

If an audit finds serious unresolved defects, the proposal should remain below external-circulation readiness even if the page is otherwise developed.

### Audit Learning and Method Improvement

Every audit—T0 through T4, Change Audit, Horizon Scan, monitoring pass, source-development review, and Project Consistency Audit—must end by considering whether the work revealed a reusable improvement to the project's method, not merely whether the immediate page passed. Reusable improvements include a missing validation, ambiguous ownership rule, recurring reader-language problem, unreliable routing convention, overlooked evidence-placement condition, avoidable duplication, or a safeguard that would make a later audit more reliable.

Apply a finding at the narrowest durable level: correct the affected issue or its sidecar when it is issue-specific; update the governing framework or methodology when it changes a general convention; extend an existing validation script or test when the condition is objective and repeatable. Preserve historical findings in their existing audit sidecars or historical records, but do not create a new ledger merely to document learning. An improvement must remain consistent with the project framework and may not silently change substantive scope, legal conclusions, remedies, scores, or lifecycle posture; those changes retain their ordinary review and human-judgment safeguards.
