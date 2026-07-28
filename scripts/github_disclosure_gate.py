#!/usr/bin/env python3
"""Fail-closed ARRP disclosure classification for every GitHub-bound payload."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "framework/project/github/disclosure-policy.json"
DEFAULT_STATE_ROOT = Path.home() / "Library/Application Support/ARRP"
CATEGORY_RANK = {
    "public_by_design": 0,
    "public_operational_summary": 1,
    "restricted_operational": 2,
    "private": 3,
    "prohibited_secret": 4,
}
PUBLIC_CATEGORIES = frozenset({"public_by_design", "public_operational_summary"})
TEXT_LIMIT = 64 * 1024 * 1024

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


def load_control_pack(
    path: Path | None = None,
    *,
    policy: Mapping[str, Any] | None = None,
    allow_candidate: bool = False,
) -> dict[str, Any]:
    """Load the required owner-local restricted controls without exposing them."""

    active_policy = dict(policy) if policy is not None else load_policy()
    contract = active_policy.get("control_pack_contract")
    if not isinstance(contract, Mapping) or contract.get("required") is not True:
        raise DisclosureBlocked(_unavailable_decision("control-pack-contract-unavailable"))
    state_root = Path(
        os.environ.get("ARRP_STATE_ROOT", str(DEFAULT_STATE_ROOT))
    ).expanduser().resolve()
    control_root = (state_root / "disclosure-control-packs").resolve()
    if path is None:
        pointer = control_root / "active.json"
        try:
            pointer_value = json.loads(pointer.read_text(encoding="utf-8"))
            relative = str(pointer_value["control_pack"])
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise DisclosureBlocked(
                _unavailable_decision("active-control-pack-unavailable")
            ) from error
        source = (control_root / relative).resolve()
    else:
        source = path.expanduser().resolve()
    if source != control_root and control_root not in source.parents:
        raise DisclosureBlocked(_unavailable_decision("control-pack-outside-owner-root"))
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise DisclosureBlocked(_unavailable_decision("control-pack-unreadable")) from error
    return validate_control_pack(
        value,
        policy=active_policy,
        allow_candidate=allow_candidate,
    )


def validate_control_pack(
    value: object,
    *,
    policy: Mapping[str, Any],
    allow_candidate: bool = False,
) -> dict[str, Any]:
    """Validate a supplied pack; callers cannot self-assert compatibility."""

    contract = policy.get("control_pack_contract")
    if not isinstance(contract, Mapping):
        raise DisclosureBlocked(_unavailable_decision("control-pack-contract-unavailable"))
    if not isinstance(value, dict):
        raise DisclosureBlocked(_unavailable_decision("control-pack-incompatible"))
    valid_status = value.get("status") == "active" or (
        allow_candidate and value.get("status") == "candidate"
    )
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
    control_pack: Mapping[str, Any] | None = None,
    allow_candidate_control_pack: bool = False,
    complete: bool = True,
) -> dict[str, Any]:
    """Return one exact decision; raise only when registry resolution is unsafe."""

    active_policy = dict(policy) if policy is not None else load_policy()
    active_control_pack = (
        validate_control_pack(
            control_pack,
            policy=active_policy,
            allow_candidate=allow_candidate_control_pack,
        )
        if control_pack is not None
        else load_control_pack(policy=active_policy)
    )
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
        "control_pack_id": active_control_pack.get("pack_id"),
        "control_version": active_control_pack.get("control_version"),
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


def _cli() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--producer", required=True)
    parser.add_argument("--control-pack", type=Path)
    parser.add_argument("--allow-candidate-control-pack", action="store_true")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    artifacts = [
        OutboundArtifact(
            path=path,
            producer=args.producer,
            content=(ROOT / path).read_bytes(),
        )
        for path in args.paths
    ]
    policy = load_policy()
    control_pack = load_control_pack(
        args.control_pack,
        policy=policy,
        allow_candidate=args.allow_candidate_control_pack,
    )
    decision = evaluate_outbound_bundle(
        artifacts,
        operation=args.operation,
        source_revision=args.source_revision,
        policy=policy,
        control_pack=control_pack,
        allow_candidate_control_pack=args.allow_candidate_control_pack,
    )
    print(json.dumps(decision, sort_keys=True, indent=2))
    return 0 if decision["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(_cli())
