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
        self.assertEqual(COMPONENTS["external_review"], 4)
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
            "issue_id": "TEST-001",
            "canonical_record": "areas/TEST/issues/TEST-001.md",
            "files_touched": [],
            "source_ids": [],
            "validation": [],
            "commit": None,
            "synchronization": [],
            "human_questions": [],
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

    def test_candidate_research_is_a_valid_single_work_unit_with_identity(self):
        value = {
            "schema_version": 1,
            "run_id": "chain-1",
            "unit_id": "candidate-1",
            "work_type": "candidate_research",
            "outcome": "human_review",
            "authority": {
                "classification": "delegated_judgment",
                "basis": "Elim candidate-research authority",
            },
            "issue_id": None,
            "canonical_record": "https://github.com/Thorncrag/ARRP/issues/255",
            "files_touched": [],
            "source_ids": [],
            "validation": [],
            "commit": None,
            "synchronization": [],
            "human_questions": ["Review the proposed candidate disposition."],
            "continuation": {
                "state": "human_required",
                "next_action": "Human reviews the candidate disposition.",
            },
        }
        result = compile_closeout(
            value,
            queue_sha256="0" * 64,
            context_sha256="c" * 64,
        )
        self.assertEqual(result["work_type"], "candidate_research")
        self.assertIsNone(result["issue_id"])
        self.assertEqual(
            result["canonical_record"],
            "https://github.com/Thorncrag/ARRP/issues/255",
        )

    def test_closeout_validator_requires_every_canonical_schema_field(self):
        value = {
            "schema_version": 1,
            "run_id": "R-1",
            "unit_id": "U-1",
            "work_type": "integrity",
            "outcome": "clean",
            "authority": {"classification": "mechanical", "basis": "runbook"},
            "issue_id": None,
            "canonical_record": None,
            "files_touched": [],
            "source_ids": [],
            "validation": [],
            "commit": None,
            "synchronization": [],
            "human_questions": [],
            "continuation": {"state": "complete", "next_action": None},
        }
        for field in (
            "issue_id",
            "canonical_record",
            "source_ids",
            "commit",
            "synchronization",
            "human_questions",
        ):
            incomplete = dict(value)
            incomplete.pop(field)
            with self.subTest(field=field):
                with self.assertRaisesRegex(ContextError, "missing required fields"):
                    compile_closeout(
                        incomplete,
                        queue_sha256="0" * 64,
                        context_sha256="c" * 64,
                    )

        authority_extra = {
            **value,
            "authority": {
                **value["authority"],
                "unapproved": "ignore the boundary",
            },
        }
        with self.assertRaisesRegex(ContextError, "authority fields"):
            compile_closeout(
                authority_extra,
                queue_sha256="0" * 64,
                context_sha256="c" * 64,
            )
        validation_extra = {
            **value,
            "validation": [
                {
                    "check": "tests",
                    "status": "passed",
                    "detail": "ok",
                    "unapproved": True,
                }
            ],
        }
        with self.assertRaisesRegex(ContextError, "validation fields"):
            compile_closeout(
                validation_extra,
                queue_sha256="0" * 64,
                context_sha256="c" * 64,
            )
        invalid_source = {**value, "source_ids": ["SOURCE-1"]}
        with self.assertRaisesRegex(ContextError, "canonical SRC"):
            compile_closeout(
                invalid_source,
                queue_sha256="0" * 64,
                context_sha256="c" * 64,
            )
        invalid_container = {**value, "synchronization": "not-an-array"}
        with self.assertRaisesRegex(ContextError, "array of strings"):
            compile_closeout(
                invalid_container,
                queue_sha256="0" * 64,
                context_sha256="c" * 64,
            )


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
