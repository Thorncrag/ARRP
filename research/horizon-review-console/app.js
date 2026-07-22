(function () {
  "use strict";

  const data = window.ARRP_HORIZON_REVIEW_DATA;
  if (!data || !Array.isArray(data.records) || !Array.isArray(data.active_horizon_records)
      || !Array.isArray(data.cited_sources) || !Array.isArray(data.monitoring_issues)
      || !Array.isArray(data.pending_sources) || !Array.isArray(data.page_inventory)
      || !Array.isArray(data.project_logs) || !data.publication
      || !data.publication.manifest || !Array.isArray(data.publication.manifest.editions)) {
    document.body.innerHTML = "<p>Project Console data could not be loaded. Rebuild the console data bundle.</p>";
    return;
  }

  const byId = (id) => document.getElementById(id);
  const preliminaryState = { search: "", term: "all", area: "all" };
  const proposedState = { search: "", level: "all", status: "all", area: "all" };
  const sourceStates = {
    sources: { search: "", filter: "all", page: 1, sortKey: null, sortDirection: "asc" }
  };
  const pendingState = { search: "", owner: "all" };
  const manualWatchState = { search: "", kind: "all" };
  const courtWatchState = { search: "", owner: "all", updatesOnly: false };
  const directiveState = { search: "", administration: "all", status: "all", updatesOnly: false, page: 1, sortKey: "date", sortDirection: "desc" };
  const pageState = { search: "", level: "all", section: "all", sortKey: "section", sortDirection: "asc" };
  const publicationState = { edition: "public-proposal" };
  const publicationLengthState = { sortKey: "estimated_pages", sortDirection: "desc" };
  const assemblyDrafts = new Map();
  const logStates = Object.fromEntries(data.project_logs.map((log) => [
    log.id,
    {
      search: "",
      groupKey: "all",
      sortKey: (log.default_sort || {}).key || (log.columns[0] || {}).key || null,
      sortDirection: (log.default_sort || {}).direction || "asc"
    }
  ]));
  const PAGE_SIZE = 50;
  const pageIndex = new Map(data.page_inventory.map((record) => [record.path, record]));

  data.court_watch_sources = Array.isArray(data.court_watch_sources) ? data.court_watch_sources : [];
  data.presidential_directives = Array.isArray(data.presidential_directives) ? data.presidential_directives : [];
  data.watcher_metadata = data.watcher_metadata || {};
  data.progress = data.progress || {};
  data.integrity = data.integrity || {};
  data.consistency_audit = data.consistency_audit || {};

  const PRINT_LEVEL_LABELS = {
    "public-proposal": "Public proposal edition",
    "legislative-appendix": "Legislative appendix edition",
    "executive-summary": "Executive summary edition"
  };
  const PRINT_LEVEL_ORDER = Object.keys(PRINT_LEVEL_LABELS);
  const printLevelDrafts = new Map();
  const printExclusionDrafts = new Map();
  const PRINT_EXCLUSION_REASONS = [
    "Internal operational log.",
    "Internal drafting template.",
    "Internal source-development record.",
    "Internal workflow or tool documentation.",
    "Internal planning record.",
    "Website-only page."
  ];
  const LIVE_PROGRESS_URL = "https://raw.githubusercontent.com/Thorncrag/ARRP/project-console-data/progress.json";
  const LIVE_INTEGRITY_URL = "https://raw.githubusercontent.com/Thorncrag/ARRP/project-console-data/integrity.json";
  const LIVE_PULL_REQUESTS_URL = "https://api.github.com/repos/Thorncrag/ARRP/pulls?state=open&per_page=100";
  const GITHUB_BLOB_ROOT = "https://github.com/Thorncrag/ARRP/blob/main/";
  const LIVE_SITE_ROOT = "https://thorncrag.github.io/ARRP/";
  const DEVELOPMENT_LEVELS = [
    "Candidate",
    "Admitted / undeveloped",
    "Defined proposal",
    "Developed proposal",
    "Review ready",
    "Release candidate"
  ];
  const reviewSignals = {
    courts: { count: 0, url: "", ids: new Set() },
    directives: {
      count: data.presidential_directives.filter((record) => /^(New|Changed) since/.test(record.review_status || "")).length,
      url: "",
      ids: new Set(data.presidential_directives
        .filter((record) => /^(New|Changed) since/.test(record.review_status || ""))
        .map((record) => record.id))
    }
  };

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

  function compareSortValues(left, right) {
    if (typeof left === "number" && typeof right === "number") return left - right;
    return String(left || "").localeCompare(String(right || ""), undefined, {
      numeric: true,
      sensitivity: "base"
    });
  }

  function sortedRecords(records, state, valueFor) {
    if (!state.sortKey) return [...records];
    const direction = state.sortDirection === "desc" ? -1 : 1;
    return [...records].sort((left, right) => {
      const primary = compareSortValues(valueFor(left, state.sortKey), valueFor(right, state.sortKey));
      if (primary) return primary * direction;
      return compareSortValues(left.id || left.title, right.id || right.title);
    });
  }

  function sortableHeader(label, key, state, render) {
    const active = state.sortKey === key;
    const header = element("th");
    header.setAttribute("aria-sort", active ? (state.sortDirection === "asc" ? "ascending" : "descending") : "none");
    const button = element("button", "sort-button");
    button.type = "button";
    button.append(
      element("span", "", label),
      element("span", "sort-indicator", active ? (state.sortDirection === "asc" ? "▲" : "▼") : "↕")
    );
    button.addEventListener("click", () => {
      if (state.sortKey === key) {
        state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = key;
        state.sortDirection = "asc";
      }
      state.page = 1;
      render();
    });
    header.append(button);
    return header;
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

  function sourceEntry(source, hasUpdate = false) {
    const item = element("article", hasUpdate ? "evidence-record has-update" : "evidence-record");
    const heading = element("div", "evidence-heading");
    const title = source.url
      ? linkButton(source.title || source.id, source.url, true)
      : element("strong", "", text(source.title, source.id));
    heading.append(element("span", "record-id", source.id), title);
    if (hasUpdate) heading.append(element("span", "badge update-badge", "Updated"));
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
      element("span", "badge formal", text(record.development_level, "Development level unavailable")),
      element("span", "badge", text(record.workflow_status, "Workflow status unavailable")),
      element("span", "badge", text(record.area, "Area unassigned")),
      element("span", "badge", text(record.priority, "Priority unassigned"))
    );
    heading.append(badges, element("p", "record-id", record.id), element("h3", "", record.title));
    header.append(heading);

    const history = record.horizon_history || {};
    const summary = element("div", "dossier-grid");
    summary.append(
      dossierSection("Institutional question", history.original_concern || "The Horizon Scan Log does not yet contain a structured concern statement.", "wide"),
      dossierSection("Current intake posture", history.decision || record.workflow_status),
      dossierSection("Possible home and overlap", history.integrated_into || "Not recorded"),
      dossierSection("Why it may be distinct—or not", history.rationale || "Not recorded", "wide"),
      dossierSection("Open questions and next review", record.next_audit),
      dossierSection("Follow-up from intake history", history.follow_up || "Not recorded")
    );

    const lifecycle = element("dl", "candidate-details compact");
    lifecycle.append(
      labeledValue("Development level", record.development_level),
      labeledValue("Workflow status", record.workflow_status),
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
    if (!window.location.hash.startsWith(`#${selected.dataset.tab}`)) {
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
    activateTab(tabs.some((tab) => tab.dataset.tab === requested) ? requested : "progress");
  }

  function activateSectionTab(group, name, focus = false) {
    const tabs = [...document.querySelectorAll(`[role="tab"][data-subtab-group="${group}"]`)];
    const selected = tabs.find((tab) => tab.dataset.subtab === name) || tabs[0];
    tabs.forEach((tab) => {
      const active = tab === selected;
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
      byId(tab.getAttribute("aria-controls")).hidden = !active;
    });
    if (focus) selected.focus();
    if (!window.location.hash.startsWith(`#${group}:${selected.dataset.subtab}`)) {
      window.history.replaceState(null, "", `#${group}:${selected.dataset.subtab}`);
    }
  }

  function initializeSectionTabs(group, fallback) {
    const tabs = [...document.querySelectorAll(`[role="tab"][data-subtab-group="${group}"]`)];
    tabs.forEach((tab, index) => {
      tab.addEventListener("click", () => activateSectionTab(group, tab.dataset.subtab));
      tab.addEventListener("keydown", (event) => {
        let target = null;
        if (event.key === "ArrowRight") target = tabs[(index + 1) % tabs.length];
        if (event.key === "ArrowLeft") target = tabs[(index - 1 + tabs.length) % tabs.length];
        if (event.key === "Home") target = tabs[0];
        if (event.key === "End") target = tabs[tabs.length - 1];
        if (!target) return;
        event.preventDefault();
        activateSectionTab(group, target.dataset.subtab, true);
      });
    });
    const parts = window.location.hash.replace(/^#/, "").split(":");
    const requested = parts[0] === group ? parts[1] : fallback;
    activateSectionTab(group, tabs.some((tab) => tab.dataset.subtab === requested) ? requested : fallback);
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
    if (window.location.hash.startsWith("#sources:watchers")) {
      window.history.replaceState(null, "", `#sources:watchers:${selected.dataset.watcherTab}`);
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
    const requested = parts[0] === "sources" && parts[1] === "watchers" ? parts[2] : "courts";
    activateWatcherTab(tabs.some((tab) => tab.dataset.watcherTab === requested) ? requested : "courts");
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

  function sourceTable(records, state, render) {
    if (!records.length) {
      const empty = element("div", "empty-state compact-empty");
      empty.append(element("h3", "", "No matching sources"), element("p", "", "Adjust the search or filter."));
      return empty;
    }
    const wrapper = element("div", "source-table-wrap");
    const table = element("table", "source-table");
    const head = element("thead");
    const headRow = element("tr");
    [
      ["Source", "source"],
      ["Publisher", "publisher"],
      ["Date / type", "date"],
      ["Associated records", "records"],
      ["Monitor", "monitor"],
      ["Link", "link"]
    ].forEach(([label, key]) => headRow.append(sortableHeader(label, key, state, render)));
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
    });
    const ordered = state.sortKey
      ? sortedRecords(filtered, state, (record, key) => ({
          source: `${record.id} ${record.title}`,
          publisher: record.publisher,
          date: Number.isNaN(Date.parse(record.date)) ? record.date : Date.parse(record.date),
          records: (record.record_ids || []).join(" "),
          monitor: record.monitoring === "Yes" ? 1 : 0,
          link: record.url
        })[key])
      : [...filtered].sort(monitoredSourcesFirst);
    const pages = Math.max(1, Math.ceil(ordered.length / PAGE_SIZE));
    state.page = Math.min(state.page, pages);
    const start = (state.page - 1) * PAGE_SIZE;
    const rerender = () => renderSourceView(name, records, filterField);
    byId(`${name}-visible`).textContent = ordered.length;
    byId(`${name}-table`).replaceChildren(sourceTable(ordered.slice(start, start + PAGE_SIZE), state, rerender));
    pagination(name, ordered.length, state, rerender);
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
      element("span", "badge formal", record.development_level),
      element("span", "badge", record.workflow_status),
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
      return [record.id, record.title, record.kind, record.area, record.development_level, record.workflow_status, record.monitoring_rationale,
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
    const hasUpdate = records.some((record) => reviewSignals.courts.ids.has(record.id));
    const details = element("details", hasUpdate ? "monitoring-issue has-update" : "monitoring-issue");
    const summary = element("summary");
    const identity = element("div", "monitoring-identity");
    identity.append(element("span", "record-id", records[0].owner_id), element("strong", "", label));
    const metadata = element("div", "monitoring-metadata");
    metadata.append(
      ...(hasUpdate ? [element("span", "badge update-badge", "Updated")] : []),
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
    [...records].sort((left, right) => {
      const updateOrder = Number(reviewSignals.courts.ids.has(right.id)) - Number(reviewSignals.courts.ids.has(left.id));
      return updateOrder || monitoredSourcesFirst(left, right);
    }).forEach((source) => list.append(sourceEntry(source, reviewSignals.courts.ids.has(source.id))));
    body.append(list);
    details.append(summary, body);
    return details;
  }

  function renderCourtWatch() {
    const query = courtWatchState.search.toLowerCase();
    const filtered = data.court_watch_sources.filter((record) => {
      if (courtWatchState.owner !== "all" && record.owner_id !== courtWatchState.owner) return false;
      if (courtWatchState.updatesOnly && !reviewSignals.courts.ids.has(record.id)) return false;
      return !query || [sourceSearchText(record), record.owner_id, record.owner_title, record.coverage]
        .filter(Boolean).join(" ").toLowerCase().includes(query);
    });
    const groups = groupRecords(filtered, (record) => `${record.owner_id}::${record.monitoring_group || record.owner_title}`);
    byId("court-watch-visible").textContent = distinctSourceCount(filtered);
    const orderedGroups = [...groups.entries()].sort(([, left], [, right]) => {
      const updateOrder = Number(right.some((record) => reviewSignals.courts.ids.has(record.id)))
        - Number(left.some((record) => reviewSignals.courts.ids.has(record.id)));
      if (updateOrder) return updateOrder;
      return String(left[0].owner_id || "").localeCompare(String(right[0].owner_id || ""));
    });
    byId("court-watch-list").replaceChildren(...orderedGroups.map(([, records]) =>
      courtWatchCard(records[0].monitoring_group || records[0].owner_title, records)
    ));
  }

  function directiveSearchText(record) {
    return [record.id, record.type, record.number, record.title, record.president,
      record.administration, record.review_status, record.arrp_record_ids,
      record.source_ids, record.disposition_rationale]
      .flat().filter(Boolean).join(" ").toLowerCase();
  }

  function directiveTable(records, state, render) {
    if (!records.length) {
      const empty = element("div", "empty-state compact-empty");
      empty.append(element("h3", "", "No matching directives"), element("p", "", "Adjust the search or filter."));
      return empty;
    }
    const wrapper = element("div", "source-table-wrap");
    const table = element("table", "source-table directive-table");
    const head = element("thead");
    const headRow = element("tr");
    [
      ["Directive", "directive"],
      ["Administration", "administration"],
      ["Published", "date"],
      ["Screening status", "status"],
      ["ARRP routing", "routing"],
      ["Link", "link"]
    ].forEach(([label, key]) => headRow.append(sortableHeader(label, key, state, render)));
    head.append(headRow);
    const body = element("tbody");
    records.forEach((record) => {
      const row = element("tr");
      const requiresFollowUp = reviewSignals.directives.ids.has(record.id)
        || /^(New|Changed) since/.test(record.review_status || "");
      if (requiresFollowUp) row.className = "has-update";
      const titleCell = element("td", "source-title-cell");
      titleCell.append(element("span", "record-id", record.number || record.id), element("strong", "", text(record.title, "Untitled directive")));
      const presidentCell = element("td", "", text(record.administration || record.president));
      const dateCell = element("td", "", text(record.published_date || record.signed_date));
      const statusCell = element("td");
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

  function logEntryBody(entry) {
    const body = element("div", "log-entry-body markdown-body");
    // The generated payload uses the same escaped, allowlisted Markdown renderer as candidate dossiers.
    body.innerHTML = entry.details_html || "<p>No additional detail is recorded.</p>";
    return body;
  }

  function projectLogTable(log, entries, state, render) {
    const wrapper = element("div", "source-table-wrap project-log-table-wrap");
    const table = element("table", "source-table project-log-table");
    const head = element("thead");
    const headRow = element("tr");
    log.columns.forEach((column) => headRow.append(sortableHeader(column.label, column.key, state, render)));
    headRow.append(element("th", "log-details-heading", "Complete entry"));
    head.append(headRow);
    const body = element("tbody");
    entries.forEach((entry) => {
      const row = element("tr");
      log.columns.forEach((column) => {
        const cell = element("td");
        const value = element("div", "log-cell-value");
        value.innerHTML = (entry.values_html || {})[column.key] || text((entry.values || {})[column.key]);
        cell.append(value);
        row.append(cell);
      });
      const detailCell = element("td", "log-details-cell");
      const detailId = `log-${log.id}-${entry.id}-details`;
      const toggle = element("button", "log-entry-toggle", "View complete entry");
      toggle.type = "button";
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-controls", detailId);
      detailCell.append(toggle);
      row.append(detailCell);
      body.append(row);

      const expandedRow = element("tr", "log-entry-expanded");
      expandedRow.id = detailId;
      expandedRow.hidden = true;
      const expandedCell = element("td");
      expandedCell.colSpan = log.columns.length + 1;
      expandedCell.append(logEntryBody(entry));
      expandedRow.append(expandedCell);
      body.append(expandedRow);

      toggle.addEventListener("click", () => {
        const expanded = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", String(!expanded));
        toggle.textContent = expanded ? "View complete entry" : "Hide complete entry";
        expandedRow.hidden = expanded;
      });
    });
    table.append(head, body);
    wrapper.append(table);
    return wrapper;
  }

  function populateLogGroupSelect(log) {
    const select = byId(`log-${log.id}-group`);
    const selected = select.value;
    select.replaceChildren();
    const none = element("option", "", "No grouping");
    none.value = "all";
    select.append(none);
    (log.group_options || []).forEach((option) => {
      const node = element("option", "", option.label);
      node.value = option.key;
      select.append(node);
    });
    select.value = [...select.options].some((option) => option.value === selected) ? selected : "all";
  }

  function renderProjectLog(logId) {
    const log = data.project_logs.find((record) => record.id === logId);
    const state = logStates[logId];
    if (!log || !state) return;
    const query = state.search.toLowerCase();
    const filtered = log.entries.filter((entry) => !query || String(entry.search_text || "").toLowerCase().includes(query));
    const render = () => renderProjectLog(logId);
    const ordered = sortedRecords(filtered, state, (entry, key) => (entry.values || {})[key]);
    byId(`log-${logId}-visible`).textContent = ordered.length;
    const container = byId(`log-${logId}-table`);
    if (!ordered.length) {
      container.replaceChildren(element("p", "empty-state", "No log entries match the current filters."));
      return;
    }
    if (state.groupKey === "all") {
      container.replaceChildren(projectLogTable(log, ordered, state, render));
      return;
    }
    const groups = new Map();
    ordered.forEach((entry) => {
      const label = text((entry.values || {})[state.groupKey], "Not recorded");
      if (!groups.has(label)) groups.set(label, []);
      groups.get(label).push(entry);
    });
    const sections = [...groups].map(([label, entries]) => {
      const section = element("section", "log-group");
      const heading = element("h3", "log-group-heading");
      heading.append(element("span", "", label), element("span", "count-pill", String(entries.length)));
      section.append(heading, projectLogTable(log, entries, state, render));
      return section;
    });
    container.replaceChildren(...sections);
  }

  function renderDirectives() {
    const query = directiveState.search.toLowerCase();
    const filtered = data.presidential_directives.filter((record) => {
      if (directiveState.administration !== "all" && record.administration !== directiveState.administration) return false;
      if (directiveState.status !== "all" && record.review_status !== directiveState.status) return false;
      if (directiveState.updatesOnly && !reviewSignals.directives.ids.has(record.id)
          && !/^(New|Changed) since/.test(record.review_status || "")) return false;
      return !query || directiveSearchText(record).includes(query);
    });
    const records = sortedRecords(filtered, directiveState, (record, key) => ({
      directive: `${record.number || record.id} ${record.title}`,
      administration: record.administration || record.president,
      date: record.signed_date || record.published_date,
      status: record.review_status,
      routing: (record.arrp_record_ids || []).join(" "),
      link: record.official_url
    })[key]).sort((left, right) => {
      const updateOrder = Number(reviewSignals.directives.ids.has(right.id) || /^(New|Changed) since/.test(right.review_status || ""))
        - Number(reviewSignals.directives.ids.has(left.id) || /^(New|Changed) since/.test(left.review_status || ""));
      return updateOrder;
    });
    const pages = Math.max(1, Math.ceil(records.length / PAGE_SIZE));
    directiveState.page = Math.min(directiveState.page, pages);
    const start = (directiveState.page - 1) * PAGE_SIZE;
    byId("directive-visible").textContent = records.length;
    byId("directive-table").replaceChildren(directiveTable(records.slice(start, start + PAGE_SIZE), directiveState, renderDirectives));
    pagination("directive", records.length, directiveState, renderDirectives);
  }

  function watcherSummaryCard(label, value, detail) {
    const card = element("article", "watcher-summary-card");
    card.append(element("span", "eyebrow", label), element("strong", "", String(value)), element("p", "", detail));
    return card;
  }

  function setUpdateBadge(id, count) {
    const badge = byId(id);
    badge.textContent = `+${count}`;
    badge.hidden = count === 0;
    badge.setAttribute("aria-label", `${count} new or updated`);
  }

  function renderWatcherUpdateBanner(kind, label) {
    const signal = reviewSignals[kind];
    const banner = byId(`${kind === "courts" ? "court" : "directive"}-watch-update-banner`);
    const count = byId(`${kind === "courts" ? "court" : "directive"}-watch-update-count`);
    const detail = byId(`${kind === "courts" ? "court" : "directive"}-watch-update-detail`);
    const toggle = byId(`${kind === "courts" ? "court" : "directive"}-watch-updated-only`);
    const review = byId(`${kind === "courts" ? "court" : "directive"}-watch-review-pr`);
    const availableIds = kind === "courts"
      ? new Set(data.court_watch_sources.map((record) => record.id))
      : new Set(data.presidential_directives.map((record) => record.id));
    const identifiable = [...signal.ids].filter((id) => availableIds.has(id)).length;
    banner.hidden = signal.count === 0;
    count.textContent = signal.count;
    detail.textContent = identifiable
      ? `${identifiable} ${label}${identifiable === 1 ? " is" : "s are"} marked below and shown first.`
      : "The update proposal is available for review, but its records are not yet present in this checked-in view.";
    toggle.hidden = identifiable === 0;
    review.hidden = !signal.url;
    if (signal.url) review.href = signal.url;
  }

  function formalCandidatesAwaitingReview() {
    return data.active_horizon_records.filter((record) => !/deferred|parked/i.test(record.workflow_status || ""));
  }

  function navigateToConsoleTarget(target) {
    const parts = target.split(":");
    activateTab(parts[0]);
    if (parts[0] === "candidates" && parts[1]) activateSectionTab("candidates", parts[1]);
    if (parts[0] === "sources" && parts[1]) activateSectionTab("sources", parts[1]);
    if (parts[0] === "sources" && parts[1] === "watchers" && parts[2]) activateWatcherTab(parts[2]);
    byId(`panel-${parts[0]}`).scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function actionItemCard({ label, count, detail, target, updateCount = 0, externalUrl = "" }) {
    const card = element("article", `action-item-card${updateCount ? " has-update" : ""}`);
    const heading = element("div", "action-item-heading");
    heading.append(element("h3", "", label), element("strong", "action-item-count", String(count)));
    if (updateCount) heading.append(element("span", "tab-update-count action-update-count", `+${updateCount} new/updated`));
    card.append(heading, element("p", "", detail));
    const actions = element("div", "action-item-links");
    const open = element("a", "record-link secondary", "Open full view →");
    open.href = `#${target}`;
    open.addEventListener("click", (event) => {
      event.preventDefault();
      navigateToConsoleTarget(target);
    });
    actions.append(open);
    if (externalUrl) {
      const review = element("a", "record-link", "Review update PR ↗");
      review.href = externalUrl;
      review.target = "_blank";
      review.rel = "noopener noreferrer";
      actions.append(review);
    }
    card.append(actions);
    return card;
  }

  function renderActionItems() {
    const formal = formalCandidatesAwaitingReview().length;
    const preliminary = data.records.length;
    const pending = data.pending_sources.length;
    const courtUpdates = reviewSignals.courts.count;
    const directiveUpdates = reviewSignals.directives.count;
    const total = formal + preliminary + pending + courtUpdates + directiveUpdates;
    const newOrUpdated = preliminary + courtUpdates + directiveUpdates;
    byId("tab-actions-count").textContent = total;
    byId("action-items-note").textContent = total
      ? `${total} item${total === 1 ? "" : "s"} awaiting review or a decision; ${newOrUpdated} new or updated.`
      : "No items currently await review or a decision.";
    byId("action-items-grid").replaceChildren(
      actionItemCard({
        label: "Proposed candidates",
        count: formal,
        detail: "Open candidate records awaiting admission, merger, rejection, or another substantive decision; deferred records are excluded.",
        target: "candidates:formal"
      }),
      actionItemCard({
        label: "Preliminary candidates",
        count: preliminary,
        updateCount: preliminary,
        detail: preliminary ? "New synthesized institutional questions awaiting human intake review." : "No preliminary intake questions await review.",
        target: "candidates:preliminary"
      }),
      actionItemCard({
        label: "Pending source routing",
        count: pending,
        detail: pending ? "Sources still requiring a choice among plausible project destinations." : "No source-routing decisions are pending.",
        target: "sources:pending"
      }),
      actionItemCard({
        label: "Court-case updates",
        count: courtUpdates,
        updateCount: courtUpdates,
        detail: courtUpdates ? `${courtUpdates} monitored source update${courtUpdates === 1 ? "" : "s"} await review.` : "No unresolved case-watcher update is currently reported.",
        target: "sources:watchers:courts",
        externalUrl: reviewSignals.courts.url
      }),
      actionItemCard({
        label: "Presidential-directive updates",
        count: directiveUpdates,
        updateCount: directiveUpdates,
        detail: directiveUpdates ? `${directiveUpdates} new or changed directive${directiveUpdates === 1 ? "" : "s"} await screening.` : "No new or changed directive currently awaits screening.",
        target: "sources:watchers:directives",
        externalUrl: reviewSignals.directives.url
      })
    );
  }

  function parseCount(body, label) {
    const match = String(body || "").match(new RegExp(`${label}:\\s*\\*\\*(\\d+)\\*\\*`, "i"));
    return match ? Number(match[1]) : 0;
  }

  function renderReviewSignals() {
    const botUpdates = reviewSignals.courts.count + reviewSignals.directives.count;
    setUpdateBadge("tab-candidates-update", data.records.length);
    setUpdateBadge("tab-sources-update", botUpdates);
    setUpdateBadge("source-watchers-update", botUpdates);
    setUpdateBadge("court-watch-update", reviewSignals.courts.count);
    setUpdateBadge("directive-watch-update", reviewSignals.directives.count);
    renderWatcherUpdateBanner("courts", "source");
    renderWatcherUpdateBanner("directives", "directive");
    renderCourtWatch();
    renderDirectives();
    renderActionItems();
  }

  async function refreshBotReviewSignals() {
    try {
      const response = await fetch(LIVE_PULL_REQUESTS_URL, {
        cache: "no-store",
        headers: { Accept: "application/vnd.github+json" }
      });
      if (!response.ok) throw new Error(`GitHub returned ${response.status}`);
      const pullRequests = await response.json();
      const court = pullRequests.find((record) => record.head?.ref === "bot/case-monitor-updates");
      const directives = pullRequests.find((record) => record.head?.ref === "automation/presidential-directives-monitor");
      if (court) {
        const affectedSources = new Set(String(court.body || "").match(/\bSRC-\d+\b/g) || []);
        reviewSignals.courts.count = affectedSources.size || 1;
        reviewSignals.courts.url = court.html_url || "";
        reviewSignals.courts.ids = affectedSources;
      } else {
        reviewSignals.courts.count = 0;
        reviewSignals.courts.url = "";
        reviewSignals.courts.ids = new Set();
      }
      if (directives) {
        const proposed = parseCount(directives.body, "Added directives")
          + parseCount(directives.body, "Changed directives");
        reviewSignals.directives.count = Math.max(reviewSignals.directives.count, proposed || 1);
        reviewSignals.directives.url = directives.html_url || "";
      } else {
        reviewSignals.directives.url = "";
      }
      byId("action-items-live-note").textContent = "Bot-update counts were refreshed from the repository. Other counts come from the checked-in console data.";
      renderReviewSignals();
    } catch (_error) {
      byId("action-items-live-note").textContent = "Live bot-update status could not be refreshed; checked-in queue counts remain available.";
    }
  }

  function progressMetric(label, value, detail) {
    return watcherSummaryCard(label, value, detail);
  }

  function renderProgressTrajectory(snapshot) {
    const host = byId("progress-trajectory");
    const history = (snapshot.history || [])
      .filter((point) => /^\d{4}-\d{2}-\d{2}$/.test(point.date || "") && Number.isFinite(Number(point.ready)))
      .sort((left, right) => left.date.localeCompare(right.date));
    const goal = snapshot.goal || {};
    const metrics = snapshot.metrics || {};
    const startText = goal.historyStartDate || history[0]?.date;
    const endText = goal.targetDate;
    if (!history.length || !startText || !endText) {
      host.replaceChildren(element("p", "muted", "Trajectory data unavailable."));
      return;
    }

    const start = Date.parse(`${startText}T00:00:00Z`);
    const end = Date.parse(`${endText}T00:00:00Z`);
    const width = 960;
    const height = 310;
    const margin = { top: 22, right: 28, bottom: 42, left: 58 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    const maximum = Math.max(1, Number(metrics.total) || 0, ...history.map((point) => Number(point.ready) || 0));
    const x = (dateText) => margin.left + ((Date.parse(`${dateText}T00:00:00Z`) - start) / Math.max(1, end - start)) * innerWidth;
    const y = (value) => margin.top + innerHeight - (Number(value) / maximum) * innerHeight;
    const ns = "http://www.w3.org/2000/svg";
    const svgElement = (name, attributes = {}) => {
      const node = document.createElementNS(ns, name);
      Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, String(value)));
      return node;
    };
    const svgText = (content, attributes) => {
      const node = svgElement("text", attributes);
      node.textContent = content;
      return node;
    };
    const svg = svgElement("svg", { viewBox: `0 0 ${width} ${height}`, "aria-hidden": "true", focusable: "false" });

    [0, .25, .5, .75, 1].forEach((ratio) => {
      const value = Math.round(maximum * ratio);
      const rowY = y(value);
      svg.append(
        svgElement("line", { x1: margin.left, y1: rowY, x2: width - margin.right, y2: rowY, class: "progress-grid-line" }),
        svgText(String(value), { x: margin.left - 10, y: rowY + 4, class: "progress-axis-label", "text-anchor": "end" })
      );
    });

    const baselineDate = goal.baselineDate || startText;
    const baselineReady = Number(goal.baselineReady) || 0;
    svg.append(svgElement("line", {
      x1: x(baselineDate), y1: y(baselineReady), x2: x(endText), y2: y(maximum), class: "progress-target-line"
    }));
    const actualPoints = history
      .filter((point) => Date.parse(`${point.date}T00:00:00Z`) >= start && Date.parse(`${point.date}T00:00:00Z`) <= end)
      .map((point) => `${x(point.date)},${y(point.ready)}`)
      .join(" ");
    if (actualPoints) svg.append(svgElement("polyline", { points: actualPoints, class: "progress-actual-line" }));
    const latest = history[history.length - 1];
    svg.append(svgElement("circle", { cx: x(latest.date), cy: y(latest.ready), r: 5, class: "progress-actual-point" }));

    const labelDate = (value) => new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));
    const asOf = snapshot.asOf || latest.date;
    [[startText, "start"], [asOf, "middle"], [endText, "end"]].forEach(([value, anchor]) => {
      svg.append(svgText(labelDate(value), { x: x(value), y: height - 12, class: "progress-axis-label", "text-anchor": anchor }));
    });
    host.replaceChildren(svg);
    host.setAttribute("aria-label", `Review Ready trajectory from ${startText} through ${endText}; ${metrics.ready || 0} of ${metrics.total || 0} eligible proposals are currently Review Ready.`);
  }

  function proposalLiveUrl(record) {
    let path = String(record.canonicalRecord || "").trim();
    path = path.replace(/^https:\/\/github\.com\/Thorncrag\/ARRP\/blob\/(?:main|master)\//, "");
    if (!path || !path.endsWith(".md")) return "";
    if (path.endsWith("/README.md")) path = path.slice(0, -"README.md".length);
    else path = `${path.slice(0, -3)}/`;
    return `${LIVE_SITE_ROOT}${path}`;
  }

  function developmentBoardCard(record) {
    const card = element("article", "development-card");
    card.title = record.title || record.identifier;
    const identity = element("div", "development-card-identity");
    const workflow = element("span", "workflow-dot", "●");
    workflow.title = `Workflow: ${text(record.workflowStatus, "Not recorded")}`;
    workflow.setAttribute("aria-label", workflow.title);
    identity.append(
      element("strong", "", record.identifier),
      workflow,
      element("span", "development-score", record.score == null || Number(record.score) <= 0 ? "Score —" : `Score ${record.score}`)
    );
    const links = element("div", "development-card-links");
    const liveUrl = proposalLiveUrl(record);
    if (liveUrl) links.append(linkButton("Live", liveUrl, true));
    if (record.url) links.append(linkButton("Issue", record.url, true));
    card.append(identity, links);
    return card;
  }

  function renderDevelopmentBoard(snapshot) {
    const proposals = Array.isArray(snapshot.proposals) ? snapshot.proposals : [];
    const candidates = data.active_horizon_records.map((record) => ({
      identifier: record.id,
      title: record.title,
      developmentLevel: record.development_level,
      workflowStatus: record.workflow_status,
      score: null,
      canonicalRecord: "",
      url: record.issue_url
    }));
    const records = [...candidates, ...proposals];
    const recognized = new Set(DEVELOPMENT_LEVELS);
    const unassigned = records.filter((record) => !recognized.has(record.developmentLevel));
    const board = byId("development-board");
    board.replaceChildren(...DEVELOPMENT_LEVELS.map((level) => {
      const column = element("section", "development-column");
      const stageRecords = records
        .filter((record) => record.developmentLevel === level)
        .sort((left, right) => left.identifier.localeCompare(right.identifier));
      const heading = element("div", "development-column-heading");
      heading.append(element("h4", "", level), element("span", "count-pill", stageRecords.length));
      const list = element("div", "development-card-list");
      list.replaceChildren(...stageRecords.map(developmentBoardCard));
      column.append(heading, list);
      return column;
    }));
    const warning = byId("development-board-warning");
    warning.hidden = unassigned.length === 0;
    warning.textContent = unassigned.length
      ? `${unassigned.length} record${unassigned.length === 1 ? " has" : "s have"} no recognized Development level and cannot be placed on the board.`
      : "";
  }

  function renderProgress() {
    const snapshot = data.progress || {};
    const metrics = snapshot.metrics || {};
    const goal = snapshot.goal || {};
    const areas = Array.isArray(snapshot.areas) ? snapshot.areas : [];
    const backlog = Array.isArray(snapshot.backlog) ? snapshot.backlog : [];
    byId("progress-as-of").textContent = snapshot.asOf || "Unavailable";
    byId("tab-progress-count").textContent = metrics.ready ?? 0;

    if (!Object.keys(metrics).length) {
      byId("progress-summary-grid").replaceChildren(
        progressMetric("Progress unavailable", "—", "Refresh the Project Console progress data and rebuild this console.")
      );
      byId("progress-status-note").textContent = "No Project Console progress snapshot is available.";
      renderProgressTrajectory(snapshot);
      byId("progress-area-list").replaceChildren(element("p", "muted", "Area data unavailable."));
      byId("progress-backlog-list").replaceChildren(element("p", "muted", "Backlog data unavailable."));
      byId("development-board").replaceChildren(element("p", "muted", "Development-level data unavailable."));
      return;
    }

    byId("progress-summary-grid").replaceChildren(
      progressMetric("Review Ready", metrics.ready, `of ${metrics.total} eligible proposals`),
      progressMetric("Remaining", metrics.remaining, `by ${goal.targetDate || "the target date"}`),
      progressMetric("Required pace", `${metrics.requiredPerWeek} / week`, "to meet the official target"),
      progressMetric("Rolling pace", metrics.rollingWeeklyVelocity == null ? "Establishing" : `${metrics.rollingWeeklyVelocity} / week`, "net Review Ready attainment"),
      progressMetric("Forecast", metrics.forecastLabel || "Establishing", metrics.trackStatus || "Schedule status unavailable")
    );
    const percent = Math.max(0, Math.min(100, Number(metrics.percentReady) || 0));
    byId("progress-status-note").textContent = `${metrics.trackStatus || "Status unavailable"} · ${percent}% of the current active portfolio is Review Ready or higher · ${metrics.scheduleVariance >= 0 ? `${metrics.scheduleVariance} ahead of` : `${Math.abs(metrics.scheduleVariance)} behind`} the required path.`;
    byId("progress-fill").style.width = `${percent}%`;
    byId("progress-track").setAttribute("aria-valuenow", String(percent));
    renderProgressTrajectory(snapshot);
    renderDevelopmentBoard(snapshot);

    const areaRows = [...areas].sort((left, right) => right.remaining - left.remaining || left.area.localeCompare(right.area));
    byId("progress-area-list").replaceChildren(...areaRows.map((area) => {
      const row = element("div", "progress-area-row");
      const identity = element("div", "progress-area-identity");
      identity.append(element("strong", "", area.area), element("span", "", `${area.ready} of ${area.total} ready`));
      const bar = element("div", "mini-progress-track");
      const fill = element("span");
      fill.style.width = `${Math.max(0, Math.min(100, Number(area.percentReady) || 0))}%`;
      bar.append(fill);
      row.append(identity, bar, element("span", "progress-area-percent", `${area.percentReady}%`));
      return row;
    }));

    const closest = backlog.filter((record) => !record.ready).slice(0, 15);
    byId("progress-backlog-list").replaceChildren(...closest.map((record) => {
      const row = element("article", "progress-backlog-row");
      const heading = element("div");
      heading.append(
        inlineLink(record.identifier, record.url),
        element("span", "", `${record.area} · ${record.developmentLevel} · ${record.workflowStatus}`)
      );
      const score = element("strong", "", record.score == null ? "Unscored" : String(record.score));
      row.append(heading, score);
      if (record.nextAudit) row.append(element("p", "", record.nextAudit));
      return row;
    }));
  }

  async function refreshLiveProgress() {
    try {
      const response = await fetch(LIVE_PROGRESS_URL, { cache: "no-store" });
      if (!response.ok) return;
      const snapshot = await response.json();
      if (!snapshot || typeof snapshot !== "object" || !snapshot.metrics
          || !Array.isArray(snapshot.proposals) || Number(snapshot.schemaVersion || 0) < 2) return;
      data.progress = snapshot;
      renderProgress();
    } catch (_error) {
      // The embedded snapshot remains usable offline and from file://.
    }
  }

  function integrityMetric(label, value, detail) {
    const card = element("article", "integrity-metric");
    card.append(element("span", "", label), element("strong", "", String(value)), element("p", "", detail));
    return card;
  }

  function renderConsistencyAudit() {
    const audit = data.consistency_audit || {};
    const entries = Array.isArray(audit.entries) ? audit.entries : [];
    const overview = byId("consistency-audit-overview");
    const host = byId("consistency-audit-findings");
    const link = byId("consistency-audit-link");
    if (audit.source_url) link.href = audit.source_url;
    if (!entries.length) {
      overview.replaceChildren();
      host.replaceChildren(element("p", "muted", "No explanatory consistency-audit record is embedded in this Console build."));
      return;
    }
    overview.replaceChildren(
      integrityMetric("Files examined", Number(audit.records_checked || 0).toLocaleString(), "tracked repository files"),
      integrityMetric("Explanatory findings", entries.length.toLocaleString(), "corrected areas and disclosed limits"),
      integrityMetric("Audit status", audit.status || "Current", audit.last_checkpoint || "Current repository checkpoint")
    );
    host.replaceChildren(...entries.map((entry, index) => {
      const panel = element("details", "consistency-audit-finding");
      panel.open = index === 0;
      const summary = element("summary");
      const disposition = entry.disposition || "Open";
      const dispositionClass = /^corrected$/i.test(disposition) ? "ready" : /^partially/i.test(disposition) ? "warning" : "blocker";
      summary.append(element("span", "", entry.title || "Audit finding"), element("span", `finding-level ${dispositionClass}`, disposition));
      panel.append(summary);
      const body = element("div", "consistency-audit-body");
      [
        ["Problem", entry.problem],
        ["Why it mattered", entry.why_it_mattered],
        ["Correction", entry.correction],
        ["Effect", entry.effect],
        ["Remaining work", entry.remaining_work]
      ].forEach(([label, value]) => {
        if (!value) return;
        const field = element("section", "consistency-audit-field");
        field.append(element("h4", "", label), element("p", "", value));
        body.append(field);
      });
      panel.append(body);
      return panel;
    }));
  }

  function renderIntegrity(feed = data.integrity) {
    const current = feed && typeof feed.current === "object" ? feed.current : {};
    const counts = current.counts || {};
    const findings = Array.isArray(current.findings) ? current.findings : [];
    const history = Array.isArray(feed.history) ? feed.history : [];
    const findingCount = Number(counts.findings) || findings.length;
    byId("tab-integrity-count").textContent = findingCount;
    setUpdateBadge("tab-integrity-update", findingCount);
    byId("integrity-as-of").textContent = current.generated_at ? formatDate(current.generated_at) : "Not yet run";
    const status = byId("integrity-status");
    status.className = `status-badge ${findingCount ? "needs-review" : current.result === "clean" ? "ready" : ""}`.trim();
    status.textContent = current.result === "clean" ? "No findings" : findingCount ? `${findingCount} finding${findingCount === 1 ? "" : "s"}` : "Awaiting first run";
    byId("integrity-metrics").replaceChildren(
      integrityMetric("Errors", Number(counts.errors) || 0, "rule violations requiring correction"),
      integrityMetric("Warnings", Number(counts.warnings) || 0, "credible drift requiring review"),
      integrityMetric("Issue pages", Number(counts.issue_pages) || 0, "included in the structural pass"),
      integrityMetric("Proposal pages", Number(counts.proposal_pages) || 0, "included in the structural pass"),
      integrityMetric("Run time", current.duration_seconds == null ? "—" : `${current.duration_seconds}s`, "automated inspection duration")
    );
    renderConsistencyAudit();

    const grouped = new Map();
    findings.forEach((finding) => {
      const category = finding.category || "Project structure";
      if (!grouped.has(category)) grouped.set(category, []);
      grouped.get(category).push(finding);
    });
    const findingHost = byId("integrity-findings");
    if (!findings.length) {
      const empty = element("div", "empty-state compact-empty");
      empty.append(element("span", "", "✓"), element("h3", "", current.generated_at ? "No automated findings" : "No run data yet"), element("p", "", current.generated_at ? "The latest repeatable integrity checks completed without a reported error or warning." : "Run the integrity workflow manually or wait for its next scheduled pass."));
      findingHost.replaceChildren(empty);
    } else {
      findingHost.replaceChildren(...[...grouped.entries()].sort().map(([category, items]) => {
        const panel = element("details", "integrity-finding-group");
        panel.open = true;
        const summary = element("summary");
        summary.append(element("span", "", category), element("span", "panel-count", String(items.length)));
        panel.append(summary);
        const list = element("div", "integrity-finding-list");
        items.forEach((finding) => {
          const record = element("article", `integrity-finding ${finding.severity || "warning"}`);
          const heading = element("div", "integrity-finding-heading");
          heading.append(element("span", `finding-level ${finding.severity || "warning"}`, finding.severity || "warning"));
          if (finding.path) heading.append(inlineLink(finding.path, `${GITHUB_BLOB_ROOT}${finding.path}`));
          record.append(heading, element("p", "", finding.message || "Unspecified integrity finding"));
          list.append(record);
        });
        panel.append(list);
        return panel;
      }));
    }

    byId("integrity-history").replaceChildren(...history.map((run) => {
      const row = element("article", "integrity-history-row");
      const runCounts = run.counts || {};
      row.append(element("strong", "", formatDate(run.generated_at)), element("span", run.result === "clean" ? "ready" : "needs-review", run.result === "clean" ? "Clean" : `${Number(runCounts.findings) || 0} findings`));
      row.append(element("p", "", `${Number(runCounts.errors) || 0} errors · ${Number(runCounts.warnings) || 0} warnings · ${run.duration_seconds == null ? "duration unavailable" : `${run.duration_seconds}s`}`));
      return row;
    }));
    byId("integrity-scope").replaceChildren(...(Array.isArray(current.scope) ? current.scope : []).map((item) => element("li", "", item)));
  }

  async function refreshLiveIntegrity() {
    try {
      const response = await fetch(LIVE_INTEGRITY_URL, { cache: "no-store" });
      if (!response.ok) throw new Error(`GitHub returned ${response.status}`);
      const feed = await response.json();
      if (!feed || typeof feed !== "object" || !feed.current) return;
      data.integrity = feed;
      renderIntegrity(feed);
      byId("integrity-live-note").textContent = "Integrity findings and run history were refreshed from the repository data branch.";
    } catch (_error) {
      byId("integrity-live-note").textContent = "Live integrity data could not be refreshed; the checked-in snapshot remains available.";
    }
  }

  function pageSearchText(record) {
    return [record.title, record.path, record.section, ...effectivePrintLevels(record),
      ...effectivePrintLevels(record).map((level) => PRINT_LEVEL_LABELS[level]),
      effectivePublicationDisposition(record), effectivePrintExclusionReason(record)]
      .filter(Boolean).join(" ").toLowerCase();
  }

  function orderedPrintLevels(levels) {
    return [...new Set(levels)].sort((left, right) => {
      const leftIndex = PRINT_LEVEL_ORDER.indexOf(left);
      const rightIndex = PRINT_LEVEL_ORDER.indexOf(right);
      return (leftIndex < 0 ? PRINT_LEVEL_ORDER.length : leftIndex)
        - (rightIndex < 0 ? PRINT_LEVEL_ORDER.length : rightIndex)
        || left.localeCompare(right);
    });
  }

  function effectivePrintLevels(record) {
    return printLevelDrafts.has(record.path)
      ? [...printLevelDrafts.get(record.path)]
      : orderedPrintLevels(record.print_levels || []);
  }

  function effectivePrintStatus(record) {
    return printExclusionDrafts.has(record.path)
      ? printExclusionDrafts.get(record.path).status
      : (record.print_status || "");
  }

  function effectivePrintExclusionReason(record) {
    return printExclusionDrafts.has(record.path)
      ? printExclusionDrafts.get(record.path).reason
      : (record.print_exclusion_reason || "");
  }

  function effectivePublicationDisposition(record) {
    const levels = effectivePrintLevels(record);
    const excluded = effectivePrintStatus(record) === "excluded";
    if (levels.length && excluded) return "conflict";
    if (levels.length) return "included";
    if (excluded) return "excluded";
    return "unclassified";
  }

  function resetPrintDispositionDraft(record) {
    printLevelDrafts.delete(record.path);
    printExclusionDrafts.delete(record.path);
    renderPrintWorkspace();
  }

  function renderPrintWorkspace() {
    renderPrintSummary();
    renderPrintChangeToolbar();
    renderActionItems();
    renderPages();
    renderEditionAnalysis();
    renderDocumentBuilder();
  }

  function setPrintLevelDraft(record, levels) {
    const original = orderedPrintLevels(record.print_levels || []);
    const draft = orderedPrintLevels(levels);
    if (original.join("\u0000") === draft.join("\u0000")) printLevelDrafts.delete(record.path);
    else printLevelDrafts.set(record.path, draft);
    if (draft.length) {
      if ((record.print_status || "") === "excluded") {
        printExclusionDrafts.set(record.path, { status: "", reason: "" });
      } else {
        printExclusionDrafts.delete(record.path);
      }
    }
    renderPrintWorkspace();
  }

  function stagePrintExclusion(record, reason) {
    printLevelDrafts.set(record.path, []);
    printExclusionDrafts.set(record.path, { status: "excluded", reason });
    renderPrintWorkspace();
  }

  function clearPrintExclusion(record) {
    printExclusionDrafts.set(record.path, { status: "", reason: "" });
    renderPrintWorkspace();
  }

  function printLevelChanges() {
    return data.page_inventory.flatMap((record) => {
      const original = orderedPrintLevels(record.print_levels || []);
      const draft = effectivePrintLevels(record);
      const add = draft.filter((level) => !original.includes(level));
      const remove = original.filter((level) => !draft.includes(level));
      const originalStatus = record.print_status || "";
      const originalReason = record.print_exclusion_reason || "";
      const status = effectivePrintStatus(record);
      const reason = effectivePrintExclusionReason(record);
      return add.length || remove.length || originalStatus !== status || originalReason !== reason
        ? [{ path: record.path, title: record.title, add, remove,
          print_status: status || null, print_exclusion_reason: reason || null,
          clear_exclusion: originalStatus === "excluded" && status !== "excluded" }]
        : [];
    });
  }

  function exportPrintLevelChanges() {
    const changes = printLevelChanges();
    if (!changes.length) return;
    const payload = {
      schema_version: 2,
      purpose: "ARRP publication-disposition metadata changes",
      exported_at: new Date().toISOString(),
      changes
    };
    const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const download = document.createElement("a");
    download.href = url;
    download.download = `arrp-print-level-changes-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.append(download);
    download.click();
    download.remove();
    URL.revokeObjectURL(url);
  }

  function renderPrintChangeToolbar() {
    const changes = printLevelChanges();
    const operationCount = changes.length;
    byId("print-change-count").textContent = operationCount;
    byId("export-print-changes").disabled = operationCount === 0;
    byId("reset-print-changes").disabled = operationCount === 0;
    const renderedChanges = changes.map((change) => {
      const item = element("div", "print-change-item");
      const summary = element("div");
      summary.append(element("strong", "", change.title), element("code", "page-path", change.path));
      const details = [];
      if (change.add.length) details.push(`Add: ${change.add.map((level) => PRINT_LEVEL_LABELS[level] || level).join(", ")}`);
      if (change.remove.length) details.push(`Remove: ${change.remove.map((level) => PRINT_LEVEL_LABELS[level] || level).join(", ")}`);
      if (change.print_status === "excluded") details.push(`Exclude: ${change.print_exclusion_reason}`);
      else if (change.clear_exclusion) details.push("Clear print exclusion");
      summary.append(element("span", "", details.join(" · ")));
      const undo = element("button", "secondary", "Undo page changes");
      undo.type = "button";
      undo.addEventListener("click", () => {
        const record = pageIndex.get(change.path);
        if (record) resetPrintDispositionDraft(record);
      });
      item.append(summary, undo);
      return item;
    });
    if (!renderedChanges.length) {
      renderedChanges.push(element("p", "print-change-empty", "No print-level changes are staged."));
    }
    byId("print-change-list").replaceChildren(...renderedChanges);
  }

  function pageTable(records, state, render) {
    if (!records.length) {
      const empty = element("div", "empty-state compact-empty");
      empty.append(element("h3", "", "No matching pages"), element("p", "", "Adjust the search or filters."));
      return empty;
    }
    const wrapper = element("div", "source-table-wrap");
    const table = element("table", "source-table page-inventory-table");
    const head = element("thead");
    const headRow = element("tr");
    [
      ["Page", "page"],
      ["Project section", "section"],
      ["Publication disposition", "levels"],
      ["Link", "link"]
    ].forEach(([label, key]) => headRow.append(sortableHeader(label, key, state, render)));
    head.append(headRow);
    const body = element("tbody");
    records.forEach((record) => {
      const row = element("tr");
      const titleCell = element("td", "source-title-cell");
      titleCell.append(element("strong", "", record.title), element("code", "page-path", record.path));
      const sectionCell = element("td", "", record.section);
      const levelsCell = element("td", "print-level-badges");
      const originalLevels = orderedPrintLevels(record.print_levels || []);
      const levels = effectivePrintLevels(record);
      const disposition = effectivePublicationDisposition(record);
      if (disposition === "excluded") {
        const badge = element("span", "badge print-disposition excluded", "Excluded");
        const clear = element("button", "print-level-remove", "×");
        clear.type = "button";
        clear.title = "Stage removal of the print exclusion";
        clear.setAttribute("aria-label", `Remove print exclusion from ${record.title}`);
        clear.addEventListener("click", () => clearPrintExclusion(record));
        badge.append(clear);
        levelsCell.append(badge, element("span", "print-exclusion-reason", effectivePrintExclusionReason(record) || "Reason not recorded"));
      } else if (disposition === "unclassified") {
        levelsCell.append(element("span", "badge print-disposition unclassified", "Unclassified — action required"));
      } else if (disposition === "conflict") {
        levelsCell.append(element("span", "badge print-disposition conflict", "Conflicting metadata — action required"));
      }
      levels.forEach((level) => {
        const badge = element("span", `badge print-level ${level}${originalLevels.includes(level) ? "" : " staged-addition"}`);
        badge.append(document.createTextNode(PRINT_LEVEL_LABELS[level] || level));
        const remove = element("button", "print-level-remove", "×");
        remove.type = "button";
        remove.title = `Stage removal of ${PRINT_LEVEL_LABELS[level] || level}`;
        remove.setAttribute("aria-label", `Remove ${PRINT_LEVEL_LABELS[level] || level} from ${record.title}`);
        remove.addEventListener("click", () => setPrintLevelDraft(record, levels.filter((value) => value !== level)));
        badge.append(remove);
        levelsCell.append(badge);
      });
      const missingLevels = PRINT_LEVEL_ORDER.filter((level) => !levels.includes(level));
      if (missingLevels.length) {
        const add = element("select", "print-level-add");
        add.setAttribute("aria-label", `Add print level to ${record.title}`);
        const prompt = element("option", "", "Add print level…");
        prompt.value = "";
        add.append(prompt);
        missingLevels.forEach((level) => {
          const option = element("option", "", PRINT_LEVEL_LABELS[level] || level);
          option.value = level;
          add.append(option);
        });
        add.addEventListener("change", () => {
          if (add.value) setPrintLevelDraft(record, [...levels, add.value]);
        });
        levelsCell.append(add);
      }
      const exclude = element("select", "print-level-add print-exclusion-add");
      exclude.setAttribute("aria-label", `Exclude ${record.title} from print`);
      const excludePrompt = element("option", "", "Exclude from print…");
      excludePrompt.value = "";
      exclude.append(excludePrompt);
      PRINT_EXCLUSION_REASONS.forEach((reason) => {
        const option = element("option", "", reason.replace(/\.$/, ""));
        option.value = reason;
        exclude.append(option);
      });
      exclude.addEventListener("change", () => {
        if (exclude.value) stagePrintExclusion(record, exclude.value);
      });
      levelsCell.append(exclude);
      const linkCell = element("td", "source-link-cell");
      linkCell.append(inlineLink("Open ↗", record.github_url));
      row.append(titleCell, sectionCell, levelsCell, linkCell);
      body.append(row);
    });
    table.append(head, body);
    wrapper.append(table);
    return wrapper;
  }

  function renderPrintSummary() {
    const summary = byId("print-level-summary");
    const cards = [];
    const includedCount = data.page_inventory.filter((record) => effectivePublicationDisposition(record) === "included").length;
    const includedCard = element("button", "print-level-card disposition-included");
    includedCard.type = "button";
    includedCard.append(element("strong", "", String(includedCount)), element("span", "", "Included in print"));
    includedCard.addEventListener("click", () => {
      pageState.level = "__included";
      byId("pages-level").value = "__included";
      renderPages();
    });
    cards.push(includedCard);
    cards.push(...Object.entries(PRINT_LEVEL_LABELS).map(([level, label]) => {
      const count = data.page_inventory.filter((record) => effectivePrintLevels(record).includes(level)).length;
      const card = element("button", "print-level-card");
      card.type = "button";
      card.append(element("strong", "", String(count)), element("span", "", label));
      card.addEventListener("click", () => {
        pageState.level = level;
        byId("pages-level").value = level;
        renderPages();
      });
      return card;
    }));
    [
      ["excluded", "Explicitly excluded"],
      ["unclassified", "Unclassified — action required"],
      ["conflict", "Metadata conflicts — action required"]
    ].forEach(([disposition, label]) => {
      const count = data.page_inventory.filter((record) => effectivePublicationDisposition(record) === disposition).length;
      const card = element("button", `print-level-card disposition-${disposition}`);
      card.type = "button";
      card.append(element("strong", "", String(count)), element("span", "", label));
      card.addEventListener("click", () => {
        pageState.level = `__${disposition}`;
        byId("pages-level").value = `__${disposition}`;
        renderPages();
      });
      cards.push(card);
    });
    summary.replaceChildren(...cards);
  }

  function renderPages() {
    const query = pageState.search.toLowerCase();
    const filtered = data.page_inventory.filter((record) => {
      if (pageState.level.startsWith("__") && effectivePublicationDisposition(record) !== pageState.level.slice(2)) return false;
      if (pageState.level !== "all" && !pageState.level.startsWith("__") && !effectivePrintLevels(record).includes(pageState.level)) return false;
      if (pageState.section !== "all" && record.section !== pageState.section) return false;
      return !query || pageSearchText(record).includes(query);
    });
    const records = sortedRecords(filtered, pageState, (record, key) => ({
      page: `${record.title} ${record.path}`,
      section: `${record.section} ${record.title}`,
      levels: `${effectivePublicationDisposition(record)} ${effectivePrintLevels(record).join(" ")} ${effectivePrintExclusionReason(record)}`,
      link: record.github_url
    })[key]);
    byId("pages-visible").textContent = records.length;
    byId("pages-table").replaceChildren(pageTable(records, pageState, renderPages));
  }

  function publicationEditions() {
    return data.publication.manifest.editions || [];
  }

  function publicationEdition(editionId = publicationState.edition) {
    return publicationEditions().find((edition) => edition.id === editionId) || publicationEditions()[0];
  }

  function publicationRecords(editionId = publicationState.edition) {
    return data.page_inventory.filter((record) => effectivePrintLevels(record).includes(editionId));
  }

  function baseAssembly(editionId = publicationState.edition) {
    const edition = publicationEdition(editionId);
    const sections = (edition.sections || []).map((section) => ({ ...section, paths: [] }));
    const bySection = new Map(sections.map((section) => [section.id, section]));
    const unplaced = { id: "unplaced", title: "Unplaced pages", accepts: [], paths: [] };
    publicationRecords(editionId).forEach((record) => {
      const section = bySection.get((record.assembly_sections || {})[editionId]) || unplaced;
      section.paths.push(record.path);
    });
    const overrides = new Map((edition.order_overrides || []).map((path, index) => [path, index]));
    [...sections, unplaced].forEach((section) => section.paths.sort((left, right) => {
      const leftOverride = overrides.has(left) ? overrides.get(left) : Number.MAX_SAFE_INTEGER;
      const rightOverride = overrides.has(right) ? overrides.get(right) : Number.MAX_SAFE_INTEGER;
      if (leftOverride !== rightOverride) return leftOverride - rightOverride;
      const leftRecord = pageIndex.get(left) || {};
      const rightRecord = pageIndex.get(right) || {};
      return text(leftRecord.assembly_sort_key, left).localeCompare(text(rightRecord.assembly_sort_key, right));
    }));
    if (unplaced.paths.length) sections.push(unplaced);
    return { editionId, sections };
  }

  function currentAssembly(editionId = publicationState.edition) {
    const base = baseAssembly(editionId);
    const draft = assemblyDrafts.get(editionId);
    if (!draft) return base;
    const assigned = new Set(publicationRecords(editionId).map((record) => record.path));
    const seen = new Set();
    const baseById = new Map(base.sections.map((section) => [section.id, section]));
    const sections = draft.sections
      .filter((section) => section.id === "unplaced" || baseById.has(section.id))
      .map((section) => ({
        ...(baseById.get(section.id) || section),
        paths: section.paths.filter((path) => assigned.has(path) && !seen.has(path) && seen.add(path))
      }));
    base.sections.forEach((section) => {
      if (!sections.some((candidate) => candidate.id === section.id)) sections.push({ ...section, paths: [] });
      const target = sections.find((candidate) => candidate.id === section.id);
      section.paths.forEach((path) => {
        if (!seen.has(path)) {
          target.paths.push(path);
          seen.add(path);
        }
      });
    });
    return { editionId, sections: sections.filter((section) => section.id !== "unplaced" || section.paths.length) };
  }

  function ensureAssemblyDraft(editionId = publicationState.edition) {
    if (!assemblyDrafts.has(editionId)) {
      const current = currentAssembly(editionId);
      assemblyDrafts.set(editionId, {
        editionId,
        sections: current.sections.map((section) => ({ ...section, paths: [...section.paths] }))
      });
    }
    return assemblyDrafts.get(editionId);
  }

  function assemblyPositions(assembly) {
    const positions = new Map();
    assembly.sections.forEach((section, sectionIndex) => section.paths.forEach((path, pageIndexValue) => {
      positions.set(path, `${sectionIndex}:${section.id}:${pageIndexValue}`);
    }));
    return positions;
  }

  function assemblyChangeCount(editionId = publicationState.edition) {
    if (!assemblyDrafts.has(editionId)) return 0;
    const base = baseAssembly(editionId);
    const draft = currentAssembly(editionId);
    const baseSections = base.sections.map((section) => section.id).join("\u0000");
    const draftSections = draft.sections.map((section) => section.id).join("\u0000");
    const basePositions = assemblyPositions(base);
    const draftPositions = assemblyPositions(draft);
    let count = baseSections === draftSections ? 0 : 1;
    draftPositions.forEach((position, path) => {
      if (basePositions.get(path) !== position) count += 1;
    });
    return count;
  }

  function setPublicationEdition(editionId) {
    publicationState.edition = editionId;
    byId("analysis-edition").value = editionId;
    byId("builder-edition").value = editionId;
    renderEditionAnalysis();
    renderDocumentBuilder();
  }

  function moveAssemblySection(sectionId, direction) {
    const draft = ensureAssemblyDraft();
    const index = draft.sections.findIndex((section) => section.id === sectionId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= draft.sections.length) return;
    [draft.sections[index], draft.sections[target]] = [draft.sections[target], draft.sections[index]];
    renderDocumentBuilder();
  }

  function moveAssemblyPage(path, direction) {
    const draft = ensureAssemblyDraft();
    const section = draft.sections.find((candidate) => candidate.paths.includes(path));
    if (!section) return;
    const index = section.paths.indexOf(path);
    const target = index + direction;
    if (target < 0 || target >= section.paths.length) return;
    [section.paths[index], section.paths[target]] = [section.paths[target], section.paths[index]];
    renderDocumentBuilder();
  }

  function moveAssemblyPageTo(path, sectionId) {
    const draft = ensureAssemblyDraft();
    draft.sections.forEach((section) => {
      section.paths = section.paths.filter((candidate) => candidate !== path);
    });
    let target = draft.sections.find((section) => section.id === sectionId);
    if (!target) {
      target = { id: sectionId, title: sectionId === "unplaced" ? "Unplaced pages" : sectionId, accepts: [], paths: [] };
      draft.sections.push(target);
    }
    target.paths.push(path);
    renderDocumentBuilder();
  }

  function assemblyPageStarts(assembly) {
    let page = 1;
    const sectionStarts = new Map();
    const pageStarts = new Map();
    assembly.sections.forEach((section) => {
      sectionStarts.set(section.id, page);
      section.paths.forEach((path) => {
        pageStarts.set(path, page);
        page += Number((pageIndex.get(path) || {}).estimated_pages || 1);
      });
    });
    return { sectionStarts, pageStarts, totalPages: Math.max(0, page - 1) };
  }

  function publicationMetric(label, value, detail) {
    const card = element("article", "publication-metric");
    card.append(element("span", "eyebrow", label), element("strong", "", value), element("p", "", detail));
    return card;
  }

  function publicationFinding(level, title, detail, records = []) {
    const card = element("article", `publication-finding ${level}`);
    const header = element("div", "publication-finding-header");
    header.append(element("span", `finding-level ${level}`, level), element("strong", "", title));
    card.append(header, element("p", "", detail));
    if (records.length) {
      const details = element("details", "publication-finding-details");
      details.append(element("summary", "", `View ${records.length} affected record${records.length === 1 ? "" : "s"}`));
      const list = element("ul");
      records.slice(0, 30).forEach((record) => {
        const item = element("li");
        const source = record.record || record;
        item.append(inlineLink(source.title || source.path, source.github_url || `${GITHUB_BLOB_ROOT}${source.path}`));
        if (record.note) item.append(document.createTextNode(` — ${record.note}`));
        list.append(item);
      });
      if (records.length > 30) list.append(element("li", "muted", `${records.length - 30} additional records omitted from this compact view.`));
      details.append(list);
      card.append(details);
    }
    return card;
  }

  function editionSectionRecords(editionId) {
    const assembly = currentAssembly(editionId);
    return assembly.sections.map((section) => ({
      ...section,
      records: section.paths.map((path) => pageIndex.get(path)).filter(Boolean)
    }));
  }

  function renderPublicationComposition(sections) {
    const cards = sections.map((section) => {
      const words = section.records.reduce((sum, record) => sum + Number(record.word_count || 0), 0);
      const pages = section.records.reduce((sum, record) => sum + Number(record.estimated_pages || 1), 0);
      const card = element("article", `composition-card${section.id === "unplaced" ? " warning" : ""}`);
      card.append(element("strong", "", section.title), element("span", "", `${section.records.length} pages · ${words.toLocaleString()} words · ~${pages} PDF pages`));
      return card;
    });
    byId("publication-composition").replaceChildren(...cards);
  }

  function renderPublicationPreflight(records, sections, editionId) {
    const assigned = new Set(records.map((record) => record.path));
    const unplaced = sections.find((section) => section.id === "unplaced")?.records || [];
    const unclassified = data.page_inventory.filter((record) => effectivePublicationDisposition(record) === "unclassified");
    const conflicts = data.page_inventory.filter((record) => effectivePublicationDisposition(record) === "conflict");
    const missingReasons = data.page_inventory.filter((record) =>
      effectivePublicationDisposition(record) === "excluded" && !effectivePrintExclusionReason(record));
    const invalidMetadata = data.page_inventory.filter((record) => (record.invalid_print_levels || []).length);
    const excludedLinks = [];
    records.forEach((record) => (record.internal_links || []).forEach((link) => {
      if (link.exists && pageIndex.has(link.path) && !assigned.has(link.path)) {
        excludedLinks.push({ record, note: `links to excluded ${link.path}` });
      }
    }));
    const build = (data.publication.builds || []).find((record) => record.edition_id === editionId);
    const cards = [];
    cards.push(publicationFinding(
      unplaced.length || unclassified.length || conflicts.length || missingReasons.length || invalidMetadata.length ? "blocker" : "ready",
      unplaced.length || unclassified.length || conflicts.length || missingReasons.length || invalidMetadata.length ? "Assembly blockers detected" : "No structural blockers detected",
      unplaced.length || unclassified.length || conflicts.length || missingReasons.length || invalidMetadata.length
        ? `${unplaced.length} unplaced, ${unclassified.length} unclassified, ${conflicts.length} conflicting, ${missingReasons.length} exclusion-without-reason, and ${invalidMetadata.length} invalid-metadata record(s).`
        : "Every controlled page is included in an edition or explicitly excluded, and every included page has a defined document section.",
      [...unplaced, ...unclassified, ...conflicts, ...missingReasons, ...invalidMetadata]
    ));
    cards.push(publicationFinding(
      excludedLinks.length ? "warning" : "ready",
      excludedLinks.length ? "Edition-specific cross-references need review" : "Internal destinations are included",
      excludedLinks.length
        ? `${excludedLinks.length} internal page reference(s) lead to material outside this edition and may require a textual print reference or appendix placement.`
        : "No included page links to a known project page excluded from this edition.",
      excludedLinks
    ));
    if (build) {
      cards.push(publicationFinding(
        build.stale ? "warning" : "ready",
        build.stale ? "Existing PDF predates current content" : "Existing PDF reflects current content",
        `${build.page_count || "Unknown"} actual pages · built ${formatDate(build.modified_at)}.`,
        []
      ));
    } else {
      cards.push(publicationFinding("info", "No PDF build is registered", "Estimated pagination will remain in use until this edition is assembled."));
    }
    byId("publication-preflight").replaceChildren(...cards);
  }

  function publicationLengthTable(records) {
    const candidates = [...records].sort((left, right) => Number(right.estimated_pages) - Number(left.estimated_pages)).slice(0, 30);
    const ordered = sortedRecords(candidates, publicationLengthState, (record, key) => ({
      page: `${record.title} ${record.path}`,
      type: record.document_type,
      words: Number(record.word_count || 0),
      estimated_pages: Number(record.estimated_pages || 0),
      tables: Number(record.max_table_columns || 0)
    })[key]);
    const wrapper = element("div", "source-table-wrap");
    const table = element("table", "source-table publication-length-table");
    const head = element("thead");
    const headRow = element("tr");
    [["Page", "page"], ["Type", "type"], ["Words", "words"], ["Est. pages", "estimated_pages"], ["Widest table", "tables"]]
      .forEach(([label, key]) => headRow.append(sortableHeader(label, key, publicationLengthState, renderEditionAnalysis)));
    head.append(headRow);
    const body = element("tbody");
    ordered.forEach((record) => {
      const row = element("tr");
      const titleCell = element("td", "source-title-cell");
      titleCell.append(inlineLink(record.title, record.github_url), element("code", "page-path", record.path));
      row.append(
        titleCell,
        element("td", "", record.document_type.replaceAll("-", " ")),
        element("td", "", Number(record.word_count || 0).toLocaleString()),
        element("td", "", String(record.estimated_pages || 1)),
        element("td", "", record.max_table_columns ? `${record.max_table_columns} columns` : "None")
      );
      body.append(row);
    });
    table.append(head, body);
    wrapper.append(table);
    return wrapper;
  }

  function renderEditionAnalysis() {
    const edition = publicationEdition();
    if (!edition) return;
    const records = publicationRecords();
    const sections = editionSectionRecords(publicationState.edition);
    const words = records.reduce((sum, record) => sum + Number(record.word_count || 0), 0);
    const estimatedPages = records.reduce((sum, record) => sum + Number(record.estimated_pages || 1), 0);
    const wideThreshold = Number(data.publication.manifest.wide_table_column_threshold || 4);
    const longThreshold = Number(data.publication.manifest.long_page_word_threshold || 5000);
    const wide = records.filter((record) => Number(record.max_table_columns || 0) > wideThreshold);
    const long = records.filter((record) => Number(record.word_count || 0) > longThreshold);
    const heading = records.filter((record) => Number(record.heading_issue_count || 0) > 0);
    const multiEdition = records.filter((record) => effectivePrintLevels(record).length > 1);
    const build = (data.publication.builds || []).find((record) => record.edition_id === publicationState.edition);
    byId("publication-metrics").replaceChildren(
      publicationMetric("Included records", records.length.toLocaleString(), edition.label),
      publicationMetric("Words", words.toLocaleString(), "Markdown-derived count"),
      publicationMetric("Estimated pages", `~${estimatedPages.toLocaleString()}`, `${data.publication.manifest.words_per_estimated_page} words per page`),
      publicationMetric("Actual build", build?.page_count ? build.page_count.toLocaleString() : "—", build ? (build.stale ? "Existing PDF is stale" : "Existing PDF is current") : "No registered build"),
      publicationMetric("Layout review", (wide.length + long.length + heading.length).toLocaleString(), `${wide.length} wide-table · ${long.length} long-page · ${heading.length} heading`),
      publicationMetric("Shared pages", multiEdition.length.toLocaleString(), "Also assigned to another edition")
    );
    renderPublicationComposition(sections);
    renderPublicationPreflight(records, sections, publicationState.edition);
    byId("publication-length-risks").replaceChildren(publicationLengthTable(records));
  }

  function assemblyControl(label, disabled, handler) {
    const button = element("button", "assembly-control", label);
    button.type = "button";
    button.disabled = disabled;
    button.addEventListener("click", handler);
    return button;
  }

  function renderAssemblyToolbar() {
    const count = assemblyChangeCount();
    byId("assembly-change-count").textContent = count;
    byId("assembly-change-tab-count").textContent = count;
    byId("export-assembly-changes").disabled = count === 0;
    byId("reset-assembly-changes").disabled = count === 0;
  }

  function renderDocumentBuilder() {
    const edition = publicationEdition();
    if (!edition) return;
    const assembly = currentAssembly();
    const starts = assemblyPageStarts(assembly);
    const outline = element("div", "assembly-sections");
    assembly.sections.forEach((section, sectionIndex) => {
      const sectionPages = section.paths.reduce((sum, path) => sum + Number((pageIndex.get(path) || {}).estimated_pages || 1), 0);
      const card = element("article", `assembly-section${section.id === "unplaced" ? " warning" : ""}`);
      const header = element("div", "assembly-section-header");
      const heading = element("div");
      heading.append(element("span", "eyebrow", section.id.startsWith("appendix") ? "Appendix" : "Section"), element("h4", "", section.title), element("p", "", `${section.paths.length} records · ~${sectionPages} pages · starts near p. ${starts.sectionStarts.get(section.id)}`));
      const sectionControls = element("div", "assembly-controls");
      sectionControls.append(
        assemblyControl("Move section up", sectionIndex === 0, () => moveAssemblySection(section.id, -1)),
        assemblyControl("Move section down", sectionIndex === assembly.sections.length - 1, () => moveAssemblySection(section.id, 1))
      );
      header.append(heading, sectionControls);
      const details = element("details", "assembly-section-pages");
      details.open = section.id === "unplaced";
      details.append(element("summary", "", `Show ${section.paths.length} page${section.paths.length === 1 ? "" : "s"}`));
      const list = element("ol", "assembly-page-list");
      section.paths.forEach((path, pageIndexValue) => {
        const record = pageIndex.get(path);
        if (!record) return;
        const item = element("li", "assembly-page-item");
        const identity = element("div", "assembly-page-identity");
        identity.append(inlineLink(record.title, record.github_url), element("code", "page-path", record.path), element("span", "muted", `~${record.estimated_pages} page${record.estimated_pages === 1 ? "" : "s"} · starts near p. ${starts.pageStarts.get(path)}`));
        const controls = element("div", "assembly-page-controls");
        controls.append(
          assemblyControl("↑", pageIndexValue === 0, () => moveAssemblyPage(path, -1)),
          assemblyControl("↓", pageIndexValue === section.paths.length - 1, () => moveAssemblyPage(path, 1))
        );
        const select = element("select", "assembly-section-select");
        select.setAttribute("aria-label", `Move ${record.title} to another section`);
        assembly.sections.filter((candidate) => candidate.id !== "unplaced").forEach((candidate) => {
          const option = element("option", "", candidate.title);
          option.value = candidate.id;
          option.selected = candidate.id === section.id;
          select.append(option);
        });
        if (section.id === "unplaced") {
          const option = element("option", "", "Unplaced pages");
          option.value = "unplaced";
          option.selected = true;
          select.prepend(option);
        }
        select.addEventListener("change", () => moveAssemblyPageTo(path, select.value));
        controls.append(select);
        item.append(identity, controls);
        list.append(item);
      });
      details.append(list);
      card.append(header, details);
      outline.append(card);
    });
    byId("publication-outline").replaceChildren(outline);

    const toc = byId("toc-preview-list");
    toc.replaceChildren(...assembly.sections.map((section) => {
      const item = element("li", "toc-section-item");
      const label = element("div", "toc-line");
      label.append(element("strong", "", section.title), element("span", "", String(starts.sectionStarts.get(section.id))));
      item.append(label);
      const childList = element("ol");
      section.paths.forEach((path) => {
        const record = pageIndex.get(path);
        if (!record) return;
        const child = element("li");
        const line = element("div", "toc-line");
        line.append(element("span", "", record.title), element("span", "", String(starts.pageStarts.get(path))));
        child.append(line);
        childList.append(child);
      });
      item.append(childList);
      return item;
    }));
    byId("toc-preview-note").textContent = `Estimated ${starts.totalPages.toLocaleString()} pages before resolved front-matter pagination. Actual page numbers replace estimates after the first PDF pass.`;
    renderAssemblyToolbar();
  }

  function exportAssemblyChanges() {
    if (!assemblyChangeCount()) return;
    const assembly = currentAssembly();
    const edition = publicationEdition();
    const payload = {
      schema_version: 1,
      purpose: "ARRP publication assembly changes",
      exported_at: new Date().toISOString(),
      edition_id: assembly.editionId,
      edition_label: edition.label,
      section_order: assembly.sections.map((section) => section.id),
      sections: assembly.sections.map((section) => ({ id: section.id, title: section.title, page_order: section.paths }))
    };
    const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const download = document.createElement("a");
    download.href = url;
    download.download = `arrp-publication-assembly-${assembly.editionId}-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.append(download);
    download.click();
    download.remove();
    URL.revokeObjectURL(url);
  }

  function initializeScrollToTop() {
    const button = byId("scroll-to-top");
    const refresh = () => { button.hidden = window.scrollY < 700; };
    window.addEventListener("scroll", refresh, { passive: true });
    button.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
    refresh();
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
      if (proposedState.level !== "all" && record.development_level !== proposedState.level) return false;
      if (proposedState.status !== "all" && record.workflow_status !== proposedState.status) return false;
      if (proposedState.area !== "all" && record.area !== proposedState.area) return false;
      if (!query) return true;
      const history = record.horizon_history || {};
      return [record.id, record.title, record.development_level, record.workflow_status, record.area, record.priority,
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
    byId("pages-count").textContent = data.page_inventory.length;
    byId("publication-assignments-count").textContent = data.page_inventory.length;
    byId("tab-candidates-count").textContent = data.active_horizon_records.length + data.records.length;
    byId("tab-sources-count").textContent = data.cited_sources.length + data.pending_sources.length;
    byId("tab-logs-count").textContent = data.project_logs.reduce((count, log) => count + log.entries.length, 0);
    byId("tab-publication-count").textContent = data.page_inventory.length;
    byId("candidate-formal-count").textContent = data.active_horizon_records.length;
    byId("candidate-preliminary-count").textContent = data.records.length;
    byId("source-catalog-count").textContent = data.cited_sources.length;
    byId("source-pending-count").textContent = data.pending_sources.length;
    byId("source-watchers-count").textContent = data.monitoring_issues.length;
    byId("court-watch-count").textContent = distinctSourceCount(data.court_watch_sources);
    byId("directive-watch-count").textContent = data.presidential_directives.length;
    byId("manual-watch-count").textContent = data.monitoring_issues.length;
    byId("case-watcher-mode").textContent = `Current mode: ${(data.watcher_metadata.case_monitor || {}).mode || "Not configured"}.`;
    byId("directive-watcher-mode").textContent = `Current mode: ${(data.watcher_metadata.presidential_directives || {}).mode || "Not configured"}.`;

    populateSelect(byId("preliminary-area"), [...new Set(data.records.map((record) => record.proposed_area))], "All areas");
    populateSelect(byId("proposed-level"), [...new Set(data.active_horizon_records.map((record) => record.development_level))], "All levels");
    populateSelect(byId("proposed-status"), [...new Set(data.active_horizon_records.map((record) => record.workflow_status))], "All statuses");
    populateSelect(byId("proposed-area"), [...new Set(data.active_horizon_records.map((record) => record.area))], "All areas");
    populateSelect(byId("sources-type"), [...new Set(data.cited_sources.map((record) => record.type))], "All types");
    populateSelect(byId("pending-owner"), [...new Set(data.pending_sources.flatMap((record) => record.record_ids || []))], "All possible destinations");
    populateSelect(byId("manual-watch-kind"), [...new Set(data.monitoring_issues.map((record) => record.kind))], "All issue types");
    populateSelect(byId("court-watch-owner"), [...new Set(data.court_watch_sources.map((record) => record.owner_id))], "All owners");
    populateSelect(byId("directive-administration"), [...new Set(data.presidential_directives.map((record) => record.administration))], "All administrations");
    populateSelect(byId("directive-status"), [...new Set(data.presidential_directives.map((record) => record.review_status))], "All statuses");
    populateSelect(byId("pages-level"), [
      "__included", ...Object.keys(PRINT_LEVEL_LABELS), "__excluded", "__unclassified", "__conflict"
    ], "All publication dispositions");
    [...byId("pages-level").options].forEach((option) => {
      if (PRINT_LEVEL_LABELS[option.value]) option.textContent = PRINT_LEVEL_LABELS[option.value];
      if (option.value === "__included") option.textContent = "Included in one or more editions";
      if (option.value === "__excluded") option.textContent = "Explicitly excluded";
      if (option.value === "__unclassified") option.textContent = "Unclassified — action required";
      if (option.value === "__conflict") option.textContent = "Metadata conflicts — action required";
    });
    populateSelect(byId("pages-section"), [...new Set(data.page_inventory.map((record) => record.section))], "All sections");
    publicationEditions().forEach((edition) => {
      [byId("analysis-edition"), byId("builder-edition")].forEach((select) => {
        const option = element("option", "", edition.label);
        option.value = edition.id;
        select.append(option);
      });
    });
    byId("analysis-edition").value = publicationState.edition;
    byId("builder-edition").value = publicationState.edition;
    data.project_logs.forEach((log) => {
      byId(`log-${log.id}-count`).textContent = log.entries.length;
      populateLogGroupSelect(log);
      byId(`log-${log.id}-search`).addEventListener("input", (event) => {
        logStates[log.id].search = event.target.value;
        renderProjectLog(log.id);
      });
      byId(`log-${log.id}-group`).addEventListener("change", (event) => {
        logStates[log.id].groupKey = event.target.value;
        renderProjectLog(log.id);
      });
    });

    byId("preliminary-search").addEventListener("input", (event) => { preliminaryState.search = event.target.value; renderPreliminary(); });
    byId("preliminary-term").addEventListener("change", (event) => { preliminaryState.term = event.target.value; renderPreliminary(); });
    byId("preliminary-area").addEventListener("change", (event) => { preliminaryState.area = event.target.value; renderPreliminary(); });
    byId("proposed-search").addEventListener("input", (event) => { proposedState.search = event.target.value; renderProposed(); });
    byId("proposed-level").addEventListener("change", (event) => { proposedState.level = event.target.value; renderProposed(); });
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
    byId("court-watch-updated-only").addEventListener("click", (event) => {
      courtWatchState.updatesOnly = !courtWatchState.updatesOnly;
      event.currentTarget.setAttribute("aria-pressed", String(courtWatchState.updatesOnly));
      event.currentTarget.textContent = courtWatchState.updatesOnly ? "Show all court cases" : "Show updated only";
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
    byId("directive-watch-updated-only").addEventListener("click", (event) => {
      directiveState.updatesOnly = !directiveState.updatesOnly;
      directiveState.page = 1;
      event.currentTarget.setAttribute("aria-pressed", String(directiveState.updatesOnly));
      event.currentTarget.textContent = directiveState.updatesOnly ? "Show all directives" : "Show updated only";
      renderDirectives();
    });
    byId("pages-search").addEventListener("input", (event) => {
      pageState.search = event.target.value;
      renderPages();
    });
    byId("pages-level").addEventListener("change", (event) => {
      pageState.level = event.target.value;
      renderPages();
    });
    byId("pages-section").addEventListener("change", (event) => {
      pageState.section = event.target.value;
      renderPages();
    });
    byId("analysis-edition").addEventListener("change", (event) => setPublicationEdition(event.target.value));
    byId("builder-edition").addEventListener("change", (event) => setPublicationEdition(event.target.value));
    byId("export-print-changes").addEventListener("click", exportPrintLevelChanges);
    byId("reset-print-changes").addEventListener("click", () => {
      printLevelDrafts.clear();
      printExclusionDrafts.clear();
      renderPrintWorkspace();
    });
    byId("export-assembly-changes").addEventListener("click", exportAssemblyChanges);
    byId("reset-assembly-changes").addEventListener("click", () => {
      assemblyDrafts.delete(publicationState.edition);
      renderDocumentBuilder();
    });

    initializeTabs();
    initializeSectionTabs("candidates", "formal");
    initializeSectionTabs("sources", "catalog");
    initializeSectionTabs("logs", "horizon");
    initializeSectionTabs("publication", "assignments");
    initializeWatcherTabs();
    initializeScrollToTop();
    renderPreliminary();
    renderProposed();
    renderSourceView("sources", data.cited_sources, "type");
    renderPending();
    renderManualWatch();
    renderCourtWatch();
    renderDirectives();
    data.project_logs.forEach((log) => renderProjectLog(log.id));
    renderProgress();
    renderPrintSummary();
    renderPrintChangeToolbar();
    renderReviewSignals();
    renderPages();
    renderEditionAnalysis();
    renderDocumentBuilder();
    renderIntegrity();
    refreshLiveProgress();
    refreshBotReviewSignals();
    refreshLiveIntegrity();
  }

  initialize();
})();
