import argparse
import unittest

from scripts.append_agent_audit_log import entry


class AgentAuditLogTests(unittest.TestCase):
    def test_structured_entry_contains_filter_fields(self):
        args = argparse.Namespace(
            timestamp="2026-07-22T12:00:00-04:00", issue_task="Project task",
            task_type="Integrity", agent="project-integrity-bot", run_id="run-1",
            unit_id="unit-1", trigger="schedule", outcome="Completed",
            issue_page="N/A", audit_history="N/A", proposal_page="N/A", tier="none",
            files_changed="`report.md`", validation="Passed", commit="This commit",
            push_status="Proposed", rollback_notes="Close the PR.", blockers="None.",
        )

        rendered = entry(args)

        self.assertIn("| Agent | project-integrity-bot |", rendered)
        self.assertIn("| Run ID | run-1 |", rendered)
        self.assertIn("| Task type | Integrity |", rendered)
        self.assertIn("| Outcome | Completed |", rendered)


if __name__ == "__main__":
    unittest.main()
