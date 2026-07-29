from __future__ import annotations

import tempfile
import unittest
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from scripts.transaction_lifecycle import (
    TransactionLifecycleError,
    authorize_retry,
    build_console_projection,
    mark_abandoned_transactions,
    project_transaction_log,
    start_transaction,
    transition_transaction,
    validate_recovery_package_manifest,
    create_recovery_package,
    import_preexisting_attempt_group,
    import_historical_terminal_run,
    read_events,
    validate_event,
    _append,
)


UTC = timezone.utc
DIGEST = "sha256:" + "a" * 64
OTHER_DIGEST = "sha256:" + "b" * 64
NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)


def proof(name: str) -> dict[str, str]:
    return {
        "proof_digest": DIGEST,
        "evidence_ref": f"owner-local:transaction-evidence/{name}",
    }


class TransactionLifecycleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.events = Path(self.temporary.name) / "transaction-events.jsonl"

    def start(self, run_id: str = "run-1", *, group: str = "occurrence-1", attempt: int = 1, worktree: str | None = "worktree-1", authorization=None):
        return start_transaction(
            self.events,
            run_id=run_id,
            attempt_group_id=group,
            attempt_number=attempt,
            trigger="scheduled-nightly",
            branch=f"transaction-{run_id}",
            head="head-1",
            base="base-1",
            logical_worktree_id=worktree,
            logical_run_id=run_id,
            delta_digest=DIGEST,
            owner="automation-owner",
            next_action="Review the retained transaction.",
            retry_authorization=authorization,
            now=NOW,
        )

    def fail_to_package(self, run_id: str = "run-1") -> None:
        transition_transaction(self.events, run_id=run_id, state="failed_preserved", owner="automation-owner", next_action="Create recovery package.", failure_code="publication-failed", now=NOW)
        transition_transaction(self.events, run_id=run_id, state="recovery_pending", owner="automation-owner", next_action="Package unique material.", now=NOW)
        transition_transaction(self.events, run_id=run_id, state="recovery_packaged", owner="automation-owner", next_action="Approve recoverable retirement.", package_digest=OTHER_DIGEST, recovery_proof=proof("package-1"), now=NOW)

    def migration_members(self, count: int = 11):
        members = []
        for number in range(1, count + 1):
            digest = "sha256:" + f"{number:064x}"
            run_id = f"legacy-run-{number:02d}"
            members.append(
                {
                    "run_id": run_id,
                    "attempt_number": number,
                    "branch": f"automation/nightly-{run_id}",
                    "head": f"head-{number:02d}",
                    "base": f"base-{number:02d}",
                    "logical_worktree_id": run_id,
                    "logical_run_id": run_id,
                    "delta_digest": digest,
                    "package_digest": digest,
                    "recovery_proof": {
                        "proof_digest": digest,
                        "evidence_ref": (
                            f"owner-local:transaction-recovery/{run_id}"
                        ),
                    },
                    "evidence_refs": [
                        f"owner-local:transaction-recovery/{run_id}"
                    ],
                    "incident_id": "INC-2026-004",
                }
            )
        return members

    def import_migration(self):
        return import_preexisting_attempt_group(
            self.events,
            migration_batch_id="migration-p6-20260729",
            attempt_group_id="scheduled-20260727T060000Z",
            source_slots=(
                "2026-07-27T02:00:00-04:00",
                "2026-07-28T02:00:00-04:00",
            ),
            members=self.migration_members(),
            owner="automation-owner",
            next_action="Retire each source only after exact owner approval.",
            now=NOW,
        )

    def import_historical_terminal(self, *, state: str = "completed_noop"):
        return import_historical_terminal_run(
            self.events,
            migration_batch_id="migration-terminal-20260729",
            attempt_group_id="scheduled-legacy-no-worktree",
            source_slot="2026-07-26T02:00:00-04:00",
            run_id="legacy-no-worktree-run",
            attempt_number=1,
            trigger="historical-migration",
            branch="automation/legacy-no-worktree",
            head="head-legacy",
            base="base-legacy",
            logical_run_id="legacy-no-worktree-run",
            delta_digest=DIGEST,
            state=state,
            terminal_proof=proof("legacy-no-worktree"),
            owner="automation-owner",
            next_action="Retain immutable terminal reconstruction.",
            now=NOW,
        )

    def test_latest_projection_cannot_erase_prior_terminal_outcome(self) -> None:
        self.start()
        transition_transaction(self.events, run_id="run-1", state="completed_noop", owner="automation-owner", next_action="Retain immutable terminal history.", terminal_proof=proof("noop"), now=NOW)
        self.start("run-2", group="occurrence-2", worktree=None)
        projection = project_transaction_log(self.events)
        self.assertEqual(projection["unresolved_count"], 1)
        self.assertEqual(projection["items"][0]["run_id"], "run-2")
        self.assertIn('"run_id":"run-1"', self.events.read_text(encoding="utf-8"))

    def test_historical_terminal_import_is_single_member_and_non_live(self) -> None:
        event = self.import_historical_terminal()
        self.assertEqual(event["event_type"], "historical_imported")
        self.assertEqual(event["state"], "completed_noop")
        self.assertIsNone(event["logical_worktree_id"])
        self.assertIsNone(event["package_digest"])
        self.assertIsNone(event["recovery_proof"])
        self.assertEqual(project_transaction_log(self.events)["unresolved_count"], 0)

    def test_historical_terminal_import_rejects_live_or_nonterminal_shortcuts(self) -> None:
        with self.assertRaisesRegex(TransactionLifecycleError, "completed terminal state"):
            self.import_historical_terminal(state="recovery_packaged")
        event = self.import_historical_terminal()
        forged = dict(event)
        forged["logical_worktree_id"] = "forbidden-legacy-worktree"
        forged["package_digest"] = OTHER_DIGEST
        forged["recovery_proof"] = proof("forbidden-legacy-worktree")
        forged["failure_code"] = "preexisting-retained-transaction"
        forged["event_sha256"] = None
        with self.assertRaisesRegex(TransactionLifecycleError, "migration-only contract"):
            validate_event(forged)

    def test_established_timestamp_run_identity_is_supported(self) -> None:
        event = self.start("arrp-20260729T060003Z", group="scheduled:2026-07-29")
        self.assertEqual(event["run_id"], "arrp-20260729T060003Z")

    def test_released_lock_without_terminal_becomes_abandoned_recovery_pending(self) -> None:
        self.start()
        records = mark_abandoned_transactions(self.events, released_lock_run_ids=["run-1"], owner="automation-owner", now=NOW)
        self.assertEqual(records[0]["event_type"], "abandoned")
        projection = project_transaction_log(self.events)
        self.assertEqual(projection["items"][0]["state"], "recovery_pending")
        self.assertEqual(projection["items"][0]["failure_code"], "abandoned-released-lock")

    def test_retry_is_hash_bound_one_use_and_requires_retired_predecessor(self) -> None:
        self.start()
        self.fail_to_package()
        transition_transaction(self.events, run_id="run-1", state="recoverably_retired", owner="automation-owner", next_action="Retry may be claimed by authorization.", package_digest=OTHER_DIGEST, recovery_proof=proof("retired"), now=NOW)
        authorization = authorize_retry(self.events, predecessor_run_id="run-1", owner="automation-owner", expires_at="2026-07-30T12:00:00Z", now=NOW)
        self.start("run-2", attempt=2, worktree="worktree-2", authorization=authorization)
        with self.assertRaisesRegex(TransactionLifecycleError, "already used"):
            self.start("run-3", attempt=3, worktree="worktree-3", authorization=authorization)
        candidate = json.loads(self.events.read_text(encoding="utf-8").splitlines()[-1])
        candidate["run_id"] = "run-4"
        candidate["event_id"] = "run-4:0001"
        candidate["logical_run_id"] = "run-4"
        candidate["logical_worktree_id"] = None
        candidate["event_sha256"] = None
        with self.assertRaisesRegex(TransactionLifecycleError, "already used"):
            _append(self.events, candidate)

    def test_live_worktree_prevents_a_second_attempt_even_with_a_different_run_id(self) -> None:
        self.start()
        with self.assertRaisesRegex(TransactionLifecycleError, "live runtime worktree"):
            self.start("run-2", attempt=1, worktree="worktree-2", authorization=None)

    def test_reconciled_material_does_not_make_a_registered_worktree_non_live(self) -> None:
        self.start()
        transition_transaction(
            self.events,
            run_id="run-1",
            state="failed_preserved",
            owner="automation-owner",
            next_action="Reconcile preserved material.",
            failure_code="fixture-failure",
            now=NOW,
        )
        transition_transaction(
            self.events,
            run_id="run-1",
            state="recovery_pending",
            owner="automation-owner",
            next_action="Record reconciliation proof.",
            now=NOW,
        )
        transition_transaction(
            self.events,
            run_id="run-1",
            state="reconciled_or_superseded",
            owner="automation-owner",
            next_action="Package evidence and retire the worktree.",
            terminal_proof=proof("reconciled"),
            now=NOW,
        )
        with self.assertRaisesRegex(
            TransactionLifecycleError, "live runtime worktree"
        ):
            self.start(
                "run-2",
                attempt=1,
                worktree="worktree-2",
                authorization=None,
            )

    def test_historical_batch_import_is_complete_atomic_and_unresolved(self) -> None:
        imported = self.import_migration()

        self.assertEqual(len(imported), 11)
        self.assertEqual(len(read_events(self.events)), 11)
        projection = project_transaction_log(self.events)
        self.assertEqual(projection["unresolved_count"], 11)
        self.assertEqual(
            {item["state"] for item in projection["items"]},
            {"recovery_packaged"},
        )
        with self.assertRaisesRegex(
            TransactionLifecycleError, "live runtime worktree"
        ):
            self.start(
                "new-run",
                group="scheduled-20260727T060000Z",
                attempt=1,
            )

    def test_historical_batch_truncation_and_forgery_fail_closed(self) -> None:
        self.import_migration()
        rows = self.events.read_text(encoding="utf-8").splitlines()
        self.events.write_text("\n".join(rows[:-1]) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(
            TransactionLifecycleError, "incomplete or mismatched"
        ):
            read_events(self.events)

        forged = Path(self.temporary.name) / "forged-events.jsonl"
        candidate = json.loads(rows[0])
        candidate["event_sha256"] = None
        with self.assertRaisesRegex(
            TransactionLifecycleError, "incomplete or mismatched"
        ):
            _append(forged, candidate)
        self.assertEqual(forged.read_text(encoding="utf-8"), "")

    def test_single_historical_import_can_append_to_existing_authority(self) -> None:
        self.start("ordinary-run", group="ordinary-group", worktree=None)
        transition_transaction(
            self.events,
            run_id="ordinary-run",
            state="completed_noop",
            owner="automation-owner",
            next_action="Retain terminal history.",
            terminal_proof=proof("ordinary-run"),
            now=NOW,
        )
        imported = import_preexisting_attempt_group(
            self.events,
            migration_batch_id="migration-single-20260729",
            attempt_group_id="legacy-single-group",
            source_slots=("manual-p5-supervised",),
            members=self.migration_members(1),
            owner="automation-owner",
            next_action="Retire after exact approval.",
            now=NOW,
        )

        self.assertEqual(imported[0]["failure_code"], "preexisting-retained-transaction")
        self.assertEqual(project_transaction_log(self.events)["unresolved_count"], 1)

    def test_partial_migration_retirement_cannot_unlock_retry(self) -> None:
        imported = self.import_migration()
        for event in imported[:10]:
            transition_transaction(
                self.events,
                run_id=event["run_id"],
                state="recoverably_retired",
                owner="automation-owner",
                next_action="Retain the recovery package and receipt.",
                package_digest=event["package_digest"],
                recovery_proof=event["recovery_proof"],
                now=NOW,
            )
        with self.assertRaisesRegex(
            TransactionLifecycleError, "historical attempt group remains live"
        ):
            authorize_retry(
                self.events,
                predecessor_run_id=imported[0]["run_id"],
                owner="automation-owner",
                expires_at="2026-07-30T12:00:00Z",
                now=NOW,
            )

    def test_closed_migration_group_still_requires_exact_manual_retry(self) -> None:
        imported = self.import_migration()
        for event in imported:
            transition_transaction(
                self.events,
                run_id=event["run_id"],
                state="recoverably_retired",
                owner="automation-owner",
                next_action="Retain the recovery package and receipt.",
                package_digest=event["package_digest"],
                recovery_proof=event["recovery_proof"],
                now=NOW,
            )
        authorization = authorize_retry(
            self.events,
            predecessor_run_id=imported[-1]["run_id"],
            owner="automation-owner",
            expires_at="2026-07-30T12:00:00Z",
            now=NOW,
        )
        self.start(
            "manual-retry-12",
            group="scheduled-20260727T060000Z",
            attempt=12,
            authorization=authorization,
        )
        self.assertEqual(
            project_transaction_log(self.events)["unresolved_count"],
            1,
        )

    def test_transition_order_and_recovery_manifest_are_fail_closed(self) -> None:
        self.start()
        with self.assertRaisesRegex(TransactionLifecycleError, "not permitted"):
            transition_transaction(self.events, run_id="run-1", state="recovery_pending", owner="automation-owner", next_action="Skip preservation.", now=NOW)
        manifest = validate_recovery_package_manifest({
            "schema_version": 1, "recovery_package_id": "trp:run-1", "run_id": "run-1", "created_at": "2026-07-29T12:00:00Z", "branch": "transaction-run-1", "head": "head-1", "base": "base-1", "commit_digest": DIGEST, "diff_digest": DIGEST, "untracked_digest": DIGEST, "package_digest": OTHER_DIGEST, "manifest_sha256": None,
        })
        self.assertTrue(manifest["manifest_sha256"].startswith("sha256:"))
        manifest["recovery_package_id"] = "/Users/private/package"
        with self.assertRaises(TransactionLifecycleError):
            validate_recovery_package_manifest(manifest)

    def test_projection_never_exposes_worktree_or_evidence_reference(self) -> None:
        self.start()
        projection = project_transaction_log(self.events)
        rendered = str(projection)
        self.assertNotIn("worktree-1", rendered)
        self.assertNotIn("owner-local:", rendered)

    def test_recovery_package_is_non_checkout_and_reconstructable(self) -> None:
        root = Path(self.temporary.name) / "recovery"
        manifest = create_recovery_package(
            root,
            run_id="run-1",
            branch="transaction-run-1",
            head="head-1",
            base="base-1",
            commit_bundle=b"commit-material",
            diff=b"diff-material",
            untracked={"notes.txt": b"untracked-material"},
            now=NOW,
        )
        package = root / manifest["recovery_package_id"].replace(":", "-")
        self.assertEqual((package / "commits.bundle").read_bytes(), b"commit-material")
        self.assertEqual((package / "delta.patch").read_bytes(), b"diff-material")
        self.assertEqual((package / "untracked" / "notes.txt").read_bytes(), b"untracked-material")
        self.assertFalse((package / ".git").exists())
        with self.assertRaisesRegex(TransactionLifecycleError, "already exists"):
            create_recovery_package(root, run_id="run-1", branch="transaction-run-1", head="head-1", base="base-1", commit_bundle=b"commit-material", diff=b"diff-material", untracked={"notes.txt": b"untracked-material"}, now=NOW)

    def test_console_projection_uses_the_fixed_public_safe_contract(self) -> None:
        self.start()
        view = build_console_projection(
            [
                json.loads(line)
                for line in self.events.read_text(encoding="utf-8").splitlines()
            ],
            now=NOW,
        )
        self.assertEqual(
            set(view),
            {"schema_version", "availability", "complete", "generated_at", "items", "reason_code"},
        )
        self.assertEqual(view["items"][0]["specialist_route"], "automation:agents:run-coordinator-bot")
        self.assertNotIn("logical_worktree_id", view["items"][0])

    def test_event_log_rejects_symlink_and_unsafe_mode(self) -> None:
        target = Path(self.temporary.name) / "target.jsonl"
        target.write_text("", encoding="utf-8")
        link = Path(self.temporary.name) / "linked.jsonl"
        link.symlink_to(target)
        with self.assertRaisesRegex(TransactionLifecycleError, "non-symlink"):
            start_transaction(
                link,
                run_id="run-link",
                attempt_group_id="occurrence-link",
                attempt_number=1,
                trigger="scheduled-nightly",
                branch="transaction-run-link",
                head="head-1",
                base="base-1",
                logical_worktree_id=None,
                logical_run_id="run-link",
                delta_digest=DIGEST,
                owner="automation-owner",
                next_action="Do not follow a symlink.",
                now=NOW,
            )
        with self.assertRaisesRegex(TransactionLifecycleError, "owner-only"):
            os.chmod(target, 0o644)
            read_events(target)

    def test_malformed_existing_sequence_fails_closed(self) -> None:
        self.start()
        row = json.loads(self.events.read_text(encoding="utf-8"))
        row["event_id"] = "run-1:0003"
        row["event_sha256"] = None
        self.events.write_text(json.dumps(row) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(TransactionLifecycleError, "sequence is malformed"):
            read_events(self.events)


if __name__ == "__main__":
    unittest.main()
