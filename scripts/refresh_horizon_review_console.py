#!/usr/bin/env python3
"""Refresh the owner Console through the fixed Project credential boundary."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Mapping

try:
    from arrp_nightly import (
        GITHUB_PROJECT_KEYCHAIN_ACCOUNT,
        GITHUB_PROJECT_KEYCHAIN_SERVICE,
        SensitiveValue,
        read_keychain_secret,
    )
    from path_authority import ProjectPathAuthority
except ModuleNotFoundError:
    from scripts.arrp_nightly import (
        GITHUB_PROJECT_KEYCHAIN_ACCOUNT,
        GITHUB_PROJECT_KEYCHAIN_SERVICE,
        SensitiveValue,
        read_keychain_secret,
    )
    from scripts.path_authority import ProjectPathAuthority


PROJECT_CREDENTIAL_ENVIRONMENT = "ARRP_PROJECT_TOKEN"
REMOVED_CREDENTIAL_ENVIRONMENTS = (
    PROJECT_CREDENTIAL_ENVIRONMENT,
    "GH_TOKEN",
    "GITHUB_TOKEN",
)


class ConsoleRefreshError(RuntimeError):
    """A safe owner-facing failure without credential or provider detail."""


RunFunction = Callable[..., subprocess.CompletedProcess[str]]
SecretReader = Callable[[str, str], SensitiveValue]


def _run_checked(
    command: list[str],
    *,
    cwd: Path,
    environment: Mapping[str, str] | None,
    step: str,
    run: RunFunction,
) -> None:
    completed = run(
        command,
        cwd=cwd,
        env=dict(environment) if environment is not None else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise ConsoleRefreshError(
            f"{step} failed with exit status {completed.returncode}."
        )


def _require_clean_tracked_tree(
    repository: Path,
    *,
    run: RunFunction,
) -> None:
    completed = run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repository,
        env=None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise ConsoleRefreshError(
            "The tracked-tree preflight could not be verified."
        )
    if completed.stdout.strip():
        raise ConsoleRefreshError(
            "The tracked tree must be clean before an authenticated Console refresh."
        )


def _copy_progress_snapshot(source: Path, destination: Path) -> None:
    if not source.is_file() or source.is_symlink():
        raise ConsoleRefreshError(
            "The authenticated Progress producer did not create its required snapshot."
        )
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_bytes(source.read_bytes())
    os.replace(temporary, destination)


def refresh_console(
    *,
    authority: ProjectPathAuthority | None = None,
    run: RunFunction = subprocess.run,
    secret_reader: SecretReader = read_keychain_secret,
    base_environment: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Refresh public-safe Console projections without exporting credentials.

    Production has no caller-selected repository, state root, credential, or
    output path. The dedicated Project token enters only the four read-only
    producer subprocesses and is never placed in an argument or persisted.
    """

    selected_authority = authority or ProjectPathAuthority.production()
    if selected_authority.mode != "production_canonical":
        raise ConsoleRefreshError(
            "Authenticated Console refresh requires the canonical production authority."
        )
    repository = selected_authority.repository_root
    interpreter = selected_authority.repository_path(".venv/bin/python")
    progress_builder = selected_authority.repository_path(
        "scripts/build_project_console_progress.py"
    )
    integrity_auditor = selected_authority.repository_path(
        "scripts/audit_project_consistency.py"
    )
    integrity_builder = selected_authority.repository_path(
        "scripts/build_project_integrity_feed.py"
    )
    console_builder = selected_authority.repository_path(
        "scripts/build_horizon_review_console.py"
    )
    progress_config = selected_authority.repository_path(
        "framework/project/interfaces/project-console-progress.json"
    )
    registry = selected_authority.repository_path(
        "inventory/github_issue_registry.csv"
    )
    integrity_history = selected_authority.repository_path(
        "research/horizon-review-console/data/integrity.js"
    )
    integrity_markdown = selected_authority.repository_path(
        "framework/records/status/project-integrity-report.md"
    )
    temporary_root = selected_authority.repository_output(".tmp")
    temporary_root.mkdir(mode=0o700, exist_ok=True)
    progress_snapshot = selected_authority.repository_output(
        ".tmp/project-console-progress-snapshot.json"
    )
    integrity_snapshot = selected_authority.repository_output(
        ".tmp/project-console-integrity.json"
    )

    _require_clean_tracked_tree(repository, run=run)
    try:
        project_token = secret_reader(
            GITHUB_PROJECT_KEYCHAIN_SERVICE,
            GITHUB_PROJECT_KEYCHAIN_ACCOUNT,
        )
    except Exception as error:
        raise ConsoleRefreshError(
            "The dedicated Project credential is unavailable."
        ) from error
    inherited_environment = (
        os.environ if base_environment is None else base_environment
    )
    environment = dict(inherited_environment)
    for name in REMOVED_CREDENTIAL_ENVIRONMENTS:
        environment.pop(name, None)
    public_environment = dict(environment)
    environment[PROJECT_CREDENTIAL_ENVIRONMENT] = project_token.reveal()

    staging = Path(
        tempfile.mkdtemp(prefix="console-project-refresh-", dir=temporary_root)
    )
    try:
        progress_output = staging / "progress"
        _run_checked(
            [
                str(interpreter),
                str(progress_builder),
                "--config",
                str(progress_config),
                "--registry",
                str(registry),
                "--output",
                str(progress_output),
                "--token-env",
                PROJECT_CREDENTIAL_ENVIRONMENT,
            ],
            cwd=repository,
            environment=environment,
            step="Authenticated Project projection",
            run=run,
        )
        _copy_progress_snapshot(
            progress_output / "progress.json",
            progress_snapshot,
        )

        integrity_report = staging / "integrity-report.json"
        _run_checked(
            [
                str(interpreter),
                str(integrity_auditor),
                "--json-output",
                str(integrity_report),
                "--markdown-output",
                str(integrity_markdown),
                "--exit-zero-on-findings",
            ],
            cwd=repository,
            environment=environment,
            step="Authenticated Project Integrity observation",
            run=run,
        )
        _run_checked(
            [
                str(interpreter),
                str(integrity_builder),
                "--report",
                str(integrity_report),
                "--output",
                str(integrity_snapshot),
                "--existing-file",
                str(integrity_history),
            ],
            cwd=repository,
            environment=public_environment,
            step="Integrity feed construction",
            run=run,
        )

        environment["ARRP_PROGRESS_SNAPSHOT"] = (
            ".tmp/project-console-progress-snapshot.json"
        )
        environment["ARRP_INTEGRITY_SNAPSHOT"] = (
            ".tmp/project-console-integrity.json"
        )
        _run_checked(
            [
                str(interpreter),
                str(console_builder),
                "--refresh-github",
                "--console-only",
            ],
            cwd=repository,
            environment=environment,
            step="Authenticated Console generation",
            run=run,
        )
    finally:
        environment.pop(PROJECT_CREDENTIAL_ENVIRONMENT, None)
        shutil.rmtree(staging, ignore_errors=True)

    return {
        "schema_version": 1,
        "status": "refreshed",
        "authority": selected_authority.mode,
        "project_access": "read-only Keychain credential",
        "console": "research/horizon-review-console/index.html",
    }


def main() -> int:
    try:
        result = refresh_console()
    except ConsoleRefreshError as error:
        print(str(error), file=os.sys.stderr)
        return 1
    except Exception:
        print("Authenticated Console refresh failed safely.", file=os.sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
