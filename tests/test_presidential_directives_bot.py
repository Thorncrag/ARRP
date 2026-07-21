import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_presidential_directives", ROOT / "scripts" / "check_presidential_directives.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def result(
    document_number="2025-01900",
    title="Ending the Weaponization of the Federal Government",
    president_id="donald-trump",
    president_name="Donald Trump",
    signed="2025-01-20",
    published="2025-01-28",
    subtype="Executive Order",
    number="14147",
):
    return {
        "document_number": document_number,
        "title": title,
        "type": "Presidential Document",
        "subtype": subtype,
        "president": {"identifier": president_id, "name": president_name},
        "signing_date": signed,
        "publication_date": published,
        "presidential_document_number": number,
        "citation": "90 FR 8235",
        "html_url": f"https://www.federalregister.gov/documents/{document_number}",
        "pdf_url": f"https://www.govinfo.gov/content/pkg/{document_number}.pdf",
        "correction_of": None,
        "corrections": [],
        "disposition_notes": None,
    }


class PresidentialDirectivesBotTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(
            (ROOT / ".github" / "presidential-directives-bot.json").read_text()
        )

    def test_scope_covers_trump_biden_trump_without_other_presidents(self):
        examples = [
            result(signed="2017-01-20", published="2017-01-24"),
            result(
                document_number="2021-02034",
                president_id="joe-biden",
                president_name="Joseph R. Biden Jr.",
                signed="2021-01-20",
                published="2021-01-25",
            ),
            result(document_number="2025-01900"),
        ]
        administrations = [
            MODULE.normalize_result(item, self.config["scope"], "2026-07-21")[
                "Administration"
            ]
            for item in examples
        ]
        self.assertEqual(administrations, ["Trump I", "Biden", "Trump II"])
        outside = result(
            president_id="barack-obama", president_name="Barack Obama", signed="2017-01-19"
        )
        self.assertIsNone(MODULE.normalize_result(outside, self.config["scope"], "2026-07-21"))

    def test_discovery_deduplicates_identical_official_records(self):
        item = result()
        merged = MODULE.merge_discovery([], [item, item], self.config, "2026-07-21")
        self.assertEqual(merged["new_ids"], ["2025-01900"])
        self.assertEqual(len(merged["proposed_rows"]), 1)
        self.assertEqual(
            merged["proposed_rows"][0]["Review Status"],
            "New since baseline screening",
        )

    def test_changed_metadata_preserves_human_screening_fields(self):
        row = MODULE.normalize_result(result(), self.config["scope"], "2026-07-20")
        row["Review Status"] = "Routed"
        row["ARRP Record IDs"] = "DOJ-001"
        row["Source IDs"] = "SRC-9999"
        row["Disposition Rationale"] = "Supports an existing manifestation."
        changed = result(title="Ending Weaponization of the Federal Government")
        merged = MODULE.merge_discovery([row], [changed], self.config, "2026-07-21")
        proposed = merged["proposed_rows"][0]
        self.assertEqual(proposed["Review Status"], "Changed since screening")
        self.assertEqual(proposed["ARRP Record IDs"], "DOJ-001")
        self.assertEqual(proposed["Source IDs"], "SRC-9999")
        self.assertEqual(len(merged["changes"]), 1)
        self.assertIn("Title", merged["changes"][0]["changed_fields"])

    def test_missing_official_result_is_reported_but_not_deleted(self):
        row = MODULE.normalize_result(result(), self.config["scope"], "2026-07-20")
        merged = MODULE.merge_discovery([row], [], self.config, "2026-07-21")
        self.assertEqual(merged["missing_ids"], ["2025-01900"])
        self.assertEqual(merged["proposed_rows"], [row])

    def test_relationship_metadata_is_normalized(self):
        item = result(document_number="R1-2025-01900")
        item["correction_of"] = (
            "https://www.federalregister.gov/api/v1/documents/2025-01900"
        )
        item["disposition_notes"] = "Corrects: EO 14147\r\nSee: EO 14148"
        row = MODULE.normalize_result(item, self.config["scope"], "2026-07-21")
        self.assertEqual(row["Related Directive IDs"], "2025-01900")
        self.assertEqual(row["Relationship Notes"], "Corrects: EO 14147 See: EO 14148")

    def test_fixture_run_writes_report_and_proposed_registry_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            registry = temp / "registry.csv"
            fixture = temp / "fixture.json"
            summary = temp / "summary.md"
            report = temp / "report.json"
            proposed = temp / "proposed.csv"
            MODULE.write_registry(registry, [])
            fixture.write_text(json.dumps({"results": [result()]}))

            return_code = MODULE.main(
                [
                    "--registry",
                    str(registry),
                    "--fixture",
                    str(fixture),
                    "--summary",
                    str(summary),
                    "--report-json",
                    str(report),
                    "--proposed-csv",
                    str(proposed),
                    "--as-of",
                    "2026-07-21T00:00:00+00:00",
                ]
            )
            self.assertEqual(return_code, 0)
            self.assertEqual(registry.read_text(), ",".join(MODULE.CSV_FIELDS) + "\n")
            payload = json.loads(report.read_text())
            self.assertEqual(payload["counts"]["new"], 1)
            self.assertEqual(payload["mode"], "read-only-comparison")
            self.assertIn("No catalog or log update was necessary", summary.read_text())
            with proposed.open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["Directive ID"], "2025-01900")

    def test_canonical_registry_write_is_refused(self):
        with self.assertRaises(SystemExit):
            MODULE.main(
                [
                    "--registry",
                    str(ROOT / "inventory" / "presidential-directives.csv"),
                    "--proposed-csv",
                    str(ROOT / "inventory" / "presidential-directives.csv"),
                    "--fixture",
                    str(ROOT / "inventory" / "presidential-directives.csv"),
                ]
            )

    def test_apply_updates_registry_and_material_log_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            registry = temp / "registry.csv"
            fixture = temp / "fixture.json"
            summary = temp / "summary.md"
            report = temp / "report.json"
            log = temp / "SOURCE_MONITOR_LOG.md"
            MODULE.write_registry(registry, [])
            fixture.write_text(json.dumps({"results": [result()]}))

            arguments = [
                "--registry",
                str(registry),
                "--fixture",
                str(fixture),
                "--summary",
                str(summary),
                "--report-json",
                str(report),
                "--apply",
                "--log",
                str(log),
                "--run-url",
                "https://github.com/Thorncrag/ARRP/actions/runs/1",
                "--as-of",
                "2026-07-21T00:00:00+00:00",
            ]
            self.assertEqual(MODULE.main(arguments), 0)
            self.assertEqual(len(MODULE.read_registry(registry)), 1)
            log_text = log.read_text()
            self.assertIn("# Source Monitor Log", log_text)
            self.assertIn("PDM-", log_text)
            self.assertIn("Added directives: **1**", log_text)
            self.assertIn("actions/runs/1", log_text)
            payload = json.loads(report.read_text())
            self.assertTrue(payload["material_update"])
            self.assertTrue(payload["applied"])
            self.assertEqual(payload["mode"], "baseline-update")

            self.assertEqual(MODULE.main(arguments), 0)
            self.assertEqual(log.read_text(), log_text)
            payload = json.loads(report.read_text())
            self.assertFalse(payload["material_update"])
            self.assertFalse(payload["applied"])

    def test_apply_fails_closed_when_existing_directive_disappears(self):
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            registry = temp / "registry.csv"
            fixture = temp / "fixture.json"
            row = MODULE.normalize_result(result(), self.config["scope"], "2026-07-20")
            MODULE.write_registry(registry, [row])
            fixture.write_text(json.dumps({"results": []}))
            with self.assertRaises(SystemExit) as raised:
                MODULE.main(
                    [
                        "--registry",
                        str(registry),
                        "--fixture",
                        str(fixture),
                        "--apply",
                        "--log",
                        str(temp / "log.md"),
                    ]
                )
            self.assertIn("absent from discovery", str(raised.exception))

    def test_checked_in_baseline_has_completed_screening_dispositions(self):
        rows = MODULE.read_registry(ROOT / "inventory" / "presidential-directives.csv")
        self.assertEqual(len(rows), 3007)
        self.assertNotIn("Needs review", {row["Review Status"] for row in rows})
        for row in rows:
            self.assertIn(
                row["Review Status"],
                {"Routed", "Screened — no separate action"},
            )
            self.assertTrue(row["Reviewed Date"])
            self.assertTrue(row["Disposition Rationale"])
            if row["Review Status"] == "Routed":
                self.assertTrue(row["Source IDs"])

    def test_workflow_is_scheduled_and_opens_a_narrow_review_pr(self):
        workflow = (
            ROOT / ".github" / "workflows" / "presidential-directives-bot.yml"
        ).read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("schedule:", workflow)
        self.assertIn('cron: "27 4 * * *"', workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("pull-requests: write", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("scripts/check_presidential_directives.py", workflow)
        self.assertIn("--apply", workflow)
        self.assertIn("Verify the change boundary", workflow)
        self.assertIn("inventory/presidential-directives.csv", workflow)
        self.assertIn("framework/logs/SOURCE_MONITOR_LOG.md", workflow)
        self.assertIn("actions/upload-artifact@", workflow)
        self.assertIn("gh pr create", workflow)
        self.assertIn("--add-assignee", workflow)
        self.assertNotIn("ARRP_PROJECT_TOKEN", workflow)
        self.assertLess(workflow.index("git config user.name"), workflow.index("git rebase"))
        self.assertIn("Detect a pending review branch", workflow)
        self.assertIn("steps.pending.outputs.exists == 'true'", workflow)
        self.assertIn("preserves changes staged by an earlier run", workflow)
        self.assertNotIn("issue comment", workflow)
        self.assertNotIn("317", workflow)
        self.assertIn("if: always()", workflow)
        self.assertTrue(self.config["enabled"])
        self.assertNotIn("notification", self.config)
        self.assertEqual(
            self.config["automation"]["branch"],
            "automation/presidential-directives-monitor",
        )


if __name__ == "__main__":
    unittest.main()
