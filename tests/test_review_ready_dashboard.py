import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_review_ready_dashboard.py"
SPEC = importlib.util.spec_from_file_location("review_ready_dashboard", str(SCRIPT))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PUBLISH_SCRIPT = ROOT / "scripts" / "publish_review_ready_dashboard.py"
PUBLISH_SPEC = importlib.util.spec_from_file_location("publish_review_ready_dashboard", str(PUBLISH_SCRIPT))
PUBLISH_MODULE = importlib.util.module_from_spec(PUBLISH_SPEC)
PUBLISH_SPEC.loader.exec_module(PUBLISH_MODULE)


class ReviewReadyDashboardTests(unittest.TestCase):
    def setUp(self):
        self.config = MODULE.read_json(ROOT / "tests" / "fixtures" / "progress-config.json")
        self.raw = MODULE.read_json(ROOT / "tests" / "fixtures" / "progress-project.json")
        self.history = MODULE.read_json(ROOT / "tests" / "fixtures" / "progress-history.json")

    def test_filters_to_proposals_and_uses_status_as_readiness_authority(self):
        title, items = MODULE.parse_items(self.raw, self.config)
        self.assertEqual(title, "American Restoration and Resilience Project")
        self.assertEqual(len(items), 4)
        self.assertEqual(sum(item["ready"] for item in items), 1)
        mismatch = next(item for item in items if item["identifier"] == "JUD-011")
        self.assertFalse(mismatch["ready"])
        self.assertEqual(len(mismatch["warnings"]), 1)

    def test_builds_metrics_history_and_forecast_inputs(self):
        title, items = MODULE.parse_items(self.raw, self.config)
        payload = MODULE.build_dashboard_payload(title, items, self.history, self.config, date(2026, 7, 15))
        self.assertEqual(payload["metrics"]["ready"], 1)
        self.assertEqual(payload["metrics"]["total"], 4)
        self.assertEqual(payload["metrics"]["remaining"], 3)
        self.assertEqual(payload["metrics"]["percentReady"], 25.0)
        self.assertEqual(payload["history"][-1]["date"], "2026-07-15")
        self.assertEqual(len(payload["warnings"]), 1)
        self.assertTrue(payload["movement"]["available"])
        self.assertEqual(payload["movement"]["scoresImproved"], 2)
        self.assertEqual(payload["movement"]["netScoreChange"], 13.0)
        required = next(row for row in MODULE.scenario_rows(payload) if row[0] == "Pace required for official target")
        self.assertEqual(required[2], "Dec 31, 2026 (target date)")

    def test_dashboard_build_writes_github_renderable_files(self):
        title, items = MODULE.parse_items(self.raw, self.config)
        payload = MODULE.build_dashboard_payload(title, items, self.history, self.config, date(2026, 7, 15))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "site"
            MODULE.write_dashboard(output, payload)
            self.assertTrue((output / "PROGRESS.md").is_file())
            self.assertTrue((output / "assets" / "trajectory.svg").is_file())
            self.assertTrue((output / "assets" / "status-distribution.svg").is_file())
            self.assertTrue((output / "assets" / "score-proximity.svg").is_file())
            self.assertTrue((output / "assets" / "area-progress.svg").is_file())
            saved = json.loads((output / "data" / "dashboard.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["metrics"]["total"], 4)
            markdown = (output / "PROGRESS.md").read_text(encoding="utf-8")
            self.assertIn("Official goal", markdown)
            self.assertIn("Completion-date scenarios", markdown)

    def test_publisher_collects_only_generated_branch_files(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "assets").mkdir()
            (source / "PROGRESS.md").write_text("# Progress\n", encoding="utf-8")
            (source / "assets" / "chart.svg").write_text("<svg/>\n", encoding="utf-8")
            files = PUBLISH_MODULE.collect_files(source)
            self.assertEqual([path for path, _ in files], ["PROGRESS.md", "assets/chart.svg"])

    def test_publisher_creates_isolated_generated_branch_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "data").mkdir()
            (source / "PROGRESS.md").write_text("# Progress\n", encoding="utf-8")
            (source / "data" / "dashboard.json").write_text(
                json.dumps({"asOf": "2026-07-15"}), encoding="utf-8"
            )
            responses = [
                None,
                {"sha": "blob-one"},
                {"sha": "blob-two"},
                {"sha": "tree-sha"},
                {"sha": "commit-sha"},
                {"ref": "refs/heads/progress-dashboard"},
            ]
            with mock.patch.object(PUBLISH_MODULE, "api_request", side_effect=responses) as request:
                commit = PUBLISH_MODULE.publish(
                    source, "Thorncrag/ARRP", "progress-dashboard", "token"
                )
            self.assertEqual(commit, "commit-sha")
            tree_payload = request.call_args_list[3].args[3]
            self.assertNotIn("base_tree", tree_payload)
            commit_payload = request.call_args_list[4].args[3]
            self.assertEqual(commit_payload["parents"], [])
            create_ref_payload = request.call_args_list[5].args[3]
            self.assertEqual(create_ref_payload["ref"], "refs/heads/progress-dashboard")


if __name__ == "__main__":
    unittest.main()
