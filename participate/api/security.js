"use strict";

const crypto = require("node:crypto");

// This limiter is deliberately an additional burst control, not a substitute
// for the required Vercel Firewall/WAF distributed rate rule. Serverless
// instances do not share memory, but this immediately blocks repeat traffic
// that reaches one warm instance without retaining a raw IP address.
const buckets = new Map();
const MAX_BUCKETS = 4096;

function intakeMode() {
  const mode = String(process.env.ARRP_INTAKE_MODE || "preview").trim().toLowerCase();
  return mode === "live" || mode === "paused" ? mode : "preview";
}

function contactMode() {
  return String(process.env.ARRP_CONTACT_MODE || "live").trim().toLowerCase() === "disabled"
    ? "disabled"
    : "live";
}

function clientIp(req) {
  return String(
    req.headers["x-vercel-forwarded-for"]
    || req.headers["x-forwarded-for"]
    || req.headers["x-real-ip"]
    || "",
  ).split(",")[0].trim();
}

function byteLength(value) {
  try {
    return Buffer.byteLength(JSON.stringify(value || {}), "utf8");
  } catch (_) {
    return Number.POSITIVE_INFINITY;
  }
}

function requestExceedsLimit(req, limit) {
  const declared = Number(req.headers["content-length"] || 0);
  return declared > limit || byteLength(req.body) > limit;
}

function expectedTurnstile() {
  return {
    hostname: String(process.env.ARRP_TURNSTILE_HOSTNAME || "arrp-public-intake.vercel.app").trim(),
    action: String(process.env.ARRP_TURNSTILE_ACTION || "arrp_public_intake").trim(),
  };
}

async function verifyTurnstile(token, remoteIp) {
  const expected = expectedTurnstile();
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
  return result.success === true
    && result.hostname === expected.hostname
    && result.action === expected.action;
}

function allowLocalBurst(req, channel) {
  const now = Date.now();
  const policy = channel === "contact"
    ? { limit: 2, windowMs: 10 * 60 * 1000 }
    : { limit: 3, windowMs: 10 * 60 * 1000 };
  const ip = clientIp(req);
  if (!ip) return false;
  const key = crypto.createHash("sha256").update(`${channel}:${ip}`).digest("base64url");
  const existing = buckets.get(key);
  const bucket = !existing || now >= existing.resetAt
    ? { count: 0, resetAt: now + policy.windowMs }
    : existing;
  bucket.count += 1;
  buckets.set(key, bucket);

  if (buckets.size > MAX_BUCKETS) {
    for (const [storedKey, stored] of buckets) {
      if (now >= stored.resetAt || buckets.size > MAX_BUCKETS) buckets.delete(storedKey);
    }
  }
  return bucket.count <= policy.limit;
}

function setNoStore(res) {
  res.setHeader("Cache-Control", "no-store");
}

module.exports = {
  allowLocalBurst,
  clientIp,
  contactMode,
  expectedTurnstile,
  intakeMode,
  requestExceedsLimit,
  setNoStore,
  verifyTurnstile,
};
