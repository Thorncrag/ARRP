---
title: "American Restoration and Resilience Project — Framework and Methodology"
status: active
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# American Restoration and Resilience Project — Framework and Methodology

This file is ARRP's cross-cutting governing kernel and routing index. It states the principles, authority boundaries, and conventions that apply throughout the project. Detailed methodology is authoritative in the independently loadable modules linked below. Together, this kernel and those modules constitute the complete Framework; this file is not a compressed substitute for a module whose subject is implicated.

The public premise, mission, scope, and governing principles are maintained in [`../README.md`](../README.md). Repository paths and file purposes are maintained only in [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md). GitHub lifecycle fields and synchronization mechanics are maintained in [`GITHUB_WORKFLOW.md`](GITHUB_WORKFLOW.md). Print selection and assembly are maintained in [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md). Agent execution is governed by [`AGENT_OPERATING_RULES.md`](AGENT_OPERATING_RULES.md), with public-intake review governed separately by [`INTAKE_AGENT_PROCESS.md`](INTAKE_AGENT_PROCESS.md).

**Homepage synchronization notice.** The homepage's [Guiding Principle and introductory framing](../README.md#guiding-principle) mirror portions of the governing substance stated here in public-facing form. Any substantive revision in either location must include a synchronization review of the other and any necessary corresponding update in the same change. This Framework remains authoritative for project methodology; the homepage remains authoritative for the public statement of the project's premise, mission, and scope.

## How to Use This Document

Always load this kernel. Then load the smallest **complete** set of modules implicated by the work:

1. identify the primary operation and every material capability or project surface involved;
2. load the union of the corresponding modules in the [Governing Module Routes](#governing-module-routes), together with each module's stated dependencies;
3. load the applicable canonical records, such as the issue page, proposal vehicle, source records, audit history, runbook, GitHub fields, or publication surface; and
4. expand context before taking a dependent action whenever the task reveals a new subject, ambiguity, conflict, unfamiliar case, changed governing rule, stale input, or validation failure.

Routing is additive. Selecting one operation never excludes another module that the work also implicates. A bounded packet or summary is a nonauthoritative projection and may not narrow a human-reserved rule or replace the canonical file.

Automated agents should use reviewed, hash-verified routes and fail closed when required context is missing, stale, contradictory, oversized, or unregistered. Interactive work with the user remains comprehensive by default: the routes establish a minimum complete context, not a ceiling on investigation or review.

The human-readable routing and maintenance rules are in [`CONTEXT_ROUTING.md`](CONTEXT_ROUTING.md); the machine-readable registry is [`context-routes.json`](context-routes.json).

## Governing Authority

| Subject | Canonical authority |
| --- | --- |
| Cross-cutting project principles, authority, and routing | This kernel |
| Detailed scope, methodology, issue, evidence, lifecycle, source, candidate, audit, and scoring rules | The modules registered below and in [`context-routes.json`](context-routes.json) |
| Repository directories and file purposes | [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) |
| GitHub Issues, Project fields, lifecycle synchronization, workflow Status, and holds | [`GITHUB_WORKFLOW.md`](GITHUB_WORKFLOW.md) |
| Remedy selection, categories, repair and prevention, and trigger stages | [`REMEDY_FRAMEWORK.md`](REMEDY_FRAMEWORK.md) and linked specialized remedy records |
| Print selection, order, page locators, and compiled editions | [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md) and [`print-assembly.json`](print-assembly.json) |
| Agent and bot execution | [`AGENT_OPERATING_RULES.md`](AGENT_OPERATING_RULES.md), its routed modules, and the applicable registered runbook |
| Public-intake privacy and action boundary | [`INTAKE_AGENT_PROCESS.md`](INTAKE_AGENT_PROCESS.md) |
| Public release | [`PUBLIC_RELEASE.md`](PUBLIC_RELEASE.md) |

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

- **One authority and one primary home.** Each governing rule family and each institutional defect has one authoritative home. Other records link to it rather than create competing definitions. Repository placement is controlled by [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md).
- **Neutral standards, candid conclusions.** Apply the same evidentiary, legal, and remedial standards regardless of party, ideology, officeholder, administration, or movement. Distinguish fact, law, dispute or uncertainty, and ARRP's own institutional analysis. Party-neutral method does not require positionlessness or false symmetry.
- **Evidence before favorable credit.** Do not invent or infer unsupported facts, authorities, review, public support, professional validation, or outcomes. Unverified favorable propositions receive no favorable score credit.
- **Repair without reproducing arbitrariness.** Every remedy must address the independently repairable defect, preserve legitimate governmental discretion, and be tested for abuse, selective enforcement, personalization, inadequate constraint, and failure of review or correction.
- **Development level is not workflow Status.** The six-level maturity lifecycle is separate from the repeatable GitHub workflow action or hold. Research, revision, audit, external review, monitoring, and maintenance do not become maturity stages.
- **Human-reserved judgment remains human.** Only the human author may make a permanent candidate or issue disposition, answer or revise the reversed-control question, make a reserved foundational or materially consequential choice, alter project scope or methodology, change an audit rubric or scoring system, or authorize final circulation or publication. These reservations do not excuse an agent from reviewing the matter, explaining the options and uncertainty, and making a reasoned recommendation for human decision.
- **Rubrics are immutable without approval.** No rubric, formula, component, weight, penalty, threshold, or score band may change without recorded human approval and the required project-level Change Audit. A rubric may never be altered to engineer a desired score or portfolio result. The `Runs` field increases only for a completed, separately recorded T0–T4 issue-quality audit.
- **Permanent records remain traceable.** A retired, rejected, merged, integrated, removed, or otherwise finally adjudicated substantive record is preserved with its identifier, provenance, rationale, and disposition history rather than deleted.

## Governing Module Routes

The following routes are cumulative. Each linked module states its own load triggers and dependencies.

### Methodology, Issues, Evidence, and Remedies

| Work or subject | Authoritative module |
| --- | --- |
| Institutional scope, political-failure boundary, analytical method, or admission | [`methodology/scope-and-admission.md`](methodology/scope-and-admission.md) |
| Neutral characterization, claim status, motive, and reader-facing terminology | [`methodology/neutrality-and-language.md`](methodology/neutrality-and-language.md) |
| Partisan perception, public actors, President Trump, Project 2025, coalitions, or advocacy tone | [`methodology/partisan-perception-and-public-actors.md`](methodology/partisan-perception-and-public-actors.md) |
| Issue-page structure, proposal presentation, snapshot, survey, budget, or concision | [`issues/issue-architecture.md`](issues/issue-architecture.md) |
| Annotation, assertion discipline, and source quality | [`evidence/annotation-and-source-standards.md`](evidence/annotation-and-source-standards.md) |
| Evidence pages, source-development records, qualitative placement, or issue-source reconciliation | [`evidence/evidence-records.md`](evidence/evidence-records.md) |
| Remedy selection, repair and prevention, constitutional amendments, taxonomy, or triggers | [`REMEDY_FRAMEWORK.md`](REMEDY_FRAMEWORK.md) |
| Executive nullification or evasion of enacted federal commands | [`INTERBRANCH_REVIEW_FRAMEWORK.md`](INTERBRANCH_REVIEW_FRAMEWORK.md) and [`INTERBRANCH_REVIEW_COVERAGE_MATRIX.md`](INTERBRANCH_REVIEW_COVERAGE_MATRIX.md) |

### Lifecycle, Operations, Sources, Candidates, and Navigation

| Work or subject | Authoritative module |
| --- | --- |
| Six maturity levels, pre-lifecycle intake, or repeatable workflows | [`lifecycle/development-levels.md`](lifecycle/development-levels.md) |
| Four-part foundation, delegated development, human reservations, or post-admission gates | [`lifecycle/foundation-and-development-gates.md`](lifecycle/foundation-and-development-gates.md) |
| GitHub Status, holds, labels, fields, transitions, or synchronization | [`GITHUB_WORKFLOW.md`](GITHUB_WORKFLOW.md) |
| Substantive issue-work preflight and closeout | [`operations/issue-development-check.md`](operations/issue-development-check.md) |
| Cross-surface project updates | [`operations/project-update-checklist.md`](operations/project-update-checklist.md) |
| Source catalogs, stable source identity, review metadata, or source-level monitoring | [`sources/source-catalogs.md`](sources/source-catalogs.md) |
| Issue monitoring or a project-wide monitoring pass | [`sources/project-monitoring.md`](sources/project-monitoring.md) |
| Automated source routing, preliminary-candidate synthesis, or batch reconciliation | [`sources/automated-source-adjudication.md`](sources/automated-source-adjudication.md) |
| Presidential-directive completeness or substantive directive review | [`sources/presidential-directives.md`](sources/presidential-directives.md) |
| Horizon discovery | [`candidates/horizon-scanning.md`](candidates/horizon-scanning.md) |
| Formal Horizon candidate investigation or disposition implementation | [`candidates/candidate-adjudication.md`](candidates/candidate-adjudication.md) |
| Inventory files, area lists, stable issue identity, developed-work links, or cross-references | [`navigation/inventory-and-indexes.md`](navigation/inventory-and-indexes.md) |
| Topic-guide creation or revision | [`navigation/topic-guides.md`](navigation/topic-guides.md) |
| Navigation synchronization or its T1 gate | [`navigation/navigation-synchronization.md`](navigation/navigation-synchronization.md) |

### Audits and Scoring

| Work or subject | Authoritative module |
| --- | --- |
| Common audit orientation, workflow, run counting, unknowns, preservation, output, or method learning | [`audits/AUDIT_CORE.md`](audits/AUDIT_CORE.md) |
| T0–T4 depth or formatting preflight | [`audits/TIERED_AUDITS.md`](audits/TIERED_AUDITS.md) |
| Change Audit or Internal Remedy-Fit Audit | [`audits/CHANGE_AUDITS.md`](audits/CHANGE_AUDITS.md) |
| Project consistency audit | [`audits/PROJECT_CONSISTENCY_AUDITS.md`](audits/PROJECT_CONSISTENCY_AUDITS.md) |
| Hallucination resistance, source verification, or traceability | [`audits/VERIFICATION_PROTOCOL.md`](audits/VERIFICATION_PROTOCOL.md) |
| Existing law, judicial or scholarly scrutiny, prior proposals, or functional analogues | [`audits/LEGAL_AND_PRIOR_PROPOSAL_REVIEW.md`](audits/LEGAL_AND_PRIOR_PROPOSAL_REVIEW.md) |
| Proposal quality, rubric governance, penalties, fixed zeroes, or score consistency | [`scoring/PROPOSAL_QUALITY_AND_RUBRIC.md`](scoring/PROPOSAL_QUALITY_AND_RUBRIC.md) |
| Adoption formula, enactment pathway, friction, support, or coalition appeal | [`scoring/ADOPTION_AND_PATHWAY.md`](scoring/ADOPTION_AND_PATHWAY.md) |
| Qualified external review or international support and relations | [`scoring/EXTERNAL_AND_INTERNATIONAL_REVIEW.md`](scoring/EXTERNAL_AND_INTERNATIONAL_REVIEW.md) |

### Project and Agent Operations

| Work or subject | Authoritative record |
| --- | --- |
| Agent or bot behavior | [`AGENT_OPERATING_RULES.md`](AGENT_OPERATING_RULES.md), its [`agent-rules/`](agent-rules/) modules, and any applicable [`agents/`](agents/) runbook |
| Context selection, manifest maintenance, or comprehensive-review coverage | [`CONTEXT_ROUTING.md`](CONTEXT_ROUTING.md) and [`context-routes.json`](context-routes.json) |
| Repository placement | [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) |
| Project-operated interface layout and behavior | [`PROJECT_INTERFACE.md`](PROJECT_INTERFACE.md) |
| Console progress calculation and display | [`PROJECT_CONSOLE_PROGRESS.md`](PROJECT_CONSOLE_PROGRESS.md) |
| Publication and compiled editions | [`PUBLIC_RELEASE.md`](PUBLIC_RELEASE.md), [`PRINT_ASSEMBLY.md`](PRINT_ASSEMBLY.md), and [`print-assembly.json`](print-assembly.json) |

## Comprehensive Review Boundary

The machine-readable context registry identifies every stable governing document with `governing: true`. A periodic comprehensive review must load all such documents, the current mutable checkpoint, the applicable persistent-agent runbook, and the reviewed project inputs. It establishes a dated boundary so later reviews can focus on intervening change without losing the periodic whole-project look-back.

Adding, moving, renaming, or materially changing a governing module requires the same change to update its registry entry, dependencies, affected profiles and capabilities, compatibility pointer when applicable, repository-structure description, and validation. A module that is absent from the registry is not eligible to be silently omitted; automated work must fail closed and interactive work must expand to the canonical file.

## Compatibility Routing Anchors

The following stable headings preserve existing repository links. They are pointers, not duplicate statements of the detailed rules.

## Neutrality and Language Guidelines

See [`methodology/neutrality-and-language.md`](methodology/neutrality-and-language.md) and [`methodology/partisan-perception-and-public-actors.md`](methodology/partisan-perception-and-public-actors.md).

### Institutional Focus

See [`methodology/scope-and-admission.md`](methodology/scope-and-admission.md#institutional-focus).

### Resilience and Temporal Scope

See [`methodology/scope-and-admission.md`](methodology/scope-and-admission.md#resilience-and-temporal-scope).

### Political-Failure Boundary

See [`methodology/scope-and-admission.md`](methodology/scope-and-admission.md#political-failure-boundary).

### Neutral Application

See [`methodology/neutrality-and-language.md`](methodology/neutrality-and-language.md#neutral-application).

### Substantive Positions and Partisan Perception

See [`methodology/partisan-perception-and-public-actors.md`](methodology/partisan-perception-and-public-actors.md#substantive-positions-and-partisan-perception).

### Public-Actor References

See [`methodology/partisan-perception-and-public-actors.md`](methodology/partisan-perception-and-public-actors.md#public-actor-references).

### Accuracy Over Softening

See [`methodology/neutrality-and-language.md`](methodology/neutrality-and-language.md#accuracy-over-softening).

### Neutral Characterization

See [`methodology/neutrality-and-language.md`](methodology/neutrality-and-language.md#neutral-characterization).

### Motive and Intent

See [`methodology/neutrality-and-language.md`](methodology/neutrality-and-language.md#motive-and-intent).

### Conduct Before Character

See [`methodology/neutrality-and-language.md`](methodology/neutrality-and-language.md#conduct-before-character).

### Reader-Facing and Technical Terminology

See [`methodology/neutrality-and-language.md`](methodology/neutrality-and-language.md#reader-facing-and-technical-terminology).

### Project 2025 Treatment

See [`methodology/partisan-perception-and-public-actors.md`](methodology/partisan-perception-and-public-actors.md#project-2025-treatment).

### Collective Labels

See [`methodology/partisan-perception-and-public-actors.md`](methodology/partisan-perception-and-public-actors.md#collective-labels).

### Coalition Reality

See [`methodology/partisan-perception-and-public-actors.md`](methodology/partisan-perception-and-public-actors.md#coalition-reality).

### Advocacy Tone

See [`methodology/partisan-perception-and-public-actors.md`](methodology/partisan-perception-and-public-actors.md#advocacy-tone).

## Analytical Method

See [`methodology/scope-and-admission.md`](methodology/scope-and-admission.md#analytical-method).

### Issue-Admission Test

See [`methodology/scope-and-admission.md`](methodology/scope-and-admission.md#issue-admission-test).

## Mandatory Issue Architecture

See [`issues/issue-architecture.md`](issues/issue-architecture.md#mandatory-issue-architecture).

### Issue Snapshot Format

See [`issues/issue-architecture.md`](issues/issue-architecture.md#issue-snapshot-format).

### Proposal Survey

See [`issues/issue-architecture.md`](issues/issue-architecture.md#proposal-survey).

## Issue-Level Conciseness

See [`issues/issue-architecture.md`](issues/issue-architecture.md#issue-level-conciseness).

## Annotation and Evidence

See [`evidence/annotation-and-source-standards.md`](evidence/annotation-and-source-standards.md#annotation-and-evidence).

### Standard Annotation

See [`evidence/annotation-and-source-standards.md`](evidence/annotation-and-source-standards.md#standard-annotation).

### Assertion Discipline

See [`evidence/annotation-and-source-standards.md`](evidence/annotation-and-source-standards.md#assertion-discipline).

### Source Standard

See [`evidence/annotation-and-source-standards.md`](evidence/annotation-and-source-standards.md#source-standard).

## Least-Complex Adequate Remedy

See [`REMEDY_FRAMEWORK.md`](REMEDY_FRAMEWORK.md#least-complex-adequate-remedy).

## Repair and Prevention

See [`REMEDY_FRAMEWORK.md`](REMEDY_FRAMEWORK.md#repair-and-prevention).

## Constitutional Amendments

See [`REMEDY_FRAMEWORK.md`](REMEDY_FRAMEWORK.md#constitutional-amendments).

## Automatic Constitutional Stabilizers and Institutional-Failure Triggers

See [`REMEDY_FRAMEWORK.md`](REMEDY_FRAMEWORK.md#trigger-stages).

## Project Lifecycle, Sources, Navigation, and Audits

Use the applicable routes above; this heading remains only as the former section's stable entry point.

## Inventory Files

See [`navigation/inventory-and-indexes.md`](navigation/inventory-and-indexes.md#inventory-files).

## Inventory Rules

See [`navigation/inventory-and-indexes.md`](navigation/inventory-and-indexes.md#inventory-rules).

## Issue Lifecycle: Discovery Through Publication and Maintenance

See [`lifecycle/development-levels.md`](lifecycle/development-levels.md#issue-lifecycle-discovery-through-publication-and-maintenance).

### Development-Level Lifecycle

See [`lifecycle/development-levels.md`](lifecycle/development-levels.md#development-level-lifecycle).

### Intake Before the Development-Level Lifecycle

See [`lifecycle/development-levels.md`](lifecycle/development-levels.md#intake-before-the-development-level-lifecycle).

### Repeatable Workflows Around the Lifecycle

See [`lifecycle/development-levels.md`](lifecycle/development-levels.md#repeatable-workflows-around-the-lifecycle).

### Workflow Status and Hold Definitions

See [`GITHUB_WORKFLOW.md`](GITHUB_WORKFLOW.md#issue-development-lifecycle).

### Human-Governed Foundation and Delegated Development

See [`lifecycle/foundation-and-development-gates.md`](lifecycle/foundation-and-development-gates.md#human-governed-foundation-and-delegated-development).

### Post-Admission Development Gates

See [`lifecycle/foundation-and-development-gates.md`](lifecycle/foundation-and-development-gates.md#post-admission-development-gates).

### Persistent Agents and Runbooks

See [`AGENT_OPERATING_RULES.md`](AGENT_OPERATING_RULES.md#persistent-agent-runbooks).

## Issue-Development Lifecycle Check

See [`operations/issue-development-check.md`](operations/issue-development-check.md#required-check).

## Project-Update Checklist

See [`operations/project-update-checklist.md`](operations/project-update-checklist.md#project-update-checklist).

## Area and Issue Index Rules

See [`navigation/inventory-and-indexes.md`](navigation/inventory-and-indexes.md#area-and-issue-index-rules).

### Area-Page Issue Lists

See [`navigation/inventory-and-indexes.md`](navigation/inventory-and-indexes.md#area-page-issue-lists).

### Topic Page Standard

See [`navigation/topic-guides.md`](navigation/topic-guides.md#topic-page-standard).

### Navigation Synchronization Check

See [`navigation/navigation-synchronization.md`](navigation/navigation-synchronization.md#navigation-synchronization-check).

### Project-Operated Interface Visual Standard

See [`PROJECT_INTERFACE.md`](PROJECT_INTERFACE.md#project-operated-interface-visual-standard).

## Source Inventory Rules

See [`sources/source-catalogs.md`](sources/source-catalogs.md#source-inventory-rules).

## Automated Source Adjudication and Issue Evidence Records

See [`sources/automated-source-adjudication.md`](sources/automated-source-adjudication.md) and [`evidence/evidence-records.md`](evidence/evidence-records.md).

### Evidence and Monitoring Architecture

See [`evidence/evidence-records.md`](evidence/evidence-records.md#evidence-architecture) and [`sources/project-monitoring.md`](sources/project-monitoring.md).

### Source Reconciliation During Issue Work

See [`evidence/evidence-records.md`](evidence/evidence-records.md#source-reconciliation-during-issue-work).

### Project-Wide Monitoring Pass

See [`sources/project-monitoring.md`](sources/project-monitoring.md#project-wide-monitoring-pass).

### Route-Centered Automated Adjudication

See [`sources/automated-source-adjudication.md`](sources/automated-source-adjudication.md#route-centered-automated-adjudication).

### Presidential-Directive Completeness Scans

See [`sources/presidential-directives.md`](sources/presidential-directives.md#presidential-directive-completeness-scans).

### Automation and Human-Decision Boundary

See [`sources/automated-source-adjudication.md`](sources/automated-source-adjudication.md#automation-and-human-decision-boundary).

### Batch Reconciliation and Closeout

See [`sources/automated-source-adjudication.md`](sources/automated-source-adjudication.md#batch-reconciliation-and-closeout).

## Audit Rules and Proposal Quality Scoring

See the audit and scoring routes above.

### Pre-Audit Orientation

See [`audits/AUDIT_CORE.md`](audits/AUDIT_CORE.md#pre-audit-orientation).

### Change Audit

See [`audits/CHANGE_AUDITS.md`](audits/CHANGE_AUDITS.md#change-audit).

### Audit Workflow

See [`audits/AUDIT_CORE.md`](audits/AUDIT_CORE.md#audit-workflow).

### Formatting Preflight

See [`audits/TIERED_AUDITS.md`](audits/TIERED_AUDITS.md#formatting-preflight).

### Audit Run Counting Rule

See [`audits/AUDIT_CORE.md`](audits/AUDIT_CORE.md#audit-run-counting-rule).

### Project Consistency Audit

See [`audits/PROJECT_CONSISTENCY_AUDITS.md`](audits/PROJECT_CONSISTENCY_AUDITS.md#project-consistency-audit).

### Audit Learning and Method Improvement

See [`audits/AUDIT_CORE.md`](audits/AUDIT_CORE.md#audit-learning-and-method-improvement).

### Audit Depth Tiers

See [`audits/TIERED_AUDITS.md`](audits/TIERED_AUDITS.md#audit-depth-tiers).

### Horizon Scan Audit

See [`candidates/horizon-scanning.md`](candidates/horizon-scanning.md#horizon-scan).

### Horizon Candidate Adjudication Workflow

See [`candidates/candidate-adjudication.md`](candidates/candidate-adjudication.md#horizon-candidate-adjudication-workflow).

### Audit Autonomy and Unknowns

See [`audits/AUDIT_CORE.md`](audits/AUDIT_CORE.md#audit-autonomy-and-unknowns).

### Audit Preservation and GitHub Storage

See [`audits/AUDIT_CORE.md`](audits/AUDIT_CORE.md#audit-preservation-and-github-storage).

### Audit Output

See [`audits/AUDIT_CORE.md`](audits/AUDIT_CORE.md#audit-output).

### Hallucination-Resistance and Verification Protocol

See [`audits/VERIFICATION_PROTOCOL.md`](audits/VERIFICATION_PROTOCOL.md#hallucination-resistance-and-verification-protocol).

### Proposal Quality Score

See [`scoring/PROPOSAL_QUALITY_AND_RUBRIC.md`](scoring/PROPOSAL_QUALITY_AND_RUBRIC.md#proposal-quality-score).

### External Review Status and Qualified Reviewers

See [`scoring/EXTERNAL_AND_INTERNATIONAL_REVIEW.md`](scoring/EXTERNAL_AND_INTERNATIONAL_REVIEW.md#external-review-status-and-qualified-reviewers).

### Adoption Score Formula

See [`scoring/ADOPTION_AND_PATHWAY.md`](scoring/ADOPTION_AND_PATHWAY.md#adoption-score-formula).

### Enactment Pathway Check

See [`scoring/ADOPTION_AND_PATHWAY.md`](scoring/ADOPTION_AND_PATHWAY.md#enactment-pathway-check).

#### Institutional Self-Limitation Rule

See [`scoring/ADOPTION_AND_PATHWAY.md`](scoring/ADOPTION_AND_PATHWAY.md#institutional-self-limitation-rule).

### Adoption Friction Score

See [`scoring/ADOPTION_AND_PATHWAY.md`](scoring/ADOPTION_AND_PATHWAY.md#adoption-friction-score).

### International Support and Relations Score

See [`scoring/EXTERNAL_AND_INTERNATIONAL_REVIEW.md`](scoring/EXTERNAL_AND_INTERNATIONAL_REVIEW.md#international-support-and-relations-score).

### Score Consistency Rules

See [`scoring/PROPOSAL_QUALITY_AND_RUBRIC.md`](scoring/PROPOSAL_QUALITY_AND_RUBRIC.md#score-consistency-rules).

### Support and Adoption Audit

See [`scoring/ADOPTION_AND_PATHWAY.md`](scoring/ADOPTION_AND_PATHWAY.md#support-and-adoption-audit).

### Political-Language and Coalition-Appeal Audit

See [`scoring/ADOPTION_AND_PATHWAY.md`](scoring/ADOPTION_AND_PATHWAY.md#political-language-and-coalition-appeal-audit).

### Judicial and Scholarly Scrutiny Audit

See [`audits/LEGAL_AND_PRIOR_PROPOSAL_REVIEW.md`](audits/LEGAL_AND_PRIOR_PROPOSAL_REVIEW.md#judicial-and-scholarly-scrutiny-audit).

### Existing-Law and Prior-Proposal Consistency Audit

See [`audits/LEGAL_AND_PRIOR_PROPOSAL_REVIEW.md`](audits/LEGAL_AND_PRIOR_PROPOSAL_REVIEW.md#existing-law-and-prior-proposal-consistency-audit).

### Functional Analogue Search

See [`audits/LEGAL_AND_PRIOR_PROPOSAL_REVIEW.md`](audits/LEGAL_AND_PRIOR_PROPOSAL_REVIEW.md#functional-analogue-search).

## Links to Developed Work

See [`navigation/inventory-and-indexes.md`](navigation/inventory-and-indexes.md#links-to-developed-work).

## Cross-References

See [`navigation/inventory-and-indexes.md`](navigation/inventory-and-indexes.md#cross-references).
