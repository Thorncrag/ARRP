from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import path_authority as authority


class ProjectPathAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.repository = self.root / "canonical"
        self.state = self.root / "state"
        self.storage_floor = self.root / "storage"
        self.private = self.storage_floor / "private-staging"
        self.private_runtime = self.private / "role-a"
        self.private_records = self.private / "role-b"
        self.private_console_versions = self.private / "role-c"
        self.private_migration = self.private / "role-d"
        self.private_control_packs = (
            self.private / "role-e"
        )
        self.repository.mkdir(mode=0o700)
        self.state.mkdir(mode=0o700)
        self.storage_floor.mkdir(mode=0o700)
        self.private.mkdir(mode=0o700)
        for path in (
            self.private_runtime,
            self.private_records,
            self.private_console_versions,
            self.private_migration,
            self.private_control_packs,
        ):
            path.mkdir(mode=0o700, parents=True)
        (self.private_records / "automation").mkdir(mode=0o700)
        (self.state / "worktrees").mkdir(mode=0o700)
        (self.state / "runs").mkdir(mode=0o700)
        self.private_descriptor = self.private / "authority.json"
        self.private_descriptor.write_text(
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
        os.chmod(self.private_descriptor, 0o600)
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

    def test_outside_transaction_path_is_rejected_before_filesystem_probe(self) -> None:
        worktrees = self.state / "worktrees"
        for requested in (
            self.root / "outside",
            worktrees / "nested" / "run-1",
            worktrees / ".." / "runs" / "run-1",
        ):
            with self.subTest(requested=requested), mock.patch.object(
                authority,
                "_resolved_directory",
                side_effect=AssertionError("unexpected filesystem probe"),
            ) as resolve:
                with self.assertRaisesRegex(
                    authority.PathAuthorityError,
                    "outside its authorized boundary",
                ):
                    authority._direct_child(
                        worktrees,
                        requested,
                        "transaction worktree",
                    )
                resolve.assert_not_called()

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

    def test_successor_private_layout_is_validated_without_activation(self) -> None:
        selected = authority.PrivateProjectAuthority.fixture_staging(
            self.private_descriptor,
            fixture_root=self.storage_floor,
        )

        self.assertEqual(selected.private_root, self.private.resolve())
        self.assertEqual(selected.runtime_root, self.private_runtime.resolve())
        self.assertEqual(selected.records_root, self.private_records.resolve())
        self.assertEqual(
            selected.owner_console_versions_root,
            self.private_console_versions.resolve(),
        )
        self.assertEqual(
            selected.migration_root,
            self.private_migration.resolve(),
        )
        self.assertEqual(
            selected.control_pack_root,
            self.private_control_packs.resolve(),
        )
        self.assertEqual(
            selected.records_output("automation/security-incidents.jsonl"),
            self.private_records
            / "automation"
            / "security-incidents.jsonl",
        )
        supplement = self.private_records / "governance" / "supplements.jsonl"
        supplement.parent.mkdir(mode=0o700)
        supplement.write_text("{}\n", encoding="utf-8")
        os.chmod(supplement, 0o600)
        self.assertEqual(
            selected.records_path("governance/supplements.jsonl"),
            supplement,
        )
        with self.assertRaises(authority.PathAuthorityError):
            selected.records_path("../outside.jsonl")

    def test_successor_rejects_file_provider_and_symlink_boundaries(self) -> None:
        with mock.patch.object(
            authority,
            "_file_provider_domain",
            side_effect=lambda path: (
                b"provider" if path == self.private else None
            ),
        ):
            with self.assertRaisesRegex(
                authority.PathAuthorityError,
                "File Provider",
            ):
                authority.PrivateProjectAuthority.fixture_staging(
                    self.private_descriptor,
                    fixture_root=self.storage_floor,
                )

        real_private = self.private
        linked = self.storage_floor / "linked-private"
        linked.symlink_to(real_private, target_is_directory=True)
        payload = json.loads(
            self.private_descriptor.read_text(encoding="utf-8")
        )
        payload["private_root"] = str(linked)
        linked_descriptor = self.private / "linked-authority.json"
        linked_descriptor.write_text(
            json.dumps(payload) + "\n",
            encoding="utf-8",
        )
        os.chmod(linked_descriptor, 0o600)
        with self.assertRaisesRegex(
            authority.PathAuthorityError,
            "only directories",
        ):
            authority.PrivateProjectAuthority.fixture_staging(
                linked_descriptor,
                fixture_root=self.storage_floor,
            )

    def test_successor_rejects_unsafe_subroot_permissions(self) -> None:
        os.chmod(self.private_runtime, 0o755)
        with self.assertRaisesRegex(
            authority.PathAuthorityError,
            "permissions are unsafe",
        ):
            authority.PrivateProjectAuthority.fixture_staging(
                self.private_descriptor,
                fixture_root=self.storage_floor,
            )

    def test_private_staging_descriptor_cannot_overlap_production(self) -> None:
        payload = json.loads(
            self.private_descriptor.read_text(encoding="utf-8")
        )
        payload["private_root"] = str(self.state)
        payload["roles"] = {
            "runtime": "worktrees",
            "records": "runs",
            "owner_console_versions": "role-c",
            "migration": "role-d",
            "disclosure_control_packs": "role-e",
        }
        for role in ("role-c", "role-d", "role-e"):
            (self.state / role).mkdir(mode=0o700)
        descriptor = self.state / "authority.json"
        descriptor.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        os.chmod(descriptor, 0o600)
        with self.assertRaisesRegex(
            authority.PathAuthorityError,
            "overlaps an approved production boundary",
        ):
            authority.PrivateProjectAuthority.fixture_staging(
                descriptor,
                fixture_root=self.state,
            )

    def test_private_staging_descriptor_contract_fails_closed(self) -> None:
        original = json.loads(
            self.private_descriptor.read_text(encoding="utf-8")
        )
        cases = (
            ("unknown", {**original, "unexpected": True}, "unknown or missing"),
            (
                "invalid-id",
                {**original, "authority_id": "unsafe authority"},
                "unsupported",
            ),
            (
                "activation",
                {**original, "activation_authorized": True},
                "unsupported",
            ),
            (
                "unnormalized-root",
                {**original, "private_root": f"{self.private}/../private-staging"},
                "unsupported",
            ),
        )
        for name, payload, message in cases:
            with self.subTest(name=name):
                descriptor = self.private / f"{name}.json"
                descriptor.write_text(
                    json.dumps(payload) + "\n",
                    encoding="utf-8",
                )
                os.chmod(descriptor, 0o600)
                with self.assertRaisesRegex(
                    authority.PathAuthorityError,
                    message,
                ):
                    authority.PrivateProjectAuthority.fixture_staging(
                        descriptor,
                        fixture_root=self.storage_floor,
                    )

    def test_private_staging_roles_must_be_disjoint(self) -> None:
        nested = self.private_runtime / "nested"
        nested.mkdir(mode=0o700)
        payload = json.loads(
            self.private_descriptor.read_text(encoding="utf-8")
        )
        payload["roles"]["records"] = "role-a/nested"
        descriptor = self.private / "overlapping-roles.json"
        descriptor.write_text(
            json.dumps(payload) + "\n",
            encoding="utf-8",
        )
        os.chmod(descriptor, 0o600)
        with self.assertRaisesRegex(
            authority.PathAuthorityError,
            "disjoint",
        ):
            authority.PrivateProjectAuthority.fixture_staging(
                descriptor,
                fixture_root=self.storage_floor,
            )

    def test_production_private_staging_uses_only_the_fixed_descriptor(
        self,
    ) -> None:
        with (
            mock.patch.object(
                authority,
                "APPROVED_PRIVATE_STAGING_ROOT",
                self.private,
            ),
            mock.patch.object(
                authority,
                "APPROVED_PRIVATE_STAGING_DESCRIPTOR",
                self.private_descriptor,
            ),
        ):
            selected = authority.PrivateProjectAuthority.production_staging()
        self.assertEqual(selected.private_root, self.private.resolve())
        with self.assertRaises(TypeError):
            authority.PrivateProjectAuthority.production_staging(  # type: ignore[call-arg]
                self.private_descriptor
            )

    def test_fixture_private_authority_cannot_target_production_or_escape(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            authority.PathAuthorityError,
            "overlaps an approved production boundary",
        ):
            authority.PrivateProjectAuthority.fixture_staging(
                self.private_descriptor,
                fixture_root=self.repository,
            )
        outside = self.root / "outside-authority.json"
        outside.write_text(
            self.private_descriptor.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        os.chmod(outside, 0o600)
        with self.assertRaisesRegex(
            authority.PathAuthorityError,
            "outside its explicit fixture authority",
        ):
            authority.PrivateProjectAuthority.fixture_staging(
                outside,
                fixture_root=self.storage_floor,
            )

    def test_production_clis_expose_no_fixture_root_switch(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        for relative in (
            "scripts/append_agent_audit_log.py",
            "scripts/build_elim_context.py",
            "scripts/build_project_console.py",
            "scripts/build_owner_console.py",
            "scripts/operational_incidents.py",
            "scripts/record_review_epoch.py",
            "scripts/repository_gates.py",
            "scripts/verify_arrp_private_migration.py",
        ):
            with self.subTest(relative=relative):
                source = (repository / relative).read_text(encoding="utf-8")
                self.assertNotIn("--fixture-root", source)
                self.assertNotIn("--private-authority-descriptor", source)


if __name__ == "__main__":
    unittest.main()
