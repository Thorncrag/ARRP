from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from scripts.path_authority import PathAuthorityError, ProjectPathAuthority
from scripts.security_incidents import (
    LIFECYCLE,
    UNRESOLVED_STATES,
    SecurityIncidentContractError,
    link_incidents,
    main,
    opaque_evidence_reference,
    project_security_incident_log,
    read_relation_events,
    read_security_events,
    record_security_occurrence,
    relationship_projection,
    safe_text,
    security_identity_key,
    security_incident_projection,
    transition_security_incident,
    unlink_incidents,
    validate_relation_event,
    validate_security_event,
)


UTC = timezone.utc


class SecurityIncidentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.events = self.root / "security-incidents.jsonl"
        self.relations = self.root / "incident-relations.jsonl"

    def record(
        self,
        occurrence_id: str,
        *,
        safe_summary: str = "A protected review requires investigation.",
        observed_at: str = "2026-07-29T12:00:00Z",
        now: datetime = datetime(2026, 7, 29, 12, 30, tzinfo=UTC),
    ) -> dict:
        return record_security_occurrence(
            self.events,
            security_domain="repository-security",
            protected_surface="outbound-disclosure",
            event_class="material-near-miss",
            safe_summary=safe_summary,
            reported_by="Deterministic security recorder",
            owner=None,
            recommended_owner="Owner security review",
            next_action="Open the protected evidence authority.",
            occurrence_id=occurrence_id,
            observed_at=observed_at,
            source_ref=f"restricted:security-evidence/{occurrence_id}",
            safe_observation="A protected review boundary was reached.",
            restricted_evidence_refs=[
                f"restricted:security-evidence/{occurrence_id}"
            ],
            now=now,
        )

    @staticmethod
    def closure(reference: str = "closure-1") -> dict:
        return {
            "verified_at": "2026-07-29T14:00:00Z",
            "disposition_code": "remediated",
            "closure_test": "The exact protected validation completed.",
            "result": "The required protected check passed.",
            "recorded_by": "Owner security review",
            "restricted_evidence_refs": [
                f"restricted:security-evidence/{reference}"
            ],
        }

    def test_sec_allocator_is_independent_and_rejects_inc_ids(self) -> None:
        event = self.record("occurrence-1")
        self.assertEqual(event["security_incident_id"], "SEC-2026-001")
        invalid = dict(event)
        invalid["security_incident_id"] = "INC-2026-001"
        invalid["event_id"] = "INC-2026-001:0001"
        invalid["event_sha256"] = None
        with self.assertRaisesRegex(
            SecurityIncidentContractError,
            "invalid Security Incident ID",
        ):
            validate_security_event(invalid)

    def test_repeat_occurrences_group_by_typed_identity_not_prose(self) -> None:
        first = self.record("occurrence-1")
        second = self.record(
            "occurrence-2",
            safe_summary="The safe presentation wording changed.",
            observed_at="2026-07-29T13:00:00Z",
            now=datetime(2026, 7, 29, 13, 30, tzinfo=UTC),
        )
        self.assertEqual(
            first["security_incident_id"],
            second["security_incident_id"],
        )
        projection = project_security_incident_log(self.events)
        self.assertEqual(projection["unresolved_count"], 1)
        incident = projection["items"][0]
        self.assertEqual(
            [row["occurrence_id"] for row in incident["occurrences"]],
            ["occurrence-1", "occurrence-2"],
        )
        self.assertEqual(
            incident["safe_summary"],
            "The safe presentation wording changed.",
        )

    def test_identity_is_typed_and_independent_of_summary(self) -> None:
        identity = security_identity_key(
            "repository-security",
            "outbound-disclosure",
            "material-near-miss",
        )
        self.assertEqual(
            identity,
            security_identity_key(
                "repository-security",
                "outbound-disclosure",
                "material-near-miss",
            ),
        )
        self.assertNotEqual(
            identity,
            security_identity_key(
                "repository-security",
                "outbound-disclosure",
                "confirmed-event",
            ),
        )
        with self.assertRaisesRegex(
            SecurityIncidentContractError,
            "typed identity",
        ):
            security_identity_key(
                "A prose description",
                "outbound-disclosure",
                "confirmed-event",
            )

    def test_all_nonresolved_lifecycle_states_remain_unresolved(self) -> None:
        opened = self.record("occurrence-1")
        incident_id = opened["security_incident_id"]
        for offset, state in enumerate(LIFECYCLE[1:-1], 1):
            transition_security_incident(
                self.events,
                security_incident_id=incident_id,
                status=state,
                recorded_by="Owner security review",
                next_action="Continue the protected workflow.",
                now=datetime(2026, 7, 29, 12, 30 + offset, tzinfo=UTC),
            )
            projection = project_security_incident_log(self.events)
            self.assertIn(state, UNRESOLVED_STATES)
            self.assertEqual(projection["unresolved_count"], 1)
        transition_security_incident(
            self.events,
            security_incident_id=incident_id,
            status="Resolved",
            recorded_by="Owner security review",
            next_action="Retain the protected history.",
            closure=self.closure(),
            now=datetime(2026, 7, 29, 14, 30, tzinfo=UTC),
        )
        projection = project_security_incident_log(self.events)
        self.assertEqual(projection["unresolved_count"], 0)
        self.assertEqual(projection["items"][0]["status"], "Resolved")

    def test_resolution_requires_exact_closure_evidence(self) -> None:
        incident_id = self.record("occurrence-1")["security_incident_id"]
        with self.assertRaisesRegex(
            SecurityIncidentContractError,
            "exact closure evidence",
        ):
            transition_security_incident(
                self.events,
                security_incident_id=incident_id,
                status="Resolved",
                recorded_by="Owner security review",
                next_action="Retain history.",
            )
        incomplete = self.closure()
        incomplete["restricted_evidence_refs"] = []
        with self.assertRaisesRegex(
            SecurityIncidentContractError,
            "at least one opaque restricted reference",
        ):
            transition_security_incident(
                self.events,
                security_incident_id=incident_id,
                status="Resolved",
                recorded_by="Owner security review",
                next_action="Retain history.",
                closure=incomplete,
            )
        self.assertEqual(
            project_security_incident_log(self.events)["unresolved_count"],
            1,
        )

    def test_recurrence_after_resolution_creates_linked_new_sec(self) -> None:
        first = self.record("occurrence-1")
        transition_security_incident(
            self.events,
            security_incident_id=first["security_incident_id"],
            status="Resolved",
            recorded_by="Owner security review",
            next_action="Retain the protected history.",
            closure=self.closure(),
            now=datetime(2026, 7, 29, 14, 30, tzinfo=UTC),
        )
        recurrence = self.record(
            "occurrence-2",
            observed_at="2026-07-30T12:00:00Z",
            now=datetime(2026, 7, 30, 12, 30, tzinfo=UTC),
        )
        self.assertEqual(recurrence["security_incident_id"], "SEC-2026-002")
        self.assertEqual(
            recurrence["prior_security_incident_id"],
            first["security_incident_id"],
        )
        projection = project_security_incident_log(self.events)
        self.assertEqual(projection["count"], 2)
        self.assertEqual(projection["unresolved_count"], 1)

    def test_recurrence_link_is_required_and_immutable(self) -> None:
        first = self.record("occurrence-1")
        transition_security_incident(
            self.events,
            security_incident_id=first["security_incident_id"],
            status="Resolved",
            recorded_by="Owner security review",
            next_action="Retain the protected history.",
            closure=self.closure(),
            now=datetime(2026, 7, 29, 14, 30, tzinfo=UTC),
        )
        self.record(
            "occurrence-2",
            observed_at="2026-07-30T12:00:00Z",
            now=datetime(2026, 7, 30, 12, 30, tzinfo=UTC),
        )
        events = read_security_events(self.events)
        recurrence = dict(events[-1])
        recurrence["prior_security_incident_id"] = None
        recurrence["event_sha256"] = None
        with self.assertRaisesRegex(
            SecurityIncidentContractError,
            "omits its prior resolved recurrence link",
        ):
            security_incident_projection([*events[:-1], recurrence])

    def test_occurrence_cannot_change_lifecycle_state(self) -> None:
        self.record("occurrence-1")
        self.record(
            "occurrence-2",
            observed_at="2026-07-29T13:00:00Z",
            now=datetime(2026, 7, 29, 13, 30, tzinfo=UTC),
        )
        events = read_security_events(self.events)
        invalid = dict(events[-1])
        invalid["status"] = "Investigating"
        invalid["event_sha256"] = None
        with self.assertRaisesRegex(
            SecurityIncidentContractError,
            "wrong event type",
        ):
            security_incident_projection([*events[:-1], invalid])

    def test_resolved_incident_cannot_receive_more_events(self) -> None:
        first = self.record("occurrence-1")
        transition_security_incident(
            self.events,
            security_incident_id=first["security_incident_id"],
            status="Resolved",
            recorded_by="Owner security review",
            next_action="Retain the protected history.",
            closure=self.closure(),
            now=datetime(2026, 7, 29, 14, 30, tzinfo=UTC),
        )
        with self.assertRaisesRegex(
            SecurityIncidentContractError,
            "immutable",
        ):
            transition_security_incident(
                self.events,
                security_incident_id=first["security_incident_id"],
                status="Monitoring",
                recorded_by="Owner security review",
                next_action="Invalid.",
            )

    def test_secret_shaped_material_is_rejected_without_persistence(self) -> None:
        credential = "password" + "=" + "not-for-a-ledger"
        with self.assertRaisesRegex(
            SecurityIncidentContractError,
            "prohibited secret-shaped material",
        ):
            safe_text(credential, required=True)
        with self.assertRaises(SecurityIncidentContractError):
            self.record(
                "occurrence-1",
                safe_summary=f"Unsafe material {credential}",
            )
        self.assertFalse(self.events.exists())

    def test_evidence_references_are_opaque_and_pathless(self) -> None:
        self.assertEqual(
            opaque_evidence_reference(
                "restricted:security-evidence/evidence-001"
            ),
            "restricted:security-evidence/evidence-001",
        )
        for invalid in (
            "/Users/example/private-report.json",
            "file:/private/report.json",
            "restricted:security-evidence/folder/evidence-001",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(
                    SecurityIncidentContractError,
                    "opaque restricted reference",
                ):
                    opaque_evidence_reference(invalid)
        for secret_shaped in (
            "https://example.test/report?" + "token=value",
            "restricted:security-evidence/"
            + "gh" + "p_" + "1234567890abcdefghijklmnop",
        ):
            with self.subTest(secret_shaped=secret_shaped):
                with self.assertRaisesRegex(
                    SecurityIncidentContractError,
                    "prohibited secret-shaped material",
                ):
                    opaque_evidence_reference(secret_shaped)

    def test_unknown_event_fields_fail_closed(self) -> None:
        event = self.record("occurrence-1")
        event["vulnerability_detail"] = "Not an allowlisted field."
        with self.assertRaisesRegex(
            SecurityIncidentContractError,
            "deny-by-default contract",
        ):
            validate_security_event(event)

    def test_missing_or_malformed_owner_feed_is_unavailable_not_zero(self) -> None:
        missing = project_security_incident_log(self.events)
        self.assertEqual(missing["availability"], "unavailable")
        self.assertIsNone(missing["count"])
        self.assertIsNone(missing["unresolved_count"])
        self.events.write_text("{not-json}\n", encoding="utf-8")
        malformed = project_security_incident_log(self.events)
        self.assertEqual(malformed["availability"], "unavailable")
        self.assertIsNone(malformed["unresolved_count"])

    def test_append_only_ledger_is_owner_only_and_idempotent(self) -> None:
        event = self.record("occurrence-1")
        duplicate = validate_security_event(event)
        from scripts.security_incidents import append_security_event

        returned = append_security_event(self.events, duplicate)
        self.assertEqual(returned["event_sha256"], event["event_sha256"])
        self.assertEqual(len(read_security_events(self.events)), 1)
        self.assertEqual(self.events.stat().st_mode & 0o777, 0o600)

    def test_relationship_projection_is_typed_and_reciprocal(self) -> None:
        security_id = self.record("occurrence-1")["security_incident_id"]
        relation = link_incidents(
            self.relations,
            operational_incident_id="INC-2026-007",
            security_incident_id=security_id,
            relationship_type="security-event-operational-impact",
            recorded_by="Deterministic relation recorder",
            safe_summary="The two authorities describe different effects.",
            known_operational_ids={"INC-2026-007"},
            known_security_ids={security_id},
            now=datetime(2026, 7, 29, 15, 0, tzinfo=UTC),
        )
        projection = relationship_projection(
            read_relation_events(self.relations),
            known_operational_ids={"INC-2026-007"},
            known_security_ids={security_id},
        )
        self.assertEqual(
            projection["by_operational_incident"],
            {"INC-2026-007": [security_id]},
        )
        self.assertEqual(
            projection["by_security_incident"],
            {security_id: ["INC-2026-007"]},
        )
        self.assertNotIn("status", relation)
        self.assertNotIn("closure", relation)

    def test_relation_referential_integrity_fails_closed(self) -> None:
        security_id = self.record("occurrence-1")["security_incident_id"]
        link_incidents(
            self.relations,
            operational_incident_id="INC-2026-007",
            security_incident_id=security_id,
            relationship_type="security-event-operational-impact",
            recorded_by="Deterministic relation recorder",
            safe_summary="The authorities are linked.",
            known_operational_ids={"INC-2026-007"},
            known_security_ids={security_id},
        )
        with self.assertRaisesRegex(
            SecurityIncidentContractError,
            "unknown Operational Incident",
        ):
            relationship_projection(
                read_relation_events(self.relations),
                known_operational_ids=set(),
                known_security_ids={security_id},
            )

    def test_relation_events_cannot_claim_lifecycle_or_closure(self) -> None:
        security_id = self.record("occurrence-1")["security_incident_id"]
        event = link_incidents(
            self.relations,
            operational_incident_id="INC-2026-007",
            security_incident_id=security_id,
            relationship_type="security-event-operational-impact",
            recorded_by="Deterministic relation recorder",
            safe_summary="The authorities are linked.",
            known_operational_ids={"INC-2026-007"},
            known_security_ids={security_id},
        )
        event["status"] = "Resolved"
        with self.assertRaisesRegex(
            SecurityIncidentContractError,
            "deny-by-default contract",
        ):
            validate_relation_event(event)

    def test_unlinking_relation_does_not_change_incident_lifecycle(self) -> None:
        security_id = self.record("occurrence-1")["security_incident_id"]
        linked = link_incidents(
            self.relations,
            operational_incident_id="INC-2026-007",
            security_incident_id=security_id,
            relationship_type="security-event-operational-impact",
            recorded_by="Deterministic relation recorder",
            safe_summary="The authorities are linked.",
            known_operational_ids={"INC-2026-007"},
            known_security_ids={security_id},
        )
        unlink_incidents(
            self.relations,
            relation_id=linked["relation_id"],
            recorded_by="Deterministic relation recorder",
            safe_summary="The typed relationship no longer applies.",
            known_operational_ids={"INC-2026-007"},
            known_security_ids={security_id},
        )
        relation_projection = relationship_projection(
            read_relation_events(self.relations),
            known_operational_ids={"INC-2026-007"},
            known_security_ids={security_id},
        )
        security_projection = security_incident_projection(
            read_security_events(self.events)
        )
        self.assertEqual(relation_projection["active_relations"], [])
        self.assertEqual(
            security_projection["items"][0]["status"],
            "Open",
        )

    def test_fixture_projection_cli_has_no_production_fallback(self) -> None:
        with mock.patch.object(
            sys,
            "argv",
            ["security_incidents.py", "project-fixture"],
        ):
            with self.assertRaisesRegex(PathAuthorityError, "fixture-only"):
                main()

        fixture_root = self.root / "fixture"
        repository_root = fixture_root / "repo"
        state_root = fixture_root / "state"
        repository_root.mkdir(parents=True)
        (state_root / "records" / "automation").mkdir(parents=True)
        fixture_events = (
            state_root / "records" / "automation" / "security-incidents.jsonl"
        )
        fixture_events.write_text(
            self.events.read_text(encoding="utf-8")
            if self.events.exists()
            else "",
            encoding="utf-8",
        )
        authority = ProjectPathAuthority.fixture(
            fixture_root,
            repository_root=repository_root,
            state_root=state_root,
        )
        output = io.StringIO()
        with mock.patch.object(
            sys,
            "argv",
            ["security_incidents.py", "project-fixture"],
        ):
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(path_authority=authority), 0)
        projected = json.loads(output.getvalue())
        self.assertTrue(projected["complete"])
        self.assertEqual(projected["count"], 0)


if __name__ == "__main__":
    unittest.main()
