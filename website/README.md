---
title: "Public Website Build"
print_levels:
  - full-technical
---

# Public Website Build

ARRP uses one repository and one canonical `main` branch for both project development and the public website. GitHub Pages deploys a generated artifact; it does not publish the repository tree directly and does not use a `gh-pages` branch.

The live site is [https://thorncrag.github.io/ARRP/](https://thorncrag.github.io/ARRP/), and the GitHub repository homepage points readers to that address.

## Publication Boundary

The website build uses two gates:

1. a Markdown file must declare `public-proposal` in its `print_levels` metadata; and
2. it must be one of the approved root pages or live under `areas/`, `legislation/`, or `topics/`.

The approved root pages are `README.md`, `SUBJECT_INDEX.md`, `AUTHORS.md`, and `LICENSE.md`. Public pages may also live under `areas/`, `legislation/`, or `topics/`. `CITATION.cff` is copied as an explicitly approved supporting file. Website styling, `robots.txt`, and the not-found page come from this directory.

This excludes the progress dashboard, GitHub Project configuration, audit sidecars, framework files, inventories, unpublished ARRP research, locally retained external sources, archives, tests, scripts, exports, local secrets, and repository administration files. A project-authored analysis selected for public topic treatment is moved into `topics/` rather than duplicated in `research/`. Links from published pages to excluded Markdown are rendered as plain text in the generated copy so the site does not create broken links or promote internal working apparatus.

The top-level `participate/` directory deploys separately as the public [ARRP participation service](https://arrp-public-intake.vercel.app/). It is intentionally not copied into the Pages artifact or the internal Candidate Issue Intake console. Its **Submit public input** route posts to a canonical public GitHub Discussion and returns the contributor's direct link; its **Contact the author** route sends a private message to the configured mailbox and creates no public record. A contributor may optionally provide an address for private follow-up, but it is never included in a public submission. The service's anti-abuse controls and manual Codex review boundary are governed by [`../participate/README.md`](../participate/README.md) and [`../framework/INTAKE_AGENT_PROCESS.md`](../framework/INTAKE_AGENT_PROCESS.md).

The dashboard remains available on the `progress-dashboard` branch to a reader who deliberately browses the GitHub repository. It is not copied into the Pages artifact, linked from the public website, or included in the website navigation, search index, or sitemap.

## Build and Validation

Prepare the allowlisted source tree and generated navigation:

```sh
python3 scripts/prepare_public_site.py
```

Bootstrap the project-local website and document environment once, then build with warnings treated as errors:

```sh
scripts/bootstrap_local_tools.sh
.venv/bin/python scripts/prepare_public_site.py
.venv/bin/python -m mkdocs build --strict --config-file .site-build/mkdocs.yml
```

The bootstrap uses a stable host Python installation and does not depend on packages bundled inside the Codex application. On macOS it also identifies any missing Homebrew commands required for PDF extraction and rendering, OCR, document conversion, local JavaScript tests, and repository search. Sandboxed document commands should put `/opt/homebrew/bin` first and set `XDG_CACHE_HOME="$PWD/.tmp/cache"` so they use the stable host tools and keep Fontconfig's writable cache inside the ignored workspace. GitHub Actions independently installs `requirements-pages.txt` in a fresh environment before publication.

The generated source tree, manifest, MkDocs configuration, and output site live under `.site-build/`, which is ignored by Git. The manifest records every canonical Markdown source admitted to the build and every internal link demoted because its target is outside the publication boundary.

Published pages display a localized **Last modified** date in the page footer. The revision-date plugin reads the most recent commit affecting each canonical Markdown source; `website/git_revision_dates.py` temporarily maps the allowlisted staging copy back to that source during the build and supplies the visible label. The generated legislation index uses the newest committed revision among the legislation pages it lists. The deployment checkout must retain full Git history so these dates remain accurate.

The same build hook adds a metadata-driven project-status notice to issue pages and supplies page-level print and feedback actions. Developed issues use the Proposal Quality Score band recorded in canonical front matter; candidate, deferred, and adjudication-dependent issues receive status-specific language that avoids presenting them as affirmative recommendations. The feedback action opens the separate participation service with the current page title and URL as route context; it does not expose an author email address in the website artifact. `website/site.js` supplies the print and participation-link behavior. Breadcrumbs, active-heading URL tracking, table-of-contents following, and shareable searches are enabled through Material configuration. The breadcrumb override under `website/overrides/` uses compact area codes and shows the current page identifier as an unlinked final location; full area and page titles remain in the navigation and page heading.

The **Explore by Topic** index remains a semantic Markdown list in the canonical repository and compiled editions. On the website, `website/extra.css` presents that list as a restrained two-column card grid, collapses it to one column on narrow screens, and restores an ordinary list for printing.

## Deployment

`.github/workflows/public-site.yml` repeats the preparation and strict build on every push to `main`, uploads only `.site-build/site`, and deploys that artifact to GitHub Pages. The workflow may also be started manually.

The GitHub Pages site is intended to be indexed normally. The dashboard requires no website `noindex` rule because it has no Pages URL. GitHub controls indexing of public repository content on `github.com`; ARRP cannot impose a per-branch or per-file crawler rule there.
