(function () {
  "use strict";

  const data = window.ARRP_PARTICIPATION_DATA;
  if (!data || !Array.isArray(data.proposal_index) || !Array.isArray(data.horizon_index)) {
    document.body.innerHTML = "<p class=\"load-error\">Input-screening data could not be loaded. Rebuild the prototype data bundle.</p>";
    return;
  }

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
    screeningEmpty: document.querySelector("#screening-empty"),
    screeningResult: document.querySelector("#screening-result"),
    screeningBadges: document.querySelector("#screening-badges"),
    receipt: document.querySelector("#submission-receipt"),
    receiptLabel: document.querySelector("#submission-receipt-label"),
    receiptHeading: document.querySelector("#submission-receipt-heading"),
    receiptSummary: document.querySelector("#submission-receipt-summary"),
    discussionLink: document.querySelector("#submission-discussion-link"),
  };

  const submissionContext = { title: "", url: "", proposal: "" };
  const intake = { mode: "preview", turnstileWidgetId: null };
  const STOPWORDS = new Set([
    "about", "after", "again", "against", "also", "and", "any", "are", "arrp", "because", "been",
    "before", "being", "between", "both", "but", "can", "could", "does", "federal", "for", "from",
    "government", "has", "have", "into", "issue", "law", "may", "more", "not", "official", "page",
    "president", "proposal", "should", "that", "the", "their", "there", "these", "they", "this", "through",
    "under", "was", "were", "what", "when", "where", "which", "with", "would",
  ]);

  const AREA_KEYWORDS = {
    APPT: ["appointment", "nomination", "confirmation", "vacancy", "acting", "appointee", "qualification"],
    CIV: ["civil service", "career employee", "federal workforce", "schedule f", "personnel"],
    CLASS: ["classified", "classification", "clearance", "national secret"],
    CONG: ["congress", "subpoena", "contempt", "committee", "legislative oversight"],
    DOJ: ["justice department", "prosecution", "prosecutor", "attorney general", "fbi", "criminal investigation"],
    DOM: ["homeland security", "ice", "secret service", "federal agent", "domestic deployment"],
    ELEC: ["election", "voting", "ballot", "campaign finance", "redistricting", "gerrymandering"],
    EMERG: ["emergency", "ieepa", "emergency power", "sanction"],
    EMOL: ["emolument", "self-dealing", "financial conflict", "foreign gift", "private benefit"],
    FACT: ["government data", "scientific integrity", "official statistics", "factual record"],
    FED: ["federalism", "state government", "state funding", "sanctuary", "anti-commandeering"],
    FRB: ["federal reserve", "central bank", "monetary policy"],
    FUND: ["appropriation", "impoundment", "withhold funding", "congressional spending", "grant condition"],
    HER: ["national monument", "antiquities", "historic preservation", "tribal land", "national park"],
    IMM: ["immigration", "asylum", "deportation", "noncitizen", "migrant"],
    JUD: ["court", "judge", "judicial", "jurisdiction", "standing", "injunction", "court order"],
    OVS: ["inspector general", "whistleblower", "oversight", "audit", "watchdog"],
    PAR: ["pardon", "clemency", "commutation"],
    PRESS: ["press", "journalist", "news media", "reporter"],
    REC: ["records", "archives", "presidential records", "recordkeeping"],
    REG: ["agency", "regulation", "administrative", "rulemaking", "regulatory"],
    RET: ["retaliation", "retaliatory", "reprisal"],
    RIGHTS: ["civil rights", "due process", "equal protection", "constitutional rights", "discrimination"],
    WAR: ["military", "war powers", "armed force", "national guard", "hostilities"],
  };

  function tokens(value) {
    return new Set(
      String(value || "")
        .toLocaleLowerCase()
        .replace(/[^a-z0-9]+/g, " ")
        .split(/\s+/)
        .filter((token) => token.length > 2 && !STOPWORDS.has(token))
    );
  }

  function candidates() {
    return [
      ...data.proposal_index.map((record) => ({ ...record, kind: "proposal" })),
      ...data.horizon_index.map((record) => ({ ...record, kind: "horizon" })),
    ];
  }

  function classify(text) {
    if (/\b(offer|volunteer|available|willing)\b.{0,45}\b(review|reviewer|expertise|attorney|professional)\b|\bpeer review\b/i.test(text)) return "Offer to review";
    if (/\b(error|incorrect|inaccurate|correction|typo|broken link|feedback|drafting suggestion)\b/i.test(text)) return "Feedback or correction";
    if (/\b(source suggestion|suggest(?:ing)? (?:a |this )?(?:source|article|case|report)|additional source|supporting source)\b/i.test(text)) return "Source suggestion";
    if (/\b(question|can you explain|could you explain|how does|why does|what does)\b/i.test(text)) return "General question";
    return "New issue or proposal idea";
  }

  function matchSubmission(text, related) {
    const records = candidates();
    const explicit = `${related} ${text}`.toLocaleUpperCase().match(/\b(?:[A-Z]{2,8}|HOR)-\d{3}\b/);
    if (explicit) {
      const record = records.find((item) => item.id === explicit[0]);
      if (record) return { record, explicit: true };
    }

    const normalizedRelated = related.toLocaleLowerCase();
    const relatedRecord = records.find((item) => normalizedRelated && (
      normalizedRelated.includes(item.id.toLocaleLowerCase())
      || (item.issue_url && normalizedRelated.includes(item.issue_url.toLocaleLowerCase()))
      || (item.canonical_page && normalizedRelated.includes(item.canonical_page.toLocaleLowerCase()))
    ));
    if (relatedRecord) return { record: relatedRecord, explicit: true };

    const inputTokens = tokens(text);
    let best = { record: null, score: 0, explicit: false };
    records.forEach((record) => {
      const titleTokens = tokens(record.title);
      const overlap = [...titleTokens].filter((token) => inputTokens.has(token)).length;
      if (!overlap) return;
      const score = overlap / Math.max(2, Math.sqrt(titleTokens.size * Math.max(2, inputTokens.size)));
      if (score > best.score) best = { record, score, explicit: false };
    });
    return best.score >= 0.24 ? best : { record: null, score: best.score, explicit: false };
  }

  function inferArea(text, match) {
    if (match.record?.area && match.record.area !== "Horizon") return match.record.area;
    const normalized = text.toLocaleLowerCase();
    let bestArea = "Unassigned pending agent research";
    let bestScore = 0;
    Object.entries(AREA_KEYWORDS).forEach(([area, phrases]) => {
      const score = phrases.reduce((total, phrase) => total + (normalized.includes(phrase) ? phrase.split(" ").length : 0), 0);
      if (score > bestScore) {
        bestArea = area;
        bestScore = score;
      }
    });
    return bestArea;
  }

  function routeFor(type, match, area) {
    const id = match.record?.id;
    if (type === "Offer to review") return id ? `Associate the offer with ${id}; verify the reviewer's relevant scope before recording external review.` : "Identify the relevant proposal, then route the offer without creating a new proposal record.";
    if (type === "Feedback or correction") return id ? `Route to ${id}; assess whether it is a correction, material revision, or non-substantive comment.` : "Identify the affected page, then route the feedback to its existing proposal record.";
    if (type === "Source suggestion") return id ? `Verify the source and route it to ${id} using the ordinary qualitative evidence-placement rules.` : "Verify the source, identify its project relevance, and place it in the unified Sources workflow if work remains.";
    if (type === "General question") return id ? `Answer in the public discussion and link ${id}; create no project work unless the exchange exposes a distinct defect.` : "Answer in the public discussion; create project work only if screening exposes a distinct institutional question.";
    if (id) return `Compare the submission with ${id}; use the full admission test only for a genuinely distinct institutional weakness.`;
    return `Run the full ARRP admission test and provisionally evaluate ${area} as the receiving area.`;
  }

  function makeBadge(label) {
    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = label;
    return badge;
  }

  function renderRelated(record) {
    const target = document.querySelector("#screening-related");
    target.replaceChildren();
    if (!record) {
      target.textContent = "No likely existing record identified by the prototype";
      return;
    }
    const link = document.createElement("a");
    link.href = record.canonical_page || record.issue_url;
    link.textContent = `${record.id} — ${record.title}`;
    if (/^https?:/i.test(link.href)) {
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    }
    target.append(link);
  }

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
    elements.button.textContent = submitting ? "Submitting…" : intake.mode === "live" ? "Submit public input" : "Preview response and screening";
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
    const text = [title, body, sources, related, submissionContext.title, submissionContext.proposal].filter(Boolean).join(" ");
    const type = classify(text);
    const match = matchSubmission(text, related);
    const area = inferArea(text, match);
    const duplicate = match.record
      ? `${match.explicit ? "Submission is explicitly connected to" : "Possible substantive overlap with"} ${match.record.id}; a live agent should also compare open public submissions.`
      : "No likely project overlap found by this preview; a live agent would also compare open public submissions.";

    elements.screeningBadges.replaceChildren(makeBadge(type), makeBadge(area), ...(match.record ? [makeBadge(match.record.id)] : []));
    document.querySelector("#screening-type").textContent = type;
    document.querySelector("#screening-area").textContent = area;
    renderRelated(match.record);
    document.querySelector("#screening-duplicate").textContent = duplicate;
    document.querySelector("#screening-route").textContent = routeFor(type, match, area);
    document.querySelector("#screening-attention").textContent = "None until agent screening is complete; you decide only if a new issue or material project change remains.";
    elements.screeningEmpty.hidden = true;
    elements.screeningResult.hidden = false;

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

    const candidate = candidates().find((record) => record.id === submissionContext.proposal);
    const label = [submissionContext.proposal, submissionContext.title || candidate?.title].filter(Boolean).join(" — ");
    elements.contextTitle.textContent = label || submissionContext.url;
    elements.related.value = submissionContext.proposal || submissionContext.url;
    const linkTarget = submissionContext.url || candidate?.canonical_page || candidate?.issue_url;
    if (linkTarget) elements.contextLink.href = linkTarget;
    else elements.contextLink.hidden = true;
    elements.context.hidden = false;
  }

  elements.form.addEventListener("submit", screenSubmission);
  initializeContext();
  initializeIntake();
})();
