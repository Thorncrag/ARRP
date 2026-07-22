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
const {
  allowLocalBurst,
  clientIp,
  intakeMode,
  requestExceedsLimit,
  setNoStore,
  verifyTurnstile,
} = require("./security");

const GITHUB_API = "https://api.github.com";

function intakeOperationError(stage) {
  const error = new Error("ARRP intake operation failed.");
  error.intakeOperation = stage;
  return error;
}

function send(res, status, body) {
  setNoStore(res);
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

async function githubInstallationToken() {
  try {
    let jwt;
    try {
      jwt = createAppJwt(process.env.GITHUB_APP_ID, privateKey());
    } catch (_) {
      throw intakeOperationError("github-app-jwt");
    }
    const response = await fetch(`${GITHUB_API}/app/installations/${process.env.GITHUB_APP_INSTALLATION_ID}/access_tokens`, {
      method: "POST",
      headers: {
        accept: "application/vnd.github+json",
        authorization: `Bearer ${jwt}`,
        "user-agent": "ARRP-public-intake",
        "x-github-api-version": "2022-11-28",
      },
    });
    if (!response.ok) throw intakeOperationError("github-app-installation-token");
    const result = await response.json();
    if (!result?.token) throw intakeOperationError("github-app-installation-response");
    return result.token;
  } catch (error) {
    if (error?.intakeOperation) throw error;
    throw intakeOperationError("github-app-installation-request");
  }
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

async function githubGraphql(token, operation, query, variables) {
  try {
    const response = await fetch(`${GITHUB_API}/graphql`, {
      method: "POST",
      headers: githubHeaders(token),
      body: JSON.stringify({ query, variables }),
    });
    const result = await response.json();
    if (!response.ok || result.errors) throw intakeOperationError(`github-discussion-${operation}`);
    return result.data;
  } catch (error) {
    if (error?.intakeOperation) throw error;
    throw intakeOperationError(`github-discussion-${operation}-request`);
  }
}

function canonicalDiscussionTitle(route) {
  return `ARRP public input — ${route.label}`;
}

async function findCanonicalDiscussion(token, route) {
  const marker = `ARRP-INTAKE-ROUTE:${route.key}`;
  const data = await githubGraphql(token, "lookup", `query FindIntakeDiscussion($query: String!) {
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
  return data.search?.nodes?.filter((discussion) => (
    discussion?.title === expectedTitle
    && discussion?.body?.includes(marker)
    && discussion?.author?.login === data.viewer?.login
  )).sort((left, right) => left.number - right.number)[0] || null;
}

async function createCanonicalDiscussion(token, route) {
  const data = await githubGraphql(token, "create", `mutation CreateCanonicalDiscussion($input: CreateDiscussionInput!) {
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
  if (!discussion?.id || !discussion?.url) throw intakeOperationError("github-discussion-create-response");
  return discussion;
}

async function deleteDiscussion(token, discussion) {
  await githubGraphql(token, "delete", `mutation DeleteCanonicalDiscussion($input: DeleteDiscussionInput!) {
    deleteDiscussion(input: $input) { clientMutationId }
  }`, { input: { id: discussion.id } });
}

async function addSubmissionComment(token, discussion, submission, submissionId, route) {
  const data = await githubGraphql(token, "comment", `mutation AddIntakeComment($input: AddDiscussionCommentInput!) {
    addDiscussionComment(input: $input) { comment { url } }
  }`, {
    input: {
      discussionId: discussion.id,
      body: discussionCommentBody(submission, submissionId, route),
    },
  });
  const comment = data.addDiscussionComment?.comment;
  if (!comment?.url) throw intakeOperationError("github-discussion-comment-response");
  return comment;
}

async function routeSubmission(submission, submissionId) {
  const route = resolveRoute(submission);
  const token = await githubInstallationToken();
  let discussion = await findCanonicalDiscussion(token, route);
  if (!discussion) {
    const created = await createCanonicalDiscussion(token, route);
    // Search indexing can lag immediately after creation. The mutation's
    // returned Discussion is safe to use; if search has caught up and finds an
    // older canonical thread, remove the empty extra thread before commenting.
    const indexedDiscussion = await findCanonicalDiscussion(token, route);
    discussion = indexedDiscussion || created;
    if (indexedDiscussion && indexedDiscussion.id !== created.id) await deleteDiscussion(token, created);
  }
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
  setNoStore(res);
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
  if (intakeMode() === "paused") {
    send(res, 503, { error: "Public intake is currently disabled by ARRP. Please do not retry at this time." });
    return;
  }
  if (intakeMode() !== "live") {
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
  if (requestExceedsLimit(req, 20000)) {
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
  if (!allowLocalBurst(req, "public")) {
    send(res, 429, { error: "Too many requests. Please wait and try again later." });
    return;
  }
  const remoteIp = clientIp(req);
  try {
    if (!await verifyTurnstile(submission.turnstileToken, remoteIp)) {
      send(res, 400, { error: "Please complete the verification check and try again." });
      return;
    }
    const submissionId = crypto.randomUUID();
    const routed = await routeSubmission(submission, submissionId);
    const followUpRequested = Boolean(submission.email);
    if (followUpRequested) {
      try { await sendReviewNotification(submission, routed); } catch (_) { /* Public confirmation remains available. */ }
    }
    send(res, 201, {
      discussion_url: routed.discussion.url,
      discussion_title: routed.discussion.title,
      submission_url: routed.comment.url,
      route_label: routed.route.label,
      follow_up_requested: followUpRequested,
    });
  } catch (error) {
    // Keep request-derived content and secrets out of logs. A fixed operation
    // label permits an administrator to diagnose service configuration.
    console.error("ARRP public intake GitHub operation failed", {
      stage: error?.intakeOperation || "unexpected",
    });
    send(res, 502, { error: "ARRP could not create the public discussion. Please try again later." });
  }
};

module.exports._test = {
  applyCors,
  findCanonicalDiscussion,
  canonicalDiscussionTitle,
  requiredConfiguration,
  resolveRoute,
  routeSubmission,
  verifyTurnstile,
};
