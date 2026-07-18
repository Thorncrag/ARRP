(function () {
  "use strict";

  const data = window.ARRP_HORIZON_REVIEW_DATA;
  if (!data || !Array.isArray(data.records)) {
    document.body.innerHTML = "<p>Review data could not be loaded. Rebuild the console data bundle.</p>";
    return;
  }

  const state = {
    index: 0,
    search: "",
    term: "all",
    area: "all",
    filtered: [],
  };

  const elements = {
    horizonView: document.querySelector("#horizon-view"),
    historyView: document.querySelector("#history-view"),
    sourcesView: document.querySelector("#sources-view"),
    monitoringView: document.querySelector("#monitoring-view"),
    reviewView: document.querySelector("#review-view"),
    horizonButton: document.querySelector("#show-horizon"),
    historyButton: document.querySelector("#show-history"),
    sourcesButton: document.querySelector("#show-sources"),
    monitoringButton: document.querySelector("#show-monitoring"),
    reviewButton: document.querySelector("#show-review"),
    skipLink: document.querySelector(".skip-link"),
    recordPosition: document.querySelector("#record-position"),
    recordContent: document.querySelector("#record-content"),
    emptyState: document.querySelector("#empty-state"),
    recordBadges: document.querySelector("#record-badges"),
    recordId: document.querySelector("#record-id"),
    recordTitle: document.querySelector("#record-title"),
    reviewPrompt: document.querySelector("#review-prompt"),
    recordSummary: document.querySelector("#record-summary"),
    expandSummary: document.querySelector("#expand-summary"),
    recordDetails: document.querySelector("#record-details"),
    sourceLinks: document.querySelector("#source-links"),
    search: document.querySelector("#search-input"),
    termFilter: document.querySelector("#term-filter"),
    areaFilter: document.querySelector("#area-filter"),
    previous: document.querySelector("#previous-button"),
    next: document.querySelector("#next-button"),
  };

  const queueState = {
    horizonSearch: "",
    horizonStatus: "all",
    horizonArea: "all",
    sourcesSearch: "",
    sourcesType: "all",
    sourcesRoute: "all",
    monitoringSearch: "",
    monitoringRoute: "all",
  };

  function queueRecords() {
    return data.records.filter((record) => record.kind === "preliminary_candidate");
  }

  function matchesFilters(record) {
    if (state.term !== "all" && String(record.term) !== state.term) return false;
    if (state.area !== "all" && record.proposed_area !== state.area) return false;
    if (!state.search) return true;

    const haystack = [
      record.id,
      record.title,
      record.category,
      record.summary,
      record.proposed_area,
      record.coverage,
      record.distinctness,
      record.counterargument,
      record.unresolved,
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
      elements.recordPosition.textContent = "No matching records";
      elements.previous.disabled = true;
      elements.next.disabled = true;
      return;
    }

    elements.recordContent.hidden = false;
    elements.emptyState.hidden = true;
    elements.recordPosition.textContent = `Record ${state.index + 1} of ${state.filtered.length}`;
    elements.previous.disabled = state.index === 0;
    elements.next.disabled = state.index >= state.filtered.length - 1;

    elements.recordBadges.replaceChildren();
    elements.recordBadges.append(
      makeBadge("Preliminary candidate"),
      makeBadge(termLabel(record.term))
    );

    elements.recordId.textContent = record.id;
    elements.recordTitle.textContent = record.title;
    elements.reviewPrompt.textContent = record.review_prompt;
    elements.recordSummary.textContent = record.summary || "No summary is available.";
    elements.recordSummary.classList.remove("expanded");
    elements.expandSummary.textContent = "Show full summary";
    elements.expandSummary.hidden = String(record.summary || "").length < 900;

    const details = [
      detail("Possible project area", record.proposed_area),
      detail("Why it may be distinct", record.distinctness),
      detail("Existing coverage considered", record.coverage),
      detail("Best counterargument", record.counterargument),
      detail("Unresolved questions", record.unresolved),
      detail("Codex recommendation", humanize(record.recommendation)),
      detail("Supporting catalog records", record.source_record_ids),
      detail("Last reviewed", record.last_checked),
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
      noLinks.textContent = "No direct source link is attached yet; consult the candidate record before formal review.";
      elements.sourceLinks.append(noLinks);
    }
  }

  function refresh(options) {
    const settings = options || {};
    const previousId = settings.keepId ? currentRecord()?.id : null;
    const base = queueRecords();
    state.filtered = base.filter(matchesFilters);
    if (previousId) {
      const newIndex = state.filtered.findIndex((record) => record.id === previousId);
      state.index = newIndex >= 0 ? newIndex : Math.min(state.index, Math.max(0, state.filtered.length - 1));
    } else {
      state.index = Math.min(state.index, Math.max(0, state.filtered.length - 1));
    }
    renderRecord(currentRecord());
  }

  function move(amount) {
    if (!state.filtered.length) return;
    state.index = Math.max(0, Math.min(state.filtered.length - 1, state.index + amount));
    renderRecord(currentRecord());
  }

  function populateAreaFilter() {
    const selected = state.area;
    const areas = [...new Set(queueRecords().map((record) => record.proposed_area).filter(Boolean))].sort();
    elements.areaFilter.replaceChildren();
    const all = document.createElement("option");
    all.value = "all";
    all.textContent = "All areas";
    elements.areaFilter.append(all);
    areas.forEach((area) => {
      const option = document.createElement("option");
      option.value = area;
      option.textContent = area;
      elements.areaFilter.append(option);
    });
    state.area = areas.includes(selected) ? selected : "all";
    elements.areaFilter.value = state.area;
  }

  function openPrimarySource() {
    const record = currentRecord();
    const url = record?.links?.[0]?.url;
    if (url) window.open(url, "_blank", "noopener,noreferrer");
  }

  function initializeCounts() {
    document.querySelector("#candidate-tab-count").textContent = data.candidate_questions.toLocaleString();
  }

  function setText(selector, value) {
    const element = document.querySelector(selector);
    if (element) element.textContent = Number(value).toLocaleString();
  }

  function renderDispositionChart() {
    const summary = data.adjudication;
    const categories = [
      { label: "Selected for integration", value: summary.integration_records, className: "integration" },
      { label: "Placed in monitoring", value: summary.monitoring_records, className: "monitoring" },
      { label: "Redundant evidence", value: summary.redundant_records, className: "redundant" },
      { label: "No repairable project issue identified", value: summary.excluded_records, className: "excluded" },
    ];
    const chart = document.querySelector("#disposition-chart");
    const legend = document.querySelector("#disposition-legend");
    chart.replaceChildren();
    legend.replaceChildren();
    chart.setAttribute(
      "aria-label",
      categories.map((item) => `${item.label}: ${item.value.toLocaleString()} records`).join("; ")
    );

    categories.forEach((item) => {
      const segment = document.createElement("span");
      segment.className = `disposition-segment ${item.className}`;
      segment.style.width = `${(item.value / summary.records) * 100}%`;
      segment.setAttribute("aria-hidden", "true");
      chart.append(segment);

      const legendItem = document.createElement("span");
      legendItem.className = "legend-item";
      const swatch = document.createElement("i");
      swatch.className = `legend-swatch ${item.className}`;
      swatch.setAttribute("aria-hidden", "true");
      const copy = document.createElement("span");
      const value = document.createElement("b");
      value.textContent = item.value.toLocaleString();
      copy.append(value, ` ${item.label}`);
      legendItem.append(swatch, copy);
      legend.append(legendItem);
    });
  }

  function renderRouteChart() {
    const chart = document.querySelector("#route-chart");
    chart.replaceChildren();
    const routes = data.integration_routes || [];
    const maximum = Math.max(1, ...routes.map((item) => item.records));
    routes.forEach((item) => {
      const row = document.createElement("div");
      row.className = "route-row";
      const label = item.path ? document.createElement("a") : document.createElement("span");
      label.className = "route-label";
      label.textContent = item.route;
      if (item.path) label.href = item.path;
      const track = document.createElement("span");
      track.className = "route-track";
      const bar = document.createElement("span");
      bar.className = "route-bar";
      bar.style.width = `${(item.records / maximum) * 100}%`;
      track.append(bar);
      const value = document.createElement("b");
      value.textContent = item.records.toLocaleString();
      row.append(label, track, value);
      chart.append(row);
    });
  }

  function recordTag(text) {
    const tag = document.createElement("span");
    tag.className = "record-tag";
    tag.textContent = text;
    return tag;
  }

  function recordField(label, value) {
    if (!value) return null;
    const wrapper = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    wrapper.append(term, description);
    return wrapper;
  }

  function recordLinks(links) {
    if (!links?.length) return null;
    const wrapper = document.createElement("div");
    wrapper.className = "source-links";
    links.forEach((item) => {
      const link = document.createElement("a");
      link.href = item.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = item.label;
      wrapper.append(link);
    });
    return wrapper;
  }

  function operationalCard(record, kind) {
    const details = document.createElement("details");
    details.className = "record-item";
    const summary = document.createElement("summary");
    const copy = document.createElement("span");
    copy.className = "record-summary-copy";
    const identifier = document.createElement("span");
    identifier.textContent = record.id;
    const title = document.createElement("strong");
    title.textContent = record.title || "Untitled record";
    const preview = document.createElement("small");
    preview.textContent = record.question || record.trigger || record.domain || record.posture || record.status || "Open for details";
    copy.append(identifier, title, preview);
    const tags = document.createElement("span");
    tags.className = "record-tags";
    const workflowLabel = record.stage || record.role;
    if (workflowLabel) tags.append(recordTag(workflowLabel));
    (record.routes || []).forEach((route) => tags.append(recordTag(route)));
    if (!(record.routes || []).length && record.term) tags.append(recordTag(record.term));
    const toggle = document.createElement("span");
    toggle.className = "record-toggle";
    toggle.setAttribute("aria-hidden", "true");
    summary.append(copy, tags, toggle);

    const body = document.createElement("div");
    body.className = "record-body";
    const fields = document.createElement("dl");
    let values = [];
    if (kind === "integration") {
      values = [
        recordField("Work stage", record.stage),
        recordField("Owner", record.owner),
        recordField("Next action", record.next_action),
        recordField("Your attention", record.user_attention),
        recordField("Legal question or outcome", record.question),
        recordField("Litigation posture", record.posture),
        recordField("Source family", record.family),
        recordField("Last reviewed", record.date),
      ];
    } else if (kind === "monitoring") {
      values = [
        recordField("Work stage", record.stage),
        recordField("Owner", record.owner),
        recordField("Next action", record.next_action),
        recordField("Your attention", record.user_attention),
        recordField("Revisit trigger", record.trigger),
        recordField("Litigation posture", record.posture),
        recordField("Source family", record.family),
        recordField("Last checked", record.date),
      ];
    } else if (kind === "source") {
      values = [
        recordField("Role in the project", record.role),
        recordField("Owner", record.owner),
        recordField("Next action", record.next_action),
        recordField("Your attention", record.user_attention),
        recordField("Coverage domain", record.domain),
        recordField("Source type", record.source_type),
        recordField("Term coverage", record.term),
        recordField("Expected value", record.value),
        recordField("Known limitation", record.limitation),
        recordField("Last checked", record.date),
      ];
    } else {
      values = [
        recordField("Work stage", record.stage),
        recordField("Owner", record.owner),
        recordField("Next action", record.next_action),
        recordField("Your attention", record.user_attention),
        recordField("Institutional question", record.question),
        recordField("Date or period", record.period),
        recordField("Primary evidence", humanize(record.primary_status)),
        recordField("Last checked", record.date),
      ];
    }
    fields.append(...values.filter(Boolean));
    body.append(fields);
    if (record.note) {
      const note = document.createElement("p");
      note.className = "record-note";
      note.textContent = record.note;
      body.append(note);
    }
    const links = recordLinks(record.links);
    if (links) body.append(links);
    details.append(summary, body);
    return details;
  }

  function dateLabel(value) {
    if (!value) return "Not recorded";
    const date = new Date(value);
    return Number.isNaN(date.valueOf())
      ? value
      : date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
  }

  function openRelatedQueue(kind, route) {
    if (kind === "sources") {
      queueState.sourcesRoute = route;
      document.querySelector("#sources-route-filter").value = route;
      renderSourcesView();
      showView("sources");
      return;
    }
    queueState.monitoringRoute = route;
    document.querySelector("#monitoring-route-filter").value = route;
    renderMonitoringView();
    showView("monitoring");
  }

  function horizonCard(record, closed) {
    const details = document.createElement("details");
    details.className = "record-item horizon-record";
    const summary = document.createElement("summary");
    const copy = document.createElement("span");
    copy.className = "record-summary-copy";
    const identifier = document.createElement("span");
    identifier.textContent = `${record.id} · GitHub #${record.number}`;
    const title = document.createElement("strong");
    title.textContent = record.title;
    const preview = document.createElement("small");
    preview.textContent = closed ? record.full_title : record.next_audit;
    copy.append(identifier, title, preview);
    const tags = document.createElement("span");
    tags.className = "record-tags";
    tags.append(recordTag(record.status));
    if (record.area && record.area !== "Unassigned") tags.append(recordTag(record.area));
    if (record.priority && record.priority !== "Unassigned") tags.append(recordTag(record.priority));
    if (record.needs_monitoring) tags.append(recordTag("Needs monitoring"));
    const toggle = document.createElement("span");
    toggle.className = "record-toggle";
    toggle.setAttribute("aria-hidden", "true");
    summary.append(copy, tags, toggle);

    const body = document.createElement("div");
    body.className = "record-body";
    const fields = document.createElement("dl");
    fields.append(...[
      recordField("Project status", record.status),
      recordField("GitHub issue state", record.issue_state),
      recordField("Provisional area", record.area),
      recordField("Priority", record.priority),
      recordField("Last audit", record.last_audit),
      recordField("Next audit or action", record.next_audit),
      recordField("Release posture", record.release_blocker),
      recordField("GitHub updated", dateLabel(record.updated_at)),
      recordField("Related source tasks", String(record.source_task_count || 0)),
      recordField("Related monitoring items", String(record.monitoring_task_count || 0)),
    ].filter(Boolean));
    body.append(fields);

    const queueActions = document.createElement("div");
    queueActions.className = "related-queue-actions";
    if (record.source_task_count) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "text-link";
      button.textContent = `Open ${record.source_task_count.toLocaleString()} related source task${record.source_task_count === 1 ? "" : "s"}`;
      button.addEventListener("click", () => openRelatedQueue("sources", record.id));
      queueActions.append(button);
    }
    if (record.monitoring_task_count) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "text-link";
      button.textContent = `Open ${record.monitoring_task_count.toLocaleString()} related monitoring item${record.monitoring_task_count === 1 ? "" : "s"}`;
      button.addEventListener("click", () => openRelatedQueue("monitoring", record.id));
      queueActions.append(button);
    }
    if (queueActions.childElementCount) body.append(queueActions);

    if (record.related_source_links?.length) {
      const heading = document.createElement("strong");
      heading.className = "related-source-heading";
      heading.textContent = "Related source links";
      body.append(heading, recordLinks(record.related_source_links));
    }
    const links = recordLinks([
      { label: "Open GitHub issue", url: record.issue_url },
      ...(record.canonical_page && record.canonical_page !== record.issue_url
        ? [{ label: "Open canonical project page", url: record.canonical_page }]
        : []),
    ]);
    if (links) body.append(links);
    details.append(summary, body);
    return details;
  }

  function recordMatches(record, search) {
    if (!search) return true;
    return JSON.stringify(record).toLocaleLowerCase().includes(search.toLocaleLowerCase());
  }

  function renderOperationalList(containerSelector, records, total, visibleSelector, totalSelector) {
    const container = document.querySelector(containerSelector);
    container.replaceChildren();
    setText(visibleSelector, records.length);
    setText(totalSelector, total);
    if (!records.length) {
      const empty = document.createElement("p");
      empty.className = "record-list-empty";
      empty.textContent = "No records match the current search or filter.";
      container.append(empty);
      return;
    }
    const fragment = document.createDocumentFragment();
    records.forEach((record) => fragment.append(operationalCard(record, record.record_kind)));
    container.append(fragment);
  }

  function populateRouteSelect(selector, records) {
    const select = document.querySelector(selector);
    const routes = [...new Set(records.flatMap((record) => record.routes || []))].sort();
    routes.forEach((route) => {
      const option = document.createElement("option");
      option.value = route;
      option.textContent = route;
      select.append(option);
    });
  }

  function populateTypeSelect(selector, records) {
    const select = document.querySelector(selector);
    const types = [...new Set(records.map((record) => record.work_type).filter(Boolean))].sort();
    types.forEach((type) => {
      const option = document.createElement("option");
      option.value = type;
      option.textContent = type;
      select.append(option);
    });
  }

  function populateValueSelect(selector, values) {
    const select = document.querySelector(selector);
    [...new Set(values.filter(Boolean))].sort().forEach((value) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.append(option);
    });
  }

  function renderHorizonView() {
    const records = data.active_horizon_records.filter((record) =>
      recordMatches(record, queueState.horizonSearch)
      && (queueState.horizonStatus === "all" || record.status === queueState.horizonStatus)
      && (queueState.horizonArea === "all" || record.area === queueState.horizonArea)
    );
    const container = document.querySelector("#horizon-record-list");
    container.replaceChildren();
    setText("#horizon-visible-count", records.length);
    setText("#horizon-total-count", data.active_horizon_records.length);
    if (!records.length) {
      const empty = document.createElement("p");
      empty.className = "record-list-empty";
      empty.textContent = "No active proposed candidates match the current search or filter.";
      container.append(empty);
      return;
    }
    const fragment = document.createDocumentFragment();
    records.forEach((record) => fragment.append(horizonCard(record, false)));
    container.append(fragment);
  }

  function renderClosedHorizonRecords() {
    const container = document.querySelector("#closed-horizon-list");
    container.replaceChildren();
    const fragment = document.createDocumentFragment();
    data.closed_horizon_records.forEach((record) => fragment.append(horizonCard(record, true)));
    container.append(fragment);
  }

  function renderSourcesView() {
    const records = data.source_queue_records.filter((record) =>
      recordMatches(record, queueState.sourcesSearch)
      && (queueState.sourcesType === "all" || record.work_type === queueState.sourcesType)
      && (queueState.sourcesRoute === "all" || (record.routes || []).includes(queueState.sourcesRoute))
    );
    renderOperationalList(
      "#sources-record-list",
      records,
      data.source_queue_records.length,
      "#sources-visible-count",
      "#sources-total-count"
    );
  }

  function renderMonitoringView() {
    const records = data.monitoring_records.filter((record) =>
      recordMatches(record, queueState.monitoringSearch)
      && (queueState.monitoringRoute === "all" || record.routes.includes(queueState.monitoringRoute))
    );
    renderOperationalList(
      "#monitoring-record-list",
      records,
      data.monitoring_records.length,
      "#monitoring-visible-count",
      "#monitoring-total-count"
    );
  }

  function initializeDashboard() {
    const summary = data.adjudication;
    setText("#adjudicated-records", summary.baseline_records);
    setText("#adjudication-total", summary.baseline_records + data.catalog_records);
    setText("#history-main-batch-count", summary.records);
    setText("#canonical-sources-added", summary.canonical_sources_added);
    setText("#closed-horizon-count", data.closed_horizon_issue_count);
    setText("#horizon-nav-count", data.horizon_issue_count);
    setText("#review-nav-count", data.candidate_questions);
    setText("#sources-nav-count", data.source_queue_count);
    setText("#monitoring-nav-count", data.litigation_monitoring_queue);
    document.querySelector("#candidate-attention-status").textContent = data.candidate_questions
      ? `${data.candidate_questions.toLocaleString()} preliminary candidates are available for review in Codex`
      : "None—this queue is empty";
    document.querySelector("#catalog-review-status").textContent = data.catalog_records
      ? `${data.catalog_records.toLocaleString()} newly cataloged records pending review`
      : `${summary.priority_records.toLocaleString()} priority + ${summary.records.toLocaleString()} main-batch records · complete`;
    const generated = new Date(data.generated_at);
    document.querySelector("#generated-at").textContent = Number.isNaN(generated.valueOf())
      ? data.generated_at
      : generated.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
    const githubSynced = new Date(data.github_synced_at);
    document.querySelector("#github-synced-at").textContent = Number.isNaN(githubSynced.valueOf())
      ? data.github_synced_at
      : githubSynced.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
    renderDispositionChart();
    renderRouteChart();
  }

  function showView(view) {
    const views = {
      horizon: [elements.horizonView, elements.horizonButton, "#horizon-view", "Skip to proposed candidates"],
      history: [elements.historyView, elements.historyButton, "#history-view", "Skip to intake history"],
      sources: [elements.sourcesView, elements.sourcesButton, "#sources-view", "Skip to source queue"],
      monitoring: [elements.monitoringView, elements.monitoringButton, "#monitoring-view", "Skip to litigation monitor"],
      review: [elements.reviewView, elements.reviewButton, "#review-card", "Skip to preliminary candidate"],
    };
    Object.entries(views).forEach(([name, [section, button]]) => {
      const active = name === view;
      section.hidden = !active;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    elements.skipLink.href = views[view][2];
    elements.skipLink.textContent = views[view][3];
  }

  elements.horizonButton.addEventListener("click", () => showView("horizon"));
  elements.historyButton.addEventListener("click", () => showView("history"));
  elements.sourcesButton.addEventListener("click", () => showView("sources"));
  elements.monitoringButton.addEventListener("click", () => showView("monitoring"));
  elements.reviewButton.addEventListener("click", () => showView("review"));
  document.querySelector("#horizon-search").addEventListener("input", (event) => {
    queueState.horizonSearch = event.target.value.trim();
    renderHorizonView();
  });
  document.querySelector("#horizon-status-filter").addEventListener("change", (event) => {
    queueState.horizonStatus = event.target.value;
    renderHorizonView();
  });
  document.querySelector("#horizon-area-filter").addEventListener("change", (event) => {
    queueState.horizonArea = event.target.value;
    renderHorizonView();
  });
  document.querySelector("#sources-search").addEventListener("input", (event) => {
    queueState.sourcesSearch = event.target.value.trim();
    renderSourcesView();
  });
  document.querySelector("#sources-type-filter").addEventListener("change", (event) => {
    queueState.sourcesType = event.target.value;
    renderSourcesView();
  });
  document.querySelector("#sources-route-filter").addEventListener("change", (event) => {
    queueState.sourcesRoute = event.target.value;
    renderSourcesView();
  });
  document.querySelector("#monitoring-search").addEventListener("input", (event) => {
    queueState.monitoringSearch = event.target.value.trim();
    renderMonitoringView();
  });
  document.querySelector("#monitoring-route-filter").addEventListener("change", (event) => {
    queueState.monitoringRoute = event.target.value;
    renderMonitoringView();
  });
  elements.previous.addEventListener("click", () => move(-1));
  elements.next.addEventListener("click", () => move(1));

  elements.search.addEventListener("input", () => {
    state.search = elements.search.value.trim();
    state.index = 0;
    refresh();
  });
  elements.termFilter.addEventListener("change", () => {
    state.term = elements.termFilter.value;
    state.index = 0;
    refresh();
  });
  elements.areaFilter.addEventListener("change", () => {
    state.area = elements.areaFilter.value;
    state.index = 0;
    refresh();
  });
  elements.expandSummary.addEventListener("click", () => {
    const expanded = elements.recordSummary.classList.toggle("expanded");
    elements.expandSummary.textContent = expanded ? "Show less" : "Show full summary";
  });

  document.querySelector("#clear-filters").addEventListener("click", () => {
    state.search = "";
    state.term = "all";
    state.area = "all";
    state.index = 0;
    elements.search.value = "";
    elements.termFilter.value = "all";
    elements.areaFilter.value = "all";
    refresh();
  });

  document.addEventListener("keydown", (event) => {
    if (elements.reviewView.hidden) return;
    const tag = document.activeElement?.tagName;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(tag)) return;
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    const key = event.key.toLocaleLowerCase();
    if (key === "j" || event.key === "ArrowRight") move(1);
    else if (key === "k" || event.key === "ArrowLeft") move(-1);
    else if (key === "o") openPrimarySource();
    else return;
    event.preventDefault();
  });

  initializeDashboard();
  populateValueSelect("#horizon-status-filter", data.active_horizon_records.map((record) => record.status));
  populateValueSelect("#horizon-area-filter", data.active_horizon_records.map((record) => record.area));
  populateTypeSelect("#sources-type-filter", data.source_queue_records);
  populateRouteSelect("#sources-route-filter", data.source_queue_records);
  populateRouteSelect("#monitoring-route-filter", data.monitoring_records);
  renderHorizonView();
  renderClosedHorizonRecords();
  renderSourcesView();
  renderMonitoringView();
  initializeCounts();
  populateAreaFilter();
  refresh();
  showView("horizon");
})();
