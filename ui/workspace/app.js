(() => {
  "use strict";

  const ROUTES = {
    overview: { label: "Overview", document: "Audit overview" },
    visual: { label: "Visual audit", document: "Visual audit" },
    components: { label: "Component matrix", document: "Component matrix" },
    design: { label: "Design system", document: "Design system" },
    repairs: { label: "Repair queue", document: "Repair queue" },
    verification: { label: "Verification", document: "Verification" },
  };
  const SEVERITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };
  const SEVERITY_LABEL = {
    critical: "Critical",
    high: "High",
    medium: "Medium",
    low: "Low",
  };
  const READINESS_LABEL = {
    ready: "Ready",
    "needs-polish": "Needs polish",
    "at-risk": "At risk",
    blocked: "Blocked",
    "insufficient-evidence": "Insufficient evidence",
  };
  const STATUS_LABEL = {
    complete: "Complete",
    partial: "Partial",
    missing: "Missing",
    "n/a": "Not applicable",
    open: "Open",
    fixed: "Fixed",
    ignored: "Ignored",
  };
  const STATE_ORDER = [
    "default",
    "hover",
    "active",
    "focus",
    "disabled",
    "loading",
    "pending",
    "validation",
    "invalid",
    "success",
    "failure",
    "error",
    "on",
    "off",
    "open",
    "closed",
    "selected",
    "empty/no results",
    "filled",
    "readonly",
    "transition",
    "polite announcement",
  ];
  const MATRIX_COLUMNS = [
    { label: "Default", names: ["default"] },
    { label: "Hover", names: ["hover"] },
    { label: "Active", names: ["active"] },
    { label: "Focus", names: ["focus"] },
    { label: "Disabled", names: ["disabled"] },
    { label: "Loading", names: ["loading", "pending"] },
    { label: "Validate", names: ["validation", "invalid"] },
    { label: "Success", names: ["success"] },
    { label: "Failure", names: ["failure", "error"] },
    { label: "Off", names: ["off", "closed"] },
    { label: "On", names: ["on"] },
    { label: "Open", names: ["open"] },
    { label: "Selected", names: ["selected"] },
    { label: "Empty", names: ["empty/no results"] },
  ];
  const TRIAGE_KEY = "finishline.triage.v1";
  const TRIAGE_VALUES = new Set(["open", "fixed", "ignored"]);
  const INFO_ICON =
    '<svg width="15" height="15" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M12 10.5v6M12 7.5v.1" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
  const COMMANDS = [
    "python3 scripts/audit.py <project> --out audit.json",
    "python3 scripts/capture.py <project> --out screenshots",
    "python3 scripts/workspace_data.py --audit audit.json --screenshots screenshots/screenshots.json",
    "python3 -m http.server 4173 --directory ui/workspace",
  ];
  const DATE_FORMAT = new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  });
  const DAY_FORMAT = new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });

  const state = {
    audit: null,
    meta: {},
    capture: { captured: false, count: 0, shots: [], limitations: [] },
    shots: [],
    allStates: [],
    route: "overview",
    triage: loadTriage(),
    lastDialogTrigger: null,
    filters: {
      visual: "all",
      componentQuery: "",
      componentStatus: "all",
      componentKind: "all",
      repairQuery: "",
      repairSeverity: "all",
      repairTriage: "all",
    },
  };

  const app = document.getElementById("app");
  const main = document.getElementById("main");
  const rail = document.getElementById("rail");
  const railToggle = document.getElementById("rail-toggle");
  const toastNode = document.getElementById("toast");
  const announcer = document.getElementById("announcer");
  const componentDialog = document.getElementById("component-dialog");
  const shotDialog = document.getElementById("shot-dialog");
  const commandDialog = document.getElementById("command-dialog");
  const repairDialog = document.getElementById("repair-dialog");
  let toastTimer = null;

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => {
      const replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      };
      return replacements[character];
    });
  }

  function selected(value, current) {
    return value === current ? " selected" : "";
  }

  function formatDate(value, fallback = "Not recorded") {
    if (!value) return fallback;
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? fallback : DATE_FORMAT.format(date);
  }

  function formatDay(value, fallback = "Date not recorded") {
    if (!value) return fallback;
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? fallback : DAY_FORMAT.format(date);
  }

  function humanize(value) {
    const text = String(value ?? "").replace(/[-_/]+/g, " ").trim();
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : "Unknown";
  }

  function severityRank(value) {
    return Object.prototype.hasOwnProperty.call(SEVERITY_ORDER, value)
      ? SEVERITY_ORDER[value]
      : 4;
  }

  function findingsByPriority(findings) {
    return [...findings].sort((a, b) => {
      const rank = severityRank(a.severity) - severityRank(b.severity);
      return rank !== 0 ? rank : String(a.id).localeCompare(String(b.id));
    });
  }

  function loadTriage() {
    try {
      const raw = localStorage.getItem(TRIAGE_KEY);
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
      const safe = {};
      for (const [id, status] of Object.entries(parsed)) {
        if (/^FL-\d{4}$/.test(id) && TRIAGE_VALUES.has(status)) safe[id] = status;
      }
      return safe;
    } catch {
      return {};
    }
  }

  function saveTriage(id, status) {
    if (!TRIAGE_VALUES.has(status)) return false;
    state.triage[id] = status;
    try {
      localStorage.setItem(TRIAGE_KEY, JSON.stringify(state.triage));
      return true;
    } catch {
      toast("Triage updated for this session only");
      return false;
    }
  }

  function effectiveStatus(finding) {
    return state.triage[finding.id] || finding.status || "open";
  }

  function toast(message) {
    toastNode.textContent = message;
    toastNode.classList.add("is-visible");
    clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => {
      toastNode.classList.remove("is-visible");
    }, 2600);
  }

  function announce(message) {
    announcer.textContent = "";
    window.setTimeout(() => {
      announcer.textContent = message;
    }, 30);
  }

  async function fetchJson(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) throw new Error(`${path} returned HTTP ${response.status}`);
    return response.json();
  }

  function isAuditShape(audit) {
    return Boolean(
      audit &&
        typeof audit === "object" &&
        audit.summary &&
        audit.project &&
        Array.isArray(audit.findings) &&
        Array.isArray(audit.components) &&
        audit.design_system,
    );
  }

  function normalizeCapture(capture) {
    if (!capture || typeof capture !== "object") {
      return {
        captured: false,
        count: 0,
        shots: [],
        skipped: [],
        limitations: [
          "No screenshot manifest was supplied. Visual claims are unsupported.",
        ],
      };
    }
    return {
      ...capture,
      shots: Array.isArray(capture.shots)
        ? capture.shots.filter((shot) => shot && typeof shot.path === "string")
        : [],
      skipped: Array.isArray(capture.skipped) ? capture.skipped : [],
      limitations: Array.isArray(capture.limitations) ? capture.limitations : [],
      count: Number.isInteger(capture.count) ? capture.count : 0,
    };
  }

  async function loadData() {
    try {
      const audit = await fetchJson("data/audit.json");
      if (!isAuditShape(audit)) {
        throw new Error("data/audit.json does not contain a FINISHLINE audit");
      }
      const [meta, capture] = await Promise.all([
        fetchJson("data/meta.json").catch(() => null),
        fetchJson("data/screenshots.json").catch(() => null),
      ]);
      state.audit = audit;
      state.meta = meta && typeof meta === "object" ? meta : {};
      state.capture = normalizeCapture(capture);
      state.shots = state.capture.shots.filter((shot) => shot.captured !== false);
      state.allStates = collectStateNames(audit.components);
      fillChrome();
      handleRoute(true);
    } catch (error) {
      renderFatal(error);
    }
  }

  function collectStateNames(components) {
    const names = new Set();
    for (const component of components) {
      for (const item of component.states || []) {
        if (item && item.name) names.add(item.name);
      }
    }
    return [...names].sort((a, b) => {
      const ai = STATE_ORDER.indexOf(a);
      const bi = STATE_ORDER.indexOf(b);
      if (ai === -1 && bi === -1) return a.localeCompare(b);
      if (ai === -1) return 1;
      if (bi === -1) return -1;
      return ai - bi;
    });
  }

  function fillChrome() {
    const audit = state.audit;
    const summary = audit.summary;
    const readiness = summary.readiness || "insufficient-evidence";
    const projectLabel =
      state.meta.project_label || audit.project.name || "Untitled project";
    const railReadiness = document.getElementById("rail-readiness");
    const badge = document.getElementById("data-badge");

    document.getElementById("rail-project").textContent = projectLabel;
    document.getElementById("rail-project-meta").textContent =
      `${summary.findings.total} findings · ${formatDay(audit.generated_at)}`;
    railReadiness.innerHTML = `<span class="status-square is-${escapeHtml(readiness)}" aria-hidden="true"></span><span>${escapeHtml(READINESS_LABEL[readiness] || humanize(readiness))}</span>`;
    badge.textContent = state.meta.sample ? "Sample audit" : "Local evidence";
    badge.classList.toggle("is-sample", Boolean(state.meta.sample));
    badge.title = state.meta.sample
      ? "This workspace is populated with a sample audit dataset."
      : "Every number is read from the local audit files.";
  }

  function currentRoute() {
    const raw = window.location.hash.replace(/^#\/?/, "").split("?")[0];
    return Object.prototype.hasOwnProperty.call(ROUTES, raw) ? raw : "overview";
  }

  function handleRoute(initial) {
    if (!state.audit) return;
    const raw = window.location.hash.replace(/^#\/?/, "").split("?")[0];
    const route = currentRoute();
    if (!raw || !Object.prototype.hasOwnProperty.call(ROUTES, raw)) {
      history.replaceState(null, "", "#/overview");
    }
    state.route = route;
    closeOpenDialogs();
    try {
      app.innerHTML = renderRoute(route);
    } catch (error) {
      renderFatal(error);
      return;
    }
    for (const link of document.querySelectorAll(".nav-link")) {
      if (link.dataset.route === route) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    }
    document.getElementById("crumb").textContent = ROUTES[route].label;
    document.title = `${ROUTES[route].document} — FINISHLINE`;
    if (window.innerWidth <= 860) setRail(false);
    if (!initial) {
      window.scrollTo(0, 0);
      main.focus({ preventScroll: true });
    }
  }

  function renderRoute(route) {
    switch (route) {
      case "visual":
        return viewVisual();
      case "components":
        return viewComponents();
      case "design":
        return viewDesign();
      case "repairs":
        return viewRepairs();
      case "verification":
        return viewVerification();
      case "overview":
      default:
        return viewOverview();
    }
  }

  function pageHeader({ eyebrow, title, lede, aside = "" }) {
    return `
      <header class="page-header">
        <div>
          <p class="eyebrow">${eyebrow}</p>
          <h1 class="page-title">${title}</h1>
          <p class="page-lede">${lede}</p>
        </div>
        ${aside ? `<div class="page-header-aside">${aside}</div>` : ""}
      </header>`;
  }

  function stat(value, label, note = "") {
    return `
      <div class="stat">
        <div class="stat-value">${value}${note ? `<small>${note}</small>` : ""}</div>
        <p class="stat-label">${label}</p>
      </div>`;
  }

  function inlineEmpty(message) {
    return `<p class="inline-empty">${escapeHtml(message)}</p>`;
  }

  function sectionHead(title, meta, id = "") {
    return `
      <div class="section-head">
        <h2 class="section-title"${id ? ` id="${id}"` : ""}>${title}</h2>
        <span class="section-meta">${meta}</span>
      </div>`;
  }

  function findingRow(finding) {
    return `
      <a class="finding-row" href="#/repairs" data-brief="${escapeHtml(finding.id)}" aria-label="Open repair brief for ${escapeHtml(finding.id)}: ${escapeHtml(finding.title)}">
        <span class="finding-id">${escapeHtml(finding.id)}</span>
        <span class="severity is-${escapeHtml(finding.severity)}">${escapeHtml(SEVERITY_LABEL[finding.severity] || finding.severity)}</span>
        <span>
          <span class="finding-title">${escapeHtml(finding.title)}</span>
          <span class="finding-location">${escapeHtml(finding.file)}:${escapeHtml(finding.line)} · ${escapeHtml(finding.category)}</span>
        </span>
        <span class="finding-meta">
          <span class="confidence">${escapeHtml(finding.confidence)}</span>
          <span class="finding-arrow" aria-hidden="true">›</span>
        </span>
      </a>`;
  }

  function coverageBar(components) {
    const total =
      (components.complete || 0) +
      (components.partial || 0) +
      (components.missing || 0);
    if (total === 0) return "";
    const width = (value) => `${Math.round((value / total) * 100)}%`;
    return `
      <div class="coverage-bar" aria-hidden="true">
        <span class="is-complete" style="width:${width(components.complete)}"></span>
        <span class="is-partial" style="width:${width(components.partial)}"></span>
        <span class="is-missing" style="width:${width(components.missing)}"></span>
      </div>`;
  }

  function categoryRows(findings) {
    const counts = new Map();
    for (const finding of findings) {
      counts.set(finding.category, (counts.get(finding.category) || 0) + 1);
    }
    const rows = [...counts.entries()].sort((a, b) => b[1] - a[1]);
    if (rows.length === 0) return inlineEmpty("No category evidence.");
    const maximum = rows[0][1] || 1;
    return rows
      .slice(0, 6)
      .map(
        ([category, count]) => `
        <div class="category-bar">
          <span class="category-bar-label">${escapeHtml(category)}</span>
          <span class="category-bar-track"><span style="width:${Math.round((count / maximum) * 100)}%"></span></span>
          <span class="category-bar-count">${count}</span>
        </div>`,
      )
      .join("");
  }
  function viewOverview() {
    const audit = state.audit;
    const summary = audit.summary;
    const project = audit.project;
    const verification = audit.verification;
    const components = summary.components;
    const readiness = summary.readiness || "insufficient-evidence";
    const openFindings = findingsByPriority(
      audit.findings.filter((finding) => effectiveStatus(finding) === "open"),
    );
    const priorities = openFindings.slice(0, 6);
    const checkedCount =
      verification.check_count || (verification.checks_run || []).length || 0;
    const sampleNotice = state.meta.sample
      ? `<div class="limit-note">${INFO_ICON}<span><strong>Sample dataset.</strong> This workspace is populated with the shipped <code>defective-ui</code> fixture audit. It demonstrates the evidence workflow; it is not a claim about another product.</span></div>`
      : "";
    const priorityMarkup = priorities.length
      ? priorities.map(findingRow).join("")
      : inlineEmpty("No open findings remain in the local triage view.");

    return `
      ${pageHeader({
        eyebrow: `Static audit · ${escapeHtml(formatDay(audit.generated_at))}`,
        title: "Is this interface finished?",
        lede: `${escapeHtml(project.name)} was scanned across ${project.files_scanned} files. Readiness is a source-evidence signal, not a certification of usability.`,
        aside: `
          <a class="button is-quiet" href="#/repairs">Repair queue</a>
          <button class="button" type="button" data-action="open-commands">Reproduce audit</button>`,
      })}
      ${sampleNotice}
      <section class="verdict" aria-labelledby="verdict-label">
        <div>
          <p class="verdict-label" id="verdict-label">Readiness signal</p>
          <p class="verdict-value is-${escapeHtml(readiness)}">${escapeHtml(READINESS_LABEL[readiness] || humanize(readiness))}</p>
          <p class="verdict-reason">${escapeHtml(summary.readiness_reason)}</p>
        </div>
        <div class="verdict-score" aria-label="State coverage ${components.state_coverage} percent">
          <span class="verdict-score-value">${components.state_coverage}%</span>
          <span class="verdict-score-label">State coverage</span>
        </div>
      </section>
      <div class="stat-strip">
        ${stat(
          summary.findings.total,
          "Findings",
          `${summary.findings.critical} critical · ${summary.findings.high} high`,
        )}
        ${stat(
          openFindings.length,
          "Open priorities",
          `${summary.confidence.verified} verified`,
        )}
        ${stat(
          `${components.state_coverage}%`,
          "Component coverage",
          `${components.partial} partial`,
        )}
        ${stat(components.total, "Components", `${components.missing} missing states`)}
      </div>
      <div class="split" style="margin-top:42px">
        <section aria-labelledby="priority-title">
          ${sectionHead("Priority findings", `${openFindings.length} open · highest severity first`, "priority-title")}
          <div class="finding-list">${priorityMarkup}</div>
          <p class="fine-print">A source finding is a prompt for verification, not proof of a user-facing defect. Open a brief to inspect evidence, confidence, and the repair direction.</p>
        </section>
        <aside class="stack" aria-label="Audit evidence summary">
          <div class="panel">
            <p class="panel-title">Evidence envelope</p>
            <dl class="kv">
              <div><dt>Generated</dt><dd>${escapeHtml(formatDate(audit.generated_at))}</dd></div>
              <div><dt>Mode</dt><dd>${escapeHtml(verification.mode)}</dd></div>
              <div><dt>Scope</dt><dd>${project.files_scanned} files · ${project.lines_scanned} lines</dd></div>
              <div><dt>Checks</dt><dd>${checkedCount}</dd></div>
              <div><dt>Confidence</dt><dd>${summary.confidence.verified} verified · ${summary.confidence.inferred} inferred</dd></div>
              <div><dt>Captures</dt><dd>${state.capture.count || verification.screenshots || 0}</dd></div>
            </dl>
          </div>
          <div class="panel">
            <p class="panel-title">Component coverage</p>
            ${coverageBar(components)}
            <div class="coverage-legend" aria-hidden="true">
              <span class="is-complete">${components.complete} complete</span>
              <span class="is-partial">${components.partial} partial</span>
              <span class="is-missing">${components.missing} missing</span>
            </div>
            <p class="fine-print">Coverage weighs default, interaction, validation, and feedback states found in source.</p>
          </div>
          <div class="panel">
            <p class="panel-title">Findings by category</p>
            <div class="category-bars">${categoryRows(audit.findings)}</div>
          </div>
        </aside>
      </div>
      <section class="section" aria-labelledby="runlog-title">
        ${sectionHead("Audit provenance", "What ran, on what scope", "runlog-title")}
        <div class="runlog">
          <div class="runlog-item">
            <span class="runlog-time">${escapeHtml(formatDay(audit.generated_at))}</span>
            <div><p class="runlog-text">Static audit generated by ${escapeHtml(audit.generator.name)} ${escapeHtml(audit.generator.version)}</p><p class="runlog-detail">${escapeHtml(audit.generator.mode)} mode · ${checkedCount} checks registered</p></div>
          </div>
          <div class="runlog-item">
            <span class="runlog-time">Scope</span>
            <div><p class="runlog-text">${project.files_scanned} files · ${project.lines_scanned} lines · ${Math.round(project.bytes_scanned / 1024)} KiB inspected</p><p class="runlog-detail">${(project.stack || []).map(escapeHtml).join(" · ")}</p></div>
          </div>
          <div class="runlog-item">
            <span class="runlog-time">Capture</span>
            <div><p class="runlog-text">${state.capture.count || 0} viewport screenshot${state.capture.count === 1 ? "" : "s"} loaded${state.capture.captured_at ? ` on ${escapeHtml(formatDate(state.capture.captured_at))}` : ""}</p><p class="runlog-detail">${state.capture.tool ? escapeHtml(state.capture.tool.name) : "No capture manifest supplied"}</p></div>
          </div>
        </div>
        <div class="limit-note" style="margin-top:18px">
          ${INFO_ICON}
          <span>${escapeHtml((verification.limitations || [])[0] || "Static evidence cannot establish usability.")} <a href="#/verification">Read every evidence boundary</a>.</span>
        </div>
      </section>`;
  }
  function visualFindings() {
    const visualChecks = new Set([
      "a11y.contrast",
      "a11y.hover-only",
      "a11y.image-alt",
      "a11y.mobile-input-size",
      "precision.fixed-width",
      "responsive.overflow-mask",
      "responsive.media-queries",
      "motion.transition-all",
    ]);
    const categories = new Set(["visual", "typography", "motion", "anti-slop"]);
    return findingsByPriority(
      state.audit.findings.filter(
        (finding) =>
          visualChecks.has(finding.check) ||
          categories.has(finding.category) ||
          String(finding.check || "").startsWith("typography."),
      ),
    ).filter((finding) => effectiveStatus(finding) === "open");
  }

  function visualFilterOptions() {
    const viewports = [
      ...new Set(state.shots.map((shot) => shot.viewport).filter(Boolean)),
    ];
    return [
      `<button class="filter-button" type="button" data-shot-filter="all" aria-pressed="${state.filters.visual === "all"}">All</button>`,
      ...viewports.map(
        (viewport) =>
          `<button class="filter-button" type="button" data-shot-filter="${escapeHtml(viewport)}" aria-pressed="${state.filters.visual === viewport}">${escapeHtml(humanize(viewport))}</button>`,
      ),
    ].join("");
  }

  function shotCards() {
    const filtered =
      state.filters.visual === "all"
        ? state.shots
        : state.shots.filter((shot) => shot.viewport === state.filters.visual);
    if (filtered.length === 0) {
      return '<p class="inline-empty" style="grid-column:1/-1">No screenshots match this viewport.</p>';
    }
    return filtered
      .map((shot) => {
        const src = `data/${shot.path}`;
        const title = shot.title || shot.page || "Captured page";
        const dimensions = `${shot.width || "?"} × ${shot.height || "?"}`;
        return `
          <figure class="shot-card">
            <button class="shot-button" type="button" data-open-shot="${escapeHtml(shot.id)}" aria-label="Open screenshot of ${escapeHtml(title)} at ${escapeHtml(shot.viewport || "unknown")} viewport">
              <img src="${escapeHtml(src)}" alt="${escapeHtml(title)} at ${escapeHtml(shot.viewport || "unknown")} viewport" loading="lazy">
            </button>
            <figcaption>
              <div>
                <p class="shot-title">${escapeHtml(title)}</p>
                <p class="shot-meta">${escapeHtml(shot.page || "")}</p>
              </div>
              <span class="section-meta">${escapeHtml(humanize(shot.viewport || "unknown"))} · ${escapeHtml(dimensions)}</span>
            </figcaption>
          </figure>`;
      })
      .join("");
  }

  function visualFindingRow(finding) {
    return `
      <button class="visual-finding" type="button" data-brief="${escapeHtml(finding.id)}">
        <span class="severity is-${escapeHtml(finding.severity)}">${escapeHtml(SEVERITY_LABEL[finding.severity] || finding.severity)}</span>
        <h3>${escapeHtml(finding.title)}</h3>
        <p>${escapeHtml(finding.check)} · ${escapeHtml(finding.file)}:${escapeHtml(finding.line)}</p>
      </button>`;
  }

  function viewVisual() {
    const findings = visualFindings();
    const captureLimitations = state.capture.limitations || [];
    const screenshotBlock =
      state.shots.length === 0
        ? `<div class="empty-state">
            <p class="eyebrow">No visual evidence</p>
            <h2>This workspace has no screenshots</h2>
            <p>Source findings remain available, but no rendered claim is supported. Capture the project with Chromium, then regenerate the workspace data.</p>
            ${commandBlock("python3 scripts/capture.py <project> --out screenshots")}
          </div>`
        : `<section class="section" aria-labelledby="shots-title">
            ${sectionHead("Captured screens", `${state.shots.length} viewport evidence file${state.shots.length === 1 ? "" : "s"}`, "shots-title")}
            <div class="shot-toolbar" style="margin-bottom:14px">${visualFilterOptions()}</div>
            <div class="shot-grid" id="shot-grid">${shotCards()}</div>
          </section>`;

    return `
      ${pageHeader({
        eyebrow: "Rendered evidence · Chromium",
        title: "What does it actually look like?",
        lede: "Screenshots sit beside source-level findings so visual judgement is grounded in a real render, not an imagined one.",
        aside: `<button class="button is-quiet" type="button" data-action="open-commands">Capture commands</button>`,
      })}
      ${screenshotBlock}
      <div class="split" style="margin-top:46px">
        <section aria-labelledby="visual-findings-title">
          ${sectionHead("Visual and interaction findings", `${findings.length} open · source evidence`, "visual-findings-title")}
          <div class="finding-list">
            ${
              findings.length
                ? findings.map(visualFindingRow).join("")
                : inlineEmpty("No open visual findings in this dataset.")
            }
          </div>
          <p class="fine-print">Findings are selected from accessibility, responsive, motion, typography, and anti-slop checks. They are not a complete substitute for an expert visual review.</p>
        </section>
        <aside class="stack">
          <div class="panel">
            <p class="panel-title">Capture provenance</p>
            <dl class="kv">
              <div><dt>Status</dt><dd>${state.capture.captured ? "Captured" : "Not supplied"}</dd></div>
              <div><dt>Captured</dt><dd>${escapeHtml(formatDate(state.capture.captured_at, "Not recorded"))}</dd></div>
              <div><dt>Tool</dt><dd>${escapeHtml(state.capture.tool?.name || "Not recorded")}</dd></div>
              <div><dt>Viewports</dt><dd>${(state.capture.viewports || []).map((viewport) => `${escapeHtml(viewport.name)} ${viewport.width}×${viewport.height}`).join(" · ") || "Not recorded"}</dd></div>
            </dl>
          </div>
          <div class="panel">
            <p class="panel-title">Evidence boundaries</p>
            ${
              captureLimitations.length
                ? captureLimitations
                    .slice(0, 3)
                    .map((limitation) => `<p class="fine-print">${escapeHtml(limitation)}</p>`)
                    .join("")
                : '<p class="fine-print">No capture limitations were supplied.</p>'
            }
          </div>
        </aside>
      </div>`;
  }
  function componentRows(components) {
    if (components.length === 0) {
      return `<tr class="empty-row"><td colspan="${MATRIX_COLUMNS.length + 3}">No components match these filters.</td></tr>`;
    }
    return components
      .map((component) => {
        const cells = MATRIX_COLUMNS.map((column) => {
          const item = (component.states || []).find((candidate) =>
            column.names.includes(candidate.name),
          );
          if (!item) {
            return `<td class="col-state" aria-label="${escapeHtml(column.label)}: not applicable"><span class="cell-status is-na"><span class="sr-only">Not applicable</span></span></td>`;
          }
          const label = STATUS_LABEL[item.status] || item.status;
          return `<td class="col-state" aria-label="${escapeHtml(column.label)} (${escapeHtml(item.name)}): ${escapeHtml(label)}. ${escapeHtml(item.evidence)}" title="${escapeHtml(item.name)}: ${escapeHtml(item.evidence)}"><span class="cell-status is-${escapeHtml(item.status)}"><span class="sr-only">${escapeHtml(label)}</span></span></td>`;
        }).join("");
        return `
          <tr>
            <td class="col-component">
              <button class="component-button" type="button" data-component-id="${escapeHtml(component.id)}">${escapeHtml(component.name)}</button>
              <span class="component-file">${escapeHtml(component.id)} · ${escapeHtml(component.file)}:${escapeHtml(component.line)}</span>
            </td>
            ${cells}
            <td class="coverage-cell"><strong>${component.coverage}%</strong></td>
            <td><button class="row-action" type="button" data-component-id="${escapeHtml(component.id)}">Record</button></td>
          </tr>`;
      })
      .join("");
  }

  function filteredComponents() {
    const query = state.filters.componentQuery.trim().toLowerCase();
    return state.audit.components.filter((component) => {
      if (
        state.filters.componentStatus !== "all" &&
        component.status !== state.filters.componentStatus
      ) {
        return false;
      }
      if (
        state.filters.componentKind !== "all" &&
        component.kind !== state.filters.componentKind
      ) {
        return false;
      }
      if (!query) return true;
      return [
        component.id,
        component.name,
        component.kind,
        component.file,
        component.element,
      ]
        .join(" ")
        .toLowerCase()
        .includes(query);
    });
  }

  function componentCountText(list) {
    const total = state.audit.components.length;
    return list.length === total
      ? `${total} components`
      : `${list.length} of ${total} components`;
  }

  function viewComponents() {
    const components = state.audit.summary.components;
    const kinds = [
      ...new Set(state.audit.components.map((component) => component.kind)),
    ].sort();
    const filtered = filteredComponents();
    const headerCells = MATRIX_COLUMNS.map(
      (column) =>
        `<th class="col-state" scope="col" title="${escapeHtml(column.names.join(" / "))}">${escapeHtml(column.label)}</th>`,
    ).join("");
    const minWidth = 230 + MATRIX_COLUMNS.length * 54 + 110;

    return `
      ${pageHeader({
        eyebrow: "Coverage ledger",
        title: "Every component, every state",
        lede: "The matrix records source evidence for default, interaction, validation, and feedback states. Open a record for the complete state list and evidence notes.",
        aside: `
          <span class="chip is-${escapeHtml(components.missing ? "blocked" : components.partial ? "at-risk" : "ready")}">${components.missing} missing · ${components.partial} partial</span>
          <span class="chip">${components.state_coverage}% coverage</span>`,
      })}
      <div class="section" style="margin-top:0">
        ${sectionHead("State matrix", `${components.total} components · ${state.allStates.length} inferred states`, "matrix-title")}
        <div class="filter-bar">
          <div class="field">
            <label for="component-search">Search</label>
            <input id="component-search" type="search" placeholder="Name, file, element…" value="${escapeHtml(state.filters.componentQuery)}">
          </div>
          <div class="field">
            <label for="component-status">State</label>
            <select id="component-status">
              <option value="all"${selected("all", state.filters.componentStatus)}>All states</option>
              <option value="complete"${selected("complete", state.filters.componentStatus)}>Complete</option>
              <option value="partial"${selected("partial", state.filters.componentStatus)}>Partial</option>
              <option value="missing"${selected("missing", state.filters.componentStatus)}>Missing</option>
            </select>
          </div>
          <div class="field">
            <label for="component-kind">Kind</label>
            <select id="component-kind">
              <option value="all"${selected("all", state.filters.componentKind)}>All kinds</option>
              ${kinds.map((kind) => `<option value="${escapeHtml(kind)}"${selected(kind, state.filters.componentKind)}>${escapeHtml(humanize(kind))}</option>`).join("")}
            </select>
          </div>
          <p class="section-meta" id="component-count">${componentCountText(filtered)}</p>
        </div>
        <div class="table-wrap">
          <table class="matrix" style="min-width:${minWidth}px">
            <caption>Core state columns · grouped aliases and specialized states live in each component record.</caption>
            <thead>
              <tr>
                <th class="col-component" scope="col">Component</th>
                ${headerCells}
                <th scope="col">Coverage</th>
                <th scope="col"><span class="sr-only">Open record</span></th>
              </tr>
            </thead>
            <tbody id="component-rows">${componentRows(filtered)}</tbody>
          </table>
        </div>
        <p class="fine-print">A filled circle means evidence exists; a half circle means partial evidence; a cross means the state was not found. Absence is inferred from scanned source and may not reflect framework-generated behavior.</p>
      </div>`;
  }

  function refreshComponents() {
    const rows = document.getElementById("component-rows");
    if (!rows) return;
    const filtered = filteredComponents();
    rows.innerHTML = componentRows(filtered);
    const count = document.getElementById("component-count");
    if (count) count.textContent = componentCountText(filtered);
  }
  function tokenRows(items, emptyMessage) {
    if (!items || items.length === 0) return inlineEmpty(emptyMessage);
    return items
      .map(
        (item) => `
        <div class="token-row">
          <span class="token-name">${escapeHtml(item.value)}</span>
          <span class="token-value">${item.count} use${item.count === 1 ? "" : "s"}</span>
        </div>`,
      )
      .join("");
  }

  function safeRadius(value) {
    const raw = String(value || "").trim();
    return /^(0|(?:\d*\.?\d+)(?:px|rem|em|%|vh|vw|pt))$/i.test(raw) ? raw : "0";
  }

  function valueChart(items, emptyMessage) {
    if (!items || items.length === 0) return inlineEmpty(emptyMessage);
    const maximum = Math.max(...items.map((item) => item.count), 1);
    return `<div class="scale-list">${items
      .map(
        (item) => `
        <div class="scale-row">
          <span class="scale-label">${escapeHtml(item.value)}</span>
          <span class="scale-track" aria-hidden="true"><span style="width:${Math.round((item.count / maximum) * 100)}%"></span></span>
          <span class="scale-count">×${item.count}</span>
        </div>`,
      )
      .join("")}</div>`;
  }

  function viewDesign() {
    const design = state.audit.design_system;
    const colors = (design.colors || []).filter((color) =>
      /^#[0-9a-f]{6}$/i.test(color.value),
    );
    const fonts = design.fonts || [];
    const notes = design.notes || [];
    const literals = design.literals_vs_tokens || {
      colour_literals: 0,
      token_references: 0,
    };
    const specimenTitle = state.meta.project_label || state.audit.project.name;

    return `
      ${pageHeader({
        eyebrow: "Extracted tokens · source evidence",
        title: "The system beneath the screen",
        lede: "Colour, type, spacing, and radius values are read from the scanned source. This is an evidence inventory, not a house style guide.",
        aside: `<a class="button is-quiet" href="data/audit.json" download="finishline-audit.json">Audit JSON</a>`,
      })}
      <p class="design-note"><strong>${literals.colour_literals}</strong> colour literals against <strong>${literals.token_references}</strong> token references were found. ${notes.length ? escapeHtml(notes[0]) : "Inspect local conventions before prescribing a system."}</p>
      <section class="section" style="margin-top:0" aria-labelledby="type-specimen-title">
        ${sectionHead("Reading specimen", "FINISHLINE's reading face, not the audited font", "type-specimen-title")}
        <div class="specimen">
          <p class="specimen-display">${escapeHtml(specimenTitle)}</p>
          <p class="specimen-lede">Finished interfaces are not only visually resolved. They hold together under error, loading, empty, and success conditions, and they remain legible when the happy path is not available.</p>
          <p class="specimen-mono">Newsreader / IBM Plex Sans / IBM Plex Mono</p>
        </div>
        <p class="fine-print">This specimen demonstrates the workspace's own typography. Audited families are listed below; they are not downloaded or previewed here.</p>
      </section>
      <div class="split" style="margin-top:46px">
        <section aria-labelledby="colour-title">
          ${sectionHead("Colour evidence", `${colors.length} literal shades`, "colour-title")}
          <div class="swatch-grid">
            ${
              colors.length
                ? colors
                    .map(
                      (color) => `
                      <div class="swatch">
                        <div class="swatch-color" style="background:${color.value}" aria-hidden="true"></div>
                        <div class="swatch-meta">
                          <span class="swatch-hex">${escapeHtml(color.value)}</span>
                          <span class="swatch-count">${color.count} use${color.count === 1 ? "" : "s"}</span>
                        </div>
                      </div>`,
                    )
                    .join("")
                : inlineEmpty("No literal colours were extracted.")
            }
          </div>
          <p class="fine-print">Exact literals only; gradients, alpha composites, and variable-resolved colours are excluded from this evidence.</p>
        </section>
        <aside class="stack">
          <div class="panel">
            <p class="panel-title">Families</p>
            ${tokenRows(fonts, "No font families were extracted.")}
          </div>
          <div class="panel">
            <p class="panel-title">Type scale</p>
            ${tokenRows(design.font_sizes, "No font sizes were extracted.")}
          </div>
          <div class="panel">
            <p class="panel-title">Custom properties</p>
            ${
              (design.custom_properties || []).length
                ? `<div class="token-list">${design.custom_properties
                    .map(
                      (property) => `
                      <div class="token-row">
                        <span class="token-name">${escapeHtml(property.name)}</span>
                        <span class="token-value">${escapeHtml(property.value)}</span>
                      </div>`,
                    )
                    .join("")}</div>`
                : inlineEmpty("No custom properties were extracted.")
            }
          </div>
        </aside>
      </div>
      <div class="split" style="margin-top:46px">
        <section aria-labelledby="spacing-title">
          ${sectionHead("Spacing frequency", "Declared values · not a verdict", "spacing-title")}
          ${valueChart(design.spacing, "No spacing values were extracted.")}
          <p class="fine-print">Repeated values suggest a de facto scale. A high number of one-off values may indicate drift, but context still decides.</p>
        </section>
        <aside class="stack">
          <div class="panel">
            <p class="panel-title">Radii</p>
            <div class="radius-grid">
              ${
                (design.radii || []).length
                  ? design.radii
                      .map(
                        (radius) => `
                        <div class="radius-sample" style="border-radius:${safeRadius(radius.value)}">${escapeHtml(radius.value)}</div>`,
                      )
                      .join("")
                  : inlineEmpty("No radii were extracted.")
              }
            </div>
          </div>
          <div class="panel">
            <p class="panel-title">Shadows</p>
            <div class="shadow-grid">
              ${
                (design.shadows || []).length
                  ? design.shadows
                      .map(
                        (shadow) => `
                        <div>
                          <div class="shadow-sample" aria-hidden="true"></div>
                          <p class="shadow-value">${escapeHtml(shadow.value)} · ×${shadow.count}</p>
                        </div>`,
                      )
                      .join("")
                  : inlineEmpty("No shadows were extracted.")
              }
            </div>
          </div>
        </aside>
      </div>
      ${
        notes.length > 1
          ? `<section class="section" aria-labelledby="design-notes-title">
              ${sectionHead("Extraction notes", "Supporting evidence", "design-notes-title")}
              ${notes.map((note) => `<div class="limit-note" style="margin-bottom:8px">${INFO_ICON}<span>${escapeHtml(note)}</span></div>`).join("")}
            </section>`
          : ""
      }`;
  }
  function repairSummaryText(filtered) {
    const all = state.audit.findings;
    const local = all.filter((finding) => state.triage[finding.id]);
    const fixed = local.filter((finding) => state.triage[finding.id] === "fixed").length;
    const ignored = local.filter((finding) => state.triage[finding.id] === "ignored").length;
    return `${filtered.length} visible · ${all.length} audited · ${fixed} fixed locally · ${ignored} ignored locally`;
  }

  function filteredRepairs() {
    const query = state.filters.repairQuery.trim().toLowerCase();
    return findingsByPriority(state.audit.findings).filter((finding) => {
      if (
        state.filters.repairSeverity !== "all" &&
        finding.severity !== state.filters.repairSeverity
      ) {
        return false;
      }
      if (
        state.filters.repairTriage !== "all" &&
        effectiveStatus(finding) !== state.filters.repairTriage
      ) {
        return false;
      }
      if (!query) return true;
      return [
        finding.id,
        finding.title,
        finding.check,
        finding.category,
        finding.file,
        finding.component || "",
      ]
        .join(" ")
        .toLowerCase()
        .includes(query);
    });
  }

  function triageSelect(finding, label) {
    const current = effectiveStatus(finding);
    return `
      <select class="triage-select" data-triage-id="${escapeHtml(finding.id)}" aria-label="${escapeHtml(label)}">
        <option value="open"${selected("open", current)}>Open</option>
        <option value="fixed"${selected("fixed", current)}>Fixed locally</option>
        <option value="ignored"${selected("ignored", current)}>Ignored</option>
      </select>`;
  }

  function repairRows(findings) {
    if (findings.length === 0) {
      return '<tr class="empty-row"><td colspan="7">No findings match these filters.</td></tr>';
    }
    return findings
      .map(
        (finding) => `
        <tr>
          <td class="finding-id">${escapeHtml(finding.id)}</td>
          <td>
            <span class="repair-title">${escapeHtml(finding.title)}</span>
            <span class="repair-check">${escapeHtml(finding.check)}</span>
          </td>
          <td><span class="severity is-${escapeHtml(finding.severity)}">${escapeHtml(SEVERITY_LABEL[finding.severity] || finding.severity)}</span></td>
          <td><span class="component-file">${escapeHtml(finding.file)}:${escapeHtml(finding.line)}</span></td>
          <td><span class="confidence">${escapeHtml(finding.confidence)}</span></td>
          <td>${triageSelect(finding, `Triage status for ${finding.id}`)}</td>
          <td><button class="row-action" type="button" data-brief="${escapeHtml(finding.id)}">Brief</button></td>
        </tr>`,
      )
      .join("");
  }

  function viewRepairs() {
    const findings = filteredRepairs();
    return `
      ${pageHeader({
        eyebrow: "Repair briefs · execution order",
        title: "Turn evidence into finished state",
        lede: "Work highest severity first, preserve what the evidence proves, and re-run the audit after every repair. Triage is local to this browser and is not proof of a fix.",
        aside: `<button class="button" type="button" data-action="open-commands">Re-run audit</button>`,
      })}
      <div class="triage-banner">
        <p><strong>Local triage only.</strong> Status changes live in this browser and never edit the audited project.</p>
        <span class="section-meta" id="repair-stat">${escapeHtml(repairSummaryText(findings))}</span>
      </div>
      <div class="filter-bar">
        <div class="field">
          <label for="repair-search">Search</label>
          <input id="repair-search" type="search" placeholder="ID, title, check, file…" value="${escapeHtml(state.filters.repairQuery)}">
        </div>
        <div class="field">
          <label for="repair-severity">Severity</label>
          <select id="repair-severity">
            <option value="all"${selected("all", state.filters.repairSeverity)}>All severities</option>
            <option value="critical"${selected("critical", state.filters.repairSeverity)}>Critical</option>
            <option value="high"${selected("high", state.filters.repairSeverity)}>High</option>
            <option value="medium"${selected("medium", state.filters.repairSeverity)}>Medium</option>
            <option value="low"${selected("low", state.filters.repairSeverity)}>Low</option>
          </select>
        </div>
        <div class="field">
          <label for="repair-triage">Triage</label>
          <select id="repair-triage">
            <option value="all"${selected("all", state.filters.repairTriage)}>All statuses</option>
            <option value="open"${selected("open", state.filters.repairTriage)}>Open</option>
            <option value="fixed"${selected("fixed", state.filters.repairTriage)}>Fixed locally</option>
            <option value="ignored"${selected("ignored", state.filters.repairTriage)}>Ignored</option>
          </select>
        </div>
      </div>
      <div class="table-wrap">
        <table class="matrix repairs-table">
          <caption>Repair queue · sorted critical to low. Status changes are stored only in this browser.</caption>
          <thead>
            <tr>
              <th scope="col">ID</th>
              <th scope="col">Finding</th>
              <th scope="col">Severity</th>
              <th scope="col">Location</th>
              <th scope="col">Evidence</th>
              <th scope="col">Triage</th>
              <th scope="col">Brief</th>
            </tr>
          </thead>
          <tbody id="repair-rows">${repairRows(findings)}</tbody>
        </table>
      </div>
      <p class="fine-print">Marking a finding fixed here records a local intention. Close the loop by changing the project, re-running the check, and comparing the next audit.</p>`;
  }

  function refreshRepairs() {
    const rows = document.getElementById("repair-rows");
    if (!rows) return;
    const findings = filteredRepairs();
    rows.innerHTML = repairRows(findings);
    const summary = document.getElementById("repair-stat");
    if (summary) summary.textContent = repairSummaryText(findings);
  }
  function commandBlock(command) {
    return `
      <div class="command-block">
        <code>${escapeHtml(command)}</code>
        <button class="text-button" type="button" data-copy="${escapeHtml(command)}">Copy</button>
      </div>`;
  }

  function screenshotProvenance() {
    if (state.capture.shots.length === 0) {
      return inlineEmpty("No screenshot manifest was loaded.");
    }
    return `
      <div class="table-wrap">
        <table class="matrix">
          <caption>Screenshot manifest · captured evidence</caption>
          <thead>
            <tr>
              <th scope="col">Shot</th>
              <th scope="col">Page</th>
              <th scope="col">Viewport</th>
              <th scope="col">Size</th>
              <th scope="col">File</th>
            </tr>
          </thead>
          <tbody>
            ${state.capture.shots
              .map(
                (shot) => `
                <tr>
                  <td>${escapeHtml(shot.title || shot.id)}</td>
                  <td><span class="component-file">${escapeHtml(shot.page || "—")}</span></td>
                  <td>${escapeHtml(humanize(shot.viewport || "unknown"))}</td>
                  <td><span class="component-file">${shot.width || "?"} × ${shot.height || "?"}</span></td>
                  <td><span class="component-file">${escapeHtml(shot.path)}</span></td>
                </tr>`,
              )
              .join("")}
          </tbody>
        </table>
      </div>`;
  }

  function viewVerification() {
    const audit = state.audit;
    const verification = audit.verification;
    const checkCount =
      verification.check_count || (verification.checks_run || []).length;
    const limitations = verification.limitations || [];
    const captured = state.capture.count || verification.screenshots || 0;

    return `
      ${pageHeader({
        eyebrow: "Evidence boundaries · reproducibility",
        title: "What was checked, and what was not",
        lede: "Automation narrows uncertainty. It does not certify WCAG conformance, usability, or task success. Reproduce the run and inspect its limits before claiming readiness.",
        aside: `<span class="chip is-${verification.rendered ? "ready" : "needs-polish"}">${verification.rendered ? "Rendered run" : "Static only"}</span>`,
      })}
      <div class="stat-strip">
        ${stat(checkCount, "Checks executed")}
        ${stat(audit.summary.confidence.verified, "Verified findings", `${audit.summary.confidence.inferred} inferred`)}
        ${stat(captured, "Screenshots", "separate capture run")}
        ${stat(escapeHtml(verification.mode), "Audit mode", verification.rendered ? "browser-backed" : "source only")}
      </div>
      <div class="split" style="margin-top:42px">
        <section aria-labelledby="ran-title">
          ${sectionHead("Checks that ran", `${checkCount} registered checks`, "ran-title")}
          <details class="checks">
            <summary>Show every check name</summary>
            <div class="check-tags">
              ${(verification.checks_run || []).map((check) => `<span class="check-tag">${escapeHtml(check)}</span>`).join("")}
            </div>
          </details>
          <p class="fine-print">Source checks use conservative evidence rules. A missing signal is reported as inferred absence, not as a proven runtime bug.</p>
        </section>
        <aside class="stack" aria-labelledby="boundaries-title">
          ${sectionHead("Evidence boundaries", "Read before shipping", "boundaries-title")}
          ${
            limitations.length
              ? limitations
                  .map(
                    (limitation) =>
                      `<div class="limit-note">${INFO_ICON}<span>${escapeHtml(limitation)}</span></div>`,
                  )
                  .join("")
              : `<div class="limit-note">${INFO_ICON}<span>No limitations were supplied. Treat that as missing evidence, not confidence.</span></div>`
          }
        </aside>
      </div>
      <section class="section" aria-labelledby="reproduce-title">
        ${sectionHead("Reproduce this evidence", "Local commands · no hosted service", "reproduce-title")}
        ${COMMANDS.map(commandBlock).join("")}
        <p class="fine-print">The workspace reads <code>data/audit.json</code>, <code>data/screenshots.json</code>, and <code>data/meta.json</code>. It does not upload project source or screenshots.</p>
      </section>
      <section class="section" aria-labelledby="provenance-title">
        ${sectionHead("Captured evidence", "Real renders only", "provenance-title")}
        ${screenshotProvenance()}
        <p class="fine-print">Screenshots prove that pixels existed at a given viewport and time. They do not prove keyboard access, screen-reader behavior, or task completion.</p>
      </section>`;
  }
  function openBrief(id) {
    const finding = state.audit.findings.find((item) => item.id === id);
    if (!finding) return;
    const status = effectiveStatus(finding);
    document.getElementById("repair-dialog-title").textContent = finding.title;
    document.getElementById("repair-dialog-body").innerHTML = `
      <p class="dialog-lede">${escapeHtml(finding.id)} · ${escapeHtml(finding.check)}</p>
      <ul class="detail-meta">
        <li>${escapeHtml(SEVERITY_LABEL[finding.severity] || finding.severity)}</li>
        <li>${escapeHtml(finding.category)}</li>
        <li>${escapeHtml(finding.confidence)} evidence</li>
        <li>${escapeHtml(finding.file)}:${escapeHtml(finding.line)}</li>
        <li>${escapeHtml(STATUS_LABEL[status] || status)}</li>
      </ul>
      <div class="detail-section">
        <h3>Evidence</h3>
        <pre class="evidence-block">${escapeHtml(finding.evidence)}</pre>
      </div>
      <div class="detail-section">
        <h3>Why it matters</h3>
        <p>${escapeHtml(finding.why)}</p>
      </div>
      <div class="detail-section">
        <h3>Repair direction</h3>
        <p>${escapeHtml(finding.repair)}</p>
      </div>
      <div class="detail-section">
        <h3>Local triage</h3>
        <p>This status is browser-only. It does not edit source or prove that a repair was made.</p>
        <div class="dialog-actions">
          <button class="button is-quiet" type="button" data-set-triage="open" data-finding-id="${escapeHtml(finding.id)}">Reopen</button>
          <button class="button is-quiet" type="button" data-set-triage="ignored" data-finding-id="${escapeHtml(finding.id)}">Ignore locally</button>
          <button class="button" type="button" data-set-triage="fixed" data-finding-id="${escapeHtml(finding.id)}">Mark fixed locally</button>
        </div>
      </div>`;
    openDialog(repairDialog, document.activeElement);
  }

  function openComponent(id) {
    const component = state.audit.components.find((item) => item.id === id);
    if (!component) return;
    document.getElementById("component-dialog-title").textContent = component.name;
    document.getElementById("component-dialog-body").innerHTML = `
      <p class="dialog-lede">${escapeHtml(component.id)} · ${escapeHtml(humanize(component.kind))} · ${escapeHtml(STATUS_LABEL[component.status] || component.status)}</p>
      <ul class="detail-meta">
        <li>${escapeHtml(component.file)}:${escapeHtml(component.line)}</li>
        <li>${component.coverage}% coverage</li>
        <li>${(component.states || []).length} inferred states</li>
      </ul>
      <div class="coverage-bar" aria-hidden="true"><span class="is-${escapeHtml(component.status)}" style="width:${component.coverage}%"></span></div>
      <pre class="evidence-block">${escapeHtml(component.element)}</pre>
      <div class="state-detail-list">
        ${(component.states || [])
          .map(
            (item) => `
            <div class="state-detail">
              <span class="state-detail-name">${escapeHtml(item.name)}</span>
              <span class="cell-status is-${escapeHtml(item.status)}">${escapeHtml(STATUS_LABEL[item.status] || item.status)}</span>
              <span class="state-detail-evidence">${escapeHtml(item.evidence)} <span class="confidence">${escapeHtml(item.confidence)}</span></span>
            </div>`,
          )
          .join("")}
      </div>
      <p class="fine-print">State presence and absence are inferred from scanned source. Check framework behavior and real interaction before treating this record as proof.</p>`;
    openDialog(componentDialog, document.activeElement);
  }

  function openShot(id) {
    const shot = state.shots.find((item) => item.id === id);
    if (!shot) return;
    const title = shot.title || shot.page || "Screenshot";
    document.getElementById("shot-dialog-title").textContent = title;
    document.getElementById("shot-dialog-body").innerHTML = `
      <img src="${escapeHtml(`data/${shot.path}`)}" alt="${escapeHtml(title)} at ${escapeHtml(shot.viewport || "unknown")} viewport">
      <p class="lightbox-caption">
        <span>${escapeHtml(shot.page || "")} · ${escapeHtml(humanize(shot.viewport || "unknown"))} · ${shot.width || "?"} × ${shot.height || "?"}</span>
        <span>${escapeHtml(formatDate(shot.captured_at || state.capture.captured_at))}</span>
      </p>`;
    openDialog(shotDialog, document.activeElement);
  }

  function openDialog(dialog, trigger) {
    if (!dialog) return;
    state.lastDialogTrigger = trigger || document.activeElement;
    for (const other of document.querySelectorAll("dialog[open]")) {
      if (other !== dialog) other.close();
    }
    if (typeof dialog.showModal === "function") {
      dialog.showModal();
    } else {
      dialog.setAttribute("open", "");
    }
  }

  function closeOpenDialogs() {
    state.lastDialogTrigger = null;
    for (const dialog of document.querySelectorAll("dialog[open]")) {
      dialog.close();
    }
  }

  function renderFatal(error) {
    state.audit = null;
    document.getElementById("rail-project").textContent = "Evidence unavailable";
    document.getElementById("rail-project-meta").textContent =
      "Audit data could not be loaded";
    document.getElementById("rail-readiness").innerHTML =
      '<span class="status-square is-neutral" aria-hidden="true"></span><span>No static run</span>';
    const badge = document.getElementById("data-badge");
    badge.textContent = "No evidence";
    badge.classList.remove("is-sample");
    document.title = "Evidence unavailable — FINISHLINE";
    const message = error instanceof Error ? error.message : String(error);
    app.innerHTML = `
      <header class="page-header">
        <div>
          <p class="eyebrow">Workspace blocked</p>
          <h1 class="page-title">The evidence did not load</h1>
          <p class="page-lede">This workspace renders only from local audit files. It will not invent a fallback dataset.</p>
        </div>
      </header>
      <div class="empty-state">
        <h2>Could not read the audit</h2>
        <p>${escapeHtml(message)}</p>
        <p>Open the workspace from a local web server, not directly from the filesystem, then regenerate its data.</p>
        ${commandBlock("python3 scripts/workspace_data.py --audit audit.json --screenshots screenshots/screenshots.json --out ui/workspace/data")}
        ${commandBlock("python3 -m http.server 4173 --directory ui/workspace")}
      </div>`;
    main.focus({ preventScroll: true });
  }
  function setRail(open) {
    const next = Boolean(open);
    rail.classList.toggle("is-open", next);
    railToggle.setAttribute("aria-expanded", String(next));
    const label = railToggle.querySelector(".sr-only");
    if (label) label.textContent = next ? "Close navigation" : "Open navigation";
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      toast("Command copied");
      announce("Command copied to clipboard");
    } catch {
      const field = document.createElement("textarea");
      field.value = text;
      field.setAttribute("readonly", "");
      field.style.position = "fixed";
      field.style.opacity = "0";
      document.body.append(field);
      field.select();
      let copied = false;
      try {
        copied = document.execCommand("copy");
      } catch {
        copied = false;
      }
      field.remove();
      toast(copied ? "Command copied" : "Copy failed");
      announce(copied ? "Command copied to clipboard" : "Could not copy command");
    }
  }

  function updateRepairAfterTriage() {
    if (state.filters.repairTriage === "all") {
      const summary = document.getElementById("repair-stat");
      if (summary) summary.textContent = repairSummaryText(filteredRepairs());
    } else {
      refreshRepairs();
    }
  }

  function setFindingTriage(id, status) {
    if (!saveTriage(id, status)) return;
    toast(`${id} marked ${STATUS_LABEL[status].toLowerCase()} locally`);
    announce(`${id} marked ${STATUS_LABEL[status].toLowerCase()} in this browser only`);
    closeOpenDialogs();
    if (state.route === "repairs") refreshRepairs();
  }

  function handleActionClick(event) {
    const closeButton = event.target.closest("[data-close-dialog]");
    if (closeButton) {
      const dialog = closeButton.closest("dialog");
      if (dialog) dialog.close();
      return;
    }

    const commandButton = event.target.closest('[data-action="open-commands"]');
    if (commandButton) {
      openDialog(commandDialog, commandButton);
      return;
    }

    const copyButton = event.target.closest("[data-copy]");
    if (copyButton) {
      event.preventDefault();
      copyText(copyButton.dataset.copy || "");
      return;
    }

    const shotFilter = event.target.closest("[data-shot-filter]");
    if (shotFilter) {
      state.filters.visual = shotFilter.dataset.shotFilter || "all";
      for (const button of document.querySelectorAll("[data-shot-filter]")) {
        button.setAttribute(
          "aria-pressed",
          String(button.dataset.shotFilter === state.filters.visual),
        );
      }
      const grid = document.getElementById("shot-grid");
      if (grid) grid.innerHTML = shotCards();
      return;
    }

    const shotButton = event.target.closest("[data-open-shot]");
    if (shotButton) {
      openShot(shotButton.dataset.openShot);
      return;
    }

    const componentButton = event.target.closest("[data-component-id]");
    if (componentButton) {
      openComponent(componentButton.dataset.componentId);
      return;
    }

    const briefButton = event.target.closest("[data-brief]");
    if (briefButton) {
      event.preventDefault();
      openBrief(briefButton.dataset.brief);
      return;
    }

    const triageButton = event.target.closest("[data-set-triage]");
    if (triageButton) {
      setFindingTriage(
        triageButton.dataset.findingId,
        triageButton.dataset.setTriage,
      );
      return;
    }

    const navLink = event.target.closest(".nav-link");
    if (navLink && window.innerWidth <= 860) setRail(false);
  }

  function handleAppInput(event) {
    const input = event.target;
    if (input.id === "component-search") {
      state.filters.componentQuery = input.value;
      refreshComponents();
      return;
    }
    if (input.id === "repair-search") {
      state.filters.repairQuery = input.value;
      refreshRepairs();
    }
  }

  function handleAppChange(event) {
    const control = event.target;
    if (control.id === "component-status") {
      state.filters.componentStatus = control.value;
      refreshComponents();
      return;
    }
    if (control.id === "component-kind") {
      state.filters.componentKind = control.value;
      refreshComponents();
      return;
    }
    if (control.id === "repair-severity") {
      state.filters.repairSeverity = control.value;
      refreshRepairs();
      return;
    }
    if (control.id === "repair-triage") {
      state.filters.repairTriage = control.value;
      refreshRepairs();
      return;
    }
    if (control.matches("[data-triage-id]")) {
      const id = control.dataset.triageId;
      const status = control.value;
      if (!saveTriage(id, status)) return;
      toast(`${id} marked ${STATUS_LABEL[status].toLowerCase()} locally`);
      announce(`${id} marked ${STATUS_LABEL[status].toLowerCase()} in this browser only`);
      updateRepairAfterTriage();
    }
  }

  function bindDialog(dialog) {
    if (!dialog) return;
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener("close", () => {
      const trigger = state.lastDialogTrigger;
      state.lastDialogTrigger = null;
      if (trigger && document.contains(trigger)) {
        trigger.focus({ preventScroll: true });
      }
    });
  }

  function bindEvents() {
    railToggle.addEventListener("click", () => {
      setRail(!rail.classList.contains("is-open"));
    });
    document.addEventListener("click", handleActionClick);
    app.addEventListener("input", handleAppInput);
    app.addEventListener("change", handleAppChange);
    window.addEventListener("hashchange", () => handleRoute(false));
    window.addEventListener("resize", () => {
      if (window.innerWidth > 860 && rail.classList.contains("is-open")) {
        setRail(false);
      }
    });
    bindDialog(componentDialog);
    bindDialog(shotDialog);
    bindDialog(commandDialog);
    bindDialog(repairDialog);
    setRail(false);
  }

  bindEvents();
  loadData();
})();
