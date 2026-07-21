import csv
import unittest

from scripts.audit_project_consistency import (
    ROOT,
    active_project_files,
    github_repository_targets,
    research_files,
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
    "PRESS-006",
    "REC-001",
    "REG-006",
    "RET-001",
}


class GitHubIssueLinkTests(unittest.TestCase):
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
        body = "https://github.com/Thorncrag/ARRP/blob/progress-dashboard/PROGRESS.md"

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
            self.assertIn("  - full-technical", text, issue_id)
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
