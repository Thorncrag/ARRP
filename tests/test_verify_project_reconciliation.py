import contextlib
import fcntl
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("project_reconciliation", ROOT / "scripts" / "verify_project_reconciliation.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class VerifyProjectReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.state = self.root / "state"
        self.repo.mkdir()
        self.state.mkdir()
        os.chmod(self.root, 0o700)
        os.chmod(self.state, 0o700)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "ARRP Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git("commit", "-m", "fixture")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        (self.state / "runs").mkdir()
        (self.state / "worktrees").mkdir()
        handoffs = self.state / "records" / "handoffs"
        incidents = self.state / "records" / "automation"
        handoffs.mkdir(parents=True)
        incidents.mkdir(parents=True)
        (handoffs / "current-task.local.md").write_text(
            "\n".join(
                (
                    "---",
                    "status: inactive",
                    "---",
                    "| Handoff state | Inactive |",
                    "| Active issue/task | None. |",
                    "| Next step | None. |",
                    "| Blockers/questions | None. |",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        (incidents / "operational-incidents.jsonl").write_text(
            '{"schema_version":1,"event_type":"registry_initialized"}\n',
            encoding="utf-8",
        )
        (self.state / "incident-spool.jsonl").write_text("", encoding="utf-8")
        (self.state / "status.json").write_text(
            '{"schema_version":"1.0","run_id":"none","status":"idle"}\n',
            encoding="utf-8",
        )
        (self.state / "PAUSED").write_text("", encoding="utf-8")
        (self.state / "run.lock").write_text("", encoding="utf-8")
        for path in self.state.rglob("*"):
            if path.is_file():
                os.chmod(path, 0o600)
        self.authority = MODULE.ProjectPathAuthority.fixture(
            self.root,
            repository_root=self.repo,
            state_root=self.state,
        )
        self.now = datetime(2026, 7, 29, 18, 0, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *args: str, cwd: Path | None = None) -> str:
        completed = subprocess.run(
            ["git", "-C", str(cwd or self.repo), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return completed.stdout.strip()

    def collect(self):
        return MODULE.collect_local(self.authority, checked_at=self.now)

    def ledger(self, snapshot, *, pending=()):
        pending_keys = set(pending)
        rows = []
        for items in snapshot["inventory"].values():
            for item in items:
                if item["status"] != "retained":
                    continue
                key = (item["kind"], item["id"])
                is_pending = key in pending_keys
                rows.append(
                    {
                        "id": item["id"],
                        "kind": item["kind"],
                        "identity_binding": item["identity_binding"],
                        "disposition": (
                            "pending_human_review"
                            if is_pending
                            else "retained_historical"
                        ),
                        "evidence_refs": ["fixture:evidence"],
                        "reviewed_at": self.now.isoformat(),
                        "next_action": "Retain for fixture verification.",
                        "reconciliation_eligible": not is_pending,
                    }
                )
        return {
            "schema_version": 1,
            "ledger_id": "fixture-ledger",
            "reviewed_at": self.now.isoformat(),
            "local_snapshot_digest": snapshot["inventory_digest"],
            "retained_states": rows,
        }

    def live(self, snapshot, *, checked_at=None, revision=None, **overrides):
        remote = snapshot["inventory"]["remote_revision"][0]["revision"]
        value = {
            "schema_version": 1,
            "complete": True,
            "checked_at": (checked_at or self.now).isoformat(),
            "max_age_seconds": 1800,
            "origin_main_revision": revision or remote,
            "default_branch": "main",
            "open_pull_requests": [],
            "in_progress_actions": [],
            "required_actions_status": "success",
            "required_actions_revision": remote,
            "pages_status": "success",
            "pages_revision": remote,
            "vercel_status": "success",
            "vercel_revision": remote,
        }
        value.update(overrides)
        return value

    def test_clean_fixed_authority_with_pause_is_fully_reconciled(self):
        current = self.collect()
        result = MODULE.verify(
            self.ledger(current), current, self.live(current), now=self.now
        )
        self.assertTrue(result["fully_reconciled"])
        self.assertEqual(result["reason_codes"], [])
        self.assertEqual(
            current["inventory"]["control_state"][0]["status"], "paused"
        )

    def test_new_branch_and_pending_disposition_fail_closed(self):
        self.git("branch", "preserved")
        current = self.collect()
        result = MODULE.verify(
            self.ledger(current, pending={("local_branch", "preserved")}),
            current,
            self.live(current),
            now=self.now,
        )
        self.assertIn("PENDING_REVIEW", result["reason_codes"])

        missing = self.ledger(current)
        missing["retained_states"] = [
            item
            for item in missing["retained_states"]
            if not (
                item["kind"] == "local_branch" and item["id"] == "preserved"
            )
        ]
        self.assertIn(
            "UNREGISTERED_STATE",
            MODULE.verify(
                missing, current, self.live(current), now=self.now
            )["reason_codes"],
        )

    def test_dirty_worktree_binding_drift_is_detected(self):
        worktree = self.state / "worktrees" / "run-1"
        self.git("worktree", "add", "-b", "run-1", str(worktree))
        (worktree / "README.md").write_text("first\n", encoding="utf-8")
        current = self.collect()
        ledger = self.ledger(current)
        self.assertTrue(
            MODULE.verify(
                ledger, current, self.live(current), now=self.now
            )["fully_reconciled"]
        )
        (worktree / "README.md").write_text("second\n", encoding="utf-8")
        changed = self.collect()
        result = MODULE.verify(
            ledger, changed, self.live(changed), now=self.now
        )
        self.assertIn("LEDGER_INVALID", result["reason_codes"])
        self.assertIn("RETAINED_STATE_UNBOUND", result["reason_codes"])

    def test_new_runtime_run_is_not_silently_clear(self):
        run = self.state / "runs" / "run-2"
        run.mkdir()
        (run / "result.json").write_text('{"status":"failed"}\n', encoding="utf-8")
        current = self.collect()
        ledger = self.ledger(current)
        ledger["retained_states"] = [
            item
            for item in ledger["retained_states"]
            if not (item["kind"] == "runtime_run" and item["id"] == "run-2")
        ]
        self.assertIn(
            "UNREGISTERED_STATE",
            MODULE.verify(
                ledger, current, self.live(current), now=self.now
            )["reason_codes"],
        )

    def test_retained_run_symlink_is_bound_without_being_followed(self):
        run = self.state / "runs" / "run-symlink"
        run.mkdir()
        outside = self.root / "outside.txt"
        outside.write_text("first\n", encoding="utf-8")
        (run / "tool-link").symlink_to(outside)
        current = self.collect()
        row = next(
            item
            for item in current["inventory"]["runtime_runs"]
            if item["id"] == "run-symlink"
        )
        first_binding = row["identity_binding"]["sha256"]
        outside.write_text("second\n", encoding="utf-8")
        changed = self.collect()
        changed_row = next(
            item
            for item in changed["inventory"]["runtime_runs"]
            if item["id"] == "run-symlink"
        )
        self.assertEqual(
            first_binding,
            changed_row["identity_binding"]["sha256"],
        )

    def test_stale_incomplete_and_revision_mismatched_live_readback_fail(self):
        current = self.collect()
        ledger = self.ledger(current)
        stale = self.live(
            current, checked_at=self.now - timedelta(hours=2)
        )
        self.assertIn(
            "LIVE_READBACK_STALE",
            MODULE.verify(ledger, current, stale, now=self.now)["reason_codes"],
        )
        incomplete = self.live(current, complete=False)
        self.assertIn(
            "LIVE_READBACK_INCOMPLETE",
            MODULE.verify(
                ledger, current, incomplete, now=self.now
            )["reason_codes"],
        )
        mismatch = self.live(current, revision="0" * 40)
        self.assertIn(
            "LIVE_READBACK_MISMATCH",
            MODULE.verify(
                ledger, current, mismatch, now=self.now
            )["reason_codes"],
        )

    def test_active_lock_and_stale_handoff_fail(self):
        lock_path = self.state / "run.lock"
        with lock_path.open("a+") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            current = self.collect()
            result = MODULE.verify(
                self.ledger(current),
                current,
                self.live(current),
                now=self.now,
            )
            self.assertIn("ACTIVE_LOCK", result["reason_codes"])
        handoff = (
            self.state / "records" / "handoffs" / "current-task.local.md"
        )
        handoff.write_text(
            "status: inactive\n| Handoff state | Blocked |\n",
            encoding="utf-8",
        )
        current = self.collect()
        self.assertIn(
            "PENDING_REVIEW",
            MODULE.verify(
                self.ledger(current),
                current,
                self.live(current),
                now=self.now,
            )["reason_codes"],
        )

    def test_cli_has_no_root_or_owner_file_substitution(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                MODULE._parser().parse_args(
                    ["--ledger", "/tmp/substitute.json"]
                )
        with self.assertRaises(MODULE.PathAuthorityError):
            MODULE.ProjectPathAuthority.fixture(
                self.root,
                repository_root=ROOT,
                state_root=self.state,
            )

    def test_public_result_is_path_safe(self):
        current = self.collect()
        result = MODULE.verify(
            self.ledger(current), current, self.live(current), now=self.now
        )
        rendered = json.dumps(result)
        self.assertNotIn(str(self.root), rendered)
        self.assertNotIn(str(self.repo), rendered)
        self.assertNotIn(str(self.state), rendered)


if __name__ == "__main__":
    unittest.main()
