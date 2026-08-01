#!/usr/bin/env python3
"""Read-only helpers for bounded ARRP agent context and deterministic work queues."""

from __future__ import annotations

import csv
import ast
import hashlib
import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

try:
    import yaml
except ModuleNotFoundError:  # The repository .venv includes PyYAML; keep read-only tools portable.
    yaml = None

try:
    from source_monitor_recommendations import (
        RecommendationError,
        exact_head_recommendation,
        parse_source_monitor_recommendations,
    )
except ModuleNotFoundError:  # Imported as scripts.arrp_context.
    from scripts.source_monitor_recommendations import (
        RecommendationError,
        exact_head_recommendation,
        parse_source_monitor_recommendations,
    )

try:
    from path_authority import ProjectPathAuthority
except ModuleNotFoundError:
    from scripts.path_authority import ProjectPathAuthority


ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR_ROUTE_RELATIVE = (
    Path("framework") / "project" / "automation" / "context-routes.json"
)
ISSUE_ID_RE = re.compile(r"\b(?:[A-Z][A-Z0-9]*-\d{3}|HOR-\d{3})\b")
FORMAL_HORIZON_ID_RE = re.compile(r"^HOR-\d{3}$")
HORIZON_ISSUE_URL_RE = re.compile(
    r"^https://github\.com/Thorncrag/ARRP/issues/\d+$"
)
WORK_ITEM_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
WORK_KIND_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
MAX_ISSUE_ID_LENGTH = 64
MAX_REPOSITORY_RELATIVE_PATH_LENGTH = 1024
MAX_REPOSITORY_PATH_PARTS = 32
GITHUB_CANONICAL_PREFIXES = (
    "https://github.com/Thorncrag/ARRP/blob/main/",
    "https://github.com/Thorncrag/ARRP/blob/master/",
)
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
PLACEHOLDER_HASHES = {"", "__SET_AT_INTEGRATION__", "AUTO", "PENDING"}
LINKED_VEHICLE_FIELDS = (
    "legislative_proposal",
    "federal_legislative_proposal",
    "federal_legislation",
    "constitutional_proposal",
    "alternative_legislative_proposal",
    "proposal_legislation",
    "enabling_legislation",
)
SOURCE_CONTEXT_FIELDS = (
    "Source ID",
    "Associated Record IDs",
    "Monitoring",
    "Source Type",
    "Authority / Publisher",
    "Title or Description",
    "Date",
    "URL",
    "Proposition Supported",
    "Reliability Tier",
    "Reviewed?",
    "Pending Reason",
    "Next Action",
    "Blocker",
)
SOURCE_CHECKER_ACTIONABLE = {
    "broken",
    "identity mismatch",
    "review required",
}
USER_PRIORITY_SCORES = {
    "critical": 2_000,
    "high": 1_500,
    "normal": None,
    "low": -1_000,
}
WORK_ITEM_PROFILE_BY_KIND = {
    "bot_failure": "integrity_reconciliation",
    "integrity": "integrity_reconciliation",
    "public_intake": "public_intake",
    "change_audit": "change_audit",
    "issue_audit": "issue_audit",
    "issue_development": "issue_development",
    "candidate_research": "candidate_research",
    "comprehensive_review": "comprehensive_review",
}
WORK_ITEM_CLASS_BY_KIND = {
    "bot_failure": "automation_failure",
    "integrity": "integrity",
    "public_intake": "public_intake",
    "change_audit": "audit",
    "issue_audit": "audit",
    "issue_development": "development",
    "candidate_research": "research",
    "comprehensive_review": "periodic_review",
}
WORK_ITEM_DEFAULT_SEVERITY = {
    "bot_failure": "critical",
    "integrity": "warning",
    "public_intake": "normal",
    "change_audit": "high",
    "issue_audit": "high",
    "issue_development": "normal",
    "candidate_research": "normal",
    "comprehensive_review": "high",
}
WORK_ITEM_NEXT_ACTION_BY_KIND = {
    "bot_failure": "Diagnose the failed deterministic stage and repair or route it.",
    "integrity": "Resolve the exact integrity finding or route it for human review.",
    "public_intake": "Review and disposition the identified public submission.",
    "change_audit": "Run the required Change Audit against the identified record.",
    "issue_audit": "Run the due issue audit through the authorized consecutive tier.",
    "issue_development": "Perform one bounded issue-development operation.",
    "candidate_research": "Perform one bounded candidate-research operation.",
    "comprehensive_review": "Run the due comprehensive Review Epoch.",
}
GAP_OBLIGATION_OPEN_STATUSES = {
    "open",
    "investigating",
    "blocked",
    "human_required",
}
GAP_OBLIGATION_CLOSED_STATUSES = {
    "resolved",
    "human_disposition",
}
GAP_OBLIGATION_STATUSES = (
    GAP_OBLIGATION_OPEN_STATUSES | GAP_OBLIGATION_CLOSED_STATUSES
)
GAP_OBLIGATION_SEVERITY_PRIORITY = {
    "critical": 950,
    "error": 900,
    "high": 800,
    "warning": 700,
    "normal": 600,
    "low": 450,
}
MAX_GAP_OBLIGATIONS = 512
GOVERNANCE_DISCOVERY_MIN_INTERVAL_HOURS = 168
EXACT_SOURCE_REVISION_RE = re.compile(
    r"^(?:[0-9a-f]{40}|sha256:[0-9a-f]{64}|[0-9a-f]{64})$"
)


class ContextError(RuntimeError):
    """Fail-closed input, routing, freshness, or size error."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def json_safe(value: Any) -> Any:
    """Preserve structured metadata while normalizing YAML-native dates."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def contained_path(path: Path, root: Path = ROOT) -> Path:
    """Normalize a path and require it to remain inside one reviewed root."""
    normalized_root = os.path.realpath(os.fspath(root))
    normalized_path = os.path.realpath(os.fspath(path))
    if normalized_path == normalized_root:
        return Path(normalized_path)
    if normalized_path.startswith(normalized_root + os.sep):
        return Path(normalized_path)
    raise ContextError(f"path escapes allowed root: {path}")


def sha256_path(path: Path, root: Path = ROOT) -> str:
    normalized_root = os.path.realpath(os.fspath(root))
    normalized_path = os.path.realpath(os.fspath(path))
    if normalized_path.startswith(normalized_root + os.sep):
        return sha256_bytes(Path(normalized_path).read_bytes())
    raise ContextError(f"path escapes allowed root: {path}")


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


def canonical_issue_area(issue_id: str) -> str:
    """Parse one bounded AREA-NNN identifier without regex backtracking."""
    if (
        not isinstance(issue_id, str)
        or len(issue_id) > MAX_ISSUE_ID_LENGTH
        or len(issue_id) < 5
    ):
        raise ContextError(f"invalid canonical issue identifier: {issue_id!r}")
    area, separator, sequence = issue_id.partition("-")
    valid_area = (
        bool(area)
        and "A" <= area[0] <= "Z"
        and all(
            ("A" <= character <= "Z") or ("0" <= character <= "9")
            for character in area
        )
    )
    valid_sequence = len(sequence) == 3 and all(
        "0" <= character <= "9" for character in sequence
    )
    if separator != "-" or not valid_area or not valid_sequence:
        raise ContextError(f"invalid canonical issue identifier: {issue_id!r}")
    return area


def repository_relative_parts(relative: str) -> tuple[str, ...]:
    """Validate one bounded, normalized repository-relative POSIX file path."""
    if (
        not isinstance(relative, str)
        or not relative
        or len(relative) > MAX_REPOSITORY_RELATIVE_PATH_LENGTH
        or "\\" in relative
        or "\x00" in relative
    ):
        raise ContextError(
            f"path must be a bounded repository-relative POSIX path: {relative!r}"
        )
    parsed = PurePosixPath(relative)
    parts = parsed.parts
    if (
        parsed.is_absolute()
        or parsed.as_posix() != relative
        or not parts
        or len(parts) > MAX_REPOSITORY_PATH_PARTS
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ContextError(
            f"path must be an exact normalized repository-relative path: {relative!r}"
        )
    return parts


def repository_file(
    root: Path,
    relative: str,
    *,
    required: bool = True,
) -> Path | None:
    """Resolve a bounded repository file while rejecting traversal and aliases."""
    parts = repository_relative_parts(relative)
    safe_root = os.path.realpath(os.fspath(root))
    candidate = os.path.realpath(os.path.join(safe_root, relative))
    if not candidate.startswith(safe_root + os.sep):
        raise ContextError(f"path escapes allowed root: {relative}")
    actual_relative = os.path.relpath(candidate, safe_root).replace(os.sep, "/")
    if actual_relative != relative:
        raise ContextError(
            f"path must be an exact normalized repository-relative path: {relative!r}"
        )
    try:
        candidate_mode = os.stat(candidate).st_mode
    except (FileNotFoundError, NotADirectoryError):
        if required:
            raise ContextError(f"repository file is missing: {relative}")
        return None
    except OSError as exc:
        raise ContextError(f"cannot inspect repository file {relative}: {exc}") from exc
    current = candidate
    try:
        for component in reversed(parts):
            parent = os.path.dirname(current)
            if component not in os.listdir(parent):
                raise ContextError(
                    "path must use the exact repository entry spelling: "
                    f"{relative!r}"
                )
            if parent != safe_root and not parent.startswith(safe_root + os.sep):
                raise ContextError(f"path escapes allowed root: {relative}")
            current = parent
    except OSError as exc:
        raise ContextError(f"cannot inspect repository file {relative}: {exc}") from exc
    if current != safe_root:
        raise ContextError(
            f"path must be an exact normalized repository-relative path: {relative!r}"
        )
    if not stat.S_ISREG(candidate_mode):
        if required:
            raise ContextError(f"repository file is missing: {relative}")
        return None
    return Path(candidate)


def path_is_excluded(relative: str, exclusions: Iterable[str]) -> bool:
    normalized = relative.strip("/").replace("\\", "/")
    for exclusion in exclusions:
        candidate = str(exclusion).strip("/").replace("\\", "/")
        if normalized == candidate or normalized.startswith(candidate + "/"):
            return True
    return False


def load_json(path: Path, root: Path = ROOT) -> Any:
    normalized_root = os.path.realpath(os.fspath(root))
    normalized_path = os.path.realpath(os.fspath(path))
    try:
        if normalized_path.startswith(normalized_root + os.sep):
            return json.loads(Path(normalized_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextError(f"cannot read valid JSON from {normalized_path}: {exc}") from exc
    raise ContextError(f"path escapes allowed root: {path}")


def file_provenance(path: Path, root: Path = ROOT) -> dict[str, Any]:
    normalized_root = os.path.realpath(os.fspath(root))
    normalized_path = os.path.realpath(os.fspath(path))
    if normalized_path.startswith(normalized_root + os.sep):
        safe_path = Path(normalized_path)
        stat = safe_path.stat()
    else:
        raise ContextError(f"path escapes allowed root: {path}")
    display = safe_path.relative_to(Path(normalized_root)).as_posix()
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


def _document_dependency_closure(
    manifest: dict[str, Any],
    seeds: Iterable[str],
) -> list[str]:
    documents = manifest["documents"]
    resolved: list[str] = []
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name not in documents:
            raise ContextError(f"context route references unknown document {name}")
        if name in visiting:
            cycle = " -> ".join([*visiting[visiting.index(name) :], name])
            raise ContextError(f"context document dependency cycle: {cycle}")
        if name in visited:
            return
        visiting.append(name)
        for dependency in documents[name].get("requires") or []:
            visit(str(dependency))
        visiting.pop()
        visited.add(name)
        resolved.append(name)

    for seed in seeds:
        visit(str(seed))
    return resolved


def _profile_document_ids(
    manifest: dict[str, Any],
    profile: dict[str, Any],
    extra_capabilities: Iterable[str] = (),
) -> list[str]:
    seeds = [str(item) for item in manifest.get("required_modules") or []]
    seeds.extend(str(item) for item in profile.get("modules") or [])
    capabilities = manifest.get("capabilities") or {}
    selected_capabilities = [
        *(str(item) for item in profile.get("capabilities") or []),
        *(str(item) for item in extra_capabilities),
    ]
    for capability in selected_capabilities:
        if capability not in capabilities:
            raise ContextError(f"unknown context capability: {capability}")
        seeds.extend(str(item) for item in capabilities[capability])
    if profile.get("include_all_governing"):
        seeds.extend(
            name
            for name, spec in manifest["documents"].items()
            if bool(spec.get("governing"))
        )
    return _document_dependency_closure(manifest, seeds)


def _validate_section_module_conflicts(
    profile_name: str,
    profile: dict[str, Any],
    module_ids: Iterable[str],
) -> None:
    """Reject packets that would load one document both whole and by section."""
    selected_documents = set(module_ids)
    conflicts = sorted(
        {
            str(route.get("document") or "")
            for route in profile.get("sections") or []
            if isinstance(route, dict)
        }
        & selected_documents
    )
    if conflicts:
        raise ContextError(
            f"profile {profile_name} loads {', '.join(conflicts)} both as a whole "
            "module and a section"
        )


def load_route_manifest(path: Path, root: Path = ROOT, verify_hashes: bool = True) -> dict[str, Any]:
    path = contained_path(path, root)
    canonical_root = Path(os.path.realpath(os.fspath(root)))
    canonical_manifest = (
        canonical_root == ROOT.resolve()
        and path
        == canonical_root / PREDECESSOR_ROUTE_RELATIVE
    )
    manifest = load_json(path, root)
    schema_version = manifest.get("schema_version")
    if schema_version not in {1, 2}:
        raise ContextError("context route manifest must use schema_version 1 or 2")
    documents = manifest.get("documents")
    profiles = manifest.get("profiles")
    if not isinstance(documents, dict) or not documents:
        raise ContextError("context route manifest has no documents")
    if not isinstance(profiles, dict) or not profiles:
        raise ContextError("context route manifest has no profiles")
    required_modules = manifest.get("required_modules") or []
    if not isinstance(required_modules, list):
        raise ContextError("context route manifest required_modules must be an array")
    if canonical_manifest and required_modules != [
        "framework_kernel",
        "agent_rules_kernel",
        "task_handoff",
    ]:
        raise ContextError(
            "production required_modules must be exactly framework_kernel, "
            "agent_rules_kernel, task_handoff in that order"
        )
    exclusions = manifest.get("generated_path_exclusions") or []
    seen_paths: dict[str, tuple[str, str]] = {}
    for name, spec in documents.items():
        if not isinstance(spec, dict):
            raise ContextError(f"document {name} is not an object")
        relative = str(spec.get("path") or "")
        dependencies = spec.get("requires") or []
        if not isinstance(dependencies, list):
            raise ContextError(f"document {name} requires must be an array")
        if path_is_excluded(relative, exclusions):
            raise ContextError(f"document {name} points to an excluded generated path: {relative}")
        if (
            canonical_manifest
            and relative.startswith("framework/records/")
            and name != "task_handoff"
        ):
            raise ContextError(
                "shared routing records are excluded except task_handoff"
            )
        source = within_root(root, relative)
        canonical_source = os.path.realpath(os.fspath(source))
        if canonical_source in seen_paths:
            prior_name, prior_relative = seen_paths[canonical_source]
            raise ContextError(
                f"documents {prior_name} ({prior_relative}) and {name} ({relative}) "
                "duplicate one canonical path"
            )
        seen_paths[canonical_source] = (name, relative)
        if not source.is_file():
            raise ContextError(f"document {name} is missing: {relative}")
        if schema_version == 2:
            if "governing" not in spec or not isinstance(spec["governing"], bool):
                raise ContextError(
                    f"schema-2 document {name} governing must be an explicit boolean"
                )
        elif "governing" in spec and not isinstance(spec["governing"], bool):
            raise ContextError(f"document {name} governing must be a boolean")
        governing = spec.get("governing", False)
        hash_policy = str(spec.get("hash_policy") or "pinned")
        if hash_policy not in {"pinned", "runtime"}:
            raise ContextError(
                f"document {name} has invalid hash_policy {hash_policy!r}"
            )
        if hash_policy == "runtime" and governing is not False:
            raise ContextError(
                f"runtime-hashed document {name} must be explicitly non-governing"
            )
        if governing is True and hash_policy != "pinned":
            raise ContextError(
                f"governing document {name} must use hash_policy 'pinned'"
            )
        expected = str(spec.get("sha256") or "")
        if hash_policy == "runtime" and expected not in PLACEHOLDER_HASHES:
            raise ContextError(
                f"runtime-hashed document {name} must not carry a pinned sha256"
            )
        if verify_hashes and hash_policy == "pinned":
            if expected in PLACEHOLDER_HASHES:
                raise ContextError(f"document {name} has no integration-pinned sha256")
            actual = sha256_path(source, root)
            if expected != actual:
                raise ContextError(
                    f"document {name} hash changed: expected {expected}, found {actual}"
                )
    if canonical_manifest:
        runtime_documents = {
            name
            for name, spec in documents.items()
            if str(spec.get("hash_policy") or "pinned") == "runtime"
        }
        if runtime_documents != {"task_handoff"}:
            raise ContextError(
                "task_handoff must be the sole runtime-hashed shared document"
            )
        task_handoff = documents.get("task_handoff")
        if (
            not isinstance(task_handoff, dict)
            or task_handoff.get("governing") is not False
            or task_handoff.get("hash_policy") != "runtime"
            or str(task_handoff.get("sha256") or "") not in PLACEHOLDER_HASHES
        ):
            raise ContextError(
                "task_handoff must be non-governing, runtime-hashed, and unpinned"
            )
    _document_dependency_closure(manifest, documents)
    capabilities = manifest.get("capabilities") or {}
    if not isinstance(capabilities, dict):
        raise ContextError("context route manifest capabilities must be an object")
    for capability, members in capabilities.items():
        if not isinstance(members, list) or not members:
            raise ContextError(f"context capability {capability} must contain documents")
        _document_dependency_closure(manifest, (str(item) for item in members))
    for name, profile in profiles.items():
        if not isinstance(profile, dict):
            raise ContextError(f"profile {name} is not an object")
        sections = profile.get("sections") or []
        modules = profile.get("modules") or []
        profile_capabilities = profile.get("capabilities") or []
        if not isinstance(sections, list):
            raise ContextError(f"profile {name} sections must be an array")
        if not isinstance(modules, list):
            raise ContextError(f"profile {name} modules must be an array")
        if not isinstance(profile_capabilities, list):
            raise ContextError(f"profile {name} capabilities must be an array")
        if "include_all_governing" in profile and not isinstance(
            profile["include_all_governing"], bool
        ):
            raise ContextError(
                f"profile {name} include_all_governing must be a boolean"
            )
        if schema_version == 1 and not sections:
            raise ContextError(f"profile {name} has no sections array")
        if schema_version == 2 and not (
            sections
            or modules
            or profile_capabilities
            or profile.get("include_all_governing")
            or manifest.get("required_modules")
        ):
            raise ContextError(f"profile {name} has no context routes")
        identities: set[tuple[str, str]] = set()
        for route in sections:
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
        _validate_section_module_conflicts(
            name,
            profile,
            _profile_document_ids(manifest, profile),
        )
        maximum = profile.get("max_bytes")
        if not isinstance(maximum, int) or maximum <= 0:
            raise ContextError(f"profile {name} has invalid max_bytes")
    if canonical_manifest:
        comprehensive = profiles.get("comprehensive_review")
        if (
            not isinstance(comprehensive, dict)
            or comprehensive.get("include_all_governing") is not True
        ):
            raise ContextError(
                "comprehensive_review include_all_governing must be true"
            )
        expected_members = set(
            _document_dependency_closure(
                manifest,
                [
                    *required_modules,
                    *(
                        name
                        for name, spec in documents.items()
                        if spec.get("governing") is True
                    ),
                ],
            )
        )
        actual_members = set(
            _profile_document_ids(manifest, comprehensive)
        )
        if actual_members != expected_members:
            raise ContextError(
                "comprehensive_review membership must be exactly the required "
                "floor, governing documents, and dependency closure"
            )
    return manifest


def manifest_hash_updates(path: Path, root: Path = ROOT) -> dict[str, str]:
    manifest = load_route_manifest(path, root=root, verify_hashes=False)
    return {
        name: sha256_path(within_root(root, str(spec["path"])), root)
        for name, spec in sorted(manifest["documents"].items())
        if str(spec.get("hash_policy") or "pinned") == "pinned"
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
    return json_safe(parsed)


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


def source_rows(
    path: Path,
    issue_id: str,
    *,
    fields: tuple[str, ...] | None = None,
) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            associated = str(row.get("Associated Record IDs") or "")
            if issue_id in ISSUE_ID_RE.findall(associated):
                if fields is None:
                    rows.append(dict(row))
                else:
                    rows.append(
                        {
                            field: str(row.get(field) or "")
                            for field in fields
                            if str(row.get(field) or "").strip()
                        }
                    )
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


def issue_page_matches(root: Path, issue_id: str) -> list[Path]:
    """Find exact issue-page names through controlled repository traversal."""
    canonical_issue_area(issue_id)
    areas_root = contained_path(root / "areas", root)
    if not areas_root.is_dir():
        return []
    expected_name = f"{issue_id}.md"
    matches: list[Path] = []
    for area_entry in areas_root.iterdir():
        safe_area = contained_path(area_entry, root)
        if not safe_area.is_dir():
            continue
        issues_directory = contained_path(safe_area / "issues", root)
        if not issues_directory.is_dir():
            continue
        for entry in issues_directory.iterdir():
            if entry.name != expected_name:
                continue
            safe_entry = contained_path(entry, root)
            if safe_entry.is_file() and not safe_entry.name.endswith(".audit.md"):
                matches.append(safe_entry)
    return sorted(matches)


def find_issue_page(root: Path, issue_id: str) -> Path:
    matches = issue_page_matches(root, issue_id)
    if len(matches) != 1:
        raise ContextError(f"expected exactly one canonical page for {issue_id}; found {len(matches)}")
    return matches[0]


def resolve_issue_context_record(
    root: Path,
    issue_id: str,
    *,
    allow_area_readme: bool,
) -> tuple[str, Path]:
    """Resolve either a standalone issue page or the approved undeveloped area record."""
    area = canonical_issue_area(issue_id)
    matches = issue_page_matches(root, issue_id)
    if len(matches) == 1:
        return "issue_page", matches[0]
    if len(matches) > 1:
        raise ContextError(
            f"expected exactly one canonical page for {issue_id}; found {len(matches)}"
        )
    if allow_area_readme:
        area_readme = repository_file(
            root,
            f"areas/{area}/README.md",
            required=False,
        )
        if area_readme is not None:
            return "area_readme", area_readme
    raise ContextError(
        f"expected a canonical issue page for {issue_id}; found no eligible record"
    )


def resolve_linked_vehicles(
    root: Path,
    issue_path: Path,
    metadata: dict[str, Any],
) -> list[Path]:
    candidates: list[Any] = []
    for field in LINKED_VEHICLE_FIELDS:
        value = metadata.get(field)
        if value:
            candidates.extend(value if isinstance(value, list) else [value])
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
        if path not in resolved:
            resolved.append(path)
    return resolved


def context_packet_selection(
    *,
    root: Path,
    work_item_id: str | None,
    work_kind: str | None,
    canonical_record: str | None,
) -> dict[str, str | None] | None:
    """Validate and preserve the exact queue unit that authorized one packet."""
    if work_item_id is None and work_kind is None:
        if canonical_record is not None:
            raise ContextError(
                "--canonical-record requires --work-item-id and --work-kind"
            )
        return None
    if work_item_id is None or work_kind is None:
        raise ContextError(
            "--work-item-id and --work-kind must be supplied together"
        )
    if not isinstance(work_item_id, str) or not WORK_ITEM_ID_RE.fullmatch(
        work_item_id
    ):
        raise ContextError(
            "--work-item-id must be a nonblank safe identifier without whitespace"
        )
    if not isinstance(work_kind, str) or not WORK_KIND_RE.fullmatch(work_kind):
        raise ContextError(
            "--work-kind must be a nonblank lower-snake-case identifier"
        )

    normalized_record: str | None = None
    if canonical_record is not None and canonical_record != "":
        if not isinstance(canonical_record, str):
            raise ContextError("--canonical-record must be text, blank, or null")
        if canonical_record.strip() != canonical_record:
            raise ContextError(
                "--canonical-record must not contain surrounding whitespace"
            )
        if HORIZON_ISSUE_URL_RE.fullmatch(canonical_record):
            normalized_record = canonical_record
        else:
            if "://" in canonical_record:
                raise ContextError(
                    "--canonical-record contains an unsupported URL"
                )
            if "\\" in canonical_record:
                raise ContextError(
                    "--canonical-record must use a repository-relative POSIX path"
                )
            try:
                record_path = repository_file(
                    root,
                    canonical_record,
                    required=False,
                )
            except ContextError as exc:
                raise ContextError(
                    f"--canonical-record is unsafe: {exc}"
                ) from exc
            if record_path is None:
                raise ContextError(
                    f"--canonical-record is missing: {canonical_record}"
                )
            normalized_record = canonical_record

    return {
        "work_item_id": work_item_id,
        "kind": work_kind,
        "canonical_record": normalized_record,
    }


def build_context_packet(
    manifest_path: Path | Mapping[str, Any],
    profile_name: str,
    *,
    root: Path = ROOT,
    review_epoch_root: Path | None = None,
    issue_id: str | None = None,
    review_epoch_path: Path | None = None,
    max_total_bytes: int | None = None,
    capabilities: Iterable[str] = (),
    work_item_id: str | None = None,
    work_kind: str | None = None,
    canonical_record: str | None = None,
    path_authority: ProjectPathAuthority | None = None,
    routing_authority_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    selection = context_packet_selection(
        root=root,
        work_item_id=work_item_id,
        work_kind=work_kind,
        canonical_record=canonical_record,
    )
    if isinstance(manifest_path, Mapping):
        if (
            not isinstance(routing_authority_identity, Mapping)
            or set(routing_authority_identity)
            != {
                "path",
                "sha256",
                "registry_id",
                "registry_revision",
                "validation_mode",
                "authoritative",
                "executable",
                "validated_component_registry_view",
            }
            or routing_authority_identity.get(
                "validated_component_registry_view"
            )
            is not True
            or not isinstance(routing_authority_identity.get("path"), str)
            or not isinstance(routing_authority_identity.get("sha256"), str)
            or not isinstance(
                routing_authority_identity.get("registry_id"),
                str,
            )
            or not isinstance(
                routing_authority_identity.get("registry_revision"),
                int,
            )
            or routing_authority_identity.get("validation_mode")
            not in {
                "candidate_validation_only",
                "active_configuration_validation_only",
                "active_component_registry",
                "proposed_revision_validation",
                "adopted_configuration_validation",
                "live_authority_validation",
            }
            or not isinstance(
                routing_authority_identity.get("authoritative"), bool
            )
            or not isinstance(
                routing_authority_identity.get("executable"), bool
            )
            or re.fullmatch(
                r"[0-9a-f]{64}",
                str(routing_authority_identity.get("sha256") or ""),
            )
            is None
        ):
            raise ContextError(
                "in-memory routing requires a validated Component Registry identity"
            )
        manifest = json.loads(canonical_json(manifest_path))
        manifest_display_path = str(routing_authority_identity["path"])
        manifest_sha = str(routing_authority_identity["sha256"])
        routing_registry_id = str(
            routing_authority_identity["registry_id"]
        )
        routing_registry_revision = int(
            routing_authority_identity["registry_revision"]
        )
        routing_validation_mode = str(
            routing_authority_identity["validation_mode"]
        )
        routing_authoritative = bool(
            routing_authority_identity["authoritative"]
        )
        routing_executable = bool(routing_authority_identity["executable"])
    else:
        manifest_path = contained_path(manifest_path, root)
        manifest = load_route_manifest(
            manifest_path,
            root=root,
            verify_hashes=True,
        )
        manifest_display_path = manifest_path.relative_to(
            Path(os.path.realpath(os.fspath(root)))
        ).as_posix()
        manifest_sha = sha256_path(manifest_path, root)
        routing_registry_id = "context-routes"
        routing_registry_revision = int(manifest["schema_version"])
        routing_validation_mode = "predecessor_routing"
        routing_authoritative = True
        routing_executable = True
    profile = manifest["profiles"].get(profile_name)
    if profile is None:
        raise ContextError(f"unknown context profile: {profile_name}")
    requested_capabilities = [str(item) for item in capabilities]
    module_ids = _profile_document_ids(
        manifest,
        profile,
        extra_capabilities=requested_capabilities,
    )
    _validate_section_module_conflicts(profile_name, profile, module_ids)
    inclusion_reasons: dict[str, set[str]] = {
        str(identity): {"required floor"}
        for identity in manifest.get("required_modules") or []
    }
    for identity in profile.get("modules") or []:
        inclusion_reasons.setdefault(str(identity), set()).add(
            f"profile {profile_name}"
        )
    for capability in profile.get("capabilities") or []:
        for identity in manifest["capabilities"][capability]:
            inclusion_reasons.setdefault(str(identity), set()).add(
                f"profile {profile_name} capability {capability}"
            )
    for capability in requested_capabilities:
        for identity in manifest["capabilities"][capability]:
            inclusion_reasons.setdefault(str(identity), set()).add(
                f"requested capability {capability}"
            )
    if profile.get("include_all_governing"):
        for identity, document in manifest["documents"].items():
            if document.get("governing") is True:
                inclusion_reasons.setdefault(identity, set()).add(
                    f"profile {profile_name} complete governing boundary"
                )
    for identity in module_ids:
        for dependency in manifest["documents"][identity].get("requires") or []:
            inclusion_reasons.setdefault(str(dependency), set()).add(
                f"dependency of {identity}"
            )
    modules: list[dict[str, Any]] = []
    sections: list[dict[str, Any]] = []
    total = 0
    for module_id in module_ids:
        document = manifest["documents"][module_id]
        path = within_root(root, document["path"])
        content = path.read_text(encoding="utf-8")
        size = len(content.encode("utf-8"))
        actual_sha = sha256_path(path, root)
        if (
            str(document.get("hash_policy") or "pinned") == "pinned"
            and document.get("sha256") != actual_sha
        ):
            raise ContextError(
                f"document {module_id} hash changed: expected "
                f"{document.get('sha256')}, found {actual_sha}"
            )
        total += size
        modules.append(
            {
                "document": module_id,
                "path": document["path"],
                "sha256": actual_sha,
                "hash_policy": str(document.get("hash_policy") or "pinned"),
                "bytes": size,
                "content": content,
                "inclusion_reasons": sorted(
                    inclusion_reasons.get(module_id, {"dependency closure"})
                ),
            }
        )
    for route in profile.get("sections") or []:
        document = manifest["documents"][route["document"]]
        path = within_root(root, document["path"])
        text = path.read_text(encoding="utf-8")
        content, start, end = extract_exact_heading(text, route["heading"])
        size = len(content.encode("utf-8"))
        actual_sha = sha256_path(path, root)
        if (
            str(document.get("hash_policy") or "pinned") == "pinned"
            and document.get("sha256") != actual_sha
        ):
            raise ContextError(
                f"section document {route['document']} hash changed: "
                f"expected {document.get('sha256')}, found {actual_sha}"
            )
        if size > route["max_bytes"]:
            raise ContextError(
                f"section exceeds max_bytes ({size} > {route['max_bytes']}): {route['heading']}"
            )
        total += size
        sections.append(
            {
                "document": route["document"],
                "path": document["path"],
                "sha256": actual_sha,
                "hash_policy": str(document.get("hash_policy") or "pinned"),
                "heading": route["heading"],
                "start_line": start,
                "end_line": end,
                "bytes": size,
                "content": content,
            }
        )
    dossier: dict[str, Any] | None = None
    if issue_id:
        record_kind, canonical_path = resolve_issue_context_record(
            root,
            issue_id,
            allow_area_readme=profile_name == "issue_development",
        )
        sources_path = root / "inventory" / "sources.csv"
        pending_path = root / "inventory" / "sources-pending.csv"
        registry_path = root / "inventory" / "github_issue_registry.csv"
        issue_page = None
        generic_record = None
        vehicles: list[Path] = []
        latest_audit_record = None
        canonical_provenance = file_provenance(canonical_path, root)
        if record_kind == "issue_page":
            metadata = front_matter(canonical_path)
            expected_audit_name = f"{issue_id}.audit.md"
            audit_value = str(
                metadata.get("audit_history") or expected_audit_name
            )
            if audit_value != expected_audit_name:
                raise ContextError(
                    f"audit_history for {issue_id} must name its exact sibling "
                    f"{expected_audit_name}: {audit_value!r}"
                )
            audit_relative = (
                PurePosixPath(canonical_provenance["path"]).parent
                / expected_audit_name
            ).as_posix()
            audit_path = repository_file(
                root,
                audit_relative,
                required=False,
            )
            latest_audit = None
            if audit_path is not None:
                latest_audit = latest_markdown_entry(
                    audit_path, "## Audit History", entry_level=3, order="newest-first"
                )
            vehicles = resolve_linked_vehicles(root, canonical_path, metadata)
            issue_page = {
                **canonical_provenance,
                "front_matter": metadata,
                "content": canonical_path.read_text(encoding="utf-8"),
            }
            latest_audit_record = (
                {
                    **latest_audit,
                    "path": file_provenance(audit_path, root)["path"],
                    "sha256": sha256_path(audit_path, root),
                }
                if latest_audit
                else None
            )
        else:
            generic_record = {
                **canonical_provenance,
                "content": canonical_path.read_text(encoding="utf-8"),
            }
        dossier = {
            "issue_id": issue_id,
            "canonical_record_kind": record_kind,
            "canonical_record_path": canonical_provenance["path"],
            "canonical_record": generic_record,
            "issue_page": issue_page,
            "linked_vehicles": [
                {
                    **file_provenance(vehicle, root),
                    "content": vehicle.read_text(encoding="utf-8"),
                }
                for vehicle in vehicles
            ],
            "latest_audit_entry": latest_audit_record,
            "source_catalog": {
                **file_provenance(sources_path, root),
                "projection_only": True,
                "projection_fields": list(SOURCE_CONTEXT_FIELDS),
                "canonical_row_required_before_reliance": True,
            },
            "sources": source_rows(
                sources_path,
                issue_id,
                fields=SOURCE_CONTEXT_FIELDS,
            ),
            "pending_source_catalog": {
                **file_provenance(pending_path, root),
                "projection_only": True,
                "projection_fields": list(SOURCE_CONTEXT_FIELDS),
                "canonical_row_required_before_reliance": True,
            },
            "pending_sources": source_rows(
                pending_path,
                issue_id,
                fields=SOURCE_CONTEXT_FIELDS,
            ),
            "registry": registry_rows(registry_path, issue_id),
        }
        total += len(canonical_json(dossier))
    logs: dict[str, Any] = {}
    repository_log_root = within_root(root, "framework/records/automation")
    use_owner_local_logs = (
        path_authority is not None
        and path_authority.mode
        in {"production_canonical", "production_transaction"}
    )
    log_root = (
        path_authority.state_root / "records" / "automation"
        if use_owner_local_logs
        else repository_log_root
    )
    log_specs = (
        (
            "elim_last_run",
            log_root / "elim-run-log.md",
            (
                "owner-local:records/automation/elim-run-log.md"
                if use_owner_local_logs
                else "framework/records/automation/elim-run-log.md"
            ),
            "## Runs",
            "newest-last",
        ),
        (
            "agent_last_entry",
            log_root / "agent-audit-log.md",
            (
                "owner-local:records/automation/agent-audit-log.md"
                if use_owner_local_logs
                else "framework/records/automation/agent-audit-log.md"
            ),
            "## Log",
            "newest-last",
        ),
    )
    for name, path, display_path, parent, order in log_specs:
        if path.is_file():
            logs[name] = {
                "path": display_path,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "entry": latest_markdown_entry(path, parent, 3, order),
            }
    total += len(canonical_json(logs))
    review_epoch = None
    if review_epoch_path:
        reviewed_record_root = review_epoch_root or root
        review_epoch_path = contained_path(
            review_epoch_path,
            reviewed_record_root,
        )
        review_epoch = load_json(review_epoch_path, reviewed_record_root)
        total += len(canonical_json(review_epoch))
    if selection is not None:
        total += len(canonical_json(selection))
    profile_limit = int(profile["max_bytes"])
    effective_limit = min(profile_limit, max_total_bytes) if max_total_bytes else profile_limit
    if total > effective_limit:
        raise ContextError(f"context packet exceeds max bytes ({total} > {effective_limit})")
    selected_capabilities = list(
        dict.fromkeys(
            [
                *(str(item) for item in profile.get("capabilities") or []),
                *requested_capabilities,
            ]
        )
    )
    resolved_document_revisions = {
        module["document"]: {
            "path": module["path"],
            "hash_policy": module["hash_policy"],
        }
        for module in modules
    }
    resolved_document_digests = {
        module["document"]: module["sha256"]
        for module in modules
    }
    exact_sections = [
        {
            key: section[key]
            for key in (
                "document",
                "path",
                "sha256",
                "hash_policy",
                "heading",
                "start_line",
                "end_line",
                "bytes",
            )
        }
        for section in sections
    ]
    return {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repository_revision": git_revision(root),
        "profile": profile_name,
        "selection": selection,
        "manifest": {
            "path": manifest_display_path,
            "sha256": manifest_sha,
        },
        "limits": {"max_bytes": effective_limit, "actual_bytes": total},
        "capabilities": selected_capabilities,
        "routing_manifest": {
            "registry_id": routing_registry_id,
            "registry_path": manifest_display_path,
            "registry_revision": routing_registry_revision,
            "validation_mode": routing_validation_mode,
            "authoritative": routing_authoritative,
            "executable": routing_executable,
            "registry_digest": manifest_sha,
            "selected_profile": profile_name,
            "selected_capabilities": selected_capabilities,
            "resolved_document_revisions": resolved_document_revisions,
            "resolved_document_digests": resolved_document_digests,
            "resolved_document_order": [
                module["document"] for module in modules
            ],
            "dependency_closure": {
                module["document"]: list(
                    manifest["documents"][module["document"]].get(
                        "requires"
                    )
                    or []
                )
                for module in modules
            },
            "exact_sections": exact_sections,
            "dynamic_expansions": [],
            "inclusion_reasons": {
                module["document"]: module["inclusion_reasons"]
                for module in modules
            },
        },
        "modules": modules,
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


def _nonblank_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _safe_repository_relative_path(value: Any) -> bool:
    if not _nonblank_string(value):
        return False
    path = Path(str(value))
    return not path.is_absolute() and ".." not in path.parts


def validate_gap_obligation_state(value: Any) -> list[dict[str, Any]]:
    """Validate the host-retained, exact-history gap-obligation ledger."""
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "updated_at",
        "governance_review",
        "items",
    }:
        raise ContextError("gap-obligation state fields do not match the approved schema")
    if value.get("schema_version") != 1:
        raise ContextError("gap-obligation state schema_version must be 1")
    if value.get("updated_at") is not None and parse_time(value.get("updated_at")) is None:
        raise ContextError("gap-obligation state updated_at is invalid")
    governance_review = value.get("governance_review")
    if governance_review is not None:
        governance_fields = {
            "last_reviewed_at",
            "run_id",
            "selected_unit_id",
            "discovered_work_unit_id",
            "source_revision",
            "disposition",
            "canonical_detail",
            "next_trigger",
        }
        if (
            not isinstance(governance_review, dict)
            or set(governance_review) != governance_fields
            or parse_time(governance_review.get("last_reviewed_at")) is None
            or not all(
                _nonblank_string(governance_review.get(field))
                for field in (
                    "run_id",
                    "selected_unit_id",
                    "discovered_work_unit_id",
                    "source_revision",
                    "next_trigger",
                )
            )
            or EXACT_SOURCE_REVISION_RE.fullmatch(
                str(governance_review.get("source_revision") or "")
            )
            is None
            or governance_review.get("disposition")
            not in {"no_material_finding", "review_completed"}
            or not _safe_repository_relative_path(
                governance_review.get("canonical_detail")
            )
        ):
            raise ContextError("gap-obligation governance-review state is malformed")
    items = value.get("items")
    if not isinstance(items, list):
        raise ContextError("gap-obligation state items must be an array")
    if len(items) > MAX_GAP_OBLIGATIONS:
        raise ContextError("gap-obligation state exceeds its bounded capacity")

    required = {
        "obligation_id",
        "title",
        "domain",
        "severity",
        "status",
        "owner",
        "authority",
        "authority_disposition",
        "canonical_detail",
        "provenance",
        "source_revision",
        "evidence",
        "reasoning",
        "uncertainty",
        "affected_records",
        "affected_surfaces",
        "consequence",
        "action_rationale",
        "validation_readback",
        "disposition",
        "exact_next_action",
        "next_trigger",
        "first_seen",
        "last_checked",
        "occurrence_count",
        "age_days",
        "last_discovered_work_unit_id",
        "occurrences",
        "status_history",
        "resolution",
    }
    identities: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict) or set(item) != required:
            raise ContextError(
                "gap-obligation item fields do not match the approved schema"
            )
        obligation_id = str(item.get("obligation_id") or "")
        if not WORK_ITEM_ID_RE.fullmatch(obligation_id):
            raise ContextError("gap-obligation item has an invalid stable identity")
        if obligation_id in identities:
            raise ContextError("gap-obligation state repeats a stable identity")
        identities.add(obligation_id)
        for field in (
            "title",
            "domain",
            "severity",
            "owner",
            "source_revision",
            "reasoning",
            "consequence",
            "exact_next_action",
            "next_trigger",
            "last_discovered_work_unit_id",
        ):
            if not _nonblank_string(item.get(field)):
                raise ContextError(f"gap-obligation item requires {field}")
        if (
            EXACT_SOURCE_REVISION_RE.fullmatch(item["source_revision"]) is None
        ):
            raise ContextError("gap-obligation source revision is not exact")
        if item.get("status") not in GAP_OBLIGATION_STATUSES:
            raise ContextError("gap-obligation item has an invalid status")
        authority = item.get("authority")
        if not isinstance(authority, dict) or set(authority) != {
            "classification",
            "basis",
        }:
            raise ContextError("gap-obligation authority is malformed")
        if authority.get("classification") not in {
            "mechanical",
            "delegated_judgment",
            "human_reserved",
        } or not _nonblank_string(authority.get("basis")):
            raise ContextError("gap-obligation authority is invalid")
        if item.get("authority_disposition") not in {
            "permitted",
            "human_reserved",
            "forbidden",
            "unsafe",
            "out_of_scope",
            "uncertain",
        }:
            raise ContextError("gap-obligation authority disposition is invalid")
        if not _safe_repository_relative_path(item.get("canonical_detail")):
            raise ContextError("gap-obligation canonical detail path is unsafe")
        for field in ("provenance", "evidence", "affected_records"):
            entries = item.get(field)
            if not isinstance(entries, list) or not all(
                _nonblank_string(entry) for entry in entries
            ):
                raise ContextError(f"gap-obligation {field} must be a string array")
        if not item["provenance"] or not item["evidence"]:
            raise ContextError(
                "gap-obligation provenance and evidence may not be empty"
            )
        if item.get("uncertainty") is not None and not _nonblank_string(
            item.get("uncertainty")
        ):
            raise ContextError("gap-obligation uncertainty must be null or nonblank")
        surfaces = item.get("affected_surfaces")
        allowed_surfaces = {
            "repository",
            "github_issue",
            "github_project",
            "source",
            "monitoring",
            "automation",
            "console",
            "publication",
            "public",
        }
        if (
            not isinstance(surfaces, list)
            or not surfaces
            or len(surfaces) != len(set(surfaces))
            or not set(surfaces) <= allowed_surfaces
        ):
            raise ContextError("gap-obligation affected surfaces are invalid")
        if not _nonblank_string(item.get("action_rationale")):
            raise ContextError("gap-obligation action rationale is required")
        if item.get("disposition") not in {"fixed", "reported", "retained"}:
            raise ContextError("gap-obligation disposition is invalid")
        validation = item.get("validation_readback")
        if not isinstance(validation, list):
            raise ContextError(
                "gap-obligation validation and readback must be an array"
            )
        validation_fields = {"check", "status", "evidence"}
        for check in validation:
            if (
                not isinstance(check, dict)
                or set(check) != validation_fields
                or not _nonblank_string(check.get("check"))
                or check.get("status") not in {"passed", "failed", "skipped"}
                or not _nonblank_string(check.get("evidence"))
            ):
                raise ContextError(
                    "gap-obligation validation and readback entry is malformed"
                )
        first_seen = parse_time(item.get("first_seen"))
        last_checked = parse_time(item.get("last_checked"))
        if first_seen is None or last_checked is None or last_checked < first_seen:
            raise ContextError("gap-obligation observation times are invalid")
        if (
            isinstance(item.get("occurrence_count"), bool)
            or not isinstance(item.get("occurrence_count"), int)
            or item["occurrence_count"] < 1
            or isinstance(item.get("age_days"), bool)
            or not isinstance(item.get("age_days"), int)
            or item["age_days"] < 0
        ):
            raise ContextError("gap-obligation occurrence or age fields are invalid")
        occurrences = item.get("occurrences")
        history = item.get("status_history")
        if (
            not isinstance(occurrences, list)
            or len(occurrences) != item["occurrence_count"]
            or not isinstance(history, list)
            or not history
        ):
            raise ContextError("gap-obligation retained history is incomplete")
        occurrence_fields = {
            "at",
            "run_id",
            "discovered_work_unit_id",
            "source_revision",
            "status",
            "canonical_detail",
        }
        for occurrence in occurrences:
            if (
                not isinstance(occurrence, dict)
                or set(occurrence) != occurrence_fields
                or parse_time(occurrence.get("at")) is None
                or occurrence.get("status") not in GAP_OBLIGATION_STATUSES
                or not all(
                    _nonblank_string(occurrence.get(field))
                    for field in (
                        "run_id",
                        "discovered_work_unit_id",
                        "source_revision",
                    )
                )
                or EXACT_SOURCE_REVISION_RE.fullmatch(
                    str(occurrence.get("source_revision") or "")
                )
                is None
                or not _safe_repository_relative_path(
                    occurrence.get("canonical_detail")
                )
            ):
                raise ContextError("gap-obligation occurrence history is malformed")
        history_fields = {"status", "at", "run_id", "evidence", "resolution"}
        for transition in history:
            if (
                not isinstance(transition, dict)
                or set(transition) != history_fields
                or transition.get("status") not in GAP_OBLIGATION_STATUSES
                or parse_time(transition.get("at")) is None
                or not _nonblank_string(transition.get("run_id"))
                or not _nonblank_string(transition.get("evidence"))
            ):
                raise ContextError("gap-obligation status history is malformed")
            transition_resolution = transition.get("resolution")
            if transition_resolution is not None and (
                not isinstance(transition_resolution, dict)
                or set(transition_resolution)
                != {
                    "kind",
                    "verified_at",
                    "evidence",
                    "source_revision",
                    "recorded_by",
                }
                or transition_resolution.get("kind")
                not in {"verified_resolution", "human_disposition"}
                or parse_time(transition_resolution.get("verified_at")) is None
                or not _nonblank_string(transition_resolution.get("evidence"))
                or not _nonblank_string(
                    transition_resolution.get("source_revision")
                )
                or EXACT_SOURCE_REVISION_RE.fullmatch(
                    str(transition_resolution.get("source_revision") or "")
                )
                is None
                or not _nonblank_string(transition_resolution.get("recorded_by"))
            ):
                raise ContextError(
                    "gap-obligation status history resolution proof is malformed"
                )
        resolution = item.get("resolution")
        if item["status"] in GAP_OBLIGATION_CLOSED_STATUSES:
            if not isinstance(resolution, dict) or set(resolution) != {
                "kind",
                "verified_at",
                "evidence",
                "source_revision",
                "recorded_by",
            }:
                raise ContextError(
                    "closed gap-obligation item lacks exact resolution proof"
                )
            if (
                resolution.get("kind")
                not in {"verified_resolution", "human_disposition"}
                or parse_time(resolution.get("verified_at")) is None
                or not _nonblank_string(resolution.get("evidence"))
                or not _nonblank_string(resolution.get("source_revision"))
                or EXACT_SOURCE_REVISION_RE.fullmatch(
                    str(resolution.get("source_revision") or "")
                )
                is None
                or not _nonblank_string(resolution.get("recorded_by"))
            ):
                raise ContextError("gap-obligation resolution proof is invalid")
            if (
                item["status"] == "resolved"
                and resolution["kind"] != "verified_resolution"
            ) or (
                item["status"] == "human_disposition"
                and resolution["kind"] != "human_disposition"
            ):
                raise ContextError(
                    "gap-obligation closed status contradicts its resolution proof"
                )
            if item["status"] == "resolved" and item[
                "authority_disposition"
            ] in {"forbidden", "unsafe", "out_of_scope", "uncertain"}:
                raise ContextError(
                    "a prohibited, unsafe, out-of-scope, or uncertain finding "
                    "cannot close as a verified repair"
                )
            if (
                item["status"] == "resolved"
                and (
                    item["disposition"] != "fixed"
                    or not validation
                    or any(check["status"] != "passed" for check in validation)
                )
            ):
                raise ContextError(
                    "verified gap resolution requires fixed disposition and passing "
                    "validation/readback proof"
                )
        elif resolution is not None:
            raise ContextError(
                "open gap-obligation item may not carry resolution proof"
            )
        normalized.append(dict(item))
    return normalized


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
    source_revision: str | None = None,
    freshness_timestamp: Any = None,
    severity: str | None = None,
) -> dict[str, Any]:
    if kind not in WORK_ITEM_PROFILE_BY_KIND:
        raise ContextError(f"unsupported deterministic work kind: {kind!r}")
    age = age_days(created_at, now)
    fairness_boost = min(age, 365)
    source_input = str(source.get("input") or "").strip()
    canonical_identity = str(
        source.get("canonical_record")
        or source.get("canonicalRecord")
        or identity
    ).strip()
    required_authority = "human" if owner == "human" else "agent-within-runbook"
    created_text = str(created_at or "").strip() or None
    refreshed_text = str(freshness_timestamp or created_at or "").strip() or None
    return {
        "schema_version": 1,
        "id": stable_work_id(kind, identity),
        "kind": kind,
        "work_class": WORK_ITEM_CLASS_BY_KIND[kind],
        "severity": severity or WORK_ITEM_DEFAULT_SEVERITY[kind],
        "title": title,
        "owner": owner,
        "required_authority": required_authority,
        "exact_next_action": WORK_ITEM_NEXT_ACTION_BY_KIND[kind],
        "required_context_profile": WORK_ITEM_PROFILE_BY_KIND[kind],
        "originating_stage": source_input or None,
        "source_identity": identity,
        "canonical_record_identity": canonical_identity,
        "dependencies": [source_input] if source_input else [],
        "created_at": created_text,
        "refreshed_at": refreshed_text,
        "eligible_for_elim": bool(eligible and owner != "human"),
        "requires_human": owner == "human",
        "eligibility_reason": (
            "eligible under the selected runbook"
            if eligible and owner != "human"
            else "reserved for human review"
            if owner == "human"
            else "not eligible under the selected runbook"
        ),
        "blocking_reason": (
            "human authority is required" if owner == "human" else None
        ),
        "safety_class": safety_class,
        "base_priority": base_priority,
        "age_days": age,
        "fairness_boost": fairness_boost,
        "priority_score": base_priority + fairness_boost,
        "selection_priority_score": base_priority + fairness_boost,
        "reason": reason,
        "source": source,
        "source_revision": source_revision,
        "freshness_timestamp": str(freshness_timestamp or "") or None,
        "source_chain_id": None,
        "source_commit": None,
        "source_project_snapshot": None,
        "source_input_hashes": {},
        "retry_state": {
            "state": str((recovery or {}).get("state") or "new"),
            "attempt_count": int((recovery or {}).get("attempt_count") or 0),
            "continuation": (recovery or {}).get("continuation"),
            "next_retry_at": (recovery or {}).get("next_retry_at"),
        },
        "recovery": recovery,
    }


def apply_user_overrides(
    items: Iterable[dict[str, Any]],
    overrides: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Apply reviewed local-console overrides before deterministic selection."""
    copied = [dict(item) for item in items]
    if overrides is None:
        overrides = {}
    if not isinstance(overrides, dict):
        raise ContextError("queue overrides must be an object keyed by work-unit ID")
    by_id = {str(item.get("id") or ""): item for item in copied}
    if len(by_id) != len(copied) or "" in by_id:
        raise ContextError("queue items must have unique nonempty IDs before overrides")
    applied: list[str] = []
    unmatched: list[str] = []
    for work_id, raw in sorted(overrides.items()):
        if not isinstance(work_id, str) or not WORK_ITEM_ID_RE.fullmatch(work_id):
            raise ContextError(f"queue override has invalid work-unit ID: {work_id!r}")
        if not isinstance(raw, dict):
            raise ContextError(f"queue override {work_id} must be an object")
        if raw.get("source") != "user-local-console":
            raise ContextError(
                f"queue override {work_id} is not an approved local-console override"
            )
        suppressed = raw.get("suppressed") is True
        priority = raw.get("priority")
        if suppressed and priority is not None:
            raise ContextError(
                f"queue override {work_id} cannot suppress and reprioritize simultaneously"
            )
        if not suppressed and priority not in USER_PRIORITY_SCORES:
            raise ContextError(
                f"queue override {work_id} must suppress or use a reviewed priority"
            )
        item = by_id.get(work_id)
        if item is None:
            unmatched.append(work_id)
            continue
        override = {
            key: raw.get(key)
            for key in (
                "request_id",
                "source",
                "created_at",
                "reason",
                "priority",
                "suppressed",
            )
            if raw.get(key) is not None
        }
        item["user_override"] = override
        if suppressed:
            item["eligible_for_elim"] = False
            item["suppressed"] = True
            item["blocking_reason"] = str(raw.get("reason") or "Suppressed by the user.")
        else:
            score = USER_PRIORITY_SCORES[str(priority)]
            item["selection_priority_score"] = (
                item["priority_score"] if score is None else score
            )
            item["priority_override"] = priority
        applied.append(work_id)
    copied.sort(
        key=lambda item: (
            int(item.get("safety_class", 1)),
            -int(
                item.get(
                    "selection_priority_score",
                    item.get("priority_score", 0),
                )
            ),
            -int(item.get("age_days", 0)),
            item["id"],
        )
    )
    return copied, applied, unmatched


def finalize_work_item_contract(
    item: dict[str, Any],
    *,
    chain_id: str,
    source_commit: str,
    project_snapshot: str,
    input_records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Bind one queue item to the exact chain and verified deterministic inputs."""
    source_input = str((item.get("source") or {}).get("input") or "").strip()
    source_record = input_records.get(source_input) or {}
    source_hash = str(source_record.get("sha256") or "").strip()
    source_revision = str(item.get("source_revision") or source_hash).strip()
    refreshed_at = str(
        item.get("refreshed_at")
        or item.get("freshness_timestamp")
        or source_record.get("reported_at")
        or item.get("created_at")
        or ""
    ).strip()

    item["source_chain_id"] = chain_id
    item["source_commit"] = source_commit
    item["source_project_snapshot"] = project_snapshot
    item["source_revision"] = source_revision or None
    item["freshness_timestamp"] = refreshed_at or None
    item["refreshed_at"] = refreshed_at or None
    item["required_authority"] = (
        "human"
        if item.get("requires_human") or item.get("owner") == "human"
        else "agent-within-runbook"
    )
    item["source_input_hashes"] = (
        {source_input: f"sha256:{source_hash}"}
        if source_input and source_hash
        else {}
    )

    dependencies = [
        str(value).strip()
        for value in item.get("dependencies", [])
        if str(value).strip()
    ]
    canonical_record = str(item.get("canonical_record_identity") or "").strip()
    if canonical_record and canonical_record != item.get("source_identity"):
        dependencies.append(canonical_record)
    item["dependencies"] = list(dict.fromkeys(dependencies))

    recovery = item.get("recovery") if isinstance(item.get("recovery"), dict) else {}
    item["retry_state"] = {
        "state": str(recovery.get("state") or "new"),
        "attempt_count": int(recovery.get("attempt_count") or 0),
        "continuation": recovery.get("continuation"),
        "next_retry_at": recovery.get("next_retry_at"),
    }
    if item.get("suppressed"):
        item["eligibility_reason"] = "suppressed by an approved user override"
    elif item.get("requires_human"):
        item["eligibility_reason"] = "human authority is required"
        item["blocking_reason"] = str(
            item.get("blocking_reason")
            or recovery.get("last_error")
            or recovery.get("continuation")
            or "human authority is required"
        )
    elif item.get("retry_deferred_until"):
        item["eligibility_reason"] = "retry is deferred until its recorded time"
        item["blocking_reason"] = (
            f"retry deferred until {item['retry_deferred_until']}"
        )
    elif item.get("eligible_for_elim"):
        item["eligibility_reason"] = "eligible under the selected runbook"
        item["blocking_reason"] = None
    else:
        item["eligibility_reason"] = str(
            item.get("eligibility_reason") or "not eligible under the selected runbook"
        )

    required_nonempty = (
        "id",
        "kind",
        "work_class",
        "severity",
        "title",
        "owner",
        "required_authority",
        "exact_next_action",
        "required_context_profile",
        "source_identity",
        "canonical_record_identity",
        "source_chain_id",
        "source_commit",
        "source_project_snapshot",
        "eligibility_reason",
    )
    missing = [
        key for key in required_nonempty if not str(item.get(key) or "").strip()
    ]
    if missing:
        raise ContextError(
            f"queue item {item.get('id') or '<unknown>'} lacks contract fields: "
            + ", ".join(missing)
        )
    if not isinstance(item.get("dependencies"), list):
        raise ContextError(f"queue item {item['id']} dependencies must be an array")
    if not isinstance(item.get("retry_state"), dict):
        raise ContextError(f"queue item {item['id']} retry_state must be an object")
    if not isinstance(item.get("source_input_hashes"), dict):
        raise ContextError(
            f"queue item {item['id']} source_input_hashes must be an object"
        )
    return item


def validate_queue_canonical_record(
    root: Path,
    identifier: str,
    value: Any,
    *,
    formal_horizon: bool,
    allow_area_readme: bool = False,
) -> tuple[str | None, str | None]:
    """Return one safe canonical record or a fail-closed queue problem."""
    text = str(value or "").strip().strip("`")
    if not text:
        return None, f"{identifier} has no canonicalRecord in the progress feed"

    if formal_horizon and HORIZON_ISSUE_URL_RE.fullmatch(text):
        return text, None

    for prefix in GITHUB_CANONICAL_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    if "://" in text:
        return None, f"{identifier} has an unsupported canonicalRecord URL: {text}"
    while text.startswith("./"):
        text = text[2:]
    try:
        path = repository_file(root, text, required=False)
    except ContextError as exc:
        return None, f"{identifier} has an unsafe canonicalRecord: {exc}"
    if path is None:
        return None, f"{identifier} canonicalRecord is missing: {text}"
    normalized = file_provenance(path, root)["path"]
    if re.fullmatch(r"areas/[^/]+/README\.md", normalized, re.IGNORECASE):
        area = identifier.split("-", 1)[0]
        expected_area_readme = f"areas/{area}/README.md"
        if allow_area_readme and normalized == expected_area_readme:
            return normalized, None
        return None, (
            f"{identifier} canonicalRecord points to an area README that is not "
            f"eligible for this work: {normalized}"
        )

    if formal_horizon:
        if normalized != "framework/logs/candidates/candidate-discovery-log.md":
            return (
                None,
                f"{identifier} formal-candidate canonicalRecord is not its GitHub Issue "
                f"or framework/logs/candidates/candidate-discovery-log.md: {normalized}",
            )
        return normalized, None

    area = identifier.split("-", 1)[0]
    expected = f"areas/{area}/issues/{identifier}.md"
    if normalized != expected:
        return (
            None,
            f"{identifier} canonicalRecord does not match its canonical issue page "
            f"{expected}: {normalized}",
        )
    return normalized, None


def input_record(
    path: Path | None,
    required: bool,
    now: datetime,
    max_age_hours: int,
    root: Path,
) -> dict[str, Any]:
    if path is None:
        return {"required": required, "status": "missing", "path": None}
    normalized_root = os.path.realpath(os.fspath(root))
    normalized_path = os.path.realpath(os.fspath(path))
    if normalized_path.startswith(normalized_root + os.sep):
        safe_path = Path(normalized_path)
        exists = safe_path.is_file()
    else:
        raise ContextError(f"path escapes allowed root: {path}")
    if not exists:
        return {"required": required, "status": "missing", "path": str(safe_path)}
    data = load_json(safe_path, root)
    generated = (
        data.get("generated_at")
        or data.get("generatedAt")
        or data.get("checked_at")
        or data.get("completed_at")
        or data.get("asOf")
        or data.get("updated_at")
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


def pending_source_domain_proposal(
    report: Any,
    expected_agent: str,
) -> dict[str, Any] | None:
    """Validate the minimized complete-PR projection carried by a watcher report."""

    if not isinstance(report, dict) or "pending_proposal" not in report:
        return None
    pending = report["pending_proposal"]
    if not isinstance(pending, dict) or set(pending) != {
        "event_id",
        "agent_id",
        "proposal",
        "affected_records",
        "summary",
    }:
        raise ContextError(f"{expected_agent} has a malformed pending proposal")
    if pending["agent_id"] != expected_agent:
        raise ContextError(f"{expected_agent} pending proposal names another agent")
    event_id = str(pending["event_id"])
    if not re.fullmatch(r"SDE-[A-F0-9]{24}", event_id):
        raise ContextError(f"{expected_agent} pending proposal has an invalid event ID")
    proposal = pending["proposal"]
    if not isinstance(proposal, dict) or set(proposal) != {
        "repository",
        "base_ref",
        "head_ref",
        "pull_request_number",
        "pull_request_url",
        "proposal_revision",
    }:
        raise ContextError(f"{expected_agent} pending proposal has malformed PR data")
    number = proposal["pull_request_number"]
    if not isinstance(number, int) or number < 1:
        raise ContextError(f"{expected_agent} pending proposal has an invalid PR number")
    if proposal["pull_request_url"] != f"https://github.com/Thorncrag/ARRP/pull/{number}":
        raise ContextError(f"{expected_agent} pending proposal has an invalid PR URL")
    if not re.fullmatch(r"[a-f0-9]{40}", str(proposal["proposal_revision"])):
        raise ContextError(
            f"{expected_agent} pending proposal has an invalid head revision"
        )
    affected = pending["affected_records"]
    summary = pending["summary"]
    if not isinstance(affected, list) or not isinstance(summary, dict):
        raise ContextError(
            f"{expected_agent} pending proposal has malformed affected records"
        )
    if summary.get("affected_record_count") != len(affected):
        raise ContextError(
            f"{expected_agent} pending proposal affected-record count disagrees"
        )
    return pending


def build_work_queue(
    *,
    integrity_path: Path,
    progress_path: Path,
    intake_path: Path,
    chain_path: Path,
    recovery_path: Path | None = None,
    run_log_reconciliation_path: Path | None = None,
    gap_obligations_path: Path | None = None,
    review_epoch_path: Path | None = None,
    source_checker_path: Path | None = None,
    case_monitor_path: Path | None = None,
    presidential_directives_path: Path | None = None,
    overrides_path: Path | None = None,
    now: datetime | None = None,
    max_age_hours: int = 36,
    source_checker_max_age_hours: int = 192,
    governance_minimum_interval_hours: int = (
        GOVERNANCE_DISCOVERY_MIN_INTERVAL_HOURS
    ),
    input_root: Path = ROOT,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    # Queue feeds may live under a narrow run root, but repository-owned
    # authority continues to come from the reviewed checkout unless a caller
    # expressly supplies another repository root.
    reviewed_repository_root = repository_root or ROOT
    records = {
        "integrity": input_record(integrity_path, True, now, max_age_hours, input_root),
        "progress": input_record(progress_path, True, now, max_age_hours, input_root),
        "intake": input_record(intake_path, True, now, max_age_hours, input_root),
        "chain": input_record(chain_path, True, now, max_age_hours, input_root),
        "recovery": input_record(recovery_path, False, now, max_age_hours, input_root),
        "run_log_reconciliation": input_record(
            run_log_reconciliation_path,
            False,
            now,
            max_age_hours * 3650,
            input_root,
        ),
        "gap_obligations": input_record(
            gap_obligations_path,
            False,
            now,
            max_age_hours * 3650,
            input_root,
        ),
        "review_epoch": input_record(
            review_epoch_path, False, now, max_age_hours * 40, input_root
        ),
        "source_checker": input_record(
            source_checker_path,
            False,
            now,
            source_checker_max_age_hours,
            input_root,
        ),
        "case_monitor": input_record(
            case_monitor_path, False, now, max_age_hours, input_root
        ),
        "presidential_directives": input_record(
            presidential_directives_path,
            False,
            now,
            max_age_hours,
            input_root,
        ),
        "overrides": input_record(
            overrides_path,
            False,
            now,
            max_age_hours * 3650,
            input_root,
        ),
    }
    problems = [
        f"{name} input is {record['status']}"
        for name, record in records.items()
        if record["required"] and record["status"] != "current"
    ]
    source_monitor_recommendations: list[dict[str, Any]] = []
    source_monitor_log = contained_path(
        reviewed_repository_root
        / "framework"
        / "logs"
        / "sources"
        / "source-monitor-log.md",
        reviewed_repository_root,
    )
    if source_monitor_log.is_file():
        try:
            source_monitor_recommendations = parse_source_monitor_recommendations(
                source_monitor_log.read_text(encoding="utf-8")
            )
        except (OSError, RecommendationError) as exc:
            problems.append(f"source-monitor recommendation log is invalid: {exc}")
    items: list[dict[str, Any]] = []
    chain = records["chain"].get("data") or {}
    chain_id = str(chain.get("chain_id") or chain.get("run_id") or "").strip()
    if not chain_id:
        problems.append("chain input has no chain_id")
    expected_revision = str(chain.get("final_revision") or chain.get("revision") or "")
    if not expected_revision:
        problems.append("chain input has no final repository revision")
    project_snapshot_hash = str(records["progress"].get("sha256") or "").strip()
    project_snapshot = (
        f"sha256:{project_snapshot_hash}" if project_snapshot_hash else ""
    )
    if not project_snapshot:
        problems.append("progress input has no Project snapshot hash")
    revisions: dict[str, str] = {}
    for name in ("integrity", "progress"):
        data = records[name].get("data") or {}
        if data.get("collection_status") == "unavailable":
            problems.append(f"{name} collection is unavailable")
        revision = str(data.get("revision") or data.get("repositoryRevision") or "")
        if revision:
            revisions[name] = revision
            if expected_revision and revision != expected_revision:
                problems.append(
                    f"{name} revision {revision} differs from chain revision {expected_revision}"
                )
    stages = {
        str(stage.get("id") or ""): stage
        for stage in chain.get("stages", [])
        if isinstance(stage, dict) and stage.get("id")
    }
    typed_inputs = {
        "source-checker-bot": "source_checker",
        "case-monitor-bot": "case_monitor",
        "presidential-directives-bot": "presidential_directives",
    }
    trusted_typed_inputs: set[str] = set()
    for stage_id, input_name in typed_inputs.items():
        stage = stages.get(stage_id) or {}
        record = records[input_name]
        stage_due_now = stage.get("due") is True
        stage_status = str(stage.get("status") or "").casefold()
        collection_unavailable = (
            (record.get("data") or {}).get("collection_status") == "unavailable"
        )
        if stage_due_now and stage_status == "succeeded":
            if record["status"] != "current" or collection_unavailable:
                problems.append(
                    f"{input_name} report is unavailable or {record['status']} "
                    "after a successful due stage"
                )
                continue
            expected_hash = str((stage.get("output") or {}).get("sha256") or "")
            actual_hash = (
                "sha256:" + str(record.get("sha256") or "")
                if record.get("sha256")
                else ""
            )
            if expected_hash and actual_hash != expected_hash:
                problems.append(
                    f"{input_name} report hash differs from the due stage output"
                )
                continue
            trusted_typed_inputs.add(input_name)
        elif stage_due_now:
            # The bot-failure queue item carries the failure. Partial output is
            # preserved as evidence but is not trusted for substantive routing.
            continue
        elif record["status"] == "current" and not collection_unavailable:
            trusted_typed_inputs.add(input_name)
        elif stage.get("last_success_at"):
            problems.append(
                f"{input_name} report is {record['status']} despite a recorded prior success"
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
                    severity="critical",
                    reason=str(bot.get("error") or status or "missing completion proof"),
                )
            )
    reconciliation = records["run_log_reconciliation"].get("data") or {}
    if reconciliation:
        if (
            not isinstance(reconciliation, dict)
            or reconciliation.get("schema_version") != 1
            or not isinstance(reconciliation.get("items"), list)
        ):
            raise ContextError("Run Log reconciliation input is malformed")
        pending_rows: list[dict[str, Any]] = []
        pending_chain_ids: list[str] = []
        for row in reconciliation["items"]:
            if not isinstance(row, dict):
                raise ContextError(
                    "Run Log reconciliation input contains a non-object item"
                )
            chain_identity = str(row.get("chain_id") or "").strip()
            invocation_identity = str(row.get("invocation_id") or "").strip()
            if (
                not WORK_ITEM_ID_RE.fullmatch(chain_identity)
                or not WORK_ITEM_ID_RE.fullmatch(invocation_identity)
            ):
                raise ContextError(
                    "Run Log reconciliation input contains an invalid identity"
                )
            if chain_identity in pending_chain_ids:
                raise ContextError(
                    "Run Log reconciliation input repeats a Chain ID"
                )
            pending_chain_ids.append(chain_identity)
            pending_rows.append(
                {
                    "chain_id": chain_identity,
                    "invocation_id": invocation_identity,
                    "recorded_at": row.get("recorded_at"),
                    "spawned_at": row.get("spawned_at"),
                    "failure_stage": row.get("failure_stage"),
                    "reason_code": row.get("reason_code"),
                    "failure_summary": row.get("failure_summary"),
                    "selected_work_item_id": row.get("selected_work_item_id"),
                    "selected_kind": row.get("selected_kind"),
                    "source_revision": row.get("source_revision"),
                    "execution_checkout": row.get("execution_checkout"),
                    "artifacts": row.get("artifacts") or {},
                }
            )
        if len(pending_rows) > 128:
            raise ContextError(
                "Run Log reconciliation input exceeds its bounded capacity"
            )
        if pending_rows:
            snapshot_hash = str(
                records["run_log_reconciliation"].get("sha256") or ""
            )
            identity = canonical_json(
                {
                    "pending_chain_ids": pending_chain_ids,
                    "snapshot_sha256": snapshot_hash,
                }
            ).decode("utf-8")
            items.append(
                make_item(
                    kind="bot_failure",
                    identity="elim-run-log-reconciliation:" + identity,
                    title=(
                        "Reconcile missing Elim Run Log reports "
                        f"({len(pending_rows)} pending)"
                    ),
                    owner="agent",
                    created_at=pending_rows[0].get("recorded_at"),
                    now=now,
                    source={
                        "input": "run_log_reconciliation",
                        "finding_type": "elim_run_log_reconciliation",
                        "pending_chain_ids": pending_chain_ids,
                        "pending_records": pending_rows,
                        "reconciliation_snapshot_sha256": (
                            "sha256:" + snapshot_hash
                            if snapshot_hash
                            else None
                        ),
                    },
                    base_priority=1100,
                    safety_class=0,
                    severity="critical",
                    reason=(
                        "A prior launched Elim invocation lacks a verified canonical "
                        "Run Log report"
                    ),
                    source_revision=snapshot_hash,
                    freshness_timestamp=reconciliation.get("updated_at"),
                )
            )
    gap_state = records["gap_obligations"].get("data")
    governance_review: dict[str, Any] | None = None
    if gap_state is not None:
        gap_items = validate_gap_obligation_state(gap_state)
        governance_review = gap_state.get("governance_review")
        gap_snapshot = str(records["gap_obligations"].get("sha256") or "")
        for obligation in gap_items:
            if obligation["status"] in GAP_OBLIGATION_CLOSED_STATUSES:
                continue
            human_owned = (
                obligation["status"] == "human_required"
                or obligation["authority"]["classification"] == "human_reserved"
                or obligation["authority_disposition"] == "human_reserved"
                or obligation["owner"].casefold() == "human"
            )
            implementation_prohibited = obligation["authority_disposition"] in {
                "forbidden",
                "unsafe",
                "out_of_scope",
            }
            eligible = (
                not human_owned
                and not implementation_prohibited
                and obligation["status"] in {"open", "investigating"}
            )
            item = make_item(
                kind="integrity",
                identity=f"gap-obligation:{obligation['obligation_id']}",
                title=obligation["title"],
                owner="human" if human_owned else "agent",
                created_at=obligation["first_seen"],
                now=now,
                source={
                    "input": "gap_obligations",
                    "finding_type": "gap_obligation",
                    "obligation_id": obligation["obligation_id"],
                    "obligation_status": obligation["status"],
                    "obligation_projection": {
                        "severity": obligation["severity"],
                        "owner": obligation["owner"],
                        "authority": obligation["authority"],
                        "authority_disposition": obligation[
                            "authority_disposition"
                        ],
                        "disposition": obligation["disposition"],
                        "first_seen": obligation["first_seen"],
                        "last_checked": obligation["last_checked"],
                        "occurrence_count": obligation["occurrence_count"],
                        "age_days": obligation["age_days"],
                        "canonical_detail": obligation["canonical_detail"],
                        "exact_next_action": obligation["exact_next_action"],
                        "next_trigger": obligation["next_trigger"],
                        "source_revision": obligation["source_revision"],
                    },
                    "canonicalRecord": obligation["canonical_detail"],
                    "canonical_record": obligation["canonical_detail"],
                },
                base_priority=GAP_OBLIGATION_SEVERITY_PRIORITY.get(
                    obligation["severity"].casefold(),
                    GAP_OBLIGATION_SEVERITY_PRIORITY["normal"],
                ),
                eligible=eligible,
                reason=(
                    "Retained gap obligation; follow the canonical detail record "
                    "rather than a copied narrative."
                ),
                source_revision=obligation["source_revision"] or gap_snapshot,
                freshness_timestamp=obligation["last_checked"],
                severity=obligation["severity"],
            )
            item["work_class"] = "gap_stewardship"
            item["exact_next_action"] = obligation["exact_next_action"]
            item["dependencies"] = list(
                dict.fromkeys(
                    [
                        "gap_obligations",
                        obligation["canonical_detail"],
                        *obligation["affected_records"],
                    ]
                )
            )
            item["gap_obligation_id"] = obligation["obligation_id"]
            if obligation["status"] == "blocked" and not human_owned:
                item["eligibility_reason"] = (
                    "retained until its recorded next trigger occurs"
                )
                item["blocking_reason"] = obligation["next_trigger"]
            elif implementation_prohibited:
                item["eligibility_reason"] = (
                    "retained as a non-implementable obligation under the recorded "
                    f"{obligation['authority_disposition']} authority disposition"
                )
                item["blocking_reason"] = obligation["next_trigger"]
            items.append(item)
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
                severity="error" if severity == "error" else "warning",
                reason=f"{severity} integrity finding",
            )
        )
    source_checker = records["source_checker"].get("data") or {}
    if "source_checker" in trusted_typed_inputs:
        source_revision = records["source_checker"].get("sha256")
        for finding in (
            source_checker.get("results", [])
            if isinstance(source_checker, dict)
            else []
        ):
            if not isinstance(finding, dict):
                problems.append("source_checker report contains a non-object result")
                continue
            classification = " ".join(
                str(finding.get("classification") or "").casefold().split()
            )
            if classification not in SOURCE_CHECKER_ACTIONABLE:
                continue
            source_id = str(finding.get("source_id") or "").strip()
            catalog = str(finding.get("catalog") or "").strip()
            if not source_id or not catalog:
                problems.append(
                    "source_checker actionable result lacks source_id or catalog"
                )
                continue
            identity = f"source-checker:{catalog}:{source_id}:{classification}"
            base = {
                "identity mismatch": 880,
                "broken": 860,
                "review required": 750,
            }[classification]
            items.append(
                make_item(
                    kind="integrity",
                    identity=identity,
                    title=f"{source_id}: {classification}",
                    owner="agent",
                    created_at=source_checker.get("checked_at"),
                    now=now,
                    source={
                        "input": "source_checker",
                        "finding_type": "source_checker",
                        "source_id": source_id,
                        "catalog": catalog,
                        "finding": finding,
                    },
                    base_priority=base,
                    safety_class=0 if classification != "review required" else 1,
                    severity=(
                        "error"
                        if classification in {"broken", "identity mismatch"}
                        else "warning"
                    ),
                    reason=f"Source Checker classified {source_id} as {classification}",
                    source_revision=source_revision,
                    freshness_timestamp=source_checker.get("checked_at"),
                )
            )
    case_monitor = records["case_monitor"].get("data") or {}
    if "case_monitor" in trusted_typed_inputs:
        source_revision = records["case_monitor"].get("sha256")
        checked_at = case_monitor.get("checked_at")
        pending = pending_source_domain_proposal(case_monitor, "case-monitor-bot")
        recommendation = (
            exact_head_recommendation(
                source_monitor_recommendations,
                pending["proposal"]["pull_request_number"],
                pending["proposal"]["proposal_revision"],
            )
            if pending
            else None
        )
        if pending and (not recommendation or recommendation["action_owner"] == "Elim"):
            proposal = pending["proposal"]
            recommendation_reason = (
                f"Implement exact-head recommendation {recommendation['id']}"
                if recommendation
                else "Complete watcher proposal requires source and relevance review"
            )
            items.append(
                make_item(
                    kind="integrity",
                    identity=f"source-domain-proposal:{pending['event_id']}:{recommendation['id'] if recommendation else 'review'}",
                    title=(
                        f"Review complete Case Monitor PR #{proposal['pull_request_number']} "
                        f"({pending['summary']['affected_record_count']} affected records)"
                    ),
                    owner="agent",
                    created_at=checked_at,
                    now=now,
                    source={
                        "input": "case_monitor",
                        "finding_type": "source_domain_proposal",
                        "pending_proposal": pending,
                        "recommendation": recommendation,
                        "canonicalRecord": "framework/logs/sources/source-monitor-log.md",
                        "canonical_record": "framework/logs/sources/source-monitor-log.md",
                    },
                    base_priority=730,
                    reason=recommendation_reason,
                    source_revision=source_revision,
                    freshness_timestamp=checked_at,
                )
            )
        for finding in (
            []
            if pending
            else case_monitor.get("changes", [])
            if isinstance(case_monitor, dict)
            else []
        ):
            if not isinstance(finding, dict):
                problems.append("case_monitor report contains a non-object change")
                continue
            stable_key = str(finding.get("stable_key") or "").strip()
            if not stable_key:
                problems.append("case_monitor change lacks stable_key")
                continue
            identity_payload = {
                key: finding.get(key)
                for key in (
                    "kind",
                    "stable_key",
                    "tracker_status",
                    "last_case_update",
                    "changed_fields",
                )
            }
            items.append(
                make_item(
                    kind="integrity",
                    identity="case-monitor:" + canonical_json(identity_payload).decode("utf-8"),
                    title=(
                        "Case monitor: "
                        + str(finding.get("case_name") or stable_key)
                    ),
                    owner="agent",
                    created_at=checked_at,
                    now=now,
                    source={
                        "input": "case_monitor",
                        "finding_type": "case_monitor_change",
                        "finding": finding,
                    },
                    base_priority=720,
                    reason="Machine-observed monitored-case change requires review",
                    source_revision=source_revision,
                    freshness_timestamp=checked_at,
                )
            )
        for module in (
            []
            if pending
            else case_monitor.get("source_development_modules", [])
            if isinstance(case_monitor, dict)
            else []
        ):
            if not isinstance(module, dict):
                problems.append(
                    "case_monitor report contains a non-object source-development module"
                )
                continue
            module_id = str(module.get("module_id") or "").strip()
            for lead_id in module.get("added_lead_ids") or []:
                lead_id = str(lead_id).strip()
                if not module_id or not lead_id:
                    problems.append(
                        "case_monitor source-development lead lacks module or lead identity"
                    )
                    continue
                items.append(
                    make_item(
                        kind="integrity",
                        identity=f"case-monitor-lead:{module_id}:{lead_id}",
                        title=f"Review machine-observed case lead {lead_id}",
                        owner="agent",
                        created_at=checked_at,
                        now=now,
                        source={
                            "input": "case_monitor",
                            "finding_type": "case_monitor_lead",
                            "module": module,
                            "lead_id": lead_id,
                            "canonicalRecord": module.get("target_path"),
                            "canonical_record": module.get("target_path"),
                        },
                        base_priority=710,
                        reason="New source-development lead requires primary-record review",
                        source_revision=source_revision,
                        freshness_timestamp=checked_at,
                    )
                )
    directives = records["presidential_directives"].get("data") or {}
    if "presidential_directives" in trusted_typed_inputs:
        source_revision = records["presidential_directives"].get("sha256")
        generated_at = directives.get("generated_at")
        pending = pending_source_domain_proposal(
            directives, "presidential-directives-bot"
        )
        recommendation = (
            exact_head_recommendation(
                source_monitor_recommendations,
                pending["proposal"]["pull_request_number"],
                pending["proposal"]["proposal_revision"],
            )
            if pending
            else None
        )
        if pending and (not recommendation or recommendation["action_owner"] == "Elim"):
            proposal = pending["proposal"]
            recommendation_reason = (
                f"Implement exact-head recommendation {recommendation['id']}"
                if recommendation
                else "Complete watcher proposal requires directive screening and routing"
            )
            items.append(
                make_item(
                    kind="integrity",
                    identity=f"source-domain-proposal:{pending['event_id']}:{recommendation['id'] if recommendation else 'review'}",
                    title=(
                        f"Review complete Presidential Directives PR #{proposal['pull_request_number']} "
                        f"({pending['summary']['affected_record_count']} affected records)"
                    ),
                    owner="agent",
                    created_at=generated_at,
                    now=now,
                    source={
                        "input": "presidential_directives",
                        "finding_type": "source_domain_proposal",
                        "pending_proposal": pending,
                        "recommendation": recommendation,
                        "canonicalRecord": "framework/logs/sources/source-monitor-log.md",
                        "canonical_record": "framework/logs/sources/source-monitor-log.md",
                    },
                    base_priority=725,
                    reason=recommendation_reason,
                    source_revision=source_revision,
                    freshness_timestamp=generated_at,
                )
            )
        for directive in (
            []
            if pending
            else directives.get("directives", [])
            if isinstance(directives, dict)
            else []
        ):
            if not isinstance(directive, dict):
                problems.append(
                    "presidential_directives report contains a non-object directive"
                )
                continue
            disposition = str(directive.get("Bot Status") or "").casefold()
            if disposition not in {"new", "changed"}:
                continue
            directive_id = str(directive.get("Directive ID") or "").strip()
            if not directive_id:
                problems.append(
                    "presidential_directives review item lacks Directive ID"
                )
                continue
            observation = (
                str(directive.get("Content Fingerprint") or "").strip()
                or str(directive.get("Last Changed") or "").strip()
                or disposition
            )
            items.append(
                make_item(
                    kind="integrity",
                    identity=(
                        f"presidential-directive:{directive_id}:{observation}"
                    ),
                    title=(
                        f"Screen {directive_id}: "
                        + str(directive.get("Title") or "presidential directive")
                    ),
                    owner="agent",
                    created_at=generated_at,
                    now=now,
                    source={
                        "input": "presidential_directives",
                        "finding_type": "presidential_directive",
                        "directive": directive,
                    },
                    base_priority=700,
                    reason=f"Presidential directive is {disposition} and requires screening",
                    source_revision=source_revision,
                    freshness_timestamp=generated_at,
                )
            )
    intake = records["intake"].get("data") or {}
    if intake.get("collection_status") == "unavailable":
        problems.append("intake collection is unavailable")
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
    proposals = (
        [
            *(progress.get("proposals") or []),
            *(progress.get("candidates") or []),
        ]
        if isinstance(progress, dict)
        else []
    )
    for proposal in proposals:
        identifier = str(proposal.get("identifier") or "").strip()
        status = " ".join(
            str(proposal.get("workflowStatus") or proposal.get("status") or "")
            .casefold()
            .split()
        )
        development_level = " ".join(
            str(proposal.get("developmentLevel") or "").casefold().split()
        )
        next_audit = str(proposal.get("nextAudit") or "").strip()
        changed = str(proposal.get("changeAuditNeeded") or "").casefold() in {"yes", "true", "needed"}
        if not changed and "change audit" in next_audit.casefold():
            changed = True
        kind = ""
        base = 0
        formal_horizon = bool(FORMAL_HORIZON_ID_RE.fullmatch(identifier))
        candidate_level = development_level == "candidate"
        if formal_horizon or candidate_level:
            if not formal_horizon or not candidate_level:
                problems.append(
                    f"{identifier or 'unidentified progress item'} has inconsistent "
                    "formal-candidate identity or Development level"
                )
                continue
            if status != "research":
                continue
            if next_audit.casefold() in {"", "not recorded", "none", "n/a"}:
                problems.append(
                    f"{identifier} is a Research candidate without a defined Next audit"
                )
                continue
            kind, base = "candidate_research", 300
        elif changed:
            kind, base = "change_audit", 700
        elif status in {"audit needed", "audit in progress"}:
            kind, base = "issue_audit", 600
        elif status in {"research", "development"}:
            kind, base = "issue_development", 300
        if not kind or not identifier:
            continue
        canonical_record, canonical_problem = validate_queue_canonical_record(
            input_root,
            identifier,
            proposal.get("canonicalRecord"),
            formal_horizon=formal_horizon,
            allow_area_readme=(
                kind == "issue_development"
                and development_level == "admitted / undeveloped"
                and status in {"development", "research"}
            ),
        )
        retained_canonical_record = canonical_record or str(
            proposal.get("canonicalRecord") or ""
        ).strip()
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
                    "canonicalRecord": retained_canonical_record,
                    "canonical_record": retained_canonical_record,
                    "canonical_record_error": canonical_problem,
                    "workflow_status": proposal.get("workflowStatus"),
                    "development_level": proposal.get("developmentLevel"),
                    "next_audit": proposal.get("nextAudit"),
                },
                base_priority=base,
                reason=(
                    "formal Horizon candidate research route"
                    if kind == "candidate_research"
                    else f"explicit workflow route: {status}"
                ),
            )
        )
    for item in items:
        if item.get("source_revision"):
            continue
        source_input = str((item.get("source") or {}).get("input") or "").strip()
        source_hash = str((records.get(source_input) or {}).get("sha256") or "").strip()
        if source_hash:
            item["source_revision"] = source_hash

    recovery = records["recovery"].get("data") or {}
    recovery_map: dict[str, dict[str, Any]] = {}
    for retry in recovery.get("items", []) if isinstance(recovery, dict) else []:
        original = str(retry.get("work_id") or "")
        if original:
            recovery_map[original] = retry
    for item in items:
        retry = recovery_map.get(item["id"])
        if retry:
            recovery_revision = str(retry.get("source_revision") or "")
            item_revision = str(item.get("source_revision") or "")
            if (
                not recovery_revision
                or not item_revision
                or recovery_revision != item_revision
            ):
                continue
            item["recovery"] = {
                "state": retry.get("state"),
                "attempt_count": int(retry.get("attempt_count") or 0),
                "continuation": retry.get("continuation"),
                "last_error": retry.get("last_error"),
                "next_retry_at": retry.get("next_retry_at"),
                "source_revision": recovery_revision or None,
            }
            recovery_state = str(retry.get("state") or "").casefold()
            attempt_count = int(retry.get("attempt_count") or 0)
            if recovery_state in {"complete", "clean", "resolved"}:
                item["eligible_for_elim"] = False
                item["resolved_by_recovery"] = True
            elif recovery_state in {"human_required", "quarantined"} or (
                recovery_state == "retryable" and attempt_count >= 3
            ):
                item["eligible_for_elim"] = False
                item["requires_human"] = True
                item["owner"] = "human"
            else:
                next_retry_at = parse_time(retry.get("next_retry_at"))
                if next_retry_at and next_retry_at > now:
                    item["eligible_for_elim"] = False
                    item["retry_deferred_until"] = next_retry_at.isoformat(
                        timespec="seconds"
                    )
    epoch = records["review_epoch"].get("data") or {}
    chain_epoch = chain.get("review_epoch") if isinstance(chain, dict) else None
    chain_epoch = chain_epoch if isinstance(chain_epoch, dict) else {}
    due_at = parse_time(epoch.get("next_due_at")) if isinstance(epoch, dict) else None
    comprehensive_due = bool(chain_epoch.get("due")) or bool(due_at and due_at <= now)
    if comprehensive_due:
        due_reason = str(
            chain_epoch.get("due_reason")
            or epoch.get("due_reason")
            or "periodic review boundary is due"
        ).strip()
        epoch_id = str(
            epoch.get("epoch_id")
            or chain.get("chain_id")
            or epoch.get("baseline_revision")
            or "periodic"
        )
        items.append(
            make_item(
                kind="comprehensive_review",
                identity=epoch_id,
                title="Run the due comprehensive consistency review",
                owner="agent",
                created_at=(
                    epoch.get("completed_at")
                    or epoch.get("last_completed_at")
                    or epoch.get("started_at")
                    or chain.get("created_at")
                ),
                now=now,
                source={
                    "input": "review_epoch",
                    "epoch_id": epoch.get("epoch_id"),
                    "baseline_revision": epoch.get("baseline_revision"),
                    "next_due_at": epoch.get("next_due_at"),
                    "due": True,
                    "due_reason": due_reason,
                    "boundary_changes": (
                        chain_epoch.get("boundary_changes")
                        or epoch.get("boundary_changes")
                        or {}
                    ),
                    "unresolved_ids": epoch.get("unresolved_ids") or [],
                },
                base_priority=650,
                reason=due_reason,
                source_revision=records["review_epoch"].get("sha256"),
                freshness_timestamp=records["review_epoch"].get("reported_at"),
            )
        )
    ordinary_eligible_count = sum(
        bool(item.get("eligible_for_elim")) for item in items
    )
    governance_discovery_added = False
    last_governance_review_at = parse_time(
        (governance_review or {}).get("last_reviewed_at")
    )
    governance_next_due_at = (
        last_governance_review_at
        + timedelta(hours=governance_minimum_interval_hours)
        if last_governance_review_at is not None
        else None
    )
    governance_due = (
        last_governance_review_at is None
        or (
            governance_next_due_at is not None
            and now >= governance_next_due_at
        )
    )
    if (
        not problems
        and ordinary_eligible_count == 0
        and governance_due
    ):
        governance_item = make_item(
            kind="integrity",
            identity="project-governance-review-and-discovery",
            title="Project governance review and discovery",
            owner="agent",
            created_at=chain.get("created_at") or chain.get("started_at"),
            now=now,
            source={
                "input": "chain",
                "finding_type": "project_governance_review_and_discovery",
                "mode": "Project governance review and discovery",
                "ordinary_eligible_count": 0,
                "minimum_coverage_not_ceiling": True,
                "review_domains": [
                    "project structure",
                    "governing-rule integration",
                    "authority boundaries",
                    "workflow coherence",
                    "source and monitoring coverage",
                    "automation",
                    "publication",
                    "contributor readiness",
                    "technical debt",
                    "cross-surface consistency",
                ],
            },
            base_priority=200,
            reason=(
                "No ordinary eligible Elim work remains; the approved quiet-queue "
                "fallback requires a documented governance review and open discovery pass"
            ),
            source_revision=records["chain"].get("sha256"),
            freshness_timestamp=records["chain"].get("reported_at"),
            severity="maintenance",
        )
        governance_item["work_class"] = "governance_discovery"
        governance_item["exact_next_action"] = (
            "Conduct the bounded project-governance review, follow credible connected "
            "findings, and fix, report, or retain each finding according to authority."
        )
        governance_item["governance_discovery_mode"] = True
        items.append(governance_item)
        governance_discovery_added = True
    unique: dict[str, dict[str, Any]] = {}
    for item in items:
        if item["id"] in unique:
            raise ContextError(f"duplicate deterministic work identity: {item['id']}")
        unique[item["id"]] = item
    override_data = records["overrides"].get("data")
    if override_data is None:
        override_data = {}
    if not isinstance(override_data, dict):
        raise ContextError("queue override input must be a JSON object")
    if "overrides" in override_data:
        override_data = override_data.get("overrides")
        if not isinstance(override_data, dict):
            raise ContextError("queue override input overrides must be an object")
    items, applied_overrides, unmatched_overrides = apply_user_overrides(
        unique.values(),
        override_data,
    )
    items = [
        finalize_work_item_contract(
            item,
            chain_id=chain_id,
            source_commit=expected_revision,
            project_snapshot=project_snapshot,
            input_records=records,
        )
        for item in items
    ]
    ready = not problems
    selected = next(
        (item for item in items if item["eligible_for_elim"]),
        None,
    )
    return {
        "schema_version": 1,
        "item_schema_version": 1,
        "generated_at": now.isoformat(timespec="seconds"),
        "repository_revision": git_revision(reviewed_repository_root),
        "ready_for_elim": ready,
        "launch_recommended": ready and any(item["eligible_for_elim"] for item in items),
        "selected_work_item_id": selected.get("id") if selected else None,
        "problems": problems,
        "counts": {
            "total": len(items),
            "elim_eligible": sum(bool(item["eligible_for_elim"]) for item in items),
            "human": sum(bool(item["requires_human"]) for item in items),
            "safety": sum(item["safety_class"] == 0 for item in items),
            "gap_obligations": sum(
                item.get("work_class") == "gap_stewardship" for item in items
            ),
            "governance_discovery": sum(
                item.get("work_class") == "governance_discovery" for item in items
            ),
        },
        "governance_discovery": {
            "mode": "Project governance review and discovery",
            "ordinary_selection_policy": "after-ordinary-queue-clears",
            "minimum_interval_hours": governance_minimum_interval_hours,
            "selected_as_quiet_queue_fallback": governance_discovery_added,
            "ordinary_eligible_count_before_fallback": ordinary_eligible_count,
            "last_review": governance_review,
            "next_due_at": (
                governance_next_due_at.isoformat(timespec="seconds")
                if governance_next_due_at is not None
                else None
            ),
            "current_for_cadence": bool(
                not governance_due and ordinary_eligible_count == 0
            ),
            "waiting_for_ordinary_queue": ordinary_eligible_count > 0,
            "reason": (
                "No ordinary eligible Elim work remained."
                if governance_discovery_added
                else (
                    "The last committed governance review remains current for "
                    "the minimum cadence."
                    if not governance_due and ordinary_eligible_count == 0
                    else "Ordinary eligible work remains and is selected first."
                )
            ),
        },
        "fairness_policy": {
            "rule": "priority_score = base_priority + min(age_days, 365)",
            "safety_class_zero_precedes_all_normal work": True,
        },
        "user_overrides": {
            "applied": applied_overrides,
            "unmatched": unmatched_overrides,
            "request_sha256": (
                "sha256:" + sha256_bytes(canonical_json(override_data))
            ),
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
                "due": comprehensive_due,
                "due_reason": (
                    chain_epoch.get("due_reason")
                    or epoch.get("due_reason")
                ),
                "unresolved_ids": epoch.get("unresolved_ids") or [],
            }
            if isinstance(epoch, dict) and epoch
            else None
        ),
        "items": items,
    }
