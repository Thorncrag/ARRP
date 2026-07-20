#!/usr/bin/env python3
"""Deterministically check configured ARRP monitoring records for source changes.

The prototype is deliberately signal-only. It compares structured source fields with
the previously observed baseline stored in one rolling GitHub issue comment. It
does not interpret legal significance, revise project prose, or alter proposal
status, scores, audit counts, source inventories, or monitoring dispositions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html as html_lib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / ".github" / "monitoring-pilot.json"
DEFAULT_REGISTRY = ROOT / "inventory" / "github_issue_registry.csv"
DEFAULT_SOURCES = ROOT / "inventory" / "sources.csv"
DEFAULT_PENDING_SOURCES = ROOT / "inventory" / "sources-pending.csv"
STATE_MARKER = "arrp-monitor-bot-state:v1"
USER_AGENT = "ARRP deterministic monitoring prototype/0.2"


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def markdown_cell(value: str) -> str:
    value = html_lib.escape(normalize_text(value)[:500], quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|>-])", r"\\\1", value)


def safe_error(value: str) -> str:
    return normalize_text(value).replace("--", "—").replace("<", "[").replace(">", "]")[:500]


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class TablePressParser(HTMLParser):
    """Extract headers, text, and links from one TablePress table."""

    def __init__(self, table_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self.table_id = table_id
        self.in_table = False
        self.table_depth = 0
        self.section = ""
        self.in_row = False
        self.cell_tag = ""
        self.cell_text: list[str] = []
        self.cell_links: list[str] = []
        self.row_cells: list[dict[str, Any]] = []
        self.headers: list[str] = []
        self.rows: list[dict[str, dict[str, Any]]] = []

    @staticmethod
    def attrs_dict(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key: value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = self.attrs_dict(attrs)
        if tag == "table" and not self.in_table and values.get("id") == self.table_id:
            self.in_table = True
            self.table_depth = 1
            return
        if not self.in_table:
            return
        if tag == "table":
            self.table_depth += 1
        elif tag in {"thead", "tbody"}:
            self.section = tag
        elif tag == "tr":
            self.in_row = True
            self.row_cells = []
        elif self.in_row and tag in {"th", "td"}:
            self.cell_tag = tag
            self.cell_text = []
            self.cell_links = []
        elif self.cell_tag and tag == "a" and values.get("href"):
            self.cell_links.append(values["href"])

    def handle_data(self, data: str) -> None:
        if self.in_table and self.cell_tag:
            self.cell_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.in_table:
            return
        if self.cell_tag and tag == self.cell_tag:
            self.row_cells.append(
                {
                    "text": normalize_text(" ".join(self.cell_text)),
                    "links": list(dict.fromkeys(self.cell_links)),
                }
            )
            self.cell_tag = ""
            self.cell_text = []
            self.cell_links = []
            return
        if tag == "tr" and self.in_row:
            if self.section == "thead" and self.row_cells:
                self.headers = [cell["text"] for cell in self.row_cells]
            elif self.section == "tbody" and self.headers and len(self.row_cells) == len(self.headers):
                self.rows.append(dict(zip(self.headers, self.row_cells, strict=True)))
            self.in_row = False
            self.row_cells = []
        elif tag in {"thead", "tbody"}:
            self.section = ""
        elif tag == "table":
            self.table_depth -= 1
            if self.table_depth == 0:
                self.in_table = False


def parse_just_security(html_text: str) -> dict[str, dict[str, Any]]:
    parser = TablePressParser("tablepress-42")
    parser.feed(html_text)
    if not parser.headers or not parser.rows:
        raise ValueError("Just Security tablepress-42 was not found or contained no rows")
    required = {"Case Name", "Case Status", "Executive Action", "Last Case Update", "Case Updates"}
    missing = required - set(parser.headers)
    if missing:
        raise ValueError("Just Security table is missing required columns: " + ", ".join(sorted(missing)))

    grouped: dict[str, list[dict[str, dict[str, Any]]]] = defaultdict(list)
    for row in parser.rows:
        action = row["Executive Action"]["text"]
        if action:
            grouped[action].append(row)

    observations: dict[str, dict[str, Any]] = {}
    for action, rows in grouped.items():
        statuses = Counter(row["Case Status"]["text"] or "Unspecified" for row in rows)
        cases: list[dict[str, str]] = []
        for row in rows:
            case_links = [
                link for link in row["Case Name"]["links"] if "courtlistener.com/docket/" in link
            ]
            cases.append(
                {
                    "case": row["Case Name"]["text"],
                    "status": row["Case Status"]["text"] or "Unspecified",
                    "last_update": row["Last Case Update"]["text"],
                    "docket_url": case_links[0] if case_links else "",
                    "updates_hash": fingerprint(row["Case Updates"]["text"]),
                }
            )
        cases.sort(key=lambda item: (item["case"], item["docket_url"]))
        material = {
            "action": action,
            "case_count": len(cases),
            "statuses": dict(sorted(statuses.items())),
            "last_update": max((case["last_update"] for case in cases), default=""),
            "cases": cases,
        }
        observations[action] = {
            **material,
            "status_summary": "; ".join(
                f"{status}={count}" for status, count in sorted(statuses.items())
            ),
            "fingerprint": fingerprint(material),
        }
    return observations


def docket_key(url: str) -> str:
    """Return a stable CourtListener docket key without query or slug variance."""
    parsed = urllib.parse.urlsplit(url.strip())
    if parsed.hostname != "www.courtlistener.com":
        return ""
    match = re.search(r"/docket/(\d+)(?:/|$)", parsed.path)
    return f"courtlistener:{match.group(1)}" if match else ""


def tracker_cases_by_docket(
    action_observations: dict[str, dict[str, Any]],
) -> dict[str, dict[str, str]]:
    """Flatten the tracker into source-level docket observations."""
    output: dict[str, dict[str, str]] = {}
    for action, observation in action_observations.items():
        for case in observation["cases"]:
            key = docket_key(case["docket_url"])
            if not key:
                continue
            material = {
                "action": action,
                "case": case["case"],
                "status": case["status"],
                "last_update": case["last_update"],
                "docket_url": case["docket_url"],
                "updates_hash": case["updates_hash"],
            }
            material["fingerprint"] = fingerprint(material)
            output[key] = material
    return output


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_source_url(source: dict[str, Any]) -> None:
    parsed = urllib.parse.urlsplit(source["url"])
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("monitoring source must use an absolute HTTPS URL")
    if parsed.hostname not in set(source.get("allowedHosts", [])):
        raise ValueError(f"monitoring source host is not allowlisted: {parsed.hostname}")


def fetch_source(source: dict[str, Any]) -> str:
    validate_source_url(source)
    request = urllib.request.Request(
        source["url"],
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": USER_AGENT,
        },
    )
    maximum = int(source.get("maximumBytes", 8 * 1024 * 1024))
    with urllib.request.urlopen(request, timeout=30) as response:
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError(f"unexpected monitoring source content type: {content_type}")
        payload = response.read(maximum + 1)
        if len(payload) > maximum:
            raise ValueError(f"monitoring source exceeded {maximum} bytes")
        charset = response.headers.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")


def split_associations(raw: str) -> set[str]:
    return {value.strip() for value in raw.split(";") if value.strip()}


def build_targets(
    config: dict[str, Any],
    source_rows: list[dict[str, str]],
    registry_rows: list[dict[str, str]],
    monitoring_issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build the complete live monitoring set without a hand-curated target list."""
    registry_by_number = {
        int(row["GitHub Number"]): row
        for row in registry_rows
        if row.get("GitHub Number", "").isdigit()
    }
    supported_hosts = set(config.get("supportedSourceHosts", []))
    output: list[dict[str, Any]] = []
    seen_numbers: set[int] = set()
    for issue in sorted(monitoring_issues, key=lambda item: int(item["number"])):
        number = int(issue["number"])
        if number in seen_numbers:
            raise ValueError(f"duplicate live monitoring issue: #{number}")
        seen_numbers.add(number)
        registry_row = registry_by_number.get(number)
        if not registry_row:
            raise ValueError(f"live monitoring issue #{number} is missing from the issue registry")
        record_id = registry_row.get("Object ID", "").strip()
        if not record_id:
            raise ValueError(f"live monitoring issue #{number} has no stable object identifier")

        associated = [
            row
            for row in source_rows
            if record_id in split_associations(row.get("Associated Record IDs", ""))
        ]
        matters: list[dict[str, str]] = []
        unsupported: list[dict[str, str]] = []
        for row in associated:
            source_id = row.get("Source ID", "").strip()
            url = row.get("URL", "").strip()
            host = urllib.parse.urlsplit(url).hostname or ""
            key = docket_key(url) if host in supported_hosts else ""
            payload = {
                "matter_id": source_id,
                "title": row.get("Title", "").strip() or source_id,
                "url": url,
                "inventory": row.get("_inventory", "source inventory"),
            }
            if key:
                matters.append({**payload, "docket_key": key})
            else:
                unsupported.append(payload)
        output.append(
            {
                "record_id": record_id,
                "issue_number": number,
                "issue_url": registry_row["GitHub Issue"],
                "issue_title": issue.get("title", registry_row.get("GitHub Title", record_id)),
                "labels": [
                    label.get("name", "") if isinstance(label, dict) else str(label)
                    for label in issue.get("labels", [])
                ],
                "matters": matters,
                "unsupported": unsupported,
            }
        )
    return output


def observations_for_target(
    target: dict[str, Any], source_observations: dict[str, dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    observations: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for matter in target["matters"]:
        matter_id = matter["matter_id"]
        observation = source_observations.get(matter["docket_key"])
        if not observation:
            errors.append(f"{matter_id}: configured docket was not found in the current tracker")
            continue
        observations[matter_id] = observation
    return observations, errors


def state_from_comment(body: str) -> dict[str, Any] | None:
    match = re.search(
        rf"<!--\s*{re.escape(STATE_MARKER)}\s*\n(.*?)\n-->", body, re.DOTALL
    )
    if not match:
        return None
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def evaluate_target(
    previous: dict[str, Any] | None,
    observations: dict[str, dict[str, Any]],
    errors: list[str],
    *,
    review_label_present: bool,
    checked_at: str,
    source_url: str,
) -> dict[str, Any]:
    errors = [safe_error(error) for error in errors]
    current = {key: value["fingerprint"] for key, value in sorted(observations.items())}
    prior_baseline = dict((previous or {}).get("baseline", {}))
    prior_review_required = bool((previous or {}).get("review_required"))
    prior_status = (previous or {}).get("status", "")
    prior_schema = int((previous or {}).get("schema_version", 0))

    acknowledged = prior_review_required and not review_label_present
    if not observations and not errors:
        baseline = prior_baseline
        status = "manual_only"
        failures = 0
    elif previous is not None and prior_schema < 2 and not errors:
        baseline = current
        status = "baseline_migrated"
        failures = 0
    elif previous is None and not errors:
        baseline = current
        status = "baseline_established"
        failures = 0
    elif acknowledged and not errors:
        baseline = current
        status = "baseline_acknowledged"
        failures = 0
    elif errors:
        baseline = prior_baseline
        status = "check_failed"
        failures = int((previous or {}).get("consecutive_failures", 0)) + 1
    else:
        baseline = prior_baseline or current
        failures = 0
        status = "update_detected" if current != baseline else "no_change"

    needs_new_label = status == "update_detected" or (
        status == "check_failed" and failures >= 2
    )
    review_required = review_label_present or needs_new_label
    return {
        "schema_version": 2,
        "checked_at": checked_at,
        "source_url": source_url,
        "status": status,
        "baseline": baseline,
        "observed": current,
        "errors": errors,
        "consecutive_failures": failures,
        "review_required": review_required,
        "add_review_label": needs_new_label and not review_label_present,
        "prior_status": prior_status,
    }


STATUS_LABELS = {
    "baseline_established": "Baseline established",
    "baseline_migrated": "Baseline migrated to permanent source identifiers",
    "baseline_acknowledged": "Reviewed baseline accepted",
    "manual_only": "Manual monitoring required",
    "no_change": "No relevant change detected",
    "update_detected": "Possible update detected — review required",
    "check_failed": "Automated check failed",
}


def render_comment(
    target: dict[str, Any], state: dict[str, Any], observations: dict[str, dict[str, Any]]
) -> str:
    state_json = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    rows: list[str] = []
    for matter in target["matters"]:
        matter_id = matter["matter_id"]
        observation = observations.get(matter_id)
        if observation:
            baseline = state["baseline"].get(matter_id)
            result = "Unchanged" if baseline == observation["fingerprint"] else "Changed"
            rows.append(
                f"| [`{matter_id}`]({matter['url']}) | {markdown_cell(matter['title'])} | {result} | "
                f"{markdown_cell(observation['status'])} | "
                f"{markdown_cell(observation['last_update'] or 'Not stated')} |"
            )
        else:
            rows.append(
                f"| [`{matter_id}`]({matter['url']}) | {markdown_cell(matter['title'])} | "
                "Check failed | — | — |"
            )
    displayed_rows = rows[:40]
    omitted = len(rows) - len(displayed_rows)
    if omitted:
        displayed_rows.append(f"| — | {omitted} additional automated sources | See run summary | — | — |")
    error_section = ""
    if state["errors"]:
        visible_errors = state["errors"][:20]
        error_section = "\n\n### Check errors\n\n" + "\n".join(f"- {error}" for error in visible_errors)
        if len(state["errors"]) > len(visible_errors):
            error_section += f"\n- {len(state['errors']) - len(visible_errors)} additional errors are listed in the workflow report."
    unsupported_section = ""
    if target["unsupported"]:
        unsupported_section = (
            "\n\n### Sources requiring manual review\n\n"
            f"This monitor has **{len(target['unsupported'])}** associated source record(s) for which "
            "the current prototype has no deterministic adapter. They remain part of the human monitoring pass."
        )
    elif not target["matters"]:
        unsupported_section = (
            "\n\n### Manual predicate\n\n"
            "No associated source currently has a deterministic adapter. The monitoring record remains "
            "in the complete run so its defined predicate is visible and must be checked manually."
        )
    acknowledgement = ""
    if state["review_required"]:
        acknowledgement = (
            "\n\n**Human acknowledgment:** Review the detected change or failure, then remove "
            "the `needs: monitor review` label. The next successful run will accept the "
            "reviewed observation as the new baseline."
        )
    table = ""
    if displayed_rows:
        table = f"""

| Source | Record | Signal | Current tracker status | Latest tracker date |
| --- | --- | --- | --- | --- |
{chr(10).join(displayed_rows)}"""
    return f"""<!-- {STATE_MARKER}
{state_json}
-->
## Automated monitoring check

**Last automated check:** {state['checked_at']}

**Result:** {STATUS_LABELS[state['status']]}

**Source:** [Just Security litigation tracker]({state['source_url']})

This signal-only check discovered this record through the live `needs: monitoring` label and compared each supported source with the last acknowledged baseline. It does not determine legal significance, alter the proposal, or satisfy the project's substantive monitoring review.

**Automatically checked sources:** {len(target['matters'])}<br>
**Sources requiring manual review:** {len(target['unsupported'])}
{table}{error_section}{unsupported_section}{acknowledgement}
"""


class GitHubClient:
    def __init__(self, repository: str, token: str) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError("invalid GitHub repository name")
        if not token:
            raise ValueError("GITHUB_TOKEN is required with --apply")
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
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API {method} {path} failed: {exc.code} {detail}") from exc
        return json.loads(body) if body else None

    def issue(self, number: int) -> dict[str, Any]:
        return self.request("GET", f"/issues/{number}")

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

    def comments(self, number: int) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for page in range(1, 11):
            batch = self.request("GET", f"/issues/{number}/comments?per_page=100&page={page}")
            output.extend(batch)
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
            self.request(
                "POST", "/labels", {"name": name, "color": color, "description": description}
            )

    def add_label(self, number: int, label: str) -> None:
        self.request("POST", f"/issues/{number}/labels", {"labels": [label]})

    def create_comment(self, number: int, body: str) -> None:
        self.request("POST", f"/issues/{number}/comments", {"body": body})

    def update_comment(self, comment_id: int, body: str) -> None:
        self.request("PATCH", f"/issues/comments/{comment_id}", {"body": body})


def find_bot_comment(comments: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((comment for comment in comments if STATE_MARKER in comment.get("body", "")), None)


def render_summary(results: list[dict[str, Any]], *, checked_at: str, source_url: str) -> str:
    counts = Counter(result["state"]["status"] for result in results)
    lines = [
        "## ARRP automated monitoring prototype",
        "",
        f"Checked at: **{checked_at}**  ",
        f"Source: [{source_url}]({source_url})",
        "",
        "| Monitoring record | GitHub issue | Result | Automated sources | Manual sources |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for result in results:
        target = result["target"]
        lines.append(
            f"| `{target['record_id']}` | [#{target['issue_number']}]({target['issue_url']}) | "
            f"{STATUS_LABELS[result['state']['status']]} | {len(target['matters'])} | "
            f"{len(target['unsupported'])} |"
        )
    lines.extend(
        [
            "",
            "### Totals",
            "",
            *[
                f"- {STATUS_LABELS[key]}: **{value}**"
                for key, value in sorted(counts.items())
            ],
            "",
            "The prototype reports source signals only. It does not adjudicate a monitoring trigger or revise project records.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--pending-sources", type=Path, default=DEFAULT_PENDING_SOURCES)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument(
        "--monitoring-issues-json",
        type=Path,
        help="Use a saved GitHub issues JSON array for a non-applying local run.",
    )
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "Thorncrag/ARRP"))
    parser.add_argument("--source-html", type=Path, help="Use a local source snapshot instead of downloading.")
    parser.add_argument("--summary", type=Path, help="Write the Markdown run summary to this path.")
    parser.add_argument("--report-json", type=Path, help="Write a machine-readable run report.")
    parser.add_argument("--apply", action="store_true", help="Update rolling GitHub comments and review labels.")
    parser.add_argument(
        "--refresh-github",
        action="store_true",
        help="Discover the live monitoring set from GitHub without applying comments or labels.",
    )
    parser.add_argument("--checked-at", help="Override the UTC check timestamp for deterministic tests.")
    return parser.parse_args()


def github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        return token
    completed = subprocess.run(
        ["gh", "auth", "token"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def main() -> int:
    args = parse_args()
    config = read_json(args.config)
    if config.get("schemaVersion") != 2:
        raise SystemExit("unsupported monitoring-pilot schemaVersion")
    if not config.get("enabled", False):
        summary = "## ARRP automated monitoring prototype\n\nPrototype disabled by configuration.\n"
        if args.summary:
            args.summary.write_text(summary, encoding="utf-8")
        print(summary, end="")
        return 0

    checked_at = args.checked_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    discovery_client = (
        GitHubClient(args.repository, github_token()) if args.apply or args.refresh_github else None
    )
    if discovery_client:
        monitoring_issues = discovery_client.monitoring_issues(config["targetLabel"])
    elif args.monitoring_issues_json:
        monitoring_issues = read_json(args.monitoring_issues_json)
        if not isinstance(monitoring_issues, list):
            raise SystemExit("--monitoring-issues-json must contain a JSON array")
    else:
        raise SystemExit("a complete dry run requires --monitoring-issues-json")

    source_rows = [
        {**row, "_inventory": args.sources.name} for row in read_csv(args.sources)
    ]
    source_rows.extend(
        {**row, "_inventory": args.pending_sources.name}
        for row in read_csv(args.pending_sources)
    )
    targets = build_targets(config, source_rows, read_csv(args.registry), monitoring_issues)
    source = config["source"]
    global_error = ""
    source_observations: dict[str, dict[str, Any]] = {}
    try:
        html_text = (
            args.source_html.read_text(encoding="utf-8")
            if args.source_html
            else fetch_source(source)
        )
        if source["type"] != "just-security-tablepress-42":
            raise ValueError(f"unsupported monitoring source type: {source['type']}")
        source_observations = tracker_cases_by_docket(parse_just_security(html_text))
    except (OSError, ValueError, urllib.error.URLError) as exc:
        global_error = f"source check failed: {exc}"

    client = discovery_client if args.apply else None
    if client:
        client.ensure_label(
            config["reviewLabel"],
            config["reviewLabelColor"],
            config["reviewLabelDescription"],
        )

    results: list[dict[str, Any]] = []
    for target in targets:
        observations, errors = observations_for_target(target, source_observations)
        if global_error and target["matters"]:
            errors = [global_error]
        previous = None
        review_label_present = False
        bot_comment = None
        if client:
            label_names = set(target["labels"])
            review_label_present = config["reviewLabel"] in label_names
            bot_comment = find_bot_comment(client.comments(target["issue_number"]))
            previous = state_from_comment(bot_comment["body"]) if bot_comment else None

        state = evaluate_target(
            previous,
            observations,
            errors,
            review_label_present=review_label_present,
            checked_at=checked_at,
            source_url=source["url"],
        )
        comment = render_comment(target, state, observations)
        if client:
            if bot_comment:
                client.update_comment(int(bot_comment["id"]), comment)
            else:
                client.create_comment(target["issue_number"], comment)
            if state["add_review_label"]:
                client.add_label(target["issue_number"], config["reviewLabel"])
        results.append({"target": target, "state": state, "comment": comment})

    summary = render_summary(results, checked_at=checked_at, source_url=source["url"])
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(summary, encoding="utf-8")
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "schema_version": 2,
            "checked_at": checked_at,
            "source_url": source["url"],
            "apply": args.apply,
            "results": [
                {
                    "record_id": result["target"]["record_id"],
                    "issue_number": result["target"]["issue_number"],
                    "source_ids": [
                        matter["matter_id"] for matter in result["target"]["matters"]
                    ],
                    "manual_source_ids": [
                        matter["matter_id"] for matter in result["target"]["unsupported"]
                    ],
                    "state": result["state"],
                }
                for result in results
            ],
        }
        args.report_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(summary, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
