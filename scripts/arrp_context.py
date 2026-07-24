#!/usr/bin/env python3
"""Read-only helpers for bounded ARRP agent context and deterministic work queues."""

from __future__ import annotations

import csv
import ast
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ModuleNotFoundError:  # The repository .venv includes PyYAML; keep read-only tools portable.
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
ISSUE_ID_RE = re.compile(r"\b(?:[A-Z][A-Z0-9]*-\d{3}|HOR-\d{3})\b")
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
PLACEHOLDER_HASHES = {"", "__SET_AT_INTEGRATION__", "AUTO", "PENDING"}


class ContextError(RuntimeError):
    """Fail-closed input, routing, freshness, or size error."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def contained_path(path: Path, root: Path = ROOT) -> Path:
    """Normalize a path and require it to remain inside one reviewed root."""
    normalized_root = os.path.realpath(os.fspath(root))
    normalized_path = os.path.realpath(os.fspath(path))
    if normalized_path != normalized_root and not normalized_path.startswith(
        normalized_root + os.sep
    ):
        raise ContextError(f"path escapes allowed root: {path}")
    return Path(normalized_path)


def sha256_path(path: Path, root: Path = ROOT) -> str:
    return sha256_bytes(contained_path(path, root).read_bytes())


def git_revision(root: Path = ROOT) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def within_root(root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise ContextError(f"path must be a nonempty repository-relative path: {relative!r}")
    resolved_root = root.resolve()
    resolved = (resolved_root / relative).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ContextError(f"path escapes repository root: {relative}")
    return resolved


def path_is_excluded(relative: str, exclusions: Iterable[str]) -> bool:
    normalized = relative.strip("/").replace("\\", "/")
    for exclusion in exclusions:
        candidate = str(exclusion).strip("/").replace("\\", "/")
        if normalized == candidate or normalized.startswith(candidate + "/"):
            return True
    return False


def load_json(path: Path, root: Path = ROOT) -> Any:
    safe_path = contained_path(path, root)
    try:
        return json.loads(safe_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextError(f"cannot read valid JSON from {safe_path}: {exc}") from exc


def file_provenance(path: Path, root: Path = ROOT) -> dict[str, Any]:
    safe_path = contained_path(path, root)
    stat = safe_path.stat()
    display = safe_path.relative_to(Path(os.path.realpath(os.fspath(root)))).as_posix()
    return {
        "path": display,
        "sha256": sha256_path(safe_path, root),
        "bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds"),
    }


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    line: int

    @property
    def exact(self) -> str:
        return f"{'#' * self.level} {self.text}"


def markdown_headings(text: str) -> list[Heading]:
    headings: list[Heading] = []
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        fence_match = re.match(r"^(```+|~~~+)", stripped)
        if fence_match:
            marker = fence_match.group(1)[0]
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            continue
        if fence is not None:
            continue
        match = HEADING_RE.match(line)
        if match:
            headings.append(Heading(len(match.group(1)), match.group(2).strip(), number))
    return headings


def extract_exact_heading(text: str, exact_heading: str) -> tuple[str, int, int]:
    matches = [heading for heading in markdown_headings(text) if heading.exact == exact_heading]
    if not matches:
        raise ContextError(f"required exact heading is missing: {exact_heading}")
    if len(matches) != 1:
        lines = ", ".join(str(item.line) for item in matches)
        raise ContextError(f"required exact heading is duplicated at lines {lines}: {exact_heading}")
    match = matches[0]
    lines = text.splitlines(keepends=True)
    end = len(lines) + 1
    for heading in markdown_headings(text):
        if heading.line > match.line and heading.level <= match.level:
            end = heading.line
            break
    return "".join(lines[match.line - 1 : end - 1]), match.line, end - 1


def load_route_manifest(path: Path, root: Path = ROOT, verify_hashes: bool = True) -> dict[str, Any]:
    path = contained_path(path, root)
    manifest = load_json(path, root)
    if manifest.get("schema_version") != 1:
        raise ContextError("context route manifest must use schema_version 1")
    documents = manifest.get("documents")
    profiles = manifest.get("profiles")
    if not isinstance(documents, dict) or not documents:
        raise ContextError("context route manifest has no documents")
    if not isinstance(profiles, dict) or not profiles:
        raise ContextError("context route manifest has no profiles")
    exclusions = manifest.get("generated_path_exclusions") or []
    seen_paths: dict[str, str] = {}
    for name, spec in documents.items():
        if not isinstance(spec, dict):
            raise ContextError(f"document {name} is not an object")
        relative = str(spec.get("path") or "")
        if path_is_excluded(relative, exclusions):
            raise ContextError(f"document {name} points to an excluded generated path: {relative}")
        if relative in seen_paths:
            raise ContextError(f"documents {seen_paths[relative]} and {name} duplicate path {relative}")
        seen_paths[relative] = name
        source = within_root(root, relative)
        if not source.is_file():
            raise ContextError(f"document {name} is missing: {relative}")
        expected = str(spec.get("sha256") or "")
        if verify_hashes:
            if expected in PLACEHOLDER_HASHES:
                raise ContextError(f"document {name} has no integration-pinned sha256")
            actual = sha256_path(source, root)
            if expected != actual:
                raise ContextError(
                    f"document {name} hash changed: expected {expected}, found {actual}"
                )
    for name, profile in profiles.items():
        if not isinstance(profile, dict) or not isinstance(profile.get("sections"), list):
            raise ContextError(f"profile {name} has no sections array")
        identities: set[tuple[str, str]] = set()
        for route in profile["sections"]:
            if not isinstance(route, dict):
                raise ContextError(f"profile {name} contains a non-object route")
            document = str(route.get("document") or "")
            heading = str(route.get("heading") or "")
            if document not in documents:
                raise ContextError(f"profile {name} references unknown document {document}")
            identity = (document, heading)
            if identity in identities:
                raise ContextError(f"profile {name} duplicates route {document}: {heading}")
            identities.add(identity)
            if not HEADING_RE.match(heading):
                raise ContextError(f"profile {name} route is not an exact ATX heading: {heading}")
            maximum = route.get("max_bytes")
            if not isinstance(maximum, int) or maximum <= 0:
                raise ContextError(f"profile {name} route {heading} has invalid max_bytes")
    return manifest


def manifest_hash_updates(path: Path, root: Path = ROOT) -> dict[str, str]:
    manifest = load_route_manifest(path, root=root, verify_hashes=False)
    return {
        name: sha256_path(within_root(root, str(spec["path"])), root)
        for name, spec in sorted(manifest["documents"].items())
    }


def front_matter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ContextError(f"unterminated front matter: {path}")
    raw = text[4:end]
    if yaml is not None:
        try:
            parsed = yaml.safe_load(raw) or {}
        except yaml.YAMLError as exc:
            raise ContextError(f"invalid YAML front matter in {path}: {exc}") from exc
    else:
        parsed = {}
        active_list: str | None = None
        for line in raw.splitlines():
            if line.startswith("  - ") and active_list:
                parsed[active_list].append(line[4:].strip().strip("\"'"))
                continue
            active_list = None
            if not line or line.startswith((" ", "\t", "#")) or ":" not in line:
                continue
            key, value = line.split(":", 1)
            key, value = key.strip(), value.strip()
            if not value:
                parsed[key] = []
                active_list = key
                continue
            lowered = value.casefold()
            if lowered in {"true", "false"}:
                parsed[key] = lowered == "true"
            elif lowered in {"null", "none", "~"}:
                parsed[key] = None
            else:
                try:
                    parsed[key] = ast.literal_eval(value)
                except (SyntaxError, ValueError):
                    parsed[key] = value.strip("\"'")
    if not isinstance(parsed, dict):
        raise ContextError(f"front matter must be a mapping: {path}")
    return parsed


def latest_markdown_entry(
    path: Path,
    parent_heading: str,
    entry_level: int = 3,
    order: str = "newest-last",
) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    parent_content, parent_start, _ = extract_exact_heading(text, parent_heading)
    entries = [heading for heading in markdown_headings(parent_content) if heading.level == entry_level]
    if not entries:
        return None
    selected = entries[-1] if order == "newest-last" else entries[0]
    content, local_start, local_end = extract_exact_heading(parent_content, selected.exact)
    return {
        "heading": selected.exact,
        "content": content,
        "start_line": parent_start + local_start - 1,
        "end_line": parent_start + local_end - 1,
    }


def source_rows(path: Path, issue_id: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            associated = str(row.get("Associated Record IDs") or "")
            if issue_id in ISSUE_ID_RE.findall(associated):
                rows.append(dict(row))
        return rows


def registry_rows(path: Path, issue_id: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = []
        for row in csv.DictReader(handle):
            title = str(row.get("GitHub Title") or "")
            record = str(row.get("Canonical Record") or "")
            if issue_id in ISSUE_ID_RE.findall(title + " " + record):
                rows.append(dict(row))
        return rows


def find_issue_page(root: Path, issue_id: str) -> Path:
    matches = sorted((root / "areas").glob(f"*/issues/{issue_id}.md"))
    matches = [path for path in matches if not path.name.endswith(".audit.md")]
    if len(matches) != 1:
        raise ContextError(f"expected exactly one canonical page for {issue_id}; found {len(matches)}")
    return matches[0]


def resolve_linked_vehicle(root: Path, issue_path: Path, metadata: dict[str, Any]) -> Path | None:
    value = metadata.get("legislative_proposal")
    if not value:
        return None
    candidates = value if isinstance(value, list) else [value]
    resolved: list[Path] = []
    for item in candidates:
        raw = str(item).strip()
        if not raw or raw.casefold() == "pending development":
            continue
        path = (issue_path.parent / raw).resolve()
        if root.resolve() not in path.parents:
            raise ContextError(f"linked vehicle escapes repository: {raw}")
        if not path.is_file():
            raise ContextError(f"linked vehicle is missing: {raw}")
        resolved.append(path)
    if len(resolved) > 1:
        raise ContextError("multiple linked vehicles require an explicit future multi-vehicle profile")
    return resolved[0] if resolved else None


def build_context_packet(
    manifest_path: Path,
    profile_name: str,
    *,
    root: Path = ROOT,
    issue_id: str | None = None,
    review_epoch_path: Path | None = None,
    max_total_bytes: int | None = None,
) -> dict[str, Any]:
    manifest_path = contained_path(manifest_path, root)
    manifest = load_route_manifest(manifest_path, root=root, verify_hashes=True)
    profile = manifest["profiles"].get(profile_name)
    if profile is None:
        raise ContextError(f"unknown context profile: {profile_name}")
    manifest_sha = sha256_path(manifest_path, root)
    sections: list[dict[str, Any]] = []
    total = 0
    for route in profile["sections"]:
        document = manifest["documents"][route["document"]]
        path = within_root(root, document["path"])
        text = path.read_text(encoding="utf-8")
        content, start, end = extract_exact_heading(text, route["heading"])
        size = len(content.encode("utf-8"))
        if size > route["max_bytes"]:
            raise ContextError(
                f"section exceeds max_bytes ({size} > {route['max_bytes']}): {route['heading']}"
            )
        total += size
        sections.append(
            {
                "document": route["document"],
                "path": document["path"],
                "sha256": document["sha256"],
                "heading": route["heading"],
                "start_line": start,
                "end_line": end,
                "bytes": size,
                "content": content,
            }
        )
    dossier: dict[str, Any] | None = None
    if issue_id:
        issue_path = find_issue_page(root, issue_id)
        metadata = front_matter(issue_path)
        audit_value = str(metadata.get("audit_history") or f"{issue_id}.audit.md")
        audit_path = (issue_path.parent / audit_value).resolve()
        if root.resolve() not in audit_path.parents:
            raise ContextError(f"audit path escapes repository: {audit_value}")
        latest_audit = None
        if audit_path.is_file():
            latest_audit = latest_markdown_entry(
                audit_path, "## Audit History", entry_level=3, order="newest-first"
            )
        vehicle = resolve_linked_vehicle(root, issue_path, metadata)
        sources_path = root / "inventory" / "sources.csv"
        pending_path = root / "inventory" / "sources-pending.csv"
        registry_path = root / "inventory" / "github_issue_registry.csv"
        dossier = {
            "issue_id": issue_id,
            "issue_page": {
                **file_provenance(issue_path, root),
                "front_matter": metadata,
                "content": issue_path.read_text(encoding="utf-8"),
            },
            "linked_vehicle": (
                {**file_provenance(vehicle, root), "content": vehicle.read_text(encoding="utf-8")}
                if vehicle
                else None
            ),
            "latest_audit_entry": (
                {
                    **latest_audit,
                    "path": audit_path.relative_to(root.resolve()).as_posix(),
                    "sha256": sha256_path(audit_path, root),
                }
                if latest_audit
                else None
            ),
            "sources": source_rows(sources_path, issue_id),
            "pending_sources": source_rows(pending_path, issue_id),
            "registry": registry_rows(registry_path, issue_id),
        }
        total += len(canonical_json(dossier))
    logs: dict[str, Any] = {}
    log_specs = (
        ("elim_last_run", root / "framework/logs/ELIM_RUN_LOG.md", "## Runs", "newest-last"),
        ("agent_last_entry", root / "framework/logs/AGENT_AUDIT_LOG.md", "## Log", "newest-last"),
    )
    for name, path, parent, order in log_specs:
        if path.is_file():
            logs[name] = {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256_path(path, root),
                "entry": latest_markdown_entry(path, parent, 3, order),
            }
    total += len(canonical_json(logs))
    review_epoch = None
    if review_epoch_path:
        review_epoch_path = contained_path(review_epoch_path, root)
        review_epoch = load_json(review_epoch_path, root)
        total += len(canonical_json(review_epoch))
    profile_limit = int(profile["max_bytes"])
    effective_limit = min(profile_limit, max_total_bytes) if max_total_bytes else profile_limit
    if total > effective_limit:
        raise ContextError(f"context packet exceeds max bytes ({total} > {effective_limit})")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repository_revision": git_revision(root),
        "profile": profile_name,
        "manifest": {
            "path": manifest_path.relative_to(
                Path(os.path.realpath(os.fspath(root)))
            ).as_posix(),
            "sha256": manifest_sha,
        },
        "limits": {"max_bytes": effective_limit, "actual_bytes": total},
        "sections": sections,
        "issue_dossier": dossier,
        "latest_logs": logs,
        "review_epoch": review_epoch,
        "provenance_complete": True,
    }


def parse_time(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    embedded = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    if embedded and not re.match(r"^\d{4}-\d{2}-\d{2}(?:$|T| )", text):
        text = embedded.group(0)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def age_days(timestamp: Any, now: datetime) -> int:
    parsed = parse_time(timestamp)
    if not parsed:
        return 0
    return max(0, int((now - parsed).total_seconds() // 86400))


def stable_work_id(kind: str, identity: str) -> str:
    digest = sha256_bytes(f"{kind}\0{identity}".encode("utf-8"))[:12]
    return f"{kind.upper().replace('_', '-')}-{digest}"


def make_item(
    *,
    kind: str,
    identity: str,
    title: str,
    owner: str,
    created_at: Any,
    now: datetime,
    source: dict[str, Any],
    base_priority: int,
    safety_class: int = 1,
    eligible: bool = True,
    reason: str = "",
    recovery: dict[str, Any] | None = None,
) -> dict[str, Any]:
    age = age_days(created_at, now)
    fairness_boost = min(age, 365)
    return {
        "id": stable_work_id(kind, identity),
        "kind": kind,
        "title": title,
        "owner": owner,
        "eligible_for_elim": bool(eligible and owner != "human"),
        "requires_human": owner == "human",
        "safety_class": safety_class,
        "base_priority": base_priority,
        "age_days": age,
        "fairness_boost": fairness_boost,
        "priority_score": base_priority + fairness_boost,
        "reason": reason,
        "source": source,
        "recovery": recovery,
    }


def input_record(
    path: Path | None,
    required: bool,
    now: datetime,
    max_age_hours: int,
    root: Path,
) -> dict[str, Any]:
    if path is None:
        return {"required": required, "status": "missing", "path": None}
    safe_path = contained_path(path, root)
    if not safe_path.is_file():
        return {"required": required, "status": "missing", "path": str(safe_path)}
    data = load_json(safe_path, root)
    generated = (
        data.get("generated_at")
        or data.get("generatedAt")
        or data.get("completed_at")
        or data.get("asOf")
        if isinstance(data, dict)
        else None
    )
    parsed = parse_time(generated)
    stale = bool(parsed and (now - parsed).total_seconds() > max_age_hours * 3600)
    status = "undated" if required and not parsed else "stale" if stale else "current"
    return {
        "required": required,
        "status": status,
        **file_provenance(safe_path, root),
        "reported_at": generated,
        "data": data,
    }


def build_work_queue(
    *,
    integrity_path: Path,
    progress_path: Path,
    intake_path: Path,
    chain_path: Path,
    recovery_path: Path | None = None,
    review_epoch_path: Path | None = None,
    now: datetime | None = None,
    max_age_hours: int = 36,
    input_root: Path = ROOT,
) -> dict[str, Any]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    records = {
        "integrity": input_record(integrity_path, True, now, max_age_hours, input_root),
        "progress": input_record(progress_path, True, now, max_age_hours, input_root),
        "intake": input_record(intake_path, True, now, max_age_hours, input_root),
        "chain": input_record(chain_path, True, now, max_age_hours, input_root),
        "recovery": input_record(recovery_path, False, now, max_age_hours, input_root),
        "review_epoch": input_record(
            review_epoch_path, False, now, max_age_hours * 40, input_root
        ),
    }
    problems = [
        f"{name} input is {record['status']}"
        for name, record in records.items()
        if record["required"] and record["status"] != "current"
    ]
    items: list[dict[str, Any]] = []
    chain = records["chain"].get("data") or {}
    expected_revision = str(chain.get("final_revision") or chain.get("revision") or "")
    revisions: dict[str, str] = {}
    for name in ("integrity", "progress"):
        data = records[name].get("data") or {}
        revision = str(data.get("revision") or data.get("repositoryRevision") or "")
        if revision:
            revisions[name] = revision
            if expected_revision and revision != expected_revision:
                problems.append(
                    f"{name} revision {revision} differs from chain revision {expected_revision}"
                )
    for bot in chain.get("bots", []) if isinstance(chain, dict) else []:
        status = str(bot.get("status") or "").casefold()
        due = bool(bot.get("due", True))
        if due and status not in {"completed", "clean", "not_due"}:
            identity = str(bot.get("id") or bot.get("name") or "unknown-bot")
            items.append(
                make_item(
                    kind="bot_failure",
                    identity=identity,
                    title=f"Repair or route failed bot: {identity}",
                    owner="agent",
                    created_at=bot.get("started_at") or chain.get("started_at"),
                    now=now,
                    source={"input": "chain", "bot": bot},
                    base_priority=1000,
                    safety_class=0,
                    reason=str(bot.get("error") or status or "missing completion proof"),
                )
            )
    integrity = records["integrity"].get("data") or {}
    for finding in integrity.get("findings", []) if isinstance(integrity, dict) else []:
        identity = str(finding.get("id") or canonical_json(finding).decode("utf-8"))
        severity = str(finding.get("severity") or "warning").casefold()
        owner = str(finding.get("attention") or "agent").casefold()
        items.append(
            make_item(
                kind="integrity",
                identity=identity,
                title=str(finding.get("message") or "Integrity finding"),
                owner="human" if owner == "human" else "agent",
                created_at=integrity.get("generated_at"),
                now=now,
                source={"input": "integrity", "finding": finding},
                base_priority=900 if severity == "error" else 800,
                safety_class=0 if severity == "error" else 1,
                reason=f"{severity} integrity finding",
            )
        )
    intake = records["intake"].get("data") or {}
    cursor = str(intake.get("last_processed_id") or "")
    pending_submissions = []
    for submission in intake.get("items", []) if isinstance(intake, dict) else []:
        state = str(submission.get("state") or "pending").casefold()
        identity = str(submission.get("id") or submission.get("url") or "")
        if not identity or state != "pending" or identity == cursor:
            continue
        pending_submissions.append(submission)
    pending_flag = bool(intake.get("pending"))
    if pending_flag and not pending_submissions:
        problems.append("intake pending flag is set but no unprocessed item follows the cursor")
    if not pending_flag and pending_submissions:
        problems.append("intake pending flag is clear but unprocessed items follow the cursor")
    for submission in pending_submissions if pending_flag else []:
        identity = str(submission.get("id") or submission.get("url") or "")
        items.append(
            make_item(
                kind="public_intake",
                identity=identity,
                title=f"Assess public submission {identity}",
                owner="agent",
                created_at=submission.get("created_at"),
                now=now,
                source={
                    "input": "intake",
                    "submission": {
                        "id": identity,
                        "url": submission.get("url"),
                        "created_at": submission.get("created_at"),
                        "content_hash": submission.get("content_hash"),
                    },
                },
                base_priority=500,
                reason="pending marker is newer than the processed cursor",
            )
        )
    progress = records["progress"].get("data") or {}
    proposals = progress.get("proposals", []) if isinstance(progress, dict) else []
    for proposal in proposals:
        identifier = str(proposal.get("identifier") or "")
        status = str(proposal.get("workflowStatus") or proposal.get("status") or "").casefold()
        next_audit = str(proposal.get("nextAudit") or "")
        changed = str(proposal.get("changeAuditNeeded") or "").casefold() in {"yes", "true", "needed"}
        if not changed and "change audit" in next_audit.casefold():
            changed = True
        kind = ""
        base = 0
        if changed:
            kind, base = "change_audit", 700
        elif status in {"audit needed", "audit in progress"}:
            kind, base = "issue_audit", 600
        elif status in {"research", "development"}:
            kind, base = "issue_development", 300
        if not kind or not identifier:
            continue
        items.append(
            make_item(
                kind=kind,
                identity=identifier,
                title=f"{identifier}: {next_audit or status}",
                owner="agent",
                created_at=proposal.get("lastAudit") or progress.get("asOf"),
                now=now,
                source={
                    "input": "progress",
                    "identifier": identifier,
                    "canonical_record": proposal.get("canonicalRecord"),
                    "workflow_status": proposal.get("workflowStatus"),
                    "development_level": proposal.get("developmentLevel"),
                    "next_audit": proposal.get("nextAudit"),
                },
                base_priority=base,
                reason=f"explicit workflow route: {status}",
            )
        )
    recovery = records["recovery"].get("data") or {}
    recovery_map: dict[str, dict[str, Any]] = {}
    for retry in recovery.get("items", []) if isinstance(recovery, dict) else []:
        original = str(retry.get("work_id") or "")
        if original:
            recovery_map[original] = retry
    for item in items:
        retry = recovery_map.get(item["id"])
        if retry:
            item["recovery"] = {
                "state": retry.get("state"),
                "attempt_count": int(retry.get("attempt_count") or 0),
                "continuation": retry.get("continuation"),
                "last_error": retry.get("last_error"),
                "next_retry_at": retry.get("next_retry_at"),
            }
            if str(retry.get("state") or "").casefold() in {"human_required", "quarantined"}:
                item["eligible_for_elim"] = False
                item["requires_human"] = True
                item["owner"] = "human"
    epoch = records["review_epoch"].get("data") or {}
    if isinstance(epoch, dict) and epoch:
        due_at = parse_time(epoch.get("next_due_at"))
        if due_at and due_at <= now:
            epoch_id = str(epoch.get("epoch_id") or epoch.get("baseline_revision") or "periodic")
            items.append(
                make_item(
                    kind="comprehensive_review",
                    identity=epoch_id,
                    title="Run the due comprehensive consistency review",
                    owner="agent",
                    created_at=epoch.get("completed_at") or epoch.get("started_at"),
                    now=now,
                    source={
                        "input": "review_epoch",
                        "epoch_id": epoch.get("epoch_id"),
                        "baseline_revision": epoch.get("baseline_revision"),
                        "next_due_at": epoch.get("next_due_at"),
                        "unresolved_ids": epoch.get("unresolved_ids") or [],
                    },
                    base_priority=650,
                    reason="periodic review boundary is due",
                )
            )
    unique: dict[str, dict[str, Any]] = {}
    for item in items:
        if item["id"] in unique:
            raise ContextError(f"duplicate deterministic work identity: {item['id']}")
        unique[item["id"]] = item
    items = sorted(
        unique.values(),
        key=lambda item: (
            item["safety_class"],
            -item["priority_score"],
            -item["age_days"],
            item["id"],
        ),
    )
    ready = not problems
    return {
        "schema_version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "repository_revision": git_revision(),
        "ready_for_elim": ready,
        "launch_recommended": ready and any(item["eligible_for_elim"] for item in items),
        "problems": problems,
        "counts": {
            "total": len(items),
            "elim_eligible": sum(bool(item["eligible_for_elim"]) for item in items),
            "human": sum(bool(item["requires_human"]) for item in items),
            "safety": sum(item["safety_class"] == 0 for item in items),
        },
        "fairness_policy": {
            "rule": "priority_score = base_priority + min(age_days, 365)",
            "safety_class_zero_precedes_all_normal work": True,
        },
        "inputs": {
            name: {key: value for key, value in record.items() if key != "data"}
            for name, record in records.items()
        },
        "revision_evidence": {"chain": expected_revision, **revisions},
        "intake_cursor": {
            "last_processed_id": cursor or None,
            "pending_flag": pending_flag,
        },
        "review_epoch": (
            {
                "epoch_id": epoch.get("epoch_id"),
                "baseline_revision": epoch.get("baseline_revision"),
                "next_due_at": epoch.get("next_due_at"),
                "unresolved_ids": epoch.get("unresolved_ids") or [],
            }
            if isinstance(epoch, dict) and epoch
            else None
        ),
        "items": items,
    }
