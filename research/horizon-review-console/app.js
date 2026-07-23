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
  const sourceCheckerState = {
    search: "",
    classification: "all",
    domain: "all",
    owner: "all",
    sortKey: "classification",
    sortDirection: "asc"
  };
  const pageState = { search: "", level: "all", section: "all", sortKey: "section", sortDirection: "asc" };
  const publicationState = { edition: "public-proposal" };
  const publicationLengthState = { sortKey: "estimated_pages", sortDirection: "desc" };
  const problemState = { search: "", owner: "all", severity: "all", status: "all" };
  const assemblyDrafts = new Map();
  const logStates = Object.fromEntries(data.project_logs.map((log) => [
    log.id,
    {
      search: "",
      groupKey: "all",
      filters: {},
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
  data.source_checker = data.source_checker || {};
  data.agent_registry = Array.isArray(data.agent_registry) ? data.agent_registry : [];

  const LAYOUT_STORAGE_KEY = "arrp-project-console-layout-v1";
  const DISCLOSURE_STORAGE_KEY = "arrp-project-console-disclosures-v1";
  const WORKFLOW_SUMMARY_STORAGE_KEY = "arrp-project-console-intro-hidden-v1";
  const layoutZones = new Map();
  let layoutEditing = false;
  let draggedLayoutItem = null;

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
  const LIVE_SOURCE_CHECKER_URL = "https://raw.githubusercontent.com/Thorncrag/ARRP/project-console-data/source-checker.json";
  const LIVE_PULL_REQUESTS_URL = "https://api.github.com/repos/Thorncrag/ARRP/pulls?state=open&per_page=100";
  const GITHUB_BLOB_ROOT = "https://github.com/Thorncrag/ARRP/blob/main/";
  const LIVE_SITE_ROOT = "https://thorncrag.github.io/ARRP/";
  const DEVELOPMENT_LEVELS = [
    "Candidate",
    "Admitted / undeveloped",
    "In development",
    "Developed proposal",
    "Review ready",
    "Release candidate"
  ];
  const APPROVED_WORKFLOW_STATUSES = [
    "Research",
    "Development",
    "Human decision needed",
    "Audit needed",
    "Audit in progress",
    "External review",
    "Publication approval",
    "Deferred",
    "Blocked"
  ];
  const WORKFLOW_EXPLANATION_REQUIRED = new Set(["Deferred", "Blocked"]);
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

  function detailsPanel(label, count) {
    const panel = element("details", "dossier-panel");
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

    const sourcePanel = detailsPanel("Source inventory records", sources.length);
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
    const card = element("details", "candidate-card");
    card.dataset.disclosureId = `candidates-preliminary-${record.id}`;
    const header = element("summary", "card-header");
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
    const card = element("details", "candidate-card formal-card");
    card.dataset.disclosureId = `candidates-formal-${record.id}`;
    const header = element("summary", "card-header");
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

  function readLayoutPreferences() {
    try {
      const parsed = JSON.parse(window.localStorage.getItem(LAYOUT_STORAGE_KEY) || "{}");
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch (_error) {
      return {};
    }
  }

  function writeLayoutPreferences(preferences) {
    try {
      window.localStorage.setItem(LAYOUT_STORAGE_KEY, JSON.stringify(preferences));
      return true;
    } catch (_error) {
      return false;
    }
  }

  function readDisclosurePreferences() {
    try {
      const parsed = JSON.parse(window.localStorage.getItem(DISCLOSURE_STORAGE_KEY) || "{}");
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch (_error) {
      return {};
    }
  }

  function writeDisclosurePreferences(preferences) {
    try {
      window.localStorage.setItem(DISCLOSURE_STORAGE_KEY, JSON.stringify(preferences));
    } catch (_error) { /* the disclosure state remains valid until reload */ }
  }

  function disclosureIdentity(details) {
    if (details.dataset.disclosureId) return details.dataset.disclosureId;
    const view = details.closest(".tab-panel")?.id.replace(/^panel-/, "") || "console";
    const ancestor = details.parentElement?.closest("details[data-disclosure-id]")?.dataset.disclosureId || "";
    const summary = details.querySelector(":scope > summary");
    const marker = summary?.querySelector(".record-id, .action-item-title, .progress-hold-group-title, code, h2, h3, h4, strong")?.textContent
      || summary?.firstElementChild?.textContent
      || summary?.textContent
      || "details";
    const context = details.closest("article[id], section[id]")?.id || "";
    const parts = [view, ancestor, context, layoutSlug(marker)].filter(Boolean);
    return parts.join("-") || "console-details";
  }

  function updateDisclosureDefaultButton(button, defaultOpen, label) {
    button.dataset.defaultOpen = String(defaultOpen);
    button.setAttribute("aria-pressed", String(defaultOpen));
    button.textContent = `Default: ${defaultOpen ? "open" : "closed"}`;
    button.setAttribute("aria-label", `${label}: ${defaultOpen ? "open" : "collapsed"} by default. Activate to use ${defaultOpen ? "collapsed" : "open"} by default.`);
  }

  function refreshDisclosurePreferences(root = document) {
    const preferences = readDisclosurePreferences();
    root.querySelectorAll("details").forEach((details) => {
      if (!details.dataset.disclosureId) details.dataset.disclosureId = disclosureIdentity(details);
      const key = details.dataset.disclosureId;
      if (details.dataset.disclosurePreference) return;
      const summary = details.querySelector(":scope > summary");
      if (!summary) return;
      const label = summary.querySelector(".record-id, .action-item-title, .progress-hold-group-title, h2, h3, h4, strong")?.textContent
        || summary.firstElementChild?.textContent
        || summary.textContent
        || "Collapsible container";
      const defaultOpen = typeof preferences[key] === "boolean" ? preferences[key] : details.open;
      if (typeof preferences[key] === "boolean") details.open = defaultOpen;
      const button = element("button", "disclosure-default-toggle");
      button.type = "button";
      updateDisclosureDefaultButton(button, defaultOpen, label.trim());
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const nextDefault = button.dataset.defaultOpen !== "true";
        const current = readDisclosurePreferences();
        current[key] = nextDefault;
        writeDisclosurePreferences(current);
        details.open = nextDefault;
        updateDisclosureDefaultButton(button, nextDefault, label.trim());
      });
      button.addEventListener("keydown", (event) => event.stopPropagation());
      summary.append(button);
      details.classList.add("managed-disclosure");
      details.dataset.disclosurePreference = "true";
    });
  }

  function layoutIdentity(node, index) {
    if (node.dataset.layoutId) return node.dataset.layoutId;
    if (node.dataset.tab) return `tab-${node.dataset.tab}`;
    if (node.dataset.subtab) return `subtab-${node.dataset.subtab}`;
    if (node.dataset.watcherTab) return `watcher-${node.dataset.watcherTab}`;
    if (node.id) return node.id;
    const labeled = node.querySelector("[id]");
    if (labeled?.id) return labeled.id;
    const stableClass = [...node.classList].find((name) => !["layout-item", "warning", "error", "info"].includes(name));
    return stableClass ? `${stableClass}-${index}` : `item-${index}`;
  }

  function layoutSlug(value) {
    return String(value || "item").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  }

  function layoutItems(config) {
    return [...config.container.querySelectorAll(config.selector)]
      .filter((node) => node.parentElement === config.container);
  }

  function saveLayoutZone(config) {
    const preferences = readLayoutPreferences();
    preferences[config.key] = layoutItems(config).map((node) => node.dataset.layoutId);
    const saved = writeLayoutPreferences(preferences);
    const status = byId("layout-status");
    status.textContent = saved
      ? "Layout saved in this browser."
      : "This browser did not permit saving; the arrangement will last until reload.";
  }

  function refreshLayoutHandles(config) {
    const items = layoutItems(config);
    items.forEach((item, index) => {
      item.draggable = layoutEditing;
      item.classList.add("layout-item");
      if (["A", "BUTTON", "DETAILS"].includes(item.tagName)) return;
      let handle = [...item.children].find((child) => child.classList?.contains("layout-handle"));
      if (!handle) {
        handle = element("div", "layout-handle");
        const label = element("span", "", "Drag to rearrange");
        const actions = element("span", "layout-handle-actions");
        const previous = element("button", "", config.axis === "horizontal" ? "←" : "↑");
        const next = element("button", "", config.axis === "horizontal" ? "→" : "↓");
        previous.type = next.type = "button";
        previous.setAttribute("aria-label", "Move earlier");
        next.setAttribute("aria-label", "Move later");
        previous.addEventListener("click", () => moveLayoutItem(item, -1));
        next.addEventListener("click", () => moveLayoutItem(item, 1));
        actions.append(previous, next);
        handle.append(label, actions);
        item.prepend(handle);
      }
      const buttons = handle.querySelectorAll("button");
      buttons[0].disabled = index === 0;
      buttons[1].disabled = index === items.length - 1;
    });
  }

  function applyLayoutZone(config) {
    const items = layoutItems(config);
    items.forEach((item, index) => { item.dataset.layoutId = layoutIdentity(item, index); });
    const order = readLayoutPreferences()[config.key];
    if (Array.isArray(order)) {
      const byLayoutId = new Map(items.map((item) => [item.dataset.layoutId, item]));
      order.forEach((id) => {
        const item = byLayoutId.get(id);
        if (item) config.container.append(item);
      });
      items.filter((item) => !order.includes(item.dataset.layoutId)).forEach((item) => config.container.append(item));
    }
    refreshLayoutHandles(config);
  }

  function moveLayoutItem(item, delta) {
    const config = [...layoutZones.values()].find((candidate) => candidate.container === item.parentElement);
    if (!config) return;
    const items = layoutItems(config);
    const index = items.indexOf(item);
    const targetIndex = index + delta;
    if (targetIndex < 0 || targetIndex >= items.length) return;
    if (delta < 0) config.container.insertBefore(item, items[targetIndex]);
    else config.container.insertBefore(items[targetIndex], item);
    saveLayoutZone(config);
    refreshLayoutHandles(config);
  }

  function registerLayoutZone(container, key, selector = ":scope > *", axis = "vertical") {
    if (!container) return;
    const config = { container, key, selector, axis };
    layoutZones.set(key, config);
    container.classList.add("layout-zone");
    container.dataset.layoutZone = key;
    container.dataset.layoutAxis = axis;
    if (!container.dataset.layoutListeners) {
      container.addEventListener("dragstart", (event) => {
        if (!layoutEditing) return;
        const item = event.target.closest("[data-layout-id]");
        if (!item || item.parentElement !== container) return;
        draggedLayoutItem = item;
        item.classList.add("layout-dragging");
        event.dataTransfer.effectAllowed = "move";
      });
      container.addEventListener("dragover", (event) => {
        if (!layoutEditing || !draggedLayoutItem || draggedLayoutItem.parentElement !== container) return;
        const target = event.target.closest("[data-layout-id]");
        if (!target || target === draggedLayoutItem || target.parentElement !== container) return;
        event.preventDefault();
        const rect = target.getBoundingClientRect();
        const after = axis === "horizontal"
          ? event.clientX > rect.left + rect.width / 2
          : event.clientY > rect.top + rect.height / 2;
        container.insertBefore(draggedLayoutItem, after ? target.nextSibling : target);
        [...container.querySelectorAll(".layout-drop-target")].forEach((node) => node.classList.remove("layout-drop-target"));
        target.classList.add("layout-drop-target");
      });
      container.addEventListener("dragend", () => {
        if (draggedLayoutItem?.parentElement === container) saveLayoutZone(config);
        [...container.querySelectorAll(".layout-dragging, .layout-drop-target")]
          .forEach((node) => node.classList.remove("layout-dragging", "layout-drop-target"));
        draggedLayoutItem = null;
        refreshLayoutHandles(config);
      });
      container.addEventListener("keydown", (event) => {
        if (!layoutEditing || !event.altKey) return;
        const item = event.target.closest("[data-layout-id]");
        if (!item || item.parentElement !== container) return;
        const backwards = event.key === "ArrowLeft" || event.key === "ArrowUp";
        const forwards = event.key === "ArrowRight" || event.key === "ArrowDown";
        if (!backwards && !forwards) return;
        event.preventDefault();
        event.stopImmediatePropagation();
        moveLayoutItem(item, backwards ? -1 : 1);
        item.focus();
      });
      container.dataset.layoutListeners = "true";
    }
    applyLayoutZone(config);
  }

  function refreshLayoutZones() {
    layoutZones.forEach(applyLayoutZone);
    refreshDisclosurePreferences();
  }

  function resetLayoutForCurrentView() {
    const active = document.querySelector('[role="tab"][data-tab][aria-selected="true"]')?.dataset.tab || "overview";
    const preferences = readLayoutPreferences();
    Object.keys(preferences).forEach((key) => {
      if (key.startsWith(`sections-${active}`) || key.startsWith(`cards-${active}`) || key === `subtabs-${active}`) delete preferences[key];
      if (active === "sources" && key === "watcher-tabs") delete preferences[key];
    });
    writeLayoutPreferences(preferences);
    const disclosures = readDisclosurePreferences();
    Object.keys(disclosures).forEach((key) => {
      if (key.startsWith(`${active}-`)) delete disclosures[key];
    });
    writeDisclosurePreferences(disclosures);
    window.location.reload();
  }

  function setWorkflowSummaryHidden(hidden, persist = true) {
    byId("workflow-summary").hidden = hidden;
    byId("workflow-summary-restore").hidden = !hidden;
    if (!persist) return;
    try {
      if (hidden) window.localStorage.setItem(WORKFLOW_SUMMARY_STORAGE_KEY, "true");
      else window.localStorage.removeItem(WORKFLOW_SUMMARY_STORAGE_KEY);
    } catch (_error) { /* the banner remains dismissed or restored until reload */ }
  }

  function initializeWorkflowSummary() {
    let hidden = false;
    try {
      hidden = window.localStorage.getItem(WORKFLOW_SUMMARY_STORAGE_KEY) === "true";
    } catch (_error) { /* use the visible default */ }
    setWorkflowSummaryHidden(hidden, false);
    byId("workflow-summary-dismiss").addEventListener("click", () => setWorkflowSummaryHidden(true));
    byId("workflow-summary-restore").addEventListener("click", () => setWorkflowSummaryHidden(false));
  }

  function initializePersonalLayout() {
    registerLayoutZone(document.querySelector(".tab-list"), "main-tabs", ":scope > button", "horizontal");
    ["candidates", "sources", "logs", "publication"].forEach((group) => {
      registerLayoutZone(document.querySelector(`[data-subtab-group="${group}"]`)?.parentElement, `subtabs-${group}`, ":scope > button", "horizontal");
    });
    registerLayoutZone(document.querySelector(".watcher-tab-list"), "watcher-tabs", ":scope > button", "horizontal");
    registerLayoutZone(document.querySelector(".overview-view"), "sections-overview", ":scope > .overview-section");
    registerLayoutZone(byId("overview-metrics"), "cards-overview-metrics", ":scope > article");
    registerLayoutZone(byId("overview-attention"), "cards-overview-attention", ":scope > a");
    registerLayoutZone(byId("overview-operations"), "cards-overview-operations", ":scope > a");
    registerLayoutZone(byId("overview-freshness"), "cards-overview-freshness", ":scope > a");
    registerLayoutZone(byId("progress-sections"), "sections-progress-v2", ":scope > .development-board-section, :scope > .progress-disclosure");
    registerLayoutZone(byId("progress-summary-grid"), "cards-progress-summary", ":scope > article");
    registerLayoutZone(byId("action-items-grid"), "cards-actions", ":scope > .action-item-card");
    registerLayoutZone(document.querySelector(".integrity-view"), "sections-integrity", ":scope > .integrity-layout");
    registerLayoutZone(byId("integrity-metrics"), "cards-integrity-metrics", ":scope > article");
    registerLayoutZone(byId("source-checker-summary"), "cards-sources-source-checker", ":scope > article");
    registerLayoutZone(byId("automation-grid"), "cards-automation", ":scope > .automation-card");
    registerLayoutZone(byId("automation-summary"), "cards-automation-summary", ":scope > article");
    registerLayoutZone(byId("print-level-summary"), "cards-publication-assignments", ":scope > button", "horizontal");
    registerLayoutZone(byId("publication-metrics"), "cards-publication-metrics", ":scope > article");
    registerLayoutZone(document.querySelector(".publication-analysis-view"), "sections-publication", ":scope > .publication-analysis-grid, :scope > section");
    registerLayoutZone(document.querySelector(".publication-analysis-grid"), "cards-publication-analysis", ":scope > section");
    registerLayoutZone(document.querySelector(".publication-builder-grid"), "cards-publication-builder", ":scope > section, :scope > aside");

    const toggle = byId("layout-edit-toggle");
    toggle.addEventListener("click", () => {
      layoutEditing = !layoutEditing;
      document.body.classList.toggle("layout-editing", layoutEditing);
      toggle.setAttribute("aria-pressed", String(layoutEditing));
      toggle.textContent = layoutEditing ? "Done arranging" : "Arrange layout";
      byId("layout-status").classList.toggle("is-editing", layoutEditing);
      byId("layout-status").textContent = layoutEditing
        ? "Drag highlighted tabs and sections, use the arrow controls, or press Alt plus an arrow key. Changes save automatically."
        : "Layout preferences are saved in this browser.";
      refreshLayoutZones();
    });
    byId("layout-reset-view").addEventListener("click", resetLayoutForCurrentView);
    byId("layout-reset-all").addEventListener("click", () => {
      try {
        window.localStorage.removeItem(LAYOUT_STORAGE_KEY);
        window.localStorage.removeItem(DISCLOSURE_STORAGE_KEY);
        window.localStorage.removeItem(WORKFLOW_SUMMARY_STORAGE_KEY);
      } catch (_error) { /* no-op */ }
      window.location.reload();
    });
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

  function populateLabeledSelect(select, options, allLabel) {
    const selected = select.value;
    select.replaceChildren();
    const all = element("option", "", allLabel);
    all.value = "all";
    select.append(all);
    options
      .filter((option) => option && option.value)
      .sort((left, right) => left.label.localeCompare(right.label))
      .forEach((option) => {
        const node = element("option", "", option.label);
        node.value = option.value;
        select.append(node);
      });
    select.value = options.some((option) => option.value === selected) ? selected : "all";
  }

  function pluralizeWord(count, singular) {
    if (count === 1) return `${count} ${singular}`;
    if (/(.)y$/i.test(singular)) return `${count} ${singular.slice(0, -1)}ies`;
    return `${count} ${singular}s`;
  }

  function updateDenseDisclosureSummary(id, count, singular, detail = "") {
    const node = byId(id);
    if (!node) return;
    node.textContent = `${pluralizeWord(Number(count), singular)}${detail ? ` · ${detail}` : ""}`;
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
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => activateTab(tab.dataset.tab));
      tab.addEventListener("keydown", (event) => {
        const orderedTabs = [...document.querySelectorAll('[role="tab"][data-tab]')];
        const index = orderedTabs.indexOf(tab);
        let target = null;
        if (event.key === "ArrowRight") target = orderedTabs[(index + 1) % orderedTabs.length];
        if (event.key === "ArrowLeft") target = orderedTabs[(index - 1 + orderedTabs.length) % orderedTabs.length];
        if (event.key === "Home") target = orderedTabs[0];
        if (event.key === "End") target = orderedTabs[orderedTabs.length - 1];
        if (!target) return;
        event.preventDefault();
        activateTab(target.dataset.tab, true);
      });
    });
    const requested = window.location.hash.replace(/^#/, "").split(":", 1)[0];
    activateTab(tabs.some((tab) => tab.dataset.tab === requested) ? requested : "overview");
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
    const activeTopLevel = document.querySelector('[role="tab"][data-tab][aria-selected="true"]')?.dataset.tab;
    if (activeTopLevel === group && !window.location.hash.startsWith(`#${group}:${selected.dataset.subtab}`)) {
      window.history.replaceState(null, "", `#${group}:${selected.dataset.subtab}`);
    }
  }

  function initializeSectionTabs(group, fallback) {
    const tabs = [...document.querySelectorAll(`[role="tab"][data-subtab-group="${group}"]`)];
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => activateSectionTab(group, tab.dataset.subtab));
      tab.addEventListener("keydown", (event) => {
        const orderedTabs = [...document.querySelectorAll(`[role="tab"][data-subtab-group="${group}"]`)];
        const index = orderedTabs.indexOf(tab);
        let target = null;
        if (event.key === "ArrowRight") target = orderedTabs[(index + 1) % orderedTabs.length];
        if (event.key === "ArrowLeft") target = orderedTabs[(index - 1 + orderedTabs.length) % orderedTabs.length];
        if (event.key === "Home") target = orderedTabs[0];
        if (event.key === "End") target = orderedTabs[orderedTabs.length - 1];
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
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => activateWatcherTab(tab.dataset.watcherTab));
      tab.addEventListener("keydown", (event) => {
        const orderedTabs = [...document.querySelectorAll('[role="tab"][data-watcher-tab]')];
        const index = orderedTabs.indexOf(tab);
        let target = null;
        if (event.key === "ArrowRight") target = orderedTabs[(index + 1) % orderedTabs.length];
        if (event.key === "ArrowLeft") target = orderedTabs[(index - 1 + orderedTabs.length) % orderedTabs.length];
        if (event.key === "Home") target = orderedTabs[0];
        if (event.key === "End") target = orderedTabs[orderedTabs.length - 1];
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
    updateDenseDisclosureSummary(`${name}-results-summary`, ordered.length, "source", `page ${state.page} of ${pages}`);
  }

  function monitoringIssueCard(record) {
    const details = element("details", "monitoring-issue");
    details.dataset.disclosureId = `progress-monitoring-${record.id}`;
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
    const host = byId("manual-watch-list");
    host.replaceChildren(...(records.length
      ? records.map(monitoringIssueCard)
      : [element("p", "empty-state compact-empty", "No monitored issues match the current filters.")]));
    refreshDisclosurePreferences(host);
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
    byId("pending-list").replaceChildren(...(filtered.length
      ? filtered.sort(monitoredSourcesFirst).map(sourceEntry)
      : [element("p", "empty-state compact-empty", "No pending sources match the current filters.")]));
  }

  function courtWatchCard(label, records) {
    const hasUpdate = records.some((record) => reviewSignals.courts.ids.has(record.id));
    const details = element("details", hasUpdate ? "monitoring-issue has-update" : "monitoring-issue");
    details.dataset.disclosureId = `sources-court-${records[0].owner_id}`;
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
    const host = byId("court-watch-list");
    host.replaceChildren(...(orderedGroups.length
      ? orderedGroups.map(([, records]) => courtWatchCard(records[0].monitoring_group || records[0].owner_title, records))
      : [element("p", "empty-state compact-empty", "No court sources match the current filters.")]));
    refreshDisclosurePreferences(host);
  }

  function sourceCheckerRecords() {
    const sourceIndex = new Map([...data.cited_sources, ...data.pending_sources].map((record) => [record.id, record]));
    return (Array.isArray(data.source_checker.results) ? data.source_checker.results : []).map((record) => {
      const source = sourceIndex.get(record.source_id) || {};
      let domain = "Unknown domain";
      try { domain = new URL(record.requested_url || record.final_url).hostname; } catch (_error) { /* keep fallback */ }
      return { ...record, domain, publisher: source.publisher || "", owner_ids: source.record_ids || [] };
    });
  }

  function renderSourceChecker() {
    const report = data.source_checker || {};
    const records = sourceCheckerRecords();
    const counts = report.counts || {};
    const exceptions = records.filter((record) => !["verified", "identity-preserving redirect"].includes(record.classification)).length;
    byId("source-checker-count").textContent = report.eligible_urls || records.length || 0;
    byId("source-checker-as-of").textContent = report.checked_at || "Awaiting first run";
    byId("source-checker-mode").textContent = report.mode ? `Mode: ${report.mode}` : "Awaiting first run";
    const classificationCards = Object.entries(counts).map(([classification, count]) =>
      watcherSummaryCard(classification.replace(/(^|[- ])\w/g, (match) => match.toUpperCase()), count, "latest published classification count"));
    byId("source-checker-summary").replaceChildren(
      watcherSummaryCard("Eligible URLs", report.eligible_urls || 0, "across configured source catalogs"),
      watcherSummaryCard("Exceptions", exceptions, "outside verified or identity-preserving redirect"),
      ...classificationCards
    );
    const query = sourceCheckerState.search.toLowerCase();
    const filtered = records.filter((record) => {
      if (sourceCheckerState.classification !== "all" && record.classification !== sourceCheckerState.classification) return false;
      if (sourceCheckerState.domain !== "all" && record.domain !== sourceCheckerState.domain) return false;
      if (sourceCheckerState.owner !== "all" && !(record.owner_ids || []).includes(sourceCheckerState.owner)) return false;
      return !query || [record.source_id, record.title, record.publisher, record.requested_url, record.final_url]
        .filter(Boolean).join(" ").toLowerCase().includes(query);
    });
    byId("source-checker-visible").textContent = filtered.length;
    updateDenseDisclosureSummary("source-checker-results-summary", filtered.length, "source check");
    const host = byId("source-checker-table");
    if (!records.length) {
      host.replaceChildren(element("p", "empty-state", "No Source Checker Bot result is available yet. The first successful published run will populate this view."));
      return;
    }
    if (!filtered.length) {
      host.replaceChildren(element("p", "empty-state", "No source checks match the current filters."));
      return;
    }
    const ordered = sortedRecords(filtered, sourceCheckerState, (record, key) => ({
      source: `${record.source_id} ${record.title}`,
      classification: record.classification,
      domain: record.domain,
      http: record.status_code == null ? -1 : Number(record.status_code),
      owner: (record.owner_ids || []).join(" "),
      destination: record.final_url || record.requested_url
    })[key]);
    const wrapper = element("div", "source-table-wrap");
    const table = element("table", "source-table source-checker-table");
    const head = element("thead");
    const headRow = element("tr");
    [
      ["Source", "source"],
      ["Classification", "classification"],
      ["Domain", "domain"],
      ["HTTP", "http"],
      ["Owner issue", "owner"],
      ["Observed destination", "destination"]
    ].forEach(([label, key]) => headRow.append(sortableHeader(label, key, sourceCheckerState, renderSourceChecker)));
    head.append(headRow);
    const body = element("tbody");
    ordered.forEach((record) => {
      const row = element("tr");
      const source = element("td", "source-title-cell");
      source.append(element("span", "record-id", record.source_id), element("strong", "", text(record.title, "Untitled source")));
      const destination = element("td", "source-link-cell");
      destination.append(record.final_url ? inlineLink("Open ↗", record.final_url) : element("span", "muted", text(record.error, "Unavailable")));
      row.append(
        source,
        element("td", "", text(record.classification)),
        element("td", "", record.domain),
        element("td", "", record.status_code == null ? "—" : String(record.status_code)),
        element("td", "", (record.owner_ids || []).join(" · ") || "—"),
        destination
      );
      body.append(row);
    });
    table.append(head, body); wrapper.append(table); host.replaceChildren(wrapper);
  }

  async function refreshLiveSourceChecker() {
    try {
      const response = await fetch(LIVE_SOURCE_CHECKER_URL, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      if (!payload || !Array.isArray(payload.results)) throw new Error("Invalid Source Checker payload");
      data.source_checker = payload;
      populateSourceCheckerFilters();
      renderSourceChecker();
      renderIntegrity();
      byId("source-checker-live-note").textContent = "Source Checker Bot data refreshed from the published Console data branch.";
    } catch (_error) {
      byId("source-checker-live-note").textContent = "Published Source Checker Bot data is not available yet; the checked-in snapshot remains shown.";
    }
  }

  function populateSourceCheckerFilters() {
    const records = sourceCheckerRecords();
    populateSelect(byId("source-checker-classification"), [...new Set(records.map((record) => record.classification))], "All classifications");
    populateSelect(byId("source-checker-domain"), [...new Set(records.map((record) => record.domain))], "All domains");
    populateSelect(byId("source-checker-owner"), [...new Set(records.flatMap((record) => record.owner_ids || []))], "All owner issues");
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

  function logEntryLatestValue(entry) {
    const values = entry.values || {};
    const candidates = [
      values.date,
      values.timestamp,
      values.run_time,
      values.activity_time,
      values.time,
      values.created_at,
      values.generated_at,
      entry.created_at,
      entry.generated_at,
      entry.generatedAt,
      entry.date
    ];
    for (const candidate of candidates) {
      const parsed = Date.parse(String(candidate || ""));
      if (Number.isFinite(parsed)) return parsed;
    }
    const idMatch = String(entry.id || "").match(/(\d+)(?!.*\d)/);
    return idMatch ? Number(idMatch[1]) : -Infinity;
  }

  function latestLogEntryId(entries) {
    return entries.reduce((best, entry) => {
      if (!best) return entry;
      const candidate = logEntryLatestValue(entry);
      const bestValue = logEntryLatestValue(best);
      return candidate > bestValue ? entry : best;
    }, null)?.id || null;
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

  function projectLatestLogContainer(log, entry) {
    const section = element("section", "latest-log-entry");
    const heading = element("div", "latest-log-entry-header");
    heading.append(element("h3", "", "Latest log entry"));

    const fields = element("dl", "latest-log-fields");
    log.columns.forEach((column) => {
      const field = element("div", "latest-log-field");
      const value = element("dd", "log-cell-value");
      value.innerHTML = (entry.values_html || {})[column.key] || text((entry.values || {})[column.key]);
      field.append(element("dt", "", column.label), value);
      fields.append(field);
    });

    const detailId = `log-${log.id}-${entry.id}-latest-details`;
    const toggle = element("button", "record-link secondary latest-log-toggle", "View complete entry");
    toggle.type = "button";
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-controls", detailId);
    const expanded = element("div", "latest-log-details");
    expanded.id = detailId;
    expanded.hidden = true;
    expanded.append(logEntryBody(entry));
    toggle.addEventListener("click", () => {
      const isExpanded = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!isExpanded));
      toggle.textContent = isExpanded ? "View complete entry" : "Hide complete entry";
      expanded.hidden = isExpanded;
    });

    heading.append(toggle);
    section.append(heading, fields, expanded);
    return section;
  }

  function logHistoryHeading(label, count, singular = "entry") {
    const heading = element("div", "log-history-heading");
    heading.append(
      element("h3", "", label),
      element("span", "count-pill", pluralizeWord(count, singular))
    );
    return heading;
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
    const filtered = log.entries.filter((entry) => {
      if (query && !String(entry.search_text || "").toLowerCase().includes(query)) return false;
      return Object.entries(state.filters || {}).every(([key, selected]) =>
        selected === "all" || String((entry.values || {})[key] || "Not recorded") === selected);
    });
    const render = () => renderProjectLog(logId);
    const ordered = sortedRecords(filtered, state, (entry, key) => (entry.values || {})[key]);
    const latestEntryId = latestLogEntryId(ordered);
    const latestEntry = ordered.find((entry) => entry.id === latestEntryId) || null;
    const remainingEntries = latestEntry ? ordered.filter((entry) => entry.id !== latestEntry.id) : ordered;
    byId(`log-${logId}-visible`).textContent = ordered.length;
    const container = byId(`log-${logId}-table`);
    if (!ordered.length) {
      container.replaceChildren(element("p", "empty-state", "No log entries match the current filters."));
      return;
    }
    const nodes = [];
    if (latestEntry) {
      nodes.push(projectLatestLogContainer(log, latestEntry));
    }
    if (!remainingEntries.length) {
      container.replaceChildren(...nodes);
      return;
    }
    if (state.groupKey === "all") {
      nodes.push(
        logHistoryHeading("Earlier entries", remainingEntries.length),
        projectLogTable(log, remainingEntries, state, render)
      );
      container.replaceChildren(...nodes);
      return;
    }
    const groups = new Map();
    remainingEntries.forEach((entry) => {
      const label = text((entry.values || {})[state.groupKey], "Not recorded");
      if (!groups.has(label)) groups.set(label, []);
      groups.get(label).push(entry);
    });
    const sections = [...groups].map(([label, entries]) => {
      const section = element("section", "log-group");
      const heading = element("h4", "log-group-heading");
      heading.append(
        element("span", "", label),
        element("span", "count-pill", `${entries.length} entr${entries.length === 1 ? "y" : "ies"}`)
      );
      section.append(heading, projectLogTable(log, entries, state, render));
      return section;
    });
    container.replaceChildren(
      ...nodes,
      logHistoryHeading("Earlier entries", remainingEntries.length),
      ...sections
    );
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
    updateDenseDisclosureSummary("directive-results-summary", records.length, "directive", `page ${directiveState.page} of ${pages}`);
  }

  function watcherSummaryCard(label, value, detail) {
    const card = element("article", "watcher-summary-card");
    card.dataset.layoutId = `metric-${layoutSlug(label)}`;
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

  function currentLifecycleRecords() {
    const proposals = Array.isArray(data.progress?.proposals) ? data.progress.proposals : [];
    const candidates = data.active_horizon_records.map((record) => ({
      identifier: record.id,
      title: record.title,
      developmentLevel: record.development_level,
      workflowStatus: record.workflow_status,
      nextAudit: record.next_audit,
      canonicalRecord: "",
      url: record.issue_url,
      explanation: (record.horizon_history || {}).rationale || "",
      followUp: (record.horizon_history || {}).follow_up || "",
      needsMonitoring: Boolean(record.needs_monitoring)
    }));
    return [...candidates, ...proposals];
  }

  function humanDecisionRecords() {
    return currentLifecycleRecords().filter(
      (record) => record.workflowStatus === "Human decision needed"
    );
  }

  function navigateToConsoleTarget(target) {
    const parts = target.split(":");
    activateTab(parts[0]);
    if (parts[0] === "candidates" && parts[1]) activateSectionTab("candidates", parts[1]);
    if (parts[0] === "sources" && parts[1]) activateSectionTab("sources", parts[1]);
    if (parts[0] === "logs" && parts[1]) activateSectionTab("logs", parts[1]);
    if (parts[0] === "publication" && parts[1]) activateSectionTab("publication", parts[1]);
    if (parts[0] === "sources" && parts[1] === "watchers" && parts[2]) activateWatcherTab(parts[2]);
    let destination = byId(`panel-${parts[0]}`);
    if (parts[0] === "progress" && parts[1]) {
      const section = byId(`progress-${parts[1]}`);
      if (section?.tagName === "DETAILS") section.open = true;
      if (section) destination = section;
    }
    destination.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function navigateFromHash() {
    const target = window.location.hash.replace(/^#/, "");
    if (!target || !byId(`panel-${target.split(":")[0]}`)) return;
    navigateToConsoleTarget(target);
  }

  function actionItemCard({ label, count, detail, target, updateCount = 0, externalUrl = "", items = [] }) {
    const card = element("details", `action-item-card${updateCount ? " has-update" : ""}${items.length > 4 ? " dense" : ""}`);
    const identity = `action-${layoutSlug(label)}`;
    card.dataset.layoutId = identity;
    card.dataset.disclosureId = `actions-${layoutSlug(label)}`;
    const summary = element("summary", "action-item-summary");
    const heading = element("div", "action-item-heading");
    heading.append(element("span", "action-item-title", label), element("strong", "action-item-count", String(count)));
    if (updateCount) heading.append(element("span", "tab-update-count action-update-count", `+${updateCount} new/updated`));
    summary.append(heading);
    card.append(summary, element("p", "", detail));
    if (items.length) {
      const list = element("ol", "action-item-detail-list");
      items.forEach((item) => {
        const row = element("li");
        if (item && typeof item === "object" && item.href) row.append(inlineLink(item.label, item.href));
        else row.textContent = typeof item === "object" ? item.label : item;
        list.append(row);
      });
      card.append(list);
    }
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

  function integrityFindingNeedsHuman(finding) {
    if (finding.attention === "human") return true;
    const message = String(finding.message || "").toLowerCase();
    return ["workflow_hold_reason", "missing explanation", "lacks an explanation", "missing reason", "lacks a reason", "human approval", "human decision", "human review required"]
      .some((signal) => message.includes(signal));
  }

  function workflowHoldRecords() {
    return currentLifecycleRecords().filter((record) =>
      ["Deferred", "Blocked", "Human decision needed"].includes(record.workflowStatus));
  }

  function stableProblemReference(problem) {
    const identity = [problem.category, problem.path, problem.source_id, problem.owner_ids, problem.message]
      .flat().filter(Boolean).join("|");
    let hash = 2166136261;
    for (let index = 0; index < identity.length; index += 1) {
      hash ^= identity.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return `PRB-${(hash >>> 0).toString(16).toUpperCase().padStart(8, "0")}`;
  }

  function allProblemRecords(feed = data.integrity) {
    const current = feed && typeof feed.current === "object" ? feed.current : {};
    const problems = [];
    const add = (problem) => {
      const normalized = {
        category: problem.category || "Project structure",
        severity: problem.severity || "warning",
        attention: problem.attention || "agent",
        owner: problem.owner || (problem.attention === "human" ? "Human" : "Elim"),
        reported_by: problem.reported_by || "Project Console",
        status: problem.status || "Open",
        detected_at: problem.detected_at || current.generated_at || data.generated_at,
        checked_at: problem.checked_at || current.generated_at || data.generated_at,
        ...problem
      };
      normalized.affected_ids = problem.affected_ids || problem.owner_ids || [];
      normalized.reference = problem.reference || stableProblemReference(normalized);
      problems.push(normalized);
    };

    (Array.isArray(current.findings) ? current.findings : []).forEach((finding) => add({
      ...finding,
      attention: integrityFindingNeedsHuman(finding) ? "human" : (finding.attention || "agent"),
      owner: integrityFindingNeedsHuman(finding) ? "Human" : (finding.owner || "Elim"),
      reported_by: "Project Integrity Bot",
      status: finding.status || "Open"
    }));

    sourceCheckerRecords()
      .filter((record) => ["broken", "identity mismatch", "review required"].includes(record.classification))
      .forEach((record) => add({
        category: "Source integrity",
        severity: ["broken", "identity mismatch"].includes(record.classification) ? "error" : "warning",
        attention: "agent",
        owner: "Elim",
        reported_by: "Source Checker Bot",
        status: "Pending remediation",
        source_id: record.source_id,
        source_url: record.final_url || record.requested_url || "",
        owner_ids: record.owner_ids || [],
        message: `${record.classification}: ${record.error || "the observed URL or identity requires review against the cataloged source."}`,
        detected_at: data.source_checker.generated_at,
        checked_at: data.source_checker.generated_at
      }));

    (data.active_horizon_records || []).forEach((record) => {
      (record.dossier_gaps || []).forEach((gap) => add({
        category: "Candidate dossier completeness",
        severity: "info",
        attention: "agent",
        owner: "Elim",
        reported_by: "Project Console",
        status: "Pending candidate work",
        owner_ids: [record.id],
        source_url: record.issue_url,
        message: `${record.id}: ${gap}`,
        detected_at: data.github_synced_at,
        checked_at: data.github_synced_at
      }));
    });

    (Array.isArray(data.progress?.warnings) ? data.progress.warnings : []).forEach((warning) => add({
      category: "Project tracking",
      severity: "warning",
      attention: "agent",
      owner: "Elim",
      reported_by: "Project Console progress snapshot",
      status: "Open",
      message: typeof warning === "string" ? warning : (warning.message || JSON.stringify(warning)),
      source_url: "https://github.com/users/Thorncrag/projects/2",
      detected_at: data.progress.generatedAt || data.progress.asOf,
      checked_at: data.progress.generatedAt || data.progress.asOf
    }));

    const approvedWorkflowStatuses = new Set(APPROVED_WORKFLOW_STATUSES);
    const progressStatusWarnings = new Set(
      (Array.isArray(data.progress?.warnings) ? data.progress.warnings : [])
        .filter((warning) => /not an approved workflow status|Project Status is missing/i.test(
          typeof warning === "string" ? warning : warning.message || ""
        ))
        .map((warning) => String(
          typeof warning === "string" ? "" : warning.identifier || ""
        ))
        .filter(Boolean)
    );
    currentLifecycleRecords()
      .filter((record) => !approvedWorkflowStatuses.has(record.workflowStatus))
      .filter((record) => !progressStatusWarnings.has(String(record.identifier)))
      .forEach((record) => add({
        category: "Lifecycle classification",
        severity: "warning",
        attention: "agent",
        owner: "Elim",
        reported_by: "Project Console lifecycle projection",
        status: "Status correction required",
        owner_ids: [record.identifier],
        message: `${record.identifier} has an unrecognized or missing workflow Status (${text(record.workflowStatus, "not recorded")}); assign one of the approved Status values. Monitoring remains an independent issue designation.`,
        source_url: record.canonicalRecord ? `${GITHUB_BLOB_ROOT}${record.canonicalRecord}` : record.url,
        detected_at: data.progress.generatedAt || data.progress.asOf,
        checked_at: data.progress.generatedAt || data.progress.asOf
      }));

    const currentFindingText = (Array.isArray(current.findings) ? current.findings : [])
      .map((finding) => String(finding.message || "").toLowerCase());
    workflowHoldRecords()
      .filter((record) => WORKFLOW_EXPLANATION_REQUIRED.has(record.workflowStatus))
      .filter((record) => !String(record.explanation || "").trim())
      .filter((record) => !currentFindingText.some((message) =>
        message.includes(String(record.identifier).toLowerCase())
          && /workflow_hold_reason|explanation|reason/.test(message)))
      .forEach((record) => add({
        category: "Workflow explanation",
        severity: "warning",
        attention: "human",
        owner: "Human",
        reported_by: "Project Console workflow check",
        status: "Explanation required",
        owner_ids: [record.identifier],
        message: `${record.identifier} is ${record.workflowStatus} but has no recorded explanation or reason; the project must not infer one.`,
        source_url: record.canonicalRecord ? `${GITHUB_BLOB_ROOT}${record.canonicalRecord}` : record.url,
        detected_at: data.progress.generatedAt || data.progress.asOf,
        checked_at: data.progress.generatedAt || data.progress.asOf
      }));

    const dispositions = data.publication?.disposition_counts || {};
    if (Number(dispositions.unclassified || 0)) add({
      category: "Publication metadata",
      severity: "error",
      attention: "agent",
      owner: "Elim",
      reported_by: "Project Console publication check",
      status: "Open",
      message: `${dispositions.unclassified} publication-controlled page${dispositions.unclassified === 1 ? " is" : "s are"} unclassified.`,
      source_url: "#publication:assignments"
    });
    if (Number(dispositions.conflict || 0)) add({
      category: "Publication metadata",
      severity: "error",
      attention: "agent",
      owner: "Elim",
      reported_by: "Project Console publication check",
      status: "Open",
      message: `${dispositions.conflict} page${dispositions.conflict === 1 ? " has" : "s have"} conflicting publication metadata.`,
      source_url: "#publication:assignments"
    });

    if (!data.source_checker.generated_at) add({
      category: "Operational readiness",
      severity: "info",
      attention: "observed",
      owner: "source-checker-bot",
      reported_by: "Project Console readiness check",
      status: "Baseline not established",
      message: "Source Checker Bot has no complete Console baseline yet; its configured report-only pilot remains visible for oversight.",
      source_url: "#sources:watchers:source-checker"
    });

    data.agent_registry
      .filter((agent) => !/^enabled$/i.test(agent.status || ""))
      .forEach((agent) => add({
        category: "Operational readiness",
        severity: "info",
        attention: "observed",
        owner: agent.id,
        reported_by: "Agent runbook registry",
        status: agent.status,
        message: `${agent.name} is ${String(agent.status).replaceAll("-", " ")}.`,
        source_url: agent.runbook_url
      }));

    return problems.sort((left, right) => {
      const severityOrder = { error: 0, warning: 1, info: 2 };
      return (severityOrder[left.severity] ?? 3) - (severityOrder[right.severity] ?? 3)
        || left.category.localeCompare(right.category)
        || left.reference.localeCompare(right.reference);
    });
  }

  function integrityActionLink(finding) {
    const message = String(finding.message || "Integrity finding requires review");
    const identifier = message.match(/\b(?:HOR|[A-Z]{2,})-\d{3}\b/)?.[0] || "";
    const proposal = (data.progress?.proposals || []).find((record) => record.identifier === identifier);
    const candidate = (data.active_horizon_records || []).find((record) => record.id === identifier);
    const canonical = String(proposal?.canonicalRecord || "").trim();
    const href = finding.source_url || (canonical ? `${GITHUB_BLOB_ROOT}${canonical}` : (proposal?.url || candidate?.issue_url || ""));
    return { label: `${finding.reference || "Problem"}: ${message}`, href };
  }

  function renderActionItems() {
    const decisionRecords = humanDecisionRecords();
    const decisions = decisionRecords.length;
    const preliminary = data.records.length;
    const pending = data.pending_sources.length;
    const courtUpdates = reviewSignals.courts.count;
    const directiveUpdates = reviewSignals.directives.count;
    const integrityHumanFindings = allProblemRecords()
      .filter((finding) => finding.attention === "human")
      .sort((left, right) => String(left.message || "").localeCompare(String(right.message || "")));
    const integrityHuman = integrityHumanFindings.length;
    const total = decisions + preliminary + pending + courtUpdates + directiveUpdates + integrityHuman;
    const newOrUpdated = preliminary + courtUpdates + directiveUpdates;
    byId("tab-actions-count").textContent = total;
    byId("action-items-note").textContent = total
      ? `${total} item${total === 1 ? "" : "s"} awaiting review or a decision; ${newOrUpdated} new or updated.`
      : "No items currently await review or a decision.";
    byId("action-items-grid").replaceChildren(
      actionItemCard({
        label: "Integrity decisions requiring you",
        count: integrityHuman,
        detail: integrityHuman
          ? `${integrityHuman} Integrity finding${integrityHuman === 1 ? " requires" : "s require"} a reserved human decision or approval.`
          : "No Integrity finding currently requires a reserved human decision.",
        target: "integrity",
        items: integrityHumanFindings.map(integrityActionLink)
      }),
      actionItemCard({
        label: "Human decisions",
        count: decisions,
        detail: decisions
          ? "Current proposals or candidates whose recorded next action is a decision reserved to you."
          : "No current proposal or candidate has Human decision needed as its workflow Status.",
        target: "progress:holds",
        items: decisionRecords.map((record) => ({
          label: `ACT-${record.identifier}: ${record.title}`,
          href: record.canonicalRecord ? `${GITHUB_BLOB_ROOT}${record.canonicalRecord}` : record.url
        }))
      }),
      actionItemCard({
        label: "Preliminary candidates",
        count: preliminary,
        updateCount: preliminary,
        detail: preliminary ? "New synthesized institutional questions awaiting human intake review." : "No preliminary intake questions await review.",
        target: "candidates:preliminary",
        items: data.records.map((record) => ({ label: `ACT-${record.id}: ${record.title}`, href: record.links?.[0]?.url || "#candidates:preliminary" }))
      }),
      actionItemCard({
        label: "Pending source routing",
        count: pending,
        detail: pending ? "Sources still requiring a choice among plausible project destinations." : "No source-routing decisions are pending.",
        target: "sources:pending",
        items: data.pending_sources.map((record) => ({ label: `ACT-${record.id}: ${record.title}`, href: record.url }))
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
    refreshLayoutZones();
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
    renderOverview();
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
    const warning = byId("development-board-warning");
    board.replaceChildren(...DEVELOPMENT_LEVELS.map((level) => {
      const column = element("section", "development-column");
      const stageRecords = records
        .filter((record) => record.developmentLevel === level)
        .sort((left, right) => left.identifier.localeCompare(right.identifier));
      const heading = element("div", "development-column-heading");
      heading.append(element("h4", "", level), element("span", "count-pill", stageRecords.length));
      const list = element("div", "development-card-list");
      list.replaceChildren(...(stageRecords.length
        ? stageRecords.map(developmentBoardCard)
        : [element("p", "development-column-empty", "No current records")]));
      column.append(heading, list);
      return column;
    }));
    const uniqueIdentifiers = new Set(records.map((record) => record.identifier));
    const placed = records.length - unassigned.length;
    if (uniqueIdentifiers.size !== records.length) {
      byId("development-board-accounting").textContent = `${records.length} current rows loaded (${candidates.length} candidates and ${proposals.length} proposals), but identifier duplication prevents exact accounting.`;
      warning.hidden = false;
      warning.textContent = `${records.length - uniqueIdentifiers.size} duplicate identifier entr${records.length - uniqueIdentifiers.size === 1 ? "y" : "ies"} detected; rebuild the Console data after correcting the source records.`;
      return;
    }
    byId("development-board-accounting").textContent = unassigned.length
      ? `${placed} of ${records.length} current records are placed exactly once; ${unassigned.length} require Development level correction.`
      : `${records.length} current records represented exactly once across the six columns (${candidates.length} candidates and ${proposals.length} proposals).`;
    warning.hidden = unassigned.length === 0;
    warning.textContent = unassigned.length
      ? `${unassigned.length} record${unassigned.length === 1 ? " has" : "s have"} no recognized Development level and cannot be placed on the board.`
      : "";
  }

  function renderProgressHolds(snapshot) {
    const records = workflowHoldRecords();
    const groups = [
      ["Deferred", "Deferred"],
      ["Blocked", "Blocked"],
      ["Human decision needed", "Human decision needed"]
    ];
    const host = byId("progress-holds");
    byId("progress-holds-count").textContent = records.length;
    host.replaceChildren(...groups.map(([status, label]) => {
      const section = element("details", "progress-hold-group");
      section.dataset.disclosureId = `progress-hold-list-${layoutSlug(status)}`;
      const matching = records.filter((record) => record.workflowStatus === status)
        .sort((left, right) => left.identifier.localeCompare(right.identifier));
      const heading = element("summary", "section-heading-row");
      const title = element("span", "progress-hold-group-title", label);
      heading.append(title, element("span", "count-pill", matching.length));
      section.append(heading);
      if (!matching.length) {
        section.append(element("p", "development-column-empty", "No current records"));
        return section;
      }
      const list = element("div", "progress-hold-list");
      matching.forEach((record) => {
        const card = element("article", "progress-hold-card");
        const header = element("div", "progress-hold-header");
        header.append(element("strong", "record-id", record.identifier), element("span", "badge formal", text(record.developmentLevel, "Development level unavailable")), element("span", "badge", status));
        const explanation = String(record.explanation || "").trim();
        const nextAction = String(record.followUp || record.nextAudit || "").trim();
        card.append(
          header,
          element("h5", "", text(record.title, record.identifier)),
          dossierSection("Explanation / reason", explanation || "Missing: no explanation is available in the current authoritative Project or canonical metadata.", explanation ? "wide" : "wide warning"),
          dossierSection("Next trigger / action", nextAction && nextAction !== "Not recorded" ? nextAction : "Missing: no next trigger or action is recorded.", nextAction && nextAction !== "Not recorded" ? "wide" : "wide warning")
        );
        const links = element("div", "source-list compact-links");
        const liveUrl = proposalLiveUrl(record);
        if (liveUrl) links.append(linkButton("Live", liveUrl, true));
        if (record.url) links.append(linkButton("Issue", record.url, true));
        card.append(links); list.append(card);
      });
      section.append(list); return section;
    }));
    refreshDisclosurePreferences(host);
  }

  function renderProgress() {
    const snapshot = data.progress || {};
    const metrics = snapshot.metrics || {};
    const goal = snapshot.goal || {};
    const areas = Array.isArray(snapshot.areas) ? snapshot.areas : [];
    byId("progress-as-of").textContent = snapshot.asOf || "Unavailable";
    if (!Object.keys(metrics).length) {
      byId("progress-summary-grid").replaceChildren(
        progressMetric("Progress unavailable", "—", "Refresh the Project Console progress data and rebuild this console.")
      );
      byId("progress-status-note").textContent = "No Project Console progress snapshot is available.";
      byId("progress-schedule-summary").textContent = "Progress data unavailable";
      byId("progress-area-summary").textContent = "Area data unavailable";
      renderProgressTrajectory(snapshot);
      byId("progress-area-list").replaceChildren(element("p", "muted", "Area data unavailable."));
      byId("development-board").replaceChildren(element("p", "muted", "Development-level data unavailable."));
      renderProgressHolds(snapshot);
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
    byId("progress-schedule-summary").textContent = `${percent}% ready · ${metrics.trackStatus || "schedule status unavailable"}`;
    byId("progress-area-summary").textContent = `${areas.length} areas · ${metrics.ready} of ${metrics.total} eligible proposals ready`;
    byId("progress-fill").style.width = `${percent}%`;
    byId("progress-track").setAttribute("aria-valuenow", String(percent));
    renderProgressTrajectory(snapshot);
    renderDevelopmentBoard(snapshot);
    renderProgressHolds(snapshot);

    const areaRows = [...areas].sort((left, right) => right.remaining - left.remaining || left.area.localeCompare(right.area));
    byId("progress-area-list").replaceChildren(...areaRows.map((area) => {
      const row = element("div", "progress-area-row");
      const identity = element("div", "progress-area-identity");
      identity.append(element("strong", "", area.area), element("span", "", `${area.ready}/${area.total} ready`));
      const bar = element("div", "mini-progress-track");
      const fill = element("span");
      fill.style.width = `${Math.max(0, Math.min(100, Number(area.percentReady) || 0))}%`;
      bar.append(fill);
      row.append(identity, bar, element("span", "progress-area-percent", `${area.percentReady}%`));
      return row;
    }));
    renderOverview();
  }

  function overviewCard(label, value, detail, target, tone = "") {
    const card = element("a", `overview-card ${tone}`.trim());
    card.dataset.layoutId = `overview-${layoutSlug(label)}`;
    card.href = `#${target}`;
    card.append(element("span", "eyebrow", label), element("strong", "", String(value)), element("p", "", detail));
    return card;
  }

  function freshnessCard(label, value, target, thresholdHours = 48) {
    const card = element("a", "freshness-card overview-card");
    card.dataset.layoutId = `freshness-${layoutSlug(label)}`;
    card.href = `#${target}`;
    const parsed = Date.parse(value || "");
    const ageHours = Number.isFinite(parsed) ? Math.max(0, (Date.now() - parsed) / 3600000) : null;
    const state = ageHours == null ? "missing" : ageHours > thresholdHours ? "stale" : "current";
    card.classList.add(state);
    const description = ageHours == null
      ? "No baseline available"
      : ageHours < 1 ? "Updated within the last hour"
        : `${Math.round(ageHours)} hours old`;
    card.append(element("strong", "", label), element("p", "", state === "current" ? "Current" : state === "stale" ? "May be stale" : "Not established"), element("time", "", value ? formatDate(value) : description));
    card.title = description;
    return card;
  }

  function renderOverview() {
    if (!byId("overview-metrics")) return;
    const metrics = data.progress?.metrics || {};
    const problems = allProblemRecords();
    const humanProblems = problems.filter((problem) => problem.attention === "human").length;
    const decisions = humanDecisionRecords().length;
    const actionCount = humanProblems + decisions + data.records.length + data.pending_sources.length
      + reviewSignals.courts.count + reviewSignals.directives.count;
    const dispositions = data.publication?.disposition_counts || {};
    const publicationExceptions = Number(dispositions.unclassified || 0) + Number(dispositions.conflict || 0);
    const currentRecordCount = (data.progress?.proposals || []).length + data.active_horizon_records.length;
    byId("overview-generated-at").textContent = formatDate(data.generated_at);
    byId("overview-metrics").replaceChildren(
      watcherSummaryCard("Current records", currentRecordCount, `${(data.progress?.proposals || []).length} proposals plus ${data.active_horizon_records.length} active candidates in this build`),
      watcherSummaryCard("Review Ready", metrics.ready ?? "—", `of ${metrics.total ?? "—"} eligible proposals`),
      watcherSummaryCard("Remaining", metrics.remaining ?? "—", metrics.trackStatus || "Schedule unavailable"),
      watcherSummaryCard("Human actions", actionCount, "decisions and reviews assigned to you"),
      watcherSummaryCard("All problems", problems.length, `${problems.filter((problem) => problem.severity !== "info").length} errors or warnings`),
      watcherSummaryCard("Monitored issues", data.monitoring_issues.length, "defined external predicates")
    );
    byId("overview-attention").replaceChildren(
      overviewCard("Needs you", actionCount, "Human review, disposition, routing, or approval", "actions", actionCount ? "warning" : ""),
      overviewCard("Integrity", problems.length, `${humanProblems} human · ${problems.filter((problem) => problem.attention === "agent").length} agent · ${problems.filter((problem) => problem.attention === "observed").length} observed`, "integrity", problems.some((problem) => problem.severity === "error") ? "error" : ""),
      overviewCard("Publication exceptions", publicationExceptions, publicationExceptions ? "Unclassified or conflicting page metadata" : "Every controlled page is classified", "publication:assignments", publicationExceptions ? "error" : "")
    );

    const proposalDistribution = new Map((data.progress?.developmentLevelDistribution || []).map((record) => [record.level, Number(record.count) || 0]));
    proposalDistribution.set("Candidate", data.active_horizon_records.length);
    const maxCount = Math.max(1, ...DEVELOPMENT_LEVELS.map((level) => proposalDistribution.get(level) || 0));
    byId("overview-pipeline").replaceChildren(...DEVELOPMENT_LEVELS.map((level) => {
      const count = proposalDistribution.get(level) || 0;
      const stage = element("div", "pipeline-stage");
      const bar = element("div", "pipeline-stage-bar", String(count));
      bar.style.height = `${Math.max(1.5, 7 * count / maxCount)}rem`;
      stage.append(bar, element("span", "", level));
      return stage;
    }));

    const enabledAgents = data.agent_registry.filter((agent) => /^enabled$/i.test(agent.status)).length;
    const sourceResults = sourceCheckerRecords().length;
    byId("overview-operations").replaceChildren(
      overviewCard("Agents and bots", data.agent_registry.length, `${enabledAgents} enabled · ${data.agent_registry.length - enabledAgents} paused or pilot`, "automation"),
      overviewCard("Issues monitored", data.monitoring_issues.length, "Project records with a defined monitoring predicate", "progress:monitoring"),
      overviewCard("Watcher updates", reviewSignals.courts.count + reviewSignals.directives.count, "Detected external changes awaiting review", "sources:watchers", reviewSignals.courts.count + reviewSignals.directives.count ? "warning" : ""),
      overviewCard("Source-check baseline", sourceResults || "—", sourceResults ? `${sourceResults} URLs represented in the latest run` : "Full baseline not yet established", "sources:watchers:source-checker", sourceResults ? "" : "warning")
    );
    byId("overview-freshness").replaceChildren(
      freshnessCard("Console bundle", data.generated_at, "overview"),
      freshnessCard("GitHub Project", data.github_synced_at, "progress"),
      freshnessCard("Progress feed", data.progress.generatedAt || data.progress.asOf, "progress"),
      freshnessCard("Integrity feed", data.integrity?.current?.generated_at, "integrity"),
      freshnessCard("Source checks", data.source_checker.generated_at, "sources:watchers:source-checker", 192)
    );
    refreshLayoutZones();
  }

  function automationStatusClass(status) {
    if (/^enabled$/i.test(status)) return "enabled";
    if (/pilot/i.test(status)) return "pilot";
    if (/paused/i.test(status)) return "paused";
    return "";
  }

  function renderAutomation() {
    const records = data.agent_registry;
    const enabled = records.filter((record) => /^enabled$/i.test(record.status)).length;
    const agents = records.filter((record) => /llm-agent/i.test(record.type)).length;
    const bots = records.filter((record) => /bot/i.test(record.type)).length;
    byId("tab-automation-count").textContent = records.length;
    byId("automation-summary").replaceChildren(
      integrityMetric("Registered", records.length, "persistent named workers"),
      integrityMetric("Enabled", enabled, "currently enabled runbooks"),
      integrityMetric("Agents", agents, "LLM-directed workers"),
      integrityMetric("Bots", bots, "deterministic programs")
    );
    byId("automation-grid").replaceChildren(...records.map((record) => {
      const card = element("article", "automation-card");
      card.dataset.layoutId = `automation-${record.id}`;
      const summary = element("div", "automation-card-summary");
      const summaryMeta = element("span", "automation-card-tags");
      const typeTag = /llm-agent/i.test(record.type)
        ? "LLM agent"
        : /bot/i.test(record.type)
          ? "bot"
          : record.type.replaceAll("-", " ");
      summaryMeta.append(
        element("span", "badge formal automation-type", typeTag),
        element("span", `status-badge ${automationStatusClass(record.status)}`, String(record.status).replaceAll("-", " "))
      );
      summary.append(
        element("h3", "automation-card-title", record.name),
        summaryMeta,
        element("span", "record-id automation-card-id", record.id)
      );
      const body = element("div", "automation-card-body");
      const details = element("dl");
      [
        ["Identity", record.id],
        ["Type", record.type.replaceAll("-", " ")],
        ["Trigger", record.trigger.replaceAll("-", " ")],
        ["Schedule", record.schedule || "Event or manual only"],
        ["Environment", record.execution_environment.replaceAll("-", " ")],
        ["Runtime", record.runtime_id]
      ].forEach(([label, value]) => details.append(element("dt", "", label), element("dd", "", value || "Not recorded")));
      const links = element("div", "source-list dossier-actions");
      links.append(linkButton("Open runbook ↗", record.runbook_url, true));
      if (record.runtime_url) links.append(linkButton("Open runtime ↗", record.runtime_url, true));
      if (record.log_path) links.append(linkButton("Open log ↗", `${GITHUB_BLOB_ROOT}${record.log_path}`, true));
      body.append(element("p", "", record.description || "Authoritative operating configuration."), details);
      const checks = Array.isArray(record.checks) ? record.checks : [];
      const logHref = record.log_path ? `${GITHUB_BLOB_ROOT}${record.log_path}` : "";
      if (checks.length) {
        const checksSection = element("details", "automation-checks");
        checksSection.dataset.disclosureId = `automation-${record.id}-checks`;
        const heading = element("summary", "automation-checks-summary");
        const headingContent = element("div", "automation-checks-heading");
        headingContent.append(element("h4", "", `Checks included · ${checks.length}`));
        heading.append(headingContent);
        const list = element("ul");
        checks.forEach((check) => {
          const row = element("li");
          const label = typeof check === "string" ? check : check?.label || check?.name || check?.check || "";
          const href = typeof check === "object" && check && check.log_path ? `${GITHUB_BLOB_ROOT}${check.log_path}` : logHref;
          if (href) row.append(inlineLink(label || "Open check log", href));
          else row.textContent = label || "Check present (no linked log path configured)";
          list.append(row);
        });
        checksSection.append(
          heading,
          element("p", "", "This inventory comes from the authoritative runbook and is the same scope used by the bot report."),
          list
        );
        body.append(checksSection);
      }
      body.append(links);
      card.append(summary, body);
      return card;
    }));
    refreshLayoutZones();
  }

  async function refreshLiveProgress() {
    try {
      const response = await fetch(LIVE_PROGRESS_URL, { cache: "no-store" });
      if (!response.ok) return;
      const snapshot = await response.json();
      if (!snapshot || typeof snapshot !== "object" || !snapshot.metrics
          || !Array.isArray(snapshot.proposals) || Number(snapshot.schemaVersion || 0) < 2) return;
      const embeddedAt = Date.parse(data.progress?.generatedAt || data.progress?.asOf || "");
      const liveAt = Date.parse(snapshot.generatedAt || snapshot.asOf || "");
      if (Number.isFinite(embeddedAt) && (!Number.isFinite(liveAt) || liveAt < embeddedAt)) return;
      data.progress = snapshot;
      renderProgress();
      renderIntegrity();
      renderActionItems();
    } catch (_error) {
      // The embedded snapshot remains usable offline and from file://.
    }
  }

  function integrityMetric(label, value, detail) {
    const card = element("article", "integrity-metric");
    card.dataset.layoutId = `metric-${layoutSlug(label)}`;
    card.append(element("span", "", label), element("strong", "", String(value)), element("p", "", detail));
    return card;
  }

  function problemOwnerKey(finding) {
    if (finding.attention === "human") return "human";
    if (finding.attention === "observed") return "observed";
    return `${finding.attention || "agent"}:${String(finding.owner || "Unassigned").toLowerCase()}`;
  }

  function problemWorker(owner) {
    const normalized = String(owner || "").toLowerCase();
    return data.agent_registry.find((record) =>
      String(record.id || "").toLowerCase() === normalized
        || String(record.name || "").toLowerCase() === normalized);
  }

  function problemOwnerLabel(finding) {
    if (finding.attention === "human") return "You";
    if (finding.attention === "observed") return "Observed / no action assigned";
    return problemWorker(finding.owner)?.name || finding.owner || "Unassigned";
  }

  function problemQueueLabel(finding) {
    if (finding.attention === "human") return "Needs you";
    if (finding.attention === "observed") return "Observed";
    if (finding.attention === "bot") return "Bot-owned";
    return "Agent-owned";
  }

  function problemGroupOrder(finding) {
    return { human: 0, agent: 1, bot: 2, observed: 3 }[finding.attention] ?? 4;
  }

  function renderIntegrityHistory(feed = data.integrity) {
    const history = (Array.isArray(feed?.history) ? [...feed.history] : [])
      .sort((left, right) => Date.parse(right.generated_at || "") - Date.parse(left.generated_at || ""));
    const clean = history.filter((run) => run.result === "clean").length;
    const findings = history.length - clean;
    const latest = history[0] || {};
    const latestDuration = latest.duration_seconds == null ? "—" : `${Number(latest.duration_seconds).toFixed(1)}s`;
    byId("log-integrity-count").textContent = history.length;
    byId("log-integrity-visible").textContent = history.length;
    byId("tab-logs-count").textContent =
      data.project_logs.reduce((count, log) => count + log.entries.length, 0) + history.length;
    byId("integrity-log-summary").replaceChildren(
      integrityMetric("Retained runs", history.length, "bounded history in the integrity feed"),
      integrityMetric("Clean", clean, "runs with no reported findings"),
      integrityMetric("With findings", findings, "runs that reported one or more findings"),
      integrityMetric("Latest duration", latestDuration, latest.generated_at ? formatDate(latest.generated_at) : "No run available")
    );
    const host = byId("integrity-history");
    if (!history.length) {
      host.replaceChildren(element("p", "empty-state compact-empty", "No Project Integrity Bot run history is available yet."));
      return;
    }
    const renderRun = (run) => {
      const row = element("article", "integrity-history-row");
      const runCounts = run.counts || {};
      const header = element("div", "integrity-history-heading");
      header.append(
        element("strong", "", formatDate(run.generated_at)),
        element("span", run.result === "clean" ? "status-badge ready" : "status-badge needs-review",
          run.result === "clean" ? "Clean" : `${Number(runCounts.findings) || 0} findings`)
      );
      if (run.revision) {
        header.append(inlineLink(String(run.revision).slice(0, 7), `https://github.com/Thorncrag/ARRP/commit/${run.revision}`));
      }
      row.append(
        header,
        element("p", "", `${Number(runCounts.errors) || 0} errors · ${Number(runCounts.warnings) || 0} warnings · ${run.duration_seconds == null ? "duration unavailable" : `${Number(run.duration_seconds).toFixed(1)}s`}`)
      );
      return row;
    };
    const latestRun = history[0];
    const latestCard = element("section", "latest-log-entry");
    const latestHeader = element("div", "latest-log-entry-header");
    latestHeader.append(
      element("h3", "", "Latest run"),
      latestRun.revision
        ? inlineLink(String(latestRun.revision).slice(0, 7), `https://github.com/Thorncrag/ARRP/commit/${latestRun.revision}`)
        : element("span", "muted", "No revision recorded")
    );
    const latestCounts = latestRun.counts || {};
    const latestFields = element("dl", "latest-log-fields integrity-latest-fields");
    [
      ["Run time", formatDate(latestRun.generated_at)],
      ["Result", latestRun.result === "clean" ? "Clean" : `${Number(latestCounts.findings) || 0} findings`],
      ["Errors", Number(latestCounts.errors) || 0],
      ["Warnings", Number(latestCounts.warnings) || 0],
      ["Duration", latestRun.duration_seconds == null ? "Unavailable" : `${Number(latestRun.duration_seconds).toFixed(1)}s`]
    ].forEach(([label, value]) => {
      const field = element("div", "latest-log-field");
      field.append(element("dt", "", label), element("dd", "", String(value)));
      latestFields.append(field);
    });
    latestCard.append(latestHeader, latestFields);

    const earlierRuns = history.slice(1);
    const nodes = [latestCard];
    if (earlierRuns.length) {
      const rows = element("div", "integrity-history-rows");
      rows.append(...earlierRuns.map(renderRun));
      nodes.push(logHistoryHeading("Earlier runs", earlierRuns.length, "run"), rows);
    }
    host.replaceChildren(...nodes);
  }

  function renderIntegrity(feed = data.integrity) {
    const current = feed && typeof feed.current === "object" ? feed.current : {};
    const problems = allProblemRecords(feed);
    const ownerOptions = [...new Map(problems.map((finding) => [
      problemOwnerKey(finding),
      {
        value: problemOwnerKey(finding),
        label: `${problemOwnerLabel(finding)} — ${problemQueueLabel(finding)}`
      }
    ])).values()];
    if (problemState.owner !== "all" && !ownerOptions.some((option) => option.value === problemState.owner)) {
      problemState.owner = "all";
    }
    populateLabeledSelect(byId("problem-owner"), ownerOptions, "All owners");
    byId("problem-owner").value = problemState.owner;
    const problemStatuses = [...new Set(problems.map((finding) => finding.status))];
    if (problemState.status !== "all" && !problemStatuses.includes(problemState.status)) {
      problemState.status = "all";
    }
    populateSelect(byId("problem-status"), problemStatuses, "All states");
    byId("problem-status").value = problemState.status;
    const query = problemState.search.toLowerCase();
    const findings = problems.filter((finding) => {
      if (problemState.owner !== "all" && problemOwnerKey(finding) !== problemState.owner) return false;
      if (problemState.severity !== "all" && finding.severity !== problemState.severity) return false;
      if (problemState.status !== "all" && finding.status !== problemState.status) return false;
      if (!query) return true;
      return [finding.reference, finding.category, finding.message, finding.owner, finding.status,
        finding.reported_by, finding.path, finding.source_id, ...(finding.affected_ids || [])]
        .filter(Boolean).join(" ").toLowerCase().includes(query);
    });
    const findingCount = problems.length;
    const allErrors = problems.filter((finding) => finding.severity === "error").length;
    const allWarnings = problems.filter((finding) => finding.severity === "warning").length;
    const humanCount = problems.filter((finding) => finding.attention === "human").length;
    const agentCount = problems.filter((finding) => finding.attention === "agent").length;
    const botCount = problems.filter((finding) => finding.attention === "bot").length;
    const observedCount = problems.filter((finding) => finding.attention === "observed").length;
    byId("tab-integrity-count").textContent = findingCount;
    byId("problem-visible").textContent = findings.length;
    byId("integrity-as-of").textContent = current.generated_at ? formatDate(current.generated_at) : "Not yet run";
    const status = byId("integrity-status");
    status.className = `status-badge ${allErrors + allWarnings ? "needs-review" : "ready"}`.trim();
    status.textContent = findingCount ? `${findingCount} current problem${findingCount === 1 ? "" : "s"}` : "No current problems";
    byId("integrity-metrics").replaceChildren(
      integrityMetric("Needs you", humanCount, "reserved decisions or approvals"),
      integrityMetric("Agent-owned", agentCount, "visible work assigned outside the human inbox"),
      integrityMetric("Bot-owned", botCount, "deterministic remediation assigned to a bot"),
      integrityMetric("Observed", observedCount, "readiness or monitoring conditions"),
      integrityMetric("Total", findingCount, `${allErrors} errors · ${allWarnings} warnings`)
    );

    const grouped = new Map();
    findings.forEach((finding) => {
      const ownerKey = problemOwnerKey(finding);
      if (!grouped.has(ownerKey)) grouped.set(ownerKey, []);
      grouped.get(ownerKey).push(finding);
    });
    const findingHost = byId("integrity-findings");
    if (!findings.length) {
      const empty = element("div", "empty-state compact-empty");
      empty.append(element("span", "", "✓"), element("h3", "", problems.length ? "No problems match these filters" : "No current problems"), element("p", "", problems.length ? "Change or clear the filters to inspect the complete problem inventory." : "No current exception is represented in the available Console data."));
      findingHost.replaceChildren(empty);
    } else {
      findingHost.replaceChildren(...[...grouped.entries()]
        .sort(([, left], [, right]) =>
          problemGroupOrder(left[0]) - problemGroupOrder(right[0])
            || problemOwnerLabel(left[0]).localeCompare(problemOwnerLabel(right[0])))
        .map(([ownerKey, items]) => {
        const panel = element("details", "integrity-finding-group");
        panel.dataset.disclosureId = `integrity-problems-${layoutSlug(ownerKey)}`;
        const summary = element("summary");
        const ownerSummary = element("span", "problem-owner-summary");
        ownerSummary.append(
          element("strong", "", problemOwnerLabel(items[0])),
          element("span", `badge problem-queue ${items[0].attention}`, problemQueueLabel(items[0]))
        );
        summary.append(
          ownerSummary,
          element("span", "count-pill", `${items.length} problem${items.length === 1 ? "" : "s"}`)
        );
        panel.append(summary);
        const list = element("div", "integrity-finding-list");
        items.forEach((finding) => {
          const record = element("article", `integrity-finding ${finding.severity || "warning"}`);
          const heading = element("div", "integrity-finding-heading");
          heading.append(
            element("span", "problem-reference", finding.reference),
            element("span", "badge", finding.category || "Project structure"),
            element("span", `finding-level ${finding.severity || "warning"}`, finding.severity || "warning")
          );
          if (finding.path) heading.append(inlineLink(finding.path, `${GITHUB_BLOB_ROOT}${finding.path}`));
          if (finding.source_id) heading.append(finding.source_url ? inlineLink(finding.source_id, finding.source_url) : element("span", "record-id", finding.source_id));
          record.append(heading, element("p", "", finding.message || "Unspecified integrity finding"));
          if ((finding.affected_ids || []).length) {
            const affected = element("div", "problem-affected-records");
            affected.append(element("strong", "", "Affected records:"));
            finding.affected_ids.forEach((identifier) => affected.append(element("span", "badge", identifier)));
            record.append(affected);
          }
          const metadata = element("div", "problem-meta");
          metadata.append(
            element("span", "", `Reported by: ${finding.reported_by}`),
            element("span", "", `State: ${finding.status}`),
            element("span", "", `Last checked: ${formatDate(finding.checked_at)}`)
          );
          record.append(metadata);
          if (finding.source_url && !finding.source_id) {
            const actions = element("div", "integrity-finding-actions");
            const link = inlineLink("Open referenced record ↗", finding.source_url);
            if (finding.source_url.startsWith("#")) {
              link.target = "";
              link.removeAttribute("rel");
            }
            actions.append(link);
            record.append(actions);
          }
          list.append(record);
        });
        panel.append(list);
        return panel;
      }));
    }

    refreshDisclosurePreferences(findingHost);
    renderIntegrityHistory(feed);
    renderOverview();
  }

  async function refreshLiveIntegrity() {
    try {
      const response = await fetch(LIVE_INTEGRITY_URL, { cache: "no-store" });
      if (!response.ok) throw new Error(`GitHub returned ${response.status}`);
      const feed = await response.json();
      if (!feed || typeof feed !== "object" || !feed.current) return;
      const checkedAt = Date.parse(data.integrity?.current?.generated_at || "");
      const liveAt = Date.parse(feed.current.generated_at || "");
      if (Number.isFinite(checkedAt) && (!Number.isFinite(liveAt) || liveAt < checkedAt)) {
        byId("integrity-live-note").textContent = "The repository data branch is older than this checked snapshot; the newer snapshot remains displayed.";
        return;
      }
      data.integrity = feed;
      renderIntegrity(feed);
      renderActionItems();
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
    refreshLayoutZones();
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
    includedCard.dataset.layoutId = "publication-included";
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
      card.dataset.layoutId = `publication-${layoutSlug(level)}`;
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
      card.dataset.layoutId = `publication-${layoutSlug(disposition)}`;
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
    updateDenseDisclosureSummary("pages-results-summary", records.length, "page");
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
    refreshLayoutZones();
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
    card.dataset.layoutId = `metric-${layoutSlug(label)}`;
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
      details.dataset.disclosureId = `publication-finding-${layoutSlug(title)}`;
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
      details.dataset.disclosureId = `publication-assembly-${edition.id}-${section.id}`;
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
    refreshDisclosurePreferences(byId("publication-outline"));
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
    refreshDisclosurePreferences(list);
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
    byId("proposed-list").replaceChildren(...(records.length
      ? records.map(proposedCard)
      : [element("p", "empty-state compact-empty", "No formal candidates match the current filters.")]));
    byId("proposed-visible").textContent = records.length;
    refreshDisclosurePreferences(byId("proposed-list"));
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
    byId("watchers-count").textContent = 3;
    byId("pages-count").textContent = data.page_inventory.length;
    byId("publication-assignments-count").textContent = data.page_inventory.length;
    byId("tab-candidates-count").textContent = data.active_horizon_records.length + data.records.length;
    byId("tab-sources-count").textContent = data.cited_sources.length + data.pending_sources.length;
    byId("tab-logs-count").textContent =
      data.project_logs.reduce((count, log) => count + log.entries.length, 0)
      + (Array.isArray(data.integrity.history) ? data.integrity.history.length : 0);
    byId("tab-automation-count").textContent = data.agent_registry.length;
    byId("candidate-formal-count").textContent = data.active_horizon_records.length;
    byId("candidate-preliminary-count").textContent = data.records.length;
    byId("source-catalog-count").textContent = data.cited_sources.length;
    byId("source-pending-count").textContent = data.pending_sources.length;
    byId("source-watchers-count").textContent = 3;
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
    populateSourceCheckerFilters();
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
      if (log.id === "agents") {
        [["agent", "All agents"], ["task", "All task types"], ["outcome", "All outcomes"]].forEach(([key, label]) => {
          const select = byId(`log-agents-${key}`);
          populateSelect(select, [...new Set(log.entries.map((entry) => (entry.values || {})[key]).filter(Boolean))], label);
          select.addEventListener("change", (event) => {
            logStates.agents.filters[key] = event.target.value;
            renderProjectLog("agents");
          });
        });
      }
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
    byId("source-checker-search").addEventListener("input", (event) => { sourceCheckerState.search = event.target.value; renderSourceChecker(); });
    [["classification", "classification"], ["domain", "domain"], ["owner", "owner"]].forEach(([id, key]) => {
      byId(`source-checker-${id}`).addEventListener("change", (event) => { sourceCheckerState[key] = event.target.value; renderSourceChecker(); });
    });
    byId("problem-search").addEventListener("input", (event) => { problemState.search = event.target.value; renderIntegrity(); });
    byId("problem-owner").addEventListener("change", (event) => { problemState.owner = event.target.value; renderIntegrity(); });
    byId("problem-severity").addEventListener("change", (event) => { problemState.severity = event.target.value; renderIntegrity(); });
    byId("problem-status").addEventListener("change", (event) => { problemState.status = event.target.value; renderIntegrity(); });
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

    initializeWorkflowSummary();
    initializePersonalLayout();
    initializeTabs();
    initializeSectionTabs("candidates", "formal");
    initializeSectionTabs("sources", "catalog");
    initializeSectionTabs("logs", "horizon");
    initializeSectionTabs("publication", "assignments");
    initializeWatcherTabs();
    initializeScrollToTop();
    window.addEventListener("hashchange", navigateFromHash);
    renderPreliminary();
    renderProposed();
    renderSourceView("sources", data.cited_sources, "type");
    renderPending();
    renderManualWatch();
    renderCourtWatch();
    renderDirectives();
    renderSourceChecker();
    data.project_logs.forEach((log) => renderProjectLog(log.id));
    renderProgress();
    renderAutomation();
    renderOverview();
    renderPrintSummary();
    renderPrintChangeToolbar();
    renderReviewSignals();
    renderPages();
    renderEditionAnalysis();
    renderDocumentBuilder();
    renderIntegrity();
    refreshLayoutZones();
    refreshLiveProgress();
    refreshBotReviewSignals();
    refreshLiveIntegrity();
    refreshLiveSourceChecker();
  }

  initialize();
})();
