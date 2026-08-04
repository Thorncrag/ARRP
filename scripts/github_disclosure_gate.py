#!/usr/bin/env python3
"""Fail-closed ARRP disclosure classification for every GitHub-bound payload."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from path_authority import (
        APPROVED_STATE_ROOT,
        PathAuthorityError,
        ProjectPathAuthority,
    )
except ModuleNotFoundError:
    from scripts.path_authority import (
        APPROVED_STATE_ROOT,
        PathAuthorityError,
        ProjectPathAuthority,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "framework/project/github/disclosure-policy.json"
DEFAULT_STATE_ROOT = APPROVED_STATE_ROOT
CATEGORY_RANK = {
    "public_by_design": 0,
    "public_operational_summary": 1,
    "restricted_operational": 2,
    "private": 3,
    "prohibited_secret": 4,
}
PUBLIC_CATEGORIES = frozenset({"public_by_design", "public_operational_summary"})
TEXT_LIMIT = 64 * 1024 * 1024
CONTROL_FILE_LIMIT = 4 * 1024 * 1024
FULL_COMMIT_OID = re.compile(r"^[0-9a-f]{40}$")
LOCAL_HEAD_REF = re.compile(r"^(?:HEAD|refs/heads/[A-Za-z0-9._/-]+)$")
REMOTE_HEAD_REF = re.compile(r"^refs/heads/[A-Za-z0-9._/-]+$")
ZERO_COMMIT_OID = "0" * 40
GITHUB_REPOSITORY = "Thorncrag/ARRP"
GITHUB_REMOTE = "origin"
GITHUB_REMOTE_URL = "https://github.com/Thorncrag/ARRP.git"
BRANCH_REF_DELETE_PATH = "github/control/branch-ref-delete"
BRANCH_REF_DELETE_PRODUCER = "interactive-reviewed-github"
COMPONENT_REGISTRY_PATH = "framework/component-registry.json"
REPORT_LIKE_PATH = re.compile(
    r"(?:^|[-_/])(report|reports|audit|review|postmortem|assessment)(?:$|[-_./])",
    re.IGNORECASE,
)
REPORT_DOCUMENT_SUFFIXES = frozenset(
    {".doc", ".docx", ".html", ".md", ".odt", ".pdf", ".rtf", ".txt"}
)

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    (
        "private-key-material",
        re.compile(rb"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
    ),
    (
        "github-token",
        re.compile(
            rb"\b(?:gh[pousr]_[A-Za-z0-9_.-]{20,}|github_pat_[A-Za-z0-9_.-]{20,})\b"
        ),
    ),
    (
        "authorization-header",
        re.compile(rb"(?i)\bauthorization\s*:\s*(?:bearer|token|basic)\s+\S+"),
    ),
    (
        "cookie-or-session",
        re.compile(
            rb"(?i)\b(?:cookie|set-cookie|session[_-]?id)\s*[:=]\s*[^\s,;]{8,}"
        ),
    ),
    (
        "credential-assignment",
        re.compile(
            rb"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)"
            rb"\s*[:=]\s*['\"]?"
            rb"(?!(?:process\.env|os\.environ|getenv|\$\{|<|/|\*))"
            rb"[A-Za-z0-9/+_.-]{8,}"
        ),
    ),
    (
        "signed-or-tokenized-url",
        re.compile(
            rb"(?i)https?://[^\s\"'<>?]+\?[^\s\"'<>]*(?:token|signature|sig|x-amz-credential|x-amz-signature|key|auth)="
            rb"[^\s\"'<>&]+"
        ),
    ),
)
class DisclosureBlocked(RuntimeError):
    """A safe failure whose string never contains matched outbound content."""

    def __init__(self, decision: Mapping[str, Any]):
        self.decision = dict(decision)
        findings = self.decision.get("findings") or []
        summary = ", ".join(
            f"{item.get('finding_id')}:{item.get('detector_class')}"
            for item in findings
            if isinstance(item, Mapping)
        )
        super().__init__(
            "GitHub disclosure blocked"
            + (f" ({summary})" if summary else "")
        )


@dataclass(frozen=True)
class OutboundArtifact:
    path: str
    producer: str
    content: bytes
    family_id: str | None = None
    source_categories: tuple[str, ...] = ()
    artifact_group: str | None = None
    removal_only: bool = False


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise DisclosureBlocked(_unavailable_decision("policy-unavailable"))
    families = value.get("artifact_families")
    if not isinstance(families, list) or not families:
        raise DisclosureBlocked(_unavailable_decision("family-registry-incomplete"))
    return value


def _read_owner_json(path: Path) -> object:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
            or metadata.st_size > CONTROL_FILE_LIMIT
        ):
            raise OSError("owner-local control file is unsafe")
        with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
            descriptor = -1
            return json.load(handle)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def load_control_pack(
    *,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Load only the active pack from the fixed owner-local authority."""

    active_policy = dict(policy) if policy is not None else load_policy()
    contract = active_policy.get("control_pack_contract")
    if not isinstance(contract, Mapping) or contract.get("required") is not True:
        raise DisclosureBlocked(_unavailable_decision("control-pack-contract-unavailable"))
    try:
        authority = ProjectPathAuthority.production()
        control_root = (
            authority.state_root / "disclosure-control-packs"
        ).resolve(strict=True)
        pointer = authority.state_path(
            "disclosure-control-packs/active.json",
            owner_only=True,
        )
        pointer_value = _read_owner_json(pointer)
        relative = str(pointer_value["control_pack"])
        source_relative = (
            Path("disclosure-control-packs") / relative
        ).as_posix()
        source = authority.state_path(
            source_relative,
            owner_only=True,
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        PathAuthorityError,
    ) as error:
        raise DisclosureBlocked(
            _unavailable_decision("active-control-pack-unavailable")
        ) from error
    try:
        source.relative_to(control_root)
    except ValueError as error:
        raise DisclosureBlocked(
            _unavailable_decision("control-pack-outside-owner-root")
        ) from error
    try:
        value = _read_owner_json(source)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise DisclosureBlocked(_unavailable_decision("control-pack-unreadable")) from error
    return validate_control_pack(
        value,
        policy=active_policy,
    )


def validate_candidate_control_pack(
    path: Path,
    *,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a candidate for activation without authorizing transmission."""

    active_policy = dict(policy) if policy is not None else load_policy()
    try:
        authority = ProjectPathAuthority.production()
        candidates = (
            authority.state_root / "disclosure-control-packs" / "candidates"
        ).resolve(strict=True)
        source = authority.requested_state_file(path, owner_only=True)
        source.relative_to(candidates)
        value = _read_owner_json(source)
    except (
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        PathAuthorityError,
    ) as error:
        raise DisclosureBlocked(
            _unavailable_decision("candidate-control-pack-unavailable")
        ) from error
    return validate_control_pack(
        value,
        policy=active_policy,
        allowed_statuses=frozenset({"candidate"}),
    )


def _owner_directory(path: Path) -> None:
    if path.exists():
        metadata = path.lstat()
        if (
            path.is_symlink()
            or not stat.S_ISDIR(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o700
        ):
            raise DisclosureBlocked(
                _unavailable_decision("control-pack-activation-boundary-unsafe")
            )
        return
    path.mkdir(mode=0o700)


def _atomic_owner_json(path: Path, value: object) -> None:
    _owner_directory(path.parent)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()


def activate_candidate_control_pack(
    candidate_id: str,
    *,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Atomically activate one validated owner-local candidate pack."""

    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", candidate_id) is None:
        raise DisclosureBlocked(
            _unavailable_decision("candidate-control-pack-id-invalid")
        )
    active_policy = dict(policy) if policy is not None else load_policy()
    authority = ProjectPathAuthority.production()
    candidate = authority.state_path(
        (
            "disclosure-control-packs/candidates/"
            f"{candidate_id}/control-pack.json"
        ),
        owner_only=True,
    )
    value = validate_candidate_control_pack(
        candidate,
        policy=active_policy,
    )
    pack_id = str(value.get("pack_id") or "")
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", pack_id) is None:
        raise DisclosureBlocked(
            _unavailable_decision("candidate-control-pack-id-invalid")
        )
    active_value = {**value, "status": "active"}
    validate_control_pack(active_value, policy=active_policy)
    active_parent = authority.state_output("disclosure-control-packs/active")
    _owner_directory(active_parent)
    active_root = active_parent / pack_id
    _owner_directory(active_root)
    destination = active_root / "control-pack.json"
    _atomic_owner_json(destination, active_value)
    pointer = authority.state_output("disclosure-control-packs/active.json")
    _atomic_owner_json(
        pointer,
        {"control_pack": f"active/{pack_id}/control-pack.json"},
    )
    loaded = load_control_pack(policy=active_policy)
    if loaded.get("pack_id") != pack_id:
        raise DisclosureBlocked(
            _unavailable_decision("active-control-pack-readback-failed")
        )
    return {
        "pack_id": pack_id,
        "control_version": str(loaded.get("control_version") or ""),
        "status": "active",
    }


def validate_control_pack(
    value: object,
    *,
    policy: Mapping[str, Any],
    allowed_statuses: frozenset[str] = frozenset({"active"}),
) -> dict[str, Any]:
    """Validate a supplied pack; callers cannot self-assert compatibility."""

    contract = policy.get("control_pack_contract")
    if not isinstance(contract, Mapping):
        raise DisclosureBlocked(_unavailable_decision("control-pack-contract-unavailable"))
    if not isinstance(value, dict):
        raise DisclosureBlocked(_unavailable_decision("control-pack-incompatible"))
    valid_status = value.get("status") in allowed_statuses
    compatible = contract.get("compatible_control_versions") or []
    detectors = value.get("restricted_detectors")
    path_patterns = value.get("restricted_path_patterns")
    if (
        value.get("schema_version") != contract.get("schema_version")
        or value.get("policy_id") != policy.get("policy_id")
        or value.get("complete") is not True
        or not valid_status
        or value.get("control_version") not in compatible
        or not isinstance(detectors, list)
        or not detectors
        or not isinstance(path_patterns, list)
    ):
        raise DisclosureBlocked(_unavailable_decision("control-pack-incompatible"))
    for detector in detectors:
        if (
            not isinstance(detector, Mapping)
            or not str(detector.get("id") or "").strip()
            or not str(detector.get("pattern") or "").strip()
        ):
            raise DisclosureBlocked(_unavailable_decision("control-pack-incomplete"))
        try:
            re.compile(str(detector["pattern"]))
        except re.error as error:
            raise DisclosureBlocked(
                _unavailable_decision("control-pack-detector-invalid")
            ) from error
    return dict(value)


def _finding(path: str, family: str | None, detector: str, category: str) -> dict[str, str]:
    identity = "\0".join((path, family or "unclassified", detector, category))
    return {
        "finding_id": (
            "DISC-"
            + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12].upper()
        ),
        "path": path,
        "artifact_family": family or "unclassified",
        "detector_class": detector,
        "category": category,
        "next_action": (
            "Preserve the local artifact and obtain an exact governed "
            "classification or produce a separately reviewed sanitized derivative."
        ),
    }


def _unavailable_decision(detector: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "allowed": False,
        "complete": False,
        "category": "restricted_operational",
        "findings": [_finding("(bundle)", None, detector, "restricted_operational")],
    }


def _matches(path: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _resolve_family(
    policy: Mapping[str, Any],
    *,
    path: str,
    producer: str,
    requested_family: str | None,
) -> Mapping[str, Any]:
    matches: list[Mapping[str, Any]] = []
    for raw in policy.get("artifact_families") or []:
        if not isinstance(raw, Mapping):
            continue
        if requested_family is not None and raw.get("id") != requested_family:
            continue
        if producer not in (raw.get("producers") or []):
            continue
        if not _matches(path, raw.get("paths") or []):
            continue
        if _matches(path, raw.get("exclude_paths") or []):
            continue
        matches.append(raw)
    if len(matches) != 1:
        detector = "ambiguous-artifact-family" if len(matches) > 1 else "unknown-artifact-family"
        raise DisclosureBlocked(
            {
                "schema_version": 1,
                "allowed": False,
                "complete": False,
                "category": "restricted_operational",
                "findings": [_finding(path, requested_family, detector, "restricted_operational")],
            }
        )
    return matches[0]


def _exception_override(
    policy: Mapping[str, Any],
    *,
    path: str,
    family_id: str,
    revision: str,
) -> str | None:
    matches = [
        item
        for item in policy.get("exceptional_overrides") or []
        if isinstance(item, Mapping)
        and item.get("path") == path
        and item.get("artifact_family") == family_id
        and item.get("reviewed_revision") == revision
    ]
    if len(matches) > 1:
        raise DisclosureBlocked(
            {
                "schema_version": 1,
                "allowed": False,
                "complete": False,
                "category": "restricted_operational",
                "findings": [_finding(path, family_id, "ambiguous-exceptional-override", "restricted_operational")],
            }
        )
    if not matches:
        return None
    category = matches[0].get("category")
    if category not in CATEGORY_RANK:
        raise DisclosureBlocked(_unavailable_decision("invalid-exceptional-override"))
    return str(category)


def _content_findings(
    path: str,
    family_id: str,
    content: bytes,
    *,
    control_pack: Mapping[str, Any] | None = None,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if control_pack is not None and _matches(
        path, control_pack.get("restricted_path_patterns") or []
    ):
        findings.append(
            _finding(
                path,
                family_id,
                "owner-local-artifact-path",
                "restricted_operational",
            )
        )
    if len(content) > TEXT_LIMIT:
        findings.append(_finding(path, family_id, "oversized-content-uninspected", "restricted_operational"))
        return findings
    for detector, pattern in SECRET_PATTERNS:
        if pattern.search(content):
            findings.append(_finding(path, family_id, detector, "prohibited_secret"))
    if control_pack is not None and b"\0" not in content:
        text = content.decode("utf-8", "replace")
        for raw in control_pack.get("restricted_detectors") or []:
            detector = str(raw["id"])
            pattern = re.compile(str(raw["pattern"]))
            if pattern.search(text):
                findings.append(_finding(path, family_id, detector, "restricted_operational"))
    return findings


def prohibited_secret_findings(
    path: str,
    content: bytes,
    *,
    family_id: str = "private-local-state",
) -> list[dict[str, str]]:
    """Return safe metadata for secret findings without classifying destination use.

    Private local projections are not eligible for GitHub disclosure, but the
    absolute secret rule still applies before they are persisted.  This helper
    deliberately exposes only the already-redacted finding records.
    """

    return [
        finding
        for finding in _content_findings(path, family_id, content)
        if finding.get("category") == "prohibited_secret"
    ]


def evaluate_outbound_bundle(
    artifacts: Iterable[OutboundArtifact],
    *,
    operation: str,
    source_revision: str,
    policy: Mapping[str, Any] | None = None,
    defense_in_depth_only: bool = False,
    complete: bool = True,
) -> dict[str, Any]:
    """Return one exact decision.

    ``defense_in_depth_only`` is reserved for checks running after content has
    already reached GitHub. It never supplies an authoritative outbound
    authorization and deliberately cannot substitute for the owner-local
    control pack required before transmission.
    """

    active_policy = dict(policy) if policy is not None else load_policy()
    active_control_pack: Mapping[str, Any] | None = None
    if not defense_in_depth_only:
        active_control_pack = load_control_pack(policy=active_policy)
    rows = list(artifacts)
    findings: list[dict[str, str]] = []
    classified: list[dict[str, Any]] = []
    group_categories: dict[str, list[str]] = {}
    if not complete:
        findings.append(_finding("(bundle)", None, "incomplete-outbound-evidence", "restricted_operational"))
    if not rows:
        findings.append(_finding("(bundle)", None, "empty-outbound-bundle", "restricted_operational"))
    for artifact in rows:
        family = _resolve_family(
            active_policy,
            path=artifact.path,
            producer=artifact.producer,
            requested_family=artifact.family_id,
        )
        family_id = str(family["id"])
        category = str(family["category"])
        override = _exception_override(
            active_policy,
            path=artifact.path,
            family_id=family_id,
            revision=source_revision,
        )
        if override is not None:
            category = override
        source_categories = [
            item for item in artifact.source_categories if item in CATEGORY_RANK
        ]
        if len(source_categories) != len(artifact.source_categories):
            findings.append(_finding(artifact.path, family_id, "unknown-source-classification", "restricted_operational"))
        inherited = max([category, *source_categories], key=CATEGORY_RANK.__getitem__)
        if artifact.removal_only:
            if artifact.content:
                findings.append(
                    _finding(
                        artifact.path,
                        family_id,
                        "removal-record-contained-content",
                        "restricted_operational",
                    )
                )
            classified.append(
                {
                    "path": artifact.path,
                    "artifact_family": family_id,
                    "artifact_group": artifact.artifact_group or artifact.path,
                    "category": inherited,
                    "removal_only": True,
                }
            )
            continue
        content_findings = _content_findings(
            artifact.path,
            family_id,
            artifact.content,
            control_pack=active_control_pack,
        )
        findings.extend(content_findings)
        detected_categories = [item["category"] for item in content_findings]
        effective = max([inherited, *detected_categories], key=CATEGORY_RANK.__getitem__)
        group = artifact.artifact_group or artifact.path
        if artifact.artifact_group is not None and not _matches(
            artifact.artifact_group,
            active_policy.get("artifact_group_patterns") or [],
        ):
            findings.append(
                _finding(
                    artifact.path,
                    family_id,
                    "unregistered-artifact-group",
                    "restricted_operational",
                )
            )
        group_categories.setdefault(group, []).append(effective)
        classified.append(
            {
                "path": artifact.path,
                "artifact_family": family_id,
                "artifact_group": group,
                "category": effective,
                "removal_only": False,
            }
        )
    strictest_by_group = {
        group: max(categories, key=CATEGORY_RANK.__getitem__)
        for group, categories in group_categories.items()
    }
    for row in classified:
        if row.get("removal_only") is True:
            continue
        group_category = strictest_by_group[row["artifact_group"]]
        if CATEGORY_RANK[group_category] > CATEGORY_RANK[row["category"]]:
            row["category"] = group_category
            if group_category not in PUBLIC_CATEGORIES:
                findings.append(
                    _finding(
                        row["path"],
                        row["artifact_family"],
                        "artifact-family-inheritance",
                        group_category,
                    )
                )
    categories = [
        row["category"]
        for row in classified
        if row.get("removal_only") is not True
    ]
    strictest = (
        max(categories, key=CATEGORY_RANK.__getitem__)
        if categories
        else "public_operational_summary"
    )
    allowed = complete and bool(rows) and not findings and all(
        category in PUBLIC_CATEGORIES for category in categories
    )
    if not allowed and not findings:
        for row in classified:
            if (
                row.get("removal_only") is not True
                and row["category"] not in PUBLIC_CATEGORIES
            ):
                findings.append(
                    _finding(
                        row["path"],
                        row["artifact_family"],
                        "nonpublic-artifact-family",
                        row["category"],
                    )
                )
    return {
        "schema_version": 1,
        "policy_id": active_policy.get("policy_id"),
        "control_pack_id": (
            active_control_pack.get("pack_id")
            if active_control_pack is not None
            else None
        ),
        "control_version": (
            active_control_pack.get("control_version")
            if active_control_pack is not None
            else None
        ),
        "authoritative": not defense_in_depth_only,
        "mode": (
            "post_transmission_defense_in_depth"
            if defense_in_depth_only
            else "pre_transmission_authorization"
        ),
        "operation": operation,
        "source_revision": source_revision,
        "allowed": allowed,
        "complete": complete,
        "category": strictest,
        "artifacts": classified,
        "findings": findings,
    }


def require_outbound_bundle(*args: Any, **kwargs: Any) -> dict[str, Any]:
    decision = evaluate_outbound_bundle(*args, **kwargs)
    if not decision["allowed"] or decision.get("authoritative") is not True:
        raise DisclosureBlocked(decision)
    return decision


def require_defense_in_depth_bundle(
    artifacts: Iterable[OutboundArtifact],
    *,
    operation: str,
    source_revision: str,
    policy: Mapping[str, Any] | None = None,
    complete: bool = True,
) -> dict[str, Any]:
    """Run a non-authoritative public-core recheck after GitHub transmission."""

    decision = evaluate_outbound_bundle(
        artifacts,
        operation=operation,
        source_revision=source_revision,
        policy=policy,
        defense_in_depth_only=True,
        complete=complete,
    )
    if not decision["allowed"]:
        raise DisclosureBlocked(decision)
    return decision


def artifact_from_text(
    path: str,
    producer: str,
    content: str,
    *,
    family_id: str | None = None,
    source_categories: Sequence[str] = (),
    artifact_group: str | None = None,
) -> OutboundArtifact:
    return OutboundArtifact(
        path=path,
        producer=producer,
        content=content.encode("utf-8"),
        family_id=family_id,
        source_categories=tuple(source_categories),
        artifact_group=artifact_group,
    )


def _git_output(repository: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", os.fspath(repository), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=30,
    )
    if result.returncode:
        raise DisclosureBlocked(
            _unavailable_decision("git-revision-binding-unavailable")
        )
    return result.stdout


def _validated_ref(value: str, *, remote: bool = False) -> str:
    pattern = REMOTE_HEAD_REF if remote else LOCAL_HEAD_REF
    if (
        not pattern.fullmatch(value)
        or ".." in value
        or "//" in value
        or value.endswith(("/", ".lock"))
        or "@{" in value
    ):
        raise DisclosureBlocked(_unavailable_decision("git-ref-invalid"))
    return value


def _canonical_commit(repository: Path, revision: str) -> str:
    if not FULL_COMMIT_OID.fullmatch(revision):
        raise DisclosureBlocked(
            _unavailable_decision("git-full-commit-required")
        )
    resolved = _git_output(
        repository,
        "rev-parse",
        "--verify",
        "--end-of-options",
        f"{revision}^{{commit}}",
    ).decode("ascii").strip()
    if resolved != revision:
        raise DisclosureBlocked(
            _unavailable_decision("git-revision-mismatch")
        )
    return resolved


def _blob(repository: Path, revision: str, path: str) -> bytes:
    entry = _git_output(
        repository,
        "ls-tree",
        "-z",
        revision,
        "--",
        path,
    )
    if not entry.endswith(b"\0") or entry.count(b"\0") != 1:
        raise DisclosureBlocked(
            _unavailable_decision("git-manifest-incomplete")
        )
    metadata, separator, encoded_path = entry[:-1].partition(b"\t")
    fields = metadata.split(b" ")
    if (
        not separator
        or len(fields) != 3
        or fields[1] != b"blob"
        or encoded_path.decode("utf-8") != path
    ):
        raise DisclosureBlocked(
            _unavailable_decision("git-manifest-incomplete")
        )
    return _git_output(repository, "cat-file", "blob", fields[2].decode("ascii"))


def _require_public_report_registration(
    repository: Path,
    revision: str,
    artifacts: Sequence[OutboundArtifact],
) -> None:
    report_paths = [
        artifact.path
        for artifact in artifacts
        if (
            not artifact.removal_only
            and Path(artifact.path).suffix.lower() in REPORT_DOCUMENT_SUFFIXES
            and REPORT_LIKE_PATH.search(artifact.path)
        )
    ]
    if not report_paths:
        return
    try:
        registry = json.loads(
            _blob(repository, revision, COMPONENT_REGISTRY_PATH).decode("utf-8")
        )
        entries = registry["components"]["entries"]
    except (DisclosureBlocked, KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DisclosureBlocked(
            _unavailable_decision("public-report-registry-unavailable")
        ) from error
    if (
        registry.get("schema_version") != 4
        or registry.get("registry_revision") != 7
        or not isinstance(entries, Mapping)
    ):
        raise DisclosureBlocked(
            _unavailable_decision("public-report-registry-revision-invalid")
        )
    for path in report_paths:
        if not path.startswith("framework/reports/"):
            raise DisclosureBlocked(
                {
                    "schema_version": 1,
                    "allowed": False,
                    "complete": False,
                    "category": "restricted_operational",
                    "findings": [_finding(path, None, "report-outside-public-project-scope", "restricted_operational")],
                }
            )
        matches = [
            component
            for component in entries.values()
            if isinstance(component, Mapping)
            and component.get("canonical_source") == path
            and component.get("classification")
            == {"component_class": "document", "component_type": "report"}
            and component.get("information_handling")
            == {
                "information_classification": "public_by_design",
                "disclosure_rule": "public-project-report",
            }
        ]
        if len(matches) != 1:
            raise DisclosureBlocked(
                {
                    "schema_version": 1,
                    "allowed": False,
                    "complete": False,
                    "category": "restricted_operational",
                    "findings": [_finding(path, "public-project-report", "unregistered-public-project-report", "restricted_operational")],
                }
            )


def authorize_git_push(
    repository: Path,
    *,
    base_revision: str,
    source_revision: str,
    head_ref: str,
    target_ref: str,
    producer: str,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Authorize one complete committed Git range and exact push refspec."""

    repository = repository.resolve(strict=True)
    base = _canonical_commit(repository, base_revision)
    head = _canonical_commit(repository, source_revision)
    local_ref = _validated_ref(head_ref)
    remote_ref = _validated_ref(target_ref, remote=True)
    resolved_ref = _git_output(
        repository,
        "rev-parse",
        "--verify",
        "--end-of-options",
        f"{local_ref}^{{commit}}",
    ).decode("ascii").strip()
    if resolved_ref != head:
        raise DisclosureBlocked(
            _unavailable_decision("git-revision-mismatch")
        )
    ancestor = subprocess.run(
        ["git", "-C", os.fspath(repository), "merge-base", "--is-ancestor", base, head],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=30,
    )
    if ancestor.returncode != 0:
        raise DisclosureBlocked(
            _unavailable_decision("git-range-invalid")
        )
    raw = _git_output(
        repository,
        "diff",
        "--name-status",
        "-z",
        "--no-renames",
        base,
        head,
        "--",
    )
    tokens = raw.split(b"\0")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    if len(tokens) % 2:
        raise DisclosureBlocked(
            _unavailable_decision("git-manifest-incomplete")
        )
    artifacts: list[OutboundArtifact] = []
    manifest: list[dict[str, Any]] = []
    for offset in range(0, len(tokens), 2):
        status_value = tokens[offset].decode("ascii")
        path = tokens[offset + 1].decode("utf-8")
        status_code = status_value[:1]
        if status_code not in {"A", "C", "D", "M", "T", "U", "X", "B"}:
            raise DisclosureBlocked(
                _unavailable_decision("git-manifest-incomplete")
            )
        removal_only = status_code == "D"
        content = b"" if removal_only else _blob(repository, head, path)
        prior = b"" if status_code == "A" else _blob(repository, base, path)
        manifest.append(
            {
                "path": path,
                "status": status_code,
                "prior_sha256": (
                    "sha256:" + hashlib.sha256(prior).hexdigest()
                    if status_code != "A"
                    else None
                ),
                "content_sha256": (
                    "sha256:" + hashlib.sha256(content).hexdigest()
                    if not removal_only
                    else None
                ),
            }
        )
        artifacts.append(
            OutboundArtifact(
                path=path,
                producer=producer,
                content=content,
                removal_only=removal_only,
            )
        )
    manifest_digest = "sha256:" + hashlib.sha256(
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    _require_public_report_registration(repository, head, artifacts)
    decision = require_outbound_bundle(
        artifacts,
        operation="git_push",
        source_revision=head,
        policy=policy,
        complete=True,
    )
    decision.update(
        {
            "base_revision": base,
            "manifest_sha256": manifest_digest,
            "authorized_refspec": f"{head}:{remote_ref}",
        }
    )
    return decision


def _validate_branch_ref_delete_authority(
    authority: ProjectPathAuthority,
    *,
    policy: Mapping[str, Any] | None,
) -> Path:
    if authority.mode == "production_canonical":
        try:
            production = ProjectPathAuthority.production()
        except PathAuthorityError as error:
            raise DisclosureBlocked(
                _unavailable_decision("git-ref-delete-authority-invalid")
            ) from error
        if (
            authority.repository_root != production.repository_root
            or authority.state_root != production.state_root
            or policy is not None
        ):
            raise DisclosureBlocked(
                _unavailable_decision("git-ref-delete-authority-invalid")
            )
        repository = production.repository_root
        for remote_argument in (
            ("remote", "get-url", GITHUB_REMOTE),
            ("remote", "get-url", "--push", GITHUB_REMOTE),
        ):
            remote_urls = _git_output(
                repository,
                *remote_argument,
            ).decode("utf-8").splitlines()
            if remote_urls != [GITHUB_REMOTE_URL]:
                raise DisclosureBlocked(
                    _unavailable_decision("git-remote-identity-invalid")
                )
        return repository
    if (
        authority.mode == "fixture"
        and authority.fixture_root is not None
        and policy is not None
    ):
        return authority.repository_root
    raise DisclosureBlocked(
        _unavailable_decision("git-ref-delete-authority-invalid")
    )


def _remote_ref_oid(repository: Path, target_ref: str) -> str | None:
    raw = _git_output(
        repository,
        "ls-remote",
        "--refs",
        GITHUB_REMOTE,
        target_ref,
    )
    if not raw:
        return None
    lines = raw.decode("ascii").splitlines()
    if len(lines) != 1:
        raise DisclosureBlocked(
            _unavailable_decision("git-remote-ref-ambiguous")
        )
    oid, separator, observed_ref = lines[0].partition("\t")
    if (
        not separator
        or observed_ref != target_ref
        or FULL_COMMIT_OID.fullmatch(oid) is None
    ):
        raise DisclosureBlocked(
            _unavailable_decision("git-remote-ref-invalid")
        )
    return oid


def _branch_ref_delete_payload(
    *,
    target_ref: str,
    expected_old_oid: str,
) -> tuple[dict[str, str | int], bytes]:
    payload: dict[str, str | int] = {
        "schema_version": 1,
        "operation": "git_branch_ref_delete",
        "repository": GITHUB_REPOSITORY,
        "remote": GITHUB_REMOTE,
        "target_ref": target_ref,
        "expected_old_oid": expected_old_oid,
        "new_oid": ZERO_COMMIT_OID,
    }
    content = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return payload, content


def authorize_git_branch_ref_delete(
    authority: ProjectPathAuthority,
    *,
    source_revision: str,
    target_ref: str,
    producer: str,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Authorize deletion of one exact remote branch at one exact old OID."""

    repository = _validate_branch_ref_delete_authority(
        authority,
        policy=policy,
    )
    expected_old_oid = _canonical_commit(repository, source_revision)
    remote_ref = _validated_ref(target_ref, remote=True)
    if remote_ref == "refs/heads/main":
        raise DisclosureBlocked(
            _unavailable_decision("git-default-branch-delete-forbidden")
        )
    if producer != BRANCH_REF_DELETE_PRODUCER:
        raise DisclosureBlocked(
            _unavailable_decision("git-ref-delete-producer-invalid")
        )
    observed_oid = _remote_ref_oid(repository, remote_ref)
    if observed_oid is None:
        raise DisclosureBlocked(
            _unavailable_decision("git-remote-ref-missing")
        )
    if observed_oid != expected_old_oid:
        raise DisclosureBlocked(
            _unavailable_decision("git-remote-ref-moved")
        )
    payload, content = _branch_ref_delete_payload(
        target_ref=remote_ref,
        expected_old_oid=expected_old_oid,
    )
    decision = require_outbound_bundle(
        [
            OutboundArtifact(
                path=BRANCH_REF_DELETE_PATH,
                producer=producer,
                content=content,
            )
        ],
        operation="git_branch_ref_delete",
        source_revision=expected_old_oid,
        policy=policy,
        complete=True,
    )
    decision.update(
        {
            "repository": GITHUB_REPOSITORY,
            "authority_mode": authority.mode,
            "authorized_remote": GITHUB_REMOTE,
            "target_ref": remote_ref,
            "expected_old_oid": expected_old_oid,
            "new_oid": ZERO_COMMIT_OID,
            "payload_sha256": (
                "sha256:" + hashlib.sha256(content).hexdigest()
            ),
            "authorized_refspec": f":{remote_ref}",
            "authorized_lease": f"{remote_ref}:{expected_old_oid}",
        }
    )
    return decision


def execute_authorized_git_branch_ref_delete(
    authority: ProjectPathAuthority,
    decision: Mapping[str, Any],
    *,
    policy: Mapping[str, Any] | None = None,
) -> None:
    """Execute and read back one exact lease-protected deletion decision."""

    repository = _validate_branch_ref_delete_authority(
        authority,
        policy=policy,
    )
    target_ref = _validated_ref(str(decision.get("target_ref") or ""), remote=True)
    expected_old_oid = str(decision.get("expected_old_oid") or "")
    if FULL_COMMIT_OID.fullmatch(expected_old_oid) is None:
        raise DisclosureBlocked(
            _unavailable_decision("git-full-commit-required")
        )
    _, content = _branch_ref_delete_payload(
        target_ref=target_ref,
        expected_old_oid=expected_old_oid,
    )
    current_decision = authorize_git_branch_ref_delete(
        authority,
        source_revision=expected_old_oid,
        target_ref=target_ref,
        producer=BRANCH_REF_DELETE_PRODUCER,
        policy=policy,
    )
    expected_payload_sha256 = "sha256:" + hashlib.sha256(content).hexdigest()
    expected_refspec = f":{target_ref}"
    expected_lease = f"{target_ref}:{expected_old_oid}"
    if (
        decision.get("allowed") is not True
        or decision.get("authoritative") is not True
        or decision.get("operation") != "git_branch_ref_delete"
        or decision.get("repository") != GITHUB_REPOSITORY
        or decision.get("authority_mode") != authority.mode
        or decision.get("authorized_remote") != GITHUB_REMOTE
        or decision.get("source_revision") != expected_old_oid
        or decision.get("new_oid") != ZERO_COMMIT_OID
        or decision.get("payload_sha256") != expected_payload_sha256
        or decision.get("authorized_refspec") != expected_refspec
        or decision.get("authorized_lease") != expected_lease
        or target_ref == "refs/heads/main"
        or dict(decision) != current_decision
    ):
        raise DisclosureBlocked(
            _unavailable_decision("git-ref-delete-decision-invalid")
        )
    if _remote_ref_oid(repository, target_ref) != expected_old_oid:
        raise DisclosureBlocked(
            _unavailable_decision("git-remote-ref-moved")
        )
    result = subprocess.run(
        [
            "git",
            "-C",
            os.fspath(repository),
            "push",
            GITHUB_REMOTE,
            f"--force-with-lease={expected_lease}",
            expected_refspec,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=30,
    )
    if result.returncode:
        raise DisclosureBlocked(
            _unavailable_decision("git-ref-delete-lease-failed")
        )
    if _remote_ref_oid(repository, target_ref) is not None:
        raise DisclosureBlocked(
            _unavailable_decision("git-ref-delete-readback-failed")
        )


def _cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--base-revision")
    parser.add_argument("--head-ref")
    parser.add_argument("--target-ref")
    parser.add_argument("--producer", required=True)
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    authority = ProjectPathAuthority.production()
    if args.operation == "git_push":
        if (
            args.paths
            or not args.base_revision
            or not args.head_ref
            or not args.target_ref
        ):
            parser.error(
                "git_push requires --base-revision, --head-ref, and "
                "--target-ref and derives the complete artifact range"
            )
        decision = authorize_git_push(
            authority.repository_root,
            base_revision=args.base_revision,
            source_revision=args.source_revision,
            head_ref=args.head_ref,
            target_ref=args.target_ref,
            producer=args.producer,
        )
        print(json.dumps(decision, sort_keys=True, indent=2))
        return 0
    if args.operation == "git_branch_ref_delete":
        if (
            args.paths
            or args.base_revision
            or args.head_ref
            or not args.target_ref
        ):
            parser.error(
                "git_branch_ref_delete requires --target-ref and "
                "--source-revision only"
            )
        decision = authorize_git_branch_ref_delete(
            authority,
            source_revision=args.source_revision,
            target_ref=args.target_ref,
            producer=args.producer,
        )
        print(json.dumps(decision, sort_keys=True, indent=2))
        return 0
    if not args.paths or any(
        value is not None
        for value in (args.base_revision, args.head_ref, args.target_ref)
    ):
        parser.error(
            "non-git operations require paths and do not accept Git range arguments"
        )
    artifacts = []
    for requested in args.paths:
        source = authority.repository_path(requested)
        artifacts.append(
            OutboundArtifact(
                path=source.relative_to(authority.repository_root).as_posix(),
                producer=args.producer,
                content=source.read_bytes(),
            )
        )
    policy = load_policy()
    decision = evaluate_outbound_bundle(
        artifacts,
        operation=args.operation,
        source_revision=args.source_revision,
        policy=policy,
    )
    print(json.dumps(decision, sort_keys=True, indent=2))
    return 0 if decision["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(_cli())
