import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "record_review_epoch", ROOT / "scripts" / "record_review_epoch.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def boundary(root: Path) -> tuple[Path, dict, dict[str, str]]:
    contents = {
        "framework_kernel": ("framework/FRAMEWORK.md", "# Framework\n", "pinned", True),
        "agent_rules_kernel": (
            "framework/AGENT_OPERATING_RULES.md",
            "# Agent Rules\n",
            "pinned",
            True,
        ),
        "current_audit": (
            "framework/records/handoffs/current-task.md",
            "# Current Task\n",
            "runtime",
            False,
        ),
        "additional_rule": (
            "framework/standards/content/additional.md",
            "# Additional Rule\n",
            "pinned",
            True,
        ),
    }
    for path, content, _, _ in contents.values():
        write(root, path, content)

    documents = {}
    for document_id, (path, content, policy, governing) in contents.items():
        spec = {
            "path": path,
            "hash_policy": policy,
            "governing": governing,
        }
        if policy == "pinned":
            spec["sha256"] = sha256(content)
        if document_id == "agent_rules_kernel":
            spec["requires"] = ["framework_kernel"]
        elif document_id == "current_audit":
            spec["requires"] = ["framework_kernel", "agent_rules_kernel"]
        elif document_id == "additional_rule":
            spec["requires"] = ["framework_kernel"]
        documents[document_id] = spec

    manifest = {
        "schema_version": 2,
        "generated_path_exclusions": [],
        "required_modules": [
            "framework_kernel",
            "agent_rules_kernel",
            "current_audit",
        ],
        "documents": documents,
        "capabilities": {},
        "profiles": {
            "comprehensive_review": {
                "max_bytes": 100000,
                "include_all_governing": True,
            }
        },
    }
    manifest_path = root / "framework/project/automation/context-routes.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    modules = []
    for document_id, (path, content, policy, _) in contents.items():
        modules.append(
            {
                "document": document_id,
                "path": path,
                "sha256": sha256(content),
                "hash_policy": policy,
                "bytes": len(content.encode("utf-8")),
                "content": content,
            }
        )
    packet = {
        "schema_version": 2,
        "profile": "comprehensive_review",
        "repository_revision": "b" * 40,
        "manifest": {
            "path": "framework/project/automation/context-routes.json",
            "sha256": manifest_sha,
        },
        "modules": modules,
        "sections": [],
        "provenance_complete": True,
    }
    hashes = {
        path: "sha256:" + sha256(content)
        for path, content, _, governing in contents.values()
        if governing
    }
    hashes["framework/project/automation/context-routes.json"] = "sha256:" + manifest_sha
    return manifest_path, packet, hashes


def record(hashes: dict[str, str]) -> dict:
    return {
        "epoch_id": "REVIEW-2026-07-24",
        "triggering_run_id": "arrp-chain-1",
        "baseline_commit": "a" * 40,
        "completion_commit": "b" * 40,
        "governing_hashes": hashes,
        "project_snapshot": {
            "source": "project-console-data:progress.json",
            "sha256": "sha256:" + "c" * 64,
            "record_count": 82,
        },
        "registry_snapshot": {
            "source": "inventory/github_issue_registry.csv",
            "sha256": "sha256:" + "d" * 64,
            "record_count": 256,
        },
        "reviewed_domains": ["governance", "issues"],
        "resolved_findings": [],
        "unresolved_findings": [],
        "sampling_record": ["DOJ-001", "ELEC-001"],
        "automation_health": {
            "chain_id": "arrp-chain-1",
            "status": "healthy",
            "failures": [],
            "degradations": [],
        },
        "completed_at": "2026-07-24T12:00:00+00:00",
        "next_due_at": "2026-08-07T12:00:00+00:00",
        "cadence_status": "biweekly",
        "stability_status": "evolving",
        "triggering_reason": "Periodic consistency boundary.",
    }


class ReviewEpochTests(unittest.TestCase):
    def test_validated_epoch_is_append_only_and_updates_current(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)
            value = MODULE.validate(
                record(hashes),
                manifest_path=manifest,
                context_packet=packet,
                root=root,
            )
            ledger = root / "epochs.jsonl"
            current = root / "current.json"
            self.assertTrue(MODULE.append(ledger, current, value))
            self.assertFalse(MODULE.append(ledger, current, value))
            self.assertEqual(len(ledger.read_text().splitlines()), 1)
            self.assertIn("record_sha256", current.read_text())

    def test_next_due_must_follow_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)
            value = record(hashes)
            value["next_due_at"] = value["completed_at"]
            with self.assertRaisesRegex(ValueError, "must follow"):
                MODULE.validate(
                    value,
                    manifest_path=manifest,
                    context_packet=packet,
                    root=root,
                )

    def test_partial_governing_hash_boundary_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)
            del hashes["framework/standards/content/additional.md"]
            with self.assertRaisesRegex(ValueError, "boundary is incomplete"):
                MODULE.validate(
                    record(hashes),
                    manifest_path=manifest,
                    context_packet=packet,
                    root=root,
                )

    def test_manifest_identity_is_required_in_governing_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)
            del hashes["framework/project/automation/context-routes.json"]
            with self.assertRaisesRegex(ValueError, "boundary is incomplete"):
                MODULE.validate(
                    record(hashes),
                    manifest_path=manifest,
                    context_packet=packet,
                    root=root,
                )

    def test_manifest_argument_must_resolve_inside_the_reviewed_root(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repo"
            root.mkdir()
            manifest, packet, hashes = boundary(root)
            outside = base / "outside-context-routes.json"
            outside.write_bytes(manifest.read_bytes())
            linked = root / "framework" / "linked-context-routes.json"
            linked.symlink_to(outside)

            for candidate in (outside, linked):
                with self.subTest(candidate=candidate.name):
                    with self.assertRaisesRegex(
                        ValueError,
                        "path escapes allowed root",
                    ):
                        MODULE.validate(
                            record(hashes),
                            manifest_path=candidate,
                            context_packet=packet,
                            root=root,
                        )

    def test_manifest_argument_accepts_relative_and_in_root_absolute_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)
            for candidate in (
                Path("framework/project/automation/context-routes.json"),
                manifest,
            ):
                with self.subTest(candidate=str(candidate)):
                    validated = MODULE.validate(
                        record(hashes),
                        manifest_path=candidate,
                        context_packet=packet,
                        root=root,
                    )
                    self.assertEqual(validated["epoch_id"], "REVIEW-2026-07-24")

    def test_packet_manifest_path_cannot_redirect_boundary_hashing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)
            redirected = copy.deepcopy(packet)
            redirected["manifest"]["path"] = "../outside-context-routes.json"
            with self.assertRaisesRegex(ValueError, "manifest identity"):
                MODULE.validate(
                    record(hashes),
                    manifest_path=manifest,
                    context_packet=redirected,
                    root=root,
                )

    def test_noncomprehensive_packet_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)
            packet["profile"] = "change_audit"
            with self.assertRaisesRegex(ValueError, "comprehensive_review"):
                MODULE.validate(
                    record(hashes),
                    manifest_path=manifest,
                    context_packet=packet,
                    root=root,
                )

    def test_packet_missing_governing_module_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)
            packet["modules"] = [
                module
                for module in packet["modules"]
                if module["document"] != "additional_rule"
            ]
            with self.assertRaisesRegex(ValueError, "module boundary differs"):
                MODULE.validate(
                    record(hashes),
                    manifest_path=manifest,
                    context_packet=packet,
                    root=root,
                )

    def test_stale_packet_manifest_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)
            stale_packet = copy.deepcopy(packet)
            stale_packet["manifest"]["sha256"] = "d" * 64
            with self.assertRaisesRegex(ValueError, "manifest identity"):
                MODULE.validate(
                    record(hashes),
                    manifest_path=manifest,
                    context_packet=stale_packet,
                    root=root,
                )

    def test_packet_content_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)
            packet["modules"][0]["content"] = "# Partial\n"
            packet["modules"][0]["bytes"] = len("# Partial\n".encode("utf-8"))
            with self.assertRaisesRegex(ValueError, "content hash differs"):
                MODULE.validate(
                    record(hashes),
                    manifest_path=manifest,
                    context_packet=packet,
                    root=root,
                )

    def test_commit_hashes_and_packet_completion_boundary_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)

            invalid = record(hashes)
            invalid["baseline_commit"] = "not-a-commit"
            with self.assertRaisesRegex(ValueError, "40-character Git commit"):
                MODULE.validate(
                    invalid,
                    manifest_path=manifest,
                    context_packet=packet,
                    root=root,
                )

            mismatched = record(hashes)
            mismatched["completion_commit"] = "e" * 40
            with self.assertRaisesRegex(
                ValueError,
                "must equal the comprehensive context packet",
            ):
                MODULE.validate(
                    mismatched,
                    manifest_path=manifest,
                    context_packet=packet,
                    root=root,
                )

    def test_review_scope_and_sample_must_be_nonempty(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)
            for field in ("reviewed_domains", "sampling_record"):
                with self.subTest(field=field):
                    value = record(hashes)
                    value[field] = []
                    with self.assertRaisesRegex(ValueError, f"{field} must not be empty"):
                        MODULE.validate(
                            value,
                            manifest_path=manifest,
                            context_packet=packet,
                            root=root,
                        )

    def test_structured_snapshots_findings_and_automation_health_are_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)

            invalid_snapshot = record(hashes)
            invalid_snapshot["project_snapshot"]["sha256"] = "not-a-hash"
            with self.assertRaisesRegex(ValueError, "project_snapshot.sha256"):
                MODULE.validate(
                    invalid_snapshot,
                    manifest_path=manifest,
                    context_packet=packet,
                    root=root,
                )

            invalid_resolved = record(hashes)
            invalid_resolved["resolved_findings"] = [{"summary": "No stable identity"}]
            with self.assertRaisesRegex(ValueError, "nonblank stable id"):
                MODULE.validate(
                    invalid_resolved,
                    manifest_path=manifest,
                    context_packet=packet,
                    root=root,
                )

            invalid_health = record(hashes)
            invalid_health["automation_health"]["status"] = "unknown"
            with self.assertRaisesRegex(ValueError, "must be healthy, degraded, or failed"):
                MODULE.validate(
                    invalid_health,
                    manifest_path=manifest,
                    context_packet=packet,
                    root=root,
                )

    def test_finding_ids_are_unique_within_and_across_status_lists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest, packet, hashes = boundary(root)

            repeated = record(hashes)
            repeated["unresolved_findings"] = [
                {"id": "FINDING-1"},
                {"id": "FINDING-1"},
            ]
            with self.assertRaisesRegex(ValueError, "repeats finding IDs"):
                MODULE.validate(
                    repeated,
                    manifest_path=manifest,
                    context_packet=packet,
                    root=root,
                )

            contradictory = record(hashes)
            contradictory["resolved_findings"] = [{"id": "FINDING-1"}]
            contradictory["unresolved_findings"] = [{"id": "FINDING-1"}]
            with self.assertRaisesRegex(ValueError, "may not appear in both"):
                MODULE.validate(
                    contradictory,
                    manifest_path=manifest,
                    context_packet=packet,
                    root=root,
                )

    def test_finding_continuity_requires_prior_ids_to_be_open_or_resolved(self):
        prior = {
            "unresolved_findings": [
                {"id": "FINDING-OPEN"},
                {"id": "FINDING-RESOLVED"},
            ]
        }
        carried = {
            "resolved_findings": [{"id": "FINDING-RESOLVED"}],
            "unresolved_findings": [{"id": "FINDING-OPEN"}],
        }
        self.assertIs(
            MODULE.validate_finding_continuity(prior, carried),
            carried,
        )

        omitted = {
            "resolved_findings": [],
            "unresolved_findings": [{"id": "FINDING-OPEN"}],
        }
        with self.assertRaisesRegex(ValueError, "FINDING-RESOLVED"):
            MODULE.validate_finding_continuity(prior, omitted)

    def test_main_enforces_continuity_against_latest_historical_ledger_row(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            input_path = root / "record.json"
            manifest = root / "manifest.json"
            packet_path = root / "packet.json"
            ledger = root / "epochs.jsonl"
            current = root / "current.json"
            input_path.write_text("{}\n", encoding="utf-8")
            manifest.write_text("{}\n", encoding="utf-8")
            packet_path.write_text("{}\n", encoding="utf-8")
            ledger.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "epoch_id": "legacy-epoch",
                        "unresolved_findings": ["LEGACY-FINDING"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            argv = [
                "record_review_epoch.py",
                "--input",
                str(input_path),
                "--manifest",
                str(manifest),
                "--context-packet",
                str(packet_path),
                "--ledger",
                str(ledger),
                "--current",
                str(current),
            ]
            path_authority = MODULE.ProjectPathAuthority.fixture(
                root,
                repository_root=root,
                state_root=root,
            )
            next_record = {
                "epoch_id": "next-epoch",
                "resolved_findings": [],
                "unresolved_findings": [],
            }
            with patch("sys.argv", argv), patch.object(
                MODULE,
                "validate",
                return_value=next_record,
            ):
                with self.assertRaisesRegex(ValueError, "LEGACY-FINDING"):
                    MODULE.main(path_authority=path_authority)
            self.assertEqual(len(ledger.read_text(encoding="utf-8").splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
