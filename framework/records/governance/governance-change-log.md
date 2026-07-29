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

## GOV-2026-014 — Owner-local preservation-boundary proposal

- Date: 2026-07-29
- Status: Proposed / unmerged
- Decision class: security_privacy_disclosure
- Authorities: ARRP Private owner directives
- Decision: Records the unresolved proposal to narrow the exceptional
  preservation and policy-change boundary within the owner-local workspace;
  it does not change the current directive.
- Evidence: Reviewed owner-local proposal; no canonical Git decision or exact
  owner approval.
- Policy adoption: Not adopted; exact owner approval of the replacement text remains required.
- Live activation: No directive or runtime change is activated.
- Relationships: Additive; the current owner directive remains controlling.
- Validation: Current-directive preservation, candidate isolation, and
  no-activation checks.
- Owner-local supplement: Required.

## GOV-2026-013 — Governance Change Recording authority

- Date: 2026-07-29
- Status: Proposed / unmerged
- Decision class: governance_documentation
- Authorities: framework/project/workflows/governance-change-recording.md; framework/project/workflows/governance-change-registry.json
- Decision: Proposes this public GOV index and strict provenance workflow; it
  does not create a private record or alter another governing authority.
- Evidence: Current worktree only; no canonical commit or pull request.
- Policy adoption: Not adopted on canonical history.
- Live activation: No live activation applies.
- Relationships: Additive; no recorded supersession or refinement.
- Validation: Registry, heading, parser, Console, and Markdown checks remain
  pending canonical reconciliation.
- Owner-local supplement: Not required.

## GOV-2026-012 — Separate operational and security incident authorities

- Date: 2026-07-29
- Status: Proposed / unmerged
- Decision class: security_privacy_disclosure
- Authorities: framework/project/automation/security-incidents.json; framework/project/automation/incident-relations.json
- Decision: Proposes separate operational and security incident authorities
  with a typed relation only; neither lifecycle is merged.
- Evidence: Current worktree only; no canonical commit or pull request.
- Policy adoption: Not adopted on canonical history.
- Live activation: Not activated; the proposed security authority remains unavailable.
- Relationships: Would refine GOV-2026-004 if adopted; the operational
  authority remains canonical.
- Validation: Incident-authority, relation, privacy, and Console contract
  checks remain pending canonical reconciliation.
- Owner-local supplement: Required.

## GOV-2026-011 — Owner-local runtime authority

- Date: 2026-07-29
- Status: Proposed / unmerged
- Decision class: operations_automation
- Authorities: framework/project/automation/owner-local-runtime.md
- Decision: Proposes a single current-versus-successor runtime, migration,
  cutover, rollback, and retirement authority.
- Evidence: Current worktree only; no canonical commit or pull request.
- Policy adoption: Not adopted on canonical history.
- Live activation: Not activated; existing production posture and pause state
  remain separately governed.
- Relationships: Would refine location aspects of GOV-2026-002, GOV-2026-003,
  GOV-2026-005, and GOV-2026-010 if adopted.
- Validation: Runtime documentation, migration, path-authority, and disclosure
  checks remain pending canonical reconciliation.
- Owner-local supplement: Required.

## GOV-2026-010 — Authenticated owner refresh boundary

- Date: 2026-07-29
- Status: Canonical
- Decision class: security_privacy_disclosure
- Authorities: framework/project/interfaces/project-console.md; scripts/refresh_horizon_review_console.py
- Decision: Separates owner-invoked authenticated refresh from a credential-free
  static Console that cannot initiate refresh.
- Evidence: PRs #485–486; merges
  `10ec1342713e11543377b89de5f5ffc8cf5ddf8d` and
  `572e1db1ebfff49cc26004cced1d0933934fa4c6`.
- Policy adoption: Adopted on canonical history.
- Live activation: No host service is activated by this record.
- Relationships: Refines GOV-2026-003; proposed GOV-2026-011 may later refine
  the owner-local location boundary.
- Validation: Authenticated-refresh, credential-confinement, data-contract,
  and closeout checks.
- Owner-local supplement: Required.

## GOV-2026-009 — Typed classifications and unavailable-state discipline

- Date: 2026-07-28
- Status: Canonical
- Decision class: data_provenance_integrity
- Authorities: framework/project/interfaces/project-console-classifications.json; framework/project/interfaces/project-console.md
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
- Authorities: framework/records/automation/console-development-log.md
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
- Authorities: framework/project/interfaces/project-console-classifications.json; framework/standards/interfaces/standard.md
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
- Relationships: Proposed GOV-2026-011 may refine path location only; the gate
  authority remains canonical.
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
- Relationships: Proposed GOV-2026-012 separates security investigation; the
  operational authority remains canonical.
- Validation: Operational-incident and path-authority checks.
- Owner-local supplement: Required.

## GOV-2026-003 — Owner-local protected operational records

- Date: 2026-07-28
- Status: Canonical
- Decision class: security_privacy_disclosure
- Authorities: framework/project/github/disclosure-boundary.md; framework/PROJECT_STRUCTURE.md
- Decision: Preserves restricted operational records owner-locally while using
  public-safe summaries and projections without creating a second authority.
- Evidence: PR #479; merge `93a01eb24dfb94c848a1f937e9e1bdfeea72c74d`.
- Policy adoption: Adopted on canonical history.
- Live activation: No host activation is represented.
- Relationships: Refined separately by GOV-2026-010; proposed GOV-2026-011 may
  refine the owner-local location boundary.
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
- Relationships: Proposed GOV-2026-011 may refine location only; disclosure
  authority remains canonical.
- Validation: Disclosure-gate, public-bundle, and secret-sanitization checks.
- Owner-local supplement: Required.

## GOV-2026-001 — Console information architecture

- Date: 2026-07-28
- Status: Canonical
- Decision class: interface_information_architecture
- Authorities: framework/project/interfaces/project-console.md
- Decision: Establishes the compact six-tab Console architecture and bounded,
  nonauthoritative specialist projections.
- Evidence: PR #479; merge `93a01eb24dfb94c848a1f937e9e1bdfeea72c74d`.
- Policy adoption: Adopted on canonical history.
- Live activation: No host activation is represented.
- Relationships: Refined by GOV-2026-009 only for data-state display.
- Validation: Navigation, bounded-workspace, and frontend interaction checks.
- Owner-local supplement: Not required.
