#!/usr/bin/env python3
"""Build the ARRP Project Console progress feed from GitHub Project data."""

from __future__ import annotations

import argparse
import base64
import csv
import json
import math
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

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


GRAPHQL_URL = "https://api.github.com/graphql"
REST_ROOT = "https://api.github.com"
USER_AGENT = "ARRP-project-console-progress/1.0"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_TEMP_ROOT = Path(tempfile.gettempdir()).resolve()
APPROVED_WORKFLOW_STATUSES = (
    "Research",
    "Development",
    "Human decision needed",
    "Audit needed",
    "Audit in progress",
    "External review",
    "Publication approval",
    "Deferred",
    "Blocked",
)
APPROVED_DEVELOPMENT_LEVELS = (
    "Candidate",
    "Admitted / undeveloped",
    "In development",
    "Developed proposal",
    "Review ready",
    "Release candidate",
)
OPTIONAL_PROJECT_FIELDS = {
    "workstream": ("Workstream",),
    "priority": ("Priority",),
    "releaseBlocker": ("Release blocker",),
    "runs": ("Runs",),
    "rebaselineStatus": ("Rebaseline status",),
    "changeAuditNeeded": ("Change audit needed",),
    "parentIssue": ("Parent issue",),
    "subIssuesProgress": ("Sub-issues progress",),
    "dependency": ("Dependency", "Dependencies", "Blocked by"),
    "nextAction": ("Next action",),
    "validationRequirement": ("Validation requirement", "Validation"),
    "owner": ("Owner",),
}
PORTFOLIO_ARCHITECTURE_RECORD = Path(
    "research/portfolio-issue-consolidation-review.md"
)

PROJECT_QUERY = r"""
query($owner: String!, $number: Int!, $cursor: String) {
  user(login: $owner) {
    projectV2(number: $number) {
      title
      items(first: 100, after: $cursor) {
        totalCount
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          fieldValues(first: 100) {
            totalCount
            pageInfo {
              hasNextPage
              endCursor
            }
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
          content {
            __typename
            ... on Issue {
              number
              title
              url
              state
              repository { nameWithOwner }
              labels(first: 100) {
                totalCount
                pageInfo { hasNextPage endCursor }
                nodes { name }
              }
              assignees(first: 20) {
                totalCount
                pageInfo { hasNextPage endCursor }
                nodes { login }
              }
              milestone { title dueOn url }
              parent { number title url }
              subIssues(first: 100) {
                totalCount
                pageInfo { hasNextPage endCursor }
                nodes { number title url state }
              }
            }
            ... on PullRequest {
              number
              title
              url
              state
              repository { nameWithOwner }
              labels(first: 100) {
                totalCount
                pageInfo { hasNextPage endCursor }
                nodes { name }
              }
              assignees(first: 20) {
                totalCount
                pageInfo { hasNextPage endCursor }
                nodes { login }
              }
              milestone { title dueOn url }
            }
            ... on DraftIssue {
              title
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


def trusted_input_path(
    path: Path,
    *,
    purpose: str,
    allow_system_temp: bool = False,
) -> Path:
    """Resolve one regular input file beneath an explicit trusted root."""
    resolved_path = os.path.realpath(os.fspath(path))
    trusted_roots = [REPOSITORY_ROOT]
    if allow_system_temp:
        trusted_roots.append(SYSTEM_TEMP_ROOT)
    for trusted_root in trusted_roots:
        resolved_root = os.path.realpath(os.fspath(trusted_root))
        root_prefix = resolved_root.rstrip(os.sep) + os.sep
        if (
            resolved_path.startswith(root_prefix)
            and os.path.isfile(resolved_path)
        ):
            return Path(resolved_path)
    allowed = "the repository or system temporary directory" if allow_system_temp else "the repository"
    raise ValueError(f"{purpose} must be a regular file within {allowed}.")


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


def validate_development_level_config(config: Dict[str, Any]) -> None:
    configured_ready = {
        normalize(value)
        for value in config["goal"]["readyDevelopmentLevels"]
        if str(value).strip()
    }
    approved = {normalize(value) for value in APPROVED_DEVELOPMENT_LEVELS}
    unknown = configured_ready - approved
    if unknown:
        raise RuntimeError(
            "readyDevelopmentLevels contains a noncanonical Development level: "
            + ", ".join(sorted(unknown))
        )


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
    reported_project_total: Optional[int] = None
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
        raw_total = connection.get("totalCount")
        if raw_total is not None:
            try:
                page_total = int(raw_total)
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    "Project item pagination returned an invalid totalCount."
                ) from exc
            if reported_project_total is None:
                reported_project_total = page_total
            elif page_total != reported_project_total:
                raise RuntimeError(
                    "Project item pagination changed totalCount between pages."
                )
        page_info = connection.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            raise RuntimeError("Project pagination reported another page without a cursor.")
    if (
        reported_project_total is not None
        and reported_project_total != len(items)
    ):
        raise RuntimeError(
            "Project item pagination is incomplete: expected {} nodes but "
            "received {}.".format(reported_project_total, len(items))
        )

    def connection_is_incomplete(connection: Any) -> bool:
        if not isinstance(connection, dict):
            return False
        if ((connection.get("pageInfo") or {}).get("hasNextPage")):
            return True
        raw_total = connection.get("totalCount")
        if raw_total is None:
            return False
        try:
            total = int(raw_total)
        except (TypeError, ValueError):
            return True
        nodes = connection.get("nodes")
        return not isinstance(nodes, list) or total != len(nodes)

    incomplete_field_values = sorted(
        str(node.get("id") or "unknown")
        for node in items
        if connection_is_incomplete(node.get("fieldValues"))
    )
    if incomplete_field_values:
        raise RuntimeError(
            "Project item field-value pagination is incomplete for: "
            + ", ".join(incomplete_field_values)
        )
    incomplete_subissues = sorted(
        str(node.get("id") or "unknown")
        for node in items
        if connection_is_incomplete(
            (node.get("content") or {}).get("subIssues")
        )
    )
    if incomplete_subissues:
        raise RuntimeError(
            "Project issue sub-issue pagination is incomplete for: "
            + ", ".join(incomplete_subissues)
        )
    incomplete_content_connections = sorted(
        "{}:{}".format(node.get("id") or "unknown", connection_name)
        for node in items
        for connection_name in ("labels", "assignees")
        if connection_is_incomplete(
            (node.get("content") or {}).get(connection_name)
        )
    )
    if incomplete_content_connections:
        raise RuntimeError(
            "Project item content pagination is incomplete for: "
            + ", ".join(incomplete_content_connections)
        )
    return {
        "projectTitle": title,
        "items": items,
        "_pagination": {
            "complete": True,
            "sources": [
                {
                    "source": "github-project-items",
                    "complete": True,
                    "actual_count": len(items),
                },
                {
                    "source": "github-project-field-values",
                    "complete": True,
                    "item_count": len(items),
                    "page_size": 100,
                },
                {
                    "source": "github-project-sub-issues",
                    "complete": True,
                    "item_count": len(items),
                    "page_size": 100,
                },
                {
                    "source": "github-project-labels-and-assignees",
                    "complete": True,
                    "item_count": len(items),
                    "label_page_size": 100,
                    "assignee_page_size": 20,
                },
            ],
        },
    }


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


def field_value(
    values: Dict[str, Any],
    config_fields: Dict[str, Any],
    key: str,
    default: Any = None,
) -> Any:
    """Read a configured or well-known Project field without case sensitivity."""
    names: List[str] = []
    configured = config_fields.get(key)
    if configured:
        names.append(str(configured))
    names.extend(OPTIONAL_PROJECT_FIELDS.get(key, ()))
    normalized_values = {normalize(name): value for name, value in values.items()}
    for name in names:
        if normalize(name) in normalized_values:
            return normalized_values[normalize(name)]
    return default


def content_metadata(node: Dict[str, Any]) -> Dict[str, Any]:
    content = node.get("content") or {}
    repository = ((content.get("repository") or {}).get("nameWithOwner") or "").strip()
    number = content.get("number")
    issue_identity = (
        "{}#{}".format(repository, number)
        if repository and isinstance(number, int)
        else None
    )
    assignees = sorted(
        {
            str(entry.get("login") or "").strip()
            for entry in ((content.get("assignees") or {}).get("nodes") or [])
            if str(entry.get("login") or "").strip()
        }
    )
    labels = sorted(
        {
            str(entry.get("name") or "").strip()
            for entry in ((content.get("labels") or {}).get("nodes") or [])
            if str(entry.get("name") or "").strip()
        }
    )
    milestone = content.get("milestone") or None
    parent = content.get("parent") or None
    subissues = (content.get("subIssues") or {}).get("nodes") or []
    completed_subissues = sum(
        1 for entry in subissues if normalize(entry.get("state")) == "closed"
    )
    total_subissues = int((content.get("subIssues") or {}).get("totalCount") or 0)
    return {
        "projectItemId": node.get("id"),
        "contentType": content.get("__typename"),
        "issueIdentity": issue_identity,
        "number": number,
        "title": content.get("title"),
        "url": content.get("url"),
        "state": content.get("state"),
        "repository": repository or None,
        "assignees": assignees,
        "labels": labels,
        "milestone": milestone,
        "parentIssue": parent,
        "subissueProgress": {
            "complete": True,
            "completed": completed_subissues,
            "total": total_subissues,
            "percent": (
                round(completed_subissues / total_subissues * 100.0, 1)
                if total_subissues
                else None
            ),
            "items": subissues,
        },
    }


def operational_fields(
    project_values: Dict[str, Any],
    config_fields: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    assignees = metadata.get("assignees") or []
    owner = field_value(project_values, config_fields, "owner")
    if not owner and assignees:
        owner = ", ".join(assignees)
    parent = metadata.get("parentIssue") or field_value(
        project_values, config_fields, "parentIssue"
    )
    subissue_progress = metadata.get("subissueProgress")
    configured_subissue_progress = field_value(
        project_values, config_fields, "subIssuesProgress"
    )
    if configured_subissue_progress and subissue_progress:
        subissue_progress = {
            **subissue_progress,
            "projectValue": configured_subissue_progress,
        }
    return {
        "workstream": field_value(project_values, config_fields, "workstream"),
        "priority": field_value(project_values, config_fields, "priority"),
        "releaseBlocker": field_value(
            project_values, config_fields, "releaseBlocker"
        ),
        "runs": field_value(project_values, config_fields, "runs"),
        "rebaselineStatus": field_value(
            project_values, config_fields, "rebaselineStatus"
        ),
        "changeAuditNeeded": field_value(
            project_values, config_fields, "changeAuditNeeded"
        ),
        "owner": owner,
        "assignees": assignees,
        "milestone": metadata.get("milestone"),
        "parentIssue": parent,
        "subissueProgress": subissue_progress,
        "dependencies": field_value(project_values, config_fields, "dependency"),
        "nextAction": field_value(project_values, config_fields, "nextAction"),
        "validationRequirement": field_value(
            project_values, config_fields, "validationRequirement"
        ),
        "labels": metadata.get("labels") or [],
    }


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


def canonical_front_matter_value(
    repository_root: Optional[Path], canonical_record: str, field: str
) -> str:
    """Read one simple scalar from a canonical Markdown page without a YAML dependency."""
    if repository_root is None:
        return ""
    root = repository_root.resolve()
    path = (root / canonical_record).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return ""
    if not path.is_file():
        return ""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        if key.strip() == field:
            return raw_value.strip().strip("\"'")
    return ""


def parse_items(
    raw: Dict[str, Any],
    config: Dict[str, Any],
    registry: Sequence[Dict[str, str]],
    repository_root: Optional[Path] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    validate_development_level_config(config)
    fields = config["projectFields"]
    ready_levels = {normalize(value) for value in config["goal"]["readyDevelopmentLevels"]}
    workflow_statuses = tuple(
        str(value).strip()
        for value in config.get("workflowStatuses", APPROVED_WORKFLOW_STATUSES)
        if str(value).strip()
    )
    approved_workflow_statuses = {normalize(value) for value in workflow_statuses}
    approved_development_levels = {
        normalize(value) for value in APPROVED_DEVELOPMENT_LEVELS
    }
    threshold = float(config["goal"]["reviewReadyScore"])
    parsed: List[Dict[str, Any]] = []
    project_records: List[Dict[str, Any]] = []
    project_values_by_identifier: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    project_values_by_record: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for node in raw.get("items") or []:
        project_values = extract_field_values(node)
        metadata = content_metadata(node)
        project_title = str(
            project_values.get(fields.get("title", "Title"))
            or metadata.get("title")
            or ""
        )
        project_identifier = issue_identifier(project_title)
        record = canonical_key(project_values.get(fields["canonicalPage"]), config["repository"])
        project_record = {
            "node": node,
            "values": project_values,
            "metadata": metadata,
            "title": project_title,
            "identifier": project_identifier,
            "canonicalRecord": record,
            "matched": False,
        }
        project_records.append(project_record)
        if project_identifier:
            project_values_by_identifier[normalize(project_identifier)].append(project_record)
        if record:
            project_values_by_record[record].append(project_record)

    for registry_row in registry:
        record_kind = normalize(registry_row.get("Kind"))
        if record_kind not in {"proposal", "horizon"}:
            continue
        record = canonical_key(registry_row.get("Canonical Record"), config["repository"])
        title = str(registry_row.get("GitHub Title") or "Untitled proposal")
        identifier = issue_identifier(title)
        identifier_matches = project_values_by_identifier.get(normalize(identifier)) or []
        record_matches = project_values_by_record.get(record) or []
        identity_warning: Optional[str] = None
        if len(identifier_matches) == 1:
            project_record = identifier_matches[0]
            project_values = project_record["values"]
            project_record["matched"] = True
        elif len(identifier_matches) > 1:
            project_record = None
            project_values = {}
            identity_warning = "Multiple Project items use this proposal identifier; identity is ambiguous."
        elif len(record_matches) == 1:
            project_record = record_matches[0]
            project_values = project_record["values"]
            project_record["matched"] = True
        elif len(record_matches) > 1:
            project_record = None
            project_values = {}
            identity_warning = (
                "Project Title did not identify this proposal and Canonical page matches multiple items."
            )
        else:
            project_record = None
            project_values = {}
        metadata = project_record["metadata"] if project_record else {}
        workflow_status = str(project_values.get(fields["status"], "Unspecified"))
        development_level = str(project_values.get(fields["developmentLevel"], "Unspecified"))
        score_value = project_values.get(fields["score"])
        score_state = "missing" if score_value is None else "valid"
        try:
            score = float(score_value) if score_value is not None else None
        except (TypeError, ValueError):
            score = None
            score_state = "invalid"
        if score is not None and (not math.isfinite(score) or score < 0 or score > 100):
            score = None
            score_state = "invalid"
        area = str(project_values.get(fields["area"]) or area_from_title(title))
        level_is_ready = normalize(development_level) in ready_levels
        threshold_is_met = score is not None and score >= threshold
        is_ready = level_is_ready and threshold_is_met
        warnings: List[str] = []
        if identity_warning:
            warnings.append(identity_warning)
        if not project_values:
            if not identity_warning:
                warnings.append(
                    f"{record_kind.title()} registry entry has no matching Project "
                    "item by Title or Canonical page."
                )
        if score_state == "invalid":
            warnings.append(
                'Project Score "{}" is invalid; use a finite number from 0 through 100.'.format(
                    score_value
                )
            )
        if normalize(development_level) == normalize("Unspecified"):
            warnings.append("Project Development level is missing; the proposal is not counted as ready.")
        elif normalize(development_level) not in approved_development_levels:
            warnings.append(
                f'Project Development level "{development_level}" is not one of the '
                "six canonical maturity values; assign one of: "
                + ", ".join(APPROVED_DEVELOPMENT_LEVELS)
                + "."
            )
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
        if normalize(workflow_status) == normalize("Unspecified"):
            warnings.append(
                "Project Status is missing; assign one of the approved workflow statuses: "
                + ", ".join(workflow_statuses)
                + "."
            )
        elif normalize(workflow_status) not in approved_workflow_statuses:
            warnings.append(
                f'Project Status "{workflow_status}" is not an approved workflow status; assign one of: '
                + ", ".join(workflow_statuses)
                + ". Issue monitoring is represented independently by the needs: monitoring label."
            )
        parsed.append(
            {
                "number": int(registry_row["GitHub Number"]),
                "kind": record_kind,
                "identifier": identifier,
                "title": title,
                "url": metadata.get("url") or registry_row.get("GitHub Issue"),
                "state": metadata.get("state"),
                "projectItemId": metadata.get("projectItemId"),
                "issueIdentity": metadata.get("issueIdentity")
                or "{}#{}".format(config["repository"], registry_row["GitHub Number"]),
                "canonicalRecord": record,
                "area": area,
                "developmentLevel": development_level,
                "workflowStatus": workflow_status,
                "explanation": canonical_front_matter_value(
                    repository_root, record, "workflow_hold_reason"
                ),
                "score": score,
                "rawScore": score_value,
                "scoreState": score_state,
                "lastAudit": project_values.get(fields["lastAudit"]),
                "nextAudit": project_values.get(fields["nextAudit"]),
                "ready": is_ready,
                "isIssueDevelopment": True,
                "warnings": warnings,
                **operational_fields(project_values, fields, metadata),
            }
        )

    registry_by_number = {
        str(row.get("GitHub Number") or "").strip(): row
        for row in registry
        if str(row.get("GitHub Number") or "").strip()
    }
    registry_by_identifier = {
        normalize(issue_identifier(str(row.get("GitHub Title") or ""))): row
        for row in registry
        if str(row.get("GitHub Title") or "").strip()
    }
    for project_record in project_records:
        if project_record["matched"]:
            continue
        metadata = project_record["metadata"]
        registry_row = registry_by_number.get(str(metadata.get("number") or ""))
        if registry_row is None:
            registry_row = registry_by_identifier.get(
                normalize(project_record["identifier"])
            )
        if normalize((registry_row or {}).get("Kind")) in {"proposal", "horizon"}:
            # Active issue-development records are already projected from the
            # authoritative registry, including identity-ambiguity warnings.
            continue
        project_values = project_record["values"]
        title = str(
            (registry_row or {}).get("GitHub Title")
            or project_record["title"]
            or "Untitled Project item"
        )
        identifier = issue_identifier(title)
        record_kind = normalize((registry_row or {}).get("Kind")) or normalize(
            metadata.get("contentType")
        ) or "project item"
        workflow_status = str(project_values.get(fields["status"], "Unspecified"))
        missing_fields = [
            name
            for name, value in (
                ("status", workflow_status if workflow_status != "Unspecified" else None),
                ("workstream", field_value(project_values, fields, "workstream")),
                ("priority", field_value(project_values, fields, "priority")),
                (
                    "release_blocker",
                    field_value(project_values, fields, "releaseBlocker"),
                ),
                ("owner", field_value(project_values, fields, "owner") or metadata.get("assignees")),
                ("next_action", field_value(project_values, fields, "nextAction")),
                (
                    "validation_requirement",
                    field_value(project_values, fields, "validationRequirement"),
                ),
            )
            if value in (None, "", [])
        ]
        project_url = metadata.get("url") or (registry_row or {}).get("GitHub Issue")
        canonical_record = project_record["canonicalRecord"] or canonical_key(
            (registry_row or {}).get("Canonical Record"), config["repository"]
        )
        parsed.append(
            {
                "number": (
                    int(metadata["number"])
                    if isinstance(metadata.get("number"), int)
                    else (
                        int(registry_row["GitHub Number"])
                        if registry_row and str(registry_row.get("GitHub Number") or "").isdigit()
                        else None
                    )
                ),
                "kind": record_kind,
                "identifier": identifier,
                "title": title,
                "url": project_url,
                "state": metadata.get("state"),
                "projectItemId": metadata.get("projectItemId"),
                "issueIdentity": metadata.get("issueIdentity"),
                "canonicalRecord": canonical_record,
                "area": str(project_values.get(fields["area"]) or area_from_title(title)),
                "developmentLevel": None,
                "workflowStatus": workflow_status,
                "score": None,
                "rawScore": None,
                "scoreState": "not_applicable",
                "lastAudit": None,
                "nextAudit": None,
                "ready": False,
                "isIssueDevelopment": False,
                "warnings": [],
                "links": {
                    "projectItem": (
                        "https://github.com/users/{}/projects/{}".format(
                            config["projectOwner"], config["projectNumber"]
                        )
                    ),
                    "issue": project_url,
                    "canonical": canonical_record or None,
                },
                "completeness": {
                    "complete": not missing_fields,
                    "missingFields": missing_fields,
                },
                **operational_fields(project_values, fields, metadata),
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
        "eligibleIssues": sorted(item["identifier"] for item in items),
        "readyIssues": sorted(item["identifier"] for item in items if item["ready"]),
        "scores": {
            item["identifier"]: int(item["score"]) if item["score"].is_integer() else item["score"]
            for item in items
            if item.get("score") is not None
        },
    }


def valid_history(payload: Any, *, strict: bool = True) -> Dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("snapshots"), list):
        if strict:
            raise RuntimeError("Progress history is not a JSON object with a snapshots array.")
        return {"schemaVersion": 1, "snapshots": []}
    cleaned = []
    errors: List[str] = []
    for index, snapshot in enumerate(payload["snapshots"]):
        try:
            date.fromisoformat(str(snapshot["date"]))
            total = int(snapshot["total"])
            ready = int(snapshot["ready"])
        except (KeyError, TypeError, ValueError):
            errors.append("snapshot {} has invalid date/total/ready fields".format(index))
            continue
        if total < 0 or ready < 0 or ready > total:
            errors.append("snapshot {} has impossible total/ready counts".format(index))
            continue
        eligible_issues = sorted(
            {
                str(value)
                for value in snapshot.get("eligibleIssues") or []
                if str(value).strip()
            }
        )
        ready_issues = sorted(
            {
                str(value)
                for value in snapshot.get("readyIssues") or []
                if str(value).strip()
            }
        )
        if eligible_issues and not set(ready_issues).issubset(eligible_issues):
            errors.append(
                "snapshot {} contains ready issues outside its eligibility set".format(index)
            )
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
                "eligibleIssues": eligible_issues,
                "readyIssues": ready_issues,
                "scores": {
                    str(key): value
                    for key, value in (snapshot.get("scores") or {}).items()
                    if isinstance(value, (int, float))
                },
            }
        )
    if errors and strict:
        raise RuntimeError("Progress history validation failed: " + "; ".join(errors))
    unique = {snapshot["date"]: snapshot for snapshot in cleaned}
    return {"schemaVersion": 1, "snapshots": [unique[key] for key in sorted(unique)]}


def load_history(config: Dict[str, Any], local_path: Optional[Path]) -> Dict[str, Any]:
    if local_path:
        return valid_history(read_json(local_path))
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    branch = config.get("dataBranch")
    history_path = config.get("historyPath")
    if not token or not branch or not history_path:
        raise RuntimeError(
            "Progress history cannot be retained because GITHUB_TOKEN, dataBranch, "
            "or historyPath is unavailable."
        )
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
    except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Progress history could not be fetched and validated; refusing to "
            "replace it with an empty history: {}".format(exc)
        ) from exc


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
            "eligibleIssues": [],
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
    start_eligible = set(start.get("eligibleIssues") or [])
    current_eligible = set(current.get("eligibleIssues") or [])
    if (
        start.get("detailAvailable")
        and current.get("detailAvailable")
        and start_eligible
        and current_eligible
    ):
        comparable = start_eligible & current_eligible
        start_ready = set(start.get("readyIssues") or []) & comparable
        current_ready = set(current.get("readyIssues") or []) & comparable
        attainment = len(current_ready - start_ready)
        regression = len(start_ready - current_ready)
        net_ready_change = attainment - regression
    else:
        # Compatibility fallback for historical aggregate-only snapshots.
        net_ready_change = current["ready"] - start["ready"]
    return net_ready_change / (elapsed / 7.0)


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
        "scopeChangeMeaning": (
            "Change in separately counted eligible proposal records; it is not "
            "a completion, failure, or substantive-readiness measure."
        ),
        "forecastScopeLabel": "On track for current scope",
        "checkpoints": month_end_checkpoints(baseline, target, int(goal["baselineReady"]), snapshot["total"]),
    }


def portfolio_architecture(
    snapshot: Dict[str, Any],
    config: Dict[str, Any],
    repository_root: Optional[Path],
) -> Dict[str, Any]:
    goal = config["goal"]
    baseline_total = int(goal["baselineTotal"])
    baseline_ready = int(goal["baselineReady"])
    configured_record_path = str(
        config.get(
            "portfolioArchitectureRecord",
            PORTFOLIO_ARCHITECTURE_RECORD.as_posix(),
        )
    )
    if configured_record_path != PORTFOLIO_ARCHITECTURE_RECORD.as_posix():
        raise ValueError(
            "portfolioArchitectureRecord must use the canonical allowlisted record."
        )
    record_path = PORTFOLIO_ARCHITECTURE_RECORD.as_posix()
    record_url = "https://github.com/{}/blob/main/{}".format(
        config["repository"], record_path
    )
    appt_total: Optional[int] = None
    consolidated_total: Optional[int] = None
    if repository_root is not None:
        path = repository_root / PORTFOLIO_ARCHITECTURE_RECORD
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            appt_match = re.search(
                r"review baseline contained \*\*(\d+) active proposal records\*\*",
                text,
                flags=re.IGNORECASE,
            )
            adopted_match = re.search(
                r"to \*\*(\d+) active proposals\*\*",
                text,
                flags=re.IGNORECASE,
            )
            if appt_match:
                appt_total = int(appt_match.group(1))
            if adopted_match:
                consolidated_total = int(adopted_match.group(1))
    steps: List[Dict[str, Any]] = [
        {
            "date": goal["baselineDate"],
            "total": baseline_total,
            "delta": None,
            "reasonCode": "baseline",
            "label": "Baseline active proposal architecture",
            "countsAsAttainment": False,
            "source": None,
        }
    ]
    if appt_total is not None:
        steps.append(
            {
                "date": "2026-07-16",
                "total": appt_total,
                "delta": appt_total - baseline_total,
                "reasonCode": "approved_appt_consolidation",
                "label": "After approved APPT consolidation",
                "countsAsAttainment": False,
                "source": record_url,
            }
        )
    if consolidated_total is not None:
        prior_total = appt_total if appt_total is not None else baseline_total
        steps.append(
            {
                "date": "2026-07-16",
                "total": consolidated_total,
                "delta": consolidated_total - prior_total,
                "reasonCode": "approved_portfolio_consolidation",
                "label": "After approved portfolio consolidation",
                "countsAsAttainment": False,
                "source": record_url,
            }
        )
    prior_total = (
        consolidated_total
        if consolidated_total is not None
        else appt_total if appt_total is not None else baseline_total
    )
    current_delta = snapshot["total"] - prior_total
    current_reason = (
        "later_admissions"
        if current_delta > 0 and consolidated_total is not None
        else "later_scope_reductions"
        if current_delta < 0 and consolidated_total is not None
        else "current_scope"
    )
    steps.append(
        {
            "date": snapshot["date"],
            "total": snapshot["total"],
            "delta": current_delta,
            "reasonCode": current_reason,
            "label": (
                "Current eligible proposal scope after later admissions"
                if current_reason == "later_admissions"
                else "Current eligible proposal scope"
            ),
            "countsAsAttainment": False,
            "source": None,
        }
    )
    net_change = snapshot["total"] - baseline_total
    return {
        "available": appt_total is not None and consolidated_total is not None,
        "record": {"path": record_path, "url": record_url},
        "steps": steps,
        "netScopeChange": net_change,
        "explanation": (
            "{} means {} {} separately counted eligible proposal records than the "
            "baseline; this is not a count of completions, failures, or deletions."
        ).format(
            "{:+d}".format(net_change),
            abs(net_change),
            "fewer" if net_change < 0 else "more",
        ),
        "earnedReadiness": {
            "baselineDate": goal["baselineDate"],
            "baselineReady": baseline_ready,
            "currentDate": snapshot["date"],
            "currentReady": snapshot["ready"],
            "netEarned": snapshot["ready"] - baseline_ready,
            "separateFromScope": True,
        },
        "reasonCodes": {
            "baseline": "Starting eligible portfolio count.",
            "approved_appt_consolidation": "Human-approved APPT consolidation.",
            "approved_portfolio_consolidation": "Human-approved portfolio architecture consolidation.",
            "later_admissions": "Record-specific admissions after consolidation.",
            "later_scope_reductions": "Later reason-coded removal, merger, retirement, or reroute.",
            "current_scope": "Current eligible proposal denominator.",
        },
    }


def build_progress_payload(
    project_title: str,
    items: List[Dict[str, Any]],
    history: Dict[str, Any],
    config: Dict[str, Any],
    as_of: date,
    repository_root: Optional[Path] = None,
    contract_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    goal = config["goal"]
    threshold = float(goal["reviewReadyScore"])
    proposal_items = [
        item for item in items if normalize(item.get("kind") or "proposal") == "proposal"
    ]
    candidate_items = [
        item for item in items if normalize(item.get("kind")) == "horizon"
    ]
    delivery_items = [
        item
        for item in items
        if normalize(item.get("kind")) not in {"proposal", "horizon"}
    ]
    release_blockers = [
        item
        for item in items
        if normalize(item.get("releaseBlocker")) in {"yes", "true"}
    ]
    snapshot = build_snapshot(proposal_items, as_of)
    merged_history = merge_history(history, snapshot, config)
    workflow_status_counts = Counter(
        item["workflowStatus"] for item in proposal_items
    )
    development_level_counts = Counter(
        item["developmentLevel"] for item in proposal_items
    )
    band_counts = Counter(score_band(item, threshold) for item in proposal_items)
    area_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "ready": 0, "remaining": 0})
    warnings: List[Dict[str, Any]] = []
    for item in proposal_items:
        area_counts[item["area"]]["total"] += 1
        area_counts[item["area"]]["ready"] += int(item["ready"])
        area_counts[item["area"]]["remaining"] += int(not item["ready"])
    for item in items:
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
        (item for item in proposal_items if not item["ready"]),
        key=lambda item: (
            -(item["score"] if item["score"] is not None else -1),
            item["area"],
            item["identifier"],
        ),
    )
    generated_at = utc_timestamp()
    contract_metadata = contract_metadata or {}
    projection_errors = list(contract_metadata.get("projection_errors") or [])
    for item in items:
        if item.get("projectItemId") is None:
            projection_errors.append(
                {
                    "code": "missing_project_item",
                    "severity": "error",
                    "identifier": item.get("identifier"),
                    "message": "Registry item has no unambiguous authenticated Project item.",
                }
            )
        if item.get("scoreState") == "invalid":
            projection_errors.append(
                {
                    "code": "invalid_score",
                    "severity": "error",
                    "identifier": item.get("identifier"),
                    "message": "Project Score is outside the accepted numeric contract.",
                }
            )
    expected_count = int(contract_metadata.get("expected_count", len(items)))
    actual_count = int(
        contract_metadata.get(
            "actual_count",
            sum(1 for item in items if item.get("projectItemId") is not None),
        )
    )
    contract = feed_contract(
        feed_name="project-console-progress",
        timestamp_field="generated_at",
        timestamp=generated_at,
        revision=str(contract_metadata.get("source_revision") or ""),
        hashes=contract_metadata.get("source_hashes") or {},
        expected_count=expected_count,
        actual_count=actual_count,
        pagination=contract_metadata.get("pagination")
        or {"complete": True, "sources": []},
        projection_errors=projection_errors,
    )
    contract["freshness"] = {
        "status": contract["availability"],
        "basis": (
            "latest complete authenticated GitHub Project synchronization "
            "and declared generation inputs"
        ),
        "supersession_rule": (
            "A newer complete authenticated Project synchronization supersedes "
            "an older generation; repository HEAD alone does not."
        ),
    }
    payload = {
        "schemaVersion": 2,
        "generatedAt": generated_at,
        **contract,
        "asOf": as_of.isoformat(),
        "project": {
            "title": project_title,
            "url": "https://github.com/users/{}/projects/{}".format(config["projectOwner"], config["projectNumber"]),
            "repository": config["repository"],
        },
        "workflowStatuses": list(
            config.get("workflowStatuses", APPROVED_WORKFLOW_STATUSES)
        ),
        "developmentLevels": list(APPROVED_DEVELOPMENT_LEVELS),
        "goal": goal,
        "metrics": compute_metrics(snapshot, merged_history, config, as_of),
        "portfolioArchitecture": portfolio_architecture(
            snapshot, config, repository_root
        ),
        "earnedReadiness": {
            "baseline": int(goal["baselineReady"]),
            "current": snapshot["ready"],
            "net": snapshot["ready"] - int(goal["baselineReady"]),
            "scopeChangesExcluded": True,
        },
        "projectItemReconciliation": {
            "totalProjectItems": len(items),
            "proposalItems": len(proposal_items),
            "candidateItems": len(candidate_items),
            "portfolioItems": len(proposal_items) + len(candidate_items),
            "deliveryItems": len(delivery_items),
            "releaseBlockers": len(release_blockers),
            "partitionComplete": (
                len(items)
                == len(proposal_items)
                + len(candidate_items)
                + len(delivery_items)
            ),
            "releaseBlockerFieldProjected": all(
                "releaseBlocker" in item for item in items
            ),
        },
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
        "movement": portfolio_movement(
            proposal_items,
            merged_history,
            as_of,
            int(goal["velocityWindowDays"]),
        ),
        "warnings": warnings,
        "proposals": sorted(
            proposal_items,
            key=lambda item: (item["developmentLevel"], item["identifier"]),
        ),
        "candidates": sorted(
            candidate_items,
            key=lambda item: (item["developmentLevel"], item["identifier"]),
        ),
        "delivery_items": sorted(
            delivery_items,
            key=lambda item: (
                normalize(item.get("priority")),
                normalize(item.get("workstream")),
                item.get("identifier") or "",
            ),
        ),
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
    previous_eligible = set(start.get("eligibleIssues") or [])
    current_eligible = set(current.get("eligibleIssues") or [])
    eligibility_available = bool(previous_eligible and current_eligible)
    comparable_eligible = (
        previous_eligible & current_eligible if eligibility_available else None
    )
    if comparable_eligible is not None:
        newly_ready = (current_ready - previous_ready) & comparable_eligible
        fell_below_ready = (previous_ready - current_ready) & comparable_eligible
        scope_added = current_eligible - previous_eligible
        scope_removed = previous_eligible - current_eligible
    else:
        newly_ready = current_ready - previous_ready
        fell_below_ready = previous_ready - current_ready
        scope_added = set()
        scope_removed = set()
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
        "newlyReady": linked(newly_ready),
        "fellBelowReady": linked(fell_below_ready),
        "eligibilityDetailAvailable": eligibility_available,
        "scopeAdded": linked(scope_added),
        "scopeRemoved": linked(scope_removed),
        "scopeChangesExcludedFromAttainment": eligibility_available,
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
    config_path = trusted_input_path(args.config, purpose="Project Console config")
    config = read_json(config_path)
    registry_path = trusted_input_path(
        args.registry or Path(config["registryPath"]),
        purpose="Project issue registry",
    )
    registry = read_registry(registry_path)
    as_of = date.fromisoformat(args.as_of) if args.as_of else datetime.now(timezone.utc).date()
    if args.input:
        input_path = trusted_input_path(
            args.input,
            purpose="Saved GitHub Project input",
            allow_system_temp=True,
        )
        raw = read_json(input_path)
    else:
        token = os.environ.get(args.token_env, "").strip()
        if not token:
            raise RuntimeError(
                "Missing {}. Add a repository secret containing a token with read:project access.".format(args.token_env)
            )
        raw = fetch_project(config, token)
    repository_root = REPOSITORY_ROOT
    project_title, items = parse_items(raw, config, registry, repository_root)
    if not items:
        raise RuntimeError("No eligible proposal issues were returned; refusing to publish an empty progress feed.")
    history_path = (
        trusted_input_path(
            args.history,
            purpose="Project progress history",
            allow_system_temp=True,
        )
        if args.history
        else None
    )
    retained_history = load_history(config, history_path)
    seed_history = {"schemaVersion": 1, "snapshots": []}
    seed_path = config.get("historySeedPath")
    if seed_path:
        seed_path = trusted_input_path(
            Path(seed_path),
            purpose="Project progress history seed",
        )
        seed_history = valid_history(read_json(seed_path))
    history = combine_histories(seed_history, retained_history)
    source_paths = [config_path, registry_path]
    if seed_path:
        source_paths.append(seed_path)
    payload = build_progress_payload(
        project_title,
        items,
        history,
        config,
        as_of,
        repository_root,
        {
            "source_revision": source_revision(repository_root),
            "source_hashes": source_hashes(repository_root, source_paths),
            "expected_count": len(items),
            "actual_count": sum(
                1 for item in items if item.get("projectItemId") is not None
            ),
            "pagination": raw.get("_pagination")
            or {"complete": True, "sources": []},
        },
    )
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
