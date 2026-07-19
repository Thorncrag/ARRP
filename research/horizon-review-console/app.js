(function () {
  "use strict";

  const data = window.ARRP_HORIZON_REVIEW_DATA;
  if (!data || !Array.isArray(data.records) || !Array.isArray(data.active_horizon_records)) {
    document.body.innerHTML = "<p>Candidate data could not be loaded. Rebuild the console data bundle.</p>";
    return;
  }

  const byId = (id) => document.getElementById(id);
  const preliminaryState = { search: "", term: "all", area: "all" };
  const proposedState = { search: "", status: "all", area: "all" };

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
    if (source.notes) item.append(element("p", "evidence-note", source.notes));
    return item;
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
    if (sources.length) sources.forEach((source) => sourceList.append(sourceEntry(source)));
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
      ? element("pre", "issue-body", issueBody)
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

    populateSelect(byId("preliminary-area"), [...new Set(data.records.map((record) => record.proposed_area))], "All areas");
    populateSelect(byId("proposed-status"), [...new Set(data.active_horizon_records.map((record) => record.status))], "All statuses");
    populateSelect(byId("proposed-area"), [...new Set(data.active_horizon_records.map((record) => record.area))], "All areas");

    byId("preliminary-search").addEventListener("input", (event) => { preliminaryState.search = event.target.value; renderPreliminary(); });
    byId("preliminary-term").addEventListener("change", (event) => { preliminaryState.term = event.target.value; renderPreliminary(); });
    byId("preliminary-area").addEventListener("change", (event) => { preliminaryState.area = event.target.value; renderPreliminary(); });
    byId("proposed-search").addEventListener("input", (event) => { proposedState.search = event.target.value; renderProposed(); });
    byId("proposed-status").addEventListener("change", (event) => { proposedState.status = event.target.value; renderProposed(); });
    byId("proposed-area").addEventListener("change", (event) => { proposedState.area = event.target.value; renderProposed(); });

    renderPreliminary();
    renderProposed();
  }

  initialize();
})();
