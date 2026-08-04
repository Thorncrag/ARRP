import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const testDirectory = path.dirname(fileURLToPath(import.meta.url));
const consoleDirectory = path.resolve(
  testDirectory,
  "../../framework/project/interfaces/project-console",
);
const appPath = path.join(consoleDirectory, "app.js");
const componentRegistryPath = path.join(consoleDirectory, "component-registry.js");
const componentRegistryDataPath = path.join(
  consoleDirectory,
  "data/component-registry.js",
);
const entrypointPath = path.join(consoleDirectory, "project-console.html");
const localRequire = createRequire(
  path.join(consoleDirectory, "frontend-test-loader.js"),
);
const testGenerationId = "project-console-test";
const testSourceRevision = "a".repeat(40);
const testVersionId = `${testGenerationId}-20260729T120000000000Z`;
const testOwnerPath = "/owner-console-fixture/review-copy/project-console.html";
const testStagedAt = "2026-07-29T12:00:00.000000Z";

function v4ComponentRegistryFixture() {
  const source = fs.readFileSync(componentRegistryDataPath, "utf8");
  const assignmentMarker = "Object.assign(window.ARRP_HORIZON_REVIEW_DATA,";
  const payloadStart = source.indexOf(assignmentMarker);
  assert.notEqual(payloadStart, -1, "generated registry assignment marker must exist");
  assert.equal(source.trimEnd().endsWith(");"), true, "generated registry assignment must terminate");
  const payload = JSON.parse(
    source.slice(payloadStart + assignmentMarker.length, source.trimEnd().length - 2),
  );
  return structuredClone(payload.component_registry);
}

function ownerProjectionEntry(feedId, filename, marker, availability = "current", complete = true) {
  return {
    feed_id: feedId,
    relative_path: `data/${filename}`,
    source_sha256: `sha256:${marker.repeat(64)}`,
    availability,
    complete
  };
}

function ownerProjectionWrapper(feedId, payload, binding) {
  const projection = binding.projections[feedId];
  return {
    owner_console_envelope: {
      schema_version: 1,
      feed_id: feedId,
      generation_id: binding.generation_id,
      source_revision: binding.source_revision,
      source_sha256: projection.source_sha256,
      availability: projection.availability,
      complete: projection.complete,
      staged_at: binding.staged_at
    },
    payload
  };
}

function privateOperationsFixture() {
  return {
    schema_version: 4,
    availability: "current",
    generated_at: "2026-07-29T12:00:00Z",
    catalog_generation_id: testGenerationId,
    source_revision: testSourceRevision,
    governance_change_supplements: {
      schema_version: 1,
      availability: "unavailable",
      complete: false,
      checked_at: "2026-07-29T12:00:00Z",
      source_revision: testSourceRevision,
      public_log_sha256: `sha256:${"f".repeat(64)}`,
      items: [],
      reason_code: "owner-local-governance-supplements-unavailable"
    },
    agent_registry: [],
    project_logs: [],
    integrity: {},
    run_chain: {},
    action_snapshot: {
      schema_version: 1,
      generation_id: "action-snapshot-test",
      generated_at: "2026-07-29T12:00:00Z",
      availability: "partial",
      complete: false,
      items: [],
      counts: { human: null, oversight: null, all_open: null },
      known_counts: { human: 0, oversight: 0, all_open: 0 },
      sources: {},
      predicates: {}
    },
    queue_directory: {
      schema_version: 1,
      generation_id: "queue-directory-test",
      generated_at: "2026-07-29T12:00:00Z",
      availability: "partial",
      complete: false,
      queues: [{
        queue_id: "human_actions",
        availability: "unavailable",
        complete: false,
        count: null
      }]
    },
    operational_incidents: {
      schema_version: 1,
      availability: "current",
      complete: true,
      checked_at: "2026-07-29T12:00:00Z",
      count: 0,
      unresolved_count: 0,
      items: [],
      impact_state: "green",
      active_links: {}
    },
    security_incidents: {
      schema_version: 1,
      authority: "owner-local-security-incidents",
      availability: "unavailable",
      complete: false,
      checked_at: "2026-07-29T12:00:00Z",
      count: null,
      unresolved_count: null,
      items: [],
      reason_code: "missing-security-incident-feed"
    },
    incident_relations: {
      schema_version: 1,
      authority: "owner-local-incident-relations",
      availability: "unavailable",
      complete: false,
      checked_at: null,
      active_relations: [],
      relations: [],
      by_operational_incident: {},
      by_security_incident: {},
      reason_code: "incident-relations-missing"
    },
    transaction_recovery: {
      schema_version: 1,
      availability: "unavailable",
      complete: false,
      generated_at: null,
      items: [],
      reason_code: "owner-local-transaction-recovery-projection-required"
    },
    privacy: "Owner-only local projection."
  };
}

function codexUsageFixture() {
  return {
    schema_version: 2,
    projection_id: "codex-usage",
    producer_id: "owner-local-codex-usage-sampler",
    sampler_cadence_seconds: 1800,
    generated_at: null,
    trustworthy_through: null,
    availability: "unavailable",
    completeness: "incomplete",
    reason_code: "owner_local_projection_required",
    current_through: null,
    current: null,
    history: [],
    reset_windows: [],
    anomalies: [],
    estimates: {
      available: false,
      budget_available: false,
      budget_reason_code: "projection_unavailable",
      burn_rate_available: false,
      burn_rate_reason_code: "projection_unavailable",
      coverage_hours: null,
      sample_count: null,
      average_percent_per_day: null,
      projected_exhaustion_at: null,
      remaining_percent_per_day_budget: null,
      confidence: null
    }
  };
}

function availableCodexUsageFixture() {
  return {
    ...codexUsageFixture(),
    generated_at: "2026-07-29T20:20:00Z",
    trustworthy_through: "2026-07-29T20:47:00Z",
    availability: "current",
    completeness: "complete",
    reason_code: null,
    current_through: "2026-07-29T20:17:00Z",
    current: {
      observed_at: "2026-07-29T20:17:00Z",
      plan_type: "pro",
      used_percent: 28,
      remaining_percent: 72,
      window_minutes: 10080,
      resets_at: 1785908741,
      reset_identity: "10080:29765145"
    },
    estimates: {
      available: true,
      budget_available: true,
      budget_reason_code: null,
      burn_rate_available: false,
      burn_rate_reason_code: "insufficient_observation_coverage",
      coverage_hours: 0,
      sample_count: 1,
      average_percent_per_day: null,
      projected_exhaustion_at: null,
      remaining_percent_per_day_budget: 10.1,
      confidence: "unavailable"
    }
  };
}

function componentRegistryFixture() {
  const pending = (reason = "Producer-declared pending value.") => ({
    state: "pending",
    reason
  });
  const known = (value) => ({ state: "known", value });
  const unavailable = (reason = "Producer-declared unavailable value.") => ({
    state: "unavailable",
    reason
  });
  const moduleRecord = {
    id: "framework_kernel",
    path: "framework/FRAMEWORK.md",
    governing: true,
    hash_policy: "pinned",
    sha256: "2".repeat(64),
    authority_role: "governing_authority",
    authority_scope: known("Project governance kernel."),
    authority_exclusions: pending("No normalized exclusions are registered."),
    dependencies: [],
    inclusion_reasons: ["required floor"]
  };
  const routingRuleIds = {
    invariants: ["ctxr.inv.router_preserves_source_authority", "ctxr.inv.required_floor_is_minimum", "ctxr.inv.additive_union", "ctxr.inv.dependencies_are_directional_minimums", "ctxr.inv.dependency_graph_is_acyclic", "ctxr.inv.stable_document_identity_is_path_independent", "ctxr.inv.bounded_context_never_omits_material_authority"],
    selection: ["ctxr.sel.primary_profile", "ctxr.sel.required_floor_order", "ctxr.sel.profile_starting_set", "ctxr.sel.all_implicated_capabilities", "ctxr.sel.profile_never_excludes_capability", "ctxr.sel.capability_addition_requires_no_new_profile", "ctxr.sel.profile_documents_and_exact_sections", "ctxr.sel.complete_dependency_closure", "ctxr.sel.task_specific_canonical_material", "ctxr.sel.source_projection_requires_canonical_readback", "ctxr.sel.dynamic_trigger_set", "ctxr.sel.expansion_precedes_dependent_action", "ctxr.sel.multi_agent_before_delegation", "ctxr.sel.governance_recording_plus_change_audit", "ctxr.sel.interactive_route_is_minimum_not_ceiling", "ctxr.sel.automated_expansion_allowlist", "ctxr.sel.deterministic_bot_structured_inputs"],
    validation: ["ctxr.val.registry_before_selection", "ctxr.val.integration_pinned_digest_exact", "ctxr.val.runtime_digest_at_packet_build", "ctxr.val.expansion_provenance_preserved", "ctxr.val.exact_section_unique", "ctxr.val.packet_manifest_bound", "ctxr.val.authorized_digest_update_atomic", "ctxr.val.registry_digest_external", "ctxr.val.new_authoritative_module_admission", "ctxr.val.id_rename_change_audit"],
    failure_rules: ["ctxr.fail.unknown_or_missing_selection", "ctxr.fail.pinned_digest_absent_or_stale", "ctxr.fail.runtime_digest_unreadable", "ctxr.fail.dependency_cycle", "ctxr.fail.generated_or_excluded_as_authority", "ctxr.fail.section_identity_invalid", "ctxr.fail.section_budget_exceeded", "ctxr.fail.packet_budget_exceeded", "ctxr.fail.unresolved_material_governing_gap", "ctxr.fail.safe_failure_disposition"],
    currentness: ["ctxr.cur.stable_governing_is_pinned", "ctxr.cur.mutable_handoff_is_runtime_hashed", "ctxr.cur.checkpoint_update_needs_no_registry_edit", "ctxr.cur.generated_rebuildables_excluded", "ctxr.cur.records_excluded_except_handoff", "ctxr.cur.runtime_nongoverning_excluded_from_review_boundary"],
    budgets: ["ctxr.budget.profile_max_is_fail_closed_ceiling", "ctxr.budget.ceiling_change_does_not_change_membership", "ctxr.budget.section_and_packet_limits_are_independent", "ctxr.budget.no_mandatory_trimming"],
    comprehensive_review: ["ctxr.review.select_all_active_governing", "ctxr.review.periodic_epoch_required", "ctxr.review.boundary_exact", "ctxr.review.any_valid_boundary_difference_due", "ctxr.review.invalid_drift_is_integrity_failure", "ctxr.review.completion_fields_exact", "ctxr.review.recorder_requires_exact_current_boundary", "ctxr.review.unresolved_findings_carry_forward", "ctxr.review.next_epoch_uses_delta_and_carry_forward", "ctxr.review.efficiency_never_limits_scope_or_lookback"]
  };
  const ruleCounts = Object.fromEntries(
    Object.entries(routingRuleIds).map(([namespace, ids]) => [namespace, ids.length])
  );
  const routingRules = Object.entries(routingRuleIds).flatMap(([namespace, ids]) =>
    ids.map((rule_id) => ({
      namespace,
      rule_id,
      rule_version: 1,
      status: "active",
      predicate_type: rule_id,
      parameters: {},
      label: `Producer label for ${rule_id}`,
      rendered_text: `Producer-rendered description for ${rule_id}.`,
      ...(namespace === "failure_rules" ? { failure_code: `CTXR_${rule_id.split(".").at(-1).toUpperCase()}` } : {}),
      source_provenance: {
        source_document_id: "context_routing",
        source_sha256: "5".repeat(64),
        source_heading: "Governing Context Routing",
        clause_key: rule_id
      },
      verification_ids: [`test.${rule_id}`],
      console_route: `automation:component-registry:routing?rule=${encodeURIComponent(rule_id)}`
    }))
  );
  return {
    schema_version: 1,
    projection_id: "component-registry-console",
    producer_id: "project-console-builder",
    generated_at: "2026-07-29T12:00:00Z",
    availability: "current",
    complete: true,
    reason_code: null,
    routes: {
      documents: "automation:component-registry:documents",
      directories: "automation:component-registry:directories",
      routing: "automation:component-registry:routing",
      relationships: "automation:component-registry:relationships",
      terminology: "automation:component-registry:terminology"
    },
    defaults: {
      mode: "documents",
      document: "framework_kernel",
      directory: "framework",
      routing: "profile:compact",
      relationship: "registry_validated_by_schema"
    },
    registry: {
      registry_id: "arrp_component_registry",
      registry_revision: 1,
      registry_status: "candidate",
      approval: pending("Activation approval is pending."),
      configuration_validation: known(
        "Candidate predecessor parity validated"
      ),
      live_activation: pending(
        "The tracked candidate has not entered live owner activation."
      ),
      validation_mode: "candidate_validation_only",
      authoritative: false,
      executable: false,
      live_activation_verified: false,
      predecessor_route_consulted: true,
      registry_sha256: "1".repeat(64),
      repository_revision: testSourceRevision,
      source_binding_sha256: known("2".repeat(64))
    },
    deferred: {
      display_state: "Classification pending — enforcement not active",
      reason: "Artifact classification and lifecycle mapping require complete human review.",
      activation_requirement: "A distinct Governance Change and explicit human approval are required.",
      namespaces: [
        "artifact_classes",
        "artifact_families",
        "artifact_lifecycles"
      ].map((namespace) => ({
        namespace,
        schema_version: 1,
        activation_state: "deferred_pending_human_classification",
        complete: false,
        enforced: false,
        entry_count: 0
      }))
    },
    documents: [{
      document_id: "framework_kernel",
      official_reference_name: known("ARRP Framework"),
      document_class: known("routed_governing_document"),
      revision: known(1),
      current_status: known("current_routed_source"),
      effective_date: pending(),
      approval_date: pending(),
      approval_method: pending(),
      governance_change_id: pending(),
      purpose_scope: known("Project governance kernel."),
      authority_role: "governing_authority",
      authority_exclusions: pending(),
      canonical_path: "framework/FRAMEWORK.md",
      owner: "@Thorncrag",
      review_policy: "owner_review_required",
      disclosure_class: "public_by_design",
      creation_provenance: pending(),
      governance_revision: 1,
      producer: "existing_repository_source",
      authorized_writers: ["@Thorncrag"],
      representations: ["component_registry_console_documents"],
      dependencies: [],
      consumers: ["codex_bootstrap"],
      digest_policy: "pinned",
      sha256: "2".repeat(64),
      console_route: "operations:component-registry:documents?document=framework_kernel",
      retention_posture: "current",
      history: unavailable("Normalized history is not registered.")
    }, {
      document_id: "context_routing",
      official_reference_name: known("Context Routing"),
      document_class: known("routed_governing_document"),
      revision: known(1),
      current_status: known("current_routed_source"),
      effective_date: pending(), approval_date: pending(), approval_method: pending(), governance_change_id: pending(),
      purpose_scope: known("Routing requirements."), authority_role: "governing_authority", authority_exclusions: pending(),
      canonical_path: "framework/CONTEXT_ROUTING.md", owner: "@Thorncrag", review_policy: "owner_review_required",
      disclosure_class: "public_by_design", creation_provenance: pending(), governance_revision: 1,
      producer: "existing_repository_source", authorized_writers: ["@Thorncrag"],
      representations: ["component_registry_console_documents"], dependencies: [], consumers: ["codex_bootstrap"],
      digest_policy: "pinned", sha256: "5".repeat(64),
      console_route: "operations:component-registry:documents?document=context_routing",
      retention_posture: "current", history: unavailable("Normalized history is not registered.")
    }],
    directories: [{
      scope_id: "framework",
      display_name: "Framework",
      path_pattern: "framework/**",
      match_kind: "tree",
      specificity_rank: 1,
      parameter_bindings: {},
      owning_scope_selection_rule: "highest_specificity_unique",
      ancestor_scope_ids: [],
      placement_question: "Is this a framework authority or record?",
      include_when: ["Tracked framework authorities and records."],
      exclude_when: ["Owner-local material."],
      primary_authority: "COMPONENT-REGISTRY",
      disclosure_boundary: "public_by_design",
      lifecycle_posture: "current",
      authorized_creators: ["@Thorncrag"],
      precedence: "Most-specific scope wins; ties fail closed.",
      fallback: "human_review",
      console_route: "automation:component-registry:directories?directory=framework",
      permitted_artifact_classes: unavailable(
        "Artifact classification requires complete human review."
      ),
      current_artifact_count: known(12)
    }],
    relationships: [{
      relationship_id: "registry_validated_by_schema",
      relationship_type: "validated_by",
      from: { kind: "document", id: "COMPONENT-REGISTRY" },
      to: { kind: "document", id: "component_registry_schema" },
      authority_boundary: "Schema validates structure but does not approve values or activation.",
      console_route: "automation:component-registry:relationships?relationship=registry_validated_by_schema"
    }],
    routing: {
      schema_version: 2,
      rule_catalog_version: 1,
      activation_state: "candidate_import",
      complete: true,
      authoritative: false,
      source_import: {
        path: "framework/project/automation/context-routes.json",
        sha256: "3".repeat(64),
        schema_version: 2,
        import_semantics: "exact_validated_snapshot"
      },
      predecessor_provenance: {
        state: "not_applicable",
        reason: "Candidate routing uses predecessor parity evidence."
      },
      readable_representation: {
        state: "not_applicable",
        reason: "The active readable representation is not adopted."
      },
      expected_counts: {
        documents: 2,
        governing_documents: 2,
        capabilities: 1,
        profiles: 1,
        required_modules: 1,
        generated_path_exclusions: 1
      },
      parity_policy: "exact_identity_membership_dependency_section_and_digest_parity",
      required_modules: ["framework_kernel"],
      generated_path_exclusions: ["framework/project/interfaces/project-console/data"],
      documents: [{
        document_id: "framework_kernel",
        path: "framework/FRAMEWORK.md",
        governing: true,
        hash_policy: "pinned",
        sha256: "2".repeat(64),
        requires: []
      }, {
        document_id: "context_routing",
        path: "framework/CONTEXT_ROUTING.md",
        governing: true,
        hash_policy: "pinned",
        sha256: "5".repeat(64),
        requires: []
      }],
      capabilities: [{
        capability_id: "governance",
        document_ids: ["framework_kernel"]
      }],
      profiles: [{
        profile_id: "compact",
        max_bytes: 200000,
        modules: ["framework_kernel"],
        capabilities: [],
        include_all_governing: false,
        sections: []
      }],
      selections: [{
        selection_id: "profile:compact",
        selection_kind: "profile",
        executable: false,
        authoritative: false,
        live_activation_verified: false,
        profile: "compact",
        capabilities: [],
        max_bytes: 200000,
        sections: [],
        modules: [moduleRecord],
        console_route: "automation:component-registry:routing?selection=profile%3Acompact"
      }, {
        selection_id: "capability:governance",
        selection_kind: "capability",
        executable: false,
        authoritative: false,
        live_activation_verified: false,
        profile: null,
        capabilities: ["governance"],
        max_bytes: null,
        sections: [],
        modules: [moduleRecord],
        console_route: "automation:component-registry:routing?selection=capability%3Agovernance"
      }],
      rule_namespaces: Object.keys(routingRuleIds),
      rule_counts: ruleCounts,
      rules: routingRules,
      validation: {
        valid: true,
        source_sha256: "3".repeat(64),
        registry_route_sha256: "4".repeat(64),
        counts: {
          documents: 2,
          governing_documents: 2,
          capabilities: 1,
          profiles: 1,
          required_modules: 1,
          generated_path_exclusions: 1
        },
        differences: [],
        document_ids_equal: true,
        profile_ids_equal: true,
        capability_ids_equal: true
      }
    },
    activation_readiness: {
      available: true,
      complete: true,
      activation_state: "candidate_complete",
      authoritative: false,
      executable: false,
      registry_revision: 1,
      registry_sha256: "1".repeat(64),
      current_candidate_counts: {
        documents: 88,
        governing_documents: 87,
        capabilities: 19,
        profiles: 8,
        required_modules: 3,
        generated_path_exclusions: 9,
        rules: 64
      },
      simulated_active_counts: {
        documents: 85,
        governing_documents: 84,
        capabilities: 19,
        profiles: 8,
        required_modules: 3,
        generated_path_exclusions: 9,
        rules: 64
      },
      requirement_count: 77,
      exception_count: 0,
      stage_boundaries: {
        artifact_classes: "deferred_by_approved_stage_boundary",
        artifact_families: "deferred_by_approved_stage_boundary",
        artifact_lifecycles: "deferred_by_approved_stage_boundary",
        terminology: "candidate_unpopulated",
        repository_reference_mutation: "separately_gated"
      },
      activation_decision: "pending_human_activation"
    },
    terminology: {
      available: false,
      complete: false,
      activation_state: "candidate_unpopulated",
      reason: "Canonical terminology requires separate approval.",
      entries: [],
      console_route: "automation:component-registry:terminology"
    }
  };
}

function activeComponentRegistryFixture() {
  const snapshot = structuredClone(componentRegistryFixture());
  const notApplicable = (reason) => ({
    state: "not_applicable",
    reason
  });
  snapshot.registry = {
    ...snapshot.registry,
    registry_status: "active",
    approval: {
      state: "known",
      value: "Tracked activation configuration approved"
    },
    configuration_validation: {
      state: "known",
      value: "Tracked active configuration validated"
    },
    live_activation: {
      state: "unknown",
      reason: "Live owner activation is not evaluated by this projection."
    },
    validation_mode: "active_configuration_validation_only",
    authoritative: false,
    executable: false,
    live_activation_verified: false,
    predecessor_route_consulted: false,
    source_binding_sha256: notApplicable(
      "Predecessor source binding is not active configuration authority."
    )
  };
  snapshot.activation_readiness = {
    ...snapshot.activation_readiness,
    activation_state: "active",
    activation_decision:
      "tracked_active_configuration_live_readback_separate"
  };
  snapshot.documents = snapshot.documents.filter((record) =>
    record.document_id !== "context_routing");
  snapshot.routing = {
    ...snapshot.routing,
    activation_state: "active",
    authoritative: false,
    source_import: notApplicable(
      "Predecessor routing evidence is not consulted after tracked activation."
    ),
    predecessor_provenance: {
      state: "known",
      value: "Archived predecessor provenance retained as nonauthoritative history."
    },
    readable_representation: {
      state: "known",
      representation_id: "human_readable_context_routing",
      source_registry_revision: snapshot.registry.registry_revision,
      authority_effect: "none",
      executable: false
    },
    expected_counts: {
      ...snapshot.routing.expected_counts,
      documents: 1,
      governing_documents: 1
    },
    parity_policy: notApplicable(
      "Predecessor routing evidence is not consulted after tracked activation."
    ),
    documents: snapshot.routing.documents.filter((record) =>
      record.document_id !== "context_routing"),
    validation: notApplicable(
      "Predecessor routing evidence is not consulted after tracked activation."
    ),
    rules: snapshot.routing.rules.map((record) => ({
      ...record,
      source_provenance: {
        source_document_id: "COMPONENT-REGISTRY",
        source_sha256: snapshot.registry.registry_sha256,
        source_heading: "Embedded context routing rule catalog",
        clause_key: record.rule_id
      }
    }))
  };
  return snapshot;
}

function stage2ComponentRegistryFixture() {
  const component = {
    stable_id: "framework_kernel",
    display_name: "Framework kernel",
    classification: {
      component_class: "document",
      component_type: "framework",
      roles: [],
      capabilities: []
    },
    canonical_source: {
      locator: { kind: "repository_path", value: "framework/FRAMEWORK.md" },
      source_binding: {
        binding_basis: "content_digest",
        applicability: "current",
        verification_methods: ["pinned_comparison"],
        sha256: "1".repeat(64),
        evidence_ref: "stage2_migration_from_stage1"
      }
    },
    owner: "@Thorncrag",
    information_handling: {
      information_classification: "public",
      disclosure_rule: "public_safe",
      disclosure_boundary: "repository"
    },
    retention: {
      bases: ["operational_need"],
      change_mode: "maintained",
      custody: "repository",
      review_condition: "material change",
      retirement_condition: "approved successor"
    },
    supporting_artifacts: [],
    operational_status: null,
    record_refs: {
      lifecycle_assignments: ["lifecycle_framework_kernel"],
      authority_assignments: ["authority_framework_kernel"],
      relationships: ["framework_validated_by_test"],
      migrations: [],
      provenance_events: ["created_framework_kernel"]
    },
    lifecycle_records: [{
      assignment_id: "lifecycle_framework_kernel",
      component_id: "framework_kernel",
      current_state: "adopted",
      effective_date: "2026-07-31",
      history: []
    }],
    authority_records: [{
      assignment_id: "authority_framework_kernel",
      component_id: "framework_kernel",
      authoritative: true
    }],
    relationship_records: [],
    migration_records: [],
    provenance_records: [{ event_id: "created_framework_kernel" }],
    console_route: "automation:component-registry:components?component=framework_kernel"
  };
  const terms = Array.from({ length: 69 }, (_, index) => ({
    term_id: index === 0 ? "namespace" : `term_${index + 1}`,
    label: index === 0 ? "Namespace" : `Term ${index + 1}`,
    definition: index === 0
      ? "A named domain for identifiers."
      : `Approved definition ${index + 1}.`,
    console_route: `automation:component-registry:terminology?term=${index === 0 ? "namespace" : `term_${index + 1}`}`
  }));
  return {
    schema_version: 2,
    projection_id: "component-registry-console",
    producer_id: "project-console-builder",
    generated_at: "2026-07-31T20:00:00Z",
    availability: "current",
    complete: true,
    reason_code: null,
    routes: Object.fromEntries([
      "components", "classes", "types", "lifecycles", "authority", "relationships",
      "coverage", "directories", "exemptions", "unresolved", "routing", "codeowners", "terminology"
    ].map((mode) => [mode, `automation:component-registry:${mode}`])),
    defaults: {
      mode: "components",
      component: "framework_kernel",
      class: "document",
      type: "document:framework",
      lifecycle: "lifecycle_framework_kernel",
      authority: "authority_framework_kernel",
      relationship: "framework_validated_by_test",
      coverage: "framework",
      routing: "profile:compact",
      codeowners: "component:framework_kernel",
      terminology: "namespace"
    },
    registry: {
      registry_id: "COMPONENT-REGISTRY",
      registry_revision: 2,
      registry_status: "proposed",
      validation_mode: "proposed_revision_validation",
      authoritative: false,
      executable: false,
      authority_effective: false,
      source_revision_authorized: false,
      source_bytes_current: false,
      canonical_history_confirmed: false,
      receipt_trusted: false,
      runtime_live: "not_checked",
      predecessor_route_consulted: false,
      registry_sha256: "2".repeat(64),
      repository_revision: "3".repeat(40),
      design_id: "COMPONENT-REGISTRY-2026-002-STAGE2-IMPLEMENTATION-PR",
      design_revision: `sha256:${"4".repeat(64)}`
    },
    components: [component],
    classifications: {
      classes: [{
        class_id: "document",
        term_id: "document",
        label: "Document",
        definition: "A whole readable information artifact.",
        binding_state: "bound",
        permitted_type_ids: ["framework"],
        component_ids: ["framework_kernel"],
        usage_count: 1,
        console_route: "automation:component-registry:classes?class=document"
      }],
      types: [{
        classification_id: "document:framework",
        class_id: "document",
        type_id: "framework",
        term_id: null,
        label: "Framework",
        definition: null,
        binding_state: "unbound",
        component_ids: ["framework_kernel"],
        usage_count: 1,
        console_route: "automation:component-registry:types?type=document%3Aframework"
      }],
      unbound_class_count: 0,
      unbound_type_count: 1
    },
    lifecycles: {
      states: {
        draft: "Registered and under development.",
        proposed: "Submitted for adoption.",
        adopted: "Incorporated into governed state.",
        retired: "No longer designated for current use."
      },
      permitted_transitions: [["draft", "proposed"], ["proposed", "adopted"]],
      assignments: component.lifecycle_records.map((record) => ({
        ...record,
        display_name: component.display_name,
        classification: component.classification,
        console_route: "automation:component-registry:lifecycles?assignment=lifecycle_framework_kernel"
      }))
    },
    authorities: {
      source_types: {
        owner_authorization: "Closed authority source type value: owner authorization."
      },
      sources: [{ source_id: "owner_benjamin", source_type: "owner_authorization" }],
      assignments: [{
        ...component.authority_records[0],
        display_name: component.display_name,
        source_ids: ["owner_benjamin"],
        sources: [{ source_id: "owner_benjamin", source_type: "owner_authorization" }],
        subjects: ["project framework"],
        effects: ["governs"],
        exclusions: [],
        console_route: "automation:component-registry:authority?assignment=authority_framework_kernel"
      }],
      history: []
    },
    relationships: [{
      relationship_id: "framework_validated_by_test",
      relationship_type: "validated_by",
      from: { kind: "component", id: "framework_kernel" },
      to: { kind: "component", id: "framework_kernel" },
      authority_boundary: "Validation does not create authority.",
      console_route: "automation:component-registry:relationships?relationship=framework_validated_by_test"
    }],
    coverage: {
      records: [{
        coverage_id: "framework",
        coverage_kind: "directory_scope",
        display_name: "Framework",
        path_pattern: "framework/",
        console_route: "automation:component-registry:coverage?coverage=framework"
      }, {
        coverage_id: "repository_tmp_children",
        coverage_kind: "supporting_artifact_rule",
        display_name: "Repository temporary run artifacts",
        path_pattern: ".tmp/",
        console_route: "automation:component-registry:coverage?coverage=repository_tmp_children"
      }],
      path_count: 1,
      uncovered_count: 0,
      multiply_treated_count: 0
    },
    routing: {
      schema_version: 1,
      required_components: ["framework_kernel"],
      generated_path_exclusions: [],
      components: [{ component_id: "framework_kernel", path: "framework/FRAMEWORK.md" }],
      capabilities: {},
      profiles: { compact: { components: ["framework_kernel"] } },
      selections: [{
        routing_id: "profile:compact",
        routing_kind: "profile",
        label: "compact",
        component_ids: ["framework_kernel"],
        details: { components: ["framework_kernel"] },
        console_route: "automation:component-registry:routing?selection=profile%3Acompact"
      }]
    },
    codeowners: {
      available: true,
      complete: true,
      authoritative: false,
      authority_effect: "github_review_routing_only",
      summary: { direct: 1, inherited: 0, none: 0, problems: 0 },
      records: [{
        assignment_id: "component:framework_kernel",
        record_kind: "component",
        stable_id: "framework_kernel",
        display_name: "Framework kernel",
        path_pattern: "framework/FRAMEWORK.md",
        declared_mode: "direct",
        effective_mode: "direct",
        owners: ["@Thorncrag"],
        inherited_from: null,
        generated_pattern: "/framework/FRAMEWORK.md",
        generated_line: "/framework/FRAMEWORK.md @Thorncrag",
        validation_problems: [],
        console_route: "automation:component-registry:codeowners?assignment=component%3Aframework_kernel"
      }],
      generated_rows: [{
        source_id: "component:framework_kernel",
        pattern: "/framework/FRAMEWORK.md",
        owners: ["@Thorncrag"]
      }],
      checked_in_rows: [{
        line_number: 2,
        pattern: "/framework/FRAMEWORK.md",
        owners: ["@Thorncrag"]
      }],
      generated_sha256: "6".repeat(64),
      current_sha256: "6".repeat(64),
      problems: []
    },
    terminology: {
      available: true,
      complete: true,
      adopted: true,
      record_set_sha256: "5".repeat(64),
      entries: terms
    }
  };
}

test("preserved transaction projection derives unresolved membership from retirement proof", () => {
  const { api } = loadApi();
  const current = {
    schema_version: 1,
    availability: "current",
    complete: true,
    generated_at: "2026-07-29T12:00:00Z",
    reason_code: null,
    items: [{
      run_id: "run-001", attempt_group_id: "scheduled-001", lifecycle_state: "failed_preserved",
      preserved: true, retirement_proof: "not_retired", owner: "Run Coordinator",
      age_label: "2 days", failure_class: "validation_failed", next_action: "Package and retire after approval.",
      specialist_route: "automation:agents:run-coordinator-bot"
    }, {
      run_id: "run-002", attempt_group_id: "scheduled-001", lifecycle_state: "recoverably_retired",
      preserved: true, retirement_proof: "recoverably_retired", owner: "Run Coordinator",
      age_label: "1 day", failure_class: "superseded", next_action: "Retained as recovery evidence.",
      specialist_route: "automation:agents:run-coordinator-bot"
    }]
  };
  assert.equal(api.validPrivateTransactionRecovery(current), true);
  assert.equal(api.transactionRecoveryUnresolved(current.items[0]), true);
  assert.equal(api.transactionRecoveryUnresolved(current.items[1]), false);
  assert.equal(api.validPrivateTransactionRecovery({ ...current, items: [{ ...current.items[0], retirement_proof: "recoverably_retired" }] }), false);
});

function loadApi(privateSecurityAssurance = {}, projectDataOverride = {}) {
  const projectData = {
    generation_id: testGenerationId,
    source_revision: testSourceRevision,
    records: [],
    active_horizon_records: [],
    monitoring_issues: [],
    repository_review_recommendations: [],
    ...projectDataOverride
  };
  const projections = {
    "security-assurance": ownerProjectionEntry(
      "security-assurance",
      "private-security-assurance.js",
      "1",
      privateSecurityAssurance.availability === "current" ? "current" : "unavailable",
      privateSecurityAssurance.complete === true
    ),
    "private-operations": ownerProjectionEntry(
      "private-operations",
      "private-operations.js",
      "2"
    ),
    "local-automation-status": ownerProjectionEntry(
      "local-automation-status",
      "local-automation-status.js",
      "3"
    ),
    "codex-usage": ownerProjectionEntry(
      "codex-usage",
      "private-codex-usage.js",
      "4",
      "unavailable",
      false
    )
  };
  const binding = {
    schema_version: 1,
    version_id: testVersionId,
    exact_decoded_file_path: testOwnerPath,
    generation_id: projectData.generation_id,
    source_revision: projectData.source_revision,
    staged_at: testStagedAt,
    projections
  };
  const securityWrapper = ownerProjectionWrapper(
    "security-assurance",
    privateSecurityAssurance,
    binding
  );
  const usageWrapper = ownerProjectionWrapper("codex-usage", codexUsageFixture(), binding);
  const document = {
    body: { dataset: {}, innerHTML: "" },
    querySelectorAll() { return []; }
  };
  const window = {
    ARRP_HORIZON_REVIEW_DATA: projectData,
    ARRP_PRIVATE_SECURITY_ASSURANCE: securityWrapper,
    ARRP_PRIVATE_CODEX_USAGE: usageWrapper,
    ARRP_OWNER_CONSOLE_BINDING: binding,
    location: {
      protocol: "file:",
      hostname: "",
      pathname: testOwnerPath
    },
    __ARRP_CONSOLE_TEST_MODE__: true
  };
  const priorGlobals = {
    window: globalThis.window,
    document: globalThis.document,
    CSS: globalThis.CSS
  };
  globalThis.window = window;
  globalThis.document = document;
  globalThis.CSS = { escape: String };
  const capacityModule = localRequire.resolve("./capacity.js");
  delete localRequire.cache[capacityModule];
  localRequire("./capacity.js");
  const componentRegistryModule = localRequire.resolve("./component-registry.js");
  delete localRequire.cache[componentRegistryModule];
  localRequire("./component-registry.js");
  const appModule = localRequire.resolve("./app.js");
  delete localRequire.cache[appModule];
  try {
    localRequire("./app.js");
    return {
      api: window.ARRP_CONSOLE_TEST_API,
      data: window.ARRP_HORIZON_REVIEW_DATA,
      binding,
      securityWrapper,
      usageWrapper,
      testWindow: window,
      componentRegistryApi: window.ARRP_COMPONENT_REGISTRY
    };
  } finally {
    for (const [name, value] of Object.entries(priorGlobals)) {
      if (value === undefined) delete globalThis[name];
      else globalThis[name] = value;
    }
  }
}

test("Codex usage requires the typed owner-local envelope and never infers an absolute allowance", () => {
  const { api } = loadApi();
  assert.equal(api.validPrivateCodexUsage(codexUsageFixture()), true);
  const available = availableCodexUsageFixture();
  const checkedAt = Date.parse("2026-07-29T20:20:00Z");
  assert.equal(api.validPrivateCodexUsage(available, checkedAt), true);
  assert.equal(api.validPrivateCodexUsage({ ...available, absolute_capacity: 20 }, checkedAt), false);
  assert.equal(api.validPrivateCodexUsage({ ...available, estimates: { ...available.estimates, available: false } }, checkedAt), false);
  assert.equal(api.validPrivateCodexUsage({ ...available, estimates: { ...available.estimates, burn_rate_available: false, average_percent_per_day: 2 } }, checkedAt), false);
  assert.equal(api.validPrivateCodexUsage({ ...available, current: { ...available.current, resets_at: "2026-08-05T01:45:41-04:00" } }, checkedAt), false);
  assert.equal(api.validPrivateCodexUsage({ ...available, current: { ...available.current, used_percent: 28, remaining_percent: 28 } }, checkedAt), false);
  assert.equal(api.validPrivateCodexUsage(available, Date.parse("2026-07-29T20:47:01Z")), false);
});

test("file Console routing updates the hash without the opaque-origin History API", () => {
  const { api, testWindow } = loadApi();
  const priorWindow = globalThis.window;
  let historyAttempts = 0;
  testWindow.location.hash = "#automation:component-registry";
  testWindow.history = {
    replaceState() { historyAttempts += 1; }
  };

  globalThis.window = testWindow;
  try {
    api.replaceConsoleRoute("automation:data");
  } finally {
    if (priorWindow === undefined) delete globalThis.window;
    else globalThis.window = priorWindow;
  }

  assert.equal(historyAttempts, 0);
  assert.equal(testWindow.location.hash, "#automation:data");
});

test("lazy Console domains use the generated bundle identity as their cache key", () => {
  const { api } = loadApi();
  assert.equal(
    api.consoleDomainSource("component-registry.js"),
    `data/component-registry.js?generation=${testGenerationId}`
  );
});

test("Codex usage payload binding uses the canonical semantic digest and rejects tampering", () => {
  const { api, binding, usageWrapper, testWindow } = loadApi();
  const expected = "sha256:72411d2d80862f43fbb833f924f45581f6521e755a4aa4a0131df479f975fa3e";
  assert.equal(api.codexUsagePayloadDigest(usageWrapper.payload), expected);
  binding.projections["codex-usage"].source_sha256 = expected;
  usageWrapper.owner_console_envelope.source_sha256 = expected;
  const priorWindow = globalThis.window;
  globalThis.window = testWindow;
  try {
    assert.equal(api.capturePrivateCodexUsage(), true);
    usageWrapper.payload = {
      ...usageWrapper.payload,
      reason_code: "usage_readback_stale"
    };
    testWindow.ARRP_PRIVATE_CODEX_USAGE = usageWrapper;
    assert.equal(api.validPrivateCodexUsage(usageWrapper.payload), true);
    assert.equal(api.capturePrivateCodexUsage(), false);
  } finally {
    if (priorWindow === undefined) delete globalThis.window;
    else globalThis.window = priorWindow;
  }
});

test("Codex usage graph is responsive, accessible, and uses typed reset boundaries", () => {
  const app = fs.readFileSync(appPath, "utf8");
  const capacity = fs.readFileSync(path.join(consoleDirectory, "capacity.js"), "utf8");
  assert.match(app, /codexCapacityModule\?\.historyElements\(usage, identityPrefix/);
  assert.match(capacity, /function historyElements\(usage, identityPrefix, helpers\)/);
  assert.match(capacity, /role: "img"/);
  assert.match(capacity, /tabindex: "0"/);
  assert.match(capacity, /`\$\{identityPrefix\}-usage-title \$\{identityPrefix\}-usage-description`/);
  assert.match(capacity, /const description = svgNode\(/);
  assert.match(capacity, /timestamp: record\.resets_at \* 1000/);
  assert.match(capacity, /const records = allRecords\.slice\(-48\)/);
  assert.match(capacity, /"usage-trend-reset"/);
  assert.match(capacity, /label\.textContent = `Reset \$\{formatDate\(boundary\.timestamp\)\}`/);
  assert.match(capacity, /"Codex usage readings and reset boundaries"/);
  assert.match(capacity, /usage-trend-text-summary/);
  assert.doesNotMatch(app, /function renderUsageTrend\(\)/);
});

test("Component Registry accepts only the builder-supplied typed snapshot", () => {
  const { api, componentRegistryApi } = loadApi();
  const snapshot = v4ComponentRegistryFixture();
  assert.equal(componentRegistryApi.schemaVersion, snapshot.schema_version);
  assert.equal(
    api.compatibleComponentRegistryModule(componentRegistryApi, snapshot),
    true
  );
  assert.equal(
    api.compatibleComponentRegistryModule(
      { ...componentRegistryApi, schemaVersion: snapshot.schema_version + 1 },
      snapshot
    ),
    false
  );
  assert.equal(
    api.compatibleComponentRegistryModule(
      componentRegistryApi,
      { ...snapshot, schema_version: snapshot.schema_version + 1 }
    ),
    false
  );
  assert.equal(componentRegistryApi.validSnapshot(snapshot), true);
  assert.equal(Object.keys(snapshot.routes).length, 12);
  assert.equal(snapshot.records.components.length, 110);
  assert.equal(snapshot.records.relationships.length, 16);
  assert.equal(snapshot.records.directory_scopes.length, 60);
  assert.equal(snapshot.records.registration_exemptions.length, 3);
  assert.equal(snapshot.records.routing_rules.length, 64);
  assert.equal(snapshot.records.terminology.length, 87);
  [1, 2, 3, 5, true, "4", null].forEach((schemaVersion) => {
    assert.equal(componentRegistryApi.validSnapshot({
      ...snapshot,
      schema_version: schemaVersion
    }), false);
  });
  const proposedSnapshot = structuredClone(snapshot);
  proposedSnapshot.registry.registry_status = "proposed";
  proposedSnapshot.registry.validation_mode = "proposed_revision_validation";
  proposedSnapshot.registry.source_bytes_current = false;
  assert.equal(componentRegistryApi.validSnapshot(proposedSnapshot), true);
  const adoptedSnapshot = structuredClone(snapshot);
  adoptedSnapshot.registry.registry_status = "adopted";
  adoptedSnapshot.registry.validation_mode = "adopted_configuration_validation";
  adoptedSnapshot.registry.source_bytes_current = true;
  assert.equal(componentRegistryApi.validSnapshot(adoptedSnapshot), true);
  assert.equal(componentRegistryApi.validSnapshot({
    ...proposedSnapshot,
    registry: {
      ...proposedSnapshot.registry,
      source_bytes_current: true
    }
  }), false);
  assert.equal(componentRegistryApi.validSnapshot({
    ...adoptedSnapshot,
    registry: {
      ...adoptedSnapshot.registry,
      validation_mode: "proposed_revision_validation"
    }
  }), false);
  [
    { ...snapshot, contract_payload: { private: true } },
    { ...snapshot, source_binding: { sha256: "1".repeat(64) } },
    { ...snapshot, routes: { ...snapshot.routes, documents: "automation:component-registry:documents" } },
    { ...snapshot, registry: { ...snapshot.registry, authoritative: true } },
    { ...snapshot, registry: { ...snapshot.registry, predecessor_route_consulted: true } },
    { ...snapshot, records: { ...snapshot.records, terminology: snapshot.records.terminology.slice(1) } },
    { ...snapshot, linked: { ...snapshot.linked, component_entry_fields: {} } },
    { ...snapshot, derived: { ...snapshot.derived, coverage: { ...snapshot.derived.coverage, uncovered_count: 1 } } },
    { ...snapshot, derived: { ...snapshot.derived, lifecycles: { assignments: snapshot.derived.lifecycles.assignments.map((record, index) => index ? record : { ...record, state: "proposed" }) } } },
    { ...snapshot, derived: { ...snapshot.derived, codeowners: { ...snapshot.derived.codeowners, summary: null } } },
    { ...snapshot, derived: { ...snapshot.derived, codeowners: { ...snapshot.derived.codeowners, current_sha256: "0".repeat(64) } } }
  ].forEach((invalid) => assert.equal(componentRegistryApi.validSnapshot(invalid), false));
  assert.deepEqual(
    componentRegistryApi.routeState(
      "automation:component-registry:routing?selection=capability%3Agovernance",
      snapshot
    ),
    { mode: "routing", selected: "capability:governance" }
  );
  assert.deepEqual(
    componentRegistryApi.routeState(
      "automation:component-registry:routing?rule=ctxr.inv.additive_union",
      snapshot
    ),
    { mode: "routing", selected: "ctxr.inv.additive_union" }
  );
  assert.deepEqual(
    componentRegistryApi.routeState(
      "automation:component-registry:routing?selection=profile%3Acompact&rule=ctxr.inv.additive_union",
      snapshot
    ),
    { mode: "routing", selected: "profile:compact" }
  );
  assert.deepEqual(
    componentRegistryApi.routeState(
      "automation:component-registry:relationships?relationship=registry_validated_by_schema",
      snapshot
    ),
    { mode: "relationships", selected: "registry_validated_by_schema" }
  );
});

test("Component Registry uses only the generated validated projection", () => {
  const html = fs.readFileSync(entrypointPath, "utf8");
  const app = fs.readFileSync(appPath, "utf8");
  const module = fs.readFileSync(componentRegistryPath, "utf8");
  assert.doesNotMatch(html, /<script\s+src="component-registry\.js/);
  assert.doesNotMatch(html, /<script\s+src="data\/component-registry\.js/);
  assert.match(app, /const COMPONENT_REGISTRY_MODULE_VERSION = "11";/);
  assert.match(app, /`component-registry\.js\?v=\$\{COMPONENT_REGISTRY_MODULE_VERSION\}&\$\{generationCacheQuery\}`/);
  assert.match(app, /`generation=\$\{encodeURIComponent\(catalogGenerationId\)\}`/);
  assert.match(app, /consoleDomainSource\("component-registry\.js"\)/);
  assert.match(app, /compatibleComponentRegistryModule\(candidate, data\.component_registry\)/);
  assert.doesNotMatch(app, /candidate\?\.schemaVersion !== 4/);
  assert.match(app, /if \(source\.startsWith\("data\/"\)\) validateLoadedDomainScript\(source\);/);
  assert.doesNotMatch(module, /miscellaneous|uncategorized|infer(?:red)?_taxonomy/i);
  assert.match(module, /snapshot\.records\.components/);
  assert.match(module, /derived\.lifecycles\.assignments/);
  assert.match(module, /derived\.authorities\.assignments/);
  assert.match(module, /derived\.coverage/);
  assert.match(module, /derived\.codeowners\.records/);
  assert.doesNotMatch(module, /component-registry-stage2-terminology-working-draft\.md/);
  assert.doesNotMatch(module, /global\.fetch\(/);
  assert.match(module, /const REGISTRY_SCHEMA_VERSION = 4;/);
  assert.match(module, /global\.location\?\.protocol === "file:"/);
  assert.doesNotMatch(module, /JSON\.stringify\(record\)/);
  assert.match(module, /const FORBIDDEN_KEYS = new Set/);
  assert.match(module, /function safeSearchRecord\(mode, record\)/);
  assert.match(module, /components: records\.components/);
});

test("Component Registry terminology comes only from the validated Registry projection", () => {
  const { componentRegistryApi } = loadApi();
  const snapshot = v4ComponentRegistryFixture();
  assert.equal(componentRegistryApi.validSnapshot(snapshot), true);
  assert.equal(snapshot.records.terminology.length, 87);
  const namespace = snapshot.records.terminology.find((entry) => entry.term_id === "namespace");
  assert.ok(namespace);
  const matches = componentRegistryApi.filterTerminologyEntries(
    snapshot.records.terminology,
    namespace.definition
  );
  assert.ok(matches.some((entry) => entry.term_id === "namespace"));
  assert.deepEqual(
    componentRegistryApi.filterTerminologyEntries(
      snapshot.records.terminology,
      "no-such-definition"
    ),
    []
  );
  assert.equal(componentRegistryApi.validSnapshot({
    ...snapshot,
    contract_payload: { private: true }
  }), false);
  const html = fs.readFileSync(entrypointPath, "utf8");
  assert.match(html, /id="component-registry-terminology-search" type="search"/);
  assert.doesNotMatch(html, /component-registry-terminology-working-draft/);
  const module = fs.readFileSync(componentRegistryPath, "utf8");
  assert.match(module, /terminology: \["term_id", "label", "definition"\]/);
  assert.doesNotMatch(module, /source_provenance|verification_ids/);
  assert.match(module, /global\.history\?\.replaceState/);
  assert.match(module, /filterTerminologyEntries/);
});

test("Component Registry CODEOWNERS view is typed, searchable, and read-only", () => {
  const { componentRegistryApi } = loadApi();
  const snapshot = v4ComponentRegistryFixture();
  assert.equal(componentRegistryApi.validSnapshot(snapshot), true);
  assert.deepEqual(
    componentRegistryApi.routeState(
      "automation:component-registry:codeowners?assignment=component%3Aframework_kernel",
      snapshot
    ),
    { mode: "codeowners", selected: "component:framework_kernel" }
  );
  assert.equal(snapshot.derived.codeowners.available, true);
  assert.equal(snapshot.derived.codeowners.complete, true);
  assert.equal(snapshot.derived.codeowners.problems.length, 0);
  assert.equal(snapshot.derived.codeowners.current_sha256, snapshot.derived.codeowners.generated_sha256);
  assert.deepEqual(componentRegistryApi.codeownersSummary(snapshot), [
    ["Direct", 17],
    ["Inherited", 149],
    ["None", 4],
    ["Problems", 0]
  ]);
  assert.equal(componentRegistryApi.validSnapshot({
    ...snapshot,
    derived: {
      ...snapshot.derived,
      codeowners: {
        ...snapshot.derived.codeowners,
        current_sha256: "7".repeat(64)
      }
    }
  }), false);
  const html = fs.readFileSync(entrypointPath, "utf8");
  assert.match(html, /id="component-registry-codeowners-search" type="search"/);
  assert.match(html, /id="component-registry-codeowners-mode"/);
  assert.match(html, /id="component-registry-codeowners-kind"/);
  assert.match(html, /id="component-registry-codeowners-owner"/);
  assert.match(html, /id="component-registry-codeowners-portals"/);
  assert.match(html, /CODEOWNERS controls GitHub review routing only/);
  assert.doesNotMatch(html, /component-registry-codeowners[^\n]*contenteditable/);
  const module = fs.readFileSync(componentRegistryPath, "utf8");
  assert.match(module, /Expected versus checked-in CODEOWNERS/);
  assert.match(module, /codeowners\.generated_sha256 === codeowners\.current_sha256/);
});

test("Component Registry lifecycle view presents only compact Registry states", () => {
  const { componentRegistryApi } = loadApi();
  const snapshot = v4ComponentRegistryFixture();
  const summary = componentRegistryApi.lifecycleSummary(snapshot);
  assert.deepEqual(summary.map(({ state, count }) => ({ state, count })), [
    { state: "adopted", count: 105 },
    { state: "retired", count: 5 }
  ]);
  assert.equal(
    summary.find((entry) => entry.state === "adopted").definition,
    snapshot.records.terminology.find((entry) =>
      entry.term_id === "adopted_lifecycle_state").definition
  );
  assert.equal(summary.some((entry) => ["draft", "proposed"].includes(entry.state)), false);
  const html = fs.readFileSync(entrypointPath, "utf8");
  assert.match(html, /id="component-registry-lifecycle-portals"/);
  assert.doesNotMatch(html, /component-registry-lifecycle-flow/);
  const styles = fs.readFileSync(path.join(consoleDirectory, "styles.css"), "utf8");
  assert.doesNotMatch(styles, /component-registry-transition/);
});

test("Component Registry modes explain what their records mean and how they apply", () => {
  const html = fs.readFileSync(entrypointPath, "utf8");
  assert.equal(
    (html.match(/class="[^"]*component-registry-mode-explanation/g) || []).length,
    12
  );
  assert.equal((html.match(/aria-describedby="component-registry-[^"]+"/g) || []).length, 12);
  assert.match(html, /Exemptions identify artifacts that do not need individual Registry entries/);
  assert.match(html, /because a registered scope governs them as a group/);
  assert.match(html, /an empty result means validation found no such paths, not that the Registry contains no data/);
  assert.match(html, /It controls context selection, not project authority or workflow permission/);
  const specification = fs.readFileSync(
    path.join(consoleDirectory, "specification.md"),
    "utf8"
  );
  assert.match(specification, /Every mode begins with a concise, plain-language explanation/);
  assert.match(specification, /it does not reconstruct the transition or history model/);
});

test("Component Registry separates directories, exemptions, and unresolved coverage", () => {
  const { componentRegistryApi } = loadApi();
  const snapshot = v4ComponentRegistryFixture();
  assert.deepEqual(
    componentRegistryApi.routeState(
      "automation:component-registry:directories?directory=framework",
      snapshot
    ),
    { mode: "directories", selected: "framework" }
  );
  assert.deepEqual(
    componentRegistryApi.routeState(
      "automation:component-registry:exemptions?exemption=repository_tmp_children",
      snapshot
    ),
    { mode: "exemptions", selected: "repository_tmp_children" }
  );
  assert.deepEqual(
    componentRegistryApi.routeState(
      "automation:component-registry:coverage?coverage=repository_tmp_children",
      snapshot
    ),
    { mode: "components", selected: null }
  );
  assert.deepEqual(
    componentRegistryApi.routeState(
      "automation:component-registry:unresolved",
      snapshot
    ),
    { mode: "unresolved", selected: null }
  );
});

test("Component Registry exposes distinct Classes and Types reference views", () => {
  const { componentRegistryApi } = loadApi();
  const snapshot = v4ComponentRegistryFixture();
  assert.deepEqual(
    componentRegistryApi.routeState(
      "automation:component-registry:classes?class=document",
      snapshot
    ),
    { mode: "classes", selected: "document" }
  );
  assert.deepEqual(
    componentRegistryApi.routeState(
      "automation:component-registry:types?type=document%3Aframework",
      snapshot
    ),
    { mode: "types", selected: "document:framework" }
  );
  const html = fs.readFileSync(entrypointPath, "utf8");
  assert.match(html, /id="component-registry-mode-classes"/);
  assert.match(html, /id="component-registry-mode-types"/);
  assert.match(html, /id="component-registry-classes-search"/);
  assert.match(html, /id="component-registry-types-class"/);
});

test("Component Registry is an Operations subtab after Data and before Logs", () => {
  const html = fs.readFileSync(entrypointPath, "utf8");
  const module = fs.readFileSync(componentRegistryPath, "utf8");
  const dataIndex = html.indexOf('id="automation-tab-data"');
  const registryIndex = html.indexOf('id="automation-tab-component-registry"');
  const logsIndex = html.indexOf('id="automation-tab-logs"');
  assert.ok(dataIndex >= 0 && dataIndex < registryIndex && registryIndex < logsIndex);
  ["components", "classes", "types", "lifecycles", "authority", "relationships", "directories", "exemptions", "unresolved", "routing", "codeowners", "terminology"].forEach((mode) => {
    assert.match(html, new RegExp(`id="component-registry-mode-${mode}"`));
    assert.match(html, new RegExp(`id="component-registry-panel-${mode}"`));
    assert.doesNotMatch(html, new RegExp(`id="component-registry-${mode}-count"`));
  });
  assert.equal((html.match(/class="email-workspace component-registry-workspace"/g) || []).length, 11);
  assert.equal((html.match(/class="email-list component-registry-list"/g) || []).length, 11);
  assert.doesNotMatch(html, /id="component-registry-mode-coverage"/);
  assert.doesNotMatch(module, /setCount\(|"tab-count"/);
  assert.match(module, /"email-list-row component-registry-list-row"/);
  assert.match(module, /"email-row-title"/);
  assert.match(module, /"email-row-time"/);
  assert.match(module, /classList\.toggle\("selected", active\)/);
  assert.doesNotMatch(html, /Artifact rule/);
  assert.match(html, /Validated, nonauthoritative Registry view/);
  assert.doesNotMatch(
    html.slice(
      html.indexOf('id="panel-overview"'),
      html.indexOf('id="panel-progress"')
    ),
    /component-registry/i
  );
});

test("Component details distinguish entry fields, linked records, and presentation labels", () => {
  const { componentRegistryApi } = loadApi();
  const snapshot = v4ComponentRegistryFixture();
  const premise = snapshot.records.components.find((record) =>
    record.stable_id === "project_premise");
  const registry = snapshot.records.components.find((record) =>
    record.stable_id === "COMPONENT-REGISTRY");
  const premiseModel = componentRegistryApi.componentDetailModel(snapshot, premise);
  const registryModel = componentRegistryApi.componentDetailModel(snapshot, registry);
  assert.ok(premiseModel.entryRows.some(([label]) => label === "Display name"));
  assert.ok(premiseModel.defaultRows.some(([label]) => label === "Owner"));
  assert.ok(registryModel.entryRows.some(([label]) => label === "Information handling"));
  assert.ok(registryModel.defaultRows.some(([label]) => label === "Lifecycle"));
  assert.match(registryModel.source.url, /github\.com\/Thorncrag\/ARRP\/blob\/main\/framework\/component-registry\.json/);
  assert.ok(registryModel.derivedRows.some(([label]) => label === "Stable ID"));
  const module = fs.readFileSync(componentRegistryPath, "utf8");
  assert.match(module, /"Registered component"/);
  assert.match(module, /"Canonical file: "/);
  assert.match(module, /target\.replaceChildren\(heading, node\("hr", "component-registry-heading-divider"\)\)/);
  assert.match(module, /"Component entry"/);
  assert.match(module, /"Registry defaults"/);
  assert.match(module, /"Linked Registry records"/);
  assert.match(module, /"Derived Registry view"/);
  assert.match(module, /missing Registry values are never inferred/);
  assert.doesNotMatch(module, /https:\/\/github\.com\/Thorncrag\/ARRP\/blob\/main\//);
  assert.doesNotMatch(module, /record\.record_refs/);
  assert.doesNotMatch(module, /record\.component_boundary/);
  assert.match(module, /record\.execution_controls/);
  assert.match(module, /\["ArrowDown", "ArrowUp", "Home", "End"\]/);
});

test("term normalization uses the canonical Trump I and Trump II vocabulary", () => {
  const { api } = loadApi();
  assert.equal(api.normalizeTerm("1"), "trump-i");
  assert.equal(api.normalizeTerm("Trump II"), "trump-ii");
  assert.equal(api.normalizeTerm("both terms"), "both");
  assert.equal(api.termLabel("Trump II"), "Trump II");
  assert.equal(api.termLabel("unknown"), "Term not recorded");
});

test("Console development categories render as separate readable log entries", () => {
  const app = fs.readFileSync(appPath, "utf8");
  assert.match(
    app,
    /if \(log\.id === "console-development"\) return values\.category \|\| values\.change \|\| entry\.id;/
  );
  assert.doesNotMatch(
    app,
    /log\.id === "console-development"[^;]+values\.feature/
  );
});

test("date-only audit provenance preserves its recorded calendar day", () => {
  const { api } = loadApi();
  assert.equal(api.formatDate("2026-07-10"), "Jul 10, 2026");
});

test("Integrity remains the exact authoritative report rather than a cross-domain total", () => {
  const { api, data } = loadApi();
  data.integrity = {
    current: {
      generated_at: "2026-07-28T12:00:00Z",
      findings: [{
        finding_id: "INT-001",
        check_id: "check_issue_pages",
        condition_code: "project_integrity_condition",
        canonical_target: "areas/TEST/issues/TEST-001.md",
        message: "Exact report finding"
      }]
    }
  };
  data.action_snapshot = {
    availability: "current",
    complete: true,
    items: [{
      item_id: "readiness-conflict:HOR-031",
      work_kind: "integrity_obligation",
      authority: "typed Pipeline producer",
      route: "integrity",
      label: "Pipeline provenance defect"
    }]
  };
  const exact = api.exactIntegrityProblemRecords(data.integrity);
  const combined = api.producerProblemRecords();
  assert.deepEqual(exact.map((finding) => finding.reference), ["INT-001"]);
  assert.ok(combined.some((finding) => finding.label === "Pipeline provenance defect"));
});

test("security assurance accepts only minimized registered tool status", () => {
  const publicTools = [
    { tool_id: "credential-access-review", label: "Credential and access review", purpose: "Safe purpose.", owner_class: "Human", destination_class: "owner_local_review" },
    { tool_id: "repository-change-protection", label: "Repository change protection", purpose: "Safe purpose.", owner_class: "Elim", destination_class: "protected_source" }
  ];
  const { api } = loadApi({
    schema_version: 2,
    availability: "current",
    complete: true,
    checked_at: "2026-07-28T20:00:00Z",
    public_intake_state: "unverified",
    private_attention: "required",
    active_incident: false,
    tools: [
      { tool_id: "credential-access-review", availability: "current", last_checked: "2026-07-28T20:00:00Z", coverage_state: "current", private_attention: "yes", owner_class: "Human", destination_class: "owner_local_review", active_incident: false, public_intake_state: null, next_due: null, source_revision: "safe-revision", label: "Credential and access review" },
      { tool_id: "repository-change-protection", availability: "current", last_checked: "2026-07-28T20:00:00Z", coverage_state: "current", private_attention: "yes", owner_class: "Elim", destination_class: "protected_source", active_incident: false, public_intake_state: null, next_due: null, source_revision: "safe-revision", label: "Repository change protection" }
    ]
  }, {
    security_assurance: { schema_version: 2, availability: "unavailable", complete: false, tools: publicTools },
    action_snapshot: {
      availability: "current",
      complete: true,
      items: [
        {
          item_id: "security-action:credential-access-review",
          work_kind: "security_protected_action",
          authority: "Owner-local security assurance projection",
          route: "automation:security",
          attention: "human",
          message: "Review private security action"
        },
        {
          item_id: "security-action:repository-change-protection",
          work_kind: "security_protected_action",
          authority: "Owner-local security assurance projection",
          route: "automation:security",
          attention: "oversight",
          message: "Private security remediation requires review"
        }
      ]
    }
  });
  const projection = api.securityAssuranceProjection();
  assert.equal(projection.available, true);
  assert.equal(projection.privateAttention, "required");
  assert.equal(api.securityActionRecords().filter((record) => record.attention === "human").length, 1);
  assert.equal(api.securityActionRecords().filter((record) => record.attention === "oversight").length, 1);
  assert.ok(api.securityActionRecords().every((record) => !record.message.includes("credential-access-review")));
});

test("security assurance fails closed on vulnerability-shaped or unknown fields", () => {
  const { api } = loadApi({
    schema_version: 2,
    availability: "current",
    complete: true,
    checked_at: "2026-07-28T20:00:00Z",
    public_intake_state: "live",
    private_attention: "none_reported",
    active_incident: false,
    tools: [{
      tool_id: "credential-access-review",
      label: "Credential and access review",
      availability: "current",
      coverage_state: "current",
      private_attention: "no",
      owner_class: "Human",
      destination_class: "owner_local_review",
      active_incident: false,
      vulnerability_message: "must not enter the Console"
    }]
  }, {
    security_assurance: {
      schema_version: 2,
      tools: [{ tool_id: "credential-access-review", label: "Credential and access review", purpose: "Safe purpose." }]
    }
  });
  assert.equal(api.securityAssuranceProjection().available, false);
  assert.equal(api.securityActionRecords().length, 0);
});

test("security assurance exposes staged safe actions and keyboard navigation", () => {
  const app = fs.readFileSync(appPath, "utf8");
  const html = fs.readFileSync(entrypointPath, "utf8");
  assert.match(html, /id="refresh-security-status"/);
  assert.match(html, /Download status request/);
  assert.match(html, /Download review request/);
  assert.match(html, /Security controls are non-executing/);
  assert.match(html, /they do not run a scan or change repository settings/);
  assert.match(app, /prepare_public_intake_state_request/);
  assert.match(app, /execution: "staged_request_only"/);
  assert.match(app, /mixed_state_response: "record_operational_incident"/);
  assert.match(app, /Download Live-state request/);
  assert.match(app, /Download Paused-state request/);
  assert.match(app, /they do not change the public-intake state/);
  assert.match(app, /event\.key === "ArrowDown"/);
  assert.doesNotMatch(app, /arbitrary_command_execution"\]\s*,?\s*commands:/);
});

test("security actions and Logs tertiary navigation use the shared control grammar", () => {
  const styles = fs.readFileSync(path.join(consoleDirectory, "styles.css"), "utf8");
  assert.match(styles, /#automation-panel-security button\.record-link\.secondary\s*\{[^}]*border:\s*1px solid #c6d6e7/s);
  assert.match(styles, /#automation-panel-logs \.logs-screen-header\s*\{[^}]*border-bottom:\s*0/s);
  assert.match(styles, /#automation-panel-logs \.operations-log-menu\s*\{[^}]*border-bottom:\s*0/s);
});

test("layout-only disclosure controls stay out of ordinary run details", () => {
  const styles = fs.readFileSync(path.join(consoleDirectory, "styles.css"), "utf8");
  assert.match(styles, /\.disclosure-default-toggle\s*\{[^}]*display:\s*none/s);
  assert.match(styles, /body\.layout-editing \.disclosure-default-toggle\s*\{[^}]*display:\s*inline-flex/s);
  assert.match(styles, /#automation-chain-stages \.automation-chain-summary\s*\{[^}]*grid-template-columns:\s*repeat\(3, minmax\(0, 1fr\)\)/s);
});

test("owner-local projections require exact immutable file binding", async () => {
  const { api, binding, securityWrapper } = loadApi();
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "file:",
    hostname: "",
    pathname: testOwnerPath.replaceAll(" ", "%20")
  }, binding), true);
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "file:",
    hostname: "",
    pathname: "/Users/example/ARRP/framework/project/interfaces/project-console/project-console.html"
  }, binding), false);
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "file:",
    hostname: "",
    pathname: testOwnerPath.replace("project-console.html", "copy.html")
  }, binding), false);
  const nonEntrypointBinding = {
    ...binding,
    exact_decoded_file_path: testOwnerPath.replace("project-console.html", "entry.html")
  };
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "file:",
    hostname: "",
    pathname: nonEntrypointBinding.exact_decoded_file_path
  }, nonEntrypointBinding), false);
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "http:",
    hostname: "127.0.0.1",
    pathname: "/project-console.html"
  }, binding), false);
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "https:",
    hostname: "arrp.org",
    pathname: "/framework/project/interfaces/project-console/project-console.html"
  }, binding), false);
  assert.equal(api.ownerModeUnavailableMessage(
    "Owner projection is missing.",
    {
      protocol: "https:",
      hostname: "arrp.org",
      pathname: "/framework/project/interfaces/project-console/project-console.html"
    },
    binding
  ), "Data unavailable outside the bound owner-local Console.");
  assert.equal(api.ownerModeUnavailableMessage(
    "Owner projection is missing.",
    {
      protocol: "file:",
      hostname: "",
      pathname: testOwnerPath
    },
    binding
  ), "Owner projection is missing.");
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "file:",
    hostname: "",
    pathname: testOwnerPath
  }, { ...binding, generation_id: "stale-generation" }), false);
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "file:",
    hostname: "",
    pathname: testOwnerPath
  }, { ...binding, unexpected: true }), false);
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "file:",
    hostname: "",
    pathname: testOwnerPath
  }, null), false);
  assert.doesNotMatch(
    fs.readFileSync(appPath, "utf8"),
    /console\/owner\/versions/
  );
  assert.deepEqual(
    api.ownerProjectionPayload(
      securityWrapper,
      "security-assurance",
      binding,
      { protocol: "file:", hostname: "", pathname: testOwnerPath }
    ),
    securityWrapper.payload
  );
  assert.equal(
    api.ownerProjectionPayload(
      securityWrapper.payload,
      "security-assurance",
      binding,
      { protocol: "file:", hostname: "", pathname: testOwnerPath }
    ),
    null
  );
  assert.equal(
    api.ownerProjectionPayload({
      ...securityWrapper,
      owner_console_envelope: {
        ...securityWrapper.owner_console_envelope,
        source_revision: "b".repeat(40)
      }
    }, "security-assurance", binding, {
      protocol: "file:",
      hostname: "",
      pathname: testOwnerPath
    }),
    null
  );

  const priorWindow = globalThis.window;
  const priorDocument = globalThis.document;
  let appended = 0;
  globalThis.window = {
    location: {
      protocol: "file:",
      hostname: "",
      pathname: testOwnerPath
    },
    ARRP_OWNER_CONSOLE_BINDING: binding
  };
  globalThis.document = {
    createElement() { return {}; },
    head: {
      append(script) {
        appended += 1;
        script.onerror();
      }
    }
  };
  try {
    assert.equal(
      await api.loadLocalProjection(
        "data/missing.js",
        "private-operations",
        () => false
      ),
      false
    );
    assert.equal(appended, 0);
    const swappedBinding = {
      ...binding,
      projections: {
        ...binding.projections,
        "security-assurance": {
          ...binding.projections["security-assurance"],
          relative_path: binding.projections["private-operations"].relative_path
        },
        "private-operations": {
          ...binding.projections["private-operations"],
          relative_path: binding.projections["security-assurance"].relative_path
        }
      }
    };
    globalThis.window.ARRP_OWNER_CONSOLE_BINDING = swappedBinding;
    assert.equal(api.localConsoleOriginAllowed(
      globalThis.window.location,
      swappedBinding
    ), true);
    assert.equal(
      await api.loadLocalProjection(
        "data/private-operations.js?v=1",
        "private-operations",
        () => false
      ),
      false
    );
    assert.equal(
      await api.loadLocalProjection(
        "data/private-security-assurance.js?v=1",
        "security-assurance",
        () => false
      ),
      false
    );
    assert.equal(appended, 0);
    globalThis.window.ARRP_OWNER_CONSOLE_BINDING = binding;
    assert.equal(
      await api.loadLocalProjection(
        "data/private-operations.js?v=1",
        "private-operations",
        () => false
      ),
      false
    );
    assert.equal(appended, 1);
  } finally {
    if (priorWindow === undefined) delete globalThis.window;
    else globalThis.window = priorWindow;
    if (priorDocument === undefined) delete globalThis.document;
    else globalThis.document = priorDocument;
  }
});

test("private operations require exact generation and revision binding", () => {
  const { api, data, binding, testWindow } = loadApi();
  const snapshot = privateOperationsFixture();
  assert.equal(api.validPrivateOperationsSnapshot(snapshot), true);
  assert.equal(api.validPrivateOperationsSnapshot({
    ...snapshot,
    catalog_generation_id: "older-generation"
  }), false);
  assert.equal(api.validPrivateOperationsSnapshot({
    ...snapshot,
    action_snapshot: {
      ...snapshot.action_snapshot,
      counts: { human: 0, oversight: 0, all_open: 0 }
    }
  }), false);

  const privateBinding = {
    ...binding,
    projections: {
      ...binding.projections,
      "private-operations": {
        ...binding.projections["private-operations"],
        availability: "partial",
        complete: false
      }
    }
  };
  testWindow.ARRP_OWNER_CONSOLE_BINDING = privateBinding;
  testWindow.ARRP_PRIVATE_OPERATIONS = ownerProjectionWrapper(
    "private-operations",
    snapshot,
    privateBinding
  );
  data.overview = {
    action_snapshot: { availability: "unavailable" },
    queue_directory: { availability: "unavailable" }
  };
  const priorWindow = globalThis.window;
  globalThis.window = testWindow;
  try {
    assert.equal(api.capturePrivateOperations(), true);
  } finally {
    if (priorWindow === undefined) delete globalThis.window;
    else globalThis.window = priorWindow;
  }
  assert.equal(data.action_snapshot, snapshot.action_snapshot);
  assert.equal(data.overview.action_snapshot, snapshot.action_snapshot);
  assert.equal(data.queue_directory, snapshot.queue_directory);
  assert.equal(data.overview.queue_directory, snapshot.queue_directory);
  assert.equal(data.operational_incidents, snapshot.operational_incidents);
  assert.equal(data.security_incidents, snapshot.security_incidents);
  assert.equal(data.incident_relations, snapshot.incident_relations);
});

test("governance supplements require an exact public-entry and revision match", () => {
  const { api } = loadApi();
  const item = {
    governance_change_id: "GOV-2026-001",
    public_entry_sha256: `sha256:${"1".repeat(64)}`,
    source_revision: testSourceRevision,
    recorded_at: "2026-07-29T12:00:00Z",
    safe_summary: "Owner-only implementation context."
  };
  const supplements = { complete: true, items: [item] };
  assert.deepEqual(api.governanceChangeSupplement({
    id: "GOV-2026-001",
    values: {
      governance_change_id: "GOV-2026-001",
      entry_sha256: item.public_entry_sha256
    }
  }, supplements), item);
  assert.equal(api.governanceChangeSupplement({
    id: "GOV-2026-002",
    values: {
      governance_change_id: "GOV-2026-002",
      entry_sha256: item.public_entry_sha256
    }
  }, supplements), null);
  assert.equal(api.governanceChangeSupplement({
    id: "GOV-2026-001",
    values: {
      governance_change_id: "GOV-2026-001",
      entry_sha256: item.public_entry_sha256
    }
  }, { complete: true, items: [{ ...item, source_revision: "other" }] }), null);
});

test("role surfaces share the typed projection and exact owner-only control state", () => {
  const { api } = loadApi({}, {
    automation_role_status: {
      availability: "current",
      control_state: { state: "unavailable" },
      roles: [
        {
          id: "run-coordinator-bot",
          latest_scheduled: { available: false },
          data_currentness: { state: "current" }
        },
        {
          id: "project-integrity-bot",
          latest_scheduled: { available: true, outcome: "succeeded", at: "2026-07-27T08:00:00Z" },
          data_currentness: { state: "current" }
        }
      ]
    }
  });
  const projection = api.effectiveAutomationRoleStatusProjection(
    undefined,
    {
      control_state: "paused",
      control_state_checked_at: "2026-07-28T12:00:00Z",
      trigger: "scheduled",
      status: "paused",
      scheduled_for: "2026-07-28T02:00:00-04:00",
      updated_at: "2026-07-28T12:00:00Z",
      run_id: "RUN-1"
    }
  );
  assert.equal(projection.control_state.state, "paused");
  assert.ok(projection.roles.every((role) => role.pause_state === "paused"));
  assert.equal(projection.roles[0].latest_scheduled.outcome, "paused");
});

test("score zero is valid, null is unavailable, and invalid values remain visible", () => {
  const { api } = loadApi();
  assert.deepEqual(
    JSON.parse(JSON.stringify(api.scorePresentation(0))),
    { label: "Score 0", valid: true, available: true, value: 0 }
  );
  assert.equal(api.scorePresentation(null).available, false);
  assert.equal(api.scorePresentation(101).valid, false);
  assert.match(api.scorePresentation("bad").label, /Invalid score/);
  assert.deepEqual(
    JSON.parse(JSON.stringify(api.scorePresentation(false))),
    { label: "Invalid score: false", valid: false, available: true, value: false }
  );
});

test("feed state consumes producer declarations and completeness", () => {
  const { api } = loadApi();
  assert.equal(api.feedContractState({ availability: "current" }).label, "Current");
  assert.equal(api.feedContractState({ availability: "available" }).label, "Available");
  const incomplete = api.feedContractState({
    availability: "current",
    expected_count: 2055,
    actual_count: 2048,
    completeness: { complete: false, reason: "Seven records are missing" }
  });
  assert.equal(incomplete.state, "incomplete");
  assert.equal(incomplete.complete, false);
  assert.equal(incomplete.expected, 2055);
  assert.equal(incomplete.actual, 2048);
});

test("source families match the accepted Console taxonomy while raw types remain independent", () => {
  const { api } = loadApi();
  assert.equal(api.sourceTypeFamily("Federal court opinion"), "Judicial");
  assert.equal(api.sourceTypeFamily("Congressional hearing"), "Legislative");
  assert.equal(api.sourceTypeFamily("Agency report"), "Government");
  assert.equal(api.sourceTypeFamily("Peer-reviewed journal study"), "Scholarly");
  assert.equal(api.sourceTypeFamily("News article"), "News");
  assert.equal(api.sourceTypeFamily("Advocacy organization brief"), "Advocacy");
  assert.equal(api.sourceTypeFamily("Litigation tracker"), "Tracker");
  assert.equal(api.sourceTypeFamily("Personal correspondence"), "Other");
});

test("older live feeds cannot replace newer checked-in projections", () => {
  const { api } = loadApi();
  assert.equal(api.shouldAcceptLiveFeed(
    { generated_at: "2026-07-25T10:00:00+00:00" },
    { generated_at: "2026-07-25T09:59:59Z" }
  ), false);
  assert.equal(api.shouldAcceptLiveFeed(
    { generated_at: "2026-07-25T10:00:00+00:00" },
    { generated_at: "2026-07-25T10:00:01Z" }
  ), true);
  assert.equal(api.shouldAcceptLiveFeed(
    { generated_at: "2026-07-25T10:00:00Z", source_revision: "current-revision" },
    { generated_at: "2026-07-25T10:30:00Z", source_revision: "superseded-revision" }
  ), false);
  assert.equal(api.shouldAcceptLiveFeed(
    { generated_at: "2026-07-25T10:00:00Z", source_revision: "current-revision" },
    {
      generated_at: "2026-07-25T10:30:00Z",
      source_revision: "next-revision",
      supersedes_source_revision: "current-revision"
    }
  ), true);
});

test("authority-specific freshness accepts legitimate newer generations and rejects superseded recent ones", () => {
  const { api } = loadApi();
  const complete = { complete: true, expected_count: 1, actual_count: 1 };
  assert.equal(api.shouldAcceptLiveFeed("progress",
    { generated_at: "2026-07-25T10:00:00Z", generation_id: "project-old", completeness: complete },
    { generated_at: "2026-07-25T11:00:00Z", generation_id: "project-new", completeness: complete }
  ), true);
  assert.equal(api.shouldAcceptLiveFeed("integrity",
    { generated_at: "2026-07-25T10:00:00Z", source_revision: "head-old", completeness: complete },
    { generated_at: "2026-07-25T11:00:00Z", source_revision: "head-new", completeness: complete }
  ), true);
  assert.equal(api.shouldAcceptLiveFeed("integrity",
    { generated_at: "2026-07-25T11:00:00Z", source_revision: "head-new", completeness: complete },
    { generated_at: "2026-07-25T10:30:00Z", source_revision: "head-old", completeness: complete }
  ), false);
  const hashes = { "inventory/sources.csv": `sha256:${"b".repeat(64)}` };
  assert.equal(api.shouldAcceptLiveFeed("source-checker",
    {
      checked_at: "2026-07-25T10:00:00Z",
      generation_id: "checker-old",
      completeness: complete,
      current_catalog_coverage: { source_hashes: hashes }
    },
    {
      checked_at: "2026-07-25T11:00:00Z",
      generation_id: "checker-new",
      completeness: complete,
      source_hashes: hashes
    }
  ), true);
});

test("candidate Project fields merge over dossier fields without dropping dossier evidence", () => {
  const { api, data } = loadApi();
  data.active_horizon_records = [{
    id: "HOR-001",
    title: "Dossier title",
    development_level: "Candidate",
    workflow_status: "Research",
    supporting_sources: [{ id: "SRC-1" }]
  }];
  data.progress = {
    candidates: [{
      identifier: "HOR-001",
      developmentLevel: "In development",
      workflowStatus: "Human decision needed",
      priority: "High",
      score: 0
    }]
  };
  const merged = api.candidateProjectRecords()[0];
  assert.equal(merged.development_level, "In development");
  assert.equal(merged.workflow_status, "Human decision needed");
  assert.equal(merged.priority, "High");
  assert.equal(merged.score, 0);
  assert.equal(merged.supporting_sources[0].id, "SRC-1");
});

test("Source Checker assurance deltas preserve explicit zero and baseline unavailability", () => {
  const { api } = loadApi();
  const unavailable = api.sourceCheckerDeltaPresentation({
    deltas: { available: false, reason: "No comparable prior baseline." }
  });
  assert.equal(unavailable.available, false);
  assert.match(unavailable.reason, /prior baseline/);
  const available = api.sourceCheckerDeltaPresentation({
    deltas: {
      available: true,
      baseline_checked_at: "2026-07-24T10:00:00Z",
      counts: {
        new_exceptions: 0,
        regressed_exceptions: 2,
        resolved_exceptions: 1,
        ongoing_exceptions: 3
      },
      aging_exceptions: [{ source_id: "SRC-1", classification: "broken", age_days: 4 }]
    }
  });
  assert.equal(available.counts.newExceptions, 0);
  assert.equal(available.counts.regressedExceptions, 2);
  assert.equal(available.oldest.source_id, "SRC-1");
});

test("watcher repository fixtures route to specialist views and report typed affected counts", () => {
  const { api } = loadApi();
  const pr380 = {
    complete: true,
    total_count: 43,
    source_ids: Array.from({ length: 42 }, (_, index) => `SRC-${index}`),
    directive_ids: [],
    issue_development_ids: ["HOR-035"],
    issue_development_count: 1
  };
  assert.equal(api.repositorySpecialistRoute(pr380).target, "sources:watchers:courts");
  assert.match(api.repositoryAffectedSummary(pr380), /43 affected records/);
  assert.match(api.repositoryAffectedSummary(pr380), /1 proposal\/candidate/);
  assert.match(api.repositoryAffectedSummary(pr380), /42 sources/);
  const pr381 = {
    complete: true,
    total_count: 10,
    source_ids: [],
    directive_ids: Array.from({ length: 10 }, (_, index) => `2026-${index}`),
    issue_development_ids: [],
    issue_development_count: 0
  };
  assert.equal(api.repositorySpecialistRoute(pr381).target, "sources:watchers:directives");
  assert.match(api.repositoryAffectedSummary(pr381), /10 directives/);
});

test("generation validation accepts canonical hashes and rejects mixed or missing domains", () => {
  const { api } = loadApi();
  const generation = "project-console-test";
  const manifest = {
    files: {
      "progress.js": {
        generation_id: generation,
        sha256: `sha256:${"a".repeat(64)}`,
        bytes: 123
      }
    }
  };
  assert.equal(api.domainGenerationStatus(generation, "progress.js", { "progress.js": generation }, manifest).valid, true);
  assert.equal(api.domainGenerationStatus(generation, "progress.js", { "progress.js": "other" }, manifest).valid, false);
  assert.equal(api.domainGenerationStatus(generation, "integrity.js", { "integrity.js": generation }, manifest).valid, false);
  const badHash = structuredClone(manifest);
  badHash.files["progress.js"].sha256 = "not-a-hash";
  assert.equal(api.domainGenerationStatus(generation, "progress.js", { "progress.js": generation }, badHash).valid, false);
});

test("Overview green status requires every brief feed and the loaded generation to verify", () => {
  const generation = "project-console-overview-test";
  const timestamp = "2026-07-28T12:00:00Z";
  const currentFeed = {
    availability: "current",
    generated_at: timestamp,
    completeness: { complete: true }
  };
  const runChain = {
    ...currentFeed,
    chain_id: "arrp-test",
    status: "complete"
  };
  const { api, data } = loadApi({}, {
    generation_id: generation,
    generation_manifest: {
      files: {
        "overview.js": {
          generation_id: generation,
          sha256: `sha256:${"b".repeat(64)}`,
          bytes: 123
        }
      }
    },
    domain_generation: { "overview.js": generation },
    overview: {
      progress_summary: { ...currentFeed },
      integrity_summary: { ...currentFeed },
      source_checker_summary: { ...currentFeed, checked_at: timestamp }
    }
  });

  assert.equal(api.overviewBriefVerification(runChain).verified, true);
  data.overview.source_checker_summary.availability = "stale";
  const stale = api.overviewBriefVerification(runChain);
  assert.equal(stale.verified, false);
  assert.deepEqual(stale.failed.map((entry) => entry.label), ["Source checks"]);
});

test("Current Project Brief dots distinguish success, pause, blockers, and unknown readiness", () => {
  const { api } = loadApi();
  const currentVerification = {
    verified: true,
    bundleVerified: true,
    failed: []
  };
  const staleVerification = {
    verified: false,
    bundleVerified: true,
    failed: [{
      timestampValid: true,
      state: { state: "stale", complete: true, reason: "" }
    }]
  };
  const readiness = {
    latest_attempt: { available: true, blockers: [], blocker_count: 0 },
    latest_scheduled_attempt: { available: false },
    future_run_gates: { available: true, items: [], count: 0 }
  };
  const completed = {
    trigger: "scheduled",
    status: "completed",
    control_state: "run",
    updated_at: "2026-07-28T08:55:33Z"
  };
  const healthy = api.overviewBriefFactStates({}, readiness, currentVerification, completed);
  assert.equal(healthy.latest.tone, "success");
  assert.equal(healthy.lastSuccessful.tone, "success");
  assert.equal(healthy.nextRun.tone, "success");
  assert.equal(healthy.nextEpoch.tone, "success");

  const paused = api.overviewBriefFactStates({}, readiness, staleVerification, {
    ...completed,
    status: "paused",
    control_state: "paused",
    validation_summary: { reason: "owner_pause_file_present" }
  });
  assert.equal(paused.data.tone, "warning");
  assert.equal(paused.latest.tone, "warning");
  assert.equal(paused.lastSuccessful.tone, "warning");
  assert.equal(paused.nextRun.tone, "warning");

  const scopedBlocker = {
    ...readiness,
    future_run_gates: {
      available: true,
      count: 1,
      items: [{ id: "ordinary-only", run_scope: "ordinary" }]
    }
  };
  const blocked = api.overviewBriefFactStates({}, scopedBlocker, currentVerification, {
    ...completed,
    status: "paused",
    control_state: "paused"
  });
  assert.equal(blocked.latest.tone, "error");
  assert.equal(blocked.nextRun.tone, "error");
  assert.equal(blocked.nextEpoch.tone, "warning");

  const unknown = api.overviewBriefFactStates({}, {
    latest_attempt: { available: false, blockers: [] },
    latest_scheduled_attempt: { available: false },
    future_run_gates: { available: false, items: [] }
  }, currentVerification, {});
  assert.equal(unknown.latest.tone, "unavailable");
  assert.equal(unknown.nextRun.tone, "unavailable");
});

test("GitHub Link pagination is detected before treating pull-request inventory as complete", () => {
  const { api } = loadApi();
  assert.equal(api.hasNextLink('<https://api.github.com/repositories/1/pulls?page=2>; rel="next", <https://api.github.com/repositories/1/pulls?page=4>; rel="last"'), true);
  assert.equal(api.hasNextLink('<https://api.github.com/repositories/1/pulls?page=1>; rel="prev"'), false);
});

test("typed booleans do not treat the string No as true", () => {
  const { api } = loadApi();
  assert.equal(api.explicitYes("Yes"), true);
  assert.equal(api.explicitYes("No"), false);
});

test("malformed Source Checker and Progress feeds fail runtime validation", () => {
  const { api } = loadApi();
  const source = {
    schema_version: 1,
    checked_at: "2026-07-25T10:00:00Z",
    eligible_urls: 1,
    counts: { verified: 1 },
    results: [{ source_id: "SRC-1", classification: "verified" }]
  };
  assert.equal(api.validateLivePayload("source-checker", source).valid, true);
  assert.equal(api.validateLivePayload("source-checker", {
    ...source,
    results: [...source.results, ...source.results]
  }).valid, false);
  assert.equal(api.validateLivePayload("progress", {
    schemaVersion: 2,
    generatedAt: "2026-07-25T10:00:00Z",
    metrics: { total: 2 },
    proposals: [{ identifier: "ISSUE-1" }]
  }).valid, false);
});

test("independent cloud-health and host-status payloads validate", () => {
  const { api } = loadApi();
  assert.equal(api.validateLivePayload("automation-health", {
    schema_version: 1,
    projection_kind: "cloud-automation-health",
    chain_id: "cloud-run-123",
    workflow_run_id: "123",
    status: "failed",
    updated_at: "2026-07-26T08:45:00Z"
  }).valid, true);
  assert.equal(api.validateLivePayload("host-status", {
    schema_version: 1,
    projection_kind: "host-run-status",
    chain_id: "arrp-20260726T064933Z",
    host_status: "failed",
    host_updated_at: "2026-07-26T08:43:00Z",
    stage: "elim-isolated-checkout",
    host_closeout: {
      outcome: "completed",
      commit: "a".repeat(40),
      validated_at: "2026-07-26T08:42:00Z"
    }
  }).valid, true);
  assert.equal(api.validateLivePayload("host-status", {
    schema_version: 1,
    projection_kind: "host-run-status",
    chain_id: "arrp-20260726T064933Z",
    host_status: "completed",
    host_updated_at: "2026-07-26T08:43:00Z",
    stage: "elim-closeout",
    host_closeout: { commit: "short" }
  }).valid, false);
  assert.equal(api.validateLivePayload("host-status", {
    schema_version: 1,
    projection_kind: "host-run-status",
    chain_id: "arrp-20260726T064933Z",
    host_status: "failed",
    host_updated_at: "not-a-timestamp",
    stage: "elim-isolated-checkout"
  }).valid, false);
});

test("newer published host state controls the final chain outcome while retaining cloud state", () => {
  const { api } = loadApi();
  const cloud = api.reconcileRunChainSnapshot({}, {
    schema_version: 1,
    chain_id: "arrp-20260726T064933Z",
    status: "complete",
    updated_at: "2026-07-26T06:56:00Z",
    elim_decision: { launch_recommended: true },
    failures: []
  }, "cloud");
  assert.equal(cloud.status, "host_pending");
  assert.equal(cloud.cloud_status, "complete");

  const failedHost = api.reconcileRunChainSnapshot(cloud, {
    schema_version: 1,
    projection_kind: "host-run-status",
    chain_id: "arrp-20260726T064933Z",
    host_status: "failed",
    host_updated_at: "2026-07-26T08:43:00Z",
    stage: "elim-isolated-checkout",
    host_action_items: [{ id: "incident-1", resolved: false }]
  }, "host");
  assert.equal(failedHost.status, "failed");
  assert.equal(failedHost.host_status, "failed");
  assert.equal(failedHost.cloud_status, "complete");
  assert.equal(failedHost.status_source, "published-host");
  assert.equal(failedHost.host_action_items.length, 1);

  const olderHost = api.reconcileRunChainSnapshot(failedHost, {
    schema_version: 1,
    projection_kind: "host-run-status",
    chain_id: "arrp-20260726T064933Z",
    host_status: "running",
    host_updated_at: "2026-07-26T08:00:00Z",
    stage: "elim-launch"
  }, "host");
  assert.equal(olderHost.status, "failed");
  assert.equal(olderHost.host_updated_at, "2026-07-26T08:43:00Z");
});

test("delivery aliases remain separate from proposal metrics", () => {
  const { api, data } = loadApi();
  data.progress = {
    metrics: { total: 81 },
    delivery_items: [{ id: "DEL-1" }, { id: "DEL-2" }]
  };
  assert.equal(api.deliveryItems().length, 2);
  assert.equal(data.progress.metrics.total, 81);
});

test("unavailable Integrity components do not imply zero and an available empty delivery feed shows zero", () => {
  const { api, data } = loadApi();
  assert.equal(api.integrityComponentValue({ state: "unavailable", complete: false }, 0), "Unavailable");
  assert.equal(api.integrityComponentValue({ state: "incomplete", complete: false }, 7), "Unavailable");
  assert.equal(api.integrityComponentValue({ state: "current", complete: true }, 0), 0);
  data.delivery_items = [];
  data.publication.release_readiness = { delivery_tasks: { available: true } };
  assert.equal(api.deliveryProjectionState().available, true);
  assert.equal(api.deliveryItems().length, 0);
});

test("operational readiness accepts an explicit failed legacy chain without calling it unavailable", () => {
  const { api } = loadApi();
  const state = api.operationalFeedState({
    chain_id: "arrp-20260726T140914Z",
    status: "failed",
    updated_at: "2026-07-26T14:20:00Z",
    failures: [{ stage: "elim" }]
  });
  assert.equal(state.state, "available");
  assert.equal(state.complete, true);
  assert.equal(api.integrityComponentValue(state, 1), 1);
  assert.equal(api.operationalFeedState({}).state, "undeclared");
});

test("host-recorded Elim runtime overrides a cloud decision that says it was not launched", () => {
  const { api } = loadApi();
  const presentation = api.elimRunChainPresentation({
    chain_id: "arrp-20260726T140914Z",
    elim_decision: {
      launch_recommended: false,
      reason: "Cloud decision was superseded by the host."
    },
    elim_runtime: {
      chain_id: "arrp-20260726T140914Z",
      status: "failed",
      summary: "Elim ran and was interrupted."
    }
  });
  assert.equal(presentation.label, "Failed");
  assert.equal(presentation.ran, true);
  assert.match(presentation.detail, /ran and was interrupted/i);
});

test("typed release blockers unite proposals, candidates, and delivery work without changing portfolio metrics", () => {
  const { api, data } = loadApi();
  data.active_horizon_records = [{
    id: "HOR-001",
    title: "Candidate blocker",
    issue_url: "https://github.com/Thorncrag/ARRP/issues/2"
  }];
  data.progress = {
    metrics: { total: 81 },
    proposals: [{
      identifier: "PRO-001",
      title: "Proposal blocker",
      kind: "proposal",
      releaseBlocker: "Yes",
      workflowStatus: "Development",
      priority: "High",
      owner: "Research",
      url: "https://github.com/Thorncrag/ARRP/issues/1"
    }, {
      identifier: "PRO-002",
      title: "Not a blocker",
      kind: "proposal",
      releaseBlocker: "No"
    }],
    candidates: [{
      identifier: "HOR-001",
      releaseBlocker: "true",
      workflowStatus: "Human decision needed",
      priority: "Critical",
      owner: "Human"
    }],
    delivery_items: [{
      identifier: "DEL-001",
      title: "Delivery blocker",
      kind: "task",
      releaseBlocker: true,
      workflowStatus: "Blocked",
      priority: "Normal",
      owner: "Automation",
      url: "https://github.com/Thorncrag/ARRP/issues/3"
    }],
    projectItemReconciliation: {
      releaseBlockers: 3,
      releaseBlockerFieldProjected: true
    }
  };
  data.publication = {
    release_readiness: {
      release_blockers: {
        available: true,
        count: 3,
        items: [{ identifier: "PRO-001", release_blocker: "Yes" }]
      }
    }
  };
  const blockers = api.releaseBlockerRecords();
  assert.equal(blockers.length, 3);
  assert.deepEqual([...new Set(blockers.map((record) => record.recordType))].sort(),
    ["Delivery work", "Formal candidate", "Proposal"]);
  assert.equal(api.releaseBlockerProjectionState(blockers).mismatch, false);
  assert.equal(data.progress.metrics.total, 81);
});

test("topic products require a typed mapping and preserve an explicit empty projection", () => {
  const { api, data } = loadApi();
  data.page_inventory = [{ path: "topics/example.md", title: "Example" }];
  data.publication = {};
  assert.equal(api.topicProducts(), undefined);
  data.publication.topic_products = [];
  assert.deepEqual(api.topicProducts(), []);
  data.publication.topic_products = [{ product_id: "topic-product:example" }];
  assert.equal(api.topicProducts()[0].product_id, "topic-product:example");
});

test("Pipeline deep links apply every managerial facet", () => {
  const { api } = loadApi();
  const state = api.applyPipelineParameters(
    "mode=hold&selected=ELEC-014&work_class=Proposal&scope=all&sort=due"
      + "&status=Blocked&development=Candidate&release_blocker=required"
      + "&workstream=ELEC&owner=Human&priority=Critical&gap=next_step_missing"
  );
  assert.deepEqual(JSON.parse(JSON.stringify({
    mode: state.mode,
    selectedId: state.selectedId,
    workClass: state.workClass,
    scope: state.scope,
    sort: state.sort,
    status: state.status,
    development: state.development,
    releaseBlocker: state.releaseBlocker,
    area: state.area,
    owner: state.owner,
    priority: state.priority,
    gap: state.gap
  })), {
    mode: "hold",
    selectedId: "ELEC-014",
    workClass: "Proposal",
    scope: "all",
    sort: "due",
    status: "Blocked",
    development: "Candidate",
    releaseBlocker: "required",
    area: "ELEC",
    owner: "Human",
    priority: "Critical",
    gap: "next_action_missing"
  });
});

test("browser exposes no narrative activity or capacity classifier", () => {
  const app = fs.readFileSync(appPath, "utf8");
  assert.doesNotMatch(app, /function elimImprovementRecords/);
  assert.doesNotMatch(app, /function elimUsageConsumption/);
  assert.doesNotMatch(app, /function allProblemRecords/);
  assert.doesNotMatch(app, /function stableProblemReference/);
});

test("Operations capacity state cannot interrupt Overview work-queue rendering", () => {
  const app = fs.readFileSync(appPath, "utf8");
  const capacityDefinition = app.indexOf("const capacityBlocked = Number.isFinite(capacityRemaining)");
  const operationsSummaryUse = app.indexOf(
    "incidentBlocking || chainBlockers.length > 0 || gateBlockers.length > 0 || capacityBlocked"
  );
  assert.notEqual(capacityDefinition, -1);
  assert.notEqual(operationsSummaryUse, -1);
  assert.ok(capacityDefinition < operationsSummaryUse);
  assert.match(
    app,
    /const capacityRemaining = privateUsageAvailable\s*\?\s*Number\(privateCodexUsageSnapshot\.current\.remaining_percent\)\s*:\s*null;/
  );
});

test("Overview renders only its immutable generated projection", () => {
  const app = fs.readFileSync(appPath, "utf8");
  const verificationStart = app.indexOf("function overviewBriefVerification(");
  const verificationEnd = app.indexOf("function overviewBriefFactStates(", verificationStart);
  const verification = app.slice(verificationStart, verificationEnd);
  const portalStart = app.indexOf("function renderOverviewPortals(");
  const portalEnd = app.indexOf("function serviceStatusLabel(", portalStart);
  const portals = app.slice(portalStart, portalEnd);
  const queueStart = app.indexOf("function renderOverviewQueues(");
  const queueEnd = app.indexOf("function overviewBriefVerification(", queueStart);
  const queues = app.slice(queueStart, queueEnd);
  assert.ok(verificationStart >= 0 && verificationEnd > verificationStart);
  assert.doesNotMatch(verification, /data\.(progress|integrity|source_checker)/);
  assert.match(portals, /data\.overview\?\.queue_directory/);
  assert.match(portals, /data\.overview\?\.data_directory/);
  assert.doesNotMatch(portals, /actionItemSnapshot|publicInputSnapshot/);
  assert.match(queues, /data\.overview\?\.queue_directory/);
  assert.doesNotMatch(queues, /data\.queue_directory|queue_counts/);
});

test("compact Overview activity renders only typed artifact-change fields", () => {
  const { api } = loadApi();
  const row = api.compactActivityPresentation({
    event_id: "SMR-1",
    occurred_at: "2026-07-25T22:17:40Z",
    artifact_label: "PR #381",
    producer: "Source Monitor",
    change_descriptor: "Recommendation recorded",
    artifact_ids: ["DIR-001", "DIR-002"],
    owner: "Human",
    route: "sources:watchers:directives"
  });
  assert.equal(row.title, "PR #381");
  assert.match(row.meta, /Source Monitor/);
  assert.doesNotMatch(row.meta, /Not recorded/);
  assert.equal(row.summary, "Recommendation recorded");
  assert.equal(row.target, "sources:watchers:directives");
  assert.equal(row.tone, "");
});

test("Overview material activity accepts only typed active issue score changes", () => {
  const { api } = loadApi();
  const rows = api.overviewMaterialActivityRecords([
    {
      event_id: "issue-older",
      occurred_at: "2026-07-20",
      event_code: "active_issue_score_changed",
      artifact_ids: ["TEST-001"],
      artifact_label: "TEST-001 · Test issue",
      change_descriptor: "T2 development audit",
      score_change: "60 → 70",
      canonical_record: "areas/TEST/issues/TEST-001.md"
    },
    {
      event_id: "issue-newer",
      occurred_at: "2026-07-24",
      event_code: "active_issue_score_changed",
      artifact_ids: ["TEST-002"],
      artifact_label: "TEST-002 · Newer issue",
      change_descriptor: "T3 readiness audit",
      score_change: "70 → 74",
      canonical_record: "areas/TEST/issues/TEST-002.md"
    },
    {
      event_id: "not-material",
      occurred_at: "2026-07-30",
      event_code: "content_product_changed",
      artifact_ids: [],
      change_descriptor: "General project update",
      score_change: "No score change.",
      canonical_record: "framework/README.md"
    }
  ]);
  assert.deepEqual(rows.map((row) => row.event_id), ["issue-newer", "issue-older"]);
  assert.equal(rows[0].artifact_label, "TEST-002 · Newer issue");
  assert.equal(rows[0].change_descriptor, "T3 readiness audit");
  assert.equal(rows[0].score_change, "70 → 74");
});

test("Overview loads its Change Audit domain and Capacity shows one unavailable notice", () => {
  const app = fs.readFileSync(appPath, "utf8");
  assert.match(
    app,
    /if \(tab === "overview"\) \{[\s\S]*?ensureDomain\("overview", \{ optional: true \}\)[\s\S]*?ensureDomain\("logs", \{ optional: true \}\)/
  );
  assert.match(app, /capacityHistory\.replaceChildren\(\);/);
  assert.doesNotMatch(
    app,
    /if \(capacityHistory && !privateUsageAvailable\) \{[\s\S]*?ownerModeUnavailableMessage\(CODEX_USAGE_UNAVAILABLE_DETAIL\)/
  );
});

test("Action Inbox uses a uniform selectable list with an adjacent preview", () => {
  const app = fs.readFileSync(appPath, "utf8");
  const html = fs.readFileSync(entrypointPath, "utf8");
  const styles = fs.readFileSync(path.join(consoleDirectory, "styles.css"), "utf8");
  const start = app.indexOf("function actionInboxRow(");
  const end = app.indexOf("function exactIntegrityProblemRecords(", start);
  const renderer = app.slice(start, end);
  assert.ok(start >= 0 && end > start);
  assert.match(renderer, /element\("button", "action-inbox-row"\)/);
  assert.match(renderer, /renderActionInboxPreview/);
  assert.match(renderer, /ACTION_INBOX_LAYOUT_STORAGE_KEY/);
  assert.doesNotMatch(renderer, /element\("details"/);
  assert.match(html, /data-action-filter="mine" aria-pressed="true"/);
  assert.match(html, /id="action-item-preview"/);
  assert.match(styles, /\.action-inbox-workspace\s*\{/);
  assert.match(styles, /\.action-inbox-row\[aria-pressed="true"\]/);
});

test("Priority attention is deterministic, human-owned, and capped at five", () => {
  const { api } = loadApi();
  const now = Date.parse("2026-07-28T15:00:00Z");
  const records = api.priorityAttentionItems([
    { id: "ordinary", scope: "mine", title: "Ordinary unresolved work" },
    { id: "oversight", scope: "oversight", title: "High elsewhere", priority: "Critical" },
    { id: "blocker", scope: "mine", title: "Explicit blocker", blockingEffect: true },
    { id: "critical", scope: "mine", title: "Critical record", priority: "Critical" },
    { id: "overdue", scope: "mine", title: "Overdue record", dueAt: "2026-07-27T12:00:00Z" },
    { id: "high", scope: "mine", title: "High record", priority: "High" },
    { id: "due", scope: "mine", title: "Due record", dueAt: "2026-07-29T12:00:00Z" },
    { id: "decision", scope: "mine", title: "Consequential decision", consequentialDecision: true }
  ], now);
  assert.equal(records.length, 5);
  assert.deepEqual(
    records.map((record) => record.item.id),
    ["blocker", "overdue", "critical", "high", "due"]
  );
  assert.ok(records.every((record) => record.item.scope === "mine"));
  assert.ok(records.every((record) => record.reasons.length > 0));
  assert.ok(!records.some((record) => record.item.id === "ordinary"));
  assert.ok(!records.some((record) => record.item.id === "oversight"));
});

test("Console-wide Design mode offers safe grid widths stored separately from project defaults", () => {
  const app = fs.readFileSync(appPath, "utf8");
  const html = fs.readFileSync(entrypointPath, "utf8");
  const styles = fs.readFileSync(path.join(consoleDirectory, "styles.css"), "utf8");
  assert.match(html, /id="layout-edit-toggle"[^>]*>Design layout</);
  assert.match(app, /const LAYOUT_WIDTHS = Object\.freeze/);
  assert.match(app, /layoutSizeKey/);
  assert.match(app, /setLayoutItemWidth/);
  assert.match(app, /moveLayoutItemToZone/);
  assert.match(app, /LAYOUT_PLACEMENTS_KEY/);
  assert.match(app, /layoutTransferGroup = "overview-portlet"/);
  assert.match(app, /"Project default"/);
  assert.match(app, /if \(!layoutEditing\) \{/);
  assert.match(app, /classList\?\.contains\("layout-handle"\)/);
  assert.match(styles, /\.layout-zone\.layout-size-zone/);
  assert.match(styles, /\.header-tools \.interface-tools-trigger\s*\{[^}]*position:\s*fixed[^}]*top:\s*\.75rem[^}]*right:\s*\.75rem/s);
  assert.doesNotMatch(styles, /body\.layout-editing #layout-edit-toggle/);
  assert.match(styles, /\.layout-container-select/);
  assert.match(styles, /\[data-layout-width="half"\]/);
  assert.match(styles, /\[data-layout-width="compact"\]/);
});

test("Planning and Operations consolidate navigation while preserving old routes", () => {
  const { api } = loadApi();
  const html = fs.readFileSync(entrypointPath, "utf8");
  const app = fs.readFileSync(appPath, "utf8");
  const styles = fs.readFileSync(path.join(consoleDirectory, "styles.css"), "utf8");
  const mainTabs = [...html.matchAll(/data-tab="([^"]+)"/g)].map((match) => match[1]);
  assert.deepEqual(mainTabs, [
    "overview",
    "actions",
    "progress",
    "planning",
    "integrity",
    "automation"
  ]);
  const planningTabs = [...html.matchAll(/data-subtab-group="planning" data-subtab="([^"]+)"/g)]
    .map((match) => match[1]);
  assert.deepEqual(planningTabs, [
    "workbench",
    "preliminary",
    "candidates",
    "sources",
    "publication"
  ]);
  const navigationStart = html.indexOf('<div class="console-navigation">');
  const workflowStart = html.indexOf('<section class="workflow-summary"');
  const planningPanelStart = html.indexOf('id="panel-planning"');
  const operationsPanelStart = html.indexOf('id="panel-automation"');
  const planningMenuStart = html.indexOf("planning-submenu");
  const operationsMenuStart = html.indexOf("operations-submenu");
  const planningWorkspaceStart = html.indexOf('id="planning-panel-workbench"');
  const operationsWorkspaceStart = html.indexOf('id="automation-panel-overview"');
  assert.ok(navigationStart >= 0 && navigationStart < workflowStart);
  assert.ok(planningMenuStart > planningPanelStart && planningMenuStart < planningWorkspaceStart);
  assert.ok(operationsMenuStart > operationsPanelStart && operationsMenuStart < operationsWorkspaceStart);
  assert.match(styles, /\.console-submenu\s*\{[^}]*width:\s*100%[^}]*margin:\s*0/s);
  assert.match(styles, /\.console-submenu\s*\{[^}]*border-top:\s*0[^}]*border-bottom:\s*1px solid #d7dee8[^}]*border-radius:\s*0/s);
  assert.match(styles, /#panel-planning > \.section-panel:not\(\[hidden\]\) > \.queue-view/);
  assert.match(styles, /#panel-automation > \.section-panel:not\(\[hidden\]\) > \.queue-view/);
  assert.ok(html.indexOf('class="pipeline-mode-switcher"') > planningPanelStart);
  assert.ok(html.indexOf('class="registry-mode-tabs"') > operationsPanelStart);
  assert.match(html, /data-subtab-group="automation" data-subtab="logs"/);
  assert.doesNotMatch(html, /data-tab="(?:candidates|sources|logs|publication)"/);
  assert.match(app, /initializeLogMenu/);
  assert.match(app, /operations-log-menu-button/);
  assert.match(html, /data-subtab="governance-changes"/);
  assert.match(app, /\["changes", "Change audits"\],\s*\["governance-changes", "Governance changes"\],\s*\["console-development", "Console development"\]/);
  assert.doesNotMatch(app, /operations-log-selector/);
  assert.match(app, /setNavigationMarker/);
  assert.match(styles, /\.tab-status-dot\.error/);
  assert.equal(api.normalizeConsoleTarget("candidates:formal"), "planning:candidates");
  assert.equal(api.normalizeConsoleTarget("candidates:public"), "planning:preliminary");
  assert.equal(api.normalizeConsoleTarget("sources:watchers:source-checker"), "planning:sources:watchers:source-checker");
  assert.equal(api.normalizeConsoleTarget("publication:builder"), "planning:publication:builder");
  assert.equal(api.normalizeConsoleTarget("planning:next-work"), "planning:workbench:pipeline");
  assert.equal(api.normalizeConsoleTarget("planning:pipeline"), "planning:workbench:pipeline");
  assert.equal(api.normalizeConsoleTarget("progress:next-work:status=Blocked"), "planning:workbench:pipeline:status=Blocked&mode=hold");
  assert.equal(api.normalizeConsoleTarget("progress:next-work:cohort=Human-reserved"), "actions");
  assert.equal(
    api.normalizeConsoleTarget("progress:next-work:cohort=External-review%20follow-up"),
    "planning:workbench:pipeline:status=External+review&scope=review-ready"
  );
  assert.equal(api.normalizeConsoleTarget("logs:integrity"), "automation:logs:integrity");
  assert.equal(api.normalizeConsoleTarget("automation:administration"), "automation:overview");
  assert.equal(api.normalizeConsoleTarget("automation:chain"), "automation:overview");
  assert.equal(api.normalizeConsoleTarget("automation:agents"), "automation:agents:run-coordinator-bot");
  assert.equal(
    api.normalizeConsoleTarget("operations:component-registry:documents?document=framework_kernel"),
    "automation:component-registry:documents?document=framework_kernel"
  );
  assert.equal(
    api.normalizeConsoleTarget("automation:component-registry:documents?document=framework_kernel"),
    "automation:component-registry:documents?document=framework_kernel"
  );
});

test("Stage 1 interface uses the approved prototype grammar while preserving behavior", () => {
  const html = fs.readFileSync(entrypointPath, "utf8");
  const styles = fs.readFileSync(path.join(consoleDirectory, "styles.css"), "utf8");
  const appJs = fs.readFileSync(appPath, "utf8");
  const consoleSpec = fs.readFileSync(path.join(consoleDirectory, "specification.md"), "utf8");
  assert.match(html, /styles\.css\?v=106/);
  assert.match(styles, /\.overview-section \.section-heading-row h3\s*\{\s*margin:\s*0 0 \.12rem;\s*\}/);
  assert.match(styles, /body\[data-interface-theme="arrp-tool"\]\s*\{/);
  assert.match(styles, /background:\s*#111d31/);
  assert.doesNotMatch(html, /prototype-note|Prototype status|Current prototype/);
  assert.match(consoleSpec, /### Current interface component grammar/);
  assert.match(consoleSpec, /The approved prototype is the controlling visual direction\./);
  assert.match(consoleSpec, /module_id: project_tool_interface/);
  assert.match(consoleSpec, /Approved by `@Thorncrag` on 2026-08-02/);
  assert.match(consoleSpec, /Search and primary filters remain visible together in one\s+functional-control surface\./);
  assert.match(consoleSpec, /A mail-style master\/detail result portal uses one bounded internally scrolling\s+list with one adjacent preview and does not also paginate\./);
  assert.match(styles, /width:\s*min\(1440px,\s*calc\(100% - 2rem\)\)/);
  assert.match(styles, /border-radius:\s*14px 14px 0 0/);
  assert.match(styles, /\.tab-list\s*\{[^}]*width:\s*max-content[^}]*min-width:\s*0/s);
  assert.match(styles, /\.tab-list button\s*\{[^}]*flex:\s*0 0 auto[^}]*min-width:\s*0/s);
  assert.match(styles, /border-bottom:\s*3px solid transparent/);
  assert.match(styles, /border-radius:\s*10px/);
  assert.match(styles, /\.overview-daily-brief\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1\.25fr\)\s*minmax\(28rem,\s*\.75fr\)[^}]*border-top:\s*4px solid var\(--blue\)/s);
  assert.match(styles, /\.overview-daily-facts\s*\{[^}]*grid-column:\s*2[^}]*grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*1fr\)\)/s);
  assert.match(styles, /\.overview-stage-strip\s*\{[^}]*grid-template-columns:\s*repeat\(7,\s*minmax\(8rem,\s*1fr\)\)[^}]*gap:\s*0/s);
  assert.match(styles, /\.overview-indicator-grid\s*\{[^}]*grid-template-columns:\s*repeat\(6,\s*minmax\(0,\s*1fr\)\)[^}]*gap:\s*\.7rem/s);
  assert.match(styles, /\.overview-queue-directory\s*\{[^}]*grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\)[^}]*gap:\s*\.55rem/s);
  assert.match(styles, /body\[data-interface-theme="arrp-tool"\] \.overview-lower-grid\s*\{[^}]*grid-template-columns:\s*repeat\(2, minmax\(0, 1fr\)\) !important/s);
  assert.match(styles, /\.overview-platform-indicator \.overview-status-grid,[\s\S]*\.overview-data-indicator \.overview-status-grid\s*\{[^}]*repeat\(5,\s*minmax\(0,\s*1fr\)\)[^}]*overflow:\s*hidden/s);
  assert.doesNotMatch(styles, /\.overview-platform-indicator \.overview-status-grid\s*\{[^}]*overflow-x:\s*auto/s);
  assert.match(appJs, /statusLabel:\s*"Not due"/);
  assert.match(styles, /\.overview-view\s*\{[^}]*border:\s*0[^}]*box-shadow:\s*none/s);
  assert.match(styles, /\.overview-view > \[data-layout-transfer-group="overview-portlet"\]\s*\{[^}]*margin-top:\s*0[^}]*margin-bottom:\s*1rem/s);
  assert.match(styles, /\.overview-lower-grid > \[data-layout-transfer-group="overview-portlet"\]\s*\{[^}]*margin-top:\s*0/s);
  assert.doesNotMatch(html, /Interface generated <time id="overview-generated-at"/);
  assert.match(html, /<div class="overview-supporting-data" hidden aria-hidden="true">\s*<time id="overview-generated-at">—<\/time>/s);
  assert.match(styles, /\.status-badge\s*\{[^}]*display:\s*inline-flex[^}]*border-radius:\s*999px[^}]*text-transform:\s*none/s);
  assert.match(styles, /\.status-badge::before\s*\{[^}]*border-radius:\s*50%[^}]*background:\s*currentColor[^}]*content:\s*""/s);
  assert.match(styles, /\.overview-queue-problem::before\s*\{[^}]*content:\s*"⚑"/s);
  assert.match(styles, /\.section-tabs:not\(\.console-submenu\) \.section-tab-list button,[\s\S]*border-radius:\s*999px/s);
  assert.match(styles, /\.pipeline-mode-switcher button\[aria-pressed="true"\],[\s\S]*background:\s*#193f70/s);
  assert.match(styles, /\.console-submenu\s*\{[^}]*width:\s*100%[^}]*border-bottom:\s*1px solid #d7dee8[^}]*border-radius:\s*0/s);
  assert.match(styles, /\.tab-list button:hover\s*\{[^}]*border-bottom-color:\s*#8da8ca[^}]*background:\s*#f2f6fb/s);
  assert.match(styles, /\.tab-list button\[aria-selected="true"\]\s*\{[^}]*border-bottom-color:\s*#193f70[^}]*font-weight:\s*850/s);
  assert.match(styles, /\.console-submenu \.section-tab-list button\[aria-selected="true"\]\s*\{[^}]*background:\s*rgba\(255,\s*255,\s*255,\s*\.62\)[^}]*box-shadow:\s*none[^}]*font-weight:\s*760/s);
  assert.match(styles, /\.operations-log-menu\s*\{[^}]*margin:\s*\.8rem 1\.35rem \.7rem[^}]*border-radius:\s*0/s);
  assert.match(styles, /#automation-panel-logs > \[id\^="log-panel-"\] \.log-view\s*\{[^}]*margin:\s*0 1\.35rem[^}]*border-radius:\s*10px/s);
  assert.match(styles, /#operations-security-summary\s*\{[^}]*grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\)[^}]*gap:\s*\.65rem/s);
  assert.match(styles, /#automation-panel-security \.queue-view-header > \.source-list\.compact-links\s*\{[^}]*width:\s*35rem[^}]*flex:\s*0 0 35rem[^}]*flex-wrap:\s*nowrap[^}]*justify-content:\s*flex-end[^}]*padding:\s*0/s);
  assert.match(styles, /#operations-security-list \.email-list-copy\s*\{[^}]*display:\s*grid[^}]*gap:\s*\.2rem/s);
  assert.match(styles, /#operations-security-preview > \.source-list\.compact-links\s*\{[^}]*padding:\s*\.35rem 0 0/s);
  assert.match(styles, /--console-surface-subtle:\s*#f7f9fc/);
  assert.match(styles, /--console-page-gutter:\s*1\.35rem/);
  assert.match(styles, /--console-tertiary-height:\s*2\.05rem/);
  assert.match(styles, /--console-tertiary-gap:\s*\.35rem/);
  assert.match(styles, /--console-control-height:\s*2\.25rem/);
  assert.match(styles, /\.queue-view-header \.refresh-note\s*\{[^}]*padding:\s*0[^}]*background:\s*transparent/s);
  assert.match(styles, /\.watcher-summary-card,[\s\S]*\.publication-metric,[\s\S]*#operations-security-summary \.compact-metric[\s\S]*background:\s*var\(--console-surface-subtle\)/s);
  assert.match(styles, /\.pipeline-view > \.pipeline-controls:not\(\.pipeline-controls-advanced\)\s*\{[^}]*margin-top:\s*\.55rem/s);
  assert.match(styles, /\.compact-empty\s*\{[^}]*margin:\s*\.75rem 0 0[^}]*padding:\s*\.9rem 1rem[^}]*border:\s*1px solid var\(--line\)[^}]*text-align:\s*left/s);
  assert.match(styles, /\.console-message\s*\{[^}]*width:\s*100%[^}]*padding:\s*\.58rem \.72rem[^}]*border-radius:\s*6px[^}]*text-align:\s*left/s);
  assert.match(styles, /\.console-message-info\s*\{[^}]*position:\s*relative[^}]*padding-left:\s*2rem[^}]*background:\s*var\(--console-surface-subtle\)/s);
  assert.match(styles, /\.console-message-info::before\s*\{[^}]*border-radius:\s*50%[^}]*content:\s*"i"[^}]*font-size:\s*\.58rem/s);
  assert.match(styles, /\.console-message-warning\s*\{[^}]*border-color:\s*#e7d49f[^}]*background:\s*#fff8e7/s);
  assert.match(styles, /\.console-message-warning::before,[\s\S]*content:\s*"!"/s);
  assert.match(styles, /\.owner-unavailable-notice\s*\{[^}]*border:\s*1px solid #e7d49f[^}]*background:\s*#fff8e7/s);
  assert.match(styles, /\.console-message-status\.success\s*\{[^}]*border-color:\s*#bedbc9[^}]*background:\s*#edf7f1/s);
  assert.match(styles, /\.console-message-status\.error\s*\{[^}]*border-color:\s*#e3c1bd[^}]*background:\s*#fff2f0/s);
  assert.match(styles, /\.console-message-status\.unavailable\s*\{[^}]*background:\s*var\(--console-surface-subtle\)/s);
  assert.match(styles, /\.console-message-status\.unavailable::before\s*\{[^}]*content:\s*"i"/s);
  assert.match(appJs, /note\.className = `attention-note console-message console-message-status \$\{/);
  assert.match(appJs, /host\.replaceChildren\(\);\s*host\.hidden = true;\s*return;/s);
  assert.match(appJs, /host\.hidden = false;/);
  assert.match(styles, /\.console-boundary-note\s*\{[^}]*border-top:\s*1px solid var\(--line\)[^}]*text-align:\s*center/s);
  assert.match(html, /<p class="console-boundary-note">Project data and automation status remain read-only here\./);
  assert.doesNotMatch(html, /<p class="method-note">Project data and automation status remain read-only here\./);
  assert.match(html, /<p class="refresh-note">Catalog generated <time id="sources-as-of" data-sources-as-of>—<\/time><\/p>/);
  assert.equal((html.match(/data-sources-as-of/g) || []).length, 3);
  assert.match(html, /<p class="method-note console-message console-message-info" id="sources-data-note">Loading the current source catalog projection…<\/p>/);
  assert.match(
    appJs,
    /const sourceCatalogCurrent = data\.availability === "current"\s*&& data\.completeness\?\.complete === true;/
  );
  assert.match(appJs, /Source catalog projection is current and complete for this Console generation\./);
  assert.match(html, /<header class="logs-screen-header" aria-labelledby="operations-logs-heading">[\s\S]*<h2 id="operations-logs-heading">Logs<\/h2>[\s\S]*complete operational, governance, audit, source, and Console-development histories/s);
  assert.match(styles, /\.logs-screen-header\s*\{[^}]*margin:\s*0 1\.35rem[^}]*padding:\s*1\.25rem 1\.35rem 0/s);
  assert.match(styles, /\.operations-ledger-row > div:first-child \.status-badge\s*\{[^}]*position:\s*absolute[^}]*top:\s*\.7rem[^}]*right:\s*\.7rem/s);
  assert.match(html, /class="inline-link section-heading-link" href="#automation:logs:agents">View history →<\/a>/);
  assert.match(html, /class="inline-link section-heading-link" href="#automation:agents:run-coordinator-bot">Open role details →<\/a>/);
  assert.match(styles, /\.section-heading-link\s*\{[^}]*align-self:\s*center[^}]*font-size:\s*\.7rem[^}]*text-underline-offset:\s*\.12em/s);
  assert.match(styles, /\.overview-stage-strip \.status-badge\s*\{[^}]*grid-column:\s*1[^}]*grid-row:\s*1[^}]*justify-self:\s*end/s);
  assert.match(html, />Repository Gates<\/button>/);
  assert.match(html, /<h2 id="operations-gates-heading">Repository Gates<\/h2>/);
  assert.match(styles, /#automation-panel-agents :where\([\s\S]*\.automation-role-workspace,[\s\S]*\.automation-role-unavailable[\s\S]*\)\s*\{[^}]*border:\s*0[^}]*background:\s*transparent/s);
  assert.match(html, /id="operations-platform-list" class="operations-ledger-list operations-portal-grid"/);
  assert.match(html, /id="operations-data-list" class="operations-ledger-list operations-portal-grid"/);
  assert.match(styles, /\.operations-portal-grid\s*\{[^}]*grid-template-columns:\s*repeat\(3,[^}]*gap:\s*\.65rem/s);
  assert.match(styles, /#automation-panel-data \.operations-portal-grid\s*\{[^}]*grid-template-columns:\s*repeat\(5,/s);
  assert.match(styles, /\.operations-portal-grid \.operations-ledger-row\s*\{[^}]*display:\s*flex[^}]*min-height:\s*9\.5rem[^}]*border-radius:\s*10px/s);
  assert.match(styles, /#automation-panel-logs > \[id\^="log-panel-"\] \.log-view\s*\{[^}]*margin-top:\s*0[^}]*border:\s*0[^}]*border-radius:\s*0/s);
  assert.match(styles, /#automation-panel-component-registry \.registry-mode-panel\s*\{[^}]*border:\s*0[^}]*background:\s*transparent/s);
  assert.match(styles, /#automation-panel-component-registry \.component-registry-detail\s*\{[^}]*border:\s*0[^}]*background:\s*transparent[^}]*box-shadow:\s*none/s);
  assert.match(styles, /#overview-chain-section > \.section-heading-row\s*\{[^}]*padding:\s*\.9rem 1rem/s);
  assert.match(styles, /\.overview-stage-strip \.overview-automation-card\s*\{[^}]*min-height:\s*7\.8rem[^}]*padding:\s*\.72rem \.75rem/s);
  assert.match(styles, /\.overview-stage-strip h4\s*\{[^}]*grid-row:\s*2[^}]*min-height:\s*2\.2rem[^}]*line-height:\s*1\.18/s);
  assert.match(styles, /\.overview-material-row\s*\{[^}]*grid-template-columns:\s*minmax\(0, 1fr\) auto auto/s);
  assert.match(styles, /\.overview-material-score\s*\{[^}]*grid-column:\s*2[^}]*font-variant-numeric:\s*tabular-nums/s);
  assert.match(styles, /\.overview-chain-readiness\s*\{[^}]*padding:\s*\.62rem 1rem/s);
  assert.match(styles, /\.action-priority-attention\s*\{[^}]*margin:\s*\.55rem 0 0[^}]*padding:\s*\.5rem \.65rem[^}]*box-shadow:\s*none/s);
  assert.match(styles, /\.action-priority-list\s*\{[^}]*grid-template-columns:\s*repeat\(auto-fit, minmax\(13rem, 1fr\)\)[^}]*margin-top:\s*\.4rem/s);
  assert.match(styles, /\.action-priority-row\s*\{[^}]*min-height:\s*0[^}]*flex-direction:\s*row[^}]*padding:\s*\.42rem \.52rem/s);
  assert.match(styles, /\.action-inbox-workspace\s*\{[^}]*min-height:\s*28rem/s);
  assert.match(styles, /\.action-inbox-row\s*\{[^}]*padding:\s*\.58rem \.68rem/s);
  assert.match(styles, /\.console-navigation\s*\{[^}]*background:\s*#f1f5fa/s);
  assert.match(styles, /\.console-submenu\s*\{[^}]*padding:\s*\.34rem 1\.35rem[^}]*background:\s*#f8fafc/s);
  assert.match(styles, /\.console-submenu \.section-tab-list button\s*\{[^}]*display:\s*inline-flex[^}]*align-items:\s*center[^}]*justify-content:\s*center[^}]*min-height:\s*2\.05rem[^}]*line-height:\s*1\.15/s);
  assert.match(html, /<\/div>\s*<\/div>\s*<p class="attention-note console-message console-message-warning" id="action-items-note">Loading review queues…<\/p>/s);
  assert.match(html, /id="preliminary-heading"[\s\S]*<\/div>\s*<\/div>\s*<p class="attention-note console-message console-message-warning" id="attention-note">/s);
  assert.match(styles, /#panel-planning > \.section-panel:not\(\[hidden\]\) > \.queue-view,[\s\S]*border:\s*0[\s\S]*border-radius:\s*0[\s\S]*box-shadow:\s*none/s);
  assert.match(styles, /\.source-workspace-menu,\s*\.publication-workspace-menu[\s\S]*margin:\s*\.8rem 1\.35rem 0[^}]*border-bottom:\s*1px solid var\(--line\)/s);
  assert.match(styles, /\.source-workspace-menu,\s*\.publication-workspace-menu[\s\S]*\.section-tab-list button\s*\{[^}]*min-width:\s*0[^}]*flex:\s*0 0 auto/s);
  assert.match(appJs, /initializeSectionTabs\("sources", "catalog"\)/);
  assert.match(appJs, /function placeSourceNavigation\(name\)/);
  assert.match(appJs, /if \(group === "sources"\) placeSourceNavigation\(selected\.dataset\.subtab\)/);
  assert.match(appJs, /function placePublicationNavigation\(name\)/);
  assert.match(appJs, /if \(group === "publication"\) placePublicationNavigation\(selected\.dataset\.subtab\)/);
  assert.match(appJs, /catalog: byId\("sources-heading"\)\?\.closest\("\.queue-view"\)/);
  assert.match(appJs, /const visible = ordered;/);
  assert.doesNotMatch(html, /data-disclosure-id="sources-catalog-results"/);
  assert.doesNotMatch(html, /data-disclosure-id="sources-exact-type-filter"/);
  assert.match(html, /class="queue-controls source-controls"[\s\S]*id="sources-exact-type"[\s\S]*<\/div>\s*<p class="result-count"/);
  assert.match(html, /<p class="result-count"><b id="sources-visible">0<\/b> sources match<\/p>\s*<div id="sources-table"><\/div>/);
  assert.doesNotMatch(html, /id="sources-pagination"/);
  assert.doesNotMatch(appJs, /pagination\(name, ordered\.length, state, rerender\)/);
  assert.match(styles, /\.source-view > \.source-workspace-menu,\s*body\[data-interface-theme="arrp-tool"\] \.queue-view > \.publication-workspace-menu\s*\{[^}]*margin:\s*\.8rem 0 \.75rem/s);
  assert.match(styles, /\.source-email-list\s*\{[^}]*scrollbar-gutter:\s*stable/s);
  assert.match(styles, /One tertiary-navigation rhythm across native buttons and link-backed tabs/);
  assert.match(styles, /\.compact-specialist-menu-item,[\s\S]*\.pipeline-mode-switcher button\s*\{[^}]*min-height:\s*var\(--console-tertiary-height\)[^}]*padding:\s*var\(--console-tertiary-padding\)/s);
  assert.match(styles, /#automation-panel-logs #operations-log-menu\s*\{[^}]*margin-top:\s*\.8rem[^}]*margin-bottom:\s*\.75rem[^}]*padding-right:\s*var\(--console-page-gutter\)[^}]*padding-left:\s*var\(--console-page-gutter\)/s);
  assert.match(styles, /:is\(\.tab-count, \.tab-update-count\)\[hidden\]\s*\{\s*display:\s*none;/);
  assert.match(appJs, /initializeSectionTabs\("publication", "assignments"\)/);
  assert.match(appJs, /\["sources", "publication"\]\.includes\(group\)/);
  assert.match(appJs, /activeSourceView === "watchers" && window\.location\.hash\.startsWith\("#planning:sources"\)/);
  assert.match(styles, /\.candidate-card > summary,[\s\S]*\.advanced-filters > summary[\s\S]*grid-template-columns:\s*auto minmax\(0,\s*1fr\) auto/s);
  assert.match(styles, /\.candidate-card > summary,[\s\S]*\.advanced-filters > summary[\s\S]*::before\s*\{[^}]*content:\s*"›"/s);
  assert.match(appJs, /function candidateSummaryTitle\(record\)/);
  assert.match(appJs, /header\.append\(element\("h3", "disclosure-item-name", candidateSummaryTitle\(record\)\), badges\)/);
  assert.match(appJs, /function standardizeDisclosureSummary\(summary, button\)/);
  assert.match(styles, /\.standard-disclosure-summary > \.disclosure-item-name\s*\{[^}]*text-overflow:\s*ellipsis[^}]*white-space:\s*nowrap/s);
  assert.doesNotMatch(html, /class="template-inspection"/);
  assert.match(html, /id="interface-tools-toggle"[^>]*aria-label="Interface tools\. No mode active\."[^>]*aria-expanded="false"[^>]*><svg class="interface-tools-icon" aria-hidden="true"[^>]*>[\s\S]*<\/svg><\/button>/);
  assert.match(styles, /\.interface-tools-icon\s*\{[^}]*width:\s*1\.28rem[^}]*stroke:\s*currentColor[^}]*stroke-width:\s*1\.9/s);
  assert.match(html, /id="interface-tools-drawer"[^>]*hidden/);
  assert.match(html, /id="template-inspection-toggle" aria-pressed="false">Show template boxes<\/button>/);
  assert.match(appJs, /function initializeInterfaceTools\(\)/);
  assert.match(appJs, /function setInterfaceToolsOpen\(open, restoreFocus = true\)/);
  assert.match(appJs, /function updateInterfaceToolsState\(\)/);
  assert.match(appJs, /event\.key !== "Escape"/);
  assert.match(appJs, /setInterfaceToolsOpen\(false\)/);
  assert.match(appJs, /function initializeTemplateInspection\(\)/);
  assert.match(appJs, /createTemplateRegionOverlay\(page, "A", "Metadata \+ date"/);
  assert.match(appJs, /createTemplateRegionOverlay\(page, "B", "Title \+ count"/);
  assert.match(appJs, /createTemplateRegionOverlay\(page, "D1", "Page-wide notice"/);
  assert.match(appJs, /`D\$\{index \+ 2\} · Subordinate notice`/);
  assert.match(appJs, /createTemplateRegionOverlay\(page, "F", "Tertiary navigation"/);
  assert.match(appJs, /createTemplateRegionOverlay\(page, "G", "Search \+ filters"/);
  assert.match(appJs, /createTemplateRegionOverlay\(page, "H", "Page content"/);
  assert.match(appJs, /page\.matches\("\.overview-view"\) \|\| page\.closest\("#automation-panel-overview"\)/);
  assert.match(appJs, /OV · Dashboard · A–H exempt/);
  assert.match(appJs, /\["H", "PRT", "Portal set"/);
  assert.match(appJs, /`\$\{code\}\$\{counts\[code\]\} · \$\{name\}`/);
  assert.match(appJs, /`\$\{region\}\.\$\{type\}\$\{counts\[type\]\} · \$\{name\}`/);
  assert.match(appJs, /"NAV", "Tertiary nav"/);
  assert.match(appJs, /"CTL", "Search \/ filters"/);
  assert.match(appJs, /"MSG", "Info \/ alert"/);
  assert.match(appJs, /"DSC", "Collapsible"/);
  assert.match(appJs, /"COL", "Results"/);
  assert.match(appJs, /:scope > \.pipeline-mode-switcher/);
  assert.match(appJs, /:scope > \.pipeline-advanced-filters/);
  assert.match(appJs, /\.pipeline-gap-notice, \.pipeline-context-notice/);
  assert.match(appJs, /const title = element\("span", "pipeline-row-title", candidateSummaryTitle\(record\)\)/);
  assert.match(appJs, /`\$\{record\.workClass\} · \$\{text\(record\.status, "Status unavailable"\)\}\$\{score\}`/);
  assert.doesNotMatch(html, /class="tab-count"[^>]*>—<\/span>/);
  assert.match(html, /Blocked &amp; deferred <span class="tab-count" id="pipeline-hold-mode-count">0<\/span>/);
  assert.match(html, /Monitored issues <span class="tab-count" id="manual-watch-count">0<\/span>/);
  assert.match(html, /id="tab-actions-count" hidden><\/span>/);
  assert.match(html, /id="assigned-actions-count" hidden><\/span>/);
  assert.match(html, /id="oversight-actions-count" hidden><\/span>/);
  assert.match(html, /id="all-actions-count" hidden><\/span>/);
  assert.match(appJs, /function setNavigationCount\(id, value, available\)/);
  assert.match(appJs, /const visible = available === true && Number\.isInteger\(value\) && value >= 0/);
  assert.match(appJs, /marker\.hidden = !visible/);
  assert.match(appJs, /marker\.textContent = visible \? String\(value\) : ""/);
  assert.match(appJs, /setNavigationCount\("tab-actions-count", total, complete\)/);
  assert.match(appJs, /setNavigationCount\("assigned-actions-count", total, complete\)/);
  assert.match(appJs, /setNavigationCount\("oversight-actions-count", oversightCount, complete\)/);
  assert.match(appJs, /setNavigationCount\("all-actions-count", actionInboxState\.items\.length, complete\)/);
  assert.match(styles, /\.template-region-overlay\s*\{[^}]*display:\s*none/s);
  assert.match(styles, /\.template-inspection \.template-region-overlay\s*\{[^}]*display:\s*block[^}]*position:\s*absolute[^}]*pointer-events:\s*none/s);
  assert.match(styles, /\.action-inbox-filters,[\s\S]*\.action-inbox-layout[\s\S]*\) button\s*\{[^}]*min-height:\s*1\.9rem[^}]*font-size:\s*\.68rem/s);
  assert.match(styles, /\.action-inbox-filters[\s\S]*:is\(\.tab-count, \.tab-update-count, button > span\)\s*\{[^}]*min-width:\s*1\.1rem[^}]*font-size:\s*\.56rem/s);
  assert.match(styles, /\.template-inspection \[data-template-region\]::after\s*\{[^}]*content:\s*attr\(data-template-region\)/s);
  assert.match(styles, /\.template-inspection \[data-template-component\]::before\s*\{[^}]*content:\s*attr\(data-template-component\)/s);
  assert.match(styles, /#panel-planning :where\(\s*\.candidate-card,\s*\.dense-data-disclosure,\s*\.monitoring-issue,\s*\.advanced-filters\s*\)[\s\S]*border-radius:\s*9px/s);
  assert.match(styles, /#panel-planning \.disclosure-default-toggle\s*\{[^}]*top:\s*\.68rem[^}]*transform:\s*none/s);
  assert.match(styles, /body\[data-interface-theme="arrp-tool"\] \.development-card\s*\{[^}]*display:\s*block/s);
  assert.match(styles, /\.development-card-main strong\s*\{[^}]*overflow:\s*visible[^}]*text-overflow:\s*clip/s);
  assert.match(styles, /\.development-card-links > a\s*\{[^}]*background:\s*transparent[^}]*text-decoration:\s*underline/s);
  assert.match(styles, /\.development-board-warning\[hidden\]\s*\{\s*display:\s*none !important;\s*\}/);
  assert.match(html, /class="development-board-viewport is-collapsed"[^>]*id="development-board-viewport"/);
  assert.match(html, /id="development-board-toggle"[^>]*aria-controls="development-board-viewport"[^>]*aria-expanded="false"/);
  assert.match(styles, /\.development-board-viewport\.is-collapsed\s*\{[^}]*max-height:\s*24rem[^}]*overflow:\s*hidden/s);
  assert.match(styles, /\.development-board-viewport\.is-collapsed::after\s*\{[^}]*linear-gradient/s);
  assert.match(appJs, /function initializeDevelopmentBoardToggle\(\)/);
  assert.match(appJs, /label\.textContent = expanded \? "Show fewer cards" : "Show full board"/);
  assert.doesNotMatch(html, /id="progress-holds-summary"|id="progress-monitoring"/);
  assert.match(html, /class="progress-header-meta"[\s\S]*Progress data as of[\s\S]*Open authoritative GitHub Project ↗/);
  assert.match(html, /id="workbench-monitoring-toggle"[^>]*aria-pressed="false"/);
  assert.match(html, /id="workbench-monitoring"[^>]*aria-labelledby="workbench-monitoring-heading"[^>]*hidden/);
  assert.match(appJs, /function setWorkbenchView\(view, updateRoute = false\)/);
  assert.match(appJs, /"progress" && parts\[1\] === "monitoring"[\s\S]*return "planning:workbench:monitoring"/);
  assert.match(appJs, /window\.location\.hash !== "#planning:workbench:monitoring"/);
  assert.match(appJs, /Array\.isArray\(record\.sources\) \? record\.sources\.length : 0/);
  assert.match(appJs, /internalInlineLink\("", workbenchTarget\)/);
  assert.match(appJs, /if \(score\.available\) \{/);
  assert.match(appJs, /linkButton\("Live ↗", liveUrl, true\)/);
  assert.match(appJs, /linkButton\("Issue ↗", record\.url, true\)/);
  assert.match(appJs, /data\.records\.length === 1 \? "requires" : "require"/);
  assert.match(styles, /#panel-actions > \.queue-view,[\s\S]*border:\s*0[\s\S]*box-shadow:\s*none/s);
  assert.match(styles, /\.action-inbox-toolbar\s*\{[^}]*border-bottom:\s*0[^}]*border-radius:\s*9px 9px 0 0/s);
  assert.match(styles, /\.action-inbox-workspace\s*\{[^}]*border-radius:\s*0 0 9px 9px[^}]*box-shadow:\s*none/s);
  assert.match(styles, /@media \(max-width:\s*980px\)/);
  assert.match(styles, /@media \(max-width:\s*720px\)/);
  assert.match(styles, /@media \(prefers-reduced-motion:\s*reduce\)/);
  assert.doesNotMatch(html, /https?:\/\/[^"]+\.(?:css|woff2?|ttf)(?:\?[^"]*)?"/i);
});

test("Workbench links resolve only typed planning artifacts and retain source context", () => {
  const { api } = loadApi({}, {
    progress: {
      pipeline: {
        items: [
          { id: "PROP-014", workClass: "Proposal", mode: "active" },
          { id: "HOR-031", workClass: "Formal candidate", mode: "hold" },
          { id: "SRC-009", workClass: "Source", mode: "active" }
        ]
      }
    }
  });

  assert.equal(
    api.workbenchTargetForArtifact("PROP-014", {
      source: "integrity",
      reference: "INT-014",
      returnTarget: "integrity"
    }),
    "planning:workbench:pipeline:selected=PROP-014&focus=1&source=integrity&ref=INT-014&return=integrity"
  );
  assert.equal(
    api.workbenchTargetForArtifact("HOR-031"),
    "planning:workbench:pipeline:selected=HOR-031&focus=1&mode=hold"
  );
  assert.equal(api.workbenchTargetForArtifact("SRC-009"), null);
  assert.deepEqual(
    api.structuredArtifactIdentifiers({
      artifact_id: "PROP-014",
      affected_ids: ["HOR-031", "FINDING-009"],
      message: "Narrative happens to mention PROP-999"
    }),
    ["PROP-014", "HOR-031"]
  );
});

test("Workbench navigation rejects hostile routes and external URLs", () => {
  const { api } = loadApi();
  assert.equal(api.safeConsoleTarget("integrity"), "integrity");
  assert.equal(
    api.safeConsoleTarget("planning:workbench:pipeline:status=Development"),
    "planning:workbench:pipeline:status=Development"
  );
  assert.equal(
    api.safeConsoleTarget(
      "automation:logs:security-incidents:selected=SEC-2026-001"
    ),
    "automation:logs:security-incidents:selected=SEC-2026-001"
  );
  assert.equal(api.decodeRouteSelection("INC-2026-001"), "INC-2026-001");
  assert.equal(api.decodeRouteSelection("%E0%A4%A"), "");
  assert.equal(api.decodeRouteSelection("INC-2026-001/../../x"), "");
  for (const hostile of [
    "javascript:alert(1)",
    "data:text/html,boom",
    "unknown:screen",
    "planning:unknown",
    "planning:workbench:pipeline:unknown=value",
    "automation:logs:security-incidents:selected=INC-2026-001",
    "automation:logs:security-incidents:selected=SEC-2026-001/../../x",
    "%E0%A4%A",
    `planning:workbench:pipeline:search=${"a".repeat(2100)}`,
    "integrity\u0000:overview"
  ]) {
    assert.equal(api.safeConsoleTarget(hostile), "overview");
  }

  assert.equal(
    api.safePipelineExternalUrl("https://github.com/Thorncrag/ARRP/issues/479"),
    "https://github.com/Thorncrag/ARRP/issues/479"
  );
  assert.equal(
    api.safePipelineExternalUrl(
      "https://github.com/Thorncrag/ARRP/blob/main/areas/TEST/issues/TEST-001.md#audit"
    ),
    "https://github.com/Thorncrag/ARRP/blob/main/areas/TEST/issues/TEST-001.md#audit"
  );
  for (const hostile of [
    "javascript:alert(1)",
    "data:text/html,boom",
    "//github.com/Thorncrag/ARRP/issues/479",
    "https://github.com.evil.test/Thorncrag/ARRP/issues/479",
    "https://github.com/Evil/ARRP/issues/479",
    "https://user:password@github.com/Thorncrag/ARRP/issues/479",
    "https://github.com:444/Thorncrag/ARRP/issues/479",
    "https://github.com/Thorncrag/ARRP/actions"
  ]) {
    assert.equal(api.safePipelineExternalUrl(hostile), null);
  }
});

test("typed Pipeline fails closed, preserves precedence, and uses deterministic ordering", () => {
  const items = [
    {
      id: "INTAKE-1",
      workClass: "Preliminary candidate",
      mode: "active",
      status: "Preliminary intake",
      readinessState: "not_applicable",
      nextActionState: "recorded",
      sortInputs: { classRank: 0, nextStepMissing: false, priorityRank: 99, identifier: "INTAKE-1" }
    },
    {
      id: "HOR-MISSING",
      workClass: "Formal candidate",
      mode: "active",
      status: "Development",
      readinessState: "not_applicable",
      nextActionState: "missing",
      sortInputs: { classRank: 1, nextStepMissing: true, priorityRank: 99, identifier: "HOR-MISSING" }
    },
    {
      id: "HOR-COMPLETE",
      workClass: "Formal candidate",
      mode: "active",
      status: "Development",
      readinessState: "not_applicable",
      nextActionState: "recorded",
      sortInputs: { classRank: 1, nextStepMissing: false, priorityRank: 99, identifier: "HOR-COMPLETE" }
    },
    {
      id: "PROP-0",
      workClass: "Proposal",
      mode: "active",
      status: "Development",
      readinessState: "not_ready",
      nextActionState: "recorded",
      score: 0,
      sortInputs: { classRank: 2, scoreDescending: 0, nextStepMissing: false, priorityRank: 99, identifier: "PROP-0" }
    },
    {
      id: "PROP-MISSING",
      workClass: "Proposal",
      mode: "active",
      status: "Development",
      readinessState: "not_ready",
      nextActionState: "recorded",
      score: null,
      sortInputs: { classRank: 2, scoreDescending: null, nextStepMissing: false, priorityRank: 99, identifier: "PROP-MISSING" }
    },
    {
      id: "PROP-READY",
      workClass: "Proposal",
      mode: "active",
      status: "External review",
      readinessState: "ready",
      nextActionState: "recorded",
      score: 80,
      sortInputs: { classRank: 2, scoreDescending: -80, nextStepMissing: false, priorityRank: 1, identifier: "PROP-READY" }
    },
    {
      id: "PROP-HOLD",
      workClass: "Proposal",
      mode: "hold",
      status: "Blocked",
      readinessState: "not_ready",
      nextActionState: "recorded",
      hold: { holdSince: "2026-07-01", provenanceState: "verified" },
      sortInputs: { classRank: 2, nextStepMissing: false, priorityRank: 1, identifier: "PROP-HOLD" }
    },
    {
      id: "PROP-HUMAN",
      workClass: "Proposal",
      mode: "human_action",
      status: "Human decision needed",
      readinessState: "not_ready",
      nextActionState: "recorded",
      sortInputs: { classRank: 2, nextStepMissing: false, priorityRank: 0, identifier: "PROP-HUMAN" }
    }
  ];
  const { api } = loadApi({}, {
    records: [],
    active_horizon_records: [],
    progress: {
      generation_id: "generation-1",
      proposals: items.filter((item) => item.workClass === "Proposal"),
      pipeline: {
        schemaVersion: 1,
        availability: "current",
        progressGenerationId: "generation-1",
        sourceCounts: { preliminaryCandidates: 0, formalCandidates: 0, proposals: 5 },
        items
      }
    }
  });
  assert.equal(api.pipelineProjectionState().available, true);
  api.applyPipelineParameters("mode=active&scope=active-development");
  const active = api.filteredPipelineItems(items);
  assert.deepEqual(
    active.map((item) => item.id),
    ["INTAKE-1", "HOR-COMPLETE", "HOR-MISSING", "PROP-0", "PROP-MISSING"]
  );
  assert.ok(!active.some((item) => item.id === "PROP-READY"));
  assert.ok(!active.some((item) => item.id === "PROP-HUMAN"));
  api.applyPipelineParameters("mode=hold");
  assert.deepEqual(api.filteredPipelineItems(items).map((item) => item.id), ["PROP-HOLD"]);

  const stale = loadApi({}, {
    records: [],
    active_horizon_records: [],
    progress: {
      generation_id: "generation-2",
      proposals: [],
      pipeline: {
        schemaVersion: 1,
        availability: "current",
        progressGenerationId: "older-generation",
        sourceCounts: { preliminaryCandidates: 0, formalCandidates: 0, proposals: 0 },
        items: []
      }
    }
  });
  assert.equal(stale.api.pipelineProjectionState().available, false);
});

test("initial HTML loads only bounded scripts and stays within declared budgets", () => {
  const html = fs.readFileSync(entrypointPath, "utf8");
  const app = fs.readFileSync(appPath, "utf8");
  const scriptSources = [...html.matchAll(/<script\s+src="([^"]+)"/g)].map((match) => match[1]);
  assert.deepEqual(scriptSources, [
    "catalog-data.js?v=49",
    "app.js?v=106"
  ]);
  assert.match(html, /styles\.css\?v=106/);
  assert.match(app, /const PRIVATE_SECURITY_ASSURANCE_PATH = "data\/private-security-assurance\.js\?v=1";/);
  assert.match(app, /const PRIVATE_OPERATIONS_PATH = "data\/private-operations\.js\?v=1";/);
  assert.match(app, /const PRIVATE_CODEX_USAGE_PATH = "data\/private-codex-usage\.js\?v=1";/);
  assert.match(app, /const LOCAL_AUTOMATION_STATUS_PATH = "data\/local-automation-status\.js";/);
  assert.match(app, /const CODEX_CAPACITY_MODULE_PATH = "capacity\.js\?v=1";/);
  assert.match(app, /const COMPONENT_REGISTRY_MODULE_VERSION = "11";/);
  assert.match(app, /return loadLocalProjection\(\s*PRIVATE_SECURITY_ASSURANCE_PATH,\s*"security-assurance",\s*capturePrivateSecurityAssurance\s*\)/);
  assert.match(app, /return loadLocalProjection\(\s*PRIVATE_OPERATIONS_PATH,\s*"private-operations",\s*capturePrivateOperations\s*\)/);
  assert.match(app, /return loadLocalProjection\(\s*PRIVATE_CODEX_USAGE_PATH,\s*"codex-usage",\s*capturePrivateCodexUsage\s*\)/);
  assert.match(app, /return loadScriptOnce\(CODEX_CAPACITY_MODULE_PATH\)/);
  assert.match(app, /return loadLocalProjection\(\s*LOCAL_AUTOMATION_STATUS_PATH,\s*"local-automation-status",\s*captureLocalAutomationStatus\s*\)/);
  assert.match(app, /if \(window\.__ARRP_CONSOLE_TEST_MODE__\) capturePrivateSecurityAssurance\(\);/);
  assert.doesNotMatch(app, /\n  capturePrivateSecurityAssurance\(\);/);
  assert.match(html, /data-initial-script-budget-kib="680"/);
  assert.match(html, /data-initial-dom-budget="2000"/);
  const bytes = ["catalog-data.js", "app.js"]
    .map((file) => fs.statSync(path.join(consoleDirectory, file)).size)
    .reduce((sum, size) => sum + size, 0);
  assert.ok(bytes <= 680 * 1024, `synchronous JavaScript is ${bytes} bytes`);
  const approximateElementCount = (html.match(/<[a-z][^!/][^>]*>/gi) || []).length;
  assert.ok(approximateElementCount <= 1500, `initial HTML has about ${approximateElementCount} elements`);
  assert.doesNotMatch(html, /<script\s+src="data\/(?:candidates|sources|progress|integrity|automation|logs|publication)/);
  assert.doesNotMatch(html, /private-security-assurance|private-operations|private-codex-usage|local-automation-status/);
  assert.doesNotMatch(html, /<script\s+src="capacity\.js/);
  assert.doesNotMatch(html, /<script\s+src="component-registry\.js/);
  assert.equal(fs.existsSync(path.join(consoleDirectory, "capacity.js")), true);
  assert.equal(fs.existsSync(componentRegistryPath), true);
  assert.doesNotMatch(html, /role="tabpanel"[^>]*tabindex="0"/);
  assert.match(html, /Recent material activity/);
  assert.match(html, /id="pages-pagination"/);
  assert.match(html, /id="court-watch-pagination"/);
  assert.match(html, /id="pipeline-development"/);
  assert.match(html, /id="pipeline-release-blocker"/);
  assert.match(html, /id="pipeline-area"/);
  assert.match(html, /id="pipeline-owner"/);
  assert.match(html, /id="pipeline-workspace"/);
  assert.doesNotMatch(html, /id="progress-next-work"/);
  assert.match(html, /id="proposed-monitoring"/);
  assert.match(html, /id="proposed-trigger"/);
  assert.match(html, /id="publication-release-blockers-list"/);
  assert.doesNotMatch(html, /id="tab-logs-count"/);
  assert.match(html, /id="tab-automation-count"/);
  assert.match(html, /id="automation-logs-incident-count"/);
  assert.match(html, /id="log-incidents-count"/);
  assert.match(html, /id="log-panel-incidents"/);
  assert.match(html, /id="log-security-incidents-count"/);
  assert.match(html, /id="log-panel-security-incidents"/);
  assert.match(app, /\["security-incidents", "Security incidents"\]/);
  assert.match(
    app,
    /if \(domain === "logs"\) \{[\s\S]*?renderIncidentLog\(\);[\s\S]*?renderSecurityLog\(\);[\s\S]*?\}/
  );
  assert.doesNotMatch(app, /renderSecurityIncidentLog\(\)/);
});

test("operational incidents remain typed, Action Items use supplied ownership, and unavailable is not zero", () => {
  const html = fs.readFileSync(entrypointPath, "utf8");
  assert.match(html, /id="automation-incident-count">—</);
  assert.match(html, /id="incident-log-visible">—</);
  assert.match(html, /id="security-incident-log-visible">—</);
  for (const id of [
    "local-automation-note",
    "operations-security-status",
    "incident-log-status",
    "security-incident-log-status"
  ]) {
    assert.match(
      html,
      new RegExp(`id="${id}"[^>]*>Data unavailable outside the bound owner-local Console\\.`)
    );
  }
  assert.doesNotMatch(html, /id="(?:automation-incident-count|incident-log-visible|security-incident-log-visible)">0</);
  const unavailable = loadApi({}, {
    operational_incidents: {
      availability: "unavailable",
      complete: false,
      unresolved_count: null,
      impact_state: "gray",
      reason: "producer unavailable",
      items: []
    }
  });
  assert.equal(unavailable.api.operationalIncidentProjection().complete, false);
  assert.equal(unavailable.api.operationalIncidentProjection().unresolvedCount, null);
  assert.deepEqual(unavailable.api.unresolvedOperationalIncidents(), []);

  const current = loadApi({}, {
    operational_incidents: {
      availability: "current",
      complete: true,
      unresolved_count: 2,
      impact_state: "red",
      active_links: {
        "automation-role:run-coordinator-bot": ["INC-2026-001"]
      },
      items: [
        {
          incident_id: "INC-2026-001",
          status: "open",
          impact: "blocking",
          owner: "Human"
        },
        {
          incident_id: "INC-2026-002",
          status: "monitoring",
          impact: "degraded",
          owner: "Elim"
        },
        {
          incident_id: "INC-2026-003",
          status: "resolved",
          impact: "blocking",
          owner: "Human"
        }
      ]
    }
  });
  assert.equal(current.api.operationalIncidentProjection().unresolvedCount, 2);
  assert.deepEqual(
    current.api.unresolvedOperationalIncidents().map((item) => item.incident_id),
    ["INC-2026-001", "INC-2026-002"]
  );
  assert.equal(current.api.incidentStatusPresentation(current.data.operational_incidents.items[0]).tone, "error");
  const partial = loadApi({}, {
    action_snapshot: {
      availability: "partial",
      complete: false,
      counts: { human: null, oversight: null, all_open: null },
      items: [
        {
          item_id: "incident:INC-2026-001",
          work_kind: "operational_incident",
          label: "Recorded operational incident",
          status: "open",
          owner: "Human",
          attention_class: "oversight",
          authority: "Operational Incidents projection",
          route: "automation:logs:incidents:selected=INC-2026-001"
        },
        {
          item_id: "security-incident:SEC-2026-001",
          work_kind: "security_incident",
          label: "Protected Security Incident",
          status: "Investigating",
          owner: "Elim",
          attention_class: "human",
          authority: "Owner-local Security Incidents projection",
          route: "automation:logs:security-incidents:selected=SEC-2026-001"
        }
      ]
    }
  });
  const typed = partial.api.incidentActionItems();
  assert.equal(typed.operationalHumanActions.length, 0);
  assert.equal(typed.operationalOversightActions.length, 1);
  assert.equal(typed.securityHumanActions.length, 1);
  assert.equal(partial.api.actionItemSnapshot().total, null);
  assert.equal(partial.api.producerProblemRecords().length, 2);
  const app = fs.readFileSync(appPath, "utf8");
  assert.doesNotMatch(app, /humanOwnsIncident/);
  assert.doesNotMatch(app, /unresolvedAutomationActionItems/);
});

test("Security Incidents retain separate count, lifecycle, and reciprocal typed links", () => {
  const unavailable = loadApi({}, {
    security_incidents: {
      schema_version: 1,
      authority: "owner-local-security-incidents",
      availability: "unavailable",
      complete: false,
      count: null,
      unresolved_count: null,
      items: [],
      reason_code: "owner-local-projection-required"
    }
  });
  assert.equal(unavailable.api.securityIncidentProjection().complete, false);
  assert.equal(unavailable.api.securityIncidentProjection().unresolvedCount, null);

  const current = loadApi({}, {
    security_incidents: {
      schema_version: 1,
      authority: "owner-local-security-incidents",
      availability: "current",
      complete: true,
      checked_at: "2026-07-29T12:00:00Z",
      count: 2,
      unresolved_count: 1,
      items: [
        {
          security_incident_id: "SEC-2026-002",
          status: "Investigating"
        },
        {
          security_incident_id: "SEC-2026-001",
          status: "Resolved"
        }
      ]
    },
    incident_relations: {
      schema_version: 1,
      authority: "owner-local-incident-relations",
      availability: "current",
      complete: true,
      checked_at: "2026-07-29T12:00:00Z",
      active_relations: [],
      relations: [],
      by_operational_incident: {
        "INC-2026-004": ["SEC-2026-002"]
      },
      by_security_incident: {
        "SEC-2026-002": ["INC-2026-004"]
      }
    }
  });
  assert.equal(current.api.securityIncidentProjection().unresolvedCount, 1);
  assert.deepEqual(
    current.api.securityIncidentRelations("SEC-2026-002"),
    ["INC-2026-004"]
  );
  assert.equal(
    current.api.securityIncidentStatusPresentation(
      current.data.security_incidents.items[0]
    ).tone,
    "error"
  );
  assert.equal(
    current.api.securityIncidentStatusPresentation(
      current.data.security_incidents.items[1]
    ).tone,
    "success"
  );
});

test("platform projection has five provider-neutral cells and exact scoped dependencies", () => {
  const { api } = loadApi();
  const checkedAt = "2026-07-28T20:00:00Z";
  const openai = api.platformProviderObservation(
    "openai",
    { components: [
      { id: "oa-gpts", name: "GPTs", status: "operational" },
      { id: "oa-codex", name: "Codex API", status: "degraded_performance" },
      { id: "oa-api", name: "Responses", status: "operational" }
    ] },
    { incidents: [] },
    checkedAt
  );
  const vercel = api.platformProviderObservation(
    "vercel",
    { components: [
      { id: "j7g76bfzc8hw", name: "CDN", status: "operational" },
      { id: "kgcsn9c73xzf", name: "Functions", status: "operational" },
      { id: "xxh50pzvy03x", name: "Firewall", status: "operational" },
      { id: "bc3cl3q4jn9m", name: "TLS Certificates", status: "operational" },
      { id: "7ckq6xr6nsbv", name: "Builds", status: "partial_outage" },
      { id: "hpqj1ys9gr78", name: "Git Integrations", status: "operational" },
      { id: "rsp3h37vv009", name: "AI Gateway", status: "major_outage" }
    ] },
    { incidents: [
      { id: "relevant", name: "Build delay", components: [{ id: "7ckq6xr6nsbv" }] },
      { id: "unrelated", name: "AI Gateway issue", components: [{ id: "rsp3h37vv009" }] }
    ] },
    checkedAt
  );
  const cloudflare = api.platformProviderObservation(
    "cloudflare",
    { components: [
      { id: "m4jywscr0n0k", name: "Turnstile", status: "operational" },
      { id: "unrelated-tunnel", name: "Cloudflare Tunnel", status: "major_outage" }
    ] },
    { incidents: [
      { id: "unrelated", name: "Tunnel issue", components: [{ id: "unrelated-tunnel" }] }
    ] },
    checkedAt
  );
  const cells = api.platformCellProjection({ openai, vercel, cloudflare });
  assert.deepEqual(cells.map((item) => item.label), [
    "GPTs", "Codex", "API platform", "Vercel", "Cloudflare Turnstile"
  ]);
  assert.equal(cells.find((item) => item.label === "Codex").status, "degraded_performance");
  assert.equal(cells.find((item) => item.label === "Vercel").status, "partial_outage");
  assert.deepEqual(vercel.incidents.map((item) => item.id), ["relevant"]);
  assert.equal(cells.find((item) => item.label === "Cloudflare Turnstile").status, "operational");
  assert.deepEqual(cloudflare.incidents, []);
});

test("Platform specialist view renders the five service identities as peer portals", () => {
  const app = fs.readFileSync(appPath, "utf8");
  const styles = fs.readFileSync(path.join(consoleDirectory, "styles.css"), "utf8");
  assert.match(app, /row\.classList\.add\("platform-service-card"\)/);
  assert.match(app, /prepend\(element\("span", "platform-provider-label", service\.provider\)\)/);
  assert.doesNotMatch(app, /if \(service\.provider !== priorProvider\)/);
  assert.match(styles, /#automation-panel-platform \.operations-portal-grid\s*\{[^}]*grid-template-columns:\s*repeat\(5, minmax\(12rem, 1fr\)\)[^}]*overflow-x:\s*auto/s);
});

test("Data specialist view renders the five principal feeds as peer portals", () => {
  const html = fs.readFileSync(entrypointPath, "utf8");
  const app = fs.readFileSync(appPath, "utf8");
  const styles = fs.readFileSync(path.join(consoleDirectory, "styles.css"), "utf8");
  assert.match(html, /Five peer feed portals with exact availability/);
  assert.match(app, /row\.classList\.add\("data-feed-card"\)/);
  assert.match(app, /if \(feed\.producer\) \{[\s\S]*"data-producer-label",\s*humanizeKey\(feed\.producer\)/);
  assert.doesNotMatch(app, /"Producer unavailable"/);
  assert.match(app, /producerLabel\.setAttribute\("aria-label", `Producer: \$\{feed\.producer\}`\)/);
  assert.match(app, /Trustworthy through \$\{formatOperationalDate\(feed\.trustworthy_through\)\}/);
  assert.match(app, /element\("div", "data-feed-actions"\)/);
  assert.match(styles, /#automation-panel-data \.operations-portal-grid\s*\{[^}]*grid-template-columns:\s*repeat\(5, minmax\(12rem, 1fr\)\)[^}]*overflow-x:\s*auto/s);
});

test("platform provider failures are isolated and retain last-valid identity", () => {
  const { api } = loadApi();
  const checkedAt = "2026-07-28T20:00:00Z";
  const priorCloudflare = api.platformProviderObservation(
    "cloudflare",
    { components: [{ id: "m4jywscr0n0k", name: "Turnstile", status: "operational" }] },
    { incidents: [] },
    checkedAt
  );
  const unavailableCloudflare = api.platformProviderObservation(
    "cloudflare",
    { components: [{ id: "m4jywscr0n0k", name: "Wrong name", status: "operational" }] },
    { incidents: [] },
    "2026-07-28T21:00:00Z",
    priorCloudflare
  );
  assert.equal(unavailableCloudflare.complete, false);
  assert.equal(unavailableCloudflare.aggregate, "unavailable");
  assert.equal(unavailableCloudflare.lastValid.checkedAt, checkedAt);
  assert.equal(api.platformStatusPresentation("under_maintenance").tone, "warning");
  assert.equal(api.platformStatusPresentation("major_outage").tone, "error");
  assert.equal(api.platformStatusPresentation("unavailable").tone, "unavailable");
});

test("platform sources are exact and advisory rendering does not create incidents", () => {
  const app = fs.readFileSync(appPath, "utf8");
  assert.match(app, /https:\/\/www\.vercel-status\.com\/api\/v2\/status\.json/);
  assert.match(app, /https:\/\/www\.vercel-status\.com\/api\/v2\/components\.json/);
  assert.match(app, /https:\/\/www\.cloudflarestatus\.com\/api\/v2\/components\.json/);
  assert.match(app, /m4jywscr0n0k/);
  assert.match(app, /row\.setAttribute\("aria-label", `\$\{service\.label\}: \$\{presentation\.label\}/);
  assert.doesNotMatch(app, /record_incident.*platform|createIncident.*platform/i);
});

test("local automation status distinguishes unavailable, running, failure, review, and success", () => {
  const { api } = loadApi();
  assert.deepEqual(api.localAutomationPresentation(null), {
    available: false,
    tone: "unavailable",
    label: "Unavailable",
    summary: "The optional ignored local status feed is not present; no health conclusion is inferred."
  });
  assert.equal(api.localAutomationPresentation({ status: "running", stage: "12_validate" }).label, "Running");
  assert.equal(api.localAutomationPresentation({ status: "failed" }).tone, "error");
  assert.equal(api.localAutomationPresentation({ status: "review-required" }).label, "Review required");
  assert.equal(api.localAutomationPresentation({ status: "completed" }).tone, "success");
  assert.equal(api.validLocalAutomationStatus({
    schema_version: "1.0",
    status: "completed",
    control_state: "paused",
    control_state_checked_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }), true);
  assert.equal(api.validLocalAutomationStatus({
    schema_version: "1.0",
    status: "unexpected",
    control_state: "paused",
    control_state_checked_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }), false);
  assert.equal(api.localAutomationPresentation({
    status: "completed",
    updated_at: "2020-01-01T00:00:00Z"
  }).label, "Stale");
});
