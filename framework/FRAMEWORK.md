# American Restoration and Resilience Project — Technical Framework

This file contains the project's technical operating framework: method, issue architecture, evidence standards, remedy standards, repository structure, file conventions, print assembly, contribution process, release process, and development backlog.

The project's public-facing premise, mission, scope, and governing principles are maintained in [`../README.md`](../README.md).

## Core Method

**Identify the problem.** Determine what institution or governing process failed, how the failure manifested, and what damage resulted.

**Identify the weakness.** Determine which law, structure, procedure, remedy, or norm permitted the failure or proved inadequate to constrain it.

**Identify repair and prevention.** Determine what must be restored or corrected now and what safeguards are necessary to prevent recurrence.

**Identify the least-complex adequate remedy.** Determine the least-complex measure, or package of measures, capable of adequately addressing the defect.

## Issue-Admission Test

Before promoting a candidate into a standalone issue, ask:

> Does this candidate identify a distinct institutional weakness requiring separate diagnosis or remedial analysis?

If not, merge it into a broader issue, treat it as a manifestation or example, cross-reference it, or retain it only in the research inventory.

## Unit of Analysis

Each issue must identify a generalized structural defect. Trump-era or other-administration incidents illustrate the defect but do not define it.

## Mandatory Issue Architecture

Every developed issue should use the following structure:

1. **Issue Snapshot** — a short reader-navigation box summarizing problem, repair, and vehicle.
2. **Institutional Anomaly** — a concise, generalized statement of the structural defect.
3. **Manifestation of the Failure** — only the representative facts necessary to show how the defect operates.
4. **Resulting Damage** — the principal institutional, legal, factual, administrative, or legitimacy harm.
5. **Underlying Weakness** — the law, structure, procedure, remedy, or norm that failed.
6. **Repair and Prevention** — restoration or correction of existing damage and prospective safeguards against recurrence.
7. **Proposed Legislation** — link to the proposed legislative, rule, constitutional, or procedural vehicle when one exists.
8. **Proposal Survey** — concise review of prior or adjacent models bearing on the remedy.
9. **Least-Complex Adequate Remedy** — the least-complex measure or package capable of adequately addressing the defect.
10. **Annotation** — evidence, legal analysis, qualifications, alternatives, and implementation constraints.

The headings guide analysis but do not require artificial expansion. Each section should add a distinct proposition.

Custom section headings are permitted where they make a developed issue clearer or more natural to read, provided the issue still performs the required analytical functions. A custom heading should be meaningfully distinct from the canonical heading it replaces rather than a trivial restatement. Where custom headings are used, the required function should remain clear from the heading itself, the surrounding structure, or a short orienting sentence.

Where proposed legislation or another concrete reform vehicle exists, the issue page should include a **Proposed Legislation** section immediately after **Repair and Prevention**. This placement lets a reader move directly from diagnosis and repair to the proposed vehicle before reading the deeper survey, remedy analysis, annotation, or audit record.

### Issue Snapshot Format

Each developed issue page should place an **Issue Snapshot** blockquote immediately after the issue title and before **Institutional Anomaly**. The snapshot is a reader-navigation device: it should let a reader move quickly from problem to proposed solution without reading the full issue page first.

The Issue Snapshot should be extremely concise. Each line should normally convey its point in about twelve words or fewer. To render consistently in both GitHub and Codex previews, keep the snapshot fields in a single blockquote paragraph and separate **Problem**, **Repair**, and **Vehicle** with inline `<br />` tags:

1. **Problem:** the institutional weakness.
2. **Repair:** the core proposed fix.
3. **Vehicle:** the legal or institutional form of the remedy, with a relative Markdown link to proposed legislation or amendment text where a draft exists.

Use this format:

```markdown
> ## Issue Snapshot
> **Problem:** Short problem statement.<br />**Repair:** Short repair statement.<br />**Vehicle:** Remedy vehicle ([draft link]).
>
```

### Proposal Survey

Each developed issue should include a concise survey of prior legislative, regulatory, constitutional, procedural, or institutional models that bear on the proposed remedy. The survey should identify the closest models, cite or link them, and explain why the project adopts, narrows, rejects, or combines them. It should appear before **Least-Complex Adequate Remedy** so the preferred remedy follows the comparison.

## Issue-Level Conciseness

Conciseness is an area-level and issue-level constraint, not an overall document-length limit. Each issue should be stated in the minimum space necessary to identify the defect, damage, weakness, repair, prevention, and remedy. Additional detail belongs in annotation or source notes.

Representative incidents should illustrate the structural defect, not become exhaustive narrative histories.

## Annotation and Evidence

### Standard Annotation

**Basis and Evidence.** Explain why the anomaly has been identified and cite representative authoritative support.

**Qualification.** State material uncertainty, competing interpretations, and limits necessary to keep the main assertion accurate.

**Remedial Alternatives and Constraints.** Briefly identify materially serious fallback options and the constitutional, statutory, administrative, or practical limits affecting the least-complex remedy.

### Assertion Discipline

State each institutional conclusion as directly as the record permits. An annotation must substantiate rather than retreat from the main assertion. Distinguish established fact, legal conclusion, institutional inference, and normative judgment.

### Source Standard

Use primary legal and governmental records first. Use authoritative institutional and academic sources for doctrine, design, and comparative analysis. Use high-quality secondary reporting mainly for synthesis and discovery.

Every factual, legal, and causal proposition must remain independently supportable. When an issue file refers to a real-life event, case, official action, report, statute, rule, hearing, order, or other source material, include a nearby citation or link. Do not name concrete examples in issue text without enough source information for later verification.

When referring to another page in this project, use a relative Markdown link whenever the target page exists. If the referenced issue exists only as an inventory or area-index entry, link to the nearest project page that contains that entry.

## Least-Complex Adequate Remedy

The Least-Complex Adequate Remedy is mandatory in every developed issue and functions as the project’s provisional preferred remedy.

Complexity should be assessed by legal difficulty, administrative burden, implementation speed, enforceability, durability, cost, and need for constitutional change. Simplicity is not sufficient where the simpler measure would be ineffective, temporary, unenforceable, or easily evaded.

The main text need not catalogue every conceivable remedy. It should identify the least-complex adequate measure or package and explain why it is adequate. Annotation should briefly note materially simpler but insufficient options and more complex fallback options that may be necessary for completeness, durability, or constitutional reasons.

Adequacy should be evaluated against the remedy’s proper function. Where prevention is feasible, the remedy should prevent. Where necessary discretion or constitutional structure makes complete prevention impracticable, adequacy may instead require reliable detection, evidence preservation, independent review, mandatory reporting, correction, discipline, compensation, legislative response, or another credible self-corrective mechanism.

The assessment remains provisional rather than irrevocable and may be revised as the record develops.

## Repair and Prevention

Every issue must consider both repair and prevention. Some issues may require restoration, investigation, disclosure, recovery, correction of the public record, rebuilding of capacity, or compensation. Prevention may require substantive legal limits, structural independence, professional safeguards, oversight, enforcement, transparency, procedural reform, or constitutional change.

The distinction is mandatory to consider but need not receive equal prose where one side is not materially relevant. Issues should also identify whether the proposed safeguard primarily prevents, detects, corrects, deters, or contains institutional abuse.

## Constitutional Amendments

Constitutional amendments are within scope and must not be excluded. Adequate non-amendment remedies should generally receive greater emphasis because Article V is unusually difficult and slow. Amendment options must nevertheless be preserved where lesser measures cannot lawfully, completely, or durably solve the problem.

## Automatic Constitutional Stabilizers and Institutional-Failure Triggers

A constitutional system should not permit persistent failure of essential governing processes to continue indefinitely without changing the legal allocation of power.

Trigger mechanisms are a limited, cross-cutting remedial tool. They may include mandatory notice, fixed deadlines, compulsory votes, expiration of temporary authority, caretaker succession, expedited review, temporary contraction of discretionary authority, or constitutional mechanisms for extraordinary cumulative failure.

Triggers are not a universal solution and do not organize or subsume the rest of the project. Apply them only where persistent institutional failure can be addressed through objective, measurable, proportionate, manipulation-resistant escalation or reallocation mechanisms. Many issues will instead require substantive limits, structural independence, disclosure, professional safeguards, enforcement, oversight, funding reform, or constitutional change.

## Overlap and Cross-Reference Rule

Each institutional defect should have one primary home. Related areas should cross-reference the primary issue instead of repeating the same diagnosis, evidence, and remedy. The issue inventory may identify related areas without creating duplicate substantive sections.

## Proposal Quality Audit

Before an issue or proposal is treated as ready for external circulation, it should undergo a quality audit assessing issue definition, legal authority, source support, proposal survey, remedy adequacy, abuse resistance, political adoption prospects, drafting clarity, and integration with the project inventory.

The audit should identify unresolved legal, factual, remedial, implementation, and adoption risks rather than treating completion of a draft as evidence of readiness.

Every issue should have a corresponding row in [`../inventory/audits.csv`](../inventory/audits.csv). That row records the current proposal-quality score, audit count, audit status, score basis, and next audit need.

### Audit Workflow

Each developed proposal should be audited through the following sequence. The sequence may be run as a full review or as a targeted review, but the audit record should identify which parts were completed.

1. **Issue-identification audit.** Confirm that the issue identifies a distinct institutional weakness, has the correct primary area home, is not duplicative of another issue, and is framed as a structural defect rather than as a narrative about one person or episode.
2. **Framework-compliance audit.** Confirm that the issue performs the required analytical functions: Issue Snapshot, Institutional Anomaly, Manifestation of the Failure, Resulting Damage, Underlying Weakness, Repair and Prevention, Proposed Legislation where applicable, Proposal Survey, Least-Complex Adequate Remedy, and Annotation.
3. **Evidence and citation audit.** Confirm that factual, legal, and causal claims are supported by nearby citations, that real-world examples link to source material, and that all cited external sources are captured in [`../inventory/sources.csv`](../inventory/sources.csv).
4. **Legal-support audit.** Confirm that the proposal accurately identifies the constitutional, statutory, regulatory, procedural, or institutional authority on which it depends and discloses material uncertainty, doctrine, limits, or litigation risk.
5. **Existing-law and prior-proposal audit.** Confirm that the proposal checks existing law first, prefers amendment of existing vehicles where adequate, and weighs prior proposals according to enacted use, institutional review, sponsorship, co-sponsorship, bipartisan support, and legislative progress.
6. **Remedy-adequacy audit.** Confirm that the proposed remedy is the least-complex adequate remedy, addresses both repair and prevention where relevant, identifies why simpler options are insufficient, and preserves more complex fallback options where necessary.
7. **Implementation and enforcement audit.** Confirm that the remedy can be administered, enforced, funded, reviewed, and updated without relying on the same failed institution or norm that created the problem.
8. **Abuse-resistance audit.** Confirm that the remedy includes safeguards against capture, selective enforcement, evasion, delay, retaliation, pretextual use, or partisan conversion.
9. **Drafting-quality audit.** Confirm that proposed legislation or rules use the appropriate legal vehicle, maintain legislative drafting conventions, define operative terms, assign responsible actors, specify procedures, and include remedies, deadlines, reporting, review, and severability where appropriate.
10. **Hallucination-resistance and verification audit.** Confirm that the issue contains no invented, uncited, stale, unverifiable, or overconfident claims, and that every material factual, legal, polling, legislative-history, scholarly, or real-world-example assertion is traceable to reliable source material.
11. **Judicial and scholarly scrutiny audit.** Confirm that the proposal has been tested against likely Supreme Court, relevant lower-court, and serious legal-scholar objections, and that the issue records deeply researched recommendations for increasing the likelihood that the proposal would be upheld.
12. **Argument and cogency audit.** Confirm that the problem, weakness, damage, remedy, and implementation logic follow from each other without hidden premises, overclaiming, unsupported causation, or remedy mismatch.
13. **Support and adoption audit.** Confirm that the issue can be explained to likely supporters, skeptics, lawmakers, staff, experts, and the public in terms of institutional repair rather than partisan advantage.
14. **Political-language and coalition-appeal audit.** Confirm that the proposal remains candid about misconduct while using institution-focused language and estimating likely support from bipartisan, independent, Democratic, and Republican audiences.
15. **Project-integration audit.** Confirm that internal links, legislation links, issue status, remedy type, source inventory, audit inventory, contents index, area page, and compiled-document placement remain consistent.

### Audit Resource Tiers

Audits should be scoped to a stated resource tier before work begins. A smaller tier is not a failed larger audit; it is a deliberately budgeted review. The audit record should identify the tier used, what was completed, what was skipped, and what the next higher tier should examine.

Audits should be run on exactly one issue at a time. Before starting, identify the target issue by issue ID and page path. If the request could refer to more than one issue, or if the issue ID is missing or unclear, ask the user to identify the issue before beginning the audit.

Before starting a new audit for an issue, check the most recent audit record for unresolved blocking findings, skipped prerequisites, source-development tasks, or user-input needs that must be resolved before further audit work can proceed. If blocking unresolved items remain from the last audit, cancel the new audit request, notify the user, and ask whether to resolve the existing items, explicitly override the block, or revise the audit scope. Do not begin a new audit until the user gives direction. Ordinary next-audit recommendations do not block a new audit when the requested audit is meant to address them.

If the user requests an audit without specifying a tier, ask which tier to run rather than guessing. The default recommendation should be the lowest level that appears useful, usually **T0: Triage scan** for a new or ambiguous request. Do not silently escalate to a higher tier.

Before running a higher-tier audit, confirm that the immediately lower tier has already been completed for the issue and remains reasonably current. If the lower tier has not been completed, ask the user whether to run the lower tier first or explicitly skip it. If the user confirms skipping a lower tier, record that skipped prerequisite in the audit output.

| Tier | Estimated time | Purpose | Expected output |
| --- | ---: | --- | --- |
| **T0: Triage scan** | 5 minutes or less | Catch obvious blockers before deeper work. | One-paragraph status, obvious defects, and whether deeper audit is needed. |
| **T1: Framework check** | 30 minutes or less | Check internal project consistency and visible framework compliance. | Short checklist covering structure, links, metadata, legislation link, issue status, remedy type, source-inventory presence, and obvious unsupported claims. |
| **T2: Development audit** | 2 hours or less | Verify the proposal enough to guide revision and provisional scoring. | Component-level score estimate, key source checks, current public-source refresh, legal-fit notes, remedy-fit notes, major risks, and next audit needs. |
| **T3: Readiness audit** | 6 hours or less | Test whether a proposal is close to external circulation. | Reproducible score, source-refresh log, verified claims, unresolved claims, legal and judicial-scrutiny risks, adoption/support notes, international score or `N/A`, and recommended revisions. |
| **T4: Publication-ready audit** | 18 hours or less | Resolve every publication concern that can reasonably be resolved through deep public-source research before external circulation. | Publication-readiness memo, final score recommendation, deep source-refresh log, verified and unresolved claims table, legal-durability analysis, prior-proposal comparison, adoption and opposition analysis, international score or `N/A`, drafting recommendations, and expert-review needs. |

Tier times are planning estimates rather than hard caps. If an audit exceeds the estimate by a reasonable degree and is close to a responsible stopping point, the auditor may finish the current audit unit. The audit should not exceed 150% of the selected tier's estimated time without explicit user approval.

Tier estimates are not minimums. If a responsible audit can be completed in less than the selected tier's estimated time, finish early rather than filling the allotted time. Record that the audit finished under estimate and use that result to calibrate future audit budgeting for comparable issues.

The **T4: Publication-ready audit** must not be run by default. It requires additional explicit user confirmation after the user is told the expected time estimate, likely scope, and that the audit may still identify issues requiring attorney, legislative-counsel, subject-matter expert, or stakeholder review.

A T4 audit should address every reasonably researchable publication concern, including source verification, current-law status, prior-proposal history, legislative drafting vulnerabilities, constitutional and administrative-law risks, judicial-scrutiny concerns, implementation feasibility, abuse resistance, adoption strategy, opposition arguments, public-support evidence, international implications where material, and consistency with the project's framework and inventories. It should not claim to replace professional legal advice, legislative counsel, empirical polling, fiscal scoring, or stakeholder validation.

If the selected tier cannot responsibly complete a required check within the estimate plus reasonable overage, skip that portion, mark it unresolved, assign no favorable credit for it, and identify it as work for the next tier. Do not expand beyond the selected tier unless the user asks for a deeper audit.

The selected resource tier affects audit scope and confidence, not the weighting of the scoring formula. Do not give a proposal extra credit because it was reviewed under a higher tier, and do not penalize a proposal merely because the user selected a lower tier. Apply the same component weights at every tier. Components not actually reviewed or supported within the selected tier should be marked unresolved and receive no favorable credit until reviewed.

The auditor should not allow any single audit area, source dispute, legal question, factual cluster, or research thread to consume the whole tier estimate. Allocate time across the major audit areas, use conservative scoring for unresolved portions, and move unresolved clusters into the next-audit list rather than continuing indefinitely.

On the first audit run for an issue, the auditor should do what can reasonably be accomplished within the selected target tier. If calibration requires more time, the auditor may use reasonable overage up to 150% of the selected tier's estimated time. Moving beyond that ceiling, including spillover into the next tier's full estimate, requires explicit user approval. T4 may never be reached by spillover; it always requires separate explicit confirmation.

Future audits should use prior audit results to adjust scope within the selected timeframe. If prior work already verified a component and the underlying sources have not changed, spend less time there and use the saved time on unresolved or changed components. If prior work showed an area is unusually complex, timebox that area earlier and document the follow-up need instead of allowing it to crowd out the rest of the audit.

Successive audits should be improvement-targeted. After the first audit, the auditor should identify the unresolved components, penalties, or source gaps most likely to raise the Proposal Quality Score within the selected tier and target work there first. The goal is to improve the proposal's actual quality, reliability, and adoption readiness, not merely to repeat completed checks. A score should rise only when the audit actually resolves findings, verifies support, improves legal fit, strengthens drafting, reduces risk, or otherwise satisfies the scoring rules.

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

When a defect can be corrected without user input, correct it rather than only noting it. Examples include broken links, missing internal links, stale inventory rows, missing source-inventory capture, obvious citation-placement defects, metadata inconsistencies, formatting defects, issue-status inconsistencies, and framework-compliance gaps that can be fixed from the existing record. Do not make substantive policy choices, legal judgments, or factual claims that require unresolved source support; mark those unresolved and notify the user.

### Audit Preservation and GitHub Storage

After an audit is completed, or if an audit is interrupted after changes have been made, preserve the work promptly. Where the repository and remote are available, create the necessary non-interactive commit or commits and push them to the configured GitHub remote without asking the user additional process questions, unless approval is required by the working environment or by this framework.

If local validation, formatting, pre-commit hooks, or optional checks cannot be completed in the interruption context, they may be bypassed solely to preserve audit work. Record any skipped local check in the audit output or final note. This preservation rule does not permit bypassing source-verification requirements, citation requirements, scoring rules, unresolved-claim treatment, T4 confirmation, the 150% audit-overage rule, or any other substantive audit safeguard.

If the push cannot be completed, preserve a local commit where possible, record the failure, and notify the user immediately.

### Audit Output

Audits are corrective workflows, not documentation-only reviews. When an audit identifies a defect that can be fixed within the selected tier, within the project's framework, and without requiring unresolved user judgment, the auditor should make the correction as part of the audit. The audit record should distinguish issues fixed during the audit from issues left unresolved for later work.

Human-relevant audit results should be visible on the issue page itself. CSV files are for tracking, indexing, verification, and machine-readable maintenance; they are not a substitute for human-facing disclosure. When an audit is completed, update the issue page with a concise **Audit Record** or equivalent section identifying the latest audit tier, date, proposal-quality score, corrections made, unresolved findings, material caveats, score limitations, and next audit need. Do not leave any information that a human reader would reasonably need to understand the issue's audit posture only in [`../inventory/audits.csv`](../inventory/audits.csv), [`../inventory/sources.csv`](../inventory/sources.csv), or another inventory file.

Each developed issue page should also carry compact audit metadata in front matter: `audit_status`, `audit_score`, `audit_last_type`, `audit_last_date`, and `audit_next`. These fields are for tooling and quick scanning only. They should match the latest visible **Audit Record** and [`../inventory/audits.csv`](../inventory/audits.csv), but they should not replace the human-readable audit explanation on the page.

Each completed audit should leave a concise record that identifies:

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
11. whether issue-page audit front matter was updated;
12. whether the proposal-quality score changed; and
13. why any score change is justified.

Each completed audit should also include a brief **Audit Process Feedback** note. The note should identify whether the selected tier was adequate, whether the audit finished under or over estimate, what slowed or improved the audit, what recurring defect or workflow friction appeared, and whether the audit framework, inventory method, source rules, scoring rules, or issue-page template should be revised before future audits. If a rule change is recommended, record the reason and apply the change only when it improves consistency, source reliability, transparency, resource control, or implementation quality.

If an audit finds serious unresolved defects, the proposal should remain below external-circulation readiness even if the page is otherwise developed.

### Hallucination-Resistance and Verification Protocol

The audit must be designed to minimize invented, overstated, or unverifiable claims. The default rule is: **if the project record does not contain reliable support for a claim, the claim is unresolved and receives no audit credit.**

Apply the following rules in every audit:

1. **Current-source refresh.** Do not assume the project record, prior audit, or model memory contains the latest relevant information. At the start of any substantive audit, check current sources for recent legal developments, legislation, court action, agency action, news, public-opinion evidence, stakeholder statements, scholarship, advocacy activity, implementation experience, international reactions, and other materials that could support, weaken, refine, or reframe the proposal.
2. **Government and institutional source sweep.** Check relevant government institutions and public bodies, including federal, state, local, tribal, territorial, and international sources where relevant; courts and court dockets; legislative bodies and committee materials; administrations, departments, bureaus, agencies, offices, inspectors general, commissions, boards, independent agencies, public authorities, and official blogs, journals, reports, guidance, data portals, press releases, and enforcement records.
3. **Public legal-research source sweep.** Check public-access legal research hubs and legal-information services relevant to the issue, such as CourtListener, RECAP, Justia, Google Scholar, Congress.gov, GovInfo, Federal Register, eCFR, state legislative portals, state court portals, agency adjudication databases, public law-library guides, bar-association materials, legal blogs, legal newsletters, and comparable open resources. Do not require paid-access legal databases, and do not imply that paywalled systems were checked.
4. **Professional and research source sweep.** Where relevant, check current professional journals, law reviews, policy journals, latest research, working papers, technical reports, and comparable data-bearing sources.
5. **Broad discovery, careful validation.** Discovery may include official records, court dockets, agency materials, congressional and state-legislative records, reputable news organizations, local news, trade publications, well-regarded blogs, independent media, newsletters, watchdog organizations, advocacy groups, think tanks, and academic commentary where relevant. These sources may identify leads, examples, objections, public salience, possible supporters, diplomatic concerns, or international reactions, but audit credit requires reliable verification and appropriate characterization.
6. **Primary-source preference.** When a discovery source points to a statute, bill, amendment, hearing, vote, court filing, order, agency action, poll, report, quotation, official statement, or international action, verify the underlying primary material before treating the proposition as established.
7. **Recency log.** Record the date the current-source refresh was performed, the source categories checked, the search terms or repositories used where practical, and any fresh sources added or intentionally rejected. Paid-access database nonuse need not be treated as an audit defect.
8. **No invented authority.** Do not cite or rely on a case, statute, bill, rule, executive order, regulation, report, poll, scholar, organization, official, quotation, date, docket, vote count, sponsor count, co-sponsor count, international body, foreign-government statement, or factual episode unless it is verified from a reliable source.
9. **No source laundering.** Do not cite a secondary source as though it were primary authority. Where a secondary source identifies a case, bill, report, poll, official action, or international reaction, verify the underlying primary material before treating the proposition as established.
10. **Nearby-source rule.** Every material factual, legal, causal, polling, legislative-history, international-relations, or real-world-example claim should have a nearby citation or a clearly identified source note.
11. **Source-inventory rule.** Every external source used for audit credit must be captured in [`../inventory/sources.csv`](../inventory/sources.csv), with enough context to check what proposition it supports.
12. **Claim-status rule.** Classify important propositions as established fact, legal conclusion, institutional inference, policy judgment, public-opinion evidence, international-relations assessment, prediction, discovery lead, allegation, or unresolved question. Do not let one category masquerade as another.
13. **Current-law check.** For statutes, regulations, rules, official roles, court doctrine, agency structures, and pending legislation, verify that the cited authority is current or clearly label it as historical.
14. **Polling and public-support check.** Polling, survey, referendum, state-practice, and popular-support claims must identify the source, date, jurisdiction, population, sample or methodology where available, question wording where material, and whether the evidence supports the actual mechanism or only an adjacent principle.
15. **Legislative-history check.** Sponsor counts, co-sponsor counts, bipartisan status, committee action, chamber passage, enactment, or repeated introduction must be verified from congressional, state-legislative, or other authoritative legislative records.
16. **Judicial-doctrine check.** Supreme Court, lower-court, and state-court claims must identify the relevant case, holding, doctrine, standard of review, and uncertainty. Do not infer current doctrine from memory where direct verification is feasible.
17. **Scholarly-authority check.** Do not invoke legal scholars, experts, journals, research consensus, or professional consensus unless the audit identifies the author or institution, work, claim, publication context, methodology where material, and any meaningful disagreement.
18. **International-relations check.** International-support, diplomatic, treaty, alliance, foreign-government, multilateral-institution, democracy-index, rule-of-law, human-rights, security, or comparative-law claims must identify the jurisdiction or institution, source, date, relevance, and any countervailing evidence.
19. **Media-source characterization.** News, blogs, independent media, and newsletters should be characterized according to what they can reliably support: reported facts, allegations, public salience, stakeholder framing, emerging examples, opposition arguments, international reactions, or leads requiring confirmation.
20. **Quote discipline.** Direct quotations must be exact, limited, and traceable to a cited source. Paraphrases should not imply stronger support than the source provides.
21. **No false precision.** Do not give numerical estimates, probabilities, dates, vote counts, support percentages, fiscal impacts, litigation odds, adoption likelihoods, or diplomatic impacts unless the basis is identified. If an estimate is judgment-based, label it as such and explain the inputs.
22. **Temporal discipline.** Distinguish current, pending, superseded, expired, proposed, enacted, stayed, vacated, reversed, alleged, reported, projected, or historical authorities.
23. **Adverse-evidence rule.** If reliable sources materially undermine the claim, identify the conflict rather than selecting only favorable evidence.
24. **Unverified-placeholder rule.** Use explicit placeholders such as `Source needed`, `Verification pending`, `Discovery lead only`, or `Unresolved` rather than drafting around missing support.

An audit may recommend research, but it may not award score credit for research that has not been performed. Hallucination-resistance failures should be treated as source, legal-fit, adoption, or drafting defects as applicable.

### Proposal Quality Score

The **Proposal Quality Score** is a provisional 0-100 planning value. It measures how ready the proposal is for reliance, external review, legislative outreach, or publication as a mature recommendation. It is not a measure of how important the underlying problem is.

Scores must be calculated consistently. A repeated audit using the same record, same rubric, and same findings should produce the same score. Audit count may inform the score only through the formula below; repetition alone must not increase the value. A score should increase only when an audit meaningfully broadens review, resolves findings, verifies sources, improves legal fit, strengthens drafting, reduces implementation risk, or improves adoption prospects without weakening the least-complex adequate remedy.

Use this mathematical formulation for developed proposals:

```
Proposal Quality Score =
  Structural Score
+ Evidence Score
+ Legal Fit Score
+ Prior-Proposal Score
+ Remedy Score
+ Implementation Score
+ Abuse-Resistance Score
+ Drafting Score
+ Cogency Score
+ Adoption Score
+ Project-Integration Score
+ External-Review Score
- Penalties
```

| Component | Maximum points |
| --- | ---: |
| Structural Score | 10 |
| Evidence Score | 12 |
| Legal Fit Score | 10 |
| Prior-Proposal Score | 8 |
| Remedy Score | 12 |
| Implementation Score | 8 |
| Abuse-Resistance Score | 8 |
| Drafting Score | 8 |
| Cogency Score | 8 |
| Adoption Score | 8 |
| Project-Integration Score | 4 |
| External-Review Score | 4 |
| **Total before penalties** | **100** |

For consistent application, use these component definitions:

| Component | Full-score standard |
| --- | --- |
| Structural Score | The issue has the required architecture, correct issue ownership, accurate status, and no unresolved duplication. |
| Evidence Score | Material factual, legal, causal, and real-world-example claims have nearby citations and source-inventory coverage. |
| Legal Fit Score | The proposal identifies verified authority, limits, doctrines, vulnerabilities, and judicial-scrutiny issues. |
| Prior-Proposal Score | Existing law and prior models have been checked against authoritative records and weighted by enacted use, institutional review, sponsorship, co-sponsorship, bipartisan support, and legislative progress. |
| Remedy Score | The remedy is the least-complex adequate remedy and addresses repair, prevention, fallback options, and remedy mismatch risk. |
| Implementation Score | The proposal can be administered, funded, enforced, reviewed, and updated without unrealistic institutional assumptions. |
| Abuse-Resistance Score | Capture, evasion, delay, retaliation, pretext, selective enforcement, and partisan conversion risks are identified and mitigated. |
| Drafting Score | Legislative or rule text uses proper vehicle, conventions, definitions, responsible actors, procedures, remedies, deadlines, review, and severability. |
| Cogency Score | The problem, weakness, damage, remedy, and implementation logic follow from each other without hidden premises or overclaiming. |
| Adoption Score | Support appeal, public-support evidence, audience fit, objection handling, adoption vehicle, and coalition strategy are documented. |
| Project-Integration Score | Internal links, legislation links, issue status, remedy type, source inventory, audit inventory, contents index, area page, and compiled-document placement are consistent. |
| External-Review Score | Appropriate expert, practitioner, legislative, stakeholder, judicial-scrutiny, or scholarly review has been incorporated. |

Apply each component as follows:

1. Award full points only when the relevant audit is complete and no material unresolved finding remains.
2. Award half points when the element is substantially present but has unresolved nonfatal findings.
3. Award zero points when the element is missing, materially unsupported, internally inconsistent, or not yet audited.
4. Do not estimate a component from general confidence. If evidence is unavailable, score the component as zero and record the missing work as the next audit need.
5. Do not award component credit based on memory, assumed expertise, model-generated assertions, or uncited background knowledge where verification is feasible.
6. Round only the final score, using ordinary whole-number rounding. If the result is exactly halfway between two whole numbers, round down.
7. If two auditors applying the same record would plausibly differ, use the lower score and record the ambiguity.

Apply penalties after adding component scores:

| Penalty | Points |
| --- | ---: |
| Unsupported material factual claim | -5 each |
| Unsupported material legal claim | -5 each |
| Missing nearby citation for a named real-world event | -3 each |
| Missing source inventory row for an external source | -2 each |
| Citation does not support the proposition for which it is used | -5 each |
| Invented or unverified case, statute, bill, poll, report, scholar, official action, quotation, sponsor count, or vote count | -10 each |
| Current-law, pending-legislation, polling, or public-support claim not checked for currency | -5 each |
| Internal project link missing where target exists | -1 each |
| Remedy depends on the same failed institution without fallback | -8 |
| Serious abuse, evasion, or selective-enforcement risk unaddressed | -8 |
| Proposed legislation departs from legislative conventions without justification | -5 |
| Judicial-scrutiny risk not identified for a legally vulnerable proposal | -5 |
| Existing-law amendment path not checked before new architecture | -5 |
| Duplicative issue ownership unresolved | -5 |

The final score may not be lower than 0 or higher than 100. Penalties should be recorded as findings so a later audit can reproduce the same calculation and remove the penalty only when the defect has been corrected.

### Adoption Score Formula

The **Adoption Score** is part of the 100-point proposal-quality score and is capped at 8 points. It should be calculated the same way in each audit:

| Adoption subcomponent | Points |
| --- | ---: |
| Audience segmentation and audience-specific value proposition | 1 |
| Good-faith objection handling across partisan, independent, federalism, civil-liberties, administrative, and constitutional perspectives | 1 |
| Adoption vehicle and plausible sponsor, validator, or coalition map | 1 |
| Public-trust and reciprocity showing the proposal applies fairly across parties and administrations | 1 |
| Current, methodologically credible national polling or survey evidence supports the underlying reform principle | 1 |
| Current, methodologically credible state-level polling, referendum results, enacted-state practice, or comparable state evidence supports the underlying reform principle | 1 |
| The cited public-support evidence is specific to the proposal's actual mechanism rather than only a vague adjacent value | 1 |
| The proposal explains how popular support can be used without compromising legality, rights, minority protections, institutional independence, or remedy adequacy | 1 |

Do not award polling or public-support points unless the evidence is cited, current enough for the claim being made, methodologically credible, and captured in [`../inventory/sources.csv`](../inventory/sources.csv). For volatile political questions, polling should normally be treated as current only if it was released within the last two years or if the audit explains why older evidence remains probative. For durable structural preferences, older evidence may be used only with a qualification.

State-level and federal-level support should be evaluated separately. National polling may show broad federal salience; state polling, referendum results, enacted-state practice, or bipartisan state adoption may show practical political viability. Neither should be substituted for the other without explanation.

Public support should increase only the Adoption Score. It should not override legal defects, source weaknesses, abuse risks, or an inadequate remedy. A popular proposal can still receive a low overall score if it is legally vulnerable, poorly drafted, unsupported by sources, or unlikely to survive implementation.

### International Support and Relations Score

Each developed proposal should receive a separate **International Support and Relations Score** from 0-10 where international effects are materially relevant. This score is a companion metric, not part of the 100-point Proposal Quality Score, because some strong domestic institutional repairs may have little direct international dimension.

Use this formula:

| International subcomponent | Points |
| --- | ---: |
| Comparative democratic practice, foreign constitutional practice, or international institutional precedent supports the reform principle | 1 |
| Foreign governments, multilateral institutions, treaty bodies, democracy organizations, human-rights institutions, or allied policy communities have expressed support for similar institutional safeguards | 1 |
| The proposal would likely improve rule-of-law, democratic-resilience, anti-corruption, human-rights, or institutional-stability perceptions of the United States | 1 |
| The proposal would likely strengthen allied trust, treaty reliability, diplomatic credibility, or U.S. soft power | 1 |
| The proposal is unlikely to create serious adverse foreign-policy, national-security, treaty, intelligence-sharing, or alliance-management consequences | 1 |
| Public international, comparative-law, or allied-government sources identify the reform as consistent with democratic or rule-of-law practice | 1 |
| International legal, comparative-law, diplomatic, or policy scholarship supports the reform or identifies manageable concerns | 1 |
| The proposal accounts for likely international criticism or misunderstanding without distorting the remedy | 1 |
| The proposal distinguishes domestic constitutional necessity from international preference and does not rely on foreign or international support as a substitute for U.S. legal authority | 1 |
| The international assessment is current, sourced, balanced, and includes adverse evidence or unresolved uncertainty | 1 |

Do not assign international-support points without current, cited, and properly characterized evidence. International commentary, foreign media, or foreign-government statements may show salience or perception, but they should not be treated as proof of domestic legal adequacy.

If a proposal has no material international-relations dimension, record the score as `N/A` with a short explanation. If the proposal may materially affect foreign relations but the audit has not checked current international sources, record `0` and identify the source-refresh task.

For non-developed issues, use the fixed baseline scores below. Retired, merged, and pending-controlling-finding issues are fixed at `0` and should not receive a formula-based score while that status remains in effect. Candidate issues may receive a different formula-based score only if a written audit justifies departing from the candidate baseline.

| Issue status | Baseline score |
| --- | ---: |
| Retired or merged | 0 |
| Pending judicial finding, merits adjudication, or other controlling external finding | 0 |
| Candidate inventory entry only | 10 |
| Candidate or draft issue with partial source notes or analysis | 25 |

### Score Consistency Rules

To keep scoring reproducible across audits:

1. Record the component scores, penalties, audit date, audit scope, and source record used to calculate the final score.
2. Record whether each component received full, half, or zero credit and identify the evidence supporting that choice.
3. Do not change a score unless at least one component score, penalty, public-support input, or baseline status changes.
4. Do not award points for intended future work, uncited knowledge, informal confidence, assumed public opinion, or repeated review of unchanged material.
5. Treat unknown, unavailable, stale, methodologically weak, uncited, or unreviewed inputs as unresolved rather than favorable.
6. Use the lower score where a component sits between two values.
7. If separate reviewers would assign different scores, require them to identify the disputed component, cited evidence, and specific rule causing disagreement; absent resolution, use the lower score.
8. Keep prior audit scores visible in the audit record where practical so score movement can be explained.
9. If the scoring formula is later amended, record the formula version or framework date used for the audit.
10. A higher score should reflect stronger reliability, not merely a longer or more elaborate proposal.

Use the following bands to interpret formula-based scores. These bands do not replace the scoring formula and should not be used to award points independently:

| Score range | Meaning |
| --- | --- |
| 0 | Retired, merged, blocked by pending controlling finding, or no standalone proposal quality score. |
| 1-24 | Inventory-only, minimally reviewed, or largely unaudited. |
| 25-49 | Partial draft or early development with significant unresolved source, legal, remedy, or structure issues. |
| 50-64 | Developed draft with meaningful framework structure but incomplete source, legal-fit, prior-proposal, adoption, or implementation review. |
| 65-74 | Substantially developed proposal with several audit components complete but material unresolved issues remaining. |
| 75-84 | Strong proposal with source verification, existing-law fit, prior-proposal review, and remedy analysis substantially complete. |
| 85-94 | Near-ready proposal with coalition appeal, abuse resistance, implementation, enforcement, and judicial-scrutiny review substantially complete. |
| 95-100 | Publication-ready or near-publication-ready proposal with external expert, practitioner, legislative, stakeholder, or comparable review incorporated. |

Scores should remain conservative. When in doubt, record the lower score and identify the next audit needed to justify advancement.

Audit rows created before adoption of the component formula should be treated as provisional status scores. They should be recalculated under the formula when the next T2, T3, or T4 audit is performed.

### Support and Adoption Audit

Each developed proposal should be reviewed for support appeal among the audiences most likely to affect adoption, implementation, public legitimacy, and long-term durability.

The audit should include:

1. **Audience segmentation.** Identify the proposal's likely audiences, including lawmakers, legislative staff, policy organizations, good-government groups, civil-liberties groups, institutional conservatives, election administrators, federalism advocates, legal academics, journalists, affected administrators, practitioners, and informed citizens where relevant.
2. **Audience-specific value proposition.** Confirm that each important audience can quickly see why the proposal matters to its own concerns, duties, incentives, or institutional commitments.
3. **Objection handling.** Identify the strongest good-faith objections from Democratic, Republican, independent, bipartisan, federalism, civil-libertarian, constitutional, administrative-burden, cost, implementation, and separation-of-powers perspectives, and determine whether the proposal answers them.
4. **Bad-faith misuse and caricature.** Identify how opponents could misstate, weaponize, or caricature the proposal, then revise framing or drafting to reduce avoidable misreading without weakening the remedy below adequacy.
5. **Institutional-conservative appeal.** Test whether the proposal can be defended in terms of restraint, rule of law, separation of powers, federalism, anti-corruption, predictability, reciprocity, and protection against future abuse by either party.
6. **Civil-liberties appeal.** Test whether the proposal protects due process, speech, association, equal treatment, privacy, fair notice, neutral enforcement, and limits on coercive state power.
7. **Administrative burden.** Determine whether the proposal is too complex, costly, paperwork-heavy, litigation-dependent, or agency-dependent, and whether a simpler implementation design would preserve adequacy.
8. **Lawyer and legislative-counsel seriousness.** Test whether a legally trained reader would see clear authority, precise terms, correct statutory hooks, clean definitions, appropriate severability, enforceable procedures, and no avoidable overclaiming.
9. **Staffer one-page test.** Confirm that a congressional staffer or policy aide can understand the problem, proposed repair, legal authority, cost or burden, likely opposition, and core talking point in under five minutes.
10. **Neutrality versus candor.** Confirm that the proposal avoids partisan framing while still naming objectively documented misconduct, institutional damage, and constitutional stakes where the record supports doing so.
11. **Adoption path.** Identify the most realistic vehicle, such as standalone legislation, amendment to a moving bill, appropriations rider, oversight hearing, committee report language, agency rule, state model law, court rule, professional standard, or constitutional amendment.
12. **Coalition sponsor map.** Identify plausible champions, co-sponsors, validators, and unusual coalitions, including civil-liberties groups, institutional conservatives, election officials, veterans' organizations, former officials, inspectors general, state administrators, legal scholars, policy centers, or professional associations where relevant.
13. **Current public-support evidence.** Identify whether credible current polling, survey evidence, referendum results, state practice, federal legislative support, or bipartisan adoption evidence supports the proposal's actual mechanism at the federal level, state level, or both.
14. **Public trust.** Confirm that an ordinary reader would see the proposal as fair, reciprocal, and applicable to future officeholders of either party.

The audit should produce a concise support plan identifying likely supporters, likely skeptics, likely opposition arguments, possible validators, preferred adoption vehicle, public-support evidence, and changes that could increase support without weakening the least-complex adequate remedy.

### Political-Language and Coalition-Appeal Audit

Each developed proposal should be reviewed for political-language neutrality and potential appeal across the likely adoption coalition.

The audit should check whether the proposal:

1. uses institution-focused language rather than partisan slogans, unnecessary personal attacks, or avoidably factional framing;
2. states concrete misconduct or institutional damage directly where supported by evidence, without diluting the project's truth-telling function;
3. explains why the safeguard should appeal to Democrats, Republicans, independents, institutionalists, civil libertarians, federalists, good-government advocates, and other plausible cross-pressured constituencies;
4. identifies likely objections from Democratic, Republican, independent, bipartisan, institutional, civil-libertarian, federalism, administrative, and implementation perspectives;
5. distinguishes objections to the proposal's policy merits from objections arising from partisan loyalty, short-term advantage, or bad-faith opposition;
6. considers whether neutral wording, narrower triggers, safer enforcement procedures, sunset review, reporting requirements, or clearer safe harbors could increase support without weakening the remedy below adequacy; and
7. identifies risks that the proposal could be captured, selectively enforced, or rhetorically reframed as a partisan weapon.

The audit should include provisional percentage estimates of likely support or appeal for at least the following audience classes:

| Audience class | Required estimate |
| --- | --- |
| Bipartisan / cross-party institutionalist support | Estimated percentage likely to find the proposal supportable in principle |
| Independent support | Estimated percentage likely to find the proposal reasonable or confidence-building |
| Democratic support | Estimated percentage likely to support the proposal as framed |
| Republican support | Estimated percentage likely to support the proposal as framed |

Percentage estimates are not polling claims. They are disciplined planning judgments that should be stated as provisional, briefly justified, and revised as better evidence, stakeholder feedback, polling, legislative behavior, expert review, or coalition analysis becomes available.

Each estimate should identify the principal reason for support, the principal reason for resistance, and any framing or design change that could increase adoption prospects without compromising the least-complex adequate remedy.

### Judicial and Scholarly Scrutiny Audit

Each developed proposal should be tested against likely judicial and scholarly scrutiny before it is treated as ready for external circulation, especially where the proposal alters institutional power, regulates executive discretion, affects elections, touches speech, creates enforcement mechanisms, changes judicial procedure, limits removal or appointment authority, or depends on contested constitutional doctrine.

The audit should identify:

1. the Supreme Court doctrines most likely to control or constrain the proposal;
2. the relevant lower-court doctrines, circuit splits, procedural doctrines, and standards of review;
3. any state constitutional doctrines or state-court constraints for model state legislation;
4. the most likely plaintiffs, defendants, claims, defenses, remedies, and justiciability barriers;
5. standing, ripeness, mootness, political-question, sovereign-immunity, official-immunity, and reviewability issues;
6. separation-of-powers, federalism, nondelegation, appointments, removal, due-process, equal-protection, First Amendment, criminal-procedure, spending-power, commandeering, and Article III concerns where relevant;
7. the strongest originalist, textualist, structural, precedential, functionalist, federalism, liberty-protective, and administrability objections;
8. the strongest arguments that the proposal is within congressional, state, judicial, agency, or constitutional authority;
9. how current Supreme Court justices or relevant lower-court judges might plausibly scrutinize the proposal's theory, text, tailoring, enforcement mechanism, and remedy;
10. how well-respected legal scholars, legislative counsel, former judges, former executive-branch lawyers, and institutional-design experts might criticize or strengthen the proposal;
11. whether narrowing, clearer definitions, severability, safe harbors, sunset review, factual findings, procedural protections, exhaustion rules, heightened mens rea, judicial review provisions, or alternative enforcement channels would increase the likelihood of being upheld; and
12. whether a constitutional amendment, court rule, state-law approach, appropriations condition, reporting requirement, or nonbinding institutional mechanism would be more durable than ordinary federal legislation.

The audit should produce deeply researched recommendations for increasing the likelihood that courts would uphold the proposal. Recommendations should distinguish:

1. changes that materially improve legal durability without weakening the remedy;
2. changes that improve legal durability but reduce remedial strength;
3. arguments that should appear in legislative findings or annotation;
4. authorities that should be cited before publication;
5. questions that require attorney, legislative-counsel, scholar, or practitioner review; and
6. fallback designs if the preferred remedy is likely to be invalidated.

Judicial-scrutiny analysis should not pretend to predict case outcomes with certainty. It should identify litigation risk, explain the best arguments on both sides, and make the proposal more careful, better supported, and more likely to survive review.

### Existing-Law and Prior-Proposal Consistency Audit

Each developed proposal should be checked against existing law, rules, regulations, procedures, and institutional practice before new legislative architecture is proposed.

The audit should apply the following preference order:

1. **Existing law, rule, regulation, procedure, or institutional practice.** Prefer amending or extending an existing legal or institutional vehicle where it can adequately solve the problem.
2. **Prior enacted or formally adopted models.** Prefer models that have already operated in federal, state, judicial, administrative, congressional, or comparative institutional practice.
3. **Prior proposed legislation or formal reform proposals.** Prefer proposals with meaningful demonstrated support over one-off or purely symbolic proposals.
4. **New project-drafted architecture.** Use a new structure only where existing law and prior models are inadequate, unavailable, or too compromised to adapt.

When prior legislation is used as a model, the audit should give greater weight to:

1. legislation with more than one sponsor;
2. legislation with co-sponsors, with increasing corresponding weight as the number of co-sponsors increases;
3. legislation with at least two co-sponsors as a minimum signal of support beyond symbolic introduction;
4. legislation with broad co-sponsorship across committees, states, regions, ideological factions, or institutional constituencies relevant to the proposal;
5. legislation with bipartisan co-sponsors, which should receive additional weight beyond the raw number of co-sponsors;
6. legislation that advanced beyond introduction, such as committee consideration, reported text, chamber passage, conference use, enactment in related form, or repeated reintroduction across Congresses; and
7. legislation supported by hearings, expert testimony, committee reports, agency analysis, inspector-general reports, CRS analysis, or comparable institutional review.

Co-sponsor count is a proxy for demonstrated political and institutional support, not a substitute for adequacy. A bill with many co-sponsors may still be rejected if it fails the least-complex adequate remedy standard, and a bill with few co-sponsors may remain useful if it supplies strong language, a well-tested mechanism, or an important institutional model.

The audit should identify whether the proposal:

1. amends existing law rather than creating a new standalone title where amendment is adequate;
2. explains why any existing vehicle is insufficient if the proposal departs from it;
3. distinguishes borrowed legislative language from ARRP-drafted language;
4. notes the sponsorship, co-sponsorship, bipartisan status, and legislative history of cited prior bills where available; and
5. avoids overstating the significance of a prior bill that had only a single sponsor, no co-sponsors, no bipartisan support, or no meaningful legislative activity.

This preference order does not require adopting weak prior proposals. Adequacy remains controlling: a better-supported model may still be rejected if it fails to repair the institutional weakness, lacks enforceability, creates abuse risk, or cannot satisfy the least-complex adequate remedy standard.

## Repository Architecture

- [`../README.md`](../README.md) contains the public-facing proposal front matter, including the reader notice, foundational premise, mission, scope, governing principles, rights notice, citation pointer, and technical-framework pointer.
- `framework/` contains governing methodology and cross-cutting remedial architecture.
- `areas/` contains one directory per project area and one file per developed issue.
- `legislation/` contains proposed statutory language keyed to issue identifiers.
- `inventory/` contains structured area, issue, and source records.
- `research/` contains material not yet integrated into a developed issue.
- `exports/` contains generated DOCX, PDF, and XLSX editions.
- `archive/` contains superseded snapshots retained for provenance.

Markdown and CSV files are authoritative. Binary Office and PDF files are generated outputs.

## Canonical Sources

- [`FRAMEWORK.md`](FRAMEWORK.md) — technical framework, methodology, repository conventions, and development status
- [`../inventory/areas.csv`](../inventory/areas.csv) — structured area inventory
- [`../inventory/issues.csv`](../inventory/issues.csv) — structured issue inventory
- [`../inventory/contents.csv`](../inventory/contents.csv) — combined area-and-issue contents index
- [`../inventory/audits.csv`](../inventory/audits.csv) — issue-level audit status and proposal-quality scoring
- [`../inventory/sources.csv`](../inventory/sources.csv) — source-tracking table
- [`../areas/`](../areas/) — modular area and issue analyses
- [`../legislation/`](../legislation/) — draft statutory and administrative language keyed to issue identifiers
- [`../AUTHORS.md`](../AUTHORS.md) — authorship statement
- [`../LICENSE.md`](../LICENSE.md) — rights and reuse notice
- [`../CITATION.cff`](../CITATION.cff) — citation metadata
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — contribution expectations
- [`../PUBLIC_RELEASE.md`](../PUBLIC_RELEASE.md) — public release process
- [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md) — compiled-document and print assembly framework

## Working Conventions

1. Every substantive issue has a stable identifier such as `DOJ-001`.
2. The framework governs analysis; the inventory tracks it; issue files contain the substantive work.
3. Each developed issue identifies the **Least-Complex Adequate Remedy**.
4. Supporting evidence, qualifications, and alternatives belong in annotation or source notes.
5. Where complete prevention is impracticable, a remedy may instead provide reliable detection, correction, deterrence, and institutional self-repair.
6. Candidate issues may be retired or merged when the issue-admission test shows substantial duplication.
7. A status such as **Awaiting merits adjudication** identifies a deliberately paused issue whose remedy depends materially on pending judicial resolution.
8. Markdown and CSV are canonical. DOCX, PDF, and XLSX files are generated exports.
9. Project updates must keep the structured inventory current. When an area, issue, legislation file, audit status, quality score, or cited source is added, removed, renamed, merged, retired, or materially revised, update the relevant rows in [`../inventory/areas.csv`](../inventory/areas.csv), [`../inventory/issues.csv`](../inventory/issues.csv), [`../inventory/contents.csv`](../inventory/contents.csv), [`../inventory/audits.csv`](../inventory/audits.csv), and [`../inventory/sources.csv`](../inventory/sources.csv) as part of the same change.
10. Source inventory updates are required whenever a new external source is cited or an existing cited source is repurposed for a materially different proposition. A source may remain marked `Reviewed?` as `No` until verification is complete, but the citation should still be captured promptly.

## Legislation Filename Convention

Legislative proposal files use the issue identifier as the base filename.

- Federal legislative proposals use the unsuffixed issue identifier: `XXX-NNN.md`.
- Model state legislative proposals use the state suffix: `XXX-NNN-state.md`.

For issues with both federal and state proposals, the federal proposal is the unsuffixed file and the model state proposal is the `-state` file. For issues with only a model state proposal, the proposal should still use the `-state` suffix.

Examples:

- `ELEC-003.md` — federal proposal.
- `ELEC-003-state.md` — model state proposal.
- `ELEC-002-state.md` — model state proposal where no federal proposal is yet maintained.

## Current Areas

The current area inventory is maintained in [`../areas/README.md`](../areas/README.md) and [`../inventory/areas.csv`](../inventory/areas.csv). The issue inventory is maintained in [`../inventory/issues.csv`](../inventory/issues.csv).

## Developed Issues

The developed-issue list is maintained in [`../inventory/contents.csv`](../inventory/contents.csv), with source-of-truth status tracking in [`../inventory/issues.csv`](../inventory/issues.csv). Avoid duplicating the developed-issue list in prose unless the list is generated from the inventory.

## Development Phase

The project will proceed by applying this framework to retained issues, developing authoritative source records, resolving overlap through primary ownership and cross-reference, and revising the least-complex adequate remedy as legal and factual analysis matures.

## Current Status

Current issue status is maintained in [`../inventory/issues.csv`](../inventory/issues.csv) and the ordered contents scaffold in [`../inventory/contents.csv`](../inventory/contents.csv). Area README files provide the nearest human-readable issue indexes, while developed issue pages contain the substantive analysis.

The governing framework already incorporates the project-wide rules for institutional focus, politically neutral application, issue admission, mandatory issue architecture, issue-level conciseness, standardized annotations, the Least-Complex Adequate Remedy, limited use of automatic institutional-failure triggers, and cross-referencing instead of duplicative treatment.

The area and issue inventories already include A-04 Judicial Independence and Enforcement (JUD-001 through JUD-009, with JUD-002, JUD-003, JUD-004, and JUD-006 retired into JUD-001), A-05 Presidential Clemency and Pardon Power (PAR-001 through PAR-010), A-07 Classification, Declassification, and National-Security Information (CLASS-001 through CLASS-012), and A-21 Federal Reserve Independence and Monetary Policy (FRB-001 through FRB-008). The `FED` prefix remains reserved for A-20 Federalism and Presidential Coercion of States.

## Outstanding Development

The following work remains outstanding and should not be treated as an uncommitted framework revision:

- develop authoritative source records, annotations, and individual issue files for the JUD, PAR, and CLASS candidate inventories;
- analyze constitutional and implementation constraints for judicial-enforcement remedies, including appointments, appropriations, due process, and presidential control;
- analyze the constitutional limits on restricting the legal effect of presidential clemency while developing transparency, anti-corruption, review, recordkeeping, disclosure, and surrounding-liability remedies;
- preserve and source the distinctions among classification status, authorization to disclose, lawful custody or possession, and government ownership and records-preservation duties;
- develop the A-21 annotation explaining the systemic risks of sustained political subordination of monetary policy, including inflation, unanchored expectations, leverage, asset-price distortions, currency weakness, loss of credibility, and the possibility of a later severe corrective contraction;
- conduct a systematic review of each proposal's potential bipartisan support, including cross-party institutional interests, likely objections, possible neutral framing, and risks of partisan capture or misuse;
- select and adopt an appropriate Creative Commons or other public reuse license when the project is ready for broader legislative and public engagement.

These are substantive research and issue-development tasks. They do not reopen the already committed governing framework or area inventories.
