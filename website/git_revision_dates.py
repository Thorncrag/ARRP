"""Map staged public pages to canonical files for Git revision-date lookup.

ARRP builds its public site from an allowlisted copy under ``.site-build``.
The revision-date plugin therefore needs the canonical repository path while it
queries Git, then the staged path restored before the rest of the build runs.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from mkdocs.plugins import event_priority


ROOT = Path(__file__).resolve().parents[1]
_STAGED_SOURCE_PATHS: dict[int, str] = {}
_FIRST_HEADING = re.compile(r"(?m)^#\s+.+?(?:\n|$)")


def proposal_score_band(score: object) -> tuple[str, int | None]:
    """Return the project score band and normalized integer score."""
    try:
        value = int(score)
    except (TypeError, ValueError):
        return "Developed issue", None

    if value >= 100:
        return "Fully Validated", value
    if value >= 95:
        return "Publication Ready", value
    if value >= 90:
        return "Proposal Ready", value
    if value >= 85:
        return "Advanced Review Ready", value
    if value >= 75:
        return "Review Ready", value
    if value >= 65:
        return "Substantially Developed Draft", value
    if value >= 50:
        return "Developed Draft", value
    if value >= 1:
        return "Early/Partial Draft", value
    return "Not Scored", value


def issue_status_notice(metadata: dict) -> str:
    """Build a concise public status notice from canonical issue metadata."""
    if not metadata.get("issue_id"):
        return ""

    status = str(metadata.get("status", "")).strip().lower()
    if status == "candidate":
        label = "Candidate issue"
        detail = (
            "This subject is under investigation. Its inclusion is not an affirmative "
            "project recommendation."
        )
    elif status == "deferred":
        label = "Deferred issue"
        detail = "This subject is retained for possible future development and is not an active recommendation."
    elif status == "awaiting-merits-adjudication":
        label = "Awaiting merits adjudication"
        detail = "Development is paused pending a controlling merits decision; this is not an active recommendation."
    else:
        label, score = proposal_score_band(metadata.get("audit_score"))
        score_text = f"Proposal Quality Score: {score}/100. " if score is not None else ""
        if label == "Review Ready":
            meaning = "Ready for knowledgeable external critique; not final or publication-ready."
        elif label == "Advanced Review Ready":
            meaning = "Advanced internal development is complete, but external validation remains necessary."
        elif label in {"Proposal Ready", "Publication Ready", "Fully Validated"}:
            meaning = "Consult the proposal scoring and annotations for the remaining qualifications."
        else:
            meaning = "Working draft; not final or ready for introduction."
        detail = score_text + meaning

    return (
        '<aside class="arrp-issue-status" role="note" aria-label="Project status">\n'
        f'  <strong class="arrp-issue-status__label">Project status: {html.escape(label)}</strong>\n'
        f'  <span class="arrp-issue-status__detail">{html.escape(detail)}</span>\n'
        "</aside>"
    )


def page_actions() -> str:
    """Return static actions enhanced by the public-site JavaScript."""
    return (
        '<nav class="arrp-page-actions" aria-label="Page actions">\n'
        '  <button type="button" class="arrp-page-action" data-arrp-print>Print this page</button>\n'
        '  <a class="arrp-page-action" data-arrp-feedback '
        'href="mailto:smith.benjamin.j@icloud.com">Report an error or offer review</a>\n'
        "</nav>"
    )


def add_public_page_tools(markdown: str, metadata: dict) -> str:
    """Insert status and actions immediately after a page's first heading."""
    heading = _FIRST_HEADING.search(markdown)
    if heading is None:
        return markdown

    additions = [notice for notice in (issue_status_notice(metadata), page_actions()) if notice]
    return markdown[: heading.end()] + "\n" + "\n\n".join(additions) + "\n" + markdown[heading.end() :]


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
    """Expose the canonical path and add the public page tools."""
    if page.file.src_uri == "404.md":
        return markdown

    canonical = canonical_source_path(page.file.src_uri)
    if canonical is not None:
        staged = page.file.abs_src_path
        if staged is not None:
            _STAGED_SOURCE_PATHS[id(page.file)] = staged
            page.file.abs_src_path = str(canonical)
    return add_public_page_tools(markdown, page.meta)


@event_priority(-100)
def on_page_content(html, *, page, **_kwargs):
    """Restore the staged path after Markdown and revision metadata are ready."""
    staged = _STAGED_SOURCE_PATHS.pop(id(page.file), None)
    if staged is not None:
        page.file.abs_src_path = staged
    return html


@event_priority(100)
def on_page_context(context, *, page, **_kwargs):
    """Give the footer date a visible, self-explanatory label."""
    revision_date = page.meta.get("git_revision_date_localized")
    if revision_date and not str(revision_date).startswith("Last modified:"):
        page.meta["git_revision_date_localized"] = f"Last modified: {revision_date}"
    return context
