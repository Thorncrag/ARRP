import importlib.util
import json
import tempfile
import unittest
from copy import deepcopy
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
        self.registry = MODULE.read_registry(ROOT / "tests" / "fixtures" / "progress-registry.csv")

    def test_filters_to_proposals_and_uses_status_as_readiness_authority(self):
        title, items = MODULE.parse_items(self.raw, self.config, self.registry)
        self.assertEqual(title, "American Restoration and Resilience Project")
        self.assertEqual(len(items), 4)
        self.assertEqual(sum(item["ready"] for item in items), 1)
        mismatch = next(item for item in items if item["identifier"] == "JUD-011")
        self.assertFalse(mismatch["ready"])
        self.assertEqual(len(mismatch["warnings"]), 1)

    def test_unmatched_registry_proposal_remains_visible_and_warns(self):
        registry = list(self.registry) + [{
            "GitHub Number": "999",
            "GitHub Issue": "https://github.com/Thorncrag/ARRP/issues/999",
            "Kind": "proposal",
            "GitHub Title": "TEST-999: Missing Project row",
            "Canonical Record": "areas/TEST/issues/TEST-999.md",
        }]
        _, items = MODULE.parse_items(self.raw, self.config, registry)
        missing = next(item for item in items if item["identifier"] == "TEST-999")
        self.assertEqual(len(items), 5)
        self.assertFalse(missing["ready"])
        self.assertEqual(missing["status"], "Unspecified")
        self.assertIn("no matching Project item", missing["warnings"][0])

    def test_title_identifier_wins_when_merged_items_share_canonical_page(self):
        raw = deepcopy(self.raw)
        reg = raw["items"][1]
        reg["fieldValues"]["nodes"].append(
            {
                "__typename": "ProjectV2ItemFieldTextValue",
                "text": "REG-001: Congressional Mandate Enforcement",
                "field": {"name": "Title"},
            }
        )
        merged = deepcopy(reg)
        merged["id"] = "PVTI_MERGED"
        merged["fieldValues"]["nodes"] = [
            node
            for node in merged["fieldValues"]["nodes"]
            if (node.get("field") or {}).get("name") not in {"Title", "Status", "Score"}
        ] + [
            {
                "__typename": "ProjectV2ItemFieldTextValue",
                "text": "HOR-018: Integrated into REG-001",
                "field": {"name": "Title"},
            },
            {
                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                "name": "Done / Published",
                "field": {"name": "Status"},
            },
        ]
        raw["items"].append(merged)
        _, items = MODULE.parse_items(raw, self.config, self.registry)
        proposal = next(item for item in items if item["identifier"] == "REG-001")
        self.assertEqual(proposal["status"], "Developed draft")
        self.assertEqual(proposal["score"], 68)
        self.assertFalse(proposal["ready"])
        self.assertEqual(proposal["warnings"], [])

    def test_ready_status_without_score_emits_consistency_warning(self):
        raw = deepcopy(self.raw)
        nodes = raw["items"][0]["fieldValues"]["nodes"]
        raw["items"][0]["fieldValues"]["nodes"] = [
            node for node in nodes if (node.get("field") or {}).get("name") != "Score"
        ]
        _, items = MODULE.parse_items(raw, self.config, self.registry)
        ready = next(item for item in items if item["identifier"] == "DOJ-007")
        self.assertTrue(ready["ready"])
        self.assertIsNone(ready["score"])
        self.assertIn("missing a Project score", ready["warnings"][0])

    def test_retrospective_seed_extends_history_without_replacing_live_dates(self):
        config = deepcopy(self.config)
        config["goal"]["historyStartDate"] = "2026-06-24"
        seed = {
            "schemaVersion": 1,
            "snapshots": [
                {
                    "date": "2026-06-24",
                    "total": 4,
                    "ready": 0,
                    "readyIssues": [],
                    "scores": {},
                },
                {"date": "2026-07-01", "total": 4, "ready": 0},
            ],
        }
        history = MODULE.combine_histories(seed, self.history)
        title, items = MODULE.parse_items(self.raw, config, self.registry)
        payload = MODULE.build_dashboard_payload(title, items, history, config, date(2026, 7, 15))
        self.assertEqual(payload["history"][0]["date"], "2026-06-24")
        retained_baseline = next(entry for entry in payload["history"] if entry["date"] == "2026-07-01")
        self.assertEqual(retained_baseline["ready"], 1)
        self.assertEqual(payload["metrics"]["rollingWeeklyVelocity"], 0.33)
        self.assertFalse(payload["movement"]["scoresAvailable"])
        self.assertIn("Jun 24, 2026", MODULE.trajectory_svg(payload))

    def test_repository_retrospective_seed_matches_documented_baseline(self):
        seed = MODULE.read_json(ROOT / ".github" / "progress-history-seed.json")
        evidence = seed["attainmentEvidence"]
        identifiers = {entry["identifier"] for entry in evidence}
        self.assertEqual(len(evidence), 23)
        self.assertEqual(len(identifiers), 23)
        self.assertEqual(seed["snapshots"][-1]["ready"], 23)
        self.assertEqual(set(seed["snapshots"][-1]["readyIssues"]), identifiers)
        for snapshot in seed["snapshots"]:
            self.assertEqual(snapshot["ready"], len(snapshot["readyIssues"]))
        for entry in evidence:
            audit = ROOT / entry["audit"]
            self.assertTrue(audit.is_file(), entry["audit"])
            self.assertIn("### {} —".format(entry["date"]), audit.read_text(encoding="utf-8"))

    def test_builds_metrics_history_and_forecast_inputs(self):
        title, items = MODULE.parse_items(self.raw, self.config, self.registry)
        payload = MODULE.build_dashboard_payload(title, items, self.history, self.config, date(2026, 7, 15))
        self.assertEqual(payload["metrics"]["ready"], 1)
        self.assertEqual(payload["metrics"]["total"], 4)
        self.assertEqual(payload["metrics"]["remaining"], 3)
        self.assertEqual(payload["metrics"]["percentReady"], 25.0)
        self.assertEqual(payload["history"][-1]["date"], "2026-07-15")
        self.assertEqual(len(payload["warnings"]), 1)
        self.assertTrue(payload["movement"]["available"])
        self.assertEqual(payload["movement"]["scoresImproved"], 2)
        self.assertTrue(payload["movement"]["scoresAvailable"])
        self.assertEqual(payload["movement"]["netScoreChange"], 13.0)
        required = next(row for row in MODULE.scenario_rows(payload) if row[0] == "Pace required for official target")
        self.assertEqual(required[2], "Dec 31, 2026 (target date)")

    def test_dashboard_build_writes_github_renderable_files(self):
        title, items = MODULE.parse_items(self.raw, self.config, self.registry)
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
