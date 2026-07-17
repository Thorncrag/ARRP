"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { sanitizeContextUrl } = require("../context-url");

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
