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

    def test_main_pushes_enter_the_chain_not_individual_bots(self):
        coordinator = (
            ROOT / ".github" / "workflows" / "run-coordinator-bot.yml"
        ).read_text()
        self.assertIn("  push:\n    branches:\n      - main", coordinator)
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

    def test_attach_context_rejects_wrong_profile_for_comprehensive_chain(self):
        manifest = {
            "schema_version": 1,
            "elim_decision": {"profile": {"full_context": True}},
            "queue_counts": {"total": 0},
            "review_epoch": {"due": True},
            "status": "complete",
        }
        queue = {
            "schema_version": 1,
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
            "schema_version": 1,
            "status": "ready",
            "profile": "change_audit",
            "provenance_complete": True,
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
            with self.assertRaisesRegex(ValueError, "comprehensive full context"):
                MODULE.attach_context(args)
            args.context = None
            with self.assertRaisesRegex(ValueError, "no context packet"):
                MODULE.attach_context(args)


if __name__ == "__main__":
    unittest.main()
