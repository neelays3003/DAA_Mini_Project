from flask import Flask, render_template, request, jsonify
import json
from algorithms import (
    dijkstra, floyd_warshall, greedy_tsp, tsp_dp,
    knapsack_events, activity_selection, build_graph,
    greedy_budget, branch_and_bound_knapsack, backtrack_knapsack
)
from visualizer import draw_graph, draw_route

app = Flask(__name__)

# ---------- Sample Data ----------
COLLEGES = {
    "A": {"name": "Alpha College",   "x": 100, "y": 300},
    "B": {"name": "Beta Institute",  "x": 250, "y": 150},
    "C": {"name": "Gamma University","x": 400, "y": 300},
    "D": {"name": "Delta College",   "x": 250, "y": 450},
    "E": {"name": "Epsilon Tech",    "x": 550, "y": 150},
    "F": {"name": "Zeta College",    "x": 550, "y": 450},
}

ROADS = [
    ("A","B", 60),  ("A","D", 50),  ("B","C", 70),
    ("B","E", 90),  ("C","D", 80),  ("C","E", 40),
    ("C","F", 60),  ("D","F", 100), ("E","F", 55),
    ("B","D", 110), ("A","C", 130),
]

EVENTS = [
    {"id":1,"name":"Tech Fest",     "host":"E","budget":500,"duration":3,"start":9, "end":12,"value":90},
    {"id":2,"name":"Cultural Night","host":"B","budget":300,"duration":2,"start":14,"end":16,"value":70},
    {"id":3,"name":"Sports Meet",   "host":"D","budget":200,"duration":4,"start":8, "end":12,"value":60},
    {"id":4,"name":"Hackathon",     "host":"C","budget":400,"duration":5,"start":10,"end":15,"value":85},
    {"id":5,"name":"Quiz Bowl",     "host":"F","budget":150,"duration":2,"start":13,"end":15,"value":50},
    {"id":6,"name":"Art Expo",      "host":"A","budget":250,"duration":3,"start":11,"end":14,"value":65},
]

graph = build_graph(COLLEGES, ROADS)


def rebuild_graph():
    return build_graph(COLLEGES, ROADS)


def normalize_colleges(payload):
    if not isinstance(payload, dict) or not payload:
        raise ValueError("Colleges must be a non-empty JSON object.")

    normalized = {}
    codes = list(payload.keys())
    positioned = 0

    for index, (code, value) in enumerate(payload.items()):
        code = str(code).strip()
        if not code:
            raise ValueError("College codes cannot be empty.")

        if isinstance(value, str):
            name = value.strip()
            x = y = None
        elif isinstance(value, dict):
            name = str(value.get("name", "")).strip()
            x = value.get("x")
            y = value.get("y")
        else:
            raise ValueError(f"Invalid college entry for {code}.")

        if not name:
            raise ValueError(f"College name is required for {code}.")

        if x is not None and y is not None:
            try:
                x = int(x)
                y = int(y)
                positioned += 1
            except (TypeError, ValueError):
                raise ValueError(f"College coordinates for {code} must be numbers.")

        normalized[code] = {"name": name, "x": x, "y": y}

    if positioned == 0:
        from math import cos, sin, tau

        center_x, center_y = 350, 300
        radius = max(140, 40 * len(normalized))
        for index, code in enumerate(codes):
            angle = tau * index / max(len(codes), 1)
            normalized[code]["x"] = round(center_x + radius * cos(angle))
            normalized[code]["y"] = round(center_y + radius * sin(angle))
    else:
        missing = [code for code, value in normalized.items() if value.get("x") is None or value.get("y") is None]
        if missing:
            from math import cos, sin, tau

            center_x, center_y = 350, 300
            radius = max(140, 40 * len(missing))
            for index, code in enumerate(missing):
                angle = tau * index / max(len(missing), 1)
                normalized[code]["x"] = round(center_x + radius * cos(angle))
                normalized[code]["y"] = round(center_y + radius * sin(angle))

    return normalized


def normalize_roads(payload, colleges):
    if not isinstance(payload, list):
        raise ValueError("Roads must be a JSON array.")

    normalized = []
    for index, item in enumerate(payload, start=1):
        if isinstance(item, dict):
            u = str(item.get("from", "")).strip()
            v = str(item.get("to", "")).strip()
            w = item.get("weight")
        elif isinstance(item, (list, tuple)) and len(item) == 3:
            u, v, w = item
            u = str(u).strip()
            v = str(v).strip()
        else:
            raise ValueError(f"Road #{index} must be either [from, to, weight] or an object.")

        if u not in colleges or v not in colleges:
            raise ValueError(f"Road #{index} references an unknown college.")

        try:
            w = float(w)
        except (TypeError, ValueError):
            raise ValueError(f"Road #{index} weight must be numeric.")

        if w <= 0:
            raise ValueError(f"Road #{index} weight must be greater than zero.")

        normalized.append((u, v, w))

    return normalized


def normalize_events(payload, colleges):
    if not isinstance(payload, list):
        raise ValueError("Events must be a JSON array.")

    required_fields = ["name", "host", "budget", "duration", "start", "end", "value"]
    normalized = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Event #{index} must be an object.")

        event = {}
        for field in required_fields:
            if field not in item:
                raise ValueError(f"Event #{index} is missing '{field}'.")
            event[field] = item[field]

        event["name"] = str(event["name"]).strip()
        event["host"] = str(event["host"]).strip()
        if not event["name"]:
            raise ValueError(f"Event #{index} name cannot be empty.")
        if event["host"] not in colleges:
            raise ValueError(f"Event #{index} host must match a college code.")

        try:
            event["budget"] = int(event["budget"])
            event["duration"] = int(event["duration"])
            event["start"] = int(event["start"])
            event["end"] = int(event["end"])
            event["value"] = int(event["value"])
        except (TypeError, ValueError):
            raise ValueError(f"Event #{index} budget, duration, start, end, and value must be integers.")

        normalized.append({
            "id": item.get("id", index),
            "name": event["name"],
            "host": event["host"],
            "budget": event["budget"],
            "duration": event["duration"],
            "start": event["start"],
            "end": event["end"],
            "value": event["value"],
        })

    return normalized

# ---------- Routes ----------

@app.route("/")
def index():
    return render_template("index.html", colleges=COLLEGES, roads=ROADS, events=EVENTS)


@app.route("/api/custom_dataset", methods=["POST"])
def custom_dataset():
    global COLLEGES, ROADS, EVENTS, graph

    data = request.get_json(silent=True) or {}

    try:
        colleges = normalize_colleges(data.get("colleges"))
        roads = normalize_roads(data.get("roads"), colleges)
        events = normalize_events(data.get("events"), colleges)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    COLLEGES = colleges
    ROADS = roads
    EVENTS = events
    graph = rebuild_graph()

    return jsonify({
        "message": "Custom dataset applied successfully.",
        "college_count": len(COLLEGES),
        "road_count": len(ROADS),
        "event_count": len(EVENTS),
    })

@app.route("/api/shortest_path", methods=["POST"])
def shortest_path():
    data    = request.json
    source  = str(data.get("source", "")).strip().upper()
    target  = str(data.get("target", "")).strip().upper()

    if source not in COLLEGES or target not in COLLEGES:
        return jsonify({"error": "Please select valid colleges."}), 400

    if source == target:
        return jsonify({"error": "Source and destination must be different."}), 400

    dist, prev = dijkstra(graph, source)
    if target not in dist:
        return jsonify({"error": "No path found"}), 400
    path, cost = [], dist[target]
    node = target
    while node:
        path.append(node)
        node = prev.get(node)
    path.reverse()
    steps = get_dijkstra_steps(graph, source, target)
    img   = draw_route(COLLEGES, ROADS, path, title=f"Shortest Path: {source} → {target}")
    return jsonify({"path": path, "cost": cost, "image": img,
                    "steps": steps, "complexity": "O((V+E) log V)"})

@app.route("/api/tsp", methods=["POST"])
def tsp_route():
    try:
        data     = request.json
        colleges = data.get("colleges", list(COLLEGES.keys()))
        print(f"[TSP] Starting with colleges: {colleges}")

        selected = [c for c in colleges if c in COLLEGES]
        if len(selected) < 2:
            return jsonify({"error": "Select at least 2 colleges for TSP."}), 400

        # Precompute on the full graph so shortest paths can pass through intermediate colleges.
        print(f"[TSP] Computing Floyd-Warshall on full graph...")
        all_nodes = list(COLLEGES.keys())
        dist_matrix, next_node = floyd_warshall(graph, all_nodes)

        print(f"[TSP] Running dynamic programming TSP...")
        dp_route, dp_cost = tsp_dp(graph, selected, dist_matrix)
        print(f"[TSP] DP route: {dp_route}")
        print(f"[TSP] DP cost: {dp_cost}")
        
        print(f"[TSP] Running greedy TSP...")
        greedy   = greedy_tsp(graph, selected, dist_matrix, start_node=selected[0])
        print(f"[TSP] Greedy route: {greedy}")
        gc = route_cost_matrix(greedy, dist_matrix)
        print(f"[TSP] Greedy cost: {gc}")

        dp_full_route = expand_route(dp_route, next_node)
        greedy_full_route = expand_route(greedy, next_node)
        
        print(f"[TSP] Generating visualizations...")
        img_dp = draw_route(COLLEGES, ROADS, dp_full_route, title="DP TSP Route", highlight_color="#8e44ad")
        img_g = draw_route(COLLEGES, ROADS, greedy_full_route, title="Greedy TSP Route", highlight_color="#e74c3c")
        print(f"[TSP] Done! Returning response...")
        
        response = {
            "dp_route": dp_route,
            "dp_cost": dp_cost,
            "dp_full_route": dp_full_route,
            "image_dp": img_dp,
            "greedy_route": greedy, 
            "greedy_cost": gc,
            "greedy_full_route": greedy_full_route,
            "image_greedy": img_g, 
            "complexity": "DP: O(n²·2ⁿ) | Greedy: O(n²)"
        }
        print(f"[TSP] Response keys: {response.keys()}")
        return jsonify(response)
    except Exception as e:
        print(f"[TSP] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/floyd_warshall", methods=["GET"])
def all_pairs():
    nodes = list(COLLEGES.keys())
    dist_matrix, _ = floyd_warshall(graph, nodes)
    table = []
    for u in nodes:
        row = {"from": u, "name": COLLEGES[u]["name"]}
        for v in nodes:
            val = dist_matrix[u][v]
            row[v] = round(val, 1) if val < float("inf") else "∞"
        table.append(row)
    img = draw_graph(COLLEGES, ROADS, title="All Colleges — Road Network")
    return jsonify({"table": table, "nodes": nodes, "image": img,
                    "complexity": "O(V³)"})

@app.route("/api/knapsack", methods=["POST"])
def knapsack():
    data   = request.json
    budget = int(data.get("budget", 800))
    chosen, total_val, total_cost, dp_table = knapsack_events(EVENTS, budget)
    return jsonify({"chosen_events": chosen, "total_value": total_val,
                    "total_cost": total_cost, "budget": budget,
                    "dp_table_size": f"{len(EVENTS)+1} × {budget+1}",
                    "complexity": "O(n × W)",
                    "algorithm": "Dynamic Programming"})

@app.route("/api/knapsack_greedy", methods=["POST"])
def knapsack_greedy():
    data   = request.json
    budget = int(data.get("budget", 800))
    chosen, total_val, total_cost = greedy_budget(EVENTS, budget)
    return jsonify({"chosen_events": chosen, "total_value": total_val,
                    "total_cost": total_cost, "budget": budget,
                    "complexity": "O(n log n)",
                    "algorithm": "Greedy (Value/Cost Ratio)"})

@app.route("/api/knapsack_bb", methods=["POST"])
def knapsack_bb():
    data   = request.json
    budget = int(data.get("budget", 800))
    chosen, total_val, total_cost = branch_and_bound_knapsack(EVENTS, budget)
    return jsonify({"chosen_events": chosen, "total_value": total_val,
                    "total_cost": total_cost, "budget": budget,
                    "complexity": "O(2^n) with pruning",
                    "algorithm": "Branch and Bound"})

@app.route("/api/knapsack_backtrack", methods=["POST"])
def knapsack_backtrack():
    data   = request.json
    budget = int(data.get("budget", 800))
    chosen, total_val, total_cost = backtrack_knapsack(EVENTS, budget)
    return jsonify({"chosen_events": chosen, "total_value": total_val,
                    "total_cost": total_cost, "budget": budget,
                    "complexity": "O(2^n)",
                    "algorithm": "Backtracking"})

@app.route("/api/schedule", methods=["POST"])
def schedule():
    data   = request.json
    chosen = data.get("event_ids", [e["id"] for e in EVENTS])
    evts   = [e for e in EVENTS if e["id"] in chosen]
    selected, timeline = activity_selection(evts)
    return jsonify({"selected": selected, "timeline": timeline,
                    "total_selected": len(selected),
                    "complexity": "O(n log n)"})

@app.route("/api/graph_data", methods=["GET"])
def graph_data():
    img = draw_graph(COLLEGES, ROADS, title="College Road Network")
    return jsonify({"image": img})

# ---------- Helpers ----------

def route_cost(g, route):
    cost = 0
    for i in range(len(route)-1):
        u, v = route[i], route[i+1]
        cost += g.get(u, {}).get(v, float("inf"))
    return round(cost, 2)

def route_cost_matrix(route, dist_matrix):
    """Calculate route cost using precomputed distance matrix."""
    cost = 0
    for i in range(len(route)-1):
        u, v = route[i], route[i+1]
        cost += dist_matrix[u][v]
    return round(cost, 2)


def expand_route(route, next_node):
    """Expand a terminal route into the underlying shortest-path walk."""
    if not route:
        return []

    expanded = [route[0]]
    for i in range(len(route) - 1):
        u, v = route[i], route[i + 1]
        if u == v:
            continue

        if next_node.get(u, {}).get(v) is None:
            expanded.append(v)
            continue

        current = u
        while current != v:
            current = next_node[current][v]
            if current is None:
                break
            expanded.append(current)

    return expanded

def get_dijkstra_steps(g, source, target):
    import heapq
    dist  = {n: float("inf") for n in g}
    dist[source] = 0
    prev  = {}
    pq    = [(0, source)]
    steps = []
    visited = set()
    while pq:
        d, u = heapq.heappop(pq)
        if u in visited: continue
        visited.add(u)
        steps.append({"visit": u, "dist": round(d,1),
                      "distances": {k: round(v,1) if v<float("inf") else "∞"
                                    for k,v in dist.items()}})
        if u == target: break
        for v, w in g.get(u, {}).items():
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    return steps

if __name__ == "__main__":
    app.run(debug=True)
