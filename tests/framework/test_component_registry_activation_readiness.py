"""Deterministic tests for Component Registry candidate activation readiness."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

from scripts import component_registry as registry


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "framework" / "component-registry.json"
READINESS_PATH = ROOT / registry.ACTIVATION_READINESS_RECEIPT_PATH
CLOSURE_PATH = ROOT / registry.REQUIREMENT_CLOSURE_RECEIPT_PATH
STAGE1_CANONICAL_REVISION = "357293fc3bd814618fefdede91cd1008ce8683d8"


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_candidate_registry() -> tuple[dict[str, object], dict[str, object]]:
    current = load(REGISTRY_PATH)
    if current.get("schema_version") == 2:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "show",
                f"{STAGE1_CANONICAL_REVISION}:framework/component-registry.json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        current = json.loads(completed.stdout)
    if current.get("status") == "candidate":
        return current, current
    candidate_revision = current["approval"]["value"]["base_revision"]
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "show",
            f"{candidate_revision}:framework/component-registry.json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    candidate = json.loads(completed.stdout)
    if (
        candidate.get("status") != "candidate"
        or registry._canonical_registry_digest(candidate)
        != current["approval"]["value"]["candidate_registry_sha256"]
    ):
        raise AssertionError("active registry candidate parent is not exact")
    return current, candidate


def write_console_fixture(
    root: Path,
    *,
    oversized_domain: bool = False,
) -> dict[str, object]:
    closure = root / registry.REQUIREMENT_CLOSURE_RECEIPT_PATH
    closure.parent.mkdir(parents=True, exist_ok=True)
    closure.write_bytes(CLOSURE_PATH.read_bytes())
    data = root / registry.CONSOLE_DATA_DIRECTORY
    data.mkdir(parents=True, exist_ok=True)
    name = "component-registry.js"
    value = ("x" * (2 * 1024 * 1024 + 1)) if oversized_domain else "ok"
    payload = {
        "component_registry": [{"value": value}],
        "domain_generation": {name: "project-console-test"},
    }
    domain_text = (
        registry.CONSOLE_DOMAIN_PREFIX
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ");\n"
    )
    domain_path = data / name
    domain_path.write_text(domain_text, encoding="utf-8")
    domain = {
        "file": name,
        "sha256": f"sha256:{registry._sha256(domain_path)}",
        "bytes": domain_path.stat().st_size,
        "keys": ["component_registry"],
        "record_count": 1,
    }
    manifest = {
        "manifest_schema_version": 1,
        "generation_id": "project-console-test",
        "generated_at": "2026-07-30T12:00:00Z",
        "source_revision": "b" * 40,
        "availability": "current",
        "completeness": {
            "complete": True,
            "expected_count": 1,
            "actual_count": 1,
            "missing_count": 0,
        },
        "domain_count": 1,
        "domains": [domain],
        "files": {
            name: {
                "generation_id": "project-console-test",
                **{
                    key: value
                    for key, value in domain.items()
                    if key != "file"
                },
            },
        },
    }
    manifest_path = root / registry.CONSOLE_GENERATION_MANIFEST_PATH
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    source_hashes = {
        registry.REQUIREMENT_CLOSURE_RECEIPT_PATH: (
            f"sha256:{registry._sha256(closure)}"
        ),
        "feed:synthetic": f"sha256:{'1' * 64}",
    }
    catalog = {
        "generation_id": manifest["generation_id"],
        "generated_at": manifest["generated_at"],
        "source_revision": manifest["source_revision"],
        "availability": manifest["availability"],
        "completeness": manifest["completeness"],
        "source_hashes": source_hashes,
        "generation_manifest": manifest,
    }
    catalog_path = root / registry.CONSOLE_CATALOG_PATH
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        registry.CONSOLE_CATALOG_PREFIX
        + json.dumps(catalog, ensure_ascii=False)
        + ";\n",
        encoding="utf-8",
    )
    return {
        "catalog": catalog_path,
        "manifest": manifest_path,
        "domain": domain_path,
    }


class HistoricalComponentRegistryActivationReadinessTests:
    @classmethod
    def setUpClass(cls) -> None:
        cls.current, cls.candidate = load_candidate_registry()
        cls.readiness = load(READINESS_PATH)
        cls.closure = load(CLOSURE_PATH)

    def test_requirement_catalog_is_exact_contiguous_and_design_bound(self):
        registry.validate_requirement_closure_receipt(self.closure)
        self.assertEqual(
            self.closure["source_design"],
            {
                "document_id": "CR-PROPOSAL-2026-001",
                "revision": 15,
                "sha256": (
                    "95e6a67263a7ef228e395f8a9429ba1082d874d79939d"
                    "95269d9f5d91d4f7a0d"
                ),
                "section": "Registry enforcement requirements",
                "requirement_count": 77,
                "normalization": (
                    "markdown_continuation_whitespace_only"
                ),
            },
        )
        self.assertEqual(
            self.closure["implementation_blueprint"]["sha256"],
            (
                "a3dd3fa31c3e02b5fbddc89b1aa293ec0164e667d45f"
                "4142ebaa884020989ac8"
            ),
        )
        rows = self.closure["rows"]
        self.assertEqual(
            [row["cr_id"] for row in rows],
            [f"CR-{ordinal:03d}" for ordinal in range(1, 78)],
        )
        self.assertEqual(
            [row["ordinal"] for row in rows],
            list(range(1, 78)),
        )
        self.assertEqual(
            len({row["design_requirement"] for row in rows}),
            77,
        )

    def test_stage_boundaries_are_explicit_not_false_passes(self):
        rows = {
            row["ordinal"]: row
            for row in self.closure["rows"]
        }
        for ordinal in (9, 14, 65, 66):
            self.assertEqual(
                rows[ordinal]["pre_activation_result"],
                "deferred_by_approved_stage_boundary",
            )
            self.assertEqual(
                rows[ordinal]["approved_deferral"],
                "deferred_by_approved_stage_boundary",
            )
        for ordinal in range(67, 78):
            self.assertEqual(
                rows[ordinal]["approved_deferral"],
                "deferred_by_approved_stage_boundary",
            )
            self.assertIn(
                "mutation_not_activated",
                rows[ordinal]["pre_activation_result"],
            )
        self.assertTrue(
            all(row["exception_status"] == "" for row in rows.values())
        )

    def test_requirement_mutations_fail_closed(self):
        for mutation in ("missing", "duplicate", "wording"):
            altered = copy.deepcopy(self.closure)
            if mutation == "missing":
                altered["rows"].pop()
            elif mutation == "duplicate":
                altered["rows"][1]["design_requirement"] = altered[
                    "rows"
                ][0]["design_requirement"]
            else:
                altered["rows"][0]["design_requirement"] += " altered"
                altered["rows"][1]["design_requirement"] = altered[
                    "rows"
                ][0]["design_requirement"]
            with self.subTest(mutation=mutation), self.assertRaises(
                registry.RegistryError
            ):
                registry.validate_requirement_closure_receipt(altered)

    def test_future_tree_is_complete_unique_and_dispositioned(self):
        future = self.readiness["future_tree"]
        self.assertTrue(future["complete"])
        self.assertEqual(future["source_count"], len(future["items"]))
        self.assertEqual(
            future["future_count"],
            len({item["future_path"] for item in future["items"]}),
        )
        current_paths = set(
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(ROOT),
                    "ls-tree",
                    "-r",
                    "--name-only",
                    STAGE1_CANONICAL_REVISION,
                ],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
        )
        if self.current["status"] == "active":
            for specification in registry.ROUTING_PREDECESSOR_PATHS.values():
                current_paths.remove(specification["archived_path"])
                current_paths.add(specification["historical_path"])
        self.assertEqual(
            {item["source_path"] for item in future["items"]},
            current_paths,
        )
        references = self.readiness["reference_dispositions"]
        self.assertTrue(references["complete"])
        baseline = references["replacement_baseline"]
        self.assertEqual(
            baseline["finding_count"],
            len(baseline["items"]),
        )
        self.assertTrue(
            all(item["disposition"] for item in baseline["items"])
        )
        self.assertEqual(
            baseline["disposition_classifier"],
            {
                "schema_version": 1,
                "complete": True,
                "source_revision": (
                    "0b394db1bdfbe8a76632e56bf5ed8587714e7ce2"
                ),
                "disposition_counts": (
                    registry.REFERENCE_DISPOSITION_COUNTS
                ),
            },
        )
        self.assertEqual(
            dict(
                sorted(
                    Counter(
                        item["disposition"]
                        for item in baseline["items"]
                    ).items()
                )
            ),
            registry.REFERENCE_DISPOSITION_COUNTS,
        )

    def test_ignored_inventory_is_exact_and_content_was_not_read(self):
        ignored = self.readiness["ignored_artifacts"]
        self.assertTrue(ignored["complete"])
        self.assertFalse(ignored["content_read"])
        self.assertEqual(ignored["count"], 9)
        self.assertEqual(
            len({item["path"] for item in ignored["items"]}),
            9,
        )

    def test_simulated_active_model_is_exact_and_nonauthorizing(self):
        modeled = self.readiness["simulated_active"]
        self.assertTrue(modeled["complete"])
        self.assertEqual(
            modeled["counts"],
            self.candidate["activation_readiness"][
                "simulated_active_counts"
            ],
        )
        self.assertEqual(modeled["predecessor_ids"], [
            "project_structure",
            "context_routing",
            "repository_map",
            "context_routes_source",
        ])
        self.assertEqual(
            set(modeled["stage1_namespace_states"].values()),
            {"active"},
        )
        self.assertFalse(modeled["executable"])
        self.assertEqual(self.candidate["status"], "candidate")
        self.assertFalse(
            self.candidate["context_routing"]["authoritative"]
        )

    def test_readiness_receipt_is_exact_registry_bound(self):
        if self.current["status"] == "active":
            self.assertEqual(
                self.readiness["registry_binding"],
                {
                    "registry_id": "COMPONENT-REGISTRY",
                    "registry_revision": self.current["registry_revision"],
                    "status": "candidate",
                    "authoritative": False,
                    "executable": False,
                    "canonical_sha256": self.current["approval"]["value"][
                        "candidate_registry_sha256"
                    ],
                },
            )
            self.assertEqual(len(self.closure["rows"]), 77)
            return
        registry._validate_activation_readiness_receipts(
            self.candidate,
            root=ROOT,
        )
        report = registry.activation_readiness_report(
            self.candidate,
            root=ROOT,
        )
        self.assertTrue(report["complete"])
        self.assertFalse(report["authoritative"])
        self.assertFalse(report["executable"])
        self.assertEqual(report["requirement_count"], 77)
        self.assertEqual(report["exception_count"], 0)
        self.assertEqual(
            report["activation_decision"],
            "pending_human_activation",
        )

    def test_candidate_projection_does_not_consult_terminal_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            closure = root / registry.REQUIREMENT_CLOSURE_RECEIPT_PATH
            closure.parent.mkdir(parents=True)
            closure.write_bytes(CLOSURE_PATH.read_bytes())
            terminal = root / registry.ACTIVATION_READINESS_RECEIPT_PATH
            terminal.write_text("first", encoding="utf-8")
            original = registry._load_public_readiness_receipt

            def guarded_loader(
                candidate_root: Path,
                relative: str,
                label: str,
            ):
                if relative == registry.ACTIVATION_READINESS_RECEIPT_PATH:
                    raise AssertionError("terminal receipt was consulted")
                return original(candidate_root, relative, label)

            with mock.patch.object(
                registry,
                "_load_public_readiness_receipt",
                side_effect=guarded_loader,
            ):
                first = registry.activation_readiness_report(
                    self.candidate,
                    root=root,
                )
                terminal.write_text("second", encoding="utf-8")
                second = registry.activation_readiness_report(
                    self.candidate,
                    root=root,
                )
            self.assertEqual(first, second)
            self.assertEqual(first["requirement_count"], 77)

    def test_terminal_console_readback_binds_complete_public_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = write_console_fixture(root, oversized_domain=True)
            readback = registry.build_console_generation_readback(root=root)
            self.assertTrue(readback["complete"])
            self.assertEqual(readback["domain_count"], 1)
            self.assertGreater(readback["domains"][0]["bytes"], 2 * 1024 * 1024)
            self.assertNotIn(
                registry.ACTIVATION_READINESS_RECEIPT_PATH,
                json.loads(
                    paths["catalog"]
                    .read_text(encoding="utf-8")
                    .removeprefix(registry.CONSOLE_CATALOG_PREFIX)
                    .removesuffix(";\n")
                )["source_hashes"],
            )
            self.assertEqual(
                readback["public_file_set"],
                [
                    registry.CONSOLE_CATALOG_PATH,
                    registry.CONSOLE_GENERATION_MANIFEST_PATH,
                    (
                        f"{registry.CONSOLE_DATA_DIRECTORY}/"
                        "component-registry.js"
                    ),
                ],
            )

    def test_terminal_console_readback_rejects_bundle_mutations(self):
        for mutation in ("catalog", "manifest", "domain", "extra"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                paths = write_console_fixture(root)
                registry.build_console_generation_readback(root=root)
                if mutation == "catalog":
                    paths["catalog"].write_text(
                        paths["catalog"].read_text(encoding="utf-8") + " ",
                        encoding="utf-8",
                    )
                elif mutation == "manifest":
                    value = json.loads(
                        paths["manifest"].read_text(encoding="utf-8")
                    )
                    value["generation_id"] = "project-console-changed"
                    paths["manifest"].write_text(
                        json.dumps(value, indent=2) + "\n",
                        encoding="utf-8",
                    )
                elif mutation == "domain":
                    paths["domain"].write_text(
                        paths["domain"].read_text(encoding="utf-8").replace(
                            '"ok"',
                            '"changed"',
                        ),
                        encoding="utf-8",
                    )
                else:
                    (
                        root / registry.CONSOLE_DATA_DIRECTORY / "extra.js"
                    ).write_text("public extra", encoding="utf-8")
                with self.assertRaises(registry.RegistryError):
                    registry.build_console_generation_readback(root=root)

    def test_readiness_receipt_has_one_deterministic_fixed_builder(self):
        if self.current["status"] == "active":
            self.assertEqual(
                self.readiness["registry_binding"]["canonical_sha256"],
                self.current["approval"]["value"][
                    "candidate_registry_sha256"
                ],
            )
            self.assertTrue(self.readiness["future_tree"]["complete"])
            self.assertTrue(
                self.readiness["reference_dispositions"]["complete"]
            )
            self.assertTrue(self.readiness["simulated_active"]["complete"])
            return
        rebuilt = registry.build_activation_readiness_receipt(
            self.candidate,
            root=ROOT,
        )
        self.assertEqual(
            rebuilt["registry_binding"],
            self.readiness["registry_binding"],
        )
        self.assertEqual(
            rebuilt["created_artifacts"],
            self.readiness["created_artifacts"],
        )
        self.assertEqual(
            rebuilt["ignored_artifacts"],
            self.readiness["ignored_artifacts"],
        )
        self.assertEqual(
            rebuilt["simulated_active"],
            self.readiness["simulated_active"],
        )
        self.assertEqual(
            rebuilt["reference_dispositions"],
            self.readiness["reference_dispositions"],
        )

    def test_historical_reference_evidence_is_exactly_count_only(self):
        historical = self.readiness["reference_dispositions"][
            "historical_preflight"
        ]
        self.assertEqual(
            historical,
            registry.HISTORICAL_REFERENCE_EVIDENCE,
        )
        self.assertEqual(historical["finding_count"], 773)
        self.assertEqual(
            historical["state_counts"],
            {"requires_rewrite_or_historical_classification": 773},
        )
        self.assertEqual(len(historical["alias_counts"]), 17)
        self.assertEqual(
            sum(historical["alias_counts"].values()),
            773,
        )
        self.assertEqual(
            historical["identity_completeness"],
            "unavailable",
        )
        self.assertFalse(historical["identity_preservation_claim"])
        self.assertEqual(
            historical["partial_capture"]["identity_count"],
            167,
        )
        self.assertFalse(historical["partial_capture"]["complete"])

    def test_replacement_reference_baseline_is_reproducibly_bound(self):
        replacement = self.readiness["reference_dispositions"][
            "replacement_baseline"
        ]
        bindings = replacement["bindings"]
        self.assertEqual(
            replacement["finding_count"],
            len(replacement["items"]),
        )
        self.assertEqual(
            len(
                {
                    item["reference_id"]
                    for item in replacement["items"]
                }
            ),
            replacement["finding_count"],
        )
        self.assertEqual(
            bindings["input_manifest_sha256"],
            bindings["input_manifest"]["canonical_sha256"],
        )
        self.assertEqual(
            bindings["sorted_identity_set_sha256"],
            hashlib.sha256(
                registry.canonical_json(
                    sorted(
                        item["reference_id"]
                        for item in replacement["items"]
                    )
                ).encode("utf-8")
            ).hexdigest(),
        )
        registry._validate_reference_baseline_evidence(
            self.readiness,
            self.candidate,
            root=ROOT,
        )

    def test_reference_baseline_mutations_fail_closed(self):
        mutations = {
            "historical_complete": lambda receipt: receipt[
                "reference_dispositions"
            ]["historical_preflight"].update(
                {"identity_completeness": "complete"}
            ),
            "preservation_claim": lambda receipt: receipt[
                "reference_dispositions"
            ]["historical_preflight"].update(
                {"identity_preservation_claim": True}
            ),
            "input_digest": lambda receipt: receipt[
                "reference_dispositions"
            ]["replacement_baseline"]["bindings"].update(
                {"input_manifest_sha256": "0" * 64}
            ),
            "item_disposition": lambda receipt: receipt[
                "reference_dispositions"
            ]["replacement_baseline"]["items"][0].update(
                {"disposition": "invented"}
            ),
            "classification_source": lambda receipt: receipt[
                "reference_dispositions"
            ]["replacement_baseline"]["disposition_classifier"].update(
                {"source_revision": "0" * 40}
            ),
        }
        for name, mutate in mutations.items():
            altered = copy.deepcopy(self.readiness)
            mutate(altered)
            with self.subTest(name=name), self.assertRaises(
                registry.RegistryError
            ):
                registry._validate_reference_baseline_evidence(
                    altered,
                    self.candidate,
                    root=ROOT,
                )


class ComponentRegistryV4ConfigurationReadinessTests(unittest.TestCase):
    def setUp(self):
        self.registry = load(REGISTRY_PATH)

    def test_v4_configuration_is_complete_without_a_legacy_readiness_namespace(self):
        result = registry.validate_v4_registry(self.registry, root=ROOT)
        self.assertTrue(result["valid"])
        self.assertNotIn("activation_readiness", self.registry)
        self.assertEqual(result["component_count"], 105)
        self.assertEqual(result["terminology_count"], 87)

    def test_configuration_view_is_exact_v4_and_not_live_authority(self):
        view = registry.load_component_registry_configuration_routing_view()
        self.assertEqual(view["schema_version"], 4)
        self.assertEqual(view["registry_revision"], 4)
        self.assertEqual(view["validation_mode"], "adopted_configuration_validation")
        self.assertFalse(view["authoritative"])
        self.assertFalse(view["executable"])
        self.assertFalse(view["activation_receipt_consulted"])
        self.assertTrue(view["source_bytes_current"])

    def test_malformed_versions_fail_before_configuration_readiness(self):
        for value in (None, True, 1, 2, 3, 5, "4"):
            altered = copy.deepcopy(self.registry)
            altered["schema_version"] = value
            with self.subTest(value=value), self.assertRaises(registry.RegistryError):
                registry.validate_v4_registry(
                    altered, root=ROOT, compare_codeowners=False
                )


if __name__ == "__main__":
    unittest.main()
