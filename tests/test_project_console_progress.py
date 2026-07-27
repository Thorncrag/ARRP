import importlib.util
import json
import tempfile
import unittest
from copy import deepcopy
from datetime import date
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_project_console_progress.py"
SPEC = importlib.util.spec_from_file_location("project_console_progress", str(SCRIPT))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProjectConsoleProgressTests(unittest.TestCase):
    def setUp(self):
        self.config = MODULE.read_json(ROOT / "tests" / "fixtures" / "progress-config.json")
        self.raw = MODULE.read_json(ROOT / "tests" / "fixtures" / "progress-project.json")
        self.history = MODULE.read_json(ROOT / "tests" / "fixtures" / "progress-history.json")
        self.registry = MODULE.read_registry(ROOT / "tests" / "fixtures" / "progress-registry.csv")

    def project_response(
        self,
        node,
        *,
        total_count=1,
        has_next_page=False,
        end_cursor=None,
    ):
        return {
            "data": {
                "node": {
                    "title": "ARRP",
                    "items": {
                        "totalCount": total_count,
                        "nodes": [node],
                        "pageInfo": {
                            "hasNextPage": has_next_page,
                            "endCursor": end_cursor,
                        },
                    }
                }
            }
        }

    def pagination_node(self):
        return {
            "id": "PVTI-PAGINATION",
            "fieldValues": {
                "totalCount": 0,
                "nodes": [],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            },
            "content": {
                "__typename": "Issue",
                "labels": {
                    "totalCount": 0,
                    "nodes": [],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                },
                "assignees": {
                    "totalCount": 0,
                    "nodes": [],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                },
                "subIssues": {
                    "totalCount": 0,
                    "nodes": [],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                },
            },
        }

    def test_project_item_pagination_fails_closed_on_under_returned_total(self):
        response = self.project_response(
            self.pagination_node(),
            total_count=2,
        )
        with (
            mock.patch.object(MODULE, "graphql_request", return_value=response),
            self.assertRaisesRegex(
                RuntimeError,
                "Project item pagination is incomplete",
            ),
        ):
            MODULE.fetch_project(self.config, "token")

    def test_project_item_pagination_fails_closed_without_next_cursor(self):
        response = self.project_response(
            self.pagination_node(),
            has_next_page=True,
            end_cursor=None,
        )
        with (
            mock.patch.object(MODULE, "graphql_request", return_value=response),
            self.assertRaisesRegex(
                RuntimeError,
                "another page without a cursor",
            ),
        ):
            MODULE.fetch_project(self.config, "token")

    def test_nested_label_and_assignee_pagination_fail_visibly(self):
        node = self.pagination_node()
        node["content"]["labels"] = {
            "totalCount": 1,
            "nodes": [{"name": "kind: proposal"}],
            "pageInfo": {"hasNextPage": True, "endCursor": "cursor"},
        }
        node["content"]["assignees"] = {
            "totalCount": 2,
            "nodes": [{"login": "Thorncrag"}],
            "pageInfo": {"hasNextPage": False, "endCursor": None},
        }
        response = self.project_response(node)
        with mock.patch.object(
            MODULE,
            "graphql_request",
            return_value=response,
        ):
            with self.assertRaises(RuntimeError) as raised:
                MODULE.fetch_project(self.config, "token")
        message = str(raised.exception)
        self.assertIn("Project item content pagination is incomplete", message)
        self.assertIn("PVTI-PAGINATION:labels", message)
        self.assertIn("PVTI-PAGINATION:assignees", message)

    def test_nested_field_value_and_subissue_totals_fail_closed(self):
        fixtures = (
            (
                "fieldValues",
                "Project item field-value pagination is incomplete",
            ),
            (
                "subIssues",
                "Project issue sub-issue pagination is incomplete",
            ),
        )
        for connection_name, expected_message in fixtures:
            with self.subTest(connection=connection_name):
                node = self.pagination_node()
                target = (
                    node["fieldValues"]
                    if connection_name == "fieldValues"
                    else node["content"]["subIssues"]
                )
                target.update(
                    {
                        "totalCount": 2,
                        "nodes": [{"id": "only-node"}],
                    }
                )
                response = self.project_response(node)
                with (
                    mock.patch.object(
                        MODULE,
                        "graphql_request",
                        return_value=response,
                    ),
                    self.assertRaisesRegex(
                        RuntimeError,
                        expected_message,
                    ),
                ):
                    MODULE.fetch_project(self.config, "token")

    def test_includes_active_horizon_items_without_counting_them_as_proposals(self):
        title, items = MODULE.parse_items(self.raw, self.config, self.registry)
        self.assertEqual(title, "American Restoration and Resilience Project")
        self.assertEqual(len(items), 5)
        self.assertEqual(sum(item["ready"] for item in items), 1)
        mismatch = next(item for item in items if item["identifier"] == "JUD-011")
        self.assertFalse(mismatch["ready"])
        self.assertEqual(len(mismatch["warnings"]), 1)
        candidate = next(item for item in items if item["identifier"] == "HOR-029")
        self.assertEqual(candidate["kind"], "horizon")
        self.assertEqual(candidate["developmentLevel"], "Candidate")
        self.assertEqual(candidate["workflowStatus"], "Human decision needed")

        payload = MODULE.build_progress_payload(
            title,
            items,
            self.history,
            self.config,
            date(2026, 7, 15),
        )
        self.assertEqual(payload["metrics"]["total"], 4)
        self.assertEqual(
            [item["identifier"] for item in payload["candidates"]],
            ["HOR-029"],
        )

    def test_unmatched_registry_proposal_remains_visible_and_warns(self):
        registry = list(self.registry) + [{
            "GitHub Number": "999",
            "GitHub Issue": "https://github.com/Thorncrag/ARRP/issues/999",
            "Kind": "proposal",
            "GitHub Title": "TEST-999: Missing Project row",
            "Canonical Record": "areas/TEST/issues/TEST-999.md",
        }]
        _, items = MODULE.parse_items(self.raw, self.config, registry)
        missing = next(item for item in items if item["identifier"] == "TEST-999")
        self.assertEqual(len(items), 6)
        self.assertFalse(missing["ready"])
        self.assertEqual(missing["developmentLevel"], "Unspecified")
        self.assertEqual(missing["workflowStatus"], "Unspecified")
        self.assertIn("no matching Project item", missing["warnings"][0])

    def test_title_identifier_wins_when_merged_items_share_canonical_page(self):
        raw = deepcopy(self.raw)
        reg = raw["items"][1]
        reg["fieldValues"]["nodes"].append(
            {
                "__typename": "ProjectV2ItemFieldTextValue",
                "text": "REG-001: Congressional Mandate Enforcement",
                "field": {"name": "Title"},
            }
        )
        merged = deepcopy(reg)
        merged["id"] = "PVTI_MERGED"
        merged["fieldValues"]["nodes"] = [
            node
            for node in merged["fieldValues"]["nodes"]
            if (node.get("field") or {}).get("name") not in {"Title", "Status", "Development level", "Score"}
        ] + [
            {
                "__typename": "ProjectV2ItemFieldTextValue",
                "text": "HOR-018: Integrated into REG-001",
                "field": {"name": "Title"},
            },
            {
                "__typename": "ProjectV2ItemFieldSingleSelectValue",
                "name": "Development",
                "field": {"name": "Status"},
            },
        ]
        raw["items"].append(merged)
        _, items = MODULE.parse_items(raw, self.config, self.registry)
        proposal = next(item for item in items if item["identifier"] == "REG-001")
        self.assertEqual(proposal["developmentLevel"], "Developed proposal")
        self.assertEqual(proposal["workflowStatus"], "Audit needed")
        self.assertEqual(proposal["score"], 68)
        self.assertFalse(proposal["ready"])
        self.assertEqual(proposal["warnings"], [])

    def test_ready_development_level_without_score_emits_consistency_warning(self):
        raw = deepcopy(self.raw)
        nodes = raw["items"][0]["fieldValues"]["nodes"]
        raw["items"][0]["fieldValues"]["nodes"] = [
            node for node in nodes if (node.get("field") or {}).get("name") != "Score"
        ]
        _, items = MODULE.parse_items(raw, self.config, self.registry)
        ready = next(item for item in items if item["identifier"] == "DOJ-007")
        self.assertFalse(ready["ready"])
        self.assertIsNone(ready["score"])
        self.assertIn("is not counted", ready["warnings"][0])

    def test_development_status_is_not_inferred_from_proposal_vehicle_presence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            issue = root / "areas" / "DOM" / "issues" / "DOM-005.md"
            vehicle = root / "legislation" / "DOM-005.md"
            issue.parent.mkdir(parents=True)
            vehicle.parent.mkdir(parents=True)
            issue.write_text(
                "---\nlegislative_proposal: \"../../../legislation/DOM-005.md\"\n---\n",
                encoding="utf-8",
            )
            vehicle.write_text("# Proposed legislation\n", encoding="utf-8")
            _, items = MODULE.parse_items(self.raw, self.config, self.registry, root)
        development = next(item for item in items if item["identifier"] == "DOM-005")
        self.assertEqual(development["workflowStatus"], "Development")
        self.assertEqual(development["warnings"], [])

    def test_progress_item_carries_canonical_workflow_hold_reason(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            issue = root / "areas" / "DOJ" / "issues" / "DOJ-007.md"
            issue.parent.mkdir(parents=True)
            issue.write_text(
                '---\nworkflow_hold_reason: "Waiting for a controlling decision."\n---\n',
                encoding="utf-8",
            )
            _, items = MODULE.parse_items(self.raw, self.config, self.registry, root)
        record = next(item for item in items if item["identifier"] == "DOJ-007")
        self.assertEqual(record["explanation"], "Waiting for a controlling decision.")

    def test_workflow_status_does_not_change_development_progress(self):
        raw = deepcopy(self.raw)
        nodes = raw["items"][0]["fieldValues"]["nodes"]
        for node in nodes:
            if (node.get("field") or {}).get("name") == "Status":
                node["name"] = "Publication approval"
        _, items = MODULE.parse_items(raw, self.config, self.registry)
        completed = next(item for item in items if item["identifier"] == "DOJ-007")
        self.assertTrue(completed["ready"])
        self.assertEqual(completed["developmentLevel"], "Review ready")
        self.assertEqual(completed["workflowStatus"], "Publication approval")
        self.assertEqual(completed["warnings"], [])

    def test_unapproved_workflow_status_emits_lifecycle_warning(self):
        raw = deepcopy(self.raw)
        for node in raw["items"][0]["fieldValues"]["nodes"]:
            if (node.get("field") or {}).get("name") == "Status":
                node["name"] = "Legacy workflow"
        _, items = MODULE.parse_items(raw, self.config, self.registry)
        record = next(item for item in items if item["identifier"] == "DOJ-007")
        self.assertEqual(len(record["warnings"]), 1)
        self.assertIn("not an approved workflow status", record["warnings"][0])
        self.assertIn("needs: monitoring label", record["warnings"][0])

    def test_noncanonical_development_level_emits_maturity_warning(self):
        raw = deepcopy(self.raw)
        for node in raw["items"][0]["fieldValues"]["nodes"]:
            if (node.get("field") or {}).get("name") == "Development level":
                node["name"] = "Almost ready"
        _, items = MODULE.parse_items(raw, self.config, self.registry)
        record = next(item for item in items if item["identifier"] == "DOJ-007")
        self.assertFalse(record["ready"])
        self.assertTrue(
            any("six canonical maturity values" in warning for warning in record["warnings"])
        )

    def test_noncanonical_ready_level_configuration_fails_closed(self):
        config = deepcopy(self.config)
        config["goal"]["readyDevelopmentLevels"].append("Almost ready")
        with self.assertRaisesRegex(RuntimeError, "noncanonical Development level"):
            MODULE.parse_items(self.raw, config, self.registry)

    def test_monitoring_label_does_not_replace_workflow_status(self):
        raw = deepcopy(self.raw)
        raw["items"][2]["content"]["labels"]["nodes"].append({"name": "needs: monitoring"})
        _, items = MODULE.parse_items(raw, self.config, self.registry)
        record = next(item for item in items if item["identifier"] == "DOM-005")
        self.assertEqual(record["workflowStatus"], "Development")
        self.assertEqual(record["warnings"], [])

    def test_production_config_projects_only_approved_workflow_statuses(self):
        config = MODULE.read_json(
            ROOT / "framework/project/interfaces/project-console-progress.json"
        )
        self.assertEqual(
            tuple(config["workflowStatuses"]),
            MODULE.APPROVED_WORKFLOW_STATUSES,
        )

    def test_builder_exposes_only_the_canonical_six_development_levels(self):
        title, items = MODULE.parse_items(self.raw, self.config, self.registry)
        payload = MODULE.build_progress_payload(
            title, items, self.history, self.config, date(2026, 7, 15)
        )
        self.assertEqual(
            tuple(payload["developmentLevels"]),
            MODULE.APPROVED_DEVELOPMENT_LEVELS,
        )
        self.assertEqual(len(payload["developmentLevels"]), 6)

    def test_retired_progress_workflow_and_publisher_are_absent(self):
        self.assertFalse(
            (ROOT / ".github/workflows/project-console-progress.yml").exists()
        )
        self.assertFalse(
            (ROOT / "scripts/publish_project_console_progress.py").exists()
        )

    def test_retrospective_seed_extends_history_without_replacing_live_dates(self):
        config = deepcopy(self.config)
        config["goal"]["historyStartDate"] = "2026-06-24"
        seed = {
            "schemaVersion": 1,
            "snapshots": [
                {
                    "date": "2026-06-24",
                    "total": 4,
                    "ready": 0,
                    "readyIssues": [],
                    "scores": {},
                },
                {"date": "2026-07-01", "total": 4, "ready": 0},
            ],
        }
        history = MODULE.combine_histories(seed, self.history)
        title, items = MODULE.parse_items(self.raw, config, self.registry)
        payload = MODULE.build_progress_payload(title, items, history, config, date(2026, 7, 15))
        self.assertEqual(payload["history"][0]["date"], "2026-06-24")
        retained_baseline = next(entry for entry in payload["history"] if entry["date"] == "2026-07-01")
        self.assertEqual(retained_baseline["ready"], 1)
        self.assertEqual(payload["metrics"]["rollingWeeklyVelocity"], 0.33)
        self.assertFalse(payload["movement"]["scoresAvailable"])
        self.assertEqual(payload["history"][0]["date"], "2026-06-24")

    def test_repository_retrospective_seed_preserves_baseline_after_scope_changes(self):
        seed = MODULE.read_json(ROOT / ".github" / "progress-history-seed.json")
        config = MODULE.read_json(
            ROOT / "framework/project/interfaces/project-console-progress.json"
        )
        registry = MODULE.read_registry(ROOT / "inventory" / "github_issue_registry.csv")
        evidence = seed["attainmentEvidence"]
        identifiers = {entry["identifier"] for entry in evidence}
        active_proposals = [row for row in registry if MODULE.normalize(row["Kind"]) == "proposal"]
        # The retrospective baseline remains historical even after proposal
        # admission, merger, or retirement changes the live denominator.
        self.assertGreater(len(active_proposals), len(evidence))
        self.assertEqual(config["goal"]["baselineTotal"], 204)
        self.assertEqual(len(evidence), 23)
        self.assertEqual(len(identifiers), 23)
        self.assertEqual(seed["snapshots"][-1]["ready"], 23)
        self.assertEqual(set(seed["snapshots"][-1]["readyIssues"]), identifiers)
        for snapshot in seed["snapshots"]:
            self.assertEqual(snapshot["total"], 204)
            self.assertEqual(snapshot["ready"], len(snapshot["readyIssues"]))
        for entry in evidence:
            audit = ROOT / entry["audit"]
            self.assertTrue(audit.is_file(), entry["audit"])
            self.assertIn("### {} —".format(entry["date"]), audit.read_text(encoding="utf-8"))

    def test_builds_metrics_history_and_forecast_inputs(self):
        title, items = MODULE.parse_items(self.raw, self.config, self.registry)
        payload = MODULE.build_progress_payload(title, items, self.history, self.config, date(2026, 7, 15))
        self.assertEqual(payload["metrics"]["ready"], 1)
        self.assertEqual(payload["metrics"]["total"], 4)
        self.assertEqual(payload["metrics"]["remaining"], 3)
        self.assertEqual(payload["metrics"]["percentReady"], 25.0)
        self.assertEqual(payload["history"][-1]["date"], "2026-07-15")
        self.assertIn(
            "repository HEAD alone does not",
            payload["freshness"]["supersession_rule"],
        )
        self.assertEqual(len(payload["warnings"]), 1)
        self.assertTrue(payload["movement"]["available"])
        self.assertEqual(payload["movement"]["scoresImproved"], 2)
        self.assertTrue(payload["movement"]["scoresAvailable"])
        self.assertEqual(payload["movement"]["netScoreChange"], 13.0)
        self.assertGreater(payload["metrics"]["requiredPerWeek"], 0)
        self.assertEqual(payload["goal"]["targetDate"], "2026-12-31")
        self.assertEqual(len(payload["proposals"]), 4)
        self.assertEqual(
            [item["identifier"] for item in payload["candidates"]],
            ["HOR-029"],
        )

    def test_portfolio_architecture_separates_scope_from_earned_readiness(self):
        config = MODULE.read_json(
            ROOT / "framework/project/interfaces/project-console-progress.json"
        )
        architecture = MODULE.portfolio_architecture(
            {
                "date": "2026-07-25",
                "total": 81,
                "ready": 27,
            },
            config,
            ROOT,
        )
        self.assertTrue(architecture["available"])
        self.assertEqual(
            [step["total"] for step in architecture["steps"]],
            [204, 198, 77, 81],
        )
        self.assertEqual(
            architecture["steps"][-1]["reasonCode"],
            "later_admissions",
        )
        self.assertEqual(
            architecture["earnedReadiness"],
            {
                "baselineDate": "2026-07-13",
                "baselineReady": 23,
                "currentDate": "2026-07-25",
                "currentReady": 27,
                "netEarned": 4,
                "separateFromScope": True,
            },
        )
        self.assertIn("123 fewer", architecture["explanation"])

    def test_portfolio_architecture_rejects_noncanonical_record_path(self):
        config = MODULE.read_json(
            ROOT / "framework/project/interfaces/project-console-progress.json"
        )
        config["portfolioArchitectureRecord"] = "../../outside.md"
        with self.assertRaisesRegex(ValueError, "canonical allowlisted record"):
            MODULE.portfolio_architecture(
                {"date": "2026-07-25", "total": 81, "ready": 27},
                config,
                ROOT,
            )

    def test_builder_rejects_inputs_outside_trusted_roots(self):
        with self.assertRaisesRegex(ValueError, "within the repository"):
            MODULE.trusted_input_path(
                Path("/etc/hosts"),
                purpose="Project Console config",
            )

    def test_builder_allows_temporary_fixture_inputs_only_when_declared(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "project.json"
            fixture.write_text("{}\n", encoding="utf-8")
            trusted = MODULE.trusted_input_path(
                fixture,
                purpose="Saved GitHub Project input",
                allow_system_temp=True,
            )
            self.assertEqual(trusted, fixture.resolve())
            with self.assertRaisesRegex(ValueError, "within the repository"):
                MODULE.trusted_input_path(
                    fixture,
                    purpose="Project Console config",
                )

    def test_projects_nonproposal_project_items_as_typed_delivery_work(self):
        raw = deepcopy(self.raw)
        raw["items"].append(
            {
                "id": "PVTI_DELIVERY",
                "fieldValues": {
                    "nodes": [
                        {
                            "name": "Publication approval",
                            "field": {"name": "Status"},
                        },
                        {
                            "name": "Project governance",
                            "field": {"name": "Workstream"},
                        },
                        {
                            "name": "Critical",
                            "field": {"name": "Priority"},
                        },
                        {
                            "name": "Yes",
                            "field": {"name": "Release blocker"},
                        },
                        {
                            "text": "Confirm every publication prerequisite.",
                            "field": {"name": "Next action"},
                        },
                        {
                            "text": "Clean final integrity and publication readback.",
                            "field": {"name": "Validation requirement"},
                        },
                    ]
                },
                "content": {
                    "__typename": "Issue",
                    "number": 900,
                    "title": "Pre-publication final audit",
                    "url": "https://github.com/Thorncrag/ARRP/issues/900",
                    "state": "OPEN",
                    "repository": {"nameWithOwner": "Thorncrag/ARRP"},
                    "labels": {"nodes": [{"name": "kind: governance"}]},
                    "assignees": {"nodes": [{"login": "Thorncrag"}]},
                    "milestone": {
                        "title": "Initial release",
                        "dueOn": "2026-12-31T00:00:00Z",
                        "url": "https://github.com/Thorncrag/ARRP/milestone/1",
                    },
                    "parent": None,
                    "subIssues": {
                        "totalCount": 1,
                        "nodes": [
                            {
                                "number": 901,
                                "title": "Child",
                                "url": "https://github.com/Thorncrag/ARRP/issues/901",
                                "state": "CLOSED",
                            }
                        ],
                    },
                },
            }
        )
        title, items = MODULE.parse_items(raw, self.config, self.registry)
        delivery = next(item for item in items if item["projectItemId"] == "PVTI_DELIVERY")
        self.assertFalse(delivery["isIssueDevelopment"])
        self.assertEqual(delivery["issueIdentity"], "Thorncrag/ARRP#900")
        self.assertEqual(delivery["priority"], "Critical")
        self.assertEqual(delivery["releaseBlocker"], "Yes")
        self.assertEqual(delivery["owner"], "Thorncrag")
        self.assertEqual(delivery["subissueProgress"]["percent"], 100.0)
        payload = MODULE.build_progress_payload(
            title,
            items,
            self.history,
            self.config,
            date(2026, 7, 15),
        )
        self.assertEqual(payload["metrics"]["total"], 4)
        self.assertEqual(len(payload["delivery_items"]), 1)
        self.assertEqual(
            payload["delivery_items"][0]["title"],
            "Pre-publication final audit",
        )

    def test_july_25_project_item_reconciliation_fixture(self):
        title, parsed = MODULE.parse_items(
            self.raw,
            self.config,
            self.registry,
        )
        proposal_template = next(
            item for item in parsed if item["kind"] == "proposal"
        )
        candidate_template = next(
            item for item in parsed if item["kind"] == "horizon"
        )
        items = []
        for index in range(81):
            item = deepcopy(proposal_template)
            item.update(
                {
                    "identifier": f"PRO-{index + 1:03d}",
                    "projectItemId": f"PVTI_PRO_{index + 1:03d}",
                    "releaseBlocker": "Yes" if index < 26 else None,
                    "warnings": [],
                }
            )
            items.append(item)
        for index in range(17):
            item = deepcopy(candidate_template)
            item.update(
                {
                    "identifier": f"HOR-{index + 1:03d}",
                    "projectItemId": f"PVTI_HOR_{index + 1:03d}",
                    "releaseBlocker": None,
                    "warnings": [],
                }
            )
            items.append(item)
        for index in range(12):
            item = deepcopy(candidate_template)
            item.update(
                {
                    "kind": "task",
                    "identifier": f"DEL-{index + 1:03d}",
                    "projectItemId": f"PVTI_DEL_{index + 1:03d}",
                    "isIssueDevelopment": False,
                    "releaseBlocker": None,
                    "warnings": [],
                }
            )
            items.append(item)
        payload = MODULE.build_progress_payload(
            title,
            items,
            self.history,
            self.config,
            date(2026, 7, 25),
        )
        self.assertEqual(len(payload["proposals"]), 81)
        self.assertEqual(len(payload["candidates"]), 17)
        self.assertEqual(len(payload["delivery_items"]), 12)
        self.assertEqual(
            payload["projectItemReconciliation"],
            {
                "totalProjectItems": 110,
                "proposalItems": 81,
                "candidateItems": 17,
                "portfolioItems": 98,
                "deliveryItems": 12,
                "releaseBlockers": 26,
                "partitionComplete": True,
                "releaseBlockerFieldProjected": True,
            },
        )

    def test_progress_history_fails_closed_instead_of_erasing_invalid_rows(self):
        with self.assertRaisesRegex(RuntimeError, "validation failed"):
            MODULE.valid_history(
                {
                    "schemaVersion": 1,
                    "snapshots": [
                        {"date": "not-a-date", "total": 4, "ready": 1}
                    ],
                }
            )

    def test_scope_removal_is_not_reported_as_readiness_regression(self):
        items = [
            {
                "identifier": "TEST-001",
                "url": "https://example.test/1",
            }
        ]
        history = {
            "snapshots": [
                {
                    "date": "2026-07-01",
                    "total": 2,
                    "ready": 2,
                    "detailAvailable": True,
                    "eligibleIssues": ["TEST-001", "TEST-002"],
                    "readyIssues": ["TEST-001", "TEST-002"],
                    "scores": {},
                },
                {
                    "date": "2026-07-15",
                    "total": 1,
                    "ready": 1,
                    "detailAvailable": True,
                    "eligibleIssues": ["TEST-001"],
                    "readyIssues": ["TEST-001"],
                    "scores": {},
                },
            ]
        }
        movement = MODULE.portfolio_movement(
            items, history, date(2026, 7, 15), 28
        )
        self.assertEqual(movement["fellBelowReady"], [])
        self.assertEqual(
            [item["identifier"] for item in movement["scopeRemoved"]],
            ["TEST-002"],
        )
        self.assertTrue(movement["scopeChangesExcludedFromAttainment"])

    def test_progress_build_writes_data_only_files(self):
        title, items = MODULE.parse_items(self.raw, self.config, self.registry)
        payload = MODULE.build_progress_payload(title, items, self.history, self.config, date(2026, 7, 15))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "site"
            MODULE.write_progress_data(output, payload)
            self.assertEqual(sorted(path.name for path in output.iterdir()), ["history.json", "progress.json"])
            saved = json.loads((output / "progress.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["metrics"]["total"], 4)

    def test_vercel_config_excludes_data_branch_from_application_previews(self):
        config = json.loads((ROOT / "participate" / "vercel.json").read_text(encoding="utf-8"))
        self.assertFalse(config["git"]["deploymentEnabled"]["project-console-data"])


if __name__ == "__main__":
    unittest.main()
