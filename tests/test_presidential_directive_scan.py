import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_presidential_directive_gap_scan.py"
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("presidential_directive_scan", MODULE_PATH)
assert SPEC and SPEC.loader
scan = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scan)


class PresidentialDirectiveScanTest(unittest.TestCase):
    @staticmethod
    def directive(**overrides: str) -> dict[str, str]:
        row = {
            "document_number": "2025-99999",
            "directive_type": "executive_order",
            "subtype": "Executive Order",
            "title": "Test Direction Concerning Federal Administration",
            "executive_order_number": "14999",
            "proclamation_number": "",
            "presidential_document_number": "14999",
            "signing_date": "2025-02-01",
            "publication_date": "2025-02-03",
            "html_url": "https://www.federalregister.gov/documents/2025/02/03/2025-99999/test-direction",
            "pdf_url": "https://www.govinfo.gov/content/pkg/FR-2025-02-03/pdf/2025-99999.pdf",
            "raw_text_url": "https://www.federalregister.gov/documents/full_text/text/2025/02/03/2025-99999.txt",
            "correction_of": "",
        }
        row.update(overrides)
        return row

    def test_query_uses_signing_date_and_all_presidential_documents(self) -> None:
        url = scan.federal_register_url("2025-01-20", "2026-07-18", page=2)
        query = parse_qs(urlsplit(url).query)
        self.assertEqual(query["conditions[type][]"], ["PRESDOCU"])
        self.assertEqual(query["conditions[signing_date][gte]"], ["2025-01-20"])
        self.assertEqual(query["conditions[signing_date][lte]"], ["2026-07-18"])
        self.assertEqual(query["page"], ["2"])
        self.assertIn("subtype", query["fields[]"])
        self.assertIn("correction_of", query["fields[]"])

    def test_fetch_paginates_and_includes_presidential_orders(self) -> None:
        pages = [
            {
                "total_pages": 2,
                "results": [
                    {
                        **self.directive(),
                        "subtype": "Executive Order",
                    }
                ],
            },
            {
                "total_pages": 2,
                "results": [
                    {
                        **self.directive(document_number="2025-99998"),
                        "subtype": "Presidential Order",
                    }
                ],
            },
        ]

        def fetcher(_url: str) -> dict[str, object]:
            return pages.pop(0)

        rows = scan.fetch_directives(
            ["executive_order", "presidential_order"],
            "2025-01-20",
            "2026-07-18",
            fetcher,
        )
        self.assertEqual(
            [row["directive_type"] for row in rows],
            ["executive_order", "presidential_order"],
        )

    def test_official_identity_deduplicates_cross_format_urls(self) -> None:
        row = self.directive()
        keys = scan.directive_identity_keys(row)
        self.assertIn("2025-99999", keys)
        self.assertIn("executive order 14999", keys)
        self.assertIn(scan.normalize_url(row["pdf_url"]).lower(), keys)

    def test_existing_record_match_uses_document_number_and_routes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "areas" / "REG" / "REG-001.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "# REG-001\nFederal Register document 2025-99999 supplies the directive.\n",
                encoding="utf-8",
            )
            files, routes = scan.existing_project_matches(
                self.directive(), [(path, path.read_text(encoding="utf-8"))], root=root
            )
        self.assertEqual(files, ["areas/REG/REG-001.md"])
        self.assertEqual(routes, ["REG-001"])

    def test_ceremonial_proclamation_is_no_project_action(self) -> None:
        directive = self.directive(
            directive_type="proclamation",
            subtype="Proclamation",
            title="National Volunteer Recognition Day, 2025",
            executive_order_number="",
            proclamation_number="10999",
        )
        classification = scan.classify_directive(directive, [], [])
        self.assertEqual(
            classification["status"], "routine-ceremonial-no-project-action"
        )

    def test_operative_proclamation_is_not_excluded_by_document_type(self) -> None:
        directive = self.directive(
            directive_type="proclamation",
            subtype="Proclamation",
            title="Continuation of a National Emergency and Tariff Measures",
            executive_order_number="",
            proclamation_number="10998",
        )
        classification = scan.classify_directive(directive, [], [])
        self.assertEqual(classification["status"], "unmatched-agent-review")
        self.assertIn("emergency-force-foreign-authority", classification["signals"])

    def test_unmatched_directive_enters_only_existing_staging_schema(self) -> None:
        directive = self.directive(title="Withholding Funds From State Programs")
        classification = scan.classify_directive(directive, [], [])
        catalog, routing = scan.staging_rows(
            directive, classification, "2026-07-18", "2"
        )
        self.assertEqual(catalog["arrp_coverage_status"], "unmatched-potential-gap")
        self.assertEqual(routing["disposition"], "agent-review-needed")
        self.assertEqual(routing["candidate_id"], "")
        self.assertIn("congressional-displacement", catalog["notes"])

    def test_merge_staging_is_idempotent_and_rejects_conflicts(self) -> None:
        row = {"catalog_id": "TAC-PD-202599999", "value": "one"}
        self.assertEqual(scan.merge_staging([row], [dict(row)]), [row])
        with self.assertRaisesRegex(SystemExit, "different content"):
            scan.merge_staging([row], [{**row, "value": "two"}])

    def test_select_staging_rows_preserves_reconciliation_and_order(self) -> None:
        catalog = [
            {"catalog_id": "TAC-PD-1", "value": "one"},
            {"catalog_id": "TAC-PD-2", "value": "two"},
        ]
        routing = [
            {"catalog_id": "TAC-PD-1", "route": "one"},
            {"catalog_id": "TAC-PD-2", "route": "two"},
        ]
        selected_catalog, selected_routing = scan.select_staging_rows(
            catalog, routing, {"TAC-PD-2"}
        )
        self.assertEqual([row["catalog_id"] for row in selected_catalog], ["TAC-PD-2"])
        self.assertEqual([row["catalog_id"] for row in selected_routing], ["TAC-PD-2"])
        with self.assertRaisesRegex(SystemExit, "not unmatched scan records"):
            scan.select_staging_rows(catalog, routing, {"TAC-PD-3"})


if __name__ == "__main__":
    unittest.main()
