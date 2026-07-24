import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from arrp_context import (  # noqa: E402
    ContextError,
    build_context_packet,
    build_work_queue,
    extract_exact_heading,
    load_route_manifest,
    stable_work_id,
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class ExactContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "framework").mkdir()
        (self.root / "areas/TEST/issues").mkdir(parents=True)
        (self.root / "inventory").mkdir()
        self.document = self.root / "framework/rules.md"
        self.document.write_text(
            "# Rules\n\n## Selected\n\nRequired.\n\n### Child\n\nAlso required.\n\n## Other\n\nExcluded.\n",
            encoding="utf-8",
        )
        issue = self.root / "areas/TEST/issues/TEST-001.md"
        issue.write_text(
            "---\nissue_id: TEST-001\naudit_history: TEST-001.audit.md\n"
            'legislative_proposal: "../../../legislation/TEST-001.md"\n---\n# TEST-001\n',
            encoding="utf-8",
        )
        (self.root / "areas/TEST/issues/TEST-001.audit.md").write_text(
            "# Audit\n\n## Audit History\n\n### Newest\n\nLatest.\n\n### Older\n\nOld.\n",
            encoding="utf-8",
        )
        (self.root / "legislation").mkdir()
        (self.root / "legislation/TEST-001.md").write_text("# Vehicle\n", encoding="utf-8")
        (self.root / "inventory/sources.csv").write_text(
            "Source ID,Associated Record IDs,Title or Description\nSRC-0001,TEST-001,One\n"
            "SRC-0002,TEST-002,Two\n",
            encoding="utf-8",
        )
        (self.root / "inventory/sources-pending.csv").write_text(
            "Source ID,Associated Record IDs,Title or Description\n", encoding="utf-8"
        )
        (self.root / "inventory/github_issue_registry.csv").write_text(
            "GitHub Title,Canonical Record\nTEST-001: Test,areas/TEST/issues/TEST-001.md\n",
            encoding="utf-8",
        )
        digest = hashlib.sha256(self.document.read_bytes()).hexdigest()
        self.manifest = self.root / "manifest.json"
        write_json(
            self.manifest,
            {
                "schema_version": 1,
                "generated_path_exclusions": ["generated"],
                "documents": {"rules": {"path": "framework/rules.md", "sha256": digest}},
                "profiles": {
                    "issue": {
                        "max_bytes": 20000,
                        "sections": [
                            {
                                "document": "rules",
                                "heading": "## Selected",
                                "max_bytes": 1000,
                            }
                        ],
                    }
                },
            },
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_heading_includes_children_but_not_next_peer(self):
        content, start, end = extract_exact_heading(self.document.read_text(), "## Selected")
        self.assertIn("### Child", content)
        self.assertNotIn("## Other", content)
        self.assertEqual(start, 3)
        self.assertGreater(end, start)

    def test_context_packet_is_bounded_and_issue_specific(self):
        packet = build_context_packet(
            self.manifest, "issue", root=self.root, issue_id="TEST-001"
        )
        self.assertTrue(packet["provenance_complete"])
        self.assertEqual(packet["issue_dossier"]["sources"][0]["Source ID"], "SRC-0001")
        self.assertEqual(packet["issue_dossier"]["latest_audit_entry"]["heading"], "### Newest")
        self.assertIn("# Vehicle", packet["issue_dossier"]["linked_vehicle"]["content"])
        self.assertLessEqual(packet["limits"]["actual_bytes"], packet["limits"]["max_bytes"])

    def test_changed_hash_fails_closed(self):
        self.document.write_text(self.document.read_text() + "\nchanged\n", encoding="utf-8")
        with self.assertRaisesRegex(ContextError, "hash changed"):
            load_route_manifest(self.manifest, root=self.root)

    def test_missing_duplicate_and_oversized_sections_fail_closed(self):
        self.document.write_text("## Selected\none\n## Selected\ntwo\n", encoding="utf-8")
        digest = hashlib.sha256(self.document.read_bytes()).hexdigest()
        manifest = json.loads(self.manifest.read_text())
        manifest["documents"]["rules"]["sha256"] = digest
        write_json(self.manifest, manifest)
        with self.assertRaisesRegex(ContextError, "duplicated"):
            build_context_packet(self.manifest, "issue", root=self.root)
        self.document.write_text("## Selected\n" + "x" * 2000, encoding="utf-8")
        manifest["documents"]["rules"]["sha256"] = hashlib.sha256(
            self.document.read_bytes()
        ).hexdigest()
        write_json(self.manifest, manifest)
        with self.assertRaisesRegex(ContextError, "exceeds max_bytes"):
            build_context_packet(self.manifest, "issue", root=self.root)

    def test_generated_paths_and_placeholder_hashes_are_rejected(self):
        manifest = json.loads(self.manifest.read_text())
        manifest["documents"]["rules"] = {
            "path": "generated/catalog-data.js",
            "sha256": "__SET_AT_INTEGRATION__",
        }
        write_json(self.manifest, manifest)
        with self.assertRaisesRegex(ContextError, "excluded generated path"):
            load_route_manifest(self.manifest, root=self.root)


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.now = datetime(2026, 7, 24, 12, tzinfo=timezone.utc)

    def tearDown(self):
        self.temp.cleanup()

    def path(self, name: str, data: dict) -> Path:
        path = self.root / name
        write_json(path, data)
        return path

    def test_queue_uses_flags_cursor_fairness_recovery_and_epoch(self):
        integrity = self.path(
            "integrity.json",
            {
                "generated_at": "2026-07-24T11:00:00Z",
                "revision": "abc",
                "findings": [
                    {
                        "id": "warning-1",
                        "severity": "warning",
                        "attention": "human",
                        "message": "Missing human explanation",
                    }
                ],
            },
        )
        progress = self.path(
            "progress.json",
            {
                "generatedAt": "2026-07-24T11:00:00Z",
                "repositoryRevision": "abc",
                "asOf": "2026-01-01",
                "proposals": [
                    {
                        "identifier": "TEST-001",
                        "workflowStatus": "Development",
                        "nextAudit": "Continue drafting",
                    },
                    {
                        "identifier": "TEST-002",
                        "workflowStatus": "Audit needed",
                        "nextAudit": "Targeted Change Audit",
                        "changeAuditNeeded": True,
                    },
                ],
            },
        )
        intake = self.path(
            "intake.json",
            {
                "generated_at": "2026-07-24T11:00:00Z",
                "pending": True,
                "last_processed_id": "D-1",
                "items": [
                    {"id": "D-1", "state": "pending", "created_at": "2026-07-24"},
                    {
                        "id": "D-2",
                        "state": "pending",
                        "created_at": "2026-07-23",
                        "content_hash": "safe-hash",
                    },
                ],
            },
        )
        chain = self.path(
            "chain.json",
            {
                "completed_at": "2026-07-24T11:00:00Z",
                "final_revision": "abc",
                "bots": [
                    {"id": "source-checker-bot", "due": True, "status": "failed", "error": "timeout"}
                ],
            },
        )
        development_id = stable_work_id("issue_development", "TEST-001")
        recovery = self.path(
            "recovery.json",
            {
                "generated_at": "2026-07-24T11:00:00Z",
                "items": [
                    {
                        "work_id": development_id,
                        "state": "human_required",
                        "attempt_count": 3,
                        "continuation": "Resolve ambiguity",
                    }
                ],
            },
        )
        epoch = self.path(
            "epoch.json",
            {
                "completed_at": "2026-07-01T00:00:00Z",
                "epoch_id": "EPOCH-1",
                "baseline_revision": "old",
                "next_due_at": "2026-07-20T00:00:00Z",
                "unresolved_ids": ["X-1"],
            },
        )
        queue = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            recovery_path=recovery,
            review_epoch_path=epoch,
            now=self.now,
            input_root=self.root,
        )
        self.assertTrue(queue["ready_for_elim"])
        self.assertEqual(queue["items"][0]["kind"], "bot_failure")
        self.assertEqual(sum(item["kind"] == "public_intake" for item in queue["items"]), 1)
        self.assertTrue(any(item["kind"] == "comprehensive_review" for item in queue["items"]))
        development = next(item for item in queue["items"] if item["id"] == development_id)
        self.assertFalse(development["eligible_for_elim"])
        self.assertEqual(development["recovery"]["attempt_count"], 3)
        self.assertGreater(development["fairness_boost"], 0)

    def test_stale_or_revision_mismatched_inputs_block_launch(self):
        common = {"generated_at": "2026-01-01T00:00:00Z"}
        integrity = self.path("integrity.json", {**common, "revision": "a", "findings": []})
        progress = self.path(
            "progress.json", {**common, "repositoryRevision": "b", "proposals": []}
        )
        intake = self.path("intake.json", {**common, "items": []})
        chain = self.path(
            "chain.json", {**common, "final_revision": "c", "bots": []}
        )
        queue = build_work_queue(
            integrity_path=integrity,
            progress_path=progress,
            intake_path=intake,
            chain_path=chain,
            now=self.now,
            input_root=self.root,
        )
        self.assertFalse(queue["ready_for_elim"])
        self.assertFalse(queue["launch_recommended"])
        self.assertTrue(any("revision" in problem for problem in queue["problems"]))


class RepositorySearchBoundaryTests(unittest.TestCase):
    def test_generated_console_and_local_artifacts_are_excluded_from_ordinary_search(self):
        policy = (ROOT / ".rgignore").read_text(encoding="utf-8")
        self.assertIn("research/horizon-review-console/catalog-data.js", policy)
        self.assertIn("research/horizon-review-console/data/", policy)
        self.assertIn(".site-build/", policy)
        self.assertIn(".tmp/", policy)
        self.assertIn(".venv/", policy)

    def test_production_context_routes_are_hash_pinned_and_extractable(self):
        path = ROOT / "framework/agents/elim-context-routes.json"
        manifest = load_route_manifest(path, root=ROOT)
        for profile in manifest["profiles"].values():
            total = 0
            for route in profile["sections"]:
                document = manifest["documents"][route["document"]]
                content, _, _ = extract_exact_heading(
                    (ROOT / document["path"]).read_text(encoding="utf-8"),
                    route["heading"],
                )
                size = len(content.encode("utf-8"))
                self.assertLessEqual(size, route["max_bytes"])
                total += size
            self.assertLessEqual(total, profile["max_bytes"])


if __name__ == "__main__":
    unittest.main()
