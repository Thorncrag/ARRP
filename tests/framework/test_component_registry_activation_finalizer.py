"""Fixture-only tests for the fixed Component Registry activation finalizer."""

from __future__ import annotations

import copy
import errno
import hashlib
import inspect
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import finalize_component_registry_activation as finalizer
from scripts.path_authority import ProjectPathAuthority


class LegacyStage1ActivationFinalizerExamples:
    def git(self, repository: Path, *arguments: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    def source_candidate(self) -> dict[str, object]:
        current = json.loads(
            finalizer.registry.DEFAULT_REGISTRY.read_text(encoding="utf-8")
        )
        if current.get("status") == "candidate":
            return current
        candidate_revision = current["approval"]["value"]["base_revision"]
        candidate = json.loads(
            self.git(
                finalizer.registry.ROOT,
                "show",
                f"{candidate_revision}:framework/component-registry.json",
            )
        )
        if (
            candidate.get("status") != "candidate"
            or finalizer.registry._canonical_registry_digest(candidate)
            != current["approval"]["value"]["candidate_registry_sha256"]
        ):
            self.fail("active registry candidate parent is not exact")
        return candidate

    def fixture(
        self,
        temporary: str,
    ) -> tuple[
        ProjectPathAuthority,
        dict[str, object],
        dict[str, object],
    ]:
        root = Path(temporary)
        repository = root / "repository"
        state = root / "state"
        output = root / "output"
        for directory in (repository, state, output):
            directory.mkdir(mode=0o700)
        self.git(repository, "init", "-b", "main")
        self.git(repository, "config", "user.name", "ARRP Fixture")
        self.git(
            repository,
            "config",
            "user.email",
            "fixture@example.invalid",
        )
        marker = repository / "marker.txt"
        marker.write_text("base\n", encoding="utf-8")
        schema = (
            repository
            / "framework"
            / "standards"
            / "automation"
            / "component-registry.schema.json"
        )
        schema.parent.mkdir(parents=True)
        shutil.copy2(
            finalizer.registry.ROOT
            / "framework"
            / "standards"
            / "automation"
            / "component-registry.schema.json",
            schema,
        )
        self.git(repository, "add", ".")
        self.git(repository, "commit", "-m", "base")
        pull_request_base = self.git(repository, "rev-parse", "HEAD")
        self.git(repository, "switch", "-c", "activation")
        registry_path = repository / "framework/component-registry.json"
        candidate = self.source_candidate()
        candidate["source_baseline"][
            "repository_revision"
        ] = pull_request_base
        candidate["source_baseline"]["working_tree_binding"]["sha256"] = (
            finalizer.registry._route_source_binding(
                pull_request_base,
                finalizer.registry._routing_snapshot(candidate),
            )
        )
        registry_path.write_text(
            json.dumps(candidate, indent=2) + "\n",
            encoding="utf-8",
        )
        self.git(repository, "add", str(registry_path))
        self.git(repository, "commit", "-m", "candidate snapshot")
        candidate_revision = self.git(repository, "rev-parse", "HEAD")
        candidate_digest = finalizer.registry._canonical_registry_digest(
            candidate
        )
        approval = {
            "approval_type": "stage1_component_registry_activation",
            "approved_by": "@Thorncrag",
            "approval_method": "explicit_recorded_owner_activation",
            "governance_change_id": "GOV-2026-001",
            "implementation_contract_id": (
                "COMPONENT-REGISTRY-2026-001-ACTIVATION"
            ),
            "base_revision": candidate_revision,
            "candidate_registry_sha256": candidate_digest,
            "affected_stable_ids": ["COMPONENT-REGISTRY"],
            "purpose_scope": "Activate the reviewed registry.",
            "bounded_diff_sha256": "0" * 64,
            "approved_at": "2026-07-30T00:00:00-04:00",
            "owner_review_reference": (
                "github-review:Thorncrag/ARRP#123"
            ),
        }
        normalized_active = (
            finalizer.registry.build_simulated_active_registry(
                candidate,
                repository_revision=candidate_revision,
                approval_value=approval,
            )
        )
        transition = {
            "schema_version": 1,
            "algorithm": "component_registry_candidate_to_active_v1",
            "candidate_registry_sha256": candidate_digest,
            "normalized_active_registry_sha256": (
                finalizer.registry._canonical_registry_digest(
                    normalized_active
                )
            ),
            "affected_stable_ids": ["COMPONENT-REGISTRY"],
        }
        approval["bounded_diff_sha256"] = hashlib.sha256(
            finalizer.registry.canonical_json(transition).encode("utf-8")
        ).hexdigest()
        active = finalizer.registry.build_simulated_active_registry(
            candidate,
            repository_revision=candidate_revision,
            approval_value=approval,
        )
        registry_path.write_text(
            json.dumps(active, indent=2) + "\n",
            encoding="utf-8",
        )
        self.git(repository, "commit", "-am", "reviewed activation")
        reviewed_head = self.git(repository, "rev-parse", "HEAD")
        self.git(repository, "switch", "main")
        self.git(
            repository,
            "merge",
            "--no-ff",
            "activation",
            "-m",
            "merged activation",
        )
        remote_main = self.git(repository, "rev-parse", "HEAD")
        self.git(
            repository,
            "update-ref",
            "refs/remotes/origin/main",
            remote_main,
        )
        local_revision = remote_main
        authority = ProjectPathAuthority.fixture(
            root,
            repository_root=repository,
            state_root=state,
            output_root=output,
        )
        observations = {
            "repository": "Thorncrag/ARRP",
            "default_branch": "main",
            "pull_request_number": 123,
            "pull_request_state": "closed",
            "pull_request_merged": True,
            "pull_request_auto_merge": None,
            "merged_by": "Thorncrag",
            "pull_request_base_repository": "Thorncrag/ARRP",
            "pull_request_base_branch": "main",
            "pull_request_base_revision": pull_request_base,
            "reviewed_head_revision": reviewed_head,
            "merge_commit_sha": remote_main,
            "merged_at": "2026-07-30T00:02:00-04:00",
            "check_runs": [
                {
                    "name": "ARRP validation",
                    "head_sha": reviewed_head,
                    "status": "completed",
                    "conclusion": "success",
                    "completed_at": "2026-07-30T00:01:00-04:00",
                    "app": {"id": 1},
                }
            ],
            "check_runs_total_count": 1,
            "check_runs_complete": True,
            "legacy_statuses": [],
            "legacy_statuses_complete": True,
            "required_status_checks": [
                {"context": "ARRP validation", "app_id": 1}
            ],
            "requirements_complete": True,
            "remote_main_revision": remote_main,
            "reviewed_registry": copy.deepcopy(active),
            "remote_registry": copy.deepcopy(active),
            "local_revision": local_revision,
            "origin_main_revision": remote_main,
            "verified_at": "2026-07-30T00:03:00-04:00",
        }
        return authority, active, observations

    def test_production_entry_point_accepts_no_authority_or_evidence(self):
        self.assertEqual(
            list(inspect.signature(finalizer.finalize_activation).parameters),
            [],
        )

    def test_fixture_finalizer_writes_exact_owner_only_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority, active, observations = self.fixture(temporary)
            receipt = finalizer.verify_fixture_and_write(
                authority,
                active,
                observations,
            )
            logical = (
                "records/governance/component-registry/"
                "activation-readbacks/"
                f"{receipt['registry_sha256']}.json"
            )
            path = authority.state_root / logical
            self.assertTrue(path.is_file())
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                receipt,
            )
            with self.assertRaises(finalizer.ActivationFinalizationError):
                finalizer.verify_fixture_and_write(
                    authority,
                    active,
                    observations,
                )

    def test_wrong_identity_merge_checks_and_remote_registry_fail(self):
        mutations = [
            ("repository", "Other/Repository"),
            ("pull_request_number", 124),
            ("pull_request_merged", False),
            ("merged_by", "SomeoneElse"),
            ("pull_request_auto_merge", {"enabled_by": {"login": "Thorncrag"}}),
            (
                "check_runs",
                [
                    {
                        "name": "ARRP validation",
                        "head_sha": "0" * 40,
                        "status": "completed",
                        "conclusion": "success",
                        "completed_at": "2026-07-30T00:01:00-04:00",
                    }
                ],
            ),
            ("remote_registry", {"registry_id": "OTHER"}),
        ]
        for key, value in mutations:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                authority, active, observations = self.fixture(temporary)
                observations[key] = value
                with self.assertRaises(
                    finalizer.ActivationFinalizationError
                ):
                    finalizer._build_receipt(
                        authority,
                        active,
                        observations,
                    )

    def test_nonancestral_revisions_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority, active, observations = self.fixture(temporary)
            observations["remote_main_revision"] = "f" * 40
            with self.assertRaises(finalizer.ActivationFinalizationError):
                finalizer._build_receipt(
                    authority,
                    active,
                    observations,
                )

    def test_candidate_transition_facts_are_derived(self):
        mutations = {
            "candidate_digest": lambda active, observations: active[
                "approval"
            ]["value"].__setitem__("candidate_registry_sha256", "0" * 64),
            "bounded_diff": lambda active, observations: active["approval"][
                "value"
            ].__setitem__("bounded_diff_sha256", "0" * 64),
            "affected_ids": lambda active, observations: active["approval"][
                "value"
            ].__setitem__(
                "affected_stable_ids",
                ["COMPONENT-REGISTRY", "OTHER"],
            ),
            "nonparent_base": lambda active, observations: active["approval"][
                "value"
            ].__setitem__(
                "base_revision",
                observations["pull_request_base_revision"],
            ),
            "extra_active_leaf": lambda active, observations: active.__setitem__(
                "unexpected_fixture_leaf",
                True,
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                authority, active, observations = self.fixture(temporary)
                mutate(active, observations)
                observations["reviewed_registry"] = copy.deepcopy(active)
                observations["remote_registry"] = copy.deepcopy(active)
                with self.assertRaises(
                    finalizer.ActivationFinalizationError
                ):
                    finalizer._build_receipt(
                        authority,
                        active,
                        observations,
                    )

    def test_candidate_parent_internal_base_and_route_binding_are_exact(self):
        mutations = {
            "source_baseline": lambda candidate: candidate[
                "source_baseline"
            ].__setitem__("repository_revision", "0" * 40),
            "route_binding": lambda candidate: candidate[
                "source_baseline"
            ]["working_tree_binding"].__setitem__("sha256", "0" * 64),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                authority, active, observations = self.fixture(temporary)
                candidate = finalizer._git_registry_at_revision(
                    authority.repository_root,
                    active["approval"]["value"]["base_revision"],
                )
                mutate(candidate)
                with (
                    patch.object(
                        finalizer,
                        "_git_registry_at_revision",
                        return_value=candidate,
                    ),
                    self.assertRaises(
                        finalizer.ActivationFinalizationError
                    ),
                ):
                    finalizer._build_receipt(
                        authority,
                        active,
                        observations,
                    )

    def test_exact_merge_local_origin_and_pr_base_are_required(self):
        mutations = (
            ("pull_request_base_repository", "Other/ARRP"),
            ("pull_request_base_branch", "develop"),
            ("merge_commit_sha", "0" * 40),
            ("remote_main_revision", "0" * 40),
            ("local_revision", "0" * 40),
            ("origin_main_revision", "0" * 40),
        )
        for key, value in mutations:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                authority, active, observations = self.fixture(temporary)
                observations[key] = value
                with self.assertRaises(
                    finalizer.ActivationFinalizationError
                ):
                    finalizer._build_receipt(
                        authority,
                        active,
                        observations,
                    )

    def test_exact_head_owner_manual_merge_governs(self):
        for key, value in (
            ("merged_by", "SomeoneElse"),
            ("pull_request_auto_merge", {"enabled_by": {"login": "Thorncrag"}}),
        ):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                authority, active, observations = self.fixture(temporary)
                observations[key] = value
                with self.assertRaises(
                    finalizer.ActivationFinalizationError
                ):
                    finalizer._build_receipt(
                        authority,
                        active,
                        observations,
                    )

    def test_required_checks_are_exact_and_optional_failures_are_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority, active, observations = self.fixture(temporary)
            observations["check_runs"].append(
                {
                    "name": "Optional experiment",
                    "head_sha": observations["reviewed_head_revision"],
                    "status": "completed",
                    "conclusion": "failure",
                    "completed_at": "2026-07-30T00:01:00-04:00",
                    "app": {"id": 2},
                }
            )
            observations["check_runs_total_count"] = 2
            receipt = finalizer._build_receipt(
                authority,
                active,
                observations,
            )
            self.assertEqual(receipt["required_checks_state"], "success")

        mutations = (
            ("check_runs", []),
            (
                "check_runs",
                [
                    {
                        "name": "ARRP validation",
                        "head_sha": "0" * 40,
                        "status": "completed",
                        "conclusion": "success",
                        "completed_at": "2026-07-30T00:01:00-04:00",
                        "app": {"id": 1},
                    }
                ],
            ),
            (
                "check_runs",
                [
                    {
                        "name": "ARRP validation",
                        "head_sha": None,
                        "status": "in_progress",
                        "conclusion": None,
                        "completed_at": None,
                        "app": {"id": 1},
                    }
                ],
            ),
            (
                "required_status_checks",
                [{"context": "ARRP validation", "app_id": 2}],
            ),
        )
        for key, value in mutations:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                authority, active, observations = self.fixture(temporary)
                if key == "check_runs" and value:
                    value[0]["head_sha"] = (
                        value[0]["head_sha"]
                        or observations["reviewed_head_revision"]
                    )
                observations[key] = value
                observations["check_runs_total_count"] = len(
                    observations["check_runs"]
                )
                with self.assertRaises(
                    finalizer.ActivationFinalizationError
                ):
                    finalizer._build_receipt(
                        authority,
                        active,
                        observations,
                    )

    def test_required_legacy_status_and_ambiguous_duplicates(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority, active, observations = self.fixture(temporary)
            observations["check_runs"] = []
            observations["check_runs_total_count"] = 0
            observations["required_status_checks"] = [
                {"context": "ARRP validation", "app_id": None}
            ]
            observations["legacy_statuses"] = [
                {
                    "context": "ARRP validation",
                    "sha": observations["reviewed_head_revision"],
                    "state": "success",
                    "updated_at": "2026-07-30T00:01:00-04:00",
                }
            ]
            finalizer._build_receipt(authority, active, observations)
            observations["legacy_statuses"].append(
                copy.deepcopy(observations["legacy_statuses"][0])
            )
            with self.assertRaises(finalizer.ActivationFinalizationError):
                finalizer._build_receipt(
                    authority,
                    active,
                    observations,
                )

    def test_paginated_evidence_requires_complete_declared_counts(self):
        pages = [
            {"total_count": 2, "check_runs": [{"id": 1}]},
            {"total_count": 2, "check_runs": [{"id": 2}]},
        ]
        with patch.object(finalizer, "_paginated_pages", return_value=pages):
            rows, total = finalizer._paginated_check_runs("fixture")
        self.assertEqual(total, 2)
        self.assertEqual([row["id"] for row in rows], [1, 2])
        pages[-1]["total_count"] = 3
        with (
            patch.object(finalizer, "_paginated_pages", return_value=pages),
            self.assertRaises(finalizer.ActivationFinalizationError),
        ):
            finalizer._paginated_check_runs("fixture")

    def test_ruleset_and_branch_requirements_are_combined_exactly(self):
        branch = {
            "protection": {
                "required_status_checks": {
                    "checks": [{"context": "Build", "app_id": 1}],
                    "contexts": ["Legacy"],
                }
            }
        }
        rules = [
            {
                "type": "required_status_checks",
                "parameters": {
                    "required_status_checks": [
                        {"context": "Audit", "integration_id": 2}
                    ]
                },
            }
        ]
        self.assertEqual(
            finalizer._required_status_checks(branch, rules),
            [
                {"context": "Audit", "app_id": 2},
                {"context": "Build", "app_id": 1},
                {"context": "Legacy", "app_id": None},
            ],
        )

    def test_activation_chronology_is_strict_and_timezone_bound(self):
        mutations = (
            ("merged_at", "2026-07-29T23:59:00-04:00"),
            ("verified_at", "not-a-time"),
            ("merged_at", "2026-07-30T00:02:00"),
        )
        for key, value in mutations:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                authority, active, observations = self.fixture(temporary)
                observations[key] = value
                with self.assertRaises(
                    finalizer.ActivationFinalizationError
                ):
                    finalizer._build_receipt(
                        authority,
                        active,
                        observations,
                    )

    def test_partial_write_leaves_no_final_or_temporary_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority, active, observations = self.fixture(temporary)
            receipt = finalizer._build_receipt(
                authority,
                active,
                observations,
            )
            with (
                patch.object(
                    finalizer.os,
                    "write",
                    side_effect=OSError("fixture partial write"),
                ),
                self.assertRaises(finalizer.ActivationFinalizationError),
            ):
                finalizer._write_fixed_receipt(authority, receipt)
            directory = (
                authority.state_root
                / "records"
                / "governance"
                / "component-registry"
                / "activation-readbacks"
            )
            self.assertEqual(list(directory.iterdir()), [])

    def test_cli_rejects_every_argument_before_finalization(self):
        with patch.object(finalizer, "finalize_activation") as finalize:
            self.assertEqual(finalizer.main(["--receipt", "fixture"]), 2)
        finalize.assert_not_called()

    def test_fixture_harness_cannot_target_production_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority, active, observations = self.fixture(temporary)
            substitute = copy.copy(authority)
            object.__setattr__(substitute, "mode", "production_canonical")
            with self.assertRaises(finalizer.ActivationFinalizationError):
                finalizer.verify_fixture_and_write(
                    substitute,
                    active,
                    observations,
                )

    def test_symlink_receipt_directory_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority, active, observations = self.fixture(temporary)
            target = Path(temporary) / "elsewhere"
            target.mkdir()
            records = authority.state_root / "records"
            records.symlink_to(target, target_is_directory=True)
            with self.assertRaises(finalizer.ActivationFinalizationError):
                finalizer.verify_fixture_and_write(
                    authority,
                    active,
                    observations,
                )


class ComponentRegistryStage2FinalizerTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(
            finalizer.registry.DEFAULT_REGISTRY.read_text(encoding="utf-8")
        )
        self.revision = "1" * 40
        self.evidence = {
            "adopted_by": "@Thorncrag",
            "adopted_at": "2026-07-31T12:00:00-04:00",
            "pull_request": "github-review:Thorncrag/ARRP#501",
            "base_revision": "3" * 40,
            "reviewed_head": "2" * 40,
            "merge_commit": self.revision,
            "checks_revision": "2" * 40,
            "checks_state": "success",
        }

    def authority(self, temporary: str) -> ProjectPathAuthority:
        root = Path(temporary)
        repository = root / "repository"
        state = root / "state"
        output = root / "output"
        for directory in (repository, state, output):
            directory.mkdir(mode=0o700)
        return ProjectPathAuthority.fixture(
            root,
            repository_root=repository,
            state_root=state,
            output_root=output,
        )

    def test_fixture_writes_exact_owner_only_digest_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority = self.authority(temporary)
            result = finalizer.verify_stage2_fixture_and_write(
                authority,
                self.registry,
                canonical_revision=self.revision,
                adoption_evidence=self.evidence,
            )
            receipt = authority.state_root / result["receipt_path"]
            metadata = receipt.stat()
            self.assertEqual(stat.S_IMODE(metadata.st_mode), 0o600)
            self.assertEqual(metadata.st_uid, os.getuid())
            self.assertEqual(receipt.stem, result["registry_sha256"])
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(payload["validation_mode"], "live_authority_validation")
            self.assertEqual(payload["canonical_revision"], self.revision)

    def test_existing_receipt_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority = self.authority(temporary)
            finalizer.verify_stage2_fixture_and_write(
                authority,
                self.registry,
                canonical_revision=self.revision,
                adoption_evidence=self.evidence,
            )
            with self.assertRaisesRegex(
                finalizer.ActivationFinalizationError, "already exists"
            ):
                finalizer.verify_stage2_fixture_and_write(
                    authority,
                    self.registry,
                    canonical_revision=self.revision,
                    adoption_evidence=self.evidence,
                )

    def test_fixture_authority_and_closed_evidence_are_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority = self.authority(temporary)
            forged = copy.copy(authority)
            object.__setattr__(forged, "mode", "repository_validation")
            with self.assertRaisesRegex(
                finalizer.ActivationFinalizationError, "fixture authority"
            ):
                finalizer.verify_stage2_fixture_and_write(
                    forged,
                    self.registry,
                    canonical_revision=self.revision,
                    adoption_evidence=self.evidence,
                )
            malformed = dict(self.evidence)
            malformed["adopted_by"] = "@someone-else"
            with self.assertRaisesRegex(
                finalizer.ActivationFinalizationError, "not exact"
            ):
                finalizer.verify_stage2_fixture_and_write(
                    authority,
                    self.registry,
                    canonical_revision=self.revision,
                    adoption_evidence=malformed,
                )
            with self.assertRaisesRegex(
                finalizer.ActivationFinalizationError, "revision is invalid"
            ):
                finalizer.verify_stage2_fixture_and_write(
                    authority,
                    self.registry,
                    canonical_revision="not-a-revision",
                    adoption_evidence=self.evidence,
                )

    def test_symlinked_receipt_ancestry_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority = self.authority(temporary)
            outside = Path(temporary) / "outside"
            outside.mkdir(mode=0o700)
            (authority.state_root / "records").symlink_to(
                outside,
                target_is_directory=True,
            )
            with self.assertRaisesRegex(
                finalizer.ActivationFinalizationError, "directory is unsafe"
            ):
                finalizer.verify_stage2_fixture_and_write(
                    authority,
                    self.registry,
                    canonical_revision=self.revision,
                    adoption_evidence=self.evidence,
                )

    def test_partial_write_leaves_no_receipt_or_temporary(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority = self.authority(temporary)
            real_write = os.write
            calls = 0

            def interrupted(descriptor, value):
                nonlocal calls
                calls += 1
                if calls > 1:
                    raise OSError(errno.EIO, "interrupted fixture write")
                return real_write(descriptor, value[:1])

            with patch.object(finalizer.os, "write", side_effect=interrupted):
                with self.assertRaisesRegex(
                    finalizer.ActivationFinalizationError,
                    "temporary write failed",
                ):
                    finalizer.verify_stage2_fixture_and_write(
                        authority,
                        self.registry,
                        canonical_revision=self.revision,
                        adoption_evidence=self.evidence,
                    )
            receipts = authority.state_root / "records" / "governance" / "component-registry" / "activation-readbacks"
            self.assertFalse(receipts.exists() and any(receipts.iterdir()))

    def test_preexisting_hidden_receipt_residue_fails_closed_and_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority = self.authority(temporary)
            receipts = (
                authority.state_root
                / "records"
                / "governance"
                / "component-registry"
                / "activation-readbacks"
            )
            current = authority.state_root
            for part in (
                "records",
                "governance",
                "component-registry",
                "activation-readbacks",
            ):
                current = current / part
                current.mkdir(mode=0o700)
            receipts = current
            residue = receipts / ".interrupted-receipt"
            residue.write_text("preserve for review\n", encoding="utf-8")
            residue.chmod(0o600)
            with self.assertRaisesRegex(
                finalizer.ActivationFinalizationError,
                "unexpected temporary state",
            ):
                finalizer.verify_stage2_fixture_and_write(
                    authority,
                    self.registry,
                    canonical_revision=self.revision,
                    adoption_evidence=self.evidence,
                )
            self.assertEqual(
                residue.read_text(encoding="utf-8"),
                "preserve for review\n",
            )

    def test_receipt_selection_is_digest_bound_and_revision_aware(self):
        stage2 = finalizer._build_stage2_synthetic_receipt(
            self.registry,
            canonical_revision=self.revision,
            adoption_evidence=self.evidence,
        )
        stage1 = {
            "verification_type": "component_registry_activation_readback",
            "registry_sha256": "0" * 64,
        }
        selected = finalizer.select_component_registry_receipt(
            self.registry, [stage1, stage2]
        )
        self.assertEqual(selected["receipt"], stage2)
        with self.assertRaisesRegex(
            finalizer.ActivationFinalizationError, "exactly one"
        ):
            finalizer.select_component_registry_receipt(self.registry, [stage1])

    def test_no_argument_finalizer_uses_stage2_production_path(self):
        legacy_registry = copy.deepcopy(self.registry)
        legacy_registry.pop("authority_digest_model", None)
        receipt = {
            "registry_sha256": finalizer.registry._canonical_registry_digest(
                legacy_registry
            )
        }
        adopted_view = {
            "validation_mode": "adopted_configuration_validation",
            "authoritative": False,
            "executable": False,
        }
        live_view = {
            "validation_mode": "live_authority_validation",
            "authoritative": True,
            "executable": True,
            "live_authority_verified": True,
            "activation_receipt_consulted": True,
        }
        class Authority:
            repository_root = finalizer.registry.ROOT

            def repository_path(self, _path, required=False):
                self.required = required
                return finalizer.registry.DEFAULT_REGISTRY

        authority = Authority()
        with (
            patch.object(finalizer.ProjectPathAuthority, "production", return_value=authority),
            patch.object(finalizer.registry, "_read_json", return_value=legacy_registry),
            patch.object(
                finalizer.registry,
                "load_component_registry_configuration_routing_view",
                return_value=adopted_view,
            ),
            patch.object(
                finalizer,
                "_collect_stage2_authenticated_observations",
                return_value={"fixed": True},
            ) as collect,
            patch.object(
                finalizer,
                "_build_stage2_production_receipt",
                return_value=receipt,
            ) as build,
            patch.object(finalizer, "_write_fixed_receipt") as write,
            patch.object(
                finalizer.registry,
                "load_validated_component_registry_routing_view",
                return_value=live_view,
            ),
        ):
            result = finalizer.finalize_activation()
        self.assertTrue(result["complete"])
        self.assertEqual(result["verification_state"], "live_authority_validation")
        collect.assert_called_once_with(authority)
        build.assert_called_once_with(authority, legacy_registry, {"fixed": True})
        write.assert_called_once_with(authority, receipt)

    def test_authority_v1_receipt_is_distinct_and_crash_idempotent(self):
        digest = "a" * 64
        receipt = {
            "authority_sha256": digest,
            "generation": 1,
            "verification_type": (
                "component_registry_stage2_authority_readback"
            ),
        }
        logical = (
            "records/governance/component-registry/activation-readbacks/"
            f"authority-v1/{digest}.json"
        )
        with tempfile.TemporaryDirectory() as temporary:
            authority = self.authority(temporary)
            with patch.object(
                finalizer.registry,
                "_stage2_authority_readback_logical_path",
                create=True,
                return_value=logical,
            ):
                path, created = finalizer._write_stage2_authority_receipt(
                    authority,
                    receipt,
                )
                repeated_path, repeated_created = (
                    finalizer._write_stage2_authority_receipt(
                        authority,
                        receipt,
                    )
                )
                self.assertTrue(created)
                self.assertFalse(repeated_created)
                self.assertEqual(repeated_path, path)
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
                self.assertIn("authority-v1", path.parts)
                conflicting = dict(receipt, generation=2)
                with self.assertRaisesRegex(
                    finalizer.ActivationFinalizationError,
                    "conflicts",
                ):
                    finalizer._write_stage2_authority_receipt(
                        authority,
                        conflicting,
                    )

    def test_typed_and_untyped_requirement_share_one_receipt_evidence(self):
        reviewed = "a" * 40
        observations = {
            "check_runs": [
                {
                    "id": 41,
                    "name": "Build",
                    "head_sha": reviewed,
                    "status": "completed",
                    "conclusion": "success",
                    "completed_at": "2026-08-01T12:00:00Z",
                    "app": {"id": 7},
                }
            ],
            "check_runs_total_count": 1,
            "check_runs_complete": True,
            "legacy_statuses": [],
            "legacy_statuses_complete": True,
            "required_status_checks": [
                {"context": "Build", "app_id": None},
                {"context": "Build", "app_id": 7},
            ],
            "requirements_complete": True,
        }
        self.assertEqual(
            finalizer._validated_required_check_evidence(
                observations,
                reviewed_head=reviewed,
            ),
            [
                {
                    "evidence_type": "check_run",
                    "context": "Build",
                    "app_id": 7,
                    "run_id": 41,
                    "completed_at": "2026-08-01T12:00:00Z",
                }
            ],
        )

    def test_authority_v1_merge_and_history_are_exact(self):
        repository = Path("/fixture/repository")
        base = "1" * 40
        head = "2" * 40
        merge = "3" * 40
        pull_request = {
            "id": 41,
            "node_id": "PR_node",
            "number": 502,
            "state": "closed",
            "merged": True,
            "merged_at": "2026-08-01T12:02:00Z",
            "merge_commit_sha": merge,
            "auto_merge": None,
            "base": {
                "ref": "main",
                "repo": {"full_name": "Thorncrag/ARRP"},
            },
            "head": {"sha": head},
            "merged_by": {
                "login": "Thorncrag",
                "id": 7,
                "node_id": "USER_node",
            },
        }

        def git_readback(_repository, *arguments):
            if arguments[:3] == ("rev-list", "--parents", "-n"):
                return f"{merge} {base} {head}"
            if arguments[0] == "merge-base":
                return base
            if arguments[0] == "show" and arguments[-1] == merge:
                return "tree-id"
            if arguments[0] == "show" and arguments[-1] == head:
                return "tree-id"
            if arguments[:3] == ("rev-list", "--first-parent", "--reverse"):
                return merge
            self.fail(f"unexpected Git readback: {arguments!r}")

        with patch.object(finalizer, "_git", side_effect=git_readback):
            evidence = finalizer._merge_evidence(
                repository,
                pull_request,
                merge,
            )
            history = finalizer._validate_canonical_pull_request_history(
                repository,
                correction_merge=merge,
                remote_main=merge,
                pull_requests=[pull_request],
            )
        self.assertEqual(evidence["base_revision"], base)
        self.assertEqual(evidence["reviewed_head"], head)
        self.assertEqual(history, [evidence])
        wrong_tree = dict(pull_request)
        with (
            patch.object(
                finalizer,
                "_git",
                side_effect=[
                    f"{merge} {base} {head}",
                    base,
                    "merge-tree",
                    "reviewed-tree",
                ],
            ),
            self.assertRaisesRegex(
                finalizer.ActivationFinalizationError,
                "merge evidence differs",
            ),
        ):
            finalizer._merge_evidence(repository, wrong_tree, merge)

    def test_authority_v1_finalizer_uses_read_only_online_verifier(self):
        authority_digest = finalizer.registry._stage2_authority_digest(
            self.registry
        )
        receipt = {
            "authority_sha256": authority_digest,
            "generation": 1,
            "issuance_revision": "4" * 40,
        }
        configuration_view = {
            "validation_mode": "adopted_configuration_validation",
            "authoritative": False,
            "executable": False,
        }
        online_view = {
            "validation_mode": "online_governed_eligibility",
            "registry_sha256": finalizer.registry._canonical_registry_digest(
                self.registry
            ),
            "authority_sha256": authority_digest,
            "authority_protocol": finalizer.STAGE2_AUTHORITY_PROTOCOL,
            "authority_generation": 1,
            "authoritative": True,
            "executable": False,
            "activation_receipt_consulted": True,
            "runtime_live": "not_checked",
            "authority_effective": True,
            "source_revision_authorized": True,
            "source_bytes_current": True,
            "canonical_history_confirmed": True,
            "receipt_trusted": True,
        }

        class Authority:
            mode = "production_canonical"
            repository_root = finalizer.registry.ROOT

            def repository_path(self, _path, required=False):
                self.required = required
                return finalizer.registry.DEFAULT_REGISTRY

        authority = Authority()
        with (
            patch.object(
                finalizer.ProjectPathAuthority,
                "production",
                return_value=authority,
            ),
            patch.object(
                finalizer.registry,
                "_read_json",
                return_value=self.registry,
            ),
            patch.object(
                finalizer.registry,
                "load_component_registry_configuration_routing_view",
                return_value=configuration_view,
            ),
            patch.object(
                finalizer,
                "_collect_stage2_authority_observations",
                return_value={"fixed": True},
            ) as collect,
            patch.object(
                finalizer,
                "_build_stage2_authority_receipt",
                return_value=receipt,
            ) as build,
            patch.object(
                finalizer,
                "_write_stage2_authority_receipt",
                return_value=(Path("receipt.json"), True),
            ) as write,
            patch.object(
                finalizer,
                "verify_stage2_authority_v1_online_eligibility",
                return_value=online_view,
            ) as verify,
        ):
            result = finalizer.finalize_activation()
        self.assertTrue(result["complete"])
        self.assertTrue(result["created"])
        self.assertEqual(result["runtime_live"], "not_checked")
        collect.assert_called_once_with(authority, self.registry)
        build.assert_called_once_with(authority, self.registry, {"fixed": True})
        write.assert_called_once_with(authority, receipt)
        verify.assert_called_once_with(authority, self.registry)

    def test_authority_v1_correction_digest_is_not_current_full_digest(self):
        correction = copy.deepcopy(self.registry)
        current = copy.deepcopy(correction)
        current["validation"]["repository_base_revision"] = "f" * 40
        correction_full_digest = (
            finalizer.registry._canonical_registry_digest(correction)
        )
        current_full_digest = finalizer.registry._canonical_registry_digest(
            current
        )
        authority_digest = finalizer.registry._stage2_authority_digest(
            current
        )
        self.assertNotEqual(correction_full_digest, current_full_digest)
        self.assertEqual(
            finalizer.registry._stage2_authority_digest(correction),
            authority_digest,
        )
        model = finalizer._stage2_authority_model(current)
        finalizer._validate_stage2_correction_registry_binding(
            correction,
            {"correction_registry_sha256": correction_full_digest},
            current_authority_digest=authority_digest,
            current_model=model,
        )
        with self.assertRaisesRegex(
            finalizer.ActivationFinalizationError,
            "binding differs",
        ):
            finalizer._validate_stage2_correction_registry_binding(
                correction,
                {"correction_registry_sha256": current_full_digest},
                current_authority_digest=authority_digest,
                current_model=model,
            )

    def test_online_verifier_rejects_nonproduction_authority_before_io(self):
        with tempfile.TemporaryDirectory() as temporary:
            authority = self.authority(temporary)
            with self.assertRaisesRegex(
                finalizer.ActivationFinalizationError,
                "fixed production authority",
            ):
                finalizer.verify_stage2_authority_v1_online_eligibility(
                    authority,
                    self.registry,
                )

    def test_classic_branch_protection_supplies_closed_history_rules(self):
        protection = {
            "required_status_checks": {"strict": True},
            "required_pull_request_reviews": {"required_approving_review_count": 0},
            "allow_force_pushes": {"enabled": False},
            "allow_deletions": {"enabled": False},
            "enforce_admins": {"enabled": True},
        }
        with patch.object(finalizer, "_run_json", return_value=protection):
            posture = finalizer._collect_classic_main_protection()
        self.assertEqual(
            posture["rule_types"],
            [
                "deletion",
                "non_fast_forward",
                "pull_request",
                "required_status_checks",
            ],
        )
        self.assertFalse(posture["bypass_permitted"])
        protection["enforce_admins"] = {"enabled": False}
        with patch.object(finalizer, "_run_json", return_value=protection):
            posture = finalizer._collect_classic_main_protection()
        self.assertTrue(posture["bypass_permitted"])

    def test_stage2_production_receipt_binds_exact_pr_merge_and_checks(self):
        class Authority:
            mode = "production_canonical"
            repository_root = finalizer.registry.ROOT

        base = "1" * 40
        reviewed = "2" * 40
        merge = "3" * 40
        observations = {
            "repository": "Thorncrag/ARRP",
            "default_branch": "main",
            "pull_request_number": 501,
            "pull_request_state": "closed",
            "pull_request_merged": True,
            "pull_request_auto_merge": None,
            "merged_by": "Thorncrag",
            "pull_request_base_repository": "Thorncrag/ARRP",
            "pull_request_base_branch": "main",
            "pull_request_base_revision": base,
            "reviewed_head_revision": reviewed,
            "merge_commit_sha": merge,
            "merged_at": "2026-08-01T12:02:00Z",
            "check_runs": [
                {
                    "name": "ARRP Validation",
                    "head_sha": reviewed,
                    "status": "completed",
                    "conclusion": "success",
                    "completed_at": "2026-08-01T12:01:00Z",
                    "app": {"id": 1},
                }
            ],
            "check_runs_total_count": 1,
            "check_runs_complete": True,
            "legacy_statuses": [],
            "legacy_statuses_complete": True,
            "required_status_checks": [
                {"context": "ARRP Validation", "app_id": 1}
            ],
            "requirements_complete": True,
            "remote_main_revision": merge,
            "reviewed_registry": self.registry,
            "remote_registry": self.registry,
            "local_revision": merge,
            "origin_main_revision": merge,
            "verified_at": "2026-08-01T12:03:00Z",
        }
        with (
            patch.object(finalizer.registry, "validate_stage2_registry"),
            patch.object(
                finalizer,
                "_git",
                return_value=f"{merge} {base} {reviewed}",
            ),
        ):
            receipt = finalizer._build_stage2_production_receipt(
                Authority(),
                self.registry,
                observations,
            )
        self.assertEqual(receipt["canonical_revision"], merge)
        self.assertEqual(receipt["adoption_evidence"]["base_revision"], base)
        self.assertEqual(
            receipt["adoption_evidence"]["pull_request"],
            "github-review:Thorncrag/ARRP#501",
        )
        wrong = dict(observations)
        wrong["pull_request_number"] = 502
        with (
            patch.object(finalizer.registry, "validate_stage2_registry"),
            self.assertRaisesRegex(
                finalizer.ActivationFinalizationError,
                "identity differs",
            ),
        ):
            finalizer._build_stage2_production_receipt(
                Authority(),
                self.registry,
                wrong,
            )


if __name__ == "__main__":
    unittest.main()
