from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import path_authority
from scripts import verify_arrp_private_migration as migration


class PrivateMigrationVerifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.repository = self.root / "repo"
        self.legacy = self.root / "legacy"
        self.storage = self.root / "storage"
        self.private = self.storage / "owner-staging"
        self.runtime = self.private / "role-a"
        self.records = self.private / "role-b"
        self.console = self.private / "role-c"
        self.migration = self.private / "role-d"
        self.control_packs = self.private / "role-e"
        for directory in (
            self.repository,
            self.legacy,
            self.storage,
            self.private,
            self.runtime,
            self.records,
            self.console,
            self.migration,
            self.control_packs,
        ):
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        (self.legacy / "worktrees").mkdir(mode=0o700)
        (self.legacy / "runs").mkdir(mode=0o700)
        (self.legacy / "PAUSED").write_text("paused\n", encoding="utf-8")
        (self.legacy / "run.lock").write_text("", encoding="utf-8")
        (self.legacy / "record.json").write_text(
            '{"safe": true}\n', encoding="utf-8"
        )
        for file_path in self.legacy.iterdir():
            if file_path.is_file():
                os.chmod(file_path, 0o600)
        self.descriptor = self.private / "authority.json"
        self.descriptor.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "authority_id": "fixture-private-staging",
                    "authority_mode": "inactive_successor_staging",
                    "activation_authorized": False,
                    "private_root": str(self.private),
                    "roles": {
                        "runtime": "role-a",
                        "records": "role-b",
                        "owner_console_versions": "role-c",
                        "migration": "role-d",
                        "disclosure_control_packs": "role-e",
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        os.chmod(self.descriptor, 0o600)
        patches = (
            mock.patch.object(
                path_authority, "APPROVED_REPOSITORY_ROOT", self.repository
            ),
            mock.patch.object(
                path_authority, "APPROVED_STATE_ROOT", self.legacy
            ),
        )
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_manifest_proves_pause_and_free_lock_without_activation(self) -> None:
        manifest = migration.build_manifest(
            private_authority_descriptor=self.descriptor, deep=True
        )

        self.assertEqual(
            manifest["status"],
            "inactive_successor_inventory_complete",
        )
        self.assertFalse(manifest["activation_authorized"])
        self.assertTrue(manifest["pause"]["present"])
        self.assertTrue(manifest["lock"]["free"])
        self.assertGreaterEqual(
            manifest["current_inventory"]["file_count"], 3
        )
        self.assertTrue(
            manifest["current_inventory"]["manifest_sha256"].startswith(
                "sha256:"
            )
        )
        file_entries = [
            entry
            for entry in manifest["current_inventory"]["entries"]
            if entry["type"] == "file"
        ]
        self.assertTrue(all("sha256" in entry for entry in file_entries))

    def test_missing_pause_or_owned_lock_fails_closed(self) -> None:
        os.rename(self.legacy / "PAUSED", self.legacy / "pause-preserved")
        with self.assertRaisesRegex(
            migration.MigrationVerificationError,
            "required runtime control",
        ):
            migration.build_manifest(
                private_authority_descriptor=self.descriptor, deep=False
            )

        os.rename(self.legacy / "pause-preserved", self.legacy / "PAUSED")
        with mock.patch.object(migration, "_lock_is_free", return_value=False):
            with self.assertRaisesRegex(
                migration.MigrationVerificationError,
                "currently owned",
            ):
                migration.build_manifest(
                    private_authority_descriptor=self.descriptor, deep=False
                )

    def test_private_manifest_is_new_owner_only_and_never_replaced(self) -> None:
        manifest = migration.build_manifest(
            private_authority_descriptor=self.descriptor, deep=False
        )
        output = self.migration / "review" / "inventory.json"

        migration._write_new_private_manifest(output, manifest)

        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        loaded = json.loads(output.read_text(encoding="utf-8"))
        self.assertFalse(loaded["activation_authorized"])
        with self.assertRaises(FileExistsError):
            migration._write_new_private_manifest(output, manifest)

    def test_inventory_records_symlink_content_without_following_it(self) -> None:
        outside = self.root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        (self.legacy / "linked.txt").symlink_to(outside)

        inventory = migration.inventory_tree(self.legacy, deep=False)

        self.assertEqual(inventory["symlink_count"], 1)
        linked = next(
            entry
            for entry in inventory["entries"]
            if entry["path"] == "linked.txt"
        )
        self.assertEqual(linked["type"], "symlink")
        self.assertEqual(linked["target"], str(outside))

    def test_descriptor_is_required_and_a_missing_descriptor_fails_closed(self) -> None:
        parser = migration._parser()
        descriptor_action = next(
            action
            for action in parser._actions
            if action.dest == "private_authority_descriptor"
        )
        self.assertTrue(descriptor_action.required)
        with self.assertRaises(path_authority.PathAuthorityError):
            migration.build_manifest(
                private_authority_descriptor=self.private / "missing.json",
                deep=False,
            )


if __name__ == "__main__":
    unittest.main()
