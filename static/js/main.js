/* main.js — Inter-College Travel Optimizer Frontend Logic */

/* ── Tab Switching ── */
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
  });
});

/* ── Load overview graph on start ── */
window.addEventListener("load", () => {
  fetch("/api/graph_data")
    .then(r => r.json())
    .then(d => {
      const box = document.getElementById("overview-graph");
      document.getElementById("overview-loader").remove();
      box.innerHTML = `<img src="data:image/png;base64,${d.image}" alt="College Network"/>`;
    });
});

/* ── Helpers ── */
function show(id)   { document.getElementById(id).classList.remove("hidden"); }
function hide(id)   { document.getElementById(id).classList.add("hidden"); }
function setHTML(id, html) { document.getElementById(id).innerHTML = html; }

function statCard(label, value, color="blue") {
  return `<div class="stat-card ${color}">
    <div class="stat-label">${label}</div>
    <div class="stat-value">${value}</div>
  </div>`;
}

function setImg(id, b64) {
  document.getElementById(id).innerHTML =
    `<img src="data:image/png;base64,${b64}" alt="Graph"/>`;
}

/* ── Dijkstra ── */
async function runDijkstra() {
  const source = document.getElementById("sp-source").value;
  const target = document.getElementById("sp-target").value;
  if (source === target) { alert("Source and target must be different."); return; }

  hide("sp-result");
  show("sp-loader");

  const res  = await fetch("/api/shortest_path", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source, target })
  });
  const data = await res.json();
  hide("sp-loader");

  if (data.error) { alert(data.error); return; }

  setHTML("sp-stats",
    statCard("Source", source, "blue") +
    statCard("Destination", target, "blue") +
    statCard("Shortest Distance", `${data.cost} km`, "green") +
    statCard("Hops", data.path.length - 1, "red")
  );

  setImg("sp-graph", data.image);

  const stepsHTML = data.steps.map((s, i) =>
    `<div class="step-item">
      <div class="step-num">${i+1}</div>
      <div>Visiting <strong>${s.visit}</strong> — dist so far: <strong>${s.dist} km</strong></div>
    </div>`
  ).join("");
  setHTML("sp-steps", stepsHTML);

  setHTML("sp-complexity", `⏱ Time Complexity: ${data.complexity}`);
  show("sp-result");
}

/* ── TSP ── */
async function runTSP() {
  const checked = [...document.querySelectorAll("#tsp-checkboxes input:checked")]
    .map(cb => cb.value);
  if (checked.length < 3) { alert("Select at least 3 colleges for TSP."); return; }

  hide("tsp-result");
  show("tsp-loader");

  const res  = await fetch("/api/tsp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ colleges: checked })
  });
  const data = await res.json();
  hide("tsp-loader");

  setHTML("tsp-greedy-cost",  `${data.greedy_cost} km`);
  setHTML("tsp-opt-cost",     `${data.optimized_cost} km`);
  setHTML("tsp-greedy-route", data.greedy_route.join(" → "));
  setHTML("tsp-opt-route",    data.optimized_route.join(" → "));
  setImg("tsp-greedy-graph",  data.image_greedy);
  setImg("tsp-opt-graph",     data.image_optimized);

  const pct = ((data.savings / data.greedy_cost) * 100).toFixed(1);
  setHTML("tsp-savings",
    `🎯 2-opt saved ${data.savings} km (${pct}% improvement over greedy)`);

  setHTML("tsp-complexity", `⏱ Time Complexity: ${data.complexity}`);
  show("tsp-result");
}

/* ── Floyd-Warshall ── */
async function runFloyd() {
  hide("floyd-result");
  show("floyd-loader");

  const data = await fetch("/api/floyd_warshall").then(r => r.json());
  hide("floyd-loader");

  setImg("floyd-graph", data.image);

  const nodes = data.nodes;
  let th = `<table class="data-table"><thead><tr><th>From \\ To</th>`;
  nodes.forEach(n => th += `<th>${n}</th>`);
  th += `</tr></thead><tbody>`;
  data.table.forEach(row => {
    th += `<tr><td><strong>${row.from}</strong></td>`;
    nodes.forEach(n => {
      const v = row[n];
      const cls = v === "∞" ? "color:#ccc" : v === 0 ? "color:#3498db;font-weight:700" : "";
      th += `<td style="${cls}">${v}</td>`;
    });
    th += `</tr>`;
  });
  th += `</tbody></table>`;
  setHTML("floyd-table", th);

  setHTML("floyd-complexity", `⏱ Time Complexity: ${data.complexity}`);
  show("floyd-result");
}

/* ── MST ── */
async function runMST() {
  hide("mst-result");
  show("mst-loader");

  const data = await fetch("/api/mst").then(r => r.json());
  hide("mst-loader");

  setImg("mst-graph", data.image);

  let table = `<table class="data-table"><thead>
    <tr><th>#</th><th>From</th><th>To</th><th>Cost (km)</th></tr>
  </thead><tbody>`;
  data.mst_edges.forEach(([u, v, w], i) => {
    table += `<tr><td>${i+1}</td><td><span class="node-pill">${u}</span></td>
      <td><span class="node-pill">${v}</span></td><td>${w} km</td></tr>`;
  });
  table += `<tr><td colspan="3"><strong>Total MST Cost</strong></td>
    <td><strong>${data.total_cost} km</strong></td></tr>`;
  table += `</tbody></table>`;
  setHTML("mst-table", table);

  setHTML("mst-complexity", `⏱ Time Complexity: ${data.complexity}`);
  show("mst-result");
}

/* ── Knapsack ── */
async function runKnapsack() {
  const budget = document.getElementById("budget-slider").value;
  hide("knapsack-result");
  show("knapsack-loader");

  const data = await fetch("/api/knapsack", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ budget: parseInt(budget) })
  }).then(r => r.json());
  hide("knapsack-loader");

  setHTML("ks-stats",
    statCard("Budget", `₹${data.budget}`, "blue") +
    statCard("Spent", `₹${data.total_cost}`, "red") +
    statCard("Remaining", `₹${data.budget - data.total_cost}`, "green") +
    statCard("Total Value", data.total_value, "purple") +
    statCard("Events Chosen", data.chosen_events.length, "blue")
  );

  let table = `<table class="data-table"><thead>
    <tr><th>#</th><th>Event</th><th>Host</th><th>Budget</th><th>Value</th></tr>
  </thead><tbody>`;
  data.chosen_events.forEach((e, i) => {
    table += `<tr>
      <td>${i+1}</td>
      <td><strong>${e.name}</strong></td>
      <td><span class="node-pill">${e.host}</span></td>
      <td>₹${e.budget}</td>
      <td><span class="val-bar"><span style="width:${e.value}%"></span></span> ${e.value}</td>
    </tr>`;
  });
  table += `</tbody></table>`;
  setHTML("ks-table", table);

  setHTML("ks-complexity",
    `⏱ Time Complexity: ${data.complexity} | DP Table: ${data.dp_table_size}`);
  show("knapsack-result");
}

/* ── Activity Selection / Scheduler ── */
async function runSchedule() {
  hide("schedule-result");
  show("schedule-loader");

  const data = await fetch("/api/schedule", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({})
  }).then(r => r.json());
  hide("schedule-loader");

  const sel = data.selected.length;
  const tot = data.timeline.length;
  setHTML("sched-stats",
    statCard("Events Selected", sel, "green") +
    statCard("Events Skipped", tot - sel, "red") +
    statCard("Total Events", tot, "blue")
  );

  // Build timeline (hours 8–16)
  const START_HOUR = 8, END_HOUR = 16, SPAN = END_HOUR - START_HOUR;
  let ruler = `<div class="timeline-ruler">`;
  for (let h = START_HOUR; h <= END_HOUR; h++) {
    ruler += `<span>${h}:00</span>`;
  }
  ruler += `</div>`;

  let bars = "";
  data.timeline.forEach(ev => {
    const leftPct  = ((ev.start - START_HOUR) / SPAN * 100).toFixed(1);
    const widthPct = ((ev.end   - ev.start)   / SPAN * 100).toFixed(1);
    bars += `<div class="timeline-bar">
      <div class="timeline-label">${ev.name}</div>
      <div class="timeline-track">
        <div class="timeline-seg ${ev.status}"
             style="left:${leftPct}%;width:${widthPct}%">
          ${ev.status === "selected" ? "✓" : "✗"}
        </div>
      </div>
    </div>`;
  });

  setHTML("sched-timeline", ruler + bars);
  setHTML("sched-complexity", `⏱ Time Complexity: O(n log n) — sorted by finish time`);
  show("schedule-result");
}
