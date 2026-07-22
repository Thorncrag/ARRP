import importlib.util
import json
import tempfile
import unittest
from copy import deepcopy
from datetime import date
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_project_console_progress.py"
SPEC = importlib.util.spec_from_file_location("project_console_progress", str(SCRIPT))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PUBLISH_SCRIPT = ROOT / "scripts" / "publish_project_console_progress.py"
PUBLISH_SPEC = importlib.util.spec_from_file_location("publish_project_console_progress", str(PUBLISH_SCRIPT))
PUBLISH_MODULE = importlib.util.module_from_spec(PUBLISH_SPEC)
PUBLISH_SPEC.loader.exec_module(PUBLISH_MODULE)


class ProjectConsoleProgressTests(unittest.TestCase):
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
                "name": "Completed within scope",
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
        self.assertFalse(ready["ready"])
        self.assertIsNone(ready["score"])
        self.assertIn("is not counted", ready["warnings"][0])

    def test_pending_status_with_existing_vehicle_emits_lifecycle_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            issue = root / "areas" / "DOM" / "issues" / "DOM-005.md"
            vehicle = root / "legislation" / "DOM-005.md"
            issue.parent.mkdir(parents=True)
            vehicle.parent.mkdir(parents=True)
            issue.write_text(
                "---\nlegislative_proposal: \"../../../legislation/DOM-005.md\"\n---\n",
                encoding="utf-8",
            )
            vehicle.write_text("# Proposed legislation\n", encoding="utf-8")
            _, items = MODULE.parse_items(self.raw, self.config, self.registry, root)
        pending = next(item for item in items if item["identifier"] == "DOM-005")
        self.assertEqual(len(pending["warnings"]), 1)
        self.assertIn("review whether the status should be In development or Audit needed", pending["warnings"][0])

    def test_completed_within_scope_is_not_counted_as_development_progress(self):
        raw = deepcopy(self.raw)
        nodes = raw["items"][1]["fieldValues"]["nodes"]
        for node in nodes:
            if (node.get("field") or {}).get("name") == "Status":
                node["name"] = "Completed within scope"
        _, items = MODULE.parse_items(raw, self.config, self.registry)
        completed = next(item for item in items if item["identifier"] == "REG-001")
        self.assertFalse(completed["ready"])
        self.assertEqual(completed["score"], 68)
        self.assertEqual(completed["warnings"], [])

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
        payload = MODULE.build_progress_payload(title, items, history, config, date(2026, 7, 15))
        self.assertEqual(payload["history"][0]["date"], "2026-06-24")
        retained_baseline = next(entry for entry in payload["history"] if entry["date"] == "2026-07-01")
        self.assertEqual(retained_baseline["ready"], 1)
        self.assertEqual(payload["metrics"]["rollingWeeklyVelocity"], 0.33)
        self.assertFalse(payload["movement"]["scoresAvailable"])
        self.assertEqual(payload["history"][0]["date"], "2026-06-24")

    def test_repository_retrospective_seed_preserves_baseline_after_scope_changes(self):
        seed = MODULE.read_json(ROOT / ".github" / "progress-history-seed.json")
        config = MODULE.read_json(ROOT / ".github" / "project-console-progress.json")
        registry = MODULE.read_registry(ROOT / "inventory" / "github_issue_registry.csv")
        evidence = seed["attainmentEvidence"]
        identifiers = {entry["identifier"] for entry in evidence}
        active_proposals = [row for row in registry if MODULE.normalize(row["Kind"]) == "proposal"]
        # The retrospective baseline remains historical even after proposal
        # admission, merger, or retirement changes the live denominator.
        self.assertEqual(len(active_proposals), 81)
        self.assertEqual(config["goal"]["baselineTotal"], 204)
        self.assertEqual(len(evidence), 23)
        self.assertEqual(len(identifiers), 23)
        self.assertEqual(seed["snapshots"][-1]["ready"], 23)
        self.assertEqual(set(seed["snapshots"][-1]["readyIssues"]), identifiers)
        for snapshot in seed["snapshots"]:
            self.assertEqual(snapshot["total"], 204)
            self.assertEqual(snapshot["ready"], len(snapshot["readyIssues"]))
        for entry in evidence:
            audit = ROOT / entry["audit"]
            self.assertTrue(audit.is_file(), entry["audit"])
            self.assertIn("### {} —".format(entry["date"]), audit.read_text(encoding="utf-8"))

    def test_builds_metrics_history_and_forecast_inputs(self):
        title, items = MODULE.parse_items(self.raw, self.config, self.registry)
        payload = MODULE.build_progress_payload(title, items, self.history, self.config, date(2026, 7, 15))
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
        self.assertGreater(payload["metrics"]["requiredPerWeek"], 0)
        self.assertEqual(payload["goal"]["targetDate"], "2026-12-31")

    def test_progress_build_writes_data_only_files(self):
        title, items = MODULE.parse_items(self.raw, self.config, self.registry)
        payload = MODULE.build_progress_payload(title, items, self.history, self.config, date(2026, 7, 15))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "site"
            MODULE.write_progress_data(output, payload)
            self.assertEqual(sorted(path.name for path in output.iterdir()), ["history.json", "progress.json"])
            saved = json.loads((output / "progress.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["metrics"]["total"], 4)

    def test_publisher_collects_generated_data_and_optional_deployment_control(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "data"
            source.mkdir()
            (source / "progress.json").write_text("{}\n", encoding="utf-8")
            (source / "history.json").write_text("{}\n", encoding="utf-8")
            vercel_config = Path(directory) / "vercel-control.json"
            vercel_config.write_text('{"git":{"deploymentEnabled":false}}\n', encoding="utf-8")
            files = PUBLISH_MODULE.collect_files(source, vercel_config)
            self.assertEqual(
                [path for path, _ in files],
                ["history.json", "progress.json", "participate/vercel.json"],
            )

    def test_publisher_creates_isolated_generated_branch_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "data"
            source.mkdir()
            (source / "progress.json").write_text(
                json.dumps({"asOf": "2026-07-15"}), encoding="utf-8"
            )
            (source / "history.json").write_text(
                json.dumps({"schemaVersion": 1, "snapshots": []}), encoding="utf-8"
            )
            vercel_config = Path(directory) / "vercel-control.json"
            vercel_config.write_text('{"git":{"deploymentEnabled":false}}\n', encoding="utf-8")
            responses = [
                None,
                {"sha": "blob-one"},
                {"sha": "blob-two"},
                {"sha": "blob-three"},
                {"sha": "tree-sha"},
                {"sha": "commit-sha"},
                {"ref": "refs/heads/project-console-data"},
            ]
            with mock.patch.object(PUBLISH_MODULE, "api_request", side_effect=responses) as request:
                commit = PUBLISH_MODULE.publish(
                    source,
                    "Thorncrag/ARRP",
                    "project-console-data",
                    "token",
                    vercel_config,
                )
            self.assertEqual(commit, "commit-sha")
            tree_payload = request.call_args_list[4].args[3]
            self.assertNotIn("base_tree", tree_payload)
            self.assertEqual(
                [entry["path"] for entry in tree_payload["tree"]],
                ["history.json", "progress.json", "participate/vercel.json"],
            )
            commit_payload = request.call_args_list[5].args[3]
            self.assertEqual(commit_payload["parents"], [])
            create_ref_payload = request.call_args_list[6].args[3]
            self.assertEqual(create_ref_payload["ref"], "refs/heads/project-console-data")

    def test_vercel_config_excludes_data_branch_from_application_previews(self):
        config = json.loads((ROOT / "participate" / "vercel.json").read_text(encoding="utf-8"))
        self.assertFalse(config["git"]["deploymentEnabled"]["project-console-data"])


if __name__ == "__main__":
    unittest.main()
