import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "arrp_nightly_runtime", ROOT / "scripts" / "arrp_nightly.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def run(*args: str, cwd: Path) -> str:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


class ArrpRuntimeBoundaryTests(unittest.TestCase):
    def test_materializes_exact_reviewed_blob_with_owner_only_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            run("git", "init", "-b", "main", str(repo), cwd=root)
            run("git", "config", "user.name", "Fixture", cwd=repo)
            run("git", "config", "user.email", "fixture@example.invalid", cwd=repo)
            script = repo / "scripts/tool.py"
            script.parent.mkdir()
            script.write_text("print('reviewed')\n", encoding="utf-8")
            os.chmod(script, 0o755)
            run("git", "add", "scripts/tool.py", cwd=repo)
            run("git", "commit", "-m", "runtime", cwd=repo)
            commit = run("git", "rev-parse", "HEAD", cwd=repo)
            destination = root / "state/runtime" / commit
            hashes = MODULE.materialize_reviewed_runtime(
                repo, commit, destination, ("scripts/tool.py",)
            )
            exported = destination / "scripts/tool.py"
            self.assertEqual(exported.read_bytes(), script.read_bytes())
            self.assertEqual(exported.stat().st_mode & 0o777, 0o700)
            manifest = json.loads(
                (destination / "runtime-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["files"], hashes)
            self.assertEqual(manifest["source_commit"], commit)

    def test_rejects_symlink_runtime_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            run("git", "init", "-b", "main", str(repo), cwd=root)
            run("git", "config", "user.name", "Fixture", cwd=repo)
            run("git", "config", "user.email", "fixture@example.invalid", cwd=repo)
            scripts = repo / "scripts"
            scripts.mkdir()
            (scripts / "target.py").write_text("safe\n", encoding="utf-8")
            (scripts / "link.py").symlink_to("target.py")
            run("git", "add", "scripts/target.py", "scripts/link.py", cwd=repo)
            run("git", "commit", "-m", "symlink", cwd=repo)
            commit = run("git", "rev-parse", "HEAD", cwd=repo)
            with self.assertRaisesRegex(MODULE.TransactionError, "unsafe reviewed runtime"):
                MODULE.materialize_reviewed_runtime(
                    repo, commit, root / "runtime", ("scripts/link.py",)
                )


if __name__ == "__main__":
    unittest.main()
