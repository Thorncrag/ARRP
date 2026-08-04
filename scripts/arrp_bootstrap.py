#!/usr/bin/env python3
"""Trusted bootstrap for the reviewed ARRP local-first runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence


CANONICAL_PATH = Path("/Users/benjaminsmith/Automation Workspaces/ARRP")
STATE_ROOT = Path.home() / "Library/Application Support/ARRP"
APPROVED_ORIGINS = {
    "https://github.com/Thorncrag/ARRP.git",
    "git@github.com:Thorncrag/ARRP.git",
}
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
    "scripts/record_review_epoch.py",
    "scripts/check_codex_usage_reserve.py",
    "scripts/codex_usage_projection.py",
    "scripts/console_data_contracts.py",
    "framework/project/github/disclosure-policy.json",
)


class BootstrapError(RuntimeError):
    pass


def _git(repository: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode:
        raise BootstrapError(
            f"git {' '.join(arguments)} failed ({result.returncode})"
        )
    return result


def _git_text(repository: Path, *arguments: str) -> str:
    return _git(repository, *arguments).stdout.decode("utf-8", "strict").strip()


def _owner_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    info = path.stat()
    if info.st_uid != os.getuid() or not stat.S_ISDIR(info.st_mode):
        raise BootstrapError(f"unsafe owner directory: {path}")


def _owner_directory_chain(root: Path, destination: Path) -> None:
    relative = destination.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        _owner_directory(current)


def _write_json(path: Path, payload: object) -> None:
    data = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _tree_blob(repository: Path, revision: str, relative: str) -> tuple[str, str, bytes]:
    raw = _git_text(repository, "ls-tree", revision, "--", relative)
    if not raw:
        raise BootstrapError(f"reviewed runtime file is absent: {relative}")
    metadata, listed = raw.split("\t", 1)
    mode, kind, blob = metadata.split()
    if listed != relative or kind != "blob" or mode == "120000":
        raise BootstrapError(f"unsafe reviewed runtime entry: {relative}")
    content = _git(repository, "show", f"{revision}:{relative}").stdout
    if _hash_object(repository, content) != blob:
        raise BootstrapError(f"reviewed runtime blob mismatch: {relative}")
    return mode, blob, content


def _hash_object(repository: Path, content: bytes) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), "hash-object", "--stdin"],
        input=content,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise BootstrapError("git hash-object failed")
    return result.stdout.decode("ascii", "strict").strip()


def materialize_runtime(
    repository: Path,
    state_root: Path,
    revision: str,
    runtime_files: Sequence[str] = RUNTIME_FILES,
) -> Path:
    runtime_root = state_root / "runtime"
    _owner_directory(state_root)
    _owner_directory(runtime_root)
    destination = runtime_root / revision
    if destination.exists():
        destination_info = destination.lstat()
        if (
            destination.is_symlink()
            or not stat.S_ISDIR(destination_info.st_mode)
            or destination_info.st_uid != os.getuid()
            or stat.S_IMODE(destination_info.st_mode) != 0o700
        ):
            raise BootstrapError("existing runtime directory permissions are unsafe")
        manifest_path = destination / "runtime-manifest.json"
        manifest_info = manifest_path.lstat()
        if (
            manifest_path.is_symlink()
            or not stat.S_ISREG(manifest_info.st_mode)
            or manifest_info.st_uid != os.getuid()
            or stat.S_IMODE(manifest_info.st_mode) != 0o600
        ):
            raise BootstrapError("existing runtime manifest permissions are unsafe")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("source_commit") != revision:
            raise BootstrapError("existing runtime manifest has the wrong commit")
        for relative, expected in manifest.get("files", {}).items():
            target = destination / relative
            reviewed_mode, _blob, _content = _tree_blob(
                repository,
                revision,
                relative,
            )
            expected_mode = 0o700 if int(reviewed_mode, 8) & 0o111 else 0o600
            target_info = target.lstat()
            if (
                not target.is_file()
                or target.is_symlink()
                or target_info.st_uid != os.getuid()
                or stat.S_IMODE(target_info.st_mode) != expected_mode
                or hashlib.sha256(target.read_bytes()).hexdigest() != expected
            ):
                raise BootstrapError(f"existing runtime verification failed: {relative}")
        if set(manifest.get("files", {})) != set(runtime_files):
            raise BootstrapError("existing runtime manifest has the wrong file set")
        expected_paths = {
            "runtime-manifest.json",
            *(str(Path(relative)) for relative in runtime_files),
        }
        actual_paths = {
            str(path.relative_to(destination))
            for path in destination.rglob("*")
            if path.is_file() or path.is_symlink()
        }
        if actual_paths != expected_paths:
            raise BootstrapError("existing runtime contains an unexpected path")
        return destination

    temporary = Path(tempfile.mkdtemp(prefix=f".{revision}.", dir=runtime_root))
    os.chmod(temporary, 0o700)
    hashes: dict[str, str] = {}
    for relative in runtime_files:
        mode, blob, content = _tree_blob(repository, revision, relative)
        if _hash_object(repository, content) != blob:
            raise BootstrapError(f"runtime content identity failed: {relative}")
        target = temporary / relative
        _owner_directory_chain(temporary, target.parent)
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(target, 0o700 if int(mode, 8) & 0o111 else 0o600)
        hashes[relative] = hashlib.sha256(content).hexdigest()
    _write_json(
        temporary / "runtime-manifest.json",
        {"schema_version": 1, "source_commit": revision, "files": hashes},
    )
    os.rename(temporary, destination)
    return destination


def reviewed_runtime(
    repository: Path | None = None,
    state_root: Path | None = None,
) -> tuple[Path, str]:
    repository = repository or CANONICAL_PATH
    state_root = state_root or STATE_ROOT
    repository = repository.resolve()
    state_root = state_root.resolve()
    if repository != CANONICAL_PATH.resolve():
        raise BootstrapError("canonical repository path is not approved")
    if state_root != STATE_ROOT.resolve():
        raise BootstrapError("state root path is not approved")
    if _git_text(repository, "remote", "get-url", "origin") not in APPROVED_ORIGINS:
        raise BootstrapError("canonical origin is not approved")
    _git(repository, "fetch", "origin", "main")
    revision = _git_text(repository, "rev-parse", "origin/main")
    if len(revision) != 40:
        raise BootstrapError("fetched origin/main is not a commit")
    return materialize_runtime(repository, state_root, revision), revision


def build_command(
    runtime: Path,
    revision: str,
    *,
    repository: Path = CANONICAL_PATH,
    state_root: Path = STATE_ROOT,
    manual: bool = False,
) -> list[str]:
    command = [
        sys.executable,
        "-B",
        str(runtime / "scripts/arrp_nightly.py"),
        "--canonical-path",
        str(repository),
        "--state-root",
        str(state_root),
        "--runtime-commit",
        revision,
    ]
    command.append("--manual" if manual else "--scheduled")
    return command


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manual", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        runtime, revision = reviewed_runtime()
        command = build_command(runtime, revision, manual=args.manual)
        if args.dry_run:
            print(json.dumps({"runtime_commit": revision, "command": command}))
            return 0
        return subprocess.run(command, check=False).returncode
    except (BootstrapError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ARRP_BOOTSTRAP_FAILED: {error}", file=sys.stderr)
        return 70


if __name__ == "__main__":
    raise SystemExit(main())
