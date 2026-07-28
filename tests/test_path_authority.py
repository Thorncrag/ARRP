from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import path_authority as authority


class ProjectPathAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository = self.root / "canonical"
        self.state = self.root / "state"
        self.repository.mkdir()
        self.state.mkdir(mode=0o700)
        (self.state / "worktrees").mkdir(mode=0o700)
        (self.state / "runs").mkdir(mode=0o700)
        self.patch_repository = mock.patch.object(
            authority, "APPROVED_REPOSITORY_ROOT", self.repository
        )
        self.patch_state = mock.patch.object(
            authority, "APPROVED_STATE_ROOT", self.state
        )
        self.patch_repository.start()
        self.patch_state.start()
        self.addCleanup(self.patch_repository.stop)
        self.addCleanup(self.patch_state.stop)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_matching_transaction_worktree_and_run_root_are_authorized(self) -> None:
        worktree = self.state / "worktrees" / "run-1"
        run = self.state / "runs" / "run-1"
        worktree.mkdir(mode=0o700)
        run.mkdir(mode=0o700)

        selected = authority.ProjectPathAuthority.production_transaction(
            repository_root=worktree,
            run_root=run,
        )

        self.assertEqual(selected.mode, "production_transaction")
        self.assertEqual(selected.repository_root, worktree.resolve())
        self.assertEqual(selected.output_root, run.resolve())

    def test_transaction_identity_mismatch_and_symlink_escape_are_rejected(self) -> None:
        worktree = self.state / "worktrees" / "run-1"
        run = self.state / "runs" / "run-2"
        worktree.mkdir(mode=0o700)
        run.mkdir(mode=0o700)
        with self.assertRaises(authority.PathAuthorityError):
            authority.ProjectPathAuthority.production_transaction(
                repository_root=worktree,
                run_root=run,
            )

        outside = self.root / "outside"
        outside.mkdir()
        link = self.state / "worktrees" / "run-2"
        link.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(authority.PathAuthorityError):
            authority.ProjectPathAuthority.production_transaction(
                repository_root=link,
                run_root=run,
            )

    def test_fixture_cannot_overlap_any_production_boundary(self) -> None:
        nested = self.state / "fixture"
        nested.mkdir(mode=0o700)
        with self.assertRaises(authority.PathAuthorityError):
            authority.ProjectPathAuthority.fixture(
                nested,
                repository_root=nested,
                state_root=nested,
            )

    def test_fixture_paths_are_contained_and_normalized(self) -> None:
        fixture = self.root / "fixture"
        repository = fixture / "repo"
        state = fixture / "state"
        output = fixture / "output"
        for path in (fixture, repository, state, output):
            path.mkdir()
        selected = authority.ProjectPathAuthority.fixture(
            fixture,
            repository_root=repository,
            state_root=state,
            output_root=output,
        )
        (repository / "safe.txt").write_text("safe", encoding="utf-8")
        self.assertEqual(
            selected.repository_path("safe.txt"),
            (repository / "safe.txt").resolve(),
        )
        for unsafe in ("../outside", "/absolute", "nested//value", "./value"):
            with self.assertRaises(authority.PathAuthorityError):
                selected.repository_path(unsafe)

    def test_owner_state_permissions_fail_closed(self) -> None:
        os.chmod(self.state, 0o755)
        with self.assertRaises(authority.PathAuthorityError):
            authority.ProjectPathAuthority.production()


if __name__ == "__main__":
    unittest.main()
