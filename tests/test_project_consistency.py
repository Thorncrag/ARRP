import csv
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import scripts.audit_project_consistency as consistency
from scripts.audit_project_consistency import (
    ISSUE_PAGE_STATUSES,
    ISSUE_SNAPSHOT_WORD_GUIDELINE,
    PROJECT_WORKFLOW_STATUSES,
    ROOT,
    active_project_files,
    check_agent_runbooks,
    check_context_registry,
    check_github_pages_deployment,
    check_issue_pages,
    external_review_action_missing_components,
    expected_project_development_level,
    expected_project_workflow_status,
    github_repository_targets,
    is_recognized_issue_page_status,
    is_recognized_project_status,
    issue_page_status_error,
    issue_snapshot_fields,
    issue_snapshot_word_counts,
    local_target,
    markdown_anchor_ids,
    markdown_report,
    monitoring_wrapper_missing_components,
    project_lifecycle_findings,
    project_status_reason_missing_components,
    project_status_reason_is_present,
    report,
    research_files,
    requires_workflow_hold_reason,
    source_citation_corpus,
    visible_markdown_word_count,
)
from scripts.prepare_public_site import discover_public_markdown


SOURCE_DEVELOPMENT_STUB_IDS = {
    "CIV-001",
    "CIV-009",
    "CLASS-011",
    "DOM-001",
    "EMOL-001",
    "FACT-001",
    "HER-001",
    "OVS-001",
    "PAR-001",
    "PRESS-001",
    "PRESS-003",
    "PRESS-006",
    "REC-001",
    "REG-006",
    "RET-001",
}


def lifecycle_findings(
    *,
    kind: str = "proposal",
    object_id: str = "TEST-001",
    metadata: dict[str, str] | None = None,
    issue_body: str = "",
    **overrides: object,
) -> list[tuple[str, str]]:
    item: dict[str, object] = {
        "content": {"number": 999},
        "status": "Development",
        "development level": "Admitted / undeveloped",
        "workstream": "Proposal development",
        "area": "TEST",
        "score": 0,
        "next audit": "Source-development pass",
    }
    item.update(overrides)
    return project_lifecycle_findings(
        kind=kind,
        object_id=object_id,
        metadata=metadata or {},
        project_item=item,
        issue_body=issue_body,
)


class RetiredControlPlaneTests(unittest.TestCase):
    def test_p6_control_plane_sources_are_absent(self):
        retired = (
            "scripts/run_chain_dispatcher.py",
            "scripts/run_coordinator_control.py",
            "scripts/build_automation_health_projection.py",
            "scripts/publish_project_console_progress.py",
            "scripts/publish_immutable_data_file.py",
            "framework/project/automation/configuration/launchd/com.thorncrag.arrp-run-coordinator.plist.example",
            "framework/project/automation/configuration/launchd/com.thorncrag.arrp-run-coordinator-control.plist.example",
        )
        self.assertEqual(
            [relative for relative in retired if (ROOT / relative).exists()],
            [],
        )
        self.assertEqual(
            consistency.source_domain_event_pipeline_findings(ROOT),
            [],
        )

    def test_github_validation_uses_repository_only_routing_authority(self):
        workflow = (
            ROOT / ".github" / "workflows" / "arrp-validation.yml"
        ).read_text(encoding="utf-8")
        normalized = " ".join(workflow.split())
        self.assertIn(
            "python scripts/audit_project_consistency.py "
            "--routing-authority repository-validation "
            "--exit-zero-on-findings",
            normalized,
        )
        self.assertIn(
            "python scripts/component_registry.py validate",
            normalized,
        )
        self.assertNotIn(
            "python scripts/build_elim_context.py "
            "--path-authority repository-validation",
            normalized,
        )
        self.assertNotIn(
            "audit_project_consistency.py "
            "--routing-authority production-canonical",
            normalized,
        )
        self.assertNotIn(
            "audit_project_consistency.py "
            "--routing-authority production-transaction",
            normalized,
        )


class GitHubIssueLinkTests(unittest.TestCase):
    CONTEXT_ROUTING_AUTHORITY_FIELDS = {
        "authority_mode",
        "validation_mode",
        "registry_revision",
        "registry_sha256",
        "configuration_valid",
        "authoritative",
        "executable",
        "authority_effective",
        "source_revision_authorized",
        "source_bytes_current",
        "canonical_history_confirmed",
        "receipt_trusted",
        "runtime_live",
        "predecessor_route_consulted",
        "activation_receipt_consulted",
    }

    def test_ignored_private_console_projection_is_an_optional_html_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            console = (
                root
                / "framework"
                / "project"
                / "interfaces"
                / "project-console"
            )
            console.mkdir(parents=True)
            page = console / "project-console.html"
            page.write_text(
                '<script src="data/private-github-security.js?v=1"></script>\n',
                encoding="utf-8",
            )
            failures: list[str] = []
            warnings: list[str] = []
            with (
                patch.object(consistency, "ROOT", root),
                patch.object(
                    consistency,
                    "active_project_files",
                    return_value=[page],
                ),
            ):
                consistency.check_html_links(failures, warnings)
            self.assertEqual(failures, [])
            self.assertEqual(warnings, [])

    def context_registry_fixture(self, root: Path) -> dict[str, object]:
        framework = root / "framework"
        framework.mkdir(parents=True)
        (root / "AGENTS.md").write_text(
            "---\n"
            "module_id: codex_bootstrap\n"
            "dependencies:\n"
            '  - "framework/FRAMEWORK.md"\n'
            '  - "framework/AGENT_OPERATING_RULES.md"\n'
            "---\n\n"
            "# Bootstrap\n",
            encoding="utf-8",
        )
        (framework / "FRAMEWORK.md").write_text("# Framework\n", encoding="utf-8")
        (framework / "AGENT_OPERATING_RULES.md").write_text(
            "# Agent rules\n",
            encoding="utf-8",
        )
        (framework / "EXTRA.md").write_text("# Extra authority\n", encoding="utf-8")
        handoffs = framework / "handoffs"
        handoffs.mkdir(parents=True)
        (handoffs / "current-task.md").write_text(
            "# Current audit\n",
            encoding="utf-8",
        )
        return {
            "required_modules": [
                "framework_kernel",
                "agent_rules_kernel",
                "task_handoff",
            ],
            "documents": {
                "codex_bootstrap": {
                    "path": "AGENTS.md",
                    "hash_policy": "pinned",
                    "governing": True,
                    "requires": [
                        "framework_kernel",
                        "agent_rules_kernel",
                    ],
                },
                "framework_kernel": {
                    "path": "framework/FRAMEWORK.md",
                    "hash_policy": "pinned",
                    "governing": True,
                },
                "agent_rules_kernel": {
                    "path": "framework/AGENT_OPERATING_RULES.md",
                    "hash_policy": "pinned",
                    "governing": True,
                },
                "task_handoff": {
                    "path": "framework/handoffs/current-task.md",
                    "hash_policy": "runtime",
                    "governing": False,
                },
                "extra": {
                    "path": "framework/EXTRA.md",
                    "hash_policy": "pinned",
                    "governing": True,
                },
            },
            "profiles": {
                "comprehensive_review": {
                    "include_all_governing": True,
                }
            },
        }

    def context_registry_fixture_path_authority(
        self,
        root: Path,
    ) -> consistency.ProjectPathAuthority:
        return consistency.ProjectPathAuthority.fixture(
            root,
            repository_root=root,
            state_root=root,
            output_root=root,
        )

    def context_registry_view(
        self,
        route: dict[str, object],
        *,
        mode: str = "adopted_configuration_validation",
    ) -> dict[str, object]:
        postures = {
            "proposed_revision_validation": {
                "authoritative": False,
                "executable": False,
                "authority_effective": False,
                "source_revision_authorized": False,
                "source_bytes_current": False,
                "canonical_history_confirmed": False,
                "receipt_trusted": False,
                "runtime_live": "not_checked",
                "activation_receipt_consulted": False,
                "predecessor_route_consulted": False,
            },
            "adopted_configuration_validation": {
                "authoritative": False,
                "executable": False,
                "authority_effective": False,
                "source_revision_authorized": False,
                "source_bytes_current": True,
                "canonical_history_confirmed": False,
                "receipt_trusted": False,
                "runtime_live": "not_checked",
                "activation_receipt_consulted": False,
                "predecessor_route_consulted": False,
            },
            "live_authority_validation": {
                "authoritative": True,
                "executable": False,
                "authority_effective": True,
                "source_revision_authorized": True,
                "source_bytes_current": True,
                "canonical_history_confirmed": True,
                "receipt_trusted": True,
                "runtime_live": "not_checked",
                "activation_receipt_consulted": True,
                "predecessor_route_consulted": False,
            },
        }
        return {
            "schema_version": 4,
            "validation_mode": mode,
            "registry_id": "COMPONENT-REGISTRY",
            "registry_revision": 5,
            "registry_sha256": "a" * 64,
            "registry_path": "framework/component-registry.json",
            **postures[mode],
            "route": route,
        }

    def test_context_registry_requires_kernels_runtime_checkpoint_and_full_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = self.context_registry_fixture(root)

            failures: list[str] = []
            warnings: list[str] = []
            authority = self.context_registry_fixture_path_authority(root)
            with (
                patch.object(consistency, "ROOT", root),
                patch.object(
                    consistency,
                    "load_fixture_component_registry_configuration_routing_view",
                    return_value=self.context_registry_view(baseline),
                ),
            ):
                envelope = check_context_registry(
                    failures,
                    warnings,
                    authority_mode="fixture",
                    fixture_path_authority=authority,
                )
            self.assertEqual(failures, [])
            self.assertEqual(warnings, [])
            self.assertEqual(
                envelope["validation_mode"],
                "adopted_configuration_validation",
            )

            variants = []
            missing_kernel = {
                **baseline,
                "required_modules": ["framework_kernel", "task_handoff"],
            }
            variants.append((missing_kernel, "required floor omits: agent_rules_kernel"))

            wrong_current = {
                **baseline,
                "documents": {
                    **baseline["documents"],
                    "task_handoff": {
                        "path": "framework/handoffs/current-task.md",
                        "hash_policy": "pinned",
                        "governing": True,
                    },
                },
            }
            variants.append(
                (
                    wrong_current,
                    "current-task handoff must be the required runtime-hashed",
                )
            )

            incomplete_review = {
                **baseline,
                "profiles": {
                    "comprehensive_review": {
                        "include_all_governing": False,
                    }
                },
            }
            variants.append(
                (
                    incomplete_review,
                    "comprehensive_review must include every governing",
                )
            )
            reversed_floor = {
                **baseline,
                "required_modules": list(reversed(baseline["required_modules"])),
            }
            variants.append(
                (
                    reversed_floor,
                    "required floor must be exactly "
                    "framework_kernel, agent_rules_kernel, task_handoff in that order",
                )
            )

            for manifest, expected in variants:
                with self.subTest(expected=expected):
                    failures = []
                    warnings = []
                    with (
                        patch.object(consistency, "ROOT", root),
                        patch.object(
                            consistency,
                            "load_fixture_component_registry_configuration_routing_view",
                            return_value=self.context_registry_view(manifest),
                        ),
                    ):
                        check_context_registry(
                            failures,
                            warnings,
                            authority_mode="fixture",
                            fixture_path_authority=authority,
                        )
                    self.assertTrue(
                        any(expected in failure for failure in failures),
                        failures,
                    )
            self.assertEqual(warnings, [])

    def test_context_registry_checks_root_agents_declarations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.context_registry_fixture(root)
            (root / "AGENTS.md").write_text(
                "---\n"
                "module_id: wrong_bootstrap\n"
                "dependencies:\n"
                '  - "framework/FRAMEWORK.md"\n'
                "---\n\n"
                "# Bootstrap\n",
                encoding="utf-8",
            )
            failures: list[str] = []
            warnings: list[str] = []
            authority = self.context_registry_fixture_path_authority(root)
            with (
                patch.object(consistency, "ROOT", root),
                patch.object(
                    consistency,
                    "load_fixture_component_registry_configuration_routing_view",
                    return_value=self.context_registry_view(manifest),
                ),
            ):
                check_context_registry(
                    failures,
                    warnings,
                    authority_mode="fixture",
                    fixture_path_authority=authority,
                )

            self.assertTrue(
                any(
                    "AGENTS.md front-matter module_id differs" in failure
                    and "wrong_bootstrap" in failure
                    and "codex_bootstrap" in failure
                    for failure in failures
                ),
                failures,
            )
            self.assertTrue(
                any(
                    "codex_bootstrap front-matter dependencies differ" in failure
                    and "framework/AGENT_OPERATING_RULES.md" in failure
                    for failure in failures
                ),
                failures,
            )
            self.assertEqual(warnings, [])

    def test_context_registry_flags_unregistered_managed_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.context_registry_fixture(root)
            manifest["documents"] = {
                key: value
                for key, value in manifest["documents"].items()
                if key != "extra"
            }
            failures: list[str] = []
            warnings: list[str] = []
            authority = self.context_registry_fixture_path_authority(root)
            with (
                patch.object(consistency, "ROOT", root),
                patch.object(
                    consistency,
                    "load_fixture_component_registry_configuration_routing_view",
                    return_value=self.context_registry_view(manifest),
                ),
            ):
                check_context_registry(
                    failures,
                    warnings,
                    authority_mode="fixture",
                    fixture_path_authority=authority,
                )
            self.assertTrue(
                any(
                    "governing framework Markdown is absent" in failure
                    and "framework/EXTRA.md" in failure
                    for failure in failures
                ),
                failures,
            )
            self.assertEqual(warnings, [])

    def test_context_registry_checks_top_level_framework_yaml_dependency_arrays(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.context_registry_fixture(root)
            module = root / "framework/project/interfaces/project-console/specification.md"
            module.parent.mkdir(parents=True)
            module.write_text(
                "---\n"
                "module_id: project_tool_interface\n"
                "dependencies:\n"
                '  - "../AGENT_OPERATING_RULES.md"\n'
                "---\n\n"
                "# Interface\n",
                encoding="utf-8",
            )
            manifest["documents"]["project_tool_interface"] = {
                "path": "framework/project/interfaces/project-console/specification.md",
                "hash_policy": "pinned",
                "governing": True,
                "requires": ["framework_kernel"],
            }
            failures: list[str] = []
            warnings: list[str] = []
            authority = self.context_registry_fixture_path_authority(root)
            with (
                patch.object(consistency, "ROOT", root),
                patch.object(
                    consistency,
                    "load_fixture_component_registry_configuration_routing_view",
                    return_value=self.context_registry_view(manifest),
                ),
            ):
                check_context_registry(
                    failures,
                    warnings,
                    authority_mode="fixture",
                    fixture_path_authority=authority,
                )

            self.assertTrue(
                any(
                    "project_tool_interface front-matter dependencies differ" in failure
                    and "framework/project/interfaces/AGENT_OPERATING_RULES.md"
                    in failure
                    and "framework/FRAMEWORK.md" in failure
                    for failure in failures
                ),
                failures,
            )
            self.assertFalse(
                any("module_id differs" in failure for failure in failures),
                failures,
            )
            self.assertEqual(warnings, [])

    def test_context_registry_requires_module_front_matter_to_match_route_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.context_registry_fixture(root)
            module = root / "framework/standards/content/test-rule.md"
            module.parent.mkdir(parents=True)
            module.write_text(
                "---\n"
                'title: "Test Rule"\n'
                "dependencies: ../AGENT_OPERATING_RULES.md\n"
                "---\n\n"
                "# Test Rule\n",
                encoding="utf-8",
            )
            manifest["documents"]["test_rule"] = {
                "path": "framework/standards/content/test-rule.md",
                "hash_policy": "pinned",
                "governing": True,
                "requires": ["framework_kernel"],
            }
            failures: list[str] = []
            warnings: list[str] = []
            authority = self.context_registry_fixture_path_authority(root)
            with (
                patch.object(consistency, "ROOT", root),
                patch.object(
                    consistency,
                    "load_fixture_component_registry_configuration_routing_view",
                    return_value=self.context_registry_view(manifest),
                ),
            ):
                check_context_registry(
                    failures,
                    warnings,
                    authority_mode="fixture",
                    fixture_path_authority=authority,
                )
            self.assertTrue(
                any(
                    "test_rule front-matter dependencies differ" in failure
                    and "framework/standards/AGENT_OPERATING_RULES.md" in failure
                    and "framework/FRAMEWORK.md" in failure
                    for failure in failures
                ),
                failures,
            )
            self.assertEqual(warnings, [])

    def test_context_registry_dependency_transition_is_exact_and_status_sensitive(self):
        registry_path = "framework/component-registry.json"
        predecessor_paths = frozenset(
            {
                "framework/CONTEXT_ROUTING.md",
                "framework/PROJECT_STRUCTURE.md",
                "framework/project/REPOSITORY_MAP.md",
            }
        )
        transitions = {
            "codex_bootstrap": (
                [
                    "framework/FRAMEWORK.md",
                    "framework/AGENT_OPERATING_RULES.md",
                    "framework/handoffs/current-task.md",
                    "framework/CONTEXT_ROUTING.md",
                    "framework/PROJECT_STRUCTURE.md",
                ],
                [
                    "framework/FRAMEWORK.md",
                    "framework/AGENT_OPERATING_RULES.md",
                    "framework/handoffs/current-task.md",
                    registry_path,
                ],
            ),
            "interface_standard": (
                ["framework/PROJECT_STRUCTURE.md"],
                [registry_path],
            ),
            "navigation_inventory": (
                [
                    "framework/FRAMEWORK.md",
                    "framework/PROJECT_STRUCTURE.md",
                    "framework/standards/content/maturity-and-gates.md",
                ],
                [
                    "framework/FRAMEWORK.md",
                    registry_path,
                    "framework/standards/content/maturity-and-gates.md",
                ],
            ),
            "navigation_project_sync": (
                [
                    "framework/standards/content/navigation-and-indexes.md",
                    "framework/standards/content/topic-guides.md",
                    "framework/project/github/workflow.md",
                    "framework/project/REPOSITORY_MAP.md",
                    "framework/project/interfaces/visual-identity.md",
                ],
                [
                    "framework/standards/content/navigation-and-indexes.md",
                    "framework/standards/content/topic-guides.md",
                    "framework/project/github/workflow.md",
                    registry_path,
                    "framework/project/interfaces/visual-identity.md",
                ],
            ),
            "operation_governance_change_recording": (
                [
                    "framework/FRAMEWORK.md",
                    "framework/PROJECT_STRUCTURE.md",
                    "framework/standards/audits/change-audits.md",
                    "framework/project/workflows/project-update.md",
                ],
                [
                    "framework/FRAMEWORK.md",
                    registry_path,
                    "framework/standards/audits/change-audits.md",
                    "framework/project/workflows/project-update.md",
                ],
            ),
            "operation_project_update": (
                [
                    "framework/FRAMEWORK.md",
                    "framework/project/github/workflow.md",
                    "framework/PROJECT_STRUCTURE.md",
                    "framework/project/publication/print-assembly.md",
                    "framework/project/publication/first-release.md",
                    "framework/standards/audits/change-audits.md",
                    "framework/project/workflows/navigation-sync.md",
                    "framework/project/workflows/source-adjudication.md",
                ],
                [
                    "framework/FRAMEWORK.md",
                    "framework/project/github/workflow.md",
                    registry_path,
                    "framework/project/publication/print-assembly.md",
                    "framework/project/publication/first-release.md",
                    "framework/standards/audits/change-audits.md",
                    "framework/project/workflows/navigation-sync.md",
                    "framework/project/workflows/source-adjudication.md",
                ],
            ),
            "print_assembly": (
                [
                    "framework/standards/publication/print-assembly.md",
                    "framework/PROJECT_STRUCTURE.md",
                    "framework/project/workflows/source-adjudication.md",
                ],
                [
                    "framework/standards/publication/print-assembly.md",
                    registry_path,
                    "framework/project/workflows/source-adjudication.md",
                ],
            ),
            "project_runtime_authority": (
                [
                    "framework/AGENT_OPERATING_RULES.md",
                    "framework/PROJECT_STRUCTURE.md",
                    "framework/standards/automation/autonomous-execution.md",
                    "framework/project/github/disclosure-boundary.md",
                    "framework/project/automation/schemas/private-staging-authority.schema.json",
                ],
                [
                    "framework/AGENT_OPERATING_RULES.md",
                    registry_path,
                    "framework/standards/automation/autonomous-execution.md",
                    "framework/project/github/disclosure-boundary.md",
                    "framework/project/automation/schemas/private-staging-authority.schema.json",
                ],
            ),
            "source_catalogs": (
                [
                    "framework/standards/sources/claims-and-citations.md",
                    "framework/standards/content/record-architecture.md",
                    "framework/PROJECT_STRUCTURE.md",
                ],
                [
                    "framework/standards/sources/claims-and-citations.md",
                    "framework/standards/content/record-architecture.md",
                    registry_path,
                ],
            ),
        }

        for document_id, (candidate_expected, declared) in transitions.items():
            with self.subTest(document_id=document_id, mode="candidate"):
                self.assertFalse(
                    consistency.context_registry_dependencies_match(
                        declared,
                        candidate_expected,
                        validation_mode="adopted_configuration_validation",
                        predecessor_paths=predecessor_paths,
                    )
                )
            active_expected = [
                dependency
                for dependency in candidate_expected
                if dependency not in predecessor_paths
            ]
            with self.subTest(document_id=document_id, mode="active"):
                self.assertTrue(
                    consistency.context_registry_dependencies_match(
                        declared,
                        active_expected,
                        validation_mode="adopted_configuration_validation",
                        predecessor_paths=predecessor_paths,
                    )
                )
                self.assertFalse(
                    consistency.context_registry_dependencies_match(
                        candidate_expected,
                        active_expected,
                        validation_mode="adopted_configuration_validation",
                        predecessor_paths=predecessor_paths,
                    )
                )

        candidate_expected, declared = transitions["codex_bootstrap"]
        invalid_declarations = {
            "wrong_order": [
                registry_path,
                *declared[:-1],
            ],
            "duplicate_registry": [
                *declared,
                registry_path,
            ],
            "missing_registry": declared[:-1],
            "non_predecessor_substitution": [
                "framework/FRAMEWORK.md",
                registry_path,
                "framework/handoffs/current-task.md",
            ],
        }
        for case, invalid in invalid_declarations.items():
            with self.subTest(case=case):
                self.assertFalse(
                    consistency.context_registry_dependencies_match(
                        invalid,
                        candidate_expected,
                        validation_mode="adopted_configuration_validation",
                        predecessor_paths=predecessor_paths,
                    )
                )

        stage2_expected = [
            "framework/FRAMEWORK.md",
            "framework/handoffs/current-task.md",
        ]
        stage2_declared = [
            "framework/FRAMEWORK.md",
            registry_path,
            "framework/handoffs/current-task.md",
        ]
        self.assertTrue(
            consistency.context_registry_dependencies_match(
                stage2_declared,
                stage2_expected,
                validation_mode="adopted_configuration_validation",
                predecessor_paths=predecessor_paths,
            )
        )
        for invalid in (
            [registry_path, registry_path, *stage2_expected],
            [registry_path, *reversed(stage2_expected)],
            [*stage2_expected, "framework/PROJECT_STRUCTURE.md"],
        ):
            self.assertFalse(
                consistency.context_registry_dependencies_match(
                    invalid,
                    stage2_expected,
                    validation_mode="adopted_configuration_validation",
                    predecessor_paths=predecessor_paths,
                )
            )

    def test_context_registry_rejects_standard_dependency_on_project_layer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.context_registry_fixture(root)
            project_module = root / "framework/project/profile/exact-values.md"
            project_module.parent.mkdir(parents=True)
            project_module.write_text("# Exact Values\n", encoding="utf-8")
            standard = root / "framework/standards/content/reusable-rule.md"
            standard.parent.mkdir(parents=True)
            standard.write_text(
                "---\n"
                "dependencies:\n"
                '  - "../../project/profile/exact-values.md"\n'
                "---\n\n"
                "# Reusable Rule\n",
                encoding="utf-8",
            )
            manifest["documents"]["project_exact"] = {
                "path": "framework/project/profile/exact-values.md",
                "hash_policy": "pinned",
                "governing": True,
            }
            manifest["documents"]["reusable_rule"] = {
                "path": "framework/standards/content/reusable-rule.md",
                "hash_policy": "pinned",
                "governing": True,
                "requires": ["project_exact"],
            }
            failures: list[str] = []
            warnings: list[str] = []
            authority = self.context_registry_fixture_path_authority(root)
            with (
                patch.object(consistency, "ROOT", root),
                patch.object(
                    consistency,
                    "load_fixture_component_registry_configuration_routing_view",
                    return_value=self.context_registry_view(manifest),
                ),
            ):
                check_context_registry(
                    failures,
                    warnings,
                    authority_mode="fixture",
                    fixture_path_authority=authority,
                )

            self.assertTrue(
                any(
                    "reusable standard "
                    "framework/standards/content/reusable-rule.md depends on "
                    "project-specific or historical module "
                    "framework/project/profile/exact-values.md"
                    in failure
                    for failure in failures
                ),
                failures,
            )
            self.assertEqual(warnings, [])

    def test_context_registry_fails_closed_for_stale_or_placeholder_hashes(self):
        for error in (
            "document framework_kernel hash changed: expected old, found new",
            "document framework_kernel has no integration-pinned sha256",
        ):
            with self.subTest(error=error):
                failures: list[str] = []
                warnings: list[str] = []
                with patch.object(
                    consistency,
                    "_load_context_registry_routing_view",
                    side_effect=consistency.ComponentRegistryError(error),
                ):
                    check_context_registry(
                        failures,
                        warnings,
                        authority_mode="repository-validation",
                    )
                self.assertEqual(len(failures), 1)
                self.assertIn(
                    "Component Registry routing authority validation failed",
                    failures[0],
                )
                self.assertIn(error, failures[0])
                self.assertEqual(warnings, [])

    def test_context_registry_configuration_modes_use_zero_argument_loader(self):
        for mode in (
            "proposed_revision_validation",
            "adopted_configuration_validation",
        ):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                route = self.context_registry_fixture(root)
                view = self.context_registry_view(route, mode=mode)
                failures: list[str] = []
                warnings: list[str] = []
                with (
                    patch.object(consistency, "ROOT", root),
                    patch.object(
                        consistency,
                        "load_component_registry_configuration_routing_view",
                        return_value=view,
                    ) as configuration_loader,
                    patch.object(
                        consistency,
                        "load_validated_component_registry_routing_view",
                    ) as production_loader,
                    patch.object(
                        consistency,
                        "load_fixture_component_registry_configuration_routing_view",
                    ) as fixture_loader,
                ):
                    envelope = check_context_registry(
                        failures,
                        warnings,
                        authority_mode="repository-validation",
                    )

                configuration_loader.assert_called_once_with()
                production_loader.assert_not_called()
                fixture_loader.assert_not_called()
                self.assertEqual(failures, [])
                self.assertEqual(warnings, [])
                self.assertEqual(
                    set(envelope),
                    self.CONTEXT_ROUTING_AUTHORITY_FIELDS,
                )
                self.assertEqual(
                    envelope["authority_mode"],
                    "repository-validation",
                )
                self.assertTrue(envelope["configuration_valid"])
                self.assertEqual(envelope["validation_mode"], mode)
                self.assertFalse(envelope["authoritative"])
                self.assertFalse(envelope["executable"])
                self.assertFalse(envelope["authority_effective"])
                self.assertFalse(envelope["source_revision_authorized"])
                self.assertEqual(
                    envelope["source_bytes_current"],
                    mode == "adopted_configuration_validation",
                )
                self.assertFalse(envelope["canonical_history_confirmed"])
                self.assertFalse(envelope["receipt_trusted"])
                self.assertEqual(envelope["runtime_live"], "not_checked")
                self.assertFalse(envelope["activation_receipt_consulted"])

    def test_context_registry_production_uses_only_fixed_runtime_loader(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            route = self.context_registry_fixture(root)
            view = self.context_registry_view(
                route,
                mode="live_authority_validation",
            )
            authority = SimpleNamespace(mode="production_transaction")
            failures: list[str] = []
            warnings: list[str] = []
            with (
                patch.object(consistency, "ROOT", root),
                patch.object(
                    consistency,
                    "_production_context_registry_path_authority",
                    return_value=authority,
                ),
                patch.object(
                    consistency,
                    "load_validated_component_registry_routing_view",
                    return_value=view,
                ) as production_loader,
                patch.object(
                    consistency,
                    "load_component_registry_configuration_routing_view",
                ) as configuration_loader,
            ):
                envelope = check_context_registry(
                    failures,
                    warnings,
                    authority_mode="production-transaction",
                )

            production_loader.assert_called_once_with(authority)
            configuration_loader.assert_not_called()
            self.assertEqual(failures, [])
            self.assertEqual(warnings, [])
            self.assertEqual(
                set(envelope),
                self.CONTEXT_ROUTING_AUTHORITY_FIELDS,
            )
            self.assertEqual(
                envelope["authority_mode"],
                "production-transaction",
            )
            self.assertTrue(envelope["configuration_valid"])
            self.assertEqual(
                envelope["validation_mode"],
                "live_authority_validation",
            )
            self.assertTrue(envelope["authoritative"])
            self.assertFalse(envelope["executable"])
            self.assertTrue(envelope["authority_effective"])
            self.assertTrue(envelope["source_revision_authorized"])
            self.assertTrue(envelope["source_bytes_current"])
            self.assertTrue(envelope["canonical_history_confirmed"])
            self.assertTrue(envelope["receipt_trusted"])
            self.assertEqual(envelope["runtime_live"], "not_checked")
            self.assertTrue(envelope["activation_receipt_consulted"])

    def test_context_registry_active_mode_checks_current_markdown_without_opening_predecessors(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            route = self.context_registry_fixture(root)
            view = self.context_registry_view(
                route,
                mode="adopted_configuration_validation",
            )
            archive = root / "framework" / "archive" / "authorities"
            archive.mkdir(parents=True)
            (archive / "CONTEXT_ROUTING.md").write_text(
                "# Retired context routing\n",
                encoding="utf-8",
            )
            (archive / "context-routes.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            predecessor_paths = {
                "framework/CONTEXT_ROUTING.md",
                "framework/project/automation/context-routes.json",
                "framework/archive/authorities/CONTEXT_ROUTING.md",
                "framework/archive/authorities/context-routes.json",
            }
            current_markdown = {
                str(spec["path"])
                for spec in route["documents"].values()
                if str(spec["path"]).endswith(".md")
            }
            visited: set[str] = set()
            original_read = consistency.read

            def guarded_read(path: Path) -> str:
                relative = path.resolve().relative_to(root.resolve()).as_posix()
                if relative in predecessor_paths:
                    raise AssertionError(
                        f"active routing validation opened predecessor {relative}"
                    )
                visited.add(relative)
                return original_read(path)

            failures: list[str] = []
            warnings: list[str] = []
            with (
                patch.object(consistency, "ROOT", root),
                patch.object(
                    consistency,
                    "load_component_registry_configuration_routing_view",
                    return_value=view,
                ),
                patch.object(consistency, "read", side_effect=guarded_read),
            ):
                envelope = check_context_registry(
                    failures,
                    warnings,
                    authority_mode="repository-validation",
                )

            self.assertEqual(failures, [])
            self.assertEqual(warnings, [])
            self.assertEqual(visited, current_markdown)
            self.assertTrue(predecessor_paths.isdisjoint(visited))
            self.assertEqual(
                envelope["validation_mode"],
                "adopted_configuration_validation",
            )
            self.assertFalse(envelope["predecessor_route_consulted"])

    def test_context_registry_missing_production_receipt_is_fatal(self):
        authority = SimpleNamespace(mode="production_transaction")
        failures: list[str] = []
        warnings: list[str] = []
        with (
            patch.object(
                consistency,
                "_production_context_registry_path_authority",
                return_value=authority,
            ),
            patch.object(
                consistency,
                "load_validated_component_registry_routing_view",
                side_effect=consistency.ComponentRegistryError(
                    "active Component Registry activation receipt is unavailable"
                ),
            ),
            patch.object(
                consistency,
                "load_component_registry_configuration_routing_view",
            ) as configuration_loader,
        ):
            envelope = check_context_registry(
                failures,
                warnings,
                authority_mode="production-transaction",
            )

        configuration_loader.assert_not_called()
        self.assertIsNone(envelope)
        self.assertEqual(len(failures), 1)
        self.assertIn("activation receipt is unavailable", failures[0])
        self.assertEqual(warnings, [])
        self.assertEqual(
            consistency.project_integrity_exit_code(
                failures,
                exit_zero_on_findings=True,
                context_routing_authority=envelope,
            ),
            2,
        )
        unavailable = (
            consistency.unavailable_context_registry_authority_envelope(
                "production-transaction"
            )
        )
        self.assertEqual(
            set(unavailable),
            self.CONTEXT_ROUTING_AUTHORITY_FIELDS,
        )
        self.assertEqual(
            unavailable,
            {
                "authority_mode": "production-transaction",
                "validation_mode": "unavailable",
                "registry_revision": None,
                "registry_sha256": None,
                "configuration_valid": False,
                "authoritative": False,
                "executable": False,
                "authority_effective": False,
                "source_revision_authorized": False,
                "source_bytes_current": False,
                "canonical_history_confirmed": False,
                "receipt_trusted": False,
                "runtime_live": "not_checked",
                "predecessor_route_consulted": False,
                "activation_receipt_consulted": False,
            },
        )

    def test_context_registry_rejects_cross_mode_authority_posture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            route = self.context_registry_fixture(root)
            invalid = self.context_registry_view(
                route,
                mode="adopted_configuration_validation",
            )
            invalid["predecessor_route_consulted"] = True
            failures: list[str] = []
            warnings: list[str] = []
            with (
                patch.object(consistency, "ROOT", root),
                patch.object(
                    consistency,
                    "load_component_registry_configuration_routing_view",
                    return_value=invalid,
                ),
            ):
                envelope = check_context_registry(
                    failures,
                    warnings,
                    authority_mode="repository-validation",
                )

            self.assertIsNone(envelope)
            self.assertEqual(len(failures), 1)
            self.assertIn("invalid routing authority posture", failures[0])
            self.assertEqual(warnings, [])

    def test_context_registry_rejects_incoherent_online_eligibility_facets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            route = self.context_registry_fixture(root)
            authority = SimpleNamespace(mode="production_transaction")
            invalid_values = {
                "authority_effective": False,
                "source_revision_authorized": False,
                "source_bytes_current": False,
                "canonical_history_confirmed": False,
                "receipt_trusted": False,
                "runtime_live": "running",
            }
            for field, invalid_value in invalid_values.items():
                with self.subTest(field=field):
                    invalid = self.context_registry_view(
                        route,
                        mode="live_authority_validation",
                    )
                    invalid[field] = invalid_value
                    failures: list[str] = []
                    warnings: list[str] = []
                    with (
                        patch.object(consistency, "ROOT", root),
                        patch.object(
                            consistency,
                            "_production_context_registry_path_authority",
                            return_value=authority,
                        ),
                        patch.object(
                            consistency,
                            "load_validated_component_registry_routing_view",
                            return_value=invalid,
                        ),
                    ):
                        envelope = check_context_registry(
                            failures,
                            warnings,
                            authority_mode="production-transaction",
                        )

                    self.assertIsNone(envelope)
                    self.assertEqual(len(failures), 1)
                    self.assertIn(
                        "invalid routing authority posture",
                        failures[0],
                    )
                    self.assertEqual(warnings, [])

    def test_context_registry_rejects_authority_mode_validation_mode_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            route = self.context_registry_fixture(root)
            invalid = self.context_registry_view(
                route,
                mode="live_authority_validation",
            )
            failures: list[str] = []
            warnings: list[str] = []
            with (
                patch.object(consistency, "ROOT", root),
                patch.object(
                    consistency,
                    "load_component_registry_configuration_routing_view",
                    return_value=invalid,
                ),
            ):
                envelope = check_context_registry(
                    failures,
                    warnings,
                    authority_mode="repository-validation",
                )

            self.assertIsNone(envelope)
            self.assertEqual(len(failures), 1)
            self.assertIn(
                "authority mode and validation mode differ",
                failures[0],
            )
            self.assertEqual(warnings, [])

    def test_task_handoff_handoff_state_is_coherent(self):
        task_handoff = (ROOT / "framework/handoffs/current-task.md").read_text(
            encoding="utf-8"
        )
        current_table = task_handoff.split("## Current Task", 1)[1].split(
            "## Handoff Rules", 1
        )[0]
        rows: dict[str, str] = {}
        for line in current_table.splitlines():
            if not line.startswith("| ") or line.startswith("| ---"):
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) == 2 and cells[0] != "Field":
                rows[cells[0]] = cells[1]

        state = rows["Handoff state"]
        self.assertIn(state, {"Open", "Paused", "Blocked", "Inactive"})
        if state == "Inactive":
            for field in (
                "Active issue/task",
                "Audit type/tier",
                "Started",
                "User request",
                "Scope",
                "Files touched",
                "Completed steps",
                "Next step",
                "Blockers/questions",
            ):
                self.assertEqual(rows[field], "None.", field)
            self.assertEqual(rows["Validation status"], "Not applicable.")
        else:
            for field in (
                "Active issue/task",
                "Audit type/tier",
                "Started",
                "User request",
                "Scope",
                "Next step",
            ):
                self.assertNotIn(rows[field], {"", "None."}, field)
            self.assertNotEqual(rows["Validation status"], "Not applicable.")
            if state in {"Paused", "Blocked"}:
                self.assertNotIn(
                    rows["Blockers/questions"],
                    {"", "None."},
                    "Paused and Blocked handoffs require resumption or blocker details",
                )
        self.assertRegex(
            rows["Last checkpoint"],
            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4}$",
        )

    def test_task_handoff_rules_separate_handoff_from_runtime_liveness(self):
        task_handoff = (ROOT / "framework/handoffs/current-task.md").read_text(
            encoding="utf-8"
        )
        agent_rules = (ROOT / "framework/AGENT_OPERATING_RULES.md").read_text(
            encoding="utf-8"
        )
        handoff_rules = (
            ROOT / "framework/standards/automation/task-handoffs.md"
        ).read_text(encoding="utf-8")
        agent_policy = (
            ROOT / "framework/project/automation/agent-policy.md"
        ).read_text(encoding="utf-8")
        project_autonomous = (
            ROOT / "framework/project/automation/autonomous-execution.md"
        ).read_text(encoding="utf-8")
        normalized_handoff = " ".join(handoff_rules.split())
        normalized_policy = " ".join(agent_policy.split())
        elim = (ROOT / "framework/project/automation/runbooks/elim.md").read_text(encoding="utf-8")
        coordinator = (ROOT / "framework/project/automation/runbooks/run-coordinator-bot.md").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "| Handoff state | Open / Paused / Blocked / Inactive |",
            task_handoff,
        )
        self.assertNotIn("| Status | Active / Paused / Blocked / Inactive |", task_handoff)
        self.assertIn("records continuation state only", task_handoff)
        self.assertIn("It is not evidence that an agent", task_handoff)
        self.assertIn("This file is not a completion ledger.", task_handoff)
        self.assertIn("## Context Handoff", agent_rules)
        self.assertIn(
            "[`task-handoffs.md`](standards/automation/task-handoffs.md#context-handoff)",
            agent_rules,
        )
        self.assertIn("Successful closeout requires", normalized_handoff)
        self.assertIn(
            "A continuation state never establishes runtime liveness",
            normalized_handoff,
        )
        self.assertIn(
            "If a required commit, push, review or merge, synchronization, "
            "publication, validation, or human-reserved decision remains part "
            "of the same task, retain `Paused` or `Blocked`",
            normalized_policy,
        )
        self.assertIn("#### Dispatcher liveness authority", project_autonomous)
        self.assertIn(
            "one operating-system-held local dispatcher lease separately "
            "serializes host dispatch and Elim execution",
            project_autonomous,
        )
        self.assertIn("continuation state, not proof", elim)
        self.assertIn("identifies unfinished continuation state only", coordinator)
        self.assertIn("A successfully completed task requires an `Inactive` handoff", coordinator)

    def test_persistent_agent_runbooks_match_runtime_configuration(self):
        failures: list[str] = []
        warnings: list[str] = []

        check_agent_runbooks(failures, warnings)

        self.assertEqual(failures, [])
        self.assertEqual(warnings, [])

    def test_runbook_runtime_drift_reports_material_invariants_and_owner(self):
        values = {
            "runtime_id": ".github/workflows/source-checker-bot.yml",
            "execution_environment": "github-actions",
            "trigger": "run-chain-or-manual",
            "schedule": "Due every 168 hours in the Run Coordinator chain; no independent schedule",
            "status": "report-only-pilot",
            "current_report": "framework/status/source-checker-report.md",
            "current_data": "project-console-data:source-checker.json",
            "offline_cache_path": ".tmp/project-console-source-checker.json",
        }
        config = {
            "agentId": "source-checker-bot",
            "mode": "report-only",
            "schedule": {
                "mode": "run-chain",
                "coordinator": ".github/workflows/run-coordinator-bot.yml",
                "dueEveryHours": 168,
            },
            "currentReport": "framework/status/source-checker-report.md",
            "currentData": "project-console-data:source-checker.json",
            "offlineCachePath": ".tmp/project-console-source-checker.json",
        }
        coordinator = {
            "stages": [
                {
                    "id": "source-checker-bot",
                    "workflow": ".github/workflows/source-checker-bot.yml",
                    "due": {"kind": "interval", "hours": 168},
                }
            ]
        }
        workflow = "on:\n  workflow_dispatch:\n  workflow_call:\n"
        self.assertEqual(
            consistency.agent_runtime_invariant_findings(
                "source-checker-bot",
                values,
                workflow_text=workflow,
                config=config,
                coordinator=coordinator,
            ),
            [],
        )

        drifted_values = {
            **values,
            "execution_environment": "local-shell",
            "current_data": "framework/status/source-checker.json",
            "offline_cache_path": ".tmp/wrong.json",
        }
        drifted_config = {
            **config,
            "schedule": {**config["schedule"], "dueEveryHours": 24},
        }
        findings = consistency.agent_runtime_invariant_findings(
            "source-checker-bot",
            drifted_values,
            workflow_text=workflow,
            config=drifted_config,
            coordinator=coordinator,
        )
        self.assertGreaterEqual(len(findings), 4)
        self.assertTrue(all("owner: source-checker-bot" in item for item in findings))
        self.assertTrue(any("execution_environment" in item for item in findings))
        self.assertTrue(any("current_data" in item for item in findings))
        self.assertTrue(any("offline_cache_path" in item for item in findings))
        self.assertTrue(any("due interval" in item for item in findings))

    def test_pages_in_flight_during_current_publish_grace_is_not_an_error(self):
        failures: list[str] = []
        warnings: list[str] = []
        current_sha = "a" * 40
        committed_at = int(consistency.datetime.now(consistency.timezone.utc).timestamp()) - 60

        with (
            patch.object(
                consistency,
                "run_gh_json",
                side_effect=[
                    ([{"id": 123, "sha": current_sha}], ""),
                    ([{"state": "in_progress"}], ""),
                ],
            ),
            patch.object(consistency, "git_revision", return_value=current_sha),
            patch.object(
                consistency.subprocess,
                "run",
                return_value=SimpleNamespace(stdout=str(committed_at)),
            ),
        ):
            check_github_pages_deployment(failures, warnings)

        self.assertEqual(failures, [])
        self.assertEqual(warnings, [])

    def test_project_sync_uses_exact_node_reader_without_duplicating_items(self):
        failures: list[str] = []
        warnings: list[str] = []
        project = {
            "items": [
                {
                    "id": "PVTI_fixture",
                    "fieldValues": {
                        "nodes": [
                            {
                                "name": "Development",
                                "field": {"name": "Status"},
                            }
                        ]
                    },
                    "content": {
                        "__typename": "Issue",
                        "number": 42,
                        "title": "HOR-042: Fixture",
                        "url": "https://github.com/Thorncrag/ARRP/issues/42",
                    },
                }
            ]
        }
        with (
            patch.dict(consistency.os.environ, {"ARRP_PROJECT_TOKEN": "fixture-token"}),
            patch.object(consistency, "fetch_project", return_value=project) as fetch,
        ):
            items = consistency.fetch_github_project_items(failures, warnings)

        fetch.assert_called_once()
        self.assertEqual(failures, [])
        self.assertEqual(warnings, [])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["status"], "Development")

    def test_pages_terminal_failure_is_an_error_during_publish_grace(self):
        failures: list[str] = []
        warnings: list[str] = []
        current_sha = "b" * 40
        committed_at = int(consistency.datetime.now(consistency.timezone.utc).timestamp()) - 60

        with (
            patch.object(
                consistency,
                "run_gh_json",
                side_effect=[
                    ([{"id": 124, "sha": current_sha}], ""),
                    ([{"state": "failure"}], ""),
                ],
            ),
            patch.object(consistency, "git_revision", return_value=current_sha),
            patch.object(
                consistency.subprocess,
                "run",
                return_value=SimpleNamespace(stdout=str(committed_at)),
            ),
        ):
            check_github_pages_deployment(failures, warnings)

        self.assertEqual(
            failures,
            ["ERROR: latest GitHub Pages deployment is not successful: failure"],
        )
        self.assertEqual(warnings, [])

    def test_pages_in_flight_beyond_publish_grace_is_an_error(self):
        failures: list[str] = []
        warnings: list[str] = []
        current_sha = "c" * 40
        committed_at = int(consistency.datetime.now(consistency.timezone.utc).timestamp()) - 1801

        with (
            patch.object(
                consistency,
                "run_gh_json",
                side_effect=[
                    ([{"id": 125, "sha": current_sha}], ""),
                    ([{"state": "queued"}], ""),
                ],
            ),
            patch.object(consistency, "git_revision", return_value=current_sha),
            patch.object(
                consistency.subprocess,
                "run",
                return_value=SimpleNamespace(stdout=str(committed_at)),
            ),
        ):
            check_github_pages_deployment(failures, warnings)

        self.assertEqual(
            failures,
            ["ERROR: latest GitHub Pages deployment is not successful: queued"],
        )
        self.assertEqual(warnings, [])

    def test_local_link_queries_do_not_change_filesystem_target(self):
        source = (
            ROOT
            / "framework"
            / "project"
            / "interfaces"
            / "project-console"
            / "project-console.html"
        )
        self.assertEqual(
            local_target(source, "app.js?v=20"),
            (source.parent / "app.js").resolve(),
        )

    def test_markdown_anchor_inventory_supports_generated_and_explicit_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.md"
            path.write_text(
                "# Main Title\n\n## Budgetary Impact Statement\n\n"
                "## Repeated\n\n## Repeated\n\n<h2 id=\"manual-anchor\">Manual</h2>\n",
                encoding="utf-8",
            )

            anchors = markdown_anchor_ids(path)

        self.assertIn("main-title", anchors)
        self.assertIn("budgetary-impact-statement", anchors)
        self.assertIn("repeated", anchors)
        self.assertIn("repeated-1", anchors)
        self.assertIn("manual-anchor", anchors)

    def test_project_maturity_and_workflow_are_inferred_independently(self):
        self.assertEqual(
            expected_project_development_level({"status": "developed", "audit_score": "77"}),
            {
                "release candidate",
                "review ready",
            },
        )
        self.assertEqual(
            expected_project_development_level({"status": "developed", "audit_score": "63"}),
            {"developed proposal"},
        )
        self.assertEqual(
            expected_project_development_level({"status": "candidate", "audit_score": "0"}),
            set(),
        )
        self.assertEqual(
            expected_project_workflow_status({"status": "deferred", "audit_score": "0"}),
            {"deferred"},
        )
        self.assertEqual(
            expected_project_workflow_status({"status": "awaiting-decision", "audit_score": "0"}),
            {"human decision needed"},
        )
        self.assertEqual(
            expected_project_workflow_status({"status": "in-development", "audit_score": "0"}),
            set(),
        )
        self.assertEqual(
            expected_project_workflow_status({"status": "blocked", "audit_score": "0"}),
            {"blocked"},
        )

    def test_deferred_workflow_requires_machine_readable_hold_reason(self):
        self.assertTrue(requires_workflow_hold_reason({"status": "deferred"}))
        self.assertTrue(requires_workflow_hold_reason({"status": "awaiting-merits-adjudication"}))
        self.assertFalse(requires_workflow_hold_reason({"status": "developed"}))

    def test_console_safe_integrity_summary_never_repeats_diagnostic_prose(self):
        finding = {
            "severity": "ERROR",
            "message": "ARRP_STATE_ROOT=/Users/owner/private GH_TOKEN=credential_value",
        }
        summary = consistency.console_safe_finding_summary(finding)
        self.assertEqual(summary, "A typed integrity error requires review.")
        self.assertNotIn("ARRP_STATE_ROOT", summary)
        self.assertNotIn("credential_value", summary)

    def test_project_status_vocabulary_is_exact_and_excludes_superseded_values(self):
        self.assertEqual(
            PROJECT_WORKFLOW_STATUSES,
            {
                "research",
                "development",
                "human decision needed",
                "audit needed",
                "audit in progress",
                "external review",
                "publication approval",
                "deferred",
                "blocked",
            },
        )
        for status in PROJECT_WORKFLOW_STATUSES:
            with self.subTest(status=status):
                self.assertTrue(is_recognized_project_status(status))
        for superseded in (
            "Awaiting decision",
            "Pending development",
            "In development",
            "Monitoring",
            "External review needed",
            "Publication review needed",
            "Deferred / Parked",
            "Completed within scope",
        ):
            with self.subTest(superseded=superseded):
                self.assertFalse(is_recognized_project_status(superseded))

    def test_issue_page_status_vocabulary_remains_distinct_from_project_status(self):
        self.assertEqual(
            ISSUE_PAGE_STATUSES,
            {
                "awaiting-decision",
                "awaiting-merits-adjudication",
                "blocked",
                "candidate",
                "deferred",
                "developed",
                "in-development",
                "retired",
            },
        )
        for status in ISSUE_PAGE_STATUSES:
            with self.subTest(status=status):
                self.assertTrue(is_recognized_issue_page_status(status))
        for project_status in (
            "research",
            "development",
            "human decision needed",
            "audit needed",
            "audit in progress",
            "external review",
            "publication approval",
        ):
            with self.subTest(project_status=project_status):
                self.assertFalse(is_recognized_issue_page_status(project_status))

    def test_research_status_requires_a_defined_next_investigation(self):
        missing = lifecycle_findings(
            kind="horizon",
            status="Research",
            **{"development level": "Candidate", "next audit": ""},
        )
        self.assertTrue(
            any(
                severity == "WARNING"
                and "Status 'Research' but lacks a concrete Next audit" in message
                for severity, message in missing
            ),
            missing,
        )

        defined = lifecycle_findings(
            kind="horizon",
            status="Research",
            **{
                "development level": "Candidate",
                "next audit": "Cross-administration docket study of review-evasion signals",
            },
        )
        self.assertFalse(
            any("Status 'Research'" in message for _, message in defined),
            defined,
        )

    def test_issue_page_status_check_flags_blank_and_nonstandard_values(self):
        relative = Path("areas/TEST/issues/TEST-001.md")
        self.assertIn(
            "lacks required nonblank issue-page status metadata",
            issue_page_status_error(relative, {}),
        )
        self.assertIn(
            "lacks required nonblank issue-page status metadata",
            issue_page_status_error(relative, {"status": "   "}),
        )
        self.assertIn(
            "distinct from GitHub Project Status",
            issue_page_status_error(relative, {"status": "development"}),
        )
        self.assertEqual(
            issue_page_status_error(relative, {"status": "in-development"}),
            "",
        )

    def test_issue_page_status_is_checked_even_when_issue_id_is_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            issue_path = root / "areas" / "TEST" / "issues" / "TEST-001.md"
            issue_path.parent.mkdir(parents=True)
            issue_path.write_text(
                "---\n"
                'title: "Missing identifiers and status"\n'
                "---\n\n"
                "# TEST-001 — Missing identifiers and status\n",
                encoding="utf-8",
            )
            failures: list[str] = []
            warnings: list[str] = []
            with (
                patch.object(consistency, "ROOT", root),
                patch.object(consistency, "ISSUE_PATH", root / "areas"),
            ):
                check_issue_pages(failures, warnings)

        self.assertTrue(
            any("lacks required nonblank issue-page status metadata" in value for value in failures),
            failures,
        )
        self.assertTrue(
            any("lacks a valid issue_id" in value for value in failures),
            failures,
        )

    def test_issue_snapshot_word_counts_use_reader_visible_text(self):
        body = (
            "# TEST-001 — Snapshot test\n\n"
            "> ## Issue Snapshot\n"
            "> **Problem:** Executive orders can bypass Congress.<br />"
            "**Repair:** Require congressional authorization and timely judicial review.<br />"
            "**Vehicle:** [Institutional Safeguards Act](../../../legislation/TEST-001.md).\n"
            ">\n\n"
            "## Institutional Anomaly\n"
        )

        self.assertEqual(
            issue_snapshot_fields(body),
            {
                "Problem": "Executive orders can bypass Congress.",
                "Repair": "Require congressional authorization and timely judicial review.",
                "Vehicle": "[Institutional Safeguards Act](../../../legislation/TEST-001.md).",
            },
        )
        self.assertEqual(
            issue_snapshot_word_counts(body),
            {
                "Problem": 5,
                "Repair": 7,
                "Vehicle": 3,
            },
        )
        self.assertEqual(
            visible_markdown_word_count(
                "[Interbranch Review Framework Act (JUD-011)]"
                "(../../../legislation/JUD-011.md) alone"
            ),
            6,
        )
        self.assertEqual(ISSUE_SNAPSHOT_WORD_GUIDELINE, 12)

    def test_issue_snapshot_parser_exposes_missing_and_long_fields(self):
        body = (
            "> ## Issue Snapshot\n"
            "> **Problem:** One two three four five six seven eight nine ten eleven twelve "
            "thirteen.<br />**Repair:** Short repair.\n"
            ">\n"
        )

        self.assertEqual(
            issue_snapshot_word_counts(body),
            {
                "Problem": 13,
                "Repair": 2,
            },
        )

    def test_lifecycle_kind_workstream_area_and_development_applicability(self):
        cases = (
            (
                "proposal wrong workstream",
                lifecycle_findings(workstream="Project governance and operations"),
                "proposal items require 'proposal development'",
            ),
            (
                "horizon wrong level",
                lifecycle_findings(
                    kind="horizon",
                    object_id="HOR-999",
                    **{
                        "development level": "Admitted / undeveloped",
                        "workstream": "Proposal development",
                    },
                ),
                "expected 'Candidate'",
            ),
            (
                "governance missing area",
                lifecycle_findings(
                    kind="governance",
                    object_id="#999",
                    status="Development",
                    **{
                        "development level": "",
                        "workstream": "Project governance and operations",
                        "area": "",
                        "score": None,
                    },
                ),
                "lacks an Area",
            ),
            (
                "source review has maturity",
                lifecycle_findings(
                    kind="source review",
                    object_id="#998",
                    status="Development",
                    **{
                        "development level": "In development",
                        "workstream": "Project governance and operations",
                        "area": "Source development",
                        "score": None,
                    },
                ),
                "nonproposal items must leave it blank",
            ),
        )
        for name, findings, message in cases:
            with self.subTest(name=name):
                self.assertTrue(
                    any(severity == "ERROR" and message in text for severity, text in findings),
                    findings,
                )

    def test_maturity_score_and_foundation_coherence(self):
        cases = (
            (
                "scored below developed",
                lifecycle_findings(score=12),
                "ERROR",
                "below Developed proposal",
            ),
            (
                "developed score belongs in review ready",
                lifecycle_findings(
                    status="Audit needed",
                    **{
                        "development level": "Developed proposal",
                        "score": 75,
                        "next audit": "T2 audit",
                    },
                ),
                "ERROR",
                "remains below Review ready",
            ),
            (
                "review ready score below threshold",
                lifecycle_findings(
                    status="External review",
                    **{
                        "development level": "Review ready",
                        "score": 74,
                        "next audit": "External expert review",
                    },
                ),
                "ERROR",
                "below 75",
            ),
            (
                "explicit pending foundation contradicts development",
                lifecycle_findings(
                    metadata={"foundation_status": "pending"},
                    **{"development level": "In development"},
                ),
                "ERROR",
                "recorded foundation is pending",
            ),
            (
                "missing foundation is reconcilable",
                lifecycle_findings(**{"development level": "In development"}),
                "WARNING",
                "Elim must reconcile",
            ),
            (
                "approved foundation has stale maturity",
                lifecycle_findings(metadata={"foundation_status": "approved"}),
                "WARNING",
                "stale Development level",
            ),
        )
        for name, findings, severity, message in cases:
            with self.subTest(name=name):
                self.assertTrue(
                    any(level == severity and message in text for level, text in findings),
                    findings,
                )

    def test_issue_admission_next_audit_is_stale_only_after_admission(self):
        proposal_findings = lifecycle_findings(**{"next audit": "Issue-admission test"})
        self.assertTrue(
            any(
                severity == "WARNING" and "stale Issue-admission" in message
                for severity, message in proposal_findings
            ),
            proposal_findings,
        )

        horizon_findings = lifecycle_findings(
            kind="horizon",
            object_id="HOR-999",
            **{
                "development level": "Candidate",
                "next audit": "Issue-admission test",
            },
        )
        self.assertFalse(
            any("stale Issue-admission" in message for _, message in horizon_findings),
            horizon_findings,
        )

    def test_audit_and_review_status_require_maturity_and_concrete_next_action(self):
        invalid_audit = lifecycle_findings(
            status="Audit needed",
            **{"next audit": "Not recorded"},
        )
        self.assertTrue(
            any(
                severity == "ERROR" and "before reaching Developed proposal" in message
                for severity, message in invalid_audit
            ),
            invalid_audit,
        )
        self.assertTrue(
            any(
                severity == "WARNING" and "lacks a concrete Next audit" in message
                for severity, message in invalid_audit
            ),
            invalid_audit,
        )

        valid_external_review = lifecycle_findings(
            status="External review",
            **{
                "development level": "Review ready",
                "score": 82,
                "next audit": "Qualified constitutional-law review of enforcement scope and severability",
            },
        )
        self.assertEqual(valid_external_review, [])

        generic_external_review = lifecycle_findings(
            status="External review",
            **{
                "development level": "Review ready",
                "score": 82,
                "next audit": "T4 follow-up or external-validation pass",
            },
        )
        self.assertTrue(
            any(
                severity == "WARNING"
                and "reviewer type" in message
                and "review scope" in message
                for severity, message in generic_external_review
            ),
            generic_external_review,
        )
        self.assertEqual(
            external_review_action_missing_components(
                "Qualified constitutional-law review focused on enforcement scope and severability"
            ),
            (),
        )
        self.assertEqual(
            external_review_action_missing_components("Qualified external review / T4 follow-up"),
            ("reviewer type", "review scope"),
        )

        invalid_publication = lifecycle_findings(
            status="Publication approval",
            **{
                "development level": "Review ready",
                "score": 82,
                "next audit": "Publication approval",
            },
        )
        self.assertTrue(
            any(
                severity == "ERROR" and "Release candidate" in message
                for severity, message in invalid_publication
            ),
            invalid_publication,
        )

        below_release_floor = lifecycle_findings(
            status="Publication approval",
            **{
                "development level": "Release candidate",
                "score": 74,
                "next audit": "Publication approval",
            },
        )
        self.assertTrue(
            any(
                severity == "ERROR" and "below 75" in message
                for severity, message in below_release_floor
            ),
            below_release_floor,
        )

        valid_publication = lifecycle_findings(
            status="Publication approval",
            **{
                "development level": "Release candidate",
                "score": 90,
                "next audit": "Publication approval",
            },
        )
        self.assertEqual(valid_publication, [])

    def test_deferred_blocked_and_human_decision_require_explanations(self):
        for status in ("Deferred", "Blocked", "Human decision needed"):
            with self.subTest(status=status):
                findings = lifecycle_findings(status=status)
                self.assertTrue(
                    any(
                        severity == "WARNING" and "lacks an explanation or reason" in message
                        for severity, message in findings
                    ),
                    findings,
                )

        self.assertTrue(
            project_status_reason_is_present(
                "Deferred",
                {
                    "workflow_hold_reason": (
                        "Development is postponed because election-method evidence remains "
                        "insufficient. Reconsider after certified post-election data is available."
                    )
                },
                "",
            )
        )
        self.assertFalse(
            project_status_reason_is_present(
                "Deferred",
                {"workflow_hold_reason": "Expert input would be useful."},
                "",
            )
        )
        self.assertTrue(
            project_status_reason_is_present(
                "Blocked",
                {
                    "workflow_hold_reason": (
                        "Remedy selection is blocked because the sealed warrant is an "
                        "indispensable prerequisite. Resume when the warrant is unsealed."
                    )
                },
                "",
            )
        )
        self.assertEqual(
            project_status_reason_missing_components(
                "Blocked",
                {},
                "## Blocker\n\nThe indispensable warrant remains sealed and unavailable.",
            ),
            ("blocked action", "unblock trigger"),
        )
        self.assertEqual(
            project_status_reason_missing_components(
                "Deferred",
                {"workflow_hold_reason": "The issue is unusually nuanced."},
                "",
            ),
            ("reconsideration condition or date",),
        )
        self.assertTrue(
            project_status_reason_is_present(
                "Deferred",
                {},
                (
                    "## Current disposition\n\n"
                    "Deferred pending a later event.\n\n"
                    "## Why this is deferred\n\n"
                    "ARRP is postponing development because the incomplete record makes "
                    "remedy selection premature.\n\n"
                    "## Reconsideration conditions\n\n"
                    "Reconsider when the responsible agency publishes its final findings."
                ),
            )
        )
        self.assertTrue(
            project_status_reason_is_present(
                "Blocked",
                {},
                (
                    "## Why this is blocked\n\n"
                    "Remedy selection cannot proceed because the sealed order is an "
                    "indispensable prerequisite.\n\n"
                    "## Unblock trigger\n\n"
                    "Resume when the order is unsealed and available for review."
                ),
            )
        )
        self.assertTrue(
            project_status_reason_is_present(
                "Human decision needed",
                {},
                "## Decision needed\n\nChoose whether the proposed remedy should be statutory.",
            )
        )

        incomplete_block = lifecycle_findings(
            status="Blocked",
            metadata={"workflow_hold_reason": "The indispensable record is unavailable."},
        )
        self.assertTrue(
            any(
                severity == "WARNING"
                and "blocked action" in message
                and "unblock trigger" in message
                for severity, message in incomplete_block
            ),
            incomplete_block,
        )

    def test_integrity_finding_identity_does_not_depend_on_wording(self):
        failures: list[str] = []
        warnings: list[str] = []
        prior_definitions = dict(consistency.INTEGRITY_CHECK_DEFINITIONS)
        consistency.STRUCTURED_FINDINGS.clear()

        def registered_wording_check(message: str) -> None:
            path = ROOT / "framework" / "FRAMEWORK.md"
            report("WARNING", message, failures, warnings)

        try:
            consistency.INTEGRITY_CHECK_DEFINITIONS[
                "registered_wording_check"
            ] = "Test check"
            registered_wording_check("First presentation wording")
            first_ids = set(consistency.STRUCTURED_FINDINGS)
            consistency.STRUCTURED_FINDINGS.clear()
            registered_wording_check("Completely different presentation wording")
            self.assertEqual(set(consistency.STRUCTURED_FINDINGS), first_ids)
        finally:
            consistency.INTEGRITY_CHECK_DEFINITIONS.clear()
            consistency.INTEGRITY_CHECK_DEFINITIONS.update(prior_definitions)
            consistency.STRUCTURED_FINDINGS.clear()

    def test_authenticated_readback_gaps_emit_distinct_typed_findings(self):
        cases: list[tuple[str, str, str]] = []

        consistency.STRUCTURED_FINDINGS.clear()
        with patch.object(
            consistency,
            "run_gh_json",
            return_value=(None, "provider diagnostic must remain private"),
        ):
            consistency.fetch_github_issues([], [])
        issue_finding = next(iter(consistency.STRUCTURED_FINDINGS.values()))
        cases.append(
            (
                str(issue_finding["finding_code"]),
                str(issue_finding["console_safe_summary"])
                if "console_safe_summary" in issue_finding
                else consistency.console_safe_finding_summary(issue_finding),
                "GitHub Issues synchronization could not be verified.",
            )
        )

        consistency.STRUCTURED_FINDINGS.clear()
        with patch.dict(
            consistency.os.environ,
            {"ARRP_PROJECT_TOKEN": ""},
        ):
            consistency.fetch_github_project_items([], [])
        project_access_finding = next(
            iter(consistency.STRUCTURED_FINDINGS.values())
        )
        cases.append(
            (
                str(project_access_finding["finding_code"]),
                consistency.console_safe_finding_summary(
                    project_access_finding
                ),
                (
                    "GitHub Project synchronization could not be verified "
                    "because the registered read-only access was unavailable."
                ),
            )
        )

        consistency.STRUCTURED_FINDINGS.clear()
        with (
            patch.dict(
                consistency.os.environ,
                {"ARRP_PROJECT_TOKEN": "fixture-token"},
            ),
            patch.object(
                consistency,
                "fetch_project",
                side_effect=RuntimeError("private provider diagnostic"),
            ),
        ):
            consistency.fetch_github_project_items([], [])
        project_readback_finding = next(
            iter(consistency.STRUCTURED_FINDINGS.values())
        )
        cases.append(
            (
                str(project_readback_finding["finding_code"]),
                consistency.console_safe_finding_summary(
                    project_readback_finding
                ),
                (
                    "GitHub Project synchronization could not be verified "
                    "because the registered readback did not complete."
                ),
            )
        )

        consistency.STRUCTURED_FINDINGS.clear()
        with patch.object(
            consistency,
            "run_gh_json",
            return_value=(None, "provider diagnostic must remain private"),
        ):
            check_github_pages_deployment([], [])
        pages_finding = next(iter(consistency.STRUCTURED_FINDINGS.values()))
        cases.append(
            (
                str(pages_finding["finding_code"]),
                consistency.console_safe_finding_summary(pages_finding),
                "GitHub Pages deployment synchronization could not be verified.",
            )
        )

        self.assertEqual(
            [code for code, _, _ in cases],
            [
                "github_issues_readback_unavailable",
                "github_project_access_unavailable",
                "github_project_readback_unavailable",
                "github_pages_readback_unavailable",
            ],
        )
        for code, summary, expected_summary in cases:
            with self.subTest(condition_code=code):
                self.assertEqual(summary, expected_summary)
                self.assertNotIn("provider diagnostic", summary)
        for finding in (
            issue_finding,
            project_access_finding,
            project_readback_finding,
            pages_finding,
        ):
            self.assertEqual(finding["owner"], "Elim")
            self.assertEqual(finding["route"], "integrity")
            self.assertTrue(str(finding["finding_id"]).startswith("INT-"))
        registry = consistency.json.loads(
            (
                ROOT
                / "framework/project/interfaces/project-console/configuration/classifications.json"
            ).read_text(encoding="utf-8")
        )
        registered_findings = {
            entry["id"]: entry
            for entry in registry["namespaces"]["finding_code"]
        }
        for code, definition in (
            consistency.INTEGRITY_CONDITION_DEFINITIONS.items()
        ):
            with self.subTest(registered_condition=code):
                registered = registered_findings[code]
                self.assertEqual(registered, definition)
        consistency.STRUCTURED_FINDINGS.clear()

    def test_monitoring_wrapper_requires_all_four_governance_components(self):
        generic_wrapper = (
            "## Workflow Purpose\n\n"
            "This issue tracks the proposal.\n\n"
            "## Next Step\n\n"
            "Use the Project fields to identify the next task."
        )
        self.assertEqual(
            monitoring_wrapper_missing_components(generic_wrapper),
            (
                "watched matter",
                "material relevance",
                "reassessment trigger",
                "checking method",
            ),
        )

        structured_wrapper = (
            "## Monitoring\n\n"
            "- Watched matter: The pending court ruling on the statutory cause of action.\n"
            "- Material relevance: The ruling could alter the proposal's enforcement design.\n"
            "- Reassessment trigger: Reassess when the court issues its decision.\n"
            "- Checking method: Review the appellate docket monthly.\n"
        )
        self.assertEqual(
            monitoring_wrapper_missing_components(structured_wrapper),
            (),
        )

        bold_label_wrapper = (
            "## Monitoring\n\n"
            "**Watched matter:** The pending court ruling on the statutory cause of action.\n\n"
            "**Material relevance:** The ruling could alter the proposal's enforcement design.\n\n"
            "**Reassessment trigger:** Reassess when the court issues its decision.\n\n"
            "**Checking method:** Review the appellate docket monthly.\n"
        )
        self.assertEqual(
            monitoring_wrapper_missing_components(bold_label_wrapper),
            (),
        )

        incomplete_wrapper = (
            "## Monitoring\n\n"
            "- Watched matter: The pending court ruling.\n"
            "- Reassessment trigger: Reassess when the court issues its decision.\n"
        )
        self.assertEqual(
            monitoring_wrapper_missing_components(incomplete_wrapper),
            ("material relevance", "checking method"),
        )

    def test_integrity_markdown_report_is_a_stable_current_snapshot(self):
        report = markdown_report(
            {
                "generated_at": "2026-07-21T12:00:00+00:00",
                "revision": "abc123",
                "counts": {
                    "errors": 0,
                    "warnings": 0,
                    "issue_pages": 61,
                    "proposal_pages": 40,
                },
                "scope": ["Internal repository links"],
                "findings": [],
            }
        )

        self.assertIn("# Current Project Integrity Report", report)
        self.assertIn("**Result:** Clean", report)
        self.assertIn("No repeatable integrity findings", report)
        self.assertIn("Project Integrity Bot runbook", report)
        self.assertIn(
            "../project/automation/runbooks/project-integrity-bot.md#checks-included",
            report,
        )
        self.assertNotIn("../../project/automation/runbooks", report)
        self.assertNotIn("- Internal repository links", report)
        self.assertNotIn("2026-07-21T12:00:00", report)
        self.assertNotIn("abc123", report)

    def test_integrity_markdown_uses_only_console_safe_finding_text(self):
        diagnostic = (
            "ARRP_PROJECT_TOKEN failed at "
            "file:///Users/example/private/report.json"
        )
        report = markdown_report(
            {
                "counts": {
                    "errors": 0,
                    "warnings": 1,
                    "issue_pages": 64,
                    "proposal_pages": 41,
                },
                "findings": [
                    {
                        "category": "GitHub records",
                        "severity": "warning",
                        "message": diagnostic,
                        "console_safe_summary": (
                            "A typed integrity finding requires review."
                        ),
                    }
                ],
            }
        )

        self.assertIn(
            "A typed integrity finding requires review.",
            report,
        )
        self.assertNotIn("ARRP_PROJECT_TOKEN", report)
        self.assertNotIn("file:///", report)
        self.assertNotIn("/Users/", report)

    def test_extracts_main_branch_blob_target(self):
        body = (
            "[Horizon log](https://github.com/Thorncrag/ARRP/blob/main/"
            "framework/logs/candidates/candidate-discovery-log.md#horizon-integration-log)"
        )

        targets = github_repository_targets(body)

        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0][1], "framework/logs/candidates/candidate-discovery-log.md")

    def test_extracts_repository_target_from_json_escaped_html(self):
        body = (
            '{"html":"<a href=\\"https://github.com/Thorncrag/ARRP/blob/main/'
            'framework/logs/candidates/candidate-discovery-log.md\\" target=\\"_blank\\">log</a>"}'
        )

        targets = github_repository_targets(body)

        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0][1], "framework/logs/candidates/candidate-discovery-log.md")

    def test_ignores_non_main_branch_target(self):
        body = "https://github.com/Thorncrag/ARRP/blob/project-console-data/progress.json"

        self.assertEqual(github_repository_targets(body), [])

    def test_active_markdown_scope_includes_research_and_templates(self):
        relative_paths = {path.relative_to(ROOT).as_posix() for path in active_project_files(".md")}

        self.assertIn("research/README.md", relative_paths)
        self.assertTrue(
            any(
                path.startswith(
                    (
                        "framework/standards/content/templates/",
                        "framework/standards/sources/templates/",
                    )
                )
                for path in relative_paths
            )
        )
        self.assertFalse(any(path.startswith("archive/") for path in relative_paths))

    def test_active_project_scope_excludes_owner_only_console_projections(self):
        relative_paths = {
            path.relative_to(ROOT)
            for path in active_project_files(".js")
        }

        self.assertTrue(consistency.LOCAL_ONLY_CONSOLE_PROJECTIONS)
        self.assertTrue(
            consistency.LOCAL_ONLY_CONSOLE_PROJECTIONS.isdisjoint(
                relative_paths
            )
        )

    def test_research_scope_includes_central_and_area_records(self):
        relative_paths = {path.relative_to(ROOT).as_posix() for path in research_files(".md")}

        self.assertIn("research/portfolio-issue-consolidation-review.md", relative_paths)
        self.assertIn(
            "areas/JUD/research/JUD-012-judicial-review-foreclosure-case-review.md",
            relative_paths,
        )

    def test_generated_console_inventory_is_not_a_citation_source(self):
        corpus = source_citation_corpus()

        self.assertNotIn("window.ARRP_HORIZON_REVIEW_DATA=", corpus)

    def test_source_development_shells_are_internal_and_have_no_audit_sidecars(self):
        shells = {}
        for path in ROOT.glob("areas/*/issues/*.md"):
            if path.name.endswith(".audit.md"):
                continue
            text = path.read_text(encoding="utf-8")
            if "record_type: source-development" in text:
                shells[path.stem] = (path, text)

        self.assertEqual(set(shells), SOURCE_DEVELOPMENT_STUB_IDS)
        for issue_id, (path, text) in shells.items():
            self.assertIn("print_status: excluded", text, issue_id)
            self.assertIn('print_exclusion_reason: "Internal source-development record."', text, issue_id)
            self.assertNotIn("  - full-technical", text, issue_id)
            self.assertNotIn("  - public-proposal", text, issue_id)
            self.assertFalse(path.with_name(f"{issue_id}.audit.md").exists(), issue_id)
            self.assertIn("**Source-development record only.**", text, issue_id)

    def test_source_development_shells_are_registry_routes_but_not_public_pages(self):
        registry = ROOT / "inventory/github_issue_registry.csv"
        with registry.open(newline="", encoding="utf-8") as handle:
            rows = {row["Object ID"]: row for row in csv.DictReader(handle)}

        public_pages = {path.resolve() for path in discover_public_markdown()}
        for issue_id in SOURCE_DEVELOPMENT_STUB_IDS:
            row = rows[issue_id]
            area = issue_id.split("-", 1)[0]
            expected = ROOT / f"areas/{area}/issues/{issue_id}.md"
            self.assertEqual(row["Canonical Record"], expected.relative_to(ROOT).as_posix())
            self.assertTrue(expected.exists(), issue_id)
            self.assertNotIn(expected.resolve(), public_pages, issue_id)
            issue_text = expected.read_text(encoding="utf-8")
            registry_title = row["GitHub Title"].split(": ", 1)[1]
            self.assertIn(f'title: "{registry_title}"', issue_text, issue_id)
            area_index = (ROOT / f"areas/{area}/README.md").read_text(encoding="utf-8")
            self.assertIn(f"(issues/{issue_id}.md)", area_index, issue_id)


class Stage3MigrationAuthorityTests(unittest.TestCase):
    def test_applied_stage3_migrations_are_not_current_link_fallbacks(self):
        consistency.candidate_migration_aliases.cache_clear()
        with patch.object(
            consistency,
            "load_validated_registry",
            return_value=(
                {
                    "schema_version": 3,
                    "migrations_and_aliases": {
                        "entries": {
                            "historical": {
                                "source_path": "old/path.md",
                                "target_path": "new/path.md",
                            }
                        }
                    },
                },
                {},
            ),
        ):
            self.assertEqual(consistency.candidate_migration_aliases(), ())
        consistency.candidate_migration_aliases.cache_clear()


if __name__ == "__main__":
    unittest.main()
