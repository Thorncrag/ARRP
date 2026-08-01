import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from arrp_context import (  # noqa: E402
    ContextError,
    apply_user_overrides,
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
from elim_execution import merge_gap_obligation_state  # noqa: E402
from build_elim_context import (  # noqa: E402
    main as build_elim_context_main,
    parse_args as parse_build_elim_context_args,
)
import build_elim_context as build_elim_context_module  # noqa: E402
from component_registry import RegistryError, RoutingRuleFailure  # noqa: E402
import component_registry as component_registry_module  # noqa: E402
import path_authority as path_authority_module  # noqa: E402
from path_authority import ProjectPathAuthority  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class ExactContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
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

    def test_context_cli_uses_exact_repository_and_output_roots(self):
        output_root = self.root / "output"
        output_root.mkdir()
        output = output_root / "packet.json"
        authority = ProjectPathAuthority.fixture(
            self.root,
            repository_root=self.root,
            state_root=self.root,
            output_root=output_root,
        )
        stdout = io.StringIO()
        with (
            patch.object(
                build_elim_context_module,
                "load_validated_component_registry_routing_view",
            ) as registry_loader,
            redirect_stdout(stdout),
        ):
            return_code = build_elim_context_main(
                [
                    "--manifest",
                    str(self.manifest),
                    "--profile",
                    "issue",
                    "--output",
                    str(output),
                ],
                path_authority=authority,
            )
        self.assertEqual(return_code, 0, stdout.getvalue())
        registry_loader.assert_not_called()
        self.assertEqual(stdout.getvalue(), "")
        packet = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(packet["profile"], "issue")
        self.assertEqual(packet["manifest"]["path"], "manifest.json")

    def test_context_cli_rejects_output_outside_exact_output_root(self):
        output_root = self.root / "output"
        output_root.mkdir()
        outside = self.root / "outside.json"
        authority = ProjectPathAuthority.fixture(
            self.root,
            repository_root=self.root,
            state_root=self.root,
            output_root=output_root,
        )
        with redirect_stdout(io.StringIO()):
            return_code = build_elim_context_main(
                [
                    "--manifest",
                    str(self.manifest),
                    "--profile",
                    "issue",
                    "--output",
                    str(outside),
                ],
                path_authority=authority,
            )
        self.assertEqual(return_code, 2)
        self.assertFalse(outside.exists())

    def test_context_cli_rejects_nested_output_under_exact_output_root(self):
        output_root = self.root / "output"
        output_root.mkdir()
        nested = output_root / "nested" / "packet.json"
        authority = ProjectPathAuthority.fixture(
            self.root,
            repository_root=self.root,
            state_root=self.root,
            output_root=output_root,
        )
        with redirect_stdout(io.StringIO()):
            return_code = build_elim_context_main(
                [
                    "--manifest",
                    str(self.manifest),
                    "--profile",
                    "issue",
                    "--output",
                    str(nested),
                ],
                path_authority=authority,
            )
        self.assertEqual(return_code, 2)
        self.assertFalse(nested.exists())

    def test_context_cli_exposes_no_fixture_authority_switches(self):
        for arguments in (
            ["--fixture-root", str(self.root)],
            ["--path-authority", "fixture"],
            ["--component-registry", str(self.root / "registry.json")],
        ):
            with self.subTest(arguments=arguments), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    parse_build_elim_context_args(arguments)

    def test_context_injection_rejects_production_selectors(self):
        output_root = self.root / "output"
        output_root.mkdir()
        authority = ProjectPathAuthority.fixture(
            self.root,
            repository_root=self.root,
            state_root=self.root,
            output_root=output_root,
        )
        for arguments in (
            ["--input-root", str(self.root)],
            ["--output-root", str(output_root)],
            ["--path-authority", "repository-validation"],
        ):
            with self.subTest(arguments=arguments), redirect_stdout(io.StringIO()):
                self.assertEqual(
                    build_elim_context_main(
                        arguments,
                        path_authority=authority,
                    ),
                    2,
                )

    def test_context_injection_accepts_only_fixture_authority(self):
        authority = ProjectPathAuthority(
            "repository_validation",
            self.root,
            self.root,
            self.root,
        )
        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                build_elim_context_main([], path_authority=authority),
                2,
            )

    def _production_transaction_paths(
        self,
        base: Path,
    ) -> tuple[Path, Path, Path, Path]:
        state = base / "state"
        worktrees = state / "worktrees"
        runs = state / "runs"
        worktree = worktrees / "run-1"
        run = runs / "run-1"
        state.mkdir(mode=0o700)
        worktrees.mkdir(mode=0o700)
        runs.mkdir(mode=0o700)
        shutil.copytree(self.root, worktree)
        run.mkdir(mode=0o700)
        registry = worktree / "framework/component-registry.json"
        registry.write_text("{}\n", encoding="utf-8")
        return state, worktree, run, registry

    def test_production_transaction_cli_rejects_predecessor_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            state, worktree, run, _registry = self._production_transaction_paths(
                base
            )
            output = run / "packet.json"
            with (
                patch.object(
                    path_authority_module,
                    "APPROVED_STATE_ROOT",
                    state,
                ),
                patch.object(
                    build_elim_context_module,
                    "load_validated_component_registry_routing_view",
                ) as registry_loader,
                redirect_stdout(io.StringIO()),
            ):
                return_code = build_elim_context_main(
                    [
                        "--path-authority",
                        "production-transaction",
                        "--input-root",
                        str(worktree),
                        "--output-root",
                        str(run),
                        "--manifest",
                        str(worktree / "manifest.json"),
                        "--profile",
                        "issue",
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(return_code, 2)
            registry_loader.assert_not_called()
            blocked = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(blocked["status"], "blocked")
            self.assertIn(
                "forbids predecessor --manifest routing",
                blocked["error"],
            )

    def test_production_transaction_cli_uses_active_registry_view(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            state, worktree, run, _registry = self._production_transaction_paths(
                base
            )
            output = run / "packet.json"
            active_view = {
                "schema_version": 2,
                "validation_mode": "live_authority_validation",
                "authoritative": True,
                "executable": True,
                "live_authority_verified": True,
                "activation_receipt_consulted": True,
                "predecessor_route_consulted": False,
            }
            packet = {
                "schema_version": 2,
                "profile": "issue",
                "routing_authority": "component-registry",
            }
            with (
                patch.object(
                    path_authority_module,
                    "APPROVED_STATE_ROOT",
                    state,
                ),
                patch.object(
                    build_elim_context_module,
                    "load_validated_component_registry_routing_view",
                    return_value=active_view,
                ) as registry_loader,
                patch.object(
                    build_elim_context_module,
                    "build_context_packet_from_view",
                    return_value=packet,
                ) as packet_builder,
                redirect_stdout(io.StringIO()),
            ):
                return_code = build_elim_context_main(
                    [
                        "--path-authority",
                        "production-transaction",
                        "--input-root",
                        str(worktree),
                        "--output-root",
                        str(run),
                        "--profile",
                        "issue",
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(return_code, 0)
            registry_loader.assert_called_once()
            authority = registry_loader.call_args.args[0]
            self.assertIsInstance(authority, ProjectPathAuthority)
            self.assertEqual(authority.mode, "production_transaction")
            self.assertEqual(authority.repository_root, worktree)
            self.assertEqual(authority.state_root, state)
            self.assertEqual(authority.output_root, run)
            self.assertIs(packet_builder.call_args.args[0], active_view)
            self.assertEqual(packet_builder.call_args.args[1], "issue")
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")),
                packet,
            )

    def test_production_transaction_cli_blocks_candidate_registry_view(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            state, worktree, run, _registry = self._production_transaction_paths(
                base
            )
            output = run / "packet.json"
            candidate_view = {
                "schema_version": 2,
                "validation_mode": "proposed_revision_validation",
                "authoritative": False,
                "executable": False,
                "live_authority_verified": False,
                "activation_receipt_consulted": False,
                "predecessor_route_consulted": False,
            }
            with (
                patch.object(
                    path_authority_module,
                    "APPROVED_STATE_ROOT",
                    state,
                ),
                patch.object(
                    build_elim_context_module,
                    "load_validated_component_registry_routing_view",
                    return_value=candidate_view,
                ),
                patch.object(
                    build_elim_context_module,
                    "build_context_packet_from_view",
                ) as packet_builder,
                redirect_stdout(io.StringIO()),
            ):
                return_code = build_elim_context_main(
                    [
                        "--path-authority",
                        "production-transaction",
                        "--input-root",
                        str(worktree),
                        "--output-root",
                        str(run),
                        "--profile",
                        "issue",
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(return_code, 2)
            packet_builder.assert_not_called()
            blocked = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(blocked["status"], "blocked")
            self.assertIn(
                "requires active Component Registry routing",
                blocked["error"],
            )

    def test_production_transaction_cli_preserves_safe_readback_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            state, worktree, run, _registry = self._production_transaction_paths(
                base
            )
            output = run / "packet.json"
            with (
                patch.object(
                    path_authority_module,
                    "APPROVED_STATE_ROOT",
                    state,
                ),
                patch.object(
                    build_elim_context_module,
                    "load_validated_component_registry_routing_view",
                    side_effect=RegistryError(
                        "active registry lacks authenticated activation readback"
                    ),
                ),
                patch.object(
                    build_elim_context_module,
                    "build_context_packet_from_view",
                ) as packet_builder,
                redirect_stdout(io.StringIO()),
            ):
                return_code = build_elim_context_main(
                    [
                        "--path-authority",
                        "production-transaction",
                        "--input-root",
                        str(worktree),
                        "--output-root",
                        str(run),
                        "--profile",
                        "issue",
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(return_code, 2)
            packet_builder.assert_not_called()
            blocked = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(blocked["status"], "blocked")
            self.assertEqual(
                blocked["error"],
                "active registry lacks authenticated activation readback",
            )

    def test_production_transaction_cli_preserves_typed_routing_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            state, worktree, run, _registry = self._production_transaction_paths(
                base
            )
            output = run / "packet.json"
            active_view = {
                "schema_version": 2,
                "validation_mode": "live_authority_validation",
                "authoritative": True,
                "executable": True,
                "live_authority_verified": True,
                "activation_receipt_consulted": True,
                "predecessor_route_consulted": False,
            }
            failure = RoutingRuleFailure(
                failure_code="CTXR_PACKET_BUDGET_EXCEEDED",
                phase="packet_build",
                rule_ids=("ctxr.fail.packet_budget_exceeded",),
                message="Component Registry context packet exceeded its ceiling",
            )
            with (
                patch.object(
                    path_authority_module,
                    "APPROVED_STATE_ROOT",
                    state,
                ),
                patch.object(
                    build_elim_context_module,
                    "load_validated_component_registry_routing_view",
                    return_value=active_view,
                ),
                patch.object(
                    build_elim_context_module,
                    "build_context_packet_from_view",
                    side_effect=failure,
                ),
                redirect_stdout(io.StringIO()),
            ):
                return_code = build_elim_context_main(
                    [
                        "--path-authority",
                        "production-transaction",
                        "--input-root",
                        str(worktree),
                        "--output-root",
                        str(run),
                        "--profile",
                        "issue",
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(return_code, 2)
            blocked = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(blocked["status"], "blocked")
            self.assertEqual(
                blocked["routing_failure"],
                failure.safe_evidence(),
            )

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

    def test_explicit_fixture_never_falls_back_to_owner_local_logs(self):
        state = self.root / "fixture-state"
        state.mkdir()
        authority = ProjectPathAuthority.fixture(
            self.root,
            repository_root=self.root,
            state_root=state,
        )
        packet = build_context_packet(
            self.manifest,
            "issue",
            root=self.root,
            path_authority=authority,
        )
        self.assertEqual(packet.get("logs", {}), {})

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

    def test_repository_file_rejects_wrong_case_alias_on_case_insensitive_filesystems(self):
        exact = self.root / "areas/TEST/issues/Case-Alias.md"
        exact.write_text("exact\n", encoding="utf-8")
        relative_alias = "areas/TEST/issues/case-alias.md"
        alias = self.root / relative_alias

        if alias.exists():
            with self.assertRaisesRegex(ContextError, "exact repository entry spelling"):
                repository_file(self.root, relative_alias)
        else:
            self.assertIsNone(
                repository_file(self.root, relative_alias, required=False)
            )

    def test_repository_file_never_suppresses_optional_path_inspection_errors(self):
        with patch(
            "arrp_context.os.listdir",
            side_effect=PermissionError("inspection denied"),
        ):
            with self.assertRaisesRegex(ContextError, "cannot inspect repository file"):
                repository_file(
                    self.root,
                    "areas/TEST/issues/TEST-001.md",
                    required=False,
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

    def quiet_inputs(self) -> tuple[Path, Path, Path, Path]:
        common = {"generated_at": "2026-07-24T11:00:00Z"}
        return (
            self.path(
                "integrity.json",
                {**common, "revision": "abc", "findings": []},
            ),
            self.path(
                "progress.json",
                {**common, "repositoryRevision": "abc", "proposals": []},
            ),
            self.path(
                "intake.json",
                {**common, "pending": False, "items": []},
            ),
            self.path(
                "chain.json",
                {
                    **common,
                    "chain_id": "fresh-chain",
                    "final_revision": "abc",
                    "bots": [],
                },
            ),
        )

    def gap_state(self, *, authority_disposition: str = "permitted") -> dict:
        result = {
            "run_id": "chain-prior",
            "unit_id": "selected-gap-prior",
            "files_touched": ["framework/records/automation/elim-run-log.md"],
            "discovered_work_units": [
                {
                    "id": "DISC-1",
                    "obligation_id": "GAP-1",
                    "domain": "automation",
                    "discovery_context": "Project governance review and discovery.",
                    "observed_at": "2026-07-24T11:30:00+00:00",
                    "source_revision": "a" * 40,
                    "evidence": ["A canonical route lacks an accountable owner."],
                    "reasoning": "The omission prevents deterministic stewardship.",
                    "uncertainty": None,
                    "affected_records": ["framework/project/automation/context-routes.json"],
                    "consequence": "The route gap may leave work undiscovered.",
                    "authority": {
                        "classification": "delegated_judgment",
                        "basis": "Elim governance-discovery runbook.",
                        "disposition": authority_disposition,
                    },
                    "action_rationale": (
                        "Repair the route."
                        if authority_disposition == "permitted"
                        else "Retain evidence without implementing the prohibited change."
                    ),
                    "changed_files": ["framework/records/automation/elim-run-log.md"],
                    "affected_surfaces": ["repository", "automation", "console"],
                    "validation_readback": [
                        {
                            "check": "canonical detail readback",
                            "status": "passed",
                            "evidence": "The Run Log detail was read back.",
                        }
                    ],
                    "disposition": "reported",
                    "canonical_detail": "framework/records/automation/elim-run-log.md",
                    "provenance": ["framework/records/automation/elim-run-log.md#gap-1"],
                    "owner": "Elim",
                    "next_action": "Recheck the route and apply only an authorized repair.",
                    "next_trigger": "The route or authority record changes.",
                    "outside_contribution": None,
                }
            ],
            "gap_obligation_updates": [
                {
                    "obligation_id": "GAP-1",
                    "discovered_work_unit_id": "DISC-1",
                    "status": "open",
                    "observed_at": "2026-07-24T11:30:00+00:00",
                    "resolution": None,
                }
            ],
        }
        return merge_gap_obligation_state(None, result)

    def governance_review_state(self, reviewed_at: str) -> dict:
        result = {
            "run_id": "chain-governance-prior",
            "unit_id": "governance-review-prior",
            "files_touched": ["framework/records/automation/elim-run-log.md"],
            "discovered_work_units": [
                {
                    "id": "DISC-governance-control",
                    "obligation_id": None,
                    "domain": "project-governance-review",
                    "discovery_context": "Completed the minimum governance domains.",
                    "observed_at": reviewed_at,
                    "source_revision": "b" * 40,
                    "evidence": ["All minimum domains were reviewed at the pinned boundary."],
                    "reasoning": "No material defect was established.",
                    "uncertainty": None,
                    "affected_records": ["framework/records/automation/elim-run-log.md"],
                    "consequence": "The quiet-queue review is current for its cadence.",
                    "authority": {
                        "classification": "delegated_judgment",
                        "basis": "Elim governance-discovery runbook.",
                        "disposition": "permitted",
                    },
                    "action_rationale": "Record a clean review without inventing work.",
                    "changed_files": ["framework/records/automation/elim-run-log.md"],
                    "affected_surfaces": ["repository", "automation", "console"],
                    "validation_readback": [
                        {
                            "check": "governance review record",
                            "status": "passed",
                            "evidence": "The canonical Run Log record was read back.",
                        }
                    ],
                    "disposition": "no_material_finding",
                    "canonical_detail": "framework/records/automation/elim-run-log.md",
                    "provenance": ["framework/records/automation/elim-run-log.md#governance-review"],
                    "owner": "Elim",
                    "next_action": "Wait for the next due governance review.",
                    "next_trigger": "The 168-hour minimum interval elapses.",
                    "outside_contribution": None,
                }
            ],
            "gap_obligation_updates": [],
        }
        return merge_gap_obligation_state(None, result)

    def test_quiet_queue_synthesizes_project_governance_discovery(self):
        integrity, progress, intake, chain = self.quiet_inputs()
        queue = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            now=self.now,
            input_root=self.root,
        )
        selected = next(
            item
            for item in queue["items"]
            if item["id"] == queue["selected_work_item_id"]
        )
        self.assertEqual(selected["work_class"], "governance_discovery")
        self.assertTrue(selected["governance_discovery_mode"])
        self.assertEqual(
            selected["source"]["finding_type"],
            "project_governance_review_and_discovery",
        )
        self.assertTrue(queue["launch_recommended"])

    def test_queue_revision_comes_from_explicit_repository_root(self):
        integrity, progress, intake, chain = self.quiet_inputs()
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=self.root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        subprocess.run(
            ["git", "config", "user.name", "ARRP Queue Fixture"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "queue@example.invalid"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Queue fixture"],
            cwd=self.root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()

        queue = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            now=self.now,
            input_root=self.root,
            repository_root=self.root,
        )

        self.assertEqual(queue["repository_revision"], revision)

    def test_clean_governance_review_is_visible_but_not_immediately_reselected(self):
        integrity, progress, intake, chain = self.quiet_inputs()
        gaps = self.path(
            "gap-obligations.json",
            self.governance_review_state("2026-07-24T11:30:00+00:00"),
        )
        current = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            gap_obligations_path=gaps,
            now=self.now,
            input_root=self.root,
        )
        self.assertFalse(current["launch_recommended"])
        self.assertTrue(current["governance_discovery"]["current_for_cadence"])
        self.assertEqual(
            current["governance_discovery"]["last_review"]["disposition"],
            "no_material_finding",
        )
        self.assertEqual(current["counts"]["governance_discovery"], 0)

        due = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            gap_obligations_path=gaps,
            now=datetime(2026, 8, 1, 12, tzinfo=timezone.utc),
            max_age_hours=240,
            input_root=self.root,
        )
        self.assertTrue(due["launch_recommended"])
        self.assertEqual(due["counts"]["governance_discovery"], 1)

    def test_queue_cli_reconstructs_governance_state_when_cache_is_missing(self):
        integrity, progress, intake, chain = self.quiet_inputs()
        config = self.root / ".github/run-coordinator-bot.json"
        config.parent.mkdir(parents=True, exist_ok=True)
        write_json(
            config,
            {
                "governanceDiscovery": {
                    "enabled": True,
                    "mode": "Project governance review and discovery",
                    "ordinarySelectionPolicy": "after-ordinary-queue-clears",
                    "minimumIntervalHours": 168,
                }
            },
        )
        run_log = self.root / "framework/records/automation/elim-run-log.md"
        run_log.parent.mkdir(parents=True, exist_ok=True)
        from elim_execution import render_discovery_markers  # noqa: E402

        run_log.write_text(
            "# Elim Run Log\n\n"
            + render_discovery_markers(
                {
                    "run_id": "chain-governance-prior",
                    "unit_id": "governance-review-prior",
                    "files_touched": ["framework/records/automation/elim-run-log.md"],
                    "discovered_work_units": [
                        {
                            "id": "DISC-governance-control",
                            "obligation_id": None,
                            "domain": "project-governance-review",
                            "discovery_context": "Reviewed every minimum domain.",
                            "observed_at": "2026-07-24T11:30:00+00:00",
                            "source_revision": "b" * 40,
                            "evidence": ["The complete minimum domain list was reviewed."],
                            "reasoning": "No material defect was established.",
                            "uncertainty": None,
                            "affected_records": ["framework/records/automation/elim-run-log.md"],
                            "consequence": "The review is current for its cadence.",
                            "authority": {
                                "classification": "delegated_judgment",
                                "basis": "Elim governance-discovery runbook.",
                                "disposition": "permitted",
                            },
                            "action_rationale": "Record a clean review.",
                            "changed_files": ["framework/records/automation/elim-run-log.md"],
                            "affected_surfaces": [
                                "repository",
                                "automation",
                                "console",
                            ],
                            "validation_readback": [
                                {
                                    "check": "review record",
                                    "status": "passed",
                                    "evidence": "The Run Log record was read back.",
                                }
                            ],
                            "disposition": "no_material_finding",
                            "canonical_detail": "framework/records/automation/elim-run-log.md",
                            "provenance": [
                                "framework/records/automation/elim-run-log.md#governance"
                            ],
                            "owner": "Elim",
                            "next_action": "Wait for the next due review.",
                            "next_trigger": "The 168-hour interval elapses.",
                            "outside_contribution": None,
                        }
                    ],
                    "gap_obligation_updates": [],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/build_elim_work_queue.py"),
                "--input-root",
                str(self.root),
                "--integrity",
                str(integrity),
                "--progress",
                str(progress),
                "--intake",
                str(intake),
                "--chain",
                str(chain),
                "--as-of",
                "2026-07-24T12:00:00+00:00",
                "--output",
                str(self.root / "queue.json"),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "")
        queue = json.loads((self.root / "queue.json").read_text())
        self.assertTrue(queue["governance_discovery"]["current_for_cadence"])
        self.assertEqual(
            queue["governance_discovery"]["minimum_interval_hours"],
            168,
        )
        reconstructed = chain.parent / "gap-obligations-reconstructed.json"
        self.assertTrue(reconstructed.is_file())
        self.assertEqual(
            json.loads(reconstructed.read_text())["governance_review"]["disposition"],
            "no_material_finding",
        )

    def test_one_remaining_ordinary_item_runs_before_governance_review(self):
        integrity, progress, intake, chain = self.quiet_inputs()
        write_json(
            integrity,
            {
                "generated_at": "2026-07-24T11:00:00Z",
                "revision": "abc",
                "findings": [
                    {
                        "id": "ordinary-integrity-1",
                        "severity": "warning",
                        "attention": "agent",
                        "message": "One ordinary repair remains.",
                    }
                ],
            },
        )
        ordinary = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            now=self.now,
            input_root=self.root,
        )
        selected = next(
            item
            for item in ordinary["items"]
            if item["id"] == ordinary["selected_work_item_id"]
        )
        self.assertNotEqual(selected.get("work_class"), "governance_discovery")
        self.assertEqual(ordinary["counts"]["governance_discovery"], 0)
        self.assertEqual(
            ordinary["governance_discovery"]["reason"],
            "Ordinary eligible work remains and is selected first.",
        )

        write_json(
            integrity,
            {
                "generated_at": "2026-07-24T11:00:00Z",
                "revision": "abc",
                "findings": [],
            },
        )
        after_clear = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            now=self.now,
            input_root=self.root,
        )
        selected = next(
            item
            for item in after_clear["items"]
            if item["id"] == after_clear["selected_work_item_id"]
        )
        self.assertEqual(selected["work_class"], "governance_discovery")

    def test_gap_queue_is_a_compact_link_projection_and_respects_prohibition(self):
        integrity, progress, intake, chain = self.quiet_inputs()
        gaps = self.path(
            "gap-obligations.json",
            self.gap_state(authority_disposition="forbidden"),
        )
        queue = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            gap_obligations_path=gaps,
            now=self.now,
            input_root=self.root,
        )
        gap = next(
            item for item in queue["items"] if item.get("work_class") == "gap_stewardship"
        )
        self.assertFalse(gap["eligible_for_elim"])
        self.assertIn("forbidden", gap["eligibility_reason"])
        self.assertIn("obligation_projection", gap["source"])
        self.assertNotIn("evidence", gap["source"])
        self.assertNotIn("reasoning", gap["source"])
        self.assertNotIn("consequence", gap["source"])
        selected = next(
            item
            for item in queue["items"]
            if item["id"] == queue["selected_work_item_id"]
        )
        self.assertEqual(selected["work_class"], "governance_discovery")

    def test_pending_run_log_reconciliation_is_selected_as_safety_zero(self):
        common = {"generated_at": "2026-07-24T11:00:00Z"}
        integrity = self.path(
            "integrity.json",
            {**common, "revision": "abc", "findings": []},
        )
        progress = self.path(
            "progress.json",
            {**common, "repositoryRevision": "abc", "proposals": []},
        )
        intake = self.path(
            "intake.json",
            {**common, "pending": False, "items": []},
        )
        chain = self.path(
            "chain.json",
            {
                **common,
                "chain_id": "fresh-chain",
                "final_revision": "abc",
                "bots": [],
            },
        )
        reconciliation = self.path(
            "run-log-reconciliation.json",
            {
                "schema_version": 1,
                "updated_at": "2026-07-24T11:30:00Z",
                "items": [
                    {
                        "chain_id": "failed-chain",
                        "invocation_id": "failed-chain-20260724T110000Z",
                        "recorded_at": "2026-07-24T11:05:00Z",
                        "failure_stage": "elim-execution",
                        "reason_code": "post-spawn-interruption",
                        "artifacts": {
                            "output": ".tmp/run-coordinator/failed-chain/output.jsonl"
                        },
                    }
                ],
            },
        )
        queue = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            run_log_reconciliation_path=reconciliation,
            now=self.now,
            input_root=self.root,
        )
        selected = queue["items"][0]
        self.assertEqual(selected["kind"], "bot_failure")
        self.assertEqual(selected["safety_class"], 0)
        self.assertEqual(
            selected["source"]["input"],
            "run_log_reconciliation",
        )
        self.assertEqual(
            selected["source"]["pending_chain_ids"],
            ["failed-chain"],
        )
        self.assertEqual(queue["selected_work_item_id"], selected["id"])
        self.assertTrue(queue["launch_recommended"])

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
                "chain_id": "queue-contract-chain",
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
                        "source_revision": hashlib.sha256(
                            progress.read_bytes()
                        ).hexdigest(),
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
        self.assertEqual(development["schema_version"], 1)
        self.assertEqual(development["source_chain_id"], "queue-contract-chain")
        self.assertEqual(development["source_commit"], "abc")
        self.assertTrue(
            development["source_project_snapshot"].startswith("sha256:")
        )
        self.assertEqual(development["work_class"], "development")
        self.assertEqual(development["required_authority"], "human")
        self.assertEqual(
            development["required_context_profile"], "issue_development"
        )
        self.assertEqual(development["retry_state"]["attempt_count"], 3)
        self.assertIn(
            "areas/TEST/issues/TEST-001.md",
            development["dependencies"],
        )
        self.assertTrue(development["blocking_reason"])
        self.assertTrue(development["source_input_hashes"]["progress"].startswith("sha256:"))

    def test_blank_or_stale_recovery_revision_cannot_suppress_current_work(self):
        issue_directory = self.root / "areas/TEST/issues"
        issue_directory.mkdir(parents=True)
        issue = issue_directory / "TEST-001.md"
        issue.write_text("# TEST-001\n", encoding="utf-8")
        common = {"generated_at": "2026-07-24T11:00:00Z"}
        integrity = self.path(
            "integrity.json",
            {**common, "revision": "abc", "findings": []},
        )
        progress = self.path(
            "progress.json",
            {
                **common,
                "repositoryRevision": "abc",
                "proposals": [
                    {
                        "identifier": "TEST-001",
                        "canonicalRecord": "areas/TEST/issues/TEST-001.md",
                        "developmentLevel": "In development",
                        "workflowStatus": "Development",
                        "nextAudit": "Continue drafting",
                    }
                ],
            },
        )
        intake = self.path(
            "intake.json",
            {**common, "pending": False, "items": []},
        )
        chain = self.path(
            "chain.json",
            {
                **common,
                "chain_id": "recovery-freshness-chain",
                "final_revision": "abc",
                "bots": [],
            },
        )
        work_id = stable_work_id("issue_development", "TEST-001")
        for label, revision in (("blank", ""), ("mismatched", "stale-revision")):
            with self.subTest(label=label):
                recovery = self.path(
                    "recovery.json",
                    {
                        **common,
                        "items": [
                            {
                                "work_id": work_id,
                                "state": "complete",
                                "attempt_count": 1,
                                "source_revision": revision,
                            }
                        ],
                    },
                )
                queue = build_work_queue(
                    integrity_path=integrity,
                    progress_path=progress,
                    intake_path=intake,
                    chain_path=chain,
                    recovery_path=recovery,
                    now=self.now,
                    input_root=self.root,
                )
                item = next(row for row in queue["items"] if row["id"] == work_id)
                self.assertTrue(item["eligible_for_elim"])
                self.assertIsNone(item["recovery"])
                self.assertEqual(item["retry_state"]["state"], "new")

    def test_chain_due_state_creates_forced_or_off_cycle_epoch_unit(self):
        common = {"generated_at": "2026-07-24T11:00:00Z"}
        integrity = self.path(
            "integrity.json",
            {**common, "revision": "abc", "findings": []},
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
            {**common, "pending": False, "items": []},
        )
        chain = self.path(
            "chain.json",
            {
                **common,
                "chain_id": "chain-off-cycle",
                "final_revision": "abc",
                "bots": [],
                "review_epoch": {
                    "due": True,
                    "due_reason": "governing_boundary_changed",
                    "boundary_changes": {
                        "missing": ["framework/new.md"],
                        "extra": [],
                        "mismatched": [],
                    },
                },
            },
        )
        epoch = self.path(
            "epoch.json",
            {
                **common,
                "epoch_id": "epoch-chain-off-cycle",
                "next_due_at": "2026-08-07T00:00:00Z",
                "unresolved_ids": ["FINDING-1"],
            },
        )
        queue = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            review_epoch_path=epoch,
            now=self.now,
            input_root=self.root,
        )
        unit = next(
            item
            for item in queue["items"]
            if item["kind"] == "comprehensive_review"
        )
        self.assertEqual(unit["reason"], "governing_boundary_changed")
        self.assertEqual(
            unit["source"]["boundary_changes"]["missing"],
            ["framework/new.md"],
        )
        self.assertTrue(queue["review_epoch"]["due"])

    def test_typed_bot_reports_create_exact_queue_items(self):
        common = {"generated_at": "2026-07-24T11:00:00Z"}
        integrity = self.path(
            "integrity.json",
            {**common, "revision": "abc", "findings": []},
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
            {**common, "pending": False, "items": []},
        )
        chain = self.path(
            "chain.json",
            {
                **common,
                "chain_id": "typed-input-chain",
                "final_revision": "abc",
                "bots": [],
                "stages": [
                    {"id": "source-checker-bot", "due": False, "status": "not_due"},
                    {"id": "case-monitor-bot", "due": False, "status": "not_due"},
                    {
                        "id": "presidential-directives-bot",
                        "due": False,
                        "status": "not_due",
                    },
                ],
            },
        )
        source_checker = self.path(
            "source-checker.json",
            {
                "checked_at": "2026-07-24T11:00:00Z",
                "results": [
                    {
                        "source_id": "SRC-0001",
                        "catalog": "inventory/sources.csv",
                        "classification": "broken",
                    },
                    {
                        "source_id": "SRC-0002",
                        "catalog": "inventory/sources.csv",
                        "classification": "verified",
                    },
                ],
            },
        )
        case_monitor = self.path(
            "case-monitor.json",
            {
                "checked_at": "2026-07-24T11:00:00Z",
                "changes": [
                    {
                        "kind": "changed",
                        "stable_key": "docket-1",
                        "case_name": "Example v. Agency",
                        "tracker_status": "Pending",
                        "last_case_update": "2026-07-24",
                        "changed_fields": ["tracker_status"],
                    }
                ],
                "source_development_modules": [
                    {
                        "module_id": "test-module",
                        "record_id": "HOR-035",
                        "target_path": (
                            "research/candidate-source-development/"
                            "HOR-035-source-development.md"
                        ),
                        "added_lead_ids": ["CASELEAD-ABCDEF012345"],
                    }
                ],
            },
        )
        directives = self.path(
            "directives.json",
            {
                "generated_at": "2026-07-24T11:00:00Z",
                "directives": [
                    {
                        "Directive ID": "2026-00001",
                        "Title": "Example directive",
                        "Bot Status": "new",
                        "Content Fingerprint": "f" * 64,
                    },
                    {
                        "Directive ID": "2026-00002",
                        "Title": "Unchanged directive",
                        "Bot Status": "unchanged",
                    },
                ],
            },
        )
        queue = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            source_checker_path=source_checker,
            case_monitor_path=case_monitor,
            presidential_directives_path=directives,
            now=self.now,
            input_root=self.root,
        )
        typed = [
            item["source"]["finding_type"]
            for item in queue["items"]
            if item["source"].get("finding_type")
        ]
        self.assertCountEqual(
            typed,
            [
                "source_checker",
                "case_monitor_change",
                "case_monitor_lead",
                "presidential_directive",
            ],
        )
        self.assertTrue(queue["ready_for_elim"])
        self.assertEqual(
            queue["selected_work_item_id"],
            queue["items"][0]["id"],
        )

    def test_complete_source_domain_proposal_is_one_elim_unit_until_recommended(self):
        common = {"generated_at": "2026-07-24T11:00:00Z"}
        integrity = self.path(
            "integrity.json",
            {**common, "revision": "abc", "findings": []},
        )
        progress = self.path(
            "progress.json",
            {**common, "repositoryRevision": "abc", "proposals": []},
        )
        intake = self.path(
            "intake.json",
            {**common, "pending": False, "items": []},
        )
        chain = self.path(
            "chain.json",
            {
                **common,
                "chain_id": "source-domain-chain",
                "final_revision": "abc",
                "stages": [
                    {
                        "id": "presidential-directives-bot",
                        "due": True,
                        "status": "succeeded",
                    }
                ],
            },
        )
        head = "a" * 40
        affected = [
            {
                "record_type": "presidential-directive",
                "record_id": f"2026-{index:05d}",
            }
            for index in range(1, 11)
        ]
        directives = self.path(
            "directives.json",
            {
                **common,
                "directives": [
                    {
                        "Directive ID": "2026-00001",
                        "Title": "Latest-run change only",
                        "Bot Status": "changed",
                    }
                ],
                "pending_proposal": {
                    "event_id": "SDE-1234567890ABCDEF12345678",
                    "agent_id": "presidential-directives-bot",
                    "proposal": {
                        "repository": "Thorncrag/ARRP",
                        "base_ref": "main",
                        "head_ref": "automation/presidential-directives-monitor",
                        "pull_request_number": 9,
                        "pull_request_url": "https://github.com/Thorncrag/ARRP/pull/9",
                        "proposal_revision": head,
                    },
                    "affected_records": affected,
                    "summary": {
                        "status": "presidential directives proposal delta",
                        "affected_record_count": 10,
                        "counts": {
                            "affected-files": 1,
                            "affected-records": 10,
                            "presidential-directive-records": 10,
                        },
                    },
                },
            },
        )
        recommendation_text = f"""# Source Monitor Log

## 2026-07-24T11:30:00Z — Repository review recommendation SMR-20260724-PR9

- Recommendation ID: `SMR-20260724-PR9`
- Recorded at: `2026-07-24T11:30:00Z`
- Reviewer: Elim
- Pull request number: `9`
- Pull request URL: `https://github.com/Thorncrag/ARRP/pull/9`
- Head revision: `{head}`
- Proposal event ID: `SDE-1234567890ABCDEF12345678`
- Recommended disposition: Hold for the owner-gated merge decision.
- Rationale: The exact head was reviewed against all ten primary records.
- Affected records: 10 directives.
- Confidence and uncertainty: High confidence; final acceptance remains owner-gated.
- Action owner: Human
- Human question: Approve the exact reviewed head for merge?
- Reassessment trigger: Any head change invalidates this recommendation.
"""
        untrusted_log = self.root / "framework/logs/sources/source-monitor-log.md"
        untrusted_log.parent.mkdir(parents=True)
        untrusted_log.write_text(recommendation_text, encoding="utf-8")
        runtime_root = self.root / "reviewed-runtime"
        with patch("arrp_context.ROOT", runtime_root):
            queue = build_work_queue(
                integrity_path=integrity,
                progress_path=progress,
                intake_path=intake,
                chain_path=chain,
                presidential_directives_path=directives,
                now=self.now,
                input_root=self.root,
            )
        source_items = [
            item
            for item in queue["items"]
            if item["source"].get("finding_type") == "source_domain_proposal"
        ]
        self.assertEqual(len(source_items), 1)
        self.assertIn("10 affected records", source_items[0]["title"])
        self.assertFalse(
            any(
                item["source"].get("finding_type") == "presidential_directive"
                for item in queue["items"]
            )
        )

        source_log = runtime_root / "framework/logs/sources/source-monitor-log.md"
        source_log.parent.mkdir(parents=True)
        source_log.write_text(recommendation_text, encoding="utf-8")
        with patch("arrp_context.ROOT", runtime_root):
            recommended_queue = build_work_queue(
                integrity_path=integrity,
                progress_path=progress,
                intake_path=intake,
                chain_path=chain,
                presidential_directives_path=directives,
                now=self.now,
                input_root=self.root,
            )
        self.assertFalse(
            any(
                item["source"].get("finding_type") == "source_domain_proposal"
                for item in recommended_queue["items"]
            )
        )

    def test_recovery_and_user_override_apply_before_exact_selection(self):
        first = {
            "id": "INTEGRITY-FIRST",
            "kind": "integrity",
            "eligible_for_elim": True,
            "requires_human": False,
            "safety_class": 1,
            "priority_score": 900,
            "selection_priority_score": 900,
            "age_days": 0,
        }
        second = {
            "id": "INTEGRITY-SECOND",
            "kind": "integrity",
            "eligible_for_elim": True,
            "requires_human": False,
            "safety_class": 1,
            "priority_score": 800,
            "selection_priority_score": 800,
            "age_days": 0,
        }
        ordered, applied, unmatched = apply_user_overrides(
            [first, second],
            {
                "INTEGRITY-FIRST": {
                    "source": "user-local-console",
                    "suppressed": True,
                    "reason": "Wait for a source refresh.",
                },
                "INTEGRITY-SECOND": {
                    "source": "user-local-console",
                    "priority": "critical",
                },
                "INTEGRITY-MISSING": {
                    "source": "user-local-console",
                    "priority": "low",
                },
            },
        )
        self.assertEqual(ordered[0]["id"], "INTEGRITY-SECOND")
        self.assertFalse(
            next(
                item
                for item in ordered
                if item["id"] == "INTEGRITY-FIRST"
            )["eligible_for_elim"]
        )
        self.assertEqual(
            applied,
            ["INTEGRITY-FIRST", "INTEGRITY-SECOND"],
        )
        self.assertEqual(unmatched, ["INTEGRITY-MISSING"])

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
                "chain_id": "candidate-research-chain",
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
                "chain_id": "canonical-record-chain",
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
    def test_route_cli_can_write_bounded_deterministic_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            queue = root / "queue.json"
            chain = root / "chain.json"
            output = root / "route.json"
            write_json(
                queue,
                {
                    "items": [
                        {
                            "id": "INTEGRITY-FIRST",
                            "kind": "integrity",
                            "eligible_for_elim": True,
                            "source": {},
                        }
                    ]
                },
            )
            write_json(
                chain,
                {"elim_decision": {"profile": {"full_context": False}}},
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/select_elim_context_route.py"),
                    "--input-root",
                    str(root),
                    "--queue",
                    str(queue),
                    "--chain",
                    str(chain),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")),
                {
                    "canonical_record": None,
                    "issue": None,
                    "kind": "integrity",
                    "profile": "integrity_reconciliation",
                    "work_item_id": "INTEGRITY-FIRST",
                },
            )

    def test_safety_zero_bot_repair_preempts_due_comprehensive_review(self):
        queue = {
            "items": [
                {
                    "id": "repair-source",
                    "kind": "bot_failure",
                    "safety_class": 0,
                    "eligible_for_elim": True,
                    "source": {"bot": {"id": "source-checker-bot"}},
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
            "review_epoch": {"due": True},
            "elim_decision": {"profile": {"full_context": True}},
        }
        route = select_context_route(queue, chain)
        self.assertEqual(route["work_item_id"], "repair-source")
        self.assertEqual(route["kind"], "bot_failure")
        self.assertEqual(route["profile"], "integrity_reconciliation")
        self.assertTrue(chain["review_epoch"]["due"])

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

    def test_local_override_is_applied_before_route_selection(self):
        queue = {
            "items": [
                {
                    "id": "INTEGRITY-FIRST",
                    "kind": "integrity",
                    "eligible_for_elim": True,
                    "safety_class": 1,
                    "priority_score": 900,
                    "age_days": 0,
                    "source": {},
                },
                {
                    "id": "PUBLIC-SECOND",
                    "kind": "public_intake",
                    "eligible_for_elim": True,
                    "safety_class": 1,
                    "priority_score": 500,
                    "age_days": 0,
                    "source": {},
                },
            ],
            "selected_work_item_id": "INTEGRITY-FIRST",
        }
        chain = {
            "elim_decision": {"profile": {"full_context": False}},
            "user_overrides": {
                "INTEGRITY-FIRST": {
                    "source": "user-local-console",
                    "suppressed": True,
                    "reason": "Await a refreshed source.",
                }
            },
        }
        route = select_context_route(queue, chain)
        self.assertEqual(route["work_item_id"], "PUBLIC-SECOND")
        self.assertEqual(route["profile"], "public_intake")

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
    def configuration_route(
        self,
    ) -> tuple[dict[str, object], dict[str, object]]:
        view = (
            component_registry_module
            .load_component_registry_configuration_routing_view()
        )
        return view["route"], view

    def test_generated_console_and_local_artifacts_are_excluded_from_ordinary_search(self):
        policy = (ROOT / ".rgignore").read_text(encoding="utf-8")
        self.assertIn("framework/project/interfaces/project-console/catalog-data.js", policy)
        self.assertIn("framework/project/interfaces/project-console/data/", policy)
        self.assertIn(".site-build/", policy)
        self.assertIn(".tmp/", policy)
        self.assertIn(".venv/", policy)

    def test_production_context_routes_are_hash_pinned_and_extractable(self):
        raw, view = self.configuration_route()
        self.assertEqual(raw["schema_version"], 2)
        self.assertTrue(
            {
                "framework_kernel",
                "agent_rules_kernel",
                "task_handoff",
            }
            <= set(raw["required_modules"])
        )
        current_spec = raw["documents"]["task_handoff"]
        self.assertEqual(
            current_spec["path"],
            "framework/handoffs/current-task.md",
        )
        self.assertEqual(current_spec["hash_policy"], "runtime")
        self.assertFalse(current_spec["governing"])
        self.assertTrue(
            {"framework_kernel", "agent_rules_kernel"}
            <= set(current_spec["requires"])
        )
        self.assertNotIn("sha256", current_spec)
        for document_id, document in raw["documents"].items():
            if document_id == "task_handoff":
                continue
            self.assertEqual(document.get("hash_policy"), "pinned", document_id)
            self.assertRegex(
                document.get("sha256", ""),
                r"^[0-9a-f]{64}$",
                document_id,
            )

        manifest = raw
        packets = {
            profile_name:
                component_registry_module.build_context_packet_from_view(
                    view,
                    profile_name,
                    assurance_mode=view["validation_mode"],
                    root=ROOT,
                )
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
            if module["document"] == "task_handoff"
        )
        self.assertEqual(current_module["hash_policy"], "runtime")
        self.assertEqual(
            current_module["sha256"],
            hashlib.sha256(
                (ROOT / "framework/handoffs/current-task.md").read_bytes()
            ).hexdigest(),
        )

        expected_profile_modules = {
            "integrity_reconciliation": {
                "audit_project_consistency",
                "project_structure",
                "project_autonomous_execution",
                "agent_provenance_logging",
                "agent_validation_closeout",
                "audit_change",
                "github_workflow",
                "evidence_standards",
                "source_project_monitoring",
                "project_console_progress",
                "project_tool_interface",
                "runbook_run_coordinator_bot",
                "print_assembly",
                "public_release",
            },
            "issue_development": {
                "project_configuration",
                "project_source_adjudication",
                "method_scope_admission",
                "method_partisan_perception",
                "issue_architecture",
                "development_levels",
                "proposal_development_model",
                "agent_issue_candidate_work",
                "github_workflow",
            },
            "candidate_research": {
                "project_configuration",
                "project_source_adjudication",
                "candidate_adjudication",
                "method_partisan_perception",
                "source_catalogs",
                "agent_issue_candidate_work",
            },
            "issue_audit": {
                "project_configuration",
                "project_source_adjudication",
                "project_audit_execution",
                "audit_core",
                "audit_verification",
                "audit_tiered",
                "audit_legal_prior_proposal",
                "proposal_scoring_model",
                "scoring_adoption_pathway",
                "scoring_external_international",
            },
            "change_audit": {
                "project_configuration",
                "project_source_adjudication",
                "project_audit_execution",
                "audit_change",
                "audit_project_consistency",
                "proposal_scoring_model",
                "github_workflow",
            },
            "public_intake": {
                "project_source_adjudication",
                "intake_process",
                "method_scope_admission",
                "agent_issue_candidate_work",
                "github_workflow",
            },
            "github_sync": {
                "github_workflow",
                "navigation_inventory",
                "navigation_project_sync",
            },
        }
        for profile_name, expected_modules in expected_profile_modules.items():
            if view["validation_mode"] != "proposed_revision_validation":
                expected_modules = expected_modules - {
                    "project_structure",
                    "context_routing",
                    "repository_map",
                }
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
        self.assertIn("task_handoff", comprehensive_modules)

    def test_small_profiles_allow_additive_audit_capabilities_with_headroom(self):
        manifest, view = self.configuration_route()
        profiles = ("integrity_reconciliation", "github_sync")
        capabilities = ("change_control", "tiered_quality_audit")

        for profile_name in profiles:
            self.assertEqual(
                manifest["profiles"][profile_name]["max_bytes"],
                900000 if profile_name == "integrity_reconciliation" else 500000,
            )
            for capability in capabilities:
                with self.subTest(profile=profile_name, capability=capability):
                    packet = component_registry_module.build_context_packet_from_view(
                        view,
                        profile_name,
                        assurance_mode=view["validation_mode"],
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
        with self.assertRaisesRegex(
            RoutingRuleFailure,
            r"context packet exceeds max bytes \(\d+ > 300000\)",
        ):
            _manifest, view = self.configuration_route()
            component_registry_module.build_context_packet_from_view(
                view,
                "integrity_reconciliation",
                assurance_mode=view["validation_mode"],
                root=ROOT,
                capabilities=("change_control",),
                max_total_bytes=300000,
            )


if __name__ == "__main__":
    unittest.main()
