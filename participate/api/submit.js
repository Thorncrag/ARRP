"use strict";

const crypto = require("node:crypto");
const {
  allowedOrigins,
  createAppJwt,
  discussionBody,
  isAllowedOrigin,
  validateSubmission,
} = require("./_shared");

const GITHUB_API = "https://api.github.com";

function send(res, status, body) {
  res.status(status).json(body);
}

function applyCors(req, res) {
  const origin = req.headers.origin;
  const accepted = isAllowedOrigin(origin, allowedOrigins(process.env.ARRP_ALLOWED_ORIGINS));
  if (accepted) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    res.setHeader("Vary", "Origin");
  }
  return accepted;
}

function privateKey() {
  return String(process.env.GITHUB_APP_PRIVATE_KEY || "").replace(/\\n/g, "\n");
}

function requiredConfiguration() {
  const required = [
    "ARRP_ALLOWED_ORIGINS",
    "TURNSTILE_SECRET_KEY",
    "GITHUB_APP_ID",
    "GITHUB_APP_INSTALLATION_ID",
    "GITHUB_APP_PRIVATE_KEY",
    "GITHUB_REPOSITORY_ID",
    "GITHUB_DISCUSSION_CATEGORY_ID",
  ];
  return required.filter((key) => !process.env[key]);
}

async function verifyTurnstile(token, remoteIp) {
  const response = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      secret: process.env.TURNSTILE_SECRET_KEY,
      response: token,
      ...(remoteIp ? { remoteip: remoteIp } : {}),
    }),
  });
  if (!response.ok) return false;
  const result = await response.json();
  return result.success === true;
}

async function githubInstallationToken() {
  const jwt = createAppJwt(process.env.GITHUB_APP_ID, privateKey());
  const response = await fetch(`${GITHUB_API}/app/installations/${process.env.GITHUB_APP_INSTALLATION_ID}/access_tokens`, {
    method: "POST",
    headers: {
      accept: "application/vnd.github+json",
      authorization: `Bearer ${jwt}`,
      "user-agent": "ARRP-public-intake",
      "x-github-api-version": "2022-11-28",
    },
  });
  if (!response.ok) throw new Error("GitHub App authentication failed.");
  const result = await response.json();
  return result.token;
}

async function createDiscussion(submission, submissionId) {
  const token = await githubInstallationToken();
  const response = await fetch(`${GITHUB_API}/graphql`, {
    method: "POST",
    headers: {
      accept: "application/vnd.github+json",
      authorization: `Bearer ${token}`,
      "content-type": "application/json",
      "user-agent": "ARRP-public-intake",
      "x-github-api-version": "2022-11-28",
    },
    body: JSON.stringify({
      query: `mutation CreateDiscussion($input: CreateDiscussionInput!) {
        createDiscussion(input: $input) {
          discussion { url number title }
        }
      }`,
      variables: {
        input: {
          repositoryId: process.env.GITHUB_REPOSITORY_ID,
          categoryId: process.env.GITHUB_DISCUSSION_CATEGORY_ID,
          title: `Public submission — ${submission.title}`,
          body: discussionBody(submission, submissionId),
        },
      },
    }),
  });
  const result = await response.json();
  if (!response.ok || result.errors || !result.data?.createDiscussion?.discussion?.url) {
    throw new Error("GitHub Discussion creation failed.");
  }
  return result.data.createDiscussion.discussion;
}

async function sendEmail(email, discussion) {
  if (!email || !process.env.RESEND_API_KEY || !process.env.RESEND_FROM_EMAIL) return false;
  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      authorization: `Bearer ${process.env.RESEND_API_KEY}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      from: process.env.RESEND_FROM_EMAIL,
      to: [email],
      subject: "Your ARRP submission link",
      text: `Your public ARRP submission is available at: ${discussion.url}\n\nKeep this link to follow responses. A GitHub account is optional; signed-in users can subscribe to the discussion for notifications.`,
    }),
  });
  return response.ok;
}

module.exports = async function submit(req, res) {
  const acceptedOrigin = applyCors(req, res);
  if (req.method === "OPTIONS") {
    if (!acceptedOrigin) {
      send(res, 403, { error: "This request did not come from an approved ARRP page." });
      return;
    }
    res.status(204).end();
    return;
  }
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    send(res, 405, { error: "Method not allowed." });
    return;
  }
  if (process.env.ARRP_INTAKE_MODE !== "live") {
    send(res, 503, { error: "The public intake service is not live yet." });
    return;
  }
  const missing = requiredConfiguration();
  if (missing.length) {
    send(res, 503, { error: "The intake service is not configured." });
    return;
  }
  if (!acceptedOrigin) {
    send(res, 403, { error: "This request did not come from an approved ARRP page." });
    return;
  }
  if (!String(req.headers["content-type"] || "").toLowerCase().includes("application/json")) {
    send(res, 415, { error: "Use the ARRP submission form to send this request." });
    return;
  }
  if (Number(req.headers["content-length"] || 0) > 20000) {
    send(res, 413, { error: "The submission is too large." });
    return;
  }
  const { submission, errors } = validateSubmission(req.body);
  if (submission.honeypot) {
    send(res, 202, { received: true });
    return;
  }
  if (errors.length) {
    send(res, 400, { error: errors[0] });
    return;
  }
  const remoteIp = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim();
  try {
    if (!await verifyTurnstile(submission.turnstileToken, remoteIp)) {
      send(res, 400, { error: "Please complete the verification check and try again." });
      return;
    }
    const submissionId = crypto.randomUUID();
    const discussion = await createDiscussion(submission, submissionId);
    let emailSent = false;
    if (submission.email) {
      try { emailSent = await sendEmail(submission.email, discussion); } catch (_) { emailSent = false; }
    }
    send(res, 201, {
      discussion_url: discussion.url,
      discussion_title: discussion.title,
      email_sent: emailSent,
    });
  } catch (error) {
    console.error("ARRP public intake failure", error.message);
    send(res, 502, { error: "ARRP could not create the public discussion. Please try again later." });
  }
};

module.exports._test = { applyCors, requiredConfiguration, verifyTurnstile };
