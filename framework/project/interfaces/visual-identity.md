---
title: "ARRP Tool Visual Identity"
status: active
authority_scope: "ARRP-specific colors, brand mark, variables, typography, tool theme, and public topic-guide presentation classes."
load_when: "Styling or reviewing an ARRP dashboard, console, intake form, other application-like interface, or public topic-guide layout."
dependencies:
  - "../../standards/interfaces/standard.md"
print_status: excluded
print_exclusion_reason: "Internal interface configuration."
---

# ARRP Tool Visual Identity

ARRP-operated interfaces use a deep navy-to-blue gradient header, a compact
square `ARRP` mark, a cool gray page background, white cards with restrained
blue-gray borders, rounded corners and soft shadows, dark ink text, blue
navigation and action accents, gold for attention or privacy cautions, and
green for successful or private states.

Use the interface variables `--ink`, `--muted`, `--line`, `--soft`, `--blue`,
`--blue-soft`, `--gold`, `--gold-soft`, `--green`, and `--shadow`, with the
system sans-serif stack used by the Project Console. Tool pages identify this
profile with `data-interface-theme="arrp-tool"` on the document body.

The tool profile above does not govern the public GitHub Pages policy-document
theme, canonical Markdown presentation, or print editions. The narrow
topic-guide configuration below records only the classes and behavior adopted
for that content type; it does not alter the site's general theme.

## Public topic-guide presentation

ARRP topic guides use the title class `.arrp-topic-guide-title`. Their routing
tables use the shared wrapper `.arrp-topic-table`, with
`.arrp-topic-table--map` for the applicable-proposals table and
`.arrp-topic-table--related` for the related-ideas table.

The screen layout uses unshaded headers and fixed wrapping columns. The print
layout repeats table headers, prevents individual rows from splitting, and
keeps a short related-ideas table with its heading when space permits.
Individual topic pages must use these configured classes rather than
reproducing the presentation rules inline.
