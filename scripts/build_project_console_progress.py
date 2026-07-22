#!/usr/bin/env python3
"""Build the ARRP Project Console progress feed from GitHub Project data."""

from __future__ import annotations

import argparse
import base64
import csv
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
USER_AGENT = "ARRP-project-console-progress/1.0"
PROPOSAL_VEHICLE_FIELDS = {
    "alternative_legislative_proposal",
    "constitutional_proposal",
    "federal_legislative_proposal",
    "legislative_proposal",
    "model_state_legislative_proposal",
    "proposal_legislation",
    "state_legislative_proposal",
}

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


def has_concrete_proposal_vehicle(repository_root: Path, canonical_record: str) -> bool:
    """Return whether an issue front matter links to an existing local proposal vehicle."""
    root = repository_root.resolve()
    issue_path = (root / canonical_record).resolve()
    try:
        issue_path.relative_to(root)
    except ValueError:
        return False
    if not issue_path.is_file():
        return False
    try:
        lines = issue_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    if not lines or lines[0].strip() != "---":
        return False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        if key.strip() not in PROPOSAL_VEHICLE_FIELDS:
            continue
        value = raw_value.strip().strip("\"'")
        if not value:
            continue
        vehicle_path = (issue_path.parent / value).resolve()
        try:
            vehicle_path.relative_to(root)
        except ValueError:
            continue
        if vehicle_path.is_file():
            return True
    return False


def parse_items(
    raw: Dict[str, Any],
    config: Dict[str, Any],
    registry: Sequence[Dict[str, str]],
    repository_root: Optional[Path] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    fields = config["projectFields"]
    ready_levels = {normalize(value) for value in config["goal"]["readyDevelopmentLevels"]}
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
        workflow_status = str(project_values.get(fields["status"], "Unspecified"))
        development_level = str(project_values.get(fields["developmentLevel"], "Unspecified"))
        score_value = project_values.get(fields["score"])
        try:
            score = float(score_value) if score_value is not None else None
        except (TypeError, ValueError):
            score = None
        area = str(project_values.get(fields["area"]) or area_from_title(title))
        level_is_ready = normalize(development_level) in ready_levels
        threshold_is_met = score is not None and score >= threshold
        is_ready = level_is_ready and threshold_is_met
        warnings: List[str] = []
        if identity_warning:
            warnings.append(identity_warning)
        if not project_values:
            if not identity_warning:
                warnings.append("Proposal registry entry has no matching Project item by Title or Canonical page.")
        if normalize(development_level) == normalize("Unspecified"):
            warnings.append("Project Development level is missing; the proposal is not counted as ready.")
        if level_is_ready and score is None:
            warnings.append(
                "Ready development level is missing a Project score and is not counted until the Review Ready threshold can be verified."
            )
        if level_is_ready and score is not None and score < threshold:
            warnings.append(
                "Ready development level is paired with a score below the Review Ready threshold and is not counted."
            )
        if not level_is_ready and score is not None and score >= threshold:
            warnings.append("Score meets the Review Ready threshold but Development level is not Review ready or higher.")
        if (
            repository_root is not None
            and normalize(workflow_status) == normalize("Pending development")
            and has_concrete_proposal_vehicle(repository_root, record)
        ):
            warnings.append(
                "Pending development may be stale because the canonical issue page links to an existing "
                "proposal vehicle; review whether the status should be In development or Audit needed."
            )
        parsed.append(
            {
                "number": int(registry_row["GitHub Number"]),
                "identifier": identifier,
                "title": title,
                "url": registry_row.get("GitHub Issue"),
                "state": None,
                "canonicalRecord": record,
                "area": area,
                "developmentLevel": development_level,
                "workflowStatus": workflow_status,
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
    branch = config.get("dataBranch")
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


def build_progress_payload(
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
    workflow_status_counts = Counter(item["workflowStatus"] for item in items)
    development_level_counts = Counter(item["developmentLevel"] for item in items)
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
        "schemaVersion": 2,
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
        "workflowStatusDistribution": [
            {"status": name, "count": count} for name, count in workflow_status_counts.most_common()
        ],
        "developmentLevelDistribution": [
            {"level": name, "count": count} for name, count in development_level_counts.most_common()
        ],
        "scoreBands": [{"band": name, "count": band_counts.get(name, 0)} for name in (
            "Review Ready or higher", "Within 15 points", "Below 60", "Unscored or fixed zero"
        )],
        "areas": areas,
        "movement": portfolio_movement(items, merged_history, as_of, int(goal["velocityWindowDays"])),
        "warnings": warnings,
        "proposals": sorted(items, key=lambda item: (item["developmentLevel"], item["identifier"])),
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


def write_progress_data(output: Path, payload: Dict[str, Any]) -> None:
    if output.exists():
        shutil.rmtree(str(output))
    output.mkdir(parents=True)
    write_json(output / "progress.json", payload)
    write_json(output / "history.json", {"schemaVersion": 1, "snapshots": payload["history"]})


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
    repository_root = registry_path.resolve().parent.parent
    project_title, items = parse_items(raw, config, registry, repository_root)
    if not items:
        raise RuntimeError("No eligible proposal issues were returned; refusing to publish an empty progress feed.")
    retained_history = load_history(config, args.history)
    seed_history = {"schemaVersion": 1, "snapshots": []}
    seed_path = config.get("historySeedPath")
    if seed_path:
        seed_history = valid_history(read_json(Path(seed_path)))
    history = combine_histories(seed_history, retained_history)
    payload = build_progress_payload(project_title, items, history, config, as_of)
    write_progress_data(args.output, payload)
    print(
        "Built Project Console progress data: {ready}/{total} ready; status={status}".format(
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
