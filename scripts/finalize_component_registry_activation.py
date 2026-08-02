#!/usr/bin/env python3
"""Issue the fixed owner-local Component Registry activation readback.

The production entry point accepts no caller-selected authority, path, payload,
digest, revision, review evidence, or environment override.  Tests use the
explicit fixture-only verifier and a contained fixture path authority.
"""

from __future__ import annotations

import copy
import errno
import hashlib
import json
import os
import re
import secrets
import stat
import subprocess
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

try:
    from . import component_registry as registry
    from .path_authority import PathAuthorityError, ProjectPathAuthority
except ImportError:  # Direct script execution places scripts/ on sys.path.
    import component_registry as registry
    from path_authority import PathAuthorityError, ProjectPathAuthority


class ActivationFinalizationError(RuntimeError):
    """Raised when exact activation evidence cannot authorize a receipt."""


STAGE2_PULL_REQUEST_NUMBER = 501
STAGE2_ORIGINAL_CANONICAL_REVISION = (
    "c1c0b8ecbdcc1b4c7994b33f1a1cc72d61a20214"
)
STAGE2_ORIGINAL_REGISTRY_SHA256 = (
    "cfdcc68500fca953863aa34b77e7b5d687f13bda2f0ad63214373111959056e7"
)
STAGE2_ORIGINAL_DESIGN_ID = (
    "COMPONENT-REGISTRY-2026-002-STAGE2-IMPLEMENTATION-PR"
)
STAGE2_ORIGINAL_DESIGN_REVISION = (
    "sha256:16c7801b08397a640829bcb9141de7482c68ea9d9aa793fba0d1080fea9d95b0"
)
STAGE2_AUTHORITY_CORRECTION_DESIGN_ID = (
    "COMPONENT-REGISTRY-2026-002-AUTHORITY-CURRENTNESS-SEPARATION-CLOSEOUT"
)
STAGE2_AUTHORITY_CORRECTION_DESIGN_REVISION = (
    "sha256:70f48e4a6668e1cdee965c0777cc52056469b954df5abb34e95642e095fcfca5"
)
STAGE2_AUTHORITY_PROTOCOL = "component_registry_stage2_authority_digest_v1"
STAGE2_SOURCE_ADMISSION_PREDICATE = (
    "component_registry_source_revision_admission_v1"
)
STAGE2_AUTHORITY_RECEIPT_DIRECTORY = (
    "records/governance/component-registry/activation-readbacks/authority-v1"
)


def _run_json(*arguments: str) -> Any:
    try:
        completed = subprocess.run(
            list(arguments),
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return json.loads(completed.stdout)
    except (
        OSError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ) as exc:
        raise ActivationFinalizationError(
            "authenticated activation observation is unavailable"
        ) from exc


def _git(repository: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ActivationFinalizationError(
            "activation repository readback is unavailable"
        ) from exc
    return completed.stdout.strip()


def _registry_at_revision(
    repository: Path,
    revision: str,
) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ActivationFinalizationError(
            "historical Registry revision is invalid"
        )
    text = _git(
        repository,
        "show",
        f"{revision}:{registry.CANONICAL_REGISTRY_PATH}",
    )
    try:
        return registry._parse_closed_json_object(
            text,
            "historical Component Registry",
        )
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "historical Component Registry is invalid"
        ) from exc


def _paginated_pages(endpoint: str) -> list[Any]:
    value = _run_json(
        "gh",
        "api",
        "--paginate",
        "--slurp",
        endpoint,
    )
    if not isinstance(value, list):
        raise ActivationFinalizationError(
            "authenticated pagination is incomplete"
        )
    return value


def _paginated_array(endpoint: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in _paginated_pages(endpoint):
        if not isinstance(page, list) or any(
            not isinstance(item, dict) for item in page
        ):
            raise ActivationFinalizationError(
                "authenticated paginated array is malformed"
            )
        items.extend(page)
    return items


def _paginated_check_runs(
    endpoint: str,
) -> tuple[list[dict[str, Any]], int]:
    items: list[dict[str, Any]] = []
    declared_total: int | None = None
    for page in _paginated_pages(endpoint):
        if (
            not isinstance(page, dict)
            or not isinstance(page.get("total_count"), int)
            or not isinstance(page.get("check_runs"), list)
            or any(
                not isinstance(item, dict)
                for item in page["check_runs"]
            )
        ):
            raise ActivationFinalizationError(
                "authenticated check-run page is malformed"
            )
        if declared_total is None:
            declared_total = page["total_count"]
        elif declared_total != page["total_count"]:
            raise ActivationFinalizationError(
                "check-run total count changed during pagination"
            )
        items.extend(page["check_runs"])
    if declared_total is None or declared_total != len(items):
        raise ActivationFinalizationError(
            "check-run pagination is incomplete"
        )
    return items, declared_total


def _required_status_checks(
    branch: Mapping[str, Any],
    rules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    required: dict[tuple[str, int | None], dict[str, Any]] = {}

    def include(context: object, app_id: object) -> None:
        if not isinstance(context, str) or not context:
            raise ActivationFinalizationError(
                "required status-check context is invalid"
            )
        normalized_app = (
            None
            if app_id is None
            else app_id
            if isinstance(app_id, int) and app_id > 0
            else ...
        )
        if normalized_app is ...:
            raise ActivationFinalizationError(
                "required status-check app identity is invalid"
            )
        required[(context, normalized_app)] = {
            "context": context,
            "app_id": normalized_app,
        }

    protection = branch.get("protection")
    required_status = (
        protection.get("required_status_checks")
        if isinstance(protection, Mapping)
        else None
    )
    if isinstance(required_status, Mapping):
        checks = required_status.get("checks")
        contexts = required_status.get("contexts")
        if isinstance(checks, list):
            for check in checks:
                if not isinstance(check, Mapping):
                    raise ActivationFinalizationError(
                        "branch required-check definition is invalid"
                    )
                include(
                    check.get("context") or check.get("name"),
                    check.get("app_id"),
                )
        if isinstance(contexts, list):
            for context in contexts:
                include(context, None)
    for rule in rules:
        if rule.get("type") != "required_status_checks":
            continue
        parameters = rule.get("parameters")
        entries = (
            parameters.get("required_status_checks")
            if isinstance(parameters, Mapping)
            else None
        )
        if not isinstance(entries, list):
            raise ActivationFinalizationError(
                "ruleset required-check definition is invalid"
            )
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise ActivationFinalizationError(
                    "ruleset required-check entry is invalid"
                )
            include(
                entry.get("context"),
                entry.get("integration_id"),
            )
    return [
        required[key]
        for key in sorted(
            required,
            key=lambda item: (item[0], item[1] or 0),
        )
    ]


def _stage2_authority_receipt_logical_path(authority_digest: str) -> str:
    if registry.SHA256_RE.fullmatch(authority_digest) is None:
        raise ActivationFinalizationError(
            "Stage 2 authority digest cannot select receipt evidence"
        )
    function = getattr(
        registry,
        "_stage2_authority_readback_logical_path",
        None,
    )
    if not callable(function):
        raise ActivationFinalizationError(
            "Stage 2 authority receipt path implementation is unavailable"
        )
    try:
        logical = function(authority_digest)
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "Stage 2 authority receipt path cannot be derived"
        ) from exc
    expected = (
        f"{STAGE2_AUTHORITY_RECEIPT_DIRECTORY}/{authority_digest}.json"
    )
    if logical != expected:
        raise ActivationFinalizationError(
            "Stage 2 authority receipt path is not the fixed v1 namespace"
        )
    return logical


def _stage2_authority_model(
    stage2_registry: Mapping[str, Any],
) -> tuple[str, int, str]:
    model = stage2_registry.get("authority_digest_model")
    if not isinstance(model, Mapping):
        raise ActivationFinalizationError(
            "Stage 2 authority digest model is unavailable"
        )
    protocol = model.get("protocol")
    generation = model.get("generation")
    predicate = model.get("source_revision_admission_predicate")
    registry_protocol = getattr(
        registry,
        "STAGE2_AUTHORITY_DIGEST_PROTOCOL",
        None,
    )
    registry_predicate = getattr(
        registry,
        "STAGE2_SOURCE_REVISION_ADMISSION_PREDICATE",
        None,
    )
    if (
        registry_protocol != STAGE2_AUTHORITY_PROTOCOL
        or protocol != registry_protocol
        or not isinstance(generation, int)
        or isinstance(generation, bool)
        or generation < 1
        or registry_predicate != STAGE2_SOURCE_ADMISSION_PREDICATE
        or predicate != registry_predicate
    ):
        raise ActivationFinalizationError(
            "Stage 2 authority digest model is not exact"
        )
    return protocol, generation, predicate


def _stage2_authority_digest(
    stage2_registry: Mapping[str, Any],
) -> str:
    function = getattr(registry, "_stage2_authority_digest", None)
    if not callable(function):
        raise ActivationFinalizationError(
            "Stage 2 authority digest implementation is unavailable"
        )
    try:
        digest = function(stage2_registry)
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "Stage 2 authority digest cannot be derived"
        ) from exc
    if not isinstance(digest, str) or registry.SHA256_RE.fullmatch(digest) is None:
        raise ActivationFinalizationError(
            "Stage 2 authority digest has an invalid result"
        )
    return digest


def _pull_request_for_merge_commit(
    merge_commit: str,
) -> dict[str, Any]:
    associated = _paginated_array(
        "repos/Thorncrag/ARRP/commits/"
        f"{merge_commit}/pulls?per_page=100"
    )
    matching = [
        item
        for item in associated
        if item.get("merge_commit_sha") == merge_commit
        and item.get("merged_at") is not None
        and item.get("base", {}).get("repo", {}).get("full_name")
        == "Thorncrag/ARRP"
        and item.get("base", {}).get("ref") == "main"
    ]
    if len(matching) != 1 or not isinstance(matching[0].get("number"), int):
        raise ActivationFinalizationError(
            "canonical merge lacks one exact pull request"
        )
    pull_request = _run_json(
        "gh",
        "api",
        f"repos/Thorncrag/ARRP/pulls/{matching[0]['number']}",
    )
    if not isinstance(pull_request, dict):
        raise ActivationFinalizationError(
            "canonical pull request observation is malformed"
        )
    return pull_request


def _collect_pull_request_checks(
    pull_request: Mapping[str, Any],
    *,
    branch: Mapping[str, Any],
    effective_rules: list[dict[str, Any]],
) -> dict[str, Any]:
    reviewed_head = str(pull_request.get("head", {}).get("sha") or "")
    checks, check_total = _paginated_check_runs(
        f"repos/Thorncrag/ARRP/commits/{reviewed_head}/check-runs?per_page=100"
    )
    statuses = _paginated_array(
        f"repos/Thorncrag/ARRP/commits/{reviewed_head}/statuses?per_page=100"
    )
    return {
        "check_runs": checks,
        "check_runs_total_count": check_total,
        "check_runs_complete": True,
        "legacy_statuses": statuses,
        "legacy_statuses_complete": True,
        "required_status_checks": _required_status_checks(
            branch,
            effective_rules,
        ),
        "requirements_complete": True,
    }


def _collect_effective_main_rules() -> dict[str, Any]:
    effective = _paginated_array(
        "repos/Thorncrag/ARRP/rules/branches/main?per_page=100"
    )
    ruleset_ids = sorted(
        {
            item.get("ruleset_id")
            for item in effective
            if isinstance(item.get("ruleset_id"), int)
            and item.get("ruleset_id") > 0
        }
    )
    details: list[dict[str, Any]] = []
    for ruleset_id in ruleset_ids:
        detail = _run_json(
            "gh",
            "api",
            (
                "repos/Thorncrag/ARRP/rulesets/"
                f"{ruleset_id}?includes_parents=true"
            ),
        )
        if (
            not isinstance(detail, dict)
            or detail.get("id") != ruleset_id
            or detail.get("enforcement") != "active"
            or not isinstance(detail.get("bypass_actors"), list)
        ):
            raise ActivationFinalizationError(
                "effective ruleset bypass posture is unavailable"
            )
        details.append(detail)
    return {
        "effective_rules": effective,
        "rulesets": details,
        "complete": True,
    }


def _collect_classic_main_protection() -> dict[str, Any]:
    """Return the closed rule posture supplied by classic branch protection."""

    protection = _run_json(
        "gh",
        "api",
        "repos/Thorncrag/ARRP/branches/main/protection",
    )
    if not isinstance(protection, Mapping):
        raise ActivationFinalizationError(
            "classic main branch protection is unavailable"
        )
    rule_types: set[str] = set()
    if isinstance(protection.get("required_status_checks"), Mapping):
        rule_types.add("required_status_checks")
    if isinstance(protection.get("required_pull_request_reviews"), Mapping):
        rule_types.add("pull_request")
    allow_force_pushes = protection.get("allow_force_pushes")
    allow_deletions = protection.get("allow_deletions")
    enforce_admins = protection.get("enforce_admins")
    if not all(
        isinstance(value, Mapping)
        and isinstance(value.get("enabled"), bool)
        for value in (allow_force_pushes, allow_deletions, enforce_admins)
    ):
        raise ActivationFinalizationError(
            "classic main branch protection posture is incomplete"
        )
    if allow_force_pushes["enabled"] is False:
        rule_types.add("non_fast_forward")
    if allow_deletions["enabled"] is False:
        rule_types.add("deletion")
    return {
        "rule_types": sorted(rule_types),
        "bypass_permitted": enforce_admins["enabled"] is False,
        "complete": True,
    }


def _merge_evidence(
    repository: Path,
    pull_request: Mapping[str, Any],
    merge_commit: str,
) -> dict[str, Any]:
    if re.fullmatch(r"[0-9a-f]{40}", merge_commit) is None:
        raise ActivationFinalizationError("canonical merge revision is invalid")
    parents = _git(
        repository,
        "rev-list",
        "--parents",
        "-n",
        "1",
        merge_commit,
    ).split()
    reviewed_head = str(pull_request.get("head", {}).get("sha") or "")
    if len(parents) != 3 or parents[0] != merge_commit or parents[2] != reviewed_head:
        raise ActivationFinalizationError(
            "canonical merge parents do not bind the reviewed head"
        )
    base_revision = parents[1]
    merge_base = _git(repository, "merge-base", base_revision, reviewed_head)
    merge_tree = _git(repository, "show", "-s", "--format=%T", merge_commit)
    reviewed_tree = _git(repository, "show", "-s", "--format=%T", reviewed_head)
    merged_by = pull_request.get("merged_by")
    if (
        merge_base != base_revision
        or merge_tree != reviewed_tree
        or pull_request.get("state") != "closed"
        or pull_request.get("merged") is not True
        or pull_request.get("merge_commit_sha") != merge_commit
        or pull_request.get("auto_merge") is not None
        or pull_request.get("base", {}).get("repo", {}).get("full_name")
        != "Thorncrag/ARRP"
        or pull_request.get("base", {}).get("ref") != "main"
        or not isinstance(pull_request.get("id"), int)
        or not isinstance(pull_request.get("number"), int)
        or not isinstance(pull_request.get("node_id"), str)
        or not isinstance(merged_by, Mapping)
        or merged_by.get("login") != "Thorncrag"
        or not isinstance(merged_by.get("id"), int)
        or not isinstance(merged_by.get("node_id"), str)
    ):
        raise ActivationFinalizationError(
            "canonical pull request merge evidence differs"
        )
    _exact_timestamp(pull_request.get("merged_at"), "canonical merge")
    return {
        "pull_request_number": pull_request["number"],
        "pull_request_id": pull_request["id"],
        "pull_request_node_id": pull_request["node_id"],
        "base_revision": base_revision,
        "reviewed_head": reviewed_head,
        "reviewed_tree": reviewed_tree,
        "merge_commit": merge_commit,
        "merge_tree": merge_tree,
        "merged_by": "Thorncrag",
        "merged_by_id": merged_by["id"],
        "merged_by_node_id": merged_by["node_id"],
        "merged_at": pull_request["merged_at"],
    }


def _validated_required_check_evidence(
    observations: Mapping[str, Any],
    *,
    reviewed_head: str,
) -> list[dict[str, Any]]:
    _validate_required_checks(observations, reviewed_head=reviewed_head)
    checks = observations["check_runs"]
    statuses = observations["legacy_statuses"]
    evidence: list[dict[str, Any]] = []
    evidence_by_identity: dict[tuple[str, int | None], dict[str, Any]] = {}

    def include(item: dict[str, Any]) -> None:
        identity = (str(item["context"]), item.get("app_id"))
        existing = evidence_by_identity.get(identity)
        if existing is not None:
            if existing != item:
                raise ActivationFinalizationError(
                    "required check resolves to conflicting evidence"
                )
            return
        evidence_by_identity[identity] = item
        evidence.append(item)

    for requirement in observations["required_status_checks"]:
        context = requirement["context"]
        app_id = requirement["app_id"]
        matching_checks = [
            item for item in checks
            if item.get("name") == context
            and item.get("head_sha") == reviewed_head
            and (app_id is None or item.get("app", {}).get("id") == app_id)
        ]
        if matching_checks:
            item = matching_checks[0]
            include({
                "evidence_type": "check_run",
                "context": context,
                "app_id": item.get("app", {}).get("id"),
                "run_id": item.get("id"),
                "completed_at": item.get("completed_at"),
            })
            continue
        item = next(
            item for item in statuses
            if item.get("context") == context and item.get("sha") == reviewed_head
        )
        include({
            "evidence_type": "commit_status",
            "context": context,
            "app_id": None,
            "run_id": item.get("id"),
            "completed_at": item.get("updated_at"),
        })
    return sorted(
        evidence,
        key=lambda item: (str(item["context"]), int(item["app_id"] or 0)),
    )


def _collect_authenticated_observations(
    authority: ProjectPathAuthority,
    active_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Collect exact GitHub observations from the fixed production authority."""

    if authority.mode != "production_canonical":
        raise ActivationFinalizationError(
            "production observation collection requires fixed authority"
        )
    approval = active_registry["approval"]["value"]
    review_reference = str(approval["owner_review_reference"])
    match = registry.OWNER_REVIEW_REFERENCE_RE.fullmatch(review_reference)
    if match is None:
        raise ActivationFinalizationError(
            "activation approval review reference is invalid"
        )
    pull_request_number = int(match.group(1))
    pull_request = _run_json(
        "gh",
        "api",
        f"repos/Thorncrag/ARRP/pulls/{pull_request_number}",
    )
    branch = _run_json(
        "gh",
        "api",
        "repos/Thorncrag/ARRP/branches/main",
    )
    reviewed_head = str(pull_request.get("head", {}).get("sha") or "")
    checks, check_total = _paginated_check_runs(
        f"repos/Thorncrag/ARRP/commits/{reviewed_head}/check-runs?per_page=100"
    )
    statuses = _paginated_array(
        f"repos/Thorncrag/ARRP/commits/{reviewed_head}/statuses?per_page=100"
    )
    rules = _paginated_array(
        "repos/Thorncrag/ARRP/rules/branches/main?per_page=100"
    )
    remote_main = str(branch.get("commit", {}).get("sha") or "")
    reviewed_registry = _run_json(
        "gh",
        "api",
        "-H",
        "Accept: application/vnd.github.raw+json",
        (
            "repos/Thorncrag/ARRP/contents/"
            f"{registry.CANONICAL_REGISTRY_PATH}?ref={reviewed_head}"
        ),
    )
    remote_registry = _run_json(
        "gh",
        "api",
        "-H",
        "Accept: application/vnd.github.raw+json",
        (
            "repos/Thorncrag/ARRP/contents/"
            f"{registry.CANONICAL_REGISTRY_PATH}?ref={remote_main}"
        ),
    )
    return {
        "repository": "Thorncrag/ARRP",
        "default_branch": "main",
        "pull_request_number": pull_request_number,
        "pull_request_state": pull_request.get("state"),
        "pull_request_merged": pull_request.get("merged") is True,
        "pull_request_auto_merge": pull_request.get("auto_merge"),
        "merged_by": pull_request.get("merged_by", {}).get("login"),
        "pull_request_base_repository": pull_request.get("base", {})
        .get("repo", {})
        .get("full_name"),
        "pull_request_base_branch": pull_request.get("base", {}).get("ref"),
        "pull_request_base_revision": pull_request.get("base", {}).get("sha"),
        "reviewed_head_revision": reviewed_head,
        "merge_commit_sha": pull_request.get("merge_commit_sha"),
        "merged_at": pull_request.get("merged_at"),
        "check_runs": checks,
        "check_runs_total_count": check_total,
        "check_runs_complete": True,
        "legacy_statuses": statuses,
        "legacy_statuses_complete": True,
        "required_status_checks": _required_status_checks(
            branch,
            rules,
        ),
        "requirements_complete": True,
        "remote_main_revision": remote_main,
        "reviewed_registry": reviewed_registry,
        "remote_registry": remote_registry,
        "local_revision": _git(
            authority.repository_root,
            "rev-parse",
            "HEAD",
        ),
        "origin_main_revision": _git(
            authority.repository_root,
            "rev-parse",
            "refs/remotes/origin/main",
        ),
        "verified_at": datetime.now(timezone.utc).isoformat().replace(
            "+00:00",
            "Z",
        ),
    }


def _collect_stage2_authenticated_observations(
    authority: ProjectPathAuthority,
) -> dict[str, Any]:
    """Collect the fixed PR #501 Stage 2 adoption evidence."""
    if authority.mode != "production_canonical":
        raise ActivationFinalizationError(
            "Stage 2 observation collection requires fixed production authority"
        )
    pull_request = _run_json(
        "gh",
        "api",
        f"repos/Thorncrag/ARRP/pulls/{STAGE2_PULL_REQUEST_NUMBER}",
    )
    branch = _run_json("gh", "api", "repos/Thorncrag/ARRP/branches/main")
    reviewed_head = str(pull_request.get("head", {}).get("sha") or "")
    checks, check_total = _paginated_check_runs(
        f"repos/Thorncrag/ARRP/commits/{reviewed_head}/check-runs?per_page=100"
    )
    statuses = _paginated_array(
        f"repos/Thorncrag/ARRP/commits/{reviewed_head}/statuses?per_page=100"
    )
    rules = _paginated_array(
        "repos/Thorncrag/ARRP/rules/branches/main?per_page=100"
    )
    remote_main = str(branch.get("commit", {}).get("sha") or "")
    reviewed_registry = _run_json(
        "gh",
        "api",
        "-H",
        "Accept: application/vnd.github.raw+json",
        (
            "repos/Thorncrag/ARRP/contents/"
            f"{registry.CANONICAL_REGISTRY_PATH}?ref={reviewed_head}"
        ),
    )
    remote_registry = _run_json(
        "gh",
        "api",
        "-H",
        "Accept: application/vnd.github.raw+json",
        (
            "repos/Thorncrag/ARRP/contents/"
            f"{registry.CANONICAL_REGISTRY_PATH}?ref={remote_main}"
        ),
    )
    return {
        "repository": "Thorncrag/ARRP",
        "default_branch": "main",
        "pull_request_number": STAGE2_PULL_REQUEST_NUMBER,
        "pull_request_state": pull_request.get("state"),
        "pull_request_merged": pull_request.get("merged") is True,
        "pull_request_auto_merge": pull_request.get("auto_merge"),
        "merged_by": pull_request.get("merged_by", {}).get("login"),
        "pull_request_base_repository": pull_request.get("base", {})
        .get("repo", {})
        .get("full_name"),
        "pull_request_base_branch": pull_request.get("base", {}).get("ref"),
        "pull_request_base_revision": pull_request.get("base", {}).get("sha"),
        "reviewed_head_revision": reviewed_head,
        "merge_commit_sha": pull_request.get("merge_commit_sha"),
        "merged_at": pull_request.get("merged_at"),
        "check_runs": checks,
        "check_runs_total_count": check_total,
        "check_runs_complete": True,
        "legacy_statuses": statuses,
        "legacy_statuses_complete": True,
        "required_status_checks": _required_status_checks(branch, rules),
        "requirements_complete": True,
        "remote_main_revision": remote_main,
        "reviewed_registry": reviewed_registry,
        "remote_registry": remote_registry,
        "local_revision": _git(authority.repository_root, "rev-parse", "HEAD"),
        "origin_main_revision": _git(
            authority.repository_root,
            "rev-parse",
            "refs/remotes/origin/main",
        ),
        "verified_at": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
    }


def _is_ancestor(repository: Path, older: str, newer: str) -> bool:
    try:
        subprocess.run(
            ["git", "-C", str(repository), "merge-base", "--is-ancestor", older, newer],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.CalledProcessError:
        return False
    except (OSError, subprocess.SubprocessError) as exc:
        raise ActivationFinalizationError(
            "activation ancestry proof is unavailable"
        ) from exc
    return True


def _exact_timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ActivationFinalizationError(
            f"{label} timestamp is unavailable"
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ActivationFinalizationError(
            f"{label} timestamp is invalid"
        ) from exc
    if parsed.tzinfo is None:
        raise ActivationFinalizationError(
            f"{label} timestamp lacks a timezone"
        )
    return parsed.astimezone(timezone.utc)


def _git_registry_at_revision(
    repository: Path,
    revision: str,
) -> dict[str, Any]:
    try:
        value = json.loads(
            _git(
                repository,
                "show",
                f"{revision}:{registry.CANONICAL_REGISTRY_PATH}",
            )
        )
    except json.JSONDecodeError as exc:
        raise ActivationFinalizationError(
            "historical Component Registry is not valid JSON"
        ) from exc
    if not isinstance(value, dict):
        raise ActivationFinalizationError(
            "historical Component Registry is not one object"
        )
    return value


def _candidate_transition_evidence(
    authority: ProjectPathAuthority,
    active_registry: Mapping[str, Any],
    approval: Mapping[str, Any],
    *,
    reviewed_head: str,
    pull_request_base_revision: str,
) -> dict[str, Any]:
    parents = _git(
        authority.repository_root,
        "rev-list",
        "--parents",
        "-n",
        "1",
        reviewed_head,
    ).split()
    if len(parents) != 2 or parents[0] != reviewed_head:
        raise ActivationFinalizationError(
            "reviewed activation head lacks one exact candidate parent"
        )
    candidate_revision = parents[1]
    if approval.get("base_revision") != candidate_revision:
        raise ActivationFinalizationError(
            "activation approval base revision is not the immediate candidate "
            "parent"
        )
    if not _is_ancestor(
        authority.repository_root,
        pull_request_base_revision,
        candidate_revision,
    ):
        raise ActivationFinalizationError(
            "candidate parent is not descended from the canonical PR base"
        )
    candidate = _git_registry_at_revision(
        authority.repository_root,
        candidate_revision,
    )
    if candidate.get("status") != "candidate":
        raise ActivationFinalizationError(
            "reviewed activation parent is not a candidate registry"
        )
    candidate_parents = _git(
        authority.repository_root,
        "rev-list",
        "--parents",
        "-n",
        "1",
        candidate_revision,
    ).split()
    if (
        len(candidate_parents) != 2
        or candidate_parents[0] != candidate_revision
    ):
        raise ActivationFinalizationError(
            "candidate parent lacks one exact source-baseline parent"
        )
    candidate_base = candidate["source_baseline"]["repository_revision"]
    if candidate_base != candidate_parents[1]:
        raise ActivationFinalizationError(
            "candidate parent source baseline is not its immediate parent"
        )
    candidate_route = registry._routing_snapshot(candidate)
    expected_candidate_binding = registry._route_source_binding(
        candidate_base,
        candidate_route,
    )
    if (
        candidate["source_baseline"]["working_tree_binding"]["sha256"]
        != expected_candidate_binding
    ):
        raise ActivationFinalizationError(
            "candidate parent route binding is not exact"
        )
    candidate_digest = registry._canonical_registry_digest(candidate)
    if approval.get("candidate_registry_sha256") != candidate_digest:
        raise ActivationFinalizationError(
            "approval candidate digest differs from the reconstructed parent"
        )
    affected_ids = approval.get("affected_stable_ids")
    if affected_ids != ["COMPONENT-REGISTRY"]:
        raise ActivationFinalizationError(
            "activation affected stable IDs are not exact"
        )
    normalized_approval = copy.deepcopy(dict(approval))
    normalized_approval["bounded_diff_sha256"] = "0" * 64
    try:
        expected_normalized = registry.build_simulated_active_registry(
            candidate,
            repository_revision=candidate_revision,
            approval_value=normalized_approval,
        )
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "candidate-to-active transition cannot be reconstructed"
        ) from exc
    normalized_active = copy.deepcopy(dict(active_registry))
    normalized_active["approval"]["value"][
        "bounded_diff_sha256"
    ] = "0" * 64
    if registry.canonical_json(normalized_active) != registry.canonical_json(
        expected_normalized
    ):
        raise ActivationFinalizationError(
            "reviewed active registry contains an unapproved transition"
        )
    normalized_active_digest = registry._canonical_registry_digest(
        normalized_active
    )
    transition = {
        "schema_version": 1,
        "algorithm": "component_registry_candidate_to_active_v1",
        "candidate_registry_sha256": candidate_digest,
        "normalized_active_registry_sha256": normalized_active_digest,
        "affected_stable_ids": ["COMPONENT-REGISTRY"],
    }
    bounded_diff = hashlib.sha256(
        registry.canonical_json(transition).encode("utf-8")
    ).hexdigest()
    if approval.get("bounded_diff_sha256") != bounded_diff:
        raise ActivationFinalizationError(
            "activation bounded diff is not deterministically derived"
        )
    return {
        "candidate_revision": candidate_revision,
        "candidate_registry_sha256": candidate_digest,
        "normalized_active_registry_sha256": normalized_active_digest,
        "bounded_diff_sha256": bounded_diff,
    }


def _validate_required_checks(
    observations: Mapping[str, Any],
    *,
    reviewed_head: str,
) -> datetime:
    checks = observations.get("check_runs")
    statuses = observations.get("legacy_statuses")
    requirements = observations.get("required_status_checks")
    if (
        observations.get("check_runs_complete") is not True
        or observations.get("legacy_statuses_complete") is not True
        or observations.get("requirements_complete") is not True
        or not isinstance(checks, list)
        or observations.get("check_runs_total_count") != len(checks)
        or not isinstance(statuses, list)
        or not isinstance(requirements, list)
        or not requirements
    ):
        raise ActivationFinalizationError(
            "required review or check evidence is incomplete"
        )
    identities: set[tuple[str, int | None]] = set()
    completion_times: list[datetime] = []
    for requirement in requirements:
        if not isinstance(requirement, Mapping):
            raise ActivationFinalizationError(
                "required status-check definition is invalid"
            )
        context = requirement.get("context")
        app_id = requirement.get("app_id")
        if (
            not isinstance(context, str)
            or not context
            or (
                app_id is not None
                and (not isinstance(app_id, int) or app_id <= 0)
            )
            or (context, app_id) in identities
        ):
            raise ActivationFinalizationError(
                "required status-check identity is invalid or duplicated"
            )
        identities.add((context, app_id))
        matching_checks = [
            item
            for item in checks
            if isinstance(item, Mapping)
            and item.get("name") == context
            and item.get("head_sha") == reviewed_head
            and (
                app_id is None
                or item.get("app", {}).get("id") == app_id
            )
        ]
        matching_statuses = (
            []
            if app_id is not None
            else [
                item
                for item in statuses
                if isinstance(item, Mapping)
                and item.get("context") == context
                and item.get("sha") == reviewed_head
            ]
        )
        matching = [*matching_checks, *matching_statuses]
        if len(matching) != 1:
            raise ActivationFinalizationError(
                "required exact-head check is missing or ambiguous"
            )
        item = matching[0]
        if item in matching_checks:
            succeeded = (
                item.get("status") == "completed"
                and item.get("conclusion") == "success"
            )
            completed_at = item.get("completed_at")
        else:
            succeeded = item.get("state") == "success"
            completed_at = item.get("updated_at")
        if not succeeded:
            raise ActivationFinalizationError(
                "required exact-head check is not a terminal success"
            )
        completion_times.append(
            _exact_timestamp(completed_at, "required exact-head check")
        )
    return max(completion_times)


def _build_receipt(
    authority: ProjectPathAuthority,
    active_registry: Mapping[str, Any],
    observations: Mapping[str, Any],
) -> dict[str, Any]:
    approval = active_registry.get("approval", {}).get("value")
    if not isinstance(approval, Mapping):
        raise ActivationFinalizationError(
            "active owner approval is unavailable"
        )
    review_match = registry.OWNER_REVIEW_REFERENCE_RE.fullmatch(
        str(approval.get("owner_review_reference") or "")
    )
    if review_match is None:
        raise ActivationFinalizationError(
            "owner review reference is not canonical"
        )
    pull_request_number = int(review_match.group(1))
    reviewed_head = str(observations.get("reviewed_head_revision") or "")
    merge_commit = str(observations.get("merge_commit_sha") or "")
    remote_main = str(observations.get("remote_main_revision") or "")
    local_revision = str(observations.get("local_revision") or "")
    origin_main = str(observations.get("origin_main_revision") or "")
    pull_request_base = str(
        observations.get("pull_request_base_revision") or ""
    )
    if (
        observations.get("repository") != "Thorncrag/ARRP"
        or observations.get("default_branch") != "main"
        or observations.get("pull_request_base_repository")
        != "Thorncrag/ARRP"
        or observations.get("pull_request_base_branch") != "main"
        or observations.get("pull_request_number") != pull_request_number
        or observations.get("pull_request_state") != "closed"
        or observations.get("pull_request_merged") is not True
        or observations.get("pull_request_auto_merge") is not None
        or observations.get("merged_by") != "Thorncrag"
        or not all(
            isinstance(value, str)
            and len(value) == 40
            and all(char in "0123456789abcdef" for char in value)
            for value in (
                reviewed_head,
                merge_commit,
                remote_main,
                local_revision,
                origin_main,
                pull_request_base,
            )
        )
        or merge_commit != remote_main
        or local_revision != merge_commit
        or origin_main != merge_commit
    ):
        raise ActivationFinalizationError(
            "pull request or repository identity readback differs"
        )
    if not _is_ancestor(
        authority.repository_root,
        reviewed_head,
        merge_commit,
    ):
        raise ActivationFinalizationError(
            "reviewed head is not incorporated by the exact merge commit"
        )
    transition = _candidate_transition_evidence(
        authority,
        active_registry,
        approval,
        reviewed_head=reviewed_head,
        pull_request_base_revision=pull_request_base,
    )
    checks_completed_at = _validate_required_checks(
        observations,
        reviewed_head=reviewed_head,
    )
    if not _is_ancestor(
        authority.repository_root,
        pull_request_base,
        transition["candidate_revision"],
    ):
        raise ActivationFinalizationError(
            "activation candidate is not descended from the PR base"
        )
    reviewed_registry = observations.get("reviewed_registry")
    remote_registry = observations.get("remote_registry")
    if (
        not isinstance(reviewed_registry, Mapping)
        or not isinstance(remote_registry, Mapping)
    ):
        raise ActivationFinalizationError(
            "remote Component Registry readback is unavailable"
        )
    registry_digest = registry._canonical_registry_digest(active_registry)
    if (
        registry._canonical_registry_digest(reviewed_registry)
        != registry_digest
        or registry.canonical_json(reviewed_registry)
        != registry.canonical_json(active_registry)
        or reviewed_registry.get("status") != "active"
        or registry._canonical_registry_digest(remote_registry)
        != registry_digest
        or registry.canonical_json(remote_registry)
        != registry.canonical_json(active_registry)
        or remote_registry.get("status") != "active"
    ):
        raise ActivationFinalizationError(
            "remote Component Registry differs from the activated authority"
        )
    approval_time = _exact_timestamp(
        approval.get("approved_at"),
        "activation approval",
    )
    merged_time = _exact_timestamp(
        observations.get("merged_at"),
        "pull request merge",
    )
    verified_time = _exact_timestamp(
        observations.get("verified_at"),
        "activation verification",
    )
    if not approval_time <= checks_completed_at <= merged_time <= verified_time:
        raise ActivationFinalizationError(
            "activation evidence chronology is invalid"
        )
    approval_digest = hashlib.sha256(
        registry.canonical_json(approval).encode("utf-8")
    ).hexdigest()
    receipt = {
        "schema_version": 1,
        "verification_type": "component_registry_activation_readback",
        "verification_state": "authenticated_owner_readback",
        "complete": True,
        "issuer": "component_registry_activation_finalizer",
        "repository": "Thorncrag/ARRP",
        "default_branch": "main",
        "registry_id": active_registry["registry_id"],
        "registry_path": registry.CANONICAL_REGISTRY_PATH,
        "registry_revision": active_registry["registry_revision"],
        "registry_sha256": registry_digest,
        "governance_change_id": approval["governance_change_id"],
        "implementation_contract_id": approval[
            "implementation_contract_id"
        ],
        "approval_sha256": approval_digest,
        "candidate_registry_sha256": transition[
            "candidate_registry_sha256"
        ],
        "bounded_diff_sha256": transition["bounded_diff_sha256"],
        "owner_review_reference": approval["owner_review_reference"],
        "pull_request_number": pull_request_number,
        "approval_evidence_type": "github_owner_manual_merge",
        "approved_head_revision": reviewed_head,
        "approved_by": "@Thorncrag",
        "merged_by": "Thorncrag",
        "merged_at": observations["merged_at"],
        "merge_commit_revision": merge_commit,
        "required_checks_state": "success",
        "required_checks_revision": reviewed_head,
        "remote_main_revision": remote_main,
        "remote_registry_sha256": registry_digest,
        "verified_at": observations["verified_at"],
    }
    try:
        schema = registry._read_json(
            authority.repository_root
            / "framework"
            / "component-registry.schema.json"
        )
        registry._validate_activation_readback_schema(
            receipt,
            schema=schema,
        )
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "activation receipt failed its closed schema"
        ) from exc
    return receipt


def _write_fixed_receipt(
    authority: ProjectPathAuthority,
    receipt: Mapping[str, Any],
) -> Path:
    logical = registry._activation_readback_logical_path(
        str(receipt["registry_sha256"])
    )
    parts = Path(logical).parts
    current = authority.state_root
    for part in parts[:-1]:
        current = current / part
        try:
            current.mkdir(mode=0o700)
        except FileExistsError:
            metadata = current.lstat()
            if (
                stat.S_ISLNK(metadata.st_mode)
                or not stat.S_ISDIR(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o700
            ):
                raise ActivationFinalizationError(
                    "activation receipt directory is unsafe"
                )
    path = current / parts[-1]
    try:
        unexpected_temporaries = [
            entry
            for entry in current.iterdir()
            if entry.name.startswith(".")
        ]
    except OSError as exc:
        raise ActivationFinalizationError(
            "activation receipt directory cannot be inventoried safely"
        ) from exc
    if unexpected_temporaries:
        raise ActivationFinalizationError(
            "activation receipt directory contains unexpected temporary state"
        )
    try:
        path.lstat()
    except FileNotFoundError:
        pass
    else:
        raise ActivationFinalizationError(
            "activation receipt destination already exists"
        )
    payload = (
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    temporary = current / (
        f".{parts[-1]}.tmp-{os.getpid()}-{secrets.token_hex(12)}"
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(temporary, flags, 0o600)
    except OSError as exc:
        raise ActivationFinalizationError(
            "activation receipt temporary cannot be created safely"
        ) from exc
    try:
        try:
            offset = 0
            while offset < len(payload):
                written = os.write(descriptor, payload[offset:])
                if written <= 0:
                    raise OSError(
                        errno.EIO,
                        "short activation receipt write",
                    )
                offset += written
            os.fsync(descriptor)
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o600
            ):
                raise ActivationFinalizationError(
                    "activation receipt temporary is unsafe"
                )
        finally:
            os.close(descriptor)
    except (OSError, ActivationFinalizationError) as exc:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        if isinstance(exc, ActivationFinalizationError):
            raise
        raise ActivationFinalizationError(
            "activation receipt temporary write failed"
        ) from exc
    try:
        os.link(temporary, path, follow_symlinks=False)
        directory_descriptor = os.open(
            current,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as exc:
        raise ActivationFinalizationError(
            "activation receipt cannot be published atomically"
        ) from exc
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    directory_descriptor = os.open(
        current,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
    )
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)
    return path


def _read_exact_owner_receipt_bytes(path: Path) -> bytes:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ActivationFinalizationError(
            "Stage 2 authority receipt cannot be opened safely"
        ) from exc
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise ActivationFinalizationError(
                "Stage 2 authority receipt is unsafe"
            )
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, 16 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > registry.ACTIVATION_READBACK_MAX_BYTES:
                raise ActivationFinalizationError(
                    "Stage 2 authority receipt exceeds its bounded size"
                )
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _write_stage2_authority_receipt(
    authority: ProjectPathAuthority,
    receipt: Mapping[str, Any],
) -> tuple[Path, bool]:
    logical = _stage2_authority_receipt_logical_path(
        str(receipt["authority_sha256"])
    )
    parts = Path(logical).parts
    current = authority.state_root
    for part in parts[:-1]:
        current = current / part
        try:
            current.mkdir(mode=0o700)
        except FileExistsError:
            metadata = current.lstat()
            if (
                stat.S_ISLNK(metadata.st_mode)
                or not stat.S_ISDIR(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o700
            ):
                raise ActivationFinalizationError(
                    "Stage 2 authority receipt directory is unsafe"
                )
    path = current / parts[-1]
    payload = (
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    try:
        entries = list(current.iterdir())
    except OSError as exc:
        raise ActivationFinalizationError(
            "Stage 2 authority receipt namespace cannot be inventoried"
        ) from exc
    for entry in entries:
        if entry.name.startswith("."):
            raise ActivationFinalizationError(
                "Stage 2 authority receipt namespace contains temporary state"
            )
        metadata = entry.lstat()
        if (
            entry.suffix != ".json"
            or registry.SHA256_RE.fullmatch(entry.stem) is None
            or stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise ActivationFinalizationError(
                "Stage 2 authority receipt namespace contains unsafe state"
            )
    if path.exists():
        if _read_exact_owner_receipt_bytes(path) != payload:
            raise ActivationFinalizationError(
                "Stage 2 authority receipt conflicts with existing evidence"
            )
        return path, False
    temporary = current / (
        f".{parts[-1]}.tmp-{os.getpid()}-{secrets.token_hex(12)}"
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(temporary, flags, 0o600)
    except OSError as exc:
        raise ActivationFinalizationError(
            "Stage 2 authority receipt temporary cannot be created safely"
        ) from exc
    try:
        try:
            offset = 0
            while offset < len(payload):
                written = os.write(descriptor, payload[offset:])
                if written <= 0:
                    raise OSError(errno.EIO, "short authority receipt write")
                offset += written
            os.fsync(descriptor)
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o600
            ):
                raise ActivationFinalizationError(
                    "Stage 2 authority receipt temporary is unsafe"
                )
        finally:
            os.close(descriptor)
    except (OSError, ActivationFinalizationError) as exc:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        if isinstance(exc, ActivationFinalizationError):
            raise
        raise ActivationFinalizationError(
            "Stage 2 authority receipt temporary write failed"
        ) from exc
    created = True
    try:
        os.link(temporary, path, follow_symlinks=False)
    except FileExistsError:
        created = False
        if _read_exact_owner_receipt_bytes(path) != payload:
            raise ActivationFinalizationError(
                "Stage 2 authority receipt publication raced with conflicting evidence"
            )
    except OSError as exc:
        raise ActivationFinalizationError(
            "Stage 2 authority receipt cannot be published atomically"
        ) from exc
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    directory_descriptor = os.open(
        current,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
    )
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)
    if _read_exact_owner_receipt_bytes(path) != payload:
        raise ActivationFinalizationError(
            "Stage 2 authority receipt changed after publication"
        )
    return path, created


def verify_fixture_and_write(
    path_authority: ProjectPathAuthority,
    active_registry: Mapping[str, Any],
    authenticated_observations: Mapping[str, Any],
) -> dict[str, Any]:
    """Fixture-only construction harness; it cannot target production."""

    if path_authority.mode != "fixture":
        raise ActivationFinalizationError(
            "fixture verifier requires contained fixture authority"
        )
    try:
        schema = registry._read_json(
            path_authority.repository_root
            / "framework"
            / "component-registry.schema.json"
        )
        registry._validate_against_schema(
            active_registry,
            schema,
            schema,
        )
        configuration_view = (
            registry._validated_component_registry_routing_view(
                active_registry,
                active_configuration_validation_only=True,
            )
        )
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "fixture active configuration validation failed"
        ) from exc
    if (
        configuration_view.get("validation_mode")
        != "active_configuration_validation_only"
        or configuration_view.get("authoritative") is not False
        or configuration_view.get("executable") is not False
    ):
        raise ActivationFinalizationError(
            "fixture active configuration posture is invalid"
        )
    receipt = _build_receipt(
        path_authority,
        active_registry,
        authenticated_observations,
    )
    _write_fixed_receipt(path_authority, receipt)
    try:
        readback = registry._load_fixed_activation_readback(
            path_authority,
            active_registry,
            schema=schema,
        )
        active_view = registry._validated_component_registry_routing_view(
            active_registry,
            activation_readback=readback,
        )
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "fixture post-publication activation readback failed"
        ) from exc
    if (
        active_view.get("validation_mode") != "active_component_registry"
        or active_view.get("authoritative") is not True
        or active_view.get("executable") is not True
    ):
        raise ActivationFinalizationError(
            "fixture post-publication active posture is invalid"
        )
    return receipt


def _validate_canonical_pull_request_history(
    repository: Path,
    *,
    correction_merge: str,
    remote_main: str,
    pull_requests: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    correction_parents = _git(
        repository,
        "rev-list",
        "--parents",
        "-n",
        "1",
        correction_merge,
    ).split()
    if len(correction_parents) != 3:
        raise ActivationFinalizationError(
            "correction epoch is not an ordinary merge"
        )
    commits = [
        line
        for line in _git(
            repository,
            "rev-list",
            "--first-parent",
            "--reverse",
            f"{correction_parents[1]}..{remote_main}",
        ).splitlines()
        if line
    ]
    if not commits or commits[0] != correction_merge:
        raise ActivationFinalizationError(
            "canonical first-parent history lacks the correction epoch"
        )
    by_merge: dict[str, list[Mapping[str, Any]]] = {}
    for pull_request in pull_requests:
        merge = pull_request.get("merge_commit_sha")
        if not isinstance(merge, str):
            raise ActivationFinalizationError(
                "merged pull request history is malformed"
            )
        by_merge.setdefault(merge, []).append(pull_request)
    if set(by_merge) != set(commits) or any(
        len(matches) != 1 for matches in by_merge.values()
    ):
        raise ActivationFinalizationError(
            "merged pull requests and canonical first-parent history differ"
        )
    evidence: list[dict[str, Any]] = []
    previous = correction_parents[1]
    for commit in commits:
        merge = _merge_evidence(repository, by_merge[commit][0], commit)
        if merge["base_revision"] != previous:
            raise ActivationFinalizationError(
                "canonical first-parent pull request sequence differs"
            )
        evidence.append(merge)
        previous = commit
    return evidence


def _collect_stage2_authority_observations(
    authority: ProjectPathAuthority,
    stage2_registry: Mapping[str, Any],
) -> dict[str, Any]:
    if authority.mode != "production_canonical":
        raise ActivationFinalizationError(
            "Stage 2 authority observation requires fixed production authority"
        )
    repository_start = _run_json("gh", "api", "repos/Thorncrag/ARRP")
    branch_start = _run_json(
        "gh",
        "api",
        "repos/Thorncrag/ARRP/branches/main",
    )
    if not isinstance(repository_start, dict) or not isinstance(branch_start, dict):
        raise ActivationFinalizationError(
            "Stage 2 authority repository observation is malformed"
        )
    remote_main = str(branch_start.get("commit", {}).get("sha") or "")
    correction_pull_request = _pull_request_for_merge_commit(remote_main)
    stage2_pull_request = _run_json(
        "gh",
        "api",
        f"repos/Thorncrag/ARRP/pulls/{STAGE2_PULL_REQUEST_NUMBER}",
    )
    if not isinstance(stage2_pull_request, dict):
        raise ActivationFinalizationError(
            "Stage 2 predecessor pull request is malformed"
        )
    branch_rules = _collect_effective_main_rules()
    correction_checks = _collect_pull_request_checks(
        correction_pull_request,
        branch=branch_start,
        effective_rules=branch_rules["effective_rules"],
    )
    original_checks = _collect_pull_request_checks(
        stage2_pull_request,
        branch=branch_start,
        effective_rules=branch_rules["effective_rules"],
    )
    correction_merged_at = _exact_timestamp(
        correction_pull_request.get("merged_at"),
        "correction merge",
    )
    closed = _paginated_array(
        "repos/Thorncrag/ARRP/pulls?state=closed&base=main&sort=updated&"
        "direction=asc&per_page=100"
    )
    qualifying_numbers = sorted(
        {
            int(item["number"])
            for item in closed
            if isinstance(item.get("number"), int)
            and item.get("merged_at") is not None
            and _exact_timestamp(item.get("merged_at"), "merged pull request")
            >= correction_merged_at
        }
    )
    pull_requests = [
        _run_json(
            "gh",
            "api",
            f"repos/Thorncrag/ARRP/pulls/{number}",
        )
        for number in qualifying_numbers
    ]
    if any(not isinstance(item, dict) for item in pull_requests):
        raise ActivationFinalizationError(
            "canonical pull request history is malformed"
        )
    remote_commit = _run_json(
        "gh",
        "api",
        f"repos/Thorncrag/ARRP/git/commits/{remote_main}",
    )
    reviewed_head = str(correction_pull_request.get("head", {}).get("sha") or "")
    reviewed_registry = _run_json(
        "gh",
        "api",
        "-H",
        "Accept: application/vnd.github.raw+json",
        (
            "repos/Thorncrag/ARRP/contents/"
            f"{registry.CANONICAL_REGISTRY_PATH}?ref={reviewed_head}"
        ),
    )
    remote_registry = _run_json(
        "gh",
        "api",
        "-H",
        "Accept: application/vnd.github.raw+json",
        (
            "repos/Thorncrag/ARRP/contents/"
            f"{registry.CANONICAL_REGISTRY_PATH}?ref={remote_main}"
        ),
    )
    original_reviewed_head = str(
        stage2_pull_request.get("head", {}).get("sha") or ""
    )
    original_registry = _run_json(
        "gh",
        "api",
        "-H",
        "Accept: application/vnd.github.raw+json",
        (
            "repos/Thorncrag/ARRP/contents/"
            f"{registry.CANONICAL_REGISTRY_PATH}?ref={original_reviewed_head}"
        ),
    )
    repository_end = _run_json("gh", "api", "repos/Thorncrag/ARRP")
    branch_end = _run_json(
        "gh",
        "api",
        "repos/Thorncrag/ARRP/branches/main",
    )
    if not isinstance(repository_end, dict) or not isinstance(branch_end, dict):
        raise ActivationFinalizationError(
            "Stage 2 authority closing observation is malformed"
        )
    if (
        repository_start.get("id") != repository_end.get("id")
        or repository_start.get("node_id") != repository_end.get("node_id")
        or repository_start.get("full_name") != repository_end.get("full_name")
        or branch_end.get("commit", {}).get("sha") != remote_main
    ):
        raise ActivationFinalizationError(
            "remote repository moved during authority observation"
        )
    return {
        "repository": repository_start,
        "remote_main_revision": remote_main,
        "remote_commit": remote_commit,
        "correction_pull_request": correction_pull_request,
        "correction_checks": correction_checks,
        "original_pull_request": stage2_pull_request,
        "original_checks": original_checks,
        "pull_requests": pull_requests,
        "effective_rules": branch_rules,
        "reviewed_registry": reviewed_registry,
        "remote_registry": remote_registry,
        "original_registry": original_registry,
        "local_revision": _git(authority.repository_root, "rev-parse", "HEAD"),
        "origin_main_revision": _git(
            authority.repository_root,
            "rev-parse",
            "refs/remotes/origin/main",
        ),
    }


def _build_stage2_authority_receipt(
    authority: ProjectPathAuthority,
    stage2_registry: Mapping[str, Any],
    observations: Mapping[str, Any],
) -> dict[str, Any]:
    if authority.mode != "production_canonical":
        raise ActivationFinalizationError(
            "Stage 2 authority receipt requires fixed production authority"
        )
    try:
        registry.validate_stage2_registry(
            stage2_registry,
            root=authority.repository_root,
        )
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "Stage 2 authority Registry validation failed"
        ) from exc
    protocol, generation, predicate = _stage2_authority_model(stage2_registry)
    authority_digest = _stage2_authority_digest(stage2_registry)
    registry_digest = registry._canonical_registry_digest(stage2_registry)
    repository = observations.get("repository")
    correction_pr = observations.get("correction_pull_request")
    original_pr = observations.get("original_pull_request")
    remote_main = str(observations.get("remote_main_revision") or "")
    if (
        not isinstance(repository, Mapping)
        or not isinstance(repository.get("id"), int)
        or not isinstance(repository.get("node_id"), str)
        or repository.get("full_name") != "Thorncrag/ARRP"
        or repository.get("default_branch") != "main"
        or not isinstance(correction_pr, Mapping)
        or not isinstance(original_pr, Mapping)
        or correction_pr.get("base", {}).get("repo", {}).get("id")
        != repository.get("id")
        or original_pr.get("base", {}).get("repo", {}).get("id")
        != repository.get("id")
        or observations.get("local_revision") != remote_main
        or observations.get("origin_main_revision") != remote_main
    ):
        raise ActivationFinalizationError(
            "Stage 2 authority repository identity differs"
        )
    rules = observations.get("effective_rules")
    if (
        not isinstance(rules, Mapping)
        or rules.get("complete") is not True
        or not isinstance(rules.get("effective_rules"), list)
        or not isinstance(rules.get("rulesets"), list)
        or any(
            not isinstance(item, Mapping)
            or not isinstance(item.get("bypass_actors"), list)
            for item in rules.get("rulesets", [])
        )
    ):
        raise ActivationFinalizationError(
            "present effective rules or bypass posture is incomplete"
        )
    correction = _merge_evidence(
        authority.repository_root,
        correction_pr,
        remote_main,
    )
    history = _validate_canonical_pull_request_history(
        authority.repository_root,
        correction_merge=remote_main,
        remote_main=remote_main,
        pull_requests=observations.get("pull_requests", []),
    )
    original = _merge_evidence(
        authority.repository_root,
        original_pr,
        STAGE2_ORIGINAL_CANONICAL_REVISION,
    )
    correction_checks = _validated_required_check_evidence(
        observations["correction_checks"],
        reviewed_head=correction["reviewed_head"],
    )
    original_checks = _validated_required_check_evidence(
        observations["original_checks"],
        reviewed_head=original["reviewed_head"],
    )
    correction_check_time = max(
        _exact_timestamp(item["completed_at"], "correction check")
        for item in correction_checks
    )
    original_check_time = max(
        _exact_timestamp(item["completed_at"], "Stage 2 adoption check")
        for item in original_checks
    )
    if (
        original["pull_request_number"] != STAGE2_PULL_REQUEST_NUMBER
        or original["merge_commit"] != STAGE2_ORIGINAL_CANONICAL_REVISION
        or not original_check_time
        <= _exact_timestamp(original["merged_at"], "Stage 2 adoption merge")
        or not correction_check_time
        <= _exact_timestamp(correction["merged_at"], "correction merge")
    ):
        raise ActivationFinalizationError(
            "Stage 2 authority chronology or predecessor evidence differs"
        )
    original_registry = observations.get("original_registry")
    reviewed_registry = observations.get("reviewed_registry")
    remote_registry = observations.get("remote_registry")
    if (
        not isinstance(original_registry, Mapping)
        or registry._canonical_registry_digest(original_registry)
        != STAGE2_ORIGINAL_REGISTRY_SHA256
        or not isinstance(reviewed_registry, Mapping)
        or registry.canonical_json(reviewed_registry)
        != registry.canonical_json(stage2_registry)
        or not isinstance(remote_registry, Mapping)
        or registry.canonical_json(remote_registry)
        != registry.canonical_json(stage2_registry)
    ):
        raise ActivationFinalizationError(
            "Stage 2 authority Registry revisions differ"
        )
    remote_commit = observations.get("remote_commit")
    remote_committed_at = (
        remote_commit.get("committer", {}).get("date")
        if isinstance(remote_commit, Mapping)
        else None
    )
    _exact_timestamp(remote_committed_at, "remote issuance commit")
    if history != [correction]:
        raise ActivationFinalizationError(
            "authority receipt issuance history is not the correction epoch"
        )
    receipt = {
        "schema_version": 1,
        "verification_type": "component_registry_stage2_authority_readback",
        "issuer": "component_registry_activation_finalizer",
        "repository": {
            "id": repository["id"],
            "node_id": repository["node_id"],
            "full_name": "Thorncrag/ARRP",
            "default_branch": "main",
        },
        "registry_id": stage2_registry["registry_id"],
        "registry_revision": stage2_registry["registry_revision"],
        "protocol": protocol,
        "generation": generation,
        "authority_sha256": authority_digest,
        "adopted_registry_sha256": STAGE2_ORIGINAL_REGISTRY_SHA256,
        "correction_registry_sha256": registry_digest,
        "canonical_revision": STAGE2_ORIGINAL_CANONICAL_REVISION,
        "issuance_revision": remote_main,
        "original_design": {
            "design_id": STAGE2_ORIGINAL_DESIGN_ID,
            "design_revision": STAGE2_ORIGINAL_DESIGN_REVISION,
        },
        "correction_design": {
            "design_id": STAGE2_AUTHORITY_CORRECTION_DESIGN_ID,
            "design_revision": STAGE2_AUTHORITY_CORRECTION_DESIGN_REVISION,
        },
        "validation_mode": "online_governed_eligibility",
        "source_revision_admission_predicate": predicate,
        "original_adoption_evidence": {
            **original,
            "required_checks": original_checks,
        },
        "correction_evidence": {
            **correction,
            "approved_by": "@Thorncrag",
            "required_checks": correction_checks,
        },
        "canonical_history": {
            "protocol_epoch_revision": remote_main,
            "epoch_revision": remote_main,
            "observed_remote_revision": remote_main,
            "observed_remote_commit_time": remote_committed_at,
            "merge_commits": [remote_main],
        },
    }
    validator = getattr(
        registry,
        "_validate_stage2_authority_readback_schema",
        None,
    )
    if not callable(validator):
        raise ActivationFinalizationError(
            "Stage 2 authority receipt schema validator is unavailable"
        )
    try:
        schema = registry._read_json(
            authority.repository_root
            / "framework"
            / "component-registry.schema.json"
        )
        validator(receipt, schema=schema)
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "Stage 2 authority receipt failed its closed schema"
        ) from exc
    return receipt


def _load_stage2_authority_receipt(
    authority: ProjectPathAuthority,
    stage2_registry: Mapping[str, Any],
) -> tuple[Path, dict[str, Any]]:
    authority_digest = _stage2_authority_digest(stage2_registry)
    logical = _stage2_authority_receipt_logical_path(authority_digest)
    path = authority.state_root.joinpath(*Path(logical).parts)
    try:
        schema = registry._read_json(
            authority.repository_root
            / "framework"
            / "component-registry.schema.json"
        )
    except (OSError, registry.RegistryError) as exc:
        raise ActivationFinalizationError(
            "Stage 2 authority receipt schema is unavailable"
        ) from exc
    directory = authority.state_root.joinpath(
        *Path(STAGE2_AUTHORITY_RECEIPT_DIRECTORY).parts
    )
    current = authority.state_root
    for part in Path(STAGE2_AUTHORITY_RECEIPT_DIRECTORY).parts:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise ActivationFinalizationError(
                "fixed Stage 2 authority receipt is unavailable"
            ) from exc
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISDIR(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o700
        ):
            raise ActivationFinalizationError(
                "Stage 2 authority receipt ancestry is unsafe"
            )
    try:
        entries = list(directory.iterdir())
    except OSError as exc:
        raise ActivationFinalizationError(
            "Stage 2 authority receipt namespace is unavailable"
        ) from exc
    receipts: dict[str, tuple[Path, dict[str, Any]]] = {}
    generations: set[int] = set()
    for entry in entries:
        try:
            metadata = entry.lstat()
            if (
                entry.suffix != ".json"
                or registry.SHA256_RE.fullmatch(entry.stem) is None
                or stat.S_ISLNK(metadata.st_mode)
                or not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o600
            ):
                raise ActivationFinalizationError(
                    "Stage 2 authority receipt namespace contains unsafe state"
                )
            item = registry._read_owner_only_json_object(entry)
            registry._validate_stage2_authority_readback_schema(
                item,
                schema=schema,
            )
        except (OSError, registry.RegistryError) as exc:
            raise ActivationFinalizationError(
                "Stage 2 authority receipt namespace is invalid"
            ) from exc
        generation = item.get("generation")
        if (
            item.get("authority_sha256") != entry.stem
            or item.get("protocol") != STAGE2_AUTHORITY_PROTOCOL
            or not isinstance(generation, int)
            or isinstance(generation, bool)
            or generation in generations
        ):
            raise ActivationFinalizationError(
                "Stage 2 authority receipt namespace is inconsistent"
            )
        generations.add(generation)
        receipts[entry.stem] = (entry, item)
    selected = receipts.get(authority_digest)
    if selected is None or selected[0] != path:
        raise ActivationFinalizationError(
            "fixed Stage 2 authority receipt is unavailable"
        )
    path, receipt = selected
    return path, receipt


def _checks_for_fixed_requirements(
    pull_request: Mapping[str, Any],
    requirements: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    reviewed_head = str(pull_request.get("head", {}).get("sha") or "")
    checks, check_total = _paginated_check_runs(
        f"repos/Thorncrag/ARRP/commits/{reviewed_head}/check-runs?per_page=100"
    )
    statuses = _paginated_array(
        f"repos/Thorncrag/ARRP/commits/{reviewed_head}/statuses?per_page=100"
    )
    normalized = [
        {
            "context": item.get("context"),
            "app_id": item.get("app_id"),
        }
        for item in requirements
    ]
    return {
        "check_runs": checks,
        "check_runs_total_count": check_total,
        "check_runs_complete": True,
        "legacy_statuses": statuses,
        "legacy_statuses_complete": True,
        "required_status_checks": normalized,
        "requirements_complete": True,
    }


def _validate_stage2_correction_registry_binding(
    correction_registry: Mapping[str, Any],
    receipt: Mapping[str, Any],
    *,
    current_authority_digest: str,
    current_model: tuple[str, int, str],
) -> None:
    if (
        registry._canonical_registry_digest(correction_registry)
        != receipt.get("correction_registry_sha256")
        or _stage2_authority_digest(correction_registry)
        != current_authority_digest
        or _stage2_authority_model(correction_registry) != current_model
    ):
        raise ActivationFinalizationError(
            "authority correction Registry binding differs"
        )


def verify_stage2_authority_v1_online_eligibility(
    authority: ProjectPathAuthority,
    stage2_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Read back fixed authority-v1 evidence without creating any state."""

    if (
        authority.mode != "production_canonical"
        or authority.repository_root != registry.ROOT
    ):
        raise ActivationFinalizationError(
            "Stage 2 online eligibility requires fixed production authority"
        )
    try:
        registry_path = authority.repository_path(
            registry.CANONICAL_REGISTRY_PATH,
            required=True,
        )
    except PathAuthorityError as exc:
        raise ActivationFinalizationError(
            "fixed production authority is unavailable"
        ) from exc
    tracked_registry = registry._read_json(registry_path)
    if registry.canonical_json(tracked_registry) != registry.canonical_json(
        stage2_registry
    ):
        raise ActivationFinalizationError(
            "Stage 2 authority source changed before online verification"
        )
    try:
        registry.validate_stage2_registry(
            stage2_registry,
            root=authority.repository_root,
        )
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "Stage 2 authority source currentness failed"
        ) from exc
    _path, receipt = _load_stage2_authority_receipt(
        authority,
        stage2_registry,
    )
    protocol, generation, predicate = _stage2_authority_model(stage2_registry)
    authority_digest = _stage2_authority_digest(stage2_registry)
    registry_digest = registry._canonical_registry_digest(stage2_registry)
    if (
        receipt.get("protocol") != protocol
        or receipt.get("generation") != generation
        or receipt.get("authority_sha256") != authority_digest
        or receipt.get("source_revision_admission_predicate") != predicate
        or receipt.get("adopted_registry_sha256")
        != STAGE2_ORIGINAL_REGISTRY_SHA256
        or receipt.get("canonical_revision")
        != STAGE2_ORIGINAL_CANONICAL_REVISION
        or receipt.get("validation_mode")
        != "online_governed_eligibility"
    ):
        raise ActivationFinalizationError(
            "Stage 2 authority receipt identity differs"
        )
    repository_start = _run_json("gh", "api", "repos/Thorncrag/ARRP")
    branch_start = _run_json(
        "gh",
        "api",
        "repos/Thorncrag/ARRP/branches/main",
    )
    if not isinstance(repository_start, Mapping) or not isinstance(
        branch_start,
        Mapping,
    ):
        raise ActivationFinalizationError(
            "online authority repository observation is malformed"
        )
    remote_main = str(branch_start.get("commit", {}).get("sha") or "")
    repository_evidence = receipt.get("repository")
    correction_evidence = receipt.get("correction_evidence")
    canonical_history = receipt.get("canonical_history")
    if (
        not isinstance(repository_evidence, Mapping)
        or repository_start.get("id") != repository_evidence.get("id")
        or repository_start.get("node_id") != repository_evidence.get("node_id")
        or repository_start.get("full_name") != "Thorncrag/ARRP"
        or repository_start.get("default_branch") != "main"
        or not isinstance(correction_evidence, Mapping)
        or not isinstance(canonical_history, Mapping)
        or receipt.get("issuance_revision")
        != canonical_history.get("epoch_revision")
        or canonical_history.get("protocol_epoch_revision")
        != receipt.get("issuance_revision")
    ):
        raise ActivationFinalizationError(
            "online authority repository or epoch identity differs"
        )
    correction_number = correction_evidence.get("pull_request_number")
    if not isinstance(correction_number, int):
        raise ActivationFinalizationError(
            "authority correction pull request identity is invalid"
        )
    correction_pull_request = _run_json(
        "gh",
        "api",
        f"repos/Thorncrag/ARRP/pulls/{correction_number}",
    )
    if not isinstance(correction_pull_request, Mapping):
        raise ActivationFinalizationError(
            "authority correction pull request is unavailable"
        )
    observed_correction = _merge_evidence(
        authority.repository_root,
        correction_pull_request,
        str(receipt["issuance_revision"]),
    )
    recorded_correction = {
        key: correction_evidence[key]
        for key in observed_correction
    }
    if observed_correction != recorded_correction:
        raise ActivationFinalizationError(
            "authority correction merge evidence differs"
        )
    correction_registry = _registry_at_revision(
        authority.repository_root,
        str(observed_correction["reviewed_head"]),
    )
    _validate_stage2_correction_registry_binding(
        correction_registry,
        receipt,
        current_authority_digest=authority_digest,
        current_model=(protocol, generation, predicate),
    )
    correction_time = _exact_timestamp(
        correction_evidence.get("merged_at"),
        "authority correction merge",
    )
    closed = _paginated_array(
        "repos/Thorncrag/ARRP/pulls?state=closed&base=main&sort=updated&"
        "direction=asc&per_page=100"
    )
    numbers = sorted(
        {
            int(item["number"])
            for item in closed
            if isinstance(item.get("number"), int)
            and item.get("merged_at") is not None
            and _exact_timestamp(item.get("merged_at"), "merged pull request")
            >= correction_time
        }
    )
    pull_requests = [
        _run_json(
            "gh",
            "api",
            f"repos/Thorncrag/ARRP/pulls/{number}",
        )
        for number in numbers
    ]
    if any(not isinstance(item, Mapping) for item in pull_requests):
        raise ActivationFinalizationError(
            "online canonical pull request history is malformed"
        )
    history = _validate_canonical_pull_request_history(
        authority.repository_root,
        correction_merge=str(receipt["issuance_revision"]),
        remote_main=remote_main,
        pull_requests=pull_requests,
    )
    fixed_requirements = correction_evidence.get("required_checks")
    if not isinstance(fixed_requirements, list) or not fixed_requirements:
        raise ActivationFinalizationError(
            "authority admission predicate lacks required checks"
        )
    requirements = [
        {"context": item.get("context"), "app_id": item.get("app_id")}
        for item in fixed_requirements
        if isinstance(item, Mapping)
    ]
    if len(requirements) != len(fixed_requirements):
        raise ActivationFinalizationError(
            "authority admission predicate check evidence is malformed"
        )
    pull_requests_by_merge = {
        str(item.get("merge_commit_sha")): item
        for item in pull_requests
    }
    for merge in history:
        pull_request = pull_requests_by_merge.get(str(merge["merge_commit"]))
        if pull_request is None:
            raise ActivationFinalizationError(
                "canonical merge lacks required check evidence"
            )
        check_observation = _checks_for_fixed_requirements(
            pull_request,
            requirements,
        )
        _validate_required_checks(
            check_observation,
            reviewed_head=str(merge["reviewed_head"]),
        )
    present_rules = _collect_effective_main_rules()
    classic_protection = _collect_classic_main_protection()
    present_rule_types = {
        item.get("type") for item in present_rules["effective_rules"]
    } | set(classic_protection["rule_types"])
    if (
        not {
            "deletion",
            "non_fast_forward",
            "pull_request",
            "required_status_checks",
        }
        <= present_rule_types
        or classic_protection["bypass_permitted"] is True
        or any(
            detail.get("bypass_actors")
            for detail in present_rules["rulesets"]
        )
    ):
        raise ActivationFinalizationError(
            "present effective protection permits history bypass"
        )
    remote_registry = _run_json(
        "gh",
        "api",
        "-H",
        "Accept: application/vnd.github.raw+json",
        (
            "repos/Thorncrag/ARRP/contents/"
            f"{registry.CANONICAL_REGISTRY_PATH}?ref={remote_main}"
        ),
    )
    local_revision = _git(authority.repository_root, "rev-parse", "HEAD")
    origin_main = _git(
        authority.repository_root,
        "rev-parse",
        "refs/remotes/origin/main",
    )
    repository_end = _run_json("gh", "api", "repos/Thorncrag/ARRP")
    branch_end = _run_json(
        "gh",
        "api",
        "repos/Thorncrag/ARRP/branches/main",
    )
    if (
        local_revision != remote_main
        or origin_main != remote_main
        or not isinstance(remote_registry, Mapping)
        or registry.canonical_json(remote_registry)
        != registry.canonical_json(stage2_registry)
        or not isinstance(repository_end, Mapping)
        or repository_end.get("id") != repository_start.get("id")
        or repository_end.get("full_name") != repository_start.get("full_name")
        or not isinstance(branch_end, Mapping)
        or branch_end.get("commit", {}).get("sha") != remote_main
    ):
        raise ActivationFinalizationError(
            "online authority observation is not one coherent canonical state"
        )
    return {
        "validation_mode": "online_governed_eligibility",
        "registry_sha256": registry_digest,
        "authority_sha256": authority_digest,
        "authority_protocol": protocol,
        "authority_generation": generation,
        "authoritative": True,
        "executable": False,
        "authority_effective": True,
        "source_revision_authorized": True,
        "source_bytes_current": True,
        "canonical_history_confirmed": True,
        "receipt_trusted": True,
        "activation_receipt_consulted": True,
        "runtime_live": "not_checked",
        "generation": generation,
        "receipt_verification_type": receipt["verification_type"],
        "issuance_revision": receipt["issuance_revision"],
        "remote_main_revision": remote_main,
    }


def _build_stage2_synthetic_receipt(
    proposed_registry: Mapping[str, Any],
    *,
    canonical_revision: str,
    adoption_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Build deterministic public-safe Stage 2 evidence for a fixture only."""
    if proposed_registry.get("schema_version") != 2:
        raise ActivationFinalizationError("Stage 2 receipt requires schema version 2")
    if proposed_registry.get("validation", {}).get("mode") != "proposed_revision_validation":
        raise ActivationFinalizationError("Stage 2 receipt requires a proposed revision")
    if registry.SHA256_RE.fullmatch(str(canonical_revision)) is not None:
        # A Git revision is exactly forty hexadecimal characters, not a digest.
        raise ActivationFinalizationError("canonical adoption revision has the wrong shape")
    if re.fullmatch(r"[0-9a-f]{40}", str(canonical_revision)) is None:
        raise ActivationFinalizationError("canonical adoption revision is invalid")
    required_evidence = {
        "adopted_by", "adopted_at", "pull_request", "base_revision",
        "reviewed_head", "merge_commit", "checks_revision", "checks_state",
    }
    if set(adoption_evidence) != required_evidence:
        raise ActivationFinalizationError("Stage 2 adoption evidence is not closed")
    if (
        adoption_evidence.get("adopted_by") != "@Thorncrag"
        or adoption_evidence.get("merge_commit") != canonical_revision
        or adoption_evidence.get("checks_revision") != adoption_evidence.get("reviewed_head")
        or adoption_evidence.get("checks_state") != "success"
    ):
        raise ActivationFinalizationError("Stage 2 adoption evidence is not exact")
    digest = registry._canonical_registry_digest(proposed_registry)
    return {
        "schema_version": 2,
        "verification_type": "component_registry_stage2_adoption_readback",
        "issuer": "component_registry_activation_finalizer",
        "registry_id": proposed_registry["registry_id"],
        "registry_revision": proposed_registry["registry_revision"],
        "registry_sha256": digest,
        "canonical_revision": canonical_revision,
        "design_id": proposed_registry["validation"]["design_id"],
        "design_revision": proposed_registry["validation"]["design_revision"],
        "validation_mode": "live_authority_validation",
        "adoption_evidence": dict(adoption_evidence),
    }


def _build_stage2_production_receipt(
    authority: ProjectPathAuthority,
    proposed_registry: Mapping[str, Any],
    observations: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind the exact merged PR #501 and canonical Registry into one receipt."""
    if authority.mode != "production_canonical":
        raise ActivationFinalizationError(
            "Stage 2 production receipt requires fixed production authority"
        )
    try:
        registry.validate_stage2_registry(proposed_registry, root=authority.repository_root)
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "Stage 2 adopted Registry validation failed"
        ) from exc
    reviewed_head = str(observations.get("reviewed_head_revision") or "")
    merge_commit = str(observations.get("merge_commit_sha") or "")
    remote_main = str(observations.get("remote_main_revision") or "")
    local_revision = str(observations.get("local_revision") or "")
    origin_main = str(observations.get("origin_main_revision") or "")
    base_revision = str(observations.get("pull_request_base_revision") or "")
    revisions = (
        reviewed_head,
        merge_commit,
        remote_main,
        local_revision,
        origin_main,
        base_revision,
    )
    if (
        observations.get("repository") != "Thorncrag/ARRP"
        or observations.get("default_branch") != "main"
        or observations.get("pull_request_number") != STAGE2_PULL_REQUEST_NUMBER
        or observations.get("pull_request_base_repository") != "Thorncrag/ARRP"
        or observations.get("pull_request_base_branch") != "main"
        or observations.get("pull_request_state") != "closed"
        or observations.get("pull_request_merged") is not True
        or observations.get("pull_request_auto_merge") is not None
        or observations.get("merged_by") != "Thorncrag"
        or any(re.fullmatch(r"[0-9a-f]{40}", value) is None for value in revisions)
        or merge_commit != remote_main
        or local_revision != merge_commit
        or origin_main != merge_commit
    ):
        raise ActivationFinalizationError(
            "Stage 2 pull request or repository identity differs"
        )
    parents = _git(
        authority.repository_root,
        "rev-list",
        "--parents",
        "-n",
        "1",
        merge_commit,
    ).split()
    if parents != [merge_commit, base_revision, reviewed_head]:
        raise ActivationFinalizationError(
            "Stage 2 adoption merge parents are not exact"
        )
    checks_completed_at = _validate_required_checks(
        observations,
        reviewed_head=reviewed_head,
    )
    merged_time = _exact_timestamp(observations.get("merged_at"), "Stage 2 merge")
    verified_time = _exact_timestamp(
        observations.get("verified_at"),
        "Stage 2 verification",
    )
    if not checks_completed_at <= merged_time <= verified_time:
        raise ActivationFinalizationError("Stage 2 adoption chronology is invalid")
    reviewed_registry = observations.get("reviewed_registry")
    remote_registry = observations.get("remote_registry")
    if (
        not isinstance(reviewed_registry, Mapping)
        or not isinstance(remote_registry, Mapping)
        or registry.canonical_json(reviewed_registry)
        != registry.canonical_json(proposed_registry)
        or registry.canonical_json(remote_registry)
        != registry.canonical_json(proposed_registry)
    ):
        raise ActivationFinalizationError(
            "Stage 2 remote Registry differs from the adopted authority"
        )
    receipt = _build_stage2_synthetic_receipt(
        proposed_registry,
        canonical_revision=merge_commit,
        adoption_evidence={
            "adopted_by": "@Thorncrag",
            "adopted_at": str(observations["merged_at"]),
            "pull_request": (
                f"github-review:Thorncrag/ARRP#{STAGE2_PULL_REQUEST_NUMBER}"
            ),
            "base_revision": base_revision,
            "reviewed_head": reviewed_head,
            "merge_commit": merge_commit,
            "checks_revision": reviewed_head,
            "checks_state": "success",
        },
    )
    try:
        schema = registry._read_json(
            authority.repository_root
            / "framework"
            / "component-registry.schema.json"
        )
        registry._validate_stage2_adoption_readback_schema(
            receipt,
            schema=schema,
        )
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "Stage 2 adoption receipt failed its closed schema"
        ) from exc
    return receipt


def select_component_registry_receipt(
    tracked_registry: Mapping[str, Any],
    receipts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Select only evidence bound to the exact tracked Registry bytes.

    Both Stage 1 and Stage 2 receipts may remain preserved. Selection follows
    the tracked Registry revision and digest, so a verified revert selects the
    preserved Stage 1 evidence without deleting or rewriting either receipt.
    """
    digest = registry._canonical_registry_digest(tracked_registry)
    if tracked_registry.get("schema_version") == 2:
        matches = [
            receipt for receipt in receipts
            if receipt.get("verification_type") == "component_registry_stage2_adoption_readback"
            and receipt.get("registry_revision") == 2
            and receipt.get("registry_sha256") == digest
            and receipt.get("design_id") == registry.STAGE2_DESIGN_ID
            and receipt.get("design_revision") == registry.STAGE2_DESIGN_REVISION
            and receipt.get("validation_mode") == "live_authority_validation"
        ]
        selected_mode = "live_authority_validation"
    elif tracked_registry.get("schema_version") == 1:
        matches = [
            receipt for receipt in receipts
            if receipt.get("verification_type") == "component_registry_activation_readback"
            and receipt.get("registry_sha256") == digest
        ]
        selected_mode = "active_component_registry"
    else:
        raise ActivationFinalizationError("tracked Registry revision is unsupported")
    if len(matches) != 1:
        raise ActivationFinalizationError("exactly one digest-bound Registry receipt is required")
    return {
        "validation_mode": selected_mode,
        "registry_sha256": digest,
        "receipt": copy.deepcopy(dict(matches[0])),
    }


def verify_stage2_fixture_and_write(
    path_authority: ProjectPathAuthority,
    proposed_registry: Mapping[str, Any],
    *,
    canonical_revision: str,
    adoption_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Exercise Stage 2 receipt construction only inside a contained fixture."""
    if path_authority.mode != "fixture":
        raise ActivationFinalizationError("Stage 2 verifier requires fixture authority")
    try:
        registry.validate_stage2_registry(
            proposed_registry,
            root=path_authority.repository_root,
            verify_repository_coverage=False,
            verify_source_bindings=False,
            verify_migration_residuals=False,
        )
    except registry.RegistryError as exc:
        raise ActivationFinalizationError("fixture Stage 2 Registry validation failed") from exc
    receipt = _build_stage2_synthetic_receipt(
        proposed_registry,
        canonical_revision=canonical_revision,
        adoption_evidence=adoption_evidence,
    )
    try:
        receipt_schema = registry._read_json(
            registry.ROOT
            / "framework"
            / "component-registry.schema.json"
        )
        registry._validate_against_schema(
            receipt,
            receipt_schema["$defs"]["componentRegistryStage2AdoptionReadback"],
            receipt_schema,
        )
    except (KeyError, TypeError, registry.RegistryError) as exc:
        raise ActivationFinalizationError(
            "fixture Stage 2 receipt failed its closed schema"
        ) from exc
    path = _write_fixed_receipt(path_authority, receipt)
    try:
        metadata = path.lstat()
        readback = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ActivationFinalizationError("Stage 2 fixture receipt readback failed") from exc
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o600
        or readback != receipt
        or path.name != f"{receipt['registry_sha256']}.json"
    ):
        raise ActivationFinalizationError("Stage 2 fixture receipt identity is invalid")
    selected = select_component_registry_receipt(proposed_registry, [receipt])
    if selected["validation_mode"] != "live_authority_validation":
        raise ActivationFinalizationError("Stage 2 fixture receipt was not selected")
    return {
        "created": True,
        "registry_revision": 2,
        "registry_sha256": receipt["registry_sha256"],
        "canonical_revision": canonical_revision,
        "validation_mode": selected["validation_mode"],
        "receipt_path": str(path.relative_to(path_authority.state_root)),
    }


def _collect_stage3_authority_observations(
    authority: ProjectPathAuthority,
) -> dict[str, Any]:
    """Collect one coherent exact-main observation for the Stage 3 merge."""

    if authority.mode != "production_canonical":
        raise ActivationFinalizationError(
            "Stage 3 authority observation requires fixed production authority"
        )
    repository_start = _run_json("gh", "api", "repos/Thorncrag/ARRP")
    branch_start = _run_json("gh", "api", "repos/Thorncrag/ARRP/branches/main")
    if not isinstance(repository_start, Mapping) or not isinstance(branch_start, Mapping):
        raise ActivationFinalizationError("Stage 3 repository observation is malformed")
    remote_main = str(branch_start.get("commit", {}).get("sha") or "")
    pull_request = _pull_request_for_merge_commit(remote_main)
    effective_rules = _collect_effective_main_rules()
    checks = _collect_pull_request_checks(
        pull_request,
        branch=branch_start,
        effective_rules=effective_rules["effective_rules"],
    )
    reviewed_head = str(pull_request.get("head", {}).get("sha") or "")
    reviewed_registry = _run_json(
        "gh", "api", "-H", "Accept: application/vnd.github.raw+json",
        "repos/Thorncrag/ARRP/contents/"
        f"{registry.CANONICAL_REGISTRY_PATH}?ref={reviewed_head}",
    )
    remote_registry = _run_json(
        "gh", "api", "-H", "Accept: application/vnd.github.raw+json",
        "repos/Thorncrag/ARRP/contents/"
        f"{registry.CANONICAL_REGISTRY_PATH}?ref={remote_main}",
    )
    repository_end = _run_json("gh", "api", "repos/Thorncrag/ARRP")
    branch_end = _run_json("gh", "api", "repos/Thorncrag/ARRP/branches/main")
    if (
        not isinstance(repository_end, Mapping)
        or not isinstance(branch_end, Mapping)
        or repository_end.get("id") != repository_start.get("id")
        or repository_end.get("node_id") != repository_start.get("node_id")
        or repository_end.get("full_name") != repository_start.get("full_name")
        or branch_end.get("commit", {}).get("sha") != remote_main
    ):
        raise ActivationFinalizationError(
            "remote repository moved during Stage 3 authority observation"
        )
    return {
        "repository": repository_start,
        "remote_main_revision": remote_main,
        "pull_request": pull_request,
        "checks": checks,
        "reviewed_registry": reviewed_registry,
        "remote_registry": remote_registry,
        "local_revision": _git(authority.repository_root, "rev-parse", "HEAD"),
        "origin_main_revision": _git(
            authority.repository_root,
            "rev-parse",
            "refs/remotes/origin/main",
        ),
        "verified_at": _stage3_verified_at(),
    }


def _stage3_verified_at() -> str:
    """Return the closed Stage 3 receipt timestamp at whole-second precision."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _stage3_authority_receipt_payload(
    stage3_registry: Mapping[str, Any],
    *,
    repository_evidence: Mapping[str, Any],
    canonical_revision: str,
    merge_evidence: Mapping[str, Any],
    verified_at: str,
) -> dict[str, Any]:
    model = registry._validate_stage2_authority_digest_model(stage3_registry)
    receipt = {
        "schema_version": 1,
        "verification_type": "component_registry_stage3_authority_readback",
        "issuer": "component_registry_activation_finalizer",
        "repository": {
            "id": repository_evidence["id"],
            "node_id": repository_evidence["node_id"],
            "full_name": "Thorncrag/ARRP",
            "default_branch": "main",
        },
        "registry_id": stage3_registry["registry_id"],
        "registry_revision": stage3_registry["registry_revision"],
        "registry_sha256": registry._canonical_registry_digest(stage3_registry),
        "authority_sha256": registry._stage2_authority_digest(stage3_registry),
        "authority_protocol": model["protocol"],
        "authority_generation": model["generation"],
        "canonical_revision": canonical_revision,
        "design_contract": {
            "design_id": registry.STAGE3_DESIGN_ID,
            "design_revision": registry.STAGE3_DESIGN_REVISION,
            "contract_revision": 1,
            "external_evidence_id": registry.STAGE3_EXTERNAL_EVIDENCE_ID,
            "contract_sha256": registry.STAGE3_CONTRACT_SHA256,
        },
        "validation_mode": "live_authority_validation",
        "merge_evidence": dict(merge_evidence),
        "verified_at": verified_at,
    }
    try:
        schema = registry._read_json(
            registry.ROOT / "framework" / "component-registry.schema.json"
        )
        registry._validate_stage3_authority_readback_schema(receipt, schema=schema)
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "Stage 3 authority receipt failed its closed schema"
        ) from exc
    return receipt


def _build_stage3_authority_receipt(
    authority: ProjectPathAuthority,
    stage3_registry: Mapping[str, Any],
    observations: Mapping[str, Any],
) -> dict[str, Any]:
    if authority.mode != "production_canonical":
        raise ActivationFinalizationError(
            "Stage 3 authority receipt requires fixed production authority"
        )
    try:
        registry.validate_stage3_registry(stage3_registry, root=authority.repository_root)
    except registry.RegistryError as exc:
        raise ActivationFinalizationError("Stage 3 Registry validation failed") from exc
    repository_evidence = observations.get("repository")
    pull_request = observations.get("pull_request")
    remote_main = str(observations.get("remote_main_revision") or "")
    if (
        not isinstance(repository_evidence, Mapping)
        or not isinstance(repository_evidence.get("id"), int)
        or not isinstance(repository_evidence.get("node_id"), str)
        or repository_evidence.get("full_name") != "Thorncrag/ARRP"
        or repository_evidence.get("default_branch") != "main"
        or not isinstance(pull_request, Mapping)
        or observations.get("local_revision") != remote_main
        or observations.get("origin_main_revision") != remote_main
    ):
        raise ActivationFinalizationError("Stage 3 canonical repository identity differs")
    merge = _merge_evidence(authority.repository_root, pull_request, remote_main)
    required_checks = _validated_required_check_evidence(
        observations["checks"],
        reviewed_head=merge["reviewed_head"],
    )
    check_time = max(
        _exact_timestamp(item["completed_at"], "Stage 3 required check")
        for item in required_checks
    )
    merged_at = _exact_timestamp(merge["merged_at"], "Stage 3 merge")
    verified_at = _exact_timestamp(observations.get("verified_at"), "Stage 3 verification")
    if check_time > merged_at or merged_at > verified_at:
        raise ActivationFinalizationError("Stage 3 authority chronology differs")
    reviewed_registry = observations.get("reviewed_registry")
    remote_registry = observations.get("remote_registry")
    if (
        not isinstance(reviewed_registry, Mapping)
        or registry.canonical_json(reviewed_registry) != registry.canonical_json(stage3_registry)
        or not isinstance(remote_registry, Mapping)
        or registry.canonical_json(remote_registry) != registry.canonical_json(stage3_registry)
    ):
        raise ActivationFinalizationError("Stage 3 Registry merge bytes differ")
    return _stage3_authority_receipt_payload(
        stage3_registry,
        repository_evidence=repository_evidence,
        canonical_revision=remote_main,
        merge_evidence={**merge, "approved_by": "@Thorncrag", "required_checks": required_checks},
        verified_at=str(observations["verified_at"]),
    )


def verify_stage3_fixture_and_write(
    path_authority: ProjectPathAuthority,
    stage3_registry: Mapping[str, Any],
    *,
    canonical_revision: str,
    merge_evidence: Mapping[str, Any],
    verified_at: str,
) -> dict[str, Any]:
    """Exercise the Stage 3 closed receipt only in contained fixtures."""

    if path_authority.mode != "fixture":
        raise ActivationFinalizationError("Stage 3 fixture requires fixture authority")
    try:
        registry.validate_stage3_registry(stage3_registry, root=registry.ROOT)
    except registry.RegistryError as exc:
        raise ActivationFinalizationError("Stage 3 fixture Registry is invalid") from exc
    receipt = _stage3_authority_receipt_payload(
        stage3_registry,
        repository_evidence={
            "id": 1,
            "node_id": "fixture-repository",
        },
        canonical_revision=canonical_revision,
        merge_evidence=merge_evidence,
        verified_at=verified_at,
    )
    path = _write_fixed_receipt(path_authority, receipt)
    return {
        "created": True,
        "registry_revision": 3,
        "registry_sha256": receipt["registry_sha256"],
        "authority_sha256": receipt["authority_sha256"],
        "canonical_revision": canonical_revision,
        "validation_mode": "live_authority_validation",
        "receipt_path": str(path.relative_to(path_authority.state_root)),
    }


def finalize_activation() -> dict[str, Any]:
    """Finalize one active registry using only fixed production authorities."""

    try:
        authority = ProjectPathAuthority.production()
        registry_path = authority.repository_path(
            registry.CANONICAL_REGISTRY_PATH,
            required=True,
        )
    except PathAuthorityError as exc:
        raise ActivationFinalizationError(
            "fixed production authority is unavailable"
        ) from exc
    active_registry = registry._read_json(registry_path)
    if active_registry.get("schema_version") == 3:
        try:
            configuration_view = (
                registry.load_component_registry_configuration_routing_view()
            )
        except registry.RegistryError as exc:
            raise ActivationFinalizationError(
                "Stage 3 adopted configuration validation failed before observation"
            ) from exc
        if (
            configuration_view.get("validation_mode")
            != "adopted_configuration_validation"
            or configuration_view.get("authoritative") is not False
            or configuration_view.get("executable") is not False
            or configuration_view.get("source_bytes_current") is not True
        ):
            raise ActivationFinalizationError(
                "Stage 3 adopted configuration posture is invalid"
            )
        observations = _collect_stage3_authority_observations(authority)
        receipt = _build_stage3_authority_receipt(
            authority,
            active_registry,
            observations,
        )
        _write_fixed_receipt(authority, receipt)
        try:
            live_view = registry.load_validated_component_registry_routing_view(
                authority
            )
        except registry.RegistryError as exc:
            raise ActivationFinalizationError(
                "Stage 3 post-publication authority readback failed"
            ) from exc
        if (
            live_view.get("validation_mode") != "live_authority_validation"
            or live_view.get("authoritative") is not True
            or live_view.get("executable") is not False
            or live_view.get("live_authority_verified") is not True
            or live_view.get("activation_receipt_consulted") is not True
            or live_view.get("authority_effective") is not True
            or live_view.get("source_bytes_current") is not True
            or live_view.get("receipt_trusted") is not True
            or live_view.get("runtime_live") != "not_checked"
        ):
            raise ActivationFinalizationError(
                "Stage 3 authority posture is invalid"
            )
        return {
            "complete": True,
            "registry_sha256": receipt["registry_sha256"],
            "authority_sha256": receipt["authority_sha256"],
            "canonical_revision": receipt["canonical_revision"],
            "verification_state": "live_authority_validation",
            "runtime_live": "not_checked",
        }
    if active_registry.get("schema_version") == 2:
        try:
            configuration_view = (
                registry.load_component_registry_configuration_routing_view()
            )
        except registry.RegistryError as exc:
            raise ActivationFinalizationError(
                "Stage 2 adopted configuration validation failed before observation"
            ) from exc
        if (
            configuration_view.get("validation_mode")
            != "adopted_configuration_validation"
            or configuration_view.get("authoritative") is not False
            or configuration_view.get("executable") is not False
        ):
            raise ActivationFinalizationError(
                "Stage 2 adopted configuration posture is invalid"
            )
        if "authority_digest_model" in active_registry:
            observations = _collect_stage2_authority_observations(
                authority,
                active_registry,
            )
            receipt = _build_stage2_authority_receipt(
                authority,
                active_registry,
                observations,
            )
            _path, created = _write_stage2_authority_receipt(
                authority,
                receipt,
            )
            try:
                active_view = (
                    verify_stage2_authority_v1_online_eligibility(
                        authority,
                        active_registry,
                    )
                )
            except ActivationFinalizationError as exc:
                raise ActivationFinalizationError(
                    "Stage 2 authority post-publication readback failed"
                ) from exc
            if (
                active_view.get("validation_mode")
                != "online_governed_eligibility"
                or active_view.get("authoritative") is not True
                or active_view.get("executable") is not False
                or active_view.get("activation_receipt_consulted") is not True
                or active_view.get("runtime_live") != "not_checked"
                or active_view.get("authority_effective") is not True
                or active_view.get("source_revision_authorized") is not True
                or active_view.get("source_bytes_current") is not True
                or active_view.get("canonical_history_confirmed") is not True
                or active_view.get("receipt_trusted") is not True
            ):
                raise ActivationFinalizationError(
                    "Stage 2 authority live posture is invalid"
                )
            return {
                "complete": True,
                "created": created,
                "authority_sha256": receipt["authority_sha256"],
                "generation": receipt["generation"],
                "issuance_revision": receipt["issuance_revision"],
                "verification_state": "online_governed_eligibility",
                "runtime_live": "not_checked",
            }
        observations = _collect_stage2_authenticated_observations(authority)
        receipt = _build_stage2_production_receipt(
            authority,
            active_registry,
            observations,
        )
        _write_fixed_receipt(authority, receipt)
        try:
            active_view = registry.load_validated_component_registry_routing_view(
                authority
            )
        except registry.RegistryError as exc:
            raise ActivationFinalizationError(
                "Stage 2 post-publication production readback failed"
            ) from exc
        if (
            active_view.get("validation_mode") != "live_authority_validation"
            or active_view.get("authoritative") is not True
            or active_view.get("executable") is not True
            or active_view.get("live_authority_verified") is not True
            or active_view.get("activation_receipt_consulted") is not True
        ):
            raise ActivationFinalizationError(
                "Stage 2 post-publication live posture is invalid"
            )
        return {
            "complete": True,
            "registry_sha256": receipt["registry_sha256"],
            "verification_state": "live_authority_validation",
        }
    try:
        configuration_view = (
            registry.load_component_registry_configuration_routing_view()
        )
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "active configuration validation failed before observation"
        ) from exc
    if (
        active_registry.get("status") != "active"
        or configuration_view.get("validation_mode")
        != "active_configuration_validation_only"
        or configuration_view.get("authoritative") is not False
        or configuration_view.get("executable") is not False
    ):
        raise ActivationFinalizationError(
            "Component Registry active configuration posture is invalid"
        )
    observations = _collect_authenticated_observations(
        authority,
        active_registry,
    )
    receipt = _build_receipt(authority, active_registry, observations)
    _write_fixed_receipt(authority, receipt)
    try:
        active_view = registry.load_validated_component_registry_routing_view(
            authority
        )
    except registry.RegistryError as exc:
        raise ActivationFinalizationError(
            "post-publication active production readback failed"
        ) from exc
    if (
        active_view.get("validation_mode") != "active_component_registry"
        or active_view.get("authoritative") is not True
        or active_view.get("executable") is not True
        or active_view.get("activation_receipt_consulted") is not True
    ):
        raise ActivationFinalizationError(
            "post-publication active production posture is invalid"
        )
    return {
        "complete": True,
        "registry_sha256": receipt["registry_sha256"],
        "verification_state": receipt["verification_state"],
    }


def main(arguments: list[str] | None = None) -> int:
    supplied = list(arguments) if arguments is not None else list(os.sys.argv[1:])
    if supplied:
        print("activation finalization error: arguments are not accepted")
        return 2
    try:
        result = finalize_activation()
    except ActivationFinalizationError as exc:
        print(f"activation finalization error: {exc}")
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
