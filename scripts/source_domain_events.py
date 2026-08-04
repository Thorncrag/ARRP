#!/usr/bin/env python3
"""Create, verify, accept, and render minimized local source-domain events.

The proposed event is an immutable projection of one deterministic watcher
delta in the coordinator-owned nightly branch. Acceptance is a separate state
transition and is permitted only after the exact proposal revision is merged
by a GitHub ``User``. This utility has no branch creation, push, merge,
credential, scheduler, or data-branch authority.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SCHEMA_URI = "framework/project/automation/schemas/source-domain-event.schema.json"
KIND = "source-domain-event"
HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
REVISION_RE = re.compile(r"^[a-f0-9]{40}$")
EVENT_ID_RE = re.compile(r"^SDE-[A-F0-9]{24}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
RUNTIME_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]*$")
STATUS_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _./:-]*$")
AUTHORIZED_ACCEPTORS = {"Thorncrag"}
ISO_TIME_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)
MARKER_RE = re.compile(r"<!-- ARRP_SOURCE_DOMAIN_EVENT (\{[^\r\n]*\}) -->")
SUMMARY_RE = re.compile(
    r"\n*<!-- ARRP_SOURCE_DOMAIN_SUMMARY_START -->.*?"
    r"<!-- ARRP_SOURCE_DOMAIN_SUMMARY_END -->\n*",
    re.DOTALL,
)
SOURCE_ID_RE = re.compile(r"^SRC-[0-9]{4,}$")
PROJECT_RECORD_RE = re.compile(r"^(?:HOR|[A-Z]+)-[0-9]{3}$")
NIGHTLY_BRANCH_RE = re.compile(r"^automation/nightly-[0-9]{8}T[0-9]{6}Z$")

AGENTS: dict[str, dict[str, Any]] = {
    "case-monitor-bot": {
        "display": "Case Monitor Bot",
        "allowed_paths": [
            re.compile(r"^inventory/sources(?:-pending)?\.csv$"),
            re.compile(
                r"^research/candidate-source-development/HOR-[0-9]{3}-source-development\.md$"
            ),
            re.compile(
                r"^areas/[A-Z]+/research/[A-Z]+-[0-9]{3}-source-development\.md$"
            ),
        ],
    },
    "presidential-directives-bot": {
        "display": "Presidential Directives Bot",
        "allowed_paths": [
            re.compile(r"^inventory/presidential-directives\.csv$"),
        ],
    },
    "source-checker-bot": {
        "display": "Source Checker Bot",
        "allowed_paths": [
            re.compile(r"^framework/status/sources/source-checker-report\.md$"),
        ],
    },
}

class EventError(ValueError):
    """A fail-closed source-domain-event validation error."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def hash_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def hash_json(value: Any) -> str:
    return hash_bytes(canonical_json(value).encode("utf-8"))


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise EventError(f"{path} must contain one JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> bytes:
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(encoded) > 262_144:
        raise EventError("source-domain event exceeds the 256 KiB safety ceiling")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    return encoded


def git(*arguments: str, binary: bool = False, check: bool = True) -> str | bytes:
    completed = subprocess.run(
        ["git", *arguments],
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout if binary else completed.stdout.decode("utf-8").strip()


def resolve_revision(ref: str) -> str:
    revision = str(git("rev-parse", "--verify", f"{ref}^{{commit}}"))
    if not REVISION_RE.fullmatch(revision):
        raise EventError(f"invalid Git revision resolved for {ref!r}")
    return revision


def is_ancestor(ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def validate_repository(repository: str) -> None:
    if not REPOSITORY_RE.fullmatch(repository):
        raise EventError("repository must use the owner/name form")


def validate_branch(agent_id: str, branch: str) -> None:
    if agent_id not in AGENTS:
        raise EventError(f"unknown source-domain agent: {agent_id}")
    if not NIGHTLY_BRANCH_RE.fullmatch(branch):
        raise EventError(
            f"{agent_id} proposal must use the coordinator-owned nightly "
            f"branch pattern, not {branch!r}"
        )


def path_is_allowed(agent_id: str, path: str) -> bool:
    if path.startswith("/") or ".." in Path(path).parts or "\\" in path:
        return False
    return any(pattern.fullmatch(path) for pattern in AGENTS[agent_id]["allowed_paths"])


def exact_modified_paths(
    agent_id: str,
    base_revision: str,
    head_revision: str,
    *,
    merge_base: bool,
) -> list[str]:
    """Return the complete ordinary-file modification set for one reviewed delta."""
    revision_range = (
        f"{base_revision}...{head_revision}"
        if merge_base
        else f"{base_revision}..{head_revision}"
    )
    try:
        status_text = str(
            git(
                "diff",
                "--name-status",
                revision_range,
                "--",
            )
        )
    except subprocess.CalledProcessError as exc:
        raise EventError("could not inspect the complete source-domain delta") from exc
    paths: list[str] = []
    invalid_statuses: list[str] = []
    for line in status_text.splitlines():
        if not line:
            continue
        fields = line.split("\t")
        status = fields[0]
        # All watcher-owned outputs already exist. Reject additions,
        # deletions, renames, copies, type changes, and unknown statuses so a
        # second unrepresented path can never ride beside an allowed update.
        if status != "M" or len(fields) != 2:
            invalid_statuses.append(line)
            continue
        paths.append(fields[1])
    if invalid_statuses:
        raise EventError(
            "proposal contains a non-modification path status: "
            + ", ".join(invalid_statuses)
        )
    if not paths:
        raise EventError("a source-domain event requires a nonempty reviewed delta")
    if len(paths) > 300:
        raise EventError("source-domain delta changes more than 300 files")
    unexpected = [path for path in paths if not path_is_allowed(agent_id, path)]
    if unexpected:
        raise EventError(
            f"source-domain delta contains paths outside the watcher boundary: {unexpected}"
        )
    for path in paths:
        base_tree = str(git("ls-tree", base_revision, "--", path))
        head_tree = str(git("ls-tree", head_revision, "--", path))
        if not base_tree.startswith("100644 blob ") or not head_tree.startswith(
            "100644 blob "
        ):
            raise EventError(
                f"watcher outputs must remain ordinary non-executable files: {path}"
            )
    return paths


def proposal_outputs(
    agent_id: str, base_ref: str
) -> tuple[str, str, list[dict[str, Any]], bytes]:
    source_revision = resolve_revision(base_ref)
    proposal_revision = resolve_revision("HEAD")
    paths = exact_modified_paths(
        agent_id,
        source_revision,
        proposal_revision,
        merge_base=True,
    )
    files: list[dict[str, Any]] = []
    for path in paths:
        content = bytes(git("show", f"{proposal_revision}:{path}", binary=True))
        if len(content) > 20_000_000:
            raise EventError(f"proposal output exceeds 20 MB: {path}")
        files.append({"path": path, "sha256": hash_bytes(content), "bytes": len(content)})
    patch = bytes(
        git(
            "diff",
            "--binary",
            f"{source_revision}...{proposal_revision}",
            "--",
            *paths,
            binary=True,
        )
    )
    return source_revision, proposal_revision, files, patch


def records_from_proposal_delta(
    agent_id: str, paths: list[str], patch: bytes
) -> list[dict[str, str]]:
    """Recover stable record IDs from the complete pending branch delta.

    This supplements the current run report when an existing watcher pull
    request contains unresolved changes from an earlier run.
    """

    text = patch.decode("utf-8", errors="replace")
    changed_lines = "\n".join(
        line[1:]
        for line in text.splitlines()
        if line.startswith(("+", "-"))
        and not line.startswith(("+++", "---"))
    )
    records: list[dict[str, str]] = []
    if agent_id in {"case-monitor-bot", "source-checker-bot"}:
        for source_id in sorted(set(re.findall(r"\bSRC-[0-9]{4,}\b", changed_lines))):
            candidate = record("source", source_id)
            if candidate:
                records.append(candidate)
    if agent_id == "case-monitor-bot":
        for path in paths:
            match = re.search(r"/((?:HOR|[A-Z]+)-[0-9]{3})-source-development\.md$", path)
            if not match:
                continue
            record_id = match.group(1)
            record_type = "candidate" if record_id.startswith("HOR-") else "issue"
            candidate = record(record_type, record_id)
            if candidate:
                records.append(candidate)
    if agent_id == "presidential-directives-bot":
        for line in changed_lines.splitlines():
            first_cell = line.split(",", 1)[0].strip().strip('"')
            candidate = record("presidential-directive", first_cell)
            if candidate:
                records.append(candidate)
    return records


def delta_semantic_projection(
    agent_id: str,
    paths: list[str],
    patch: bytes,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Describe only semantic facts reproducible from the reviewed Git delta."""
    records = records_from_proposal_delta(agent_id, paths, patch)
    unique_records = {
        (item["record_type"], item["record_id"]): item for item in records
    }
    records = [unique_records[key] for key in sorted(unique_records)]
    if len(records) > 5000:
        raise EventError("source-domain event affects more than 5,000 records")
    type_counts: dict[str, int] = {}
    for item in records:
        key = f"{item['record_type']}-records"
        type_counts[key] = type_counts.get(key, 0) + 1
    counts = {
        "affected-files": len(paths),
        "affected-records": len(records),
        **type_counts,
    }
    status_by_agent = {
        "case-monitor-bot": "case monitor proposal delta",
        "presidential-directives-bot": "presidential directives proposal delta",
        "source-checker-bot": "source checker proposal delta",
    }
    return records, {
        "status": status_by_agent[agent_id],
        "affected_record_count": len(records),
        "counts": counts,
    }


def safe_counts(values: Any) -> dict[str, int]:
    if not isinstance(values, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw in sorted(values.items()):
        normalized = str(key).strip().lower().replace("_", "-")
        if not re.fullmatch(r"[a-z0-9][a-z0-9 -]{0,60}", normalized):
            continue
        if isinstance(raw, bool):
            continue
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if 0 <= value <= 10_000_000:
            result[normalized] = value
    return result


def record(record_type: str, record_id: str) -> dict[str, str] | None:
    record_id = str(record_id).strip()
    if record_type == "source" and SOURCE_ID_RE.fullmatch(record_id):
        return {"record_type": record_type, "record_id": record_id}
    if record_type in {"issue", "candidate"} and PROJECT_RECORD_RE.fullmatch(record_id):
        return {"record_type": record_type, "record_id": record_id}
    if record_type == "presidential-directive" and re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]{2,100}", record_id
    ):
        return {"record_type": record_type, "record_id": record_id}
    return None


def event_identity(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": event["schema_version"],
        "kind": event["kind"],
        "agent_id": event["agent_id"],
        "chain_id": event["chain_id"],
        "run_id": event["run_id"],
        "source_revision": event["source_revision"],
        "proposal": {
            "repository": event["proposal"]["repository"],
            "base_ref": event["proposal"]["base_ref"],
            "head_ref": event["proposal"]["head_ref"],
            "pull_request_number": event["proposal"]["pull_request_number"],
            "proposal_revision": event["proposal"]["proposal_revision"],
        },
        "semantic_report": event["output_hashes"]["semantic_report"],
        "proposal_diff": event["output_hashes"]["proposal_diff"],
    }


def expected_idempotency_key(event: dict[str, Any]) -> str:
    return hash_json(event_identity(event))


def event_id_for(key: str) -> str:
    if not HASH_RE.fullmatch(key):
        raise EventError("invalid event idempotency hash")
    return "SDE-" + key.removeprefix("sha256:")[:24].upper()


def validate_event(event: dict[str, Any], *, expected_state: str | None = None) -> None:
    required = {
        "schema_version",
        "schema_uri",
        "kind",
        "event_id",
        "idempotency_key",
        "state",
        "agent_id",
        "chain_id",
        "run_id",
        "trigger",
        "source_revision",
        "proposal",
        "output_hashes",
        "affected_records",
        "summary",
        "acceptance",
    }
    if set(event) != required:
        raise EventError(
            f"event fields do not match schema: missing={sorted(required - set(event))}, "
            f"extra={sorted(set(event) - required)}"
        )
    if event["schema_version"] != SCHEMA_VERSION or event["schema_uri"] != SCHEMA_URI:
        raise EventError("unsupported source-domain-event schema")
    if event["kind"] != KIND:
        raise EventError("invalid event kind")
    if event["state"] not in {"proposed", "accepted"}:
        raise EventError("invalid event state")
    if expected_state and event["state"] != expected_state:
        raise EventError(f"expected {expected_state} event, found {event['state']}")
    if event["agent_id"] not in AGENTS:
        raise EventError("invalid event agent")
    maximums = {"chain_id": 200, "run_id": 240, "trigger": 100}
    for field in ("chain_id", "run_id", "trigger"):
        value = event[field]
        if (
            not isinstance(value, str)
            or not RUNTIME_ID_RE.fullmatch(value)
            or len(value) > maximums[field]
        ):
            raise EventError(f"invalid event {field}")
    if not REVISION_RE.fullmatch(str(event["source_revision"])):
        raise EventError("invalid source revision")
    proposal = event["proposal"]
    if not isinstance(proposal, dict) or set(proposal) != {
        "repository",
        "base_ref",
        "head_ref",
        "pull_request_number",
        "pull_request_url",
        "proposal_revision",
    }:
        raise EventError("invalid event proposal")
    validate_repository(str(proposal["repository"]))
    if proposal["base_ref"] != "main":
        raise EventError("source-domain proposal base must be main")
    validate_branch(event["agent_id"], str(proposal["head_ref"]))
    if not isinstance(proposal["pull_request_number"], int) or proposal["pull_request_number"] < 1:
        raise EventError("invalid proposal pull-request number")
    expected_url = (
        f"https://github.com/{proposal['repository']}/pull/"
        f"{proposal['pull_request_number']}"
    )
    if proposal["pull_request_url"] != expected_url:
        raise EventError("proposal pull-request URL does not match repository and number")
    if not REVISION_RE.fullmatch(str(proposal["proposal_revision"])):
        raise EventError("invalid proposal revision")
    output_hashes = event["output_hashes"]
    if not isinstance(output_hashes, dict) or set(output_hashes) != {
        "semantic_report",
        "proposal_diff",
        "files",
    }:
        raise EventError("invalid event output hashes")
    if not HASH_RE.fullmatch(str(output_hashes["semantic_report"])):
        raise EventError("invalid semantic-report hash")
    if not HASH_RE.fullmatch(str(output_hashes["proposal_diff"])):
        raise EventError("invalid proposal-diff hash")
    files = output_hashes["files"]
    if not isinstance(files, list) or not files or len(files) > 300:
        raise EventError("event must identify 1-300 affected files")
    seen_paths: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "bytes"}:
            raise EventError("invalid affected-file record")
        path = str(item["path"])
        if path in seen_paths or not path_is_allowed(event["agent_id"], path):
            raise EventError(f"invalid or duplicated affected path: {path}")
        seen_paths.add(path)
        if not HASH_RE.fullmatch(str(item["sha256"])):
            raise EventError(f"invalid file hash for {path}")
        if not isinstance(item["bytes"], int) or not 0 <= item["bytes"] <= 20_000_000:
            raise EventError(f"invalid file size for {path}")
    affected_records = event["affected_records"]
    if not isinstance(affected_records, list) or len(affected_records) > 5000:
        raise EventError("invalid affected-record list")
    record_keys: set[tuple[str, str]] = set()
    for item in affected_records:
        if not isinstance(item, dict) or set(item) != {"record_type", "record_id"}:
            raise EventError("invalid affected-record entry")
        normalized = record(str(item["record_type"]), str(item["record_id"]))
        if normalized != item:
            raise EventError(f"invalid affected record: {item}")
        key = (item["record_type"], item["record_id"])
        if key in record_keys:
            raise EventError(f"duplicated affected record: {item}")
        record_keys.add(key)
    summary = event["summary"]
    if not isinstance(summary, dict) or set(summary) != {
        "status",
        "affected_record_count",
        "counts",
    }:
        raise EventError("invalid event summary")
    if (
        not isinstance(summary["status"], str)
        or not STATUS_RE.fullmatch(summary["status"])
        or len(summary["status"]) > 100
    ):
        raise EventError("invalid or unsafe event status")
    if summary["affected_record_count"] != len(affected_records):
        raise EventError("affected-record count does not match the record list")
    if safe_counts(summary["counts"]) != summary["counts"]:
        raise EventError("invalid or non-minimized event counts")
    semantic_projection_hash = hash_json(
        {"affected_records": affected_records, "summary": summary}
    )
    if output_hashes["semantic_report"] != semantic_projection_hash:
        raise EventError(
            "semantic-report hash does not match the delta-derived projection"
        )
    if event["state"] == "proposed":
        if event["acceptance"] is not None:
            raise EventError("proposed event may not contain acceptance data")
    else:
        acceptance = event["acceptance"]
        if not isinstance(acceptance, dict) or set(acceptance) != {
            "boundary",
            "pull_request_number",
            "pull_request_url",
            "merged_at",
            "merged_by",
            "merged_by_type",
            "merge_commit",
        }:
            raise EventError("accepted event lacks the exact acceptance record")
        if acceptance["boundary"] != "human-pull-request-merge":
            raise EventError("invalid acceptance boundary")
        if acceptance["merged_by_type"] != "User":
            raise EventError("acceptance was not performed by a GitHub User")
        if not ISO_TIME_RE.fullmatch(str(acceptance["merged_at"])):
            raise EventError("invalid acceptance timestamp")
        if not re.fullmatch(
            r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?",
            str(acceptance["merged_by"]),
        ):
            raise EventError("invalid accepting GitHub user")
        if not REVISION_RE.fullmatch(str(acceptance["merge_commit"])):
            raise EventError("invalid accepted merge commit")
        if acceptance["pull_request_number"] != proposal["pull_request_number"]:
            raise EventError("acceptance pull request does not match proposal")
        if acceptance["pull_request_url"] != proposal["pull_request_url"]:
            raise EventError("acceptance pull-request URL does not match proposal")
    key = expected_idempotency_key(event)
    if event["idempotency_key"] != key:
        raise EventError("event idempotency key does not match its identity fields")
    if event["event_id"] != event_id_for(key):
        raise EventError("event ID does not match its idempotency key")


def build_proposed_event(args: argparse.Namespace) -> dict[str, Any]:
    validate_repository(args.repository)
    validate_branch(args.agent, args.head_ref)
    if args.base_ref != "main":
        raise EventError("source-domain proposal base must be main")
    if args.pull_request_number < 1:
        raise EventError("pull-request number must be positive")
    expected_url = (
        f"https://github.com/{args.repository}/pull/{args.pull_request_number}"
    )
    if args.pull_request_url != expected_url:
        raise EventError("pull-request URL does not match repository and number")
    # The full watcher report remains available as a retained artifact/current
    # feed for review. The accepted event deliberately does not trust its
    # classifications or prose: only facts reproducible from Git are admitted.
    read_json(args.report)
    source_revision, proposal_revision, outputs, patch = proposal_outputs(
        args.agent, args.git_base
    )
    records, summary = delta_semantic_projection(
        args.agent,
        [item["path"] for item in outputs],
        patch,
    )
    chain_id = args.chain_id.strip() or f"standalone:{args.run_id}"
    event: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "schema_uri": SCHEMA_URI,
        "kind": KIND,
        "event_id": "",
        "idempotency_key": "",
        "state": "proposed",
        "agent_id": args.agent,
        "chain_id": chain_id,
        "run_id": args.run_id,
        "trigger": args.trigger,
        "source_revision": source_revision,
        "proposal": {
            "repository": args.repository,
            "base_ref": args.base_ref,
            "head_ref": args.head_ref,
            "pull_request_number": args.pull_request_number,
            "pull_request_url": args.pull_request_url,
            "proposal_revision": proposal_revision,
        },
        "output_hashes": {
            "semantic_report": hash_json(
                {"affected_records": records, "summary": summary}
            ),
            "proposal_diff": hash_bytes(patch),
            "files": outputs,
        },
        "affected_records": records,
        "summary": summary,
        "acceptance": None,
    }
    event["idempotency_key"] = expected_idempotency_key(event)
    event["event_id"] = event_id_for(event["idempotency_key"])
    validate_event(event, expected_state="proposed")
    return event


def data_path(event: dict[str, Any]) -> str:
    return (
        f"source-domain-events/{event['state']}/{event['agent_id']}/"
        f"{event['event_id']}.json"
    )


def marker(event: dict[str, Any], encoded: bytes) -> str:
    validate_event(event, expected_state="proposed")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "event_id": event["event_id"],
        "idempotency_key": event["idempotency_key"],
        "sha256": hash_bytes(encoded),
        "path": data_path(event),
    }
    return f"<!-- ARRP_SOURCE_DOMAIN_EVENT {canonical_json(payload)} -->"


def pending_proposal_projection(event: dict[str, Any]) -> dict[str, Any]:
    """Return the complete, minimized proposal context needed by Elim."""

    validate_event(event, expected_state="proposed")
    return {
        "event_id": event["event_id"],
        "agent_id": event["agent_id"],
        "proposal": copy.deepcopy(event["proposal"]),
        "affected_records": copy.deepcopy(event["affected_records"]),
        "summary": copy.deepcopy(event["summary"]),
    }


def enrich_report(report: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Bind a current-run report to the complete unresolved nightly delta."""

    enriched = copy.deepcopy(report)
    enriched["pending_proposal"] = pending_proposal_projection(event)
    return enriched


def proposal_summary(event: dict[str, Any]) -> str:
    """Render a human-readable summary of the complete pending PR delta."""

    validate_event(event, expected_state="proposed")
    proposal = event["proposal"]
    paths = ", ".join(
        f"`{item['path']}`" for item in event["output_hashes"]["files"]
    )
    return f"""<!-- ARRP_SOURCE_DOMAIN_SUMMARY_START -->
## Complete unresolved proposal

This section describes the complete change currently pending on the persistent
coordinator-owned nightly branch, including checkpoint ancestry. It—not a
current-run count by itself—is the review boundary.

- Proposal event: `{event['event_id']}`
- Exact head revision: `{proposal['proposal_revision']}`
- Affected files ({len(event['output_hashes']['files'])}): {paths}
- Affected records ({event['summary']['affected_record_count']}): {display_records(event)}
- Delta counts: {count_summary(event)}
- Review boundary: the recommendation must cover this exact head; any later head revision requires reassessment.
<!-- ARRP_SOURCE_DOMAIN_SUMMARY_END -->"""


def attach_marker(body: str, event: dict[str, Any], encoded: bytes) -> str:
    without_marker = MARKER_RE.sub("", body)
    without_summary = SUMMARY_RE.sub("\n", without_marker).rstrip()
    return (
        without_summary
        + "\n\n"
        + proposal_summary(event)
        + "\n\n"
        + marker(event, encoded)
        + "\n"
    )


def marker_payload(body: str) -> dict[str, Any]:
    matches = MARKER_RE.findall(body)
    if len(matches) != 1:
        raise EventError(
            "accepted watcher pull request must contain exactly one source-domain-event marker"
        )
    payload = json.loads(matches[0])
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "event_id",
        "idempotency_key",
        "sha256",
        "path",
    }:
        raise EventError("invalid source-domain-event pull-request marker")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise EventError("unsupported marker schema")
    if not EVENT_ID_RE.fullmatch(str(payload["event_id"])):
        raise EventError("invalid marker event ID")
    if not HASH_RE.fullmatch(str(payload["idempotency_key"])):
        raise EventError("invalid marker idempotency key")
    if not HASH_RE.fullmatch(str(payload["sha256"])):
        raise EventError("invalid marker content hash")
    path = str(payload["path"])
    expected = re.compile(
        r"^source-domain-events/proposed/"
        r"(case-monitor-bot|presidential-directives-bot|source-checker-bot)/"
        r"SDE-[A-F0-9]{24}\.json$"
    )
    if not expected.fullmatch(path) or ".." in Path(path).parts:
        raise EventError("invalid marker event path")
    return payload


def event_from_data_ref(data_ref: str, path: str) -> tuple[dict[str, Any], bytes]:
    """Read an event from an existing repository ref without writing it."""
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", data_ref) or data_ref.startswith("-"):
        raise EventError("invalid repository event ref")
    encoded = bytes(git("show", f"{data_ref}:{path}", binary=True))
    try:
        payload = json.loads(encoded)
    except json.JSONDecodeError as exc:
        raise EventError("proposed event is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise EventError("proposed event must be a JSON object")
    return payload, encoded


def verify_merged_file_hashes(event: dict[str, Any], merge_commit: str) -> None:
    for item in event["output_hashes"]["files"]:
        path = item["path"]
        try:
            content = bytes(git("show", f"{merge_commit}:{path}", binary=True))
        except subprocess.CalledProcessError as exc:
            raise EventError(f"accepted merge does not contain expected path: {path}") from exc
        if len(content) != item["bytes"] or hash_bytes(content) != item["sha256"]:
            raise EventError(
                f"accepted merge content does not match the proposed event: {path}"
            )


def verify_acceptance_delta(
    event: dict[str, Any],
    *,
    pr_head_revision: str,
    merge_commit: str,
) -> None:
    """Bind acceptance to both the exact proposal and exact accepted delta."""
    source_revision = event["source_revision"]
    expected_paths = [item["path"] for item in event["output_hashes"]["files"]]
    proposal_paths = exact_modified_paths(
        event["agent_id"],
        source_revision,
        pr_head_revision,
        merge_base=True,
    )
    if proposal_paths != expected_paths:
        raise EventError(
            "pull-request proposal delta does not match the event affected-file set"
        )
    proposal_patch = bytes(
        git(
            "diff",
            "--binary",
            f"{source_revision}...{pr_head_revision}",
            "--",
            *proposal_paths,
            binary=True,
        )
    )
    if hash_bytes(proposal_patch) != event["output_hashes"]["proposal_diff"]:
        raise EventError("pull-request proposal delta hash does not match the event")
    records, summary = delta_semantic_projection(
        event["agent_id"],
        proposal_paths,
        proposal_patch,
    )
    if event["affected_records"] != records or event["summary"] != summary:
        raise EventError(
            "event semantic projection does not match the reviewed proposal delta"
        )
    if event["output_hashes"]["semantic_report"] != hash_json(
        {"affected_records": records, "summary": summary}
    ):
        raise EventError(
            "event semantic-report hash does not match the reviewed proposal delta"
        )

    parent_line = str(git("rev-list", "--parents", "-n", "1", merge_commit))
    revisions = parent_line.split()
    if not revisions or revisions[0] != merge_commit or len(revisions) not in {2, 3}:
        raise EventError(
            "accepted source-domain change must use a supported one- or two-parent merge"
        )
    parents = revisions[1:]
    if len(parents) == 2 and parents[1] != pr_head_revision:
        raise EventError(
            "accepted merge second parent does not match the reviewed pull-request head"
        )
    first_parent = parents[0]
    accepted_paths = exact_modified_paths(
        event["agent_id"],
        first_parent,
        merge_commit,
        merge_base=False,
    )
    if accepted_paths != expected_paths:
        raise EventError(
            "accepted first-parent delta does not match the event affected-file set"
        )


def accept_event(args: argparse.Namespace) -> dict[str, Any]:
    if args.merged != "true":
        raise EventError("pull request was not merged")
    validate_repository(args.repository)
    if args.base_ref != "main":
        raise EventError("accepted source-domain pull request must target main")
    if args.merged_by_type != "User":
        raise EventError("accepted source-domain pull request was not merged by a User")
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", args.merged_by):
        raise EventError("invalid accepting GitHub user")
    if args.merged_by.endswith("[bot]"):
        raise EventError("bot actors may not establish the human acceptance boundary")
    if args.merged_by not in AUTHORIZED_ACCEPTORS:
        raise EventError(
            "accepted source-domain pull request was not merged by an authorized project owner"
        )
    if not REVISION_RE.fullmatch(args.merge_commit):
        raise EventError("invalid merge commit")
    if not REVISION_RE.fullmatch(args.pr_head_revision):
        raise EventError("invalid pull-request head revision")
    body = args.pr_body_file.read_text(encoding="utf-8")
    marker_data = marker_payload(body)
    proposed, encoded = event_from_data_ref(args.data_ref, marker_data["path"])
    if hash_bytes(encoded) != marker_data["sha256"]:
        raise EventError(
            "repository-ref proposed event does not match the PR marker hash"
        )
    validate_event(proposed, expected_state="proposed")
    if proposed["event_id"] != marker_data["event_id"]:
        raise EventError("marker event ID does not match proposed event")
    if proposed["idempotency_key"] != marker_data["idempotency_key"]:
        raise EventError("marker idempotency key does not match proposed event")
    proposal = proposed["proposal"]
    if proposal["repository"] != args.repository:
        raise EventError("proposed-event repository does not match merged PR")
    if proposal["base_ref"] != args.base_ref:
        raise EventError("proposed-event base does not match merged PR")
    if proposal["head_ref"] != args.head_ref:
        raise EventError("proposed-event branch does not match merged PR")
    validate_branch(proposed["agent_id"], args.head_ref)
    if proposal["pull_request_number"] != args.pull_request_number:
        raise EventError("proposed-event PR number does not match merged PR")
    if proposal["pull_request_url"] != args.pull_request_url:
        raise EventError("proposed-event PR URL does not match merged PR")
    if proposal["proposal_revision"] != args.pr_head_revision:
        raise EventError(
            "merged PR head changed after the proposed event marker was attached"
        )
    if not is_ancestor(proposed["source_revision"], args.merge_commit):
        raise EventError("event source revision is not an ancestor of the accepted merge")
    verify_acceptance_delta(
        proposed,
        pr_head_revision=args.pr_head_revision,
        merge_commit=args.merge_commit,
    )
    verify_merged_file_hashes(proposed, args.merge_commit)
    accepted = copy.deepcopy(proposed)
    accepted["state"] = "accepted"
    accepted["acceptance"] = {
        "boundary": "human-pull-request-merge",
        "pull_request_number": args.pull_request_number,
        "pull_request_url": args.pull_request_url,
        "merged_at": args.merged_at,
        "merged_by": args.merged_by,
        "merged_by_type": args.merged_by_type,
        "merge_commit": args.merge_commit,
    }
    validate_event(accepted, expected_state="accepted")
    return accepted


def display_records(event: dict[str, Any], limit: int = 100) -> str:
    values = [item["record_id"] for item in event["affected_records"]]
    if not values:
        return "None"
    if len(values) <= limit:
        return ", ".join(values)
    return ", ".join(values[:limit]) + f", and {len(values) - limit} more"


def count_summary(event: dict[str, Any]) -> str:
    counts = event["summary"]["counts"]
    if not counts:
        return "No categorized counts."
    return "; ".join(f"{name}: {value}" for name, value in sorted(counts.items()))


def source_log_entry(event: dict[str, Any]) -> str:
    acceptance = event["acceptance"]
    display = AGENTS[event["agent_id"]]["display"]
    marker_line = f"<!-- ARRP_SOURCE_DOMAIN_EVENT:{event['event_id']}:source-monitor -->"
    return f"""

{marker_line}
## {acceptance['merged_at']} — {display} accepted event

- Event ID: `{event['event_id']}`
- State: `accepted`
- Chain ID: `{event['chain_id']}`
- Run ID: `{event['run_id']}`
- Human acceptance: [PR #{acceptance['pull_request_number']}]({acceptance['pull_request_url']}) merged by `{acceptance['merged_by']}`
- Source revision: `{event['source_revision']}`
- Accepted merge: `{acceptance['merge_commit']}`
- Affected records ({event['summary']['affected_record_count']}): {display_records(event)}
- Result: {event['summary']['status']}
- Counts: {count_summary(event)}
- Output hashes: semantic report `{event['output_hashes']['semantic_report']}`; proposal delta `{event['output_hashes']['proposal_diff']}`
- Boundary: Deterministic source observation only; no legal significance, route, disposition, source substitution, score, or project-field decision was inferred.
"""


def agent_log_entry(event: dict[str, Any]) -> str:
    acceptance = event["acceptance"]
    paths = ", ".join(item["path"] for item in event["output_hashes"]["files"])
    marker_line = f"<!-- ARRP_SOURCE_DOMAIN_EVENT:{event['event_id']}:agent-audit -->"
    date = str(acceptance["merged_at"])[:10]
    return f"""

{marker_line}
### {date} — Accepted source-domain event {event['event_id']} — source monitoring

| Field | Entry |
| --- | --- |
| Date/time | {acceptance['merged_at']} |
| Agent | {event['agent_id']} |
| Run ID | {event['run_id']} |
| Unit ID | {event['event_id']} |
| Trigger | {event['trigger']} |
| Task type | source-domain observation and accepted baseline/report update |
| Outcome | Accepted through human merge of [PR #{acceptance['pull_request_number']}]({acceptance['pull_request_url']}) |
| Issue/task | {event['summary']['status']}; {event['summary']['affected_record_count']} affected records |
| Issue page | N/A |
| Audit history | N/A |
| Proposal page | {acceptance['pull_request_url']} |
| Tier | none |
| Files changed | {paths} |
| Validation | Proposed-event schema and content hash; exact same-repository coordinator-owned nightly branch and PR; exact PR head revision; source-revision ancestry; exact proposal patch and delta-derived semantics; supported merge topology; exact first-parent accepted delta and file hashes; allowlisted human-owner merge boundary |
| Commit | {acceptance['merge_commit']} |
| Push status | Accepted on `main`; human-readable log rendering proposed separately |
| Rollback notes | Revert accepted merge `{acceptance['merge_commit']}`; retain this provenance entry and record any revert separately |
| Blockers/skipped checks | No substantive source meaning, legal significance, route, disposition, or citation substitution was determined by the bot |
"""


def append_once(path: Path, marker_text: str, entry_text: str) -> bool:
    if not path.is_file():
        raise EventError(f"required shared log is missing: {path}")
    existing = path.read_text(encoding="utf-8")
    if marker_text in existing:
        return False
    separator = "" if existing.endswith("\n") else "\n"
    path.write_text(existing + separator + entry_text.lstrip("\n"), encoding="utf-8")
    return True


def render_event(event: dict[str, Any], source_log: Path, agent_log: Path) -> bool:
    validate_event(event, expected_state="accepted")
    source_marker = f"<!-- ARRP_SOURCE_DOMAIN_EVENT:{event['event_id']}:source-monitor -->"
    agent_marker = f"<!-- ARRP_SOURCE_DOMAIN_EVENT:{event['event_id']}:agent-audit -->"
    source_changed = append_once(
        source_log, source_marker, source_log_entry(event)
    )
    agent_changed = append_once(agent_log, agent_marker, agent_log_entry(event))
    return source_changed or agent_changed


def verify_existing_log_branch(
    *,
    base_ref: str,
    branch_ref: str,
    source_log: Path,
    agent_log: Path,
) -> None:
    """Require a reusable event branch to equal the fresh deterministic render."""
    expected_paths = [source_log.as_posix(), agent_log.as_posix()]
    status_text = str(git("diff", "--name-status", f"{base_ref}...{branch_ref}", "--"))
    observed_paths: list[str] = []
    invalid: list[str] = []
    for line in status_text.splitlines():
        if not line:
            continue
        fields = line.split("\t")
        if len(fields) != 2 or fields[0] != "M":
            invalid.append(line)
            continue
        observed_paths.append(fields[1])
    if invalid or sorted(observed_paths) != sorted(expected_paths):
        raise EventError(
            "pre-existing event log branch does not contain the exact two-log delta"
        )
    for path in expected_paths:
        local = Path(path)
        if not local.is_file():
            raise EventError(f"freshly rendered log is missing: {path}")
        tree_entry = str(git("ls-tree", branch_ref, "--", path))
        mode = tree_entry.split(maxsplit=1)[0] if tree_entry else ""
        if mode != "100644":
            raise EventError(f"pre-existing event log is not an ordinary file: {path}")
        remote_content = bytes(git("show", f"{branch_ref}:{path}", binary=True))
        if remote_content != local.read_bytes():
            raise EventError(
                f"pre-existing event log branch differs from the fresh render: {path}"
            )


def write_github_outputs(path: Path | None, values: dict[str, Any]) -> None:
    if path is None:
        return
    with path.open("a", encoding="utf-8") as output:
        for key, value in values.items():
            text = str(value)
            if "\n" in text or "\r" in text:
                raise EventError(f"GitHub output {key} contains a newline")
            output.write(f"{key}={text}\n")


def propose_command(args: argparse.Namespace) -> int:
    event = build_proposed_event(args)
    encoded = write_json(args.output, event)
    if args.enrich_report:
        report = read_json(args.enrich_report)
        args.enrich_report.write_text(
            json.dumps(enrich_report(report, event), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    write_github_outputs(
        args.github_output,
        {
            "domain_event_id": event["event_id"],
            "domain_event_key": event["idempotency_key"],
            "domain_event_hash": hash_bytes(encoded),
            "domain_event_path": data_path(event),
            "domain_event_state": event["state"],
            "domain_event_json": canonical_json(event),
        },
    )
    print(f"Created proposed source-domain event {event['event_id']}")
    return 0


def attach_command(args: argparse.Namespace) -> int:
    event = read_json(args.event)
    encoded = args.event.read_bytes()
    validate_event(event, expected_state="proposed")
    body = args.body.read_text(encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(attach_marker(body, event, encoded), encoding="utf-8")
    return 0


def accept_command(args: argparse.Namespace) -> int:
    event = accept_event(args)
    encoded = write_json(args.output, event)
    write_github_outputs(
        args.github_output,
        {
            "domain_event_id": event["event_id"],
            "domain_event_key": event["idempotency_key"],
            "domain_event_hash": hash_bytes(encoded),
            "domain_event_path": data_path(event),
            "domain_event_state": event["state"],
            "domain_event_json": canonical_json(event),
        },
    )
    print(f"Verified accepted source-domain event {event['event_id']}")
    return 0


def render_command(args: argparse.Namespace) -> int:
    event = read_json(args.event)
    changed = render_event(event, args.source_log, args.agent_log)
    write_github_outputs(args.github_output, {"changed": str(changed).lower()})
    print("Rendered accepted event." if changed else "Event was already rendered.")
    return 0


def verify_log_branch_command(args: argparse.Namespace) -> int:
    verify_existing_log_branch(
        base_ref=args.base_ref,
        branch_ref=args.branch_ref,
        source_log=args.source_log,
        agent_log=args.agent_log,
    )
    print("Verified exact pre-existing event log branch.")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)

    propose = subparsers.add_parser("propose")
    propose.add_argument("--agent", choices=sorted(AGENTS), required=True)
    propose.add_argument("--report", type=Path, required=True)
    propose.add_argument("--output", type=Path, required=True)
    propose.add_argument("--repository", required=True)
    propose.add_argument("--base-ref", default="main")
    propose.add_argument("--git-base", required=True)
    propose.add_argument("--head-ref", required=True)
    propose.add_argument("--pull-request-number", type=int, required=True)
    propose.add_argument("--pull-request-url", required=True)
    propose.add_argument("--chain-id", default="")
    propose.add_argument("--run-id", required=True)
    propose.add_argument("--trigger", required=True)
    propose.add_argument(
        "--enrich-report",
        type=Path,
        help=(
            "Write the complete unresolved proposal projection into this "
            "current-run report for downstream Elim queue construction."
        ),
    )
    propose.add_argument("--github-output", type=Path)
    propose.set_defaults(handler=propose_command)

    attach = subparsers.add_parser("attach-marker")
    attach.add_argument("--event", type=Path, required=True)
    attach.add_argument("--body", type=Path, required=True)
    attach.add_argument("--output", type=Path, required=True)
    attach.set_defaults(handler=attach_command)

    accept = subparsers.add_parser("accept")
    accept.add_argument("--pr-body-file", type=Path, required=True)
    accept.add_argument(
        "--event-ref",
        "--data-ref",
        dest="data_ref",
        required=True,
        help="Existing repository ref containing the proposed event; read-only.",
    )
    accept.add_argument("--repository", required=True)
    accept.add_argument("--base-ref", required=True)
    accept.add_argument("--head-ref", required=True)
    accept.add_argument("--pull-request-number", type=int, required=True)
    accept.add_argument("--pull-request-url", required=True)
    accept.add_argument("--pr-head-revision", required=True)
    accept.add_argument("--merged", choices=("true", "false"), required=True)
    accept.add_argument("--merged-at", required=True)
    accept.add_argument("--merged-by", required=True)
    accept.add_argument("--merged-by-type", required=True)
    accept.add_argument("--merge-commit", required=True)
    accept.add_argument("--output", type=Path, required=True)
    accept.add_argument("--github-output", type=Path)
    accept.set_defaults(handler=accept_command)

    render = subparsers.add_parser("render")
    render.add_argument("--event", type=Path, required=True)
    render.add_argument("--source-log", type=Path, required=True)
    render.add_argument("--agent-log", type=Path, required=True)
    render.add_argument("--github-output", type=Path)
    render.set_defaults(handler=render_command)

    verify_log_branch = subparsers.add_parser("verify-log-branch")
    verify_log_branch.add_argument("--base-ref", required=True)
    verify_log_branch.add_argument("--branch-ref", required=True)
    verify_log_branch.add_argument("--source-log", type=Path, required=True)
    verify_log_branch.add_argument("--agent-log", type=Path, required=True)
    verify_log_branch.set_defaults(handler=verify_log_branch_command)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (EventError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise SystemExit(f"source-domain-event error: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
