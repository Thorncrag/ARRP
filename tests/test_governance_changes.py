from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import governance_changes as changes


ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "framework/records/governance/governance-change-log.md"
REGISTRY = ROOT / "framework/project/workflows/governance-change-registry.json"


class GovernanceChangeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.log = self.root / "log.md"
        self.registry = self.root / "registry.json"
        self.log.write_text(LOG.read_text(encoding="utf-8"), encoding="utf-8")
        self.registry.write_text(REGISTRY.read_text(encoding="utf-8"), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def public(self) -> dict[str, changes.GovernanceChange]:
        return changes.parse_public_changes(self.log, self.registry)

    def event(self, identifier: str, event_id: str) -> dict[str, object]:
        entry = self.public()[identifier]
        return {
            "schema_version": 1,
            "event_id": event_id,
            "event_class": "governance_change_supplement",
            "governance_id": identifier,
            "public_entry_sha256": entry.entry_sha256,
            "recorded_at": "2026-07-29T12:00:00Z",
            "provenance": "owner-local:governance-review:fixture",
            "decision_context": "Protected decision context is retained locally.",
            "protected_references": ["private:fixture:decision-evidence"],
            "validation_references": ["private:fixture:validation"],
            "disclosure_review": "owner_local_only",
            "safe_summary": "Owner-local supporting evidence is retained.",
        }

    def test_public_log_is_registry_bound_and_digest_stable(self) -> None:
        public = self.public()
        self.assertTrue(public)
        first = public[sorted(public)[0]]
        self.assertEqual(first.record_class, "governance_change")
        self.assertRegex(first.entry_sha256, r"^sha256:[0-9a-f]{64}$")

    def test_proposed_not_adopted_is_merged_but_not_active(self) -> None:
        public = self.public()
        proposal = public["GOV-2026-014"]
        registry = json.loads(self.registry.read_text(encoding="utf-8"))
        registered = next(
            entry
            for entry in registry["entries"]
            if entry["id"] == proposal.id
        )
        self.assertEqual(proposal.status, "Proposed / not adopted")
        self.assertEqual(registered["source"]["kind"], "git_merge")
        self.assertEqual(
            registered["policy_adoption"],
            "Not adopted; exact owner approval of the replacement text remains required.",
        )
        self.assertEqual(
            registered["live_activation"],
            "No directive or runtime change is activated.",
        )

        registered["source"] = {
            "kind": "current_worktree",
            "commits": [],
            "pull_requests": [],
        }
        self.registry.write_text(json.dumps(registry), encoding="utf-8")
        with self.assertRaisesRegex(
            changes.GovernanceChangeError,
            "status disagrees with source evidence",
        ):
            self.public()

    def test_public_unknown_duplicate_and_registry_mismatch_fail_closed(self) -> None:
        self.log.write_text(
            self.log.read_text(encoding="utf-8").replace(
                "- Validation:", "- Restricted evidence: no\n- Validation:", 1
            ),
            encoding="utf-8",
        )
        with self.assertRaises(changes.GovernanceChangeError):
            self.public()
        self.log.write_text(LOG.read_text(encoding="utf-8"), encoding="utf-8")
        payload = json.loads(self.registry.read_text(encoding="utf-8"))
        payload["entries"].append(dict(payload["entries"][0]))
        self.registry.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(changes.GovernanceChangeError):
            self.public()

    def test_private_supplements_require_exact_digest_identity_and_allowlist(self) -> None:
        public = self.public()
        path = self.root / "supplements.jsonl"
        identifier = sorted(public)[0]
        event = self.event(identifier, "GOVSUP-2026-001")
        path.write_text(json.dumps(event) + "\n", encoding="utf-8")
        self.assertEqual(changes.parse_private_supplements(path, public), [event])
        event["private_policy"] = "forbidden"
        path.write_text(json.dumps(event) + "\n", encoding="utf-8")
        with self.assertRaises(changes.GovernanceChangeError):
            changes.parse_private_supplements(path, public)
        event.pop("private_policy")
        event["public_entry_sha256"] = "sha256:" + "0" * 64
        path.write_text(json.dumps(event) + "\n", encoding="utf-8")
        with self.assertRaises(changes.GovernanceChangeError):
            changes.parse_private_supplements(path, public)
        event["public_entry_sha256"] = public[identifier].entry_sha256
        event.pop("provenance")
        path.write_text(json.dumps(event) + "\n", encoding="utf-8")
        with self.assertRaises(changes.GovernanceChangeError):
            changes.parse_private_supplements(path, public)
        event["provenance"] = "owner-local:governance-review:fixture"
        path.write_text(
            json.dumps(event) + "\n" + json.dumps(event) + "\n",
            encoding="utf-8",
        )
        with self.assertRaises(changes.GovernanceChangeError):
            changes.parse_private_supplements(path, public)

    def test_private_supplement_identity_and_protected_fields_fail_closed(self) -> None:
        public = self.public()
        identifier = sorted(public)[0]
        event = self.event(identifier, "GOVSUP-2026-999")
        path = self.root / "supplements.jsonl"
        path.write_text(json.dumps(event) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(
            changes.GovernanceChangeError,
            "identity does not match",
        ):
            changes.parse_private_supplements(path, public)

        event = self.event(identifier, "GOVSUP-2026-001")
        event["protected_references"] = []
        path.write_text(json.dumps(event) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(
            changes.GovernanceChangeError,
            "protected references",
        ):
            changes.parse_private_supplements(path, public)

    def test_supplement_projection_is_unavailable_not_zero_when_required_evidence_missing(self) -> None:
        public = self.public()
        projection = changes.project_private_supplements(self.root / "absent.jsonl", public)
        self.assertEqual(projection["availability"], "unavailable")
        self.assertFalse(projection["complete"])
        self.assertEqual(projection["items"], [])
        path = self.root / "complete.jsonl"
        events = [
            self.event(identifier, f"GOVSUP-2026-{number:03d}")
            for number, identifier in enumerate(sorted(public), start=1)
            if public[identifier].private_supplement_required
        ]
        path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        projection = changes.project_private_supplements(path, public)
        self.assertEqual(projection["availability"], "current")
        self.assertTrue(projection["complete"])


if __name__ == "__main__":
    unittest.main()
