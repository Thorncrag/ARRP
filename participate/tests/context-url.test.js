"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { sanitizeContextUrl, resolveReturnTarget } = require("../context-url");

test("context links accept only canonical ARRP Pages and repository URLs", () => {
  assert.equal(
    sanitizeContextUrl("https://thorncrag.github.io/ARRP/areas/JUD/issues/JUD-011/"),
    "https://thorncrag.github.io/ARRP/areas/JUD/issues/JUD-011/",
  );
  assert.equal(
    sanitizeContextUrl("https://github.com/Thorncrag/ARRP/issues/246"),
    "https://github.com/Thorncrag/ARRP/issues/246",
  );
});

test("context links reject executable, credentialed, and unrelated URLs", () => {
  for (const value of [
    "javascript:alert(document.domain)",
    "data:text/html,example",
    "https://attacker.example/ARRP/",
    "https://user:password@thorncrag.github.io/ARRP/",
    "http://thorncrag.github.io/ARRP/",
  ]) {
    assert.equal(sanitizeContextUrl(value), "");
  }
});

test("return navigation prefers page context and uses ARRP history when available", () => {
  assert.deepEqual(
    resolveReturnTarget(
      "https://thorncrag.github.io/",
      "https://thorncrag.github.io/ARRP/areas/JUD/issues/JUD-011/#proposal-scoring",
    ),
    {
      url: "https://thorncrag.github.io/ARRP/areas/JUD/issues/JUD-011/#proposal-scoring",
      useHistory: true,
    },
  );
});

test("return navigation safely falls back to the ARRP home page", () => {
  assert.deepEqual(resolveReturnTarget("https://unrelated.example/", "javascript:alert(1)"), {
    url: "https://thorncrag.github.io/ARRP/",
    useHistory: false,
  });
});
