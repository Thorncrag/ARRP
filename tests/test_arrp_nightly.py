import fcntl
import importlib
import importlib.util
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.disclosure_test_support import install_test_control_pack


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "arrp_nightly", ROOT / "scripts" / "arrp_nightly.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
install_test_control_pack(MODULE)
path_authority_module = importlib.import_module(
    MODULE.ProjectPathAuthority.__module__
)


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


class GitFixture:
    def __init__(self, root: Path):
        self.root = root
        self.remote = root / "remote.git"
        self.seed = root / "seed"
        self.repo = root / "repo"
        self.state = root / "state"
        run("git", "init", "--bare", str(self.remote))
        run("git", "init", "-b", "main", str(self.seed))
        self.configure(self.seed)
        (self.seed / ".gitignore").write_text(".env\nprivate-*\n", encoding="utf-8")
        issue = self.seed / "areas/TEST/issues/TEST-001.md"
        issue.parent.mkdir(parents=True)
        issue.write_text("baseline\n", encoding="utf-8")
        scripts = self.seed / "scripts"
        scripts.mkdir()
        (scripts / "arrp_nightly.py").write_text("print('reviewed')\n", encoding="utf-8")
        run("git", "add", ".gitignore", "areas/TEST/issues/TEST-001.md", "scripts/arrp_nightly.py", cwd=self.seed)
        run("git", "commit", "-m", "baseline", cwd=self.seed)
        run("git", "remote", "add", "origin", str(self.remote), cwd=self.seed)
        run("git", "push", "-u", "origin", "main", cwd=self.seed)
        run("git", "clone", "--branch", "main", str(self.remote), str(self.repo))
        self.configure(self.repo)

    @staticmethod
    def configure(repository: Path) -> None:
        run("git", "config", "user.name", "Fixture User", cwd=repository)
        run("git", "config", "user.email", "fixture@example.invalid", cwd=repository)

    def config(self) -> MODULE.RunnerConfig:
        return MODULE.RunnerConfig(
            self.repo,
            self.state,
            fixture_root=self.root,
            runtime_files=(),
        )

    def remote_commit(self, content: str, *, clone_name: str = "upstream") -> str:
        checkout = self.root / clone_name
        run("git", "clone", "--branch", "main", str(self.remote), str(checkout))
        self.configure(checkout)
        path = checkout / "areas/TEST/issues/TEST-001.md"
        path.write_text(content, encoding="utf-8")
        run("git", "add", "areas/TEST/issues/TEST-001.md", cwd=checkout)
        run("git", "commit", "-m", "origin change", cwd=checkout)
        run("git", "push", "origin", "main", cwd=checkout)
        return run("git", "rev-parse", "HEAD", cwd=checkout)


class ArrpNightlyTransactionTests(unittest.TestCase):
    def test_capacity_module_is_a_protected_console_shell_file(self):
        self.assertIn(
            "framework/project/interfaces/project-console/capacity.js",
            MODULE.PROTECTED_EXACT,
        )

    def test_component_registry_module_is_a_protected_console_shell_file(self):
        self.assertIn(
            "framework/project/interfaces/project-console/component-registry.js",
            MODULE.PROTECTED_EXACT,
        )

    def test_component_registry_router_is_in_the_runtime_snapshot(self):
        self.assertIn(
            "scripts/component_registry.py",
            MODULE.RUNTIME_FILES,
        )

    def test_occurrence_finalizer_dependencies_are_in_runtime_snapshot(self):
        self.assertIn("scripts/codex_usage_projection.py", MODULE.RUNTIME_FILES)
        self.assertNotIn("scripts/build_owner_console.py", MODULE.RUNTIME_FILES)

    def test_owner_usage_wrapper_preserves_valid_unavailable_posture(self):
        unavailable = MODULE.unavailable_codex_usage_projection(
            "owner_local_projection_required"
        )
        with (
            mock.patch.object(
                MODULE,
                "read_owner_text",
                return_value=json.dumps(unavailable),
            ),
            mock.patch.object(
                MODULE,
                "codex_usage_projection_is_valid",
                return_value=True,
            ),
        ):
            observed = MODULE._read_current_codex_usage()
        self.assertEqual(observed["availability"], "unavailable")
        self.assertEqual(observed["payload"], unavailable)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fixture = GitFixture(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def test_occurrence_finalizer_builds_once_and_preserves_primary_status(self):
        config = self.fixture.config()
        config.state_root.mkdir(mode=0o700)
        MODULE.atomic_write_json(
            config.state_root / "status.json",
            {
                "run_id": "finalizer-success",
                "status": "failed",
                "updated_at": "2026-08-04T14:00:00Z",
                "pull_request": None,
                "merge_commit": None,
                "pages_conclusion": None,
            },
        )
        run_dir = config.state_root / "runs" / "finalizer-success"
        run_dir.mkdir(parents=True)
        MODULE.atomic_write_json(
            run_dir / "run-chain.json",
            {
                "run_id": "finalizer-success",
                "status": "complete",
                "usage": {
                    "remaining_percent": 26,
                    "status": "available",
                },
            },
        )
        operations = {
            "schema_version": 4,
            "availability": "current",
            "generated_at": "2026-08-04T14:00:00Z",
            "catalog_generation_id": "project-console-test",
            "source_revision": "a" * 40,
            "agent_registry": [],
            "project_logs": [],
            "integrity": {},
            "run_chain": {"run_id": "finalizer-success"},
            "action_snapshot": {},
            "queue_directory": {},
            "operational_incidents": {},
            "security_incidents": {},
            "incident_relations": {},
            "transaction_recovery": {},
            "governance_change_supplements": {},
            "privacy": "owner-only",
        }
        security = {
            "schema_version": 2,
            "availability": "current",
            "complete": True,
            "checked_at": "2026-08-04T14:00:00Z",
            "public_intake_state": "live",
            "private_attention": "no",
            "active_incident": False,
            "tools": [],
        }
        owner_data = config.state_root / "console"
        MODULE.atomic_write_bytes(
            owner_data / "private-operations.js",
            (
                "/* Private local projection; never commit or publish. */\n"
                "window.ARRP_PRIVATE_OPERATIONS="
                + json.dumps(operations, separators=(",", ":"))
                + ";\n"
            ).encode("utf-8"),
        )
        MODULE.atomic_write_bytes(
            owner_data / "private-security-assurance.js",
            (
                "/* Private local projection; never commit or publish. */\n"
                "window.ARRP_PRIVATE_SECURITY_ASSURANCE="
                + json.dumps(security, separators=(",", ":"))
                + ";\n"
            ).encode("utf-8"),
        )
        unavailable = MODULE.unavailable_codex_usage_projection(
            "source_unavailable"
        )
        with mock.patch.object(
            MODULE,
            "_read_current_codex_usage",
            return_value={"availability": "unavailable", "payload": unavailable},
        ):
            first = MODULE.finalize_occurrence(config, "finalizer-success")
            second = MODULE.finalize_occurrence(config, "finalizer-success")

        self.assertEqual(first, second)
        self.assertEqual(first["status"], "completed")
        self.assertEqual(first["primary_status"], "failed")
        package_path = Path(first["project_package_path"])
        package = json.loads(package_path.read_text(encoding="utf-8"))
        self.assertEqual(package["run_id"], "finalizer-success")
        self.assertEqual(package["usage"]["occurrence"]["remaining_percent"], 26)
        self.assertEqual(
            package["usage"]["occurrence"]["availability"],
            "available_for_occurrence",
        )
        self.assertEqual(package["operations"]["availability"], "current")
        self.assertTrue(package["operations"]["matches_occurrence"])
        self.assertEqual(package["operations"]["payload"]["agent_registry"], [])
        self.assertEqual(package["security_assurance"]["availability"], "retained")
        self.assertIsNone(package["security_assurance"]["matches_occurrence"])
        self.assertEqual(package["security_assurance"]["payload"]["tools"], [])
        contradictory = dict(package)
        contradictory["usage"] = {
            **package["usage"],
            "current": {
                "availability": "current",
                "payload": unavailable,
            },
        }
        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "usage payload is invalid",
        ):
            MODULE._validate_owner_project_package(
                contradictory,
                run_id="finalizer-success",
            )
        self.assertEqual(first["project_package_sha256"], MODULE.file_sha256(package_path))
        self.assertNotIn(
            "publication-readback-unavailable",
            first["health"]["gaps"],
        )
        self.assertTrue(
            (
                config.state_root
                / "runs"
                / "finalizer-success"
                / MODULE.OCCURRENCE_FINALIZER_FILENAME
            ).is_file()
        )

    def test_occurrence_finalizer_failure_is_separate_from_primary_result(self):
        config = self.fixture.config()
        error = MODULE.TransactionError("owner Console unavailable")
        with (
            mock.patch.object(MODULE, "finalize_occurrence", side_effect=error),
            mock.patch.object(MODULE, "spool_failure_incident") as spool,
        ):
            MODULE.finalize_occurrence_safely(config, "finalizer-failure")
        spool.assert_called_once()
        self.assertEqual(
            spool.call_args.kwargs["component"],
            "occurrence-finalizer",
        )

    def test_occurrence_finalizer_creates_early_failure_evidence_directory(self):
        config = self.fixture.config()
        config.state_root.mkdir(mode=0o700)
        MODULE.atomic_write_json(
            config.state_root / "status.json",
            {
                "run_id": "early-failure",
                "status": "failed",
                "updated_at": "2026-08-04T14:00:00Z",
                "runtime_commit": None,
                "pull_request": None,
                "merge_commit": None,
                "pages_conclusion": None,
            },
        )
        security = {
            "schema_version": 2,
            "availability": "current",
            "complete": True,
            "checked_at": "2026-08-03T14:00:00Z",
            "public_intake_state": "live",
            "private_attention": "no",
            "active_incident": False,
            "tools": [],
        }
        MODULE.atomic_write_bytes(
            config.state_root / "console/private-security-assurance.js",
            (
                "/* Private local projection; never commit or publish. */\n"
                "window.ARRP_PRIVATE_SECURITY_ASSURANCE="
                + json.dumps(security, separators=(",", ":"))
                + ";\n"
            ).encode("utf-8"),
        )
        with mock.patch.object(
            MODULE,
            "_read_current_codex_usage",
            return_value={
                "availability": "unavailable",
                "payload": MODULE.unavailable_codex_usage_projection(
                    "source_unavailable"
                ),
            },
        ):
            result = MODULE.finalize_occurrence(config, "early-failure")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["primary_status"], "failed")
        self.assertTrue(
            (
                config.state_root
                / "runs"
                / "early-failure"
                / MODULE.OCCURRENCE_FINALIZER_FILENAME
            ).is_file()
        )
        package = json.loads(
            Path(result["project_package_path"]).read_text(encoding="utf-8")
        )
        self.assertIsNone(package["run_chain"])
        self.assertEqual(package["usage"]["occurrence"]["availability"], "unavailable")
        self.assertEqual(package["security_assurance"]["availability"], "retained")
        self.assertIsNone(package["security_assurance"]["matches_occurrence"])

    def test_exclusive_lock_runs_finalizer_before_unlock(self):
        observed = {"lock_held": False}

        def finalize():
            contender = os.open(self.fixture.state / "run.lock", os.O_RDWR)
            try:
                with self.assertRaises(BlockingIOError):
                    fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
                observed["lock_held"] = True
            finally:
                os.close(contender)

        with MODULE.exclusive_lock(
            self.fixture.state,
            "locked-finalizer",
            on_finalize=finalize,
        ):
            pass
        self.assertTrue(observed["lock_held"])

    def test_lock_contention_does_not_invoke_finalizer(self):
        finalize = mock.Mock()
        with MODULE.exclusive_lock(self.fixture.state, "active-owner"):
            with self.assertRaisesRegex(
                MODULE.TransactionError,
                "owns the operating-system lock",
            ):
                with MODULE.exclusive_lock(
                    self.fixture.state,
                    "blocked-contender",
                    on_finalize=finalize,
                ):
                    pass
        finalize.assert_not_called()

    def production_routing_authority(
        self,
        *,
        create_registry: bool = True,
    ) -> tuple[Path, Path, Path, MODULE.ProjectPathAuthority]:
        state = (self.root / "production-state").resolve()
        worktrees = state / "worktrees"
        runs = state / "runs"
        repository = worktrees / "routing-run"
        run_dir = runs / "routing-run"
        for path in (state, worktrees, runs, repository, run_dir):
            path.mkdir(mode=0o700, exist_ok=True)
        if create_registry:
            registry = repository / "framework/component-registry.json"
            registry.parent.mkdir(mode=0o700)
            registry.write_text("{}\n", encoding="utf-8")
        with mock.patch.object(
            path_authority_module,
            "APPROVED_STATE_ROOT",
            state,
        ):
            authority = MODULE.ProjectPathAuthority.production_transaction(
                repository_root=repository,
                run_root=run_dir,
            )
        return repository, state, run_dir, authority

    def fixture_routing_authority(self) -> MODULE.ProjectPathAuthority:
        self.fixture.state.mkdir(mode=0o700, exist_ok=True)
        return MODULE.routing_path_authority(
            self.fixture.config(),
            self.fixture.repo,
        )

    def write_predecessor_route(
        self,
        *,
        repository: Path | None = None,
        sha256: str | None = None,
    ) -> Path:
        repository = repository or self.fixture.repo
        document = repository / "framework/governing.md"
        document.parent.mkdir(parents=True, exist_ok=True)
        document.write_text("governing fixture\n", encoding="utf-8")
        digest = sha256 or hashlib.sha256(document.read_bytes()).hexdigest()
        route = repository / "framework/project/automation/context-routes.json"
        route.parent.mkdir(parents=True, exist_ok=True)
        route.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "documents": {
                        "governing": {
                            "path": "framework/governing.md",
                            "requires": [],
                            "governing": True,
                            "hash_policy": "pinned",
                            "sha256": digest,
                        }
                    },
                    "required_modules": ["governing"],
                    "profiles": {
                        "fixture": {
                            "modules": ["governing"],
                            "sections": [],
                            "capabilities": [],
                            "max_bytes": 4096,
                        }
                    },
                    "capabilities": {},
                    "generated_path_exclusions": [],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return route

    def test_fixture_protected_paths_can_omit_component_registry(self):
        authority = self.fixture_routing_authority()
        with mock.patch.object(
            MODULE,
            "load_validated_component_registry_routing_view",
        ) as registry_loader:
            protected = MODULE.governing_protected_paths(
                self.fixture.repo,
                ("scripts/fixture-runtime.py",),
                path_authority=authority,
            )

        self.assertEqual(protected, frozenset({"scripts/fixture-runtime.py"}))
        registry_loader.assert_not_called()

    def test_nonfixture_protected_paths_require_a_routing_authority(self):
        repository, _state, _run_dir, authority = (
            self.production_routing_authority(create_registry=False)
        )
        self.assertEqual(authority.mode, "production_transaction")
        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "routing authority is unavailable",
        ):
            MODULE.governing_protected_paths(
                repository,
                ("scripts/fixture-runtime.py",),
                path_authority=authority,
            )

    def test_fixture_predecessor_supplies_governing_paths(self):
        self.write_predecessor_route()
        authority = self.fixture_routing_authority()
        with (
            mock.patch.object(
                MODULE,
                "load_fixture_component_registry_routing_view",
            ) as candidate_loader,
            mock.patch.object(
                MODULE,
                "load_route_manifest",
                wraps=MODULE.load_route_manifest,
            ) as predecessor_loader,
        ):
            protected = MODULE.governing_protected_paths(
                self.fixture.repo,
                ("scripts/fixture-runtime.py",),
                path_authority=authority,
            )

        candidate_loader.assert_not_called()
        predecessor_loader.assert_called_once_with(
            self.fixture.repo.resolve()
            / "framework/project/automation/context-routes.json",
            root=self.fixture.repo.resolve(),
            verify_hashes=True,
        )
        self.assertEqual(
            protected,
            frozenset(
                {
                    "scripts/fixture-runtime.py",
                    "framework/governing.md",
                }
            ),
        )

    def test_fixture_predecessor_stale_pin_fails_closed(self):
        self.write_predecessor_route(sha256="0" * 64)
        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "predecessor routing validation failed",
        ):
            MODULE.governing_protected_paths(
                self.fixture.repo,
                path_authority=self.fixture_routing_authority(),
            )

    def test_predecessor_rejects_authority_repository_mismatch(self):
        self.write_predecessor_route()
        other_repository = self.root / "other-repository"
        other_repository.mkdir()
        self.fixture.state.mkdir(mode=0o700, exist_ok=True)
        authority = MODULE.ProjectPathAuthority.fixture(
            self.root,
            repository_root=other_repository,
            state_root=self.fixture.state,
            output_root=other_repository,
        )
        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "routing authority and repository differ",
        ):
            MODULE.governing_protected_paths(
                self.fixture.repo,
                path_authority=authority,
            )

    def test_fixture_candidate_uses_only_fixture_registry_loader(self):
        registry = self.fixture.repo / "framework/component-registry.json"
        registry.parent.mkdir(parents=True)
        registry.write_text("{}\n", encoding="utf-8")
        self.fixture.state.mkdir(mode=0o700)
        authority = MODULE.routing_path_authority(
            self.fixture.config(),
            self.fixture.repo,
        )
        candidate_view = {
            "schema_version": 4,
            "validation_mode": "adopted_configuration_validation",
            "authoritative": False,
            "executable": False,
            "authority_effective": False,
            "source_revision_authorized": False,
            "source_bytes_current": True,
            "canonical_history_confirmed": False,
            "receipt_trusted": False,
            "runtime_live": "not_checked",
            "activation_receipt_consulted": False,
            "predecessor_route_consulted": False,
            "route": {
                "documents": {
                    "governing": {
                        "governing": True,
                        "path": "framework/governing.md",
                    }
                }
            },
        }
        with (
            mock.patch.object(
                MODULE,
                "load_fixture_component_registry_routing_view",
                return_value=candidate_view,
            ) as fixture_loader,
            mock.patch.object(
                MODULE,
                "load_validated_component_registry_routing_view",
            ) as production_loader,
        ):
            protected = MODULE.governing_protected_paths(
                self.fixture.repo,
                ("scripts/fixture-runtime.py",),
                path_authority=authority,
            )

        fixture_loader.assert_called_once_with(authority)
        production_loader.assert_not_called()
        self.assertEqual(
            protected,
            frozenset(
                {
                    "scripts/fixture-runtime.py",
                    "framework/governing.md",
                }
            ),
        )

    def test_production_protected_paths_require_component_registry(self):
        self.write_predecessor_route()
        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "active Component Registry routing is unavailable",
        ):
            MODULE.governing_protected_paths(
                self.fixture.repo,
                path_authority=self.fixture_routing_authority(),
                require_active_registry=True,
            )

    def test_production_protected_paths_use_active_registry_view(self):
        repository, _state, _run_dir, authority = (
            self.production_routing_authority()
        )
        active_view = {
            "schema_version": 4,
            "validation_mode": "live_authority_validation",
            "authoritative": True,
            "executable": False,
            "authority_effective": True,
            "source_revision_authorized": True,
            "source_bytes_current": True,
            "canonical_history_confirmed": True,
            "receipt_trusted": True,
            "runtime_live": "not_checked",
            "activation_receipt_consulted": True,
            "predecessor_route_consulted": False,
            "route": {
                "documents": {
                    "governing": {
                        "governing": True,
                        "path": "framework/governing.md",
                    },
                    "nongoverning": {
                        "governing": False,
                        "path": "framework/nongoverning.md",
                    },
                }
            },
        }
        with mock.patch.object(
            MODULE,
            "load_validated_component_registry_routing_view",
            return_value=active_view,
        ) as registry_loader:
            protected = MODULE.governing_protected_paths(
                repository,
                ("scripts/fixture-runtime.py",),
                path_authority=authority,
                require_active_registry=True,
            )

        registry_loader.assert_called_once_with(authority)
        self.assertEqual(
            protected,
            frozenset(
                {
                    "scripts/fixture-runtime.py",
                    "framework/governing.md",
                }
            ),
        )

    def test_production_protected_paths_reject_candidate_registry_view(self):
        repository, _state, _run_dir, authority = (
            self.production_routing_authority()
        )
        candidate_view = {
            "schema_version": 4,
            "validation_mode": "adopted_configuration_validation",
            "authoritative": False,
            "executable": False,
            "authority_effective": False,
            "source_revision_authorized": False,
            "source_bytes_current": True,
            "canonical_history_confirmed": False,
            "receipt_trusted": False,
            "runtime_live": "not_checked",
            "activation_receipt_consulted": False,
            "predecessor_route_consulted": False,
            "route": {"documents": {}},
        }
        with (
            mock.patch.object(
                MODULE,
                "load_validated_component_registry_routing_view",
                return_value=candidate_view,
            ),
            self.assertRaisesRegex(
                MODULE.TransactionError,
                "production routing requires live Registry v4 Component Registry",
            ),
        ):
            MODULE.governing_protected_paths(
                repository,
                path_authority=authority,
                require_active_registry=True,
            )

    def test_production_protected_paths_preserve_safe_validation_failure(self):
        repository, _state, _run_dir, authority = (
            self.production_routing_authority()
        )
        self.write_predecessor_route(repository=repository)
        with (
            mock.patch.object(
                MODULE,
                "load_validated_component_registry_routing_view",
                side_effect=MODULE.ComponentRegistryError(
                    "active registry lacks authenticated activation readback"
                ),
            ),
            mock.patch.object(
                MODULE,
                "load_route_manifest",
            ) as predecessor_loader,
            self.assertRaisesRegex(
                MODULE.TransactionError,
                "Component Registry routing validation failed",
            ),
        ):
            MODULE.governing_protected_paths(
                repository,
                path_authority=authority,
                require_active_registry=True,
            )
        predecessor_loader.assert_not_called()

    def test_production_publication_requires_active_registry_classification(self):
        head = run("git", "rev-parse", "HEAD", cwd=self.fixture.repo)
        transaction = MODULE.TransactionResult(
            run_id="production-publication-routing",
            status="completed",
            branch="codex/production-publication-routing",
            checkpoint_commit=None,
            worktree_path=str(self.fixture.repo),
            fetched_origin_main=head,
        )
        cycle_summary = {
            "phase": "P6",
            "final_commit": {"commit": head},
            "last_success_candidate": {"run_id": transaction.run_id},
        }
        run_dir = (
            self.fixture.state
            / "runs"
            / "production-publication-routing"
        )
        run_dir.mkdir(parents=True)
        with mock.patch.object(
            MODULE,
            "classify_publication_range",
            side_effect=MODULE.TransactionError("classification sentinel"),
        ) as classifier:
            with self.assertRaisesRegex(
                MODULE.TransactionError,
                "classification sentinel",
            ):
                MODULE.publish_production_transaction(
                    self.fixture.config(),
                    transaction,
                    cycle_summary,
                )

        classifier.assert_called_once()
        call = classifier.call_args
        self.assertEqual(call.args, (self.fixture.repo.resolve(), run_dir))
        self.assertEqual(call.kwargs["base_commit"], head)
        self.assertEqual(call.kwargs["head_commit"], head)
        self.assertTrue(call.kwargs["require_active_registry"])
        authority = call.kwargs["path_authority"]
        self.assertEqual(authority.mode, "fixture")
        self.assertEqual(authority.repository_root, self.fixture.repo.resolve())
        self.assertEqual(authority.output_root, run_dir.resolve())

    def test_dirty_ordinary_fixture_is_checkpointed(self):
        path = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        path.write_text("daytime ordinary work\n", encoding="utf-8")
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="ordinary-checkpoint"
        )
        self.assertEqual(result.status, "completed")
        self.assertIsNotNone(result.checkpoint_commit)
        committed = run(
            "git",
            "show",
            f"{result.checkpoint_commit}:areas/TEST/issues/TEST-001.md",
            cwd=self.fixture.repo,
        )
        self.assertEqual(committed, "daytime ordinary work")
        self.assertEqual(run("git", "status", "--porcelain", cwd=self.fixture.repo), "")
        manifest = json.loads(
            (
                self.fixture.state
                / "runs/ordinary-checkpoint/pre-lock-manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["branch"], "main")
        self.assertEqual(manifest["origin_url"], str(self.fixture.remote))
        self.assertTrue(manifest["due"])
        self.assertEqual(manifest["paths"][0]["path"], "areas/TEST/issues/TEST-001.md")

    def test_owner_pause_file_exits_before_repository_mutation(self):
        pause = self.fixture.state / "PAUSED"
        self.fixture.state.mkdir(parents=True, exist_ok=True)
        pause.write_text("P6 rollback rehearsal\n", encoding="utf-8")
        pause.chmod(0o600)
        before = run("git", "rev-parse", "HEAD", cwd=self.fixture.repo)
        local_cycle = mock.Mock()

        result = MODULE.prepare_transaction(
            self.fixture.config(),
            run_id="paused-run",
            local_cycle=local_cycle,
        )

        self.assertEqual(result.status, "paused")
        self.assertEqual(run("git", "rev-parse", "HEAD", cwd=self.fixture.repo), before)
        self.assertEqual(run("git", "branch", "--show-current", cwd=self.fixture.repo), "main")
        self.assertEqual(run("git", "status", "--porcelain", cwd=self.fixture.repo), "")
        local_cycle.assert_not_called()
        status = json.loads(
            (self.fixture.state / "status.json").read_text(encoding="utf-8")
        )
        self.assertEqual(status["status"], "paused")
        self.assertEqual(status["stage"], "01_preflight")
        self.assertEqual(
            status["validation_summary"]["reason"],
            "owner_pause_file_present",
        )

    def test_unsafe_pause_marker_fails_closed(self):
        self.fixture.state.mkdir(parents=True, exist_ok=True)
        target = self.fixture.state / "pause-target"
        target.write_text("unsafe\n", encoding="utf-8")
        (self.fixture.state / "PAUSED").symlink_to(target.name)

        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "PAUSED must be a regular owner-only file",
        ):
            MODULE.prepare_transaction(
                self.fixture.config(),
                run_id="unsafe-pause",
            )
        self.assertEqual(run("git", "branch", "--show-current", cwd=self.fixture.repo), "main")

    def test_untracked_recognized_file_is_checkpointed(self):
        path = self.fixture.repo / "research/new-record.md"
        path.parent.mkdir()
        path.write_text("recognized\n", encoding="utf-8")
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="recognized-untracked"
        )
        names = run(
            "git",
            "show",
            "--pretty=",
            "--name-only",
            result.checkpoint_commit,
            cwd=self.fixture.repo,
        ).splitlines()
        self.assertIn("research/new-record.md", names)

    def test_ignored_private_file_is_excluded(self):
        private = self.fixture.repo / ".env"
        private_value = "SEC" + "RET=fixture-only"
        private.write_text(private_value + "\n", encoding="utf-8")
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="ignored-private"
        )
        self.assertEqual(result.status, "completed")
        self.assertIsNone(result.checkpoint_commit)
        self.assertTrue(private.exists())
        branch_files = run(
            "git", "ls-tree", "-r", "--name-only", result.branch, cwd=self.fixture.repo
        ).splitlines()
        self.assertNotIn(".env", branch_files)
        status_text = (self.fixture.state / "status.json").read_text(encoding="utf-8")
        self.assertNotIn(".env", status_text)
        self.assertNotIn(private_value, status_text)

    def test_protected_script_is_checkpointed_then_deferred(self):
        script = self.fixture.repo / "scripts/arrp_nightly.py"
        script.write_text("print('changed but not executed')\n", encoding="utf-8")
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="protected-script"
        )
        self.assertEqual(result.status, "review-required")
        self.assertEqual(result.protected_paths, ("scripts/arrp_nightly.py",))
        self.assertIsNone(result.worktree_path)
        self.assertEqual(
            run(
                "git",
                "show",
                f"{result.checkpoint_commit}:scripts/arrp_nightly.py",
                cwd=self.fixture.repo,
            ),
            "print('changed but not executed')",
        )

    def test_local_ahead_commit_remains_ancestor_of_nightly_branch(self):
        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.write_text("local commit\n", encoding="utf-8")
        run("git", "add", "areas/TEST/issues/TEST-001.md", cwd=self.fixture.repo)
        run("git", "commit", "-m", "local ahead", cwd=self.fixture.repo)
        local_ahead = run("git", "rev-parse", "HEAD", cwd=self.fixture.repo)
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="local-ahead"
        )
        ancestry = subprocess.run(
            ["git", "-C", str(self.fixture.repo), "merge-base", "--is-ancestor", local_ahead, result.branch]
        )
        self.assertEqual(ancestry.returncode, 0)

    def test_origin_ahead_is_merged_in_transaction_worktree(self):
        remote_head = self.fixture.remote_commit("origin ahead\n")
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="origin-ahead"
        )
        ancestry = subprocess.run(
            ["git", "-C", result.worktree_path, "merge-base", "--is-ancestor", remote_head, "HEAD"]
        )
        self.assertEqual(ancestry.returncode, 0)
        self.assertEqual(
            (Path(result.worktree_path) / "areas/TEST/issues/TEST-001.md").read_text(
                encoding="utf-8"
            ),
            "origin ahead\n",
        )

    def test_merge_conflict_preserves_branch_and_worktree(self):
        self.fixture.remote_commit("origin version\n")
        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.write_text("daytime conflicting version\n", encoding="utf-8")
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="merge-conflict"
        )
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.failure_class, "origin_merge_conflict")
        self.assertTrue(Path(result.worktree_path).exists())
        self.assertIn(
            "UU areas/TEST/issues/TEST-001.md",
            run("git", "status", "--porcelain", cwd=Path(result.worktree_path)),
        )
        self.assertEqual(run("git", "status", "--porcelain", cwd=self.fixture.repo), "")

    def test_post_lock_canonical_change_blocks_publication(self):
        head = run("git", "rev-parse", "HEAD", cwd=self.fixture.repo)
        digest = MODULE.manifest_digest(MODULE.status_manifest(self.fixture.repo))
        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.write_text("late human change\n", encoding="utf-8")
        with self.assertRaisesRegex(MODULE.TransactionError, "post-lock canonical change"):
            MODULE.assert_canonical_unchanged(self.fixture.repo, head, digest)
        self.assertEqual(issue.read_text(encoding="utf-8"), "late human change\n")

    def test_lock_and_descriptors_are_released(self):
        MODULE.prepare_transaction(self.fixture.config(), run_id="lock-release")
        lock_path = self.fixture.state / "run.lock"
        descriptor = os.open(lock_path, os.O_RDWR)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)
        status = json.loads((self.fixture.state / "status.json").read_text())
        self.assertEqual(status["status"], "completed")

    def test_lock_contender_does_not_overwrite_owner_status(self):
        with MODULE.exclusive_lock(self.fixture.state, "active-owner"):
            with self.assertRaisesRegex(MODULE.TransactionError, "owns the operating-system lock"):
                MODULE.prepare_transaction(
                    self.fixture.config(), run_id="blocked-contender"
                )
            self.assertFalse((self.fixture.state / "status.json").exists())
            owner = json.loads(
                (self.fixture.state / "run-owner.json").read_text(encoding="utf-8")
            )
            self.assertEqual(owner["run_id"], "active-owner")

    def test_nonmapping_local_callback_fails_with_safe_status(self):
        sensitive_marker = "callback-private-marker"

        class InvalidSummary:
            def __repr__(self) -> str:
                return sensitive_marker

        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "local cycle summary is invalid",
        ):
            MODULE.prepare_transaction(
                self.fixture.config(),
                run_id="invalid-local-summary",
                local_cycle=lambda _transaction: InvalidSummary(),
            )

        status_text = (self.fixture.state / "status.json").read_text(
            encoding="utf-8"
        )
        status = json.loads(status_text)
        self.assertEqual(status["status"], "failed")
        self.assertEqual(
            status["failure_reason"],
            "local cycle summary is invalid",
        )
        self.assertNotIn(sensitive_marker, status_text)

    def test_unserializable_nested_local_callback_fails_with_safe_status(self):
        sensitive_marker = "nested-private-marker"

        class InvalidNestedValue:
            def __repr__(self) -> str:
                return sensitive_marker

        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "local cycle summary is invalid",
        ):
            MODULE.prepare_transaction(
                self.fixture.config(),
                run_id="invalid-nested-local-summary",
                local_cycle=lambda _transaction: {
                    "phase": "P2",
                    "detail": InvalidNestedValue(),
                },
            )

        status_text = (self.fixture.state / "status.json").read_text(
            encoding="utf-8"
        )
        status = json.loads(status_text)
        self.assertEqual(status["status"], "failed")
        self.assertEqual(
            status["failure_reason"],
            "local cycle summary is invalid",
        )
        self.assertNotIn(sensitive_marker, status_text)

    def test_invalid_publication_callback_fails_with_safe_status(self):
        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "publication cycle summary is invalid",
        ):
            MODULE.prepare_transaction(
                self.fixture.config(),
                run_id="invalid-publication-summary",
                local_cycle=lambda _transaction: {"phase": "P2"},
                publication_cycle=lambda _transaction, _local: ["invalid"],
            )

        status = json.loads(
            (self.fixture.state / "status.json").read_text(encoding="utf-8")
        )
        self.assertEqual(status["status"], "failed")
        self.assertEqual(
            status["failure_reason"],
            "publication cycle summary is invalid",
        )

    def test_write_status_serialization_failure_does_not_mutate_status(self):
        config = self.fixture.config()
        config.state_root.mkdir(mode=0o700, exist_ok=True)
        status = MODULE._base_status(config, "status-copy-on-write")
        original = dict(status)

        with self.assertRaises(TypeError):
            MODULE.write_status(
                config,
                status,
                validation_summary={"invalid": object()},
            )

        self.assertEqual(status, original)
        self.assertFalse((config.state_root / "status.json").exists())
        MODULE.write_status(
            config,
            status,
            status="failed",
            completed_at=MODULE.iso_utc(),
            failure_class="TransactionError",
            failure_reason="safe generic failure",
            exact_next_action="Inspect the preserved failure.",
        )
        persisted = json.loads(
            (config.state_root / "status.json").read_text(encoding="utf-8")
        )
        self.assertEqual(persisted["status"], "failed")
        self.assertEqual(persisted["failure_reason"], "safe generic failure")

    def test_transaction_never_invokes_destructive_or_remote_publication_git(self):
        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.write_text("ordinary\n", encoding="utf-8")
        observed: list[tuple[str, ...]] = []
        original = MODULE.git

        def recording_git(repository, *args, **kwargs):
            observed.append(tuple(args))
            return original(repository, *args, **kwargs)

        with mock.patch.object(MODULE, "git", side_effect=recording_git):
            MODULE.prepare_transaction(self.fixture.config(), run_id="safe-command-set")
        prohibited = {"stash", "reset", "clean", "push", "pull", "rebase"}
        self.assertFalse(
            [arguments for arguments in observed if arguments and arguments[0] in prohibited]
        )
        self.assertFalse(
            [
                arguments
                for arguments in observed
                if "--force" in arguments or "--hard" in arguments
            ]
        )

    def test_fixture_guard_rejects_canonical_path_outside_fixture(self):
        config = MODULE.RunnerConfig(
            self.fixture.repo,
            self.fixture.state,
            fixture_root=self.root / "different",
        )
        with self.assertRaisesRegex(MODULE.TransactionError, "inside fixture root"):
            config.validate()

    def test_binary_change_is_rejected_without_staging(self):
        binary = self.fixture.repo / "research/binary.dat"
        binary.parent.mkdir()
        binary.write_bytes(b"safe-prefix\0fixture")
        with self.assertRaisesRegex(MODULE.TransactionError, "binary change is prohibited"):
            MODULE.prepare_transaction(self.fixture.config(), run_id="binary-reject")
        self.assertTrue(binary.exists())
        self.assertEqual(run("git", "diff", "--cached", "--name-only", cwd=self.fixture.repo), "")

    def test_fast_forward_main_reads_back_exact_remote_head(self):
        remote_head = self.fixture.remote_commit("fast-forward target\n")
        run("git", "fetch", "origin", "main", cwd=self.fixture.repo)
        observed = MODULE.fast_forward_main(self.fixture.repo, remote_head)
        self.assertEqual(observed, remote_head)
        self.assertEqual(run("git", "status", "--porcelain", cwd=self.fixture.repo), "")

    def test_fast_forward_main_refuses_dirty_worktree(self):
        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.write_text("dirty\n", encoding="utf-8")
        head = run("git", "rev-parse", "HEAD", cwd=self.fixture.repo)
        with self.assertRaisesRegex(MODULE.TransactionError, "requires a clean"):
            MODULE.fast_forward_main(self.fixture.repo, head)
        self.assertEqual(run("git", "rev-parse", "HEAD", cwd=self.fixture.repo), head)


if __name__ == "__main__":
    unittest.main()
