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
            / "standards"
            / "automation"
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
            / "standards"
            / "automation"
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
        "adopted_by", "adopted_at", "pull_request", "reviewed_head",
        "merge_commit", "checks_revision", "checks_state",
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
            / "standards"
            / "automation"
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
