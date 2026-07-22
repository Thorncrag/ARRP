"use strict";

const crypto = require("node:crypto");

const LIMITS = {
  title: 140,
  body: 8000,
  sources: 4000,
  related: 1000,
  pageTitle: 300,
  pageUrl: 2048,
  proposal: 64,
  email: 254,
};

function text(value, limit) {
  return typeof value === "string" ? value.trim().slice(0, limit) : "";
}

function isEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function validateSubmission(value) {
  const raw = value && typeof value === "object" ? value : {};
  const submission = {
    title: text(raw.title, LIMITS.title),
    body: text(raw.body, LIMITS.body),
    sources: text(raw.sources, LIMITS.sources),
    related: text(raw.related, LIMITS.related),
    email: text(raw.email, LIMITS.email).toLowerCase(),
    turnstileToken: text(raw.turnstileToken, 4096),
    honeypot: text(raw.website, 256),
    context: {
      proposal: text(raw.context?.proposal, LIMITS.proposal),
      pageTitle: text(raw.context?.pageTitle, LIMITS.pageTitle),
      pageUrl: text(raw.context?.pageUrl, LIMITS.pageUrl),
    },
  };
  const errors = [];
  if (!submission.title) errors.push("Provide a short title.");
  if (!submission.body) errors.push("Describe what ARRP should consider.");
  if (submission.email && !isEmail(submission.email)) errors.push("Provide a valid email address or leave it blank.");
  return { submission, errors };
}

function validateContact(value) {
  const raw = value && typeof value === "object" ? value : {};
  const contact = {
    title: text(raw.title, LIMITS.title),
    body: text(raw.body, LIMITS.body),
    email: text(raw.email, LIMITS.email).toLowerCase(),
    turnstileToken: text(raw.turnstileToken, 4096),
    honeypot: text(raw.website, 256),
    context: {
      proposal: text(raw.context?.proposal, LIMITS.proposal),
      pageTitle: text(raw.context?.pageTitle, LIMITS.pageTitle),
      pageUrl: text(raw.context?.pageUrl, LIMITS.pageUrl),
    },
  };
  const errors = [];
  if (!contact.title) errors.push("Provide a short subject.");
  if (!contact.body) errors.push("Write a message for the author.");
  if (contact.email && !isEmail(contact.email)) errors.push("Provide a valid reply email address or leave it blank.");
  return { contact, errors };
}

function allowedOrigins(value) {
  return new Set(String(value || "").split(",").map((item) => item.trim()).filter(Boolean));
}

function isAllowedOrigin(origin, allowed) {
  return Boolean(origin) && allowed.has(origin);
}

function asIndentedCode(value) {
  const lines = String(value || "").replace(/\r\n?/g, "\n").split("\n");
  return lines.map((line) => `    ${line}`).join("\n");
}

function asSafeHeading(value) {
  return String(value || "")
    .replace(/\\/g, "\\\\")
    .replace(/([`*_{}\[\]<>#|])/g, "\\$1")
    .replace(/@/g, "@\u200b")
    .replace(/[\r\n]+/g, " ")
    .trim();
}

function markdownSection(title, content) {
  return content ? `\n## ${title}\n${content}\n` : "";
}

function canonicalDiscussionBody(route) {
  return [
    "# ARRP public input",
    "",
    `This Discussion collects public input related to **${route.label}**. Each submission appears as a separate comment below.`,
    "",
    "Public input is not itself a project decision, source admission, preliminary candidate, or proposed candidate.",
    "",
    `<!-- ARRP-INTAKE-ROUTE:${route.key} -->`,
  ].join("\n");
}

function discussionCommentBody(submission, submissionId, route) {
  const followUpStatus = submission.email
    ? "Requested; the address was routed privately and is not included in this public post."
    : "Not requested; no address was supplied.";
  return [
    `<!-- ARRP-INTAKE-SUBMISSION:${submissionId} -->`,
    `## ${asSafeHeading(submission.title)}`,
    "",
    asIndentedCode(submission.body),
    markdownSection("Sources or links", submission.sources ? asIndentedCode(submission.sources) : ""),
    markdownSection("Automatic ARRP route", asIndentedCode(route.label)),
    "## Intake record",
    `- Submission reference: \`${submissionId}\``,
    `- Automatic route: ${route.label}`,
    `- Private follow-up: ${followUpStatus}`,
    "- Status: Received for ARRP review",
    "- Note: A public submission is not itself a project decision, preliminary candidate, or proposed candidate.",
  ].filter(Boolean).join("\n");
}

function base64url(value) {
  return Buffer.from(value).toString("base64url");
}

function createAppJwt(appId, privateKey, now = Math.floor(Date.now() / 1000)) {
  const header = base64url(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const payload = base64url(JSON.stringify({ iat: now - 60, exp: now + 540, iss: appId }));
  const signer = crypto.createSign("RSA-SHA256");
  signer.update(`${header}.${payload}`);
  signer.end();
  return `${header}.${payload}.${signer.sign(privateKey).toString("base64url")}`;
}

module.exports = {
  allowedOrigins,
  asIndentedCode,
  asSafeHeading,
  canonicalDiscussionBody,
  createAppJwt,
  discussionCommentBody,
  isAllowedOrigin,
  validateContact,
  validateSubmission,
};
