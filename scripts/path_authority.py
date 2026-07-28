#!/usr/bin/env python3
"""Typed path authority for ARRP production transactions and test fixtures."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


APPROVED_REPOSITORY_ROOT = Path(
    "/Users/benjaminsmith/Automation Workspaces/ARRP"
)
APPROVED_STATE_ROOT = Path(
    "/Users/benjaminsmith/Library/Application Support/ARRP"
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


def _direct_child(root: Path, path: Path, label: str) -> Path:
    resolved = _resolved_directory(path)
    if resolved.parent != root:
        raise PathAuthorityError(f"{label} is outside its authorized boundary")
    return resolved


def _contained(root: Path, relative: str) -> Path:
    parts = _relative_parts(relative)
    candidate = root.joinpath(*parts)
    resolved_parent = candidate.parent.resolve(strict=True)
    if resolved_parent != root and root not in resolved_parent.parents:
        raise PathAuthorityError("path escapes its authorized root")
    return resolved_parent / candidate.name


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
    expanded = requested.expanduser()
    try:
        if expanded.is_symlink():
            raise PathAuthorityError("requested path must not be a symlink")
        resolved = expanded.resolve(strict=required)
    except OSError as error:
        raise PathAuthorityError("requested path is unavailable") from error
    if resolved != root and root not in resolved.parents:
        raise PathAuthorityError("requested path escapes its authorized root")
    relative = resolved.relative_to(root).as_posix()
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
        production_roots = (approved_repository, approved_state)
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
