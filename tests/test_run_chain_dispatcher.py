import importlib.util
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_chain_dispatcher", ROOT / "scripts" / "run_chain_dispatcher.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class RunChainDispatcherTests(unittest.TestCase):
    def test_managed_usage_baseline_is_fixed_and_path_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            baseline = MODULE.managed_usage_baseline_path(
                repo,
                "arrp-20260725T063006Z-20260725T080739Z",
            )

            self.assertEqual(
                baseline.parent,
                repo.resolve() / MODULE.USAGE_BASELINE_DIRECTORY,
            )
            self.assertRegex(baseline.name, r"^[0-9a-f]{64}\.json$")
            with self.assertRaisesRegex(MODULE.ContextError, "unsafe invocation ID"):
                MODULE.managed_usage_baseline_path(repo, "../outside")

    def write_current_audit(
        self,
        repo: Path,
        *,
        state: str,
        next_step: str = "None.",
        blocker: str = "None.",
    ) -> None:
        inactive = state == "Inactive"
        values = {
            "Handoff state": state,
            "Active issue/task": "None." if inactive else "TEST-001",
            "Audit type/tier": "None." if inactive else "Change Audit",
            "Started": "None." if inactive else "2026-07-24 12:00:00 -0400",
            "Last checkpoint": "2026-07-24 12:30:00 -0400",
            "User request": "None." if inactive else "Complete the selected unit.",
            "Scope": "None." if inactive else "TEST-001 records.",
            "Files touched": "None." if inactive else "areas/TEST/issues/TEST-001.md",
            "Completed steps": "None." if inactive else "Preserved partial work.",
            "Next step": "None." if inactive else next_step,
            "Blockers/questions": "None." if inactive else blocker,
            "Validation status": "Not applicable." if inactive else "In progress.",
        }
        path = repo / "framework/logs/CURRENT_AUDIT.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = "\n".join(f"| {name} | {value} |" for name, value in values.items())
        path.write_text(
            "# Current Audit Handoff\n\n"
            "## Current Task\n\n"
            "| Field | Entry |\n"
            "| --- | --- |\n"
            f"{rows}\n\n"
            "## Handoff Rules\n",
            encoding="utf-8",
        )

    def elim_result(
        self,
        *,
        outcome: str = "completed",
        continuation_state: str = "complete",
        next_action=None,
        human_questions=None,
    ):
        return {
            "schema_version": 1,
            "run_id": "chain-1",
            "unit_id": "unit-1",
            "work_type": "issue_development",
            "outcome": outcome,
            "authority": {
                "classification": "delegated_judgment",
                "basis": "runbook",
            },
            "issue_id": "TEST-001",
            "canonical_record": "areas/TEST/issues/TEST-001.md",
            "files_touched": ["framework/logs/ELIM_RUN_LOG.md"],
            "source_ids": [],
            "validation": [],
            "commit": "a" * 40,
            "synchronization": ["Synchronized and read back origin/main."],
            "human_questions": human_questions or [],
            "continuation": {
                "state": continuation_state,
                "next_action": next_action,
            },
        }

    def selected_manifest(self, *, kind="issue_development", issue_id="TEST-001"):
        canonical_record = (
            f"areas/TEST/issues/{issue_id}.md" if issue_id else None
        )
        return {
            "chain_id": "chain-1",
            "baseline_commit": "b" * 40,
            "work_queue": {
                "selected_work_item_id": "unit-1",
                "next_item": {
                    "id": "unit-1",
                    "kind": kind,
                    "source": {
                        "identifier": issue_id,
                        "canonicalRecord": canonical_record,
                    },
                },
            },
            "context_packet": {
                "work_item_id": "unit-1",
                "issue_id": issue_id,
                "canonical_record": canonical_record,
            },
        }

    def write_elim_run_log(
        self,
        repo: Path,
        *,
        run_id: str = "chain-1",
        unit_id: str = "unit-1",
        material: bool = False,
        outcome: str = "Completed",
    ) -> None:
        logs = repo / "framework/logs"
        logs.mkdir(parents=True, exist_ok=True)
        (logs / "ELIM_RUN_LOG.md").write_text(
            "# Elim Run Log\n\n"
            "## Runs\n\n"
            f"### 2026-07-24 — {run_id} — Completed\n\n"
            "| Field | Entry |\n"
            "| --- | --- |\n"
            "| Started | 2026-07-24 12:00:00 -0400 |\n"
            "| Ended | 2026-07-24 12:05:00 -0400 |\n"
            f"| Run ID | `{run_id}` |\n"
            "| Trigger | Scheduled automation |\n"
            f"| Outcome | {outcome} |\n"
            "| Usage | 90 percent remaining; 1 percentage point consumed. |\n"
            "| Work summary | Completed the selected bounded unit. |\n"
            + (
                "| Material units | [Shared entry](AGENT_AUDIT_LOG.md#entry) |\n"
                if material
                else "| Material units | None. |\n"
            )
            + "| Issue audit records | None. |\n"
            "| Commits and synchronization | Committed and synchronized. |\n"
            "| Validation | Focused checks passed. |\n"
            "| Human review | None. |\n"
            "| Stop reason | Normal completion. |\n"
            "| Exact next action | None. |\n",
            encoding="utf-8",
        )
        if material:
            (logs / "AGENT_AUDIT_LOG.md").write_text(
                "# Agent Audit Log\n\n"
                "## Entries\n\n"
                "### 2026-07-24 — Entry\n\n"
                "| Field | Entry |\n"
                "| --- | --- |\n"
                f"| Run ID | {run_id} |\n"
                f"| Unit ID | {unit_id} |\n",
                encoding="utf-8",
            )

    def test_prompt_preserves_elim_identity_and_comprehensive_mode(self):
        payload = {
            "chain_id": "chain-1",
            "elim_decision": {
                "profile": {
                    "full_context": True,
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "xhigh",
                }
            },
            "usage": {
                "host_monitor": {
                    "status_path": ".tmp/run-coordinator/chain-1/usage-status.json",
                    "snapshot_max_age_seconds": 120,
                }
            },
            "context_packet": {
                "local_path": ".tmp/run-coordinator/chain-1/elim-context.json",
                "work_item_id": "unit-1",
                "issue_id": None,
                "canonical_record": None,
            },
            "work_queue": {
                "selected_work_item_id": "unit-1",
                "next_item": {
                    "id": "unit-1",
                    "kind": "comprehensive_review",
                    "source": {},
                },
            },
        }
        execution = Path("/tmp/elim-checkout")
        prompt = MODULE.elim_prompt(
            execution / ".tmp/run-coordinator/chain-1/run-chain.json",
            payload,
        )
        self.assertIn("You are Elim", prompt)
        self.assertIn("comprehensive full-context review", prompt)
        self.assertIn("15 percent hard", prompt)
        self.assertIn("approved host dispatcher", prompt)
        self.assertIn("Do not launch a second Codex app-server", prompt)
        self.assertIn("usage-status.json", prompt)
        self.assertIn(
            "--context-packet .tmp/run-coordinator/chain-1/elim-context.json",
            prompt,
        )
        self.assertIn("represents exactly the one manifest-selected unit", prompt)
        self.assertIn("stop_requested", prompt)
        self.assertIn("trusted host dispatcher", prompt)
        self.assertIn("Do not run repository Git mutations", prompt)
        self.assertIn("Authorized GitHub Issue, Project", prompt)
        self.assertIn("Leave commit null", prompt)

    def test_prompt_confines_bot_failure_to_repair_only(self):
        payload = {
            "chain_id": "chain-1",
            "elim_decision": {
                "profile": {
                    "full_context": False,
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "high",
                }
            },
            "usage": {"host_monitor": {}},
            "context_packet": {
                "local_path": ".tmp/run-coordinator/chain-1/context.json",
                "issue_id": None,
                "canonical_record": None,
            },
            "work_queue": {
                "selected_work_item_id": "repair-source",
                "next_item": {
                    "id": "repair-source",
                    "kind": "bot_failure",
                    "safety_class": 0,
                    "source": {},
                },
            },
        }
        prompt = MODULE.elim_prompt(
            Path("/tmp/elim-checkout/run-chain.json"),
            payload,
        )
        self.assertIn("Process only the selected safety-class-0", prompt)
        self.assertIn("Review Epoch remains due", prompt)

    def test_config_uses_explicit_host_paths_and_conservative_profiles(self):
        config = json.loads(
            (ROOT / ".github" / "run-coordinator-bot.json").read_text()
        )
        for key in ("pythonPath", "gitPath", "githubCliPath", "codexPath"):
            self.assertTrue(Path(config["hostDispatcher"][key]).is_absolute())
        profiles = config["llmRouting"]["profiles"]
        self.assertEqual(profiles["read-heavy-triage"]["model"], "gpt-5.6-terra")
        self.assertEqual(profiles["substantive"]["model"], "gpt-5.6-sol")
        self.assertTrue(profiles["comprehensive"]["fullContext"])
        self.assertEqual(config["usage"]["monitorIntervalSeconds"], 60)
        self.assertEqual(config["usage"]["snapshotMaxAgeSeconds"], 120)
        self.assertEqual(config["hostDispatcher"]["staleLockSeconds"], 900)
        self.assertEqual(
            config["hostDispatcher"]["isolatedCheckoutPath"],
            ".tmp/run-coordinator/elim-checkout",
        )
        self.assertEqual(
            config["hostDispatcher"]["repositoryCloseout"],
            MODULE.HOST_CLOSEOUT_POLICY,
        )

    def test_host_closeout_policy_rejects_runtime_drift(self):
        config = {
            "hostDispatcher": {
                "repositoryCloseout": dict(MODULE.HOST_CLOSEOUT_POLICY),
            }
        }
        MODULE.validate_host_closeout_policy(config)
        config["hostDispatcher"]["repositoryCloseout"]["modelGitMutation"] = (
            "allowed"
        )
        with self.assertRaisesRegex(RuntimeError, "trusted-host boundary"):
            MODULE.validate_host_closeout_policy(config)

    def test_dispatcher_uses_only_the_reviewed_config_path(self):
        source = (ROOT / "scripts" / "run_chain_dispatcher.py").read_text()
        self.assertNotIn('parser.add_argument("--config"', source)
        self.assertIn("config = read_json(CONFIG)", source)
        self.assertIn('"--recover-stale-lock-only"', source)
        self.assertIn("do not fetch, synchronize, trigger a chain", source)
        self.assertIn("record_bootstrap_failure_best_effort(", source)

    def test_bootstrap_failure_projects_action_item_when_host_lock_is_free(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            completed = MODULE.subprocess.CompletedProcess(
                [MODULE.EXECUTABLES["notificationPath"]],
                0,
                stdout="",
                stderr="",
            )
            with (
                mock.patch.object(
                    MODULE,
                    "executable",
                    return_value=MODULE.EXECUTABLES["notificationPath"],
                ),
                mock.patch.object(MODULE, "command", return_value=completed),
            ):
                event = MODULE.record_bootstrap_failure_best_effort(
                    repo,
                    stage="dispatcher-executables",
                    message="Reviewed executable is unavailable.",
                )
            self.assertTrue(event["shared_projection"])
            control = json.loads(
                (
                    repo / ".tmp/run-coordinator/control.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                control["action_items"][-1]["stage"],
                "dispatcher-executables",
            )
            self.assertTrue(
                list(
                    (
                        repo
                        / ".tmp/run-coordinator/bootstrap-failures"
                    ).glob("*.json")
                )
            )

    def test_bootstrap_failure_does_not_race_an_active_host_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            state = repo / ".tmp/run-coordinator"
            state.mkdir(parents=True)
            lock = state / "host-dispatch.lock"
            descriptor = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
            MODULE.fcntl.flock(
                descriptor,
                MODULE.fcntl.LOCK_EX | MODULE.fcntl.LOCK_NB,
            )
            completed = MODULE.subprocess.CompletedProcess(
                [MODULE.EXECUTABLES["notificationPath"]],
                0,
                stdout="",
                stderr="",
            )
            try:
                with (
                    mock.patch.object(
                        MODULE,
                        "executable",
                        return_value=MODULE.EXECUTABLES["notificationPath"],
                    ),
                    mock.patch.object(MODULE, "command", return_value=completed),
                ):
                    event = MODULE.record_bootstrap_failure_best_effort(
                        repo,
                        stage="dispatcher-lock",
                        message="Another dispatcher owns the lock.",
                    )
            finally:
                MODULE.fcntl.flock(descriptor, MODULE.fcntl.LOCK_UN)
                os.close(descriptor)
            self.assertFalse(event["shared_projection"])
            self.assertIn("shared_projection_error", event)
            self.assertFalse((state / "control.json").exists())
            self.assertTrue(list((state / "bootstrap-failures").glob("*.json")))

    def test_bootstrap_failure_event_retention_keeps_newest_128(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            events = repo / ".tmp/run-coordinator/bootstrap-failures"
            events.mkdir(parents=True)
            for index in range(130):
                (events / f"20260724T12{index:010d}Z-1.json").write_text(
                    "{}\n",
                    encoding="utf-8",
                )
            unexpected = events / "keep-me.txt"
            unexpected.write_text("not a managed event\n", encoding="utf-8")
            MODULE.prune_bootstrap_failure_events(repo, events)
            retained = sorted(events.glob("*.json"))
            self.assertEqual(
                len(retained),
                MODULE.MAX_BOOTSTRAP_FAILURE_EVENTS,
            )
            self.assertEqual(
                retained[0].name,
                "20260724T120000000002Z-1.json",
            )
            self.assertTrue(unexpected.is_file())

    def test_coordinator_reads_fresh_queue_inputs_through_github_api(self):
        workflow = (
            ROOT / ".github" / "workflows" / "run-coordinator-bot.yml"
        ).read_text()
        self.assertIn(
            "https://api.github.com/repos/Thorncrag/ARRP/contents/${name}.json"
            "?ref=project-console-data",
            workflow,
        )
        self.assertIn("application/vnd.github.raw+json", workflow)

    def test_elim_result_schema_is_strict_structured_output_compatible(self):
        schema = json.loads(
            (
                ROOT
                / "framework"
                / "agents"
                / "elim-work-unit-result.schema.json"
            ).read_text()
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), set(schema["properties"]))
        self.assertIn(
            "candidate_research",
            schema["properties"]["work_type"]["enum"],
        )
        self.assertIn("canonical_record", schema["required"])
        self.assertNotIn("uniqueItems", json.dumps(schema))
        self.assertEqual(schema["properties"]["schema_version"]["type"], "integer")
        for name in ("work_type", "outcome"):
            self.assertEqual(schema["properties"][name]["type"], "string")
        self.assertEqual(
            schema["properties"]["authority"]["properties"]["classification"]["type"],
            "string",
        )
        self.assertEqual(
            schema["properties"]["validation"]["items"]["properties"]["status"]["type"],
            "string",
        )
        self.assertEqual(
            set(schema["properties"]["validation"]["items"]["required"]),
            set(schema["properties"]["validation"]["items"]["properties"]),
        )
        self.assertEqual(
            schema["properties"]["continuation"]["properties"]["state"]["type"],
            "string",
        )

    def test_contained_path_rejects_parent_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            outside = Path(directory) / "outside"
            root.mkdir()
            outside.mkdir()
            (root / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(MODULE.ContextError):
                MODULE.contained_path(root / ".." / "outside", root)
            with self.assertRaises(MODULE.ContextError):
                MODULE.contained_path(root / "link" / "payload.json", root)

    def test_comprehensive_epoch_proof_and_alerts_are_deduplicated(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            ledger = repo / "research" / "review-epochs.jsonl"
            ledger.parent.mkdir()
            packet = repo / "elim-context.json"
            packet.write_text("{}\n", encoding="utf-8")
            ledger.write_text(
                json.dumps({"triggering_run_id": "chain-1"}) + "\n",
                encoding="utf-8",
            )
            self.assertFalse(
                MODULE.comprehensive_epoch_recorded(repo, "chain-1", packet)
            )
            record = {
                "schema_version": 1,
                "triggering_run_id": "chain-1",
                "epoch_id": "epoch-chain-1",
            }
            digest = hashlib.sha256(
                json.dumps(
                    record,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            ).hexdigest()
            ledger.write_text(
                json.dumps(
                    {**record, "record_sha256": "sha256:" + digest},
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            with (
                mock.patch.object(
                    MODULE,
                    "validate_review_epoch",
                    return_value=record,
                ) as validate,
                mock.patch.object(
                    MODULE,
                    "validate_finding_continuity",
                    return_value=record,
                ) as continuity,
            ):
                self.assertTrue(
                    MODULE.comprehensive_epoch_recorded(repo, "chain-1", packet)
                )
                validate.assert_called_once()
                continuity.assert_called_once()
            tampered = json.loads(ledger.read_text(encoding="utf-8"))
            tampered["epoch_id"] = "altered"
            ledger.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
            self.assertFalse(
                MODULE.comprehensive_epoch_recorded(repo, "chain-1", packet)
            )
            config = json.loads(
                (ROOT / ".github" / "run-coordinator-bot.json").read_text()
            )
            control = {}
            manifest = {
                "chain_id": "chain-1",
                "updated_at": "2026-07-24T12:00:00+00:00",
                "status": "blocked",
                "failures": [
                    {
                        "stage": "project-integrity-bot",
                        "message": "failed",
                    }
                ],
            }
            with mock.patch.object(MODULE, "command"):
                self.assertTrue(MODULE.alert_failures(config, control, manifest, repo))
                self.assertFalse(MODULE.alert_failures(config, control, manifest, repo))
            self.assertEqual(len(control["action_items"]), 1)
            healthy = {
                "chain_id": "chain-2",
                "updated_at": "2026-07-24T13:00:00+00:00",
                "status": "complete",
                "failures": [],
                "work_queue": {"problems": []},
            }
            self.assertFalse(MODULE.alert_failures(config, control, healthy, repo))
            self.assertEqual(len(control["action_items"]), 1)
            self.assertFalse(control["action_items"][0]["resolved"])
            self.assertFalse(MODULE.alert_failures(config, control, healthy, repo))

    def test_thread_id_is_recovered_for_later_elim_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            events = Path(directory) / "elim.jsonl"
            events.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "turn.started"}),
                        json.dumps(
                            {
                                "type": "thread.started",
                                "thread_id": "019f9999-1234-7000-8000-123456789abc",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                MODULE.thread_id_from_jsonl(events),
                "019f9999-1234-7000-8000-123456789abc",
            )

    def test_runtime_preflight_allows_feature_branch_and_unrelated_dirty_files(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            for relative in MODULE.AUTOMATION_RUNTIME_PATHS:
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative + "\n", encoding="utf-8")
            same_blob = "b" * 40 + "\n"
            responses = [
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout="https://github.com/Thorncrag/ARRP.git\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout="a" * 40 + "\n", stderr=""
                ),
            ]
            for _relative in MODULE.AUTOMATION_RUNTIME_PATHS:
                responses.extend(
                    [
                        MODULE.subprocess.CompletedProcess(
                            [], 0, stdout=same_blob, stderr=""
                        ),
                        MODULE.subprocess.CompletedProcess(
                            [], 0, stdout=same_blob, stderr=""
                        ),
                    ]
                )
            with mock.patch.object(
                MODULE,
                "command",
                side_effect=responses,
            ) as invoked:
                revision = MODULE.verify_canonical_runtime_boundary(
                    "/usr/bin/git",
                    repo,
                )
            self.assertEqual(revision, "a" * 40)
            argument_vectors = [call.args[0] for call in invoked.mock_calls]
            self.assertFalse(
                any(
                    vector[1:3] in (["status", "--porcelain"], ["branch", "--show-current"])
                    for vector in argument_vectors
                )
            )
            self.assertFalse(any("merge" in vector for vector in argument_vectors))

    def test_runtime_preflight_blocks_automation_file_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            for relative in MODULE.AUTOMATION_RUNTIME_PATHS:
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative + "\n", encoding="utf-8")
            responses = [
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout="https://github.com/Thorncrag/ARRP.git\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout="a" * 40 + "\n", stderr=""
                ),
            ]
            for index, _relative in enumerate(MODULE.AUTOMATION_RUNTIME_PATHS):
                responses.extend(
                    [
                        MODULE.subprocess.CompletedProcess(
                            [], 0, stdout=("c" if index == 0 else "b") * 40 + "\n", stderr=""
                        ),
                        MODULE.subprocess.CompletedProcess(
                            [], 0, stdout="b" * 40 + "\n", stderr=""
                        ),
                    ]
                )
            with mock.patch.object(MODULE, "command", side_effect=responses):
                with self.assertRaisesRegex(RuntimeError, "runtime differs"):
                    MODULE.verify_canonical_runtime_boundary("/usr/bin/git", repo)

    def test_manifest_must_match_origin_main_before_launch(self):
        with mock.patch.object(
            MODULE,
            "command",
            return_value=MODULE.subprocess.CompletedProcess(
                [],
                0,
                stdout="a" * 40 + "\n",
                stderr="",
            ),
        ):
            self.assertTrue(
                MODULE.manifest_matches_current_repo(
                    "/usr/bin/git",
                    Path("/tmp/repo"),
                    {"final_revision": "a" * 40},
                )
            )
            self.assertFalse(
                MODULE.manifest_matches_current_repo(
                    "/usr/bin/git",
                    Path("/tmp/repo"),
                    {"final_revision": "b" * 40},
                )
            )
        with self.assertRaisesRegex(RuntimeError, "valid final revision"):
            MODULE.manifest_matches_current_repo(
                "/usr/bin/git",
                Path("/tmp/repo"),
                {"final_revision": "main"},
            )

    def test_host_usage_attestation_is_chain_bound_and_repo_relative(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            baseline = repo / ".tmp/run-coordinator/usage-chain-1.json"
            baseline.parent.mkdir(parents=True)
            baseline.write_text("{}\n", encoding="utf-8")
            status = repo / ".tmp/run-coordinator/chain-1/usage-status.json"
            config = {
                "usage": {
                    "hardReservePercent": 15,
                    "softRunTargetPercent": 10,
                    "monitorIntervalSeconds": 60,
                    "snapshotMaxAgeSeconds": 120,
                }
            }
            value = MODULE.write_usage_attestation(
                status,
                repo=repo,
                chain_id="chain-1",
                invocation_id="chain-1-invocation",
                baseline_path=baseline,
                gate={
                    "status": "pass",
                    "checkedAtUtc": "2026-07-24T15:00:00+00:00",
                    "lowestRemainingPercent": 99,
                },
                config=config,
            )
            self.assertEqual(value["source"], "approved-host-dispatcher")
            self.assertEqual(value["chain_id"], "chain-1")
            self.assertFalse(Path(value["baseline_path"]).is_absolute())
            self.assertEqual(json.loads(status.read_text()), value)

    def test_completed_elim_closeout_requires_inactive_cleared_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_current_audit(repo, state="Inactive")
            complete, detail = MODULE.verify_elim_closeout(
                repo,
                self.elim_result(),
            )
            self.assertTrue(complete)
            self.assertIn("verified", detail)

            failed_validation = self.elim_result()
            failed_validation["validation"] = [
                {
                    "check": "repository consistency",
                    "status": "failed",
                    "detail": "mismatch",
                }
            ]
            with self.assertRaisesRegex(MODULE.ContextError, "failed validation"):
                MODULE.verify_elim_closeout(repo, failed_validation)

            self.write_current_audit(
                repo,
                state="Open",
                next_step="Finish synchronization.",
            )
            with self.assertRaisesRegex(MODULE.ContextError, "state Inactive"):
                MODULE.verify_elim_closeout(repo, self.elim_result())

    def test_fully_routed_human_review_closes_inactive(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_current_audit(repo, state="Inactive")
            complete, _ = MODULE.verify_elim_closeout(
                repo,
                self.elim_result(
                    outcome="human_review",
                    continuation_state="human_required",
                    next_action="Human answers the recorded question in Action Items.",
                    human_questions=["Would the same rule be acceptable under reversed control?"],
                ),
            )
            self.assertTrue(complete)

    def test_retryable_closeout_requires_paused_or_blocked_exact_continuation(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            next_action = "Resume from source SRC-0001."
            self.write_current_audit(
                repo,
                state="Paused",
                next_step=next_action,
                blocker="Usage reserve required safe closeout.",
            )
            complete, detail = MODULE.verify_elim_closeout(
                repo,
                self.elim_result(
                    outcome="usage_stopped",
                    continuation_state="retryable",
                    next_action=next_action,
                ),
            )
            self.assertFalse(complete)
            self.assertIn("continuation is preserved", detail)

            self.write_current_audit(
                repo,
                state="Blocked",
                next_step="A different action.",
                blocker="Required source is unavailable.",
            )
            with self.assertRaisesRegex(MODULE.ContextError, "does not match"):
                MODULE.verify_elim_closeout(
                    repo,
                    self.elim_result(
                        outcome="blocked",
                        continuation_state="retryable",
                        next_action=next_action,
                    ),
                )

    def test_inactive_handoff_rejects_uncleared_task_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_current_audit(repo, state="Inactive")
            path = repo / "framework/logs/CURRENT_AUDIT.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "| Completed steps | None. |",
                    "| Completed steps | Work is complete. |",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(MODULE.ContextError, "Completed steps"):
                MODULE.verify_elim_closeout(repo, self.elim_result())

    def test_elim_result_is_required_and_fails_closed_when_malformed(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            missing = repo / ".tmp/missing.json"
            with self.assertRaisesRegex(MODULE.ContextError, "did not emit"):
                MODULE.read_elim_result(missing, repo)

            malformed = repo / ".tmp/malformed.json"
            malformed.parent.mkdir()
            malformed.write_text('{"outcome":"completed"}\n', encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ContextError, "approved schema"):
                MODULE.read_elim_result(malformed, repo)

    def test_dispatcher_result_gate_controls_success_marking(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            result_path = repo / ".tmp/result.json"
            result_path.parent.mkdir()
            self.write_current_audit(repo, state="Inactive")
            self.write_elim_run_log(repo)
            result_path.write_text(
                json.dumps(self.elim_result()) + "\n",
                encoding="utf-8",
            )
            with mock.patch.object(MODULE, "verify_successful_elim_evidence"):
                outcome, complete, reason = MODULE.enforce_elim_result_closeout(
                    0,
                    repo=repo,
                    result_path=result_path,
                )
            self.assertEqual(outcome, 0)
            self.assertTrue(complete)
            self.assertEqual(reason, "")

            self.write_current_audit(
                repo,
                state="Open",
                next_step="Finish synchronization.",
            )
            outcome, complete, reason = MODULE.enforce_elim_result_closeout(
                0,
                repo=repo,
                result_path=result_path,
            )
            self.assertEqual(outcome, 6)
            self.assertFalse(complete)
            self.assertIn("state Inactive", reason)

            outcome, complete, reason = MODULE.enforce_elim_result_closeout(
                0,
                repo=repo,
                result_path=repo / ".tmp/missing.json",
            )
            self.assertEqual(outcome, 6)
            self.assertFalse(complete)
            self.assertIn("did not emit", reason)

    def test_success_gate_is_chain_bound_without_mutating_user_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            result_path = repo / ".tmp/result.json"
            result_path.parent.mkdir()
            self.write_current_audit(repo, state="Inactive")
            self.write_elim_run_log(repo)
            result_path.write_text(
                json.dumps(self.elim_result()) + "\n",
                encoding="utf-8",
            )
            with (
                mock.patch.object(MODULE, "require_clean_repo") as clean,
                mock.patch.object(MODULE, "verify_successful_elim_evidence"),
            ):
                outcome, complete, reason = MODULE.enforce_elim_result_closeout(
                    0,
                    repo=repo,
                    result_path=result_path,
                    git="/usr/bin/git",
                    expected_run_id="chain-1",
            )
            self.assertEqual((outcome, complete, reason), (0, True, ""))
            clean.assert_called_once_with("/usr/bin/git", repo)

            with (
                mock.patch.object(MODULE, "require_clean_repo") as clean,
                mock.patch.object(MODULE, "verify_successful_elim_evidence"),
            ):
                outcome, complete, reason = MODULE.enforce_elim_result_closeout(
                    0,
                    repo=repo,
                    result_path=result_path,
                    git="/usr/bin/git",
                    expected_run_id="different-chain",
                )
            self.assertEqual(outcome, 6)
            self.assertFalse(complete)
            self.assertIn("current Chain ID", reason)
            clean.assert_not_called()

    def test_closeout_converts_clean_tree_runtime_error_to_failed_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            result_path = repo / ".tmp/result.json"
            result_path.parent.mkdir()
            self.write_current_audit(repo, state="Inactive")
            self.write_elim_run_log(repo)
            result_path.write_text(
                json.dumps(self.elim_result()) + "\n",
                encoding="utf-8",
            )
            with (
                mock.patch.object(
                    MODULE,
                    "require_clean_repo",
                    side_effect=RuntimeError("unexpected dirty checkout"),
                ),
                mock.patch.object(MODULE, "verify_successful_elim_evidence"),
            ):
                outcome, complete, reason = MODULE.enforce_elim_result_closeout(
                    0,
                    repo=repo,
                    result_path=result_path,
                    git="/usr/bin/git",
                    expected_run_id="chain-1",
                )
            self.assertEqual(outcome, 6)
            self.assertFalse(complete)
            self.assertIn("unexpected dirty checkout", reason)

    def test_legacy_active_is_not_an_approved_handoff_state(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_current_audit(
                repo,
                state="Active",
                next_step="Continue.",
                blocker="None.",
            )
            with self.assertRaisesRegex(MODULE.ContextError, "invalid Handoff state"):
                MODULE.read_current_audit(
                    repo / "framework/logs/CURRENT_AUDIT.md",
                    repo,
                )

    def test_preserved_inputs_are_independently_rehashed(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            artifact = repo / ".tmp/artifact"
            inputs = artifact / "inputs"
            inputs.mkdir(parents=True)
            queue_inputs = {}
            filenames = {
                "integrity": "integrity.json",
                "progress": "progress.json",
                "intake": "intake.json",
                "review_epoch": "review-epoch.json",
                "chain": "chain.json",
            }
            for name, filename in filenames.items():
                path = inputs / filename
                path.write_text(json.dumps({"name": name}) + "\n", encoding="utf-8")
                queue_inputs[name] = {
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()
                }
            manifest = artifact / "run-chain.json"
            manifest.write_text("{}\n", encoding="utf-8")
            queue = repo / ".tmp/queue.json"
            queue.write_text(json.dumps({"inputs": queue_inputs}), encoding="utf-8")
            verified = MODULE.materialize_verified_inputs(
                {"manifest": {"dataBranch": "unused"}, "repository": "unused/unused"},
                repo=repo,
                manifest_path=manifest,
                queue_path=queue,
                destination=repo / ".tmp/local-inputs",
            )
            self.assertEqual(set(verified), set(queue_inputs))
            self.assertTrue(
                all(not Path(item["path"]).is_absolute() for item in verified.values())
            )

    def test_elim_runtime_failure_is_projected_to_local_console_state(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            config = {"manifest": {"localFallback": ".tmp/run-chain.json"}}
            control = {"last_failed_reason": "Review Epoch was not recorded."}
            payload = {"chain_id": "chain-1", "status": "complete"}
            MODULE.record_elim_runtime(
                repo=repo,
                config=config,
                control=control,
                payload=payload,
                outcome=4,
            )
            self.assertEqual(control["elim_runtime"]["status"], "failed")
            projected = json.loads(
                (repo / ".tmp/run-chain.json").read_text(encoding="utf-8")
            )
            self.assertEqual(projected["elim_runtime"]["id"], "elim")
            self.assertIn("Review Epoch", projected["elim_runtime"]["details"])

    def test_elim_runtime_uses_current_chain_and_safe_stop_status(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            config = {"manifest": {"localFallback": ".tmp/run-chain.json"}}
            control = {}
            payload = {"chain_id": "chain-current", "status": "complete"}
            (repo / ".tmp").mkdir()
            (repo / ".tmp/run-chain.json").write_text(
                json.dumps(
                    {
                        "chain_id": "chain-stale",
                        "status": "complete",
                        "elim_runtime": {
                            "chain_id": "chain-stale",
                            "status": "failed",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            MODULE.record_elim_runtime(
                repo=repo,
                config=config,
                control=control,
                payload=payload,
                outcome=5,
                result_outcome="usage_stopped",
            )
            self.assertEqual(control["elim_runtime"]["chain_id"], "chain-current")
            self.assertEqual(control["elim_runtime"]["status"], "usage-stopped")
            self.assertEqual(payload["host_status"], "usage-stopped")
            projected = json.loads(
                (repo / ".tmp/run-chain.json").read_text(encoding="utf-8")
            )
            self.assertEqual(projected["chain_id"], "chain-current")
            self.assertEqual(projected["elim_runtime"]["chain_id"], "chain-current")
            self.assertEqual(projected["elim_runtime"]["status"], "usage-stopped")
            self.assertEqual(projected["host_status"], "usage-stopped")
            self.assertEqual(
                projected["host_updated_at"],
                projected["elim_runtime"]["completed_at"],
            )

    def test_dead_dispatch_owner_is_recovered_as_failed_elim_run(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            state = repo / ".tmp/run-coordinator"
            lock = state / "host-dispatch.lock"
            lock.mkdir(parents=True)
            (lock / "owner.json").write_text(
                json.dumps(
                    {
                        "pid": 999999,
                        "chain_id": "chain-interrupted",
                        "status": "elim-running",
                        "started_at": "2026-07-24T16:52:11+00:00",
                        "output_path": (
                            ".tmp/run-coordinator/"
                            "elim-chain-interrupted.jsonl"
                        ),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            manifest = state / "run-chain.json"
            manifest.write_text(
                json.dumps(
                    {
                        "chain_id": "chain-interrupted",
                        "status": "complete",
                        "failures": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            config = json.loads(
                (ROOT / ".github" / "run-coordinator-bot.json").read_text()
            )
            config["manifest"]["localFallback"] = ".tmp/run-coordinator/run-chain.json"
            control = {}
            with (
                mock.patch.object(MODULE, "process_is_alive", return_value=False),
                mock.patch.object(MODULE, "command"),
            ):
                recovered, lease = MODULE.acquire_dispatch_lock(
                    lock,
                    repo=repo,
                    config=config,
                    control=control,
                )
                self.assertTrue(recovered)
            self.assertEqual(control["elim_runtime"]["status"], "failed")
            self.assertEqual(
                control["last_failed_chain_id"],
                "chain-interrupted",
            )
            self.assertEqual(len(control["action_items"]), 1)
            projected = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(projected["status"], "failed")
            self.assertEqual(projected["failures"][-1]["stage"], "elim")
            self.assertIn("interrupted", projected["elim_runtime"]["details"])
            self.assertTrue(lease.owner_path.is_file())
            MODULE.release_dispatch_lock(lease)
            self.assertTrue(lock.is_file())
            self.assertFalse(lease.owner_path.exists())

    def test_abandoned_post_spawn_owner_creates_run_log_reconciliation(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            state = repo / ".tmp/run-coordinator"
            state.mkdir(parents=True)
            lock = state / "host-dispatch.lock"
            lock.touch()
            execution = state / "elim-checkout"
            chain_state = execution / ".tmp/run-coordinator/chain-abrupt"
            chain_state.mkdir(parents=True)
            output = chain_state / "elim-chain-abrupt.jsonl"
            output.write_text('{"type":"thread.started"}\n', encoding="utf-8")
            usage = chain_state / "usage-status.json"
            usage.write_text('{"status":"pass"}\n', encoding="utf-8")
            current_audit = execution / MODULE.CURRENT_AUDIT_LOG
            current_audit.parent.mkdir(parents=True)
            current_audit.write_text(
                "# Abrupt CURRENT_AUDIT checkpoint\n",
                encoding="utf-8",
            )
            selected = self.selected_manifest(
                kind="bot_failure",
                issue_id=None,
            )
            selected["chain_id"] = "chain-abrupt"
            selected["work_queue"]["next_item"]["source"] = {"input": "chain"}
            (chain_state / "run-chain.json").write_text(
                json.dumps(selected) + "\n",
                encoding="utf-8",
            )
            manifest = state / "run-chain.json"
            manifest.write_text(
                json.dumps({"chain_id": "chain-abrupt", "failures": []}) + "\n",
                encoding="utf-8",
            )
            owner_path = lock.with_name(f"{lock.name}.owner.json")
            owner_path.write_text(
                json.dumps(
                    {
                        "pid": 999999,
                        "chain_id": "chain-abrupt",
                        "invocation_id": (
                            "chain-abrupt-20260724T120000Z"
                        ),
                        "status": "elim-running",
                        "started_at": "2026-07-24T12:00:00+00:00",
                        "execution_checkout": (
                            ".tmp/run-coordinator/elim-checkout"
                        ),
                        "output_path": (
                            ".tmp/run-coordinator/elim-checkout/"
                            ".tmp/run-coordinator/chain-abrupt/"
                            "elim-chain-abrupt.jsonl"
                        ),
                        "usage_status_path": (
                            ".tmp/run-coordinator/elim-checkout/"
                            ".tmp/run-coordinator/chain-abrupt/"
                            "usage-status.json"
                        ),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            config = json.loads(
                (ROOT / ".github" / "run-coordinator-bot.json").read_text()
            )
            config["manifest"]["localFallback"] = (
                ".tmp/run-coordinator/run-chain.json"
            )
            with mock.patch.object(MODULE, "command"):
                recovered, lease = MODULE.acquire_dispatch_lock(
                    lock,
                    repo=repo,
                    config=config,
                    control={},
                )
            self.assertTrue(recovered)
            pending = MODULE.read_pending_run_log_reconciliations(
                repo,
                repo / MODULE.ELIM_RUN_LOG_RECONCILIATION_STATE,
            )
            self.assertEqual(
                [row["chain_id"] for row in pending["items"]],
                ["chain-abrupt"],
            )
            preserved = (
                execution
                / pending["items"][0]["artifacts"]["current_audit"]
            )
            self.assertEqual(
                preserved.read_text(encoding="utf-8"),
                "# Abrupt CURRENT_AUDIT checkpoint\n",
            )
            MODULE.release_dispatch_lock(lease)

    def test_live_dispatch_owner_cannot_be_recovered(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            lock = repo / ".tmp/run-coordinator/host-dispatch.lock"
            lock.parent.mkdir(parents=True)
            first_descriptor = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
            MODULE.fcntl.flock(
                first_descriptor,
                MODULE.fcntl.LOCK_EX | MODULE.fcntl.LOCK_NB,
            )
            config = json.loads(
                (ROOT / ".github" / "run-coordinator-bot.json").read_text()
            )
            try:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "another host dispatcher",
                ):
                    MODULE.acquire_dispatch_lock(
                        lock,
                        repo=repo,
                        config=config,
                        control={},
                    )
            finally:
                MODULE.fcntl.flock(first_descriptor, MODULE.fcntl.LOCK_UN)
                os.close(first_descriptor)

    def test_dispatch_owner_token_is_required_for_update_and_release(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            state = repo / ".tmp/run-coordinator"
            state.mkdir(parents=True)
            (state / "run-chain.json").write_text("{}\n", encoding="utf-8")
            config = json.loads(
                (ROOT / ".github" / "run-coordinator-bot.json").read_text()
            )
            config["manifest"]["localFallback"] = ".tmp/run-coordinator/run-chain.json"
            _, lease = MODULE.acquire_dispatch_lock(
                state / "host-dispatch.lock",
                repo=repo,
                config=config,
                control={},
            )
            owner = json.loads(lease.owner_path.read_text(encoding="utf-8"))
            owner["owner_token"] = "different-acquisition"
            lease.owner_path.write_text(json.dumps(owner) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "ownership changed"):
                MODULE.write_dispatch_lock_owner(lease, updates={"status": "test"})
            with self.assertRaisesRegex(RuntimeError, "another acquisition"):
                MODULE.release_dispatch_lock(lease)
            self.assertTrue(lease.owner_path.is_file())

    def test_abandoned_pre_elim_owner_does_not_fabricate_elim_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            state = repo / ".tmp/run-coordinator"
            state.mkdir(parents=True)
            manifest = state / "run-chain.json"
            manifest.write_text(
                json.dumps({"chain_id": "chain-1", "failures": []}) + "\n",
                encoding="utf-8",
            )
            owner_path = state / "host-dispatch.lock.owner.json"
            owner_path.write_text(
                json.dumps(
                    {
                        "owner_token": "abandoned",
                        "chain_id": "chain-1",
                        "status": "usage-gated",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            config = json.loads(
                (ROOT / ".github" / "run-coordinator-bot.json").read_text()
            )
            config["manifest"]["localFallback"] = ".tmp/run-coordinator/run-chain.json"
            control = {}
            recovered, lease = MODULE.acquire_dispatch_lock(
                state / "host-dispatch.lock",
                repo=repo,
                config=config,
                control=control,
            )
            self.assertTrue(recovered)
            self.assertNotIn("elim_runtime", control)
            projected = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(projected["failures"][-1]["stage"], "run-coordinator")
            self.assertNotIn("elim_runtime", projected)
            self.assertFalse(
                (repo / MODULE.ELIM_RUN_LOG_RECONCILIATION_STATE).exists()
            )
            MODULE.release_dispatch_lock(lease)

    def test_legacy_lock_recovery_accepts_known_owner_temp_residue(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            state = repo / ".tmp/run-coordinator"
            lock = state / "host-dispatch.lock"
            lock.mkdir(parents=True)
            (lock / "owner.json").write_text(
                json.dumps({"pid": 999999, "status": "dispatcher-running"}) + "\n",
                encoding="utf-8",
            )
            (lock / "owner.json.tmp").write_text("{}\n", encoding="utf-8")
            (state / "run-chain.json").write_text(
                json.dumps({"chain_id": "chain-1", "failures": []}) + "\n",
                encoding="utf-8",
            )
            config = json.loads(
                (ROOT / ".github" / "run-coordinator-bot.json").read_text()
            )
            config["manifest"]["localFallback"] = ".tmp/run-coordinator/run-chain.json"
            recovered, lease = MODULE.acquire_dispatch_lock(
                lock,
                repo=repo,
                config=config,
                control={},
            )
            self.assertTrue(recovered)
            self.assertTrue(lock.is_file())
            MODULE.release_dispatch_lock(lease)

    def test_abnormal_elim_exit_reports_open_checkpoint_as_recovery_only(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_current_audit(
                repo,
                state="Open",
                next_step="Resume the interrupted unit.",
            )
            outcome, complete, reason = MODULE.enforce_elim_result_closeout(
                130,
                repo=repo,
                result_path=repo / "missing.json",
            )
            self.assertEqual(outcome, 130)
            self.assertFalse(complete)
            self.assertIn("unfinished-work evidence", reason)
            self.assertIn("never runtime liveness", reason)

    def test_retryable_terminal_result_is_failed_but_run_log_accounted(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            result_path = repo / ".tmp/result.json"
            result_path.parent.mkdir()
            next_action = "Retry the exact selected unit from its checkpoint."
            self.write_current_audit(
                repo,
                state="Blocked",
                next_step=next_action,
                blocker="The required source was unavailable.",
            )
            result = self.elim_result(
                outcome="failed",
                continuation_state="retryable",
                next_action=next_action,
            )
            result_path.write_text(json.dumps(result) + "\n", encoding="utf-8")
            accounting = {}
            with mock.patch.object(
                MODULE,
                "verify_successful_elim_evidence",
            ) as evidence:
                outcome, complete, reason = MODULE.enforce_elim_result_closeout(
                    9,
                    repo=repo,
                    result_path=result_path,
                    expected_manifest=self.selected_manifest(),
                    accounting=accounting,
                )
            self.assertEqual(outcome, 9)
            self.assertFalse(complete)
            self.assertIn("safely closed", reason)
            self.assertTrue(accounting["run_log_verified"])
            evidence.assert_called_once()

    def test_pending_run_log_reconciliation_is_post_spawn_only_and_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            execution = repo / ".tmp/run-coordinator/elim-checkout"
            execution.mkdir(parents=True)
            current_audit = execution / MODULE.CURRENT_AUDIT_LOG
            current_audit.parent.mkdir(parents=True)
            current_audit.write_text(
                "# Preserved abrupt checkpoint\n",
                encoding="utf-8",
            )
            state_path = repo / MODULE.ELIM_RUN_LOG_RECONCILIATION_STATE
            payload = self.selected_manifest(kind="bot_failure", issue_id=None)
            payload["work_queue"]["next_item"]["source"] = {
                "input": "chain",
            }
            invocation_id = "chain-1-20260724T120000Z"
            launch_state = {
                "spawned": False,
                "run_log_verified": False,
                "execution_checkout": (
                    ".tmp/run-coordinator/elim-checkout"
                ),
                "artifacts": {
                    "output": ".tmp/run-coordinator/chain-1/output.jsonl",
                    "current_audit": MODULE.CURRENT_AUDIT_LOG,
                },
            }
            persisted = MODULE.persist_pending_run_log_reconciliation(
                repo,
                state_path,
                payload=payload,
                invocation_id=invocation_id,
                failure_stage="usage-gate",
                reason_code="pre-launch-failure",
                failure_summary="No process was launched.",
                launch_state=launch_state,
            )
            self.assertFalse(persisted)
            self.assertFalse(state_path.exists())

            launch_state["spawned"] = True
            persisted = MODULE.persist_pending_run_log_reconciliation(
                repo,
                state_path,
                payload=payload,
                invocation_id=invocation_id,
                failure_stage="elim-execution",
                reason_code="post-spawn-interruption",
                failure_summary="The launched process was interrupted.",
                launch_state=launch_state,
            )
            self.assertTrue(persisted)
            state = MODULE.read_pending_run_log_reconciliations(
                repo,
                state_path,
            )
            self.assertEqual(
                [row["chain_id"] for row in state["items"]],
                ["chain-1"],
            )
            self.assertEqual(
                state["items"][0]["reason_code"],
                "post-spawn-interruption",
            )
            checkpoint = (
                execution
                / state["items"][0]["artifacts"]["current_audit"]
            )
            self.assertEqual(
                checkpoint.read_text(encoding="utf-8"),
                "# Preserved abrupt checkpoint\n",
            )

            launch_state["run_log_verified"] = True
            self.assertFalse(
                MODULE.persist_pending_run_log_reconciliation(
                    repo,
                    state_path,
                    payload=payload,
                    invocation_id=invocation_id,
                    failure_stage="elim-closeout",
                    reason_code="already-accounted",
                    failure_summary="The Run Log was already verified.",
                    launch_state=launch_state,
                )
            )

    def test_reconciliation_clears_only_exact_unchanged_completed_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            execution = repo / ".tmp/run-coordinator/elim-checkout"
            execution.mkdir(parents=True)
            state_path = repo / MODULE.ELIM_RUN_LOG_RECONCILIATION_STATE
            payload = self.selected_manifest(kind="bot_failure", issue_id=None)
            payload["work_queue"]["next_item"]["source"] = {
                "input": "chain",
            }
            MODULE.persist_pending_run_log_reconciliation(
                repo,
                state_path,
                payload=payload,
                invocation_id="chain-1-20260724T120000Z",
                failure_stage="elim-execution",
                reason_code="post-spawn-interruption",
                failure_summary="Interrupted.",
                launch_state={
                    "spawned": True,
                    "run_log_verified": False,
                    "execution_checkout": (
                        ".tmp/run-coordinator/elim-checkout"
                    ),
                    "artifacts": {},
                },
            )
            digest = hashlib.sha256(state_path.read_bytes()).hexdigest()
            repair_manifest = self.selected_manifest(
                kind="bot_failure",
                issue_id=None,
            )
            repair_manifest["chain_id"] = "repair-chain"
            repair_manifest["work_queue"]["next_item"].update(
                {
                    "source_revision": digest,
                    "source": {
                        "input": "run_log_reconciliation",
                        "pending_chain_ids": ["chain-1"],
                    },
                }
            )
            result = self.elim_result()
            result["outcome"] = "completed"
            MODULE.clear_reconciled_run_log_items(
                repo,
                state_path,
                payload=repair_manifest,
                result=result,
            )
            state = MODULE.read_pending_run_log_reconciliations(
                repo,
                state_path,
            )
            self.assertEqual(state["items"], [])

    def test_nonpassing_final_usage_attestation_prevents_success(self):
        self.assertEqual(
            MODULE.enforce_usage_monitor_closeout(0, {"status": "abort"}),
            5,
        )
        self.assertEqual(
            MODULE.enforce_usage_monitor_closeout(0, {"status": "unavailable"}),
            5,
        )
        self.assertEqual(
            MODULE.enforce_usage_monitor_closeout(0, {"status": "pass"}),
            0,
        )
        self.assertEqual(
            MODULE.enforce_usage_monitor_closeout(4, {"status": "pass"}),
            4,
        )

    def test_unspecified_launch_authority_is_fail_closed(self):
        payload = {
            "elim_decision": {
                "launch_recommended": True,
                "reason": "Queue contains work.",
            }
        }
        result = MODULE.enforce_trigger_launch_boundary(payload)
        self.assertFalse(result["elim_decision"]["launch_recommended"])
        self.assertIn("unspecified trigger", result["elim_decision"]["reason"])

    def test_authorized_trigger_preserves_launch_decision(self):
        payload = {
            "llm_launch_allowed": True,
            "elim_decision": {
                "launch_recommended": True,
                "reason": "Queue contains work.",
            },
        }
        result = MODULE.enforce_trigger_launch_boundary(payload)
        self.assertTrue(result["elim_decision"]["launch_recommended"])

    def test_monitor_probe_converts_host_read_error_to_unavailable(self):
        result = MODULE.monitored_usage_probe(
            lambda: (_ for _ in ()).throw(RuntimeError("meter unavailable"))
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("meter unavailable", result["error"])

    def test_result_is_bound_to_exact_selected_manifest_unit(self):
        manifest = self.selected_manifest()
        result = self.elim_result()
        MODULE.verify_elim_result_binding(manifest, result)
        variants = (
            ("run_id", "different-chain", "Chain ID"),
            ("unit_id", "different-unit", "work-unit ID"),
            ("work_type", "issue_audit", "work_type"),
            ("issue_id", "TEST-002", "issue identity"),
            (
                "canonical_record",
                "areas/TEST/issues/TEST-002.md",
                "canonical identity",
            ),
        )
        for field, value, expected in variants:
            with self.subTest(field=field):
                changed = {**result, field: value}
                with self.assertRaisesRegex(MODULE.ContextError, expected):
                    MODULE.verify_elim_result_binding(manifest, changed)

    def test_candidate_research_result_binding_preserves_nonissue_identity(self):
        canonical = "https://github.com/Thorncrag/ARRP/issues/255"
        manifest = {
            "chain_id": "chain-1",
            "work_queue": {
                "selected_work_item_id": "unit-1",
                "next_item": {
                    "id": "unit-1",
                    "kind": "candidate_research",
                    "source": {
                        "identifier": "HOR-035",
                        "canonicalRecord": canonical,
                    },
                },
            },
            "context_packet": {
                "work_item_id": "unit-1",
                "issue_id": None,
                "canonical_record": canonical,
            },
        }
        result = self.elim_result()
        result.update(
            {
                "work_type": "candidate_research",
                "issue_id": None,
                "canonical_record": canonical,
            }
        )
        MODULE.verify_elim_result_binding(manifest, result)

    def test_successful_closeout_requires_current_chain_run_log(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            result_path = repo / ".tmp/result.json"
            result_path.parent.mkdir()
            self.write_current_audit(repo, state="Inactive")
            result_path.write_text(
                json.dumps(self.elim_result()) + "\n",
                encoding="utf-8",
            )
            with (
                mock.patch.object(MODULE, "require_clean_repo"),
                mock.patch.object(
                    MODULE,
                    "verify_commit_and_synchronization",
                    return_value=({MODULE.ELIM_RUN_LOG}, "b" * 40),
                ),
                mock.patch.object(
                    MODULE,
                    "git_text_at_commit",
                    return_value="# Elim Run Log\n",
                ),
            ):
                outcome, complete, reason = MODULE.enforce_elim_result_closeout(
                    0,
                    repo=repo,
                    result_path=result_path,
                    git="/usr/bin/git",
                    expected_manifest=self.selected_manifest(),
                )
            self.assertEqual(outcome, 6)
            self.assertFalse(complete)
            self.assertIn("no Run Log report", reason)

    def test_material_success_requires_shared_log_reachable_commit_and_sync(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_elim_run_log(repo, material=True)
            result = self.elim_result()
            result["files_touched"] = [
                "areas/TEST/issues/TEST-001.md",
                "framework/logs/AGENT_AUDIT_LOG.md",
                "framework/logs/ELIM_RUN_LOG.md",
            ]
            result["synchronization"] = ["Merged pull request to origin/main."]
            def completed(argv, **_kwargs):
                if argv[1] == "diff":
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=(
                            "areas/TEST/issues/TEST-001.md\n"
                            "framework/logs/AGENT_AUDIT_LOG.md\n"
                            "framework/logs/ELIM_RUN_LOG.md\n"
                        ),
                        stderr="",
                    )
                if argv[1] == "show":
                    revision, relative = argv[2].split(":", 1)
                    if revision == "b" * 40:
                        return MODULE.subprocess.CompletedProcess(
                            argv, 0, stdout="# Elim Run Log\n\n## Runs\n", stderr=""
                        )
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=(repo / relative).read_text(encoding="utf-8"),
                        stderr="",
                    )
                if argv[1] == "rev-list":
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=f"{'a' * 40} {'b' * 40}\n",
                        stderr="",
                    )
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="a" * 40 + "\n", stderr=""
                )
            with mock.patch.object(MODULE, "command", side_effect=completed):
                MODULE.verify_successful_elim_evidence(
                    repo,
                    result,
                    git="/usr/bin/git",
                    expected_manifest=self.selected_manifest(),
                )

    def test_clean_launched_outcome_requires_durable_run_log_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_elim_run_log(repo, outcome="Clean")
            result = self.elim_result(outcome="clean")
            result.update(
                {
                    "work_type": "integrity",
                    "issue_id": None,
                    "canonical_record": None,
                    "files_touched": [MODULE.ELIM_RUN_LOG],
                }
            )
            def clean_boundary(argv, **_kwargs):
                if argv[1] == "diff":
                    return MODULE.subprocess.CompletedProcess(
                        argv, 0, stdout=MODULE.ELIM_RUN_LOG + "\n", stderr=""
                    )
                if argv[1] == "show":
                    revision = argv[2].split(":", 1)[0]
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=(
                            "# Elim Run Log\n\n## Runs\n"
                            if revision == "b" * 40
                            else (repo / MODULE.ELIM_RUN_LOG).read_text(
                                encoding="utf-8"
                            )
                        ),
                        stderr="",
                    )
                if argv[1] == "rev-list":
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=f"{'a' * 40} {'b' * 40}\n",
                        stderr="",
                    )
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="a" * 40 + "\n", stderr=""
                )
            with mock.patch.object(MODULE, "command", side_effect=clean_boundary):
                MODULE.verify_successful_elim_evidence(
                    repo,
                    result,
                    git="/usr/bin/git",
                    expected_manifest=self.selected_manifest(),
                )
            result["commit"] = None
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "full verified Git commit",
            ):
                MODULE.verify_successful_elim_evidence(
                    repo,
                    result,
                    git="/usr/bin/git",
                    expected_manifest=self.selected_manifest(),
                )
            result["commit"] = None
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "full verified Git commit",
            ):
                MODULE.verify_successful_elim_evidence(
                    repo,
                    result,
                    git="/usr/bin/git",
                    expected_manifest=self.selected_manifest(),
                )

    def test_human_review_accepts_verified_open_pr_without_merging(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_elim_run_log(repo, material=True, outcome="Human review")
            commit = "a" * 40
            result = self.elim_result()
            result.update(
                {
                    "outcome": "human_review",
                    "files_touched": [
                        "areas/TEST/issues/TEST-001.md",
                        "framework/logs/AGENT_AUDIT_LOG.md",
                        "framework/logs/ELIM_RUN_LOG.md",
                    ],
                    "commit": commit,
                    "synchronization": [
                        "Pushed review branch.",
                        "Opened pull request.",
                        "Readback confirmed the open pull request head.",
                    ],
                    "human_questions": ["Approve the proposed material change?"],
                    "continuation": {
                        "state": "human_required",
                        "next_action": "Review the open pull request.",
                    },
                }
            )
            def human_review_command(argv, **_kwargs):
                if argv[1] == "show":
                    revision, relative = argv[2].split(":", 1)
                    if revision == "b" * 40:
                        return MODULE.subprocess.CompletedProcess(
                            argv, 0, stdout="# Elim Run Log\n\n## Runs\n", stderr=""
                        )
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=(repo / relative).read_text(encoding="utf-8"),
                        stderr="",
                    )
                if argv[1] == "rev-parse":
                    revision = "a" * 40 if argv[2] == "HEAD" else "b" * 40
                    return MODULE.subprocess.CompletedProcess(
                        argv, 0, stdout=revision + "\n", stderr=""
                    )
                if argv[1] == "branch":
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout="  origin/codex/elim-review\n",
                        stderr="",
                    )
                if argv[1:3] == ["pr", "list"]:
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=json.dumps(
                            [
                                {
                                    "number": 42,
                                    "headRefOid": commit,
                                    "baseRefName": "main",
                                    "baseRefOid": "b" * 40,
                                    "url": "https://github.com/Thorncrag/ARRP/pull/42",
                                }
                            ]
                        ),
                        stderr="",
                    )
                if argv[1:3] == ["pr", "diff"]:
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=(
                            "areas/TEST/issues/TEST-001.md\n"
                            "framework/logs/AGENT_AUDIT_LOG.md\n"
                            "framework/logs/ELIM_RUN_LOG.md\n"
                        ),
                        stderr="",
                    )
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="", stderr=""
                )
            with mock.patch.object(
                MODULE,
                "command",
                side_effect=human_review_command,
            ):
                MODULE.verify_successful_elim_evidence(
                    repo,
                    result,
                    git="/usr/bin/git",
                    gh="/opt/homebrew/bin/gh",
                    expected_manifest=self.selected_manifest(),
                )

    def test_material_closeout_rejects_old_ancestor_commit_with_current_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_elim_run_log(repo, material=True)
            result = self.elim_result()
            result.update(
                {
                    "commit": "b" * 40,
                    "files_touched": [
                        "areas/TEST/issues/TEST-001.md",
                        "framework/logs/AGENT_AUDIT_LOG.md",
                        "framework/logs/ELIM_RUN_LOG.md",
                    ],
                    "synchronization": ["Merged and read back origin/main."],
                }
            )
            def old_boundary(argv, **_kwargs):
                if argv[1] == "rev-parse":
                    return MODULE.subprocess.CompletedProcess(
                        argv, 0, stdout="a" * 40 + "\n", stderr=""
                    )
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="", stderr=""
                )
            with mock.patch.object(MODULE, "command", side_effect=old_boundary):
                with self.assertRaisesRegex(
                    MODULE.ContextError,
                    "exact reviewed origin/main boundary",
                ):
                    MODULE.verify_successful_elim_evidence(
                        repo,
                        result,
                        git="/usr/bin/git",
                        expected_manifest=self.selected_manifest(),
                    )

    def test_material_closeout_rejects_hidden_extra_changed_file(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_elim_run_log(repo, material=True)
            result = self.elim_result()
            result["files_touched"] = [
                "areas/TEST/issues/TEST-001.md",
                MODULE.AGENT_AUDIT_LOG,
                MODULE.ELIM_RUN_LOG,
            ]
            def hidden_change(argv, **_kwargs):
                if argv[1] == "diff":
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=(
                            "\n".join(
                                [
                                    *result["files_touched"],
                                    "areas/TEST/issues/HIDDEN.md",
                                ]
                            )
                            + "\n"
                        ),
                        stderr="",
                    )
                if argv[1] == "rev-list":
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=f"{'a' * 40} {'b' * 40}\n",
                        stderr="",
                    )
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="a" * 40 + "\n", stderr=""
                )
            with mock.patch.object(MODULE, "command", side_effect=hidden_change):
                with self.assertRaisesRegex(
                    MODULE.ContextError,
                    "unreported changed files.*HIDDEN",
                ):
                    MODULE.verify_successful_elim_evidence(
                        repo,
                        result,
                        git="/usr/bin/git",
                        expected_manifest=self.selected_manifest(),
                    )

    def test_run_log_report_must_be_complete_unique_new_and_match_outcome(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_elim_run_log(repo)
            result = self.elim_result()
            current = (repo / MODULE.ELIM_RUN_LOG).read_text(encoding="utf-8")

            def verify_with(current_text: str, prior_text: str = "# Elim Run Log\n"):
                with (
                    mock.patch.object(
                        MODULE,
                        "verify_commit_and_synchronization",
                        return_value=(
                            {MODULE.ELIM_RUN_LOG},
                            "b" * 40,
                        ),
                    ),
                    mock.patch.object(
                        MODULE,
                        "git_text_at_commit",
                        side_effect=[current_text, prior_text],
                    ),
                ):
                    MODULE.verify_successful_elim_evidence(
                        repo,
                        result,
                        git="/usr/bin/git",
                        expected_manifest=self.selected_manifest(),
                    )

            verify_with(current)
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "incomplete.*Validation",
            ):
                verify_with(
                    current.replace(
                        "| Validation | Focused checks passed. |\n",
                        "",
                    )
                )
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "outcome does not match",
            ):
                verify_with(
                    current.replace(
                        "| Outcome | Completed |",
                        "| Outcome | Failed |",
                    )
                )
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "exactly one Run Log report",
            ):
                section = current[current.index("### 2026-07-24") :]
                verify_with(current + "\n" + section)
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "predates the reviewed Git boundary",
            ):
                verify_with(current, current)

    def test_run_log_repair_proves_prior_chain_reports_are_newly_synchronized(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_elim_run_log(repo)
            current = (repo / MODULE.ELIM_RUN_LOG).read_text(encoding="utf-8")
            current_section = current[current.index("### 2026-07-24") :]
            repaired_section = current_section.replace(
                "chain-1",
                "failed-chain",
            ).replace("| Outcome | Completed |", "| Outcome | Failed |")
            repaired_body = current + "\n" + repaired_section
            result = self.elim_result()
            result.update(
                {
                    "work_type": "bot_failure",
                    "issue_id": None,
                    "canonical_record": None,
                }
            )
            manifest = self.selected_manifest(
                kind="bot_failure",
                issue_id=None,
            )
            manifest["work_queue"]["next_item"]["source"] = {
                "input": "run_log_reconciliation",
                "pending_chain_ids": ["failed-chain"],
            }

            def verify_with(prior_body: str):
                with (
                    mock.patch.object(
                        MODULE,
                        "verify_commit_and_synchronization",
                        return_value=({MODULE.ELIM_RUN_LOG}, "b" * 40),
                    ),
                    mock.patch.object(
                        MODULE,
                        "git_text_at_commit",
                        side_effect=[repaired_body, prior_body],
                    ),
                ):
                    MODULE.verify_successful_elim_evidence(
                        repo,
                        result,
                        git="/usr/bin/git",
                        expected_manifest=manifest,
                    )

            verify_with("# Elim Run Log\n\n## Runs\n")
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "predates the reviewed repair boundary",
            ):
                verify_with(
                    "# Elim Run Log\n\n## Runs\n\n" + repaired_section
                )

    def test_applied_boundary_accounts_entire_pinned_baseline_range(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            self.write_elim_run_log(repo)
            result = self.elim_result()
            observed_diff: list[str] = []

            def multi_commit_boundary(argv, **_kwargs):
                if argv[1] == "rev-parse":
                    return MODULE.subprocess.CompletedProcess(
                        argv, 0, stdout="a" * 40 + "\n", stderr=""
                    )
                if argv[1] == "rev-list":
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=f"{'a' * 40} {'c' * 40}\n",
                        stderr="",
                    )
                if argv[1] == "diff":
                    observed_diff.extend(argv)
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=(
                            MODULE.ELIM_RUN_LOG
                            + "\nareas/TEST/issues/UNDECLARED-EARLIER.md\n"
                        ),
                        stderr="",
                    )
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="", stderr=""
                )

            with mock.patch.object(
                MODULE,
                "command",
                side_effect=multi_commit_boundary,
            ):
                with self.assertRaisesRegex(
                    MODULE.ContextError,
                    "unreported changed files.*UNDECLARED-EARLIER",
                ):
                    MODULE.verify_successful_elim_evidence(
                        repo,
                        result,
                        git="/usr/bin/git",
                        expected_manifest=self.selected_manifest(),
                    )
            self.assertIn("b" * 40, observed_diff)
            self.assertNotIn("c" * 40, observed_diff)

    def test_codex_launch_paths_are_all_inside_isolated_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            execution = Path(directory) / "checkout"
            chain = execution / ".tmp/run-coordinator/chain-1"
            chain.mkdir(parents=True)
            payload = {
                "work_queue": {"local_path": ".tmp/run-coordinator/chain-1/queue.json"},
                "context_packet": {
                    "local_path": ".tmp/run-coordinator/chain-1/context.json"
                },
                "verified_inputs": {
                    "integrity": {
                        "path": ".tmp/run-coordinator/chain-1/inputs/integrity.json"
                    }
                },
            }
            MODULE.validate_elim_launch_containment(
                execution,
                manifest=chain / "run-chain.json",
                payload=payload,
                usage_status_path=chain / "usage.json",
                output_path=chain / "events.jsonl",
                last_message_path=chain / "result.json",
            )
            payload["context_packet"]["local_path"] = str(
                Path(directory) / "canonical-context.json"
            )
            with self.assertRaises(MODULE.ContextError):
                MODULE.validate_elim_launch_containment(
                    execution,
                    manifest=chain / "run-chain.json",
                    payload=payload,
                    usage_status_path=chain / "usage.json",
                    output_path=chain / "events.jsonl",
                    last_message_path=chain / "result.json",
                )

    def test_interrupted_child_group_is_terminated_then_killed_and_reaped(self):
        process = mock.Mock()
        process.pid = 43210
        process.poll.return_value = None
        process.wait.side_effect = [
            MODULE.subprocess.TimeoutExpired(["codex"], 0.01),
            0,
        ]
        with mock.patch.object(MODULE.os, "killpg") as killpg:
            MODULE.terminate_process_group(process, timeout_seconds=0.01)
        self.assertEqual(
            killpg.call_args_list,
            [
                mock.call(43210, MODULE.signal.SIGTERM),
                mock.call(43210, MODULE.signal.SIGKILL),
            ],
        )
        self.assertEqual(process.wait.call_args_list[1], mock.call())

    def test_process_lookup_race_still_reaps_child(self):
        process = mock.Mock()
        process.pid = 43210
        process.poll.return_value = None
        process.wait.return_value = 0
        with mock.patch.object(
            MODULE.os,
            "killpg",
            side_effect=ProcessLookupError,
        ):
            MODULE.terminate_process_group(process, timeout_seconds=0.01)
        process.wait.assert_called_once_with(timeout=0.01)

    def test_post_spawn_exception_stops_and_reaps_child(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            state = repo / ".tmp/run-coordinator/chain-1"
            state.mkdir(parents=True)
            manifest = state / "run-chain.json"
            manifest.write_text("{}\n", encoding="utf-8")
            payload = {
                "chain_id": "chain-1",
                "elim_decision": {
                    "profile": {
                        "model": "gpt-5.6-sol",
                        "reasoning_effort": "high",
                    }
                },
                "work_queue": {
                    "local_path": ".tmp/run-coordinator/chain-1/queue.json",
                    "selected_work_item_id": "unit-1",
                    "next_item": {
                        "id": "unit-1",
                        "kind": "integrity",
                        "source": {},
                    },
                    "user_overrides": {
                        "request_sha256": MODULE.canonical_json_hash({})
                    },
                },
                "context_packet": {
                    "local_path": ".tmp/run-coordinator/chain-1/context.json",
                    "work_item_id": "unit-1",
                    "issue_id": None,
                    "canonical_record": None,
                },
                "usage": {"host_monitor": {}},
            }
            process = mock.Mock()
            process.pid = 43210
            process.stdin = mock.Mock()
            with (
                mock.patch.object(MODULE.subprocess, "Popen", return_value=process),
                mock.patch.object(
                    MODULE,
                    "write_dispatch_lock_owner",
                    side_effect=RuntimeError("injected post-spawn failure"),
                ),
                mock.patch.object(MODULE, "terminate_process_group") as terminate,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "injected post-spawn failure",
                ):
                    MODULE.launch_elim(
                        "/Applications/ChatGPT.app/Contents/Resources/codex",
                        repo,
                        repo,
                        manifest,
                        payload,
                        state,
                        usage_probe=lambda: {},
                        usage_status_path=state / "usage.json",
                        usage_attestation_args={},
                        monitor_interval_seconds=60,
                        dispatcher_lock=mock.Mock(),
                    )
            terminate.assert_called_once_with(process)

    def test_control_change_at_spawn_boundary_prevents_process_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            state = repo / ".tmp/run-coordinator/chain-1"
            state.mkdir(parents=True)
            manifest = state / "run-chain.json"
            manifest.write_text("{}\n", encoding="utf-8")
            control_path = repo / ".tmp/run-coordinator/control.json"
            control_path.write_text(
                json.dumps(
                    {
                        "overrides": {
                            "unit-1": {
                                "suppressed": True,
                                "reason": "Changed at the launch boundary.",
                            }
                        }
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            payload = {
                "chain_id": "chain-1",
                "elim_decision": {
                    "profile": {
                        "model": "gpt-5.6-sol",
                        "reasoning_effort": "high",
                    }
                },
                "work_queue": {
                    "local_path": ".tmp/run-coordinator/chain-1/queue.json",
                    "selected_work_item_id": "unit-1",
                    "next_item": {
                        "id": "unit-1",
                        "kind": "integrity",
                        "source": {},
                    },
                    "user_overrides": {
                        "request_sha256": MODULE.canonical_json_hash({})
                    },
                },
                "context_packet": {
                    "local_path": ".tmp/run-coordinator/chain-1/context.json",
                    "work_item_id": "unit-1",
                    "issue_id": None,
                    "canonical_record": None,
                },
                "usage": {"host_monitor": {}},
            }
            with mock.patch.object(MODULE.subprocess, "Popen") as popen:
                with self.assertRaises(MODULE.ControlSelectionChanged):
                    MODULE.launch_elim(
                        "/Applications/ChatGPT.app/Contents/Resources/codex",
                        repo,
                        repo,
                        manifest,
                        payload,
                        state,
                        usage_probe=lambda: {},
                        usage_status_path=state / "usage.json",
                        usage_attestation_args={},
                        monitor_interval_seconds=60,
                        dispatcher_lock=mock.Mock(),
                        control_path=control_path,
                        control_repo=repo,
                    )
            popen.assert_not_called()

    def test_public_intake_success_requires_matching_content_free_cursor(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            ledger = repo / "research/intake-review-ledger.jsonl"
            ledger.parent.mkdir(parents=True)
            result = self.elim_result()
            result["work_type"] = "public_intake"
            result["issue_id"] = None
            result["canonical_record"] = None
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "no Intake Review Ledger",
            ):
                MODULE.verify_intake_review_ledger(repo, result)
            ledger.write_text(
                json.dumps(
                    {
                        "run_id": "chain-1",
                        "unit_id": "unit-1",
                        "content_included": False,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            MODULE.verify_intake_review_ledger(repo, result)

    def test_usage_attestation_cooperatively_requests_safe_closeout(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            baseline = repo / ".tmp/run-coordinator/usage.json"
            baseline.parent.mkdir(parents=True)
            baseline.write_text("{}\n", encoding="utf-8")
            config = {
                "usage": {
                    "hardReservePercent": 15,
                    "softRunTargetPercent": 10,
                    "monitorIntervalSeconds": 60,
                    "snapshotMaxAgeSeconds": 120,
                }
            }
            stopped = MODULE.write_usage_attestation(
                repo / ".tmp/run-coordinator/usage-status.json",
                repo=repo,
                chain_id="chain-1",
                invocation_id="invocation-1",
                baseline_path=baseline,
                gate={
                    "status": "abort",
                    "checkedAtUtc": "2026-07-24T15:00:00+00:00",
                    "lowestRemainingPercent": 15,
                },
                config=config,
            )
            self.assertTrue(stopped["stop_requested"])
            self.assertEqual(stopped["new_substantive_unit_policy"], "no")
            self.assertIn("already-started atomic operation", stopped["host_directive"])

            soft = MODULE.write_usage_attestation(
                repo / ".tmp/run-coordinator/usage-soft.json",
                repo=repo,
                chain_id="chain-1",
                invocation_id="invocation-1",
                baseline_path=baseline,
                gate={
                    "status": "pass",
                    "checkedAtUtc": "2026-07-24T15:00:00+00:00",
                    "lowestRemainingPercent": 80,
                    "runBudget": {"softTargetReached": True},
                },
                config=config,
            )
            self.assertFalse(soft["stop_requested"])
            self.assertTrue(soft["soft_closeout_recommended"])
            self.assertEqual(
                soft["new_substantive_unit_policy"],
                "one-high-value-bounded-unit-after-recheck",
            )

    def test_terminal_failure_projects_and_preserves_prior_action_items(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            config = json.loads(
                (ROOT / ".github/run-coordinator-bot.json").read_text()
            )
            config["manifest"]["localFallback"] = ".tmp/run-chain.json"
            control_path = repo / ".tmp/run-coordinator/control.json"
            control = {}
            with mock.patch.object(
                MODULE,
                "command",
                return_value=MODULE.subprocess.CompletedProcess(
                    [], 0, stdout="", stderr=""
                ),
            ):
                MODULE.record_terminal_failure(
                    config,
                    control,
                    repo,
                    stage="chain-manifest",
                    message="manifest unavailable",
                    exit_code=1,
                    next_action="Retry from a current manifest.",
                    chain_id="host-dispatch-1",
                    control_path=control_path,
                )
                MODULE.record_terminal_failure(
                    config,
                    control,
                    repo,
                    stage="usage-gate",
                    message="usage unavailable",
                    exit_code=5,
                    next_action="Restore an official usage reading.",
                    chain_id="chain-2",
                    control_path=control_path,
                )
            self.assertEqual(len(control["action_items"]), 2)
            self.assertEqual(
                {item["chain_id"] for item in control["action_items"]},
                {"host-dispatch-1", "chain-2"},
            )
            projected = json.loads(
                (repo / ".tmp/run-chain.json").read_text(encoding="utf-8")
            )
            self.assertEqual(projected["chain_id"], "chain-2")
            self.assertEqual(projected["status"], "failed")
            persisted_control = json.loads(control_path.read_text(encoding="utf-8"))
            self.assertEqual(len(persisted_control["action_items"]), 2)

    def test_control_merge_preserves_concurrent_user_updates_and_resolutions(self):
        proposed = {
            "schema_version": 1,
            "overrides": {"unit-old": {"source": "user-local-console"}},
            "requests": [{"request_id": "request-old"}],
            "requested_run": {"request_id": "request-old"},
            "action_items": [
                {
                    "id": "automation-failure-one",
                    "resolved": False,
                    "stage": "integrity",
                }
            ],
            "last_successful_chain_id": "chain-one",
        }
        latest = {
            "schema_version": 1,
            "overrides": {
                "unit-new": {
                    "source": "user-local-console",
                    "priority": "high",
                }
            },
            "requests": [
                {"request_id": "request-old"},
                {"request_id": "request-new"},
            ],
            "requested_run": {"request_id": "request-new"},
            "action_items": [
                {
                    "id": "automation-failure-one",
                    "resolved": True,
                    "resolution_reason": "Human reviewed it.",
                }
            ],
        }
        merged = MODULE.merge_control_states(
            latest,
            proposed,
            consumed_requests={"requested_run": "request-old"},
        )
        self.assertEqual(set(merged["overrides"]), {"unit-new"})
        self.assertEqual(
            merged["requested_run"]["request_id"],
            "request-new",
        )
        self.assertEqual(
            {row["request_id"] for row in merged["requests"]},
            {"request-old", "request-new"},
        )
        self.assertTrue(merged["action_items"][0]["resolved"])
        self.assertEqual(
            merged["action_items"][0]["stage"],
            "integrity",
        )

    def test_post_selection_override_change_forces_fresh_evaluation(self):
        original = {
            "unit-one": {
                "source": "user-local-console",
                "priority": "normal",
            }
        }
        payload = {
            "work_queue": {
                "user_overrides": {
                    "request_sha256": MODULE.canonical_json_hash(original)
                }
            }
        }
        self.assertTrue(
            MODULE.control_overrides_match_selection(
                {"overrides": original},
                payload,
            )
        )
        changed = {
            "unit-one": {
                "source": "user-local-console",
                "suppressed": True,
                "reason": "Pause this unit.",
            }
        }
        self.assertFalse(
            MODULE.control_overrides_match_selection(
                {"overrides": changed},
                payload,
            )
        )

    def test_synthetic_failure_projection_never_inherits_prior_chain_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            config = json.loads(
                (ROOT / ".github/run-coordinator-bot.json").read_text()
            )
            fallback = repo / config["manifest"]["localFallback"]
            fallback.parent.mkdir(parents=True)
            fallback.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "chain_id": "old-chain",
                        "stages": [{"id": "old-stage", "status": "succeeded"}],
                        "work_queue": {"selected_work_item_id": "old-unit"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            control = {}
            with mock.patch.object(
                MODULE,
                "command",
                return_value=MODULE.subprocess.CompletedProcess(
                    [], 0, stdout="", stderr=""
                ),
            ):
                MODULE.record_terminal_failure(
                    config,
                    control,
                    repo,
                    stage="host-repository-preflight",
                    message="Runtime drift.",
                    exit_code=1,
                    next_action="Restore the reviewed runtime.",
                    chain_id="host-dispatch-new",
                )
            projection = json.loads(fallback.read_text(encoding="utf-8"))
            self.assertEqual(projection["chain_id"], "host-dispatch-new")
            self.assertEqual(projection["stages"], [])
            self.assertIsNone(projection["work_queue"])
            self.assertNotIn("old-stage", json.dumps(projection))

    def test_host_outcome_history_is_bounded_and_contains_no_freeform_details(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            config = {
                "manifest": {"historyLimit": 2},
            }
            for index in range(3):
                MODULE.append_host_outcome_history(
                    config,
                    repo,
                    chain_id=f"chain-{index}",
                    status="completed",
                    stage="elim-closeout",
                    exit_code=0,
                    payload=self.selected_manifest(),
                )
            value = json.loads(
                (repo / MODULE.HOST_OUTCOME_HISTORY).read_text(encoding="utf-8")
            )
            self.assertEqual(
                [item["chain_id"] for item in value["items"]],
                ["chain-1", "chain-2"],
            )
            allowed = {
                "recorded_at",
                "chain_id",
                "status",
                "stage",
                "exit_code",
                "work_item_id",
                "elim_launch_recommended",
                "usage_status",
                "action_required",
            }
            self.assertTrue(
                all(set(item) == allowed for item in value["items"])
            )

    def test_validated_recovery_is_bound_and_persisted_for_next_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            path = repo / MODULE.ELIM_RECOVERY_STATE
            manifest = self.selected_manifest()
            manifest["final_revision"] = "d" * 40
            manifest["work_queue"]["next_item"]["source_revision"] = "sha256:abc"
            result = self.elim_result()
            result.update(
                {
                    "outcome": "usage_stopped",
                    "continuation": {
                        "state": "retryable",
                        "next_action": "Resume the exact selected unit.",
                    },
                }
            )
            MODULE.persist_validated_recovery(repo, path, manifest, result)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["items"][0]["work_id"], "unit-1")
            self.assertEqual(saved["items"][0]["state"], "retryable")
            self.assertEqual(
                saved["items"][0]["source_revision"],
                "sha256:abc",
            )
            changed = {**result, "unit_id": "other-unit"}
            with self.assertRaisesRegex(MODULE.ContextError, "work-unit ID"):
                MODULE.persist_validated_recovery(
                    repo,
                    path,
                    manifest,
                    changed,
                )

    def test_permanent_checkout_keeps_git_metadata_inside_sandbox_and_advances_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            checkout = repo / ".tmp/run-coordinator/elim-checkout"
            (checkout / ".git").mkdir(parents=True)
            config = json.loads(
                (ROOT / ".github/run-coordinator-bot.json").read_text()
            )
            current = "a" * 40
            remote = "b" * 40
            origin = "https://github.com/Thorncrag/ARRP.git"
            responses = [
                MODULE.subprocess.CompletedProcess([], 0, stdout=origin + "\n", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout=origin + "\n", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout=current + "\n", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout=remote + "\n", stderr=""),
            ]
            with (
                mock.patch.object(MODULE, "require_clean_repo"),
                mock.patch.object(MODULE, "command", side_effect=responses) as command,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "prior unsynchronized baseline",
                ):
                    MODULE.prepare_elim_checkout(
                        "/usr/bin/git",
                        repo,
                        config,
                    )
            self.assertFalse(
                any(call.args[0][1:3] == ["switch", "--detach"] for call in command.mock_calls)
            )

            responses = [
                MODULE.subprocess.CompletedProcess([], 0, stdout=origin + "\n", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout=origin + "\n", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout=current + "\n", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout=remote + "\n", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout=remote + "\n", stderr=""),
            ]
            with (
                mock.patch.object(MODULE, "require_clean_repo"),
                mock.patch.object(MODULE, "command", side_effect=responses) as command,
            ):
                prepared = MODULE.prepare_elim_checkout(
                    "/usr/bin/git",
                    repo,
                    config,
                    safe_prior_head=current,
                )
            self.assertEqual(prepared.resolve(), checkout.resolve())
            self.assertTrue((prepared / ".git").is_dir())
            self.assertTrue(
                any(call.args[0][1:3] == ["switch", "--detach"] for call in command.mock_calls)
            )
            launch_source = Path(MODULE.__file__).read_text(encoding="utf-8")
            self.assertIn("cwd=execution_repo", launch_source)
            self.assertIn("str(execution_repo)", launch_source)

    def test_reconciled_dirty_checkout_is_archived_only_after_canonical_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "remote.git"
            repo = root / "canonical"

            def git(cwd: Path, *args: str) -> str:
                completed = MODULE.subprocess.run(
                    ["/usr/bin/git", *args],
                    cwd=cwd,
                    text=True,
                    stdout=MODULE.subprocess.PIPE,
                    stderr=MODULE.subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(
                    completed.returncode,
                    0,
                    msg=f"git {' '.join(args)} failed: {completed.stderr}",
                )
                return completed.stdout.strip()

            remote.mkdir()
            git(remote, "init", "--bare")
            repo.mkdir()
            git(repo, "init", "-b", "main")
            (repo / "framework/logs").mkdir(parents=True)
            (repo / "framework/logs/ELIM_RUN_LOG.md").write_text(
                "# Elim Run Log\n\n## Runs\n",
                encoding="utf-8",
            )
            git(repo, "add", "framework/logs/ELIM_RUN_LOG.md")
            git(
                repo,
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-m",
                "baseline",
            )
            git(repo, "remote", "add", "origin", str(remote))
            git(repo, "push", "-u", "origin", "main")
            checkout = repo / ".tmp/run-coordinator/elim-checkout"
            checkout.parent.mkdir(parents=True)
            git(repo, "clone", str(remote), str(checkout))
            git(checkout, "switch", "main")

            chain_id = "arrp-20260725T063006Z"
            self.write_elim_run_log(
                repo,
                run_id=chain_id,
                outcome="Failed before substantive work",
            )
            git(repo, "add", "framework/logs/ELIM_RUN_LOG.md")
            git(
                repo,
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-m",
                "account failed run",
            )
            git(repo, "push", "origin", "main")
            (checkout / "framework/logs/CURRENT_AUDIT.md").write_text(
                "Preserved interrupted checkpoint.\n",
                encoding="utf-8",
            )
            reconciliation = (
                repo / MODULE.ELIM_RUN_LOG_RECONCILIATION_STATE
            )
            reconciliation.write_text(
                json.dumps({"schema_version": 1, "items": []}) + "\n",
                encoding="utf-8",
            )
            config = json.loads(
                (ROOT / ".github/run-coordinator-bot.json").read_text()
            )
            control = {
                "action_items": [
                    {
                        "id": "automation-failure-1",
                        "chain_id": chain_id,
                        "resolved": True,
                    }
                ],
                "elim_thread_id": "019f9850-ceef-74f0-8cc4-2457f5322706",
                "elim_thread_checkout": ".tmp/run-coordinator/elim-checkout",
            }

            with mock.patch.object(
                MODULE,
                "APPROVED_ORIGIN_URLS",
                frozenset({str(remote)}),
            ):
                unresolved = {
                    **control,
                    "action_items": [
                        {
                            "id": "automation-failure-1",
                            "chain_id": chain_id,
                            "resolved": False,
                        }
                    ],
                }
                with self.assertRaisesRegex(
                    MODULE.ContextError,
                    "matching resolved Action Item",
                ):
                    MODULE.archive_reconciled_elim_checkout(
                        "/usr/bin/git",
                        repo,
                        config,
                        unresolved,
                        chain_id=chain_id,
                    )
                self.assertTrue(checkout.exists())
                record = MODULE.archive_reconciled_elim_checkout(
                    "/usr/bin/git",
                    repo,
                    config,
                    control,
                    chain_id=chain_id,
                )

            archived = repo / record["archive_path"]
            self.assertFalse(checkout.exists())
            self.assertTrue((archived / ".git").is_dir())
            self.assertTrue(
                (archived / ".arrp-reconciled-checkout.json").is_file()
            )
            self.assertEqual(
                record["changed_paths"],
                ["framework/logs/CURRENT_AUDIT.md"],
            )
            self.assertEqual(
                control["checkout_archive_history"][0]["chain_id"],
                chain_id,
            )
            self.assertNotIn("elim_thread_id", control)
            self.assertNotIn("elim_thread_checkout", control)

    def test_trusted_host_preserves_declared_usage_stop_with_real_git(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "remote.git"
            repo = root / "checkout"

            def git(cwd: Path, *args: str) -> str:
                completed = MODULE.subprocess.run(
                    ["/usr/bin/git", *args],
                    cwd=cwd,
                    text=True,
                    stdout=MODULE.subprocess.PIPE,
                    stderr=MODULE.subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(
                    completed.returncode,
                    0,
                    msg=f"git {' '.join(args)} failed: {completed.stderr}",
                )
                return completed.stdout.strip()

            remote.mkdir()
            git(remote, "init", "--bare")
            repo.mkdir()
            git(repo, "init", "-b", "main")
            (repo / ".gitignore").write_text(".tmp/\n", encoding="utf-8")
            self.write_current_audit(repo, state="Inactive")
            logs = repo / "framework/logs"
            (logs / "ELIM_RUN_LOG.md").write_text(
                "# Elim Run Log\n\n## Runs\n",
                encoding="utf-8",
            )
            git(repo, "add", ".gitignore", "framework/logs/CURRENT_AUDIT.md", "framework/logs/ELIM_RUN_LOG.md")
            git(
                repo,
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-m",
                "baseline",
            )
            git(repo, "remote", "add", "origin", str(remote))
            git(repo, "push", "-u", "origin", "main")
            baseline = git(repo, "rev-parse", "HEAD")

            next_action = "Resume the exact selected unit on a fresh chain."
            self.write_current_audit(
                repo,
                state="Paused",
                next_step=next_action,
                blocker="The usage boundary requested safe closeout.",
            )
            self.write_elim_run_log(
                repo,
                outcome="Usage stopped before substantive work",
            )
            result = self.elim_result(
                outcome="usage_stopped",
                continuation_state="retryable",
                next_action=next_action,
            )
            result["commit"] = None
            result["synchronization"] = []
            result["files_touched"] = [
                "framework/logs/CURRENT_AUDIT.md",
                "framework/logs/ELIM_RUN_LOG.md",
            ]
            result_path = repo / ".tmp/result.json"
            result_path.parent.mkdir(parents=True)
            result_path.write_text(json.dumps(result) + "\n", encoding="utf-8")
            manifest = self.selected_manifest()
            manifest["final_revision"] = baseline

            with mock.patch.object(
                MODULE,
                "APPROVED_ORIGIN_URLS",
                frozenset({str(remote)}),
            ):
                preserved = MODULE.host_preserve_elim_result(
                    git="/usr/bin/git",
                    gh=MODULE.EXECUTABLES["githubCliPath"],
                    repo=repo,
                    result_path=result_path,
                    expected_manifest=manifest,
                    repository="Thorncrag/ARRP",
                )

            self.assertRegex(preserved["commit"], r"^[0-9a-f]{40}$")
            self.assertNotEqual(preserved["commit"], baseline)
            self.assertEqual(
                git(remote, "rev-parse", "refs/heads/main"),
                preserved["commit"],
            )
            self.assertEqual(git(repo, "status", "--porcelain"), "")
            self.assertTrue(
                (repo / ".tmp/result-model-result.json").is_file()
            )
            stored = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(stored["commit"], preserved["commit"])
            self.assertTrue(
                any(
                    row["check"] == "Trusted-host Git closeout"
                    and row["status"] == "passed"
                    for row in stored["validation"]
                )
            )

    def test_trusted_host_rejects_an_undeclared_working_tree_path(self):
        result = self.elim_result(
            outcome="usage_stopped",
            continuation_state="retryable",
            next_action="Resume the selected unit.",
        )
        result["commit"] = None
        result["synchronization"] = []
        result["files_touched"] = [
            "framework/logs/CURRENT_AUDIT.md",
            "framework/logs/ELIM_RUN_LOG.md",
        ]
        with (
            tempfile.TemporaryDirectory() as directory,
            mock.patch.object(
                MODULE,
                "worktree_changed_paths",
                return_value={
                    *result["files_touched"],
                    "areas/OVS/issues/OVS-001.md",
                },
            ),
        ):
            with self.assertRaisesRegex(MODULE.ContextError, "unreported="):
                MODULE.verify_uncommitted_elim_evidence(
                    "/usr/bin/git",
                    Path(directory),
                    result,
                    expected_manifest=self.selected_manifest(),
                )


if __name__ == "__main__":
    unittest.main()
