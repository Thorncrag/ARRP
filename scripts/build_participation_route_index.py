#!/usr/bin/env python3
"""Build the server-side public-intake route index from participation data."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "participate" / "intake-data.js"
OUTPUT = ROOT / "participate" / "api" / "route-index.js"
PREFIX = "window.ARRP_PARTICIPATION_DATA="


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    start = source.find(PREFIX)
    if start < 0:
        raise RuntimeError(f"{SOURCE} does not contain the participation-data assignment.")
    payload = json.loads(source[start + len(PREFIX):].strip().removesuffix(";"))
    records = [
        {
            "id": record["id"],
            "title": record["title"],
            "area": record["area"],
            "canonical_page": record["canonical_page"],
            "issue_url": record["issue_url"],
        }
        for record in [*payload["proposal_index"], *payload["horizon_index"]]
    ]
    serialized = json.dumps(records, ensure_ascii=False, indent=2)
    target = OUTPUT.read_text(encoding="utf-8")
    before, marker, after = target.partition("const records = Object.freeze(")
    if not marker:
        raise RuntimeError(f"{OUTPUT} does not contain the route-record marker.")
    end = after.find(");\n\nconst proposals")
    if end < 0:
        raise RuntimeError(f"{OUTPUT} does not contain the route-record terminator.")
    updated = f"{before}{marker}{serialized}{after[end:]}"
    OUTPUT.write_text(updated, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(records)} route records.")


if __name__ == "__main__":
    main()
