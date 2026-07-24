import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from arrp_context import ContextError  # noqa: E402
from arrp_corpus_index import AUTHORITY_NOTICE, build_index, query_index  # noqa: E402
from elim_execution import (  # noqa: E402
    COMPONENTS,
    RUBRIC_VERSION,
    calculate_score,
    compile_closeout,
    summarize_validation,
    validation_plan,
)


class ExecutionHelperTests(unittest.TestCase):
    def score_input(self):
        return {
            "rubric_version": RUBRIC_VERSION,
            "components": {
                name: {"rating": "half", "evidence_ref": f"AUDIT#{name}"}
                for name in COMPONENTS
            },
            "penalties": [
                {
                    "code": "missing_internal_project_link",
                    "count": 1,
                    "evidence_ref": "finding-1",
                }
            ],
        }

    def test_score_calculator_only_accepts_rubric_ratings_and_does_arithmetic(self):
        result = calculate_score(self.score_input())
        self.assertEqual(result["subtotal"], 50)
        self.assertEqual(result["final_score"], 49)
        self.assertEqual(result["band"], "Early/Partial Draft")
        self.assertTrue(result["judgment_supplied_externally"])

    def test_score_calculator_rejects_arbitrary_points_and_unknown_penalties(self):
        value = self.score_input()
        value["components"]["evidence"]["rating"] = 7
        with self.assertRaisesRegex(ContextError, "zero, half, or full"):
            calculate_score(value)
        value = self.score_input()
        value["penalties"][0]["code"] = "make_score_lower"
        with self.assertRaisesRegex(ContextError, "approved code"):
            calculate_score(value)

    def test_validation_plan_is_changed_file_aware_and_summary_is_compact(self):
        plan = validation_plan(
            ["scripts/example.py", "areas/DOJ/issues/DOJ-002.md"], "issue_development"
        )
        identifiers = {row["id"] for row in plan["checks"]}
        self.assertIn("python_compile", identifiers)
        self.assertIn("repository_consistency", identifiers)
        results = [
            {"id": identifier, "status": "passed", "summary": "ok"}
            for identifier in identifiers
        ]
        summary = summarize_validation(plan, results)
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["counts"]["expected"], len(identifiers))

    def test_closeout_preserves_authority_and_recovery_without_writing_logs(self):
        value = {
            "schema_version": 1,
            "run_id": "R-1",
            "unit_id": "U-1",
            "work_type": "issue_development",
            "outcome": "blocked",
            "authority": {"classification": "delegated_judgment", "basis": "runbook"},
            "files_touched": [],
            "validation": [],
            "continuation": {"state": "retryable", "next_action": "Resume source review"},
        }
        result = compile_closeout(
            value, queue_sha256="0" * 64, context_sha256="c" * 64
        )
        self.assertTrue(result["requeue"])
        self.assertEqual(result["attempt_count"], 1)
        value["outcome"] = "completed"
        value["authority"]["classification"] = "human_reserved"
        value["continuation"] = {"state": "complete", "next_action": None}
        with self.assertRaisesRegex(ContextError, "human-reserved"):
            compile_closeout(value, queue_sha256="0" * 64, context_sha256="c" * 64)


class CorpusIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "areas/TEST/issues").mkdir(parents=True)
        (self.root / "inventory").mkdir()
        (self.root / "areas/TEST/issues/TEST-001.md").write_text(
            "# TEST-001 — Inspector independence\n\nIndependent oversight mechanism.\n",
            encoding="utf-8",
        )
        (self.root / "inventory/sources.csv").write_text(
            "Source ID,Associated Record IDs,Title or Description,Proposition Supported\n"
            "SRC-0001,TEST-001,Inspector report,Independent oversight evidence\n",
            encoding="utf-8",
        )
        self.index = self.root / ".tmp/index.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def test_index_is_bounded_provenance_verified_and_non_authoritative(self):
        built = build_index(self.root, self.index)
        self.assertGreaterEqual(built["records"], 2)
        result = query_index(self.root, self.index, "independent oversight", limit=3)
        self.assertLessEqual(len(result["results"]), 3)
        self.assertEqual(result["authority_notice"], AUTHORITY_NOTICE)
        self.assertTrue(any(row["record_key"] == "TEST-001" for row in result["results"]))
        (self.root / "areas/TEST/issues/TEST-001.md").write_text(
            "# TEST-001\nChanged\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(ContextError, "stale"):
            query_index(self.root, self.index, "changed")

    def test_index_refuses_canonical_output_location(self):
        with self.assertRaisesRegex(ContextError, "ignored .tmp"):
            build_index(self.root, self.root / "index.sqlite3")


if __name__ == "__main__":
    unittest.main()
