#!/usr/bin/env python3
"""Build or query an ignored, provenance-verified ARRP FTS retrieval index."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from arrp_context import ContextError, ROOT, file_provenance, git_revision, sha256_path


DEFAULT_INDEX = ROOT / ".tmp" / "arrp-corpus-index.sqlite3"
AUTHORITY_NOTICE = (
    "Retrieval aid only. Results are not substantive authority and must be verified "
    "against the cited canonical record."
)


def corpus_paths(root: Path) -> list[Path]:
    paths = []
    for pattern in (
        "areas/*/issues/*.md",
        "areas/*/research/*.md",
        "legislation/*.md",
        "research/*.md",
        "framework/logs/*.md",
    ):
        paths.extend(root.glob(pattern))
    return sorted(
        {
            path.resolve()
            for path in paths
            if path.is_file()
            and "horizon-review-console" not in path.parts
            and not path.name.startswith(".")
        }
    )


def ensure_ignored_output(root: Path, output: Path) -> Path:
    resolved = output.resolve()
    temp_root = (root / ".tmp").resolve()
    if temp_root not in resolved.parents:
        raise ContextError("corpus index output must remain under the ignored .tmp directory")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def build_index(root: Path, output: Path) -> dict[str, object]:
    root = root.resolve()
    output = ensure_ignored_output(root, output)
    if output.exists():
        output.unlink()
    connection = sqlite3.connect(output)
    try:
        connection.executescript(
            """
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE files (path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, bytes INTEGER NOT NULL);
            CREATE VIRTUAL TABLE corpus USING fts5(
                record_key UNINDEXED,
                kind UNINDEXED,
                path UNINDEXED,
                title,
                content,
                tokenize='porter unicode61'
            );
            """
        )
        documents = 0
        for path in corpus_paths(root):
            relative = path.relative_to(root).as_posix()
            content = path.read_text(encoding="utf-8", errors="replace")
            title = next(
                (line.lstrip("# ").strip() for line in content.splitlines() if line.startswith("# ")),
                path.stem,
            )
            kind = (
                "audit"
                if path.name.endswith(".audit.md")
                else "issue"
                if "/issues/" in f"/{relative}"
                else "vehicle"
                if relative.startswith("legislation/")
                else "research"
                if "/research/" in f"/{relative}" or relative.startswith("research/")
                else "log"
            )
            connection.execute(
                "INSERT INTO corpus(record_key, kind, path, title, content) VALUES (?, ?, ?, ?, ?)",
                (path.stem, kind, relative, title, content),
            )
            provenance = file_provenance(path, root)
            connection.execute(
                "INSERT INTO files(path, sha256, bytes) VALUES (?, ?, ?)",
                (relative, provenance["sha256"], provenance["bytes"]),
            )
            documents += 1
        sources_path = root / "inventory" / "sources.csv"
        if sources_path.is_file():
            with sources_path.open("r", encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    record_key = str(row.get("Source ID") or "")
                    title = str(row.get("Title or Description") or record_key)
                    content = " | ".join(
                        str(row.get(field) or "")
                        for field in (
                            "Associated Record IDs",
                            "Authority / Publisher",
                            "Proposition Supported",
                            "Reliability Tier",
                            "Reviewed?",
                            "Notes",
                            "Next Action",
                        )
                    )
                    connection.execute(
                        "INSERT INTO corpus(record_key, kind, path, title, content) VALUES (?, 'source', ?, ?, ?)",
                        (record_key, "inventory/sources.csv", title, content),
                    )
                    documents += 1
            provenance = file_provenance(sources_path, root)
            connection.execute(
                "INSERT INTO files(path, sha256, bytes) VALUES (?, ?, ?)",
                ("inventory/sources.csv", provenance["sha256"], provenance["bytes"]),
            )
        metadata = {
            "schema_version": "1",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "repository_revision": git_revision(root),
            "authority_notice": AUTHORITY_NOTICE,
        }
        connection.executemany("INSERT INTO metadata(key, value) VALUES (?, ?)", metadata.items())
        connection.commit()
    finally:
        connection.close()
    return {
        "schema_version": 1,
        "status": "built",
        "path": output.relative_to(root).as_posix(),
        "sha256": sha256_path(output),
        "records": documents,
        "authority_notice": AUTHORITY_NOTICE,
    }


def verify_index(root: Path, connection: sqlite3.Connection) -> dict[str, str]:
    files = dict(connection.execute("SELECT path, sha256 FROM files"))
    current_paths = {
        path.resolve().relative_to(root.resolve()).as_posix() for path in corpus_paths(root)
    }
    if (root / "inventory/sources.csv").is_file():
        current_paths.add("inventory/sources.csv")
    if current_paths != set(files):
        added = sorted(current_paths - set(files))
        removed = sorted(set(files) - current_paths)
        raise ContextError(
            f"corpus membership changed; rebuild before querying (added={added}, removed={removed})"
        )
    for relative, expected in files.items():
        path = root / relative
        if not path.is_file():
            raise ContextError(f"indexed canonical input is missing: {relative}")
        actual = sha256_path(path)
        if actual != expected:
            raise ContextError(f"corpus index is stale for {relative}; rebuild before querying")
    return dict(connection.execute("SELECT key, value FROM metadata"))


def query_index(
    root: Path,
    index: Path,
    query: str,
    *,
    limit: int = 10,
    max_bytes: int = 20000,
    kinds: list[str] | None = None,
) -> dict[str, object]:
    if limit < 1 or limit > 50 or max_bytes < 1000 or max_bytes > 200000:
        raise ContextError("query bounds are outside the reviewed range")
    if not index.is_file():
        raise ContextError("corpus index is missing; build it before querying")
    connection = sqlite3.connect(index)
    connection.row_factory = sqlite3.Row
    try:
        metadata = verify_index(root, connection)
        parameters: list[object] = [query]
        where = "corpus MATCH ?"
        if kinds:
            placeholders = ",".join("?" for _ in kinds)
            where += f" AND kind IN ({placeholders})"
            parameters.extend(kinds)
        parameters.append(limit)
        rows = connection.execute(
            f"""
            SELECT record_key, kind, path, title,
                   snippet(corpus, 4, '[', ']', ' … ', 32) AS snippet,
                   bm25(corpus) AS rank
            FROM corpus
            WHERE {where}
            ORDER BY rank
            LIMIT ?
            """,
            parameters,
        ).fetchall()
    except sqlite3.Error as exc:
        raise ContextError(f"invalid or failed corpus query: {exc}") from exc
    finally:
        connection.close()
    results = []
    used = 0
    for row in rows:
        item = dict(row)
        size = len(json.dumps(item, ensure_ascii=False).encode("utf-8"))
        if used + size > max_bytes:
            break
        results.append(item)
        used += size
    return {
        "schema_version": 1,
        "query": query,
        "kinds": kinds or [],
        "limits": {"maximum_results": limit, "maximum_bytes": max_bytes, "actual_bytes": used},
        "index_revision": metadata.get("repository_revision"),
        "index_generated_at": metadata.get("generated_at"),
        "authority_notice": AUTHORITY_NOTICE,
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--output", type=Path, default=DEFAULT_INDEX)
    query = commands.add_parser("query")
    query.add_argument("query")
    query.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    query.add_argument("--limit", type=int, default=10)
    query.add_argument("--max-bytes", type=int, default=20000)
    query.add_argument("--kind", action="append", choices=["issue", "audit", "vehicle", "research", "source", "log"])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = (
            build_index(ROOT, args.output)
            if args.command == "build"
            else query_index(
                ROOT,
                args.index,
                args.query,
                limit=args.limit,
                max_bytes=args.max_bytes,
                kinds=args.kind,
            )
        )
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0
    except ContextError as exc:
        json.dump({"schema_version": 1, "status": "blocked", "error": str(exc)}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
