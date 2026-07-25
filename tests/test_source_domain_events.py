import argparse
import base64
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import publish_immutable_data_file as publisher
from scripts import source_domain_events as events
from scripts import audit_project_consistency as consistency


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, cwd: Path) -> str:
    return subprocess.check_output(
        list(args), cwd=cwd, text=True, stderr=subprocess.STDOUT
    ).strip()


class TemporaryRepository:
    def __init__(
        self,
        root: Path,
        *,
        agent: str = "presidential-directives-bot",
        changed_path: str = "inventory/presidential-directives.csv",
        base_text: str = "Directive ID,Title\n2025-00001,Existing\n",
        changed_text: str = (
            "Directive ID,Title\n"
            "2025-00001,Existing\n"
            "2025-01900,New directive\n"
        ),
    ):
        self.root = root
        self.agent = agent
        self.changed_path = changed_path
        run("git", "init", "-b", "main", cwd=root)
        run("git", "config", "user.name", "Source Event Test", cwd=root)
        run("git", "config", "user.email", "source-event@example.test", cwd=root)
        for log in (
            "framework/logs/SOURCE_MONITOR_LOG.md",
            "framework/logs/AGENT_AUDIT_LOG.md",
        ):
            path = root / log
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {path.stem}\n", encoding="utf-8")
        trusted = root / "scripts/trusted-helper.py"
        trusted.parent.mkdir(parents=True, exist_ok=True)
        trusted.write_text("print('trusted')\n", encoding="utf-8")
        target = root / changed_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(base_text, encoding="utf-8")
        run("git", "add", ".", cwd=root)
        run("git", "commit", "-m", "baseline", cwd=root)
        self.base_revision = run("git", "rev-parse", "HEAD", cwd=root)
        self.branch = str(events.AGENTS[agent]["branch"])
        run("git", "checkout", "-b", self.branch, cwd=root)
        target.write_text(changed_text, encoding="utf-8")
        run("git", "add", changed_path, cwd=root)
        run("git", "commit", "-m", "proposal", cwd=root)
        self.proposal_revision = run("git", "rev-parse", "HEAD", cwd=root)

    def proposed_event(self, report: dict, number: int = 88) -> dict:
        report_path = self.root / "report.json"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        args = argparse.Namespace(
            repository="Thorncrag/ARRP",
            agent=self.agent,
            head_ref=self.branch,
            base_ref="main",
            git_base=self.base_revision,
            pull_request_number=number,
            pull_request_url=f"https://github.com/Thorncrag/ARRP/pull/{number}",
            report=report_path,
            chain_id="chain-2026-07-24",
            run_id="github-actions:Thorncrag/ARRP:12345",
            trigger="workflow_call",
        )
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            return events.build_proposed_event(args)
        finally:
            os.chdir(previous)

    def preserve_proposed(self, event: dict) -> tuple[bytes, str]:
        event_file = self.root / "proposed.json"
        encoded = events.write_json(event_file, event)
        run(
            "git",
            "checkout",
            "-b",
            "project-console-data",
            self.base_revision,
            cwd=self.root,
        )
        remote_path = events.data_path(event)
        target = self.root / remote_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(encoded)
        run("git", "add", remote_path, cwd=self.root)
        run("git", "commit", "-m", "preserve proposed event", cwd=self.root)
        run("git", "checkout", "main", cwd=self.root)
        run("git", "merge", "--no-ff", self.branch, "-m", "accept proposal", cwd=self.root)
        return encoded, run("git", "rev-parse", "HEAD", cwd=self.root)


class SourceDomainEventTests(unittest.TestCase):
    def test_proposed_event_is_versioned_minimized_and_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TemporaryRepository(Path(directory))
            report = {
                "schema_version": 2,
                "generated_at": "2026-07-24T00:00:00Z",
                "counts": {
                    "new": 1,
                    "changed": 0,
                    "unchanged": 2,
                    "not_seen": 0,
                    "discovered": 3,
                    "out_of_scope": 0,
                },
                "changes": [],
                "directives": [
                    {
                        "Directive ID": "2025-01900",
                        "Bot Status": "new",
                        "Title": "Sensitive title must not be copied",
                        "HTML URL": "https://example.test/private-looking-path",
                    }
                ],
            }
            first = repository.proposed_event(report)
            second = repository.proposed_event(
                {
                    **report,
                    "generated_at": "2026-07-24T00:01:00Z",
                    "counts": {
                        "new": 0,
                        "changed": 999,
                        "unchanged": 0,
                        "not_seen": 400,
                        "discovered": 0,
                        "out_of_scope": 800,
                    },
                    "changes": [],
                    "directives": [],
                }
            )
            self.assertEqual(first, second)
            self.assertEqual(first["schema_version"], 1)
            self.assertEqual(first["state"], "proposed")
            self.assertEqual(first["source_revision"], repository.base_revision)
            self.assertEqual(
                first["proposal"]["proposal_revision"],
                repository.proposal_revision,
            )
            self.assertEqual(
                first["affected_records"],
                [
                    {
                        "record_type": "presidential-directive",
                        "record_id": "2025-01900",
                    }
                ],
            )
            encoded = events.canonical_json(first)
            self.assertNotIn("Sensitive title", encoded)
            self.assertNotIn("example.test", encoded)
            events.validate_event(first, expected_state="proposed")
            amended = json.loads(json.dumps(first))
            amended["proposal"]["proposal_revision"] = "f" * 40
            self.assertNotEqual(
                events.expected_idempotency_key(first),
                events.expected_idempotency_key(amended),
            )

    def test_source_checker_event_excludes_urls_titles_and_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TemporaryRepository(
                Path(directory),
                agent="source-checker-bot",
                changed_path="framework/reports/SOURCE_CHECKER_REPORT.md",
                base_text="# Report\n\nNo exceptions.\n",
                changed_text="# Report\n\n| SRC-0007 | broken |\n",
            )
            report = {
                "schema_version": 1,
                "counts": {"broken": 1, "verified": 2},
                "results": [
                    {
                        "source_id": "SRC-0007",
                        "classification": "broken",
                        "title": "Private-looking title",
                        "final_url": "https://example.test/sensitive",
                        "error": "server response body",
                    }
                ],
            }
            event = repository.proposed_event(report)
            encoded = events.canonical_json(event)
            self.assertIn("SRC-0007", encoded)
            self.assertNotIn("Private-looking", encoded)
            self.assertNotIn("example.test", encoded)
            self.assertNotIn("response body", encoded)
            self.assertEqual(
                event["summary"]["counts"],
                {
                    "affected-files": 1,
                    "affected-records": 1,
                    "source-records": 1,
                },
            )

    def test_existing_pending_delta_supplies_affected_record_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TemporaryRepository(Path(directory))
            event = repository.proposed_event(
                {
                    "counts": {"new": 0, "changed": 0},
                    "changes": [],
                    "directives": [],
                }
            )
            self.assertEqual(
                event["affected_records"][0]["record_id"], "2025-01900"
            )

    def test_human_merge_acceptance_and_exact_once_log_rendering(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TemporaryRepository(Path(directory))
            event = repository.proposed_event(
                {
                    "counts": {"new": 1, "changed": 0},
                    "changes": [],
                    "directives": [
                        {"Directive ID": "2025-01900", "Bot Status": "new"}
                    ],
                }
            )
            encoded, merge_commit = repository.preserve_proposed(event)
            body = repository.root / "pr-body.md"
            body.write_text(
                events.attach_marker("Review this watcher update.", event, encoded),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                merged="true",
                repository="Thorncrag/ARRP",
                base_ref="main",
                head_ref=repository.branch,
                pull_request_number=88,
                pull_request_url="https://github.com/Thorncrag/ARRP/pull/88",
                pr_head_revision=repository.proposal_revision,
                merged_at="2026-07-24T22:00:00Z",
                merged_by="Thorncrag",
                merged_by_type="User",
                merge_commit=merge_commit,
                pr_body_file=body,
                data_ref="project-console-data",
            )
            previous = Path.cwd()
            try:
                os.chdir(repository.root)
                accepted = events.accept_event(args)
                changed = events.render_event(
                    accepted,
                    Path("framework/logs/SOURCE_MONITOR_LOG.md"),
                    Path("framework/logs/AGENT_AUDIT_LOG.md"),
                )
                unchanged = events.render_event(
                    accepted,
                    Path("framework/logs/SOURCE_MONITOR_LOG.md"),
                    Path("framework/logs/AGENT_AUDIT_LOG.md"),
                )
            finally:
                os.chdir(previous)
            self.assertEqual(accepted["state"], "accepted")
            self.assertEqual(accepted["event_id"], event["event_id"])
            self.assertEqual(
                accepted["acceptance"]["boundary"], "human-pull-request-merge"
            )
            self.assertTrue(changed)
            self.assertFalse(unchanged)
            for relative in (
                "framework/logs/SOURCE_MONITOR_LOG.md",
                "framework/logs/AGENT_AUDIT_LOG.md",
            ):
                text = (repository.root / relative).read_text(encoding="utf-8")
                marker_suffix = (
                    "agent-audit" if "AGENT_AUDIT" in relative else "source-monitor"
                )
                marker = (
                    f"<!-- ARRP_SOURCE_DOMAIN_EVENT:{event['event_id']}:"
                    f"{marker_suffix} -->"
                )
                self.assertEqual(text.count(marker), 1)

    def test_acceptance_fails_for_bot_merge_changed_head_and_changed_output(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TemporaryRepository(Path(directory))
            event = repository.proposed_event(
                {
                    "counts": {"new": 1},
                    "changes": [],
                    "directives": [
                        {"Directive ID": "2025-01900", "Bot Status": "new"}
                    ],
                }
            )
            encoded, merge_commit = repository.preserve_proposed(event)
            body = repository.root / "pr-body.md"
            body.write_text(events.attach_marker("Body", event, encoded), encoding="utf-8")
            base = dict(
                merged="true",
                repository="Thorncrag/ARRP",
                base_ref="main",
                head_ref=repository.branch,
                pull_request_number=88,
                pull_request_url="https://github.com/Thorncrag/ARRP/pull/88",
                pr_head_revision=repository.proposal_revision,
                merged_at="2026-07-24T22:00:00Z",
                merged_by="Thorncrag",
                merged_by_type="User",
                merge_commit=merge_commit,
                pr_body_file=body,
                data_ref="project-console-data",
            )
            previous = Path.cwd()
            try:
                os.chdir(repository.root)
                with self.assertRaises(events.EventError):
                    events.accept_event(
                        argparse.Namespace(
                            **{**base, "merged_by": "github-actions[bot]", "merged_by_type": "Bot"}
                        )
                    )
                with self.assertRaises(events.EventError):
                    events.accept_event(
                        argparse.Namespace(**{**base, "merged_by": "other-maintainer"})
                    )
                with self.assertRaises(events.EventError):
                    events.accept_event(
                        argparse.Namespace(
                            **{**base, "pr_head_revision": repository.base_revision}
                        )
                    )
                target = repository.root / repository.changed_path
                target.write_text("Directive ID,Title\n2025-01900,Tampered\n")
                run("git", "add", repository.changed_path, cwd=repository.root)
                run("git", "commit", "-m", "tamper after merge", cwd=repository.root)
                tampered = run("git", "rev-parse", "HEAD", cwd=repository.root)
                with self.assertRaises(events.EventError):
                    events.accept_event(
                        argparse.Namespace(**{**base, "merge_commit": tampered})
                    )
            finally:
                os.chdir(previous)

    def test_acceptance_rejects_unrepresented_merge_result_path(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TemporaryRepository(Path(directory))
            event = repository.proposed_event(
                {
                    "counts": {"new": 1},
                    "changes": [],
                    "directives": [
                        {"Directive ID": "2025-01900", "Bot Status": "new"}
                    ],
                }
            )
            encoded, _merge_commit = repository.preserve_proposed(event)
            extra = repository.root / "inventory/sources.csv"
            extra.parent.mkdir(parents=True, exist_ok=True)
            extra.write_text("Source ID,Title\nSRC-0001,Unexpected\n", encoding="utf-8")
            run("git", "add", "inventory/sources.csv", cwd=repository.root)
            run("git", "commit", "--amend", "--no-edit", cwd=repository.root)
            merge_commit = run("git", "rev-parse", "HEAD", cwd=repository.root)
            body = repository.root / "pr-body.md"
            body.write_text(
                events.attach_marker("Body", event, encoded),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                merged="true",
                repository="Thorncrag/ARRP",
                base_ref="main",
                head_ref=repository.branch,
                pull_request_number=88,
                pull_request_url="https://github.com/Thorncrag/ARRP/pull/88",
                pr_head_revision=repository.proposal_revision,
                merged_at="2026-07-24T22:00:00Z",
                merged_by="Thorncrag",
                merged_by_type="User",
                merge_commit=merge_commit,
                pr_body_file=body,
                data_ref="project-console-data",
            )
            previous = Path.cwd()
            try:
                os.chdir(repository.root)
                with self.assertRaisesRegex(
                    events.EventError,
                    "non-modification path status|affected-file set",
                ):
                    events.accept_event(args)
            finally:
                os.chdir(previous)

    def test_acceptance_rejects_tampered_proposal_delta_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TemporaryRepository(Path(directory))
            event = repository.proposed_event(
                {
                    "counts": {"new": 1},
                    "changes": [],
                    "directives": [
                        {"Directive ID": "2025-01900", "Bot Status": "new"}
                    ],
                }
            )
            event["output_hashes"]["proposal_diff"] = "sha256:" + ("0" * 64)
            event["idempotency_key"] = events.expected_idempotency_key(event)
            event["event_id"] = events.event_id_for(event["idempotency_key"])
            events.validate_event(event, expected_state="proposed")
            encoded, merge_commit = repository.preserve_proposed(event)
            body = repository.root / "pr-body.md"
            body.write_text(
                events.attach_marker("Body", event, encoded),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                merged="true",
                repository="Thorncrag/ARRP",
                base_ref="main",
                head_ref=repository.branch,
                pull_request_number=88,
                pull_request_url="https://github.com/Thorncrag/ARRP/pull/88",
                pr_head_revision=repository.proposal_revision,
                merged_at="2026-07-24T22:00:00Z",
                merged_by="Thorncrag",
                merged_by_type="User",
                merge_commit=merge_commit,
                pr_body_file=body,
                data_ref="project-console-data",
            )
            previous = Path.cwd()
            try:
                os.chdir(repository.root)
                with self.assertRaisesRegex(events.EventError, "delta hash"):
                    events.accept_event(args)
            finally:
                os.chdir(previous)

    def test_acceptance_rejects_semantics_not_reproducible_from_delta(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TemporaryRepository(Path(directory))
            event = repository.proposed_event(
                {
                    "counts": {"new": 1},
                    "changes": [],
                    "directives": [
                        {"Directive ID": "2025-01900", "Bot Status": "new"}
                    ],
                }
            )
            event["affected_records"] = []
            event["summary"] = {
                "status": "presidential directives proposal delta",
                "affected_record_count": 0,
                "counts": {"affected-files": 1, "affected-records": 0},
            }
            event["output_hashes"]["semantic_report"] = events.hash_json(
                {
                    "affected_records": event["affected_records"],
                    "summary": event["summary"],
                }
            )
            event["idempotency_key"] = events.expected_idempotency_key(event)
            event["event_id"] = events.event_id_for(event["idempotency_key"])
            events.validate_event(event, expected_state="proposed")
            encoded, merge_commit = repository.preserve_proposed(event)
            body = repository.root / "pr-body.md"
            body.write_text(
                events.attach_marker("Body", event, encoded),
                encoding="utf-8",
            )
            args = argparse.Namespace(
                merged="true",
                repository="Thorncrag/ARRP",
                base_ref="main",
                head_ref=repository.branch,
                pull_request_number=88,
                pull_request_url="https://github.com/Thorncrag/ARRP/pull/88",
                pr_head_revision=repository.proposal_revision,
                merged_at="2026-07-24T22:00:00Z",
                merged_by="Thorncrag",
                merged_by_type="User",
                merge_commit=merge_commit,
                pr_body_file=body,
                data_ref="project-console-data",
            )
            previous = Path.cwd()
            try:
                os.chdir(repository.root)
                with self.assertRaisesRegex(
                    events.EventError, "semantic projection"
                ):
                    events.accept_event(args)
            finally:
                os.chdir(previous)

    def test_marker_replacement_retains_exactly_one_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TemporaryRepository(Path(directory))
            event = repository.proposed_event(
                {
                    "counts": {"new": 1},
                    "changes": [],
                    "directives": [
                        {"Directive ID": "2025-01900", "Bot Status": "new"}
                    ],
                }
            )
            path = repository.root / "event.json"
            encoded = events.write_json(path, event)
            first = events.attach_marker("Pull request body", event, encoded)
            second = events.attach_marker(first, event, encoded)
            self.assertEqual(len(events.MARKER_RE.findall(second)), 1)
            payload = events.marker_payload(second)
            self.assertEqual(payload["event_id"], event["event_id"])

    def test_unrepresented_deletion_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TemporaryRepository(Path(directory))
            (repository.root / "scripts/trusted-helper.py").unlink()
            run("git", "add", "-u", cwd=repository.root)
            run("git", "commit", "-m", "malicious deletion", cwd=repository.root)
            with self.assertRaisesRegex(
                events.EventError, "non-modification path status"
            ):
                repository.proposed_event(
                    {
                        "counts": {"new": 1},
                        "changes": [],
                        "directives": [
                            {"Directive ID": "2025-01900", "Bot Status": "new"}
                        ],
                    }
                )

    def test_runtime_identifiers_cannot_inject_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TemporaryRepository(Path(directory))
            event = repository.proposed_event(
                {
                    "counts": {"new": 1},
                    "changes": [],
                    "directives": [
                        {"Directive ID": "2025-01900", "Bot Status": "new"}
                    ],
                }
            )
            for field, value in (
                ("chain_id", "chain\n| Injected |"),
                ("run_id", "run`bad"),
                ("trigger", "workflow call"),
            ):
                altered = dict(event)
                altered[field] = value
                with self.assertRaisesRegex(events.EventError, f"invalid event {field}"):
                    events.validate_event(altered)

    def test_preexisting_log_branch_must_equal_fresh_render(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            TemporaryRepository(root)
            run("git", "checkout", "main", cwd=root)
            source_log = root / "framework/logs/SOURCE_MONITOR_LOG.md"
            agent_log = root / "framework/logs/AGENT_AUDIT_LOG.md"
            run("git", "checkout", "-b", "event-log", cwd=root)
            source_log.write_text(
                "# SOURCE_MONITOR_LOG\n\nUnrelated edit.\n",
                encoding="utf-8",
            )
            agent_log.write_text(
                "# AGENT_AUDIT_LOG\n\nUnrelated edit.\n",
                encoding="utf-8",
            )
            run(
                "git",
                "add",
                str(source_log.relative_to(root)),
                str(agent_log.relative_to(root)),
                cwd=root,
            )
            run("git", "commit", "-m", "hostile pre-existing log branch", cwd=root)
            run("git", "checkout", "main", cwd=root)
            source_log.write_text(
                "# SOURCE_MONITOR_LOG\n\nExpected render.\n",
                encoding="utf-8",
            )
            agent_log.write_text(
                "# AGENT_AUDIT_LOG\n\nExpected render.\n",
                encoding="utf-8",
            )
            previous = Path.cwd()
            try:
                os.chdir(root)
                with self.assertRaisesRegex(
                    events.EventError, "differs from the fresh render"
                ):
                    events.verify_existing_log_branch(
                        base_ref="main",
                        branch_ref="event-log",
                        source_log=Path("framework/logs/SOURCE_MONITOR_LOG.md"),
                        agent_log=Path("framework/logs/AGENT_AUDIT_LOG.md"),
                    )
            finally:
                os.chdir(previous)


class ImmutablePublisherTests(unittest.TestCase):
    def valid_event_file(self, directory: str) -> tuple[Path, dict]:
        repository = TemporaryRepository(Path(directory))
        event = repository.proposed_event(
            {
                "counts": {"new": 1},
                "changes": [],
                "directives": [
                    {"Directive ID": "2025-01900", "Bot Status": "new"}
                ],
            }
        )
        path = Path(directory) / "event.json"
        events.write_json(path, event)
        return path, event

    def test_identical_existing_event_is_noop(self):
        with tempfile.TemporaryDirectory() as directory:
            path, event = self.valid_event_file(directory)
            existing = {
                "type": "file",
                "encoding": "base64",
                "content": base64.b64encode(path.read_bytes()).decode("ascii"),
            }
            with patch.object(publisher, "api_request", return_value=existing) as request:
                result = publisher.publish(
                    repository="Thorncrag/ARRP",
                    branch="project-console-data",
                    local_file=path,
                    remote_path=events.data_path(event),
                    token="test-token",
                )
            self.assertEqual(result, "unchanged")
            self.assertEqual(request.call_count, 1)

    def test_existing_different_event_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path, event = self.valid_event_file(directory)
            existing = {
                "type": "file",
                "encoding": "base64",
                "content": base64.b64encode(b"{}").decode("ascii"),
            }
            with patch.object(publisher, "api_request", return_value=existing):
                with self.assertRaises(publisher.PublishError):
                    publisher.publish(
                        repository="Thorncrag/ARRP",
                        branch="project-console-data",
                        local_file=path,
                        remote_path=events.data_path(event),
                        token="test-token",
                    )

    def test_new_event_is_created_without_update_or_force(self):
        with tempfile.TemporaryDirectory() as directory:
            path, event = self.valid_event_file(directory)
            responses = [None, {"content": {"sha": "created"}}]
            with patch.object(publisher, "api_request", side_effect=responses) as request:
                result = publisher.publish(
                    repository="Thorncrag/ARRP",
                    branch="project-console-data",
                    local_file=path,
                    remote_path=events.data_path(event),
                    token="test-token",
                )
            self.assertEqual(result, "created")
            self.assertEqual(request.call_args_list[1].args[1], "PUT")
            payload = request.call_args_list[1].args[3]
            self.assertNotIn("sha", payload)
            self.assertEqual(payload["branch"], "project-console-data")


class SourceDomainWorkflowContractTests(unittest.TestCase):
    def test_watcher_workflows_expose_and_retain_events_without_artifact_collisions(self):
        paths = (
            ".github/workflows/case-monitor-bot.yml",
            ".github/workflows/presidential-directives-bot.yml",
            ".github/workflows/source-checker-bot.yml",
        )
        for relative in paths:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("domain_event_json", text, relative)
            self.assertIn("publish_immutable_data_file.py", text, relative)
            self.assertIn("attach-marker", text, relative)
            self.assertIn("attempt_key", text, relative)
            self.assertIn(
                "${{ steps.invocation.outputs.attempt_key }}-${{ github.run_attempt }}",
                text,
                relative,
            )
            self.assertIn("CHAIN_ID: ${{ inputs.chain_id }}", text, relative)
            self.assertIn('--chain-id "${CHAIN_ID}"', text, relative)
            self.assertIn("${GITHUB_RUN_ATTEMPT}", text, relative)
            self.assertNotIn('--chain-id "${{ inputs.chain_id }}"', text, relative)
            self.assertNotIn("\n          name: source-checker-report\n", text)
            self.assertNotIn("\n          name: case-monitor-report\n", text)
            self.assertNotIn("\n          name: presidential-directives-report\n", text)

    def test_case_monitor_counts_only_new_lead_deltas(self):
        workflow = (
            ROOT / ".github/workflows/case-monitor-bot.yml"
        ).read_text(encoding="utf-8")
        self.assertIn('len(item.get("added_lead_ids") or [])', workflow)
        self.assertNotIn('len(item.get("leads") or [])', workflow)

    def test_acceptance_workflow_has_all_fail_closed_boundaries(self):
        workflow = (
            ROOT / ".github/workflows/source-domain-event-acceptance.yml"
        ).read_text(encoding="utf-8")
        for required in (
            "pull_request.merged == true",
            "pull_request.base.ref == 'main'",
            "pull_request.head.repo.full_name == github.repository",
            "pull_request.merged_by.type == 'User'",
            "pull_request.merged_by.login == 'Thorncrag'",
            "--pr-head-revision",
            "--merge-commit",
            "publish_immutable_data_file.py",
            'trusted-source-domain-events.py" render',
            "framework/logs/SOURCE_MONITOR_LOG.md",
            "framework/logs/AGENT_AUDIT_LOG.md",
            "Prove the accepted pull request contains only watcher-owned data",
            'git diff --name-status "${BASE_SHA}...${HEAD_SHA}"',
            "Accepted merge changed trusted execution code",
            "trusted-source-domain-events.py",
            "verify-log-branch",
        ):
            self.assertIn(required, workflow)
        self.assertNotIn("gh pr merge", workflow)
        self.assertNotIn("git push origin main", workflow)
        self.assertNotIn("git push --set-upstream origin main", workflow)

    def test_checked_in_schema_is_version_one_and_closed(self):
        schema = json.loads(
            (ROOT / ".github/source-domain-event.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertEqual(
            schema["properties"]["acceptance"]["oneOf"][1]["properties"]["boundary"][
                "const"
            ],
            "human-pull-request-merge",
        )
        for field in ("chain_id", "run_id", "trigger"):
            self.assertEqual(
                schema["properties"][field]["pattern"],
                "^[A-Za-z0-9][A-Za-z0-9_.:/-]*$",
            )

    def test_live_project_integrity_contract_is_connected(self):
        self.assertEqual(consistency.source_domain_event_pipeline_findings(), [])

    def test_live_project_integrity_detects_removed_human_merge_gate(self):
        critical = (
            ".github/source-domain-event.schema.json",
            ".github/workflows/source-domain-event-acceptance.yml",
            ".github/workflows/case-monitor-bot.yml",
            ".github/workflows/presidential-directives-bot.yml",
            ".github/workflows/source-checker-bot.yml",
            "scripts/source_domain_events.py",
            "scripts/publish_immutable_data_file.py",
            "framework/agents/CASE_MONITOR_BOT.md",
            "framework/agents/PRESIDENTIAL_DIRECTIVES_BOT.md",
            "framework/agents/SOURCE_CHECKER_BOT.md",
        )
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            for relative in critical:
                target = temporary / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
            workflow = temporary / ".github/workflows/source-domain-event-acceptance.yml"
            workflow.write_text(
                workflow.read_text(encoding="utf-8").replace(
                    "pull_request.merged_by.type == 'User'",
                    "pull_request.merged_by.type != ''",
                ),
                encoding="utf-8",
            )
            findings = consistency.source_domain_event_pipeline_findings(temporary)
        self.assertTrue(
            any("merged_by.type == 'User'" in finding for finding in findings),
            findings,
        )


if __name__ == "__main__":
    unittest.main()
