import csv
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

CSV_FIELDS = [
    "Source ID",
    "Associated Record IDs",
    "Monitoring",
    "Source Type",
    "Authority / Publisher",
    "Title or Description",
    "Date",
    "URL",
    "Proposition Supported",
    "Reliability Tier",
    "Reviewed?",
    "Notes",
    "Retention Rationale",
    "Pending Reason",
    "Next Action",
    "Blocker",
    "Monitoring Rationale",
    "Monitoring Group",
    "Monitoring Baseline",
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
    return [
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
    return {"tableId": "tablepress-42", "minimumEntries": minimum, "maximumEntries": maximum}


def source(source_id="SRC-0001", docket_id=100, monitoring="Yes", baseline=""):
    result = {field: "" for field in CSV_FIELDS}
    result.update(
        {
            "Source ID": source_id,
            "Associated Record IDs": "DOJ-001",
            "Monitoring": monitoring,
            "Source Type": "Court Docket or Judicial Record",
            "Authority / Publisher": "CourtListener / RECAP",
            "Title or Description": "Example docket",
            "URL": f"https://www.courtlistener.com/docket/{docket_id}/example/",
            "Monitoring Baseline": baseline,
        }
    )
    return result


def write_catalog(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


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
        self.assertIn("courtlistener:100|docket:1:26-cv-00100", entries)
        self.assertIn("courtlistener:100|docket:2:26-cv-00200", entries)

    def test_duplicate_composite_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicate identity"):
            MODULE.parse_tracker_html(tracker_html([row(), row(name="Duplicate")]), parser_config())

    def test_appeal_link_in_updates_is_not_treated_as_primary(self):
        updates = '<a href="https://www.courtlistener.com/docket/999/appeal/">Appeal docket</a>'
        entries = MODULE.parse_tracker_html(
            tracker_html([row(docket_id=100, updates=updates)]), parser_config()
        )
        entry = next(iter(entries.values()))
        self.assertEqual(entry["primary_docket_key"], "courtlistener:100")
        self.assertNotIn("999", entry["key"])

    def test_declared_total_status_and_structure_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "declared 2 entries"):
            MODULE.parse_tracker_html(tracker_html([row()], declared_total=2), parser_config())
        with self.assertRaisesRegex(ValueError, "status totals"):
            MODULE.parse_tracker_html(
                tracker_html([row()], declared_statuses={"Case Pending": 2}), parser_config()
            )
        malformed = tracker_html([row()]).replace("<td>Initial update.</td>", "")
        with self.assertRaisesRegex(ValueError, "column count"):
            MODULE.parse_tracker_html(malformed, parser_config())

    def test_deliberate_initialization_populates_only_mapped_blank_rows(self):
        entries = MODULE.parse_tracker_html(tracker_html([row()]), parser_config())
        mapped = source()
        uncovered = source("SRC-0002", 200)
        status, changes, coverage = MODULE.evaluate_catalog_sources(
            entries=entries,
            sources_rows=[mapped, uncovered],
            pending_rows=[],
            baseline_field="Monitoring Baseline",
            initialize=True,
        )
        self.assertEqual(status, "baselines_initialized")
        self.assertEqual(changes, [])
        self.assertTrue(mapped["Monitoring Baseline"].startswith(MODULE.STATE_PREFIX))
        self.assertEqual(uncovered["Monitoring Baseline"], "")
        self.assertEqual(coverage["case_baselines_initialized"], 1)
        self.assertEqual(coverage["uncovered_catalog_rows"], 1)

    def test_normal_mode_rejects_blank_mapped_baseline(self):
        entries = MODULE.parse_tracker_html(tracker_html([row()]), parser_config())
        with self.assertRaisesRegex(ValueError, "--initialize-baselines"):
            MODULE.evaluate_catalog_sources(
                entries=entries,
                sources_rows=[source()],
                pending_rows=[],
                baseline_field="Monitoring Baseline",
                initialize=False,
            )

    def test_change_updates_each_duplicate_catalog_row_once(self):
        original = MODULE.parse_tracker_html(tracker_html([row()]), parser_config())
        baseline = MODULE.encode_state(
            "case", MODULE.compact_case_baseline(list(original.values()))
        )
        rows = [source("SRC-0001", baseline=baseline), source("SRC-0002", baseline=baseline)]
        changed = MODULE.parse_tracker_html(
            tracker_html([row(status="Government Action Blocked", last="2026-07-21")]),
            parser_config(),
        )
        status, changes, coverage = MODULE.evaluate_catalog_sources(
            entries=changed,
            sources_rows=rows,
            pending_rows=[],
            baseline_field="Monitoring Baseline",
            initialize=False,
        )
        self.assertEqual(status, "changes_detected")
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["changed_fields"], ["status", "last case update"])
        self.assertEqual(coverage["case_baselines_updated"], 2)
        self.assertEqual(rows[0]["Monitoring Baseline"], rows[1]["Monitoring Baseline"])

    def test_previously_mapped_source_disappearance_fails_closed(self):
        original = MODULE.parse_tracker_html(tracker_html([row()]), parser_config())
        baseline = MODULE.encode_state(
            "case", MODULE.compact_case_baseline(list(original.values()))
        )
        different = MODULE.parse_tracker_html(
            tracker_html([row(docket="2:26-cv-00200", docket_id=200)]), parser_config()
        )
        with self.assertRaisesRegex(ValueError, "disappeared from the tracker"):
            MODULE.evaluate_catalog_sources(
                entries=different,
                sources_rows=[source(baseline=baseline)],
                pending_rows=[],
                baseline_field="Monitoring Baseline",
                initialize=False,
            )

    def test_uncovered_blank_source_is_reported_without_failure(self):
        entries = MODULE.parse_tracker_html(tracker_html([row()]), parser_config())
        status, changes, coverage = MODULE.evaluate_catalog_sources(
            entries=entries,
            sources_rows=[source(docket_id=200)],
            pending_rows=[],
            baseline_field="Monitoring Baseline",
            initialize=False,
        )
        self.assertEqual(status, "no_change")
        self.assertEqual(changes, [])
        self.assertEqual(coverage["uncovered_catalog_rows"], 1)

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
        config = {
            "maxDocketsPerRun": 1,
            "requestIntervalSeconds": 0,
            "apiRoot": "https://www.courtlistener.com/api/rest/v4",
        }
        self.assertEqual(
            set(MODULE.verify_changed_dockets(changes, config, "")),
            {"courtlistener:100", "courtlistener:200"},
        )
        results = MODULE.verify_changed_dockets(
            changes,
            config,
            "",
            {"100": docket_payload(100), "200": docket_payload(200)},
        )
        self.assertEqual(results["courtlistener:100"]["outcome"], "queried")
        self.assertEqual(results["courtlistener:200"]["outcome"], "unverified")

    def test_main_initialization_then_change_apply_updates_log(self):
        config = json.loads((ROOT / ".github" / "case-monitor-bot.json").read_text())
        config["tracker"]["minimumEntries"] = 1
        config["tracker"]["maximumEntries"] = 10
        config["verification"]["requestIntervalSeconds"] = 0
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {name: root / name for name in ["config.json", "tracker.html", "sources.csv", "pending.csv", "summary.md", "report.json", "log.md"]}
            paths["config.json"].write_text(json.dumps(config))
            paths["tracker.html"].write_text(tracker_html([row()]))
            write_catalog(paths["sources.csv"], [source()])
            write_catalog(paths["pending.csv"], [])

            original_argv = MODULE.sys.argv
            try:
                MODULE.sys.argv = [
                    "check_case_updates.py",
                    "--config", str(paths["config.json"]),
                    "--tracker-html", str(paths["tracker.html"]),
                    "--sources", str(paths["sources.csv"]),
                    "--pending-sources", str(paths["pending.csv"]),
                    "--log", str(paths["log.md"]),
                    "--initialize-baselines",
                    "--summary", str(paths["summary.md"]),
                    "--report-json", str(paths["report.json"]),
                ]
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(MODULE.main(), 0)
                self.assertFalse(paths["log.md"].exists())

                paths["tracker.html"].write_text(
                    tracker_html([row(status="Government Action Blocked", last="2026-07-21")])
                )
                MODULE.sys.argv = [
                    "check_case_updates.py",
                    "--config", str(paths["config.json"]),
                    "--tracker-html", str(paths["tracker.html"]),
                    "--sources", str(paths["sources.csv"]),
                    "--pending-sources", str(paths["pending.csv"]),
                    "--log", str(paths["log.md"]),
                    "--apply",
                    "--summary", str(paths["summary.md"]),
                    "--report-json", str(paths["report.json"]),
                ]
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(MODULE.main(), 0)
            finally:
                MODULE.sys.argv = original_argv
            report = json.loads(paths["report.json"].read_text())
            self.assertEqual(report["status"], "changes_detected")
            log_text = paths["log.md"].read_text()
            self.assertIn("Government Action Blocked", log_text)
            self.assertIn("Activity code: `CASE-", log_text)
            self.assertIn("Affected source IDs: SRC-0001", log_text)
            with paths["pending.csv"].open(newline="", encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 0)

    def test_config_has_no_tracking_issue_dependency(self):
        config = json.loads((ROOT / ".github" / "case-monitor-bot.json").read_text())
        self.assertEqual(config["schemaVersion"], 5)
        self.assertEqual(config["sourceBaselineField"], "Monitoring Baseline")
        self.assertNotIn("notification", config)
        self.assertEqual(config["automation"]["branch"], "bot/case-monitor-updates")

        workflow = (ROOT / ".github" / "workflows" / "case-monitor-bot.yml").read_text()
        self.assertIn("contents: write", workflow)
        self.assertIn("pull-requests: write", workflow)
        self.assertIn("issues: write", workflow)
        self.assertNotIn("ARRP_PROJECT_TOKEN", workflow)
        self.assertNotIn("317", workflow)
        self.assertLess(workflow.index("git config user.name"), workflow.index("git rebase"))
        self.assertIn('echo "new_change=false"', workflow)
        self.assertIn('echo "new_change=true"', workflow)
        self.assertIn("preserves unresolved changes staged by an earlier run", workflow)


if __name__ == "__main__":
    unittest.main()
