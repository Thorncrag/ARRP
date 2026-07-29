from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.path_authority import ProjectPathAuthority
from scripts.recover_transactions import (
    TransactionRecoveryError,
    collect_transaction_material,
    package_transaction,
    refresh_console_projection,
    safe_inventory,
)
from scripts.transaction_lifecycle import start_transaction


class TransactionRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.state = self.root / "state"
        self.worktrees = self.state / "worktrees"
        self.runs = self.state / "runs"
        self.worktrees.mkdir(parents=True)
        self.runs.mkdir()
        self.repository.mkdir()
        self.git("init", "-b", "main", cwd=self.repository)
        self.git("config", "user.name", "ARRP Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.repository / "README.md").write_text("base\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git("commit", "-m", "base")
        self.git("remote", "add", "origin", str(self.repository))
        base = self.rev("HEAD")
        self.git("update-ref", "refs/remotes/origin/main", base)
        self.authority = ProjectPathAuthority.fixture(
            self.root,
            repository_root=self.repository,
            state_root=self.state,
            output_root=self.repository,
        )

    def git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=cwd or self.repository,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def rev(self, revision: str) -> str:
        return self.git("rev-parse", revision).stdout.strip()

    def add_transaction(self, run_id: str = "run-1") -> Path:
        worktree = self.worktrees / run_id
        run = self.runs / run_id
        run.mkdir()
        branch = f"automation/nightly-{run_id}"
        self.git("worktree", "add", "-b", branch, str(worktree))
        (worktree / "README.md").write_text("preserved\n", encoding="utf-8")
        return worktree

    def test_registered_dirty_transaction_is_classified_and_packaged(self) -> None:
        self.add_transaction()
        material = collect_transaction_material(self.authority, "run-1")
        inventory = safe_inventory(material)
        self.assertEqual(inventory["classification"], "unique_review_required")
        result = package_transaction(self.authority, "run-1")
        self.assertEqual(result["classification"], "recovery_packaged")
        package = (
            self.state
            / "records/reconciliation/transaction-recovery"
            / result["recovery_package_id"].replace(":", "-")
        )
        self.assertTrue((package / "manifest.json").is_file())
        self.assertTrue((package / "delta.patch").is_file())
        self.assertFalse((package / ".git").exists())
        self.assertTrue((self.worktrees / "run-1").is_dir())

    def test_unregistered_or_mismatched_run_fails_closed(self) -> None:
        with self.assertRaises(TransactionRecoveryError):
            collect_transaction_material(self.authority, "missing-run")

    def test_symlinked_untracked_material_is_rejected(self) -> None:
        worktree = self.add_transaction()
        outside = self.root / "outside.txt"
        outside.write_text("outside\n", encoding="utf-8")
        (worktree / "unsafe-link").symlink_to(outside)
        with self.assertRaises(TransactionRecoveryError):
            collect_transaction_material(self.authority, "run-1")

    def test_console_projection_refresh_uses_fixed_owner_state(self) -> None:
        events = (
            self.state
            / "records"
            / "automation"
            / "transaction-events.jsonl"
        )
        start_transaction(
            events,
            run_id="run-1",
            attempt_group_id="group-1",
            attempt_number=1,
            trigger="fixture",
            branch="automation/nightly-run-1",
            head=self.rev("HEAD"),
            base=self.rev("HEAD"),
            logical_worktree_id="run-1",
            logical_run_id="run-1",
            delta_digest="sha256:" + "0" * 64,
            owner="fixture",
            next_action="Review preserved transaction.",
        )

        result = refresh_console_projection(self.authority)

        self.assertEqual(result["unresolved_count"], 1)
        output = (
            self.state
            / "records"
            / "reconciliation"
            / "transaction-recovery"
            / "console-projection.json"
        )
        self.assertTrue(output.is_file())
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
