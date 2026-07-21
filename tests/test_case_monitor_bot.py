import html
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_case_updates", ROOT / "scripts" / "check_case_updates.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


HEADINGS = [
    "Case Name",
    "Filings",
    "Date Case Filed",
    "State A.G.'s",
    "Case Status",
    "Issue",
    "Executive Action",
    "Last Case Update",
    "Case Summary",
    "Case Updates",
]


def row(
    name="Example v. United States",
    docket="1:26-cv-00100",
    docket_id=100,
    status="Case Pending",
    last="2026-07-20",
    summary="Initial summary.",
    updates="Initial update.",
    case_link=True,
):
    link = (
        f'<a href="https://www.courtlistener.com/docket/{docket_id}/example/">{html.escape(name)}</a>'
        if case_link
        else html.escape(name)
    )
    values = [
        f"{link}<p>{html.escape(docket)}</p>",
        "",
        "2026-07-01",
        "",
        html.escape(status),
        "Separation of Powers",
        "Executive order",
        html.escape(last),
        html.escape(summary),
        updates,
    ]
    return values


def tracker_html(rows, *, declared_total=None, declared_statuses=None):
    declared_total = len(rows) if declared_total is None else declared_total
    actual = {}
    for values in rows:
        actual[html.unescape(values[4])] = actual.get(html.unescape(values[4]), 0) + 1
    declared_statuses = actual if declared_statuses is None else declared_statuses
    totals = "<br>".join(
        f"<span>{html.escape(status)}: {count}</span>"
        for status, count in declared_statuses.items()
    )
    heading_html = "".join(f"<th>{html.escape(value)}</th>" for value in HEADINGS)
    row_html = "".join(
        "<tr>" + "".join(f"<td>{value}</td>" for value in values) + "</tr>"
        for values in rows
    )
    return (
        f"<strong>Total number of cases currently tracked</strong>: {declared_total}."
        f"{totals}<table id=\"tablepress-42\"><thead><tr>{heading_html}</tr></thead>"
        f"<tbody>{row_html}</tbody></table>"
    )


def parser_config(minimum=1, maximum=20):
    return {
        "tableId": "tablepress-42",
        "minimumEntries": minimum,
        "maximumEntries": maximum,
    }


def docket_payload(docket_id, modified="2026-07-20T12:00:00Z"):
    return {
        "id": docket_id,
        "case_name": "Example v. United States",
        "docket_number": "1:26-cv-00100",
        "date_modified": modified,
        "date_last_index": modified,
        "date_last_filing": "2026-07-20",
        "date_terminated": None,
        "blocked": False,
    }


class CaseMonitorBotTests(unittest.TestCase):
    def test_composite_identity_allows_one_courtlistener_id_for_distinct_rows(self):
        entries = MODULE.parse_tracker_html(
            tracker_html(
                [
                    row(name="Trial", docket="1:26-cv-00100", docket_id=100),
                    row(name="Related", docket="2:26-cv-00200", docket_id=100),
                ]
            ),
            parser_config(),
        )
        self.assertEqual(len(entries), 2)
        self.assertEqual({entry["primary_docket_key"] for entry in entries.values()}, {"courtlistener:100"})
        self.assertIn("courtlistener:100|docket:1:26-cv-00100", entries)
        self.assertIn("courtlistener:100|docket:2:26-cv-00200", entries)

    def test_duplicate_composite_identity_fails_closed(self):
        document = tracker_html([row(), row(name="Duplicate")])
        with self.assertRaisesRegex(ValueError, "duplicate identity"):
            MODULE.parse_tracker_html(document, parser_config())

    def test_appeal_link_in_updates_is_not_treated_as_primary(self):
        updates = (
            '<a href="https://www.courtlistener.com/docket/999/appeal/">Appeal docket</a>'
        )
        entries = MODULE.parse_tracker_html(
            tracker_html([row(docket_id=100, updates=updates)]), parser_config()
        )
        entry = next(iter(entries.values()))
        self.assertEqual(entry["primary_docket_key"], "courtlistener:100")
        self.assertNotIn("999", entry["key"])

    def test_declared_total_and_status_tallies_must_match_rows(self):
        with self.assertRaisesRegex(ValueError, "declared 2 entries"):
            MODULE.parse_tracker_html(
                tracker_html([row()], declared_total=2), parser_config()
            )
        with self.assertRaisesRegex(ValueError, "status totals"):
            MODULE.parse_tracker_html(
                tracker_html([row()], declared_statuses={"Case Pending": 2}), parser_config()
            )

    def test_column_and_entry_bounds_fail_closed(self):
        malformed = tracker_html([row()]).replace("<td>Initial update.</td>", "")
        with self.assertRaisesRegex(ValueError, "column count"):
            MODULE.parse_tracker_html(malformed, parser_config())
        with self.assertRaisesRegex(ValueError, "expected between"):
            MODULE.parse_tracker_html(tracker_html([row()]), parser_config(minimum=2))

    def test_compare_reports_added_changed_removed_and_rejects_mass_removal(self):
        original = MODULE.parse_tracker_html(tracker_html([row()]), parser_config())
        previous = MODULE.compact_snapshot(original)
        changed = MODULE.parse_tracker_html(
            tracker_html([row(status="Government Action Blocked", last="2026-07-21")]),
            parser_config(),
        )
        status, changes = MODULE.compare_snapshots(previous, changed, 1.0)
        self.assertEqual(status, "changes_detected")
        self.assertEqual(changes[0]["changed_fields"], ["status", "last case update"])
        with self.assertRaisesRegex(ValueError, "mass removal"):
            MODULE.compare_snapshots(previous, {}, 0.1)

    def test_compressed_baseline_round_trips_with_room_for_live_scale(self):
        snapshot = {
            f"courtlistener:{number}|docket:1:26-cv-{number:05d}": {
                "s": "Case Pending",
                "l": "2026-07-20",
                "f": f"{number:032x}"[-32:],
            }
            for number in range(1, 902)
        }
        body = MODULE.render_baseline_comment(
            snapshot, "2026-07-21T00:00:00+00:00", "no_change", 0
        )
        self.assertLess(len(body.encode("utf-8")), MODULE.MAX_COMMENT_BYTES)
        self.assertEqual(MODULE.baseline_from_comment(body), snapshot)

    def test_verification_is_optional_deduplicated_and_capped(self):
        entries = MODULE.parse_tracker_html(
            tracker_html(
                [
                    row(name="First", docket="1:26-cv-00100", docket_id=100),
                    row(name="Related", docket="2:26-cv-00200", docket_id=100),
                    row(name="Second", docket="3:26-cv-00300", docket_id=200),
                ]
            ),
            parser_config(),
        )
        changes = [
            {"kind": "added", "key": key, "current": entry, "previous": None}
            for key, entry in entries.items()
        ]
        config = {"maxDocketsPerRun": 1, "requestIntervalSeconds": 0, "apiRoot": "https://www.courtlistener.com/api/rest/v4"}
        no_token = MODULE.verify_changed_dockets(changes, config, "")
        self.assertEqual(set(no_token), {"courtlistener:100", "courtlistener:200"})
        results = MODULE.verify_changed_dockets(
            changes, config, "", {"100": docket_payload(100), "200": docket_payload(200)}
        )
        self.assertEqual(results["courtlistener:100"]["outcome"], "queried")
        self.assertEqual(results["courtlistener:200"]["outcome"], "unverified")

    def test_source_mapping_uses_primary_docket_not_composite_row_key(self):
        entries = MODULE.parse_tracker_html(tracker_html([row(docket_id=100)]), parser_config())
        key, entry = next(iter(entries.items()))
        changes = [{"kind": "added", "key": key, "current": entry, "previous": None}]
        mapping = MODULE.source_map(
            [{"Source ID": "SRC-0001", "Associated Record IDs": "DOJ-001", "URL": "https://www.courtlistener.com/docket/100/example/"}]
        )
        MODULE.attach_source_matches(changes, mapping)
        self.assertEqual(changes[0]["source_matches"][0]["source_id"], "SRC-0001")

    def test_display_text_is_sanitized_for_markdown_reports(self):
        escaped = MODULE.markdown_text("<img src=x> [click](https://example.test) | value")
        self.assertNotIn("<img", escaped)
        self.assertNotIn("[click]", escaped)
        self.assertIn("\\|", escaped)

    def test_local_dry_run_establishes_baseline_and_writes_outputs(self):
        config = json.loads((ROOT / ".github" / "case-monitor-bot.json").read_text())
        config["tracker"]["minimumEntries"] = 1
        config["tracker"]["maximumEntries"] = 10
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            paths = {name: path / name for name in ["config.json", "tracker.html", "sources.csv", "pending.csv", "registry.csv", "issues.json", "summary.md", "report.json"]}
            paths["config.json"].write_text(json.dumps(config))
            paths["tracker.html"].write_text(tracker_html([row()]))
            header = "Source ID,Associated Record IDs,Source Type,Title or Description,URL,Monitoring\n"
            paths["sources.csv"].write_text(header)
            paths["pending.csv"].write_text(header)
            paths["registry.csv"].write_text("GitHub Number,GitHub Issue,Object ID,GitHub Title\n")
            paths["issues.json"].write_text("[]")
            old_argv = MODULE.sys.argv
            try:
                MODULE.sys.argv = [
                    "check_case_updates.py", "--config", str(paths["config.json"]),
                    "--tracker-html", str(paths["tracker.html"]), "--sources", str(paths["sources.csv"]),
                    "--pending-sources", str(paths["pending.csv"]), "--registry", str(paths["registry.csv"]),
                    "--monitoring-issues-json", str(paths["issues.json"]), "--summary", str(paths["summary.md"]),
                    "--report-json", str(paths["report.json"]), "--checked-at", "2026-07-21T00:00:00+00:00",
                ]
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(MODULE.main(), 0)
            finally:
                MODULE.sys.argv = old_argv
            report = json.loads(paths["report.json"].read_text())
            self.assertEqual(report["status"], "baseline_established")
            self.assertEqual(report["tracker_entry_count"], 1)
            self.assertEqual(report["repository_changes"], [])

    def test_config_preserves_console_metadata_and_signal_only_boundary(self):
        config = json.loads((ROOT / ".github" / "case-monitor-bot.json").read_text())
        self.assertEqual(config["schemaVersion"], 4)
        self.assertEqual(config["sourceMonitoringField"], "Monitoring")
        self.assertIn("Court Docket", config["eligibleSourceTypes"])
        self.assertEqual(config["verification"]["maxDocketsPerRun"], 20)
        self.assertEqual(config["notification"]["issueNumber"], 317)


if __name__ == "__main__":
    unittest.main()
