#!/usr/bin/env python3
"""Typed path authority for ARRP production transactions and test fixtures."""

from __future__ import annotations

import errno
import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


APPROVED_REPOSITORY_ROOT = Path(
    "/Users/benjaminsmith/Automation Workspaces/ARRP"
)
APPROVED_STATE_ROOT = Path(
    "/Users/benjaminsmith/Library/Application Support/ARRP"
)
FILE_PROVIDER_XATTR = "com.apple.file-provider-domain-id"
PRIVATE_AUTHORITY_SCHEMA_VERSION = 1
PRIVATE_AUTHORITY_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
)
PRIVATE_AUTHORITY_KEYS = frozenset(
    {
        "schema_version",
        "authority_id",
        "authority_mode",
        "activation_authorized",
        "private_root",
        "roles",
    }
)
PRIVATE_AUTHORITY_ROLE_KEYS = frozenset(
    {
        "runtime",
        "records",
        "owner_console_versions",
        "migration",
        "disclosure_control_packs",
    }
)


class PathAuthorityError(ValueError):
    """Raised when a path has no explicit ARRP production or fixture authority."""


def _relative_parts(relative: str) -> tuple[str, ...]:
    if (
        not isinstance(relative, str)
        or not relative
        or "\x00" in relative
        or "\\" in relative
    ):
        raise PathAuthorityError("path must be a normalized relative POSIX path")
    parsed = PurePosixPath(relative)
    parts = parsed.parts
    if (
        parsed.is_absolute()
        or parsed.as_posix() != relative
        or not parts
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise PathAuthorityError("path must be a normalized relative POSIX path")
    return parts


def _resolved_directory(path: Path) -> Path:
    try:
        if path.expanduser().is_symlink():
            raise PathAuthorityError("authorized root must not be a symlink")
        resolved = path.expanduser().resolve(strict=True)
    except OSError as error:
        raise PathAuthorityError("authorized root is unavailable") from error
    if not resolved.is_dir():
        raise PathAuthorityError("authorized root is not a directory")
    return resolved


def _owner_directory(path: Path) -> Path:
    resolved = _resolved_directory(path)
    metadata = resolved.stat()
    if (
        metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) & 0o077
    ):
        raise PathAuthorityError("owner-local root permissions are unsafe")
    return resolved


def _reject_symlink_ancestors(path: Path, *, floor: Path) -> None:
    """Reject a successor root whose governed ancestry contains a symlink."""

    normalized_floor = Path(os.path.abspath(os.fspath(floor)))
    normalized_path = Path(os.path.abspath(os.fspath(path)))
    if (
        normalized_path != normalized_floor
        and normalized_floor not in normalized_path.parents
    ):
        raise PathAuthorityError("authorized path is outside its storage floor")
    current = normalized_path
    governed: list[Path] = []
    while True:
        governed.append(current)
        if current == normalized_floor:
            break
        current = current.parent
    for candidate in reversed(governed):
        try:
            metadata = candidate.lstat()
        except OSError as error:
            raise PathAuthorityError(
                "authorized storage ancestry is unavailable"
            ) from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise PathAuthorityError(
                "authorized storage ancestry must contain only directories"
            )


def _file_provider_domain(path: Path) -> bytes | None:
    if hasattr(os, "listxattr"):
        try:
            names = os.listxattr(path)
        except OSError as error:
            no_attribute = {
                errno.ENODATA,
                getattr(errno, "ENOATTR", errno.ENODATA),
            }
            if error.errno in no_attribute:
                return None
            raise PathAuthorityError(
                "storage synchronization boundary cannot be verified"
            ) from error
    else:
        try:
            result = subprocess.run(
                ["/usr/bin/xattr", os.fspath(path)],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise PathAuthorityError(
                "storage synchronization boundary cannot be verified"
            ) from error
        if result.returncode != 0:
            raise PathAuthorityError(
                "storage synchronization boundary cannot be verified"
            )
        names = result.stdout.splitlines()
    return b"present" if FILE_PROVIDER_XATTR in names else None


def _reject_file_provider_boundary(path: Path, *, floor: Path) -> None:
    normalized_floor = Path(os.path.abspath(os.fspath(floor)))
    normalized_path = Path(os.path.abspath(os.fspath(path)))
    current = normalized_path
    governed: list[Path] = []
    while True:
        governed.append(current)
        if current == normalized_floor:
            break
        if normalized_floor not in current.parents:
            raise PathAuthorityError(
                "authorized path is outside its storage floor"
            )
        current = current.parent
    for candidate in governed:
        if _file_provider_domain(candidate):
            raise PathAuthorityError(
                "authorized storage must not use a File Provider boundary"
            )


def _direct_child(root: Path, path: Path, label: str) -> Path:
    normalized_root = os.path.normpath(os.path.abspath(os.fspath(root)))
    normalized_path = os.path.normpath(
        os.path.abspath(os.path.expanduser(os.fspath(path)))
    )
    if (
        not normalized_path.startswith(normalized_root + os.sep)
        or os.path.dirname(normalized_path) != normalized_root
    ):
        raise PathAuthorityError(f"{label} is outside its authorized boundary")
    resolved = _resolved_directory(Path(normalized_path))
    if resolved.parent != root:
        raise PathAuthorityError(f"{label} is outside its authorized boundary")
    return resolved


def _contained(root: Path, relative: str) -> Path:
    parts = _relative_parts(relative)
    parent = root
    for part in parts[:-1]:
        parent = parent / part
        try:
            metadata = parent.lstat()
        except OSError as error:
            raise PathAuthorityError("authorized parent is unavailable") from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise PathAuthorityError(
                "authorized parent must be a non-symlink directory"
            )
    return parent / parts[-1]


def _regular_owner_file(
    path: Path,
    *,
    required: bool,
    owner_only: bool,
) -> Path:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        if required:
            raise PathAuthorityError("authorized file is unavailable")
        return path
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise PathAuthorityError("authorized file must be a regular non-symlink")
    if owner_only and metadata.st_mode & 0o077:
        raise PathAuthorityError("authorized file must be owner-only")
    if metadata.st_uid != os.getuid():
        raise PathAuthorityError("authorized file has an unexpected owner")
    return path


def _requested_path(
    root: Path,
    requested: Path,
    *,
    required: bool,
    owner_only: bool,
) -> Path:
    normalized_root = os.path.normpath(os.path.abspath(os.fspath(root)))
    normalized_path = os.path.normpath(
        os.path.abspath(os.path.expanduser(os.fspath(requested)))
    )
    if (
        normalized_path != normalized_root
        and not normalized_path.startswith(normalized_root + os.sep)
    ):
        raise PathAuthorityError("requested path escapes its authorized root")
    relative = os.path.relpath(normalized_path, normalized_root)
    if not relative or relative == ".":
        raise PathAuthorityError("requested path must name a file")
    path = _contained(root, relative)
    return _regular_owner_file(
        path, required=required, owner_only=owner_only
    )


@dataclass(frozen=True)
class ProjectPathAuthority:
    """One explicit repository, state, and output authority."""

    mode: str
    repository_root: Path
    state_root: Path
    output_root: Path
    fixture_root: Path | None = None

    @classmethod
    def production(cls) -> "ProjectPathAuthority":
        repository = _resolved_directory(APPROVED_REPOSITORY_ROOT)
        state = _owner_directory(APPROVED_STATE_ROOT)
        return cls("production_canonical", repository, state, repository)

    @classmethod
    def production_transaction(
        cls,
        *,
        repository_root: Path,
        run_root: Path,
    ) -> "ProjectPathAuthority":
        """Authorize one reviewed worktree/run pair under the fixed state root."""

        state = _owner_directory(APPROVED_STATE_ROOT)
        worktrees = _owner_directory(state / "worktrees")
        runs = _owner_directory(state / "runs")
        repository = _direct_child(
            worktrees, repository_root, "transaction worktree"
        )
        output = _direct_child(runs, run_root, "transaction run root")
        _owner_directory(output)
        if repository.name != output.name:
            raise PathAuthorityError(
                "transaction worktree and run root identities do not match"
            )
        return cls("production_transaction", repository, state, output)

    @classmethod
    def repository_validation(cls, repository_root: Path) -> "ProjectPathAuthority":
        """Authorize the script's own checkout for non-publishing hash validation."""

        repository = _resolved_directory(repository_root)
        return cls(
            "repository_validation",
            repository,
            repository,
            repository,
        )

    @classmethod
    def fixture(
        cls,
        fixture_root: Path,
        *,
        repository_root: Path,
        state_root: Path | None = None,
        output_root: Path | None = None,
    ) -> "ProjectPathAuthority":
        fixture = _resolved_directory(fixture_root)
        repository = _resolved_directory(repository_root)
        state = _resolved_directory(state_root or fixture / "state")
        output = _resolved_directory(output_root or repository)
        for candidate in (repository, state, output):
            if candidate != fixture and fixture not in candidate.parents:
                raise PathAuthorityError("fixture path escapes the explicit fixture root")
        approved_repository = APPROVED_REPOSITORY_ROOT.resolve()
        approved_state = APPROVED_STATE_ROOT.resolve()
        production_roots = (
            approved_repository,
            approved_state,
        )
        if any(
            candidate == production
            or candidate in production.parents
            or production in candidate.parents
            for candidate in (fixture, repository, state, output)
            for production in production_roots
        ):
            raise PathAuthorityError("fixture authority cannot target production")
        return cls("fixture", repository, state, output, fixture)

    def repository_path(
        self,
        relative: str,
        *,
        required: bool = True,
    ) -> Path:
        path = _contained(self.repository_root, relative)
        return _regular_owner_file(
            path, required=required, owner_only=False
        )

    def state_path(
        self,
        relative: str,
        *,
        required: bool = True,
        owner_only: bool = True,
    ) -> Path:
        path = _contained(self.state_root, relative)
        return _regular_owner_file(
            path, required=required, owner_only=owner_only
        )

    def repository_output(self, relative: str) -> Path:
        return _contained(self.repository_root, relative)

    def state_output(self, relative: str) -> Path:
        return _contained(self.state_root, relative)

    def output_path(
        self,
        relative: str,
        *,
        required: bool = True,
        owner_only: bool = False,
    ) -> Path:
        path = _contained(self.output_root, relative)
        return _regular_owner_file(
            path, required=required, owner_only=owner_only
        )

    def output_file(self, requested: Path, *, required: bool = True) -> Path:
        return _requested_path(
            self.output_root,
            requested,
            required=required,
            owner_only=False,
        )

    def requested_repository_file(
        self,
        requested: Path,
        *,
        required: bool = True,
    ) -> Path:
        return _requested_path(
            self.repository_root,
            requested,
            required=required,
            owner_only=False,
        )

    def requested_state_file(
        self,
        requested: Path,
        *,
        required: bool = True,
        owner_only: bool = True,
    ) -> Path:
        return _requested_path(
            self.state_root,
            requested,
            required=required,
            owner_only=owner_only,
        )


@dataclass(frozen=True)
class PrivateProjectAuthority:
    """Validated inactive successor roles from an owner-only descriptor."""

    authority_id: str
    descriptor_path: Path
    private_root: Path
    runtime_root: Path
    records_root: Path
    owner_console_versions_root: Path
    migration_root: Path
    control_pack_root: Path

    @classmethod
    def staging(cls, descriptor_path: Path) -> "PrivateProjectAuthority":
        """Validate one explicitly selected non-publishing staging descriptor.

        The descriptor can identify an inactive candidate layout, but it can
        never establish production authority or authorize activation.
        """

        descriptor = _regular_owner_file(
            Path(descriptor_path),
            required=True,
            owner_only=True,
        )
        try:
            value = json.loads(descriptor.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise PathAuthorityError(
                "private staging authority descriptor is invalid"
            ) from error
        if not isinstance(value, dict) or set(value) != PRIVATE_AUTHORITY_KEYS:
            raise PathAuthorityError(
                "private staging authority descriptor has unknown or missing fields"
            )
        if (
            value.get("schema_version") != PRIVATE_AUTHORITY_SCHEMA_VERSION
            or value.get("authority_mode") != "inactive_successor_staging"
            or value.get("activation_authorized") is not False
            or not isinstance(value.get("authority_id"), str)
            or not PRIVATE_AUTHORITY_ID_PATTERN.fullmatch(
                value["authority_id"]
            )
            or not isinstance(value.get("private_root"), str)
            or not value["private_root"].startswith("/")
            or "\x00" in value["private_root"]
            or os.path.normpath(value["private_root"]) != value["private_root"]
            or not isinstance(value.get("roles"), dict)
            or set(value["roles"]) != PRIVATE_AUTHORITY_ROLE_KEYS
        ):
            raise PathAuthorityError(
                "private staging authority descriptor is unsupported"
            )
        private_candidate = Path(value["private_root"])
        _reject_symlink_ancestors(private_candidate, floor=Path("/"))
        _reject_file_provider_boundary(private_candidate, floor=Path("/"))
        private_root = _owner_directory(private_candidate)
        descriptor_resolved = descriptor.resolve(strict=True)
        if descriptor_resolved != private_root and private_root not in descriptor_resolved.parents:
            raise PathAuthorityError(
                "private staging descriptor is outside its declared authority"
            )
        _reject_symlink_ancestors(
            descriptor_resolved.parent,
            floor=private_root,
        )
        for production in (
            APPROVED_REPOSITORY_ROOT.resolve(),
            APPROVED_STATE_ROOT.resolve(),
        ):
            if (
                private_root == production
                or private_root in production.parents
                or production in private_root.parents
            ):
                raise PathAuthorityError(
                    "private staging authority overlaps production"
                )
        role_roots: dict[str, Path] = {}
        for role, relative in value["roles"].items():
            if not isinstance(relative, str):
                raise PathAuthorityError(
                    "private staging role path is invalid"
                )
            role_roots[role] = _owner_directory(
                _contained(private_root, relative)
            )
        role_values = tuple(role_roots.values())
        if len(set(role_values)) != len(role_values) or any(
            left in right.parents or right in left.parents
            for index, left in enumerate(role_values)
            for right in role_values[index + 1 :]
        ):
            raise PathAuthorityError(
                "private staging roles must resolve to disjoint directories"
            )
        roots = {
            "runtime_root": role_roots["runtime"],
            "records_root": role_roots["records"],
            "owner_console_versions_root": role_roots[
                "owner_console_versions"
            ],
            "migration_root": role_roots["migration"],
            "control_pack_root": role_roots["disclosure_control_packs"],
        }
        for root in roots.values():
            if root == private_root or private_root not in root.parents:
                raise PathAuthorityError(
                    "private staging role escapes its declared authority"
                )
        return cls(
            authority_id=value["authority_id"].strip(),
            descriptor_path=descriptor_resolved,
            private_root=private_root,
            **roots,
        )

    def runtime_output(self, relative: str) -> Path:
        return _contained(self.runtime_root, relative)

    def records_output(self, relative: str) -> Path:
        return _contained(self.records_root, relative)

    def records_path(
        self,
        relative: str,
        *,
        required: bool = True,
    ) -> Path:
        """Read one owner-only supplement from inactive successor records."""

        path = _contained(self.records_root, relative)
        return _regular_owner_file(path, required=required, owner_only=True)

    def console_version_output(self, relative: str) -> Path:
        return _contained(self.owner_console_versions_root, relative)

    def migration_output(self, relative: str) -> Path:
        return _contained(self.migration_root, relative)

    def control_pack_path(
        self,
        relative: str,
        *,
        required: bool = True,
    ) -> Path:
        path = _contained(self.control_pack_root, relative)
        return _regular_owner_file(
            path,
            required=required,
            owner_only=True,
        )
