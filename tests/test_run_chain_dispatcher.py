import importlib.util
import hashlib
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
            "chain_id": "chain-1",
            "elim_decision": {
                "profile": {
                    "full_context": True,
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "xhigh",
                }
            },
            "usage": {
                "host_monitor": {
                    "status_path": ".tmp/run-coordinator/chain-1/usage-status.json",
                    "snapshot_max_age_seconds": 120,
                }
            },
        }
        prompt = MODULE.elim_prompt(Path("/tmp/run-chain.json"), payload)
        self.assertIn("You are Elim", prompt)
        self.assertIn("comprehensive full-context review", prompt)
        self.assertIn("15 percent hard", prompt)
        self.assertIn("approved host dispatcher", prompt)
        self.assertIn("Do not launch a second Codex app-server", prompt)
        self.assertIn("usage-status.json", prompt)

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
        self.assertEqual(config["usage"]["monitorIntervalSeconds"], 60)
        self.assertEqual(config["usage"]["snapshotMaxAgeSeconds"], 120)

    def test_dispatcher_uses_only_the_reviewed_config_path(self):
        source = (ROOT / "scripts" / "run_chain_dispatcher.py").read_text()
        self.assertNotIn('parser.add_argument("--config"', source)
        self.assertIn("config = read_json(CONFIG)", source)

    def test_coordinator_reads_fresh_queue_inputs_through_github_api(self):
        workflow = (
            ROOT / ".github" / "workflows" / "run-coordinator-bot.yml"
        ).read_text()
        self.assertIn(
            "https://api.github.com/repos/Thorncrag/ARRP/contents/${name}.json"
            "?ref=project-console-data",
            workflow,
        )
        self.assertIn("application/vnd.github.raw+json", workflow)

    def test_elim_result_schema_is_strict_structured_output_compatible(self):
        schema = json.loads(
            (
                ROOT
                / "framework"
                / "agents"
                / "elim-work-unit-result.schema.json"
            ).read_text()
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), set(schema["properties"]))
        self.assertNotIn("uniqueItems", json.dumps(schema))
        self.assertEqual(schema["properties"]["schema_version"]["type"], "integer")
        for name in ("work_type", "outcome"):
            self.assertEqual(schema["properties"][name]["type"], "string")
        self.assertEqual(
            schema["properties"]["authority"]["properties"]["classification"]["type"],
            "string",
        )
        self.assertEqual(
            schema["properties"]["validation"]["items"]["properties"]["status"]["type"],
            "string",
        )
        self.assertEqual(
            set(schema["properties"]["validation"]["items"]["required"]),
            set(schema["properties"]["validation"]["items"]["properties"]),
        )
        self.assertEqual(
            schema["properties"]["continuation"]["properties"]["state"]["type"],
            "string",
        )

    def test_contained_path_rejects_parent_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            outside = Path(directory) / "outside"
            root.mkdir()
            outside.mkdir()
            (root / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(MODULE.ContextError):
                MODULE.contained_path(root / ".." / "outside", root)
            with self.assertRaises(MODULE.ContextError):
                MODULE.contained_path(root / "link" / "payload.json", root)

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
            with mock.patch.object(MODULE, "command"):
                self.assertTrue(MODULE.alert_failures(config, control, manifest, repo))
                self.assertFalse(MODULE.alert_failures(config, control, manifest, repo))
            self.assertEqual(len(control["action_items"]), 1)
            healthy = {
                "chain_id": "chain-2",
                "updated_at": "2026-07-24T13:00:00+00:00",
                "status": "complete",
                "failures": [],
                "work_queue": {"problems": []},
            }
            self.assertTrue(MODULE.alert_failures(config, control, healthy, repo))
            self.assertEqual(control["action_items"], [])
            self.assertFalse(MODULE.alert_failures(config, control, healthy, repo))

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

    def test_manifest_must_match_current_main_before_launch(self):
        with mock.patch.object(
            MODULE,
            "command",
            return_value=MODULE.subprocess.CompletedProcess(
                [],
                0,
                stdout="a" * 40 + "\n",
                stderr="",
            ),
        ):
            self.assertTrue(
                MODULE.manifest_matches_current_repo(
                    "/usr/bin/git",
                    Path("/tmp/repo"),
                    {"final_revision": "a" * 40},
                )
            )
            self.assertFalse(
                MODULE.manifest_matches_current_repo(
                    "/usr/bin/git",
                    Path("/tmp/repo"),
                    {"final_revision": "b" * 40},
                )
            )
        with self.assertRaisesRegex(RuntimeError, "valid final revision"):
            MODULE.manifest_matches_current_repo(
                "/usr/bin/git",
                Path("/tmp/repo"),
                {"final_revision": "main"},
            )

    def test_host_usage_attestation_is_chain_bound_and_repo_relative(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            baseline = repo / ".tmp/run-coordinator/usage-chain-1.json"
            baseline.parent.mkdir(parents=True)
            baseline.write_text("{}\n", encoding="utf-8")
            status = repo / ".tmp/run-coordinator/chain-1/usage-status.json"
            config = {
                "usage": {
                    "hardReservePercent": 15,
                    "softRunTargetPercent": 10,
                    "monitorIntervalSeconds": 60,
                    "snapshotMaxAgeSeconds": 120,
                }
            }
            value = MODULE.write_usage_attestation(
                status,
                repo=repo,
                chain_id="chain-1",
                invocation_id="chain-1-invocation",
                baseline_path=baseline,
                gate={
                    "status": "pass",
                    "checkedAtUtc": "2026-07-24T15:00:00+00:00",
                    "lowestRemainingPercent": 99,
                },
                config=config,
            )
            self.assertEqual(value["source"], "approved-host-dispatcher")
            self.assertEqual(value["chain_id"], "chain-1")
            self.assertFalse(Path(value["baseline_path"]).is_absolute())
            self.assertEqual(json.loads(status.read_text()), value)

    def test_preserved_inputs_are_independently_rehashed(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            artifact = repo / ".tmp/artifact"
            inputs = artifact / "inputs"
            inputs.mkdir(parents=True)
            queue_inputs = {}
            filenames = {
                "integrity": "integrity.json",
                "progress": "progress.json",
                "intake": "intake.json",
                "review_epoch": "review-epoch.json",
                "chain": "chain.json",
            }
            for name, filename in filenames.items():
                path = inputs / filename
                path.write_text(json.dumps({"name": name}) + "\n", encoding="utf-8")
                queue_inputs[name] = {
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest()
                }
            manifest = artifact / "run-chain.json"
            manifest.write_text("{}\n", encoding="utf-8")
            queue = repo / ".tmp/queue.json"
            queue.write_text(json.dumps({"inputs": queue_inputs}), encoding="utf-8")
            verified = MODULE.materialize_verified_inputs(
                {"manifest": {"dataBranch": "unused"}, "repository": "unused/unused"},
                repo=repo,
                manifest_path=manifest,
                queue_path=queue,
                destination=repo / ".tmp/local-inputs",
            )
            self.assertEqual(set(verified), set(queue_inputs))
            self.assertTrue(
                all(not Path(item["path"]).is_absolute() for item in verified.values())
            )

    def test_elim_runtime_failure_is_projected_to_local_console_state(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            config = {"manifest": {"localFallback": ".tmp/run-chain.json"}}
            control = {"last_failed_reason": "Review Epoch was not recorded."}
            payload = {"chain_id": "chain-1", "status": "complete"}
            MODULE.record_elim_runtime(
                repo=repo,
                config=config,
                control=control,
                payload=payload,
                outcome=4,
            )
            self.assertEqual(control["elim_runtime"]["status"], "failed")
            projected = json.loads(
                (repo / ".tmp/run-chain.json").read_text(encoding="utf-8")
            )
            self.assertEqual(projected["elim_runtime"]["id"], "elim")
            self.assertIn("Review Epoch", projected["elim_runtime"]["details"])

    def test_nonpassing_final_usage_attestation_prevents_success(self):
        self.assertEqual(
            MODULE.enforce_usage_monitor_closeout(0, {"status": "abort"}),
            5,
        )
        self.assertEqual(
            MODULE.enforce_usage_monitor_closeout(0, {"status": "unavailable"}),
            5,
        )
        self.assertEqual(
            MODULE.enforce_usage_monitor_closeout(0, {"status": "pass"}),
            0,
        )
        self.assertEqual(
            MODULE.enforce_usage_monitor_closeout(4, {"status": "pass"}),
            4,
        )

    def test_monitor_probe_converts_host_read_error_to_unavailable(self):
        result = MODULE.monitored_usage_probe(
            lambda: (_ for _ in ()).throw(RuntimeError("meter unavailable"))
        )
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("meter unavailable", result["error"])


if __name__ == "__main__":
    unittest.main()
