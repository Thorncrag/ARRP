#!/usr/bin/env python3
"""Detect litigation-tracker changes and prepare source-catalog updates.

The watcher compares the Just Security Trump-administration litigation tracker with
case-specific baselines stored on monitored CourtListener rows in the source
catalogs. When an observable source changes, ``--apply`` updates those catalog fields
and appends a material event to ``framework/logs/SOURCE_MONITOR_LOG.md``. GitHub
Actions, rather than this script, commits the changes and creates or updates a narrow
review PR. Discovery of entirely new cases remains part of the separate intake scan;
this watcher does not turn unmatched tracker rows into source records.

This is source-change detection only. It does not interpret legal significance,
alter proposal analysis, or make admission or disposition decisions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html as html_lib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / ".github" / "case-monitor-bot.json"
DEFAULT_SOURCES = ROOT / "inventory" / "sources.csv"
DEFAULT_PENDING_SOURCES = ROOT / "inventory" / "sources-pending.csv"
DEFAULT_LOG = ROOT / "framework" / "logs" / "SOURCE_MONITOR_LOG.md"
USER_AGENT = "ARRP case-monitor-bot/0.3"
STATE_PREFIX = "arrp-case-monitor:v1:"


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


def read_csv_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no CSV header")
        return list(reader.fieldnames), list(reader)


def write_csv_table(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def docket_key(url: str) -> str:
    parsed = urllib.parse.urlsplit(url.strip())
    if parsed.scheme != "https" or parsed.hostname != "www.courtlistener.com":
        return ""
    match = re.search(r"/docket/(\d+)(?:/|$)", parsed.path)
    return f"courtlistener:{match.group(1)}" if match else ""


def normalize_docket_identity(value: str) -> str:
    return re.sub(r"\s+", "", normalize_text(value, 100)).casefold()


def primary_docket_key(entry: dict[str, Any] | None) -> str:
    if not entry:
        return ""
    return str(entry.get("primary_docket_key") or docket_key(str(entry.get("courtlistener_url") or "")))


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
    case_summary = normalize_text(cells["Case Summary"]["text"], 100_000)
    material = {
        "case_name": case_name or "Unnamed tracker entry",
        "docket_number": normalize_text(docket_number, 100),
        "courtlistener_url": courtlistener_url,
        "status": normalize_text(cells["Case Status"]["text"], 300),
        "last_case_update": normalize_text(cells["Last Case Update"]["text"], 100),
        "case_summary": case_summary,
        "case_updates": case_updates,
    }
    return {
        "key": key,
        "primary_docket_key": primary_key,
        **material,
        "fingerprint": fingerprint(material),
        "case_update_excerpt": normalize_text(case_updates, 800),
        "date_case_filed": normalize_text(cells["Date Case Filed"]["text"], 100),
    }


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
        entry = tracker_entry(dict(zip(headings, row)))
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
        raise ValueError(f"tracker declared {declared_total} entries but parser found {len(entries)}")
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


def expand_snapshot_entry(key: str, value: dict[str, str]) -> dict[str, str]:
    primary = key.split("|docket:", 1)[0] if key.startswith("courtlistener:") else ""
    return {
        "key": key,
        "primary_docket_key": primary,
        "case_name": value.get("n", "Removed tracker entry"),
        "docket_number": value.get("d", ""),
        "courtlistener_url": value.get("u", ""),
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


def encode_state(kind: str, payload: Any) -> str:
    return STATE_PREFIX + canonical_json({"kind": kind, "payload": payload})


def decode_state(value: str, expected_kind: str) -> Any:
    if not value.startswith(STATE_PREFIX):
        raise ValueError("unsupported monitoring-baseline format")
    payload = json.loads(value[len(STATE_PREFIX) :])
    if payload.get("kind") != expected_kind:
        raise ValueError(f"expected {expected_kind} monitoring baseline")
    return payload.get("payload")


class TrackerClient:
    def __init__(self, config: dict[str, Any]) -> None:
        parsed = urllib.parse.urlsplit(config["url"])
        if parsed.scheme != "https" or parsed.hostname not in set(config["allowedHosts"]):
            raise ValueError("tracker URL must use an allowlisted HTTPS host")
        self.url = config["url"]
        self.maximum = int(config["maximumResponseBytes"])

    def fetch(self) -> str:
        request = urllib.request.Request(
            self.url, headers={"Accept": "text/html", "User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            if response.headers.get_content_type() not in {"text/html", "application/xhtml+xml"}:
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
            raise RuntimeError(
                f"CourtListener docket {number} failed with HTTP {exc.code}"
            ) from exc
        if not isinstance(payload, dict):
            raise ValueError(f"CourtListener docket {number} returned invalid JSON")
        return payload


def source_map(rows: list[dict[str, str]]) -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = docket_key(row.get("URL", ""))
        if key:
            output[key].append(row)
    return output


def attach_source_matches(
    changes: list[dict[str, Any]], mapping: dict[str, list[dict[str, Any]]]
) -> None:
    for change in changes:
        entry = change.get("current") or change.get("previous")
        change["source_matches"] = [
            {
                "source_id": normalize_text(row.get("Source ID", ""), 100),
                "record_ids": sorted(
                    value.strip()
                    for value in row.get("Associated Record IDs", "").split(";")
                    if value.strip()
                ),
            }
            for row in mapping.get(primary_docket_key(entry), [])
        ]


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
    if not token and fixture is None:
        return {
            key: {"outcome": "unverified", "reason": "CourtListener token unavailable"}
            for key in keys
        }
    client = None if fixture is not None else CourtListenerClient(token, config["apiRoot"])
    interval = float(config.get("requestIntervalSeconds", 0))
    results: dict[str, dict[str, Any]] = {}
    queried = 0
    for key in keys:
        if key not in selected:
            results[key] = {"outcome": "unverified", "reason": "per-run verification cap reached"}
            continue
        if client is not None and queried and interval > 0:
            time.sleep(interval)
        queried += 1
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


def verification_for_change(
    change: dict[str, Any], verification: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    return verification.get(
        primary_docket_key(change.get("current")), {"outcome": "not applicable"}
    )


def require_catalog_schema(fields: list[str], baseline_field: str, path: Path) -> None:
    required = {"Source ID", "Associated Record IDs", "Monitoring", "URL", baseline_field}
    missing = sorted(required - set(fields))
    if missing:
        raise ValueError(f"{path} is missing required columns: {', '.join(missing)}")


def entries_by_docket(entries: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries.values():
        if entry["primary_docket_key"]:
            grouped[entry["primary_docket_key"]].append(entry)
    for values in grouped.values():
        values.sort(key=lambda entry: entry["key"])
    return grouped


def compact_case_baseline(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "k": entry["key"],
            "n": entry["case_name"],
            "d": entry["docket_number"],
            "u": entry["courtlistener_url"],
            "s": entry["status"],
            "l": entry["last_case_update"],
            "f": entry["fingerprint"][:32],
        }
        for entry in entries
    ]


def monitored_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("Monitoring", "").strip().casefold() == "yes" and docket_key(row.get("URL", ""))
    ]


def baseline_to_snapshot(value: str) -> dict[str, dict[str, str]]:
    observations = decode_state(value, "case")
    if not isinstance(observations, list):
        raise ValueError("case monitoring baseline must contain an observation list")
    output: dict[str, dict[str, str]] = {}
    for observation in observations:
        if not isinstance(observation, dict) or not observation.get("k"):
            raise ValueError("case monitoring baseline contains an invalid observation")
        key = str(observation["k"])
        if key in output:
            raise ValueError(f"case monitoring baseline contains duplicate identity {key}")
        output[key] = {
            "n": str(observation.get("n", "")),
            "d": str(observation.get("d", "")),
            "u": str(observation.get("u", "")),
            "s": str(observation.get("s", "")),
            "l": str(observation.get("l", "")),
            "f": str(observation.get("f", "")),
        }
    return output


def evaluate_catalog_sources(
    *,
    entries: dict[str, dict[str, Any]],
    sources_rows: list[dict[str, str]],
    pending_rows: list[dict[str, str]],
    baseline_field: str,
    initialize: bool,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    grouped = entries_by_docket(entries)
    rows = monitored_rows(sources_rows + pending_rows)
    by_docket = source_map(rows)
    mapped_keys = sorted(set(by_docket) & set(grouped))
    uncovered_keys = sorted(set(by_docket) - set(grouped))
    initialized = 0
    updated = 0
    changes_by_identity: dict[tuple[str, str], dict[str, Any]] = {}
    blank_sources: list[str] = []

    for key in mapped_keys:
        current_entries = {entry["key"]: entry for entry in grouped[key]}
        encoded = encode_state("case", compact_case_baseline(grouped[key]))
        baselines = {
            row.get(baseline_field, "").strip()
            for row in by_docket[key]
            if row.get(baseline_field, "").strip()
        }
        blank_rows = [row for row in by_docket[key] if not row.get(baseline_field, "").strip()]
        if initialize:
            for row in blank_rows:
                row[baseline_field] = encoded
                initialized += 1
            continue
        if blank_rows:
            blank_sources.extend(row.get("Source ID", "") or "unnamed source" for row in blank_rows)
            continue
        if len(baselines) != 1:
            ids = ", ".join(row.get("Source ID", "") for row in by_docket[key])
            raise ValueError(f"monitored source baselines disagree for {key}: {ids}")
        previous = baseline_to_snapshot(next(iter(baselines)))
        _, docket_changes = compare_snapshots(previous, current_entries, 1.0)
        if docket_changes:
            for row in by_docket[key]:
                if row.get(baseline_field, "") != encoded:
                    row[baseline_field] = encoded
                    updated += 1
            for change in docket_changes:
                changes_by_identity[(change["kind"], change["key"])] = change

    for key in uncovered_keys:
        rows_with_baseline = [
            row for row in by_docket[key] if row.get(baseline_field, "").strip()
        ]
        if rows_with_baseline:
            ids = ", ".join(row.get("Source ID", "") for row in rows_with_baseline)
            raise ValueError(
                f"previously mapped monitored source disappeared from the tracker ({key}: {ids})"
            )

    if blank_sources and not initialize:
        preview = ", ".join(blank_sources[:12])
        suffix = f" and {len(blank_sources) - 12} more" if len(blank_sources) > 12 else ""
        raise ValueError(
            "mapped monitored sources have blank Monitoring Baseline values; run "
            f"--initialize-baselines deliberately first: {preview}{suffix}"
        )

    changes = list(changes_by_identity.values())
    attach_source_matches(changes, by_docket)
    status = "baselines_initialized" if initialize else ("changes_detected" if changes else "no_change")
    coverage = {
        "monitored_catalog_rows": len(rows),
        "mapped_catalog_rows": sum(len(by_docket[key]) for key in mapped_keys),
        "mapped_docket_families": len(mapped_keys),
        "uncovered_catalog_rows": sum(len(by_docket[key]) for key in uncovered_keys),
        "uncovered_docket_families": len(uncovered_keys),
        "tracker_entries_outside_catalog_scope": len(entries)
        - sum(len(grouped[key]) for key in mapped_keys),
        "case_baselines_initialized": initialized,
        "case_baselines_updated": updated,
    }
    return status, changes, coverage


def change_entry(change: dict[str, Any]) -> dict[str, Any]:
    return change["current"] or change["previous"]


def render_log_entry(
    checked_at: str,
    status: str,
    changes: list[dict[str, Any]],
    coverage: dict[str, Any],
    verification: dict[str, dict[str, Any]],
) -> str:
    counts = Counter(change["kind"] for change in changes)
    verification_counts = Counter(result["outcome"] for result in verification.values())
    source_ids = sorted(
        {
            match["source_id"]
            for change in changes
            for match in change.get("source_matches", [])
            if match["source_id"]
        }
    )
    activity_hash = fingerprint(
        {"checked_at": checked_at, "changes": [(change["kind"], change["key"]) for change in changes]}
    )[:8].upper()
    date_code = re.sub(r"[^0-9]", "", checked_at)[:14]
    activity_code = f"CASE-{date_code}-{activity_hash}"
    run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
    repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    run_reference = (
        f"[{run_id}]({server}/{repository}/actions/runs/{run_id})"
        if run_id and repository
        else "Local or manually invoked run"
    )
    lines = [
        f"## {checked_at} — Case monitor bot",
        "",
        f"- Activity code: `{activity_code}`",
        f"- Originating workflow run: {run_reference}",
        f"- Result: `{status}`",
        f"- Affected source IDs: {', '.join(source_ids) or 'None'}",
        f"- Tracker changes: {counts['added']} added; {counts['changed']} changed; {counts['removed']} removed",
        f"- Case baselines updated: {coverage['case_baselines_updated']}",
        f"- Coverage: {coverage['mapped_catalog_rows']} mapped monitored CourtListener rows; {coverage['uncovered_catalog_rows']} monitored CourtListener rows outside tracker coverage",
        f"- Targeted CourtListener checks: {verification_counts['queried']} queried; {verification_counts['failed']} failed; {verification_counts['unverified']} unverified",
        "- Interpretation: source-change signal only; no legal significance or project disposition determined.",
    ]
    if changes:
        lines.extend(["", "| Change | Case | Docket | Previous observation | Current observation | Catalog match |", "| --- | --- | --- | --- | --- | --- |"])
        for change in changes[:100]:
            entry = change_entry(change)
            previous = change.get("previous") or {}
            current = change.get("current") or {}
            previous_observation = "; ".join(
                part for part in [previous.get("status", ""), previous.get("last_case_update", "")] if part
            ) or "Not present"
            current_observation = "; ".join(
                part for part in [current.get("status", ""), current.get("last_case_update", "")] if part
            ) or "Not present"
            matches = ", ".join(
                match["source_id"] for match in change.get("source_matches", []) if match["source_id"]
            ) or "None"
            lines.append(
                f"| {markdown_text(change['kind'].title(), 20)} | {markdown_text(entry['case_name'])} | "
                f"{markdown_text(entry['docket_number'] or 'Not stated', 100)} | "
                f"{markdown_text(previous_observation, 250)} | {markdown_text(current_observation, 250)} | "
                f"{markdown_text(matches, 250)} |"
            )
        if len(changes) > 100:
            lines.append(f"\n{len(changes) - 100} additional changes are retained in the workflow artifact.")
    return "\n".join(lines) + "\n\n"


def append_material_log(path: Path, entry: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = (
            '---\ntitle: "Source Monitor Log"\nprint_levels:\n  - full-technical\n---\n\n'
            "# Source Monitor Log\n\nMaterial source-monitor activity is recorded here; "
            "routine no-change runs remain in GitHub Actions.\n\n"
        )
    separator = "" if existing.endswith("\n") else "\n"
    path.write_text(existing + separator + entry, encoding="utf-8")


def render_summary(
    *,
    status: str,
    checked_at: str,
    tracker_url: str,
    entry_count: int,
    changes: list[dict[str, Any]],
    verification: dict[str, dict[str, Any]],
    coverage: dict[str, Any],
    applied: bool,
) -> str:
    counts = Counter(change["kind"] for change in changes)
    verification_counts = Counter(result["outcome"] for result in verification.values())
    affected_source_ids = sorted(
        {
            match["source_id"]
            for change in changes
            for match in change.get("source_matches", [])
            if match.get("source_id")
        }
    )
    lines = [
        "## ARRP case-monitor-bot",
        "",
        f"Checked at: **{checked_at}**  ",
        f"Tracker: [Just Security litigation tracker]({tracker_url})  ",
        f"Parsed tracker entries: **{entry_count}**  ",
        f"Result: **{status.replace('_', ' ')}**",
        "",
        "### Source observations",
        "",
        f"- Added tracker entries: **{counts['added']}**",
        f"- Changed tracker entries: **{counts['changed']}**",
        f"- Removed tracker entries: **{counts['removed']}**",
        f"- Eligible monitored CourtListener rows: **{coverage['monitored_catalog_rows']}**",
        f"- Mapped monitored CourtListener rows: **{coverage['mapped_catalog_rows']}**",
        f"- Monitored CourtListener rows outside tracker coverage: **{coverage['uncovered_catalog_rows']}**",
        f"- Tracker entries outside catalog-monitor scope: **{coverage['tracker_entries_outside_catalog_scope']}**",
        f"- Case baselines initialized: **{coverage['case_baselines_initialized']}**",
        f"- Case baselines updated: **{coverage['case_baselines_updated']}**",
        f"- Affected source IDs: **{', '.join(affected_source_ids) or 'None'}**",
        "",
        "### Targeted CourtListener checks",
        "",
        f"- Queried: **{verification_counts['queried']}**",
        f"- Failed: **{verification_counts['failed']}**",
        f"- Unverified: **{verification_counts['unverified']}**",
    ]
    if status == "no_change":
        lines.extend(["", "No repository update or pull request is needed."])
    elif status == "baselines_initialized":
        lines.extend(
            [
                "",
                "Deliberate local initialization only. Blank baselines were populated without classifying any observation as a change; this mode must not create an automated monitoring PR.",
            ]
        )
    elif applied:
        lines.extend(
            [
                "",
                "Catalog and material-log updates were prepared in the worktree. The workflow will commit them to the deterministic bot branch and create or update a review pull request.",
            ]
        )
    else:
        lines.extend(["", "Dry run only; no repository files were changed."])
    if changes:
        lines.extend(
            [
                "",
                "| Change | Case | Docket | Status | Last case update | Catalog source | CourtListener |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for change in changes[:40]:
            entry = change_entry(change)
            source_ids = ", ".join(
                match["source_id"] for match in change.get("source_matches", []) if match["source_id"]
            ) or "None"
            lines.append(
                f"| {markdown_text(change['kind'].title(), 20)} | {markdown_text(entry['case_name'])} | "
                f"{markdown_text(entry['docket_number'] or 'Not stated', 100)} | "
                f"{markdown_text(entry['status'] or 'Not stated', 200)} | "
                f"{markdown_text(entry['last_case_update'] or 'Not stated', 100)} | "
                f"{markdown_text(source_ids, 200)} | "
                f"{markdown_text(verification_for_change(change, verification)['outcome'], 50)} |"
            )
        if len(changes) > 40:
            lines.append(f"\n{len(changes) - 40} additional changes are retained in the JSON artifact.")
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
        "changed_fields": change.get("changed_fields", []),
        "source_matches": change.get("source_matches", []),
        "courtlistener_verification": verification_for_change(change, verification),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--pending-sources", type=Path, default=DEFAULT_PENDING_SOURCES)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--tracker-html", type=Path, help="Use a saved tracker HTML fixture.")
    parser.add_argument("--docket-json", type=Path, help="Use CourtListener responses keyed by docket ID.")
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--checked-at")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changed catalog baselines and append the material source-monitor log.",
    )
    parser.add_argument(
        "--initialize-baselines",
        action="store_true",
        help="Deliberately populate blank baselines for currently mapped monitored sources; writes catalogs but does not log a detected change.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.apply and args.initialize_baselines:
        raise SystemExit("--apply and --initialize-baselines are separate modes")
    config = read_json(args.config)
    if config.get("schemaVersion") != 5:
        raise SystemExit("unsupported case-monitor-bot schemaVersion")
    if not config.get("enabled", False):
        summary = "## ARRP case-monitor-bot\n\nBot disabled by configuration.\n"
        if args.summary:
            args.summary.write_text(summary, encoding="utf-8")
        print(summary, end="")
        return 0
    checked_at = args.checked_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    baseline_field = config["sourceBaselineField"]
    source_fields, source_rows = read_csv_table(args.sources)
    pending_fields, pending_rows = read_csv_table(args.pending_sources)
    require_catalog_schema(source_fields, baseline_field, args.sources)
    require_catalog_schema(pending_fields, baseline_field, args.pending_sources)
    tracker_document = (
        args.tracker_html.read_text(encoding="utf-8")
        if args.tracker_html
        else TrackerClient(config["tracker"]).fetch()
    )
    entries = parse_tracker_html(tracker_document, config["tracker"])
    status, changes, coverage = evaluate_catalog_sources(
        entries=entries,
        sources_rows=source_rows,
        pending_rows=pending_rows,
        baseline_field=baseline_field,
        initialize=args.initialize_baselines,
    )
    fixture = read_json(args.docket_json) if args.docket_json else None
    verification = verify_changed_dockets(
        changes,
        config["verification"],
        os.environ.get("COURTLISTENER_API_TOKEN", "").strip(),
        fixture,
    )

    material = status == "changes_detected"
    should_write_catalogs = (args.apply and material) or args.initialize_baselines
    if should_write_catalogs:
        write_csv_table(args.sources, source_fields, source_rows)
        write_csv_table(args.pending_sources, pending_fields, pending_rows)
    if args.apply and material:
        append_material_log(
            args.log,
            render_log_entry(checked_at, status, changes, coverage, verification),
        )

    summary = render_summary(
        status=status,
        checked_at=checked_at,
        tracker_url=config["tracker"]["url"],
        entry_count=len(entries),
        changes=changes,
        verification=verification,
        coverage=coverage,
        applied=args.apply and material,
    )
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(summary, encoding="utf-8")
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "schema_version": 5,
            "checked_at": checked_at,
            "status": status,
            "tracker_url": config["tracker"]["url"],
            "tracker_entry_count": len(entries),
            "change_counts": dict(Counter(change["kind"] for change in changes)),
            "changes": [report_change(change, verification) for change in changes],
            "coverage": coverage,
            "repository_changes_prepared": args.apply and material,
            "baseline_initialization_mode": args.initialize_baselines,
            "legal_significance_determined": False,
        }
        args.report_json.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(summary, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
