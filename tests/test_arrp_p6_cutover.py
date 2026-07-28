import hashlib
import importlib.util
import json
import os
import plistlib
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PLIST_PATH = (
    ROOT / ".github/launchd/com.thorncrag.arrp-nightly.plist.example"
)
STATE_ROOT = Path("/Users/benjaminsmith/Library/Application Support/ARRP")
BOOTSTRAP_SPEC = importlib.util.spec_from_file_location(
    "arrp_p6_bootstrap",
    ROOT / "scripts/arrp_bootstrap.py",
)
BOOTSTRAP = importlib.util.module_from_spec(BOOTSTRAP_SPEC)
assert BOOTSTRAP_SPEC.loader is not None
BOOTSTRAP_SPEC.loader.exec_module(BOOTSTRAP)


def git(*arguments: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


class ArrpP6LaunchAgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with PLIST_PATH.open("rb") as handle:
            cls.plist = plistlib.load(handle)

    def test_exact_identity_and_installed_bootstrap(self):
        self.assertEqual(
            self.plist["Label"],
            "com.thorncrag.arrp-nightly",
        )
        self.assertEqual(
            self.plist["ProgramArguments"],
            [str(STATE_ROOT / "bin/arrp-bootstrap.py")],
        )

    def test_enabled_run_at_load_and_exact_local_schedule(self):
        self.assertFalse(self.plist["Disabled"])
        self.assertTrue(self.plist["RunAtLoad"])
        self.assertEqual(
            self.plist["StartCalendarInterval"],
            {"Hour": 2, "Minute": 0},
        )

    def test_launchd_path_exposes_reviewed_local_toolchain(self):
        self.assertEqual(
            self.plist["EnvironmentVariables"]["PATH"],
            "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        )

    def test_launchd_logs_stay_inside_owner_only_state_root(self):
        self.assertEqual(
            self.plist["StandardOutPath"],
            str(STATE_ROOT / "logs/launchd.out.log"),
        )
        self.assertEqual(
            self.plist["StandardErrorPath"],
            str(STATE_ROOT / "logs/launchd.err.log"),
        )


class ArrpP6ProductionBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.origin = self.root / "origin.git"
        self.repository = self.root / "canonical"
        self.state_root = self.root / "state"
        git("init", "--bare", str(self.origin), cwd=self.root)
        git("init", "-b", "main", str(self.repository), cwd=self.root)
        git("config", "user.name", "ARRP P6 Fixture", cwd=self.repository)
        git(
            "config",
            "user.email",
            "arrp-p6@example.invalid",
            cwd=self.repository,
        )
        for relative in BOOTSTRAP.RUNTIME_FILES:
            target = self.repository / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                f"# reviewed fixture for {relative}\n",
                encoding="utf-8",
            )
        git("add", "--", *BOOTSTRAP.RUNTIME_FILES, cwd=self.repository)
        git("commit", "-m", "Reviewed P6 runtime fixture", cwd=self.repository)
        git("remote", "add", "origin", str(self.origin), cwd=self.repository)
        git("push", "-u", "origin", "main", cwd=self.repository)
        self.revision = git("rev-parse", "HEAD", cwd=self.repository)

    def tearDown(self):
        self.temporary.cleanup()

    def production_boundary(self):
        return (
            mock.patch.object(
                BOOTSTRAP,
                "CANONICAL_PATH",
                self.repository,
            ),
            mock.patch.object(
                BOOTSTRAP,
                "STATE_ROOT",
                self.state_root,
            ),
            mock.patch.object(
                BOOTSTRAP,
                "APPROVED_ORIGINS",
                {str(self.origin)},
            ),
        )

    def test_reviewed_runtime_fetches_origin_main_and_materializes_exact_files(self):
        canonical_patch, state_patch, origins_patch = self.production_boundary()
        with canonical_patch, state_patch, origins_patch:
            runtime, revision = BOOTSTRAP.reviewed_runtime(
                self.repository,
                self.state_root,
            )

        self.assertEqual(revision, self.revision)
        self.assertEqual(
            runtime,
            (self.state_root / "runtime" / self.revision).resolve(),
        )
        manifest_path = runtime / "runtime-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_commit"], self.revision)
        self.assertEqual(set(manifest["files"]), set(BOOTSTRAP.RUNTIME_FILES))
        self.assertEqual(stat.S_IMODE(manifest_path.stat().st_mode), 0o600)

        for directory, _, filenames in os.walk(self.state_root):
            self.assertEqual(
                stat.S_IMODE(Path(directory).stat().st_mode),
                0o700,
            )
            for filename in filenames:
                path = Path(directory) / filename
                self.assertFalse(path.is_symlink())
                self.assertEqual(stat.S_IMODE(path.stat().st_mode) & 0o077, 0)

        for relative in BOOTSTRAP.RUNTIME_FILES:
            reviewed = subprocess.run(
                ["git", "show", f"{self.revision}:{relative}"],
                cwd=self.repository,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout
            exported = runtime / relative
            self.assertEqual(exported.read_bytes(), reviewed)
            self.assertEqual(
                manifest["files"][relative],
                hashlib.sha256(exported.read_bytes()).hexdigest(),
            )

    def test_no_argument_bootstrap_invokes_exact_scheduled_snapshot_command(self):
        runtime = self.state_root / "runtime" / self.revision
        expected = BOOTSTRAP.build_command(
            runtime,
            self.revision,
            repository=BOOTSTRAP.CANONICAL_PATH,
            state_root=BOOTSTRAP.STATE_ROOT,
        )
        with (
            mock.patch.object(
                BOOTSTRAP,
                "reviewed_runtime",
                return_value=(runtime, self.revision),
            ) as reviewed,
            mock.patch.object(
                BOOTSTRAP.subprocess,
                "run",
                return_value=mock.Mock(returncode=0),
            ) as run,
        ):
            self.assertEqual(BOOTSTRAP.main([]), 0)

        reviewed.assert_called_once_with()
        run.assert_called_once_with(expected, check=False)
        self.assertEqual(
            expected[1:],
            [
                str(runtime / "scripts/arrp_nightly.py"),
                "--canonical-path",
                str(BOOTSTRAP.CANONICAL_PATH),
                "--state-root",
                str(BOOTSTRAP.STATE_ROOT),
                "--runtime-commit",
                self.revision,
                "--scheduled",
            ],
        )

    def test_dirty_protected_runtime_is_preserved_but_origin_runtime_is_materialized(self):
        dirty = self.repository / BOOTSTRAP.RUNTIME_FILES[0]
        dirty.write_text("unreviewed local runtime\n", encoding="utf-8")
        canonical_patch, state_patch, origins_patch = self.production_boundary()
        with canonical_patch, state_patch, origins_patch:
            runtime, revision = BOOTSTRAP.reviewed_runtime(
                self.repository,
                self.state_root,
            )
        self.assertEqual(revision, self.revision)
        self.assertEqual(dirty.read_text(encoding="utf-8"), "unreviewed local runtime\n")
        self.assertNotEqual(
            (runtime / BOOTSTRAP.RUNTIME_FILES[0]).read_text(encoding="utf-8"),
            dirty.read_text(encoding="utf-8"),
        )

    def test_symlink_runtime_tree_entry_is_rejected(self):
        relative = BOOTSTRAP.RUNTIME_FILES[0]
        target = self.repository / relative
        target.unlink()
        target.symlink_to("untrusted-target.py")
        git("add", "--", relative, cwd=self.repository)
        git("commit", "-m", "Unsafe runtime symlink", cwd=self.repository)
        revision = git("rev-parse", "HEAD", cwd=self.repository)
        with self.assertRaisesRegex(
            BOOTSTRAP.BootstrapError,
            "unsafe reviewed runtime entry",
        ):
            BOOTSTRAP.materialize_runtime(
                self.repository,
                self.state_root,
                revision,
            )

    def test_wrong_canonical_path_and_origin_are_rejected(self):
        canonical_patch, state_patch, origins_patch = self.production_boundary()
        with (
            canonical_patch,
            state_patch,
            origins_patch,
            self.assertRaisesRegex(
                BOOTSTRAP.BootstrapError,
                "canonical repository path is not approved",
            ),
        ):
            BOOTSTRAP.reviewed_runtime(
                self.root / "different-repository",
                self.state_root,
            )

        git(
            "remote",
            "set-url",
            "origin",
            str(self.root / "unapproved.git"),
            cwd=self.repository,
        )
        canonical_patch, state_patch, origins_patch = self.production_boundary()
        with (
            canonical_patch,
            state_patch,
            origins_patch,
            self.assertRaisesRegex(
                BOOTSTRAP.BootstrapError,
                "canonical origin is not approved",
            ),
        ):
            BOOTSTRAP.reviewed_runtime(self.repository, self.state_root)

    def test_existing_runtime_hash_mismatch_is_rejected(self):
        runtime = BOOTSTRAP.materialize_runtime(
            self.repository,
            self.state_root,
            self.revision,
        )
        tampered = runtime / BOOTSTRAP.RUNTIME_FILES[0]
        tampered.write_text("tampered after materialization\n", encoding="utf-8")
        with self.assertRaisesRegex(
            BOOTSTRAP.BootstrapError,
            "existing runtime verification failed",
        ):
            BOOTSTRAP.materialize_runtime(
                self.repository,
                self.state_root,
                self.revision,
            )

    def test_existing_runtime_mode_drift_is_rejected(self):
        runtime = BOOTSTRAP.materialize_runtime(
            self.repository,
            self.state_root,
            self.revision,
        )
        target = runtime / BOOTSTRAP.RUNTIME_FILES[0]
        target.chmod(0o666)
        with self.assertRaisesRegex(
            BOOTSTRAP.BootstrapError,
            "existing runtime verification failed",
        ):
            BOOTSTRAP.materialize_runtime(
                self.repository,
                self.state_root,
                self.revision,
            )


if __name__ == "__main__":
    unittest.main()
