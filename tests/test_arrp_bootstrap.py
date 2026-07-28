import importlib.util
import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
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
    def test_scheduled_command_uses_reviewed_runtime(self):
        runtime = Path("/tmp/reviewed-runtime")
        revision = "a" * 40
        command = MODULE.build_command(runtime, revision)
        self.assertEqual(
            command[1:],
            [
                "-B",
                "/tmp/reviewed-runtime/scripts/arrp_nightly.py",
                "--canonical-path",
                str(MODULE.CANONICAL_PATH),
                "--state-root",
                str(MODULE.STATE_ROOT),
                "--runtime-commit",
                revision,
                "--scheduled",
            ],
        )

    def test_manual_command_is_forwarded_exactly(self):
        runtime = Path("/tmp/reviewed-runtime")
        revision = "b" * 40
        command = MODULE.build_command(runtime, revision, manual=True)
        self.assertEqual(command[-1], "--manual")
        self.assertNotIn("--scheduled", command)
        self.assertEqual(command[1], "-B")

    def test_reviewed_runner_does_not_create_bytecode_cache(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            scripts = runtime / "scripts"
            scripts.mkdir()
            (scripts / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
            (scripts / "arrp_nightly.py").write_text(
                "import helper\nassert helper.VALUE == 1\n",
                encoding="utf-8",
            )
            subprocess.run(
                MODULE.build_command(runtime, "e" * 40),
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertFalse(any(runtime.rglob("__pycache__")))
            self.assertFalse(any(runtime.rglob("*.pyc")))

    def test_dry_run_reports_without_invoking_runner(self):
        runtime = Path("/tmp/reviewed-runtime")
        revision = "c" * 40
        output = io.StringIO()
        with (
            mock.patch.object(
                MODULE,
                "reviewed_runtime",
                return_value=(runtime, revision),
            ),
            mock.patch.object(MODULE.subprocess, "run") as run,
            redirect_stdout(output),
        ):
            self.assertEqual(MODULE.main(["--dry-run"]), 0)
            run.assert_not_called()
        self.assertIn(revision, output.getvalue())
        self.assertIn(
            str(runtime / "scripts/arrp_nightly.py"),
            output.getvalue(),
        )

    def test_manual_main_invokes_reviewed_runtime_runner(self):
        runtime = Path("/tmp/reviewed-runtime")
        revision = "d" * 40
        with (
            mock.patch.object(
                MODULE,
                "reviewed_runtime",
                return_value=(runtime, revision),
            ),
            mock.patch.object(
                MODULE.subprocess,
                "run",
                return_value=mock.Mock(returncode=0),
            ) as run,
        ):
            self.assertEqual(MODULE.main(["--manual"]), 0)
            run.assert_called_once_with(
                MODULE.build_command(runtime, revision, manual=True),
                check=False,
            )


if __name__ == "__main__":
    unittest.main()
