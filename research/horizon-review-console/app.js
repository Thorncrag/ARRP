(function () {
  "use strict";

  const data = window.ARRP_HORIZON_REVIEW_DATA;
  if (!data || !Array.isArray(data.records) || !Array.isArray(data.active_horizon_records)
      || !Array.isArray(data.cited_sources) || !Array.isArray(data.monitoring_issues)
      || !Array.isArray(data.pending_sources)) {
    document.body.innerHTML = "<p>Candidate and source data could not be loaded. Rebuild the console data bundle.</p>";
    return;
  }

  const byId = (id) => document.getElementById(id);
  const preliminaryState = { search: "", term: "all", area: "all" };
  const proposedState = { search: "", status: "all", area: "all" };
  const sourceStates = {
    sources: { search: "", filter: "all", page: 1 }
  };
  const pendingState = { search: "", owner: "all" };
  const manualWatchState = { search: "", kind: "all" };
  const courtWatchState = { search: "", owner: "all" };
  const directiveState = { search: "", administration: "all", status: "all", page: 1 };
  const PAGE_SIZE = 50;

  data.court_watch_sources = Array.isArray(data.court_watch_sources) ? data.court_watch_sources : [];
  data.presidential_directives = Array.isArray(data.presidential_directives) ? data.presidential_directives : [];
  data.watcher_metadata = data.watcher_metadata || {};

  function text(value, fallback = "—") {
    return String(value || fallback);
  }

  function termLabel(term) {
    if (String(term) === "1") return "First term";
    if (String(term) === "2") return "Second term";
    return "Both terms";
  }

  function formatDate(value) {
    if (!value) return "Not recorded";
    const date = new Date(value);
    return Number.isNaN(date.valueOf())
      ? value
      : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
  }

  function element(tag, className, content) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = content;
    return node;
  }

  function renderedIssueBody(html, fallbackText) {
    if (!html) return element("pre", "issue-body issue-body-plain", fallbackText);
    const node = element("div", "issue-body markdown-body");
    // The build script escapes all source HTML and emits only allowlisted markup.
    node.innerHTML = html;
    return node;
  }

  function labeledValue(label, value) {
    const wrapper = element("div", "detail-item");
    wrapper.append(element("dt", "", label), element("dd", "", text(value)));
    return wrapper;
  }

  function linkButton(label, url, secondary) {
    const anchor = element("a", secondary ? "record-link secondary" : "record-link", label);
    anchor.href = url;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
    return anchor;
  }

  function inlineLink(label, url) {
    const anchor = element("a", "inline-link", label);
    anchor.href = url;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
    return anchor;
  }

  function dossierSection(label, value, className = "") {
    const section = element("section", `dossier-summary ${className}`.trim());
    section.append(element("h4", "", label), element("p", "", text(value)));
    return section;
  }

  function detailsPanel(label, count, open = false) {
    const panel = element("details", "dossier-panel");
    panel.open = open;
    const summary = element("summary");
    summary.append(element("span", "", label));
    if (count !== undefined) summary.append(element("span", "panel-count", String(count)));
    panel.append(summary);
    return panel;
  }

  function sourceEntry(source) {
    const item = element("article", "evidence-record");
    const heading = element("div", "evidence-heading");
    const title = source.url
      ? linkButton(source.title || source.id, source.url, true)
      : element("strong", "", text(source.title, source.id));
    heading.append(element("span", "record-id", source.id), title);
    const meta = element("p", "evidence-meta",
      [source.publisher, source.date, source.type, source.reliability, source.inventory_status]
        .filter(Boolean).join(" · "));
    item.append(heading, meta);
    if (source.proposition) item.append(element("p", "evidence-proposition", source.proposition));
    if (source.retention_rationale) item.append(element("p", "evidence-note", `Why retained: ${source.retention_rationale}`));
    if (source.pending_reason) item.append(element("p", "evidence-note", `Why still pending: ${source.pending_reason}`));
    if (source.next_action) item.append(element("p", "evidence-note", `Next action: ${source.next_action}`));
    if (source.blocker) item.append(element("p", "evidence-note warning-text", `Blocker: ${source.blocker}`));
    if (source.monitoring_rationale) {
      const group = source.monitoring_group ? ` [${source.monitoring_group}]` : "";
      item.append(element("p", "evidence-note", `Why monitored${group}: ${source.monitoring_rationale}`));
    }
    if (source.notes) item.append(element("p", "evidence-note", source.notes));
    return item;
  }

  function monitoredSourcesFirst(left, right) {
    const monitoringOrder = Number(right.monitoring === "Yes") - Number(left.monitoring === "Yes");
    if (monitoringOrder) return monitoringOrder;
    return String(left.id || "").localeCompare(String(right.id || ""));
  }

  function catalogEntry(record) {
    const item = element("article", "evidence-record");
    const heading = element("div", "evidence-heading");
    heading.append(element("span", "record-id", record.id), element("strong", "", record.title));
    item.append(heading, element("p", "evidence-meta",
      [termLabel(record.term), record.date, record.type, record.actor].filter(Boolean).join(" · ")));
    if (record.legal_question) item.append(element("p", "evidence-proposition", record.legal_question));
    if (record.litigation_posture) item.append(element("p", "evidence-note", `Posture: ${record.litigation_posture}`));
    const links = element("div", "inline-links");
    (record.links || []).forEach((link) => links.append(linkButton(link.label, link.url, true)));
    if (links.children.length) item.append(links);
    return item;
  }

  function researchEntry(record) {
    const item = element("article", "research-record");
    item.append(linkButton(record.title, record.url, true), element("code", "", record.path));
    return item;
  }

  function evidencePanels(record) {
    const fragment = document.createDocumentFragment();
    const sources = record.supporting_sources || [];
    const catalog = record.evidence_records || [];
    const research = record.research_records || [];

    const sourcePanel = detailsPanel("Source inventory records", sources.length, sources.length <= 4);
    const sourceList = element("div", "evidence-list");
    if (sources.length) [...sources].sort(monitoredSourcesFirst).forEach((source) => sourceList.append(sourceEntry(source)));
    else sourceList.append(element("p", "muted panel-empty", "No source-inventory record is currently associated by identifier."));
    sourcePanel.append(sourceList);
    fragment.append(sourcePanel);

    if (catalog.length) {
      const catalogPanel = detailsPanel("Supporting evidence catalog", catalog.length);
      const catalogList = element("div", "evidence-list");
      catalog.forEach((item) => catalogList.append(catalogEntry(item)));
      catalogPanel.append(catalogList);
      fragment.append(catalogPanel);
    }

    if (research.length) {
      const researchPanel = detailsPanel("Project research mentioning this candidate", research.length);
      const researchList = element("div", "research-list");
      research.forEach((item) => researchList.append(researchEntry(item)));
      researchPanel.append(researchList);
      fragment.append(researchPanel);
    }
    return fragment;
  }

  function preliminaryCard(record) {
    const card = element("article", "candidate-card");
    const header = element("div", "card-header");
    const heading = element("div");
    const badges = element("div", "badges");
    badges.append(
      element("span", "badge primary", "Preliminary candidate"),
      element("span", "badge", termLabel(record.term)),
      element("span", "badge", text(record.proposed_area, "Area undecided"))
    );
    heading.append(badges, element("p", "record-id", record.id), element("h3", "", record.title));
    header.append(heading);

    const defect = element("section", "defect-summary");
    defect.append(element("h4", "", "Possible institutional defect"), element("p", "", record.summary));

    const details = element("dl", "candidate-details");
    details.append(
      labeledValue("Why it may be distinct", record.distinctness),
      labeledValue("Existing coverage checked", record.coverage),
      labeledValue("Best counterargument", record.counterargument),
      labeledValue("Questions remaining", record.unresolved),
      labeledValue("Current recommendation", record.recommendation)
    );

    const sources = element("section", "dossier-panels");
    sources.append(evidencePanels(record));

    const footer = element("div", "card-footer");
    footer.append(
      element("span", "", `Last reviewed: ${text(record.last_checked, "Not recorded")}`),
      element("span", "", "Review disposition in Codex")
    );
    card.append(header, defect, details, sources, footer);
    return card;
  }

  function proposedCard(record) {
    const card = element("article", "candidate-card formal-card");
    const header = element("div", "card-header");
    const heading = element("div");
    const badges = element("div", "badges");
    badges.append(
      element("span", "badge formal", text(record.status)),
      element("span", "badge", text(record.area, "Area unassigned")),
      element("span", "badge", text(record.priority, "Priority unassigned"))
    );
    heading.append(badges, element("p", "record-id", record.id), element("h3", "", record.title));
    header.append(heading);

    const history = record.horizon_history || {};
    const summary = element("div", "dossier-grid");
    summary.append(
      dossierSection("Institutional question", history.original_concern || "The Horizon Scan Log does not yet contain a structured concern statement.", "wide"),
      dossierSection("Current intake posture", history.decision || record.status),
      dossierSection("Possible home and overlap", history.integrated_into || "Not recorded"),
      dossierSection("Why it may be distinct—or not", history.rationale || "Not recorded", "wide"),
      dossierSection("Open questions and next review", record.next_audit),
      dossierSection("Follow-up from intake history", history.follow_up || "Not recorded")
    );

    const lifecycle = element("dl", "candidate-details compact");
    lifecycle.append(
      labeledValue("Project status", record.status),
      labeledValue("Last internal review", record.last_audit),
      labeledValue("Release blocker", record.release_blocker),
      labeledValue("Last GitHub update", formatDate(record.updated_at))
    );

    const panels = element("section", "dossier-panels");
    panels.append(evidencePanels(record));

    if ((history.links || []).length) {
      const historyPanel = detailsPanel("Links preserved in the Horizon intake history", history.links.length);
      const historyLinks = element("div", "source-list compact-links");
      history.links.forEach((item) => historyLinks.append(linkButton(item.label, item.url, true)));
      historyPanel.append(historyLinks);
      panels.append(historyPanel);
    }

    const issueBody = (record.issue_body_lines || []).join("\n");
    const issuePanel = detailsPanel("GitHub intake record", issueBody ? 1 : 0);
    issuePanel.append(issueBody
      ? renderedIssueBody(record.issue_body_html, issueBody)
      : element("p", "muted panel-empty", "The issue body is not present in this snapshot. Run a GitHub refresh to include it."));
    panels.append(issuePanel);

    const gaps = record.dossier_gaps || [];
    const recordCheck = element("section", gaps.length ? "record-check warning" : "record-check complete");
    recordCheck.append(element("h4", "", "Decision-record check"));
    if (gaps.length) {
      const list = element("ul");
      gaps.forEach((gap) => list.append(element("li", "", gap)));
      recordCheck.append(list);
    } else {
      recordCheck.append(element("p", "", "The configured authoritative inputs are represented in this dossier."));
    }

    const links = element("div", "source-list dossier-actions");
    links.append(linkButton("Open GitHub issue", record.issue_url));
    if (record.canonical_page && record.canonical_page !== record.issue_url) {
      links.append(linkButton("Open canonical page", record.canonical_page, true));
    }
    links.append(linkButton("Open Horizon intake history", record.horizon_log_url, true));
    card.append(header, summary, lifecycle, panels, recordCheck, links);
    return card;
  }

  function populateSelect(select, values, allLabel) {
    const selected = select.value;
    select.replaceChildren();
    const all = element("option", "", allLabel);
    all.value = "all";
    select.append(all);
    values.filter(Boolean).sort().forEach((value) => {
      const option = element("option", "", value);
      option.value = value;
      select.append(option);
    });
    select.value = values.includes(selected) ? selected : "all";
  }

  function activateTab(name, focus = false) {
    const tabs = [...document.querySelectorAll('[role="tab"][data-tab]')];
    const selected = tabs.find((tab) => tab.dataset.tab === name) || tabs[0];
    tabs.forEach((tab) => {
      const active = tab === selected;
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
      byId(tab.getAttribute("aria-controls")).hidden = !active;
    });
    if (focus) selected.focus();
    if (window.location.hash !== `#${selected.dataset.tab}`) {
      window.history.replaceState(null, "", `#${selected.dataset.tab}`);
    }
  }

  function initializeTabs() {
    const tabs = [...document.querySelectorAll('[role="tab"][data-tab]')];
    tabs.forEach((tab, index) => {
      tab.addEventListener("click", () => activateTab(tab.dataset.tab));
      tab.addEventListener("keydown", (event) => {
        let target = null;
        if (event.key === "ArrowRight") target = tabs[(index + 1) % tabs.length];
        if (event.key === "ArrowLeft") target = tabs[(index - 1 + tabs.length) % tabs.length];
        if (event.key === "Home") target = tabs[0];
        if (event.key === "End") target = tabs[tabs.length - 1];
        if (!target) return;
        event.preventDefault();
        activateTab(target.dataset.tab, true);
      });
    });
    const requested = window.location.hash.replace(/^#/, "").split(":", 1)[0];
    activateTab(tabs.some((tab) => tab.dataset.tab === requested) ? requested : "candidates");
  }

  function activateWatcherTab(name, focus = false) {
    const tabs = [...document.querySelectorAll('[role="tab"][data-watcher-tab]')];
    const selected = tabs.find((tab) => tab.dataset.watcherTab === name) || tabs[0];
    tabs.forEach((tab) => {
      const active = tab === selected;
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
      byId(tab.getAttribute("aria-controls")).hidden = !active;
    });
    if (focus) selected.focus();
    if (window.location.hash.startsWith("#watchers")) {
      window.history.replaceState(null, "", `#watchers:${selected.dataset.watcherTab}`);
    }
  }

  function initializeWatcherTabs() {
    const tabs = [...document.querySelectorAll('[role="tab"][data-watcher-tab]')];
    tabs.forEach((tab, index) => {
      tab.addEventListener("click", () => activateWatcherTab(tab.dataset.watcherTab));
      tab.addEventListener("keydown", (event) => {
        let target = null;
        if (event.key === "ArrowRight") target = tabs[(index + 1) % tabs.length];
        if (event.key === "ArrowLeft") target = tabs[(index - 1 + tabs.length) % tabs.length];
        if (event.key === "Home") target = tabs[0];
        if (event.key === "End") target = tabs[tabs.length - 1];
        if (!target) return;
        event.preventDefault();
        activateWatcherTab(target.dataset.watcherTab, true);
      });
    });
    const parts = window.location.hash.replace(/^#/, "").split(":");
    const requested = parts[0] === "watchers" ? parts[1] : "overview";
    activateWatcherTab(tabs.some((tab) => tab.dataset.watcherTab === requested) ? requested : "overview");
  }

  function sourceSearchText(record) {
    return [record.id, record.title, record.publisher, record.date, record.type,
      record.proposition, record.reliability, record.reviewed, record.notes,
      record.monitoring, record.retention_rationale, record.pending_reason,
      record.next_action, record.blocker, record.monitoring_rationale,
      record.monitoring_group,
      ...(record.record_ids || [])]
      .filter(Boolean).join(" ").toLowerCase();
  }

  function sourceTable(records) {
    if (!records.length) {
      const empty = element("div", "empty-state compact-empty");
      empty.append(element("h3", "", "No matching sources"), element("p", "", "Adjust the search or filter."));
      return empty;
    }
    const wrapper = element("div", "source-table-wrap");
    const table = element("table", "source-table");
    const head = element("thead");
    const headRow = element("tr");
    ["Source", "Publisher", "Date / type", "Associated records", "Monitor", "Link"]
      .forEach((label) => headRow.append(element("th", "", label)));
    head.append(headRow);
    const body = element("tbody");
    records.forEach((record) => {
      const row = element("tr");
      const sourceCell = element("td", "source-title-cell");
      sourceCell.append(element("span", "record-id", record.id), element("strong", "", text(record.title, "Untitled source")));
      const publisherCell = element("td", "", text(record.publisher));
      const detailsCell = element("td");
      detailsCell.append(element("span", "", text(record.date)), element("small", "", text(record.type)));
      const ownerCell = element("td");
      const owners = record.record_ids || [];
      ownerCell.textContent = owners.length ? owners.join(" · ") : "—";
      const monitoringCell = element("td");
      monitoringCell.append(element(
        "span",
        record.monitoring === "Yes" ? "monitoring-flag active" : "monitoring-flag",
        record.monitoring === "Yes" ? "Yes" : "No"
      ));
      if (record.monitoring === "Yes") {
        monitoringCell.append(element("small", "", record.monitoring_rationale || "No source-specific rationale recorded"));
        monitoringCell.append(element(
          "small",
          "",
          record.monitoring_baseline_present ? "Watcher baseline accepted" : "No automated baseline"
        ));
      }
      const linkCell = element("td", "source-link-cell");
      linkCell.append(record.url ? inlineLink("Open ↗", record.url) : element("span", "muted", "No link"));
      row.append(sourceCell, publisherCell, detailsCell, ownerCell, monitoringCell, linkCell);
      body.append(row);
    });
    table.append(head, body);
    wrapper.append(table);
    return wrapper;
  }

  function pagination(name, total, state, render) {
    const nav = byId(`${name}-pagination`);
    nav.replaceChildren();
    const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    state.page = Math.min(state.page, pages);
    const previous = element("button", "page-button", "← Previous");
    previous.type = "button";
    previous.disabled = state.page === 1;
    previous.addEventListener("click", () => { state.page -= 1; render(); });
    const status = element("span", "page-status", `Page ${state.page} of ${pages}`);
    const next = element("button", "page-button", "Next →");
    next.type = "button";
    next.disabled = state.page === pages;
    next.addEventListener("click", () => { state.page += 1; render(); });
    nav.append(previous, status, next);
  }

  function renderSourceView(name, records, filterField) {
    const state = sourceStates[name];
    const query = state.search.toLowerCase();
    const filtered = records.filter((record) => {
      if (state.filter !== "all" && record[filterField] !== state.filter) return false;
      return !query || sourceSearchText(record).includes(query);
    }).sort(monitoredSourcesFirst);
    const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
    state.page = Math.min(state.page, pages);
    const start = (state.page - 1) * PAGE_SIZE;
    byId(`${name}-visible`).textContent = filtered.length;
    byId(`${name}-table`).replaceChildren(sourceTable(filtered.slice(start, start + PAGE_SIZE)));
    pagination(name, filtered.length, state, () => renderSourceView(name, records, filterField));
  }

  function monitoringIssueCard(record) {
    const details = element("details", "monitoring-issue");
    const summary = element("summary");
    const identity = element("div", "monitoring-identity");
    identity.append(element("span", "record-id", record.id), element("strong", "", record.title));
    const metadata = element("div", "monitoring-metadata");
    metadata.append(
      element("span", "badge formal", record.kind),
      element("span", "badge", record.area),
      element("span", "badge", record.status),
      element("span", "badge", `${record.source_count} source${record.source_count === 1 ? "" : "s"}`)
    );
    summary.append(identity, metadata);
    const body = element("div", "monitoring-body");
    const actions = element("div", "source-list compact-links");
    actions.append(linkButton("Open GitHub issue", record.issue_url));
    body.append(
      dossierSection("Why this issue is monitored", record.monitoring_rationale || "The owning issue has not yet recorded a structured monitoring trigger.", "wide"),
      actions
    );
    if ((record.sources || []).length) {
      const sourceList = element("div", "evidence-list monitoring-sources");
      [...record.sources].sort(monitoredSourcesFirst).forEach((source) => sourceList.append(sourceEntry(source)));
      body.append(sourceList);
    } else {
      body.append(element("p", "muted panel-empty", "No source-inventory records are currently associated with this issue."));
    }
    details.append(summary, body);
    return details;
  }

  function renderManualWatch() {
    const query = manualWatchState.search.toLowerCase();
    const records = data.monitoring_issues.filter((record) => {
      if (manualWatchState.kind !== "all" && record.kind !== manualWatchState.kind) return false;
      if (!query) return true;
      return [record.id, record.title, record.kind, record.area, record.status, record.monitoring_rationale,
        ...(record.sources || []).flatMap((source) => [sourceSearchText(source)])]
        .filter(Boolean).join(" ").toLowerCase().includes(query);
    });
    byId("manual-watch-visible").textContent = records.length;
    byId("manual-watch-list").replaceChildren(...records.map(monitoringIssueCard));
  }

  function groupRecords(records, keyFor) {
    const groups = new Map();
    records.forEach((record) => {
      const key = keyFor(record);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(record);
    });
    return groups;
  }

  function distinctSourceCount(records) {
    return new Set(records.map((record) => record.id)).size;
  }

  function renderPending() {
    const query = pendingState.search.toLowerCase();
    const filtered = data.pending_sources.filter((record) => {
      if (pendingState.owner !== "all" && !(record.record_ids || []).includes(pendingState.owner)) return false;
      return !query || sourceSearchText(record).includes(query);
    });
    byId("pending-visible").textContent = filtered.length;
    byId("pending-list").replaceChildren(
      ...filtered.sort(monitoredSourcesFirst).map(sourceEntry)
    );
  }

  function courtWatchCard(label, records) {
    const details = element("details", "monitoring-issue");
    const summary = element("summary");
    const identity = element("div", "monitoring-identity");
    identity.append(element("span", "record-id", records[0].owner_id), element("strong", "", label));
    const metadata = element("div", "monitoring-metadata");
    metadata.append(
      element("span", "badge formal", "Tracker-assisted"),
      element("span", "badge", `${records.length} docket${records.length === 1 ? "" : "s"}`)
    );
    summary.append(identity, metadata);
    const body = element("div", "monitoring-body");
    body.append(dossierSection("Why monitored", records[0].monitoring_rationale || "A structured source-specific rationale has not yet been recorded.", "wide"));
    body.append(dossierSection(
      "Watcher baseline",
      records.every((record) => record.monitoring_baseline_present)
        ? "Accepted for every listed source. A later material change will be proposed through a review pull request."
        : "Initialization is still required for at least one listed source before normal scheduled comparison can proceed.",
      "wide"
    ));
    const links = element("div", "source-list compact-links");
    if (records[0].owner_issue_url) links.append(linkButton("Open owning GitHub issue", records[0].owner_issue_url));
    body.append(links);
    const list = element("div", "evidence-list");
    [...records].sort(monitoredSourcesFirst).forEach((source) => list.append(sourceEntry(source)));
    body.append(list);
    details.append(summary, body);
    return details;
  }

  function renderCourtWatch() {
    const query = courtWatchState.search.toLowerCase();
    const filtered = data.court_watch_sources.filter((record) => {
      if (courtWatchState.owner !== "all" && record.owner_id !== courtWatchState.owner) return false;
      return !query || [sourceSearchText(record), record.owner_id, record.owner_title, record.coverage]
        .filter(Boolean).join(" ").toLowerCase().includes(query);
    });
    const groups = groupRecords(filtered, (record) => `${record.owner_id}::${record.monitoring_group || record.owner_title}`);
    byId("court-watch-visible").textContent = distinctSourceCount(filtered);
    byId("court-watch-list").replaceChildren(
      ...[...groups.entries()].map(([, records]) => courtWatchCard(records[0].monitoring_group || records[0].owner_title, records))
    );
  }

  function directiveSearchText(record) {
    return [record.id, record.type, record.number, record.title, record.president,
      record.administration, record.review_status, record.arrp_record_ids,
      record.source_ids, record.disposition_rationale]
      .flat().filter(Boolean).join(" ").toLowerCase();
  }

  function directiveTable(records) {
    if (!records.length) {
      const empty = element("div", "empty-state compact-empty");
      empty.append(element("h3", "", "No matching directives"), element("p", "", "Adjust the search or filter."));
      return empty;
    }
    const wrapper = element("div", "source-table-wrap");
    const table = element("table", "source-table directive-table");
    const head = element("thead");
    const headRow = element("tr");
    ["Directive", "Administration", "Published", "Screening status", "ARRP routing", "Link"]
      .forEach((label) => headRow.append(element("th", "", label)));
    head.append(headRow);
    const body = element("tbody");
    records.forEach((record) => {
      const row = element("tr");
      const titleCell = element("td", "source-title-cell");
      titleCell.append(element("span", "record-id", record.number || record.id), element("strong", "", text(record.title, "Untitled directive")));
      const presidentCell = element("td", "", text(record.administration || record.president));
      const dateCell = element("td", "", text(record.published_date || record.signed_date));
      const statusCell = element("td");
      const requiresFollowUp = /^(New|Changed) since/.test(record.review_status || "");
      statusCell.append(element("span", requiresFollowUp ? "monitoring-flag active" : "monitoring-flag", text(record.review_status)));
      const routingCell = element("td", "", (record.arrp_record_ids || []).join(" · ") || "—");
      const linkCell = element("td", "source-link-cell");
      linkCell.append(record.official_url ? inlineLink("Open ↗", record.official_url) : element("span", "muted", "No link"));
      row.append(titleCell, presidentCell, dateCell, statusCell, routingCell, linkCell);
      body.append(row);
    });
    table.append(head, body);
    wrapper.append(table);
    return wrapper;
  }

  function renderDirectives() {
    const query = directiveState.search.toLowerCase();
    const records = data.presidential_directives.filter((record) => {
      if (directiveState.administration !== "all" && record.administration !== directiveState.administration) return false;
      if (directiveState.status !== "all" && record.review_status !== directiveState.status) return false;
      return !query || directiveSearchText(record).includes(query);
    });
    const pages = Math.max(1, Math.ceil(records.length / PAGE_SIZE));
    directiveState.page = Math.min(directiveState.page, pages);
    const start = (directiveState.page - 1) * PAGE_SIZE;
    byId("directive-visible").textContent = records.length;
    byId("directive-table").replaceChildren(directiveTable(records.slice(start, start + PAGE_SIZE)));
    pagination("directive", records.length, directiveState, renderDirectives);
  }

  function watcherSummaryCard(label, value, detail) {
    const card = element("article", "watcher-summary-card");
    card.append(element("span", "eyebrow", label), element("strong", "", String(value)), element("p", "", detail));
    return card;
  }

  function renderWatcherOverview() {
    const monitoredSources = [...data.cited_sources, ...data.pending_sources]
      .filter((source) => source.monitoring === "Yes").length;
    const directiveFollowUp = data.presidential_directives
      .filter((record) => /^(New|Changed) since/.test(record.review_status || "")).length;
    byId("watcher-summary-grid").replaceChildren(
      watcherSummaryCard("Issue-level monitoring", data.monitoring_issues.length, "GitHub issues requiring a complete monitoring pass."),
      watcherSummaryCard("Changing source records", monitoredSources, "Dockets and other sources whose own contents may change."),
      watcherSummaryCard("Tracker-assisted cases", distinctSourceCount(data.court_watch_sources), "Cataloged court sources covered by per-source watcher baselines."),
      watcherSummaryCard("Directive follow-up", directiveFollowUp, "New or changed directives awaiting another project screening pass.")
    );
  }

  function renderPreliminary() {
    const query = preliminaryState.search.toLowerCase();
    const records = data.records.filter((record) => {
      if (preliminaryState.term !== "all" && String(record.term) !== preliminaryState.term) return false;
      if (preliminaryState.area !== "all" && record.proposed_area !== preliminaryState.area) return false;
      if (!query) return true;
      return [record.id, record.title, record.summary, record.proposed_area, record.distinctness,
        record.coverage, record.counterargument, record.unresolved,
        ...(record.links || []).map((item) => item.label)]
        .filter(Boolean).join(" ").toLowerCase().includes(query);
    });
    const list = byId("preliminary-list");
    list.replaceChildren(...records.map(preliminaryCard));
    byId("preliminary-visible").textContent = records.length;
    byId("preliminary-empty").hidden = records.length !== 0;
  }

  function renderProposed() {
    const query = proposedState.search.toLowerCase();
    const records = data.active_horizon_records.filter((record) => {
      if (proposedState.status !== "all" && record.status !== proposedState.status) return false;
      if (proposedState.area !== "all" && record.area !== proposedState.area) return false;
      if (!query) return true;
      const history = record.horizon_history || {};
      return [record.id, record.title, record.status, record.area, record.priority,
        record.next_audit, record.last_audit, history.original_concern, history.decision,
        history.integrated_into, history.rationale, history.follow_up,
        ...(record.labels || []),
        ...(record.supporting_sources || []).flatMap((item) => [item.id, item.title, item.publisher, item.proposition]),
        ...(record.evidence_records || []).flatMap((item) => [item.id, item.title, item.legal_question]),
        ...(record.research_records || []).flatMap((item) => [item.title, item.path])]
        .filter(Boolean).join(" ").toLowerCase().includes(query);
    });
    byId("proposed-list").replaceChildren(...records.map(proposedCard));
    byId("proposed-visible").textContent = records.length;
  }

  function initialize() {
    byId("preliminary-count").textContent = data.records.length;
    byId("proposed-count").textContent = data.active_horizon_records.length;
    byId("attention-note").textContent = data.records.length
      ? `${data.records.length} preliminary candidate${data.records.length === 1 ? "" : "s"} require human review.`
      : "No preliminary candidates currently require review.";
    byId("github-synced-at").textContent = formatDate(data.github_synced_at);
    byId("sources-count").textContent = data.cited_sources.length;
    byId("pending-count").textContent = data.pending_sources.length;
    byId("watchers-count").textContent = data.monitoring_issues.length;
    byId("tab-candidates-count").textContent = data.active_horizon_records.length;
    byId("tab-preliminaries-count").textContent = data.records.length;
    byId("tab-sources-count").textContent = data.cited_sources.length;
    byId("tab-pending-count").textContent = data.pending_sources.length;
    byId("tab-watchers-count").textContent = data.monitoring_issues.length;
    byId("court-watch-count").textContent = distinctSourceCount(data.court_watch_sources);
    byId("directive-watch-count").textContent = data.presidential_directives.length;
    byId("manual-watch-count").textContent = data.monitoring_issues.length;
    byId("case-watcher-mode").textContent = `Current mode: ${(data.watcher_metadata.case_monitor || {}).mode || "Not configured"}.`;
    byId("directive-watcher-mode").textContent = `Current mode: ${(data.watcher_metadata.presidential_directives || {}).mode || "Not configured"}.`;

    populateSelect(byId("preliminary-area"), [...new Set(data.records.map((record) => record.proposed_area))], "All areas");
    populateSelect(byId("proposed-status"), [...new Set(data.active_horizon_records.map((record) => record.status))], "All statuses");
    populateSelect(byId("proposed-area"), [...new Set(data.active_horizon_records.map((record) => record.area))], "All areas");
    populateSelect(byId("sources-type"), [...new Set(data.cited_sources.map((record) => record.type))], "All types");
    populateSelect(byId("pending-owner"), [...new Set(data.pending_sources.flatMap((record) => record.record_ids || []))], "All possible destinations");
    populateSelect(byId("manual-watch-kind"), [...new Set(data.monitoring_issues.map((record) => record.kind))], "All issue types");
    populateSelect(byId("court-watch-owner"), [...new Set(data.court_watch_sources.map((record) => record.owner_id))], "All owners");
    populateSelect(byId("directive-administration"), [...new Set(data.presidential_directives.map((record) => record.administration))], "All administrations");
    populateSelect(byId("directive-status"), [...new Set(data.presidential_directives.map((record) => record.review_status))], "All statuses");

    byId("preliminary-search").addEventListener("input", (event) => { preliminaryState.search = event.target.value; renderPreliminary(); });
    byId("preliminary-term").addEventListener("change", (event) => { preliminaryState.term = event.target.value; renderPreliminary(); });
    byId("preliminary-area").addEventListener("change", (event) => { preliminaryState.area = event.target.value; renderPreliminary(); });
    byId("proposed-search").addEventListener("input", (event) => { proposedState.search = event.target.value; renderProposed(); });
    byId("proposed-status").addEventListener("change", (event) => { proposedState.status = event.target.value; renderProposed(); });
    byId("proposed-area").addEventListener("change", (event) => { proposedState.area = event.target.value; renderProposed(); });
    [["sources", data.cited_sources, "type"]]
      .forEach(([name, records, filterField]) => {
        byId(`${name}-search`).addEventListener("input", (event) => {
          sourceStates[name].search = event.target.value;
          sourceStates[name].page = 1;
          renderSourceView(name, records, filterField);
        });
        const filterId = `${name}-type`;
        byId(filterId).addEventListener("change", (event) => {
          sourceStates[name].filter = event.target.value;
          sourceStates[name].page = 1;
          renderSourceView(name, records, filterField);
        });
      });
    byId("pending-search").addEventListener("input", (event) => {
      pendingState.search = event.target.value;
      renderPending();
    });
    byId("pending-owner").addEventListener("change", (event) => {
      pendingState.owner = event.target.value;
      renderPending();
    });
    byId("manual-watch-search").addEventListener("input", (event) => {
      manualWatchState.search = event.target.value;
      renderManualWatch();
    });
    byId("manual-watch-kind").addEventListener("change", (event) => {
      manualWatchState.kind = event.target.value;
      renderManualWatch();
    });
    byId("court-watch-search").addEventListener("input", (event) => {
      courtWatchState.search = event.target.value;
      renderCourtWatch();
    });
    byId("court-watch-owner").addEventListener("change", (event) => {
      courtWatchState.owner = event.target.value;
      renderCourtWatch();
    });
    byId("directive-search").addEventListener("input", (event) => {
      directiveState.search = event.target.value;
      directiveState.page = 1;
      renderDirectives();
    });
    byId("directive-administration").addEventListener("change", (event) => {
      directiveState.administration = event.target.value;
      directiveState.page = 1;
      renderDirectives();
    });
    byId("directive-status").addEventListener("change", (event) => {
      directiveState.status = event.target.value;
      directiveState.page = 1;
      renderDirectives();
    });

    initializeTabs();
    initializeWatcherTabs();
    renderPreliminary();
    renderProposed();
    renderSourceView("sources", data.cited_sources, "type");
    renderPending();
    renderManualWatch();
    renderCourtWatch();
    renderDirectives();
    renderWatcherOverview();
  }

  initialize();
})();
