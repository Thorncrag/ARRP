from __future__ import annotations

import copy
import hashlib
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
    "github_disclosure_gate",
    ROOT / "scripts/github_disclosure_gate.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class GitHubDisclosureGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = MODULE.load_policy()
        self.revision = "a" * 40
        self.control_pack = {
            "schema_version": 1,
            "pack_id": "test-control-pack",
            "policy_id": self.policy["policy_id"],
            "control_version": "2026-07-28.1",
            "status": "active",
            "complete": True,
            "restricted_detectors": [
                {
                    "id": "generic-owner-local-control",
                    "pattern": r"OWNER[- ]LOCAL[- ]CONTROL[- ]CANARY",
                }
            ],
            "restricted_path_patterns": ["restricted-local/**"],
        }
        self.original_load_control_pack = MODULE.load_control_pack
        self.original_activate_candidate_control_pack = (
            MODULE.activate_candidate_control_pack
        )
        loader = mock.patch.object(
            MODULE,
            "load_control_pack",
            return_value=self.control_pack,
        )
        loader.start()
        self.addCleanup(loader.stop)

    def artifact(self, path: str, content: str, **kwargs):
        return MODULE.artifact_from_text(
            path,
            kwargs.pop("producer", "arrp-nightly-publication"),
            content,
            **kwargs,
        )

    def git_fixture(self) -> tuple[tempfile.TemporaryDirectory, Path, str, str]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repository = Path(temporary.name)
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=repository,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "ARRP Fixture"],
            cwd=repository,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "fixture@example.invalid"],
            cwd=repository,
            check=True,
        )
        path = repository / "areas" / "CONGRESS" / "issues" / "CON-001.md"
        path.parent.mkdir(parents=True)
        path.write_text("# Base\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repository, check=True)
        subprocess.run(
            ["git", "commit", "-m", "base"],
            cwd=repository,
            check=True,
            capture_output=True,
        )
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        path.write_text("# Head\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repository, check=True)
        subprocess.run(
            ["git", "commit", "-m", "head"],
            cwd=repository,
            check=True,
            capture_output=True,
        )
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return temporary, repository, base, head

    def git_report_fixture(
        self, path: str, *, registered: bool
    ) -> tuple[tempfile.TemporaryDirectory, Path, str, str]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repository = Path(temporary.name)
        subprocess.run(["git", "init", "-b", "main"], cwd=repository, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "ARRP Fixture"], cwd=repository, check=True)
        subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repository, check=True)
        entries = {}
        if registered:
            entries["fixture_public_report"] = {
                "display_name": "Fixture public report",
                "classification": {"component_class": "document", "component_type": "report"},
                "canonical_source": path,
                "information_handling": {
                    "information_classification": "public_by_design",
                    "disclosure_rule": "public-project-report",
                },
            }
        registry = {
            "schema_version": 4,
            "registry_revision": 6,
            "components": {"entries": entries},
        }
        registry_path = repository / "framework" / "component-registry.json"
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(json.dumps(registry), encoding="utf-8")
        base_path = repository / "areas" / "base.md"
        base_path.parent.mkdir(parents=True)
        base_path.write_text("# Base\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repository, check=True)
        subprocess.run(["git", "commit", "-m", "base"], cwd=repository, check=True, capture_output=True)
        base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository, check=True, capture_output=True, text=True).stdout.strip()
        report = repository / path
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("# Report\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repository, check=True)
        subprocess.run(["git", "commit", "-m", "report"], cwd=repository, check=True, capture_output=True)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository, check=True, capture_output=True, text=True).stdout.strip()
        return temporary, repository, base, head

    def git_remote_fixture(
        self,
    ) -> tuple[
        tempfile.TemporaryDirectory,
        MODULE.ProjectPathAuthority,
        Path,
        str,
        str,
        Path,
    ]:
        temporary, repository, base, head = self.git_fixture()
        state = Path(temporary.name) / "state"
        state.mkdir()
        remote_temporary = tempfile.TemporaryDirectory()
        self.addCleanup(remote_temporary.cleanup)
        remote = Path(remote_temporary.name) / "remote.git"
        subprocess.run(
            ["git", "init", "--bare", remote],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "remote", "add", "origin", str(remote)],
            cwd=repository,
            check=True,
        )
        subprocess.run(
            ["git", "push", "origin", f"{head}:refs/heads/fixture"],
            cwd=repository,
            check=True,
            capture_output=True,
        )
        authority = MODULE.ProjectPathAuthority.fixture(
            Path(temporary.name),
            repository_root=repository,
            state_root=state,
        )
        return temporary, authority, repository, base, head, remote

    def test_git_push_authorization_binds_exact_committed_range(self) -> None:
        _, repository, base, head = self.git_fixture()
        decision = MODULE.authorize_git_push(
            repository,
            base_revision=base,
            source_revision=head,
            head_ref="HEAD",
            target_ref="refs/heads/fixture",
            producer="interactive-reviewed-github",
            policy=self.policy,
        )
        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["source_revision"], head)
        self.assertEqual(
            decision["authorized_refspec"],
            f"{head}:refs/heads/fixture",
        )
        self.assertRegex(
            decision["manifest_sha256"],
            r"^sha256:[0-9a-f]{64}$",
        )

    def test_git_push_rejects_fabricated_abbreviated_and_wrong_head(self) -> None:
        _, repository, base, head = self.git_fixture()
        for revision in ("f" * 40, head[:12], base):
            with self.subTest(revision=revision):
                with self.assertRaises(MODULE.DisclosureBlocked):
                    MODULE.authorize_git_push(
                        repository,
                        base_revision=base,
                        source_revision=revision,
                        head_ref="HEAD",
                        target_ref="refs/heads/fixture",
                        producer="interactive-reviewed-github",
                        policy=self.policy,
                    )

    def test_git_push_reads_commit_blobs_not_dirty_worktree(self) -> None:
        _, repository, base, head = self.git_fixture()
        path = repository / "areas" / "CONGRESS" / "issues" / "CON-001.md"
        path.write_text("OWNER-LOCAL-CONTROL-CANARY\n", encoding="utf-8")
        decision = MODULE.authorize_git_push(
            repository,
            base_revision=base,
            source_revision=head,
            head_ref="HEAD",
            target_ref="refs/heads/fixture",
            producer="interactive-reviewed-github",
            policy=self.policy,
        )
        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["artifacts"][0]["category"], "public_by_design")

    def test_git_push_manifest_includes_removals(self) -> None:
        _, repository, _, head = self.git_fixture()
        base = head
        subprocess.run(
            [
                "git",
                "update-index",
                "--force-remove",
                "areas/CONGRESS/issues/CON-001.md",
            ],
            cwd=repository,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "remove"],
            cwd=repository,
            check=True,
            capture_output=True,
        )
        removed_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        decision = MODULE.authorize_git_push(
            repository,
            base_revision=base,
            source_revision=removed_head,
            head_ref="HEAD",
            target_ref="refs/heads/fixture",
            producer="interactive-reviewed-github",
            policy=self.policy,
        )
        self.assertTrue(decision["allowed"])
        self.assertTrue(decision["artifacts"][0]["removal_only"])

    def test_exact_commit_report_publication_requires_registry_admission(self) -> None:
        path = "framework/reports/fixtures/public-review.md"
        _, repository, base, head = self.git_report_fixture(path, registered=True)
        decision = MODULE.authorize_git_push(
            repository,
            base_revision=base,
            source_revision=head,
            head_ref="HEAD",
            target_ref="refs/heads/fixture",
            producer="interactive-reviewed-github",
            policy=self.policy,
        )
        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["artifacts"][0]["artifact_family"], "public-project-report")

    def test_exact_commit_report_publication_blocks_unadmitted_paths(self) -> None:
        cases = (
            ("framework/reports/fixtures/unregistered-review.md", False, "unregistered-public-project-report"),
            ("framework/internal/repair-postmortem.md", False, "report-outside-public-project-scope"),
            ("notes/unknown-audit.md", False, "report-outside-public-project-scope"),
        )
        for path, registered, detector in cases:
            with self.subTest(path=path):
                _, repository, base, head = self.git_report_fixture(path, registered=registered)
                with self.assertRaises(MODULE.DisclosureBlocked) as caught:
                    MODULE.authorize_git_push(
                        repository,
                        base_revision=base,
                        source_revision=head,
                        head_ref="HEAD",
                        target_ref="refs/heads/fixture",
                        producer="interactive-reviewed-github",
                        policy=self.policy,
                    )
                self.assertEqual(caught.exception.decision["findings"][0]["detector_class"], detector)

    def test_git_push_ref_movement_invalidates_stale_authorization_input(self) -> None:
        _, repository, base, head = self.git_fixture()
        first = MODULE.authorize_git_push(
            repository,
            base_revision=base,
            source_revision=head,
            head_ref="HEAD",
            target_ref="refs/heads/fixture",
            producer="interactive-reviewed-github",
            policy=self.policy,
        )
        path = repository / "areas" / "CONGRESS" / "issues" / "CON-001.md"
        path.write_text("# Later\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repository, check=True)
        subprocess.run(
            ["git", "commit", "-m", "later"],
            cwd=repository,
            check=True,
            capture_output=True,
        )
        self.assertEqual(
            first["authorized_refspec"],
            f"{head}:refs/heads/fixture",
        )
        with self.assertRaises(MODULE.DisclosureBlocked):
            MODULE.authorize_git_push(
                repository,
                base_revision=base,
                source_revision=head,
                head_ref="HEAD",
                target_ref="refs/heads/fixture",
                producer="interactive-reviewed-github",
                policy=self.policy,
            )

    def test_branch_ref_delete_authorization_is_exact_and_deterministic(self) -> None:
        _, authority, _, _, head, _ = self.git_remote_fixture()
        first = MODULE.authorize_git_branch_ref_delete(
            authority,
            source_revision=head,
            target_ref="refs/heads/fixture",
            producer="interactive-reviewed-github",
            policy=self.policy,
        )
        second = MODULE.authorize_git_branch_ref_delete(
            authority,
            source_revision=head,
            target_ref="refs/heads/fixture",
            producer="interactive-reviewed-github",
            policy=self.policy,
        )
        self.assertTrue(first["allowed"])
        self.assertTrue(first["authoritative"])
        self.assertEqual(first["operation"], "git_branch_ref_delete")
        self.assertEqual(
            first["artifacts"][0]["artifact_family"],
            "github-branch-ref-delete-control",
        )
        self.assertEqual(first["source_revision"], head)
        self.assertEqual(first["authorized_remote"], "origin")
        self.assertEqual(
            first["authorized_refspec"],
            ":refs/heads/fixture",
        )
        self.assertEqual(
            first["authorized_lease"],
            f"refs/heads/fixture:{head}",
        )
        self.assertEqual(first["new_oid"], "0" * 40)
        self.assertEqual(first["payload_sha256"], second["payload_sha256"])

    def test_branch_ref_delete_executes_with_lease_and_reads_back_absence(self) -> None:
        _, authority, repository, _, head, _ = self.git_remote_fixture()
        decision = MODULE.authorize_git_branch_ref_delete(
            authority,
            source_revision=head,
            target_ref="refs/heads/fixture",
            producer="interactive-reviewed-github",
            policy=self.policy,
        )
        MODULE.execute_authorized_git_branch_ref_delete(
            authority,
            decision,
            policy=self.policy,
        )
        observed = subprocess.run(
            [
                "git",
                "ls-remote",
                "--refs",
                "origin",
                "refs/heads/fixture",
            ],
            cwd=repository,
            check=True,
            capture_output=True,
        ).stdout
        self.assertEqual(observed, b"")

    def test_branch_ref_delete_lease_preserves_a_moved_remote_head(self) -> None:
        _, authority, repository, _, head, _ = self.git_remote_fixture()
        decision = MODULE.authorize_git_branch_ref_delete(
            authority,
            source_revision=head,
            target_ref="refs/heads/fixture",
            producer="interactive-reviewed-github",
            policy=self.policy,
        )
        path = repository / "areas" / "CONGRESS" / "issues" / "CON-001.md"
        path.write_text("# Moved\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repository, check=True)
        subprocess.run(
            ["git", "commit", "-m", "move fixture"],
            cwd=repository,
            check=True,
            capture_output=True,
        )
        moved = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "push", "origin", "HEAD:refs/heads/fixture"],
            cwd=repository,
            check=True,
            capture_output=True,
        )
        with self.assertRaises(MODULE.DisclosureBlocked):
            MODULE.execute_authorized_git_branch_ref_delete(
                authority,
                decision,
                policy=self.policy,
            )
        observed = subprocess.run(
            [
                "git",
                "ls-remote",
                "--refs",
                "origin",
                "refs/heads/fixture",
            ],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()[0]
        self.assertEqual(observed, moved)

    def test_branch_ref_delete_rejects_a_fabricated_decision(self) -> None:
        _, authority, repository, _, head, _ = self.git_remote_fixture()
        fabricated = {
            "allowed": True,
            "authoritative": True,
            "operation": "git_branch_ref_delete",
            "repository": "Thorncrag/ARRP",
            "authority_mode": "fixture",
            "authorized_remote": "origin",
            "target_ref": "refs/heads/fixture",
            "expected_old_oid": head,
            "source_revision": head,
            "new_oid": "0" * 40,
            "payload_sha256": MODULE._branch_ref_delete_payload(
                target_ref="refs/heads/fixture",
                expected_old_oid=head,
            )[1],
            "authorized_refspec": ":refs/heads/fixture",
            "authorized_lease": f"refs/heads/fixture:{head}",
        }
        fabricated["payload_sha256"] = (
            "sha256:"
            + hashlib.sha256(fabricated["payload_sha256"]).hexdigest()
        )
        with self.assertRaises(MODULE.DisclosureBlocked):
            MODULE.execute_authorized_git_branch_ref_delete(
                authority,
                fabricated,
                policy=self.policy,
            )
        observed = subprocess.run(
            [
                "git",
                "ls-remote",
                "--refs",
                "origin",
                "refs/heads/fixture",
            ],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()[0]
        self.assertEqual(observed, head)

    def test_branch_ref_delete_rejects_invalid_or_substituted_inputs(self) -> None:
        _, authority, _, _, head, _ = self.git_remote_fixture()
        sensitive_marker = "SENSITIVE" + "-MARKER"
        invalid = (
            "refs/heads/main",
            "refs/tags/fixture",
            "refs/heads/*",
            "refs/heads/fixture..other",
            f"refs/heads/{sensitive_marker}",
        )
        for target_ref in invalid:
            with self.subTest(target_ref=target_ref):
                with self.assertRaises(MODULE.DisclosureBlocked) as raised:
                    MODULE.authorize_git_branch_ref_delete(
                        authority,
                        source_revision=head,
                        target_ref=target_ref,
                        producer="interactive-reviewed-github",
                        policy=self.policy,
                    )
                self.assertNotIn(sensitive_marker, str(raised.exception))
                self.assertNotIn(
                    sensitive_marker,
                    json.dumps(raised.exception.decision),
                )
        for source_revision in (head[:12], "f" * 40):
            with self.subTest(source_revision=source_revision):
                with self.assertRaises(MODULE.DisclosureBlocked):
                    MODULE.authorize_git_branch_ref_delete(
                        authority,
                        source_revision=source_revision,
                        target_ref="refs/heads/fixture",
                        producer="interactive-reviewed-github",
                        policy=self.policy,
                    )
        with self.assertRaises(MODULE.DisclosureBlocked):
            MODULE.authorize_git_branch_ref_delete(
                authority,
                source_revision=head,
                target_ref="refs/heads/fixture",
                producer="arrp-semantic-broker",
                policy=self.policy,
            )
        with self.assertRaises(MODULE.DisclosureBlocked):
            MODULE.authorize_git_branch_ref_delete(
                authority,
                source_revision=head,
                target_ref="refs/heads/missing",
                producer="interactive-reviewed-github",
                policy=self.policy,
            )

    def test_branch_ref_delete_rejects_substituted_production_authority(self) -> None:
        _, authority, repository, _, head, _ = self.git_remote_fixture()
        substituted = MODULE.ProjectPathAuthority(
            mode="production_canonical",
            repository_root=repository,
            state_root=authority.state_root,
            output_root=repository,
        )
        with self.assertRaises(MODULE.DisclosureBlocked):
            MODULE.authorize_git_branch_ref_delete(
                substituted,
                source_revision=head,
                target_ref="refs/heads/fixture",
                producer="interactive-reviewed-github",
            )
        with self.assertRaises(MODULE.DisclosureBlocked):
            MODULE.authorize_git_branch_ref_delete(
                authority,
                source_revision=head,
                target_ref="refs/heads/fixture",
                producer="interactive-reviewed-github",
            )

    def test_branch_ref_delete_does_not_widen_generic_control_payloads(self) -> None:
        with self.assertRaises(MODULE.DisclosureBlocked) as raised:
            MODULE.evaluate_outbound_bundle(
                [
                    MODULE.OutboundArtifact(
                        path="github/control/arbitrary",
                        producer="interactive-reviewed-github",
                        content=b"{}",
                    )
                ],
                operation="git_branch_ref_delete",
                source_revision=self.revision,
                policy=self.policy,
            )
        self.assertFalse(raised.exception.decision["allowed"])

    def test_git_push_empty_range_and_app_delete_refspec_remain_blocked(self) -> None:
        _, repository, _, head = self.git_fixture()
        with self.assertRaises(MODULE.DisclosureBlocked):
            MODULE.authorize_git_push(
                repository,
                base_revision=head,
                source_revision=head,
                head_ref="HEAD",
                target_ref="refs/heads/fixture",
                producer="interactive-reviewed-github",
                policy=self.policy,
            )
        from scripts import arrp_nightly

        with self.assertRaises(arrp_nightly.GitHubBrokerError):
            arrp_nightly.git_push_with_token(
                repository,
                ":refs/heads/fixture",
                arrp_nightly.SensitiveValue("fixture-token"),
                disclosure_decision={
                    "allowed": True,
                    "authoritative": True,
                    "operation": "git_branch_ref_delete",
                    "source_revision": head,
                },
            )

    def test_known_public_family_passes_without_per_file_label(self) -> None:
        decision = MODULE.evaluate_outbound_bundle(
            [self.artifact("areas/CONGRESS/issues/CON-001.md", "# Public proposal")],
            operation="git_push",
            source_revision=self.revision,
            policy=self.policy,
        )
        self.assertTrue(decision["allowed"])
        self.assertEqual(
            decision["artifacts"][0]["artifact_family"],
            "public-research-and-proposals",
        )

    def test_public_project_proposal_scope_is_explicitly_classified(self) -> None:
        family = MODULE._resolve_family(
            self.policy,
            path="framework/proposals/component-registry-stage2-design.md",
            producer="interactive-reviewed-github",
            requested_family=None,
        )
        self.assertEqual(family["id"], "public-research-and-proposals")
        self.assertEqual(family["category"], "public_by_design")

    def test_component_registry_archive_targets_have_exact_public_families(
        self,
    ) -> None:
        expected = {
            "framework/archive/authorities/AGENT_BOT_REGISTRY.md":
                "portable-automation-and-controls",
            "framework/archive/authorities/PROJECT_STRUCTURE.md":
                "public-governance-summary",
            "framework/archive/authorities/REPOSITORY_MAP.md":
                "public-governance-summary",
            "framework/archive/authorities/CONTEXT_ROUTING.md":
                "portable-automation-and-controls",
            "framework/archive/authorities/context-routes.json":
                "portable-automation-and-controls",
        }
        for path, family_id in expected.items():
            with self.subTest(path=path):
                family = MODULE._resolve_family(
                    self.policy,
                    path=path,
                    producer="interactive-reviewed-github",
                    requested_family=None,
                )
                self.assertEqual(family["id"], family_id)

    def test_current_repository_files_map_once_and_contain_no_secret_canary(self) -> None:
        paths = [
            item
            for item in subprocess.run(
                ["git", "ls-files", "-co", "--exclude-standard", "-z"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            ).stdout.decode("utf-8").split("\0")
            if item
        ]
        secret_findings = []
        for relative in paths:
            path = ROOT / relative
            if not path.is_file():
                continue
            family = MODULE._resolve_family(
                self.policy,
                path=relative,
                producer="interactive-reviewed-github",
                requested_family=None,
            )
            secret_findings.extend(
                finding
                for finding in MODULE._content_findings(
                    relative,
                    str(family["id"]),
                    path.read_bytes(),
                    control_pack=self.control_pack,
                )
                if finding["category"] == "prohibited_secret"
            )
        self.assertEqual(secret_findings, [])

    def test_restricted_operational_spec_in_public_directory_is_blocked(self) -> None:
        decision = MODULE.evaluate_outbound_bundle(
            [
                self.artifact(
                    "areas/CONGRESS/issues/CON-001.md",
                    "OWNER-LOCAL-CONTROL-CANARY",
                )
            ],
            operation="git_push",
            source_revision=self.revision,
            policy=self.policy,
        )
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["category"], "restricted_operational")
        self.assertIn(
            "generic-owner-local-control",
            {item["detector_class"] for item in decision["findings"]},
        )

    def test_unknown_family_fails_closed(self) -> None:
        with self.assertRaises(MODULE.DisclosureBlocked) as caught:
            MODULE.evaluate_outbound_bundle(
                [self.artifact("new-family/output.md", "ordinary text")],
                operation="git_push",
                source_revision=self.revision,
                policy=self.policy,
            )
        self.assertIn("unknown-artifact-family", str(caught.exception))

    def test_exceptional_override_is_exact_revision_bound(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["artifact_families"].append(
            {
                "id": "fixture-restricted-override",
                "category": "restricted_operational",
                "producers": ["arrp-nightly-publication"],
                "paths": ["fixture/reviewed-summary.py"],
            }
        )
        policy["exceptional_overrides"] = [
            {
                "path": "fixture/reviewed-summary.py",
                "artifact_family": "fixture-restricted-override",
                "reviewed_revision": self.revision,
                "category": "public_operational_summary",
            }
        ]
        artifact = self.artifact("fixture/reviewed-summary.py", "print('safe summary')")
        allowed = MODULE.evaluate_outbound_bundle(
            [artifact],
            operation="git_push",
            source_revision=self.revision,
            policy=policy,
        )
        stale = MODULE.evaluate_outbound_bundle(
            [artifact],
            operation="git_push",
            source_revision="b" * 40,
            policy=policy,
        )
        self.assertTrue(allowed["allowed"])
        self.assertFalse(stale["allowed"])

    def test_generated_family_inherits_strictest_member_and_aggregation(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["artifact_families"].extend(
            [
                {
                    "id": "fixture-public-generator",
                    "category": "public_by_design",
                    "producers": ["fixture-builder"],
                    "paths": ["fixture/generator.py", "fixture/output.pdf"],
                },
                {
                    "id": "fixture-restricted-test",
                    "category": "restricted_operational",
                    "producers": ["fixture-builder"],
                    "paths": ["fixture/test_generator.py"],
                },
            ]
        )
        artifacts = [
            MODULE.OutboundArtifact(
                "fixture/generator.py",
                "fixture-builder",
                b"safe generator",
                artifact_group="generated-document-family",
            ),
            MODULE.OutboundArtifact(
                "fixture/output.pdf",
                "fixture-builder",
                b"%PDF-safe fixture",
                artifact_group="generated-document-family",
            ),
            MODULE.OutboundArtifact(
                "fixture/test_generator.py",
                "fixture-builder",
                b"content-bearing restricted fixture",
                artifact_group="generated-document-family",
            ),
        ]
        decision = MODULE.evaluate_outbound_bundle(
            artifacts,
            operation="release_asset",
            source_revision=self.revision,
            policy=policy,
        )
        self.assertFalse(decision["allowed"])
        self.assertTrue(
            all(
                item["category"] == "restricted_operational"
                for item in decision["artifacts"]
            )
        )

    def test_secret_canaries_never_appear_in_safe_result_or_exception(self) -> None:
        canary = "github_pat_" + "A" * 32
        artifact = self.artifact(
            "README.md",
            "Authorization" + ": " + "Bearer " + canary,
        )
        decision = MODULE.evaluate_outbound_bundle(
            [artifact],
            operation="git_push",
            source_revision=self.revision,
            policy=self.policy,
        )
        rendered = json.dumps(decision)
        self.assertFalse(decision["allowed"])
        self.assertNotIn(canary, rendered)
        with self.assertRaises(MODULE.DisclosureBlocked) as caught:
            MODULE.require_outbound_bundle(
                [artifact],
                operation="git_push",
                source_revision=self.revision,
                policy=self.policy,
            )
        self.assertNotIn(canary, str(caught.exception))

    def test_signed_url_and_raw_credential_error_are_blocked_without_echo(self) -> None:
        signed = (
            "https://example.test/file?"
            + "token="
            + "TOPSECRET123456"
        )
        decision = MODULE.evaluate_outbound_bundle(
            [self.artifact("README.md", f"request failed at {signed}")],
            operation="issue_body",
            source_revision=self.revision,
            policy=self.policy,
        )
        self.assertFalse(decision["allowed"])
        self.assertNotIn("TOPSECRET", json.dumps(decision))

    def test_issue_discussion_and_project_text_use_the_same_gate(self) -> None:
        rows = [
            MODULE.artifact_from_text(
                "github/issue/12/body",
                "arrp-semantic-broker",
                "Public issue wrapper",
            ),
            MODULE.artifact_from_text(
                "github/discussion/12/reply",
                "arrp-semantic-broker",
                "Public discussion reply",
            ),
            MODULE.artifact_from_text(
                "github/project-field/2/value",
                "arrp-semantic-broker",
                "Development",
            ),
        ]
        decision = MODULE.evaluate_outbound_bundle(
            rows,
            operation="github_api_mutation",
            source_revision=self.revision,
            policy=self.policy,
        )
        self.assertTrue(decision["allowed"])

    def test_private_repository_label_does_not_allow_secret(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["artifact_families"].append(
            {
                "id": "private-repository-text",
                "category": "private",
                "producers": ["fixture"],
                "paths": ["github/private/**"],
            }
        )
        decision = MODULE.evaluate_outbound_bundle(
            [
                MODULE.artifact_from_text(
                    "github/private/issue",
                    "fixture",
                    "password" + "=" + "SECRET123456",
                )
            ],
            operation="github_api_mutation",
            source_revision=self.revision,
            policy=policy,
        )
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["category"], "prohibited_secret")

    def test_incomplete_evidence_cannot_pass(self) -> None:
        decision = MODULE.evaluate_outbound_bundle(
            [self.artifact("README.md", "Public summary")],
            operation="git_push",
            source_revision=self.revision,
            policy=self.policy,
            complete=False,
        )
        self.assertFalse(decision["allowed"])
        self.assertFalse(decision["complete"])

    def test_blocked_artifact_is_preserved_locally(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "artifact.md"
            path.write_text(
                "password" + "=" + "SECRET123456",
                encoding="utf-8",
            )
            decision = MODULE.evaluate_outbound_bundle(
                [self.artifact("README.md", path.read_text(encoding="utf-8"))],
                operation="git_push",
                source_revision=self.revision,
                policy=self.policy,
            )
            self.assertFalse(decision["allowed"])
            self.assertTrue(path.is_file())

    def test_removal_of_nonpublic_artifact_transmits_no_content_and_is_allowed(self) -> None:
        decision = MODULE.evaluate_outbound_bundle(
            [
                MODULE.OutboundArtifact(
                    path="scripts/retired_internal_tool.py",
                    producer="arrp-nightly-publication",
                    content=b"",
                    removal_only=True,
                )
            ],
            operation="git_push",
            source_revision=self.revision,
            policy=self.policy,
        )
        self.assertTrue(decision["allowed"])
        self.assertTrue(decision["artifacts"][0]["removal_only"])

        with_content = MODULE.evaluate_outbound_bundle(
            [
                MODULE.OutboundArtifact(
                    path="scripts/retired_internal_tool.py",
                    producer="arrp-nightly-publication",
                    content=b"not actually removed",
                    removal_only=True,
                )
            ],
            operation="git_push",
            source_revision=self.revision,
            policy=self.policy,
        )
        self.assertFalse(with_content["allowed"])

    def test_empty_environment_template_is_public_but_live_environment_is_not(self) -> None:
        template = MODULE.evaluate_outbound_bundle(
            [
                self.artifact(
                    "participate/.env.example",
                    "ARRP_INTAKE_MODE=\n",
                    producer="interactive-reviewed-github",
                )
            ],
            operation="git_push",
            source_revision=self.revision,
            policy=self.policy,
        )
        live = MODULE.evaluate_outbound_bundle(
            [
                self.artifact(
                    "participate/.env.local",
                    "ARRP_INTAKE_MODE=live\n",
                    producer="interactive-reviewed-github",
                )
            ],
            operation="git_push",
            source_revision=self.revision,
            policy=self.policy,
        )
        self.assertTrue(template["allowed"])
        self.assertEqual(
            template["artifacts"][0]["artifact_family"],
            "public-empty-environment-template",
        )
        self.assertFalse(live["allowed"])
        self.assertEqual(live["category"], "private")

    def test_governance_supplement_is_private_while_public_log_and_registry_are_permitted(self) -> None:
        public = MODULE.evaluate_outbound_bundle(
            [
                self.artifact(
                    "framework/logs/governance/governance-change-log.md",
                    "# Public governance change log\n",
                    producer="interactive-reviewed-github",
                ),
                self.artifact(
                    "framework/project/workflows/governance-change-registry.json",
                    '{"schema_version":1}\n',
                    producer="interactive-reviewed-github",
                ),
            ],
            operation="git_push",
            source_revision=self.revision,
            policy=self.policy,
        )
        self.assertTrue(public["allowed"])
        self.assertEqual(
            {
                item["artifact_family"] for item in public["artifacts"]
            },
            {"public-governance-summary", "public-methodology"},
        )

        supplement = MODULE.evaluate_outbound_bundle(
            [
                self.artifact(
                    "owner-local/records/governance/governance-change-supplements.jsonl",
                    '{"schema_version":1}\n',
                    producer="interactive-reviewed-github",
                )
            ],
            operation="git_push",
            source_revision=self.revision,
            policy=self.policy,
        )
        self.assertFalse(supplement["allowed"])
        self.assertEqual(supplement["category"], "private")
        self.assertEqual(
            supplement["artifacts"][0]["artifact_family"],
            "private-local-state",
        )

    def test_component_registry_receipt_family_is_narrowly_public(self) -> None:
        receipt = MODULE.evaluate_outbound_bundle(
            [
                self.artifact(
                    "framework/receipts/component-registry/"
                    "context-routing-v1-rule-closure.json",
                    '{"schema_version":1,"receipt_id":"fixture"}\n',
                    producer="interactive-reviewed-github",
                )
            ],
            operation="git_push",
            source_revision=self.revision,
            policy=self.policy,
        )
        self.assertTrue(receipt["allowed"])
        self.assertEqual(
            receipt["artifacts"][0]["artifact_family"],
            "public-governance-summary",
        )
        self.assertEqual(
            receipt["artifacts"][0]["category"],
            "public_operational_summary",
        )

        with self.assertRaises(MODULE.DisclosureBlocked) as caught:
            MODULE.evaluate_outbound_bundle(
                [
                    self.artifact(
                        "framework/receipts/unrelated/receipt.json",
                        '{"schema_version":1,"receipt_id":"unmapped"}\n',
                        producer="interactive-reviewed-github",
                    )
                ],
                operation="git_push",
                source_revision=self.revision,
                policy=self.policy,
            )
        self.assertIn("unknown-artifact-family", str(caught.exception))

    def test_unrelated_members_of_one_family_do_not_inherit_by_default(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["artifact_families"].append(
            {
                "id": "fixture-restricted",
                "category": "restricted_operational",
                "producers": ["fixture-builder"],
                "paths": ["fixture/restricted.txt"],
            }
        )
        decision = MODULE.evaluate_outbound_bundle(
            [
                self.artifact("README.md", "Public project entry"),
                self.artifact(
                    "fixture/restricted.txt",
                    "Restricted fixture",
                    producer="fixture-builder",
                ),
            ],
            operation="git_push",
            source_revision=self.revision,
            policy=policy,
        )
        by_path = {item["path"]: item for item in decision["artifacts"]}
        self.assertEqual(
            by_path["README.md"]["category"],
            "public_by_design",
        )
        self.assertEqual(
            by_path["fixture/restricted.txt"]["category"],
            "restricted_operational",
        )

    def test_missing_control_pack_fails_before_classification(self) -> None:
        with (
            mock.patch.object(
                MODULE,
                "load_control_pack",
                side_effect=MODULE.DisclosureBlocked(
                    MODULE._unavailable_decision("active-control-pack-unavailable")
                ),
            ),
            self.assertRaises(MODULE.DisclosureBlocked) as caught,
        ):
            MODULE.evaluate_outbound_bundle(
                [self.artifact("README.md", "Public project entry")],
                operation="git_push",
                source_revision=self.revision,
                policy=self.policy,
            )
        self.assertIn("active-control-pack-unavailable", str(caught.exception))

    def test_production_api_rejects_caller_supplied_pack_substitution(self) -> None:
        weaker = {
            **self.control_pack,
            "pack_id": "caller-selected-weaker-pack",
            "restricted_detectors": [
                {"id": "weaker", "pattern": "NEVER-MATCH-THIS"}
            ],
        }
        with self.assertRaises(TypeError):
            MODULE.evaluate_outbound_bundle(
                [self.artifact("README.md", "Public project entry")],
                operation="git_push",
                source_revision=self.revision,
                policy=self.policy,
                control_pack=weaker,
            )

    def test_active_loader_does_not_accept_candidate_path_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "control-pack.json"
            candidate.write_text(json.dumps(self.control_pack), encoding="utf-8")
            with self.assertRaises(TypeError):
                self.original_load_control_pack(
                    candidate,
                    policy=self.policy,
                )

    def test_candidate_activation_is_atomic_and_preserves_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            repository = root / "repo"
            state = root / "state"
            candidate_root = (
                state
                / "disclosure-control-packs"
                / "candidates"
                / "candidate-1"
            )
            repository.mkdir()
            candidate_root.mkdir(parents=True)
            os.chmod(state, 0o700)
            os.chmod(state / "disclosure-control-packs", 0o700)
            candidate = {**self.control_pack, "status": "candidate"}
            candidate_path = candidate_root / "control-pack.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            os.chmod(candidate_path, 0o600)
            fixture_authority = MODULE.ProjectPathAuthority.fixture(
                root,
                repository_root=repository,
                state_root=state,
            )
            with (
                mock.patch.object(
                    MODULE.ProjectPathAuthority,
                    "production",
                    return_value=fixture_authority,
                ),
                mock.patch.object(
                    MODULE,
                    "load_control_pack",
                    wraps=self.original_load_control_pack,
                ),
            ):
                result = self.original_activate_candidate_control_pack(
                    "candidate-1",
                    policy=self.policy,
                )
            self.assertEqual(result["status"], "active")
            self.assertEqual(
                json.loads(candidate_path.read_text())["status"],
                "candidate",
            )
            pointer = json.loads(
                (
                    state / "disclosure-control-packs" / "active.json"
                ).read_text()
            )
            active = (
                state
                / "disclosure-control-packs"
                / pointer["control_pack"]
            )
            self.assertEqual(json.loads(active.read_text())["status"], "active")
            self.assertEqual(active.stat().st_mode & 0o777, 0o600)

    def test_github_actions_defense_check_is_explicitly_nonauthoritative(self) -> None:
        with mock.patch.object(
            MODULE,
            "load_control_pack",
            side_effect=AssertionError("defense check must not load local controls"),
        ):
            decision = MODULE.require_defense_in_depth_bundle(
                [self.artifact("README.md", "Public project entry")],
                operation="github_actions_defense_in_depth",
                source_revision=self.revision,
                policy=self.policy,
                complete=True,
            )
        self.assertTrue(decision["allowed"])
        self.assertFalse(decision["authoritative"])
        self.assertEqual(decision["mode"], "post_transmission_defense_in_depth")
        self.assertIsNone(decision["control_pack_id"])

    def test_defense_only_decision_cannot_authorize_outbound_mutation(self) -> None:
        with self.assertRaises(MODULE.DisclosureBlocked):
            MODULE.require_outbound_bundle(
                [self.artifact("README.md", "Public project entry")],
                operation="git_push",
                source_revision=self.revision,
                policy=self.policy,
                defense_in_depth_only=True,
                complete=True,
            )


if __name__ == "__main__":
    unittest.main()
