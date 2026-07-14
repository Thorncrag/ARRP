"""Map staged public pages to canonical files for Git revision-date lookup.

ARRP builds its public site from an allowlisted copy under ``.site-build``.
The revision-date plugin therefore needs the canonical repository path while it
queries Git, then the staged path restored before the rest of the build runs.
"""

from __future__ import annotations

from pathlib import Path

from mkdocs.plugins import event_priority


ROOT = Path(__file__).resolve().parents[1]
_STAGED_SOURCE_PATHS: dict[int, str] = {}


def canonical_source_path(source_uri: str) -> Path | None:
    """Resolve a staged MkDocs URI to its canonical repository source."""
    relative = Path(source_uri)
    if relative == Path("legislation/index.md"):
        return None
    if relative == Path("index.md"):
        relative = Path("README.md")
    elif relative.name == "index.md":
        relative = relative.with_name("README.md")

    candidate = ROOT / relative
    return candidate if candidate.is_file() else None


@event_priority(100)
def on_page_markdown(markdown, *, page, **_kwargs):
    """Expose the canonical path before the revision-date plugin runs."""
    canonical = canonical_source_path(page.file.src_uri)
    if canonical is None:
        return markdown

    staged = page.file.abs_src_path
    if staged is not None:
        _STAGED_SOURCE_PATHS[id(page.file)] = staged
        page.file.abs_src_path = str(canonical)
    return markdown


@event_priority(-100)
def on_page_content(html, *, page, **_kwargs):
    """Restore the staged path after Markdown and revision metadata are ready."""
    staged = _STAGED_SOURCE_PATHS.pop(id(page.file), None)
    if staged is not None:
        page.file.abs_src_path = staged
    return html
