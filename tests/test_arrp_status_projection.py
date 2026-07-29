import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "arrp_nightly_status", ROOT / "scripts" / "arrp_nightly.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ArrpStatusProjectionTests(unittest.TestCase):
    def test_status_has_complete_schema_and_owner_only_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = MODULE.RunnerConfig(
                root / "repo", root / "state", fixture_root=root
            )
            status = MODULE._base_status(config, "status-test")
            self.assertEqual(status["control_state"], "run")
            MODULE.write_status(config, status, status="paused", stage="01_preflight")
            path = config.state_root / "status.json"
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(set(saved), set(MODULE.STATUS_FIELDS))
            self.assertEqual(saved["status"], "paused")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(config.state_root.stat().st_mode & 0o777, 0o700)
            self.assertFalse(
                (config.canonical_path / "research/horizon-review-console/data/local-automation-status.js").exists()
            )

    def test_status_reads_only_the_authoritative_owner_only_pause_control(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = MODULE.RunnerConfig(
                root / "repo", root / "state", fixture_root=root
            )
            config.state_root.mkdir(mode=0o700)
            pause_path = config.state_root / "PAUSED"
            pause_path.write_text("paused\n", encoding="utf-8")
            pause_path.chmod(0o600)

            status = MODULE._base_status(config, "paused-status-test")

            self.assertEqual(status["control_state"], "paused")

    def test_optional_projection_is_valid_javascript_assignment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            status = root / "status.json"
            status.write_text('{"status":"completed","run_id":"fixture"}\n', encoding="utf-8")
            output = MODULE.write_console_status_projection(
                status, root / "projection/local-automation-status.js"
            )
            text = output.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("window.ARRP_LOCAL_AUTOMATION_STATUS = "))
            payload = text.removeprefix(
                "window.ARRP_LOCAL_AUTOMATION_STATUS = "
            ).removesuffix(";\n")
            parsed = json.loads(payload)
            self.assertEqual(parsed["status"], "completed")
            self.assertEqual(parsed["control_state"], "run")
            self.assertRegex(
                parsed["control_state_checked_at"],
                r"^\d{4}-\d{2}-\d{2}T",
            )
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_projection_refreshes_current_pause_without_rewriting_occurrence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            status = root / "status.json"
            status.write_text(
                '{"status":"failed","control_state":"run","run_id":"fixture"}\n',
                encoding="utf-8",
            )
            pause = root / "PAUSED"
            pause.write_text("paused\n", encoding="utf-8")
            pause.chmod(0o600)

            output = MODULE.write_console_status_projection(
                status, root / "projection/local-automation-status.js"
            )
            payload = json.loads(
                output.read_text(encoding="utf-8")
                .removeprefix("window.ARRP_LOCAL_AUTOMATION_STATUS = ")
                .removesuffix(";\n")
            )

            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["control_state"], "paused")
            self.assertEqual(
                json.loads(status.read_text(encoding="utf-8"))["control_state"],
                "run",
            )

    def test_atomic_rewrite_never_changes_file_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state/status.json"
            MODULE.atomic_write_json(path, {"version": 1})
            MODULE.atomic_write_json(path, {"version": 2})
            self.assertEqual(json.loads(path.read_text())["version"], 2)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(os.stat(path.parent).st_mode & 0o777, 0o700)


if __name__ == "__main__":
    unittest.main()
