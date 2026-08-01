import copy
import importlib.util
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from scripts import component_registry as component_registry_tool


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_project_console.py"
SPEC = importlib.util.spec_from_file_location("console_data_contract_builder", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

CONTRACT_SCRIPT = ROOT / "scripts" / "console_data_contracts.py"
CONTRACT_SPEC = importlib.util.spec_from_file_location(
    "console_data_contract_helpers", CONTRACT_SCRIPT
)
CONTRACTS = importlib.util.module_from_spec(CONTRACT_SPEC)
assert CONTRACT_SPEC.loader is not None
CONTRACT_SPEC.loader.exec_module(CONTRACTS)


def candidate_registry_fixture() -> dict[str, object]:
    current = json.loads(MODULE.COMPONENT_REGISTRY.read_text(encoding="utf-8"))
    if current.get("status") == "candidate":
        return current
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
        or component_registry_tool._canonical_registry_digest(candidate)
        != current["approval"]["value"]["candidate_registry_sha256"]
    ):
        raise AssertionError("active registry candidate parent is not exact")
    return candidate


class ConsoleDataContractTests(unittest.TestCase):
    def component_registry_view(
        self,
        registry: dict[str, object],
        *,
        status: str,
    ) -> dict[str, object]:
        routing = registry["context_routing"]
        route = {
            "schema_version": routing["schema_version"],
            "generated_path_exclusions": routing[
                "generated_path_exclusions"
            ],
            "required_modules": routing["required_modules"],
            "documents": routing["documents"],
            "capabilities": routing["capabilities"],
            "profiles": routing["profiles"],
        }
        candidate = status == "candidate"
        registry_sha256 = hashlib.sha256(
            MODULE.component_registry_canonical_json(registry).encode(
                "utf-8"
            )
        ).hexdigest()
        return {
            "schema_version": 1,
            "validation_mode": (
                "candidate_validation_only"
                if candidate
                else "active_configuration_validation_only"
            ),
            "registry_id": registry["registry_id"],
            "registry_revision": registry["registry_revision"],
            "registry_status": status,
            "registry_sha256": registry_sha256,
            "routing_authority_sha256": (
                routing["source_import"]["sha256"]
                if candidate
                else registry_sha256
            ),
            "registry_path": "framework/component-registry.json",
            "authoritative": False,
            "executable": False,
            "live_activation_verified": False,
            "activation_receipt_consulted": False,
            "predecessor_route_consulted": candidate,
            "route": route,
            "_validated_registry": registry,
        }

    def codex_usage_projection(self) -> dict[str, object]:
        return {
            "schema_version": 2,
            "projection_id": "codex-usage",
            "producer_id": "owner-local-codex-usage-sampler",
            "sampler_cadence_seconds": 1800,
            "generated_at": "2026-07-29T20:20:00Z",
            "trustworthy_through": "2026-07-29T20:47:00Z",
            "availability": "current",
            "completeness": "complete",
            "reason_code": None,
            "current_through": "2026-07-29T20:17:00Z",
            "current": {
                "observed_at": "2026-07-29T20:17:00Z",
                "plan_type": "pro",
                "used_percent": 28,
                "remaining_percent": 72,
                "window_minutes": 10080,
                "resets_at": 1785908741,
                "reset_identity": "10080:29765145",
            },
            "history": [
                {
                    "observed_at": "2026-07-29T19:47:00Z",
                    "event_type": "baseline",
                    "plan_type": "pro",
                    "used_percent": 27,
                    "remaining_percent": 73,
                    "window_minutes": 10080,
                    "resets_at": 1785908741,
                    "reset_identity": "10080:29765145",
                }
            ],
            "reset_windows": [
                {
                    "reset_identity": "10080:29765145",
                    "first_observed": "2026-07-29T19:47:00Z",
                    "last_observed": "2026-07-29T20:17:00Z",
                    "window_minutes": 10080,
                    "resets_at": 1785908741,
                    "plan_types": ["pro"],
                    "min_used_percent": 27,
                    "max_used_percent": 28,
                    "observation_count": 2,
                    "material": True,
                }
            ],
            "anomalies": [],
            "estimates": {
                "available": True,
                "budget_available": True,
                "budget_reason_code": None,
                "burn_rate_available": False,
                "burn_rate_reason_code": "insufficient_observation_coverage",
                "coverage_hours": 0.5,
                "sample_count": 2,
                "average_percent_per_day": None,
                "projected_exhaustion_at": None,
                "remaining_percent_per_day_budget": 10.1,
                "confidence": "unavailable",
            },
        }

    def test_codex_usage_projection_has_strict_nested_schema(self):
        payload = self.codex_usage_projection()
        checked_at = datetime(2026, 7, 29, 20, 20, tzinfo=timezone.utc)
        self.assertTrue(
            MODULE.valid_codex_usage_projection(payload, now=checked_at)
        )
        altered = json.loads(json.dumps(payload))
        altered["current"]["prompt"] = "not allowed"
        self.assertFalse(
            MODULE.valid_codex_usage_projection(altered, now=checked_at)
        )
        altered = json.loads(json.dumps(payload))
        altered["reset_windows"][0]["observation_count"] = True
        self.assertFalse(
            MODULE.valid_codex_usage_projection(altered, now=checked_at)
        )
        altered = json.loads(json.dumps(payload))
        altered["estimates"]["available"] = False
        self.assertFalse(
            MODULE.valid_codex_usage_projection(altered, now=checked_at)
        )
        altered = json.loads(json.dumps(payload))
        altered["estimates"]["average_percent_per_day"] = 2
        self.assertFalse(
            MODULE.valid_codex_usage_projection(altered, now=checked_at)
        )

    def test_codex_usage_unavailable_projection_retains_exact_shape(self):
        payload = MODULE.unavailable_codex_usage_projection()
        self.assertTrue(MODULE.valid_codex_usage_projection(payload))
        self.assertEqual(MODULE.codex_usage_projection(), payload)
        self.assertFalse(payload["estimates"]["available"])
        self.assertFalse(payload["estimates"]["budget_available"])
        self.assertFalse(payload["estimates"]["burn_rate_available"])
        self.assertIsNone(payload["estimates"]["remaining_percent_per_day_budget"])
        self.assertIsNone(payload["estimates"]["average_percent_per_day"])

    def test_status_projection_contract_distinguishes_complete_from_partial(self):
        complete = CONTRACTS.status_projection_contract(6)
        self.assertEqual(complete["availability"], "current")
        self.assertTrue(complete["completeness"]["complete"])
        self.assertEqual(complete["actual_count"], 6)

        partial = CONTRACTS.status_projection_contract(6, 5)
        self.assertEqual(partial["availability"], "stale")
        self.assertFalse(partial["completeness"]["complete"])
        self.assertEqual(partial["completeness"]["missing_count"], 1)

        for invalid in (True, -1, 1.5):
            with self.assertRaises(ValueError):
                CONTRACTS.status_projection_contract(invalid)

    def test_snapshot_override_rejects_paths_outside_trusted_roots(self):
        with self.assertRaisesRegex(RuntimeError, "fixed repository staging file"):
            MODULE.read_trusted_snapshot_file(
                "/etc/hosts",
                environment_name="ARRP_PROGRESS_SNAPSHOT",
            )

    def test_hash_helper_rejects_files_outside_declared_root(self):
        with (
            tempfile.TemporaryDirectory() as first,
            tempfile.TemporaryDirectory() as second,
        ):
            root = Path(first)
            outside = Path(second) / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "outside"):
                CONTRACTS.file_sha256(root, outside)

    def test_repository_authority_prefers_expected_source_revision_before_age(self):
        old = {
            "generated_at": "2026-07-25T13:00:00+00:00",
            "source_revision": "older",
            "generation_id": "old-generation",
            "completeness": {"complete": True},
        }
        current = {
            "generated_at": "2026-07-25T12:00:00+00:00",
            "source_revision": "reviewed-head",
            "generation_id": "current-generation",
            "completeness": {"complete": True},
        }
        completed = MODULE.subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr=""
        )
        with mock.patch.object(MODULE.subprocess, "run", return_value=completed):
            selected = MODULE.newest_snapshot(
                [old, current],
                authority="repository_revision",
                expected_revision="reviewed-head",
            )
        self.assertIs(selected, current)

    def test_project_authority_prefers_newer_complete_sync_not_repository_head(self):
        newer_project_sync = {
            "generated_at": "2026-07-25T13:00:00+00:00",
            "source_revision": "older-repository-revision",
            "generation_id": "newer-project-generation",
            "completeness": {"complete": True},
        }
        older_head_build = {
            "generated_at": "2026-07-25T12:00:00+00:00",
            "source_revision": "reviewed-head",
            "generation_id": "older-head-generation",
            "completeness": {"complete": True},
        }
        selected = MODULE.newest_snapshot(
            [newer_project_sync, older_head_build],
            authority="generation",
            expected_revision="reviewed-head",
        )
        self.assertIs(selected, newer_project_sync)
        currentness = MODULE.with_project_generation_currentness(selected)
        self.assertTrue(currentness["currentness"]["current"])
        self.assertEqual(
            currentness["currentness"]["authority"],
            "authenticated_project_generation",
        )

    def test_repository_supersession_is_immediate_even_under_48_hours(self):
        payload = {
            "generated_at": "2026-07-25T11:30:00+00:00",
            "source_revision": "prior-head",
            "generation_id": "integrity-prior-head",
            "availability": "current",
            "completeness": {"complete": True},
            "freshness": {
                "equivalent_source_revisions": ["authoritative-head"],
            },
        }
        projected = MODULE.with_repository_revision_currentness(
            payload,
            expected_revision="authoritative-head",
        )
        self.assertEqual(projected["availability"], "stale")
        self.assertEqual(projected["producer_availability"], "current")
        self.assertFalse(projected["currentness"]["current"])
        self.assertEqual(
            projected["currentness"]["producer_source_revision"],
            "prior-head",
        )
        self.assertEqual(
            projected["currentness"]["expected_source_revision"],
            "authoritative-head",
        )

    def test_integrity_accepts_only_sole_parent_manifested_console_outputs(self):
        parent = "a" * 40
        head = "b" * 40
        domain_path = (
            "framework/project/interfaces/project-console/data/overview.js"
        )
        manifest = json.dumps({
            "manifest_schema_version": 1,
            "generation_id": "project-console-test",
            "availability": "current",
            "completeness": {"complete": True},
            "domain_count": 1,
            "domains": [{"file": "overview.js", "sha256": "1" * 64}],
            "files": {"overview.js": {"sha256": "1" * 64}},
        })

        def result_for(changed, *, ancestry=None, tree_mode="100644"):
            def fake_git_text(root, arguments):
                if arguments[:4] == ["rev-list", "--parents", "-n", "1"]:
                    return ancestry or f"{head} {parent}\n"
                if arguments[:1] == ["show"]:
                    return manifest
                if arguments[:2] == ["ls-tree", parent] or arguments[:2] == [
                    "ls-tree",
                    head,
                ]:
                    return f"{tree_mode} blob {'2' * 40}\t{domain_path}\n"
                if arguments[:3] == ["diff", "--name-only", "--no-renames"]:
                    return "\0".join(changed) + "\0"
                raise AssertionError(f"unexpected Git query: {arguments}")

            with (
                mock.patch.object(
                    MODULE,
                    "current_repository_head",
                    return_value=head,
                ),
                mock.patch.object(
                    MODULE,
                    "_git_console_text",
                    side_effect=fake_git_text,
                ),
            ):
                return MODULE.integrity_parent_output_equivalent(
                    parent,
                    head,
                    root=ROOT,
                )

        self.assertTrue(result_for([
            MODULE.CONSOLE_GENERATION_CATALOG_PATH,
            MODULE.CONSOLE_GENERATION_MANIFEST_PATH,
            domain_path,
            "framework/status/integrity/project-integrity-report.md",
            "framework/status/sources/source-checker-report.md",
        ]))
        self.assertFalse(result_for(["scripts/build_project_console.py"]))
        self.assertFalse(result_for([
            "framework/project/interfaces/project-console/data/nested/overview.js"
        ]))
        self.assertFalse(result_for(
            [domain_path],
            ancestry=f"{head} {parent} {'c' * 40}\n",
        ))
        self.assertFalse(result_for([domain_path], tree_mode="120000"))
        with (
            mock.patch.object(
                MODULE,
                "current_repository_head",
                return_value=head,
            ),
            mock.patch.object(
                MODULE,
                "_git_console_text",
                return_value=f"{head} {'c' * 40}\n",
            ),
        ):
            self.assertFalse(MODULE.integrity_parent_output_equivalent(
                parent,
                head,
                root=ROOT,
            ))

    def public_source_checker_fixture(
        self,
        root: Path,
    ) -> tuple[Path, Path, dict[str, object], str]:
        catalog = root / "inventory" / "sources.csv"
        catalog.parent.mkdir(parents=True)
        catalog.write_text(
            "Source ID,URL,Title or Description,Authority / Publisher\n"
            "SRC-1,https://example.test/1,One,Publisher\n",
            encoding="utf-8",
        )
        config = root / "source-checker-config.json"
        config.write_text(
            json.dumps(
                {
                    "catalogs": ["inventory/sources.csv"],
                    "idField": "Source ID",
                    "urlField": "URL",
                }
            ),
            encoding="utf-8",
        )
        stage = root / ".tmp" / "project-console-source-checker.json"
        stage.parent.mkdir()
        revision = "a" * 40
        hashes = CONTRACTS.source_hashes(root, [catalog])
        payload: dict[str, object] = {
            "schema_version": 2,
            "contract_schema_version": 1,
            "agent_id": "source-checker-bot",
            "mode": "report-only",
            "checked_at": "2026-07-30T12:00:00+00:00",
            "generation_id": "source-checker-test-generation",
            "source_revision": revision,
            "source_hashes": hashes,
            "catalogs": ["inventory/sources.csv"],
            "expected_count": 1,
            "actual_count": 1,
            "availability": "current",
            "completeness": {
                "complete": True,
                "expected_count": 1,
                "actual_count": 1,
                "missing_count": 0,
            },
            "pagination": {
                "complete": True,
                "sources": [
                    {
                        "source": "inventory/sources.csv",
                        "complete": True,
                        "expected_count": 1,
                        "actual_count": 1,
                    }
                ],
            },
            "projection_errors": [],
            "eligible_urls": 1,
            "counts": {"verified": 1},
            "results": [
                {
                    "source_id": "SRC-1",
                    "catalog": "inventory/sources.csv",
                    "classification": "verified",
                }
            ],
            "missing_source_ids": [],
            "unexpected_source_ids": [],
            "duplicate_result_ids": [],
        }
        stage.write_text(json.dumps(payload), encoding="utf-8")
        return config, stage, payload, revision

    def test_public_source_checker_stage_requires_public_only(self):
        args = mock.Mock(
            public_only=False,
            refresh_github=False,
            public_source_checker_stage=True,
        )
        with self.assertRaisesRegex(RuntimeError, "requires --public-only"):
            MODULE.validate_console_modes(args)

    def test_public_source_checker_stage_uses_catalog_binding_across_head_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config, stage, _, revision = self.public_source_checker_fixture(root)
            legacy = root / ".tmp" / "source-checker.json"
            legacy.write_text("must not open", encoding="utf-8")
            original_open = open

            def guarded_open(path, *args, **kwargs):
                if os.path.realpath(os.fspath(path)) == os.path.realpath(legacy):
                    raise AssertionError("legacy Source Checker cache opened")
                return original_open(path, *args, **kwargs)

            with (
                mock.patch.object(MODULE, "ROOT", root),
                mock.patch.object(MODULE, "SOURCE_CHECKER_CONFIG", config),
                mock.patch.object(
                    MODULE, "PUBLIC_SOURCE_CHECKER_STAGE", stage
                ),
                mock.patch.object(
                    MODULE,
                    "current_repository_head",
                    return_value="f" * 40,
                ) as head_reader,
                mock.patch("builtins.open", guarded_open),
                mock.patch.dict(
                    os.environ,
                    {"ARRP_SOURCE_CHECKER_SNAPSHOT": ""},
                    clear=False,
                ),
            ):
                projected = MODULE.source_checker_snapshot(
                    public_source_checker_stage=True
                )
        head_reader.assert_not_called()
        self.assertEqual(projected["availability"], "current")
        self.assertTrue(projected["completeness"]["complete"])
        self.assertEqual(projected["actual_count"], 1)
        self.assertEqual(projected["source_revision"], revision)
        self.assertNotIn(".tmp", json.dumps(projected))

    def test_public_source_checker_stage_rejects_other_input_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config, stage, _, revision = self.public_source_checker_fixture(root)
            with (
                mock.patch.object(MODULE, "ROOT", root),
                mock.patch.object(MODULE, "SOURCE_CHECKER_CONFIG", config),
                mock.patch.object(
                    MODULE, "PUBLIC_SOURCE_CHECKER_STAGE", stage
                ),
                mock.patch.object(
                    MODULE, "current_repository_head", return_value=revision
                ),
                mock.patch.dict(
                    os.environ,
                    {"ARRP_SOURCE_CHECKER_SNAPSHOT": str(stage)},
                    clear=False,
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "cannot be combined"):
                    MODULE.source_checker_snapshot(
                        public_source_checker_stage=True
                    )

    def test_public_source_checker_stage_rejects_missing_nonregular_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config, stage, _, revision = self.public_source_checker_fixture(root)
            stage.unlink()
            cases = ("missing", "directory", "symlink")
            for case in cases:
                with self.subTest(case=case):
                    if stage.exists() or stage.is_symlink():
                        if stage.is_dir():
                            stage.rmdir()
                        else:
                            stage.unlink()
                    if case == "directory":
                        stage.mkdir()
                    elif case == "symlink":
                        target = root / "elsewhere.json"
                        target.write_text("{}", encoding="utf-8")
                        stage.symlink_to(target)
                    with (
                        mock.patch.object(MODULE, "ROOT", root),
                        mock.patch.object(
                            MODULE, "SOURCE_CHECKER_CONFIG", config
                        ),
                        mock.patch.object(
                            MODULE, "PUBLIC_SOURCE_CHECKER_STAGE", stage
                        ),
                        mock.patch.object(
                            MODULE,
                            "current_repository_head",
                            return_value=revision,
                        ),
                        mock.patch.dict(
                            os.environ,
                            {"ARRP_SOURCE_CHECKER_SNAPSHOT": ""},
                            clear=False,
                        ),
                    ):
                        with self.assertRaisesRegex(
                            RuntimeError, "stage is unavailable"
                        ):
                            MODULE.source_checker_snapshot(
                                public_source_checker_stage=True
                            )

    def test_public_source_checker_stage_rejects_invalid_current_report(self):
        mutations = {
            "producer": lambda payload: payload.update(agent_id="other"),
            "schema": lambda payload: payload.update(schema_version=1),
            "hash": lambda payload: payload.update(source_hashes={}),
            "completeness": lambda payload: payload["completeness"].update(
                complete=False
            ),
            "pagination": lambda payload: payload["pagination"].update(
                complete=False
            ),
            "count": lambda payload: payload.update(actual_count=0),
            "identity": lambda payload: payload["results"][0].update(
                source_id="SRC-OTHER"
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config, stage, payload, revision = (
                    self.public_source_checker_fixture(root)
                )
                mutate(payload)
                stage.write_text(json.dumps(payload), encoding="utf-8")
                with (
                    mock.patch.object(MODULE, "ROOT", root),
                    mock.patch.object(MODULE, "SOURCE_CHECKER_CONFIG", config),
                    mock.patch.object(
                        MODULE, "PUBLIC_SOURCE_CHECKER_STAGE", stage
                    ),
                    mock.patch.object(
                        MODULE,
                        "current_repository_head",
                        return_value=revision,
                    ),
                    mock.patch.dict(
                        os.environ,
                        {"ARRP_SOURCE_CHECKER_SNAPSHOT": ""},
                        clear=False,
                    ),
                ):
                    with self.assertRaisesRegex(RuntimeError, "stage is invalid"):
                        MODULE.source_checker_snapshot(
                            public_source_checker_stage=True
                        )

    def test_source_checker_keeps_stale_generation_and_enumerates_missing_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "sources.csv"
            catalog.write_text(
                "Source ID,URL,Title or Description,Authority / Publisher\n"
                "SRC-1,https://example.test/1,One,Publisher\n"
                "SRC-2,https://example.test/2,Two,Publisher\n",
                encoding="utf-8",
            )
            snapshot = root / ".tmp" / "source-checker.json"
            snapshot.parent.mkdir()
            snapshot.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "checked_at": "2026-07-25T12:00:00Z",
                        "eligible_urls": 1,
                        "counts": {"verified": 1},
                        "results": [
                            {
                                "source_id": "SRC-1",
                                "classification": "verified",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            config = root / "source-checker-config.json"
            config.write_text(
                json.dumps(
                    {
                        "catalogs": [str(catalog)],
                        "idField": "Source ID",
                        "urlField": "URL",
                        "offlineCachePath": str(root / "missing.json"),
                    }
                ),
                encoding="utf-8",
            )
            with (
                mock.patch.object(MODULE, "ROOT", root),
                mock.patch.object(MODULE, "SOURCE_CHECKER_CONFIG", config),
                mock.patch.dict(
                    os.environ,
                    {"ARRP_SOURCE_CHECKER_SNAPSHOT": str(snapshot)},
                    clear=False,
                ),
            ):
                projected = MODULE.source_checker_snapshot()
        self.assertEqual(projected["availability"], "stale")
        self.assertEqual(projected["expected_count"], 2)
        self.assertEqual(projected["actual_count"], 1)
        self.assertEqual(projected["missing_source_ids"], ["SRC-2"])
        self.assertFalse(projected["completeness"]["complete"])

    def test_source_checker_rejects_empty_results_as_false_zero_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "sources.csv"
            catalog.write_text(
                "Source ID,URL,Title or Description,Authority / Publisher\n"
                "SRC-1,https://example.test/1,One,Publisher\n",
                encoding="utf-8",
            )
            snapshot = root / ".tmp" / "source-checker.json"
            snapshot.parent.mkdir()
            snapshot.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "checked_at": "2026-07-25T12:00:00Z",
                        "eligible_urls": 1,
                        "counts": {},
                        "results": [],
                    }
                ),
                encoding="utf-8",
            )
            config = root / "config.json"
            config.write_text(
                json.dumps(
                    {
                        "catalogs": [str(catalog)],
                        "idField": "Source ID",
                        "urlField": "URL",
                    }
                ),
                encoding="utf-8",
            )
            with (
                mock.patch.object(MODULE, "ROOT", root),
                mock.patch.object(MODULE, "SOURCE_CHECKER_CONFIG", config),
                mock.patch.dict(
                    os.environ,
                    {"ARRP_SOURCE_CHECKER_SNAPSHOT": str(snapshot)},
                    clear=False,
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "invalid producer generation"):
                    MODULE.source_checker_snapshot()

    def test_source_checker_preserves_producer_validity_across_stale_overlay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "sources.csv"
            catalog.write_text(
                "Source ID,URL,Title or Description,Authority / Publisher\n"
                "SRC-1,https://example.test/1,One,Publisher\n"
                "SRC-2,https://example.test/2,Two,Publisher\n",
                encoding="utf-8",
            )
            snapshot = root / ".tmp" / "source-checker.json"
            snapshot.parent.mkdir()
            snapshot.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "checked_at": "2026-07-25T12:00:00+00:00",
                        "generation_id": "valid-producer-generation",
                        "source_revision": "checker-revision",
                        "source_hashes": {},
                        "expected_count": 1,
                        "actual_count": 1,
                        "availability": "current",
                        "completeness": {
                            "complete": True,
                            "expected_count": 1,
                            "actual_count": 1,
                            "missing_count": 0,
                        },
                        "pagination": {"complete": True, "sources": []},
                        "projection_errors": [],
                        "eligible_urls": 1,
                        "counts": {"verified": 1},
                        "results": [
                            {
                                "source_id": "SRC-1",
                                "classification": "verified",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            config = root / "source-checker-config.json"
            config.write_text(
                json.dumps(
                    {
                        "catalogs": [str(catalog)],
                        "idField": "Source ID",
                        "urlField": "URL",
                    }
                ),
                encoding="utf-8",
            )
            environment = {"ARRP_SOURCE_CHECKER_SNAPSHOT": str(snapshot)}
            with (
                mock.patch.object(MODULE, "ROOT", root),
                mock.patch.object(MODULE, "SOURCE_CHECKER_CONFIG", config),
                mock.patch.dict(os.environ, environment, clear=False),
            ):
                first_projection = MODULE.source_checker_snapshot()
            self.assertFalse(first_projection["completeness"]["complete"])
            self.assertTrue(
                first_projection["producer_contract"]["completeness"]["complete"]
            )
            snapshot.write_text(
                json.dumps(first_projection),
                encoding="utf-8",
            )
            with (
                mock.patch.object(MODULE, "ROOT", root),
                mock.patch.object(MODULE, "SOURCE_CHECKER_CONFIG", config),
                mock.patch.dict(os.environ, environment, clear=False),
            ):
                recovered = MODULE.source_checker_snapshot()
        self.assertEqual(recovered["availability"], "stale")
        self.assertEqual(recovered["missing_source_ids"], ["SRC-2"])
        self.assertTrue(
            recovered["producer_contract"]["completeness"]["complete"]
        )

    def test_source_checker_currentness_uses_catalog_hash_not_repository_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "sources.csv"
            catalog.write_text(
                "Source ID,URL,Title or Description,Authority / Publisher\n"
                "SRC-1,https://example.test/1,One,Publisher\n",
                encoding="utf-8",
            )
            catalog_label = "sources.csv"
            digest = CONTRACTS.file_sha256(root, catalog)
            snapshot = root / ".tmp" / "source-checker.json"
            snapshot.parent.mkdir()
            snapshot.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "checked_at": "2026-07-25T12:00:00+00:00",
                        "generation_id": "hash-bound-generation",
                        "source_revision": "not-repository-head",
                        "source_hashes": {catalog_label: digest},
                        "expected_count": 1,
                        "actual_count": 1,
                        "availability": "current",
                        "completeness": {
                            "complete": True,
                            "expected_count": 1,
                            "actual_count": 1,
                            "missing_count": 0,
                        },
                        "pagination": {"complete": True, "sources": []},
                        "projection_errors": [],
                        "eligible_urls": 1,
                        "counts": {"verified": 1},
                        "results": [
                            {
                                "source_id": "SRC-1",
                                "classification": "verified",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            config = root / "source-checker-config.json"
            config.write_text(
                json.dumps(
                    {
                        "catalogs": [str(catalog)],
                        "idField": "Source ID",
                        "urlField": "URL",
                    }
                ),
                encoding="utf-8",
            )
            with (
                mock.patch.object(MODULE, "ROOT", root),
                mock.patch.object(MODULE, "SOURCE_CHECKER_CONFIG", config),
                mock.patch.dict(
                    os.environ,
                    {"ARRP_SOURCE_CHECKER_SNAPSHOT": str(snapshot)},
                    clear=False,
                ),
            ):
                current = MODULE.source_checker_snapshot()
        self.assertEqual(current["availability"], "current")
        self.assertTrue(current["currentness"]["current"])
        self.assertEqual(
            current["currentness"]["authority"],
            "source_catalog_identity_and_hashes",
        )

    def test_exact_head_affected_set_uses_structured_event_enumeration(self):
        recommendation = {
            "proposal_event_id": "SDE-TEST",
            "pull_request_number": 380,
            "head_revision": "head-sha",
        }
        event = {
            "event_id": "SDE-TEST",
            "proposal": {
                "pull_request_number": 380,
                "proposal_revision": "head-sha",
            },
            "affected_records": [
                {"record_id": "HOR-035", "record_type": "candidate"},
                {"record_id": "SRC-1", "record_type": "source"},
                {"record_id": "SRC-2", "record_type": "source"},
            ],
            "summary": {"affected_record_count": 3},
        }
        affected = MODULE.structured_affected_set(recommendation, event)
        self.assertTrue(affected["complete"])
        self.assertEqual(affected["total_count"], 3)
        self.assertEqual(affected["issue_development_ids"], ["HOR-035"])
        self.assertEqual(affected["source_ids"], ["SRC-1", "SRC-2"])
        event["proposal"]["proposal_revision"] = "changed-head"
        with self.assertRaisesRegex(RuntimeError, "head revision"):
            MODULE.structured_affected_set(recommendation, event)

    def test_markdown_projection_reports_row_schema_drift(self):
        errors = []
        rows = MODULE.markdown_table_records(
            "| A | B | C |\n|---|---|---|\n| one | two |\n",
            ("A", "B", "C"),
            errors,
            "governed-log.md",
        )
        self.assertEqual(rows, [])
        self.assertEqual(errors[0]["code"], "markdown_table_row_width")
        self.assertEqual(errors[0]["source"], "governed-log.md")

    def _legacy_stage1_candidate_projection(self):
        projection_source = SCRIPT.read_text(encoding="utf-8").split(
            "def component_registry_console_snapshot(",
            1,
        )[1].split(
            "def load_component_registry_console_snapshot(",
            1,
        )[0]
        self.assertEqual(
            projection_source.count('"source_import": source_import'),
            1,
        )
        self.assertNotIn(
            '"source_import": routing["source_import"]',
            projection_source,
        )
        registry = candidate_registry_fixture()
        embedded = registry["context_routing"]
        view = self.component_registry_view(
            registry,
            status="candidate",
        )
        inventory = {
            "classification_complete": True,
            "scope_counts": {
                scope_id: 0
                for scope_id in registry["directory_scopes"]["entries"]
            },
        }
        with mock.patch.object(
            MODULE,
            "component_registry_inventory_report",
            return_value=inventory,
        ):
            snapshot = MODULE.component_registry_console_snapshot(
                view,
                generated_at="2026-07-29T12:00:00Z",
            )
        self.assertEqual(
            set(snapshot),
            {
                "schema_version",
                "projection_id",
                "producer_id",
                "generated_at",
                "availability",
                "complete",
                "reason_code",
                "routes",
                "defaults",
                "registry",
                "deferred",
                "documents",
                "directories",
                "relationships",
                "routing",
                "activation_readiness",
                "terminology",
            },
        )
        self.assertEqual(
            set(snapshot["routing"]),
            {
                "schema_version",
                "rule_catalog_version",
                "activation_state",
                "complete",
                "authoritative",
                "source_import",
                "predecessor_provenance",
                "readable_representation",
                "expected_counts",
                "parity_policy",
                "required_modules",
                "generated_path_exclusions",
                "documents",
                "capabilities",
                "profiles",
                "selections",
                "rule_namespaces",
                "rule_counts",
                "rules",
                "validation",
            },
        )
        self.assertEqual(snapshot["schema_version"], 1)
        self.assertEqual(
            len(snapshot["relationships"]),
            len(registry["component_relationships"]),
        )
        self.assertEqual(
            snapshot["relationships"][0]["console_route"],
            (
                "automation:component-registry:relationships?relationship="
                + snapshot["relationships"][0]["relationship_id"]
            ),
        )

        self.assertEqual(
            snapshot["registry"]["validation_mode"],
            "candidate_validation_only",
        )
        self.assertFalse(snapshot["registry"]["authoritative"])
        self.assertFalse(snapshot["registry"]["executable"])
        self.assertFalse(snapshot["registry"]["live_activation_verified"])
        self.assertTrue(snapshot["registry"]["predecessor_route_consulted"])
        self.assertEqual(
            snapshot["registry"]["configuration_validation"]["value"],
            "Candidate predecessor parity validated",
        )
        self.assertEqual(
            snapshot["registry"]["live_activation"]["state"],
            "pending",
        )
        self.assertEqual(
            snapshot["registry"]["source_binding_sha256"]["state"],
            "known",
        )
        self.assertEqual(
            snapshot["routing"]["predecessor_provenance"]["state"],
            "not_applicable",
        )
        self.assertEqual(
            snapshot["routing"]["readable_representation"]["state"],
            "not_applicable",
        )
        candidate_sources = MODULE.component_registry_source_paths(snapshot)
        self.assertIn(
            MODULE.COMPONENT_REGISTRY_ROUTE_SOURCE,
            candidate_sources,
        )
        self.assertIn(
            ROOT
            / "framework"
            / "receipts"
            / "component-registry"
            / "stage1-requirement-closure.json",
            candidate_sources,
        )
        self.assertNotIn(
            ROOT
            / "framework"
            / "receipts"
            / "component-registry"
            / "stage1-activation-readiness.json",
            candidate_sources,
        )
        self.assertEqual(snapshot["routing"]["schema_version"], 2)
        self.assertEqual(snapshot["routing"]["rule_catalog_version"], 1)
        self.assertTrue(snapshot["complete"])
        self.assertEqual(
            snapshot["activation_readiness"]["requirement_count"],
            77,
        )
        self.assertEqual(
            snapshot["activation_readiness"]["activation_decision"],
            "pending_human_activation",
        )
        self.assertEqual(
            snapshot["deferred"]["display_state"],
            "Classification pending — enforcement not active",
        )
        self.assertEqual(
            snapshot["routes"]["documents"],
            "automation:component-registry:documents",
        )
        self.assertEqual(
            len(snapshot["documents"]),
            len(registry["operational_documents"]["entries"]),
        )
        self.assertEqual(
            len(snapshot["directories"]),
            len(registry["directory_scopes"]["entries"]),
        )
        self.assertEqual(
            len(snapshot["routing"]["selections"]),
            len(embedded["profiles"]) + len(embedded["capabilities"]),
        )
        self.assertTrue(
            all(
                record["executable"] is False
                and record["authoritative"] is False
                and record["live_activation_verified"] is False
                for record in snapshot["routing"]["selections"]
            )
        )
        expected_rule_counts = {
            "invariants": 7,
            "selection": 17,
            "validation": 10,
            "failure_rules": 10,
            "currentness": 6,
            "budgets": 4,
            "comprehensive_review": 10,
        }
        self.assertEqual(snapshot["routing"]["rule_counts"], expected_rule_counts)
        self.assertEqual(len(snapshot["routing"]["rules"]), 64)
        for rule in snapshot["routing"]["rules"]:
            self.assertEqual(rule["predicate_type"], rule["rule_id"])
            self.assertEqual(rule["rule_version"], 1)
            self.assertEqual(rule["status"], "active")
            self.assertEqual(
                rule["source_provenance"]["source_document_id"],
                "context_routing",
            )
            self.assertEqual(
                rule["source_provenance"]["clause_key"],
                rule["rule_id"],
            )
            self.assertEqual(rule["verification_ids"], [f"test.{rule['rule_id']}"])
            self.assertIn("rendered_text", rule)
            self.assertTrue(rule["console_route"].startswith(
                "automation:component-registry:routing?rule="
            ))
        self.assertNotIn("failure_code", snapshot["routing"]["rules"][0])
        failure_rule = next(
            rule for rule in snapshot["routing"]["rules"]
            if rule["namespace"] == "failure_rules"
        )
        self.assertTrue(failure_rule["failure_code"].startswith("CTXR_"))
        self.assertEqual(
            snapshot["terminology"]["console_route"],
            "automation:component-registry:terminology",
        )
        self.assertTrue(
            all(
                row["permitted_artifact_classes"]["state"] == "unavailable"
                for row in snapshot["directories"]
            )
        )
        self.assertTrue(
            all(
                row["console_route"].startswith(
                    "operations:component-registry:documents?document="
                )
                for row in snapshot["documents"]
            )
        )

    def test_component_registry_stage2_projection_has_one_validated_source(self):
        source = Path(MODULE.__file__).read_text(encoding="utf-8")
        self.assertIn(
            "def _stage2_component_registry_console_snapshot(",
            source,
        )
        self.assertIn(
            'routing_view.get("validation_mode")\n'
            '        != "proposed_revision_validation"',
            source,
        )
        for mode in (
            "components",
            "lifecycles",
            "authority",
            "relationships",
            "coverage",
            "routing",
            "terminology",
        ):
            self.assertIn(f'                "{mode}",', source)
        self.assertIn(
            'terminology_entries = terminology.get("entries")',
            source,
        )
        self.assertNotIn(
            "component-registry-stage2-terminology-working-draft.md",
            source,
        )
        self.assertNotIn(
            "framework/proposals/component-registry-stage2-design.md",
            source,
        )
        paths = MODULE.component_registry_source_paths(
            {
                "registry": {
                    "validation_mode": "proposed_revision_validation",
                },
            },
            root=Path("/tmp/arrp-stage2-console-test"),
        )
        self.assertEqual(
            paths,
            [
                Path("/tmp/arrp-stage2-console-test/framework/component-registry.json"),
                Path(
                    "/tmp/arrp-stage2-console-test/framework/standards/automation/"
                    "component-registry.schema.json"
                ),
            ],
        )

        snapshot = MODULE.load_component_registry_console_snapshot(
            generated_at="2026-07-31T12:00:00Z",
        )
        self.assertEqual(snapshot["schema_version"], 2)
        self.assertEqual(snapshot["availability"], "current")
        self.assertTrue(snapshot["complete"])
        self.assertEqual(
            set(snapshot["routes"]),
            {
                "components",
                "lifecycles",
                "authority",
                "relationships",
                "coverage",
                "routing",
                "terminology",
            },
        )
        self.assertEqual(
            snapshot["registry"]["validation_mode"],
            "proposed_revision_validation",
        )
        self.assertEqual(snapshot["registry"]["registry_status"], "proposed")
        self.assertFalse(snapshot["registry"]["authoritative"])
        self.assertFalse(snapshot["registry"]["executable"])
        self.assertFalse(snapshot["registry"]["live_authority_verified"])
        self.assertFalse(snapshot["registry"]["predecessor_route_consulted"])
        self.assertEqual(len(snapshot["components"]), 103)
        self.assertEqual(len(snapshot["lifecycles"]["assignments"]), 103)
        self.assertEqual(len(snapshot["authorities"]["assignments"]), 103)
        self.assertEqual(len(snapshot["relationships"]), 15)
        self.assertEqual(len(snapshot["coverage"]["records"]), 57)
        self.assertEqual(snapshot["coverage"]["uncovered_count"], 0)
        self.assertEqual(snapshot["coverage"]["multiply_treated_count"], 0)
        self.assertEqual(len(snapshot["routing"]["selections"]), 27)
        self.assertTrue(snapshot["terminology"]["adopted"])
        self.assertEqual(len(snapshot["terminology"]["entries"]), 69)
        self.assertEqual(
            MODULE.component_registry_projection_count(snapshot),
            sum(
                len(records)
                for records in (
                    snapshot["components"],
                    snapshot["lifecycles"]["assignments"],
                    snapshot["authorities"]["sources"],
                    snapshot["authorities"]["assignments"],
                    snapshot["authorities"]["history"],
                    snapshot["relationships"],
                    snapshot["coverage"]["records"],
                    snapshot["routing"]["components"],
                    snapshot["routing"]["selections"],
                    snapshot["terminology"]["entries"],
                )
            ),
        )
        for component in snapshot["components"]:
            self.assertIn("classification", component)
            self.assertIn("canonical_source", component)
            self.assertIn("information_handling", component)
            self.assertIn("retention", component)
            self.assertIn("supporting_artifacts", component)
            self.assertIn("lifecycle_records", component)
            self.assertIn("authority_records", component)
            self.assertIn("relationship_records", component)
            self.assertIn("migration_records", component)
            self.assertIn("provenance_records", component)
        proposal = next(
            component
            for component in snapshot["components"]
            if component["stable_id"]
            == "component_registry_stage2_design_proposal"
        )
        self.assertEqual(
            proposal["canonical_source"]["locator"]["value"],
            "framework/proposals/component-registry-stage2-design.md",
        )
        self.assertTrue(
            any(
                migration.get("source_path")
                == "research/component-registry-stage2-terminology-working-draft.md"
                and migration.get("target_path")
                == "framework/proposals/component-registry-stage2-design.md"
                and migration.get("historical_only") is True
                for migration in proposal["migration_records"]
            )
        )

    def test_console_generation_timestamp_is_bound_to_exact_revision(self):
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        expected = subprocess.run(
            ["git", "show", "-s", "--format=%cI", revision],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(
            MODULE.repository_revision_timestamp(ROOT, revision),
            datetime.fromisoformat(expected).isoformat(timespec="seconds"),
        )
        with self.assertRaisesRegex(RuntimeError, "exact Git object ID"):
            MODULE.repository_revision_timestamp(ROOT, "HEAD")

    def _legacy_stage1_active_projection(self):
        registry = candidate_registry_fixture()
        candidate_registry = copy.deepcopy(registry)
        registry["status"] = "active"
        registry["approval"] = {
            "state": "known",
            "value": {
                "owner_review_reference": "restricted-review-reference",
                "approved_by": "@Thorncrag",
                "governance_change_id": "GOV-2026-001",
                "implementation_contract_id":
                    "COMPONENT-REGISTRY-2026-001-ACTIVATION",
            },
        }
        registry["context_routing"]["activation_state"] = "active"
        registry["context_routing"]["authoritative"] = True
        registry["context_routing"].pop("source_import")
        registry["context_routing"].pop("parity_policy")
        predecessor_digests = {
            "context_routing": "6" * 64,
            "context_routes_source": "7" * 64,
        }
        registry["context_routing"]["predecessor_provenance"] = {
            "schema_version": 1,
            "complete": True,
            "authority_effect":
                "historical_provenance_only_no_runtime_read",
            "records": {
                "context_routing": {
                    "stable_id": "context_routing",
                    "artifact_kind": "markdown_authority",
                    "historical_path": "framework/CONTEXT_ROUTING.md",
                    "archived_path":
                        "framework/archive/authorities/CONTEXT_ROUTING.md",
                    "sha256": predecessor_digests["context_routing"],
                    "source_schema_version": None,
                    "state": "archived_retired_provenance_only",
                    "retirement_proof": {
                        "proof_type":
                            "authenticated_activation_cutover",
                        "governance_change_id": "GOV-2026-001",
                        "implementation_contract_id":
                            "COMPONENT-REGISTRY-2026-001-ACTIVATION",
                        "owner_review_reference":
                            "restricted-review-reference",
                    },
                },
                "context_routes_source": {
                    "stable_id": "context_routes_source",
                    "artifact_kind": "route_data_authority",
                    "historical_path":
                        "framework/project/automation/context-routes.json",
                    "archived_path":
                        "framework/archive/authorities/context-routes.json",
                    "sha256": predecessor_digests[
                        "context_routes_source"
                    ],
                    "source_schema_version": 2,
                    "state": "archived_retired_provenance_only",
                    "retirement_proof": {
                        "proof_type":
                            "authenticated_activation_cutover",
                        "governance_change_id": "GOV-2026-001",
                        "implementation_contract_id":
                            "COMPONENT-REGISTRY-2026-001-ACTIVATION",
                        "owner_review_reference":
                            "restricted-review-reference",
                    },
                },
            },
            "migration_alias_ids": [
                "relocate_context_routing",
                "relocate_context_routes_source",
            ],
            "verification_ids": [
                "test_active_predecessor_provenance_is_closed",
                "test_active_loader_does_not_read_predecessors",
                "test_active_embedded_route_excludes_predecessors",
            ],
        }
        registry["context_routing"]["readable_representation"] = {
            "representation_id": "human_readable_context_routing",
            "binding_kind": "component_registry_revision",
            "source_registry_revision": registry["registry_revision"],
            "generated_from": "embedded_context_routing",
            "authority_effect": "none",
            "executable": False,
        }
        archived_paths = {
            "context_routing":
                "framework/archive/authorities/CONTEXT_ROUTING.md",
            "context_routes_source":
                "framework/archive/authorities/context-routes.json",
        }
        document_template = dict(
            registry["operational_documents"]["entries"][
                "context_routing"
            ]
        )
        for stable_id, archived_path in archived_paths.items():
            document = dict(document_template)
            document.update({
                "document_id": stable_id,
                "canonical_path": archived_path,
                "authority_role": "archived_predecessor",
                "retention_posture": "archived",
                "digest_policy": "provenance_only",
                "sha256": predecessor_digests[stable_id],
                "dependencies": [],
                "consumers": [],
                "current_status": {
                    "state": "known",
                    "value": "retired",
                },
            })
            registry["operational_documents"]["entries"][
                stable_id
            ] = document
        registry["representations"]["entries"][
            "human_readable_context_routing"
        ].update({
            "canonical_path":
                (
                    "framework/project/interfaces/project-console/data/"
                    "component-registry.js"
                ),
            "source_revision_binding":
                f"component_registry_revision:{registry['registry_revision']}",
            "state": "active",
        })
        registry["context_routing"]["documents"].pop("context_routing")
        registry = component_registry_tool.build_simulated_active_registry(
            candidate_registry,
            repository_revision="a" * 40,
            approval_value={
                "approval_type": "stage1_component_registry_activation",
                "approved_by": "@Thorncrag",
                "approval_method": "explicit_recorded_owner_activation",
                "governance_change_id": "GOV-2026-001",
                "implementation_contract_id":
                    "COMPONENT-REGISTRY-2026-001-ACTIVATION",
                "base_revision": "a" * 40,
                "candidate_registry_sha256": "b" * 64,
                "affected_stable_ids": ["COMPONENT-REGISTRY"],
                "purpose_scope": "restricted-review-reference",
                "bounded_diff_sha256": "c" * 64,
                "approved_at": "2026-07-30T00:00:00-04:00",
                "owner_review_reference":
                    "github-review:Thorncrag/ARRP#123",
            },
        )
        view = self.component_registry_view(
            registry,
            status="active",
        )
        inventory = {
            "classification_complete": True,
            "scope_counts": {
                scope_id: 0
                for scope_id in registry["directory_scopes"]["entries"]
            },
        }
        with mock.patch.object(
            MODULE,
            "component_registry_inventory_report",
            return_value=inventory,
        ), mock.patch.object(
            MODULE,
            "component_registry_parity_report",
            side_effect=AssertionError(
                "active configuration must not consult predecessor parity"
            ),
        ), mock.patch.object(
            MODULE,
            "component_registry_routed_profile_preview",
            return_value={
                "executable": False,
                "authoritative": False,
                "live_activation_verified": False,
                "modules": [],
            },
        ), mock.patch.object(
            MODULE,
            "component_registry_routed_capability_preview",
            return_value={
                "executable": False,
                "authoritative": False,
                "live_activation_verified": False,
                "modules": [],
            },
        ):
            snapshot = MODULE.component_registry_console_snapshot(
                view,
                generated_at="2026-07-29T12:00:00Z",
            )
        self.assertEqual(
            snapshot["registry"]["approval"],
            {
                "state": "known",
                "value": "Tracked activation configuration approved",
            },
        )
        self.assertEqual(
            snapshot["registry"]["validation_mode"],
            "active_configuration_validation_only",
        )
        self.assertFalse(snapshot["registry"]["authoritative"])
        self.assertFalse(snapshot["registry"]["executable"])
        self.assertFalse(snapshot["registry"]["live_activation_verified"])
        self.assertFalse(
            snapshot["registry"]["predecessor_route_consulted"]
        )
        self.assertEqual(
            snapshot["registry"]["live_activation"]["state"],
            "unknown",
        )
        self.assertEqual(
            snapshot["registry"]["source_binding_sha256"]["state"],
            "not_applicable",
        )
        self.assertEqual(
            snapshot["routing"]["source_import"]["state"],
            "not_applicable",
        )
        self.assertEqual(
            snapshot["routing"]["validation"]["state"],
            "not_applicable",
        )
        self.assertEqual(
            snapshot["routing"]["parity_policy"]["state"],
            "not_applicable",
        )
        self.assertEqual(
            snapshot["routing"]["predecessor_provenance"],
            {
                "state": "known",
                "value": (
                    "Archived predecessor provenance retained as "
                    "nonauthoritative history."
                ),
            },
        )
        self.assertEqual(
            snapshot["routing"]["readable_representation"],
            {
                "state": "known",
                "representation_id": "human_readable_context_routing",
                "source_registry_revision": registry["registry_revision"],
                "authority_effect": "none",
                "executable": False,
            },
        )
        self.assertNotIn(
            "context_routing",
            {
                record["document_id"]
                for record in snapshot["routing"]["documents"]
            },
        )
        self.assertTrue(
            all(
                rule["source_provenance"]["source_document_id"]
                == "COMPONENT-REGISTRY"
                and rule["source_provenance"]["source_sha256"]
                == snapshot["registry"]["registry_sha256"]
                for rule in snapshot["routing"]["rules"]
            )
        )
        self.assertFalse(snapshot["routing"]["authoritative"])
        self.assertNotIn(
            MODULE.COMPONENT_REGISTRY_ROUTE_SOURCE,
            MODULE.component_registry_source_paths(snapshot),
        )
        self.assertNotIn(
            "restricted-review-reference",
            json.dumps(snapshot, sort_keys=True),
        )
        self.assertNotIn(
            "Owner activation verified",
            json.dumps(snapshot, sort_keys=True),
        )
        self.assertNotIn(
            "activation_receipt",
            json.dumps(snapshot, sort_keys=True),
        )
        serialized = json.dumps(snapshot, sort_keys=True)
        self.assertNotIn(
            "framework/CONTEXT_ROUTING.md",
            serialized,
        )
        self.assertNotIn(
            "framework/project/automation/context-routes.json",
            serialized,
        )
        self.assertNotIn(predecessor_digests["context_routing"], serialized)
        self.assertNotIn(
            predecessor_digests["context_routes_source"],
            serialized,
        )

    def test_component_registry_loader_fails_closed_on_invalid_configuration(self):
        with mock.patch.object(
            MODULE,
            "load_component_registry_configuration_routing_view",
            side_effect=MODULE.ComponentRegistryError("source baseline drift"),
        ) as loader:
            with self.assertRaisesRegex(
                RuntimeError,
                "configuration validation is unavailable",
            ):
                MODULE.load_component_registry_console_snapshot(
                    generated_at="2026-07-29T12:00:00Z",
                )
        loader.assert_called_once_with()

    def test_atomic_bundle_removes_stale_domains_and_verifies_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            console = Path(directory) / "console"
            data = console / "data"
            data.mkdir(parents=True)
            (data / "stale.js").write_text("stale", encoding="utf-8")
            local_status = data / "local-automation-status.js"
            local_status.write_text(
                'window.ARRP_LOCAL_AUTOMATION_STATUS = {"status":"running"};\n',
                encoding="utf-8",
            )
            output = console / "catalog-data.js"
            output.write_text("old", encoding="utf-8")
            contract = CONTRACTS.feed_contract(
                feed_name="project-console",
                timestamp_field="generated_at",
                timestamp="2026-07-25T12:00:00+00:00",
                revision="reviewed-head",
                hashes={"input": "sha256:test"},
                expected_count=1,
                actual_count=1,
            )
            with mock.patch.object(
                MODULE,
                "require_outbound_bundle",
                return_value={"allowed": True, "complete": True},
            ):
                manifest = MODULE.write_console_bundle(
                    {"schema_version": 27, "overview": {"queue_counts": {}}},
                    {
                        "component-registry.js": {
                            "component_registry": {
                                "schema_version": 1,
                                "projection_id": "component-registry-console",
                            }
                        },
                        "overview.js": {"overview": {"queue_counts": {}}},
                        "progress.js": {"progress": {"metrics": {"total": 1}}},
                    },
                    generation_contract=contract,
                    output=output,
                    data_dir=data,
                )
            self.assertFalse((data / "stale.js").exists())
            self.assertTrue((data / "overview.js").is_file())
            self.assertEqual(
                (data / "local-automation-status.js").read_text(encoding="utf-8"),
                'window.ARRP_LOCAL_AUTOMATION_STATUS = {"status":"running"};\n',
            )
            self.assertEqual(
                (data / "local-automation-status.js").stat().st_mode & 0o777,
                0o600,
            )
            self.assertFalse((data / ".generation-manifest.json").exists())
            saved_manifest = json.loads(
                (data / "generation-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(saved_manifest, manifest)
            for name, metadata in manifest["files"].items():
                self.assertRegex(metadata["sha256"], r"^sha256:[a-f0-9]{64}$")
                self.assertEqual(
                    CONTRACTS.file_sha256(data, data / name),
                    metadata["sha256"],
                )
                part = MODULE.generated_console_part(
                    (data / name).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    part["domain_generation"][name],
                    contract["generation_id"],
                )
            catalog = MODULE.existing_console_payload.__globals__["json"].loads(
                output.read_text(encoding="utf-8")
                .removeprefix(MODULE.CATALOG_PREFIX)
                .removesuffix(";\n")
            )
            self.assertEqual(catalog["generation_id"], contract["generation_id"])
            self.assertEqual(
                set(catalog["generation_manifest"]["files"]),
                {"component-registry.js", "overview.js", "progress.js"},
            )

    def test_topic_products_have_stable_nonissue_identity(self):
        products = MODULE.topic_product_records()
        self.assertEqual(len(products), 5)
        self.assertEqual(
            len({product["product_id"] for product in products}), len(products)
        )
        self.assertTrue(all(product["is_issue"] is False for product in products))
        self.assertTrue(
            all(product["current_stage"] == "published" for product in products)
        )

    def test_release_readiness_separates_known_facts_from_unavailable_approval(self):
        progress = {
            "availability": "current",
            "completeness": {"complete": True},
            "proposals": [
                {
                    "identifier": "TEST-001",
                    "title": "Test proposal",
                    "url": "https://example.test/1",
                    "projectItemId": "PVTI-1",
                    "workflowStatus": "Audit needed",
                    "releaseBlocker": "Yes",
                    "changeAuditNeeded": "Yes",
                    "rebaselineStatus": "Current",
                }
            ],
            "candidates": [],
            "delivery_items": [
                {
                    "identifier": "DEL-001",
                    "title": "Release task",
                    "url": "https://example.test/delivery",
                    "projectItemId": "PVTI-2",
                    "workflowStatus": "Development",
                    "releaseBlocker": "No",
                    "changeAuditNeeded": "No",
                    "rebaselineStatus": "Not applicable",
                    "completeness": {"complete": True},
                }
            ],
        }
        readiness = MODULE.publication_release_readiness(
            [],
            [],
            progress,
            {
                "current": {
                    "result": "pass",
                    "counts": {"findings": 0},
                    "revision": "reviewed-head",
                    "generated_at": "2026-07-25T12:00:00+00:00",
                }
            },
        )
        self.assertEqual(readiness["status"], "not_determined")
        self.assertEqual(
            readiness["assembly"]["label"],
            "Assembly structurally valid",
        )
        self.assertEqual(readiness["delivery_tasks"]["count"], 1)
        self.assertEqual(readiness["release_blockers"]["count"], 1)
        self.assertEqual(readiness["required_audits"]["count"], 1)
        self.assertFalse(
            readiness["link_export_validation"]["export_validation_available"]
        )
        self.assertFalse(readiness["export_lineage"]["available"])
        self.assertEqual(
            readiness["stale_pdf"]["revision_backed_status"],
            "unavailable",
        )
        self.assertEqual(
            readiness["human_go_no_go"]["status"],
            "human_decision_required",
        )

    def test_overview_projects_compact_manager_signals_without_false_zeroes(self):
        overview = MODULE.overview_data(
            candidates=[],
            active_horizon_records=[],
            monitoring_issues=[],
            pending_sources=[],
            review_recommendations=[
                {
                    "id": "REC-1",
                    "action_owner": "Human",
                    "human_question": "Approve the exact affected set?",
                    "console_target": "logs:source-monitor",
                }
            ],
            progress={
                "availability": "stale",
                "generated_at": "2026-07-25T12:00:00+00:00",
                "metrics": {"ready": 27, "total": 81, "remaining": 54},
                "proposals": [
                    {
                        "identifier": "TEST-001",
                        "title": "Human decision and release blocker",
                        "url": "https://example.test/1",
                        "workflowStatus": "Human decision needed",
                        "priority": "Critical",
                        "releaseBlocker": "Yes",
                    }
                ],
                "candidates": [],
            },
            integrity={
                "availability": "current",
                "current": {
                    "result": "pass",
                    "counts": {"findings": 2},
                },
            },
            run_chain={
                "chain_id": "CHAIN-1",
                "status": "blocked",
                "failures": [
                    {
                        "stage": "publish",
                        "message": "Refusing a non-main branch instead of main.",
                        "recorded_at": "2026-07-25T12:00:00+00:00",
                    }
                ],
                "host_action_items": [
                    {
                        "id": "retry-row",
                        "kind": "automation_failure",
                        "owner": "human",
                        "stage": "publish",
                        "details": "Refusing a non-main branch instead of main.",
                        "created_at": "2026-07-25T11:55:00+00:00",
                        "failure_count": 4,
                        "resolved": False,
                    }
                ],
            },
            publication={
                "release_readiness": {
                    "status": "not_determined",
                    "status_explanation": "Human release decision is pending.",
                }
            },
            project_logs=[],
            agent_registry=[],
            watcher_metadata={},
            source_checker={
                "availability": "stale",
                "checked_at": "2026-07-25T12:00:00+00:00",
                "completeness": {"complete": False},
            },
            operational_incidents={
                "availability": "current",
                "complete": True,
                "unresolved_count": 1,
                "impact_state": "red",
                "items": [
                    {
                        "incident_id": "INC-2026-001",
                        "status": "open",
                        "impact": "blocking",
                        "classification": "hold",
                    }
                ],
            },
        )
        focus = overview["manager_focus"]
        self.assertEqual(focus["human_decisions"], 2)
        self.assertEqual(focus["active_incidents"], 1)
        self.assertEqual(focus["incidents"][0]["classification"], "hold")
        self.assertEqual(focus["critical_high_release_blockers"], 1)
        self.assertEqual(focus["integrity_findings"], 2)
        self.assertTrue(focus["integrity_findings_available"])
        self.assertIsNone(focus["delivery_items"])
        attention_domains = {
            item["domain"] for item in focus["domain_attention"]
        }
        self.assertTrue(
            {
                "progress",
                "source_checker",
                "automation",
                "publication_release",
            }
            <= attention_domains
        )

    def test_overview_does_not_infer_zero_integrity_findings_when_unavailable(self):
        overview = MODULE.overview_data(
            progress={},
            candidates=[],
            active_horizon_records=[],
            monitoring_issues=[],
            pending_sources=[],
            review_recommendations=[],
            integrity={"availability": "unavailable", "current": {}},
            run_chain={},
            publication={},
            project_logs=[],
            agent_registry=[],
            watcher_metadata={},
            source_checker={},
        )
        focus = overview["manager_focus"]
        self.assertIsNone(focus["integrity_findings"])
        self.assertFalse(focus["integrity_findings_available"])

    def test_overview_automation_readiness_owns_latest_blockers_and_future_gates(self):
        readiness = MODULE.overview_automation_readiness(
            {
                "chain_id": "CHAIN-READINESS-1",
                "status": "blocked",
                "updated_at": "2026-07-28T13:00:00+00:00",
                "failures": [
                    {
                        "id": "latest-source-failure",
                        "stage": "source-checker",
                        "message": "Source check could not complete.",
                        "recorded_at": "2026-07-28T12:59:00+00:00",
                    }
                ],
                "repository_gates": {
                    "complete": True,
                    "count": 2,
                    "checked_at": "2026-07-28T12:58:00+00:00",
                    "items": [
                        {
                            "id": "PR-501",
                            "number": 501,
                            "title": "Future automation contract",
                        },
                        {
                            "id": "PR-502",
                            "number": 502,
                            "title": "Gate that affected the latest attempt",
                            "affected_latest_attempt": True,
                            "affected_stage": "project-integrity",
                            "reason": "The latest Integrity stage was gated.",
                        },
                    ],
                },
            }
        )
        self.assertEqual(readiness["schema_version"], 1)
        self.assertEqual(readiness["latest_attempt"]["chain_id"], "CHAIN-READINESS-1")
        self.assertEqual(readiness["latest_attempt"]["blocker_count"], 2)
        self.assertEqual(
            {item["stage_id"] for item in readiness["latest_attempt"]["blockers"]},
            {"source-checker-bot", "project-integrity-bot"},
        )
        self.assertTrue(readiness["future_run_gates"]["available"])
        self.assertEqual(readiness["future_run_gates"]["count"], 2)

    def test_overview_automation_readiness_fails_closed_on_untyped_gate_inventory(self):
        readiness = MODULE.overview_automation_readiness(
            {
                "chain_id": "CHAIN-READINESS-2",
                "status": "complete",
                "repository_gates": {
                    "complete": False,
                    "count": 0,
                },
            }
        )
        self.assertFalse(readiness["future_run_gates"]["available"])
        self.assertIsNone(readiness["future_run_gates"]["count"])
        self.assertEqual(readiness["latest_attempt"]["blocker_count"], 0)

    def test_current_future_gate_does_not_rewrite_latest_attempt_and_applied_gate_counts_once(self):
        readiness = MODULE.overview_automation_readiness(
            {
                "chain_id": "CHAIN-GATED",
                "status": "blocked",
                "failures": [
                    {
                        "stage": "project-integrity-bot",
                        "message": "Repository gate GATE-001 blocked this stage.",
                    }
                ],
                "stages": [
                    {
                        "id": "project-integrity-bot",
                        "status": "failed",
                        "details": "Repository gate GATE-001 blocked this stage.",
                    }
                ],
                "repository_gates": {
                    "complete": True,
                    "count": 1,
                    "items": [
                        {
                            "gate_id": "GATE-001",
                            "blocks_automation": True,
                            "affected_stages": ["project-integrity-bot"],
                            "affected_latest_attempt": True,
                            "reason": "Exact-head gate applied.",
                        }
                    ],
                },
            },
            {
                "complete": True,
                "count": 1,
                "items": [
                    {
                        "gate_id": "GATE-002",
                        "blocks_automation": True,
                        "affected_stages": ["project-console-progress-bot"],
                        "affected_latest_attempt": False,
                        "reason": "Future run only.",
                    }
                ],
            },
        )
        self.assertEqual(readiness["latest_attempt"]["blocker_count"], 1)
        self.assertEqual(
            readiness["latest_attempt"]["blockers"][0]["id"],
            "GATE-001",
        )
        self.assertEqual(readiness["future_run_gates"]["count"], 1)

    def test_active_issue_score_activity_uses_exact_issue_audit_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            issue_root = root / "areas" / "TEST" / "issues"
            issue_root.mkdir(parents=True)
            (issue_root / "TEST-001.md").write_text(
                "# TEST-001 — Useful issue\n", encoding="utf-8"
            )
            (issue_root / "TEST-001.audit.md").write_text(
                """# TEST-001 — Audit History

### 2026-07-30 — Editorial follow-up

**Score effect:** No Proposal Quality Score change. The score remains 74/100.

### 2026-07-29 — T3 readiness audit

**Score effect:** Proposal Quality Score increased from 70 to 74.
""",
                encoding="utf-8",
            )
            progress = {
                "proposals": [
                    {
                        "identifier": "TEST-001",
                        "title": "TEST-001: Useful issue",
                        "canonicalRecord": "areas/TEST/issues/TEST-001.md",
                        "isIssueDevelopment": True,
                        "workflowStatus": "External review",
                        "state": "OPEN",
                        "score": 74,
                    },
                    {
                        "identifier": "TEST-AREA",
                        "title": "Area summary is not an issue page",
                        "canonicalRecord": "areas/TEST/README.md",
                        "isIssueDevelopment": True,
                        "state": "OPEN",
                        "score": 74,
                    },
                ]
            }
            activity = MODULE.active_issue_score_activity(
                progress, repository_root=root
            )
        self.assertEqual(len(activity), 1)
        self.assertEqual(activity[0]["event_code"], "active_issue_score_changed")
        self.assertEqual(activity[0]["artifact_label"], "TEST-001 · Useful issue")
        self.assertEqual(activity[0]["change_descriptor"], "T3 readiness audit")
        self.assertEqual(activity[0]["score_change"], "70 → 74")
        self.assertEqual(activity[0]["old_score"], 70)
        self.assertEqual(activity[0]["new_score"], 74)
        self.assertEqual(
            activity[0]["canonical_record"], "areas/TEST/issues/TEST-001.md"
        )

    def test_overview_activity_uses_issue_projection_not_general_logs(self):
        projected = {
            "event_id": "TEST-001-score-2026-07-29",
            "occurred_at": "2026-07-29",
            "event_code": "active_issue_score_changed",
            "artifact_label": "TEST-001 · Useful issue",
            "artifact_ids": ["TEST-001"],
            "change_descriptor": "T3 readiness audit",
            "score_change": "70 → 74",
            "canonical_record": "areas/TEST/issues/TEST-001.md",
            "route": "https://example.test/TEST-001",
        }
        with mock.patch.object(
            MODULE, "active_issue_score_activity", return_value=[projected]
        ):
            overview = MODULE.overview_data(
                candidates=[],
                active_horizon_records=[],
                monitoring_issues=[],
                pending_sources=[],
                review_recommendations=[],
                progress={"proposals": []},
                integrity={},
                run_chain={},
                publication={},
                project_logs=[
                    {
                        "id": "changes",
                        "title": "Change Audit Log",
                        "entries": [
                            {
                                "id": "generic-change",
                                "values": {
                                    "date": "2026-07-30",
                                    "change": "General project change",
                                    "scope": "Not one issue page",
                                    "effect": "No score change.",
                                },
                            }
                        ],
                    }
                ],
                agent_registry=[],
                watcher_metadata={},
                source_checker={},
            )
        self.assertEqual(overview["activity"], [projected])

    def test_overview_uses_typed_incident_projection_without_regrouping_run_text(self):
        message_a = (
            "host-repository-preflight failed: canonical ARRP workspace is not "
            "reconciled with GitHub: current branch is codex/first instead of main."
        )
        message_b = message_a.replace("codex/first", "codex/second")
        overview = MODULE.overview_data(
            candidates=[],
            active_horizon_records=[],
            monitoring_issues=[],
            pending_sources=[],
            review_recommendations=[],
            progress={},
            integrity={},
            run_chain={
                "chain_id": "CHAIN-2",
                "failures": [
                    {
                        "stage": "host-repository-preflight",
                        "message": message_a,
                        "recorded_at": "2026-07-25T12:00:00+00:00",
                    },
                    {
                        "stage": "host-repository-preflight",
                        "message": message_b,
                        "recorded_at": "2026-07-25T12:10:00+00:00",
                    },
                ],
                "host_action_items": [
                    {
                        "kind": "automation_failure",
                        "owner": "human",
                        "stage": "host-repository-preflight",
                        "details": message_b,
                        "created_at": "2026-07-25T12:10:00+00:00",
                        "resolved": False,
                    }
                ],
            },
            publication={},
            project_logs=[],
            agent_registry=[],
            watcher_metadata={},
            source_checker={},
            operational_incidents={
                "availability": "current",
                "complete": True,
                "unresolved_count": 1,
                "impact_state": "red",
                "items": [
                    {
                        "incident_id": "INC-2026-002",
                        "status": "investigating",
                        "impact": "blocking",
                        "occurrence_count": 2,
                        "root_cause": (
                            "Canonical ARRP workspace is off main and not "
                            "reconciled with GitHub."
                        ),
                    }
                ],
            },
        )
        incidents = overview["manager_focus"]["incidents"]
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["occurrence_count"], 2)
        self.assertEqual(
            incidents[0]["root_cause"],
            "Canonical ARRP workspace is off main and not reconciled with GitHub.",
        )

    def test_occurrence_directory_never_combines_distinct_runs(self):
        run_chain = {
            "chain_id": "push-20260727",
            "trigger": "push",
            "status": "succeeded",
            "completed_at": "2026-07-27T12:00:00+00:00",
            "stages": [
                {
                    "id": "case-monitor-bot",
                    "status": "succeeded",
                    "completed_at": "2026-07-27T11:55:00+00:00",
                }
            ],
            "elim_decision": {"launch_recommended": False, "reason": "Not due."},
        }
        local_status = {
            "run_id": "scheduled-20260728",
            "trigger": "scheduled",
            "status": "completed",
            "scheduled_for": "2026-07-28T02:00:00-04:00",
            "started_at": "2026-07-28T08:55:33+00:00",
            "completed_at": "2026-07-28T08:55:34+00:00",
            "updated_at": "2026-07-28T08:55:34+00:00",
            "control_state": "run",
            "validation_summary": {
                "reason": "scheduled_slot_already_claimed",
            },
        }
        projection = MODULE.automation_occurrence_projection(
            run_chain,
            local_status,
            checked_at="2026-07-28T12:00:00+00:00",
        )
        self.assertEqual(projection["latest_attempt_id"], "scheduled-20260728")
        self.assertEqual(
            projection["latest_scheduled_attempt_id"],
            "scheduled-20260728",
        )
        self.assertEqual(
            [item["occurrence_id"] for item in projection["occurrences"]],
            ["scheduled-20260728", "push-20260727"],
        )
        current = projection["occurrences"][0]
        self.assertEqual(len(current["stages"]), 7)
        self.assertEqual(
            {stage["status"] for stage in current["stages"]},
            {"not_due"},
        )
        self.assertIsNone(projection["last_fully_successful_occurrence"])

        expired = MODULE.automation_occurrence_projection(
            run_chain,
            local_status,
            checked_at="2026-07-31T12:00:00+00:00",
        )
        self.assertEqual(expired["role_currentness"]["state"], "stale")

    def test_public_automation_and_integrity_projections_redact_diagnostics(self):
        marker = "ARRP_STATE_ROOT=/Users/owner/private GH_TOKEN=credential_value"
        occurrences = MODULE.public_safe_automation_occurrences(
            {
                "occurrences": [
                    {
                        "occurrence_id": "scheduled-20260729",
                        "trigger": "launchd host dispatcher command",
                        "status": "failed",
                        "blockers": [
                            {
                                "id": "INC-private",
                                "reason": marker,
                                "stage_id": "run-coordinator-bot",
                            }
                        ],
                        "stages": [
                            {
                                "stage_id": "run-coordinator-bot",
                                "status": "failed",
                                "reason": marker,
                                "active_incident_ids": ["INC-private"],
                            }
                        ],
                    }
                ]
            }
        )
        safe_occurrence = occurrences["occurrences"][0]
        self.assertEqual(safe_occurrence["trigger"], "scheduled")
        self.assertEqual(safe_occurrence["status"], "failed")
        self.assertEqual(safe_occurrence["stages"][0]["status"], "failed")
        rendered = json.dumps(occurrences)
        for forbidden in ("ARRP_STATE_ROOT", "/Users/owner", "GH_TOKEN", "credential_value", "INC-private"):
            self.assertNotIn(forbidden, rendered)

        integrity = MODULE.public_safe_integrity(
            {
                "availability": "current",
                "current": {
                    "finding_count": 1,
                    "findings": [
                        {
                            "finding_id": "INT-001",
                            "finding_code": "project_integrity_condition",
                            "message": marker,
                            "route": "file:///Users/owner/private/report",
                        }
                    ],
                },
            }
        )
        self.assertEqual(
            integrity["current"]["findings"][0]["finding_code"],
            "project_integrity_condition",
        )
        self.assertEqual(
            integrity["current"]["findings"][0]["message"],
            "A typed integrity finding requires review.",
        )
        self.assertNotIn(marker, json.dumps(integrity))
        typed_integrity = MODULE.public_safe_integrity(
            {
                "availability": "current",
                "current": {
                    "finding_count": 1,
                    "findings": [
                        {
                            "finding_id": "INT-GITHUB-PROJECT",
                            "condition_code": (
                                "github_project_access_unavailable"
                            ),
                            "severity": "warning",
                            "category": "GitHub records",
                            "status": "open",
                            "message": marker,
                            "route": "file:///Users/owner/private/report",
                        }
                    ],
                },
            }
        )
        typed_finding = typed_integrity["current"]["findings"][0]
        self.assertEqual(
            typed_finding["finding_code"],
            "github_project_access_unavailable",
        )
        self.assertEqual(
            typed_finding["message"],
            (
                "GitHub Project synchronization could not be verified because "
                "the registered read-only access was unavailable."
            ),
        )
        self.assertEqual(typed_finding["owner"], "Elim")
        self.assertEqual(typed_finding["route"], "integrity")
        self.assertEqual(
            typed_finding["next_action"],
            "Run the registered authenticated Console refresh.",
        )
        self.assertNotIn(marker, json.dumps(typed_integrity))
        action_snapshot = MODULE.build_action_snapshot(
            progress={"proposals": [], "candidates": [], "pipeline": {}},
            integrity=integrity,
            review_recommendations=[],
            operational_incidents={
                "availability": "unavailable",
                "complete": False,
                "items": [],
            },
            security_incidents={
                "availability": "unavailable",
                "complete": False,
                "items": [],
            },
            generated_at="2026-07-29T12:00:00+00:00",
            require_private_incident_completeness=True,
        )
        self.assertNotIn(marker, json.dumps(action_snapshot))

        readiness = MODULE.public_safe_automation_readiness(
            {
                "latest_attempt": {
                    "available": True,
                    "status": "failed",
                    "trigger": "launchd host dispatch",
                    "blockers": [{"id": "GATE-private", "reason": marker}],
                }
            }
        )
        self.assertEqual(readiness["latest_attempt"]["trigger"], "scheduled")
        self.assertNotIn(marker, json.dumps(readiness))
        self.assertNotIn("GATE-private", json.dumps(readiness))

    def test_queue_directory_and_action_snapshot_share_exact_counts(self):
        action_snapshot = MODULE.build_action_snapshot(
            progress={"proposals": [], "candidates": [], "pipeline": {}},
            integrity={},
            review_recommendations=[],
            operational_incidents={
                "availability": "current",
                "complete": True,
                "items": [],
            },
            security_incidents={
                "availability": "current",
                "complete": True,
                "items": [],
            },
            generated_at="2026-07-28T12:00:00+00:00",
            require_private_incident_completeness=True,
        )
        directory = MODULE.build_queue_directory(
            progress={"pipeline": {"items": []}},
            preliminary_records=[{"id": "PRE-001"}],
            formal_candidates=[],
            pending_sources=[],
            review_recommendations=[],
            action_snapshot=action_snapshot,
            operational_incidents={
                "availability": "current",
                "complete": True,
                "unresolved_count": 0,
            },
            security_incidents={
                "availability": "current",
                "complete": True,
                "unresolved_count": 0,
            },
            generated_at="2026-07-28T12:00:00+00:00",
        )
        queues = {item["queue_id"]: item for item in directory["queues"]}
        self.assertEqual(queues["candidate_intake"]["count"], 1)
        self.assertEqual(
            queues["human_actions"]["count"],
            action_snapshot["counts"]["human"],
        )
        self.assertEqual(queues["operational_incidents"]["count"], 0)
        self.assertEqual(queues["security_incidents"]["count"], 0)

    def test_public_incident_projection_is_unavailable_without_private_ids(self):
        operational = MODULE.unavailable_incident_projection("operational")
        security = MODULE.unavailable_incident_projection("security")
        action_snapshot = MODULE.build_action_snapshot(
            progress={"proposals": [], "candidates": [], "pipeline": {}},
            integrity={},
            review_recommendations=[],
            operational_incidents=operational,
            security_incidents=security,
            generated_at="2026-07-29T12:00:00+00:00",
            require_private_incident_completeness=True,
        )
        directory = MODULE.build_queue_directory(
            progress={"pipeline": {"items": []}},
            preliminary_records=[],
            formal_candidates=[],
            pending_sources=[],
            review_recommendations=[],
            action_snapshot=action_snapshot,
            operational_incidents=operational,
            security_incidents=security,
            generated_at="2026-07-29T12:00:00+00:00",
        )
        queues = {item["queue_id"]: item for item in directory["queues"]}
        self.assertFalse(action_snapshot["complete"])
        self.assertEqual(action_snapshot["availability"], "partial")
        self.assertIsNone(action_snapshot["counts"]["human"])
        self.assertIsNone(queues["operational_incidents"]["count"])
        self.assertIsNone(queues["security_incidents"]["count"])
        self.assertEqual(operational["items"], [])
        self.assertEqual(security["items"], [])

    def test_unknown_console_classification_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "Unregistered"):
            MODULE.require_registered_classification(
                "queue_id",
                "browser_invented_queue",
            )

    def test_public_only_payload_does_not_open_ignored_console_projections(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            output = root / "catalog-data.js"
            data_dir = root / "data"
            data_dir.mkdir()
            output.write_text(
                "/* Generated by scripts/build_project_console.py. */\n"
                "window.ARRP_HORIZON_REVIEW_DATA={\"schema_version\":29};\n",
                encoding="utf-8",
            )
            (data_dir / "private-operations.js").write_text(
                "owner-only canary",
                encoding="utf-8",
            )
            (data_dir / "private-security-assurance.js").write_text(
                "owner-only canary",
                encoding="utf-8",
            )
            (data_dir / "local-automation-status.js").write_text(
                "owner-only canary",
                encoding="utf-8",
            )
            original_read_text = Path.read_text

            def guarded_read_text(path: Path, *args, **kwargs):
                if (
                    path.name.startswith("private-")
                    or path.name == "local-automation-status.js"
                ):
                    raise AssertionError(
                        f"public-only generation opened {path.name}"
                    )
                return original_read_text(path, *args, **kwargs)

            with (
                mock.patch.object(MODULE, "OUTPUT", output),
                mock.patch.object(MODULE, "CONSOLE_DATA_DIR", data_dir),
                mock.patch.object(
                    MODULE, "ALLOW_PRIVATE_CONSOLE_INPUTS", False
                ),
                mock.patch.object(Path, "read_text", guarded_read_text),
            ):
                payload = MODULE.existing_console_payload()
        self.assertEqual(payload["schema_version"], 29)

    def test_public_only_logs_do_not_open_owner_local_log_sources(self):
        with (
            mock.patch.object(
                MODULE, "ALLOW_PRIVATE_CONSOLE_INPUTS", False
            ),
            mock.patch.object(
                MODULE,
                "agent_audit_log_view",
                side_effect=AssertionError("owner-local log opened"),
            ),
            mock.patch.object(
                MODULE,
                "elim_run_log_view",
                side_effect=AssertionError("owner-local log opened"),
            ),
        ):
            logs = MODULE.project_log_views([])
        by_id = {item["id"]: item for item in logs}
        self.assertEqual(by_id["agents"]["availability"], "unavailable")
        self.assertEqual(by_id["elim"]["availability"], "unavailable")
        self.assertFalse(by_id["agents"]["complete"])
        self.assertFalse(by_id["elim"]["complete"])
        self.assertEqual(by_id["agents"]["entries"], [])
        self.assertEqual(by_id["elim"]["entries"], [])
        self.assertEqual(
            [item["key"] for item in by_id["agents"]["columns"]],
            ["date", "record", "task", "agent", "run", "outcome"],
        )
        self.assertEqual(
            [item["key"] for item in by_id["elim"]["columns"]],
            ["date", "outcome", "trigger", "summary", "usage", "next"],
        )
        public = {
            item["id"]: item
            for item in MODULE.public_safe_project_logs(logs)
        }
        for log_id in ("agents", "elim"):
            self.assertIsNone(public[log_id]["entry_count"])
            self.assertEqual(public[log_id]["entries"], [])
            self.assertEqual(
                public[log_id]["availability"], "unavailable"
            )
            self.assertFalse(public[log_id]["complete"])
            self.assertIsNone(public[log_id]["current_through"])
            self.assertIsNone(public[log_id]["source_url"])
            self.assertEqual(
                public[log_id]["reason"],
                MODULE.OWNER_MODE_UNAVAILABLE_MESSAGE,
            )


if __name__ == "__main__":
    unittest.main()
