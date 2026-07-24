import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_chain_dispatcher", ROOT / "scripts" / "run_chain_dispatcher.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class RunChainDispatcherTests(unittest.TestCase):
    def test_prompt_preserves_elim_identity_and_comprehensive_mode(self):
        payload = {
            "elim_decision": {
                "profile": {
                    "full_context": True,
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "xhigh",
                }
            }
        }
        prompt = MODULE.elim_prompt(Path("/tmp/run-chain.json"), payload)
        self.assertIn("You are Elim", prompt)
        self.assertIn("comprehensive full-context review", prompt)
        self.assertIn("15 percent hard", prompt)

    def test_config_uses_explicit_host_paths_and_conservative_profiles(self):
        config = json.loads(
            (ROOT / ".github" / "run-coordinator-bot.json").read_text()
        )
        for key in ("pythonPath", "gitPath", "githubCliPath", "codexPath"):
            self.assertTrue(Path(config["hostDispatcher"][key]).is_absolute())
        profiles = config["llmRouting"]["profiles"]
        self.assertEqual(profiles["read-heavy-triage"]["model"], "gpt-5.6-terra")
        self.assertEqual(profiles["substantive"]["model"], "gpt-5.6-sol")
        self.assertTrue(profiles["comprehensive"]["fullContext"])

    def test_comprehensive_epoch_proof_and_alerts_are_deduplicated(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            ledger = repo / "research" / "review-epochs.jsonl"
            ledger.parent.mkdir()
            ledger.write_text(
                json.dumps({"triggering_run_id": "chain-1"}) + "\n",
                encoding="utf-8",
            )
            self.assertTrue(MODULE.comprehensive_epoch_recorded(repo, "chain-1"))
            config = json.loads(
                (ROOT / ".github" / "run-coordinator-bot.json").read_text()
            )
            config["hostDispatcher"]["notificationPath"] = str(repo / "absent")
            control = {}
            manifest = {
                "chain_id": "chain-1",
                "updated_at": "2026-07-24T12:00:00+00:00",
                "status": "blocked",
                "failures": [
                    {
                        "stage": "project-integrity-bot",
                        "message": "failed",
                    }
                ],
            }
            self.assertTrue(MODULE.alert_failures(config, control, manifest, repo))
            self.assertFalse(MODULE.alert_failures(config, control, manifest, repo))
            self.assertEqual(len(control["action_items"]), 1)

    def test_thread_id_is_recovered_for_later_elim_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            events = Path(directory) / "elim.jsonl"
            events.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "turn.started"}),
                        json.dumps(
                            {
                                "type": "thread.started",
                                "thread_id": "019f9999-1234-7000-8000-123456789abc",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                MODULE.thread_id_from_jsonl(events),
                "019f9999-1234-7000-8000-123456789abc",
            )

    def test_synchronize_requires_main_before_fetching(self):
        fake = mock.Mock()
        fake.side_effect = [
            MODULE.subprocess.CompletedProcess([], 0, stdout="", stderr=""),
            MODULE.subprocess.CompletedProcess(
                [], 0, stdout="codex/run-chain-automation\n", stderr=""
            ),
        ]
        with mock.patch.object(MODULE, "command", fake):
            with self.assertRaisesRegex(RuntimeError, "not on main"):
                MODULE.synchronize_canonical_repo("/usr/bin/git", Path("/tmp/repo"))


if __name__ == "__main__":
    unittest.main()
