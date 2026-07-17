# Public Input Prototype

This folder contains the standalone prototype for ARRP's eventual public interaction entry point. It is deliberately separate from the read-only [`Candidate Issues and Source Intake`](../research/horizon-review-console/) dashboard.

The prototype accepts a short title, a plain-language explanation, optional sources, and an optional related ARRP page. Its preview does not create a GitHub Discussion, send email, or modify any project record.

The intended live submission response contains the direct link to the newly created public GitHub Discussion. It tells the contributor to keep and watch that post, explains that a signed-in GitHub user can subscribe for GitHub notifications, and advises a contributor without an account to bookmark the link. When the private follow-up service is configured, a contributor may also provide an address and expressly authorize ARRP to use it for private follow-up. Email addresses are never included in the GitHub Discussion, and the service does not send a receipt to the contributor. In local preview mode, the response is visibly labeled as a preview and links only to the ARRP Discussions index; it never claims that a post was created.

Page-specific feedback and review links can pass `proposal`, `page_title`, and `page` query parameters. The prototype visibly confirms that context and prepopulates the related-page field.

## Vercel Prototype

This directory is a self-contained Vercel project. Deploy this directory—not the repository root—as the Vercel project root. Its static files serve the form and its two server-side functions implement:

- `api/config` — exposes only the public runtime configuration needed by the browser;
- `api/submit` — validates the request, checks the bot token and a narrow server-side privacy preflight, creates a GitHub Discussion through a narrowly scoped GitHub App, and, when an address is authorized, sends it only to the private ARRP follow-up mailbox.

The service is deliberately **preview-only** unless `ARRP_INTAKE_MODE=live`. In preview mode, `api/submit` rejects every request and the browser displays only its local receipt demonstration. Do not set live mode until every deployment gate below has been completed.

### Required live-service configuration

Create a GitHub App rather than using a personal access token. Install it only on `Thorncrag/ARRP` and grant only the repository **Discussions: Read and write** permission needed to create the intake posts. Store the App ID, installation ID, private key, repository node ID, and intake-category node ID in Vercel's encrypted environment-variable settings. The client never receives any of those values.

Cloudflare Turnstile is mandatory in live mode. Store its secret key only in Vercel; the site key returned by `api/config` is intentionally public. Configure Vercel Firewall/WAF rate limiting before live activation, with a conservative per-IP rule for `POST /api/submit`. Turnstile and a honeypot reduce automated traffic; the rate rule protects against repeated valid-token submissions and excessive function use.

Private follow-up is optional. If enabled, configure a transactional provider supported by the endpoint (currently Resend) with `RESEND_API_KEY` and `RESEND_FROM_EMAIL`. Set `ARRP_INTAKE_REVIEW_EMAIL` only to a private project mailbox; it receives the contributor's address and public-discussion link only when the contributor expressly authorized possible follow-up. The endpoint creates the public Discussion first. A mail-delivery failure does not delete the Discussion or expose the contributor's address; the browser still receives the direct public link. The service never sends an email to the contributor.

Copy [`.env.example`](.env.example) into Vercel's environment-variable interface. Set `ARRP_ALLOWED_ORIGINS` to the exact origins permitted to call the service, including the Vercel deployment origin and, when the form is later included in GitHub Pages, `https://thorncrag.github.io`. Set `ARRP_INTAKE_MODE=live` last.

`intake-runtime.js` contains no secret. Leave its endpoint blank when Vercel serves this folder itself. If an approved future GitHub Pages page uses this backend from a separate origin, set `window.ARRP_INTAKE_ENDPOINT` to the Vercel deployment origin and include that Pages origin in `ARRP_ALLOWED_ORIGINS`.

The formal candidate-admission decision remains a Codex workflow step. The intake service preserves and acknowledges public submissions; it does not classify them as preliminary candidates, create `HOR-###` records, modify issues, or trigger an agent.

## Privacy preflight and intake-agent prototype

Before it creates a public Discussion, the service rejects common direct disclosures in the public fields: email addresses, telephone numbers, Social Security-number patterns, payment-card numbers with a valid checksum, and common credentials or private-key headers. It returns only a general correction message; it does not place matched text in a GitHub post, an intake log, or an endpoint log. The separately authorized optional email field is not part of that public-content screen and is never included in the Discussion.

This is a due-diligence privacy screen, not a guarantee that every address, personal fact, sensitive narrative, or inappropriate statement can be recognized mechanically. The form’s public-warning language remains essential. A semantic moderation service will be added only after its retention settings, error handling, and review policy have been expressly approved.

[`../framework/INTAKE_AGENT_PROCESS.md`](../framework/INTAKE_AGENT_PROCESS.md) defines the next-stage, report-only intake-agent prototype. Its manual [`../.github/workflows/intake-agent-report.yml`](../.github/workflows/intake-agent-report.yml) workflow can assess one public Discussion, use structured output to produce a short routing recommendation, and retain the report as a 14-day maintainer workflow artifact. It has no authority in this phase to edit ARRP records, create a candidate, alter a project field, comment publicly, or send mail. It remains inactive until the maintainer sets the `OPENAI_INTAKE_API_KEY` GitHub Actions secret and `OPENAI_INTAKE_MODEL` GitHub Actions variable; it is not triggered by a public submission. The future action ledger and console view are also specified there; they will be added after the current console redesign is committed so that this prototype does not overwrite in-progress intake-console work.
