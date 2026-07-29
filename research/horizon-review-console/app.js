(function () {
  "use strict";

  const data = window.ARRP_HORIZON_REVIEW_DATA;
  if (!data || typeof data !== "object") {
    document.body.innerHTML = "<p>Project Console summary data could not be loaded. Rebuild the Console data bundle.</p>";
    return;
  }

  function normalizeLoadedData() {
    const sourceChunkKeys = Object.keys(data)
      .filter((key) => key.startsWith("cited_sources_chunk_"))
      .sort();
    if (sourceChunkKeys.length) {
      data.cited_sources = sourceChunkKeys.flatMap((key) => {
        const records = Array.isArray(data[key]) ? data[key] : [];
        delete data[key];
        return records;
      }).sort((left, right) => String(left.id || "").localeCompare(String(right.id || "")));
    }
    const directiveChunkKeys = Object.keys(data)
      .filter((key) => key.startsWith("presidential_directives_chunk_"))
      .sort();
    if (directiveChunkKeys.length) {
      data.presidential_directives = directiveChunkKeys.flatMap((key) => {
        const records = Array.isArray(data[key]) ? data[key] : [];
        delete data[key];
        return records;
      });
    }
    data.records = Array.isArray(data.records) ? data.records : [];
    data.active_horizon_records = Array.isArray(data.active_horizon_records) ? data.active_horizon_records : [];
    data.cited_sources = Array.isArray(data.cited_sources) ? data.cited_sources : [];
    data.monitoring_issues = Array.isArray(data.monitoring_issues) ? data.monitoring_issues : [];
    data.pending_sources = Array.isArray(data.pending_sources) ? data.pending_sources : [];
    data.page_inventory = Array.isArray(data.page_inventory) ? data.page_inventory : [];
    data.project_logs = Array.isArray(data.project_logs) ? data.project_logs : [];
    data.court_watch_sources = Array.isArray(data.court_watch_sources) ? data.court_watch_sources : [];
    data.presidential_directives = Array.isArray(data.presidential_directives) ? data.presidential_directives : [];
    data.watcher_metadata = data.watcher_metadata || {};
    data.progress = data.progress || {};
    data.integrity = data.integrity || {};
    data.source_checker = data.source_checker || {};
    data.run_chain = data.run_chain || {};
    data.repository_gates = data.repository_gates || {};
    data.security_assurance = data.security_assurance
      && typeof data.security_assurance === "object"
      ? data.security_assurance
      : { schema_version: 2, availability: "unavailable", complete: false, tools: [] };
    data.operational_incidents = data.operational_incidents
      && typeof data.operational_incidents === "object"
      ? data.operational_incidents
      : {
          availability: "unavailable",
          complete: false,
          unresolved_count: null,
          impact_state: "gray",
          items: [],
          active_links: {},
          reason: "Operational incident feed is unavailable."
        };
    data.agent_registry = Array.isArray(data.agent_registry) ? data.agent_registry : [];
    data.automation_role_status = data.automation_role_status
      && typeof data.automation_role_status === "object"
      ? data.automation_role_status
      : { availability: "unavailable", roles: [] };
    data.repository_review_recommendations = Array.isArray(data.repository_review_recommendations)
      ? data.repository_review_recommendations
      : [];
    data.publication = data.publication || { manifest: { editions: [] }, disposition_counts: {} };
    data.publication.manifest = data.publication.manifest || { editions: [] };
    data.publication.manifest.editions = Array.isArray(data.publication.manifest.editions)
      ? data.publication.manifest.editions
      : [];
  }
  normalizeLoadedData();
  const PRIVATE_SECURITY_ASSURANCE_PATH = "data/private-security-assurance.js?v=1";
  const PRIVATE_OPERATIONS_PATH = "data/private-operations.js?v=1";
  const LOCAL_AUTOMATION_STATUS_PATH = "data/local-automation-status.js";
  const SECURITY_TOOL_FIELDS = new Set([
    "tool_id", "label", "availability", "last_checked", "next_due",
    "source_revision", "coverage_state", "private_attention", "owner_class",
    "destination_class", "active_incident", "public_intake_state"
  ]);
  let privateSecurityAssuranceSnapshot = null;
  function validPrivateSecuritySnapshot(snapshot) {
    if (!snapshot || snapshot.schema_version !== 2 || !Array.isArray(snapshot.tools)) return false;
    const topFields = [
      "schema_version", "availability", "complete", "checked_at",
      "public_intake_state", "private_attention", "active_incident", "tools"
    ];
    if (Object.keys(snapshot).length !== topFields.length
      || Object.keys(snapshot).some((key) => !topFields.includes(key))) return false;
    if (!["current", "unavailable"].includes(snapshot.availability)
      || typeof snapshot.complete !== "boolean"
      || !["live", "paused", "unverified"].includes(snapshot.public_intake_state)
      || !["required", "none_reported", "unavailable"].includes(snapshot.private_attention)
      || typeof snapshot.active_incident !== "boolean") return false;
    const publicDefinitions = new Map((data.security_assurance.tools || []).map((tool) => [
      String(tool.tool_id || ""),
      tool
    ]));
    const observed = new Set();
    for (const tool of snapshot.tools) {
      if (!tool || typeof tool !== "object") return false;
      if (Object.keys(tool).length !== SECURITY_TOOL_FIELDS.size
        || Object.keys(tool).some((key) => !SECURITY_TOOL_FIELDS.has(key))) return false;
      const toolId = String(tool.tool_id || "");
      const definition = publicDefinitions.get(toolId);
      if (!toolId || observed.has(toolId) || !definition) return false;
      if (tool.label !== definition.label
        || tool.owner_class !== definition.owner_class
        || tool.destination_class !== definition.destination_class
        || !["current", "unavailable"].includes(tool.availability)
        || !["current", "stale", "incomplete", "unavailable"].includes(tool.coverage_state)
        || !["yes", "no", "unknown"].includes(tool.private_attention)
        || typeof tool.active_incident !== "boolean"
        || ![null, "live", "paused", "unverified"].includes(tool.public_intake_state)) return false;
      observed.add(toolId);
    }
    return observed.size === publicDefinitions.size;
  }
  function capturePrivateSecurityAssurance() {
    const snapshot = window.ARRP_PRIVATE_SECURITY_ASSURANCE;
    if (!validPrivateSecuritySnapshot(snapshot)) return false;
    privateSecurityAssuranceSnapshot = snapshot;
    return true;
  }
  let privateOperationsSnapshot = null;
  function validPrivateOperationsSnapshot(snapshot) {
    const fields = [
      "schema_version", "availability", "generated_at", "catalog_generation_id",
      "source_revision", "agent_registry", "project_logs", "integrity",
      "run_chain", "privacy"
    ];
    return Boolean(
      snapshot
      && typeof snapshot === "object"
      && Object.keys(snapshot).length === fields.length
      && Object.keys(snapshot).every((key) => fields.includes(key))
      && snapshot.schema_version === 2
      && snapshot.availability === "current"
      && snapshot.catalog_generation_id === catalogGenerationId
      && snapshot.source_revision === String(data.source_revision || "")
      && parseTimestamp(snapshot.generated_at) !== null
      && Array.isArray(snapshot.agent_registry)
      && Array.isArray(snapshot.project_logs)
      && snapshot.integrity && typeof snapshot.integrity === "object"
      && snapshot.run_chain && typeof snapshot.run_chain === "object"
    );
  }
  function capturePrivateOperations() {
    const snapshot = window.ARRP_PRIVATE_OPERATIONS;
    if (!validPrivateOperationsSnapshot(snapshot)) return false;
    privateOperationsSnapshot = snapshot;
    data.agent_registry = snapshot.agent_registry;
    data.project_logs = snapshot.project_logs;
    if (snapshot.integrity && typeof snapshot.integrity === "object") {
      data.integrity = snapshot.integrity;
    }
    if (snapshot.run_chain && typeof snapshot.run_chain === "object") {
      data.run_chain = snapshot.run_chain;
    }
    return true;
  }
  function validLocalAutomationStatus(status) {
    const allowedStatuses = new Set([
      "completed", "review-required", "failed", "blocked",
      "usage-stopped", "missed", "running"
    ]);
    return Boolean(
      status
      && typeof status === "object"
      && status.schema_version === "1.0"
      && allowedStatuses.has(String(status.status || "").toLowerCase())
      && parseTimestamp(status.updated_at || status.completed_at || status.started_at) !== null
    );
  }
  function captureLocalAutomationStatus() {
    if (validLocalAutomationStatus(window.ARRP_LOCAL_AUTOMATION_STATUS)) return true;
    window.ARRP_LOCAL_AUTOMATION_STATUS = null;
    return false;
  }
  function securityAssuranceProjection(snapshot = privateSecurityAssuranceSnapshot) {
    const publicProjection = data.security_assurance || {};
    const publicTools = Array.isArray(publicProjection.tools) ? publicProjection.tools : [];
    if (!validPrivateSecuritySnapshot(snapshot)) {
      return {
        available: false,
        checkedAt: null,
        publicIntakeState: "unverified",
        privateAttention: "unavailable",
        activeIncident: false,
        tools: publicTools.map((tool) => ({ ...tool, availability: "unavailable", coverage_state: "unavailable", private_attention: "unknown" }))
      };
    }
    const privateById = new Map(snapshot.tools.map((tool) => [tool.tool_id, tool]));
    return {
      available: snapshot.availability === "current" && snapshot.complete === true,
      checkedAt: snapshot.checked_at || null,
      publicIntakeState: ["live", "paused"].includes(snapshot.public_intake_state)
        ? snapshot.public_intake_state
        : "unverified",
      privateAttention: ["required", "none_reported"].includes(snapshot.private_attention)
        ? snapshot.private_attention
        : "unavailable",
      activeIncident: snapshot.active_incident === true,
      tools: publicTools.map((tool) => ({ ...tool, ...(privateById.get(tool.tool_id) || {}) }))
    };
  }
  if (window.__ARRP_CONSOLE_TEST_MODE__) capturePrivateSecurityAssurance();
  const catalogGenerationId = String(
    data.generation_id || data.generation_manifest?.generation_id || ""
  );
  const consoleOpenedAt = new Date().toISOString();

  const byId = (id) => document.getElementById(id);
  const preliminaryState = { search: "", term: "all", area: "all" };
  const proposedState = {
    search: "",
    level: "all",
    status: "all",
    area: "all",
    priority: "all",
    gap: "all",
    monitoring: "all",
    trigger: "all",
    sort: "attention"
  };
  const sourceStates = {
    sources: {
      search: "",
      filter: "all",
      exactType: "all",
      reviewed: "all",
      reliability: "all",
      monitoring: "all",
      health: "all",
      page: 1,
      sortKey: null,
      sortDirection: "asc"
    }
  };
  const pipelineState = {
    mode: "active",
    search: "",
    workClass: "all",
    scope: "active-development",
    sort: "pipeline",
    status: "all",
    development: "all",
    area: "all",
    owner: "all",
    priority: "all",
    releaseBlocker: "all",
    gap: "all",
    selectedId: "",
    focused: false,
    sourceContext: "",
    sourceReference: "",
    returnTarget: "",
    items: []
  };
  const pendingState = { search: "", owner: "all" };
  const manualWatchState = { search: "", kind: "all" };
  const courtWatchState = { search: "", owner: "all", updatesOnly: false, page: 1 };
  const directiveState = { search: "", administration: "all", status: "all", updatesOnly: false, page: 1, sortKey: "date", sortDirection: "desc" };
  const sourceCheckerState = {
    search: "",
    classification: "all",
    domain: "all",
    owner: "all",
    sortKey: "classification",
    sortDirection: "asc",
    page: 1
  };
  const pageState = { search: "", level: "all", section: "all", sortKey: "section", sortDirection: "asc", page: 1 };
  const publicationState = { edition: "public-proposal" };
  const releaseBlockerState = { status: "all", priority: "all", owner: "all" };
  const publicationLengthState = { sortKey: "estimated_pages", sortDirection: "desc" };
  const problemState = { search: "", owner: "all", severity: "all", status: "all" };
  const actionInboxState = {
    filter: "mine",
    search: "",
    layout: "right",
    selectedId: "",
    items: []
  };
  const incidentLogState = {
    scope: "unresolved",
    search: "",
    selectedId: ""
  };
  const assemblyDrafts = new Map();
  const assemblyOperations = new Map();
  const automationConfigurationDrafts = new Map();
  const automationRoleState = {
    selectedId: "run-coordinator-bot",
    unavailableId: ""
  };
  const logStates = {};
  const PAGE_SIZE = 50;
  const SOURCE_CHECKER_PAGE_SIZE = 50;
  let pageIndex = new Map(data.page_inventory.map((record) => [record.path, record]));

  const LAYOUT_STORAGE_KEY = "arrp-project-console-layout-v1";
  const LAYOUT_PLACEMENTS_KEY = "__placements";
  const LAYOUT_WIDTHS = Object.freeze({
    full: "Full",
    half: "Half",
    third: "Third",
    quarter: "Quarter",
    compact: "Compact"
  });
  const DISCLOSURE_STORAGE_KEY = "arrp-project-console-disclosures-v1";
  const WORKFLOW_SUMMARY_STORAGE_KEY = "arrp-project-console-intro-hidden-v1";
  const ACTION_INBOX_LAYOUT_STORAGE_KEY = "arrp-project-console-action-inbox-layout-v1";
  const layoutZones = new Map();
  const successfulStageHistory = new Map();
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
  const LIVE_PULL_REQUESTS_URL = "https://api.github.com/repos/Thorncrag/ARRP/pulls?state=open&per_page=100";
  const OPENAI_STATUS_URL = "https://status.openai.com/api/v2/status.json";
  const OPENAI_COMPONENTS_URL = "https://status.openai.com/api/v2/components.json";
  const OPENAI_INCIDENTS_URL = "https://status.openai.com/api/v2/incidents/unresolved.json";
  const VERCEL_STATUS_URL = "https://www.vercel-status.com/api/v2/status.json";
  const VERCEL_COMPONENTS_URL = "https://www.vercel-status.com/api/v2/components.json";
  const VERCEL_INCIDENTS_URL = "https://www.vercel-status.com/api/v2/incidents/unresolved.json";
  const CLOUDFLARE_COMPONENTS_URL = "https://www.cloudflarestatus.com/api/v2/components.json";
  const CLOUDFLARE_INCIDENTS_URL = "https://www.cloudflarestatus.com/api/v2/incidents/unresolved.json";
  const GITHUB_BLOB_ROOT = "https://github.com/Thorncrag/ARRP/blob/main/";
  const LIVE_SITE_ROOT = "https://thorncrag.github.io/ARRP/";
  const SCRIPT_VERSION = "49";
  const sourceCatalogScripts = Array.from(
    { length: 16 },
    (_, index) => `data/sources-catalog-${String(index + 1).padStart(3, "0")}.js?v=${SCRIPT_VERSION}`
  );
  const directiveCatalogScripts = Array.from(
    { length: 16 },
    (_, index) => `data/directives-catalog-${String(index + 1).padStart(3, "0")}.js?v=${SCRIPT_VERSION}`
  );
  const DOMAIN_SCRIPTS = Object.freeze({
    overview: [`data/overview.js?v=${SCRIPT_VERSION}`],
    candidates: [`data/candidates.js?v=${SCRIPT_VERSION}`],
    progress: [`data/progress.js?v=${SCRIPT_VERSION}`],
    sources: [`data/sources.js?v=${SCRIPT_VERSION}`, ...sourceCatalogScripts, ...directiveCatalogScripts],
    "source-checker": [`data/source-checker.js?v=${SCRIPT_VERSION}`],
    integrity: [`data/integrity.js?v=${SCRIPT_VERSION}`],
    automation: [`data/automation.js?v=${SCRIPT_VERSION}`],
    logs: [`data/logs.js?v=${SCRIPT_VERSION}`],
    publication: [`data/publication.js?v=${SCRIPT_VERSION}`]
  });
  const domainLoads = new Map();
  const loadedDomains = new Set();
  const loadedScripts = new Set(
    [...document.querySelectorAll("script[src]")].map((script) => script.getAttribute("src"))
  );
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
    courts: { count: 0, totalCount: 0, proposalCount: 0, url: "", ids: new Set(), state: "pending", reason: "" },
    directives: {
      count: data.presidential_directives.filter((record) => /^(New|Changed) since/.test(record.review_status || "")).length,
      totalCount: 0,
      proposalCount: 0,
      url: "",
      ids: new Set(data.presidential_directives
        .filter((record) => /^(New|Changed) since/.test(record.review_status || ""))
        .map((record) => record.id)),
      state: "checked-in",
      reason: ""
    },
    pullRequests: [],
    pullRequestsStatus: "pending",
    pullRequestsCheckedAt: null
  };
  const PLATFORM_PROVIDER_SPECS = Object.freeze({
    openai: {
      label: "OpenAI",
      source: "https://status.openai.com/",
      registrations: [
        { id: "gpts", label: "GPTs", names: ["GPTs"] },
        { id: "codex", label: "Codex", names: ["Codex in ChatGPT Desktop", "Codex API", "Codex Web", "CLI", "VS Code extension"] },
        { id: "api-platform", label: "API platform", names: ["Responses", "Chat Completions", "Realtime", "Files", "Embeddings"] }
      ]
    },
    vercel: {
      label: "Vercel",
      source: "https://www.vercel-status.com/",
      registrations: [
        { id: "j7g76bfzc8hw", label: "CDN", exactName: "CDN" },
        { id: "kgcsn9c73xzf", label: "Functions", exactName: "Functions" },
        { id: "xxh50pzvy03x", label: "Firewall", exactName: "Firewall" },
        { id: "bc3cl3q4jn9m", label: "TLS Certificates", exactName: "TLS Certificates" },
        { id: "7ckq6xr6nsbv", label: "Builds", exactName: "Builds" },
        { id: "hpqj1ys9gr78", label: "Git Integrations", exactName: "Git Integrations" }
      ]
    },
    cloudflare: {
      label: "Cloudflare",
      source: "https://www.cloudflarestatus.com/",
      registrations: [
        { id: "m4jywscr0n0k", label: "Turnstile", exactName: "Turnstile" }
      ]
    }
  });
  const platformSignals = {
    schemaVersion: 1,
    providers: {
      openai: { availability: "pending", complete: false, checkedAt: null, components: [], incidents: [], lastValid: null },
      vercel: { availability: "pending", complete: false, checkedAt: null, components: [], incidents: [], lastValid: null },
      cloudflare: { availability: "pending", complete: false, checkedAt: null, components: [], incidents: [], lastValid: null }
    }
  };

  function text(value, fallback = "—") {
    return value === null || value === undefined || value === "" ? String(fallback) : String(value);
  }

  function normalizeTerm(term) {
    const value = String(term ?? "").trim().toLowerCase().replaceAll("_", " ").replaceAll("-", " ");
    if (["1", "first", "first term", "trump i", "trump 1"].includes(value)) return "trump-i";
    if (["2", "second", "second term", "trump ii", "trump 2"].includes(value)) return "trump-ii";
    if (["both", "both terms", "trump i and ii", "trump i & ii"].includes(value)) return "both";
    return value ? "unavailable" : "unavailable";
  }

  function termLabel(term) {
    const normalized = normalizeTerm(term);
    if (normalized === "trump-i") return "Trump I";
    if (normalized === "trump-ii") return "Trump II";
    if (normalized === "both") return "Trump I and Trump II";
    return "Term not recorded";
  }

  function parseTimestamp(value) {
    if (!value) return null;
    if (typeof value === "number" && Number.isFinite(value)) return value;
    const normalized = String(value)
      .trim()
      .replace(/([+-]\d{2})(\d{2})$/, "$1:$2");
    const timestamp = Date.parse(normalized);
    return Number.isFinite(timestamp) ? timestamp : null;
  }

  function formatDate(value) {
    const dateOnly = typeof value === "string"
      && /^\d{4}-\d{2}-\d{2}$/.test(value.trim());
    if (dateOnly) {
      const [year, month, day] = value.trim().split("-").map(Number);
      return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" })
        .format(new Date(year, month - 1, day));
    }
    const timestamp = parseTimestamp(value);
    if (timestamp === null) return value ? String(value) : "Not recorded";
    const date = new Date(timestamp);
    return Number.isNaN(date.valueOf())
      ? value
      : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
  }

  function formatOperationalDate(value) {
    const timestamp = parseTimestamp(value);
    if (timestamp === null) return value ? String(value) : "Not recorded";
    return new Intl.DateTimeFormat(undefined, {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZoneName: "short"
    }).format(new Date(timestamp));
  }

  function nextScheduledCoordinatorRun(afterValue = Date.now()) {
    const timestamp = parseTimestamp(afterValue) ?? Date.now();
    const candidate = new Date(timestamp);
    candidate.setHours(2, 0, 0, 0);
    if (candidate.getTime() < timestamp) candidate.setDate(candidate.getDate() + 1);
    return candidate.toISOString();
  }

  function scorePresentation(value) {
    if (value === null || value === undefined || value === "") {
      return { label: "Score unavailable", valid: true, available: false, value: null };
    }
    if (typeof value === "boolean") {
      return { label: `Invalid score: ${text(value)}`, valid: false, available: true, value };
    }
    const numeric = Number(value);
    if (!Number.isFinite(numeric) || numeric < 0 || numeric > 100) {
      return { label: `Invalid score: ${text(value)}`, valid: false, available: true, value: numeric };
    }
    return { label: `Score ${numeric}`, valid: true, available: true, value: numeric };
  }

  function integrityComponentValue(state, value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "Unavailable";
    if (["unavailable", "incomplete", "undeclared"].includes(state?.state)) return "Unavailable";
    if (numeric === 0 && !(state?.complete === true && ["current", "available"].includes(state.state))) {
      return "Unavailable";
    }
    return numeric;
  }

  function sourceTypeFamily(type) {
    const value = String(type || "").toLowerCase();
    if (/court|judicial|opinion|case|docket/.test(value)) return "Judicial";
    if (/congress|legislat|statute|hearing|committee|bill/.test(value)) return "Legislative";
    if (/government|official|agency|executive order|directive|regulation|constitution/.test(value)) return "Government";
    if (/journal|research|study|academic|scholarly|book/.test(value)) return "Scholarly";
    if (/news|media|article|press|reporting/.test(value)) return "News";
    if (/advocacy|ngo|civil society|association/.test(value)) return "Advocacy";
    if (/tracker|database|index|dashboard/.test(value)) return "Tracker";
    return "Other";
  }

  function feedContractState(feed = {}, fallbackTimestamp = "") {
    const availability = String(feed.availability || "").toLowerCase();
    const completeness = feed.completeness && typeof feed.completeness === "object"
      ? feed.completeness
      : null;
    const expected = Number(feed.expected_count ?? completeness?.expected_count);
    const actual = Number(feed.actual_count ?? completeness?.actual_count);
    const complete = completeness?.complete;
    const errors = Array.isArray(feed.projection_errors) ? feed.projection_errors : [];
    const errorReason = errors.map((error) => {
      if (typeof error === "string") return error;
      if (error && typeof error === "object") return error.message || error.code || "Projection error";
      return String(error);
    }).join("; ");
    let state = availability || "undeclared";
    if (errors.length || complete === false || (Number.isFinite(expected) && Number.isFinite(actual) && expected !== actual)) {
      state = state === "unavailable" ? "unavailable" : "incomplete";
    }
    const label = {
      available: "Available",
      current: "Current",
      stale: "Stale by producer declaration",
      unavailable: "Unavailable",
      incomplete: "Incomplete projection",
      undeclared: "Currentness not declared"
    }[state] || `Unknown state: ${state}`;
    return {
      state,
      label,
      complete: (complete === true
        || (complete == null && ["available", "current", "stale"].includes(state)))
        && !errors.length
        && !(Number.isFinite(expected) && Number.isFinite(actual) && expected !== actual),
      expected: Number.isFinite(expected) ? expected : null,
      actual: Number.isFinite(actual) ? actual : null,
      reason: typeof completeness?.reason === "string"
        ? completeness.reason
        : errorReason,
      timestamp: feed.generated_at || feed.checked_at || fallbackTimestamp || ""
    };
  }

  function operationalFeedState(chain = {}) {
    const timestamp = chain.host_updated_at || chain.updated_at
      || chain.completed_at || chain.created_at || "";
    const declared = feedContractState(chain, timestamp);
    if (declared.state !== "undeclared") return declared;
    const hasIdentity = Boolean(chain.chain_id || chain.id);
    const hasStatus = Boolean(chain.host_status || chain.status || chain.outcome);
    if (hasIdentity && hasStatus && parseTimestamp(timestamp) !== null) {
      return {
        ...declared,
        state: "available",
        label: "Available",
        complete: true,
        reason: "Legacy typed chain status; producer completeness was not yet declared.",
        timestamp
      };
    }
    return declared;
  }

  function shouldAcceptLiveFeed(kindOrCurrent = {}, currentOrIncoming = {}, maybeIncoming = {}) {
    const kind = typeof kindOrCurrent === "string" ? kindOrCurrent : "generic";
    const current = typeof kindOrCurrent === "string" ? currentOrIncoming : kindOrCurrent;
    const incoming = typeof kindOrCurrent === "string" ? maybeIncoming : currentOrIncoming;
    const contractView = (feed) => feed?.producer_contract && typeof feed.producer_contract === "object"
      ? { ...feed, ...feed.producer_contract }
      : feed || {};
    const currentView = contractView(current);
    const incomingView = contractView(incoming);
    const currentContract = feedContractState(currentView);
    const incomingContract = feedContractState(incomingView);
    if (currentContract.complete && !incomingContract.complete) return false;
    const currentTime = parseTimestamp(
      currentView.generated_at || currentView.generatedAt || currentView.checked_at
        || currentView.updated_at || currentView.asOf || currentView.as_of
        || currentView.current?.generated_at
    );
    const incomingTime = parseTimestamp(
      incomingView.generated_at || incomingView.generatedAt || incomingView.checked_at
        || incomingView.updated_at || incomingView.asOf || incomingView.as_of
        || incomingView.current?.generated_at
    );
    if (currentTime !== null && incomingTime !== null && incomingTime < currentTime) return false;
    const currentRevision = String(currentView.source_revision || currentView.revision
      || currentView.current?.source_revision || currentView.current?.revision || "");
    const incomingRevision = String(incomingView.source_revision || incomingView.revision
      || incomingView.current?.source_revision || incomingView.current?.revision || "");
    const currentGeneration = String(currentView.generation_id || "");
    const incomingGeneration = String(incomingView.generation_id || "");
    const identityDiffers = Boolean(
      (currentRevision && incomingRevision && currentRevision !== incomingRevision)
      || (currentGeneration && incomingGeneration && currentGeneration !== incomingGeneration)
    );
    if (!identityDiffers) return true;
    const explicitlySupersedes = [
      incomingView.supersedes_source_revision,
      incomingView.previous_source_revision,
      incomingView.supersedes_generation_id,
      ...(Array.isArray(incomingView.superseded_source_revisions) ? incomingView.superseded_source_revisions : [])
    ].map(String).some((value) => value && [currentRevision, currentGeneration].includes(value));
    if (explicitlySupersedes) return true;
    if (!incomingContract.complete || incomingTime === null
        || (currentTime !== null && incomingTime <= currentTime)) return false;
    if (kind === "progress" || kind === "integrity" || kind === "run-chain") return true;
    if (kind === "source-checker") {
      const authoritativeHashes = current.current_catalog_coverage?.source_hashes || {};
      const incomingHashes = incomingView.source_hashes
        || incoming.current_catalog_coverage?.source_hashes
        || {};
      const expectedEntries = Object.entries(authoritativeHashes);
      return incoming.current_catalog_coverage?.complete === true
        || (expectedEntries.length > 0
          && expectedEntries.length === Object.keys(incomingHashes).length
          && expectedEntries.every(([key, hash]) => incomingHashes[key] === hash));
    }
    return false;
  }

  function validateLivePayload(kind, payload, current = {}) {
    const errors = [];
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      return { valid: false, errors: ["Payload is not an object."] };
    }
    const contract = payload.producer_contract && typeof payload.producer_contract === "object"
      ? { ...payload, ...payload.producer_contract }
      : payload;
    const schema = Number(payload.schema_version ?? payload.schemaVersion);
    const minimumSchema = kind === "progress" ? 2 : 1;
    if (!Number.isFinite(schema) || schema < minimumSchema) errors.push(`Schema version ${minimumSchema} or later is required.`);
    const availability = contract.availability;
    if (availability !== undefined && !["current", "available", "stale", "unavailable"].includes(String(availability))) {
      errors.push("Availability is not a recognized contract value.");
    }
    if (contract.projection_errors !== undefined && !Array.isArray(contract.projection_errors)) {
      errors.push("projection_errors must be an array.");
    }
    const completeness = contract.completeness;
    if (completeness !== undefined) {
      if (!completeness || typeof completeness !== "object" || Array.isArray(completeness)) {
        errors.push("completeness must be an object.");
      } else {
        const expected = Number(completeness.expected_count ?? contract.expected_count);
        const actual = Number(completeness.actual_count ?? contract.actual_count);
        if (!Number.isFinite(expected) || expected < 0 || !Number.isFinite(actual) || actual < 0) {
          errors.push("Completeness counts must be nonnegative numbers.");
        }
        if (typeof completeness.complete !== "boolean") errors.push("completeness.complete must be boolean.");
        if (completeness.complete === true && expected !== actual) errors.push("A complete feed cannot declare unequal expected and actual counts.");
      }
    }
    const timestamp = kind === "progress"
      ? contract.generatedAt || contract.asOf || contract.generated_at
      : kind === "integrity"
        ? payload.current?.generated_at
        : kind === "source-checker"
          ? contract.checked_at
          : kind === "host-status"
            ? contract.host_updated_at || contract.updated_at
          : contract.updated_at || contract.completed_at || contract.created_at;
    if (parseTimestamp(timestamp) === null) errors.push("A valid producer timestamp is required.");
    if (kind === "source-checker") {
      if (!Array.isArray(payload.results)) errors.push("results must be an array.");
      else {
        const ids = payload.results.map((record) => String(record?.source_id || ""));
        if (ids.some((id) => !id)) errors.push("Every source result must have a source_id.");
        if (new Set(ids).size !== ids.length) errors.push("Source result IDs must be unique.");
        const eligible = Number(payload.eligible_urls);
        if (!Number.isFinite(eligible) || eligible < 0 || eligible !== payload.results.length) {
          errors.push("eligible_urls must equal the result-set length.");
        }
        if (!payload.counts || typeof payload.counts !== "object" || Array.isArray(payload.counts)) {
          errors.push("Classification counts must be an object.");
        } else {
          const aggregate = new Map();
          payload.results.forEach((record) => {
            const classification = String(record.classification || "");
            aggregate.set(classification, (aggregate.get(classification) || 0) + 1);
          });
          const declaredTotal = Object.values(payload.counts).reduce((sum, value) => sum + Number(value || 0), 0);
          if (declaredTotal !== payload.results.length) errors.push("Classification counts do not sum to the result-set length.");
          aggregate.forEach((count, classification) => {
            if (Number(payload.counts[classification]) !== count) errors.push(`Classification count mismatch for ${classification || "blank classification"}.`);
          });
        }
      }
    } else if (kind === "progress") {
      if (!payload.metrics || typeof payload.metrics !== "object") errors.push("Progress metrics are required.");
      if (!Array.isArray(payload.proposals)) errors.push("Progress proposals must be an array.");
      else {
        const ids = payload.proposals.map((record) => String(record?.identifier || ""));
        if (ids.some((id) => !id) || new Set(ids).size !== ids.length) errors.push("Progress proposal identifiers must be present and unique.");
        if (Number.isFinite(Number(payload.metrics?.total)) && Number(payload.metrics.total) !== payload.proposals.length) {
          errors.push("Progress metrics.total does not match the proposal inventory.");
        }
      }
    } else if (kind === "integrity") {
      if (!payload.current || typeof payload.current !== "object") errors.push("Integrity current state is required.");
      const findings = payload.current?.findings;
      if (!Array.isArray(findings)) errors.push("Integrity findings must be an array.");
      else if (Number(payload.current?.counts?.findings) !== findings.length) errors.push("Integrity finding count does not match the finding inventory.");
      if (payload.history !== undefined && !Array.isArray(payload.history)) errors.push("Integrity history must be an array.");
    } else if (kind === "run-chain") {
      if (!String(payload.chain_id || payload.id || "")) errors.push("Run-chain identity is required.");
      const stages = Array.isArray(payload.stages)
        ? payload.stages
        : payload.stages && typeof payload.stages === "object"
          ? Object.entries(payload.stages).map(([id, stage]) => ({ id, ...(stage || {}) }))
          : null;
      if (!stages) errors.push("Run-chain stages must be an array or keyed object.");
      else {
        const ids = stages.map((stage) => String(stage.id || stage.stage_id || ""));
        if (ids.some((id) => !id) || new Set(ids).size !== ids.length) errors.push("Run-chain stage IDs must be present and unique.");
      }
    } else if (kind === "host-status") {
      if (payload.projection_kind !== "host-run-status") errors.push("Host-status projection kind is invalid.");
      if (!String(payload.chain_id || "")) errors.push("Host-status chain identity is required.");
      if (!["blocked", "completed", "failed", "human-review", "launch-deferred", "not-launched", "running", "usage-stopped"]
        .includes(String(payload.host_status || ""))) errors.push("Host-status value is invalid.");
      if (!String(payload.stage || "")) errors.push("Host-status stage is required.");
      if (payload.host_action_items !== undefined && !Array.isArray(payload.host_action_items)) {
        errors.push("Host-status action items must be an array.");
      }
      if (payload.host_closeout !== undefined) {
        if (!payload.host_closeout || typeof payload.host_closeout !== "object" || Array.isArray(payload.host_closeout)) {
          errors.push("Host-status closeout must be an object.");
        } else if (!/^[0-9a-f]{40}$/.test(String(payload.host_closeout.commit || ""))) {
          errors.push("Host-status closeout commit is invalid.");
        }
      }
    } else if (kind === "automation-health") {
      if (payload.projection_kind !== "cloud-automation-health") errors.push("Automation-health projection kind is invalid.");
      if (!String(payload.chain_id || "")) errors.push("Automation-health chain identity is required.");
      if (!["healthy", "failed"].includes(String(payload.status || ""))) errors.push("Automation-health status is invalid.");
      if (!String(payload.workflow_run_id || "")) errors.push("Automation-health workflow run identity is required.");
    }
    const currentForFreshness = current;
    const incomingForFreshness = payload;
    if (currentForFreshness && Object.keys(currentForFreshness).length
        && !shouldAcceptLiveFeed(kind, currentForFreshness, incomingForFreshness)) {
      errors.push("The payload is older, incomplete, or not proven to supersede the current revision/generation.");
    }
    return { valid: errors.length === 0, errors };
  }

  function loadScriptOnce(source) {
    if (loadedScripts.has(source)) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = source;
      script.async = false;
      script.dataset.consoleDomainScript = "true";
      script.addEventListener("load", () => {
        loadedScripts.add(source);
        resolve();
      }, { once: true });
      script.addEventListener("error", () => reject(new Error(`Could not load ${source}`)), { once: true });
      document.body.append(script);
    });
  }

  function domainGenerationStatus(expectedGeneration, filename, domainGeneration, manifest) {
    if (!expectedGeneration) {
      return { valid: true, legacy: true, reason: "Catalog generation identity is not declared." };
    }
    const declared = typeof domainGeneration === "string"
      ? domainGeneration
      : domainGeneration && typeof domainGeneration === "object"
        ? domainGeneration[filename]
        : "";
    if (!declared) return { valid: false, reason: `${filename} did not declare its domain generation.` };
    if (String(declared) !== String(expectedGeneration)) {
      return { valid: false, reason: `${filename} belongs to generation ${declared}, not ${expectedGeneration}.` };
    }
    const files = manifest?.files;
    const entry = files && typeof files === "object" ? files[filename] : null;
    if (!entry) return { valid: false, reason: `${filename} is absent from the catalog generation manifest.` };
    if (String(entry.generation_id || "") !== String(expectedGeneration)) {
      return { valid: false, reason: `${filename} manifest generation does not match the catalog.` };
    }
    if (!/^(?:sha256:)?[a-f0-9]{64}$/i.test(String(entry.sha256 || ""))
        || !Number.isFinite(Number(entry.bytes))
        || Number(entry.bytes) <= 0) {
      return { valid: false, reason: `${filename} manifest hash or byte metadata is incomplete.` };
    }
    return { valid: true, legacy: false, reason: "" };
  }

  function validateLoadedDomainScript(source) {
    const filename = source.split("?")[0].split("/").pop();
    const result = domainGenerationStatus(
      catalogGenerationId,
      filename,
      data.domain_generation,
      data.generation_manifest
    );
    if (!result.valid) throw new Error(`Mixed or incomplete Console data bundle: ${result.reason}`);
  }

  async function ensureDomain(domain, { optional = false } = {}) {
    if (loadedDomains.has(domain)) return true;
    if (domainLoads.has(domain)) return domainLoads.get(domain);
    const scripts = DOMAIN_SCRIPTS[domain] || [];
    const promise = (async () => {
      try {
        for (const source of scripts) {
          await loadScriptOnce(source);
          validateLoadedDomainScript(source);
        }
        normalizeLoadedData();
        // Public domain files carry only safe summaries. Restore the complete
        // ignored owner-local projection after a domain assignment replaces it.
        if (privateOperationsSnapshot) capturePrivateOperations();
        loadedDomains.add(domain);
        hydrateLoadedDomain(domain);
        return true;
      } catch (error) {
        if (!optional) {
          console.error(error);
          showDomainError(domain, error);
        }
        return false;
      } finally {
        domainLoads.delete(domain);
      }
    })();
    domainLoads.set(domain, promise);
    return promise;
  }

  function announce(message) {
    const node = byId("console-announcer");
    if (!node) return;
    node.textContent = "";
    window.setTimeout(() => { node.textContent = message; }, 20);
  }

  function focusToken() {
    const active = document.activeElement;
    if (!active || active === document.body) return null;
    return {
      id: active.id || "",
      key: active.dataset?.focusKey || "",
      selectionStart: typeof active.selectionStart === "number" ? active.selectionStart : null
    };
  }

  function restoreFocus(token, message = "") {
    window.requestAnimationFrame(() => {
      const target = token?.id
        ? byId(token.id)
        : token?.key
          ? document.querySelector(`[data-focus-key="${CSS.escape(token.key)}"]`)
          : null;
      if (target) {
        target.focus({ preventScroll: true });
        if (token.selectionStart !== null && typeof target.setSelectionRange === "function") {
          target.setSelectionRange(token.selectionStart, token.selectionStart);
        }
      }
      if (message) announce(message);
    });
  }

  function rerenderPreservingFocus(render, message = "") {
    const token = focusToken();
    render();
    restoreFocus(token, message);
  }

  function showDomainError(domain, error) {
    const panel = byId(`panel-${domain === "candidates" ? "candidates" : domain}`);
    if (panel) panel.setAttribute("aria-busy", "false");
    announce(`${domain} data is unavailable. ${error.message}`);
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

  function consoleLinkButton(label, hash, secondary = true) {
    const anchor = element("a", secondary ? "record-link secondary" : "record-link", label);
    anchor.href = hash;
    return anchor;
  }

  function inlineLink(label, url) {
    const anchor = element("a", "inline-link", label);
    anchor.href = url;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
    return anchor;
  }

  function internalInlineLink(label, target) {
    const anchor = element("a", "inline-link", label);
    anchor.href = target.startsWith("#") ? target : `#${target}`;
    anchor.addEventListener("click", (event) => {
      event.preventDefault();
      navigateToConsoleTarget(anchor.getAttribute("href").replace(/^#/, ""));
    });
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
    button.dataset.focusKey = `sort:${key}`;
    button.append(
      element("span", "", label),
      element("span", "sort-indicator", active ? (state.sortDirection === "asc" ? "▲" : "▼") : "↕")
    );
    button.querySelector(".sort-indicator").setAttribute("aria-hidden", "true");
    button.addEventListener("click", () => {
      if (state.sortKey === key) {
        state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = key;
        state.sortDirection = "asc";
      }
      state.page = 1;
      rerenderPreservingFocus(render, `${label} sorted ${state.sortDirection === "asc" ? "ascending" : "descending"}.`);
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
    card.id = `candidate-${record.id}`;
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
    const links = element("div", "source-list dossier-actions");
    const workbenchTarget = workbenchTargetForArtifact(record.id, {
      source: "Preliminary Candidates",
      reference: record.id,
      returnTarget: `planning:preliminary:selected=${encodeURIComponent(record.id)}`
    });
    if (workbenchTarget) links.append(internalInlineLink("Open in Workbench", workbenchTarget));
    card.append(header, defect, details, sources, footer, links);
    return card;
  }

  function proposedCard(record) {
    const card = element("details", "candidate-card formal-card");
    card.id = `candidate-${record.id}`;
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
    const score = scorePresentation(record.score);
    lifecycle.append(
      labeledValue("Development level", record.development_level),
      labeledValue("Workflow status", record.workflow_status),
      labeledValue("Score", score.label),
      labeledValue("Priority", record.priority),
      labeledValue("Workstream", record.workstream),
      labeledValue("Audit runs", record.runs),
      labeledValue("Rebaseline status", record.rebaseline_status),
      labeledValue("Change Audit needed", record.change_audit_needed),
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
    const workbenchTarget = workbenchTargetForArtifact(record.id, {
      source: "Candidates",
      reference: record.id,
      returnTarget: `planning:candidates:selected=${encodeURIComponent(record.id)}`
    });
    if (workbenchTarget) links.append(internalInlineLink("Open in Workbench", workbenchTarget));
    links.append(linkButton("Open GitHub issue", record.issue_url));
    if (record.canonical_page && record.canonical_page !== record.issue_url) {
      links.append(linkButton("Open canonical page", record.canonical_page, true));
    }
    links.append(linkButton("Open Horizon intake history", record.horizon_log_url, true));
    card.append(header, summary, lifecycle, panels, recordCheck, links);
    return card;
  }

  function candidateProjectRecords() {
    const projectCandidates = Array.isArray(data.progress?.candidates) ? data.progress.candidates : [];
    const projectIndex = new Map(projectCandidates.map((record) => [
      String(record.identifier || record.id || ""),
      record
    ]));
    return data.active_horizon_records.map((record) => {
      const project = projectIndex.get(String(record.id)) || {};
      return {
        ...record,
        title: project.title ?? record.title,
        development_level: project.developmentLevel ?? project.development_level ?? record.development_level,
        workflow_status: project.workflowStatus ?? project.workflow_status ?? record.workflow_status,
        priority: project.priority ?? record.priority,
        release_blocker: project.releaseBlocker ?? project.release_blocker ?? record.release_blocker,
        workstream: project.workstream ?? record.workstream,
        owner: project.owner ?? record.owner ?? record.assignee,
        runs: project.runs ?? record.runs,
        score: project.score ?? record.score,
        rebaseline_status: project.rebaselineStatus ?? project.rebaseline_status ?? record.rebaseline_status,
        change_audit_needed: project.changeAuditNeeded ?? project.change_audit_needed ?? record.change_audit_needed,
        next_audit: project.nextAudit ?? project.next_audit ?? record.next_audit,
        needs_monitoring: project.needsMonitoring ?? project.needs_monitoring ?? record.needs_monitoring,
        monitoring_trigger: project.monitoringTrigger ?? project.monitoring_trigger ?? record.monitoring_trigger,
        next_trigger: project.nextTrigger ?? project.next_trigger ?? project.followUp ?? record.next_trigger ?? record.horizon_history?.follow_up,
        last_audit: project.lastAudit ?? project.last_audit ?? record.last_audit,
        updated_at: project.updatedAt ?? project.updated_at ?? record.updated_at
      };
    });
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
    const selected = [...config.container.querySelectorAll(config.selector)]
      .filter((node) => node.parentElement === config.container);
    const transferred = [...config.container.children].filter((node) =>
      node.dataset.layoutTransferGroup
      && config.acceptedTransferGroups.has(node.dataset.layoutTransferGroup));
    return [...new Set([...selected, ...transferred])];
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

  function layoutSizeKey(config) {
    return `${config.key}:sizes`;
  }

  function layoutItemDefaultWidth(item, config) {
    return item.dataset.layoutDefaultWidth || config.defaultWidth || "full";
  }

  function setLayoutItemWidth(item, config, width) {
    if (!config.sizable) return;
    const preferences = readLayoutPreferences();
    const key = layoutSizeKey(config);
    const sizes = preferences[key] && typeof preferences[key] === "object"
      ? { ...preferences[key] }
      : {};
    if (width === "default") delete sizes[item.dataset.layoutId];
    else if (Object.prototype.hasOwnProperty.call(LAYOUT_WIDTHS, width)) {
      sizes[item.dataset.layoutId] = width;
    }
    if (Object.keys(sizes).length) preferences[key] = sizes;
    else delete preferences[key];
    const saved = writeLayoutPreferences(preferences);
    applyLayoutZone(config);
    byId("layout-status").textContent = saved
      ? "Layout size saved in this browser."
      : "This browser did not permit saving; the size will last until reload.";
    announce(
      `${item.querySelector("h2, h3, h4, strong")?.textContent || "Item"} width set to ${
        width === "default"
          ? `project default (${LAYOUT_WIDTHS[layoutItemDefaultWidth(item, config)]})`
          : LAYOUT_WIDTHS[width]
      }.`
    );
  }

  function compatibleLayoutZones(item) {
    const transferGroup = item.dataset.layoutTransferGroup;
    if (!transferGroup) return [];
    return [...layoutZones.values()].filter((config) =>
      config.acceptedTransferGroups.has(transferGroup));
  }

  function layoutConfigForItem(item) {
    return [...layoutZones.values()].find((config) =>
      config.container === item.parentElement
      && layoutItems(config).includes(item));
  }

  function moveLayoutItemToZone(item, targetKey) {
    const sourceConfig = layoutConfigForItem(item);
    const targetConfig = layoutZones.get(targetKey);
    const transferGroup = item.dataset.layoutTransferGroup;
    if (!sourceConfig || !targetConfig || sourceConfig === targetConfig) return;
    if (!targetConfig.acceptedTransferGroups.has(transferGroup)) return;
    targetConfig.container.append(item);
    const preferences = readLayoutPreferences();
    const placements = preferences[LAYOUT_PLACEMENTS_KEY]
      && typeof preferences[LAYOUT_PLACEMENTS_KEY] === "object"
      ? { ...preferences[LAYOUT_PLACEMENTS_KEY] }
      : {};
    if (targetConfig.key === item.dataset.layoutOriginZone) {
      delete placements[item.dataset.layoutId];
    } else {
      placements[item.dataset.layoutId] = targetConfig.key;
    }
    if (Object.keys(placements).length) preferences[LAYOUT_PLACEMENTS_KEY] = placements;
    else delete preferences[LAYOUT_PLACEMENTS_KEY];
    preferences[sourceConfig.key] = layoutItems(sourceConfig).map((node) => node.dataset.layoutId);
    preferences[targetConfig.key] = layoutItems(targetConfig).map((node) => node.dataset.layoutId);
    const saved = writeLayoutPreferences(preferences);
    applyLayoutZone(sourceConfig);
    applyLayoutZone(targetConfig);
    const itemLabel = item.querySelector("h2, h3, h4, strong")?.textContent || "Item";
    byId("layout-status").textContent = saved
      ? `${itemLabel} moved to ${targetConfig.label}.`
      : `${itemLabel} moved, but this browser did not permit saving the placement.`;
    announce(`${itemLabel} moved to ${targetConfig.label}.`);
  }

  function refreshLayoutHandles(config) {
    const items = layoutItems(config);
    items.forEach((item, index) => {
      item.draggable = layoutEditing;
      item.classList.add("layout-item");
      if (!layoutEditing) {
        [...item.children]
          .filter((child) => child.classList?.contains("layout-handle"))
          .forEach((handle) => handle.remove());
        return;
      }
      if (["A", "BUTTON", "DETAILS"].includes(item.tagName)) return;
      let handle = [...item.children].find((child) => child.classList?.contains("layout-handle"));
      if (!handle) {
        handle = element("div", "layout-handle");
        const label = element("span", "", "Drag to rearrange");
        const actions = element("span", "layout-handle-actions");
        if (config.sizable) {
          const widthLabel = element("label", "layout-width-control", "Width");
          const widthSelect = element("select", "layout-width-select");
          const defaultOption = element("option", "", "Project default");
          defaultOption.value = "default";
          widthSelect.append(defaultOption);
          Object.entries(LAYOUT_WIDTHS).forEach(([value, textLabel]) => {
            const option = element("option", "", textLabel);
            option.value = value;
            widthSelect.append(option);
          });
          widthSelect.addEventListener("change", (event) => {
            setLayoutItemWidth(item, config, event.currentTarget.value);
          });
          widthLabel.append(widthSelect);
          actions.append(widthLabel);
        }
        const destinations = compatibleLayoutZones(item);
        if (destinations.length > 1) {
          const containerLabel = element("label", "layout-container-control", "Container");
          const containerSelect = element("select", "layout-container-select");
          destinations.forEach((destination) => {
            const option = element("option", "", destination.label);
            option.value = destination.key;
            containerSelect.append(option);
          });
          containerSelect.addEventListener("change", (event) => {
            moveLayoutItemToZone(item, event.currentTarget.value);
          });
          containerLabel.append(containerSelect);
          actions.append(containerLabel);
        }
        const previous = element("button", "", config.axis === "horizontal" ? "←" : "↑");
        const next = element("button", "", config.axis === "horizontal" ? "→" : "↓");
        previous.type = next.type = "button";
        previous.addEventListener("click", () => moveLayoutItem(item, -1));
        next.addEventListener("click", () => moveLayoutItem(item, 1));
        actions.append(previous, next);
        handle.append(label, actions);
        item.prepend(handle);
      }
      const buttons = handle.querySelectorAll("button");
      const itemLabel = item.getAttribute("aria-label")
        || item.querySelector("h2, h3, h4, strong, .action-item-title")?.textContent
        || item.dataset.layoutId
        || "item";
      buttons[0].setAttribute("aria-label", `Move ${itemLabel.trim()} ${config.axis === "horizontal" ? "left" : "up"}`);
      buttons[1].setAttribute("aria-label", `Move ${itemLabel.trim()} ${config.axis === "horizontal" ? "right" : "down"}`);
      buttons[0].disabled = index === 0;
      buttons[1].disabled = index === items.length - 1;
      const widthSelect = handle.querySelector(".layout-width-select");
      if (widthSelect) {
        const sizes = readLayoutPreferences()[layoutSizeKey(config)];
        widthSelect.value = sizes?.[item.dataset.layoutId] || "default";
        widthSelect.setAttribute("aria-label", `Width for ${itemLabel.trim()}`);
      }
      const containerSelect = handle.querySelector(".layout-container-select");
      if (containerSelect) {
        containerSelect.value = config.key;
        containerSelect.setAttribute("aria-label", `Container for ${itemLabel.trim()}`);
      }
    });
  }

  function applyLayoutZone(config) {
    const items = layoutItems(config);
    items.forEach((item, index) => { item.dataset.layoutId = layoutIdentity(item, index); });
    const preferences = readLayoutPreferences();
    const order = preferences[config.key];
    if (Array.isArray(order)) {
      const byLayoutId = new Map(items.map((item) => [item.dataset.layoutId, item]));
      order.forEach((id) => {
        const item = byLayoutId.get(id);
        if (item) config.container.append(item);
      });
      items.filter((item) => !order.includes(item.dataset.layoutId)).forEach((item) => config.container.append(item));
    }
    const sizes = preferences[layoutSizeKey(config)];
    const hasSizes = config.sizable
      && sizes
      && typeof sizes === "object"
      && Object.keys(sizes).length > 0;
    config.container.classList.toggle("layout-size-zone", Boolean(hasSizes));
    layoutItems(config).forEach((item) => {
      if (hasSizes) {
        item.dataset.layoutWidth = sizes[item.dataset.layoutId]
          || layoutItemDefaultWidth(item, config);
      } else {
        delete item.dataset.layoutWidth;
      }
    });
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
    announce(`${item.querySelector("h2, h3, h4, strong")?.textContent || "Item"} moved ${delta < 0 ? "earlier" : "later"}.`);
  }

  function registerLayoutZone(
    container,
    key,
    selector = ":scope > *",
    axis = "vertical",
    sizable = false,
    defaultWidth = "full",
    options = {}
  ) {
    if (!container) return;
    const config = {
      container,
      key,
      selector,
      axis,
      sizable,
      defaultWidth,
      label: options.label || key,
      acceptedTransferGroups: new Set(options.accepts || [])
    };
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

  function applySavedLayoutPlacements() {
    const preferences = readLayoutPreferences();
    const placements = preferences[LAYOUT_PLACEMENTS_KEY];
    if (!placements || typeof placements !== "object") return;
    document.querySelectorAll("[data-layout-transfer-group][data-layout-id]").forEach((item) => {
      const currentConfig = layoutConfigForItem(item);
      if (currentConfig && !item.dataset.layoutOriginZone) {
        item.dataset.layoutOriginZone = currentConfig.key;
      }
      const targetConfig = layoutZones.get(placements[item.dataset.layoutId]);
      if (!targetConfig
        || !targetConfig.acceptedTransferGroups.has(item.dataset.layoutTransferGroup)
        || targetConfig.container === item.parentElement) return;
      targetConfig.container.append(item);
    });
  }

  function refreshLayoutZones() {
    layoutZones.forEach((config) => {
      layoutItems(config).forEach((item) => {
        if (item.dataset.layoutTransferGroup && !item.dataset.layoutOriginZone) {
          item.dataset.layoutOriginZone = config.key;
        }
      });
    });
    applySavedLayoutPlacements();
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
    if (active === "overview") delete preferences[LAYOUT_PLACEMENTS_KEY];
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

  function movePanelContents(sourceId, destinationId, stacked = false) {
    const source = byId(sourceId);
    const destination = byId(destinationId);
    if (!source || !destination) return;
    source.hidden = false;
    source.removeAttribute("role");
    source.removeAttribute("aria-labelledby");
    if (stacked) source.classList.add("planning-stacked-section");
    destination.append(...source.children);
  }

  function prepareConsolidatedNavigation() {
    movePanelContents("candidate-panel-formal", "planning-panel-candidates");
    movePanelContents("candidate-panel-preliminary", "planning-panel-preliminary");
    ["catalog", "pending", "watchers"].forEach((name) => {
      const source = byId(`source-panel-${name}`);
      if (!source) return;
      source.hidden = false;
      source.removeAttribute("role");
      source.removeAttribute("aria-labelledby");
      source.classList.add("planning-stacked-section");
      byId("planning-panel-sources").append(...source.children);
    });
    ["assignments", "analysis", "builder"].forEach((name) => {
      const source = byId(`publication-panel-${name}`);
      if (!source) return;
      source.hidden = false;
      source.removeAttribute("role");
      source.removeAttribute("aria-labelledby");
      source.classList.add("planning-stacked-section");
      byId("planning-panel-publication").append(...source.children);
    });

    const watcherTabs = document.querySelector(".watcher-tabs");
    if (watcherTabs) watcherTabs.hidden = true;
    const watcherHeading = byId("watchers-heading")?.closest(".queue-view-header");
    if (watcherHeading && !byId("source-workspace-selector")) {
      const selector = element("label", "compact-view-selector", "Source workspace");
      const select = element("select", "");
      select.id = "source-workspace-selector";
      [
        ["courts", "Court cases"],
        ["directives", "Presidential directives"],
        ["source-checker", "Source Checker Bot"]
      ].forEach(([value, label]) => {
        const option = element("option", "", label);
        option.value = value;
        select.append(option);
      });
      selector.append(select);
      watcherHeading.after(selector);
    }

    const legacyLogs = byId("panel-logs");
    const operationsLogs = byId("automation-panel-logs");
    if (legacyLogs && operationsLogs) {
      const logTabs = legacyLogs.querySelector(".section-tabs");
      if (logTabs) logTabs.hidden = true;
      const menu = element("nav", "compact-specialist-menu operations-log-menu");
      menu.id = "operations-log-menu";
      menu.setAttribute("aria-label", "Project logs");
      const menuList = element("div", "compact-specialist-menu-list operations-log-menu-list");
      [
        ["incidents", "Incidents"],
        ["horizon", "Horizon"],
        ["elim", "Elim"],
        ["agents", "Bots"],
        ["source-monitor", "Sources"],
        ["integrity", "Integrity"],
        ["changes", "Change audits"],
        ["console-development", "Console development"]
      ].forEach(([value, label]) => {
        const button = element("a", "compact-specialist-menu-item operations-log-menu-button", label);
        button.href = `#automation:logs:${value}`;
        button.dataset.logView = value;
        button.setAttribute("aria-current", "false");
        if (value === "incidents") {
          const count = element("span", "tab-count", "—");
          count.id = "operations-log-menu-incident-count";
          button.append(count);
        }
        menuList.append(button);
      });
      menu.append(menuList);
      const logPanels = [...legacyLogs.children].filter((child) => child !== logTabs);
      operationsLogs.append(menu, ...logPanels);
      if (logTabs) operationsLogs.append(logTabs);
    }

    [
      ["panel-candidates", ".section-tabs"],
      ["panel-sources", ".section-tabs"],
      ["panel-publication", ".section-tabs"]
    ].forEach(([panelId, selector]) => {
      const navigation = byId(panelId)?.querySelector(selector);
      if (navigation) navigation.hidden = true;
    });
  }

  function initializePersonalLayout() {
    registerLayoutZone(document.querySelector(".tab-list"), "main-tabs", ":scope > button", "horizontal");
    ["planning", "automation"].forEach((group) => {
      registerLayoutZone(document.querySelector(`[data-subtab-group="${group}"]`)?.parentElement, `subtabs-${group}`, ":scope > button", "horizontal");
    });
    registerLayoutZone(
      document.querySelector(".overview-view"),
      "sections-overview",
      ":scope > .overview-section",
      "vertical",
      true,
      "full",
      { label: "Overview main flow", accepts: ["overview-portlet"] }
    );
    registerLayoutZone(
      document.querySelector(".overview-lower-grid"),
      "sections-overview-lower",
      ":scope > .overview-section",
      "horizontal",
      true,
      "half",
      { label: "Overview lower row", accepts: ["overview-portlet"] }
    );
    registerLayoutZone(byId("overview-queue-directory"), "cards-overview-queues", ":scope > article", "horizontal", true, "quarter");
    registerLayoutZone(byId("overview-automation-activity-grid"), "cards-overview-overnight", ":scope > a", "horizontal", true, "compact");
    registerLayoutZone(
      byId("overview-portals"),
      "cards-overview-portals",
      ":scope > article",
      "horizontal",
      true,
      "quarter",
      { label: "Operational indicators", accepts: ["overview-portlet"] }
    );
    registerLayoutZone(byId("overview-system-grid"), "cards-overview-system", ":scope > article", "horizontal", true, "third");
    registerLayoutZone(byId("overview-freshness"), "cards-overview-freshness", ":scope > a", "horizontal", true, "third");
    registerLayoutZone(byId("progress-sections"), "sections-progress-v3", ":scope > section, :scope > details", "vertical", true, "full");
    registerLayoutZone(byId("progress-summary-grid"), "cards-progress-summary", ":scope > article", "horizontal", true, "quarter");
    registerLayoutZone(document.querySelector(".integrity-view"), "sections-integrity", ":scope > .integrity-layout", "vertical", true, "full");
    registerLayoutZone(byId("integrity-metrics"), "cards-integrity-metrics", ":scope > article", "horizontal", true, "quarter");
    registerLayoutZone(byId("integrity-components"), "cards-integrity-components", ":scope > article", "horizontal", true, "quarter");
    registerLayoutZone(byId("source-checker-summary"), "cards-sources-source-checker", ":scope > article", "horizontal", true, "quarter");
    registerLayoutZone(byId("automation-overview-grid"), "cards-automation-overview", ":scope > a", "horizontal");
    registerLayoutZone(byId("automation-incidents"), "cards-automation-incidents", ":scope > article", "vertical", true, "full");
    registerLayoutZone(byId("print-level-summary"), "cards-publication-assignments", ":scope > button", "horizontal");
    registerLayoutZone(byId("publication-metrics"), "cards-publication-metrics", ":scope > article", "horizontal", true, "quarter");
    registerLayoutZone(byId("publication-delivery-list"), "cards-publication-delivery", ":scope > article", "horizontal", true, "third");
    registerLayoutZone(byId("publication-release-blockers-list"), "cards-publication-release-blockers", ":scope > article", "vertical", true, "full");
    registerLayoutZone(byId("topic-products-list"), "cards-publication-topics", ":scope > article", "horizontal", true, "third");
    registerLayoutZone(byId("release-readiness-grid"), "cards-publication-release", ":scope > article", "horizontal", true, "quarter");
    registerLayoutZone(document.querySelector(".publication-analysis-view"), "sections-publication", ":scope > .publication-analysis-grid, :scope > section", "vertical", true, "full");
    registerLayoutZone(document.querySelector(".publication-analysis-grid"), "cards-publication-analysis", ":scope > section", "horizontal", true, "half");
    registerLayoutZone(document.querySelector(".publication-builder-grid"), "cards-publication-builder", ":scope > section, :scope > aside", "horizontal", true, "half");

    const toggle = byId("layout-edit-toggle");
    toggle.addEventListener("click", () => {
      layoutEditing = !layoutEditing;
      document.body.classList.toggle("layout-editing", layoutEditing);
      toggle.setAttribute("aria-pressed", String(layoutEditing));
      toggle.textContent = layoutEditing ? "Done designing" : "Design layout";
      byId("layout-status").classList.toggle("is-editing", layoutEditing);
      byId("layout-status").textContent = layoutEditing
        ? "Drag highlighted items, use the arrow controls, or choose a safe grid width. Changes save automatically in this browser."
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
    const selectedSubtab = document.querySelector(
      `[data-subtab-group="${selected.dataset.tab}"][aria-selected="true"]`
    )?.dataset.subtab || "";
    void activateDomainForTab(selected.dataset.tab, selectedSubtab);
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
    const rawTarget = window.location.hash.replace(/^#/, "");
    const normalizedTarget = normalizeConsoleTarget(rawTarget);
    if (rawTarget && normalizedTarget !== rawTarget) {
      window.history.replaceState(null, "", `#${normalizedTarget}`);
    }
    const requested = normalizedTarget.split(":", 1)[0];
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
    if (activeTopLevel === group) void activateDomainForTab(group, selected.dataset.subtab);
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
    const selector = byId("source-workspace-selector");
    if (selector) {
      selector.value = selected.dataset.watcherTab;
      if (focus) selector.focus();
    }
    if (window.location.hash.startsWith("#planning:sources")
      || window.location.hash.startsWith("#sources:watchers")) {
      window.history.replaceState(null, "", `#planning:sources:watchers:${selected.dataset.watcherTab}`);
    }
    if (name === "source-checker") {
      void Promise.all([
        ensureDomain("source-checker"),
        ensureDomain("automation")
      ]).then((loaded) => {
        if (loaded.every(Boolean)) {
          populateSourceCheckerFilters();
          renderSourceChecker();
          refreshLiveSourceChecker();
        }
      });
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
    const requested = parts[0] === "planning" && parts[1] === "sources" && parts[2] === "watchers"
      ? parts[3]
      : parts[0] === "sources" && parts[1] === "watchers"
        ? parts[2]
        : "courts";
    activateWatcherTab(tabs.some((tab) => tab.dataset.watcherTab === requested) ? requested : "courts");
    byId("source-workspace-selector")?.addEventListener("change", (event) => {
      activateWatcherTab(event.currentTarget.value);
    });
  }

  function activateLogView(name, focus = false) {
    const panels = [...document.querySelectorAll('[id^="log-panel-"]')];
    const selected = panels.find((panel) => panel.id === `log-panel-${name}`)
      || byId("log-panel-incidents");
    panels.forEach((panel) => { panel.hidden = panel !== selected; });
    const selectedName = selected.id.replace(/^log-panel-/, "");
    const buttons = [...document.querySelectorAll("[data-log-view]")];
    const selectedButton = buttons.find((button) => button.dataset.logView === selectedName);
    buttons.forEach((button) => {
      const active = button === selectedButton;
      button.setAttribute("aria-current", active ? "page" : "false");
      button.tabIndex = active ? 0 : -1;
    });
    if (focus) selectedButton?.focus();
    const activeTopLevel = document.querySelector('[role="tab"][data-tab][aria-selected="true"]')?.dataset.tab;
    const activeOperation = document.querySelector('[data-subtab-group="automation"][aria-selected="true"]')?.dataset.subtab;
    if (activeTopLevel === "automation" && activeOperation === "logs") {
      if (!window.location.hash.startsWith(`#automation:logs:${selectedName}`)) {
        window.history.replaceState(null, "", `#automation:logs:${selectedName}`);
      }
      void activateDomainForTab("automation", "logs");
    }
    if (selectedName === "incidents") renderIncidentLog();
  }

  function initializeLogMenu() {
    const buttons = [...document.querySelectorAll("[data-log-view]")];
    if (!buttons.length) return;
    buttons.forEach((button) => {
      button.addEventListener("click", () => activateLogView(button.dataset.logView));
      button.addEventListener("keydown", (event) => {
        const index = buttons.indexOf(button);
        let target = null;
        if (event.key === "ArrowRight") target = buttons[(index + 1) % buttons.length];
        if (event.key === "ArrowLeft") target = buttons[(index - 1 + buttons.length) % buttons.length];
        if (event.key === "Home") target = buttons[0];
        if (event.key === "End") target = buttons[buttons.length - 1];
        if (!target) return;
        event.preventDefault();
        activateLogView(target.dataset.logView, true);
      });
    });
    const parts = window.location.hash.replace(/^#/, "").split(":");
    const requested = parts[0] === "automation" && parts[1] === "logs"
      ? parts[2]
      : parts[0] === "logs"
        ? parts[1]
      : "incidents";
    activateLogView(requested || "incidents");
  }

  function operationalIncidentProjection() {
    const projection = data.operational_incidents || {};
    const complete = projection.availability === "current"
      && projection.complete === true
      && Number.isInteger(projection.unresolved_count)
      && Array.isArray(projection.items)
      && projection.active_links
      && typeof projection.active_links === "object";
    return {
      ...projection,
      complete,
      unresolvedCount: complete ? projection.unresolved_count : null,
      items: Array.isArray(projection.items) ? projection.items : [],
      impactState: complete ? projection.impact_state : "gray"
    };
  }

  function unresolvedOperationalIncidents() {
    const projection = operationalIncidentProjection();
    if (!projection.complete) return [];
    return projection.items.filter((incident) =>
      ["open", "investigating", "mitigated", "monitoring"].includes(incident.status));
  }

  function operationalIncidentsById(ids = []) {
    const wanted = new Set(ids);
    return operationalIncidentProjection().items.filter((incident) =>
      wanted.has(incident.incident_id));
  }

  function activeIncidentIdsForTypedLink(reference) {
    const projection = operationalIncidentProjection();
    return projection.complete && Array.isArray(projection.active_links?.[reference])
      ? projection.active_links[reference]
      : [];
  }

  function incidentIdsIncludeBlocker(ids = []) {
    return operationalIncidentsById(ids).some((incident) =>
      ["blocking", "disrupted"].includes(incident.impact)
      && ["open", "investigating"].includes(incident.status));
  }

  function humanOwnsIncident(incident) {
    return ["human", "benjamin", "benjamin smith", "you"].includes(
      String(incident?.owner || "").trim().toLowerCase()
    );
  }

  function incidentStatusPresentation(incident) {
    const status = String(incident?.status || "unavailable");
    if (status === "resolved") return { tone: "success", label: "Resolved" };
    if (["mitigated", "monitoring"].includes(status)) {
      return { tone: "warning", label: humanizeKey(status) };
    }
    if (["blocking", "disrupted"].includes(incident?.impact)) {
      return { tone: "error", label: humanizeKey(status) };
    }
    return { tone: "warning", label: humanizeKey(status) };
  }

  function incidentTypedLink(reference) {
    const [kind, ...rest] = String(reference || "").split(":");
    const identifier = rest.join(":");
    if (!identifier) return null;
    const routes = {
      "automation-role": `automation:agents:${encodeURIComponent(identifier)}`,
      "repository-gate": "automation:gates",
      security: "automation:security",
      platform: "automation:platform",
      data: "automation:data",
      log: `automation:logs:${encodeURIComponent(identifier)}`
    };
    if (routes[kind]) {
      return {
        label: kind === "automation-role"
          ? "Open affected role"
          : `Open ${kind.replaceAll("-", " ")} detail`,
        route: routes[kind],
        external: false
      };
    }
    if (kind === "github" && /^https?:\/\//.test(identifier)) {
      return { label: "Open GitHub record ↗", route: identifier, external: true };
    }
    return null;
  }

  function renderIncidentPreview(incident, preview) {
    if (!incident) {
      preview.replaceChildren(element("p", "empty-state", "No incident is selected."));
      return;
    }
    const presentation = incidentStatusPresentation(incident);
    const header = element("div", "email-preview-heading");
    const title = element("div");
    title.append(
      element("span", "eyebrow", incident.incident_id),
      element("h3", "", incident.summary || "Operational incident")
    );
    header.append(
      title,
      element("span", `status-badge ${presentation.tone}`, presentation.label)
    );
    const fields = element("dl", "email-preview-fields incident-preview-fields");
    [
      ["Component", incident.component],
      ["Prerequisite", incident.prerequisite],
      ["Failure class", incident.failure_class],
      ["Impact", humanizeKey(incident.impact)],
      ["Owner", incident.owner || "Unassigned"],
      ["Recommended owner", incident.recommended_owner],
      ["Reported by", incident.reported_by],
      ["First observed", formatOperationalDate(incident.first_observed)],
      ["Last observed", formatOperationalDate(incident.last_observed)],
      ["Next action", incident.next_action]
    ].forEach(([label, value]) => {
      const field = element("div", "email-preview-field");
      field.append(element("dt", "", label), element("dd", "", value || "Unavailable"));
      fields.append(field);
    });
    const timeline = element("section", "incident-occurrence-timeline");
    timeline.append(
      element("h4", "", "Occurrence timeline"),
      element(
        "p",
        "micro-note",
        `${pluralizeWord((incident.occurrences || []).length, "exact occurrence")} retained`
      )
    );
    const occurrenceList = element("ol", "incident-occurrence-list");
    [...(incident.occurrences || [])]
      .sort((left, right) => String(right.observed_at || "").localeCompare(String(left.observed_at || "")))
      .forEach((occurrence) => {
        const row = element("li", "");
        row.append(
          element("strong", "", formatOperationalDate(occurrence.observed_at)),
          element("span", "", occurrence.diagnostic || "No diagnostic recorded."),
          element("span", "micro-note", [
            occurrence.run_id ? `Run ${occurrence.run_id}` : "",
            occurrence.source_ref || ""
          ].filter(Boolean).join(" · "))
        );
        occurrenceList.append(row);
      });
    timeline.append(occurrenceList);
    const recovery = element("section", "incident-recovery-evidence");
    recovery.append(element("h4", "", "Recovery and closure evidence"));
    if ((incident.recovery_evidence || []).length) {
      const list = element("ul", "");
      incident.recovery_evidence.forEach((item) => {
        list.append(element(
          "li",
          "",
          `${item.result} · ${item.closure_test} · verified ${formatOperationalDate(item.verified_at)}`
        ));
      });
      recovery.append(list);
    } else {
      recovery.append(element("p", "micro-note", "No exact recovery evidence has been recorded."));
    }
    const links = element("div", "source-list dossier-actions");
    (incident.active_links || []).map(incidentTypedLink).filter(Boolean).forEach((link) => {
      links.append(actionInboxLink(link.label, link.route, link.external));
    });
    preview.replaceChildren(header, fields, timeline, recovery, links);
  }

  function updateIncidentNavigationCounts() {
    const projection = operationalIncidentProjection();
    const display = projection.complete ? String(projection.unresolvedCount) : "—";
    [
      "tab-automation-count",
      "automation-logs-incident-count",
      "log-incidents-count",
      "operations-log-menu-incident-count"
    ].forEach((id) => {
      if (byId(id)) byId(id).textContent = display;
    });
  }

  function renderIncidentLog() {
    const projection = operationalIncidentProjection();
    const status = byId("incident-log-status");
    const host = byId("incident-log-workspace");
    if (!status || !host) return;
    updateIncidentNavigationCounts();
    if (!projection.complete) {
      status.textContent = `${projection.reason || "Operational incident feed is unavailable."} Unresolved count is not inferred.`;
      byId("incident-log-visible").textContent = "—";
      host.replaceChildren(element("p", "empty-state", "Incident history is unavailable; zero incidents cannot be established."));
      return;
    }
    const query = incidentLogState.search.trim().toLowerCase();
    const items = projection.items
      .filter((incident) => incidentLogState.scope === "all"
        || ["open", "investigating", "mitigated", "monitoring"].includes(incident.status))
      .filter((incident) => !query || [
        incident.incident_id,
        incident.summary,
        incident.component,
        incident.prerequisite,
        incident.failure_class,
        incident.owner,
        incident.recommended_owner,
        incident.next_action,
        ...(incident.occurrences || []).map((row) => row.diagnostic)
      ].filter(Boolean).join(" ").toLowerCase().includes(query))
      .sort((left, right) =>
        String(right.last_observed || "").localeCompare(String(left.last_observed || ""))
        || String(right.incident_id || "").localeCompare(String(left.incident_id || "")));
    const selectedFromRoute = decodeURIComponent(
      window.location.hash.split(":").find((part) => part.startsWith("selected="))?.slice(9) || ""
    );
    if (selectedFromRoute && items.some((item) => item.incident_id === selectedFromRoute)) {
      incidentLogState.selectedId = selectedFromRoute;
    }
    if (!items.some((item) => item.incident_id === incidentLogState.selectedId)) {
      incidentLogState.selectedId = items[0]?.incident_id || "";
    }
    byId("incident-log-visible").textContent = items.length;
    status.textContent = `${pluralizeWord(projection.unresolvedCount, "unresolved incident")} · checked ${formatOperationalDate(projection.checked_at)} · ${projection.impactState} impact posture`;
    if (!items.length) {
      host.replaceChildren(element(
        "p",
        "empty-state",
        incidentLogState.scope === "unresolved"
          ? "No unresolved operational incidents are recorded."
          : "No incidents match the current search."
      ));
      return;
    }
    const workspace = element("div", "email-workspace log-email-workspace incident-email-workspace");
    const list = element("div", "email-list log-email-list incident-email-list");
    list.setAttribute("role", "listbox");
    list.setAttribute("aria-label", "Operational incidents, newest occurrence first");
    const preview = element("article", "email-preview log-email-preview incident-email-preview");
    const select = (incident, focus = false) => {
      incidentLogState.selectedId = incident.incident_id;
      list.querySelectorAll(".email-list-row").forEach((row) => {
        const selected = row.dataset.entryId === incident.incident_id;
        row.classList.toggle("selected", selected);
        row.setAttribute("aria-selected", String(selected));
      });
      renderIncidentPreview(incident, preview);
      window.history.replaceState(
        null,
        "",
        `#automation:logs:incidents:selected=${encodeURIComponent(incident.incident_id)}`
      );
      if (focus) list.querySelector(`[data-entry-id="${incident.incident_id}"]`)?.focus();
    };
    items.forEach((incident) => {
      const presentation = incidentStatusPresentation(incident);
      const row = element("button", "email-list-row log-email-row");
      row.type = "button";
      row.dataset.entryId = incident.incident_id;
      row.setAttribute("role", "option");
      row.setAttribute("aria-selected", String(incident.incident_id === incidentLogState.selectedId));
      if (incident.incident_id === incidentLogState.selectedId) row.classList.add("selected");
      const copy = element("span", "email-list-copy");
      copy.append(
        element("strong", "", `${incident.incident_id} · ${incident.summary}`),
        element("span", "", `${incident.component} · ${incident.owner || "Unassigned owner"}`)
      );
      row.append(
        element("span", `status-dot ${presentation.tone}`, ""),
        copy,
        element("span", "email-list-meta", `${pluralizeWord((incident.occurrences || []).length, "occurrence")} · ${formatOperationalDate(incident.last_observed)}`)
      );
      row.addEventListener("click", () => select(incident));
      list.append(row);
    });
    list.addEventListener("keydown", (event) => {
      if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
      const currentIndex = Math.max(
        0,
        items.findIndex((item) => item.incident_id === incidentLogState.selectedId)
      );
      const nextIndex = event.key === "Home"
        ? 0
        : event.key === "End"
          ? items.length - 1
          : event.key === "ArrowDown"
            ? Math.min(items.length - 1, currentIndex + 1)
            : Math.max(0, currentIndex - 1);
      event.preventDefault();
      select(items[nextIndex], true);
    });
    workspace.append(list, preview);
    host.replaceChildren(workspace);
    renderIncidentPreview(
      items.find((item) => item.incident_id === incidentLogState.selectedId),
      preview
    );
  }

  function initializeIncidentLog() {
    const search = byId("incident-log-search");
    const scope = byId("incident-log-scope");
    if (!search || !scope || search.dataset.bound) return;
    search.dataset.bound = "true";
    search.addEventListener("input", (event) => {
      incidentLogState.search = event.target.value;
      renderIncidentLog();
    });
    scope.addEventListener("change", (event) => {
      incidentLogState.scope = event.target.value;
      renderIncidentLog();
    });
    renderIncidentLog();
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
      ["Assurance", "assurance"],
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
      const assuranceCell = element("td");
      const health = sourceCheckerRecords().find((result) => result.source_id === record.id);
      assuranceCell.append(
        element("span", "source-assurance-value", text(record.reviewed, "Review not recorded")),
        element("small", "", text(record.reliability, "Reliability not recorded")),
        element("small", "", health ? text(health.classification) : "URL health unavailable")
      );
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
      row.append(sourceCell, publisherCell, detailsCell, assuranceCell, ownerCell, monitoringCell, linkCell);
      body.append(row);
    });
    table.append(head, body);
    wrapper.append(table);
    return wrapper;
  }

  function paginationControls(name, total, state, render, pageSize = PAGE_SIZE) {
    const nav = element("nav", "pagination");
    nav.setAttribute("aria-label", `${name.replaceAll("-", " ")} pages`);
    nav.replaceChildren();
    const pages = Math.max(1, Math.ceil(total / pageSize));
    state.page = Math.min(state.page, pages);
    const previous = element("button", "page-button", "← Previous");
    previous.type = "button";
    previous.dataset.focusKey = `${name}:pagination:previous`;
    previous.disabled = state.page === 1;
    previous.addEventListener("click", () => {
      state.page -= 1;
      rerenderPreservingFocus(render, `${name} results, page ${state.page} of ${pages}.`);
    });
    const status = element("span", "page-status", `Page ${state.page} of ${pages}`);
    const next = element("button", "page-button", "Next →");
    next.type = "button";
    next.dataset.focusKey = `${name}:pagination:next`;
    next.disabled = state.page === pages;
    next.addEventListener("click", () => {
      state.page += 1;
      rerenderPreservingFocus(render, `${name} results, page ${state.page} of ${pages}.`);
    });
    nav.append(previous, status, next);
    return nav;
  }

  function pagination(name, total, state, render, pageSize = PAGE_SIZE) {
    const nav = byId(`${name}-pagination`);
    if (!nav) return;
    nav.replaceChildren(...paginationControls(name, total, state, render, pageSize).childNodes);
  }

  function renderSourceView(name, records, filterField) {
    const state = sourceStates[name];
    const query = state.search.toLowerCase();
    const healthIndex = new Map(sourceCheckerRecords().map((record) => [record.source_id, record.classification]));
    const filtered = records.filter((record) => {
      if (state.filter !== "all" && sourceTypeFamily(record[filterField]) !== state.filter) return false;
      if (state.exactType !== "all" && record[filterField] !== state.exactType) return false;
      if (state.reviewed !== "all" && text(record.reviewed, "Not recorded") !== state.reviewed) return false;
      if (state.reliability !== "all" && text(record.reliability, "Not recorded") !== state.reliability) return false;
      const monitoring = record.monitoring === "Yes" ? "Monitored" : "Not monitored";
      if (state.monitoring !== "all" && monitoring !== state.monitoring) return false;
      const health = healthIndex.get(record.id) || "Unavailable";
      if (state.health !== "all" && health !== state.health) return false;
      return !query || sourceSearchText(record).includes(query);
    });
    const ordered = state.sortKey
      ? sortedRecords(filtered, state, (record, key) => ({
          source: `${record.id} ${record.title}`,
          publisher: record.publisher,
          date: Number.isNaN(Date.parse(record.date)) ? record.date : Date.parse(record.date),
          assurance: `${record.reviewed || ""} ${record.reliability || ""}`,
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
    const visible = ordered.slice(start, start + PAGE_SIZE);
    const host = byId(`${name}-table`);
    if (!visible.length) {
      host.replaceChildren(element("p", "empty-state", "No sources match the current filters."));
    } else {
      if (!visible.some((record) => record.id === state.selectedId)) state.selectedId = visible[0].id;
      const workspace = element("div", "email-workspace source-email-workspace");
      const list = element("div", "email-list source-email-list");
      list.setAttribute("role", "listbox");
      list.setAttribute("aria-label", `${name} sources`);
      const preview = element("article", "email-preview source-email-preview");
      const showSource = (record) => {
        state.selectedId = record.id;
        list.querySelectorAll(".email-list-row").forEach((row) => {
          const selected = row.dataset.entryId === record.id;
          row.classList.toggle("selected", selected);
          row.setAttribute("aria-selected", String(selected));
        });
        const heading = element("div", "email-preview-heading");
        const title = element("div");
        title.append(element("span", "record-id", record.id), element("h3", "", text(record.title, "Untitled source")));
        heading.append(title, record.url ? inlineLink("Open source ↗", record.url) : element("span", "muted", "No source link"));
        const fields = element("dl", "email-preview-fields");
        [
          ["Publisher", text(record.publisher)],
          ["Date", text(record.date)],
          ["Type", text(record[filterField])],
          ["Reviewed", text(record.reviewed, "Not recorded")],
          ["Reliability", text(record.reliability, "Not recorded")],
          ["URL health", text(healthIndex.get(record.id), "Unavailable")],
          ["Associated records", (record.record_ids || []).join(" · ") || "None recorded"],
          ["Monitoring", record.monitoring === "Yes" ? text(record.monitoring_rationale, "Enabled") : "No"]
        ].forEach(([label, value]) => {
          const field = element("div", "email-preview-field");
          field.append(element("dt", "", label), element("dd", "", value));
          fields.append(field);
        });
        const links = element("div", "source-list dossier-actions");
        (record.record_ids || []).forEach((identifier) => {
          const target = workbenchTargetForArtifact(identifier, {
            source: "Sources",
            reference: record.id,
            returnTarget: `planning:sources:${name}`
          });
          if (target) links.append(internalInlineLink(`Open ${identifier} in Workbench`, target));
        });
        preview.replaceChildren(heading, fields, links);
      };
      visible.forEach((record) => {
        const row = element("button", "email-list-row");
        row.type = "button";
        row.dataset.entryId = record.id;
        row.setAttribute("role", "option");
        row.append(
          element("strong", "email-row-title", `${record.id} · ${text(record.title, "Untitled source")}`),
          element("span", "email-row-time", text(record.date, "Date unavailable")),
          element("span", "email-row-summary", `${text(record.publisher, "Publisher unavailable")} · ${text(record[filterField], "Type unavailable")}`)
        );
        row.addEventListener("click", () => showSource(record));
        list.append(row);
      });
      workspace.append(list, preview);
      host.replaceChildren(workspace);
      showSource(visible.find((record) => record.id === state.selectedId) || visible[0]);
    }
    pagination(name, ordered.length, state, rerender);
    updateDenseDisclosureSummary(`${name}-results-summary`, ordered.length, "source", `page ${state.page} of ${pages}`);
    const monitored = records.filter((record) => record.monitoring === "Yes").length;
    const unreviewed = records.filter((record) => !record.reviewed || /no|not|pending/i.test(record.reviewed)).length;
    const unhealthy = [...healthIndex.values()].filter((classification) =>
      !["verified", "identity-preserving redirect"].includes(classification)).length;
    byId("source-assurance-summary")?.replaceChildren(
      watcherSummaryCard("Cataloged", records.length, "source records in the loaded projection"),
      watcherSummaryCard("Reviewed gaps", unreviewed, "records without a positive recorded review state"),
      watcherSummaryCard("Monitored", monitored, "source records with monitoring enabled"),
      watcherSummaryCard("URL exceptions", unhealthy, "loaded Source Checker results outside verified classes")
    );
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
      dossierSection("Why this issue is monitored", record.monitoring_rationale || "The owning issue has not yet recorded a structured monitoring rationale.", "wide"),
      dossierSection("Trigger", record.monitoring_trigger || record.trigger || "Trigger unavailable"),
      dossierSection("Method", record.monitoring_method || record.method || "Method unavailable"),
      dossierSection("Cadence", record.monitoring_cadence || record.cadence || "Cadence unavailable"),
      dossierSection("Last checked", record.last_checked ? formatDate(record.last_checked) : "Last checked unavailable"),
      dossierSection("Next due", record.next_due ? formatDate(record.next_due) : "Next due unavailable"),
      dossierSection("Change since last pass", record.change_since_last_pass || record.latest_change || "Change unavailable"),
      dossierSection("Material relevance", record.material_relevance || record.relevance || "Material relevance unavailable"),
      dossierSection("Coverage sources", record.coverage || record.coverage_sources || "Coverage statement unavailable"),
      dossierSection("Coverage gaps", record.coverage_gap || record.coverage_gaps || "Coverage gap unavailable"),
      dossierSection("Latest posture", record.latest_posture || record.posture || "Latest posture unavailable"),
      dossierSection("Owner", record.owner || record.monitoring_owner || "Owner unavailable"),
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
    if (byId("pending-controls")) byId("pending-controls").hidden = data.pending_sources.length === 0;
  }

  function courtWatchCard(label, records) {
    const hasUpdate = records.some((record) => reviewSignals.courts.ids.has(record.id));
    const details = element("details", hasUpdate ? "monitoring-issue has-update" : "monitoring-issue");
    details.dataset.disclosureId = `sources-court-${records[0].owner_id}-${layoutSlug(records[0].monitoring_group || label)}`;
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
    const pages = Math.max(1, Math.ceil(orderedGroups.length / PAGE_SIZE));
    courtWatchState.page = Math.min(courtWatchState.page, pages);
    const start = (courtWatchState.page - 1) * PAGE_SIZE;
    const visibleGroups = orderedGroups.slice(start, start + PAGE_SIZE);
    const host = byId("court-watch-list");
    host.replaceChildren(...(visibleGroups.length
      ? visibleGroups.map(([, records]) => courtWatchCard(records[0].monitoring_group || records[0].owner_title, records))
      : [element("p", "empty-state compact-empty", "No court sources match the current filters.")]));
    pagination("court-watch", orderedGroups.length, courtWatchState, renderCourtWatch);
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

  function sourceCheckerDeltaPresentation(report = {}) {
    const deltas = report.deltas;
    if (!deltas || typeof deltas !== "object" || deltas.available !== true) {
      return {
        available: false,
        reason: deltas?.reason || "No comparable prior per-source baseline is available.",
        baseline: deltas?.baseline_checked_at || null,
        counts: {},
        oldest: null
      };
    }
    const counts = deltas.counts && typeof deltas.counts === "object" ? deltas.counts : {};
    const aging = Array.isArray(deltas.aging_exceptions) ? deltas.aging_exceptions : [];
    const oldest = aging.reduce((current, record) =>
      Number(record?.age_days) > Number(current?.age_days ?? -1) ? record : current, null);
    return {
      available: true,
      reason: "",
      baseline: deltas.baseline_checked_at || null,
      counts: {
        newExceptions: counts.new_exceptions,
        regressedExceptions: counts.regressed_exceptions,
        resolvedExceptions: counts.resolved_exceptions,
        ongoingExceptions: counts.ongoing_exceptions,
        enteredScope: counts.entered_scope,
        leftScope: counts.left_scope
      },
      oldest
    };
  }

  function sourceCheckerDeltaCards(report = {}) {
    const delta = sourceCheckerDeltaPresentation(report);
    if (!delta.available) {
      return [
        watcherSummaryCard(
          "Assurance delta",
          "Unavailable",
          `${delta.reason}${delta.baseline ? ` · candidate baseline ${formatDate(delta.baseline)}` : ""}`
        )
      ];
    }
    const countCard = (label, value, detail) =>
      watcherSummaryCard(label, value ?? "Unavailable", detail);
    return [
      countCard("New exceptions", delta.counts.newExceptions, `since ${formatDate(delta.baseline)}`),
      countCard("Regressed", delta.counts.regressedExceptions, "previously non-exception sources now worse"),
      countCard("Resolved", delta.counts.resolvedExceptions, "prior exceptions no longer exceptional"),
      countCard("Ongoing", delta.counts.ongoingExceptions, "exceptions retained from the baseline"),
      countCard(
        "Oldest exception",
        delta.oldest ? `${text(delta.oldest.age_days, "Unavailable")}d` : delta.counts.ongoingExceptions === 0 ? "None" : "Unavailable",
        delta.oldest
          ? `${delta.oldest.source_id || "Source unavailable"} · ${delta.oldest.classification || "classification unavailable"}`
          : "No aging record is available"
      )
    ];
  }

  function sourceCheckerAssuranceDetails(report, contract, resultCount) {
    const details = element("details", "source-checker-assurance");
    const heading = element("summary", "", "Projection assurance details");
    const body = element("div", "source-checker-assurance-body");
    const currentCoverage = report.current_catalog_coverage || {};
    const missingIds = [
      ...(Array.isArray(report.missing_source_ids) ? report.missing_source_ids : []),
      ...(Array.isArray(report.completeness?.missing_ids) ? report.completeness.missing_ids : []),
      ...(Array.isArray(currentCoverage.missing_ids) ? currentCoverage.missing_ids : [])
    ];
    const fields = element("dl", "source-checker-assurance-fields");
    [
      ["Source revision", report.source_revision || report.revision || "Unavailable"],
      ["Generation", report.generation_id || "Unavailable"],
      ["Result records", resultCount],
      ["Expected / actual projection", contract.expected !== null ? `${contract.expected} / ${contract.actual ?? "Unavailable"}` : "Unavailable"],
      ["Missing Source IDs", missingIds.length ? [...new Set(missingIds)].join(", ") : contract.complete ? "Explicitly none" : "Unavailable"]
    ].forEach(([label, value]) => fields.append(element("dt", "", label), element("dd", "", String(value))));
    body.append(fields);
    const coverage = report.catalog_coverage || report.catalog_counts;
    const coverageRows = Array.isArray(coverage)
      ? coverage
      : coverage && typeof coverage === "object"
        ? Object.entries(coverage).map(([catalog, value]) => ({
            catalog,
            ...(value && typeof value === "object" ? value : { actual_count: value })
          }))
        : [];
    const coverageList = element("ul", "source-checker-catalog-coverage");
    if (coverageRows.length) {
      coverageRows.forEach((row) => {
        coverageList.append(element("li", "", `${row.catalog || row.path || "Catalog"}: ${text(row.actual_count ?? row.actual, "Unavailable")} actual / ${text(row.expected_count ?? row.expected, "Unavailable")} expected`));
      });
    } else {
      coverageList.append(element("li", "muted", "Per-catalog expected and actual counts are unavailable."));
    }
    body.append(element("h4", "", "Catalog coverage"), coverageList);
    const hashes = report.source_hashes || report.catalog_hashes || currentCoverage.source_hashes || {};
    const hashList = element("ul", "source-checker-hashes");
    if (hashes && typeof hashes === "object" && Object.keys(hashes).length) {
      Object.entries(hashes).forEach(([source, hash]) => {
        const value = hash && typeof hash === "object" ? hash.sha256 || hash.hash : hash;
        hashList.append(element("li", "", `${source}: ${text(value, "Unavailable")}`));
      });
    } else {
      hashList.append(element("li", "muted", "Source/catalog hashes are unavailable."));
    }
    body.append(element("h4", "", "Source hashes"), hashList);
    details.append(heading, body);
    return details;
  }

  function renderSourceChecker() {
    const report = data.source_checker || {};
    const records = sourceCheckerRecords();
    const validation = validateLivePayload("source-checker", report);
    const validProjection = validation.valid;
    const counts = report.counts || {};
    const exceptions = records.filter((record) => !["verified", "identity-preserving redirect"].includes(record.classification)).length;
    setButtonBlockerFlag(
      "watcher-tab-source-checker",
      !validProjection,
      "Source Checker is unavailable"
    );
    byId("source-checker-as-of").textContent = report.checked_at || "Awaiting first run";
    byId("source-checker-mode").textContent = report.mode ? `Mode: ${report.mode}` : "Awaiting first run";
    const classificationCards = validProjection
      ? Object.entries(counts).map(([classification, count]) =>
          watcherSummaryCard(classification.replace(/(^|[- ])\w/g, (match) => match.toUpperCase()), count, "latest published classification count"))
      : [];
    byId("source-checker-summary").replaceChildren(
      watcherSummaryCard("Eligible URLs", validProjection ? report.eligible_urls : "Unavailable", validProjection ? "across configured source catalogs" : "feed failed structural validation"),
      watcherSummaryCard("Exceptions", validProjection ? exceptions : "Unavailable", "outside verified or identity-preserving redirect"),
      ...sourceCheckerDeltaCards(report),
      ...classificationCards
    );
    const contract = feedContractState(report, report.checked_at);
    const declaredCatalogCount = Number(report.actual_catalog_count ?? report.catalog_count);
    const loadedCatalogCount = data.cited_sources.length + data.pending_sources.length;
    const expected = contract.expected
      ?? (Number.isFinite(declaredCatalogCount) ? declaredCatalogCount : loadedCatalogCount || null);
    const actual = contract.actual ?? records.length;
    const reconciledState = !validProjection ? "unavailable" : expected !== null && actual !== expected ? "incomplete" : contract.state;
    const reconciledLabel = reconciledState === "incomplete" ? "Incomplete projection" : contract.label;
    const completeness = byId("source-checker-completeness");
    completeness.className = `source-checker-completeness feed-state-${reconciledState}`;
    completeness.replaceChildren(
      element("p", "", [
        !validProjection ? "Unavailable" : reconciledLabel,
        validProjection
          ? Number.isFinite(expected) ? `${actual} of ${expected} expected projection records represented · ${records.length} URL results` : `${records.length} URL result records represented`
          : validation.errors.join(" "),
        contract.reason
      ].filter(Boolean).join(" · ")),
      sourceCheckerAssuranceDetails(report, contract, records.length)
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
    const pages = Math.max(1, Math.ceil(filtered.length / SOURCE_CHECKER_PAGE_SIZE));
    sourceCheckerState.page = Math.min(sourceCheckerState.page, pages);
    updateDenseDisclosureSummary("source-checker-results-summary", filtered.length, "source check", `page ${sourceCheckerState.page} of ${pages}`);
    const host = byId("source-checker-table");
    if (!validProjection || !records.length) {
      host.replaceChildren(element("p", "empty-state", validProjection
        ? "The valid Source Checker feed explicitly contains zero result records."
        : "No valid Source Checker Bot result is available. The loaded feed is missing or failed contract validation."));
      byId("source-checker-pagination").replaceChildren();
      return;
    }
    if (!filtered.length) {
      host.replaceChildren(element("p", "empty-state", "No source checks match the current filters."));
      byId("source-checker-pagination").replaceChildren();
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
    const start = (sourceCheckerState.page - 1) * SOURCE_CHECKER_PAGE_SIZE;
    ordered.slice(start, start + SOURCE_CHECKER_PAGE_SIZE).forEach((record) => {
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
    pagination("source-checker", ordered.length, sourceCheckerState, renderSourceChecker);
  }

  async function refreshLiveSourceChecker() {
    byId("source-checker-live-note").textContent =
      "Source Checker data is the checked-in projection from the latest local transaction.";
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
    const ordered = [...filtered].sort((left, right) =>
      logEntryLatestValue(right) - logEntryLatestValue(left));
    byId(`log-${logId}-visible`).textContent = ordered.length;
    const container = byId(`log-${logId}-table`);
    if (!ordered.length) {
      container.replaceChildren(element("p", "empty-state", "No log entries match the current filters."));
      return;
    }
    if (!ordered.some((entry) => entry.id === state.selectedId)) {
      state.selectedId = ordered[0].id;
    }
    const workspace = element("div", "email-workspace log-email-workspace");
    const list = element("div", "email-list log-email-list");
    list.setAttribute("role", "listbox");
    list.setAttribute("aria-label", `${log.title || log.id} entries, newest first`);
    const preview = element("article", "email-preview log-email-preview");

    const showEntry = (entry) => {
      state.selectedId = entry.id;
      list.querySelectorAll(".email-list-row").forEach((row) => {
        const selected = row.dataset.entryId === String(entry.id);
        row.classList.toggle("selected", selected);
        row.setAttribute("aria-selected", String(selected));
      });
      const heading = element("div", "email-preview-heading");
      const title = element("div");
      title.append(element("span", "eyebrow", "Selected entry"), element("h3", "", logEntryHeadline(log, entry)));
      heading.append(
        title,
        element("time", "email-preview-time", formatDate((entry.values || {}).date || entry.created_at || entry.generated_at))
      );
      const fields = element("dl", "email-preview-fields");
      log.columns.forEach((column) => {
        const field = element("div", "email-preview-field");
        const value = element("dd", "log-cell-value");
        value.innerHTML = (entry.values_html || {})[column.key] || text((entry.values || {})[column.key]);
        field.append(element("dt", "", column.label), value);
        fields.append(field);
      });
      const actions = element("div", "source-list dossier-actions");
      structuredArtifactIdentifiers({
        ...entry,
        ...(entry.structured || {}),
        ...(entry.affected || {})
      }).forEach((identifier) => {
        const target = workbenchTargetForArtifact(identifier, {
          source: "Logs",
          reference: entry.id,
          returnTarget: `automation:logs:${logId}`
        });
        if (target) actions.append(internalInlineLink(`Open ${identifier} in Workbench`, target));
      });
      preview.replaceChildren(heading, fields, logEntryBody(entry), actions);
    };

    ordered.forEach((entry) => {
      const values = entry.values || {};
      const row = element("button", "email-list-row");
      row.type = "button";
      row.dataset.entryId = String(entry.id);
      row.setAttribute("role", "option");
      row.append(
        element("strong", "email-row-title", logEntryHeadline(log, entry)),
        element("time", "email-row-time", formatDate(values.date || entry.created_at || entry.generated_at)),
        element("span", "email-row-summary", text(logEntrySummary(log, entry), "No summary recorded."))
      );
      if (state.groupKey !== "all") {
        row.append(element("span", "email-row-group", text(values[state.groupKey], "Not recorded")));
      }
      row.addEventListener("click", () => showEntry(entry));
      list.append(row);
    });
    workspace.append(list, preview);
    container.replaceChildren(workspace);
    showEntry(ordered.find((entry) => entry.id === state.selectedId) || ordered[0]);
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
    })[key]);
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
    if (!badge) return;
    badge.textContent = `+${count}`;
    badge.hidden = count === 0;
    badge.setAttribute("aria-label", `${count} new or updated`);
  }

  function setNavigationMarker(id, value, status = "", label = "") {
    const marker = byId(id);
    if (!marker) return;
    if (status) {
      marker.className = `tab-status-dot ${status}`.trim();
      marker.textContent = "";
      marker.setAttribute("role", "img");
      marker.setAttribute("aria-label", label || serviceStatusLabel(status));
      marker.title = label || serviceStatusLabel(status);
      return;
    }
    marker.className = "tab-count";
    marker.textContent = String(value ?? 0);
    marker.removeAttribute("role");
    marker.removeAttribute("aria-label");
    marker.removeAttribute("title");
  }

  function setButtonBlockerFlag(id, blocked, label = "Blocking condition represented in this screen") {
    const button = byId(id);
    if (!button) return;
    let marker = button.querySelector(".button-blocker-dot");
    if (!marker) {
      marker = element("span", "tab-status-dot error button-blocker-dot", "");
      marker.setAttribute("role", "img");
      button.append(marker);
    }
    marker.hidden = !blocked;
    marker.setAttribute("aria-label", label);
    marker.title = label;
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
    const incomplete = ["incomplete", "unavailable"].includes(signal.state);
    banner.hidden = signal.count === 0 && !incomplete;
    count.textContent = incomplete
      ? "Update proposal coverage unavailable"
      : signal.proposalCount
        ? `${pluralizeWord(signal.proposalCount, "update proposal")} / ${pluralizeWord(signal.totalCount, "affected record")}`
        : "No current update proposal";
    detail.textContent = incomplete
      ? `${signal.reason || "Exact affected-record identity is unavailable."} Updated-only filtering is disabled.`
      : identifiable
        ? `${identifiable} ${label}${identifiable === 1 ? " is" : "s are"} marked below and shown first.`
        : "The update proposal is available for review, but its records are not yet present in this checked-in view.";
    toggle.hidden = identifiable === 0 || incomplete;
    toggle.disabled = incomplete;
    if (incomplete) {
      if (kind === "courts") courtWatchState.updatesOnly = false;
      else directiveState.updatesOnly = false;
      toggle.setAttribute("aria-pressed", "false");
      toggle.textContent = "Show updated only";
    }
    review.hidden = !signal.url;
    if (signal.url) review.href = signal.url;
  }

  function currentLifecycleRecords() {
    const proposals = Array.isArray(data.progress?.proposals) ? data.progress.proposals : [];
    const pipelineById = new Map(
      (Array.isArray(data.progress?.pipeline?.items) ? data.progress.pipeline.items : [])
        .map((record) => [String(record.id || ""), record])
    );
    const candidates = candidateProjectRecords().map((record) => ({
      ...(() => {
        const pipelineRecord = pipelineById.get(String(record.id)) || {};
        return {
          explanation: pipelineRecord.hold?.reason || "",
          followUp: pipelineRecord.hold?.trigger || (record.horizon_history || {}).follow_up || ""
        };
      })(),
      identifier: record.id,
      kind: "horizon",
      title: record.title,
      kind: "horizon",
      developmentLevel: record.development_level,
      workflowStatus: record.workflow_status,
      nextAudit: record.next_audit,
      priority: record.priority,
      releaseBlocker: record.release_blocker,
      area: record.area || record.proposed_area,
      workstream: record.workstream,
      runs: record.runs,
      score: record.score,
      rebaselineStatus: record.rebaseline_status,
      changeAuditNeeded: record.change_audit_needed,
      lastAudit: record.last_audit,
      owner: record.owner || record.assignee,
      blocker: record.blocker || record.release_blocker,
      dependency: record.dependency || record.dependencies,
      milestone: record.milestone,
      dueDate: record.due_date || record.due,
      monitoringTrigger: record.monitoring_trigger || record.trigger,
      monitoringMethod: record.monitoring_method || record.method,
      monitoringCadence: record.monitoring_cadence || record.cadence,
      monitoringChange: record.change_since_last_pass || record.latest_change,
      monitoringRelevance: record.material_relevance || record.relevance,
      monitoringCoverage: record.monitoring_coverage || record.coverage,
      monitoringGaps: record.monitoring_gaps || record.coverage_gap,
      monitoringTriggered: record.monitoring_triggered || record.trigger_fired,
      lastUpdated: record.updated_at,
      canonicalRecord: "",
      url: record.issue_url,
      needsMonitoring: explicitYes(record.needs_monitoring)
    }));
    return [...candidates, ...proposals];
  }

  function humanDecisionRecords() {
    return currentLifecycleRecords().filter(
      (record) => record.workflowStatus === "Human decision needed"
    );
  }

  function workbenchArtifactRecord(identifier) {
    const id = String(identifier || "").trim();
    if (!id) return null;
    const items = data.progress?.pipeline?.items;
    if (!Array.isArray(items)) return null;
    return items.find((record) =>
      String(record.id || "") === id
      && ["Preliminary candidate", "Formal candidate", "Proposal"].includes(record.workClass)
    ) || null;
  }

  function safeConsoleTarget(value, fallback = "overview") {
    const raw = String(value || "").replace(/^#/, "");
    if (raw.length > 2048 || /[\u0000-\u001f\u007f]/.test(raw)) return fallback;
    try {
      const target = normalizeConsoleTarget(raw);
      if (
        target.length > 2048
        || !/^[A-Za-z0-9_.~%=&:+-]+$/.test(target)
      ) return fallback;
      const staticRoutes = new Set([
        "overview",
        "actions",
        "progress",
        "progress:monitoring",
        "planning",
        "planning:preliminary",
        "planning:candidates",
        "planning:sources",
        "planning:publication",
        "planning:publication:analysis",
        "integrity",
        "automation",
        "automation:overview",
        "automation:gates",
        "automation:capacity",
        "automation:platform",
        "automation:data",
        "automation:security"
      ]);
      if (staticRoutes.has(target)) return target;
      if (/^planning:(?:preliminary|candidates):selected=[A-Za-z0-9._-]{1,128}$/.test(target)) {
        return target;
      }
      if (/^planning:sources:[A-Za-z0-9._:+-]{1,256}$/.test(target)) return target;
      if (/^automation:agents:[A-Za-z0-9._-]{1,128}$/.test(target)) return target;
      if (/^automation:logs:[A-Za-z0-9._-]{1,128}$/.test(target)) return target;
      if (target === "planning:workbench:pipeline") return target;
      if (target.startsWith("planning:workbench:pipeline:")) {
        const parameters = new URLSearchParams(
          target.slice("planning:workbench:pipeline:".length)
        );
        const allowed = new Set([
          "mode", "selected", "search", "gap", "work_class", "scope",
          "sort", "status", "development", "release_blocker", "area",
          "workstream", "owner", "priority", "source", "ref", "return", "focus"
        ]);
        if ([...parameters.keys()].every((key) => allowed.has(key))) return target;
      }
    } catch (_error) {
      return fallback;
    }
    return fallback;
  }

  function safePipelineExternalUrl(value) {
    try {
      const target = new URL(String(value || ""));
      const allowedPath = (
        /^\/Thorncrag\/ARRP\/issues\/[1-9][0-9]*$/.test(target.pathname)
        || /^\/Thorncrag\/ARRP\/blob\/(?:main|[0-9a-f]{40})\/[^?#]+$/.test(target.pathname)
      );
      if (
        target.protocol !== "https:"
        || target.hostname !== "github.com"
        || target.port
        || !allowedPath
        || target.username
        || target.password
      ) return null;
      return target.href;
    } catch (_error) {
      return null;
    }
  }

  function workbenchTargetForArtifact(identifier, context = {}) {
    const record = workbenchArtifactRecord(identifier);
    if (!record) return null;
    const parameters = new URLSearchParams();
    parameters.set("selected", record.id);
    parameters.set("focus", "1");
    if (record.mode === "hold") parameters.set("mode", "hold");
    if (context.source) parameters.set("source", context.source);
    if (context.reference) parameters.set("ref", context.reference);
    if (context.returnTarget) {
      parameters.set("return", safeConsoleTarget(context.returnTarget));
    }
    return `planning:workbench:pipeline:${parameters.toString()}`;
  }

  function structuredArtifactIdentifiers(record = {}) {
    const candidates = [
      record.artifact_id,
      record.artifactId,
      record.affected_artifact_id,
      record.affectedArtifactId,
      record.identifier,
      ...(Array.isArray(record.artifact_ids) ? record.artifact_ids : []),
      ...(Array.isArray(record.affected_artifact_ids) ? record.affected_artifact_ids : []),
      ...(Array.isArray(record.affected_ids) ? record.affected_ids : []),
      ...(Array.isArray(record.record_ids) ? record.record_ids : [])
    ];
    return [...new Set(candidates.map((value) => String(value || "").trim()).filter(Boolean))]
      .filter((identifier) => workbenchArtifactRecord(identifier));
  }

  function applyPipelineParameters(serialized) {
    const parameters = new URLSearchParams(serialized);
    const keys = {
      mode: "mode",
      selected: "selectedId",
      search: "search",
      gap: "gap",
      work_class: "workClass",
      scope: "scope",
      sort: "sort",
      status: "status",
      development: "development",
      release_blocker: "releaseBlocker",
      area: "area",
      workstream: "area",
      owner: "owner",
      priority: "priority",
      source: "sourceContext",
      ref: "sourceReference",
      return: "returnTarget"
    };
    Object.entries(keys).forEach(([parameter, stateKey]) => {
      if (parameters.has(parameter)) {
        const value = parameters.get(parameter) || "all";
        pipelineState[stateKey] = stateKey === "returnTarget"
          ? safeConsoleTarget(value)
          : value;
      }
    });
    pipelineState.mode = pipelineState.mode === "hold" ? "hold" : "active";
    pipelineState.focused = parameters.get("focus") === "1";
    if (pipelineState.mode === "hold") pipelineState.scope = "all";
    return { ...pipelineState };
  }

  function legacyNextWorkTarget(serialized) {
    const parameters = new URLSearchParams(serialized);
    const cohort = parameters.get("cohort") || "";
    const status = parameters.get("status") || "";
    if (cohort === "Human-reserved") return "actions";
    if (cohort === "Fired monitoring") return "progress:monitoring";
    if (status === "Human decision needed") return "actions";
    if (status === "Publication approval") return "planning:publication";
    if (["Blocked", "Deferred"].includes(status)) parameters.set("mode", "hold");
    parameters.delete("cohort");
    if (cohort === "Audit-ready") parameters.set("status", "Audit work");
    if (cohort === "External-review follow-up") {
      parameters.set("status", "External review");
      parameters.set("scope", "review-ready");
    }
    if (cohort === "Critical / High release blocker") {
      parameters.set("release_blocker", "required");
    }
    const suffix = parameters.toString();
    return `planning:workbench:pipeline${suffix ? `:${suffix}` : ""}`;
  }

  function normalizeConsoleTarget(target) {
    const parts = String(target || "").replace(/^#/, "").split(":");
    if (parts[0] === "candidates") {
      const destination = ["preliminary", "public"].includes(parts[1])
        ? "preliminary"
        : "candidates";
      return ["planning", destination, ...parts.slice(2)].join(":");
    }
    if (parts[0] === "sources") {
      return ["planning", "sources", ...parts.slice(1)].join(":");
    }
    if (parts[0] === "publication" || parts[0] === "pages") {
      return ["planning", "publication", ...parts.slice(1)].join(":");
    }
    if (parts[0] === "planning" && parts[1] === "next-work") {
      return legacyNextWorkTarget(parts.slice(2).join(":"));
    }
    if (parts[0] === "progress" && parts[1] === "next-work") {
      return legacyNextWorkTarget(parts.slice(2).join(":"));
    }
    if (parts[0] === "planning" && parts[1] === "pipeline") {
      return ["planning", "workbench", "pipeline", ...parts.slice(2)].join(":");
    }
    if (parts[0] === "planning" && parts[1] === "workbench" && !parts[2]) {
      return "planning:workbench:pipeline";
    }
    if (parts[0] === "logs") {
      return ["automation", "logs", parts[1] || "incidents", ...parts.slice(2)].join(":");
    }
    if (parts[0] === "automation" && ["administration", "chain"].includes(parts[1])) {
      return ["automation", "overview", ...parts.slice(2)].join(":");
    }
    if (parts[0] === "automation" && parts[1] === "workers") {
      return ["automation", "agents", ...parts.slice(2)].join(":");
    }
    if (parts[0] === "automation" && [
      "run-coordinator-bot",
      "case-monitor-bot",
      "presidential-directives-bot",
      "source-checker-bot",
      "project-console-progress-bot",
      "project-integrity-bot",
      "elim"
    ].includes(parts[1])) {
      return ["automation", "agents", parts[1], ...parts.slice(2)].join(":");
    }
    if (parts[0] === "automation" && parts[1] === "agents" && !parts[2]) {
      return "automation:agents:run-coordinator-bot";
    }
    return parts.join(":");
  }

  function navigateToConsoleTarget(target) {
    const normalizedTarget = normalizeConsoleTarget(target);
    const parts = normalizedTarget.split(":");
    if (normalizedTarget !== String(target || "").replace(/^#/, "")) {
      window.history.replaceState(null, "", `#${normalizedTarget}`);
    }
    const automationSubviews = ["overview", "agents", "gates", "security", "capacity", "platform", "data", "logs"];
    activateTab(parts[0]);
    if (parts[0] === "planning" && parts[1]) activateSectionTab("planning", parts[1]);
    if (parts[0] === "automation" && parts[1] === "logs") {
      activateSectionTab("automation", "logs");
      activateLogView(parts[2] || "incidents");
      if (parts[2] === "agents" && parts[3]) {
        const record = data.agent_registry.find((agent) => agent.id === parts[3]);
        const select = byId("log-agents-agent");
        const match = [...(select?.options || [])].find((option) =>
          [parts[3], record?.name].filter(Boolean).some((value) =>
            String(option.value).localeCompare(String(value), undefined, { sensitivity: "accent" }) === 0));
        if (select && match) {
          select.value = match.value;
          logStates.agents.filters.agent = match.value;
          renderProjectLog("agents");
        }
      }
    }
    if (parts[0] === "planning" && parts[1] === "workbench" && parts[2] === "pipeline") {
      resetPipelineMode("active");
      if (parts[3]) applyPipelineParameters(parts.slice(3).join(":"));
      if (loadedDomains.has("progress")) renderPipeline();
    }
    if (parts[0] === "automation" && automationSubviews.includes(parts[1])) {
      activateSectionTab("automation", parts[1]);
    }
    if (parts[0] === "planning" && parts[1] === "sources"
      && parts[2] === "watchers" && parts[3]) activateWatcherTab(parts[3]);
    let destination = byId(`panel-${parts[0]}`);
    if (parts[0] === "progress" && parts[1]) {
      const section = byId(`progress-${parts[1]}`);
      if (section?.tagName === "DETAILS") section.open = true;
      if (section) destination = section;
    }
    if (parts[0] === "automation" && parts[1] === "agents" && parts[2]) {
      activateAutomationRole(parts[2], false, false);
      destination = byId("automation-role-detail") || destination;
    }
    if (parts[0] === "planning" && parts[1] === "sources" && parts[2]) {
      destination = {
        catalog: byId("sources-heading"),
        pending: byId("pending-heading"),
        watchers: byId("watchers-heading")
      }[parts[2]] || destination;
    }
    if (parts[0] === "planning"
      && ["candidates", "preliminary"].includes(parts[1])
      && parts[2]?.startsWith("selected=")) {
      const selected = decodeURIComponent(parts[2].slice("selected=".length));
      const card = byId(`candidate-${selected}`);
      if (card) {
        card.open = true;
        destination = card;
      }
    }
    if (parts[0] === "planning" && parts[1] === "publication" && parts[2]) {
      destination = {
        assignments: byId("pages-heading"),
        analysis: byId("publication-analysis-heading"),
        builder: byId("publication-builder-heading")
      }[parts[2]] || destination;
    }
    destination?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function navigateFromHash() {
    const target = window.location.hash.replace(/^#/, "");
    const normalized = normalizeConsoleTarget(target);
    if (!normalized || !byId(`panel-${normalized.split(":")[0]}`)) return;
    navigateToConsoleTarget(target);
  }

  function actionInboxIdentity(value) {
    let hash = 2166136261;
    const input = String(value || "");
    for (let index = 0; index < input.length; index += 1) {
      hash ^= input.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return `action-inbox-${(hash >>> 0).toString(16).padStart(8, "0")}`;
  }

  function actionInboxItem(group, item, index) {
    const repositoryReview = item && typeof item === "object" && item.kind === "repository-review";
    const title = typeof item === "object" ? item.label : String(item || "Untitled action item");
    const rawIdentity = [
      group.scope,
      group.label,
      repositoryReview ? item.evidenceUrl : item?.href,
      title,
      index
    ].filter(Boolean).join("|");
    const id = actionInboxIdentity(rawIdentity);
    const itemHref = String(item?.href || "");
    const route = repositoryReview
      ? item.specialistTarget || group.target
      : item?.route
        ? item.route
      : itemHref.startsWith("#")
        ? itemHref.replace(/^#/, "")
        : group.target;
    const externalUrl = repositoryReview
      ? item.evidenceUrl || ""
      : item?.canonicalUrl
        ? item.canonicalUrl
      : /^https?:\/\//.test(itemHref)
        ? itemHref
        : "";
    const question = repositoryReview
      ? item.humanQuestion && String(item.humanQuestion).toLowerCase() !== "none"
        ? item.humanQuestion
        : group.scope === "mine"
          ? "Review and decide the exact-head recommendation."
          : "Monitor Elim's exact-head review and disposition."
      : item?.question || item?.recovery || "";
    const recommendation = repositoryReview
      ? item.recommendation
      : item?.recommendation || item?.options || "";
    const artifactIdentifier = structuredArtifactIdentifiers(item || {})[0] || "";
    const workbenchTarget = artifactIdentifier
      ? workbenchTargetForArtifact(artifactIdentifier, {
          source: "Action Items",
          reference: id,
          returnTarget: "actions"
        })
      : null;
    return {
      id,
      scope: group.scope,
      queue: group.label,
      title,
      owner: repositoryReview ? item.owner : item?.owner || (group.scope === "mine" ? "You" : "Assigned elsewhere"),
      status: repositoryReview ? item.status : item?.status || group.status,
      tone: repositoryReview ? item.tone || group.tone : item?.tone || group.tone,
      updated: Boolean(group.updated || item?.updated),
      summary: question || recommendation || group.detail,
      question,
      recommendation,
      whyNow: repositoryReview
        ? item.rationale
        : item?.whyNow || group.detail,
      consequence: repositoryReview
        ? item.consequence
        : item?.consequence || "",
      due: repositoryReview ? item.due : item?.due || "",
      dueAt: item?.dueAt || "",
      priority: item?.priority || "",
      blockingEffect: item?.blockingEffect === true,
      consequentialDecision: item?.consequentialDecision === true,
      route,
      routeLabel: repositoryReview
        ? `Open ${item.specialistLabel || "owning specialist view"}`
        : group.openLabel || "Open owning Console view",
      workbenchTarget,
      externalUrl,
      externalLabel: repositoryReview ? "Open pull request ↗" : "Open canonical record ↗",
      affectedSummary: repositoryReview ? item.affectedSummary : "",
      provenance: repositoryReview
        ? `Head ${String(item.headRevision || "unknown").slice(0, 10)} · ${item.reviewer || "Reviewer unavailable"}`
        : "",
      searchText: [
        group.label,
        title,
        repositoryReview ? item.owner : item?.owner,
        repositoryReview ? item.status : group.status,
        question,
        recommendation,
        repositoryReview ? item.rationale : item?.whyNow,
        repositoryReview ? item.affectedSummary : "",
        item?.consequence,
        item?.due
      ].filter(Boolean).join(" ").toLowerCase()
    };
  }

  function priorityAttentionReasons(item, now = Date.now()) {
    if (!item || item.scope !== "mine") return [];
    const reasons = [];
    if (item.blockingEffect === true) {
      reasons.push({ key: "blocking", rank: 0, label: "Explicit blocking effect" });
    }
    const priority = String(item.priority || "").trim().toLowerCase();
    if (priority === "critical") {
      reasons.push({ key: "critical", rank: 1, label: "Critical priority" });
    } else if (priority === "high") {
      reasons.push({ key: "high", rank: 2, label: "High priority" });
    }
    const dueAt = parseTimestamp(item.dueAt);
    if (dueAt !== null) {
      reasons.push({
        key: dueAt <= now ? "overdue" : "due",
        rank: dueAt <= now ? 1 : 3,
        label: dueAt <= now
          ? `Overdue since ${formatOperationalDate(item.dueAt)}`
          : `Due ${formatOperationalDate(item.dueAt)}`
      });
    }
    if (item.consequentialDecision === true) {
      reasons.push({ key: "consequential", rank: 4, label: "Recorded consequential decision" });
    }
    return reasons;
  }

  function priorityAttentionItems(items = actionInboxState.items, now = Date.now()) {
    return items
      .map((item) => ({ item, reasons: priorityAttentionReasons(item, now) }))
      .filter((record) => record.reasons.length)
      .sort((left, right) =>
        Math.min(...left.reasons.map((reason) => reason.rank))
          - Math.min(...right.reasons.map((reason) => reason.rank))
        || (parseTimestamp(left.item.dueAt) ?? Infinity) - (parseTimestamp(right.item.dueAt) ?? Infinity)
        || left.item.title.localeCompare(right.item.title)
      )
      .slice(0, 5);
  }

  function openPriorityAttentionItem(item) {
    actionInboxState.filter = "mine";
    actionInboxState.search = "";
    byId("action-inbox-search").value = "";
    document.querySelectorAll("[data-action-filter]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.actionFilter === "mine"));
    });
    renderActionInboxRows();
    selectActionInboxItem(item.id);
    byId(`${item.id}-row`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function renderPriorityAttention() {
    const section = byId("action-priority-attention");
    const host = byId("action-priority-list");
    const records = priorityAttentionItems();
    section.hidden = records.length === 0;
    if (!records.length) {
      host.replaceChildren();
      byId("action-priority-summary").textContent = "";
      return;
    }
    host.replaceChildren(...records.map(({ item, reasons }) => {
      const row = element("button", "action-priority-row");
      row.type = "button";
      const copy = element("span", "action-priority-copy");
      copy.append(
        element("strong", "", item.title),
        element("span", "", reasons.map((reason) => reason.label).join(" · "))
      );
      row.append(
        copy,
        element("span", "action-priority-open", "Open in inbox →")
      );
      row.addEventListener("click", () => openPriorityAttentionItem(item));
      return row;
    }));
    byId("action-priority-summary").textContent =
      `${records.length} elevated item${records.length === 1 ? "" : "s"}`;
  }

  function actionInboxRow(item) {
    const row = element("button", "action-inbox-row");
    row.type = "button";
    row.id = `${item.id}-row`;
    row.dataset.actionItemId = item.id;
    row.setAttribute("aria-pressed", String(actionInboxState.selectedId === item.id));
    const attention = element("span", `action-inbox-attention ${item.tone || ""}`.trim());
    attention.setAttribute("aria-hidden", "true");
    const copy = element("span", "action-inbox-row-copy");
    copy.append(
      element("span", "action-inbox-row-title", item.title),
      element("span", "action-inbox-row-summary", item.summary || "Open the item preview for details.")
    );
    const meta = element("span", "action-inbox-row-meta");
    meta.append(
      element("span", "", item.queue),
      element("span", "", item.owner),
      ...(item.due ? [element("span", "", item.due)] : [])
    );
    copy.append(meta);
    const scope = element(
      "span",
      `action-inbox-row-scope${item.scope === "oversight" ? " oversight" : ""}`,
      item.scope === "mine" ? "Mine" : "Oversight"
    );
    row.append(attention, copy, scope);
    row.addEventListener("click", () => selectActionInboxItem(item.id));
    return row;
  }

  function actionInboxLink(label, route, external = false) {
    const link = element("a", external ? "record-link" : "record-link secondary", label);
    link.href = external ? route : `#${route}`;
    if (external) {
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    } else {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        navigateToConsoleTarget(route);
      });
    }
    return link;
  }

  function renderActionInboxPreview(item) {
    const preview = byId("action-item-preview");
    if (!item) {
      const empty = element("div", "action-preview-empty");
      empty.append(
        element("span", "eyebrow", "Item preview"),
        element("h3", "", "No item selected"),
        element("p", "", "No action items match the current filter and search.")
      );
      empty.querySelector("h3").id = "action-preview-heading";
      preview.replaceChildren(empty);
      return;
    }
    const header = element("header", "action-preview-header");
    header.append(element("span", "eyebrow", item.queue));
    const heading = element("h3", "", item.title);
    heading.id = "action-preview-heading";
    header.append(heading);
    const badges = element("div", "action-preview-badges");
    badges.append(
      element("span", "badge info", item.scope === "mine" ? "Assigned to you" : "Oversight"),
      element("span", `badge ${item.tone || "info"}`.trim(), item.status || "Open"),
      element("span", "badge", item.owner)
    );
    if (item.updated) badges.append(element("span", "badge warning", "New or updated"));
    header.append(badges);
    const sections = [];
    [
      ["Question or recovery", item.question],
      ["Recommendation or options", item.recommendation],
      ["Why this is here now", item.whyNow],
      ["Consequence of delay", item.consequence],
      ["Age or due trigger", item.due],
      ["Affected records", item.affectedSummary],
      ["Review provenance", item.provenance]
    ].forEach(([label, value]) => {
      if (!value) return;
      const section = element("section", "action-preview-section");
      section.append(element("h4", "", label), element("p", "", value));
      sections.push(section);
    });
    const links = element("div", "action-preview-links");
    if (item.route) links.append(actionInboxLink(item.routeLabel, item.route));
    if (item.workbenchTarget) links.append(actionInboxLink("Open in Workbench", item.workbenchTarget));
    if (item.externalUrl) links.append(actionInboxLink(item.externalLabel, item.externalUrl, true));
    preview.replaceChildren(header, ...sections, links);
  }

  function filteredActionInboxItems() {
    const query = actionInboxState.search.trim().toLowerCase();
    return actionInboxState.items.filter((item) => {
      if (actionInboxState.filter !== "all" && item.scope !== actionInboxState.filter) return false;
      return !query || item.searchText.includes(query);
    });
  }

  function selectActionInboxItem(id, focus = false) {
    actionInboxState.selectedId = id;
    document.querySelectorAll(".action-inbox-row").forEach((row) => {
      row.setAttribute("aria-pressed", String(row.dataset.actionItemId === id));
    });
    const item = actionInboxState.items.find((record) => record.id === id);
    renderActionInboxPreview(item);
    if (focus) byId(`${id}-row`)?.focus();
  }

  function renderActionInboxRows() {
    const items = filteredActionInboxItems();
    if (!items.some((item) => item.id === actionInboxState.selectedId)) {
      actionInboxState.selectedId = items[0]?.id || "";
    }
    byId("action-items-grid").replaceChildren(...(items.length
      ? items.map(actionInboxRow)
      : [element("p", "action-inbox-empty", "No action items match this view.")]));
    const filterLabels = { mine: "My items", oversight: "Oversight", all: "All open" };
    byId("action-inbox-list-heading").textContent = filterLabels[actionInboxState.filter];
    byId("action-inbox-result-summary").textContent = actionInboxState.search
      ? `${pluralizeWord(items.length, "matching item")} · ${pluralizeWord(actionInboxState.items.length, "open item")} total`
      : pluralizeWord(items.length, "open item");
    renderActionInboxPreview(
      actionInboxState.items.find((item) => item.id === actionInboxState.selectedId)
    );
  }

  function applyActionInboxLayout(layout, persist = true) {
    actionInboxState.layout = layout === "below" ? "below" : "right";
    byId("action-inbox-workspace").dataset.previewPosition = actionInboxState.layout;
    document.querySelectorAll("[data-action-layout]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.actionLayout === actionInboxState.layout));
    });
    if (!persist) return;
    try {
      window.localStorage.setItem(ACTION_INBOX_LAYOUT_STORAGE_KEY, actionInboxState.layout);
    } catch (_error) { /* keep the selected layout until reload */ }
  }

  function initializeActionInboxControls() {
    document.querySelectorAll("[data-action-filter]").forEach((button) => {
      button.addEventListener("click", () => {
        actionInboxState.filter = button.dataset.actionFilter;
        document.querySelectorAll("[data-action-filter]").forEach((candidate) => {
          candidate.setAttribute("aria-pressed", String(candidate === button));
        });
        renderActionInboxRows();
      });
    });
    byId("action-inbox-search").addEventListener("input", (event) => {
      actionInboxState.search = event.target.value;
      renderActionInboxRows();
    });
    document.querySelectorAll("[data-action-layout]").forEach((button) => {
      button.addEventListener("click", () => applyActionInboxLayout(button.dataset.actionLayout));
    });
    let savedLayout = "right";
    try {
      savedLayout = window.localStorage.getItem(ACTION_INBOX_LAYOUT_STORAGE_KEY) || "right";
    } catch (_error) { /* use the right-side default */ }
    applyActionInboxLayout(savedLayout, false);
    byId("action-items-grid").addEventListener("keydown", (event) => {
      if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
      const rows = [...byId("action-items-grid").querySelectorAll(".action-inbox-row")];
      if (!rows.length) return;
      const current = event.target.closest(".action-inbox-row");
      let index = rows.indexOf(current);
      if (event.key === "Home") index = 0;
      else if (event.key === "End") index = rows.length - 1;
      else if (event.key === "ArrowDown") index = Math.min(rows.length - 1, Math.max(0, index + 1));
      else index = Math.max(0, index < 0 ? 0 : index - 1);
      event.preventDefault();
      selectActionInboxItem(rows[index].dataset.actionItemId, true);
    });
  }

  function integrityFindingNeedsHuman(finding) {
    return String(finding.attention || "").toLowerCase() === "human";
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

  function exactIntegrityProblemRecords(feed = data.integrity) {
    const current = feed && typeof feed.current === "object" ? feed.current : {};
    return (Array.isArray(current.findings) ? current.findings : []).map((finding) => {
      const human = integrityFindingNeedsHuman(finding);
      const normalized = {
        category: finding.category || "Project structure",
        severity: finding.severity || "warning",
        attention: human ? "human" : (finding.attention || "agent"),
        owner: human ? "Human" : (finding.owner || "Elim"),
        reported_by: "Project Integrity Bot",
        status: finding.status || "Open",
        detected_at: finding.detected_at || current.generated_at || data.generated_at,
        checked_at: finding.checked_at || current.generated_at || data.generated_at,
        ...finding
      };
      normalized.affected_ids = finding.affected_ids || finding.owner_ids || [];
      normalized.reference = finding.reference || stableProblemReference(normalized);
      return normalized;
    });
  }

  function securityActionRecords() {
    const projection = securityAssuranceProjection();
    return projection.tools
      .filter((tool) => tool.private_attention === "yes")
      .filter((tool) => ["Human", "Elim"].includes(tool.owner_class))
      .map((tool) => ({
        reference: `SECURITY-${String(tool.tool_id).toUpperCase()}`,
        category: "Protected security action",
        severity: "warning",
        attention: tool.owner_class === "Human" ? "human" : "agent",
        owner: tool.owner_class,
        reported_by: "Security assurance projection",
        status: "Protected review required",
        message: tool.owner_class === "Human"
          ? "Review private security action"
          : "Private security remediation requires review",
        source_url: "#automation:security",
        checked_at: tool.last_checked || projection.checkedAt,
        security_tool_id: tool.tool_id
      }));
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
        source_url: "#sources:catalog",
        observed_url: record.final_url || record.requested_url || "",
        owner_ids: record.owner_ids || [],
        message: `${record.classification}: ${record.error || "the observed URL or identity requires review against the cataloged source."}`,
        detected_at: data.source_checker.checked_at || data.source_checker.generated_at,
        checked_at: data.source_checker.checked_at || data.source_checker.generated_at
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

    currentLifecycleRecords()
      .map((record) => ({ record, score: scorePresentation(record.score) }))
      .filter(({ score }) => !score.valid)
      .forEach(({ record, score }) => add({
        category: "Project consistency",
        severity: "error",
        attention: "agent",
        owner: "Elim",
        reported_by: "Project Console score check",
        status: "Correction required",
        owner_ids: [record.identifier],
        message: `${record.identifier} has ${score.label}; scores must be numeric values from 0 through 100 or explicitly unavailable.`,
        source_url: record.canonicalRecord ? `${GITHUB_BLOB_ROOT}${record.canonicalRecord}` : record.url
      }));

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
    (Array.isArray(data.progress?.pipeline?.integrityFindings)
      ? data.progress.pipeline.integrityFindings
      : []).forEach((finding) => add({
      category: "Pipeline integrity",
      severity: finding.severity || "warning",
      attention: "agent",
      owner: "Elim",
      reported_by: "Project Console Pipeline projection",
      status: "Correction required",
      owner_ids: [finding.identifier].filter(Boolean),
      message: finding.message,
      source_url: finding.route?.startsWith("http")
        ? finding.route
        : `#${finding.route || "planning:workbench:pipeline"}`,
      detected_at: data.progress.pipeline.generatedAt,
      checked_at: data.progress.pipeline.generatedAt
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

    failedAutomationStages().forEach((stage) => {
      const record = data.agent_registry.find((agent) => agent.id === stage.id);
      add({
        category: "Automation failure",
        severity: "error",
        attention: "human",
        owner: "Human",
        reported_by: "Run Coordinator Bot",
        status: String(stage.status || "Error").replaceAll("_", " "),
        owner_ids: [stage.id],
        message: `${record?.name || stage.id}: ${botFailureSummary(stage)}`,
        source_url: `#automation:agents:${stage.id}`,
        detected_at: stage.completed_at || stage.updated_at || data.run_chain?.updated_at,
        checked_at: data.run_chain?.updated_at || data.generated_at
      });
    });

    securityActionRecords().forEach((problem) => add(problem));

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
    const identifier = structuredArtifactIdentifiers(finding)[0] || "";
    return {
      label: `${finding.reference || "Problem"}: ${message}`,
      href: /^https?:\/\//.test(String(finding.source_url || ""))
        ? finding.source_url : "#integrity",
      owner: problemOwnerLabel(finding),
      status: text(finding.status, "Open"),
      tone: finding.severity || "warning",
      question: finding.human_question || finding.next_action || message,
      recommendation: finding.recommendation || "Review the complete finding in Integrity and record the disposition at its canonical owner.",
      whyNow: `${text(finding.status, "Open")} ${finding.severity || "warning"} finding`,
      consequence: finding.consequence_of_delay || "The exception remains unresolved and may block reliable project or release decisions.",
      due: finding.due_at ? formatDate(finding.due_at) : `Detected ${formatDate(finding.detected_at)}`,
      dueAt: finding.due_at || "",
      priority: finding.priority || "",
      blockingEffect: (
        finding.blocking === true
        || finding.blocks_automation === true
        || finding.release_blocker === true
      ),
      consequentialDecision: Boolean(
        finding.human_question && finding.consequence_of_delay
      ),
      artifact_id: identifier
    };
  }

  function exactHeadRecommendation(pullRequest) {
    const headRevision = String(pullRequest?.head?.sha || "");
    if (!headRevision) return null;
    return data.repository_review_recommendations.find((record) =>
      Number(record.pull_request_number) === Number(pullRequest.number)
        && String(record.head_revision || "") === headRevision) || null;
  }

  function exactWatcherAffected(pullRequest, affectedKey) {
    const exact = exactHeadRecommendation(pullRequest);
    const affected = exact?.affected;
    if (!exact || !affected || typeof affected !== "object" || affected.complete !== true) {
      return { valid: false, ids: new Set(), count: null, totalCount: null, proposalCount: null, reason: "No complete structured exact-head affected-record enumeration is available." };
    }
    const ids = Array.isArray(affected[affectedKey])
      ? [...new Set(affected[affectedKey].map(String).filter(Boolean))]
      : null;
    const total = Number(affected.total_count);
    if (!ids || !Number.isFinite(total) || total < 0 || (total > 0 && ids.length === 0)) {
      return { valid: false, ids: new Set(), count: null, totalCount: null, proposalCount: null, reason: "The exact-head recommendation lacks valid typed affected IDs or a total count." };
    }
    return {
      valid: true,
      ids: new Set(ids),
      count: ids.length,
      totalCount: total,
      proposalCount: 1,
      reason: ""
    };
  }

  function hasNextLink(linkHeader) {
    return String(linkHeader || "").split(",").some((part) =>
      /;\s*rel\s*=\s*"?next"?/i.test(part));
  }

  function repositorySpecialistRoute(affected = {}) {
    const directiveIds = [...new Set(Array.isArray(affected.directive_ids) ? affected.directive_ids : [])];
    const sourceIds = [...new Set(Array.isArray(affected.source_ids) ? affected.source_ids : [])];
    if (directiveIds.length) {
      return {
        target: "sources:watchers:directives",
        label: "Presidential-directives watcher"
      };
    }
    if (sourceIds.length) {
      return {
        target: "sources:watchers:courts",
        label: "Court-case watcher"
      };
    }
    return {
      target: "automation:overview",
      label: "Agents & Bots administration"
    };
  }

  function repositoryAffectedSummary(affected = {}) {
    const sourceIds = [...new Set(Array.isArray(affected.source_ids) ? affected.source_ids : [])];
    const directiveIds = [...new Set(Array.isArray(affected.directive_ids) ? affected.directive_ids : [])];
    const issueIds = [...new Set(Array.isArray(affected.issue_development_ids)
      ? affected.issue_development_ids
      : [])];
    const declaredIssueCount = Number(affected.issue_development_count);
    const issueCount = Number.isFinite(declaredIssueCount) && declaredIssueCount >= 0
      ? declaredIssueCount
      : issueIds.length;
    const declaredTotal = Number(affected.total_count);
    const total = Number.isFinite(declaredTotal) && declaredTotal >= 0
      ? declaredTotal
      : new Set([...sourceIds, ...directiveIds, ...issueIds]).size;
    return [
      affectedCompleteLabel(total, affected.complete === true),
      pluralizeWord(issueCount, "proposal/candidate"),
      pluralizeWord(sourceIds.length, "source"),
      pluralizeWord(directiveIds.length, "directive")
    ].join(" · ");
  }

  function repositoryReviewEntry(pullRequest) {
    const branch = String(pullRequest.head?.ref || "");
    const kind = branch.startsWith("dependabot/")
      ? "dependency update"
      : /^(?:bot|automation)\//.test(branch)
        ? "bot proposal"
        : branch.startsWith("codex/")
          ? "Codex change"
          : "repository change";
    const headRevision = String(pullRequest.head?.sha || "");
    const recommendations = data.repository_review_recommendations
      .filter((record) => Number(record.pull_request_number) === Number(pullRequest.number))
      .sort((left, right) => String(right.recorded_at || "").localeCompare(String(left.recorded_at || "")));
    const exact = exactHeadRecommendation(pullRequest);
    const stale = !exact && recommendations[0];
    const owner = exact?.action_owner || "Elim";
    const status = exact
      ? "Recommendation current"
      : stale
        ? "Recommendation stale"
        : "Awaiting Elim review";
    const recommendation = exact
      ? exact.recommendation
      : stale
        ? "Elim must reassess the complete current head before any disposition; the earlier recommendation is retained only as history."
        : "Elim must review the complete pull-request head and record a reasoned disposition before this can become a human action.";
    const rationale = exact
      ? exact.rationale
      : stale
        ? `The logged recommendation is bound to ${String(stale.head_revision || "").slice(0, 10)}, not the live head.`
        : "An open pull request is repository evidence, not by itself a decision assigned to the project owner.";
    const affected = exact?.affected && typeof exact.affected === "object" ? exact.affected : {};
    const sourceIds = [...new Set(affected.source_ids || [])];
    const directiveIds = [...new Set(affected.directive_ids || [])];
    const recordIds = [...new Set(affected.record_ids || [])];
    const specialist = repositorySpecialistRoute(affected);
    const declaredTotal = affected.total_count;
    const affectedCount = declaredTotal !== null && declaredTotal !== undefined
      && declaredTotal !== "" && Number.isFinite(Number(declaredTotal))
      ? Number(declaredTotal)
      : recordIds.length || new Set([...sourceIds, ...directiveIds]).size;
    return {
      kind: "repository-review",
      label: `PR #${pullRequest.number}: ${pullRequest.title} — ${pullRequest.draft ? "draft" : kind}`,
      status,
      tone: exact ? (owner === "Human" ? "warning" : "current") : "stale",
      owner: owner === "Human" ? "Assigned to you" : owner === "None" ? "No further action" : "Owned by Elim",
      actionOwner: owner,
      countsAsHuman: Boolean(exact && owner === "Human"),
      recommendation,
      rationale,
      humanQuestion: exact?.human_question || "None",
      reviewer: exact
        ? `${exact.reviewer} · ${exact.recorded_at}`
        : stale
          ? `Prior review ${stale.recorded_at}`
          : "Recommendation not yet recorded",
      headRevision: headRevision || "unknown",
      affectedCount,
      sourceCount: sourceIds.length,
      directiveCount: directiveIds.length,
      recordCount: recordIds.length,
      affectedComplete: affected.complete === true,
      affectedSummary: exact
        ? repositoryAffectedSummary(affected)
        : "Affected-record enumeration unavailable until an exact-head review is recorded.",
      evidenceUrl: pullRequest.html_url,
      specialistTarget: specialist.target,
      specialistLabel: specialist.label,
      consequence: exact?.consequence_of_delay || "The repository proposal cannot be authoritatively disposed until the assigned review is completed.",
      due: exact?.due_at ? formatDate(exact.due_at) : `Reviewed ${formatDate(exact?.recorded_at)}`,
      dueAt: exact?.due_at || "",
      priority: exact?.priority || "",
      blockingEffect: exact?.blocks_future_automation === true,
      consequentialDecision: Boolean(
        owner === "Human"
        && exact?.human_question
        && String(exact.human_question).toLowerCase() !== "none"
        && exact?.consequence_of_delay
      )
    };
  }

  function affectedCompleteLabel(count, complete) {
    if (!complete) return `${count || 0} enumerated; completeness not confirmed`;
    return `${pluralizeWord(Number(count || 0), "affected record")} in the complete exact-head enumeration`;
  }

  function unresolvedAutomationActionItems(problemRecords = allProblemRecords()) {
    const integrityHumanFindings = problemRecords
      .filter((finding) => finding.attention === "human")
      .filter((finding) => finding.category !== "Automation failure")
      .filter((finding) => finding.reported_by !== "Security assurance projection")
      .sort((left, right) => String(left.message || "").localeCompare(String(right.message || "")));
    const automationActions = unresolvedOperationalIncidents().map((incident) => ({
      id: incident.incident_id,
      stage: incident.component,
      summary: incident.summary,
      occurrences: (incident.occurrences || []).length,
      owners: incident.owner ? [incident.owner] : [],
      humanOwned: humanOwnsIncident(incident),
      recovery: incident.next_action,
      firstSeen: incident.first_observed,
      lastSeen: incident.last_observed,
      impact: incident.impact,
      status: incident.status,
      recommendedOwner: incident.recommended_owner,
      source_url: `#automation:logs:incidents:selected=${encodeURIComponent(incident.incident_id)}`
    }));
    return {
      integrityHumanFindings,
      automationActions,
      automationHumanActions: automationActions.filter((item) => item.humanOwned),
      automationOversightActions: automationActions.filter((item) => !item.humanOwned)
    };
  }

  function actionItemSnapshot() {
    const decisionRecords = humanDecisionRecords();
    const problemRecords = allProblemRecords();
    const {
      integrityHumanFindings,
      automationActions,
      automationHumanActions,
      automationOversightActions
    } = unresolvedAutomationActionItems(problemRecords);
    const pullRequestsKnown = reviewSignals.pullRequestsStatus === "current";
    const openPullRequests = pullRequestsKnown ? reviewSignals.pullRequests : [];
    const repositoryReviews = openPullRequests.map(repositoryReviewEntry);
    const repositoryHumanActions = repositoryReviews.filter((item) => item.countsAsHuman);
    const repositoryElimActions = repositoryReviews.filter(
      (item) => item.actionOwner === "Elim"
    );
    const securityProblems = problemRecords.filter((item) =>
      item.reported_by === "Security assurance projection");
    const securityHumanActions = securityProblems.filter((item) =>
      item.attention === "human" || String(item.owner || "").toLowerCase() === "human");
    const securityOversightActions = securityProblems.filter((item) =>
      !securityHumanActions.includes(item));
    return {
      decisionRecords,
      decisions: decisionRecords.length,
      preliminary: data.records.length,
      pending: data.pending_sources.length,
      problemRecords,
      integrityHumanFindings,
      integrityHuman: integrityHumanFindings.length,
      automationActions,
      automationHumanActions,
      automationOversightActions,
      pullRequests: openPullRequests.length,
      pullRequestsKnown,
      repositoryReviews,
      repositoryHumanActions,
      repositoryElimActions,
      securityHumanActions,
      securityOversightActions,
      total: decisionRecords.length
        + data.records.length
        + data.pending_sources.length
        + repositoryHumanActions.length
        + securityHumanActions.length
        + integrityHumanFindings.length
        + automationHumanActions.length
    };
  }

  function renderActionItems() {
    const {
      decisionRecords,
      decisions,
      preliminary,
      pending,
      problemRecords,
      integrityHumanFindings,
      integrityHuman,
      automationActions,
      automationHumanActions,
      automationOversightActions,
      pullRequests,
      pullRequestsKnown,
      repositoryReviews,
      repositoryHumanActions,
      repositoryElimActions,
      securityHumanActions,
      securityOversightActions,
      total
    } = actionItemSnapshot();
    const newOrUpdated = preliminary;
    const oversightProblems = problemRecords
      .filter((finding) => finding.attention !== "human")
      .filter((finding) => finding.reported_by !== "Security assurance projection")
      .filter((finding) => !/resolved|closed|complete/i.test(String(finding.status || "")));
    const oversightCount = repositoryElimActions.length
      + securityOversightActions.length
      + automationOversightActions.length
      + oversightProblems.length;
    byId("tab-actions-count").textContent = total;
    byId("assigned-actions-count").textContent = total;
    byId("oversight-actions-count").textContent = oversightCount;
    byId("action-items-note").textContent = total
      ? `${total} confirmed item${total === 1 ? "" : "s"} assigned to you, all listed below; ${newOrUpdated} new or updated.${repositoryElimActions.length ? ` ${repositoryElimActions.length} repository proposal${repositoryElimActions.length === 1 ? " remains" : "s remain"} with Elim and do not count as your action.` : ""}${pullRequestsKnown ? "" : " Live pull-request status is unavailable."}`
      : repositoryElimActions.length
        ? `No confirmed human action is pending; ${repositoryElimActions.length} repository proposal${repositoryElimActions.length === 1 ? " awaits" : "s await"} Elim's recommendation.`
        : "No items currently await a human review or decision.";
    const automationItem = (item, humanOwned) => ({
      label: `${item.id || "Automation"}: ${item.stage || "run coordinator"} — ${item.summary || item.details || "Review the recorded failure."}`,
      href: item.source_url || "#automation:logs:incidents",
      route: String(item.source_url || "").replace(/^#/, "") || "automation:logs:incidents",
      owner: item.owners?.join(", ") || `Unassigned · recommended ${item.recommendedOwner || "owner unavailable"}`,
      status: humanOwned ? "Human resolution required" : humanizeKey(item.status || "Open"),
      tone: ["blocking", "disrupted"].includes(item.impact) ? "error" : "warning",
      question: item.recovery || (humanOwned
        ? "Complete the recorded next action and attach exact closure evidence."
        : "The accountable specialist must complete the recorded next action; unassigned ownership remains an oversight problem."),
      recommendation: humanOwned
        ? "Open the authoritative incident record, preserve every occurrence, and resolve only after its exact closure test passes."
        : "Open the authoritative incident record and correct its typed ownership or recovery state without inventing a browser disposition.",
      whyNow: `${pluralizeWord(item.occurrences || 1, "occurrence")} · latest ${item.lastSeen ? formatDate(item.lastSeen) : "time unavailable"}`,
      consequence: humanOwned
        ? "The affected run-chain work remains blocked or untrustworthy until repair and validation are recorded."
        : "The failure remains active but is not counted as a project-manager action until Human ownership is explicit.",
      due: item.firstSeen ? `Open since ${formatDate(item.firstSeen)}` : "First detection unavailable",
      blockingEffect: humanOwned && ["blocking", "disrupted"].includes(item.impact)
    });
    const groups = [
      {
        scope: "mine",
        label: "Security actions requiring you",
        target: "automation:security",
        status: "Human security action",
        tone: "error",
        detail: "A credential, secret, or other security action is explicitly assigned to you.",
        items: securityHumanActions.map(integrityActionLink)
      },
      {
        scope: "mine",
        label: "Integrity decisions requiring you",
        target: "integrity",
        status: "Human decision required",
        tone: "warning",
        detail: "A reserved human decision or approval is required.",
        items: integrityHumanFindings.map(integrityActionLink)
      },
      {
        scope: "mine",
        label: "Operational incidents requiring your action",
        target: "automation:logs:incidents",
        status: "Human resolution required",
        tone: "error",
        detail: "An unresolved host or run-chain failure requires explicit human resolution.",
        items: automationHumanActions.map((item) => automationItem(item, true))
      },
      {
        scope: "mine",
        label: "Human decisions",
        target: "actions",
        status: "Human decision needed",
        tone: "warning",
        detail: "A proposal or candidate is waiting for reserved human judgment.",
        items: decisionRecords.map((record) => ({
          label: `ACT-${record.identifier}: ${record.title}`,
          artifact_id: record.identifier,
          route: record.kind === "horizon"
            ? "planning:candidates"
            : record.workflowStatus === "Publication approval"
              ? "planning:publication"
              : "actions",
          canonicalUrl: record.url,
          owner: text(record.owner, "You / reserved human authority"),
          question: record.followUp || record.nextAction || `Decide the recorded next step for ${record.identifier}.`,
          recommendation: record.recommendation || "Review the evidence, options, and authority boundary in the owning dossier before recording a decision in the canonical record.",
          whyNow: `Workflow Status is ${record.workflowStatus}.`,
          consequence: record.consequence || "The record cannot advance to its next workflow state without the reserved decision.",
          due: record.dueDate ? formatDate(record.dueDate) : record.nextAudit ? `Next audit ${formatDate(record.nextAudit)}` : "No due trigger recorded",
          dueAt: record.dueDate || "",
          priority: record.priority || "",
          blockingEffect: record.releaseBlocker === true || explicitYes(record.releaseBlocker),
          consequentialDecision: Boolean(record.consequence)
        }))
      },
      {
        scope: "mine",
        label: "Repository decisions assigned to you",
        target: "automation:overview",
        openLabel: "Open specialist administration",
        status: "Exact-head decision",
        tone: "warning",
        detail: "A current repository recommendation assigns the decision to you.",
        items: repositoryHumanActions
      },
      {
        scope: "mine",
        label: "Preliminary candidates",
        target: "candidates:preliminary",
        status: "Intake review",
        tone: "warning",
        updated: true,
        detail: "A synthesized institutional question awaits human intake review.",
        items: data.records.map((record) => ({
          label: `ACT-${record.id}: ${record.title}`,
          artifact_id: record.id,
          href: "#candidates:preliminary",
          owner: "You",
          question: record.unresolved || "Admit, merge, defer, or reject this preliminary candidate.",
          recommendation: "Review its distinctness, coverage, counterargument, and evidence links before recording an intake disposition.",
          whyNow: `Preliminary intake candidate · ${termLabel(record.term)}`,
          consequence: "The question remains outside the formal portfolio and cannot enter issue development until disposition.",
          due: record.created_at ? `Created ${formatDate(record.created_at)}` : "Intake age unavailable"
        }))
      },
      {
        scope: "mine",
        label: "Pending source routing",
        target: "sources:pending",
        status: "Routing decision",
        tone: "info",
        detail: "A retained source still requires a choice among plausible project destinations.",
        items: data.pending_sources.map((record) => ({
          label: `ACT-${record.id}: ${record.title}`,
          record_ids: record.record_ids || [],
          href: "#sources:pending",
          owner: "You",
          question: `Choose the appropriate project destination${record.record_ids?.length ? ` among ${record.record_ids.join(", ")}` : ""}.`,
          recommendation: "Inspect provenance, proposition, candidate destinations, and monitoring relevance in Pending source routing.",
          whyNow: "The source is retained but not yet assigned to an authoritative project record.",
          consequence: "Evidence coverage and downstream monitoring remain incomplete until a destination is recorded.",
          due: record.date ? `Source dated ${formatDate(record.date)}` : "Routing age unavailable"
        }))
      },
      {
        scope: "oversight",
        label: "Security remediation owned by Elim",
        target: "automation:security",
        status: "Owned by Elim",
        tone: "error",
        detail: "Protected security-assurance work remains with Elim; details stay at the authorized source.",
        items: securityOversightActions.map(integrityActionLink)
      },
      {
        scope: "oversight",
        label: "Repository work owned by Elim",
        target: "automation:overview",
        status: "Owned by Elim",
        tone: "info",
        detail: pullRequestsKnown
          ? "An open repository proposal remains with Elim under an exact-head recommendation."
          : "Live pull-request heads are unavailable.",
        items: repositoryElimActions
      },
      {
        scope: "oversight",
        label: "Operational incidents under oversight",
        target: "automation:logs:incidents",
        status: "Owned elsewhere",
        tone: "error",
        detail: "An active incident family remains assigned outside the Human action queue.",
        items: automationOversightActions.map((item) => automationItem(item, false))
      },
      {
        scope: "oversight",
        label: "Integrity and readiness work owned elsewhere",
        target: "integrity",
        status: "Owned elsewhere",
        tone: "info",
        detail: "An open observation or remediation obligation is assigned to Elim, a bot, or another named owner.",
        items: oversightProblems.map(integrityActionLink)
      }
    ];
    actionInboxState.items = groups.flatMap((group) =>
      group.items.map((item, index) => actionInboxItem(group, item, index))
    );
    const blockingItems = actionInboxState.items.filter((item) => item.blockingEffect === true);
    setButtonBlockerFlag(
      "tab-actions",
      blockingItems.length > 0,
      `${pluralizeWord(blockingItems.length, "blocker")} represented in Action Items`
    );
    byId("all-actions-count").textContent = actionInboxState.items.length;
    renderPriorityAttention();
    renderActionInboxRows();
  }

  function parseCount(body, label) {
    const match = String(body || "").match(new RegExp(`${label}:\\s*\\*\\*(\\d+)\\*\\*`, "i"));
    return match ? Number(match[1]) : 0;
  }

  function completeProposalCount(body) {
    const match = String(body || "").match(/Affected records\s*\((\d+)\):/i);
    return match ? Number(match[1]) : 0;
  }

  function renderReviewSignals() {
    const botUpdates = reviewSignals.courts.count + reviewSignals.directives.count;
    setUpdateBadge("planning-preliminary-update", data.records.length);
    setUpdateBadge("candidate-preliminary-update", data.records.length);
    setUpdateBadge("planning-sources-update", botUpdates);
    setUpdateBadge("source-watchers-update", botUpdates);
    setUpdateBadge("court-watch-update", reviewSignals.courts.count);
    setUpdateBadge("directive-watch-update", reviewSignals.directives.count);
    if (!byId("panel-sources").hidden || loadedDomains.has("sources")) {
      renderWatcherUpdateBanner("courts", "source");
      renderWatcherUpdateBanner("directives", "directive");
      renderCourtWatch();
      renderDirectives();
    }
    if (!byId("panel-actions").hidden) renderActionItems();
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
      if (!Array.isArray(pullRequests)) throw new Error("GitHub returned an invalid pull-request list");
      const listIncomplete = hasNextLink(response.headers?.get?.("Link"));
      reviewSignals.pullRequests = pullRequests
        .filter((record) => record && Number.isInteger(record.number) && record.html_url)
        .sort((left, right) => right.number - left.number);
      reviewSignals.pullRequestsStatus = listIncomplete ? "incomplete" : "current";
      reviewSignals.pullRequestsCheckedAt = new Date().toISOString();
      const court = pullRequests.find((record) => record.head?.ref === "bot/case-monitor-updates");
      const directives = pullRequests.find((record) => record.head?.ref === "automation/presidential-directives-monitor");
      if (court) {
        const affected = exactWatcherAffected(court, "source_ids");
        reviewSignals.courts.count = affected.count ?? 0;
        reviewSignals.courts.totalCount = affected.totalCount ?? 0;
        reviewSignals.courts.proposalCount = affected.proposalCount ?? 0;
        reviewSignals.courts.url = court.html_url || "";
        reviewSignals.courts.ids = affected.ids;
        reviewSignals.courts.state = affected.valid ? "current" : "incomplete";
        reviewSignals.courts.reason = affected.reason;
      } else {
        reviewSignals.courts.count = 0;
        reviewSignals.courts.totalCount = 0;
        reviewSignals.courts.proposalCount = 0;
        reviewSignals.courts.url = "";
        reviewSignals.courts.ids = new Set();
        reviewSignals.courts.state = listIncomplete ? "incomplete" : "current";
        reviewSignals.courts.reason = listIncomplete ? "GitHub returned more than one page, so absence cannot be established from this response." : "";
      }
      if (directives) {
        const affected = exactWatcherAffected(directives, "directive_ids");
        reviewSignals.directives.count = affected.count ?? 0;
        reviewSignals.directives.totalCount = affected.totalCount ?? 0;
        reviewSignals.directives.proposalCount = affected.proposalCount ?? 0;
        reviewSignals.directives.ids = affected.ids;
        reviewSignals.directives.url = directives.html_url || "";
        reviewSignals.directives.state = affected.valid ? "current" : "incomplete";
        reviewSignals.directives.reason = affected.reason;
      } else {
        reviewSignals.directives.count = 0;
        reviewSignals.directives.totalCount = 0;
        reviewSignals.directives.proposalCount = 0;
        reviewSignals.directives.ids = new Set();
        reviewSignals.directives.url = "";
        reviewSignals.directives.state = listIncomplete ? "incomplete" : "current";
        reviewSignals.directives.reason = listIncomplete ? "GitHub returned more than one page, so absence cannot be established from this response." : "";
      }
      byId("action-items-live-note").textContent = listIncomplete
        ? "GitHub returned a paginated pull-request inventory, so live repository state is incomplete and no human actions are counted. The Action Inbox remains a nonauthoritative routing index."
        : "Live pull-request heads were refreshed from GitHub and matched against checked-in exact-head recommendations. The Action Inbox is a nonauthoritative routing index; specialist Console views and canonical records own status and disposition.";
      renderReviewSignals();
    } catch (_error) {
      reviewSignals.pullRequestsStatus = reviewSignals.pullRequests.length ? "stale" : "unavailable";
      reviewSignals.pullRequestsCheckedAt = new Date().toISOString();
      ["courts", "directives"].forEach((kind) => {
        reviewSignals[kind].state = "unavailable";
        reviewSignals[kind].reason = "Live pull-request heads could not be verified against a complete exact-head recommendation.";
        reviewSignals[kind].count = 0;
        reviewSignals[kind].ids = new Set();
      });
      courtWatchState.updatesOnly = false;
      directiveState.updatesOnly = false;
      byId("action-items-live-note").textContent = reviewSignals.pullRequests.length
        ? "Pull-request heads could not be refreshed; the last successful in-session recommendation match is shown as stale."
        : "Pull-request heads could not be refreshed, so checked-in recommendations are not counted as current human actions.";
      renderActionItems();
      if (loadedDomains.has("sources")) renderReviewSignals();
      renderOverview();
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
    const score = scorePresentation(record.score);
    identity.append(
      element("strong", "", record.identifier),
      workflow,
      element("span", score.valid ? "development-score" : "development-score invalid", score.label)
    );
    const links = element("div", "development-card-links");
    const workbenchTarget = workbenchTargetForArtifact(record.identifier, {
      source: "Progress",
      reference: record.identifier,
      returnTarget: "progress"
    });
    if (workbenchTarget) links.append(internalInlineLink("Open in Workbench", workbenchTarget));
    const liveUrl = proposalLiveUrl(record);
    if (liveUrl) links.append(linkButton("Live", liveUrl, true));
    if (record.url) links.append(linkButton("Issue", record.url, true));
    card.append(identity, links);
    return card;
  }

  function renderDevelopmentBoard(snapshot) {
    const proposals = Array.isArray(snapshot.proposals) ? snapshot.proposals : [];
    const candidates = candidateProjectRecords().map((record) => ({
      identifier: record.id,
      title: record.title,
      developmentLevel: record.development_level,
      workflowStatus: record.workflow_status,
      score: record.score,
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
    const items = Array.isArray(snapshot.pipeline?.items)
      ? snapshot.pipeline.items.filter((item) => item.mode === "hold")
      : [];
    const blocked = items.filter((item) => item.status === "Blocked").length;
    const deferred = items.filter((item) => item.status === "Deferred").length;
    byId("progress-holds-count").textContent = items.length;
    byId("progress-blocked-count").textContent = blocked;
    byId("progress-deferred-count").textContent = deferred;
  }

  function portfolioArchitecturePoints(snapshot) {
    const configured = snapshot.portfolioArchitecture || snapshot.portfolio_architecture;
    if (Array.isArray(configured) && configured.length) return configured;
    if (Array.isArray(configured?.steps) && configured.steps.length) return configured.steps;
    const baseline = snapshot.baseline || {};
    return [
      { label: "Original enumerated baseline", count: 204, reason: "Initial separately counted proposal architecture." },
      { label: "Scope reconciliation", count: 198, reason: "Eligibility and counting reconciliation." },
      { label: "Adopted consolidation", count: 77, reason: "Overlapping proposal records consolidated under the adopted portfolio review." },
      { label: "Current proposal scope", count: Number(snapshot.metrics?.total) || 81, reason: "Current eligible proposal denominator; candidates and delivery work are excluded." }
    ].filter((point, index, points) => index < points.length - 1 || point.count);
  }

  function renderPortfolioArchitecture(snapshot) {
    const architecture = snapshot.portfolioArchitecture || snapshot.portfolio_architecture || {};
    const points = portfolioArchitecturePoints(snapshot);
    byId("progress-portfolio-history").replaceChildren(...points.map((point, index) => {
      const count = Number(point.total ?? point.count ?? point.value);
      const previous = index ? Number(points[index - 1].count ?? points[index - 1].total ?? points[index - 1].value) : null;
      const card = element("article", "portfolio-history-card");
      card.append(
        element("span", "eyebrow", point.label || point.name || `Architecture point ${index + 1}`),
        element("strong", "", Number.isFinite(count) ? String(count) : "Unavailable"),
        element("p", "", point.reason_label || point.reason || point.explanation || "Reason not recorded"),
        element("span", "portfolio-delta", point.delta !== undefined && point.delta !== null
          ? `${Number(point.delta) >= 0 ? "+" : ""}${point.delta} separately counted proposals`
          : previous === null || !Number.isFinite(count)
            ? "Baseline"
            : `${count - previous >= 0 ? "+" : ""}${count - previous} separately counted proposals`)
      );
      return card;
    }));
    const readiness = architecture.earnedReadiness || architecture.earned_readiness
      || snapshot.earnedReadiness || snapshot.earned_readiness || {};
    const baselineReady = Number(readiness.baseline ?? readiness.from ?? snapshot.goal?.baselineReady ?? 23);
    const currentReady = Number(readiness.current ?? readiness.to ?? snapshot.metrics?.ready ?? 27);
    byId("progress-architecture-note").textContent = [
      architecture.explanation,
      `Portfolio count changes are architectural, not earned attainment. Earned Review Ready movement is ${baselineReady} → ${currentReady} (${currentReady - baselineReady >= 0 ? "+" : ""}${currentReady - baselineReady}) against the current ${Number(snapshot.metrics?.total) || 81}-proposal scope.`
    ].filter(Boolean).join(" ");
    const record = architecture.record;
    if (record) {
      byId("progress-consolidation-link").href = /^https?:/i.test(String(record))
        ? record
        : `${GITHUB_BLOB_ROOT}${String(record).replace(/^\.?\//, "")}`;
    }
  }

  function explicitYes(value) {
    return value === true || value === 1 || /^(?:yes|true|required|active|fired|blocked)$/i.test(String(value || "").trim());
  }

  function typedReleaseBlocker(value) {
    return value === true || /^(?:yes|true)$/i.test(String(value ?? "").trim());
  }

  function pipelineProjectionState() {
    const projection = data.progress?.pipeline;
    if (!projection || projection.schemaVersion !== 1) {
      return { available: false, reason: "No compatible typed Pipeline projection is available.", items: [], projection: {} };
    }
    const sourceCounts = projection.sourceCounts || {};
    const incompatible = (
      projection.progressGenerationId
      && data.progress?.generation_id
      && projection.progressGenerationId !== data.progress.generation_id
    ) || Number(sourceCounts.preliminaryCandidates) !== data.records.length
      || Number(sourceCounts.formalCandidates) !== data.active_horizon_records.length
      || Number(sourceCounts.proposals) !== (data.progress?.proposals || []).length;
    if (incompatible) {
      return { available: false, reason: "Pipeline inputs do not match the loaded candidate and Progress generation; rebuild the Console.", items: [], projection };
    }
    if (["stale", "unavailable"].includes(String(projection.availability || ""))) {
      return { available: false, reason: "The typed Pipeline projection is stale or unavailable and is not used for planning classification.", items: [], projection };
    }
    return {
      available: true,
      reason: "",
      items: Array.isArray(projection.items) ? projection.items : [],
      projection
    };
  }

  function resetPipelineMode(mode = pipelineState.mode) {
    Object.assign(pipelineState, {
      mode: mode === "hold" ? "hold" : "active",
      search: "",
      workClass: "all",
      scope: mode === "hold" ? "all" : "active-development",
      sort: "pipeline",
      status: "all",
      development: "all",
      area: "all",
      owner: "all",
      priority: "all",
      releaseBlocker: "all",
      gap: "all",
      selectedId: "",
      focused: false,
      sourceContext: "",
      sourceReference: "",
      returnTarget: ""
    });
  }

  function pipelineStatusMatches(record) {
    if (pipelineState.status === "all") return true;
    if (pipelineState.status === "Audit work") {
      return ["Audit needed", "Audit in progress"].includes(record.status);
    }
    return record.status === pipelineState.status;
  }

  function pipelineDefaultSort(left, right) {
    const leftSort = left.sortInputs || {};
    const rightSort = right.sortInputs || {};
    if (pipelineState.mode === "hold") {
      const now = Date.now();
      const holdRank = (record) => {
        const hold = record.hold || {};
        const due = parseTimestamp(hold.reviewDue);
        if (due !== null && due <= now) return [0, due];
        if (due !== null) return [1, due];
        if (!hold.lastReviewed) return [2, Infinity];
        return [3, Infinity];
      };
      const leftRank = holdRank(left);
      const rightRank = holdRank(right);
      return leftRank[0] - rightRank[0]
        || leftRank[1] - rightRank[1]
        || (parseTimestamp(left.hold?.holdSince) ?? Infinity) - (parseTimestamp(right.hold?.holdSince) ?? Infinity)
        || Number(leftSort.priorityRank ?? 99) - Number(rightSort.priorityRank ?? 99)
        || String(left.id).localeCompare(String(right.id));
    }
    return Number(leftSort.classRank ?? 99) - Number(rightSort.classRank ?? 99)
      || (
        left.workClass === "Proposal" && right.workClass === "Proposal"
          ? Number(leftSort.scoreDescending ?? Infinity) - Number(rightSort.scoreDescending ?? Infinity)
          : 0
      )
      || Number(Boolean(leftSort.nextStepMissing)) - Number(Boolean(rightSort.nextStepMissing))
      || Number(leftSort.priorityRank ?? 99) - Number(rightSort.priorityRank ?? 99)
      || (parseTimestamp(leftSort.dueDate) ?? Infinity) - (parseTimestamp(rightSort.dueDate) ?? Infinity)
      || String(left.id).localeCompare(String(right.id));
  }

  function pipelineSortRecords(left, right) {
    if (pipelineState.sort === "identifier") return String(left.id).localeCompare(String(right.id));
    if (pipelineState.sort === "priority") {
      return Number(left.sortInputs?.priorityRank ?? 99) - Number(right.sortInputs?.priorityRank ?? 99)
        || pipelineDefaultSort(left, right);
    }
    if (pipelineState.sort === "due") {
      const leftDue = pipelineState.mode === "hold" ? left.hold?.reviewDue : left.dueDate;
      const rightDue = pipelineState.mode === "hold" ? right.hold?.reviewDue : right.dueDate;
      return (parseTimestamp(leftDue) ?? Infinity) - (parseTimestamp(rightDue) ?? Infinity)
        || pipelineDefaultSort(left, right);
    }
    return pipelineDefaultSort(left, right);
  }

  function filteredPipelineItems(items = pipelineState.items) {
    const query = pipelineState.search.trim().toLowerCase();
    return items.filter((record) => {
      if (record.mode !== pipelineState.mode) return false;
      if (pipelineState.workClass !== "all" && record.workClass !== pipelineState.workClass) return false;
      if (pipelineState.mode === "active") {
        if (pipelineState.scope === "active-development" && record.readinessState === "ready") return false;
        if (pipelineState.scope === "review-ready" && record.readinessState !== "ready") return false;
      }
      if (!pipelineStatusMatches(record)) return false;
      if (pipelineState.development !== "all" && text(record.developmentLevel, "Unassigned") !== pipelineState.development) return false;
      if (pipelineState.area !== "all" && text(record.area, "Unassigned") !== pipelineState.area) return false;
      if (pipelineState.owner !== "all" && text(record.owner, "Unassigned") !== pipelineState.owner) return false;
      if (pipelineState.priority !== "all" && text(record.priority, "Unassigned") !== pipelineState.priority) return false;
      const releaseRequired = typedReleaseBlocker(record.releaseBlocker);
      if (pipelineState.releaseBlocker === "required" && !releaseRequired) return false;
      if (pipelineState.releaseBlocker === "not-required" && releaseRequired) return false;
      if (pipelineState.gap === "next_step_missing" && record.nextActionState !== "missing") return false;
      return !query || [
        record.id,
        record.title,
        record.workClass,
        record.status,
        record.nextAction,
        record.owner,
        record.area,
        record.hold?.reason,
        record.hold?.trigger
      ].filter(Boolean).join(" ").toLowerCase().includes(query);
    }).sort(pipelineSortRecords);
  }

  function pipelineRouteParameters() {
    const parameters = new URLSearchParams();
    if (pipelineState.mode !== "active") parameters.set("mode", pipelineState.mode);
    if (pipelineState.selectedId) parameters.set("selected", pipelineState.selectedId);
    const defaults = pipelineState.mode === "hold"
      ? { scope: "all" }
      : { scope: "active-development" };
    [
      ["work_class", "workClass", "all"],
      ["scope", "scope", defaults.scope],
      ["sort", "sort", "pipeline"],
      ["status", "status", "all"],
      ["development", "development", "all"],
      ["area", "area", "all"],
      ["owner", "owner", "all"],
      ["priority", "priority", "all"],
      ["release_blocker", "releaseBlocker", "all"]
    ].forEach(([parameter, key, defaultValue]) => {
      if (pipelineState[key] !== defaultValue) parameters.set(parameter, pipelineState[key]);
    });
    if (pipelineState.gap !== "all") parameters.set("gap", pipelineState.gap);
    if (pipelineState.search) parameters.set("search", pipelineState.search);
    if (pipelineState.focused) parameters.set("focus", "1");
    if (pipelineState.sourceContext) parameters.set("source", pipelineState.sourceContext);
    if (pipelineState.sourceReference) parameters.set("ref", pipelineState.sourceReference);
    if (pipelineState.returnTarget) parameters.set("return", pipelineState.returnTarget);
    return parameters.toString();
  }

  function updatePipelineRoute() {
    if (window.location.hash
      && !window.location.hash.startsWith("#planning:workbench:pipeline")) return;
    const parameters = pipelineRouteParameters();
    window.history.replaceState(null, "", `#planning:workbench:pipeline${parameters ? `:${parameters}` : ""}`);
  }

  function pipelineLink(label, route, external = false) {
    const link = element("a", external ? "record-link" : "record-link secondary", label);
    if (external) {
      const safeRoute = safePipelineExternalUrl(route);
      if (!safeRoute) {
        return element("span", "record-link unavailable", "Link unavailable");
      }
      const parsedRoute = new URL(safeRoute);
      link.href = "https://github.com/Thorncrag/ARRP/";
      link.pathname = parsedRoute.pathname;
      link.search = parsedRoute.search;
      link.hash = parsedRoute.hash;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    } else {
      const safeRoute = safeConsoleTarget(route);
      link.href = "#";
      link.hash = safeRoute;
      link.addEventListener("click", (event) => {
        event.preventDefault();
        navigateToConsoleTarget(safeRoute);
      });
    }
    return link;
  }

  function renderPipelinePreview(record) {
    const preview = byId("pipeline-preview");
    if (!record) {
      const empty = element("div", "pipeline-preview-empty");
      empty.append(
        element("span", "eyebrow", "Workbench preview"),
        element("h3", "", "No record selected"),
        element("p", "", "No artifacts match the current Workbench mode and filters.")
      );
      empty.querySelector("h3").id = "pipeline-preview-heading";
      preview.replaceChildren(empty);
      return;
    }
    const heading = element("h3", "", `${record.id}: ${text(record.title, "Untitled record")}`);
    heading.id = "pipeline-preview-heading";
    const header = element("header", "pipeline-preview-header");
    const badges = element("div", "pipeline-preview-badges");
    badges.append(
      element("span", "badge formal", record.workClass),
      element("span", "badge", text(record.status, "Status unavailable"))
    );
    if (record.workClass === "Proposal") {
      badges.append(element("span", "badge", scorePresentation(record.score).label));
    }
    header.append(element("span", "eyebrow", pipelineState.mode === "hold" ? "Hold artifact" : "Workbench artifact"), heading, badges);
    const sections = [];
    const add = (label, value, className = "") => {
      if (!value) return;
      const section = element("section", `pipeline-preview-section ${className}`.trim());
      section.append(element("h4", "", label), element("p", "", value));
      sections.push(section);
    };
    add("Why this record is here", record.membershipReason);
    add("Why it occupies this position", record.positionReason);
    if (record.mode === "hold") {
      const hold = record.hold || {};
      add("Hold reason", hold.reason || "Warning: required hold reason is not recorded.", hold.reason ? "" : "warning");
      if (record.status === "Blocked") {
        add("Blocked action", hold.blockedAction || "Not separately structured in the producer record.");
        add("Missing prerequisite", hold.missingPrerequisite || "Not separately structured in the producer record.");
      }
      add(record.status === "Blocked" ? "Unblock trigger" : "Reconsideration trigger", hold.trigger || "Warning: required trigger is not recorded.", hold.trigger ? "" : "warning");
      add("Hold since", hold.holdSince ? formatDate(hold.holdSince) : "Warning: no matching transition entry exists in the issue audit log.", hold.holdSince ? "" : "warning");
      add("Last reviewed", hold.lastReviewed ? formatDate(hold.lastReviewed) : "No later hold-review entry is recorded.");
      add("Review due", hold.reviewDue ? formatDate(hold.reviewDue) : "No explicit reconsideration date is recorded.");
      add("Audit provenance", hold.provenanceState === "verified" ? "Matched to the exact Status transition in the issue audit log." : "Warning: Project Status and audit transition provenance do not reconcile.", hold.provenanceState === "verified" ? "" : "warning");
    } else {
      add("Exact recorded next action", record.nextAction || "Next step not recorded", record.nextAction ? "" : "warning");
      add("Owner", text(record.owner, "Unassigned"));
      add("Development level and score", record.workClass === "Proposal"
        ? `${text(record.developmentLevel, "Unavailable")} · ${scorePresentation(record.score).label}`
        : `${text(record.developmentLevel, "Unavailable")} · Candidate score: Not applicable`);
      if ((record.readinessGaps || []).length) {
        add("Typed readiness gaps", record.readinessGaps.join(" "));
      }
      if (record.nextActionState === "missing") {
        add("Missing planning input", "The authoritative producer does not record an exact next step. The record remains visible after peers with complete next steps.", "warning");
      }
    }
    add("Area and workstream", [record.area, record.workstream].filter(Boolean).join(" · "));
    add("Priority and due date", [record.priority, record.dueDate ? formatDate(record.dueDate) : ""].filter(Boolean).join(" · ") || "No priority or due date recorded.");
    const links = element("div", "pipeline-preview-links");
    if (record.links?.dossier) links.append(pipelineLink("Open complete dossier", record.links.dossier));
    if (record.links?.issue) links.append(pipelineLink("Open GitHub issue ↗", record.links.issue, true));
    if (record.links?.canonical && record.links.canonical !== record.links.issue) {
      links.append(pipelineLink("Open canonical record ↗", record.links.canonical, true));
    }
    if (record.links?.audit) links.append(pipelineLink("Open audit transition ↗", record.links.audit, true));
    preview.replaceChildren(header, ...sections, links);
  }

  function pipelineRow(record) {
    const row = element("button", "pipeline-row");
    row.type = "button";
    row.dataset.pipelineId = record.id;
    row.setAttribute("role", "option");
    row.setAttribute("aria-selected", String(pipelineState.selectedId === record.id));
    row.tabIndex = pipelineState.selectedId === record.id ? 0 : -1;
    const title = element("span", "pipeline-row-title");
    title.append(element("strong", "", record.id), element("span", "", text(record.title, "Untitled record")));
    const score = record.workClass === "Proposal"
      ? ` · ${scorePresentation(record.score).label}`
      : "";
    const nextAction = record.nextAction || (
      record.mode === "hold"
        ? record.hold?.trigger || "Trigger not recorded"
        : "Next step not recorded"
    );
    const meta = element(
      "span",
      "pipeline-row-meta",
      `${record.workClass} · ${text(record.status, "Status unavailable")}${score} · ${nextAction}`
    );
    row.append(title, meta);
    row.addEventListener("click", () => selectPipelineItem(record.id, false, true));
    return row;
  }

  function selectPipelineItem(id, focus = false, updateRoute = false) {
    const record = pipelineState.items.find((item) => item.id === id);
    if (!record) return;
    pipelineState.selectedId = id;
    byId("pipeline-list").querySelectorAll(".pipeline-row").forEach((row) => {
      const selected = row.dataset.pipelineId === id;
      row.setAttribute("aria-selected", String(selected));
      row.tabIndex = selected ? 0 : -1;
    });
    renderPipelinePreview(record);
    if (focus) byId("pipeline-list").querySelector(`[data-pipeline-id="${CSS.escape(id)}"]`)?.focus();
    if (updateRoute) updatePipelineRoute();
  }

  function renderPipeline() {
    const projectionState = pipelineProjectionState();
    const projection = projectionState.projection || {};
    byId("pipeline-as-of").textContent = projection.asOf || "Unavailable";
    byId("pipeline-hold-mode-count").textContent = projection.counts?.blockedDeferred ?? 0;
    if (!projectionState.available) {
      pipelineState.items = [];
      byId("pipeline-data-note").textContent = projectionState.reason;
      byId("pipeline-list").replaceChildren(element("p", "empty-state compact-empty", "Pipeline classification is unavailable until the typed projection is rebuilt."));
      byId("pipeline-result-summary").textContent = "Projection unavailable";
      renderPipelinePreview(null);
      return;
    }
    pipelineState.items = projectionState.items;
    const workbenchBlockers = pipelineState.items.filter((item) =>
      !["Blocked", "Deferred"].includes(item.status)
      && typedReleaseBlocker(item.releaseBlocker)
    );
    setButtonBlockerFlag(
      "planning-tab-workbench",
      workbenchBlockers.length > 0,
      `${pluralizeWord(workbenchBlockers.length, "blocker")} represented in Workbench`
    );
    setButtonBlockerFlag(
      "tab-planning",
      workbenchBlockers.length > 0,
      "A blocker is represented in Planning"
    );
    const modeItems = pipelineState.items.filter((item) => item.mode === pipelineState.mode);
    const values = (key, fallback = "Unassigned") => [...new Set(modeItems.map((item) => text(item[key], fallback)))];
    populateSelect(byId("pipeline-work-class"), values("workClass"), "All work classes");
    populateSelect(byId("pipeline-status"), [...new Set(modeItems.map((item) => item.status).filter(Boolean))], "All statuses");
    populateSelect(byId("pipeline-development"), values("developmentLevel"), "All development levels");
    populateSelect(byId("pipeline-area"), values("area"), "All areas");
    populateSelect(byId("pipeline-owner"), values("owner"), "All owners");
    populateSelect(byId("pipeline-priority"), values("priority"), "All priorities");
    [
      ["pipeline-work-class", "workClass"],
      ["pipeline-scope", "scope"],
      ["pipeline-sort", "sort"],
      ["pipeline-status", "status"],
      ["pipeline-development", "development"],
      ["pipeline-area", "area"],
      ["pipeline-owner", "owner"],
      ["pipeline-priority", "priority"],
      ["pipeline-release-blocker", "releaseBlocker"]
    ].forEach(([id, key]) => {
      const select = byId(id);
      if ([...select.options].some((option) => option.value === pipelineState[key])) {
        select.value = pipelineState[key];
      } else {
        pipelineState[key] = id === "pipeline-scope" && pipelineState.mode === "hold" ? "all" : "all";
        select.value = pipelineState[key];
      }
    });
    byId("pipeline-scope").disabled = pipelineState.mode === "hold";
    byId("pipeline-search").value = pipelineState.search;
    document.querySelectorAll("[data-pipeline-mode]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.pipelineMode === pipelineState.mode));
    });
    const filtered = filteredPipelineItems();
    const focusedRecord = pipelineState.focused
      ? pipelineState.items.find((item) => item.id === pipelineState.selectedId)
      : null;
    const focusOutsideDefault = Boolean(
      focusedRecord && !filtered.some((item) => item.id === focusedRecord.id)
    );
    const displayed = focusOutsideDefault
      ? [focusedRecord, ...filtered]
      : filtered;
    if (!displayed.some((item) => item.id === pipelineState.selectedId)) {
      pipelineState.selectedId = displayed[0]?.id || "";
    }
    byId("pipeline-list").replaceChildren(...(displayed.length
      ? displayed.map(pipelineRow)
      : [element("p", "empty-state compact-empty", "No records match the current Pipeline mode and filters.")]));
    byId("pipeline-list-heading").textContent = pipelineState.mode === "hold"
      ? "Blocked & deferred"
      : "Active Pipeline";
    byId("pipeline-result-summary").textContent = `${filtered.length} of ${modeItems.length} records shown${focusOutsideDefault ? " · 1 contextual artifact added" : ""}`;
    const contextNotice = byId("workbench-context-notice");
    contextNotice.hidden = !focusedRecord;
    if (focusedRecord) {
      const source = pipelineState.sourceContext
        ? pipelineState.sourceContext.replaceAll("-", " ")
        : "a linked project screen";
      const reference = pipelineState.sourceReference
        ? ` ${pipelineState.sourceReference}`
        : "";
      byId("workbench-context-copy").textContent =
        `Opened from ${source}${reference}; ${focusOutsideDefault ? "outside the current Pipeline mode or filters" : "also represented in the current Pipeline view"}.`;
      const returnLink = byId("workbench-context-return");
      const returnTarget = safeConsoleTarget(pipelineState.returnTarget || "overview");
      returnLink.href = "#";
      returnLink.hash = returnTarget;
      returnLink.onclick = (event) => {
        event.preventDefault();
        navigateToConsoleTarget(returnTarget);
      };
      returnLink.textContent = `Return to ${source} →`;
    }
    const gaps = Array.isArray(projection.dataGaps) ? projection.dataGaps : [];
    byId("pipeline-gap-count").textContent = gaps.length;
    byId("pipeline-gap-notice").hidden = gaps.length === 0;
    const appliedAdvanced = ["status", "development", "area", "owner", "priority", "releaseBlocker"]
      .filter((key) => pipelineState[key] !== "all").length;
    byId("pipeline-advanced-summary").textContent = appliedAdvanced
      ? `${appliedAdvanced} applied`
      : "None applied";
    byId("pipeline-data-note").textContent =
      `Typed planning projection · ${projection.counts?.active ?? 0} active · ${projection.counts?.blockedDeferred ?? 0} blocked or deferred · browser classification disabled`;
    renderPipelinePreview(displayed.find((item) => item.id === pipelineState.selectedId));
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
      renderPortfolioArchitecture(snapshot);
      renderPipeline();
      return;
    }

    byId("progress-summary-grid").replaceChildren(
      progressMetric("Review Ready", metrics.ready, `of ${metrics.total} eligible proposals`),
      progressMetric("Remaining", metrics.remaining, `by ${goal.targetDate || "the target date"}`),
      progressMetric("Required pace", `${metrics.requiredPerWeek} / week`, "to meet the official target"),
      progressMetric("Rolling pace", metrics.rollingWeeklyVelocity == null ? "Establishing" : `${metrics.rollingWeeklyVelocity} / week`, "net Review Ready attainment"),
      progressMetric("Forecast for current scope", metrics.forecastLabel || "Establishing", metrics.trackStatus || "Schedule status unavailable")
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
    renderPortfolioArchitecture(snapshot);
    renderPipeline();

    const areaRows = [...areas].sort((left, right) => right.remaining - left.remaining || left.area.localeCompare(right.area));
    byId("progress-area-list").replaceChildren(...areaRows.map((area) => {
      const row = element("a", "progress-area-row");
      row.href = `#planning:workbench:pipeline:area=${encodeURIComponent(area.area)}`;
      row.setAttribute("aria-label", `Open ${area.area} artifacts in Workbench`);
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
    card.href = target.startsWith("http") ? target : `#${target}`;
    if (target.startsWith("http")) {
      card.target = "_blank";
      card.rel = "noopener noreferrer";
    }
    card.append(element("span", "eyebrow", label), element("strong", "", String(value)), element("p", "", detail));
    return card;
  }

  function projectionStatusCard(label, feed, target, fallbackTimestamp = "") {
    const contract = feedContractState(feed || {}, fallbackTimestamp);
    const card = element("a", `freshness-card overview-card ${contract.state}`);
    card.dataset.layoutId = `freshness-${layoutSlug(label)}`;
    card.href = `#${target}`;
    const countDetail = contract.expected !== null
      ? `${contract.actual ?? "—"} of ${contract.expected} expected`
      : "";
    card.append(
      element("strong", "", label),
      element("p", "", contract.label),
      element("time", "", contract.timestamp ? formatDate(contract.timestamp) : "Producer timestamp unavailable"),
      ...(countDetail ? [element("span", "micro-note", countDetail)] : [])
    );
    card.title = contract.reason || contract.label;
    return card;
  }

  function dateTimestamp(value) {
    if (!value) return 0;
    const direct = parseTimestamp(value);
    if (direct !== null) return direct;
    const matches = String(value).match(/\d{4}-\d{2}-\d{2}(?:[T ][0-9:.]+(?:Z| ?[+-]\d{2}:?\d{2})?)?/g) || [];
    for (const candidate of matches.reverse()) {
      const parsed = parseTimestamp(candidate);
      if (parsed !== null) return parsed;
    }
    return 0;
  }

  function overviewDisplayDate(value) {
    const matches = String(value || "").match(/\d{4}-\d{2}-\d{2}(?:[T ][0-9:.]+(?:Z| ?[+-]\d{2}:?\d{2})?)?/g) || [];
    const candidate = matches[matches.length - 1] || value;
    if (/^\d{4}-\d{2}-\d{2}$/.test(String(candidate || ""))) {
      const parsed = new Date(`${candidate}T12:00:00`);
      return Number.isNaN(parsed.valueOf())
        ? String(candidate)
        : new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(parsed);
    }
    return formatDate(candidate);
  }

  function agePosture(value) {
    const timestamp = dateTimestamp(value);
    if (!timestamp) return "No timestamp";
    const hours = Math.max(0, (Date.now() - timestamp) / 3600000);
    if (hours < 1) return "Within the hour";
    if (hours < 24) return `${Math.round(hours)}h old`;
    return `${Math.round(hours / 24)}d old`;
  }

  function effectiveRunChainStatus(chain) {
    const raw = String(chain.host_status || chain.status || chain.outcome || "");
    const launchRecommended = chain.elim_decision?.launch_recommended === true
      || chain.elim?.launch_recommended === true;
    const currentRuntime = matchingElimRuntime(chain.elim_runtime, chain.chain_id);
    if (/^complete$/i.test(raw) && launchRecommended && !currentRuntime && !chain.host_status) return "host_pending";
    return raw || (runChainStages(chain).length ? "in_progress" : "unavailable");
  }

  function overviewStagePresentation(status) {
    const value = String(status || "unavailable").toLowerCase().replaceAll(" ", "_");
    if (value === "major_outage") return { icon: "×", statusLabel: "Major Outage", tone: "error" };
    if (value === "partial_outage") return { icon: "!", statusLabel: "Partial Outage", tone: "warning" };
    if (value === "degraded_performance") return { icon: "!", statusLabel: "Degraded Performance", tone: "warning" };
    if (value === "under_maintenance") return { icon: "!", statusLabel: "Under Maintenance", tone: "warning" };
    if (/fail|error|block|cancel|timeout/.test(value)) {
      const statusLabel = /block/.test(value)
        ? "Blocked"
        : /timeout/.test(value)
          ? "Timed out"
          : /cancel/.test(value)
            ? "Cancelled"
            : "Failed";
      return { icon: "×", statusLabel, tone: "error" };
    }
    if (/degrad|warn|partial/.test(value)) return { icon: "!", statusLabel: serviceStatusLabel(value), tone: "warning" };
    if (/pending|progress|recommended|stopp/.test(value)) return { icon: "◌", statusLabel: serviceStatusLabel(value), tone: "warning" };
    if (/success|succeed|pass/.test(value)) return { icon: "✓", statusLabel: "Succeeded", tone: "success" };
    if (/complete|healthy/.test(value)) return { icon: "✓", statusLabel: "Succeeded", tone: "success" };
    if (/operational/.test(value)) return { icon: "✓", statusLabel: "Operational", tone: "success" };
    if (/not_due|no.?op|current/.test(value)) return { icon: "—", statusLabel: "Not due this chain", tone: "not-due" };
    return { icon: "○", statusLabel: serviceStatusLabel(value), tone: "unavailable" };
  }

  function stageExecutionPresentation(stage = {}) {
    const rawStatus = stage.status || (stage.due === false ? "not_due" : "unavailable");
    const isNotDue = /^(?:not_due|not due|no.?op)$/i.test(String(rawStatus));
    const lastSuccessAt = stage.last_success_at || stage.last_success || stage.last_succeeded_at;
    const explicitCurrentChainLabel = stage.current_chain_label || stage.currentChainLabel;
    if (isNotDue && lastSuccessAt) {
      return {
        rawStatus,
        currentChainLabel: explicitCurrentChainLabel || "Not due this chain",
        lastSuccessAt,
        scheduleDetail: stage.due_reason || "The latest successful result remains current.",
        ...overviewStagePresentation("succeeded")
      };
    }
    return {
      rawStatus,
      currentChainLabel: explicitCurrentChainLabel
        || (isNotDue ? "Not due this chain" : serviceStatusLabel(rawStatus)),
      lastSuccessAt,
      scheduleDetail: stage.due_reason || stage.details || "",
      ...overviewStagePresentation(rawStatus)
    };
  }

  function overviewRunChainStages(chain) {
    const stages = new Map(runChainStages(chain).map((stage) => [stage.id, stage]));
    const stageForAgent = (id) => {
      const record = data.agent_registry.find((agent) => agent.id === id);
      return record ? agentCurrentStage(record, chain) : stages.get(id) || {};
    };
    const runtime = matchingElimRuntime(chain.elim_runtime, chain.chain_id);
    const launchRecommended = chain.elim_decision?.launch_recommended === true
      || chain.elim?.launch_recommended === true;
    const elimStatus = runtime?.status
      || (launchRecommended ? "launch recommended" : chain.elim_decision ? "not due" : "not launched");
    const specs = [
      ["case-monitor-bot", "Cases", stageForAgent("case-monitor-bot")],
      ["presidential-directives-bot", "Presidential directives", stageForAgent("presidential-directives-bot")],
      ["source-checker-bot", "Sources", stageForAgent("source-checker-bot")],
      ["public-intake", "Public input", stages.get("public-intake") || {}],
      ["project-console-progress-bot", "Progress", stageForAgent("project-console-progress-bot")],
      ["project-integrity-bot", "Integrity", stageForAgent("project-integrity-bot")],
      ["elim", "Elim", { ...(runtime || {}), status: elimStatus, details: runtime?.summary || chain.elim_decision?.reason || "No host Elim result is attached to this chain" }]
    ];
    return specs.map(([id, label, stage]) => {
      const presentation = stageExecutionPresentation(stage);
      const scheduling = presentation.currentChainLabel === "Not due this chain"
        ? `${presentation.currentChainLabel}${presentation.scheduleDetail ? ` · ${presentation.scheduleDetail}` : ""}`
        : "";
      return {
        id,
        label,
        status: presentation.rawStatus || "unavailable",
        detail: scheduling || stage.details || stage.due_reason || "No detail recorded",
        completedAt: stage.completed_at || stage.updated_at || presentation.lastSuccessAt,
        activeIncidentIds: Array.isArray(stage.active_incident_ids)
          ? stage.active_incident_ids
          : [],
        ...presentation
      };
    });
  }

  function agentCurrentStage(record, chain = data.run_chain || {}) {
    if (record.id === "run-coordinator-bot") {
      const status = effectiveRunChainStatus(chain);
      return {
        id: record.id,
        status,
        completed_at: chain.host_updated_at || chain.completed_at || chain.updated_at,
        last_success_at: /success|succeed|complete|healthy/i.test(status)
          ? chain.host_updated_at || chain.completed_at || chain.updated_at
          : null,
        details: chain.host_closeout?.details || chain.next_action || "No coordinator closeout detail is recorded."
      };
    }
    if (record.id === "elim") {
      const runtime = matchingElimRuntime(chain.elim_runtime, chain.chain_id);
      if (runtime) return { id: record.id, ...runtime };
      const entry = latestLogEntry("elim");
      return entry
        ? {
            id: record.id,
            status: entry.values?.outcome || "completed",
            completed_at: entry.values?.date,
            last_success_at: /fail|error|block|cancel/i.test(entry.values?.outcome || "")
              ? null
              : entry.values?.date,
            details: entry.values?.summary || "Open the Elim log for the complete run report."
          }
        : { id: record.id, status: "unavailable", details: "No Elim run is recorded." };
    }
    const current = runChainStages(chain).find((stage) => stage.id === record.id);
    const historical = successfulStageHistory.get(record.id);
    if (current) {
      const currentStatus = String(current.status || "");
      if (historical && !current.last_success_at && /not.?due|no.?op/i.test(currentStatus)) {
        return {
          ...current,
          last_success_at: historical.last_success_at
        };
      }
      return current;
    }
    if (historical) {
      return {
        ...historical,
        id: record.id,
        status: "succeeded",
        current_chain_label: "Not reached this chain",
        details: "The latest successful execution remains recorded; the current chain did not reach this stage."
      };
    }
    return { id: record.id, status: "unavailable", details: "No successful execution or current run-chain stage is published." };
  }

  function renderOverviewAutomationActivity(
    chain = data.run_chain || {},
    readiness = data.overview?.automation_readiness || {}
  ) {
    const stages = overviewRunChainStages(chain);
    const latestAttempt = readiness.latest_attempt || {};
    const blockers = Array.isArray(latestAttempt.blockers)
      ? latestAttempt.blockers
      : [];
    byId("overview-automation-activity-grid").replaceChildren(...stages.map((stage, index) => {
      const stageBlockers = blockers.filter((blocker) => blocker.stage_id === stage.id);
      const tone = stageBlockers.length ? "error" : stage.tone;
      const statusLabel = stageBlockers.length ? "Blocked" : stage.statusLabel;
      const card = element("a", `overview-automation-card ${tone}`.trim());
      card.dataset.layoutId = `overview-stage-${index + 1}`;
      card.href = "#automation:overview";
      card.append(
        element("span", "overview-stage-number", `Stage ${index + 1}`),
        element("h4", "", stage.label),
        element("span", `status-badge ${tone}`, statusLabel),
        element(
          "time",
          "overview-stage-time",
          formatDate(
            stage.lastSuccessAt
              || stage.completedAt
              || chain.updated_at
          )
        )
      );
      if (stageBlockers.length) {
        card.append(element(
          "p",
          "overview-stage-reason",
          stageBlockers.map((blocker) => blocker.reason).join(" · ")
        ));
      } else if (stage.tone === "error" || stage.tone === "warning") {
        card.append(element("p", "overview-stage-reason", stage.detail));
      }
      if (stage.activeIncidentIds.length) {
        card.append(element(
          "p",
          "overview-stage-reason",
          `Incident ${stage.activeIncidentIds.join(", ")}`
        ));
      }
      card.setAttribute(
        "aria-label",
        `Stage ${index + 1}, ${stage.label}: ${statusLabel}. Open complete run-chain detail.`
      );
      return card;
    }));
    const futureGates = readiness.future_run_gates || {};
    const unassignedBlockers = blockers.filter((blocker) =>
      !stages.some((stage) => stage.id === blocker.stage_id));
    const latestLabel = latestAttempt.available === true
      ? unassignedBlockers.length
        ? `Latest-attempt blockers: ${unassignedBlockers.length} chain-level`
        : `Latest-attempt blockers: ${Number(latestAttempt.blocker_count || 0)}`
      : "Latest-attempt blockers: unavailable";
    const gatesLabel = futureGates.available === true
      ? `Future-run gates: ${Number(futureGates.count || 0)} open`
      : "Future-run gates: unavailable";
    const readinessLink = byId("overview-chain-readiness");
    readinessLink.textContent = `${latestLabel} · ${gatesLabel}`;
    readinessLink.className = `overview-chain-readiness ${
      latestAttempt.available !== true || futureGates.available !== true
        ? "unavailable"
        : Number(latestAttempt.blocker_count || 0) || Number(futureGates.count || 0)
          ? "error"
          : "success"
    }`;
    readinessLink.title = [
      latestAttempt.reason,
      futureGates.reason,
      ...unassignedBlockers.map((blocker) => blocker.reason)
    ].filter(Boolean).join(" · ");
  }

  function projectLog(logId) {
    return data.project_logs.find((log) => log.id === logId);
  }

  function latestLogEntry(logId) {
    const log = projectLog(logId);
    return [...(log?.entries || [])].sort((left, right) =>
      dateTimestamp(right.values?.date) - dateTimestamp(left.values?.date))[0] || null;
  }

  function elimUsageConsumption(entry) {
    const usage = String(entry?.values?.usage || "");
    const patterns = [
      /highest valid consumption was\s+(\d+(?:\.\d+)?)\s+percentage points?/i,
      /(\d+(?:\.\d+)?)\s+percentage points?\s+as (?:the )?highest consumption/i,
      /for\s+(\d+(?:\.\d+)?)\s+percentage points? consumed/i,
      /for\s+(\d+(?:\.\d+)?)\s+recorded percentage points? consumed/i,
      /(\d+(?:\.\d+)?)\s+percentage points? consumed/i
    ];
    for (const pattern of patterns) {
      const match = usage.match(pattern);
      if (match) return Number(match[1]);
    }
    return null;
  }

  function elimImprovementRecords(entry) {
    const summary = String(entry?.values?.summary || "");
    if (!summary || /preflight only|did not begin|no .* (?:change|completed|performed)|no substantive/i.test(summary)) return [];
    const identifiers = [...new Set(summary.match(/\b(?:HOR|[A-Z]{2,})-\d{3}\b/g) || [])];
    const sentences = summary.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [summary];
    const scoreMatch = summary.match(/\b(?:at|to)\s+(\d{1,3})\/100\b/i);
    const deltaMatch = summary.match(/\bfrom\s+(\d{1,3})(?:\/100)?\s+to\s+(\d{1,3})\/100\b/i);
    return identifiers.map((identifier) => {
      const record = currentLifecycleRecords().find((candidate) => candidate.identifier === identifier);
      const impact = sentences
        .filter((sentence) => sentence.includes(identifier))
        .slice(0, 2)
        .join(" ")
        .trim() || "The run summary identifies this record but does not isolate its impact.";
      let score = "Score effect not recorded";
      if (/no score|score .* unchanged|preserved .* score/i.test(summary)) score = "Score unchanged";
      else if (deltaMatch && identifiers.length === 1) score = `Score ${deltaMatch[1]} → ${deltaMatch[2]} (${Number(deltaMatch[2]) - Number(deltaMatch[1]) >= 0 ? "+" : ""}${Number(deltaMatch[2]) - Number(deltaMatch[1])})`;
      else if (scoreMatch && identifiers.length === 1) score = `Score ${scoreMatch[1]} · change not separately recorded`;
      else {
        const currentScore = scorePresentation(record?.score);
        if (currentScore.available && currentScore.valid) {
          score = `Current score ${currentScore.value} · run delta not recorded`;
        }
      }
      return { identifier, impact, score, href: record?.canonicalRecord ? `${GITHUB_BLOB_ROOT}${record.canonicalRecord}` : record?.url };
    });
  }

  function overviewLogRow({ title, meta, summary, target, tone = "" }) {
    const row = element("details", `overview-expandable-row ${tone}`.trim());
    row.dataset.disclosureId = `overview-log-${layoutSlug(`${target}-${title}`)}`;
    const heading = element("summary", "");
    heading.append(element("strong", "", title), element("span", "overview-row-meta", meta));
    const body = element("div", "overview-row-body");
    body.append(element("p", "", summary || "No summary recorded."));
    const link = element("a", "record-link secondary compact-link", "Open complete record →");
    link.href = `#${target}`;
    body.append(link);
    row.append(heading, body);
    return row;
  }

  function compactActivityPresentation(activity = {}) {
    const logLabels = {
      agents: "Agents & Bots",
      elim: "Elim",
      horizon: "Horizon",
      "source-monitor": "Source monitoring",
      integrity: "Integrity",
      changes: "Change Audit"
    };
    const actor = activity.actor || logLabels[activity.log] || activity.source || "Project activity";
    const headline = activity.record || activity.label || activity.outcome || activity.id || "Activity";
    const title = activity.title || `${actor} · ${headline}`;
    const source = activity.source || logLabels[activity.log] || activity.kind || "Overview projection";
    const occurredAt = activity.at || activity.date || activity.generated_at;
    const outcome = activity.outcome || activity.result;
    const affected = activity.affected_scope || activity.affected || activity.affected_count;
    const detail = activity.summary || activity.detail || activity.label;
    const managerEffect = activity.manager_effect || activity.manager_action || activity.next_action;
    const owner = activity.owner;
    const labeledSentence = (label, value) => {
      const rendered = String(value ?? "").trim();
      if (!rendered) return "";
      return `${label}: ${rendered}${/[.!?]$/.test(rendered) ? "" : "."}`;
    };
    const summary = [
      labeledSentence("Outcome", outcome),
      affected !== undefined && affected !== null && String(affected).trim()
        ? labeledSentence("Affected", affected)
        : "",
      detail || "",
      labeledSentence("Manager effect", managerEffect || "No manager action recorded"),
      labeledSentence("Owner", owner)
    ].filter(Boolean).join(" ");
    const outcomeText = `${outcome || ""} ${activity.tone || ""} ${activity.severity || ""}`;
    const tone = activity.tone
      || activity.severity
      || (/fail|error|block/i.test(outcomeText)
        ? "error"
        : /warn|attention|recommendation/i.test(outcomeText)
          ? "warning"
          : "");
    return {
      title,
      meta: `${source} · ${overviewDisplayDate(occurredAt)}`,
      summary: summary || "No summary recorded.",
      target: String(activity.route || activity.target || "logs").replace(/^#/, ""),
      tone
    };
  }

  function logEntryHeadline(log, entry) {
    const values = entry.values || {};
    if (log.id === "elim") return values.outcome || entry.id;
    if (log.id === "agents") return `${values.record || "Project"} · ${values.task || "agent activity"}`;
    if (log.id === "source-monitor") return `${values.watcher || "Source monitor"} · ${String(values.result || "result").replaceAll("_", " ")}`;
    if (log.id === "changes") return values.change || entry.id;
    if (log.id === "console-development") return values.category || values.change || entry.id;
    return `${values.record || entry.id} · ${values.disposition || "decision"}`;
  }

  function logEntrySummary(log, entry) {
    const values = entry.values || {};
    if (log.id === "elim") return values.summary;
    if (log.id === "agents") return `${values.agent || "Agent"} recorded ${values.outcome || "an outcome"} for run ${values.run || "not identified"}.`;
    if (log.id === "source-monitor") return `Affected: ${values.affected || "not recorded"} · Activity: ${values.activity || "not recorded"}.`;
    if (log.id === "changes") return `${values.scope || ""} ${values.effect || ""}`.trim();
    if (log.id === "console-development") return `${values.change || "Change ID unavailable"} · ${values.lifecycle || "Changed"} · ${values.state || "state unavailable"}`;
    return values.destination || values.disposition;
  }

  function renderOverviewRecentActivity() {
    const activity = Array.isArray(data.overview?.activity) ? data.overview.activity.slice(0, 8) : [];
    const rows = activity.map((record) => {
      const target = String(record.route || record.target || "logs").replace(/^#/, "");
      const row = element("a", "overview-material-row");
      row.href = target.startsWith("http") ? target : `#${target}`;
      const rawArtifact = text(record.affected_scope || record.title || record.id, "Project artifact");
      const affectedItems = String(record.affected_scope || "").split(",").map((item) => item.trim()).filter(Boolean);
      const artifact = rawArtifact.length > 96 && affectedItems.length > 1
        ? `${affectedItems.length} touched artifacts`
        : rawArtifact;
      const descriptor = text(
        record.score_change
          || record.delta
          || record.outcome
          || record.summary,
        "Change recorded"
      );
      row.append(
        element("strong", "", artifact),
        element("span", "overview-material-change", descriptor),
        element("time", "", overviewDisplayDate(record.date || record.recorded_at))
      );
      return row;
    });
    byId("overview-recent-actions").replaceChildren(...(rows.length
      ? rows
      : [element("p", "empty-state compact-empty", "No recent material artifact changes are recorded.")]));
  }

  function publicInputSnapshot(chain = data.run_chain || {}) {
    const stage = runChainStages(chain).find((record) => record.id === "public-intake");
    if (stage && Number.isFinite(Number(stage.work_count))) {
      return {
        count: Number(stage.work_count),
        available: true,
        checkedAt: stage.completed_at || chain.updated_at,
        detail: stage.work_count ? "eligible public submissions awaiting Elim triage" : "latest intake check found no eligible submission"
      };
    }
    if (chain.queue_counts && Object.prototype.hasOwnProperty.call(chain.queue_counts, "intake")) {
      return {
        count: runChainCount(chain.queue_counts, "intake"),
        available: true,
        checkedAt: chain.updated_at,
        detail: "published run-chain intake count"
      };
    }
    return { count: null, available: false, checkedAt: null, detail: "no current intake count is published" };
  }

  function renderOverviewPortals(snapshot, chain) {
    const intake = publicInputSnapshot(chain);
    const humanActionCount = data.overview?.queue_counts?.human_actions ?? snapshot.total;
    const makeCard = (title, value, detail, target, tone = "") => {
      const card = element("article", `overview-indicator-card ${tone}`.trim());
      card.dataset.layoutId = `overview-portlet-${layoutSlug(title)}`;
      card.dataset.layoutTransferGroup = "overview-portlet";
      const heading = element("div", "overview-card-heading");
      heading.append(element("h4", "", title));
      if (tone) heading.append(element("span", `status-badge ${tone}`, serviceStatusLabel(tone)));
      const link = internalInlineLink("View details →", target);
      link.className = "overview-indicator-link";
      card.append(
        heading,
        element("strong", "overview-indicator-value", value),
        element("p", "overview-indicator-detail", detail),
        link
      );
      return card;
    };
    const publicCard = makeCard(
      "Public intake",
      intake.available ? `${intake.count} unresolved` : "Unavailable",
      `${intake.detail}${intake.checkedAt ? ` · checked ${formatOperationalDate(intake.checkedAt)}` : ""}`,
      "planning:preliminary",
      intake.available && intake.count ? "notice" : intake.available ? "" : "unavailable"
    );
    const humanCard = makeCard(
      "Human action items",
      `${humanActionCount} unresolved`,
      `${snapshot.decisions} decisions · ${snapshot.repositoryHumanActions.length} repository reviews · ${snapshot.automationHumanActions.length} technical interventions`,
      "actions",
      humanActionCount ? "notice" : "success"
    );
    const capacityCard = element("article", "overview-indicator-card overview-capacity-indicator");
    capacityCard.dataset.layoutId = "overview-portlet-codex-capacity";
    capacityCard.dataset.layoutTransferGroup = "overview-portlet";
    capacityCard.append(
      element("div", "overview-card-heading", ""),
      internalInlineLink("View capacity →", "automation:capacity")
    );
    capacityCard.firstChild.append(
      element("h4", "", "Codex capacity"),
      byId("overview-usage-posture")
    );
    capacityCard.insertBefore(byId("overview-usage-summary"), capacityCard.lastChild);
    capacityCard.insertBefore(byId("overview-usage-trend"), capacityCard.lastChild);

    const platformCard = element("article", "overview-indicator-card overview-compact-indicator overview-platform-indicator");
    platformCard.dataset.layoutId = "overview-portlet-platform-status";
    platformCard.dataset.layoutTransferGroup = "overview-portlet";
    const platformHeading = element("div", "overview-card-heading");
    platformHeading.append(element("h4", "", "Platform status"));
    platformCard.append(
      platformHeading,
      byId("overview-openai-status"),
      byId("overview-openai-checked"),
      internalInlineLink("View platform status →", "automation:platform")
    );

    const dataCard = element("article", "overview-indicator-card overview-compact-indicator");
    dataCard.dataset.layoutId = "overview-portlet-project-data";
    dataCard.dataset.layoutTransferGroup = "overview-portlet";
    const dataHeading = element("div", "overview-card-heading");
    const progressFeed = Object.keys(data.progress || {}).length ? data.progress : data.overview?.progress_summary;
    const sourceFeed = Object.keys(data.source_checker || {}).length ? data.source_checker : data.overview?.source_checker_summary;
    const integrityFeed = Object.keys(data.integrity || {}).length ? data.integrity : data.overview?.integrity_summary;
    const feedSpecs = [
      ["Progress", progressFeed, progressFeed?.generated_at || progressFeed?.generatedAt],
      ["Sources", sourceFeed, sourceFeed?.checked_at],
      ["Chain", chain, chain.updated_at || chain.completed_at],
      ["Candidates", { availability: "current", completeness: { complete: true } }, data.generated_at],
      ["Public input", { availability: intake.available ? "current" : "unavailable" }, intake.checkedAt],
      ["Integrity", integrityFeed, integrityFeed?.current?.generated_at || integrityFeed?.generated_at]
    ];
    const feedStates = feedSpecs.map(([label, feed, timestamp]) => ({
      label,
      state: feedContractState(feed || {}, timestamp)
    }));
    const problemFeeds = feedStates.filter(({ state }) =>
      !state.complete || state.state === "stale");
    dataHeading.append(
      element("h4", "", "Project data"),
      element(
        "span",
        `status-badge ${problemFeeds.length ? "warning" : "success"}`,
        problemFeeds.length ? "Problem" : "Current"
      )
    );
    const dataGrid = element("div", "overview-status-grid");
    dataGrid.append(...feedStates.map(({ label, state }) => {
      const tone = state.complete && state.state !== "stale"
        ? "success"
        : state.state === "unavailable"
          ? "unavailable"
          : "error";
      const cell = element("div", "overview-status-cell");
      cell.setAttribute("aria-label", `${label}: ${state.label}`);
      cell.title = state.reason || state.label;
      cell.append(element("span", `health-dot ${tone}`, ""), element("strong", "", label));
      return cell;
    }));
    const dataLink = internalInlineLink(
      problemFeeds.length ? `View ${pluralizeWord(problemFeeds.length, "data problem")} →` : "View data status →",
      "automation:data"
    );
    dataCard.append(dataHeading, dataGrid, dataLink);
    [capacityCard, platformCard, dataCard].forEach((card) => {
      card.lastChild.className = "overview-indicator-link";
    });
    const cards = [publicCard, humanCard, capacityCard, platformCard, dataCard];
    document.querySelectorAll('[data-layout-transfer-group="overview-portlet"]')
      .forEach((card) => card.remove());
    byId("overview-portals").replaceChildren(...cards);
  }

  function serviceStatusLabel(status) {
    return String(status || "unavailable")
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function platformStatusRank(status) {
    return {
      operational: 1,
      under_maintenance: 2,
      degraded_performance: 3,
      partial_outage: 4,
      major_outage: 5
    }[status] || 99;
  }

  function platformStatusPresentation(status) {
    if (status === "operational") return { tone: "success", label: "Operational" };
    if (["under_maintenance", "degraded_performance"].includes(status)) {
      return { tone: "warning", label: serviceStatusLabel(status) };
    }
    if (["partial_outage", "major_outage"].includes(status)) {
      return { tone: "error", label: serviceStatusLabel(status) };
    }
    return { tone: "unavailable", label: "Unavailable" };
  }

  function worstPlatformStatus(components) {
    if (!components.length) return "unavailable";
    return [...components]
      .sort((left, right) => platformStatusRank(right.status) - platformStatusRank(left.status))[0]
      ?.status || "unavailable";
  }

  function relevantPlatformIncidents(incidents, componentIds) {
    const relevantIds = new Set(componentIds);
    return (Array.isArray(incidents) ? incidents : []).filter((incident) => {
      const linked = Array.isArray(incident?.components) ? incident.components : [];
      return linked.some((component) => relevantIds.has(String(component?.id || component)));
    }).map((incident) => ({
      id: incident.id,
      name: incident.name,
      status: incident.status,
      impact: incident.impact,
      shortlink: incident.shortlink || null,
      updatedAt: incident.updated_at || null
    }));
  }

  function platformProviderObservation(providerId, componentPayload, incidentPayload, checkedAt, previous = null) {
    const spec = PLATFORM_PROVIDER_SPECS[providerId];
    const components = Array.isArray(componentPayload?.components) ? componentPayload.components : null;
    const incidents = Array.isArray(incidentPayload?.incidents) ? incidentPayload.incidents : [];
    const unavailable = (reason) => ({
      providerId,
      provider: spec?.label || providerId,
      source: spec?.source || "",
      availability: "unavailable",
      complete: false,
      checkedAt,
      aggregate: "unavailable",
      components: [],
      incidents: [],
      reason,
      lastValid: previous?.complete ? previous : previous?.lastValid || null
    });
    if (!spec || !components) return unavailable("The official component feed was unavailable or incomplete.");
    const selected = [];
    for (const registration of spec.registrations) {
      let matches;
      if (registration.exactName) {
        matches = components.filter((component) =>
          component.id === registration.id && component.name === registration.exactName);
      } else {
        matches = components.filter((component) => registration.names.includes(component.name));
      }
      if (!matches.length) {
        return unavailable(`Registered component ${registration.label} could not be established exactly.`);
      }
      selected.push(...matches.map((component) => ({
        id: component.id,
        name: component.name,
        label: registration.label,
        status: component.status
      })));
    }
    if (selected.some((component) => platformStatusRank(component.status) === 99)) {
      return unavailable("A registered component returned an unrecognized status.");
    }
    const relevantIncidents = relevantPlatformIncidents(
      incidents,
      selected.map((component) => component.id)
    );
    return {
      providerId,
      provider: spec.label,
      source: spec.source,
      availability: "current",
      complete: true,
      checkedAt,
      aggregate: worstPlatformStatus(selected),
      components: selected,
      incidents: relevantIncidents,
      reason: "",
      lastValid: null
    };
  }

  function platformCellProjection(providers = platformSignals.providers) {
    const openai = providers.openai || {};
    const openaiComponent = (label) => {
      if (!openai.complete) {
        return {
          label,
          provider: "OpenAI",
          status: "unavailable",
          checkedAt: openai.checkedAt,
          detail: openai.reason || "OpenAI status is unavailable.",
          source: PLATFORM_PROVIDER_SPECS.openai.source,
          lastValid: openai.lastValid
        };
      }
      const components = openai.components.filter((component) => component.label === label);
      return {
        label,
        provider: "OpenAI",
        status: worstPlatformStatus(components),
        checkedAt: openai.checkedAt,
        detail: components.map((component) => `${component.name}: ${serviceStatusLabel(component.status)}`).join(" · "),
        source: openai.source,
        incidents: openai.incidents,
        lastValid: openai.lastValid
      };
    };
    const providerCell = (providerId, label) => {
      const provider = providers[providerId] || {};
      return {
        label,
        provider: provider.provider || PLATFORM_PROVIDER_SPECS[providerId].label,
        status: provider.complete ? provider.aggregate : "unavailable",
        checkedAt: provider.checkedAt,
        detail: provider.complete
          ? provider.components.map((component) => `${component.label}: ${serviceStatusLabel(component.status)}`).join(" · ")
          : provider.reason || `${label} status is unavailable.`,
        source: provider.source || PLATFORM_PROVIDER_SPECS[providerId].source,
        incidents: provider.incidents || [],
        lastValid: provider.lastValid || null
      };
    };
    return [
      openaiComponent("GPTs"),
      openaiComponent("Codex"),
      openaiComponent("API platform"),
      providerCell("vercel", "Vercel"),
      providerCell("cloudflare", "Cloudflare Turnstile")
    ];
  }

  function renderPlatformStatus() {
    const host = byId("overview-openai-status");
    host.className = "overview-status-grid";
    const cells = platformCellProjection();
    host.replaceChildren(...cells.map((service) => {
      const presentation = platformStatusPresentation(service.status);
      const row = element("div", "overview-status-cell");
      const retained = service.lastValid?.checkedAt
        ? ` Last valid observation ${formatOperationalDate(service.lastValid.checkedAt)}.`
        : "";
      row.title = `${service.detail}${retained}`;
      row.setAttribute("aria-label", `${service.label}: ${presentation.label}.${retained}`);
      row.append(element("span", `health-dot ${presentation.tone}`, ""), element("strong", "", service.label));
      return row;
    }));
    const currentChecks = Object.values(platformSignals.providers)
      .filter((provider) => provider.complete && provider.checkedAt)
      .map((provider) => provider.checkedAt);
    const unavailableCount = Object.values(platformSignals.providers)
      .filter((provider) => !provider.complete).length;
    byId("overview-openai-checked").textContent = currentChecks.length
      ? `Official provider observations checked independently${unavailableCount ? ` · ${unavailableCount} unavailable` : ""}`
      : "Checking independent official provider feeds…";
    renderOperationsLedgers(data.run_chain || {});
  }

  async function fetchPlatformProvider(providerId, urls) {
    const previous = platformSignals.providers[providerId];
    const checkedAt = new Date().toISOString();
    try {
      const [statusResponse, componentResponse, incidentResponse] = await Promise.all([
        urls.status ? fetch(urls.status, { cache: "no-store" }) : Promise.resolve(null),
        fetch(urls.components, { cache: "no-store" }),
        fetch(urls.incidents, { cache: "no-store" })
      ]);
      if ((statusResponse && !statusResponse.ok) || !componentResponse.ok || !incidentResponse.ok) {
        throw new Error("Official provider feed unavailable");
      }
      const [statusData, componentData, incidentData] = await Promise.all([
        statusResponse ? statusResponse.json() : Promise.resolve(null),
        componentResponse.json(),
        incidentResponse.json()
      ]);
      if (statusResponse && !statusData?.status) throw new Error("Official provider status feed incomplete");
      return {
        ...platformProviderObservation(providerId, componentData, incidentData, checkedAt, previous),
        overall: statusData?.status || null
      };
    } catch (_error) {
      return platformProviderObservation(providerId, null, null, checkedAt, previous);
    }
  }

  async function refreshPlatformStatus() {
    const observations = await Promise.all([
      fetchPlatformProvider("openai", { status: OPENAI_STATUS_URL, components: OPENAI_COMPONENTS_URL, incidents: OPENAI_INCIDENTS_URL }),
      fetchPlatformProvider("vercel", { status: VERCEL_STATUS_URL, components: VERCEL_COMPONENTS_URL, incidents: VERCEL_INCIDENTS_URL }),
      fetchPlatformProvider("cloudflare", { components: CLOUDFLARE_COMPONENTS_URL, incidents: CLOUDFLARE_INCIDENTS_URL })
    ]);
    observations.forEach((observation) => {
      platformSignals.providers[observation.providerId] = observation;
    });
    renderPlatformStatus();
  }

  function renderUsageTrend() {
    const log = projectLog("elim");
    const points = (log?.entries || []).map((entry) => ({
      id: entry.id,
      date: entry.values?.date,
      value: elimUsageConsumption(entry)
    })).slice(-10);
    const measured = points.filter((point) => Number.isFinite(point.value));
    const host = byId("overview-usage-trend");
    if (!points.length || !measured.length) {
      host.replaceChildren(element("p", "empty-state compact-empty", "No comparable Elim usage readings are recorded."));
      return;
    }
    const maximum = Math.max(10, ...measured.map((point) => point.value));
    const average = measured.reduce((sum, point) => sum + point.value, 0) / measured.length;
    const heading = element("div", "usage-trend-heading");
    heading.append(
      element("strong", "", "Elim consumption by run"),
      element("span", "", `${average.toFixed(1)}-point measured average`)
    );
    const namespace = "http://www.w3.org/2000/svg";
    const chart = document.createElementNS(namespace, "svg");
    chart.classList.add("usage-trend-svg");
    chart.setAttribute("viewBox", "0 0 640 210");
    chart.setAttribute("role", "img");
    const description = points.map((point) =>
      `${point.id}: ${point.value == null ? "not measured" : `${point.value} percentage points`}`).join("; ");
    chart.setAttribute("aria-label", description);
    const title = document.createElementNS(namespace, "title");
    title.textContent = `Elim consumption by run. ${description}`;
    chart.append(title);

    const left = 42;
    const right = 16;
    const top = 18;
    const bottom = 40;
    const width = 640 - left - right;
    const height = 210 - top - bottom;
    const chartMaximum = Math.ceil(maximum / 10) * 10;
    const xFor = (index) => points.length === 1
      ? left + width / 2
      : left + index * width / (points.length - 1);
    const yFor = (value) => top + height - value / chartMaximum * height;
    const svgNode = (name, attributes = {}, className = "") => {
      const node = document.createElementNS(namespace, name);
      Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, String(value)));
      if (className) node.setAttribute("class", className);
      return node;
    };

    [0, 0.25, 0.5, 0.75, 1].forEach((fraction) => {
      const value = chartMaximum * fraction;
      const y = yFor(value);
      chart.append(svgNode("line", { x1: left, x2: left + width, y1: y, y2: y }, "usage-trend-grid"));
      const label = svgNode("text", { x: left - 8, y: y + 4, "text-anchor": "end" }, "usage-trend-axis-label");
      label.textContent = String(Math.round(value));
      chart.append(label);
    });

    const epoch = data.run_chain?.review_epoch;
    const epochAt = Date.parse(String(epoch?.last_completed_at || ""));
    if (Number.isFinite(epochAt)) {
      const dated = points
        .map((point, index) => ({ index, distance: Math.abs(Date.parse(String(point.date || "")) - epochAt) }))
        .filter((point) => Number.isFinite(point.distance))
        .sort((leftPoint, rightPoint) => leftPoint.distance - rightPoint.distance)[0];
      if (dated) {
        const epochX = xFor(dated.index);
        chart.append(svgNode("line", { x1: epochX, x2: epochX, y1: top, y2: top + height }, "usage-trend-epoch"));
        const epochLabel = svgNode("text", { x: epochX + 5, y: top + 10 }, "usage-trend-epoch-label");
        epochLabel.textContent = "Review Epoch";
        chart.append(epochLabel);
      }
    }

    let segment = [];
    const appendSegment = () => {
      if (!segment.length) return;
      const path = svgNode("path", {
        d: segment.map((point, index) => `${index ? "L" : "M"} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ")
      }, "usage-trend-line");
      const firstPoint = chart.querySelector(".usage-trend-point");
      if (firstPoint) chart.insertBefore(path, firstPoint);
      else chart.append(path);
      segment = [];
    };
    points.forEach((point, index) => {
      const x = xFor(index);
      const xLabel = svgNode("text", { x, y: 196, "text-anchor": "middle" }, "usage-trend-axis-label usage-trend-run-label");
      xLabel.textContent = point.id.replace("elim-run-", "#");
      chart.append(xLabel);
      if (!Number.isFinite(point.value)) {
        appendSegment();
        const missing = svgNode("text", { x, y: top + height / 2, "text-anchor": "middle" }, "usage-trend-missing");
        missing.textContent = "—";
        chart.append(missing);
        return;
      }
      const y = yFor(point.value);
      segment.push({ x, y });
      const pointNode = svgNode("circle", { cx: x, cy: y, r: 4.5 }, "usage-trend-point");
      const pointTitle = document.createElementNS(namespace, "title");
      pointTitle.textContent = `${point.id}: ${point.value} percentage points`;
      pointNode.append(pointTitle);
      chart.append(pointNode);
      const valueLabel = svgNode("text", { x, y: Math.max(12, y - 9), "text-anchor": "middle" }, "usage-trend-value-label");
      valueLabel.textContent = String(point.value);
      chart.append(valueLabel);
    });
    appendSegment();
    host.replaceChildren(heading, chart);
  }

  function renderOverviewUsage(chain) {
    const usage = chain.usage || data.overview?.usage || {};
    const gate = usage.gate || {};
    const windows = Array.isArray(gate.windows) ? gate.windows : [];
    const remainingValue = gate.lowestRemainingPercent ?? usage.remaining_percent;
    const remaining = remainingValue === null || remainingValue === undefined || remainingValue === ""
      ? NaN
      : Number(remainingValue);
    const reserve = Number(gate.reservePercent ?? usage.hard_reserve_percent ?? 15);
    const softTarget = Number(gate.runBudget?.softTargetPercent ?? usage.soft_run_target_percent ?? 10);
    let posture = "Unavailable";
    let tone = "";
    if (Number.isFinite(remaining)) {
      if (remaining <= reserve) {
        posture = "Protected reserve";
        tone = "error";
      } else if (remaining <= reserve + softTarget) {
        posture = "Approaching reserve";
        tone = "warning";
      } else {
        posture = "Safe";
        tone = "success";
      }
    }
    const postureNode = byId("overview-usage-posture");
    postureNode.className = `status-badge ${tone}`.trim();
    postureNode.textContent = posture;
    const summary = byId("overview-usage-summary");
    if (!Number.isFinite(remaining)) {
      summary.replaceChildren(element("p", "empty-state compact-empty", "No current host-attested usage reading is available."));
    } else {
      const lowestWindow = windows.find((window) => Number(window.remainingPercent) === remaining);
      summary.replaceChildren(
        element("strong", "overview-usage-remaining", `${remaining}% remaining`),
        element("p", "", `${reserve}% hard reserve · ${softTarget}-point soft run target${lowestWindow?.resetsAtUtc ? ` · resets ${formatDate(lowestWindow.resetsAtUtc)}` : ""}`),
        element("span", "micro-note", `Checked ${formatDate(gate.checkedAtUtc || chain.updated_at)}`)
      );
    }
    byId("overview-usage-windows").replaceChildren(...(windows.length
      ? windows.map((window) => {
          const row = element("div", "overview-usage-window");
          row.append(
            element("strong", "", window.limitName || window.limitId || "Usage window"),
            element("span", "", `${window.remainingPercent}% remaining`),
            element("time", "", window.resetsAtUtc ? `Reset ${formatDate(window.resetsAtUtc)}` : "Reset not recorded")
          );
          return row;
        })
      : [element("p", "empty-state compact-empty", "No individual usage windows are recorded.")]));
    byId("overview-usage-detail-summary").textContent = `${windows.length} window${windows.length === 1 ? "" : "s"} · ${Number.isFinite(remaining) ? `${remaining}% lowest` : "reading unavailable"}`;
    renderUsageTrend();
  }

  function queueDirectoryCard(queue) {
    const card = element("article", `overview-queue-card${queue.tone ? ` ${queue.tone}` : ""}`);
    card.dataset.layoutId = `overview-queue-${layoutSlug(queue.label)}`;
    const external = queue.target.startsWith("http");
    const primary = element("a", "overview-queue-primary");
    primary.href = external ? queue.target : `#${queue.target}`;
    if (external) {
      primary.target = "_blank";
      primary.rel = "noopener noreferrer";
    }
    const count = queue.count == null ? "—" : String(queue.count);
    const heading = element("div", "overview-queue-card-heading");
    heading.append(element("strong", "", queue.label), element("span", "overview-queue-count", count));
    primary.append(heading, element("span", "overview-queue-open", external ? "Details ↗" : "Details →"));
    card.append(primary);
    if (queue.tone && queue.tone !== "success") {
      const problem = element(
        "a",
        "overview-queue-problem",
        queue.problemLabel || (queue.count == null ? "Feed unavailable · open log →" : "Problem · open log →")
      );
      problem.href = `#${queue.problemTarget || "logs:agents"}`;
      card.append(problem);
    }
    return card;
  }

  function renderOverviewQueues(snapshot, chain) {
    const lifecycle = currentLifecycleRecords();
    const workflowCount = (...statuses) => lifecycle.filter((record) => statuses.includes(record.workflowStatus)).length;
    const intake = publicInputSnapshot(chain);
    const incidentProjection = operationalIncidentProjection();
    const configuredQueues = Array.isArray(data.overview?.queue_counts)
      ? data.overview.queue_counts
      : data.overview?.queue_counts && typeof data.overview.queue_counts === "object"
        ? Object.entries(data.overview.queue_counts).map(([label, value]) => ({
            label,
            ...(value && typeof value === "object" ? value : { count: value })
          }))
        : [];
    const queueTarget = (label, target) => {
      const normalized = String(label || "").toLowerCase();
      if (normalized === "development") return "planning:workbench:pipeline:status=Development";
      if (normalized === "research") return "planning:workbench:pipeline:status=Research";
      if (normalized === "audits") return "planning:workbench:pipeline:status=Audit%20work";
      if (normalized === "external review") return "planning:workbench:pipeline:status=External%20review&scope=review-ready";
      if (["candidate intake", "preliminary intake"].includes(normalized)) {
        return "planning:workbench:pipeline:work_class=Preliminary%20candidate";
      }
      if (target && target !== "progress") return target;
      return target || "overview";
    };
    const allowedQueues = new Set([
      "Human actions", "Development", "Research", "Audits", "External review",
      "Candidate intake", "Preliminary intake", "Source routing", "Pending source routing",
      "Operational incidents", "Security remediation"
    ]);
    const configuredActiveQueues = configuredQueues.filter((queue) =>
      allowedQueues.has(queue.label || queue.name || queue.id));
    const compactCounts = data.overview?.queue_counts || {};
    const queues = configuredActiveQueues.length ? configuredActiveQueues.map((queue) => ({
      label: queue.label || queue.name || queue.id,
      count: queue.available === false ? null : queue.count,
      target: queueTarget(queue.label || queue.name || queue.id, queue.target || queue.route),
      tone: queue.tone || "",
      problemTarget: queue.problem_target || queue.log_route
    })) : [
      { label: "Human actions", count: compactCounts.human_actions ?? snapshot.total, target: "actions", problemTarget: "logs:integrity" },
      { label: "Development", count: compactCounts.development ?? workflowCount("Development"), target: "planning:workbench:pipeline:status=Development" },
      { label: "Research", count: compactCounts.research ?? workflowCount("Research"), target: "planning:workbench:pipeline:status=Research" },
      { label: "Audits", count: compactCounts.audits ?? workflowCount("Audit needed", "Audit in progress"), target: "planning:workbench:pipeline:status=Audit%20work" },
      { label: "External review", count: compactCounts.external_review ?? workflowCount("External review"), target: "planning:workbench:pipeline:status=External%20review&scope=review-ready" },
      { label: "Candidate intake", count: compactCounts.preliminary_candidates ?? data.records.length, target: "planning:workbench:pipeline:work_class=Preliminary%20candidate" },
      { label: "Source routing", count: compactCounts.pending_sources ?? data.pending_sources.length, target: "sources:pending" },
      {
        label: "Operational incidents",
        count: incidentProjection.unresolvedCount,
        target: "automation:logs:incidents",
        tone: incidentProjection.complete
          ? incidentProjection.impactState === "red"
            ? "error"
            : incidentProjection.impactState === "yellow"
              ? "warning"
              : ""
          : "unavailable",
        problemTarget: "automation:logs:incidents",
        problemLabel: incidentProjection.complete
          ? "Open incident ledger →"
          : "Incident feed unavailable →"
      }
    ];
    if (!queues.some((queue) => queue.label === "Security remediation")) {
      const security = securityAssuranceProjection();
      const protectedActions = security.available
        ? security.tools.filter((tool) => tool.private_attention === "yes").length
        : null;
      queues.push({
        label: "Security remediation",
        count: protectedActions,
        target: "automation:security",
        tone: security.available ? (protectedActions ? "warning" : "") : "unavailable",
        problemTarget: "automation:security",
        problemLabel: security.available
          ? "Open protected review →"
          : "Private feed unavailable →"
      });
    }
    queues.forEach((queue) => {
      if (queue.count == null) queue.tone = "unavailable";
      else if (queue.label === "Operational incidents") {
        queue.tone = incidentProjection.impactState === "red"
          ? "error"
          : incidentProjection.impactState === "yellow"
            ? "warning"
            : "";
      }
    });
    const active = queues.filter((queue) => queue.count != null && queue.count > 0);
    const empty = queues.filter((queue) => queue.count === 0);
    const unavailable = queues.filter((queue) => queue.count == null);
    byId("overview-queue-directory").replaceChildren(...queues.map(queueDirectoryCard));
    byId("overview-queues-summary").textContent = `${active.length} active · ${empty.length} empty · ${unavailable.length} unavailable`;
  }

  function overviewBriefVerification(chain) {
    const progressFeed = Object.keys(data.progress || {}).length
      ? data.progress
      : data.overview?.progress_summary || {};
    const integrityFeed = Object.keys(data.integrity || {}).length
      ? data.integrity
      : data.overview?.integrity_summary || {};
    const sourceFeed = Object.keys(data.source_checker || {}).length
      ? data.source_checker
      : data.overview?.source_checker_summary || {};
    const required = [
      {
        label: "Progress",
        state: feedContractState(
          progressFeed,
          progressFeed.generated_at || progressFeed.generatedAt
        )
      },
      {
        label: "Integrity",
        state: feedContractState(
          integrityFeed,
          integrityFeed.current?.generated_at || integrityFeed.generated_at
        )
      },
      {
        label: "Source checks",
        state: feedContractState(sourceFeed, sourceFeed.checked_at)
      },
      {
        label: "Run chain",
        state: operationalFeedState(chain)
      }
    ].map((entry) => ({
      ...entry,
      timestampValid: parseTimestamp(entry.state.timestamp) !== null,
      current: (
        entry.state.state === "current"
        && entry.state.complete
        && parseTimestamp(entry.state.timestamp) !== null
      )
    }));
    const bundle = domainGenerationStatus(
      catalogGenerationId,
      "overview.js",
      data.domain_generation,
      data.generation_manifest
    );
    const bundleVerified = bundle.valid && !bundle.legacy;
    const failed = required.filter((entry) => !entry.current);
    return {
      required,
      failed,
      passed: required.length - failed.length,
      bundle,
      bundleVerified,
      verified: bundleVerified && failed.length === 0
    };
  }

  function attemptRecordedAt(attempt = {}) {
    return attempt.host_updated_at
      || attempt.checked_at
      || attempt.updated_at
      || attempt.completed_at
      || attempt.created_at
      || attempt.started_at;
  }

  function attemptFailed(attempt = {}) {
    return Boolean(attempt.failure_reason)
      || /fail|error|block|cancel|timeout/i.test(String(attempt.status || ""));
  }

  function attemptSucceeded(attempt = {}) {
    return !attemptFailed(attempt)
      && /success|succeed|complete|healthy|pass|not[-_ ]?due/i.test(String(attempt.status || ""));
  }

  function attemptIntentionallyPaused(attempt = {}) {
    const reason = String(
      attempt.pause_reason
      || attempt.suppression_reason
      || attempt.validation_summary?.reason
      || ""
    );
    return attempt.control_state === "paused"
      || /pause|suppressed/i.test(String(attempt.status || ""))
      || /owner_pause_file_present|intentional_pause/i.test(reason);
  }

  function newestAttempt(...attempts) {
    return attempts
      .filter((attempt) => attempt && typeof attempt === "object" && attemptRecordedAt(attempt))
      .sort((left, right) =>
        (parseTimestamp(attemptRecordedAt(right)) ?? -Infinity)
        - (parseTimestamp(attemptRecordedAt(left)) ?? -Infinity))[0] || {};
  }

  function scopedAutomationBlockers(readiness, scope) {
    const latest = readiness.latest_attempt || {};
    const gates = readiness.future_run_gates || {};
    const blockers = [
      ...(Array.isArray(latest.blockers) ? latest.blockers : []),
      ...(Array.isArray(gates.items) ? gates.items : [])
    ];
    return blockers.filter((blocker) => {
      const declared = blocker.run_scopes
        || blocker.applies_to
        || blocker.scope
        || blocker.run_scope;
      if (!declared) return true;
      const values = (Array.isArray(declared) ? declared : [declared])
        .map((value) => String(value).toLowerCase());
      if (values.some((value) => /all|both|automation/.test(value))) return true;
      return scope === "full-review"
        ? values.some((value) => /full|review|epoch|biweekly/.test(value))
        : values.some((value) => /ordinary|scheduled|daily|next/.test(value));
    });
  }

  function upcomingAutomationState(readiness, controlState, scope) {
    const blockers = scopedAutomationBlockers(readiness, scope);
    if (blockers.length) {
      return {
        tone: "error",
        label: `${pluralizeWord(blockers.length, "confirmed automation blocker")} applies to this run`,
        route: "automation:gates"
      };
    }
    if (controlState === "paused") {
      return {
        tone: "warning",
        label: "Automation is intentionally Paused",
        route: "automation:overview"
      };
    }
    const readinessKnown = readiness.latest_attempt?.available === true
      && readiness.future_run_gates?.available === true;
    if (controlState === "run" && readinessKnown) {
      return {
        tone: "success",
        label: "Automation is in Run state with no applicable blocker recorded"
      };
    }
    return {
      tone: "unavailable",
      label: "Run readiness cannot be verified from the authoritative control and blocker records",
      route: "automation:data"
    };
  }

  function overviewBriefFactStates(
    chain,
    readiness,
    verification,
    localStatus = window.ARRP_LOCAL_AUTOMATION_STATUS
  ) {
    const scheduledProjection = readiness.latest_scheduled_attempt || {};
    const scheduledAttempt = newestAttempt(
      scheduledProjection.available === true ? scheduledProjection : null,
      /schedule|launchd/i.test(String(chain.trigger || "")) ? chain : null,
      /schedule|launchd/i.test(String(localStatus?.trigger || "")) ? localStatus : null
    );
    const controlState = ["run", "paused"].includes(String(localStatus?.control_state || "").toLowerCase())
      ? String(localStatus.control_state).toLowerCase()
      : ["run", "paused"].includes(String(readiness.control_state || "").toLowerCase())
        ? String(readiness.control_state).toLowerCase()
        : "unknown";
    const scheduledPaused = attemptIntentionallyPaused(scheduledAttempt);
    const scheduledFailed = attemptFailed(scheduledAttempt);
    const scheduledBlocked = scopedAutomationBlockers(readiness, "ordinary").length > 0;
    const scheduledState = scheduledFailed || (scheduledPaused && scheduledBlocked)
      ? {
          tone: "error",
          label: scheduledFailed
            ? "The chronologically latest scheduled attempt failed or was prevented by an operational fault"
            : "A confirmed operational blocker takes precedence over the recorded pause state",
          route: "automation:overview"
        }
      : scheduledPaused
        ? {
            tone: "warning",
            label: "The chronologically latest scheduled attempt was intentionally Paused",
            route: "automation:overview"
          }
        : attemptSucceeded(scheduledAttempt)
          ? {
              tone: "success",
              label: "The chronologically latest scheduled attempt completed successfully"
            }
          : {
              tone: "unavailable",
              label: "The chronologically latest scheduled attempt outcome cannot be determined reliably",
              route: "automation:data"
            };
    const staleOnly = verification.failed.length > 0
      && verification.bundleVerified
      && verification.failed.every((entry) =>
        entry.state.state === "stale"
        && entry.state.complete
        && entry.timestampValid);
    const explicitRefreshFailure = verification.failed.some((entry) =>
      /fail|error|block/i.test(String(entry.state.reason || "")));
    const dataState = verification.verified
      ? {
          tone: "success",
          label: "The loaded project data meets every defined freshness cadence"
        }
      : explicitRefreshFailure
        ? {
            tone: "error",
            label: "A required project-data refresh reports a confirmed failure or blocker",
            route: "automation:data"
          }
        : staleOnly && controlState === "paused"
        ? {
            tone: "warning",
            label: "The loaded project data became stale while automation was intentionally Paused",
            route: "automation:data"
          }
        : staleOnly
          ? {
              tone: "error",
              label: "Required project data is unexpectedly stale or its latest refresh failed",
              route: "automation:data"
            }
          : {
              tone: "unavailable",
              label: "Project data freshness cannot be verified reliably",
              route: "automation:data"
            };
    return {
      latestAttempt: scheduledAttempt,
      scheduledAttempt,
      controlState,
      data: dataState,
      latest: scheduledState,
      lastSuccessful: {
        ...scheduledState,
        label: scheduledState.tone === "success"
          ? "No newer scheduled attempt failed after this full success"
          : scheduledState.tone === "warning"
            ? "A deliberate pause occurred after this full success without a later failure"
            : scheduledState.tone === "error"
              ? "The immediately latest scheduled attempt failed after this full success"
              : "The relationship between this full success and the latest scheduled attempt cannot be verified",
        route: scheduledState.tone === "success" ? undefined : scheduledState.route
      },
      nextRun: upcomingAutomationState(readiness, controlState, "ordinary"),
      nextEpoch: upcomingAutomationState(readiness, controlState, "full-review")
    };
  }

  function renderOverviewDaily(
    snapshot,
    chain,
    readiness = data.overview?.automation_readiness || {}
  ) {
    const humanActionCount = data.overview?.queue_counts?.human_actions ?? snapshot.total;
    const stages = overviewRunChainStages(chain);
    const failed = stages.filter((stage) => stage.tone === "error").length;
    const degraded = stages.filter((stage) => stage.tone === "warning").length;
    const succeeded = stages.filter((stage) =>
      stage.tone === "success" && stage.currentChainLabel !== "Not due this chain").length;
    const notDue = stages.filter((stage) => stage.currentChainLabel === "Not due this chain").length;
    const unavailable = stages.filter((stage) => stage.tone === "unavailable").length;
    const chainStatus = effectiveRunChainStatus(chain);
    const verification = overviewBriefVerification(chain);
    let tone = "success";
    let summary = `${succeeded} current-chain stage result${succeeded === 1 ? "" : "s"} succeeded; ${notDue} stage${notDue === 1 ? " was" : "s were"} not due this chain. Latest successful worker results remain visible separately.`;
    if (failed) {
      tone = "error";
      summary = `${failed} current-chain stage${failed === 1 ? "" : "s"} failed or blocked. ${succeeded} current-chain stage result${succeeded === 1 ? "" : "s"} succeeded; ${notDue} ${notDue === 1 ? "was" : "were"} not due.`;
    } else if (degraded || /pending|progress|stopp/i.test(chainStatus)) {
      tone = "warning";
      summary = `${succeeded} current-chain stage result${succeeded === 1 ? "" : "s"} succeeded; ${notDue} ${notDue === 1 ? "was" : "were"} not due; ${degraded} stage${degraded === 1 ? "" : "s"} still lack${degraded === 1 ? "s" : ""} a final or fully healthy result.`;
    } else if (unavailable) {
      tone = "warning";
      summary = `${succeeded} current-chain stage result${succeeded === 1 ? "" : "s"} succeeded; ${notDue} ${notDue === 1 ? "was" : "were"} not due; ${unavailable} stage${unavailable === 1 ? "" : "s"} lack${unavailable === 1 ? "s" : ""} a current result.`;
    } else if (!verification.bundleVerified || verification.failed.some((entry) =>
      !entry.state.complete
      || !entry.timestampValid
      || ["unavailable", "incomplete", "undeclared"].includes(entry.state.state))) {
      tone = "warning";
      summary = `${summary} The brief cannot verify ${verification.failed.map((entry) => entry.label).join(", ") || "its generation identity"}.`;
    } else if (verification.failed.length) {
      tone = "warning";
      summary = `${summary} ${verification.failed.map((entry) => entry.label).join(" and ")} ${verification.failed.length === 1 ? "is" : "are"} producer-declared stale.`;
    }
    const factStates = overviewBriefFactStates(chain, readiness, verification);
    const badge = byId("overview-daily-status");
    badge.className = `status-badge ${factStates.latest.tone}`;
    badge.textContent = {
      success: "Current",
      warning: "Paused",
      error: "Failed",
      unavailable: "Unknown"
    }[factStates.latest.tone];
    badge.title = factStates.latest.label;
    const attemptAt = attemptRecordedAt(factStates.latestAttempt)
      || chain.host_updated_at
      || chain.completed_at
      || chain.updated_at
      || chain.created_at;
    const successfulTimes = overviewRunChainStages(chain)
      .map((stage) => parseTimestamp(stage.lastSuccessAt))
      .filter((value) => value !== null);
    const lastFullySuccessfulAt = chain.last_successful_at
      || chain.last_success_at
      || (successfulTimes.length ? new Date(Math.min(...successfulTimes)).toISOString() : null);
    const progressFeed = Object.keys(data.progress || {}).length ? data.progress : data.overview?.progress_summary;
    const integrityFeed = Object.keys(data.integrity || {}).length ? data.integrity : data.overview?.integrity_summary;
    const sourceFeed = Object.keys(data.source_checker || {}).length ? data.source_checker : data.overview?.source_checker_summary;
    const feedTimes = [
      progressFeed?.generated_at || progressFeed?.generatedAt,
      integrityFeed?.current?.generated_at || integrityFeed?.generated_at,
      sourceFeed?.checked_at,
      chain.updated_at || chain.completed_at
    ].map(parseTimestamp).filter((value) => value !== null);
    const currentThrough = feedTimes.length ? new Date(Math.min(...feedTimes)).toISOString() : null;
    const asOf = attemptAt || data.generated_at;
    byId("overview-daily-summary").textContent =
      `As of ${formatOperationalDate(asOf)}, ${summary} ${humanActionCount} confirmed human action${humanActionCount === 1 ? "" : "s"} remain${humanActionCount === 1 ? "s" : ""}.`;
    const epoch = chain.review_epoch || {};
    const facts = [
      ["Data current through", formatOperationalDate(currentThrough), factStates.data],
      ["Latest scheduled attempt", formatOperationalDate(attemptAt), factStates.latest],
      ["Last fully successful", formatOperationalDate(lastFullySuccessfulAt), factStates.lastSuccessful],
      ["Next scheduled run", formatOperationalDate(chain.next_scheduled_at || nextScheduledCoordinatorRun()), factStates.nextRun],
      ["Next full Review Epoch", epoch.next_due_at
        ? formatOperationalDate(nextScheduledCoordinatorRun(epoch.next_due_at))
        : "No review boundary recorded", factStates.nextEpoch]
    ];
    byId("overview-daily-facts").replaceChildren(...facts.map(([label, value, state]) => {
      const fact = element("div", "overview-daily-fact");
      const valueRow = element(state.tone === "success" || !state.route ? "span" : "a", "overview-daily-value");
      if (state.route) valueRow.href = `#${state.route}`;
      const dot = element("span", `overview-fact-dot ${state.tone}`, "");
      dot.setAttribute("role", "img");
      dot.setAttribute("aria-label", state.label);
      dot.tabIndex = 0;
      dot.title = state.label;
      valueRow.append(dot, element("span", "overview-daily-date", value));
      fact.append(element("strong", "", label), valueRow);
      return fact;
    }));
    const verificationNode = byId("overview-daily-verification");
    const failedBasis = verification.failed.map((entry) => {
      if (!entry.timestampValid) return `${entry.label} has no valid timestamp`;
      if (!entry.state.complete) return `${entry.label} is incomplete`;
      return `${entry.label} is ${entry.state.label.toLowerCase()}`;
    });
    if (!verification.bundleVerified) {
      failedBasis.unshift(verification.bundle.reason || "Overview generation identity is not verifiable");
    }
    verificationNode.className = `overview-daily-verification${verification.verified ? "" : " warning"}`;
    verificationNode.replaceChildren(
      document.createTextNode(
        verification.verified
          ? `Verified when this page opened ${formatOperationalDate(consoleOpenedAt)}: all ${verification.required.length} required snapshot feeds are producer-declared current, structurally complete, timestamped, and generation-compatible. `
          : `Not verified current when this page opened ${formatOperationalDate(consoleOpenedAt)}: ${verification.passed} of ${verification.required.length} required snapshot feeds passed; ${failedBasis.join("; ")}. `
      ),
      document.createTextNode("This evaluates the loaded snapshot; it does not reread every external authority. "),
      (() => {
        const link = element("a", "", "Open Data evidence →");
        link.href = "#automation:data";
        return link;
      })()
    );
    const explanation = byId("overview-degraded-explanation");
    const integrityState = feedContractState(
      integrityFeed,
      integrityFeed?.current?.generated_at || integrityFeed?.generated_at
    );
    const needsExplanation = tone !== "success" || !integrityState.complete || !verification.verified;
    explanation.hidden = !needsExplanation;
    if (needsExplanation) {
      const fields = [
        ["Affected", verification.failed.length
          ? `${verification.failed.map((entry) => entry.label).join(", ")} and dependent summaries`
          : !verification.bundleVerified
            ? "Overview generation identity and dependent summaries"
            : Number(readiness.latest_attempt?.blocker_count || 0)
              ? `${pluralizeWord(Number(readiness.latest_attempt.blocker_count), "latest-attempt blocker")} and dependent summaries`
              : "One or more current operational summaries"],
        ["Why", failedBasis.join("; ") || integrityState.reason || chain.next_action || summary],
        ["Still trustworthy", currentThrough
          ? `Last valid projections through ${formatOperationalDate(currentThrough)}`
          : "The specialist ledgers identify their last valid boundaries"],
        ["Next action", verification.failed.length || !verification.bundleVerified
          ? "Open the Data ledger and follow the affected feed's recorded recovery route"
          : chain.next_action || "Open the affected specialist ledger and follow its recorded recovery route"]
      ];
      explanation.replaceChildren(...fields.flatMap(([label, value]) => [
        element("dt", "", label),
        element("dd", "", value)
      ]));
    } else {
      explanation.replaceChildren();
    }
  }

  function renderOverview() {
    if (!byId("overview-daily-section")) return;
    const chain = Object.keys(data.run_chain || {}).length
      ? data.run_chain
      : data.overview?.automation_summary?.run_chain || data.overview?.automation_summary || {};
    captureSuccessfulStageHistory(chain);
    const snapshot = actionItemSnapshot();
    const readiness = data.overview?.automation_readiness || {};
    byId("overview-generated-at").textContent = formatDate(data.generated_at);
    renderOverviewDaily(snapshot, chain, readiness);
    renderOverviewAutomationActivity(chain, readiness);
    renderOverviewPortals(snapshot, chain);
    renderOverviewRecentActivity();
    const progressFeed = Object.keys(data.progress || {}).length
      ? data.progress
      : data.overview?.progress_summary || {};
    const integrityFeed = Object.keys(data.integrity || {}).length
      ? data.integrity
      : data.overview?.integrity_summary || {};
    const sourceCheckerFeed = Object.keys(data.source_checker || {}).length
      ? data.source_checker
      : data.overview?.source_checker_summary || {};
    byId("overview-freshness").replaceChildren(
      projectionStatusCard("Console bundle", data, "overview", data.generated_at),
      projectionStatusCard("GitHub Project", data.overview?.progress_summary || {}, "progress", data.github_synced_at),
      projectionStatusCard("Progress feed", progressFeed, "progress", progressFeed.generatedAt || progressFeed.asOf || progressFeed.generated_at),
      projectionStatusCard("Integrity feed", integrityFeed, "integrity", integrityFeed?.current?.generated_at || integrityFeed.generated_at),
      projectionStatusCard("Run chain", chain, "automation", chain.updated_at || chain.created_at || data.overview?.automation_summary?.generated_at),
      projectionStatusCard("Source checks", sourceCheckerFeed, "sources:watchers:source-checker", sourceCheckerFeed.checked_at || sourceCheckerFeed.generated_at)
    );
    renderPlatformStatus();
    renderOverviewUsage(chain);
    renderOverviewQueues(snapshot, chain);
    refreshLayoutZones();
  }

  function automationStatusClass(status) {
    if (/^enabled$/i.test(status)) return "enabled";
    if (/pilot/i.test(status)) return "pilot";
    if (/paused/i.test(status)) return "paused";
    return "";
  }

  function runChainStages(chain) {
    if (Array.isArray(chain.stages)) return chain.stages;
    if (chain.stages && typeof chain.stages === "object") {
      return Object.entries(chain.stages).map(([id, stage]) => ({ id, ...(stage || {}) }));
    }
    return [];
  }

  function captureSuccessfulStageHistory(chain = {}) {
    const stages = [
      ...runChainStages(chain),
      ...(Array.isArray(chain.last_successful_stages) ? chain.last_successful_stages : [])
    ];
    stages.forEach((stage) => {
      const id = stage?.id || stage?.stage_id;
      const status = String(stage?.status || "");
      const lastSuccessAt = stage?.last_success_at
        || stage?.last_success
        || stage?.last_succeeded_at
        || (/success|succeed|complete|healthy|pass/i.test(status) ? stage?.completed_at || stage?.updated_at : null);
      if (!id || !lastSuccessAt) return;
      const existing = successfulStageHistory.get(id);
      if (!existing || dateTimestamp(lastSuccessAt) >= dateTimestamp(existing.last_success_at)) {
        successfulStageHistory.set(id, {
          ...stage,
          id,
          status: "succeeded",
          last_success_at: lastSuccessAt
        });
      }
    });
  }

  function failedAutomationStages(chain = data.run_chain || {}) {
    const registeredWorkers = new Set(data.agent_registry.map((record) => record.id));
    const stageMap = new Map(runChainStages(chain).map((stage) => [stage.id, stage]));
    if (chain.elim_runtime && typeof chain.elim_runtime === "object") {
      stageMap.set("elim", { id: "elim", ...chain.elim_runtime });
    }
    [...(Array.isArray(chain.failures) ? chain.failures : []),
      ...(Array.isArray(chain.degradations) ? chain.degradations : [])]
      .filter((failure) => failure && typeof failure === "object")
      .forEach((failure) => {
        const id = failure.stage_id || failure.stage || failure.bot_id || failure.id;
        if (registeredWorkers.has(id)) stageMap.set(id, { ...(stageMap.get(id) || { id }), ...failure, id });
      });
    return [...stageMap.values()].filter((stage) => {
      if (!registeredWorkers.has(stage.id)) return false;
      const status = String(stage.status || "").toLowerCase();
      const classification = String(stage.failure_class || stage.classification || "").toLowerCase();
      const explicitFailure = /fail|error|stale|block|timeout|timed.out|cancel/.test(status);
      const blockingFailure = String(stage.failure_class || "").toLowerCase() === "blocking"
        && !["", "pending", "not_due", "not due", "succeeded", "success", "completed", "healthy"].includes(status);
      return explicitFailure || /fail|error|stale|block/.test(classification)
        || stage.stale === true || stage.blocking === true || blockingFailure;
    });
  }

  function botFailureSummary(stage) {
    return stage.diagnostic
      || stage.details
      || stage.reason
      || stage.message
      || stage.failure_summary
      || `${String(stage.status || "Error").replaceAll("_", " ")} in the current run chain.`;
  }

  function automationIncidentIdentity(record, index) {
    const rawCause = String(
      record.root_cause || record.failed_prerequisite || record.prerequisite
        || record.failure_class || record.classification || botFailureSummary(record)
        || `unclassified-${index}`
    ).trim();
    const compact = rawCause.toLowerCase().replace(/\s+/g, " ");
    if (
      /canonical arrp workspace is not reconciled with github/.test(compact)
      || /current branch (?:is )?.+ instead of main/.test(compact)
    ) {
      return {
        rootCause: "Canonical ARRP workspace is off main and not reconciled with GitHub.",
        failedPrerequisite: "host-repository-preflight",
        checkoutState: "off-main canonical checkout",
        runtimeState: "dispatch blocked before launch"
      };
    }
    if (/isolated elim checkout contains a prior unsynchronized baseline/.test(compact)) {
      return {
        rootCause: "The isolated Elim checkout contains a prior unsynchronized baseline.",
        failedPrerequisite: "elim-isolated-checkout",
        checkoutState: "unsynchronized isolated checkout",
        runtimeState: "Elim launch blocked"
      };
    }
    return {
      rootCause: rawCause,
      failedPrerequisite: String(record.failed_prerequisite || record.prerequisite || ""),
      checkoutState: String(
        record.checkout_state || record.worktree_state
          || record.repository_state || record.checkout || ""
      ),
      runtimeState: String(
        record.runtime_state || record.host_state
          || record.execution_state || record.runtime || ""
      )
    };
  }

  function incidentHasHumanOwner(incident) {
    return (incident.owners || []).some((owner) =>
      /^(?:human|you|project manager|human project owner)$/i.test(String(owner).trim()));
  }

  function automationIncidentRecordResolved(record) {
    return record.resolved === true
      || /^(?:resolved|closed|superseded|complete)$/i.test(String(record.status || ""));
  }

  function automationIncidentObserved(record, chain = {}) {
    return record.recorded_at || record.detected_at || record.created_at
      || record.updated_at || record.completed_at || chain.updated_at || "";
  }

  function automationIncidentEventKey(record, chain = {}, index = 0) {
    const normalizeKey = (value) => String(value || "").trim().toLowerCase().replace(/\s+/g, " ");
    const observed = automationIncidentObserved(record, chain);
    const parsedObserved = parseTimestamp(observed);
    if (!observed) {
      // A missing timestamp cannot safely establish that two otherwise similar rows are one event.
      return JSON.stringify(["undated", record.__incidentSource || "incident", index]);
    }
    const chainId = record.chain_id || record.review_epoch
      || chain.chain_id || chain.review_epoch || "current-chain-unavailable";
    const stage = record.stage_id || record.stage || record.bot_id || record.id || "stage-unavailable";
    const detail = record.details || record.message || record.summary || record.root_cause
      || record.failed_prerequisite || record.prerequisite || "detail-unavailable";
    return JSON.stringify([
      normalizeKey(chainId),
      normalizeKey(stage),
      parsedObserved === null ? normalizeKey(observed) : String(parsedObserved),
      normalizeKey(detail)
    ]);
  }

  function deduplicateAutomationIncidentRecords(records, chain = {}) {
    const events = new Map();
    const sourceRank = {
      "current-failure": 0,
      "current-degradation": 1,
      "host-action": 2,
      incident: 3
    };
    records.forEach((record, index) => {
      const key = automationIncidentEventKey(record, chain, index);
      if (!events.has(key)) {
        const currentSource = ["current-failure", "current-degradation"].includes(record.__incidentSource);
        events.set(key, {
          ...record,
          chain_id: record.chain_id || (currentSource ? chain.chain_id : "") || "",
          __incidentSources: [record.__incidentSource || "incident"]
        });
        return;
      }
      const previous = events.get(key);
      const sources = [...new Set([
        ...(previous.__incidentSources || [previous.__incidentSource]),
        record.__incidentSource || "incident"
      ].filter(Boolean))];
      const preferredSource = [...sources].sort((left, right) =>
        (sourceRank[left] ?? 9) - (sourceRank[right] ?? 9))[0];
      const previousCount = Number(previous.occurrences || previous.failure_count || 1);
      const recordCount = Number(record.occurrences || record.failure_count || 1);
      events.set(key, {
        ...previous,
        ...record,
        chain_id: record.chain_id || previous.chain_id
          || (sources.some((source) => ["current-failure", "current-degradation"].includes(source))
            ? chain.chain_id
            : "") || "",
        owner: record.owner || previous.owner,
        action_owner: record.action_owner || previous.action_owner,
        assigned_to: record.assigned_to || previous.assigned_to,
        recorded_at: record.recorded_at || previous.recorded_at,
        detected_at: record.detected_at || previous.detected_at,
        created_at: record.created_at || previous.created_at,
        updated_at: record.updated_at || previous.updated_at,
        completed_at: record.completed_at || previous.completed_at,
        details: record.details || previous.details,
        message: record.message || previous.message,
        recovery: record.recovery || previous.recovery,
        next_action: record.next_action || previous.next_action,
        occurrences: Math.max(
          Number.isFinite(previousCount) ? previousCount : 1,
          Number.isFinite(recordCount) ? recordCount : 1
        ),
        resolved: automationIncidentRecordResolved(previous)
          && automationIncidentRecordResolved(record),
        __incidentSource: preferredSource,
        __incidentSources: sources
      });
    });
    return [...events.values()];
  }

  function groupAutomationIncidents(chain = data.run_chain || {}) {
    const records = deduplicateAutomationIncidentRecords([
      ...(Array.isArray(chain.incidents) ? chain.incidents.map((record) => ({ ...record, __incidentSource: "incident" })) : []),
      ...(Array.isArray(chain.failures) ? chain.failures.map((record) => ({ ...record, __incidentSource: "current-failure" })) : []),
      ...(Array.isArray(chain.degradations) ? chain.degradations.map((record) => ({ ...record, __incidentSource: "current-degradation" })) : []),
      ...(Array.isArray(chain.host_action_items) ? chain.host_action_items.map((record) => ({ ...record, __incidentSource: "host-action" })) : [])
    ], chain);
    const groups = new Map();
    records.forEach((record, index) => {
      const identity = automationIncidentIdentity(record, index);
      const {
        rootCause,
        failedPrerequisite,
        checkoutState,
        runtimeState
      } = identity;
      const normalizeKey = (value) => String(value || "").trim().toLowerCase().replace(/\s+/g, " ");
      const key = JSON.stringify([
        normalizeKey(rootCause || `unclassified-${index}`),
        normalizeKey(failedPrerequisite),
        normalizeKey(checkoutState),
        normalizeKey(runtimeState)
      ]);
      if (!groups.has(key)) {
        groups.set(key, {
          rootCause: String(rootCause || "Unclassified automation incident"),
          failedPrerequisite: String(failedPrerequisite || "Not recorded"),
          checkoutState: String(checkoutState || "Not recorded"),
          runtimeState: String(runtimeState || "Not recorded"),
          occurrences: 0,
          history: [],
          stages: new Set(),
          activeOwners: new Set(),
          historicalOwners: new Set(),
          postures: new Set(),
          active: false,
          activeOccurrences: 0,
          firstSeen: null,
          lastSeen: null,
          recovery: record.recovery || record.next_action || record.resolution || ""
        });
      }
      const group = groups.get(key);
      const occurrenceCount = Number(record.occurrences || record.failure_count || 1);
      const resolved = automationIncidentRecordResolved(record);
      const active = !resolved;
      group.occurrences += occurrenceCount;
      if (active) {
        group.active = true;
        group.activeOccurrences += occurrenceCount;
      }
      const stage = record.stage_id || record.stage || record.bot_id || record.id;
      if (stage) group.stages.add(String(stage));
      const owner = record.owner || record.action_owner || record.assigned_to;
      if (owner) {
        if (active) group.activeOwners.add(String(owner));
        else group.historicalOwners.add(String(owner));
      }
      const observed = automationIncidentObserved(record, chain);
      const timestamp = parseTimestamp(observed);
      const posture = record.superseded === true || resolved
        ? "Superseded"
        : record.__incidentSource === "current-failure"
          || record.__incidentSource === "current-degradation"
          || String(record.chain_id || record.review_epoch || "") === String(chain.chain_id || chain.review_epoch || "")
          ? "Current chain"
          : record.posture || record.status || "Historical";
      group.postures.add(posture);
      group.history.push({
        observed,
        stage: stage || "unavailable",
        status: record.status || record.outcome || "unavailable",
        posture,
        chainId: record.chain_id || "",
        details: record.details || record.message || record.summary || "",
        checkoutState: record.checkout_state || record.worktree_state
          || record.repository_state || record.checkout || ""
      });
      if (timestamp !== null && (group.firstSeen === null || timestamp < group.firstSeen)) group.firstSeen = timestamp;
      if (timestamp !== null && (group.lastSeen === null || timestamp > group.lastSeen)) group.lastSeen = timestamp;
      if (!group.recovery) group.recovery = record.recovery || record.next_action || record.resolution || "";
    });
    return [...groups.values()].map((group) => ({
      ...group,
      stages: [...group.stages].sort(),
      owners: [...group.activeOwners].sort(),
      historicalOwners: [...group.historicalOwners].sort(),
      postures: [...group.postures].sort(),
      history: [...group.history].sort((left, right) =>
        (parseTimestamp(right.observed) || 0) - (parseTimestamp(left.observed) || 0))
    })).filter((group) => group.active)
      .sort((left, right) => right.occurrences - left.occurrences || left.rootCause.localeCompare(right.rootCause));
  }

  function runChainQueue(chain) {
    return chain.work_queue?.counts || chain.queue_counts || chain.queue || {};
  }

  function runChainCount(queue, key) {
    const value = Number(queue[key] ?? queue[`${key}_count`] ?? 0);
    return Number.isFinite(value) ? value : 0;
  }

  function runChainStatusClass(status) {
    if (/fail|block|error/i.test(status || "")) return "error";
    if (/degrad|warn|partial|pending|stopp/i.test(status || "")) return "warning";
    if (/complete|healthy|success|no.?op/i.test(status || "")) return "success";
    return "";
  }

  function localAutomationPresentation(status = window.ARRP_LOCAL_AUTOMATION_STATUS) {
    if (!status || typeof status !== "object" || !Object.keys(status).length) {
      return {
        available: false,
        tone: "unavailable",
        label: "Unavailable",
        summary: "The optional ignored local status feed is not present; no health conclusion is inferred."
      };
    }
    const checkedAt = parseTimestamp(
      status.updated_at || status.completed_at || status.started_at
    );
    if (checkedAt !== null && Date.now() - checkedAt > 36 * 60 * 60 * 1000) {
      return {
        available: false,
        tone: "unavailable",
        label: "Stale",
        summary: `The ignored local status feed has not been refreshed since ${formatOperationalDate(checkedAt)}.`
      };
    }
    const value = String(status.status || "").toLowerCase();
    if (value === "completed") {
      return {
        available: true,
        tone: "success",
        label: "Completed",
        summary: status.failure_reason || "The local-only transaction completed."
      };
    }
    if (value === "review-required") {
      return {
        available: true,
        tone: "warning",
        label: "Review required",
        summary: status.failure_reason || "The preserved transaction requires Benjamin's review."
      };
    }
    if (["failed", "blocked", "usage-stopped", "missed"].includes(value)) {
      return {
        available: true,
        tone: "error",
        label: value.replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()),
        summary: status.failure_reason || "The local transaction stopped and preserved its state."
      };
    }
    if (value === "running") {
      return {
        available: true,
        tone: "warning",
        label: "Running",
        summary: `The local transaction is active at ${status.stage || "an unreported stage"}.`
      };
    }
    return {
      available: true,
      tone: "warning",
      label: value ? value.replaceAll("-", " ") : "Unknown status",
      summary: status.failure_reason || "The local feed is present but does not report a terminal success."
    };
  }

  function renderLocalAutomationStatus() {
    const status = window.ARRP_LOCAL_AUTOMATION_STATUS;
    const presentation = localAutomationPresentation(status);
    const note = byId("local-automation-note");
    const summary = byId("local-automation-summary");
    if (!note || !summary) return;
    const controlState = String(status?.control_state || "").toLowerCase();
    const controlLabel = controlState === "run"
      ? "Run"
      : controlState === "paused"
        ? "Paused"
        : "Unavailable";
    note.className = `attention-note ${
      controlState === "paused" ? "warning" : presentation.tone
    }`.trim();
    note.textContent = `${controlLabel} · ${presentation.label} · ${presentation.summary}`;
    summary.replaceChildren(
      integrityMetric("State", controlLabel, `Checked ${formatDate(status?.control_state_checked_at)}`),
      integrityMetric("Latest scheduled", presentation.label, formatDate(status?.completed_at || status?.updated_at)),
      integrityMetric("Next scheduled", formatOperationalDate(nextScheduledCoordinatorRun()), controlState === "paused" ? "Intentionally suppressed while Paused" : "Owner-only local schedule"),
      integrityMetric("Currentness", status?.updated_at ? "Current feed" : "Unavailable", status?.updated_at ? `Updated ${formatDate(status.updated_at)}` : "No owner-only status loaded")
    );
  }

  function elimRunChainPresentation(chain = {}) {
    const decision = chain.elim || chain.elim_decision || {};
    const runtime = matchingElimRuntime(chain.elim_runtime, chain.chain_id);
    if (runtime) {
      const runtimeStatus = runtime.status || chain.host_status || "completed";
      return {
        label: overviewStagePresentation(runtimeStatus).statusLabel,
        detail: runtime.summary || runtime.details || decision.reason
          || "The host recorded this Elim execution.",
        ran: true
      };
    }
    const launched = decision.launched ?? decision.launch
      ?? decision.launch_recommended ?? chain.elim_launched;
    return {
      label: launched === true
        ? "Launched"
        : launched === false
          ? "Not launched"
          : decision.decision || "Awaiting decision",
      detail: decision.reason || chain.elim_reason || "No launch reason recorded",
      ran: launched === true
    };
  }

  function renderRunChain() {
    const chain = data.run_chain || {};
    const stages = runChainStages(chain);
    const queue = runChainQueue(chain);
    const epoch = chain.review_epoch || {};
    const usage = chain.usage || chain.usage_summary || {};
    const chainId = chain.chain_id || chain.id || "Awaiting baseline";
    const status = chain.status || chain.outcome || (stages.length ? "In progress" : "Not yet published");
    const queueAvailable = Object.keys(queue).length > 0;
    const queueTotal = queueAvailable
      ? runChainCount(queue, "total")
        || ["human", "llm", "agent", "bot", "blocked"].reduce((sum, key) => sum + runChainCount(queue, key), 0)
      : null;
    const elimEligible = runChainCount(queue, "elim_eligible")
      || runChainCount(queue, "llm")
      || runChainCount(queue, "agent");
    const failures = Array.isArray(chain.failures) ? chain.failures : [];
    const degradations = Array.isArray(chain.degradations) ? chain.degradations : [];
    const elimPresentation = elimRunChainPresentation(chain);
    const remaining = usage.remaining_percent ?? usage.remaining ?? usage.applicable_remaining_percent;
    const consumed = usage.consumed_percent ?? usage.consumed;
    const usageLabel = remaining !== undefined && remaining !== null
      ? `${remaining}% remaining`
      : consumed !== undefined && consumed !== null
        ? `${consumed}% consumed`
        : "Not recorded";
    const nextReview = epoch.next_review_at || epoch.next_review || epoch.next || epoch.due_at;
    const cloudStatus = chain.cloud_status
      ? String(chain.cloud_status).replaceAll("_", " ")
      : "not reported";
    const hostStatus = chain.host_status
      ? String(chain.host_status).replaceAll("_", " ")
      : "not yet reported";
    const hostCommit = chain.host_closeout?.commit
      ? ` · Commit ${String(chain.host_closeout.commit).slice(0, 12)}`
      : "";
    const phaseDetail = `Cloud ${cloudStatus} · Host ${hostStatus}${hostCommit}`;

    const note = byId("automation-chain-note");
    note.className = `attention-note ${runChainStatusClass(status)}`.trim();
    const hasPublishedChain = Boolean(chain.chain_id || chain.id || chain.status || chain.outcome);
    note.textContent = hasPublishedChain
      ? `${chainId} · ${String(status).replaceAll("_", " ")} · ${phaseDetail} · ${chain.trigger || chain.trigger_type || "trigger not recorded"}`
      : "Awaiting the first Run Coordinator Bot projection. No chain health conclusion is available yet.";

    const runStrip = byId("operations-run-strip");
    if (runStrip) {
      runStrip.replaceChildren(...overviewRunChainStages(chain).map((stage, index) => {
        const card = element("a", `operations-run-stage ${stage.tone}`.trim());
        card.href = stage.id === "elim"
          ? "#automation:agents:elim"
          : stage.id === "public-intake"
            ? "#planning:candidates"
            : `#automation:agents:${stage.id}`;
        card.append(
          element("span", "overview-stage-number", String(index + 1)),
          element("strong", "", stage.label),
          element("span", `status-badge ${stage.tone}`, stage.statusLabel)
        );
        if (stage.activeIncidentIds.length) {
          card.append(element("span", "micro-note", stage.activeIncidentIds.join(", ")));
          card.href = `#automation:logs:incidents:selected=${encodeURIComponent(stage.activeIncidentIds[0])}`;
        }
        card.setAttribute(
          "aria-label",
          `Stage ${index + 1}, ${stage.label}: ${stage.statusLabel}`
        );
        return card;
      }));
    }

    byId("automation-chain-summary").replaceChildren(
      integrityMetric("Chain", chainId, `Baseline ${String(chain.baseline_commit || "not recorded").slice(0, 12)}`),
      integrityMetric("Health", String(status).replaceAll("_", " "), `${phaseDetail} · ${failures.length} failed · ${degradations.length} degraded`),
      integrityMetric("Work queue", queueTotal ?? "Unavailable", queueAvailable
        ? `${runChainCount(queue, "human")} human · ${elimEligible} Elim-eligible · ${runChainCount(queue, "safety")} safety-sensitive`
        : "The producer did not publish queue counts; zero is not inferred."),
      integrityMetric("Elim", elimPresentation.label, elimPresentation.detail),
      integrityMetric("Review epoch", epoch.review_id || epoch.id || "Not established", nextReview ? `Next ${formatDate(nextReview)}` : "Next review not recorded"),
      integrityMetric("Usage", usageLabel, usage.stop_reason || usage.gate || "15% reserve applies")
    );

    byId("automation-chain-stage-count").textContent = stages.length;
    const stageRows = stages.map((stage, index) => {
      const item = element("details", "automation-chain-stage");
      const presentation = stageExecutionPresentation(stage);
      const heading = element("summary", "");
      heading.append(
        element("span", "automation-stage-order", String(index + 1)),
        element("strong", "", stage.name || stage.id || `Stage ${index + 1}`),
        element("span", `status-badge ${presentation.tone}`, presentation.statusLabel)
      );
      const details = element("dl", "automation-stage-fields");
      [
        ["Current chain", presentation.currentChainLabel],
        ["Due", stage.due === undefined ? "Not recorded" : stage.due ? "Yes" : "No"],
        ["Latest successful execution", formatDate(presentation.lastSuccessAt)],
        ["Schedule detail", presentation.scheduleDetail || "No additional scheduling detail recorded"],
        ["Started", formatDate(stage.started_at || stage.started || stage.timestamps?.started_at || stage.timestamps?.started)],
        ["Latest recorded activity", formatDate(stage.completed_at || stage.completed || stage.updated_at || stage.timestamps?.completed_at || stage.timestamps?.completed)],
        ["Retries", Array.isArray(stage.retries) ? stage.retries.length : stage.retries ?? stage.retry_count ?? 0],
        ["Output", stage.output || stage.output_path || "No output path recorded"],
        ["Hash", stage.output_hash || "Not recorded"],
        ["Diagnostic", stage.diagnostic || stage.reason || stage.message || "No exception recorded"]
      ].forEach(([label, value]) => details.append(element("dt", "", label), element("dd", "", String(value ?? "Not recorded"))));
      item.append(heading, details);
      return item;
    });
    byId("automation-chain-stage-list").replaceChildren(...(stageRows.length
      ? stageRows
      : [element("p", "empty-state compact-empty", "No run-chain stages have been published.")]));
  }

  function renderGovernanceReviewSpecialist(chain = data.run_chain || {}) {
    const compactRecord = chain.work_queue?.governance_discovery;
    const record = compactRecord
      || chain.governance_review
      || chain.project_governance_review
      || chain.work_queue?.governance_review
      || data.overview?.automation_summary?.governance_review
      || {};
    const lastReview = record.last_review && typeof record.last_review === "object"
      ? record.last_review
      : {};
    const host = byId("governance-review-specialist-detail");
    const badge = byId("governance-review-specialist-status");
    if (!host || !badge) return;
    if (!Object.keys(record).length) {
      badge.className = "status-badge unavailable";
      badge.textContent = "Unavailable";
      host.replaceChildren(element("p", "empty-state compact-empty", "No typed governance-review projection is available; no no-finding conclusion is inferred."));
      if (byId("governance-discovery-status")) byId("governance-discovery-status").textContent = "Governance-review and discovery mode is unavailable in the loaded projection.";
      return;
    }
    const current = record.current_for_cadence === true || record.current === true;
    const waiting = record.waiting_for_ordinary_queue === true || record.waiting === true;
    const nextDueTimestamp = parseTimestamp(record.next_due_at);
    const due = record.due === true
      || record.selected_as_quiet_queue_fallback === true
      || (!current && !waiting && nextDueTimestamp !== null && nextDueTimestamp <= Date.now());
    const derivedStatus = waiting
      ? "waiting for ordinary queue"
      : due
        ? "due"
        : current
          ? "current"
          : record.status || record.outcome || record.posture;
    const presentation = waiting
      ? { tone: "warning", statusLabel: "Waiting for ordinary queue" }
      : due
        ? { tone: "warning", statusLabel: "Due" }
        : current
          ? { tone: "success", statusLabel: "Current for cadence" }
          : overviewStagePresentation(derivedStatus);
    badge.className = `status-badge ${presentation.tone}`;
    badge.textContent = presentation.statusLabel;
    if (byId("governance-discovery-status")) {
      byId("governance-discovery-status").textContent = `Project governance review and discovery: ${presentation.statusLabel} · ${record.reason_selected || record.selection_reason || record.reason || "selection reason unavailable"}.`;
    }
    const fields = compactRecord ? [
      ["Mode", text(record.mode, "Unavailable")],
      ["Selection policy", text(record.ordinary_selection_policy, "Unavailable")],
      ["Minimum interval", record.minimum_interval_hours == null ? "Unavailable" : `${record.minimum_interval_hours} hours`],
      ["Current / due", due ? "Due now" : waiting ? "Waiting behind ordinary eligible work" : current ? "Current for cadence" : "Due posture unavailable"],
      ["Selected as quiet-queue fallback", record.selected_as_quiet_queue_fallback === true ? "Yes" : record.selected_as_quiet_queue_fallback === false ? "No" : "Unavailable"],
      ["Ordinary eligible work before fallback", text(record.ordinary_eligible_count_before_fallback, "Unavailable")],
      ["Reason", text(record.reason, "Unavailable")],
      ["Next due", formatDate(record.next_due_at)],
      ["Last reviewed", formatDate(lastReview.last_reviewed_at)],
      ["Last review identities", `run ${text(lastReview.run_id, "Unavailable")} · selected unit ${text(lastReview.selected_unit_id, "Unavailable")} · discovered unit ${text(lastReview.discovered_work_unit_id, "Unavailable")}`],
      ["Last review revision / disposition", `${text(lastReview.source_revision, "Unavailable")} · ${text(lastReview.disposition, "Unavailable")}`],
      ["Next trigger", text(lastReview.next_trigger, "Unavailable")]
    ] : [
      ["Current / due", due ? "Due now" : waiting ? "Waiting behind ordinary eligible work" : current ? "Current for cadence" : record.next_due_at ? `Next due ${formatDate(record.next_due_at)}` : "Due posture unavailable"],
      ["Last run", formatDate(record.last_run_at || record.completed_at || record.checked_at)],
      ["Selection reason", record.selection_reason || record.reason_selected || record.reason || "Unavailable"],
      ["Legacy detail", "This compatibility projection predates the compact governance-discovery contract; open its canonical record for complete findings and validation."]
    ];
    const grid = element("dl", "governance-review-fields");
    fields.forEach(([label, value]) => grid.append(element("dt", "", label), element("dd", "", String(value))));
    host.replaceChildren(grid);
    const links = element("div", "source-list compact-links");
    const canonicalDetail = lastReview.canonical_detail || record.canonical_detail;
    [
      ["Open governance record ↗", record.canonical_url || record.url || (canonicalDetail ? `${GITHUB_BLOB_ROOT}${canonicalDetail}` : "")],
      ["Open report ↗", lastReview.report_url || record.report_url],
      ["Open validation ↗", lastReview.validation_url || record.validation_url]
    ].forEach(([label, url]) => {
      if (url) links.append(linkButton(label, url, true));
    });
    if (links.childNodes.length) host.append(links);
  }

  function operationsLedgerRow(label, state, detail, timestamp, link = null) {
    const row = element("article", "operations-ledger-row");
    const identity = element("div");
    identity.append(
      element("strong", "", label),
      element("span", `status-badge ${state.tone || "unavailable"}`, state.label || "Unavailable")
    );
    const copy = element("div");
    copy.append(
      element("p", "", detail || "No detail is recorded."),
      element("p", "micro-note", timestamp ? `Checked ${formatOperationalDate(timestamp)}` : "Checked time unavailable")
    );
    row.append(identity, copy);
    if (link) row.append(link.startsWith("http")
      ? inlineLink("Open source ↗", link)
      : internalInlineLink("Open source →", link));
    return row;
  }

  function downloadSecurityWorkOrder(filename, workOrder) {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob(
      [JSON.stringify({ schema_version: 1, requested_at: new Date().toISOString(), ...workOrder }, null, 2)],
      { type: "application/json" }
    ));
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function securityWorkOrderButton(label, filename, workOrder) {
    const button = element("button", "record-link secondary", label);
    button.type = "button";
    button.addEventListener("click", () => downloadSecurityWorkOrder(filename, workOrder));
    return button;
  }

  function renderSecurityRemediation() {
    const projection = securityAssuranceProjection();
    const status = byId("operations-security-status");
    const summary = byId("operations-security-summary");
    const host = byId("operations-security-list");
    const preview = byId("operations-security-preview");
    if (!status || !summary || !host || !preview) return;
    const currentChecks = projection.tools.filter((tool) => tool.coverage_state === "current").length;
    status.textContent = projection.available
      ? `Authenticated assurance checked ${formatOperationalDate(projection.checkedAt)}. Check completion is not a claim that no vulnerability exists.`
      : "Authenticated security assurance is unavailable; absence of private findings is not inferred.";
    const summaryValues = [
      ["Public intake", projection.publicIntakeState === "live" ? "Live" : projection.publicIntakeState === "paused" ? "Paused" : "Unverified"],
      ["Check coverage", projection.available ? `${currentChecks} of ${projection.tools.length} current` : "Unavailable"],
      ["Private attention", projection.privateAttention === "required" ? "Required" : projection.privateAttention === "none_reported" ? "None reported" : "Unavailable"],
      ["Security incident", projection.activeIncident ? "Active" : projection.available ? "None linked" : "Unavailable"]
    ];
    summary.replaceChildren(...summaryValues.map(([label, value]) => {
      const cell = element("div", "metric-card compact-metric");
      cell.append(element("span", "metric-label", label), element("strong", "", value));
      return cell;
    }));
    let selectedId = projection.tools[0]?.tool_id || null;
    const renderPreview = (tool) => {
      if (!tool) {
        preview.replaceChildren(element("p", "empty-state", "Security check definitions are unavailable."));
        return;
      }
      const heading = element("div", "email-preview-heading");
      heading.append(element("div", "", ""), element("span", `status-badge ${tool.coverage_state === "current" ? "success" : tool.coverage_state === "stale" || tool.coverage_state === "incomplete" ? "warning" : "unavailable"}`, tool.coverage_state || "unavailable"));
      heading.firstChild.append(element("span", "record-id", tool.tool_id), element("h3", "", tool.label || "Registered security check"));
      const fields = element("dl", "email-preview-fields");
      [
        ["Owner", tool.owner_class || "Unavailable"],
        ["Last checked", tool.last_checked ? formatOperationalDate(tool.last_checked) : "Unavailable"],
        ["Next due", tool.next_due ? formatOperationalDate(tool.next_due) : "Unavailable"],
        ["Private attention", tool.private_attention === "yes" ? "Required" : tool.private_attention === "no" ? "None reported" : "Unknown"],
        ["Source revision", tool.source_revision || "Unavailable"],
        ["Destination", tool.destination_class || "Unavailable"]
      ].forEach(([term, value]) => {
        const field = element("div", "email-preview-field");
        field.append(element("dt", "", term), element("dd", "", value));
        fields.append(field);
      });
      const links = element("div", "source-list compact-links");
      links.append(inlineLink("Open protected source ↗", "https://github.com/Thorncrag/ARRP/security"));
      if (tool.active_incident) links.append(internalInlineLink("View incident history →", "automation:logs:incidents"));
      if (tool.tool_id === "public-intake-protection") {
        const sharedRequest = {
          action: "prepare_public_intake_state_request",
          scope: ["form", "public_apis", "collector", "elim_intake_review", "replies"],
          required_readback: "exact_authorized_state",
          mixed_state_response: "record_operational_incident",
          execution: "staged_request_only"
        };
        links.append(
          securityWorkOrderButton(
            "Prepare Live request",
            "arrp-public-intake-live-request.json",
            { ...sharedRequest, requested_state: "live" }
          ),
          securityWorkOrderButton(
            "Prepare Paused request",
            "arrp-public-intake-paused-request.json",
            { ...sharedRequest, requested_state: "paused" }
          )
        );
      }
      preview.replaceChildren(heading, element("p", "automation-purpose", tool.purpose || "High-level scope unavailable."), fields, links);
    };
    const selectTool = (tool) => {
      selectedId = tool.tool_id;
      host.querySelectorAll(".email-list-row").forEach((row) => {
        const selected = row.dataset.toolId === selectedId;
        row.classList.toggle("selected", selected);
        row.setAttribute("aria-selected", selected ? "true" : "false");
      });
      renderPreview(tool);
    };
    host.replaceChildren(...projection.tools.map((tool) => {
      const row = element("button", "email-list-row");
      row.type = "button";
      row.dataset.toolId = tool.tool_id;
      row.setAttribute("role", "option");
      const copy = element("span", "email-list-copy");
      copy.append(element("strong", "", tool.label || tool.tool_id), element("span", "email-list-meta", tool.coverage_state || "unavailable"));
      row.append(copy);
      row.addEventListener("click", () => selectTool(tool));
      row.addEventListener("keydown", (event) => {
        const rows = [...host.querySelectorAll(".email-list-row")];
        const index = rows.indexOf(row);
        const nextIndex = event.key === "ArrowDown"
          ? Math.min(rows.length - 1, index + 1)
          : event.key === "ArrowUp"
            ? Math.max(0, index - 1)
            : event.key === "Home"
              ? 0
              : event.key === "End"
                ? rows.length - 1
                : null;
        if (nextIndex === null || nextIndex === index) return;
        event.preventDefault();
        const nextTool = projection.tools[nextIndex];
        selectTool(nextTool);
        rows[nextIndex].focus();
      });
      return row;
    }));
    selectTool(projection.tools.find((tool) => tool.tool_id === selectedId) || projection.tools[0]);
    const prepare = byId("prepare-security-review");
    if (prepare && !prepare.dataset.bound) {
      prepare.dataset.bound = "true";
      prepare.addEventListener("click", () => downloadSecurityWorkOrder(
        "arrp-security-review-work-order.json",
        {
          action: "prepare_read_only_security_review",
          allowed_actions: ["read_only_verification", "protected_source_routing"],
          prohibited_actions: ["credential_mutation", "provider_disposition", "arbitrary_command_execution"]
        }
      ));
    }
    const refresh = byId("refresh-security-status");
    if (refresh && !refresh.dataset.bound) {
      refresh.dataset.bound = "true";
      refresh.addEventListener("click", () => downloadSecurityWorkOrder(
        "arrp-security-status-refresh-request.json",
        {
          action: "refresh_authenticated_security_assurance",
          allowed_actions: ["read_only_provider_status", "minimized_projection_refresh"],
          prohibited_actions: ["credential_mutation", "provider_disposition", "arbitrary_command_execution"]
        }
      ));
    }
    setButtonBlockerFlag(
      "automation-tab-security",
      projection.activeIncident,
      "An active operational incident is represented in Security"
    );
  }

  function renderOperationsLedgers(chain = data.run_chain || {}) {
    const gates = data.overview?.automation_readiness?.future_run_gates || {};
    const chainBlockers = failedAutomationStages(chain);
    const gateBlockers = gates.available === true
      ? (Array.isArray(gates.items) ? gates.items : [])
      : [];
    setButtonBlockerFlag(
      "automation-tab-overview",
      chainBlockers.length > 0,
      `${pluralizeWord(chainBlockers.length, "current automation blocker")} represented in Operations overview`
    );
    setButtonBlockerFlag(
      "automation-tab-gates",
      gateBlockers.length > 0,
      `${pluralizeWord(gateBlockers.length, "forward automation blocker")} represented in Repository gates`
    );
    const gateHost = byId("operations-gates-list");
    if (gateHost) {
      if (gates.available !== true) {
        gateHost.replaceChildren(operationsLedgerRow(
          "Automation-blocking pull requests",
          { tone: "unavailable", label: "Unavailable" },
          gates.reason || "The producer has not declared a complete typed blocker inventory.",
          gates.checked_at,
          "logs:agents"
        ));
      } else if (!(gates.items || []).length) {
        gateHost.replaceChildren(operationsLedgerRow(
          "Automation-blocking pull requests",
          { tone: "success", label: "None open" },
          "No open pull request is explicitly typed as blocking future automation.",
          gates.checked_at
        ));
      } else {
        gateHost.replaceChildren(...gates.items.map((gate) => {
          const row = operationsLedgerRow(
            `Pull request #${gate.number || gate.id || "—"}`,
            { tone: "error", label: "Blocks automation" },
            gate.title || gate.reason || "Typed automation gate",
            gate.updated_at || gates.checked_at,
            gate.url || "logs:agents"
          );
          (gate.active_incident_ids || []).forEach((incidentId) => {
            row.append(consoleLinkButton(
              `${incidentId} →`,
              `#automation:logs:incidents:selected=${encodeURIComponent(incidentId)}`
            ));
          });
          return row;
        }));
      }
    }

    const usage = chain.usage || data.overview?.usage || {};
    const usageGate = usage.gate || {};
    const remaining = usageGate.lowestRemainingPercent ?? usage.remaining_percent;
    const capacityBlocked = Number.isFinite(Number(remaining))
      && Number(remaining) <= Number(usageGate.reservePercent ?? 15);
    setButtonBlockerFlag(
      "automation-tab-capacity",
      capacityBlocked,
      "Codex capacity is at or below the automation reserve"
    );
    const capacitySummary = byId("operations-capacity-summary");
    if (capacitySummary) {
      capacitySummary.replaceChildren(
        operationsLedgerRow(
          "Current reserve posture",
          Number.isFinite(Number(remaining))
            ? { tone: Number(remaining) <= Number(usageGate.reservePercent ?? 15) ? "error" : "success", label: `${remaining}% remaining` }
            : { tone: "unavailable", label: "Unavailable" },
          `${usageGate.reservePercent ?? 15}% hard reserve · ${usageGate.runBudget?.softTargetPercent ?? 10}-point soft run target`,
          usageGate.checkedAtUtc || chain.updated_at
        ),
        operationsLedgerRow(
          "Full Review Epoch",
          { tone: chain.review_epoch?.due ? "warning" : "success", label: chain.review_epoch?.due ? "Due" : "Scheduled" },
          `Last completed ${formatOperationalDate(chain.review_epoch?.last_completed_at)} · next due ${formatOperationalDate(chain.review_epoch?.next_due_at)}`,
          chain.review_epoch?.last_completed_at
        )
      );
    }
    const capacityHistory = byId("operations-capacity-history");
    if (capacityHistory) {
      const points = (projectLog("elim")?.entries || []).map((entry) => ({
        id: entry.id,
        date: entry.values?.date,
        value: elimUsageConsumption(entry)
      })).filter((point) => Number.isFinite(point.value)).slice(-12).reverse();
      capacityHistory.replaceChildren(
        logHistoryHeading("Measured consumption history", points.length, "run"),
        ...points.map((point) => operationsLedgerRow(
          point.id,
          { tone: "success", label: `${point.value} points` },
          "Measured Elim consumption for this run.",
          point.date,
          "logs:elim"
        ))
      );
    }

    const services = platformCellProjection();
    const platformBlocked = services.some((service) =>
      ["major_outage", "partial_outage", "unavailable"].includes(service.status));
    setButtonBlockerFlag(
      "automation-tab-platform",
      platformBlocked,
      "A platform outage represented in this screen may block automation"
    );
    const platformHost = byId("operations-platform-list");
    if (platformHost) {
      const providerRows = [];
      let priorProvider = "";
      services.forEach((service) => {
        if (service.provider !== priorProvider) {
          const providerHeading = element("div", "operations-ledger-provider");
          providerHeading.append(
            element("strong", "", service.provider),
            inlineLink("Official source ↗", service.source)
          );
          providerRows.push(providerHeading);
          priorProvider = service.provider;
        }
        const presentation = platformStatusPresentation(service.status);
        const retained = service.lastValid?.checkedAt
          ? ` · last valid ${formatOperationalDate(service.lastValid.checkedAt)}`
          : "";
        const relevantIncidents = (service.incidents || []).length
          ? ` · ${pluralizeWord(service.incidents.length, "relevant provider incident")}`
          : " · no relevant provider incident returned";
        const row = operationsLedgerRow(
          service.label,
          { tone: presentation.tone, label: serviceStatusLabel(service.status) },
          `${service.detail}${relevantIncidents}${retained}`,
          service.checkedAt,
          service.source
        );
        activeIncidentIdsForTypedLink(`platform:${layoutSlug(service.label)}`).forEach((incidentId) => {
          row.append(consoleLinkButton(
            `${incidentId} →`,
            `#automation:logs:incidents:selected=${encodeURIComponent(incidentId)}`
          ));
        });
        providerRows.push(row);
      });
      platformHost.replaceChildren(...providerRows);
    }

    const intake = publicInputSnapshot(chain);
    const operationsProgressFeed = Object.keys(data.progress || {}).length ? data.progress : data.overview?.progress_summary;
    const operationsSourceFeed = Object.keys(data.source_checker || {}).length ? data.source_checker : data.overview?.source_checker_summary;
    const operationsIntegrityFeed = Object.keys(data.integrity || {}).length ? data.integrity : data.overview?.integrity_summary;
    const feedSpecs = [
      ["Progress", operationsProgressFeed, operationsProgressFeed?.generated_at || operationsProgressFeed?.generatedAt, "progress"],
      ["Sources", operationsSourceFeed, operationsSourceFeed?.checked_at, "sources:watchers"],
      ["Operations overview", chain, chain.updated_at || chain.completed_at, "automation:overview"],
      ["Candidates", { availability: "current", completeness: { complete: true } }, data.generated_at, "candidates"],
      ["Public input", { availability: intake.available ? "current" : "unavailable" }, intake.checkedAt, "candidates:public"],
      ["Integrity", operationsIntegrityFeed, operationsIntegrityFeed?.current?.generated_at || operationsIntegrityFeed?.generated_at, "integrity"]
    ];
    const dataBlocked = feedSpecs.some(([, feed, timestamp]) => {
      const state = feedContractState(feed || {}, timestamp);
      return !state.complete || ["unavailable", "incomplete"].includes(state.state);
    });
    setButtonBlockerFlag(
      "automation-tab-data",
      dataBlocked,
      "Unavailable or incomplete project data represented in this screen blocks reliable use"
    );
    const incidentBlocking = incidentIdsIncludeBlocker(
      unresolvedOperationalIncidents().map((incident) => incident.incident_id)
    );
    setButtonBlockerFlag(
      "tab-automation",
      incidentBlocking || chainBlockers.length > 0 || gateBlockers.length > 0 || capacityBlocked || platformBlocked || dataBlocked,
      "An operational blocker is represented in Operations"
    );
    const dataHost = byId("operations-data-list");
    if (dataHost) {
      dataHost.replaceChildren(...feedSpecs.map(([label, feed, timestamp, route]) => {
        const state = feedContractState(feed || {}, timestamp);
        const row = operationsLedgerRow(
          label,
          {
            tone: state.complete && state.state !== "stale"
              ? "success"
              : state.state === "unavailable"
                ? "unavailable"
                : "error",
            label: state.label
          },
          state.reason || (state.complete ? "The producer declares this projection complete." : "The producer does not establish a complete current projection."),
          state.timestamp || timestamp,
          route
        );
        activeIncidentIdsForTypedLink(`data:${layoutSlug(label)}`).forEach((incidentId) => {
          row.append(consoleLinkButton(
            `${incidentId} →`,
            `#automation:logs:incidents:selected=${encodeURIComponent(incidentId)}`
          ));
        });
        return row;
      }));
    }
  }

  function humanizeKey(value) {
    return String(value || "")
      .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
      .replaceAll("_", " ")
      .replaceAll("-", " ")
      .replace(/\b\w/g, (character) => character.toUpperCase());
  }

  function automationConfigurationInput(path, value) {
    const row = element("label", "automation-config-control");
    const key = path[path.length - 1];
    row.append(element("span", "", humanizeKey(key)));
    let control;
    if (typeof value === "boolean") {
      control = element("select", "");
      control.append(
        element("option", "", "True"),
        element("option", "", "False")
      );
      control.options[0].value = "true";
      control.options[1].value = "false";
      control.value = String(value);
      control.dataset.valueType = "boolean";
    } else if (typeof value === "number") {
      control = element("input", "");
      control.type = "number";
      control.step = Number.isInteger(value) ? "1" : "any";
      control.value = String(value);
      control.dataset.valueType = "number";
    } else if (Array.isArray(value)) {
      control = element("textarea", "automation-config-json");
      control.rows = Math.min(8, Math.max(2, JSON.stringify(value, null, 2).split("\n").length));
      control.value = JSON.stringify(value, null, 2);
      control.dataset.valueType = "json";
    } else if (value && typeof value === "object") {
      control = element("textarea", "automation-config-json");
      control.rows = Math.min(10, Math.max(3, JSON.stringify(value, null, 2).split("\n").length));
      control.value = JSON.stringify(value, null, 2);
      control.dataset.valueType = "json";
    } else {
      control = element("input", "");
      control.type = "text";
      control.value = value ?? "";
      control.dataset.valueType = value === null ? "null" : "string";
    }
    control.dataset.configPath = JSON.stringify(path);
    row.append(control);
    return row;
  }

  function automationConfigurationFields(configuration) {
    const fields = element("div", "automation-config-fields");
    Object.entries(configuration || {}).forEach(([key, value]) => {
      if (value && typeof value === "object" && !Array.isArray(value)) {
        const group = element("fieldset", "automation-config-group");
        group.append(element("legend", "", humanizeKey(key)));
        Object.entries(value).forEach(([nestedKey, nestedValue]) => {
          group.append(automationConfigurationInput([key, nestedKey], nestedValue));
        });
        fields.append(group);
      } else {
        fields.append(automationConfigurationInput([key], value));
      }
    });
    return fields;
  }

  function setConfigurationPath(target, path, value) {
    let cursor = target;
    path.slice(0, -1).forEach((part) => {
      if (!cursor[part] || typeof cursor[part] !== "object" || Array.isArray(cursor[part])) {
        cursor[part] = {};
      }
      cursor = cursor[part];
    });
    cursor[path[path.length - 1]] = value;
  }

  function configurationControlValue(control) {
    if (control.dataset.valueType === "boolean") return control.value === "true";
    if (control.dataset.valueType === "number") {
      const value = Number(control.value);
      if (!Number.isFinite(value)) throw new Error("Enter a valid number.");
      return value;
    }
    if (control.dataset.valueType === "json") return JSON.parse(control.value);
    if (control.dataset.valueType === "null" && !control.value.trim()) return null;
    return control.value;
  }

  function configurationFromPanel(panel, original) {
    const next = JSON.parse(JSON.stringify(original || {}));
    panel.querySelectorAll("[data-config-path]").forEach((control) => {
      const path = JSON.parse(control.dataset.configPath);
      setConfigurationPath(next, path, configurationControlValue(control));
    });
    return next;
  }

  function downloadConsoleFile(filename, content, type = "application/json") {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const download = document.createElement("a");
    download.href = url;
    download.download = filename;
    document.body.append(download);
    download.click();
    download.remove();
    URL.revokeObjectURL(url);
  }

  function automationConfigurationPanel(record) {
    const configuration = record.runtime_configuration;
    if (!configuration || typeof configuration !== "object" || !Object.keys(configuration).length) {
      return null;
    }
    const panel = element("details", "automation-config-panel");
    panel.dataset.disclosureId = `automation-config-${record.id}`;
    const summary = element("summary", "");
    summary.append(
      element("strong", "", "Staged configuration"),
      element("span", "overview-row-meta", "Browser-local · collapsed")
    );
    const content = element("div", "automation-config-content");
    const note = element(
      "p",
      "muted",
      "Edits remain only for this open Console session until exported. They do not change the live runner or survive a reload."
    );
    const error = element("p", "warning-text automation-config-error");
    error.hidden = true;
    const fieldsHost = element("div", "");
    const renderFields = () => {
      const draft = automationConfigurationDrafts.get(record.id);
      fieldsHost.replaceChildren(automationConfigurationFields(configuration));
      if (draft?.rawValues) {
        fieldsHost.querySelectorAll("[data-config-path]").forEach((control) => {
          const key = control.dataset.configPath;
          if (!Object.prototype.hasOwnProperty.call(draft.rawValues, key)) return;
          if (control.type === "checkbox") control.checked = draft.rawValues[key] === true;
          else control.value = draft.rawValues[key];
        });
      }
    };
    renderFields();
    const captureDraft = () => {
      const rawValues = {};
      fieldsHost.querySelectorAll("[data-config-path]").forEach((control) => {
        rawValues[control.dataset.configPath] = control.type === "checkbox"
          ? control.checked
          : control.value;
      });
      automationConfigurationDrafts.set(record.id, { rawValues });
    };
    fieldsHost.addEventListener("input", captureDraft);
    fieldsHost.addEventListener("change", captureDraft);
    const actions = element("div", "source-list dossier-actions");
    const exportButton = element("button", "record-link", "Export configuration");
    exportButton.type = "button";
    exportButton.addEventListener("click", () => {
      try {
        const payload = configurationFromPanel(fieldsHost, configuration);
        error.hidden = true;
        const filename = record.runtime_config?.split("/").pop() || `${record.id}.json`;
        downloadConsoleFile(filename, `${JSON.stringify(payload, null, 2)}\n`);
      } catch (caught) {
        error.textContent = `Export blocked: ${caught.message || "a configuration value is invalid."}`;
        error.hidden = false;
      }
    });
    const restoreButton = element("button", "record-link secondary", "Restore loaded values");
    restoreButton.type = "button";
    restoreButton.addEventListener("click", () => {
      automationConfigurationDrafts.delete(record.id);
      renderFields();
      error.hidden = true;
    });
    actions.append(exportButton, restoreButton);
    content.append(note, fieldsHost, error, actions);
    panel.append(summary, content);
    return panel;
  }

  function automationOutcomePresentation(value) {
    const normalized = String(value || "").toLowerCase().replaceAll("_", "-");
    if (/success|succeed|complete|healthy/.test(normalized)) {
      return { tone: "success", label: "Succeeded" };
    }
    if (/pause|suppress|skip/.test(normalized)) {
      return { tone: "warning", label: "Paused" };
    }
    if (/fail|block|error|miss/.test(normalized)) {
      return { tone: "error", label: "Failed" };
    }
    if (/running|progress|pending/.test(normalized)) {
      return { tone: "warning", label: "Running" };
    }
    return { tone: "unavailable", label: "Unavailable" };
  }

  function effectiveAutomationRoleStatusProjection(
    projection = data.automation_role_status,
    localStatus = window.ARRP_LOCAL_AUTOMATION_STATUS
  ) {
    const source = projection && typeof projection === "object"
      ? projection
      : { availability: "unavailable", roles: [] };
    const roles = (Array.isArray(source.roles) ? source.roles : []).map((role) => ({
      ...role,
      latest_scheduled: { ...(role.latest_scheduled || {}) },
      last_successful: { ...(role.last_successful || {}) },
      data_currentness: { ...(role.data_currentness || {}) },
      current_blocker: role.current_blocker && typeof role.current_blocker === "object"
        ? { ...role.current_blocker }
        : null
    }));
    const controlValue = String(localStatus?.control_state || "").toLowerCase();
    const exactControl = ["run", "paused"].includes(controlValue)
      ? {
          state: controlValue,
          source: "owner-only-local-status",
          checked_at: localStatus.control_state_checked_at || localStatus.updated_at,
          reason: ""
        }
      : { ...(source.control_state || {}) };
    roles.forEach((role) => { role.pause_state = exactControl.state || "unavailable"; });

    const coordinator = roles.find((role) => role.id === "run-coordinator-bot");
    if (coordinator && String(localStatus?.trigger || "").toLowerCase() === "scheduled") {
      coordinator.latest_scheduled = {
        available: true,
        outcome: localStatus.status || "unavailable",
        at: localStatus.completed_at || localStatus.updated_at || localStatus.scheduled_for,
        scheduled_for: localStatus.scheduled_for,
        source: "owner-only-local-status",
        run_id: localStatus.run_id,
        reason: localStatus.failure_reason || ""
      };
      if (/complete|success/i.test(String(localStatus.status || ""))) {
        coordinator.last_successful = {
          available: true,
          at: localStatus.completed_at || localStatus.updated_at,
          source: "owner-only-local-status",
          reason: ""
        };
      }
      if (/fail|block|error|miss/i.test(String(localStatus.status || ""))) {
        coordinator.current_blocker = {
          id: localStatus.run_id || "local-scheduled-attempt",
          summary: localStatus.failure_reason || "The latest scheduled local attempt failed.",
          route: "automation:overview"
        };
      }
      coordinator.checked_at = localStatus.updated_at || coordinator.checked_at;
    }
    return {
      ...source,
      control_state: exactControl,
      roles
    };
  }

  function automationRoleRecords() {
    const projection = effectiveAutomationRoleStatusProjection();
    const registry = new Map(data.agent_registry.map((record) => [record.id, record]));
    return [...projection.roles]
      .sort((left, right) =>
        Number(left.display_order || 999) - Number(right.display_order || 999)
        || String(left.display_name || left.id).localeCompare(String(right.display_name || right.id)))
      .map((status) => ({
        ...status,
        registry: registry.get(status.id) || null
      }));
  }

  function automationRoleProblem(role) {
    if (role.current_blocker) {
      return {
        tone: "error",
        label: role.current_blocker.summary || "Current blocker"
      };
    }
    const currentness = String(role.data_currentness?.state || "").toLowerCase();
    if (["stale", "error", "failed"].includes(currentness)) {
      return {
        tone: "error",
        label: role.data_currentness?.reason || `Data ${currentness}`
      };
    }
    if (!currentness || ["unavailable", "unknown"].includes(currentness)) {
      return {
        tone: "unavailable",
        label: role.data_currentness?.reason || "Currentness unavailable"
      };
    }
    return null;
  }

  function renderAutomationRoleMenu() {
    const host = byId("operations-role-menu-list");
    if (!host) return;
    const roles = automationRoleRecords();
    host.replaceChildren(...roles.map((role) => {
      const link = element("a", "compact-specialist-menu-item", role.menu_label || role.display_name || role.id);
      link.href = `#automation:agents:${role.id}`;
      link.dataset.automationRole = role.id;
      link.setAttribute("aria-current", role.id === automationRoleState.selectedId ? "page" : "false");
      link.tabIndex = role.id === automationRoleState.selectedId ? 0 : -1;
      if (role.current_blocker || incidentIdsIncludeBlocker(role.active_incident_ids)) {
        const dot = element("span", "nav-flag-dot error");
        dot.setAttribute("aria-label", "Current blocker or linked operational incident");
        link.append(dot);
      }
      return link;
    }));
  }

  function renderAutomationRoleDetail() {
    const host = byId("automation-role-detail");
    if (!host) return;
    const role = automationRoleRecords().find((candidate) =>
      candidate.id === automationRoleState.selectedId);
    if (!role) {
      const unavailable = element("section", "automation-role-unavailable");
      unavailable.append(
        element("span", "eyebrow", "Unavailable role"),
        element("h3", "", automationRoleState.unavailableId || "Unknown role"),
        element(
          "p",
          "",
          "This role is unknown or retired in the loaded typed registry. No other role has been selected in its place."
        ),
        consoleLinkButton("Open Coordinator →", "#automation:agents:run-coordinator-bot")
      );
      host.replaceChildren(unavailable);
      return;
    }
    const registry = role.registry || {};
    const latest = role.latest_scheduled || {};
    const presentation = latest.available === true
      ? automationOutcomePresentation(latest.outcome)
      : { tone: "unavailable", label: "Unavailable" };
    const problem = automationRoleProblem(role);
    const view = element("article", `automation-role-workspace${problem?.tone === "error" ? " has-error" : ""}`);
    const heading = element("div", "automation-role-heading");
    const identity = element("div");
    identity.append(
      element("span", "eyebrow", `${role.role_type || "Role"} detail`),
      element("h3", "", role.display_name || registry.name || role.id),
      element("p", "automation-purpose", registry.purpose || "Purpose not recorded.")
    );
    const status = element("div", "automation-role-posture");
    status.append(
      element("span", `status-badge ${presentation.tone}`, presentation.label),
      element("time", "", latest.available === true ? formatDate(latest.at) : "Date unavailable")
    );
    heading.append(identity, status);

    const details = element("dl", "automation-role-fields");
    [
      ["Current execution posture", `${presentation.label}${latest.available === true ? ` · ${formatDate(latest.at)}` : ` · ${latest.reason || "No typed occurrence"}`}`],
      ["Last successful occurrence", role.last_successful?.available === true ? formatDate(role.last_successful.at) : role.last_successful?.reason || "Unavailable"],
      ["Trigger", String(registry.trigger || "Not recorded").replaceAll("-", " ")],
      ["Cadence", role.cadence || registry.schedule || "Not recorded"],
      ["Eligibility", role.eligibility || "Not recorded"],
      ["Authority", String(registry.status || "Not recorded").replaceAll("-", " ")],
      ["Environment", String(registry.execution_environment || "Not recorded").replaceAll("-", " ")],
      ["Runtime", registry.runtime_id || "Not recorded"],
      ["Data currentness", `${String(role.data_currentness?.state || "unavailable").replaceAll("-", " ")} · ${role.data_currentness?.reason || "No additional detail"}`],
      ["Checked", formatDate(role.checked_at)]
    ].forEach(([label, value]) => {
      details.append(element("dt", "", label), element("dd", "", value));
    });

    const recovery = element("section", `automation-role-recovery ${problem?.tone || "success"}`);
    recovery.append(
      element("h4", "", problem ? "Current exception" : "Recovery"),
      element("p", "", problem?.label || "No current blocker is recorded for this role.")
    );
    const linkedIncidents = operationalIncidentsById(role.active_incident_ids);
    const incidentLinks = element("section", "automation-role-incidents");
    incidentLinks.append(element("h4", "", "Linked operational incidents"));
    if (linkedIncidents.length) {
      const list = element("ul", "");
      linkedIncidents.forEach((incident) => {
        const row = element("li", "");
        row.append(
          consoleLinkButton(
            `${incident.incident_id} · ${incident.summary} →`,
            `#automation:logs:incidents:selected=${encodeURIComponent(incident.incident_id)}`
          )
        );
        list.append(row);
      });
      incidentLinks.append(list);
    } else {
      incidentLinks.append(element("p", "micro-note", "No active incident is linked to this role."));
    }

    const links = element("div", "source-list dossier-actions");
    if (registry.runbook_url) links.append(linkButton("View runbook ↗", registry.runbook_url, true));
    if (registry.current_report_url) links.append(linkButton("View current report ↗", registry.current_report_url, true));
    links.append(consoleLinkButton(
      "View history →",
      role.id === "elim"
        ? "#automation:logs:elim"
        : `#automation:logs:agents:${role.id}`
    ));
    if (registry.log_path) links.append(linkButton("View authoritative log ↗", `${GITHUB_BLOB_ROOT}${registry.log_path}`, true));

    view.append(heading, details, recovery, incidentLinks, links);
    if (role.id !== "source-checker-bot") {
      const configuration = automationConfigurationPanel(registry);
      if (configuration) view.append(configuration);
    }
    if (role.id === "elim") {
      const governance = element("section", "governance-review-specialist");
      governance.id = "governance-review-specialist";
      const governanceHeading = element("div", "section-heading-row");
      const governanceIdentity = element("div");
      governanceIdentity.append(
        element("h3", "", "Project governance review and discovery"),
        element("p", "", "Elim-specific periodic governance review, finding disposition, documentation, and validation.")
      );
      const governanceStatus = element("span", "status-badge unavailable", "Unavailable");
      governanceStatus.id = "governance-review-specialist-status";
      governanceHeading.append(governanceIdentity, governanceStatus);
      const governanceDetail = element("div", "governance-review-specialist-detail");
      governanceDetail.id = "governance-review-specialist-detail";
      governance.append(governanceHeading, governanceDetail);
      view.append(governance);
    }
    host.replaceChildren(view);
    if (role.id === "elim") renderGovernanceReviewSpecialist(data.run_chain || {});
    refreshDisclosurePreferences(host);
  }

  function activateAutomationRole(roleId, focus = false, updateHash = true) {
    const roles = automationRoleRecords();
    const exact = roles.find((role) => role.id === roleId);
    automationRoleState.selectedId = exact ? exact.id : "";
    automationRoleState.unavailableId = exact ? "" : String(roleId || "Unknown role");
    renderAutomationRoleMenu();
    renderAutomationRoleDetail();
    const links = [...document.querySelectorAll("[data-automation-role]")];
    const selected = links.find((link) => link.dataset.automationRole === automationRoleState.selectedId);
    if (focus) selected?.focus();
    if (updateHash) {
      const target = exact
        ? `automation:agents:${exact.id}`
        : `automation:agents:${encodeURIComponent(automationRoleState.unavailableId)}`;
      window.history.replaceState(null, "", `#${target}`);
    }
  }

  function initializeAutomationRoleMenu() {
    const host = byId("operations-role-menu-list");
    if (!host || host.dataset.bound) return;
    host.dataset.bound = "true";
    host.addEventListener("click", (event) => {
      const link = event.target.closest("[data-automation-role]");
      if (!link) return;
      event.preventDefault();
      activateAutomationRole(link.dataset.automationRole, false, true);
    });
    host.addEventListener("keydown", (event) => {
      if (!["ArrowRight", "ArrowLeft", "Home", "End"].includes(event.key)) return;
      const links = [...host.querySelectorAll("[data-automation-role]")];
      if (!links.length) return;
      const current = event.target.closest("[data-automation-role]");
      const index = Math.max(0, links.indexOf(current));
      let target = current;
      if (event.key === "ArrowRight") target = links[(index + 1) % links.length];
      if (event.key === "ArrowLeft") target = links[(index - 1 + links.length) % links.length];
      if (event.key === "Home") target = links[0];
      if (event.key === "End") target = links[links.length - 1];
      event.preventDefault();
      activateAutomationRole(target.dataset.automationRole, true, true);
    });
    const parts = normalizeConsoleTarget(window.location.hash).split(":");
    activateAutomationRole(
      parts[0] === "automation" && parts[1] === "agents"
        ? decodeURIComponent(parts[2] || "run-coordinator-bot")
        : "run-coordinator-bot",
      false,
      false
    );
  }

  function renderAutomation() {
    const chain = data.run_chain || {};
    captureSuccessfulStageHistory(chain);
    renderOperationsLedgers(chain);
    renderSecurityRemediation();
    renderLocalAutomationStatus();
    renderRunChain();

    const roles = automationRoleRecords();
    const roleBlockers = roles.filter((role) => role.current_blocker);
    setButtonBlockerFlag(
      "automation-tab-agents",
      roleBlockers.length > 0,
      `${pluralizeWord(roleBlockers.length, "automation blocker")} represented in Agents & Bots`
    );
    byId("automation-overview-grid")?.replaceChildren(...roles.map((role) => {
      const latest = role.latest_scheduled || {};
      const presentation = latest.available === true
        ? automationOutcomePresentation(latest.outcome)
        : { tone: "unavailable", label: "Unavailable" };
      const problem = automationRoleProblem(role);
      const card = element("a", `automation-overview-card ${problem?.tone || presentation.tone}`.trim());
      card.href = `#automation:agents:${role.id}`;
      card.dataset.layoutId = `automation-overview-${role.id}`;
      card.append(
        element("strong", "", role.display_name || role.id),
        element("span", "automation-role-type", role.role_type || "Role"),
        element(
          "p",
          "automation-role-occurrence",
          latest.available === true
            ? `${presentation.label} · ${formatDate(latest.at)}`
            : `Latest scheduled attempt unavailable`
        ),
        element("span", "automation-role-cadence", role.cadence || "Cadence unavailable")
      );
      if (problem) {
        const flag = element("span", `automation-role-problem ${problem.tone}`, problem.label);
        card.append(flag);
      }
      card.setAttribute(
        "aria-label",
        `${role.display_name || role.id}, ${role.role_type || "role"}: ${presentation.label}. Open role details.`
      );
      return card;
    }));

    const incidentProjection = operationalIncidentProjection();
    const incidents = unresolvedOperationalIncidents();
    const representedRoleIds = new Set(
      roles
        .filter((role) => (role.active_incident_ids || []).length)
        .map((role) => role.id)
    );
    const roleExceptions = roles.filter((role) =>
      automationRoleProblem(role) && !representedRoleIds.has(role.id));
    const exceptionCount = incidentProjection.complete
      ? incidents.length + roleExceptions.length
      : null;
    byId("automation-incident-count").textContent = exceptionCount == null ? "—" : exceptionCount;
    const incidentRows = incidents.map((incident) => {
      const row = element("article", "automation-incident-card");
      row.append(
        element("strong", "", `${incident.incident_id} · ${incident.summary}`),
        element("p", "", `${incident.component} · ${incident.owner || "Unassigned owner"}`),
        element("p", "warning-text", incident.next_action || "Exact next action is unavailable.")
      );
      const links = element("div", "source-list compact-links");
      links.append(consoleLinkButton(
        "Open incident →",
        `#automation:logs:incidents:selected=${encodeURIComponent(incident.incident_id)}`
      ));
      row.append(links);
      return row;
    });
    const roleRows = roleExceptions.map((role) => {
      const problem = automationRoleProblem(role);
      const row = element("article", `automation-incident-card ${problem.tone}`);
      row.append(
        element("strong", "", role.display_name || role.id),
        element("p", "", problem.label)
      );
      row.append(consoleLinkButton("View details →", `#automation:agents:${role.id}`));
      return row;
    });
    byId("automation-incidents").replaceChildren(...(
      exceptionCount == null
        ? [element("p", "empty-state compact-empty", incidentProjection.reason || "Operational incident feed is unavailable; zero incidents cannot be inferred.")]
        : exceptionCount
        ? [...incidentRows, ...roleRows]
        : [element("p", "empty-state compact-empty", "No current operational exception is represented in the loaded typed projection.")]
    ));
    updateIncidentNavigationCounts();

    if (!automationRoleState.selectedId
      && roles.some((role) => role.id === automationRoleState.unavailableId)) {
      automationRoleState.selectedId = automationRoleState.unavailableId;
      automationRoleState.unavailableId = "";
    }
    renderAutomationRoleMenu();
    if (!automationRoleState.selectedId && !automationRoleState.unavailableId) {
      automationRoleState.selectedId = "run-coordinator-bot";
    }
    renderAutomationRoleDetail();
    refreshLayoutZones();
  }

  function runChainTimestamp(snapshot) {
    if (!snapshot || typeof snapshot !== "object") return 0;
    for (const value of [
      snapshot.host_updated_at,
      snapshot.updated_at,
      snapshot.completed_at,
      snapshot.created_at
    ]) {
      const parsed = Date.parse(value || "");
      if (Number.isFinite(parsed)) return parsed;
    }
    return 0;
  }

  function matchingElimRuntime(runtime, chainId) {
    return runtime
      && typeof runtime === "object"
      && String(runtime.chain_id || "") === String(chainId || "")
      ? runtime
      : undefined;
  }

  function mergeRunChainRows(left = [], right = []) {
    const rows = new Map();
    [...left, ...right]
      .filter((row) => row && typeof row === "object")
      .forEach((row) => {
        const key = JSON.stringify([
          row.stage_id || row.stage || row.id || "",
          row.recorded_at || row.completed_at || "",
          row.message || row.details || ""
        ]);
        rows.set(key, row);
      });
    return [...rows.values()];
  }

  function cloudRunChainSnapshot(snapshot) {
    const cloud = {
      ...snapshot,
      cloud_status: snapshot.status,
      cloud_updated_at: snapshot.updated_at || snapshot.completed_at || snapshot.created_at,
      status_source: "cloud"
    };
    const launchRecommended = snapshot.elim_decision?.launch_recommended === true
      || snapshot.elim?.launch_recommended === true;
    if (/^complete$/i.test(String(snapshot.status || "")) && launchRecommended) {
      cloud.status = "host_pending";
      cloud.cloud_next_action = snapshot.next_action;
      cloud.next_action = "The deterministic cloud chain completed; the final host and Elim result is not yet available on this surface.";
    }
    return cloud;
  }

  function reconcileRunChainSnapshot(current, incoming, source) {
    if (!incoming || typeof incoming !== "object" || Array.isArray(incoming)) {
      return current || {};
    }
    const currentSnapshot = current && typeof current === "object" ? current : {};
    const hostSource = source === "local" || source === "host";
    const reportedHostStatus = hostSource
      ? String(incoming.host_status || "")
      : "";
    const candidate = hostSource
      ? {
          ...incoming,
          status: reportedHostStatus || incoming.status,
          host_status: reportedHostStatus || undefined,
          host_updated_at: reportedHostStatus
            ? incoming.host_updated_at || incoming.updated_at || incoming.completed_at
            : undefined,
          status_source: reportedHostStatus
            ? source === "local" ? "local-host" : "published-host"
            : source === "local" ? "local-cache" : "published-host-cache"
        }
      : cloudRunChainSnapshot(incoming);
    const sameChain = String(currentSnapshot.chain_id || "") === String(candidate.chain_id || "");
    const sharedHostState = {
      host_action_items: hostSource
        ? candidate.host_action_items
        : currentSnapshot.host_action_items,
      host_action_item_history: hostSource
        ? candidate.host_action_item_history
        : currentSnapshot.host_action_item_history
    };

    if (!sameChain) {
      const newer = runChainTimestamp(candidate) >= runChainTimestamp(currentSnapshot)
        ? candidate
        : currentSnapshot;
      const merged = { ...newer };
      Object.entries(sharedHostState).forEach(([key, value]) => {
        if (value !== undefined) merged[key] = value;
      });
      const runtime = matchingElimRuntime(
        newer.elim_runtime,
        newer.chain_id
      );
      if (runtime) merged.elim_runtime = runtime;
      else delete merged.elim_runtime;
      return merged;
    }

    const currentIsHost = ["local-host", "published-host"].includes(currentSnapshot.status_source)
      || Boolean(currentSnapshot.host_status);
    const candidateIsHost = ["local-host", "published-host"].includes(candidate.status_source);
    const hostSnapshot = candidateIsHost
      ? currentIsHost && runChainTimestamp(currentSnapshot) > runChainTimestamp(candidate)
        ? currentSnapshot
        : candidate
      : currentIsHost
        ? currentSnapshot
        : null;
    if (hostSnapshot) {
      if (hostSnapshot.host_action_items !== undefined) {
        sharedHostState.host_action_items = hostSnapshot.host_action_items;
      }
      if (hostSnapshot.host_action_item_history !== undefined) {
        sharedHostState.host_action_item_history = hostSnapshot.host_action_item_history;
      }
    }
    const cloudSnapshot = candidateIsHost ? currentSnapshot : candidate;
    const merged = {
      ...cloudSnapshot,
      ...currentSnapshot,
      ...candidate,
      failures: mergeRunChainRows(
        currentSnapshot.failures,
        candidate.failures
      ),
      degradations: mergeRunChainRows(
        currentSnapshot.degradations,
        candidate.degradations
      )
    };
    if (hostSnapshot) {
      merged.status = hostSnapshot.host_status || hostSnapshot.status;
      merged.host_status = hostSnapshot.host_status || hostSnapshot.status;
      merged.host_updated_at = hostSnapshot.host_updated_at
        || hostSnapshot.updated_at
        || hostSnapshot.completed_at;
      merged.status_source = hostSnapshot.status_source || "published-host";
    } else if (
      runChainTimestamp(currentSnapshot) > runChainTimestamp(candidate)
    ) {
      merged.status = currentSnapshot.status;
      merged.status_source = currentSnapshot.status_source;
    }
    if (cloudSnapshot.cloud_status || cloudSnapshot.status_source === "cloud") {
      merged.cloud_status = cloudSnapshot.cloud_status || cloudSnapshot.status;
      merged.cloud_updated_at = cloudSnapshot.cloud_updated_at
        || cloudSnapshot.updated_at
        || cloudSnapshot.completed_at;
    }
    Object.entries(sharedHostState).forEach(([key, value]) => {
      if (value !== undefined) merged[key] = value;
    });
    const runtime = matchingElimRuntime(
      hostSnapshot?.elim_runtime || currentSnapshot.elim_runtime,
      merged.chain_id
    );
    if (runtime) merged.elim_runtime = runtime;
    else delete merged.elim_runtime;
    return merged;
  }

  async function refreshLiveRunChain() {
    byId("run-chain-live-note").textContent =
      "Run-chain state is the checked-in projection from the latest local transaction.";
  }

  function canonicalFileConsolePath(pathname) {
    try {
      const decoded = decodeURIComponent(String(pathname || ""));
      return !decoded.includes("\0")
        && !decoded.includes("\\")
        && !/(?:^|\/)\.{1,2}(?:\/|$)/.test(decoded)
        && decoded.endsWith("/research/horizon-review-console/index.html");
    } catch (_error) {
      return false;
    }
  }

  function localConsoleOriginAllowed(location = window.location) {
    const protocol = String(location?.protocol || "");
    const hostname = String(location?.hostname || "");
    if (["http:", "https:"].includes(protocol)) {
      return ["127.0.0.1", "localhost", "::1", "[::1]"].includes(hostname);
    }
    return protocol === "file:"
      && hostname === ""
      && canonicalFileConsolePath(location?.pathname);
  }

  function loadLocalProjection(path, capture) {
    if (!localConsoleOriginAllowed()) return Promise.resolve(false);
    if (capture()) return Promise.resolve(true);
    return new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = path;
      script.onload = () => resolve(capture());
      script.onerror = () => resolve(false);
      document.head.append(script);
    });
  }

  function loadPrivateSecurityAssurance() {
    return loadLocalProjection(
      PRIVATE_SECURITY_ASSURANCE_PATH,
      capturePrivateSecurityAssurance
    );
  }

  function loadPrivateOperations() {
    return loadLocalProjection(PRIVATE_OPERATIONS_PATH, capturePrivateOperations);
  }

  function loadLocalAutomationStatus() {
    return loadLocalProjection(
      LOCAL_AUTOMATION_STATUS_PATH,
      captureLocalAutomationStatus
    );
  }

  async function refreshLiveProgress() {
    byId("progress-live-note").textContent =
      "Progress is the checked-in projection from the latest local transaction.";
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
    byId("log-integrity-visible").textContent = history.length;
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
    const workspace = element("div", "email-workspace log-email-workspace");
    const list = element("div", "email-list log-email-list");
    list.setAttribute("role", "listbox");
    list.setAttribute("aria-label", "Integrity runs, newest first");
    const preview = element("article", "email-preview log-email-preview");
    const showRun = (run, selectedRow) => {
      list.querySelectorAll(".email-list-row").forEach((row) => {
        const selected = row === selectedRow;
        row.classList.toggle("selected", selected);
        row.setAttribute("aria-selected", String(selected));
      });
      const counts = run.counts || {};
      const heading = element("div", "email-preview-heading");
      const title = element("div");
      title.append(element("span", "eyebrow", "Selected run"), element("h3", "", formatDate(run.generated_at)));
      heading.append(title, element("span", run.result === "clean" ? "status-badge ready" : "status-badge needs-review",
        run.result === "clean" ? "Clean" : `${Number(counts.findings) || 0} findings`));
      const fields = element("dl", "email-preview-fields");
      [
        ["Errors", Number(counts.errors) || 0],
        ["Warnings", Number(counts.warnings) || 0],
        ["Duration", run.duration_seconds == null ? "Unavailable" : `${Number(run.duration_seconds).toFixed(1)}s`],
        ["Revision", run.revision || "Unavailable"]
      ].forEach(([label, value]) => {
        const field = element("div", "email-preview-field");
        field.append(element("dt", "", label), element("dd", "", String(value)));
        fields.append(field);
      });
      const links = element("div", "source-list compact-links");
      if (run.revision) links.append(inlineLink("Open commit ↗", `https://github.com/Thorncrag/ARRP/commit/${run.revision}`));
      preview.replaceChildren(heading, fields, links);
    };
    let firstRow = null;
    history.forEach((run) => {
      const counts = run.counts || {};
      const row = element("button", "email-list-row");
      row.type = "button";
      row.setAttribute("role", "option");
      row.append(
        element("strong", "email-row-title", formatDate(run.generated_at)),
        element("span", "email-row-time", run.result === "clean" ? "Clean" : `${Number(counts.findings) || 0} findings`),
        element("span", "email-row-summary", `${Number(counts.errors) || 0} errors · ${Number(counts.warnings) || 0} warnings`)
      );
      row.addEventListener("click", () => showRun(run, row));
      list.append(row);
      if (!firstRow) firstRow = row;
    });
    workspace.append(list, preview);
    host.replaceChildren(workspace);
    showRun(history[0], firstRow);
  }

  function renderIntegrityComponents(feed = data.integrity) {
    const current = feed && typeof feed.current === "object" ? feed.current : {};
    const sourceHealth = feedContractState(data.source_checker, data.source_checker?.checked_at);
    const projectHealth = feedContractState(
      { ...feed, generated_at: current.generated_at, availability: feed.availability },
      current.generated_at
    );
    const progressHealth = feedContractState(data.progress, data.progress?.generatedAt || data.progress?.asOf);
    const automationHealth = operationalFeedState(data.run_chain);
    const sourceExceptions = sourceCheckerRecords().filter((record) =>
      !["verified", "identity-preserving redirect"].includes(record.classification)).length;
    const candidateGaps = candidateProjectRecords()
      .reduce((count, record) => count + (record.dossier_gaps || []).length, 0);
    const componentDelta = (key) => {
      if (key === "source_health") {
        const sourceDelta = sourceCheckerDeltaPresentation(data.source_checker);
        if (!sourceDelta.available) {
          return { available: false, reason: sourceDelta.reason };
        }
        return {
          available: true,
          newCount: sourceDelta.counts.newExceptions,
          regressed: sourceDelta.counts.regressedExceptions,
          resolved: sourceDelta.counts.resolvedExceptions,
          aging: sourceDelta.oldest
            ? `${sourceDelta.oldest.source_id || "source unavailable"} ${text(sourceDelta.oldest.age_days, "Unavailable")}d`
            : sourceDelta.counts.ongoingExceptions === 0
              ? "no ongoing exceptions"
              : "aging detail unavailable"
        };
      }
      const sources = [
        feed.component_deltas?.[key],
        current.component_deltas?.[key],
        (Array.isArray(feed.components) ? feed.components : []).find((record) =>
          [record.id, record.key, record.label].map((value) => layoutSlug(value || "")).includes(layoutSlug(key)))?.delta
      ].filter((record) => record && typeof record === "object");
      const delta = sources[0];
      if (!delta) return null;
      return {
        available: true,
        newCount: delta.new ?? delta.opened ?? delta.added,
        regressed: delta.regressed ?? delta.reopened ?? delta.worsened,
        resolved: delta.resolved ?? delta.closed ?? delta.fixed
      };
    };
    const components = [
      {
        key: "project_consistency",
        label: "Project consistency",
        state: projectHealth,
        value: Number(current.counts?.findings) || 0,
        unit: "deterministic findings",
        source: "Project Integrity Bot",
        revision: current.revision || feed.source_revision,
        owner: "Project Integrity Bot / Elim"
      },
      {
        key: "source_health",
        label: "Source health",
        state: sourceHealth,
        value: sourceExceptions,
        unit: "URL or identity exceptions",
        source: "Source Checker Bot",
        revision: data.source_checker.source_revision || data.source_checker.revision,
        owner: "Source Checker Bot / Elim"
      },
      {
        key: "candidate_completeness",
        label: "Candidate completeness",
        state: progressHealth,
        value: candidateGaps,
        unit: "configured dossier gaps",
        source: "Candidate and Project projections",
        revision: data.progress.source_revision || data.progress.revision,
        owner: "Elim"
      },
      {
        key: "operational_readiness",
        label: "Operational readiness",
        state: automationHealth,
        value: failedAutomationStages().length,
        unit: "current failed stages",
        source: "Run Coordinator chain",
        revision: data.run_chain.source_revision || data.run_chain.revision,
        owner: "Run Coordinator / named recovery owner"
      }
    ];
    byId("integrity-components").replaceChildren(...components.map((component) => {
      const card = element("article", `integrity-component feed-state-${component.state.state}`);
      const delta = componentDelta(component.key);
      const displayedValue = integrityComponentValue(component.state, component.value);
      card.append(
        element("span", "eyebrow", component.label),
        element("strong", "", String(displayedValue)),
        element("p", "", component.unit),
        element("p", "integrity-component-delta", delta?.available
          ? `Δ ${text(delta.newCount, "unavailable")} new · ${text(delta.regressed, "unavailable")} regressed · ${text(delta.resolved, "unavailable")} resolved`
            + (delta.aging ? ` · aging: ${delta.aging}` : "")
          : delta?.reason
            ? `Δ unavailable: ${delta.reason}`
            : "Δ new / regressed / resolved unavailable"),
        element("p", "micro-note", `${component.state.label} · checked ${formatDate(component.state.timestamp)}`),
        element("p", "micro-note", `Source: ${component.source} · revision ${component.revision ? String(component.revision).slice(0, 10) : "unavailable"} · owner ${component.owner}`)
      );
      if (component.state.reason) card.append(element("p", "warning-text", component.state.reason));
      return card;
    }));
  }

  function renderIntegrity(feed = data.integrity) {
    const current = feed && typeof feed.current === "object" ? feed.current : {};
    const problems = exactIntegrityProblemRecords(feed);
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
    const blockingProblems = problems.filter((finding) =>
      finding.blocking === true
      || finding.blocks_automation === true
      || finding.release_blocker === true
    );
    setButtonBlockerFlag(
      "tab-integrity",
      blockingProblems.length > 0,
      `${pluralizeWord(blockingProblems.length, "blocker")} represented in Integrity`
    );
    byId("integrity-as-of").textContent = current.generated_at ? formatDate(current.generated_at) : "Not yet run";
    const status = byId("integrity-status");
    const contract = feedContractState(
      { ...feed, generated_at: current.generated_at, availability: feed.availability },
      current.generated_at
    );
    const structural = validateLivePayload("integrity", feed);
    const feedAvailable = Boolean(current.generated_at)
      && structural.valid
      && !["unavailable", "incomplete"].includes(contract.state);
    setNavigationMarker(
      "tab-integrity-count",
      findingCount,
      feedAvailable ? "" : "error",
      "Integrity unavailable"
    );
    byId("problem-visible").textContent = feedAvailable ? findings.length : "Unavailable";
    status.className = `status-badge ${!feedAvailable || allErrors + allWarnings ? "needs-review" : "ready"}`.trim();
    status.textContent = !feedAvailable
      ? "Integrity feed unavailable"
      : findingCount
        ? `${findingCount} current problem${findingCount === 1 ? "" : "s"}`
        : "No current problems";
    byId("integrity-metrics").replaceChildren(
      integrityMetric("Needs you", feedAvailable ? humanCount : "Unavailable", "reserved decisions or approvals"),
      integrityMetric("Agent-owned", feedAvailable ? agentCount : "Unavailable", "visible work assigned outside the human inbox"),
      integrityMetric("Bot-owned", feedAvailable ? botCount : "Unavailable", "deterministic remediation assigned to a bot"),
      integrityMetric("Observed", feedAvailable ? observedCount : "Unavailable", "readiness or monitoring conditions"),
      integrityMetric("Total", feedAvailable ? findingCount : "Unavailable", feedAvailable ? `${allErrors} errors · ${allWarnings} warnings` : "No valid current Integrity projection is available")
    );

    const grouped = new Map();
    findings.forEach((finding) => {
      const ownerKey = problemOwnerKey(finding);
      if (!grouped.has(ownerKey)) grouped.set(ownerKey, []);
      grouped.get(ownerKey).push(finding);
    });
    const findingHost = byId("integrity-findings");
    if (!feedAvailable) {
      const unavailable = element("div", "empty-state compact-empty");
      unavailable.append(
        element("h3", "", "No valid Integrity feed is available"),
        element("p", "", [...structural.errors, contract.reason].filter(Boolean).join(" ") || "Refresh or rebuild the current Integrity projection before drawing a clean or zero-finding conclusion.")
      );
      findingHost.replaceChildren(unavailable);
    } else if (!findings.length) {
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
          if (finding.source_id) {
            heading.append(finding.source_url?.startsWith("#")
              ? internalInlineLink(finding.source_id, finding.source_url)
              : finding.source_url
                ? inlineLink(finding.source_id, finding.source_url)
                : element("span", "record-id", finding.source_id));
          }
          record.append(heading, element("p", "", finding.message || "Unspecified integrity finding"));
          if ((finding.affected_ids || []).length) {
            const affected = element("div", "problem-affected-records");
            affected.append(element("strong", "", "Affected records:"));
            finding.affected_ids.forEach((identifier) => {
              const target = workbenchTargetForArtifact(identifier, {
                source: "Integrity",
                reference: finding.reference,
                returnTarget: "integrity"
              });
              affected.append(target
                ? internalInlineLink(`Open ${identifier} in Workbench`, target)
                : element("span", "badge", identifier));
            });
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
    renderIntegrityComponents(feed);
    renderIntegrityHistory(feed);
    renderOverview();
  }

  async function refreshLiveIntegrity() {
    byId("integrity-live-note").textContent =
      "Integrity is the checked-in projection from the latest local transaction.";
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
        const resolution = element("div", "publication-conflict-controls");
        const keepEditions = element("button", "secondary", "Keep editions / clear exclusion");
        keepEditions.type = "button";
        keepEditions.setAttribute("aria-label", `Keep edition assignments and clear the print exclusion for ${record.title}`);
        keepEditions.addEventListener("click", () => clearPrintExclusion(record));
        const keepExclusion = element("button", "secondary", "Keep exclusion / clear editions");
        keepExclusion.type = "button";
        keepExclusion.setAttribute("aria-label", `Keep the print exclusion and clear all edition assignments for ${record.title}`);
        keepExclusion.addEventListener("click", () => setPrintLevelDraft(record, []));
        resolution.append(keepEditions, keepExclusion);
        levelsCell.append(resolution);
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
      pageState.page = 1;
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
        pageState.page = 1;
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
        pageState.page = 1;
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
    const pages = Math.max(1, Math.ceil(records.length / PAGE_SIZE));
    pageState.page = Math.min(pageState.page, pages);
    const start = (pageState.page - 1) * PAGE_SIZE;
    byId("pages-visible").textContent = records.length;
    updateDenseDisclosureSummary("pages-results-summary", records.length, "page", `page ${pageState.page} of ${pages}`);
    byId("pages-table").replaceChildren(pageTable(records.slice(start, start + PAGE_SIZE), pageState, renderPages));
    pagination("pages", records.length, pageState, renderPages);
  }

  function publicationEditions() {
    return data.publication.manifest.editions || [];
  }

  function deliveryItems() {
    const candidates = [
      data.delivery_items,
      data.progress?.delivery_items,
      data.progress?.deliveryItems,
      data.publication?.delivery_items,
      data.publication?.deliveryItems,
      data.overview?.publication_summary?.delivery_items
    ];
    return candidates.find(Array.isArray) || [];
  }

  function deliveryProjectionState() {
    const readiness = data.publication?.release_readiness?.delivery_tasks || {};
    const explicitAvailability = readiness.available
      ?? data.publication?.delivery_items_available
      ?? data.delivery_items_available;
    return {
      available: explicitAvailability === true,
      unavailableReason: readiness.unavailable_reason || "Delivery-item projection unavailable."
    };
  }

  function topicProducts() {
    return Array.isArray(data.publication?.topic_products)
      ? data.publication.topic_products
      : undefined;
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
    const basePositions = assemblyPositions(base);
    const draftPositions = assemblyPositions(draft);
    let count = 0;
    draftPositions.forEach((position, path) => {
      if (basePositions.get(path) !== position) count += 1;
    });
    return count;
  }

  function assemblyStructureChanged(editionId = publicationState.edition) {
    if (!assemblyDrafts.has(editionId)) return false;
    const base = baseAssembly(editionId);
    const draft = currentAssembly(editionId);
    return base.sections.map((section) => `${section.id}:${section.paths.join(",")}`).join("|")
      !== draft.sections.map((section) => `${section.id}:${section.paths.join(",")}`).join("|");
  }

  function recordAssemblyOperation(kind, target, detail) {
    const operations = assemblyOperations.get(publicationState.edition) || [];
    operations.push({ kind, target, detail, at: new Date().toISOString() });
    assemblyOperations.set(publicationState.edition, operations);
  }

  function assemblyOperationCount(editionId = publicationState.edition) {
    return (assemblyOperations.get(editionId) || []).length;
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
    recordAssemblyOperation("move-section", sectionId, direction < 0 ? "up" : "down");
    rerenderPreservingFocus(renderDocumentBuilder, `Section moved ${direction < 0 ? "up" : "down"}.`);
  }

  function moveAssemblyPage(path, direction) {
    const draft = ensureAssemblyDraft();
    const section = draft.sections.find((candidate) => candidate.paths.includes(path));
    if (!section) return;
    const index = section.paths.indexOf(path);
    const target = index + direction;
    if (target < 0 || target >= section.paths.length) return;
    [section.paths[index], section.paths[target]] = [section.paths[target], section.paths[index]];
    recordAssemblyOperation("move-page", path, direction < 0 ? "up" : "down");
    rerenderPreservingFocus(renderDocumentBuilder, `Page moved ${direction < 0 ? "up" : "down"}.`);
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
    recordAssemblyOperation("move-page-to-section", path, sectionId);
    rerenderPreservingFocus(renderDocumentBuilder, "Page moved to the selected section.");
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
      unplaced.length || unclassified.length || conflicts.length || missingReasons.length || invalidMetadata.length ? "Assembly blockers detected" : "Assembly structurally valid",
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

  function publicationLengthTable(records, limit = null) {
    const candidates = [...records].sort((left, right) => Number(right.estimated_pages) - Number(left.estimated_pages));
    if (limit !== null) candidates.splice(limit);
    if (!candidates.length) return element("p", "empty-state compact-empty", "No records are present in this view.");
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
    const riskPaths = new Set([...wide, ...long, ...heading].map((record) => record.path));
    const riskRecords = records.filter((record) => riskPaths.has(record.path));
    const build = (data.publication.builds || []).find((record) => record.edition_id === publicationState.edition);
    byId("publication-metrics").replaceChildren(
      publicationMetric("Included records", records.length.toLocaleString(), edition.label),
      publicationMetric("Words", words.toLocaleString(), "Markdown-derived count"),
      publicationMetric("Estimated pages", `~${estimatedPages.toLocaleString()}`, `${data.publication.manifest.words_per_estimated_page} words per page`),
      publicationMetric("Actual build", build?.page_count ? build.page_count.toLocaleString() : "—", build ? (build.stale ? "Existing PDF is stale" : "Existing PDF is current") : "No registered build"),
      publicationMetric("Layout review", riskPaths.size.toLocaleString(), `${wide.length} wide-table · ${long.length} long-page · ${heading.length} heading flags across the distinct union`),
      publicationMetric("Shared pages", multiEdition.length.toLocaleString(), "Also assigned to another edition")
    );
    renderPublicationComposition(sections);
    renderPublicationPreflight(records, sections, publicationState.edition);
    byId("publication-length-risks").replaceChildren(publicationLengthTable(riskRecords));
    byId("publication-largest-pages").replaceChildren(publicationLengthTable(records, 30));
    renderPublicationDelivery();
    renderPublicationReleaseBlockers();
    renderTopicProducts();
    renderReleaseReadiness(records, sections, build);
  }

  function renderPublicationDelivery() {
    const items = deliveryItems();
    const projection = deliveryProjectionState();
    const statusCounts = items.reduce((counts, item) => {
      const status = text(item.status || item.workflow_status, "Unavailable");
      counts.set(status, (counts.get(status) || 0) + 1);
      return counts;
    }, new Map());
    byId("publication-delivery-summary").textContent = projection.available
      ? `${items.length} non-proposal delivery items · excluded from Progress metrics`
      : `${projection.unavailableReason} No empty conclusion is inferred.`;
    byId("publication-delivery-metrics").replaceChildren(
      publicationMetric("Delivery items", projection.available ? items.length : "Unavailable", "tracked separately from proposals and candidates"),
      ...[...statusCounts.entries()].slice(0, 4).map(([status, count]) =>
        publicationMetric(status, count, "typed delivery workflow status"))
    );
    byId("publication-delivery-list").replaceChildren(...(items.length ? items.map((item, index) => {
      const card = element("article", "publication-delivery-card");
      const parentCompleted = item.parent_completion ?? item.parent_complete ?? item.parent?.complete;
      const subissueCompleted = item.subissue_completion ?? item.subissues_complete ?? item.subissues?.complete;
      card.append(
        element("span", "record-id", item.id || item.identifier || `Delivery ${index + 1}`),
        element("h4", "", item.title || item.name || "Untitled delivery item"),
        element("p", "", item.summary || item.next_action || "No delivery detail recorded."),
        dossierSection("Milestone", text(item.milestone || item.milestone_title, "Unavailable")),
        dossierSection("Parent / subissue completion", `${text(parentCompleted, "Unavailable")} / ${text(subissueCompleted, "Unavailable")}`),
        dossierSection("Dependency", text(item.dependency || item.dependencies, "Unavailable")),
        dossierSection("Required validation", text(item.required_validation || item.validation_required || item.validation, "Unavailable")),
        dossierSection("Exact next action", text(item.exact_next_action || item.next_action, "Unavailable")),
        element("p", "micro-note", `Status: ${text(item.status || item.workflow_status, "Unavailable")} · owner: ${text(item.owner, "Unassigned")} · priority: ${text(item.priority, "Unassigned")} · blocker: ${text(item.blocker || item.release_blocker, "Unavailable")}`)
      );
      if (item.url || item.issue_url || item.canonical_url) card.append(linkButton("Open delivery record ↗", item.url || item.issue_url || item.canonical_url, true));
      return card;
    }) : [element("p", "empty-state compact-empty", "The loaded data does not include non-proposal delivery items. These are not counted as zero and are never added to Progress metrics.")]));
  }

  function releaseBlockerDetail(record) {
    const value = record.releaseBlocker ?? record.release_blocker;
    return typedReleaseBlocker(value) ? text(value) : null;
  }

  function releaseBlockerCanonicalUrl(record) {
    const direct = record.url || record.issue_url || record.canonical_url || record.github_url;
    if (direct) return direct;
    const path = record.canonicalRecord || record.canonical_record || record.path;
    return path ? `${GITHUB_BLOB_ROOT}${String(path).replace(/^\.?\//, "")}` : "";
  }

  function releaseBlockerType(record) {
    const kind = String(record.kind || record.type || "").toLowerCase();
    if (kind === "proposal") return "Proposal";
    if (kind === "horizon" || kind === "candidate" || /^HOR-/i.test(String(record.identifier || record.id || ""))) {
      return "Formal candidate";
    }
    if (kind && !["issue", "project item", "project-item"].includes(kind)) return "Delivery work";
    return "Project work item (type unavailable)";
  }

  function releaseBlockerRecords() {
    const lifecycle = currentLifecycleRecords();
    const delivery = deliveryItems().map((record) => ({ ...record, kind: record.kind || "delivery" }));
    const declared = data.publication?.release_readiness?.release_blockers?.items || [];
    const records = new Map();
    [...lifecycle, ...delivery]
      .filter((record) => releaseBlockerDetail(record) !== null)
      .forEach((record, index) => {
        const identifier = record.identifier || record.id || record.projectItemId || `release-blocker-${index + 1}`;
        records.set(String(identifier), {
          ...record,
          identifier: String(identifier),
          recordType: releaseBlockerType(record),
          workflowStatus: record.workflowStatus || record.workflow_status || record.status,
          canonicalUrl: releaseBlockerCanonicalUrl(record)
        });
      });
    declared.forEach((record, index) => {
      const identifier = record.identifier || record.id || record.projectItemId || `declared-release-blocker-${index + 1}`;
      const existing = records.get(String(identifier)) || {};
      records.set(String(identifier), {
        ...record,
        ...existing,
        releaseBlocker: existing.releaseBlocker ?? existing.release_blocker
          ?? record.releaseBlocker ?? record.release_blocker ?? "Yes",
        identifier: String(identifier),
        recordType: existing.recordType || releaseBlockerType(record),
        workflowStatus: existing.workflowStatus || record.workflowStatus || record.workflow_status || record.status,
        canonicalUrl: existing.canonicalUrl || releaseBlockerCanonicalUrl(record)
      });
    });
    return [...records.values()].sort((left, right) =>
      String(left.recordType).localeCompare(String(right.recordType))
      || String(left.identifier).localeCompare(String(right.identifier)));
  }

  function releaseBlockerProjectionState(records = releaseBlockerRecords()) {
    const readiness = data.publication?.release_readiness?.release_blockers || {};
    const reconciliation = data.progress?.projectItemReconciliation
      || data.progress?.project_item_reconciliation || {};
    const expected = Number(readiness.count ?? reconciliation.releaseBlockers);
    const declaredAvailable = readiness.available === true
      || reconciliation.releaseBlockerFieldProjected === true;
    return {
      available: records.length > 0 || declaredAvailable,
      expected: Number.isFinite(expected) ? expected : null,
      mismatch: Number.isFinite(expected) && expected !== records.length,
      unavailableReason: readiness.unavailable_reason
        || "Typed Project Release blocker fields are unavailable."
    };
  }

  function renderPublicationReleaseBlockers() {
    const records = releaseBlockerRecords();
    const projection = releaseBlockerProjectionState(records);
    const statusValue = (record) => text(record.workflowStatus, "Unassigned");
    const priorityValue = (record) => text(record.priority, "Unassigned");
    const ownerValue = (record) => text(record.owner || record.assignee, "Unassigned");
    const actionableBlockers = records.filter((record) =>
      !["Blocked", "Deferred"].includes(record.workflowStatus)
    );
    setButtonBlockerFlag(
      "planning-tab-publication",
      actionableBlockers.length > 0,
      `${pluralizeWord(actionableBlockers.length, "blocker")} represented in Publication`
    );
    setButtonBlockerFlag(
      "publication-tab-analysis",
      actionableBlockers.length > 0,
      `${pluralizeWord(actionableBlockers.length, "blocker")} represented in release analysis`
    );
    const statuses = [...new Set(records.map(statusValue))];
    const priorities = [...new Set(records.map(priorityValue))];
    const owners = [...new Set(records.map(ownerValue))];
    if (releaseBlockerState.status !== "all" && !statuses.includes(releaseBlockerState.status)) releaseBlockerState.status = "all";
    if (releaseBlockerState.priority !== "all" && !priorities.includes(releaseBlockerState.priority)) releaseBlockerState.priority = "all";
    if (releaseBlockerState.owner !== "all" && !owners.includes(releaseBlockerState.owner)) releaseBlockerState.owner = "all";
    populateSelect(byId("publication-blocker-status"), statuses, "All statuses");
    populateSelect(byId("publication-blocker-priority"), priorities, "All priorities");
    populateSelect(byId("publication-blocker-owner"), owners, "All owners");
    byId("publication-blocker-status").value = releaseBlockerState.status;
    byId("publication-blocker-priority").value = releaseBlockerState.priority;
    byId("publication-blocker-owner").value = releaseBlockerState.owner;
    const filtered = records.filter((record) =>
      (releaseBlockerState.status === "all" || statusValue(record) === releaseBlockerState.status)
      && (releaseBlockerState.priority === "all" || priorityValue(record) === releaseBlockerState.priority)
      && (releaseBlockerState.owner === "all" || ownerValue(record) === releaseBlockerState.owner));
    byId("publication-release-blockers-summary").textContent = projection.available
      ? `${filtered.length} of ${records.length} typed blockers${projection.mismatch ? ` · producer declares ${projection.expected}; reconcile this mismatch` : ""}`
      : `${projection.unavailableReason} No zero-blocker conclusion is inferred.`;
    byId("publication-release-blockers-list").replaceChildren(...(filtered.length
      ? filtered.map((record) => {
        const card = element("article", "publication-delivery-card");
        card.append(
          element("span", "record-id", record.identifier),
          element("h4", "", record.title || record.name || "Untitled release blocker"),
          element("p", "", record.summary || record.explanation || record.next_action || "No blocker rationale is recorded in this projection."),
          dossierSection("Work type", record.recordType),
          dossierSection("Status", statusValue(record)),
          dossierSection("Priority", priorityValue(record)),
          dossierSection("Owner", ownerValue(record)),
          dossierSection("Area / workstream", text(record.area || record.workstream, "Unassigned")),
          dossierSection("Release blocker field", releaseBlockerDetail(record) || "Declared by publication readiness"),
          dossierSection("Dependency", text(record.dependency || record.dependencies || record.blocker, "Unavailable")),
          dossierSection("Exact next action", text(record.exact_next_action || record.next_action || record.nextAudit, "Unavailable"))
        );
        const workbenchTarget = workbenchTargetForArtifact(record.identifier, {
          source: "Publication",
          reference: record.identifier,
          returnTarget: "planning:publication:analysis"
        });
        if (workbenchTarget) card.append(internalInlineLink("Open in Workbench", workbenchTarget));
        if (record.canonicalUrl) card.append(linkButton("Open canonical record ↗", record.canonicalUrl, true));
        return card;
      })
      : [element(
        "p",
        "empty-state compact-empty",
        projection.available
          ? records.length
            ? "No release blockers match the current filters."
            : "The complete typed projection contains no release blockers."
          : "The release-blocker worklist is unavailable; absence is not treated as zero."
      )]));
  }

  function renderTopicProducts() {
    const products = topicProducts();
    const available = Array.isArray(products);
    byId("topic-products-summary").textContent = available
      ? `${products.length} stable topic product${products.length === 1 ? "" : "s"}`
      : "Topic-product projection unavailable; no product identity is inferred from page paths";
    byId("topic-products-list").replaceChildren(...(available && products.length ? products.map((product, index) => {
      const card = element("article", "topic-product-card");
      const productId = product.product_id || product.id || `Topic ${index + 1}`;
      const stages = Array.isArray(product.stages) ? product.stages : [];
      card.append(
        element("span", "record-id", productId),
        element("h4", "", product.title || product.name || "Untitled topic product"),
        element("p", "", product.summary || "Stable publication product; not an issue, proposal, candidate, or evidence record."),
        dossierSection("Current stage", text(product.current_stage, "Unavailable")),
        dossierSection("Product status", text(product.product_status || product.status || product.release_status, "Unavailable")),
        dossierSection("Owner", text(product.owner, "Unavailable")),
        dossierSection("Prerequisites", text(product.prerequisites || product.dependencies || product.validation_requirement, "Unavailable")),
        dossierSection("Transition decision", text(product.transition_decision || product.next_transition || product.next_action, "Unavailable")),
        element("p", "micro-note", "Stable product identity · no issue ID · no Development level · no Score · no Runs")
      );
      const links = element("div", "source-list compact-links");
      stages.forEach((stage) => {
        const href = stage.url || (stage.path ? `${GITHUB_BLOB_ROOT}${String(stage.path).replace(/^\.?\//, "")}` : "");
        const label = `${stage.stage_id || stage.id || "Stage"}${stage.available === false ? " (unavailable)" : ""}`;
        if (href) links.append(linkButton(`${label} ↗`, href, true));
        else links.append(element("span", "muted", `${label}: route unavailable`));
      });
      if (product.crosswalk_url) links.append(linkButton("Open internal crosswalk ↗", product.crosswalk_url, true));
      if (product.published_url || product.url) links.append(linkButton("Open published topic ↗", product.published_url || product.url, true));
      card.append(links);
      return card;
    }) : [element(
      "p",
      "empty-state compact-empty",
      available
        ? "The complete typed projection contains no topic products."
        : "Typed topic-product data is unavailable. Topic pages are not treated as stable products without a canonical mapping."
    )]));
  }

  function renderReleaseReadiness(records, sections, build) {
    const readiness = data.publication.release_readiness || data.publication.releaseReadiness || {};
    const dispositions = data.publication.disposition_counts || {};
    const unplaced = sections.find((section) => section.id === "unplaced")?.records?.length || 0;
    const structuralBlockers = Number(dispositions.unclassified || 0)
      + Number(dispositions.conflict || 0)
      + unplaced;
    const typedState = (value) => value === true ? true : value === false ? false : null;
    const delivery = deliveryItems();
    const terminalDelivery = delivery.filter((item) => /complete|closed|done|validated|released/i.test(String(item.status || item.workflow_status || ""))).length;
    const deliveryState = readiness.delivery_tasks || {};
    const blockerState = readiness.release_blockers || {};
    const auditState = readiness.required_audits || {};
    const reviewState = readiness.external_review || {};
    const validationState = readiness.link_export_validation || {};
    const lineageState = readiness.export_lineage || {};
    const stalePdfState = readiness.stale_pdf || {};
    const referencesState = readiness.cross_edition_references || {};
    const rightsState = readiness.copyright_reuse || {};
    const integrityState = readiness.integrity_validation || {};
    const approvalState = readiness.human_go_no_go || {};
    const blockerCount = Number(blockerState.count ?? readiness.release_blocker_count);
    const exportHashes = lineageState.input_hashes || readiness.input_hashes || readiness.export_input_hashes;
    const deliveryAvailable = deliveryState.available === true && deliveryState.source_complete !== false;
    const releaseBlockersAvailable = blockerState.available === true && blockerState.source_complete !== false;
    const auditsAvailable = auditState.available === true && auditState.source_complete !== false
      && auditState.control_fields_complete !== false;
    const reviewAvailable = reviewState.available === true && reviewState.source_complete !== false;
    const checks = [
      { label: "Assembly structurally valid", state: structuralBlockers === 0, detail: structuralBlockers ? `${structuralBlockers} structural blocker(s)` : `${records.length} included records placed` },
      { label: "Delivery tasks", state: deliveryAvailable ? terminalDelivery === delivery.length && Number(deliveryState.incomplete_metadata_count || 0) === 0 : null, detail: deliveryAvailable ? `${terminalDelivery} of ${delivery.length} delivery tasks complete` : deliveryState.unavailable_reason || "Delivery-task projection unavailable" },
      { label: "Release blockers", state: releaseBlockersAvailable && Number.isFinite(blockerCount) ? blockerCount === 0 : null, detail: releaseBlockersAvailable && Number.isFinite(blockerCount) ? `${blockerCount} typed release blockers` : blockerState.unavailable_reason || "Release-blocker count unavailable" },
      { label: "Required audits", state: auditsAvailable ? Number(auditState.count || 0) === 0 : null, detail: auditsAvailable ? `${Number(auditState.count || 0)} required audits remain` : auditState.unavailable_reason || `${text(auditState.known_count, "Unknown")} known audit items; completion controls are incomplete` },
      { label: "External / qualified review", state: reviewAvailable ? Number(reviewState.count || 0) === 0 : null, detail: reviewAvailable ? `${Number(reviewState.count || 0)} external-review items remain` : reviewState.completion_requirement || "External-review completion not declared" },
      { label: "Link validation", state: validationState.link_inventory_available === true ? Number(validationState.missing_link_count || 0) === 0 : null, detail: validationState.link_inventory_available === true ? `${Number(validationState.missing_link_count || 0)} missing links in ${Number(validationState.internal_link_count || 0)} internal links` : validationState.unavailable_reason || "Link validation not declared" },
      { label: "Export validation", state: validationState.export_validation_available === true ? /pass|complete|valid/i.test(String(validationState.export_validation_status || "")) : null, detail: validationState.export_validation_available === true ? text(validationState.export_validation_status) : validationState.unavailable_reason || "Export validation not declared" },
      { label: "Export revision and input hashes", state: lineageState.available === true && lineageState.build_source_revision && exportHashes ? true : null, detail: lineageState.available === true && lineageState.build_source_revision && exportHashes ? `Revision ${String(lineageState.build_source_revision).slice(0, 12)} · ${Object.keys(exportHashes).length} input hash(es)` : lineageState.unavailable_reason || "Export revision or input hashes unavailable" },
      { label: "Current PDF / stale build", state: stalePdfState.revision_backed_status === "current" ? true : stalePdfState.revision_backed_status === "stale" ? false : null, detail: stalePdfState.explanation || (build ? (build.stale ? "Registered PDF is stale" : `${build.page_count || "Unknown"}-page build; revision-backed state unavailable`) : "No registered PDF build") },
      { label: "Cross-edition references", state: referencesState.available === true ? typedState(referencesState.disposition_complete) : null, detail: referencesState.explanation || "Cross-edition reference validation not declared" },
      { label: "Copyright, reuse, and attribution", state: rightsState.status ? /complete|approved|cleared/i.test(String(rightsState.status)) : null, detail: rightsState.status ? `${serviceStatusLabel(rightsState.status)} · third-party review ${text(rightsState.third_party_reuse_review, "unavailable")}` : "Copyright/reuse review not declared" },
      { label: "Integrity validation", state: integrityState.available === true ? /clean|pass|valid/i.test(String(integrityState.result)) : null, detail: integrityState.available === true ? `${serviceStatusLabel(integrityState.result)} at revision ${String(integrityState.revision || "unavailable").slice(0, 12)}` : "Integrity validation unavailable" },
      { label: "Human go / no-go", state: approvalState.decision === "go" || approvalState.decision === true ? true : approvalState.decision === "no-go" || approvalState.decision === false || approvalState.status === "human_decision_required" ? false : null, detail: approvalState.decision ? `Human decision: ${approvalState.decision}` : approvalState.question || "Human decision not recorded" }
    ];
    const ready = checks.every((check) => check.state === true);
    const status = byId("release-readiness-status");
    status.className = `status-badge ${ready ? "ready" : "needs-review"}`;
    status.textContent = ready ? "Release ready" : "Not release ready";
    byId("release-readiness-grid").replaceChildren(...checks.map(({ label, state, detail }) => {
      const card = element("article", `release-readiness-card ${state === true ? "ready" : state === false ? "needs-review" : "unavailable"}`);
      card.append(
        element("strong", "", label),
        element("span", `status-badge ${state === true ? "ready" : state === false ? "needs-review" : "unavailable"}`, state === true ? "Complete" : state === false ? "Incomplete" : "Unavailable"),
        element("p", "", detail)
      );
      return card;
    }));
  }

  function assemblyControl(label, disabled, handler, focusKey = "", visibleLabel = label) {
    const button = element("button", "assembly-control", visibleLabel);
    button.type = "button";
    button.disabled = disabled;
    button.setAttribute("aria-label", label);
    if (focusKey) button.dataset.focusKey = focusKey;
    button.addEventListener("click", handler);
    return button;
  }

  function renderAssemblyToolbar() {
    const affected = assemblyChangeCount();
    const changed = assemblyStructureChanged();
    if (!changed) assemblyOperations.delete(publicationState.edition);
    const operations = changed ? assemblyOperationCount() : 0;
    byId("assembly-operation-count").textContent = operations;
    byId("assembly-change-count").textContent = affected;
    byId("assembly-change-tab-count").textContent = operations;
    byId("export-assembly-changes").disabled = !changed;
    byId("reset-assembly-changes").disabled = !changed;
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
        assemblyControl(`Move ${section.title} section up`, sectionIndex === 0, () => moveAssemblySection(section.id, -1), `assembly:section:${section.id}:up`, "↑"),
        assemblyControl(`Move ${section.title} section down`, sectionIndex === assembly.sections.length - 1, () => moveAssemblySection(section.id, 1), `assembly:section:${section.id}:down`, "↓")
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
          assemblyControl(`Move ${record.title} up`, pageIndexValue === 0, () => moveAssemblyPage(path, -1), `assembly:page:${path}:up`, "↑"),
          assemblyControl(`Move ${record.title} down`, pageIndexValue === section.paths.length - 1, () => moveAssemblyPage(path, 1), `assembly:page:${path}:down`, "↓")
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
    if (!assemblyStructureChanged()) return;
    const assembly = currentAssembly();
    const edition = publicationEdition();
    const payload = {
      schema_version: 1,
      purpose: "ARRP publication assembly changes",
      exported_at: new Date().toISOString(),
      edition_id: assembly.editionId,
      edition_label: edition.label,
      operation_count: assemblyOperationCount(),
      affected_record_count: assemblyChangeCount(),
      operations: assemblyOperations.get(publicationState.edition) || [],
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
      if (preliminaryState.term !== "all" && normalizeTerm(record.term) !== preliminaryState.term) return false;
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
    setButtonBlockerFlag("planning-tab-preliminary", false);
    byId("preliminary-empty").hidden = records.length !== 0;
    refreshDisclosurePreferences(list);
  }

  function renderProposed() {
    const query = proposedState.search.toLowerCase();
    const priorityOrder = { urgent: 0, high: 1, medium: 2, normal: 3, low: 4, "": 5 };
    const records = candidateProjectRecords().filter((record) => {
      if (proposedState.level !== "all" && record.development_level !== proposedState.level) return false;
      if (proposedState.status !== "all" && record.workflow_status !== proposedState.status) return false;
      if (proposedState.area !== "all" && record.area !== proposedState.area) return false;
      if (proposedState.priority !== "all" && text(record.priority, "Unassigned") !== proposedState.priority) return false;
      const hasGaps = Boolean((record.dossier_gaps || []).length);
      if (proposedState.gap === "gaps" && !hasGaps) return false;
      if (proposedState.gap === "complete" && hasGaps) return false;
      const monitoringRequired = explicitYes(record.needs_monitoring)
        || /monitor/i.test(String(record.workflow_status || ""));
      if (proposedState.monitoring === "required" && !monitoringRequired) return false;
      if (proposedState.monitoring === "not-required" && monitoringRequired) return false;
      const triggerRecorded = Boolean(record.next_trigger || record.monitoring_trigger || record.next_audit);
      if (proposedState.trigger === "recorded" && !triggerRecorded) return false;
      if (proposedState.trigger === "missing" && triggerRecorded) return false;
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
    }).sort((left, right) => {
      if (proposedState.sort === "identifier") return String(left.id).localeCompare(String(right.id));
      if (proposedState.sort === "oldest") {
        return (parseTimestamp(left.last_audit || left.updated_at) ?? Number.MAX_SAFE_INTEGER)
          - (parseTimestamp(right.last_audit || right.updated_at) ?? Number.MAX_SAFE_INTEGER);
      }
      if (proposedState.sort === "priority") {
        return (priorityOrder[String(left.priority || "").toLowerCase()] ?? 5)
          - (priorityOrder[String(right.priority || "").toLowerCase()] ?? 5)
          || String(left.id).localeCompare(String(right.id));
      }
      const leftAttention = Number(["Human decision needed", "Blocked"].includes(left.workflow_status)) * 4
        + Number(Boolean((left.dossier_gaps || []).length)) * 2
        + Number(typedReleaseBlocker(left.release_blocker));
      const rightAttention = Number(["Human decision needed", "Blocked"].includes(right.workflow_status)) * 4
        + Number(Boolean((right.dossier_gaps || []).length)) * 2
        + Number(typedReleaseBlocker(right.release_blocker));
      return rightAttention - leftAttention || String(left.id).localeCompare(String(right.id));
    });
    byId("proposed-list").replaceChildren(...(records.length
      ? records.map(proposedCard)
      : [element("p", "empty-state compact-empty", "No formal candidates match the current filters.")]));
    byId("proposed-visible").textContent = records.length;
    const blockers = records.filter((record) =>
      !["Blocked", "Deferred"].includes(record.workflow_status)
      && typedReleaseBlocker(record.release_blocker)
    );
    setButtonBlockerFlag(
      "planning-tab-candidates",
      blockers.length > 0,
      `${pluralizeWord(blockers.length, "blocker")} represented in Candidates`
    );
    setButtonBlockerFlag(
      "candidate-tab-formal",
      blockers.length > 0,
      `${pluralizeWord(blockers.length, "blocker")} represented in formal candidates`
    );
    refreshDisclosurePreferences(byId("proposed-list"));
  }

  function initializeStaticControls() {
    byId("preliminary-search").addEventListener("input", (event) => { preliminaryState.search = event.target.value; renderPreliminary(); });
    byId("preliminary-term").addEventListener("change", (event) => { preliminaryState.term = event.target.value; renderPreliminary(); });
    byId("preliminary-area").addEventListener("change", (event) => { preliminaryState.area = event.target.value; renderPreliminary(); });
    byId("proposed-search").addEventListener("input", (event) => { proposedState.search = event.target.value; renderProposed(); });
    byId("proposed-level").addEventListener("change", (event) => { proposedState.level = event.target.value; renderProposed(); });
    byId("proposed-status").addEventListener("change", (event) => { proposedState.status = event.target.value; renderProposed(); });
    byId("proposed-area").addEventListener("change", (event) => { proposedState.area = event.target.value; renderProposed(); });
    [["priority", "priority"], ["gap", "gap"], ["monitoring", "monitoring"], ["trigger", "trigger"], ["sort", "sort"]].forEach(([id, key]) => {
      byId(`proposed-${id}`).addEventListener("change", (event) => {
        proposedState[key] = event.target.value;
        renderProposed();
      });
    });
    byId("sources-search").addEventListener("input", (event) => {
      sourceStates.sources.search = event.target.value;
      sourceStates.sources.page = 1;
      renderSourceView("sources", data.cited_sources, "type");
    });
    [
      ["type", "filter"],
      ["exact-type", "exactType"],
      ["reviewed", "reviewed"],
      ["reliability", "reliability"],
      ["monitoring", "monitoring"],
      ["health", "health"]
    ].forEach(([id, key]) => {
      byId(`sources-${id}`).addEventListener("change", (event) => {
        sourceStates.sources[key] = event.target.value;
        sourceStates.sources.page = 1;
        renderSourceView("sources", data.cited_sources, "type");
      });
    });
    document.querySelectorAll("[data-pipeline-mode]").forEach((button) => {
      button.addEventListener("click", () => {
        resetPipelineMode(button.dataset.pipelineMode);
        renderPipeline();
        updatePipelineRoute();
      });
    });
    byId("pipeline-search").addEventListener("input", (event) => {
      pipelineState.search = event.target.value;
      renderPipeline();
      updatePipelineRoute();
    });
    [
      ["work-class", "workClass"],
      ["scope", "scope"],
      ["sort", "sort"],
      ["status", "status"],
      ["development", "development"],
      ["area", "area"],
      ["owner", "owner"],
      ["priority", "priority"],
      ["release-blocker", "releaseBlocker"]
    ].forEach(([id, key]) => {
      byId(`pipeline-${id}`).addEventListener("change", (event) => {
        pipelineState[key] = event.target.value;
        renderPipeline();
        updatePipelineRoute();
      });
    });
    byId("pipeline-reset").addEventListener("click", () => {
      resetPipelineMode();
      renderPipeline();
      updatePipelineRoute();
    });
    byId("pipeline-list").addEventListener("keydown", (event) => {
      if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
      const rows = [...byId("pipeline-list").querySelectorAll(".pipeline-row")];
      if (!rows.length) return;
      const current = event.target.closest(".pipeline-row");
      let index = rows.indexOf(current);
      if (event.key === "Home") index = 0;
      else if (event.key === "End") index = rows.length - 1;
      else if (event.key === "ArrowDown") index = Math.min(rows.length - 1, Math.max(0, index + 1));
      else index = Math.max(0, index < 0 ? 0 : index - 1);
      event.preventDefault();
      selectPipelineItem(rows[index].dataset.pipelineId, true, true);
    });
    [
      ["status", "status"],
      ["priority", "priority"],
      ["owner", "owner"]
    ].forEach(([id, key]) => {
      byId(`publication-blocker-${id}`).addEventListener("change", (event) => {
        releaseBlockerState[key] = event.target.value;
        renderPublicationReleaseBlockers();
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
      courtWatchState.page = 1;
      renderCourtWatch();
    });
    byId("court-watch-owner").addEventListener("change", (event) => {
      courtWatchState.owner = event.target.value;
      courtWatchState.page = 1;
      renderCourtWatch();
    });
    byId("court-watch-updated-only").addEventListener("click", (event) => {
      courtWatchState.updatesOnly = !courtWatchState.updatesOnly;
      courtWatchState.page = 1;
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
    byId("source-checker-search").addEventListener("input", (event) => {
      sourceCheckerState.search = event.target.value;
      sourceCheckerState.page = 1;
      renderSourceChecker();
    });
    [["classification", "classification"], ["domain", "domain"], ["owner", "owner"]].forEach(([id, key]) => {
      byId(`source-checker-${id}`).addEventListener("change", (event) => {
        sourceCheckerState[key] = event.target.value;
        sourceCheckerState.page = 1;
        renderSourceChecker();
      });
    });
    byId("problem-search").addEventListener("input", (event) => { problemState.search = event.target.value; renderIntegrity(); });
    byId("problem-owner").addEventListener("change", (event) => { problemState.owner = event.target.value; renderIntegrity(); });
    byId("problem-severity").addEventListener("change", (event) => { problemState.severity = event.target.value; renderIntegrity(); });
    byId("problem-status").addEventListener("change", (event) => { problemState.status = event.target.value; renderIntegrity(); });
    byId("pages-search").addEventListener("input", (event) => {
      pageState.search = event.target.value;
      pageState.page = 1;
      renderPages();
    });
    byId("pages-level").addEventListener("change", (event) => {
      pageState.level = event.target.value;
      pageState.page = 1;
      renderPages();
    });
    byId("pages-section").addEventListener("change", (event) => {
      pageState.section = event.target.value;
      pageState.page = 1;
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
      assemblyOperations.delete(publicationState.edition);
      renderDocumentBuilder();
    });
  }

  function hydrateCandidateData() {
    const candidates = candidateProjectRecords();
    byId("preliminary-count").textContent = data.records.length;
    byId("proposed-count").textContent = candidates.length;
    byId("candidate-formal-count").textContent = candidates.length;
    byId("candidate-preliminary-count").textContent = data.records.length;
    byId("planning-candidates-count").textContent = candidates.length;
    byId("planning-preliminary-count").textContent = data.records.length;
    byId("attention-note").textContent = data.records.length
      ? `${pluralizeWord(data.records.length, "preliminary candidate")} require human review.`
      : "No preliminary candidates currently require review.";
    populateSelect(byId("preliminary-area"), [...new Set(data.records.map((record) => record.proposed_area))], "All areas");
    populateSelect(byId("proposed-level"), [...new Set(candidates.map((record) => record.development_level))], "All levels");
    populateSelect(byId("proposed-status"), [...new Set(candidates.map((record) => record.workflow_status))], "All statuses");
    populateSelect(byId("proposed-area"), [...new Set(candidates.map((record) => record.area))], "All areas");
    populateSelect(byId("proposed-priority"), [...new Set(candidates.map((record) => text(record.priority, "Unassigned")))], "All priorities");
    renderPreliminary();
    renderProposed();
  }

  function hydrateSourceData() {
    const changedDirectives = data.presidential_directives
      .filter((record) => /^(New|Changed) since/.test(record.review_status || ""));
    reviewSignals.directives.count = changedDirectives.length;
    reviewSignals.directives.ids = new Set(changedDirectives.map((record) => record.id));
    byId("sources-count").textContent = data.cited_sources.length;
    byId("pending-count").textContent = data.pending_sources.length;
    byId("source-pending-count").textContent = data.pending_sources.length;
    byId("planning-sources-count").textContent = data.pending_sources.length;
    byId("manual-watch-count").textContent = data.monitoring_issues.length;
    byId("case-watcher-mode").textContent = `Current mode: ${(data.watcher_metadata.case_monitor || {}).mode || "Not configured"}.`;
    byId("directive-watcher-mode").textContent = `Current mode: ${(data.watcher_metadata.presidential_directives || {}).mode || "Not configured"}.`;
    populateSelect(byId("sources-type"), [...new Set(data.cited_sources.map((record) => sourceTypeFamily(record.type)))], "All source families");
    populateSelect(byId("sources-exact-type"), [...new Set(data.cited_sources.map((record) => record.type))], "All exact types");
    populateSelect(byId("sources-reviewed"), [...new Set(data.cited_sources.map((record) => text(record.reviewed, "Not recorded")))], "All review states");
    populateSelect(byId("sources-reliability"), [...new Set(data.cited_sources.map((record) => text(record.reliability, "Not recorded")))], "All reliability classes");
    populateSelect(byId("sources-monitoring"), ["Monitored", "Not monitored"], "All monitoring states");
    populateSelect(byId("sources-health"), [...new Set(sourceCheckerRecords().map((record) => record.classification)), "Unavailable"], "All health states");
    populateSelect(byId("pending-owner"), [...new Set(data.pending_sources.flatMap((record) => record.record_ids || []))], "All possible destinations");
    populateSelect(byId("manual-watch-kind"), [...new Set(data.monitoring_issues.map((record) => record.kind))], "All issue types");
    populateSelect(byId("court-watch-owner"), [...new Set(data.court_watch_sources.map((record) => record.owner_id))], "All owners");
    populateSelect(byId("directive-administration"), [...new Set(data.presidential_directives.map((record) => record.administration))], "All administrations");
    populateSelect(byId("directive-status"), [...new Set(data.presidential_directives.map((record) => record.review_status))], "All statuses");
    renderSourceView("sources", data.cited_sources, "type");
    renderPending();
    renderManualWatch();
    renderCourtWatch();
    renderDirectives();
  }

  function ensureLogStates() {
    data.project_logs.forEach((log) => {
      if (!logStates[log.id]) {
        logStates[log.id] = {
          search: "",
          groupKey: "all",
          filters: {},
          page: 1,
          sortKey: (log.default_sort || {}).key || (log.columns[0] || {}).key || null,
          sortDirection: (log.default_sort || {}).direction || "asc"
        };
      }
      populateLogGroupSelect(log);
      const search = byId(`log-${log.id}-search`);
      const group = byId(`log-${log.id}-group`);
      if (!search.dataset.bound) {
        search.dataset.bound = "true";
        search.addEventListener("input", (event) => {
          logStates[log.id].search = event.target.value;
          logStates[log.id].page = 1;
          renderProjectLog(log.id);
        });
        group.addEventListener("change", (event) => {
          logStates[log.id].groupKey = event.target.value;
          logStates[log.id].page = 1;
          renderProjectLog(log.id);
        });
      }
      if (log.id === "agents") {
        [["agent", "All bots and historical automation"], ["task", "All task types"], ["outcome", "All outcomes"]].forEach(([key, label]) => {
          const select = byId(`log-agents-${key}`);
          populateSelect(select, [...new Set(log.entries.map((entry) => (entry.values || {})[key]).filter(Boolean))], label);
          if (!select.dataset.bound) {
            select.dataset.bound = "true";
            select.addEventListener("change", (event) => {
              logStates.agents.filters[key] = event.target.value;
              logStates.agents.page = 1;
              renderProjectLog("agents");
            });
          }
        });
      }
      renderProjectLog(log.id);
    });
  }

  function hydratePublicationData() {
    pageIndex = new Map(data.page_inventory.map((record) => [record.path, record]));
    byId("pages-count").textContent = data.page_inventory.length;
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
    [byId("analysis-edition"), byId("builder-edition")].forEach((select) => select.replaceChildren());
    publicationEditions().forEach((edition) => {
      [byId("analysis-edition"), byId("builder-edition")].forEach((select) => {
        const option = element("option", "", edition.label);
        option.value = edition.id;
        select.append(option);
      });
    });
    if (!publicationEditions().some((edition) => edition.id === publicationState.edition)) {
      publicationState.edition = publicationEditions()[0]?.id || "public-proposal";
    }
    byId("analysis-edition").value = publicationState.edition;
    byId("builder-edition").value = publicationState.edition;
    renderPrintSummary();
    renderPrintChangeToolbar();
    renderPages();
    renderEditionAnalysis();
    renderDocumentBuilder();
  }

  function hydrateLoadedDomain(domain) {
    if (domain === "overview") renderOverview();
    if (domain === "candidates") hydrateCandidateData();
    if (domain === "progress") {
      hydrateCandidateData();
      renderProgress();
      if (loadedDomains.has("publication")) renderEditionAnalysis();
      refreshLiveProgress();
    }
    if (domain === "sources") hydrateSourceData();
    if (domain === "source-checker") {
      populateSourceCheckerFilters();
      renderSourceChecker();
      refreshLiveSourceChecker();
      if (loadedDomains.has("sources")) {
        populateSelect(byId("sources-health"), [...new Set(sourceCheckerRecords().map((record) => record.classification)), "Unavailable"], "All health states");
        renderSourceView("sources", data.cited_sources, "type");
      }
      if (loadedDomains.has("integrity")) renderIntegrity();
    }
    if (domain === "automation") {
      renderAutomation();
      if (loadedDomains.has("sources")) {
        populateSelect(byId("sources-health"), [...new Set(sourceCheckerRecords().map((record) => record.classification)), "Unavailable"], "All health states");
        renderSourceView("sources", data.cited_sources, "type");
      }
      refreshLiveRunChain();
    }
    if (domain === "integrity") {
      renderIntegrity();
      refreshLiveIntegrity();
    }
    if (domain === "logs") {
      ensureLogStates();
      renderIntegrityHistory();
      renderIncidentLog();
    }
    if (domain === "publication") hydratePublicationData();
    renderOverview();
  }

  async function activateDomainForTab(tab, subtab = "") {
    const panel = byId(`panel-${tab}`);
    if (panel) panel.setAttribute("aria-busy", "true");
    let dependencies = {
      overview: [],
      progress: ["candidates", "progress"],
      actions: ["candidates", "progress", "sources", "source-checker", "automation", "integrity", "publication"],
      planning: ["candidates", "progress"],
      integrity: ["candidates", "progress", "sources", "source-checker", "automation", "integrity", "publication"],
      automation: ["automation"],
    }[tab] || [];
    if (tab === "planning") {
      dependencies = {
        workbench: ["candidates", "progress"],
        candidates: ["candidates", "progress"],
        preliminary: ["candidates", "progress"],
        sources: ["sources", "source-checker", "automation"],
        publication: ["publication", "progress"]
      }[subtab || "workbench"] || ["candidates", "progress"];
    }
    if (tab === "automation" && subtab === "logs") {
      dependencies = ["automation", "logs", "integrity"];
    }
    if (tab === "overview") {
      await ensureDomain("overview", { optional: true });
      renderOverview();
    } else {
      await Promise.all(dependencies.map((domain) => ensureDomain(domain)));
    }
    if (tab === "planning" && subtab === "sources"
      && byId("source-workspace-selector")?.value === "source-checker") {
      await Promise.all([
        ensureDomain("source-checker"),
        ensureDomain("automation")
      ]);
    }
    if (tab === "actions") renderActionItems();
    if (tab === "planning" && (subtab || "workbench") === "workbench") renderPipeline();
    if (panel) panel.setAttribute("aria-busy", "false");
    announce(`${document.querySelector(`[data-tab="${tab}"]`)?.textContent?.trim() || tab} data loaded.`);
  }

  function initialize() {
    byId("github-synced-at").textContent = formatDate(data.github_synced_at);
    byId("watchers-count").textContent = 3;
    byId("preliminary-count").textContent = data.records.length;
    byId("proposed-count").textContent = data.active_horizon_records.length;
    byId("planning-candidates-count").textContent = data.active_horizon_records.length;
    byId("planning-preliminary-count").textContent = data.records.length;
    byId("tab-actions-count").textContent = data.overview?.queue_counts?.human_actions ?? 0;
    byId("manual-watch-count").textContent = data.monitoring_issues.length;
    initializeStaticControls();
    initializeActionInboxControls();
    initializeWorkflowSummary();
    prepareConsolidatedNavigation();
    initializePersonalLayout();
    initializeTabs();
    initializeSectionTabs("planning", "workbench");
    initializeSectionTabs("automation", "overview");
    initializeWatcherTabs();
    initializeLogMenu();
    initializeIncidentLog();
    initializeAutomationRoleMenu();
    initializeScrollToTop();
    window.addEventListener("hashchange", navigateFromHash);
    renderOverview();
    refreshLayoutZones();
    refreshBotReviewSignals();
    refreshPlatformStatus();
    const domCount = document.querySelectorAll("*").length;
    document.body.dataset.initialDomCount = String(domCount);
    const budget = Number(document.body.dataset.initialDomBudget || 1400);
    if (domCount > budget) console.warn(`Initial DOM budget exceeded: ${domCount} > ${budget}`);
  }

  window.ARRP_CONSOLE_TEST_API = Object.freeze({
    normalizeTerm,
    termLabel,
    parseTimestamp,
    formatDate,
    scorePresentation,
    integrityComponentValue,
    sourceTypeFamily,
    sourceCheckerDeltaPresentation,
    feedContractState,
    operationalFeedState,
    shouldAcceptLiveFeed,
    validateLivePayload,
    reconcileRunChainSnapshot,
    domainGenerationStatus,
    hasNextLink,
    exactIntegrityProblemRecords,
    allProblemRecords,
    repositorySpecialistRoute,
    repositoryAffectedSummary,
    explicitYes,
    applyPipelineParameters,
    workbenchArtifactRecord,
    workbenchTargetForArtifact,
    structuredArtifactIdentifiers,
    pipelineProjectionState,
    pipelineDefaultSort,
    filteredPipelineItems,
    groupAutomationIncidents,
    incidentHasHumanOwner,
    candidateProjectRecords,
    deliveryItems,
    deliveryProjectionState,
    releaseBlockerDetail,
    releaseBlockerRecords,
    releaseBlockerProjectionState,
    topicProducts,
    elimImprovementRecords,
    compactActivityPresentation,
    priorityAttentionReasons,
    priorityAttentionItems,
    normalizeConsoleTarget,
    safeConsoleTarget,
    safePipelineExternalUrl,
    pluralizeWord,
    overviewBriefVerification,
    overviewStagePresentation,
    elimRunChainPresentation,
    localAutomationPresentation,
    overviewBriefFactStates,
    securityAssuranceProjection,
    securityActionRecords,
    effectiveAutomationRoleStatusProjection,
    automationOutcomePresentation,
    platformProviderObservation,
    platformCellProjection,
    platformStatusPresentation,
    relevantPlatformIncidents,
    operationalIncidentProjection,
    unresolvedOperationalIncidents,
    humanOwnsIncident,
    incidentStatusPresentation,
    canonicalFileConsolePath,
    localConsoleOriginAllowed,
    validPrivateOperationsSnapshot,
    validLocalAutomationStatus,
    loadLocalProjection
  });
  if (window.__ARRP_CONSOLE_TEST_MODE__) return;
  Promise.all([
    loadPrivateSecurityAssurance(),
    loadPrivateOperations(),
    loadLocalAutomationStatus()
  ]).then(initialize);
})();
