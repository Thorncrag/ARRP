from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts import build_automation_health_projection as MODULE


ROOT = Path(__file__).resolve().parents[1]


def run(
    run_id: int,
    *,
    event: str = "schedule",
    conclusion: str | None = "success",
    created_at: str = "2026-07-26T04:17:00Z",
) -> dict:
    return {
        "id": run_id,
        "name": "ARRP Run Coordinator Bot",
        "event": event,
        "status": "completed" if conclusion is not None else "in_progress",
        "conclusion": conclusion,
        "created_at": created_at,
        "run_started_at": created_at,
        "updated_at": created_at,
        "head_branch": "main",
        "head_sha": f"{run_id:040x}",
        "html_url": f"https://github.com/Thorncrag/ARRP/actions/runs/{run_id}",
    }


class AutomationHealthProjectionTests(unittest.TestCase):
    def test_workflow_run_failure_is_projected_without_run_chain_output(self):
        payload = MODULE.workflow_run_projection(
            {"workflow_run": run(123, conclusion="failure")}
        )
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["chain_id"], "cloud-run-123")
        self.assertEqual(
            payload["failure"]["stage"],
            "github-actions-run-coordinator",
        )
        self.assertIn("failure", payload["failure"]["message"])

    def test_successful_workflow_run_clears_cloud_failure_state(self):
        payload = MODULE.workflow_run_projection(
            {"workflow_run": run(124)}
        )
        self.assertEqual(payload["status"], "healthy")
        self.assertIsNone(payload["failure"])
        self.assertEqual(payload["workflow_run_id"], "124")

    def test_watchdog_accepts_a_recent_successful_daily_run(self):
        scheduled = run(125)
        payload = MODULE.watchdog_projection(
            {"workflow_runs": [scheduled]},
            {"workflow_runs": [scheduled]},
            now=datetime(2026, 7, 26, 10, 47, tzinfo=timezone.utc),
            maximum_age_hours=18,
        )
        self.assertEqual(payload["status"], "healthy")
        self.assertEqual(
            payload["heartbeat"]["scheduled_run_age_hours"],
            6.5,
        )

    def test_watchdog_reports_a_missing_or_stale_daily_run(self):
        stale = run(126, created_at="2026-07-25T04:17:00Z")
        later_manual = run(
            127,
            event="workflow_dispatch",
            created_at="2026-07-26T09:00:00Z",
        )
        payload = MODULE.watchdog_projection(
            {"workflow_runs": [stale]},
            {"workflow_runs": [later_manual]},
            now=datetime(2026, 7, 26, 10, 47, tzinfo=timezone.utc),
            maximum_age_hours=18,
        )
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["workflow_run_id"], "126")
        self.assertEqual(
            payload["failure"]["stage"],
            "scheduled-chain-heartbeat",
        )
        self.assertIn("beyond", payload["failure"]["message"])

    def test_watchdog_retains_a_newer_failed_run(self):
        scheduled = run(128)
        later_failure = run(
            129,
            event="push",
            conclusion="timed_out",
            created_at="2026-07-26T09:00:00Z",
        )
        payload = MODULE.watchdog_projection(
            {"workflow_runs": [scheduled]},
            {"workflow_runs": [later_failure]},
            now=datetime(2026, 7, 26, 10, 47, tzinfo=timezone.utc),
            maximum_age_hours=18,
        )
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["workflow_run_id"], "129")
        self.assertEqual(payload["conclusion"], "timed_out")

    def test_workflow_has_three_independent_projection_triggers(self):
        source = (
            ROOT / ".github/workflows/automation-health-projection.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("workflow_run:", source)
        self.assertIn("repository_dispatch:", source)
        self.assertIn('cron: "47 10 * * *"', source)
        self.assertIn("workflow_dispatch:", source)
        self.assertIn("--mode workflow-run", source)
        self.assertIn("--mode watchdog", source)
        self.assertIn("arrp-host-status", source)
        self.assertEqual(
            source.count("scripts/publish_project_console_progress.py"),
            3,
        )


if __name__ == "__main__":
    unittest.main()
