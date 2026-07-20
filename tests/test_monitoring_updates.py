import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_monitoring_updates", ROOT / "scripts" / "check_monitoring_updates.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def tracker_html(*, second_status: str = "Case Pending", second_update: str = "2026-07-02") -> str:
    return f"""
    <html><body>
      <table id="tablepress-42">
        <thead><tr>
          <th>Case Name</th><th>Case Status</th><th>Executive Action</th>
          <th>Last Case Update</th><th>Case Updates</th>
        </tr></thead>
        <tbody>
          <tr>
            <td><a href="https://www.courtlistener.com/docket/100/example-one/">Example One</a></td>
            <td>Government Action Temporarily Blocked</td><td>Accessibility</td>
            <td>2026-07-01</td><td>Initial injunction entered.</td>
          </tr>
          <tr>
            <td><a href="https://www.courtlistener.com/docket/101/example-two/">Example Two</a></td>
            <td>{second_status}</td><td>Accessibility</td>
            <td>{second_update}</td><td>Second case update.</td>
          </tr>
        </tbody>
      </table>
    </body></html>
    """


class MonitoringUpdateTests(unittest.TestCase):
    def test_parser_extracts_only_structured_action_fields(self):
        parsed = MODULE.parse_just_security(tracker_html())
        self.assertEqual(set(parsed), {"Accessibility"})
        observation = parsed["Accessibility"]
        self.assertEqual(observation["case_count"], 2)
        self.assertEqual(observation["last_update"], "2026-07-02")
        self.assertEqual(
            observation["statuses"],
            {"Case Pending": 1, "Government Action Temporarily Blocked": 1},
        )
        self.assertEqual(len(observation["fingerprint"]), 64)

    def test_material_tracker_change_changes_fingerprint(self):
        baseline = MODULE.parse_just_security(tracker_html())["Accessibility"]["fingerprint"]
        changed = MODULE.parse_just_security(
            tracker_html(second_status="Case Closed", second_update="2026-07-03")
        )["Accessibility"]["fingerprint"]
        self.assertNotEqual(baseline, changed)

    def test_tracker_cases_are_keyed_by_permanent_docket_identity(self):
        cases = MODULE.tracker_cases_by_docket(MODULE.parse_just_security(tracker_html()))

        self.assertEqual(set(cases), {"courtlistener:100", "courtlistener:101"})
        self.assertEqual(cases["courtlistener:100"]["case"], "Example One")
        self.assertEqual(len(cases["courtlistener:100"]["fingerprint"]), 64)

    def test_untrusted_display_text_is_markdown_escaped(self):
        escaped = MODULE.markdown_cell("<img src=x> [click](https://example.test) | value")
        self.assertNotIn("<img", escaped)
        self.assertNotIn("[click]", escaped)
        self.assertIn("\\|", escaped)

    def test_evaluation_requires_review_until_label_acknowledgment(self):
        observation = MODULE.parse_just_security(tracker_html())["Accessibility"]
        current = {"SRC-0913": observation}
        first = MODULE.evaluate_target(
            None,
            current,
            [],
            review_label_present=False,
            checked_at="2026-07-20T00:00:00+00:00",
            source_url="https://example.test/",
        )
        self.assertEqual(first["status"], "baseline_established")

        changed_observation = MODULE.parse_just_security(
            tracker_html(second_status="Case Closed", second_update="2026-07-03")
        )["Accessibility"]
        changed = MODULE.evaluate_target(
            first,
            {"SRC-0913": changed_observation},
            [],
            review_label_present=False,
            checked_at="2026-07-21T00:00:00+00:00",
            source_url="https://example.test/",
        )
        self.assertEqual(changed["status"], "update_detected")
        self.assertTrue(changed["add_review_label"])
        self.assertNotEqual(changed["baseline"], changed["observed"])

        waiting = MODULE.evaluate_target(
            changed,
            {"SRC-0913": changed_observation},
            [],
            review_label_present=True,
            checked_at="2026-07-22T00:00:00+00:00",
            source_url="https://example.test/",
        )
        self.assertEqual(waiting["status"], "update_detected")
        self.assertFalse(waiting["add_review_label"])

        acknowledged = MODULE.evaluate_target(
            waiting,
            {"SRC-0913": changed_observation},
            [],
            review_label_present=False,
            checked_at="2026-07-23T00:00:00+00:00",
            source_url="https://example.test/",
        )
        self.assertEqual(acknowledged["status"], "baseline_acknowledged")
        self.assertEqual(acknowledged["baseline"], acknowledged["observed"])

    def test_pre_source_schema_baseline_migrates_without_false_alert(self):
        observation = MODULE.parse_just_security(tracker_html())["Accessibility"]
        previous = {
            "schema_version": 1,
            "baseline": {"legacy-key": observation["fingerprint"]},
            "review_required": False,
            "status": "no_change",
        }

        migrated = MODULE.evaluate_target(
            previous,
            {"SRC-0913": observation},
            [],
            review_label_present=False,
            checked_at="2026-07-20T00:00:00+00:00",
            source_url="https://example.test/",
        )

        self.assertEqual(migrated["status"], "baseline_migrated")
        self.assertFalse(migrated["add_review_label"])
        self.assertEqual(migrated["baseline"], migrated["observed"])

    def test_check_failure_labels_only_after_two_consecutive_failures(self):
        first = MODULE.evaluate_target(
            None,
            {},
            ["temporary source failure"],
            review_label_present=False,
            checked_at="2026-07-20T00:00:00+00:00",
            source_url="https://example.test/",
        )
        self.assertEqual(first["status"], "check_failed")
        self.assertFalse(first["add_review_label"])
        second = MODULE.evaluate_target(
            first,
            {},
            ["temporary source failure"],
            review_label_present=False,
            checked_at="2026-07-21T00:00:00+00:00",
            source_url="https://example.test/",
        )
        self.assertTrue(second["add_review_label"])
        self.assertEqual(second["consecutive_failures"], 2)

    def test_complete_target_discovery_is_not_limited_by_configuration(self):
        config = json.loads((ROOT / ".github" / "monitoring-pilot.json").read_text())
        registry = MODULE.read_csv(ROOT / "inventory" / "github_issue_registry.csv")
        monitoring_issues = [
            {
                "number": int(row["GitHub Number"]),
                "title": row["GitHub Title"],
                "labels": [{"name": "needs: monitoring"}],
            }
            for row in registry
            if row["Kind"] == "source review" and row["Object ID"]
        ]
        sources = [
            {**row, "_inventory": "sources.csv"}
            for row in MODULE.read_csv(ROOT / "inventory" / "sources.csv")
        ]
        sources.extend(
            {**row, "_inventory": "sources-pending.csv"}
            for row in MODULE.read_csv(ROOT / "inventory" / "sources-pending.csv")
        )
        targets = MODULE.build_targets(
            config,
            sources,
            registry,
            monitoring_issues,
        )
        self.assertEqual(len(targets), len(monitoring_issues))
        self.assertGreater(sum(len(target["matters"]) for target in targets), 500)
        self.assertTrue(
            all(matter["matter_id"].startswith("SRC-") for target in targets for matter in target["matters"])
        )
        self.assertTrue(all(target["issue_number"] for target in targets))
        self.assertNotIn("targets", config)

    def test_workflow_uses_minimum_permissions_and_no_repository_write(self):
        workflow = (ROOT / ".github" / "workflows" / "monitoring-pilot.yml").read_text()
        config = json.loads((ROOT / ".github" / "monitoring-pilot.json").read_text())
        self.assertIn("contents: read", workflow)
        self.assertIn("issues: write", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("pull-requests: write", workflow)
        self.assertIn("scripts/check_monitoring_updates.py", workflow)
        self.assertIn('cron: "13 0 * * *"', workflow)
        self.assertIn('timezone: "America/New_York"', workflow)
        self.assertIn("continue-on-error: true", workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn("gh issue comment", workflow)
        self.assertIn("Verify the signal-only boundary", workflow)
        self.assertIn('git diff --quiet "${GITHUB_SHA}" -- .', workflow)
        self.assertIn("This monitoring workflow is signal-only and read-only", workflow)
        self.assertIn("steps.monitor.outcome == 'failure' || steps.read_only.outcome == 'failure'", workflow)
        self.assertEqual(config["notification"]["issueNumber"], 317)
        self.assertEqual(config["notification"]["mention"], "@Thorncrag")
        self.assertEqual(config["targetLabel"], "needs: monitoring")

    def test_local_dry_run_writes_a_complete_summary(self):
        config = {
            "schemaVersion": 2,
            "enabled": True,
            "reviewLabel": "needs: monitor review",
            "reviewLabelColor": "FBCA04",
            "reviewLabelDescription": "Review required.",
            "targetLabel": "needs: monitoring",
            "source": {
                "type": "just-security-tablepress-42",
                "url": "https://www.justsecurity.org/example/",
                "allowedHosts": ["www.justsecurity.org"],
                "maximumBytes": 100000,
            },
            "supportedSourceHosts": ["www.courtlistener.com"],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            config_path = path / "config.json"
            source_path = path / "source.html"
            summary_path = path / "summary.md"
            report_path = path / "report.json"
            issues_path = path / "issues.json"
            config_path.write_text(json.dumps(config))
            source_path.write_text(tracker_html())
            issues_path.write_text("[]")
            old_argv = MODULE.sys.argv
            try:
                MODULE.sys.argv = [
                    "check_monitoring_updates.py",
                    "--config",
                    str(config_path),
                    "--source-html",
                    str(source_path),
                    "--monitoring-issues-json",
                    str(issues_path),
                    "--summary",
                    str(summary_path),
                    "--report-json",
                    str(report_path),
                    "--checked-at",
                    "2026-07-20T00:00:00+00:00",
                ]
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(MODULE.main(), 0)
            finally:
                MODULE.sys.argv = old_argv
            self.assertIn("ARRP automated monitoring prototype", summary_path.read_text())
            self.assertEqual(json.loads(report_path.read_text())["results"], [])


if __name__ == "__main__":
    unittest.main()
