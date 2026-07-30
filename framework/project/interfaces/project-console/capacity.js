(function (global) {
  "use strict";

  const fields = (value) => new Set(value.split(" "));
  const TOP_FIELDS = fields("schema_version projection_id producer_id sampler_cadence_seconds generated_at trustworthy_through availability completeness reason_code current_through current history reset_windows anomalies estimates");
  const CURRENT_FIELDS = fields("observed_at plan_type used_percent remaining_percent window_minutes resets_at reset_identity");
  const HISTORY_FIELDS = fields("observed_at event_type plan_type used_percent remaining_percent window_minutes resets_at reset_identity");
  const WINDOW_FIELDS = fields("reset_identity first_observed last_observed window_minutes resets_at plan_types min_used_percent max_used_percent observation_count material");
  const ANOMALY_FIELDS = fields("anomaly_id type observed_at observed_reset_identity current_reset_identity");
  const ESTIMATE_FIELDS = fields("available budget_available budget_reason_code burn_rate_available burn_rate_reason_code coverage_hours sample_count average_percent_per_day projected_exhaustion_at remaining_percent_per_day_budget confidence");
  const PROJECTION_REASONS = new Set(["no_valid_usage_observation", "owner_local_projection_required", "source_unavailable", "usage_readback_stale", "usage_readback_invalid"]);
  const BUDGET_REASONS = new Set(["projection_unavailable", "reset_boundary_elapsed", "budget_input_unavailable"]);
  const BURN_REASONS = new Set(["projection_unavailable", "burn_rate_input_unavailable", "insufficient_observation_coverage", "nonpositive_usage_change"]);
  const EVENT_TYPES = new Set(["baseline", "usage_change", "reset_change", "plan_change"]);
  const hasExactFields = (value, expected) => {
    const keys = value && typeof value === "object" ? Object.keys(value) : [];
    return keys.length === expected.size && keys.every((key) => expected.has(key));
  };
  const parseTimestamp = (value) => {
    if (typeof value !== "string"
      || !/^\d{4}-\d{2}-\d{2}T.+(?:Z|[+-]\d{2}:\d{2})$/.test(value)) return null;
    const timestamp = Date.parse(value);
    return Number.isFinite(timestamp) ? timestamp : null;
  };

  function validProjection(snapshot, now = Date.now()) {
    if (!hasExactFields(snapshot, TOP_FIELDS)
      || snapshot.schema_version !== 2
      || snapshot.projection_id !== "codex-usage"
      || snapshot.producer_id !== "owner-local-codex-usage-sampler"
      || snapshot.sampler_cadence_seconds !== 1800
      || !["current", "unavailable"].includes(snapshot.availability)
      || !["complete", "incomplete"].includes(snapshot.completeness)
      || !Array.isArray(snapshot.history) || snapshot.history.length > 512
      || !Array.isArray(snapshot.reset_windows) || snapshot.reset_windows.length > 64
      || !Array.isArray(snapshot.anomalies) || snapshot.anomalies.length > 64
      || !hasExactFields(snapshot.estimates, ESTIMATE_FIELDS)) return false;
    const projectionCurrent = snapshot.availability === "current";
    const validId = (value, maximum = 128) => typeof value === "string"
      && value.length <= maximum && /^[a-z0-9][a-z0-9._-]*$/.test(value);
    const validPercent = (value) => Number.isFinite(value) && value >= 0 && value <= 100;
    const validResetTime = (value) => Number.isInteger(value)
      && value >= 946684800 && value <= 4102444800;
    const validResetIdentity = (identity, windowMinutes, resetsAt) =>
      typeof identity === "string"
      && /^[1-9][0-9]{0,6}:[1-9][0-9]{0,11}$/.test(identity)
      && identity === `${windowMinutes}:${Math.floor(resetsAt / 60)}`;
    const generatedAt = parseTimestamp(snapshot.generated_at);
    const validUsageRecord = (record, expected, current = false) => {
      const observedAt = parseTimestamp(record?.observed_at);
      return hasExactFields(record, expected)
        && observedAt !== null && generatedAt !== null && observedAt <= generatedAt
        && validId(record.plan_type, 64)
        && validPercent(record.used_percent) && validPercent(record.remaining_percent)
        && Math.abs(record.used_percent + record.remaining_percent - 100) <= 0.001
        && record.window_minutes === 10080
        && validResetTime(record.resets_at)
        && validResetIdentity(record.reset_identity, record.window_minutes, record.resets_at)
        && record.resets_at * 1000 >= observedAt
        && (current || EVENT_TYPES.has(record.event_type));
    };
    let currentThrough = null;
    if (projectionCurrent) {
      currentThrough = parseTimestamp(snapshot.current_through);
      const trustworthy = parseTimestamp(snapshot.trustworthy_through);
      if (snapshot.completeness !== "complete" || snapshot.reason_code !== null
        || generatedAt === null || currentThrough === null || trustworthy === null
        || currentThrough > generatedAt || now > trustworthy
        || !validUsageRecord(snapshot.current, CURRENT_FIELDS, true)
        || currentThrough !== parseTimestamp(snapshot.current.observed_at)
        || trustworthy !== Math.min(
          currentThrough + snapshot.sampler_cadence_seconds * 1000,
          snapshot.current.resets_at * 1000
        )
        || generatedAt > trustworthy) return false;
    } else if (snapshot.completeness !== "incomplete"
      || !PROJECTION_REASONS.has(snapshot.reason_code)
      || snapshot.current !== null || snapshot.current_through !== null
      || snapshot.trustworthy_through !== null
      || snapshot.history.length || snapshot.reset_windows.length
      || snapshot.anomalies.length
      || (snapshot.generated_at !== null && generatedAt === null)) return false;
    if (projectionCurrent) {
      if (!snapshot.history.every((record) =>
        validUsageRecord(record, HISTORY_FIELDS))) return false;
      const historyTimes = snapshot.history.map((record) =>
        parseTimestamp(record.observed_at));
      const historyIds = snapshot.history.map((record) =>
        `${record.observed_at}|${record.event_type}|${record.reset_identity}`);
      if (historyTimes.some((value, index) =>
        index && value < historyTimes[index - 1])
        || historyTimes.some((value) => value > currentThrough)
        || new Set(historyIds).size !== historyIds.length) return false;
      if (!snapshot.reset_windows.every((record) => {
        const first = parseTimestamp(record?.first_observed);
        const last = parseTimestamp(record?.last_observed);
        return hasExactFields(record, WINDOW_FIELDS)
          && first !== null && last !== null && first <= last
          && last <= generatedAt
          && record.window_minutes === 10080
          && validResetTime(record.resets_at)
          && validResetIdentity(record.reset_identity, record.window_minutes, record.resets_at)
          && last <= record.resets_at * 1000
          && Array.isArray(record.plan_types)
          && record.plan_types.length >= 1 && record.plan_types.length <= 8
          && record.plan_types.every((value) => validId(value, 64))
          && record.plan_types.join("|") ===
            [...new Set(record.plan_types)].sort().join("|")
          && validPercent(record.min_used_percent)
          && validPercent(record.max_used_percent)
          && record.min_used_percent <= record.max_used_percent
          && Number.isInteger(record.observation_count)
          && record.observation_count >= 1
          && typeof record.material === "boolean";
      })) return false;
      const windowIds = snapshot.reset_windows.map((record) =>
        record.reset_identity);
      const windowTimes = snapshot.reset_windows.map((record) =>
        record.resets_at);
      if (new Set(windowIds).size !== windowIds.length
        || windowTimes.some((value, index) =>
          index && value < windowTimes[index - 1])) return false;
      if (!snapshot.anomalies.every((record) =>
        hasExactFields(record, ANOMALY_FIELDS)
        && /^conflicting-reset-[1-9][0-9]{0,6}-[1-9][0-9]{0,11}-[1-9][0-9]{0,11}$/.test(record.anomaly_id)
        && record.type === "conflicting_reset_identity"
        && parseTimestamp(record.observed_at) !== null
        && parseTimestamp(record.observed_at) <= generatedAt
        && /^[1-9][0-9]{0,6}:[1-9][0-9]{0,11}$/.test(record.observed_reset_identity)
        && /^[1-9][0-9]{0,6}:[1-9][0-9]{0,11}$/.test(record.current_reset_identity)
        && record.observed_reset_identity !==
          record.current_reset_identity)) return false;
      const anomalyIds = snapshot.anomalies.map((record) =>
        record.anomaly_id);
      const anomalyTimes = snapshot.anomalies.map((record) =>
        parseTimestamp(record.observed_at));
      if (new Set(anomalyIds).size !== anomalyIds.length
        || anomalyTimes.some((value, index) =>
          index && value < anomalyTimes[index - 1])) return false;
    }
    const estimate = snapshot.estimates;
    if (!["available", "budget_available", "burn_rate_available"].every(
      (key) => typeof estimate[key] === "boolean"
    ) || estimate.available !== (
      estimate.budget_available || estimate.burn_rate_available
    )) return false;
    if (!projectionCurrent) {
      return !estimate.available && !estimate.budget_available
        && estimate.budget_reason_code === "projection_unavailable"
        && !estimate.burn_rate_available
        && estimate.burn_rate_reason_code === "projection_unavailable"
        && [
          "coverage_hours", "sample_count", "average_percent_per_day",
          "projected_exhaustion_at", "remaining_percent_per_day_budget",
          "confidence"
        ].every((key) => estimate[key] === null);
    }
    if (!Number.isFinite(estimate.coverage_hours)
      || estimate.coverage_hours < 0
      || !Number.isInteger(estimate.sample_count)
      || estimate.sample_count < 1
      || !["unavailable", "low", "medium", "high"].includes(
        estimate.confidence
      )) return false;
    if (estimate.budget_available
      ? (estimate.budget_reason_code !== null
        || !Number.isFinite(estimate.remaining_percent_per_day_budget)
        || estimate.remaining_percent_per_day_budget < 0)
      : (!BUDGET_REASONS.has(estimate.budget_reason_code)
        || estimate.remaining_percent_per_day_budget !== null)) return false;
    if (estimate.burn_rate_available
      ? (estimate.burn_rate_reason_code !== null
        || !Number.isFinite(estimate.average_percent_per_day)
        || estimate.average_percent_per_day < 0
        || parseTimestamp(estimate.projected_exhaustion_at) === null
        || parseTimestamp(estimate.projected_exhaustion_at) < currentThrough
        || estimate.confidence === "unavailable")
      : (!BURN_REASONS.has(estimate.burn_rate_reason_code)
        || estimate.average_percent_per_day !== null
        || estimate.projected_exhaustion_at !== null)) return false;
    return true;
  }

  function integrityMaterial(value) {
    if (value === null) return "n;";
    if (value === true) return "b1;";
    if (value === false) return "b0;";
    if (typeof value === "number" && Number.isFinite(value)) {
      const buffer = new ArrayBuffer(8);
      new DataView(buffer).setFloat64(0, value, false);
      const bytes = [...new Uint8Array(buffer)]
        .map((byte) => byte.toString(16).padStart(2, "0")).join("");
      return `f${bytes};`;
    }
    if (typeof value === "string") {
      return `s${new TextEncoder().encode(value).length}:${value}`;
    }
    if (Array.isArray(value)) {
      return `a${value.length}[${value.map(integrityMaterial).join("")}]`;
    }
    if (value && typeof value === "object") {
      const keys = Object.keys(value).sort();
      return `o${keys.length}{${keys.map((key) =>
        integrityMaterial(key) + integrityMaterial(value[key])).join("")}}`;
    }
    throw new TypeError("unsupported Codex usage payload value");
  }

  function sha256(bytes) {
    const constants = [
      0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
      0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
      0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
      0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
      0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
      0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
      0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
      0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    ];
    const paddedLength = Math.ceil((bytes.length + 9) / 64) * 64;
    const message = new Uint8Array(paddedLength);
    message.set(bytes);
    message[bytes.length] = 0x80;
    const bitLength = bytes.length * 8;
    const view = new DataView(message.buffer);
    view.setUint32(
      paddedLength - 8,
      Math.floor(bitLength / 0x100000000),
      false
    );
    view.setUint32(paddedLength - 4, bitLength >>> 0, false);
    const hash = new Uint32Array([
      0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
      0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    ]);
    const words = new Uint32Array(64);
    const rotate = (value, count) =>
      (value >>> count) | (value << (32 - count));
    for (let offset = 0; offset < paddedLength; offset += 64) {
      for (let index = 0; index < 16; index += 1) {
        words[index] = view.getUint32(offset + index * 4, false);
      }
      for (let index = 16; index < 64; index += 1) {
        const left = words[index - 15];
        const right = words[index - 2];
        const sigma0 = rotate(left, 7) ^ rotate(left, 18) ^ (left >>> 3);
        const sigma1 = rotate(right, 17) ^ rotate(right, 19) ^ (right >>> 10);
        words[index] = (
          words[index - 16] + sigma0 + words[index - 7] + sigma1
        ) >>> 0;
      }
      let [a, b, c, d, e, f, g, h] = hash;
      for (let index = 0; index < 64; index += 1) {
        const sum1 = rotate(e, 6) ^ rotate(e, 11) ^ rotate(e, 25);
        const choice = (e & f) ^ (~e & g);
        const temporary1 = (
          h + sum1 + choice + constants[index] + words[index]
        ) >>> 0;
        const sum0 = rotate(a, 2) ^ rotate(a, 13) ^ rotate(a, 22);
        const majority = (a & b) ^ (a & c) ^ (b & c);
        const temporary2 = (sum0 + majority) >>> 0;
        h = g; g = f; f = e; e = (d + temporary1) >>> 0;
        d = c; c = b; b = a; a = (temporary1 + temporary2) >>> 0;
      }
      [a, b, c, d, e, f, g, h].forEach((value, index) => {
        hash[index] = (hash[index] + value) >>> 0;
      });
    }
    return [...hash]
      .map((value) => value.toString(16).padStart(8, "0")).join("");
  }

  function payloadDigest(payload) {
    try {
      return "sha256:" + sha256(
        new TextEncoder().encode(integrityMaterial(payload))
      );
    } catch (_error) {
      return null;
    }
  }

  function historyElements(usage, identityPrefix, helpers) {
    const {
      element, formatDate, pluralizeWord, document: documentObject
    } = helpers;
    const allRecords = [...new Map([...usage.history, usage.current]
      .map((record) => ({
        ...record,
        timestamp: parseTimestamp(record.observed_at)
      }))
      .filter((record) => record.timestamp !== null)
      .sort((left, right) => left.timestamp - right.timestamp)
      .map((record) => [
        `${record.observed_at}|${record.reset_identity}|${record.used_percent}`,
        record
      ])).values()];
    const records = allRecords.slice(-48);
    const materialWindows = usage.reset_windows.filter(
      (window) => window.material === true
    );
    const heading = element("div", "usage-trend-heading");
    heading.append(
      element("strong", "", "Codex usage"),
      element(
        "span",
        "",
        `${records.length === allRecords.length
          ? pluralizeWord(records.length, "reading")
          : `${records.length} of ${allRecords.length} readings`} · ` +
          pluralizeWord(materialWindows.length, "material window")
      )
    );
    if (!records.length) {
      return [
        heading,
        element(
          "p",
          "empty-state compact-empty",
          "No typed usage history yet."
        )
      ];
    }
    const namespace = "http://www.w3.org/2000/svg";
    const svgNode = (name, attributes = {}, className = "") => {
      const node = documentObject.createElementNS(namespace, name);
      Object.entries(attributes).forEach(([key, value]) =>
        node.setAttribute(key, String(value)));
      if (className) node.setAttribute("class", className);
      return node;
    };
    const chart = svgNode("svg", {
      viewBox: "0 0 640 210",
      role: "img",
      tabindex: "0",
      "aria-labelledby":
        `${identityPrefix}-usage-title ${identityPrefix}-usage-description`
    }, "usage-trend-svg");
    const title = svgNode("title", { id: `${identityPrefix}-usage-title` });
    title.textContent = "Codex usage history";
    const plottedResetIdentities = new Set(
      records.map((record) => record.reset_identity)
    );
    const boundaries = [
      ...records.map((record) => ({
        identity: record.reset_identity,
        timestamp: record.resets_at * 1000
      })),
      ...materialWindows
        .filter((window) =>
          plottedResetIdentities.has(window.reset_identity))
        .map((window) => ({
          identity: window.reset_identity,
          timestamp: window.resets_at * 1000
        }))
    ].filter((boundary) => Number.isFinite(boundary.timestamp));
    const uniqueBoundaries = [...new Map(boundaries.map((boundary) => [
      `${boundary.identity}:${boundary.timestamp}`,
      boundary
    ])).values()];
    const description = svgNode(
      "desc",
      { id: `${identityPrefix}-usage-description` }
    );
    description.textContent =
      `${records.length} readings, ${formatDate(records[0].observed_at)}–` +
      `${formatDate(records.at(-1).observed_at)}; ` +
      `${uniqueBoundaries.length} typed reset ` +
      `${uniqueBoundaries.length === 1 ? "boundary" : "boundaries"}.`;
    chart.append(title, description);
    const left = 42;
    const top = 18;
    const width = 582;
    const height = 154;
    const firstTime = Math.min(
      records[0].timestamp,
      ...uniqueBoundaries.map((boundary) => boundary.timestamp)
    );
    const lastTime = Math.max(
      records.at(-1).timestamp,
      ...uniqueBoundaries.map((boundary) => boundary.timestamp)
    );
    const xForTime = (timestamp) => firstTime === lastTime
      ? left + width / 2
      : left + (timestamp - firstTime) / (lastTime - firstTime) * width;
    const yFor = (value) => top + height - value / 100 * height;
    [0, 25, 50, 75, 100].forEach((value) => {
      const y = yFor(value);
      chart.append(svgNode(
        "line",
        { x1: left, x2: left + width, y1: y, y2: y },
        "usage-trend-grid"
      ));
      const label = svgNode(
        "text",
        { x: left - 8, y: y + 4, "text-anchor": "end" },
        "usage-trend-axis-label"
      );
      label.textContent = String(value);
      chart.append(label);
    });
    uniqueBoundaries.forEach((boundary) => {
      const x = xForTime(boundary.timestamp);
      chart.append(svgNode(
        "line",
        { x1: x, x2: x, y1: top, y2: top + height },
        "usage-trend-reset"
      ));
      const label = svgNode(
        "text",
        { x: x + 5, y: top + 10 },
        "usage-trend-reset-label"
      );
      label.textContent = `Reset ${formatDate(boundary.timestamp)}`;
      chart.append(label);
    });
    chart.append(svgNode("path", {
      d: records.map((record, index) =>
        `${index ? "L" : "M"} ` +
        `${xForTime(record.timestamp).toFixed(1)} ` +
        `${yFor(record.used_percent).toFixed(1)}`).join(" ")
    }, "usage-trend-line"));
    records.forEach((record) => {
      const point = svgNode("circle", {
        cx: xForTime(record.timestamp),
        cy: yFor(record.used_percent),
        r: 4.5
      }, "usage-trend-point");
      const pointTitle = svgNode("title");
      pointTitle.textContent =
        `${formatDate(record.observed_at)}: ${record.used_percent}% used; ` +
        `${record.remaining_percent}% remaining`;
      point.append(pointTitle);
      chart.append(point);
    });
    [
      { record: records[0], anchor: "start" },
      { record: records.at(-1), anchor: "end" }
    ].forEach(({ record, anchor }) => {
      const label = svgNode("text", {
        x: xForTime(record.timestamp),
        y: 198,
        "text-anchor": anchor
      }, "usage-trend-axis-label");
      label.textContent = formatDate(record.observed_at);
      chart.append(label);
    });
    const accessibleHistory = element("ul", "visually-hidden");
    accessibleHistory.setAttribute(
      "aria-label",
      "Codex usage readings and reset boundaries"
    );
    records.forEach((record) => {
      accessibleHistory.append(element(
        "li",
        "",
        `${formatDate(record.observed_at)}: ${record.used_percent}% used ` +
        `and ${record.remaining_percent}% remaining; reset ` +
        `${formatDate(record.resets_at * 1000)}.`
      ));
    });
    uniqueBoundaries.forEach((boundary) => {
      accessibleHistory.append(element(
        "li",
        "",
        `Reset boundary ${boundary.identity}: ` +
        `${formatDate(boundary.timestamp)}.`
      ));
    });
    return [
      heading,
      chart,
      accessibleHistory,
      element(
        "p",
        "micro-note usage-trend-text-summary",
        `${records.length === allRecords.length
          ? records.length
          : `${records.length} of ${allRecords.length}`} readings plotted; ` +
        `latest ${usage.current.used_percent}% used, ` +
        `${usage.current.remaining_percent}% remaining; ` +
        `${uniqueBoundaries.length} exact reset ` +
        `${uniqueBoundaries.length === 1 ? "boundary" : "boundaries"}.`
      )
    ];
  }

  function renderCapacity(usage, helpers) {
    const {
      byId, element, formatOperationalDate, operationsLedgerRow,
      logHistoryHeading, unavailableMessage
    } = helpers;
    const host = byId("operations-capacity-summary");
    const historyHost = byId("operations-capacity-history");
    if (!host || !historyHost) return;
    if (!validProjection(usage) || usage.availability !== "current") {
      host.replaceChildren(element(
        "p",
        "empty-state compact-empty",
        unavailableMessage
      ));
      historyHost.replaceChildren();
      return;
    }
    const current = usage.current;
    const estimate = usage.estimates;
    const budgetAvailable = estimate.budget_available === true;
    const burnAvailable = estimate.burn_rate_available === true;
    const reasons = {
      projection_unavailable: "The bound usage projection is unavailable.",
      reset_boundary_elapsed: "The recorded reset boundary has elapsed.",
      budget_input_unavailable:
        "The producer did not supply sufficient budget inputs.",
      burn_rate_input_unavailable:
        "The producer did not supply sufficient burn-rate inputs.",
      insufficient_observation_coverage:
        "More observation coverage is required for a burn-rate estimate.",
      nonpositive_usage_change:
        "No positive usage change was observed during the covered interval."
    };
    const reason = (value) => reasons[value] || "Estimate unavailable.";
    host.replaceChildren(
      operationsLedgerRow(
        "Current readback",
        { tone: "success", label: `${current.remaining_percent}% remaining` },
        `${current.used_percent}% used · ${current.plan_type} · reset ` +
        `${formatOperationalDate(current.resets_at * 1000)} · ` +
        `${current.reset_identity} · trustworthy through ` +
        `${formatOperationalDate(usage.trustworthy_through)}`,
        current.observed_at
      ),
      operationsLedgerRow(
        "Even-spend budget",
        {
          tone: budgetAvailable ? "notice" : "unavailable",
          label: budgetAvailable
            ? `${estimate.remaining_percent_per_day_budget}% per day`
            : "Unavailable"
        },
        budgetAvailable
          ? "Estimated percent available per day through the reset; no absolute allowance is inferred."
          : reason(estimate.budget_reason_code),
        usage.current_through
      ),
      operationsLedgerRow(
        "Burn rate and projected exhaustion",
        {
          tone: burnAvailable ? "notice" : "unavailable",
          label: burnAvailable
            ? formatOperationalDate(estimate.projected_exhaustion_at)
            : "Unavailable"
        },
        burnAvailable
          ? `${estimate.average_percent_per_day}% per day · ` +
            `${estimate.confidence} confidence`
          : reason(estimate.burn_rate_reason_code),
        usage.current_through
      ),
      operationsLedgerRow(
        "Estimate coverage",
        {
          tone: estimate.available ? "notice" : "unavailable",
          label: `${estimate.sample_count} ` +
            `${estimate.sample_count === 1 ? "sample" : "samples"}`
        },
        `${estimate.coverage_hours} hours · ${estimate.confidence} ` +
        "confidence · producer-declared availability only",
        usage.current_through
      )
    );
    const windows = usage.reset_windows
      .filter((window) => window.material === true)
      .map((window) => operationsLedgerRow(
        window.reset_identity,
        {
          tone: "notice",
          label:
            `${window.min_used_percent}–${window.max_used_percent}% used`
        },
        `Reset ${formatOperationalDate(window.resets_at * 1000)} · ` +
        `${window.observation_count} observations`,
        window.last_observed
      ));
    const anomalies = usage.anomalies.map((event) => operationsLedgerRow(
      event.anomaly_id,
      { tone: "warning", label: "Reset identity changed" },
      `Observed ${event.observed_reset_identity}; current ` +
      `${event.current_reset_identity}. Extrapolation may be unreliable.`,
      event.observed_at
    ));
    historyHost.replaceChildren(
      ...historyElements(usage, "operations", helpers),
      logHistoryHeading("Material reset windows", windows.length, "window"),
      ...windows,
      ...anomalies
    );
  }

  global.ARRP_CODEX_CAPACITY = Object.freeze({
    schemaVersion: 1,
    validProjection,
    payloadDigest,
    historyElements,
    renderCapacity
  });
})(window);
