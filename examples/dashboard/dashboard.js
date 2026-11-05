(() => {
  "use strict";

  const svg = document.getElementById("traffic-chart");
  const chartTitle = document.getElementById("chart-svg-title");
  const chartDescription = document.getElementById("chart-svg-desc");
  const chartSummary = document.getElementById("chart-summary");
  const chartSub = document.getElementById("chart-sub");
  const requestsBody = document.getElementById("requests-body");
  const tableEmpty = document.getElementById("table-empty");
  const tableCount = document.getElementById("table-count");
  const lastUpdated = document.getElementById("last-updated");
  const search = document.getElementById("request-search");
  const statusFilter = document.getElementById("status-filter");
  const clearFilters = document.getElementById("clear-filters");
  const refresh = document.getElementById("refresh-data");
  const exportButton = document.getElementById("export-csv");
  const dateNode = document.getElementById("current-date");
  const svgNamespace = "http://www.w3.org/2000/svg";

  const requests = [
    { key: "req_01J8X4M2", method: "GET", path: "/v1/workspaces", code: 200, tone: "ok", duration: "82 ms", region: "iad1", when: "12s ago" },
    { key: "req_01J8X4KQ", method: "POST", path: "/v1/keys", code: 201, tone: "ok", duration: "104 ms", region: "iad1", when: "28s ago" },
    { key: "req_01J8X4J7", method: "GET", path: "/v1/usage/rollups", code: 200, tone: "ok", duration: "67 ms", region: "fra1", when: "41s ago" },
    { key: "req_01J8X4HT", method: "GET", path: "/v1/requests", code: 429, tone: "warn", duration: "8 ms", region: "sfo1", when: "1m ago" },
    { key: "req_01J8X4G9", method: "POST", path: "/v1/webhooks/deliveries", code: 202, tone: "ok", duration: "193 ms", region: "sfo1", when: "1m ago" },
    { key: "req_01J8X4F3", method: "PATCH", path: "/v1/workspaces/current", code: 200, tone: "ok", duration: "116 ms", region: "iad1", when: "2m ago" },
    { key: "req_01J8X4DZ", method: "GET", path: "/v1/usage/rollups", code: 500, tone: "error", duration: "1.2 s", region: "fra1", when: "3m ago" },
    { key: "req_01J8X4C1", method: "DELETE", path: "/v1/keys/old_test_key", code: 204, tone: "ok", duration: "74 ms", region: "iad1", when: "3m ago" },
    { key: "req_01J8X4B8", method: "POST", path: "/v1/tokens/rotate", code: 200, tone: "ok", duration: "91 ms", region: "iad1", when: "4m ago" },
    { key: "req_01J8X49V", method: "GET", path: "/v1/health", code: 200, tone: "ok", duration: "4 ms", region: "sfo1", when: "4m ago" },
    { key: "req_01J8X48N", method: "GET", path: "/v1/requests/export", code: 409, tone: "error", duration: "312 ms", region: "fra1", when: "5m ago" },
    { key: "req_01J8X479", method: "GET", path: "/v1/workspaces", code: 200, tone: "ok", duration: "78 ms", region: "sfo1", when: "5m ago" },
  ];

  const statusLabels = {
    ok: "Successful",
    warn: "Throttled",
    error: "Failed",
  };

  const traffic = {
    "24h": {
      labels: Array.from({ length: 24 }, (_, index) => `${String(index).padStart(2, "0")}:00`),
      points: [58, 51, 46, 42, 44, 55, 68, 79, 93, 86, 72, 64, 77, 88, 102, 97, 81, 69, 74, 91, 110, 120, 96, 84],
      capacity: 130,
      sub: "Requests accepted per hour, UTC",
      rangeLabel: "24 hours",
      rejected: "0.42%",
    },
    "7d": {
      labels: ["Thu", "Fri", "Sat", "Sun", "Mon", "Tue", "Wed"],
      points: [1680, 1570, 1410, 1360, 1740, 1890, 1820],
      capacity: 2000,
      sub: "Requests accepted per day, UTC",
      rangeLabel: "7 days",
      rejected: "0.51%",
    },
    "30d": {
      labels: Array.from({ length: 30 }, (_, index) => `${index + 1} Oct`),
      points: [1540, 1580, 1490, 1610, 1570, 1480, 1520, 1630, 1680, 1560, 1510, 1470, 1590, 1650, 1600, 1540, 1490, 1570, 1620, 1680, 1710, 1640, 1590, 1550, 1610, 1690, 1740, 1810, 1760, 1820],
      capacity: 2000,
      sub: "Requests accepted per day, UTC",
      rangeLabel: "30 days",
      rejected: "0.47%",
    },
  };

  let activeRange = "24h";

  function svgElement(name, attributes = {}) {
    const node = document.createElementNS(svgNamespace, name);
    for (const [key, value] of Object.entries(attributes)) {
      node.setAttribute(key, value);
    }
    return node;
  }

  function formatAxis(value) {
    if (value >= 1000) {
      return `${(value / 1000).toFixed(value % 1000 === 0 ? 0 : 1)}M`;
    }
    return `${value}k`;
  }

  function formatCompact(value) {
    return new Intl.NumberFormat("en-US", {
      notation: "compact",
      maximumFractionDigits: 2,
    }).format(value);
  }

  function renderChart(range) {
    const data = traffic[range];
    const width = 640;
    const height = 240;
    const inset = { top: 14, right: 12, bottom: 27, left: 38 };
    const plotWidth = width - inset.left - inset.right;
    const plotHeight = height - inset.top - inset.bottom;
    const max = Math.max(...data.points, data.capacity);
    const rough = max * 1.15;
    const magnitude = 10 ** Math.floor(Math.log10(rough));
    const fraction = rough / magnitude;
    const niceFactor = fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 2.5 ? 2.5 : fraction <= 5 ? 5 : 10;
    const yMax = niceFactor * magnitude;
    const tickCount = yMax >= 1000 ? 5 : 4;
    const bottom = inset.top + plotHeight;
    const xAt = (index) =>
      inset.left + (data.points.length === 1 ? 0 : (plotWidth * index) / (data.points.length - 1));
    const yAt = (value) => inset.top + plotHeight - (value / yMax) * plotHeight;

    for (const child of [...svg.children]) {
      if (child.id !== "chart-svg-title" && child.id !== "chart-svg-desc") {
        child.remove();
      }
    }

    const grid = svgElement("g", { "aria-hidden": "true" });
    for (let step = 0; step <= tickCount; step += 1) {
      const value = (yMax / tickCount) * step;
      const y = yAt(value);
      grid.append(
        svgElement("line", {
          x1: inset.left,
          x2: width - inset.right,
          y1: y,
          y2: y,
          class: "chart-grid-line",
        }),
      );
      const label = svgElement("text", {
        x: inset.left - 7,
        y: y + 3,
        class: "chart-axis-text",
        "text-anchor": "end",
      });
      label.textContent = step === 0 ? "0" : formatAxis(value);
      grid.append(label);
    }

    grid.append(
      svgElement("line", {
        x1: inset.left,
        x2: width - inset.right,
        y1: yAt(data.capacity),
        y2: yAt(data.capacity),
        class: "chart-capacity-line",
      }),
    );

    const labelStep = Math.max(1, Math.ceil(data.points.length / 6));
    data.labels.forEach((text, index) => {
      if (index % labelStep !== 0 && index !== data.points.length - 1) return;
      const anchor = index === 0 ? "start" : index === data.points.length - 1 ? "end" : "middle";
      const label = svgElement("text", {
        x: xAt(index),
        y: height - 7,
        class: "chart-axis-text",
        "text-anchor": anchor,
      });
      label.textContent = text;
      grid.append(label);
    });
    svg.append(grid);

    const plot = svgElement("g", { "aria-hidden": "true" });
    const points = data.points.map((value, index) => [xAt(index), yAt(value)]);
    const linePath = points
      .map(([x, y], index) => `${index === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`)
      .join(" ");
    const areaPath = `M${points[0][0].toFixed(1)} ${bottom} ${linePath.replace(/^M/, "L")} L${points.at(-1)[0].toFixed(1)} ${bottom} Z`;

    plot.append(svgElement("path", { d: areaPath, class: "chart-area" }));
    plot.append(svgElement("path", { d: linePath, class: "chart-line" }));
    plot.append(
      svgElement("circle", {
        cx: points.at(-1)[0].toFixed(1),
        cy: points.at(-1)[1].toFixed(1),
        r: "3.5",
        class: "chart-marker",
      }),
    );
    svg.append(plot);

    const total = data.points.reduce((sum, value) => sum + value, 0) * 1000;
    const summary = `${formatCompact(total)} requests accepted · ${data.rejected} rejected`;
    chartSummary.textContent = summary;
    chartSub.textContent = data.sub;
    chartTitle.textContent = `Request volume for the last ${data.rangeLabel}`;
    chartDescription.textContent = `Line chart of requests accepted over the last ${data.rangeLabel}. ${summary}. Values are sampled demo traffic.`;
    svg.setAttribute("aria-busy", "false");
  }

  function renderRows() {
    const query = search.value.trim().toLowerCase();
    const filter = statusFilter.value;
    const visible = requests.filter((request) => {
      const matchesQuery =
        !query ||
        request.path.toLowerCase().includes(query) ||
        request.key.toLowerCase().includes(query) ||
        request.region.toLowerCase().includes(query);
      const matchesStatus = filter === "all" || request.tone === filter;
      return matchesQuery && matchesStatus;
    });

    requestsBody.innerHTML = visible
      .map(
        (request) => `
          <tr>
            <td><span class="request-key">${Meridian.escapeHtml(request.key)}</span></td>
            <td><span class="request-path"><span class="request-method">${Meridian.escapeHtml(request.method)}</span>${Meridian.escapeHtml(request.path)}</span></td>
            <td><span class="row-status is-${request.tone}">${request.code} ${statusLabels[request.tone]}</span></td>
            <td class="mono">${Meridian.escapeHtml(request.duration)}</td>
            <td class="mono">${Meridian.escapeHtml(request.region)}</td>
            <td class="mono">${Meridian.escapeHtml(request.when)}</td>
          </tr>`,
      )
      .join("");

    tableEmpty.hidden = visible.length > 0;
    tableCount.textContent = `Showing ${visible.length} of ${requests.length} sampled requests`;
    return visible;
  }

  function skeletonRows() {
    return Array.from({ length: 5 })
      .map(
        () =>
          `<tr aria-hidden="true"><td><span class="skeleton-bar is-short"></span></td><td><span class="skeleton-bar"></span></td><td><span class="skeleton-bar is-short"></span></td><td><span class="skeleton-bar is-short"></span></td><td><span class="skeleton-bar is-short"></span></td><td><span class="skeleton-bar is-short"></span></td></tr>`,
      )
      .join("");
  }

  function setUpdatedNow() {
    const now = new Date();
    const time = now.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
    lastUpdated.textContent = `Updated ${time}`;
  }

  function updateActiveRange(range) {
    activeRange = range;
    for (const button of document.querySelectorAll("[data-range]")) {
      button.setAttribute("aria-pressed", String(button.dataset.range === range));
    }
    renderChart(range);
    Meridian.announce(`Chart range changed to ${traffic[range].rangeLabel}. ${chartSummary.textContent}.`);
  }

  for (const button of document.querySelectorAll("[data-range]")) {
    button.addEventListener("click", () => updateActiveRange(button.dataset.range));
  }

  search.addEventListener("input", renderRows);
  statusFilter.addEventListener("change", renderRows);
  clearFilters.addEventListener("click", () => {
    search.value = "";
    statusFilter.value = "all";
    renderRows();
    search.focus();
    Meridian.announce("Request filters cleared.");
  });

  refresh.addEventListener("click", async () => {
    Meridian.setBusy(refresh, true, "Refreshing…");
    requestsBody.innerHTML = skeletonRows();
    tableEmpty.hidden = true;
    tableCount.textContent = "Refreshing sample requests…";
    requestsBody.closest("table").setAttribute("aria-busy", "true");
    await Meridian.wait(650);
    requestsBody.closest("table").setAttribute("aria-busy", "false");
    Meridian.setBusy(refresh, false);
    renderRows();
    setUpdatedNow();
    Meridian.toast("Sample requests refreshed");
    Meridian.announce(`Sample requests refreshed. ${tableCount.textContent}.`);
  });

  exportButton.addEventListener("click", () => {
    const visible = renderRows();
    if (!visible.length) {
      Meridian.toast("No rows to export", { error: true });
      Meridian.announce("No rows match the current filters. Nothing was exported.");
      return;
    }
    const cells = [
      ["request_key", "method", "route", "status", "duration", "region", "when"],
      ...visible.map((request) => [
        request.key,
        request.method,
        request.path,
        String(request.code),
        request.duration,
        request.region,
        request.when,
      ]),
    ];
    const csv = cells
      .map((row) => row.map((value) => `"${String(value).replace(/"/g, '""')}"`).join(","))
      .join("\n");
    const blob = new Blob([`${csv}\n`], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `meridian-requests-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    Meridian.toast(`Exported ${visible.length} requests`);
    Meridian.announce(`Exported ${visible.length} requests as CSV.`);
  });

  dateNode.dateTime = new Date().toISOString().slice(0, 10);
  dateNode.textContent = Meridian.todayLabel();
  renderChart(activeRange);
  renderRows();
  setUpdatedNow();
})();
