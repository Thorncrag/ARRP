import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


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

    def test_stage_order_ends_with_integrity_and_elim_is_not_a_bot_stage(self):
        MODULE.validate_config(self.config)
        ids = [stage["id"] for stage in self.config["stages"]]
        self.assertEqual(ids[-1], "project-integrity-bot")
        self.assertNotIn("elim", ids)

    def test_comprehensive_queue_uses_the_full_context_profile(self):
        workflow = (
            ROOT / ".github" / "workflows" / "run-coordinator-bot.yml"
        ).read_text()
        self.assertIn(
            "scripts/select_elim_context_route.py",
            workflow,
        )

    def test_workflow_forces_off_cycle_epoch_and_carries_unresolved_findings(self):
        workflow = (
            ROOT / ".github" / "workflows" / "run-coordinator-bot.yml"
        ).read_text()
        self.assertIn("review_epoch_boundary_status(", workflow)
        self.assertIn('payload["force_comprehensive_review"] = True', workflow)
        self.assertIn('"governing_boundary_changed"', workflow)
        self.assertIn('"comprehensive_review_boundary_changes"', workflow)
        self.assertIn('"comprehensive_review_unresolved_findings"', workflow)

    def test_main_pushes_enter_the_chain_not_individual_bots(self):
        coordinator = (
            ROOT / ".github" / "workflows" / "run-coordinator-bot.yml"
        ).read_text()
        self.assertIn("  push:\n    branches:\n      - main", coordinator)
        self.assertIn('"allow_elim_launch": allow_elim_launch', coordinator)
        self.assertIn("launch_policy[\"authorizedTriggers\"]", coordinator)
        self.assertIn(
            "push",
            self.config["llmLaunchPolicy"]["deterministicOnlyTriggers"],
        )
        self.assertNotIn(
            "push",
            self.config["llmLaunchPolicy"]["authorizedTriggers"],
        )
        for name in ("project-integrity.yml", "project-console-progress.yml"):
            workflow = (ROOT / ".github" / "workflows" / name).read_text()
            self.assertNotIn("  push:\n", workflow)

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
                    "path": "framework/logs/CURRENT_AUDIT.md",
                    "hash_policy": "runtime",
                    "governing": False,
                },
            },
        }
        current = {
            "framework/FRAMEWORK.md": "sha256:" + "a" * 64,
            "framework/context-routes.json": "sha256:" + "b" * 64,
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
            ["framework/context-routes.json"],
        )

        self_registered = json.loads(json.dumps(registry))
        self_registered["documents"]["manifest"] = {
            "path": "framework/context-routes.json",
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


if __name__ == "__main__":
    unittest.main()
