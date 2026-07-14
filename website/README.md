---
title: "Public Website Build"
print_levels:
  - full-technical
---

# Public Website Build

ARRP uses one repository and one canonical `main` branch for both project development and the public website. GitHub Pages deploys a generated artifact; it does not publish the repository tree directly and does not use a `gh-pages` branch.

## Publication Boundary

The website build uses two gates:

1. a Markdown file must declare `public-proposal` in its `print_levels` metadata; and
2. it must be one of the approved root pages or live under `areas/` or `legislation/`.

The approved root pages are `README.md`, `SUBJECT_INDEX.md`, `AUTHORS.md`, and `LICENSE.md`. `CITATION.cff` is copied as an explicitly approved supporting file. Website styling, `robots.txt`, and the not-found page come from this directory.

This excludes the progress dashboard, GitHub Project configuration, audit sidecars, framework files, inventories, research, source-development files, archives, tests, scripts, exports, local secrets, and repository administration files. Links from published pages to excluded Markdown are rendered as plain text in the generated copy so the site does not create broken links or promote internal working apparatus.

The dashboard remains available on the `progress-dashboard` branch to a reader who deliberately browses the GitHub repository. It is not copied into the Pages artifact, linked from the public website, or included in the website navigation, search index, or sitemap.

## Build and Validation

Prepare the allowlisted source tree and generated navigation:

```sh
python3 scripts/prepare_public_site.py
```

Install the pinned site dependencies and build with warnings treated as errors:

```sh
python3 -m pip install -r requirements-pages.txt
python3 -m mkdocs build --strict --config-file .site-build/mkdocs.yml
```

The generated source tree, manifest, MkDocs configuration, and output site live under `.site-build/`, which is ignored by Git. The manifest records every canonical Markdown source admitted to the build and every internal link demoted because its target is outside the publication boundary.

## Deployment

`.github/workflows/public-site.yml` repeats the preparation and strict build on every push to `main`, uploads only `.site-build/site`, and deploys that artifact to GitHub Pages. The workflow may also be started manually.

The GitHub Pages site is intended to be indexed normally. The dashboard requires no website `noindex` rule because it has no Pages URL. GitHub controls indexing of public repository content on `github.com`; ARRP cannot impose a per-branch or per-file crawler rule there.
