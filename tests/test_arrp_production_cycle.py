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
        (self.worktree / ".github").mkdir()
        (self.worktree / ".github/run-coordinator-bot.json").write_text(
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

    def tearDown(self):
        self.temporary.cleanup()

    def test_production_cycle_reuses_bound_chain_and_closes_clean_noop(self):
        calls = []
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
        ):
            result = MODULE.run_production_cycle(
                self.config,
                self.transaction,
                self.runtime,
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
        ):
            result = MODULE.publish_production_transaction(
                self.config,
                self.transaction,
                summary,
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
