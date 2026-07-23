import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.audit_project_consistency as consistency
from scripts.audit_project_consistency import (
    ISSUE_PAGE_STATUSES,
    ISSUE_SNAPSHOT_WORD_GUIDELINE,
    PROJECT_WORKFLOW_STATUSES,
    ROOT,
    active_project_files,
    check_agent_runbooks,
    check_issue_pages,
    external_review_action_missing_components,
    expected_project_development_level,
    expected_project_workflow_status,
    finding_attention_owner,
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


class GitHubIssueLinkTests(unittest.TestCase):
    def test_persistent_agent_runbooks_match_runtime_configuration(self):
        failures: list[str] = []
        warnings: list[str] = []

        check_agent_runbooks(failures, warnings)

        self.assertEqual(failures, [])
        self.assertEqual(warnings, [])

    def test_local_link_queries_do_not_change_filesystem_target(self):
        source = ROOT / "research" / "horizon-review-console" / "index.html"
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

    def test_project_status_vocabulary_is_exact_and_excludes_superseded_values(self):
        self.assertEqual(
            PROJECT_WORKFLOW_STATUSES,
            {
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
            "development",
            "human decision needed",
            "audit needed",
            "audit in progress",
            "external review",
            "publication approval",
        ):
            with self.subTest(project_status=project_status):
                self.assertFalse(is_recognized_issue_page_status(project_status))

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
                missing_message = next(
                    message
                    for _, message in findings
                    if "lacks an explanation or reason" in message
                )
                self.assertEqual(finding_attention_owner(missing_message), "human")

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

    def test_integrity_findings_route_only_reserved_decisions_to_human_attention(self):
        self.assertEqual(
            finding_attention_owner("APPT-001 lacks a machine-readable foundation decision"),
            "agent",
        )
        self.assertEqual(
            finding_attention_owner("issue page X lacks nonblank workflow_hold_reason metadata"),
            "human",
        )
        self.assertEqual(
            finding_attention_owner("issue X lacks an explanation or reason for its hold"),
            "human",
        )
        self.assertEqual(
            finding_attention_owner("research record contains generic source-development propositions"),
            "agent",
        )
        self.assertEqual(
            finding_attention_owner(
                "Project Status for APPT-001 differs; repository metadata implies Human decision needed"
            ),
            "agent",
        )

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
        self.assertNotIn("- Internal repository links", report)
        self.assertNotIn("2026-07-21T12:00:00", report)
        self.assertNotIn("abc123", report)

    def test_extracts_main_branch_blob_target(self):
        body = (
            "[Horizon log](https://github.com/Thorncrag/ARRP/blob/main/"
            "framework/logs/HORIZON_SCAN_LOG.md#horizon-integration-log)"
        )

        targets = github_repository_targets(body)

        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0][1], "framework/logs/HORIZON_SCAN_LOG.md")

    def test_extracts_repository_target_from_json_escaped_html(self):
        body = (
            '{"html":"<a href=\\"https://github.com/Thorncrag/ARRP/blob/main/'
            'framework/logs/HORIZON_SCAN_LOG.md\\" target=\\"_blank\\">log</a>"}'
        )

        targets = github_repository_targets(body)

        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0][1], "framework/logs/HORIZON_SCAN_LOG.md")

    def test_ignores_non_main_branch_target(self):
        body = "https://github.com/Thorncrag/ARRP/blob/project-console-data/progress.json"

        self.assertEqual(github_repository_targets(body), [])

    def test_active_markdown_scope_includes_research_and_templates(self):
        relative_paths = {path.relative_to(ROOT).as_posix() for path in active_project_files(".md")}

        self.assertIn("research/README.md", relative_paths)
        self.assertTrue(any(path.startswith("framework/templates/") for path in relative_paths))
        self.assertFalse(any(path.startswith("archive/") for path in relative_paths))

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


if __name__ == "__main__":
    unittest.main()
