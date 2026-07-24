#!/usr/bin/env python3
"""Safe project-tree traversal that never descends into generated roots."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path


DEFAULT_EXCLUDED_ROOTS = frozenset({".git", ".site-build", ".tmp", ".venv"})


def iter_project_files(
    root: Path,
    pattern: str = "*",
    *,
    excluded_roots: frozenset[str] = DEFAULT_EXCLUDED_ROOTS,
) -> Iterator[Path]:
    """Yield matching files without asking pathlib to traverse excluded roots."""
    for top_level in sorted(root.iterdir()):
        if top_level.name in excluded_roots:
            continue
        if top_level.is_file():
            if top_level.match(pattern):
                yield top_level
            continue
        if top_level.is_symlink() or not top_level.is_dir():
            continue
        for path in top_level.rglob(pattern):
            if path.is_file() and not excluded_roots.intersection(
                path.relative_to(root).parts
            ):
                yield path
