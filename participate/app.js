(function () {
  "use strict";

  const elements = {
    form: document.querySelector("#submission-form"),
    routes: [...document.querySelectorAll('input[name="route"]')],
    title: document.querySelector("#submission-title"),
    titleLabel: document.querySelector("#submission-title-label"),
    body: document.querySelector("#submission-body"),
    bodyLabel: document.querySelector("#submission-body-label"),
    sources: document.querySelector("#submission-sources"),
    sourcesField: document.querySelector("#submission-sources-field"),
    related: document.querySelector("#submission-related"),
    relatedField: document.querySelector("#submission-related-field"),
    emailFollowup: document.querySelector("#email-followup-fields"),
    email: document.querySelector("#submission-email"),
    emailLabel: document.querySelector("#submission-email-label"),
    emailConsent: document.querySelector("#submission-email-consent"),
    emailConsentField: document.querySelector("#submission-email-consent-field"),
    website: document.querySelector("#submission-website"),
    notice: document.querySelector("#submission-notice"),
    noticeTitle: document.querySelector("#submission-notice-title"),
    noticeBody: document.querySelector("#submission-notice-body"),
    noticeDetail: document.querySelector("#submission-notice-detail"),
    privacyNote: document.querySelector("#submission-privacy-note"),
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
    discussionRow: document.querySelector("#submission-discussion-row"),
    discussionLink: document.querySelector("#submission-discussion-link"),
    followUpNote: document.querySelector("#submission-follow-up-note"),
  };

  const submissionContext = { title: "", url: "", proposal: "" };
  const intake = { mode: "preview", route: "input", turnstileWidgetId: null, emailEnabled: true, contactEnabled: true };

  function isContactRoute() {
    return intake.route === "contact";
  }

  function setEmailFields() {
    const visible = isContactRoute() || intake.emailEnabled;
    elements.emailFollowup.hidden = !visible;
    elements.email.disabled = !visible;
    elements.emailConsentField.hidden = isContactRoute() || !visible;
    elements.emailConsent.disabled = isContactRoute() || !visible;
    if (isContactRoute()) elements.emailConsent.checked = false;
  }

  function setRoute(route) {
    intake.route = route === "contact" ? "contact" : "input";
    elements.routes.forEach((input) => {
      const selected = input.value === intake.route;
      input.checked = selected;
      input.closest(".route-option")?.classList.toggle("is-selected", selected);
    });
    const contact = isContactRoute();
    elements.sourcesField.hidden = contact;
    elements.relatedField.hidden = contact;
    elements.titleLabel.textContent = contact ? "Subject" : "Short title";
    elements.title.placeholder = contact ? "What would you like to discuss?" : "What should ARRP look at?";
    elements.bodyLabel.textContent = contact ? "Message for the author" : "What should ARRP consider?";
    elements.body.placeholder = contact
      ? "Write your private message. Do not include sensitive information."
      : "Explain the event, concern, possible defect, correction, question, or offer to help. Ordinary language is fine.";
    elements.notice.classList.toggle("private-submission-notice", contact);
    elements.noticeTitle.textContent = contact ? "Your message will be private." : "Your submission will be public.";
    elements.noticeBody.textContent = contact
      ? "ARRP will send this message only to the project author. It will not create a GitHub Discussion or other public post. Do not include financial, government-identifier, credential, medical, or other sensitive information."
      : "ARRP will post it in a public GitHub Discussion. Do not include private, sensitive, or identifying information—such as an address, phone number, government identifier, medical or financial information, or anyone else's personal details.";
    elements.noticeDetail.textContent = contact
      ? "A reply email is optional. If you provide one, it is sent only to the author so they can reply to you."
      : "The optional email field is used only for private ARRP follow-up and is not included in the public post.";
    elements.emailLabel.textContent = contact
      ? "Email for a reply (optional)"
      : "Email for possible private follow-up (optional)";
    elements.privacyNote.textContent = contact
      ? "Private message: it is sent to the author and is not posted publicly. Do not include sensitive information."
      : "Public post: do not include personal or sensitive information. Optional email is private, is not posted to GitHub, and is used only for follow-up about this submission.";
    setEmailFields();
    setSubmitting(false);
  }

  function renderReceipt(result) {
    const discussionUrl = typeof result?.discussion_url === "string" ? result.discussion_url.trim() : "";
    const submissionUrl = typeof result?.submission_url === "string" ? result.submission_url.trim() : discussionUrl;
    const isLiveDiscussion = /^https:\/\/github\.com\/Thorncrag\/ARRP\/discussions\/\d+(?:[/?#]|$)/i.test(discussionUrl);
    const privateContact = result?.contacted === true;

    elements.discussionRow.hidden = privateContact;
    elements.followUpNote.hidden = privateContact;
    if (privateContact) {
      elements.receiptLabel.textContent = "Private message sent";
      elements.receiptHeading.textContent = "Your message was sent privately to the author";
      elements.receiptSummary.textContent = "No public post or GitHub Discussion was created.";
      elements.status.textContent = result.reply_email_provided
        ? "Your reply email was sent privately to the author."
        : "No reply email was provided.";
    } else if (isLiveDiscussion) {
      elements.receiptLabel.textContent = "Submission received";
      elements.receiptHeading.textContent = "Your submission is available in a public discussion";
      elements.receiptSummary.textContent = result.route_label
        ? `It was added to the discussion for ${result.route_label}. Use the direct link below to follow responses.`
        : "Use the direct link below to follow responses and continue the conversation.";
      elements.discussionRow.hidden = false;
      elements.followUpNote.hidden = false;
      elements.discussionLink.href = submissionUrl;
      elements.discussionLink.textContent = "Open your submission";
      elements.status.textContent = result.follow_up_requested
        ? "Your email was provided for private ARRP follow-up and was not posted publicly. Keep this public link to follow responses."
        : "Keep this public link to follow responses.";
    } else if (isContactRoute()) {
      elements.receiptLabel.textContent = "Prototype response";
      elements.receiptHeading.textContent = "Your private-message receipt will appear here";
      elements.receiptSummary.textContent = "This local preview did not send anything. A live author-contact message would be sent privately and create no public post.";
    } else {
      elements.receiptLabel.textContent = "Prototype response";
      elements.receiptHeading.textContent = "Your public discussion link will appear here";
      elements.receiptSummary.textContent = "This local preview did not send anything. A live submission would appear in the matching public ARRP discussion and place its direct link here.";
      elements.discussionRow.hidden = false;
      elements.followUpNote.hidden = false;
      elements.discussionLink.href = "https://github.com/Thorncrag/ARRP/discussions";
      elements.discussionLink.textContent = "Open ARRP Discussions (prototype destination)";
    }
    elements.receipt.hidden = false;
    elements.receipt.focus();
  }

  function setSubmitting(submitting) {
    if (intake.mode === "paused") {
      elements.button.disabled = true;
      elements.button.textContent = "Intake temporarily unavailable";
      return;
    }
    elements.button.disabled = submitting;
    if (submitting) elements.button.textContent = isContactRoute() ? "Sending private message…" : "Submitting public input…";
    else if (intake.mode === "live") elements.button.textContent = isContactRoute() ? "Send private message" : "Submit public input";
    else elements.button.textContent = isContactRoute() ? "Preview private-message response" : "Preview public-input response";
  }

  function turnstileToken() {
    if (intake.mode !== "live" || intake.turnstileWidgetId === null || !window.turnstile) return "";
    return window.turnstile.getResponse(intake.turnstileWidgetId);
  }

  function intakeEndpoint(path) {
    const configured = String(window.ARRP_INTAKE_ENDPOINT || "").trim().replace(/\/$/, "");
    return configured ? `${configured}/api/${path}` : `/api/${path}`;
  }

  function sanitizeContextUrl(value) {
    return window.ARRP_CONTEXT_URLS?.sanitizeContextUrl(value) || "";
  }

  async function sendRequest(path, payload) {
    // Public input continues through intakeEndpoint("submit"); private author
    // contact uses the separate endpoint so it can never create a Discussion.
    const response = await fetch(intakeEndpoint(path), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.error || "ARRP could not receive the request. Please try again later.");
    return result;
  }

  async function screenSubmission(event) {
    event.preventDefault();
    // This form preserves public input; the full ARRP admission test remains a
    // separate human-review step after a public Discussion is created.
    if (intake.mode === "paused") {
      elements.status.textContent = "This intake service is temporarily unavailable. Please try again later.";
      elements.status.focus();
      return;
    }
    if (intake.mode !== "live") return renderReceipt({});
    if (isContactRoute() && !intake.contactEnabled) {
      elements.status.textContent = "Private author contact is temporarily unavailable.";
      return;
    }
    if (!isContactRoute() && !turnstileToken()) {
      elements.status.textContent = "Complete the verification check before submitting.";
      elements.status.focus();
      return;
    }
    if (isContactRoute() && !turnstileToken()) {
      elements.status.textContent = "Complete the verification check before sending your message.";
      elements.status.focus();
      return;
    }
    const payload = {
      title: elements.title.value.trim(),
      body: elements.body.value.trim(),
      email: elements.email.value.trim(),
      website: elements.website.value,
      turnstileToken: turnstileToken(),
      context: { proposal: submissionContext.proposal, pageTitle: submissionContext.title, pageUrl: submissionContext.url },
    };
    if (!isContactRoute()) {
      payload.sources = elements.sources.value.trim();
      payload.related = elements.related.value.trim();
      payload.emailConsent = elements.emailConsent.checked;
    }
    elements.status.textContent = isContactRoute() ? "Sending your private message…" : "Creating your public discussion…";
    setSubmitting(true);
    try {
      renderReceipt(await sendRequest(isContactRoute() ? "contact" : "submit", payload));
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
      intake.turnstileWidgetId = window.turnstile.render(elements.turnstile, {
        sitekey: siteKey,
        action: "arrp_public_intake",
      });
    };
    script.onerror = () => { elements.status.textContent = "The verification check could not load. Please refresh and try again."; };
    document.head.append(script);
  }

  async function initializeIntake() {
    if (!/^https?:$/i.test(window.location.protocol)) return;
    try {
      const response = await fetch(intakeEndpoint("config"), { cache: "no-store" });
      const config = await response.json();
      if (!response.ok || (config.mode !== "live" && config.mode !== "paused")) return;
      intake.mode = config.mode;
      intake.emailEnabled = Boolean(config.emailEnabled);
      intake.contactEnabled = Boolean(config.contactEnabled);
      document.querySelector(".prototype-label").textContent = "Public interaction";
      document.querySelector(".prototype-boundary").hidden = true;
      setRoute(intake.route);
      if (intake.mode === "paused") {
        elements.status.textContent = "This intake service is temporarily unavailable. Please try again later.";
        return;
      }
      loadTurnstile(config.turnstileSiteKey);
    } catch (_) {
      // Local file previews deliberately remain non-transmitting.
    }
  }

  function initializeContext() {
    const params = new URLSearchParams(window.location.search);
    submissionContext.title = params.get("page_title")?.trim() || "";
    submissionContext.url = sanitizeContextUrl(params.get("page"));
    submissionContext.proposal = params.get("proposal")?.trim().toLocaleUpperCase() || "";
    const requestedRoute = params.get("mode")?.trim().toLowerCase();
    if (requestedRoute === "contact") setRoute("contact");
    const subject = params.get("subject")?.trim();
    if (subject && !elements.title.value) elements.title.value = subject.slice(0, 140);
    if (!submissionContext.title && !submissionContext.url && !submissionContext.proposal) return;
    const label = [submissionContext.proposal, submissionContext.title].filter(Boolean).join(" — ");
    elements.contextTitle.textContent = label || submissionContext.url;
    if (!isContactRoute()) elements.related.value = submissionContext.proposal || submissionContext.url;
    if (submissionContext.url) elements.contextLink.href = submissionContext.url;
    else elements.contextLink.hidden = true;
    elements.context.hidden = false;
  }

  elements.form.addEventListener("submit", screenSubmission);
  elements.routes.forEach((input) => input.addEventListener("change", () => setRoute(input.value)));
  setRoute("input");
  initializeContext();
  initializeIntake();
})();
