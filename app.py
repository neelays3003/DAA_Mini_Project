from flask import Flask, render_template, request, jsonify
import json
from algorithms import (
    dijkstra, floyd_warshall, greedy_tsp, two_opt,
    knapsack_events, activity_selection, build_graph,
    prim_mst
)
from visualizer import draw_graph, draw_route, draw_mst

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

# ---------- Routes ----------

@app.route("/")
def index():
    return render_template("index.html", colleges=COLLEGES, events=EVENTS)

@app.route("/api/shortest_path", methods=["POST"])
def shortest_path():
    data    = request.json
    source  = data.get("source")
    target  = data.get("target")
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
        
        # Precompute distance matrix once
        print(f"[TSP] Computing Floyd-Warshall...")
        dist_matrix, _ = floyd_warshall(graph, colleges)
        
        print(f"[TSP] Running greedy TSP...")
        greedy   = greedy_tsp(graph, colleges, dist_matrix)
        print(f"[TSP] Greedy route: {greedy}")
        
        print(f"[TSP] Running 2-opt optimization...")
        optimized= two_opt(graph, greedy, dist_matrix)
        print(f"[TSP] Optimized route: {optimized}")
        
        gc = route_cost_matrix(greedy, dist_matrix)
        oc = route_cost_matrix(optimized, dist_matrix)
        print(f"[TSP] Greedy cost: {gc}, Optimized cost: {oc}")
        
        print(f"[TSP] Generating visualizations...")
        img_g = draw_route(COLLEGES, ROADS, greedy,     title="Greedy TSP Route",    highlight_color="#e74c3c")
        img_o = draw_route(COLLEGES, ROADS, optimized,  title="Optimized (2-opt) Route", highlight_color="#27ae60")
        print(f"[TSP] Done! Returning response...")
        
        response = {
            "greedy_route": greedy, 
            "greedy_cost": gc,
            "optimized_route": optimized, 
            "optimized_cost": oc,
            "savings": round(gc - oc, 2),
            "image_greedy": img_g, 
            "image_optimized": img_o,
            "complexity": "Greedy: O(n²) | 2-opt: O(n²) per pass"
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

@app.route("/api/mst", methods=["GET"])
def mst():
    mst_edges, total = prim_mst(graph, list(COLLEGES.keys()))
    img = draw_mst(COLLEGES, ROADS, mst_edges, title="Minimum Spanning Tree (Prim's)")
    return jsonify({"mst_edges": mst_edges, "total_cost": total,
                    "image": img, "complexity": "O(E log V)"})

@app.route("/api/knapsack", methods=["POST"])
def knapsack():
    data   = request.json
    budget = int(data.get("budget", 800))
    chosen, total_val, total_cost, dp_table = knapsack_events(EVENTS, budget)
    return jsonify({"chosen_events": chosen, "total_value": total_val,
                    "total_cost": total_cost, "budget": budget,
                    "dp_table_size": f"{len(EVENTS)+1} × {budget+1}",
                    "complexity": "O(n × W)"})

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
