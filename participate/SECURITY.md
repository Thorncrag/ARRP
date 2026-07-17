# Public Intake Security Controls

This checklist governs the live Vercel public-intake service. Repository code can enforce request shape, privacy screening, Turnstile validation, output safety, and a local burst limit. Provider-side controls are the only reliable protection across serverless instances and networks.

## Deployment protections

- **Firewall/WAF:** use provider-level rate limiting and bot protections where available. The service also applies application-level safeguards.
- **Turnstile:** restrict the site key to `arrp-public-intake.vercel.app` (and only explicitly approved future domains). Set `ARRP_TURNSTILE_HOSTNAME` and `ARRP_TURNSTILE_ACTION` to the same hostname and `arrp_public_intake` action used by the browser. The endpoints reject a successful token whose hostname or action differs.
- **GitHub App:** install it only on `Thorncrag/ARRP`; grant only **Discussions: Read and write**. Do not grant Contents, Issues, Actions, administration, organization, or user permissions. Rotate the private key if the App scope changes or a compromise is suspected.
- **Vercel access:** keep the App private key, Turnstile secret, and Resend key as production-only encrypted environment values; restrict production deployment and environment access to the smallest maintainer set. Preview deployments must not inherit production secrets unless they are explicitly intended for controlled testing.
- **Resend:** use a verified sender domain, a least-privileged API key, and provider alerts for unusual sending volume. The contributor's optional email is never posted publicly; it is delivered only to the configured private mailbox.
- **GitHub Actions:** leave the intake agent manually dispatched and report-only. The workflow accepts a specific numeric public-intake comment ID, reads only that comment, and uses a read-only token. Do not add write permissions or automatic triggers without revising `framework/INTAKE_AGENT_PROCESS.md` and testing the action-specific validator.

## Application protections

- Exact-origin CORS, JSON-only requests, no-store API responses, field and serialized-body limits, a honeypot, Turnstile verification, and a local per-instance burst limiter protect both endpoints.
- The public privacy preflight screens every submitted field, including page context. It returns categories only and does not copy rejected text into GitHub, an action record, or an error message.
- Public comments render contributor text and source material as literal text rather than executable Markdown. The server publishes only the official route label, not raw context supplied by the browser.
- A Content Security Policy limits the Vercel page to local assets and the Turnstile service. HSTS, MIME protection, frame denial, referrer policy, permissions policy, and no-store API responses are also applied.
- Concurrent first submissions re-check for an existing marked canonical Discussion, select the oldest one, and remove an empty locally created duplicate before posting a comment. Absolute cross-instance serialization would require a managed lock service and is not claimed here.

## Operational review

Review these controls after any provider change and at least quarterly: WAF rule activity, Turnstile hostname settings, GitHub App installation and permissions, Vercel project access, Resend sending activity, deployed response headers, and the current repository secret-scan result.
