(function (global) {
  "use strict";

  const MODES = Object.freeze([
    "documents",
    "directories",
    "routing",
    "relationships",
    "terminology"
  ]);
  const PENDING_DISPLAY = "Classification pending — enforcement not active";
  const TYPED_STATES = new Set([
    "known",
    "pending",
    "not_applicable",
    "none",
    "unknown",
    "unavailable"
  ]);
  const fieldSet = (value) => new Set(value.split(" "));
  const TOP_FIELDS = fieldSet(
    "schema_version projection_id producer_id generated_at availability complete reason_code routes defaults registry deferred documents directories relationships routing activation_readiness terminology"
  );
  const LEGACY_TOP_FIELDS = fieldSet(
    "schema_version projection_id producer_id generated_at availability complete reason_code routes defaults registry deferred documents directories routing activation_readiness terminology"
  );
  const ROUTE_FIELDS = fieldSet("documents directories routing relationships terminology");
  const LEGACY_ROUTE_FIELDS = fieldSet("documents directories routing terminology");
  const DEFAULT_FIELDS = fieldSet("mode document directory routing relationship");
  const LEGACY_DEFAULT_FIELDS = fieldSet("mode document directory routing");
  const REGISTRY_FIELDS = fieldSet(
    "registry_id registry_revision registry_status approval configuration_validation live_activation validation_mode authoritative executable live_activation_verified predecessor_route_consulted registry_sha256 repository_revision source_binding_sha256"
  );
  const DEFERRED_FIELDS = fieldSet(
    "display_state reason activation_requirement namespaces"
  );
  const NAMESPACE_FIELDS = fieldSet(
    "namespace schema_version activation_state complete enforced entry_count"
  );
  const DOCUMENT_FIELDS = fieldSet(
    "document_id official_reference_name document_class revision current_status effective_date approval_date approval_method governance_change_id purpose_scope authority_role authority_exclusions canonical_path owner review_policy disclosure_class creation_provenance governance_revision producer authorized_writers representations dependencies consumers digest_policy sha256 console_route retention_posture history"
  );
  const DIRECTORY_FIELDS = fieldSet(
    "scope_id display_name path_pattern match_kind specificity_rank parameter_bindings owning_scope_selection_rule ancestor_scope_ids placement_question include_when exclude_when primary_authority disclosure_boundary lifecycle_posture authorized_creators precedence fallback console_route permitted_artifact_classes current_artifact_count"
  );
  const RELATIONSHIP_FIELDS = fieldSet(
    "relationship_id relationship_type from to authority_boundary console_route"
  );
  const RELATIONSHIP_ENDPOINT_FIELDS = fieldSet("kind id");
  const REGISTRY_RELATIONSHIP_FIELDS = fieldSet(
    "relationship_id relationship_type from to authority_boundary"
  );
  const PARAMETER_FIELDS = fieldSet("allowed_values");
  const ROUTING_FIELDS = fieldSet(
    "schema_version rule_catalog_version activation_state complete authoritative source_import predecessor_provenance readable_representation expected_counts parity_policy required_modules generated_path_exclusions documents capabilities profiles selections rule_namespaces rule_counts rules validation"
  );
  const SOURCE_IMPORT_FIELDS = fieldSet(
    "path sha256 schema_version import_semantics"
  );
  const COUNT_FIELDS = fieldSet(
    "documents governing_documents capabilities profiles required_modules generated_path_exclusions"
  );
  const ROUTING_DOCUMENT_FIELDS = fieldSet(
    "document_id path governing hash_policy sha256 requires"
  );
  const CAPABILITY_FIELDS = fieldSet("capability_id document_ids");
  const PROFILE_FIELDS = fieldSet(
    "profile_id max_bytes modules capabilities include_all_governing sections"
  );
  const SECTION_FIELDS = fieldSet("document heading max_bytes");
  const SELECTION_FIELDS = fieldSet(
    "selection_id selection_kind executable authoritative live_activation_verified profile capabilities max_bytes sections modules console_route"
  );
  const MODULE_FIELDS = fieldSet(
    "id path governing hash_policy sha256 authority_role authority_scope authority_exclusions dependencies inclusion_reasons"
  );
  const VALIDATION_FIELDS = fieldSet(
    "valid source_sha256 registry_route_sha256 counts differences document_ids_equal profile_ids_equal capability_ids_equal"
  );
  const READABLE_REPRESENTATION_FIELDS = fieldSet(
    "state representation_id source_registry_revision authority_effect executable"
  );
  const RULE_NAMESPACE_COUNTS = Object.freeze({
    invariants: 7,
    selection: 17,
    validation: 10,
    failure_rules: 10,
    currentness: 6,
    budgets: 4,
    comprehensive_review: 10
  });
  // This is a closed wire-format allowlist, not a presentation taxonomy. The
  // producer supplies all display wording and membership remains invalid when
  // an unregistered wire identity appears.
  const RULE_IDS_BY_NAMESPACE = Object.freeze({
    invariants: [
      "ctxr.inv.router_preserves_source_authority", "ctxr.inv.required_floor_is_minimum",
      "ctxr.inv.additive_union", "ctxr.inv.dependencies_are_directional_minimums",
      "ctxr.inv.dependency_graph_is_acyclic", "ctxr.inv.stable_document_identity_is_path_independent",
      "ctxr.inv.bounded_context_never_omits_material_authority"
    ],
    selection: [
      "ctxr.sel.primary_profile", "ctxr.sel.required_floor_order", "ctxr.sel.profile_starting_set",
      "ctxr.sel.all_implicated_capabilities", "ctxr.sel.profile_never_excludes_capability",
      "ctxr.sel.capability_addition_requires_no_new_profile", "ctxr.sel.profile_documents_and_exact_sections",
      "ctxr.sel.complete_dependency_closure", "ctxr.sel.task_specific_canonical_material",
      "ctxr.sel.source_projection_requires_canonical_readback", "ctxr.sel.dynamic_trigger_set",
      "ctxr.sel.expansion_precedes_dependent_action", "ctxr.sel.multi_agent_before_delegation",
      "ctxr.sel.governance_recording_plus_change_audit", "ctxr.sel.interactive_route_is_minimum_not_ceiling",
      "ctxr.sel.automated_expansion_allowlist", "ctxr.sel.deterministic_bot_structured_inputs"
    ],
    validation: [
      "ctxr.val.registry_before_selection", "ctxr.val.integration_pinned_digest_exact",
      "ctxr.val.runtime_digest_at_packet_build", "ctxr.val.expansion_provenance_preserved",
      "ctxr.val.exact_section_unique", "ctxr.val.packet_manifest_bound",
      "ctxr.val.authorized_digest_update_atomic", "ctxr.val.registry_digest_external",
      "ctxr.val.new_authoritative_module_admission", "ctxr.val.id_rename_change_audit"
    ],
    failure_rules: [
      "ctxr.fail.unknown_or_missing_selection", "ctxr.fail.pinned_digest_absent_or_stale",
      "ctxr.fail.runtime_digest_unreadable", "ctxr.fail.dependency_cycle",
      "ctxr.fail.generated_or_excluded_as_authority", "ctxr.fail.section_identity_invalid",
      "ctxr.fail.section_budget_exceeded", "ctxr.fail.packet_budget_exceeded",
      "ctxr.fail.unresolved_material_governing_gap", "ctxr.fail.safe_failure_disposition"
    ],
    currentness: [
      "ctxr.cur.stable_governing_is_pinned", "ctxr.cur.mutable_handoff_is_runtime_hashed",
      "ctxr.cur.checkpoint_update_needs_no_registry_edit", "ctxr.cur.generated_rebuildables_excluded",
      "ctxr.cur.records_excluded_except_handoff", "ctxr.cur.runtime_nongoverning_excluded_from_review_boundary"
    ],
    budgets: [
      "ctxr.budget.profile_max_is_fail_closed_ceiling", "ctxr.budget.ceiling_change_does_not_change_membership",
      "ctxr.budget.section_and_packet_limits_are_independent", "ctxr.budget.no_mandatory_trimming"
    ],
    comprehensive_review: [
      "ctxr.review.select_all_active_governing", "ctxr.review.periodic_epoch_required",
      "ctxr.review.boundary_exact", "ctxr.review.any_valid_boundary_difference_due",
      "ctxr.review.invalid_drift_is_integrity_failure", "ctxr.review.completion_fields_exact",
      "ctxr.review.recorder_requires_exact_current_boundary", "ctxr.review.unresolved_findings_carry_forward",
      "ctxr.review.next_epoch_uses_delta_and_carry_forward", "ctxr.review.efficiency_never_limits_scope_or_lookback"
    ]
  });
  const RULE_NAMESPACES = Object.freeze(Object.keys(RULE_NAMESPACE_COUNTS));
  let boundRelationships = null;
  const RULE_BASE_FIELDS = fieldSet(
    "namespace rule_id rule_version status predicate_type parameters label rendered_text source_provenance verification_ids console_route"
  );
  const RULE_FAILURE_FIELDS = fieldSet(
    "namespace rule_id rule_version status predicate_type parameters label rendered_text failure_code source_provenance verification_ids console_route"
  );
  const RULE_PROVENANCE_FIELDS = fieldSet(
    "source_document_id source_sha256 source_heading clause_key"
  );
  const TERMINOLOGY_FIELDS = fieldSet(
    "available complete activation_state reason entries console_route"
  );
  const READINESS_FIELDS = fieldSet(
    "available complete activation_state authoritative executable registry_revision registry_sha256 current_candidate_counts simulated_active_counts requirement_count exception_count stage_boundaries activation_decision"
  );
  const READINESS_COUNT_FIELDS = fieldSet(
    "documents governing_documents capabilities profiles required_modules generated_path_exclusions rules"
  );
  const READINESS_BOUNDARY_FIELDS = fieldSet(
    "artifact_classes artifact_families artifact_lifecycles terminology repository_reference_mutation"
  );

  function plainObject(value) {
    return Boolean(value)
      && typeof value === "object"
      && !Array.isArray(value);
  }

  function exactFields(value, fields) {
    if (!plainObject(value)) return false;
    const keys = Object.keys(value);
    return keys.length === fields.size && keys.every((key) => fields.has(key));
  }

  function exactFieldsOneOf(value, options) {
    return options.some((fields) => exactFields(value, fields));
  }

  function string(value) {
    return typeof value === "string" && value.length > 0;
  }

  function integer(value, minimum = 0) {
    return Number.isInteger(value) && value >= minimum;
  }

  function stringArray(value) {
    return Array.isArray(value)
      && value.every(string)
      && new Set(value).size === value.length;
  }

  function digest(value) {
    return typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
  }

  function typedValue(value) {
    if (!plainObject(value) || !TYPED_STATES.has(value.state)) return false;
    if (value.state === "known") {
      return exactFields(value, fieldSet("state value"))
        && (
          string(value.value)
          || Number.isInteger(value.value)
          || typeof value.value === "boolean"
        );
    }
    return exactFields(value, fieldSet("state reason")) && string(value.reason);
  }

  function validRoute(value, mode) {
    return value === `automation:component-registry:${mode}`;
  }

  function validSelectionRoute(value, mode, key, identity) {
    if (!string(value)) return false;
    const [path, query = ""] = value.split("?", 2);
    if (path !== `automation:component-registry:${mode}`) return false;
    const parameters = new URLSearchParams(query);
    return [...parameters.keys()].length === 1
      && parameters.get(key) === identity;
  }

  function validRoutingRuleRoute(value, identity) {
    return validSelectionRoute(value, "routing", "rule", identity);
  }

  function validDocumentRoute(value, identity) {
    if (!string(value)) return false;
    const [path, query = ""] = value.split("?", 2);
    if (path !== "operations:component-registry:documents") return false;
    const parameters = new URLSearchParams(query);
    return [...parameters.keys()].length === 1
      && parameters.get("document") === identity;
  }

  function validRelationshipRoute(value, identity) {
    return validSelectionRoute(value, "relationships", "relationship", identity);
  }

  function validRelationshipEndpoint(value) {
    return exactFields(value, RELATIONSHIP_ENDPOINT_FIELDS)
      && string(value.kind)
      && string(value.id);
  }

  function validRelationship(value) {
    return exactFields(value, RELATIONSHIP_FIELDS)
      && string(value.relationship_id)
      && string(value.relationship_type)
      && validRelationshipEndpoint(value.from)
      && validRelationshipEndpoint(value.to)
      && string(value.authority_boundary)
      && validRelationshipRoute(value.console_route, value.relationship_id);
  }

  function canonicalValue(value) {
    if (Array.isArray(value)) return value.map(canonicalValue);
    if (!plainObject(value)) return value;
    return Object.fromEntries(
      Object.keys(value).sort().map((key) => [key, canonicalValue(value[key])])
    );
  }

  async function sha256(value) {
    const bytes = new TextEncoder().encode(value);
    const result = await global.crypto.subtle.digest("SHA-256", bytes);
    return [...new Uint8Array(result)]
      .map((byte) => byte.toString(16).padStart(2, "0"))
      .join("");
  }

  async function loadBoundRelationships(snapshot) {
    return Array.isArray(snapshot?.relationships)
      ? snapshot.relationships
      : [];
  }

  function validRegistry(value) {
    if (!exactFields(value, REGISTRY_FIELDS)) return false;
    if (!string(value.registry_id)
      || !integer(value.registry_revision, 1)
      || !["candidate", "active"].includes(value.registry_status)
      || !typedValue(value.approval)
      || !typedValue(value.configuration_validation)
      || !typedValue(value.live_activation)
      || ![
        "candidate_validation_only",
        "active_configuration_validation_only"
      ].includes(value.validation_mode)
      || value.authoritative !== false
      || value.executable !== false
      || value.live_activation_verified !== false
      || typeof value.predecessor_route_consulted !== "boolean"
      || !digest(value.registry_sha256)
      || !/^[0-9a-f]{40}(?:[0-9a-f]{24})?$/.test(value.repository_revision)
      || !typedValue(value.source_binding_sha256)) return false;
    if (value.registry_status === "candidate") {
      return value.validation_mode === "candidate_validation_only"
        && value.approval.state === "pending"
        && value.configuration_validation.state === "known"
        && value.configuration_validation.value
          === "Candidate predecessor parity validated"
        && value.live_activation.state === "pending"
        && value.predecessor_route_consulted === true
        && value.source_binding_sha256.state === "known"
        && digest(value.source_binding_sha256.value);
    }
    return value.validation_mode
        === "active_configuration_validation_only"
      && value.approval.state === "known"
      && value.approval.value
        === "Tracked activation configuration approved"
      && value.configuration_validation.state === "known"
      && value.configuration_validation.value
        === "Tracked active configuration validated"
      && value.live_activation.state === "unknown"
      && value.predecessor_route_consulted === false
      && value.source_binding_sha256.state === "not_applicable";
  }

  function validDeferred(value) {
    if (!exactFields(value, DEFERRED_FIELDS)
      || value.display_state !== PENDING_DISPLAY
      || !string(value.reason)
      || !string(value.activation_requirement)
      || !Array.isArray(value.namespaces)
      || value.namespaces.length !== 3) return false;
    const expected = new Set([
      "artifact_classes",
      "artifact_families",
      "artifact_lifecycles"
    ]);
    return value.namespaces.every((record) => {
      if (!exactFields(record, NAMESPACE_FIELDS)
        || !expected.has(record.namespace)
        || record.schema_version !== 1
        || record.activation_state !== "deferred_pending_human_classification"
        || record.complete !== false
        || record.enforced !== false
        || record.entry_count !== 0) return false;
      expected.delete(record.namespace);
      return true;
    }) && expected.size === 0;
  }

  function validDocument(value) {
    if (!exactFields(value, DOCUMENT_FIELDS)
      || !string(value.document_id)
      || ![
        "official_reference_name",
        "document_class",
        "revision",
        "current_status",
        "effective_date",
        "approval_date",
        "approval_method",
        "governance_change_id",
        "purpose_scope",
        "authority_exclusions",
        "creation_provenance",
        "history"
      ].every((field) => typedValue(value[field]))
      || !string(value.authority_role)
      || !string(value.canonical_path)
      || !string(value.owner)
      || !string(value.review_policy)
      || !string(value.disclosure_class)
      || !integer(value.governance_revision, 1)
      || !string(value.producer)
      || !stringArray(value.authorized_writers)
      || !stringArray(value.representations)
      || !stringArray(value.dependencies)
      || !stringArray(value.consumers)
      || ![
        "pinned",
        "runtime",
        "external",
        "provenance_only"
      ].includes(value.digest_policy)
      || !(value.sha256 === null || digest(value.sha256))
      || !validDocumentRoute(value.console_route, value.document_id)
      || !string(value.retention_posture)) return false;
    return ["pinned", "provenance_only"].includes(value.digest_policy)
      ? digest(value.sha256)
      : value.sha256 === null;
  }

  function validParameterBindings(value) {
    if (!plainObject(value)) return false;
    return Object.entries(value).every(([name, spec]) =>
      /^[a-z][a-z0-9_]*$/.test(name)
      && exactFields(spec, PARAMETER_FIELDS)
      && stringArray(spec.allowed_values)
      && spec.allowed_values.length > 0);
  }

  function validDirectory(value) {
    return exactFields(value, DIRECTORY_FIELDS)
      && string(value.scope_id)
      && string(value.display_name)
      && string(value.path_pattern)
      && string(value.match_kind)
      && integer(value.specificity_rank)
      && validParameterBindings(value.parameter_bindings)
      && string(value.owning_scope_selection_rule)
      && stringArray(value.ancestor_scope_ids)
      && string(value.placement_question)
      && stringArray(value.include_when)
      && stringArray(value.exclude_when)
      && string(value.primary_authority)
      && string(value.disclosure_boundary)
      && string(value.lifecycle_posture)
      && stringArray(value.authorized_creators)
      && string(value.precedence)
      && string(value.fallback)
      && validSelectionRoute(
        value.console_route,
        "directories",
        "directory",
        value.scope_id
      )
      && typedValue(value.permitted_artifact_classes)
      && typedValue(value.current_artifact_count)
      && value.current_artifact_count.state === "known"
      && integer(value.current_artifact_count.value);
  }

  function validCounts(value) {
    return exactFields(value, COUNT_FIELDS)
      && [...COUNT_FIELDS].every((field) => integer(value[field]));
  }

  function validSourceImport(value) {
    return exactFields(value, SOURCE_IMPORT_FIELDS)
      && string(value.path)
      && digest(value.sha256)
      && value.schema_version === 2
      && value.import_semantics === "exact_validated_snapshot";
  }

  function validRoutingDocument(value) {
    return exactFields(value, ROUTING_DOCUMENT_FIELDS)
      && string(value.document_id)
      && string(value.path)
      && typeof value.governing === "boolean"
      && ["pinned", "runtime"].includes(value.hash_policy)
      && (
        value.hash_policy === "pinned"
          ? digest(value.sha256)
          : value.sha256 === null
      )
      && stringArray(value.requires);
  }

  function validSection(value) {
    return exactFields(value, SECTION_FIELDS)
      && string(value.document)
      && /^#+\s/.test(value.heading)
      && integer(value.max_bytes, 1);
  }

  function validProfile(value) {
    return exactFields(value, PROFILE_FIELDS)
      && string(value.profile_id)
      && integer(value.max_bytes, 1)
      && stringArray(value.modules)
      && stringArray(value.capabilities)
      && typeof value.include_all_governing === "boolean"
      && Array.isArray(value.sections)
      && value.sections.every(validSection);
  }

  function validModule(value) {
    return exactFields(value, MODULE_FIELDS)
      && string(value.id)
      && string(value.path)
      && typeof value.governing === "boolean"
      && ["pinned", "runtime"].includes(value.hash_policy)
      && (
        value.hash_policy === "pinned"
          ? digest(value.sha256)
          : value.sha256 === null
      )
      && string(value.authority_role)
      && typedValue(value.authority_scope)
      && typedValue(value.authority_exclusions)
      && stringArray(value.dependencies)
      && stringArray(value.inclusion_reasons);
  }

  function validSelection(value) {
    if (!exactFields(value, SELECTION_FIELDS)
      || !string(value.selection_id)
      || !["profile", "capability"].includes(value.selection_kind)
      || value.executable !== false
      || value.authoritative !== false
      || value.live_activation_verified !== false
      || !(value.profile === null || string(value.profile))
      || !stringArray(value.capabilities)
      || !(value.max_bytes === null || integer(value.max_bytes, 1))
      || !Array.isArray(value.sections)
      || !value.sections.every(validSection)
      || !Array.isArray(value.modules)
      || !value.modules.every(validModule)
      || !validSelectionRoute(
        value.console_route,
        "routing",
        "selection",
        value.selection_id
      )) return false;
    if (value.selection_kind === "profile") {
      return value.selection_id === `profile:${value.profile}`
        && value.capabilities.length === 0
        && value.max_bytes !== null;
    }
    return value.profile === null
      && value.selection_id === `capability:${value.capabilities[0]}`
      && value.capabilities.length === 1
      && value.max_bytes === null
      && value.sections.length === 0;
  }

  function validValidation(value) {
    return exactFields(value, VALIDATION_FIELDS)
      && value.valid === true
      && digest(value.source_sha256)
      && digest(value.registry_route_sha256)
      && validCounts(value.counts)
      && Array.isArray(value.differences)
      && value.differences.length === 0
      && value.document_ids_equal === true
      && value.profile_ids_equal === true
      && value.capability_ids_equal === true;
  }

  function jsonValue(value) {
    if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "boolean") return true;
    if (Array.isArray(value)) return value.every(jsonValue);
    return plainObject(value) && Object.values(value).every(jsonValue);
  }

  function validRuleProvenance(value, sourceDocumentId, sourceDigest, ruleId) {
    return exactFields(value, RULE_PROVENANCE_FIELDS)
      && value.source_document_id === sourceDocumentId
      && value.source_sha256 === sourceDigest
      && string(value.source_heading)
      && value.clause_key === ruleId;
  }

  function validRoutingRule(value, sourceDocumentId, sourceDigest) {
    if (!plainObject(value)
      || !exactFields(value, value.namespace === "failure_rules" ? RULE_FAILURE_FIELDS : RULE_BASE_FIELDS)
      || !RULE_NAMESPACES.includes(value.namespace)
      || !/^ctxr\.(?:inv|sel|val|fail|cur|budget|review)\.[a-z][a-z0-9_]*$/.test(value.rule_id)
      || value.rule_version !== 1
      || value.status !== "active"
      || value.predicate_type !== value.rule_id
      || !plainObject(value.parameters)
      || !Object.values(value.parameters).every(jsonValue)
      || !string(value.label)
      || !string(value.rendered_text)
      || !validRuleProvenance(
        value.source_provenance,
        sourceDocumentId,
        sourceDigest,
        value.rule_id
      )
      || !stringArray(value.verification_ids)
      || !value.verification_ids.includes(`test.${value.rule_id}`)
      || !validRoutingRuleRoute(value.console_route, value.rule_id)) return false;
    return value.namespace === "failure_rules"
      ? /^CTXR_[A-Z0-9_]+$/.test(value.failure_code)
      : !Object.hasOwn(value, "failure_code");
  }

  function validPredecessorProvenance(value, candidateMode) {
    if (candidateMode) {
      return typedValue(value) && value.state === "not_applicable";
    }
    return typedValue(value)
      && value.state === "known"
      && value.value
        === "Archived predecessor provenance retained as nonauthoritative history.";
  }

  function validReadableRepresentation(value, candidateMode, revision) {
    if (candidateMode) {
      return typedValue(value) && value.state === "not_applicable";
    }
    return exactFields(value, READABLE_REPRESENTATION_FIELDS)
      && value.state === "known"
      && value.representation_id === "human_readable_context_routing"
      && value.source_registry_revision === revision
      && value.authority_effect === "none"
      && value.executable === false;
  }

  function validRouting(value, registry) {
    // Kept as a single fail-closed predicate so consumers never recover from
    // an incomplete routing catalog with browser-generated defaults.
    const candidateMode = registry.validation_mode
      === "candidate_validation_only";
    const expectedActivation = candidateMode ? "candidate_import" : "active";
    const validSourceState = candidateMode
      ? validSourceImport(value.source_import)
      : typedValue(value.source_import)
        && value.source_import.state === "not_applicable";
    const validParityState = candidateMode
      ? validValidation(value.validation)
      : typedValue(value.validation)
        && value.validation.state === "not_applicable";
    const validParityPolicy = candidateMode
      ? string(value.parity_policy)
      : typedValue(value.parity_policy)
        && value.parity_policy.state === "not_applicable";
    if (!exactFields(value, ROUTING_FIELDS)
      || value.schema_version !== 2
      || value.rule_catalog_version !== 1
      || value.activation_state !== expectedActivation
      || value.complete !== true
      || value.authoritative !== false
      || !validSourceState
      || !validPredecessorProvenance(
        value.predecessor_provenance,
        candidateMode
      )
      || !validReadableRepresentation(
        value.readable_representation,
        candidateMode,
        registry.registry_revision
      )
      || !validCounts(value.expected_counts)
      || !validParityPolicy
      || !stringArray(value.required_modules)
      || !stringArray(value.generated_path_exclusions)
      || !Array.isArray(value.documents)
      || !value.documents.every(validRoutingDocument)
      || !Array.isArray(value.capabilities)
      || !value.capabilities.every((record) =>
        exactFields(record, CAPABILITY_FIELDS)
        && string(record.capability_id)
        && stringArray(record.document_ids))
      || !Array.isArray(value.profiles)
      || !value.profiles.every(validProfile)
      || !Array.isArray(value.selections)
      || !value.selections.every(validSelection)
      || !Array.isArray(value.rule_namespaces)
      || value.rule_namespaces.length !== RULE_NAMESPACES.length
      || !value.rule_namespaces.every((name, index) => name === RULE_NAMESPACES[index])
      || !plainObject(value.rule_counts)
      || Object.keys(value.rule_counts).length !== RULE_NAMESPACES.length
      || !validParityState) return false;
    const documentIds = value.documents.map((record) => record.document_id);
    const capabilityIds = value.capabilities.map((record) => record.capability_id);
    const profileIds = value.profiles.map((record) => record.profile_id);
    const selectionIds = value.selections.map((record) => record.selection_id);
    const routingDocument = value.documents.find((record) =>
      record.document_id === "context_routing");
    const ruleSourceDocumentId = candidateMode
      ? "context_routing"
      : "COMPONENT-REGISTRY";
    const ruleSourceDigest = candidateMode
      ? routingDocument?.sha256
      : registry.registry_sha256;
    if ((candidateMode && (
      !routingDocument
      || routingDocument.path !== "framework/CONTEXT_ROUTING.md"
      || !digest(routingDocument.sha256)
    ))
      || (!candidateMode && routingDocument)
      || !digest(ruleSourceDigest)
      || !Array.isArray(value.rules)
      || !value.rules.every((record) =>
        validRoutingRule(
          record,
          ruleSourceDocumentId,
          ruleSourceDigest
        ))) return false;
    const ruleIds = value.rules.map((record) => record.rule_id);
    return new Set(documentIds).size === documentIds.length
      && new Set(capabilityIds).size === capabilityIds.length
      && new Set(profileIds).size === profileIds.length
      && new Set(selectionIds).size === selectionIds.length
      && value.expected_counts.documents === documentIds.length
      && value.expected_counts.capabilities === capabilityIds.length
      && value.expected_counts.profiles === profileIds.length
      && value.selections.length === capabilityIds.length + profileIds.length
      && new Set(ruleIds).size === ruleIds.length
      && ruleIds.every((id) => !selectionIds.includes(id))
      && RULE_NAMESPACES.every((namespace) =>
        value.rule_counts[namespace] === RULE_NAMESPACE_COUNTS[namespace]
        && value.rules.filter((rule) => rule.namespace === namespace).length
          === RULE_NAMESPACE_COUNTS[namespace]
        && RULE_IDS_BY_NAMESPACE[namespace].every((id) =>
          value.rules.some((rule) => rule.namespace === namespace && rule.rule_id === id)))
      && value.rules.length === 64;
  }

  function validTerminology(value) {
    return exactFields(value, TERMINOLOGY_FIELDS)
      && value.available === false
      && value.complete === false
      && value.activation_state === "candidate_unpopulated"
      && string(value.reason)
      && Array.isArray(value.entries)
      && value.entries.length === 0
      && validRoute(value.console_route, "terminology");
  }

  function validReadinessCounts(value, expectedDocuments, expectedGoverning) {
    return exactFields(value, READINESS_COUNT_FIELDS)
      && value.documents === expectedDocuments
      && value.governing_documents === expectedGoverning
      && value.capabilities === 19
      && value.profiles === 8
      && value.required_modules === 3
      && value.generated_path_exclusions === 9
      && value.rules === 64;
  }

  function validActivationReadiness(value, registryValue) {
    return exactFields(value, READINESS_FIELDS)
      && value.available === true
      && value.complete === true
      && ["candidate_complete", "active"].includes(value.activation_state)
      && value.authoritative === false
      && value.executable === false
      && value.registry_revision === registryValue.registry_revision
      && value.registry_sha256 === registryValue.registry_sha256
      && validReadinessCounts(value.current_candidate_counts, 88, 87)
      && validReadinessCounts(value.simulated_active_counts, 85, 84)
      && value.requirement_count === 77
      && value.exception_count === 0
      && exactFields(value.stage_boundaries, READINESS_BOUNDARY_FIELDS)
      && value.stage_boundaries.artifact_classes
        === "deferred_by_approved_stage_boundary"
      && value.stage_boundaries.artifact_families
        === "deferred_by_approved_stage_boundary"
      && value.stage_boundaries.artifact_lifecycles
        === "deferred_by_approved_stage_boundary"
      && value.stage_boundaries.terminology === "candidate_unpopulated"
      && value.stage_boundaries.repository_reference_mutation
        === "separately_gated"
      && [
        "pending_human_activation",
        "tracked_active_configuration_live_readback_separate"
      ].includes(value.activation_decision);
  }

  function validSnapshot(value) {
    const hasRelationships = Array.isArray(value?.relationships);
    if (!exactFieldsOneOf(value, [TOP_FIELDS, LEGACY_TOP_FIELDS])
      || value.schema_version !== 1
      || value.projection_id !== "component-registry-console"
      || value.producer_id !== "project-console-builder"
      || Number.isNaN(Date.parse(value.generated_at))
      || value.availability !== "current"
      || value.complete !== true
      || value.reason_code !== null
      || !(hasRelationships
        ? exactFields(value.routes, ROUTE_FIELDS)
          && exactFields(value.defaults, DEFAULT_FIELDS)
          && MODES.every((mode) => validRoute(value.routes[mode], mode))
        : exactFields(value.routes, LEGACY_ROUTE_FIELDS)
          && exactFields(value.defaults, LEGACY_DEFAULT_FIELDS)
          && MODES.filter((mode) => mode !== "relationships")
            .every((mode) => validRoute(value.routes[mode], mode)))
      || value.defaults.mode !== "documents"
      || !string(value.defaults.document)
      || !string(value.defaults.directory)
      || !string(value.defaults.routing)
      || !validRegistry(value.registry)
      || !validDeferred(value.deferred)
      || !Array.isArray(value.documents)
      || !value.documents.every(validDocument)
      || !Array.isArray(value.directories)
      || !value.directories.every(validDirectory)
      || (hasRelationships && !value.relationships.every(validRelationship))
      || !validRouting(value.routing, value.registry)
      || value.routing.authoritative !== false
      || !validActivationReadiness(
        value.activation_readiness,
        value.registry
      )
      || !validTerminology(value.terminology)) return false;
    const documentIds = value.documents.map((record) => record.document_id);
    const directoryIds = value.directories.map((record) => record.scope_id);
    const relationshipIds = hasRelationships
      ? value.relationships.map((record) => record.relationship_id)
      : [];
    return new Set(documentIds).size === documentIds.length
      && new Set(directoryIds).size === directoryIds.length
      && new Set(relationshipIds).size === relationshipIds.length
      && documentIds.includes(value.defaults.document)
      && directoryIds.includes(value.defaults.directory)
      && (!hasRelationships || relationshipIds.includes(value.defaults.relationship))
      && value.routing.selections.some((record) =>
        record.selection_id === value.defaults.routing)
      && value.routing.documents.every((record) =>
        documentIds.includes(record.document_id));
  }

  function routeState(target, snapshot) {
    const [path, query = ""] = String(target || "").replace(/^#/, "").split("?", 2);
    const parts = path.split(":");
    const requestedMode = parts[0] === "automation"
      && parts[1] === "component-registry"
      ? parts[2]
      : "";
    const mode = MODES.includes(requestedMode)
      ? requestedMode
      : validSnapshot(snapshot)
        ? snapshot.defaults.mode
        : "documents";
    const parameters = new URLSearchParams(query);
    const allowedKeys = {
      documents: ["document"],
      directories: ["directory"],
      routing: ["selection", "rule"],
      relationships: ["relationship"],
      terminology: []
    }[mode];
    const parameterKeys = [...parameters.keys()];
    const validQuery = parameterKeys.length === 0
      || (parameterKeys.length === 1 && allowedKeys.includes(parameterKeys[0]));
    const selected = validQuery ? {
      documents: parameters.get("document"),
      directories: parameters.get("directory"),
      routing: parameters.get("selection") || parameters.get("rule"),
      relationships: parameters.get("relationship"),
      terminology: null
    }[mode] : null;
    if (!validSnapshot(snapshot)) return { mode, selected: null };
    const records = {
      documents: snapshot.documents.map((record) => record.document_id),
      directories: snapshot.directories.map((record) => record.scope_id),
      routing: [
        ...snapshot.routing.selections.map((record) => record.selection_id),
        ...snapshot.routing.rules.map((record) => record.rule_id)
      ],
      relationships: (snapshot.relationships || []).map((record) =>
        record.relationship_id),
      terminology: []
    }[mode];
    const producerDefault = {
      documents: snapshot.defaults.document,
      directories: snapshot.defaults.directory,
      routing: snapshot.defaults.routing,
      relationships: snapshot.defaults.relationship || null,
      terminology: null
    }[mode];
    return {
      mode,
      selected: records.includes(selected) ? selected : producerDefault
    };
  }

  function node(tag, className = "", text = "") {
    const value = document.createElement(tag);
    if (className) value.className = className;
    if (text !== "") value.textContent = String(text);
    return value;
  }

  function renderValue(value) {
    if (!typedValue(value)) return "Unavailable";
    if (value.state === "known") return String(value.value);
    const label = value.state.replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
    return `${label} — ${value.reason}`;
  }

  function appendRows(host, rows) {
    const list = node("dl", "component-registry-metadata");
    rows.forEach(([label, value]) => {
      list.append(node("dt", "", label), node("dd", "", value));
    });
    host.append(list);
  }

  function joined(values) {
    return values.length ? values.join(", ") : "None registered";
  }

  function renderDocument(host, record) {
    host.replaceChildren();
    host.append(node("h3", "", renderValue(record.official_reference_name)));
    appendRows(host, [
      ["Stable identity", record.document_id],
      ["Class", renderValue(record.document_class)],
      ["Revision", renderValue(record.revision)],
      ["Status", renderValue(record.current_status)],
      ["Authority role", record.authority_role],
      ["Purpose and scope", renderValue(record.purpose_scope)],
      ["Authority exclusions", renderValue(record.authority_exclusions)],
      ["Canonical path", record.canonical_path],
      ["Owner", record.owner],
      ["Review policy", record.review_policy],
      ["Disclosure", record.disclosure_class],
      ["Producer", record.producer],
      ["Authorized writers", joined(record.authorized_writers)],
      ["Representations", joined(record.representations)],
      ["Dependencies", joined(record.dependencies)],
      ["Consumers", joined(record.consumers)],
      ["Digest policy", `${record.digest_policy} · ${record.sha256 || "runtime"}`],
      ["Approval", `${renderValue(record.approval_method)} · ${renderValue(record.approval_date)}`],
      ["Governance change", renderValue(record.governance_change_id)],
      ["Effective date", renderValue(record.effective_date)],
      ["Creation provenance", renderValue(record.creation_provenance)],
      ["Retention posture", record.retention_posture],
      ["History", renderValue(record.history)]
    ]);
  }

  function renderDirectory(host, record) {
    host.replaceChildren();
    host.append(node("h3", "", record.display_name));
    appendRows(host, [
      ["Stable identity", record.scope_id],
      ["Path pattern", record.path_pattern],
      ["Match kind", record.match_kind],
      ["Specificity rank", record.specificity_rank],
      ["Ancestor scopes", joined(record.ancestor_scope_ids)],
      ["Placement question", record.placement_question],
      ["Include when", joined(record.include_when)],
      ["Exclude when", joined(record.exclude_when)],
      ["Primary authority", record.primary_authority],
      ["Disclosure boundary", record.disclosure_boundary],
      ["Lifecycle posture", record.lifecycle_posture],
      ["Authorized creators", joined(record.authorized_creators)],
      ["Precedence", record.precedence],
      ["Fallback", record.fallback],
      ["Current artifact count", renderValue(record.current_artifact_count)],
      ["Permitted artifact classes", renderValue(record.permitted_artifact_classes)]
    ]);
  }

  function relationshipEndpoint(value) {
    return `${value.id} (${readableCategory(value.kind)})`;
  }

  function renderRelationship(host, record) {
    host.replaceChildren();
    host.append(node("h3", "", readableCategory(record.relationship_type)));
    appendRows(host, [
      ["Stable relationship identity", record.relationship_id],
      ["Relationship type", readableCategory(record.relationship_type)],
      ["From", relationshipEndpoint(record.from)],
      ["To", relationshipEndpoint(record.to)],
      ["Authority boundary", record.authority_boundary]
    ]);
  }

  function renderRouting(host, record, snapshot) {
    host.replaceChildren();
    if (Object.hasOwn(record, "rule_id")) {
      host.append(node("h3", "", record.label));
      appendRows(host, [
        ["Stable rule identity", record.rule_id],
        ["Category", record.namespace],
        ["Rule version", record.rule_version],
        ["Status", record.status],
        ["Predicate type", record.predicate_type],
        ["Registered description", record.rendered_text],
        ["Failure code", record.failure_code || "Not applicable"],
        ["Source document", record.source_provenance.source_document_id],
        ["Source digest", record.source_provenance.source_sha256],
        ["Source heading", record.source_provenance.source_heading],
        ["Verification", joined(record.verification_ids)]
      ]);
      const parameters = node("pre", "component-registry-rule-parameters");
      parameters.textContent = JSON.stringify(record.parameters, null, 2);
      host.append(node("h4", "", "Registered parameters"), parameters);
      return;
    }
    host.append(node("h3", "", record.selection_id));
    appendRows(host, [
      ["Selection kind", record.selection_kind],
      ["Profile", record.profile || "None"],
      ["Capabilities", joined(record.capabilities)],
      ["Maximum bytes", record.max_bytes === null ? "Not applicable" : record.max_bytes],
      ["Resolved modules", record.modules.length],
      [
        "Route-source digest",
        snapshot.routing.source_import.state
          ? renderValue(snapshot.routing.source_import)
          : snapshot.routing.source_import.sha256
      ],
      [
        "Parity state",
        snapshot.routing.validation.state
          ? renderValue(snapshot.routing.validation)
          : snapshot.routing.validation.valid
            ? "Exact"
            : "Unavailable"
      ],
      [
        "Historical predecessor provenance",
        renderValue(snapshot.routing.predecessor_provenance)
      ],
      [
        "Readable representation",
        snapshot.routing.readable_representation.state === "known"
          ? (
            `${snapshot.routing.readable_representation.representation_id}`
            + ` · registry revision ${
              snapshot.routing.readable_representation.source_registry_revision
            } · nonauthoritative`
          )
          : renderValue(snapshot.routing.readable_representation)
      ],
      ["Executable", record.executable ? "Yes" : "No"],
      ["Authoritative", record.authoritative ? "Yes" : "No"]
    ]);
    const table = node("table", "component-registry-route-table");
    const head = node("thead");
    const headRow = node("tr");
    ["Document", "Path", "Authority role", "Inclusion reason"].forEach((label) =>
      headRow.append(node("th", "", label)));
    head.append(headRow);
    const body = node("tbody");
    record.modules.forEach((module) => {
      const row = node("tr");
      row.append(
        node("td", "", module.id),
        node("td", "", module.path),
        node("td", "", module.authority_role),
        node("td", "", joined(module.inclusion_reasons))
      );
      body.append(row);
    });
    table.append(head, body);
    host.append(table);
  }

  function renderTerminology(host, terminology) {
    host.replaceChildren();
    host.append(
      node("h3", "", "Canonical terminology"),
      node("p", "empty-state compact-empty", terminology.reason)
    );
    appendRows(host, [
      ["Activation state", terminology.activation_state],
      ["Availability", "Unavailable"],
      ["Completeness", "Incomplete"],
      ["Entries", terminology.entries.length]
    ]);
  }

  function filterTerminologyEntries(entries, query) {
    const tokens = String(query || "")
      .trim()
      .toLocaleLowerCase()
      .split(/\s+/)
      .filter(Boolean);
    if (!tokens.length) return [...entries];
    return entries.filter((entry) => {
      const searchable = `${entry.label} ${entry.definition}`
        .toLocaleLowerCase();
      return tokens.every((token) => searchable.includes(token));
    });
  }

  function renderTerminologyDraft(entries) {
    if (!entries.length) return;
    const listHost = document.getElementById("component-registry-terminology-list");
    const detailHost = document.getElementById("component-registry-terminology-detail");
    const search = document.getElementById("component-registry-terminology-search");
    const resultCount = document.getElementById("component-registry-terminology-results");
    if (!listHost || !detailHost || !search || !resultCount) return;
    const count = document.getElementById("component-registry-terminology-count");
    if (count) {
      count.hidden = false;
      count.textContent = `Draft ${entries.length}`;
      count.setAttribute("aria-label", `${entries.length} working-draft definitions`);
    }
    const renderDetail = (entry) => {
      detailHost.replaceChildren(
        node("h3", "", entry.term),
        node(
          "p",
          "empty-state compact-empty",
          "Working-draft preview — nonauthoritative and not active in the Registry."
        ),
        ...entry.paragraphs.map((paragraph) => node("p", "", paragraph))
      );
    };
    let selectedTerm = entries[0].term;
    const renderResults = () => {
      const filtered = filterTerminologyEntries(entries, search.value);
      resultCount.textContent = `${filtered.length} of ${entries.length} working-draft definitions`;
      listHost.replaceChildren();
      if (!filtered.length) {
        listHost.append(node(
          "p",
          "empty-state compact-empty",
          "No definitions match this search."
        ));
        detailHost.replaceChildren(node(
          "p",
          "empty-state compact-empty",
          "Clear or revise the search to inspect a definition."
        ));
        return;
      }
      const selected = filtered.find((entry) => entry.term === selectedTerm) || filtered[0];
      selectedTerm = selected.term;
      const rows = [];
      const group = node(
        "div",
        "component-registry-group-label",
        `Approved working draft · ${filtered.length}`
      );
      group.setAttribute("role", "presentation");
      listHost.append(group);
      filtered.forEach((entry) => {
        const row = node("button", "email-list-row component-registry-list-row");
        const isSelected = entry.term === selectedTerm;
        row.type = "button";
        row.setAttribute("role", "option");
        row.setAttribute("aria-selected", String(isSelected));
        row.tabIndex = isSelected ? 0 : -1;
        if (isSelected) row.classList.add("selected");
        row.append(
          node("strong", "email-row-title", entry.term),
          node("span", "email-row-time", "Draft"),
          node("span", "email-row-summary", entry.paragraphs[0])
        );
        row.addEventListener("click", () => {
          selectedTerm = entry.term;
          rows.forEach((candidate) => {
            const candidateSelected = candidate === row;
            candidate.classList.toggle("selected", candidateSelected);
            candidate.setAttribute("aria-selected", String(candidateSelected));
            candidate.tabIndex = candidateSelected ? 0 : -1;
          });
          renderDetail(entry);
        });
        row.addEventListener("keydown", (event) => {
          if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
          const current = rows.indexOf(row);
          const next = event.key === "Home"
            ? 0
            : event.key === "End"
              ? rows.length - 1
              : event.key === "ArrowDown"
                ? Math.min(rows.length - 1, current + 1)
                : Math.max(0, current - 1);
          event.preventDefault();
          rows[next].focus();
          rows[next].click();
        });
        rows.push(row);
        listHost.append(row);
      });
      renderDetail(selected);
    };
    search.disabled = false;
    search.oninput = renderResults;
    renderResults();
  }

  function readableCategory(value) {
    return String(value || "Unclassified")
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function renderRegistryList(
    host,
    records,
    identity,
    title,
    summary,
    meta,
    category,
    selectedIdentity
  ) {
    host.replaceChildren();
    const ordered = [...records].sort((left, right) =>
      title(left).localeCompare(title(right), undefined, { numeric: true }));
    const groups = new Map();
    ordered.forEach((record) => {
      const group = category(record);
      if (!groups.has(group)) groups.set(group, []);
      groups.get(group).push(record);
    });
    const rows = [];
    [...groups].sort(([left], [right]) => left.localeCompare(right)).forEach(([group, items]) => {
      const groupLabel = node(
        "div",
        "component-registry-group-label",
        `${group} · ${items.length}`
      );
      groupLabel.setAttribute("role", "presentation");
      host.append(groupLabel);
      items.forEach((record) => {
        const recordIdentity = identity(record);
        const selected = recordIdentity === selectedIdentity;
        const row = node("button", "email-list-row component-registry-list-row");
        row.type = "button";
        row.dataset.registryRecord = recordIdentity;
        row.setAttribute("role", "option");
        row.setAttribute("aria-selected", String(selected));
        row.tabIndex = selected ? 0 : -1;
        if (selected) row.classList.add("selected");
        row.append(
          node("strong", "email-row-title", title(record)),
          node("span", "email-row-time", meta(record)),
          node("span", "email-row-summary", summary(record))
        );
        row.addEventListener("click", () => go(record.console_route));
        row.addEventListener("keydown", (event) => {
          if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
          const current = rows.indexOf(row);
          const next = event.key === "Home"
            ? 0
            : event.key === "End"
              ? rows.length - 1
              : event.key === "ArrowDown"
                ? Math.min(rows.length - 1, current + 1)
                : Math.max(0, current - 1);
          event.preventDefault();
          rows[next].focus();
          rows[next].click();
        });
        rows.push(row);
        host.append(row);
      });
    });
  }

  function renderRelationshipRecords(records, selectedIdentity = null) {
    const selected = records.find((record) =>
      record.relationship_id === selectedIdentity) || records[0];
    setModeCount("relationships", records.length, true);
    renderRegistryList(
      document.getElementById("component-registry-relationship-list"),
      records,
      (record) => record.relationship_id,
      (record) => `${record.from.id} → ${record.to.id}`,
      (record) => record.authority_boundary,
      (record) => readableCategory(record.relationship_type),
      (record) => readableCategory(record.relationship_type),
      selected?.relationship_id
    );
    const detail = document.getElementById("component-registry-relationship-detail");
    if (selected) {
      renderRelationship(detail, selected);
    } else if (detail) {
      detail.replaceChildren(node(
        "p",
        "empty-state compact-empty",
        "No component relationships are registered."
      ));
    }
  }

  function setModeCount(mode, count, available = true) {
    const value = document.getElementById(`component-registry-${mode}-count`);
    if (!value) return;
    value.hidden = !available;
    value.textContent = available ? String(count) : "";
  }

  function go(route) {
    if (!string(route)) return;
    global.location.hash = `#${route}`;
  }

  function applyMode(mode) {
    MODES.forEach((candidate) => {
      const button = document.getElementById(`component-registry-mode-${candidate}`);
      const panel = document.getElementById(`component-registry-panel-${candidate}`);
      if (button) {
        const selected = candidate === mode;
        button.setAttribute("aria-selected", String(selected));
        button.tabIndex = selected ? 0 : -1;
      }
      if (panel) panel.hidden = candidate !== mode;
    });
  }

  function bindControls(snapshot) {
    const buttons = MODES.map((mode) =>
      document.getElementById(`component-registry-mode-${mode}`));
    buttons.forEach((button, index) => {
      if (!button || button.dataset.registryBound === "true") return;
      button.dataset.registryBound = "true";
      button.addEventListener("click", () =>
        go(
          snapshot.routes[button.dataset.registryMode]
          || `automation:component-registry:${button.dataset.registryMode}`
        ));
      button.addEventListener("keydown", (event) => {
        let next = null;
        if (event.key === "ArrowRight") next = (index + 1) % buttons.length;
        if (event.key === "ArrowLeft") next = (index - 1 + buttons.length) % buttons.length;
        if (event.key === "Home") next = 0;
        if (event.key === "End") next = buttons.length - 1;
        if (next === null || !buttons[next]) return;
        event.preventDefault();
        buttons[next].focus();
        const mode = buttons[next].dataset.registryMode;
        go(snapshot.routes[mode] || `automation:component-registry:${mode}`);
      });
    });
  }

  function unavailable() {
    const status = document.getElementById("component-registry-status");
    if (status) {
      status.className = "status-badge unavailable";
      status.textContent = "Unavailable";
    }
    [
      "component-registry-document-detail",
      "component-registry-directory-detail",
      "component-registry-routing-detail",
      "component-registry-relationship-detail",
      "component-registry-terminology-detail"
    ].forEach((id) => {
      const host = document.getElementById(id);
      if (host) host.replaceChildren(
        node("p", "empty-state compact-empty", "Component Registry data unavailable.")
      );
    });
  }

  function render(snapshot, target = "") {
    if (!validSnapshot(snapshot)) {
      unavailable();
      return false;
    }
    const state = routeState(target, snapshot);
    const status = document.getElementById("component-registry-status");
    if (status) {
      status.className = "status-badge warning";
      status.textContent = snapshot.registry.registry_status === "active"
        ? "Tracked active configuration"
        : "Candidate";
    }
    const deferred = document.getElementById("component-registry-deferred");
    if (deferred) {
      deferred.replaceChildren();
      deferred.append(
        node("strong", "", snapshot.deferred.display_state),
        node(
          "p",
          "component-registry-configuration",
          renderValue(snapshot.registry.configuration_validation)
        ),
        node(
          "p",
          "component-registry-live-activation",
          `Live activation — ${renderValue(snapshot.registry.live_activation)}`
        ),
        node(
          "p",
          "component-registry-readiness",
          (
            `Activation readiness — ${snapshot.activation_readiness.requirement_count}`
            + " requirements cataloged; "
            + `${snapshot.activation_readiness.exception_count} exceptions; `
            + (
              snapshot.activation_readiness.activation_decision
                === "pending_human_activation"
                ? "human activation pending"
                : "tracked configuration active; live readback remains separate"
            )
          )
        ),
        node("p", "", snapshot.deferred.reason),
        node("p", "component-registry-activation", snapshot.deferred.activation_requirement)
      );
    }
    setModeCount("documents", snapshot.documents.length);
    setModeCount("directories", snapshot.directories.length);
    setModeCount(
      "routing",
      snapshot.routing.selections.length + snapshot.routing.rules.length
    );
    setModeCount(
      "relationships",
      (snapshot.relationships || []).length,
      Array.isArray(snapshot.relationships)
    );
    setModeCount(
      "terminology",
      snapshot.terminology.entries.length,
      snapshot.terminology.available === true
    );
    bindControls(snapshot);
    const selectedDocument = snapshot.documents.find((record) =>
      record.document_id === (
        state.mode === "documents"
          ? state.selected
          : snapshot.defaults.document
      ));
    const selectedDirectory = snapshot.directories.find((record) =>
      record.scope_id === (
        state.mode === "directories"
          ? state.selected
          : snapshot.defaults.directory
      ));
    const routingRecords = [...snapshot.routing.selections, ...snapshot.routing.rules];
    const selectedRouting = routingRecords.find((record) =>
      (record.selection_id || record.rule_id) === (
        state.mode === "routing"
          ? state.selected
          : snapshot.defaults.routing
      ));
    const relationshipRecords = snapshot.relationships || boundRelationships || [];
    const selectedRelationship = relationshipRecords.find((record) =>
      record.relationship_id === (
        state.mode === "relationships"
          ? state.selected
          : snapshot.defaults.relationship
      ));
    renderRegistryList(
      document.getElementById("component-registry-document-list"),
      snapshot.documents,
      (record) => record.document_id,
      (record) => renderValue(record.official_reference_name),
      (record) => record.canonical_path,
      (record) => renderValue(record.current_status),
      (record) => readableCategory(record.authority_role),
      selectedDocument?.document_id
    );
    renderRegistryList(
      document.getElementById("component-registry-directory-list"),
      snapshot.directories,
      (record) => record.scope_id,
      (record) => record.display_name,
      (record) => record.path_pattern,
      (record) => readableCategory(record.lifecycle_posture),
      (record) => readableCategory(record.lifecycle_posture),
      selectedDirectory?.scope_id
    );
    renderRegistryList(
      document.getElementById("component-registry-routing-list"),
      routingRecords,
      (record) => record.selection_id || record.rule_id,
      (record) => record.selection_id || record.label,
      (record) => record.rule_id || joined(record.capabilities),
      (record) => record.rule_id ? "Rule" : readableCategory(record.selection_kind),
      (record) => record.rule_id
        ? `Rules · ${readableCategory(record.namespace)}`
        : readableCategory(`${record.selection_kind}s`),
      selectedRouting?.selection_id || selectedRouting?.rule_id
    );
    renderRelationshipRecords(
      relationshipRecords,
      selectedRelationship?.relationship_id
    );
    const terminologyList = document.getElementById("component-registry-terminology-list");
    terminologyList.replaceChildren(node(
      "p",
      "empty-state compact-empty",
      "No terminology entries are active."
    ));
    if (selectedDocument) {
      renderDocument(
        document.getElementById("component-registry-document-detail"),
        selectedDocument
      );
    }
    if (selectedDirectory) {
      renderDirectory(
        document.getElementById("component-registry-directory-detail"),
        selectedDirectory
      );
    }
    if (selectedRouting) {
      renderRouting(
        document.getElementById("component-registry-routing-detail"),
        selectedRouting,
        snapshot
      );
    }
    if (!relationshipRecords.length) {
      const [path, query = ""] = String(target || "").replace(/^#/, "").split("?", 2);
      const parameters = new URLSearchParams(query);
      const requestedRelationship = path === "automation:component-registry:relationships"
        && [...parameters.keys()].length === 1
        ? parameters.get("relationship")
        : null;
      loadBoundRelationships(snapshot).then((records) => {
        renderRelationshipRecords(records, requestedRelationship);
      }).catch(() => {
        const relationshipDetail = document.getElementById(
          "component-registry-relationship-detail"
        );
        if (relationshipDetail) relationshipDetail.replaceChildren(node(
          "p",
          "empty-state compact-empty",
          "Relationship data is unavailable because the current Registry binding could not be verified."
        ));
      });
    }
    renderTerminology(
      document.getElementById("component-registry-terminology-detail"),
      snapshot.terminology
    );
    applyMode(state.mode);
    return true;
  }

  global.ARRP_COMPONENT_REGISTRY = Object.freeze({
    schemaVersion: 1,
    pendingDisplay: PENDING_DISPLAY,
    validSnapshot,
    routeState,
    filterTerminologyEntries,
    render
  });
})(window);

(function (global) {
  "use strict";

  const legacyApi = global.ARRP_COMPONENT_REGISTRY;

  const MODES = Object.freeze([
    "components",
    "lifecycles",
    "authority",
    "relationships",
    "coverage",
    "routing",
    "terminology"
  ]);

  function object(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function text(value) {
    return typeof value === "string" && value.length > 0;
  }

  function unique(records, key) {
    return Array.isArray(records)
      && records.every((record) => object(record) && text(record[key]))
      && new Set(records.map((record) => record[key])).size === records.length;
  }

  function containsPrivatePayload(value) {
    if (Array.isArray(value)) return value.some(containsPrivatePayload);
    if (!object(value)) return false;
    return Object.entries(value).some(([key, nested]) =>
      ["private_payload", "contract_payload", "attachment_path", "credential", "secret"]
        .includes(key)
      || containsPrivatePayload(nested));
  }

  function validSnapshot(snapshot) {
    if (snapshot?.schema_version === 1) {
      return legacyApi.validSnapshot(snapshot);
    }
    if (!object(snapshot)
      || snapshot.schema_version !== 2
      || snapshot.projection_id !== "component-registry-console"
      || snapshot.producer_id !== "project-console-builder"
      || Number.isNaN(Date.parse(snapshot.generated_at))
      || snapshot.availability !== "current"
      || snapshot.complete !== true
      || snapshot.reason_code !== null
      || !object(snapshot.routes)
      || !object(snapshot.defaults)
      || !object(snapshot.registry)
      || snapshot.registry.registry_id !== "COMPONENT-REGISTRY"
      || snapshot.registry.registry_revision !== 2
      || snapshot.registry.registry_status !== "proposed"
      || snapshot.registry.validation_mode !== "proposed_revision_validation"
      || snapshot.registry.authoritative !== false
      || snapshot.registry.executable !== false
      || snapshot.registry.authority_effective !== false
      || snapshot.registry.source_revision_authorized !== false
      || snapshot.registry.source_bytes_current !== false
      || snapshot.registry.canonical_history_confirmed !== false
      || snapshot.registry.receipt_trusted !== false
      || snapshot.registry.runtime_live !== "not_checked"
      || snapshot.registry.predecessor_route_consulted !== false
      || !/^[0-9a-f]{64}$/.test(snapshot.registry.registry_sha256 || "")
      || !unique(snapshot.components, "stable_id")
      || !object(snapshot.lifecycles)
      || !unique(snapshot.lifecycles.assignments, "assignment_id")
      || !object(snapshot.authorities)
      || !unique(snapshot.authorities.assignments, "assignment_id")
      || !unique(snapshot.relationships, "relationship_id")
      || !object(snapshot.coverage)
      || !unique(snapshot.coverage.records, "coverage_id")
      || !object(snapshot.routing)
      || !unique(snapshot.routing.selections, "routing_id")
      || !object(snapshot.terminology)
      || snapshot.terminology.available !== true
      || snapshot.terminology.complete !== true
      || snapshot.terminology.adopted !== true
      || !/^[0-9a-f]{64}$/.test(snapshot.terminology.record_set_sha256 || "")
      || !unique(snapshot.terminology.entries, "term_id")
      || snapshot.terminology.entries.length !== 69
      || containsPrivatePayload(snapshot)) return false;
    if (!MODES.every((mode) =>
      snapshot.routes[mode] === `automation:component-registry:${mode}`)) return false;
    const componentIds = new Set(snapshot.components.map((record) => record.stable_id));
    if (!snapshot.components.every((record) =>
      text(record.display_name)
      && object(record.classification)
      && text(record.classification.component_class)
      && object(record.canonical_source)
      && (text(record.owner) || object(record.owner))
      && object(record.information_handling)
      && object(record.retention)
      && Array.isArray(record.supporting_artifacts)
      && object(record.record_refs)
      && Array.isArray(record.lifecycle_records)
      && Array.isArray(record.authority_records)
      && Array.isArray(record.relationship_records)
      && Array.isArray(record.migration_records)
      && Array.isArray(record.provenance_records)
      && record.console_route === (
        "automation:component-registry:components?component="
        + encodeURIComponent(record.stable_id)
      ))) return false;
    if (!snapshot.lifecycles.assignments.every((record) =>
      componentIds.has(record.component_id))) return false;
    if (!snapshot.authorities.assignments.every((record) =>
      componentIds.has(record.component_id))) return false;
    if (!snapshot.terminology.entries.every((record) =>
      text(record.label) && text(record.definition))) return false;
    return snapshot.defaults.mode === "components"
      && componentIds.has(snapshot.defaults.component)
      && snapshot.coverage.uncovered_count === 0
      && snapshot.coverage.multiply_treated_count === 0;
  }

  function routeState(target, snapshot) {
    if (snapshot?.schema_version === 1) {
      return legacyApi.routeState(target, snapshot);
    }
    const [route, query = ""] = String(target || "").replace(/^#/, "").split("?", 2);
    const parts = route.split(":");
    const requested = parts[0] === "automation" && parts[1] === "component-registry"
      ? parts[2]
      : "";
    const mode = MODES.includes(requested) ? requested : "components";
    if (!validSnapshot(snapshot)) return { mode, selected: null };
    const key = {
      components: "component",
      lifecycles: "assignment",
      authority: "assignment",
      relationships: "relationship",
      coverage: "coverage",
      routing: "selection",
      terminology: "term"
    }[mode];
    const parameters = new URLSearchParams(query);
    const selected = [...parameters.keys()].every((name) => name === key)
      ? parameters.get(key)
      : null;
    const identities = {
      components: snapshot.components.map((record) => record.stable_id),
      lifecycles: snapshot.lifecycles.assignments.map((record) => record.assignment_id),
      authority: snapshot.authorities.assignments.map((record) => record.assignment_id),
      relationships: snapshot.relationships.map((record) => record.relationship_id),
      coverage: snapshot.coverage.records.map((record) => record.coverage_id),
      routing: snapshot.routing.selections.map((record) => record.routing_id),
      terminology: snapshot.terminology.entries.map((record) => record.term_id)
    }[mode];
    return {
      mode,
      selected: identities.includes(selected) ? selected : snapshot.defaults[
        mode === "components" ? "component"
          : mode === "lifecycles" ? "lifecycle"
            : mode === "relationships" ? "relationship"
              : mode === "terminology" ? "terminology"
                : mode
      ]
    };
  }

  function node(tag, className = "", value = "") {
    const result = document.createElement(tag);
    if (className) result.className = className;
    if (value !== "") result.textContent = String(value);
    return result;
  }

  function readable(value) {
    return String(value || "Unavailable")
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function display(value) {
    if (value === null || value === undefined || value === "") return "Not applicable";
    if (typeof value === "boolean") return value ? "Yes" : "No";
    if (Array.isArray(value)) return value.length ? value.map(display).join(", ") : "None";
    if (object(value)) {
      return Object.entries(value)
        .map(([key, nested]) => `${readable(key)}: ${display(nested)}`)
        .join(" · ");
    }
    return String(value);
  }

  function appendRows(host, rows) {
    const list = node("dl", "component-registry-metadata");
    rows.forEach(([label, value]) => {
      list.append(node("dt", "", label), node("dd", "", display(value)));
    });
    host.append(list);
  }

  function section(host, title, rows) {
    const value = node("section", "component-registry-detail-section");
    value.append(node("h4", "", title));
    appendRows(value, rows);
    host.append(value);
  }

  function primaryLifecycle(component) {
    const record = component.lifecycle_records[component.lifecycle_records.length - 1] || {};
    return record.current_state || record.state || "unavailable";
  }

  function canonicalPath(component) {
    const source = component.canonical_source || {};
    return source.locator?.value
      || source.locator
      || source.path
      || source.canonical_path
      || "Unavailable";
  }

  function renderComponent(host, record) {
    host.replaceChildren(node("h3", "", record.display_name));
    section(host, "Identity and classification", [
      ["Stable ID", record.stable_id],
      ["Class", readable(record.classification.component_class)],
      ["Type", readable(record.classification.component_type)],
      ["Roles", record.classification.roles],
      ["Capabilities", record.classification.capabilities],
      ["Owner", record.owner]
    ]);
    section(host, "Lifecycle and operation", [
      ["Lifecycle", primaryLifecycle(record)],
      ["Operational status", record.operational_status],
      ["Lifecycle history", record.lifecycle_records]
    ]);
    section(host, "Authority", [
      ["Assignments", record.authority_records]
    ]);
    section(host, "Canonical source and binding", [
      ["Canonical source", canonicalPath(record)],
      ["Source binding", record.canonical_source.source_binding]
    ]);
    section(host, "Information and retention", [
      ["Information handling", record.information_handling],
      ["Retention", record.retention]
    ]);
    section(host, "Artifacts and connections", [
      ["Supporting artifacts", record.supporting_artifacts],
      ["Relationships", record.relationship_records],
      ["Migrations and aliases", record.migration_records],
      ["Provenance", record.provenance_records]
    ]);
  }

  function renderLifecycle(host, record, snapshot) {
    host.replaceChildren(node("h3", "", record.display_name || record.component_id));
    const state = record.current_state || record.state;
    const definition = snapshot.lifecycles.states[state];
    section(host, "Current assignment", [
      ["Component", record.component_id],
      ["State", readable(state)],
      ["Definition", definition],
      ["Effective date", record.effective_date],
      ["Transition reason", record.transition_reason]
    ]);
    section(host, "Lifecycle history", [
      ["Transitions", record.history || record.transitions],
      ["Provenance", record.provenance_ref || record.provenance_refs]
    ]);
  }

  function renderAuthority(host, record) {
    host.replaceChildren(node("h3", "", record.display_name || record.component_id));
    section(host, "Authority assignment", [
      ["Assignment ID", record.assignment_id],
      ["Component", record.component_id],
      ["Status", record.authoritative ? "Authoritative" : "Nonauthoritative"],
      ["Subjects", record.subjects],
      ["Effects", record.effects],
      ["Exclusions", record.exclusions],
      ["Effective date", record.effective_date],
      ["Termination conditions", record.termination_conditions]
    ]);
    section(host, "Authority chain", [
      ["Sources", record.sources],
      ["Governing precedence", record.governing_precedence],
      ["Provenance", record.provenance_ref || record.provenance_refs]
    ]);
  }

  function endpoint(value) {
    return object(value) ? `${value.id} (${readable(value.kind)})` : display(value);
  }

  function renderRelationship(host, record) {
    host.replaceChildren(node("h3", "", readable(record.relationship_type)));
    appendRows(host, [
      ["Relationship ID", record.relationship_id],
      ["From", endpoint(record.from)],
      ["To", endpoint(record.to)],
      ["Effective date", record.effective_date],
      ["Provenance", record.provenance_ref || record.provenance_refs],
      ["Authority boundary", record.authority_boundary]
    ]);
  }

  function renderCoverage(host, record, snapshot) {
    host.replaceChildren(node("h3", "", record.display_name || record.coverage_id));
    appendRows(host, [
      ["Coverage ID", record.coverage_id],
      ["Kind", readable(record.coverage_kind)],
      ["Path or pattern", record.path_pattern || record.path || record.pattern],
      ["Owning component", record.component_id || record.owner_component_id],
      ["Authorized producers", record.authorized_producers || record.producers],
      ["Child policy", record.child_policy],
      ["Disclosure", record.disclosure_boundary || record.information_handling],
      ["Disposition", record.disposition || record.retirement_condition],
      ["Fallback", record.fallback],
      ["Covered repository paths", snapshot.coverage.path_count],
      ["Unresolved", snapshot.coverage.uncovered_count]
    ]);
  }

  function renderRouting(host, record) {
    host.replaceChildren(node("h3", "", record.label));
    appendRows(host, [
      ["Selection ID", record.routing_id],
      ["Kind", readable(record.routing_kind)],
      ["Resolved components", record.component_ids],
      ["Registered details", record.details]
    ]);
  }

  function renderTerminology(host, record) {
    host.replaceChildren(
      node("h3", "", record.label),
      node("p", "component-registry-term-id", record.term_id),
      ...record.definition.split("\n\n").map((paragraph) => node("p", "", paragraph))
    );
  }

  function optionValues(select, values, allLabel) {
    if (!select || select.dataset.registryOptions === "true") return;
    select.replaceChildren(node("option", "", allLabel));
    select.firstElementChild.value = "";
    [...new Set(values.filter(text))].sort().forEach((value) => {
      const option = node("option", "", readable(value));
      option.value = value;
      select.append(option);
    });
    select.dataset.registryOptions = "true";
  }

  function searchable(record) {
    return JSON.stringify(record).toLocaleLowerCase();
  }

  function renderList(host, records, selectedId, id, title, meta, route) {
    host.replaceChildren();
    if (!records.length) {
      host.append(node("p", "empty-state compact-empty", "No records match these filters."));
      return;
    }
    const rows = [];
    records.forEach((record) => {
      const row = node("button", "email-list-row component-registry-list-row");
      const selected = id(record) === selectedId;
      row.type = "button";
      row.setAttribute("role", "option");
      row.setAttribute("aria-selected", String(selected));
      row.tabIndex = selected ? 0 : -1;
      if (selected) row.classList.add("selected");
      row.append(
        node("strong", "email-row-title", title(record)),
        node("span", "email-row-time", meta(record)),
        node("span", "email-row-summary", id(record))
      );
      row.addEventListener("click", () => {
        global.location.hash = `#${route(record)}`;
      });
      row.addEventListener("keydown", (event) => {
        if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
        const current = rows.indexOf(row);
        const next = event.key === "Home" ? 0
          : event.key === "End" ? rows.length - 1
            : event.key === "ArrowDown" ? Math.min(rows.length - 1, current + 1)
              : Math.max(0, current - 1);
        event.preventDefault();
        rows[next].focus();
      });
      rows.push(row);
      host.append(row);
    });
  }

  function setCount(mode, count) {
    const host = document.getElementById(`component-registry-${mode}-count`);
    if (!host) return;
    host.hidden = false;
    host.textContent = String(count);
  }

  function bindFilter(id, render) {
    const control = document.getElementById(id);
    if (!control || control.dataset.registryBound === "true") return;
    control.dataset.registryBound = "true";
    control.addEventListener(control.tagName === "SELECT" ? "change" : "input", render);
  }

  function renderLifecycleSummary(snapshot) {
    const portals = document.getElementById("component-registry-lifecycle-portals");
    const flow = document.getElementById("component-registry-lifecycle-flow");
    if (portals) {
      portals.replaceChildren();
      Object.entries(snapshot.lifecycles.states).forEach(([state, definition]) => {
        const count = snapshot.lifecycles.assignments.filter((record) =>
          (record.current_state || record.state) === state).length;
        const card = node("article", "component-registry-state-portal");
        card.title = display(definition);
        card.append(node("span", "", readable(state)), node("strong", "", count));
        portals.append(card);
      });
    }
    if (flow) {
      flow.replaceChildren();
      snapshot.lifecycles.permitted_transitions.forEach(([from, to]) => {
        flow.append(node("span", "component-registry-transition", `${readable(from)} → ${readable(to)}`));
      });
    }
  }

  function applyMode(mode) {
    MODES.forEach((candidate) => {
      const button = document.getElementById(`component-registry-mode-${candidate}`);
      const panel = document.getElementById(`component-registry-panel-${candidate}`);
      if (button) {
        const selected = candidate === mode;
        button.setAttribute("aria-selected", String(selected));
        button.tabIndex = selected ? 0 : -1;
      }
      if (panel) panel.hidden = candidate !== mode;
    });
  }

  function bindModes(snapshot) {
    const buttons = MODES.map((mode) =>
      document.getElementById(`component-registry-mode-${mode}`));
    buttons.forEach((button, index) => {
      if (!button || button.dataset.registryBound === "true") return;
      button.dataset.registryBound = "true";
      button.addEventListener("click", () => {
        global.location.hash = `#${snapshot.routes[button.dataset.registryMode]}`;
      });
      button.addEventListener("keydown", (event) => {
        let next = null;
        if (event.key === "ArrowRight") next = (index + 1) % buttons.length;
        if (event.key === "ArrowLeft") next = (index - 1 + buttons.length) % buttons.length;
        if (event.key === "Home") next = 0;
        if (event.key === "End") next = buttons.length - 1;
        if (next === null) return;
        event.preventDefault();
        buttons[next].focus();
      });
    });
  }

  function unavailable() {
    const status = document.getElementById("component-registry-status");
    if (status) {
      status.className = "status-badge unavailable";
      status.textContent = "Unavailable";
    }
    MODES.forEach((mode) => {
      const detail = document.getElementById(
        `component-registry-${mode === "components" ? "component" : mode === "lifecycles" ? "lifecycle" : mode}-detail`
      );
      if (detail) detail.replaceChildren(
        node("p", "empty-state compact-empty", "Component Registry data unavailable.")
      );
    });
  }

  function render(snapshot, target = "") {
    if (snapshot?.schema_version === 1) {
      return legacyApi.render(snapshot, target);
    }
    if (!validSnapshot(snapshot)) {
      unavailable();
      return false;
    }
    const state = routeState(target, snapshot);
    const status = document.getElementById("component-registry-status");
    status.className = "status-badge warning";
    status.textContent = "Proposed Stage 2 revision";
    const notice = document.getElementById("component-registry-deferred");
    notice.replaceChildren(
      node("strong", "", "Proposed — nonauthoritative"),
      node("p", "", "This view is generated from the validated Stage 2 Registry revision. Live authority remains separately receipt-bound."),
      node("p", "", `Registry revision ${snapshot.registry.registry_revision} · ${snapshot.registry.registry_sha256}`)
    );
    bindModes(snapshot);
    renderLifecycleSummary(snapshot);

    const componentSearch = document.getElementById("component-registry-components-search");
    const componentClass = document.getElementById("component-registry-components-class");
    const componentLifecycle = document.getElementById("component-registry-components-lifecycle");
    optionValues(componentClass, snapshot.components.map((record) =>
      record.classification.component_class), "All classes");
    optionValues(componentLifecycle, snapshot.components.map(primaryLifecycle), "All states");
    const renderComponents = () => {
      const query = componentSearch.value.trim().toLocaleLowerCase();
      const filtered = snapshot.components.filter((record) =>
        (!query || searchable(record).includes(query))
        && (!componentClass.value || record.classification.component_class === componentClass.value)
        && (!componentLifecycle.value || primaryLifecycle(record) === componentLifecycle.value));
      document.getElementById("component-registry-components-results").textContent =
        `${filtered.length} of ${snapshot.components.length} components`;
      const selected = filtered.find((record) => record.stable_id === state.selected) || filtered[0];
      renderList(
        document.getElementById("component-registry-component-list"),
        filtered,
        selected?.stable_id,
        (record) => record.stable_id,
        (record) => record.display_name,
        (record) => `${readable(record.classification.component_class)} · ${readable(primaryLifecycle(record))}`,
        (record) => record.console_route
      );
      if (selected) renderComponent(document.getElementById("component-registry-component-detail"), selected);
    };
    ["component-registry-components-search", "component-registry-components-class", "component-registry-components-lifecycle"]
      .forEach((id) => bindFilter(id, renderComponents));
    renderComponents();

    const lifecycleSearch = document.getElementById("component-registry-lifecycles-search");
    const lifecycleState = document.getElementById("component-registry-lifecycles-state");
    optionValues(lifecycleState, Object.keys(snapshot.lifecycles.states), "All states");
    const renderLifecycles = () => {
      const query = lifecycleSearch.value.trim().toLocaleLowerCase();
      const filtered = snapshot.lifecycles.assignments.filter((record) => {
        const current = record.current_state || record.state;
        return (!query || searchable(record).includes(query))
          && (!lifecycleState.value || current === lifecycleState.value);
      });
      document.getElementById("component-registry-lifecycles-results").textContent =
        `${filtered.length} of ${snapshot.lifecycles.assignments.length} assignments`;
      const selected = filtered.find((record) => record.assignment_id === state.selected) || filtered[0];
      renderList(document.getElementById("component-registry-lifecycle-list"), filtered,
        selected?.assignment_id, (record) => record.assignment_id,
        (record) => record.display_name || record.component_id,
        (record) => readable(record.current_state || record.state),
        (record) => record.console_route);
      if (selected) renderLifecycle(document.getElementById("component-registry-lifecycle-detail"), selected, snapshot);
    };
    ["component-registry-lifecycles-search", "component-registry-lifecycles-state"]
      .forEach((id) => bindFilter(id, renderLifecycles));
    renderLifecycles();

    const authoritySearch = document.getElementById("component-registry-authority-search");
    const authorityStatus = document.getElementById("component-registry-authority-status");
    const renderAuthorities = () => {
      const query = authoritySearch.value.trim().toLocaleLowerCase();
      const filtered = snapshot.authorities.assignments.filter((record) =>
        (!query || searchable(record).includes(query))
        && (!authorityStatus.value
          || (authorityStatus.value === "authoritative") === record.authoritative));
      document.getElementById("component-registry-authority-results").textContent =
        `${filtered.length} of ${snapshot.authorities.assignments.length} assignments`;
      const selected = filtered.find((record) => record.assignment_id === state.selected) || filtered[0];
      renderList(document.getElementById("component-registry-authority-list"), filtered,
        selected?.assignment_id, (record) => record.assignment_id,
        (record) => record.display_name || record.component_id,
        (record) => record.authoritative ? "Authoritative" : "Nonauthoritative",
        (record) => record.console_route);
      if (selected) renderAuthority(document.getElementById("component-registry-authority-detail"), selected);
    };
    ["component-registry-authority-search", "component-registry-authority-status"]
      .forEach((id) => bindFilter(id, renderAuthorities));
    renderAuthorities();

    const relationshipSearch = document.getElementById("component-registry-relationships-search");
    const relationshipType = document.getElementById("component-registry-relationships-type");
    optionValues(relationshipType, snapshot.relationships.map((record) => record.relationship_type), "All types");
    const renderRelationships = () => {
      const query = relationshipSearch.value.trim().toLocaleLowerCase();
      const filtered = snapshot.relationships.filter((record) =>
        (!query || searchable(record).includes(query))
        && (!relationshipType.value || record.relationship_type === relationshipType.value));
      document.getElementById("component-registry-relationships-results").textContent =
        `${filtered.length} of ${snapshot.relationships.length} relationships`;
      const selected = filtered.find((record) => record.relationship_id === state.selected) || filtered[0];
      renderList(document.getElementById("component-registry-relationship-list"), filtered,
        selected?.relationship_id, (record) => record.relationship_id,
        (record) => `${endpoint(record.from)} → ${endpoint(record.to)}`,
        (record) => readable(record.relationship_type),
        (record) => record.console_route);
      if (selected) renderRelationship(document.getElementById("component-registry-relationship-detail"), selected);
    };
    ["component-registry-relationships-search", "component-registry-relationships-type"]
      .forEach((id) => bindFilter(id, renderRelationships));
    renderRelationships();

    const coverageSearch = document.getElementById("component-registry-coverage-search");
    const coverageKind = document.getElementById("component-registry-coverage-kind");
    const renderCoverageRows = () => {
      const query = coverageSearch.value.trim().toLocaleLowerCase();
      const filtered = snapshot.coverage.records.filter((record) =>
        (!query || searchable(record).includes(query))
        && (!coverageKind.value || record.coverage_kind === coverageKind.value));
      document.getElementById("component-registry-coverage-results").textContent =
        `${filtered.length} rules · ${snapshot.coverage.path_count} covered paths · ${snapshot.coverage.uncovered_count} unresolved`;
      const selected = filtered.find((record) => record.coverage_id === state.selected) || filtered[0];
      renderList(document.getElementById("component-registry-coverage-list"), filtered,
        selected?.coverage_id, (record) => record.coverage_id,
        (record) => record.display_name || record.coverage_id,
        (record) => readable(record.coverage_kind),
        (record) => record.console_route);
      if (selected) renderCoverage(document.getElementById("component-registry-coverage-detail"), selected, snapshot);
    };
    ["component-registry-coverage-search", "component-registry-coverage-kind"]
      .forEach((id) => bindFilter(id, renderCoverageRows));
    renderCoverageRows();

    const routingSearch = document.getElementById("component-registry-routing-search");
    const renderRoutingRows = () => {
      const query = routingSearch.value.trim().toLocaleLowerCase();
      const filtered = snapshot.routing.selections.filter((record) =>
        !query || searchable(record).includes(query));
      document.getElementById("component-registry-routing-results").textContent =
        `${filtered.length} of ${snapshot.routing.selections.length} selections`;
      const selected = filtered.find((record) => record.routing_id === state.selected) || filtered[0];
      renderList(document.getElementById("component-registry-routing-list"), filtered,
        selected?.routing_id, (record) => record.routing_id,
        (record) => record.label, (record) => readable(record.routing_kind),
        (record) => record.console_route);
      if (selected) renderRouting(document.getElementById("component-registry-routing-detail"), selected);
    };
    bindFilter("component-registry-routing-search", renderRoutingRows);
    renderRoutingRows();

    const terminologySearch = document.getElementById("component-registry-terminology-search");
    const renderTerms = () => {
      const filtered = filterTerminologyEntries(snapshot.terminology.entries, terminologySearch.value);
      document.getElementById("component-registry-terminology-results").textContent =
        `${filtered.length} of ${snapshot.terminology.entries.length} adopted terms`;
      const selected = filtered.find((record) => record.term_id === state.selected) || filtered[0];
      renderList(document.getElementById("component-registry-terminology-list"), filtered,
        selected?.term_id, (record) => record.term_id,
        (record) => record.label, () => "Adopted", (record) => record.console_route);
      if (selected) renderTerminology(document.getElementById("component-registry-terminology-detail"), selected);
    };
    bindFilter("component-registry-terminology-search", renderTerms);
    renderTerms();

    setCount("components", snapshot.components.length);
    setCount("lifecycles", snapshot.lifecycles.assignments.length);
    setCount("authority", snapshot.authorities.assignments.length);
    setCount("relationships", snapshot.relationships.length);
    setCount("coverage", snapshot.coverage.records.length);
    setCount("routing", snapshot.routing.selections.length);
    setCount("terminology", snapshot.terminology.entries.length);
    applyMode(state.mode);
    return true;
  }

  function filterTerminologyEntries(entries, query) {
    const tokens = String(query || "").trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    if (!tokens.length) return [...entries];
    return entries.filter((entry) => {
      const value = `${entry.term_id} ${entry.label} ${entry.definition}`.toLocaleLowerCase();
      return tokens.every((token) => value.includes(token));
    });
  }

  global.ARRP_COMPONENT_REGISTRY = Object.freeze({
    schemaVersion: 1,
    pendingDisplay: legacyApi.pendingDisplay,
    validSnapshot,
    routeState,
    filterTerminologyEntries,
    render
  });
})(window);
