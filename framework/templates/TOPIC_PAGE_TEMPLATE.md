---
title: "Topic Page Template"
print_levels:
  - full-technical
---

# Topic Page Template

Use this structure for every public topic guide. Replace bracketed instructions, omit the optional **Related Ideas Not Included** and **Sources and Updates** sections when they do not apply, and preserve the title class and table wrappers so screen and print styling remain consistent. Each Applicable Proposals row must contain exactly one proposal identifier or `Pending` for an unresolved concern that has no stable record; split a broad concern into proposal-specific rows rather than listing several identifiers together.

```markdown
---
title: "[Public Topic Title]"
page_type: topic-guide
status: maintained
purpose: "Help readers find the ARRP proposals addressing [public subject]."
last_reviewed: "YYYY-MM-DD"
print_levels:
  - public-proposal
  - full-technical
---

# [Public Topic Title] {.arrp-topic-guide-title}

## Overview

[Normally 100–200 words explaining the recognizable public subject, the institutional questions ARRP addresses, and any necessary boundary with a narrower topic guide.]

## Applicable Proposals

<div class="arrp-topic-table arrp-topic-table--map" markdown>

| Public concern | Proposal | How ARRP addresses it |
| --- | --- | --- |
| [Short familiar public descriptor] | [ISSUE-ID](../../areas/AREA/issues/ISSUE-ID.md) | [One sentence explaining the proposal's institutional function.] |
| [Unresolved public concern] | Pending | [One sentence identifying the institutional question still requiring project review.] |

</div>

<!-- Omit this section when no final adverse decision is materially related. -->
## Related Ideas Not Included

<div class="arrp-topic-table arrp-topic-table--related" markdown>

| Idea | Record | Why it is not included |
| --- | --- | --- |
| [Concise idea] | [HOR-###](https://github.com/Thorncrag/ARRP/issues/NUMBER) | [One sentence stating the final rejection, retirement, or outside-scope reason.] |

</div>

## What ARRP Does and Does Not Address

[Briefly distinguish the institutional defects addressed from ordinary policy or political disagreement.]

<!-- Add Sources and Updates only when the subject changes over time or relies on a defined source hierarchy. -->
```
