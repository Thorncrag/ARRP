"use strict";

const crypto = require("node:crypto");
const test = require("node:test");
const assert = require("node:assert/strict");
const { createAppJwt, discussionBody, validateSubmission } = require("../api/_shared");

test("submission validation retains public content and removes excess whitespace", () => {
  const { submission, errors } = validateSubmission({
    title: "  A source to consider  ",
    body: "  ARRP should consider this institutional question. ",
    sources: " https://example.org/source ",
    email: " Reader@example.org ",
    emailConsent: true,
    context: { proposal: "DOJ-007", pageTitle: "Example", pageUrl: "https://example.org/page" },
  });
  assert.deepEqual(errors, []);
  assert.equal(submission.title, "A source to consider");
  assert.equal(submission.email, "reader@example.org");
  assert.match(discussionBody(submission, "record-1"), /DOJ-007/);
  assert.doesNotMatch(discussionBody(submission, "record-1"), /reader@example\.org/);
});

test("submission validation requires explicit permission before email delivery", () => {
  const { errors } = validateSubmission({ title: "Concern", body: "Details", email: "reader@example.org" });
  assert.match(errors[0], /Confirm/);
});

test("GitHub App JWT has three compact components", () => {
  const { privateKey } = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
  const jwt = createAppJwt("123", privateKey.export({ type: "pkcs1", format: "pem" }), 1000);
  assert.equal(jwt.split(".").length, 3);
});
