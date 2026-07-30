"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const PARTICIPATE_ROOT = path.resolve(__dirname, "../../participate");
const indexHtml = fs.readFileSync(path.join(PARTICIPATE_ROOT, "index.html"), "utf8");
const appJavaScript = fs.readFileSync(path.join(PARTICIPATE_ROOT, "app.js"), "utf8");
const vercelConfig = JSON.parse(
  fs.readFileSync(path.join(PARTICIPATE_ROOT, "vercel.json"), "utf8"),
);

function contentSecurityPolicy() {
  const siteHeaders = vercelConfig.headers.find((entry) => entry.source === "/(.*)");
  const policy = siteHeaders?.headers?.find(
    (header) => header.key === "Content-Security-Policy",
  );
  return policy?.value || "";
}

test("installs exactly one Cloudflare Web Analytics beacon", () => {
  const beaconScripts = indexHtml.match(
    /<script\b[^>]*src="https:\/\/static\.cloudflareinsights\.com\/beacon\.min\.js"[^>]*>/g,
  ) || [];
  assert.equal(beaconScripts.length, 1);
  assert.match(beaconScripts[0], /\btype="module"/);
  assert.match(
    beaconScripts[0],
    /data-cf-beacon='\{"token": "[a-f0-9]{32}"\}'/,
  );
  assert.doesNotMatch(indexHtml, /googletagmanager|google-analytics|session[_ -]?replay/i);
});

test("permits only the required Cloudflare analytics origins", () => {
  const policy = contentSecurityPolicy();
  assert.match(
    policy,
    /script-src[^;]*https:\/\/static\.cloudflareinsights\.com(?:;|$)/,
  );
  assert.match(
    policy,
    /connect-src[^;]*https:\/\/cloudflareinsights\.com(?:;|$)/,
  );
  assert.doesNotMatch(policy, /https:\/\/\*|\*\.cloudflare/);
});

test("publishes the analytics privacy boundary", () => {
  assert.match(indexHtml, /cookie-free Cloudflare Web Analytics/);
  assert.match(indexHtml, /form fields are not part of that analytics integration/);
  assert.match(appJavaScript, /privacyNote\.textContent = \(contact/);
  assert.match(appJavaScript, /\+ analyticsPrivacyNote/);
});
