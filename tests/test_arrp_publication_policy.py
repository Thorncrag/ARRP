import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.test_arrp_local_stages import FIXTURES, stage_spec
from tests.test_arrp_nightly import GitFixture, MODULE, run

ROOT = Path(__file__).resolve().parents[1]


def write_predecessor_route_fixture(
    repository: Path,
    *,
    governing_path: str,
) -> Path:
    source = repository / governing_path
    registry = (
        repository
        / "framework"
        / "project"
        / "automation"
        / "context-routes.json"
    )
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "required_modules": ["fixture_governing"],
                "documents": {
                    "fixture_governing": {
                        "path": governing_path,
                        "requires": [],
                        "governing": True,
                        "hash_policy": "pinned",
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    }
                },
                "capabilities": {},
                "profiles": {
                    "fixture": {
                        "sections": [],
                        "modules": ["fixture_governing"],
                        "capabilities": [],
                        "max_bytes": 4096,
                    }
                },
                "generated_path_exclusions": [],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return registry


class PublicationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fixture = GitFixture(self.root)
        self.run_dir = self.fixture.state / "runs/p3-policy"
        self.run_dir.mkdir(parents=True)
        self.path_authority = MODULE.routing_path_authority(
            self.fixture.config(),
            self.fixture.repo,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def finalize(self):
        return MODULE.create_local_final_commit(
            self.fixture.repo,
            self.run_dir,
            message="fixture local final commit",
            path_authority=self.path_authority,
        )

    def test_ordinary_protected_prohibited_and_mixed_classification(self):
        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.write_text("ordinary final work\n", encoding="utf-8")
        ordinary = self.finalize()
        self.assertEqual(
            ordinary["classification"]["ordinary"],
            ["areas/TEST/issues/TEST-001.md"],
        )
        self.assertFalse(ordinary["review_required"])

        script = self.fixture.repo / "scripts/arrp_nightly.py"
        script.write_text("print('protected final work')\n", encoding="utf-8")
        protected = self.finalize()
        self.assertEqual(
            protected["classification"]["protected"],
            ["scripts/arrp_nightly.py"],
        )
        self.assertTrue(protected["review_required"])

        issue.write_text("mixed ordinary work\n", encoding="utf-8")
        script.write_text("print('mixed protected work')\n", encoding="utf-8")
        mixed = self.finalize()
        self.assertEqual(
            mixed["classification"]["ordinary"],
            ["areas/TEST/issues/TEST-001.md"],
        )
        self.assertEqual(
            mixed["classification"]["protected"],
            ["scripts/arrp_nightly.py"],
        )
        self.assertTrue(mixed["review_required"])

        private = self.fixture.repo / "research/.env.secret"
        private.parent.mkdir(exist_ok=True)
        private.write_text("fixture private material\n", encoding="utf-8")
        with self.assertRaisesRegex(MODULE.TransactionError, "prohibited paths"):
            self.finalize()
        self.assertTrue(private.exists())

    def test_new_file_class_is_protected(self):
        tool = self.fixture.repo / "research/new-tool.py"
        tool.parent.mkdir(exist_ok=True)
        tool.write_text("print('new class')\n", encoding="utf-8")
        result = self.finalize()
        self.assertEqual(
            result["classification"]["protected"],
            ["research/new-tool.py"],
        )
        self.assertTrue(result["review_required"])

    def test_governing_registry_path_is_dynamically_protected(self):
        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.write_text("governing change\n", encoding="utf-8")
        registry = write_predecessor_route_fixture(
            self.fixture.repo,
            governing_path="areas/TEST/issues/TEST-001.md",
        )
        run(
            "git",
            "add",
            str(registry.relative_to(self.fixture.repo)),
            cwd=self.fixture.repo,
        )
        run("git", "commit", "-m", "fixture governing registry", cwd=self.fixture.repo)
        result = self.finalize()
        self.assertEqual(
            result["classification"]["protected"],
            ["areas/TEST/issues/TEST-001.md"],
        )
        self.assertTrue(result["review_required"])

    def test_full_post_elim_validation_command_set_is_bound(self):
        specs = MODULE.default_post_elim_validation_specs()
        identifiers = {spec.identifier for spec in specs}
        self.assertEqual(
            identifiers,
            {
                "integrity-final-report",
                "integrity-final-feed",
                "console-build",
                "site-prepare",
                "site-build",
                "python-tests",
                "console-tests",
                "participation-tests",
                "python-compile",
                "diff-check",
                "launchagent-template",
            },
        )

    def test_validation_globs_expand_only_path_arguments(self):
        tests = self.fixture.repo / "tests/participation"
        tests.mkdir(parents=True)
        (tests / "first.test.js").write_text("// fixture\n", encoding="utf-8")
        (tests / "second.test.js").write_text("// fixture\n", encoding="utf-8")

        expanded = MODULE.expand_validation_command(
            self.fixture.repo,
            (
                "python",
                "-m",
                "unittest",
                "discover",
                "-p",
                "test_*.py",
                "tests/participation/*.test.js",
            ),
        )

        self.assertIn("test_*.py", expanded)
        self.assertEqual(
            expanded[-2:],
            (
                "tests/participation/first.test.js",
                "tests/participation/second.test.js",
            ),
        )

    def test_validation_credentials_are_confined_to_named_spec(self):
        environments = []

        def record_run(command, **kwargs):
            environments.append(dict(kwargs["env"]))
            return subprocess.CompletedProcess(command, 0, b"", b"")

        with mock.patch.object(
            MODULE.subprocess,
            "run",
            side_effect=record_run,
        ):
            MODULE.run_validation_specs(
                worktree=self.fixture.repo,
                run_dir=self.run_dir,
                specs=(
                    MODULE.ValidationSpec("public-check", ("true",)),
                    MODULE.ValidationSpec("console-build", ("true",)),
                ),
                environment={"PATH": os.environ["PATH"]},
                environment_by_spec={
                    "console-build": {
                        "ARRP_PROJECT_TOKEN": "project-token",
                    },
                },
            )

        self.assertNotIn("ARRP_PROJECT_TOKEN", environments[0])
        self.assertNotIn("GH_TOKEN", environments[0])
        self.assertEqual(
            environments[1]["ARRP_PROJECT_TOKEN"],
            "project-token",
        )
        self.assertNotIn("GH_TOKEN", environments[1])

    def test_symlink_submodule_and_executable_mode_are_rejected(self):
        symlink = self.fixture.repo / "research/link.md"
        symlink.parent.mkdir(exist_ok=True)
        symlink.symlink_to("../areas/TEST/issues/TEST-001.md")
        with self.assertRaisesRegex(MODULE.TransactionError, "symlink change"):
            self.finalize()
        symlink.unlink()

        commit = run("git", "rev-parse", "HEAD", cwd=self.fixture.repo)
        run(
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{commit},research/submodule",
            cwd=self.fixture.repo,
        )
        with self.assertRaisesRegex(MODULE.TransactionError, "submodule change"):
            self.finalize()
        run("git", "update-index", "--force-remove", "research/submodule", cwd=self.fixture.repo)

        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.chmod(0o755)
        with self.assertRaisesRegex(MODULE.TransactionError, "executable mode change"):
            self.finalize()

    def test_secret_detector_redacts_value_and_blocks_commit(self):
        token = "ghp_" + "A" * 36
        path = self.fixture.repo / "research/fixture-secret.txt"
        path.parent.mkdir(exist_ok=True)
        path.write_text(f"token={token}\n", encoding="utf-8")
        with self.assertRaisesRegex(MODULE.TransactionError, "secret/private detector"):
            self.finalize()
        manifest = json.loads(
            (self.run_dir / "final-staging-manifest.json").read_text(encoding="utf-8")
        )
        encoded = json.dumps(manifest, sort_keys=True)
        self.assertNotIn(token, encoded)
        self.assertEqual(
            manifest["secret_private_findings"][0]["detector"],
            "github-token",
        )
        self.assertEqual(
            set(manifest["secret_private_findings"][0]),
            {"path", "line", "detector", "finding_id"},
        )

    def test_commit_tree_exactly_matches_manifest(self):
        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.write_text("exact manifest\n", encoding="utf-8")
        added = self.fixture.repo / "research/new-record.md"
        added.parent.mkdir(exist_ok=True)
        added.write_text("new record\n", encoding="utf-8")
        result = self.finalize()
        manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
        expected = sorted(row["path"] for row in manifest["records"])
        observed = run(
            "git",
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            result["commit"],
            cwd=self.fixture.repo,
        ).splitlines()
        self.assertEqual(sorted(observed), expected)
        self.assertEqual(run("git", "status", "--porcelain", cwd=self.fixture.repo), "")

    def test_rename_stages_old_and_new_paths_and_matches_manifest(self):
        old = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        new = self.fixture.repo / "areas/TEST/issues/TEST-RENAMED.md"
        old.rename(new)
        result = self.finalize()
        manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(
            sorted((row["status"], row["path"]) for row in manifest["records"]),
            [
                ("A", "areas/TEST/issues/TEST-RENAMED.md"),
                ("D", "areas/TEST/issues/TEST-001.md"),
            ],
        )
        self.assertFalse(old.exists())
        self.assertTrue(new.exists())
        self.assertEqual(run("git", "status", "--porcelain", cwd=self.fixture.repo), "")


class TrustedConsolePublicationTests(unittest.TestCase):
    def prepared_repository(
        self,
        root: Path,
        *,
        ordinary_mix: bool = False,
        protected_mix: bool = False,
    ) -> tuple[Path, str, str]:
        repository = root / "trusted-console"
        run("git", "init", "-b", "main", str(repository))
        GitFixture.configure(repository)
        for relative in (
            "framework/component-registry.json",
            ".github/CODEOWNERS",
        ):
            source = ROOT / relative
            target = repository / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        data_target = (
            repository / "framework/project/interfaces/project-console/data"
        )
        data_target.mkdir(parents=True)
        tracked_data = run(
            "git",
            "ls-files",
            "framework/project/interfaces/project-console/data/",
            cwd=ROOT,
        ).splitlines()
        for relative in tracked_data:
            shutil.copyfile(ROOT / relative, data_target / Path(relative).name)
        catalog = (
            repository
            / "framework/project/interfaces/project-console/catalog-data.js"
        )
        catalog.parent.mkdir(parents=True, exist_ok=True)
        catalog.write_text("old generated catalog\n", encoding="utf-8")
        script = repository / "scripts/fixture.py"
        script.parent.mkdir(parents=True)
        script.write_text("baseline\n", encoding="utf-8")
        issue = repository / "areas/TEST/issues/TEST-001.md"
        issue.parent.mkdir(parents=True)
        issue.write_text("baseline\n", encoding="utf-8")
        run("git", "add", "--", ".", cwd=repository)
        run("git", "commit", "-m", "fixture base", cwd=repository)
        base = run("git", "rev-parse", "HEAD", cwd=repository)

        shutil.copyfile(
            ROOT / "framework/project/interfaces/project-console/catalog-data.js",
            catalog,
        )
        if ordinary_mix:
            issue.write_text("ordinary change\n", encoding="utf-8")
        if protected_mix:
            script.write_text("protected change\n", encoding="utf-8")
        run("git", "add", "--", ".", cwd=repository)
        run("git", "commit", "-m", "fixture head", cwd=repository)
        head = run("git", "rev-parse", "HEAD", cwd=repository)
        return repository, base, head

    def test_exact_app_generated_only_passes_and_human_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            repository, base, head = self.prepared_repository(Path(directory))
            result = MODULE.validate_trusted_console_pull_request(
                repository,
                base_commit=base,
                head_commit=head,
                pull_request_author=MODULE.TRUSTED_CONSOLE_PR_ACTOR,
                pull_request_author_type="Bot",
                event_actor=MODULE.TRUSTED_CONSOLE_PR_ACTOR,
            )
            self.assertTrue(result["generated_only"])
            with self.assertRaisesRegex(
                MODULE.TransactionError,
                "exact Automation App",
            ):
                MODULE.validate_trusted_console_pull_request(
                    repository,
                    base_commit=base,
                    head_commit=head,
                    pull_request_author="human",
                    pull_request_author_type="User",
                    event_actor="human",
                )

    def test_human_console_plus_unowned_fails_but_owned_mix_is_reviewed(self):
        with tempfile.TemporaryDirectory() as directory:
            repository, base, head = self.prepared_repository(
                Path(directory),
                ordinary_mix=True,
            )
            with self.assertRaisesRegex(
                MODULE.TransactionError,
                "ordinary unowned",
            ):
                MODULE.validate_trusted_console_pull_request(
                    repository,
                    base_commit=base,
                    head_commit=head,
                    pull_request_author="human",
                    pull_request_author_type="User",
                    event_actor="human",
                )
            app_result = MODULE.validate_trusted_console_pull_request(
                repository,
                base_commit=base,
                head_commit=head,
                pull_request_author=MODULE.TRUSTED_CONSOLE_PR_ACTOR,
                pull_request_author_type="Bot",
                event_actor=MODULE.TRUSTED_CONSOLE_PR_ACTOR,
            )
            self.assertTrue(app_result["exact_app"])
            self.assertFalse(app_result["generated_only"])
        with tempfile.TemporaryDirectory() as directory:
            repository, base, head = self.prepared_repository(
                Path(directory),
                protected_mix=True,
            )
            result = MODULE.validate_trusted_console_pull_request(
                repository,
                base_commit=base,
                head_commit=head,
                pull_request_author="human",
                pull_request_author_type="User",
                event_actor="human",
            )
            self.assertFalse(result["generated_only"])
            self.assertEqual(
                MODULE.classify_path(
                    "scripts/fixture.py",
                    0o644,
                    tracked=True,
                ),
                "protected",
            )

    def test_tampered_or_extra_console_domain_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            repository, _base, head = self.prepared_repository(Path(directory))
            domain = (
                repository
                / "framework/project/interfaces/project-console/data/automation.js"
            )
            domain.write_text(
                domain.read_text(encoding="utf-8") + "alert('unexpected');\n",
                encoding="utf-8",
            )
            run("git", "add", "--", str(domain.relative_to(repository)), cwd=repository)
            run("git", "commit", "-m", "tamper domain", cwd=repository)
            tampered = run("git", "rev-parse", "HEAD", cwd=repository)
            with self.assertRaises(MODULE.TransactionError):
                MODULE.validate_trusted_console_generation(repository, tampered)
            self.assertNotEqual(head, tampered)

        with tempfile.TemporaryDirectory() as directory:
            repository, _base, _head = self.prepared_repository(Path(directory))
            extra = (
                repository
                / "framework/project/interfaces/project-console/data/extra.js"
            )
            extra.write_text("alert('unexpected');\n", encoding="utf-8")
            run("git", "add", "--", str(extra.relative_to(repository)), cwd=repository)
            run("git", "commit", "-m", "extra domain", cwd=repository)
            extra_head = run("git", "rev-parse", "HEAD", cwd=repository)
            with self.assertRaisesRegex(
                MODULE.TransactionError,
                "inventory differs",
            ):
                MODULE.validate_trusted_console_generation(repository, extra_head)

    def test_source_monitor_log_is_protected(self):
        self.assertEqual(
            MODULE.classify_path(
                "framework/logs/sources/source-monitor-log.md",
                0o644,
                tracked=True,
            ),
            "protected",
        )


class P3FixtureTransactionTests(unittest.TestCase):
    def test_complete_fixture_transaction_ends_in_local_final_commit_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = GitFixture(root)
            schema = (
                fixture.repo
                / "framework/project/automation/schemas/elim-work-unit-result.schema.json"
            )
            schema.parent.mkdir(parents=True)
            schema.write_text('{"type":"object"}\n', encoding="utf-8")
            gitignore = fixture.repo / ".gitignore"
            gitignore.write_text(
                gitignore.read_text(encoding="utf-8")
                + "/framework/project/interfaces/project-console/data/local-automation-status.js\n",
                encoding="utf-8",
            )
            run("git", "add", str(schema.relative_to(fixture.repo)), cwd=fixture.repo)
            run("git", "add", ".gitignore", cwd=fixture.repo)
            run("git", "commit", "-m", "fixture schema", cwd=fixture.repo)
            plan = root / "p3-plan.json"
            fixture_codex = root / "codex-fixture.py"
            shutil.copyfile(FIXTURES / "codex_fixture.py", fixture_codex)
            os.chmod(fixture_codex, 0o755)
            stages = []
            for identifier in MODULE.LOCAL_STAGE_ORDER:
                output = f"{{run_dir}}/stages/{identifier}/report.json"
                stages.append(
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
                        "stages": stages,
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
                                {"run_id": "p3-full-cycle", "unit_id": "fixture-unit"}
                            ),
                        },
                        "post_commands": [],
                        "validation_commands": [
                            [sys.executable, "-c", "raise SystemExit(0)"]
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            summary = {}
            config = MODULE.RunnerConfig(
                fixture.repo,
                fixture.state,
                fixture_root=root,
                runtime_files=(),
                console_projection=(
                    fixture.repo
                    / "framework/project/interfaces/project-console/data/local-automation-status.js"
                ),
            )

            def local_cycle(transaction):
                summary.update(MODULE.run_p3_fixture_cycle(config, transaction, plan))
                return summary

            result = MODULE.prepare_transaction(
                config,
                run_id="p3-full-cycle",
                local_cycle=local_cycle,
            )
            self.assertEqual(result.status, "completed")
            self.assertEqual(summary["phase"], "P3")
            final = summary["final_commit"]
            self.assertIsNotNone(final["commit"])
            self.assertFalse(summary["publication_attempted"])
            self.assertEqual(
                run("git", "status", "--porcelain", cwd=Path(result.worktree_path)),
                "",
            )
            self.assertEqual(run("git", "status", "--porcelain", cwd=fixture.repo), "")
            status = json.loads((fixture.state / "status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["validation_summary"]["phase"], "P3")
            self.assertIsNone(status["pull_request"])
            self.assertIsNone(status["merge_commit"])
            projection = (
                fixture.repo
                / "framework/project/interfaces/project-console/data/local-automation-status.js"
            )
            self.assertTrue(projection.is_file())
            self.assertIn('"status":"completed"', projection.read_text(encoding="utf-8"))


class RunChainCompletionTests(unittest.TestCase):
    def test_accepted_elim_outcome_is_bound_into_run_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            chain_path = run_dir / "run-chain.json"
            result_path = run_dir / "elim-result.json"
            result_path.write_text(
                json.dumps({"outcome": "completed"}) + "\n",
                encoding="utf-8",
            )
            updated = MODULE.record_elim_outcome_in_run_chain(
                chain_path,
                {
                    "run_id": "arrp-test",
                    "elim_decision": {"launch_recommended": True},
                },
                {"outcome": "completed"},
            )
            self.assertTrue(updated["elim_decision"]["launched"])
            self.assertEqual(updated["elim_decision"]["outcome"], "completed")
            self.assertEqual(
                updated["elim_decision"]["result_sha256"],
                "sha256:" + hashlib.sha256(result_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                json.loads(chain_path.read_text(encoding="utf-8")),
                updated,
            )


if __name__ == "__main__":
    unittest.main()
