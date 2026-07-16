import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from apply_source_adjudication import UNRESOLVED_DISPOSITIONS, validate_integration_targets
from complete_source_catalog_adjudication import (
    Episode,
    placement_routes,
    preliminary_classification,
)
from source_adjudication_common import (
    merge_routes,
    normalize_url,
    read_csv,
    write_csv_preserving_unchanged,
)


class SourceAdjudicationTest(unittest.TestCase):
    @staticmethod
    def catalog_record(**overrides: str) -> dict[str, str]:
        row = {
            "catalog_id": "TAC-TEST-001",
            "term": "2",
            "record_type": "science-integrity-discovery-lead",
            "action_or_policy": "Agency ends research program",
            "action_date_or_period": "",
            "responsible_actor_or_category": "Federal → Agency; Research Hindrance",
            "legal_question_or_outcome": "",
            "litigation_posture": "specialist tracker update status: No Updates",
            "screening_track": "verify-legal-question-and-institutional-defect",
            "source_family": "Silencing Science Tracker",
            "source_entry_url": "https://example.org/item",
            "representative_case": "",
            "representative_case_url": "",
            "official_action_url": "",
            "arrp_coverage_status": "possible-existing-coverage",
            "provisional_arrp_routes": "FACT-001",
            "normalization_status": "source-normalized",
            "last_checked": "2026-07-16",
            "notes": "",
        }
        row.update(overrides)
        return row

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

    def test_retained_evidence_requires_reader_or_queue_target(self) -> None:
        with self.assertRaisesRegex(SystemExit, "association alone"):
            validate_integration_targets(
                {
                    "disposition": "supporting-evidence",
                    "catalog_ids": ["TAC-TEST-001"],
                    "integration_targets": [],
                },
                set(),
            )

    def test_existing_issue_queue_target_requires_catalog_row(self) -> None:
        target = "research/existing-issue-evidence-integration.csv"
        with self.assertRaisesRegex(SystemExit, "missing catalog records"):
            validate_integration_targets(
                {
                    "disposition": "comparator-or-counterexample",
                    "catalog_ids": ["TAC-TEST-001"],
                    "integration_targets": [target],
                },
                set(),
            )
        validate_integration_targets(
            {
                "disposition": "comparator-or-counterexample",
                "catalog_ids": ["TAC-TEST-001"],
                "integration_targets": [target],
            },
            {"TAC-TEST-001"},
        )

    def test_registry_only_corroboration_requires_explicit_qualitative_finding(self) -> None:
        decision = {
            "disposition": "corroborating-source",
            "catalog_ids": ["TAC-TEST-001"],
            "integration_targets": [],
            "reader_facing_value": "no-additional-value",
            "registry_only_rationale": "The issue page already cites the controlling opinion; this report adds no distinct proposition.",
        }
        validate_integration_targets(decision, set())

        decision["registry_only_rationale"] = ""
        with self.assertRaisesRegex(SystemExit, "explicit no-additional-reader-value"):
            validate_integration_targets(decision, set())

    def test_formal_horizon_route_keeps_one_existing_record_boundary(self) -> None:
        record = self.catalog_record(catalog_id="TAC-IPT-138")
        episode = Episode(
            group="EP-TEST",
            records=[record],
            routes=["HOR-034", "CIV-009", "REC-001"],
            primary=record,
            score=1,
        )
        self.assertEqual(placement_routes(episode), ["HOR-034", "CIV-009"])

    def test_science_policy_lead_requires_information_integrity_mechanism(self) -> None:
        record = self.catalog_record()
        episode = Episode(
            group="EP-TEST",
            records=[record],
            routes=["FACT-001"],
            primary=record,
            score=1,
        )
        disposition, _ = preliminary_classification(episode)
        self.assertEqual(disposition, "rejected")

        record["action_or_policy"] = "Agency deletes scientific report from website"
        disposition, _ = preliminary_classification(episode)
        self.assertEqual(disposition, "shortlist")


if __name__ == "__main__":
    unittest.main()
