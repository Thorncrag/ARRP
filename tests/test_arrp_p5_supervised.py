import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.test_arrp_nightly import GitFixture, MODULE, run


def check_api_sequence(states):
    sequence = iter(states)

    def api(_method, path, _token, *, payload=None):
        if "check-runs" in path:
            state = next(sequence)
            return {
                "check_runs": [
                    {"name": "ARRP Validation", "conclusion": state[0]},
                    {"name": "CodeQL", "conclusion": state[1]},
                ]
            }
        if path.endswith("/status"):
            return {"statuses": []}
        raise AssertionError(path)

    return api


class P5PlanBoundaryTests(unittest.TestCase):
    def test_plan_requires_owner_only_mode_exact_authorization_and_external_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "p5.json"
            path.write_text(
                json.dumps(
                    {
                        "contract_phase": MODULE.P5_SUPERVISED_PHASE,
                        "authorization": MODULE.P5_SUPERVISED_AUTHORIZATION,
                        "stages": [],
                        "queue_command": ["fixture"],
                        "context_command": ["fixture"],
                        "elim": {},
                        "post_commands": [],
                        "validation_commands": [],
                        "publication": {
                            "app_identity_file": "/tmp/app.json",
                            "check_timeout_seconds": 60,
                            "pages_timeout_seconds": 60,
                            "poll_seconds": 0,
                            "pull_request_title": "fixture",
                            "pull_request_body": "fixture",
                            "project_fixture": None,
                        },
                    }
                ),
                encoding="utf-8",
            )
            os.chmod(path, 0o600)
            observed = MODULE.read_p5_supervised_plan(path)
            self.assertEqual(
                observed["contract_phase"],
                MODULE.P5_SUPERVISED_PHASE,
            )
            os.chmod(path, 0o644)
            with self.assertRaisesRegex(MODULE.TransactionError, "owner-only"):
                MODULE.read_p5_supervised_plan(path)

    def test_live_configuration_requires_exact_manual_trigger(self):
        config = MODULE.RunnerConfig(
            Path("/Users/benjaminsmith/Automation Workspaces/ARRP"),
            Path.home() / "Library/Application Support/ARRP",
            trigger="manual",
            supervised_live=True,
        )
        with self.assertRaisesRegex(MODULE.TransactionError, "exact P5"):
            config.validate()

    def test_trusted_codex_auth_home_requires_owner_only_regular_auth_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            auth_home = root / ".codex"
            auth_home.mkdir()
            auth = auth_home / "auth.json"
            auth.write_text("{}\n", encoding="utf-8")
            os.chmod(auth, 0o600)
            with mock.patch.object(MODULE.Path, "home", return_value=root):
                self.assertEqual(
                    MODULE.trusted_codex_auth_home(),
                    auth_home.resolve(),
                )
                os.chmod(auth, 0o644)
                with self.assertRaisesRegex(MODULE.TransactionError, "unsafe"):
                    MODULE.trusted_codex_auth_home()


class P5SealedProcessTests(unittest.TestCase):
    def test_failed_elim_preserves_jsonl_before_returning(self):
        class FailedProcess:
            pid = 1234
            returncode = 1

            def communicate(self, *, input=None, timeout=None):
                self.returncode = 1
                return b'{"type":"fixture.failed"}\n', b"fixture failure"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jsonl = root / "run/elim.jsonl"
            with mock.patch.object(
                MODULE.subprocess,
                "Popen",
                return_value=FailedProcess(),
            ) as launch:
                result = MODULE.run_sealed_elim_process(
                    ["codex", "exec"],
                    worktree=root,
                    environment={},
                    prompt=b"fixture",
                    timeout_seconds=10,
                    jsonl_path=jsonl,
                )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(jsonl.read_bytes(), b'{"type":"fixture.failed"}\n')
            self.assertEqual(jsonl.stat().st_mode & 0o777, 0o600)
            launch.assert_called_once()

    def test_timeout_terminates_process_group_and_preserves_partial_jsonl(self):
        class TimedOutProcess:
            pid = 4321
            returncode = None

            def __init__(self):
                self.calls = 0

            def communicate(self, *, input=None, timeout=None):
                self.calls += 1
                if self.calls == 1:
                    raise MODULE.subprocess.TimeoutExpired(["codex"], timeout)
                self.returncode = -15
                return b'{"type":"fixture.partial"}\n', b""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jsonl = root / "run/elim.jsonl"
            process = TimedOutProcess()
            with (
                mock.patch.object(
                    MODULE.subprocess,
                    "Popen",
                    return_value=process,
                ) as launch,
                mock.patch.object(MODULE.os, "killpg") as kill_group,
            ):
                with self.assertRaisesRegex(MODULE.TransactionError, "timed out"):
                    MODULE.run_sealed_elim_process(
                        ["codex", "exec"],
                        worktree=root,
                        environment={},
                        prompt=b"fixture",
                        timeout_seconds=1,
                        jsonl_path=jsonl,
                    )
            self.assertEqual(jsonl.read_bytes(), b'{"type":"fixture.partial"}\n')
            kill_group.assert_called_once_with(4321, MODULE.signal.SIGTERM)
            launch.assert_called_once()


class P5GitHubWaitTests(unittest.TestCase):
    def test_existing_pull_request_refreshes_metadata_and_retries_stale_head(self):
        expected_head = "a" * 40
        calls = []
        readbacks = iter(
            [
                {
                    "number": 12,
                    "head": {"sha": "b" * 40},
                    "base": {"ref": "main"},
                },
                {
                    "number": 12,
                    "head": {"sha": expected_head},
                    "base": {"ref": "main"},
                },
            ]
        )

        def api(method, path, _token, *, payload=None):
            calls.append((method, path, payload))
            if path.endswith("/git/ref/heads/automation/nightly-fixture"):
                return {"object": {"sha": expected_head}}
            if "/pulls?state=open" in path:
                return [{"number": 12}]
            if method == "PATCH":
                return {"number": 12}
            if path.endswith("/pulls/12"):
                return next(readbacks)
            raise AssertionError((method, path))

        observed = MODULE.open_or_update_nightly_pull_request(
            MODULE.SensitiveValue("fixture"),
            branch="automation/nightly-fixture",
            expected_head=expected_head,
            title="Updated fixture",
            body="Updated fixture body",
            api_request=api,
            readback_timeout_seconds=1,
            readback_poll_seconds=0,
            monotonic=lambda: 0,
            sleeper=lambda _seconds: None,
        )
        self.assertEqual(observed["head"]["sha"], expected_head)
        self.assertIn(
            (
                "PATCH",
                f"/repos/{MODULE.GITHUB_REPOSITORY}/pulls/12",
                {"title": "Updated fixture", "body": "Updated fixture body"},
            ),
            calls,
        )

    def test_pull_request_stale_head_fails_after_bounded_readback(self):
        expected_head = "a" * 40
        clock = iter([0.0, 1.0])

        def api(method, path, _token, *, payload=None):
            if path.endswith("/git/ref/heads/automation/nightly-fixture"):
                return {"object": {"sha": expected_head}}
            if "/pulls?state=open" in path:
                return []
            if method == "POST":
                return {"number": 12}
            if path.endswith("/pulls/12"):
                return {
                    "number": 12,
                    "head": {"sha": "b" * 40},
                    "base": {"ref": "main"},
                }
            raise AssertionError((method, path))

        with self.assertRaisesRegex(MODULE.GitHubBrokerError, "head/base"):
            MODULE.open_or_update_nightly_pull_request(
                MODULE.SensitiveValue("fixture"),
                branch="automation/nightly-fixture",
                expected_head=expected_head,
                title="Fixture",
                body="Fixture",
                api_request=api,
                readback_timeout_seconds=0.5,
                readback_poll_seconds=0,
                monotonic=lambda: next(clock),
                sleeper=lambda _seconds: None,
            )

    def test_required_checks_wait_for_both_exact_checks(self):
        times = iter([0.0, 0.0, 1.0])
        observed = MODULE.wait_for_required_checks(
            MODULE.SensitiveValue("fixture"),
            head_sha="a" * 40,
            timeout_seconds=10,
            poll_seconds=0,
            api_request=check_api_sequence(
                [("success", None), ("success", "success")]
            ),
            monotonic=lambda: next(times),
            sleeper=lambda _seconds: None,
        )
        self.assertEqual(observed["ARRP Validation"], "success")
        self.assertEqual(observed["CodeQL"], "success")

    def test_required_check_failure_stops_immediately(self):
        with self.assertRaisesRegex(MODULE.GitHubBrokerError, "checks failed"):
            MODULE.wait_for_required_checks(
                MODULE.SensitiveValue("fixture"),
                head_sha="a" * 40,
                timeout_seconds=10,
                poll_seconds=0,
                api_request=check_api_sequence([("success", "failure")]),
                monotonic=lambda: 0.0,
                sleeper=lambda _seconds: None,
            )

    def test_pages_readback_requires_exact_sha_and_success(self):
        calls = []

        def api(_method, path, _token, *, payload=None):
            calls.append(path)
            return {
                "workflow_runs": [
                    {
                        "id": 9,
                        "head_sha": "b" * 40,
                        "status": "completed",
                        "conclusion": "success",
                    },
                    {
                        "id": 10,
                        "head_sha": "a" * 40,
                        "status": "completed",
                        "conclusion": "success",
                        "html_url": "https://example.invalid/run/10",
                    },
                ]
            }

        observed = MODULE.wait_for_pages_deployment(
            MODULE.SensitiveValue("fixture"),
            merge_sha="a" * 40,
            timeout_seconds=10,
            poll_seconds=0,
            api_request=api,
            monotonic=lambda: 0.0,
            sleeper=lambda _seconds: None,
        )
        self.assertEqual(observed["head_sha"], "a" * 40)
        self.assertEqual(observed["conclusion"], "success")
        self.assertIn("head_sha=" + "a" * 40, calls[0])


class P5ProjectFixtureTests(unittest.TestCase):
    def test_project_text_fixture_changes_reads_and_restores(self):
        state = {"value": None}
        writes = []
        fixture = {
            "project_id": "project",
            "item_id": "item",
            "field_id": "field",
            "expected_old_value": None,
            "fixture_value": "p5 reversible fixture",
        }

        def read_field(_fixture, _token):
            return state["value"]

        def write_field(_fixture, value, _token):
            writes.append(value)
            state["value"] = value

        observed = MODULE.run_reversible_project_text_fixture(
            fixture,
            MODULE.SensitiveValue("fixture"),
            read_field=read_field,
            write_field=write_field,
        )
        self.assertEqual(writes, ["p5 reversible fixture", None])
        self.assertTrue(observed["restored"])
        self.assertIsNone(state["value"])


class P5PublicationManifestTests(unittest.TestCase):
    def test_complete_commit_range_includes_checkpoint_ancestry(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = GitFixture(Path(directory))
            base = run("git", "rev-parse", "HEAD", cwd=fixture.repo)
            issue = fixture.repo / "areas/TEST/issues/TEST-001.md"
            issue.write_text("checkpoint fixture\n", encoding="utf-8")
            run("git", "add", "areas/TEST/issues/TEST-001.md", cwd=fixture.repo)
            run("git", "commit", "-m", "checkpoint", cwd=fixture.repo)
            record = fixture.repo / "research/p5-proof.txt"
            record.parent.mkdir(exist_ok=True)
            record.write_text("final fixture\n", encoding="utf-8")
            run("git", "add", "research/p5-proof.txt", cwd=fixture.repo)
            run("git", "commit", "-m", "final", cwd=fixture.repo)
            head = run("git", "rev-parse", "HEAD", cwd=fixture.repo)
            run_dir = fixture.state / "runs/p5-manifest"
            result = MODULE.classify_publication_range(
                fixture.repo,
                run_dir,
                base_commit=base,
                head_commit=head,
            )
            self.assertEqual(
                result["classification"]["ordinary"],
                [
                    "areas/TEST/issues/TEST-001.md",
                    "research/p5-proof.txt",
                ],
            )
            self.assertFalse(result["review_required"])

    def test_successful_worktree_cleanup_is_bounded_and_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = GitFixture(Path(directory))
            worktree = fixture.state / "worktrees/p5-cleanup"
            worktree.parent.mkdir(parents=True)
            run(
                "git",
                "worktree",
                "add",
                str(worktree),
                "-b",
                "p5-cleanup",
                cwd=fixture.repo,
            )
            MODULE.remove_successful_transaction_worktree(
                fixture.repo,
                fixture.state,
                worktree,
            )
            self.assertFalse(worktree.exists())
            with self.assertRaisesRegex(MODULE.TransactionError, "outside state root"):
                MODULE.remove_successful_transaction_worktree(
                    fixture.repo,
                    fixture.state,
                    fixture.repo,
                )


class P5CoordinatorIntegrationTests(unittest.TestCase):
    def test_dynamic_governing_change_stops_before_worktree_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = GitFixture(Path(directory))
            registry = (
                fixture.repo
                / "framework/project/automation/context-routes.json"
            )
            registry.parent.mkdir(parents=True)
            registry.write_text(
                json.dumps(
                    {
                        "documents": {
                            "fixture_governing": {
                                "path": "areas/TEST/issues/TEST-001.md",
                                "governing": True,
                            }
                        }
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            run("git", "add", str(registry.relative_to(fixture.repo)), cwd=fixture.repo)
            run("git", "commit", "-m", "add governing fixture", cwd=fixture.repo)
            issue = fixture.repo / "areas/TEST/issues/TEST-001.md"
            issue.write_text("protected governing change\n", encoding="utf-8")
            local_cycle = mock.Mock()

            result = MODULE.prepare_transaction(
                fixture.config(),
                run_id="p5-dynamic-governing",
                local_cycle=local_cycle,
            )

            self.assertEqual(result.status, "review-required")
            self.assertEqual(
                result.protected_paths,
                ("areas/TEST/issues/TEST-001.md",),
            )
            self.assertIsNone(result.worktree_path)
            local_cycle.assert_not_called()

    def test_supervised_publication_joins_all_required_success_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            worktree = root / "state/worktrees/p5-live"
            worktree.mkdir(parents=True)
            config = MODULE.RunnerConfig(
                root / "repo",
                root / "state",
                trigger="manual-p5-supervised",
                supervised_live=True,
            )
            transaction = MODULE.TransactionResult(
                "p5-live",
                "completed",
                "automation/nightly-p5-live",
                None,
                str(worktree),
                "b" * 40,
            )
            publication = {
                "app_identity_file": str(root / "app.json"),
                "check_timeout_seconds": 60,
                "pages_timeout_seconds": 60,
                "poll_seconds": 0,
                "pull_request_title": "P5",
                "pull_request_body": "P5",
                "project_fixture": None,
            }
            token = MODULE.SensitiveValue("fixture")
            identity = MODULE.GitHubAppIdentity(1, 2, 3)

            def git_text(_repository, *args):
                if args == ("rev-parse", "HEAD"):
                    return "a" * 40
                if args == ("rev-parse", "origin/main"):
                    return "c" * 40
                raise AssertionError(args)

            with (
                mock.patch.object(MODULE, "git_text", side_effect=git_text),
                mock.patch.object(
                    MODULE,
                    "classify_publication_range",
                    return_value={
                        "classification": {
                            "ordinary": ["research/p5.txt"],
                            "protected": [],
                            "prohibited": [],
                        },
                        "review_required": False,
                    },
                ),
                mock.patch.object(
                    MODULE.GitHubAppIdentity,
                    "from_json",
                    return_value=identity,
                ),
                mock.patch.object(
                    MODULE,
                    "read_keychain_secret",
                    return_value=token,
                ),
                mock.patch.object(
                    MODULE,
                    "mint_installation_token",
                    return_value=token,
                ),
                mock.patch.object(MODULE, "git_push_with_token") as push,
                mock.patch.object(
                    MODULE,
                    "open_or_update_nightly_pull_request",
                    return_value={
                        "number": 12,
                        "html_url": "https://example.invalid/12",
                    },
                ),
                mock.patch.object(
                    MODULE,
                    "wait_for_required_checks",
                    return_value={"ARRP Validation": "success", "CodeQL": "success"},
                ),
                mock.patch.object(
                    MODULE,
                    "merge_exact_head",
                    return_value="c" * 40,
                ),
                mock.patch.object(
                    MODULE,
                    "wait_for_pages_deployment",
                    return_value={"id": 22, "conclusion": "success"},
                ),
                mock.patch.object(MODULE, "git") as git_command,
                mock.patch.object(
                    MODULE,
                    "fast_forward_main",
                    return_value="c" * 40,
                ) as fast_forward,
                mock.patch.object(
                    MODULE,
                    "remove_successful_transaction_worktree",
                ) as cleanup,
            ):
                observed = MODULE.publish_supervised_transaction(
                    config,
                    transaction,
                    {"phase": "P5"},
                    publication,
                )
            push.assert_called_once()
            canonical = config.canonical_path.resolve()
            git_command.assert_called_once_with(canonical, "fetch", "origin", "main")
            fast_forward.assert_called_once_with(canonical, "c" * 40)
            cleanup.assert_called_once_with(canonical, config.state_root, worktree.resolve())
            self.assertEqual(observed["merge_commit"], "c" * 40)
            self.assertTrue(observed["worktree_removed"])

    def test_publication_callback_runs_under_lock_and_updates_terminal_status(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = GitFixture(Path(directory))
            config = fixture.config()
            publication = {}

            def local_cycle(transaction):
                worktree = Path(transaction.worktree_path)
                record = worktree / "research/p5-proof.txt"
                record.parent.mkdir(exist_ok=True)
                record.write_text("fixture\n", encoding="utf-8")
                final = MODULE.create_local_final_commit(
                    worktree,
                    fixture.state / "runs/p5-callback",
                    message="p5 fixture",
                )
                return {"phase": "P5", "final_commit": final}

            def publication_cycle(transaction, _summary):
                publication["called"] = True
                return {
                    "pull_request": {"number": 1, "url": "https://example.invalid/1"},
                    "expected_pr_head": "a" * 40,
                    "merge_commit": "b" * 40,
                    "project_sync": {"restored": True},
                    "pages_workflow_run": {"id": 1},
                    "pages_conclusion": "success",
                }

            result = MODULE.prepare_transaction(
                config,
                run_id="p5-callback",
                local_cycle=local_cycle,
                publication_cycle=publication_cycle,
            )
            self.assertEqual(result.status, "completed")
            self.assertTrue(publication["called"])
            status = json.loads(
                (fixture.state / "status.json").read_text(encoding="utf-8")
            )
            self.assertEqual(status["stage"], "20_finish")
            self.assertEqual(status["merge_commit"], "b" * 40)
            self.assertEqual(status["pages_conclusion"], "success")

    def test_network_failure_writes_independent_terminal_status_and_preserves(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = GitFixture(Path(directory))
            config = fixture.config()

            def local_cycle(_transaction):
                return {"phase": "P5"}

            def publication_cycle(_transaction, _summary):
                raise MODULE.GitHubBrokerError("fixture network unavailable")

            with self.assertRaisesRegex(
                MODULE.GitHubBrokerError,
                "network unavailable",
            ):
                MODULE.prepare_transaction(
                    config,
                    run_id="p5-network-failure",
                    local_cycle=local_cycle,
                    publication_cycle=publication_cycle,
                )
            status = json.loads(
                (fixture.state / "status.json").read_text(encoding="utf-8")
            )
            self.assertEqual(status["status"], "failed")
            self.assertEqual(status["failure_class"], "GitHubBrokerError")
            self.assertEqual(len(status["preserved_paths"]), 2)

    def test_missed_slot_claim_is_idempotent_and_cannot_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            self.assertTrue(
                MODULE.claim_scheduled_slot(state, "2026-07-27T04:17:00-04:00")
            )
            self.assertFalse(
                MODULE.claim_scheduled_slot(state, "2026-07-27T08:17:00Z")
            )
            self.assertTrue(
                MODULE.claim_scheduled_slot(state, "2026-07-28T08:17:00Z")
            )


if __name__ == "__main__":
    unittest.main()
