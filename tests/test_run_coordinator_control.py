import importlib.util
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
