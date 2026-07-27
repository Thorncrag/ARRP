import fcntl
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "arrp_nightly", ROOT / "scripts" / "arrp_nightly.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


class GitFixture:
    def __init__(self, root: Path):
        self.root = root
        self.remote = root / "remote.git"
        self.seed = root / "seed"
        self.repo = root / "repo"
        self.state = root / "state"
        run("git", "init", "--bare", str(self.remote))
        run("git", "init", "-b", "main", str(self.seed))
        self.configure(self.seed)
        (self.seed / ".gitignore").write_text(".env\nprivate-*\n", encoding="utf-8")
        issue = self.seed / "areas/TEST/issues/TEST-001.md"
        issue.parent.mkdir(parents=True)
        issue.write_text("baseline\n", encoding="utf-8")
        scripts = self.seed / "scripts"
        scripts.mkdir()
        (scripts / "arrp_nightly.py").write_text("print('reviewed')\n", encoding="utf-8")
        run("git", "add", ".gitignore", "areas/TEST/issues/TEST-001.md", "scripts/arrp_nightly.py", cwd=self.seed)
        run("git", "commit", "-m", "baseline", cwd=self.seed)
        run("git", "remote", "add", "origin", str(self.remote), cwd=self.seed)
        run("git", "push", "-u", "origin", "main", cwd=self.seed)
        run("git", "clone", "--branch", "main", str(self.remote), str(self.repo))
        self.configure(self.repo)

    @staticmethod
    def configure(repository: Path) -> None:
        run("git", "config", "user.name", "Fixture User", cwd=repository)
        run("git", "config", "user.email", "fixture@example.invalid", cwd=repository)

    def config(self) -> MODULE.RunnerConfig:
        return MODULE.RunnerConfig(
            self.repo,
            self.state,
            fixture_root=self.root,
            runtime_files=(),
        )

    def remote_commit(self, content: str, *, clone_name: str = "upstream") -> str:
        checkout = self.root / clone_name
        run("git", "clone", "--branch", "main", str(self.remote), str(checkout))
        self.configure(checkout)
        path = checkout / "areas/TEST/issues/TEST-001.md"
        path.write_text(content, encoding="utf-8")
        run("git", "add", "areas/TEST/issues/TEST-001.md", cwd=checkout)
        run("git", "commit", "-m", "origin change", cwd=checkout)
        run("git", "push", "origin", "main", cwd=checkout)
        return run("git", "rev-parse", "HEAD", cwd=checkout)


class ArrpNightlyTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fixture = GitFixture(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def test_dirty_ordinary_fixture_is_checkpointed(self):
        path = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        path.write_text("daytime ordinary work\n", encoding="utf-8")
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="ordinary-checkpoint"
        )
        self.assertEqual(result.status, "completed")
        self.assertIsNotNone(result.checkpoint_commit)
        committed = run(
            "git",
            "show",
            f"{result.checkpoint_commit}:areas/TEST/issues/TEST-001.md",
            cwd=self.fixture.repo,
        )
        self.assertEqual(committed, "daytime ordinary work")
        self.assertEqual(run("git", "status", "--porcelain", cwd=self.fixture.repo), "")
        manifest = json.loads(
            (
                self.fixture.state
                / "runs/ordinary-checkpoint/pre-lock-manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["branch"], "main")
        self.assertEqual(manifest["origin_url"], str(self.fixture.remote))
        self.assertTrue(manifest["due"])
        self.assertEqual(manifest["paths"][0]["path"], "areas/TEST/issues/TEST-001.md")

    def test_untracked_recognized_file_is_checkpointed(self):
        path = self.fixture.repo / "research/new-record.md"
        path.parent.mkdir()
        path.write_text("recognized\n", encoding="utf-8")
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="recognized-untracked"
        )
        names = run(
            "git",
            "show",
            "--pretty=",
            "--name-only",
            result.checkpoint_commit,
            cwd=self.fixture.repo,
        ).splitlines()
        self.assertIn("research/new-record.md", names)

    def test_ignored_private_file_is_excluded(self):
        private = self.fixture.repo / ".env"
        private_value = "SEC" + "RET=fixture-only"
        private.write_text(private_value + "\n", encoding="utf-8")
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="ignored-private"
        )
        self.assertEqual(result.status, "completed")
        self.assertIsNone(result.checkpoint_commit)
        self.assertTrue(private.exists())
        branch_files = run(
            "git", "ls-tree", "-r", "--name-only", result.branch, cwd=self.fixture.repo
        ).splitlines()
        self.assertNotIn(".env", branch_files)
        status_text = (self.fixture.state / "status.json").read_text(encoding="utf-8")
        self.assertNotIn(".env", status_text)
        self.assertNotIn(private_value, status_text)

    def test_protected_script_is_checkpointed_then_deferred(self):
        script = self.fixture.repo / "scripts/arrp_nightly.py"
        script.write_text("print('changed but not executed')\n", encoding="utf-8")
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="protected-script"
        )
        self.assertEqual(result.status, "review-required")
        self.assertEqual(result.protected_paths, ("scripts/arrp_nightly.py",))
        self.assertIsNone(result.worktree_path)
        self.assertEqual(
            run(
                "git",
                "show",
                f"{result.checkpoint_commit}:scripts/arrp_nightly.py",
                cwd=self.fixture.repo,
            ),
            "print('changed but not executed')",
        )

    def test_local_ahead_commit_remains_ancestor_of_nightly_branch(self):
        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.write_text("local commit\n", encoding="utf-8")
        run("git", "add", "areas/TEST/issues/TEST-001.md", cwd=self.fixture.repo)
        run("git", "commit", "-m", "local ahead", cwd=self.fixture.repo)
        local_ahead = run("git", "rev-parse", "HEAD", cwd=self.fixture.repo)
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="local-ahead"
        )
        ancestry = subprocess.run(
            ["git", "-C", str(self.fixture.repo), "merge-base", "--is-ancestor", local_ahead, result.branch]
        )
        self.assertEqual(ancestry.returncode, 0)

    def test_origin_ahead_is_merged_in_transaction_worktree(self):
        remote_head = self.fixture.remote_commit("origin ahead\n")
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="origin-ahead"
        )
        ancestry = subprocess.run(
            ["git", "-C", result.worktree_path, "merge-base", "--is-ancestor", remote_head, "HEAD"]
        )
        self.assertEqual(ancestry.returncode, 0)
        self.assertEqual(
            (Path(result.worktree_path) / "areas/TEST/issues/TEST-001.md").read_text(
                encoding="utf-8"
            ),
            "origin ahead\n",
        )

    def test_merge_conflict_preserves_branch_and_worktree(self):
        self.fixture.remote_commit("origin version\n")
        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.write_text("daytime conflicting version\n", encoding="utf-8")
        result = MODULE.prepare_transaction(
            self.fixture.config(), run_id="merge-conflict"
        )
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.failure_class, "origin_merge_conflict")
        self.assertTrue(Path(result.worktree_path).exists())
        self.assertIn(
            "UU areas/TEST/issues/TEST-001.md",
            run("git", "status", "--porcelain", cwd=Path(result.worktree_path)),
        )
        self.assertEqual(run("git", "status", "--porcelain", cwd=self.fixture.repo), "")

    def test_post_lock_canonical_change_blocks_publication(self):
        head = run("git", "rev-parse", "HEAD", cwd=self.fixture.repo)
        digest = MODULE.manifest_digest(MODULE.status_manifest(self.fixture.repo))
        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.write_text("late human change\n", encoding="utf-8")
        with self.assertRaisesRegex(MODULE.TransactionError, "post-lock canonical change"):
            MODULE.assert_canonical_unchanged(self.fixture.repo, head, digest)
        self.assertEqual(issue.read_text(encoding="utf-8"), "late human change\n")

    def test_lock_and_descriptors_are_released(self):
        MODULE.prepare_transaction(self.fixture.config(), run_id="lock-release")
        lock_path = self.fixture.state / "run.lock"
        descriptor = os.open(lock_path, os.O_RDWR)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)
        status = json.loads((self.fixture.state / "status.json").read_text())
        self.assertEqual(status["status"], "completed")

    def test_lock_contender_does_not_overwrite_owner_status(self):
        with MODULE.exclusive_lock(self.fixture.state, "active-owner"):
            with self.assertRaisesRegex(MODULE.TransactionError, "owns the operating-system lock"):
                MODULE.prepare_transaction(
                    self.fixture.config(), run_id="blocked-contender"
                )
            self.assertFalse((self.fixture.state / "status.json").exists())
            owner = json.loads(
                (self.fixture.state / "run-owner.json").read_text(encoding="utf-8")
            )
            self.assertEqual(owner["run_id"], "active-owner")

    def test_transaction_never_invokes_destructive_or_remote_publication_git(self):
        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.write_text("ordinary\n", encoding="utf-8")
        observed: list[tuple[str, ...]] = []
        original = MODULE.git

        def recording_git(repository, *args, **kwargs):
            observed.append(tuple(args))
            return original(repository, *args, **kwargs)

        with mock.patch.object(MODULE, "git", side_effect=recording_git):
            MODULE.prepare_transaction(self.fixture.config(), run_id="safe-command-set")
        prohibited = {"stash", "reset", "clean", "push", "pull", "rebase"}
        self.assertFalse(
            [arguments for arguments in observed if arguments and arguments[0] in prohibited]
        )
        self.assertFalse(
            [
                arguments
                for arguments in observed
                if "--force" in arguments or "--hard" in arguments
            ]
        )

    def test_fixture_guard_rejects_canonical_path_outside_fixture(self):
        config = MODULE.RunnerConfig(
            self.fixture.repo,
            self.fixture.state,
            fixture_root=self.root / "different",
        )
        with self.assertRaisesRegex(MODULE.TransactionError, "inside fixture root"):
            config.validate()

    def test_binary_change_is_rejected_without_staging(self):
        binary = self.fixture.repo / "research/binary.dat"
        binary.parent.mkdir()
        binary.write_bytes(b"safe-prefix\0fixture")
        with self.assertRaisesRegex(MODULE.TransactionError, "binary change is prohibited"):
            MODULE.prepare_transaction(self.fixture.config(), run_id="binary-reject")
        self.assertTrue(binary.exists())
        self.assertEqual(run("git", "diff", "--cached", "--name-only", cwd=self.fixture.repo), "")

    def test_fast_forward_main_reads_back_exact_remote_head(self):
        remote_head = self.fixture.remote_commit("fast-forward target\n")
        run("git", "fetch", "origin", "main", cwd=self.fixture.repo)
        observed = MODULE.fast_forward_main(self.fixture.repo, remote_head)
        self.assertEqual(observed, remote_head)
        self.assertEqual(run("git", "status", "--porcelain", cwd=self.fixture.repo), "")

    def test_fast_forward_main_refuses_dirty_worktree(self):
        issue = self.fixture.repo / "areas/TEST/issues/TEST-001.md"
        issue.write_text("dirty\n", encoding="utf-8")
        head = run("git", "rev-parse", "HEAD", cwd=self.fixture.repo)
        with self.assertRaisesRegex(MODULE.TransactionError, "requires a clean"):
            MODULE.fast_forward_main(self.fixture.repo, head)
        self.assertEqual(run("git", "rev-parse", "HEAD", cwd=self.fixture.repo), head)


if __name__ == "__main__":
    unittest.main()
