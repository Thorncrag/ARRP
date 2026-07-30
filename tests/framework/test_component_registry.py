import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

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
    ROOT / "framework" / "project" / "automation" / "context-routes.json"
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class ComponentRegistryCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate = load_json(REGISTRY_PATH)
        self.schema = load_json(SCHEMA_PATH)
        self.route = load_json(ROUTE_PATH)

    def _build_refresh_fixture(
        self,
        root: Path,
    ) -> tuple[Path, Path, dict[str, object]]:
        candidate = copy.deepcopy(self.candidate)
        route = registry._routing_snapshot(candidate)
        candidate_path = root / "framework" / "component-registry.json"
        route_path = (
            root
            / "framework"
            / "project"
            / "automation"
            / "context-routes.json"
        )
        source_paths = {
            spec["path"] for spec in route["documents"].values()
        }
        source_paths.update(
            entry["canonical_path"]
            for entry in candidate["operational_documents"]["entries"].values()
            if entry["digest_policy"] == "pinned"
        )
        for relative in sorted(source_paths):
            source = ROOT / relative
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        for identity, spec in route["documents"].items():
            if spec["hash_policy"] != "pinned":
                continue
            digest = registry._sha256(root / spec["path"])
            spec["sha256"] = digest
            candidate["context_routing"]["documents"][identity][
                "sha256"
            ] = digest
        for entry in candidate["operational_documents"]["entries"].values():
            if entry["digest_policy"] == "pinned":
                entry["sha256"] = registry._sha256(
                    root / entry["canonical_path"]
                )

        route_path.parent.mkdir(parents=True, exist_ok=True)
        route_path.write_text(
            json.dumps(route, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        route_digest = registry._sha256(route_path)
        candidate["context_routing"]["source_import"]["sha256"] = (
            route_digest
        )
        candidate["context_routing"]["expected_counts"] = (
            registry.route_counts(route)
        )
        candidate["source_baseline"]["route_source"]["sha256"] = route_digest
        candidate["source_baseline"]["working_tree_binding"]["sha256"] = (
            registry._route_source_binding(
                candidate["source_baseline"]["repository_revision"],
                route,
            )
        )
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        candidate_path.write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        registry.load_validated_registry(candidate_path, root=root)
        return candidate_path, route_path, route

    @staticmethod
    def _introduce_fixture_route_hash_drift(
        root: Path,
        route_path: Path,
        route: dict[str, object],
        document_id: str = "public_premise",
    ) -> None:
        source = root / route["documents"][document_id]["path"]
        source.write_text(
            source.read_text(encoding="utf-8")
            + "\n<!-- candidate refresh fixture -->\n",
            encoding="utf-8",
        )
        route["documents"][document_id]["sha256"] = registry._sha256(source)
        route_path.write_text(
            json.dumps(route, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_live_candidate_validates_and_preserves_route_parity(self):
        candidate, route = registry.load_validated_registry()
        self.assertEqual(candidate["status"], "candidate")
        self.assertFalse(candidate["context_routing"]["authoritative"])
        self.assertEqual(
            registry.route_counts(route),
            {
                "documents": 88,
                "governing_documents": 87,
                "capabilities": 19,
                "profiles": 8,
                "required_modules": 3,
                "generated_path_exclusions": 9,
            },
        )
        parity = registry.parity_report(candidate, route)
        self.assertTrue(parity["valid"])
        self.assertEqual(parity["differences"], [])
        self.assertTrue(parity["document_ids_equal"])
        self.assertTrue(parity["profile_ids_equal"])
        self.assertTrue(parity["capability_ids_equal"])

    def test_routing_rule_catalog_definitions_are_exact_and_closed(self):
        routing = self.candidate["context_routing"]
        self.assertEqual(routing["schema_version"], 2)
        self.assertEqual(routing["rule_catalog_version"], 1)
        self.assertEqual(
            tuple(registry.ROUTING_RULE_IDS),
            registry.ROUTING_RULE_MAPS,
        )
        expected_ids = {
            rule_id
            for map_name in registry.ROUTING_RULE_MAPS
            for rule_id in registry.ROUTING_RULE_IDS[map_name]
        }
        actual_ids = {
            rule_id
            for map_name in registry.ROUTING_RULE_MAPS
            for rule_id in routing[map_name]
        }
        self.assertEqual(len(expected_ids), 64)
        self.assertEqual(actual_ids, expected_ids)
        self.assertEqual(
            set(registry.ROUTING_RULE_DEFINITION_VALIDATORS),
            expected_ids,
        )
        registry._validate_routing_rule_catalog(self.candidate)
        for map_name in registry.ROUTING_RULE_MAPS:
            for rule_id, entry in routing[map_name].items():
                with self.subTest(rule_id=rule_id):
                    dispatched = registry.validate_routing_rule_definition(
                        rule_id,
                        entry,
                    )
                    self.assertEqual(dispatched["rule_id"], rule_id)
                    self.assertEqual(
                        dispatched["predicate_type"],
                        rule_id,
                    )

    def test_routing_catalog_structure_and_identity_fail_closed(self):
        cases = []

        unknown_map = copy.deepcopy(self.candidate)
        unknown_map["context_routing"]["unregistered_rules"] = {}
        cases.append(("unknown fields", unknown_map))

        missing_id = copy.deepcopy(self.candidate)
        missing_id["context_routing"]["invariants"].pop(
            "ctxr.inv.router_preserves_source_authority"
        )
        cases.append(("rule identities differ", missing_id))

        duplicate_id = copy.deepcopy(self.candidate)
        duplicate_id["context_routing"]["invariants"][
            "ctxr.inv.required_floor_is_minimum"
        ]["rule_id"] = "ctxr.inv.router_preserves_source_authority"
        cases.append(("duplicate IDs", duplicate_id))

        unsupported_version = copy.deepcopy(self.candidate)
        unsupported_version["context_routing"]["invariants"][
            "ctxr.inv.router_preserves_source_authority"
        ]["rule_version"] = 2
        cases.append(("unsupported rule_version", unsupported_version))

        unsupported_status = copy.deepcopy(self.candidate)
        unsupported_status["context_routing"]["invariants"][
            "ctxr.inv.router_preserves_source_authority"
        ]["status"] = "retired"
        cases.append(("unsupported status", unsupported_status))

        unknown_predicate = copy.deepcopy(self.candidate)
        unknown_predicate["context_routing"]["invariants"][
            "ctxr.inv.router_preserves_source_authority"
        ]["predicate_type"] = "ctxr.inv.unregistered"
        cases.append(("predicate_type", unknown_predicate))

        invalid_provenance = copy.deepcopy(self.candidate)
        invalid_provenance["context_routing"]["invariants"][
            "ctxr.inv.router_preserves_source_authority"
        ]["source_provenance"].pop("clause_key")
        cases.append(("source_provenance fields differ", invalid_provenance))

        missing_verification = copy.deepcopy(self.candidate)
        missing_verification["context_routing"]["invariants"][
            "ctxr.inv.router_preserves_source_authority"
        ]["verification_ids"] = []
        cases.append(("verification_ids", missing_verification))

        invalid_failure = copy.deepcopy(self.candidate)
        invalid_failure["context_routing"]["failure_rules"][
            "ctxr.fail.dependency_cycle"
        ]["failure_code"] = "CTXR_UNREGISTERED"
        cases.append(("invalid failure_code", invalid_failure))

        for expected_error, altered in cases:
            with self.subTest(expected_error=expected_error):
                with self.assertRaises(registry.RegistryError) as caught:
                    registry._validate_routing_rule_catalog(altered)
                self.assertIn(expected_error, str(caught.exception))

    def test_every_routing_rule_definition_rejects_unregistered_parameters(self):
        """Definition shape is closed; this is not semantic execution proof."""
        routing = self.candidate["context_routing"]
        failures = {}
        for map_name in registry.ROUTING_RULE_MAPS:
            for rule_id, entry in routing[map_name].items():
                altered = copy.deepcopy(entry)
                altered["parameters"]["unregistered_parameter"] = True
                try:
                    registry.validate_routing_rule_definition(rule_id, altered)
                except registry.RegistryError as exc:
                    failures[rule_id] = str(exc)
                else:  # pragma: no cover - fail-closed invariant
                    self.fail(f"{rule_id} accepted an unregistered parameter")
        self.assertEqual(len(failures), 64)
        for rule_id, error in failures.items():
            self.assertIn(rule_id, error)
            self.assertIn("invalid parameters", error)

    def test_routing_definition_validator_refuses_unknown_predicate_type(self):
        with self.assertRaisesRegex(
            registry.RegistryError,
            "unknown predicate_type",
        ):
            registry.validate_routing_rule_definition(
                "ctxr.inv.router_preserves_source_authority",
                {
                    "predicate_type": "ctxr.inv.unregistered_predicate",
                    "parameters": {},
                },
            )

    def test_every_rule_definition_has_its_declared_verification_id(self):
        """Declared IDs are source bindings, not 64-rule semantic closure."""
        routing = self.candidate["context_routing"]
        for map_name in registry.ROUTING_RULE_MAPS:
            for rule_id, entry in routing[map_name].items():
                with self.subTest(rule_id=rule_id):
                    self.assertEqual(
                        entry["verification_ids"],
                        [f"test.{rule_id}"],
                    )
                    altered = copy.deepcopy(self.candidate)
                    altered["context_routing"][map_name][rule_id][
                        "verification_ids"
                    ] = []
                    with self.assertRaises(
                        registry.RegistryError
                    ) as caught:
                        registry._validate_routing_rule_catalog(altered)
                    self.assertIn(rule_id, str(caught.exception))
                    self.assertIn(
                        "verification_ids",
                        str(caught.exception),
                    )

    def test_routing_rule_renderer_uses_only_typed_predicates_and_parameters(self):
        routing = self.candidate["context_routing"]
        entry = copy.deepcopy(
            routing["selection"]["ctxr.sel.required_floor_order"]
        )
        entry["source_provenance"][
            "source_heading"
        ] = "PRIVATE NARRATIVE SENTINEL"
        rendered = registry.render_context_routing_rule(
            "ctxr.sel.required_floor_order",
            entry,
        )
        self.assertEqual(
            set(rendered),
            {
                "rule_id",
                "predicate_type",
                "parameters",
                "label",
                "rendered_text",
            },
        )
        self.assertIn("Required Floor Order", rendered["rendered_text"])
        self.assertIn("framework kernel", rendered["rendered_text"])
        self.assertNotIn(
            "PRIVATE NARRATIVE SENTINEL",
            rendered["rendered_text"],
        )

        document = registry.render_routing_rules(self.candidate)
        registry_digest = hashlib.sha256(
            registry.canonical_json(self.candidate).encode("utf-8")
        ).hexdigest()
        self.assertIn(
            f"Registry revision: `{self.candidate['registry_revision']}`",
            document,
        )
        self.assertIn(f"Registry SHA-256: `{registry_digest}`", document)
        self.assertEqual(document.count("- Predicate type:"), 64)

    def test_every_tracked_or_candidate_path_has_one_owning_scope(self):
        candidate, _route = registry.load_validated_registry()
        paths = registry._tracked_and_candidate_paths(ROOT)
        result = registry.classify_repository_paths(candidate, paths)
        self.assertTrue(result["complete"])
        self.assertEqual(result["path_count"], len(paths))
        self.assertEqual(
            len({item["path"] for item in result["items"]}),
            len(paths),
        )
        self.assertTrue(
            all(item["owning_scope_id"] for item in result["items"])
        )
        registry_item = next(
            item
            for item in result["items"]
            if item["path"] == "framework/component-registry.json"
        )
        self.assertEqual(
            registry_item["owning_scope_id"],
            "component_registry_file",
        )

    def test_scope_selection_fails_for_zero_or_tied_owners(self):
        candidate, _route = registry.load_validated_registry()
        scopes = copy.deepcopy(candidate["directory_scopes"]["entries"])
        scopes.pop("repository_root")
        with self.assertRaisesRegex(registry.RegistryError, "no owning"):
            registry.select_owning_scope("README.md", scopes)

        scopes = copy.deepcopy(candidate["directory_scopes"]["entries"])
        duplicate = copy.deepcopy(scopes["component_registry_file"])
        duplicate["scope_id"] = "component_registry_file_duplicate"
        scopes["component_registry_file_duplicate"] = duplicate
        with self.assertRaisesRegex(registry.RegistryError, "equally specific"):
            registry.select_owning_scope(
                "framework/component-registry.json",
                scopes,
            )

    def test_unregistered_nested_directory_does_not_fall_back_to_root(self):
        candidate, _route = registry.load_validated_registry()
        with self.assertRaisesRegex(
            registry.RegistryError,
            "no registered directory scope",
        ):
            registry.select_owning_scope(
                "unregistered-directory/file.md",
                candidate["directory_scopes"]["entries"],
            )

    def test_selected_scope_requires_every_registered_ancestor(self):
        candidate, _route = registry.load_validated_registry()
        scopes = copy.deepcopy(candidate["directory_scopes"]["entries"])
        scopes["component_registry_file"]["ancestor_scope_ids"].append(
            "github_admin"
        )
        with self.assertRaisesRegex(registry.RegistryError, "violates ancestor"):
            registry.select_owning_scope(
                "framework/component-registry.json",
                scopes,
            )

    def test_parameterized_scope_tokens_and_bindings_are_exact(self):
        candidate, route = registry.load_validated_registry()
        scopes = candidate["directory_scopes"]["entries"]
        for identity in ("area", "area_issues", "area_research", "area_evidence"):
            with self.subTest(identity=identity):
                self.assertNotIn("{{", scopes[identity]["path_pattern"])
                self.assertEqual(
                    set(scopes[identity]["parameter_bindings"]),
                    {"area"},
                )
        self.assertEqual(
            registry.select_owning_scope(
                "areas/APPT/issues/APPT-001.md",
                scopes,
            ),
            "area_issues",
        )

        altered = copy.deepcopy(candidate)
        altered["directory_scopes"]["entries"]["area_issues"][
            "path_pattern"
        ] = "areas/{{area}}/issues/"
        with self.assertRaisesRegex(
            registry.RegistryError,
            "invalid path parameter form",
        ):
            registry._validate_stage1_semantics(altered, route)

    def test_operational_documents_cover_every_routed_identity(self):
        candidate, route = registry.load_validated_registry()
        documents = candidate["operational_documents"]["entries"]
        self.assertEqual(set(route["documents"]) - set(documents), set())
        self.assertIn("COMPONENT-REGISTRY", documents)
        self.assertIn("component_registry_schema", documents)
        self.assertIn("component_registry_tool", documents)
        self.assertIn("component_registry_tests", documents)
        for identity, route_entry in route["documents"].items():
            with self.subTest(identity=identity):
                entry = documents[identity]
                self.assertEqual(entry["document_id"], identity)
                self.assertEqual(
                    entry["canonical_path"],
                    route_entry["path"],
                )
                self.assertEqual(
                    entry["dependencies"],
                    route_entry.get("requires", []),
                )
        self.assertEqual(
            documents["current_audit"]["authority_role"],
            "runtime_checkpoint",
        )

    def test_operational_document_paths_and_console_routes_are_unique(self):
        candidate, route = registry.load_validated_registry()
        altered = copy.deepcopy(candidate)
        copied = copy.deepcopy(
            altered["operational_documents"]["entries"]["framework_kernel"]
        )
        copied["document_id"] = "framework_kernel_copy"
        copied["console_route"] = (
            "operations:component-registry:documents"
            "?document=framework_kernel_copy"
        )
        altered["operational_documents"]["entries"][
            "framework_kernel_copy"
        ] = copied
        with self.assertRaisesRegex(
            registry.RegistryError,
            "duplicate canonical path",
        ):
            registry._validate_stage1_semantics(altered, route)

    def test_agent_authored_flag_cannot_activate_the_registry(self):
        candidate, route = registry.load_validated_registry()
        altered = copy.deepcopy(candidate)
        altered["status"] = "active"
        altered["approval"] = {
            "state": "known",
            "value": {
                "approved": True,
                "source": "agent-authored assertion",
            },
        }
        with self.assertRaisesRegex(
            registry.RegistryError,
            "exact human activation approval envelope",
        ):
            registry._validate_stage1_semantics(altered, route)

        altered["approval"] = {
            "state": "known",
            "value": {
                "approval_type": "stage1_component_registry_activation",
                "approved_by": "@Thorncrag",
                "approval_method": "explicit_recorded_owner_activation",
                "governance_change_id": "GOV-2026-999",
                "implementation_contract_id": "test-only-activation",
                "base_revision": candidate["source_baseline"][
                    "repository_revision"
                ],
                "candidate_registry_sha256": "1" * 64,
                "affected_stable_ids": ["COMPONENT-REGISTRY"],
                "purpose_scope": "Test-only self-authored envelope.",
                "bounded_diff_sha256": "2" * 64,
                "approved_at": "2026-07-29T12:00:00Z",
                "owner_review_reference": (
                    "github-review:Thorncrag/ARRP#999"
                ),
            },
        }
        with self.assertRaisesRegex(
            registry.RegistryError,
            "separately authenticated owner-review readback",
        ):
            registry._validate_stage1_semantics(altered, route)

    def test_required_document_metadata_is_typed_and_nonblank(self):
        candidate, route = registry.load_validated_registry()
        required = {
            "official_reference_name",
            "document_class",
            "revision",
            "current_status",
            "effective_date",
            "approval_date",
            "approval_method",
            "governance_change_id",
            "purpose_scope",
        }
        for identity, entry in candidate["operational_documents"][
            "entries"
        ].items():
            with self.subTest(identity=identity):
                for field in required:
                    registry._typed_value(
                        entry[field],
                        f"{identity} {field}",
                    )

        altered = copy.deepcopy(candidate)
        altered["operational_documents"]["entries"]["public_premise"][
            "purpose_scope"
        ] = {"state": "known", "value": ""}
        with self.assertRaisesRegex(registry.RegistryError, "requires a value"):
            registry._validate_stage1_semantics(altered, route)

    def test_metadata_renderer_emits_the_complete_compact_table(self):
        candidate, _route = registry.load_validated_registry()
        rendered = registry.render_metadata_block(
            candidate,
            "COMPONENT-REGISTRY",
        )
        expected_labels = (
            "Official reference name",
            "Stable document ID",
            "Document class",
            "Revision",
            "Current status",
            "Effective date",
            "Approval date",
            "Approval method",
            "Governance Change ID",
            "Purpose and scope",
            "Component Registry entry",
        )
        self.assertEqual(rendered.count("\n"), 13)
        for label in expected_labels:
            self.assertIn(f"| {label} |", rendered)
        self.assertNotIn("| Digest |", rendered)

    def test_full_route_parity_detects_non_count_semantic_drift(self):
        candidate, route = registry.load_validated_registry()
        altered = copy.deepcopy(candidate)
        profile = altered["context_routing"]["profiles"][
            "candidate_research"
        ]
        profile["max_bytes"] += 1
        report = registry.parity_report(altered, route)
        self.assertFalse(report["valid"])
        self.assertEqual(report["differences"], ["profiles"])

    def test_section_selectors_resolve_exact_headings_within_limits(self):
        registry._validate_section_selectors(self.route, root=ROOT)

        missing = copy.deepcopy(self.route)
        missing["profiles"]["candidate_research"]["sections"][0][
            "heading"
        ] = "## Heading that does not exist"
        with self.assertRaisesRegex(
            registry.RegistryError,
            "selector is invalid",
        ):
            registry._validate_section_selectors(missing, root=ROOT)

        over_limit = copy.deepcopy(self.route)
        over_limit["profiles"]["candidate_research"]["sections"][0][
            "max_bytes"
        ] = 1
        with self.assertRaisesRegex(
            registry.RegistryError,
            "exceeds max_bytes",
        ):
            registry._validate_section_selectors(over_limit, root=ROOT)

    def test_route_result_explains_membership_and_binds_registry(self):
        candidate, route = registry.load_validated_registry()
        result = registry.routed_documents(
            candidate,
            route,
            profile_id="candidate_research",
            capability_ids=[],
        )
        self.assertEqual(
            result["selection_kind"],
            "configuration_validation_packet",
        )
        self.assertFalse(result["executable"])
        self.assertRegex(result["registry_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(result["registry_status"], "candidate")
        self.assertFalse(result["authoritative"])
        for module in result["modules"]:
            self.assertTrue(module["inclusion_reasons"])
            self.assertIn("authority_scope", module)
            self.assertIn("authority_exclusions", module)

    def test_required_cli_surface_is_registered(self):
        parser = registry._parser()
        command_action = next(
            action
            for action in parser._actions
            if getattr(action, "choices", None)
        )
        self.assertTrue(
            registry.REQUIRED_COMMANDS.issubset(set(command_action.choices))
        )

    def test_generated_codeowners_protects_the_bootstrap_core(self):
        candidate, _route = registry.load_validated_registry()
        generated = registry.generate_codeowners_text(candidate)
        self.assertTrue(generated.startswith(registry.CODEOWNERS_HEADER))
        self.assertIn(
            "/framework/component-registry.json @Thorncrag",
            generated,
        )
        for path in registry.PROTECTED_CORE_PATHS:
            matching = [
                entry
                for entry in candidate["ownership_and_review"][
                    "entries"
                ].values()
                if registry._codeowners_pattern_matches(
                    path,
                    entry["path_pattern"],
                )
            ]
            self.assertTrue(matching, path)
            effective = sorted(
                matching,
                key=lambda item: item["precedence"],
            )[-1]
            self.assertIn("@Thorncrag", effective["owners"])

    def test_ownership_cannot_weaken_owner_review(self):
        candidate, route = registry.load_validated_registry()
        altered = copy.deepcopy(candidate)
        entry = next(
            entry
            for entry in altered["ownership_and_review"]["entries"].values()
            if entry["path_pattern"] == "/framework/component-registry.json"
        )
        entry["owners"] = ["@Unapproved"]
        with self.assertRaisesRegex(
            registry.RegistryError,
            "Benjamin owner review",
        ):
            registry._validate_stage1_semantics(altered, route)

    def test_ownership_precedence_must_be_unambiguous(self):
        candidate, route = registry.load_validated_registry()
        altered = copy.deepcopy(candidate)
        entries = list(
            altered["ownership_and_review"]["entries"].values()
        )
        entries[1]["precedence"] = entries[0]["precedence"]
        with self.assertRaisesRegex(
            registry.RegistryError,
            "ambiguous precedence",
        ):
            registry._validate_stage1_semantics(altered, route)

    def test_validated_log_appender_does_not_weaken_definition_review(self):
        candidate, route = registry.load_validated_registry()
        entry = candidate["ownership_and_review"]["entries"][
            "ownership_24_framework_logs"
        ]
        self.assertEqual(entry["ordinary_writer_policy"], "validated_appender")
        self.assertEqual(
            set(entry["protected_change_classes"]),
            registry.VALIDATED_APPENDER_PROTECTIONS,
        )
        self.assertEqual(entry["review_policy"], "owner_review_required")
        self.assertEqual(
            entry["branch_protection"],
            "default_branch_owner_review",
        )
        self.assertIn(
            "/framework/logs/ @Thorncrag",
            registry.generate_codeowners_text(candidate),
        )

        altered = copy.deepcopy(candidate)
        altered["ownership_and_review"]["entries"][
            "ownership_24_framework_logs"
        ]["protected_change_classes"].remove("log_schema")
        with self.assertRaisesRegex(
            registry.RegistryError,
            "incomplete validated-appender boundary",
        ):
            registry._validate_stage1_semantics(altered, route)

    def test_pinned_core_digest_must_match_the_exact_source(self):
        candidate, route = registry.load_validated_registry()
        altered = copy.deepcopy(candidate)
        altered["operational_documents"]["entries"][
            "component_registry_tool"
        ]["sha256"] = "0" * 64
        with self.assertRaisesRegex(
            registry.RegistryError,
            "pinned digest differs",
        ):
            registry._validate_stage1_semantics(altered, route)

    def test_future_tree_applies_registered_longest_alias(self):
        candidate, _route = registry.load_validated_registry()
        console_tests_alias = candidate["aliases_and_migrations"]["entries"][
            "relocate_project_console_tests"
        ]
        console_test_source = (
            f"{console_tests_alias['source_path']}/frontend.test.mjs"
        )
        result = registry.future_tree_manifest(
            candidate,
            [
                "framework/project/interfaces/project-console/app.js",
                console_test_source,
                "research/candidate-source-development/README.md",
                "README.md",
            ],
        )
        by_source = {item["source_path"]: item for item in result["items"]}
        self.assertEqual(
            by_source["framework/project/interfaces/project-console/app.js"]["future_path"],
            "framework/project/interfaces/project-console/app.js",
        )
        self.assertEqual(
            by_source[console_test_source]["future_path"],
            "tests/project-console/frontend.test.mjs",
        )
        self.assertEqual(
            by_source["research/candidate-source-development/README.md"][
                "future_path"
            ],
            "research/candidate-source-development/README.md",
        )
        self.assertEqual(
            by_source["README.md"]["future_path"],
            "README.md",
        )

    def test_scan_exclusions_have_exact_non_authority_bindings(self):
        candidate, route = registry.load_validated_registry()
        exclusions = set(
            candidate["context_routing"]["generated_path_exclusions"]
        )
        bindings = candidate["context_routing"]["scan_exclusion_bindings"]
        self.assertEqual(set(bindings), exclusions)
        for excluded_path, binding in bindings.items():
            with self.subTest(excluded_path=excluded_path):
                self.assertEqual(binding["excluded_path"], excluded_path)
                self.assertEqual(
                    binding["authority_effect"],
                    "scan_exclusion_only_no_authority",
                )
                self.assertEqual(
                    binding["classification_policy"],
                    "deferred_classification_fails_closed",
                )
        altered = copy.deepcopy(candidate)
        altered["context_routing"]["scan_exclusion_bindings"].pop(".tmp")
        with self.assertRaisesRegex(
            registry.RegistryError,
            "exactly cover",
        ):
            registry._validate_stage1_semantics(altered, route)

    def test_future_tree_rejects_colliding_alias_targets(self):
        candidate, _route = registry.load_validated_registry()
        altered = copy.deepcopy(candidate)
        altered["aliases_and_migrations"]["entries"]["collision_a"] = {
            "alias_id": "collision_a",
            "alias_type": "relocation",
            "source_path": "README.md",
            "target_path": "framework/status/collision.md",
            "path_kind": "file",
            "stable_component_id": "collision_a",
            "reference_policy": "rewrite_active",
            "activation_state": "candidate",
            "retirement_condition": "Test-only collision.",
        }
        altered["aliases_and_migrations"]["entries"]["collision_b"] = {
            "alias_id": "collision_b",
            "alias_type": "relocation",
            "source_path": "AGENTS.md",
            "target_path": "framework/status/collision.md",
            "path_kind": "file",
            "stable_component_id": "collision_b",
            "reference_policy": "rewrite_active",
            "activation_state": "candidate",
            "retirement_condition": "Test-only collision.",
        }
        with self.assertRaisesRegex(registry.RegistryError, "collision"):
            registry.future_tree_manifest(
                altered,
                ["README.md", "AGENTS.md"],
            )

    def test_terminology_remains_explicitly_unavailable(self):
        candidate, _route = registry.load_validated_registry()
        result = registry.audit_terminology(candidate)
        self.assertFalse(result["available"])
        self.assertFalse(result["complete"])
        self.assertEqual(
            result["activation_state"],
            "candidate_unpopulated",
        )
        self.assertIn("Implementation Contract", result["reason"])

    def test_repository_reference_classes_are_exact_and_inactive(self):
        candidate, _route = registry.load_validated_registry()
        namespace = candidate["repository_ref_lifecycle"]
        self.assertFalse(namespace["enforced"])
        self.assertEqual(
            set(namespace["entries"]),
            {
                "canonical_default",
                "registered_persistent",
                "change_ephemeral",
                "transaction_ephemeral",
                "fixture_ephemeral",
            },
        )
        for entry in namespace["entries"].values():
            self.assertEqual(
                entry["mutation_activation"],
                "separately_gated",
            )

    def test_unknown_relationship_endpoint_fails_closed(self):
        candidate, route = registry.load_validated_registry()
        altered = copy.deepcopy(candidate)
        altered["component_relationships"][0]["to"] = {
            "kind": "document",
            "id": "invented_document",
        }
        with self.assertRaisesRegex(registry.RegistryError, "unknown to"):
            registry._validate_stage1_semantics(altered, route)

    def test_unknown_representation_source_fails_closed(self):
        candidate, route = registry.load_validated_registry()
        altered = copy.deepcopy(candidate)
        altered["representations"]["entries"]["component_registry_console"][
            "canonical_document_id"
        ] = "invented_document"
        with self.assertRaisesRegex(
            registry.RegistryError,
            "unknown canonical document",
        ):
            registry._validate_stage1_semantics(altered, route)

    def test_project_console_representations_use_approved_entrypoint(self):
        candidate, _route = registry.load_validated_registry()
        representations = candidate["representations"]["entries"]
        canonical_entrypoint = (
            "framework/project/interfaces/project-console/"
            "project-console.html"
        )
        for identity in (
            "component_registry_console",
            "component_registry_console_documents",
            "capacity_specialist",
            "capacity_overview_compact",
        ):
            with self.subTest(identity=identity):
                self.assertEqual(
                    representations[identity]["canonical_path"],
                    canonical_entrypoint,
                )
        self.assertEqual(
            representations["legacy_console_redirect"]["canonical_path"],
            "framework/project/interfaces/project-console/project-console.html",
        )
        serialized = registry.canonical_json(representations)
        self.assertNotIn("project-console/index.html", serialized)

    def test_invalid_alias_target_fails_closed(self):
        candidate, route = registry.load_validated_registry()
        altered = copy.deepcopy(candidate)
        altered["aliases_and_migrations"]["entries"][
            "relocate_project_structure"
        ]["target_path"] = "../outside.md"
        with self.assertRaisesRegex(
            registry.RegistryError,
            "outside the repository authority",
        ):
            registry._validate_stage1_semantics(altered, route)

    def test_deferred_stage2_values_cannot_validate_or_influence_stage1(self):
        candidate, route = registry.load_validated_registry()
        before = registry.classify_repository_paths(
            candidate,
            ["README.md"],
        )
        altered = copy.deepcopy(candidate)
        altered["artifact_classes"]["entries"]["miscellaneous"] = {
            "meaning": "invented"
        }
        altered["artifact_classes"]["complete"] = True
        altered["artifact_classes"]["enforced"] = True
        after = registry.classify_repository_paths(
            altered,
            ["README.md"],
        )
        self.assertEqual(before, after)
        with self.assertRaisesRegex(
            registry.RegistryError,
            "exact deferred",
        ):
            registry._validate_stage1_semantics(altered, route)

    def test_schema_rejects_unknown_top_level_field(self):
        altered = copy.deepcopy(self.candidate)
        altered["invented_namespace"] = {}
        with self.assertRaisesRegex(
            registry.RegistryError,
            "unknown fields",
        ):
            registry._validate_against_schema(
                altered,
                self.schema,
                self.schema,
            )

    def test_all_lifecycle_namespaces_use_exact_deferred_envelope(self):
        for namespace in registry.DEFERRED_NAMESPACES:
            with self.subTest(namespace=namespace):
                self.assertEqual(
                    self.candidate[namespace],
                    registry.DEFERRED_ENVELOPE,
                )

    def test_schema_rejects_permissive_deferred_lifecycle_envelope(self):
        altered = copy.deepcopy(self.candidate)
        altered["artifact_lifecycles"]["enforced"] = True
        altered["artifact_lifecycles"]["entries"]["default"] = {
            "meaning": "inferred"
        }
        with self.assertRaises(registry.RegistryError):
            registry._validate_against_schema(
                altered,
                self.schema,
                self.schema,
            )

    def test_classification_status_is_unavailable_not_empty_or_clean(self):
        candidate, _route = registry.load_validated_registry()
        for namespace in registry.DEFERRED_NAMESPACES:
            self.assertEqual(
                candidate[namespace]["activation_state"],
                "deferred_pending_human_classification",
            )
            self.assertFalse(candidate[namespace]["complete"])
            self.assertFalse(candidate[namespace]["enforced"])
            self.assertEqual(candidate[namespace]["entries"], {})
        self.assertEqual(
            candidate["deferred_namespace_notice"]["display_state"],
            "Classification pending — enforcement not active",
        )

    def test_route_source_rejects_unknown_document_dependency(self):
        altered = copy.deepcopy(self.route)
        altered["documents"]["framework_kernel"]["requires"] = [
            "missing_document"
        ]
        with self.assertRaisesRegex(
            registry.RegistryError,
            "unknown context document",
        ):
            registry.validate_route_source(altered)

    def test_route_source_rejects_dependency_cycle(self):
        altered = copy.deepcopy(self.route)
        altered["documents"]["framework_kernel"]["requires"] = [
            "agent_rules_kernel"
        ]
        with self.assertRaisesRegex(
            registry.RegistryError,
            "dependency cycle",
        ):
            registry.validate_route_source(altered)

    def test_route_source_rejects_unknown_capability_member(self):
        altered = copy.deepcopy(self.route)
        altered["capabilities"]["audit_common"].append("unknown_document")
        with self.assertRaisesRegex(
            registry.RegistryError,
            "unknown identities",
        ):
            registry.validate_route_source(altered)

    def test_route_source_rejects_duplicate_paths(self):
        altered = copy.deepcopy(self.route)
        altered["documents"]["agent_rules_kernel"]["path"] = altered[
            "documents"
        ]["framework_kernel"]["path"]
        with self.assertRaisesRegex(
            registry.RegistryError,
            "duplicate context document path",
        ):
            registry.validate_route_source(altered)

    def test_route_source_requires_exact_ordered_floor(self):
        reversed_floor = copy.deepcopy(self.route)
        reversed_floor["required_modules"] = list(
            reversed(reversed_floor["required_modules"])
        )
        with self.assertRaisesRegex(
            registry.RegistryError,
            "required_modules must be exactly",
        ):
            registry.validate_route_source(reversed_floor)

        substituted = copy.deepcopy(self.route)
        substituted["required_modules"][1] = "agent_rules"
        with self.assertRaisesRegex(
            registry.RegistryError,
            "required_modules must be exactly",
        ):
            registry.validate_route_source(substituted)

    def test_route_source_requires_exact_hash_currentness_classes(self):
        altered = copy.deepcopy(self.route)
        framework = altered["documents"]["framework_kernel"]
        checkpoint = altered["documents"]["current_audit"]
        framework["hash_policy"] = "runtime"
        framework.pop("sha256")
        framework["governing"] = False
        checkpoint["hash_policy"] = "pinned"
        checkpoint["sha256"] = "a" * 64
        with self.assertRaisesRegex(
            registry.RegistryError,
            "sole runtime-hashed",
        ):
            registry.validate_route_source(altered)

        pinned_checkpoint = copy.deepcopy(self.route)
        pinned_checkpoint["documents"]["current_audit"]["sha256"] = "a" * 64
        with self.assertRaisesRegex(
            registry.RegistryError,
            "runtime document current_audit cannot pin",
        ):
            registry.validate_route_source(pinned_checkpoint)

    def test_route_source_excludes_shared_records_except_current_audit(self):
        altered = copy.deepcopy(self.route)
        altered["documents"]["extra_record"] = {
            "path": "framework/records/example.md",
            "sha256": "a" * 64,
            "hash_policy": "pinned",
            "governing": False,
            "requires": [],
        }
        with self.assertRaisesRegex(
            registry.RegistryError,
            "excluded except current_audit",
        ):
            registry.validate_route_source(altered)

    def test_comprehensive_review_definition_is_exact(self):
        disabled = copy.deepcopy(self.route)
        disabled["profiles"]["comprehensive_review"][
            "include_all_governing"
        ] = False
        with self.assertRaisesRegex(
            registry.RegistryError,
            "include_all_governing must be true",
        ):
            registry.validate_route_source(disabled)

        extra = copy.deepcopy(self.route)
        extra["documents"]["nongoverning_extra"] = {
            "path": "framework/example-nongoverning.md",
            "sha256": "a" * 64,
            "hash_policy": "pinned",
            "governing": False,
            "requires": [],
        }
        extra["profiles"]["comprehensive_review"]["modules"] = [
            "nongoverning_extra"
        ]
        with self.assertRaisesRegex(
            registry.RegistryError,
            "membership must be exactly",
        ):
            registry.validate_route_source(extra)

    def test_candidate_and_active_routing_states_cannot_cross(self):
        coherent = {
            ("candidate", "candidate_import", False),
            ("active", "active", True),
        }
        for status in ("candidate", "active"):
            for activation_state in ("candidate_import", "active"):
                for authoritative in (False, True):
                    altered = copy.deepcopy(self.candidate)
                    altered["status"] = status
                    altered["context_routing"][
                        "activation_state"
                    ] = activation_state
                    altered["context_routing"][
                        "authoritative"
                    ] = authoritative
                    combination = (
                        status,
                        activation_state,
                        authoritative,
                    )
                    with self.subTest(combination=combination):
                        if combination in coherent:
                            registry._validate_registry_routing_state(altered)
                        else:
                            with self.assertRaisesRegex(
                                registry.RegistryError,
                                "authority states disagree",
                            ):
                                registry._validate_registry_routing_state(
                                    altered
                                )

    def test_capability_preview_is_not_an_executable_selection(self):
        candidate = self.candidate
        route = registry._routing_snapshot(candidate)
        preview = registry.routed_capability_preview(
            candidate,
            route,
            capability_ids=["github_lifecycle"],
        )
        self.assertEqual(preview["selection_kind"], "capability_preview")
        self.assertFalse(preview["executable"])
        self.assertFalse(preview["authoritative"])
        self.assertIsNone(preview["profile"])
        with self.assertRaisesRegex(
            registry.RegistryError,
            "not an executable",
        ):
            registry.require_executable_routing_selection(preview)

    def test_executable_selection_requires_exactly_one_profile(self):
        candidate = self.candidate
        route = registry._routing_snapshot(candidate)
        with self.assertRaisesRegex(
            registry.RegistryError,
            "requires one nonexecuting",
        ):
            registry.routed_documents(
                candidate,
                route,
                profile_id=None,  # type: ignore[arg-type]
                capability_ids=["github_lifecycle"],
            )
        selected = registry.routed_documents(
            candidate,
            route,
            profile_id="github_sync",
            capability_ids=[],
        )
        with self.assertRaisesRegex(
            registry.RegistryError,
            "not an executable",
        ):
            registry.require_executable_routing_selection(selected)
        with self.assertRaisesRegex(
            registry.RegistryError,
            "not an executable",
        ):
            registry.require_executable_routing_selection(
                selected,
                require_authoritative=False,
            )

    def test_active_routing_requires_bound_readback_and_never_predecessor(self):
        active = copy.deepcopy(self.candidate)
        active["status"] = "active"
        with self.assertRaisesRegex(
            registry.RegistryError,
            "only through fixed path authority",
        ):
            registry.validated_component_registry_routing_view(
                active,
                candidate_source_route=registry._routing_snapshot(active),
            )

    def test_profile_route_is_deterministic_and_uses_only_known_documents(self):
        candidate, route = registry.load_validated_registry()
        first = registry.routed_documents(
            candidate,
            route,
            profile_id="candidate_research",
            capability_ids=[],
        )
        second = registry.routed_documents(
            candidate,
            route,
            profile_id="candidate_research",
            capability_ids=[],
        )
        self.assertEqual(registry.canonical_json(first), registry.canonical_json(second))
        known = set(route["documents"])
        self.assertTrue(first["modules"])
        self.assertTrue(
            all(module["id"] in known for module in first["modules"])
        )
        self.assertFalse(first["authoritative"])

    def test_unknown_route_identity_fails_closed(self):
        candidate, route = registry.load_validated_registry()
        with self.assertRaisesRegex(
            registry.RegistryError,
            "unknown context profile",
        ):
            registry.routed_documents(
                candidate,
                route,
                profile_id="invented_profile",
                capability_ids=[],
            )

    def test_registry_path_outside_repository_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            outside = Path(directory) / "component-registry.json"
            outside.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(
                registry.RegistryError,
                "outside the repository authority",
            ):
                registry.load_validated_registry(outside)

    def test_registry_symlink_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            framework = root / "framework"
            framework.mkdir()
            external = root / "external-registry.json"
            external.write_text("{}", encoding="utf-8")
            linked = framework / "component-registry.json"
            linked.symlink_to(external)
            with self.assertRaisesRegex(
                registry.RegistryError,
                "symlinked path",
            ):
                registry.load_validated_registry(linked, root=root)

    def test_candidate_refresh_updates_only_acknowledged_route_hash_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_path, route_path, route = self._build_refresh_fixture(
                root
            )
            self._introduce_fixture_route_hash_drift(
                root,
                route_path,
                route,
            )
            live_route_bytes = route_path.read_bytes()

            result = registry.refresh_candidate_registry(
                candidate_path,
                root=root,
                acknowledged_document_ids=["public_premise"],
            )

            self.assertEqual(result["status"], "candidate")
            self.assertFalse(result["authoritative"])
            self.assertEqual(
                result["changed_document_ids"],
                ["public_premise"],
            )
            self.assertEqual(route_path.read_bytes(), live_route_bytes)
            refreshed, validated_route = registry.load_validated_registry(
                candidate_path,
                root=root,
            )
            self.assertEqual(refreshed["status"], "candidate")
            self.assertEqual(refreshed["approval"]["state"], "pending")
            self.assertEqual(
                refreshed["context_routing"]["documents"][
                    "public_premise"
                ]["sha256"],
                validated_route["documents"]["public_premise"]["sha256"],
            )
            self.assertEqual(
                refreshed["context_routing"]["source_import"]["sha256"],
                registry._sha256(route_path),
            )
            self.assertEqual(
                refreshed["context_routing"]["expected_counts"],
                registry.route_counts(validated_route),
            )
            self.assertEqual(
                refreshed["source_baseline"]["working_tree_binding"]["sha256"],
                registry._route_source_binding(
                    refreshed["source_baseline"]["repository_revision"],
                    validated_route,
                ),
            )
            for entry in refreshed["operational_documents"][
                "entries"
            ].values():
                if entry["digest_policy"] == "pinned":
                    self.assertEqual(
                        entry["sha256"],
                        registry._sha256(root / entry["canonical_path"]),
                    )
            self.assertEqual(
                list(candidate_path.parent.glob(
                    ".component-registry.json.refresh-*"
                )),
                [],
            )

    def test_candidate_refresh_rejects_unacknowledged_route_hash_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_path, route_path, route = self._build_refresh_fixture(
                root
            )
            self._introduce_fixture_route_hash_drift(
                root,
                route_path,
                route,
            )
            before = candidate_path.read_bytes()

            with self.assertRaisesRegex(
                registry.RegistryError,
                "acknowledgements do not exactly match",
            ):
                registry.refresh_candidate_registry(
                    candidate_path,
                    root=root,
                    acknowledged_document_ids=[],
                )
            self.assertEqual(candidate_path.read_bytes(), before)

    def test_candidate_refresh_rejects_active_status_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_path, _route_path, _route = (
                self._build_refresh_fixture(root)
            )
            candidate = load_json(candidate_path)
            candidate["status"] = "active"
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            before = candidate_path.read_bytes()

            with self.assertRaisesRegex(
                registry.RegistryError,
                "rejects active registry status",
            ):
                registry.refresh_candidate_registry(
                    candidate_path,
                    root=root,
                    acknowledged_document_ids=[],
                )
            self.assertEqual(candidate_path.read_bytes(), before)

    def test_candidate_refresh_rejects_structural_route_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            candidate_path, route_path, route = self._build_refresh_fixture(
                root
            )
            route["profiles"]["candidate_research"]["max_bytes"] += 1
            route_path.write_text(
                json.dumps(route, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            before = candidate_path.read_bytes()

            with self.assertRaisesRegex(
                registry.RegistryError,
                "structural route drift",
            ):
                registry.refresh_candidate_registry(
                    candidate_path,
                    root=root,
                    acknowledged_document_ids=[],
                )
            self.assertEqual(candidate_path.read_bytes(), before)

    def test_source_digest_mismatch_fails_closed_before_route_use(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = copy.deepcopy(self.candidate)
            schema = copy.deepcopy(self.schema)
            route = copy.deepcopy(self.route)
            candidate_path = root / "framework" / "component-registry.json"
            schema_path = (
                root
                / "framework"
                / "standards"
                / "automation"
                / "component-registry.schema.json"
            )
            route_path = (
                root
                / "framework"
                / "project"
                / "automation"
                / "context-routes.json"
            )
            candidate_path.parent.mkdir(parents=True)
            schema_path.parent.mkdir(parents=True)
            route_path.parent.mkdir(parents=True)
            candidate_path.write_text(
                json.dumps(candidate),
                encoding="utf-8",
            )
            schema_path.write_text(
                json.dumps(schema),
                encoding="utf-8",
            )
            route["generated_path_exclusions"].append("new-generated-root")
            route_path.write_text(
                json.dumps(route),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                registry.RegistryError,
                "digest differs",
            ):
                registry.load_validated_registry(
                    candidate_path,
                    root=root,
                )


if __name__ == "__main__":
    unittest.main()
