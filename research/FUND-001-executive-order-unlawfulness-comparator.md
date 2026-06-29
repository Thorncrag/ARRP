---
title: "FUND-001 Executive-Order Unlawfulness Comparator"
status: source-development
associated_issue: FUND-001
print_levels:
  - full-technical
---

# FUND-001 Executive-Order Unlawfulness Comparator

This comparator supports [FUND-001](../areas/FUND/issues/FUND-001.md) by separating two questions:

1. how many executive orders were issued during a presidency or term; and
2. how many executive orders or covered implementation actions were later found unlawful by a court or the Comptroller General.

The first question supplies a neutral denominator. The second supplies a possible abuse-risk numerator. Neither should be used alone as proof of executive-order abuse.

## Denominator

The denominator source is the Federal Register's executive-order disposition tables. See [Executive Orders](https://www.federalregister.gov/presidential-documents/executive-orders), Office of the Federal Register.

T2 should verify the count date, publication lag, and whether comparison should use full administrations, individual terms, calendar years, or orders per day in office.

## Numerator Inclusion Rule

An executive order or covered executive directive should be included in the numerator only if source review identifies one of the following:

1. a final judgment holding the executive order, directive, or covered implementation action unlawful;
2. a three-judge-court decision granting relief after a merits finding that the order or implementation action is likely unlawful;
3. a Comptroller General decision finding that the order or implementation action violated the Impoundment Control Act, an appropriations Act, or another budget-authority statute;
4. a final judgment compelling release, obligation, or expenditure of budget authority withheld, delayed, conditioned, or redirected under the order or implementation action.

Entries should distinguish:

- the executive order itself;
- agency rules, memoranda, grant conditions, apportionments, or implementation actions taken under the order;
- preliminary injunctions later vacated or mooted;
- orders superseded before final judgment;
- findings based on statutory authority, constitutional authority, APA defects, procedural defects, or appropriations/impoundment defects.

## Comparator Fields

When populated, the comparator should use a case-level CSV or table with these fields:

| Field | Purpose |
| --- | --- |
| `record_id` | Stable comparator row ID, such as `FUND-001-COMP-001`. |
| `president` | President who issued the order or directive. |
| `term` | Term or administration period. |
| `directive_type` | Executive order, presidential memorandum, OMB directive, agency implementation action, or other directive. |
| `directive_number_or_identifier` | EO number or other public identifier. |
| `directive_title` | Public title or short description. |
| `directive_date` | Date issued. |
| `implementation_action` | Agency action, apportionment, grant condition, rule, memorandum, or nonspending action if the case concerns implementation rather than the EO on its face. |
| `legal_finding_source` | Court, Comptroller General, or other official source. |
| `case_or_decision_citation` | Case caption, docket, GAO file number, or citation. |
| `finding_date` | Date of finding. |
| `finding_finality` | Final judgment, preliminary relief, GAO decision, vacated, mooted, superseded, or unresolved. |
| `basis_of_unlawfulness` | Statutory conflict, constitutional conflict, APA defect, appropriations/impoundment violation, procedural defect, or other basis. |
| `appropriations_relevance` | Whether the case involved spending, withholding, delay, deferral, apportionment, reprogramming, grant conditions, or program execution. |
| `fund_001_trigger_credit` | Yes, no, partial, or unresolved under the proposed FUND-001 trigger. |
| `notes` | Caveats, source limits, and relationship to FUND-001. |

## Initial Status

No complete official comparator has been identified. The project should construct the numerator during T2 source development from court decisions, Comptroller General decisions, Federal Register records, OMB materials, and agency implementation records.

Candidate entries should not be treated as trigger-credit entries until the legal finding, finality posture, and implementation relationship are verified.

## Same-Administration Repeal / Revocation Analog

A more feasible public-data analog may be to tabulate executive orders that were repealed, revoked, superseded, or materially amended during the same presidential administration that issued them.

This analog should be treated cautiously. Same-administration repeal does not prove illegality or abuse. Orders may be revoked because policy changed, a later order consolidated prior directives, implementation became unnecessary, Congress acted, litigation pressure mounted, or the administration chose a different legal vehicle. Still, the measure is useful because it is more likely to be tabulatable from public Federal Register disposition data than judicial unlawfulness outcomes across administrations.

Potential fields:

| Field | Purpose |
| --- | --- |
| `eo_number` | Executive order number. |
| `issuing_president` | President who issued the order. |
| `issue_date` | Date signed or published. |
| `revoking_or_amending_document` | Later EO, proclamation, memorandum, or notice that revokes, supersedes, or amends the order. |
| `revocation_date` | Date of repeal, revocation, supersession, or material amendment. |
| `same_administration` | Yes/no field identifying whether revocation occurred during the same administration or term. |
| `disposition_type` | Revoked, superseded, amended, partially revoked, terminated, expired, or unclear. |
| `litigation_or_legal_context` | Whether public sources connect the disposition to litigation, legal vulnerability, statutory conflict, or court/GAO findings. |
| `fund_001_value` | Denominator analog, litigation-pressure proxy, or possible source-development lead. |

T2 should test whether the Federal Register bulk CSV/JSON files include disposition metadata in a machine-readable form. If not, the same-administration analog may require text parsing of disposition notes or individual EO pages.

### Trump Second-Term Quick Scan

On 2026-06-29, a quick Federal Register API scan identified 268 Trump second-term executive-order records published on or after January 20, 2025. Searching those records for revocation, rescission, repeal, and supersession terms produced 83 unique term-hit documents. A follow-up text scan of those 83 documents did not identify any referenced Trump second-term executive-order number, using `14147` and higher as the Trump 2.0 EO-number range.

Preliminary result:

| Administration / term | Total EO records checked | Revocation/rescission/supersession term-hit documents | Same-administration Trump 2.0 EO numbers found as revoked/rescinded/superseded | Status |
| --- | ---: | ---: | ---: | --- |
| Donald Trump, second term | 268 | 83 | 0 | Quick API/text scan; not publication-ready |

This result is preliminary. It does not prove no same-administration revocation exists, because Federal Register HTML text, disposition notes, corrections, non-EO presidential documents, and later updates may require additional parsing. It does suggest that most Trump 2.0 revocation/rescission language located in the quick scan concerns prior administrations' actions or non-EO directives rather than revocation of Trump 2.0 executive orders.

## Public-Source Check

Initial public-source review did not identify a complete all-presidents dataset matching the FUND-001 comparator. Existing public sources are useful inputs, but they appear to cover different scopes:

- **Manheim and Watts, Reviewing Presidential Orders.** Provides a scholarly framework for why presidential-order review is difficult to code: courts often review agency implementation rather than the presidential order itself, the APA does not apply directly to the President, and direct challenges to presidential orders increased sharply in the Trump era. This supports separate comparator fields for facial EO invalidation, implementation invalidation, and review posture.
- **American Presidency Project.** Provides a free, searchable archive of presidential documents and executive orders. It is useful as a parallel denominator/text source alongside the Federal Register, especially for order text, dates, titles, and presidential-document searching. It does not appear to provide a curated legal-outcome field.
- **Federal Judicial Center.** The FJC site was verified as the federal judiciary's research and education agency and includes history, research, federal-court case data, and judicial-branch resources. A specific public archive titled "Judicial Review of Executive Orders" was not verified in this pass. Treat FJC as a promising institutional source lead, not as a confirmed EO-unlawfulness comparator.
- **HeinOnline.** Verified as a subscription legal-research platform with law journals, U.S. federal content, case law, historical material, and image-based PDFs. It is likely useful for T2/T3 literature review and historical doctrine, but it is not a public, ready-made comparator and may require institutional access.
- **CRS R48467, Nationwide Injunctions Under the First Trump Administration and the Biden Administration.** Verified as a Congress.gov CRS product. It is not EO-specific, but it is the strongest public institutional comparator found so far for cross-administration judicial blocking of federal policy. CRS identifies 86 nationwide injunction cases under the first Trump Administration and 28 under the Biden Administration in its appendix analysis, while warning that its appendix should not be treated as a definitive list of every nationwide injunction. The report's front-page discussion also cites prior Department of Justice and Harvard Law Review counts across the George W. Bush, Obama, Trump, and Biden administrations, making it useful for a public-facing comparator column even though it does not answer the narrower EO-unlawfulness question.
- **Ballotpedia Biden multistate-lawsuit page.** Verified as a public routing source for multistate lawsuits against the federal government during the Biden Administration. It is useful for identifying Biden-era state-plaintiff litigation and possible comparator leads, but it is not EO-specific and should not be treated as a final legal-outcome dataset.
- **American Bar Association materials.** ABA materials and litigation may be useful for doctrine and current examples involving executive-order challenges. No general ABA comparator for EO legality outcomes was verified in this pass.
- **Just Security Litigation Tracker.** Tracks legal challenges to Trump administration executive actions, links many dockets, and provides detailed status categories. It is useful for Trump second-term litigation but is not an all-presidents executive-order comparator and groups cases by administration actions rather than by Federal Register executive-order denominator.
- **CourtListener / RECAP.** Provides free case-law and docket search, raw data, alerts, and APIs. It is likely the best public infrastructure for building the comparator, but it is not itself a curated list of executive orders later found unlawful.
- **Civil Rights Litigation Clearinghouse, Lawfare, Court Watch, Associated Press, and Washington Post trackers.** Public reporting and secondary tracking identify substantial Trump second-term litigation and litigation outcomes, but their scopes, status categories, docket-link depth, and grouping methods differ.
- **First Trump presidency lists.** Public lists exist for major lawsuits concerning first-term executive orders, proclamations, and memoranda, but they do not appear to provide a structured all-EO denominator-to-outcome dataset.
- **Clinton, George W. Bush, Obama, and Biden.** No public all-EO legal-outcome comparator was identified in this initial search.

T2 should therefore treat public trackers as source leads and construct a normalized project comparator rather than importing any one tracker wholesale.

## Candidate Tracker Check

The following user-identified trackers should be treated as follows:

| Source | Initial verification | Comparator value | Limits |
| --- | --- | --- | --- |
| New York Times tracker | Identified indirectly through public references, but not directly accessed in this pass because the site is not available to the browsing tool. | Potential secondary source lead. | Do not rely on without direct access, date check, and methodology review. |
| Just Security Litigation Tracker | Verified. The tracker is searchable, case-level, docket-linked, and includes methodology notes and status categories. | Strongest public tracker lead for Trump second-term pilot coding. | Trump-administration scope; groups by executive actions/cases rather than Federal Register EO denominator. |
| NAACP LDF tracker | No standalone "LDF-Trump Lawsuit Tracker" was verified in public search. LDF appears in individual civil-rights cases and tracker entries. | Useful for case leads involving civil rights, voting, DEI, and immigration if a tracker URL is later identified. | Do not cite as a tracker until directly verified. |
| Littler Executive Order Tracker | Verified. Tracks Trump executive orders, with special focus on labor and employment compliance after the first 100 days. | Useful for identifying labor/employment EO titles, implementation actions, and affected statutes. | Not a litigation-outcome tracker and not a general unlawfulness comparator. |
| Congressman Steve Cohen / House tracker | No public tracker was verified in this pass. | Possible lead if a live House page is later located. | Do not cite until directly verified. |
| Wikipedia legal-affairs summary | Verified. Summarizes second-Trump-presidency litigation and identifies multiple public trackers and case groupings. | Useful routing layer for source discovery. | Community-edited secondary source; verify all legal outcomes against primary dockets or tracker sources. |
| American Presidency Project | Verified. Free, searchable presidential-document archive hosted at UC Santa Barbara. | Strong denominator and order-text source. | Does not provide court-outcome coding. |
| Federal Judicial Center | FJC site verified; specific "Judicial Review of Executive Orders" archive not verified. | Potential historical/court-research lead. | Do not cite as a specific EO-review archive until located. |
| HeinOnline | Verified as subscription legal-research infrastructure. | Strong secondary literature and historical-source lead if available. | Not public and not a ready-made comparator. |
| CRS R48467 | Verified. Compares nationwide injunctions under Trump 1 and Biden by subject matter and issuing court geography, and cites prior DOJ and Harvard Law Review counts for multiple administrations. | Strong cross-administration public comparator for judicial blocking of federal policy; now integrated into the FUND-001 front-page table. | Not EO-specific; CRS warns its appendix is illustrative rather than definitive. |
| Ballotpedia Biden multistate lawsuits | Verified. Tracks multistate lawsuits against the federal government during the Biden Administration. | Useful Biden-era litigation routing layer and state-plaintiff comparator lead. | Not EO-specific; verify outcomes against primary dockets and opinions. |

T2 should prioritize Just Security and CourtListener for pilot coding, use Littler for labor/employment EO identification, and treat NYT, LDF, Cohen/House, and Wikipedia as routing sources unless directly verified and reconciled with primary docket materials.

CRS R48467 should be treated as the best currently identified public cross-administration comparator, but for nationwide injunctions rather than EO unlawfulness. The front-page issue table therefore compares Federal Register EO counts against CRS appendix nationwide-injunction counts where available, and uses the higher CRS-reported DOJ-cited count for George W. Bush and Obama with a notation that CRS did not provide appendix counts for those administrations. Harvard Law Review-cited counts remain source-note and T2 verification leads. The Trump second-term AP figure is not a nationwide-injunction count; it is displayed as a caveated temporary proxy in the "Unlawful" column because it reports court blocks of executive actions rather than final EO-specific unlawfulness findings.

## CRS Source Leads

The CRS report's source trail is relevant, but it does not appear to solve the EO-specific unlawfulness numerator. The source trail instead supports a second-best comparator: nationwide-injunction frequency by administration.

| CRS source lead | Data relevance | FUND-001 treatment |
| --- | --- | --- |
| CRS appendix analysis | Most reliable identified public count for the report's covered administrations: 86 nationwide-injunction cases under the first Trump Administration and 28 under the Biden Administration. CRS also codes subject matter and issuing-court geography. | Use as the strongest public cross-administration comparator currently identified, with the caveat that it is nationwide-injunction data rather than EO-specific final unlawfulness data. |
| Department of Justice nationwide-injunction counts cited by CRS | CRS reports DOJ historical counts for George W. Bush, Obama, and the first Trump Administration. These are useful because they extend the comparison beyond the CRS appendix period. | Use as a CRS-cited comparator lead, but label as DOJ-cited counts because DOJ has an institutional litigation position against nationwide injunctions. |
| Harvard Law Review nationwide-injunction counts cited by CRS | CRS reports Harvard Law Review counts for George W. Bush, Obama, the first Trump Administration, and the first three years of the Biden Administration. These are useful because they provide an academic comparator series across multiple administrations. | Use as a strong T2 verification target. If the underlying Harvard table or methodology is accessible, it may become the preferred non-governmental comparator series for the front-page table. |
| CRS case list and subject-matter coding | Potentially useful for building a pilot dataset of federal-policy blocks by administration and subject matter. | Treat as a bridge dataset: it can help classify litigation pressure, but each case would still need separate coding for EO number, implementation action, finality, and appropriations relevance. |

Research assessment: these CRS source leads are relevant enough to remain integrated in the front-page table, but they should be kept in a separate "nationwide injunction" comparator column. They do not replace the stricter FUND-001 trigger question: whether an executive order or covered implementation action was later found unlawful by a final court judgment, qualifying three-judge-court determination, or Comptroller General finding.

## Narrow SCOTUS Pilot: Trump First Term

Pilot question: identify final Supreme Court merits opinions from the first Trump administration holding an executive order itself unlawful.

Initial result: no qualifying final Supreme Court merits opinion was identified in this narrow first pass.

The principal near-miss is the travel-ban litigation. The Supreme Court's final merits decision in *Trump v. Hawaii* upheld Presidential Proclamation 9645 against statutory and Establishment Clause challenges. The opinion describes earlier executive orders as part of the review history, but the final Supreme Court outcome was not a facial invalidation of an executive order. Predecessor travel-ban executive-order litigation and lower-court injunctions therefore should not be counted as final SCOTUS EO invalidations in this narrow comparator unless a later T2 review identifies a separate final Supreme Court merits opinion.

Coding implication:

| Administration / term | Narrow metric | Initial pilot result | Notes |
| --- | --- | ---: | --- |
| Trump first term | Final SCOTUS merits opinions holding an executive order itself unlawful | 0 | Preliminary pilot result; does not include lower-court injunctions, emergency orders, implementation-only cases, mooted cases, or Supreme Court decisions upholding presidential directives. |

T2 should verify this pilot with Supreme Court docket searches for EO number variants, order titles, Federal Register citations, and known litigation names before treating the zero as final.

## Narrow D.C. Circuit Pilot: Trump First Term

Pilot question: identify final U.S. Court of Appeals for the District of Columbia Circuit opinions from the first Trump administration holding an executive order itself unlawful.

Initial result: no qualifying final D.C. Circuit opinion was identified in this narrow first pass.

The principal D.C. Circuit near-miss is the federal workforce and labor-relations executive-order litigation involving the 2018 orders directed at federal unions and civil-service management. A D.D.C. ruling blocked or invalidated major portions of the orders, but the D.C. Circuit reversed on jurisdictional and Civil Service Reform Act channeling grounds rather than issuing a final appellate holding that the executive orders were unlawful. This therefore should not count as a D.C. Circuit final invalidation under the narrow comparator, though it is a useful implementation and remedial-channeling example.

Other first-term Trump EO litigation located in this pass either proceeded outside the D.C. Circuit, involved lower-court or preliminary relief, involved presidential memoranda/proclamations rather than executive orders, was mooted or superseded, or did not produce a final D.C. Circuit merits holding facially invalidating an EO.

Coding implication:

| Administration / term | Narrow metric | Initial pilot result | Notes |
| --- | --- | ---: | --- |
| Trump first term | Final D.C. Circuit opinions holding an executive order itself unlawful | 0 | Preliminary pilot result; does not include district-court orders, preliminary injunctions, implementation-only cases, jurisdictional reversals, mooted cases, or cases in other circuits. |

T2 should verify this pilot with CourtListener, official D.C. Circuit opinions, Federal Register EO-number searches, and known case names before treating the zero as final.

## Narrow D.D.C. Pilot: Trump First Term

Pilot question: identify final U.S. District Court for the District of Columbia opinions from the first Trump administration holding an executive order itself unlawful.

Initial result: at least one qualifying district-court merits invalidation was identified, but it was later reversed on appeal and therefore should not be treated as a durable final invalidation.

The principal qualifying district-court example is the 2018 federal workforce and labor-relations litigation challenging Executive Orders 13836, 13837, and 13839. The D.D.C. ruling blocked or invalidated major portions of the orders affecting federal union official time, collective bargaining, and civil-service management. The D.C. Circuit later reversed on jurisdictional and Civil Service Reform Act channeling grounds. For comparator purposes, this should be coded as:

- `district_court_outcome`: EO provisions held unlawful / relief granted;
- `appellate_status`: reversed on jurisdictional or review-channeling grounds;
- `durable_trigger_credit`: no, unless the FUND-001 trigger is later designed to count district judgments regardless of later appellate reversal;
- `methodology_note`: useful example showing why district outcome, appellate outcome, finality, and trigger-credit fields must remain separate.

Coding implication:

| Administration / term | Narrow metric | Initial pilot result | Notes |
| --- | --- | ---: | --- |
| Trump first term | Final D.D.C. opinions holding an executive order itself unlawful before appellate review | 1 identified | Preliminary pilot result; principal example is federal workforce/union EO litigation, later reversed by the D.C. Circuit on jurisdictional/CSRA-channeling grounds. |
| Trump first term | Durable D.D.C. EO invalidations surviving appellate review | 0 identified | Preliminary pilot result; requires primary-source verification. |

T2 should verify the district-court opinion, D.C. Circuit reversal, docket posture, and exact scope of relief before treating these counts as final.

## AP News Tracker Proxy: Trump Second Term

The Associated Press appears to maintain or use a tracker/tally of lawsuits against Trump administration executive actions. A directly reviewed AP article published May 1, 2025 reported that Trump executive actions had been partially or fully blocked by courts around 70 times, had not been impeded in nearly 50 cases, and that dozens of other cases were pending.

The project would prefer to include comparable judicial-review outcomes for other presidential administrations. Public-facing data reviewed so far, however, are not sufficiently complete, standardized, or accessible to feasibly track and tabulate comparable unlawfulness outcomes across all administrations with the sources currently available. Trump second-term litigation is therefore treated as the only currently usable public proxy, not as an analytically complete comparison to earlier presidencies.

This AP tally is useful as a Trump-second-term litigation proxy, but it does not yet satisfy the FUND-001 comparator because:

- it counts executive actions broadly, not only Federal Register executive orders;
- it appears to count court blocks, including preliminary relief, rather than only final merits judgments;
- it does not map each outcome to an EO number in the reviewed article;
- it does not provide the final appellate posture needed for trigger-credit coding;
- the number is time-sensitive and should be updated if the AP tracker or article updates.

Applied pilot coding for the issue-page table:

| Administration / term | AP proxy metric | AP proxy result | FUND-001 treatment |
| --- | --- | ---: | --- |
| Trump second term | Executive actions partially or fully blocked by courts as of May 1, 2025 | About 70 | Use only as a broad litigation-pressure proxy; EO-specific, finality, and trigger-credit fields remain TBD. |
| Trump second term | Executive actions not impeded by courts as of May 1, 2025 | Nearly 50 | Use only as broad context. |
| Trump second term | Pending executive-action cases as of May 1, 2025 | Dozens | Use only as broad context. |

T2 should try to locate the live AP tracker page or underlying AP dataset, reconcile it with Just Security and CourtListener, and then code only entries that can be mapped to EO number, directive title, implementation action, court, posture, and finality.
