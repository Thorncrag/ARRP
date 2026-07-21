#!/usr/bin/env python3
"""Detect Just Security tracker changes and selectively verify changed court dockets.

The watcher fetches the Just Security Trump administration litigation tracker once,
compares stable tracker-entry fingerprints with a compressed rolling baseline stored in
one GitHub issue comment, and reports added, changed, or removed entries. CourtListener
is queried only for added or changed entries that link to a supported docket, subject
to a conservative cap and pacing. Signals never decide legal significance or modify
repository content, Project fields, source inventories, proposals, or issue status.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html as html_lib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / ".github" / "case-monitor-bot.json"
DEFAULT_REGISTRY = ROOT / "inventory" / "github_issue_registry.csv"
DEFAULT_SOURCES = ROOT / "inventory" / "sources.csv"
DEFAULT_PENDING_SOURCES = ROOT / "inventory" / "sources-pending.csv"
BASELINE_MARKER = "arrp-case-monitor-tracker-state:v1"
ISSUE_SIGNAL_MARKER = "arrp-case-monitor-tracker-signal:v1"
USER_AGENT = "ARRP case-monitor-bot/0.2"
MAX_COMMENT_BYTES = 60_000


def normalize_text(value: str, limit: int = 4000) -> str:
    value = " ".join(value.replace("\xa0", " ").split())
    value = "".join(character for character in value if character >= " " or character == "\n")
    return value[:limit]


def markdown_text(value: str, limit: int = 500) -> str:
    value = html_lib.escape(normalize_text(value, limit), quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|>-])", r"\\\1", value)


def safe_error(value: str) -> str:
    return normalize_text(value, 500).replace("--", "—").replace("<", "[").replace(">", "]")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def split_associations(raw: str) -> set[str]:
    return {value.strip() for value in raw.split(";") if value.strip()}


def docket_key(url: str) -> str:
    parsed = urllib.parse.urlsplit(url.strip())
    if parsed.scheme != "https" or parsed.hostname != "www.courtlistener.com":
        return ""
    match = re.search(r"/docket/(\d+)(?:/|$)", parsed.path)
    return f"courtlistener:{match.group(1)}" if match else ""


def docket_id(url: str) -> int | None:
    key = docket_key(url)
    return int(key.split(":", 1)[1]) if key else None


def normalize_docket_identity(value: str) -> str:
    """Normalize displayed docket text for use in a row-level composite key."""

    return re.sub(r"\s+", "", normalize_text(value, 100)).casefold()


def primary_docket_key(entry: dict[str, Any] | None) -> str:
    if not entry:
        return ""
    return docket_key(str(entry.get("courtlistener_url") or ""))


def normalize_docket_observation(payload: dict[str, Any], expected_id: int) -> dict[str, Any]:
    if int(payload.get("id", 0)) != expected_id:
        raise ValueError(f"CourtListener returned the wrong docket ID for {expected_id}")
    material = {
        "docket_id": expected_id,
        "case_name": normalize_text(str(payload.get("case_name") or ""), 500),
        "docket_number": normalize_text(str(payload.get("docket_number") or ""), 100),
        "date_modified": str(payload.get("date_modified") or ""),
        "date_last_index": str(payload.get("date_last_index") or ""),
        "date_last_filing": str(payload.get("date_last_filing") or ""),
        "date_terminated": str(payload.get("date_terminated") or ""),
        "blocked": bool(payload.get("blocked", False)),
    }
    return {**material, "fingerprint": fingerprint(material)}


class TrackerTableParser(HTMLParser):
    """Extract one configured HTML table without external parser dependencies."""

    def __init__(self, table_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self.table_id = table_id
        self.in_table = False
        self.in_cell = False
        self.current_cell: dict[str, Any] | None = None
        self.current_row: list[dict[str, Any]] | None = None
        self.rows: list[list[dict[str, Any]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "table" and attributes.get("id") == self.table_id:
            if self.in_table:
                raise ValueError("nested tracker table")
            self.in_table = True
            return
        if not self.in_table:
            return
        if tag == "tr":
            self.current_row = []
        elif tag in {"th", "td"} and self.current_row is not None:
            self.in_cell = True
            self.current_cell = {"text": [], "links": []}
        elif tag == "a" and self.current_cell is not None:
            href = normalize_text(attributes.get("href") or "", 2000)
            if href:
                self.current_cell["links"].append(href)

    def handle_data(self, data: str) -> None:
        if self.in_cell and self.current_cell is not None:
            self.current_cell["text"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.in_table:
            return
        if tag in {"th", "td"} and self.current_cell is not None and self.current_row is not None:
            self.current_row.append(
                {
                    "text": normalize_text(" ".join(self.current_cell["text"])),
                    "links": list(dict.fromkeys(self.current_cell["links"])),
                }
            )
            self.current_cell = None
            self.in_cell = False
        elif tag == "tr" and self.current_row is not None:
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = None
        elif tag == "table":
            self.in_table = False


class PlainTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return normalize_text(" ".join(self.parts), 500_000)


DOCKET_PATTERN = re.compile(
    r"\b(?:\d{1,2}:)?\d{2}-(?:cv|cr|mc|md|bk|ap|misc)-\d{2,8}(?:-[A-Za-z0-9-]+)?\b|\b\d{2}-\d{3,7}\b",
    re.IGNORECASE,
)

EXPECTED_TRACKER_HEADINGS = [
    "Case Name",
    "Filings",
    "Date Case Filed",
    "State A.G.'s",
    "Case Status",
    "Issue",
    "Executive Action",
    "Last Case Update",
    "Case Summary",
    "Case Updates",
]


def tracker_entry(cells: dict[str, dict[str, Any]]) -> dict[str, Any]:
    case_cell = cells["Case Name"]
    case_text = normalize_text(case_cell["text"], 1500)
    match = DOCKET_PATTERN.search(case_text)
    docket_number = match.group(0) if match else ""
    case_name = normalize_text(case_text[: match.start()] if match else case_text, 500)
    courtlistener_url = ""
    for link in case_cell["links"]:
        if docket_key(link):
            parsed = urllib.parse.urlsplit(link)
            courtlistener_url = urllib.parse.urlunsplit(
                ("https", "www.courtlistener.com", parsed.path, "", "")
            )
            break
    primary_key = docket_key(courtlistener_url)
    displayed_identity = normalize_docket_identity(docket_number)
    if primary_key:
        if not displayed_identity:
            displayed_identity = "missing-" + hashlib.sha256(
                case_name.casefold().encode("utf-8")
            ).hexdigest()[:16]
        key = f"{primary_key}|docket:{displayed_identity}"
    else:
        identity = f"{case_name.casefold()}|{displayed_identity}"
        key = "tracker:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    case_updates = normalize_text(cells["Case Updates"]["text"], 100_000)
    case_summary = normalize_text(cells.get("Case Summary", {}).get("text", ""), 100_000)
    summary_hash = hashlib.sha256(case_summary.encode("utf-8")).hexdigest()
    updates_hash = hashlib.sha256(case_updates.encode("utf-8")).hexdigest()
    entry = {
        "key": key,
        "primary_docket_key": primary_key,
        "case_name": case_name or "Unnamed tracker entry",
        "docket_number": normalize_text(docket_number, 100),
        "courtlistener_url": courtlistener_url,
        "status": normalize_text(cells["Case Status"]["text"], 300),
        "last_case_update": normalize_text(cells["Last Case Update"]["text"], 100),
        "case_summary_hash": summary_hash,
        "case_updates_hash": updates_hash,
        "case_update_excerpt": normalize_text(case_updates, 800),
    }
    entry["fingerprint"] = fingerprint(
        {
            "case_name": entry["case_name"],
            "docket_number": entry["docket_number"],
            "courtlistener_url": entry["courtlistener_url"],
            "status": entry["status"],
            "last_case_update": entry["last_case_update"],
            "case_summary": case_summary,
            "case_updates": case_updates,
        }
    )
    return entry


def declared_tracker_snapshot(
    document: str, table_id: str, actual_statuses: Counter[str]
) -> tuple[int, dict[str, int]]:
    table_match = re.search(
        rf"<table\b[^>]*\bid=[\"']{re.escape(table_id)}[\"']",
        document,
        flags=re.IGNORECASE,
    )
    if not table_match:
        raise ValueError(f"tracker table {table_id} was not found")
    parser = PlainTextParser()
    parser.feed(document[: table_match.start()])
    preamble = parser.text()
    total_match = re.search(
        r"Total number of cases currently tracked\s*:\s*(\d+)", preamble, re.IGNORECASE
    )
    if not total_match:
        raise ValueError("tracker did not declare its total number of tracked cases")
    declared_statuses: dict[str, int] = {}
    for status in actual_statuses:
        if not status:
            raise ValueError("tracker contains a row without a case status")
        match = re.search(rf"{re.escape(status)}\s*:\s*(\d+)", preamble)
        if not match:
            raise ValueError(f"tracker status snapshot omitted row status {status!r}")
        declared_statuses[status] = int(match.group(1))
    return int(total_match.group(1)), declared_statuses


def parse_tracker_html(document: str, config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    parser = TrackerTableParser(config["tableId"])
    parser.feed(document)
    if not parser.rows:
        raise ValueError(f"tracker table {config['tableId']} was not found or was empty")
    headings = [normalize_text(cell["text"], 200) for cell in parser.rows[0]]
    if headings != EXPECTED_TRACKER_HEADINGS:
        raise ValueError("tracker table headings do not match the expected 10-column schema")
    entries: dict[str, dict[str, Any]] = {}
    for row in parser.rows[1:]:
        if len(row) != len(headings):
            raise ValueError("tracker table contains a row with an unexpected column count")
        cells = dict(zip(headings, row))
        entry = tracker_entry(cells)
        if entry["key"] in entries:
            raise ValueError(f"tracker table contains duplicate identity {entry['key']}")
        entries[entry["key"]] = entry
    minimum = int(config["minimumEntries"])
    maximum = int(config["maximumEntries"])
    if not minimum <= len(entries) <= maximum:
        raise ValueError(
            f"tracker parse produced {len(entries)} entries; expected between {minimum} and {maximum}"
        )
    actual_statuses = Counter(entry["status"] for entry in entries.values())
    declared_total, declared_statuses = declared_tracker_snapshot(
        document, config["tableId"], actual_statuses
    )
    if declared_total != len(entries):
        raise ValueError(
            f"tracker declared {declared_total} entries but parser found {len(entries)}"
        )
    mismatches = {
        status: (declared_statuses[status], count)
        for status, count in actual_statuses.items()
        if declared_statuses[status] != count
    }
    if mismatches:
        detail = "; ".join(
            f"{status}: declared {declared}, parsed {actual}"
            for status, (declared, actual) in sorted(mismatches.items())
        )
        raise ValueError("tracker status totals do not match parsed rows: " + detail)
    if sum(declared_statuses.values()) != declared_total:
        raise ValueError("tracker status totals do not sum to the declared tracker total")
    return entries


def compact_snapshot(entries: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    return {
        key: {
            "s": entry["status"],
            "l": entry["last_case_update"],
            # A 128-bit prefix keeps the GitHub comment comfortably bounded while
            # still representing the exact normalized row, including both narratives.
            "f": entry["fingerprint"][:32],
        }
        for key, entry in sorted(entries.items())
    }


def expand_snapshot_entry(key: str, value: dict[str, str]) -> dict[str, str]:
    primary = key.split("|docket:", 1)[0] if key.startswith("courtlistener:") else ""
    displayed = key.split("|docket:", 1)[1] if "|docket:" in key else ""
    courtlistener_url = ""
    if primary:
        courtlistener_url = f"https://www.courtlistener.com/docket/{primary.split(':', 1)[1]}/"
    return {
        "key": key,
        "primary_docket_key": primary,
        "case_name": "Removed tracker entry",
        "docket_number": displayed,
        "courtlistener_url": courtlistener_url,
        "status": value.get("s", ""),
        "last_case_update": value.get("l", ""),
        "fingerprint": value.get("f", ""),
        "case_update_excerpt": "",
    }


def changed_fields(previous: dict[str, str], current: dict[str, Any]) -> list[str]:
    fields = []
    if previous.get("s", "") != current["status"]:
        fields.append("status")
    if previous.get("l", "") != current["last_case_update"]:
        fields.append("last case update")
    if previous.get("f", "") != current["fingerprint"][:32] and not fields:
        fields.append("case name or narrative content")
    return fields


def compare_snapshots(
    previous: dict[str, dict[str, str]] | None,
    current: dict[str, dict[str, Any]],
    maximum_removal_fraction: float,
) -> tuple[str, list[dict[str, Any]]]:
    if previous is None:
        return "baseline_established", []
    previous_keys = set(previous)
    current_keys = set(current)
    removed_count = len(previous_keys - current_keys)
    if previous_keys and removed_count / len(previous_keys) > maximum_removal_fraction:
        raise ValueError(
            f"tracker parse would remove {removed_count} of {len(previous_keys)} baseline entries; "
            "refusing structurally implausible mass removal"
        )
    changes: list[dict[str, Any]] = []
    for key in sorted(current_keys - previous_keys):
        changes.append({"kind": "added", "key": key, "current": current[key], "previous": None})
    for key in sorted(previous_keys & current_keys):
        if previous[key].get("f", "")[:32] != current[key]["fingerprint"][:32]:
            changes.append(
                {
                    "kind": "changed",
                    "key": key,
                    "current": current[key],
                    "previous": expand_snapshot_entry(key, previous[key]),
                    "changed_fields": changed_fields(previous[key], current[key]),
                }
            )
    for key in sorted(previous_keys - current_keys):
        changes.append(
            {
                "kind": "removed",
                "key": key,
                "current": None,
                "previous": expand_snapshot_entry(key, previous[key]),
            }
        )
    return ("changes_detected" if changes else "no_change"), changes


def encode_baseline(snapshot: dict[str, dict[str, str]]) -> str:
    raw = canonical_json({"v": 2, "e": snapshot}).encode("utf-8")
    return base64.urlsafe_b64encode(zlib.compress(raw, level=9)).decode("ascii")


def decode_baseline(value: str) -> dict[str, dict[str, str]]:
    payload = json.loads(zlib.decompress(base64.urlsafe_b64decode(value)).decode("utf-8"))
    if payload.get("v") == 2 and isinstance(payload.get("e"), dict):
        return payload["e"]
    if payload.get("schema_version") == 1 and isinstance(payload.get("entries"), dict):
        return payload["entries"]
    raise ValueError("unsupported tracker baseline schema")


def baseline_from_comment(body: str) -> dict[str, dict[str, str]] | None:
    match = re.search(
        rf"<!--\s*{re.escape(BASELINE_MARKER)}\s*\n([A-Za-z0-9_=-]+)\s*\n-->", body
    )
    return decode_baseline(match.group(1)) if match else None


def render_baseline_comment(
    snapshot: dict[str, dict[str, str]], checked_at: str, status: str, change_count: int
) -> str:
    encoded = encode_baseline(snapshot)
    body = f"""<!-- {BASELINE_MARKER}
{encoded}
-->
## Case-monitor tracker baseline

**Last successful tracker check:** {checked_at}

**Tracker entries:** {len(snapshot)}
**Run result:** {status.replace('_', ' ')}
**Changed entries reported:** {change_count}

This compressed state supports deterministic change detection. It is not a legal finding, source record, or project disposition.
"""
    if len(body.encode("utf-8")) > MAX_COMMENT_BYTES:
        raise ValueError("compressed tracker baseline exceeds the safe GitHub comment size")
    return body


class TrackerClient:
    def __init__(self, config: dict[str, Any]) -> None:
        parsed = urllib.parse.urlsplit(config["url"])
        if parsed.scheme != "https" or parsed.hostname not in set(config["allowedHosts"]):
            raise ValueError("tracker URL must use an allowlisted HTTPS host")
        self.url = config["url"]
        self.maximum = int(config["maximumResponseBytes"])

    def fetch(self) -> str:
        request = urllib.request.Request(
            self.url,
            headers={"Accept": "text/html", "User-Agent": USER_AGENT},
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            content_type = response.headers.get_content_type()
            if content_type not in {"text/html", "application/xhtml+xml"}:
                raise ValueError("tracker returned a non-HTML response")
            payload = response.read(self.maximum + 1)
            if len(payload) > self.maximum:
                raise ValueError("tracker response exceeded configured size limit")
            return payload.decode(response.headers.get_content_charset() or "utf-8", errors="replace")


class CourtListenerClient:
    def __init__(self, token: str, api_root: str) -> None:
        parsed = urllib.parse.urlsplit(api_root)
        if parsed.scheme != "https" or parsed.hostname != "www.courtlistener.com":
            raise ValueError("CourtListener API root must use the allowlisted HTTPS host")
        self.token = token
        self.api_root = api_root.rstrip("/")

    def docket(self, number: int) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.api_root}/dockets/{number}/",
            headers={
                "Accept": "application/json",
                "Authorization": f"Token {self.token}",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.headers.get_content_type() != "application/json":
                    raise ValueError("CourtListener returned a non-JSON response")
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"CourtListener docket {number} failed with HTTP {exc.code}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"CourtListener docket {number} returned invalid JSON")
        return payload


class GitHubClient:
    def __init__(self, repository: str, token: str) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError("invalid GitHub repository name")
        if not token:
            raise ValueError("GITHUB_TOKEN is required for GitHub state access")
        self.repository = repository
        self.token = token
        self.root = f"https://api.github.com/repos/{repository}"

    def request(self, method: str, path: str, payload: Any | None = None) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.root + path,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "User-Agent": USER_AGENT,
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"GitHub API {method} {path} failed: {exc.code} {detail}") from exc
        return json.loads(body) if body else None

    def comments(self, number: int) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for page in range(1, 11):
            batch = self.request("GET", f"/issues/{number}/comments?per_page=100&page={page}")
            output.extend(batch)
            if len(batch) < 100:
                break
        return output

    def monitoring_issues(self, label: str) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        encoded = urllib.parse.quote(label, safe="")
        for page in range(1, 11):
            batch = self.request(
                "GET", f"/issues?state=open&labels={encoded}&per_page=100&page={page}"
            )
            output.extend(issue for issue in batch if "pull_request" not in issue)
            if len(batch) < 100:
                break
        return output

    def ensure_label(self, name: str, color: str, description: str) -> None:
        encoded = urllib.parse.quote(name, safe="")
        try:
            self.request("GET", f"/labels/{encoded}")
        except RuntimeError as exc:
            if "failed: 404" not in str(exc):
                raise
            self.request("POST", "/labels", {"name": name, "color": color, "description": description})

    def add_label(self, number: int, label: str) -> None:
        self.request("POST", f"/issues/{number}/labels", {"labels": [label]})

    def create_comment(self, number: int, body: str) -> dict[str, Any]:
        return self.request("POST", f"/issues/{number}/comments", {"body": body})

    def update_comment(self, comment_id: int, body: str) -> dict[str, Any]:
        return self.request("PATCH", f"/issues/comments/{comment_id}", {"body": body})


def github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        return token
    completed = subprocess.run(
        ["gh", "auth", "token"], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def marked_comment(comments: list[dict[str, Any]], marker: str) -> dict[str, Any] | None:
    return next((comment for comment in comments if marker in comment.get("body", "")), None)


def source_map(rows: list[dict[str, str]]) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = docket_key(row.get("URL", ""))
        if not key:
            continue
        output[key].append(
            {
                "source_id": normalize_text(row.get("Source ID", ""), 100),
                "record_ids": sorted(split_associations(row.get("Associated Record IDs", ""))),
            }
        )
    return output


def attach_source_matches(
    changes: list[dict[str, Any]], mapping: dict[str, list[dict[str, Any]]]
) -> None:
    for change in changes:
        change["source_matches"] = mapping.get(primary_docket_key(change_entry(change)), [])


def verify_changed_dockets(
    changes: list[dict[str, Any]],
    config: dict[str, Any],
    token: str,
    fixture: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    keys = sorted(
        {
            primary_docket_key(change.get("current"))
            for change in changes
            if change["kind"] in {"added", "changed"}
            and primary_docket_key(change.get("current"))
        },
        key=lambda value: int(value.split(":", 1)[1]),
    )
    maximum = int(config["maxDocketsPerRun"])
    selected = set(keys[:maximum])
    results: dict[str, dict[str, Any]] = {}
    if not token and fixture is None:
        return {
            key: {"outcome": "unverified", "reason": "CourtListener token unavailable"}
            for key in keys
        }
    client = None if fixture is not None else CourtListenerClient(token, config["apiRoot"])
    interval = float(config.get("requestIntervalSeconds", 0))
    for position, key in enumerate(keys):
        if key not in selected:
            results[key] = {"outcome": "unverified", "reason": "per-run verification cap reached"}
            continue
        if client is not None and position and interval > 0:
            time.sleep(interval)
        number = int(key.split(":", 1)[1])
        try:
            payload = fixture.get(str(number)) if fixture is not None else client.docket(number)
            if not isinstance(payload, dict):
                raise ValueError(f"CourtListener docket {number} is absent from fixture")
            results[key] = {
                "outcome": "queried",
                "observation": normalize_docket_observation(payload, number),
            }
        except (OSError, RuntimeError, ValueError, urllib.error.URLError) as exc:
            results[key] = {"outcome": "failed", "reason": safe_error(str(exc))}
    return results


def registry_issue_map(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("GitHub Number", "").isdigit() and row.get("Object ID", "").strip():
            output[row["Object ID"].strip()] = {
                "number": int(row["GitHub Number"]),
                "url": row.get("GitHub Issue", ""),
                "title": row.get("GitHub Title", ""),
            }
    return output


def mapped_issue_signals(
    changes: list[dict[str, Any]],
    registry: dict[str, dict[str, Any]],
    monitoring_issues: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    live = {int(issue["number"]): issue for issue in monitoring_issues}
    output: dict[int, dict[str, Any]] = {}
    for change in changes:
        record_ids = {
            record_id
            for match in change.get("source_matches", [])
            for record_id in match["record_ids"]
        }
        for record_id in sorted(record_ids):
            issue = registry.get(record_id)
            if not issue or issue["number"] not in live:
                continue
            signal = output.setdefault(
                issue["number"],
                {"record_id": record_id, "issue": issue, "changes": []},
            )
            if change not in signal["changes"]:
                signal["changes"].append(change)
    return output


def change_entry(change: dict[str, Any]) -> dict[str, Any]:
    entry = change["current"] or change["previous"]
    return entry


def verification_for_change(
    change: dict[str, Any], verification: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    key = primary_docket_key(change.get("current"))
    return verification.get(key, {"outcome": "not applicable"})


def render_issue_signal(signal: dict[str, Any], checked_at: str, verification: dict[str, Any]) -> str:
    rows = []
    for change in signal["changes"][:25]:
        entry = change_entry(change)
        source_ids = sorted(
            {
                match["source_id"]
                for match in change.get("source_matches", [])
                if match["source_id"]
            }
        )
        verify = verification_for_change(change, verification)["outcome"]
        rows.append(
            f"| {markdown_text(change['kind'].title(), 20)} | {markdown_text(entry['case_name'])} | "
            f"{markdown_text(entry['docket_number'] or 'Not stated', 100)} | "
            f"{markdown_text(', '.join(source_ids) or 'No matched source', 200)} | {markdown_text(verify, 50)} |"
        )
    omitted = len(signal["changes"]) - len(rows)
    omission = f"\n\n{omitted} additional mapped changes are listed in the workflow report." if omitted else ""
    return f"""<!-- {ISSUE_SIGNAL_MARKER} -->
## Automated tracker-change signal

**Last tracker check:** {checked_at}

The Just Security litigation tracker changed for source records associated with this monitored issue. This is a routing signal only: it does not establish that a filing is legally significant, alter ARRP's analysis, or satisfy the required human monitoring review.

| Tracker change | Case | Docket | Matched source | CourtListener check |
| --- | --- | --- | --- | --- |
{chr(10).join(rows)}{omission}

Review the tracker change and controlling record, then remove `needs: monitor review` after acknowledgment.
"""


def render_summary(
    *,
    status: str,
    checked_at: str,
    tracker_url: str,
    entry_count: int,
    changes: list[dict[str, Any]],
    verification: dict[str, dict[str, Any]],
    mapped_signals: dict[int, dict[str, Any]],
) -> str:
    counts = Counter(change["kind"] for change in changes)
    verification_counts = Counter(result["outcome"] for result in verification.values())
    lines = [
        "## ARRP case-monitor-bot",
        "",
        f"Checked at: **{checked_at}**  ",
        f"Tracker: [Just Security litigation tracker]({tracker_url})  ",
        f"Parsed tracker entries: **{entry_count}**  ",
        f"Result: **{status.replace('_', ' ')}**",
        "",
        "### Tracker changes",
        "",
        f"- Added: **{counts['added']}**",
        f"- Changed: **{counts['changed']}**",
        f"- Removed: **{counts['removed']}**",
        f"- Mapped monitored ARRP issues signaled: **{len(mapped_signals)}**",
        "",
        "### Targeted CourtListener checks",
        "",
        f"- Queried: **{verification_counts['queried']}**",
        f"- Failed: **{verification_counts['failed']}**",
        f"- Unverified: **{verification_counts['unverified']}**",
    ]
    if changes:
        lines.extend(
            [
                "",
                "| Change | Case | Docket | Tracker status | Last case update | ARRP source match | CourtListener |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for change in changes[:40]:
            entry = change_entry(change)
            source_ids = sorted(
                {
                    match["source_id"]
                    for match in change.get("source_matches", [])
                    if match["source_id"]
                }
            )
            verify = verification_for_change(change, verification)["outcome"]
            lines.append(
                f"| {markdown_text(change['kind'].title(), 20)} | {markdown_text(entry['case_name'])} | "
                f"{markdown_text(entry['docket_number'] or 'Not stated', 100)} | "
                f"{markdown_text(entry['status'] or 'Not stated', 200)} | "
                f"{markdown_text(entry['last_case_update'] or 'Not stated', 100)} | "
                f"{markdown_text(', '.join(source_ids) or 'None', 200)} | {markdown_text(verify, 50)} |"
            )
        if len(changes) > 40:
            lines.append(f"\n{len(changes) - 40} additional changes are retained in the JSON report.")
    unmapped_added = [
        change
        for change in changes
        if change["kind"] == "added" and not change.get("source_matches")
    ]
    if unmapped_added:
        lines.extend(
            [
                "",
                "### Unmatched added entries",
                "",
                "These are later intake leads only. The bot did not create a candidate or make an admission decision.",
                "",
            ]
        )
        lines.extend(
            f"- {markdown_text(change['current']['case_name'])} — {markdown_text(change['current']['docket_number'] or 'docket not stated', 100)}"
            for change in unmapped_added[:25]
        )
        if len(unmapped_added) > 25:
            lines.append(f"- {len(unmapped_added) - 25} additional unmatched additions are in the JSON report.")
    lines.extend(
        [
            "",
            "The bot reports source changes only. Human review determines relevance, controlling authority, factual meaning, and any project action.",
        ]
    )
    return "\n".join(lines) + "\n"


def report_change(change: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    entry = change_entry(change)
    return {
        "kind": change["kind"],
        "stable_key": change["key"],
        "case_name": normalize_text(entry["case_name"], 500),
        "docket_number": normalize_text(entry["docket_number"], 100),
        "courtlistener_url": entry["courtlistener_url"],
        "tracker_status": normalize_text(entry["status"], 300),
        "last_case_update": normalize_text(entry["last_case_update"], 100),
        "case_update_excerpt": normalize_text(entry.get("case_update_excerpt", ""), 800),
        "changed_fields": change.get("changed_fields", []),
        "source_matches": change.get("source_matches", []),
        "courtlistener_verification": verification_for_change(change, verification),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--pending-sources", type=Path, default=DEFAULT_PENDING_SOURCES)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--tracker-html", type=Path, help="Use a saved tracker HTML fixture.")
    parser.add_argument("--baseline-json", type=Path, help="Use a saved compact baseline for a dry run.")
    parser.add_argument("--docket-json", type=Path, help="Use CourtListener responses keyed by docket ID.")
    parser.add_argument(
        "--monitoring-issues-json", type=Path, help="Use a saved GitHub monitoring-issues array."
    )
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "Thorncrag/ARRP"))
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--checked-at")
    parser.add_argument("--apply", action="store_true", help="Update rolling GitHub state and signals.")
    parser.add_argument(
        "--refresh-github", action="store_true", help="Read the live baseline and monitoring issues without applying."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = read_json(args.config)
    if config.get("schemaVersion") != 4:
        raise SystemExit("unsupported case-monitor-bot schemaVersion")
    if not config.get("enabled", False):
        summary = "## ARRP case-monitor-bot\n\nBot disabled by configuration.\n"
        if args.summary:
            args.summary.write_text(summary, encoding="utf-8")
        print(summary, end="")
        return 0
    checked_at = args.checked_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    client = GitHubClient(args.repository, github_token()) if args.apply or args.refresh_github else None
    notification_issue = int(config["notification"]["issueNumber"])

    previous: dict[str, dict[str, str]] | None = None
    baseline_comment = None
    if args.baseline_json:
        loaded = read_json(args.baseline_json)
        previous = loaded.get("entries", loaded)
    elif client:
        baseline_comment = marked_comment(client.comments(notification_issue), BASELINE_MARKER)
        if baseline_comment:
            previous = baseline_from_comment(baseline_comment["body"])

    if args.tracker_html:
        tracker_document = args.tracker_html.read_text(encoding="utf-8")
    else:
        tracker_document = TrackerClient(config["tracker"]).fetch()
    entries = parse_tracker_html(tracker_document, config["tracker"])
    status, changes = compare_snapshots(
        previous, entries, float(config["tracker"]["maximumRemovalFraction"])
    )

    rows = [{**row, "_inventory": args.sources.name} for row in read_csv(args.sources)]
    rows.extend(
        {**row, "_inventory": args.pending_sources.name}
        for row in read_csv(args.pending_sources)
    )
    attach_source_matches(changes, source_map(rows))

    fixture = read_json(args.docket_json) if args.docket_json else None
    verification = verify_changed_dockets(
        changes,
        config["verification"],
        os.environ.get("COURTLISTENER_API_TOKEN", "").strip(),
        fixture,
    )

    if args.monitoring_issues_json:
        monitoring_issues = read_json(args.monitoring_issues_json)
    elif client:
        monitoring_issues = client.monitoring_issues(config["targetLabel"])
    else:
        monitoring_issues = []
    issue_signals = mapped_issue_signals(
        changes, registry_issue_map(read_csv(args.registry)), monitoring_issues
    )

    snapshot = compact_snapshot(entries)
    if args.apply and client:
        if issue_signals:
            client.ensure_label(
                config["reviewLabel"],
                config["reviewLabelColor"],
                config["reviewLabelDescription"],
            )
        for issue_number, signal in issue_signals.items():
            body = render_issue_signal(signal, checked_at, verification)
            existing = marked_comment(client.comments(issue_number), ISSUE_SIGNAL_MARKER)
            if existing:
                client.update_comment(int(existing["id"]), body)
            else:
                client.create_comment(issue_number, body)
            client.add_label(issue_number, config["reviewLabel"])
        # Advance the baseline only after every affected issue signal succeeds.
        # A partial GitHub failure must not suppress the same signal next run.
        baseline_body = render_baseline_comment(snapshot, checked_at, status, len(changes))
        if baseline_comment:
            client.update_comment(int(baseline_comment["id"]), baseline_body)
        else:
            client.create_comment(notification_issue, baseline_body)

    summary = render_summary(
        status=status,
        checked_at=checked_at,
        tracker_url=config["tracker"]["url"],
        entry_count=len(entries),
        changes=changes,
        verification=verification,
        mapped_signals=issue_signals,
    )
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(summary, encoding="utf-8")
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "schema_version": 4,
            "checked_at": checked_at,
            "status": status,
            "tracker_url": config["tracker"]["url"],
            "tracker_entry_count": len(entries),
            "change_counts": dict(Counter(change["kind"] for change in changes)),
            "mapped_issue_numbers": sorted(issue_signals),
            "changes": [report_change(change, verification) for change in changes],
            "repository_changes": [],
            "legal_significance_determined": False,
        }
        args.report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(summary, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
