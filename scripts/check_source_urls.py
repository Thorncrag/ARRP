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

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / ".github" / "source-checker-bot.json"
USER_AGENT = "ARRP source-checker-bot/1.0 (+https://github.com/Thorncrag/ARRP)"
CLASSIFICATIONS = {
    "verified", "identity-preserving redirect", "access restricted",
    "transient failure", "broken", "identity mismatch", "review required",
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
    for relative in config["catalogs"]:
        path = ROOT / relative
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            required = {config["idField"], config["urlField"], config["titleField"], config["publisherField"]}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ValueError(f"{relative} lacks required source-checker fields")
            for number, row in enumerate(reader, 2):
                if row[config["urlField"]].strip():
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
    return {"schema_version": 1, "agent_id": config["agentId"], "mode": config["mode"], "checked_at": now,
            "catalogs": config["catalogs"], "eligible_urls": len(rows), "counts": {key: counts.get(key, 0) for key in sorted(CLASSIFICATIONS)}, "results": results}


def with_history(report: dict[str, Any], existing: Path | None, limit: int) -> dict[str, Any]:
    history: list[dict[str, Any]] = []
    if existing and existing.exists():
        try: history = list(json.loads(existing.read_text(encoding="utf-8")).get("history", []))
        except (ValueError, OSError): history = []
    summary = {key: report[key] for key in ("checked_at", "eligible_urls", "counts")}
    report["history"] = ([summary] + [item for item in history if item.get("checked_at") != report["checked_at"]])[:limit]
    return report


def markdown(report: dict[str, Any]) -> str:
    lines = ["---", 'title: "Source Checker Bot Current Report"', "print_status: excluded", 'print_exclusion_reason: "Replaceable internal automation report."', "---", "", "# Source Checker Bot Current Report", "", "> This replaceable snapshot changes only when the classified result set changes. Run timestamps and bounded history remain in the Project Console data feed and GitHub Actions.", "", f"Mode: **{report['mode']}**  ", f"Eligible URLs: **{report['eligible_urls']}**", "", "## Results", "", "| Classification | Count |", "|---|---:|"]
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
