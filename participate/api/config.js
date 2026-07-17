"use strict";

const { allowedOrigins, isAllowedOrigin } = require("./_shared");
const { contactMode, intakeMode, setNoStore } = require("./security");

module.exports = function config(req, res) {
  setNoStore(res);
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
  const mode = intakeMode();
  const live = mode === "live";
  const reviewEmail = String(process.env.ARRP_INTAKE_REVIEW_EMAIL || "").trim();
  const contactEmail = String(process.env.ARRP_CONTACT_EMAIL || reviewEmail).trim();
  res.status(200).json({
    mode,
    turnstileSiteKey: live ? (process.env.TURNSTILE_SITE_KEY || "") : "",
    emailEnabled: live && Boolean(
      process.env.RESEND_API_KEY
      && process.env.RESEND_FROM_EMAIL
      && reviewEmail,
    ),
    contactEnabled: live && contactMode() === "live" && Boolean(
      process.env.RESEND_API_KEY
      && process.env.RESEND_FROM_EMAIL
      && contactEmail,
    ),
  });
};
