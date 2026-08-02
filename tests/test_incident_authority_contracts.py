from __future__ import annotations

import json
import hashlib
import unittest
from pathlib import Path

from scripts import component_registry


ROOT = Path(__file__).resolve().parents[1]


class IncidentAuthorityContractTest(unittest.TestCase):
    def setUp(self) -> None:
        automation = ROOT / "framework" / "project" / "automation"
        self.operational = json.loads(
            (automation / "operational-incidents.json").read_text(encoding="utf-8")
        )
        self.security = json.loads(
            (automation / "security-incidents.json").read_text(encoding="utf-8")
        )
        self.relations = json.loads(
            (automation / "incident-relations.json").read_text(encoding="utf-8")
        )
        self.classifications = json.loads(
            (
                ROOT
                / "framework"
                / "project"
                / "interfaces"
                / "project-console"
                / "configuration"
                / "classifications.json"
            ).read_text(encoding="utf-8")
        )
        registry = json.loads(
            (ROOT / "framework" / "component-registry.json").read_text(
                encoding="utf-8"
            )
        )
        self.context_routes = component_registry._routing_snapshot(registry)

    def test_inc_and_sec_have_distinct_owner_local_authorities(self) -> None:
        self.assertIn("operational-incidents.jsonl", self.operational["event_authority"])
        self.assertIn("security-incidents.jsonl", self.security["event_authority"])
        self.assertNotEqual(
            self.operational["event_authority"], self.security["event_authority"]
        )
        self.assertEqual(self.operational["incident_id_pattern"], "INC-YYYY-NNN")
        self.assertTrue(self.operational["live_activation"])
        self.assertEqual(self.security["incident_id_pattern"], "SEC-YYYY-NNN")
        self.assertFalse(self.security["live_activation"])
        self.assertIn("after verified resolution", self.operational["recurrence"])
        self.assertIn("exact recovery proof", self.operational["closure"])

    def test_relation_is_not_a_third_lifecycle_or_count_authority(self) -> None:
        boundary = self.relations["authority_boundary"].lower()
        index = self.relations["cross_domain_index"].lower()
        self.assertIn("owns no incident identity", boundary)
        self.assertIn("separate per-domain counts", index)
        self.assertIn("not a third incident ledger", index)
        self.assertIn("does not alter either incident lifecycle", self.operational["security_relation_boundary"])

    def test_incident_work_and_queue_ids_stay_separate(self) -> None:
        namespaces = self.classifications["namespaces"]
        work = {record["id"]: record for record in namespaces["work_kind"]}
        queues = {record["id"]: record for record in namespaces["queue_id"]}
        self.assertEqual(work["operational_incident"]["destination"], "automation:logs:incidents")
        self.assertEqual(work["security_incident"]["destination"], "automation:logs:security-incidents")
        self.assertEqual(queues["operational_incidents"]["destination"], "automation:logs:incidents")
        self.assertEqual(queues["security_incidents"]["destination"], "automation:logs:security-incidents")
        self.assertIn("unavailable outside", queues["operational_incidents"]["meaning"])
        self.assertIn("unavailable outside", queues["security_incidents"]["meaning"])

    def test_interface_contract_preserves_inactive_runtime_staging(self) -> None:
        interface = (
            ROOT / "framework/project/interfaces/project-console/specification.md"
        ).read_text(encoding="utf-8")
        self.assertIn("current production runtime remains at", interface)
        self.assertIn(
            "protected staging\ndescriptor remains inactive until separately approved host",
            interface,
        )
        self.assertIn(
            "Repository-source direct-disk, loopback, and hosted/public",
            interface,
        )
        self.assertIn("`live_activation: false`", interface)

    def test_incident_policies_are_pinned_governing_context(self) -> None:
        documents = self.context_routes["documents"]
        expected = {
            "operational_incident_policy": "operational-incidents.json",
            "security_incident_policy": "security-incidents.json",
            "incident_relation_policy": "incident-relations.json",
        }
        for document_id, filename in expected.items():
            document = documents[document_id]
            path = ROOT / document["path"]
            self.assertEqual(path.name, filename)
            self.assertTrue(document["governing"])
            self.assertEqual(document["hash_policy"], "pinned")
            self.assertEqual(
                document["sha256"],
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        self.assertEqual(
            documents["incident_relation_policy"]["requires"],
            ["operational_incident_policy", "security_incident_policy"],
        )

    def test_loopback_is_public_shell_only(self) -> None:
        interface = (
            ROOT / "framework/project/interfaces/project-console/specification.md"
        ).read_text(encoding="utf-8")
        self.assertIn("public-shell and fixture", interface)
        self.assertIn("must not request or load ignored private projections", interface)


if __name__ == "__main__":
    unittest.main()
