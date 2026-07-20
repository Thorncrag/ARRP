#!/usr/bin/env python3
"""Deterministically check configured ARRP monitoring records for source changes.

The pilot is deliberately signal-only. It compares structured source fields with
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
DEFAULT_LEDGER = ROOT / "research" / "trump-administration-litigation-monitoring.csv"
DEFAULT_REGISTRY = ROOT / "inventory" / "github_issue_registry.csv"
STATE_MARKER = "arrp-monitor-bot-state:v1"
USER_AGENT = "ARRP deterministic monitoring pilot/0.1"


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
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


def split_routes(raw: str) -> set[str]:
    return {part.strip() for part in raw.split(";") if part.strip()}


def build_targets(
    config: dict[str, Any], ledger_rows: list[dict[str, str]], registry_rows: list[dict[str, str]]
) -> list[dict[str, Any]]:
    ledger = {row["monitor_id"]: row for row in ledger_rows if row.get("monitor_id")}
    registry = {row["Object ID"]: row for row in registry_rows if row.get("Object ID")}
    output: list[dict[str, Any]] = []
    seen_records: set[str] = set()
    for target in config.get("targets", []):
        record_id = target["recordId"]
        route_id = target["routeId"]
        if record_id in seen_records:
            raise ValueError(f"duplicate monitoring target record: {record_id}")
        seen_records.add(record_id)
        registry_row = registry.get(record_id)
        if not registry_row:
            raise ValueError(f"monitoring target is missing from the issue registry: {record_id}")
        matters: list[dict[str, str]] = []
        for monitor_id in target.get("monitorIds", []):
            row = ledger.get(monitor_id)
            if not row:
                raise ValueError(f"configured monitoring matter is missing from the ledger: {monitor_id}")
            if row.get("monitoring_status") != "active-defined-predicate":
                raise ValueError(f"configured monitoring matter is not active: {monitor_id}")
            if route_id not in split_routes(row.get("integration_routes", "")):
                raise ValueError(f"{monitor_id} is not routed to {route_id}")
            if "Just Security litigation tracker" not in row.get("source_family", ""):
                raise ValueError(f"pilot matter does not use the configured source family: {monitor_id}")
            matters.append(row)
        if not matters:
            raise ValueError(f"monitoring target has no configured matters: {record_id}")
        output.append(
            {
                "record_id": record_id,
                "route_id": route_id,
                "issue_number": int(registry_row["GitHub Number"]),
                "issue_url": registry_row["GitHub Issue"],
                "matters": matters,
            }
        )
    return output


def observations_for_target(
    target: dict[str, Any], source_observations: dict[str, dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    observations: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for matter in target["matters"]:
        monitor_id = matter["monitor_id"]
        action = matter["action_or_policy"]
        observation = source_observations.get(action)
        if not observation:
            errors.append(f"{monitor_id}: configured action was not found in the current tracker")
            continue
        observations[monitor_id] = observation
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

    acknowledged = prior_review_required and not review_label_present
    if previous is None and not errors:
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
        "schema_version": 1,
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
    "baseline_acknowledged": "Reviewed baseline accepted",
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
        monitor_id = matter["monitor_id"]
        observation = observations.get(monitor_id)
        if observation:
            baseline = state["baseline"].get(monitor_id)
            result = "Unchanged" if baseline == observation["fingerprint"] else "Changed"
            rows.append(
                f"| `{monitor_id}` | {result} | {observation['case_count']} | "
                f"{markdown_cell(observation['status_summary'])} | "
                f"{markdown_cell(observation['last_update'] or 'Not stated')} |"
            )
        else:
            rows.append(f"| `{monitor_id}` | Check failed | — | — | — |")
    error_section = ""
    if state["errors"]:
        error_section = "\n\n### Check errors\n\n" + "\n".join(
            f"- {error}" for error in state["errors"]
        )
    acknowledgement = ""
    if state["review_required"]:
        acknowledgement = (
            "\n\n**Human acknowledgment:** Review the detected change or failure, then remove "
            "the `needs: monitor review` label. The next successful run will accept the "
            "reviewed observation as the new baseline."
        )
    return f"""<!-- {STATE_MARKER}
{state_json}
-->
## Automated monitoring check

**Last automated check:** {state['checked_at']}

**Result:** {STATUS_LABELS[state['status']]}

**Source:** [Just Security litigation tracker]({state['source_url']})

This signal-only check compares structured tracker fields with the last acknowledged baseline. It does not determine legal significance, alter the proposal, or satisfy the project's substantive monitoring review.

| Matter | Signal | Cases | Current tracker status | Latest tracker date |
| --- | --- | ---: | --- | --- |
{chr(10).join(rows)}{error_section}{acknowledgement}
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
        "## ARRP automated monitoring pilot",
        "",
        f"Checked at: **{checked_at}**  ",
        f"Source: [{source_url}]({source_url})",
        "",
        "| Monitoring record | GitHub issue | Result | Matters checked |",
        "| --- | --- | --- | ---: |",
    ]
    for result in results:
        target = result["target"]
        lines.append(
            f"| `{target['record_id']}` | [#{target['issue_number']}]({target['issue_url']}) | "
            f"{STATUS_LABELS[result['state']['status']]} | {len(target['matters'])} |"
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
            "The pilot reports source signals only. It does not adjudicate a monitoring trigger or revise project records.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "Thorncrag/ARRP"))
    parser.add_argument("--source-html", type=Path, help="Use a local source snapshot instead of downloading.")
    parser.add_argument("--summary", type=Path, help="Write the Markdown run summary to this path.")
    parser.add_argument("--report-json", type=Path, help="Write a machine-readable run report.")
    parser.add_argument("--apply", action="store_true", help="Update rolling GitHub comments and review labels.")
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
    if config.get("schemaVersion") != 1:
        raise SystemExit("unsupported monitoring-pilot schemaVersion")
    if not config.get("enabled", False):
        summary = "## ARRP automated monitoring pilot\n\nPilot disabled by configuration.\n"
        if args.summary:
            args.summary.write_text(summary, encoding="utf-8")
        print(summary, end="")
        return 0

    targets = build_targets(config, read_csv(args.ledger), read_csv(args.registry))
    checked_at = args.checked_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
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
        source_observations = parse_just_security(html_text)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        global_error = f"source check failed: {exc}"

    client = None
    if args.apply:
        client = GitHubClient(args.repository, github_token())
        client.ensure_label(
            config["reviewLabel"],
            config["reviewLabelColor"],
            config["reviewLabelDescription"],
        )

    results: list[dict[str, Any]] = []
    for target in targets:
        observations, errors = observations_for_target(target, source_observations)
        if global_error:
            errors = [global_error]
        previous = None
        review_label_present = False
        bot_comment = None
        if client:
            issue = client.issue(target["issue_number"])
            label_names = {label["name"] for label in issue.get("labels", [])}
            if issue.get("state") != "open" or "needs: monitoring" not in label_names:
                raise RuntimeError(
                    f"configured target #{target['issue_number']} is not an open issue marked needs: monitoring"
                )
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
            "schema_version": 1,
            "checked_at": checked_at,
            "source_url": source["url"],
            "apply": args.apply,
            "results": [
                {
                    "record_id": result["target"]["record_id"],
                    "issue_number": result["target"]["issue_number"],
                    "monitor_ids": [
                        matter["monitor_id"] for matter in result["target"]["matters"]
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
