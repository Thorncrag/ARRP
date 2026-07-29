#!/usr/bin/env python3
"""Inspect and package one registered ARRP runtime transaction safely.

The production CLI accepts only a stable run ID. Repository, runtime, and
recovery roots come from the fixed project path authority. It never removes a
worktree, branch, run directory, or Git reference and never starts automation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from path_authority import PathAuthorityError, ProjectPathAuthority
    from transaction_lifecycle import (
        TransactionLifecycleError,
        build_console_projection,
        create_recovery_package,
        read_events,
    )
except ModuleNotFoundError:
    from scripts.path_authority import PathAuthorityError, ProjectPathAuthority
    from scripts.transaction_lifecycle import (
        TransactionLifecycleError,
        build_console_projection,
        create_recovery_package,
        read_events,
    )


RUN_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
RECOVERY_RELATIVE_ROOT = "records/reconciliation/transaction-recovery"
EVENTS_RELATIVE_PATH = "records/automation/transaction-events.jsonl"


class TransactionRecoveryError(ValueError):
    """A registered transaction cannot be inspected or packaged safely."""


@dataclass(frozen=True)
class TransactionMaterial:
    run_id: str
    repository: Path
    branch: str
    head: str
    base: str
    commit_bundle: bytes
    delta: bytes
    untracked: dict[str, bytes]
    clean: bool
    head_in_origin_main: bool
    base_in_origin_main: bool


def _git_bytes(repository: Path, *args: str, timeout: int = 60) -> bytes:
    result = subprocess.run(
        ["git", "-C", os.fspath(repository), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=timeout,
    )
    if result.returncode:
        raise TransactionRecoveryError("registered transaction Git read failed")
    return result.stdout


def _git(repository: Path, *args: str) -> str:
    return _git_bytes(repository, *args).decode("utf-8").strip()


def _is_ancestor(repository: Path, older: str, newer: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            os.fspath(repository),
            "merge-base",
            "--is-ancestor",
            older,
            newer,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=30,
    )
    if result.returncode not in {0, 1}:
        raise TransactionRecoveryError("registered transaction ancestry is unavailable")
    return result.returncode == 0


def _registered_worktree(repository: Path, expected: Path) -> dict[str, str]:
    blocks: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in [
        *_git(repository, "worktree", "list", "--porcelain").splitlines(),
        "",
    ]:
        if not line:
            if current:
                blocks.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    matches = [
        block
        for block in blocks
        if Path(block.get("worktree", "")).resolve() == expected.resolve()
    ]
    if len(matches) != 1:
        raise TransactionRecoveryError(
            "runtime worktree is not registered exactly once"
        )
    return matches[0]


def _untracked_material(repository: Path) -> dict[str, bytes]:
    root = repository.resolve()
    material: dict[str, bytes] = {}
    for raw in sorted(
        item
        for item in _git_bytes(
            repository,
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
        ).split(b"\0")
        if item
    ):
        try:
            relative = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise TransactionRecoveryError(
                "untracked transaction path is not valid UTF-8"
            ) from error
        candidate = root.joinpath(*relative.split("/"))
        try:
            resolved = candidate.resolve(strict=True)
            metadata = candidate.lstat()
        except OSError as error:
            raise TransactionRecoveryError(
                "untracked transaction material is unavailable"
            ) from error
        if (
            root not in resolved.parents
            or stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
        ):
            raise TransactionRecoveryError(
                "untracked transaction material is unsafe"
            )
        material[relative] = candidate.read_bytes()
    return material


def collect_transaction_material(
    authority: ProjectPathAuthority,
    run_id: str,
) -> TransactionMaterial:
    """Collect exact Git and worktree material for one typed runtime run."""

    if not RUN_ID.fullmatch(run_id):
        raise TransactionRecoveryError("run ID is invalid")
    worktree = authority.state_root / "worktrees" / run_id
    run_root = authority.state_root / "runs" / run_id
    try:
        transaction = (
            ProjectPathAuthority.production_transaction(
                repository_root=worktree,
                run_root=run_root,
            )
            if authority.mode == "production_canonical"
            else ProjectPathAuthority.fixture(
                authority.fixture_root or authority.state_root.parent,
                repository_root=worktree,
                state_root=authority.state_root,
                output_root=run_root,
            )
        )
    except PathAuthorityError as error:
        raise TransactionRecoveryError(
            "run and worktree do not have a matching transaction authority"
        ) from error

    repository = transaction.repository_root
    block = _registered_worktree(authority.repository_root, repository)
    branch_ref = block.get("branch")
    if not branch_ref or not branch_ref.startswith("refs/heads/"):
        raise TransactionRecoveryError("runtime worktree lacks a local branch")
    branch = branch_ref.removeprefix("refs/heads/")
    if not branch.startswith("automation/nightly-"):
        raise TransactionRecoveryError("runtime worktree branch is not registered")
    symbolic = _git(repository, "symbolic-ref", "--quiet", "--short", "HEAD")
    head = _git(repository, "rev-parse", "--verify", "HEAD^{commit}")
    if symbolic != branch or block.get("HEAD") != head:
        raise TransactionRecoveryError("runtime worktree identity is inconsistent")
    origin_main = _git(
        authority.repository_root,
        "rev-parse",
        "--verify",
        "refs/remotes/origin/main^{commit}",
    )
    base = _git(repository, "merge-base", head, origin_main)
    base_in_origin = _is_ancestor(repository, base, origin_main)
    if not base_in_origin:
        raise TransactionRecoveryError(
            "transaction base is not contained in origin/main"
        )

    status = _git_bytes(
        repository,
        "status",
        "--porcelain=v2",
        "-z",
        "--untracked-files=all",
    )
    delta = _git_bytes(
        repository,
        "diff",
        "--binary",
        "--no-ext-diff",
        base,
        "--",
    )
    if head == base:
        commit_bundle = b""
    else:
        commit_bundle = _git_bytes(
            repository,
            "bundle",
            "create",
            "-",
            branch,
            f"^{base}",
            timeout=120,
        )
    return TransactionMaterial(
        run_id=run_id,
        repository=repository,
        branch=branch,
        head=head,
        base=base,
        commit_bundle=commit_bundle,
        delta=delta,
        untracked=_untracked_material(repository),
        clean=not status,
        head_in_origin_main=_is_ancestor(repository, head, origin_main),
        base_in_origin_main=base_in_origin,
    )


def safe_inventory(material: TransactionMaterial) -> dict[str, Any]:
    """Return a path-free deterministic classification for operator review."""

    if material.clean and material.head_in_origin_main:
        classification = "incorporated"
    elif material.clean and material.head == material.base:
        classification = "duplicate_superseded"
    else:
        classification = "unique_review_required"
    return {
        "schema_version": 1,
        "run_id": material.run_id,
        "branch": material.branch,
        "head": material.head,
        "base": material.base,
        "clean": material.clean,
        "head_in_origin_main": material.head_in_origin_main,
        "base_in_origin_main": material.base_in_origin_main,
        "classification": classification,
        "commit_digest": "sha256:"
        + hashlib.sha256(material.commit_bundle).hexdigest(),
        "delta_digest": "sha256:" + hashlib.sha256(material.delta).hexdigest(),
        "untracked_count": len(material.untracked),
    }


def package_transaction(
    authority: ProjectPathAuthority,
    run_id: str,
) -> dict[str, Any]:
    """Create a fixed-root owner-only package without retiring source state."""

    material = collect_transaction_material(authority, run_id)
    recovery_root = authority.state_root / RECOVERY_RELATIVE_ROOT
    manifest = create_recovery_package(
        recovery_root,
        run_id=run_id,
        branch=material.branch,
        head=material.head,
        base=material.base,
        commit_bundle=material.commit_bundle,
        diff=material.delta,
        untracked=material.untracked,
    )
    return {
        **safe_inventory(material),
        "classification": "recovery_packaged",
        "recovery_package_id": manifest["recovery_package_id"],
        "package_digest": manifest["package_digest"],
        "manifest_sha256": manifest["manifest_sha256"],
    }


def refresh_console_projection(authority: ProjectPathAuthority) -> dict[str, Any]:
    """Write the minimized owner-local queue projection at its fixed path."""

    recovery_root = authority.state_root / RECOVERY_RELATIVE_ROOT
    events = read_events(authority.state_root / EVENTS_RELATIVE_PATH)
    projection = build_console_projection(events)
    recovery_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if recovery_root.is_symlink() or not recovery_root.is_dir():
        raise TransactionRecoveryError("recovery root is unavailable")
    output = recovery_root / "console-projection.json"
    temporary = recovery_root / ".console-projection.pending"
    if temporary.exists():
        raise TransactionRecoveryError(
            "prior Console projection staging state requires review"
        )
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )
    try:
        payload = json.dumps(
            projection,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise TransactionRecoveryError(
                    "Console projection staging write was incomplete"
                )
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, output)
    os.chmod(output, 0o600)
    return {
        "schema_version": 1,
        "availability": projection["availability"],
        "complete": projection["complete"],
        "unresolved_count": len(projection["items"]),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("inspect", "package", "project"))
    parser.add_argument("--run-id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        authority = ProjectPathAuthority.production()
        if args.operation == "project":
            if args.run_id is not None:
                raise TransactionRecoveryError(
                    "Console projection does not accept a run ID"
                )
            material = refresh_console_projection(authority)
        else:
            if args.run_id is None:
                raise TransactionRecoveryError(
                    "transaction inspection or packaging requires a run ID"
                )
            material = (
                safe_inventory(
                    collect_transaction_material(authority, args.run_id)
                )
                if args.operation == "inspect"
                else package_transaction(authority, args.run_id)
            )
    except (
        OSError,
        subprocess.SubprocessError,
        PathAuthorityError,
        TransactionLifecycleError,
        TransactionRecoveryError,
    ):
        material = {
            "schema_version": 1,
            "run_id": args.run_id,
            "availability": "unavailable",
            "reason_code": "transaction-recovery-unavailable",
        }
        print(json.dumps(material, sort_keys=True, separators=(",", ":")))
        return 2
    print(json.dumps(material, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
