import importlib.util
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_coordinator", ROOT / "scripts" / "run_coordinator.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class RunCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(
            (ROOT / ".github" / "run-coordinator-bot.json").read_text()
        )
        self.now = datetime(2026, 7, 24, 8, tzinfo=timezone.utc)

    def governance_projection(
        self,
        *,
        ordinary_count: int = 1,
        current: bool = False,
    ):
        last_review = (
            {
                "last_reviewed_at": "2026-07-24T07:00:00+00:00",
                "run_id": "run-1",
                "selected_unit_id": "governance-unit-1",
                "discovered_work_unit_id": "discovery-control-1",
                "source_revision": "b" * 40,
                "disposition": "no_material_finding",
                "canonical_detail": "framework/records/automation/elim-run-log.md",
                "next_trigger": "Repeat at the minimum cadence or when new work appears.",
            }
            if current
            else None
        )
        return {
            "mode": "Project governance review and discovery",
            "ordinary_selection_policy": "after-ordinary-queue-clears",
            "minimum_interval_hours": 168,
            "selected_as_quiet_queue_fallback": False,
            "ordinary_eligible_count_before_fallback": ordinary_count,
            "last_review": last_review,
            "next_due_at": (
                "2026-07-31T07:00:00+00:00" if current else None
            ),
            "current_for_cadence": current,
            "waiting_for_ordinary_queue": ordinary_count > 0,
            "reason": (
                "The last committed governance review remains current for the "
                "minimum cadence."
                if current
                else "Ordinary eligible work remains and is selected first."
            ),
        }

    def gap_queue_item(self):
        projection = {
            "severity": "warning",
            "owner": "agent",
            "authority": {
                "classification": "delegated_judgment",
                "basis": "The runbook authorizes investigation but not implementation.",
            },
            "authority_disposition": "forbidden",
            "disposition": "retained",
            "first_seen": "2026-07-20T08:00:00+00:00",
            "last_checked": "2026-07-24T08:00:00+00:00",
            "occurrence_count": 2,
            "age_days": 4,
            "canonical_detail": "framework/records/automation/elim-run-log.md",
            "exact_next_action": "Retain the finding until its recorded trigger.",
            "next_trigger": "A governing rule authorizes the change.",
            "source_revision": "c" * 40,
        }
        return {
            "id": "INTEGRITY-gap-1",
            "kind": "integrity",
            "work_class": "gap_stewardship",
            "title": "Retained governance gap",
            "eligible_for_elim": False,
            "requires_human": False,
            "eligibility_reason": "not eligible under the selected runbook",
            "blocking_reason": None,
            "exact_next_action": projection["exact_next_action"],
            "gap_obligation_id": "GAP-001",
            "source": {
                "input": "gap_obligations",
                "finding_type": "gap_obligation",
                "obligation_id": "GAP-001",
                "obligation_status": "open",
                "obligation_projection": projection,
                "canonicalRecord": "framework/records/automation/elim-run-log.md",
                "canonical_record": "framework/records/automation/elim-run-log.md",
            },
        }

    def test_stage_order_ends_with_integrity_and_elim_is_not_a_bot_stage(self):
        MODULE.validate_config(self.config)
        ids = [stage["id"] for stage in self.config["stages"]]
        self.assertEqual(ids[-1], "project-integrity-bot")
        self.assertNotIn("elim", ids)

    def test_local_config_has_no_required_workflow_adapter(self):
        self.assertTrue(MODULE.is_local_first_config(self.config))
        MODULE.validate_config(self.config)
        health = MODULE.workflow_health(self.config, ROOT)
        self.assertEqual(
            health,
            {"healthy": True, "missing": [], "checks": []},
        )

    def test_local_plan_uses_external_runner_lock_and_plain_json_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "run-chain.json"
            args = mock.Mock(
                config=ROOT / ".github/run-coordinator-bot.json",
                previous=None,
                signals=None,
                now="2026-07-24T08:00:00+00:00",
                chain_id="local-chain",
                resume=False,
                lock_path=None,
                repo=ROOT,
                run_id="local-run",
                trigger="fixture",
                output=output,
                github_output=None,
                local=True,
            )
            self.assertEqual(MODULE.plan(args), 0)
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["lock"]["status"],
                "external-local-lock",
            )
            self.assertEqual(
                manifest["workflow_health"]["checks"],
                [],
            )

    def test_comprehensive_queue_uses_the_full_context_profile(self):
        self.assertFalse(
            (ROOT / ".github/workflows/run-coordinator-bot.yml").exists()
        )
        profile = self.config["llmRouting"]["profiles"]["comprehensive"]
        self.assertTrue(profile["fullContext"])
        self.assertIn("comprehensive-review", profile["eligibleQueueClasses"])

    def test_local_planner_owns_review_epoch_boundary(self):
        self.assertTrue(callable(MODULE.review_epoch_boundary_status))
        self.assertEqual(self.config["reviewEpoch"]["intervalDays"], 14)
        self.assertTrue(self.config["governanceDiscovery"]["enabled"])

    def test_local_stage_inventory_is_exact_and_has_no_workflow_adapter(self):
        stage_ids = [stage["id"] for stage in self.config["stages"]]
        self.assertEqual(len(stage_ids), len(set(stage_ids)))
        self.assertEqual(
            stage_ids,
            [
                "case-monitor-bot",
                "presidential-directives-bot",
                "source-checker-bot",
                "public-intake",
                "project-console-progress-bot",
                "project-integrity-bot",
            ],
        )
        for stage in self.config["stages"]:
            self.assertNotIn("workflow", stage)
            self.assertTrue(stage["command"])
            self.assertTrue(stage["output"])

    def test_ordinary_stage_compile_does_not_require_watcher_attempt_outputs(self):
        for stage in self.config["stages"]:
            self.assertNotIn("attempt_key", stage)
            self.assertNotIn("artifact", stage)
            self.assertNotIn("workflow", stage)
        self.assertEqual(
            self.config["outputs"]["stageDirectory"],
            "<run-dir>/stages",
        )

    def test_selected_watcher_artifact_is_hash_and_attempt_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = root / "artifacts"
            selected = artifacts / "case-monitor"
            selected.mkdir(parents=True)
            destination = root / "inputs"
            destination.mkdir()
            report = selected / "monitoring-report.json"
            report.write_text('{"selected":"retry"}\n', encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(report.read_bytes()).hexdigest()
            run_id = "github-actions:Thorncrag/ARRP:100:2:retry"
            manifest = {
                "chain_id": "chain-1",
                "stages": [
                    {
                        "id": "case-monitor-bot",
                        "due": True,
                        "status": "succeeded",
                        "attempt_key": "retry",
                        "run_id": run_id,
                        "output": {"sha256": digest},
                    }
                ],
            }
            attestation = {
                "schema_version": 1,
                "stage_id": "case-monitor-bot",
                "chain_id": "chain-1",
                "run_id": run_id,
                "attempt_key": "retry",
                "report_sha256": digest,
                "domain_event": None,
            }
            (selected / "watcher-attempt.json").write_text(
                json.dumps(attestation) + "\n",
                encoding="utf-8",
            )
            MODULE.materialize_selected_watcher_artifacts(
                manifest,
                artifacts,
                destination,
            )
            self.assertEqual(
                (destination / "case-monitor.json").read_text(encoding="utf-8"),
                '{"selected":"retry"}\n',
            )

            attestation["attempt_key"] = "primary"
            (selected / "watcher-attempt.json").write_text(
                json.dumps(attestation) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "attempt attestation"):
                MODULE.materialize_selected_watcher_artifacts(
                    manifest,
                    artifacts,
                    destination,
                )

            attestation["attempt_key"] = "retry"
            (selected / "watcher-attempt.json").write_text(
                json.dumps(attestation) + "\n",
                encoding="utf-8",
            )
            manifest["stages"][0]["output"]["sha256"] = "sha256:" + "0" * 64
            with self.assertRaisesRegex(ValueError, "report hash differs"):
                MODULE.materialize_selected_watcher_artifacts(
                    manifest,
                    artifacts,
                    destination,
                )

    def test_successful_watcher_cannot_fall_back_when_artifact_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "inputs"
            destination.mkdir()
            prior = destination / "source-checker.json"
            prior.write_text('{"prior":true}\n', encoding="utf-8")
            manifest = {
                "chain_id": "chain-1",
                "stages": [
                    {
                        "id": "source-checker-bot",
                        "due": True,
                        "status": "succeeded",
                        "attempt_key": "primary",
                        "run_id": "github-actions:Thorncrag/ARRP:100:2:primary",
                        "output": {"sha256": "sha256:" + "0" * 64},
                    }
                ],
            }
            with self.assertRaisesRegex(ValueError, "lacks its selected primary artifact"):
                MODULE.materialize_selected_watcher_artifacts(
                    manifest,
                    root / "artifacts",
                    destination,
                )
            self.assertEqual(prior.read_text(encoding="utf-8"), '{"prior":true}\n')

    def test_source_checker_materializes_actual_downloaded_artifact_hierarchy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected = root / "artifacts/source-checker"
            nested = selected / "arrp-source-checker"
            nested.mkdir(parents=True)
            report = nested / "source-checker.json"
            report.write_text('{"results":[]}\n', encoding="utf-8")
            digest = "sha256:" + hashlib.sha256(report.read_bytes()).hexdigest()
            run_id = "github-actions:Thorncrag/ARRP:100:2:primary"
            attestation = {
                "schema_version": 1,
                "stage_id": "source-checker-bot",
                "chain_id": "chain-1",
                "run_id": run_id,
                "attempt_key": "primary",
                "report_sha256": digest,
                "domain_event": None,
            }
            (selected / "watcher-attempt.json").write_text(
                json.dumps(attestation) + "\n",
                encoding="utf-8",
            )
            manifest = {
                "chain_id": "chain-1",
                "stages": [
                    {
                        "id": "source-checker-bot",
                        "due": True,
                        "status": "succeeded",
                        "attempt_key": "primary",
                        "run_id": run_id,
                        "output": {"sha256": digest},
                    }
                ],
            }
            MODULE.materialize_selected_watcher_artifacts(
                manifest,
                root / "artifacts",
                root / "inputs",
            )
            self.assertEqual(
                (root / "inputs/source-checker.json").read_bytes(),
                report.read_bytes(),
            )

    def test_watcher_event_is_bound_to_chain_run_and_proposal_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected = root / "artifacts/presidential-directives"
            selected.mkdir(parents=True)
            report = selected / "directives-report.json"
            report.write_text('{"counts":{}}\n', encoding="utf-8")
            report_hash = (
                "sha256:" + hashlib.sha256(report.read_bytes()).hexdigest()
            )
            event = {
                "event_id": "event-1",
                "chain_id": "wrong-chain",
                "run_id": "github-actions:Thorncrag/ARRP:100:2:retry",
                "proposal": {"proposal_revision": "a" * 40},
            }
            event_path = selected / "presidential-directives-domain-event.json"
            event_path.write_text(
                json.dumps(event, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            event_hash = (
                "sha256:" + hashlib.sha256(event_path.read_bytes()).hexdigest()
            )
            event_metadata = {
                "id": "event-1",
                "sha256": event_hash,
                "json": event,
            }
            run_id = "github-actions:Thorncrag/ARRP:100:2:retry"
            (selected / "watcher-attempt.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "stage_id": "presidential-directives-bot",
                        "chain_id": "chain-1",
                        "run_id": run_id,
                        "attempt_key": "retry",
                        "report_sha256": report_hash,
                        "domain_event": event_metadata,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            manifest = {
                "chain_id": "chain-1",
                "stages": [
                    {
                        "id": "presidential-directives-bot",
                        "due": True,
                        "status": "succeeded",
                        "attempt_key": "retry",
                        "run_id": run_id,
                        "output": {"sha256": report_hash},
                        "domain_event": event_metadata,
                    }
                ],
            }
            with self.assertRaisesRegex(ValueError, "event identity is not bound"):
                MODULE.materialize_selected_watcher_artifacts(
                    manifest,
                    root / "artifacts",
                    root / "inputs",
                )

    def test_local_first_config_has_no_workflow_trigger_authority(self):
        self.assertTrue(self.config["enabled"])
        self.assertFalse(self.config["runtime"]["cloudWorkflowAuthority"])
        self.assertEqual(
            self.config["activation"]["allowed"],
            ["fixture", "manual-dry-run", "manual", "scheduled"],
        )
        self.assertFalse(
            self.config["activation"]["cutoverRequiredForCanonicalRun"]
        )
        self.assertEqual(self.config["schedule"]["mode"], "launchd")
        self.assertEqual(self.config["schedule"]["localTime"], "02:00")
        self.assertEqual(
            self.config["schedule"]["timeZone"],
            "America/New_York",
        )
        for stage in self.config["stages"]:
            self.assertNotIn("workflow", stage)
            self.assertTrue(stage["command"])
            self.assertTrue(stage["output"])

    def test_interval_and_intake_reconciliation_due_logic(self):
        previous = {
            "stages": [
                {
                    "id": "case-monitor-bot",
                    "status": "succeeded",
                    "completed_at": "2026-07-24T00:00:00+00:00",
                }
            ]
        }
        case = self.config["stages"][0]
        intake = next(
            stage for stage in self.config["stages"] if stage["id"] == "public-intake"
        )
        self.assertFalse(MODULE.stage_due(case, previous, {}, self.now)[0])
        self.assertTrue(MODULE.stage_due(intake, previous, {}, self.now)[0])
        self.assertEqual(intake["due"]["kind"], "always")

    def test_persistent_input_failure_forces_watcher_due_with_exact_reason(self):
        previous = {
            "stages": [
                {
                    "id": "case-monitor-bot",
                    "status": "succeeded",
                    "completed_at": "2026-07-24T00:00:00+00:00",
                }
            ]
        }
        signals = {
            "force_stages": ["case-monitor-bot"],
            "force_stage_reasons": {
                "case-monitor-bot": "persistent watcher input is unavailable"
            },
        }
        due, reason = MODULE.stage_due(
            self.config["stages"][0],
            previous,
            signals,
            self.now,
        )
        self.assertTrue(due)
        self.assertEqual(reason, "persistent watcher input is unavailable")

    def test_watcher_input_refresh_requirements_fail_closed_and_self_heal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(
                MODULE.watcher_input_refresh_requirements(
                    root,
                    self.config["stages"],
                    self.now,
                ),
                {
                    stage_id: "persistent watcher input is missing"
                    for stage_id in MODULE.PERSISTENT_WATCHER_INPUTS
                },
            )

            (root / "case-monitor.json").write_text(
                '{"collection_status":"unavailable"}\n',
                encoding="utf-8",
            )
            (root / "presidential-directives.json").write_text(
                "[]\n",
                encoding="utf-8",
            )
            (root / "source-checker.json").write_text(
                "{",
                encoding="utf-8",
            )
            self.assertEqual(
                MODULE.watcher_input_refresh_requirements(
                    root,
                    self.config["stages"],
                    self.now,
                ),
                {
                    "case-monitor-bot": "persistent watcher input is unavailable",
                    "presidential-directives-bot": (
                        "persistent watcher input is not an object"
                    ),
                    "source-checker-bot": "persistent watcher input is malformed",
                },
            )

            valid = {
                "case-monitor.json": {
                    "schema_version": 6,
                    "checked_at": self.now.isoformat(),
                    "changes": [],
                    "source_development_modules": [],
                },
                "presidential-directives.json": {
                    "schema_version": 2,
                    "generated_at": self.now.isoformat(),
                    "counts": {},
                    "changes": [],
                    "directives": [],
                },
                "source-checker.json": {
                    "schema_version": 2,
                    "checked_at": self.now.isoformat(),
                    "counts": {},
                    "results": [],
                },
            }
            for filename, payload in valid.items():
                (root / filename).write_text(
                    json.dumps(payload) + "\n",
                    encoding="utf-8",
                )
            self.assertEqual(
                MODULE.watcher_input_refresh_requirements(
                    root,
                    self.config["stages"],
                    self.now,
                ),
                {},
            )

            valid["source-checker.json"]["schema_version"] = 1
            (root / "source-checker.json").write_text(
                json.dumps(valid["source-checker.json"]) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                MODULE.watcher_input_refresh_requirements(
                    root,
                    self.config["stages"],
                    self.now,
                ),
                {
                    "source-checker-bot": (
                        "persistent watcher input schema is invalid"
                    )
                },
            )
            valid["source-checker.json"]["schema_version"] = 2
            (root / "source-checker.json").write_text(
                json.dumps(valid["source-checker.json"]) + "\n",
                encoding="utf-8",
            )

            for filename in (
                "case-monitor.json",
                "presidential-directives.json",
            ):
                (root / filename).write_text("{}\n", encoding="utf-8")
            oversized = root / "source-checker.json"
            oversized.write_text("x" * 11, encoding="utf-8")
            with mock.patch.object(
                MODULE,
                "MAX_PERSISTENT_WATCHER_INPUT_BYTES",
                10,
            ):
                self.assertEqual(
                    MODULE.watcher_input_refresh_requirements(
                        root,
                        self.config["stages"],
                        self.now,
                    ),
                    {
                        "case-monitor-bot": (
                            "persistent watcher input schema is invalid"
                        ),
                        "presidential-directives-bot": (
                            "persistent watcher input schema is invalid"
                        ),
                        "source-checker-bot": (
                            "persistent watcher input is oversized"
                        ),
                    },
                )

    def test_watcher_input_refresh_requires_typed_current_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = {
                "case-monitor.json": {
                    "schema_version": 5,
                    "checked_at": self.now.isoformat(),
                    "changes": [],
                    "source_development_modules": [],
                },
                "presidential-directives.json": {
                    "schema_version": 2,
                    "generated_at": "not-a-time",
                    "counts": {},
                    "changes": [],
                    "directives": [],
                },
                "source-checker.json": {
                    "schema_version": True,
                    "checked_at": (
                        self.now + timedelta(minutes=11)
                    ).isoformat(),
                    "counts": {},
                    "results": [],
                },
            }
            for filename, payload in reports.items():
                (root / filename).write_text(
                    json.dumps(payload) + "\n",
                    encoding="utf-8",
                )
            self.assertEqual(
                MODULE.watcher_input_refresh_requirements(
                    root,
                    self.config["stages"],
                    self.now,
                ),
                {
                    "case-monitor-bot": (
                        "persistent watcher input schema is invalid"
                    ),
                    "presidential-directives-bot": (
                        "persistent watcher input timestamp is malformed"
                    ),
                    "source-checker-bot": (
                        "persistent watcher input schema is invalid"
                    ),
                },
            )

            reports["case-monitor.json"]["schema_version"] = 6
            reports["presidential-directives.json"]["generated_at"] = (
                self.now.isoformat()
            )
            reports["source-checker.json"]["schema_version"] = 2
            for filename, payload in reports.items():
                (root / filename).write_text(
                    json.dumps(payload) + "\n",
                    encoding="utf-8",
                )
            self.assertEqual(
                MODULE.watcher_input_refresh_requirements(
                    root,
                    self.config["stages"],
                    self.now,
                ),
                {
                    "source-checker-bot": (
                        "persistent watcher input is future-dated"
                    ),
                },
            )

            reports["case-monitor.json"]["schema_version"] = 6
            reports["case-monitor.json"]["checked_at"] = (
                self.now - timedelta(hours=24, seconds=1)
            ).isoformat()
            reports["presidential-directives.json"]["generated_at"] = ""
            reports["source-checker.json"]["schema_version"] = 2
            reports["source-checker.json"]["checked_at"] = (
                self.now - timedelta(hours=168, seconds=1)
            ).isoformat()
            for filename, payload in reports.items():
                (root / filename).write_text(
                    json.dumps(payload) + "\n",
                    encoding="utf-8",
                )
            self.assertEqual(
                MODULE.watcher_input_refresh_requirements(
                    root,
                    self.config["stages"],
                    self.now,
                ),
                {
                    "case-monitor-bot": "persistent watcher input is stale",
                    "presidential-directives-bot": (
                        "persistent watcher input is undated"
                    ),
                    "source-checker-bot": "persistent watcher input is stale",
                },
            )

    def test_review_epoch_is_biweekly_and_boundary_is_preserved(self):
        previous = {
            "baseline_commit": "abc",
            "review_epoch": {
                "last_completed_at": "2026-07-01T00:00:00+00:00",
                "boundary_commit": "def",
            },
        }
        epoch = MODULE.review_epoch(self.config, previous, {}, self.now)
        self.assertTrue(epoch["due"])
        self.assertEqual(epoch["boundary_commit"], "def")
        self.assertEqual(epoch["interval_days"], 14)

    def test_review_epoch_preserves_unresolved_findings_from_signals(self):
        unresolved = [{"id": "EPOCH-FINDING-1", "summary": "Still open"}]
        epoch = MODULE.review_epoch(
            self.config,
            {},
            {
                "comprehensive_review_completed_at": "2026-07-20T00:00:00+00:00",
                "comprehensive_review_next_due_at": "2026-08-03T00:00:00+00:00",
                "comprehensive_review_unresolved_findings": unresolved,
            },
            self.now,
        )
        self.assertEqual(epoch["unresolved_findings"], unresolved)

    def test_review_epoch_preserves_boundary_trigger_reason_and_exact_delta(self):
        changes = {
            "missing": ["framework/new-rule.md"],
            "extra": [],
            "mismatched": ["framework/FRAMEWORK.md"],
        }
        epoch = MODULE.review_epoch(
            self.config,
            {},
            {
                "force_comprehensive_review": True,
                "comprehensive_review_trigger_reason": "governing_boundary_changed",
                "comprehensive_review_boundary_changes": changes,
            },
            self.now,
        )
        self.assertEqual(epoch["due_reason"], "governing_boundary_changed")
        self.assertEqual(epoch["boundary_changes"], changes)

    def test_review_epoch_boundary_status_compares_all_governing_hashes_and_manifest(self):
        registry = {
            "schema_version": 2,
            "documents": {
                "framework": {
                    "path": "framework/FRAMEWORK.md",
                    "hash_policy": "pinned",
                    "governing": True,
                    "sha256": "a" * 64,
                },
                "checkpoint": {
                    "path": "framework/records/handoffs/current-task.md",
                    "hash_policy": "runtime",
                    "governing": False,
                },
            },
        }
        current = {
            "framework/FRAMEWORK.md": "sha256:" + "a" * 64,
            "framework/project/automation/context-routes.json": "sha256:" + "b" * 64,
        }
        status = MODULE.review_epoch_boundary_status(
            {"governing_hashes": current},
            registry,
            "b" * 64,
        )
        self.assertFalse(status["off_cycle_required"])
        self.assertEqual(status["current_governing_hashes"], current)

        changed = MODULE.review_epoch_boundary_status(
            {
                "governing_hashes": {
                    "framework/FRAMEWORK.md": "sha256:" + "c" * 64,
                }
            },
            registry,
            "b" * 64,
        )
        self.assertTrue(changed["off_cycle_required"])
        self.assertEqual(changed["mismatched"], ["framework/FRAMEWORK.md"])
        self.assertEqual(
            changed["missing"],
            ["framework/project/automation/context-routes.json"],
        )

        self_registered = json.loads(json.dumps(registry))
        self_registered["documents"]["manifest"] = {
            "path": "framework/project/automation/context-routes.json",
            "hash_policy": "pinned",
            "governing": True,
            "sha256": "b" * 64,
        }
        with self.assertRaisesRegex(ValueError, "must not self-register"):
            MODULE.review_epoch_boundary_status(
                None,
                self_registered,
                "b" * 64,
            )

    def test_lock_rejects_another_chain_and_allows_same_chain_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "run-chain.lock"
            MODULE.acquire_lock(lock, "chain-a", False)
            with self.assertRaisesRegex(RuntimeError, "chain-a"):
                MODULE.acquire_lock(lock, "chain-b", False)
            resumed = MODULE.acquire_lock(lock, "chain-a", True)
            self.assertEqual(resumed["owner_chain_id"], "chain-a")

    def test_finalize_fails_closed_without_usage_measurement(self):
        manifest = {
            "schema_version": 1,
            "stages": [
                {
                    "id": stage["id"],
                    "due": stage["id"] == "project-integrity-bot",
                    "status": "pending"
                    if stage["id"] == "project-integrity-bot"
                    else "not_due",
                    "failure_class": "none",
                    "details": "",
                }
                for stage in self.config["stages"]
            ],
            "queue_counts": {
                "integrity": 0,
                "monitoring": 0,
                "sources": 0,
                "intake": 0,
                "total": 0,
            },
            "review_epoch": {"due": False},
            "usage": {
                "hard_reserve_percent": 15,
                "soft_run_target_percent": 10,
            },
            "failures": [],
            "degradations": [],
            "lock": {
                "path": None,
                "status": "github-concurrency",
                "owner_chain_id": "chain",
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            path = directory / "manifest.json"
            results = directory / "results.json"
            path.write_text(json.dumps(manifest))
            results.write_text(
                json.dumps(
                    {
                        "project-integrity-bot": {
                            "result": "success",
                            "work_count": 3,
                        }
                    }
                )
            )
            args = type(
                "Args",
                (),
                {
                    "config": ROOT / ".github" / "run-coordinator-bot.json",
                    "manifest": path,
                    "stage_results": results,
                    "output": None,
                    "usage_remaining": None,
                    "now": "2026-07-24T08:00:00+00:00",
                },
            )()
            MODULE.finalize(args)
            final = json.loads(path.read_text())
        self.assertFalse(final["elim_decision"]["launch_recommended"])
        self.assertEqual(final["usage"]["status"], "unknown")
        self.assertEqual(final["queue_counts"]["integrity"], 3)

    def test_finalize_enforces_hard_reserve_and_places_elim_last(self):
        manifest = {
            "schema_version": 1,
            "stages": [
                {
                    "id": stage["id"],
                    "due": False,
                    "status": "not_due",
                    "failure_class": "none",
                    "details": "",
                }
                for stage in self.config["stages"]
            ],
            "queue_counts": {
                "integrity": 1,
                "monitoring": 0,
                "sources": 0,
                "intake": 0,
                "total": 1,
            },
            "review_epoch": {"due": True},
            "llm_launch_allowed": True,
            "usage": {
                "hard_reserve_percent": 15,
                "soft_run_target_percent": 10,
            },
            "failures": [],
            "degradations": [],
            "lock": {
                "path": None,
                "status": "github-concurrency",
                "owner_chain_id": "chain",
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            path = directory / "manifest.json"
            results = directory / "results.json"
            path.write_text(json.dumps(manifest))
            results.write_text("{}")
            args = type(
                "Args",
                (),
                {
                    "config": ROOT / ".github" / "run-coordinator-bot.json",
                    "manifest": path,
                    "stage_results": results,
                    "output": None,
                    "usage_remaining": 15.0,
                    "now": "2026-07-24T08:00:00+00:00",
                },
            )()
            MODULE.finalize(args)
            reserved = json.loads(path.read_text())
            args.usage_remaining = 24.0
            path.write_text(json.dumps(manifest))
            MODULE.finalize(args)
            available = json.loads(path.read_text())
        self.assertFalse(reserved["elim_decision"]["launch_recommended"])
        self.assertTrue(available["elim_decision"]["launch_recommended"])
        self.assertTrue(available["elim_decision"]["last_substantive_stage"])
        self.assertEqual(
            available["next_action"],
            "The governed local production cycle may launch Elim.",
        )

    def test_failed_bot_authorizes_only_selected_safety_zero_repair(self):
        failed_stage = "source-checker-bot"
        manifest = {
            "schema_version": 1,
            "chain_id": "chain-repair",
            "llm_launch_allowed": True,
            "stages": [
                {
                    "id": stage["id"],
                    "due": stage["id"] == failed_stage,
                    "status": "failed" if stage["id"] == failed_stage else "not_due",
                    "failure_class": (
                        "blocking" if stage["id"] == failed_stage else "none"
                    ),
                    "details": (
                        "Source scan failed."
                        if stage["id"] == failed_stage
                        else ""
                    ),
                    "work_count": 0,
                }
                for stage in self.config["stages"]
            ],
            "queue_counts": {
                "integrity": 0,
                "monitoring": 0,
                "sources": 0,
                "intake": 0,
                "total": 1,
            },
            "work_queue": {
                "ready_for_elim": True,
                "launch_recommended": True,
                "problems": [],
                "next_item": {
                    "id": "repair-source",
                    "kind": "bot_failure",
                    "safety_class": 0,
                    "eligible_for_elim": True,
                    "source": {"bot": {"id": failed_stage}},
                },
            },
            "context_packet": {"profile": "integrity_reconciliation"},
            "review_epoch": {"due": True},
            "usage": {
                "hard_reserve_percent": 15,
                "soft_run_target_percent": 10,
            },
            "failures": [],
            "degradations": [],
            "lock": {
                "path": None,
                "status": "released-by-workflow",
                "owner_chain_id": "chain-repair",
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            path = directory / "manifest.json"
            results = directory / "results.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            results.write_text("{}\n", encoding="utf-8")
            args = type(
                "Args",
                (),
                {
                    "config": ROOT / ".github/run-coordinator-bot.json",
                    "manifest": path,
                    "stage_results": results,
                    "output": None,
                    "usage_remaining": 90.0,
                    "now": "2026-07-24T08:00:00+00:00",
                },
            )()
            MODULE.finalize(args)
            final = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(final["elim_decision"]["launch_recommended"])
        self.assertIn("repair-only", final["elim_decision"]["reason"])
        self.assertEqual(final["elim_decision"]["blockers"], [])
        self.assertFalse(final["elim_decision"]["profile"]["full_context"])
        self.assertTrue(final["review_epoch"]["due"])
        self.assertEqual(final["status"], "degraded")
        self.assertEqual(final["failures"][0]["stage"], failed_stage)

    def test_host_refinalize_preserves_degraded_stage_and_queue_counts(self):
        stages = [
            {
                "id": stage["id"],
                "due": stage["id"] in {
                    "case-monitor-bot",
                    "source-checker-bot",
                },
                "status": (
                    "succeeded"
                    if stage["id"] == "case-monitor-bot"
                    else "degraded"
                    if stage["id"] == "source-checker-bot"
                    else "not_due"
                ),
                "failure_class": (
                    "degraded"
                    if stage["id"] == "source-checker-bot"
                    else "none"
                ),
                "details": (
                    "Provider throttled the scan."
                    if stage["id"] == "source-checker-bot"
                    else ""
                ),
                "work_count": (
                    2
                    if stage["id"] == "case-monitor-bot"
                    else 4
                    if stage["id"] == "source-checker-bot"
                    else 0
                ),
            }
            for stage in self.config["stages"]
        ]
        manifest = {
            "schema_version": 1,
            "chain_id": "chain",
            "llm_launch_allowed": True,
            "stages": stages,
            "queue_counts": {
                "integrity": 0,
                "monitoring": 2,
                "sources": 4,
                "intake": 0,
                "total": 6,
            },
            "review_epoch": {"due": False},
            "usage": {
                "hard_reserve_percent": 15,
                "soft_run_target_percent": 10,
            },
            "failures": [],
            "degradations": [
                {
                    "stage": "source-checker-bot",
                    "classification": "degraded",
                    "message": "Provider throttled the scan.",
                }
            ],
            "lock": {
                "path": None,
                "status": "released-by-workflow",
                "owner_chain_id": "chain",
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            path = directory / "manifest.json"
            results = directory / "results.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            results.write_text("{}\n", encoding="utf-8")
            args = type(
                "Args",
                (),
                {
                    "config": ROOT / ".github" / "run-coordinator-bot.json",
                    "manifest": path,
                    "stage_results": results,
                    "output": None,
                    "usage_remaining": 80.0,
                    "now": "2026-07-24T08:00:00+00:00",
                },
            )()
            MODULE.finalize(args)
            final = json.loads(path.read_text(encoding="utf-8"))
        source = next(
            stage
            for stage in final["stages"]
            if stage["id"] == "source-checker-bot"
        )
        self.assertEqual(source["status"], "degraded")
        self.assertEqual(final["status"], "degraded")
        self.assertEqual(final["queue_counts"]["monitoring"], 2)
        self.assertEqual(final["queue_counts"]["sources"], 4)
        self.assertEqual(len(final["degradations"]), 1)
        self.assertEqual(final["failures"], [])

    def test_host_refinalize_blocks_unapplied_local_queue_overrides(self):
        manifest = {
            "schema_version": 1,
            "chain_id": "chain",
            "llm_launch_allowed": True,
            "stages": [
                {
                    "id": stage["id"],
                    "due": False,
                    "status": "not_due",
                    "failure_class": "none",
                    "details": "",
                    "work_count": 0,
                }
                for stage in self.config["stages"]
            ],
            "queue_counts": {
                "integrity": 0,
                "monitoring": 0,
                "sources": 0,
                "intake": 0,
                "total": 1,
            },
            "work_queue": {
                "ready_for_elim": True,
                "launch_recommended": True,
                "problems": [],
                "user_overrides": {
                    "applied": [],
                    "unmatched": [],
                    "request_sha256": MODULE.json_hash({}),
                },
            },
            "user_overrides": {
                "work-integrity-123456789abc": {
                    "source": "user-local-console",
                    "suppressed": True,
                    "reason": "Review later.",
                }
            },
            "review_epoch": {"due": False},
            "usage": {
                "hard_reserve_percent": 15,
                "soft_run_target_percent": 10,
            },
            "failures": [],
            "degradations": [],
            "lock": {
                "path": None,
                "status": "released-by-workflow",
                "owner_chain_id": "chain",
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            path = directory / "manifest.json"
            results = directory / "results.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            results.write_text("{}\n", encoding="utf-8")
            args = type(
                "Args",
                (),
                {
                    "config": ROOT / ".github" / "run-coordinator-bot.json",
                    "manifest": path,
                    "stage_results": results,
                    "output": None,
                    "usage_remaining": 80.0,
                    "now": "2026-07-24T08:00:00+00:00",
                },
            )()
            MODULE.finalize(args)
            final = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(final["elim_decision"]["launch_recommended"])
        self.assertEqual(final["status"], "blocked")
        self.assertTrue(
            any(
                "exact queue selection" in blocker
                for blocker in final["elim_decision"]["blockers"]
            )
        )

    def test_push_trigger_cannot_launch_elim_even_with_ready_work(self):
        manifest = {
            "schema_version": 1,
            "trigger": "push",
            "llm_launch_allowed": False,
            "stages": [
                {
                    "id": stage["id"],
                    "due": False,
                    "status": "not_due",
                    "failure_class": "none",
                    "details": "",
                }
                for stage in self.config["stages"]
            ],
            "queue_counts": {
                "integrity": 0,
                "monitoring": 0,
                "sources": 0,
                "intake": 0,
                "total": 1,
            },
            "work_queue": {
                "ready_for_elim": True,
                "launch_recommended": True,
                "problems": [],
            },
            "review_epoch": {"due": False},
            "usage": {
                "hard_reserve_percent": 15,
                "soft_run_target_percent": 10,
            },
            "failures": [],
            "degradations": [],
            "lock": {
                "path": None,
                "status": "github-concurrency",
                "owner_chain_id": "chain",
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            path = directory / "manifest.json"
            results = directory / "results.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            results.write_text("{}", encoding="utf-8")
            args = type(
                "Args",
                (),
                {
                    "config": ROOT / ".github" / "run-coordinator-bot.json",
                    "manifest": path,
                    "stage_results": results,
                    "output": None,
                    "usage_remaining": 90.0,
                    "now": "2026-07-24T08:00:00+00:00",
                },
            )()
            MODULE.finalize(args)
            final = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(final["elim_decision"]["launch_recommended"])
        self.assertIn("deterministic refresh only", final["elim_decision"]["reason"])

    def test_attach_context_rejects_wrong_profile_for_comprehensive_chain(self):
        manifest = {
            "schema_version": 1,
            "final_revision": "a" * 40,
            "elim_decision": {"profile": {"full_context": True}},
            "queue_counts": {"total": 0},
            "review_epoch": {"due": True},
            "status": "complete",
        }
        queue = {
            "schema_version": 1,
            "repository_revision": "a" * 40,
            "ready_for_elim": True,
            "launch_recommended": True,
            "counts": {"total": 1},
            "items": [
                {
                    "id": "epoch-1",
                    "kind": "comprehensive_review",
                    "eligible_for_elim": True,
                }
            ],
            "governance_discovery": self.governance_projection(),
            "problems": [],
        }
        context = {
            "schema_version": 2,
            "status": "ready",
            "profile": "change_audit",
            "repository_revision": "a" * 40,
            "provenance_complete": True,
            "limits": {"actual_bytes": 100, "max_bytes": 1000},
            "selection": {
                "work_item_id": "epoch-1",
                "kind": "comprehensive_review",
                "canonical_record": None,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            manifest_path = directory / "manifest.json"
            queue_path = directory / "queue.json"
            context_path = directory / "context.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            queue_path.write_text(json.dumps(queue), encoding="utf-8")
            context_path.write_text(json.dumps(context), encoding="utf-8")
            args = type(
                "Args",
                (),
                {
                    "manifest": manifest_path,
                    "queue": queue_path,
                    "context": context_path,
                    "output": None,
                },
            )()
            with self.assertRaisesRegex(ValueError, "requires context profile"):
                MODULE.attach_context(args)
            args.context = None
            with self.assertRaisesRegex(ValueError, "has no context packet"):
                MODULE.attach_context(args)

    def test_attach_context_lets_safety_zero_repair_preempt_due_epoch(self):
        manifest = {
            "schema_version": 1,
            "final_revision": "a" * 40,
            "elim_decision": {
                "launch_recommended": False,
                "profile": {"full_context": True},
            },
            "queue_counts": {"total": 0},
            "review_epoch": {"due": True},
            "status": "blocked",
        }
        selected = {
            "id": "repair-source",
            "kind": "bot_failure",
            "safety_class": 0,
            "eligible_for_elim": True,
            "source": {"bot": {"id": "source-checker-bot"}},
        }
        queue = {
            "schema_version": 1,
            "repository_revision": "a" * 40,
            "ready_for_elim": True,
            "launch_recommended": True,
            "counts": {"total": 2},
            "items": [
                selected,
                {
                    "id": "epoch-1",
                    "kind": "comprehensive_review",
                    "eligible_for_elim": True,
                },
            ],
            "governance_discovery": self.governance_projection(
                ordinary_count=2
            ),
            "problems": [],
        }
        context = {
            "schema_version": 2,
            "status": "ready",
            "profile": "integrity_reconciliation",
            "repository_revision": "a" * 40,
            "provenance_complete": True,
            "limits": {"actual_bytes": 100, "max_bytes": 1000},
            "selection": {
                "work_item_id": "repair-source",
                "kind": "bot_failure",
                "canonical_record": None,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            manifest_path = directory / "manifest.json"
            queue_path = directory / "queue.json"
            context_path = directory / "context.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            queue_path.write_text(json.dumps(queue), encoding="utf-8")
            context_path.write_text(json.dumps(context), encoding="utf-8")
            args = type(
                "Args",
                (),
                {
                    "manifest": manifest_path,
                    "queue": queue_path,
                    "context": context_path,
                    "output": None,
                },
            )()
            MODULE.attach_context(args)
            attached = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            attached["work_queue"]["selected_work_item_id"],
            "repair-source",
        )
        self.assertFalse(attached["elim_decision"]["profile"]["full_context"])
        self.assertTrue(attached["review_epoch"]["due"])

    def test_attach_context_binds_selected_item_context_and_model(self):
        manifest = {
            "schema_version": 1,
            "final_revision": "a" * 40,
            "elim_decision": {
                "launch_recommended": True,
                "profile": {"full_context": False},
            },
            "queue_counts": {"total": 0},
            "review_epoch": {"due": False},
            "status": "complete",
        }
        selected = {
            "id": "change-1",
            "kind": "change_audit",
            "eligible_for_elim": True,
            "source": {
                "identifier": "JUD-009",
                "canonicalRecord": "areas/JUD/issues/JUD-009.md",
            },
        }
        queue = {
            "schema_version": 1,
            "repository_revision": "a" * 40,
            "ready_for_elim": True,
            "launch_recommended": True,
            "counts": {"total": 2},
            "items": [
                {
                    "id": "human-1",
                    "kind": "integrity",
                    "eligible_for_elim": False,
                },
                selected,
            ],
            "governance_discovery": self.governance_projection(),
            "problems": [],
        }
        context = {
            "schema_version": 2,
            "profile": "change_audit",
            "repository_revision": "a" * 40,
            "provenance_complete": True,
            "limits": {"actual_bytes": 100, "max_bytes": 1000},
            "selection": {
                "work_item_id": "change-1",
                "kind": "change_audit",
                "canonical_record": "areas/JUD/issues/JUD-009.md",
            },
            "issue_dossier": {
                "issue_id": "JUD-009",
                "issue_page": {"path": "areas/JUD/issues/JUD-009.md"},
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            manifest_path = directory / "manifest.json"
            queue_path = directory / "queue.json"
            context_path = directory / "context.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            queue_path.write_text(json.dumps(queue), encoding="utf-8")
            context_path.write_text(json.dumps(context), encoding="utf-8")
            args = type(
                "Args",
                (),
                {
                    "manifest": manifest_path,
                    "queue": queue_path,
                    "context": context_path,
                    "output": None,
                },
            )()
            MODULE.attach_context(args)
            attached = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(attached["work_queue"]["next_item"], selected)
        self.assertEqual(attached["work_queue"]["selected_work_item_id"], "change-1")
        self.assertEqual(
            attached["work_queue"]["user_overrides"]["request_sha256"],
            MODULE.json_hash({}),
        )
        self.assertEqual(attached["context_packet"]["work_item_id"], "change-1")
        self.assertEqual(attached["context_packet"]["issue_id"], "JUD-009")
        self.assertEqual(
            attached["context_packet"]["canonical_record"],
            "areas/JUD/issues/JUD-009.md",
        )
        self.assertEqual(attached["context_packet"]["selection"], context["selection"])
        self.assertEqual(attached["elim_decision"]["profile"]["id"], "substantive")
        self.assertEqual(
            attached["elim_decision"]["profile"]["model"],
            self.config["llmRouting"]["profiles"]["substantive"]["model"],
        )

    def test_attach_context_treats_candidate_research_as_nonissue_work(self):
        manifest = {
            "schema_version": 1,
            "final_revision": "a" * 40,
            "elim_decision": {
                "launch_recommended": True,
                "profile": {"full_context": False},
            },
            "queue_counts": {"total": 0},
            "review_epoch": {"due": False},
            "status": "complete",
        }
        queue = {
            "schema_version": 1,
            "repository_revision": "a" * 40,
            "ready_for_elim": True,
            "launch_recommended": True,
            "counts": {"total": 1},
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
            ],
            "governance_discovery": self.governance_projection(),
            "problems": [],
        }
        context = {
            "schema_version": 2,
            "profile": "candidate_research",
            "repository_revision": "a" * 40,
            "provenance_complete": True,
            "limits": {"actual_bytes": 100, "max_bytes": 1000},
            "selection": {
                "work_item_id": "candidate-1",
                "kind": "candidate_research",
                "canonical_record": "https://github.com/Thorncrag/ARRP/issues/255",
            },
            "issue_dossier": None,
        }
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            manifest_path = directory / "manifest.json"
            queue_path = directory / "queue.json"
            context_path = directory / "context.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            queue_path.write_text(json.dumps(queue), encoding="utf-8")
            context_path.write_text(json.dumps(context), encoding="utf-8")
            args = type(
                "Args",
                (),
                {
                    "manifest": manifest_path,
                    "queue": queue_path,
                    "context": context_path,
                    "output": None,
                },
            )()
            MODULE.attach_context(args)
            attached = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(attached["context_packet"]["work_item_id"], "candidate-1")
        self.assertIsNone(attached["context_packet"]["issue_id"])
        self.assertEqual(
            attached["context_packet"]["canonical_record"],
            "https://github.com/Thorncrag/ARRP/issues/255",
        )
        self.assertEqual(attached["elim_decision"]["profile"]["id"], "substantive")

    def test_attach_context_projects_governance_and_compact_gap_obligations(self):
        manifest = {
            "schema_version": 1,
            "final_revision": "a" * 40,
            "elim_decision": {
                "launch_recommended": False,
                "profile": {"full_context": False},
            },
            "queue_counts": {"total": 0},
            "review_epoch": {"due": False},
            "status": "complete",
            "next_action": "Wait.",
        }
        gap_item = self.gap_queue_item()
        governance = self.governance_projection(
            ordinary_count=0,
            current=True,
        )
        queue = {
            "schema_version": 1,
            "repository_revision": "a" * 40,
            "ready_for_elim": True,
            "launch_recommended": False,
            "counts": {
                "total": 1,
                "gap_obligations": 1,
                "governance_discovery": 0,
            },
            "items": [gap_item],
            "governance_discovery": governance,
            "problems": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            manifest_path = directory / "manifest.json"
            queue_path = directory / "queue.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            queue_path.write_text(json.dumps(queue), encoding="utf-8")
            args = type(
                "Args",
                (),
                {
                    "manifest": manifest_path,
                    "queue": queue_path,
                    "context": None,
                    "output": None,
                },
            )()
            MODULE.attach_context(args)
            attached = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(
            attached["work_queue"]["governance_discovery"],
            governance,
        )
        self.assertEqual(len(attached["work_queue"]["gap_obligations"]), 1)
        projected = attached["work_queue"]["gap_obligations"][0]
        self.assertEqual(projected["obligation_id"], "GAP-001")
        self.assertEqual(projected["authority_disposition"], "forbidden")
        self.assertEqual(
            projected["canonical_detail"],
            "framework/records/automation/elim-run-log.md",
        )
        self.assertNotIn("evidence", projected)
        self.assertNotIn("reasoning", projected)
        self.assertNotIn("consequence", projected)

    def test_gap_and_governance_projections_fail_closed_on_malformed_or_unbounded_data(
        self,
    ):
        gap_item = self.gap_queue_item()
        with self.assertRaisesRegex(ValueError, "projection bound"):
            MODULE.gap_obligation_projections(
                {"items": [gap_item]},
                maximum=0,
            )

        malformed_gap = json.loads(json.dumps(gap_item))
        malformed_gap["source"]["obligation_projection"]["evidence"] = [
            "Narrative belongs in the canonical detail record."
        ]
        with self.assertRaisesRegex(ValueError, "compact canonical projection"):
            MODULE.gap_obligation_projections(
                {"items": [malformed_gap]},
                maximum=512,
            )

        malformed_governance = self.governance_projection()
        malformed_governance["minimum_interval_hours"] = 24
        with self.assertRaisesRegex(ValueError, "differs from coordinator policy"):
            MODULE.governance_discovery_projection(
                {
                    "items": [],
                    "governance_discovery": malformed_governance,
                },
                self.config,
            )

    def test_attach_context_rejects_missing_stale_unbounded_or_unbound_packets(self):
        manifest = {
            "schema_version": 1,
            "final_revision": "a" * 40,
            "elim_decision": {
                "launch_recommended": True,
                "profile": {"full_context": False},
            },
            "queue_counts": {"total": 0},
            "review_epoch": {"due": False},
            "status": "complete",
        }
        queue = {
            "schema_version": 1,
            "repository_revision": "a" * 40,
            "ready_for_elim": True,
            "launch_recommended": True,
            "counts": {"total": 1},
            "items": [
                {
                    "id": "development-1",
                    "kind": "issue_development",
                    "eligible_for_elim": True,
                    "source": {
                        "identifier": "TEST-001",
                        "canonicalRecord": "areas/TEST/issues/TEST-001.md",
                    },
                }
            ],
            "governance_discovery": self.governance_projection(),
            "problems": [],
        }
        valid = {
            "schema_version": 2,
            "profile": "issue_development",
            "repository_revision": "a" * 40,
            "provenance_complete": True,
            "limits": {"actual_bytes": 100, "max_bytes": 1000},
            "selection": {
                "work_item_id": "development-1",
                "kind": "issue_development",
                "canonical_record": "areas/TEST/issues/TEST-001.md",
            },
            "issue_dossier": {
                "issue_id": "TEST-001",
                "issue_page": {"path": "areas/TEST/issues/TEST-001.md"},
            },
        }
        variants = (
            ("schema", {**valid, "schema_version": 1}, "blocked or unsupported"),
            (
                "provenance",
                {**valid, "provenance_complete": False},
                "provenance is incomplete",
            ),
            (
                "limits",
                {**valid, "limits": {"actual_bytes": 1001, "max_bytes": 1000}},
                "byte limits are invalid",
            ),
            (
                "revision",
                {**valid, "repository_revision": "b" * 40},
                "revision differs",
            ),
            (
                "profile",
                {**valid, "profile": "change_audit"},
                "requires context profile",
            ),
            (
                "issue",
                {**valid, "issue_dossier": {"issue_id": "TEST-002"}},
                "requires issue TEST-001",
            ),
            (
                "selection",
                {
                    **valid,
                    "selection": {
                        **valid["selection"],
                        "work_item_id": "development-2",
                    },
                },
                "selection differs",
            ),
            (
                "canonical",
                {
                    **valid,
                    "issue_dossier": {
                        "issue_id": "TEST-001",
                        "issue_page": {
                            "path": "areas/TEST/issues/TEST-002.md",
                        },
                    },
                },
                "requires canonical record",
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            queue_path = directory / "queue.json"
            queue_path.write_text(json.dumps(queue), encoding="utf-8")
            for name, context, expected in variants:
                with self.subTest(name=name):
                    manifest_path = directory / f"manifest-{name}.json"
                    context_path = directory / f"context-{name}.json"
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    context_path.write_text(json.dumps(context), encoding="utf-8")
                    args = type(
                        "Args",
                        (),
                        {
                            "manifest": manifest_path,
                            "queue": queue_path,
                            "context": context_path,
                            "output": None,
                        },
                    )()
                    with self.assertRaisesRegex(ValueError, expected):
                        MODULE.attach_context(args)

            missing_path = directory / "manifest-missing.json"
            missing_path.write_text(json.dumps(manifest), encoding="utf-8")
            args = type(
                "Args",
                (),
                {
                    "manifest": missing_path,
                    "queue": queue_path,
                    "context": None,
                    "output": None,
                },
            )()
            with self.assertRaisesRegex(ValueError, "has no context packet"):
                MODULE.attach_context(args)

            stale_queue = {**queue, "repository_revision": "b" * 40}
            stale_queue_path = directory / "queue-stale.json"
            stale_queue_path.write_text(json.dumps(stale_queue), encoding="utf-8")
            stale_manifest_path = directory / "manifest-stale-queue.json"
            stale_manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            valid_context_path = directory / "context-valid.json"
            valid_context_path.write_text(json.dumps(valid), encoding="utf-8")
            args = type(
                "Args",
                (),
                {
                    "manifest": stale_manifest_path,
                    "queue": stale_queue_path,
                    "context": valid_context_path,
                    "output": None,
                },
            )()
            with self.assertRaisesRegex(ValueError, "queue repository revision differs"):
                MODULE.attach_context(args)

    def test_attach_repository_gates_marks_only_applicable_gate_on_attempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            manifest_path = directory / "run-chain.json"
            gate_path = directory / "repository-gates.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "trigger": "scheduled",
                        "updated_at": "2026-07-28T00:00:00Z",
                        "stages": [
                            {"id": "project-console-progress-bot"},
                            {"id": "project-integrity-bot"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            gate_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "availability": "current",
                        "complete": True,
                        "count": 2,
                        "items": [
                            {
                                "gate_id": "GATE-SCHEDULED",
                                "blocks_automation": True,
                                "affected_stages": ["project-console-progress-bot"],
                                "next_run_scope": ["scheduled"],
                            },
                            {
                                "gate_id": "GATE-MANUAL",
                                "blocks_automation": True,
                                "affected_stages": ["project-integrity-bot"],
                                "next_run_scope": ["manual"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            args = type(
                "Args",
                (),
                {
                    "manifest": manifest_path,
                    "repository_gates": gate_path,
                    "output": None,
                },
            )()
            MODULE.attach_repository_gates(args)
            attached = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            attached["repository_gates"]["applied_gate_ids"],
            ["GATE-SCHEDULED"],
        )
        by_id = {
            item["gate_id"]: item["affected_latest_attempt"]
            for item in attached["repository_gates"]["items"]
        }
        self.assertTrue(by_id["GATE-SCHEDULED"])
        self.assertFalse(by_id["GATE-MANUAL"])


if __name__ == "__main__":
    unittest.main()
