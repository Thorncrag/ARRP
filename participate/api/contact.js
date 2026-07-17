"use strict";

const crypto = require("node:crypto");
const { allowedOrigins, isAllowedOrigin, validateContact } = require("./_shared");
const { screenPrivateContact } = require("./safety");

function send(res, status, body) {
  res.status(status).json(body);
}

function applyCors(req, res) {
  const origin = req.headers.origin;
  const accepted = isAllowedOrigin(origin, allowedOrigins(process.env.ARRP_ALLOWED_ORIGINS));
  if (accepted) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    res.setHeader("Vary", "Origin");
  }
  return accepted;
}

function contactMailbox() {
  // The older name remains a deployment-compatible fallback for the current
  // private mailbox configuration. New deployments should use CONTACT_EMAIL.
  return String(process.env.ARRP_CONTACT_EMAIL || process.env.ARRP_INTAKE_REVIEW_EMAIL || "").trim();
}

function requiredConfiguration() {
  const required = ["ARRP_ALLOWED_ORIGINS", "TURNSTILE_SECRET_KEY", "RESEND_API_KEY", "RESEND_FROM_EMAIL"];
  const missing = required.filter((key) => !process.env[key]);
  if (!contactMailbox()) missing.push("ARRP_CONTACT_EMAIL");
  return missing;
}

async function verifyTurnstile(token, remoteIp) {
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
  return (await response.json()).success === true;
}

async function sendPrivateMessage(contact, contactId) {
  const context = [contact.context.proposal, contact.context.pageTitle, contact.context.pageUrl].filter(Boolean).join("\n");
  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      authorization: `Bearer ${process.env.RESEND_API_KEY}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      from: process.env.RESEND_FROM_EMAIL,
      to: [contactMailbox()],
      ...(contact.email ? { reply_to: contact.email } : {}),
      subject: `ARRP author contact: ${contact.title}`,
      text: [
        "Private message from the ARRP contact form.",
        "",
        contact.body,
        context ? `\nRegarding:\n${context}` : "",
        contact.email ? `\nReply email: ${contact.email}` : "\nNo reply email supplied.",
        `\nContact reference: ${contactId}`,
      ].filter(Boolean).join("\n"),
    }),
  });
  return response.ok;
}

module.exports = async function contact(req, res) {
  const acceptedOrigin = applyCors(req, res);
  if (req.method === "OPTIONS") {
    if (!acceptedOrigin) return send(res, 403, { error: "This request did not come from an approved ARRP page." });
    return res.status(204).end();
  }
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return send(res, 405, { error: "Method not allowed." });
  }
  if (process.env.ARRP_INTAKE_MODE !== "live") return send(res, 503, { error: "The contact service is not live yet." });
  if (requiredConfiguration().length) return send(res, 503, { error: "The private contact service is not configured." });
  if (!acceptedOrigin) return send(res, 403, { error: "This request did not come from an approved ARRP page." });
  if (!String(req.headers["content-type"] || "").toLowerCase().includes("application/json")) {
    return send(res, 415, { error: "Use the ARRP contact form to send this request." });
  }
  if (Number(req.headers["content-length"] || 0) > 12000) return send(res, 413, { error: "The message is too large." });

  const { contact: message, errors } = validateContact(req.body);
  if (message.honeypot) return send(res, 202, { received: true });
  if (errors.length) return send(res, 400, { error: errors[0] });
  if (!screenPrivateContact(message).allowed) {
    return send(res, 400, { error: "Remove financial, government-identifier, or credential information before sending this message." });
  }

  const remoteIp = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim();
  try {
    if (!await verifyTurnstile(message.turnstileToken, remoteIp)) {
      return send(res, 400, { error: "Please complete the verification check and try again." });
    }
    if (!await sendPrivateMessage(message, crypto.randomUUID())) {
      return send(res, 502, { error: "ARRP could not send your private message. Please try again later." });
    }
    return send(res, 201, { contacted: true, reply_email_provided: Boolean(message.email) });
  } catch (_) {
    // No request-derived text is written to endpoint logs.
    return send(res, 502, { error: "ARRP could not send your private message. Please try again later." });
  }
};

module.exports._test = { contactMailbox, requiredConfiguration };
