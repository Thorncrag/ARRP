"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { contactMode, expectedTurnstile, intakeMode } = require("../api/security");

function withEnvironment(values, callback) {
  const original = Object.fromEntries(Object.keys(values).map((key) => [key, process.env[key]]));
  try {
    for (const [key, value] of Object.entries(values)) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
    callback();
  } finally {
    for (const [key, value] of Object.entries(original)) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }
}

test("intake mode recognizes live and emergency paused states", () => {
  withEnvironment({ ARRP_INTAKE_MODE: "live" }, () => assert.equal(intakeMode(), "live"));
  withEnvironment({ ARRP_INTAKE_MODE: "paused" }, () => assert.equal(intakeMode(), "paused"));
  withEnvironment({ ARRP_INTAKE_MODE: "unexpected" }, () => assert.equal(intakeMode(), "preview"));
});

test("contact mode defaults live and requires an explicit disable", () => {
  withEnvironment({ ARRP_CONTACT_MODE: undefined }, () => assert.equal(contactMode(), "live"));
  withEnvironment({ ARRP_CONTACT_MODE: "disabled" }, () => assert.equal(contactMode(), "disabled"));
});

test("Turnstile defaults to the canonical public hostname and action", () => {
  withEnvironment(
    { ARRP_TURNSTILE_HOSTNAME: undefined, ARRP_TURNSTILE_ACTION: undefined },
    () => assert.deepEqual(expectedTurnstile(), {
      hostname: "gab.durablerepublic.org",
      action: "arrp_public_intake",
    }),
  );
});
