import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_horizon_review_console.py"
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


class ConsoleDataContractTests(unittest.TestCase):
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
            manifest = MODULE.write_console_bundle(
                {"schema_version": 27, "overview": {"queue_counts": {}}},
                {
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
                {"overview.js", "progress.js"},
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

    def test_overview_activity_is_typed_deduplicated_and_collapses_clean_retries(self):
        overview = MODULE.overview_data(
            candidates=[],
            active_horizon_records=[],
            monitoring_issues=[],
            pending_sources=[],
            review_recommendations=[
                {
                    "id": "SMR-1",
                    "recorded_at": "2026-07-25T12:01:00Z",
                    "reviewer": "Interactive Codex",
                    "pull_request_number": 381,
                    "recommendation": "Review the complete exact-head delta.",
                    "affected_records": "10 directive records",
                    "action_owner": "Human",
                    "human_question": "Approve the recorded disposition?",
                    "console_target": "sources:watchers:directives",
                }
            ],
            progress={},
            integrity={},
            run_chain={},
            publication={},
            project_logs=[
                {
                    "id": "source-monitor",
                    "title": "Source Monitor Log",
                    "entries": [
                        {
                            "id": "source-monitor-1",
                            "values": {
                                "date": "2026-07-25T12:01:00Z",
                                "watcher": "Repository review recommendation SMR-1",
                                "result": "recommendation_recorded",
                                "activity": "SMR-1",
                            },
                        }
                    ],
                },
                {
                    "id": "agents",
                    "title": "Agent Audit Log",
                    "entries": [
                        {
                            "id": "agent-1",
                            "values": {
                                "date": "2026-07-25T12:00:00Z",
                                "record": "TEST-001",
                                "agent": "Elim",
                                "outcome": "Completed",
                            },
                        },
                        {
                            "id": "agent-2",
                            "values": {
                                "date": "2026-07-25T11:59:00Z",
                                "record": "TEST-001",
                                "agent": "Elim",
                                "outcome": "Completed",
                            },
                        },
                    ],
                },
            ],
            agent_registry=[],
            watcher_metadata={},
            source_checker={},
        )
        activity = overview["activity"]
        self.assertEqual(len(activity), 2)
        self.assertEqual(activity[0]["kind"], "repository_review_recommendation")
        self.assertEqual(activity[0]["actor"], "Interactive Codex")
        self.assertEqual(activity[0]["route"], "sources:watchers:directives")
        self.assertEqual(activity[1]["kind"], "collapsed_activity")
        self.assertEqual(activity[1]["collapsed_count"], 2)
        self.assertEqual(activity[1]["affected_scope"], "2 retained log activities")

    def test_overview_groups_branch_specific_retries_and_deduplicates_one_event(self):
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
        )
        incidents = overview["manager_focus"]["incidents"]
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["occurrence_count"], 2)
        self.assertEqual(
            incidents[0]["root_cause"],
            "Canonical ARRP workspace is off main and not reconciled with GitHub.",
        )


if __name__ == "__main__":
    unittest.main()
