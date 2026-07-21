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
            self.assertIn("No project files", summary.read_text())
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

    def test_workflow_is_scheduled_read_only_and_preserves_reports(self):
        workflow = (
            ROOT / ".github" / "workflows" / "presidential-directives-bot.yml"
        ).read_text()
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("schedule:", workflow)
        self.assertIn('cron: "27 4 * * *"', workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("scripts/check_presidential_directives.py", workflow)
        self.assertIn("Verify the read-only boundary", workflow)
        self.assertIn('git diff --quiet "${GITHUB_SHA}" -- .', workflow)
        self.assertIn("actions/upload-artifact@", workflow)
        self.assertIn("Notify the project owner", workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn("Preserve a failed comparison outcome", workflow)
        self.assertTrue(self.config["enabled"])
        self.assertEqual(self.config["notification"]["issueNumber"], 317)


if __name__ == "__main__":
    unittest.main()
