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

    def test_untrusted_display_text_is_markdown_escaped(self):
        escaped = MODULE.markdown_cell("<img src=x> [click](https://example.test) | value")
        self.assertNotIn("<img", escaped)
        self.assertNotIn("[click]", escaped)
        self.assertIn("\\|", escaped)

    def test_evaluation_requires_review_until_label_acknowledgment(self):
        observation = MODULE.parse_just_security(tracker_html())["Accessibility"]
        current = {"MON-0001": observation}
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
            {"MON-0001": changed_observation},
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
            {"MON-0001": changed_observation},
            [],
            review_label_present=True,
            checked_at="2026-07-22T00:00:00+00:00",
            source_url="https://example.test/",
        )
        self.assertEqual(waiting["status"], "update_detected")
        self.assertFalse(waiting["add_review_label"])

        acknowledged = MODULE.evaluate_target(
            waiting,
            {"MON-0001": changed_observation},
            [],
            review_label_present=False,
            checked_at="2026-07-23T00:00:00+00:00",
            source_url="https://example.test/",
        )
        self.assertEqual(acknowledged["status"], "baseline_acknowledged")
        self.assertEqual(acknowledged["baseline"], acknowledged["observed"])

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

    def test_pilot_configuration_routes_to_registered_active_monitors(self):
        config = json.loads((ROOT / ".github" / "monitoring-pilot.json").read_text())
        targets = MODULE.build_targets(
            config,
            MODULE.read_csv(ROOT / "research" / "trump-administration-litigation-monitoring.csv"),
            MODULE.read_csv(ROOT / "inventory" / "github_issue_registry.csv"),
        )
        self.assertEqual(len(targets), 5)
        self.assertEqual(sum(len(target["matters"]) for target in targets), 5)
        self.assertTrue(all(target["issue_number"] for target in targets))

    def test_workflow_uses_minimum_permissions_and_no_repository_write(self):
        workflow = (ROOT / ".github" / "workflows" / "monitoring-pilot.yml").read_text()
        self.assertIn("contents: read", workflow)
        self.assertIn("issues: write", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("pull-requests: write", workflow)
        self.assertIn("scripts/check_monitoring_updates.py", workflow)

    def test_local_dry_run_writes_a_complete_summary(self):
        config = {
            "schemaVersion": 1,
            "enabled": True,
            "reviewLabel": "needs: monitor review",
            "reviewLabelColor": "FBCA04",
            "reviewLabelDescription": "Review required.",
            "source": {
                "type": "just-security-tablepress-42",
                "url": "https://www.justsecurity.org/example/",
                "allowedHosts": ["www.justsecurity.org"],
                "maximumBytes": 100000,
            },
            "targets": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            config_path = path / "config.json"
            source_path = path / "source.html"
            summary_path = path / "summary.md"
            report_path = path / "report.json"
            config_path.write_text(json.dumps(config))
            source_path.write_text(tracker_html())
            old_argv = MODULE.sys.argv
            try:
                MODULE.sys.argv = [
                    "check_monitoring_updates.py",
                    "--config",
                    str(config_path),
                    "--source-html",
                    str(source_path),
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
            self.assertIn("ARRP automated monitoring pilot", summary_path.read_text())
            self.assertEqual(json.loads(report_path.read_text())["results"], [])


if __name__ == "__main__":
    unittest.main()
