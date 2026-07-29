from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import build_owner_console as owner_console
from scripts.security_incidents import (
    project_security_incident_log,
    record_security_occurrence,
)


GENERATION_ID = "project-console-test"
SOURCE_REVISION = "a" * 40
STAGED_AT = datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc)
VERSION_ID = f"{GENERATION_ID}-20260729T120000000000Z"


def digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def assignment(prefix: str, payload: dict[str, object], comment: str = "") -> bytes:
    return (
        comment
        + prefix
        + json.dumps(payload, sort_keys=True, separators=(",", ":"))
        + ";\n"
    ).encode("utf-8")


def parsed_assignment(path: Path, global_name: str) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    prefix = (
        "/* Generated owner-only Console snapshot; never commit or publish. */\n"
        f"{global_name}="
    )
    return json.loads(text.removeprefix(prefix).removesuffix(";\n"))


class OwnerConsoleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.repository = self.root / "ARRP"
        self.console = (
            self.repository / "research" / "horizon-review-console"
        )
        self.data = self.console / "data"
        self.data.mkdir(parents=True)
        self.private_versions = self.root / "private-staging" / "role-c"
        self.private_versions.mkdir(parents=True, mode=0o700)
        os.chmod(self.private_versions.parent, 0o700)
        os.chmod(self.private_versions, 0o700)
        self.security_tool = {
            "tool_id": "credential-access-review",
            "label": "Credential and access review",
            "availability": "current",
            "last_checked": "2026-07-29T11:00:00Z",
            "next_due": None,
            "source_revision": None,
            "coverage_state": "current",
            "private_attention": "no",
            "owner_class": "Human",
            "destination_class": "owner_local_review",
            "active_incident": False,
            "public_intake_state": None,
        }
        self.public_security_tool = {
            **self.security_tool,
            "purpose": "Verify access review currentness.",
        }
        self.public_security_tool.pop("last_checked")
        self.public_security_tool.pop("next_due")
        self.public_security_tool.pop("source_revision")
        self.public_security_tool.pop("coverage_state")
        self.public_security_tool.pop("private_attention")
        self.public_security_tool.pop("active_incident")
        self.public_security_tool.pop("public_intake_state")
        self._write_public_generation()
        self._write_private_projections()
        self.authority = SimpleNamespace(
            owner_console_versions_root=self.private_versions
        )
        self.patch_repository = mock.patch.object(
            owner_console,
            "APPROVED_REPOSITORY_ROOT",
            self.repository,
        )
        self.patch_repository.start()
        self.addCleanup(self.patch_repository.stop)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def build(self) -> Path:
        return owner_console.build_owner_console(
            private_authority=self.authority,
            now=STAGED_AT,
        )

    def _write_public_generation(self) -> None:
        part_payload = {
            "overview": {"status": "current"},
            "domain_generation": {"overview.js": GENERATION_ID},
        }
        domain = (
            owner_console.PART_PREFIX
            + json.dumps(part_payload, indent=2)
            + ");\n"
        ).encode("utf-8")
        (self.data / "overview.js").write_bytes(domain)
        metadata = {
            "generation_id": GENERATION_ID,
            "sha256": digest(domain),
            "bytes": len(domain),
            "keys": ["overview"],
            "record_count": 1,
        }
        domain_row = {
            key: value
            for key, value in metadata.items()
            if key != "generation_id"
        }
        domain_row["file"] = "overview.js"
        manifest = {
            "manifest_schema_version": 1,
            "generation_id": GENERATION_ID,
            "generated_at": "2026-07-29T11:30:00Z",
            "source_revision": SOURCE_REVISION,
            "availability": "current",
            "completeness": {
                "actual_count": 1,
                "complete": True,
                "expected_count": 1,
                "missing_count": 0,
            },
            "domain_count": 1,
            "domains": [domain_row],
            "files": {"overview.js": metadata},
        }
        (self.data / "generation-manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        catalog = {
            "schema_version": 1,
            "generation_id": GENERATION_ID,
            "source_revision": SOURCE_REVISION,
            "generation_manifest": manifest,
            "security_assurance": {
                "schema_version": 2,
                "availability": "unavailable",
                "complete": False,
                "tools": [self.public_security_tool],
            },
        }
        (self.console / "catalog-data.js").write_bytes(
            assignment(owner_console.CATALOG_PREFIX, catalog)
        )
        (self.console / "index.html").write_text(
            "<!doctype html>\n"
            '<script src="catalog-data.js?v=48"></script>\n'
            '<script src="app.js?v=65"></script>\n',
            encoding="utf-8",
        )
        (self.console / "app.js").write_text(
            'console.log("public shell");\n',
            encoding="utf-8",
        )
        (self.console / "styles.css").write_text(
            "body { color: black; }\n",
            encoding="utf-8",
        )

    def _local_status(self) -> dict[str, object]:
        payload = {field: None for field in owner_console.LOCAL_STATUS_FIELDS}
        payload.update(
            {
                "schema_version": "1.0",
                "run_id": "arrp-20260729T110000Z",
                "trigger": "scheduled",
                "started_at": "2026-07-29T11:00:00Z",
                "updated_at": "2026-07-29T11:00:01Z",
                "status": "failed",
                "control_state": "paused",
                "control_state_checked_at": "2026-07-29T11:15:00Z",
                "stage": "00_start",
                "canonical_path": str(self.repository),
                "preserved_paths": [],
                "runtime_commit": None,
                "starting_local_head": None,
            }
        )
        return payload

    def _write_private_projections(self) -> None:
        security = {
            "schema_version": 2,
            "availability": "current",
            "complete": True,
            "checked_at": "2026-07-29T11:00:00Z",
            "public_intake_state": "paused",
            "private_attention": "none_reported",
            "active_incident": False,
            "tools": [self.security_tool],
        }
        operations = {
            "schema_version": 4,
            "availability": "current",
            "generated_at": "2026-07-29T11:30:00Z",
            "catalog_generation_id": GENERATION_ID,
            "source_revision": SOURCE_REVISION,
            "agent_registry": [],
            "project_logs": [],
            "integrity": {},
            "run_chain": {},
            "action_snapshot": {
                "schema_version": 1,
                "generation_id": "action-snapshot-test",
                "generated_at": "2026-07-29T11:30:00Z",
                "availability": "partial",
                "complete": False,
                "items": [],
                "counts": {
                    "human": None,
                    "oversight": None,
                    "all_open": None,
                },
                "known_counts": {
                    "human": 0,
                    "oversight": 0,
                    "all_open": 0,
                },
                "sources": {},
                "predicates": {},
                "private_join": {
                    "security_assurance": "complete",
                    "checked_at": "2026-07-29T11:00:00Z",
                },
            },
            "queue_directory": {
                "schema_version": 1,
                "generation_id": "queue-directory-test",
                "generated_at": "2026-07-29T11:30:00Z",
                "availability": "partial",
                "complete": False,
                "queues": [
                    {
                        "queue_id": "human_actions",
                        "availability": "unavailable",
                        "complete": False,
                        "count": None,
                    }
                ],
            },
            "operational_incidents": {
                "schema_version": 1,
                "availability": "current",
                "complete": True,
                "checked_at": "2026-07-29T11:30:00Z",
                "count": 0,
                "unresolved_count": 0,
                "impact_state": "green",
                "items": [],
                "active_links": {},
            },
            "security_incidents": {
                "schema_version": 1,
                "authority": "owner-local-security-incidents",
                "availability": "unavailable",
                "complete": False,
                "checked_at": "2026-07-29T11:30:00Z",
                "count": None,
                "unresolved_count": None,
                "items": [],
                "reason_code": "missing-security-incident-feed",
            },
            "incident_relations": {
                "schema_version": 1,
                "authority": "owner-local-incident-relations",
                "availability": "unavailable",
                "complete": False,
                "checked_at": None,
                "active_relations": [],
                "relations": [],
                "by_operational_incident": {},
                "by_security_incident": {},
                "reason_code": "incident-relations-missing",
            },
            "governance_change_supplements": {
                "schema_version": 1,
                "availability": "unavailable",
                "complete": False,
                "checked_at": "2026-07-29T11:30:00Z",
                "source_revision": SOURCE_REVISION,
                "public_log_sha256": "sha256:" + "f" * 64,
                "items": [],
                "reason_code": (
                    "owner-local-governance-supplements-unavailable"
                ),
            },
            "privacy": "Owner-only local projection.",
        }
        values = {
            "private-security-assurance.js": assignment(
                "window.ARRP_PRIVATE_SECURITY_ASSURANCE=",
                security,
                "/* Private local projection; never commit or publish. */\n",
            ),
            "private-operations.js": assignment(
                "window.ARRP_PRIVATE_OPERATIONS=",
                operations,
                "/* Private local projection; never commit or publish. */\n",
            ),
            "local-automation-status.js": assignment(
                "window.ARRP_LOCAL_AUTOMATION_STATUS = ",
                self._local_status(),
            ),
        }
        for name, content in values.items():
            path = self.data / name
            path.write_bytes(content)
            os.chmod(path, 0o600)

    def test_builds_immutable_generation_bound_owner_snapshot(self) -> None:
        source_index = (self.console / "index.html").read_bytes()

        version = self.build()

        self.assertEqual(version.name, VERSION_ID)
        self.assertEqual(
            version.parent,
            self.private_versions,
        )
        self.assertEqual(
            (self.console / "index.html").read_bytes(),
            source_index,
        )
        index = (version / "index.html").read_text(encoding="utf-8")
        self.assertLess(
            index.index('src="owner-console-binding.js"'),
            index.index('src="app.js?v=65"'),
        )
        binding = parsed_assignment(
            version / "owner-console-binding.js",
            owner_console.OWNER_BINDING_GLOBAL,
        )
        self.assertEqual(
            binding["exact_decoded_file_path"],
            str(version / "index.html"),
        )
        self.assertEqual(binding["generation_id"], GENERATION_ID)
        self.assertEqual(binding["source_revision"], SOURCE_REVISION)
        self.assertEqual(
            set(binding["projections"]),
            {
                "security-assurance",
                "private-operations",
                "local-automation-status",
            },
        )
        local = parsed_assignment(
            version / "data" / "local-automation-status.js",
            "window.ARRP_LOCAL_AUTOMATION_STATUS",
        )
        self.assertEqual(
            local["owner_console_envelope"]["generation_id"],
            GENERATION_ID,
        )
        self.assertIsNone(local["payload"]["runtime_commit"])
        self.assertIsNone(local["payload"]["starting_local_head"])
        operations = parsed_assignment(
            version / "data" / "private-operations.js",
            "window.ARRP_PRIVATE_OPERATIONS",
        )
        self.assertEqual(
            operations["owner_console_envelope"]["availability"],
            "partial",
        )
        self.assertFalse(
            operations["owner_console_envelope"]["complete"],
        )
        self.assertIsNone(
            operations["payload"]["action_snapshot"]["counts"]["human"]
        )
        self.assertEqual(
            (version / "data" / "overview.js").read_bytes(),
            (self.data / "overview.js").read_bytes(),
        )
        for current, directories, files in os.walk(version):
            self.assertEqual(
                stat.S_IMODE(Path(current).stat().st_mode),
                0o700,
            )
            for directory in directories:
                self.assertEqual(
                    stat.S_IMODE((Path(current) / directory).stat().st_mode),
                    0o700,
                )
            for filename in files:
                self.assertEqual(
                    stat.S_IMODE((Path(current) / filename).stat().st_mode),
                    0o600,
                )
        self.assertFalse(
            any(
                path.name.startswith(".staging-")
                for path in version.parent.iterdir()
            )
        )

    def test_existing_version_is_never_overwritten(self) -> None:
        version = self.build()
        original = (version / "index.html").read_bytes()

        with self.assertRaisesRegex(
            owner_console.OwnerConsoleBuildError,
            "never overwritten",
        ):
            self.build()

        self.assertEqual((version / "index.html").read_bytes(), original)

    def test_incomplete_or_hash_mismatched_public_generation_fails_closed(self) -> None:
        manifest_path = self.data / "generation-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["completeness"]["complete"] = False
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        with self.assertRaisesRegex(
            owner_console.OwnerConsoleBuildError,
            "incomplete",
        ):
            self.build()

        self.assertFalse(any(self.private_versions.iterdir()))

    def test_public_domain_hash_mismatch_fails_closed(self) -> None:
        (self.data / "overview.js").write_text(
            "/* altered after manifest generation */\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            owner_console.OwnerConsoleBuildError,
            "hash verification",
        ):
            self.build()

        self.assertFalse(any(self.private_versions.iterdir()))

    def test_manifest_cannot_select_an_unobserved_domain_path(self) -> None:
        manifest_path = self.data / "generation-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        metadata = dict(manifest["files"]["overview.js"])
        row = {
            key: value
            for key, value in metadata.items()
            if key != "generation_id"
        }
        row["file"] = "not-present.js"
        manifest["files"]["not-present.js"] = metadata
        manifest["domains"].append(row)
        manifest["domain_count"] = 2
        manifest["completeness"].update(
            {
                "actual_count": 2,
                "expected_count": 2,
            }
        )
        manifest_path.write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )

        with mock.patch.object(
            owner_console,
            "_read_regular",
            wraps=owner_console._read_regular,
        ) as read_regular:
            with self.assertRaisesRegex(
                owner_console.OwnerConsoleBuildError,
                "canonical data inventory disagree",
            ):
                self.build()
        self.assertNotIn(
            "not-present.js",
            {
                call.args[0].name
                for call in read_regular.call_args_list
                if call.args
            },
        )

    def test_unmanifested_or_symlinked_public_domain_fails_closed(
        self,
    ) -> None:
        extra = self.data / "unexpected-domain.js"
        extra.write_text("/* not in the manifest */\n", encoding="utf-8")
        with self.assertRaisesRegex(
            owner_console.OwnerConsoleBuildError,
            "canonical data inventory disagree",
        ):
            self.build()
        extra.rename(self.root / "unexpected-domain.preserved")

        domain = self.data / "overview.js"
        preserved = self.root / "overview.preserved"
        domain.rename(preserved)
        domain.symlink_to(preserved)
        with self.assertRaisesRegex(
            owner_console.OwnerConsoleBuildError,
            "unsafe domain",
        ):
            self.build()

    def test_private_projection_cannot_become_a_public_manifest_domain(
        self,
    ) -> None:
        manifest_path = self.data / "generation-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        metadata = dict(manifest["files"]["overview.js"])
        row = {
            key: value
            for key, value in metadata.items()
            if key != "generation_id"
        }
        row["file"] = "private-operations.js"
        manifest["files"]["private-operations.js"] = metadata
        manifest["domains"].append(row)
        manifest["domain_count"] = 2
        manifest["completeness"].update(
            {
                "actual_count": 2,
                "expected_count": 2,
            }
        )
        manifest_path.write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            owner_console.OwnerConsoleBuildError,
            "canonical data inventory disagree",
        ):
            self.build()

    def test_stale_private_operations_binding_fails_closed(self) -> None:
        path = self.data / "private-operations.js"
        payload = owner_console._json_script_payload(
            path.read_bytes(),
            prefix="window.ARRP_PRIVATE_OPERATIONS=",
            leading_comment=(
                "/* Private local projection; never commit or publish. */\n"
            ),
        )
        payload["catalog_generation_id"] = "stale-generation"
        path.write_bytes(
            assignment(
                "window.ARRP_PRIVATE_OPERATIONS=",
                payload,
                "/* Private local projection; never commit or publish. */\n",
            )
        )
        os.chmod(path, 0o600)

        with self.assertRaisesRegex(
            owner_console.OwnerConsoleBuildError,
            "stale, incomplete, or unbound",
        ):
            self.build()

    def test_unknown_security_field_fails_closed(self) -> None:
        path = self.data / "private-security-assurance.js"
        payload = owner_console._json_script_payload(
            path.read_bytes(),
            prefix="window.ARRP_PRIVATE_SECURITY_ASSURANCE=",
            leading_comment=(
                "/* Private local projection; never commit or publish. */\n"
            ),
        )
        payload["tools"][0]["vulnerability_detail"] = "not allowed"
        path.write_bytes(
            assignment(
                "window.ARRP_PRIVATE_SECURITY_ASSURANCE=",
                payload,
                "/* Private local projection; never commit or publish. */\n",
            )
        )
        os.chmod(path, 0o600)

        with self.assertRaisesRegex(
            owner_console.OwnerConsoleBuildError,
            "field allowlist",
        ):
            self.build()

    def test_unknown_security_incident_field_fails_closed(self) -> None:
        ledger = self.root / "security-incidents.jsonl"
        record_security_occurrence(
            ledger,
            security_domain="repository-security",
            protected_surface="outbound-disclosure",
            event_class="material-near-miss",
            safe_summary="A protected review requires investigation.",
            reported_by="Deterministic security recorder",
            owner=None,
            recommended_owner="Owner security review",
            next_action="Open the protected evidence authority.",
            occurrence_id="owner-console-test",
            observed_at="2026-07-29T11:00:00Z",
            source_ref="restricted:security-evidence/owner-console-test",
            safe_observation="A protected review boundary was reached.",
            restricted_evidence_refs=[
                "restricted:security-evidence/owner-console-test"
            ],
            now=STAGED_AT,
        )
        projection = project_security_incident_log(ledger)
        self.assertTrue(
            owner_console._valid_incident_projection(
                projection,
                incident_kind="security",
            )
        )
        projection["items"][0]["vulnerability_detail"] = "not allowed"
        self.assertFalse(
            owner_console._valid_incident_projection(
                projection,
                incident_kind="security",
            )
        )

    def test_private_projection_symlink_is_rejected(self) -> None:
        path = self.data / "local-automation-status.js"
        original = self.root / "local-automation-status.real"
        path.rename(original)
        path.symlink_to(original)

        with self.assertRaisesRegex(
            owner_console.OwnerConsoleBuildError,
            "regular non-symlink",
        ):
            self.build()

    def test_missing_private_projection_fails_closed(self) -> None:
        path = self.data / "private-operations.js"
        moved = self.root / "private-operations.preserved"
        path.rename(moved)

        with self.assertRaisesRegex(
            owner_console.OwnerConsoleBuildError,
            "required Console source is unavailable",
        ):
            self.build()

        self.assertFalse(any(self.private_versions.iterdir()))

    def test_secret_shaped_local_status_is_not_staged(self) -> None:
        path = self.data / "local-automation-status.js"
        payload = self._local_status()
        payload["failure_reason"] = (
            "Authorization" + ": " + "Bearer "
            + "owner_console_secret_canary_123456"
        )
        path.write_bytes(
            assignment(
                "window.ARRP_LOCAL_AUTOMATION_STATUS = ",
                payload,
            )
        )
        os.chmod(path, 0o600)

        with self.assertRaisesRegex(
            owner_console.OwnerConsoleBuildError,
            "prohibited secret",
        ):
            self.build()

        self.assertFalse(any(self.private_versions.iterdir()))


if __name__ == "__main__":
    unittest.main()
