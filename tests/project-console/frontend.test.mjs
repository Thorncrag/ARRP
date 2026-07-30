import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const testDirectory = path.dirname(fileURLToPath(import.meta.url));
const consoleDirectory = path.resolve(testDirectory, "..");
const appPath = path.join(consoleDirectory, "app.js");
const componentRegistryPath = path.join(consoleDirectory, "component-registry.js");
const entrypointPath = path.join(consoleDirectory, "project-console.html");
const localRequire = createRequire(import.meta.url);
const testGenerationId = "project-console-test";
const testSourceRevision = "a".repeat(40);
const testVersionId = `${testGenerationId}-20260729T120000000000Z`;
const testOwnerPath = "/owner-console-fixture/review-copy/project-console.html";
const testStagedAt = "2026-07-29T12:00:00.000000Z";

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
      terminology: "automation:component-registry:terminology"
    },
    defaults: {
      mode: "documents",
      document: "framework_kernel",
      directory: "framework",
      routing: "profile:compact"
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
  const capacityModule = localRequire.resolve("../capacity.js");
  delete localRequire.cache[capacityModule];
  localRequire("../capacity.js");
  const componentRegistryModule = localRequire.resolve("../component-registry.js");
  delete localRequire.cache[componentRegistryModule];
  localRequire("../component-registry.js");
  const appModule = localRequire.resolve("../app.js");
  delete localRequire.cache[appModule];
  try {
    localRequire("../app.js");
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
  const { componentRegistryApi } = loadApi();
  const snapshot = componentRegistryFixture();
  assert.equal(componentRegistryApi.validSnapshot(snapshot), true);
  assert.equal(componentRegistryApi.pendingDisplay, "Classification pending — enforcement not active");
  assert.equal(componentRegistryApi.validSnapshot({ ...snapshot, inferred_taxonomy: [] }), false);
  assert.equal(componentRegistryApi.validSnapshot({
    ...snapshot,
    documents: [{
      ...snapshot.documents[0],
      browser_classification: "miscellaneous"
    }]
  }), false);
  assert.equal(componentRegistryApi.validSnapshot({
    ...snapshot,
    routing: {
      ...snapshot.routing,
      rules: [{ ...snapshot.routing.rules[0], rule_id: "ctxr.inv.unregistered" }, ...snapshot.routing.rules.slice(1)]
    }
  }), false);
  assert.equal(componentRegistryApi.validSnapshot({
    ...snapshot,
    routing: {
      ...snapshot.routing,
      rules: [{ ...snapshot.routing.rules[0], namespace: "browser_invented" }, ...snapshot.routing.rules.slice(1)]
    }
  }), false);
  assert.equal(componentRegistryApi.validSnapshot({
    ...snapshot,
    routing: {
      ...snapshot.routing,
      rule_counts: { ...snapshot.routing.rule_counts, selection: 16 }
    }
  }), false);
  assert.equal(componentRegistryApi.validSnapshot({
    ...snapshot,
    routing: {
      ...snapshot.routing,
      rules: [{ ...snapshot.routing.rules[0], rendered_text: "Producer-rendered text only.", browser_summary: "invented" }, ...snapshot.routing.rules.slice(1)]
    }
  }), false);
  assert.equal(componentRegistryApi.validSnapshot({
    ...snapshot,
    registry: {
      ...snapshot.registry,
      registry_status: "active",
      approval: {
        state: "known",
        value: "Owner activation verified"
      }
    },
    routing: { ...snapshot.routing, authoritative: true }
  }), false);
  const active = activeComponentRegistryFixture();
  assert.equal(componentRegistryApi.validSnapshot(active), true);
  [
    {
      ...active,
      registry: { ...active.registry, authoritative: true }
    },
    {
      ...active,
      registry: { ...active.registry, executable: true }
    },
    {
      ...active,
      registry: { ...active.registry, live_activation_verified: true }
    },
    {
      ...active,
      registry: { ...active.registry, predecessor_route_consulted: true }
    },
    {
      ...active,
      registry: {
        ...active.registry,
        live_activation: {
          state: "known",
          value: "Owner activation verified"
        }
      }
    },
    {
      ...active,
      registry: {
        ...active.registry,
        source_binding_sha256: {
          state: "known",
          value: "2".repeat(64)
        }
      }
    },
    {
      ...active,
      registry: {
        ...active.registry,
        activation_receipt: "must not enter the public Console"
      }
    },
    {
      ...active,
      routing: {
        ...active.routing,
        source_import: snapshot.routing.source_import
      }
    },
    {
      ...active,
      routing: {
        ...active.routing,
        predecessor_provenance: {
          ...active.routing.predecessor_provenance,
          historical_path: "framework/CONTEXT_ROUTING.md"
        }
      }
    },
    {
      ...active,
      routing: {
        ...active.routing,
        readable_representation: {
          ...active.routing.readable_representation,
          executable: true
        }
      }
    },
    {
      ...active,
      routing: {
        ...active.routing,
        authoritative: true
      }
    },
    {
      ...active,
      routing: {
        ...active.routing,
        selections: [{
          ...active.routing.selections[0],
          executable: true
        }, ...active.routing.selections.slice(1)]
      }
    },
    {
      ...active,
      routing: {
        ...active.routing,
        rules: [{
          ...active.routing.rules[0],
          source_provenance: snapshot.routing.rules[0].source_provenance
        }, ...active.routing.rules.slice(1)]
      }
    }
  ].forEach((invalid) => {
    assert.equal(componentRegistryApi.validSnapshot(invalid), false);
  });
  assert.equal(componentRegistryApi.validSnapshot({
    ...snapshot,
    registry: {
      ...snapshot.registry,
      registry_status: "active",
      approval: {
        state: "known",
        value: { owner_review_reference: "must not enter the Console" }
      }
    }
  }), false);
  assert.equal(componentRegistryApi.validSnapshot({
    ...snapshot,
    routing: {
      ...snapshot.routing,
      validation: { ...snapshot.routing.validation, valid: false }
    }
  }), false);
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
});

test("Component Registry uses only deferred module and generated-domain entrypoints", () => {
  const html = fs.readFileSync(entrypointPath, "utf8");
  const app = fs.readFileSync(appPath, "utf8");
  const module = fs.readFileSync(componentRegistryPath, "utf8");
  assert.doesNotMatch(html, /<script\s+src="component-registry\.js/);
  assert.doesNotMatch(html, /<script\s+src="data\/component-registry\.js/);
  assert.match(app, /const COMPONENT_REGISTRY_MODULE_PATH = "component-registry\.js\?v=1";/);
  assert.match(app, /`data\/component-registry\.js\?v=\$\{SCRIPT_VERSION\}`/);
  assert.match(app, /if \(source\.startsWith\("data\/"\)\) validateLoadedDomainScript\(source\);/);
  assert.doesNotMatch(module, /miscellaneous|uncategorized|infer(?:red)?_taxonomy/i);
});

test("Component Registry is an Operations subtab after Data and before Logs", () => {
  const html = fs.readFileSync(entrypointPath, "utf8");
  const dataIndex = html.indexOf('id="automation-tab-data"');
  const registryIndex = html.indexOf('id="automation-tab-component-registry"');
  const logsIndex = html.indexOf('id="automation-tab-logs"');
  assert.ok(dataIndex >= 0 && dataIndex < registryIndex && registryIndex < logsIndex);
  ["documents", "directories", "routing", "terminology"].forEach((mode) => {
    assert.match(html, new RegExp(`id="component-registry-mode-${mode}"`));
    assert.match(html, new RegExp(`id="component-registry-panel-${mode}"`));
  });
  assert.match(html, /Classification pending — enforcement not active/);
  assert.doesNotMatch(
    html.slice(
      html.indexOf('id="panel-overview"'),
      html.indexOf('id="panel-progress"')
    ),
    /component-registry/i
  );
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
  assert.match(app, /prepare_public_intake_state_request/);
  assert.match(app, /execution: "staged_request_only"/);
  assert.match(app, /mixed_state_response: "record_operational_incident"/);
  assert.match(app, /event\.key === "ArrowDown"/);
  assert.doesNotMatch(app, /arbitrary_command_execution"\]\s*,?\s*commands:/);
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

test("Action Inbox uses a uniform selectable list with an adjacent preview", () => {
  const app = fs.readFileSync(appPath, "utf8");
  const html = fs.readFileSync(entrypointPath, "utf8");
  const styles = fs.readFileSync(path.join(consoleDirectory, "styles.css"), "utf8");
  const start = app.indexOf("function actionInboxRow(");
  const end = app.indexOf("function integrityFindingNeedsHuman(", start);
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
  assert.match(styles, /body\.layout-editing #layout-edit-toggle/);
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
    "catalog-data.js?v=48",
    "app.js?v=65"
  ]);
  assert.match(app, /const PRIVATE_SECURITY_ASSURANCE_PATH = "data\/private-security-assurance\.js\?v=1";/);
  assert.match(app, /const PRIVATE_OPERATIONS_PATH = "data\/private-operations\.js\?v=1";/);
  assert.match(app, /const PRIVATE_CODEX_USAGE_PATH = "data\/private-codex-usage\.js\?v=1";/);
  assert.match(app, /const LOCAL_AUTOMATION_STATUS_PATH = "data\/local-automation-status\.js";/);
  assert.match(app, /const CODEX_CAPACITY_MODULE_PATH = "capacity\.js\?v=1";/);
  assert.match(app, /const COMPONENT_REGISTRY_MODULE_PATH = "component-registry\.js\?v=1";/);
  assert.match(app, /return loadLocalProjection\(\s*PRIVATE_SECURITY_ASSURANCE_PATH,\s*"security-assurance",\s*capturePrivateSecurityAssurance\s*\)/);
  assert.match(app, /return loadLocalProjection\(\s*PRIVATE_OPERATIONS_PATH,\s*"private-operations",\s*capturePrivateOperations\s*\)/);
  assert.match(app, /return loadLocalProjection\(\s*PRIVATE_CODEX_USAGE_PATH,\s*"codex-usage",\s*capturePrivateCodexUsage\s*\)/);
  assert.match(app, /return loadScriptOnce\(CODEX_CAPACITY_MODULE_PATH\)/);
  assert.match(app, /return loadLocalProjection\(\s*LOCAL_AUTOMATION_STATUS_PATH,\s*"local-automation-status",\s*captureLocalAutomationStatus\s*\)/);
  assert.match(app, /if \(window\.__ARRP_CONSOLE_TEST_MODE__\) capturePrivateSecurityAssurance\(\);/);
  assert.doesNotMatch(app, /\n  capturePrivateSecurityAssurance\(\);/);
  assert.match(html, /data-initial-script-budget-kib="655"/);
  assert.match(html, /data-initial-dom-budget="1500"/);
  const bytes = ["catalog-data.js", "app.js"]
    .map((file) => fs.statSync(path.join(consoleDirectory, file)).size)
    .reduce((sum, size) => sum + size, 0);
  assert.ok(bytes <= 655 * 1024, `synchronous JavaScript is ${bytes} bytes`);
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
