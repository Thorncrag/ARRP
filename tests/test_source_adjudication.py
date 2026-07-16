import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from apply_source_adjudication import UNRESOLVED_DISPOSITIONS
from source_adjudication_common import (
    merge_routes,
    normalize_url,
    read_csv,
    write_csv_preserving_unchanged,
)


class SourceAdjudicationTest(unittest.TestCase):
    def test_normalize_url_removes_tracking_and_fragment(self) -> None:
        self.assertEqual(
            normalize_url("http://Example.com/report/?utm_source=x&b=2&a=1#page"),
            "https://example.com/report?a=1&b=2",
        )

    def test_normalize_url_preserves_document_query(self) -> None:
        self.assertEqual(
            normalize_url("https://uscode.house.gov/view.xhtml?edition=prelim&req=abc"),
            "https://uscode.house.gov/view.xhtml?edition=prelim&req=abc",
        )

    def test_merge_routes_is_stable_and_unique(self) -> None:
        self.assertEqual(
            merge_routes(["REG-006", "FACT-001"], ["FACT-001", "HOR-036"]),
            ["REG-006", "FACT-001", "HOR-036"],
        )

    def test_unresolved_dispositions_remain_in_temporary_queue(self) -> None:
        self.assertEqual(
            UNRESOLVED_DISPOSITIONS,
            {
                "preliminary-horizon-candidate",
                "insufficiently-verified",
                "unresolved-legal-question",
            },
        )

    def test_source_writer_preserves_unchanged_record_text(self) -> None:
        original_text = (
            'Source ID,Associated Record IDs,Notes\n'
            'SRC-0001,REG-001,"deliberately quoted"\n'
            'SRC-0002,REG-002,"line one\nline two"\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.csv"
            path.write_text(original_text, encoding="utf-8")
            original = read_csv(path)
            updated = [dict(row) for row in original]
            updated[1]["Associated Record IDs"] = "REG-002; HOR-036"
            write_csv_preserving_unchanged(
                path,
                original,
                updated,
                list(original[0]),
                key_field="Source ID",
            )
            result = path.read_text(encoding="utf-8")

        self.assertIn('SRC-0001,REG-001,"deliberately quoted"\n', result)
        self.assertIn('SRC-0002,REG-002; HOR-036,"line one\nline two"\n', result)


if __name__ == "__main__":
    unittest.main()
