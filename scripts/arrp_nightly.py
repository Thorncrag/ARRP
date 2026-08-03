#!/usr/bin/env python3
"""Reviewed local-first transaction runner for ARRP.

The runner owns the deterministic stages, sealed Elim boundary, local
validation and classification, exact-head GitHub App publication, semantic
action brokerage, Pages verification, canonical-main reconciliation, and
typed host status used by the P6 launchd service.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import errno
import fcntl
import hashlib
import json
import os
import re
import signal
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence
from zoneinfo import ZoneInfo

try:
    from repository_gates import (
        atomic_write as write_repository_gate_snapshot,
        produce_repository_gate_snapshot,
        read_json as read_repository_gate_snapshot,
    )
except ModuleNotFoundError:
    from scripts.repository_gates import (
        atomic_write as write_repository_gate_snapshot,
        produce_repository_gate_snapshot,
        read_json as read_repository_gate_snapshot,
    )

try:
    from operational_incidents import (
        IncidentContractError,
        record_incident_occurrence,
        record_incident_reports,
        reconcile_failure_spool,
        spool_failure_incident,
        validate_incident_report,
    )
except ModuleNotFoundError:
    from scripts.operational_incidents import (
        IncidentContractError,
        record_incident_occurrence,
        record_incident_reports,
        reconcile_failure_spool,
        spool_failure_incident,
        validate_incident_report,
    )

try:
    from github_disclosure_gate import (
        DisclosureBlocked,
        OutboundArtifact,
        artifact_from_text,
        evaluate_outbound_bundle,
        require_outbound_bundle,
    )
except ModuleNotFoundError:
    from scripts.github_disclosure_gate import (
        DisclosureBlocked,
        OutboundArtifact,
        artifact_from_text,
        evaluate_outbound_bundle,
        require_outbound_bundle,
    )

try:
    from transaction_lifecycle import (
        TransactionLifecycleError,
        current_transaction_states,
        mark_abandoned_transactions,
        read_events as read_transaction_events,
        start_transaction,
        transition_transaction,
    )
except ModuleNotFoundError:
    from scripts.transaction_lifecycle import (
        TransactionLifecycleError,
        current_transaction_states,
        mark_abandoned_transactions,
        read_events as read_transaction_events,
        start_transaction,
        transition_transaction,
    )

try:
    from component_registry import (
        RegistryError as ComponentRegistryError,
        ROUTING_PREDECESSOR_PATHS,
        load_fixture_component_registry_routing_view,
        load_validated_component_registry_routing_view,
    )
except ModuleNotFoundError:
    from scripts.component_registry import (
        RegistryError as ComponentRegistryError,
        ROUTING_PREDECESSOR_PATHS,
        load_fixture_component_registry_routing_view,
        load_validated_component_registry_routing_view,
    )

try:
    from arrp_context import (
        ContextError as RoutingContextError,
        load_route_manifest,
    )
except ModuleNotFoundError:
    from scripts.arrp_context import (
        ContextError as RoutingContextError,
        load_route_manifest,
    )

try:
    from elim_execution import (
        ContextError as ElimContextError,
        reconstruct_gap_obligation_state,
    )
except ModuleNotFoundError:
    from scripts.elim_execution import (
        ContextError as ElimContextError,
        reconstruct_gap_obligation_state,
    )

try:
    from path_authority import PathAuthorityError, ProjectPathAuthority
except ModuleNotFoundError:
    from scripts.path_authority import PathAuthorityError, ProjectPathAuthority

SCHEMA_VERSION = "1.0"
APPROVED_ORIGINS = frozenset(
    {
        "https://github.com/Thorncrag/ARRP.git",
        "git@github.com:Thorncrag/ARRP.git",
    }
)
BRANCH_PREFIX = "automation/nightly-"
CHECKPOINT_MESSAGE = "Checkpoint Benjamin's local ARRP work before nightly automation"
STATUS_FIELDS = (
    "schema_version",
    "run_id",
    "trigger",
    "scheduled_for",
    "started_at",
    "updated_at",
    "completed_at",
    "status",
    "control_state",
    "stage",
    "canonical_path",
    "starting_branch",
    "starting_local_head",
    "fetched_origin_main",
    "preexisting_path_manifest_sha256",
    "checkpoint_commit",
    "nightly_branch",
    "worktree_path",
    "runtime_commit",
    "elim_unit",
    "elim_outcome",
    "validation_summary",
    "classification",
    "pull_request",
    "expected_pr_head",
    "merge_commit",
    "project_sync",
    "pages_workflow_run",
    "pages_conclusion",
    "preserved_paths",
    "failure_class",
    "failure_reason",
    "exact_next_action",
)
PROTECTED_PREFIXES = (
    ".github/",
    "scripts/",
    "tests/",
    "framework/standards/",
    "framework/project/",
    "participate/",
    "website/",
)
PROTECTED_EXACT = frozenset(
    {
        "AGENTS.md",
        "pyproject.toml",
        "package.json",
        "package-lock.json",
        "framework/FRAMEWORK.md",
        "framework/AGENT_OPERATING_RULES.md",
        "framework/component-registry.json",
        *(
            specification["archived_path"]
            for specification in ROUTING_PREDECESSOR_PATHS.values()
        ),
        "framework/project/interfaces/project-console/README.md",
        "framework/project/interfaces/project-console/project-console.html",
        "framework/project/interfaces/project-console/app.js",
        "framework/project/interfaces/project-console/capacity.js",
        "framework/project/interfaces/project-console/component-registry.js",
        "framework/project/interfaces/project-console/styles.css",
    }
)
RECOGNIZED_NEW_PREFIXES = (
    "areas/",
    "legislation/",
    "topics/",
    "research/",
    "inventory/",
    "framework/logs/",
)
PRIVATE_NAMES = frozenset({".env", ".env.local", "PAUSED"})
RUNTIME_FILES = (
    "scripts/arrp_nightly.py",
    "scripts/arrp_bootstrap.py",
    "scripts/arrp_context.py",
    "scripts/component_registry.py",
    "scripts/transaction_lifecycle.py",
    "scripts/path_authority.py",
    "scripts/github_disclosure_gate.py",
    "scripts/operational_incidents.py",
    "scripts/repository_gates.py",
    "scripts/source_monitor_recommendations.py",
    "scripts/run_coordinator.py",
    "scripts/build_elim_work_queue.py",
    "scripts/select_elim_context_route.py",
    "scripts/build_elim_context.py",
    "scripts/elim_execution.py",
    "scripts/check_codex_usage_reserve.py",
    "scripts/console_data_contracts.py",
    "framework/project/github/disclosure-policy.json",
)
SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
LOCAL_STAGE_ORDER = (
    "case-monitor-bot",
    "presidential-directives-bot",
    "source-checker-bot",
    "public-intake",
    "project-console-progress-bot",
    "project-integrity-bot",
)
SEALED_DISABLED_FEATURES = (
    "apps",
    "browser_use",
    "computer_use",
    "goals",
    "hooks",
    "image_generation",
    "memories",
    "multi_agent",
    "plugin_sharing",
    "plugins",
    "remote_plugin",
    "skill_mcp_dependency_install",
    "skill_search",
    "tool_suggest",
    "workspace_dependencies",
)
ELIM_ENVIRONMENT_ALLOWLIST = frozenset(
    {
        "HOME",
        "USER",
        "LOGNAME",
        "PATH",
        "TMPDIR",
        "LANG",
        "LC_ALL",
        "CODEX_HOME",
        "CODEX_SQLITE_HOME",
        "ARRP_TRANSACTION_WORKTREE",
        "ARRP_RUN_DIR",
        "ARRP_ELIM_MODEL",
    }
)
SECRET_DETECTORS = (
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
        "credential-assignment",
        re.compile(
            rb"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)"
            rb"\s*[:=]\s*['\"]?[A-Za-z0-9/+_.-]{12,}"
        ),
    ),
)
ORDINARY_NEW_SUFFIXES = frozenset(
    {".csv", ".json", ".jsonl", ".js", ".md", ".txt", ".yaml", ".yml"}
)
GITHUB_API_ROOT = "https://api.github.com"
GITHUB_REPOSITORY = "Thorncrag/ARRP"
GITHUB_OWNER = "Thorncrag"
GITHUB_APP_KEYCHAIN_SERVICE = "org.thorncrag.arrp.github-app.v1"
GITHUB_APP_KEYCHAIN_ACCOUNT = "ARRP Automation private key"
GITHUB_PROJECT_KEYCHAIN_SERVICE = "org.thorncrag.arrp.github-project"
GITHUB_PROJECT_KEYCHAIN_ACCOUNT = "ARRP Project token"
REQUIRED_CHECKS = frozenset({"ARRP Validation", "CodeQL"})
P5_SUPERVISED_PHASE = "P5_SUPERVISED_END_TO_END_PROOF"
P5_SUPERVISED_AUTHORIZATION = "BENJAMIN_APPROVED_P5_LIVE_FIXTURE"
PRODUCTION_TIME_ZONE = ZoneInfo("America/New_York")
PRODUCTION_SCHEDULE_HOUR = 2
PRODUCTION_CODEX = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
BROKER_OPERATION_TYPES = frozenset(
    {
        "read_state",
        "set_project_field",
        "update_issue_wrapper",
        "post_discussion_reply",
    }
)
RUNNER_OWNED_BROKER_OPERATIONS = frozenset({"nightly_pull_request"})
BROKER_INTENT_FIELDS = frozenset(
    {
        "operation_type",
        "repository",
        "target_node_or_number",
        "source_revision",
        "authority_record",
        "expected_old_state",
        "new_state_or_content",
        "idempotency_key",
        "privacy_class",
        "human_reserved",
        "rollback_or_correction",
        "readback_contract",
    }
)
BROKER_TARGET_FIELDS = {
    "set_project_field": frozenset({"project_id", "item_id", "field_id"}),
    "update_issue_wrapper": frozenset({"issue_number", "marker"}),
    "post_discussion_reply": frozenset(
        {"discussion_number", "reply_to_comment_id"}
    ),
}
BROKER_READBACK_CONTRACTS = {
    "read_state": "exact_state_snapshot",
    "set_project_field": "exact_project_field_value",
    "update_issue_wrapper": "exact_issue_body",
    "post_discussion_reply": "exactly_one_discussion_reply",
}
BROKER_NODE_ID = re.compile(r"^[A-Za-z0-9_-]{4,128}$")
BROKER_WRAPPER_MARKER = re.compile(
    r"^<!-- ARRP-WRAPPER:[A-Za-z0-9._:-]{1,96} -->$"
)
APP_REPOSITORY_PERMISSIONS = {
    "actions": "read",
    "checks": "read",
    "statuses": "read",
    "contents": "write",
    "discussions": "write",
    "issues": "write",
    "metadata": "read",
    "pull_requests": "write",
}
EXPECTED_TRACKED_EXECUTABLES = frozenset(
    {
        "scripts/bootstrap_local_tools.sh",
        "scripts/build_project_console.py",
        "scripts/congress_api_smoke_test.py",
    }
)


class TransactionError(RuntimeError):
    """A fail-closed local transaction error."""


class GitError(TransactionError):
    """A Git command failed without exposing credential-bearing environment."""

    def __init__(self, args: Sequence[str], result: subprocess.CompletedProcess[bytes]):
        command = "git " + " ".join(args)
        stderr = result.stderr.decode("utf-8", "replace").strip()
        super().__init__(f"{command} failed ({result.returncode}): {stderr}")
        self.args_run = tuple(args)
        self.returncode = result.returncode


class GitHubBrokerError(TransactionError):
    """A fail-closed GitHub or semantic-broker error with redacted diagnostics."""


class DisclosurePreventionError(GitHubBrokerError):
    """A sanitized prevented-disclosure near miss."""


class SensitiveValue:
    """A non-serializable secret wrapper whose display is always redacted."""

    __slots__ = ("_value",)

    def __init__(self, value: str):
        if not value:
            raise GitHubBrokerError("credential lookup returned an empty value")
        self._value = value

    def reveal(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "<redacted>"

    __str__ = __repr__


@dataclass(frozen=True)
class GitHubAppIdentity:
    app_id: int
    installation_id: int
    repository_id: int

    @classmethod
    def from_json(cls, path: Path) -> "GitHubAppIdentity":
        value = read_json_object(path)
        exact = {"app_id", "installation_id", "repository_id", "repository"}
        if set(value) != exact or value["repository"] != GITHUB_REPOSITORY:
            raise GitHubBrokerError("GitHub App identity file has unexpected fields")
        try:
            identity = cls(
                app_id=int(value["app_id"]),
                installation_id=int(value["installation_id"]),
                repository_id=int(value["repository_id"]),
            )
        except (TypeError, ValueError) as error:
            raise GitHubBrokerError("GitHub App identity values must be integers") from error
        if min(identity.app_id, identity.installation_id, identity.repository_id) <= 0:
            raise GitHubBrokerError("GitHub App identity values must be positive")
        return identity


@dataclass(frozen=True)
class PathRecord:
    path: str
    status: str
    old_path: str | None
    mode: int | None
    sha256: str | None
    classification: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "status": self.status,
            "old_path": self.old_path,
            "mode": self.mode,
            "sha256": self.sha256,
            "classification": self.classification,
        }


@dataclass(frozen=True)
class IndexRecord:
    path: str
    mode: str | None
    blob: str | None
    status: str
    classification: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "mode": self.mode,
            "blob": self.blob,
            "status": self.status,
            "classification": self.classification,
        }


@dataclass(frozen=True)
class RunnerConfig:
    canonical_path: Path
    state_root: Path
    fixture_root: Path | None = None
    trigger: str = "manual"
    scheduled_for: str | None = None
    runtime_files: tuple[str, ...] = field(default_factory=lambda: RUNTIME_FILES)
    console_projection: Path | None = None
    supervised_live: bool = False
    runtime_commit: str | None = None
    attempt_group_id: str | None = None
    retry_attempt_number: int = 1
    retry_authorization: Mapping[str, str] | None = None
    retry_mode: str | None = None

    def validate(self) -> None:
        canonical = self.canonical_path.resolve()
        state = self.state_root.resolve()
        if self.fixture_root is None:
            expected = Path("/Users/benjaminsmith/Automation Workspaces/ARRP")
            if canonical != expected:
                raise TransactionError("non-fixture canonical path is not the approved ARRP path")
            if state != Path.home() / "Library/Application Support/ARRP":
                raise TransactionError("non-fixture state root is not the approved ARRP state root")
            if self.supervised_live and self.trigger != "manual-p5-supervised":
                raise TransactionError("live supervision requires the exact P5 manual trigger")
            if self.trigger in {"manual", "scheduled"}:
                if (
                    self.runtime_commit is None
                    or re.fullmatch(r"[0-9a-f]{40}", self.runtime_commit) is None
                ):
                    raise TransactionError(
                        "production execution requires an exact runtime commit"
                    )
        else:
            fixture = self.fixture_root.resolve()
            if not _is_within(canonical, fixture) or not _is_within(state, fixture):
                raise TransactionError("fixture repository and state root must stay inside fixture root")
            if canonical == Path("/Users/benjaminsmith/Automation Workspaces/ARRP"):
                raise TransactionError("fixture mode cannot target Benjamin's canonical repository")
            if self.supervised_live:
                raise TransactionError("fixture mode cannot claim live supervision")
        if self.retry_attempt_number < 1:
            raise TransactionError("retry attempt number must be positive")
        if self.retry_attempt_number == 1 and self.retry_authorization is not None:
            raise TransactionError("primary transaction cannot claim retry authorization")
        if self.retry_attempt_number > 1:
            if self.trigger != "manual-retry" or self.retry_authorization is None:
                raise TransactionError(
                    "linked retry requires the exact manual-retry trigger and authorization"
                )
            if self.retry_mode not in {"deterministic-recovery", None}:
                raise TransactionError("linked retry has an unsupported retry mode")


@dataclass(frozen=True)
class TransactionResult:
    run_id: str
    status: str
    branch: str | None
    checkpoint_commit: str | None
    worktree_path: str | None
    fetched_origin_main: str | None
    protected_paths: tuple[str, ...] = ()
    failure_class: str | None = None


@dataclass(frozen=True)
class LocalStageSpec:
    identifier: str
    cadence_hours: int | None
    failure_class: str
    command: tuple[str, ...]
    outputs: tuple[str, ...]


@dataclass(frozen=True)
class LocalStageResult:
    identifier: str
    status: str
    reason: str
    returncode: int | None
    envelope: str | None


@dataclass(frozen=True)
class ValidationSpec:
    identifier: str
    command: tuple[str, ...]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: datetime | None = None) -> str:
    return (value or utc_now()).isoformat().replace("+00:00", "Z")


def make_run_id(value: datetime | None = None) -> str:
    return (value or utc_now()).strftime("arrp-%Y%m%dT%H%M%SZ")


def scheduled_slot(value: datetime | None = None) -> str:
    """Return the most recent 02:00 America/New_York slot for due evaluation."""

    current = (value or utc_now()).astimezone(PRODUCTION_TIME_ZONE)
    candidate = current.replace(
        hour=PRODUCTION_SCHEDULE_HOUR,
        minute=0,
        second=0,
        microsecond=0,
    )
    if current < candidate:
        candidate = (candidate - timedelta(days=1)).astimezone(PRODUCTION_TIME_ZONE)
    return candidate.isoformat()


def verify_executed_runtime(
    state_root: Path,
    runtime_commit: str,
    *,
    executed_script: Path | None = None,
) -> Path:
    """Prove this runner is the exact hash-bound script from the reviewed snapshot."""

    if re.fullmatch(r"[0-9a-f]{40}", runtime_commit) is None:
        raise TransactionError("runtime commit must be a 40-character Git hash")
    runtime = (state_root / "runtime" / runtime_commit).resolve()
    script = (executed_script or Path(__file__)).resolve()
    expected = (runtime / "scripts/arrp_nightly.py").resolve()
    if script != expected:
        raise TransactionError("executed runner is outside the reviewed runtime snapshot")
    manifest_path = runtime / "runtime-manifest.json"
    try:
        manifest = read_json_object(manifest_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        raise TransactionError("reviewed runtime manifest is unavailable") from error
    files = manifest.get("files")
    if (
        manifest.get("source_commit") != runtime_commit
        or not isinstance(files, dict)
        or set(files) != set(RUNTIME_FILES)
    ):
        raise TransactionError("reviewed runtime manifest identity is invalid")
    for relative in RUNTIME_FILES:
        target = (runtime / relative).resolve()
        if not _is_within(target, runtime) or target.is_symlink() or not target.is_file():
            raise TransactionError(f"reviewed runtime entry is unsafe: {relative}")
        info = target.stat()
        if info.st_uid != os.getuid() or bool(stat.S_IMODE(info.st_mode) & 0o077):
            raise TransactionError(f"reviewed runtime mode is unsafe: {relative}")
        expected_hash = files.get(relative)
        if (
            not isinstance(expected_hash, str)
            or file_sha256(target) != expected_hash
        ):
            raise TransactionError(f"reviewed runtime hash mismatch: {relative}")
    return runtime


def ensure_owner_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise TransactionError(f"unsafe state directory ownership or mode: {path}")


def pause_requested(state_root: Path) -> bool:
    """Return true only for a regular owner-only persistent pause marker."""

    path = state_root / "PAUSED"
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    if (
        path.is_symlink()
        or not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.getuid()
        or bool(stat.S_IMODE(info.st_mode) & 0o077)
    ):
        raise TransactionError("PAUSED must be a regular owner-only file")
    return True


def atomic_write_bytes(path: Path, encoded: bytes) -> None:
    ensure_owner_directory(path.parent)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_json(path: Path, value: Any) -> None:
    encoded = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    atomic_write_bytes(path, encoded)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TransactionError(f"JSON value is not an object: {path}")
    return value


def read_owner_text(path: Path, *, label: str, maximum_bytes: int) -> str:
    """Read one bounded owner-only regular file without following symlinks."""

    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError as error:
        raise TransactionError(f"{label} is unavailable") from error
    except OSError as error:
        if error.errno == errno.ELOOP:
            raise TransactionError(f"{label} is unsafe") from error
        raise TransactionError(f"{label} is unreadable") from error
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or bool(stat.S_IMODE(info.st_mode) & 0o077)
            or info.st_size > maximum_bytes
        ):
            raise TransactionError(f"{label} is unsafe")
        content = bytearray()
        while len(content) <= maximum_bytes:
            chunk = os.read(
                descriptor,
                min(64 * 1024, maximum_bytes + 1 - len(content)),
            )
            if not chunk:
                break
            content.extend(chunk)
        if len(content) > maximum_bytes:
            raise TransactionError(f"{label} is unsafe")
    except OSError as error:
        raise TransactionError(f"{label} is unreadable") from error
    finally:
        os.close(descriptor)
    try:
        return bytes(content).decode("utf-8")
    except UnicodeError as error:
        raise TransactionError(f"{label} is unreadable") from error


def reconstruct_owner_gap_obligations(path: Path) -> dict[str, Any]:
    """Reconstruct typed gap state from the fixed owner-local Run Log."""

    try:
        return reconstruct_gap_obligation_state(
            read_owner_text(
                path,
                label="owner-local Elim Run Log",
                maximum_bytes=8 * 1024 * 1024,
            )
        )
    except (ElimContextError, ValueError, TypeError) as error:
        raise TransactionError(
            "owner-local Elim Run Log cannot reconstruct gap obligations"
        ) from error


def structured_failure_detail(path: Path) -> str | None:
    """Return a bounded structured artifact failure without masking its cause."""

    try:
        if not path.is_file() or path.is_symlink():
            return None
        failure = read_json_object(path).get("error")
    except (OSError, ValueError, TransactionError):
        return None
    if isinstance(failure, str) and failure.strip():
        return failure.strip()[:500]
    return None


def read_keychain_secret(service: str, account: str) -> SensitiveValue:
    """Read one dedicated Keychain item without printing or exporting its value."""

    result = subprocess.run(
        ["security", "find-generic-password", "-w", "-s", service, "-a", account],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if result.returncode:
        raise GitHubBrokerError(
            f"Keychain item unavailable for service={service!r}, account={account!r}"
        )
    raw = result.stdout.strip()
    if len(raw) % 2 == 0 and re.fullmatch(r"[0-9A-Fa-f]+", raw):
        try:
            raw = bytes.fromhex(raw).decode("utf-8").strip()
        except (ValueError, UnicodeDecodeError) as error:
            raise GitHubBrokerError("Keychain credential hex readback is invalid") from error
    if "-----BEGIN" in raw:
        blocks = re.findall(
            r"-----BEGIN [A-Z0-9 ]+ PRIVATE KEY-----.*?"
            r"-----END [A-Z0-9 ]+ PRIVATE KEY-----",
            raw,
            re.DOTALL,
        )
        remainder = raw
        for block in blocks:
            remainder = remainder.replace(block, "", 1)
        if not blocks or remainder.strip() or len(set(blocks)) != 1:
            raise GitHubBrokerError("Keychain private-key readback is ambiguous")
        return SensitiveValue(blocks[0] + "\n")
    lines = [line for line in raw.splitlines() if line]
    if not lines or len(set(lines)) != 1:
        raise GitHubBrokerError("Keychain credential readback is ambiguous")
    return SensitiveValue(lines[0])


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_github_app_jwt(
    app_id: int,
    private_key: SensitiveValue,
    *,
    now: int | None = None,
) -> SensitiveValue:
    """Create a ten-minute RS256 App JWT without placing key material in argv."""

    timestamp = int(time.time() if now is None else now)
    header = _base64url(b'{"alg":"RS256","typ":"JWT"}')
    payload = _base64url(
        json.dumps(
            {"iat": timestamp - 60, "exp": timestamp + 540, "iss": str(app_id)},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    read_descriptor, write_descriptor = os.pipe()
    try:
        os.write(write_descriptor, private_key.reveal().encode("utf-8"))
    finally:
        os.close(write_descriptor)
    try:
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", f"/dev/fd/{read_descriptor}"],
            input=signing_input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            pass_fds=(read_descriptor,),
        )
    finally:
        os.close(read_descriptor)
    if result.returncode:
        raise GitHubBrokerError("GitHub App JWT signing failed")
    return SensitiveValue(f"{signing_input.decode('ascii')}.{_base64url(result.stdout)}")


def github_api_request(
    method: str,
    path: str,
    token: SensitiveValue,
    *,
    payload: Mapping[str, Any] | None = None,
    api_root: str = GITHUB_API_ROOT,
) -> Any:
    """Call GitHub with an in-memory authorization header and redacted errors."""

    if not path.startswith("/"):
        raise GitHubBrokerError("GitHub API path must be absolute")
    body = (
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
        if payload is not None
        else None
    )
    request = urllib.request.Request(
        api_root + path,
        data=body,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token.reveal()}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "ARRP-Local-First-Automation",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        diagnostic = error.read(4096).decode("utf-8", "replace")
        if token.reveal() in diagnostic:
            diagnostic = diagnostic.replace(token.reveal(), "<redacted>")
        raise GitHubBrokerError(
            f"GitHub API {method} {path} failed with HTTP {error.code}: {diagnostic}"
        ) from error
    except urllib.error.URLError as error:
        raise GitHubBrokerError(
            f"GitHub API {method} {path} could not be reached"
        ) from error
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise GitHubBrokerError("GitHub API returned invalid JSON") from error


def mint_installation_token(
    identity: GitHubAppIdentity,
    private_key: SensitiveValue,
    *,
    api_request: Callable[..., Any] = github_api_request,
    now: int | None = None,
) -> SensitiveValue:
    jwt = create_github_app_jwt(identity.app_id, private_key, now=now)
    response = api_request(
        "POST",
        f"/app/installations/{identity.installation_id}/access_tokens",
        jwt,
        payload={
            "repository_ids": [identity.repository_id],
            "permissions": APP_REPOSITORY_PERMISSIONS,
        },
    )
    if not isinstance(response, dict) or not isinstance(response.get("token"), str):
        raise GitHubBrokerError("installation-token response omitted the token")
    return SensitiveValue(response["token"])


def git_push_with_token(
    repository: Path,
    refspec: str,
    token: SensitiveValue,
    *,
    remote: str = "origin",
    disclosure_decision: Mapping[str, Any] | None = None,
) -> None:
    """Push through a pipe-backed askpass helper; the token never enters argv or disk."""

    source_ref, separator, destination_ref = refspec.partition(":")
    source_ref = source_ref.removeprefix("+")
    if (
        not separator
        or not source_ref
        or not destination_ref.startswith("refs/heads/")
    ):
        raise GitHubBrokerError("authenticated push refspec is not an exact branch update")
    if (
        not isinstance(disclosure_decision, Mapping)
        or disclosure_decision.get("allowed") is not True
        or disclosure_decision.get("operation") != "git_push"
    ):
        raise GitHubBrokerError(
            "authenticated push requires an exact successful disclosure decision"
        )
    expected_revision = git_text(repository, "rev-parse", source_ref)
    if disclosure_decision.get("source_revision") != expected_revision:
        raise GitHubBrokerError(
            "authenticated push disclosure decision is bound to another revision"
        )
    outgoing = git(
        repository,
        "diff",
        "--name-only",
        "-z",
        f"{remote}/main...{source_ref}",
    ).stdout.split(b"\0")
    workflow_paths = sorted(
        path.decode("utf-8", "surrogateescape")
        for path in outgoing
        if path.startswith(b".github/workflows/")
    )
    if workflow_paths:
        raise GitHubBrokerError(
            "workflow changes require Benjamin's credential and cannot enter "
            "the GitHub App push boundary: "
            + ", ".join(workflow_paths)
        )

    run_dir = Path(tempfile.mkdtemp(prefix="arrp-askpass-"))
    try:
        os.chmod(run_dir, 0o700)
        helper = run_dir / "askpass.py"
        helper.write_text(
            "#!/usr/bin/env python3\n"
            "import os, sys\n"
            "if 'username' in sys.argv[-1].lower():\n"
            "    print('x-access-token')\n"
            "else:\n"
            "    with os.fdopen(int(os.environ['ARRP_TOKEN_FD'])) as handle:\n"
            "        print(handle.read(), end='')\n",
            encoding="utf-8",
        )
        os.chmod(helper, 0o700)
        read_descriptor, write_descriptor = os.pipe()
        try:
            os.write(write_descriptor, token.reveal().encode("utf-8"))
        finally:
            os.close(write_descriptor)
        environment = {
            **os.environ,
            "GIT_ASKPASS": str(helper),
            "GIT_TERMINAL_PROMPT": "0",
            "ARRP_TOKEN_FD": str(read_descriptor),
        }
        try:
            result = subprocess.run(
                ["git", "-C", str(repository), "push", remote, refspec],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                env=environment,
                pass_fds=(read_descriptor,),
            )
        finally:
            os.close(read_descriptor)
        if result.returncode:
            diagnostic = result.stderr.decode("utf-8", "replace")
            if token.reveal() in diagnostic:
                diagnostic = diagnostic.replace(token.reveal(), "<redacted>")
            raise GitHubBrokerError(
                f"authenticated Git push failed ({result.returncode}): {diagnostic}"
            )
    finally:
        shutil.rmtree(run_dir)


def encode_broker_target(operation_type: str, target: Mapping[str, Any]) -> str:
    """Return the one canonical, bounded JSON encoding for a broker target."""

    if operation_type == "read_state":
        kind = target.get("kind") if isinstance(target, Mapping) else None
        if kind == "project_field":
            required = frozenset({"kind", "project_id", "item_id", "field_id"})
        elif kind == "issue":
            required = frozenset({"kind", "issue_number"})
        elif kind == "discussion":
            required = frozenset(
                {"kind", "discussion_number", "reply_to_comment_id"}
            )
        else:
            raise GitHubBrokerError("read-state target kind is not registered")
    else:
        required = BROKER_TARGET_FIELDS.get(operation_type)
        if required is None:
            raise GitHubBrokerError("broker target operation is not registered")
    if not isinstance(target, Mapping) or set(target) != required:
        raise GitHubBrokerError("broker target fields do not match the operation")
    for key, item in target.items():
        if key in {"issue_number", "discussion_number", "reply_to_comment_id"}:
            if isinstance(item, bool) or not isinstance(item, int) or item <= 0:
                raise GitHubBrokerError("broker numeric target must be a positive integer")
        elif key == "kind":
            continue
        elif key == "marker":
            if not isinstance(item, str) or not BROKER_WRAPPER_MARKER.fullmatch(item):
                raise GitHubBrokerError("broker Issue marker is invalid")
        elif not isinstance(item, str) or not BROKER_NODE_ID.fullmatch(item):
            raise GitHubBrokerError(f"broker target {key} is not a bounded node ID")
    encoded = json.dumps(dict(target), sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > 1024:
        raise GitHubBrokerError("broker target encoding exceeds the bound")
    return encoded


def decode_broker_target(operation_type: str, encoded: object) -> dict[str, Any]:
    """Decode a broker target only when it uses the exact canonical encoding."""

    if not isinstance(encoded, str) or not encoded or len(encoded.encode("utf-8")) > 1024:
        raise GitHubBrokerError("broker target must be a bounded JSON string")
    try:
        target = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise GitHubBrokerError("broker target is not valid JSON") from exc
    if not isinstance(target, dict):
        raise GitHubBrokerError("broker target must encode one object")
    if encode_broker_target(operation_type, target) != encoded:
        raise GitHubBrokerError("broker target is not canonically encoded")
    return target


def _validate_broker_state_contract(value: Mapping[str, Any]) -> None:
    operation = value["operation_type"]
    expected = value["expected_old_state"]
    new = value["new_state_or_content"]
    if operation == "set_project_field":
        if expected is not None and not isinstance(expected, str):
            raise GitHubBrokerError("Project expected state must be text or null")
        if new is not None and not isinstance(new, str):
            raise GitHubBrokerError("Project new state must be text or null")
    elif operation == "update_issue_wrapper":
        if (
            not isinstance(expected, dict)
            or set(expected) != {"body"}
            or (expected["body"] is not None and not isinstance(expected["body"], str))
            or not isinstance(new, dict)
            or set(new) != {"body"}
            or not isinstance(new["body"], str)
        ):
            raise GitHubBrokerError("Issue wrapper states must contain only body")
        marker = decode_broker_target(operation, value["target_node_or_number"])["marker"]
        if len(new["body"].encode("utf-8")) > 65536 or new["body"].count(marker) != 1:
            raise GitHubBrokerError("Issue wrapper body must contain its marker exactly once")
    elif operation == "post_discussion_reply":
        if (
            not isinstance(expected, dict)
            or set(expected) != {"reply_absent"}
            or expected["reply_absent"] != value["idempotency_key"]
            or not isinstance(new, dict)
            or set(new) != {"body"}
            or not isinstance(new["body"], str)
            or len(new["body"].encode("utf-8")) > 65536
            or new["body"].count(value["idempotency_key"]) != 1
        ):
            raise GitHubBrokerError("Discussion reply state or idempotency marker is invalid")
    elif operation == "read_state" and new is not None:
        raise GitHubBrokerError("read-state intent cannot request a new state")


def validate_broker_intent(value: object, *, source_revision: str) -> dict[str, Any]:
    """Validate one exact, non-human-reserved semantic action request."""

    if not isinstance(value, dict) or set(value) != BROKER_INTENT_FIELDS:
        raise GitHubBrokerError("broker intent fields do not match the registered schema")
    operation_type = value["operation_type"]
    if not isinstance(operation_type, str):
        raise GitHubBrokerError("broker operation must be a string")
    if operation_type in RUNNER_OWNED_BROKER_OPERATIONS:
        raise GitHubBrokerError("nightly pull requests are runner-owned")
    if operation_type not in BROKER_OPERATION_TYPES:
        raise GitHubBrokerError("broker operation is not registered")
    if value["repository"] != GITHUB_REPOSITORY:
        raise GitHubBrokerError("broker intent targets a different repository")
    if value["source_revision"] != source_revision:
        raise GitHubBrokerError("broker intent source revision is stale")
    if value["human_reserved"] is not False:
        raise GitHubBrokerError("human-reserved action cannot enter the broker")
    if value["privacy_class"] != "public":
        raise GitHubBrokerError("broker intent is not public")
    for field_name in (
        "authority_record",
        "idempotency_key",
        "rollback_or_correction",
        "readback_contract",
    ):
        if not isinstance(value[field_name], str) or not value[field_name].strip():
            raise GitHubBrokerError(f"broker intent {field_name} must be nonblank")
    if not re.fullmatch(r"[0-9a-f]{40}", value["source_revision"]):
        raise GitHubBrokerError("broker intent source revision is not a full Git SHA")
    if not value["authority_record"].startswith("framework/"):
        raise GitHubBrokerError("broker authority record must be a framework path")
    if value["readback_contract"] != BROKER_READBACK_CONTRACTS[operation_type]:
        raise GitHubBrokerError("broker readback contract does not match the operation")
    decode_broker_target(operation_type, value["target_node_or_number"])
    _validate_broker_state_contract(value)
    return dict(value)


def require_broker_content_disclosure(
    intent: Mapping[str, Any],
    *,
    virtual_path: str,
    content: str,
    family_id: str,
) -> dict[str, Any]:
    """Independently gate exact broker content; privacy_class is not proof."""

    try:
        return require_outbound_bundle(
            [
                artifact_from_text(
                    virtual_path,
                    "arrp-semantic-broker",
                    content,
                    family_id=family_id,
                )
            ],
            operation="github_api_mutation",
            source_revision=str(intent.get("source_revision") or ""),
        )
    except DisclosureBlocked as error:
        raise DisclosurePreventionError(str(error)) from error


def require_pull_request_disclosure(
    *,
    branch: str,
    expected_head: str,
    title: str,
    body: str,
) -> dict[str, Any]:
    try:
        return require_outbound_bundle(
            [
                artifact_from_text(
                    f"github/pull-request/{branch}/title",
                    "arrp-nightly-pull-request",
                    title,
                    artifact_group=f"pull-request:{branch}",
                ),
                artifact_from_text(
                    f"github/pull-request/{branch}/body",
                    "arrp-nightly-pull-request",
                    body,
                    artifact_group=f"pull-request:{branch}",
                ),
            ],
            operation="pull_request_mutation",
            source_revision=expected_head,
        )
    except DisclosureBlocked as error:
        raise DisclosurePreventionError(str(error)) from error


def open_or_update_nightly_pull_request(
    token: SensitiveValue,
    *,
    branch: str,
    expected_head: str,
    title: str,
    body: str,
    api_request: Callable[..., Any] = github_api_request,
    readback_timeout_seconds: float = 15.0,
    readback_poll_seconds: float = 0.5,
    monotonic: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Create or read back exactly one App-authored nightly pull request."""

    if readback_timeout_seconds <= 0 or readback_poll_seconds < 0:
        raise GitHubBrokerError("invalid pull-request readback timing")
    require_pull_request_disclosure(
        branch=branch,
        expected_head=expected_head,
        title=title,
        body=body,
    )
    head = api_request(
        "GET",
        f"/repos/{GITHUB_REPOSITORY}/git/ref/heads/{branch}",
        token,
    )
    observed_head = (
        head.get("object", {}).get("sha") if isinstance(head, dict) else None
    )
    if observed_head != expected_head:
        raise GitHubBrokerError("remote nightly branch head differs from expected head")
    pulls = api_request(
        "GET",
        f"/repos/{GITHUB_REPOSITORY}/pulls?state=open&head={GITHUB_OWNER}:{branch}&base=main",
        token,
    )
    if not isinstance(pulls, list):
        raise GitHubBrokerError("pull-request lookup returned an invalid response")
    if len(pulls) > 1:
        raise GitHubBrokerError("multiple open pull requests exist for the nightly branch")
    if pulls:
        pull = pulls[0]
        number = pull.get("number") if isinstance(pull, dict) else None
        if not isinstance(number, int):
            raise GitHubBrokerError("existing pull-request lookup omitted identity")
        pull = api_request(
            "PATCH",
            f"/repos/{GITHUB_REPOSITORY}/pulls/{number}",
            token,
            payload={"title": title, "body": body},
        )
    else:
        pull = api_request(
            "POST",
            f"/repos/{GITHUB_REPOSITORY}/pulls",
            token,
            payload={
                "title": title,
                "head": branch,
                "base": "main",
                "body": body,
                "maintainer_can_modify": False,
            },
        )
    if not isinstance(pull, dict):
        raise GitHubBrokerError("pull-request operation returned an invalid response")
    number = pull.get("number")
    if not isinstance(number, int):
        raise GitHubBrokerError("pull-request operation omitted identity")
    deadline = monotonic() + readback_timeout_seconds
    while True:
        readback = api_request(
            "GET",
            f"/repos/{GITHUB_REPOSITORY}/pulls/{number}",
            token,
        )
        if (
            isinstance(readback, dict)
            and readback.get("head", {}).get("sha") == expected_head
            and readback.get("base", {}).get("ref") == "main"
        ):
            return readback
        if monotonic() >= deadline:
            raise GitHubBrokerError("pull-request head/base readback failed")
        sleeper(readback_poll_seconds)


def required_checks_readback(
    token: SensitiveValue,
    *,
    head_sha: str,
    api_request: Callable[..., Any] = github_api_request,
) -> dict[str, str]:
    checks = api_request(
        "GET",
        f"/repos/{GITHUB_REPOSITORY}/commits/{head_sha}/check-runs?per_page=100",
        token,
    )
    statuses = api_request(
        "GET",
        f"/repos/{GITHUB_REPOSITORY}/commits/{head_sha}/status",
        token,
    )
    observed: dict[str, str] = {}
    if isinstance(checks, dict):
        for row in checks.get("check_runs", []):
            if isinstance(row, dict) and isinstance(row.get("name"), str):
                observed[row["name"]] = str(row.get("conclusion") or row.get("status"))
    if isinstance(statuses, dict):
        for row in statuses.get("statuses", []):
            if isinstance(row, dict) and isinstance(row.get("context"), str):
                observed[row["context"]] = str(row.get("state"))
    return observed


def wait_for_required_checks(
    token: SensitiveValue,
    *,
    head_sha: str,
    timeout_seconds: int,
    poll_seconds: float,
    api_request: Callable[..., Any] = github_api_request,
    monotonic: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, str]:
    """Wait for the exact required checks while failing closed on any failure."""

    if timeout_seconds <= 0 or poll_seconds < 0:
        raise GitHubBrokerError("invalid required-check wait configuration")
    deadline = monotonic() + timeout_seconds
    while True:
        observed = required_checks_readback(
            token,
            head_sha=head_sha,
            api_request=api_request,
        )
        failed = {
            name: result
            for name, result in observed.items()
            if result
            in {
                "failure",
                "cancelled",
                "timed_out",
                "action_required",
                "error",
            }
        }
        if failed:
            raise GitHubBrokerError(f"pull-request checks failed: {failed}")
        if all(
            observed.get(name) in {"success", "neutral", "skipped"}
            for name in REQUIRED_CHECKS
        ):
            return observed
        if monotonic() >= deadline:
            incomplete = {
                name: observed.get(name)
                for name in REQUIRED_CHECKS
                if observed.get(name) not in {"success", "neutral", "skipped"}
            }
            raise GitHubBrokerError(
                f"required checks did not complete before timeout: {incomplete}"
            )
        sleeper(poll_seconds)


def merge_exact_head(
    token: SensitiveValue,
    *,
    pull_number: int,
    expected_head: str,
    expected_base: str,
    protected: bool,
    api_request: Callable[..., Any] = github_api_request,
) -> str:
    """Fail closed on head/base movement, review holds, checks, or merge mismatch."""

    try:
        require_outbound_bundle(
            [
                artifact_from_text(
                    f"github/control/pull-request/{pull_number}/merge",
                    "arrp-nightly-publication",
                    json.dumps(
                        {
                            "pull_number": pull_number,
                            "expected_head": expected_head,
                            "expected_base": expected_base,
                            "protected": protected,
                        },
                        sort_keys=True,
                    ),
                    family_id="github-control-payload",
                )
            ],
            operation="pull_request_merge",
            source_revision=expected_head,
        )
    except DisclosureBlocked as error:
        raise DisclosurePreventionError(str(error)) from error
    pull = api_request(
        "GET",
        f"/repos/{GITHUB_REPOSITORY}/pulls/{pull_number}",
        token,
    )
    if (
        not isinstance(pull, dict)
        or pull.get("head", {}).get("sha") != expected_head
        or pull.get("base", {}).get("sha") != expected_base
    ):
        raise GitHubBrokerError("pull request head or base moved")
    reviews = api_request(
        "GET",
        f"/repos/{GITHUB_REPOSITORY}/pulls/{pull_number}/reviews?per_page=100",
        token,
    )
    approved = any(
        isinstance(row, dict)
        and row.get("state") == "APPROVED"
        and row.get("user", {}).get("login") == GITHUB_OWNER
        for row in (reviews if isinstance(reviews, list) else [])
    )
    if protected and not approved:
        raise GitHubBrokerError("protected pull request lacks Benjamin code-owner approval")
    checks = required_checks_readback(
        token, head_sha=expected_head, api_request=api_request
    )
    required = REQUIRED_CHECKS
    incomplete = {
        name: checks.get(name)
        for name in required
        if checks.get(name) not in {"success", "neutral", "skipped"}
    }
    failed = {
        name: result
        for name, result in checks.items()
        if result in {"failure", "cancelled", "timed_out", "action_required", "error"}
    }
    if incomplete or failed:
        raise GitHubBrokerError(
            f"required checks are incomplete or failed: required={incomplete}, failed={failed}"
        )
    result = api_request(
        "PUT",
        f"/repos/{GITHUB_REPOSITORY}/pulls/{pull_number}/merge",
        token,
        payload={"merge_method": "merge", "sha": expected_head},
    )
    merge_sha = result.get("sha") if isinstance(result, dict) else None
    if not result or result.get("merged") is not True or not isinstance(merge_sha, str):
        raise GitHubBrokerError("exact-head merge was refused")
    commit = api_request(
        "GET",
        f"/repos/{GITHUB_REPOSITORY}/git/commits/{merge_sha}",
        token,
    )
    parent_shas = (
        [row.get("sha") for row in commit.get("parents", [])]
        if isinstance(commit, dict)
        else []
    )
    if expected_head not in parent_shas or expected_base not in parent_shas:
        raise GitHubBrokerError("merge-commit parent readback failed")
    return merge_sha


def wait_for_pages_deployment(
    token: SensitiveValue,
    *,
    merge_sha: str,
    timeout_seconds: int,
    poll_seconds: float,
    api_request: Callable[..., Any] = github_api_request,
    monotonic: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Require a successful public-site workflow for the exact merge SHA."""

    if timeout_seconds <= 0 or poll_seconds < 0:
        raise GitHubBrokerError("invalid Pages wait configuration")
    encoded_sha = urllib.parse.quote(merge_sha, safe="")
    path = (
        f"/repos/{GITHUB_REPOSITORY}/actions/workflows/public-site.yml/runs"
        f"?event=push&head_sha={encoded_sha}&per_page=20"
    )
    deadline = monotonic() + timeout_seconds
    while True:
        response = api_request("GET", path, token)
        rows = response.get("workflow_runs") if isinstance(response, dict) else None
        if not isinstance(rows, list):
            raise GitHubBrokerError("Pages workflow lookup returned invalid data")
        exact = [
            row
            for row in rows
            if isinstance(row, dict) and row.get("head_sha") == merge_sha
        ]
        if len(exact) > 1:
            exact.sort(key=lambda row: int(row.get("id", 0)), reverse=True)
        if exact:
            run = exact[0]
            if run.get("status") == "completed":
                if run.get("conclusion") != "success":
                    raise GitHubBrokerError(
                        "exact-SHA public-site workflow did not succeed"
                    )
                return {
                    "id": run.get("id"),
                    "head_sha": merge_sha,
                    "status": "completed",
                    "conclusion": "success",
                    "url": run.get("html_url"),
                }
        if monotonic() >= deadline:
            raise GitHubBrokerError(
                "exact-SHA public-site workflow did not complete before timeout"
            )
        sleeper(poll_seconds)


def github_graphql_request(
    query: str,
    variables: Mapping[str, Any],
    token: SensitiveValue,
    *,
    api_request: Callable[..., Any] = github_api_request,
) -> dict[str, Any]:
    response = api_request(
        "POST",
        "/graphql",
        token,
        payload={"query": query, "variables": dict(variables)},
    )
    if not isinstance(response, dict) or response.get("errors"):
        raise GitHubBrokerError("GitHub GraphQL operation failed")
    data = response.get("data")
    if not isinstance(data, dict):
        raise GitHubBrokerError("GitHub GraphQL response omitted data")
    return data


PROJECT_TEXT_FIELD_QUERY = """
query($item: ID!) {
  node(id: $item) {
    ... on ProjectV2Item {
      fieldValues(first: 100) {
        nodes {
          ... on ProjectV2ItemFieldTextValue {
            text
            field {
              ... on ProjectV2FieldCommon {
                id
              }
            }
          }
        }
      }
    }
  }
}
"""

PROJECT_TEXT_FIELD_UPDATE = """
mutation($project: ID!, $item: ID!, $field: ID!, $text: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $project,
    itemId: $item,
    fieldId: $field,
    value: {text: $text}
  }) {
    projectV2Item { id }
  }
}
"""

PROJECT_FIELD_CLEAR = """
mutation($project: ID!, $item: ID!, $field: ID!) {
  clearProjectV2ItemFieldValue(input: {
    projectId: $project,
    itemId: $item,
    fieldId: $field
  }) {
    projectV2Item { id }
  }
}
"""


def read_project_text_field(
    fixture: Mapping[str, Any],
    token: SensitiveValue,
    *,
    graphql_request: Callable[..., dict[str, Any]] = github_graphql_request,
) -> str | None:
    data = graphql_request(
        PROJECT_TEXT_FIELD_QUERY,
        {"item": fixture["item_id"]},
        token,
    )
    node = data.get("node")
    values = node.get("fieldValues", {}).get("nodes", []) if isinstance(node, dict) else []
    for value in values:
        field_value = value.get("field") if isinstance(value, dict) else None
        if (
            isinstance(value, dict)
            and isinstance(field_value, dict)
            and field_value.get("id") == fixture["field_id"]
        ):
            text_value = value.get("text")
            return text_value if isinstance(text_value, str) else None
    return None


def write_project_text_field(
    fixture: Mapping[str, Any],
    value: str | None,
    token: SensitiveValue,
    *,
    graphql_request: Callable[..., dict[str, Any]] = github_graphql_request,
) -> None:
    variables = {
        "project": fixture["project_id"],
        "item": fixture["item_id"],
        "field": fixture["field_id"],
    }
    if value is None:
        graphql_request(PROJECT_FIELD_CLEAR, variables, token)
    else:
        graphql_request(
            PROJECT_TEXT_FIELD_UPDATE,
            {**variables, "text": value},
            token,
        )


def run_reversible_project_text_fixture(
    fixture: Mapping[str, Any],
    token: SensitiveValue,
    *,
    read_field: Callable[..., str | None] = read_project_text_field,
    write_field: Callable[..., None] = write_project_text_field,
) -> dict[str, Any]:
    """Change one exact text field, read it back, and restore its prior value."""

    required = {
        "project_id",
        "item_id",
        "field_id",
        "expected_old_value",
        "fixture_value",
    }
    if set(fixture) != required or not all(
        isinstance(fixture[name], str) and fixture[name]
        for name in ("project_id", "item_id", "field_id", "fixture_value")
    ):
        raise GitHubBrokerError("Project fixture fields are invalid")
    expected_old = fixture["expected_old_value"]
    if expected_old is not None and not isinstance(expected_old, str):
        raise GitHubBrokerError("Project fixture expected value is invalid")
    try:
        require_outbound_bundle(
            [
                artifact_from_text(
                    f"github/project-field/{fixture['field_id']}/fixture",
                    "arrp-semantic-broker",
                    json.dumps(
                        {
                            "fixture_value": fixture["fixture_value"],
                            "restore_value": expected_old,
                        },
                        sort_keys=True,
                    ),
                    family_id="github-project-field-text",
                )
            ],
            operation="github_api_mutation",
            source_revision="p5-supervised-fixture",
        )
    except DisclosureBlocked as error:
        raise DisclosurePreventionError(str(error)) from error
    observed = read_field(fixture, token)
    if observed != expected_old:
        raise GitHubBrokerError("Project fixture prior-state check failed")
    changed = False
    try:
        write_field(fixture, fixture["fixture_value"], token)
        changed = True
        if read_field(fixture, token) != fixture["fixture_value"]:
            raise GitHubBrokerError("Project fixture changed-state readback failed")
    finally:
        if changed:
            write_field(fixture, expected_old, token)
    restored = read_field(fixture, token)
    if restored != expected_old:
        raise GitHubBrokerError("Project fixture restoration readback failed")
    return {
        "project_id": fixture["project_id"],
        "item_id": fixture["item_id"],
        "field_id": fixture["field_id"],
        "changed_value_readback": True,
        "restored": True,
        "restored_value": restored,
    }


def execute_project_field_intent(
    intent: Mapping[str, Any],
    project_token: SensitiveValue,
    *,
    read_field: Callable[[Mapping[str, Any], SensitiveValue], Any],
    write_field: Callable[[Mapping[str, Any], Any, SensitiveValue], None],
) -> dict[str, Any]:
    """Apply one exact Project field transition and require readback."""

    if intent.get("operation_type") != "set_project_field":
        raise GitHubBrokerError("intent is not a Project field operation")
    target = decode_broker_target(
        "set_project_field", intent.get("target_node_or_number")
    )
    requested = intent.get("new_state_or_content")
    require_broker_content_disclosure(
        intent,
        virtual_path=f"github/project-field/{target['field_id']}/value",
        content=json.dumps(requested, sort_keys=True, ensure_ascii=False),
        family_id="github-project-field-text",
    )
    observed = read_field(target, project_token)
    if observed == requested:
        return {
            "idempotency_key": intent["idempotency_key"],
            "old_state": intent.get("expected_old_state"),
            "new_state": observed,
            "already_applied": True,
        }
    if observed != intent.get("expected_old_state"):
        raise GitHubBrokerError("Project field prior-state check failed")
    write_field(target, requested, project_token)
    readback = read_field(target, project_token)
    if readback != requested:
        raise GitHubBrokerError("Project field readback failed")
    return {
        "idempotency_key": intent["idempotency_key"],
        "old_state": observed,
        "new_state": readback,
        "already_applied": False,
    }


def execute_issue_wrapper_intent(
    intent: Mapping[str, Any],
    token: SensitiveValue,
    *,
    api_request: Callable[..., Any] = github_api_request,
) -> dict[str, Any]:
    """Apply an exact Issue body transition and read it back."""

    if intent.get("operation_type") != "update_issue_wrapper":
        raise GitHubBrokerError("intent is not an Issue wrapper operation")
    target = decode_broker_target(
        "update_issue_wrapper", intent.get("target_node_or_number")
    )
    requested = intent["new_state_or_content"]["body"]
    require_broker_content_disclosure(
        intent,
        virtual_path=f"github/issue/{target['issue_number']}/body",
        content=requested,
        family_id="github-issue-text",
    )
    path = f"/repos/{GITHUB_REPOSITORY}/issues/{target['issue_number']}"

    def read_body() -> str | None:
        response = api_request("GET", path, token)
        if not isinstance(response, dict) or "pull_request" in response:
            raise GitHubBrokerError("Issue wrapper target did not read back as an Issue")
        body = response.get("body")
        if body is not None and not isinstance(body, str):
            raise GitHubBrokerError("Issue wrapper body readback is invalid")
        return body

    expected = intent["expected_old_state"]["body"]
    observed = read_body()
    if observed == requested:
        return {
            "idempotency_key": intent["idempotency_key"],
            "old_state": expected,
            "new_state": observed,
            "already_applied": True,
        }
    if observed != expected:
        raise GitHubBrokerError("Issue wrapper prior-state check failed")
    response = api_request("PATCH", path, token, payload={"body": requested})
    if not isinstance(response, dict):
        raise GitHubBrokerError("Issue wrapper update returned invalid data")
    readback = read_body()
    if readback != requested:
        raise GitHubBrokerError("Issue wrapper readback failed")
    return {
        "idempotency_key": intent["idempotency_key"],
        "old_state": observed,
        "new_state": readback,
        "already_applied": False,
    }


DISCUSSION_REPLY_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    discussion(number: $number) {
      id
      comments(first: 100) {
        nodes {
          id
          databaseId
          body
          replies(first: 100) {
            nodes { id body }
            pageInfo { hasNextPage }
          }
        }
        pageInfo { hasNextPage }
      }
    }
  }
}
"""

DISCUSSION_REPLY_MUTATION = """
mutation($discussion: ID!, $replyTo: ID!, $body: String!) {
  addDiscussionComment(input: {
    discussionId: $discussion,
    replyToId: $replyTo,
    body: $body
  }) {
    comment { id body }
  }
}
"""


def discussion_reply_matches(
    target: Mapping[str, Any],
    idempotency_key: str,
    token: SensitiveValue,
    *,
    graphql_request: Callable[..., dict[str, Any]] = github_graphql_request,
) -> list[dict[str, str]]:
    """Read exact replies carrying one broker idempotency marker."""

    data = graphql_request(
        DISCUSSION_REPLY_QUERY,
        {
            "owner": GITHUB_OWNER,
            "name": GITHUB_REPOSITORY.split("/", 1)[1],
            "number": target["discussion_number"],
        },
        token,
    )
    discussion = data.get("repository", {}).get("discussion")
    comments = discussion.get("comments") if isinstance(discussion, dict) else None
    if not isinstance(comments, dict) or comments.get("pageInfo", {}).get("hasNextPage"):
        raise GitHubBrokerError("Discussion comment lookup is missing or paginated")
    nodes = comments.get("nodes")
    if not isinstance(nodes, list):
        raise GitHubBrokerError("Discussion comment lookup rows are invalid")
    parent = next(
        (
            row
            for row in nodes
            if isinstance(row, dict)
            and row.get("databaseId") == target["reply_to_comment_id"]
        ),
        None,
    )
    replies = parent.get("replies") if isinstance(parent, dict) else None
    if not isinstance(replies, dict) or replies.get("pageInfo", {}).get("hasNextPage"):
        raise GitHubBrokerError("Discussion reply readback is missing or paginated")
    rows = replies.get("nodes")
    if not isinstance(rows, list):
        raise GitHubBrokerError("Discussion reply readback rows are invalid")
    return [
        {"id": row["id"], "body": row["body"]}
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("id"), str)
        and isinstance(row.get("body"), str)
        and idempotency_key in row["body"]
    ]


def discussion_target_node_ids(
    target: Mapping[str, Any],
    token: SensitiveValue,
    *,
    graphql_request: Callable[..., dict[str, Any]] = github_graphql_request,
) -> tuple[str, str]:
    """Resolve a bounded public Discussion number/comment database ID pair."""

    data = graphql_request(
        DISCUSSION_REPLY_QUERY,
        {
            "owner": GITHUB_OWNER,
            "name": GITHUB_REPOSITORY.split("/", 1)[1],
            "number": target["discussion_number"],
        },
        token,
    )
    discussion = data.get("repository", {}).get("discussion")
    comments = discussion.get("comments") if isinstance(discussion, dict) else None
    nodes = comments.get("nodes") if isinstance(comments, dict) else None
    if (
        not isinstance(discussion, dict)
        or not BROKER_NODE_ID.fullmatch(str(discussion.get("id", "")))
        or not isinstance(comments, dict)
        or comments.get("pageInfo", {}).get("hasNextPage")
        or not isinstance(nodes, list)
    ):
        raise GitHubBrokerError("Discussion target resolution is invalid or paginated")
    parent = next(
        (
            row
            for row in nodes
            if isinstance(row, dict)
            and row.get("databaseId") == target["reply_to_comment_id"]
            and BROKER_NODE_ID.fullmatch(str(row.get("id", "")))
        ),
        None,
    )
    if parent is None:
        raise GitHubBrokerError("Discussion reply target was not found")
    return str(discussion["id"]), str(parent["id"])


def execute_discussion_reply_intent(
    intent: Mapping[str, Any],
    token: SensitiveValue,
    *,
    graphql_request: Callable[..., dict[str, Any]] = github_graphql_request,
) -> dict[str, Any]:
    """Post one validated Discussion reply and prove exactly-once readback."""

    if intent.get("operation_type") != "post_discussion_reply":
        raise GitHubBrokerError("intent is not a Discussion reply operation")
    target = decode_broker_target(
        "post_discussion_reply", intent.get("target_node_or_number")
    )
    marker = intent["idempotency_key"]
    requested = intent["new_state_or_content"]["body"]
    require_broker_content_disclosure(
        intent,
        virtual_path=(
            f"github/discussion/{target['discussion_number']}/"
            f"reply/{target['reply_to_comment_id']}"
        ),
        content=requested,
        family_id="github-discussion-text",
    )
    matches = discussion_reply_matches(
        target, marker, token, graphql_request=graphql_request
    )
    if len(matches) > 1:
        raise GitHubBrokerError("Discussion reply idempotency marker is duplicated")
    if len(matches) == 1:
        if matches[0]["body"] != requested:
            raise GitHubBrokerError("Discussion reply marker has different content")
        return {
            "idempotency_key": marker,
            "reply_id": matches[0]["id"],
            "already_applied": True,
        }
    discussion_id, reply_to_id = discussion_target_node_ids(
        target, token, graphql_request=graphql_request
    )
    data = graphql_request(
        DISCUSSION_REPLY_MUTATION,
        {
            "discussion": discussion_id,
            "replyTo": reply_to_id,
            "body": requested,
        },
        token,
    )
    comment = data.get("addDiscussionComment", {}).get("comment")
    if not isinstance(comment, dict) or comment.get("body") != requested:
        raise GitHubBrokerError("Discussion reply mutation response is invalid")
    matches = discussion_reply_matches(
        target, marker, token, graphql_request=graphql_request
    )
    if len(matches) != 1 or matches[0]["body"] != requested:
        raise GitHubBrokerError("Discussion reply exact-once readback failed")
    return {
        "idempotency_key": marker,
        "reply_id": matches[0]["id"],
        "already_applied": False,
    }


def execute_read_state_intent(
    intent: Mapping[str, Any],
    github_token: SensitiveValue,
    *,
    project_token: SensitiveValue | None = None,
    api_request: Callable[..., Any] = github_api_request,
    graphql_request: Callable[..., dict[str, Any]] = github_graphql_request,
) -> dict[str, Any]:
    """Read one registered state target without performing a mutation."""

    if intent.get("operation_type") != "read_state":
        raise GitHubBrokerError("intent is not a read-state operation")
    target = decode_broker_target("read_state", intent.get("target_node_or_number"))
    if target["kind"] == "project_field":
        if project_token is None:
            raise GitHubBrokerError("Project read requires the Project-only credential")
        observed = read_project_text_field(
            target, project_token, graphql_request=graphql_request
        )
    elif target["kind"] == "issue":
        response = api_request(
            "GET",
            f"/repos/{GITHUB_REPOSITORY}/issues/{target['issue_number']}",
            github_token,
        )
        if not isinstance(response, dict) or "pull_request" in response:
            raise GitHubBrokerError("Issue state readback is invalid")
        observed = {"body": response.get("body"), "state": response.get("state")}
    else:
        data = graphql_request(
            DISCUSSION_REPLY_QUERY,
            {
                "owner": GITHUB_OWNER,
                "name": GITHUB_REPOSITORY.split("/", 1)[1],
                "number": target["discussion_number"],
            },
            github_token,
        )
        discussion = data.get("repository", {}).get("discussion")
        comments = discussion.get("comments") if isinstance(discussion, dict) else None
        nodes = comments.get("nodes") if isinstance(comments, dict) else None
        node = next(
            (
                row
                for row in nodes or []
                if isinstance(row, dict)
                and row.get("databaseId") == target["reply_to_comment_id"]
            ),
            None,
        )
        if not isinstance(node, dict) or not isinstance(node.get("body"), str):
            raise GitHubBrokerError("Discussion state readback is invalid")
        observed = {"body": node["body"]}
    expected = intent.get("expected_old_state")
    if expected is not None and observed != expected:
        raise GitHubBrokerError("read-state exact snapshot check failed")
    return {
        "idempotency_key": intent["idempotency_key"],
        "state": observed,
        "mutated": False,
    }


def execute_semantic_broker_intent(
    intent: object,
    *,
    source_revision: str,
    github_token: SensitiveValue,
    project_token: SensitiveValue | None = None,
    api_request: Callable[..., Any] = github_api_request,
    graphql_request: Callable[..., dict[str, Any]] = github_graphql_request,
) -> dict[str, Any]:
    """Validate and execute exactly one model-requestable broker operation."""

    accepted = validate_broker_intent(intent, source_revision=source_revision)
    preflight_semantic_broker_disclosure(accepted)
    operation = accepted["operation_type"]
    if operation == "set_project_field":
        if project_token is None:
            raise GitHubBrokerError("Project write requires the Project-only credential")
        return execute_project_field_intent(
            accepted,
            project_token,
            read_field=lambda target, token: read_project_text_field(
                target, token, graphql_request=graphql_request
            ),
            write_field=lambda target, value, token: write_project_text_field(
                target, value, token, graphql_request=graphql_request
            ),
        )
    if operation == "update_issue_wrapper":
        return execute_issue_wrapper_intent(
            accepted, github_token, api_request=api_request
        )
    if operation == "post_discussion_reply":
        return execute_discussion_reply_intent(
            accepted, github_token, graphql_request=graphql_request
        )
    return execute_read_state_intent(
        accepted,
        github_token,
        project_token=project_token,
        api_request=api_request,
        graphql_request=graphql_request,
    )


def preflight_semantic_broker_disclosure(
    accepted: Mapping[str, Any],
) -> dict[str, Any]:
    """Gate exact semantic content before any credential-backed access."""

    operation = str(accepted.get("operation_type") or "")
    target = decode_broker_target(
        operation, accepted.get("target_node_or_number")
    )
    requested = accepted.get("new_state_or_content")
    if operation == "set_project_field":
        return require_broker_content_disclosure(
            accepted,
            virtual_path=f"github/project-field/{target['field_id']}/value",
            content=json.dumps(requested, sort_keys=True, ensure_ascii=False),
            family_id="github-project-field-text",
        )
    if operation == "update_issue_wrapper":
        return require_broker_content_disclosure(
            accepted,
            virtual_path=f"github/issue/{target['issue_number']}/body",
            content=str((requested or {}).get("body") or ""),
            family_id="github-issue-text",
        )
    if operation == "post_discussion_reply":
        return require_broker_content_disclosure(
            accepted,
            virtual_path=(
                f"github/discussion/{target['discussion_number']}/"
                f"reply/{target['reply_to_comment_id']}"
            ),
            content=str((requested or {}).get("body") or ""),
            family_id="github-discussion-text",
        )
    return require_broker_content_disclosure(
        accepted,
        virtual_path="github/control/read-state",
        content=json.dumps(target, sort_keys=True, ensure_ascii=False),
        family_id="github-control-payload",
    )


def validate_repository_policy(repository: Path) -> dict[str, Any]:
    """Reject tracked symlinks, submodules, and unregistered executable modes."""

    output = git(repository, "ls-files", "-s", "-z").stdout.split(b"\0")
    symlinks: list[str] = []
    submodules: list[str] = []
    unexpected_executables: list[str] = []
    for raw in output:
        if not raw:
            continue
        metadata, path_bytes = raw.split(b"\t", 1)
        mode = metadata.split(b" ", 1)[0].decode("ascii")
        path = path_bytes.decode("utf-8", "surrogateescape")
        if mode == "120000":
            symlinks.append(path)
        elif mode == "160000":
            submodules.append(path)
        elif mode == "100755" and path not in EXPECTED_TRACKED_EXECUTABLES:
            unexpected_executables.append(path)
    if symlinks or submodules or unexpected_executables:
        raise TransactionError(
            "repository runtime policy failed: "
            f"symlinks={symlinks}, submodules={submodules}, "
            f"unexpected_executables={unexpected_executables}"
        )
    return {
        "tracked_symlinks": 0,
        "tracked_submodules": 0,
        "tracked_executables": sorted(EXPECTED_TRACKED_EXECUTABLES),
    }


def _resolve_inside(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if not _is_within(candidate, root.resolve()):
        raise TransactionError(f"path escapes its local root: {relative}")
    return candidate


def _valid_stage_envelope(
    state_root: Path,
    spec: LocalStageSpec,
    record: Mapping[str, Any] | None,
    now: datetime,
) -> bool:
    if spec.cadence_hours is None or not isinstance(record, Mapping):
        return False
    relative = record.get("envelope")
    expected_hash = record.get("sha256")
    if not isinstance(relative, str) or not isinstance(expected_hash, str):
        return False
    try:
        envelope_path = _resolve_inside(state_root, relative)
        envelope = read_json_object(envelope_path)
        completed = datetime.fromisoformat(
            str(envelope["completed_at"]).replace("Z", "+00:00")
        )
    except (KeyError, OSError, UnicodeError, ValueError, json.JSONDecodeError, TransactionError):
        return False
    if completed.tzinfo is None:
        return False
    age = (now - completed.astimezone(timezone.utc)).total_seconds()
    if age < 0 or age > spec.cadence_hours * 3600:
        return False
    if (
        envelope.get("schema_version") != 1
        or envelope.get("stage_id") != spec.identifier
        or envelope.get("status") != "succeeded"
        or file_sha256(envelope_path) != expected_hash
    ):
        return False
    outputs = envelope.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        return False
    for output in outputs:
        if not isinstance(output, dict):
            return False
        try:
            path = _resolve_inside(state_root, str(output["path"]))
            expected = str(output["sha256"])
            read_json_object(path)
        except (KeyError, OSError, UnicodeError, json.JSONDecodeError, TransactionError):
            return False
        if path.is_symlink() or not path.is_file() or file_sha256(path) != expected:
            return False
    return True


def determine_stage_due(
    state_root: Path,
    spec: LocalStageSpec,
    last_success: Mapping[str, Any],
    *,
    now: datetime | None = None,
) -> tuple[bool, str]:
    current = now or utc_now()
    stages = last_success.get("stages")
    record = stages.get(spec.identifier) if isinstance(stages, Mapping) else None
    if _valid_stage_envelope(state_root, spec, record, current):
        return False, "current_typed_output"
    if spec.cadence_hours is None:
        return True, "always"
    return True, "missing_stale_or_invalid_typed_output"


def _render_stage_value(
    value: str,
    worktree: Path,
    run_dir: Path,
    runtime_root: Path | None = None,
) -> str:
    return (
        value.replace("{worktree}", str(worktree))
        .replace("{run_dir}", str(run_dir))
        .replace("{runtime}", str(runtime_root or worktree))
    )


def verify_worktree_entrypoint(
    worktree: Path,
    runtime_commit: str,
    entrypoint: Path,
) -> None:
    """Require a worktree script to remain byte-identical to reviewed runtime."""

    resolved = entrypoint.resolve()
    if not _is_within(resolved, worktree.resolve()):
        raise TransactionError("worktree entrypoint escapes the transaction root")
    relative = resolved.relative_to(worktree.resolve()).as_posix()
    if resolved.is_symlink() or not resolved.is_file():
        raise TransactionError(f"worktree entrypoint is unsafe: {relative}")
    reviewed = git(worktree, "show", f"{runtime_commit}:{relative}").stdout
    if hashlib.sha256(resolved.read_bytes()).digest() != hashlib.sha256(reviewed).digest():
        raise TransactionError(
            f"worktree entrypoint differs from runtime commit: {relative}"
        )


def run_local_stages(
    *,
    worktree: Path,
    run_dir: Path,
    state_root: Path,
    specs: Sequence[LocalStageSpec],
    last_success: Mapping[str, Any] | None = None,
    environment: Mapping[str, str] | None = None,
    environment_by_stage: Mapping[str, Mapping[str, str]] | None = None,
    now: datetime | None = None,
    runtime_root: Path | None = None,
    runtime_commit: str | None = None,
    blocked_stages: Mapping[str, str] | None = None,
) -> list[LocalStageResult]:
    """Execute exact stage commands and write typed, hash-bound envelopes."""

    ensure_owner_directory(run_dir)
    current = now or utc_now()
    baseline = last_success or {}
    results: list[LocalStageResult] = []
    for spec in specs:
        blocked_reason = (blocked_stages or {}).get(spec.identifier)
        if blocked_reason:
            stage_dir = run_dir / "stages" / spec.identifier
            ensure_owner_directory(stage_dir)
            envelope_path = stage_dir / "stage-result.json"
            atomic_write_json(
                envelope_path,
                {
                    "schema_version": 1,
                    "stage_id": spec.identifier,
                    "status": "failed",
                    "reason": blocked_reason,
                    "returncode": None,
                    "outputs": [],
                },
            )
            results.append(
                LocalStageResult(
                    spec.identifier,
                    "failed",
                    blocked_reason,
                    None,
                    str(envelope_path),
                )
            )
            continue
        due, reason = determine_stage_due(
            state_root, spec, baseline, now=current
        )
        if not due:
            results.append(LocalStageResult(spec.identifier, "not_due", reason, None, None))
            continue
        stage_dir = run_dir / "stages" / spec.identifier
        ensure_owner_directory(stage_dir)
        command = tuple(
            _render_stage_value(value, worktree, run_dir, runtime_root)
            for value in spec.command
        )
        if runtime_commit is not None:
            if len(command) < 2:
                raise TransactionError(
                    f"stage command lacks a reviewed entrypoint: {spec.identifier}"
                )
            verify_worktree_entrypoint(
                worktree,
                runtime_commit,
                Path(command[1]),
            )
        stage_environment = dict(environment or os.environ)
        stage_environment.update(
            (environment_by_stage or {}).get(spec.identifier, {})
        )
        # The reviewed bootstrap uses ``-B`` for this coordinator process, but
        # that interpreter flag is not inherited by child Python processes.
        # Enforce the same invariant in every deterministic stage so a run
        # cannot add bytecode to its reviewed runtime or transaction worktree.
        stage_environment["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.run(
            command,
            cwd=worktree,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=stage_environment,
        )
        output_rows: list[dict[str, str]] = []
        output_error: str | None = None
        for relative in spec.outputs:
            rendered = _render_stage_value(
                relative,
                worktree,
                run_dir,
                runtime_root,
            )
            path = Path(rendered).resolve()
            if not _is_within(path, run_dir.resolve()) and not _is_within(
                path, worktree.resolve()
            ):
                output_error = f"output outside run/worktree roots: {path}"
                break
            try:
                if path.is_symlink() or not path.is_file():
                    raise TransactionError("output is absent, nonregular, or a symlink")
                read_json_object(path)
                output_rows.append(
                    {
                        "path": str(path.relative_to(state_root.resolve())),
                        "sha256": file_sha256(path),
                    }
                )
            except (OSError, UnicodeError, ValueError, json.JSONDecodeError, TransactionError) as error:
                output_error = f"{path}: {error}"
                break
        failed = process.returncode != 0 or output_error is not None
        status = (
            "failed"
            if failed and spec.failure_class == "blocking"
            else "degraded"
            if failed
            else "succeeded"
        )
        envelope_path = stage_dir / "stage-result.json"
        stderr_diagnostic = process.stderr.decode("utf-8", "replace").strip()
        diagnostic_parts = []
        if output_error is not None:
            diagnostic_parts.append(f"output validation: {output_error}")
        if stderr_diagnostic:
            diagnostic_parts.append(f"stderr: {stderr_diagnostic}")
        atomic_write_json(
            envelope_path,
            {
                "schema_version": 1,
                "stage_id": spec.identifier,
                "status": status,
                "failure_class": spec.failure_class,
                "completed_at": iso_utc(current),
                "returncode": process.returncode,
                "outputs": output_rows,
                "diagnostic": "\n".join(diagnostic_parts)[:1000],
            },
        )
        results.append(
            LocalStageResult(
                spec.identifier,
                status,
                reason,
                process.returncode,
                str(envelope_path),
            )
        )
        if status == "failed":
            break
    return results


def last_success_document(
    state_root: Path,
    run_dir: Path,
    results: Sequence[LocalStageResult],
    *,
    run_id: str,
    previous: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    prior_stages = (previous or {}).get("stages")
    stages: dict[str, dict[str, str]] = {}
    for result in results:
        if (
            result.status in {"not_due", "degraded"}
            and isinstance(prior_stages, Mapping)
            and isinstance(prior_stages.get(result.identifier), Mapping)
        ):
            stages[result.identifier] = dict(prior_stages[result.identifier])
            continue
        if result.status != "succeeded" or result.envelope is None:
            continue
        envelope = Path(result.envelope).resolve()
        stages[result.identifier] = {
            "envelope": str(envelope.relative_to(state_root.resolve())),
            "sha256": file_sha256(envelope),
        }
    return {
        "schema_version": 1,
        "run_id": run_id,
        "completed_at": iso_utc(),
        "run_directory": str(run_dir.resolve().relative_to(state_root.resolve())),
        "stages": stages,
    }


def _validated_successful_stage_binding(
    state_root: Path,
    identifier: str,
    record: Mapping[str, Any],
) -> tuple[str, str]:
    relative = record.get("envelope")
    parts = Path(str(relative)).parts if isinstance(relative, str) else ()
    if (
        len(parts) != 5
        or parts[0] != "runs"
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", parts[1]) is None
        or parts[2:] != ("stages", identifier, "stage-result.json")
        or not isinstance(record.get("sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", str(record["sha256"])) is None
    ):
        raise TransactionError("last-success stage binding is malformed")
    origin_run_id = parts[1]
    runs_root = state_root / "runs"
    origin_root = runs_root / origin_run_id
    stage_root = origin_root / "stages" / identifier
    for directory in (runs_root, origin_root, origin_root / "stages", stage_root):
        try:
            info = directory.lstat()
        except OSError as error:
            raise TransactionError("last-success stage path is unavailable") from error
        if (
            stat.S_ISLNK(info.st_mode)
            or not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.getuid()
            or bool(stat.S_IMODE(info.st_mode) & 0o022)
        ):
            raise TransactionError("last-success stage path is unsafe")
    envelope_path = stage_root / "stage-result.json"
    try:
        envelope = json.loads(
            read_owner_text(
                envelope_path,
                label=f"last-success envelope for {identifier}",
                maximum_bytes=2 * 1024 * 1024,
            )
        )
    except (json.JSONDecodeError, UnicodeError) as error:
        raise TransactionError("last-success stage envelope is malformed") from error
    origin_chain_path = origin_root / "run-chain.json"
    try:
        origin_chain = json.loads(
            read_owner_text(
                origin_chain_path,
                label=f"origin chain for {identifier}",
                maximum_bytes=2 * 1024 * 1024,
            )
        )
    except (json.JSONDecodeError, UnicodeError) as error:
        raise TransactionError("last-success origin chain is malformed") from error
    origin_stages = (
        origin_chain.get("stages") if isinstance(origin_chain, Mapping) else None
    )
    origin_stage = next(
        (
            row
            for row in origin_stages or []
            if isinstance(row, Mapping) and row.get("id") == identifier
        ),
        None,
    )
    stage_output = _stage_output_from_envelope(state_root, envelope_path)
    last_success_at = (
        origin_stage.get("last_success_at")
        if isinstance(origin_stage, Mapping)
        else None
    )
    if (
        not isinstance(envelope, Mapping)
        or envelope.get("schema_version") != 1
        or envelope.get("stage_id") != identifier
        or envelope.get("status") != "succeeded"
        or file_sha256(envelope_path) != record["sha256"]
        or not isinstance(origin_chain, Mapping)
        or origin_chain.get("schema_version") != 1
        or origin_chain.get("run_id") != origin_run_id
        or origin_chain.get("chain_id") != origin_run_id
        or not isinstance(origin_stages, list)
        or [
            row.get("id")
            for row in origin_stages
            if isinstance(row, Mapping)
        ]
        != list(LOCAL_STAGE_ORDER)
        or origin_stage is None
        or origin_stage.get("status") != "succeeded"
        or not isinstance(last_success_at, str)
        or not isinstance(origin_stage.get("output"), Mapping)
        or origin_stage["output"].get("sha256")
        not in {
            "sha256:" + file_sha256(stage_output),
            "sha256:" + str(record["sha256"]),
        }
    ):
        raise TransactionError("last-success stage binding differs")
    return origin_run_id, last_success_at


def prior_run_chain_for_plan(
    state_root: Path,
    last_success: Mapping[str, Any],
) -> Path:
    """Bind coordinator cadence planning to the exact prior successful chain."""

    run_id = last_success.get("run_id")
    stages = last_success.get("stages")
    if (
        last_success.get("schema_version") != 1
        or not isinstance(run_id, str)
        or SAFE_RUN_ID.fullmatch(run_id) is None
        or last_success.get("run_directory") != f"runs/{run_id}"
        or not isinstance(stages, Mapping)
        or not set(stages).issubset(LOCAL_STAGE_ORDER)
    ):
        raise TransactionError("last-success cadence authority is malformed")

    runs_root = state_root / "runs"
    run_root = runs_root / run_id
    for directory in (runs_root, run_root):
        try:
            info = directory.lstat()
        except OSError as error:
            raise TransactionError("prior successful run path is unavailable") from error
        if (
            stat.S_ISLNK(info.st_mode)
            or not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.getuid()
            or bool(stat.S_IMODE(info.st_mode) & 0o022)
        ):
            raise TransactionError("prior successful run path is unsafe")
    chain_path = run_root / "run-chain.json"
    try:
        chain = json.loads(
            read_owner_text(
                chain_path,
                label="prior successful run chain",
                maximum_bytes=2 * 1024 * 1024,
            )
        )
    except (json.JSONDecodeError, UnicodeError) as error:
        raise TransactionError("prior successful run chain is malformed") from error
    chain_stages = chain.get("stages") if isinstance(chain, Mapping) else None
    if (
        not isinstance(chain, Mapping)
        or chain.get("schema_version") != 1
        or chain.get("run_id") != run_id
        or chain.get("chain_id") != run_id
        or not isinstance(chain_stages, list)
        or [row.get("id") for row in chain_stages if isinstance(row, Mapping)]
        != list(LOCAL_STAGE_ORDER)
    ):
        raise TransactionError("prior successful run chain identity differs")

    chain_by_id = {str(row["id"]): row for row in chain_stages}
    for identifier in LOCAL_STAGE_ORDER:
        chain_stage = chain_by_id[identifier]
        record = stages.get(identifier)
        if record is None:
            if (
                chain_stage.get("status") not in {"not_due", "degraded"}
                or chain_stage.get("last_success_at") is not None
            ):
                raise TransactionError("last-success stage binding differs")
            continue
        if not isinstance(record, Mapping):
            raise TransactionError("last-success stage binding is malformed")
        origin_run_id, last_success_at = _validated_successful_stage_binding(
            state_root,
            identifier,
            record,
        )
        current_status = chain_stage.get("status")
        if (
            current_status not in {"succeeded", "not_due", "degraded"}
            or chain_stage.get("last_success_at") != last_success_at
            or (current_status == "succeeded") != (origin_run_id == run_id)
        ):
            raise TransactionError("prior successful stage binding differs")
    return chain_path


def sealed_elim_environment(
    source: Mapping[str, str],
    *,
    worktree: Path,
    run_dir: Path,
    model: str,
    codex_home: Path,
    codex_sqlite_home: Path | None = None,
) -> dict[str, str]:
    environment = {
        key: value for key, value in source.items() if key in ELIM_ENVIRONMENT_ALLOWLIST
    }
    environment.update(
        {
            "ARRP_TRANSACTION_WORKTREE": str(worktree),
            "ARRP_RUN_DIR": str(run_dir),
            "ARRP_ELIM_MODEL": model,
            "CODEX_HOME": str(codex_home),
            "CODEX_SQLITE_HOME": str(codex_sqlite_home or codex_home),
        }
    )
    return environment


def trusted_codex_auth_home() -> Path:
    """Return Benjamin's exact owner-only Codex authentication home."""

    home = (Path.home() / ".codex").resolve()
    auth = home / "auth.json"
    info = auth.lstat()
    if (
        auth.is_symlink()
        or not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.getuid()
        or bool(stat.S_IMODE(info.st_mode) & 0o077)
    ):
        raise TransactionError("trusted Codex authentication file is unsafe")
    return home


def run_sealed_elim_process(
    command: Sequence[str],
    *,
    worktree: Path,
    environment: Mapping[str, str],
    prompt: bytes,
    timeout_seconds: int,
    jsonl_path: Path,
) -> subprocess.CompletedProcess[bytes]:
    """Run one process group and preserve its JSONL before any failure returns."""

    if timeout_seconds <= 0:
        raise TransactionError("sealed Elim timeout must be positive")
    process = subprocess.Popen(
        list(command),
        cwd=worktree,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=dict(environment),
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(input=prompt, timeout=timeout_seconds)
    except subprocess.TimeoutExpired as error:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        atomic_write_bytes(jsonl_path, stdout or b"")
        raise TransactionError(
            f"sealed fixture Elim timed out after {timeout_seconds} seconds"
        ) from error
    atomic_write_bytes(jsonl_path, stdout)
    return subprocess.CompletedProcess(
        list(command),
        process.returncode,
        stdout,
        stderr,
    )


def sealed_elim_command(
    *,
    codex: Path,
    worktree: Path,
    run_dir: Path,
    model: str,
    schema: Path,
) -> tuple[str, ...]:
    auth_home = (Path.home() / ".codex").resolve()
    keychain_home = (Path.home() / "Library/Keychains").resolve()
    command = [
        str(codex),
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--cd",
        str(worktree),
        "--model",
        model,
        "-c",
        'approval_policy="never"',
        "-c",
        'default_permissions="arrp_elim"',
        "-c",
        'permissions.arrp_elim.extends=":workspace"',
        "-c",
        (
            "permissions.arrp_elim.filesystem."
            f"{json.dumps(str(auth_home))}=\"deny\""
        ),
        "-c",
        'permissions.arrp_elim.filesystem."/usr/bin/security"="deny"',
        "-c",
        (
            "permissions.arrp_elim.filesystem."
            f"{json.dumps(str(keychain_home))}=\"deny\""
        ),
        "-c",
        "permissions.arrp_elim.network.enabled=false",
        "-c",
        'shell_environment_policy.inherit="none"',
        "-c",
        'shell_environment_policy.set={PATH="/usr/bin:/bin"}',
        "-c",
        "allow_login_shell=false",
        "-c",
        "project_doc_max_bytes=0",
    ]
    for feature in SEALED_DISABLED_FEATURES:
        command.extend(("--disable", feature))
    command.extend(
        (
            "--output-schema",
            str(schema),
            "--output-last-message",
            str(run_dir / "elim-result.json"),
            "-",
        )
    )
    return tuple(command)


def validate_sealed_feature_readback(text: str) -> None:
    observed: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            observed[parts[0]] = parts[-1]
    unsafe = [
        feature
        for feature in SEALED_DISABLED_FEATURES
        if observed.get(feature) != "false"
    ]
    if unsafe:
        raise TransactionError(f"sealed Codex features are not disabled: {unsafe}")


def git_metadata_snapshot(worktree: Path) -> dict[str, str]:
    git_pointer = worktree / ".git"
    pointer_bytes = git_pointer.read_bytes() if git_pointer.is_file() else b""
    index_state = git(
        worktree,
        "ls-files",
        "-v",
        "--stage",
        "-z",
    ).stdout
    refs = git(
        worktree,
        "for-each-ref",
        "--format=%(refname)%00%(objectname)",
    ).stdout
    return {
        "head": git_text(worktree, "rev-parse", "HEAD"),
        "branch": git_text(worktree, "rev-parse", "--abbrev-ref", "HEAD"),
        "index_sha256": hashlib.sha256(index_state).hexdigest(),
        "refs_sha256": hashlib.sha256(refs).hexdigest(),
        "git_pointer_sha256": hashlib.sha256(pointer_bytes).hexdigest(),
    }


def validate_elim_result_boundary(
    value: Mapping[str, Any],
    *,
    run_id: str,
    unit_id: str,
    files_touched: Sequence[str],
    source_revision: str | None = None,
    allow_github_actions: bool = False,
) -> None:
    if value.get("run_id") != run_id or value.get("unit_id") != unit_id:
        raise TransactionError("Elim result does not match the selected run and unit")
    if value.get("commit") is not None or value.get("synchronization") != []:
        raise TransactionError("Elim claimed forbidden Git or synchronization authority")
    action_requests = value.get("github_action_requests")
    if not allow_github_actions and action_requests != []:
        raise TransactionError("sealed local phases require github_action_requests to be empty")
    if allow_github_actions:
        if not isinstance(action_requests, list) or source_revision is None:
            raise TransactionError("broker-enabled result requires typed action requests and revision")
        for action in action_requests:
            validate_broker_intent(action, source_revision=source_revision)
    incident_reports = value.get("incident_reports")
    if not isinstance(incident_reports, list) or len(incident_reports) > 16:
        raise TransactionError("Elim result requires a bounded incident_reports array")
    try:
        for report in incident_reports:
            validate_incident_report(report)
    except IncidentContractError as error:
        raise TransactionError(f"Elim incident report is invalid: {error}") from error
    declared = value.get("files_touched")
    if not isinstance(declared, list) or sorted(declared) != sorted(files_touched):
        raise TransactionError("Elim files_touched does not equal the exact worktree delta")
    for path in declared:
        if not isinstance(path, str) or classify_path(path, None, tracked=True) != "ordinary":
            raise TransactionError(f"Elim touched a protected or prohibited path: {path}")


def record_run_chain_incidents(
    incident_path: Path,
    chain: Mapping[str, Any],
    *,
    run_id: str,
) -> list[dict[str, Any]]:
    """Record typed failed/degraded occurrences without browser inference."""

    recorded: list[dict[str, Any]] = []
    for index, item in enumerate(
        [
            *[
                {**row, "impact": "blocking"}
                for row in chain.get("failures") or []
                if isinstance(row, Mapping)
            ],
            *[
                {**row, "impact": "degraded"}
                for row in chain.get("degradations") or []
                if isinstance(row, Mapping)
            ],
        ],
        1,
    ):
        stage = str(item.get("stage") or "run-coordinator-bot")
        failure_class = str(item.get("classification") or item["impact"])
        diagnostic = str(item.get("message") or "No diagnostic was recorded.")
        recorded.append(
            record_incident_occurrence(
                incident_path,
                component=stage,
                prerequisite=stage,
                failure_class=failure_class,
                impact=str(item["impact"]),
                summary=(
                    "Scheduled automation stage failed or was prevented."
                    if item["impact"] == "blocking"
                    else "Scheduled automation stage completed in degraded mode."
                ),
                reported_by="Run Coordinator",
                owner=None,
                recommended_owner=stage,
                next_action="Inspect the exact run occurrence and restore the failed prerequisite.",
                occurrence_id=f"{run_id}:chain:{index}:{stage}",
                observed_at=str(
                    item.get("recorded_at")
                    or chain.get("completed_at")
                    or chain.get("generated_at")
                    or iso_utc()
                ),
                source_ref=f"run:{run_id}",
                diagnostic=diagnostic,
                run_id=run_id,
                evidence_refs=[f"run:{run_id}"],
                active_links=[f"automation-role:{stage}"],
            )
        )
    return recorded


def default_local_stage_specs(python: str | None = None) -> tuple[LocalStageSpec, ...]:
    """Return the retained deterministic entry points in contract order."""

    interpreter = python or sys.executable
    return (
        LocalStageSpec(
            "case-monitor-bot",
            24,
            "blocking",
            (
                interpreter,
                "{worktree}/scripts/check_case_updates.py",
                "--apply",
                "--summary",
                "{run_dir}/stages/case-monitor-bot/summary.md",
                "--report-json",
                "{run_dir}/stages/case-monitor-bot/report.json",
            ),
            ("{run_dir}/stages/case-monitor-bot/report.json",),
        ),
        LocalStageSpec(
            "presidential-directives-bot",
            24,
            "blocking",
            (
                interpreter,
                "{worktree}/scripts/check_presidential_directives.py",
                "--apply",
                "--summary",
                "{run_dir}/stages/presidential-directives-bot/summary.md",
                "--report-json",
                "{run_dir}/stages/presidential-directives-bot/report.json",
            ),
            ("{run_dir}/stages/presidential-directives-bot/report.json",),
        ),
        LocalStageSpec(
            "source-checker-bot",
            168,
            "degraded",
            (
                interpreter,
                "{worktree}/scripts/check_source_urls.py",
                "--json-output",
                "{run_dir}/stages/source-checker-bot/report.json",
                "--markdown-output",
                "{worktree}/framework/status/source-checker-report.md",
            ),
            ("{run_dir}/stages/source-checker-bot/report.json",),
        ),
        LocalStageSpec(
            "public-intake",
            None,
            "degraded",
            (
                interpreter,
                "{worktree}/scripts/collect_public_intake.py",
                "--output",
                "{run_dir}/stages/public-intake/report.json",
            ),
            ("{run_dir}/stages/public-intake/report.json",),
        ),
        LocalStageSpec(
            "project-console-progress-bot",
            24,
            "blocking",
            (
                interpreter,
                "{worktree}/scripts/build_project_console_progress.py",
                "--config",
                "{worktree}/framework/project/interfaces/project-console/configuration/progress.json",
                "--registry",
                "{worktree}/inventory/github_issue_registry.csv",
                "--output",
                "{run_dir}/stages/project-console-progress-bot/data",
                "--token-env",
                "ARRP_PROJECT_TOKEN",
            ),
            (
                "{run_dir}/stages/project-console-progress-bot/data/progress.json",
            ),
        ),
        LocalStageSpec(
            "project-integrity-bot",
            None,
            "blocking",
            (
                interpreter,
                "{worktree}/scripts/audit_project_consistency.py",
                "--routing-authority",
                "production-transaction",
                "--json-output",
                "{run_dir}/stages/project-integrity-bot/report.json",
                "--markdown-output",
                "{worktree}/framework/status/project-integrity-report.md",
                "--exit-zero-on-findings",
            ),
            ("{run_dir}/stages/project-integrity-bot/report.json",),
        ),
    )


def default_post_elim_validation_specs(
    python: str = "python3",
    venv_python: str = ".venv/bin/python",
) -> tuple[ValidationSpec, ...]:
    """Return the contract-bound local generation and validation command set."""

    return (
        ValidationSpec(
            "integrity-final-report",
            (
                python,
                "scripts/audit_project_consistency.py",
                "--routing-authority",
                "production-transaction",
                "--json-output",
                ".tmp/project-integrity-final.json",
                "--markdown-output",
                "framework/status/project-integrity-report.md",
                "--exit-zero-on-findings",
            ),
        ),
        ValidationSpec(
            "integrity-final-feed",
            (
                python,
                "scripts/build_project_integrity_feed.py",
                "--report",
                ".tmp/project-integrity-final.json",
                "--existing-file",
                "framework/project/interfaces/project-console/data/integrity.js",
                "--output",
                ".tmp/project-console-integrity.json",
            ),
        ),
        ValidationSpec(
            "console-build",
            (python, "scripts/build_project_console.py", "--refresh-github"),
        ),
        ValidationSpec(
            "site-prepare",
            (venv_python, "scripts/prepare_public_site.py"),
        ),
        ValidationSpec(
            "site-build",
            (
                venv_python,
                "-m",
                "mkdocs",
                "build",
                "--strict",
                "--config-file",
                ".site-build/mkdocs.yml",
            ),
        ),
        ValidationSpec(
            "python-tests",
            (python, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"),
        ),
        ValidationSpec(
            "console-tests",
            ("node", "--test", "tests/project-console/frontend.test.mjs"),
        ),
        ValidationSpec(
            "participation-tests",
            ("node", "--test", "tests/participation/*.test.js"),
        ),
        ValidationSpec(
            "python-compile",
            (python, "-m", "compileall", "-q", "scripts", "tests"),
        ),
        ValidationSpec("diff-check", ("git", "diff", "--check")),
        ValidationSpec(
            "launchagent-template",
            ("plutil", "-lint", "framework/project/automation/configuration/launchd/com.thorncrag.arrp-nightly.plist.example"),
        ),
    )


def expand_validation_command(
    worktree: Path,
    command: Sequence[str],
) -> tuple[str, ...]:
    expanded: list[str] = []
    for value in command:
        if "*" not in value or "/" not in value:
            expanded.append(value)
            continue
        matches = sorted(
            str(path.relative_to(worktree))
            for path in worktree.glob(value)
            if path.is_file() and not path.is_symlink()
        )
        if not matches:
            raise TransactionError(f"validation glob matched no files: {value}")
        expanded.extend(matches)
    return tuple(expanded)


def _validation_count(output: bytes) -> int | None:
    text = output.decode("utf-8", "replace")
    matches = (
        re.search(r"\bRan ([0-9]+) tests?\b", text),
        re.search(r"(?m)^# tests ([0-9]+)$", text),
    )
    for match in matches:
        if match:
            return int(match.group(1))
    return None


def run_validation_specs(
    *,
    worktree: Path,
    run_dir: Path,
    specs: Sequence[ValidationSpec],
    environment: Mapping[str, str] | None = None,
    environment_by_spec: Mapping[str, Mapping[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """Run and record the bound validation set without persisting command output."""

    records: list[dict[str, Any]] = []
    for spec in specs:
        command = expand_validation_command(worktree, spec.command)
        spec_environment = dict(environment or os.environ)
        spec_environment.update(
            (environment_by_spec or {}).get(spec.identifier, {})
        )
        spec_environment["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            command,
            cwd=worktree,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=spec_environment,
        )
        combined = result.stdout + b"\n" + result.stderr
        record = {
            "id": spec.identifier,
            "command": list(command),
            "returncode": result.returncode,
            "count": _validation_count(combined),
            "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
        }
        records.append(record)
        if result.returncode:
            atomic_write_json(run_dir / "validation-results.json", records)
            raise TransactionError(
                f"validation command failed: {spec.identifier} ({result.returncode})"
            )
    atomic_write_json(run_dir / "validation-results.json", records)
    return records


def _run_fixture_command(
    command: Sequence[str],
    *,
    worktree: Path,
    run_dir: Path,
    environment: Mapping[str, str],
) -> None:
    rendered = [
        _render_stage_value(value, worktree, run_dir) for value in command
    ]
    result = subprocess.run(
        rendered,
        cwd=worktree,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=dict(environment),
    )
    if result.returncode:
        raise TransactionError(
            f"fixture command exited {result.returncode}: "
            + result.stderr.decode("utf-8", "replace")[:500]
        )


def _manifest_path_state(repository: Path) -> dict[str, tuple[str, int | None, str | None]]:
    return {
        record.path: (record.status, record.mode, record.sha256)
        for record in status_manifest(repository)
    }


def read_p5_supervised_plan(path: Path) -> dict[str, Any]:
    """Read an owner-only explicit live-fixture plan outside the repository."""

    resolved = path.resolve()
    info = resolved.stat()
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o600
    ):
        raise TransactionError("P5 supervised plan must be an owner-only 0600 file")
    repository = Path("/Users/benjaminsmith/Automation Workspaces/ARRP").resolve()
    if _is_within(resolved, repository):
        raise TransactionError("P5 supervised plan must remain outside the repository")
    plan = read_json_object(resolved)
    required_plan = {
        "contract_phase",
        "authorization",
        "stages",
        "queue_command",
        "context_command",
        "elim",
        "post_commands",
        "validation_commands",
        "publication",
    }
    if set(plan) != required_plan:
        raise TransactionError("P5 supervised plan fields are not exact")
    if plan.get("contract_phase") != P5_SUPERVISED_PHASE:
        raise TransactionError("P5 supervised plan has the wrong contract phase")
    if plan.get("authorization") != P5_SUPERVISED_AUTHORIZATION:
        raise TransactionError("P5 supervised plan lacks exact owner authorization")
    publication = plan.get("publication")
    if not isinstance(publication, dict):
        raise TransactionError("P5 supervised plan lacks publication configuration")
    required_publication = {
        "app_identity_file",
        "check_timeout_seconds",
        "pages_timeout_seconds",
        "poll_seconds",
        "pull_request_title",
        "pull_request_body",
        "project_fixture",
    }
    if set(publication) != required_publication:
        raise TransactionError("P5 publication configuration fields are not exact")
    for name in ("check_timeout_seconds", "pages_timeout_seconds"):
        if not isinstance(publication[name], int) or publication[name] <= 0:
            raise TransactionError(f"P5 publication {name} is invalid")
    if (
        not isinstance(publication["poll_seconds"], (int, float))
        or publication["poll_seconds"] < 0
    ):
        raise TransactionError("P5 publication poll_seconds is invalid")
    for name in ("app_identity_file", "pull_request_title", "pull_request_body"):
        if not isinstance(publication[name], str) or not publication[name]:
            raise TransactionError(f"P5 publication {name} is invalid")
    if publication["project_fixture"] is not None and not isinstance(
        publication["project_fixture"], dict
    ):
        raise TransactionError("P5 Project fixture is invalid")
    return plan


def run_p2_fixture_cycle(
    config: RunnerConfig,
    transaction: TransactionResult,
    plan_path: Path,
    *,
    supervised: bool = False,
) -> dict[str, Any]:
    """Run a complete P2 cycle against an explicit fixture or supervised plan."""

    if transaction.worktree_path is None:
        raise TransactionError("P2 cycle requires a prepared transaction worktree")
    plan = read_json_object(plan_path)
    if supervised:
        if not config.supervised_live:
            raise TransactionError("P5 supervision is not enabled in runner configuration")
        if (
            plan.get("contract_phase") != P5_SUPERVISED_PHASE
            or plan.get("authorization") != P5_SUPERVISED_AUTHORIZATION
        ):
            raise TransactionError("P5 supervised cycle lacks exact authorization")
    elif config.fixture_root is None:
        raise TransactionError("P2 fixture cycle requires fixture mode")
    run_dir = config.state_root / "runs" / transaction.run_id
    worktree = Path(transaction.worktree_path).resolve()
    environment = dict(os.environ)
    raw_specs = plan.get("stages")
    if not isinstance(raw_specs, list):
        raise TransactionError("fixture plan stages must be an array")
    specs = tuple(
        LocalStageSpec(
            str(row["id"]),
            row.get("cadence_hours"),
            str(row["failure_class"]),
            tuple(str(value) for value in row["command"]),
            tuple(str(value) for value in row["outputs"]),
        )
        for row in raw_specs
    )
    if tuple(spec.identifier for spec in specs) != LOCAL_STAGE_ORDER:
        raise TransactionError("fixture plan stage order differs from the contract")
    last_success_path = config.state_root / "last-success.json"
    last_success = (
        read_json_object(last_success_path) if last_success_path.exists() else {}
    )
    results = run_local_stages(
        worktree=worktree,
        run_dir=run_dir,
        state_root=config.state_root,
        specs=specs,
        last_success=last_success,
        environment=environment,
    )
    if any(result.status == "failed" for result in results):
        raise TransactionError("blocking deterministic fixture stage failed")
    for key in ("queue_command", "context_command"):
        command = plan.get(key)
        if not isinstance(command, list) or not command:
            raise TransactionError(f"fixture plan lacks {key}")
        _run_fixture_command(
            [str(value) for value in command],
            worktree=worktree,
            run_dir=run_dir,
            environment=environment,
        )
    elim = plan.get("elim")
    if not isinstance(elim, dict):
        raise TransactionError("fixture plan lacks sealed Elim configuration")
    codex = Path(str(elim["codex"])).resolve()
    schema = _resolve_inside(worktree, str(elim["schema"]))
    codex_sqlite_home = run_dir / "codex-home"
    ensure_owner_directory(codex_sqlite_home)
    codex_home = trusted_codex_auth_home() if supervised else codex_sqlite_home
    sealed_environment = sealed_elim_environment(
        environment,
        worktree=worktree,
        run_dir=run_dir,
        model=str(elim["model"]),
        codex_home=codex_home,
        codex_sqlite_home=codex_sqlite_home,
    )
    feature_command = [str(codex), "features", "list"]
    for feature in SEALED_DISABLED_FEATURES:
        feature_command.extend(("--disable", feature))
    feature_environment = dict(sealed_environment)
    feature_environment["CODEX_HOME"] = str(codex_sqlite_home)
    feature_readback = subprocess.run(
        feature_command,
        cwd=worktree,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=feature_environment,
    )
    if feature_readback.returncode:
        raise TransactionError("sealed Codex feature readback failed")
    validate_sealed_feature_readback(
        feature_readback.stdout.decode("utf-8", "strict")
    )
    before_git = git_metadata_snapshot(worktree)
    before_paths = _manifest_path_state(worktree)
    command = sealed_elim_command(
        codex=codex,
        worktree=worktree,
        run_dir=run_dir,
        model=str(elim["model"]),
        schema=schema,
    )
    process = run_sealed_elim_process(
        command,
        worktree=worktree,
        prompt=str(elim["prompt"]).encode("utf-8"),
        environment=sealed_environment,
        timeout_seconds=int(elim.get("timeout_seconds", 60)),
        jsonl_path=run_dir / "elim.jsonl",
    )
    if process.returncode:
        raise TransactionError(
            f"sealed fixture Elim exited {process.returncode}: "
            + process.stderr.decode("utf-8", "replace")[:500]
        )
    after_git = git_metadata_snapshot(worktree)
    if after_git != before_git:
        raise TransactionError("Elim changed Git metadata")
    after_paths = _manifest_path_state(worktree)
    touched = sorted(
        path
        for path in set(before_paths) | set(after_paths)
        if before_paths.get(path) != after_paths.get(path)
    )
    result_path = run_dir / "elim-result.json"
    result = read_json_object(result_path)
    validate_elim_result_boundary(
        result,
        run_id=transaction.run_id,
        unit_id=str(elim["unit_id"]),
        files_touched=touched,
    )
    record_incident_reports(
        config.state_root / "records" / "automation" / "operational-incidents.jsonl",
        result["incident_reports"],
        run_id=transaction.run_id,
    )
    status_path = config.state_root / "status.json"
    if status_path.exists():
        status_document = read_json_object(status_path)
        write_status(
            config,
            status_document,
            stage="09_elim",
            elim_unit=str(elim["unit_id"]),
            elim_outcome=str(result["outcome"]),
        )
    success = last_success_document(
        config.state_root, run_dir, results, run_id=transaction.run_id
    )
    atomic_write_json(last_success_path, success)
    return {
        "schema_version": 1,
        "phase": "P2",
        "run_id": transaction.run_id,
        "publication_attempted": False,
        "stage_results": [result.__dict__ for result in results],
        "queue": str(run_dir / "queue.json"),
        "context": str(run_dir / "context.json"),
        "elim_result": str(result_path),
        "elim_unit": str(elim["unit_id"]),
        "elim_outcome": str(result["outcome"]),
        "files_touched": touched,
        "git_metadata_immutable": True,
        "persistent_session_required": False,
    }


def run_p3_fixture_cycle(
    config: RunnerConfig,
    transaction: TransactionResult,
    plan_path: Path,
    *,
    supervised: bool = False,
) -> dict[str, Any]:
    """Run P2 plus post-generation, validation, and a proved local-only commit."""

    if transaction.worktree_path is None:
        raise TransactionError("P3 cycle requires a prepared transaction worktree")
    if not supervised and config.fixture_root is None:
        raise TransactionError("P3 fixture cycle requires fixture mode")
    plan = read_json_object(plan_path)
    p2 = run_p2_fixture_cycle(
        config,
        transaction,
        plan_path,
        supervised=supervised,
    )
    worktree = Path(transaction.worktree_path).resolve()
    run_dir = config.state_root / "runs" / transaction.run_id
    environment = dict(os.environ)
    command_results: list[dict[str, Any]] = []
    for group_name in ("post_commands", "validation_commands"):
        commands = plan.get(group_name, [])
        if not isinstance(commands, list):
            raise TransactionError(f"P3 fixture plan {group_name} must be an array")
        for index, command in enumerate(commands):
            if not isinstance(command, list) or not command:
                raise TransactionError(
                    f"P3 fixture plan {group_name}[{index}] must be a command array"
                )
            _run_fixture_command(
                [str(value) for value in command],
                worktree=worktree,
                run_dir=run_dir,
                environment=environment,
            )
            command_results.append(
                {"group": group_name, "index": index, "result": "passed"}
            )
    commit = create_local_final_commit(
        worktree,
        run_dir,
        message=f"ARRP nightly automation {utc_now().date().isoformat()}",
        path_authority=routing_path_authority(
            config,
            worktree,
            output_root=run_dir,
        ),
    )
    return {
        "schema_version": 1,
        "phase": "P5" if supervised else "P3",
        "run_id": transaction.run_id,
        "publication_attempted": False,
        "p2": p2,
        "commands": command_results,
        "final_commit": commit,
    }


def _run_production_command(
    command: Sequence[str],
    *,
    cwd: Path,
    accepted: frozenset[int] = frozenset({0}),
    environment: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    process_environment = dict(environment or os.environ)
    process_environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        list(command),
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=process_environment,
    )
    if result.returncode not in accepted:
        raise TransactionError(
            f"production command failed ({result.returncode}): "
            + result.stderr.decode("utf-8", "replace")[:500]
        )
    return result


def _stage_output_from_envelope(
    state_root: Path,
    envelope_path: Path,
) -> Path:
    envelope = read_json_object(envelope_path)
    outputs = envelope.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        raise TransactionError("stage result lacks a typed output")
    relative = outputs[0].get("path") if isinstance(outputs[0], dict) else None
    if not isinstance(relative, str) or not relative:
        raise TransactionError("stage result output path is invalid")
    output = (state_root / relative).resolve()
    if not _is_within(output, state_root.resolve()) or not output.is_file():
        raise TransactionError("stage result output is outside owner state")
    if file_sha256(output) != outputs[0].get("sha256"):
        raise TransactionError("stage result output hash does not match")
    return output


def _production_stage_outputs(
    state_root: Path,
    results: Sequence[LocalStageResult],
    last_success: Mapping[str, Any],
) -> dict[str, Path]:
    outputs: dict[str, Path] = {}
    prior = last_success.get("stages")
    prior = prior if isinstance(prior, Mapping) else {}
    for result in results:
        envelope: Path | None = None
        if result.envelope is not None:
            envelope = Path(result.envelope).resolve()
        elif result.status == "not_due":
            record = prior.get(result.identifier)
            if isinstance(record, Mapping) and isinstance(record.get("envelope"), str):
                envelope = (state_root / record["envelope"]).resolve()
                if file_sha256(envelope) != record.get("sha256"):
                    raise TransactionError(
                        f"prior stage envelope hash differs: {result.identifier}"
                    )
        if envelope is not None:
            try:
                outputs[result.identifier] = _stage_output_from_envelope(
                    state_root,
                    envelope,
                )
            except TransactionError:
                if result.status != "degraded":
                    raise
    return outputs


def _mirror_production_inputs(
    run_dir: Path,
    stage_outputs: Mapping[str, Path],
) -> dict[str, Path]:
    inputs = run_dir / "inputs"
    ensure_owner_directory(inputs)
    mirrored: dict[str, Path] = {}
    for identifier, source in stage_outputs.items():
        destination = inputs / f"{identifier}.json"
        atomic_write_bytes(destination, source.read_bytes())
        mirrored[identifier] = destination
    return mirrored


def _usage_remaining(
    runtime: Path,
    worktree: Path,
    run_id: str,
    reserve_percent: int,
    baseline_root: Path,
) -> float | None:
    result = _run_production_command(
        (
            sys.executable,
            str(runtime / "scripts/check_codex_usage_reserve.py"),
            "--reserve-percent",
            str(reserve_percent),
            "--soft-target-percent",
            str(reserve_percent),
            "--run-baseline-id",
            run_id,
            "--baseline-root",
            str(baseline_root),
        ),
        cwd=worktree,
        accepted=frozenset({0, 2, 3}),
    )
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    remaining = value.get("lowestRemainingPercent") if isinstance(value, dict) else None
    return float(remaining) if isinstance(remaining, (int, float)) else None


def execute_production_semantic_actions(
    requests: Sequence[Mapping[str, Any]],
    *,
    source_revision: str,
    github_token: SensitiveValue,
) -> list[dict[str, Any]]:
    """Execute validated intents after PR checks and before exact-head merge."""

    accepted_requests = [
        validate_broker_intent(request, source_revision=source_revision)
        for request in requests
    ]
    for accepted in accepted_requests:
        preflight_semantic_broker_disclosure(accepted)
    project_token = None
    if any(
        request.get("operation_type") == "set_project_field"
        or (
            request.get("operation_type") == "read_state"
            and decode_broker_target(
                "read_state", request.get("target_node_or_number")
            ).get("kind")
            == "project_field"
        )
        for request in accepted_requests
    ):
        project_token = read_keychain_secret(
            GITHUB_PROJECT_KEYCHAIN_SERVICE,
            GITHUB_PROJECT_KEYCHAIN_ACCOUNT,
        )
    return [
        execute_semantic_broker_intent(
            request,
            source_revision=source_revision,
            github_token=github_token,
            project_token=project_token,
        )
        for request in accepted_requests
    ]


def run_production_cycle(
    config: RunnerConfig,
    transaction: TransactionResult,
    runtime: Path,
) -> dict[str, Any]:
    """Run the enabled local-first chain without a fixture or persistent plan."""

    if (
        config.trigger not in {"scheduled", "manual"}
        or config.runtime_commit is None
        or transaction.worktree_path is None
        or transaction.fetched_origin_main != config.runtime_commit
    ):
        raise TransactionError("production cycle lacks exact runtime/transaction binding")
    worktree = Path(transaction.worktree_path).resolve()
    run_dir = config.state_root / "runs" / transaction.run_id
    ensure_owner_directory(run_dir)
    coordinator = runtime / "scripts/run_coordinator.py"
    coordinator_config = worktree / "framework/project/automation/configuration/bots/run-coordinator-bot.json"
    chain = run_dir / "run-chain.json"
    signals = run_dir / "signals.json"
    atomic_write_json(
        signals,
        {
            "allow_elim_launch": True,
            "elim_launch_trigger": config.trigger,
        },
    )
    last_success_path = config.state_root / "last-success.json"
    last_success = (
        read_json_object(last_success_path) if last_success_path.exists() else {}
    )
    plan_command = [
        sys.executable,
        str(coordinator),
        "plan",
        "--config",
        str(coordinator_config),
        "--repo",
        str(worktree),
        "--signals",
        str(signals),
        "--output",
        str(chain),
        "--chain-id",
        transaction.run_id,
        "--run-id",
        transaction.run_id,
        "--trigger",
        config.trigger,
        "--local",
    ]
    if last_success_path.exists():
        previous_chain = prior_run_chain_for_plan(
            config.state_root,
            last_success,
        )
        plan_command.extend(
            ("--previous", str(previous_chain))
        )
    _run_production_command(
        plan_command,
        cwd=worktree,
    )
    project_token = read_keychain_secret(
        GITHUB_PROJECT_KEYCHAIN_SERVICE,
        GITHUB_PROJECT_KEYCHAIN_ACCOUNT,
    )
    app_identity = GitHubAppIdentity.from_json(
        config.state_root / "github-app.json"
    )
    app_private_key = read_keychain_secret(
        GITHUB_APP_KEYCHAIN_SERVICE,
        GITHUB_APP_KEYCHAIN_ACCOUNT,
    )
    app_token = mint_installation_token(app_identity, app_private_key)
    repository_gate_last_good_path = (
        config.state_root / "repository-gates-last-good.json"
    )
    repository_gate_last_good = read_repository_gate_snapshot(
        repository_gate_last_good_path
    )

    def repository_gate_request(path: str) -> Any:
        return github_api_request(
            "GET",
            f"/repos/Thorncrag/ARRP/{path.lstrip('/')}",
            app_token,
        )

    repository_gates = produce_repository_gate_snapshot(
        repository="Thorncrag/ARRP",
        declarations_path=(
            config.state_root / "records" / "automation" / "repository-gates.jsonl"
        ),
        token="",
        last_good=repository_gate_last_good,
        request=repository_gate_request,
    )
    repository_gate_path = run_dir / "repository-gates.json"
    write_repository_gate_snapshot(repository_gate_path, repository_gates)
    if repository_gates.get("complete") is not True:
        raise TransactionError(
            "repository-gate inventory is incomplete; future-run safety cannot be verified"
        )
    write_repository_gate_snapshot(
        repository_gate_last_good_path,
        repository_gates,
    )
    _run_production_command(
        (
            sys.executable,
            str(coordinator),
            "attach-repository-gates",
            "--manifest",
            str(chain),
            "--repository-gates",
            str(repository_gate_path),
        ),
        cwd=worktree,
    )
    attached_gate_snapshot = read_json_object(chain).get("repository_gates") or {}
    blocked_stages: dict[str, str] = {}
    for item in attached_gate_snapshot.get("items") or []:
        if item.get("affected_latest_attempt") is not True:
            continue
        gate_id = str(item.get("gate_id") or "repository-gate")
        reason = str(item.get("reason") or "Repository gate blocks this stage.")
        for stage_id in item.get("affected_stages") or []:
            blocked_stages[str(stage_id)] = f"Repository gate {gate_id}: {reason}"
    production_python = str(config.canonical_path / ".venv/bin/python")
    stage_specs = default_local_stage_specs(production_python)
    stage_environment = dict(os.environ)
    for credential_name in ("ARRP_PROJECT_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        stage_environment.pop(credential_name, None)
    stages = run_local_stages(
        worktree=worktree,
        run_dir=run_dir,
        state_root=config.state_root,
        specs=stage_specs,
        last_success=last_success,
        environment=stage_environment,
        environment_by_stage={
            "public-intake": {
                "GH_TOKEN": app_token.reveal(),
            },
            "project-console-progress-bot": {
                "ARRP_PROJECT_TOKEN": project_token.reveal(),
            },
            "project-integrity-bot": {
                "ARRP_PROJECT_TOKEN": project_token.reveal(),
                "GH_TOKEN": app_token.reveal(),
            },
        },
        runtime_root=runtime,
        runtime_commit=config.runtime_commit,
        blocked_stages=blocked_stages,
    )
    for result in stages:
        command = [
            sys.executable,
            str(coordinator),
            "record",
            "--manifest",
            str(chain),
            "--stage",
            result.identifier,
            "--status",
            result.status,
            "--failure-class",
            (
                    "none"
                    if result.status in {"succeeded", "not_due"}
                    else next(
                        spec.failure_class
                        for spec in stage_specs
                        if spec.identifier == result.identifier
                    )
                ),
            "--details",
            result.reason,
            "--work-count",
            "0",
        ]
        if result.envelope is not None:
            recorded_output = Path(result.envelope)
            if result.status == "succeeded":
                recorded_output = _stage_output_from_envelope(
                    config.state_root,
                    recorded_output,
                )
            command.extend(("--output-file", str(recorded_output)))
        _run_production_command(command, cwd=worktree)
    if any(result.status == "failed" for result in stages):
        raise TransactionError("blocking deterministic production stage failed")

    run_config = read_json_object(coordinator_config)
    reserve = int(run_config["usageGate"]["hardReservePercent"])
    remaining = _usage_remaining(
        runtime,
        worktree,
        transaction.run_id,
        reserve,
        config.state_root / "usage-baselines",
    )
    empty_results = run_dir / "stage-results.json"
    atomic_write_json(empty_results, {})
    finalize = [
        sys.executable,
        str(coordinator),
        "finalize",
        "--config",
        str(coordinator_config),
        "--manifest",
        str(chain),
        "--stage-results",
        str(empty_results),
    ]
    if remaining is not None:
        finalize.extend(("--usage-remaining", str(remaining)))
    _run_production_command(finalize, cwd=worktree)

    outputs = _production_stage_outputs(config.state_root, stages, last_success)
    required = {
        "project-integrity-bot",
        "project-console-progress-bot",
        "public-intake",
    }
    if not required.issubset(outputs):
        raise TransactionError("required production queue inputs are unavailable")
    mirrored = _mirror_production_inputs(run_dir, outputs)
    review_epoch = run_dir / "review-epoch.json"
    atomic_write_json(
        review_epoch,
        read_json_object(chain).get("review_epoch") or {},
    )
    queue = run_dir / "queue.json"
    run_log = (
        config.state_root / "records" / "automation" / "elim-run-log.md"
    )
    gap_obligations = run_dir / "gap-obligations-reconstructed.json"
    atomic_write_json(
        gap_obligations,
        reconstruct_owner_gap_obligations(run_log),
    )
    queue_command = [
        sys.executable,
        str(runtime / "scripts/build_elim_work_queue.py"),
        "--input-root",
        str(run_dir),
        "--repository-root",
        str(worktree),
        "--integrity",
        str(mirrored["project-integrity-bot"]),
        "--progress",
        str(mirrored["project-console-progress-bot"]),
        "--intake",
        str(mirrored["public-intake"]),
        "--chain",
        str(chain),
        "--review-epoch",
        str(review_epoch),
        "--gap-obligations",
        str(gap_obligations),
        "--output",
        str(queue),
    ]
    for identifier, option in (
        ("source-checker-bot", "--source-checker"),
        ("case-monitor-bot", "--case-monitor"),
        ("presidential-directives-bot", "--presidential-directives"),
    ):
        if identifier in mirrored:
            queue_command.extend((option, str(mirrored[identifier])))
    try:
        _run_production_command(
            queue_command,
            cwd=worktree,
            accepted=frozenset({0, 3}),
        )
    except TransactionError as error:
        queue_failure = structured_failure_detail(queue)
        if queue_failure is not None:
            raise TransactionError(
                "Elim work queue blocked: " + queue_failure
            ) from error
        raise

    route = run_dir / "route.json"
    _run_production_command(
        (
            sys.executable,
            str(runtime / "scripts/select_elim_context_route.py"),
            "--queue",
            str(queue),
            "--chain",
            str(chain),
            "--input-root",
            str(run_dir),
            "--output",
            str(route),
        ),
        cwd=worktree,
    )
    selected = read_json_object(route)
    context_path: Path | None = None
    if selected.get("profile"):
        context_path = run_dir / "context.json"
        context_command = [
            sys.executable,
            str(runtime / "scripts/build_elim_context.py"),
            "--path-authority",
            "production-transaction",
            "--input-root",
            str(worktree),
            "--review-epoch-root",
            str(run_dir),
            "--output-root",
            str(run_dir),
            "--output",
            str(context_path),
            "--profile",
            str(selected["profile"]),
            "--work-item-id",
            str(selected.get("work_item_id") or ""),
            "--work-kind",
            str(selected.get("kind") or ""),
            "--review-epoch",
            str(review_epoch),
        ]
        if selected.get("issue"):
            context_command.extend(("--issue", str(selected["issue"])))
        if selected.get("canonical_record"):
            context_command.extend(
                ("--canonical-record", str(selected["canonical_record"]))
            )
        try:
            _run_production_command(context_command, cwd=worktree)
        except TransactionError as error:
            context_failure = structured_failure_detail(context_path)
            if context_failure is not None:
                raise TransactionError(
                    "Elim context blocked: " + context_failure
                ) from error
            raise

    attach = [
        sys.executable,
        str(coordinator),
        "attach-context",
        "--config",
        str(coordinator_config),
        "--manifest",
        str(chain),
        "--queue",
        str(queue),
    ]
    if context_path is not None:
        attach.extend(("--context", str(context_path)))
    _run_production_command(attach, cwd=worktree)
    _run_production_command(finalize, cwd=worktree)
    chain_value = read_json_object(chain)
    incident_path = (
        config.state_root / "records" / "automation" / "operational-incidents.jsonl"
    )
    record_run_chain_incidents(
        incident_path,
        chain_value,
        run_id=transaction.run_id,
    )

    elim_result: dict[str, Any] | None = None
    if (chain_value.get("elim_decision") or {}).get("launch_recommended"):
        unit = (chain_value.get("work_queue") or {}).get("next_item") or {}
        unit_id = str(unit.get("id") or selected.get("work_item_id") or "")
        profile = (chain_value["elim_decision"].get("profile") or {})
        model = str(profile.get("model") or run_config["llmRouting"]["profiles"][
            selected["profile"]
        ]["model"])
        codex_home = trusted_codex_auth_home()
        codex_sqlite_home = run_dir / "codex-home"
        ensure_owner_directory(codex_sqlite_home)
        sealed_environment = sealed_elim_environment(
            os.environ,
            worktree=worktree,
            run_dir=run_dir,
            model=model,
            codex_home=codex_home,
            codex_sqlite_home=codex_sqlite_home,
        )
        feature_command = [str(PRODUCTION_CODEX), "features", "list"]
        for feature in SEALED_DISABLED_FEATURES:
            feature_command.extend(("--disable", feature))
        feature_environment = dict(sealed_environment)
        feature_environment["CODEX_HOME"] = str(codex_sqlite_home)
        feature_readback = _run_production_command(
            feature_command,
            cwd=worktree,
            environment=feature_environment,
        )
        validate_sealed_feature_readback(
            feature_readback.stdout.decode("utf-8", "strict")
        )
        before_git = git_metadata_snapshot(worktree)
        before_paths = _manifest_path_state(worktree)
        command = sealed_elim_command(
            codex=PRODUCTION_CODEX,
            worktree=worktree,
            run_dir=run_dir,
            model=model,
            schema=worktree
            / "framework/project/automation/schemas/elim-work-unit-result.schema.json",
        )
        process = run_sealed_elim_process(
            command,
            worktree=worktree,
            prompt=(
                "Execute only the exact ARRP work unit bound by "
                f"{chain} and {context_path}; run_id={transaction.run_id}; "
                f"unit_id={unit_id}. Return the strict result schema."
            ).encode("utf-8"),
            environment=sealed_environment,
            timeout_seconds=1800,
            jsonl_path=run_dir / "elim.jsonl",
        )
        if process.returncode:
            raise TransactionError(f"sealed production Elim exited {process.returncode}")
        if git_metadata_snapshot(worktree) != before_git:
            raise TransactionError("Elim changed Git metadata")
        after_paths = _manifest_path_state(worktree)
        touched = sorted(
            path
            for path in set(before_paths) | set(after_paths)
            if before_paths.get(path) != after_paths.get(path)
        )
        elim_result = read_json_object(run_dir / "elim-result.json")
        validate_elim_result_boundary(
            elim_result,
            run_id=transaction.run_id,
            unit_id=unit_id,
            files_touched=touched,
            source_revision=config.runtime_commit,
            allow_github_actions=True,
        )
        record_incident_reports(
            incident_path,
            elim_result["incident_reports"],
            run_id=transaction.run_id,
        )

    validation_specs = default_post_elim_validation_specs(
        production_python,
        production_python,
    )
    for spec in validation_specs:
        command = expand_validation_command(worktree, spec.command)
        if len(command) > 1 and command[1].endswith(".py"):
            verify_worktree_entrypoint(
                worktree,
                config.runtime_commit,
                (worktree / command[1]).resolve(),
            )
    validations = run_validation_specs(
        worktree=worktree,
        run_dir=run_dir,
        specs=validation_specs,
        environment=stage_environment,
        environment_by_spec={
            "integrity-final-report": {
                "ARRP_PROJECT_TOKEN": project_token.reveal(),
                "GH_TOKEN": app_token.reveal(),
            },
            "console-build": {
                "ARRP_PROJECT_TOKEN": project_token.reveal(),
            },
        },
    )
    final_commit = create_local_final_commit(
        worktree,
        run_dir,
        message=f"ARRP nightly automation {utc_now().date().isoformat()}",
        path_authority=routing_path_authority(
            config,
            worktree,
            output_root=run_dir,
        ),
        require_active_registry=True,
    )
    success_candidate = last_success_document(
        config.state_root,
        run_dir,
        stages,
        run_id=transaction.run_id,
        previous=last_success,
    )
    return {
        "schema_version": 1,
        "phase": "P6",
        "run_id": transaction.run_id,
        "runtime_commit": config.runtime_commit,
        "stage_results": [result.__dict__ for result in stages],
        "chain": str(chain),
        "queue": str(queue),
        "route": str(route),
        "context": str(context_path) if context_path is not None else None,
        "elim_result": elim_result,
        "semantic_action_requests": (
            elim_result.get("github_action_requests") or []
            if isinstance(elim_result, Mapping)
            else []
        ),
        "validation_results": validations,
        "final_commit": final_commit,
        "last_success_candidate": success_candidate,
        "publication_attempted": False,
    }


@contextlib.contextmanager
def exclusive_lock(
    state_root: Path,
    run_id: str,
    on_error: Callable[[BaseException], None] | None = None,
) -> Iterator[int]:
    ensure_owner_directory(state_root)
    lock_path = state_root / "run.lock"
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    os.fchmod(descriptor, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise TransactionError("another ARRP run owns the operating-system lock") from error
        atomic_write_json(
            state_root / "run-owner.json",
            {"schema_version": SCHEMA_VERSION, "run_id": run_id, "pid": os.getpid()},
        )
        try:
            yield descriptor
        except BaseException as error:
            if on_error is not None:
                on_error(error)
            raise
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def git(
    repository: Path,
    *args: str,
    input_bytes: bytes | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if check and result.returncode:
        raise GitError(args, result)
    return result


def git_text(repository: Path, *args: str) -> str:
    return git(repository, *args).stdout.decode("utf-8", "strict").strip()


def routing_path_authority(
    config: RunnerConfig,
    repository: Path,
    *,
    output_root: Path | None = None,
) -> ProjectPathAuthority:
    """Construct the exact typed routing authority for this transaction phase."""

    repository = repository.resolve()
    try:
        if config.fixture_root is not None:
            return ProjectPathAuthority.fixture(
                config.fixture_root,
                repository_root=repository,
                state_root=config.state_root,
                output_root=output_root or repository,
            )
        if repository == config.canonical_path.resolve():
            return ProjectPathAuthority.production()
        if output_root is None:
            raise TransactionError(
                "transaction routing requires its exact run output root"
            )
        return ProjectPathAuthority.production_transaction(
            repository_root=repository,
            run_root=output_root,
        )
    except PathAuthorityError as error:
        raise TransactionError(
            "Component Registry routing path authority is unavailable"
        ) from error


def governing_protected_paths(
    repository: Path,
    runtime_files: Sequence[str] = RUNTIME_FILES,
    *,
    path_authority: ProjectPathAuthority | None = None,
    require_active_registry: bool = False,
) -> frozenset[str]:
    """Resolve dynamic protected paths from the canonical registry and runtime."""

    repository = repository.resolve()
    protected = set(runtime_files)
    registry_path = repository / "framework/component-registry.json"
    if not registry_path.exists():
        if require_active_registry:
            raise TransactionError(
                "active Component Registry routing is unavailable"
            )
        if path_authority is None:
            raise TransactionError(
                "routing requires a typed path authority"
            )
        if path_authority.repository_root != repository:
            raise TransactionError(
                "routing authority and repository differ"
            )
        predecessor_path = (
            repository
            / ROUTING_PREDECESSOR_PATHS["context_routes_source"][
                "historical_path"
            ]
        )
        if not predecessor_path.exists():
            if path_authority.mode == "fixture":
                return frozenset(protected)
            raise TransactionError(
                "routing authority is unavailable"
            )
        try:
            route = load_route_manifest(
                predecessor_path,
                root=repository,
                verify_hashes=True,
            )
        except (OSError, ValueError, RoutingContextError) as error:
            raise TransactionError(
                "predecessor routing validation failed"
            ) from error
        documents = route.get("documents")
        if not isinstance(documents, dict):
            raise TransactionError(
                "predecessor routing documents must be an object"
            )
        for identifier, document in documents.items():
            if not isinstance(document, dict):
                raise TransactionError(
                    f"invalid predecessor routing document: {identifier}"
                )
            if document.get("governing") is True:
                path = document.get("path")
                if not isinstance(path, str) or not path:
                    raise TransactionError(
                        "governing predecessor routing document lacks path: "
                        f"{identifier}"
                    )
                protected.add(path)
        return frozenset(protected)
    if path_authority is None:
        raise TransactionError(
            "Component Registry routing requires a typed path authority"
        )
    if path_authority.repository_root != repository:
        raise TransactionError(
            "Component Registry routing authority and repository differ"
        )
    try:
        if path_authority.mode == "fixture":
            routing_view = load_fixture_component_registry_routing_view(
                path_authority
            )
        else:
            routing_view = load_validated_component_registry_routing_view(
                path_authority
            )
    except ComponentRegistryError as error:
        raise TransactionError(
            "Component Registry routing validation failed"
        ) from error
    validation_mode = routing_view.get("validation_mode")
    expected_posture = {
        "adopted_configuration_validation": {
            "authoritative": False,
            "executable": False,
            "authority_effective": False,
            "source_revision_authorized": False,
            "source_bytes_current": True,
            "canonical_history_confirmed": False,
            "receipt_trusted": False,
            "runtime_live": "not_checked",
            "activation_receipt_consulted": False,
            "predecessor_route_consulted": False,
        },
        "live_authority_validation": {
            "authoritative": True,
            "executable": False,
            "authority_effective": True,
            "source_revision_authorized": True,
            "source_bytes_current": True,
            "canonical_history_confirmed": True,
            "receipt_trusted": True,
            "runtime_live": "not_checked",
            "activation_receipt_consulted": True,
            "predecessor_route_consulted": False,
        },
    }.get(str(validation_mode))
    if routing_view.get("schema_version") != 4 or expected_posture is None or any(
        routing_view.get(field) is not expected
        for field, expected in expected_posture.items()
    ):
        raise TransactionError(
            "Component Registry routing view has an invalid authority posture"
        )
    if require_active_registry and (
        validation_mode != "live_authority_validation"
    ):
        raise TransactionError(
            "production routing requires live Registry v4 Component Registry "
            "authority with authenticated receipt evidence"
        )
    route = routing_view.get("route")
    documents = route.get("documents") if isinstance(route, Mapping) else None
    if not isinstance(documents, dict):
        raise TransactionError(
            "Component Registry routing documents must be an object"
        )
    for identifier, document in documents.items():
        if not isinstance(document, dict):
            raise TransactionError(
                f"invalid Component Registry routing document: {identifier}"
            )
        if document.get("governing") is True:
            path = document.get("path")
            if not isinstance(path, str) or not path:
                raise TransactionError(
                    "governing Component Registry routing document lacks path: "
                    f"{identifier}"
                )
            protected.add(path)
    return frozenset(protected)


def classify_path(
    path: str,
    mode: int | None,
    *,
    tracked: bool,
    dynamic_protected: frozenset[str] = frozenset(),
) -> str:
    name = Path(path).name
    if (
        name in PRIVATE_NAMES
        or name.startswith(".env.")
        or path.startswith(".tmp/")
        or path.startswith(".git/")
        or "private" in name.lower()
    ):
        return "prohibited"
    if (
        path in dynamic_protected
        or
        path in PROTECTED_EXACT
        or path.startswith(PROTECTED_PREFIXES)
        or path.endswith(".schema.json")
        or path.startswith("requirements")
        or (mode is not None and bool(mode & 0o111))
    ):
        return "protected"
    if tracked:
        return "ordinary"
    if path.startswith(RECOGNIZED_NEW_PREFIXES):
        suffix = Path(path).suffix.lower()
        return "ordinary" if suffix in ORDINARY_NEW_SUFFIXES else "protected"
    return "protected"


def _path_details(repository: Path, path: str) -> tuple[int | None, str | None]:
    target = repository / path
    if not target.exists() and not target.is_symlink():
        return None, None
    info = target.lstat()
    mode = stat.S_IMODE(info.st_mode)
    if stat.S_ISLNK(info.st_mode):
        return mode, None
    if not stat.S_ISREG(info.st_mode):
        return mode, None
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return mode, digest


def status_manifest(
    repository: Path,
    *,
    dynamic_protected: frozenset[str] = frozenset(),
) -> list[PathRecord]:
    output = git(
        repository,
        "status",
        "--porcelain=v2",
        "-z",
        "--untracked-files=all",
    ).stdout
    entries = output.split(b"\0")
    records: list[PathRecord] = []
    index = 0
    while index < len(entries):
        raw = entries[index]
        index += 1
        if not raw:
            continue
        text = raw.decode("utf-8", "surrogateescape")
        old_path: str | None = None
        if text.startswith("1 "):
            parts = text.split(" ", 8)
            status_code, path = parts[1], parts[8]
            tracked = True
        elif text.startswith("2 "):
            parts = text.split(" ", 9)
            status_code, path = parts[1], parts[9]
            if index >= len(entries):
                raise TransactionError("malformed porcelain-v2 rename record")
            old_path = entries[index].decode("utf-8", "surrogateescape")
            index += 1
            tracked = True
        elif text.startswith("u "):
            raise TransactionError("unmerged path in canonical repository")
        elif text.startswith("? "):
            status_code, path, tracked = "??", text[2:], False
        elif text.startswith("! "):
            continue
        else:
            raise TransactionError(f"unknown porcelain-v2 record: {text[:20]}")
        mode, digest = _path_details(repository, path)
        records.append(
            PathRecord(
                path=path,
                status=status_code,
                old_path=old_path,
                mode=mode,
                sha256=digest,
                classification=classify_path(
                    path,
                    mode,
                    tracked=tracked,
                    dynamic_protected=dynamic_protected,
                ),
            )
        )
    return sorted(records, key=lambda item: (item.path, item.old_path or ""))


def manifest_digest(records: Sequence[PathRecord]) -> str:
    encoded = json.dumps(
        [record.as_dict() for record in records],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def manifest_stage_paths(records: Sequence[PathRecord]) -> list[str]:
    return sorted(
        {
            path
            for record in records
            for path in (record.path, record.old_path)
            if path is not None
        }
    )


def reject_unsafe_manifest_entries(
    repository: Path, records: Sequence[PathRecord]
) -> None:
    for record in records:
        target = repository / record.path
        if target.is_symlink():
            raise TransactionError(f"symlink change is prohibited: {record.path}")
        tracked = git_text(repository, "ls-files", "--stage", "--", record.path)
        if tracked.startswith("160000 "):
            raise TransactionError(f"submodule change is prohibited: {record.path}")
        if target.is_file() and b"\0" in target.read_bytes():
            raise TransactionError(f"binary change is prohibited: {record.path}")


def write_prelock_manifest(
    config: RunnerConfig,
    run_id: str,
    *,
    origin: str,
    branch: str,
    head: str,
    records: Sequence[PathRecord],
) -> Path:
    path = config.state_root / "runs" / run_id / "pre-lock-manifest.json"
    atomic_write_json(
        path,
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "canonical_path": str(config.canonical_path.resolve()),
            "origin_url": origin,
            "branch": branch,
            "head": head,
            "trigger": config.trigger,
            "scheduled_for": config.scheduled_for,
            "due": True,
            "due_reason": "fixture" if config.fixture_root else "explicit-manual-dry-run",
            "paths": [record.as_dict() for record in records],
        },
    )
    return path


def _base_status(config: RunnerConfig, run_id: str) -> dict[str, Any]:
    status = {field: None for field in STATUS_FIELDS}
    status.update(
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "trigger": config.trigger,
            "scheduled_for": config.scheduled_for,
            "started_at": iso_utc(),
            "updated_at": iso_utc(),
            "status": "running",
            "control_state": (
                "paused" if pause_requested(config.state_root) else "run"
            ),
            "stage": "00_start",
            "canonical_path": str(config.canonical_path.resolve()),
            "preserved_paths": [],
        }
    )
    return status


def write_status(
    config: RunnerConfig, status_document: dict[str, Any], **updates: Any
) -> None:
    unknown = set(updates) - set(STATUS_FIELDS)
    if unknown:
        raise TransactionError(f"unknown status fields: {sorted(unknown)}")
    candidate = dict(status_document)
    candidate.update(updates)
    candidate["updated_at"] = iso_utc()
    missing = set(STATUS_FIELDS) - set(candidate)
    if missing:
        raise TransactionError(f"missing status fields: {sorted(missing)}")
    atomic_write_json(config.state_root / "status.json", candidate)
    status_document.clear()
    status_document.update(candidate)
    if config.console_projection is not None:
        write_console_status_projection(
            config.state_root / "status.json", config.console_projection
        )


def _callback_summary(
    value: Any,
    *,
    callback_name: str,
) -> dict[str, Any]:
    """Return a bounded plain JSON mapping without exposing invalid contents."""

    if not isinstance(value, Mapping):
        raise TransactionError(f"{callback_name} summary is invalid")
    try:
        encoded = json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        if len(encoded) > 262_144:
            raise ValueError("callback summary exceeds the bounded size")
        normalized = json.loads(encoded)
    except (TypeError, ValueError, OverflowError) as error:
        raise TransactionError(
            f"{callback_name} summary is invalid"
        ) from error
    if not isinstance(normalized, dict):
        raise TransactionError(f"{callback_name} summary is invalid")
    return normalized


def write_console_status_projection(status_path: Path, output: Path | None = None) -> Path:
    value = json.loads(status_path.read_text(encoding="utf-8"))
    # The occurrence document preserves the control posture that existed when
    # that occurrence was recorded.  The owner Console needs the current
    # authoritative posture as a separate access-time fact, so refresh only
    # the projection from the exact state authority without rewriting history.
    value["control_state"] = (
        "paused" if pause_requested(status_path.parent) else "run"
    )
    value["control_state_checked_at"] = iso_utc()
    target = output or status_path.parent / "console/local-automation-status.js"
    ensure_owner_directory(target.parent)
    material = "window.ARRP_LOCAL_AUTOMATION_STATUS = " + json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ) + ";\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(material)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        os.chmod(target, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()
    return target


def claim_scheduled_slot(state_root: Path, scheduled_for: str) -> bool:
    """Update the nonauthoritative scheduled-slot compatibility projection.

    Lifecycle records, not this replaceable projection, determine whether a
    scheduled occurrence has already been attempted.  This helper remains for
    compatibility with existing status consumers only.
    """

    try:
        parsed = datetime.fromisoformat(scheduled_for.replace("Z", "+00:00"))
    except ValueError as error:
        raise TransactionError("scheduled_for is not a valid timestamp") from error
    if parsed.tzinfo is None:
        raise TransactionError("scheduled_for must include a timezone")
    normalized = parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    path = state_root / "last-scheduled-slot.json"
    if path.exists():
        previous = read_json_object(path)
        if previous.get("scheduled_for") == normalized:
            return False
    atomic_write_json(
        path,
        {
            "schema_version": SCHEMA_VERSION,
            "scheduled_for": normalized,
            "claimed_at": iso_utc(),
        },
    )
    return True


def transaction_events_path(config: RunnerConfig) -> Path:
    """Return the one owner-local lifecycle authority for this state root."""

    return config.state_root / "records" / "automation" / "transaction-events.jsonl"


def _scheduled_attempt_group(scheduled_for: str) -> str:
    try:
        parsed = datetime.fromisoformat(scheduled_for.replace("Z", "+00:00"))
    except ValueError as error:
        raise TransactionError("scheduled_for is not a valid timestamp") from error
    if parsed.tzinfo is None:
        raise TransactionError("scheduled_for must include a timezone")
    normalized = parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    # Lifecycle identities are deliberately lower-case and opaque.
    return "scheduled:" + normalized.lower()


def _attempt_group(config: RunnerConfig, run_id: str) -> str:
    if config.attempt_group_id is not None:
        return config.attempt_group_id
    if config.scheduled_for is not None:
        return _scheduled_attempt_group(config.scheduled_for)
    return run_id


def _lifecycle_proof(run_id: str, kind: str, material: Mapping[str, Any]) -> dict[str, str]:
    digest = "sha256:" + hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "proof_digest": digest,
        "evidence_ref": f"owner-local:transaction-evidence/{run_id}:{kind}",
    }


def scheduled_occurrence_exists(events_path: Path, attempt_group_id: str) -> bool:
    """Fail closed if immutable lifecycle history already names this slot."""

    try:
        return any(
            event["attempt_group_id"] == attempt_group_id
            and event["event_type"] != "retry_authorized"
            for event in read_transaction_events(events_path)
        )
    except TransactionLifecycleError as error:
        raise TransactionError("scheduled lifecycle history is unavailable") from error


def _start_lifecycle_attempt(
    config: RunnerConfig,
    *,
    run_id: str,
    branch: str,
    head: str,
    base: str,
) -> str:
    """Append the independent start record before transaction work begins."""

    events_path = transaction_events_path(config)
    attempt_group_id = _attempt_group(config, run_id)
    try:
        start_transaction(
            events_path,
            run_id=run_id,
            attempt_group_id=attempt_group_id,
            attempt_number=config.retry_attempt_number,
            trigger=config.trigger,
            branch=branch,
            head=head,
            base=base,
            logical_worktree_id=run_id,
            logical_run_id=run_id,
            delta_digest="sha256:" + "0" * 64,
            owner="run-coordinator",
            next_action="Run the bounded transaction or preserve its exact failure state.",
            retry_authorization=config.retry_authorization,
        )
    except TransactionLifecycleError as error:
        raise TransactionError("transaction lifecycle start was rejected") from error
    return attempt_group_id


def _transition_lifecycle_failure(config: RunnerConfig, run_id: str, error: BaseException) -> None:
    """Record preservation/recovery without masking the original failure."""

    failure_code = type(error).__name__.lower()
    events_path = transaction_events_path(config)
    current = current_transaction_states(events_path).get(run_id)
    if current is None or current["state"] in {"recoverably_retired", "completed_noop", "completed_published"}:
        return
    if current["state"] == "active":
        transition_transaction(
            events_path,
            run_id=run_id,
            state="failed_preserved",
            owner="run-coordinator",
            next_action="Inspect and preserve the exact failed transaction material.",
            failure_code=failure_code,
        )
        current = {"state": "failed_preserved"}
    if current["state"] == "failed_preserved":
        transition_transaction(
            events_path,
            run_id=run_id,
            state="recovery_pending",
            owner="run-coordinator",
            next_action="Classify, reconcile, or package preserved transaction material.",
            failure_code=failure_code,
        )


def explicit_stage(repository: Path, paths: Sequence[str]) -> None:
    if not paths:
        return
    if any("\0" in path for path in paths):
        raise TransactionError("NUL in repository path")
    material = b"".join(os.fsencode(path) + b"\0" for path in paths)
    git(
        repository,
        "add",
        "--pathspec-from-file=-",
        "--pathspec-file-nul",
        input_bytes=material,
    )
    git(repository, "diff", "--cached", "--check")


def _index_entries(repository: Path) -> dict[str, tuple[str, str]]:
    output = git(repository, "ls-files", "--stage", "-z").stdout
    entries: dict[str, tuple[str, str]] = {}
    for raw in output.split(b"\0"):
        if not raw:
            continue
        metadata, encoded_path = raw.split(b"\t", 1)
        mode, blob, stage = metadata.decode("ascii").split()
        if stage != "0":
            raise TransactionError("unmerged index entry is prohibited")
        path = encoded_path.decode("utf-8", "surrogateescape")
        entries[path] = (mode, blob)
    return entries


def _tree_entry(repository: Path, revision: str, path: str) -> tuple[str, str] | None:
    output = git(repository, "ls-tree", "-z", revision, "--", path).stdout
    if not output:
        return None
    metadata, encoded_path = output.rstrip(b"\0").split(b"\t", 1)
    mode, object_type, blob = metadata.decode("ascii").split()
    observed = encoded_path.decode("utf-8", "surrogateescape")
    if observed != path or object_type != "blob":
        raise TransactionError(f"unsafe tree entry: {path}")
    return mode, blob


def _changed_paths_against(repository: Path, base_commit: str) -> list[tuple[str, str]]:
    output = git(
        repository,
        "diff",
        "--cached",
        "--name-status",
        "-z",
        "--find-renames",
        base_commit,
    ).stdout
    fields = output.split(b"\0")
    rows: list[tuple[str, str]] = []
    index = 0
    while index < len(fields):
        status_bytes = fields[index]
        index += 1
        if not status_bytes:
            continue
        status = status_bytes.decode("ascii")
        if index >= len(fields):
            raise TransactionError("malformed staged name-status output")
        if status.startswith(("R", "C")):
            old_path = fields[index].decode("utf-8", "surrogateescape")
            index += 1
            if index >= len(fields):
                raise TransactionError("malformed staged rename output")
            path = fields[index].decode("utf-8", "surrogateescape")
            index += 1
            rows.append(("D", old_path))
            rows.append(("A", path))
        else:
            path = fields[index].decode("utf-8", "surrogateescape")
            index += 1
            rows.append((status[0], path))
    return sorted(rows, key=lambda row: (row[1], row[0]))


def staged_manifest(
    repository: Path,
    base_commit: str,
    *,
    dynamic_protected: frozenset[str] | None = None,
) -> list[IndexRecord]:
    protected = (
        dynamic_protected
        if dynamic_protected is not None
        else governing_protected_paths(repository)
    )
    index_entries = _index_entries(repository)
    records: list[IndexRecord] = []
    for status_code, path in _changed_paths_against(repository, base_commit):
        entry = index_entries.get(path)
        mode, blob = entry if entry is not None else (None, None)
        base_entry = _tree_entry(repository, base_commit, path)
        if mode == "120000":
            raise TransactionError(f"symlink change is prohibited: {path}")
        if mode == "160000":
            raise TransactionError(f"submodule change is prohibited: {path}")
        if mode is not None and mode.endswith("755"):
            base_mode = base_entry[0] if base_entry else None
            if base_mode != mode:
                raise TransactionError(f"executable mode change is prohibited: {path}")
        classification = classify_path(
            path,
            int(mode, 8) if mode else None,
            tracked=base_entry is not None,
            dynamic_protected=protected,
        )
        records.append(IndexRecord(path, mode, blob, status_code, classification))
    return records


def scan_staged_blobs(
    repository: Path,
    records: Sequence[IndexRecord],
) -> list[dict[str, Any]]:
    """Legacy local-commit scan returning only safe path/line/detector evidence."""

    findings: list[dict[str, Any]] = []
    for record in records:
        if record.blob is None:
            continue
        content = git(repository, "cat-file", "blob", record.blob).stdout
        if b"\0" in content:
            findings.append(
                {
                    "path": record.path,
                    "line": 0,
                    "detector": "binary-content",
                    "finding_id": "LOCAL-BINARY-CONTENT",
                }
            )
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            for detector, pattern in SECRET_DETECTORS:
                if pattern.search(line):
                    findings.append(
                        {
                            "path": record.path,
                            "line": line_number,
                            "detector": detector,
                            "finding_id": (
                                "LOCAL-"
                                + hashlib.sha256(
                                    f"{record.path}\0{line_number}\0{detector}".encode(
                                        "utf-8"
                                    )
                                ).hexdigest()[:12].upper()
                            ),
                        }
                    )
    return findings


def write_final_manifest(
    run_dir: Path,
    *,
    base_commit: str,
    records: Sequence[IndexRecord],
    findings: Sequence[Mapping[str, Any]],
) -> Path:
    path = run_dir / "final-staging-manifest.json"
    atomic_write_json(
        path,
        {
            "schema_version": SCHEMA_VERSION,
            "base_commit": base_commit,
            "records": [record.as_dict() for record in records],
            "secret_private_findings": list(findings),
        },
    )
    return path


def prove_commit_matches_manifest(
    repository: Path,
    commit: str,
    expected: Sequence[IndexRecord],
) -> None:
    parents = git_text(repository, "rev-list", "--parents", "-n", "1", commit).split()
    if len(parents) != 2:
        raise TransactionError("local final commit must have exactly one parent")
    observed_rows = _changed_paths_against_commit(repository, parents[1], commit)
    expected_rows = sorted(
        ((record.status, record.path) for record in expected),
        key=lambda row: (row[1], row[0]),
    )
    if observed_rows != expected_rows:
        raise TransactionError("commit changed paths differ from the staging manifest")
    for record in expected:
        observed = _tree_entry(repository, commit, record.path)
        expected_entry = (
            (record.mode, record.blob)
            if record.mode is not None and record.blob is not None
            else None
        )
        if observed != expected_entry:
            raise TransactionError(f"commit tree entry differs from manifest: {record.path}")


def _changed_paths_against_commit(
    repository: Path,
    base_commit: str,
    commit: str,
) -> list[tuple[str, str]]:
    output = git(
        repository,
        "diff",
        "--name-status",
        "-z",
        "--no-renames",
        base_commit,
        commit,
    ).stdout
    fields = output.split(b"\0")
    rows: list[tuple[str, str]] = []
    index = 0
    while index < len(fields):
        status_bytes = fields[index]
        index += 1
        if not status_bytes:
            continue
        if index >= len(fields):
            raise TransactionError("malformed committed name-status output")
        path = fields[index].decode("utf-8", "surrogateescape")
        index += 1
        rows.append((status_bytes.decode("ascii")[0], path))
    return sorted(rows, key=lambda row: (row[1], row[0]))


def create_local_final_commit(
    repository: Path,
    run_dir: Path,
    *,
    message: str,
    path_authority: ProjectPathAuthority | None = None,
    require_active_registry: bool = False,
) -> dict[str, Any]:
    """Classify, scan, commit, and prove the exact local-only final delta."""

    base_commit = git_text(repository, "rev-parse", "HEAD")
    dynamic_protected = governing_protected_paths(
        repository,
        path_authority=path_authority,
        require_active_registry=require_active_registry,
    )
    records = status_manifest(repository, dynamic_protected=dynamic_protected)
    reject_unsafe_manifest_entries(repository, records)
    prohibited = [
        record.path
        for record in records
        if record.classification in {"prohibited", "unrecognized"}
    ]
    if prohibited:
        raise TransactionError(
            "prohibited paths cannot enter the local final commit: "
            + ", ".join(prohibited)
        )
    explicit_stage(repository, manifest_stage_paths(records))
    manifest = staged_manifest(
        repository,
        base_commit,
        dynamic_protected=dynamic_protected,
    )
    findings = scan_staged_blobs(repository, manifest)
    manifest_path = write_final_manifest(
        run_dir,
        base_commit=base_commit,
        records=manifest,
        findings=findings,
    )
    if findings:
        raise TransactionError(
            "secret/private detector blocked the local final commit; "
            "see redacted path-only manifest"
        )
    if not manifest:
        return {
            "commit": None,
            "manifest": str(manifest_path),
            "classification": {"ordinary": [], "protected": [], "prohibited": []},
            "review_required": False,
        }
    git(repository, "commit", "-m", message)
    commit = git_text(repository, "rev-parse", "HEAD")
    prove_commit_matches_manifest(repository, commit, manifest)
    if status_manifest(repository):
        raise TransactionError("worktree is not clean after local final commit")
    classification = {
        name: [record.path for record in manifest if record.classification == name]
        for name in ("ordinary", "protected", "prohibited")
    }
    return {
        "commit": commit,
        "manifest": str(manifest_path),
        "classification": classification,
        "review_required": bool(classification["protected"]),
    }


def committed_range_manifest(
    repository: Path,
    base_commit: str,
    head_commit: str,
    *,
    path_authority: ProjectPathAuthority | None = None,
    require_active_registry: bool = False,
) -> list[IndexRecord]:
    """Classify the complete publication range, including checkpoint ancestry."""

    routing_repository = (
        path_authority.repository_root
        if require_active_registry
        and path_authority is not None
        and path_authority.mode == "production_canonical"
        else repository
    )
    dynamic_protected = governing_protected_paths(
        routing_repository,
        path_authority=path_authority,
        require_active_registry=require_active_registry,
    )
    records: list[IndexRecord] = []
    for status_code, path in _changed_paths_against_commit(
        repository,
        base_commit,
        head_commit,
    ):
        base_entry = _tree_entry(repository, base_commit, path)
        head_entry = _tree_entry(repository, head_commit, path)
        mode, blob = head_entry if head_entry is not None else (None, None)
        effective_mode = mode or (base_entry[0] if base_entry else None)
        if effective_mode == "120000":
            raise TransactionError(f"symlink change is prohibited: {path}")
        if effective_mode == "160000":
            raise TransactionError(f"submodule change is prohibited: {path}")
        if mode is not None and mode.endswith("755"):
            base_mode = base_entry[0] if base_entry else None
            if base_mode != mode:
                raise TransactionError(f"executable mode change is prohibited: {path}")
        classification = classify_path(
            path,
            int(effective_mode, 8) if effective_mode else None,
            tracked=base_entry is not None,
            dynamic_protected=dynamic_protected,
        )
        records.append(
            IndexRecord(path, mode, blob, status_code, classification)
        )
    return records


def classify_publication_range(
    repository: Path,
    run_dir: Path,
    *,
    base_commit: str,
    head_commit: str,
    path_authority: ProjectPathAuthority | None = None,
    require_active_registry: bool = False,
) -> dict[str, Any]:
    records = committed_range_manifest(
        repository,
        base_commit,
        head_commit,
        path_authority=path_authority,
        require_active_registry=require_active_registry,
    )
    findings = scan_staged_blobs(repository, records)
    prohibited = [
        record.path
        for record in records
        if record.classification in {"prohibited", "unrecognized"}
    ]
    try:
        disclosure_decision = evaluate_outbound_bundle(
            [
                OutboundArtifact(
                    path=record.path,
                    producer="arrp-nightly-publication",
                    content=(
                        git(repository, "cat-file", "blob", record.blob).stdout
                        if record.blob is not None
                        else b""
                    ),
                    removal_only=record.blob is None,
                )
                for record in records
            ],
            operation="git_push",
            source_revision=head_commit,
            complete=True,
        )
    except DisclosureBlocked as error:
        disclosure_decision = error.decision
    atomic_write_json(
        run_dir / "publication-manifest.json",
        {
            "schema_version": SCHEMA_VERSION,
            "base_commit": base_commit,
            "head_commit": head_commit,
            "records": [record.as_dict() for record in records],
            "secret_private_findings": findings,
            "disclosure_decision": disclosure_decision,
        },
    )
    if prohibited:
        raise TransactionError(
            "prohibited paths cannot enter publication: " + ", ".join(prohibited)
        )
    if findings:
        raise DisclosurePreventionError(
            "secret/private detector blocked publication; "
            "see redacted path-only manifest"
        )
    if disclosure_decision.get("allowed") is not True:
        raise DisclosurePreventionError(
            "GitHub disclosure gate blocked publication; "
            "see the redacted disclosure decision in the publication manifest"
        )
    classification = {
        name: [record.path for record in records if record.classification == name]
        for name in ("ordinary", "protected", "prohibited")
    }
    return {
        "base_commit": base_commit,
        "head_commit": head_commit,
        "classification": classification,
        "review_required": bool(classification["protected"]),
        "manifest": str(run_dir / "publication-manifest.json"),
        "disclosure_decision": disclosure_decision,
    }


def assert_canonical_unchanged(
    repository: Path, expected_head: str, expected_manifest_sha256: str
) -> None:
    observed_head = git_text(repository, "rev-parse", "HEAD")
    observed_manifest = manifest_digest(status_manifest(repository))
    if observed_head != expected_head or observed_manifest != expected_manifest_sha256:
        raise TransactionError(
            "post-lock canonical change detected; publication is blocked"
        )


def materialize_reviewed_runtime(
    repository: Path,
    source_commit: str,
    destination: Path,
    runtime_files: Sequence[str] = RUNTIME_FILES,
) -> dict[str, str]:
    ensure_owner_directory(destination)
    hashes: dict[str, str] = {}
    for relative in runtime_files:
        tree_entry = git_text(repository, "ls-tree", source_commit, "--", relative)
        if not tree_entry:
            raise TransactionError(f"reviewed runtime file absent at source commit: {relative}")
        metadata, listed_path = tree_entry.split("\t", 1)
        mode, object_type, object_id = metadata.split()
        if listed_path != relative or object_type != "blob" or mode == "120000":
            raise TransactionError(f"unsafe reviewed runtime entry: {relative}")
        content = git(repository, "show", f"{source_commit}:{relative}").stdout
        target = destination / relative
        ensure_owner_directory(target.parent)
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        file_mode = 0o700 if int(mode, 8) & 0o111 else 0o600
        os.chmod(target, file_mode)
        info = target.stat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or bool(stat.S_IMODE(info.st_mode) & 0o022)
        ):
            raise TransactionError(f"unsafe materialized runtime file: {relative}")
        source_hash = hashlib.sha256(content).hexdigest()
        if hashlib.sha256(target.read_bytes()).hexdigest() != source_hash:
            raise TransactionError(f"reviewed runtime hash mismatch: {relative}")
        hashes[relative] = source_hash
        if git_text(repository, "hash-object", target) != object_id:
            raise TransactionError(f"reviewed runtime blob mismatch: {relative}")
    atomic_write_json(
        destination / "runtime-manifest.json",
        {"schema_version": SCHEMA_VERSION, "source_commit": source_commit, "files": hashes},
    )
    return hashes


def fast_forward_main(repository: Path, expected_origin_main: str) -> str:
    if git_text(repository, "rev-parse", "--abbrev-ref", "HEAD") != "main":
        raise TransactionError("fast-forward sync requires canonical main")
    if status_manifest(repository):
        raise TransactionError("fast-forward sync requires a clean canonical worktree")
    result = git(
        repository,
        "merge",
        "--ff-only",
        expected_origin_main,
        check=False,
    )
    if result.returncode:
        raise GitError(("merge", "--ff-only", expected_origin_main), result)
    observed = git_text(repository, "rev-parse", "HEAD")
    if observed != expected_origin_main:
        raise TransactionError("fast-forward readback did not reach expected origin/main")
    return observed


def remove_successful_transaction_worktree(
    canonical_repository: Path,
    state_root: Path,
    worktree: Path,
) -> None:
    """Remove only a clean, successful transaction worktree under state_root."""

    canonical = canonical_repository.resolve()
    candidate = worktree.resolve()
    expected_parent = (state_root / "worktrees").resolve()
    if candidate == canonical or not _is_within(candidate, expected_parent):
        raise TransactionError("transaction worktree cleanup target is outside state root")
    if not candidate.exists():
        raise TransactionError("transaction worktree cleanup target is missing")
    if status_manifest(candidate):
        raise TransactionError("successful transaction worktree is not clean")
    git(canonical, "worktree", "remove", str(candidate))
    if candidate.exists():
        raise TransactionError("transaction worktree still exists after cleanup")
    registered = git_text(canonical, "worktree", "list", "--porcelain")
    if str(candidate) in registered:
        raise TransactionError("transaction worktree remains registered after cleanup")


def publish_supervised_transaction(
    config: RunnerConfig,
    transaction: TransactionResult,
    cycle_summary: Mapping[str, Any],
    publication: Mapping[str, Any],
    *,
    api_request: Callable[..., Any] = github_api_request,
    graphql_request: Callable[..., dict[str, Any]] = github_graphql_request,
) -> dict[str, Any]:
    """Publish one reviewed P5 transaction and complete exact local readback."""

    if not config.supervised_live or config.trigger != "manual-p5-supervised":
        raise TransactionError("live publication requires exact P5 supervision")
    if (
        transaction.worktree_path is None
        or transaction.branch is None
        or transaction.fetched_origin_main is None
    ):
        raise TransactionError("P5 publication requires a complete transaction")
    if cycle_summary.get("phase") != "P5":
        raise TransactionError("P5 publication received the wrong local cycle")
    worktree = Path(transaction.worktree_path).resolve()
    run_dir = config.state_root / "runs" / transaction.run_id
    expected_head = git_text(worktree, "rev-parse", "HEAD")
    publication_range = classify_publication_range(
        worktree,
        run_dir,
        base_commit=transaction.fetched_origin_main,
        head_commit=expected_head,
        path_authority=routing_path_authority(
            config,
            worktree,
            output_root=run_dir,
        ),
    )
    if publication_range["review_required"]:
        raise TransactionError(
            "the ordinary P5 supervised cycle unexpectedly contains protected paths"
        )
    if not publication_range["classification"]["ordinary"]:
        raise TransactionError("the ordinary P5 supervised cycle has no publishable change")

    identity_path = Path(str(publication["app_identity_file"])).resolve()
    identity = GitHubAppIdentity.from_json(identity_path)
    private_key = read_keychain_secret(
        GITHUB_APP_KEYCHAIN_SERVICE,
        GITHUB_APP_KEYCHAIN_ACCOUNT,
    )
    app_token = mint_installation_token(
        identity,
        private_key,
        api_request=api_request,
    )
    refspec = f"{expected_head}:refs/heads/{transaction.branch}"
    git_push_with_token(
        worktree,
        refspec,
        app_token,
        disclosure_decision=publication_range["disclosure_decision"],
    )
    pull = open_or_update_nightly_pull_request(
        app_token,
        branch=transaction.branch,
        expected_head=expected_head,
        title=str(publication["pull_request_title"]),
        body=str(publication["pull_request_body"]),
        api_request=api_request,
    )
    pull_number = pull.get("number")
    pull_url = pull.get("html_url")
    if not isinstance(pull_number, int) or not isinstance(pull_url, str):
        raise GitHubBrokerError("P5 pull-request readback omitted identity")
    checks = wait_for_required_checks(
        app_token,
        head_sha=expected_head,
        timeout_seconds=int(publication["check_timeout_seconds"]),
        poll_seconds=float(publication["poll_seconds"]),
        api_request=api_request,
    )

    project_result = None
    project_fixture = publication.get("project_fixture")
    if project_fixture is not None:
        project_token = read_keychain_secret(
            GITHUB_PROJECT_KEYCHAIN_SERVICE,
            GITHUB_PROJECT_KEYCHAIN_ACCOUNT,
        )

        def project_graphql(
            query: str,
            variables: Mapping[str, Any],
            token: SensitiveValue,
        ) -> dict[str, Any]:
            return graphql_request(
                query,
                variables,
                token,
                api_request=api_request,
            )

        project_result = run_reversible_project_text_fixture(
            project_fixture,
            project_token,
            read_field=lambda fixture, token: read_project_text_field(
                fixture,
                token,
                graphql_request=project_graphql,
            ),
            write_field=lambda fixture, value, token: write_project_text_field(
                fixture,
                value,
                token,
                graphql_request=project_graphql,
            ),
        )

    merge_sha = merge_exact_head(
        app_token,
        pull_number=pull_number,
        expected_head=expected_head,
        expected_base=transaction.fetched_origin_main,
        protected=False,
        api_request=api_request,
    )
    pages = wait_for_pages_deployment(
        app_token,
        merge_sha=merge_sha,
        timeout_seconds=int(publication["pages_timeout_seconds"]),
        poll_seconds=float(publication["poll_seconds"]),
        api_request=api_request,
    )
    canonical = config.canonical_path.resolve()
    git(canonical, "fetch", "origin", "main")
    observed_origin = git_text(canonical, "rev-parse", "origin/main")
    if observed_origin != merge_sha:
        raise TransactionError("origin/main readback differs from the exact merge commit")
    synchronized = fast_forward_main(canonical, merge_sha)
    remove_successful_transaction_worktree(canonical, config.state_root, worktree)
    return {
        "phase": "P5",
        "publication_attempted": True,
        "publication_range": publication_range,
        "pull_request": {"number": pull_number, "url": pull_url},
        "expected_pr_head": expected_head,
        "required_checks": checks,
        "project_sync": project_result,
        "merge_commit": merge_sha,
        "pages_workflow_run": pages,
        "pages_conclusion": "success",
        "canonical_main": synchronized,
        "worktree_removed": True,
    }


def publish_production_transaction(
    config: RunnerConfig,
    transaction: TransactionResult,
    cycle_summary: Mapping[str, Any],
    *,
    api_request: Callable[..., Any] = github_api_request,
) -> dict[str, Any]:
    """Publish or cleanly close one enabled P6 production transaction."""

    if (
        config.trigger not in {"scheduled", "manual"}
        or transaction.worktree_path is None
        or transaction.branch is None
        or transaction.fetched_origin_main is None
        or cycle_summary.get("phase") != "P6"
    ):
        raise TransactionError("production publication lacks exact cycle binding")
    worktree = Path(transaction.worktree_path).resolve()
    final = cycle_summary.get("final_commit")
    if not isinstance(final, Mapping):
        raise TransactionError("production cycle omitted final commit evidence")
    success_candidate = cycle_summary.get("last_success_candidate")
    if not isinstance(success_candidate, Mapping):
        raise TransactionError("production cycle omitted last-success evidence")
    expected_head = git_text(worktree, "rev-parse", "HEAD")
    run_dir = config.state_root / "runs" / transaction.run_id
    transaction_path_authority = routing_path_authority(
        config,
        worktree,
        output_root=run_dir,
    )
    publication_path_authority = (
        routing_path_authority(
            config,
            config.canonical_path,
            output_root=run_dir,
        )
        if transaction_path_authority.mode == "production_transaction"
        else transaction_path_authority
    )
    publication_range = classify_publication_range(
        worktree,
        run_dir,
        base_commit=transaction.fetched_origin_main,
        head_commit=expected_head,
        path_authority=publication_path_authority,
        require_active_registry=True,
    )
    if final.get("commit") is not None and expected_head != final.get("commit"):
        raise TransactionError("production final commit readback differs")
    if (
        expected_head == transaction.fetched_origin_main
        and not publication_range["classification"]["ordinary"]
        and not publication_range["review_required"]
    ):
        if status_manifest(worktree):
            raise TransactionError("no-op production cycle left a dirty worktree")
        remove_successful_transaction_worktree(
            config.canonical_path,
            config.state_root,
            worktree,
        )
        git(config.canonical_path, "branch", "-d", transaction.branch)
        atomic_write_json(
            config.state_root / "last-success.json",
            success_candidate,
        )
        return {
            "phase": "P6",
            "publication_attempted": False,
            "no_op": True,
            "project_sync": {
                "source": "project-console-progress-bot",
                "readback": "typed-stage-output",
            },
            "canonical_main": git_text(config.canonical_path, "rev-parse", "HEAD"),
            "worktree_removed": True,
            "branch_removed": True,
        }
    if not publication_range["classification"]["ordinary"] and not publication_range[
        "review_required"
    ]:
        raise TransactionError("production cycle has no publishable evidence")
    run_config = read_json_object(
        worktree / "framework/project/automation/configuration/bots/run-coordinator-bot.json"
    )
    publication = run_config.get("publication")
    required = {
        "pullRequestTitle",
        "pullRequestBody",
        "requiredChecksTimeoutSeconds",
        "pagesTimeoutSeconds",
        "pollSeconds",
    }
    if not isinstance(publication, dict) or set(publication) != required:
        raise TransactionError("production publication configuration is not exact")
    require_pull_request_disclosure(
        branch=transaction.branch,
        expected_head=expected_head,
        title=str(publication["pullRequestTitle"]),
        body=str(publication["pullRequestBody"]),
    )
    for request in cycle_summary.get("semantic_action_requests") or []:
        accepted = validate_broker_intent(
            request,
            source_revision=config.runtime_commit or transaction.fetched_origin_main,
        )
        preflight_semantic_broker_disclosure(accepted)
    identity = GitHubAppIdentity.from_json(config.state_root / "github-app.json")
    private_key = read_keychain_secret(
        GITHUB_APP_KEYCHAIN_SERVICE,
        GITHUB_APP_KEYCHAIN_ACCOUNT,
    )
    app_token = mint_installation_token(
        identity,
        private_key,
        api_request=api_request,
    )
    git_push_with_token(
        worktree,
        f"{expected_head}:refs/heads/{transaction.branch}",
        app_token,
        disclosure_decision=publication_range["disclosure_decision"],
    )
    pull = open_or_update_nightly_pull_request(
        app_token,
        branch=transaction.branch,
        expected_head=expected_head,
        title=str(publication["pullRequestTitle"]),
        body=str(publication["pullRequestBody"]),
        api_request=api_request,
    )
    pull_number = pull.get("number") if isinstance(pull, dict) else None
    pull_url = pull.get("html_url") if isinstance(pull, dict) else None
    if not isinstance(pull_number, int) or not isinstance(pull_url, str):
        raise GitHubBrokerError("production pull-request readback omitted identity")
    if publication_range["review_required"]:
        return {
            "phase": "P6",
            "publication_attempted": True,
            "publication_range": publication_range,
            "pull_request": {"number": pull_number, "url": pull_url},
            "expected_pr_head": expected_head,
            "review_required": True,
            "project_sync": {
                "source": "project-console-progress-bot",
                "readback": "typed-stage-output",
            },
            "worktree_removed": False,
        }
    checks = wait_for_required_checks(
        app_token,
        head_sha=expected_head,
        timeout_seconds=int(publication["requiredChecksTimeoutSeconds"]),
        poll_seconds=float(publication["pollSeconds"]),
        api_request=api_request,
    )
    semantic_results = execute_production_semantic_actions(
        cycle_summary.get("semantic_action_requests") or [],
        source_revision=config.runtime_commit or transaction.fetched_origin_main,
        github_token=app_token,
    )
    merge_sha = merge_exact_head(
        app_token,
        pull_number=pull_number,
        expected_head=expected_head,
        expected_base=transaction.fetched_origin_main,
        protected=False,
        api_request=api_request,
    )
    pages = wait_for_pages_deployment(
        app_token,
        merge_sha=merge_sha,
        timeout_seconds=int(publication["pagesTimeoutSeconds"]),
        poll_seconds=float(publication["pollSeconds"]),
        api_request=api_request,
    )
    canonical = config.canonical_path.resolve()
    git(canonical, "fetch", "origin", "main")
    if git_text(canonical, "rev-parse", "origin/main") != merge_sha:
        raise TransactionError("origin/main differs from production merge readback")
    synchronized = fast_forward_main(canonical, merge_sha)
    remove_successful_transaction_worktree(
        canonical,
        config.state_root,
        worktree,
    )
    atomic_write_json(
        config.state_root / "last-success.json",
        success_candidate,
    )
    return {
        "phase": "P6",
        "publication_attempted": True,
        "publication_range": publication_range,
        "pull_request": {"number": pull_number, "url": pull_url},
        "expected_pr_head": expected_head,
        "required_checks": checks,
        "project_sync": {
            "source": "project-console-progress-bot",
            "readback": "typed-stage-output",
            "semantic_actions": semantic_results,
        },
        "merge_commit": merge_sha,
        "pages_workflow_run": pages,
        "pages_conclusion": "success",
        "canonical_main": synchronized,
        "worktree_removed": True,
    }


def prepare_transaction(
    config: RunnerConfig,
    *,
    run_id: str | None = None,
    local_cycle: Callable[[TransactionResult], Mapping[str, Any]] | None = None,
    publication_cycle: Callable[
        [TransactionResult, Mapping[str, Any]], Mapping[str, Any]
    ]
    | None = None,
) -> TransactionResult:
    config.validate()
    if config.retry_attempt_number > 1 and publication_cycle is not None:
        raise TransactionError(
            "linked retry may not automatically reattempt publication"
        )
    if config.retry_attempt_number > 1 and local_cycle is not None and config.retry_mode != "deterministic-recovery":
        raise TransactionError(
            "linked retry local work must be an explicit deterministic recovery cycle"
        )
    run_id = run_id or make_run_id()
    if not SAFE_RUN_ID.fullmatch(run_id):
        raise TransactionError("unsafe run ID")
    ensure_owner_directory(config.state_root)
    status = _base_status(config, run_id)
    branch: str | None = None
    checkpoint: str | None = None
    worktree: Path | None = None
    fetched: str | None = None
    lifecycle_started = False
    lifecycle_branch = BRANCH_PREFIX + utc_now().strftime("%Y%m%dT%H%M%SZ")
    previous_owner_run_id: str | None = None
    owner_path = config.state_root / "run-owner.json"
    if owner_path.is_file():
        try:
            owner = read_json_object(owner_path)
            candidate = owner.get("run_id")
            if isinstance(candidate, str) and SAFE_RUN_ID.fullmatch(candidate):
                previous_owner_run_id = candidate
        except (OSError, ValueError, json.JSONDecodeError, TransactionError):
            raise TransactionError("previous run owner record is unavailable or invalid")

    def record_failure(error: BaseException) -> None:
        prevented_disclosure = isinstance(error, DisclosurePreventionError)
        if prevented_disclosure:
            failure_class = "outbound-disclosure-prevented"
        elif isinstance(error, KeyboardInterrupt):
            failure_class = "KeyboardInterrupt"
        else:
            failure_class = type(error).__name__
        write_status(
            config,
            status,
            status="failed",
            completed_at=iso_utc(),
            failure_class=failure_class,
            failure_reason=str(error),
            preserved_paths=[
                value for value in (branch, str(worktree) if worktree else None) if value
            ],
            exact_next_action="Inspect the exact failure and preserved local state; do not publish.",
        )
        try:
            spool_failure_incident(
                config.state_root / "incident-spool.jsonl",
                run_id=run_id,
                component="run-coordinator-bot",
                prerequisite=str(status.get("stage") or "transaction"),
                failure_class=failure_class,
                diagnostic=str(error),
                observed_at=iso_utc(),
                impact="near_miss" if prevented_disclosure else "blocking",
                summary=(
                    "A project-operated GitHub disclosure was prevented before transmission."
                    if prevented_disclosure
                    else "Automation transaction failed before normal incident reconciliation."
                ),
                reported_by="GitHub disclosure gate"
                if prevented_disclosure
                else "Run Coordinator failure spool",
                recommended_owner="Project security governance"
                if prevented_disclosure
                else "Run Coordinator",
                next_action=(
                    "Review the opaque disclosure finding and classify or sanitize the preserved local artifact."
                    if prevented_disclosure
                    else "Inspect the preserved run status and reconcile the exact failure boundary."
                ),
                active_links=(
                    ("log:incidents",)
                    if prevented_disclosure
                    else ("automation-role:run-coordinator-bot",)
                ),
            )
        except (OSError, IncidentContractError):
            # Status already preserves the primary failure. Do not mask it if
            # the independent owner-only incident spool is also unavailable.
            pass
        if lifecycle_started:
            _transition_lifecycle_failure(config, run_id, error)

    try:
        with exclusive_lock(config.state_root, run_id, on_error=record_failure):
            events_path = transaction_events_path(config)
            try:
                if previous_owner_run_id is not None and previous_owner_run_id != run_id:
                    mark_abandoned_transactions(
                        events_path,
                        released_lock_run_ids=[previous_owner_run_id],
                        owner="run-coordinator",
                    )
            except TransactionLifecycleError as error:
                raise TransactionError(
                    "prior transaction lifecycle cannot be recovered deterministically"
                ) from error
            if config.scheduled_for is not None and scheduled_occurrence_exists(
                events_path,
                _attempt_group(config, run_id),
            ):
                # The status is only a latest projection.  This immutable log
                # check is the authority; changing last-scheduled-slot cannot
                # replay an occurrence.
                write_status(
                    config,
                    status,
                    status="completed",
                    stage="20_finish",
                    completed_at=iso_utc(),
                    validation_summary={
                        "phase": "due-check",
                        "due": False,
                        "reason": "scheduled_occurrence_already_recorded",
                    },
                    exact_next_action="No duplicate scheduled occurrence was started.",
                )
                return TransactionResult(run_id, "completed", None, None, None, None)
            repository = config.canonical_path.resolve()
            if not (repository / ".git").exists():
                raise TransactionError("canonical path is not a Git worktree")
            starting_branch = git_text(repository, "rev-parse", "--abbrev-ref", "HEAD")
            starting_head = git_text(repository, "rev-parse", "HEAD")
            base_head = git_text(repository, "rev-parse", "refs/remotes/origin/main")
            origin = git_text(repository, "remote", "get-url", "origin")
            if config.fixture_root is None and origin not in APPROVED_ORIGINS:
                raise TransactionError("canonical origin is not approved")
            if starting_branch != "main":
                raise TransactionError("canonical repository is off main")
            _start_lifecycle_attempt(
                config,
                run_id=run_id,
                branch=lifecycle_branch,
                head=starting_head,
                base=base_head,
            )
            lifecycle_started = True
            paused = pause_requested(config.state_root)
            write_status(
                config,
                status,
                control_state="paused" if paused else "run",
            )
            if paused:
                write_status(
                    config,
                    status,
                    status="paused",
                    control_state="paused",
                    stage="01_preflight",
                    completed_at=iso_utc(),
                    validation_summary={
                        "phase": "pause-control",
                        "due": False,
                        "reason": "owner_pause_file_present",
                    },
                    exact_next_action=(
                        "Remove the owner-only PAUSED file and invoke the same "
                        "reviewed bootstrap manually or wait for the next schedule."
                    ),
                )
                transition_transaction(
                    events_path,
                    run_id=run_id,
                    state="completed_noop",
                    owner="run-coordinator",
                    next_action="Remain paused until the owner separately resumes automation.",
                    terminal_proof=_lifecycle_proof(
                        run_id,
                        "paused",
                        {"control_state": "paused", "status": "paused"},
                    ),
                )
                return TransactionResult(
                    run_id,
                    "paused",
                    None,
                    None,
                    None,
                    None,
                )
            if config.scheduled_for is not None:
                claim_scheduled_slot(config.state_root, config.scheduled_for)
            dynamic_protected = governing_protected_paths(
                repository,
                config.runtime_files,
                path_authority=routing_path_authority(
                    config,
                    repository,
                ),
                require_active_registry=(
                    config.fixture_root is None
                    and config.trigger
                    in {"scheduled", "manual", "manual-retry"}
                ),
            )
            preexisting = status_manifest(
                repository,
                dynamic_protected=dynamic_protected,
            )
            reject_unsafe_manifest_entries(repository, preexisting)
            write_prelock_manifest(
                config,
                run_id,
                origin=origin,
                branch=starting_branch,
                head=starting_head,
                records=preexisting,
            )
            write_status(
                config,
                status,
                stage="01_preflight",
                starting_branch=starting_branch,
                starting_local_head=starting_head,
                preexisting_path_manifest_sha256=manifest_digest(preexisting),
                classification={
                    name: [item.path for item in preexisting if item.classification == name]
                    for name in ("ordinary", "protected", "prohibited", "unrecognized")
                },
            )
            prohibited = [
                item.path
                for item in preexisting
                if item.classification in {"prohibited", "unrecognized"}
            ]
            if prohibited:
                raise TransactionError(
                    "unpublishable pre-lock paths require Benjamin review: "
                    + ", ".join(prohibited)
                )
            git(repository, "fetch", "origin", "main")
            fetched = git_text(repository, "rev-parse", "origin/main")
            if (
                config.runtime_commit is not None
                and fetched != config.runtime_commit
            ):
                raise TransactionError(
                    "fetched origin/main moved beyond the executed runtime commit"
                )
            write_status(
                config,
                status,
                stage="02_fetch",
                fetched_origin_main=fetched,
                runtime_commit=fetched,
            )
            branch = lifecycle_branch
            git(repository, "switch", "-c", branch)
            stage_paths = manifest_stage_paths(preexisting)
            explicit_stage(repository, stage_paths)
            if git(repository, "diff", "--cached", "--quiet", check=False).returncode:
                git(repository, "commit", "-m", CHECKPOINT_MESSAGE)
                checkpoint = git_text(repository, "rev-parse", "HEAD")
            git(repository, "switch", "main")
            clean_manifest = status_manifest(repository)
            if clean_manifest:
                raise TransactionError(
                    "canonical worktree is not clean after checkpoint: "
                    + ", ".join(item.path for item in clean_manifest)
                )
            clean_digest = manifest_digest(clean_manifest)
            protected = tuple(
                item.path for item in preexisting if item.classification == "protected"
            )
            write_status(
                config,
                status,
                stage="04_checkpoint",
                checkpoint_commit=checkpoint,
                nightly_branch=branch,
                classification={
                    **(status["classification"] or {}),
                    "protected_review": bool(protected),
                },
            )
            if protected:
                write_status(
                    config,
                    status,
                    status="review-required",
                    stage="04_checkpoint",
                    completed_at=iso_utc(),
                    preserved_paths=[branch],
                    failure_class="protected_runtime_at_start",
                    failure_reason="protected work was checkpointed but will not be executed",
                    exact_next_action="Benjamin reviews the protected checkpoint before any runtime execution.",
                )
                transition_transaction(
                    events_path,
                    run_id=run_id,
                    state="failed_preserved",
                    owner="run-coordinator",
                    next_action="Preserve the protected checkpoint pending recovery classification.",
                    failure_code="protected-runtime-at-start",
                )
                transition_transaction(
                    events_path,
                    run_id=run_id,
                    state="recovery_pending",
                    owner="run-coordinator",
                    next_action="Reconcile the preserved protected checkpoint before any retry.",
                    failure_code="protected-runtime-at-start",
                )
                return TransactionResult(
                    run_id,
                    "review-required",
                    branch,
                    checkpoint,
                    None,
                    fetched,
                    protected,
                    "protected_runtime_at_start",
                )
            worktree = config.state_root / "worktrees" / run_id
            ensure_owner_directory(worktree.parent)
            git(repository, "worktree", "add", str(worktree), branch)
            merge = git(worktree, "merge", "--no-edit", fetched, check=False)
            if merge.returncode:
                spool_failure_incident(
                    config.state_root / "incident-spool.jsonl",
                    run_id=run_id,
                    component="run-coordinator-bot",
                    prerequisite="origin-main-merge",
                    failure_class="origin_merge_conflict",
                    diagnostic=(
                        "origin/main merge failed; the worktree and branch are preserved"
                    ),
                    observed_at=iso_utc(),
                )
                write_status(
                    config,
                    status,
                    status="blocked",
                    stage="05_worktree",
                    completed_at=iso_utc(),
                    worktree_path=str(worktree),
                    preserved_paths=[branch, str(worktree)],
                    failure_class="origin_merge_conflict",
                    failure_reason="origin/main merge failed; the worktree and branch are preserved",
                    exact_next_action="Inspect the preserved merge conflict without changing canonical main.",
                )
                transition_transaction(
                    events_path,
                    run_id=run_id,
                    state="failed_preserved",
                    owner="run-coordinator",
                    next_action="Inspect the preserved merge conflict without changing canonical main.",
                    failure_code="origin-merge-conflict",
                )
                transition_transaction(
                    events_path,
                    run_id=run_id,
                    state="recovery_pending",
                    owner="run-coordinator",
                    next_action="Classify, reconcile, or package the preserved merge-conflict material.",
                    failure_code="origin-merge-conflict",
                )
                return TransactionResult(
                    run_id,
                    "blocked",
                    branch,
                    checkpoint,
                    str(worktree),
                    fetched,
                    (),
                    "origin_merge_conflict",
                )
            assert_canonical_unchanged(repository, starting_head, clean_digest)
            reconcile_failure_spool(
                config.state_root / "incident-spool.jsonl",
                config.state_root
                / "records"
                / "automation"
                / "operational-incidents.jsonl",
            )
            prepared = TransactionResult(
                run_id, "completed", branch, checkpoint, str(worktree), fetched
            )
            write_status(
                config,
                status,
                stage="05_worktree",
                worktree_path=str(worktree),
            )
            cycle_summary = (
                _callback_summary(
                    local_cycle(prepared),
                    callback_name="local cycle",
                )
                if local_cycle is not None
                else None
            )
            cycle_phase = (
                str(cycle_summary.get("phase"))
                if isinstance(cycle_summary, Mapping) and cycle_summary.get("phase")
                else "P2"
            )
            publication_summary = None
            if publication_cycle is not None:
                if not isinstance(cycle_summary, Mapping):
                    raise TransactionError(
                        "publication requires a completed local cycle summary"
                    )
                assert_canonical_unchanged(repository, starting_head, clean_digest)
                publication_summary = _callback_summary(
                    publication_cycle(prepared, cycle_summary),
                    callback_name="publication cycle",
                )
                cycle_phase = str(publication_summary.get("phase") or cycle_phase)
            cycle_elim_summary = None
            if isinstance(cycle_summary, Mapping):
                nested_elim = cycle_summary.get("p2", cycle_summary)
                if isinstance(nested_elim, Mapping):
                    cycle_elim_summary = nested_elim
            write_status(
                config,
                status,
                status="completed",
                stage="20_finish" if publication_summary is not None else
                "06_local_cycle" if cycle_summary is not None else "05_worktree",
                completed_at=iso_utc(),
                worktree_path=str(worktree),
                preserved_paths=(
                    []
                    if publication_summary is not None
                    and publication_summary.get("worktree_removed") is True
                    else [value for value in (branch, str(worktree)) if value]
                ),
                elim_unit=(
                    cycle_elim_summary.get("elim_unit")
                    if cycle_elim_summary is not None
                    else status.get("elim_unit")
                ),
                elim_outcome=(
                    cycle_elim_summary.get("elim_outcome")
                    if cycle_elim_summary is not None
                    else status.get("elim_outcome")
                ),
                validation_summary={
                    "phase": cycle_phase if cycle_summary is not None else "P1",
                    "transaction_worktree_prepared": True,
                    "publication_attempted": publication_summary is not None,
                    **({"local_cycle": cycle_summary} if cycle_summary is not None else {}),
                    **(
                        {"publication_cycle": publication_summary}
                        if publication_summary is not None
                        else {}
                    ),
                },
                pull_request=(
                    publication_summary.get("pull_request")
                    if publication_summary is not None
                    else None
                ),
                expected_pr_head=(
                    publication_summary.get("expected_pr_head")
                    if publication_summary is not None
                    else None
                ),
                merge_commit=(
                    publication_summary.get("merge_commit")
                    if publication_summary is not None
                    else None
                ),
                project_sync=(
                    publication_summary.get("project_sync")
                    if publication_summary is not None
                    else None
                ),
                pages_workflow_run=(
                    publication_summary.get("pages_workflow_run")
                    if publication_summary is not None
                    else None
                ),
                pages_conclusion=(
                    publication_summary.get("pages_conclusion")
                    if publication_summary is not None
                    else None
                ),
                exact_next_action=(
                    "P6 production cycle completed with exact readback."
                    if cycle_phase == "P6"
                    and publication_summary is not None
                    and not publication_summary.get("review_required")
                    else "Benjamin reviews the protected P6 pull request."
                    if cycle_phase == "P6"
                    and publication_summary is not None
                    and publication_summary.get("review_required")
                    else "P5 supervised publication completed with exact readback."
                    if publication_summary is not None
                    else "Preserve the completed local-only final commit for review."
                    if cycle_summary is not None and cycle_phase == "P3"
                    else "Preserve the completed local-only cycle for review."
                    if cycle_summary is not None
                    else "P2 may add deterministic local stages after protected review and integration."
                ),
            )
            if publication_summary is not None and publication_summary.get("worktree_removed") is True:
                transition_transaction(
                    events_path,
                    run_id=run_id,
                    state="completed_published",
                    owner="run-coordinator",
                    next_action="Published transaction has exact readback evidence.",
                    terminal_proof=_lifecycle_proof(
                        run_id,
                        "published",
                        {
                            "merge_commit": publication_summary.get("merge_commit"),
                            "worktree_removed": True,
                        },
                    ),
                )
            else:
                transition_transaction(
                    events_path,
                    run_id=run_id,
                    state="recovery_pending",
                    owner="run-coordinator",
                    next_action="Reconcile or package the retained transaction worktree before retry or retirement.",
                    failure_code="retained-live-worktree",
                )
            return prepared
    except Exception:
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validate-repository-policy",
        action="store_true",
        help="validate tracked modes and file types without running a transaction",
    )
    parser.add_argument("--canonical-path", type=Path)
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--fixture", type=Path, help="owner-controlled fixture root")
    parser.add_argument("--manual", action="store_true")
    parser.add_argument("--scheduled", action="store_true")
    parser.add_argument("--runtime-commit")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--run-id")
    parser.add_argument(
        "--p2-fixture-plan",
        type=Path,
        help="explicit local-only P2 fixture plan; valid only with --fixture",
    )
    parser.add_argument(
        "--p3-fixture-plan",
        type=Path,
        help="explicit local-only P3 fixture plan; valid only with --fixture",
    )
    parser.add_argument(
        "--p5-supervised-plan",
        type=Path,
        help="owner-approved P5 live plan; requires --manual and reviewed main",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.validate_repository_policy:
        repository = (args.canonical_path or Path.cwd()).resolve()
        print(json.dumps(validate_repository_policy(repository), sort_keys=True))
        return 0
    production = (
        args.fixture is None
        and args.p5_supervised_plan is None
        and args.runtime_commit is not None
        and (args.scheduled or args.manual)
        and not args.dry_run
    )
    if args.scheduled and args.manual:
        print("select exactly one of --scheduled or --manual", file=sys.stderr)
        return 64
    if args.scheduled and (args.fixture is not None or args.dry_run):
        print("scheduled execution cannot use fixture or dry-run mode", file=sys.stderr)
        return 64
    if args.p5_supervised_plan is not None:
        if args.fixture is not None or args.dry_run or not args.manual:
            print(
                "P5 supervised execution requires --manual without fixture or dry-run",
                file=sys.stderr,
            )
            return 64
    elif args.fixture is None and not (args.manual and args.dry_run) and not production:
        print(
            "production execution requires --scheduled/--manual and --runtime-commit",
            file=sys.stderr,
        )
        return 64
    fixture = args.fixture.resolve() if args.fixture else None
    selected_plans = [
        path
        for path in (
            args.p2_fixture_plan,
            args.p3_fixture_plan,
            args.p5_supervised_plan,
        )
        if path is not None
    ]
    if (
        (args.p2_fixture_plan is not None or args.p3_fixture_plan is not None)
        and fixture is None
    ):
        print("P2/P3 fixture plans require --fixture", file=sys.stderr)
        return 64
    if len(selected_plans) > 1:
        print("select only one fixture phase plan", file=sys.stderr)
        return 64
    canonical = args.canonical_path or (
        fixture / "repo"
        if fixture
        else Path("/Users/benjaminsmith/Automation Workspaces/ARRP")
    )
    state = args.state_root or (
        fixture / "state"
        if fixture
        else Path.home() / "Library/Application Support/ARRP"
    )
    if args.dry_run and fixture is None:
        config = RunnerConfig(canonical, state, trigger="manual-dry-run")
        config.validate()
        print("P1_DRY_RUN_OK: configuration validated; no repository operation performed")
        return 0
    runtime: Path | None = None
    if production:
        runtime = verify_executed_runtime(
            state,
            str(args.runtime_commit),
        )
    supervised_plan = (
        read_p5_supervised_plan(args.p5_supervised_plan)
        if args.p5_supervised_plan is not None
        else None
    )
    config = RunnerConfig(
        canonical,
        state,
        fixture_root=fixture,
        trigger=(
            "manual-p5-supervised"
            if supervised_plan is not None
            else "scheduled"
            if args.scheduled
            else "manual"
            if production
            else "fixture"
        ),
        scheduled_for=scheduled_slot() if args.scheduled else None,
        console_projection=(
            canonical
            / "framework/project/interfaces/project-console/data/local-automation-status.js"
        ),
        supervised_live=supervised_plan is not None,
        runtime_commit=str(args.runtime_commit) if production else None,
    )
    cycle_output: dict[str, Any] = {}
    publication_output: dict[str, Any] = {}
    local_cycle = None
    if args.p2_fixture_plan is not None:
        plan = args.p2_fixture_plan.resolve()
        if not _is_within(plan, fixture):
            raise TransactionError("P2 fixture plan must remain inside the fixture root")

        def local_cycle(transaction: TransactionResult) -> Mapping[str, Any]:
            cycle_output.update(run_p2_fixture_cycle(config, transaction, plan))
            return cycle_output
    elif args.p3_fixture_plan is not None:
        plan = args.p3_fixture_plan.resolve()
        if not _is_within(plan, fixture):
            raise TransactionError("P3 fixture plan must remain inside the fixture root")

        def local_cycle(transaction: TransactionResult) -> Mapping[str, Any]:
            cycle_output.update(run_p3_fixture_cycle(config, transaction, plan))
            return cycle_output
    elif supervised_plan is not None:
        plan = args.p5_supervised_plan.resolve()

        def local_cycle(transaction: TransactionResult) -> Mapping[str, Any]:
            cycle_output.update(
                run_p3_fixture_cycle(
                    config,
                    transaction,
                    plan,
                    supervised=True,
                )
            )
            return cycle_output

        def publication_cycle(
            transaction: TransactionResult,
            summary: Mapping[str, Any],
        ) -> Mapping[str, Any]:
            publication_output.update(
                publish_supervised_transaction(
                    config,
                    transaction,
                    summary,
                    supervised_plan["publication"],
                )
            )
            return publication_output
    elif production:
        assert runtime is not None

        def local_cycle(transaction: TransactionResult) -> Mapping[str, Any]:
            cycle_output.update(
                run_production_cycle(
                    config,
                    transaction,
                    runtime,
                )
            )
            return cycle_output

        def publication_cycle(
            transaction: TransactionResult,
            summary: Mapping[str, Any],
        ) -> Mapping[str, Any]:
            publication_output.update(
                publish_production_transaction(
                    config,
                    transaction,
                    summary,
                )
            )
            return publication_output

    result = prepare_transaction(
        config,
        run_id=args.run_id,
        local_cycle=local_cycle,
        publication_cycle=(
            publication_cycle if supervised_plan is not None or production else None
        ),
    )
    output: dict[str, Any] = {"transaction": result.__dict__}
    if cycle_output:
        output[cycle_output.get("phase", "P2").lower()] = cycle_output
    if publication_output:
        output["publication"] = publication_output
    print(json.dumps(output, sort_keys=True, default=list))
    return 0 if result.status in {"completed", "paused"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
