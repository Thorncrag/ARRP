"""Deterministic closure evidence for the context-routing rule migration."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess
import unittest
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from scripts.arrp_context import extract_exact_heading
from scripts import record_review_epoch, run_coordinator
from scripts import component_registry as registry_tool


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "framework" / "CONTEXT_ROUTING.md"
if not SOURCE_PATH.exists():
    SOURCE_PATH = (
        ROOT / "framework" / "archive" / "authorities"
        / "CONTEXT_ROUTING.md"
    )
REGISTRY_PATH = ROOT / "framework" / "component-registry.json"
STAGE1_CANONICAL_REVISION = "357293fc3bd814618fefdede91cd1008ce8683d8"
SCHEMA_PATH = (
    ROOT
    / "framework"
    / "standards"
    / "automation"
    / "component-registry.schema.json"
)
MATRIX_PATH = (
    ROOT
    / "framework"
    / "receipts"
    / "component-registry"
    / "context-routing-v1-rule-closure.json"
)
SOURCE_SHA256 = (
    "246a2bc927fa232507ac733192c42f42e469557b3b25cd92d74c111ef6d5e4a7"
)
BASE_BLUEPRINT_REVISION = (
    "sha256:"
    "a3dd3fa31c3e02b5fbddc89b1aa293ec0164e667d45f4142ebaa884020989ac8"
)
ROUTING_CATALOG_REVISION = f"sha256:{SOURCE_SHA256}"
ROUTING_CATALOG_APPROVAL_REFERENCE = (
    "codex-thread:019fa401-0c64-7c00-ab6b-636e7e516a88:"
    "2026-07-30:routing-rule-catalog-approval"
)
ACTIVATION_AUTHORITY_MODES_REVISION = (
    "sha256:277d9e59882d3c49399526e15a50adb6f1098f4a7a1898ff8ac1941bc7f6148f"
)
ACTIVE_PREDECESSOR_RETIREMENT_REVISION = (
    "sha256:19f03f6daacb580680cb481bf93caf2c7efdd5b4afb4e8ce1486dd9a61575f44"
)
ULTRA_ACCEPTANCE_CORRECTIONS_REVISION = (
    "sha256:6b9f8f7cf12059730ff7406feb59178bca501d23181cb0147cb6f137f60c15fb"
)

APPROVED_RULES = {
    "invariants": {
        "ctxr.inv.router_preserves_source_authority",
        "ctxr.inv.required_floor_is_minimum",
        "ctxr.inv.additive_union",
        "ctxr.inv.dependencies_are_directional_minimums",
        "ctxr.inv.dependency_graph_is_acyclic",
        "ctxr.inv.stable_document_identity_is_path_independent",
        "ctxr.inv.bounded_context_never_omits_material_authority",
    },
    "selection": {
        "ctxr.sel.primary_profile",
        "ctxr.sel.required_floor_order",
        "ctxr.sel.profile_starting_set",
        "ctxr.sel.all_implicated_capabilities",
        "ctxr.sel.profile_never_excludes_capability",
        "ctxr.sel.capability_addition_requires_no_new_profile",
        "ctxr.sel.profile_documents_and_exact_sections",
        "ctxr.sel.complete_dependency_closure",
        "ctxr.sel.task_specific_canonical_material",
        "ctxr.sel.source_projection_requires_canonical_readback",
        "ctxr.sel.dynamic_trigger_set",
        "ctxr.sel.expansion_precedes_dependent_action",
        "ctxr.sel.multi_agent_before_delegation",
        "ctxr.sel.governance_recording_plus_change_audit",
        "ctxr.sel.interactive_route_is_minimum_not_ceiling",
        "ctxr.sel.automated_expansion_allowlist",
        "ctxr.sel.deterministic_bot_structured_inputs",
    },
    "validation": {
        "ctxr.val.registry_before_selection",
        "ctxr.val.integration_pinned_digest_exact",
        "ctxr.val.runtime_digest_at_packet_build",
        "ctxr.val.expansion_provenance_preserved",
        "ctxr.val.exact_section_unique",
        "ctxr.val.packet_manifest_bound",
        "ctxr.val.authorized_digest_update_atomic",
        "ctxr.val.registry_digest_external",
        "ctxr.val.new_authoritative_module_admission",
        "ctxr.val.id_rename_change_audit",
    },
    "failure_rules": {
        "ctxr.fail.unknown_or_missing_selection",
        "ctxr.fail.pinned_digest_absent_or_stale",
        "ctxr.fail.runtime_digest_unreadable",
        "ctxr.fail.dependency_cycle",
        "ctxr.fail.generated_or_excluded_as_authority",
        "ctxr.fail.section_identity_invalid",
        "ctxr.fail.section_budget_exceeded",
        "ctxr.fail.packet_budget_exceeded",
        "ctxr.fail.unresolved_material_governing_gap",
        "ctxr.fail.safe_failure_disposition",
    },
    "currentness": {
        "ctxr.cur.stable_governing_is_pinned",
        "ctxr.cur.mutable_handoff_is_runtime_hashed",
        "ctxr.cur.checkpoint_update_needs_no_registry_edit",
        "ctxr.cur.generated_rebuildables_excluded",
        "ctxr.cur.records_excluded_except_handoff",
        "ctxr.cur.runtime_nongoverning_excluded_from_review_boundary",
    },
    "budgets": {
        "ctxr.budget.profile_max_is_fail_closed_ceiling",
        "ctxr.budget.ceiling_change_does_not_change_membership",
        "ctxr.budget.section_and_packet_limits_are_independent",
        "ctxr.budget.no_mandatory_trimming",
    },
    "comprehensive_review": {
        "ctxr.review.select_all_active_governing",
        "ctxr.review.periodic_epoch_required",
        "ctxr.review.boundary_exact",
        "ctxr.review.any_valid_boundary_difference_due",
        "ctxr.review.invalid_drift_is_integrity_failure",
        "ctxr.review.completion_fields_exact",
        "ctxr.review.recorder_requires_exact_current_boundary",
        "ctxr.review.unresolved_findings_carry_forward",
        "ctxr.review.next_epoch_uses_delta_and_carry_forward",
        "ctxr.review.efficiency_never_limits_scope_or_lookback",
    },
}
ALL_APPROVED_RULES = set().union(*APPROVED_RULES.values())
REGISTERED_PHASES = {
    "registry_state",
    "route_definition",
    "packet_build",
    "dynamic_expansion",
    "governance_change",
    "review_epoch",
    "failure_disposition",
}
APPROVED_FAILURE_CODES = {
    "CTXR_UNKNOWN_OR_MISSING_SELECTION",
    "CTXR_PINNED_DIGEST_ABSENT_OR_STALE",
    "CTXR_RUNTIME_DIGEST_UNREADABLE",
    "CTXR_DEPENDENCY_CYCLE",
    "CTXR_GENERATED_OR_EXCLUDED_AS_AUTHORITY",
    "CTXR_SECTION_IDENTITY_INVALID",
    "CTXR_SECTION_BUDGET_EXCEEDED",
    "CTXR_PACKET_BUDGET_EXCEEDED",
    "CTXR_UNRESOLVED_MATERIAL_GOVERNING_GAP",
    "CTXR_SAFE_FAILURE_DISPOSITION",
}
SOURCE_CLAUSE_FIELDS = {
    "clause_key",
    "rule_id",
    "category",
    "source_heading",
    "source_line_ranges",
}
ASSURANCE_ROW_FIELDS = {
    "rule_id",
    "assurance_mode",
    "registered_phase",
    "registered_failure_code",
    "negative_fixture_id",
    "catalog_verification_id",
    "implementation_anchor",
    "packet_inclusion",
    "test_anchor",
}
ASSURANCE_MODES = {
    "deterministic_enforcement",
    "governing_instruction_precondition",
    "candidate_validation_only",
}
RULES_BY_ASSURANCE_MODE = {
    "candidate_validation_only": {
        "ctxr.inv.router_preserves_source_authority",
    },
    "governing_instruction_precondition": {
        "ctxr.inv.dependencies_are_directional_minimums",
        "ctxr.inv.bounded_context_never_omits_material_authority",
        "ctxr.sel.all_implicated_capabilities",
        "ctxr.sel.task_specific_canonical_material",
        "ctxr.sel.source_projection_requires_canonical_readback",
        "ctxr.sel.dynamic_trigger_set",
        "ctxr.sel.expansion_precedes_dependent_action",
        "ctxr.sel.multi_agent_before_delegation",
        "ctxr.sel.governance_recording_plus_change_audit",
        "ctxr.sel.interactive_route_is_minimum_not_ceiling",
        "ctxr.sel.automated_expansion_allowlist",
        "ctxr.sel.deterministic_bot_structured_inputs",
        "ctxr.val.expansion_provenance_preserved",
        "ctxr.val.authorized_digest_update_atomic",
        "ctxr.val.new_authoritative_module_admission",
        "ctxr.val.id_rename_change_audit",
        "ctxr.fail.unresolved_material_governing_gap",
        "ctxr.fail.safe_failure_disposition",
        "ctxr.review.efficiency_never_limits_scope_or_lookback",
    },
}
RULES_BY_ASSURANCE_MODE["deterministic_enforcement"] = (
    ALL_APPROVED_RULES
    - RULES_BY_ASSURANCE_MODE["candidate_validation_only"]
    - RULES_BY_ASSURANCE_MODE["governing_instruction_precondition"]
)
APPROVED_ASSURANCE_MODE_BY_RULE = {
    rule_id: mode
    for mode, rule_ids in RULES_BY_ASSURANCE_MODE.items()
    for rule_id in rule_ids
}
RULES_BY_PHASE = {
    "registry_state": {"ctxr.val.registry_before_selection"},
    "route_definition": {
        "ctxr.inv.router_preserves_source_authority",
        "ctxr.inv.dependencies_are_directional_minimums",
        "ctxr.inv.dependency_graph_is_acyclic",
        "ctxr.sel.required_floor_order",
        "ctxr.sel.profile_starting_set",
        "ctxr.sel.capability_addition_requires_no_new_profile",
        "ctxr.sel.deterministic_bot_structured_inputs",
        "ctxr.fail.dependency_cycle",
        "ctxr.fail.generated_or_excluded_as_authority",
        "ctxr.cur.stable_governing_is_pinned",
        "ctxr.cur.mutable_handoff_is_runtime_hashed",
        "ctxr.cur.generated_rebuildables_excluded",
        "ctxr.cur.records_excluded_except_handoff",
    },
    "dynamic_expansion": {
        "ctxr.sel.dynamic_trigger_set",
        "ctxr.sel.expansion_precedes_dependent_action",
        "ctxr.sel.multi_agent_before_delegation",
        "ctxr.sel.automated_expansion_allowlist",
        "ctxr.val.expansion_provenance_preserved",
    },
    "governance_change": {
        "ctxr.inv.stable_document_identity_is_path_independent",
        "ctxr.sel.governance_recording_plus_change_audit",
        "ctxr.val.authorized_digest_update_atomic",
        "ctxr.val.new_authoritative_module_admission",
        "ctxr.val.id_rename_change_audit",
        "ctxr.cur.checkpoint_update_needs_no_registry_edit",
        "ctxr.budget.ceiling_change_does_not_change_membership",
    },
    "review_epoch": {
        "ctxr.cur.runtime_nongoverning_excluded_from_review_boundary",
        *APPROVED_RULES["comprehensive_review"],
    },
    "failure_disposition": {"ctxr.fail.safe_failure_disposition"},
}
RULES_BY_PHASE["packet_build"] = ALL_APPROVED_RULES - set().union(
    *RULES_BY_PHASE.values()
)
APPROVED_PHASE_BY_RULE = {
    rule_id: phase
    for phase, rule_ids in RULES_BY_PHASE.items()
    for rule_id in rule_ids
}
RULES_BY_FAILURE_CODE = {
    "CTXR_DEPENDENCY_CYCLE": {
        "ctxr.inv.dependency_graph_is_acyclic",
        "ctxr.fail.dependency_cycle",
    },
    "CTXR_GENERATED_OR_EXCLUDED_AS_AUTHORITY": {
        "ctxr.sel.automated_expansion_allowlist",
        "ctxr.fail.generated_or_excluded_as_authority",
        "ctxr.cur.generated_rebuildables_excluded",
        "ctxr.cur.records_excluded_except_handoff",
    },
    "CTXR_SECTION_IDENTITY_INVALID": {
        "ctxr.sel.profile_documents_and_exact_sections",
        "ctxr.val.exact_section_unique",
        "ctxr.fail.section_identity_invalid",
    },
    "CTXR_SECTION_BUDGET_EXCEEDED": {
        "ctxr.fail.section_budget_exceeded",
        "ctxr.budget.section_and_packet_limits_are_independent",
    },
    "CTXR_PACKET_BUDGET_EXCEEDED": {
        "ctxr.inv.bounded_context_never_omits_material_authority",
        "ctxr.fail.packet_budget_exceeded",
        "ctxr.budget.profile_max_is_fail_closed_ceiling",
        "ctxr.budget.no_mandatory_trimming",
        "ctxr.review.efficiency_never_limits_scope_or_lookback",
    },
    "CTXR_RUNTIME_DIGEST_UNREADABLE": {
        "ctxr.val.runtime_digest_at_packet_build",
        "ctxr.val.expansion_provenance_preserved",
        "ctxr.fail.runtime_digest_unreadable",
        "ctxr.cur.mutable_handoff_is_runtime_hashed",
        "ctxr.cur.runtime_nongoverning_excluded_from_review_boundary",
    },
    "CTXR_PINNED_DIGEST_ABSENT_OR_STALE": {
        "ctxr.val.integration_pinned_digest_exact",
        "ctxr.val.authorized_digest_update_atomic",
        "ctxr.val.registry_digest_external",
        "ctxr.fail.pinned_digest_absent_or_stale",
        "ctxr.cur.stable_governing_is_pinned",
        "ctxr.review.boundary_exact",
        "ctxr.review.invalid_drift_is_integrity_failure",
        "ctxr.review.recorder_requires_exact_current_boundary",
    },
    "CTXR_SAFE_FAILURE_DISPOSITION": {
        "ctxr.fail.safe_failure_disposition",
    },
    "CTXR_UNRESOLVED_MATERIAL_GOVERNING_GAP": {
        "ctxr.inv.router_preserves_source_authority",
        "ctxr.inv.dependencies_are_directional_minimums",
        "ctxr.inv.stable_document_identity_is_path_independent",
        "ctxr.sel.source_projection_requires_canonical_readback",
        "ctxr.val.new_authoritative_module_admission",
        "ctxr.val.id_rename_change_audit",
        "ctxr.fail.unresolved_material_governing_gap",
        "ctxr.cur.checkpoint_update_needs_no_registry_edit",
        "ctxr.budget.ceiling_change_does_not_change_membership",
        "ctxr.review.any_valid_boundary_difference_due",
        "ctxr.review.unresolved_findings_carry_forward",
        "ctxr.review.next_epoch_uses_delta_and_carry_forward",
    },
}
RULES_BY_FAILURE_CODE["CTXR_UNKNOWN_OR_MISSING_SELECTION"] = (
    ALL_APPROVED_RULES - set().union(*RULES_BY_FAILURE_CODE.values())
)
APPROVED_FAILURE_CODE_BY_RULE = {
    rule_id: code
    for code, rule_ids in RULES_BY_FAILURE_CODE.items()
    for rule_id in rule_ids
}
GOVERNING_INSTRUCTION_TEST_ANCHOR = (
    "tests/framework/test_context_routing_rule_closure.py"
    "::ContextRoutingRuleClosureTests"
    "::test_governing_instruction_assurance_is_pinned_and_packet_included"
)
PREDECESSOR_IDS = {
    "project_structure",
    "context_routing",
    "repository_map",
    "context_routes_source",
}
PREDECESSOR_VERIFICATION_IDS = [
    "test_active_predecessor_provenance_is_closed",
    "test_active_loader_does_not_read_predecessors",
    "test_active_embedded_route_excludes_predecessors",
]
PREDECESSOR_ALIAS_IDS = [
    "relocate_project_structure",
    "relocate_context_routing",
    "relocate_repository_map",
    "relocate_context_routes_source",
]
PREDECESSOR_PATHS = {
    "framework/PROJECT_STRUCTURE.md",
    "framework/CONTEXT_ROUTING.md",
    "framework/project/REPOSITORY_MAP.md",
    "framework/project/automation/context-routes.json",
    "framework/archive/authorities/PROJECT_STRUCTURE.md",
    "framework/archive/authorities/CONTEXT_ROUTING.md",
    "framework/archive/authorities/REPOSITORY_MAP.md",
    "framework/archive/authorities/context-routes.json",
}

# These rules have a production predicate but not a deterministic cognitive
# interception boundary. Their assurance is exact instruction delivery only.
INSTRUCTION_ONLY_RULES = {
    "ctxr.inv.bounded_context_never_omits_material_authority",
    "ctxr.inv.dependencies_are_directional_minimums",
    "ctxr.sel.all_implicated_capabilities",
    "ctxr.sel.automated_expansion_allowlist",
    "ctxr.sel.deterministic_bot_structured_inputs",
    "ctxr.sel.dynamic_trigger_set",
    "ctxr.sel.expansion_precedes_dependent_action",
    "ctxr.sel.governance_recording_plus_change_audit",
    "ctxr.sel.interactive_route_is_minimum_not_ceiling",
    "ctxr.sel.multi_agent_before_delegation",
    "ctxr.sel.source_projection_requires_canonical_readback",
    "ctxr.sel.task_specific_canonical_material",
    "ctxr.val.authorized_digest_update_atomic",
    "ctxr.val.expansion_provenance_preserved",
    "ctxr.val.id_rename_change_audit",
    "ctxr.val.new_authoritative_module_admission",
    "ctxr.fail.safe_failure_disposition",
    "ctxr.fail.unresolved_material_governing_gap",
    "ctxr.review.efficiency_never_limits_scope_or_lookback",
}


def _load_matrix() -> dict[str, object]:
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def _load_registry() -> dict[str, object]:
    current = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if current.get("schema_version") == 2:
        current = json.loads(
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(ROOT),
                    "show",
                    f"{STAGE1_CANONICAL_REVISION}:framework/component-registry.json",
                ],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        )
    if current["status"] == "candidate":
        return current
    candidate_revision = current["source_baseline"]["repository_revision"]
    result = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "show",
            f"{candidate_revision}:framework/component-registry.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    candidate = json.loads(result.stdout)
    if (
        candidate.get("status") != "candidate"
        or registry_tool._canonical_registry_digest(candidate)
        != current["approval"]["value"]["candidate_registry_sha256"]
    ):
        raise AssertionError("active registry candidate parent is not exact")
    return candidate


def _load_schema() -> dict[str, object]:
    return json.loads(
        subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "show",
                f"{STAGE1_CANONICAL_REVISION}:framework/standards/automation/"
                "component-registry.schema.json",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )


def _stage1_path_bytes(relative_path: str) -> bytes:
    """Read one exact path from the frozen Stage 1 acceptance revision."""

    return subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "show",
            f"{STAGE1_CANONICAL_REVISION}:{relative_path}",
        ],
        check=True,
        capture_output=True,
    ).stdout


def _route_checkpoint_id(route: dict[str, object]) -> str:
    documents = route["documents"]
    return (
        "task_handoff"
        if "task_handoff" in documents
        else registry_tool.LEGACY_CONTEXT_CHECKPOINT
    )


def _known_approval_fixture() -> dict[str, object]:
    return {
        "state": "known",
        "value": {
            "approval_type": "stage1_component_registry_activation",
            "approved_by": "@Thorncrag",
            "approval_method": "explicit_recorded_owner_activation",
            "governance_change_id": "GOV-2026-001",
            "implementation_contract_id": "test-activation-contract",
            "base_revision": "a" * 40,
            "candidate_registry_sha256": "b" * 64,
            "affected_stable_ids": ["component_registry"],
            "purpose_scope": "Schema-only coherent active-state fixture.",
            "bounded_diff_sha256": "c" * 64,
            "approved_at": "2026-07-30T00:00:00-04:00",
            "owner_review_reference": "github-review:Thorncrag/ARRP#123",
        },
    }


def _active_schema_fixture(candidate: dict[str, object]) -> dict[str, object]:
    """Return a schema-complete active-shape fixture without activating state."""

    active = registry_tool.build_simulated_active_registry(
        candidate,
        repository_revision="a" * 40,
        approval_value=_known_approval_fixture()["value"],
    )
    active["context_routing"]["predecessor_provenance"][
        "schema_version"
    ] = 1
    return active

    active = copy.deepcopy(candidate)
    routing = active["context_routing"]
    documents = routing["documents"]
    operational = active["operational_documents"]["entries"]
    predecessor_digests = {
        "context_routing": operational["context_routing"]["sha256"],
        "context_routes_source": routing["source_import"]["sha256"],
    }

    documents.pop("context_routing")
    documents["codex_bootstrap"]["requires"] = [
        identity
        for identity in documents["codex_bootstrap"]["requires"]
        if identity != "context_routing"
    ]
    operational["codex_bootstrap"]["dependencies"] = list(
        documents["codex_bootstrap"]["requires"]
    )

    archived_context = operational["context_routing"]
    archived_context.update(
        {
            "canonical_path": (
                "framework/archive/authorities/CONTEXT_ROUTING.md"
            ),
            "current_status": {
                "state": "known",
                "value": "retired",
            },
            "authority_role": "archived_predecessor",
            "representations": [],
            "dependencies": [],
            "consumers": [],
            "retention_posture": "archived",
            "digest_policy": "provenance_only",
        }
    )
    archived_route = copy.deepcopy(archived_context)
    archived_route.update(
        {
            "document_id": "context_routes_source",
            "official_reference_name": {
                "state": "known",
                "value": "Historical Context Route Data",
            },
            "document_class": {
                "state": "known",
                "value": "archived_route_data_authority",
            },
            "canonical_path": (
                "framework/archive/authorities/context-routes.json"
            ),
            "console_route": (
                "operations:component-registry:documents"
                "?document=context_routes_source"
            ),
            "sha256": predecessor_digests["context_routes_source"],
        }
    )
    operational["context_routes_source"] = archived_route

    routing.pop("source_import")
    routing.pop("parity_policy")
    retirement_proof = {
        "proof_type": "authenticated_activation_cutover",
        "governance_change_id": "GOV-2026-001",
        "implementation_contract_id": (
            "COMPONENT-REGISTRY-2026-001-ACTIVATION"
        ),
        "owner_review_reference": "github-review:Thorncrag/ARRP#123",
    }
    routing["predecessor_provenance"] = {
        "schema_version": 1,
        "complete": True,
        "authority_effect": (
            "historical_provenance_only_no_runtime_read"
        ),
        "records": {
            "context_routing": {
                "stable_id": "context_routing",
                "artifact_kind": "markdown_authority",
                "historical_path": "framework/CONTEXT_ROUTING.md",
                "archived_path": (
                    "framework/archive/authorities/CONTEXT_ROUTING.md"
                ),
                "sha256": predecessor_digests["context_routing"],
                "source_schema_version": None,
                "state": "archived_retired_provenance_only",
                "retirement_proof": copy.deepcopy(retirement_proof),
            },
            "context_routes_source": {
                "stable_id": "context_routes_source",
                "artifact_kind": "route_data_authority",
                "historical_path": (
                    "framework/project/automation/context-routes.json"
                ),
                "archived_path": (
                    "framework/archive/authorities/context-routes.json"
                ),
                "sha256": predecessor_digests[
                    "context_routes_source"
                ],
                "source_schema_version": 2,
                "state": "archived_retired_provenance_only",
                "retirement_proof": copy.deepcopy(retirement_proof),
            },
        },
        "migration_alias_ids": list(PREDECESSOR_ALIAS_IDS),
        "verification_ids": list(PREDECESSOR_VERIFICATION_IDS),
    }
    routing["readable_representation"] = {
        "representation_id": "human_readable_context_routing",
        "binding_kind": "component_registry_revision",
        "source_registry_revision": active["registry_revision"],
        "generated_from": "embedded_context_routing",
        "authority_effect": "none",
        "executable": False,
    }
    routing["expected_counts"] = registry_tool.route_counts(
        registry_tool._routing_snapshot(active)
    )
    routing["activation_state"] = "active"
    routing["authoritative"] = True

    active["representations"]["entries"][
        "human_readable_context_routing"
    ].update(
        {
            "source_revision_binding": (
                "component_registry_revision:"
                f"{active['registry_revision']}"
            ),
            "canonical_path": (
                "framework/project/interfaces/project-console/data/"
                "component-registry.js"
            ),
            "state": "active",
        }
    )
    baseline = active["source_baseline"]
    baseline.pop("route_source")
    baseline["repository_state"] = "clean_committed"
    baseline["working_tree_binding"].update(
        {
            "mode": "active_revision_plus_embedded_route",
            "scope": "complete_embedded_component_registry_route",
        }
    )
    active["status"] = "active"
    active["approval"] = _known_approval_fixture()
    return active


def _test_anchor_exists(anchor: object) -> bool:
    if not isinstance(anchor, str):
        return False
    parts = anchor.split("::")
    if len(parts) != 3:
        return False
    path = ROOT / parts[0]
    if path.is_file():
        source = path.read_text(encoding="utf-8")
    else:
        source = ""
    def contains(candidate: str) -> bool:
        tree = ast.parse(candidate)
        class_node = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == parts[1]
            ),
            None,
        )
        return class_node is not None and any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == parts[2]
            for node in class_node.body
        )

    if source and contains(source):
        return True
    historical = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "show",
            f"{STAGE1_CANONICAL_REVISION}:{parts[0]}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return historical.returncode == 0 and contains(historical.stdout)


def _implementation_anchor_exists(anchor: object) -> bool:
    if not isinstance(anchor, str):
        return False
    if anchor.startswith("scripts.") and ":" in anchor:
        module, symbol = anchor.split(":", 1)
        path = ROOT / f"{module.replace('.', '/')}.py"
        if not path.is_file():
            return False
        tree = ast.parse(path.read_text(encoding="utf-8"))
        return any(
            isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            )
            and node.name == symbol
            for node in ast.walk(tree)
        )
    if anchor.startswith("framework/") and "#" in anchor:
        relative, heading = anchor.split("#", 1)
        path = ROOT / relative
        if not path.is_file():
            return False
        headings = {
            line.lstrip("#").strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("#")
        }
        return heading in headings
    return False


def _dependency_closure(
    routing: dict[str, object],
    initial: list[str],
) -> set[str]:
    documents = routing["documents"]
    selected: set[str] = set()
    pending = list(initial)
    while pending:
        document_id = pending.pop()
        if document_id in selected:
            continue
        if document_id not in documents:
            return set()
        selected.add(document_id)
        pending.extend(documents[document_id].get("requires") or [])
    return selected


def _body_blocks(lines: list[str]) -> list[tuple[int, int]]:
    """Return every nonblank, nonheading body block after front matter."""

    blocks: list[tuple[int, int]] = []
    in_front_matter = bool(lines and lines[0] == "---")
    start: int | None = None
    for line_number, line in enumerate(lines, start=1):
        if in_front_matter:
            if line_number > 1 and line == "---":
                in_front_matter = False
            continue
        structural = not line.strip() or line.startswith("#")
        if structural:
            if start is not None:
                blocks.append((start, line_number - 1))
                start = None
            continue
        if start is None:
            start = line_number
    if start is not None:
        blocks.append((start, len(lines)))
    return blocks


def _heading_at(lines: list[str], line_number: int) -> str | None:
    for candidate in range(line_number - 1, -1, -1):
        line = lines[candidate]
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return None


def _closure_errors(
    matrix: dict[str, object],
    source_bytes: bytes,
    registry: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    source_text = source_bytes.decode("utf-8")
    lines = source_text.splitlines()

    source = matrix.get("source", {})
    if source.get("document_id") != "context_routing":
        errors.append("source document identity is not context_routing")
    if source.get("path") != "framework/CONTEXT_ROUTING.md":
        errors.append("source path does not identify the predecessor")
    actual_sha = hashlib.sha256(source_bytes).hexdigest()
    if source.get("sha256") != SOURCE_SHA256 or actual_sha != SOURCE_SHA256:
        errors.append("source digest does not equal the approved pin")
    if source.get("line_count") != len(lines):
        errors.append("source line count is not exact")

    authorities = matrix.get("design_authorities", {})
    base_blueprint = authorities.get("base_blueprint", {})
    if (
        base_blueprint.get("design_id")
        != "COMPONENT-REGISTRY-2026-001-STAGE-1-LOCAL-ACCEPTANCE"
        or base_blueprint.get("design_revision") != BASE_BLUEPRINT_REVISION
        or base_blueprint.get("role") != "stage_1_architectural_blueprint"
    ):
        errors.append("base blueprint design authority is missing or mismatched")
    supplemental = authorities.get("supplemental_routing_catalog", {})
    if (
        supplemental.get("design_id")
        != "COMPONENT-REGISTRY-2026-001-ROUTING-RULE-CATALOG"
        or supplemental.get("design_revision") != ROUTING_CATALOG_REVISION
        or supplemental.get("role")
        != "approved_context_routing_rule_catalog_migration"
    ):
        errors.append(
            "supplemental routing-catalog design authority is missing or mismatched"
        )
    if set(supplemental.get("closes_decision_ids", [])) != {
        "CR-045",
        "CR-046",
    }:
        errors.append("CR-045/046 supplemental design provenance is incomplete")
    approval = supplemental.get("approval", {})
    if (
        approval.get("date") != "2026-07-30"
        or approval.get("method")
        != "explicit_user_approval_in_primary_codex_task"
        or approval.get("reference") != ROUTING_CATALOG_APPROVAL_REFERENCE
    ):
        errors.append("human routing-catalog approval evidence is incomplete")
    if set(source) & {"design_id", "design_revision", "approval"}:
        errors.append("predecessor source improperly contains design authority")
    if set(supplemental) & {
        "document_id",
        "path",
        "sha256",
        "line_count",
    }:
        errors.append("supplemental design improperly contains source authority")
    activation_modes = authorities.get("activation_authority_modes", {})
    if activation_modes != {
        "design_id": "COMPONENT-REGISTRY-2026-001-ACTIVATION-AUTHORITY-MODES",
        "design_revision": ACTIVATION_AUTHORITY_MODES_REVISION,
        "role": "approved_configuration_and_live_activation_authority_modes",
    }:
        errors.append("activation-authority-modes design provenance differs")
    predecessor_retirement = authorities.get(
        "active_predecessor_retirement",
        {},
    )
    if predecessor_retirement != {
        "design_id": "COMPONENT-REGISTRY-2026-001-ACTIVE-PREDECESSOR-RETIREMENT",
        "design_revision": ACTIVE_PREDECESSOR_RETIREMENT_REVISION,
        "role": (
            "approved_active_no_predecessor_io_and_historical_provenance_model"
        ),
    }:
        errors.append("active-predecessor-retirement design provenance differs")
    ultra_acceptance = authorities.get("ultra_acceptance_corrections", {})
    if ultra_acceptance != {
        "design_id": (
            "COMPONENT-REGISTRY-2026-001-ULTRA-ACCEPTANCE-CORRECTIONS"
        ),
        "design_revision": ULTRA_ACCEPTANCE_CORRECTIONS_REVISION,
        "role": (
            "approved_terminal_acceptance_and_routing_assurance_correction"
        ),
    }:
        errors.append("Ultra acceptance-correction design provenance differs")

    if matrix.get("authoritative") is not False:
        errors.append("migration evidence must remain nonauthoritative")
    if matrix.get("status") != "candidate":
        errors.append("pre-activation migration evidence must be candidate")

    clauses = matrix.get("clauses", [])
    clause_keys = [item.get("clause_key") for item in clauses]
    rule_ids = [item.get("rule_id") for item in clauses]
    duplicate_clause_keys = {
        key for key, count in Counter(clause_keys).items() if count != 1
    }
    duplicate_rule_ids = {
        key for key, count in Counter(rule_ids).items() if count != 1
    }
    if duplicate_clause_keys:
        errors.append(f"duplicate clause keys: {sorted(duplicate_clause_keys)}")
    if duplicate_rule_ids:
        errors.append(f"duplicate rule IDs: {sorted(duplicate_rule_ids)}")
    if set(clause_keys) != ALL_APPROVED_RULES:
        errors.append("atomic clause inventory differs from approved rules")
    if set(rule_ids) != ALL_APPROVED_RULES:
        errors.append("rule inventory differs from approved catalog")

    by_key = {item.get("clause_key"): item for item in clauses}
    routing_catalog = registry.get("context_routing", {})
    for key in ALL_APPROVED_RULES:
        clause = by_key.get(key)
        if clause is None:
            continue
        if set(clause) != SOURCE_CLAUSE_FIELDS:
            errors.append(f"{key}: source-closure evidence fields differ")
        if clause.get("rule_id") != key:
            errors.append(f"{key}: clause and rule identity differ")
        expected_category = next(
            category
            for category, identities in APPROVED_RULES.items()
            if key in identities
        )
        if clause.get("category") != expected_category:
            errors.append(f"{key}: category is not approved")
        catalog_entry = routing_catalog.get(expected_category, {}).get(key)
        if not isinstance(catalog_entry, dict):
            errors.append(f"{key}: registered catalog entry is absent")
        else:
            if (
                catalog_entry.get("rule_id") != key
                or catalog_entry.get("predicate_type") != key
                or catalog_entry.get("source_provenance", {}).get("clause_key")
                != key
            ):
                errors.append(
                    f"{key}: matrix and registered rule identity differ"
                )
            provenance = catalog_entry.get("source_provenance", {})
            if provenance.get("source_document_id") != source.get(
                "document_id"
            ):
                errors.append(
                    f"{key}: matrix and registered source identity differ"
                )
            if provenance.get("source_sha256") != source.get("sha256"):
                errors.append(
                    f"{key}: matrix and registered source digest differ"
                )
            if (
                provenance.get("source_heading")
                != clause.get("source_heading")
            ):
                errors.append(
                    f"{key}: matrix and registered source heading differ"
                )
        ranges = clause.get("source_line_ranges", [])
        if not ranges:
            errors.append(f"{key}: source provenance is absent")
            continue
        headings: set[str | None] = set()
        for span in ranges:
            if (
                not isinstance(span, list)
                or len(span) != 2
                or not all(isinstance(value, int) for value in span)
            ):
                errors.append(f"{key}: invalid source span")
                continue
            start, end = span
            if start < 1 or end < start or end > len(lines):
                errors.append(f"{key}: source span is outside predecessor")
                continue
            if not any(lines[index - 1].strip() for index in range(start, end + 1)):
                errors.append(f"{key}: source span contains no source text")
            headings.add(_heading_at(lines, start))
        if clause.get("source_heading") not in headings:
            errors.append(f"{key}: named source heading is not cited")

    blocks = matrix.get("source_blocks", [])
    block_ids = [item.get("block_id") for item in blocks]
    if len(block_ids) != len(set(block_ids)):
        errors.append("source block identity is duplicated")
    matrix_spans = [tuple(item.get("line_range", [])) for item in blocks]
    if matrix_spans != _body_blocks(lines):
        errors.append("source blocks do not exactly partition the body")

    referenced_keys: set[str] = set()
    for block in blocks:
        classification = block.get("classification")
        keys = block.get("clause_keys", [])
        if classification == "normative":
            if not keys:
                errors.append(f"{block.get('block_id')}: normative block orphaned")
            unknown = set(keys) - ALL_APPROVED_RULES
            if unknown:
                errors.append(
                    f"{block.get('block_id')}: unknown clauses {sorted(unknown)}"
                )
            referenced_keys.update(keys)
        elif classification == "registered_routing_data":
            if keys:
                errors.append(
                    f"{block.get('block_id')}: routing data coined a rule"
                )
            if block.get("verification") != "context_routing_profile_parity":
                errors.append(
                    f"{block.get('block_id')}: routing data lacks parity proof"
                )
        else:
            errors.append(
                f"{block.get('block_id')}: unregistered block classification"
            )
    if referenced_keys != ALL_APPROVED_RULES:
        errors.append("normative source blocks do not close every approved rule")

    expected = matrix.get("expected_counts", {})
    if expected.get("rules") != len(clauses):
        errors.append("declared rule count is not exact")
    if expected.get("source_blocks") != len(blocks):
        errors.append("declared source-block count is not exact")
    expected_categories = expected.get("categories", {})
    actual_categories = Counter(item.get("category") for item in clauses)
    if dict(actual_categories) != expected_categories:
        errors.append("declared category counts are not exact")
    errors.extend(_predecessor_transition_errors(matrix, registry))
    return errors


def _enforcement_closure_errors(
    matrix: dict[str, object],
    registry: dict[str, object],
) -> list[str]:
    """Return truthful per-rule assurance gaps without inventing consumers."""

    errors: list[str] = []
    assurance = matrix.get("rule_assurance")
    expected_assurance_fields = {
        "schema_version",
        "status",
        "authoritative",
        "allowed_modes",
        "mode_semantics",
        "rows",
    }
    if not isinstance(assurance, dict):
        return ["rule assurance evidence is absent"]
    if set(assurance) != expected_assurance_fields:
        errors.append("rule assurance envelope fields differ")
    if assurance.get("schema_version") != 1:
        errors.append("rule assurance schema version differs")
    if assurance.get("status") != "candidate":
        errors.append("rule assurance must remain candidate")
    if assurance.get("authoritative") is not False:
        errors.append("rule assurance must remain nonauthoritative")
    allowed_modes = assurance.get("allowed_modes")
    if (
        not isinstance(allowed_modes, list)
        or set(allowed_modes) != ASSURANCE_MODES
        or len(allowed_modes) != len(ASSURANCE_MODES)
    ):
        errors.append("rule assurance modes differ")
    mode_semantics = assurance.get("mode_semantics")
    if (
        not isinstance(mode_semantics, dict)
        or set(mode_semantics) != ASSURANCE_MODES
        or any(
            not isinstance(value, str) or not value.strip()
            for value in mode_semantics.values()
        )
    ):
        errors.append("rule assurance mode semantics are incomplete")

    rows = assurance.get("rows")
    if not isinstance(rows, list):
        return errors + ["rule assurance rows are absent"]
    row_ids = [
        row.get("rule_id") if isinstance(row, dict) else None
        for row in rows
    ]
    duplicates = {
        rule_id
        for rule_id, count in Counter(row_ids).items()
        if count != 1
    }
    if duplicates:
        errors.append(f"rule assurance identities are duplicated: {sorted(duplicates)}")
    if set(row_ids) != ALL_APPROVED_RULES:
        errors.append("rule assurance inventory differs from approved rules")
    by_rule = {
        row["rule_id"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("rule_id"), str)
    }
    negative_fixture_ids: list[object] = []
    catalog_verification_ids: list[object] = []
    routing = registry.get("context_routing", {})
    documents = routing.get("documents", {})

    for rule_id in sorted(ALL_APPROVED_RULES):
        row = by_rule.get(rule_id)
        if row is None:
            continue
        if set(row) != ASSURANCE_ROW_FIELDS:
            errors.append(f"{rule_id}: assurance evidence fields differ")
            continue
        if row.get("assurance_mode") != APPROVED_ASSURANCE_MODE_BY_RULE[
            rule_id
        ]:
            errors.append(f"{rule_id}: assurance mode differs")
        if row.get("registered_phase") != APPROVED_PHASE_BY_RULE[rule_id]:
            errors.append(f"{rule_id}: registered phase differs")
        if (
            row.get("registered_failure_code")
            != APPROVED_FAILURE_CODE_BY_RULE[rule_id]
        ):
            errors.append(f"{rule_id}: registered failure code differs")
        expected_fixture_id = f"fixture.assurance.{rule_id}"
        if row.get("negative_fixture_id") != expected_fixture_id:
            errors.append(f"{rule_id}: negative fixture identity differs")
        expected_verification_id = f"test.{rule_id}"
        if row.get("catalog_verification_id") != expected_verification_id:
            errors.append(f"{rule_id}: catalog verification identity differs")

        category = next(
            name
            for name, rule_ids in APPROVED_RULES.items()
            if rule_id in rule_ids
        )
        catalog_entry = routing.get(category, {}).get(rule_id)
        if (
            not isinstance(catalog_entry, dict)
            or expected_verification_id
            not in catalog_entry.get("verification_ids", [])
        ):
            errors.append(
                f"{rule_id}: assurance does not bind catalog verification"
            )
        if not _implementation_anchor_exists(
            row.get("implementation_anchor")
        ):
            errors.append(f"{rule_id}: implementation anchor is not real")
        if not _test_anchor_exists(row.get("test_anchor")):
            errors.append(f"{rule_id}: test anchor is not real")

        packet_inclusion = row.get("packet_inclusion")
        if row.get("assurance_mode") == "governing_instruction_precondition":
            if (
                not isinstance(packet_inclusion, dict)
                or set(packet_inclusion)
                != {"kind", "selector", "document_id"}
            ):
                errors.append(
                    f"{rule_id}: governing instruction packet binding differs"
                )
            else:
                document_id = packet_inclusion["document_id"]
                document = documents.get(document_id)
                anchor_path = str(row["implementation_anchor"]).split(
                    "#",
                    1,
                )[0]
                if (
                    not isinstance(document, dict)
                    or document.get("path") != anchor_path
                    or document.get("hash_policy") != "pinned"
                    or document.get("governing") is not True
                ):
                    errors.append(
                        f"{rule_id}: governing instruction document binding differs"
                    )
                elif (
                    hashlib.sha256(
                        _stage1_path_bytes(anchor_path)
                    ).hexdigest()
                    != document.get("sha256")
                ):
                    errors.append(
                        f"{rule_id}: governing instruction pin is stale"
                    )
                kind = packet_inclusion["kind"]
                selector = packet_inclusion["selector"]
                if kind == "required_module":
                    if (
                        selector != document_id
                        or document_id
                        not in routing.get("required_modules", [])
                    ):
                        errors.append(
                            f"{rule_id}: required-module packet binding differs"
                        )
                elif kind == "capability_dependency_closure":
                    capability = routing.get("capabilities", {}).get(selector)
                    if (
                        not isinstance(capability, list)
                        or document_id
                        not in _dependency_closure(routing, capability)
                    ):
                        errors.append(
                            f"{rule_id}: capability packet binding differs"
                        )
                else:
                    errors.append(
                        f"{rule_id}: packet inclusion kind is unregistered"
                    )
        elif packet_inclusion is not None:
            errors.append(
                f"{rule_id}: non-instruction assurance claims packet inclusion"
            )

        negative_fixture_ids.append(row.get("negative_fixture_id"))
        catalog_verification_ids.append(
            row.get("catalog_verification_id")
        )

    if (
        len(set(negative_fixture_ids)) != len(ALL_APPROVED_RULES)
        or any(
            not isinstance(item, str) or not item
            for item in negative_fixture_ids
        )
    ):
        errors.append("negative assurance fixture IDs are missing or duplicated")
    if (
        len(set(catalog_verification_ids)) != len(ALL_APPROVED_RULES)
        or any(
            not isinstance(item, str) or not item
            for item in catalog_verification_ids
        )
    ):
        errors.append(
            "catalog assurance verification IDs are missing or duplicated"
        )
    return errors


def _predecessor_transition_errors(
    matrix: dict[str, object],
    registry: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    transition = matrix.get("candidate_to_active_predecessor_transition")
    expected_fields = {
        "schema_version",
        "status",
        "authoritative",
        "candidate_counts",
        "active_counts",
        "predecessors",
        "active_no_current_io",
        "migration_alias_ids",
        "readable_representation",
        "verification_ids",
    }
    if not isinstance(transition, dict):
        return ["candidate-to-active predecessor transition is absent"]
    if set(transition) != expected_fields:
        errors.append("predecessor transition fields differ")
    if transition.get("schema_version") != 1:
        errors.append("predecessor transition schema version differs")
    if transition.get("status") != "candidate":
        errors.append("predecessor transition must remain candidate")
    if transition.get("authoritative") is not False:
        errors.append("predecessor transition must remain nonauthoritative")

    routing = registry.get("context_routing", {})
    candidate_counts = registry_tool.route_counts(
        registry_tool._routing_snapshot(registry)
    )
    candidate_counts.update(
        {
            "context_routing_route_membership": int(
                "context_routing" in routing.get("documents", {})
            ),
            "codex_bootstrap_context_routing_dependencies": (
                routing.get("documents", {})
                .get("codex_bootstrap", {})
                .get("requires", [])
                .count("context_routing")
            ),
        }
    )
    active_counts = copy.deepcopy(candidate_counts)
    active_counts["documents"] -= 3
    active_counts["governing_documents"] -= 3
    active_counts["context_routing_route_membership"] = 0
    active_counts["codex_bootstrap_context_routing_dependencies"] = 0
    if transition.get("candidate_counts") != candidate_counts:
        errors.append("candidate predecessor-transition counts differ")
    if transition.get("active_counts") != active_counts:
        errors.append("active predecessor-transition counts differ")

    predecessors = transition.get("predecessors")
    if not isinstance(predecessors, list):
        errors.append("predecessor transition records are absent")
    else:
        expected_predecessors = {
            "project_structure": {
                "artifact_kind": "markdown_authority",
                "historical_path": "framework/PROJECT_STRUCTURE.md",
                "archived_path": (
                    "framework/archive/authorities/PROJECT_STRUCTURE.md"
                ),
                "frozen_sha256_binding": (
                    "operational_documents.entries.project_structure.sha256"
                ),
                "source_schema_version": None,
            },
            "context_routing": {
                "artifact_kind": "markdown_authority",
                "historical_path": "framework/CONTEXT_ROUTING.md",
                "archived_path": (
                    "framework/archive/authorities/CONTEXT_ROUTING.md"
                ),
                "frozen_sha256_binding": (
                    "operational_documents.entries.context_routing.sha256"
                ),
                "source_schema_version": None,
            },
            "repository_map": {
                "artifact_kind": "markdown_authority",
                "historical_path": "framework/project/REPOSITORY_MAP.md",
                "archived_path": (
                    "framework/archive/authorities/REPOSITORY_MAP.md"
                ),
                "frozen_sha256_binding": (
                    "operational_documents.entries.repository_map.sha256"
                ),
                "source_schema_version": None,
            },
            "context_routes_source": {
                "artifact_kind": "route_data_authority",
                "historical_path": (
                    "framework/project/automation/context-routes.json"
                ),
                "archived_path": (
                    "framework/archive/authorities/context-routes.json"
                ),
                "frozen_sha256_binding": (
                    "context_routing.source_import.sha256"
                ),
                "source_schema_version": 2,
            },
        }
        by_id = {
            item.get("stable_id"): item
            for item in predecessors
            if isinstance(item, dict)
        }
        if set(by_id) != PREDECESSOR_IDS or len(predecessors) != 4:
            errors.append("predecessor transition identities differ")
        for stable_id, expected in expected_predecessors.items():
            actual = by_id.get(stable_id)
            if (
                not isinstance(actual, dict)
                or set(actual) != {"stable_id", *expected}
                or any(actual.get(key) != value for key, value in expected.items())
            ):
                errors.append(
                    f"{stable_id}: predecessor transition binding differs"
                )
        if (
            registry.get("operational_documents", {})
            .get("entries", {})
            .get("context_routing", {})
            .get("sha256")
            != SOURCE_SHA256
        ):
            errors.append("context_routing frozen provenance pin differs")
        route_source_digest = routing.get("source_import", {}).get("sha256")
        if (
            not isinstance(route_source_digest, str)
            or len(route_source_digest) != 64
        ):
            errors.append("context route source provenance pin is absent")

    expected_no_io = {
        "authority_effect": (
            "historical_provenance_only_no_runtime_read"
        ),
        "forbidden_current_authority_paths": sorted(PREDECESSOR_PATHS),
        "active_loader_must_not_call": (
            "scripts.arrp_context:load_route_manifest"
        ),
        "provenance_digest_policy": (
            "shape_and_internal_equality_only_no_filesystem_recompute"
        ),
    }
    actual_no_io = transition.get("active_no_current_io")
    if not isinstance(actual_no_io, dict):
        errors.append("active no-predecessor-I/O evidence is absent")
    else:
        normalized_no_io = copy.deepcopy(actual_no_io)
        if isinstance(
            normalized_no_io.get("forbidden_current_authority_paths"),
            list,
        ):
            normalized_no_io[
                "forbidden_current_authority_paths"
            ] = sorted(
                normalized_no_io["forbidden_current_authority_paths"]
            )
        if normalized_no_io != expected_no_io:
            errors.append("active no-predecessor-I/O evidence differs")
    if transition.get("migration_alias_ids") != PREDECESSOR_ALIAS_IDS:
        errors.append("predecessor migration alias identities differ")
    if transition.get("verification_ids") != PREDECESSOR_VERIFICATION_IDS:
        errors.append("predecessor verification identities differ")
    if transition.get("readable_representation") != {
        "representation_id": "human_readable_context_routing",
        "canonical_document_id": "COMPONENT-REGISTRY",
        "canonical_path": (
            "framework/project/interfaces/project-console/data/"
            "component-registry.js"
        ),
        "generated_from": "embedded_context_routing",
        "authority_effect": "none",
        "executable": False,
    }:
        errors.append("readable routing representation evidence differs")
    return errors


DETERMINISTIC_SCENARIO_RULES = {
    "packet_material": {
        "ctxr.inv.required_floor_is_minimum",
        "ctxr.inv.additive_union",
        "ctxr.sel.profile_never_excludes_capability",
        "ctxr.sel.complete_dependency_closure",
    },
    "route_cycle": {
        "ctxr.inv.dependency_graph_is_acyclic",
        "ctxr.fail.dependency_cycle",
    },
    "route_floor": {"ctxr.sel.required_floor_order"},
    "selection_profile": {
        "ctxr.sel.primary_profile",
        "ctxr.fail.unknown_or_missing_selection",
    },
    "selection_profile_route": {"ctxr.sel.profile_starting_set"},
    "selection_capability": {
        "ctxr.sel.capability_addition_requires_no_new_profile",
    },
    "packet_pinned": {
        "ctxr.val.integration_pinned_digest_exact",
        "ctxr.fail.pinned_digest_absent_or_stale",
    },
    "registry_before_selection": {"ctxr.val.registry_before_selection"},
    "registry_digest": {"ctxr.val.registry_digest_external"},
    "packet_runtime": {
        "ctxr.val.runtime_digest_at_packet_build",
        "ctxr.fail.runtime_digest_unreadable",
    },
    "section_invalid": {
        "ctxr.sel.profile_documents_and_exact_sections",
        "ctxr.val.exact_section_unique",
        "ctxr.fail.section_identity_invalid",
    },
    "section_budget": {
        "ctxr.fail.section_budget_exceeded",
        "ctxr.budget.section_and_packet_limits_are_independent",
    },
    "packet_budget": {
        "ctxr.fail.packet_budget_exceeded",
        "ctxr.budget.profile_max_is_fail_closed_ceiling",
        "ctxr.budget.no_mandatory_trimming",
    },
    "route_generated": {
        "ctxr.fail.generated_or_excluded_as_authority",
        "ctxr.cur.generated_rebuildables_excluded",
    },
    "route_pinned": {"ctxr.cur.stable_governing_is_pinned"},
    "route_runtime": {"ctxr.cur.mutable_handoff_is_runtime_hashed"},
    "route_records": {"ctxr.cur.records_excluded_except_handoff"},
    "route_checkpoint_drift": {
        "ctxr.cur.checkpoint_update_needs_no_registry_edit",
    },
    "route_ceiling_drift": {
        "ctxr.budget.ceiling_change_does_not_change_membership",
    },
    "packet_manifest": {"ctxr.val.packet_manifest_bound"},
    "review_runtime": {
        "ctxr.cur.runtime_nongoverning_excluded_from_review_boundary",
    },
    "review_select": {"ctxr.review.select_all_active_governing"},
    "review_schedule": {"ctxr.review.periodic_epoch_required"},
    "review_boundary": {
        "ctxr.review.boundary_exact",
        "ctxr.review.invalid_drift_is_integrity_failure",
        "ctxr.review.recorder_requires_exact_current_boundary",
    },
    "review_difference": {
        "ctxr.review.any_valid_boundary_difference_due",
    },
    "review_completion": {"ctxr.review.completion_fields_exact"},
    "review_findings": {
        "ctxr.review.unresolved_findings_carry_forward",
        "ctxr.review.next_epoch_uses_delta_and_carry_forward",
    },
    "stable_identity": {
        "ctxr.inv.stable_document_identity_is_path_independent",
    },
}
DETERMINISTIC_SCENARIO_BY_RULE = {
    rule_id: scenario
    for scenario, rule_ids in DETERMINISTIC_SCENARIO_RULES.items()
    for rule_id in rule_ids
}


def _current_candidate_view() -> dict[str, object]:
    """Return an in-memory candidate view pinned to the current test checkout."""

    candidate = _load_registry()
    route = json.loads(
        subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "show",
                f"{STAGE1_CANONICAL_REVISION}:framework/archive/authorities/"
                "context-routes.json",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    for document in route["documents"].values():
        if document.get("hash_policy", "pinned") == "pinned":
            source = ROOT / document["path"]
            if not source.exists():
                if document["path"] == "framework/project/automation/registry.md":
                    source = (
                        ROOT / "framework" / "archive" / "authorities"
                        / "AGENT_BOT_REGISTRY.md"
                    )
                    document["path"] = source.relative_to(ROOT).as_posix()
                for specification in (
                    registry_tool.ROUTING_PREDECESSOR_PATHS.values()
                ):
                    if (
                        document["path"]
                        == specification["historical_path"]
                    ):
                        source = ROOT / specification["archived_path"]
                        document["path"] = specification["archived_path"]
                        break
            document["sha256"] = hashlib.sha256(
                source.read_bytes()
            ).hexdigest()
    candidate["context_routing"]["documents"] = copy.deepcopy(
        route["documents"]
    )
    return registry_tool.validated_component_registry_routing_view(
        candidate,
        candidate_source_route=route,
    )


def _candidate_packet(
    *,
    view: dict[str, object] | None = None,
    profile: str = "comprehensive_review",
    capabilities: tuple[str, ...] = (),
    **options: object,
) -> dict[str, object]:
    selected_view = view or _current_candidate_view()
    return registry_tool.build_context_packet_from_view(
        selected_view,
        profile,
        assurance_mode=selected_view["validation_mode"],
        root=ROOT,
        capabilities=capabilities,
        **options,
    )


def _candidate_review_selection(
    view: dict[str, object],
) -> dict[str, object]:
    selection = registry_tool.routed_configuration_documents_from_view(
        view,
        profile_id="comprehensive_review",
    )
    selection["selection_kind"] = "executable_packet"
    selection["executable"] = True
    selection["authoritative"] = False
    return selection


def _require_instruction_packet(
    packet: dict[str, object],
    row: dict[str, object],
) -> dict[str, object]:
    """Verify one exact governing instruction before a simulated action."""

    binding = row["packet_inclusion"]
    document_id = binding["document_id"]
    module = next(
        (
            item
            for item in packet.get("modules", [])
            if item.get("document") == document_id
        ),
        None,
    )
    try:
        if not isinstance(module, dict):
            raise ValueError("required governing instruction is absent")
        relative, heading_name = row["implementation_anchor"].split("#", 1)
        source = ROOT / relative
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if module.get("sha256") != digest:
            raise ValueError("required governing instruction pin is stale")
        heading = next(
            (
                line
                for line in source.read_text(encoding="utf-8").splitlines()
                if line.startswith("#")
                and line.lstrip("#").strip() == heading_name
            ),
            None,
        )
        if heading is None:
            raise ValueError("required governing instruction heading is absent")
        expected_content, _start, _end = extract_exact_heading(
            source.read_text(encoding="utf-8"),
            heading,
        )
        if expected_content not in str(module.get("content") or ""):
            raise ValueError("required governing instruction content is absent")
        reasons = module.get("inclusion_reasons")
        acceptable_reason = (
            isinstance(reasons, list)
            and (
                (
                    binding["kind"] == "required_module"
                    and "required floor" in reasons
                )
                or (
                    binding["kind"] == "capability_dependency_closure"
                    and (
                        f"requested capability {binding['selector']}" in reasons
                        or any(
                            reason.startswith("dependency of ")
                            for reason in reasons
                        )
                    )
                )
            )
        )
        if not acceptable_reason:
            raise ValueError(
                "required governing instruction inclusion reason is absent"
            )
    except ValueError as exc:
        raise registry_tool.RoutingRuleFailure(
            failure_code=row["registered_failure_code"],
            phase=row["registered_phase"],
            rule_ids=(row["rule_id"],),
            message=f"Governing instruction precondition is invalid: {exc}",
        ) from exc
    return module


class HistoricalContextRoutingRuleClosureTests:
    def setUp(self) -> None:
        self.matrix = _load_matrix()
        self.source = SOURCE_PATH.read_bytes()
        self.registry = _load_registry()
        self.schema = _load_schema()

    def deterministic_failure_evidence(
        self,
        rule_id: str,
    ) -> dict[str, object]:
        """Mutate one real consumer condition and return its typed evidence."""

        scenario = DETERMINISTIC_SCENARIO_BY_RULE[rule_id]
        view = _current_candidate_view()
        route = copy.deepcopy(view["route"])
        try:
            if scenario == "packet_material":
                packet = _candidate_packet(view=view)
                omitted = packet["routing_manifest"][
                    "resolved_document_order"
                ][-1]
                packet["modules"] = [
                    item
                    for item in packet["modules"]
                    if item["document"] != omitted
                ]
                for field in (
                    "resolved_document_revisions",
                    "resolved_document_digests",
                    "dependency_closure",
                    "inclusion_reasons",
                ):
                    packet["routing_manifest"][field].pop(omitted)
                packet["routing_manifest"]["resolved_document_order"].remove(
                    omitted
                )
                registry_tool.validate_context_packet_binding(
                    packet,
                    view=view,
                    profile_id="comprehensive_review",
                )
            elif scenario == "route_cycle":
                route["documents"]["framework_kernel"]["requires"] = [
                    "framework_kernel"
                ]
                registry_tool.validate_route_source(route)
            elif scenario == "route_floor":
                route["required_modules"] = list(
                    reversed(route["required_modules"])
                )
                registry_tool.validate_route_source(route)
            elif scenario == "selection_profile":
                registry_tool.routed_documents_from_view(
                    view,
                    profile_id="",
                )
            elif scenario == "selection_profile_route":
                registry_tool.routed_configuration_documents_from_view(
                    view,
                    profile_id="",
                )
            elif scenario == "selection_capability":
                registry_tool.routed_capability_preview_from_view(
                    view,
                    capability_ids=("unregistered_capability",),
                )
            elif scenario == "packet_pinned":
                view["route"]["documents"]["framework_kernel"][
                    "sha256"
                ] = "0" * 64
                _candidate_packet(view=view)
            elif scenario == "registry_before_selection":
                view.pop("_validated_registry")
                registry_tool.routed_configuration_documents_from_view(
                    view,
                    profile_id="comprehensive_review",
                )
            elif scenario == "registry_digest":
                view["_validated_registry"] = copy.deepcopy(
                    view["_validated_registry"]
                )
                view["_validated_registry"]["unexpected_fixture_leaf"] = True
                registry_tool.routed_configuration_documents_from_view(
                    view,
                    profile_id="comprehensive_review",
                )
            elif scenario == "packet_runtime":
                checkpoint_id = _route_checkpoint_id(view["route"])
                view["route"]["documents"][checkpoint_id]["path"] = (
                    "framework/runtime-missing.md"
                )
                _candidate_packet(view=view)
            elif scenario == "section_invalid":
                view["route"]["profiles"]["integrity_reconciliation"][
                    "sections"
                ][0]["heading"] = "## Missing Fixture Heading"
                _candidate_packet(
                    view=view,
                    profile="integrity_reconciliation",
                )
            elif scenario == "section_budget":
                view["route"]["profiles"]["integrity_reconciliation"][
                    "sections"
                ][0]["max_bytes"] = 1
                _candidate_packet(
                    view=view,
                    profile="integrity_reconciliation",
                )
            elif scenario == "packet_budget":
                _candidate_packet(view=view, max_total_bytes=1)
            elif scenario == "route_generated":
                route["documents"]["project_interface"]["path"] = (
                    "framework/project/interfaces/project-console/data/fixture.md"
                )
                registry_tool.validate_route_source(route)
            elif scenario == "route_pinned":
                route["documents"]["framework_kernel"]["sha256"] = None
                registry_tool.validate_route_source(route)
            elif scenario == "route_runtime":
                checkpoint_id = _route_checkpoint_id(route)
                route["documents"][checkpoint_id].update(
                    {
                        "hash_policy": "pinned",
                        "sha256": "0" * 64,
                    }
                )
                registry_tool.validate_route_source(route)
            elif scenario == "route_records":
                route["documents"]["project_interface"]["path"] = (
                    "framework/records/fixture.md"
                )
                registry_tool.validate_route_source(route)
            elif scenario == "route_checkpoint_drift":
                altered = copy.deepcopy(route)
                altered["required_modules"] = list(
                    reversed(altered["required_modules"])
                )
                registry_tool._candidate_route_hash_drift(route, altered)
            elif scenario == "route_ceiling_drift":
                altered = copy.deepcopy(route)
                altered["profiles"]["comprehensive_review"][
                    "max_bytes"
                ] += 1
                registry_tool._candidate_route_hash_drift(route, altered)
            elif scenario == "packet_manifest":
                packet = _candidate_packet(view=view)
                packet["routing_manifest"].pop("dynamic_expansions")
                registry_tool.validate_context_packet_binding(
                    packet,
                    view=view,
                    profile_id="comprehensive_review",
                )
            elif scenario in {
                "review_runtime",
                "review_select",
                "review_boundary",
            }:
                selection = _candidate_review_selection(view)
                if scenario == "review_runtime":
                    current = next(
                        item
                        for item in selection["modules"]
                        if item["id"] == _route_checkpoint_id(view["route"])
                    )
                    current["hash_policy"] = "pinned"
                    current["sha256"] = "0" * 64
                elif scenario == "review_select":
                    view["route"]["profiles"]["comprehensive_review"][
                        "include_all_governing"
                    ] = False
                else:
                    selection["modules"] = selection["modules"][:-1]
                run_coordinator.review_epoch_boundary_status(
                    None,
                    view,
                    selection,
                    allow_candidate_validation=True,
                )
            elif scenario == "review_schedule":
                run_coordinator.review_epoch(
                    {},
                    {},
                    {},
                    datetime.now(timezone.utc),
                )
            elif scenario == "review_difference":
                result = run_coordinator.review_epoch_boundary_status(
                    None,
                    view,
                    _candidate_review_selection(view),
                    allow_candidate_validation=True,
                )
                return result["routing_failure"]
            elif scenario == "review_completion":
                record_review_epoch.validate(
                    {},
                    routing_view=view,
                    routing_selection=_candidate_review_selection(view),
                    context_packet={},
                    root=ROOT,
                    allow_candidate_validation=True,
                )
            elif scenario == "review_findings":
                record_review_epoch.validate_finding_continuity(
                    {
                        "unresolved_findings": [
                            {"id": "fixture-unresolved"}
                        ]
                    },
                    {
                        "resolved_findings": [],
                        "unresolved_findings": [],
                    },
                )
            elif scenario == "stable_identity":
                candidate = copy.deepcopy(self.registry)
                alias = next(
                    iter(candidate["aliases_and_migrations"]["entries"].values())
                )
                alias["target_path"] = alias["source_path"]
                registry_tool._validate_aliases(candidate)
            else:  # pragma: no cover - the inventory assertion closes this.
                self.fail(f"unregistered deterministic scenario: {scenario}")
        except registry_tool.RoutingRuleFailure as exc:
            return exc.safe_evidence()
        self.fail(f"deterministic scenario did not block: {scenario}")

    def test_all_64_assurance_fixture_ids_execute_real_boundaries(self):
        rows = {
            row["rule_id"]: row
            for row in self.matrix["rule_assurance"]["rows"]
        }
        self.assertEqual(
            set(DETERMINISTIC_SCENARIO_BY_RULE),
            RULES_BY_ASSURANCE_MODE["deterministic_enforcement"],
        )
        routines = {}
        for rule_id, row in rows.items():
            fixture_id = row["negative_fixture_id"]
            if row["assurance_mode"] == "deterministic_enforcement":
                routines[fixture_id] = (
                    lambda current=rule_id: self.deterministic_failure_evidence(
                        current
                    )
                )
            elif (
                row["assurance_mode"]
                == "governing_instruction_precondition"
            ):
                routines[fixture_id] = (
                    lambda current=row: self._instruction_negative_evidence(
                        current
                    )
                )
            else:
                routines[fixture_id] = self._candidate_only_negative_evidence
        self.assertEqual(
            set(routines),
            {
                row["negative_fixture_id"]
                for row in self.matrix["rule_assurance"]["rows"]
            },
        )
        for rule_id, row in rows.items():
            with self.subTest(rule_id=rule_id):
                evidence = routines[row["negative_fixture_id"]]()
                self.assertEqual(
                    evidence["failure_code"],
                    row["registered_failure_code"],
                )
                self.assertEqual(
                    evidence["phase"],
                    row["registered_phase"],
                )
                self.assertIn(rule_id, evidence["rule_ids"])
                self.assertTrue(evidence["message"])

    def _instruction_negative_evidence(
        self,
        row: dict[str, object],
    ) -> dict[str, object]:
        binding = row["packet_inclusion"]
        capabilities = (
            (binding["selector"],)
            if binding["kind"] == "capability_dependency_closure"
            else ()
        )
        packet = _candidate_packet(capabilities=capabilities)
        _require_instruction_packet(packet, row)
        packet["modules"] = [
            module
            for module in packet["modules"]
            if module["document"] != binding["document_id"]
        ]
        with self.assertRaises(
            registry_tool.RoutingRuleFailure
        ) as blocked:
            _require_instruction_packet(packet, row)
        return blocked.exception.safe_evidence()

    def _candidate_only_negative_evidence(self) -> dict[str, object]:
        candidate = copy.deepcopy(self.registry)
        source = copy.deepcopy(candidate["context_routing"])
        source = {
            key: source[key]
            for key in (
                "schema_version",
                "generated_path_exclusions",
                "required_modules",
                "documents",
                "capabilities",
                "profiles",
            )
        }
        source["profiles"]["comprehensive_review"]["max_bytes"] += 1
        report = registry_tool.parity_report(candidate, source)
        self.assertFalse(report["valid"])
        view = _current_candidate_view()
        with self.assertRaises(
            registry_tool.RoutingRuleFailure
        ):
            registry_tool.routed_documents_from_view(
                view,
                profile_id="comprehensive_review",
            )
        return registry_tool.RoutingRuleFailure(
            failure_code="CTXR_UNRESOLVED_MATERIAL_GOVERNING_GAP",
            phase="route_definition",
            rule_ids=("ctxr.inv.router_preserves_source_authority",),
            message=(
                "Candidate predecessor parity differs and cannot authorize "
                "execution"
            ),
        ).safe_evidence()

    def test_each_instruction_group_blocks_missing_and_stale_content(self):
        rows = [
            row
            for row in self.matrix["rule_assurance"]["rows"]
            if row["assurance_mode"]
            == "governing_instruction_precondition"
        ]
        groups = {
            (
                row["packet_inclusion"]["kind"],
                row["packet_inclusion"]["selector"],
                row["packet_inclusion"]["document_id"],
            )
            for row in rows
        }
        self.assertEqual(len(groups), 5)
        for kind, selector, document_id in groups:
            row = next(
                item
                for item in rows
                if item["packet_inclusion"]
                == {
                    "kind": kind,
                    "selector": selector,
                    "document_id": document_id,
                }
            )
            capabilities = (
                (selector,)
                if kind == "capability_dependency_closure"
                else ()
            )
            packet = _candidate_packet(capabilities=capabilities)
            module = _require_instruction_packet(packet, row)
            module["sha256"] = "0" * 64
            with self.assertRaises(registry_tool.RoutingRuleFailure):
                _require_instruction_packet(packet, row)

    def test_pinned_source_has_complete_one_to_one_rule_closure(self):
        self.assertEqual(
            _closure_errors(self.matrix, self.source, self.registry),
            [],
        )

    def test_semantic_enforcement_closure_is_complete(self):
        self.assertEqual(
            _enforcement_closure_errors(self.matrix, self.registry),
            [],
        )

    def test_governing_instruction_assurance_is_pinned_and_packet_included(
        self,
    ):
        instruction_rows = [
            row
            for row in self.matrix["rule_assurance"]["rows"]
            if row["assurance_mode"]
            == "governing_instruction_precondition"
        ]
        self.assertEqual(
            {row["rule_id"] for row in instruction_rows},
            RULES_BY_ASSURANCE_MODE[
                "governing_instruction_precondition"
            ],
        )
        self.assertTrue(
            all(row["packet_inclusion"] for row in instruction_rows)
        )
        self.assertEqual(
            _enforcement_closure_errors(self.matrix, self.registry),
            [],
        )

        stale = copy.deepcopy(self.registry)
        stale["context_routing"]["documents"]["agent_rules_kernel"][
            "sha256"
        ] = "0" * 64
        self.assertTrue(
            any(
                "governing instruction pin is stale" in error
                for error in _enforcement_closure_errors(
                    self.matrix,
                    stale,
                )
            )
        )

    def test_assurance_mode_anchor_and_fixture_drift_fail_closed(self):
        wrong_mode = copy.deepcopy(self.matrix)
        wrong_mode["rule_assurance"]["rows"][0][
            "assurance_mode"
        ] = "deterministic_enforcement"
        self.assertTrue(
            any(
                "assurance mode differs" in error
                for error in _enforcement_closure_errors(
                    wrong_mode,
                    self.registry,
                )
            )
        )

        fake_anchor = copy.deepcopy(self.matrix)
        fake_anchor["rule_assurance"]["rows"][1][
            "implementation_anchor"
        ] = "scripts.component_registry:invented_consumer"
        self.assertTrue(
            any(
                "implementation anchor is not real" in error
                for error in _enforcement_closure_errors(
                    fake_anchor,
                    self.registry,
                )
            )
        )

        duplicate_fixture = copy.deepcopy(self.matrix)
        duplicate_fixture["rule_assurance"]["rows"][1][
            "negative_fixture_id"
        ] = duplicate_fixture["rule_assurance"]["rows"][0][
            "negative_fixture_id"
        ]
        errors = _enforcement_closure_errors(
            duplicate_fixture,
            self.registry,
        )
        self.assertTrue(
            any("negative fixture identity differs" in error for error in errors)
        )
        self.assertIn(
            "negative assurance fixture IDs are missing or duplicated",
            errors,
        )

    def test_candidate_to_active_predecessor_transition_is_complete(self):
        self.assertEqual(
            _predecessor_transition_errors(self.matrix, self.registry),
            [],
        )

        altered = copy.deepcopy(self.matrix)
        altered["candidate_to_active_predecessor_transition"][
            "active_counts"
        ]["documents"] += 1
        self.assertIn(
            "active predecessor-transition counts differ",
            _predecessor_transition_errors(altered, self.registry),
        )

        altered = copy.deepcopy(self.matrix)
        altered["candidate_to_active_predecessor_transition"][
            "active_no_current_io"
        ]["forbidden_current_authority_paths"].pop()
        self.assertIn(
            "active no-predecessor-I/O evidence differs",
            _predecessor_transition_errors(altered, self.registry),
        )

    def test_missing_atomic_clause_fails_closed(self):
        altered = copy.deepcopy(self.matrix)
        altered["clauses"].pop()
        self.assertIn(
            "atomic clause inventory differs from approved rules",
            _closure_errors(altered, self.source, self.registry),
        )

    def test_duplicate_atomic_clause_fails_closed(self):
        altered = copy.deepcopy(self.matrix)
        altered["clauses"].append(copy.deepcopy(altered["clauses"][0]))
        errors = _closure_errors(altered, self.source, self.registry)
        self.assertTrue(
            any(error.startswith("duplicate clause keys:") for error in errors)
        )
        self.assertTrue(
            any(error.startswith("duplicate rule IDs:") for error in errors)
        )

    def test_rule_without_source_or_design_provenance_fails_closed(self):
        altered = copy.deepcopy(self.matrix)
        altered["clauses"][0]["source_line_ranges"] = []
        altered["design_authorities"]["supplemental_routing_catalog"][
            "closes_decision_ids"
        ] = ["CR-045"]
        errors = _closure_errors(altered, self.source, self.registry)
        self.assertTrue(any("source provenance is absent" in error for error in errors))
        self.assertIn(
            "CR-045/046 supplemental design provenance is incomplete",
            errors,
        )

    def test_base_and_supplemental_design_authorities_are_independent(self):
        missing_base = copy.deepcopy(self.matrix)
        missing_base["design_authorities"].pop("base_blueprint")
        self.assertIn(
            "base blueprint design authority is missing or mismatched",
            _closure_errors(missing_base, self.source, self.registry),
        )

        conflated = copy.deepcopy(self.matrix)
        conflated["design_authorities"]["base_blueprint"] = copy.deepcopy(
            conflated["design_authorities"]["supplemental_routing_catalog"]
        )
        self.assertIn(
            "base blueprint design authority is missing or mismatched",
            _closure_errors(conflated, self.source, self.registry),
        )

        missing_supplemental = copy.deepcopy(self.matrix)
        missing_supplemental["design_authorities"].pop(
            "supplemental_routing_catalog"
        )
        self.assertIn(
            "supplemental routing-catalog design authority is missing or mismatched",
            _closure_errors(
                missing_supplemental,
                self.source,
                self.registry,
            ),
        )

    def test_matrix_and_registered_catalog_provenance_must_match(self):
        wrong_heading = copy.deepcopy(self.registry)
        wrong_heading["context_routing"]["selection"][
            "ctxr.sel.required_floor_order"
        ]["source_provenance"]["source_heading"] = "Additive Routing"
        self.assertIn(
            "ctxr.sel.required_floor_order: "
            "matrix and registered source heading differ",
            _closure_errors(self.matrix, self.source, wrong_heading),
        )

        wrong_digest = copy.deepcopy(self.registry)
        wrong_digest["context_routing"]["selection"][
            "ctxr.sel.required_floor_order"
        ]["source_provenance"]["source_sha256"] = "0" * 64
        self.assertIn(
            "ctxr.sel.required_floor_order: "
            "matrix and registered source digest differ",
            _closure_errors(self.matrix, self.source, wrong_digest),
        )

        wrong_category = copy.deepcopy(self.registry)
        moved = wrong_category["context_routing"]["selection"].pop(
            "ctxr.sel.required_floor_order"
        )
        wrong_category["context_routing"]["invariants"][
            "ctxr.sel.required_floor_order"
        ] = moved
        self.assertIn(
            "ctxr.sel.required_floor_order: registered catalog entry is absent",
            _closure_errors(self.matrix, self.source, wrong_category),
        )

    def test_schema_accepts_only_coherent_candidate_and_active_states(self):
        approval_states = {
            "pending": {
                "state": "pending",
                "reason": "Schema-only pending-state fixture.",
            },
            "known": _known_approval_fixture(),
        }
        coherent = {
            ("candidate", "pending", "candidate_import", False),
            ("active", "known", "active", True),
        }
        for status in ("candidate", "active"):
            for approval_state, approval in approval_states.items():
                for activation_state in ("candidate_import", "active"):
                    for authoritative in (False, True):
                        fixture = (
                            _active_schema_fixture(self.registry)
                            if status == "active"
                            else copy.deepcopy(self.registry)
                        )
                        fixture["status"] = status
                        fixture["approval"] = copy.deepcopy(approval)
                        fixture["context_routing"][
                            "activation_state"
                        ] = activation_state
                        fixture["context_routing"][
                            "authoritative"
                        ] = authoritative
                        key = (
                            status,
                            approval_state,
                            activation_state,
                            authoritative,
                        )
                        with self.subTest(state=key):
                            if key in coherent:
                                registry_tool._validate_against_schema(
                                    fixture,
                                    self.schema,
                                    self.schema,
                                )
                            else:
                                with self.assertRaises(
                                    registry_tool.RegistryError
                                ):
                                    registry_tool._validate_against_schema(
                                        fixture,
                                        self.schema,
                                        self.schema,
                                    )

    def test_orphaned_source_block_fails_closed(self):
        altered = copy.deepcopy(self.matrix)
        normative = next(
            block
            for block in altered["source_blocks"]
            if block["classification"] == "normative"
        )
        normative["clause_keys"] = []
        self.assertTrue(
            any(
                error.endswith("normative block orphaned")
                for error in _closure_errors(
                    altered,
                    self.source,
                    self.registry,
                )
            )
        )


class ContextRoutingV4RuleClosureTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def rule_ids(self):
        return {
            rule_id
            for group in self.registry["routing"]["rules"].values()
            for rule_id in group
        }

    def test_all_64_rule_identities_are_map_keys_and_match_runtime_catalog(self):
        ids = self.rule_ids()
        expected = {
            rule_id
            for namespace in registry_tool.ROUTING_RULE_MAPS
            for rule_id in registry_tool.ROUTING_RULE_IDS[namespace]
        }
        self.assertEqual(len(ids), 64)
        self.assertEqual(ids, expected)
        self.assertEqual(
            set(registry_tool.ROUTING_RULE_SEMANTIC_IMPLEMENTATION_PLAN), ids
        )

    def test_compact_rules_derive_predicate_version_status_and_verification(self):
        for namespace, rules in self.registry["routing"]["rules"].items():
            for rule_id, compact in rules.items():
                self.assertTrue({
                    "rule_id", "predicate_type", "rule_version", "status",
                    "source_provenance", "verification_ids",
                }.isdisjoint(compact))
                derived = {
                    "predicate_type": rule_id,
                    "parameters": copy.deepcopy(compact.get("parameters", {})),
                }
                if "failure_code" in compact:
                    derived["failure_code"] = compact["failure_code"]
                validated = registry_tool.validate_routing_rule_definition(rule_id, derived)
                self.assertEqual(validated["rule_id"], rule_id)
                self.assertEqual(validated["predicate_type"], rule_id)
                self.assertEqual(namespace, next(
                    name for name, values in registry_tool.ROUTING_RULE_IDS.items()
                    if rule_id in values
                ))

    def test_rule_definition_rejects_wrong_derived_identity_and_parameters(self):
        rule_id = "ctxr.inv.additive_union"
        compact = self.registry["routing"]["rules"]["invariants"][rule_id]
        valid = {
            "predicate_type": rule_id,
            "parameters": copy.deepcopy(compact["parameters"]),
        }
        wrong_identity = copy.deepcopy(valid)
        wrong_identity["predicate_type"] = "ctxr.inv.required_floor_is_minimum"
        wrong_parameters = copy.deepcopy(valid)
        wrong_parameters["parameters"] = {}
        for altered in (wrong_identity, wrong_parameters):
            with self.assertRaises(registry_tool.RegistryError):
                registry_tool.validate_routing_rule_definition(rule_id, altered)

    def test_v4_registry_rejects_reintroduced_rule_metadata(self):
        altered = copy.deepcopy(self.registry)
        altered["routing"]["rules"]["invariants"][
            "ctxr.inv.router_preserves_source_authority"
        ]["rule_version"] = 1
        with self.assertRaisesRegex(registry_tool.RegistryError, "repeats derived data"):
            registry_tool.validate_v4_registry(
                altered, root=ROOT, compare_codeowners=False
            )


if __name__ == "__main__":
    unittest.main()
