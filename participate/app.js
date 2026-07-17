(function () {
  "use strict";

  const elements = {
    form: document.querySelector("#submission-form"),
    title: document.querySelector("#submission-title"),
    body: document.querySelector("#submission-body"),
    sources: document.querySelector("#submission-sources"),
    related: document.querySelector("#submission-related"),
    email: document.querySelector("#submission-email"),
    emailConsent: document.querySelector("#submission-email-consent"),
    website: document.querySelector("#submission-website"),
    turnstile: document.querySelector("#turnstile-container"),
    status: document.querySelector("#submission-status"),
    button: document.querySelector("#submission-button"),
    context: document.querySelector("#submission-context"),
    contextTitle: document.querySelector("#submission-context-title"),
    contextLink: document.querySelector("#submission-context-link"),
    receipt: document.querySelector("#submission-receipt"),
    receiptLabel: document.querySelector("#submission-receipt-label"),
    receiptHeading: document.querySelector("#submission-receipt-heading"),
    receiptSummary: document.querySelector("#submission-receipt-summary"),
    discussionLink: document.querySelector("#submission-discussion-link"),
  };

  const submissionContext = { title: "", url: "", proposal: "" };
  const intake = { mode: "preview", turnstileWidgetId: null };
  function renderSubmissionReceipt(result) {
    const discussionUrl = result && typeof result.discussion_url === "string"
      ? result.discussion_url.trim()
      : "";
    const isLiveDiscussion = /^https:\/\/github\.com\/Thorncrag\/ARRP\/discussions\/\d+(?:[/?#]|$)/i.test(discussionUrl);

    if (isLiveDiscussion) {
      elements.receiptLabel.textContent = "Submission received";
      elements.receiptHeading.textContent = "Your submission is available in a public discussion";
      elements.receiptSummary.textContent = "Use the direct link below to follow responses and continue the conversation.";
      elements.discussionLink.href = discussionUrl;
      elements.discussionLink.textContent = result.discussion_title || "Open your submission";
      elements.status.textContent = result.email_sent
        ? "A copy of this link was sent to the address you provided."
        : "Keep this public link to follow responses.";
    } else {
      elements.receiptLabel.textContent = "Prototype response";
      elements.receiptHeading.textContent = "Your public discussion link will appear here";
      elements.receiptSummary.textContent = "This local preview did not send anything. A live submission would create one public GitHub discussion and replace the destination below with a direct link to that post.";
      elements.discussionLink.href = "https://github.com/Thorncrag/ARRP/discussions";
      elements.discussionLink.textContent = "Open ARRP Discussions (prototype destination)";
      elements.status.textContent = "";
    }

    elements.receipt.hidden = false;
    elements.receipt.focus();
  }

  function setSubmitting(submitting) {
    elements.button.disabled = submitting;
    elements.button.textContent = submitting ? "Submitting…" : intake.mode === "live" ? "Submit public input" : "Preview submission response";
  }

  function turnstileToken() {
    if (intake.mode !== "live" || intake.turnstileWidgetId === null || !window.turnstile) return "";
    return window.turnstile.getResponse(intake.turnstileWidgetId);
  }

  async function submitToIntake(payload) {
    const response = await fetch(intakeEndpoint("submit"), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.error || "ARRP could not receive the submission. Please try again later.");
    return result;
  }

  function intakeEndpoint(path) {
    const configured = String(window.ARRP_INTAKE_ENDPOINT || "").trim().replace(/\/$/, "");
    return configured ? `${configured}/api/${path}` : `/api/${path}`;
  }

  async function screenSubmission(event) {
    event.preventDefault();
    const title = elements.title.value.trim();
    const body = elements.body.value.trim();
    const sources = elements.sources.value.trim();
    const related = elements.related.value.trim();
    if (intake.mode !== "live") {
      renderSubmissionReceipt({});
      return;
    }
    if (!turnstileToken()) {
      elements.status.textContent = "Complete the verification check before submitting.";
      elements.status.focus();
      return;
    }

    elements.status.textContent = "Creating your public discussion…";
    setSubmitting(true);
    try {
      const result = await submitToIntake({
        title,
        body,
        sources,
        related,
        email: elements.email.value.trim(),
        emailConsent: elements.emailConsent.checked,
        website: elements.website.value,
        turnstileToken: turnstileToken(),
        context: {
          proposal: submissionContext.proposal,
          pageTitle: submissionContext.title,
          pageUrl: submissionContext.url,
        },
      });
      renderSubmissionReceipt(result);
    } catch (error) {
      elements.status.textContent = error.message;
      if (window.turnstile && intake.turnstileWidgetId !== null) window.turnstile.reset(intake.turnstileWidgetId);
    } finally {
      setSubmitting(false);
    }
  }

  function loadTurnstile(siteKey) {
    if (!siteKey) {
      elements.status.textContent = "The submission service is not ready yet.";
      return;
    }
    const script = document.createElement("script");
    script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
    script.async = true;
    script.defer = true;
    script.onload = () => {
      intake.turnstileWidgetId = window.turnstile.render(elements.turnstile, { sitekey: siteKey });
    };
    script.onerror = () => { elements.status.textContent = "The verification check could not load. Please refresh and try again."; };
    document.head.append(script);
  }

  async function initializeIntake() {
    if (!/^https?:$/i.test(window.location.protocol)) return;
    try {
      const response = await fetch(intakeEndpoint("config"), { cache: "no-store" });
      const config = await response.json();
      if (!response.ok || config.mode !== "live") return;
      intake.mode = "live";
      setSubmitting(false);
      document.querySelector(".prototype-label").textContent = "Public input";
      document.querySelector(".prototype-boundary").hidden = true;
      loadTurnstile(config.turnstileSiteKey);
    } catch (_) {
      // A local file preview and a GitHub Pages copy deliberately stay in preview mode.
    }
  }

  function initializeContext() {
    const params = new URLSearchParams(window.location.search);
    submissionContext.title = params.get("page_title")?.trim() || "";
    submissionContext.url = params.get("page")?.trim() || "";
    submissionContext.proposal = params.get("proposal")?.trim().toLocaleUpperCase() || "";
    if (!submissionContext.title && !submissionContext.url && !submissionContext.proposal) return;

    const label = [submissionContext.proposal, submissionContext.title].filter(Boolean).join(" — ");
    elements.contextTitle.textContent = label || submissionContext.url;
    elements.related.value = submissionContext.proposal || submissionContext.url;
    const linkTarget = submissionContext.url;
    if (linkTarget) elements.contextLink.href = linkTarget;
    else elements.contextLink.hidden = true;
    elements.context.hidden = false;
  }

  elements.form.addEventListener("submit", screenSubmission);
  initializeContext();
  initializeIntake();
})();
