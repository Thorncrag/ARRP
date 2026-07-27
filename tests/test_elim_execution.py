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
    parse_discovery_markers,
    merge_gap_obligation_state,
    reconstruct_gap_obligation_state,
    render_discovery_markers,
    summarize_validation,
    validate_discovery_records,
    verify_discovery_markers,
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

    def discovery_result(
        self,
        *,
        disposition="retained",
        authority_disposition="uncertain",
        status="open",
        observed_at="2026-07-25T12:00:00+00:00",
        resolution=None,
    ):
        unit = {
            "id": "DISC-gap-1",
            "obligation_id": "GAP-structure-1",
            "domain": "project-structure",
            "discovery_context": "Quiet-queue governance review.",
            "observed_at": observed_at,
            "source_revision": "a" * 40,
            "evidence": ["framework/PROJECT_STRUCTURE.md documents the expected owner."],
            "reasoning": "The current record omits the required canonical linkage.",
            "uncertainty": "The intended owner is not yet conclusive.",
            "affected_records": ["framework/PROJECT_STRUCTURE.md"],
            "consequence": "The gap can evade ordinary deterministic routing.",
            "authority": {
                "classification": "delegated_judgment",
                "basis": "Elim governance-discovery runbook.",
                "disposition": authority_disposition,
            },
            "action_rationale": "Retain the gap until the ownership evidence is conclusive.",
            "changed_files": ["framework/records/automation/elim-run-log.md"],
            "affected_surfaces": ["repository", "automation", "console"],
            "validation_readback": [
                {
                    "check": "canonical detail readback",
                    "status": "passed",
                    "evidence": "The Run Log contains the linked detail.",
                }
            ],
            "disposition": disposition,
            "canonical_detail": "framework/records/automation/elim-run-log.md",
            "provenance": ["framework/records/automation/elim-run-log.md#gap-structure-1"],
            "owner": "Elim",
            "next_action": "Recheck the owning record at the next current revision.",
            "next_trigger": "A governing or ownership record changes.",
            "outside_contribution": None,
        }
        return {
            "run_id": "chain-1",
            "files_touched": ["framework/records/automation/elim-run-log.md"],
            "discovered_work_units": [unit],
            "gap_obligation_updates": [
                {
                    "obligation_id": "GAP-structure-1",
                    "discovered_work_unit_id": "DISC-gap-1",
                    "status": status,
                    "observed_at": observed_at,
                    "resolution": resolution,
                }
            ],
        }

    def governance_review_result(
        self,
        *,
        observed_at="2026-07-25T12:00:00+00:00",
        disposition="no_material_finding",
    ):
        return {
            "run_id": "chain-governance",
            "unit_id": "selected-governance",
            "files_touched": ["framework/records/automation/elim-run-log.md"],
            "discovered_work_units": [
                {
                    "id": "DISC-governance-control",
                    "obligation_id": None,
                    "domain": "project-governance-review",
                    "discovery_context": "Reviewed every minimum governance domain.",
                    "observed_at": observed_at,
                    "source_revision": "c" * 40,
                    "evidence": ["The bounded review covered every required domain."],
                    "reasoning": "The review outcome is recorded without inventing work.",
                    "uncertainty": None,
                    "affected_records": ["framework/records/automation/elim-run-log.md"],
                    "consequence": "Governance discovery is current for its cadence.",
                    "authority": {
                        "classification": "delegated_judgment",
                        "basis": "Elim governance-discovery runbook.",
                        "disposition": "permitted",
                    },
                    "action_rationale": "Record the review result and next trigger.",
                    "changed_files": ["framework/records/automation/elim-run-log.md"],
                    "affected_surfaces": ["repository", "automation", "console"],
                    "validation_readback": [
                        {
                            "check": "review-control readback",
                            "status": "passed",
                            "evidence": "The current Run Log section was read back.",
                        }
                    ],
                    "disposition": disposition,
                    "canonical_detail": "framework/records/automation/elim-run-log.md",
                    "provenance": ["framework/records/automation/elim-run-log.md#governance"],
                    "owner": "Elim",
                    "next_action": "Wait for the recorded next trigger.",
                    "next_trigger": "The 168-hour minimum interval elapses.",
                    "outside_contribution": None,
                }
            ],
            "gap_obligation_updates": [],
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
            "discovered_work_units": [],
            "gap_obligation_updates": [],
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
            "discovered_work_units": [],
            "gap_obligation_updates": [],
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
            "discovered_work_units": [],
            "gap_obligation_updates": [],
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

    def test_gap_obligation_retains_stable_identity_and_full_occurrence_history(self):
        first = self.discovery_result()
        state = merge_gap_obligation_state(None, first)
        retained = state["items"][0]
        self.assertEqual(retained["first_seen"], "2026-07-25T12:00:00+00:00")
        self.assertEqual(retained["occurrence_count"], 1)
        self.assertEqual(retained["authority_disposition"], "uncertain")
        self.assertIn("canonical_detail", retained)
        self.assertIn("affected_surfaces", retained)
        self.assertIn("validation_readback", retained)

        second = self.discovery_result(observed_at="2026-07-27T12:00:00+00:00")
        second["run_id"] = "chain-2"
        state = merge_gap_obligation_state(state, second)
        retained = state["items"][0]
        self.assertEqual(retained["first_seen"], "2026-07-25T12:00:00+00:00")
        self.assertEqual(retained["last_checked"], "2026-07-27T12:00:00+00:00")
        self.assertEqual(retained["occurrence_count"], 2)
        self.assertEqual(retained["age_days"], 2)
        self.assertEqual(len(retained["occurrences"]), 2)
        self.assertEqual(len(retained["status_history"]), 2)

        absent = {
            "run_id": "chain-3",
            "files_touched": [],
            "discovered_work_units": [],
            "gap_obligation_updates": [],
        }
        self.assertEqual(merge_gap_obligation_state(state, absent), state)

    def test_committed_markers_reconstruct_ledger_after_cache_loss(self):
        first = self.discovery_result()
        second = self.discovery_result(observed_at="2026-07-27T12:00:00+00:00")
        first["unit_id"] = "selected-1"
        second["run_id"] = "chain-2"
        second["unit_id"] = "selected-2"
        run_log = "\n".join(
            (
                "# Elim Run Log",
                render_discovery_markers(first),
                render_discovery_markers(second),
            )
        )
        markers = parse_discovery_markers(run_log)
        self.assertEqual(len(markers), 2)
        reconstructed = reconstruct_gap_obligation_state(run_log)
        item = reconstructed["items"][0]
        self.assertEqual(item["obligation_id"], "GAP-structure-1")
        self.assertEqual(item["occurrence_count"], 2)
        self.assertEqual(item["first_seen"], "2026-07-25T12:00:00+00:00")
        self.assertEqual(item["last_checked"], "2026-07-27T12:00:00+00:00")
        verify_discovery_markers(render_discovery_markers(second), second)

        tampered = json.loads(json.dumps(second))
        tampered["discovered_work_units"][0]["reasoning"] = "Different reasoning."
        with self.assertRaisesRegex(ContextError, "exactly match"):
            verify_discovery_markers(render_discovery_markers(second), tampered)

    def test_governance_review_control_is_durable_without_creating_a_gap(self):
        result = self.governance_review_result()
        run_log = "# Elim Run Log\n\n" + render_discovery_markers(result)
        reconstructed = reconstruct_gap_obligation_state(run_log)
        self.assertEqual(reconstructed["items"], [])
        self.assertEqual(
            reconstructed["governance_review"]["last_reviewed_at"],
            "2026-07-25T12:00:00+00:00",
        )
        self.assertEqual(
            reconstructed["governance_review"]["disposition"],
            "no_material_finding",
        )
        self.assertEqual(
            reconstructed["governance_review"]["selected_unit_id"],
            "selected-governance",
        )

    def test_reporting_or_prohibited_authority_cannot_close_a_gap(self):
        reported = self.discovery_result(
            disposition="reported",
            authority_disposition="forbidden",
            status="resolved",
            resolution={
                "kind": "verified_resolution",
                "verified_at": "2026-07-25T12:05:00+00:00",
                "evidence": "The finding was reported.",
                "source_revision": "a" * 40,
                "recorded_by": "Elim",
            },
        )
        with self.assertRaisesRegex(
            ContextError,
            "prohibited|reporting a finding|permitted repair",
        ):
            validate_discovery_records(reported)

        human_closed = self.discovery_result(
            disposition="reported",
            authority_disposition="forbidden",
            status="human_disposition",
            resolution={
                "kind": "human_disposition",
                "verified_at": "2026-07-25T12:05:00+00:00",
                "evidence": "Recorded human disposition HD-1.",
                "source_revision": "a" * 40,
                "recorded_by": "project owner",
            },
        )
        validate_discovery_records(human_closed)

    def test_discovery_cannot_close_without_documentation_and_readback_floor(self):
        fixed = self.discovery_result(
            disposition="fixed",
            authority_disposition="permitted",
            status="resolved",
            resolution={
                "kind": "verified_resolution",
                "verified_at": "2026-07-25T12:05:00+00:00",
                "evidence": "Focused tests and canonical readback passed.",
                "source_revision": "a" * 40,
                "recorded_by": "Elim",
            },
        )
        fixed["discovered_work_units"][0]["changed_files"] = [
            "framework/records/automation/elim-run-log.md"
        ]
        validate_discovery_records(fixed)
        for missing in (
            "action_rationale",
            "affected_surfaces",
            "validation_readback",
            "canonical_detail",
            "owner",
            "next_trigger",
        ):
            broken = json.loads(json.dumps(fixed))
            broken["discovered_work_units"][0].pop(missing)
            with self.subTest(missing=missing):
                with self.assertRaisesRegex(ContextError, "fields"):
                    validate_discovery_records(broken)

    def test_outside_contribution_requires_exact_revision_and_complete_check_floor(self):
        result = self.discovery_result()
        result["discovered_work_units"][0]["outside_contribution"] = {
            "identity": "PR-42",
            "revision": "b" * 40,
            "classification": "outside contribution",
            "checks": [
                {
                    "check": check,
                    "status": "passed",
                    "evidence": f"{check} verified at exact head.",
                }
                for check in (
                    "identity",
                    "classification",
                    "required_fields",
                    "canonical_linkage",
                    "evidence_and_provenance",
                    "lifecycle_and_authority",
                    "generated_views",
                    "tests",
                    "documentation",
                )
            ],
            "integration_posture": "ready",
        }
        validate_discovery_records(result)
        result["discovered_work_units"][0]["outside_contribution"]["checks"].pop()
        with self.assertRaisesRegex(ContextError, "required floor"):
            validate_discovery_records(result)


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
