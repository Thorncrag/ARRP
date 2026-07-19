import unittest

from scripts.audit_project_consistency import ROOT, active_project_files, github_repository_targets


class GitHubIssueLinkTests(unittest.TestCase):
    def test_extracts_main_branch_blob_target(self):
        body = (
            "[Horizon log](https://github.com/Thorncrag/ARRP/blob/main/"
            "framework/logs/HORIZON_SCAN_LOG.md#horizon-integration-log)"
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


if __name__ == "__main__":
    unittest.main()
