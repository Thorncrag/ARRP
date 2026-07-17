"use strict";

const crypto = require("node:crypto");
const test = require("node:test");
const assert = require("node:assert/strict");
const {
  canonicalDiscussionBody,
  createAppJwt,
  discussionCommentBody,
  validateContact,
  validateSubmission,
} = require("../api/_shared");
const { resolveRoute } = require("../api/route-index");
const submitEndpoint = require("../api/submit");

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
  const route = resolveRoute(submission);
  assert.equal(route.key, "PROPOSAL:DOJ-007");
  assert.match(discussionCommentBody(submission, "record-1", route), /DOJ-007/);
  assert.doesNotMatch(discussionCommentBody(submission, "record-1", route), /reader@example\.org/);
  assert.match(canonicalDiscussionBody(route), /ARRP-INTAKE-ROUTE:PROPOSAL:DOJ-007/);
});

test("public comment rendering does not publish raw context or executable Markdown", () => {
  const { submission } = validateSubmission({
    title: "[Misleading](https://example.invalid)",
    body: "![external image](https://example.invalid/pixel.png)",
    sources: "https://example.invalid/source",
    context: { pageTitle: "synthetic@example.invalid" },
  });
  const rendered = discussionCommentBody(submission, "record-1", { label: "General input" });
  assert.doesNotMatch(rendered, /synthetic@example\.invalid/);
  assert.match(rendered, /^    !\[external image\]/m);
  assert.match(rendered, /Automatic ARRP route/);
});

test("route resolution uses the entered related page before the page where the form opened", () => {
  const route = resolveRoute({
    related: "https://thorncrag.github.io/ARRP/areas/REG/issues/REG-001/",
    context: {
      proposal: "DOJ-007",
      pageTitle: "DOJ-007 — Independent Investigation of Presidential and Senior Executive Misconduct",
      pageUrl: "https://thorncrag.github.io/ARRP/areas/DOJ/issues/DOJ-007/",
    },
  });
  assert.equal(route.key, "PROPOSAL:REG-001");
});

test("route resolution uses page context and sends unrecognized input to general intake", () => {
  assert.equal(resolveRoute({ context: { pageUrl: "https://thorncrag.github.io/ARRP/areas/DOM/issues/DOM-005/" } }).key, "PROPOSAL:DOM-005");
  assert.equal(resolveRoute({ related: "not an ARRP page", context: {} }).key, "GENERAL");
});

test("canonical Discussion lookup accepts only the intake app's marked thread", async () => {
  const originalFetch = global.fetch;
  const route = resolveRoute({ context: { proposal: "DOJ-007" } });
  const title = submitEndpoint._test.canonicalDiscussionTitle(route);
  global.fetch = async () => ({
    ok: true,
    json: async () => ({
      data: {
        viewer: { login: "arrp-public-intake[bot]" },
        search: {
          nodes: [
            { id: "bad", title, body: "<!-- ARRP-INTAKE-ROUTE:PROPOSAL:DOJ-007 -->", author: { login: "someone-else" } },
            { id: "good", title, body: "<!-- ARRP-INTAKE-ROUTE:PROPOSAL:DOJ-007 -->", author: { login: "arrp-public-intake[bot]" }, url: "https://github.com/Thorncrag/ARRP/discussions/1" },
          ],
        },
      },
    }),
  });
  try {
    const found = await submitEndpoint._test.findCanonicalDiscussion("test-token", route);
    assert.equal(found.id, "good");
  } finally {
    global.fetch = originalFetch;
  }
});

test("canonical Discussion lookup chooses the oldest matching intake thread", async () => {
  const originalFetch = global.fetch;
  const route = resolveRoute({ context: { proposal: "DOJ-007" } });
  const title = submitEndpoint._test.canonicalDiscussionTitle(route);
  global.fetch = async () => ({
    ok: true,
    json: async () => ({
      data: {
        viewer: { login: "arrp-public-intake[bot]" },
        search: {
          nodes: [
            { id: "later", number: 9, title, body: "<!-- ARRP-INTAKE-ROUTE:PROPOSAL:DOJ-007 -->", author: { login: "arrp-public-intake[bot]" }, url: "https://github.com/Thorncrag/ARRP/discussions/9" },
            { id: "first", number: 4, title, body: "<!-- ARRP-INTAKE-ROUTE:PROPOSAL:DOJ-007 -->", author: { login: "arrp-public-intake[bot]" }, url: "https://github.com/Thorncrag/ARRP/discussions/4" },
          ],
        },
      },
    }),
  });
  try {
    const found = await submitEndpoint._test.findCanonicalDiscussion("test-token", route);
    assert.equal(found.id, "first");
  } finally {
    global.fetch = originalFetch;
  }
});

test("submission validation requires explicit permission before email delivery", () => {
  const { errors } = validateSubmission({ title: "Concern", body: "Details", email: "reader@example.org" });
  assert.match(errors[0], /Confirm/);
});

test("private author contact accepts an optional reply email without public-input consent", () => {
  const { contact, errors } = validateContact({
    title: "  Printable edition request ",
    body: " Please send information about the printable edition. ",
    email: "Reader@example.org",
    context: { pageTitle: "ARRP", pageUrl: "https://thorncrag.github.io/ARRP/" },
  });
  assert.deepEqual(errors, []);
  assert.equal(contact.title, "Printable edition request");
  assert.equal(contact.email, "reader@example.org");
});

test("GitHub App JWT has three compact components", () => {
  const { privateKey } = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
  const jwt = createAppJwt("123", privateKey.export({ type: "pkcs1", format: "pem" }), 1000);
  assert.equal(jwt.split(".").length, 3);
});
