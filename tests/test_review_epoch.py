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


def boundary(
    root: Path,
    *,
    status: str = "active",
) -> tuple[dict, dict, dict, dict[str, str]]:
    contents = {
        "framework_kernel": ("framework/FRAMEWORK.md", "# Framework\n", "pinned", True),
        "agent_rules_kernel": (
            "framework/AGENT_OPERATING_RULES.md",
            "# Agent Rules\n",
            "pinned",
            True,
        ),
        "task_handoff": (
            "framework/handoffs/current-task.md",
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
        elif document_id == "task_handoff":
            spec["requires"] = ["framework_kernel", "agent_rules_kernel"]
        elif document_id == "additional_rule":
            spec["requires"] = ["framework_kernel"]
        documents[document_id] = spec

    route = {
        "required_modules": [
            "framework_kernel",
            "agent_rules_kernel",
            "task_handoff",
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
    active = status == "active"
    view = {
        "schema_version": 4,
        "validation_mode": (
            "live_authority_validation"
            if active
            else "adopted_configuration_validation"
        ),
        "registry_status": "adopted",
        "registry_id": "COMPONENT-REGISTRY",
        "registry_revision": 6,
        "registry_sha256": "d" * 64,
        "registry_path": "framework/component-registry.json",
        "authoritative": active,
        "executable": False,
        "authority_effective": active,
        "source_revision_authorized": active,
        "source_bytes_current": True,
        "canonical_history_confirmed": active,
        "receipt_trusted": active,
        "runtime_live": "not_checked",
        "activation_receipt_consulted": active,
        "predecessor_route_consulted": False,
        "route": route,
    }
    inclusion_reasons = {
        "framework_kernel": ["required floor"],
        "agent_rules_kernel": ["required floor"],
        "task_handoff": ["required floor"],
        "additional_rule": [
            "profile comprehensive_review complete governing boundary"
        ],
    }
    ordered_ids = [
        "framework_kernel",
        "agent_rules_kernel",
        "task_handoff",
        "additional_rule",
    ]
    selection = {
        "selection_kind": "configuration_validation_packet",
        "executable": False,
        "registry_id": view["registry_id"],
        "registry_revision": view["registry_revision"],
        "registry_sha256": view["registry_sha256"],
        "registry_path": view["registry_path"],
        "authoritative": False,
        "profile": "comprehensive_review",
        "capabilities": [],
        "modules": [
            {
                "id": document_id,
                "path": documents[document_id]["path"],
                "governing": documents[document_id]["governing"],
                "hash_policy": documents[document_id]["hash_policy"],
                "sha256": documents[document_id].get("sha256"),
                "inclusion_reasons": inclusion_reasons[document_id],
            }
            for document_id in ordered_ids
        ],
        "sections": [],
    }
    modules = []
    for document_id in ordered_ids:
        path, content, policy, _ = contents[document_id]
        modules.append(
            {
                "document": document_id,
                "path": path,
                "sha256": sha256(content),
                "hash_policy": policy,
                "bytes": len(content.encode("utf-8")),
                "content": content,
                "inclusion_reasons": inclusion_reasons[document_id],
            }
        )
    packet = {
        "schema_version": 2,
        "profile": "comprehensive_review",
        "repository_revision": "b" * 40,
        "manifest": {
            "path": view["registry_path"],
            "sha256": view["registry_sha256"],
        },
        "routing_manifest": {
            "registry_id": view["registry_id"],
            "registry_path": view["registry_path"],
            "registry_revision": view["registry_revision"],
            "validation_mode": view["validation_mode"],
            "authoritative": view["authoritative"],
            "executable": view["executable"],
            "registry_digest": view["registry_sha256"],
            "selected_profile": "comprehensive_review",
            "selected_capabilities": [],
            "resolved_document_revisions": {
                document_id: {
                    "path": documents[document_id]["path"],
                    "hash_policy": documents[document_id]["hash_policy"],
                }
                for document_id in ordered_ids
            },
            "resolved_document_digests": {
                document_id: sha256(contents[document_id][1])
                for document_id in ordered_ids
            },
            "resolved_document_order": ordered_ids,
            "dependency_closure": {
                document_id: documents[document_id].get("requires", [])
                for document_id in ordered_ids
            },
            "exact_sections": [],
            "dynamic_expansions": [],
            "inclusion_reasons": inclusion_reasons,
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
    hashes[view["registry_path"]] = "sha256:" + view["registry_sha256"]
    return view, selection, packet, hashes


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
            view, selection, packet, hashes = boundary(root)
            value = MODULE.validate(
                record(hashes),
                routing_view=view,
                routing_selection=selection,
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
            view, selection, packet, hashes = boundary(root)
            value = record(hashes)
            value["next_due_at"] = value["completed_at"]
            with self.assertRaisesRegex(ValueError, "must follow"):
                MODULE.validate(
                    value,
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=packet,
                    root=root,
                )

    def test_partial_governing_hash_boundary_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            view, selection, packet, hashes = boundary(root)
            del hashes["framework/standards/content/additional.md"]
            with self.assertRaisesRegex(ValueError, "boundary is incomplete"):
                MODULE.validate(
                    record(hashes),
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=packet,
                    root=root,
                )

    def test_component_registry_identity_is_required_in_governing_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            view, selection, packet, hashes = boundary(root)
            del hashes["framework/component-registry.json"]
            with self.assertRaisesRegex(ValueError, "boundary is incomplete"):
                MODULE.validate(
                    record(hashes),
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=packet,
                    root=root,
                )

    def test_active_closeout_rejects_predecessor_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            view, selection, packet, hashes = boundary(root)
            view["predecessor_route_consulted"] = True
            with self.assertRaisesRegex(ValueError, "governed-eligible"):
                MODULE.validate(
                    record(hashes),
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=packet,
                    root=root,
                )

    def test_candidate_closeout_requires_explicit_fixture_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            view, selection, packet, hashes = boundary(
                root,
                status="candidate",
            )
            with self.assertRaisesRegex(ValueError, "must be explicitly enabled"):
                MODULE.validate(
                    record(hashes),
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=packet,
                    root=root,
                )
            validated = MODULE.validate(
                record(hashes),
                routing_view=view,
                routing_selection=selection,
                context_packet=packet,
                root=root,
                allow_candidate_validation=True,
            )
            self.assertEqual(validated["epoch_id"], "REVIEW-2026-07-24")

    def test_packet_registry_path_cannot_redirect_boundary_hashing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            view, selection, packet, hashes = boundary(root)
            redirected = copy.deepcopy(packet)
            redirected["manifest"]["path"] = "../outside-context-routes.json"
            with self.assertRaisesRegex(ValueError, "registry identity"):
                MODULE.validate(
                    record(hashes),
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=redirected,
                    root=root,
                )

    def test_noncomprehensive_packet_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            view, selection, packet, hashes = boundary(root)
            packet["profile"] = "change_audit"
            with self.assertRaisesRegex(ValueError, "comprehensive_review"):
                MODULE.validate(
                    record(hashes),
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=packet,
                    root=root,
                )

    def test_packet_missing_governing_module_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            view, selection, packet, hashes = boundary(root)
            packet["modules"] = [
                module
                for module in packet["modules"]
                if module["document"] != "additional_rule"
            ]
            with self.assertRaisesRegex(ValueError, "module boundary differs"):
                MODULE.validate(
                    record(hashes),
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=packet,
                    root=root,
                )

    def test_stale_packet_registry_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            view, selection, packet, hashes = boundary(root)
            stale_packet = copy.deepcopy(packet)
            stale_packet["manifest"]["sha256"] = "e" * 64
            with self.assertRaisesRegex(ValueError, "registry identity"):
                MODULE.validate(
                    record(hashes),
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=stale_packet,
                    root=root,
                )

    def test_packet_content_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            view, selection, packet, hashes = boundary(root)
            packet["modules"][0]["content"] = "# Partial\n"
            packet["modules"][0]["bytes"] = len("# Partial\n".encode("utf-8"))
            with self.assertRaisesRegex(ValueError, "content hash differs"):
                MODULE.validate(
                    record(hashes),
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=packet,
                    root=root,
                )

    def test_commit_hashes_and_packet_completion_boundary_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            view, selection, packet, hashes = boundary(root)

            invalid = record(hashes)
            invalid["baseline_commit"] = "not-a-commit"
            with self.assertRaisesRegex(ValueError, "40-character Git commit"):
                MODULE.validate(
                    invalid,
                    routing_view=view,
                    routing_selection=selection,
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
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=packet,
                    root=root,
                )

    def test_review_scope_and_sample_must_be_nonempty(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            view, selection, packet, hashes = boundary(root)
            for field in ("reviewed_domains", "sampling_record"):
                with self.subTest(field=field):
                    value = record(hashes)
                    value[field] = []
                    with self.assertRaisesRegex(ValueError, f"{field} must not be empty"):
                        MODULE.validate(
                            value,
                            routing_view=view,
                            routing_selection=selection,
                            context_packet=packet,
                            root=root,
                        )

    def test_structured_snapshots_findings_and_automation_health_are_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            view, selection, packet, hashes = boundary(root)

            invalid_snapshot = record(hashes)
            invalid_snapshot["project_snapshot"]["sha256"] = "not-a-hash"
            with self.assertRaisesRegex(ValueError, "project_snapshot.sha256"):
                MODULE.validate(
                    invalid_snapshot,
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=packet,
                    root=root,
                )

            invalid_resolved = record(hashes)
            invalid_resolved["resolved_findings"] = [{"summary": "No stable identity"}]
            with self.assertRaisesRegex(ValueError, "nonblank stable id"):
                MODULE.validate(
                    invalid_resolved,
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=packet,
                    root=root,
                )

            invalid_health = record(hashes)
            invalid_health["automation_health"]["status"] = "unknown"
            with self.assertRaisesRegex(ValueError, "must be healthy, degraded, or failed"):
                MODULE.validate(
                    invalid_health,
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=packet,
                    root=root,
                )

    def test_finding_ids_are_unique_within_and_across_status_lists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            view, selection, packet, hashes = boundary(root)

            repeated = record(hashes)
            repeated["unresolved_findings"] = [
                {"id": "FINDING-1"},
                {"id": "FINDING-1"},
            ]
            with self.assertRaisesRegex(ValueError, "repeats finding IDs"):
                MODULE.validate(
                    repeated,
                    routing_view=view,
                    routing_selection=selection,
                    context_packet=packet,
                    root=root,
                )

            contradictory = record(hashes)
            contradictory["resolved_findings"] = [{"id": "FINDING-1"}]
            contradictory["unresolved_findings"] = [{"id": "FINDING-1"}]
            with self.assertRaisesRegex(ValueError, "may not appear in both"):
                MODULE.validate(
                    contradictory,
                    routing_view=view,
                    routing_selection=selection,
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
            packet_path = root / "packet.json"
            ledger = root / "epochs.jsonl"
            current = root / "current.json"
            input_path.write_text("{}\n", encoding="utf-8")
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
            ), patch.object(
                MODULE,
                "load_fixture_component_registry_routing_view",
                return_value={"validation_mode": "proposed_revision_validation"},
            ) as fixture_loader, patch.object(
                MODULE,
                "routed_configuration_documents_from_view",
                return_value={},
            ):
                with self.assertRaisesRegex(ValueError, "LEGACY-FINDING"):
                    MODULE.main(path_authority=path_authority)
            fixture_loader.assert_called_once_with(path_authority)
            self.assertEqual(len(ledger.read_text(encoding="utf-8").splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
