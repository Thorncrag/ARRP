---
title: "Audit Core"
status: active
dependencies:
  - "../../FRAMEWORK.md"
  - "../../AGENT_OPERATING_RULES.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Audit Core

## Authority, Loading, and Dependencies

**Authority.** This module is the reusable detailed rule set for audit orientation, the common audit workflow, issue-quality run counting, audit autonomy, preservation, and audit output. The [Framework kernel](../../FRAMEWORK.md) remains controlling for cross-cutting project principles and reserved human authority. Project-specific scoring, hosted workflow, paths, display fields, and closeout procedures belong in the project layer.

**Load when.** Load this module for every T0–T4 audit, Change Audit, Project Consistency Audit, or other formal project audit, and whenever an audit result, run count, preservation state, or audit output is created or changed.

**Dependencies.** Always load the [Framework kernel](../../FRAMEWORK.md) and [Agent Operating Rules](../../AGENT_OPERATING_RULES.md). Load the project's hosted-workflow authority whenever human-facing or machine-readable status may change. Then load the tier, Change Audit, consistency, verification, legal-review, scoring, adoption, or external-review module implicated by the selected scope. This module does not enlarge the authority granted by those records.

## Audit Rules and Proposal Quality Scoring

Before an issue or proposal is treated as ready for external circulation, it should undergo a quality audit assessing issue definition, legal authority, source support, proposal survey, remedy adequacy, abuse resistance, political adoption prospects, drafting clarity, and integration with the project inventory.

The audit should identify unresolved legal, factual, remedial, implementation, and adoption risks rather than treating completion of a draft as evidence of readiness.

Every developed issue should have the project's configured audit metadata,
visible scoring summary, and durable audit-history record. Human-facing
explanation belongs with the substantive issue; cross-project routing,
audit-control, and release-triage fields belong on the configured hosted
workflow surface.

### Pre-Audit Orientation

Every audit should begin with the Framework kernel and this Audit Core, then follow the linked governing files relevant to the audit's scope before applying the audit to an issue, proposal, hosted workflow item, inventory, candidate, or export product. The auditor need not reread every project file for every audit, but must consult enough governing material to avoid applying stale rules.

At minimum:

- all audits should consult the Framework kernel for the project's governing structure, then load the authoritative modules implicated by the audit's scope for issue architecture, drafting method, neutrality rules, source standards, Issue Snapshot format, Proposal Survey requirements, annotation conventions, cross-reference rules, audit procedure, scoring rules, tier requirements, current-status checks, output requirements, and proposal-page alignment and audit-preservation rules;
- remedy-type, least-complex-remedy, or remedial-adequacy audits should consult
  the [Remedy Selection and Design Standard](../content/remedies.md);
- print, appendix, compiled-document, PDF, DOCX, public-release, or export-placement audits should consult the reusable [Print Assembly Standard](../publication/print-assembly.md) and the project's exact publication profile;
- Change Audits should consult every governing project material listed in the Change Audit workflow before updating individual proposal pages; and
- audits that update human-facing or machine-readable status should consult the affected issue page, audit-history record, hosted workflow item, and relevant retained source records before finalizing changes.

If linked governing records appear inconsistent, document the inconsistency as a Change Audit issue and resolve or report it before relying on either rule for downstream scoring or page updates.


### Audit Workflow

Each developed proposal should be audited through the following sequence. The sequence may be run as a full review or as a targeted review, but the audit record should identify which parts were completed.

1. **Style, section-fit, concision, and reader-language audit.** Begin with the [Formatting Preflight](levels.md#formatting-preflight). Confirm that the issue follows the project's style and architecture conventions, that each main section contains material appropriate to its function, and that the main narrative is as concise as reasonably possible while still establishing the issue and proposed remedy. On reader-facing surfaces, identify unexplained project shorthand and loaded, conclusory, pejorative, or imprecise labels; replace them with direct descriptions of the conduct, basis, legal defect, or review result unless exact quoted, attributed, legally operative, or source terminology is necessary. Distinguish fact, law, disputed interpretation or uncertainty, and the project's own institutional analysis or policy position. Apply the project's public-actor and position-disclosure profile when a reasonable reader could perceive partisan alignment. Preserve exact technical terminology in internal audit and workflow records. Apply this as an editorial guideline rather than a hard word-count or section-length rule. At audit closeout, repeat the check briefly so material added during the audit does not introduce new style, section-placement, concision, neutrality, position-disclosure, or reader-comprehension problems.
2. **Issue-identification audit.** Confirm that the issue identifies a distinct institutional weakness, has the correct primary area home, is not duplicative of another issue, and is framed as a structural defect rather than as a narrative about one person or episode.
3. **Framework-compliance audit.** Confirm that the issue performs the required analytical functions: Issue Snapshot, Institutional Anomaly, Manifestation of the Failure with evidence-backed titled instances or observable categories, Resulting Damage, Underlying Weakness, Proposal Survey, Least-Complex Adequate Remedy, Repair and Prevention, Proposed Legislation where applicable, Proposed Constitutional Amendment and Proposed Enabling Legislation where applicable, Relationship to Adjacent Proposals where overlap would otherwise cause confusion, and Annotation.
4. **Enactment-pathway audit.** Confirm the minimum electoral environment required for the proposal to become seriously actionable, whether the proposal can be narrowed or staged to fit a more realistic environment, and whether further development is immediate, active, conditional, reserve, or deprioritized. This check begins at T1 and must be evidence-bound rather than speculative.
5. **Evidence and citation audit.** Confirm that factual, legal, and causal claims are supported by nearby citations, that real-world examples link to source material, and that cited external sources are captured in the project's authoritative source inventory.
6. **Legal-support audit.** Confirm that the proposal accurately identifies the constitutional, statutory, regulatory, procedural, or institutional authority on which it depends and discloses material uncertainty, doctrine, limits, or litigation risk.
7. **Existing-law and prior-proposal audit.** Confirm that the proposal checks existing law first, prefers amendment of existing vehicles where adequate, searches direct and functional analogues, and weighs prior proposals according to enacted use, institutional review, sponsorship, co-sponsorship, bipartisan support, and legislative progress.
8. **Remedy-adequacy audit.** Confirm that the proposed remedy is the least-complex adequate remedy, addresses both repair and prevention where relevant, identifies why simpler options are insufficient, preserves more complex fallback options where necessary, and materially reduces the probability that public authority can be converted into arbitrary injury.
9. **Internal remedy-fit audit.** Confirm that the issue's anomaly, manifestations, resulting damage, underlying weakness, least-complex adequate remedy, repair/prevention language, proposed legislation or other vehicle, and scoring annotations still address the same institutional defect. If recent source-development or framing updates create a mismatch, document and reconcile it when the correction remains within the human-approved foundation. Do not treat the proposal score as current while a mismatch remains unresolved; request human review when resolution would require a reserved foundational, contraction, or other materially consequential change.
10. **Implementation and enforcement audit.** Confirm that the remedy can be administered, enforced, funded, reviewed, and updated without relying on the same failed institution or norm that created the problem.
11. **Budgetary-impact audit.** Confirm that the issue page and proposal page contain the required preliminary **Budgetary Impact Statement** and that any fiscal characterization is appropriately sourced, caveated, tier-scaled, and checked against available budget or appropriations analogues. If the issue presents a preferred shared-remedy path and a separately enactable alternative, confirm that the page contains two separately labeled budget statements and distinguishes shared, incremental, function-specific, and fully standalone costs.
12. **Abuse-resistance audit.** Confirm that the remedy includes safeguards against capture, selective enforcement, evasion, delay, retaliation, pretextual use, or partisan conversion. Prepare a neutral analysis of how the existing arrangement and proposed repair would operate under materially different political control. Record and apply any existing human reversed-control decision; if that decision is material and missing, route it for human review rather than answering it.
13. **Drafting-quality audit.** Confirm that proposed legislation or rules use the appropriate legal vehicle, maintain legislative drafting conventions, define operative terms, assign responsible actors, specify procedures, and include remedies, deadlines, reporting, review, and severability where appropriate.
14. **Proposal-to-legislation consistency audit.** Where an issue page links to proposed legislation, proposed constitutional amendment text, proposed enabling legislation, or another proposal vehicle, compare the Issue Snapshot vehicle, Least-Complex Adequate Remedy, Repair and Prevention section, Proposed Legislation or amendment/enabling sections, Annotation, and scoring/audit summary against the linked bill, rule, constitutional amendment, or procedural text. Confirm that the issue page still accurately describes the operative vehicle, covered actors, legal hook, remedy type, enforcement mechanism, deadlines, responsible institutions, scope limits, and any material drafting notes. If the audit discovers a substantive discrepancy, document it and reconcile the records when the correction remains within the human-approved foundation. Leave it unresolved and request human approval only when the correction would change a reserved foundation, materially contract the proposal, or make another reserved change.
15. **Hallucination-resistance and verification audit.** Confirm that the issue contains no invented, uncited, stale, unverifiable, or overconfident claims, and that every material factual, legal, polling, legislative-history, scholarly, real-world-example, or fiscal-impact assertion is traceable to reliable source material.
16. **Judicial and scholarly scrutiny audit.** Confirm that the proposal has been tested against likely Supreme Court, relevant lower-court, and serious legal-scholar objections, and that the issue records deeply researched recommendations for increasing the likelihood that the proposal would be upheld.
17. **Argument and cogency audit.** Confirm that the page makes the complete chain from human harm or material risk, through the institutional defect and operation of public authority, to the proposed repair and its anti-arbitrariness safeguards visible without hidden premises, overclaiming, unsupported causation, or remedy mismatch.
18. **Support and adoption audit.** Confirm that the issue can be explained to likely supporters, skeptics, lawmakers, staff, experts, and the public in terms of institutional repair rather than partisan advantage.
19. **Political-language and coalition-appeal audit.** Confirm that the proposal remains candid about misconduct while using institution-focused language and estimating likely support from bipartisan, independent, Democratic, and Republican audiences.
20. **Project-integration audit.** Confirm that internal and proposal-vehicle links, issue posture, remedy type, source inventory, audit metadata, audit history, hosted canonical-page links, project and area contents, subject index, hosted registry, and compiled-document placement remain consistent. At the project's configured tier, perform its Navigation Synchronization Check for a stable reader-facing record.


### Audit Run Counting Rule

The project run counter includes only completed, separately recorded
issue-quality audits expressly conducted at a configured tier. Each completed
tier counts once. A cumulative highest-tier audit counts as one run unless
lower tiers were separately performed, completed, and recorded as distinct
events. A successive sequence counts each tier actually completed and
separately memorialized.

Change Audits, Internal Remedy-Fit Audits, Project Consistency Audits,
candidate scans, source-development passes, drafting sessions, formatting
reviews, hold-predicate checks, external-review intake, validation reruns,
dashboard refreshes, bookkeeping corrections, and continuations of the same
still-open tier do not increment the run counter. When one occurs inside a
tiered audit, it receives no additional count. An abandoned, interrupted, or
blocked tier does not count until completed and closed.

The run count is procedural history, not a quality score. Lower tiers may count
even when they do not produce a formula score; a score-changing Change Audit
does not count unless a distinct tiered audit also completed. Correct a
miscount in the configured tracking field and summaries without inventing a
tier or rewriting substantive history.

Issue-quality audits should be run on exactly one issue at a time. Before
starting, identify the target issue by its stable identifier and canonical
path. If the request could refer to more than one issue, or if the identity is
missing or unclear, ask the user to identify the issue before beginning the
audit. Project-wide discovery scans and project-consistency audits are standing
non-scoring exceptions; neither may be used as a substitute for scoring or
substantively revising an individual issue.


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

When a defect can be corrected without user input, correct it rather than only
noting it. Examples include broken links, stale source or hosted-workflow
records, missing source-inventory capture, obvious citation-placement defects,
metadata inconsistencies, formatting defects, posture inconsistencies, and
framework-compliance gaps supported by the existing record. Do not make
substantive policy choices, legal judgments, or factual claims requiring
unresolved support; mark those unresolved and notify the user.

### Audit Preservation and Closeout

After an audit completes, or when it is interrupted after making useful
changes, preserve the work promptly through the project's configured
repository, hosted-workflow, and handoff procedures. Closeout must synchronize
every surface that would otherwise drift, read back authoritative hosted
values, complete or document validation, and leave exact continuation state
for any unfinished critical step.

An interruption may bypass optional local checks only to preserve completed
work. Record each skipped check. This exception never bypasses source
verification, citation requirements, scoring rules, unresolved-claim
treatment, selected-tier safeguards, or another substantive audit rule.

The project layer owns exact commit, push, hosted-field, generated-view,
readback, and failure-state procedures.

### Audit Output

Audits are corrective workflows, not documentation-only reviews. When an audit identifies a defect that can be fixed within the selected tier, within the project's framework, and without requiring unresolved user judgment, the auditor should make the correction as part of the audit. The audit record should distinguish issues fixed during the audit from issues left unresolved for later work.

Human-relevant audit results should remain visible without making the
substantive issue unwieldy. Hosted fields support tracking, filtering, triage,
and machine-readable maintenance; they do not replace human-facing disclosure.
Use the project scoring profile's exact display labels, metadata, companion
scores, descriptors, and audit-history path convention. Technical metadata
must agree with the visible summary and durable audit history and must not
replace either.

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

Every audit—T0 through T4, Change Audit, project-wide discovery scan,
monitoring pass, source-development review, and project-consistency
audit—must end by considering whether the work revealed a reusable improvement
to the project's method, not merely whether the immediate page passed.
Reusable improvements include a missing validation, ambiguous ownership rule,
recurring reader-language problem, unreliable routing convention, overlooked
evidence-placement condition, avoidable duplication, or a safeguard that would
make a later audit more reliable.

Apply a finding at the narrowest durable level: correct the affected issue or its sidecar when it is issue-specific; update the governing framework or methodology when it changes a general convention; extend an existing validation script or test when the condition is objective and repeatable. Preserve historical findings in their existing audit sidecars or historical records, but do not create a new ledger merely to document learning. An improvement must remain consistent with the project framework and may not silently change substantive scope, legal conclusions, remedies, scores, or lifecycle posture; those changes retain their ordinary review and human-judgment safeguards.
