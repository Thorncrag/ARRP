import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import component_registry as registry


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "framework" / "component-registry.json"
SCHEMA_PATH = (
    ROOT
    / "framework"
    / "standards"
    / "automation"
    / "component-registry.schema.json"
)
ROUTE_PATH = (
    ROOT / "framework" / "archive" / "authorities" / "context-routes.json"
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_candidate_registry() -> dict[str, object]:
    current = load_json(REGISTRY_PATH)
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
        or registry._canonical_registry_digest(candidate)
        != current["approval"]["value"]["candidate_registry_sha256"]
    ):
        raise AssertionError("active registry candidate parent is not exact")
    return candidate


def current_source_path(relative: str) -> Path:
    source = ROOT / relative
    if source.exists():
        return source
    for specification in registry.ROUTING_PREDECESSOR_PATHS.values():
        if relative == specification["historical_path"]:
            return ROOT / specification["archived_path"]
    return source


class HistoricalComponentRegistryStage2AcceptanceTests:
    def setUp(self) -> None:
        self.registry = load_json(REGISTRY_PATH)
        self.route = registry._stage2_route_snapshot(self.registry)

    def test_stage2_registry_validates_in_proposed_mode(self):
        result = registry.validate_stage2_registry(self.registry, root=ROOT)
        self.assertTrue(result["valid"])
        self.assertEqual(result["validation_mode"], "proposed_revision_validation")
        self.assertFalse(result["authoritative"])
        self.assertFalse(result["executable"])
        self.assertFalse(result["live_authority"])

    def test_stage2_top_level_is_closed_and_has_no_family_construct(self):
        expected = {
            "$schema", "schema_version", "registry_id", "registry_revision",
            "validation", "authority_digest_model", "terminology",
            "implementation_enums",
            "directory_scopes", "components", "component_lifecycles",
            "component_authorities", "relationships", "migrations_and_aliases",
            "provenance_events", "routing", "supporting_artifact_rules",
            "repository_coverage",
        }
        self.assertEqual(set(self.registry), expected)
        self.assertFalse(any("famil" in key.lower() for key in self.registry))

    def test_exact_eight_component_classes_are_defined_and_used(self):
        definitions = self.registry["implementation_enums"]["component_classes"]
        self.assertEqual(tuple(definitions), registry.STAGE2_COMPONENT_CLASSES)
        used = {
            item["classification"]["component_class"]
            for item in self.registry["components"]["entries"].values()
        }
        self.assertTrue(used <= set(registry.STAGE2_COMPONENT_CLASSES))

    def test_exact_69_term_glossary_and_digest(self):
        records = registry._stage2_term_records(self.registry)
        self.assertEqual(len(records), 69)
        self.assertEqual(
            self.registry["terminology"]["record_set_sha256"],
            registry.STAGE2_TERMINOLOGY_SHA256,
        )

    def test_enum_definitions_preserve_owner_glossary_decision(self):
        enums = self.registry["implementation_enums"]
        self.assertEqual(
            enums["owner_decision"],
            {
                "decision": "closed_implementation_enums_are_schema_metadata_not_glossary_terms",
                "terminology_record_count": 69,
                "terminology_record_set_sha256": registry.STAGE2_TERMINOLOGY_SHA256,
            },
        )
        self.assertTrue(all(value.strip() for group in enums.values() if isinstance(group, dict) for value in group.values() if isinstance(value, str)))

    def test_component_inventory_has_unique_ids_and_canonical_paths(self):
        components = self.registry["components"]["entries"]
        self.assertEqual(len(components), 103)
        paths = [
            registry._stage2_component_path(component)
            for component in components.values()
        ]
        paths = [path for path in paths if path is not None]
        self.assertEqual(len(paths), len(set(paths)))

    def test_five_stable_id_migrations_are_exact(self):
        components = self.registry["components"]["entries"]
        migrations = self.registry["migrations_and_aliases"]["entries"]
        records = [
            value for value in migrations.values()
            if value["kind"] == "stable_id_migration"
        ]
        self.assertEqual(len(records), 5)
        self.assertEqual(
            {value["target_id"] for value in records},
            registry.STAGE2_STABLE_ID_TARGETS,
        )
        for value in records:
            self.assertNotIn(value["source_id"], components)
            self.assertIn(value["target_id"], components)
            self.assertTrue(value["historical_only"])

    def test_lifecycle_states_transitions_and_assignments_are_complete(self):
        lifecycle = self.registry["component_lifecycles"]
        self.assertEqual(tuple(lifecycle["states"]), ("draft", "proposed", "adopted", "retired"))
        self.assertEqual(
            lifecycle["permitted_transitions"],
            [["draft", "proposed"], ["draft", "retired"], ["proposed", "draft"], ["proposed", "adopted"], ["proposed", "retired"], ["adopted", "retired"], ["retired", "draft"]],
        )
        self.assertEqual(set(lifecycle["assignments"]), set(self.registry["components"]["entries"]))

    def test_operational_status_exists_only_for_executable_components(self):
        for component in self.registry["components"]["entries"].values():
            executable = "executable" in component["classification"]["capabilities"]
            self.assertEqual("operational_status" in component, executable)

    def test_component_record_references_are_unique_and_resolve(self):
        registry.validate_stage2_registry(self.registry, root=ROOT)
        for component in self.registry["components"]["entries"].values():
            for values in component["record_refs"].values():
                self.assertEqual(len(values), len(set(values)))

    def test_duplicate_record_reference_fails_closed(self):
        altered = copy.deepcopy(self.registry)
        refs = altered["components"]["entries"]["COMPONENT-REGISTRY"]["record_refs"]["relationships"]
        refs.append(refs[0])
        with self.assertRaisesRegex(registry.RegistryError, "duplicate"):
            registry.validate_stage2_registry(altered, root=ROOT)

    def test_relationships_have_only_approved_types_and_known_components(self):
        allowed = {"implemented_by", "validated_by", "verified_by", "consumes", "supersedes"}
        components = self.registry["components"]["entries"]
        for relationship in self.registry["relationships"]["entries"].values():
            self.assertIn(relationship["relationship_type"], allowed)
            self.assertIn(relationship["from"]["id"], components)
            self.assertIn(relationship["to"]["id"], components)

    def test_agent_and_bot_registry_is_one_retired_predecessor(self):
        components = self.registry["components"]["entries"]
        self.assertEqual(sum(c["classification"]["component_class"] == "agent" for c in components.values()), 1)
        self.assertEqual(sum(c["classification"]["component_class"] == "bot" for c in components.values()), 6)
        self.assertEqual(
            components["agent_registry"]["canonical_source"]["locator"]["value"],
            "framework/archive/authorities/AGENT_BOT_REGISTRY.md",
        )
        self.assertEqual(self.registry["component_lifecycles"]["assignments"]["agent_registry"]["current_state"], "retired")
        self.assertNotIn("agent_registry", self.registry["routing"]["components"])

    def test_proposal_is_registered_and_adopted(self):
        identity = "component_registry_stage2_design_proposal"
        component = self.registry["components"]["entries"][identity]
        self.assertEqual(component["classification"]["roles"], ["proposal"])
        self.assertEqual(component["canonical_source"]["locator"]["value"], "framework/proposals/component-registry-stage2-design.md")
        self.assertEqual(self.registry["component_lifecycles"]["assignments"][identity]["current_state"], "adopted")

    def test_routing_is_compact_and_synthesizes_exact_closure(self):
        for record in self.registry["routing"]["components"].values():
            self.assertNotIn("path", record)
            self.assertNotIn("sha256", record)
        self.assertEqual(registry.route_counts(self.route), {
            "documents": 84, "governing_documents": 83, "capabilities": 19,
            "profiles": 8, "required_modules": 3, "generated_path_exclusions": 9,
        })

    def test_repository_coverage_is_exact_for_current_path_universe(self):
        coverage = self.registry["repository_coverage"]
        self.assertEqual(coverage["uncovered_count"], 0)
        self.assertEqual(coverage["multiply_treated_count"], 0)
        self.assertEqual(set(coverage["entries"]), set(registry._tracked_and_candidate_paths(ROOT)))

    def test_repository_tmp_is_categorical_not_component(self):
        scope = self.registry["directory_scopes"]["entries"]["repository_tmp"]
        self.assertEqual(scope["path_pattern"], ".tmp/")
        self.assertIn("repository_tmp_children", self.registry["supporting_artifact_rules"]["entries"])

    def test_proposed_routing_view_has_no_status_or_receipt_claim(self):
        view = registry.load_component_registry_configuration_routing_view()
        self.assertEqual(view["schema_version"], 2)
        self.assertEqual(view["validation_mode"], "proposed_revision_validation")
        self.assertNotIn("registry_status", view)
        self.assertFalse(view["authoritative"])
        self.assertFalse(view["executable"])
        self.assertFalse(view["activation_receipt_consulted"])
        self.assertFalse(view["predecessor_route_consulted"])
        self.assertFalse(view["authority_effective"])
        self.assertFalse(view["source_revision_authorized"])
        self.assertFalse(view["source_bytes_current"])
        self.assertFalse(view["canonical_history_confirmed"])
        self.assertFalse(view["receipt_trusted"])
        self.assertEqual(view["runtime_live"], "not_checked")
        self.assertFalse(view["registry_component_executable"])

    def test_proposed_view_rejects_executable_selection(self):
        view = registry.load_component_registry_configuration_routing_view()
        with self.assertRaises(registry.RegistryError):
            registry.require_executable_routing_selection(view)

    def test_component_type_is_optional_but_never_null(self):
        for identity in (
            "task_handoff",
            "project_configuration",
            "progress_config",
            "context_routes_source",
        ):
            self.assertNotIn(
                "component_type",
                self.registry["components"]["entries"][identity]["classification"],
            )
        altered = copy.deepcopy(self.registry)
        altered["components"]["entries"]["task_handoff"]["classification"][
            "component_type"
        ] = None
        with self.assertRaisesRegex(registry.RegistryError, "optional component type"):
            registry.validate_stage2_registry(
                altered,
                root=ROOT,
                verify_repository_coverage=False,
                verify_source_bindings=False,
                verify_migration_residuals=False,
            )

    def test_schema_rejects_unknown_top_level_field(self):
        altered = copy.deepcopy(self.registry)
        altered["component_families"] = {}
        schema = load_json(SCHEMA_PATH)
        with self.assertRaises(registry.RegistryError):
            registry._validate_against_schema(altered, schema, schema)

    def test_stable_id_residuals_are_bound_to_exact_typed_occurrences(self):
        altered = copy.deepcopy(self.registry)
        migration = next(
            value
            for value in altered["migrations_and_aliases"]["entries"].values()
            if value.get("kind") == "stable_id_migration"
        )
        migration["allowed_residual_occurrences"].append({
            "path": "invented/current-reference.md",
            "locator": {
                "kind": "text_line",
                "line_number": 1,
                "line_sha256": "0" * 64,
                "occurrence_index": 1,
            },
        })
        with self.assertRaisesRegex(registry.RegistryError, "exact typed locators"):
            registry.validate_stage2_registry(
                altered,
                root=ROOT,
                verify_repository_coverage=False,
                verify_source_bindings=False,
            )


class ComponentRegistryV4AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def test_semantic_minimal_registry_is_accepted(self):
        result = registry.validate_v4_registry(self.registry, root=ROOT)
        self.assertTrue(result["valid"])
        self.assertEqual(result["registry_revision"], 6)
        self.assertEqual(result["codeowners"]["problems"], 0)

    def test_removed_stage_namespaces_do_not_reappear(self):
        removed = {
            "validation", "authority_digest_model", "component_lifecycles",
            "component_authorities", "migrations_and_aliases",
            "provenance_events", "repository_coverage", "supporting_artifact_rules",
        }
        self.assertTrue(removed.isdisjoint(self.registry))
        self.assertIn("registration_exemptions", self.registry)

    def test_registration_exemptions_are_categorical_not_components(self):
        components = self.registry["components"]["entries"]
        exemptions = self.registry["registration_exemptions"]["entries"]
        self.assertEqual(
            set(exemptions),
            {"repository_tmp_children", "project_console_generated_data", "maintained_root_files"},
        )
        self.assertTrue(set(exemptions).isdisjoint(components))

    def test_historical_stage3_helper_is_not_an_active_supporting_artifact(self):
        artifacts = self.registry["components"]["entries"]["component_registry_tool"].get(
            "supporting_artifacts", []
        )
        self.assertNotIn("scripts/apply_component_registry_stage3_migration.py", artifacts)
        self.assertTrue((ROOT / "scripts/apply_component_registry_stage3_migration.py").is_file())
