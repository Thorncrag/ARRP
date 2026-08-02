import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from tests.test_arrp_nightly import GitFixture, MODULE
from scripts.operational_incidents import (
    project_incident_log,
    reconcile_failure_spool,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/local-first"


def stage_spec(
    identifier: str,
    output: str,
    *,
    cadence: int | None = 24,
    failure: str = "blocking",
    exit_code: int = 0,
) -> MODULE.LocalStageSpec:
    return MODULE.LocalStageSpec(
        identifier,
        cadence,
        failure,
        (
            sys.executable,
            str(FIXTURES / "stage_fixture.py"),
            "--stage-id",
            identifier,
            "--output",
            output,
            "--exit-code",
            str(exit_code),
        ),
        (output,),
    )


class LocalStageTests(unittest.TestCase):
    def test_invalid_elim_result_is_preserved_in_failure_safe_incident_spool(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = GitFixture(root)

            def invalid_elim(_transaction):
                raise MODULE.TransactionError(
                    "sealed production Elim returned no valid result"
                )

            with self.assertRaisesRegex(MODULE.TransactionError, "no valid result"):
                MODULE.prepare_transaction(
                    fixture.config(),
                    run_id="invalid-elim-result",
                    local_cycle=invalid_elim,
                )

            spool = fixture.state / "incident-spool.jsonl"
            self.assertTrue(spool.is_file())
            rows = [
                json.loads(line)
                for line in spool.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["run_id"], "invalid-elim-result")
            self.assertNotIn("token", rows[0]["diagnostic"].lower())

            events = root / "reconciled-incidents.jsonl"
            self.assertEqual(reconcile_failure_spool(spool, events), 1)
            projection = project_incident_log(events)
            self.assertEqual(projection["unresolved_count"], 1)
            self.assertEqual(
                projection["items"][0]["affected_runs"],
                ["invalid-elim-result"],
            )

    def test_due_stage_is_reproducible_and_current_typed_output_is_not_due(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            worktree = root / "worktree"
            run_dir = state / "runs/run-1"
            worktree.mkdir()
            now = datetime(2026, 7, 27, tzinfo=timezone.utc)
            spec = stage_spec(
                "case-monitor-bot",
                "{run_dir}/stages/case-monitor-bot/report.json",
            )
            first = MODULE.run_local_stages(
                worktree=worktree,
                run_dir=run_dir,
                state_root=state,
                specs=(spec,),
                now=now,
            )
            self.assertEqual(first[0].status, "succeeded")
            first_hash = MODULE.file_sha256(
                run_dir / "stages/case-monitor-bot/report.json"
            )
            repeated = MODULE.run_local_stages(
                worktree=worktree,
                run_dir=state / "runs/repeated",
                state_root=state,
                specs=(spec,),
                now=now,
            )
            self.assertEqual(repeated[0].status, "succeeded")
            self.assertEqual(
                first_hash,
                MODULE.file_sha256(
                    state / "runs/repeated/stages/case-monitor-bot/report.json"
                ),
            )
            success = MODULE.last_success_document(
                state, run_dir, first, run_id="run-1"
            )
            second = MODULE.run_local_stages(
                worktree=worktree,
                run_dir=state / "runs/run-2",
                state_root=state,
                specs=(spec,),
                last_success=success,
                now=now + timedelta(hours=1),
            )
            self.assertEqual(second[0].status, "not_due")
            missing_success = json.loads(json.dumps(success))
            missing_success["stages"]["case-monitor-bot"]["envelope"] = (
                "runs/missing/stage-result.json"
            )
            due, reason = MODULE.determine_stage_due(
                state, spec, missing_success, now=now + timedelta(hours=1)
            )
            self.assertTrue(due)
            self.assertEqual(reason, "missing_stale_or_invalid_typed_output")
            report = run_dir / "stages/case-monitor-bot/report.json"
            original = report.read_text(encoding="utf-8")
            report.write_text(original.replace("fixture", "tampered"), encoding="utf-8")
            due, reason = MODULE.determine_stage_due(
                state, spec, success, now=now + timedelta(hours=1)
            )
            self.assertTrue(due)
            self.assertEqual(reason, "missing_stale_or_invalid_typed_output")

    def test_stale_typed_output_forces_due(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            worktree = root / "worktree"
            worktree.mkdir()
            run_dir = state / "runs/run-1"
            now = datetime(2026, 7, 20, tzinfo=timezone.utc)
            spec = stage_spec(
                "case-monitor-bot",
                "{run_dir}/stages/case-monitor-bot/report.json",
            )
            result = MODULE.run_local_stages(
                worktree=worktree,
                run_dir=run_dir,
                state_root=state,
                specs=(spec,),
                now=now,
            )
            success = MODULE.last_success_document(
                state, run_dir, result, run_id="run-1"
            )
            due, _ = MODULE.determine_stage_due(
                state, spec, success, now=now + timedelta(hours=25)
            )
            self.assertTrue(due)

    def test_blocking_failure_stops_and_degraded_failure_continues(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            worktree = root / "worktree"
            worktree.mkdir()
            blocking = stage_spec(
                "case-monitor-bot",
                "{run_dir}/stages/case-monitor-bot/report.json",
                exit_code=7,
            )
            later = stage_spec(
                "presidential-directives-bot",
                "{run_dir}/stages/presidential-directives-bot/report.json",
            )
            stopped = MODULE.run_local_stages(
                worktree=worktree,
                run_dir=state / "runs/block",
                state_root=state,
                specs=(blocking, later),
            )
            self.assertEqual([row.status for row in stopped], ["failed"])
            degraded = stage_spec(
                "source-checker-bot",
                "{run_dir}/stages/source-checker-bot/report.json",
                failure="degraded",
                exit_code=8,
            )
            continued = MODULE.run_local_stages(
                worktree=worktree,
                run_dir=state / "runs/degraded",
                state_root=state,
                specs=(degraded, later),
            )
            self.assertEqual(
                [row.status for row in continued], ["degraded", "succeeded"]
            )

    def test_production_stage_order_and_entry_points(self):
        specs = MODULE.default_local_stage_specs("python3")
        self.assertEqual(tuple(row.identifier for row in specs), MODULE.LOCAL_STAGE_ORDER)
        expected = (
            "check_case_updates.py",
            "check_presidential_directives.py",
            "check_source_urls.py",
            "collect_public_intake.py",
            "build_project_console_progress.py",
            "audit_project_consistency.py",
        )
        self.assertEqual(
            tuple(Path(row.command[1]).name for row in specs),
            expected,
        )
        integrity = next(
            row for row in specs if row.identifier == "project-integrity-bot"
        )
        self.assertIn("--routing-authority", integrity.command)
        self.assertEqual(
            integrity.command[
                integrity.command.index("--routing-authority") + 1
            ],
            "production-transaction",
        )
        final_integrity = next(
            row
            for row in MODULE.default_post_elim_validation_specs()
            if row.identifier == "integrity-final-report"
        )
        self.assertIn("--routing-authority", final_integrity.command)
        self.assertEqual(
            final_integrity.command[
                final_integrity.command.index("--routing-authority") + 1
            ],
            "production-transaction",
        )
        coordinator = json.loads(
            (ROOT / "framework/project/automation/configuration/bots/run-coordinator-bot.json").read_text(
                encoding="utf-8"
            )
        )
        registered_integrity = next(
            row
            for row in coordinator["stages"]
            if row["id"] == "project-integrity-bot"
        )
        self.assertIn(
            "--routing-authority production-transaction",
            registered_integrity["command"],
        )

    def test_project_progress_stage_validates_the_generated_json_leaf(self):
        progress = next(
            row
            for row in MODULE.default_local_stage_specs("python3")
            if row.identifier == "project-console-progress-bot"
        )
        output_root = progress.command[progress.command.index("--output") + 1]
        self.assertEqual(
            output_root,
            "{run_dir}/stages/project-console-progress-bot/data",
        )
        self.assertEqual(
            progress.outputs,
            (
                "{run_dir}/stages/project-console-progress-bot/data/progress.json",
            ),
        )

    def test_stage_environment_override_is_confined_to_named_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state"
            worktree = root / "worktree"
            worktree.mkdir()
            first = stage_spec(
                "case-monitor-bot",
                "{run_dir}/stages/case-monitor-bot/report.json",
            )
            progress = stage_spec(
                "project-console-progress-bot",
                "{run_dir}/stages/project-console-progress-bot/report.json",
            )
            original_run = MODULE.subprocess.run
            environments = []

            def recording_run(*args, **kwargs):
                environments.append(dict(kwargs["env"]))
                return original_run(*args, **kwargs)

            with mock.patch.object(MODULE.subprocess, "run", side_effect=recording_run):
                result = MODULE.run_local_stages(
                    worktree=worktree,
                    run_dir=state / "runs/run-1",
                    state_root=state,
                    specs=(first, progress),
                    environment={"PATH": os.environ["PATH"]},
                    environment_by_stage={
                        "project-console-progress-bot": {
                            "ARRP_PROJECT_TOKEN": "project-token",
                        }
                    },
                )

            self.assertEqual([row.status for row in result], ["succeeded", "succeeded"])
            self.assertNotIn("ARRP_PROJECT_TOKEN", environments[0])
            self.assertEqual(environments[1]["ARRP_PROJECT_TOKEN"], "project-token")


class SealedElimTests(unittest.TestCase):
    def test_command_and_environment_remove_inherited_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            worktree = root / "worktree"
            run_dir = root / "run"
            home = root / "codex-home"
            sqlite_home = root / "codex-sqlite-home"
            for path in (worktree, run_dir, home, sqlite_home):
                path.mkdir()
            environment = MODULE.sealed_elim_environment(
                {
                    "HOME": str(root),
                    "PATH": os.environ["PATH"],
                    "GH_TOKEN": "forbidden",
                    "GITHUB_TOKEN": "forbidden",
                    "OPENAI_API_KEY": "forbidden",
                    "SSH_AUTH_SOCK": "forbidden",
                },
                worktree=worktree,
                run_dir=run_dir,
                model="fixture-model",
                codex_home=home,
                codex_sqlite_home=sqlite_home,
            )
            self.assertFalse(
                {"GH_TOKEN", "GITHUB_TOKEN", "OPENAI_API_KEY", "SSH_AUTH_SOCK"}
                & set(environment)
            )
            self.assertEqual(environment["CODEX_HOME"], str(home))
            self.assertEqual(environment["CODEX_SQLITE_HOME"], str(sqlite_home))
            command = MODULE.sealed_elim_command(
                codex=root / "codex",
                worktree=worktree,
                run_dir=run_dir,
                model="fixture-model",
                schema=worktree / "schema.json",
            )
            joined = " ".join(command)
            for required in (
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--strict-config",
                'default_permissions="arrp_elim"',
                'permissions.arrp_elim.extends=":workspace"',
                'permissions.arrp_elim.filesystem."/usr/bin/security"="deny"',
                "permissions.arrp_elim.network.enabled=false",
                'shell_environment_policy.inherit="none"',
                "allow_login_shell=false",
                'approval_policy="never"',
            ):
                self.assertIn(required, joined)
            self.assertNotIn("--sandbox workspace-write", joined)
            for feature in MODULE.SEALED_DISABLED_FEATURES:
                self.assertIn(f"--disable {feature}", joined)

    def test_result_binding_rejects_git_protected_and_action_authority(self):
        base = {
            "run_id": "run",
            "unit_id": "unit",
            "commit": None,
            "synchronization": [],
            "github_action_requests": [],
            "incident_reports": [],
            "files_touched": ["research/result.md"],
        }
        MODULE.validate_elim_result_boundary(
            base,
            run_id="run",
            unit_id="unit",
            files_touched=["research/result.md"],
        )
        for change in (
            {"commit": "a" * 40},
            {"github_action_requests": [{"kind": "issue"}]},
            {"files_touched": ["scripts/arrp_nightly.py"]},
        ):
            value = {**base, **change}
            with self.assertRaises(MODULE.TransactionError):
                MODULE.validate_elim_result_boundary(
                    value,
                    run_id="run",
                    unit_id="unit",
                    files_touched=value["files_touched"],
                )

    def test_git_metadata_mutation_is_detectable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = GitFixture(root)
            before = MODULE.git_metadata_snapshot(fixture.repo)
            issue = fixture.repo / "areas/TEST/issues/TEST-001.md"
            issue.write_text("staged mutation\n", encoding="utf-8")
            from tests.test_arrp_nightly import run

            run("git", "add", "areas/TEST/issues/TEST-001.md", cwd=fixture.repo)
            after = MODULE.git_metadata_snapshot(fixture.repo)
            self.assertNotEqual(before, after)

    def test_full_fixture_cycle_has_no_publication_or_session_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = GitFixture(root)
            schema = fixture.repo / "framework/project/automation/schemas/elim-work-unit-result.schema.json"
            schema.parent.mkdir(parents=True)
            schema.write_text('{"type":"object"}\n', encoding="utf-8")
            from tests.test_arrp_nightly import run

            run("git", "add", str(schema.relative_to(fixture.repo)), cwd=fixture.repo)
            run("git", "commit", "-m", "fixture schema", cwd=fixture.repo)
            plan = root / "p2-plan.json"
            fixture_codex = root / "codex-fixture.py"
            shutil.copyfile(FIXTURES / "codex_fixture.py", fixture_codex)
            os.chmod(fixture_codex, 0o755)
            stage_rows = []
            for identifier in MODULE.LOCAL_STAGE_ORDER:
                output = f"{{run_dir}}/stages/{identifier}/report.json"
                stage_rows.append(
                    {
                        "id": identifier,
                        "cadence_hours": None
                        if identifier in {"public-intake", "project-integrity-bot"}
                        else 24,
                        "failure_class": "degraded"
                        if identifier in {"source-checker-bot", "public-intake"}
                        else "blocking",
                        "command": list(stage_spec(identifier, output).command),
                        "outputs": [output],
                    }
                )
            plan.write_text(
                json.dumps(
                    {
                        "stages": stage_rows,
                        "queue_command": [
                            sys.executable,
                            str(FIXTURES / "selection_fixture.py"),
                            "--kind",
                            "queue",
                            "--output",
                            "{run_dir}/queue.json",
                        ],
                        "context_command": [
                            sys.executable,
                            str(FIXTURES / "selection_fixture.py"),
                            "--kind",
                            "context",
                            "--output",
                            "{run_dir}/context.json",
                        ],
                        "elim": {
                            "codex": str(fixture_codex),
                            "schema": "framework/project/automation/schemas/elim-work-unit-result.schema.json",
                            "model": "fixture-model",
                            "unit_id": "fixture-unit",
                            "prompt": json.dumps(
                                {
                                    "run_id": "p2-full-cycle",
                                    "unit_id": "fixture-unit",
                                }
                            ),
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            cycle_result = {}

            def run_cycle(transaction):
                with mock.patch.dict(
                    os.environ,
                    {
                        "GH_TOKEN": "must-not-pass",
                        "GITHUB_TOKEN": "must-not-pass",
                        "OPENAI_API_KEY": "must-not-pass",
                    },
                ):
                    cycle_result.update(
                        MODULE.run_p2_fixture_cycle(
                            fixture.config(), transaction, plan
                        )
                    )
                return cycle_result

            transaction = MODULE.prepare_transaction(
                fixture.config(),
                run_id="p2-full-cycle",
                local_cycle=run_cycle,
            )
            result = cycle_result
            self.assertFalse(result["publication_attempted"])
            self.assertTrue(result["git_metadata_immutable"])
            self.assertFalse(result["persistent_session_required"])
            self.assertEqual(result["files_touched"], ["research/elim-fixture.txt"])
            invocation = json.loads(
                (fixture.state / "runs/p2-full-cycle/elim-invocation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(
                {"GH_TOKEN", "GITHUB_TOKEN", "OPENAI_API_KEY"}
                & set(invocation["environment_keys"])
            )
            codex_home = fixture.state / "runs/p2-full-cycle/codex-home"
            self.assertEqual(list(codex_home.iterdir()), [])
            status = json.loads(
                (fixture.state / "status.json").read_text(encoding="utf-8")
            )
            self.assertEqual(status["elim_unit"], "fixture-unit")
            self.assertEqual(status["elim_outcome"], "completed")


if __name__ == "__main__":
    unittest.main()
