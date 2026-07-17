"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { containsPaymentCard, screenPrivateContact, screenPublicSubmission } = require("../api/safety");

test("public privacy screen allows ordinary policy discussion", () => {
  const result = screenPublicSubmission({
    title: "Preserve a public record",
    body: "ARRP should examine whether the policy supplies a durable public remedy.",
    sources: "https://example.org/record",
    related: "JUD-011",
  });
  assert.equal(result.allowed, true);
  assert.deepEqual(result.findings, []);
});

test("public privacy screen returns categories without retaining matched material", () => {
  const result = screenPublicSubmission({ title: "Contact me at reader@example.org", body: "Call (202) 555-0199." });
  assert.equal(result.allowed, false);
  assert.deepEqual(result.findings, ["email_address", "phone_number"]);
  assert.doesNotMatch(JSON.stringify(result), /reader@example\.org|555-0199/);
});

test("payment-card detector uses checksum validation", () => {
  assert.equal(containsPaymentCard("4111 1111 1111 1111"), true);
  assert.equal(containsPaymentCard("4111 1111 1111 1112"), false);
});

test("public privacy screen blocks credentials and identifiers", () => {
  const result = screenPublicSubmission({
    title: "Private material",
    body: "SSN 123-45-6789 and -----BEGIN PRIVATE KEY----- should never be public.",
  });
  assert.equal(result.allowed, false);
  assert.deepEqual(result.findings, ["government_identifier", "credential"]);
});

test("public privacy screen includes all submitted page context", () => {
  const result = screenPublicSubmission({
    title: "Ordinary public input",
    body: "The issue should be reviewed.",
    context: { pageTitle: "synthetic@example.invalid" },
  });
  assert.equal(result.allowed, false);
  assert.deepEqual(result.findings, ["email_address"]);
});

test("private contact allows an email but blocks financial or credential material", () => {
  assert.equal(screenPrivateContact({ title: "Reply", body: "Reach me at reader@example.org." }).allowed, true);
  assert.equal(screenPrivateContact({ title: "Private material", body: "Use 4111 1111 1111 1111." }).allowed, false);
});
