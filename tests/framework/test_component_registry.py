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
SCHEMA_PATH = ROOT / "framework" / "component-registry.schema.json"
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


class ComponentRegistryStage3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_json(REGISTRY_PATH)
        self.route = registry._stage2_route_snapshot(self.registry)

    def test_stage3_registry_validates_as_adopted_configuration(self):
        result = registry.validate_stage3_registry(self.registry, root=ROOT)
        self.assertTrue(result["valid"])
        self.assertEqual(result["validation_mode"], "adopted_configuration_validation")
        self.assertFalse(result["authoritative"])
        self.assertFalse(result["executable"])
        self.assertFalse(result["live_authority"])

    def test_stage3_top_level_is_closed_and_has_no_family_construct(self):
        expected = {
            "$schema", "schema_version", "registry_id", "registry_revision",
            "validation", "authority_digest_model", "terminology",
            "implementation_enums",
            "directory_scopes", "components", "component_lifecycles",
            "component_authorities", "relationships", "migrations_and_aliases",
            "provenance_events", "routing", "registration_exemptions",
            "repository_coverage",
        }
        self.assertEqual(set(self.registry), expected)
        self.assertFalse(any("famil" in key.lower() for key in self.registry))

    def test_authority_digest_model_is_exact_and_schema_closed(self):
        model = self.registry["authority_digest_model"]
        self.assertEqual(
            model,
            registry._expected_stage2_authority_digest_model(4),
        )
        schema = load_json(SCHEMA_PATH)
        registry._validate_against_schema(
            model,
            schema["$defs"]["authorityDigestModel"],
            schema,
        )
        altered = copy.deepcopy(model)
        altered["uncontrolled_normalization"] = True
        with self.assertRaises(registry.RegistryError):
            registry._validate_against_schema(
                altered,
                schema["$defs"]["authorityDigestModel"],
                schema,
            )

    def test_only_exact_failed_generation2_receipt_may_retain_duplicates(self):
        duplicated = [
            {"context": "ARRP Validation", "app_id": 15368},
            {"context": "ARRP Validation", "app_id": 15368},
            {"context": "CodeQL", "app_id": 57789},
            {"context": "CodeQL", "app_id": 57789},
        ]
        readback = {
            "generation": 2,
            "authority_sha256": (
                registry.STAGE2_GENERATION2_FAILED_RECEIPT_AUTHORITY_SHA256
            ),
            "original_adoption_evidence": {
                "required_checks": copy.deepcopy(duplicated),
            },
            "correction_evidence": {
                "required_checks": copy.deepcopy(duplicated),
            },
        }
        registry._validate_stage2_authority_check_identities(readback)
        current = copy.deepcopy(readback)
        current["generation"] = 3
        with self.assertRaisesRegex(registry.RegistryError, "duplicated"):
            registry._validate_stage2_authority_check_identities(current)
        different = copy.deepcopy(readback)
        different["authority_sha256"] = "f" * 64
        with self.assertRaisesRegex(registry.RegistryError, "duplicated"):
            registry._validate_stage2_authority_check_identities(different)

    def test_authority_digest_has_fixed_cross_implementation_vector(self):
        vector = {
            "authority_digest_model": (
                registry._expected_stage2_authority_digest_model(1)
            ),
            "validation": {"repository_base_revision": "b" * 40},
            "components": {
                "entries": {
                    "alpha": {
                        "canonical_source": {
                            "source_binding": {
                                "binding_basis": "content_digest",
                                "sha256": "a" * 64,
                            }
                        },
                        "label": "café",
                    }
                }
            },
        }
        self.assertEqual(
            registry._stage2_authority_digest(vector),
            "274bddfdab278ac633fe67f27ec3d445e58b887904c07404aa91f1223ec9e07a",
        )

    def test_registry_json_parser_rejects_duplicate_keys_at_any_depth(self):
        with self.assertRaisesRegex(registry.RegistryError, "duplicate field"):
            registry._parse_closed_json_object(
                '{"outer":{"sha256":"' + "a" * 64
                + '","sha256":"' + "b" * 64 + '"}}',
                "duplicate fixture",
            )

    def test_authority_digest_normalizes_every_currentness_location_only(self):
        expected = registry._stage2_authority_digest(self.registry)
        altered = copy.deepcopy(self.registry)
        altered["validation"]["repository_base_revision"] = "f" * 40
        self.assertEqual(registry._stage2_authority_digest(altered), expected)

        content_bound_ids = []
        for component_id, component in self.registry["components"]["entries"].items():
            binding = component["canonical_source"]["source_binding"]
            if binding["binding_basis"] != "content_digest":
                continue
            content_bound_ids.append(component_id)
            altered = copy.deepcopy(self.registry)
            digest = altered["components"]["entries"][component_id][
                "canonical_source"
            ]["source_binding"]["sha256"]
            altered["components"]["entries"][component_id][
                "canonical_source"
            ]["source_binding"]["sha256"] = (
                ("0" if digest[0] != "0" else "1") + digest[1:]
            )
            self.assertEqual(
                registry._stage2_authority_digest(altered),
                expected,
                component_id,
            )
        self.assertEqual(len(content_bound_ids), 101)

    def test_authority_digest_is_sensitive_to_all_other_change_classes(self):
        expected = registry._stage2_authority_digest(self.registry)
        mutations = []

        scalar = copy.deepcopy(self.registry)
        scalar["registry_id"] = "DIFFERENT-REGISTRY"
        mutations.append(scalar)

        structural_addition = copy.deepcopy(self.registry)
        structural_addition["unexpected"] = True
        mutations.append(structural_addition)

        structural_removal = copy.deepcopy(self.registry)
        del structural_removal["terminology"]
        mutations.append(structural_removal)

        ordered_array = copy.deepcopy(self.registry)
        ordered_array["terminology"]["order"] = list(
            reversed(ordered_array["terminology"]["order"])
        )
        mutations.append(ordered_array)

        semantic_binding = copy.deepcopy(self.registry)
        semantic_binding["components"]["entries"]["elim"][
            "canonical_source"
        ]["source_binding"]["external_identifier"] += "-changed"
        mutations.append(semantic_binding)

        for altered in mutations:
            self.assertNotEqual(
                registry._stage2_authority_digest(altered),
                expected,
            )

    def test_currentness_only_equivalence_rejects_semantic_or_generation_change(self):
        refreshed = copy.deepcopy(self.registry)
        refreshed["validation"]["repository_base_revision"] = "f" * 40
        first_component = next(
            component
            for component in refreshed["components"]["entries"].values()
            if component["canonical_source"]["source_binding"]["binding_basis"]
            == "content_digest"
        )
        first_component["canonical_source"]["source_binding"]["sha256"] = (
            "e" * 64
        )
        self.assertTrue(
            registry._stage2_currentness_only_equivalent(
                self.registry,
                refreshed,
            )
        )

        semantic = copy.deepcopy(refreshed)
        semantic["registry_id"] = "DIFFERENT-REGISTRY"
        self.assertFalse(
            registry._stage2_currentness_only_equivalent(
                self.registry,
                semantic,
            )
        )

        generation = copy.deepcopy(refreshed)
        generation["authority_digest_model"]["generation"] = 5
        self.assertFalse(
            registry._stage2_currentness_only_equivalent(
                self.registry,
                generation,
            )
        )

    def test_authority_digest_sentinels_are_outside_live_value_domains(self):
        self.assertIsNone(
            registry.SHA256_RE.fullmatch(
                registry.STAGE2_AUTHORITY_CONTENT_DIGEST_SENTINEL
            )
        )
        self.assertIsNone(
            registry.re.fullmatch(
                r"[0-9a-f]{40}",
                registry.STAGE2_AUTHORITY_BASE_REVISION_SENTINEL,
            )
        )

    def test_exact_eight_component_classes_are_defined_and_used(self):
        definitions = self.registry["implementation_enums"]["component_classes"]
        self.assertEqual(tuple(definitions), registry.STAGE2_COMPONENT_CLASSES)
        used = {
            item["classification"]["component_class"]
            for item in self.registry["components"]["entries"].values()
        }
        self.assertTrue(used <= set(registry.STAGE2_COMPONENT_CLASSES))

    def test_exact_stage3_terminology_and_digest(self):
        records = registry._stage3_term_records(self.registry)
        self.assertEqual(len(records), 87)
        self.assertEqual(
            len(self.registry["terminology"]["record_set_sha256"]),
            64,
        )

    def test_enum_definitions_preserve_owner_glossary_decision(self):
        enums = self.registry["implementation_enums"]
        self.assertEqual(
            enums["owner_decision"],
            {
                "decision": "approved_terms_bind_new_stage3_values_legacy_values_remain_explicitly_unbound",
                "terminology_record_count": 87,
                "terminology_record_set_sha256": self.registry["terminology"]["record_set_sha256"],
                "deferred_audit": "component_registry_110_value_operative_use_audit",
            },
        )
        registry._stage3_validate_new_term_bindings(self.registry)

    def test_component_inventory_has_unique_ids_and_canonical_paths(self):
        components = self.registry["components"]["entries"]
        self.assertEqual(len(components), 105)
        paths = [
            registry._stage2_component_path(component)
            for component in components.values()
        ]
        paths = [path for path in paths if path is not None]
        self.assertEqual(len(paths), len(set(paths)))

    def test_seven_stable_id_migrations_are_exact(self):
        components = self.registry["components"]["entries"]
        migrations = self.registry["migrations_and_aliases"]["entries"]
        records = [
            value for value in migrations.values()
            if value["kind"] == "stable_id_migration"
        ]
        self.assertEqual(len(records), 7)
        self.assertEqual(
            {value["source_id"] for value in records},
            {
                "public_premise", "current_audit", "project_profile",
                "maturity_profile", "scoring_quality_rubric",
                "project_console_progress", "project_console_classifications",
            },
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
        registry.validate_stage3_registry(self.registry, root=ROOT)
        for component in self.registry["components"]["entries"].values():
            for values in component["record_refs"].values():
                self.assertEqual(len(values), len(set(values)))

    def test_duplicate_record_reference_fails_closed(self):
        altered = copy.deepcopy(self.registry)
        refs = altered["components"]["entries"]["COMPONENT-REGISTRY"]["record_refs"]["relationships"]
        refs.append(refs[0])
        with self.assertRaisesRegex(registry.RegistryError, "duplicate"):
            registry.validate_stage3_registry(altered, root=ROOT)

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
            "documents": 82, "governing_documents": 81, "capabilities": 19,
            "profiles": 8, "required_modules": 3, "generated_path_exclusions": 9,
        })

    def test_repository_coverage_is_exact_for_current_path_universe(self):
        coverage = self.registry["repository_coverage"]
        self.assertEqual(coverage["uncovered_count"], 0)
        self.assertEqual(coverage["multiply_treated_count"], 0)
        self.assertEqual(set(coverage["entries"]), set(registry._tracked_and_candidate_paths(ROOT)))

    def test_current_path_universe_excludes_unstaged_move_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            (root / "current.txt").write_text("current\n", encoding="utf-8")
            (root / "future.txt").write_text("future\n", encoding="utf-8")
            with mock.patch.object(
                registry,
                "_git_output",
                return_value="current.txt\nremoved-source.txt\nfuture.txt\n",
            ):
                self.assertEqual(
                    registry._tracked_and_candidate_paths(root),
                    ["current.txt", "future.txt"],
                )

    def test_repository_tmp_is_categorical_not_component(self):
        scope = self.registry["directory_scopes"]["entries"]["repository_tmp"]
        self.assertEqual(scope["path_pattern"], ".tmp/")
        self.assertIn("repository_tmp_children", self.registry["registration_exemptions"]["entries"])

    def test_codeowners_is_exact_generated_nonauthoritative_configuration(self):
        result = registry.stage2_codeowners_projection(self.registry, root=ROOT)
        self.assertTrue(result["available"])
        self.assertTrue(result["complete"])
        self.assertFalse(result["authoritative"])
        self.assertEqual(result["problems"], [])
        self.assertEqual(
            result["generated_text"],
            (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8"),
        )
        registry_record = next(
            record for record in result["records"]
            if record["assignment_id"] == "component:COMPONENT-REGISTRY"
        )
        self.assertEqual(registry_record["declared_mode"], "none")
        self.assertEqual(registry_record["effective_mode"], "none")
        self.assertEqual(registry_record["owners"], [])
        self.assertIsNone(registry_record["generated_line"])

    def test_codeowners_direct_inherit_and_none_are_closed(self):
        result = registry.stage2_codeowners_projection(
            self.registry,
            root=ROOT,
            compare_current=False,
        )
        records = {record["assignment_id"]: record for record in result["records"]}
        self.assertEqual(records["scope:tests"]["effective_mode"], "direct")
        self.assertEqual(records["scope:tests"]["owners"], ["@Thorncrag"])
        self.assertEqual(
            records["scope:test_fixtures"]["declared_mode"],
            "inherit",
        )
        self.assertEqual(records["scope:test_fixtures"]["effective_mode"], "direct")
        self.assertEqual(
            records["scope:test_fixtures"]["inherited_from"],
            "scope:tests",
        )
        self.assertEqual(
            records["scope:repository_root"]["effective_mode"],
            "none",
        )

    def test_codeowners_none_emits_ownerless_override_only_when_needed(self):
        altered = copy.deepcopy(self.registry)
        altered["directory_scopes"]["entries"]["framework"][
            "repository_controls"
        ] = {"github_codeowners": {"mode": "direct", "owners": ["@Thorncrag"]}}
        result = registry.stage2_codeowners_projection(
            altered,
            root=ROOT,
            compare_current=False,
        )
        self.assertIn("/framework/ @Thorncrag\n", result["generated_text"])
        self.assertIn("/framework/component-registry.json\n", result["generated_text"])

    def test_codeowners_rejects_invalid_shape_and_inheritance_cycle(self):
        invalid = copy.deepcopy(self.registry)
        invalid["components"]["entries"]["COMPONENT-REGISTRY"][
            "repository_controls"
        ] = {"github_codeowners": {"mode": "none", "owners": []}}
        with self.assertRaisesRegex(registry.RegistryError, "cannot declare owners"):
            registry.stage2_codeowners_projection(
                invalid,
                root=ROOT,
                compare_current=False,
            )

        cyclic = copy.deepcopy(self.registry)
        scopes = cyclic["directory_scopes"]["entries"]
        scopes["framework"]["ancestor_scope_ids"] = ["framework_project"]
        scopes["framework_project"]["repository_controls"] = {
            "github_codeowners": {"mode": "inherit"}
        }
        scopes["framework_project"]["ancestor_scope_ids"] = ["framework"]
        with self.assertRaisesRegex(registry.RegistryError, "cycles"):
            registry.stage2_codeowners_projection(
                cyclic,
                root=ROOT,
                compare_current=False,
            )

    def test_codeowners_rejects_unknown_missing_and_invalid_direct_values(self):
        schema = load_json(SCHEMA_PATH)
        for setting, message in (
            ({"mode": "automatic"}, "mode is invalid"),
            ({"mode": "direct"}, "not closed"),
            ({"mode": "direct", "owners": ["Thorncrag"]}, "owners are invalid"),
        ):
            with self.subTest(setting=setting):
                altered = copy.deepcopy(self.registry)
                altered["components"]["entries"]["framework_kernel"][
                    "repository_controls"
                ] = {"github_codeowners": setting}
                with self.assertRaises(registry.RegistryError):
                    registry._validate_against_schema(altered, schema, schema)
                with self.assertRaisesRegex(registry.RegistryError, message):
                    registry.stage2_codeowners_projection(
                        altered,
                        root=ROOT,
                        compare_current=False,
                    )

    def test_codeowners_rejects_ambiguous_and_duplicate_patterns(self):
        ambiguous = copy.deepcopy(self.registry)
        ambiguous["directory_scopes"]["entries"]["test_fixtures"][
            "ancestor_scope_ids"
        ] = ["tests", "scripts"]
        with self.assertRaisesRegex(registry.RegistryError, "ambiguous"):
            registry.stage2_codeowners_projection(
                ambiguous,
                root=ROOT,
                compare_current=False,
            )

        duplicate = copy.deepcopy(self.registry)
        duplicate["components"]["entries"]["agent_rules_kernel"][
            "canonical_source"
        ]["locator"]["value"] = "framework/FRAMEWORK.md"
        with self.assertRaisesRegex(registry.RegistryError, "duplicate generated"):
            registry.stage2_codeowners_projection(
                duplicate,
                root=ROOT,
                compare_current=False,
            )

    def test_codeowners_allows_none_but_rejects_direct_for_nonrepository_sources(self):
        nonrepository = copy.deepcopy(self.registry)
        identity = next(
            component_id
            for component_id, component in nonrepository["components"]["entries"].items()
            if component["canonical_source"]["locator"]["kind"]
            != "repository_path"
        )
        nonrepository["components"]["entries"][identity]["repository_controls"] = {
            "github_codeowners": {"mode": "none"}
        }
        registry.stage2_codeowners_projection(
            nonrepository,
            root=ROOT,
            compare_current=False,
        )
        nonrepository["components"]["entries"][identity]["repository_controls"] = {
            "github_codeowners": {"mode": "direct", "owners": ["@Thorncrag"]}
        }
        with self.assertRaisesRegex(registry.RegistryError, "nonrepository"):
            registry.stage2_codeowners_projection(
                nonrepository,
                root=ROOT,
                compare_current=False,
            )

        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            codeowners = temporary_root / ".github" / "CODEOWNERS"
            codeowners.parent.mkdir()
            expected = registry.stage2_codeowners_projection(
                self.registry,
                root=ROOT,
                compare_current=False,
            )["generated_text"]
            codeowners.write_text(
                expected + "/unexplained/ @Thorncrag\n",
                encoding="utf-8",
            )
            result = registry.stage2_codeowners_projection(
                self.registry,
                root=temporary_root,
            )
        self.assertFalse(result["complete"])
        self.assertEqual(
            [problem["code"] for problem in result["problems"]],
            ["checked_in_codeowners_drift"],
        )

    def test_codeowners_generation_is_ordered_idempotent_and_registry_native(self):
        first = registry.stage2_codeowners_projection(
            self.registry,
            root=ROOT,
            compare_current=False,
        )
        second = registry.stage2_codeowners_projection(
            self.registry,
            root=ROOT,
            compare_current=False,
        )
        self.assertEqual(first["generated_text"], second["generated_text"])
        self.assertEqual(first["generated_rows"], second["generated_rows"])
        self.assertNotIn("ownership_and_review", self.registry)
        self.assertEqual(
            registry.generate_codeowners_text(self.registry),
            first["generated_text"],
        )
        generated_lines = [
            line
            for line in first["generated_text"].splitlines()
            if line and not line.startswith("#")
        ]
        self.assertEqual(
            generated_lines,
            [
                " ".join([row["pattern"], *row["owners"]]).rstrip()
                for row in first["generated_rows"]
            ],
        )

    def test_codeowners_migration_preserves_every_covered_path_except_registry(self):
        prior_rows = [
            ("/.github/", ["@Thorncrag"]),
            ("/scripts/", ["@Thorncrag"]),
            ("/tests/", ["@Thorncrag"]),
            ("/AGENTS.md", ["@Thorncrag"]),
            ("/requirements*.txt", ["@Thorncrag"]),
            ("/pyproject.toml", ["@Thorncrag"]),
            ("/package.json", ["@Thorncrag"]),
            ("/package-lock.json", ["@Thorncrag"]),
            ("/**/*.schema.json", ["@Thorncrag"]),
            ("/framework/FRAMEWORK.md", ["@Thorncrag"]),
            ("/framework/AGENT_OPERATING_RULES.md", ["@Thorncrag"]),
            ("/framework/archive/authorities/CONTEXT_ROUTING.md", ["@Thorncrag"]),
            ("/framework/archive/authorities/PROJECT_STRUCTURE.md", ["@Thorncrag"]),
            ("/framework/component-registry.json", ["@Thorncrag"]),
            ("/framework/standards/", ["@Thorncrag"]),
            ("/framework/project/", ["@Thorncrag"]),
            ("/participate/", ["@Thorncrag"]),
            ("/website/", ["@Thorncrag"]),
            ("/framework/project/interfaces/project-console/README.md", ["@Thorncrag"]),
            ("/framework/project/interfaces/project-console/project-console.html", ["@Thorncrag"]),
            ("/framework/project/interfaces/project-console/app.js", ["@Thorncrag"]),
            ("/framework/project/interfaces/project-console/styles.css", ["@Thorncrag"]),
            ("/tests/project-console/", ["@Thorncrag"]),
            ("/framework/logs/", ["@Thorncrag"]),
        ]
        generated = registry.stage2_codeowners_projection(
            self.registry,
            root=ROOT,
            compare_current=False,
        )

        def resolve(path, rows):
            owners = []
            for pattern, candidate in rows:
                if registry._codeowners_pattern_matches(path, pattern):
                    owners = candidate
            return owners

        generated_rows = [
            (row["pattern"], row["owners"])
            for row in generated["generated_rows"]
        ]
        differences = {}
        for path in self.registry["repository_coverage"]["entries"]:
            before = resolve(path, prior_rows)
            after = resolve(path, generated_rows)
            if before != after:
                differences[path] = (before, after)
        self.assertEqual(
            differences,
            {"framework/component-registry.json": (["@Thorncrag"], [])},
        )

    def test_adopted_configuration_view_has_no_live_authority_claim(self):
        view = registry.load_component_registry_configuration_routing_view()
        self.assertEqual(view["schema_version"], 3)
        self.assertEqual(view["validation_mode"], "adopted_configuration_validation")
        self.assertEqual(view["registry_status"], "adopted")
        self.assertFalse(view["authoritative"])
        self.assertFalse(view["executable"])
        self.assertFalse(view["activation_receipt_consulted"])
        self.assertFalse(view["predecessor_route_consulted"])
        self.assertFalse(view["authority_effective"])
        self.assertFalse(view["source_revision_authorized"])
        self.assertTrue(view["source_bytes_current"])
        self.assertFalse(view["canonical_history_confirmed"])
        self.assertFalse(view["receipt_trusted"])
        self.assertEqual(view["runtime_live"], "not_checked")
        self.assertFalse(view["registry_component_executable"])

    def test_configuration_view_rejects_executable_selection(self):
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
            registry.validate_stage3_registry(
                altered,
                root=ROOT,
                verify_repository_coverage=False,
                verify_source_bindings=False,
            )

    def test_schema_rejects_unknown_top_level_field(self):
        altered = copy.deepcopy(self.registry)
        altered["component_families"] = {}
        schema = load_json(SCHEMA_PATH)
        with self.assertRaises(registry.RegistryError):
            registry._validate_against_schema(altered, schema, schema)

    def test_root_scope_has_no_placement_fallback(self):
        altered = copy.deepcopy(self.registry)
        scopes = altered["directory_scopes"]["entries"]
        with self.assertRaisesRegex(registry.RegistryError, "no non-root placement scope"):
            registry.select_stage3_placement_scope("UNREGISTERED.unknown", scopes)

    def test_equal_specificity_scope_tie_fails_closed(self):
        scopes = copy.deepcopy(self.registry["directory_scopes"]["entries"])
        duplicate = copy.deepcopy(scopes["framework"])
        duplicate["scope_id"] = "framework_duplicate"
        scopes["framework_duplicate"] = duplicate
        with self.assertRaisesRegex(registry.RegistryError, "multiple equally specific"):
            registry.select_stage3_placement_scope("framework/example.txt", scopes)

    def test_source_checker_execution_controls_are_exact(self):
        registry._validate_stage3_execution_controls(self.registry)
        altered = copy.deepcopy(self.registry)
        altered["components"]["entries"]["source-checker-bot"][
            "execution_controls"
        ]["prohibited_purposes"].remove("console_currentness")
        with self.assertRaisesRegex(registry.RegistryError, "Source Checker"):
            registry._validate_stage3_execution_controls(altered)

    def test_registry_modification_authority_is_exactly_contract_bound(self):
        registry._validate_stage3_authority_binding(self.registry)
        altered = copy.deepcopy(self.registry)
        altered["component_authorities"]["registry_modification_control"][
            "active_mode"
        ] = "owner_direct"
        with self.assertRaisesRegex(registry.RegistryError, "modification control"):
            registry._validate_stage3_authority_binding(altered)
