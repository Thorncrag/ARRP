---
title: "Public Topic Guide Standard"
status: active
authority_scope: "Admission, ownership, structure, language, routing tables, disposition references, and nonauthoritative limits for public topic guides."
load_when: "Creating, converting, materially revising, rerouting, or reviewing a public topic page or a research crosswalk proposed for public topic treatment."
dependencies:
  - "../../FRAMEWORK.md"
  - "navigation-and-indexes.md"
  - "neutrality-and-language.md"
  - "../publication/print-assembly.md"
print_status: excluded
print_exclusion_reason: "Online technical framework and methodology."
---

# Public Topic Guide Standard

## Authority and Dependencies

This file is the authoritative reusable standard for public topic guides. Topic
guides are navigation and synthesis surfaces, not substantive proposal
authorities. Apply
[`navigation-and-indexes.md`](navigation-and-indexes.md) to primary ownership
and routing changes, [`neutrality-and-language.md`](neutrality-and-language.md)
to public prose, and the reusable
[`print-assembly.md`](../publication/print-assembly.md) standard to publication
disposition. Exact repository paths, public headings, table labels, unresolved
markers, identifiers, presentation classes, and edition membership belong in
the project configuration.

## Load When

Load this file when creating, converting, materially revising, rerouting, or
reviewing a public topic page; deciding whether a research crosswalk warrants
public topic treatment; or changing a topic table, included proposal route, or
final non-inclusion reference.

## Topic Page Standard

A topic page exists to help a reader who knows a public subject but does not
yet know the project's taxonomy. It is a selective navigation and synthesis
layer, not an independent research memorandum, issue page, proposal,
cross-project status report, or source of authoritative disposition decisions.
Admit one only when the subject is commonly recognizable, spans more than one
project record or collection, materially benefits from synthesis, and has
enough verified source support to describe the subject accurately.

Apply this ownership test during drafting and review: **if a passage could be moved verbatim into an issue page as diagnosis, manifestations, legal analysis, remedy analysis, proposed legislation, implementation design, or proposal development work, it does not belong on the topic page.** Move or preserve that material in the record that owns it; do not delete a unique supported proposition merely to shorten the guide.

Each topic page should ordinarily contain, in this order, using the
project-configured reader-facing headings and table labels:

1. an overview — normally 100–200 words identifying the public subject and
   explaining why readers may encounter it across the project;
2. an applicable-records section — one compact three-column routing table with
   a short familiar public descriptor, one concise record identifier, and one
   explanatory sentence per row;
3. a related-final-dispositions section, only when the project has finally
   rejected, retired, or held outside scope a topic-related candidate, using a
   matching three-column table for the idea, record, and concise reason; and
4. a scope-boundary section — a short statement distinguishing in-scope
   institutional defects from ordinary policy or political disagreement.

A short **Sources and Updates** note may follow when the subject changes over time or the guide relies on a defined source hierarchy. Topic pages should use nearby citations for material factual claims and the ordinary source-inventory rules, but detailed source methodology, backup-file administration, audit procedure, and reusable mapping rules belong in the methodology or source inventory rather than on the public guide.

Use plain language because these pages are intended for readers who do not
already know the project's taxonomy or internal terminology. Public headings
should describe what the reader will find. Avoid unexplained phrases such as
`authoritative route`, `record owner`, `treatment`, `proposal vehicle`, or
`crosswalk`; identify the proposal, analysis, legislation, or other destination
directly. Stable proposal identifiers remain appropriate because they give
readers precise links and match the rest of the project.

In the routing table, use concise stable issue identifiers rather than
repeating full issue titles. Each row must identify exactly one proposal or
display the project-configured unresolved marker when the concern has no stable
proposal or candidate identifier. When one public event or broad concern
implicates several proposals, use separate rows and phrase each concern
narrowly enough to identify the institutional question owned by that proposal.
Preserve an unresolved topical concern rather than dropping it merely because
routing or admission has not yet been decided; replace the marker when a
stable record is assigned. The marker is not a lifecycle status, promise to
develop a proposal, score, or priority. A finally rejected, retired, or
outside-scope idea belongs in the related-final-dispositions or scope-boundary
section, not in an unresolved row. Do not place a null value or a list of
identifiers in the proposal column. Link a developed identifier directly to
its standalone issue page. When an applicable issue has a stable identifier
but no standalone page, display that identifier as plain text: do not create a
knowingly broken link or route the reader through a collection page as a
substitute. Collection pages do not appear in the routing table. When a topic
genuinely spans much of a collection and a broad overview would materially
help, an optional collection link may instead appear in overview prose; label
it with the collection's descriptive title rather than only its internal
designation. Direct issue routing remains the default.

Treat the issue page—not each linked bill, amendment, rule, model act, or implementation vehicle—as the applicable proposal when one issue owns the public concern. Do not create additional concern rows merely to display multiple vehicles or make the topic appear to have broader coverage. Readers should ordinarily reach those vehicles through the issue page that explains their relationship and priority. Link legislation or another vehicle directly from a topic table only when the public subject is specifically the named vehicle or when independently intelligible competing proposals must be distinguished for navigation.

Describe the first column as a publicly recognizable concern rather than an
attribute of an individual reader. Express each concern as the shortest
familiar, neutral phrase that remains clear—prefer a common noun phrase or
descriptor over a sentence, explanation, or embedded list of examples. Use
plain reader-facing headings and labels adopted by the project; do not use
`authoritative route`, `record owner`, `function`, or similar project-internal
phrasing. The linked issue and proposal records remain authoritative; the
topic page only identifies which ones apply.

Topic categories are not mutually exclusive, but their reader routes should be
deliberate rather than duplicative. The topic-index card and the table should
lead with the subject's distinctive concerns. When a narrower topic guide
already supplies the natural public route, a broader guide should ordinarily
link to it briefly in the overview or in a tailored table explanation instead
of repeating the narrower guide's full mapping. Event- and document-centered
guides may intentionally cross several subject guides when the recognizable
event or source is itself the reader's entry point.

Use the reusable structure in
[`templates/topic-guide.md`](templates/topic-guide.md) and any wrapper and title
classes supplied by the project interface configuration. This allows the
publication surface to apply a topic-specific layout without changing other
reader pages. Do not reproduce presentation rules inline on individual topic
pages.

The related-final-dispositions section is a discovery aid, not a second
disposition log. Include only final adverse decisions materially connected to
the topic; reproduce neither the full candidate analysis nor every rejected
project idea. The designated disposition record and closed work item remain
authoritative. Do not list a deferred record separately: it remains an ordinary
live route unless and until finally adjudicated. Do not list merged or
integrated records separately: route the reader to the current authoritative
home through the applicable-records section. If no topic-related rejection,
retirement, or outside-scope decision has been formally recorded, omit the
section rather than announcing that none exists. General scope boundaries may
be stated separately but must not be presented as individualized rejection
decisions.

Topic pages must not carry quality or adoption scores, audit histories,
lifecycle fields, budget analyses, proposal text, independent remedy
recommendations, priority rankings, gap lists, next-action lists, or claims
that the topic page itself adopts or rejects a proposal. When implementation
status is useful to explain routing, use only sourced concise terms such as
`proposed`, `attempted`, `enacted`, `enjoined`, `abandoned`, `superseded`, or
`uncertain`; do not turn the guide into an implementation tracker. Keep
headings, tables, and prose as short as accurate routing permits.

Each subject has one canonical topic page. Describe `topic guide`, `crosswalk`,
or similar internal functions in metadata or technical project records, not in
the visible public title or headings. The project-configured applicable-records
heading retains the navigational function of a crosswalk in language intended
for lay readers. When an existing project-authored crosswalk is selected for
topic treatment, move and convert it into the configured topic directory
rather than retaining a parallel research copy. Issue pages remain
authoritative for diagnosis and remedies; proposal pages for proposed text;
disposition records and closed work items for rejection decisions; the source
catalog for citation administration; and the work tracker for live status.

A retained research crosswalk does not automatically warrant its own public
topic guide. When its subject fits an existing public topic, link the crosswalk
from that topic page's source/update section and leave the detailed matrix in
the configured research location. When a crosswalk instead concerns a familiar
public subject that independently satisfies the topic-page admission standard,
create or convert one canonical topic guide and link the crosswalk there.
Select one principal topic home; add a secondary topic link only when it
materially improves reader discovery. When research records are excluded from
the public artifact, link through the stable repository URL configured by the
project rather than a local Markdown link the publication process would
demote.
