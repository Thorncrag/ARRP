import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const testDirectory = path.dirname(fileURLToPath(import.meta.url));
const consoleDirectory = path.resolve(testDirectory, "..");
const appPath = path.join(consoleDirectory, "app.js");
const indexPath = path.join(consoleDirectory, "index.html");
const localRequire = createRequire(import.meta.url);

function loadApi(privateSecurityAssurance = {}, projectDataOverride = {}) {
  const projectData = {
    records: [],
    active_horizon_records: [],
    monitoring_issues: [],
    repository_review_recommendations: [],
    ...projectDataOverride
  };
  const document = {
    body: { dataset: {}, innerHTML: "" },
    querySelectorAll() { return []; }
  };
  const window = {
    ARRP_HORIZON_REVIEW_DATA: projectData,
    ARRP_PRIVATE_SECURITY_ASSURANCE: privateSecurityAssurance,
    __ARRP_CONSOLE_TEST_MODE__: true
  };
  const priorGlobals = {
    window: globalThis.window,
    document: globalThis.document,
    CSS: globalThis.CSS
  };
  globalThis.window = window;
  globalThis.document = document;
  globalThis.CSS = { escape: String };
  const appModule = localRequire.resolve("../app.js");
  delete localRequire.cache[appModule];
  try {
    localRequire("../app.js");
    return {
      api: window.ARRP_CONSOLE_TEST_API,
      data: window.ARRP_HORIZON_REVIEW_DATA
    };
  } finally {
    for (const [name, value] of Object.entries(priorGlobals)) {
      if (value === undefined) delete globalThis[name];
      else globalThis[name] = value;
    }
  }
}

test("term normalization uses the canonical Trump I and Trump II vocabulary", () => {
  const { api } = loadApi();
  assert.equal(api.normalizeTerm("1"), "trump-i");
  assert.equal(api.normalizeTerm("Trump II"), "trump-ii");
  assert.equal(api.normalizeTerm("both terms"), "both");
  assert.equal(api.termLabel("Trump II"), "Trump II");
  assert.equal(api.termLabel("unknown"), "Term not recorded");
});

test("Console development categories render as separate readable log entries", () => {
  const app = fs.readFileSync(appPath, "utf8");
  assert.match(
    app,
    /if \(log\.id === "console-development"\) return values\.category \|\| values\.change \|\| entry\.id;/
  );
  assert.doesNotMatch(
    app,
    /log\.id === "console-development"[^;]+values\.feature/
  );
});

test("date-only audit provenance preserves its recorded calendar day", () => {
  const { api } = loadApi();
  assert.equal(api.formatDate("2026-07-10"), "Jul 10, 2026");
});

test("Integrity remains the exact authoritative report rather than a cross-domain total", () => {
  const { api, data } = loadApi();
  data.integrity = {
    current: {
      generated_at: "2026-07-28T12:00:00Z",
      findings: [{ reference: "INT-001", message: "Exact report finding" }]
    }
  };
  data.progress = {
    pipeline: {
      integrityFindings: [{
        identifier: "HOR-031",
        message: "Pipeline provenance defect",
        severity: "warning"
      }]
    }
  };
  const exact = api.exactIntegrityProblemRecords(data.integrity);
  const combined = api.allProblemRecords(data.integrity);
  assert.deepEqual(exact.map((finding) => finding.reference), ["INT-001"]);
  assert.ok(combined.some((finding) => finding.message === "Pipeline provenance defect"));
});

test("security assurance accepts only minimized registered tool status", () => {
  const publicTools = [
    { tool_id: "credential-access-review", label: "Credential and access review", purpose: "Safe purpose.", owner_class: "Human", destination_class: "owner_local_review" },
    { tool_id: "repository-change-protection", label: "Repository change protection", purpose: "Safe purpose.", owner_class: "Elim", destination_class: "protected_source" }
  ];
  const { api } = loadApi({
    schema_version: 2,
    availability: "current",
    complete: true,
    checked_at: "2026-07-28T20:00:00Z",
    public_intake_state: "unverified",
    private_attention: "required",
    active_incident: false,
    tools: [
      { tool_id: "credential-access-review", availability: "current", last_checked: "2026-07-28T20:00:00Z", coverage_state: "current", private_attention: "yes", owner_class: "Human", destination_class: "owner_local_review", active_incident: false, public_intake_state: null, next_due: null, source_revision: "safe-revision", label: "Credential and access review" },
      { tool_id: "repository-change-protection", availability: "current", last_checked: "2026-07-28T20:00:00Z", coverage_state: "current", private_attention: "yes", owner_class: "Elim", destination_class: "protected_source", active_incident: false, public_intake_state: null, next_due: null, source_revision: "safe-revision", label: "Repository change protection" }
    ]
  }, {
    security_assurance: { schema_version: 2, availability: "unavailable", complete: false, tools: publicTools }
  });
  const projection = api.securityAssuranceProjection();
  assert.equal(projection.available, true);
  assert.equal(projection.privateAttention, "required");
  assert.equal(api.securityActionRecords().filter((record) => record.attention === "human").length, 1);
  assert.equal(api.securityActionRecords().filter((record) => record.attention === "agent").length, 1);
  assert.ok(api.securityActionRecords().every((record) => !record.message.includes("credential-access-review")));
});

test("security assurance fails closed on vulnerability-shaped or unknown fields", () => {
  const { api } = loadApi({
    schema_version: 2,
    availability: "current",
    complete: true,
    checked_at: "2026-07-28T20:00:00Z",
    public_intake_state: "live",
    private_attention: "none_reported",
    active_incident: false,
    tools: [{
      tool_id: "credential-access-review",
      label: "Credential and access review",
      availability: "current",
      coverage_state: "current",
      private_attention: "no",
      owner_class: "Human",
      destination_class: "owner_local_review",
      active_incident: false,
      vulnerability_message: "must not enter the Console"
    }]
  }, {
    security_assurance: {
      schema_version: 2,
      tools: [{ tool_id: "credential-access-review", label: "Credential and access review", purpose: "Safe purpose." }]
    }
  });
  assert.equal(api.securityAssuranceProjection().available, false);
  assert.equal(api.securityActionRecords().length, 0);
});

test("security assurance exposes staged safe actions and keyboard navigation", () => {
  const app = fs.readFileSync(appPath, "utf8");
  const html = fs.readFileSync(indexPath, "utf8");
  assert.match(html, /id="refresh-security-status"/);
  assert.match(app, /prepare_public_intake_state_request/);
  assert.match(app, /execution: "staged_request_only"/);
  assert.match(app, /mixed_state_response: "record_operational_incident"/);
  assert.match(app, /event\.key === "ArrowDown"/);
  assert.doesNotMatch(app, /arbitrary_command_execution"\]\s*,?\s*commands:/);
});

test("owner-local projections load only from canonical disk or loopback mode", async () => {
  const { api } = loadApi();
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "file:",
    hostname: "",
    pathname: "/Users/example/ARRP/research/horizon-review-console/index.html"
  }), true);
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "file:",
    hostname: "",
    pathname: "/Users/example/ARRP/research/horizon-review-console/copy.html"
  }), false);
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "file:",
    hostname: "localhost",
    pathname: "/Users/example/ARRP/research/horizon-review-console/index.html"
  }), false);
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "http:",
    hostname: "127.0.0.1",
    pathname: "/index.html"
  }), true);
  assert.equal(api.localConsoleOriginAllowed({
    protocol: "https:",
    hostname: "arrp.org",
    pathname: "/research/horizon-review-console/index.html"
  }), false);

  const priorWindow = globalThis.window;
  const priorDocument = globalThis.document;
  let appended = 0;
  globalThis.window = {
    location: {
      protocol: "file:",
      hostname: "",
      pathname: "/Users/example/ARRP/research/horizon-review-console/index.html"
    }
  };
  globalThis.document = {
    createElement() { return {}; },
    head: {
      append(script) {
        appended += 1;
        script.onerror();
      }
    }
  };
  try {
    assert.equal(await api.loadLocalProjection("data/missing.js", () => false), false);
    assert.equal(appended, 1);
  } finally {
    if (priorWindow === undefined) delete globalThis.window;
    else globalThis.window = priorWindow;
    if (priorDocument === undefined) delete globalThis.document;
    else globalThis.document = priorDocument;
  }
});

test("private operations require exact generation and revision binding", () => {
  const { api } = loadApi({}, {
    generation_id: "generation-current",
    source_revision: "revision-current"
  });
  const snapshot = {
    schema_version: 2,
    availability: "current",
    generated_at: "2026-07-28T20:00:00Z",
    catalog_generation_id: "generation-current",
    source_revision: "revision-current",
    agent_registry: [],
    project_logs: [],
    integrity: {},
    run_chain: {},
    privacy: "Owner-only local projection."
  };
  assert.equal(api.validPrivateOperationsSnapshot(snapshot), true);
  assert.equal(api.validPrivateOperationsSnapshot({
    ...snapshot,
    catalog_generation_id: "older-generation"
  }), false);
});

test("role surfaces share the typed projection and exact owner-only control state", () => {
  const { api } = loadApi({}, {
    automation_role_status: {
      availability: "current",
      control_state: { state: "unavailable" },
      roles: [
        {
          id: "run-coordinator-bot",
          latest_scheduled: { available: false },
          data_currentness: { state: "current" }
        },
        {
          id: "project-integrity-bot",
          latest_scheduled: { available: true, outcome: "succeeded", at: "2026-07-27T08:00:00Z" },
          data_currentness: { state: "current" }
        }
      ]
    }
  });
  const projection = api.effectiveAutomationRoleStatusProjection(
    undefined,
    {
      control_state: "paused",
      control_state_checked_at: "2026-07-28T12:00:00Z",
      trigger: "scheduled",
      status: "paused",
      scheduled_for: "2026-07-28T02:00:00-04:00",
      updated_at: "2026-07-28T12:00:00Z",
      run_id: "RUN-1"
    }
  );
  assert.equal(projection.control_state.state, "paused");
  assert.ok(projection.roles.every((role) => role.pause_state === "paused"));
  assert.equal(projection.roles[0].latest_scheduled.outcome, "paused");
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

test("Overview green status requires every brief feed and the loaded generation to verify", () => {
  const generation = "project-console-overview-test";
  const timestamp = "2026-07-28T12:00:00Z";
  const currentFeed = {
    availability: "current",
    generated_at: timestamp,
    completeness: { complete: true }
  };
  const runChain = {
    ...currentFeed,
    chain_id: "arrp-test",
    status: "complete"
  };
  const { api, data } = loadApi({}, {
    generation_id: generation,
    generation_manifest: {
      files: {
        "overview.js": {
          generation_id: generation,
          sha256: `sha256:${"b".repeat(64)}`,
          bytes: 123
        }
      }
    },
    domain_generation: { "overview.js": generation },
    overview: {
      progress_summary: { ...currentFeed },
      integrity_summary: { ...currentFeed },
      source_checker_summary: { ...currentFeed, checked_at: timestamp }
    }
  });

  assert.equal(api.overviewBriefVerification(runChain).verified, true);
  data.overview.source_checker_summary.availability = "stale";
  const stale = api.overviewBriefVerification(runChain);
  assert.equal(stale.verified, false);
  assert.deepEqual(stale.failed.map((entry) => entry.label), ["Source checks"]);
});

test("Current Project Brief dots distinguish success, pause, blockers, and unknown readiness", () => {
  const { api } = loadApi();
  const currentVerification = {
    verified: true,
    bundleVerified: true,
    failed: []
  };
  const staleVerification = {
    verified: false,
    bundleVerified: true,
    failed: [{
      timestampValid: true,
      state: { state: "stale", complete: true, reason: "" }
    }]
  };
  const readiness = {
    latest_attempt: { available: true, blockers: [], blocker_count: 0 },
    latest_scheduled_attempt: { available: false },
    future_run_gates: { available: true, items: [], count: 0 }
  };
  const completed = {
    trigger: "scheduled",
    status: "completed",
    control_state: "run",
    updated_at: "2026-07-28T08:55:33Z"
  };
  const healthy = api.overviewBriefFactStates({}, readiness, currentVerification, completed);
  assert.equal(healthy.latest.tone, "success");
  assert.equal(healthy.lastSuccessful.tone, "success");
  assert.equal(healthy.nextRun.tone, "success");
  assert.equal(healthy.nextEpoch.tone, "success");

  const paused = api.overviewBriefFactStates({}, readiness, staleVerification, {
    ...completed,
    status: "paused",
    control_state: "paused",
    validation_summary: { reason: "owner_pause_file_present" }
  });
  assert.equal(paused.data.tone, "warning");
  assert.equal(paused.latest.tone, "warning");
  assert.equal(paused.lastSuccessful.tone, "warning");
  assert.equal(paused.nextRun.tone, "warning");

  const scopedBlocker = {
    ...readiness,
    future_run_gates: {
      available: true,
      count: 1,
      items: [{ id: "ordinary-only", run_scope: "ordinary" }]
    }
  };
  const blocked = api.overviewBriefFactStates({}, scopedBlocker, currentVerification, {
    ...completed,
    status: "paused",
    control_state: "paused"
  });
  assert.equal(blocked.latest.tone, "error");
  assert.equal(blocked.nextRun.tone, "error");
  assert.equal(blocked.nextEpoch.tone, "warning");

  const unknown = api.overviewBriefFactStates({}, {
    latest_attempt: { available: false, blockers: [] },
    latest_scheduled_attempt: { available: false },
    future_run_gates: { available: false, items: [] }
  }, currentVerification, {});
  assert.equal(unknown.latest.tone, "unavailable");
  assert.equal(unknown.nextRun.tone, "unavailable");
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

test("independent cloud-health and host-status payloads validate", () => {
  const { api } = loadApi();
  assert.equal(api.validateLivePayload("automation-health", {
    schema_version: 1,
    projection_kind: "cloud-automation-health",
    chain_id: "cloud-run-123",
    workflow_run_id: "123",
    status: "failed",
    updated_at: "2026-07-26T08:45:00Z"
  }).valid, true);
  assert.equal(api.validateLivePayload("host-status", {
    schema_version: 1,
    projection_kind: "host-run-status",
    chain_id: "arrp-20260726T064933Z",
    host_status: "failed",
    host_updated_at: "2026-07-26T08:43:00Z",
    stage: "elim-isolated-checkout",
    host_closeout: {
      outcome: "completed",
      commit: "a".repeat(40),
      validated_at: "2026-07-26T08:42:00Z"
    }
  }).valid, true);
  assert.equal(api.validateLivePayload("host-status", {
    schema_version: 1,
    projection_kind: "host-run-status",
    chain_id: "arrp-20260726T064933Z",
    host_status: "completed",
    host_updated_at: "2026-07-26T08:43:00Z",
    stage: "elim-closeout",
    host_closeout: { commit: "short" }
  }).valid, false);
  assert.equal(api.validateLivePayload("host-status", {
    schema_version: 1,
    projection_kind: "host-run-status",
    chain_id: "arrp-20260726T064933Z",
    host_status: "failed",
    host_updated_at: "not-a-timestamp",
    stage: "elim-isolated-checkout"
  }).valid, false);
});

test("newer published host state controls the final chain outcome while retaining cloud state", () => {
  const { api } = loadApi();
  const cloud = api.reconcileRunChainSnapshot({}, {
    schema_version: 1,
    chain_id: "arrp-20260726T064933Z",
    status: "complete",
    updated_at: "2026-07-26T06:56:00Z",
    elim_decision: { launch_recommended: true },
    failures: []
  }, "cloud");
  assert.equal(cloud.status, "host_pending");
  assert.equal(cloud.cloud_status, "complete");

  const failedHost = api.reconcileRunChainSnapshot(cloud, {
    schema_version: 1,
    projection_kind: "host-run-status",
    chain_id: "arrp-20260726T064933Z",
    host_status: "failed",
    host_updated_at: "2026-07-26T08:43:00Z",
    stage: "elim-isolated-checkout",
    host_action_items: [{ id: "incident-1", resolved: false }]
  }, "host");
  assert.equal(failedHost.status, "failed");
  assert.equal(failedHost.host_status, "failed");
  assert.equal(failedHost.cloud_status, "complete");
  assert.equal(failedHost.status_source, "published-host");
  assert.equal(failedHost.host_action_items.length, 1);

  const olderHost = api.reconcileRunChainSnapshot(failedHost, {
    schema_version: 1,
    projection_kind: "host-run-status",
    chain_id: "arrp-20260726T064933Z",
    host_status: "running",
    host_updated_at: "2026-07-26T08:00:00Z",
    stage: "elim-launch"
  }, "host");
  assert.equal(olderHost.status, "failed");
  assert.equal(olderHost.host_updated_at, "2026-07-26T08:43:00Z");
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

test("operational readiness accepts an explicit failed legacy chain without calling it unavailable", () => {
  const { api } = loadApi();
  const state = api.operationalFeedState({
    chain_id: "arrp-20260726T140914Z",
    status: "failed",
    updated_at: "2026-07-26T14:20:00Z",
    failures: [{ stage: "elim" }]
  });
  assert.equal(state.state, "available");
  assert.equal(state.complete, true);
  assert.equal(api.integrityComponentValue(state, 1), 1);
  assert.equal(api.operationalFeedState({}).state, "undeclared");
});

test("host-recorded Elim runtime overrides a cloud decision that says it was not launched", () => {
  const { api } = loadApi();
  const presentation = api.elimRunChainPresentation({
    chain_id: "arrp-20260726T140914Z",
    elim_decision: {
      launch_recommended: false,
      reason: "Cloud decision was superseded by the host."
    },
    elim_runtime: {
      chain_id: "arrp-20260726T140914Z",
      status: "failed",
      summary: "Elim ran and was interrupted."
    }
  });
  assert.equal(presentation.label, "Failed");
  assert.equal(presentation.ran, true);
  assert.match(presentation.detail, /ran and was interrupted/i);
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

test("Pipeline deep links apply every managerial facet", () => {
  const { api } = loadApi();
  const state = api.applyPipelineParameters(
    "mode=hold&selected=ELEC-014&work_class=Proposal&scope=all&sort=due"
      + "&status=Blocked&development=Candidate&release_blocker=required"
      + "&workstream=ELEC&owner=Human&priority=Critical&gap=next_step_missing"
  );
  assert.deepEqual(JSON.parse(JSON.stringify({
    mode: state.mode,
    selectedId: state.selectedId,
    workClass: state.workClass,
    scope: state.scope,
    sort: state.sort,
    status: state.status,
    development: state.development,
    releaseBlocker: state.releaseBlocker,
    area: state.area,
    owner: state.owner,
    priority: state.priority,
    gap: state.gap
  })), {
    mode: "hold",
    selectedId: "ELEC-014",
    workClass: "Proposal",
    scope: "all",
    sort: "due",
    status: "Blocked",
    development: "Candidate",
    releaseBlocker: "required",
    area: "ELEC",
    owner: "Human",
    priority: "Critical",
    gap: "next_step_missing"
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
    affected_scope: "10 directive records.",
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
  assert.doesNotMatch(row.summary, /\.\./);
  assert.doesNotMatch(row.summary, /\?\./);
  assert.equal(row.target, "sources:watchers:directives");
  assert.equal(row.tone, "warning");
});

test("Action Inbox uses a uniform selectable list with an adjacent preview", () => {
  const app = fs.readFileSync(appPath, "utf8");
  const html = fs.readFileSync(indexPath, "utf8");
  const styles = fs.readFileSync(path.join(consoleDirectory, "styles.css"), "utf8");
  const start = app.indexOf("function actionInboxRow(");
  const end = app.indexOf("function integrityFindingNeedsHuman(", start);
  const renderer = app.slice(start, end);
  assert.ok(start >= 0 && end > start);
  assert.match(renderer, /element\("button", "action-inbox-row"\)/);
  assert.match(renderer, /renderActionInboxPreview/);
  assert.match(renderer, /ACTION_INBOX_LAYOUT_STORAGE_KEY/);
  assert.doesNotMatch(renderer, /element\("details"/);
  assert.match(html, /data-action-filter="mine" aria-pressed="true"/);
  assert.match(html, /id="action-item-preview"/);
  assert.match(styles, /\.action-inbox-workspace\s*\{/);
  assert.match(styles, /\.action-inbox-row\[aria-pressed="true"\]/);
});

test("Priority attention is deterministic, human-owned, and capped at five", () => {
  const { api } = loadApi();
  const now = Date.parse("2026-07-28T15:00:00Z");
  const records = api.priorityAttentionItems([
    { id: "ordinary", scope: "mine", title: "Ordinary unresolved work" },
    { id: "oversight", scope: "oversight", title: "High elsewhere", priority: "Critical" },
    { id: "blocker", scope: "mine", title: "Explicit blocker", blockingEffect: true },
    { id: "critical", scope: "mine", title: "Critical record", priority: "Critical" },
    { id: "overdue", scope: "mine", title: "Overdue record", dueAt: "2026-07-27T12:00:00Z" },
    { id: "high", scope: "mine", title: "High record", priority: "High" },
    { id: "due", scope: "mine", title: "Due record", dueAt: "2026-07-29T12:00:00Z" },
    { id: "decision", scope: "mine", title: "Consequential decision", consequentialDecision: true }
  ], now);
  assert.equal(records.length, 5);
  assert.deepEqual(
    records.map((record) => record.item.id),
    ["blocker", "overdue", "critical", "high", "due"]
  );
  assert.ok(records.every((record) => record.item.scope === "mine"));
  assert.ok(records.every((record) => record.reasons.length > 0));
  assert.ok(!records.some((record) => record.item.id === "ordinary"));
  assert.ok(!records.some((record) => record.item.id === "oversight"));
});

test("Console-wide Design mode offers safe grid widths stored separately from project defaults", () => {
  const app = fs.readFileSync(appPath, "utf8");
  const html = fs.readFileSync(indexPath, "utf8");
  const styles = fs.readFileSync(path.join(consoleDirectory, "styles.css"), "utf8");
  assert.match(html, /id="layout-edit-toggle"[^>]*>Design layout</);
  assert.match(app, /const LAYOUT_WIDTHS = Object\.freeze/);
  assert.match(app, /layoutSizeKey/);
  assert.match(app, /setLayoutItemWidth/);
  assert.match(app, /moveLayoutItemToZone/);
  assert.match(app, /LAYOUT_PLACEMENTS_KEY/);
  assert.match(app, /layoutTransferGroup = "overview-portlet"/);
  assert.match(app, /"Project default"/);
  assert.match(app, /if \(!layoutEditing\) \{/);
  assert.match(app, /classList\?\.contains\("layout-handle"\)/);
  assert.match(styles, /\.layout-zone\.layout-size-zone/);
  assert.match(styles, /body\.layout-editing #layout-edit-toggle/);
  assert.match(styles, /\.layout-container-select/);
  assert.match(styles, /\[data-layout-width="half"\]/);
  assert.match(styles, /\[data-layout-width="compact"\]/);
});

test("Planning and Operations consolidate navigation while preserving old routes", () => {
  const { api } = loadApi();
  const html = fs.readFileSync(indexPath, "utf8");
  const app = fs.readFileSync(appPath, "utf8");
  const styles = fs.readFileSync(path.join(consoleDirectory, "styles.css"), "utf8");
  const mainTabs = [...html.matchAll(/data-tab="([^"]+)"/g)].map((match) => match[1]);
  assert.deepEqual(mainTabs, [
    "overview",
    "actions",
    "progress",
    "planning",
    "integrity",
    "automation"
  ]);
  const planningTabs = [...html.matchAll(/data-subtab-group="planning" data-subtab="([^"]+)"/g)]
    .map((match) => match[1]);
  assert.deepEqual(planningTabs, [
    "workbench",
    "preliminary",
    "candidates",
    "sources",
    "publication"
  ]);
  assert.match(html, /data-subtab-group="automation" data-subtab="logs"/);
  assert.doesNotMatch(html, /data-tab="(?:candidates|sources|logs|publication)"/);
  assert.match(app, /initializeLogMenu/);
  assert.match(app, /operations-log-menu-button/);
  assert.doesNotMatch(app, /operations-log-selector/);
  assert.match(app, /setNavigationMarker/);
  assert.match(styles, /\.tab-status-dot\.error/);
  assert.equal(api.normalizeConsoleTarget("candidates:formal"), "planning:candidates");
  assert.equal(api.normalizeConsoleTarget("candidates:public"), "planning:preliminary");
  assert.equal(api.normalizeConsoleTarget("sources:watchers:source-checker"), "planning:sources:watchers:source-checker");
  assert.equal(api.normalizeConsoleTarget("publication:builder"), "planning:publication:builder");
  assert.equal(api.normalizeConsoleTarget("planning:next-work"), "planning:workbench:pipeline");
  assert.equal(api.normalizeConsoleTarget("planning:pipeline"), "planning:workbench:pipeline");
  assert.equal(api.normalizeConsoleTarget("progress:next-work:status=Blocked"), "planning:workbench:pipeline:status=Blocked&mode=hold");
  assert.equal(api.normalizeConsoleTarget("progress:next-work:cohort=Human-reserved"), "actions");
  assert.equal(
    api.normalizeConsoleTarget("progress:next-work:cohort=External-review%20follow-up"),
    "planning:workbench:pipeline:status=External+review&scope=review-ready"
  );
  assert.equal(api.normalizeConsoleTarget("logs:integrity"), "automation:logs:integrity");
  assert.equal(api.normalizeConsoleTarget("automation:administration"), "automation:overview");
  assert.equal(api.normalizeConsoleTarget("automation:chain"), "automation:overview");
  assert.equal(api.normalizeConsoleTarget("automation:agents"), "automation:agents:run-coordinator-bot");
});

test("Workbench links resolve only typed planning artifacts and retain source context", () => {
  const { api } = loadApi({}, {
    progress: {
      pipeline: {
        items: [
          { id: "PROP-014", workClass: "Proposal", mode: "active" },
          { id: "HOR-031", workClass: "Formal candidate", mode: "hold" },
          { id: "SRC-009", workClass: "Source", mode: "active" }
        ]
      }
    }
  });

  assert.equal(
    api.workbenchTargetForArtifact("PROP-014", {
      source: "integrity",
      reference: "INT-014",
      returnTarget: "integrity"
    }),
    "planning:workbench:pipeline:selected=PROP-014&focus=1&source=integrity&ref=INT-014&return=integrity"
  );
  assert.equal(
    api.workbenchTargetForArtifact("HOR-031"),
    "planning:workbench:pipeline:selected=HOR-031&focus=1&mode=hold"
  );
  assert.equal(api.workbenchTargetForArtifact("SRC-009"), null);
  assert.deepEqual(
    api.structuredArtifactIdentifiers({
      artifact_id: "PROP-014",
      affected_ids: ["HOR-031", "FINDING-009"],
      message: "Narrative happens to mention PROP-999"
    }),
    ["PROP-014", "HOR-031"]
  );
});

test("Workbench navigation rejects hostile routes and external URLs", () => {
  const { api } = loadApi();
  assert.equal(api.safeConsoleTarget("integrity"), "integrity");
  assert.equal(
    api.safeConsoleTarget("planning:workbench:pipeline:status=Development"),
    "planning:workbench:pipeline:status=Development"
  );
  for (const hostile of [
    "javascript:alert(1)",
    "data:text/html,boom",
    "unknown:screen",
    "planning:unknown",
    "planning:workbench:pipeline:unknown=value",
    "%E0%A4%A",
    `planning:workbench:pipeline:search=${"a".repeat(2100)}`,
    "integrity\u0000:overview"
  ]) {
    assert.equal(api.safeConsoleTarget(hostile), "overview");
  }

  assert.equal(
    api.safePipelineExternalUrl("https://github.com/Thorncrag/ARRP/issues/479"),
    "https://github.com/Thorncrag/ARRP/issues/479"
  );
  assert.equal(
    api.safePipelineExternalUrl(
      "https://github.com/Thorncrag/ARRP/blob/main/areas/TEST/issues/TEST-001.md#audit"
    ),
    "https://github.com/Thorncrag/ARRP/blob/main/areas/TEST/issues/TEST-001.md#audit"
  );
  for (const hostile of [
    "javascript:alert(1)",
    "data:text/html,boom",
    "//github.com/Thorncrag/ARRP/issues/479",
    "https://github.com.evil.test/Thorncrag/ARRP/issues/479",
    "https://github.com/Evil/ARRP/issues/479",
    "https://user:password@github.com/Thorncrag/ARRP/issues/479",
    "https://github.com:444/Thorncrag/ARRP/issues/479",
    "https://github.com/Thorncrag/ARRP/actions"
  ]) {
    assert.equal(api.safePipelineExternalUrl(hostile), null);
  }
});

test("typed Pipeline fails closed, preserves precedence, and uses deterministic ordering", () => {
  const items = [
    {
      id: "INTAKE-1",
      workClass: "Preliminary candidate",
      mode: "active",
      status: "Preliminary intake",
      readinessState: "not_applicable",
      nextActionState: "recorded",
      sortInputs: { classRank: 0, nextStepMissing: false, priorityRank: 99, identifier: "INTAKE-1" }
    },
    {
      id: "HOR-MISSING",
      workClass: "Formal candidate",
      mode: "active",
      status: "Development",
      readinessState: "not_applicable",
      nextActionState: "missing",
      sortInputs: { classRank: 1, nextStepMissing: true, priorityRank: 99, identifier: "HOR-MISSING" }
    },
    {
      id: "HOR-COMPLETE",
      workClass: "Formal candidate",
      mode: "active",
      status: "Development",
      readinessState: "not_applicable",
      nextActionState: "recorded",
      sortInputs: { classRank: 1, nextStepMissing: false, priorityRank: 99, identifier: "HOR-COMPLETE" }
    },
    {
      id: "PROP-0",
      workClass: "Proposal",
      mode: "active",
      status: "Development",
      readinessState: "not_ready",
      nextActionState: "recorded",
      score: 0,
      sortInputs: { classRank: 2, scoreDescending: 0, nextStepMissing: false, priorityRank: 99, identifier: "PROP-0" }
    },
    {
      id: "PROP-MISSING",
      workClass: "Proposal",
      mode: "active",
      status: "Development",
      readinessState: "not_ready",
      nextActionState: "recorded",
      score: null,
      sortInputs: { classRank: 2, scoreDescending: null, nextStepMissing: false, priorityRank: 99, identifier: "PROP-MISSING" }
    },
    {
      id: "PROP-READY",
      workClass: "Proposal",
      mode: "active",
      status: "External review",
      readinessState: "ready",
      nextActionState: "recorded",
      score: 80,
      sortInputs: { classRank: 2, scoreDescending: -80, nextStepMissing: false, priorityRank: 1, identifier: "PROP-READY" }
    },
    {
      id: "PROP-HOLD",
      workClass: "Proposal",
      mode: "hold",
      status: "Blocked",
      readinessState: "not_ready",
      nextActionState: "recorded",
      hold: { holdSince: "2026-07-01", provenanceState: "verified" },
      sortInputs: { classRank: 2, nextStepMissing: false, priorityRank: 1, identifier: "PROP-HOLD" }
    },
    {
      id: "PROP-HUMAN",
      workClass: "Proposal",
      mode: "human_action",
      status: "Human decision needed",
      readinessState: "not_ready",
      nextActionState: "recorded",
      sortInputs: { classRank: 2, nextStepMissing: false, priorityRank: 0, identifier: "PROP-HUMAN" }
    }
  ];
  const { api } = loadApi({}, {
    records: [],
    active_horizon_records: [],
    progress: {
      generation_id: "generation-1",
      proposals: items.filter((item) => item.workClass === "Proposal"),
      pipeline: {
        schemaVersion: 1,
        availability: "current",
        progressGenerationId: "generation-1",
        sourceCounts: { preliminaryCandidates: 0, formalCandidates: 0, proposals: 5 },
        items
      }
    }
  });
  assert.equal(api.pipelineProjectionState().available, true);
  api.applyPipelineParameters("mode=active&scope=active-development");
  const active = api.filteredPipelineItems(items);
  assert.deepEqual(
    active.map((item) => item.id),
    ["INTAKE-1", "HOR-COMPLETE", "HOR-MISSING", "PROP-0", "PROP-MISSING"]
  );
  assert.ok(!active.some((item) => item.id === "PROP-READY"));
  assert.ok(!active.some((item) => item.id === "PROP-HUMAN"));
  api.applyPipelineParameters("mode=hold");
  assert.deepEqual(api.filteredPipelineItems(items).map((item) => item.id), ["PROP-HOLD"]);

  const stale = loadApi({}, {
    records: [],
    active_horizon_records: [],
    progress: {
      generation_id: "generation-2",
      proposals: [],
      pipeline: {
        schemaVersion: 1,
        availability: "current",
        progressGenerationId: "older-generation",
        sourceCounts: { preliminaryCandidates: 0, formalCandidates: 0, proposals: 0 },
        items: []
      }
    }
  });
  assert.equal(stale.api.pipelineProjectionState().available, false);
});

test("initial HTML loads only bounded scripts and stays within declared budgets", () => {
  const html = fs.readFileSync(indexPath, "utf8");
  const app = fs.readFileSync(appPath, "utf8");
  const scriptSources = [...html.matchAll(/<script\s+src="([^"]+)"/g)].map((match) => match[1]);
  assert.deepEqual(scriptSources, [
    "catalog-data.js?v=48",
    "app.js?v=65"
  ]);
  assert.match(app, /const PRIVATE_SECURITY_ASSURANCE_PATH = "data\/private-security-assurance\.js\?v=1";/);
  assert.match(app, /const PRIVATE_OPERATIONS_PATH = "data\/private-operations\.js\?v=1";/);
  assert.match(app, /const LOCAL_AUTOMATION_STATUS_PATH = "data\/local-automation-status\.js";/);
  assert.match(app, /return loadLocalProjection\(\s*PRIVATE_SECURITY_ASSURANCE_PATH,\s*capturePrivateSecurityAssurance\s*\)/);
  assert.match(app, /return loadLocalProjection\(PRIVATE_OPERATIONS_PATH, capturePrivateOperations\)/);
  assert.match(app, /return loadLocalProjection\(\s*LOCAL_AUTOMATION_STATUS_PATH,\s*captureLocalAutomationStatus\s*\)/);
  assert.match(app, /if \(window\.__ARRP_CONSOLE_TEST_MODE__\) capturePrivateSecurityAssurance\(\);/);
  assert.doesNotMatch(app, /\n  capturePrivateSecurityAssurance\(\);/);
  assert.match(html, /data-initial-script-budget-kib="605"/);
  assert.match(html, /data-initial-dom-budget="1500"/);
  const bytes = ["catalog-data.js", "app.js"]
    .map((file) => fs.statSync(path.join(consoleDirectory, file)).size)
    .reduce((sum, size) => sum + size, 0);
  assert.ok(bytes <= 605 * 1024, `synchronous JavaScript is ${bytes} bytes`);
  const approximateElementCount = (html.match(/<[a-z][^!/][^>]*>/gi) || []).length;
  assert.ok(approximateElementCount <= 1500, `initial HTML has about ${approximateElementCount} elements`);
  assert.doesNotMatch(html, /<script\s+src="data\/(?:candidates|sources|progress|integrity|automation|logs|publication)/);
  assert.doesNotMatch(html, /private-security-assurance|private-operations|local-automation-status/);
  assert.doesNotMatch(html, /role="tabpanel"[^>]*tabindex="0"/);
  assert.match(html, /Recent material activity/);
  assert.match(html, /id="pages-pagination"/);
  assert.match(html, /id="court-watch-pagination"/);
  assert.match(html, /id="pipeline-development"/);
  assert.match(html, /id="pipeline-release-blocker"/);
  assert.match(html, /id="pipeline-area"/);
  assert.match(html, /id="pipeline-owner"/);
  assert.match(html, /id="pipeline-workspace"/);
  assert.doesNotMatch(html, /id="progress-next-work"/);
  assert.match(html, /id="proposed-monitoring"/);
  assert.match(html, /id="proposed-trigger"/);
  assert.match(html, /id="publication-release-blockers-list"/);
  assert.doesNotMatch(html, /id="tab-logs-count"/);
  assert.match(html, /id="tab-automation-count"/);
  assert.match(html, /id="automation-logs-incident-count"/);
  assert.match(html, /id="log-incidents-count"/);
  assert.match(html, /id="log-panel-incidents"/);
});

test("operational incidents remain typed, human-owned only when explicit, and unavailable is not zero", () => {
  const unavailable = loadApi({}, {
    operational_incidents: {
      availability: "unavailable",
      complete: false,
      unresolved_count: null,
      impact_state: "gray",
      reason: "producer unavailable",
      items: []
    }
  });
  assert.equal(unavailable.api.operationalIncidentProjection().complete, false);
  assert.equal(unavailable.api.operationalIncidentProjection().unresolvedCount, null);
  assert.deepEqual(unavailable.api.unresolvedOperationalIncidents(), []);

  const current = loadApi({}, {
    operational_incidents: {
      availability: "current",
      complete: true,
      unresolved_count: 2,
      impact_state: "red",
      active_links: {
        "automation-role:run-coordinator-bot": ["INC-2026-001"]
      },
      items: [
        {
          incident_id: "INC-2026-001",
          status: "open",
          impact: "blocking",
          owner: "Human"
        },
        {
          incident_id: "INC-2026-002",
          status: "monitoring",
          impact: "degraded",
          owner: "Elim"
        },
        {
          incident_id: "INC-2026-003",
          status: "resolved",
          impact: "blocking",
          owner: "Human"
        }
      ]
    }
  });
  assert.equal(current.api.operationalIncidentProjection().unresolvedCount, 2);
  assert.deepEqual(
    current.api.unresolvedOperationalIncidents().map((item) => item.incident_id),
    ["INC-2026-001", "INC-2026-002"]
  );
  assert.equal(current.api.humanOwnsIncident(current.data.operational_incidents.items[0]), true);
  assert.equal(current.api.humanOwnsIncident(current.data.operational_incidents.items[1]), false);
  assert.equal(current.api.incidentStatusPresentation(current.data.operational_incidents.items[0]).tone, "error");
});

test("platform projection has five provider-neutral cells and exact scoped dependencies", () => {
  const { api } = loadApi();
  const checkedAt = "2026-07-28T20:00:00Z";
  const openai = api.platformProviderObservation(
    "openai",
    { components: [
      { id: "oa-gpts", name: "GPTs", status: "operational" },
      { id: "oa-codex", name: "Codex API", status: "degraded_performance" },
      { id: "oa-api", name: "Responses", status: "operational" }
    ] },
    { incidents: [] },
    checkedAt
  );
  const vercel = api.platformProviderObservation(
    "vercel",
    { components: [
      { id: "j7g76bfzc8hw", name: "CDN", status: "operational" },
      { id: "kgcsn9c73xzf", name: "Functions", status: "operational" },
      { id: "xxh50pzvy03x", name: "Firewall", status: "operational" },
      { id: "bc3cl3q4jn9m", name: "TLS Certificates", status: "operational" },
      { id: "7ckq6xr6nsbv", name: "Builds", status: "partial_outage" },
      { id: "hpqj1ys9gr78", name: "Git Integrations", status: "operational" },
      { id: "rsp3h37vv009", name: "AI Gateway", status: "major_outage" }
    ] },
    { incidents: [
      { id: "relevant", name: "Build delay", components: [{ id: "7ckq6xr6nsbv" }] },
      { id: "unrelated", name: "AI Gateway issue", components: [{ id: "rsp3h37vv009" }] }
    ] },
    checkedAt
  );
  const cloudflare = api.platformProviderObservation(
    "cloudflare",
    { components: [
      { id: "m4jywscr0n0k", name: "Turnstile", status: "operational" },
      { id: "unrelated-tunnel", name: "Cloudflare Tunnel", status: "major_outage" }
    ] },
    { incidents: [
      { id: "unrelated", name: "Tunnel issue", components: [{ id: "unrelated-tunnel" }] }
    ] },
    checkedAt
  );
  const cells = api.platformCellProjection({ openai, vercel, cloudflare });
  assert.deepEqual(cells.map((item) => item.label), [
    "GPTs", "Codex", "API platform", "Vercel", "Cloudflare Turnstile"
  ]);
  assert.equal(cells.find((item) => item.label === "Codex").status, "degraded_performance");
  assert.equal(cells.find((item) => item.label === "Vercel").status, "partial_outage");
  assert.deepEqual(vercel.incidents.map((item) => item.id), ["relevant"]);
  assert.equal(cells.find((item) => item.label === "Cloudflare Turnstile").status, "operational");
  assert.deepEqual(cloudflare.incidents, []);
});

test("platform provider failures are isolated and retain last-valid identity", () => {
  const { api } = loadApi();
  const checkedAt = "2026-07-28T20:00:00Z";
  const priorCloudflare = api.platformProviderObservation(
    "cloudflare",
    { components: [{ id: "m4jywscr0n0k", name: "Turnstile", status: "operational" }] },
    { incidents: [] },
    checkedAt
  );
  const unavailableCloudflare = api.platformProviderObservation(
    "cloudflare",
    { components: [{ id: "m4jywscr0n0k", name: "Wrong name", status: "operational" }] },
    { incidents: [] },
    "2026-07-28T21:00:00Z",
    priorCloudflare
  );
  assert.equal(unavailableCloudflare.complete, false);
  assert.equal(unavailableCloudflare.aggregate, "unavailable");
  assert.equal(unavailableCloudflare.lastValid.checkedAt, checkedAt);
  assert.equal(api.platformStatusPresentation("under_maintenance").tone, "warning");
  assert.equal(api.platformStatusPresentation("major_outage").tone, "error");
  assert.equal(api.platformStatusPresentation("unavailable").tone, "unavailable");
});

test("platform sources are exact and advisory rendering does not create incidents", () => {
  const app = fs.readFileSync(appPath, "utf8");
  assert.match(app, /https:\/\/www\.vercel-status\.com\/api\/v2\/status\.json/);
  assert.match(app, /https:\/\/www\.vercel-status\.com\/api\/v2\/components\.json/);
  assert.match(app, /https:\/\/www\.cloudflarestatus\.com\/api\/v2\/components\.json/);
  assert.match(app, /m4jywscr0n0k/);
  assert.match(app, /row\.setAttribute\("aria-label", `\$\{service\.label\}: \$\{presentation\.label\}/);
  assert.doesNotMatch(app, /record_incident.*platform|createIncident.*platform/i);
});

test("local automation status distinguishes unavailable, running, failure, review, and success", () => {
  const { api } = loadApi();
  assert.deepEqual(api.localAutomationPresentation(null), {
    available: false,
    tone: "unavailable",
    label: "Unavailable",
    summary: "The optional ignored local status feed is not present; no health conclusion is inferred."
  });
  assert.equal(api.localAutomationPresentation({ status: "running", stage: "12_validate" }).label, "Running");
  assert.equal(api.localAutomationPresentation({ status: "failed" }).tone, "error");
  assert.equal(api.localAutomationPresentation({ status: "review-required" }).label, "Review required");
  assert.equal(api.localAutomationPresentation({ status: "completed" }).tone, "success");
  assert.equal(api.validLocalAutomationStatus({
    schema_version: "1.0",
    status: "completed",
    updated_at: new Date().toISOString()
  }), true);
  assert.equal(api.validLocalAutomationStatus({
    schema_version: "1.0",
    status: "unexpected",
    updated_at: new Date().toISOString()
  }), false);
  assert.equal(api.localAutomationPresentation({
    status: "completed",
    updated_at: "2020-01-01T00:00:00Z"
  }).label, "Stale");
});
