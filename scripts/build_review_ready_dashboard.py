#!/usr/bin/env python3
"""Build the ARRP Review Ready progress dashboard from GitHub Project data."""

from __future__ import annotations

import argparse
import base64
import csv
import html
import json
import math
import os
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


GRAPHQL_URL = "https://api.github.com/graphql"
REST_ROOT = "https://api.github.com"
USER_AGENT = "ARRP-review-ready-dashboard/1.0"

PROJECT_QUERY = r"""
query($owner: String!, $number: Int!, $cursor: String) {
  user(login: $owner) {
    projectV2(number: $number) {
      title
      items(first: 100, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          fieldValues(first: 50) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldNumberValue {
                number
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldTextValue {
                text
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldDateValue {
                date
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldIterationValue {
                title
                field { ... on ProjectV2FieldCommon { name } }
              }
            }
          }
        }
      }
    }
  }
}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--registry",
        type=Path,
        help="Read proposal identity and links from the repository issue registry.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Read a saved GraphQL item fixture instead of querying GitHub.",
    )
    parser.add_argument(
        "--history",
        type=Path,
        help="Read history from a local file instead of the configured live URL.",
    )
    parser.add_argument(
        "--as-of",
        type=str,
        help="Override the snapshot date (YYYY-MM-DD) for deterministic tests.",
    )
    parser.add_argument(
        "--token-env",
        default="ARRP_PROJECT_TOKEN",
        help="Environment variable containing a token with read:project access.",
    )
    return parser.parse_args()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_registry(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"GitHub Number", "GitHub Issue", "Kind", "GitHub Title", "Canonical Record"}
    missing = required - set(rows[0] if rows else [])
    if missing:
        raise RuntimeError("Issue registry is missing required columns: {}".format(", ".join(sorted(missing))))
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def human_date(value: date, full_month: bool = False) -> str:
    pattern = "%B %d, %Y" if full_month else "%b %d, %Y"
    return value.strftime(pattern).replace(" 0", " ")


def graphql_request(token: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    body = json.dumps({"query": PROJECT_QUERY, "variables": variables}).encode("utf-8")
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        headers={
            "Authorization": "bearer " + token,
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError("GitHub GraphQL request failed: {} {}".format(exc.code, detail))
    if payload.get("errors"):
        raise RuntimeError("GitHub GraphQL returned errors: {}".format(payload["errors"]))
    return payload


def fetch_project(config: Dict[str, Any], token: str) -> Dict[str, Any]:
    cursor: Optional[str] = None
    items: List[Dict[str, Any]] = []
    title = ""
    while True:
        payload = graphql_request(
            token,
            {
                "owner": config["projectOwner"],
                "number": int(config["projectNumber"]),
                "cursor": cursor,
            },
        )
        project = ((payload.get("data") or {}).get("user") or {}).get("projectV2")
        if not project:
            raise RuntimeError("The configured GitHub user Project could not be read.")
        title = project.get("title") or title
        connection = project.get("items") or {}
        items.extend(connection.get("nodes") or [])
        page_info = connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            raise RuntimeError("Project pagination reported another page without a cursor.")
    return {"projectTitle": title, "items": items}


def extract_field_values(node: Dict[str, Any]) -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for value in ((node.get("fieldValues") or {}).get("nodes") or []):
        field_name = ((value.get("field") or {}).get("name") or "").strip()
        if not field_name:
            continue
        for key in ("name", "number", "text", "date", "title"):
            if value.get(key) is not None:
                values[field_name] = value[key]
                break
    return values


def issue_identifier(title: str) -> str:
    prefix = title.split(":", 1)[0].strip()
    return prefix if "-" in prefix else title.strip()


def area_from_title(title: str) -> str:
    identifier = issue_identifier(title)
    return identifier.split("-", 1)[0] if "-" in identifier else "Unassigned"


def canonical_key(value: Any, repository: str) -> str:
    text = str(value or "").strip().strip("`")
    prefixes = (
        "https://github.com/{}/blob/main/".format(repository),
        "https://github.com/{}/blob/master/".format(repository),
    )
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    return text.lstrip("./")


def parse_items(
    raw: Dict[str, Any], config: Dict[str, Any], registry: Sequence[Dict[str, str]]
) -> Tuple[str, List[Dict[str, Any]]]:
    fields = config["projectFields"]
    ready_statuses = {normalize(value) for value in config["goal"]["readyStatuses"]}
    threshold = float(config["goal"]["reviewReadyScore"])
    parsed: List[Dict[str, Any]] = []
    project_values_by_identifier: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    project_values_by_record: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for node in raw.get("items") or []:
        project_values = extract_field_values(node)
        project_title = str(project_values.get(fields.get("title", "Title")) or "")
        project_identifier = issue_identifier(project_title)
        if project_identifier:
            project_values_by_identifier[normalize(project_identifier)].append(project_values)
        record = canonical_key(project_values.get(fields["canonicalPage"]), config["repository"])
        if record:
            project_values_by_record[record].append(project_values)

    for registry_row in registry:
        if normalize(registry_row.get("Kind")) != "proposal":
            continue
        record = canonical_key(registry_row.get("Canonical Record"), config["repository"])
        title = str(registry_row.get("GitHub Title") or "Untitled proposal")
        identifier = issue_identifier(title)
        identifier_matches = project_values_by_identifier.get(normalize(identifier)) or []
        record_matches = project_values_by_record.get(record) or []
        identity_warning: Optional[str] = None
        if len(identifier_matches) == 1:
            project_values = identifier_matches[0]
        elif len(identifier_matches) > 1:
            project_values = {}
            identity_warning = "Multiple Project items use this proposal identifier; identity is ambiguous."
        elif len(record_matches) == 1:
            project_values = record_matches[0]
        elif len(record_matches) > 1:
            project_values = {}
            identity_warning = (
                "Project Title did not identify this proposal and Canonical page matches multiple items."
            )
        else:
            project_values = {}
        status = str(project_values.get(fields["status"], "Unspecified"))
        score_value = project_values.get(fields["score"])
        try:
            score = float(score_value) if score_value is not None else None
        except (TypeError, ValueError):
            score = None
        area = str(project_values.get(fields["area"]) or area_from_title(title))
        is_ready = normalize(status) in ready_statuses
        warnings: List[str] = []
        if identity_warning:
            warnings.append(identity_warning)
        if not project_values:
            if not identity_warning:
                warnings.append("Proposal registry entry has no matching Project item by Title or Canonical page.")
        if is_ready and score is None:
            warnings.append(
                "Ready status is missing a Project score, so threshold consistency cannot be verified."
            )
        if is_ready and score is not None and score < threshold and normalize(status) != normalize("Done / Published"):
            warnings.append("Ready status is paired with a score below the Review Ready threshold.")
        if not is_ready and score is not None and score >= threshold:
            warnings.append("Score meets the Review Ready threshold but status is not Review ready or higher.")
        parsed.append(
            {
                "number": int(registry_row["GitHub Number"]),
                "identifier": identifier,
                "title": title,
                "url": registry_row.get("GitHub Issue"),
                "state": None,
                "canonicalRecord": record,
                "area": area,
                "status": status,
                "score": score,
                "lastAudit": project_values.get(fields["lastAudit"]),
                "nextAudit": project_values.get(fields["nextAudit"]),
                "ready": is_ready,
                "warnings": warnings,
            }
        )
    return str(raw.get("projectTitle") or "ARRP GitHub Project"), parsed


def score_band(item: Dict[str, Any], threshold: float) -> str:
    if item["ready"]:
        return "Review Ready or higher"
    score = item.get("score")
    if score is None or score <= 0:
        return "Unscored or fixed zero"
    if score >= threshold - 15:
        return "Within 15 points"
    return "Below 60"


def build_snapshot(items: Sequence[Dict[str, Any]], snapshot_date: date) -> Dict[str, Any]:
    by_area: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "ready": 0})
    for item in items:
        by_area[item["area"]]["total"] += 1
        by_area[item["area"]]["ready"] += int(item["ready"])
    return {
        "date": snapshot_date.isoformat(),
        "total": len(items),
        "ready": sum(1 for item in items if item["ready"]),
        "byArea": dict(sorted(by_area.items())),
        "detailAvailable": True,
        "readyIssues": sorted(item["identifier"] for item in items if item["ready"]),
        "scores": {
            item["identifier"]: int(item["score"]) if item["score"].is_integer() else item["score"]
            for item in items
            if item.get("score") is not None
        },
    }


def valid_history(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("snapshots"), list):
        return {"schemaVersion": 1, "snapshots": []}
    cleaned = []
    for snapshot in payload["snapshots"]:
        try:
            date.fromisoformat(str(snapshot["date"]))
            total = int(snapshot["total"])
            ready = int(snapshot["ready"])
        except (KeyError, TypeError, ValueError):
            continue
        if total < 0 or ready < 0 or ready > total:
            continue
        cleaned.append(
            {
                "date": str(snapshot["date"]),
                "total": total,
                "ready": ready,
                "byArea": snapshot.get("byArea") or {},
                "detailAvailable": bool(
                    snapshot.get("detailAvailable", "readyIssues" in snapshot or "scores" in snapshot)
                ),
                "readyIssues": sorted(
                    {str(value) for value in snapshot.get("readyIssues") or [] if str(value).strip()}
                ),
                "scores": {
                    str(key): value
                    for key, value in (snapshot.get("scores") or {}).items()
                    if isinstance(value, (int, float))
                },
            }
        )
    unique = {snapshot["date"]: snapshot for snapshot in cleaned}
    return {"schemaVersion": 1, "snapshots": [unique[key] for key in sorted(unique)]}


def load_history(config: Dict[str, Any], local_path: Optional[Path]) -> Dict[str, Any]:
    if local_path:
        return valid_history(read_json(local_path))
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    branch = config.get("dashboardBranch")
    history_path = config.get("historyPath")
    if not token or not branch or not history_path:
        return {"schemaVersion": 1, "snapshots": []}
    url = "{}/repos/{}/contents/{}?ref={}".format(
        REST_ROOT,
        config["repository"],
        urllib.parse.quote(str(history_path), safe="/"),
        urllib.parse.quote(str(branch), safe=""),
    )
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2026-03-10",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
        encoded = str(payload.get("content") or "").replace("\n", "")
        return valid_history(json.loads(base64.b64decode(encoded).decode("utf-8")))
    except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError):
        return {"schemaVersion": 1, "snapshots": []}


def combine_histories(*histories: Dict[str, Any]) -> Dict[str, Any]:
    """Combine validated histories in precedence order; later values win by date."""
    by_date: Dict[str, Dict[str, Any]] = {}
    for history in histories:
        for snapshot in valid_history(history).get("snapshots") or []:
            by_date[snapshot["date"]] = snapshot
    return {
        "schemaVersion": 1,
        "snapshots": [by_date[key] for key in sorted(by_date)],
    }


def merge_history(history: Dict[str, Any], snapshot: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    goal = config["goal"]
    by_date = {entry["date"]: entry for entry in history.get("snapshots") or []}
    baseline_date = goal["baselineDate"]
    history_start_date = goal.get("historyStartDate", baseline_date)
    by_date.setdefault(
        baseline_date,
        {
            "date": baseline_date,
            "total": int(goal["baselineTotal"]),
            "ready": int(goal["baselineReady"]),
            "byArea": {},
            "detailAvailable": False,
            "readyIssues": [],
            "scores": {},
        },
    )
    by_date[snapshot["date"]] = snapshot
    snapshots = [
        by_date[key]
        for key in sorted(by_date)
        if history_start_date <= key <= snapshot["date"]
    ]
    return {"schemaVersion": 1, "snapshots": snapshots[-740:]}


def snapshot_on_or_before(snapshots: Sequence[Dict[str, Any]], when: date) -> Optional[Dict[str, Any]]:
    candidates = [entry for entry in snapshots if date.fromisoformat(entry["date"]) <= when]
    return candidates[-1] if candidates else None


def weekly_velocity(
    snapshots: Sequence[Dict[str, Any]],
    current_date: date,
    window_days: int,
    minimum_days: int,
) -> Optional[float]:
    current = snapshot_on_or_before(snapshots, current_date)
    if not current:
        return None
    start = snapshot_on_or_before(snapshots, current_date - timedelta(days=window_days))
    if not start:
        start = snapshots[0] if snapshots else None
    if not start:
        return None
    elapsed = (current_date - date.fromisoformat(start["date"])).days
    if elapsed < minimum_days:
        return None
    return (current["ready"] - start["ready"]) / (elapsed / 7.0)


def iso_forecast(current_date: date, remaining: int, weekly_rate: Optional[float]) -> Optional[str]:
    if weekly_rate is None or weekly_rate <= 0 or remaining <= 0:
        return current_date.isoformat() if remaining <= 0 else None
    days = int(math.ceil((remaining / weekly_rate) * 7.0))
    return (current_date + timedelta(days=days)).isoformat()


def month_end_checkpoints(start: date, target: date, baseline_ready: int, target_total: int) -> List[Dict[str, Any]]:
    points: List[date] = []
    cursor = date(start.year, start.month, 1)
    while cursor <= target:
        if cursor.month == 12:
            next_month = date(cursor.year + 1, 1, 1)
        else:
            next_month = date(cursor.year, cursor.month + 1, 1)
        end = min(next_month - timedelta(days=1), target)
        if end >= start:
            points.append(end)
        cursor = next_month
    total_days = max((target - start).days, 1)
    checkpoints = []
    for point in points:
        fraction = min(max((point - start).days / total_days, 0.0), 1.0)
        planned = baseline_ready + fraction * max(target_total - baseline_ready, 0)
        checkpoints.append({"date": point.isoformat(), "plannedReady": int(math.ceil(planned))})
    return checkpoints


def compute_metrics(
    snapshot: Dict[str, Any], history: Dict[str, Any], config: Dict[str, Any], as_of: date
) -> Dict[str, Any]:
    goal = config["goal"]
    target = date.fromisoformat(goal["targetDate"])
    baseline = date.fromisoformat(goal["baselineDate"])
    remaining = max(snapshot["total"] - snapshot["ready"], 0)
    days_remaining = (target - as_of).days
    weeks_remaining = max(days_remaining / 7.0, 0.0)
    required = remaining / weeks_remaining if weeks_remaining > 0 else None
    velocity = weekly_velocity(
        history["snapshots"],
        as_of,
        int(goal["velocityWindowDays"]),
        int(goal["minimumForecastDays"]),
    )
    since_baseline = weekly_velocity(
        history["snapshots"],
        as_of,
        max((as_of - baseline).days, 1),
        int(goal["minimumForecastDays"]),
    )
    forecast = iso_forecast(as_of, remaining, velocity)
    if forecast:
        forecast_label = forecast
    elif remaining == 0:
        forecast_label = as_of.isoformat()
    elif velocity is None:
        forecast_label = "Pending history"
    else:
        forecast_label = "No forward pace"
    total_goal_days = max((target - baseline).days, 1)
    elapsed_fraction = min(max((as_of - baseline).days / total_goal_days, 0.0), 1.0)
    planned_now = int(
        math.ceil(int(goal["baselineReady"]) + elapsed_fraction * max(snapshot["total"] - int(goal["baselineReady"]), 0))
    )
    variance = snapshot["ready"] - planned_now

    if remaining == 0:
        track_status = "Goal complete"
    elif velocity is None:
        track_status = "Establishing pace"
    elif forecast and date.fromisoformat(forecast) <= target:
        track_status = "On track"
    elif forecast and date.fromisoformat(forecast) <= target + timedelta(days=30):
        track_status = "At risk"
    else:
        track_status = "Off track"

    return {
        "ready": snapshot["ready"],
        "total": snapshot["total"],
        "remaining": remaining,
        "percentReady": round((snapshot["ready"] / snapshot["total"] * 100.0), 1) if snapshot["total"] else 0.0,
        "daysRemaining": days_remaining,
        "requiredPerWeek": round(required, 2) if required is not None else None,
        "rollingWeeklyVelocity": round(velocity, 2) if velocity is not None else None,
        "sinceBaselineWeeklyVelocity": round(since_baseline, 2) if since_baseline is not None else None,
        "forecastDate": forecast,
        "forecastLabel": forecast_label,
        "plannedReadyToday": planned_now,
        "scheduleVariance": variance,
        "trackStatus": track_status,
        "scopeChange": snapshot["total"] - int(goal["baselineTotal"]),
        "checkpoints": month_end_checkpoints(baseline, target, int(goal["baselineReady"]), snapshot["total"]),
    }


def build_dashboard_payload(
    project_title: str,
    items: List[Dict[str, Any]],
    history: Dict[str, Any],
    config: Dict[str, Any],
    as_of: date,
) -> Dict[str, Any]:
    goal = config["goal"]
    threshold = float(goal["reviewReadyScore"])
    snapshot = build_snapshot(items, as_of)
    merged_history = merge_history(history, snapshot, config)
    status_counts = Counter(item["status"] for item in items)
    band_counts = Counter(score_band(item, threshold) for item in items)
    area_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "ready": 0, "remaining": 0})
    warnings: List[Dict[str, Any]] = []
    for item in items:
        area_counts[item["area"]]["total"] += 1
        area_counts[item["area"]]["ready"] += int(item["ready"])
        area_counts[item["area"]]["remaining"] += int(not item["ready"])
        for warning in item["warnings"]:
            warnings.append({"identifier": item["identifier"], "url": item["url"], "message": warning})
    areas = [
        {
            "area": area,
            **counts,
            "percentReady": round(counts["ready"] / counts["total"] * 100.0, 1) if counts["total"] else 0.0,
        }
        for area, counts in sorted(area_counts.items(), key=lambda pair: (-pair[1]["remaining"], pair[0]))
    ]
    backlog = sorted(
        (item for item in items if not item["ready"]),
        key=lambda item: (
            -(item["score"] if item["score"] is not None else -1),
            item["area"],
            item["identifier"],
        ),
    )
    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "asOf": as_of.isoformat(),
        "project": {
            "title": project_title,
            "url": "https://github.com/users/{}/projects/{}".format(config["projectOwner"], config["projectNumber"]),
            "repository": config["repository"],
        },
        "goal": goal,
        "metrics": compute_metrics(snapshot, merged_history, config, as_of),
        "history": merged_history["snapshots"],
        "statusDistribution": [{"status": name, "count": count} for name, count in status_counts.most_common()],
        "scoreBands": [{"band": name, "count": band_counts.get(name, 0)} for name in (
            "Review Ready or higher", "Within 15 points", "Below 60", "Unscored or fixed zero"
        )],
        "areas": areas,
        "movement": portfolio_movement(items, merged_history, as_of, int(goal["velocityWindowDays"])),
        "warnings": warnings,
        "backlog": backlog,
    }
    return payload


def portfolio_movement(
    items: Sequence[Dict[str, Any]], history: Dict[str, Any], as_of: date, window_days: int
) -> Dict[str, Any]:
    snapshots = history.get("snapshots") or []
    current = snapshot_on_or_before(snapshots, as_of)
    prior = [
        entry
        for entry in snapshots
        if entry.get("detailAvailable") and date.fromisoformat(entry["date"]) < as_of
    ]
    if not current or not current.get("detailAvailable") or not prior:
        return {"available": False, "windowDays": window_days}
    target_start = as_of - timedelta(days=window_days)
    candidates = [entry for entry in prior if date.fromisoformat(entry["date"]) <= target_start]
    start = candidates[-1] if candidates else prior[0]
    elapsed = (as_of - date.fromisoformat(start["date"])).days
    if elapsed <= 0:
        return {"available": False, "windowDays": window_days}

    previous_ready = set(start.get("readyIssues") or [])
    current_ready = set(current.get("readyIssues") or [])
    current_scores = current.get("scores") or {}
    previous_scores = start.get("scores") or {}
    comparable_scores = set(current_scores) & set(previous_scores)
    deltas = {
        identifier: float(current_scores[identifier]) - float(previous_scores[identifier])
        for identifier in comparable_scores
    }
    item_lookup = {item["identifier"]: item for item in items}

    def linked(identifiers: Iterable[str]) -> List[Dict[str, Any]]:
        return [
            {
                "identifier": identifier,
                "url": (item_lookup.get(identifier) or {}).get("url"),
            }
            for identifier in sorted(identifiers)
        ]

    return {
        "available": True,
        "windowDays": window_days,
        "periodStart": start["date"],
        "elapsedDays": elapsed,
        "newlyReady": linked(current_ready - previous_ready),
        "fellBelowReady": linked(previous_ready - current_ready),
        "scoresAvailable": bool(comparable_scores),
        "scoresImproved": sum(1 for value in deltas.values() if value > 0),
        "scoresDeclined": sum(1 for value in deltas.values() if value < 0),
        "netScoreChange": round(sum(deltas.values()), 1),
    }


def svg_style() -> str:
    return """
    <style>
      text { fill: #263029; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
      .muted { fill: #687269; }
      .grid { stroke: #d9ded9; stroke-width: 1; }
      .actual { fill: none; stroke: #317957; stroke-width: 4; }
      .plan { fill: none; stroke: #a56a24; stroke-width: 3; }
      .forecast { fill: none; stroke: #765b8d; stroke-width: 3; stroke-dasharray: 8 7; }
      .point { fill: #317957; stroke: #ffffff; stroke-width: 2; }
      .bar-bg { fill: #e5e9e5; }
      .bar { fill: #4c7691; }
      .ready { fill: #317957; }
      @media (prefers-color-scheme: dark) {
        text { fill: #edf2ee; }
        .muted { fill: #aab6ad; }
        .grid { stroke: #3b4740; }
        .point { stroke: #19211c; }
        .bar-bg { fill: #2a342e; }
        .bar { fill: #82b2d0; }
        .ready { fill: #73c49a; }
      }
    </style>
    """


def trajectory_svg(payload: Dict[str, Any]) -> str:
    width, height = 1100, 390
    left, right, top, bottom = 64, 34, 42, 54
    baseline = date.fromisoformat(payload["goal"]["baselineDate"])
    target = date.fromisoformat(payload["goal"]["targetDate"])
    as_of = date.fromisoformat(payload["asOf"])
    historical_dates = [
        date.fromisoformat(entry["date"])
        for entry in payload["history"]
        if date.fromisoformat(entry["date"]) <= as_of
    ]
    chart_start = min([baseline] + historical_dates)
    forecast_value = payload["metrics"].get("forecastDate")
    forecast = date.fromisoformat(forecast_value) if forecast_value else None
    end = max(target, as_of, forecast or target)
    total_days = max((end - chart_start).days, 1)
    total = max(int(payload["metrics"]["total"]), 1)

    def x(value: date) -> float:
        return left + ((value - chart_start).days / total_days) * (width - left - right)

    def y(value: float) -> float:
        return height - bottom - (value / total) * (height - top - bottom)

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="0 0 {} {}" role="img" aria-labelledby="title desc">'.format(width, height, width, height),
        "<title id=\"title\">Review Ready goal trajectory</title>",
        "<desc id=\"desc\">Actual Review Ready proposals compared with the required path and rolling forecast.</desc>",
        svg_style(),
    ]
    for fraction in (0, 0.25, 0.5, 0.75, 1):
        value = total * fraction
        position = y(value)
        parts.append('<line class="grid" x1="{}" x2="{}" y1="{:.1f}" y2="{:.1f}"/>'.format(left, width - right, position, position))
        parts.append('<text class="muted" x="{}" y="{:.1f}" text-anchor="end" font-size="13">{}</text>'.format(left - 10, position + 5, int(round(value))))

    parts.append(
        '<path class="plan" d="M{:.1f},{:.1f} L{:.1f},{:.1f}"/>'.format(
            x(baseline), y(payload["goal"]["baselineReady"]), x(target), y(total)
        )
    )
    history_points = [
        (date.fromisoformat(entry["date"]), int(entry["ready"]))
        for entry in payload["history"]
        if chart_start <= date.fromisoformat(entry["date"]) <= as_of
    ]
    if len(history_points) > 1:
        path = " ".join(
            "{}{:0.1f},{:0.1f}".format("M" if index == 0 else "L", x(point_date), y(ready))
            for index, (point_date, ready) in enumerate(history_points)
        )
        parts.append('<path class="actual" d="{}"/>'.format(path))
    for point_date, ready in history_points:
        parts.append('<circle class="point" cx="{:.1f}" cy="{:.1f}" r="5"/>'.format(x(point_date), y(ready)))
    if forecast:
        parts.append(
            '<path class="forecast" d="M{:.1f},{:.1f} L{:.1f},{:.1f}"/>'.format(
                x(as_of), y(payload["metrics"]["ready"]), x(forecast), y(total)
            )
        )
    date_labels = [(chart_start, "start")]
    if chart_start < baseline:
        date_labels.append((baseline, "middle"))
    if end == target:
        date_labels.append((target, "end"))
    else:
        date_labels.extend(((target, "middle"), (end, "end")))
    for point_date, anchor in date_labels:
        label = human_date(point_date)
        parts.append('<text class="muted" x="{:.1f}" y="{}" text-anchor="{}" font-size="13">{}</text>'.format(x(point_date), height - 18, anchor, html.escape(label)))
    parts.append('<text x="{}" y="24" font-size="17" font-weight="600">Actual vs. required path</text>'.format(left))
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def bar_chart_svg(title: str, entries: Sequence[Dict[str, Any]], label_key: str) -> str:
    width = 1100
    row_height = 40
    height = 74 + max(len(entries), 1) * row_height
    label_x, bar_x, bar_width, count_x = 28, 340, 650, 1066
    maximum = max([int(entry["count"]) for entry in entries] or [1])
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="0 0 {} {}" role="img" aria-labelledby="title desc">'.format(width, height, width, height),
        '<title id="title">{}</title>'.format(html.escape(title)),
        '<desc id="desc">Counts of eligible ARRP proposals by {}.</desc>'.format(html.escape(title.casefold())),
        svg_style(),
        '<text x="{}" y="28" font-size="17" font-weight="600">{}</text>'.format(label_x, html.escape(title)),
    ]
    for index, entry in enumerate(entries):
        y_position = 56 + index * row_height
        count = int(entry["count"])
        filled = (count / maximum) * bar_width if maximum else 0
        label = str(entry[label_key])
        if len(label) > 38:
            label = label[:35] + "…"
        parts.extend(
            [
                '<text x="{}" y="{}" font-size="14">{}</text>'.format(label_x, y_position + 5, html.escape(label)),
                '<rect class="bar-bg" x="{}" y="{}" width="{}" height="12" rx="6"/>'.format(bar_x, y_position - 7, bar_width),
                '<rect class="bar" x="{}" y="{}" width="{:.1f}" height="12" rx="6"/>'.format(bar_x, y_position - 7, filled),
                '<text x="{}" y="{}" text-anchor="end" font-size="14">{}</text>'.format(count_x, y_position + 5, count),
            ]
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def area_chart_svg(areas: Sequence[Dict[str, Any]]) -> str:
    width = 1100
    row_height = 35
    height = 72 + max(len(areas), 1) * row_height
    label_x, bar_x, bar_width, count_x = 28, 150, 760, 1066
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" viewBox="0 0 {} {}" role="img" aria-labelledby="title desc">'.format(width, height, width, height),
        '<title id="title">Review Ready progress by ARRP area</title>',
        '<desc id="desc">Percentage and count of eligible proposals at Review Ready or higher in each area.</desc>',
        svg_style(),
        '<text x="{}" y="28" font-size="17" font-weight="600">Progress by area</text>'.format(label_x),
    ]
    for index, entry in enumerate(areas):
        y_position = 54 + index * row_height
        percent = float(entry["percentReady"])
        parts.extend(
            [
                '<text x="{}" y="{}" font-size="13" font-weight="600">{}</text>'.format(label_x, y_position + 5, html.escape(str(entry["area"]))),
                '<rect class="bar-bg" x="{}" y="{}" width="{}" height="11" rx="5.5"/>'.format(bar_x, y_position - 6, bar_width),
                '<rect class="ready" x="{}" y="{}" width="{:.1f}" height="11" rx="5.5"/>'.format(bar_x, y_position - 6, bar_width * percent / 100.0),
                '<text x="{}" y="{}" text-anchor="end" font-size="13">{} / {} · {}%</text>'.format(count_x, y_position + 5, entry["ready"], entry["total"], percent),
            ]
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def markdown_cell(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value if value is not None else "—").replace("|", "\\|").replace("\n", " ").strip()


def scenario_rows(payload: Dict[str, Any]) -> List[Tuple[str, float, str]]:
    remaining = int(payload["metrics"]["remaining"])
    as_of = date.fromisoformat(payload["asOf"])
    target = date.fromisoformat(payload["goal"]["targetDate"])
    named: List[Tuple[str, Optional[float]]] = [
        ("Rolling 28-day pace", payload["metrics"].get("rollingWeeklyVelocity")),
        ("Pace required for official target", payload["metrics"].get("requiredPerWeek")),
        ("Two per week", 2.0),
        ("Four per week", 4.0),
        ("Six per week", 6.0),
        ("Eight per week", 8.0),
        ("Ten per week", 10.0),
    ]
    rows = []
    seen = set()
    for label, rate in named:
        if rate is None or rate <= 0:
            continue
        rounded = round(float(rate), 2)
        key = (label, rounded)
        if key in seen:
            continue
        seen.add(key)
        if label == "Pace required for official target":
            finish = target
        else:
            finish = as_of + timedelta(days=int(math.ceil(remaining / float(rate) * 7)))
        delta = (finish - target).days
        comparison = "target date" if delta == 0 else "{} days {}".format(abs(delta), "early" if delta < 0 else "late")
        rows.append((label, rounded, "{} ({})".format(human_date(finish), comparison)))
    return rows


def markdown_dashboard(payload: Dict[str, Any]) -> str:
    metrics = payload["metrics"]
    goal = payload["goal"]
    lines = [
        "# ARRP Review Ready Progress",
        "",
        "> **Official goal:** {} by **{}**. The target stays fixed until deliberately revised; the rolling forecast changes with observed progress.".format(
            goal["name"], human_date(date.fromisoformat(goal["targetDate"]), full_month=True)
        ),
        "",
        "| Progress | Remaining | Required pace | Rolling pace | Reforecast |",
        "| ---: | ---: | ---: | ---: | --- |",
        "| **{} / {} ({:.1f}%)** | **{}** | **{} / week** | **{}** | **{}** |".format(
            metrics["ready"],
            metrics["total"],
            metrics["percentReady"],
            metrics["remaining"],
            metrics["requiredPerWeek"] if metrics["requiredPerWeek"] is not None else "—",
            (str(metrics["rollingWeeklyVelocity"]) + " / week") if metrics["rollingWeeklyVelocity"] is not None else "Establishing history",
            human_date(date.fromisoformat(metrics["forecastDate"])) if metrics.get("forecastDate") else metrics["forecastLabel"],
        ),
        "",
        "**Tracking status:** {}  ".format(metrics["trackStatus"]),
        "**Schedule variance:** {}  ".format(
            "on the required path" if metrics["scheduleVariance"] == 0 else "{} proposal{} {} the required path".format(
                abs(metrics["scheduleVariance"]),
                "" if abs(metrics["scheduleVariance"]) == 1 else "s",
                "ahead of" if metrics["scheduleVariance"] > 0 else "behind",
            )
        ),
        "**Scope change:** {} relative to the {}-proposal baseline".format(
            "none" if metrics["scopeChange"] == 0 else "{:+d}".format(metrics["scopeChange"]), goal["baselineTotal"]
        ),
        "",
        "![Actual Review Ready progress, required path, and rolling forecast](assets/trajectory.svg)",
        "",
        "Legend: **green** is actual progress; **gold** is the path required for December 31; **purple dashes** are the rolling reforecast.",
        "",
        "## Recent portfolio movement",
        "",
    ]
    movement = payload["movement"]
    if movement["available"]:
        scores_improved = movement["scoresImproved"] if movement.get("scoresAvailable") else "—"
        scores_declined = movement["scoresDeclined"] if movement.get("scoresAvailable") else "—"
        net_score_change = (
            "{:+g}".format(movement["netScoreChange"])
            if movement.get("scoresAvailable")
            else "—"
        )
        lines.extend(
            [
                "Comparison begins with the nearest available snapshot to the {}-day lookback: **{}** ({} elapsed days).".format(
                    movement["windowDays"],
                    human_date(date.fromisoformat(movement["periodStart"])),
                    movement["elapsedDays"],
                ),
                "",
                "| Newly Review Ready | Fell below Review Ready | Scores increased | Scores declined | Net score points |",
                "| ---: | ---: | ---: | ---: | ---: |",
                "| **{}** | **{}** | **{}** | **{}** | **{}** |".format(
                    len(movement["newlyReady"]),
                    len(movement["fellBelowReady"]),
                    scores_improved,
                    scores_declined,
                    net_score_change,
                ),
                "",
            ]
        )
        if movement["newlyReady"]:
            lines.append("**Newly Review Ready:** " + ", ".join(
                "[{}]({})".format(markdown_cell(item["identifier"]), item["url"])
                for item in movement["newlyReady"]
            ))
            lines.append("")
        if movement["fellBelowReady"]:
            lines.append("**Fell below Review Ready:** " + ", ".join(
                "[{}]({})".format(markdown_cell(item["identifier"]), item["url"])
                for item in movement["fellBelowReady"]
            ))
            lines.append("")
    else:
        lines.extend(
            [
                "Movement metrics begin after the first two comparable automated snapshots. The current totals and goal forecast remain available immediately.",
                "",
            ]
        )
    lines.extend(
        [
        "## Monthly checkpoints",
        "",
        "| Checkpoint | Planned ready | Actual at checkpoint |",
        "| --- | ---: | ---: |",
        ]
    )
    for checkpoint in metrics["checkpoints"]:
        actual = "—"
        if checkpoint["date"] <= payload["asOf"]:
            candidates = [entry for entry in payload["history"] if entry["date"] <= checkpoint["date"]]
            if candidates:
                actual = str(candidates[-1]["ready"])
        lines.append("| {} | {} | {} |".format(human_date(date.fromisoformat(checkpoint["date"])), checkpoint["plannedReady"], actual))
    lines.extend(
        [
            "",
            "## Portfolio composition",
            "",
            "![Proposal counts by GitHub Project lifecycle status](assets/status-distribution.svg)",
            "",
            "![Proposal counts by score proximity to Review Ready](assets/score-proximity.svg)",
            "",
            "## Progress by area",
            "",
            "![Review Ready progress by ARRP area](assets/area-progress.svg)",
            "",
            "| Area | Ready | Total | Remaining | Percent |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for area in payload["areas"]:
        lines.append("| {} | {} | {} | {} | {:.1f}% |".format(markdown_cell(area["area"]), area["ready"], area["total"], area["remaining"], area["percentReady"]))
    lines.extend(
        [
            "",
            "## Completion-date scenarios",
            "",
            "These are planning comparisons, not automatic changes to the official target.",
            "",
            "| Sustained pace | Proposals per week | Estimated completion |",
            "| --- | ---: | --- |",
        ]
    )
    for label, rate, finish in scenario_rows(payload):
        lines.append("| {} | {:.2f} | {} |".format(markdown_cell(label), rate, markdown_cell(finish)))
    lines.extend(
        [
            "",
            "## Closest to Review Ready",
            "",
            "| Proposal | Area | Score | Status | Next audit |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for item in payload["backlog"][:15]:
        lines.append(
            "| [{}]({}) | {} | {} | {} | {} |".format(
                markdown_cell(item["identifier"]),
                item["url"],
                markdown_cell(item["area"]),
                markdown_cell(item["score"]),
                markdown_cell(item["status"]),
                markdown_cell(item["nextAudit"] or "Not recorded"),
            )
        )
    if payload["warnings"]:
        lines.extend(["", "## Tracking checks", ""])
        for warning in payload["warnings"]:
            lines.append("- [{}]({}): {}".format(markdown_cell(warning["identifier"]), warning["url"], markdown_cell(warning["message"])))
    lines.extend(
        [
            "",
            "---",
            "",
            "Project data as of **{}**. Generated at `{}` from the private [ARRP GitHub Project]({}).".format(
                human_date(date.fromisoformat(payload["asOf"]), full_month=True), payload["generatedAt"], payload["project"]["url"]
            ),
            "",
            "This branch is an automated, read-only planning view. The GitHub Project remains the authoritative workflow record; repository issue pages and audit sidecars remain the authoritative substantive record.",
            "",
        ]
    )
    return "\n".join(lines)


def write_dashboard(output: Path, payload: Dict[str, Any]) -> None:
    if output.exists():
        shutil.rmtree(str(output))
    (output / "assets").mkdir(parents=True)
    (output / "data").mkdir(parents=True)
    (output / "PROGRESS.md").write_text(markdown_dashboard(payload), encoding="utf-8")
    (output / "assets" / "trajectory.svg").write_text(trajectory_svg(payload), encoding="utf-8")
    (output / "assets" / "status-distribution.svg").write_text(
        bar_chart_svg("Lifecycle status distribution", payload["statusDistribution"], "status"), encoding="utf-8"
    )
    (output / "assets" / "score-proximity.svg").write_text(
        bar_chart_svg("Score proximity to Review Ready", payload["scoreBands"], "band"), encoding="utf-8"
    )
    (output / "assets" / "area-progress.svg").write_text(area_chart_svg(payload["areas"]), encoding="utf-8")
    write_json(output / "data" / "dashboard.json", payload)
    write_json(output / "data" / "history.json", {"schemaVersion": 1, "snapshots": payload["history"]})


def main() -> int:
    args = parse_args()
    config = read_json(args.config)
    registry_path = args.registry or Path(config["registryPath"])
    registry = read_registry(registry_path)
    as_of = date.fromisoformat(args.as_of) if args.as_of else datetime.now(timezone.utc).date()
    if args.input:
        raw = read_json(args.input)
    else:
        token = os.environ.get(args.token_env, "").strip()
        if not token:
            raise RuntimeError(
                "Missing {}. Add a repository secret containing a token with read:project access.".format(args.token_env)
            )
        raw = fetch_project(config, token)
    project_title, items = parse_items(raw, config, registry)
    if not items:
        raise RuntimeError("No eligible proposal issues were returned; refusing to publish an empty dashboard.")
    retained_history = load_history(config, args.history)
    seed_history = {"schemaVersion": 1, "snapshots": []}
    seed_path = config.get("historySeedPath")
    if seed_path:
        seed_history = valid_history(read_json(Path(seed_path)))
    history = combine_histories(seed_history, retained_history)
    payload = build_dashboard_payload(project_title, items, history, config, as_of)
    write_dashboard(args.output, payload)
    print(
        "Built Review Ready dashboard: {ready}/{total} ready; status={status}".format(
            ready=payload["metrics"]["ready"],
            total=payload["metrics"]["total"],
            status=payload["metrics"]["trackStatus"],
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, OSError, RuntimeError, ValueError) as exc:
        print("error: {}".format(exc), file=sys.stderr)
        sys.exit(1)
