import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_coordinator_control", ROOT / "scripts" / "run_coordinator_control.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class RunCoordinatorControlTests(unittest.TestCase):
    def state(self):
        return {"schema_version": 1, "overrides": {}, "requests": []}

    def test_reprioritize_and_clear_only_user_override(self):
        state = self.state()
        MODULE.apply_control(
            state,
            {
                "action": "reprioritize",
                "work_unit_id": "HOR-035:lead-1",
                "priority": "high",
                "reason": "Review first.",
            },
        )
        self.assertEqual(state["overrides"]["HOR-035:lead-1"]["priority"], "high")
        MODULE.apply_control(
            state,
            {"action": "clear_override", "work_unit_id": "HOR-035:lead-1"},
        )
        self.assertNotIn("HOR-035:lead-1", state["overrides"])

    def test_clear_refuses_non_user_override(self):
        state = self.state()
        state["overrides"]["APPT-001"] = {"source": "automation"}
        with self.assertRaisesRegex(ValueError, "no user-created"):
            MODULE.apply_control(
                state,
                {"action": "clear_override", "work_unit_id": "APPT-001"},
            )

    def test_invalid_ids_and_actions_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "valid work_unit_id"):
            MODULE.apply_control(
                self.state(),
                {"action": "suppress", "work_unit_id": "../../outside"},
            )
        with self.assertRaisesRegex(ValueError, "unsupported"):
            MODULE.apply_control(self.state(), {"action": "delete_everything"})

    def test_action_item_resolution_is_explicit_and_append_only(self):
        state = self.state()
        state["action_items"] = [
            {
                "id": "automation-failure-abc123",
                "resolved": False,
                "summary": "Run failed.",
            }
        ]
        record = MODULE.apply_control(
            state,
            {
                "action": "resolve_action_item",
                "action_item_id": "automation-failure-abc123",
                "reason": "Reviewed after the corrected chain completed.",
            },
        )
        item = state["action_items"][0]
        self.assertTrue(item["resolved"])
        self.assertEqual(item["resolved_by"], "human-local-console")
        self.assertEqual(
            record["action_item_id"],
            "automation-failure-abc123",
        )
        self.assertEqual(
            state["action_item_history"][0]["event"],
            "resolved",
        )
        with self.assertRaisesRegex(ValueError, "already resolved"):
            MODULE.apply_control(
                state,
                {
                    "action": "resolve_action_item",
                    "action_item_id": "automation-failure-abc123",
                    "reason": "Resolve twice.",
                },
            )

    def test_action_item_resolution_requires_reason_and_known_id(self):
        state = self.state()
        state["action_items"] = []
        with self.assertRaisesRegex(ValueError, "resolution reason"):
            MODULE.apply_control(
                state,
                {
                    "action": "resolve_action_item",
                    "action_item_id": "automation-failure-abc123",
                },
            )

    def test_locked_transaction_reads_latest_state_before_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "control.json"
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "overrides": {
                            "unit-one": {
                                "source": "user-local-console",
                                "priority": "high",
                            }
                        },
                        "requests": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            _record, state = MODULE.apply_control_transaction(
                state_path,
                {"action": "request_run"},
                root=root,
            )
            self.assertIn("unit-one", state["overrides"])
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertIn("unit-one", persisted["overrides"])
            self.assertTrue((root / "control.lock").is_file())
        with self.assertRaisesRegex(ValueError, "no coordinator action item"):
            MODULE.apply_control(
                state,
                {
                    "action": "resolve_action_item",
                    "action_item_id": "automation-failure-abc123",
                    "reason": "Reviewed.",
                },
            )

    def test_control_token_is_persistent_and_private(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "control.token"
            root = Path(directory)
            token = MODULE.load_or_create_token(path, root)
            self.assertEqual(MODULE.load_or_create_token(path, root), token)
            self.assertGreaterEqual(len(token), 32)
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
