#!/usr/bin/env python3
"""Verify and privately inventory an inactive owner-local runtime successor."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from path_authority import (
        PathAuthorityError,
        PrivateProjectAuthority,
        ProjectPathAuthority,
    )
except ModuleNotFoundError:
    from scripts.path_authority import (
        PathAuthorityError,
        PrivateProjectAuthority,
        ProjectPathAuthority,
    )


SCHEMA_VERSION = 1


class MigrationVerificationError(ValueError):
    """Raised when the inactive successor cannot be verified safely."""


def iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def inventory_tree(root: Path, *, deep: bool) -> dict[str, Any]:
    """Return a deterministic private manifest without following links."""

    entries: list[dict[str, Any]] = []
    file_count = 0
    directory_count = 0
    symlink_count = 0
    other_count = 0
    hard_link_count = 0
    total_bytes = 0
    for current, directory_names, file_names in os.walk(
        root, topdown=True, followlinks=False
    ):
        directory_names.sort()
        file_names.sort()
        current_path = Path(current)
        for name in list(directory_names):
            path = current_path / name
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                directory_names.remove(name)
                symlink_count += 1
                entries.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "type": "symlink",
                        "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
                        "size": metadata.st_size,
                        "mtime_ns": metadata.st_mtime_ns,
                        "target": os.readlink(path),
                    }
                )
                continue
            if not stat.S_ISDIR(metadata.st_mode):
                directory_names.remove(name)
                other_count += 1
                entries.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "type": "unsupported",
                        "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
                        "size": metadata.st_size,
                        "mtime_ns": metadata.st_mtime_ns,
                    }
                )
                continue
            relative = path.relative_to(root).as_posix()
            directory_count += 1
            entries.append(
                {
                    "path": relative,
                    "type": "directory",
                    "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
                    "size": 0,
                    "mtime_ns": metadata.st_mtime_ns,
                }
            )
        for name in file_names:
            path = current_path / name
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                symlink_count += 1
                entries.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "type": "symlink",
                        "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
                        "size": metadata.st_size,
                        "mtime_ns": metadata.st_mtime_ns,
                        "target": os.readlink(path),
                    }
                )
                continue
            if not stat.S_ISREG(metadata.st_mode):
                other_count += 1
                entries.append(
                    {
                        "path": path.relative_to(root).as_posix(),
                        "type": "unsupported",
                        "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
                        "size": metadata.st_size,
                        "mtime_ns": metadata.st_mtime_ns,
                    }
                )
                continue
            relative = path.relative_to(root).as_posix()
            file_count += 1
            if metadata.st_nlink > 1:
                hard_link_count += 1
            total_bytes += metadata.st_size
            entry = {
                "path": relative,
                "type": "file",
                "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
                "size": metadata.st_size,
                "mtime_ns": metadata.st_mtime_ns,
            }
            if deep:
                entry["sha256"] = _file_digest(path)
            entries.append(entry)
    payload = json.dumps(
        entries,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "root": str(root),
        "deep": deep,
        "file_count": file_count,
        "directory_count": directory_count + 1,
        "symlink_count": symlink_count,
        "unsupported_count": other_count,
        "hard_link_count": hard_link_count,
        "total_bytes": total_bytes,
        "manifest_sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
        "entries": entries,
    }


def _regular_owner_control(path: Path, *, required: bool) -> dict[str, Any]:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        if required:
            raise MigrationVerificationError(
                "required runtime control is unavailable"
            )
        return {"present": False, "mode": None}
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) & 0o077
    ):
        raise MigrationVerificationError(
            "runtime control is not a safe owner-only regular file"
        )
    return {
        "present": True,
        "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
        "mtime_ns": metadata.st_mtime_ns,
    }


def _lock_is_free(path: Path) -> bool:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise MigrationVerificationError(
                "runtime lock is not a regular file"
            )
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            except OSError:
                pass
        return True
    finally:
        os.close(descriptor)


def build_manifest(
    *,
    private_authority: PrivateProjectAuthority | None = None,
    deep: bool,
) -> dict[str, Any]:
    """Inventory the legacy runtime against one explicit inactive successor."""

    current = ProjectPathAuthority.production()
    if current.mode != "production_canonical":
        raise MigrationVerificationError(
            "current runtime authority is not the approved production authority"
        )
    successor = (
        private_authority
        if private_authority is not None
        else PrivateProjectAuthority.production_staging()
    )
    pause = _regular_owner_control(current.state_root / "PAUSED", required=True)
    lock = _regular_owner_control(current.state_root / "run.lock", required=True)
    lock["free"] = _lock_is_free(current.state_root / "run.lock")
    if not lock["free"]:
        raise MigrationVerificationError(
            "runtime lock is currently owned; migration must remain inactive"
        )
    current_inventory = inventory_tree(current.state_root, deep=deep)
    successor_inventory = inventory_tree(successor.private_root, deep=deep)
    hazards = {
        "current_symlinks": current_inventory["symlink_count"],
        "current_unsupported_types": current_inventory["unsupported_count"],
        "current_hard_links": current_inventory["hard_link_count"],
        "successor_symlinks": successor_inventory["symlink_count"],
        "successor_unsupported_types": successor_inventory[
            "unsupported_count"
        ],
        "successor_hard_links": successor_inventory["hard_link_count"],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": iso_utc(),
        "status": "inactive_successor_inventory_complete",
        "activation_authorized": False,
        "current_authority": str(current.state_root),
        "successor_private_root": str(successor.private_root),
        "successor_roots": {
            "runtime": str(successor.runtime_root),
            "records": str(successor.records_root),
            "owner_console_versions": str(successor.owner_console_versions_root),
            "control_packs": str(successor.control_pack_root),
        },
        "pause": pause,
        "lock": lock,
        "migration_hazards": hazards,
        "current_inventory": current_inventory,
        "successor_inventory": successor_inventory,
    }


def _write_new_private_manifest(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Hash every regular file into the private migration manifest.",
    )
    parser.add_argument(
        "--output-relative",
        help=(
            "Write a new owner-only manifest below the descriptor migration role. "
            "Existing files are never replaced."
        ),
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    successor = PrivateProjectAuthority.production_staging()
    manifest = build_manifest(private_authority=successor, deep=args.deep)
    if args.output_relative:
        output = successor.migration_output(args.output_relative)
        _write_new_private_manifest(output, manifest)
        summary = {
            "schema_version": manifest["schema_version"],
            "status": manifest["status"],
            "generated_at": manifest["generated_at"],
            "activation_authorized": False,
            "output": str(output),
            "current_manifest_sha256": manifest["current_inventory"][
                "manifest_sha256"
            ],
            "successor_manifest_sha256": manifest["successor_inventory"][
                "manifest_sha256"
            ],
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        redacted = dict(manifest)
        redacted["current_inventory"] = {
            key: value
            for key, value in manifest["current_inventory"].items()
            if key != "entries"
        }
        redacted["successor_inventory"] = {
            key: value
            for key, value in manifest["successor_inventory"].items()
            if key != "entries"
        }
        print(json.dumps(redacted, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, PathAuthorityError, MigrationVerificationError) as error:
        raise SystemExit(f"migration verification failed: {error}") from None
