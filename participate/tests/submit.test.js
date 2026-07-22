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
const contactEndpoint = require("../api/contact");
const submitEndpoint = require("../api/submit");

test("submission validation retains public content and removes excess whitespace", () => {
  const { submission, errors } = validateSubmission({
    title: "  A source to consider  ",
    body: "  ARRP should consider this institutional question. ",
    sources: " https://example.org/source ",
    email: " Reader@example.org ",
    context: { proposal: "DOJ-007", pageTitle: "Example", pageUrl: "https://example.org/page" },
  });
  assert.deepEqual(errors, []);
  assert.equal(submission.title, "A source to consider");
  assert.equal(submission.email, "reader@example.org");
  const route = resolveRoute(submission);
  assert.equal(route.key, "PROPOSAL:DOJ-007");
  assert.match(discussionCommentBody(submission, "record-1", route), /DOJ-007/);
  assert.doesNotMatch(discussionCommentBody(submission, "record-1", route), /reader@example\.org/);
  assert.match(discussionCommentBody(submission, "record-1", route), /Private follow-up: Requested/);
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
  assert.match(rendered, /Private follow-up: Not requested/);
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

test("first submission uses GitHub's created Discussion before search indexing catches up", async () => {
  const originalFetch = global.fetch;
  const environmentKeys = [
    "GITHUB_APP_ID",
    "GITHUB_APP_INSTALLATION_ID",
    "GITHUB_APP_PRIVATE_KEY",
    "GITHUB_REPOSITORY_ID",
    "GITHUB_DISCUSSION_CATEGORY_ID",
  ];
  const originalEnvironment = Object.fromEntries(environmentKeys.map((key) => [key, process.env[key]]));
  const { privateKey } = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
  Object.assign(process.env, {
    GITHUB_APP_ID: "123",
    GITHUB_APP_INSTALLATION_ID: "456",
    GITHUB_APP_PRIVATE_KEY: privateKey.export({ type: "pkcs1", format: "pem" }),
    GITHUB_REPOSITORY_ID: "repository-id",
    GITHUB_DISCUSSION_CATEGORY_ID: "category-id",
  });
  global.fetch = async (url, options = {}) => {
    if (String(url).includes("/access_tokens")) {
      return { ok: true, json: async () => ({ token: "installation-token" }) };
    }
    const request = JSON.parse(options.body);
    if (request.query.includes("FindIntakeDiscussion")) {
      return { ok: true, json: async () => ({ data: { viewer: { login: "arrp-public-intake[bot]" }, search: { nodes: [] } } }) };
    }
    if (request.query.includes("CreateCanonicalDiscussion")) {
      return { ok: true, json: async () => ({ data: { createDiscussion: { discussion: { id: "created", number: 1, url: "https://github.com/Thorncrag/ARRP/discussions/1" } } } }) };
    }
    if (request.query.includes("AddIntakeComment")) {
      return { ok: true, json: async () => ({ data: { addDiscussionComment: { comment: { url: "https://github.com/Thorncrag/ARRP/discussions/1#discussioncomment-1" } } } }) };
    }
    throw new Error("Unexpected GitHub request in test.");
  };
  try {
    const routed = await submitEndpoint._test.routeSubmission({ title: "Test", body: "Test", context: {} }, "record-1");
    assert.equal(routed.discussion.id, "created");
    assert.match(routed.comment.url, /discussioncomment-1/);
  } finally {
    global.fetch = originalFetch;
    for (const [key, value] of Object.entries(originalEnvironment)) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }
});

test("entering an optional public follow-up email is itself the contact request", () => {
  const { submission, errors } = validateSubmission({ title: "Concern", body: "Details", email: "reader@example.org" });
  assert.deepEqual(errors, []);
  assert.equal(submission.email, "reader@example.org");
});

test("private author contact retains an optional reply email", () => {
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

test("private author contact accepts a blank reply email", () => {
  const { contact, errors } = validateContact({
    title: "Printable edition request",
    body: "Please send information about the printable edition.",
    email: "",
  });
  assert.deepEqual(errors, []);
  assert.equal(contact.email, "");
});

test("private author message clearly marks whether a reply email was supplied", async () => {
  const originalFetch = global.fetch;
  const originalMailbox = process.env.ARRP_CONTACT_EMAIL;
  const sent = [];
  process.env.ARRP_CONTACT_EMAIL = "author@example.org";
  global.fetch = async (_url, options) => {
    sent.push(JSON.parse(options.body));
    return { ok: true };
  };
  try {
    const noReply = validateContact({
      title: "No reply address",
      body: "Please review this message.",
      email: "",
    }).contact;
    const permitted = validateContact({
      title: "Permitted reply",
      body: "Please review this message.",
      email: "reader@example.org",
    }).contact;
    assert.equal(await contactEndpoint._test.sendPrivateMessage(noReply, "contact-1"), true);
    assert.equal(await contactEndpoint._test.sendPrivateMessage(permitted, "contact-2"), true);
    assert.equal(sent[0].reply_to, undefined);
    assert.doesNotMatch(sent[0].text, /reader@example\.org/);
    assert.match(sent[0].subject, /^\[NO CONTRIBUTOR REPLY\]/);
    assert.match(sent[0].text, /DO NOT REPLY TO THE CONTRIBUTOR/);
    assert.equal(sent[1].reply_to, "reader@example.org");
    assert.match(sent[1].text, /REPLY AUTHORIZED/);
  } finally {
    global.fetch = originalFetch;
    if (originalMailbox === undefined) delete process.env.ARRP_CONTACT_EMAIL;
    else process.env.ARRP_CONTACT_EMAIL = originalMailbox;
  }
});

test("GitHub App JWT has three compact components", () => {
  const { privateKey } = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
  const jwt = createAppJwt("123", privateKey.export({ type: "pkcs1", format: "pem" }), 1000);
  assert.equal(jwt.split(".").length, 3);
});
