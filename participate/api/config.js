"use strict";

const { allowedOrigins, isAllowedOrigin } = require("./_shared");

module.exports = function config(req, res) {
  if (req.method !== "GET") {
    res.setHeader("Allow", "GET");
    res.status(405).json({ error: "Method not allowed." });
    return;
  }
  const origin = req.headers.origin;
  if (origin && isAllowedOrigin(origin, allowedOrigins(process.env.ARRP_ALLOWED_ORIGINS))) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Vary", "Origin");
  }
  const live = process.env.ARRP_INTAKE_MODE === "live";
  res.setHeader("Cache-Control", "no-store");
  res.status(200).json({
    mode: live ? "live" : "preview",
    turnstileSiteKey: live ? (process.env.TURNSTILE_SITE_KEY || "") : "",
    emailEnabled: live && Boolean(process.env.RESEND_API_KEY && process.env.RESEND_FROM_EMAIL),
  });
};
