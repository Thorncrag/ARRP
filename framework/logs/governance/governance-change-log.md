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

## GOV-2026-022 — Component Registry executable-selection correction

- Date: 2026-08-03
- Status: Canonical
- Decision class: governance_documentation
- Authorities: framework/component-registry.json;
  framework/component-registry.schema.json; scripts/component_registry.py;
  scripts/build_elim_context.py; scripts/arrp_nightly.py;
  scripts/finalize_component_registry_activation.py;
  framework/project/automation/owner-local-runtime.md
- Decision: Adopts advancing the schema-version-4 Component Registry
  to revision 5 while preserving authority generation 4 and the existing
  five-file receipt-binding family. The correction keeps the Registry and its
  live-authority view nonexecutable while allowing the canonical router to
  produce a separately executable primary-profile work selection only after
  exact live-authority, currentness, receipt, and predecessor-exclusion checks.
  Context packets remain bound to the original nonexecutable Registry view,
  and their manifest paths, hash policies, digests, and inclusion reasons must
  match the routed module contents. The component inventory, routing catalog,
  schema family, authority generation, operational component executability,
  and revision-4 historical evidence do not change.
- Evidence: Benjamin's exact revision-5 authorization dated 2026-08-03;
  candidate Registry SHA-256
  `b189cbe0c934a38ba5671f1f43338bae2423b9ab0972bfd5d7aad65c9149adc1`;
  the mapped Registry, activation, routing, nightly, coordinator, consistency,
  and documentation validation seams; exact implementation head
  `9a7178a3569d9f8c2b69183d096684faf3e556b3`, PR #518, and merge
  `61d2a6614bc9fc41ceaf8d21943d4fdc40e2331c`. The implementation merge
  parents are exactly the prior canonical main and the approved head, its tree
  equals the approved-head tree, and the Registry plus all five receipt-bound
  interpreter files remain byte-identical. Governance-only closeout anchor
  `67442ccc794e4635a0fbe26c85ecd99017b0ad64` and PR #519 record the
  canonical evidence. The exact final PR #519 head is the final commit
  containing this record and is separately approved and read back before
  merge; its merge and the later activation receipt remain pending.
- Policy adoption: Adopted on canonical history through exact approved PR #518
  head `9a7178a3569d9f8c2b69183d096684faf3e556b3` and merge
  `61d2a6614bc9fc41ceaf8d21943d4fdc40e2331c`; governance-only closeout records
  exact provenance and does not establish live owner-local authority.
- Live activation: Not active. Automation remains Paused. A new live-authority
  claim requires the separately governed, digest-addressed owner-local receipt
  binding the exact revision-5 Registry and existing five interpreter paths.
- Relationships: Refines GOV-2026-021 without superseding or modifying its
  exact historical Markdown or registry entry.
- Validation: 778 mapped Python tests pass with 15 intentional skips; 75
  browser tests pass; focused Registry, readiness, Console, and context tests
  pass; exact public Console regeneration emits the proposed/non-current
  revision-5 posture; the GOV-2026-021 raw Markdown block remains exactly
  8,696 bytes with SHA-256
  `9de8307f3a7a1ea5af53c33fee3bb6791e9e99e7b728e3a91eda552bec97eda9`
  and its parsed public-entry digest remains
  `sha256:2fa924d23b66488c84b5bb4c393fef100b6583ff45d0c158b273d1dbc87a092c`.
  PR #518 required checks passed, its exact head was owner-approved, and its
  merge readback and first byte-continuity gate passed. Closeout checks,
  exact-head approval, merge readback, and later live-authority verification
  remain pending; no unresolved finding is silently accepted. Score, rubric,
  rebaseline, and Runs effect are None.
- Owner-local supplement: Required.

## GOV-2026-021 — Component Registry semantic-minimal authority

- Date: 2026-08-02
- Status: Canonical
- Decision class: governance_documentation
- Authorities: framework/component-registry.json;
  framework/component-registry.schema.json; scripts/component_registry.py;
  scripts/arrp_context.py; scripts/run_coordinator.py;
  scripts/finalize_component_registry_activation.py;
  framework/project/automation/owner-local-runtime.md;
  framework/project/interfaces/project-console/specification.md
- Decision: Adopts schema and revision 4 as the exact semantic-minimal
  Component Registry. The Registry remains the sole component, routing, and
  CODEOWNERS authority; `.github/CODEOWNERS` and the Console snapshot are
  generated nonauthoritative representations. Exact-only version-4 loaders,
  a schema-version-2 same-family readback, and five receipt-bound interpreter
  blobs replace live compatibility with earlier Registry formats.
- Evidence: Owner-authorized design `CR-SM-2026-08-02` revision R7; preserved
  baseline commit `07fe5f357f2604f25d6393e6f6fd14c1ab337165`; exact PR1 head
  `eb569526c0c5281816485683af3bf5fb7a91c662`, PR #511, and merge
  `15405bb3d4d709678a68c6aacadc1d7d02c8c5c5`; PR2 anchor commit
  `8b9f56a92eb27233c62ad881589cf9760460ef22` and PR #512; exact 11-key,
  105-component, 87-term, 59-scope, 64-rule, 16-relationship, and
  three-exemption inventory; normalized pre/post field parity; exact helper
  coverage transition; byte-reproducible Console generation; and generated
  CODEOWNERS equality. The exact final PR2 head is the final commit containing
  this record and is separately approved and read back before merge. Its merge
  evidence is established by canonical-main readback and the separately
  governed owner-local activation receipt after merge.
  Consumer closure map:
  `canonical_authority` — `framework/component-registry.json` and
    `framework/component-registry.schema.json`; validated by
    `tests/framework/test_component_registry.py` and the schema-negative
    fixtures.
  `generated_output` — `.github/CODEOWNERS` and
    `framework/project/interfaces/project-console/data/component-registry.js`;
    validated by exact regeneration, protected-path comparison,
    `tests/framework/test_component_registry.py`, and
    `tests/test_console_data_contracts.py`.
  `active_v4_interpreter_receipt_bound` — `scripts/component_registry.py`,
    `scripts/arrp_context.py`, `scripts/run_coordinator.py`, and
    `scripts/finalize_component_registry_activation.py`; validated by the
    component, routing-closure, coordinator, finalizer, readiness, and
    readback tests.
  `active_v4_producer_or_operational_consumer` —
    `scripts/build_project_console.py`, `scripts/arrp_nightly.py`,
    `scripts/audit_project_consistency.py`,
    `scripts/record_review_epoch.py`, and
    `scripts/refresh_project_console.py`; validated respectively by Console
    data contracts plus frontend tests, nightly tests, consistency tests,
    review-epoch tests, and authenticated-refresh tests.
  `current_console_ui_documentation_or_metadata` —
    `framework/project/interfaces/project-console/README.md`,
    `framework/project/interfaces/project-console/app.js`,
    `framework/project/interfaces/project-console/component-registry.js`,
    `framework/project/interfaces/project-console/configuration/classifications.json`,
    `framework/project/interfaces/project-console/project-console.html`,
    `framework/project/interfaces/project-console/specification.md`, and
    `framework/project/interfaces/project-console/styles.css`; validated by
    `tests/test_console_data_contracts.py` and
    `tests/project-console/frontend.test.mjs` across all twelve modes.
  `current_guidance_dependency_or_configured_entrypoint` —
    `.github/workflows/arrp-validation.yml`, `framework/FRAMEWORK.md`,
    `framework/AGENT_OPERATING_RULES.md`, `framework/project/README.md`,
    `framework/project/automation/agent-policy.md`,
    `framework/project/automation/owner-local-runtime.md`,
    `framework/project/automation/runbooks/project-integrity-bot.md`,
    `framework/project/github/disclosure-policy.json`,
    `framework/project/github/workflow.md`,
    `framework/project/publication/print-assembly.md`,
    `framework/project/workflows/governance-change-recording.md`,
    `framework/project/workflows/navigation-sync.md`,
    `framework/project/workflows/project-update.md`,
    `framework/standards/content/navigation-and-indexes.md`,
    `framework/standards/interfaces/standard.md`, and
    `framework/standards/sources/source-records.md`; these are dependency,
    authority-link, disclosure-family, or exact CLI-entrypoint references,
    validated by the v4 CLI, runtime-documentation, and project-consistency
    seams without another Registry parser.
  `unchanged_generic_or_opaque_consumer` —
    `scripts/build_elim_context.py` and `scripts/build_owner_console.py`;
    validated by `tests/test_elim_context.py`,
    `tests/test_owner_console.py`, and
    `tests/test_incident_authority_contracts.py` without source changes.
  `historical_only_or_explicit_rejection` —
    `scripts/apply_component_registry_stage3_migration.py`, archived Registry
    authorities, preserved receipts and proposals, and prior-version fixture
    methods; validated by the helper blob and coverage comparison, active-loader
    no-predecessor tests, and exact rejection of missing, Boolean, malformed,
    prior, and future versions.
  `direct_test_or_fixture_reference` —
    `tests/framework/test_component_registry.py`,
    `tests/framework/test_component_registry_activation_finalizer.py`,
    `tests/framework/test_component_registry_activation_readback.py`,
    `tests/framework/test_component_registry_activation_readiness.py`,
    `tests/framework/test_component_registry_stage1_acceptance.py`,
    `tests/framework/test_context_routing_rule_closure.py`,
    `tests/framework/test_context_routing_semantics.py`,
    `tests/project-console/frontend.test.mjs`,
    `tests/test_arrp_nightly.py`,
    `tests/test_console_authenticated_refresh.py`,
    `tests/test_console_data_contracts.py`,
    `tests/test_elim_context.py`, `tests/test_elim_execution.py`,
    `tests/test_github_disclosure_gate.py`, `tests/test_horizon_intake.py`,
    `tests/test_incident_authority_contracts.py`,
    `tests/test_owner_console.py`, `tests/test_project_consistency.py`,
    `tests/test_review_epoch.py`, `tests/test_run_coordinator.py`, and
    `tests/test_runtime_authority_documentation.py`; each is either a mapped
    v4 assertion, unchanged generic seam, unrelated disclosure or intake
    fixture, or explicit historical rejection fixture and is not a production
    parser.
- Policy adoption: Adopted on canonical history through PR #511 and PR #512.
- Live activation: Canonical policy adoption does not itself activate
  execution. The Registry is nonexecutable and automation remains Paused; live
  readback is established only by the separately governed schema-version-2
  owner-local receipt.
- Relationships: Supersedes GOV-2026-020 one-way. GOV-2026-020 remains
  byte-preserved as historical provenance and does not supersede or refine
  GOV-2026-021.
- Validation: Mapped Python, browser, deterministic generation, normalized
  parity, CODEOWNERS preservation, helper coverage, exact-version, and
  continuity-gate checks pass. Historical Change Audit Log SHA-256
  `8cd8dfec677d5edfa354431becc6024544f0d23fec090cfba31e1660b2b7eb6b`,
  GOV-2026-020 raw JSON SHA-256
  `337f9476be11c3fbcbe4d43fd2248cf51b5effd6ece24a12c167ce9ba4528b85`,
  and GOV-2026-020 raw Markdown SHA-256
  `0dee6703d2c7b3a7e2bff9171e7b27df92e8ede7358a4d06e5cea90e4e0ac5ca`
  are the exact PR1 merge baselines. Project-wide Change Audit — affected
  scope: Registry, routing, generated CODEOWNERS, all twelve Console modes,
  active consumers, governance, disclosure, continuity, and Paused activation;
  findings and corrections: the approved semantic subtraction, exact-version
  migration, protected-path preservation, Console parity, executable-fixture
  correction, and historical-log authority correction are incorporated in
  their owning PR1 files and tests; score, rubric, rebaseline, and Runs effect:
  None; owning evidence: the consumer closure map above, exact Git history, and
  the mapped validation seams; unresolved findings: None. On the exact final
  PR2 candidate, the diff remains limited to these two governance files and
  the three named preservation hashes remain unchanged. Canonical-main merge
  readback and the owner-local activation receipt follow only after exact-head
  approval and merge.
- Owner-local supplement: Required.

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
