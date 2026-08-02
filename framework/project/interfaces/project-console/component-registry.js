/* Registry v4 exact projection */
(function (global) {
  "use strict";

  const MODES = Object.freeze([
    "components", "classes", "types", "lifecycles", "authority",
    "relationships", "directories", "exemptions", "unresolved",
    "routing", "terminology", "codeowners"
  ]);
  const FORBIDDEN_KEYS = new Set([
    "private_payload", "contract_payload", "attachment_path", "credential",
    "secret", "source_binding", "record_refs", "source_kind",
    "authority_digest_model", "repository_coverage", "component_authorities",
    "component_lifecycles", "migrations_and_aliases", "provenance_events"
  ]);
  const COLLECTIONS = Object.freeze({
    components: ["component-registry-component-list", "component-registry-component-detail"],
    classes: ["component-registry-classes-list", "component-registry-classes-detail"],
    types: ["component-registry-types-list", "component-registry-types-detail"],
    lifecycles: ["component-registry-lifecycle-list", "component-registry-lifecycle-detail"],
    authority: ["component-registry-authority-list", "component-registry-authority-detail"],
    relationships: ["component-registry-relationship-list", "component-registry-relationship-detail"],
    directories: ["component-registry-directories-list", "component-registry-directories-detail"],
    exemptions: ["component-registry-exemptions-list", "component-registry-exemptions-detail"],
    routing: ["component-registry-routing-list", "component-registry-routing-detail"],
    terminology: ["component-registry-terminology-list", "component-registry-terminology-detail"],
    codeowners: ["component-registry-codeowners-list", "component-registry-codeowners-detail"]
  });

  function object(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function text(value) {
    return typeof value === "string" && value.length > 0;
  }

  function digest(value) {
    return typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
  }

  function unique(records, key) {
    return Array.isArray(records)
      && records.every((record) => object(record) && text(record[key]))
      && new Set(records.map((record) => record[key])).size === records.length;
  }

  function hasForbiddenPayload(value) {
    if (Array.isArray(value)) return value.some(hasForbiddenPayload);
    if (!object(value)) return false;
    return Object.entries(value).some(([key, nested]) =>
      FORBIDDEN_KEYS.has(key) || hasForbiddenPayload(nested));
  }

  function validSnapshot(snapshot) {
    if (!object(snapshot)
      || snapshot.schema_version !== 4
      || snapshot.projection_id !== "component-registry-console"
      || snapshot.producer_id !== "project-console-builder"
      || Number.isNaN(Date.parse(snapshot.generated_at))
      || snapshot.availability !== "current"
      || snapshot.complete !== true
      || snapshot.reason_code !== null
      || !object(snapshot.routes)
      || Object.keys(snapshot.routes).length !== MODES.length
      || !MODES.every((mode) =>
        snapshot.routes[mode] === `automation:component-registry:${mode}`)
      || !object(snapshot.defaults)
      || snapshot.defaults.mode !== "components"
      || !object(snapshot.registry)
      || snapshot.registry.registry_id !== "COMPONENT-REGISTRY"
      || snapshot.registry.registry_revision !== 4
      || snapshot.registry.registry_status !== "adopted"
      || snapshot.registry.validation_mode !== "adopted_configuration_validation"
      || snapshot.registry.authoritative !== false
      || snapshot.registry.executable !== false
      || snapshot.registry.source_bytes_current !== true
      || snapshot.registry.predecessor_route_consulted !== false
      || !digest(snapshot.registry.registry_sha256)
      || !text(snapshot.registry.source_url)
      || !text(snapshot.registry.tracked_live_notice)
      || !object(snapshot.records)
      || !object(snapshot.linked)
      || !object(snapshot.derived)
      || !unique(snapshot.records.components, "stable_id")
      || snapshot.records.components.length !== 105
      || !unique(snapshot.records.relationships, "relationship_id")
      || snapshot.records.relationships.length !== 16
      || !unique(snapshot.records.directory_scopes, "scope_id")
      || snapshot.records.directory_scopes.length !== 59
      || !unique(snapshot.records.registration_exemptions, "exemption_id")
      || snapshot.records.registration_exemptions.length !== 3
      || !unique(snapshot.records.routing_rules, "rule_id")
      || snapshot.records.routing_rules.length !== 64
      || !unique(snapshot.records.terminology, "term_id")
      || snapshot.records.terminology.length !== 87
      || !object(snapshot.derived.classifications)
      || !object(snapshot.derived.lifecycles)
      || !object(snapshot.derived.authorities)
      || !object(snapshot.derived.coverage)
      || !object(snapshot.derived.routing)
      || !object(snapshot.derived.codeowners)
      || snapshot.derived.coverage.uncovered_count !== 0
      || snapshot.derived.coverage.multiply_treated_count !== 0
      || snapshot.derived.codeowners.available !== true
      || snapshot.derived.codeowners.complete !== true
      || snapshot.derived.codeowners.problems.length !== 0
      || snapshot.derived.codeowners.current_sha256
        !== snapshot.derived.codeowners.generated_sha256
      || hasForbiddenPayload(snapshot)) return false;
    return snapshot.records.components.every((record) =>
      text(record.display_name)
      && object(record.classification)
      && object(record.canonical_source)
      && text(record.canonical_source.kind)
      && text(record.canonical_source.value)
      && (record.canonical_source.url === null || text(record.canonical_source.url)))
      && snapshot.records.terminology.every((record) =>
        text(record.label) && text(record.definition));
  }

  function routeState(target, snapshot) {
    const [route, query = ""] = String(target || "").replace(/^#/, "").split("?", 2);
    const parts = route.split(":");
    const requested = parts[0] === "automation" && parts[1] === "component-registry"
      ? parts[2] : "";
    const mode = MODES.includes(requested) ? requested : "components";
    if (!validSnapshot(snapshot)) return { mode, selected: null };
    const key = {
      components: "component", classes: "class", types: "type",
      lifecycles: "assignment", authority: "assignment",
      relationships: "relationship", directories: "directory",
      exemptions: "exemption", unresolved: "coverage",
      routing: "selection", terminology: "term", codeowners: "assignment"
    }[mode];
    const params = new URLSearchParams(query);
    const selected = mode === "routing"
      ? params.get("selection") || params.get("rule")
      : params.get(key);
    return { mode, selected };
  }

  function safeSearchRecord(mode, record) {
    const fields = {
      components: ["stable_id", "display_name", "owner", "lifecycle", "revision_mode"],
      classes: ["class_id", "label"], types: ["classification_id", "class_id", "type_id", "label"],
      lifecycles: ["assignment_id", "component_id", "state", "revision_mode"],
      authority: ["assignment_id", "component_id", "source"],
      relationships: ["relationship_id", "relationship_type", "from", "to"],
      directories: ["scope_id", "display_name", "path_pattern", "purpose", "owner"],
      exemptions: ["exemption_id", "artifact_class", "post_run_disposition"],
      routing: ["routing_id", "routing_kind", "label", "rule_id", "namespace", "failure_code"],
      terminology: ["term_id", "label", "definition"],
      codeowners: ["assignment_id", "record_kind", "stable_id", "display_name", "path_pattern", "declared_mode", "effective_mode"]
    }[mode] || [];
    const values = fields.map((field) => record[field]);
    if (mode === "components") {
      values.push(record.classification.component_class);
      values.push(record.classification.component_type);
      values.push(record.canonical_source.value);
    }
    if (mode === "codeowners") values.push(...record.owners);
    return values.flat().filter((value) => typeof value === "string")
      .join(" ").toLocaleLowerCase();
  }

  function filterTerminologyEntries(entries, query) {
    const tokens = String(query || "").trim().toLocaleLowerCase()
      .split(/\s+/).filter(Boolean);
    if (!tokens.length) return [...entries];
    return entries.filter((entry) => tokens.every((token) =>
      safeSearchRecord("terminology", entry).includes(token)));
  }

  function node(tag, className = "", value = "") {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (value !== "") element.textContent = String(value);
    return element;
  }

  function label(value) {
    return String(value || "").replaceAll("_", " ").replaceAll(":", " · ");
  }

  function displayValue(value) {
    if (value === null || value === undefined || value === "") return "Not applicable";
    if (Array.isArray(value)) return value.length ? value.join(", ") : "None";
    if (object(value)) return Object.entries(value)
      .map(([key, nested]) => `${label(key)}: ${displayValue(nested)}`).join(" · ");
    if (typeof value === "boolean") return value ? "Yes" : "No";
    return label(value);
  }

  function renderDetail(target, record, title) {
    target.replaceChildren();
    target.append(node("h3", "", title));
    const source = record.canonical_source;
    if (object(source) && text(source.url)) {
      const link = node("a", "record-link secondary", "Open canonical source ↗");
      link.href = source.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      target.append(link);
    }
    const list = node("dl", "record-details component-registry-record-details");
    Object.entries(record).forEach(([key, value]) => {
      if (["console_route", "canonical_source"].includes(key)) return;
      list.append(node("dt", "", label(key)), node("dd", "", displayValue(value)));
    });
    if (object(source)) {
      list.append(node("dt", "", "Canonical source"),
        node("dd", "", `${label(source.kind)} · ${source.value}`));
    }
    target.append(list);
  }

  function optionValues(select, values, initial) {
    if (!select) return;
    select.replaceChildren();
    const blank = node("option", "", initial);
    blank.value = "";
    select.append(blank);
    [...new Set(values.filter(text))].sort().forEach((value) => {
      const option = node("option", "", label(value));
      option.value = value;
      select.append(option);
    });
  }

  function recordsFor(snapshot, mode) {
    const records = snapshot.records;
    const derived = snapshot.derived;
    return {
      components: records.components,
      classes: derived.classifications.classes,
      types: derived.classifications.types,
      lifecycles: derived.lifecycles.assignments,
      authority: derived.authorities.assignments,
      relationships: records.relationships,
      directories: records.directory_scopes,
      exemptions: records.registration_exemptions,
      routing: [...derived.routing.selections, ...records.routing_rules],
      terminology: records.terminology,
      codeowners: derived.codeowners.records
    }[mode] || [];
  }

  function identityFor(mode, record) {
    return record[{
      components: "stable_id", classes: "class_id", types: "classification_id",
      lifecycles: "assignment_id", authority: "assignment_id",
      relationships: "relationship_id", directories: "scope_id",
      exemptions: "exemption_id", routing: record.rule_id ? "rule_id" : "routing_id",
      terminology: "term_id", codeowners: "assignment_id"
    }[mode]];
  }

  function titleFor(mode, record) {
    return record.display_name || record.label || record.stable_id
      || record.component_id || record.relationship_id || record.scope_id
      || record.exemption_id || record.routing_id || record.rule_id
      || record.term_id || record.assignment_id || mode;
  }

  function applyFilters(mode, records) {
    const search = document.getElementById(`component-registry-${mode}-search`)
      || (mode === "components" ? document.getElementById("component-registry-components-search") : null);
    const query = String(search?.value || "").trim().toLocaleLowerCase();
    return records.filter((record) => {
      if (query && !safeSearchRecord(mode, record).includes(query)) return false;
      if (mode === "components") {
        const classValue = document.getElementById("component-registry-components-class")?.value;
        const lifecycle = document.getElementById("component-registry-components-lifecycle")?.value;
        if (classValue && record.classification.component_class !== classValue) return false;
        if (lifecycle && record.lifecycle !== lifecycle) return false;
      }
      if (mode === "types") {
        const classValue = document.getElementById("component-registry-types-class")?.value;
        if (classValue && record.class_id !== classValue) return false;
      }
      if (mode === "lifecycles") {
        const state = document.getElementById("component-registry-lifecycles-state")?.value;
        if (state && record.state !== state) return false;
      }
      if (mode === "authority") {
        const state = document.getElementById("component-registry-authority-status")?.value;
        if (state && (record.authoritative ? "authoritative" : "nonauthoritative") !== state) return false;
      }
      if (mode === "relationships") {
        const type = document.getElementById("component-registry-relationships-type")?.value;
        if (type && record.relationship_type !== type) return false;
      }
      if (mode === "codeowners") {
        const resolution = document.getElementById("component-registry-codeowners-mode")?.value;
        const kind = document.getElementById("component-registry-codeowners-kind")?.value;
        const owner = document.getElementById("component-registry-codeowners-owner")?.value;
        const effective = record.declared_mode === "inherit" ? "inherited" : record.effective_mode;
        if (resolution && effective !== resolution) return false;
        if (kind && record.record_kind !== kind) return false;
        if (owner && !record.owners.includes(owner)) return false;
      }
      return true;
    });
  }

  function renderCollection(snapshot, mode, selectedId = null) {
    const ids = COLLECTIONS[mode];
    if (!ids) return;
    const list = document.getElementById(ids[0]);
    const detail = document.getElementById(ids[1]);
    if (!list || !detail) return;
    const all = recordsFor(snapshot, mode);
    const records = applyFilters(mode, all);
    const result = document.getElementById(`component-registry-${mode}-results`);
    if (result) result.textContent = `${records.length} of ${all.length} records`;
    list.replaceChildren();
    let selected = records.find((record) => identityFor(mode, record) === selectedId)
      || records[0];
    records.forEach((record) => {
      const id = identityFor(mode, record);
      const button = node("button", "email-row component-registry-row");
      button.type = "button";
      button.dataset.recordId = id;
      button.setAttribute("aria-selected", String(record === selected));
      button.append(node("strong", "", titleFor(mode, record)),
        node("span", "", label(id)));
      button.addEventListener("click", () => {
        selected = record;
        renderDetail(detail, record, titleFor(mode, record));
        const route = record.console_route || snapshot.routes[mode];
        if (global.history?.replaceState) global.history.replaceState(null, "", `#${route}`);
        [...list.children].forEach((child) => child.setAttribute(
          "aria-selected", String(child === button)));
      });
      list.append(button);
    });
    if (selected) renderDetail(detail, selected, titleFor(mode, selected));
    else detail.replaceChildren(node("p", "empty-state compact-empty", "No records match these filters."));
  }

  function setCount(mode, count) {
    const button = document.getElementById(`component-registry-mode-${mode}`);
    if (!button) return;
    let badge = button.querySelector(".tab-count");
    if (!badge) {
      badge = node("span", "tab-count");
      button.append(" ", badge);
    }
    badge.textContent = String(count);
  }

  function render(snapshot, target = "") {
    if (!validSnapshot(snapshot)) return false;
    const state = routeState(target || global.location?.hash || "", snapshot);
    const status = document.getElementById("component-registry-status");
    if (status) {
      status.textContent = "Tracked Registry v4";
      status.className = "status-badge proposed";
    }
    const notice = document.getElementById("component-registry-summary");
    if (notice) notice.textContent = snapshot.registry.tracked_live_notice;

    optionValues(document.getElementById("component-registry-components-class"),
      snapshot.derived.classifications.classes.map((record) => record.class_id), "All classes");
    optionValues(document.getElementById("component-registry-components-lifecycle"),
      snapshot.records.components.map((record) => record.lifecycle), "All states");
    optionValues(document.getElementById("component-registry-types-class"),
      snapshot.derived.classifications.classes.map((record) => record.class_id), "All parent classes");
    optionValues(document.getElementById("component-registry-lifecycles-state"),
      snapshot.derived.lifecycles.assignments.map((record) => record.state), "All states");
    optionValues(document.getElementById("component-registry-relationships-type"),
      snapshot.records.relationships.map((record) => record.relationship_type), "All types");
    optionValues(document.getElementById("component-registry-codeowners-owner"),
      snapshot.derived.codeowners.records.flatMap((record) => record.owners), "All owners");

    const applyMode = (mode) => {
      MODES.forEach((candidate) => {
        const button = document.getElementById(`component-registry-mode-${candidate}`);
        const panel = document.getElementById(`component-registry-panel-${candidate}`);
        if (button) {
          button.setAttribute("aria-selected", String(candidate === mode));
          button.tabIndex = candidate === mode ? 0 : -1;
        }
        if (panel) panel.hidden = candidate !== mode;
      });
      if (mode === "unresolved") {
        const results = document.getElementById("component-registry-unresolved-results");
        const detail = document.getElementById("component-registry-unresolved-detail");
        if (results) results.textContent = "0 uncovered · 0 multiply treated";
        if (detail) detail.textContent = "No unresolved coverage. Every governed path treatment is derived from the Registry model.";
      } else renderCollection(snapshot, mode, state.selected);
    };

    MODES.forEach((mode) => {
      document.getElementById(`component-registry-mode-${mode}`)
        ?.addEventListener("click", () => {
          applyMode(mode);
          if (global.history?.replaceState) global.history.replaceState(null, "", `#${snapshot.routes[mode]}`);
        });
      const search = document.getElementById(`component-registry-${mode}-search`)
        || (mode === "components" ? document.getElementById("component-registry-components-search") : null);
      search?.addEventListener("input", () => renderCollection(snapshot, mode));
    });
    [
      "component-registry-components-class", "component-registry-components-lifecycle",
      "component-registry-types-class", "component-registry-lifecycles-state",
      "component-registry-authority-status", "component-registry-relationships-type",
      "component-registry-codeowners-mode", "component-registry-codeowners-kind",
      "component-registry-codeowners-owner"
    ].forEach((id) => document.getElementById(id)?.addEventListener("change", () => {
      const mode = id.split("-")[2] === "components" ? "components"
        : id.split("-")[2];
      renderCollection(snapshot, mode);
    }));

    MODES.forEach((mode) => setCount(mode,
      mode === "unresolved" ? 0 : recordsFor(snapshot, mode).length));
    applyMode(state.mode);
    return true;
  }

  global.ARRP_COMPONENT_REGISTRY = Object.freeze({
    schemaVersion: 4,
    validSnapshot,
    routeState,
    filterTerminologyEntries,
    render
  });
})(window);
