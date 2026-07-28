from __future__ import annotations

import copy
import importlib.util
import json
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


if __name__ == "__main__":
    unittest.main()
