#!/usr/bin/env python3
"""Refresh the owner Console through the fixed Project credential boundary."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
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
    from component_registry import (
        RegistryError as ComponentRegistryError,
        load_component_registry_configuration_routing_view,
    )
except ModuleNotFoundError:
    from scripts.arrp_nightly import (
        GITHUB_PROJECT_KEYCHAIN_ACCOUNT,
        GITHUB_PROJECT_KEYCHAIN_SERVICE,
        SensitiveValue,
        read_keychain_secret,
    )
    from scripts.path_authority import ProjectPathAuthority
    from scripts.component_registry import (
        RegistryError as ComponentRegistryError,
        load_component_registry_configuration_routing_view,
    )


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


def _component_registry_configuration_state() -> str:
    """Validate tracked configuration without consulting live owner state."""
    try:
        view = load_component_registry_configuration_routing_view(
        )
    except (ComponentRegistryError, OSError, ValueError) as error:
        raise ConsoleRefreshError(
            "Component Registry configuration validation is unavailable."
        ) from error
    mode = view.get("validation_mode")
    if (
        view.get("schema_version") != 4
        or view.get("registry_path")
        != "framework/component-registry.json"
        or mode
        not in {
            "adopted_configuration_validation",
        }
        or view.get("authoritative") is not False
        or view.get("executable") is not False
        or view.get("authority_effective") is not False
        or view.get("source_revision_authorized") is not False
        or view.get("source_bytes_current") is not True
        or view.get("canonical_history_confirmed") is not False
        or view.get("receipt_trusted") is not False
        or view.get("runtime_live") != "not_checked"
        or view.get("activation_receipt_consulted") is not False
        or view.get("predecessor_route_consulted") is not False
    ):
        raise ConsoleRefreshError(
            "Component Registry configuration validation returned an "
            "incompatible authority mode."
        )
    return str(mode)


def _refresh_console(
    *,
    authority: ProjectPathAuthority,
    interpreter: Path,
    run: RunFunction = subprocess.run,
    secret_reader: SecretReader = read_keychain_secret,
    base_environment: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Refresh public-safe Console projections without exporting credentials.

    Production has no caller-selected repository, state root, credential, or
    output path. The dedicated Project token enters only the four read-only
    producer subprocesses and is never placed in an argument or persisted.
    """

    if authority.mode != "production_canonical":
        raise ConsoleRefreshError(
            "Authenticated Console refresh requires the canonical production authority."
        )
    repository = authority.repository_root
    progress_builder = authority.repository_path(
        "scripts/build_project_console_progress.py"
    )
    integrity_auditor = authority.repository_path(
        "scripts/audit_project_consistency.py"
    )
    integrity_builder = authority.repository_path(
        "scripts/build_project_integrity_feed.py"
    )
    console_builder = authority.repository_path(
        "scripts/build_project_console.py"
    )
    progress_config = authority.repository_path(
        "framework/project/interfaces/project-console/configuration/progress.json"
    )
    registry = authority.repository_path(
        "inventory/github_issue_registry.csv"
    )
    integrity_history = authority.repository_path(
        "framework/project/interfaces/project-console/data/integrity.js"
    )
    integrity_markdown = authority.repository_path(
        "framework/status/project-integrity-report.md"
    )
    temporary_root = authority.repository_output(".tmp")
    temporary_root.mkdir(mode=0o700, exist_ok=True)
    progress_snapshot = authority.repository_output(
        ".tmp/project-console-progress-snapshot.json"
    )
    integrity_snapshot = authority.repository_output(
        ".tmp/project-console-integrity.json"
    )

    _require_clean_tracked_tree(repository, run=run)
    component_registry_mode = _component_registry_configuration_state()
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
                "--routing-authority",
                "production-canonical",
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
        "authority": authority.mode,
        "project_access": "read-only Keychain credential",
        "component_registry_validation_mode": component_registry_mode,
        "console": "framework/project/interfaces/project-console/project-console.html",
    }


def _production_interpreter(repository: Path) -> Path:
    expected_prefix = (repository / ".venv").resolve(strict=True)
    if Path(sys.prefix).resolve() != expected_prefix:
        raise ConsoleRefreshError(
            "Authenticated Console refresh must run with the project virtual environment."
        )
    bin_directory = repository / ".venv/bin"
    for directory in (repository / ".venv", bin_directory):
        metadata = directory.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ConsoleRefreshError(
                "The project virtual-environment boundary is invalid."
            )
    interpreter = bin_directory / "python"
    metadata = interpreter.lstat()
    if not (
        stat.S_ISREG(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
    ):
        raise ConsoleRefreshError(
            "The project virtual-environment interpreter is invalid."
        )
    resolved_interpreter = interpreter.resolve(strict=True)
    if not resolved_interpreter.is_file() or not os.access(
        resolved_interpreter,
        os.X_OK,
    ):
        raise ConsoleRefreshError(
            "The project virtual-environment interpreter is unavailable."
        )
    # Preserve the verified venv launcher path. Executing its resolved Homebrew
    # target directly would discard the venv prefix and dependency context.
    return interpreter


def refresh_console() -> dict[str, object]:
    """Run the production refresh with no caller-selected trust authority."""

    authority = ProjectPathAuthority.production()
    return _refresh_console(
        authority=authority,
        interpreter=_production_interpreter(authority.repository_root),
    )


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
