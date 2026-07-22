import csv
import tempfile
import unittest
from pathlib import Path

from scripts.audit_project_consistency import (
    ROOT,
    active_project_files,
    check_agent_runbooks,
    expected_project_development_level,
    expected_project_workflow_status,
    finding_attention_owner,
    github_repository_targets,
    local_target,
    markdown_anchor_ids,
    markdown_report,
    research_files,
    requires_workflow_hold_reason,
    source_citation_corpus,
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
            {"deferred / parked"},
        )
        self.assertEqual(
            expected_project_workflow_status({"status": "awaiting-decision", "audit_score": "0"}),
            {"awaiting decision"},
        )

    def test_deferred_workflow_requires_machine_readable_hold_reason(self):
        self.assertTrue(requires_workflow_hold_reason({"status": "deferred"}))
        self.assertTrue(requires_workflow_hold_reason({"status": "awaiting-merits-adjudication"}))
        self.assertFalse(requires_workflow_hold_reason({"status": "developed"}))

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
