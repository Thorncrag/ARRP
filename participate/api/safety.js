"use strict";

// This is a deliberately narrow pre-publication privacy screen. It is not a
// substitute for human judgment or a semantic moderation service. It returns
// categories only so callers never need to retain or log matched material.

const EMAIL = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i;
const PHONE = /(?<!\d)(?:\+?\d{1,3}[ .-]?)?(?:\(?\d{3}\)?[ .-]?)\d{3}[ .-]?\d{4}(?!\d)/;
const SSN = /(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)/;
const SECRET = /-----BEGIN [A-Z ]*PRIVATE KEY-----|\b(?:ghp|github_pat|sk|rk|xox[baprs])[-_A-Za-z0-9]{16,}\b|\bauthorization\s*:\s*bearer\s+\S+/i;

function luhnValid(digits) {
  let total = 0;
  let doubleDigit = false;
  for (let index = digits.length - 1; index >= 0; index -= 1) {
    let value = Number(digits[index]);
    if (doubleDigit) value = value > 4 ? value * 2 - 9 : value * 2;
    total += value;
    doubleDigit = !doubleDigit;
  }
  return total % 10 === 0;
}

function containsPaymentCard(value) {
  const candidates = String(value || "").match(/(?:\d[ -]?){13,19}/g) || [];
  return candidates.some((candidate) => {
    const digits = candidate.replace(/\D/g, "");
    return digits.length >= 13 && digits.length <= 19 && luhnValid(digits);
  });
}

function publicText(submission) {
  return [
    submission?.title,
    submission?.body,
    submission?.sources,
    submission?.related,
    submission?.context?.proposal,
    submission?.context?.pageTitle,
    submission?.context?.pageUrl,
  ]
    .filter((value) => typeof value === "string")
    .join("\n");
}

function screenPublicSubmission(submission) {
  const value = publicText(submission);
  const findings = [];
  if (EMAIL.test(value)) findings.push("email_address");
  if (PHONE.test(value)) findings.push("phone_number");
  if (SSN.test(value)) findings.push("government_identifier");
  if (containsPaymentCard(value)) findings.push("payment_card");
  if (SECRET.test(value)) findings.push("credential");
  return { allowed: findings.length === 0, findings };
}

function screenPrivateContact(contact) {
  const value = [contact?.title, contact?.body].filter((item) => typeof item === "string").join("\n");
  const findings = [];
  if (SSN.test(value)) findings.push("government_identifier");
  if (containsPaymentCard(value)) findings.push("payment_card");
  if (SECRET.test(value)) findings.push("credential");
  return { allowed: findings.length === 0, findings };
}

module.exports = { containsPaymentCard, screenPrivateContact, screenPublicSubmission };
