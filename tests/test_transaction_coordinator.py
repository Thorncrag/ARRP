"""Coordinator bindings for the owner-local transaction lifecycle authority."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.transaction_lifecycle import (
    authorize_retry,
    read_events,
    start_transaction,
    transition_transaction,
)
from tests.test_arrp_nightly import GitFixture, MODULE


class TransactionCoordinatorTests(unittest.TestCase):
    def test_latest_status_cannot_erase_per_run_terminal_events(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = GitFixture(Path(directory))
            fixture.state.mkdir(parents=True)
            (fixture.state / "PAUSED").write_text("remain paused\n", encoding="utf-8")
            (fixture.state / "PAUSED").chmod(0o600)

            MODULE.prepare_transaction(fixture.config(), run_id="first-paused")
            MODULE.prepare_transaction(fixture.config(), run_id="second-paused")

            events = read_events(MODULE.transaction_events_path(fixture.config()))
            terminals = {
                event["run_id"]: event["state"]
                for event in events
                if event["state"] == "completed_noop"
            }
            self.assertEqual(terminals, {
                "first-paused": "completed_noop",
                "second-paused": "completed_noop",
            })
            status = json.loads((fixture.state / "status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["run_id"], "second-paused")

    def test_established_timestamp_run_id_reaches_lifecycle_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = GitFixture(Path(directory))
            fixture.state.mkdir(parents=True)
            (fixture.state / "PAUSED").write_text(
                "remain paused\n", encoding="utf-8"
            )
            (fixture.state / "PAUSED").chmod(0o600)

            result = MODULE.prepare_transaction(
                fixture.config(), run_id="arrp-20260729T060003Z"
            )

            self.assertEqual(result.status, "paused")
            events = read_events(
                MODULE.transaction_events_path(fixture.config())
            )
            self.assertEqual(events[0]["run_id"], "arrp-20260729T060003Z")

    def test_released_lock_with_missing_terminal_becomes_recovery_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = GitFixture(Path(directory))
            events_path = MODULE.transaction_events_path(fixture.config())
            start_transaction(
                events_path,
                run_id="abandoned-run",
                attempt_group_id="abandoned-run",
                attempt_number=1,
                trigger="fixture",
                branch="automation/nightly-abandoned",
                head="unknown",
                base="unknown",
                logical_worktree_id="abandoned-run",
                logical_run_id="abandoned-run",
                delta_digest="sha256:" + "0" * 64,
                owner="run-coordinator",
                next_action="Run transaction.",
            )
            fixture.state.mkdir(parents=True, exist_ok=True)
            (fixture.state / "run-owner.json").write_text(
                json.dumps({"schema_version": "1.0", "run_id": "abandoned-run", "pid": 1}),
                encoding="utf-8",
            )
            (fixture.state / "PAUSED").write_text("remain paused\n", encoding="utf-8")
            (fixture.state / "PAUSED").chmod(0o600)

            MODULE.prepare_transaction(fixture.config(), run_id="recovery-observer")

            latest = [event for event in read_events(events_path) if event["run_id"] == "abandoned-run"][-1]
            self.assertEqual(latest["state"], "recovery_pending")
            self.assertEqual(latest["failure_code"], "abandoned-released-lock")

    def test_moving_slot_projection_cannot_replay_scheduled_occurrence(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = GitFixture(Path(directory))
            scheduled_for = "2026-07-29T02:00:00-04:00"
            config = MODULE.RunnerConfig(
                fixture.repo,
                fixture.state,
                fixture_root=fixture.root,
                runtime_files=(),
                trigger="scheduled",
                scheduled_for=scheduled_for,
            )
            first = MODULE.prepare_transaction(config, run_id="scheduled-first")
            self.assertEqual(first.status, "completed")
            slot = fixture.state / "last-scheduled-slot.json"
            slot.rename(fixture.state / "moved-slot-projection.json")

            second = MODULE.prepare_transaction(config, run_id="scheduled-second")

            self.assertEqual(second.status, "completed")
            status = json.loads((fixture.state / "status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["validation_summary"]["reason"], "scheduled_occurrence_already_recorded")
            starts = [
                event for event in read_events(MODULE.transaction_events_path(config))
                if event["event_type"] == "started"
            ]
            self.assertEqual([event["run_id"] for event in starts], ["scheduled-first"])

    def test_linked_retry_cannot_auto_invoke_elim_or_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = GitFixture(Path(directory))
            config = MODULE.RunnerConfig(
                fixture.repo,
                fixture.state,
                fixture_root=fixture.root,
                runtime_files=(),
                trigger="manual-retry",
                attempt_group_id="retry-group",
                retry_attempt_number=2,
                retry_authorization={
                    "authorization_id": "retry:prior:1",
                    "predecessor_run_id": "prior",
                    "predecessor_terminal_digest": "sha256:" + "0" * 64,
                    "expires_at": "2099-01-01T00:00:00Z",
                },
            )

            with self.assertRaisesRegex(MODULE.TransactionError, "deterministic recovery"):
                MODULE.prepare_transaction(
                    config,
                    run_id="linked-retry",
                    local_cycle=mock.Mock(),
                )

    def test_exact_authorized_linked_retry_is_one_use(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = GitFixture(Path(directory))
            events_path = MODULE.transaction_events_path(fixture.config())
            start_transaction(
                events_path,
                run_id="prior-run",
                attempt_group_id="retry-group",
                attempt_number=1,
                trigger="fixture",
                branch="automation/nightly-prior",
                head="a" * 40,
                base="a" * 40,
                logical_worktree_id="prior-run",
                logical_run_id="prior-run",
                delta_digest="sha256:" + "0" * 64,
                owner="run-coordinator",
                next_action="Reconcile prior worktree.",
            )
            transition_transaction(
                events_path,
                run_id="prior-run",
                state="failed_preserved",
                owner="run-coordinator",
                next_action="Preserve material.",
                failure_code="fixture-failure",
            )
            transition_transaction(
                events_path,
                run_id="prior-run",
                state="recovery_pending",
                owner="run-coordinator",
                next_action="Reconcile material.",
                failure_code="fixture-failure",
            )
            transition_transaction(
                events_path,
                run_id="prior-run",
                state="recovery_packaged",
                owner="run-coordinator",
                next_action="Approve recoverable retirement.",
                package_digest="sha256:" + "2" * 64,
                recovery_proof={
                    "proof_digest": "sha256:" + "3" * 64,
                    "evidence_ref": "owner-local:transaction-recovery/prior-run:package",
                },
            )
            transition_transaction(
                events_path,
                run_id="prior-run",
                state="recoverably_retired",
                owner="run-coordinator",
                next_action="Owner authorized one linked retry.",
                package_digest="sha256:" + "2" * 64,
                recovery_proof={
                    "proof_digest": "sha256:" + "3" * 64,
                    "evidence_ref": "owner-local:transaction-recovery/prior-run:package",
                },
            )
            authorization = authorize_retry(
                events_path,
                predecessor_run_id="prior-run",
                owner="benjamin",
                expires_at="2099-01-01T00:00:00Z",
            )
            retry_config = MODULE.RunnerConfig(
                fixture.repo,
                fixture.state,
                fixture_root=fixture.root,
                runtime_files=(),
                trigger="manual-retry",
                attempt_group_id="retry-group",
                retry_attempt_number=2,
                retry_authorization=authorization,
            )

            accepted = MODULE.prepare_transaction(retry_config, run_id="linked-retry")
            self.assertEqual(accepted.status, "completed")
            with self.assertRaisesRegex(MODULE.TransactionError, "lifecycle start was rejected"):
                MODULE.prepare_transaction(retry_config, run_id="reused-retry")

            claimed = [
                event for event in read_events(events_path)
                if event["event_type"] == "retry_claimed"
            ]
            self.assertEqual([event["run_id"] for event in claimed], ["linked-retry"])

    def test_second_live_attempt_in_group_is_rejected_before_worktree_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = GitFixture(Path(directory))
            config = MODULE.RunnerConfig(
                fixture.repo,
                fixture.state,
                fixture_root=fixture.root,
                runtime_files=(),
                attempt_group_id="shared-group",
            )
            first = MODULE.prepare_transaction(config, run_id="group-first")
            self.assertTrue(Path(first.worktree_path).is_dir())

            with self.assertRaisesRegex(MODULE.TransactionError, "lifecycle start was rejected"):
                MODULE.prepare_transaction(config, run_id="group-second")
            self.assertFalse((fixture.state / "worktrees/group-second").exists())


if __name__ == "__main__":
    unittest.main()
