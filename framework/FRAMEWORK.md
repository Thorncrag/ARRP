---
title: "American Restoration and Resilience Project — Framework and Methodology"
status: active
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# American Restoration and Resilience Project — Framework and Methodology

This file is ARRP's cross-cutting governing kernel and routing index. It states the principles, authority boundaries, and conventions that apply throughout the project. Detailed methodology is authoritative in the independently loadable modules linked below. Together, this kernel and those modules constitute the complete Framework; this file is not a compressed substitute for a module whose subject is implicated.

The public premise, mission, scope, and governing principles are maintained in
[`../README.md`](../README.md). Placement and stable document identity are
governed by the [`Component Registry`](component-registry.json). Exact ARRP
GitHub mechanics are in
[`project/github/workflow.md`](project/github/workflow.md). Reusable print
rules and ARRP edition configuration are separated between
[`standards/publication/`](standards/publication/) and
[`project/publication/`](project/publication/). Agent execution is governed by
[`AGENT_OPERATING_RULES.md`](AGENT_OPERATING_RULES.md), with public-input review
governed separately by
[`project/workflows/public-input-review.md`](project/workflows/public-input-review.md).

**Homepage synchronization notice.** The homepage's [Guiding Principle and introductory framing](../README.md#guiding-principle) mirror portions of the governing substance stated here in public-facing form. Any substantive revision in either location must include a synchronization review of the other and any necessary corresponding update in the same change. This Framework remains authoritative for project methodology; the homepage remains authoritative for the public statement of the project's premise, mission, and scope.

## How to Use This Document

Always load this kernel. Then load the smallest **complete** set of modules implicated by the work:

1. identify the primary operation and every material capability or project surface involved;
2. load the union of the corresponding modules in the [Governing Module Routes](#governing-module-routes), together with each module's stated dependencies;
3. load the applicable canonical records, such as the issue page, proposal vehicle, source records, audit history, runbook, GitHub fields, or publication surface; and
4. expand context before taking a dependent action whenever the task reveals a new subject, ambiguity, conflict, unfamiliar case, changed governing rule, stale input, or validation failure.

Routing is additive. Selecting one operation never excludes another module that the work also implicates. A bounded packet or summary is a nonauthoritative projection and may not narrow a human-reserved rule or replace the canonical file.

Automated agents should use reviewed, hash-verified routes and fail closed when required context is missing, stale, contradictory, oversized, or unregistered. Interactive work with the user remains comprehensive by default: the routes establish a minimum complete context, not a ceiling on investigation or review.

The validated embedded routing namespace in the
[`Component Registry`](component-registry.json) is the sole current routing
authority. Its Project Console representation is nonauthoritative and
human-readable.

## Governing Authority

| Subject | Canonical authority |
| --- | --- |
| Cross-cutting project principles, authority, and routing | This kernel |
| Detailed scope, methodology, issue, evidence, lifecycle, source, candidate, audit, and scoring rules | The modules registered below and in the [`Component Registry`](component-registry.json) |
| Repository directories, stable document identities, and file purposes | [`Component Registry`](component-registry.json) |
| GitHub Issues, Project fields, lifecycle synchronization, workflow Status, and holds | [`project/github/workflow.md`](project/github/workflow.md) |
| Remedy selection, categories, repair and prevention, and trigger stages | [`standards/content/remedies.md`](standards/content/remedies.md) |
| Print selection, order, page locators, and compiled editions | [`standards/publication/print-assembly.md`](standards/publication/print-assembly.md), [`project/publication/print-assembly.md`](project/publication/print-assembly.md), and [`project/publication/print-assembly.json`](project/publication/print-assembly.json) |
| Agent and bot execution | [`AGENT_OPERATING_RULES.md`](AGENT_OPERATING_RULES.md), its routed modules, and the applicable registered runbook |
| Public-input privacy and action boundary | [`standards/interfaces/public-input.md`](standards/interfaces/public-input.md) and [`project/workflows/public-input-review.md`](project/workflows/public-input-review.md) |
| Public release | [`standards/publication/releases.md`](standards/publication/releases.md) and [`project/publication/first-release.md`](project/publication/first-release.md) |

A specialized authority governs its assigned subject. It may implement or elaborate this kernel but may not silently alter a cross-cutting rule, enlarge an agent's authority, or redefine another authority's subject. A generated view, dashboard, context packet, automation manifest, runbook summary, or compatibility pointer is not an independent source of substantive authority.

## Substantive Framework

The Guiding Principle supplies the common purpose and constraint for every domain module. The routed methodology then determines what the project studies, how it characterizes conduct, how issues and remedies are structured, what evidence is sufficient, and how quality is reviewed.

## Guiding Principle

**The architecture matters because people live underneath it.**

> **No person should suffer grave, arbitrary harm merely because institutional design permits one officeholder to convert lawful public authority into an instrument of personal will.**

Everything in ARRP derives from this principle. The project exists to identify and repair institutional defects because those defects expose human beings to arbitrary harm. **Unchecked public power eventually manifests as arbitrary injury to actual human beings.** Constitutional structure, institutional independence, lawful administration, review, correction, and democratic resilience are not ends pursued for institutional elegance alone; they matter because people live under the public power those arrangements organize.

ARRP's corresponding constitutional claim is: **The first obligation of constitutional government is to ensure that no person suffers grave, arbitrary harm because institutional design permits lawful public authority to be exercised as personal power.** That obligation supplies the human purpose of constitutional architecture: **Government exists to exercise public authority in a manner that protects persons from arbitrary harm, and constitutional structure exists to ensure that public authority cannot be converted into personal power.**

ARRP therefore treats grave arbitrary human harm caused or enabled by public authority as the human manifestation—and diagnostic symptom—of institutional failure. Analysis must identify the independently repairable legal, structural, administrative, procedural, or remedial defect that permitted the harm, made it likely, or left it without effective correction. The project may not call an outcome arbitrary merely because it is harmful, unjust, politically disfavored, or inconsistent with the author's preferred policy. In this framework, arbitrariness means that serious human harm is caused, enabled, or made practically uncorrectable by public power that is personalized, selectively applied without an adequate lawful basis, inadequately reasoned toward a legitimate public purpose, insufficiently constrained, or effectively insulated from review and correction. Grave harm includes acute or irreversible injury as well as cumulative or systematically distributed injury serious enough to warrant institutional repair.

The [Political-Failure Boundary](#political-failure-boundary) remains part of this principle's discipline. Harm alone does not bring a topic within ARRP when the ordinary constitutional process remains available and no independently repairable defect prevents it from functioning. But once the record establishes arbitrary harm in the institutional sense defined here, the project should treat that harm as a symptom of institutional failure and locate the defect in authorization, constraint, administration, review, correction, or remedy rather than dismissing it as ordinary political disagreement.

The principle also constrains ARRP's proposed repairs: **if the objective is to prevent arbitrary human harm, then reforms must not themselves become arbitrary instruments of power.** Neutral application, constitutional fidelity, institutional durability, abuse resistance, corrigibility, preservation of legitimate governmental discretion, and selection of the least-complex adequate remedy all follow from that recursive constraint. The existing issue architecture should collectively make the complete chain visible:

1. the human harm or material risk;
2. the institutional defect that permits, causes, or fails to correct it;
3. the way public authority operates through that defect;
4. the proposed repair and how it reduces the harm; and
5. the safeguards that keep the repair from becoming a new source of arbitrary power.

Every substantive issue-development pass and audit must answer the causal question: **Does this reform materially reduce the probability that lawful governmental authority can be converted into arbitrary injury against individuals?**

The corresponding reversed-control question is reserved exclusively to the human author: **Would we want this institutional design if our least-favored political opponent controlled it?** An LLM agent may prepare a neutral analysis of how both the existing arrangement and the proposed repair would operate under materially different political control, including foreseeable misuse, asymmetry, and available safeguards, but it may not answer the question or represent it as satisfied. A deterministic bot may verify only whether a human decision has been recorded. An agent may apply a recorded human decision but may not originate, revise, or infer one. When the decision is material and unresolved, preserve the analysis and route the question through `Status: Human decision needed`.

The causal question and human reversed-control decision are applications of the existing remedy-fit, abuse-resistance, and cogency rules, not a new scoring component, foundation, audit tier, or mandatory reader-facing heading. They do not independently authorize a score, lifecycle, foundation, or candidate-disposition change.

Where the evidence establishes a dangerous institutional arrangement but does not establish—or does not require resolution of—subjective intent, the following is an approved neutral analytical formulation:

> **Regardless of intent, this institutional arrangement predictably allows arbitrary human harm, and here is a neutral reform that would reduce that risk under any future administration.**

The scope rule follows from the same principle: **If an institutional design predictably permits arbitrary harm through concentrated public power, then that design should be examined and, if possible, repaired—whether today's beneficiaries are Democrats, Republicans, or anyone else.** The Political-Failure Boundary still requires an independently repairable institutional defect and does not convert ordinary adverse policy outcomes into ARRP issues.

## Cross-Cutting Rules and Conventions

- **One authority and one primary home.** Each governing rule family and each institutional defect has one authoritative home. Other records link to it rather than create competing definitions. Repository placement is controlled by the [`Component Registry`](component-registry.json).
- **Neutral standards, candid conclusions.** Apply the same evidentiary, legal, and remedial standards regardless of party, ideology, officeholder, administration, or movement. Distinguish fact, law, dispute or uncertainty, and ARRP's own institutional analysis. Party-neutral method does not require positionlessness or false symmetry.
- **Evidence before favorable credit.** Do not invent or infer unsupported facts, authorities, review, public support, professional validation, or outcomes. Unverified favorable propositions receive no favorable score credit.
- **Repair without reproducing arbitrariness.** Every remedy must address the independently repairable defect, preserve legitimate governmental discretion, and be tested for abuse, selective enforcement, personalization, inadequate constraint, and failure of review or correction.
- **Development level is not workflow Status.** The six-level maturity lifecycle is separate from the repeatable GitHub workflow action or hold. Research, revision, audit, external review, monitoring, and maintenance do not become maturity stages.
- **Human-reserved judgment remains human.** Only the human author may make a permanent candidate or issue disposition, answer or revise the reversed-control question, make a reserved foundational or materially consequential choice, alter project scope or methodology, change an audit rubric or scoring system, or authorize final circulation or publication. These reservations do not excuse an agent from reviewing the matter, explaining the options and uncertainty, and making a reasoned recommendation for human decision.
- **Discovery duty and change authority remain distinct.** A named queue, detector, context packet, work order, or assigned duty establishes required coverage but does not prevent an authorized LLM agent from investigating a credible connected project anomaly, omission, contradiction, risk, or structural defect. The agent may implement only actions allowed by the applicable authority; it must document and route human-reserved, unsafe, out-of-scope, forbidden, or inconclusive findings without silently discarding them or treating a later clean aggregate result as proof of resolution.
- **Rubrics are immutable without approval.** No rubric, formula, component, weight, penalty, threshold, or score band may change without recorded human approval and the required project-level Change Audit. A rubric may never be altered to engineer a desired score or portfolio result. The `Runs` field increases only for a completed, separately recorded T0–T4 issue-quality audit.
- **Permanent records remain traceable.** A retired, rejected, merged, integrated, removed, or otherwise finally adjudicated substantive record is preserved with its identifier, provenance, rationale, and disposition history rather than deleted.

## Governing Module Routes

The following routes are cumulative. Each linked module states its own load triggers and dependencies.

### Methodology, Issues, Evidence, and Remedies

| Work or subject | Authoritative module |
| --- | --- |
| Institutional scope, political-failure boundary, analytical method, or admission | [`standards/content/scope-and-admission.md`](standards/content/scope-and-admission.md) |
| Neutral characterization, claim status, motive, and reader-facing terminology | [`Neutrality and Language`](standards/content/neutrality-and-language.md) |
| Partisan perception, public actors, President Trump, Project 2025, coalitions, or advocacy tone | [`ARRP Public-Actor Conventions`](project/profile/public-actor-conventions.md) |
| Issue-page structure, proposal presentation, snapshot, survey, budget, or concision | [`Content Record Architecture`](standards/content/record-architecture.md) |
| Annotation, assertion discipline, and source quality | [`Claims and Citations`](standards/sources/claims-and-citations.md) |
| Evidence pages, source-development records, qualitative placement, or issue-source reconciliation | [`Source and Evidence Records`](standards/sources/source-records.md) plus [`ARRP Source Catalog and Adjudication`](project/workflows/source-adjudication.md) for exact paths and fields |
| Remedy selection, repair and prevention, constitutional amendments, taxonomy, shared remedies, or triggers | [`standards/content/remedies.md`](standards/content/remedies.md) |
| JUD-011 application or executive nullification of enacted federal commands | [`standards/content/remedies.md`](standards/content/remedies.md), the canonical JUD-011 records, and the nonauthoritative [`JUD-011 coverage matrix`](../research/interbranch-review/JUD-011-coverage-matrix.md) |

### Content Development, Sources, Candidates, and Navigation

| Work or subject | Authoritative module |
| --- | --- |
| Substantive maturity, pre-lifecycle intake, or repeatable workflows | [`standards/content/maturity-and-gates.md`](standards/content/maturity-and-gates.md) |
| ARRP maturity values, thresholds, and classifiers | [`project/profile/maturity-profile.md`](project/profile/maturity-profile.md) |
| GitHub Status, holds, labels, fields, transitions, or synchronization | [`project/github/workflow.md`](project/github/workflow.md) |
| Substantive issue-work preflight and closeout | [`Content Maturity and Development Gates`](standards/content/maturity-and-gates.md) |
| Cross-surface project updates | [`ARRP Project Update`](project/workflows/project-update.md) |
| Source catalogs, stable source identity, review metadata, or source-level monitoring | [`Source and Evidence Records`](standards/sources/source-records.md) plus [`ARRP Source Catalog and Adjudication`](project/workflows/source-adjudication.md) for exact catalogs and fields |
| Issue monitoring or a project-wide monitoring pass | [`Content and Project Monitoring`](standards/sources/monitoring.md) plus the [`GitHub workflow`](project/github/workflow.md) and [`ARRP source workflow`](project/workflows/source-adjudication.md) for exact representations |
| Automated source routing or batch reconciliation | [`Automated Source Adjudication`](standards/sources/source-adjudication.md) plus [`ARRP Source Catalog and Adjudication`](project/workflows/source-adjudication.md) |
| Preliminary-candidate synthesis or promotion | [`Candidate Review`](standards/content/candidate-review.md) plus the [`ARRP Candidate Discovery and Adjudication`](project/workflows/candidate-review.md) workflow |
| Presidential-directive completeness or substantive directive review | [`Presidential-Directive Completeness and Review`](project/workflows/presidential-directive-review.md) |
| Horizon discovery, formal-candidate investigation, or disposition implementation | [`Candidate Review`](standards/content/candidate-review.md) plus [`ARRP Candidate Discovery and Adjudication`](project/workflows/candidate-review.md) |
| Inventory, stable identity, cross-references, or generic navigation | [`Content Navigation, Indexes, and Synchronization`](standards/content/navigation-and-indexes.md) |
| Topic-guide creation or revision | [`Topic Guide Standard`](standards/content/topic-guides.md) plus [`ARRP Navigation and Index Synchronization`](project/workflows/navigation-sync.md) for exact ARRP configuration |
| ARRP navigation synchronization or its T1 gate | [`ARRP Navigation and Index Synchronization`](project/workflows/navigation-sync.md) |

### Audits and Scoring

| Work or subject | Authoritative module |
| --- | --- |
| Common audit orientation, workflow, run counting, unknowns, preservation, output, or method learning | [`Audit Core`](standards/audits/core.md) |
| T0–T4 depth or formatting preflight | [`standards/audits/levels.md`](standards/audits/levels.md) |
| Change Audit or Internal Remedy-Fit Audit | [`Change Audits`](standards/audits/change-audits.md) |
| Project consistency audit | [`Project Consistency Audits`](standards/audits/project-consistency.md) |
| Hallucination resistance, source verification, or traceability | [`Verification Protocol`](standards/audits/verification.md) |
| Existing law, judicial or scholarly scrutiny, prior proposals, or functional analogues | [`Legal and Prior-Work Review`](standards/audits/legal-and-prior-work.md) |
| Reusable scoring discipline | [`standards/audits/scoring.md`](standards/audits/scoring.md) |
| ARRP Proposal Quality Score, weights, penalties, fixed zeroes, or score consistency | [`project/profile/scoring-rubric.md`](project/profile/scoring-rubric.md) |
| Adoption method, enactment pathway, friction, support, or coalition appeal | [`Adoption and Enactment Pathway Analysis`](standards/audits/adoption-and-pathways.md) plus the [`ARRP scoring profile`](project/profile/scoring-rubric.md) for exact values and formulas |
| Qualified external review or international support and relations | [`External and International Review`](standards/audits/external-review.md) plus the [`ARRP scoring profile`](project/profile/scoring-rubric.md) for exact statuses and formulas |

### Project and Agent Operations

| Work or subject | Authoritative record |
| --- | --- |
| Agent or bot behavior | [`AGENT_OPERATING_RULES.md`](AGENT_OPERATING_RULES.md), reusable [`standards/automation/`](standards/automation/) rules, and applicable [`project/automation/`](project/automation/) policy or runbook |
| Context selection, routing maintenance, or comprehensive-review coverage | [`Component Registry`](component-registry.json) |
| Repository placement | [`Component Registry`](component-registry.json) |
| Owner-local runtime paths, state classes, Application Support authority, `ARRP Private` staging, migration, cutover, rollback, or retirement | [`ARRP Owner-Local Runtime Authority`](project/automation/owner-local-runtime.md) |
| GitHub-bound disclosure, public/private artifact families, secret exclusion, or owner-local disclosure controls | [`GitHub Disclosure Boundary`](project/github/disclosure-boundary.md) and [`disclosure-policy.json`](project/github/disclosure-policy.json) |
| Operational Incident identity, admission, recurrence, recovery, or closure | [`operational-incidents.json`](project/automation/operational-incidents.json) |
| Runtime transaction attempt identity, retry authority, recovery proof, and recoverable-retirement posture | [`transaction-lifecycle.md`](project/automation/transaction-lifecycle.md) |
| Security Incident identity, protected investigation, containment, verification, or closure | [`security-incidents.json`](project/automation/security-incidents.json) |
| Reciprocal `INC`/`SEC` relationship identity or navigation | [`incident-relations.json`](project/automation/incident-relations.json) |
| Material governance-decision identity, public provenance, adoption, supersession, validation, activation posture, or protected-supplement requirement | [`ARRP Governance Change Recording`](project/workflows/governance-change-recording.md) and [`governance-change-registry.json`](project/workflows/governance-change-registry.json) |
| Project-operated interface layout and behavior | [`standards/interfaces/standard.md`](standards/interfaces/standard.md) and [`project/interfaces/project-console.md`](project/interfaces/project-console.md) |
| Console progress calculation and display | [`standards/interfaces/progress-views.md`](standards/interfaces/progress-views.md) and [`project/interfaces/project-console-progress.md`](project/interfaces/project-console-progress.md) |
| Publication and compiled editions | [`standards/publication/`](standards/publication/), [`project/publication/`](project/publication/), and [`project/publication/print-assembly.json`](project/publication/print-assembly.json) |

## Comprehensive Review Boundary

The machine-readable context registry identifies every stable governing document with `governing: true`. A periodic comprehensive review must load all such documents, the current mutable checkpoint, the applicable persistent-agent runbook, and the reviewed project inputs. It establishes a dated boundary so later reviews can focus on intervening change without losing the periodic whole-project look-back.

Adding, moving, renaming, or materially changing a governing module requires the same change to update its registry entry, dependencies, affected profiles and capabilities, compatibility pointer when applicable, repository-structure description, and validation. A module that is absent from the registry is not eligible to be silently omitted; automated work must fail closed and interactive work must expand to the canonical file.

## Compatibility Routing Anchors

The following stable headings preserve existing repository links. They are pointers, not duplicate statements of the detailed rules.

## Neutrality and Language Guidelines

See [`Neutrality and Language`](standards/content/neutrality-and-language.md) and
[`ARRP Public-Actor Conventions`](project/profile/public-actor-conventions.md).

### Institutional Focus

See [`Scope and Admission`](standards/content/scope-and-admission.md#institutional-focus).

### Resilience and Temporal Scope

See [`Scope and Admission`](standards/content/scope-and-admission.md#resilience-and-temporal-scope).

### Political-Failure Boundary

See [`Scope and Admission`](standards/content/scope-and-admission.md#political-failure-boundary).

### Neutral Application

See [`Neutrality and Language`](standards/content/neutrality-and-language.md#neutral-application).

### Substantive Positions and Partisan Perception

See [`ARRP Public-Actor Conventions`](project/profile/public-actor-conventions.md#substantive-positions-and-partisan-perception).

### Public-Actor References

See [`ARRP Public-Actor Conventions`](project/profile/public-actor-conventions.md#public-actor-references).

### Accuracy Over Softening

See [`Neutrality and Language`](standards/content/neutrality-and-language.md#accuracy-over-softening).

### Neutral Characterization

See [`Neutrality and Language`](standards/content/neutrality-and-language.md#neutral-characterization).

### Motive and Intent

See [`Neutrality and Language`](standards/content/neutrality-and-language.md#motive-and-intent).

### Conduct Before Character

See [`Neutrality and Language`](standards/content/neutrality-and-language.md#conduct-before-character).

### Reader-Facing and Technical Terminology

See [`Neutrality and Language`](standards/content/neutrality-and-language.md#reader-facing-and-technical-terminology).

### Project 2025 Treatment

See [`ARRP Public-Actor Conventions`](project/profile/public-actor-conventions.md#project-2025-treatment).

### Collective Labels

See [`ARRP Public-Actor Conventions`](project/profile/public-actor-conventions.md#collective-labels).

### Coalition Reality

See [`ARRP Public-Actor Conventions`](project/profile/public-actor-conventions.md#coalition-reality).

### Advocacy Tone

See [`ARRP Public-Actor Conventions`](project/profile/public-actor-conventions.md#advocacy-tone).

## Analytical Method

See [`Scope and Admission`](standards/content/scope-and-admission.md#analytical-method).

### Issue-Admission Test

See [`standards/content/scope-and-admission.md`](standards/content/scope-and-admission.md#issue-admission-test).

## Mandatory Issue Architecture

See [`Content Record Architecture`](standards/content/record-architecture.md#mandatory-issue-architecture).

### Issue Snapshot Format

See [`Content Record Architecture`](standards/content/record-architecture.md#issue-snapshot-format).

### Proposal Survey

See [`Content Record Architecture`](standards/content/record-architecture.md#proposal-survey).

## Issue-Level Conciseness

See [`Content Record Architecture`](standards/content/record-architecture.md#issue-level-conciseness).

## Annotation and Evidence

See [`Claims and Citations`](standards/sources/claims-and-citations.md#annotation-and-evidence).

### Standard Annotation

See [`Claims and Citations`](standards/sources/claims-and-citations.md#standard-annotation).

### Assertion Discipline

See [`Claims and Citations`](standards/sources/claims-and-citations.md#assertion-discipline).

### Source Standard

See [`Claims and Citations`](standards/sources/claims-and-citations.md#source-standard).

## Least-Complex Adequate Remedy

See the [remedy standard](standards/content/remedies.md#least-complex-adequate-remedy).

## Repair and Prevention

See the [remedy standard](standards/content/remedies.md#repair-and-prevention).

## Constitutional Amendments

See the [remedy standard](standards/content/remedies.md#constitutional-amendments).

## Automatic Constitutional Stabilizers and Institutional-Failure Triggers

See the [remedy standard](standards/content/remedies.md#trigger-stages).

## Project Lifecycle, Sources, Navigation, and Audits

Use the applicable routes above; this heading remains only as the former section's stable entry point.

## Inventory Files

See [`Content Navigation, Indexes, and Synchronization`](standards/content/navigation-and-indexes.md#inventory-files).

## Inventory Rules

See [`Content Navigation, Indexes, and Synchronization`](standards/content/navigation-and-indexes.md#inventory-rules).

## Issue Lifecycle: Discovery Through Publication and Maintenance

See the [ARRP maturity profile](project/profile/maturity-profile.md#issue-lifecycle-discovery-through-publication-and-maintenance).

### Development-Level Lifecycle

See the [ARRP maturity profile](project/profile/maturity-profile.md#development-level-lifecycle).

### Intake Before the Development-Level Lifecycle

See the [ARRP maturity profile](project/profile/maturity-profile.md#intake-before-the-development-level-lifecycle).

### Repeatable Workflows Around the Lifecycle

See the [ARRP maturity profile](project/profile/maturity-profile.md#repeatable-workflows-around-the-lifecycle).

### Workflow Status and Hold Definitions

See the [ARRP GitHub workflow](project/github/workflow.md#issue-development-lifecycle).

### Human-Governed Foundation and Delegated Development

See the [ARRP maturity profile](project/profile/maturity-profile.md#human-governed-foundation-and-delegated-development).

### Post-Admission Development Gates

See the [ARRP maturity profile](project/profile/maturity-profile.md#post-admission-development-gates).

### Persistent Agents and Runbooks

See [`AGENT_OPERATING_RULES.md`](AGENT_OPERATING_RULES.md#persistent-agent-runbooks).

## Issue-Development Lifecycle Check

See the [content-maturity standard](standards/content/maturity-and-gates.md#required-lifecycle-check)
and the [ARRP maturity profile](project/profile/maturity-profile.md#required-lifecycle-check).

## Project-Update Checklist

See [`ARRP Project Update`](project/workflows/project-update.md#project-update-checklist).

## Area and Issue Index Rules

See [`Content Navigation, Indexes, and Synchronization`](standards/content/navigation-and-indexes.md#area-and-issue-index-rules).

### Area-Page Issue Lists

See [`Content Navigation, Indexes, and Synchronization`](standards/content/navigation-and-indexes.md#area-page-issue-lists).

### Topic Page Standard

See [`Topic Guide Standard`](standards/content/topic-guides.md#topic-page-standard).

### Navigation Synchronization Check

See [`standards/content/navigation-and-indexes.md`](standards/content/navigation-and-indexes.md#navigation-synchronization).

### Project-Operated Interface Visual Standard

See the [interface standard](standards/interfaces/standard.md) and
[ARRP tool visual identity](project/interfaces/visual-identity.md).

## Source Inventory Rules

See [Source and Evidence Records](standards/sources/source-records.md#source-inventory-and-stable-identity)
and [ARRP Source Catalog and Adjudication](project/workflows/source-adjudication.md#canonical-source-catalogs).

## Automated Source Adjudication and Issue Evidence Records

See [Automated Source Adjudication](standards/sources/source-adjudication.md),
[Source and Evidence Records](standards/sources/source-records.md), and
[ARRP Source Catalog and Adjudication](project/workflows/source-adjudication.md).

### Evidence and Monitoring Architecture

See [Source and Evidence Records](standards/sources/source-records.md#evidence-architecture),
[Content and Project Monitoring](standards/sources/monitoring.md), and
[ARRP Source Catalog and Adjudication](project/workflows/source-adjudication.md).

### Source Reconciliation During Issue Work

See [Source and Evidence Records](standards/sources/source-records.md#source-reconciliation-during-issue-work)
and [ARRP Source Catalog and Adjudication](project/workflows/source-adjudication.md).

### Project-Wide Monitoring Pass

See [Content and Project Monitoring](standards/sources/monitoring.md#project-wide-monitoring-pass),
the [GitHub workflow](project/github/workflow.md#issue-specific-monitoring),
and [ARRP Source Catalog and Adjudication](project/workflows/source-adjudication.md#canonical-source-catalogs).

### Route-Centered Automated Adjudication

See [Automated Source Adjudication](standards/sources/source-adjudication.md#route-centered-automated-adjudication)
and [ARRP Source Catalog and Adjudication](project/workflows/source-adjudication.md#arrp-route-centered-adjudication).

### Presidential-Directive Completeness Scans

See [Presidential-Directive Completeness and Review](project/workflows/presidential-directive-review.md#presidential-directive-completeness-scans).

### Automation and Human-Decision Boundary

See [Automated Source Adjudication](standards/sources/source-adjudication.md#automation-and-human-decision-boundary)
and [ARRP Source Catalog and Adjudication](project/workflows/source-adjudication.md#arrp-closeout-mappings).

### Batch Reconciliation and Closeout

See [Automated Source Adjudication](standards/sources/source-adjudication.md#batch-reconciliation-and-closeout)
and [ARRP Source Catalog and Adjudication](project/workflows/source-adjudication.md#arrp-closeout-mappings).

## Audit Rules and Proposal Quality Scoring

See the audit and scoring routes above.

### Pre-Audit Orientation

See [`Audit Core`](standards/audits/core.md#pre-audit-orientation).

### Change Audit

See [`Change Audits`](standards/audits/change-audits.md#change-audit).

### Audit Workflow

See [`Audit Core`](standards/audits/core.md#audit-workflow).

### Formatting Preflight

See [`Audit Levels`](standards/audits/levels.md#formatting-preflight).

### Audit Run Counting Rule

See [`Audit Core`](standards/audits/core.md#audit-run-counting-rule).

### Project Consistency Audit

See [`Project Consistency Audits`](standards/audits/project-consistency.md#project-consistency-audit).

### Audit Learning and Method Improvement

See [`Audit Core`](standards/audits/core.md#audit-learning-and-method-improvement).

### Audit Depth Tiers

See [`standards/audits/levels.md`](standards/audits/levels.md#audit-depth-tiers).

### Horizon Scan Audit

See [`project/workflows/candidate-review.md`](project/workflows/candidate-review.md#horizon-discovery).

### Horizon Candidate Adjudication Workflow

See [`ARRP Candidate Discovery and Adjudication`](project/workflows/candidate-review.md#horizon-candidate-adjudication-workflow).

### Audit Autonomy and Unknowns

See [`Audit Core`](standards/audits/core.md#audit-autonomy-and-unknowns).

### Audit Preservation and GitHub Storage

See [`Audit Core`](standards/audits/core.md#audit-preservation-and-closeout).

### Audit Output

See [`Audit Core`](standards/audits/core.md#audit-output).

### Hallucination-Resistance and Verification Protocol

See [`Verification Protocol`](standards/audits/verification.md#hallucination-resistance-and-verification-protocol).

### Proposal Quality Score

See the reusable [scoring standard](standards/audits/scoring.md) and the
[ARRP scoring profile](project/profile/scoring-rubric.md#proposal-quality-score).

### External Review Status and Qualified Reviewers

See the reusable
[External and International Review](standards/audits/external-review.md#external-review-status-and-qualified-reviewers)
and the
[ARRP configuration](project/profile/scoring-rubric.md#external-and-international-review-configuration).

### Adoption Score Formula

See the reusable
[adoption method](standards/audits/adoption-and-pathways.md#adoption-score-formula)
and the
[ARRP configuration](project/profile/scoring-rubric.md#adoption-and-enactment-pathway-configuration).

### Enactment Pathway Check

See the reusable
[Enactment Pathway Check](standards/audits/adoption-and-pathways.md#enactment-pathway-check)
and the
[ARRP configuration](project/profile/scoring-rubric.md#adoption-and-enactment-pathway-configuration).

#### Institutional Self-Limitation Rule

See the reusable
[Institutional Self-Limitation Rule](standards/audits/adoption-and-pathways.md#institutional-self-limitation-rule)
and the
[ARRP configuration](project/profile/scoring-rubric.md#adoption-and-enactment-pathway-configuration).

### Adoption Friction Score

See the reusable
[Adoption Friction method](standards/audits/adoption-and-pathways.md#adoption-friction-score)
and the
[ARRP configuration](project/profile/scoring-rubric.md#adoption-friction-configuration).

### International Support and Relations Score

See the reusable
[International Support and Relations method](standards/audits/external-review.md#international-support-and-relations-score)
and the
[ARRP configuration](project/profile/scoring-rubric.md#external-and-international-review-configuration).

### Score Consistency Rules

See the [ARRP scoring profile](project/profile/scoring-rubric.md#score-consistency-rules).

### Support and Adoption Audit

See the
[Support and Adoption Audit](standards/audits/adoption-and-pathways.md#support-and-adoption-audit)
and the
[ARRP public-actor conventions](project/profile/public-actor-conventions.md).

### Political-Language and Coalition-Appeal Audit

See the
[Political-Language and Coalition-Appeal Audit](standards/audits/adoption-and-pathways.md#political-language-and-coalition-appeal-audit)
and the
[ARRP public-actor conventions](project/profile/public-actor-conventions.md).

### Judicial and Scholarly Scrutiny Audit

See [`Legal and Prior-Work Review`](standards/audits/legal-and-prior-work.md#judicial-and-scholarly-scrutiny-audit).

### Existing-Law and Prior-Proposal Consistency Audit

See [`Legal and Prior-Work Review`](standards/audits/legal-and-prior-work.md#existing-law-and-prior-proposal-consistency-audit).

### Functional Analogue Search

See [`Legal and Prior-Work Review`](standards/audits/legal-and-prior-work.md#functional-analogue-search).

## Links to Developed Work

See [`Content Navigation, Indexes, and Synchronization`](standards/content/navigation-and-indexes.md#links-to-developed-work).

## Cross-References

See [`Content Navigation, Indexes, and Synchronization`](standards/content/navigation-and-indexes.md#cross-references).
