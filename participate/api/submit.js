"use strict";

const crypto = require("node:crypto");
const {
  allowedOrigins,
  canonicalDiscussionBody,
  createAppJwt,
  discussionCommentBody,
  isAllowedOrigin,
  validateSubmission,
} = require("./_shared");
const { resolveRoute } = require("./route-index");
const { screenPublicSubmission } = require("./safety");

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

function githubHeaders(token) {
  return {
    accept: "application/vnd.github+json",
    authorization: `Bearer ${token}`,
    "content-type": "application/json",
    "user-agent": "ARRP-public-intake",
    "x-github-api-version": "2022-11-28",
  };
}

async function githubGraphql(token, query, variables) {
  const response = await fetch(`${GITHUB_API}/graphql`, {
    method: "POST",
    headers: githubHeaders(token),
    body: JSON.stringify({ query, variables }),
  });
  const result = await response.json();
  if (!response.ok || result.errors) throw new Error("GitHub Discussion request failed.");
  return result.data;
}

function canonicalDiscussionTitle(route) {
  return `ARRP public input — ${route.label}`;
}

async function findCanonicalDiscussion(token, route) {
  const marker = `ARRP-INTAKE-ROUTE:${route.key}`;
  const data = await githubGraphql(token, `query FindIntakeDiscussion($query: String!) {
    viewer { login }
    search(query: $query, type: DISCUSSION, first: 10) {
      nodes {
        ... on Discussion { id url number title body author { login } }
      }
    }
  }`, {
    query: `repo:Thorncrag/ARRP "${marker}"`,
  });
  const expectedTitle = canonicalDiscussionTitle(route);
  return data.search?.nodes?.find((discussion) => (
    discussion?.title === expectedTitle
    && discussion?.body?.includes(marker)
    && discussion?.author?.login === data.viewer?.login
  )) || null;
}

async function createCanonicalDiscussion(token, route) {
  const data = await githubGraphql(token, `mutation CreateCanonicalDiscussion($input: CreateDiscussionInput!) {
    createDiscussion(input: $input) { discussion { id url number title } }
  }`, {
    input: {
      repositoryId: process.env.GITHUB_REPOSITORY_ID,
      categoryId: process.env.GITHUB_DISCUSSION_CATEGORY_ID,
      title: canonicalDiscussionTitle(route),
      body: canonicalDiscussionBody(route),
    },
  });
  const discussion = data.createDiscussion?.discussion;
  if (!discussion?.id || !discussion?.url) throw new Error("GitHub Discussion creation failed.");
  return discussion;
}

async function addSubmissionComment(token, discussion, submission, submissionId, route) {
  const data = await githubGraphql(token, `mutation AddIntakeComment($input: AddDiscussionCommentInput!) {
    addDiscussionComment(input: $input) { comment { url } }
  }`, {
    input: {
      discussionId: discussion.id,
      body: discussionCommentBody(submission, submissionId, route),
    },
  });
  const comment = data.addDiscussionComment?.comment;
  if (!comment?.url) throw new Error("GitHub Discussion comment creation failed.");
  return comment;
}

async function routeSubmission(submission, submissionId) {
  const route = resolveRoute(submission);
  const token = await githubInstallationToken();
  let discussion = await findCanonicalDiscussion(token, route);
  if (!discussion) discussion = await createCanonicalDiscussion(token, route);
  const comment = await addSubmissionComment(token, discussion, submission, submissionId, route);
  return { discussion, comment, route };
}

async function sendReviewNotification(submission, routed) {
  const reviewEmail = String(process.env.ARRP_INTAKE_REVIEW_EMAIL || "").trim();
  if (!submission.email || !process.env.RESEND_API_KEY || !process.env.RESEND_FROM_EMAIL || !reviewEmail) return false;
  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      authorization: `Bearer ${process.env.RESEND_API_KEY}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      from: process.env.RESEND_FROM_EMAIL,
      to: [reviewEmail],
      subject: `ARRP public input: ${routed.route.label}`,
      text: `A contributor authorized ARRP to contact them about this submission.\n\nPublic discussion: ${routed.discussion.url}\nSubmission: ${routed.comment.url}\nRoute: ${routed.route.label}\nContributor email: ${submission.email}\nSubmission reference: ${submissionIdPlaceholder(routed.discussion)}`,
    }),
  });
  return response.ok;
}

function submissionIdPlaceholder(discussion) {
  return discussion.number ? `Discussion #${discussion.number}` : "See public discussion";
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
  // The public fields are screened before the GitHub Discussion exists. Do
  // not log a match or return the matched material: this endpoint must not
  // become a second place where sensitive content is retained.
  if (!screenPublicSubmission(submission).allowed) {
    send(res, 400, { error: "Remove personal, financial, or credential information from the public fields before submitting." });
    return;
  }
  const remoteIp = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim();
  try {
    if (!await verifyTurnstile(submission.turnstileToken, remoteIp)) {
      send(res, 400, { error: "Please complete the verification check and try again." });
      return;
    }
    const submissionId = crypto.randomUUID();
    const routed = await routeSubmission(submission, submissionId);
    const followUpRequested = Boolean(submission.email && submission.emailConsent);
    if (followUpRequested) {
      try { await sendReviewNotification(submission, routed); } catch (_) { /* Public receipt remains available. */ }
    }
    send(res, 201, {
      discussion_url: routed.discussion.url,
      discussion_title: routed.discussion.title,
      submission_url: routed.comment.url,
      route_label: routed.route.label,
      follow_up_requested: followUpRequested,
    });
  } catch (_) {
    // Do not log request-derived error text. The public receipt is the only
    // response surface for a submission that reaches this stage.
    send(res, 502, { error: "ARRP could not create the public discussion. Please try again later." });
  }
};

module.exports._test = {
  applyCors,
  findCanonicalDiscussion,
  canonicalDiscussionTitle,
  requiredConfiguration,
  resolveRoute,
  verifyTurnstile,
};
