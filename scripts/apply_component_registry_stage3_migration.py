#!/usr/bin/env python3
"""Apply the approved deterministic Component Registry Stage 3 data migration."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "framework/component-registry.json"
SCHEMA_PATH = ROOT / "framework/component-registry.schema.json"
BASE_REVISION = "fad1ea5bf69a0ef17d48879ad78a1fa27f2e694b"
DESIGN_ID = "COMPONENT-REGISTRY-2026-003-STAGE3-COORDINATED-RECONCILIATION"
DESIGN_REVISION = "sha256:7e8a524514689636acb81109c35194d0b314697dddcd723f2529f5e9b5cab4a1"
EXTERNAL_EVIDENCE_ID = "f47635a7960d275c48526ea8eec40350a47a5cdf8e2376bc4e9e55e20f7f7759"
CONTRACT_SHA256 = "fe037ef88698f15fab904605a56c86a79dc0eea89cf46c14c47ab199ab50aa52"
PROVENANCE_EVENT_ID = "stage3_coordinated_reconciliation"

PATH_MIGRATIONS = {
    "framework/standards/automation/component-registry.schema.json": "framework/component-registry.schema.json",
    "framework/project/automation/project-wide-reconciliation.schema.json": "framework/project/automation/schemas/project-wide-reconciliation.schema.json",
    "framework/project/automation/transaction-lifecycle.schema.json": "framework/project/automation/schemas/transaction-lifecycle.schema.json",
    "framework/project/automation/transaction-recovery-package.schema.json": "framework/project/automation/schemas/transaction-recovery-package.schema.json",
    ".github/source-domain-event.schema.json": "framework/project/automation/schemas/source-domain-event.schema.json",
    ".github/case-monitor-bot.json": "framework/project/automation/configuration/bots/case-monitor-bot.json",
    ".github/presidential-directives-bot.json": "framework/project/automation/configuration/bots/presidential-directives-bot.json",
    ".github/run-coordinator-bot.json": "framework/project/automation/configuration/bots/run-coordinator-bot.json",
    ".github/source-checker-bot.json": "framework/project/automation/configuration/bots/source-checker-bot.json",
    ".github/progress-history-seed.json": "framework/project/interfaces/project-console/configuration/progress-history-seed.json",
    "framework/project/interfaces/project-console.md": "framework/project/interfaces/project-console/specification.md",
    "framework/project/interfaces/project-console-classifications.json": "framework/project/interfaces/project-console/configuration/classifications.json",
    "framework/project/interfaces/project-console-progress.json": "framework/project/interfaces/project-console/configuration/progress.json",
    "framework/project/interfaces/project-console-progress.md": "framework/project/interfaces/project-console/configuration/progress.md",
}

ROOT_MAINTAINED_FILES = [
    ".gitattributes", ".gitignore", ".rgignore", "ABOUT.md", "AGENTS.md",
    "CITATION.cff", "CONTRIBUTING.md", "LICENSE.md", "PRINT_READERS_GUIDE.md",
    "README.md", "SUBJECT_INDEX.md", "SUPPORT.md", "UNDER_REVIEW.md", "mkdocs.yml",
]


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def tracked_paths() -> list[str]:
    output = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout
    return sorted({line for line in output.splitlines() if line})


def replace_current_paths(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: replace_current_paths(child) for key, child in value.items()}
    if isinstance(value, list):
        return [replace_current_paths(child) for child in value]
    if isinstance(value, str):
        if value in PATH_MIGRATIONS:
            return PATH_MIGRATIONS[value]
        old_prefix = "framework/project/interfaces/visual-baselines/"
        if value.startswith(old_prefix):
            return "framework/project/interfaces/project-console/visual-baselines/" + value[len(old_prefix):]
    return value


def term(term_id: str, label: str, definition: str) -> dict[str, str]:
    return {"term_id": term_id, "label": label, "definition": definition}


def add_term(registry: dict[str, Any], record: dict[str, str]) -> None:
    terms = registry["terminology"]
    term_id = record["term_id"]
    if term_id not in terms["entries"]:
        terms["order"].append(term_id)
    terms["entries"][term_id] = record


def refresh_terminology_digest(registry: dict[str, Any]) -> None:
    terms = registry["terminology"]
    records = [terms["entries"][term_id] for term_id in terms["order"]]
    encoded = json.dumps(
        records, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ) + "\n"
    terms["record_set_sha256"] = hashlib.sha256(encoded.encode()).hexdigest()


def normalize_terminology(registry: dict[str, Any]) -> None:
    clean_labels = {
        "active_operational_status": "Active",
        "paused_operational_status": "Paused",
        "inactive_operational_status": "Inactive",
        "current_applicability_status": "Current",
        "draft_lifecycle_state": "Draft",
        "proposed_lifecycle_state": "Proposed",
        "adopted_lifecycle_state": "Adopted",
        "retired_lifecycle_state": "Retired",
        "supersession_relationship": "Supersession",
        "predecessor_relationship_role": "Predecessor",
        "successor_relationship_role": "Successor",
        "alias_identifier_relationship": "Alias",
    }
    for term_id, label in clean_labels.items():
        registry["terminology"]["entries"][term_id]["label"] = label
    archived = registry["terminology"]["entries"].pop("archived_retention_outcome")
    archived["term_id"] = "archived_retention_posture"
    archived["label"] = "Archived"
    archived["definition"] = (
        "Retained for historical, evidentiary, or provenance purposes rather than "
        "current operational use. Archived is a retention posture, not a lifecycle state."
    )
    order = registry["terminology"]["order"]
    order[order.index("archived_retention_outcome")] = "archived_retention_posture"
    registry["terminology"]["entries"]["archived_retention_posture"] = archived

    approved_terms = [
        term("allow_children", "Allow children", "A directory-scope control indicating that ordinary descendant paths may inherit the scope's placement governance without individual registration, subject to more-specific scopes and explicit treatments."),
        term("ordinary_scoped_child", "Ordinary scoped child", "A persistent artifact whose placement is governed by a recursive directory scope and which is not independently registered, assigned as a supporting artifact, or covered by a component-registration exemption."),
        term("component_registration_exemption", "Component registration exemption", "A governed categorical rule that relieves covered artifacts from individual component registration while leaving placement, producer, information handling, retention, disposition, and coverage controls in force."),
        term("unresolved", "Unresolved", "A coverage result for an in-scope path with no valid treatment or with conflicting or multiple treatments, requiring human review before validation may pass."),
        term("revision_mode", "Revision mode", "A governed property specifying how revisions to a retained component or artifact may be made."),
        term("maintained_revision_mode", "Maintained", "Ordinary governed revisions are permitted."),
        term("append_only_revision_mode", "Append-only", "New entries are permitted while existing entries remain unchanged."),
        term("immutable_revision_mode", "Immutable", "The item is not altered; a correction requires a new or superseding component or record."),
        term("replaceable_revision_mode", "Replaceable", "The item may be regenerated or replaced from its governing source."),
        term("design_contract", "Design contract", "An exact owner-submitted implementation authority that permits a defined implementing process to make only the changes within its fixed scope, invariants, stop conditions, and mutation authorities."),
        term("owner_direct", "Owner direct", "An exact authenticated instruction directly from Benjamin authorizing an identified action within a fixed scope. This evidence mode remains unavailable to production validation until a separately approved trusted resolver exists."),
        term("execution_controls", "Execution controls", "Governed restrictions specifying who or what may initiate an executable component and for which purposes."),
        term("automated_initiation", "Automated initiation", "Execution initiated by an authorized coordinator within a governed chain and only when its defined due condition is satisfied."),
        term("manual_initiation", "Manual initiation", "Execution initiated only after an explicit current human instruction."),
        term("llm_assisted", "LLM-assisted", "A manual execution interface in which a language-model-assisted process carries out an explicit current human instruction without originating execution authority."),
        term("direct_script", "Direct script", "A manual execution interface in which a human directly invokes the governed script under an explicit current instruction."),
        term("explicit_current_human_instruction", "Explicit current human instruction", "A present, unambiguous human instruction authorizing the specific execution; an earlier or unrelated approval is insufficient."),
        term("due_under_governed_cadence", "Due under governed cadence", "The executable stage is due under its separately governed runtime cadence and coordinator decision."),
    ]
    for record in approved_terms:
        add_term(registry, record)
    refresh_terminology_digest(registry)


def normalize_enums(registry: dict[str, Any]) -> None:
    enums = registry["implementation_enums"]
    enums["owner_decision"] = {
        "decision": "approved_terms_bind_new_stage3_values_legacy_values_remain_explicitly_unbound",
        "terminology_record_count": len(registry["terminology"]["entries"]),
        "terminology_record_set_sha256": registry["terminology"]["record_set_sha256"],
        "deferred_audit": "component_registry_110_value_operative_use_audit",
    }
    enums["revision_modes"] = {
        "maintained": {"term_id": "maintained_revision_mode"},
        "append_only": {"term_id": "append_only_revision_mode"},
        "immutable": {"term_id": "immutable_revision_mode"},
        "replaceable": {"term_id": "replaceable_revision_mode"},
    }
    enums.pop("change_modes", None)
    enums["coverage_treatments"] = {
        "component": {"term_id": "component"},
        "supporting_artifact": {"term_id": "artifact"},
        "registration_exemption": {"term_id": "component_registration_exemption"},
        "ordinary_scoped_child": {"term_id": "ordinary_scoped_child"},
        "unresolved": {"term_id": "unresolved"},
    }
    enums["registry_authorization_modes"] = {
        "design_contract": {"term_id": "design_contract"},
        "owner_direct": {"term_id": "owner_direct"},
    }
    enums["execution_initiation_modes"] = {
        "automated": {"term_id": "automated_initiation"},
        "manual": {"term_id": "manual_initiation"},
    }
    enums["execution_interfaces"] = {
        "llm_assisted": {"term_id": "llm_assisted"},
        "direct_script": {"term_id": "direct_script"},
    }
    enums["controlled_fields"] = {
        "allow_children": {"term_id": "allow_children"},
        "revision_mode": {"term_id": "revision_mode"},
        "execution_controls": {"term_id": "execution_controls"},
    }
    enums["disclosure_rules"].pop("public_by_design", None)


def normalize_scope(scope: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "scope_id": scope["scope_id"],
        "display_name": scope["display_name"],
        "path_pattern": scope["path_pattern"],
        "match_kind": scope["match_kind"],
        "specificity_rank": scope["specificity_rank"],
        "parameter_bindings": scope.get("parameter_bindings", {}),
        "ancestor_scope_ids": scope.get("ancestor_scope_ids", []),
        "purpose": scope.get("purpose") or f"Canonical repository home for {scope['display_name'].lower()}.",
        "placement_question": scope["placement_question"],
        "include_when": scope["include_when"],
        "exclude_when": scope["exclude_when"],
        "primary_authority": scope.get("primary_authority", "COMPONENT-REGISTRY"),
        "ownership": scope.get("ownership", "@Thorncrag"),
        "review_policy": scope.get("review_policy", "human_review_on_unexplained_item"),
        "allow_children": scope["scope_id"] != "repository_root" and scope["match_kind"] in {"prefix", "parameterized_prefix"},
        "fallback": "human_review",
        "repository_controls": scope["repository_controls"],
    }
    if "authorized_creators" in scope:
        result["authorized_creators"] = scope["authorized_creators"]
    if "child_artifact_policy" in scope:
        result["child_artifact_policy"] = scope["child_artifact_policy"]
    else:
        result["child_artifact_policy"] = "Ordinary children inherit this scope only when allow_children is true."
    posture = scope.get("lifecycle_posture")
    if posture in {"append_only", "immutable", "replaceable"}:
        result["revision_mode"] = posture
    retention_bases: list[str] = []
    if posture == "archived":
        retention_bases.append("historical_provenance")
    if posture == "replaceable":
        retention_bases.append("regeneration_support")
    if retention_bases:
        result["retention"] = {"bases": retention_bases}
    disclosure = scope.get("disclosure_boundary")
    if disclosure in {"public_by_design", "public_safe_only"}:
        result["information_handling"] = {
            "information_classification": "public",
            "disclosure_boundary": "repository_public",
        }
    return result


def normalize_scopes(registry: dict[str, Any]) -> None:
    scopes = registry["directory_scopes"]["entries"]
    for obsolete in ("root_pyproject_configuration", "root_package_manifest", "root_package_lock"):
        scopes.pop(obsolete, None)
    scopes["research_interbranch"]["path_pattern"] = "research/interbranch-review/"
    scopes["website_partials"]["path_pattern"] = "website/overrides/partials/"
    scopes["website_partials"]["specificity_rank"] = max(
        scopes["website_partials"]["specificity_rank"], 30
    )
    normalized = {scope_id: normalize_scope(scope) for scope_id, scope in scopes.items()}
    normalized["root_maintained_files"] = {
        "scope_id": "root_maintained_files",
        "display_name": "Maintained repository-root files",
        "path_pattern": "{root_file}",
        "match_kind": "parameterized_exact",
        "specificity_rank": 20,
        "parameter_bindings": {"root_file": {"allowed_values": ROOT_MAINTAINED_FILES}},
        "ancestor_scope_ids": ["repository_root"],
        "purpose": "Canonical placement for the approved maintained public files at the repository root.",
        "placement_question": "Is this one of the exact approved maintained repository-root files?",
        "include_when": ["The path is one of the exact governed root filenames."],
        "exclude_when": ["Directories, unlisted files, generated output, temporary material, or owner-local state."],
        "primary_authority": "COMPONENT-REGISTRY",
        "ownership": "@Thorncrag",
        "review_policy": "human_review_on_unexplained_item",
        "allow_children": False,
        "child_artifact_policy": "Exact files only; no child coverage.",
        "fallback": "human_review",
        "information_handling": {
            "information_classification": "public",
            "disclosure_boundary": "repository_public",
        },
        "repository_controls": {"github_codeowners": {"mode": "inherit"}},
    }
    registry["directory_scopes"]["schema_version"] = 3
    registry["directory_scopes"]["entries"] = normalized


def supporting(path: str, purpose: str, *, producer: str | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "artifact_id": path.replace("/", "_").replace(".", "_").replace("-", "_"),
        "path": path,
        "generated": producer is not None,
        "purpose": purpose,
        "provenance_event_id": PROVENANCE_EVENT_ID,
    }
    if producer:
        record["producer_component_id"] = producer
    return record


def base_component(
    stable_id: str,
    display_name: str,
    component_class: str,
    component_type: str,
    canonical_path: str,
    *,
    capabilities: list[str] | None = None,
    locator_kind: str = "repository_path",
    boundary: str | None = None,
) -> dict[str, Any]:
    source_binding: dict[str, Any]
    if locator_kind == "repository_path":
        source_binding = {
            "binding_basis": "content_digest",
            "applicability": "current",
            "verification_methods": ["pinned_comparison"],
            "sha256": sha256(canonical_path),
            "evidence_ref": PROVENANCE_EVENT_ID,
        }
    else:
        source_binding = {
            "binding_basis": "repository_revision",
            "applicability": "current",
            "verification_methods": ["pinned_comparison"],
            "repository_revision": BASE_REVISION,
            "evidence_ref": PROVENANCE_EVENT_ID,
        }
    record: dict[str, Any] = {
        "stable_id": stable_id,
        "display_name": display_name,
        "classification": {
            "component_class": component_class,
            "component_type": component_type,
            "roles": [],
            "capabilities": capabilities or [],
            "attributes": {},
        },
        "canonical_source": {
            "locator": {"kind": locator_kind, "value": canonical_path},
            "source_binding": source_binding,
        },
        "owner": "@Thorncrag",
        "information_handling": {
            "information_classification": "public",
            "disclosure_boundary": "repository_public",
        },
        "retention": {
            "bases": ["operational_need"],
            "revision_mode": "maintained",
            "custody": "repository",
            "review_condition": "review_on_governed_change",
            "retirement_condition": "separate_authorized_disposition",
        },
        "supporting_artifacts": [],
        "record_refs": {
            "lifecycle_assignments": [stable_id],
            "authority_assignments": [f"authority_{stable_id}"],
            "relationships": [],
            "migrations": [],
            "provenance_events": [PROVENANCE_EVENT_ID],
        },
        "repository_controls": {"github_codeowners": {"mode": "inherit"}},
    }
    if boundary:
        record["component_boundary"] = {"kind": "repository_directory", "path": boundary}
    if "executable" in (capabilities or []):
        record["operational_status"] = "inactive"
    return record


def add_lifecycle_and_authority(registry: dict[str, Any], component_id: str, authoritative: bool) -> None:
    registry["component_lifecycles"]["assignments"][component_id] = {
        "component_id": component_id,
        "current_state": "adopted",
        "effective_date": "2026-08-02",
        "transition_reason": PROVENANCE_EVENT_ID,
        "history": [{
            "from": None,
            "to": "adopted",
            "effective_date": "2026-08-02",
            "reason": PROVENANCE_EVENT_ID,
            "provenance_event_id": PROVENANCE_EVENT_ID,
        }],
    }
    assignment_id = f"authority_{component_id}"
    registry["component_authorities"]["assignments"][assignment_id] = {
        "assignment_id": assignment_id,
        "component_id": component_id,
        "authoritative": authoritative,
        "source_ids": ["stage3_contract_revision"],
        "subjects": [{"kind": "component", "id": component_id}],
        "effects": ["govern_content"] if authoritative else [],
        "exclusions": ["no_authority_beyond_registered_component_scope"],
        "effective_date": "2026-08-02",
        "termination_conditions": ["retirement_or_superseding_authority"],
        "governing_precedence": ["stage3_contract_revision"],
        "provenance_event_id": PROVENANCE_EVENT_ID,
    }


def normalize_components(registry: dict[str, Any]) -> None:
    components = registry["components"]["entries"]
    registry["components"]["schema_version"] = 3
    for component in components.values():
        retention = component.get("retention")
        if isinstance(retention, dict) and "change_mode" in retention:
            retention["revision_mode"] = retention.pop("change_mode")
        component["supporting_artifacts"] = replace_current_paths(component.get("supporting_artifacts", []))
        component["canonical_source"] = replace_current_paths(component["canonical_source"])
        component.setdefault("repository_controls", {"github_codeowners": {"mode": "inherit"}})

    for former in ("project_console_progress", "project_console_classifications"):
        components.pop(former)
        registry["component_lifecycles"]["assignments"].pop(former)
        registry["component_authorities"]["assignments"].pop(f"authority_{former}")

    spec = components["project_tool_interface"]
    spec["display_name"] = "ARRP Project Console Specification"
    spec["canonical_source"] = replace_current_paths(spec["canonical_source"])
    spec["record_refs"]["relationships"].append("project_console_specification_implemented_by_console")
    spec["record_refs"]["provenance_events"].append(PROVENANCE_EVENT_ID)

    project_console = base_component(
        "project_console", "ARRP Project Console", "interface", "hybrid",
        "framework/project/interfaces/project-console/project-console.html",
        boundary="framework/project/interfaces/project-console/",
    )
    console_support = [
        ("framework/project/interfaces/project-console/app.js", "Maintained Console application behavior."),
        ("framework/project/interfaces/project-console/styles.css", "Maintained Console visual design."),
        ("framework/project/interfaces/project-console/component-registry.js", "Maintained Component Registry Console interface."),
        ("framework/project/interfaces/project-console/capacity.js", "Maintained Console capacity interface."),
        ("framework/project/interfaces/project-console/README.md", "Console implementation guidance."),
        ("framework/project/interfaces/project-console/configuration/classifications.json", "Console classification configuration."),
        ("tests/project-console/frontend.test.mjs", "Console frontend regression suite."),
        ("tests/test_console_data_contracts.py", "Console data-contract regression suite."),
    ]
    for name in (
        "project-console-v1.0-operations-overview.jpg",
        "project-console-v1.0-overview.jpg",
        "project-console-v1.0-planning-workbench.jpg",
        "project-console-v1.0-progress.jpg",
    ):
        console_support.append((f"framework/project/interfaces/project-console/visual-baselines/{name}", "Approved Console visual baseline."))
    project_console["supporting_artifacts"] = [supporting(path, purpose) for path, purpose in console_support]

    builder = base_component(
        "project_console_builder", "Project Console Builder", "script", "generator",
        "scripts/build_project_console.py", capabilities=["executable", "generator"],
    )
    website = base_component(
        "public_website", "ARRP Public Website", "interface", "human", "website/",
        locator_kind="repository_directory", boundary="website/",
    )
    participate = base_component(
        "public_participation_interface", "ARRP Public Participation Interface", "interface", "human", "participate/",
        locator_kind="repository_directory", boundary="participate/",
    )
    for component, authoritative in (
        (project_console, False), (builder, False), (website, False), (participate, False)
    ):
        components[component["stable_id"]] = component
        add_lifecycle_and_authority(registry, component["stable_id"], authoritative)

    project_console["record_refs"]["relationships"].append("project_console_specification_implemented_by_console")
    components["component_registry_tool"]["supporting_artifacts"].append(
        supporting("scripts/apply_component_registry_stage3_migration.py", "Deterministic Stage 3 Registry migration helper.")
    )
    components["component_registry_schema"]["repository_controls"] = {
        "github_codeowners": {"mode": "direct", "owners": ["@Thorncrag"]}
    }
    for path in (
        "tests/framework/test_component_registry_activation_finalizer.py",
        "tests/framework/test_component_registry_stage1_acceptance.py",
        "tests/framework/test_component_registry_activation_readback.py",
        "tests/framework/test_component_registry_activation_readiness.py",
    ):
        components["component_registry_tests"]["supporting_artifacts"].append(
            supporting(path, "Maintained Component Registry regression source.")
        )
    for component_id, config_path in {
        "case-monitor-bot": "framework/project/automation/configuration/bots/case-monitor-bot.json",
        "presidential-directives-bot": "framework/project/automation/configuration/bots/presidential-directives-bot.json",
        "run-coordinator-bot": "framework/project/automation/configuration/bots/run-coordinator-bot.json",
        "source-checker-bot": "framework/project/automation/configuration/bots/source-checker-bot.json",
    }.items():
        components[component_id]["supporting_artifacts"].append(
            supporting(config_path, "Governed runtime configuration for this bot.")
        )
    components["progress_config"]["supporting_artifacts"].append(
        supporting("framework/project/interfaces/project-console/configuration/progress-history-seed.json", "Governed progress-history seed.")
    )
    components["progress_config"]["supporting_artifacts"].append(
        supporting("framework/project/interfaces/project-console/configuration/progress.md", "Human-readable progress configuration.")
    )
    components["source-checker-bot"]["execution_controls"] = {
        "live_execution": True,
        "automated": {
            "mode": "automated",
            "coordinator_component_id": "run-coordinator-bot",
            "chain_id": "daily_automation_chain",
            "condition": "due_under_governed_cadence",
        },
        "manual": {
            "mode": "manual",
            "authority_condition": "explicit_current_human_instruction",
            "interfaces": ["llm_assisted", "direct_script"],
        },
        "runbook_component_id": "runbook_source_checker_bot",
        "prohibited_purposes": [
            "agent_discretion", "console_currentness", "generated_output_refresh",
            "testing", "validation", "evidence_refresh",
        ],
        "fixture_tests_are_live_execution": False,
    }


def normalize_authority_and_provenance(registry: dict[str, Any]) -> None:
    authorities = registry["component_authorities"]
    authorities["schema_version"] = 2
    authorities["sources"]["stage3_contract_revision"] = {
        "source_id": "stage3_contract_revision",
        "source_type": "design_contract_revision",
        "design_id": DESIGN_ID,
        "design_revision": DESIGN_REVISION,
        "contract_id": DESIGN_ID,
        "contract_revision": 1,
        "external_evidence_id": EXTERNAL_EVIDENCE_ID,
        "contract_sha256": CONTRACT_SHA256,
    }
    authorities["registry_modification_control"] = {
        "active_mode": "design_contract",
        "active_source_id": "stage3_contract_revision",
        "base_revision": BASE_REVISION,
        "permitted_scope": "exact_bound_stage3_contract_write_scope",
        "exclusions": [
            "no_authority_expansion", "no_source_checker_live_run",
            "no_production_execution", "no_unpause", "no_host_or_background_service_change",
        ],
        "termination_conditions": [
            "stage3_transaction_close", "owner_revocation", "source_supersession",
        ],
        "owner_direct": {
            "production_enabled": False,
            "resolution_state": "unavailable",
            "reason": "no_approved_authenticated_immutable_owner_instruction_resolver",
        },
    }
    assignment = authorities["assignments"]["authority_COMPONENT-REGISTRY"]
    if "stage3_contract_revision" not in assignment["source_ids"]:
        assignment["source_ids"].append("stage3_contract_revision")
        assignment["governing_precedence"].append("stage3_contract_revision")
    assignment["provenance_event_id"] = PROVENANCE_EVENT_ID
    authorities["history"].append({
        "event": "stage3_coordinated_reconciliation_authority_revision",
        "effective_date": "2026-08-02",
        "authority_generation": registry["authority_digest_model"]["generation"] + 1,
        "source_ids": ["stage3_contract_revision"],
    })
    registry["authority_digest_model"]["generation"] += 1
    registry["provenance_events"]["entries"][PROVENANCE_EVENT_ID] = {
        "event_id": PROVENANCE_EVENT_ID,
        "event_type": "adoption",
        "occurred_on": "2026-08-02",
        "originating_component_id": "COMPONENT-REGISTRY",
        "authorization_source_ids": ["stage3_contract_revision"],
        "design_contract_revision": DESIGN_REVISION,
        "change_identity": DESIGN_ID,
        "introduced_revision": "adopted_configuration_validation",
        "affected_ids": [
            "COMPONENT-REGISTRY", "directory_scopes", "registration_exemptions",
            "repository_coverage", "project_console", "project_console_builder",
            "public_website", "public_participation_interface",
        ],
    }


def normalize_relationships_and_routing(registry: dict[str, Any]) -> None:
    relationships = registry["relationships"]["entries"]
    for relationship in relationships.values():
        relationship.setdefault("effective_date", "2026-07-31")
        relationship.setdefault("provenance_event_id", "stage2_baseline_migration")
    relationships["project_console_specification_implemented_by_console"] = {
        "relationship_id": "project_console_specification_implemented_by_console",
        "relationship_type": "implemented_by",
        "from": {"kind": "component", "id": "project_tool_interface"},
        "to": {"kind": "component", "id": "project_console"},
        "authority_boundary": "The implementation does not originate or enlarge specification authority.",
        "effective_date": "2026-08-02",
        "provenance_event_id": PROVENANCE_EVENT_ID,
    }
    routing = registry["routing"]
    removed = {"project_console_progress", "project_console_classifications"}
    for record in routing["components"].values():
        record["requires"] = [value for value in record.get("requires", []) if value not in removed]
    for key, values in routing["capabilities"].items():
        routing["capabilities"][key] = [value for value in values if value not in removed]
    for profile in routing["profiles"].values():
        if "components" in profile:
            profile["components"] = [value for value in profile["components"] if value not in removed]
        for section in profile.get("sections", []):
            if section.get("component") in removed:
                section["component"] = "project_tool_interface"
    for removed_id in removed:
        routing["components"].pop(removed_id, None)
    routing["required_components"] = [value for value in routing["required_components"] if value not in removed]


def normalize_migrations(registry: dict[str, Any]) -> None:
    migrations = registry["migrations_and_aliases"]["entries"]
    canonical_by_path = {
        component.get("canonical_source", {}).get("locator", {}).get("value"): component_id
        for component_id, component in registry["components"]["entries"].items()
    }
    for index, (source, target) in enumerate(PATH_MIGRATIONS.items(), 1):
        migration_id = f"stage3_path_migration_{index:02d}"
        record = {
            "migration_id": migration_id,
            "kind": "path_migration",
            "source_path": source,
            "target_path": target,
            "historical_only": True,
            "provenance_event_id": PROVENANCE_EVENT_ID,
        }
        component_id = canonical_by_path.get(target)
        if component_id:
            record["component_id"] = component_id
            registry["components"]["entries"][component_id]["record_refs"]["migrations"].append(migration_id)
        migrations[migration_id] = record
    migrations["stage3_visual_baselines_migration"] = {
        "migration_id": "stage3_visual_baselines_migration",
        "kind": "path_migration",
        "component_id": "project_console",
        "source_path": "framework/project/interfaces/visual-baselines/",
        "target_path": "framework/project/interfaces/project-console/visual-baselines/",
        "historical_only": True,
        "provenance_event_id": PROVENANCE_EVENT_ID,
    }
    registry["components"]["entries"]["project_console"]["record_refs"]["migrations"].append("stage3_visual_baselines_migration")
    for former, target in {
        "project_console_progress": "project_console",
        "project_console_classifications": "project_console",
    }.items():
        migration_id = f"stage3_identity_consolidation_{former}"
        migrations[migration_id] = {
            "migration_id": migration_id,
            "kind": "stable_id_migration",
            "source_id": former,
            "target_id": target,
            "historical_only": True,
            "provenance_event_id": PROVENANCE_EVENT_ID,
            "allowed_residual_occurrences": [],
        }
        registry["components"]["entries"][target]["record_refs"]["migrations"].append(migration_id)


def scope_matches(path: str, scope: dict[str, Any]) -> bool:
    kind = scope["match_kind"]
    pattern = scope["path_pattern"]
    if kind == "tree":
        return True
    if kind == "exact_file":
        return path == pattern
    if kind == "prefix":
        return path.startswith(pattern.rstrip("/") + "/")
    parts = Path(path).parts
    pattern_parts = tuple(part for part in pattern.split("/") if part)
    recursive = kind == "parameterized_prefix"
    if recursive and pattern_parts:
        expected_length = len(pattern_parts)
        if len(parts) < expected_length:
            return False
    elif len(parts) != len(pattern_parts):
        return False
    for actual, expected in zip(parts, pattern_parts):
        if expected.startswith("{") and expected.endswith("}"):
            values = scope["parameter_bindings"][expected[1:-1]]["allowed_values"]
            if actual not in values:
                return False
        elif actual != expected:
            return False
    return True


def select_scope(path: str, scopes: dict[str, Any]) -> str:
    matches = [
        (scope["specificity_rank"], scope_id)
        for scope_id, scope in scopes.items()
        if scope_id != "repository_root" and scope_matches(path, scope)
    ]
    if not matches:
        raise ValueError(f"unresolved placement: {path}")
    highest = max(rank for rank, _ in matches)
    owners = [scope_id for rank, scope_id in matches if rank == highest]
    if len(owners) != 1:
        raise ValueError(f"ambiguous placement for {path}: {sorted(owners)}")
    return owners[0]


def build_coverage(registry: dict[str, Any]) -> None:
    components = registry["components"]["entries"]
    canonical_files = {
        component["canonical_source"]["locator"]["value"]: component_id
        for component_id, component in components.items()
        if component["canonical_source"]["locator"]["kind"] == "repository_path"
    }
    support: dict[str, tuple[str, str]] = {}
    for component_id, component in components.items():
        for artifact in component["supporting_artifacts"]:
            path = artifact["path"]
            if path in support:
                raise ValueError(f"supporting artifact has multiple owners: {path}")
            support[path] = (component_id, artifact["artifact_id"])
    scopes = registry["directory_scopes"]["entries"]
    entries: dict[str, Any] = {}
    unresolved: list[dict[str, str]] = []
    for path in tracked_paths():
        try:
            scope_id = select_scope(path, scopes)
        except ValueError as exc:
            unresolved.append({"path": path, "reason": str(exc)})
            continue
        explicit: list[dict[str, Any]] = []
        if path in canonical_files:
            explicit.append({"kind": "component", "component_id": canonical_files[path]})
        if path in support:
            component_id, artifact_id = support[path]
            explicit.append({"kind": "supporting_artifact", "component_id": component_id, "artifact_id": artifact_id})
        if path.startswith("framework/project/interfaces/project-console/data/") or path == "framework/project/interfaces/project-console/catalog-data.js":
            explicit.append({"kind": "registration_exemption", "exemption_id": "project_console_generated_data"})
        if path.startswith(".tmp/"):
            explicit.append({"kind": "registration_exemption", "exemption_id": "repository_tmp_children"})
        if not explicit and scope_id in {"root_maintained_files", "root_requirements_local_tools", "root_requirements_pages"}:
            explicit.append({"kind": "registration_exemption", "exemption_id": "maintained_root_files"})
        if len(explicit) > 1:
            unresolved.append({"path": path, "reason": "multiple explicit registration treatments"})
            continue
        if explicit:
            treatment = explicit[0]
        elif scopes[scope_id]["allow_children"]:
            treatment = {"kind": "ordinary_scoped_child"}
        else:
            unresolved.append({"path": path, "reason": "scope does not allow ordinary children"})
            continue
        entries[path] = {
            "placement": {"scope_id": scope_id, "admission_evidence_id": PROVENANCE_EVENT_ID},
            "treatment": treatment,
        }
    if unresolved:
        raise ValueError(json.dumps(unresolved, indent=2))
    registry["repository_coverage"] = {
        "schema_version": 2,
        "claim": "tracked_repository_coverage",
        "entries": entries,
        "unresolved": [],
        "uncovered_count": 0,
        "multiply_treated_count": 0,
    }


def normalize_exemptions(registry: dict[str, Any]) -> None:
    tmp = registry.pop("supporting_artifact_rules")["entries"]["repository_tmp_children"]
    tmp["exemption_id"] = tmp.pop("rule_id")
    tmp["term_id"] = "component_registration_exemption"
    registry["registration_exemptions"] = {
        "schema_version": 1,
        "entries": {
            "repository_tmp_children": tmp,
            "project_console_generated_data": {
                "exemption_id": "project_console_generated_data",
                "term_id": "component_registration_exemption",
                "scope_id": "project_console_data",
                "exact_paths": ["framework/project/interfaces/project-console/catalog-data.js"],
                "artifact_class": "generated_output",
                "authorized_producers": ["project_console_builder"],
                "canonical": False,
                "independently_controlled_information": False,
                "post_run_disposition": "replace_with_current_verified_generation",
                "exemption_end_conditions": [
                    "becomes_independently_maintained", "becomes_authoritative",
                    "moves_outside_approved_scope", "producer_binding_is_unavailable",
                ],
            },
            "maintained_root_files": {
                "exemption_id": "maintained_root_files",
                "term_id": "component_registration_exemption",
                "scope_ids": [
                    "root_maintained_files",
                    "root_requirements_local_tools",
                    "root_requirements_pages",
                ],
                "excluded_paths": ["AGENTS.md", "README.md"],
                "artifact_class": "maintained_repository_root_artifact",
                "authorized_producers": ["authorized_project_maintainers"],
                "canonical": True,
                "independently_controlled_information": True,
                "post_run_disposition": "not_applicable_maintained_artifact",
                "exemption_end_conditions": [
                    "moves_outside_approved_scope",
                    "becomes_an_independently_governed_component",
                ],
            },
        },
    }


def refresh_source_bindings(registry: dict[str, Any]) -> None:
    for component in registry["components"]["entries"].values():
        locator = component["canonical_source"]["locator"]
        binding = component["canonical_source"]["source_binding"]
        if locator["kind"] == "repository_path" and binding["binding_basis"] == "content_digest":
            binding["sha256"] = sha256(locator["value"])


def migrate_registry(registry: dict[str, Any]) -> dict[str, Any]:
    registry = copy.deepcopy(registry)
    registry["$schema"] = "component-registry.schema.json"
    registry["schema_version"] = 3
    registry["registry_revision"] = 3
    registry["validation"] = {
        "mode": "adopted_configuration_validation",
        "design_id": DESIGN_ID,
        "design_revision": DESIGN_REVISION,
        "repository_base_revision": BASE_REVISION,
        "live_authority": False,
    }
    normalize_terminology(registry)
    normalize_enums(registry)
    normalize_scopes(registry)
    normalize_components(registry)
    normalize_authority_and_provenance(registry)
    normalize_relationships_and_routing(registry)
    normalize_exemptions(registry)
    normalize_migrations(registry)
    refresh_source_bindings(registry)
    build_coverage(registry)
    return registry


def reconcile_stage3_current_records(registry: dict[str, Any]) -> None:
    for component in registry["components"]["entries"].values():
        locator_kind = component["canonical_source"]["locator"]["kind"]
        component.setdefault(
            "repository_controls",
            {"github_codeowners": {"mode": "inherit" if locator_kind in {"repository_path", "repository_directory"} else "none"}},
        )
        if locator_kind not in {"repository_path", "repository_directory"}:
            component["repository_controls"] = {"github_codeowners": {"mode": "none"}}
    registry["registration_exemptions"]["entries"]["maintained_root_files"]["excluded_paths"] = [
        "AGENTS.md", "README.md"
    ]
    registry["directory_scopes"]["entries"]["root_maintained_files"]["repository_controls"] = {
        "github_codeowners": {"mode": "inherit"}
    }
    registry["components"]["entries"]["component_registry_schema"][
        "repository_controls"
    ] = {
        "github_codeowners": {"mode": "direct", "owners": ["@Thorncrag"]}
    }


def closed_object(required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def entries_namespace(schema_version: int, entry_ref: str) -> dict[str, Any]:
    return closed_object(
        ["schema_version", "entries"],
        {
            "schema_version": {"const": schema_version},
            "entries": {
                "type": "object",
                "additionalProperties": {"$ref": entry_ref},
            },
        },
    )


def migrate_schema(schema: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    schema = copy.deepcopy(schema)
    schema["title"] = "ARRP Component Registry Stage 3"
    schema["description"] = "Closed Stage 3 component, directory, authority, execution, and coverage configuration."
    schema["required"] = [
        "$schema", "schema_version", "registry_id", "registry_revision",
        "validation", "authority_digest_model", "terminology", "implementation_enums",
        "directory_scopes", "components", "component_lifecycles", "component_authorities",
        "relationships", "migrations_and_aliases", "provenance_events", "routing",
        "registration_exemptions", "repository_coverage",
    ]
    properties = schema["properties"]
    properties["schema_version"] = {"const": 3}
    properties["registry_revision"] = {"const": 3}
    properties.pop("supporting_artifact_rules", None)
    properties["registration_exemptions"] = {"$ref": "#/$defs/registrationExemptionNamespace"}
    properties["repository_coverage"] = {"$ref": "#/$defs/repositoryCoverage"}
    properties["component_lifecycles"] = {"$ref": "#/$defs/lifecycleNamespace"}
    properties["component_authorities"] = {"$ref": "#/$defs/authorityNamespace"}
    properties["relationships"] = {"$ref": "#/$defs/relationshipNamespace"}
    properties["migrations_and_aliases"] = {"$ref": "#/$defs/migrationNamespace"}
    properties["provenance_events"] = {"$ref": "#/$defs/provenanceNamespace"}
    properties["routing"] = {"$ref": "#/$defs/routingNamespace"}
    defs = schema["$defs"]
    defs["validationEnvelope"] = closed_object(
        ["mode", "design_id", "design_revision", "repository_base_revision", "live_authority"],
        {
            "mode": {"const": "adopted_configuration_validation"},
            "design_id": {"const": DESIGN_ID},
            "design_revision": {"const": DESIGN_REVISION},
            "repository_base_revision": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
            "live_authority": {"const": False},
        },
    )
    term_count = len(registry["terminology"]["entries"])
    defs["terminologyNamespace"]["properties"]["record_set_sha256"] = {
        "const": registry["terminology"]["record_set_sha256"]
    }
    defs["terminologyNamespace"]["properties"]["order"].update({"minItems": term_count, "maxItems": term_count})
    defs["terminologyNamespace"]["properties"]["entries"].update({"minProperties": term_count, "maxProperties": term_count})
    term_ref = closed_object(["term_id"], {"term_id": {"$ref": "#/$defs/nonemptyString"}})
    defs["termReference"] = term_ref
    defs["enumValueDefinition"] = {
        "oneOf": [
            {"type": "string", "minLength": 1},
            {"$ref": "#/$defs/termReference"},
        ]
    }
    defs["enumDefinitions"]["additionalProperties"] = {"$ref": "#/$defs/enumValueDefinition"}
    defs["possiblyEmptyEnumDefinitions"]["additionalProperties"] = {"$ref": "#/$defs/enumValueDefinition"}
    enum_schema = defs["implementationEnums"]
    enum_schema["required"] = [
        "schema_version", "owner_decision", "component_classes", "component_types",
        "roles", "capabilities", "operational_statuses", "relationship_types",
        "retention_bases", "revision_modes", "custody_values", "information_classifications",
        "disclosure_rules", "disclosure_boundaries", "source_binding_bases",
        "verification_methods", "migration_kinds", "coverage_treatments",
        "authority_source_types", "authority_effects", "registry_authorization_modes",
        "execution_initiation_modes", "execution_interfaces", "controlled_fields",
    ]
    enum_schema["properties"].pop("change_modes", None)
    for name in (
        "revision_modes", "registry_authorization_modes", "execution_initiation_modes",
        "execution_interfaces", "controlled_fields",
    ):
        enum_schema["properties"][name] = {"$ref": "#/$defs/enumDefinitions"}

    defs["classification"] = closed_object(
        ["component_class", "roles", "capabilities", "attributes"],
        {
            "component_class": {"$ref": "#/$defs/nonemptyString"},
            "component_type": {"$ref": "#/$defs/nonemptyString"},
            "roles": {"$ref": "#/$defs/stringArray"},
            "capabilities": {"$ref": "#/$defs/stringArray"},
            "attributes": {"type": "object"},
        },
    )
    defs["locator"] = closed_object(
        ["kind", "value"],
        {
            "kind": {"enum": ["repository_path", "repository_directory", "governed_external_identifier"]},
            "value": {"$ref": "#/$defs/nonemptyString"},
        },
    )
    defs["sourceBinding"] = closed_object(
        ["binding_basis", "applicability", "verification_methods", "evidence_ref"],
        {
            "binding_basis": {"$ref": "#/$defs/nonemptyString"},
            "applicability": {"$ref": "#/$defs/nonemptyString"},
            "verification_methods": {"$ref": "#/$defs/stringArray"},
            "evidence_ref": {"$ref": "#/$defs/nonemptyString"},
            "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "repository_revision": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
            "external_identifier": {"$ref": "#/$defs/nonemptyString"},
        },
    )
    defs["canonicalSource"] = closed_object(
        ["locator", "source_binding"],
        {"locator": {"$ref": "#/$defs/locator"}, "source_binding": {"$ref": "#/$defs/sourceBinding"}},
    )
    defs["informationHandling"] = closed_object(
        ["information_classification", "disclosure_boundary"],
        {
            "information_classification": {"$ref": "#/$defs/nonemptyString"},
            "disclosure_rule": {"$ref": "#/$defs/nonemptyString"},
            "disclosure_boundary": {"$ref": "#/$defs/nonemptyString"},
        },
    )
    defs["retention"] = closed_object(
        ["bases", "revision_mode", "custody", "review_condition", "retirement_condition"],
        {
            "bases": {"$ref": "#/$defs/stringArray"},
            "revision_mode": {"enum": ["maintained", "append_only", "immutable", "replaceable"]},
            "custody": {"$ref": "#/$defs/nonemptyString"},
            "review_condition": {"$ref": "#/$defs/nonemptyString"},
            "retirement_condition": {"$ref": "#/$defs/nonemptyString"},
        },
    )
    defs["supportingArtifact"] = closed_object(
        ["artifact_id", "path", "generated", "purpose", "provenance_event_id"],
        {
            "artifact_id": {"$ref": "#/$defs/nonemptyString"},
            "path": {"$ref": "#/$defs/nonemptyString"},
            "generated": {"type": "boolean"},
            "producer_component_id": {"$ref": "#/$defs/nonemptyString"},
            "purpose": {"$ref": "#/$defs/nonemptyString"},
            "provenance_event_id": {"$ref": "#/$defs/nonemptyString"},
        },
    )
    defs["recordRefs"] = closed_object(
        ["lifecycle_assignments", "authority_assignments", "relationships", "migrations", "provenance_events"],
        {name: {"$ref": "#/$defs/stringArray"} for name in (
            "lifecycle_assignments", "authority_assignments", "relationships", "migrations", "provenance_events"
        )},
    )
    defs["componentBoundary"] = closed_object(
        ["kind", "path"],
        {"kind": {"const": "repository_directory"}, "path": {"$ref": "#/$defs/nonemptyString"}},
    )
    defs["executionControls"] = closed_object(
        ["live_execution", "automated", "manual", "runbook_component_id", "prohibited_purposes", "fixture_tests_are_live_execution"],
        {
            "live_execution": {"const": True},
            "automated": {"$ref": "#/$defs/automatedInitiation"},
            "manual": {"$ref": "#/$defs/manualInitiation"},
            "runbook_component_id": {"$ref": "#/$defs/nonemptyString"},
            "prohibited_purposes": {"$ref": "#/$defs/stringArray"},
            "fixture_tests_are_live_execution": {"const": False},
        },
    )
    defs["automatedInitiation"] = closed_object(
        ["mode", "coordinator_component_id", "chain_id", "condition"],
        {
            "mode": {"const": "automated"},
            "coordinator_component_id": {"const": "run-coordinator-bot"},
            "chain_id": {"const": "daily_automation_chain"},
            "condition": {"const": "due_under_governed_cadence"},
        },
    )
    defs["manualInitiation"] = closed_object(
        ["mode", "authority_condition", "interfaces"],
        {
            "mode": {"const": "manual"},
            "authority_condition": {"const": "explicit_current_human_instruction"},
            "interfaces": {"const": ["llm_assisted", "direct_script"]},
        },
    )
    defs["componentRecord"] = closed_object(
        ["stable_id", "display_name", "classification", "canonical_source", "owner", "information_handling", "retention", "supporting_artifacts", "record_refs", "repository_controls"],
        {
            "stable_id": {"$ref": "#/$defs/nonemptyString"},
            "display_name": {"$ref": "#/$defs/nonemptyString"},
            "classification": {"$ref": "#/$defs/classification"},
            "canonical_source": {"$ref": "#/$defs/canonicalSource"},
            "component_boundary": {"$ref": "#/$defs/componentBoundary"},
            "owner": {"$ref": "#/$defs/nonemptyString"},
            "information_handling": {"$ref": "#/$defs/informationHandling"},
            "retention": {"$ref": "#/$defs/retention"},
            "supporting_artifacts": {"type": "array", "items": {"$ref": "#/$defs/supportingArtifact"}},
            "operational_status": {"enum": ["active", "paused", "inactive"]},
            "execution_controls": {"$ref": "#/$defs/executionControls"},
            "record_refs": {"$ref": "#/$defs/recordRefs"},
            "repository_controls": {"$ref": "#/$defs/repositoryControls"},
        },
    )
    defs["componentNamespace"] = entries_namespace(3, "#/$defs/componentRecord")

    scope_properties = {
        "scope_id": {"$ref": "#/$defs/nonemptyString"}, "display_name": {"$ref": "#/$defs/nonemptyString"},
        "path_pattern": {"$ref": "#/$defs/nonemptyString"},
        "match_kind": {"enum": ["tree", "prefix", "exact_file", "parameterized_prefix", "parameterized_exact"]},
        "specificity_rank": {"type": "integer", "minimum": 0}, "parameter_bindings": {"type": "object"},
        "ancestor_scope_ids": {"$ref": "#/$defs/stringArray"}, "purpose": {"$ref": "#/$defs/nonemptyString"},
        "placement_question": {"$ref": "#/$defs/nonemptyString"}, "include_when": {"$ref": "#/$defs/stringArray"},
        "exclude_when": {"$ref": "#/$defs/stringArray"}, "primary_authority": {"$ref": "#/$defs/nonemptyString"},
        "ownership": {"$ref": "#/$defs/nonemptyString"}, "review_policy": {"$ref": "#/$defs/nonemptyString"},
        "authorized_creators": {"$ref": "#/$defs/stringArray"}, "allow_children": {"type": "boolean"},
        "child_artifact_policy": {"$ref": "#/$defs/nonemptyString"},
        "revision_mode": {"enum": ["append_only", "immutable", "replaceable"]},
        "retention": {"type": "object"}, "information_handling": {"$ref": "#/$defs/informationHandling"},
        "fallback": {"const": "human_review"}, "repository_controls": {"$ref": "#/$defs/repositoryControls"},
    }
    defs["directoryScope"] = closed_object(
        ["scope_id", "display_name", "path_pattern", "match_kind", "specificity_rank", "parameter_bindings", "ancestor_scope_ids", "purpose", "placement_question", "include_when", "exclude_when", "primary_authority", "ownership", "review_policy", "allow_children", "child_artifact_policy", "fallback", "repository_controls"],
        scope_properties,
    )
    defs["directoryScopeNamespace"] = entries_namespace(3, "#/$defs/directoryScope")

    defs["lifecycleTransition"] = closed_object(
        ["from", "to", "effective_date", "reason", "provenance_event_id"],
        {
            "from": {"anyOf": [{"type": "null"}, {"enum": ["draft", "proposed", "adopted", "retired"]}]},
            "to": {"enum": ["draft", "proposed", "adopted", "retired"]},
            "effective_date": {"$ref": "#/$defs/nonemptyString"}, "reason": {"$ref": "#/$defs/nonemptyString"},
            "provenance_event_id": {"$ref": "#/$defs/nonemptyString"},
        },
    )
    defs["lifecycleAssignment"] = closed_object(
        ["component_id", "current_state", "effective_date", "transition_reason", "history"],
        {
            "component_id": {"$ref": "#/$defs/nonemptyString"},
            "current_state": {"enum": ["draft", "proposed", "adopted", "retired"]},
            "effective_date": {"$ref": "#/$defs/nonemptyString"}, "transition_reason": {"$ref": "#/$defs/nonemptyString"},
            "history": {"type": "array", "items": {"$ref": "#/$defs/lifecycleTransition"}},
        },
    )
    defs["lifecycleNamespace"] = closed_object(
        ["schema_version", "states", "permitted_transitions", "assignments"],
        {
            "schema_version": {"const": 1}, "states": {"type": "object"},
            "permitted_transitions": {"type": "array"},
            "assignments": {"type": "object", "additionalProperties": {"$ref": "#/$defs/lifecycleAssignment"}},
        },
    )
    defs["authoritySource"] = {
        "type": "object", "additionalProperties": False, "required": ["source_id", "source_type", "revision"],
        "properties": {
            "source_id": {"$ref": "#/$defs/nonemptyString"}, "source_type": {"$ref": "#/$defs/nonemptyString"},
            "revision": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
            "public_reference": {"$ref": "#/$defs/nonemptyString"}, "component_id": {"$ref": "#/$defs/nonemptyString"},
            "design_id": {"$ref": "#/$defs/nonemptyString"}, "design_revision": {"$ref": "#/$defs/nonemptyString"},
            "contract_id": {"$ref": "#/$defs/nonemptyString"}, "contract_revision": {"type": "integer"},
            "external_evidence_id": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "contract_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
    }
    # Stage 3 source uses design_revision as its exact revision; normalize the
    # schema requirement with one branch rather than duplicating the payload.
    defs["authoritySource"].pop("required")
    defs["authoritySource"]["required"] = ["source_id", "source_type"]
    defs["authorityAssignment"] = closed_object(
        ["assignment_id", "component_id", "authoritative", "source_ids", "subjects", "effects", "exclusions", "effective_date", "termination_conditions", "governing_precedence", "provenance_event_id"],
        {
            "assignment_id": {"$ref": "#/$defs/nonemptyString"}, "component_id": {"$ref": "#/$defs/nonemptyString"},
            "authoritative": {"type": "boolean"}, "source_ids": {"$ref": "#/$defs/stringArray"},
            "subjects": {"type": "array", "items": {"type": "object"}}, "effects": {"$ref": "#/$defs/stringArray"},
            "exclusions": {"$ref": "#/$defs/stringArray"}, "effective_date": {"$ref": "#/$defs/nonemptyString"},
            "termination_conditions": {"$ref": "#/$defs/stringArray"}, "governing_precedence": {"$ref": "#/$defs/stringArray"},
            "provenance_event_id": {"$ref": "#/$defs/nonemptyString"},
        },
    )
    defs["registryModificationControl"] = closed_object(
        ["active_mode", "active_source_id", "base_revision", "permitted_scope", "exclusions", "termination_conditions", "owner_direct"],
        {
            "active_mode": {"const": "design_contract"}, "active_source_id": {"const": "stage3_contract_revision"},
            "base_revision": {"const": BASE_REVISION}, "permitted_scope": {"const": "exact_bound_stage3_contract_write_scope"},
            "exclusions": {"$ref": "#/$defs/stringArray"}, "termination_conditions": {"$ref": "#/$defs/stringArray"},
            "owner_direct": {"$ref": "#/$defs/ownerDirectControl"},
        },
    )
    defs["ownerDirectControl"] = closed_object(
        ["production_enabled", "resolution_state", "reason"],
        {"production_enabled": {"const": False}, "resolution_state": {"const": "unavailable"}, "reason": {"$ref": "#/$defs/nonemptyString"}},
    )
    defs["authorityNamespace"] = closed_object(
        ["schema_version", "source_types", "sources", "assignments", "history", "registry_modification_control"],
        {
            "schema_version": {"const": 2}, "source_types": {"type": "object"},
            "sources": {"type": "object", "additionalProperties": {"$ref": "#/$defs/authoritySource"}},
            "assignments": {"type": "object", "additionalProperties": {"$ref": "#/$defs/authorityAssignment"}},
            "history": {"type": "array", "items": {"type": "object"}},
            "registry_modification_control": {"$ref": "#/$defs/registryModificationControl"},
        },
    )
    defs["relationshipEndpoint"] = closed_object(
        ["kind", "id"], {"kind": {"$ref": "#/$defs/nonemptyString"}, "id": {"$ref": "#/$defs/nonemptyString"}}
    )
    defs["relationshipRecord"] = closed_object(
        ["relationship_id", "relationship_type", "from", "to", "authority_boundary", "effective_date", "provenance_event_id"],
        {
            "relationship_id": {"$ref": "#/$defs/nonemptyString"}, "relationship_type": {"$ref": "#/$defs/nonemptyString"},
            "from": {"$ref": "#/$defs/relationshipEndpoint"}, "to": {"$ref": "#/$defs/relationshipEndpoint"},
            "authority_boundary": {"$ref": "#/$defs/nonemptyString"}, "effective_date": {"$ref": "#/$defs/nonemptyString"},
            "provenance_event_id": {"$ref": "#/$defs/nonemptyString"},
        },
    )
    defs["relationshipNamespace"] = entries_namespace(1, "#/$defs/relationshipRecord")
    defs["migrationRecord"] = {
        "type": "object", "additionalProperties": False, "required": ["migration_id", "kind", "historical_only", "provenance_event_id"],
        "properties": {
            "migration_id": {"$ref": "#/$defs/nonemptyString"}, "kind": {"$ref": "#/$defs/nonemptyString"},
            "component_id": {"$ref": "#/$defs/nonemptyString"}, "source_path": {"$ref": "#/$defs/nonemptyString"},
            "target_path": {"$ref": "#/$defs/nonemptyString"}, "source_id": {"$ref": "#/$defs/nonemptyString"},
            "target_id": {"$ref": "#/$defs/nonemptyString"}, "historical_only": {"const": True},
            "provenance_event_id": {"$ref": "#/$defs/nonemptyString"}, "allowed_residual_occurrences": {"type": "array"},
        },
    }
    defs["migrationNamespace"] = entries_namespace(2, "#/$defs/migrationRecord")
    defs["provenanceRecord"] = closed_object(
        ["event_id", "event_type", "occurred_on", "authorization_source_ids", "change_identity", "introduced_revision", "affected_ids"],
        {
            "event_id": {"$ref": "#/$defs/nonemptyString"}, "event_type": {"$ref": "#/$defs/nonemptyString"},
            "occurred_on": {"$ref": "#/$defs/nonemptyString"}, "originating_component_id": {"$ref": "#/$defs/nonemptyString"},
            "authorization_source_ids": {"$ref": "#/$defs/stringArray"}, "design_contract_revision": {"$ref": "#/$defs/nonemptyString"},
            "change_identity": {"$ref": "#/$defs/nonemptyString"}, "introduced_revision": {"$ref": "#/$defs/nonemptyString"},
            "affected_ids": {"$ref": "#/$defs/stringArray"},
        },
    )
    defs["provenanceNamespace"] = entries_namespace(1, "#/$defs/provenanceRecord")
    defs["routingNamespace"] = closed_object(
        ["schema_version", "rule_catalog_version", "generated_path_exclusions", "required_components", "components", "capabilities", "profiles", "rules"],
        {
            "schema_version": {"const": 1}, "rule_catalog_version": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
            "generated_path_exclusions": {"$ref": "#/$defs/stringArray"}, "required_components": {"$ref": "#/$defs/stringArray"},
            "components": {"type": "object"}, "capabilities": {"type": "object"}, "profiles": {"type": "object"}, "rules": {"type": "object"},
        },
    )
    defs["registrationExemption"] = {
        "type": "object", "additionalProperties": False,
        "required": ["exemption_id", "term_id", "artifact_class", "authorized_producers", "canonical", "independently_controlled_information", "post_run_disposition", "exemption_end_conditions"],
        "properties": {
            "exemption_id": {"$ref": "#/$defs/nonemptyString"}, "term_id": {"const": "component_registration_exemption"},
            "scope_id": {"$ref": "#/$defs/nonemptyString"}, "scope_ids": {"$ref": "#/$defs/stringArray"},
            "exact_paths": {"$ref": "#/$defs/stringArray"}, "excluded_paths": {"$ref": "#/$defs/stringArray"},
            "artifact_class": {"$ref": "#/$defs/nonemptyString"},
            "authorized_producers": {"$ref": "#/$defs/stringArray"}, "canonical": {"type": "boolean"},
            "independently_controlled_information": {"type": "boolean"}, "post_run_disposition": {"$ref": "#/$defs/nonemptyString"},
            "exemption_end_conditions": {"$ref": "#/$defs/stringArray"},
        },
    }
    defs["registrationExemptionNamespace"] = entries_namespace(1, "#/$defs/registrationExemption")
    defs["coveragePlacement"] = closed_object(
        ["scope_id", "admission_evidence_id"],
        {"scope_id": {"$ref": "#/$defs/nonemptyString"}, "admission_evidence_id": {"$ref": "#/$defs/nonemptyString"}},
    )
    defs["coverageTreatment"] = {
        "type": "object", "additionalProperties": False, "required": ["kind"],
        "properties": {
            "kind": {"enum": ["component", "supporting_artifact", "registration_exemption", "ordinary_scoped_child"]},
            "component_id": {"$ref": "#/$defs/nonemptyString"}, "artifact_id": {"$ref": "#/$defs/nonemptyString"},
            "exemption_id": {"$ref": "#/$defs/nonemptyString"},
        },
    }
    defs["coverageEntry"] = closed_object(
        ["placement", "treatment"],
        {"placement": {"$ref": "#/$defs/coveragePlacement"}, "treatment": {"$ref": "#/$defs/coverageTreatment"}},
    )
    defs["repositoryCoverage"] = closed_object(
        ["schema_version", "claim", "entries", "unresolved", "uncovered_count", "multiply_treated_count"],
        {
            "schema_version": {"const": 2}, "claim": {"const": "tracked_repository_coverage"},
            "entries": {"type": "object", "additionalProperties": {"$ref": "#/$defs/coverageEntry"}},
            "unresolved": {"type": "array"}, "uncovered_count": {"const": 0}, "multiply_treated_count": {"const": 0},
        },
    )
    return schema


def main() -> int:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if registry.get("schema_version") == 2 and registry.get("registry_revision") == 2:
        registry = migrate_registry(registry)
        REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif registry.get("schema_version") != 3 or registry.get("registry_revision") != 3:
        raise SystemExit("Stage 3 migration requires the exact Stage 2 or Stage 3 Registry")
    else:
        reconcile_stage3_current_records(registry)
        REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema = migrate_schema(schema, registry)
    SCHEMA_PATH.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
