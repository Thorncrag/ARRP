import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "arrp_production_cycle",
    ROOT / "scripts/arrp_nightly.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def git(*arguments: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


class ArrpProductionRuntimeTests(unittest.TestCase):
    def test_production_subprocesses_cannot_write_python_bytecode(self):
        completed = subprocess.CompletedProcess(["fixture"], 0, b"", b"")
        with mock.patch.object(
            MODULE.subprocess,
            "run",
            return_value=completed,
        ) as run:
            MODULE._run_production_command(
                ("fixture",),
                cwd=ROOT,
                environment={"PYTHONDONTWRITEBYTECODE": "0"},
            )

        self.assertEqual(
            run.call_args.kwargs["env"]["PYTHONDONTWRITEBYTECODE"],
            "1",
        )

    def test_scheduled_slot_uses_most_recent_two_am_new_york(self):
        before = datetime(2026, 7, 27, 5, 30, tzinfo=timezone.utc)
        after = datetime(2026, 7, 27, 8, 30, tzinfo=timezone.utc)
        self.assertEqual(
            MODULE.scheduled_slot(before),
            "2026-07-26T02:00:00-04:00",
        )
        self.assertEqual(
            MODULE.scheduled_slot(after),
            "2026-07-27T02:00:00-04:00",
        )

    def test_runtime_snapshot_requires_exact_path_modes_manifest_and_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state"
            revision = "a" * 40
            runtime = state / "runtime" / revision
            hashes = {}
            for relative in MODULE.RUNTIME_FILES:
                target = runtime / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f"{relative}\n", encoding="utf-8")
                os.chmod(target.parent, 0o700)
                os.chmod(target, 0o600)
                hashes[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
            manifest = runtime / "runtime-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "source_commit": revision,
                        "files": hashes,
                    }
                ),
                encoding="utf-8",
            )
            os.chmod(manifest, 0o600)
            self.assertEqual(
                MODULE.verify_executed_runtime(
                    state,
                    revision,
                    executed_script=runtime / "scripts/arrp_nightly.py",
                ),
                runtime.resolve(),
            )
            (runtime / "scripts/arrp_context.py").write_text(
                "tampered\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                MODULE.TransactionError,
                "runtime hash mismatch",
            ):
                MODULE.verify_executed_runtime(
                    state,
                    revision,
                    executed_script=runtime / "scripts/arrp_nightly.py",
                )

    def test_worktree_entrypoint_must_match_runtime_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repo"
            git("init", "-b", "main", str(repository), cwd=Path(directory))
            git("config", "user.name", "Fixture", cwd=repository)
            git("config", "user.email", "fixture@example.invalid", cwd=repository)
            script = repository / "scripts/stage.py"
            script.parent.mkdir()
            script.write_text("reviewed\n", encoding="utf-8")
            git("add", "scripts/stage.py", cwd=repository)
            git("commit", "-m", "Reviewed stage", cwd=repository)
            revision = git("rev-parse", "HEAD", cwd=repository)
            MODULE.verify_worktree_entrypoint(repository, revision, script)
            script.write_text("unreviewed\n", encoding="utf-8")
            with self.assertRaisesRegex(
                MODULE.TransactionError,
                "differs from runtime commit",
            ):
                MODULE.verify_worktree_entrypoint(repository, revision, script)


class ArrpProductionCycleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repo"
        self.state = self.root / "state"
        self.runtime = self.state / "runtime" / ("b" * 40)
        self.worktree = self.state / "worktrees/run-1"
        self.worktree.mkdir(parents=True)
        self.run_dir = self.state / "runs/run-1"
        self.run_dir.mkdir(parents=True)
        run_log = self.state / "records/automation/elim-run-log.md"
        run_log.parent.mkdir(parents=True)
        run_log.write_text("# Elim Run Log\n", encoding="utf-8")
        os.chmod(run_log, 0o600)
        prior_run_id = "prior-run"
        prior_stages = {}
        prior_chain_stages = []
        for identifier in MODULE.LOCAL_STAGE_ORDER:
            relative = (
                f"runs/{prior_run_id}/stages/{identifier}/stage-result.json"
            )
            envelope = self.state / relative
            report_relative = f"runs/{prior_run_id}/stages/{identifier}/report.json"
            report = self.state / report_relative
            MODULE.atomic_write_json(
                report,
                {"schema_version": 1, "stage_id": identifier},
            )
            report_digest = MODULE.file_sha256(report)
            MODULE.atomic_write_json(
                envelope,
                {
                    "schema_version": 1,
                    "stage_id": identifier,
                    "status": "succeeded",
                    "completed_at": "2026-08-03T06:00:00Z",
                    "outputs": [
                        {
                            "path": report_relative,
                            "sha256": report_digest,
                        }
                    ],
                },
            )
            digest = MODULE.file_sha256(envelope)
            prior_stages[identifier] = {
                "envelope": relative,
                "sha256": digest,
            }
            prior_chain_stages.append(
                {
                    "id": identifier,
                    "status": "succeeded",
                    "last_success_at": "2026-08-03T06:00:00Z",
                    "output": {"sha256": "sha256:" + report_digest},
                }
            )
        MODULE.atomic_write_json(
            self.state / f"runs/{prior_run_id}/run-chain.json",
            {
                "schema_version": 1,
                "run_id": prior_run_id,
                "chain_id": prior_run_id,
                "stages": prior_chain_stages,
            },
        )
        MODULE.atomic_write_json(
            self.state / "last-success.json",
            {
                "schema_version": 1,
                "run_id": prior_run_id,
                "run_directory": f"runs/{prior_run_id}",
                "stages": prior_stages,
            },
        )
        (self.worktree / ".github").mkdir()
        coordinator_config = (
            self.worktree
            / "framework/project/automation/configuration/bots/run-coordinator-bot.json"
        )
        coordinator_config.parent.mkdir(parents=True)
        coordinator_config.write_text(
            json.dumps(
                {
                    "usageGate": {"hardReservePercent": 15},
                    "llmRouting": {"profiles": {}},
                }
            ),
            encoding="utf-8",
        )
        for relative in MODULE.RUNTIME_FILES:
            target = self.runtime / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("reviewed\n", encoding="utf-8")
        self.revision = "b" * 40
        self.config = MODULE.RunnerConfig(
            self.repository,
            self.state,
            trigger="scheduled",
            scheduled_for="2026-07-27T02:00:00-04:00",
            runtime_commit=self.revision,
        )
        self.transaction = MODULE.TransactionResult(
            "run-1",
            "completed",
            "automation/nightly-run-1",
            None,
            str(self.worktree),
            self.revision,
        )

    def fixture_production_transaction(self, *, repository_root, run_root):
        self.assertEqual(repository_root, self.worktree.resolve())
        self.assertEqual(run_root, self.run_dir)
        return MODULE.ProjectPathAuthority.fixture(
            self.root,
            repository_root=repository_root,
            state_root=self.state,
            output_root=run_root,
        )

    def assert_mixed_cadence_round_trip(self, carried_status):
        previous = json.loads(
            (self.state / "last-success.json").read_text(encoding="utf-8")
        )
        current_stage = MODULE.LOCAL_STAGE_ORDER[0]
        current_stage_dir = self.run_dir / "stages" / current_stage
        current_report = current_stage_dir / "report.json"
        MODULE.atomic_write_json(
            current_report,
            {"schema_version": 1, "stage_id": current_stage},
        )
        current_envelope = current_stage_dir / "stage-result.json"
        MODULE.atomic_write_json(
            current_envelope,
            {
                "schema_version": 1,
                "stage_id": current_stage,
                "status": "succeeded",
                "outputs": [
                    {
                        "path": str(current_report.relative_to(self.state)),
                        "sha256": MODULE.file_sha256(current_report),
                    }
                ],
            },
        )
        results = []
        chain_stages = []
        for index, identifier in enumerate(MODULE.LOCAL_STAGE_ORDER):
            status = (
                "succeeded"
                if index == 0
                else carried_status
                if index == 1
                else "not_due"
            )
            results.append(
                MODULE.LocalStageResult(
                    identifier,
                    status,
                    "fixture",
                    0 if status == "succeeded" else None,
                    str(current_envelope) if status == "succeeded" else None,
                )
            )
            last_success_at = (
                "2026-08-03T07:00:00Z"
                if status == "succeeded"
                else "2026-08-03T06:00:00Z"
            )
            chain_stages.append(
                {
                    "id": identifier,
                    "status": status,
                    "last_success_at": last_success_at,
                    "output": (
                        {
                            "sha256": "sha256:"
                            + MODULE.file_sha256(current_report)
                        }
                        if status == "succeeded"
                        else None
                    ),
                }
            )
        MODULE.atomic_write_json(
            self.run_dir / "run-chain.json",
            {
                "schema_version": 1,
                "run_id": "run-1",
                "chain_id": "run-1",
                "stages": chain_stages,
            },
        )
        candidate = MODULE.last_success_document(
            self.state,
            self.run_dir,
            results,
            run_id="run-1",
            previous=previous,
        )
        carried = candidate["stages"][MODULE.LOCAL_STAGE_ORDER[1]]
        self.assertTrue(carried["envelope"].startswith("runs/prior-run/"))
        self.assertEqual(
            MODULE.prior_run_chain_for_plan(self.state, candidate),
            self.run_dir / "run-chain.json",
        )

    def test_last_success_round_trips_mixed_success_and_not_due(self):
        self.assert_mixed_cadence_round_trip("not_due")

    def test_last_success_round_trips_mixed_success_and_degraded(self):
        self.assert_mixed_cadence_round_trip("degraded")

    def test_last_success_accepts_exact_legacy_envelope_binding(self):
        candidate = json.loads(
            (self.state / "last-success.json").read_text(encoding="utf-8")
        )
        chain_path = self.state / "runs/prior-run/run-chain.json"
        chain = json.loads(chain_path.read_text(encoding="utf-8"))
        for stage in chain["stages"]:
            stage["output"]["sha256"] = (
                "sha256:" + candidate["stages"][stage["id"]]["sha256"]
            )
        MODULE.atomic_write_json(chain_path, chain)
        self.assertEqual(
            MODULE.prior_run_chain_for_plan(self.state, candidate),
            chain_path,
        )

    def test_last_success_rejects_dot_segment_origin_run(self):
        candidate = json.loads(
            (self.state / "last-success.json").read_text(encoding="utf-8")
        )
        identifier = MODULE.LOCAL_STAGE_ORDER[0]
        candidate["stages"][identifier]["envelope"] = (
            f"runs/../stages/{identifier}/stage-result.json"
        )
        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "stage binding is malformed",
        ):
            MODULE.prior_run_chain_for_plan(self.state, candidate)

    def test_last_success_rejects_dot_segment_current_run(self):
        candidate = {
            "schema_version": 1,
            "run_id": "..",
            "run_directory": "runs/..",
            "stages": {},
        }
        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "cadence authority is malformed",
        ):
            MODULE.prior_run_chain_for_plan(self.state, candidate)

    def test_last_success_rejects_symlinked_origin_run(self):
        candidate = json.loads(
            (self.state / "last-success.json").read_text(encoding="utf-8")
        )
        alias = self.state / "runs/alias-run"
        alias.symlink_to(self.state / "runs/prior-run", target_is_directory=True)
        identifier = MODULE.LOCAL_STAGE_ORDER[0]
        candidate["stages"][identifier]["envelope"] = (
            f"runs/alias-run/stages/{identifier}/stage-result.json"
        )
        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "stage path is unsafe",
        ):
            MODULE.prior_run_chain_for_plan(self.state, candidate)

    def tearDown(self):
        self.temporary.cleanup()

    def test_production_cycle_reuses_bound_chain_and_closes_clean_noop(self):
        calls = []
        current_stage = MODULE.LOCAL_STAGE_ORDER[0]
        current_stage_dir = self.run_dir / "stages" / current_stage
        current_report = current_stage_dir / "report.json"
        MODULE.atomic_write_json(
            current_report,
            {"schema_version": 1, "stage_id": current_stage},
        )
        current_envelope = current_stage_dir / "stage-result.json"
        MODULE.atomic_write_json(
            current_envelope,
            {
                "schema_version": 1,
                "stage_id": current_stage,
                "status": "succeeded",
                "outputs": [
                    {
                        "path": str(current_report.relative_to(self.state)),
                        "sha256": MODULE.file_sha256(current_report),
                    }
                ],
            },
        )
        stage_results = [
            MODULE.LocalStageResult(
                identifier,
                "succeeded" if identifier == current_stage else "not_due",
                "due" if identifier == current_stage else "current",
                0 if identifier == current_stage else None,
                str(current_envelope) if identifier == current_stage else None,
            )
            for identifier in MODULE.LOCAL_STAGE_ORDER
        ]
        mirrored = {}
        for identifier in (
            "project-integrity-bot",
            "project-console-progress-bot",
            "public-intake",
        ):
            path = self.state / f"{identifier}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")
            mirrored[identifier] = path

        def command(command, *, cwd, accepted=frozenset({0}), environment=None):
            calls.append(tuple(command))
            if "plan" in command:
                output = Path(command[command.index("--output") + 1])
                MODULE.atomic_write_json(
                    output,
                    {
                        "review_epoch": {"due": False},
                        "elim_decision": {"launch_recommended": False},
                    },
                )
            elif "build_elim_work_queue.py" in str(command[1]):
                MODULE.atomic_write_json(
                    Path(command[command.index("--output") + 1]),
                    {"schema_version": 1, "items": []},
                )
            elif "select_elim_context_route.py" in str(command[1]):
                MODULE.atomic_write_json(
                    Path(command[command.index("--output") + 1]),
                    {
                        "profile": None,
                        "issue": None,
                        "work_item_id": None,
                        "kind": None,
                        "canonical_record": None,
                    },
                )
            return subprocess.CompletedProcess(command, 0, b"", b"")

        with (
            mock.patch.dict(
                os.environ,
                {
                    "ARRP_PROJECT_TOKEN": "inherited-project-token",
                    "GH_TOKEN": "inherited-github-token",
                    "GITHUB_TOKEN": "inherited-github-token",
                },
            ),
            mock.patch.object(
                MODULE,
                "_run_production_command",
                side_effect=command,
            ),
            mock.patch.object(
                MODULE,
                "run_local_stages",
                return_value=stage_results,
            ) as stages,
            mock.patch.object(MODULE, "_usage_remaining", return_value=80.0),
            mock.patch.object(
                MODULE,
                "_production_stage_outputs",
                return_value=mirrored,
            ),
            mock.patch.object(
                MODULE,
                "_mirror_production_inputs",
                return_value=mirrored,
            ),
            mock.patch.object(
                MODULE,
                "run_validation_specs",
                return_value=[{"id": "focused", "returncode": 0}],
            ) as validations,
            mock.patch.object(
                MODULE,
                "expand_validation_command",
                side_effect=lambda worktree, command: tuple(command),
            ),
            mock.patch.object(
                MODULE,
                "verify_worktree_entrypoint",
            ),
            mock.patch.object(
                MODULE,
                "read_keychain_secret",
                return_value=MODULE.SensitiveValue("project-token"),
            ),
            mock.patch.object(
                MODULE.GitHubAppIdentity,
                "from_json",
                return_value=mock.sentinel.app_identity,
            ),
            mock.patch.object(
                MODULE,
                "mint_installation_token",
                return_value=MODULE.SensitiveValue("app-token"),
            ),
            mock.patch.object(
                MODULE,
                "produce_repository_gate_snapshot",
                return_value={
                    "schema_version": 1,
                    "availability": "current",
                    "complete": True,
                    "count": 0,
                    "items": [],
                },
            ),
            mock.patch.object(
                MODULE,
                "create_local_final_commit",
                return_value={
                    "commit": None,
                    "classification": {
                        "ordinary": [],
                        "protected": [],
                        "prohibited": [],
                    },
                    "review_required": False,
                    "manifest": str(self.state / "manifest.json"),
                },
            ),
            mock.patch.object(
                MODULE.ProjectPathAuthority,
                "production_transaction",
                side_effect=self.fixture_production_transaction,
            ) as authority_constructor,
            mock.patch.object(
                MODULE,
                "load_validated_component_registry_routing_view",
                return_value={
                    "registry_path": "framework/component-registry.json",
                    "registry_sha256": "a" * 64,
                },
            ),
            mock.patch.object(
                MODULE,
                "routed_configuration_documents_from_view",
                return_value={"modules": []},
            ),
        ):
            result = MODULE.run_production_cycle(
                self.config,
                self.transaction,
                self.runtime,
            )

        self.assertEqual(authority_constructor.call_count, 2)
        authority_constructor.assert_called_with(
            repository_root=self.worktree.resolve(),
            run_root=self.run_dir,
        )
        self.assertIsNone(result["final_commit"]["commit"])
        self.assertIsNone(result["elim_result"])
        stages.assert_called_once()
        self.assertEqual(
            stages.call_args.kwargs["runtime_commit"],
            self.revision,
        )
        self.assertEqual(
            stages.call_args.kwargs["environment_by_stage"],
            {
                "public-intake": {
                    "GH_TOKEN": "app-token",
                },
                "project-console-progress-bot": {
                    "ARRP_PROJECT_TOKEN": "project-token",
                },
                "project-integrity-bot": {
                    "ARRP_PROJECT_TOKEN": "project-token",
                    "GH_TOKEN": "app-token",
                },
            },
        )
        for credential_name in (
            "ARRP_PROJECT_TOKEN",
            "GH_TOKEN",
            "GITHUB_TOKEN",
        ):
            self.assertNotIn(
                credential_name,
                stages.call_args.kwargs["environment"],
            )
        production_python = str(self.repository / ".venv/bin/python")
        self.assertTrue(
            all(
                spec.command[0] == production_python
                for spec in stages.call_args.kwargs["specs"]
            )
        )
        self.assertTrue(
            all(
                spec.command[0] == production_python
                for spec in validations.call_args.kwargs["specs"]
                if spec.command[0].endswith("python")
            )
        )
        self.assertEqual(
            validations.call_args.kwargs["environment_by_spec"],
            {
                "integrity-final-report": {
                    "ARRP_PROJECT_TOKEN": "project-token",
                    "GH_TOKEN": "app-token",
                },
                "console-build": {
                    "ARRP_PROJECT_TOKEN": "project-token",
                },
            },
        )
        for credential_name in (
            "ARRP_PROJECT_TOKEN",
            "GH_TOKEN",
            "GITHUB_TOKEN",
        ):
            self.assertNotIn(
                credential_name,
                validations.call_args.kwargs["environment"],
            )
        rendered = [" ".join(value) for value in calls]
        for operation in (
            " plan ",
            " record ",
            " finalize ",
            "build_elim_work_queue.py",
            "select_elim_context_route.py",
            " attach-context ",
        ):
            self.assertTrue(
                any(operation in f" {value} " for value in rendered),
                operation,
            )
        queue_call = next(
            command
            for command in calls
            if "build_elim_work_queue.py" in str(command[1])
        )
        self.assertEqual(
            queue_call[queue_call.index("--gap-obligations") + 1],
            str(self.run_dir / "gap-obligations-reconstructed.json"),
        )
        self.assertEqual(
            json.loads(
                (self.run_dir / "gap-obligations-reconstructed.json").read_text(
                    encoding="utf-8"
                )
            ),
            {
                "schema_version": 1,
                "updated_at": None,
                "governance_review": None,
                "items": [],
            },
        )
        plan_call = next(command for command in calls if "plan" in command)
        self.assertEqual(
            plan_call[plan_call.index("--previous") + 1],
            str(self.state / "runs/prior-run/run-chain.json"),
        )
        current_record_call = next(
            command
            for command in calls
            if "record" in command
            and command[command.index("--stage") + 1] == current_stage
        )
        self.assertEqual(
            current_record_call[current_record_call.index("--output-file") + 1],
            str(current_report.resolve()),
        )

    def test_production_cycle_rejects_unsafe_owner_local_run_log(self):
        run_log = self.state / "records/automation/elim-run-log.md"
        run_log.chmod(0o644)

        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "owner-local Elim Run Log is unsafe",
        ):
            MODULE.read_owner_text(
                run_log,
                label="owner-local Elim Run Log",
                maximum_bytes=8 * 1024 * 1024,
            )

    def test_production_cycle_rejects_malformed_owner_local_run_log(self):
        run_log = self.state / "records/automation/elim-run-log.md"
        run_log.write_text(
            "<!-- ELIM-DISCOVERY-V1 abcd -->\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            MODULE.TransactionError,
            "owner-local Elim Run Log cannot reconstruct gap obligations",
        ):
            MODULE.reconstruct_owner_gap_obligations(run_log)

    def test_owner_local_run_log_reader_rejects_symlink_and_oversize(self):
        run_log = self.state / "records/automation/elim-run-log.md"
        target = run_log.with_name("target.md")
        target.write_text("owner-local\n", encoding="utf-8")
        os.chmod(target, 0o600)
        run_log.unlink()
        run_log.symlink_to(target)
        with self.assertRaisesRegex(MODULE.TransactionError, "is unsafe"):
            MODULE.read_owner_text(run_log, label="run log", maximum_bytes=64)

        run_log.unlink()
        run_log.write_text("x" * 65, encoding="utf-8")
        os.chmod(run_log, 0o600)
        with self.assertRaisesRegex(MODULE.TransactionError, "is unsafe"):
            MODULE.read_owner_text(run_log, label="run log", maximum_bytes=64)

    def test_malformed_queue_error_does_not_replace_original_failure(self):
        queue = self.run_dir / "queue.json"
        queue.write_text("{", encoding="utf-8")
        self.assertIsNone(MODULE.structured_failure_detail(queue))

    def test_queue_builder_structured_error_is_preserved(self):
        queue = self.run_dir / "queue.json"

        def command(command, *, cwd, accepted=frozenset({0}), environment=None):
            if "plan" in command:
                MODULE.atomic_write_json(
                    Path(command[command.index("--output") + 1]),
                    {
                        "review_epoch": {"due": False},
                        "repository_gates": {"items": []},
                    },
                )
                return subprocess.CompletedProcess(command, 0, b"", b"")
            if "build_elim_work_queue.py" in str(command[1]):
                MODULE.atomic_write_json(
                    queue,
                    {"schema_version": 1, "status": "blocked", "error": "typed queue failure"},
                )
                raise MODULE.TransactionError("production command failed (2): ")
            return subprocess.CompletedProcess(command, 0, b"", b"")

        stage_results = [
            MODULE.LocalStageResult(identifier, "not_due", "current", None, None)
            for identifier in MODULE.LOCAL_STAGE_ORDER
        ]
        mirrored = {}
        for identifier in (
            "project-integrity-bot",
            "project-console-progress-bot",
            "public-intake",
        ):
            path = self.state / f"{identifier}.json"
            path.write_text("{}\n", encoding="utf-8")
            mirrored[identifier] = path

        with (
            mock.patch.object(MODULE, "_run_production_command", side_effect=command),
            mock.patch.object(MODULE, "run_local_stages", return_value=stage_results),
            mock.patch.object(MODULE, "_usage_remaining", return_value=80.0),
            mock.patch.object(MODULE, "_production_stage_outputs", return_value=mirrored),
            mock.patch.object(MODULE, "_mirror_production_inputs", return_value=mirrored),
            mock.patch.object(MODULE, "read_keychain_secret", return_value=MODULE.SensitiveValue("token")),
            mock.patch.object(MODULE.GitHubAppIdentity, "from_json", return_value=mock.sentinel.identity),
            mock.patch.object(MODULE, "mint_installation_token", return_value=MODULE.SensitiveValue("token")),
            mock.patch.object(
                MODULE,
                "produce_repository_gate_snapshot",
                return_value={"schema_version": 1, "availability": "current", "complete": True, "count": 0, "items": []},
            ),
            mock.patch.object(
                MODULE,
                "routing_path_authority",
                return_value=mock.sentinel.routing_authority,
            ),
            mock.patch.object(
                MODULE,
                "load_validated_component_registry_routing_view",
                return_value={
                    "registry_path": "framework/component-registry.json",
                    "registry_sha256": "a" * 64,
                },
            ),
            mock.patch.object(
                MODULE,
                "routed_configuration_documents_from_view",
                return_value={"modules": []},
            ),
            mock.patch.object(MODULE, "verify_worktree_entrypoint"),
        ):
            with self.assertRaisesRegex(
                MODULE.TransactionError,
                "Elim work queue blocked: typed queue failure",
            ):
                MODULE.run_production_cycle(
                    self.config,
                    self.transaction,
                    self.runtime,
                )

    def test_context_builder_structured_error_and_malformed_fallback(self):
        stage_results = [
            MODULE.LocalStageResult(identifier, "not_due", "current", None, None)
            for identifier in MODULE.LOCAL_STAGE_ORDER
        ]
        mirrored = {}
        for identifier in (
            "project-integrity-bot",
            "project-console-progress-bot",
            "public-intake",
        ):
            path = self.state / f"{identifier}.json"
            path.write_text("{}\n", encoding="utf-8")
            mirrored[identifier] = path

        cases = (
            (
                {"schema_version": 2, "status": "blocked", "error": "typed context failure"},
                "Elim context blocked: typed context failure",
            ),
            ("{", "production command failed \\(2\\): original context failure"),
        )
        for artifact, expected in cases:
            with self.subTest(artifact=artifact):
                context = self.run_dir / "context.json"

                def command(command, *, cwd, accepted=frozenset({0}), environment=None):
                    output = Path(command[command.index("--output") + 1]) if "--output" in command else None
                    if "plan" in command:
                        MODULE.atomic_write_json(
                            output,
                            {
                                "review_epoch": {"due": False},
                                "repository_gates": {"items": []},
                            },
                        )
                    elif "build_elim_work_queue.py" in str(command[1]):
                        MODULE.atomic_write_json(output, {"schema_version": 1, "items": []})
                    elif "select_elim_context_route.py" in str(command[1]):
                        MODULE.atomic_write_json(
                            output,
                            {
                                "profile": "issue",
                                "issue": None,
                                "work_item_id": "TEST-001",
                                "kind": "issue",
                                "canonical_record": None,
                            },
                        )
                    elif "build_elim_context.py" in str(command[1]):
                        if isinstance(artifact, dict):
                            MODULE.atomic_write_json(output, artifact)
                        else:
                            output.write_text(artifact, encoding="utf-8")
                        raise MODULE.TransactionError(
                            "production command failed (2): original context failure"
                        )
                    return subprocess.CompletedProcess(command, 0, b"", b"")

                with (
                    mock.patch.object(MODULE, "_run_production_command", side_effect=command),
                    mock.patch.object(MODULE, "run_local_stages", return_value=stage_results),
                    mock.patch.object(MODULE, "_usage_remaining", return_value=80.0),
                    mock.patch.object(MODULE, "_production_stage_outputs", return_value=mirrored),
                    mock.patch.object(MODULE, "_mirror_production_inputs", return_value=mirrored),
                    mock.patch.object(MODULE, "read_keychain_secret", return_value=MODULE.SensitiveValue("token")),
                    mock.patch.object(MODULE.GitHubAppIdentity, "from_json", return_value=mock.sentinel.identity),
                    mock.patch.object(MODULE, "mint_installation_token", return_value=MODULE.SensitiveValue("token")),
                    mock.patch.object(
                        MODULE,
                        "produce_repository_gate_snapshot",
                        return_value={"schema_version": 1, "availability": "current", "complete": True, "count": 0, "items": []},
                    ),
                    mock.patch.object(
                        MODULE,
                        "routing_path_authority",
                        return_value=mock.sentinel.routing_authority,
                    ),
                    mock.patch.object(
                        MODULE,
                        "load_validated_component_registry_routing_view",
                        return_value={
                            "registry_path": "framework/component-registry.json",
                            "registry_sha256": "a" * 64,
                        },
                    ),
                    mock.patch.object(
                        MODULE,
                        "routed_configuration_documents_from_view",
                        return_value={"modules": []},
                    ),
                    mock.patch.object(MODULE, "verify_worktree_entrypoint"),
                ):
                    with self.assertRaisesRegex(MODULE.TransactionError, expected):
                        MODULE.run_production_cycle(
                            self.config,
                            self.transaction,
                            self.runtime,
                        )
                self.assertTrue(context.exists())

    def test_noop_publication_removes_only_registered_run_state(self):
        summary = {
            "phase": "P6",
            "final_commit": {"commit": None},
            "last_success_candidate": {
                "schema_version": 1,
                "run_id": "run-1",
                "stages": {},
            },
        }
        with (
            mock.patch.object(MODULE, "status_manifest", return_value=[]),
            mock.patch.object(
                MODULE,
                "classify_publication_range",
                return_value={
                    "classification": {
                        "ordinary": [],
                        "protected": [],
                        "prohibited": [],
                    },
                    "review_required": False,
                },
            ),
            mock.patch.object(
                MODULE,
                "remove_successful_transaction_worktree",
            ) as remove,
            mock.patch.object(MODULE, "git") as git_call,
            mock.patch.object(MODULE, "git_text", return_value=self.revision),
            mock.patch.object(
                MODULE.ProjectPathAuthority,
                "production_transaction",
                side_effect=self.fixture_production_transaction,
            ) as authority_constructor,
        ):
            result = MODULE.publish_production_transaction(
                self.config,
                self.transaction,
                summary,
            )
        authority_constructor.assert_called_once_with(
            repository_root=self.worktree.resolve(),
            run_root=self.run_dir,
        )
        self.assertTrue(result["no_op"])
        remove.assert_called_once()
        git_call.assert_called_once_with(
            self.repository,
            "branch",
            "-d",
            "automation/nightly-run-1",
        )

    def test_scheduled_cli_wires_runtime_cycle_and_publication_without_plan(self):
        transaction = MODULE.TransactionResult(
            "cli-run",
            "completed",
            None,
            None,
            None,
            self.revision,
        )

        def prepare(config, **kwargs):
            self.assertEqual(config.trigger, "scheduled")
            self.assertEqual(config.runtime_commit, self.revision)
            self.assertIsNotNone(config.scheduled_for)
            self.assertIsNotNone(kwargs["local_cycle"])
            self.assertIsNotNone(kwargs["publication_cycle"])
            return transaction

        with (
            mock.patch.object(
                MODULE,
                "verify_executed_runtime",
                return_value=self.runtime,
            ),
            mock.patch.object(MODULE, "prepare_transaction", side_effect=prepare),
        ):
            self.assertEqual(
                MODULE.main(
                    [
                        "--scheduled",
                        "--runtime-commit",
                        self.revision,
                    ]
                ),
                0,
            )


if __name__ == "__main__":
    unittest.main()
