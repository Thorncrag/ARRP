from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.operational_incidents import (
    IncidentContractError,
    incident_projection,
    project_incident_log,
    read_incident_events,
    reconcile_failure_spool,
    record_incident_occurrence,
    sanitize_text,
    spool_failure_incident,
    transition_incident,
)


class OperationalIncidentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.events = self.root / "operational-incidents.jsonl"

    def record(
        self,
        occurrence_id: str,
        *,
        component: str = "project-integrity-bot",
        failure_class: str = "missing-feed",
        observed_at: str = "2026-07-28T12:00:00Z",
    ) -> dict:
        return record_incident_occurrence(
            self.events,
            component=component,
            prerequisite="integrity-feed",
            failure_class=failure_class,
            impact="blocking",
            summary="Integrity feed was unavailable.",
            reported_by="Run Coordinator",
            owner=None,
            recommended_owner="Project Integrity Bot",
            next_action="Restore and validate the exact feed.",
            occurrence_id=occurrence_id,
            observed_at=observed_at,
            source_ref=f"run:{occurrence_id}",
            diagnostic="The required feed was missing.",
            run_id=occurrence_id,
            evidence_refs=[f"run:{occurrence_id}"],
            active_links=["automation-role:project-integrity-bot", "data:integrity"],
            now=datetime(2026, 7, 28, 12, 30, tzinfo=timezone.utc),
        )

    def test_repeat_occurrences_group_without_losing_run_history(self) -> None:
        first = self.record("run-1")
        second = self.record(
            "run-2", observed_at="2026-07-28T13:00:00Z"
        )
        self.assertEqual(first["incident_id"], second["incident_id"])
        projection = project_incident_log(self.events)
        self.assertTrue(projection["complete"])
        self.assertEqual(projection["unresolved_count"], 1)
        incident = projection["items"][0]
        self.assertEqual(
            [row["occurrence_id"] for row in incident["occurrences"]],
            ["run-1", "run-2"],
        )
        self.assertEqual(incident["affected_runs"], ["run-1", "run-2"])

    def test_unrelated_success_cannot_resolve_an_incident(self) -> None:
        self.record("run-1")
        before = project_incident_log(self.events)
        # A generally healthy later run is deliberately not an incident event.
        after = incident_projection(read_incident_events(self.events))
        self.assertEqual(before["unresolved_count"], after["unresolved_count"])
        self.assertEqual(after["items"][0]["status"], "open")

    def test_resolution_requires_exact_recovery_proof(self) -> None:
        opened = self.record("run-1")
        with self.assertRaisesRegex(
            IncidentContractError, "exact recovery proof"
        ):
            transition_incident(
                self.events,
                incident_id=opened["incident_id"],
                status="resolved",
                recorded_by="Run Coordinator",
                next_action="None.",
            )
        transition_incident(
            self.events,
            incident_id=opened["incident_id"],
            status="resolved",
            recorded_by="Run Coordinator",
            next_action="Retain the verified history.",
            recovery={
                "verified_at": "2026-07-28T14:00:00Z",
                "closure_test": "The exact feed validates and the scheduled stage completes.",
                "result": "Passed against run-3.",
                "recorded_by": "Run Coordinator",
                "evidence_refs": ["run:run-3"],
            },
        )
        projection = project_incident_log(self.events)
        self.assertEqual(projection["unresolved_count"], 0)
        self.assertEqual(projection["items"][0]["status"], "resolved")

    def test_recurrence_after_resolution_creates_a_linked_incident(self) -> None:
        opened = self.record("run-1")
        transition_incident(
            self.events,
            incident_id=opened["incident_id"],
            status="resolved",
            recorded_by="Run Coordinator",
            next_action="Retain history.",
            recovery={
                "verified_at": "2026-07-28T14:00:00Z",
                "closure_test": "Exact retry completes.",
                "result": "Passed.",
                "recorded_by": "Run Coordinator",
                "evidence_refs": ["run:run-2"],
            },
        )
        recurrence = self.record(
            "run-4", observed_at="2026-07-29T12:00:00Z"
        )
        self.assertNotEqual(opened["incident_id"], recurrence["incident_id"])
        projection = project_incident_log(self.events)
        current = next(
            item for item in projection["items"] if item["status"] == "open"
        )
        self.assertEqual(current["prior_incident_id"], opened["incident_id"])

    def test_unavailable_feed_is_not_zero_or_green(self) -> None:
        self.events.write_text("{not-json}\n", encoding="utf-8")
        projection = project_incident_log(self.events)
        self.assertFalse(projection["complete"])
        self.assertIsNone(projection["unresolved_count"])
        self.assertEqual(projection["impact_state"], "gray")

    def test_sensitive_diagnostics_are_redacted(self) -> None:
        credential_like = (
            "Authorization"
            + ": "
            + "token-secret "
            + "password"
            + "="
            + "hunter2 "
            + "gho_"
            + "1234567890abcdefghijklmnop"
        )
        text = sanitize_text(
            credential_like
        )
        self.assertNotIn("hunter2", text)
        self.assertNotIn("gho_", text)
        self.assertIn("[REDACTED]", text)

    def test_failure_spool_reconciles_once(self) -> None:
        spool = self.root / "incident-spool.jsonl"
        spool_failure_incident(
            spool,
            run_id="run-failed",
            component="run-coordinator-bot",
            prerequisite="elim-result",
            failure_class="invalid-schema",
            diagnostic="Elim returned no valid result.",
        )
        self.assertEqual(reconcile_failure_spool(spool, self.events), 1)
        self.assertEqual(reconcile_failure_spool(spool, self.events), 0)
        projection = project_incident_log(self.events)
        self.assertEqual(projection["unresolved_count"], 1)
        self.assertEqual(
            projection["items"][0]["occurrences"][0]["run_id"],
            "run-failed",
        )

    def test_disclosure_prevention_spool_reconciles_as_near_miss(self) -> None:
        spool = self.root / "incident-spool.jsonl"
        spool_failure_incident(
            spool,
            run_id="run-disclosure-prevented",
            component="github-disclosure-gate",
            prerequisite="outbound-content",
            failure_class="outbound-disclosure-prevented",
            diagnostic="Opaque disclosure finding blocked transmission.",
            impact="near_miss",
            summary="A project-operated disclosure was prevented before transmission.",
            reported_by="GitHub disclosure gate",
            recommended_owner="Project security governance",
            next_action="Review the opaque finding and sanitize the preserved artifact.",
            active_links=("log:incidents",),
        )
        self.assertEqual(reconcile_failure_spool(spool, self.events), 1)
        projection = project_incident_log(self.events)
        incident = projection["items"][0]
        self.assertEqual(incident["impact"], "near_miss")
        self.assertEqual(incident["reported_by"], "GitHub disclosure gate")


if __name__ == "__main__":
    unittest.main()
