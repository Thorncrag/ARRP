"""Fixture-only tests for the fixed Component Registry activation finalizer."""

from __future__ import annotations

import copy
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


class ComponentRegistryActivationFinalizerTests(unittest.TestCase):
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
            "pull_request_base_repository": "Thorncrag/ARRP",
            "pull_request_base_branch": "main",
            "pull_request_base_revision": pull_request_base,
            "reviewed_head_revision": reviewed_head,
            "merge_commit_sha": remote_main,
            "merged_at": "2026-07-30T00:02:00-04:00",
            "reviews": [
                {
                    "id": 456789,
                    "state": "APPROVED",
                    "user": {"login": "Thorncrag"},
                    "commit_id": reviewed_head,
                    "submitted_at": "2026-07-30T00:01:00-04:00",
                }
            ],
            "reviews_complete": True,
            "check_runs": [
                {
                    "name": "ARRP validation",
                    "head_sha": reviewed_head,
                    "status": "completed",
                    "conclusion": "success",
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

    def test_wrong_identity_review_checks_and_remote_registry_fail(self):
        mutations = [
            ("repository", "Other/Repository"),
            ("pull_request_number", 124),
            ("pull_request_merged", False),
            ("reviews", []),
            (
                "check_runs",
                [
                    {
                        "name": "ARRP validation",
                        "head_sha": "0" * 40,
                        "status": "completed",
                        "conclusion": "success",
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

    def test_latest_decisive_exact_head_owner_review_governs(self):
        mutations = (
            {
                "id": 999,
                "state": "CHANGES_REQUESTED",
                "user": {"login": "Thorncrag"},
                "commit_id": None,
                "submitted_at": "2026-07-30T00:01:30-04:00",
            },
            {
                "id": 999,
                "state": "DISMISSED",
                "user": {"login": "Thorncrag"},
                "commit_id": None,
                "submitted_at": "2026-07-30T00:01:30-04:00",
            },
        )
        for later in mutations:
            with self.subTest(state=later["state"]), tempfile.TemporaryDirectory() as temporary:
                authority, active, observations = self.fixture(temporary)
                later["commit_id"] = observations["reviewed_head_revision"]
                observations["reviews"].append(later)
                with self.assertRaises(
                    finalizer.ActivationFinalizationError
                ):
                    finalizer._build_receipt(
                        authority,
                        active,
                        observations,
                    )
        with tempfile.TemporaryDirectory() as temporary:
            authority, active, observations = self.fixture(temporary)
            observations["reviews"][0]["id"] = 0
            with self.assertRaises(finalizer.ActivationFinalizationError):
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


if __name__ == "__main__":
    unittest.main()
