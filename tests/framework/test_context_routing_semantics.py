import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.arrp_context import build_context_packet


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ContextRoutingPacketSemanticsTests(unittest.TestCase):
    def test_packet_emits_complete_typed_routing_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            framework = root / "framework"
            framework.mkdir()
            (framework / "records" / "automation").mkdir(parents=True)
            kernel = framework / "kernel.md"
            current = framework / "current.md"
            operation = framework / "operation.md"
            kernel.write_text("# Kernel\n", encoding="utf-8")
            current.write_text("# Current\n", encoding="utf-8")
            operation.write_text("# Operation\n", encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest = {
                "schema_version": 2,
                "generated_path_exclusions": ["generated"],
                "required_modules": ["kernel", "current"],
                "documents": {
                    "kernel": {
                        "path": "framework/kernel.md",
                        "sha256": digest(kernel),
                        "hash_policy": "pinned",
                        "governing": True,
                        "requires": [],
                    },
                    "current": {
                        "path": "framework/current.md",
                        "hash_policy": "runtime",
                        "governing": False,
                        "requires": ["kernel"],
                    },
                    "operation": {
                        "path": "framework/operation.md",
                        "sha256": digest(operation),
                        "hash_policy": "pinned",
                        "governing": True,
                        "requires": ["kernel"],
                    },
                },
                "capabilities": {
                    "operation": ["operation"],
                },
                "profiles": {
                    "task": {
                        "max_bytes": 100_000,
                        "modules": [],
                        "capabilities": ["operation"],
                    },
                },
            }
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n",
                encoding="utf-8",
            )

            packet = build_context_packet(
                manifest_path,
                "task",
                root=root,
            )

            routing = packet["routing_manifest"]
            self.assertEqual(
                set(routing),
                {
                    "registry_id",
                    "registry_path",
                    "registry_revision",
                    "validation_mode",
                    "authoritative",
                    "executable",
                    "registry_digest",
                    "selected_profile",
                    "selected_capabilities",
                    "resolved_document_revisions",
                    "resolved_document_digests",
                    "resolved_document_order",
                    "dependency_closure",
                    "exact_sections",
                    "dynamic_expansions",
                    "inclusion_reasons",
                },
            )
            self.assertEqual(routing["registry_revision"], 2)
            self.assertEqual(routing["registry_id"], "context-routes")
            self.assertEqual(routing["registry_path"], "manifest.json")
            self.assertEqual(
                routing["validation_mode"],
                "predecessor_routing",
            )
            self.assertTrue(routing["authoritative"])
            self.assertTrue(routing["executable"])
            self.assertEqual(
                routing["registry_digest"],
                digest(manifest_path),
            )
            self.assertEqual(routing["selected_profile"], "task")
            self.assertEqual(
                routing["selected_capabilities"],
                ["operation"],
            )
            self.assertEqual(
                set(routing["resolved_document_revisions"]),
                {"kernel", "current", "operation"},
            )
            self.assertEqual(
                set(routing["resolved_document_digests"]),
                {"kernel", "current", "operation"},
            )
            self.assertEqual(
                routing["resolved_document_order"],
                ["kernel", "current", "operation"],
            )
            self.assertEqual(
                routing["dependency_closure"],
                {
                    "kernel": [],
                    "current": ["kernel"],
                    "operation": ["kernel"],
                },
            )
            self.assertEqual(routing["exact_sections"], [])
            self.assertEqual(routing["dynamic_expansions"], [])
            self.assertEqual(
                set(routing["inclusion_reasons"]),
                {"kernel", "current", "operation"},
            )
            self.assertIn(
                "profile task capability operation",
                routing["inclusion_reasons"]["operation"],
            )
            self.assertIn(
                "required floor",
                routing["inclusion_reasons"]["current"],
            )


if __name__ == "__main__":
    unittest.main()
