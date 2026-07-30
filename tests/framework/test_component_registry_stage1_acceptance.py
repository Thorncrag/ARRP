"""Stage 1 Component Registry acceptance tests.

These tests expand the source-design closure matrix without activating the
deferred artifact-class, artifact-family, artifact-lifecycle, terminology, or
repository-reference mutation authorities.  CR identifiers in test names
identify the design requirements for which the test supplies pre-activation
evidence.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unittest
from collections import defaultdict
from pathlib import Path
from unittest import mock

from scripts import component_registry as registry


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "framework" / "component-registry.json"
ROUTING_PREDECESSOR_PATH = ROOT / "framework" / "CONTEXT_ROUTING.md"
ROUTE_PATH = (
    ROOT / "framework" / "project" / "automation" / "context-routes.json"
)
ROUTING_PREDECESSOR_SHA256 = (
    "246a2bc927fa232507ac733192c42f42e469557b3b25cd92d74c111ef6d5e4a7"
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def dependency_closure(
    documents: dict[str, dict[str, object]],
    seeds: list[str],
) -> set[str]:
    """Resolve a small independent closure for routing-output comparison."""

    resolved: set[str] = set()

    def visit(identity: str) -> None:
        if identity in resolved:
            return
        resolved.add(identity)
        for dependency in documents[identity].get("requires", []):
            visit(str(dependency))

    for seed in seeds:
        visit(seed)
    return resolved


class ComponentRegistryStage1AcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate = load_json(REGISTRY_PATH)
        self.route = load_json(ROUTE_PATH)
        self.embedded_route = registry._routing_snapshot(self.candidate)

    def test_cr002_017_018_019_document_identity_metadata_and_links(self):
        """Stable identity, typed metadata, and exact deep links are complete."""

        entries = self.candidate["operational_documents"]["entries"]
        required_typed_fields = {
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
        }
        seen_paths: set[str] = set()
        seen_routes: set[str] = set()
        for identity, entry in entries.items():
            with self.subTest(identity=identity):
                self.assertEqual(entry["document_id"], identity)
                registry._stable_component_id(identity, "document")
                self.assertNotIn(entry["canonical_path"], seen_paths)
                seen_paths.add(entry["canonical_path"])
                self.assertNotIn(entry["console_route"], seen_routes)
                seen_routes.add(entry["console_route"])
                self.assertEqual(
                    entry["console_route"],
                    "operations:component-registry:documents"
                    f"?document={identity}",
                )
                for field in required_typed_fields:
                    value = registry._typed_value(
                        entry[field],
                        f"{identity} {field}",
                    )
                    self.assertNotEqual(value.get("value"), "")
                    self.assertNotEqual(value.get("reason"), "")

                rendered = registry.render_metadata_block(
                    self.candidate,
                    identity,
                )
                self.assertNotIn("|  |", rendered)
                self.assertNotIn("| null |", rendered.lower())
                self.assertIn(f"`{identity}`", rendered)
                self.assertIn(f"?document={identity})", rendered)

    def test_cr004_parameterized_and_duplicate_leaf_scopes_are_disjoint(self):
        """Repeated names remain disjoint and parameters use one exact form."""

        scopes = self.candidate["directory_scopes"]["entries"]
        by_leaf: dict[str, list[tuple[str, str]]] = defaultdict(list)
        token_pattern = re.compile(r"^\{([a-z][a-z0-9_]*)\}$")
        for identity, scope in scopes.items():
            pattern = scope["path_pattern"].rstrip("/")
            leaf = pattern.split("/")[-1]
            by_leaf[leaf].append((identity, pattern))
            tokens = {
                match.group(1)
                for segment in pattern.split("/")
                if (match := token_pattern.fullmatch(segment)) is not None
            }
            self.assertNotIn("{{", pattern, identity)
            self.assertNotIn("}}", pattern, identity)
            self.assertEqual(
                tokens,
                set(scope["parameter_bindings"]),
                identity,
            )
            for ancestor in scope["ancestor_scope_ids"]:
                self.assertIn(ancestor, scopes)

        for leaf, matches in by_leaf.items():
            if len(matches) < 2:
                continue
            with self.subTest(leaf=leaf):
                full_paths = [pattern for _identity, pattern in matches]
                self.assertEqual(len(full_paths), len(set(full_paths)))
                for left_index, left in enumerate(full_paths):
                    for right in full_paths[left_index + 1 :]:
                        self.assertFalse(
                            left.startswith(right.rstrip("/") + "/")
                            or right.startswith(left.rstrip("/") + "/"),
                            f"duplicate leaf {leaf!r} has nested scopes "
                            f"{left!r} and {right!r}",
                        )

    def test_cr006_011_012_013_public_lifecycle_and_canonical_roots(self):
        """Public lifecycle homes and central test/tool roots remain distinct."""

        scopes = self.candidate["directory_scopes"]["entries"]
        expected = {
            "framework_logs": ("public_safe_only", "append_only"),
            "framework_reports": ("public_safe_only", "immutable"),
            "framework_status": ("public_safe_only", "replaceable"),
            "framework_receipts": ("public_safe_only", "immutable"),
        }
        for identity, values in expected.items():
            with self.subTest(identity=identity):
                self.assertEqual(
                    (
                        scopes[identity]["disclosure_boundary"],
                        scopes[identity]["lifecycle_posture"],
                    ),
                    values,
                )

        future = registry.future_tree_manifest(
            self.candidate,
            [
                "participate/tests/test_intake.py",
                "research/project-console/tests/frontend.test.mjs",
                "scripts/component_registry.py",
                "participate/api/submit.js",
            ],
        )
        paths = {
            item["source_path"]: item["future_path"]
            for item in future["items"]
        }
        self.assertTrue(
            paths["participate/tests/test_intake.py"].startswith(
                "tests/participation/",
            )
        )
        self.assertTrue(
            paths[
                "research/project-console/tests/frontend.test.mjs"
            ].startswith("tests/project-console/")
        )
        self.assertEqual(
            paths["scripts/component_registry.py"],
            "scripts/component_registry.py",
        )
        self.assertEqual(
            paths["participate/api/submit.js"],
            "participate/api/submit.js",
        )

    def test_cr020_022_023_026_agent_authored_approval_cannot_activate(self):
        """A valid-looking approval assertion cannot activate the candidate."""

        altered = copy.deepcopy(self.candidate)
        altered["status"] = "active"
        altered["approval"] = {
            "state": "known",
            "value": {
                "approved": True,
                "source": "agent-authored assertion",
            },
        }
        validators = (
            "_validate_directory_scopes",
            "_validate_operational_documents",
            "_validate_section_selectors",
            "_validate_ownership",
            "_validate_relationships_and_representations",
            "_validate_aliases",
            "_validate_repository_refs",
        )
        patches = [
            mock.patch.object(registry, name)
            for name in validators
        ]
        for patcher in patches:
            patcher.start()
        self.addCleanup(
            lambda: [patcher.stop() for patcher in reversed(patches)]
        )
        with self.assertRaises(registry.RegistryError):
            registry._validate_stage1_semantics(
                altered,
                self.embedded_route,
            )

    def test_cr021_copy_or_rename_cannot_create_a_second_document(self):
        """Copying an existing identity to another key/path fails closed."""

        altered = copy.deepcopy(self.candidate)
        source = copy.deepcopy(
            altered["operational_documents"]["entries"]["framework_kernel"]
        )
        source["document_id"] = "framework_kernel_copy"
        source["console_route"] = (
            "operations:component-registry:documents"
            "?document=framework_kernel_copy"
        )
        altered["operational_documents"]["entries"][
            "framework_kernel_copy"
        ] = source
        expected_digests = {
            entry["canonical_path"]: entry.get("sha256")
            for entry in altered["operational_documents"]["entries"].values()
        }
        with self.assertRaises(registry.RegistryError):
            with mock.patch.object(
                registry,
                "_sha256",
                side_effect=lambda path: expected_digests[
                    path.relative_to(ROOT).as_posix()
                ],
            ):
                registry._validate_operational_documents(
                    altered,
                    self.embedded_route,
                    root=ROOT,
                )

    def test_cr025_representations_do_not_become_second_authorities(self):
        """Every representation resolves to one canonical document identity."""

        documents = self.candidate["operational_documents"]["entries"]
        representations = self.candidate["representations"]["entries"]
        for identity, representation in representations.items():
            with self.subTest(identity=identity):
                canonical = representation.get("canonical_document_id")
                if canonical is not None:
                    self.assertIn(canonical, documents)
                self.assertNotIn(identity, documents)
                self.assertNotEqual(
                    representation["representation_type"],
                    "governing_authority",
                )

    def test_cr024_local_design_proposal_is_not_misrepresented_as_adopted(self):
        """The reviewed local proposal remains outside project authority."""

        documents = self.candidate["operational_documents"]["entries"]
        self.assertNotIn("CR-PROPOSAL-2026-001", documents)
        serialized = registry.canonical_json(self.candidate)
        self.assertNotIn(
            "component-registry-directory-scope-proposal.md",
            serialized,
        )
        self.assertEqual(self.candidate["status"], "candidate")
        self.assertEqual(self.candidate["approval"]["state"], "pending")

    def test_cr027_028_029_030_031_routing_is_additive_and_typed(self):
        """The route output is a complete union with explicit authority roles."""

        profile_id = "candidate_research"
        requested_capability = "publication"
        profile = self.embedded_route["profiles"][profile_id]
        seeds = list(self.embedded_route["required_modules"])
        seeds.extend(profile.get("modules", []))
        for capability in profile.get("capabilities", []):
            seeds.extend(self.embedded_route["capabilities"][capability])
        seeds.extend(
            self.embedded_route["capabilities"][requested_capability]
        )
        expected = dependency_closure(
            self.embedded_route["documents"],
            seeds,
        )

        output = registry.routed_documents(
            self.candidate,
            self.embedded_route,
            profile_id=profile_id,
            capability_ids=[requested_capability],
        )
        actual = {item["id"] for item in output["modules"]}
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), len(output["modules"]))
        for item in output["modules"]:
            with self.subTest(identity=item["id"]):
                self.assertTrue(item["inclusion_reasons"])
                self.assertIn(
                    item["authority_role"],
                    registry.ROUTE_AUTHORITY_ROLES,
                )
                registry._typed_value(
                    item["authority_scope"],
                    f"{item['id']} authority scope",
                )
                registry._typed_value(
                    item["authority_exclusions"],
                    f"{item['id']} authority exclusions",
                )
                if item["id"] == "current_audit":
                    self.assertFalse(item["governing"])
                    self.assertEqual(
                        item["authority_role"],
                        "runtime_checkpoint",
                    )

        with self.assertRaises(registry.RegistryError):
            registry.routed_documents(
                self.candidate,
                self.embedded_route,
                profile_id=profile_id,
                capability_ids=["unregistered-capability"],
            )

    def test_cr032_050_051_source_inventory_is_exact_not_count_only(self):
        """The complete imported routing source agrees field-for-field."""

        routing = self.candidate["context_routing"]
        snapshot = self.embedded_route
        self.assertEqual(
            registry.canonical_json(snapshot),
            registry.canonical_json(self.route),
        )
        self.assertEqual(registry.route_counts(snapshot), routing["expected_counts"])
        self.assertEqual(len(snapshot["documents"]), 88)
        self.assertEqual(len(snapshot["capabilities"]), 19)
        self.assertEqual(len(snapshot["profiles"]), 8)
        self.assertEqual(len(snapshot["required_modules"]), 3)
        self.assertEqual(len(snapshot["generated_path_exclusions"]), 9)
        self.assertEqual(
            hashlib.sha256(
                ROUTE_PATH.read_bytes(),
            ).hexdigest(),
            routing["source_import"]["sha256"],
        )

    def test_cr034_053_path_changes_preserve_stable_routing_identity(self):
        """A path-only migration does not require new profile membership."""

        altered = copy.deepcopy(self.candidate)
        altered_route = copy.deepcopy(self.embedded_route)
        identity = "current_audit"
        new_path = "framework/handoffs/current-task.md"
        altered["context_routing"]["documents"][identity]["path"] = new_path
        altered["operational_documents"]["entries"][identity][
            "canonical_path"
        ] = new_path
        altered_route["documents"][identity]["path"] = new_path

        before_memberships = {
            profile_id: registry.canonical_json(profile)
            for profile_id, profile in self.embedded_route[
                "profiles"
            ].items()
        }
        after_memberships = {
            profile_id: registry.canonical_json(profile)
            for profile_id, profile in altered_route["profiles"].items()
        }
        self.assertEqual(before_memberships, after_memberships)
        self.assertIn(identity, altered["context_routing"]["documents"])
        self.assertTrue(
            registry.parity_report(altered, altered_route)["valid"],
        )

    def test_cr038_scan_exclusions_have_registered_non_authority_bindings(self):
        """Every scan exclusion remains classified without becoming authority."""

        scopes = self.candidate["directory_scopes"]["entries"]
        representations = self.candidate["representations"]["entries"]
        excluded = self.candidate["context_routing"][
            "generated_path_exclusions"
        ]
        bindings = self.candidate["context_routing"][
            "scan_exclusion_bindings"
        ]
        self.assertEqual(set(bindings), set(excluded))
        for path, binding in bindings.items():
            with self.subTest(path=path):
                self.assertEqual(binding["excluded_path"], path)
                self.assertEqual(
                    binding["authority_effect"],
                    "scan_exclusion_only_no_authority",
                )
                self.assertEqual(
                    binding["placement_policy"],
                    "registered_binding_still_applies",
                )
                self.assertEqual(
                    binding["disclosure_policy"],
                    "disclosure_gate_still_applies",
                )
                self.assertEqual(
                    binding["classification_policy"],
                    "deferred_classification_fails_closed",
                )
                if binding["binding_kind"] == "directory_scope":
                    self.assertIn(binding["binding_id"], scopes)
                elif binding["binding_kind"] == "representation":
                    self.assertIn(binding["binding_id"], representations)
                else:
                    self.fail(
                        f"{path} has unknown binding kind "
                        f"{binding['binding_kind']!r}"
                    )

    def test_cr039_040_041_048_packet_is_bound_public_safe_and_candidate(self):
        """Readable routing binds its registry and remains nonauthoritative."""

        output = registry.routed_documents(
            self.candidate,
            self.embedded_route,
            profile_id="github_sync",
            capability_ids=[],
        )
        self.assertEqual(output["registry_id"], "COMPONENT-REGISTRY")
        self.assertEqual(
            output["registry_revision"],
            self.candidate["registry_revision"],
        )
        self.assertRegex(output["registry_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            output["source_sha256"],
            self.candidate["context_routing"]["source_import"]["sha256"],
        )
        self.assertEqual(output["registry_status"], "candidate")
        self.assertFalse(output["authoritative"])
        serialized = registry.canonical_json(output)
        self.assertNotIn("".join(("/", "Users", "/")), serialized)
        self.assertNotIn(
            "".join(("Application", " Support")),
            serialized,
        )
        self.assertNotIn("".join(("Library", "/")), serialized)

    def test_cr044_052_aliases_are_deterministic_and_candidate_only(self):
        """The approved structural aliases resolve once and remain inactive."""

        aliases = self.candidate["aliases_and_migrations"]["entries"]
        required = {
            "relocate_project_structure",
            "relocate_context_routing",
            "relocate_repository_map",
            "relocate_context_routes_source",
        }
        self.assertTrue(required.issubset(aliases))
        seen_sources: set[str] = set()
        for identity, alias in aliases.items():
            with self.subTest(identity=identity):
                self.assertEqual(alias["activation_state"], "candidate")
                self.assertNotIn(alias["source_path"], seen_sources)
                seen_sources.add(alias["source_path"])
                self.assertIn(
                    alias["reference_policy"],
                    {"rewrite_active", "preserve_historical"},
                )
                result = registry.future_tree_manifest(
                    self.candidate,
                    [alias["source_path"]],
                )
                self.assertEqual(result["items"][0]["alias_id"], identity)
                self.assertEqual(
                    result["items"][0]["future_path"],
                    alias["target_path"],
                )

    def test_cr042_047_054_cutover_requirements_remain_pending(self):
        """Activation-only routing changes are not claimed during review."""

        routing = self.candidate["context_routing"]
        self.assertFalse(routing["authoritative"])
        self.assertEqual(routing["activation_state"], "candidate_import")
        self.assertEqual(
            routing["source_import"]["path"],
            "framework/project/automation/context-routes.json",
        )
        self.assertIn("route_source", self.candidate["source_baseline"])
        self.assertNotIn("predecessor_provenance", routing)
        self.assertNotIn("readable_representation", routing)
        navigation = routing["capabilities"]["navigation_and_inventory"]
        self.assertIn("repository_map", navigation)
        self.assertIn("project_structure", navigation)
        self.assertNotIn("COMPONENT-REGISTRY", navigation)
        aliases = self.candidate["aliases_and_migrations"]["entries"]
        for identity in (
            "relocate_project_structure",
            "relocate_context_routing",
            "relocate_repository_map",
            "relocate_context_routes_source",
        ):
            self.assertEqual(aliases[identity]["activation_state"], "candidate")

    def test_cr045_046_routing_rule_catalog_is_exact_and_nonauthoritative(self):
        """The approved rule IDs close the gap without activating the candidate."""

        routing = self.candidate["context_routing"]
        expected_counts = {
            "invariants": 7,
            "selection": 17,
            "validation": 10,
            "failure_rules": 10,
            "currentness": 6,
            "budgets": 4,
            "comprehensive_review": 10,
        }
        self.assertEqual(routing["schema_version"], 2)
        self.assertEqual(routing["rule_catalog_version"], 1)
        self.assertEqual(
            {
                namespace: len(routing[namespace])
                for namespace in expected_counts
            },
            expected_counts,
        )
        self.assertEqual(
            hashlib.sha256(ROUTING_PREDECESSOR_PATH.read_bytes()).hexdigest(),
            ROUTING_PREDECESSOR_SHA256,
        )
        for namespace in expected_counts:
            for rule_id, entry in routing[namespace].items():
                with self.subTest(namespace=namespace, rule_id=rule_id):
                    provenance = entry["source_provenance"]
                    self.assertEqual(entry["rule_id"], rule_id)
                    self.assertEqual(entry["predicate_type"], rule_id)
                    self.assertEqual(
                        provenance["source_document_id"],
                        "context_routing",
                    )
                    self.assertEqual(
                        provenance["source_sha256"],
                        ROUTING_PREDECESSOR_SHA256,
                    )
                    self.assertEqual(provenance["clause_key"], rule_id)

        self.assertEqual(routing["activation_state"], "candidate_import")
        self.assertFalse(routing["authoritative"])
        active_route = registry.canonical_json(self.route).lower()
        self.assertNotIn("component_registry", active_route)
        self.assertNotIn("component-registry", active_route)

    def test_cr055_repository_map_does_not_supply_runtime_posture(self):
        """The predecessor map entry contains no imported live runtime fact."""

        entry = self.candidate["operational_documents"]["entries"][
            "repository_map"
        ]
        serialized = registry.canonical_json(entry).lower()
        for forbidden in (
            "".join(("automation ", "is paused")),
            "".join(("next scheduled ", "run")),
            "".join(("launch", "agent is lo", "aded")),
            "".join(("cur", "rent l", "ock")),
            "".join(("runtime ", "topology")),
        ):
            self.assertNotIn(forbidden, serialized)

    def test_cr056_061_readmes_summaries_and_local_reports_do_not_compete(self):
        """Scope guides and local delivery artifacts are not live authorities."""

        documents = self.candidate["operational_documents"]["entries"]
        readme_paths = {
            entry["canonical_path"]
            for entry in documents.values()
            if entry["canonical_path"].endswith("README.md")
        }
        self.assertEqual(readme_paths, {"README.md"})
        self.assertNotIn("elim_run_summary", documents)
        retirement = self.candidate["aliases_and_migrations"]["entries"][
            "retire_elim_run_summary"
        ]
        self.assertEqual(retirement["alias_type"], "retirement")
        self.assertEqual(
            retirement["reference_policy"],
            "preserve_historical",
        )
        serialized = registry.canonical_json(self.candidate)
        self.assertNotIn("".join(("/", "Users", "/")), serialized)
        self.assertNotIn(".codex/visualizations", serialized)
        self.assertNotIn("local report archive", serialized.lower())

    def test_cr062_063_codeowners_is_exact_and_bootstrap_protected(self):
        """Registry ownership generates one deterministic protected projection."""

        generated = registry.generate_codeowners_text(self.candidate)
        self.assertEqual(
            generated,
            registry.generate_codeowners_text(self.candidate),
        )
        lines = generated.splitlines()
        entries = self.candidate["ownership_and_review"]["entries"]
        self.assertEqual(len(lines), len(entries) + 1)
        self.assertEqual(lines[0], registry.CODEOWNERS_HEADER)
        for path in {
            *registry.PROTECTED_CORE_PATHS,
            "tests/framework/test_component_registry_stage1_acceptance.py",
        }:
            matching = [
                entry
                for entry in entries.values()
                if registry._codeowners_pattern_matches(
                    path,
                    entry["path_pattern"],
                )
            ]
            self.assertTrue(matching, path)
            effective = max(matching, key=lambda item: item["precedence"])
            self.assertIn("@Thorncrag", effective["owners"])
            self.assertEqual(
                effective["review_policy"],
                "owner_review_required",
            )

    def test_cr064_log_append_policy_is_distinct_from_definition_review(self):
        """Validated appenders do not become approval for log definitions."""

        entries = self.candidate["ownership_and_review"]["entries"].values()
        appenders = [
            entry
            for entry in entries
            if entry["ordinary_writer_policy"] == "validated_appender"
        ]
        self.assertTrue(appenders)
        for entry in appenders:
            self.assertEqual(entry["review_policy"], "owner_review_required")
            self.assertIn("@Thorncrag", entry["owners"])
            self.assertEqual(
                entry["branch_protection"],
                "default_branch_owner_review",
            )

    def test_cr067_072_075_repository_reference_boundary_is_fail_closed(self):
        """Stage 1 defines classes but supplies no mutation or neutral claim."""

        namespace = self.candidate["repository_ref_lifecycle"]
        self.assertEqual(namespace["activation_state"], "candidate_inactive")
        self.assertTrue(namespace["complete"])
        self.assertFalse(namespace["enforced"])
        self.assertEqual(
            namespace["authority_boundary"],
            "classification_definitions_only_no_mutation_authority",
        )
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
        serialized = registry.canonical_json(namespace)
        self.assertNotIn('"historical"', serialized)
        self.assertNotIn('"unknown"', serialized)
        self.assertNotIn('"fully_reconciled"', serialized)
        self.assertNotIn('"neutral"', serialized)
        for identity, entry in namespace["entries"].items():
            with self.subTest(identity=identity):
                self.assertEqual(
                    entry["mutation_activation"],
                    "separately_gated",
                )
                self.assertTrue(entry["required_bindings"])
                self.assertTrue(entry["protected_exclusions"])
                self.assertTrue(entry["receipt_readback_required"])
                if identity != "canonical_default":
                    self.assertIn(
                        "approval",
                        entry["retirement_authority"].lower(),
                    )

    def test_cr077_retired_standing_branch_architecture_is_not_current(self):
        """Current workflow/runbooks may not claim dedicated bot branches."""

        active_paths = [
            ROOT / "framework" / "project" / "github" / "workflow.md",
            *sorted(
                (
                    ROOT / "framework" / "project" / "automation" / "runbooks"
                ).glob("*.md")
            ),
        ]
        prohibited = re.compile(
            r"(use|uses|using|on)\s+dedicated automation branches",
            re.IGNORECASE,
        )
        findings: list[str] = []
        for path in active_paths:
            text = path.read_text(encoding="utf-8")
            for line_number, line in enumerate(text.splitlines(), start=1):
                if prohibited.search(line):
                    findings.append(
                        f"{path.relative_to(ROOT).as_posix()}:{line_number}"
                    )
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
