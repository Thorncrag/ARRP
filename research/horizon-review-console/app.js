(function () {
  "use strict";

  const data = window.ARRP_HORIZON_REVIEW_DATA;
  if (!data || !Array.isArray(data.records)) {
    document.body.innerHTML = "<p>Review data could not be loaded. Rebuild the console data bundle.</p>";
    return;
  }

  const STORAGE_KEY = "arrp-horizon-review-decisions-v1";
  const PREFERENCES_KEY = "arrp-horizon-review-preferences-v1";
  const recordsById = new Map(data.records.map((record) => [record.id, record]));
  const state = {
    queue: "candidates",
    index: 0,
    search: "",
    decisionFilter: "unreviewed",
    term: "all",
    source: "all",
    decisions: loadJson(STORAGE_KEY, {}),
    preferences: loadJson(PREFERENCES_KEY, { autoAdvance: true }),
    filtered: [],
  };

  const elements = {
    reviewedCount: document.querySelector("#reviewed-count"),
    queueCount: document.querySelector("#queue-count"),
    queueDescription: document.querySelector("#queue-description"),
    progressFill: document.querySelector("#progress-fill"),
    yesCount: document.querySelector("#yes-count"),
    noCount: document.querySelector("#no-count"),
    deferCount: document.querySelector("#defer-count"),
    recordPosition: document.querySelector("#record-position"),
    recordContent: document.querySelector("#record-content"),
    emptyState: document.querySelector("#empty-state"),
    decisionBar: document.querySelector("#decision-bar"),
    recordBadges: document.querySelector("#record-badges"),
    recordId: document.querySelector("#record-id"),
    recordTitle: document.querySelector("#record-title"),
    reviewPrompt: document.querySelector("#review-prompt"),
    recordSummary: document.querySelector("#record-summary"),
    expandSummary: document.querySelector("#expand-summary"),
    recordDetails: document.querySelector("#record-details"),
    sourceLinks: document.querySelector("#source-links"),
    reviewerNotes: document.querySelector("#reviewer-notes"),
    search: document.querySelector("#search-input"),
    decisionFilter: document.querySelector("#decision-filter"),
    termFilter: document.querySelector("#term-filter"),
    sourceFilter: document.querySelector("#source-filter"),
    autoAdvance: document.querySelector("#auto-advance"),
    previous: document.querySelector("#previous-button"),
    next: document.querySelector("#next-button"),
    toast: document.querySelector("#toast"),
  };

  let toastTimer;
  let noteTimer;

  function loadJson(key, fallback) {
    try {
      const value = window.localStorage.getItem(key);
      return value ? JSON.parse(value) : fallback;
    } catch (_error) {
      return fallback;
    }
  }

  function saveDecisions() {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state.decisions));
    } catch (_error) {
      showToast("Browser storage is unavailable. Export decisions before closing this page.");
    }
  }

  function savePreferences() {
    try {
      window.localStorage.setItem(PREFERENCES_KEY, JSON.stringify(state.preferences));
    } catch (_error) {
      // Preferences are optional; decision exports remain available.
    }
  }

  function queueRecords(queue) {
    switch (queue) {
      case "candidates":
        return data.records.filter((record) => record.kind === "candidate_question");
      case "media":
        return data.records.filter((record) => record.kind === "media_episode");
      case "priority":
        return data.records.filter((record) => record.kind === "source_record" && record.priority);
      case "monitor":
        return data.records.filter(
          (record) => record.kind === "source_record" && String(record.screening).startsWith("monitor-")
        );
      default:
        return data.records.filter((record) => record.kind === "source_record");
    }
  }

  function matchesFilters(record) {
    const saved = state.decisions[record.id] || {};
    if (state.decisionFilter === "unreviewed" && saved.decision) return false;
    if (["yes", "no", "defer"].includes(state.decisionFilter) && saved.decision !== state.decisionFilter) {
      return false;
    }
    if (state.term !== "all" && String(record.term) !== state.term) return false;
    if (state.source !== "all" && record.source_family !== state.source) return false;
    if (!state.search) return true;

    const haystack = [
      record.id,
      record.title,
      record.category,
      record.summary,
      record.actor,
      record.posture,
      record.source_family,
      record.routes,
      record.representative_case,
      saved.note,
    ]
      .filter(Boolean)
      .join(" ")
      .toLocaleLowerCase();
    return haystack.includes(state.search.toLocaleLowerCase());
  }

  function currentRecord() {
    return state.filtered[state.index] || null;
  }

  function humanize(value) {
    if (!value) return "—";
    return String(value)
      .replaceAll("-", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function termLabel(term) {
    if (String(term) === "1") return "First Trump term";
    if (String(term) === "2") return "Second Trump term";
    return "Both terms";
  }

  function decisionLabel(value) {
    return { yes: "Yes — advance", no: "No — do not advance", defer: "Deferred" }[value] || "Unreviewed";
  }

  function makeBadge(text, className) {
    const span = document.createElement("span");
    span.className = `badge ${className || ""}`.trim();
    span.textContent = text;
    return span;
  }

  function detail(label, value) {
    if (!value) return null;
    const wrapper = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    wrapper.append(term, description);
    return wrapper;
  }

  function renderRecord(record) {
    if (!record) {
      elements.recordContent.hidden = true;
      elements.emptyState.hidden = false;
      elements.decisionBar.hidden = true;
      elements.recordPosition.textContent = "No matching records";
      elements.previous.disabled = true;
      elements.next.disabled = true;
      return;
    }

    const saved = state.decisions[record.id] || {};
    elements.recordContent.hidden = false;
    elements.emptyState.hidden = true;
    elements.decisionBar.hidden = false;
    elements.recordPosition.textContent = `Record ${state.index + 1} of ${state.filtered.length}`;
    elements.previous.disabled = state.index === 0;
    elements.next.disabled = state.index >= state.filtered.length - 1;

    elements.recordBadges.replaceChildren();
    const kindLabel =
      record.kind === "candidate_question"
        ? "Preliminary issue candidate"
        : record.kind === "media_episode"
          ? "Media-supported episode"
          : humanize(record.category);
    elements.recordBadges.append(
      makeBadge(kindLabel),
      makeBadge(termLabel(record.term))
    );
    if (record.priority && record.kind === "source_record") {
      elements.recordBadges.append(makeBadge("Priority disposition", "priority"));
    }
    if (record.kind === "media_episode") {
      const primaryLabel = String(record.normalization).startsWith("verified")
        ? "Primary record verified"
        : "Primary record follow-up";
      elements.recordBadges.append(makeBadge(primaryLabel, String(record.normalization).startsWith("verified") ? "yes" : "defer"));
    }
    if (saved.decision) {
      elements.recordBadges.append(makeBadge(decisionLabel(saved.decision), saved.decision));
    }

    elements.recordId.textContent = record.id;
    elements.recordTitle.textContent = record.title;
    elements.reviewPrompt.textContent = record.review_prompt;
    elements.recordSummary.textContent = record.summary || "No summary is available.";
    elements.recordSummary.classList.remove("expanded");
    elements.expandSummary.textContent = "Show full summary";
    elements.expandSummary.hidden = String(record.summary || "").length < 900;

    const details = [
      detail("Review posture", humanize(record.screening)),
      detail("Litigation status", record.posture),
      detail("Likely ARRP routes", record.routes),
      detail("Responsible actor or category", record.actor),
      detail("Action period", record.period),
      detail("Source family", record.source_family),
      detail("Coverage status", humanize(record.coverage)),
      detail("Normalization", record.normalization),
      detail("Representative case", record.representative_case),
    ].filter(Boolean);
    elements.recordDetails.replaceChildren(...details);

    elements.sourceLinks.replaceChildren();
    (record.links || []).forEach((item) => {
      const anchor = document.createElement("a");
      anchor.href = item.url;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.textContent = item.label;
      elements.sourceLinks.append(anchor);
    });
    if (!record.links || !record.links.length) {
      const noLinks = document.createElement("span");
      noLinks.className = "eyebrow";
      noLinks.textContent = "No direct external link recorded; consult the intake analysis.";
      elements.sourceLinks.append(noLinks);
    }

    elements.reviewerNotes.value = saved.note || "";
    document.querySelectorAll(".decision-button").forEach((button) => button.removeAttribute("aria-pressed"));
    if (saved.decision) {
      document.querySelector(`#decision-${saved.decision}`).setAttribute("aria-pressed", "true");
    }
  }

  function renderProgress(baseRecords) {
    const counts = { yes: 0, no: 0, defer: 0 };
    baseRecords.forEach((record) => {
      const value = state.decisions[record.id]?.decision;
      if (counts[value] !== undefined) counts[value] += 1;
    });
    const reviewed = counts.yes + counts.no + counts.defer;
    const percent = baseRecords.length ? (reviewed / baseRecords.length) * 100 : 0;
    elements.reviewedCount.textContent = reviewed.toLocaleString();
    elements.queueCount.textContent = baseRecords.length.toLocaleString();
    elements.queueDescription.textContent = "records reviewed in this queue";
    elements.progressFill.style.width = `${percent}%`;
    elements.yesCount.textContent = counts.yes.toLocaleString();
    elements.noCount.textContent = counts.no.toLocaleString();
    elements.deferCount.textContent = counts.defer.toLocaleString();
  }

  function refresh(options) {
    const settings = options || {};
    const previousId = settings.keepId ? currentRecord()?.id : null;
    const base = queueRecords(state.queue);
    state.filtered = base.filter(matchesFilters);
    if (previousId) {
      const newIndex = state.filtered.findIndex((record) => record.id === previousId);
      state.index = newIndex >= 0 ? newIndex : Math.min(state.index, Math.max(0, state.filtered.length - 1));
    } else {
      state.index = Math.min(state.index, Math.max(0, state.filtered.length - 1));
    }
    renderProgress(base);
    renderRecord(currentRecord());
  }

  function chooseQueue(queue) {
    state.queue = queue;
    state.index = 0;
    document.querySelectorAll("[data-queue]").forEach((button) => {
      button.classList.toggle("active", button.dataset.queue === queue);
    });
    populateSourceFilter();
    refresh();
  }

  function setDecision(value) {
    const record = currentRecord();
    if (!record) return;
    const existing = state.decisions[record.id] || {};
    state.decisions[record.id] = {
      decision: value,
      note: elements.reviewerNotes.value.trim(),
      reviewed_at: new Date().toISOString(),
      record_kind: record.kind,
      title: record.title,
    };
    saveDecisions();
    showToast(`${record.id} marked ${decisionLabel(value)}.`);

    if (state.preferences.autoAdvance && state.decisionFilter === "unreviewed") {
      refresh();
    } else if (state.preferences.autoAdvance && state.index < state.filtered.length - 1) {
      state.index += 1;
      refresh();
    } else {
      refresh({ keepId: true });
    }
  }

  function saveNote() {
    const record = currentRecord();
    if (!record) return;
    const note = elements.reviewerNotes.value.trim();
    const existing = state.decisions[record.id];
    if (!existing && !note) return;
    state.decisions[record.id] = {
      ...(existing || { decision: null, record_kind: record.kind, title: record.title }),
      note,
      updated_at: new Date().toISOString(),
    };
    saveDecisions();
  }

  function move(amount) {
    if (!state.filtered.length) return;
    saveNote();
    state.index = Math.max(0, Math.min(state.filtered.length - 1, state.index + amount));
    renderRecord(currentRecord());
  }

  function populateSourceFilter() {
    const selected = state.source;
    const sources = [...new Set(queueRecords(state.queue).map((record) => record.source_family).filter(Boolean))].sort();
    elements.sourceFilter.replaceChildren();
    const all = document.createElement("option");
    all.value = "all";
    all.textContent = "All sources";
    elements.sourceFilter.append(all);
    sources.forEach((source) => {
      const option = document.createElement("option");
      option.value = source;
      option.textContent = source;
      elements.sourceFilter.append(option);
    });
    state.source = sources.includes(selected) ? selected : "all";
    elements.sourceFilter.value = state.source;
  }

  function showToast(message) {
    window.clearTimeout(toastTimer);
    elements.toast.textContent = message;
    elements.toast.classList.add("visible");
    toastTimer = window.setTimeout(() => elements.toast.classList.remove("visible"), 2400);
  }

  function download(name, contents, type) {
    const blob = new Blob([contents], { type });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = name;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  function exportJson() {
    saveNote();
    const payload = {
      schema_version: 1,
      exported_at: new Date().toISOString(),
      catalog_generated_at: data.generated_at,
      decisions: state.decisions,
    };
    download(
      `arrp-horizon-review-${new Date().toISOString().slice(0, 10)}.json`,
      JSON.stringify(payload, null, 2),
      "application/json"
    );
    showToast("Decision file exported.");
  }

  function csvCell(value) {
    const rendered = value === null || value === undefined ? "" : String(value);
    return `"${rendered.replaceAll('"', '""')}"`;
  }

  function exportCsv() {
    saveNote();
    const headers = [
      "review_id",
      "record_kind",
      "title",
      "decision",
      "reviewer_note",
      "reviewed_at",
      "term",
      "screening_track",
      "provisional_arrp_routes",
      "source_family",
      "source_url",
    ];
    const rows = Object.entries(state.decisions)
      .filter(([, saved]) => saved.decision)
      .map(([id, saved]) => {
        const record = recordsById.get(id) || {};
        const source = (record.links || [])[0]?.url || "";
        return [
          id,
          record.kind || saved.record_kind,
          record.title || saved.title,
          saved.decision,
          saved.note,
          saved.reviewed_at || saved.updated_at,
          record.term,
          record.screening,
          record.routes,
          record.source_family,
          source,
        ];
      });
    const rendered = [headers, ...rows].map((row) => row.map(csvCell).join(",")).join("\r\n");
    download(
      `arrp-horizon-review-${new Date().toISOString().slice(0, 10)}.csv`,
      `\ufeff${rendered}\r\n`,
      "text/csv;charset=utf-8"
    );
    showToast("Review CSV exported.");
  }

  async function importJson(file) {
    try {
      const payload = JSON.parse(await file.text());
      if (!payload || typeof payload.decisions !== "object") throw new Error("Missing decisions");
      let imported = 0;
      Object.entries(payload.decisions).forEach(([id, saved]) => {
        if (!recordsById.has(id)) return;
        if (saved.decision && !["yes", "no", "defer"].includes(saved.decision)) return;
        state.decisions[id] = saved;
        imported += 1;
      });
      saveDecisions();
      refresh({ keepId: true });
      showToast(`Imported ${imported.toLocaleString()} review records.`);
    } catch (_error) {
      showToast("That file is not a valid ARRP Horizon review export.");
    }
  }

  function openPrimarySource() {
    const record = currentRecord();
    const url = record?.links?.[0]?.url;
    if (url) window.open(url, "_blank", "noopener,noreferrer");
  }

  function initializeCounts() {
    const monitor = data.records.filter(
      (record) => record.kind === "source_record" && String(record.screening).startsWith("monitor-")
    ).length;
    document.querySelector("#candidate-tab-count").textContent = data.candidate_questions.toLocaleString();
    document.querySelector("#media-tab-count").textContent = data.media_episodes.toLocaleString();
    document.querySelector("#priority-tab-count").textContent = data.priority_records.toLocaleString();
    document.querySelector("#monitor-tab-count").textContent = monitor.toLocaleString();
    document.querySelector("#all-tab-count").textContent = data.catalog_records.toLocaleString();
  }

  document.querySelectorAll("[data-queue]").forEach((button) => {
    button.addEventListener("click", () => chooseQueue(button.dataset.queue));
  });
  document.querySelector("#decision-yes").addEventListener("click", () => setDecision("yes"));
  document.querySelector("#decision-no").addEventListener("click", () => setDecision("no"));
  document.querySelector("#decision-defer").addEventListener("click", () => setDecision("defer"));
  elements.previous.addEventListener("click", () => move(-1));
  elements.next.addEventListener("click", () => move(1));

  elements.search.addEventListener("input", () => {
    state.search = elements.search.value.trim();
    state.index = 0;
    refresh();
  });
  elements.decisionFilter.addEventListener("change", () => {
    state.decisionFilter = elements.decisionFilter.value;
    state.index = 0;
    refresh();
  });
  elements.termFilter.addEventListener("change", () => {
    state.term = elements.termFilter.value;
    state.index = 0;
    refresh();
  });
  elements.sourceFilter.addEventListener("change", () => {
    state.source = elements.sourceFilter.value;
    state.index = 0;
    refresh();
  });
  elements.autoAdvance.checked = state.preferences.autoAdvance !== false;
  elements.autoAdvance.addEventListener("change", () => {
    state.preferences.autoAdvance = elements.autoAdvance.checked;
    savePreferences();
  });

  elements.reviewerNotes.addEventListener("input", () => {
    window.clearTimeout(noteTimer);
    noteTimer = window.setTimeout(saveNote, 400);
  });
  elements.expandSummary.addEventListener("click", () => {
    const expanded = elements.recordSummary.classList.toggle("expanded");
    elements.expandSummary.textContent = expanded ? "Show less" : "Show full summary";
  });

  document.querySelector("#clear-filters").addEventListener("click", () => {
    state.search = "";
    state.decisionFilter = "unreviewed";
    state.term = "all";
    state.source = "all";
    state.index = 0;
    elements.search.value = "";
    elements.decisionFilter.value = "unreviewed";
    elements.termFilter.value = "all";
    elements.sourceFilter.value = "all";
    refresh();
  });
  document.querySelector("#show-all-button").addEventListener("click", () => {
    state.decisionFilter = "all";
    elements.decisionFilter.value = "all";
    state.index = 0;
    refresh();
  });
  document.querySelector("#export-json-button").addEventListener("click", exportJson);
  document.querySelector("#export-csv-button").addEventListener("click", exportCsv);
  document.querySelector("#import-button").addEventListener("click", () => document.querySelector("#import-file").click());
  document.querySelector("#import-file").addEventListener("change", (event) => {
    const file = event.target.files?.[0];
    if (file) importJson(file);
    event.target.value = "";
  });

  document.addEventListener("keydown", (event) => {
    const tag = document.activeElement?.tagName;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    const key = event.key.toLocaleLowerCase();
    if (key === "y") setDecision("yes");
    else if (key === "n") setDecision("no");
    else if (key === "d") setDecision("defer");
    else if (key === "j" || event.key === "ArrowRight") move(1);
    else if (key === "k" || event.key === "ArrowLeft") move(-1);
    else if (key === "o") openPrimarySource();
    else return;
    event.preventDefault();
  });

  window.addEventListener("beforeunload", saveNote);

  initializeCounts();
  populateSourceFilter();
  refresh();
})();
