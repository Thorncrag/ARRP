#!/usr/bin/env python3
"""Deterministically check cataloged source URLs without modifying citations."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import socket
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

try:
    from console_data_contracts import (
        feed_contract,
        source_hashes,
        source_revision,
        utc_timestamp,
    )
except ModuleNotFoundError:
    from scripts.console_data_contracts import (
        feed_contract,
        source_hashes,
        source_revision,
        utc_timestamp,
    )

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "framework/project/automation/configuration/bots/source-checker-bot.json"
USER_AGENT = "ARRP source-checker-bot/1.0 (+https://github.com/Thorncrag/ARRP)"
CLASSIFICATIONS = {
    "verified", "identity-preserving redirect", "access restricted",
    "transient failure", "broken", "identity mismatch", "review required",
}
GOOD_CLASSIFICATIONS = {"verified", "identity-preserving redirect"}
CLASSIFICATION_RANK = {
    "verified": 0,
    "identity-preserving redirect": 0,
    "access restricted": 1,
    "transient failure": 1,
    "review required": 2,
    "broken": 3,
    "identity mismatch": 3,
}
ACCESS_CODES = {401, 403, 407, 429}
BROKEN_CODES = {404, 410}
TRANSIENT_CODES = {408, 425, 500, 502, 503, 504}
ID_PATTERNS = [
    re.compile(r"\b(?:H\.?R\.?|S\.?|H\.?J\.?\s*Res\.?|S\.?J\.?\s*Res\.?)\s*\d+\b", re.I),
    re.compile(r"\b(?:No\.?\s*)?\d{1,2}:\d{2}-(?:cv|cr|mc|md|bk|ap)-\d+\b", re.I),
    re.compile(r"\b(?:Pub\.?\s*L\.?\s*(?:No\.?)?\s*)\d+-\d+\b", re.I),
    re.compile(r"\b\d+\s+U\.?S\.?C\.?\s*(?:§|sec(?:tion)?\.?)?\s*\d+[A-Za-z0-9-]*\b", re.I),
    re.compile(r"\b[A-Z]{2,12}-\d{4}-\d{2,5}\b"),
]


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title": self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title": self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title: self.parts.append(data)

    def title(self) -> str:
        return normalize(" ".join(self.parts), 500)


def normalize(value: str, limit: int = 1000) -> str:
    return " ".join(value.replace("\xa0", " ").split())[:limit]


def tokens(value: str) -> set[str]:
    stop = {"the", "and", "for", "with", "from", "that", "this", "of", "to", "a", "an", "in", "on", "or"}
    return {x for x in re.findall(r"[a-z0-9]{3,}", value.casefold()) if x not in stop}


def stable_ids(value: str) -> set[str]:
    found: set[str] = set()
    for pattern in ID_PATTERNS:
        found.update(re.sub(r"[^a-z0-9]", "", match.casefold()) for match in pattern.findall(value))
    return found


class DomainPacer:
    def __init__(self, interval: float) -> None:
        self.interval = interval
        self.lock = threading.Lock()
        self.next_at: dict[str, float] = {}

    def wait(self, url: str) -> None:
        domain = urllib.parse.urlsplit(url).hostname or ""
        with self.lock:
            now = time.monotonic()
            delay = max(0.0, self.next_at.get(domain, now) - now)
            self.next_at[domain] = max(now, self.next_at.get(domain, now)) + self.interval
        if delay: time.sleep(delay)


def classify(row: dict[str, str], observation: dict[str, Any]) -> str:
    code = observation.get("status_code")
    if observation.get("error_kind") == "access" or code in ACCESS_CODES:
        return "access restricted"
    if observation.get("error_kind") == "transient" or code in TRANSIENT_CODES:
        return "transient failure"
    if code in BROKEN_CODES:
        return "broken"
    if not isinstance(code, int) or not 200 <= code < 400:
        return "review required"
    expected = normalize(f'{row.get("Title or Description", "")} {row.get("Authority / Publisher", "")}', 2000)
    observed = normalize(f'{observation.get("title", "")} {observation.get("final_url", "")}', 2000)
    expected_ids, observed_ids = stable_ids(expected), stable_ids(observed)
    if expected_ids and observed_ids and not (expected_ids & observed_ids):
        return "identity mismatch"
    if expected_ids and not observed_ids:
        return "review required"
    redirected = observation.get("final_url", "") != row.get("URL", "").strip()
    if redirected:
        overlap = tokens(expected) & tokens(observed)
        return "identity-preserving redirect" if expected_ids & observed_ids or len(overlap) >= 2 else "review required"
    if expected_ids and expected_ids & observed_ids:
        return "verified"
    if observation.get("content_type", "").startswith(("text/html", "application/pdf", "text/plain")):
        return "verified"
    return "review required"


def fetch(row: dict[str, str], settings: dict[str, Any], pacer: DomainPacer) -> dict[str, Any]:
    url = row["URL"].strip()
    retries = int(settings["retries"])
    result: dict[str, Any] = {"requested_url": url, "attempts": 0}
    for attempt in range(retries + 1):
        result["attempts"] = attempt + 1
        pacer.wait(url)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,text/plain,*/*;q=0.2"})
        try:
            with urllib.request.urlopen(request, timeout=float(settings["timeoutSeconds"])) as response:
                body = response.read(int(settings["maximumBytes"]))
                content_type = response.headers.get_content_type()
                title = ""
                if content_type == "text/html":
                    parser = TitleParser()
                    parser.feed(body.decode(response.headers.get_content_charset() or "utf-8", errors="replace"))
                    title = parser.title()
                result.update(status_code=response.status, final_url=response.geturl(), content_type=content_type, title=title, error="", error_kind="")
                break
        except urllib.error.HTTPError as exc:
            kind = "access" if exc.code in ACCESS_CODES else "transient" if exc.code in TRANSIENT_CODES else "http"
            result.update(status_code=exc.code, final_url=exc.geturl() or url, content_type=exc.headers.get_content_type() if exc.headers else "", title="", error=f"HTTP {exc.code}", error_kind=kind)
            if kind != "transient" or attempt == retries: break
        except (urllib.error.URLError, TimeoutError, socket.timeout, ssl.SSLError) as exc:
            result.update(status_code=None, final_url=url, content_type="", title="", error=normalize(str(exc.reason if isinstance(exc, urllib.error.URLError) else exc), 300), error_kind="transient")
            if attempt == retries: break
        if attempt < retries: time.sleep(float(settings["backoffSeconds"]) * (2 ** attempt))
    result["classification"] = classify(row, result)
    return result


def load_rows(config: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen_ids: dict[str, str] = {}
    for relative in config["catalogs"]:
        path = ROOT / relative
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            required = {config["idField"], config["urlField"], config["titleField"], config["publisherField"]}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ValueError(f"{relative} lacks required source-checker fields")
            for number, row in enumerate(reader, 2):
                if row[config["urlField"]].strip():
                    source_id = row[config["idField"]].strip()
                    if not source_id:
                        raise ValueError(
                            f"{relative}:{number} has a URL but no source identifier"
                        )
                    if source_id in seen_ids:
                        raise ValueError(
                            "duplicate source identifier {} in {} and {}".format(
                                source_id,
                                seen_ids[source_id],
                                f"{relative}:{number}",
                            )
                        )
                    seen_ids[source_id] = f"{relative}:{number}"
                    item = dict(row); item["catalog"] = relative; item["catalog_row"] = str(number)
                    rows.append(item)
    return rows


def build_report(config: dict[str, Any], rows: list[dict[str, str]], now: str) -> dict[str, Any]:
    pacer = DomainPacer(float(config["request"]["minimumDomainIntervalSeconds"]))
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=int(config["request"]["workers"])) as pool:
        futures = {pool.submit(fetch, row, config["request"], pacer): row for row in rows}
        for future in as_completed(futures):
            row, observation = futures[future], future.result()
            results.append({
                "source_id": row[config["idField"]], "catalog": row["catalog"],
                "catalog_row": int(row["catalog_row"]), "title": normalize(row[config["titleField"]], 500),
                **observation,
            })
    results.sort(key=lambda x: (x["catalog"], x["catalog_row"]))
    counts = Counter(item["classification"] for item in results)
    expected_ids = [row[config["idField"]].strip() for row in rows]
    actual_ids = [str(item.get("source_id") or "").strip() for item in results]
    expected_id_set = set(expected_ids)
    actual_id_set = set(actual_ids)
    missing_ids = sorted(expected_id_set - actual_id_set)
    unexpected_ids = sorted(actual_id_set - expected_id_set)
    duplicate_result_ids = sorted(
        identifier
        for identifier, count in Counter(actual_ids).items()
        if identifier and count > 1
    )
    projection_errors: list[dict[str, Any]] = []
    for identifier in missing_ids:
        projection_errors.append(
            {
                "code": "missing_source_result",
                "severity": "error",
                "source_id": identifier,
                "message": "Current catalog URL has no checker result.",
            }
        )
    for identifier in unexpected_ids:
        projection_errors.append(
            {
                "code": "unexpected_source_result",
                "severity": "error",
                "source_id": identifier,
                "message": "Checker result does not belong to the current catalog scope.",
            }
        )
    for identifier in duplicate_result_ids:
        projection_errors.append(
            {
                "code": "duplicate_source_result",
                "severity": "error",
                "source_id": identifier,
                "message": "Current checker result contains a duplicate source identifier.",
            }
        )
    checked_at = utc_timestamp(now)
    hashes = source_hashes(ROOT, [ROOT / path for path in config["catalogs"]])
    contract = feed_contract(
        feed_name="source-checker",
        timestamp_field="checked_at",
        timestamp=checked_at,
        revision=source_revision(ROOT),
        hashes=hashes,
        expected_count=len(expected_ids),
        actual_count=len(actual_ids),
        pagination={
            "complete": True,
            "sources": [
                {
                    "source": relative,
                    "complete": True,
                    "expected_count": sum(
                        1 for row in rows if row["catalog"] == relative
                    ),
                    "actual_count": sum(
                        1 for item in results if item["catalog"] == relative
                    ),
                }
                for relative in config["catalogs"]
            ],
        },
        projection_errors=projection_errors,
    )
    contract["freshness"] = {
        "status": contract["availability"],
        "basis": "source catalog identity coverage and content hashes",
        "supersession_rule": (
            "Any source catalog identity or content-hash change supersedes "
            "this checker generation immediately."
        ),
    }
    catalog_coverage = []
    for relative in config["catalogs"]:
        catalog_expected = [
            row[config["idField"]].strip()
            for row in rows
            if row["catalog"] == relative
        ]
        catalog_actual = [
            str(item.get("source_id") or "").strip()
            for item in results
            if item["catalog"] == relative
        ]
        catalog_coverage.append(
            {
                "catalog": relative,
                "source_hash": hashes.get(relative),
                "expected_count": len(catalog_expected),
                "actual_count": len(catalog_actual),
                "missing_ids": sorted(set(catalog_expected) - set(catalog_actual)),
                "complete": (
                    len(catalog_expected) == len(catalog_actual)
                    and set(catalog_expected) == set(catalog_actual)
                ),
            }
        )
    return {
        "schema_version": 2,
        "agent_id": config["agentId"],
        "mode": config["mode"],
        **contract,
        "catalogs": config["catalogs"],
        "catalog_coverage": catalog_coverage,
        "eligible_urls": len(rows),
        "missing_source_ids": missing_ids,
        "unexpected_source_ids": unexpected_ids,
        "duplicate_result_ids": duplicate_result_ids,
        "counts": {
            key: counts.get(key, 0) for key in sorted(CLASSIFICATIONS)
        },
        "results": results,
    }


def source_result_deltas(
    report: dict[str, Any],
    prior: dict[str, Any] | None,
) -> dict[str, Any]:
    current_results = report.get("results")
    if not isinstance(current_results, list):
        return {
            "available": False,
            "reason": "Current report does not contain per-source results.",
        }
    if (
        not isinstance(prior, dict)
        or not isinstance(prior.get("results"), list)
        or not str(prior.get("checked_at") or "").strip()
    ):
        return {
            "available": False,
            "reason": "No comparable prior per-source baseline is available.",
            "baseline_checked_at": (
                prior.get("checked_at") if isinstance(prior, dict) else None
            ),
        }

    def indexed(results: list[Any]) -> dict[str, dict[str, Any]] | None:
        index: dict[str, dict[str, Any]] = {}
        for item in results:
            if not isinstance(item, dict):
                return None
            identifier = str(item.get("source_id") or "").strip()
            classification = str(item.get("classification") or "").strip()
            if (
                not identifier
                or classification not in CLASSIFICATIONS
                or identifier in index
            ):
                return None
            index[identifier] = item
        return index

    current_by_id = indexed(current_results)
    prior_by_id = indexed(prior["results"])
    if current_by_id is None or prior_by_id is None:
        return {
            "available": False,
            "reason": "Current or prior per-source results violate identity/classification requirements.",
            "baseline_checked_at": prior.get("checked_at"),
        }
    current_time = datetime.fromisoformat(
        str(report["checked_at"]).replace("Z", "+00:00")
    ).astimezone(timezone.utc)
    baseline_time = datetime.fromisoformat(
        str(prior["checked_at"]).replace("Z", "+00:00")
    ).astimezone(timezone.utc)
    new_exceptions: list[str] = []
    regressed: list[str] = []
    resolved: list[str] = []
    ongoing: list[str] = []
    changed: list[dict[str, str]] = []
    aging: list[dict[str, Any]] = []
    for identifier, current in current_by_id.items():
        classification = str(current["classification"])
        previous = prior_by_id.get(identifier)
        previous_classification = (
            str(previous.get("classification") or "") if previous else ""
        )
        current_exception = classification not in GOOD_CLASSIFICATIONS
        previous_exception = (
            bool(previous)
            and previous_classification not in GOOD_CLASSIFICATIONS
        )
        if current_exception:
            if previous is None:
                new_exceptions.append(identifier)
                first_seen = str(report["checked_at"])
            elif not previous_exception:
                regressed.append(identifier)
                first_seen = str(report["checked_at"])
            else:
                ongoing.append(identifier)
                first_seen = str(
                    previous.get("exception_first_seen_at")
                    or prior.get("checked_at")
                )
                if classification != previous_classification:
                    changed.append(
                        {
                            "source_id": identifier,
                            "from": previous_classification,
                            "to": classification,
                            "direction": (
                                "regressed"
                                if CLASSIFICATION_RANK[classification]
                                > CLASSIFICATION_RANK[previous_classification]
                                else "improved"
                                if CLASSIFICATION_RANK[classification]
                                < CLASSIFICATION_RANK[previous_classification]
                                else "changed"
                            ),
                        }
                    )
                    if (
                        CLASSIFICATION_RANK[classification]
                        > CLASSIFICATION_RANK[previous_classification]
                    ):
                        regressed.append(identifier)
            try:
                first_seen_time = datetime.fromisoformat(
                    first_seen.replace("Z", "+00:00")
                ).astimezone(timezone.utc)
            except ValueError:
                first_seen = str(report["checked_at"])
                first_seen_time = current_time
            current["exception_first_seen_at"] = first_seen
            age_seconds = max(
                int((current_time - first_seen_time).total_seconds()), 0
            )
            current["exception_age_days"] = round(age_seconds / 86400.0, 2)
            aging.append(
                {
                    "source_id": identifier,
                    "classification": classification,
                    "previous_classification": previous_classification or None,
                    "first_seen_at": first_seen,
                    "age_days": current["exception_age_days"],
                }
            )
        elif previous_exception:
            resolved.append(identifier)
    left_scope = sorted(set(prior_by_id) - set(current_by_id))
    entered_scope = sorted(set(current_by_id) - set(prior_by_id))
    return {
        "available": True,
        "baseline_checked_at": prior.get("checked_at"),
        "baseline_source_revision": prior.get("source_revision"),
        "elapsed_days": round(
            max((current_time - baseline_time).total_seconds(), 0) / 86400.0,
            2,
        ),
        "new_exception_ids": sorted(set(new_exceptions)),
        "regressed_exception_ids": sorted(set(regressed)),
        "resolved_exception_ids": sorted(set(resolved)),
        "ongoing_exception_ids": sorted(set(ongoing)),
        "changed_exceptions": sorted(
            changed, key=lambda item: item["source_id"]
        ),
        "aging_exceptions": sorted(
            aging,
            key=lambda item: (-float(item["age_days"]), item["source_id"]),
        ),
        "entered_scope_ids": entered_scope,
        "left_scope_ids": left_scope,
        "counts": {
            "new_exceptions": len(set(new_exceptions)),
            "regressed_exceptions": len(set(regressed)),
            "resolved_exceptions": len(set(resolved)),
            "ongoing_exceptions": len(set(ongoing)),
            "entered_scope": len(entered_scope),
            "left_scope": len(left_scope),
        },
    }


def with_history(report: dict[str, Any], existing: Path | None, limit: int) -> dict[str, Any]:
    history: list[dict[str, Any]] = []
    prior_payload: dict[str, Any] | None = None
    if existing:
        if not existing.is_file():
            raise RuntimeError(
                "Prior Source Checker history was requested but is unavailable: "
                + str(existing)
            )
        try:
            payload = json.loads(existing.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise RuntimeError(
                "Prior Source Checker history is unreadable; refusing to erase it."
            ) from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("history"), list):
            raise RuntimeError(
                "Prior Source Checker history does not satisfy the history contract."
            )
        history = list(payload["history"])
        if any(
            not isinstance(item, dict) or not str(item.get("checked_at") or "").strip()
            for item in history
        ):
            raise RuntimeError(
                "Prior Source Checker history contains an invalid snapshot."
            )
        prior_payload = payload
    report["deltas"] = source_result_deltas(report, prior_payload)
    summary = {
        key: report[key]
        for key in (
            "checked_at",
            "generation_id",
            "source_revision",
            "source_hashes",
            "expected_count",
            "actual_count",
            "completeness",
            "eligible_urls",
            "missing_source_ids",
            "counts",
            "deltas",
        )
        if key in report
    }
    if isinstance(report.get("deltas"), dict):
        summary["deltas"] = {
            "available": report["deltas"].get("available"),
            "counts": report["deltas"].get("counts"),
            "baseline_checked_at": report["deltas"].get(
                "baseline_checked_at"
            ),
        }
    report["history"] = ([summary] + [item for item in history if item.get("checked_at") != report["checked_at"]])[:limit]
    return report


def markdown(report: dict[str, Any]) -> str:
    lines = ["---", 'title: "Source Checker Bot Current Report"', "print_status: excluded", 'print_exclusion_reason: "Replaceable internal automation report."', "---", "", "# Source Checker Bot Current Report", "", "> This replaceable snapshot changes only when the classified result set changes. Run timestamps and bounded history remain in the Project Console data feed and GitHub Actions.", "", f"Mode: **{report['mode']}**", f"Eligible URLs: **{report['eligible_urls']}**", "", "## Results", "", "| Classification | Count |", "|---|---:|"]
    for name, count in report["counts"].items(): lines.append(f"| {name} | {count} |")
    exceptions = [x for x in report["results"] if x["classification"] not in {"verified", "identity-preserving redirect"}]
    lines += ["", "## Exceptions requiring attention", ""]
    if not exceptions: lines.append("No exceptions.")
    else:
        lines += ["| Source | Classification | HTTP | Detail |", "|---|---|---:|---|"]
        for item in exceptions:
            detail = item.get("error") or item.get("final_url") or "—"
            detail = html.escape(normalize(detail, 180)).replace("|", "&#124;")
            lines.append(f"| {item['source_id']} | {item['classification']} | {item.get('status_code') or '—'} | {detail} |")
    lines += ["", "This report is diagnostic. The bot did not modify or substitute any cataloged source.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--existing-json", type=Path)
    parser.add_argument("--limit", type=int, help="Test or diagnostic limit; omitted means every URL")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if config.get("mode") != "report-only": raise ValueError("source-checker-bot must remain report-only")
    rows = load_rows(config)
    if args.limit is not None: rows = rows[:args.limit]
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    report = with_history(build_report(config, rows, now), args.existing_json, int(config["historyLimit"]))
    json_path = args.json_output or ROOT / config["currentData"]
    md_path = args.markdown_output or ROOT / config["currentReport"]
    json_path.parent.mkdir(parents=True, exist_ok=True); md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"checked": len(rows), "counts": report["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
