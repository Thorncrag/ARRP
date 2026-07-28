from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scripts import repository_gates as gates


def declaration(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "event": "declared",
        "gate_id": "GATE-001",
        "pr_number": 42,
        "pr_url": "https://github.com/Thorncrag/ARRP/pull/42",
        "head_sha": "a" * 40,
        "blocks_automation": True,
        "gate_class": "required_checks",
        "reason": "Required checks must pass before Progress runs.",
        "affected_stages": ["project-console-progress-bot"],
        "next_run_scope": ["all"],
        "owner": "Elim",
        "next_action": "Repair the required check.",
        "unblock_predicate": {"type": "pr_closed_or_merged"},
        "observed_since": "2026-07-28T00:00:00Z",
        "recorded_at": "2026-07-28T00:00:00Z",
        "source_id": "PR-42",
    }
    value.update(overrides)
    return value


def pull(number: int = 42, head: str = "a" * 40) -> dict[str, object]:
    return {
        "number": number,
        "html_url": f"https://github.com/Thorncrag/ARRP/pull/{number}",
        "head": {"sha": head},
        "base": {"sha": "b" * 40},
    }


class RepositoryGateProducerTest(unittest.TestCase):
    def test_zero_requires_complete_declaration_and_pull_request_scans(self) -> None:
        incomplete = gates.build_repository_gate_snapshot(
            repository="Thorncrag/ARRP",
            events=[],
            event_errors=["declaration scan unavailable"],
            open_pull_requests=[],
            pull_pagination={"complete": True, "actual_count": 0},
            validation={},
            checked_at="2026-07-28T12:00:00Z",
        )
        self.assertFalse(incomplete["complete"])
        self.assertIsNone(incomplete["count"])

        complete = gates.build_repository_gate_snapshot(
            repository="Thorncrag/ARRP",
            events=[],
            event_errors=[],
            open_pull_requests=[],
            pull_pagination={"complete": True, "actual_count": 0},
            validation={},
            checked_at="2026-07-28T12:00:00Z",
        )
        self.assertTrue(complete["complete"])
        self.assertEqual(complete["count"], 0)

    def test_valid_exact_head_gate_is_active(self) -> None:
        snapshot = gates.build_repository_gate_snapshot(
            repository="Thorncrag/ARRP",
            events=[declaration()],
            event_errors=[],
            open_pull_requests=[pull()],
            pull_pagination={"complete": True, "actual_count": 1},
            validation={42: {"mergeable": False}},
            checked_at="2026-07-28T12:00:00Z",
        )
        self.assertTrue(snapshot["complete"])
        self.assertEqual(snapshot["count"], 1)
        self.assertTrue(snapshot["items"][0]["exact_head_valid"])

    def test_closed_predicate_removes_gate_from_current_inventory(self) -> None:
        snapshot = gates.build_repository_gate_snapshot(
            repository="Thorncrag/ARRP",
            events=[declaration()],
            event_errors=[],
            open_pull_requests=[],
            pull_pagination={"complete": True, "actual_count": 0},
            validation={},
            checked_at="2026-07-28T12:00:00Z",
        )
        self.assertTrue(snapshot["complete"])
        self.assertEqual(snapshot["count"], 0)

    def test_changed_head_remains_visible_and_fails_closed(self) -> None:
        snapshot = gates.build_repository_gate_snapshot(
            repository="Thorncrag/ARRP",
            events=[declaration()],
            event_errors=[],
            open_pull_requests=[pull(head="c" * 40)],
            pull_pagination={"complete": True, "actual_count": 1},
            validation={42: {}},
            checked_at="2026-07-28T12:00:00Z",
        )
        self.assertFalse(snapshot["complete"])
        self.assertIsNone(snapshot["count"])
        self.assertEqual(snapshot["known_blocker_count"], 1)
        self.assertEqual(snapshot["items"][0]["validation_state"], "head_changed")

    def test_duplicate_and_malformed_declarations_are_rejected(self) -> None:
        active, errors = gates.active_gate_declarations(
            [declaration(), declaration(), {"event": "declared", "gate_id": "BAD"}]
        )
        self.assertEqual(len(active), 1)
        self.assertTrue(any("duplicate" in error for error in errors))
        self.assertTrue(any("missing" in error for error in errors))

    def test_pull_request_pagination_continues_past_one_hundred(self) -> None:
        calls: list[str] = []

        def request(path: str) -> object:
            calls.append(path)
            page = int(parse_qs(urlparse(path).query)["page"][0])
            if page == 1:
                return [pull(number=index, head=f"{index:040x}") for index in range(1, 101)]
            if page == 2:
                return [pull(number=101, head=f"{101:040x}")]
            raise AssertionError(path)

        rows, pagination = gates._paginate(
            request, "pulls?state=open&sort=created&direction=asc"
        )
        self.assertEqual(len(rows), 101)
        self.assertTrue(pagination["complete"])
        self.assertEqual(pagination["pages"], 2)

    def test_failed_refresh_retains_last_good_without_claiming_current_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "repository-gates.jsonl"
            path.write_text(
                json.dumps({"event": "registry_initialized"}) + "\n",
                encoding="utf-8",
            )
            last_good = {
                "complete": True,
                "checked_at": "2026-07-27T12:00:00Z",
                "source_revision": "prior",
                "items": [declaration()],
            }

            def unavailable(_path: str) -> object:
                raise RuntimeError("GitHub unavailable")

            snapshot = gates.produce_repository_gate_snapshot(
                repository="Thorncrag/ARRP",
                declarations_path=path,
                token="",
                last_good=last_good,
                request=unavailable,
            )
        self.assertEqual(snapshot["availability"], "last_valid_retained")
        self.assertFalse(snapshot["complete"])
        self.assertIsNone(snapshot["count"])
        self.assertEqual(snapshot["known_blocker_count"], 1)
        self.assertEqual(snapshot["trustworthy_through"], "2026-07-27T12:00:00Z")


if __name__ == "__main__":
    unittest.main()
