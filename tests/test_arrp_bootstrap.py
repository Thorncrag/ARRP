import argparse
import importlib.util
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "arrp_bootstrap", ROOT / "scripts" / "arrp_bootstrap.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ArrpBootstrapTests(unittest.TestCase):
    def test_disabled_without_fixture_or_explicit_manual_dry_run(self):
        with mock.patch.object(MODULE.subprocess, "run") as run:
            self.assertEqual(MODULE.main([]), 64)
            run.assert_not_called()

    def test_fixture_arguments_are_forwarded_exactly(self):
        arguments = argparse.Namespace(
            fixture=Path("/tmp/fixture"),
            canonical_path=Path("/tmp/fixture/repo"),
            state_root=Path("/tmp/fixture/state"),
            manual=False,
            dry_run=False,
            run_id="fixture-run",
        )
        command = MODULE.build_command(arguments)
        self.assertEqual(command[1], str(MODULE.runner_path()))
        self.assertEqual(
            command[2:],
            [
                "--fixture",
                "/tmp/fixture",
                "--canonical-path",
                "/tmp/fixture/repo",
                "--state-root",
                "/tmp/fixture/state",
                "--run-id",
                "fixture-run",
            ],
        )

    def test_manual_requires_dry_run_during_p1(self):
        with mock.patch.object(
            MODULE.subprocess, "run", return_value=mock.Mock(returncode=0)
        ) as run:
            self.assertEqual(MODULE.main(["--manual"]), 64)
            run.assert_not_called()
            self.assertEqual(MODULE.main(["--manual", "--dry-run"]), 0)
            run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
