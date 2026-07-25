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
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ModuleNotFoundError:  # The repository .venv includes PyYAML; keep read-only tools portable.
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
ISSUE_ID_RE = re.compile(r"\b(?:[A-Z][A-Z0-9]*-\d{3}|HOR-\d{3})\b")
FORMAL_HORIZON_ID_RE = re.compile(r"^HOR-\d{3}$")
HORIZON_ISSUE_URL_RE = re.compile(
    r"^https://github\.com/Thorncrag/ARRP/issues/\d+$"
)
WORK_ITEM_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
WORK_KIND_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
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


def find_issue_page(root: Path, issue_id: str) -> Path:
    matches = sorted((root / "areas").glob(f"*/issues/{issue_id}.md"))
    matches = [path for path in matches if not path.name.endswith(".audit.md")]
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
    if not re.fullmatch(r"[A-Z][A-Z0-9]*-\d{3}", issue_id):
        raise ContextError(f"invalid canonical issue identifier: {issue_id!r}")
    matches = sorted((root / "areas").glob(f"*/issues/{issue_id}.md"))
    matches = [path for path in matches if not path.name.endswith(".audit.md")]
    if len(matches) == 1:
        return "issue_page", matches[0]
    if len(matches) > 1:
        raise ContextError(
            f"expected exactly one canonical page for {issue_id}; found {len(matches)}"
        )
    if allow_area_readme and re.fullmatch(r"[A-Z][A-Z0-9]*-\d{3}", issue_id):
        area = issue_id.split("-", 1)[0]
        area_readme = root / "areas" / area / "README.md"
        if area_readme.is_file():
            return "area_readme", area_readme.resolve()
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
            record_path = within_root(root, canonical_record)
            exact_relative = record_path.relative_to(root.resolve()).as_posix()
            if exact_relative != canonical_record:
                raise ContextError(
                    "--canonical-record must be an exact normalized "
                    "repository-relative path"
                )
            if not record_path.is_file():
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
    manifest_path: Path,
    profile_name: str,
    *,
    root: Path = ROOT,
    issue_id: str | None = None,
    review_epoch_path: Path | None = None,
    max_total_bytes: int | None = None,
    capabilities: Iterable[str] = (),
    work_item_id: str | None = None,
    work_kind: str | None = None,
    canonical_record: str | None = None,
) -> dict[str, Any]:
    selection = context_packet_selection(
        root=root,
        work_item_id=work_item_id,
        work_kind=work_kind,
        canonical_record=canonical_record,
    )
    manifest_path = contained_path(manifest_path, root)
    manifest = load_route_manifest(manifest_path, root=root, verify_hashes=True)
    profile = manifest["profiles"].get(profile_name)
    if profile is None:
        raise ContextError(f"unknown context profile: {profile_name}")
    manifest_sha = sha256_path(manifest_path, root)
    requested_capabilities = [str(item) for item in capabilities]
    module_ids = _profile_document_ids(
        manifest,
        profile,
        extra_capabilities=requested_capabilities,
    )
    _validate_section_module_conflicts(profile_name, profile, module_ids)
    modules: list[dict[str, Any]] = []
    sections: list[dict[str, Any]] = []
    total = 0
    for module_id in module_ids:
        document = manifest["documents"][module_id]
        path = within_root(root, document["path"])
        content = path.read_text(encoding="utf-8")
        size = len(content.encode("utf-8"))
        actual_sha = sha256_path(path, root)
        total += size
        modules.append(
            {
                "document": module_id,
                "path": document["path"],
                "sha256": actual_sha,
                "hash_policy": str(document.get("hash_policy") or "pinned"),
                "bytes": size,
                "content": content,
            }
        )
    for route in profile.get("sections") or []:
        document = manifest["documents"][route["document"]]
        path = within_root(root, document["path"])
        text = path.read_text(encoding="utf-8")
        content, start, end = extract_exact_heading(text, route["heading"])
        size = len(content.encode("utf-8"))
        actual_sha = sha256_path(path, root)
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
        if record_kind == "issue_page":
            metadata = front_matter(canonical_path)
            audit_value = str(metadata.get("audit_history") or f"{issue_id}.audit.md")
            audit_path = (canonical_path.parent / audit_value).resolve()
            if root.resolve() not in audit_path.parents:
                raise ContextError(f"audit path escapes repository: {audit_value}")
            latest_audit = None
            if audit_path.is_file():
                latest_audit = latest_markdown_entry(
                    audit_path, "## Audit History", entry_level=3, order="newest-first"
                )
            vehicles = resolve_linked_vehicles(root, canonical_path, metadata)
            issue_page = {
                **file_provenance(canonical_path, root),
                "front_matter": metadata,
                "content": canonical_path.read_text(encoding="utf-8"),
            }
            latest_audit_record = (
                {
                    **latest_audit,
                    "path": audit_path.relative_to(root.resolve()).as_posix(),
                    "sha256": sha256_path(audit_path, root),
                }
                if latest_audit
                else None
            )
        else:
            generic_record = {
                **file_provenance(canonical_path, root),
                "content": canonical_path.read_text(encoding="utf-8"),
            }
        dossier = {
            "issue_id": issue_id,
            "canonical_record_kind": record_kind,
            "canonical_record_path": Path(
                os.path.realpath(os.fspath(canonical_path))
            )
            .relative_to(Path(os.path.realpath(os.fspath(root))))
            .as_posix(),
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
    if selection is not None:
        total += len(canonical_json(selection))
    profile_limit = int(profile["max_bytes"])
    effective_limit = min(profile_limit, max_total_bytes) if max_total_bytes else profile_limit
    if total > effective_limit:
        raise ContextError(f"context packet exceeds max bytes ({total} > {effective_limit})")
    return {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repository_revision": git_revision(root),
        "profile": profile_name,
        "selection": selection,
        "manifest": {
            "path": manifest_path.relative_to(
                Path(os.path.realpath(os.fspath(root)))
            ).as_posix(),
            "sha256": manifest_sha,
        },
        "limits": {"max_bytes": effective_limit, "actual_bytes": total},
        "capabilities": [
            *(str(item) for item in profile.get("capabilities") or []),
            *requested_capabilities,
        ],
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
        path = within_root(root, text)
    except ContextError as exc:
        return None, f"{identifier} has an unsafe canonicalRecord: {exc}"
    if not path.is_file():
        return None, f"{identifier} canonicalRecord is missing: {text}"
    normalized = path.relative_to(root.resolve()).as_posix()
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
        if normalized != "framework/logs/HORIZON_SCAN_LOG.md":
            return (
                None,
                f"{identifier} formal-candidate canonicalRecord is not its GitHub Issue "
                f"or framework/logs/HORIZON_SCAN_LOG.md: {normalized}",
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
        if data.get("collection_status") == "unavailable":
            problems.append(f"{name} collection is unavailable")
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
