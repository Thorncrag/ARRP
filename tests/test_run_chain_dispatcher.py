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
    def test_exact_head_recommendation_parser_is_runtime_attested(self):
        self.assertIn(
            "scripts/source_monitor_recommendations.py",
            MODULE.AUTOMATION_RUNTIME_PATHS,
        )

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
        path = repo / "framework/records/handoffs/current-task.md"
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
            "files_touched": ["framework/records/automation/elim-run-log.md"],
            "source_ids": [],
            "validation": [],
            "commit": "a" * 40,
            "synchronization": ["Synchronized and read back origin/main."],
            "human_questions": human_questions or [],
            "continuation": {
                "state": continuation_state,
                "next_action": next_action,
            },
            "discovered_work_units": [],
            "gap_obligation_updates": [],
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
        logs = repo / "framework/records/automation"
        logs.mkdir(parents=True, exist_ok=True)
        (logs / "elim-run-log.md").write_text(
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
            "| Discovery and gap obligations | None. |\n"
            + (
                "| Material units | [Shared entry](agent-audit-log.md#entry) |\n"
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
            (logs / "agent-audit-log.md").write_text(
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
        for field in MODULE.ELIM_RUN_REPORT_FIELD_ORDER:
            self.assertIn(field, prompt)
        self.assertIn("synonyms and aliases do not satisfy", prompt)

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

    def test_prompt_exposes_governance_discovery_and_full_gap_documentation_floor(self):
        payload = {
            "chain_id": "chain-1",
            "elim_decision": {
                "profile": {
                    "full_context": False,
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "xhigh",
                }
            },
            "usage": {"host_monitor": {}},
            "context_packet": {
                "local_path": ".tmp/run-coordinator/chain-1/context.json",
                "issue_id": None,
                "canonical_record": None,
            },
            "work_queue": {
                "selected_work_item_id": "governance-review",
                "next_item": {
                    "id": "governance-review",
                    "kind": "integrity",
                    "source": {
                        "finding_type": "project_governance_review_and_discovery"
                    },
                },
            },
        }
        prompt = MODULE.elim_prompt(Path("/tmp/run-chain.json"), payload)
        self.assertIn("Project governance review and discovery mode", prompt)
        self.assertIn("minimum coverage, not an exhaustive whitelist", prompt)
        self.assertIn("no_material_finding", prompt)
        self.assertIn("forbidden/unsafe/out-of-scope/uncertain", prompt)
        self.assertIn("nested discovered_work_units", prompt)
        self.assertIn("Outside contributions require", prompt)
        self.assertIn("render-discovery-markers", prompt)

    def test_config_uses_explicit_host_paths_and_conservative_profiles(self):
        config = json.loads(
            (ROOT / ".github" / "run-coordinator-bot.json").read_text()
        )
        for key in (
            "pythonPath",
            "gitPath",
            "xattrPath",
            "githubCliPath",
            "codexPath",
        ):
            self.assertTrue(Path(config["hostDispatcher"][key]).is_absolute())
        profiles = config["llmRouting"]["profiles"]
        self.assertEqual(profiles["read-heavy-triage"]["model"], "gpt-5.6-terra")
        self.assertEqual(profiles["substantive"]["model"], "gpt-5.6-sol")
        self.assertTrue(profiles["comprehensive"]["fullContext"])
        self.assertEqual(config["usage"]["monitorIntervalSeconds"], 60)
        self.assertEqual(config["usage"]["snapshotMaxAgeSeconds"], 120)
        self.assertEqual(config["hostDispatcher"]["staleLockSeconds"], 900)
        self.assertEqual(
            config["hostDispatcher"]["repositoryPath"],
            "/Users/benjaminsmith/Automation Workspaces/ARRP",
        )
        self.assertEqual(config["gapStewardship"], MODULE.GAP_STEWARDSHIP_POLICY)
        self.assertEqual(
            config["governanceDiscovery"]["ordinarySelectionPolicy"],
            "after-ordinary-queue-clears",
        )
        self.assertEqual(config["governanceDiscovery"]["minimumIntervalHours"], 168)
        self.assertEqual(
            config["hostDispatcher"]["isolatedCheckoutPath"],
            ".tmp/run-coordinator/elim-checkout",
        )
        self.assertEqual(
            config["hostDispatcher"]["repositoryCloseout"],
            MODULE.HOST_CLOSEOUT_POLICY,
        )
        self.assertEqual(
            config["hostDispatcher"]["canonicalWorkspaceReconciliation"],
            MODULE.CANONICAL_WORKSPACE_RECONCILIATION_POLICY,
        )
        self.assertEqual(
            config["automationHealthProjection"],
            MODULE.AUTOMATION_HEALTH_PROJECTION_POLICY,
        )
        for relative in (
            ".github/launchd/com.thorncrag.arrp-run-coordinator.plist.example",
            ".github/launchd/com.thorncrag.arrp-run-coordinator-control.plist.example",
        ):
            body = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("/Users/benjaminsmith/Automation Workspaces/ARRP", body)
            self.assertNotIn("/Users/benjaminsmith/Documents/ARRP", body)

    def test_file_provider_workspace_is_rejected_before_git_preflight(self):
        repo = Path("/Users/test/Documents/ARRP")

        def domain(path):
            return "domain-id" if path == repo.parent else None

        with mock.patch.object(
            MODULE,
            "read_file_provider_domain",
            side_effect=domain,
        ):
            self.assertEqual(
                MODULE.file_provider_managed_ancestor(repo),
                repo.parent,
            )
        with (
            mock.patch.object(
                MODULE,
                "file_provider_managed_ancestor",
                return_value=repo.parent,
            ),
            mock.patch.object(MODULE, "command") as command_mock,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "inside a macOS File Provider domain",
            ):
                MODULE.verify_canonical_runtime_boundary(
                    "/usr/bin/git",
                    repo,
                )
        command_mock.assert_not_called()

    def test_git_metadata_hygiene_detects_finder_style_duplicate_refs_and_indexes(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            refs = repo / ".git/refs/heads"
            refs.mkdir(parents=True)
            (repo / ".git/index").write_bytes(b"canonical")
            (repo / ".git/index 2").write_bytes(b"duplicate")
            (refs / "main").write_text("a" * 40 + "\n", encoding="utf-8")
            (refs / "main 2").write_text("b" * 40 + "\n", encoding="utf-8")
            (repo / ".git/refs/.DS_Store").write_bytes(b"finder")
            self.assertEqual(
                MODULE.git_metadata_foreign_artifacts(repo),
                [
                    ".git/index 2",
                    ".git/refs/.DS_Store",
                    ".git/refs/heads/main 2",
                ],
            )
            self.assertEqual(
                MODULE.automation_incident_kind(
                    "could not refresh origin/main: fatal: bad object "
                    "refs/heads/main 2"
                ),
                "canonical-git-metadata-foreign-artifact",
            )
            self.assertEqual(
                MODULE.automation_incident_kind(
                    "numbered canonical-workspace copies repeatedly regenerated"
                ),
                "canonical-workspace-conflict-copy",
            )

    def test_runtime_preflight_quarantines_allowlisted_foreign_git_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "origin.git"
            repo = root / "repo"

            def run(arguments, *, cwd):
                return MODULE.subprocess.run(
                    ["/usr/bin/git", *arguments],
                    cwd=cwd,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            run(["init", "--bare", str(remote)], cwd=root)
            repo.mkdir()
            run(["init", "-b", "main"], cwd=repo)
            for relative in MODULE.AUTOMATION_RUNTIME_PATHS:
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative + "\n", encoding="utf-8")
            canonical_data = repo / "research/horizon-review-console/data/overview.js"
            canonical_data.parent.mkdir(parents=True, exist_ok=True)
            canonical_data.write_text("canonical\n", encoding="utf-8")
            (repo / ".gitignore").write_text(
                ".tmp/\n",
                encoding="utf-8",
            )
            run(["add", "-A"], cwd=repo)
            run(
                [
                    "-c",
                    "user.name=Test User",
                    "-c",
                    "user.email=test@example.com",
                    "commit",
                    "-m",
                    "Baseline",
                ],
                cwd=repo,
            )
            run(["remote", "add", "origin", str(remote)], cwd=repo)
            run(["push", "-u", "origin", "main"], cwd=repo)
            revision = run(["rev-parse", "HEAD"], cwd=repo).stdout.strip()
            untracked_copy = canonical_data.with_name("overview 2.js")
            staged_copy = canonical_data.with_name("overview 3.js")
            untracked_copy.write_text("untracked conflict\n", encoding="utf-8")
            staged_copy.write_text("staged conflict\n", encoding="utf-8")
            run(["add", str(staged_copy.relative_to(repo))], cwd=repo)
            (repo / ".git/index 2").write_bytes(b"foreign index")
            (repo / ".git/refs/.DS_Store").write_bytes(b"finder metadata")
            (repo / ".git/refs/heads/main 2").write_text(
                revision + "\n",
                encoding="utf-8",
            )
            control = {}

            with mock.patch.object(
                MODULE,
                "APPROVED_ORIGIN_URLS",
                frozenset({str(remote)}),
            ):
                resolved, workspace_commit = (
                    MODULE.verify_canonical_runtime_boundary(
                        "/usr/bin/git",
                        repo,
                        control=control,
                    )
                )

            self.assertEqual((resolved, workspace_commit), (revision, None))
            self.assertEqual(
                MODULE.git_metadata_foreign_artifacts(repo),
                [],
            )
            history = control["git_metadata_quarantine_history"]
            self.assertEqual(len(history), 1)
            self.assertEqual(
                {
                    row["original_path"]
                    for row in history[0]["entries"]
                },
                {
                    ".git/index 2",
                    ".git/refs/.DS_Store",
                    ".git/refs/heads/main 2",
                },
            )
            archive = repo / history[0]["archive_path"]
            self.assertTrue(
                (archive / "quarantine-record.json").is_file()
            )
            self.assertTrue((archive / ".git/index 2").is_file())
            workspace_history = control[
                "workspace_conflict_quarantine_history"
            ]
            self.assertEqual(len(workspace_history), 1)
            self.assertEqual(
                {
                    row["original_path"]
                    for row in workspace_history[0]["entries"]
                },
                {
                    "research/horizon-review-console/data/overview 2.js",
                    "research/horizon-review-console/data/overview 3.js",
                },
            )
            self.assertEqual(
                {
                    row["canonical_path"]
                    for row in workspace_history[0]["entries"]
                },
                {
                    "research/horizon-review-console/data/overview.js",
                },
            )
            workspace_archive = (
                repo / workspace_history[0]["archive_path"]
            )
            self.assertTrue(
                (
                    workspace_archive
                    / "research/horizon-review-console/data/overview 2.js"
                ).is_file()
            )
            self.assertEqual(
                run(["status", "--porcelain"], cwd=repo).stdout,
                "",
            )
            ambiguous_copy = repo / "untracked note 2.md"
            ambiguous_copy.write_text("ambiguous\n", encoding="utf-8")
            with self.assertRaisesRegex(
                RuntimeError,
                "lack an exact tracked file sibling",
            ):
                MODULE.project_workspace_conflict_copy_artifacts(
                    "/usr/bin/git",
                    repo,
                )
            ambiguous_copy.unlink()

    def test_host_closeout_policy_rejects_runtime_drift(self):
        config = {
            "gapStewardship": dict(MODULE.GAP_STEWARDSHIP_POLICY),
            "hostStatusProjection": dict(
                MODULE.HOST_STATUS_PROJECTION_POLICY
            ),
            "automationHealthProjection": dict(
                MODULE.AUTOMATION_HEALTH_PROJECTION_POLICY
            ),
            "governanceDiscovery": {
                "enabled": True,
                "mode": "Project governance review and discovery",
                "ordinarySelectionPolicy": "after-ordinary-queue-clears",
                "minimumIntervalHours": 168,
            },
            "hostDispatcher": {
                "repositoryCloseout": dict(MODULE.HOST_CLOSEOUT_POLICY),
                "canonicalWorkspaceReconciliation": dict(
                    MODULE.CANONICAL_WORKSPACE_RECONCILIATION_POLICY
                ),
            }
        }
        MODULE.validate_host_closeout_policy(config)
        config["hostDispatcher"]["repositoryCloseout"]["modelGitMutation"] = (
            "allowed"
        )
        with self.assertRaisesRegex(RuntimeError, "trusted-host boundary"):
            MODULE.validate_host_closeout_policy(config)

    def test_workspace_reconciliation_policy_rejects_runtime_drift(self):
        config = {
            "gapStewardship": dict(MODULE.GAP_STEWARDSHIP_POLICY),
            "hostStatusProjection": dict(
                MODULE.HOST_STATUS_PROJECTION_POLICY
            ),
            "automationHealthProjection": dict(
                MODULE.AUTOMATION_HEALTH_PROJECTION_POLICY
            ),
            "governanceDiscovery": {
                "enabled": True,
                "mode": "Project governance review and discovery",
                "ordinarySelectionPolicy": "after-ordinary-queue-clears",
                "minimumIntervalHours": 168,
            },
            "hostDispatcher": {
                "repositoryCloseout": dict(MODULE.HOST_CLOSEOUT_POLICY),
                "canonicalWorkspaceReconciliation": dict(
                    MODULE.CANONICAL_WORKSPACE_RECONCILIATION_POLICY
                ),
            }
        }
        config["hostDispatcher"]["canonicalWorkspaceReconciliation"][
            "divergentHistoryAction"
        ] = "auto-merge"
        with self.assertRaisesRegex(
            RuntimeError,
            "canonical-workspace reconciliation",
        ):
            MODULE.validate_host_closeout_policy(config)

    def test_dispatcher_uses_only_the_reviewed_config_path(self):
        source = (ROOT / "scripts" / "run_chain_dispatcher.py").read_text()
        self.assertNotIn('parser.add_argument("--config"', source)
        self.assertIn("config = read_json(CONFIG)", source)
        self.assertIn('"--recover-stale-lock-only"', source)
        self.assertIn("do not fetch, synchronize, trigger a chain", source)
        self.assertIn("record_bootstrap_failure_best_effort(", source)
        self.assertIn(
            "Committed and synchronized canonical workspace changes as",
            source,
        )

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
                / "project"
                / "automation"
                / "schemas"
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
        self.assertNotIn('"format"', json.dumps(schema))
        self.assertNotIn('"oneOf"', json.dumps(schema))
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
            repeated = {
                **manifest,
                "chain_id": "chain-2",
                "updated_at": "2026-07-24T12:30:00+00:00",
            }
            with mock.patch.object(MODULE, "command"):
                self.assertTrue(MODULE.alert_failures(config, control, repeated, repo))
            self.assertEqual(len(control["action_items"]), 1)
            self.assertEqual(control["action_items"][0]["occurrence_count"], 2)
            self.assertEqual(control["action_items"][0]["last_chain_id"], "chain-2")
            healthy = {
                "chain_id": "chain-3",
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

    def test_runtime_preflight_requires_reconciled_main(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / ".git").mkdir()
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
                MODULE.subprocess.CompletedProcess([], 0, stdout="main\n", stderr=""),
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
                revision, workspace_commit = MODULE.verify_canonical_runtime_boundary(
                    "/usr/bin/git",
                    repo,
                )
            self.assertEqual(revision, "a" * 40)
            self.assertIsNone(workspace_commit)
            argument_vectors = [call.args[0] for call in invoked.mock_calls]
            self.assertIn(
                ["/usr/bin/git", "branch", "--show-current"],
                argument_vectors,
            )
            self.assertIn(
                ["/usr/bin/git", "status", "--porcelain"],
                argument_vectors,
            )
            self.assertFalse(
                any(
                    len(vector) > 1 and vector[1] == "merge"
                    for vector in argument_vectors
                )
            )

    def test_runtime_preflight_fast_forwards_clean_main_after_ancestor_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / ".git").mkdir()
            for relative in MODULE.AUTOMATION_RUNTIME_PATHS:
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative + "\n", encoding="utf-8")
            local = "a" * 40
            remote = "b" * 40
            same_blob = "c" * 40 + "\n"
            responses = [
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout="https://github.com/Thorncrag/ARRP.git\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout=remote + "\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="main\n", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout=local + "\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout=remote + "\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
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
                revision, workspace_commit = MODULE.verify_canonical_runtime_boundary(
                    "/usr/bin/git",
                    repo,
                )
            self.assertEqual((revision, workspace_commit), (remote, None))
            argument_vectors = [call.args[0] for call in invoked.mock_calls]
            self.assertIn(
                [
                    "/usr/bin/git",
                    "merge-base",
                    "--is-ancestor",
                    local,
                    remote,
                ],
                argument_vectors,
            )
            self.assertIn(
                ["/usr/bin/git", "merge", "--ff-only", remote],
                argument_vectors,
            )

    def test_runtime_preflight_does_not_fast_forward_dirty_main(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / ".git").mkdir()
            local = "a" * 40
            remote = "b" * 40
            responses = [
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout="https://github.com/Thorncrag/ARRP.git\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout=remote + "\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="main\n", stderr=""),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout=" M README.md\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout=local + "\n", stderr=""
                ),
            ]
            with mock.patch.object(
                MODULE,
                "command",
                side_effect=responses,
            ) as invoked:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "working tree is not clean",
                ):
                    MODULE.verify_canonical_runtime_boundary(
                        "/usr/bin/git",
                        repo,
                    )
            argument_vectors = [call.args[0] for call in invoked.mock_calls]
            self.assertFalse(
                any(
                    len(vector) > 1 and vector[1] == "merge"
                    for vector in argument_vectors
                )
            )

    def test_runtime_preflight_does_not_fast_forward_divergent_main(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / ".git").mkdir()
            local = "a" * 40
            remote = "b" * 40
            responses = [
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout="https://github.com/Thorncrag/ARRP.git\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout=remote + "\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="main\n", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout=local + "\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 1, stdout="", stderr=""),
            ]
            with mock.patch.object(
                MODULE,
                "command",
                side_effect=responses,
            ) as invoked:
                with self.assertRaisesRegex(
                    RuntimeError,
                    "not an ancestor",
                ):
                    MODULE.verify_canonical_runtime_boundary(
                        "/usr/bin/git",
                        repo,
                    )
            argument_vectors = [call.args[0] for call in invoked.mock_calls]
            self.assertFalse(
                any(
                    len(vector) > 1 and vector[1] == "merge"
                    for vector in argument_vectors
                )
            )

    def test_runtime_preflight_blocks_unreconciled_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / ".git").mkdir()
            responses = [
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout="https://github.com/Thorncrag/ARRP.git\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout="a" * 40 + "\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="codex/in-progress\n", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="a" * 40 + "\n", stderr=""),
            ]
            with mock.patch.object(MODULE, "command", side_effect=responses):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "current branch is codex/in-progress instead of main",
                ):
                    MODULE.verify_canonical_runtime_boundary("/usr/bin/git", repo)

    def test_runtime_preflight_commits_and_pushes_dirty_main(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / ".git").mkdir()
            for relative in MODULE.AUTOMATION_RUNTIME_PATHS:
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative + "\n", encoding="utf-8")
            original = "a" * 40
            committed = "c" * 40
            same_blob = "b" * 40 + "\n"
            responses = [
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout="https://github.com/Thorncrag/ARRP.git\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout=original + "\n", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="main\n", stderr=""),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout=" M areas/FACT/README.md\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout=original + "\n", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout="areas/FACT/README.md\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout=committed + "\n", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
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
            with (
                mock.patch.object(
                    MODULE,
                    "command",
                    side_effect=responses,
                ) as invoked,
                mock.patch.object(
                    MODULE,
                    "publish_checked_pull_request",
                    return_value=(
                        committed,
                        ["Checked pull request merged and read back."],
                        "https://github.com/Thorncrag/ARRP/pull/1",
                    ),
                ) as published,
            ):
                revision, workspace_commit = (
                    MODULE.verify_canonical_runtime_boundary("/usr/bin/git", repo)
                )
            self.assertEqual((revision, workspace_commit), (committed, committed))
            argument_vectors = [call.args[0] for call in invoked.mock_calls]
            self.assertIn(["/usr/bin/git", "add", "-A"], argument_vectors)
            published.assert_called_once()
            self.assertIn(
                [
                    "/usr/bin/git",
                    "merge",
                    "--ff-only",
                    "refs/remotes/origin/main",
                ],
                argument_vectors,
            )
            self.assertTrue(
                any(
                    vector[-2:] == [
                        "-m",
                        MODULE.CANONICAL_WORKSPACE_RECONCILIATION_POLICY[
                            "commitMessage"
                        ],
                    ]
                    for vector in argument_vectors
                )
            )

    def test_runtime_preflight_reconciles_a_real_git_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "origin.git"
            repo = root / "repo"

            def run(arguments, *, cwd):
                return MODULE.subprocess.run(
                    ["/usr/bin/git", *arguments],
                    cwd=cwd,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            run(["init", "--bare", str(remote)], cwd=root)
            repo.mkdir()
            run(["init", "-b", "main"], cwd=repo)
            for relative in MODULE.AUTOMATION_RUNTIME_PATHS:
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative + "\n", encoding="utf-8")
            readme = repo / "README.md"
            readme.write_text("baseline\n", encoding="utf-8")
            run(["add", "-A"], cwd=repo)
            run(
                [
                    "-c",
                    "user.name=Test User",
                    "-c",
                    "user.email=test@example.com",
                    "commit",
                    "-m",
                    "Baseline",
                ],
                cwd=repo,
            )
            run(["remote", "add", "origin", str(remote)], cwd=repo)
            run(["push", "-u", "origin", "main"], cwd=repo)
            original = run(["rev-parse", "HEAD"], cwd=repo).stdout.strip()
            readme.write_text("preserved\n", encoding="utf-8")

            def publish_locally(**kwargs):
                commit = kwargs["commit"]
                run(["push", "origin", f"{commit}:refs/heads/main"], cwd=repo)
                run(["fetch", "--no-tags", "origin", "main"], cwd=repo)
                return (
                    commit,
                    ["Test-only checked publication substitute."],
                    "https://github.com/Thorncrag/ARRP/pull/1",
                )

            with (
                mock.patch.object(
                    MODULE,
                    "APPROVED_ORIGIN_URLS",
                    frozenset({str(remote)}),
                ),
                mock.patch.object(
                    MODULE,
                    "publish_checked_pull_request",
                    side_effect=publish_locally,
                ),
            ):
                revision, workspace_commit = (
                    MODULE.verify_canonical_runtime_boundary("/usr/bin/git", repo)
                )

            self.assertIsNotNone(workspace_commit)
            self.assertNotEqual(revision, original)
            self.assertEqual(revision, workspace_commit)
            self.assertEqual(
                run(["rev-parse", "refs/remotes/origin/main"], cwd=repo)
                .stdout.strip(),
                revision,
            )
            self.assertEqual(
                run(["status", "--porcelain"], cwd=repo).stdout,
                "",
            )
            self.assertIn(
                "Preserve local ARRP changes before automated run",
                run(["log", "-1", "--pretty=%s"], cwd=repo).stdout,
            )

    def test_runtime_preflight_fast_forwards_a_real_clean_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "origin.git"
            repo = root / "repo"
            publisher = root / "publisher"

            def run(arguments, *, cwd):
                return MODULE.subprocess.run(
                    ["/usr/bin/git", *arguments],
                    cwd=cwd,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            run(["init", "--bare", str(remote)], cwd=root)
            repo.mkdir()
            run(["init", "-b", "main"], cwd=repo)
            for relative in MODULE.AUTOMATION_RUNTIME_PATHS:
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative + "\n", encoding="utf-8")
            readme = repo / "README.md"
            readme.write_text("baseline\n", encoding="utf-8")
            run(["add", "-A"], cwd=repo)
            run(
                [
                    "-c",
                    "user.name=Test User",
                    "-c",
                    "user.email=test@example.com",
                    "commit",
                    "-m",
                    "Baseline",
                ],
                cwd=repo,
            )
            run(["remote", "add", "origin", str(remote)], cwd=repo)
            run(["push", "-u", "origin", "main"], cwd=repo)
            baseline = run(["rev-parse", "HEAD"], cwd=repo).stdout.strip()

            run(["clone", "-b", "main", str(remote), str(publisher)], cwd=root)
            (publisher / "README.md").write_text(
                "baseline\nremote update\n",
                encoding="utf-8",
            )
            run(["add", "README.md"], cwd=publisher)
            run(
                [
                    "-c",
                    "user.name=Test Publisher",
                    "-c",
                    "user.email=publisher@example.com",
                    "commit",
                    "-m",
                    "Advance remote",
                ],
                cwd=publisher,
            )
            run(["push", "origin", "main"], cwd=publisher)
            expected = run(["rev-parse", "HEAD"], cwd=publisher).stdout.strip()

            with mock.patch.object(
                MODULE,
                "APPROVED_ORIGIN_URLS",
                frozenset({str(remote)}),
            ):
                revision, workspace_commit = (
                    MODULE.verify_canonical_runtime_boundary(
                        "/usr/bin/git",
                        repo,
                    )
                )

            self.assertNotEqual(baseline, expected)
            self.assertEqual((revision, workspace_commit), (expected, None))
            self.assertEqual(
                run(["rev-parse", "HEAD"], cwd=repo).stdout.strip(),
                expected,
            )
            self.assertEqual(run(["status", "--porcelain"], cwd=repo).stdout, "")

    def test_runtime_preflight_resumes_a_prepared_workspace_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "origin.git"
            repo = root / "repo"

            def run(arguments, *, cwd):
                return MODULE.subprocess.run(
                    ["/usr/bin/git", *arguments],
                    cwd=cwd,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            run(["init", "--bare", str(remote)], cwd=root)
            repo.mkdir()
            run(["init", "-b", "main"], cwd=repo)
            for relative in MODULE.AUTOMATION_RUNTIME_PATHS:
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative + "\n", encoding="utf-8")
            readme = repo / "README.md"
            readme.write_text("baseline\n", encoding="utf-8")
            run(["add", "-A"], cwd=repo)
            run(
                [
                    "-c",
                    "user.name=Test User",
                    "-c",
                    "user.email=test@example.com",
                    "commit",
                    "-m",
                    "Baseline",
                ],
                cwd=repo,
            )
            run(["remote", "add", "origin", str(remote)], cwd=repo)
            run(["push", "-u", "origin", "main"], cwd=repo)
            baseline = run(["rev-parse", "HEAD"], cwd=repo).stdout.strip()
            readme.write_text("preserved\n", encoding="utf-8")

            def publish_locally(**kwargs):
                commit = kwargs["commit"]
                run(["push", "origin", f"{commit}:refs/heads/main"], cwd=repo)
                run(["fetch", "--no-tags", "origin", "main"], cwd=repo)
                return (
                    commit,
                    ["Test-only checked publication substitute."],
                    "https://github.com/Thorncrag/ARRP/pull/1",
                )

            with mock.patch.object(
                MODULE,
                "APPROVED_ORIGIN_URLS",
                frozenset({str(remote)}),
            ):
                with mock.patch.object(
                    MODULE,
                    "publish_checked_pull_request",
                    side_effect=RuntimeError("transient publication failure"),
                ):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "transient publication failure",
                    ):
                        MODULE.verify_canonical_runtime_boundary(
                            "/usr/bin/git",
                            repo,
                        )
                prepared_branch = run(
                    ["branch", "--show-current"],
                    cwd=repo,
                ).stdout.strip()
                prepared_commit = run(
                    ["rev-parse", "HEAD"],
                    cwd=repo,
                ).stdout.strip()
                self.assertRegex(
                    prepared_branch,
                    r"^codex/host-workspace-\d{8}T\d{6}Z-[0-9a-f]{12}$",
                )
                self.assertEqual(
                    run(["rev-parse", f"{prepared_commit}^"], cwd=repo)
                    .stdout.strip(),
                    baseline,
                )
                with mock.patch.object(
                    MODULE,
                    "publish_checked_pull_request",
                    side_effect=publish_locally,
                ):
                    revision, workspace_commit = (
                        MODULE.verify_canonical_runtime_boundary(
                            "/usr/bin/git",
                            repo,
                        )
                    )

            self.assertEqual((revision, workspace_commit), (prepared_commit,) * 2)
            self.assertEqual(
                run(["branch", "--show-current"], cwd=repo).stdout.strip(),
                "main",
            )
            self.assertEqual(run(["status", "--porcelain"], cwd=repo).stdout, "")
            self.assertEqual(
                run(["rev-parse", "refs/remotes/origin/main"], cwd=repo)
                .stdout.strip(),
                prepared_commit,
            )

    def test_runtime_preflight_blocks_automation_file_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / ".git").mkdir()
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
                MODULE.subprocess.CompletedProcess([], 0, stdout="main\n", stderr=""),
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
            path = repo / "framework/records/handoffs/current-task.md"
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
                    repo / "framework/records/handoffs/current-task.md",
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

    def test_source_domain_proposal_binding_requires_exact_head_review(self):
        canonical = "framework/records/sources/source-monitor-log.md"
        manifest = {
            "chain_id": "chain-1",
            "work_queue": {
                "selected_work_item_id": "unit-1",
                "next_item": {
                    "id": "unit-1",
                    "kind": "integrity",
                    "source": {
                        "finding_type": "source_domain_proposal",
                        "canonicalRecord": canonical,
                        "canonical_record": canonical,
                        "pending_proposal": {
                            "proposal": {"proposal_revision": "d" * 40}
                        },
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
                "work_type": "integrity",
                "issue_id": None,
                "canonical_record": canonical,
            }
        )
        with self.assertRaisesRegex(
            MODULE.ContextError,
            "outside-contribution review",
        ):
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
                "framework/records/automation/agent-audit-log.md",
                "framework/records/automation/elim-run-log.md",
            ]
            result["synchronization"] = ["Merged pull request to origin/main."]
            def completed(argv, **_kwargs):
                if argv[1] == "diff":
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout=(
                            "areas/TEST/issues/TEST-001.md\n"
                            "framework/records/automation/agent-audit-log.md\n"
                            "framework/records/automation/elim-run-log.md\n"
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
                        "framework/records/automation/agent-audit-log.md",
                        "framework/records/automation/elim-run-log.md",
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
                            "framework/records/automation/agent-audit-log.md\n"
                            "framework/records/automation/elim-run-log.md\n"
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
                        "framework/records/automation/agent-audit-log.md",
                        "framework/records/automation/elim-run-log.md",
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

    def test_historical_closeout_revalidates_exact_pr_checks_tree_and_parent(self):
        commit = "a" * 40
        baseline = "b" * 40
        current = "c" * 40
        pr_head = "d" * 40
        tree = "e" * 40
        intermediate = "9" * 40
        pull_request = "https://github.com/Thorncrag/ARRP/pull/999"
        result = self.elim_result()
        result["commit"] = commit
        result["synchronization"] = [
            f"Trusted host read back exact commit {pr_head}.",
            f"Trusted host used pull request {pull_request}.",
            "Trusted host required every reported check to finish.",
            f"Trusted host read back exact origin/main boundary {commit}.",
        ]
        manifest = self.selected_manifest()
        manifest["baseline_commit"] = baseline

        def run_command(argv, **_kwargs):
            if argv[1] == "cat-file":
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="", stderr=""
                )
            if argv[1] == "fetch":
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="", stderr=""
                )
            if argv[1:3] == ["rev-parse", "HEAD"]:
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout=intermediate + "\n", stderr=""
                )
            if argv[1:3] == [
                "rev-parse",
                "refs/remotes/origin/main",
            ]:
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout=current + "\n", stderr=""
                )
            if argv[1] == "merge-base":
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="", stderr=""
                )
            if argv[1:3] == ["rev-parse", f"{commit}^{{tree}}"]:
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout=tree + "\n", stderr=""
                )
            if argv[1:3] == ["rev-parse", f"{pr_head}^{{tree}}"]:
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout=tree + "\n", stderr=""
                )
            if argv[1] == "rev-list":
                return MODULE.subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout=f"{commit} {baseline}\n",
                    stderr="",
                )
            if argv[1] == "diff":
                return MODULE.subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout=MODULE.ELIM_RUN_LOG + "\n",
                    stderr="",
                )
            self.fail(f"unexpected command: {argv}")

        def divergent_checkout(argv, **kwargs):
            if argv[1:] == [
                "merge-base",
                "--is-ancestor",
                commit,
                intermediate,
            ]:
                return MODULE.subprocess.CompletedProcess(
                    argv, 1, stdout="", stderr=""
                )
            return run_command(argv, **kwargs)

        pr = {
            "state": "MERGED",
            "baseRefName": "main",
            "baseRefOid": baseline,
            "headRefOid": pr_head,
            "mergeCommit": {"oid": commit},
            "url": pull_request,
        }
        with (
            mock.patch.object(MODULE, "command", side_effect=run_command),
            mock.patch.object(
                MODULE,
                "read_closeout_pull_request",
                return_value=pr,
            ),
            mock.patch.object(
                MODULE,
                "wait_for_closeout_checks",
                return_value=[{"name": "CodeQL", "bucket": "pass"}],
            ) as checks,
        ):
            reviewed, comparison = MODULE.verify_commit_and_synchronization(
                "/usr/bin/git",
                "/opt/homebrew/bin/gh",
                Path("/tmp"),
                result,
                baseline_commit=baseline,
            )
        self.assertEqual(reviewed, {MODULE.ELIM_RUN_LOG})
        self.assertEqual(comparison, baseline)
        checks.assert_called_once_with(
            "/opt/homebrew/bin/gh",
            Path("/tmp"),
            repository="Thorncrag/ARRP",
            pull_request=pull_request,
        )
        with (
            mock.patch.object(MODULE, "command", side_effect=run_command),
            mock.patch.object(
                MODULE,
                "read_closeout_pull_request",
                return_value={**pr, "baseRefOid": "f" * 40},
            ),
            mock.patch.object(MODULE, "wait_for_closeout_checks"),
        ):
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "differs from its exact pinned closeout boundary",
            ):
                MODULE.verify_commit_and_synchronization(
                    "/usr/bin/git",
                    "/opt/homebrew/bin/gh",
                    Path("/tmp"),
                    result,
                    baseline_commit=baseline,
                )
        with (
            mock.patch.object(
                MODULE,
                "command",
                side_effect=divergent_checkout,
            ),
            mock.patch.object(MODULE, "read_closeout_pull_request"),
            mock.patch.object(MODULE, "wait_for_closeout_checks"),
        ):
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "not on the verified Elim result-to-current",
            ):
                MODULE.verify_commit_and_synchronization(
                    "/usr/bin/git",
                    "/opt/homebrew/bin/gh",
                    Path("/tmp"),
                    result,
                    baseline_commit=baseline,
                )

    def test_verified_historical_checkout_advances_to_current_origin(self):
        result_commit = "a" * 40
        current = "c" * 40

        def run_command(argv, **_kwargs):
            if argv[1:3] == [
                "rev-parse",
                "refs/remotes/origin/main",
            ]:
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout=current + "\n", stderr=""
                )
            if argv[1] == "merge-base":
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="", stderr=""
                )
            if argv[1:3] == ["switch", "--detach"]:
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="", stderr=""
                )
            if argv[1:3] == ["rev-parse", "HEAD"]:
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout=current + "\n", stderr=""
                )
            self.fail(f"unexpected command: {argv}")

        with (
            mock.patch.object(MODULE, "require_clean_repo") as clean,
            mock.patch.object(MODULE, "command", side_effect=run_command),
        ):
            synchronized = MODULE.synchronize_verified_elim_checkout(
                "/usr/bin/git",
                Path("/tmp"),
                result_commit=result_commit,
            )
        self.assertEqual(synchronized, current)
        self.assertEqual(clean.call_count, 2)

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

    def test_host_failure_projection_dispatches_independently_and_throttles_repeats(self):
        config = json.loads(
            (ROOT / ".github/run-coordinator-bot.json").read_text()
        )
        control = {
            "action_items": [
                {
                    "id": "failure-one",
                    "kind": "automation_failure",
                    "owner": "human",
                    "stage": "elim-isolated-checkout",
                    "details": "checkout baseline unavailable",
                    "resolved": False,
                }
            ]
        }
        projection = MODULE.build_host_status_projection(
            config,
            control,
            chain_id="chain-1",
            status="failed",
            stage="elim-isolated-checkout",
            message="checkout baseline unavailable",
            next_action="Repair the verified checkout boundary.",
            exit_code=1,
            payload={
                "host_closeout": {
                    "outcome": "completed",
                    "commit": "c" * 40,
                    "validated_at": "2026-07-26T11:29:48+00:00",
                    "recovered": True,
                }
            },
        )
        self.assertEqual(projection["availability"], "current")
        self.assertTrue(projection["completeness"]["complete"])
        self.assertEqual(projection["expected_count"], 1)
        self.assertEqual(projection["actual_count"], 1)
        self.assertEqual(projection["result_revision"], "c" * 40)
        self.assertTrue(projection["host_closeout"]["recovered"])
        completed = MODULE.subprocess.CompletedProcess(
            [], 0, stdout="", stderr=""
        )
        with (
            mock.patch.object(
                MODULE,
                "executable",
                return_value="/opt/homebrew/bin/gh",
            ),
            mock.patch.object(
                MODULE,
                "command",
                return_value=completed,
            ) as command,
        ):
            self.assertTrue(
                MODULE.dispatch_host_status_projection(
                    config,
                    control,
                    ROOT,
                    projection,
                )
            )
            self.assertFalse(
                MODULE.dispatch_host_status_projection(
                    config,
                    control,
                    ROOT,
                    projection,
                )
            )
            self.assertTrue(
                control["host_status_projection"]["repeat_suppressed"]
            )
            next_chain = {
                **projection,
                "chain_id": "chain-2",
                "host_updated_at": "2026-07-26T09:00:00+00:00",
                "updated_at": "2026-07-26T09:00:00+00:00",
            }
            self.assertTrue(
                MODULE.dispatch_host_status_projection(
                    config,
                    control,
                    ROOT,
                    next_chain,
                )
            )
        self.assertEqual(command.call_count, 2)
        request = json.loads(command.call_args.kwargs["stdin"])
        self.assertEqual(request["event_type"], "arrp-host-status")
        self.assertEqual(
            request["client_payload"]["status"]["host_status"],
            "failed",
        )
        self.assertFalse(control["host_status_projection"]["repeat_suppressed"])

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

    def test_control_merge_retains_dispatcher_incident_updates(self):
        latest = {
            "action_items": [
                {
                    "id": "automation-failure-one",
                    "resolved": False,
                    "occurrence_count": 1,
                    "last_chain_id": "chain-1",
                }
            ]
        }
        proposed = {
            "action_items": [
                {
                    "id": "automation-failure-one",
                    "resolved": False,
                    "occurrence_count": 2,
                    "last_chain_id": "chain-2",
                }
            ]
        }
        merged = MODULE.merge_control_states(latest, proposed)
        self.assertEqual(merged["action_items"][0]["occurrence_count"], 2)
        self.assertEqual(merged["action_items"][0]["last_chain_id"], "chain-2")

    def test_control_merge_does_not_resurrect_resolved_failure_summary(self):
        latest = {
            "last_failed_chain_id": "chain-1",
            "last_failed_exit_code": 1,
            "last_failed_reason": "closeout failed",
            "action_items": [
                {
                    "id": "automation-failure-one",
                    "kind": "automation_failure",
                    "chain_id": "chain-1",
                    "resolved": False,
                }
            ],
        }
        proposed = {
            "action_items": [
                {
                    "id": "automation-failure-one",
                    "kind": "automation_failure",
                    "chain_id": "chain-1",
                    "resolved": True,
                    "resolved_by": "verified-host-closeout-recovery",
                }
            ]
        }
        merged = MODULE.merge_control_states(latest, proposed)
        self.assertTrue(merged["action_items"][0]["resolved"])
        self.assertNotIn("last_failed_chain_id", merged)
        self.assertNotIn("last_failed_exit_code", merged)
        self.assertNotIn("last_failed_reason", merged)

        concurrent = {
            **latest,
            "last_failed_chain_id": "chain-2",
            "last_failed_reason": "new independent failure",
            "action_items": [
                *latest["action_items"],
                {
                    "id": "automation-failure-two",
                    "kind": "automation_failure",
                    "chain_id": "chain-2",
                    "resolved": False,
                },
            ],
        }
        merged = MODULE.merge_control_states(concurrent, proposed)
        self.assertEqual(merged["last_failed_chain_id"], "chain-2")
        self.assertEqual(
            merged["last_failed_reason"],
            "new independent failure",
        )

    def test_repeated_automation_failures_consolidate_without_losing_chains(self):
        branch_message = (
            "host-repository-preflight failed: canonical ARRP workspace is not "
            "reconciled with GitHub: current branch is {} instead of main. "
            "Merge the intended branch through GitHub, return local main to "
            "origin/main, and retry automated dispatch."
        )
        control = {
            "action_items": [
                {
                    "id": "failure-one",
                    "kind": "automation_failure",
                    "chain_id": "host-1",
                    "created_at": "2026-07-25T20:00:00+00:00",
                    "stage": "host-repository-preflight",
                    "details": branch_message.format("codex/one"),
                    "resolved": False,
                },
                {
                    "id": "failure-two",
                    "kind": "automation_failure",
                    "chain_id": "host-2",
                    "created_at": "2026-07-25T20:10:00+00:00",
                    "stage": "host-repository-preflight",
                    "details": branch_message.format("codex/two"),
                    "resolved": False,
                },
            ]
        }
        self.assertTrue(
            MODULE.consolidate_automation_failure_items(
                control,
                recorded_at="2026-07-25T20:20:00+00:00",
            )
        )
        unresolved = [
            item
            for item in control["action_items"]
            if item.get("resolved") is not True
        ]
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0]["occurrence_count"], 2)
        self.assertEqual(unresolved[0]["chain_ids"], ["host-1", "host-2"])
        duplicate = next(
            item for item in control["action_items"] if item["id"] == "failure-two"
        )
        self.assertEqual(duplicate["superseded_by"], "failure-one")
        self.assertEqual(
            control["action_item_history"][-1]["event"],
            "consolidated",
        )
        self.assertEqual(
            MODULE.resolve_observed_automation_incidents(
                control,
                incident_kinds={"canonical-workspace-not-main"},
                evidence="The canonical workspace is now verified.",
                recorded_at="2026-07-25T20:30:00+00:00",
            ),
            1,
        )
        self.assertFalse(
            [
                item
                for item in control["action_items"]
                if item.get("resolved") is not True
            ]
        )
        self.assertEqual(
            control["action_item_history"][-1]["source"],
            "dispatcher-health-proof",
        )

    def test_reconciled_main_resolves_prior_head_mismatch_incident(self):
        details = (
            "host-repository-preflight failed: canonical ARRP workspace is not "
            "reconciled with GitHub: local HEAD does not equal the fetched "
            "origin/main revision. Reconcile the divergent history through "
            "GitHub and retry automated dispatch."
        )
        self.assertEqual(
            MODULE.automation_incident_kind(details),
            "canonical-workspace-history-mismatch",
        )
        control = {
            "action_items": [
                {
                    "id": "automation-failure-head-mismatch",
                    "kind": "automation_failure",
                    "chain_id": "host-dispatch-one",
                    "stage": "host-repository-preflight",
                    "details": details,
                    "resolved": False,
                }
            ]
        }
        self.assertEqual(
            MODULE.resolve_observed_automation_incidents(
                control,
                incident_kinds={"canonical-workspace-history-mismatch"},
                evidence=(
                    "The canonical workspace is clean on main and exactly "
                    "matches origin/main."
                ),
                recorded_at="2026-07-26T23:45:00+00:00",
            ),
            1,
        )
        self.assertTrue(control["action_items"][0]["resolved"])
        self.assertEqual(
            control["action_items"][0]["resolved_by"],
            "dispatcher-health-proof",
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

    def test_host_outcome_history_replays_one_exact_recovery_event(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            config = {"manifest": {"historyLimit": 10}}
            manifest = self.selected_manifest()
            for _ in range(2):
                MODULE.append_host_outcome_history(
                    config,
                    repo,
                    chain_id="chain-1",
                    status="completed",
                    stage="elim-closeout-recovery",
                    exit_code=0,
                    payload=manifest,
                    event_id="elim-closeout-recovery:chain-1:" + "a" * 40,
                )
            value = json.loads(
                (repo / MODULE.HOST_OUTCOME_HISTORY).read_text(encoding="utf-8")
            )
            self.assertEqual(len(value["items"]), 1)
            self.assertEqual(
                value["items"][0]["event_id"],
                "elim-closeout-recovery:chain-1:" + "a" * 40,
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
            self.assertEqual(saved["items"][0]["last_run_id"], "chain-1")
            self.assertEqual(saved["items"][0]["result_commit"], "a" * 40)
            recorded_at = saved["items"][0]["recorded_at"]
            MODULE.persist_validated_recovery(repo, path, manifest, result)
            replayed = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(replayed["items"][0]["attempt_count"], 1)
            self.assertEqual(replayed["items"][0]["recorded_at"], recorded_at)
            self.assertTrue(
                MODULE.validated_recovery_record_matches(
                    repo,
                    path,
                    manifest,
                    result,
                )
            )
            changed = {**result, "unit_id": "other-unit"}
            with self.assertRaisesRegex(MODULE.ContextError, "work-unit ID"):
                MODULE.persist_validated_recovery(
                    repo,
                    path,
                    manifest,
                    changed,
                )

    def test_gap_obligation_persistence_retains_history_and_does_not_close_on_absence(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            path = repo / MODULE.ELIM_GAP_OBLIGATION_STATE
            result = self.elim_result()
            result["discovered_work_units"] = [
                {
                    "id": "DISC-1",
                    "obligation_id": "GAP-1",
                    "domain": "automation",
                    "discovery_context": "Quiet-queue governance review.",
                    "observed_at": "2026-07-25T12:00:00+00:00",
                    "source_revision": "a" * 40,
                    "evidence": ["The canonical route omits a required owner."],
                    "reasoning": "The omission prevents deterministic routing.",
                    "uncertainty": "The owner remains uncertain.",
                    "affected_records": ["framework/project/automation/context-routes.json"],
                    "consequence": "The gap can persist without a selected queue unit.",
                    "authority": {
                        "classification": "delegated_judgment",
                        "basis": "Elim runbook.",
                        "disposition": "uncertain",
                    },
                    "action_rationale": "Retain and recheck; do not guess the owner.",
                    "changed_files": ["framework/records/automation/elim-run-log.md"],
                    "affected_surfaces": ["repository", "automation", "console"],
                    "validation_readback": [
                        {
                            "check": "canonical detail",
                            "status": "passed",
                            "evidence": "Run Log detail read back.",
                        }
                    ],
                    "disposition": "retained",
                    "canonical_detail": "framework/records/automation/elim-run-log.md",
                    "provenance": ["framework/records/automation/elim-run-log.md#gap-1"],
                    "owner": "Elim",
                    "next_action": "Recheck ownership at the next revision.",
                    "next_trigger": "Context routes or ownership rules change.",
                    "outside_contribution": None,
                }
            ]
            result["gap_obligation_updates"] = [
                {
                    "obligation_id": "GAP-1",
                    "discovered_work_unit_id": "DISC-1",
                    "status": "open",
                    "observed_at": "2026-07-25T12:00:00+00:00",
                    "resolution": None,
                }
            ]
            saved = MODULE.persist_gap_obligation_updates(repo, path, result)
            self.assertEqual(saved["items"][0]["occurrence_count"], 1)
            self.assertEqual(saved["items"][0]["authority_disposition"], "uncertain")

            result["run_id"] = "chain-2"
            result["gap_obligation_updates"][0][
                "observed_at"
            ] = "2026-07-26T12:00:00+00:00"
            result["discovered_work_units"][0][
                "observed_at"
            ] = "2026-07-26T12:00:00+00:00"
            saved = MODULE.persist_gap_obligation_updates(repo, path, result)
            self.assertEqual(saved["items"][0]["occurrence_count"], 2)
            first_seen = saved["items"][0]["first_seen"]

            result["run_id"] = "chain-3"
            result["discovered_work_units"] = []
            result["gap_obligation_updates"] = []
            unchanged = MODULE.persist_gap_obligation_updates(repo, path, result)
            self.assertEqual(unchanged["items"][0]["first_seen"], first_seen)
            self.assertEqual(unchanged["items"][0]["status"], "open")

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

    def test_reconciled_archive_supplies_one_time_safe_checkout_baseline(self):
        head = "a" * 40
        control = {
            "checkout_archive_history": [
                {
                    "chain_id": "chain-old",
                    "canonical_revision": head,
                }
            ]
        }
        self.assertEqual(
            MODULE.safe_prior_checkout_head(control),
            (head, "reconciled-archive-proof"),
        )
        control["elim_checkout_synced_head"] = "b" * 40
        self.assertEqual(
            MODULE.safe_prior_checkout_head(control),
            ("b" * 40, "verified-control-state"),
        )

    def test_prepared_checkout_baseline_is_persisted_before_launch_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            checkout = repo / ".tmp/run-coordinator/elim-checkout"
            checkout.mkdir(parents=True)
            control_path = repo / ".tmp/run-coordinator/control.json"
            head = "a" * 40
            responses = [
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout=head + "\n", stderr=""
                ),
                MODULE.subprocess.CompletedProcess(
                    [], 0, stdout=head + "\n", stderr=""
                ),
            ]
            control = {}
            with (
                mock.patch.object(MODULE, "require_clean_repo"),
                mock.patch.object(MODULE, "command", side_effect=responses),
            ):
                recorded = MODULE.persist_verified_checkout_baseline(
                    "/usr/bin/git",
                    checkout,
                    control,
                    control_path,
                    repo=repo,
                    chain_id="chain-1",
                    source="fresh-clone-or-current-origin-main",
                )
            self.assertEqual(recorded, head)
            self.assertEqual(control["elim_checkout_synced_head"], head)
            self.assertEqual(
                control["elim_checkout_synced_chain_id"],
                "chain-1",
            )
            persisted = json.loads(control_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["elim_checkout_synced_head"], head)

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
            (
                repo / "framework" / "records" / "automation"
            ).mkdir(parents=True)
            (repo / "framework/records/automation/elim-run-log.md").write_text(
                "# Elim Run Log\n\n## Runs\n",
                encoding="utf-8",
            )
            git(repo, "add", "framework/records/automation/elim-run-log.md")
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
            git(repo, "add", "framework/records/automation/elim-run-log.md")
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
            checkpoint = checkout / "framework/records/handoffs/current-task.md"
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            checkpoint.write_text(
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
            self.assertRegex(archived.name, r"^[0-9a-f]{64}$")
            self.assertTrue(
                (archived / ".arrp-reconciled-checkout.json").is_file()
            )
            self.assertEqual(
                record["changed_paths"],
                ["framework/records/handoffs/current-task.md"],
            )
            self.assertEqual(
                control["checkout_archive_history"][0]["chain_id"],
                chain_id,
            )
            self.assertNotIn("elim_thread_id", control)
            self.assertNotIn("elim_thread_checkout", control)

    def test_checked_closeout_pull_request_requires_checks_and_exact_merge(self):
        baseline = "a" * 40
        commit = "b" * 40
        merge_commit = "c" * 40
        branch = "codex/elim-chain-1"
        pull_request = "https://github.com/Thorncrag/ARRP/pull/999"
        open_pr = {
            "number": 999,
            "state": "OPEN",
            "url": pull_request,
            "headRefName": branch,
            "headRefOid": commit,
            "baseRefName": "main",
            "baseRefOid": baseline,
            "mergeCommit": None,
        }
        merged_pr = {
            **open_pr,
            "state": "MERGED",
            "mergeCommit": {"oid": merge_commit},
        }
        remote_readbacks = iter((baseline, merge_commit))

        def run_command(argv, **_kwargs):
            if argv[1:3] == ["pr", "create"]:
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout=pull_request + "\n", stderr=""
                )
            if argv[1:3] == ["pr", "merge"]:
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="", stderr=""
                )
            if argv[1] == "fetch":
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="", stderr=""
                )
            if argv[1:3] == ["rev-parse", "refs/remotes/origin/main"]:
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout=next(remote_readbacks) + "\n", stderr=""
                )
            if argv[1] == "rev-list":
                return MODULE.subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout=f"{merge_commit} {baseline}\n",
                    stderr="",
                )
            self.fail(f"unexpected command: {argv}")

        with (
            mock.patch.object(
                MODULE,
                "matching_closeout_pull_request",
                return_value=None,
            ),
            mock.patch.object(
                MODULE,
                "ensure_host_closeout_branch",
                return_value=True,
            ) as pushed,
            mock.patch.object(
                MODULE,
                "read_closeout_pull_request",
                side_effect=[open_pr, open_pr, merged_pr],
            ),
            mock.patch.object(
                MODULE,
                "wait_for_closeout_checks",
                return_value=[
                    {"name": "CodeQL", "bucket": "pass"},
                    {"name": "Vercel", "bucket": "pass"},
                ],
            ) as waited,
            mock.patch.object(
                MODULE,
                "command",
                side_effect=run_command,
            ) as invoked,
        ):
            observed_merge, synchronization, observed_pr = (
                MODULE.publish_checked_pull_request(
                    git="/usr/bin/git",
                    gh=MODULE.EXECUTABLES["githubCliPath"],
                    repo=Path("/tmp"),
                    repository="Thorncrag/ARRP",
                    branch=branch,
                    commit=commit,
                    baseline_commit=baseline,
                    title="Checked closeout",
                    body="Exact tested boundary.",
                )
            )

        self.assertEqual(observed_merge, merge_commit)
        self.assertEqual(observed_pr, pull_request)
        self.assertTrue(any("2 checks" in row for row in synchronization))
        pushed.assert_called_once()
        waited.assert_called_once()
        commands = [call.args[0] for call in invoked.mock_calls]
        merge_commands = [
            argv for argv in commands if argv[1:3] == ["pr", "merge"]
        ]
        self.assertEqual(len(merge_commands), 1)
        self.assertIn("--match-head-commit", merge_commands[0])
        self.assertNotIn("refs/heads/main", " ".join(" ".join(row) for row in commands))

    def test_merged_closeout_pull_request_still_revalidates_checks(self):
        baseline = "a" * 40
        commit = "b" * 40
        merge_commit = "c" * 40
        branch = "codex/elim-chain-1"
        pull_request = "https://github.com/Thorncrag/ARRP/pull/999"
        merged_pr = {
            "number": 999,
            "state": "MERGED",
            "url": pull_request,
            "headRefName": branch,
            "headRefOid": commit,
            "baseRefName": "main",
            "baseRefOid": baseline,
            "mergeCommit": {"oid": merge_commit},
        }

        def run_command(argv, **_kwargs):
            if argv[1] == "fetch":
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="", stderr=""
                )
            if argv[1:3] == ["rev-parse", "refs/remotes/origin/main"]:
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout=merge_commit + "\n", stderr=""
                )
            if argv[1] == "rev-list":
                return MODULE.subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout=f"{merge_commit} {baseline}\n",
                    stderr="",
                )
            self.fail(f"unexpected command: {argv}")

        with (
            mock.patch.object(
                MODULE,
                "matching_closeout_pull_request",
                return_value=merged_pr,
            ),
            mock.patch.object(
                MODULE,
                "wait_for_closeout_checks",
                return_value=[{"name": "CodeQL", "bucket": "pass"}],
            ) as waited,
            mock.patch.object(
                MODULE,
                "command",
                side_effect=run_command,
            ) as invoked,
        ):
            observed_merge, synchronization, observed_pr = (
                MODULE.publish_checked_pull_request(
                    git="/usr/bin/git",
                    gh=MODULE.EXECUTABLES["githubCliPath"],
                    repo=Path("/tmp"),
                    repository="Thorncrag/ARRP",
                    branch=branch,
                    commit=commit,
                    baseline_commit=baseline,
                    title="Checked closeout",
                    body="Exact tested boundary.",
                )
            )

        self.assertEqual(observed_merge, merge_commit)
        self.assertEqual(observed_pr, pull_request)
        self.assertTrue(any("1 checks" in row for row in synchronization))
        waited.assert_called_once()
        self.assertFalse(
            any(
                call.args[0][1:3] == ["pr", "merge"]
                for call in invoked.mock_calls
            )
        )

    def test_closeout_check_failure_stops_before_merge(self):
        failed = MODULE.subprocess.CompletedProcess(
            [],
            1,
            stdout=json.dumps(
                [
                    {
                        "bucket": "fail",
                        "name": "CodeQL",
                        "state": "FAILURE",
                        "link": "https://example.invalid/check",
                    }
                ]
            ),
            stderr="",
        )
        with mock.patch.object(MODULE, "command", return_value=failed):
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "checks failed or were cancelled: CodeQL",
            ):
                MODULE.wait_for_closeout_checks(
                    MODULE.EXECUTABLES["githubCliPath"],
                    Path("/tmp"),
                    repository="Thorncrag/ARRP",
                    pull_request="https://github.com/Thorncrag/ARRP/pull/999",
                )

    def test_closeout_waits_until_github_registers_the_first_check(self):
        no_checks_yet = MODULE.subprocess.CompletedProcess(
            [],
            1,
            stdout="",
            stderr="no checks reported on the 'codex/elim-chain-1' branch",
        )
        complete = MODULE.subprocess.CompletedProcess(
            [],
            0,
            stdout=json.dumps(
                [
                    {
                        "bucket": "pass",
                        "name": "CodeQL",
                        "state": "SUCCESS",
                    }
                ]
            ),
            stderr="",
        )
        with (
            mock.patch.object(
                MODULE,
                "command",
                side_effect=[no_checks_yet, complete],
            ) as checked,
            mock.patch.object(
                MODULE.time,
                "monotonic",
                side_effect=[0.0, 0.0, 1.0],
            ),
            mock.patch.object(MODULE.time, "sleep") as slept,
        ):
            rows = MODULE.wait_for_closeout_checks(
                MODULE.EXECUTABLES["githubCliPath"],
                Path("/tmp"),
                repository="Thorncrag/ARRP",
                pull_request="https://github.com/Thorncrag/ARRP/pull/999",
            )
        self.assertEqual(rows[0]["name"], "CodeQL")
        self.assertEqual(checked.call_count, 2)
        slept.assert_called_once_with(
            MODULE.HOST_CLOSEOUT_POLICY["checkPollSeconds"]
        )

    def test_closeout_rejects_unrecognized_non_json_check_output(self):
        unreadable = MODULE.subprocess.CompletedProcess(
            [],
            8,
            stdout="temporarily unavailable",
            stderr="",
        )
        with mock.patch.object(MODULE, "command", return_value=unreadable):
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "check readback is unreadable",
            ):
                MODULE.wait_for_closeout_checks(
                    MODULE.EXECUTABLES["githubCliPath"],
                    Path("/tmp"),
                    repository="Thorncrag/ARRP",
                    pull_request="https://github.com/Thorncrag/ARRP/pull/999",
                )

    def test_closeout_check_readback_rejects_unknown_bucket(self):
        unknown = MODULE.subprocess.CompletedProcess(
            [],
            0,
            stdout=json.dumps(
                [
                    {
                        "bucket": "mystery",
                        "name": "CodeQL",
                        "state": "UNKNOWN",
                    }
                ]
            ),
            stderr="",
        )
        with mock.patch.object(MODULE, "command", return_value=unknown):
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "unsupported states: mystery",
            ):
                MODULE.wait_for_closeout_checks(
                    MODULE.EXECUTABLES["githubCliPath"],
                    Path("/tmp"),
                    repository="Thorncrag/ARRP",
                    pull_request="https://github.com/Thorncrag/ARRP/pull/999",
                )

    def test_closeout_waits_for_named_required_check_to_pass(self):
        vercel_only = MODULE.subprocess.CompletedProcess(
            [],
            0,
            stdout=json.dumps(
                [
                    {
                        "bucket": "pass",
                        "name": "Vercel",
                        "state": "SUCCESS",
                    }
                ]
            ),
            stderr="",
        )
        complete = MODULE.subprocess.CompletedProcess(
            [],
            0,
            stdout=json.dumps(
                [
                    {
                        "bucket": "pass",
                        "name": "Vercel",
                        "state": "SUCCESS",
                    },
                    {
                        "bucket": "pass",
                        "name": "CodeQL",
                        "state": "SUCCESS",
                    },
                ]
            ),
            stderr="",
        )
        with (
            mock.patch.object(
                MODULE,
                "command",
                side_effect=[vercel_only, complete],
            ) as checked,
            mock.patch.object(
                MODULE.time,
                "monotonic",
                side_effect=[0.0, 0.0, 1.0],
            ),
            mock.patch.object(MODULE.time, "sleep") as slept,
        ):
            rows = MODULE.wait_for_closeout_checks(
                MODULE.EXECUTABLES["githubCliPath"],
                Path("/tmp"),
                repository="Thorncrag/ARRP",
                pull_request="https://github.com/Thorncrag/ARRP/pull/999",
            )
        self.assertEqual(len(rows), 2)
        self.assertEqual(checked.call_count, 2)
        slept.assert_called_once_with(
            MODULE.HOST_CLOSEOUT_POLICY["checkPollSeconds"]
        )

    def test_merged_closeout_must_have_the_pinned_baseline_as_sole_parent(self):
        baseline = "a" * 40
        commit = "b" * 40
        merge_commit = "c" * 40
        moved_parent = "d" * 40
        branch = "codex/elim-chain-1"
        merged_pr = {
            "number": 999,
            "state": "MERGED",
            "url": "https://github.com/Thorncrag/ARRP/pull/999",
            "headRefName": branch,
            "headRefOid": commit,
            "baseRefName": "main",
            "baseRefOid": baseline,
            "mergeCommit": {"oid": merge_commit},
        }

        def run_command(argv, **_kwargs):
            if argv[1] == "fetch":
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout="", stderr=""
                )
            if argv[1:3] == ["rev-parse", "refs/remotes/origin/main"]:
                return MODULE.subprocess.CompletedProcess(
                    argv, 0, stdout=merge_commit + "\n", stderr=""
                )
            if argv[1] == "rev-list":
                return MODULE.subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout=f"{merge_commit} {moved_parent}\n",
                    stderr="",
                )
            self.fail(f"unexpected command: {argv}")

        with (
            mock.patch.object(
                MODULE,
                "matching_closeout_pull_request",
                return_value=merged_pr,
            ),
            mock.patch.object(
                MODULE,
                "wait_for_closeout_checks",
                return_value=[{"name": "CodeQL", "bucket": "pass"}],
            ),
            mock.patch.object(MODULE, "command", side_effect=run_command),
        ):
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "pinned baseline as its exact sole parent",
            ):
                MODULE.publish_checked_pull_request(
                    git="/usr/bin/git",
                    gh=MODULE.EXECUTABLES["githubCliPath"],
                    repo=Path("/tmp"),
                    repository="Thorncrag/ARRP",
                    branch=branch,
                    commit=commit,
                    baseline_commit=baseline,
                    title="Checked closeout",
                    body="Exact tested boundary.",
                )

    def test_prepared_elim_commit_requires_all_reviewed_host_proofs(self):
        baseline = "a" * 40
        commit = "b" * 40
        second_parent = "c" * 40
        result = self.elim_result()
        result["run_id"] = "chain-1"
        result["files_touched"] = ["framework/records/automation/elim-run-log.md"]
        branch = MODULE.host_closeout_branch(result["run_id"])
        expected_identity = "\0".join(
            [
                MODULE.host_closeout_commit_message(result),
                MODULE.HOST_GIT_IDENTITY["name"],
                MODULE.HOST_GIT_IDENTITY["email"],
                MODULE.HOST_GIT_IDENTITY["name"],
                MODULE.HOST_GIT_IDENTITY["email"],
            ]
        )

        def command_for(fault):
            def run_command(argv, **_kwargs):
                if argv[1:] == ["status", "--porcelain"]:
                    return MODULE.subprocess.CompletedProcess(
                        argv, 0, stdout="", stderr=""
                    )
                if argv[1:] == ["branch", "--show-current"]:
                    return MODULE.subprocess.CompletedProcess(
                        argv, 0, stdout=branch + "\n", stderr=""
                    )
                if argv[1:] == ["rev-parse", "HEAD"]:
                    return MODULE.subprocess.CompletedProcess(
                        argv, 0, stdout=commit + "\n", stderr=""
                    )
                if argv[1] == "rev-list":
                    parents = (
                        f"{commit} {baseline} {second_parent}\n"
                        if fault == "topology"
                        else f"{commit} {baseline}\n"
                    )
                    return MODULE.subprocess.CompletedProcess(
                        argv, 0, stdout=parents, stderr=""
                    )
                if argv[1] == "show":
                    identity = (
                        expected_identity.replace(
                            MODULE.HOST_GIT_IDENTITY["name"],
                            "Untrusted Author",
                            1,
                        )
                        if fault == "identity"
                        else expected_identity
                    )
                    return MODULE.subprocess.CompletedProcess(
                        argv, 0, stdout=identity + "\n", stderr=""
                    )
                if argv[1:3] == ["diff", "--name-only"]:
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        0,
                        stdout="framework/records/automation/elim-run-log.md\0",
                        stderr="",
                    )
                if argv[1:3] == ["diff", "--check"]:
                    return MODULE.subprocess.CompletedProcess(
                        argv,
                        1 if fault == "hygiene" else 0,
                        stdout=(
                            "framework/records/automation/elim-run-log.md: trailing whitespace\n"
                            if fault == "hygiene"
                            else ""
                        ),
                        stderr="",
                    )
                self.fail(f"unexpected command: {argv}")

            return run_command

        for fault in ("topology", "identity", "hygiene"):
            with (
                self.subTest(fault=fault),
                mock.patch.object(
                    MODULE,
                    "command",
                    side_effect=command_for(fault),
                ),
                mock.patch.object(
                    MODULE,
                    "verify_elim_authored_content",
                ),
            ):
                with self.assertRaisesRegex(
                    MODULE.ContextError,
                    "topology, identity, message, file set, or diff hygiene",
                ):
                    MODULE.verify_prepared_host_closeout_commit(
                        "/usr/bin/git",
                        Path("/tmp"),
                        result,
                        expected_manifest=self.selected_manifest(),
                        branch=branch,
                        baseline_commit=baseline,
                    )

    def test_elim_result_next_action_uses_the_continuation_contract(self):
        result = self.elim_result(next_action="Use the next current chain.")
        self.assertEqual(
            MODULE.elim_result_next_action(result),
            "Use the next current chain.",
        )
        result["continuation"]["next_action"] = None
        self.assertIsNone(MODULE.elim_result_next_action(result))
        del result["continuation"]["next_action"]
        with self.assertRaisesRegex(
            MODULE.ContextError,
            "lacks its continuation next action",
        ):
            MODULE.elim_result_next_action(result)

    def test_verified_recovery_clears_only_its_exact_reconciliation_and_incident(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            state_path = repo / MODULE.ELIM_RUN_LOG_RECONCILIATION_STATE
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "items": [
                            {
                                "chain_id": "chain-1",
                                "invocation_id": "invocation-1",
                                "execution_checkout": "checkout-1",
                            },
                            {
                                "chain_id": "chain-2",
                                "invocation_id": "invocation-2",
                                "execution_checkout": "checkout-2",
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = self.elim_result(outcome="completed")
            result["run_id"] = "chain-1"
            result["commit"] = "c" * 40
            MODULE.clear_verified_run_log_reconciliation(
                repo,
                state_path,
                chain_id="chain-1",
                result=result,
            )
            retained = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(
                [row["chain_id"] for row in retained["items"]],
                ["chain-2"],
            )
            with self.assertRaisesRegex(
                MODULE.ContextError,
                "absent without an exact durable recovery marker",
            ):
                MODULE.clear_verified_run_log_reconciliation(
                    repo,
                    state_path,
                    chain_id="chain-1",
                    result=result,
                )
            recovery_path = repo / MODULE.ELIM_RECOVERY_STATE
            manifest = self.selected_manifest()
            MODULE.persist_validated_recovery(
                repo,
                recovery_path,
                manifest,
                result,
            )
            MODULE.clear_verified_run_log_reconciliation(
                repo,
                state_path,
                chain_id="chain-1",
                result=result,
                recovery_path=recovery_path,
                payload=manifest,
            )
            retained = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(
                [row["chain_id"] for row in retained["items"]],
                ["chain-2"],
            )

            control = {
                "action_items": [
                    {
                        "id": "recover-me",
                        "kind": "automation_failure",
                        "chain_id": "chain-1",
                        "stage": "elim-host-git-closeout",
                        "resolved": False,
                    },
                    {
                        "id": "recover-interrupted-execution",
                        "kind": "automation_failure",
                        "chain_id": "chain-1",
                        "stage": "elim-execution",
                        "resolved": False,
                    },
                    {
                        "id": "retain-me",
                        "kind": "automation_failure",
                        "chain_id": "chain-2",
                        "stage": "elim-host-git-closeout",
                        "resolved": False,
                    },
                    {
                        "id": "legacy-partial-transaction",
                        "kind": "automation_failure",
                        "chain_id": "host-dispatch-20260726T125538Z",
                        "stage": "host-repository-preflight",
                        "details": "host-repository-preflight failed: 'next_action'",
                        "resolved": False,
                    },
                ],
                "last_failed_chain_id": "chain-1",
                "last_failed_exit_code": 1,
                "last_failed_reason": (
                    "elim-closeout-recovery failed: isolated checkout is not "
                    "at the current boundary"
                ),
                "last_failed_at": "2026-07-26T13:47:00+00:00",
            }
            self.assertEqual(
                MODULE.record_verified_closeout_recovery(
                    control,
                    chain_id="chain-1",
                    result_commit="c" * 40,
                    synchronized_head="d" * 40,
                    recovered_at="2026-07-26T13:37:35+00:00",
                ),
                3,
            )
            self.assertTrue(control["action_items"][0]["resolved"])
            self.assertTrue(control["action_items"][1]["resolved"])
            self.assertFalse(control["action_items"][2]["resolved"])
            self.assertTrue(control["action_items"][3]["resolved"])
            self.assertEqual(
                control["action_items"][0]["resolved_by"],
                "verified-host-closeout-recovery",
            )
            self.assertEqual(
                control["action_items"][1]["resolved_by"],
                "verified-host-closeout-recovery",
            )
            self.assertNotIn("last_failed_chain_id", control)
            self.assertNotIn("last_failed_exit_code", control)
            self.assertEqual(
                control["elim_checkout_synced_head"],
                "d" * 40,
            )
            self.assertEqual(control["last_recovered_chain_id"], "chain-1")

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
            logs = repo / "framework/records/automation"
            logs.mkdir(parents=True, exist_ok=True)
            (logs / "elim-run-log.md").write_text(
                "# Elim Run Log\n\n## Runs\n",
                encoding="utf-8",
            )
            git(repo, "add", ".gitignore", "framework/records/handoffs/current-task.md", "framework/records/automation/elim-run-log.md")
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
                "framework/records/handoffs/current-task.md",
                "framework/records/automation/elim-run-log.md",
            ]
            result_path = repo / ".tmp/result.json"
            result_path.parent.mkdir(parents=True)
            result_path.write_text(json.dumps(result) + "\n", encoding="utf-8")
            manifest = self.selected_manifest()
            manifest["final_revision"] = baseline

            def publish_locally(**kwargs):
                commit = kwargs["commit"]
                git(repo, "push", "origin", f"{commit}:refs/heads/main")
                git(repo, "fetch", "--no-tags", "origin", "main")
                return (
                    commit,
                    ["Test-only checked publication substitute."],
                    "https://github.com/Thorncrag/ARRP/pull/1",
                )

            with mock.patch.object(
                MODULE,
                "APPROVED_ORIGIN_URLS",
                frozenset({str(remote)}),
            ):
                with mock.patch.object(
                    MODULE,
                    "publish_checked_pull_request",
                    side_effect=RuntimeError("transient publication failure"),
                ):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "transient publication failure",
                    ):
                        MODULE.host_preserve_elim_result(
                            git="/usr/bin/git",
                            gh=MODULE.EXECUTABLES["githubCliPath"],
                            repo=repo,
                            result_path=result_path,
                            expected_manifest=manifest,
                            repository="Thorncrag/ARRP",
                        )
                self.assertEqual(git(repo, "status", "--porcelain"), "")
                self.assertEqual(
                    git(repo, "branch", "--show-current"),
                    MODULE.host_closeout_branch(result["run_id"]),
                )
                with mock.patch.object(
                    MODULE,
                    "publish_checked_pull_request",
                    side_effect=publish_locally,
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
            "framework/records/handoffs/current-task.md",
            "framework/records/automation/elim-run-log.md",
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
