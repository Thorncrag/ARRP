---
title: "Public Interaction Service"
print_status: excluded
print_exclusion_reason: "Internal workflow or tool documentation."
---

# Public Interaction Service

This folder contains ARRP's separately deployed public interaction service, available at [arrp-public-intake.vercel.app](https://arrp-public-intake.vercel.app/). It is deliberately separate from the read-only [`ARRP Project Console`](../research/horizon-review-console/) console. Both application-like surfaces use the [project-operated interface visual standard](../framework/FRAMEWORK.md#project-operated-interface-visual-standard); that standard does not replace the main GitHub Pages or print themes.

The form presents two separate routes. **Submit public input** accepts a short title, plain-language explanation, optional sources, and optional related ARRP page; its live route adds the submission as a comment in one canonical public GitHub Discussion. **Contact the author** sends a private message to the configured author mailbox and creates no public post, GitHub record, candidate, or project record. The email field is optional and empty by default. Entering an address authorizes a private reply or follow-up about that submission; leaving it blank means the contributor does not want to be contacted. A private author message with no address has no contributor `Reply-To` header or address, and its subject and body prominently prohibit a contributor reply. Local preview mode sends neither route.

The route is deterministic and does not use an agent: an explicitly entered related ARRP page takes precedence; otherwise the page context passed by the referring ARRP page is used. A recognized proposal routes to its proposal Discussion, a recognized area routes to its area Discussion, and unrecognized material goes to the general-input Discussion. The service creates the canonical Discussion only when its route has none, then adds the public submission as a comment. Its stable title and hidden route marker prevent title-based duplicate matching. The live confirmation panel links directly to the contributor's comment and tells the contributor to keep and watch that post, explains that a signed-in GitHub user can subscribe for GitHub notifications, and advises a contributor without an account to bookmark the direct link. When the private follow-up service is configured, entering an optional address authorizes ARRP to use it for private follow-up. Email addresses are never included in the GitHub Discussion, and the service does not send a receipt email to the contributor. In local preview mode, the response is visibly labeled as a preview and links only to the ARRP Discussions index; it never claims that a post was created.

Page-specific feedback and review links can pass `proposal`, `page_title`, and `page` query parameters. The service visibly confirms that context and prepopulates the related-page field.

After the participation lookup is regenerated, run `python3 scripts/build_participation_route_index.py` from the repository root before deployment. It derives the small server-side route index from `participate/intake-data.js`, so a newly admitted proposal, proposed candidate, area route, title, canonical path, or GitHub issue link remains routable without trusting arbitrary user-entered identifiers.

## Vercel Service

This directory is a self-contained Vercel project. Deploy this directory—not the repository root—as the Vercel project root. Its static files serve the form and its two server-side functions implement:

- `api/config` — exposes only the public runtime configuration needed by the browser;
- `api/submit` — validates the request, checks the bot token and a narrow server-side privacy preflight, resolves a deterministic proposal/area/general route, finds or creates the corresponding GitHub Discussion, adds the submission as a comment through a narrowly scoped GitHub App, and, when an optional address is entered, sends it only to the private ARRP follow-up mailbox.

The service is deliberately **preview-only** unless `ARRP_INTAKE_MODE=live`. In preview mode, `api/submit` rejects every request and the browser displays only its local confirmation demonstration. Do not set live mode until every deployment gate below has been completed.

### Required live-service configuration

Create a GitHub App rather than using a personal access token. Install it only on `Thorncrag/ARRP` and grant only the repository **Discussions: Read and write** permission needed to create the intake posts. Store the App ID, installation ID, private key, repository node ID, and intake-category node ID in Vercel's encrypted environment-variable settings. The client never receives any of those values.

Cloudflare Turnstile is mandatory in live mode. Store its secret key only in Vercel; the site key returned by `api/config` is intentionally public. The browser uses the `arrp_public_intake` action and the endpoints verify both that action and the configured production hostname after every successful token check. Configure Vercel Firewall/WAF rate limiting before live activation, with conservative per-IP rules for both `POST /api/submit` and `POST /api/contact`. Turnstile, a honeypot, and a local burst limiter reduce automated traffic; the WAF rule supplies the required distributed protection against repeated valid-token submissions and excessive function use.

Private author contact requires a transactional provider supported by the endpoint (currently Resend), with `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, and `ARRP_CONTACT_EMAIL` set only in Vercel's encrypted environment. The endpoint sends the message only to that private mailbox, uses an optional contributor address as the email reply target, and never creates a public post. `ARRP_INTAKE_REVIEW_EMAIL` remains a transitional fallback for the already-configured mailbox and optional public-input follow-up notices. The service never sends an email to a contributor.

Copy [`.env.example`](.env.example) into Vercel's environment-variable interface. Set `ARRP_ALLOWED_ORIGINS` to the exact origins permitted to call the service, including the Vercel deployment origin and any separately approved future origin. Set `ARRP_INTAKE_MODE=live` last.

`intake-runtime.js` contains no secret. Leave its endpoint blank when Vercel serves this folder itself. If an approved future GitHub Pages page uses this backend from a separate origin, set `window.ARRP_INTAKE_ENDPOINT` to the Vercel deployment origin and include that Pages origin in `ARRP_ALLOWED_ORIGINS`.

### Emergency pause controls

For an immediate, reversible service pause, change the relevant **Production** environment variable in Vercel and redeploy the current production deployment:

- Set `ARRP_CONTACT_MODE=disabled` to suspend only private author contact. Public input remains available.
- Set `ARRP_INTAKE_MODE=paused` to suspend both public input and private author contact. The form and endpoints return a neutral temporary-unavailable message instead of simulating a submission.

Restore service by setting the affected variable back to `live` and redeploying. Do not use credential deletion as the ordinary pause mechanism.

The formal candidate-admission decision remains a Codex workflow step. The intake service preserves and acknowledges public submissions; it does not classify them as preliminary candidates, create `HOR-###` records, modify issues, or trigger an agent.

## Privacy preflight and intake review

Before it creates a public Discussion, the service rejects common direct disclosures in every public value, including the page-context values passed by a referring page: email addresses, telephone numbers, Social Security-number patterns, payment-card numbers with a valid checksum, and common credentials or private-key headers. It returns only a general correction message; it does not place matched text in a GitHub post, an intake log, or an endpoint log. The separately authorized optional email field is not part of that public-content screen and is never included in the Discussion. Public submissions are rendered as literal text, and the post contains only the server-selected ARRP route rather than raw browser-supplied context.

This is a due-diligence privacy screen, not a guarantee that every address, personal fact, sensitive narrative, or inappropriate statement can be recognized mechanically. The form’s public-warning language remains essential. A semantic moderation service will be added only after its retention settings, error handling, and review policy have been expressly approved.

[`../framework/INTAKE_AGENT_PROCESS.md`](../framework/INTAKE_AGENT_PROCESS.md) governs manual Codex review of a selected public-intake comment. No GitHub Action or separately billed external-model service currently assesses submissions. A review may recommend a route, but it has no authority to edit ARRP records, create a candidate, alter a project field, comment publicly, or send mail. The process specifies a separate action ledger for any later, expressly approved automation; the ARRP Project Console remains limited to preliminary and proposed candidates.

See [`SECURITY.md`](SECURITY.md) for the live-service controls and account-side verification checklist.
