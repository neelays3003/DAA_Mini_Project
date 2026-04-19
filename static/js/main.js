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

  setHTML("tsp-dp-cost",      `${data.dp_cost} km`);
  setHTML("tsp-greedy-cost",  `${data.greedy_cost} km`);
  setHTML("tsp-dp-route",     data.dp_route.join(" → "));
  setHTML("tsp-greedy-route", data.greedy_route.join(" → "));
  setImg("tsp-dp-graph",      data.image_dp);
  setImg("tsp-greedy-graph",  data.image_greedy);

  const gap = Math.max(0, data.greedy_cost - data.dp_cost).toFixed(2);
  const pct = data.dp_cost > 0 ? ((data.greedy_cost - data.dp_cost) / data.dp_cost * 100).toFixed(1) : "0.0";
  setHTML("tsp-savings",
    `🎯 DP found the exact optimum. Greedy is ${gap} km above optimum (${pct}% gap).`);

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

/* ── Knapsack ── */

async function runKnapsackDP() {
  await runKnapsackAlgorithm("/api/knapsack", "ks-dp");
}

async function runKnapsackGreedy() {
  await runKnapsackAlgorithm("/api/knapsack_greedy", "ks-greedy");
}

async function runKnapsackBB() {
  await runKnapsackAlgorithm("/api/knapsack_bb", "ks-bb");
}

async function runKnapsackBacktrack() {
  await runKnapsackAlgorithm("/api/knapsack_backtrack", "ks-backtrack");
}

async function runKnapsackAlgorithm(endpoint, cardId) {
  const budget = document.getElementById("budget-slider").value;
  show("knapsack-loader");

  try {
    const data = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ budget: parseInt(budget) })
    }).then(r => r.json());
    hide("knapsack-loader");

    // Show the result area
    if (document.getElementById("knapsack-result").classList.contains("hidden")) {
      show("knapsack-result");
    }

    // Show the specific card
    document.getElementById(cardId).style.display = "block";

    // Fill statistics
    const statsId = cardId + "-stats";
    setHTML(statsId,
      statCard("Budget", `₹${data.budget}`, "blue") +
      statCard("Spent", `₹${data.total_cost}`, "red") +
      statCard("Remaining", `₹${data.budget - data.total_cost}`, "green") +
      statCard("Total Value", data.total_value, "purple") +
      statCard("Events", data.chosen_events.length, "blue")
    );

    // Fill events table
    let table = `<table class="data-table"><thead>
      <tr><th>#</th><th>Event</th><th>Host</th><th>Budget</th><th>Value</th></tr>
    </thead><tbody>`;
    if (data.chosen_events.length === 0) {
      table += `<tr><td colspan="5" style="text-align:center">No events selected</td></tr>`;
    } else {
      data.chosen_events.forEach((e, i) => {
        table += `<tr>
          <td>${i+1}</td>
          <td><strong>${e.name}</strong></td>
          <td><span class="node-pill">${e.host}</span></td>
          <td>₹${e.budget}</td>
          <td><span class="val-bar"><span style="width:${e.value}%"></span></span> ${e.value}</td>
        </tr>`;
      });
    }
    table += `</tbody></table>`;
    setHTML(cardId + "-table", table);

    // Fill complexity
    setHTML(cardId + "-complexity",
      `⏱ Time Complexity: ${data.complexity} | Algorithm: ${data.algorithm}`);

    // Update comparison
    updateKnapsackComparison();
  } catch (error) {
    hide("knapsack-loader");
    alert("Error: " + error.message);
  }
}

function updateKnapsackComparison() {
  // Find all visible cards and their values
  const cards = ["ks-dp", "ks-greedy", "ks-bb", "ks-backtrack"];
  const results = {};

  cards.forEach(cardId => {
    const card = document.getElementById(cardId);
    if (card.style.display !== "none") {
      const valueText = card.querySelector(".stat-value:nth-child(4)")?.textContent || "0";
      results[cardId] = parseInt(valueText) || 0;
    }
  });

  // Find best and worst
  const values = Object.values(results);
  if (values.length > 0) {
    const maxValue = Math.max(...values);
    const minValue = Math.min(...values);
    
    let comparison = `<div style="background:#f0f8ff;padding:15px;border-radius:8px">
      <h4>Algorithm Comparison:</h4>
      <ul style="list-style:none;padding:0">`;
    
    Object.entries(results).forEach(([cardId, value]) => {
      const label = cardId.replace("ks-", "").toUpperCase();
      let status = "";
      if (value === maxValue && maxValue > minValue) {
        status = " ✓ Best value";
      } else if (value === minValue && maxValue > minValue) {
        status = " (suboptimal)";
      }
      comparison += `<li>• ${label}: ₹${value}${status}</li>`;
    });
    
    comparison += `</ul></div>`;
    setHTML("ks-comparison", comparison);
  }
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
