import hashlib
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from arrp_context import (  # noqa: E402
    ContextError,
    build_context_packet,
    build_work_queue,
    canonical_issue_area,
    extract_exact_heading,
    load_route_manifest,
    repository_file,
    stable_work_id,
    validate_queue_canonical_record,
)
from select_elim_context_route import select_context_route  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class ExactContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "framework").mkdir()
        (self.root / "areas/TEST/issues").mkdir(parents=True)
        (self.root / "inventory").mkdir()
        self.document = self.root / "framework/rules.md"
        self.document.write_text(
            "# Rules\n\n## Selected\n\nRequired.\n\n### Child\n\nAlso required.\n\n## Other\n\nExcluded.\n",
            encoding="utf-8",
        )
        issue = self.root / "areas/TEST/issues/TEST-001.md"
        issue.write_text(
            "---\nissue_id: TEST-001\naudit_history: TEST-001.audit.md\n"
            'legislative_proposal: "../../../legislation/TEST-001.md"\n---\n# TEST-001\n',
            encoding="utf-8",
        )
        (self.root / "areas/TEST/issues/TEST-001.audit.md").write_text(
            "# Audit\n\n## Audit History\n\n### Newest\n\nLatest.\n\n### Older\n\nOld.\n",
            encoding="utf-8",
        )
        (self.root / "legislation").mkdir()
        (self.root / "legislation/TEST-001.md").write_text("# Vehicle\n", encoding="utf-8")
        (self.root / "inventory/sources.csv").write_text(
            "Source ID,Associated Record IDs,Title or Description\nSRC-0001,TEST-001,One\n"
            "SRC-0002,TEST-002,Two\n",
            encoding="utf-8",
        )
        (self.root / "inventory/sources-pending.csv").write_text(
            "Source ID,Associated Record IDs,Title or Description\n", encoding="utf-8"
        )
        (self.root / "inventory/github_issue_registry.csv").write_text(
            "GitHub Title,Canonical Record\nTEST-001: Test,areas/TEST/issues/TEST-001.md\n",
            encoding="utf-8",
        )
        digest = hashlib.sha256(self.document.read_bytes()).hexdigest()
        self.manifest = self.root / "manifest.json"
        write_json(
            self.manifest,
            {
                "schema_version": 1,
                "generated_path_exclusions": ["generated"],
                "documents": {"rules": {"path": "framework/rules.md", "sha256": digest}},
                "profiles": {
                    "issue": {
                        "max_bytes": 20000,
                        "sections": [
                            {
                                "document": "rules",
                                "heading": "## Selected",
                                "max_bytes": 1000,
                            }
                        ],
                    }
                },
            },
        )

    def tearDown(self):
        self.temp.cleanup()

    def schema_two_manifest(self) -> Path:
        documents = {
            "kernel": ("framework/kernel.md", "# Kernel\n"),
            "current": ("framework/current.md", "# Mutable checkpoint\n"),
            "operation": ("framework/operation.md", "# Operation\n"),
            "evidence": ("framework/evidence.md", "# Evidence\n"),
        }
        for relative, content in documents.values():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        specs = {
            "kernel": {
                "path": documents["kernel"][0],
                "sha256": hashlib.sha256(
                    (self.root / documents["kernel"][0]).read_bytes()
                ).hexdigest(),
                "hash_policy": "pinned",
                "governing": True,
            },
            "current": {
                "path": documents["current"][0],
                "hash_policy": "runtime",
                "governing": False,
                "requires": ["kernel"],
            },
            "operation": {
                "path": documents["operation"][0],
                "sha256": hashlib.sha256(
                    (self.root / documents["operation"][0]).read_bytes()
                ).hexdigest(),
                "hash_policy": "pinned",
                "governing": True,
                "requires": ["kernel"],
            },
            "evidence": {
                "path": documents["evidence"][0],
                "sha256": hashlib.sha256(
                    (self.root / documents["evidence"][0]).read_bytes()
                ).hexdigest(),
                "hash_policy": "pinned",
                "governing": True,
                "requires": ["operation"],
            },
        }
        path = self.root / "schema-two.json"
        write_json(
            path,
            {
                "schema_version": 2,
                "required_modules": ["kernel", "current"],
                "documents": specs,
                "capabilities": {"evidence_review": ["evidence"]},
                "profiles": {
                    "task": {
                        "max_bytes": 100000,
                        "modules": ["operation"],
                    },
                    "comprehensive": {
                        "max_bytes": 100000,
                        "include_all_governing": True,
                    },
                },
            },
        )
        return path

    def test_exact_heading_includes_children_but_not_next_peer(self):
        content, start, end = extract_exact_heading(self.document.read_text(), "## Selected")
        self.assertIn("### Child", content)
        self.assertNotIn("## Other", content)
        self.assertEqual(start, 3)
        self.assertGreater(end, start)

    def test_context_packet_is_bounded_and_issue_specific(self):
        packet = build_context_packet(
            self.manifest, "issue", root=self.root, issue_id="TEST-001"
        )
        self.assertEqual(
            packet["schema_version"],
            2,
            "schema-1 manifests are accepted but packets use the normalized schema-2 contract",
        )
        self.assertTrue(packet["provenance_complete"])
        self.assertEqual(packet["issue_dossier"]["sources"][0]["Source ID"], "SRC-0001")
        self.assertTrue(packet["issue_dossier"]["source_catalog"]["projection_only"])
        self.assertNotIn("Notes", packet["issue_dossier"]["sources"][0])
        self.assertEqual(packet["issue_dossier"]["latest_audit_entry"]["heading"], "### Newest")
        self.assertIn(
            "# Vehicle",
            packet["issue_dossier"]["linked_vehicles"][0]["content"],
        )
        self.assertLessEqual(packet["limits"]["actual_bytes"], packet["limits"]["max_bytes"])

    def test_context_packet_preserves_exact_work_selection(self):
        packet = build_context_packet(
            self.manifest,
            "issue",
            root=self.root,
            work_item_id="ISSUE-DEVELOPMENT-abc123",
            work_kind="issue_development",
            canonical_record="areas/TEST/issues/TEST-001.md",
        )
        self.assertEqual(
            packet["selection"],
            {
                "work_item_id": "ISSUE-DEVELOPMENT-abc123",
                "kind": "issue_development",
                "canonical_record": "areas/TEST/issues/TEST-001.md",
            },
        )

    def test_context_packet_selection_is_optional_for_interactive_calls(self):
        packet = build_context_packet(self.manifest, "issue", root=self.root)
        self.assertIsNone(packet["selection"])

    def test_context_packet_selection_allows_a_non_record_work_unit(self):
        packet = build_context_packet(
            self.manifest,
            "issue",
            root=self.root,
            work_item_id="INTEGRITY-abc123",
            work_kind="integrity",
            canonical_record="",
        )
        self.assertEqual(
            packet["selection"],
            {
                "work_item_id": "INTEGRITY-abc123",
                "kind": "integrity",
                "canonical_record": None,
            },
        )

    def test_context_packet_selection_requires_a_safe_id_and_kind_pair(self):
        with self.assertRaisesRegex(ContextError, "must be supplied together"):
            build_context_packet(
                self.manifest,
                "issue",
                root=self.root,
                work_item_id="INTEGRITY-abc123",
            )
        with self.assertRaisesRegex(ContextError, "safe identifier"):
            build_context_packet(
                self.manifest,
                "issue",
                root=self.root,
                work_item_id=" INTEGRITY-abc123",
                work_kind="integrity",
            )
        with self.assertRaisesRegex(ContextError, "lower-snake-case"):
            build_context_packet(
                self.manifest,
                "issue",
                root=self.root,
                work_item_id="INTEGRITY-abc123",
                work_kind="Integrity Work",
            )

    def test_context_packet_selection_rejects_unsafe_canonical_records(self):
        common = {
            "root": self.root,
            "work_item_id": "ISSUE-DEVELOPMENT-abc123",
            "work_kind": "issue_development",
        }
        with self.assertRaisesRegex(ContextError, "surrounding whitespace"):
            build_context_packet(
                self.manifest,
                "issue",
                canonical_record=" areas/TEST/issues/TEST-001.md",
                **common,
            )
        with self.assertRaisesRegex(ContextError, "exact normalized"):
            build_context_packet(
                self.manifest,
                "issue",
                canonical_record="areas/TEST/issues/../issues/TEST-001.md",
                **common,
            )
        with self.assertRaisesRegex(ContextError, "unsupported URL"):
            build_context_packet(
                self.manifest,
                "issue",
                canonical_record="https://example.com/record",
                **common,
            )

    def test_bounded_issue_identifier_parser_rejects_adversarial_input(self):
        self.assertEqual(canonical_issue_area("TEST-001"), "TEST")
        for value in (
            "A" * 100_000 + "-001",
            "../TEST-001",
            "test-001",
            "TEST-0001",
            "TEST-00A",
        ):
            with self.subTest(value=value[:80]):
                with self.assertRaisesRegex(
                    ContextError,
                    "invalid canonical issue identifier",
                ):
                    canonical_issue_area(value)

    def test_repository_file_rejects_traversal_and_symlink_escape(self):
        self.assertEqual(
            repository_file(
                self.root,
                "areas/TEST/issues/TEST-001.md",
            ),
            (self.root / "areas/TEST/issues/TEST-001.md").resolve(),
        )
        with self.assertRaisesRegex(ContextError, "exact normalized"):
            repository_file(
                self.root,
                "areas/TEST/issues/../issues/TEST-001.md",
            )

        with tempfile.TemporaryDirectory() as outside_directory:
            outside = Path(outside_directory) / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            escape = self.root / "areas/TEST/issues/TEST-002.md"
            escape.symlink_to(outside)
            with self.assertRaisesRegex(ContextError, "escapes allowed root"):
                repository_file(
                    self.root,
                    "areas/TEST/issues/TEST-002.md",
                )

    def test_context_packet_rejects_symlinked_canonical_records(self):
        with tempfile.TemporaryDirectory() as outside_directory:
            outside = Path(outside_directory) / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            escape = self.root / "areas/TEST/issues/TEST-002.md"
            escape.symlink_to(outside)

            with self.assertRaisesRegex(ContextError, "escapes allowed root"):
                build_context_packet(
                    self.manifest,
                    "issue",
                    root=self.root,
                    issue_id="TEST-002",
                )
            canonical, problem = validate_queue_canonical_record(
                self.root,
                "TEST-002",
                "areas/TEST/issues/TEST-002.md",
                formal_horizon=False,
            )
            self.assertIsNone(canonical)
            self.assertIn("unsafe canonicalRecord", problem)
            self.assertIn("escapes allowed root", problem)

    def test_context_packet_rejects_symlinked_area_readme(self):
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["profiles"]["issue_development"] = deepcopy(
            manifest["profiles"]["issue"]
        )
        write_json(self.manifest, manifest)
        with tempfile.TemporaryDirectory() as outside_directory:
            outside = Path(outside_directory) / "README.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            (self.root / "areas/TEST/README.md").symlink_to(outside)
            with self.assertRaisesRegex(ContextError, "escapes allowed root"):
                build_context_packet(
                    self.manifest,
                    "issue_development",
                    root=self.root,
                    issue_id="TEST-003",
                )

    def test_context_packet_requires_the_exact_sibling_audit_history(self):
        issue = self.root / "areas/TEST/issues/TEST-001.md"
        issue.write_text(
            "---\n"
            "issue_id: TEST-001\n"
            'audit_history: "../../../outside.md"\n'
            "---\n"
            "# TEST-001\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            ContextError,
            "must name its exact sibling TEST-001.audit.md",
        ):
            build_context_packet(
                self.manifest,
                "issue",
                root=self.root,
                issue_id="TEST-001",
            )

    def test_yaml_dates_are_normalized_for_packet_serialization(self):
        issue = self.root / "areas/TEST/issues/TEST-001.md"
        issue.write_text(
            "---\nissue_id: TEST-001\naudit_last_date: 2026-07-24\n"
            'audit_history: "TEST-001.audit.md"\n---\n# TEST-001\n',
            encoding="utf-8",
        )
        packet = build_context_packet(
            self.manifest, "issue", root=self.root, issue_id="TEST-001"
        )
        self.assertEqual(
            packet["issue_dossier"]["issue_page"]["front_matter"]["audit_last_date"],
            "2026-07-24",
        )

    def test_context_packet_resolves_canonical_vehicle_metadata_aliases(self):
        issue = self.root / "areas/TEST/issues/TEST-001.md"
        for field in (
            "federal_legislative_proposal",
            "federal_legislation",
            "constitutional_proposal",
            "alternative_legislative_proposal",
            "proposal_legislation",
            "enabling_legislation",
        ):
            with self.subTest(field=field):
                issue.write_text(
                    "---\nissue_id: TEST-001\naudit_history: TEST-001.audit.md\n"
                    f'{field}: "../../../legislation/TEST-001.md"\n---\n# TEST-001\n',
                    encoding="utf-8",
                )
                packet = build_context_packet(
                    self.manifest, "issue", root=self.root, issue_id="TEST-001"
                )
                self.assertEqual(
                    packet["issue_dossier"]["linked_vehicles"][0]["path"],
                    "legislation/TEST-001.md",
                )

    def test_context_packet_includes_multiple_linked_vehicles(self):
        issue = self.root / "areas/TEST/issues/TEST-001.md"
        (self.root / "legislation/TEST-001-alt.md").write_text(
            "# Alternative Vehicle\n", encoding="utf-8"
        )
        issue.write_text(
            "---\nissue_id: TEST-001\naudit_history: TEST-001.audit.md\n"
            'legislative_proposal: "../../../legislation/TEST-001.md"\n'
            'alternative_legislative_proposal: "../../../legislation/TEST-001-alt.md"\n'
            "---\n# TEST-001\n",
            encoding="utf-8",
        )
        packet = build_context_packet(
            self.manifest, "issue", root=self.root, issue_id="TEST-001"
        )
        self.assertEqual(
            [
                vehicle["path"]
                for vehicle in packet["issue_dossier"]["linked_vehicles"]
            ],
            [
                "legislation/TEST-001.md",
                "legislation/TEST-001-alt.md",
            ],
        )

    def test_issue_development_can_build_a_generic_area_record_dossier(self):
        area_readme = self.root / "areas/TEST/README.md"
        area_readme.write_text(
            "# TEST\n\n## TEST-003\n\nStable undeveloped issue record.\n",
            encoding="utf-8",
        )
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["profiles"]["issue_development"] = deepcopy(
            manifest["profiles"]["issue"]
        )
        write_json(self.manifest, manifest)

        packet = build_context_packet(
            self.manifest,
            "issue_development",
            root=self.root,
            issue_id="TEST-003",
        )

        dossier = packet["issue_dossier"]
        self.assertEqual(dossier["canonical_record_kind"], "area_readme")
        self.assertEqual(
            dossier["canonical_record_path"],
            "areas/TEST/README.md",
        )
        self.assertIn(
            "Stable undeveloped issue record",
            dossier["canonical_record"]["content"],
        )
        self.assertIsNone(dossier["issue_page"])
        self.assertIsNone(dossier["latest_audit_entry"])
        self.assertEqual(dossier["linked_vehicles"], [])
        self.assertNotIn("front_matter", dossier["canonical_record"])

    def test_changed_hash_fails_closed(self):
        self.document.write_text(self.document.read_text() + "\nchanged\n", encoding="utf-8")
        with self.assertRaisesRegex(ContextError, "hash changed"):
            load_route_manifest(self.manifest, root=self.root)

    def test_missing_duplicate_and_oversized_sections_fail_closed(self):
        self.document.write_text("## Selected\none\n## Selected\ntwo\n", encoding="utf-8")
        digest = hashlib.sha256(self.document.read_bytes()).hexdigest()
        manifest = json.loads(self.manifest.read_text())
        manifest["documents"]["rules"]["sha256"] = digest
        write_json(self.manifest, manifest)
        with self.assertRaisesRegex(ContextError, "duplicated"):
            build_context_packet(self.manifest, "issue", root=self.root)
        self.document.write_text("## Selected\n" + "x" * 2000, encoding="utf-8")
        manifest["documents"]["rules"]["sha256"] = hashlib.sha256(
            self.document.read_bytes()
        ).hexdigest()
        write_json(self.manifest, manifest)
        with self.assertRaisesRegex(ContextError, "exceeds max_bytes"):
            build_context_packet(self.manifest, "issue", root=self.root)

    def test_generated_paths_and_placeholder_hashes_are_rejected(self):
        manifest = json.loads(self.manifest.read_text())
        manifest["documents"]["rules"] = {
            "path": "generated/catalog-data.js",
            "sha256": "__SET_AT_INTEGRATION__",
        }
        write_json(self.manifest, manifest)
        with self.assertRaisesRegex(ContextError, "excluded generated path"):
            load_route_manifest(self.manifest, root=self.root)

    def test_schema_two_loads_required_modules_dependencies_and_additive_capabilities(self):
        manifest_path = self.schema_two_manifest()

        base = build_context_packet(manifest_path, "task", root=self.root)
        self.assertEqual(
            [module["document"] for module in base["modules"]],
            ["kernel", "current", "operation"],
        )
        self.assertEqual(base["capabilities"], [])

        expanded = build_context_packet(
            manifest_path,
            "task",
            root=self.root,
            capabilities=("evidence_review",),
        )
        self.assertEqual(
            [module["document"] for module in expanded["modules"]],
            ["kernel", "current", "operation", "evidence"],
        )
        self.assertEqual(expanded["capabilities"], ["evidence_review"])

        current = self.root / "framework/current.md"
        current.write_text("# Mutable checkpoint\n\nChanged safely.\n", encoding="utf-8")
        refreshed = build_context_packet(manifest_path, "task", root=self.root)
        current_module = next(
            module
            for module in refreshed["modules"]
            if module["document"] == "current"
        )
        self.assertEqual(current_module["hash_policy"], "runtime")
        self.assertEqual(
            current_module["sha256"],
            hashlib.sha256(current.read_bytes()).hexdigest(),
        )

        operation = self.root / "framework/operation.md"
        operation.write_text("# Operation\n\nUnpinned change.\n", encoding="utf-8")
        with self.assertRaisesRegex(ContextError, "hash changed"):
            build_context_packet(manifest_path, "task", root=self.root)

    def test_schema_two_comprehensive_profile_includes_every_governing_document(self):
        manifest_path = self.schema_two_manifest()
        packet = build_context_packet(
            manifest_path,
            "comprehensive",
            root=self.root,
        )
        module_ids = {module["document"] for module in packet["modules"]}
        self.assertEqual(
            module_ids,
            {"kernel", "current", "operation", "evidence"},
        )

    def test_schema_two_rejects_pinned_placeholders_and_pinned_runtime_documents(self):
        manifest_path = self.schema_two_manifest()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["documents"]["operation"]["sha256"] = "__SET_AT_INTEGRATION__"
        write_json(manifest_path, manifest)
        with self.assertRaisesRegex(ContextError, "no integration-pinned sha256"):
            load_route_manifest(manifest_path, root=self.root)

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["documents"]["operation"]["sha256"] = hashlib.sha256(
            (self.root / "framework/operation.md").read_bytes()
        ).hexdigest()
        manifest["documents"]["current"]["sha256"] = hashlib.sha256(
            (self.root / "framework/current.md").read_bytes()
        ).hexdigest()
        write_json(manifest_path, manifest)
        with self.assertRaisesRegex(
            ContextError,
            "runtime-hashed document current must not carry a pinned sha256",
        ):
            load_route_manifest(manifest_path, root=self.root)

    def test_schema_two_rejects_dependency_cycles_and_unknown_capabilities(self):
        manifest_path = self.schema_two_manifest()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["documents"]["operation"]["requires"] = ["evidence"]
        write_json(manifest_path, manifest)
        with self.assertRaisesRegex(ContextError, "dependency cycle"):
            load_route_manifest(manifest_path, root=self.root)

        manifest_path = self.schema_two_manifest()
        with self.assertRaisesRegex(ContextError, "unknown context capability"):
            build_context_packet(
                manifest_path,
                "task",
                root=self.root,
                capabilities=("unregistered",),
            )

    def test_schema_two_requires_boolean_governance_and_pins_governing_documents(self):
        manifest_path = self.schema_two_manifest()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["documents"]["operation"]["governing"] = "false"
        write_json(manifest_path, manifest)
        with self.assertRaisesRegex(ContextError, "governing must be an explicit boolean"):
            load_route_manifest(manifest_path, root=self.root)

        manifest_path = self.schema_two_manifest()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["documents"]["current"]["governing"] = True
        write_json(manifest_path, manifest)
        with self.assertRaisesRegex(
            ContextError,
            "runtime-hashed document current must be explicitly non-governing",
        ):
            load_route_manifest(manifest_path, root=self.root)

    def test_schema_two_rejects_duplicate_canonical_document_paths(self):
        manifest_path = self.schema_two_manifest()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["documents"]["operation_alias"] = {
            **manifest["documents"]["operation"],
            "path": "framework/./operation.md",
        }
        write_json(manifest_path, manifest)
        with self.assertRaisesRegex(ContextError, "duplicate one canonical path"):
            load_route_manifest(manifest_path, root=self.root)

    def test_dynamic_capability_cannot_duplicate_a_routed_section(self):
        manifest_path = self.schema_two_manifest()
        evidence_path = self.root / "framework/evidence.md"
        evidence_path.write_text(
            "# Evidence\n\n## Selected Evidence\n\nRequired.\n",
            encoding="utf-8",
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["documents"]["evidence"]["sha256"] = hashlib.sha256(
            evidence_path.read_bytes()
        ).hexdigest()
        manifest["profiles"]["task"]["sections"] = [
            {
                "document": "evidence",
                "heading": "## Selected Evidence",
                "max_bytes": 1000,
            }
        ]
        write_json(manifest_path, manifest)

        build_context_packet(manifest_path, "task", root=self.root)
        with self.assertRaisesRegex(
            ContextError,
            "loads evidence both as a whole module and a section",
        ):
            build_context_packet(
                manifest_path,
                "task",
                root=self.root,
                capabilities=("evidence_review",),
            )


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.now = datetime(2026, 7, 24, 12, tzinfo=timezone.utc)

    def tearDown(self):
        self.temp.cleanup()

    def path(self, name: str, data: dict) -> Path:
        path = self.root / name
        write_json(path, data)
        return path

    def test_queue_uses_flags_cursor_fairness_recovery_and_epoch(self):
        issue_directory = self.root / "areas/TEST/issues"
        issue_directory.mkdir(parents=True)
        for identifier in ("TEST-001", "TEST-002"):
            (issue_directory / f"{identifier}.md").write_text(
                f"# {identifier}\n",
                encoding="utf-8",
            )
        integrity = self.path(
            "integrity.json",
            {
                "generated_at": "2026-07-24T11:00:00Z",
                "revision": "abc",
                "findings": [
                    {
                        "id": "warning-1",
                        "severity": "warning",
                        "attention": "human",
                        "message": "Missing human explanation",
                    }
                ],
            },
        )
        progress = self.path(
            "progress.json",
            {
                "generatedAt": "2026-07-24T11:00:00Z",
                "repositoryRevision": "abc",
                "asOf": "2026-01-01",
                "candidates": [
                    {
                        "identifier": "TEST-001",
                        "canonicalRecord": "areas/TEST/issues/TEST-001.md",
                        "developmentLevel": "In development",
                        "workflowStatus": "Development",
                        "nextAudit": "Continue drafting",
                    },
                    {
                        "identifier": "TEST-002",
                        "canonicalRecord": "areas/TEST/issues/TEST-002.md",
                        "developmentLevel": "Developed proposal",
                        "workflowStatus": "Audit needed",
                        "nextAudit": "Targeted Change Audit",
                        "changeAuditNeeded": True,
                    },
                ],
            },
        )
        intake = self.path(
            "intake.json",
            {
                "generated_at": "2026-07-24T11:00:00Z",
                "pending": True,
                "last_processed_id": "D-1",
                "items": [
                    {"id": "D-1", "state": "pending", "created_at": "2026-07-24"},
                    {
                        "id": "D-2",
                        "state": "pending",
                        "created_at": "2026-07-23",
                        "content_hash": "safe-hash",
                    },
                ],
            },
        )
        chain = self.path(
            "chain.json",
            {
                "completed_at": "2026-07-24T11:00:00Z",
                "final_revision": "abc",
                "bots": [
                    {"id": "source-checker-bot", "due": True, "status": "failed", "error": "timeout"}
                ],
            },
        )
        development_id = stable_work_id("issue_development", "TEST-001")
        recovery = self.path(
            "recovery.json",
            {
                "generated_at": "2026-07-24T11:00:00Z",
                "items": [
                    {
                        "work_id": development_id,
                        "state": "human_required",
                        "attempt_count": 3,
                        "continuation": "Resolve ambiguity",
                    }
                ],
            },
        )
        epoch = self.path(
            "epoch.json",
            {
                "completed_at": "2026-07-01T00:00:00Z",
                "epoch_id": "EPOCH-1",
                "baseline_revision": "old",
                "next_due_at": "2026-07-20T00:00:00Z",
                "unresolved_ids": ["X-1"],
            },
        )
        queue = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            recovery_path=recovery,
            review_epoch_path=epoch,
            now=self.now,
            input_root=self.root,
        )
        self.assertTrue(queue["ready_for_elim"])
        self.assertEqual(queue["items"][0]["kind"], "bot_failure")
        self.assertEqual(sum(item["kind"] == "public_intake" for item in queue["items"]), 1)
        self.assertTrue(any(item["kind"] == "comprehensive_review" for item in queue["items"]))
        development = next(item for item in queue["items"] if item["id"] == development_id)
        self.assertFalse(development["eligible_for_elim"])
        self.assertEqual(development["recovery"]["attempt_count"], 3)
        self.assertGreater(development["fairness_boost"], 0)
        self.assertEqual(
            development["source"]["canonicalRecord"],
            "areas/TEST/issues/TEST-001.md",
        )

    def test_formal_horizon_research_candidate_gets_distinct_queue_kind(self):
        integrity = self.path(
            "integrity.json",
            {
                "generated_at": "2026-07-24T11:00:00Z",
                "revision": "abc",
                "findings": [],
            },
        )
        progress = self.path(
            "progress.json",
            {
                "generatedAt": "2026-07-24T11:00:00Z",
                "repositoryRevision": "abc",
                "asOf": "2026-07-24",
                "proposals": [
                    {
                        "identifier": "HOR-035",
                        "canonicalRecord": "https://github.com/Thorncrag/ARRP/issues/255",
                        "developmentLevel": "Candidate",
                        "workflowStatus": "Research",
                        "nextAudit": "Complete the cross-administration docket study",
                    }
                ],
            },
        )
        intake = self.path(
            "intake.json",
            {
                "generated_at": "2026-07-24T11:00:00Z",
                "pending": False,
                "items": [],
            },
        )
        chain = self.path(
            "chain.json",
            {
                "completed_at": "2026-07-24T11:00:00Z",
                "final_revision": "abc",
                "bots": [],
            },
        )

        queue = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            now=self.now,
            input_root=self.root,
        )

        self.assertTrue(queue["ready_for_elim"])
        self.assertEqual(queue["counts"]["elim_eligible"], 1)
        item = queue["items"][0]
        self.assertEqual(item["kind"], "candidate_research")
        self.assertEqual(item["source"]["identifier"], "HOR-035")
        self.assertEqual(
            item["source"]["canonicalRecord"],
            "https://github.com/Thorncrag/ARRP/issues/255",
        )

    def test_area_readme_is_allowed_but_missing_record_fails_only_if_selected(self):
        area = self.root / "areas/TEST"
        area.mkdir(parents=True)
        (area / "README.md").write_text("# TEST\n", encoding="utf-8")
        issue_directory = area / "issues"
        issue_directory.mkdir()
        (issue_directory / "TEST-005.md").write_text(
            "# TEST-005\n",
            encoding="utf-8",
        )
        integrity = self.path(
            "integrity.json",
            {
                "generated_at": "2026-07-24T11:00:00Z",
                "revision": "abc",
                "findings": [],
            },
        )
        progress = self.path(
            "progress.json",
            {
                "generatedAt": "2026-07-24T11:00:00Z",
                "repositoryRevision": "abc",
                "asOf": "2026-07-24",
                "proposals": [
                    {
                        "identifier": "TEST-003",
                        "canonicalRecord": "areas/TEST/README.md",
                        "developmentLevel": "Admitted / undeveloped",
                        "workflowStatus": "Development",
                        "nextAudit": "Develop the issue",
                    },
                    {
                        "identifier": "TEST-004",
                        "canonicalRecord": "areas/TEST/issues/TEST-004.md",
                        "developmentLevel": "Admitted / undeveloped",
                        "workflowStatus": "Research",
                        "nextAudit": "Research the issue",
                    },
                    {
                        "identifier": "TEST-005",
                        "canonicalRecord": "areas/TEST/issues/TEST-005.md",
                        "developmentLevel": "Developed proposal",
                        "workflowStatus": "Audit needed",
                        "nextAudit": "Run the next audit",
                    },
                ],
            },
        )
        intake = self.path(
            "intake.json",
            {
                "generated_at": "2026-07-24T11:00:00Z",
                "pending": False,
                "items": [],
            },
        )
        chain = self.path(
            "chain.json",
            {
                "completed_at": "2026-07-24T11:00:00Z",
                "final_revision": "abc",
                "bots": [],
            },
        )

        queue = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            now=self.now,
            input_root=self.root,
        )

        self.assertTrue(queue["ready_for_elim"])
        self.assertTrue(queue["launch_recommended"])
        self.assertEqual(len(queue["items"]), 3)
        area_item = next(
            item
            for item in queue["items"]
            if item["source"]["identifier"] == "TEST-003"
        )
        self.assertEqual(
            area_item["source"]["canonicalRecord"],
            "areas/TEST/README.md",
        )
        self.assertIsNone(area_item["source"]["canonical_record_error"])
        missing_item = next(
            item
            for item in queue["items"]
            if item["source"]["identifier"] == "TEST-004"
        )
        self.assertIn(
            "canonicalRecord is missing",
            missing_item["source"]["canonical_record_error"],
        )

        selected = select_context_route(
            queue,
            {"elim_decision": {"profile": {"full_context": False}}},
        )
        self.assertEqual(selected["kind"], "issue_audit")
        self.assertEqual(
            selected["canonical_record"],
            "areas/TEST/issues/TEST-005.md",
        )

        area_route = select_context_route(
            {"items": [area_item]},
            {"elim_decision": {"profile": {"full_context": False}}},
        )
        self.assertEqual(area_route["issue"], "TEST-003")
        self.assertEqual(
            area_route["canonical_record"],
            "areas/TEST/README.md",
        )

        with self.assertRaisesRegex(ValueError, "no usable canonical record"):
            select_context_route(
                {"items": [missing_item]},
                {"elim_decision": {"profile": {"full_context": False}}},
            )

    def test_stale_or_revision_mismatched_inputs_block_launch(self):
        common = {"generated_at": "2026-01-01T00:00:00Z"}
        integrity = self.path("integrity.json", {**common, "revision": "a", "findings": []})
        progress = self.path(
            "progress.json", {**common, "repositoryRevision": "b", "proposals": []}
        )
        intake = self.path("intake.json", {**common, "items": []})
        chain = self.path(
            "chain.json", {**common, "final_revision": "c", "bots": []}
        )
        queue = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            now=self.now,
            input_root=self.root,
        )
        self.assertFalse(queue["ready_for_elim"])
        self.assertFalse(queue["launch_recommended"])
        self.assertTrue(any("revision" in problem for problem in queue["problems"]))

    def test_unavailable_fallback_input_blocks_launch(self):
        common = {"generated_at": "2026-07-24T11:00:00Z"}
        integrity = self.path(
            "integrity.json", {**common, "revision": "abc", "findings": []}
        )
        progress = self.path(
            "progress.json",
            {
                **common,
                "repositoryRevision": "abc",
                "proposals": [],
            },
        )
        intake = self.path(
            "intake.json",
            {
                **common,
                "collection_status": "unavailable",
                "pending": False,
                "items": [],
            },
        )
        chain = self.path(
            "chain.json",
            {
                **common,
                "final_revision": "abc",
                "bots": [],
            },
        )
        queue = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            now=self.now,
            input_root=self.root,
        )
        self.assertFalse(queue["ready_for_elim"])
        self.assertFalse(queue["launch_recommended"])
        self.assertIn("intake collection is unavailable", queue["problems"])


class ContextRouteTests(unittest.TestCase):
    def test_comprehensive_chain_overrides_ordinary_queue_priority(self):
        queue = {
            "items": [
                {
                    "id": "change-1",
                    "kind": "change_audit",
                    "eligible_for_elim": True,
                    "source": {
                        "identifier": "JUD-009",
                        "canonicalRecord": "areas/JUD/issues/JUD-009.md",
                    },
                },
                {
                    "id": "epoch-1",
                    "kind": "comprehensive_review",
                    "eligible_for_elim": True,
                    "source": {"identifier": "EPOCH-1"},
                },
            ]
        }
        chain = {
            "elim_decision": {"profile": {"full_context": True}}
        }
        route = select_context_route(queue, chain)
        self.assertEqual(route["profile"], "comprehensive_review")
        self.assertEqual(route["work_item_id"], "epoch-1")
        self.assertEqual(route["kind"], "comprehensive_review")
        self.assertIsNone(route["issue"])
        self.assertIsNone(route["canonical_record"])

    def test_full_context_chain_without_comprehensive_unit_fails_closed(self):
        queue = {
            "items": [
                {
                    "id": "change-1",
                    "kind": "change_audit",
                    "eligible_for_elim": True,
                }
            ]
        }
        chain = {
            "elim_decision": {"profile": {"full_context": True}}
        }
        with self.assertRaisesRegex(ValueError, "no eligible comprehensive"):
            select_context_route(queue, chain)

    def test_normal_chain_keeps_first_eligible_queue_item(self):
        queue = {
            "items": [
                {
                    "id": "change-1",
                    "kind": "change_audit",
                    "eligible_for_elim": True,
                    "source": {
                        "identifier": "JUD-009",
                        "canonicalRecord": "areas/JUD/issues/JUD-009.md",
                    },
                }
            ]
        }
        route = select_context_route(
            queue,
            {"elim_decision": {"profile": {"full_context": False}}},
        )
        self.assertEqual(route["profile"], "change_audit")
        self.assertEqual(route["issue"], "JUD-009")
        self.assertEqual(route["work_item_id"], "change-1")
        self.assertEqual(route["kind"], "change_audit")
        self.assertEqual(
            route["canonical_record"],
            "areas/JUD/issues/JUD-009.md",
        )

    def test_candidate_research_route_preserves_identity_without_issue_dossier(self):
        queue = {
            "items": [
                {
                    "id": "candidate-1",
                    "kind": "candidate_research",
                    "eligible_for_elim": True,
                    "source": {
                        "identifier": "HOR-035",
                        "canonicalRecord": "https://github.com/Thorncrag/ARRP/issues/255",
                    },
                }
            ]
        }
        route = select_context_route(
            queue,
            {"elim_decision": {"profile": {"full_context": False}}},
        )
        self.assertEqual(route["profile"], "candidate_research")
        self.assertEqual(route["work_item_id"], "candidate-1")
        self.assertEqual(route["kind"], "candidate_research")
        self.assertIsNone(route["issue"])
        self.assertEqual(
            route["canonical_record"],
            "https://github.com/Thorncrag/ARRP/issues/255",
        )


class RepositorySearchBoundaryTests(unittest.TestCase):
    def test_generated_console_and_local_artifacts_are_excluded_from_ordinary_search(self):
        policy = (ROOT / ".rgignore").read_text(encoding="utf-8")
        self.assertIn("research/horizon-review-console/catalog-data.js", policy)
        self.assertIn("research/horizon-review-console/data/", policy)
        self.assertIn(".site-build/", policy)
        self.assertIn(".tmp/", policy)
        self.assertIn(".venv/", policy)

    def test_production_context_routes_are_hash_pinned_and_extractable(self):
        path = ROOT / "framework/context-routes.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(raw["schema_version"], 2)
        self.assertTrue(
            {
                "framework_kernel",
                "agent_rules_kernel",
                "current_audit",
            }
            <= set(raw["required_modules"])
        )
        current_spec = raw["documents"]["current_audit"]
        self.assertEqual(
            current_spec["path"],
            "framework/logs/CURRENT_AUDIT.md",
        )
        self.assertEqual(current_spec["hash_policy"], "runtime")
        self.assertFalse(current_spec["governing"])
        self.assertTrue(
            {"framework_kernel", "agent_rules_kernel"}
            <= set(current_spec["requires"])
        )
        self.assertNotIn("sha256", current_spec)
        for document_id, document in raw["documents"].items():
            if document_id == "current_audit":
                continue
            self.assertEqual(document.get("hash_policy"), "pinned", document_id)
            self.assertRegex(
                document.get("sha256", ""),
                r"^[0-9a-f]{64}$",
                document_id,
            )

        manifest = load_route_manifest(path, root=ROOT)
        packets = {
            profile_name: build_context_packet(path, profile_name, root=ROOT)
            for profile_name in manifest["profiles"]
        }
        required = set(manifest["required_modules"])
        for profile_name, packet in packets.items():
            module_ids = {
                module["document"]
                for module in packet["modules"]
            }
            self.assertTrue(required <= module_ids, profile_name)
            self.assertLessEqual(
                packet["limits"]["actual_bytes"],
                packet["limits"]["max_bytes"],
                profile_name,
            )
            for section in packet["sections"]:
                route = next(
                    route
                    for route in manifest["profiles"][profile_name].get("sections", [])
                    if route["document"] == section["document"]
                    and route["heading"] == section["heading"]
                )
                self.assertLessEqual(section["bytes"], route["max_bytes"])

        current_module = next(
            module
            for module in packets["issue_development"]["modules"]
            if module["document"] == "current_audit"
        )
        self.assertEqual(current_module["hash_policy"], "runtime")
        self.assertEqual(
            current_module["sha256"],
            hashlib.sha256(
                (ROOT / "framework/logs/CURRENT_AUDIT.md").read_bytes()
            ).hexdigest(),
        )

        expected_profile_modules = {
            "integrity_reconciliation": {
                "audit_project_consistency",
                "project_structure",
                "agent_autonomous_execution",
                "agent_provenance_logging",
                "agent_validation_closeout",
            },
            "issue_development": {
                "method_scope_admission",
                "method_partisan_perception",
                "issue_architecture",
                "development_levels",
                "foundation_development_gates",
                "agent_issue_candidate_work",
                "github_workflow",
            },
            "issue_audit": {
                "audit_core",
                "audit_verification",
                "audit_tiered",
                "audit_legal_prior_proposal",
                "scoring_quality_rubric",
                "scoring_adoption_pathway",
                "scoring_external_international",
            },
            "change_audit": {
                "audit_change",
                "audit_project_consistency",
                "github_workflow",
            },
            "public_intake": {
                "intake_process",
                "method_scope_admission",
                "agent_issue_candidate_work",
                "github_workflow",
            },
            "github_sync": {
                "github_workflow",
                "navigation_inventory",
            },
        }
        for profile_name, expected_modules in expected_profile_modules.items():
            actual_modules = {
                module["document"]
                for module in packets[profile_name]["modules"]
            }
            self.assertTrue(
                expected_modules <= actual_modules,
                f"{profile_name}: missing {sorted(expected_modules - actual_modules)}",
            )

        governing = {
            document_id
            for document_id, document in manifest["documents"].items()
            if document.get("governing")
        }
        comprehensive_modules = {
            module["document"]
            for module in packets["comprehensive_review"]["modules"]
        }
        self.assertTrue(
            manifest["profiles"]["comprehensive_review"]["include_all_governing"]
        )
        self.assertTrue(governing <= comprehensive_modules)
        self.assertIn("current_audit", comprehensive_modules)

    def test_small_profiles_allow_additive_audit_capabilities_with_headroom(self):
        path = ROOT / "framework/context-routes.json"
        manifest = load_route_manifest(path, root=ROOT)
        profiles = ("integrity_reconciliation", "github_sync")
        capabilities = ("change_control", "tiered_quality_audit")

        for profile_name in profiles:
            self.assertEqual(
                manifest["profiles"][profile_name]["max_bytes"],
                400000,
            )
            for capability in capabilities:
                with self.subTest(profile=profile_name, capability=capability):
                    packet = build_context_packet(
                        path,
                        profile_name,
                        root=ROOT,
                        capabilities=(capability,),
                    )
                    module_ids = {
                        module["document"] for module in packet["modules"]
                    }
                    self.assertTrue(
                        set(manifest["capabilities"][capability]) <= module_ids
                    )
                    for module_id in module_ids:
                        self.assertTrue(
                            set(
                                manifest["documents"][module_id].get("requires")
                                or []
                            )
                            <= module_ids,
                            module_id,
                        )
                    self.assertLessEqual(
                        packet["limits"]["actual_bytes"],
                        packet["limits"]["max_bytes"],
                    )
                    self.assertGreaterEqual(
                        packet["limits"]["max_bytes"]
                        - packet["limits"]["actual_bytes"],
                        50000,
                    )

    def test_explicit_lower_packet_ceiling_still_fails_closed(self):
        path = ROOT / "framework/context-routes.json"
        with self.assertRaisesRegex(
            ContextError,
            r"context packet exceeds max bytes \(\d+ > 300000\)",
        ):
            build_context_packet(
                path,
                "integrity_reconciliation",
                root=ROOT,
                capabilities=("change_control",),
                max_total_bytes=300000,
            )


if __name__ == "__main__":
    unittest.main()
