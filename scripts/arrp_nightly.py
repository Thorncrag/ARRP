#!/usr/bin/env python3
"""Disabled-by-default local-first transaction runner for ARRP.

P1 supplied the transaction boundary, P2 added deterministic local stages and
one sealed fresh Elim invocation, and P3 adds local validation, exact delta
classification, redacted secret scanning, and a proved local final commit. P4
adds a fixture-first GitHub App, exact-PR, and semantic-action broker boundary.
Host-service installation remains unavailable.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping, Sequence


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
        "framework/CONTEXT_ROUTING.md",
        "framework/PROJECT_STRUCTURE.md",
        "research/horizon-review-console/README.md",
        "research/horizon-review-console/index.html",
        "research/horizon-review-console/app.js",
        "research/horizon-review-console/styles.css",
    }
)
RECOGNIZED_NEW_PREFIXES = (
    "areas/",
    "legislation/",
    "topics/",
    "research/",
    "inventory/",
    "framework/records/",
)
PRIVATE_NAMES = frozenset({".env", ".env.local", "PAUSED"})
RUNTIME_FILES = (
    "scripts/arrp_nightly.py",
    "scripts/arrp_bootstrap.py",
    "scripts/arrp_context.py",
    "scripts/run_coordinator.py",
    "scripts/build_elim_work_queue.py",
    "scripts/select_elim_context_route.py",
    "scripts/build_elim_context.py",
    "scripts/elim_execution.py",
    "scripts/check_codex_usage_reserve.py",
    "scripts/console_data_contracts.py",
)
SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
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
BROKER_OPERATION_TYPES = frozenset(
    {
        "read_state",
        "set_project_field",
        "update_issue_wrapper",
        "post_discussion_reply",
        "nightly_pull_request",
    }
)
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
        "scripts/build_horizon_review_console.py",
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

    def validate(self) -> None:
        canonical = self.canonical_path.resolve()
        state = self.state_root.resolve()
        if self.fixture_root is None:
            expected = Path("/Users/benjaminsmith/Automation Workspaces/ARRP")
            if canonical != expected:
                raise TransactionError("non-fixture canonical path is not the approved ARRP path")
            if state != Path.home() / "Library/Application Support/ARRP":
                raise TransactionError("non-fixture state root is not the approved ARRP state root")
        else:
            fixture = self.fixture_root.resolve()
            if not _is_within(canonical, fixture) or not _is_within(state, fixture):
                raise TransactionError("fixture repository and state root must stay inside fixture root")
            if canonical == Path("/Users/benjaminsmith/Automation Workspaces/ARRP"):
                raise TransactionError("fixture mode cannot target Benjamin's canonical repository")


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


def ensure_owner_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise TransactionError(f"unsafe state directory ownership or mode: {path}")


def atomic_write_json(path: Path, value: Any) -> None:
    ensure_owner_directory(path.parent)
    encoded = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
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


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TransactionError(f"JSON value is not an object: {path}")
    return value


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
) -> None:
    """Push through a pipe-backed askpass helper; the token never enters argv or disk."""

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


def validate_broker_intent(value: object, *, source_revision: str) -> dict[str, Any]:
    """Validate one exact, non-human-reserved semantic action request."""

    if not isinstance(value, dict) or set(value) != BROKER_INTENT_FIELDS:
        raise GitHubBrokerError("broker intent fields do not match the registered schema")
    if value["operation_type"] not in BROKER_OPERATION_TYPES:
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
        "target_node_or_number",
        "authority_record",
        "idempotency_key",
        "rollback_or_correction",
        "readback_contract",
    ):
        if not isinstance(value[field_name], str) or not value[field_name].strip():
            raise GitHubBrokerError(f"broker intent {field_name} must be nonblank")
    return dict(value)


def open_or_update_nightly_pull_request(
    token: SensitiveValue,
    *,
    branch: str,
    expected_head: str,
    title: str,
    body: str,
    api_request: Callable[..., Any] = github_api_request,
) -> dict[str, Any]:
    """Create or read back exactly one App-authored nightly pull request."""

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
    readback = api_request(
        "GET",
        f"/repos/{GITHUB_REPOSITORY}/pulls/{number}",
        token,
    )
    if (
        not isinstance(readback, dict)
        or readback.get("head", {}).get("sha") != expected_head
        or readback.get("base", {}).get("ref") != "main"
    ):
        raise GitHubBrokerError("pull-request head/base readback failed")
    return readback


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
    required = {"ARRP Validation", "CodeQL"}
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
    observed = read_field(intent, project_token)
    if observed != intent.get("expected_old_state"):
        raise GitHubBrokerError("Project field prior-state check failed")
    write_field(intent, intent.get("new_state_or_content"), project_token)
    readback = read_field(intent, project_token)
    if readback != intent.get("new_state_or_content"):
        raise GitHubBrokerError("Project field readback failed")
    return {
        "idempotency_key": intent["idempotency_key"],
        "old_state": observed,
        "new_state": readback,
    }


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


def _render_stage_value(value: str, worktree: Path, run_dir: Path) -> str:
    return value.replace("{worktree}", str(worktree)).replace("{run_dir}", str(run_dir))


def run_local_stages(
    *,
    worktree: Path,
    run_dir: Path,
    state_root: Path,
    specs: Sequence[LocalStageSpec],
    last_success: Mapping[str, Any] | None = None,
    environment: Mapping[str, str] | None = None,
    now: datetime | None = None,
) -> list[LocalStageResult]:
    """Execute exact stage commands and write typed, hash-bound envelopes."""

    ensure_owner_directory(run_dir)
    current = now or utc_now()
    baseline = last_success or {}
    results: list[LocalStageResult] = []
    for spec in specs:
        due, reason = determine_stage_due(
            state_root, spec, baseline, now=current
        )
        if not due:
            results.append(LocalStageResult(spec.identifier, "not_due", reason, None, None))
            continue
        stage_dir = run_dir / "stages" / spec.identifier
        ensure_owner_directory(stage_dir)
        command = tuple(
            _render_stage_value(value, worktree, run_dir) for value in spec.command
        )
        process = subprocess.run(
            command,
            cwd=worktree,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=dict(environment or os.environ),
        )
        output_rows: list[dict[str, str]] = []
        output_error: str | None = None
        for relative in spec.outputs:
            rendered = _render_stage_value(relative, worktree, run_dir)
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
                "diagnostic": output_error
                or process.stderr.decode("utf-8", "replace")[:500],
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
) -> dict[str, Any]:
    stages: dict[str, dict[str, str]] = {}
    for result in results:
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


def sealed_elim_environment(
    source: Mapping[str, str],
    *,
    worktree: Path,
    run_dir: Path,
    model: str,
    codex_home: Path,
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
            "CODEX_SQLITE_HOME": str(codex_home),
        }
    )
    return environment


def sealed_elim_command(
    *,
    codex: Path,
    worktree: Path,
    run_dir: Path,
    model: str,
    schema: Path,
) -> tuple[str, ...]:
    command = [
        str(codex),
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--sandbox",
        "workspace-write",
        "--cd",
        str(worktree),
        "--model",
        model,
        "-c",
        'approval_policy="never"',
        "-c",
        "sandbox_workspace_write.network_access=false",
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
    index_path = Path(git_text(worktree, "rev-parse", "--git-path", "index"))
    if not index_path.is_absolute():
        index_path = worktree / index_path
    index_bytes = index_path.read_bytes() if index_path.exists() else b""
    refs = git(
        worktree,
        "for-each-ref",
        "--format=%(refname)%00%(objectname)",
    ).stdout
    return {
        "head": git_text(worktree, "rev-parse", "HEAD"),
        "branch": git_text(worktree, "rev-parse", "--abbrev-ref", "HEAD"),
        "index_sha256": hashlib.sha256(index_bytes).hexdigest(),
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
    declared = value.get("files_touched")
    if not isinstance(declared, list) or sorted(declared) != sorted(files_touched):
        raise TransactionError("Elim files_touched does not equal the exact worktree delta")
    for path in declared:
        if not isinstance(path, str) or classify_path(path, None, tracked=True) != "ordinary":
            raise TransactionError(f"Elim touched a protected or prohibited path: {path}")


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
                "{worktree}/framework/records/status/source-checker-report.md",
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
                "{worktree}/framework/project/interfaces/project-console-progress.json",
                "--registry",
                "{worktree}/inventory/github_issue_registry.csv",
                "--output",
                "{run_dir}/stages/project-console-progress-bot/report.json",
            ),
            ("{run_dir}/stages/project-console-progress-bot/report.json",),
        ),
        LocalStageSpec(
            "project-integrity-bot",
            None,
            "blocking",
            (
                interpreter,
                "{worktree}/scripts/audit_project_consistency.py",
                "--json-output",
                "{run_dir}/stages/project-integrity-bot/report.json",
                "--markdown-output",
                "{worktree}/framework/records/status/project-integrity-report.md",
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
            "console-build",
            (python, "scripts/build_horizon_review_console.py", "--refresh-github"),
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
            ("node", "--test", "research/horizon-review-console/tests/frontend.test.mjs"),
        ),
        ValidationSpec(
            "participation-tests",
            ("node", "--test", "participate/tests/*.test.js"),
        ),
        ValidationSpec(
            "python-compile",
            (python, "-m", "compileall", "-q", "scripts", "tests"),
        ),
        ValidationSpec("diff-check", ("git", "diff", "--check")),
        ValidationSpec(
            "launchagent-template",
            ("plutil", "-lint", ".github/launchd/com.thorncrag.arrp-nightly.plist.example"),
        ),
    )


def expand_validation_command(
    worktree: Path,
    command: Sequence[str],
) -> tuple[str, ...]:
    expanded: list[str] = []
    for value in command:
        if "*" not in value:
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
) -> list[dict[str, Any]]:
    """Run and record the bound validation set without persisting command output."""

    records: list[dict[str, Any]] = []
    for spec in specs:
        command = expand_validation_command(worktree, spec.command)
        result = subprocess.run(
            command,
            cwd=worktree,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=dict(environment or os.environ),
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


def run_p2_fixture_cycle(
    config: RunnerConfig,
    transaction: TransactionResult,
    plan_path: Path,
) -> dict[str, Any]:
    """Run a complete, local-only P2 cycle against an explicit fixture plan."""

    if config.fixture_root is None or transaction.worktree_path is None:
        raise TransactionError("P2 fixture cycle requires a prepared fixture worktree")
    plan = read_json_object(plan_path)
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
    codex_home = run_dir / "codex-home"
    ensure_owner_directory(codex_home)
    sealed_environment = sealed_elim_environment(
        environment,
        worktree=worktree,
        run_dir=run_dir,
        model=str(elim["model"]),
        codex_home=codex_home,
    )
    feature_command = [str(codex), "features", "list"]
    for feature in SEALED_DISABLED_FEATURES:
        feature_command.extend(("--disable", feature))
    feature_readback = subprocess.run(
        feature_command,
        cwd=worktree,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=sealed_environment,
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
    process = subprocess.run(
        command,
        cwd=worktree,
        input=str(elim["prompt"]).encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=sealed_environment,
        start_new_session=True,
        timeout=int(elim.get("timeout_seconds", 60)),
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
        "files_touched": touched,
        "git_metadata_immutable": True,
        "persistent_session_required": False,
    }


def run_p3_fixture_cycle(
    config: RunnerConfig,
    transaction: TransactionResult,
    plan_path: Path,
) -> dict[str, Any]:
    """Run P2 plus post-generation, validation, and a proved local-only commit."""

    if config.fixture_root is None or transaction.worktree_path is None:
        raise TransactionError("P3 fixture cycle requires a prepared fixture worktree")
    plan = read_json_object(plan_path)
    p2 = run_p2_fixture_cycle(config, transaction, plan_path)
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
    )
    return {
        "schema_version": 1,
        "phase": "P3",
        "run_id": transaction.run_id,
        "publication_attempted": False,
        "p2": p2,
        "commands": command_results,
        "final_commit": commit,
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


def governing_protected_paths(
    repository: Path,
    runtime_files: Sequence[str] = RUNTIME_FILES,
) -> frozenset[str]:
    """Resolve dynamic protected paths from the canonical registry and runtime."""

    protected = set(runtime_files)
    registry_path = repository / "framework/project/automation/context-routes.json"
    if not registry_path.exists():
        return frozenset(protected)
    registry = read_json_object(registry_path)
    documents = registry.get("documents")
    if not isinstance(documents, dict):
        raise TransactionError("context-routes documents must be an object")
    for identifier, document in documents.items():
        if not isinstance(document, dict):
            raise TransactionError(f"invalid context-routes document: {identifier}")
        if document.get("governing") is True:
            path = document.get("path")
            if not isinstance(path, str) or not path:
                raise TransactionError(
                    f"governing context-routes document lacks path: {identifier}"
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
    status_document.update(updates)
    status_document["updated_at"] = iso_utc()
    missing = set(STATUS_FIELDS) - set(status_document)
    if missing:
        raise TransactionError(f"missing status fields: {sorted(missing)}")
    atomic_write_json(config.state_root / "status.json", status_document)
    if config.console_projection is not None:
        write_console_status_projection(
            config.state_root / "status.json", config.console_projection
        )


def write_console_status_projection(status_path: Path, output: Path | None = None) -> Path:
    value = json.loads(status_path.read_text(encoding="utf-8"))
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
    """Scan staged blobs while returning only redacted path/line/type/digest evidence."""

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
                    "digest": hashlib.sha256(content).hexdigest(),
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
                            "digest": hashlib.sha256(line).hexdigest(),
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
) -> dict[str, Any]:
    """Classify, scan, commit, and prove the exact local-only final delta."""

    base_commit = git_text(repository, "rev-parse", "HEAD")
    dynamic_protected = governing_protected_paths(repository)
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


def prepare_transaction(
    config: RunnerConfig,
    *,
    run_id: str | None = None,
    local_cycle: Callable[[TransactionResult], Mapping[str, Any]] | None = None,
) -> TransactionResult:
    config.validate()
    run_id = run_id or make_run_id()
    if not SAFE_RUN_ID.fullmatch(run_id):
        raise TransactionError("unsafe run ID")
    ensure_owner_directory(config.state_root)
    status = _base_status(config, run_id)
    branch: str | None = None
    checkpoint: str | None = None
    worktree: Path | None = None
    fetched: str | None = None

    def record_failure(error: BaseException) -> None:
        if isinstance(error, KeyboardInterrupt):
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
        with exclusive_lock(config.state_root, run_id, on_error=record_failure):
            write_status(config, status)
            repository = config.canonical_path.resolve()
            if not (repository / ".git").exists():
                raise TransactionError("canonical path is not a Git worktree")
            starting_branch = git_text(repository, "rev-parse", "--abbrev-ref", "HEAD")
            starting_head = git_text(repository, "rev-parse", "HEAD")
            origin = git_text(repository, "remote", "get-url", "origin")
            if config.fixture_root is None and origin not in APPROVED_ORIGINS:
                raise TransactionError("canonical origin is not approved")
            if starting_branch != "main":
                raise TransactionError("canonical repository is off main")
            preexisting = status_manifest(repository)
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
            write_status(
                config,
                status,
                stage="02_fetch",
                fetched_origin_main=fetched,
                runtime_commit=fetched,
            )
            branch = BRANCH_PREFIX + utc_now().strftime("%Y%m%dT%H%M%SZ")
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
            prepared = TransactionResult(
                run_id, "completed", branch, checkpoint, str(worktree), fetched
            )
            cycle_summary = local_cycle(prepared) if local_cycle is not None else None
            cycle_phase = (
                str(cycle_summary.get("phase"))
                if isinstance(cycle_summary, Mapping) and cycle_summary.get("phase")
                else "P2"
            )
            write_status(
                config,
                status,
                status="completed",
                stage="06_local_cycle" if cycle_summary is not None else "05_worktree",
                completed_at=iso_utc(),
                worktree_path=str(worktree),
                preserved_paths=[branch, str(worktree)],
                validation_summary={
                    "phase": cycle_phase if cycle_summary is not None else "P1",
                    "transaction_worktree_prepared": True,
                    "publication_attempted": False,
                    **({"local_cycle": cycle_summary} if cycle_summary is not None else {}),
                },
                exact_next_action=(
                    "Preserve the completed local-only final commit for review."
                    if cycle_summary is not None and cycle_phase == "P3"
                    else "Preserve the completed local-only cycle for review."
                    if cycle_summary is not None
                    else "P2 may add deterministic local stages after protected review and integration."
                ),
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.validate_repository_policy:
        repository = (args.canonical_path or Path.cwd()).resolve()
        print(json.dumps(validate_repository_policy(repository), sort_keys=True))
        return 0
    if args.fixture is None and not (args.manual and args.dry_run):
        print(
            "P1_DISABLED: use --fixture, or explicit --manual --dry-run",
            file=sys.stderr,
        )
        return 64
    fixture = args.fixture.resolve() if args.fixture else None
    selected_plans = [
        path
        for path in (args.p2_fixture_plan, args.p3_fixture_plan)
        if path is not None
    ]
    if selected_plans and fixture is None:
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
    config = RunnerConfig(
        canonical,
        state,
        fixture_root=fixture,
        trigger="fixture",
        console_projection=(
            canonical
            / "research/horizon-review-console/data/local-automation-status.js"
        ),
    )
    cycle_output: dict[str, Any] = {}
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

    result = prepare_transaction(config, run_id=args.run_id, local_cycle=local_cycle)
    output: dict[str, Any] = {"transaction": result.__dict__}
    if cycle_output:
        output[cycle_output.get("phase", "P2").lower()] = cycle_output
    print(json.dumps(output, sort_keys=True, default=list))
    return 0 if result.status == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
