---
title: "ARRP Governance Change Log"
status: active
print_status: excluded
print_exclusion_reason: "Internal governance and provenance record."
---

# ARRP Governance Change Log

This public-safe log records material governance decisions by stable GOV
identity. It is governed by the
[Governance Change Recording workflow](../../project/workflows/governance-change-recording.md).
Current governing documents remain authoritative; Git remains the exact-diff
authority. The historical [Change Audit Log](../audits/change-audit-log.md)
remains separate and unchanged.

## GOV-2026-020 — Component Registry Stage 1 authority transition

- Date: 2026-07-30
- Status: Proposed / unmerged
- Decision class: governance_documentation
- Authorities: framework/component-registry.json;
  framework/component-registry.schema.json;
  scripts/component_registry.py;
  scripts/finalize_component_registry_activation.py
- Decision: Proposes adopting the validated Component Registry as the sole
  Stage 1 component and routing authority, relocating the four frozen
  predecessors to provenance-only archive paths, and preserving terminology
  and Stage 2 lifecycle classifications as explicitly deferred.
- Evidence: Current activation worktree and draft PR #498. The exact final
  candidate commit, activation head, latest-head owner review, required
  checks, merge commit, canonical remote readback, and fixed activation
  receipt remain pending.
- Policy adoption: Proposed only; not adopted before the reviewed activation
  merge.
- Live activation: Not active. The registry remains candidate,
  nonauthoritative, and nonexecutable; the activation receipt is absent and
  automation remains Paused.
- Relationships: No supersession or refinement is claimed.
- Validation: Candidate registry, routing parity, Stage 1 closure, migration,
  disclosure, Project Integrity, Source Checker, Console, and activation
  finalizer checks are in progress under the approved transaction.
- Owner-local supplement: Required.

## GOV-2026-019 — Lease-bound GitHub branch retirement

- Date: 2026-07-29
- Status: Canonical
- Decision class: security_privacy_disclosure
- Authorities: framework/project/github/disclosure-boundary.md;
  framework/project/github/disclosure-policy.json;
  framework/project/github/workflow.md; scripts/github_disclosure_gate.py
- Decision: Adds one contentless GitHub control operation for retiring an exact
  non-default branch. It binds the fixed repository and `origin`, one complete
  expected-old object ID, the all-zero new object ID, a single deletion
  refspec, and an expected-old lease. It does not broaden ordinary publishing
  or GitHub App authority.
- Evidence: Implementation commit
  4d9e595962c2cbfab58e4822144fc60f7939ac35; PR #496; merge commit
  a8dac880e7c65250fd6ab4ec5bc30135cf39934e; four distinct public-safe
  authorization digests and remote absence readbacks.
- Policy adoption: Adopted on canonical history through PR #496.
- Live activation: The four approved obsolete remote branches were
  individually retired at their exact expected object IDs with lease-bound
  execution and absence readback.
- Relationships: Refines GOV-2026-002 and GOV-2026-017; no supersession.
- Validation: Focused authorization, lease, moved-ref, fabricated-decision,
  invalid-input, policy-isolation, and App non-expansion checks passed; the
  complete 694-test Python suite, 52 frontend tests, project consistency
  review, context-hash verification, and a read-only production authorization
  also passed. All PR validation, CodeQL, and Vercel checks passed before
  merge.
- Owner-local supplement: Required.

## GOV-2026-018 — Transaction lifecycle, retry, and recovery authority

- Date: 2026-07-29
- Status: Canonical
- Decision class: operations_automation
- Authorities: framework/project/automation/transaction-lifecycle.md;
  framework/project/automation/project-wide-reconciliation.json;
  framework/project/automation/autonomous-execution.md
- Decision: Establishes one owner-local append-only attempt history, makes
  status and scheduled-slot files nonauthoritative projections, requires
  one-use digest-bound retry authorization, preserves failed work through
  non-checkout recovery packages, and prevents a retained transaction from
  becoming reconciled merely because it is listed in a ledger.
- Evidence: Implementation commit
  e7be3ec12c09139c07959db7e25e2146b1f91a55; PR #494; merge commit
  f39fb6b7ea4e43fe12099c022d50a5c0bd3db7da; owner-local transaction
  migration and exact recoverable-retirement receipts.
- Policy adoption: Adopted on canonical history through PR #494.
- Live activation: The owner-local transaction lifecycle and recovery
  authority is active. Automation remains intentionally Paused; no production
  run or host/background-service mutation was performed.
- Relationships: Refines GOV-2026-016 and the transaction-recovery portion of
  GOV-2026-011 without changing the active runtime location.
- Validation: The complete 687-test Python suite, 52 frontend tests,
  transaction and reconciliation regressions, consistency audit, strict site
  build, disclosure gate, CodeQL, GitHub Actions, and Vercel checks passed.
  Twelve immutable recovery packages and their retirement receipts were
  independently reconciled, and no live runtime transaction worktree remains.
- Owner-local supplement: Required.

## GOV-2026-017 — Exact Git-push revision binding

- Date: 2026-07-29
- Status: Canonical
- Decision class: security_privacy_disclosure
- Authorities: framework/project/github/disclosure-boundary.md; framework/project/github/workflow.md; scripts/github_disclosure_gate.py
- Decision: Requires Git-push disclosure authorization to derive the complete
  committed base-to-head manifest and bind one exact full-OID refspec. Caller
  metadata, selected paths, working-tree bytes, abbreviated identities, and
  later validation cannot substitute for pre-transmission binding.
- Evidence: Implementation commit
  e7be3ec12c09139c07959db7e25e2146b1f91a55; PR #494; merge commit
  f39fb6b7ea4e43fe12099c022d50a5c0bd3db7da.
- Policy adoption: Adopted on canonical history through PR #494.
- Live activation: The exact committed-range gate authorized the complete
  77-artifact range and full-OID refspec before transmission. The remote branch
  and merged pull request were read back at the authorized revision.
- Relationships: Refines GOV-2026-002 without changing its classification or
  no-secret boundary.
- Validation: Exact-range, nonexistent-revision, wrong-head, dirty-worktree,
  removal, and ref-movement tests passed; the active owner-local control pack
  returned a complete authoritative decision with zero findings; all GitHub
  Actions and CodeQL checks passed with no open PR alerts.
- Owner-local supplement: Required.

## GOV-2026-016 — Project-wide operational reconciliation boundary

- Date: 2026-07-29
- Status: Canonical
- Decision class: operations_automation
- Authorities: framework/project/automation/project-wide-reconciliation.json; framework/project/workflows/project-update.md; framework/project/automation/owner-local-runtime.md
- Decision: Defines complete project-wide operational reconciliation across
  canonical and remote Git, retained local transaction state, active writers
  and handoffs, automation posture, project-created pull requests, and affected
  hosted readbacks. Every retained state requires an exact bound disposition;
  pending or unknown state cannot be reported as fully reconciled. This
  decision has no content, editorial, methodological, or political-neutrality
  meaning.
- Evidence: Implementation commit
  e7be3ec12c09139c07959db7e25e2146b1f91a55; PR #494; merge commit
  f39fb6b7ea4e43fe12099c022d50a5c0bd3db7da.
- Policy adoption: Adopted on canonical history through PR #494.
- Live activation: The verifier is read-only. Automation remains intentionally
  Paused, and no host or background-service state is changed.
- Relationships: Additive and refined by GOV-2026-018; no recorded
  supersession.
- Validation: The verifier's false-neutral, retained-state, exact-proof,
  stale-readback, and lock-posture regressions passed together with the
  complete repository suite. Final operational certification remains an
  owner-local readback rather than a public governance claim.
- Owner-local supplement: Required.

## GOV-2026-015 — Rule reconciliation and usage-aware agent delegation

- Date: 2026-07-29
- Status: Canonical
- Decision class: governance_documentation
- Authorities: AGENTS.md; framework/standards/automation/multi-agent.md; Global Codex guidance
- Decision: Requires task-appropriate lower-reasoning delegation for bounded,
  verifiable work without reducing coverage, and requires reconciliation before
  persistent rules or memories are added or materially revised. An actual
  conflict among active user-controlled rules stops affected work for Benjamin
  rather than receiving inferred precedence.
- Evidence: Implementation commit
  41c5a906a08179f284efb6a9f74bb48781d7aa8d; PR #492; merge commit
  231b9031c7f8e1575f01ec6adab8d8563dc415c0.
- Policy adoption: Adopted on canonical history through PR #492.
- Live activation: Global local guidance is active and the project delegation
  rule is canonical. No background service is changed.
- Relationships: Additive; no recorded supersession or refinement.
- Validation: Governance parser, 637-test Python suite, project consistency
  review, disclosure gate, repository validation, site, Console, participation,
  runtime-policy, CodeQL, and Vercel checks passed.
- Owner-local supplement: Not required.

## GOV-2026-014 — Owner-local preservation-boundary proposal

- Date: 2026-07-29
- Status: Proposed / not adopted
- Decision class: security_privacy_disclosure
- Authorities: ARRP Private owner directives
- Decision: Records the unresolved proposal to narrow the exceptional
  preservation and policy-change boundary within the owner-local workspace;
  it does not change the current directive.
- Evidence: Proposal preserved through PR #487 and merge commit
  ea57c9826270a12ae6e0275390a2c9555169f43d; no exact owner approval of
  replacement text.
- Policy adoption: Not adopted; exact owner approval of the replacement text remains required.
- Live activation: No directive or runtime change is activated.
- Relationships: Additive; the current owner directive remains controlling.
- Validation: Current-directive preservation, candidate isolation, and
  no-activation checks.
- Owner-local supplement: Required.

## GOV-2026-013 — Governance Change Recording authority

- Date: 2026-07-29
- Status: Canonical
- Decision class: governance_documentation
- Authorities: framework/project/workflows/governance-change-recording.md; framework/project/workflows/governance-change-registry.json
- Decision: Establishes this public GOV index and strict provenance workflow; it
  does not create a private record or alter another governing authority.
- Evidence: Implementation commits
  6167fc3554af006091ecee7d62be5a26514f7237,
  8306f07e96302afdca6ba85eae105905fc18cb60, and
  754efbacf7f578b74823dc91a2e71a63cae42ecd; PR #487; merge commit
  ea57c9826270a12ae6e0275390a2c9555169f43d.
- Policy adoption: Adopted on canonical history through PR #487.
- Live activation: No live activation applies.
- Relationships: Additive; no recorded supersession or refinement.
- Validation: Registry, heading, parser, Console, Markdown, full test, and
  disclosure checks passed; exact canonical evidence is reconciled here.
- Owner-local supplement: Not required.

## GOV-2026-012 — Separate operational and security incident authorities

- Date: 2026-07-29
- Status: Canonical
- Decision class: security_privacy_disclosure
- Authorities: framework/project/automation/security-incidents.json; framework/project/automation/incident-relations.json
- Decision: Establishes separate operational and security incident authorities
  with a typed relation only; neither lifecycle is merged.
- Evidence: Implementation commits
  6167fc3554af006091ecee7d62be5a26514f7237,
  8306f07e96302afdca6ba85eae105905fc18cb60, and
  754efbacf7f578b74823dc91a2e71a63cae42ecd; PR #487; merge commit
  ea57c9826270a12ae6e0275390a2c9555169f43d.
- Policy adoption: Adopted on canonical history through PR #487.
- Live activation: The protected Security Incident and relation authorities
  remain inactive and unavailable pending separate exact approval.
- Relationships: Refines GOV-2026-004 by separating protected security
  investigation from operational disruption and recovery.
- Validation: Incident-authority, relation, privacy, Console, full test, and
  disclosure checks passed; all PR CodeQL checks passed with no open alerts.
- Owner-local supplement: Required.

## GOV-2026-011 — Owner-local runtime authority

- Date: 2026-07-29
- Status: Canonical
- Decision class: operations_automation
- Authorities: framework/project/automation/owner-local-runtime.md
- Decision: Establishes a single current-versus-successor runtime, migration,
  cutover, rollback, and retirement authority.
- Evidence: Implementation commits
  6167fc3554af006091ecee7d62be5a26514f7237,
  8306f07e96302afdca6ba85eae105905fc18cb60, and
  754efbacf7f578b74823dc91a2e71a63cae42ecd; PR #487; merge commit
  ea57c9826270a12ae6e0275390a2c9555169f43d.
- Policy adoption: Adopted on canonical history through PR #487.
- Live activation: No cutover is activated; the current production authority
  and intentional pause remain unchanged.
- Relationships: Refines the location aspects of GOV-2026-002,
  GOV-2026-003, GOV-2026-005, and GOV-2026-010 without changing their
  disclosure, record, gate, or refresh semantics.
- Validation: Runtime documentation, migration, fixed path-authority,
  no-caller-substitution, full test, CodeQL, and disclosure checks passed.
- Owner-local supplement: Required.

## GOV-2026-010 — Authenticated owner refresh boundary

- Date: 2026-07-29
- Status: Canonical
- Decision class: security_privacy_disclosure
- Authorities: framework/project/interfaces/project-console/specification.md; scripts/refresh_project_console.py
- Decision: Separates owner-invoked authenticated refresh from a credential-free
  static Console that cannot initiate refresh.
- Evidence: PRs #485–486; merges
  `10ec1342713e11543377b89de5f5ffc8cf5ddf8d` and
  `572e1db1ebfff49cc26004cced1d0933934fa4c6`.
- Policy adoption: Adopted on canonical history.
- Live activation: No host service is activated by this record.
- Relationships: Refines GOV-2026-003; refined by GOV-2026-011 for
  owner-local location resolution only.
- Validation: Authenticated-refresh, credential-confinement, data-contract,
  and closeout checks.
- Owner-local supplement: Required.

## GOV-2026-009 — Typed classifications and unavailable-state discipline

- Date: 2026-07-28
- Status: Canonical
- Decision class: data_provenance_integrity
- Authorities: framework/project/interfaces/project-console/configuration/classifications.json; framework/project/interfaces/project-console/specification.md
- Decision: Makes typed classification enforceable and requires unavailable,
  rather than zero or healthy, treatment for missing or protected data.
- Evidence: PRs #483–484; merges
  `1da18c49db38d4f6d6bc50fe1f5d21d46ac9f5e3` and
  `4e6f2c293daf47a4584d1c25866cb6fc4f4e36ac`.
- Policy adoption: Adopted on canonical history.
- Live activation: No host activation is represented.
- Relationships: Refines GOV-2026-001 and GOV-2026-006 without replacing their
  independent authorities.
- Validation: Classification, consistency, stale-feed, public-bundle, and
  frontend checks.
- Owner-local supplement: Required.

## GOV-2026-008 — Participation-site analytics transparency

- Date: 2026-07-28
- Status: Canonical
- Decision class: public_input_transparency
- Authorities: participate/README.md; participate/SECURITY.md
- Decision: Adds a visible analytics notice that remains present across form modes.
- Evidence: PR #482; merge `5672b158a9cdfda4ca754ddcaa939bd0b26509f2`.
- Policy adoption: Adopted on canonical history.
- Live activation: No activation claim is made by this notice record.
- Relationships: No recorded supersession or refinement.
- Validation: Participation analytics and safety checks.
- Owner-local supplement: Not required.

## GOV-2026-007 — Console Development Log governance

- Date: 2026-07-28
- Status: Canonical
- Decision class: governance_documentation
- Authorities: framework/logs/automation/console-development-log.md
- Decision: Establishes stable Console Change IDs and dated, category-based
  provenance entries without making the Console log a governing authority.
- Evidence: PR #481; merge `a0dd9516a427299accd7de7ede944ae8d39a6d77`.
- Policy adoption: Adopted on canonical history.
- Live activation: No host activation is represented.
- Relationships: Additive; no recorded supersession or refinement.
- Validation: Category and frontend projection checks.
- Owner-local supplement: Not required.

## GOV-2026-006 — Public-safe security assurance

- Date: 2026-07-28
- Status: Canonical
- Decision class: security_privacy_disclosure
- Authorities: framework/project/interfaces/project-console/configuration/classifications.json; framework/standards/interfaces/standard.md
- Decision: Adopts allowlisted security-assurance presentation while excluding
  protected evidence and operational detail from public surfaces.
- Evidence: PR #480; merge `6e0b4708cd714f39c1a5b7c9f3bcd3405a72431d`.
- Policy adoption: Adopted on canonical history.
- Live activation: No host activation is represented.
- Relationships: Refined by GOV-2026-009 for typed display discipline.
- Validation: Assurance allowlist, no-detail, and frontend checks.
- Owner-local supplement: Required.

## GOV-2026-005 — Repository-gate authority

- Date: 2026-07-28
- Status: Canonical
- Decision class: operations_automation
- Authorities: framework/project/automation/repository-gates.json
- Decision: Establishes typed repository-gate declarations as the sole gate
  authority for a declared automation stage.
- Evidence: PR #479; merge `93a01eb24dfb94c848a1f937e9e1bdfeea72c74d`.
- Policy adoption: Adopted on canonical history.
- Live activation: No host activation is represented.
- Relationships: Refined by GOV-2026-011 for path resolution only; the gate
  identity and enforcement authority remain canonical.
- Validation: Repository-gate and run-chain checks.
- Owner-local supplement: Required.

## GOV-2026-004 — Operational Incident authority

- Date: 2026-07-28
- Status: Canonical
- Decision class: operations_automation
- Authorities: framework/project/automation/operational-incidents.json
- Decision: Establishes validated operational incident identity, admission,
  lifecycle, recovery evidence, and closure authority.
- Evidence: PR #479; merge `93a01eb24dfb94c848a1f937e9e1bdfeea72c74d`.
- Policy adoption: Adopted on canonical history.
- Live activation: No host activation is represented.
- Relationships: Refined by GOV-2026-012, which separates protected security
  investigation while leaving the operational lifecycle canonical.
- Validation: Operational-incident and path-authority checks.
- Owner-local supplement: Required.

## GOV-2026-003 — Owner-local protected operational records

- Date: 2026-07-28
- Status: Canonical
- Decision class: security_privacy_disclosure
- Authorities: framework/project/github/disclosure-boundary.md; framework/archive/authorities/PROJECT_STRUCTURE.md
- Decision: Preserves restricted operational records owner-locally while using
  public-safe summaries and projections without creating a second authority.
- Evidence: PR #479; merge `93a01eb24dfb94c848a1f937e9e1bdfeea72c74d`.
- Policy adoption: Adopted on canonical history.
- Live activation: No host activation is represented.
- Relationships: Refined separately by GOV-2026-010 and GOV-2026-011; their
  refresh and owner-local location scopes remain distinct.
- Validation: Disclosure, path-authority, and projection checks.
- Owner-local supplement: Required.

## GOV-2026-002 — GitHub disclosure boundary

- Date: 2026-07-28
- Status: Canonical
- Decision class: security_privacy_disclosure
- Authorities: framework/project/github/disclosure-boundary.md; framework/project/github/disclosure-policy.json
- Decision: Establishes artifact classification, a fail-closed outbound gate,
  and the no-secret public-transmission rule.
- Evidence: PR #479; merge `93a01eb24dfb94c848a1f937e9e1bdfeea72c74d`.
- Policy adoption: Adopted on canonical history.
- Live activation: No host activation is represented.
- Relationships: Refined by GOV-2026-011 for owner-local location only;
  disclosure authority remains canonical.
- Validation: Disclosure-gate, public-bundle, and secret-sanitization checks.
- Owner-local supplement: Required.

## GOV-2026-001 — Console information architecture

- Date: 2026-07-28
- Status: Canonical
- Decision class: interface_information_architecture
- Authorities: framework/project/interfaces/project-console/specification.md
- Decision: Establishes the compact six-tab Console architecture and bounded,
  nonauthoritative specialist projections.
- Evidence: PR #479; merge `93a01eb24dfb94c848a1f937e9e1bdfeea72c74d`.
- Policy adoption: Adopted on canonical history.
- Live activation: No host activation is represented.
- Relationships: Refined by GOV-2026-009 only for data-state display.
- Validation: Navigation, bounded-workspace, and frontend interaction checks.
- Owner-local supplement: Not required.
