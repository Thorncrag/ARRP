import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const testDirectory = path.dirname(fileURLToPath(import.meta.url));
const consoleDirectory = path.resolve(testDirectory, "..");
const appPath = path.join(consoleDirectory, "app.js");
const indexPath = path.join(consoleDirectory, "index.html");

function loadApi() {
  const projectData = {
    records: [],
    active_horizon_records: [],
    monitoring_issues: [],
    repository_review_recommendations: []
  };
  const document = {
    body: { dataset: {}, innerHTML: "" },
    querySelectorAll() { return []; }
  };
  const window = {
    ARRP_HORIZON_REVIEW_DATA: projectData,
    __ARRP_CONSOLE_TEST_MODE__: true
  };
  const context = {
    window,
    document,
    console,
    CSS: { escape: String },
    URL,
    URLSearchParams,
    Intl,
    Date,
    Map,
    Set,
    Number,
    String,
    Object,
    Array,
    Math,
    RegExp,
    JSON
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(appPath, "utf8"), context, { filename: appPath });
  return { api: window.ARRP_CONSOLE_TEST_API, data: window.ARRP_HORIZON_REVIEW_DATA };
}

test("term normalization uses the canonical Trump I and Trump II vocabulary", () => {
  const { api } = loadApi();
  assert.equal(api.normalizeTerm("1"), "trump-i");
  assert.equal(api.normalizeTerm("Trump II"), "trump-ii");
  assert.equal(api.normalizeTerm("both terms"), "both");
  assert.equal(api.termLabel("Trump II"), "Trump II");
  assert.equal(api.termLabel("unknown"), "Term not recorded");
});

test("score zero is valid, null is unavailable, and invalid values remain visible", () => {
  const { api } = loadApi();
  assert.deepEqual(
    JSON.parse(JSON.stringify(api.scorePresentation(0))),
    { label: "Score 0", valid: true, available: true, value: 0 }
  );
  assert.equal(api.scorePresentation(null).available, false);
  assert.equal(api.scorePresentation(101).valid, false);
  assert.match(api.scorePresentation("bad").label, /Invalid score/);
  assert.deepEqual(
    JSON.parse(JSON.stringify(api.scorePresentation(false))),
    { label: "Invalid score: false", valid: false, available: true, value: false }
  );
});

test("feed state consumes producer declarations and completeness", () => {
  const { api } = loadApi();
  assert.equal(api.feedContractState({ availability: "current" }).label, "Current");
  assert.equal(api.feedContractState({ availability: "available" }).label, "Available");
  const incomplete = api.feedContractState({
    availability: "current",
    expected_count: 2055,
    actual_count: 2048,
    completeness: { complete: false, reason: "Seven records are missing" }
  });
  assert.equal(incomplete.state, "incomplete");
  assert.equal(incomplete.complete, false);
  assert.equal(incomplete.expected, 2055);
  assert.equal(incomplete.actual, 2048);
});

test("source families match the accepted Console taxonomy while raw types remain independent", () => {
  const { api } = loadApi();
  assert.equal(api.sourceTypeFamily("Federal court opinion"), "Judicial");
  assert.equal(api.sourceTypeFamily("Congressional hearing"), "Legislative");
  assert.equal(api.sourceTypeFamily("Agency report"), "Government");
  assert.equal(api.sourceTypeFamily("Peer-reviewed journal study"), "Scholarly");
  assert.equal(api.sourceTypeFamily("News article"), "News");
  assert.equal(api.sourceTypeFamily("Advocacy organization brief"), "Advocacy");
  assert.equal(api.sourceTypeFamily("Litigation tracker"), "Tracker");
  assert.equal(api.sourceTypeFamily("Personal correspondence"), "Other");
});

test("older live feeds cannot replace newer checked-in projections", () => {
  const { api } = loadApi();
  assert.equal(api.shouldAcceptLiveFeed(
    { generated_at: "2026-07-25T10:00:00+00:00" },
    { generated_at: "2026-07-25T09:59:59Z" }
  ), false);
  assert.equal(api.shouldAcceptLiveFeed(
    { generated_at: "2026-07-25T10:00:00+00:00" },
    { generated_at: "2026-07-25T10:00:01Z" }
  ), true);
  assert.equal(api.shouldAcceptLiveFeed(
    { generated_at: "2026-07-25T10:00:00Z", source_revision: "current-revision" },
    { generated_at: "2026-07-25T10:30:00Z", source_revision: "superseded-revision" }
  ), false);
  assert.equal(api.shouldAcceptLiveFeed(
    { generated_at: "2026-07-25T10:00:00Z", source_revision: "current-revision" },
    {
      generated_at: "2026-07-25T10:30:00Z",
      source_revision: "next-revision",
      supersedes_source_revision: "current-revision"
    }
  ), true);
});

test("authority-specific freshness accepts legitimate newer generations and rejects superseded recent ones", () => {
  const { api } = loadApi();
  const complete = { complete: true, expected_count: 1, actual_count: 1 };
  assert.equal(api.shouldAcceptLiveFeed("progress",
    { generated_at: "2026-07-25T10:00:00Z", generation_id: "project-old", completeness: complete },
    { generated_at: "2026-07-25T11:00:00Z", generation_id: "project-new", completeness: complete }
  ), true);
  assert.equal(api.shouldAcceptLiveFeed("integrity",
    { generated_at: "2026-07-25T10:00:00Z", source_revision: "head-old", completeness: complete },
    { generated_at: "2026-07-25T11:00:00Z", source_revision: "head-new", completeness: complete }
  ), true);
  assert.equal(api.shouldAcceptLiveFeed("integrity",
    { generated_at: "2026-07-25T11:00:00Z", source_revision: "head-new", completeness: complete },
    { generated_at: "2026-07-25T10:30:00Z", source_revision: "head-old", completeness: complete }
  ), false);
  const hashes = { "inventory/sources.csv": `sha256:${"b".repeat(64)}` };
  assert.equal(api.shouldAcceptLiveFeed("source-checker",
    {
      checked_at: "2026-07-25T10:00:00Z",
      generation_id: "checker-old",
      completeness: complete,
      current_catalog_coverage: { source_hashes: hashes }
    },
    {
      checked_at: "2026-07-25T11:00:00Z",
      generation_id: "checker-new",
      completeness: complete,
      source_hashes: hashes
    }
  ), true);
});

test("candidate Project fields merge over dossier fields without dropping dossier evidence", () => {
  const { api, data } = loadApi();
  data.active_horizon_records = [{
    id: "HOR-001",
    title: "Dossier title",
    development_level: "Candidate",
    workflow_status: "Research",
    supporting_sources: [{ id: "SRC-1" }]
  }];
  data.progress = {
    candidates: [{
      identifier: "HOR-001",
      developmentLevel: "In development",
      workflowStatus: "Human decision needed",
      priority: "High",
      score: 0
    }]
  };
  const merged = api.candidateProjectRecords()[0];
  assert.equal(merged.development_level, "In development");
  assert.equal(merged.workflow_status, "Human decision needed");
  assert.equal(merged.priority, "High");
  assert.equal(merged.score, 0);
  assert.equal(merged.supporting_sources[0].id, "SRC-1");
});

test("automation incidents group repeated occurrences by root cause", () => {
  const { api } = loadApi();
  const groups = api.groupAutomationIncidents({
    updated_at: "2026-07-25T10:00:00Z",
    failures: [
      { stage: "sources", root_cause: "Credential unavailable", owner: "Human" },
      { stage: "directives", root_cause: "Credential unavailable", owner: "Human" }
    ]
  });
  assert.equal(groups.length, 1);
  assert.equal(groups[0].occurrences, 2);
  assert.deepEqual([...groups[0].stages], ["directives", "sources"]);
});

test("automation incident identity includes failed prerequisite and runtime or checkout state", () => {
  const { api } = loadApi();
  const groups = api.groupAutomationIncidents({
    chain_id: "chain-current",
    failures: [
      { stage: "sources", root_cause: "Repository preflight", failed_prerequisite: "clean checkout", checkout_state: "dirty", runtime_state: "ready" },
      { stage: "sources", root_cause: "Repository preflight", failed_prerequisite: "clean checkout", checkout_state: "detached", runtime_state: "ready" }
    ]
  });
  assert.equal(groups.length, 2);
});

test("off-main retries collapse to one managerial incident while retaining chain history", () => {
  const { api } = loadApi();
  const groups = api.groupAutomationIncidents({
    chain_id: "chain-current",
    failures: [{
      stage: "host-repository-preflight",
      message: "host-repository-preflight failed: canonical ARRP workspace is not reconciled with GitHub: current branch is codex/review-b instead of main."
    }],
    host_action_items: [
      {
        chain_id: "chain-old",
        stage: "host-repository-preflight",
        owner: "human",
        details: "host-repository-preflight failed: canonical ARRP workspace is not reconciled with GitHub: current branch is codex/review-a instead of main.",
        resolved: true
      },
      {
        chain_id: "chain-current",
        stage: "host-repository-preflight",
        owner: "human",
        details: "host-repository-preflight failed: canonical ARRP workspace is not reconciled with GitHub: current branch is codex/review-b instead of main.",
        resolved: false
      }
    ]
  });
  assert.equal(groups.length, 1);
  assert.equal(groups[0].history.length, 3);
  assert.equal(groups[0].postures.includes("Superseded"), true);
  assert.equal(api.incidentHasHumanOwner(groups[0]), true);
});

test("duplicate current failure and host action rows count once while distinct retries remain", () => {
  const { api } = loadApi();
  const detail = "host-repository-preflight failed: canonical ARRP workspace is not reconciled with GitHub: current branch is codex/review instead of main.";
  const groups = api.groupAutomationIncidents({
    chain_id: "chain-current",
    failures: [{
      stage: "host-repository-preflight",
      recorded_at: "2026-07-25T10:00:00Z",
      message: detail
    }],
    host_action_items: [
      {
        chain_id: "chain-current",
        stage: "host-repository-preflight",
        created_at: "2026-07-25T10:00:00+00:00",
        owner: "Human",
        details: detail,
        resolved: false
      },
      {
        chain_id: "chain-current",
        stage: "host-repository-preflight",
        created_at: "2026-07-25T11:00:00Z",
        owner: "Human",
        details: detail,
        resolved: false
      }
    ]
  });
  assert.equal(groups.length, 1);
  assert.equal(groups[0].occurrences, 2);
  assert.equal(groups[0].history.length, 2);
  assert.equal(api.incidentHasHumanOwner(groups[0]), true);
});

test("Source Checker assurance deltas preserve explicit zero and baseline unavailability", () => {
  const { api } = loadApi();
  const unavailable = api.sourceCheckerDeltaPresentation({
    deltas: { available: false, reason: "No comparable prior baseline." }
  });
  assert.equal(unavailable.available, false);
  assert.match(unavailable.reason, /prior baseline/);
  const available = api.sourceCheckerDeltaPresentation({
    deltas: {
      available: true,
      baseline_checked_at: "2026-07-24T10:00:00Z",
      counts: {
        new_exceptions: 0,
        regressed_exceptions: 2,
        resolved_exceptions: 1,
        ongoing_exceptions: 3
      },
      aging_exceptions: [{ source_id: "SRC-1", classification: "broken", age_days: 4 }]
    }
  });
  assert.equal(available.counts.newExceptions, 0);
  assert.equal(available.counts.regressedExceptions, 2);
  assert.equal(available.oldest.source_id, "SRC-1");
});

test("watcher repository fixtures route to specialist views and report typed affected counts", () => {
  const { api } = loadApi();
  const pr380 = {
    complete: true,
    total_count: 43,
    source_ids: Array.from({ length: 42 }, (_, index) => `SRC-${index}`),
    directive_ids: [],
    issue_development_ids: ["HOR-035"],
    issue_development_count: 1
  };
  assert.equal(api.repositorySpecialistRoute(pr380).target, "sources:watchers:courts");
  assert.match(api.repositoryAffectedSummary(pr380), /43 affected records/);
  assert.match(api.repositoryAffectedSummary(pr380), /1 proposal\/candidate/);
  assert.match(api.repositoryAffectedSummary(pr380), /42 sources/);
  const pr381 = {
    complete: true,
    total_count: 10,
    source_ids: [],
    directive_ids: Array.from({ length: 10 }, (_, index) => `2026-${index}`),
    issue_development_ids: [],
    issue_development_count: 0
  };
  assert.equal(api.repositorySpecialistRoute(pr381).target, "sources:watchers:directives");
  assert.match(api.repositoryAffectedSummary(pr381), /10 directives/);
});

test("generation validation accepts canonical hashes and rejects mixed or missing domains", () => {
  const { api } = loadApi();
  const generation = "project-console-test";
  const manifest = {
    files: {
      "progress.js": {
        generation_id: generation,
        sha256: `sha256:${"a".repeat(64)}`,
        bytes: 123
      }
    }
  };
  assert.equal(api.domainGenerationStatus(generation, "progress.js", { "progress.js": generation }, manifest).valid, true);
  assert.equal(api.domainGenerationStatus(generation, "progress.js", { "progress.js": "other" }, manifest).valid, false);
  assert.equal(api.domainGenerationStatus(generation, "integrity.js", { "integrity.js": generation }, manifest).valid, false);
  const badHash = structuredClone(manifest);
  badHash.files["progress.js"].sha256 = "not-a-hash";
  assert.equal(api.domainGenerationStatus(generation, "progress.js", { "progress.js": generation }, badHash).valid, false);
});

test("GitHub Link pagination is detected before treating pull-request inventory as complete", () => {
  const { api } = loadApi();
  assert.equal(api.hasNextLink('<https://api.github.com/repositories/1/pulls?page=2>; rel="next", <https://api.github.com/repositories/1/pulls?page=4>; rel="last"'), true);
  assert.equal(api.hasNextLink('<https://api.github.com/repositories/1/pulls?page=1>; rel="prev"'), false);
});

test("typed booleans do not treat the string No as true", () => {
  const { api } = loadApi();
  assert.equal(api.explicitYes("Yes"), true);
  assert.equal(api.explicitYes("No"), false);
});

test("malformed Source Checker and Progress feeds fail runtime validation", () => {
  const { api } = loadApi();
  const source = {
    schema_version: 1,
    checked_at: "2026-07-25T10:00:00Z",
    eligible_urls: 1,
    counts: { verified: 1 },
    results: [{ source_id: "SRC-1", classification: "verified" }]
  };
  assert.equal(api.validateLivePayload("source-checker", source).valid, true);
  assert.equal(api.validateLivePayload("source-checker", {
    ...source,
    results: [...source.results, ...source.results]
  }).valid, false);
  assert.equal(api.validateLivePayload("progress", {
    schemaVersion: 2,
    generatedAt: "2026-07-25T10:00:00Z",
    metrics: { total: 2 },
    proposals: [{ identifier: "ISSUE-1" }]
  }).valid, false);
});

test("delivery aliases remain separate from proposal metrics", () => {
  const { api, data } = loadApi();
  data.progress = {
    metrics: { total: 81 },
    delivery_items: [{ id: "DEL-1" }, { id: "DEL-2" }]
  };
  assert.equal(api.deliveryItems().length, 2);
  assert.equal(data.progress.metrics.total, 81);
});

test("unavailable Integrity components do not imply zero and an available empty delivery feed shows zero", () => {
  const { api, data } = loadApi();
  assert.equal(api.integrityComponentValue({ state: "unavailable", complete: false }, 0), "Unavailable");
  assert.equal(api.integrityComponentValue({ state: "incomplete", complete: false }, 7), "Unavailable");
  assert.equal(api.integrityComponentValue({ state: "current", complete: true }, 0), 0);
  data.delivery_items = [];
  data.publication.release_readiness = { delivery_tasks: { available: true } };
  assert.equal(api.deliveryProjectionState().available, true);
  assert.equal(api.deliveryItems().length, 0);
});

test("typed release blockers unite proposals, candidates, and delivery work without changing portfolio metrics", () => {
  const { api, data } = loadApi();
  data.active_horizon_records = [{
    id: "HOR-001",
    title: "Candidate blocker",
    issue_url: "https://github.com/Thorncrag/ARRP/issues/2"
  }];
  data.progress = {
    metrics: { total: 81 },
    proposals: [{
      identifier: "PRO-001",
      title: "Proposal blocker",
      kind: "proposal",
      releaseBlocker: "Yes",
      workflowStatus: "Development",
      priority: "High",
      owner: "Research",
      url: "https://github.com/Thorncrag/ARRP/issues/1"
    }, {
      identifier: "PRO-002",
      title: "Not a blocker",
      kind: "proposal",
      releaseBlocker: "No"
    }],
    candidates: [{
      identifier: "HOR-001",
      releaseBlocker: "true",
      workflowStatus: "Human decision needed",
      priority: "Critical",
      owner: "Human"
    }],
    delivery_items: [{
      identifier: "DEL-001",
      title: "Delivery blocker",
      kind: "task",
      releaseBlocker: true,
      workflowStatus: "Blocked",
      priority: "Normal",
      owner: "Automation",
      url: "https://github.com/Thorncrag/ARRP/issues/3"
    }],
    projectItemReconciliation: {
      releaseBlockers: 3,
      releaseBlockerFieldProjected: true
    }
  };
  data.publication = {
    release_readiness: {
      release_blockers: {
        available: true,
        count: 3,
        items: [{ identifier: "PRO-001", release_blocker: "Yes" }]
      }
    }
  };
  const blockers = api.releaseBlockerRecords();
  assert.equal(blockers.length, 3);
  assert.deepEqual([...new Set(blockers.map((record) => record.recordType))].sort(),
    ["Delivery work", "Formal candidate", "Proposal"]);
  assert.equal(api.releaseBlockerProjectionState(blockers).mismatch, false);
  assert.equal(data.progress.metrics.total, 81);
});

test("topic products require a typed mapping and preserve an explicit empty projection", () => {
  const { api, data } = loadApi();
  data.page_inventory = [{ path: "topics/example.md", title: "Example" }];
  data.publication = {};
  assert.equal(api.topicProducts(), undefined);
  data.publication.topic_products = [];
  assert.deepEqual(api.topicProducts(), []);
  data.publication.topic_products = [{ product_id: "topic-product:example" }];
  assert.equal(api.topicProducts()[0].product_id, "topic-product:example");
});

test("Progress Next Work deep links apply every managerial facet", () => {
  const { api } = loadApi();
  const state = api.applyProgressNextWorkParameters(
    "status=Human%20decision%20needed&cohort=Human-reserved&development=Candidate"
      + "&release_blocker=Required&workstream=ELEC&owner=Human&priority=Critical"
  );
  assert.deepEqual(JSON.parse(JSON.stringify(state)), {
    search: "",
    cohort: "Human-reserved",
    status: "Human decision needed",
    priority: "Critical",
    development: "Candidate",
    releaseBlocker: "Required",
    area: "ELEC",
    owner: "Human"
  });
});

test("recent issue-development impact preserves a valid current score of zero", () => {
  const { api, data } = loadApi();
  data.progress = {
    proposals: [{
      identifier: "HOR-001",
      title: "Zero score record",
      score: 0,
      canonicalRecord: "research/horizon-records/HOR-001.md"
    }]
  };
  const records = api.elimImprovementRecords({
    values: { summary: "HOR-001 received a material issue-development update." }
  });
  assert.equal(records[0].score, "Current score 0 · run delta not recorded");
});

test("compact Overview activity preserves actor, outcome, affected scope, time, owner, and specialist route", () => {
  const { api } = loadApi();
  const row = api.compactActivityPresentation({
    id: "SMR-1",
    log: "source-monitor",
    date: "2026-07-25T22:17:40Z",
    title: "Interactive Codex · PR #381",
    actor: "Interactive Codex",
    source: "Source Monitor Log",
    outcome: "Recommendation recorded",
    affected_scope: "10 directive records",
    summary: "Review the complete exact-head delta.",
    manager_effect: "Approve the recorded disposition?",
    owner: "Human",
    route: "sources:watchers:directives",
    tone: "warning"
  });
  assert.equal(row.title, "Interactive Codex · PR #381");
  assert.match(row.meta, /Source Monitor Log/);
  assert.doesNotMatch(row.meta, /Not recorded/);
  assert.match(row.summary, /Outcome: Recommendation recorded/);
  assert.match(row.summary, /Affected: 10 directive records/);
  assert.match(row.summary, /Manager effect: Approve the recorded disposition/);
  assert.match(row.summary, /Owner: Human/);
  assert.equal(row.target, "sources:watchers:directives");
  assert.equal(row.tone, "warning");
});

test("initial HTML loads only bounded scripts and stays within declared budgets", () => {
  const html = fs.readFileSync(indexPath, "utf8");
  const scriptSources = [...html.matchAll(/<script\s+src="([^"]+)"/g)].map((match) => match[1]);
  assert.deepEqual(scriptSources, ["catalog-data.js?v=45", "app.js?v=45"]);
  assert.match(html, /data-initial-script-budget-kib="512"/);
  assert.match(html, /data-initial-dom-budget="1400"/);
  const bytes = ["catalog-data.js", "app.js"]
    .map((file) => fs.statSync(path.join(consoleDirectory, file)).size)
    .reduce((sum, size) => sum + size, 0);
  assert.ok(bytes <= 512 * 1024, `synchronous JavaScript is ${bytes} bytes`);
  const approximateElementCount = (html.match(/<[a-z][^!/][^>]*>/gi) || []).length;
  assert.ok(approximateElementCount <= 1400, `initial HTML has about ${approximateElementCount} elements`);
  assert.doesNotMatch(html, /<script\s+src="data\/(?:candidates|sources|progress|integrity|automation|logs|publication)/);
  assert.doesNotMatch(html, /role="tabpanel"[^>]*tabindex="0"/);
  assert.match(html, /Recent material activity/);
  assert.match(html, /id="pages-pagination"/);
  assert.match(html, /id="court-watch-pagination"/);
  assert.match(html, /id="progress-next-development"/);
  assert.match(html, /id="progress-next-release-blocker"/);
  assert.match(html, /id="progress-next-area"/);
  assert.match(html, /id="progress-next-owner"/);
  assert.match(html, /id="proposed-monitoring"/);
  assert.match(html, /id="proposed-trigger"/);
  assert.match(html, /id="publication-release-blockers-list"/);
  assert.doesNotMatch(html, /id="tab-logs-count"/);
});
