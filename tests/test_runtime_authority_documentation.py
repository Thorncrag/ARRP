from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from scripts import component_registry


ROOT = Path(__file__).resolve().parents[1]


class RuntimeAuthorityDocumentationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime_path = (
            ROOT
            / "framework"
            / "project"
            / "automation"
            / "owner-local-runtime.md"
        )
        self.runtime = self.runtime_path.read_text(encoding="utf-8")
        self.registry = json.loads(
            (ROOT / "framework" / "component-registry.json").read_text(
                encoding="utf-8"
            )
        )
        self.routes = component_registry._routing_snapshot(self.registry)

    def test_runtime_authority_is_governing_pinned_and_routed(self) -> None:
        document = self.routes["documents"]["project_runtime_authority"]
        self.assertEqual(
            document["path"],
            "framework/project/automation/owner-local-runtime.md",
        )
        self.assertTrue(document["governing"])
        self.assertEqual(document["hash_policy"], "pinned")
        self.assertEqual(
            document["sha256"],
            hashlib.sha256(self.runtime_path.read_bytes()).hexdigest(),
        )
        for capability in ("autonomous_execution", "bot_governance"):
            self.assertIn(
                "project_runtime_authority",
                self.routes["capabilities"][capability],
            )
        self.assertIn(
            "project_runtime_authority",
            self.routes["documents"]["project_autonomous_execution"][
                "requires"
            ],
        )
        self.assertIn(
            "project_runtime_authority",
            self.routes["documents"]["runbook_run_coordinator_bot"]["requires"],
        )
        self.assertIn(
            "project_runtime_authority",
            self.routes["documents"]["project_tool_interface"]["requires"],
        )

    def test_runtime_authority_distinguishes_active_and_staged_state(self) -> None:
        self.assertIn(
            "Application Support state root is the current production",
            self.runtime,
        )
        self.assertIn(
            "`ARRP Private` workspace is the sole owner-local companion",
            self.runtime,
        )
        self.assertIn("inactive protected successor staging authority", self.runtime)
        self.assertIn("activation_authorized: false", self.runtime)
        self.assertIn("No symlink alias", self.runtime)
        self.assertIn("one runtime authority and one scheduler", self.runtime)

    def test_runtime_artifact_classes_cover_the_complete_state_boundary(self) -> None:
        for phrase in (
            "Binary automation control and serialization",
            "Reviewed runtime snapshots",
            "Transaction work and output",
            "Current status and cadence",
            "Failure-safe spool",
            "Durable operational records",
            "Security records and controls",
            "Owner Console versions",
            "Caches and other generated runtime state",
            "Migration evidence",
        ):
            self.assertIn(phrase, self.runtime)

    def test_current_documents_do_not_reintroduce_retired_or_ambiguous_state(self) -> None:
        workflow = (
            ROOT / "framework" / "project" / "github" / "workflow.md"
        ).read_text(encoding="utf-8")
        agent_policy = (
            ROOT / "framework" / "project" / "automation" / "agent-policy.md"
        ).read_text(encoding="utf-8")
        framework = (ROOT / "framework" / "FRAMEWORK.md").read_text(
            encoding="utf-8"
        )

        if self.registry.get("schema_version") == 3:
            self.assertEqual(
                self.registry["validation"]["mode"],
                "adopted_configuration_validation",
            )
            self.assertFalse(self.registry["validation"]["live_authority"])
        elif self.registry.get("schema_version") == 2:
            self.assertEqual(
                self.registry["validation"]["mode"],
                "proposed_revision_validation",
            )
            self.assertFalse(self.registry["validation"]["live_authority"])
        elif self.registry["status"] == "candidate":
            self.assertFalse(
                self.registry["context_routing"]["authoritative"]
            )
            self.assertEqual(
                self.registry["context_routing"]["activation_state"],
                "candidate_import",
            )
        else:
            self.assertEqual(self.registry["status"], "active")
            self.assertTrue(
                self.registry["context_routing"]["authoritative"]
            )
        self.assertNotIn("ARRP's disabled local-first runner", workflow)
        self.assertNotIn(
            "bounded GitHub Actions or Console history",
            agent_policy,
        )
        self.assertIn(
            "Component Registry",
            framework,
        )

    def test_console_documentation_matches_owner_only_incident_and_binding_contract(
        self,
    ) -> None:
        contract = (
            ROOT
            / "framework"
            / "project"
            / "interfaces"
            / "project-console"
            / "specification.md"
        ).read_text(encoding="utf-8")
        readme = (
            ROOT
            / "framework"
            / "project"
            / "interfaces"
            / "project-console"
            / "README.md"
        ).read_text(encoding="utf-8")
        classification_path = (
            ROOT
            / "framework"
            / "project"
            / "interfaces"
            / "project-console"
            / "configuration"
            / "classifications.json"
        )
        classifications = json.loads(
            classification_path.read_text(encoding="utf-8")
        )

        self.assertIn(
            "modes render both owner-local incident ledgers as unavailable",
            contract,
        )
        public_shell_message = (
            "Data unavailable outside the bound owner-local Console."
        )
        self.assertIn(public_shell_message, contract)
        self.assertIn(public_shell_message, readme)
        self.assertIn(public_shell_message, self.runtime)
        self.assertIn(
            "The checked-in public bundle\ncontains no incident events",
            contract,
        )
        self.assertIn("each copied private projection's SHA-256 digest", readme)
        queues = {
            row["id"]: row
            for row in classifications["namespaces"]["queue_id"]
        }
        for queue_id in ("operational_incidents", "security_incidents"):
            self.assertIn("unavailable outside", queues[queue_id]["meaning"])
        project_console = self.registry["components"]["entries"]["project_console"]
        self.assertIn(
            "framework/project/interfaces/project-console/configuration/classifications.json",
            {
                artifact["path"]
                for artifact in project_console["supporting_artifacts"]
            },
        )
        self.assertIn("component_classes", self.registry["implementation_enums"])
        self.assertIn("component_types", self.registry["implementation_enums"])


if __name__ == "__main__":
    unittest.main()
