import heapq
from itertools import permutations


# ─── Graph Builder ─────────────────────────────────────────────────────────────

def build_graph(colleges, roads):
    """Build undirected weighted adjacency dict from college + road data."""
    graph = {c: {} for c in colleges}
    for u, v, w in roads:
        graph[u][v] = w
        graph[v][u] = w
    return graph


# ─── Dijkstra's Algorithm ──────────────────────────────────────────────────────

def dijkstra(graph, source):
    dist = {node: float("inf") for node in graph}
    dist[source] = 0
    prev = {}
    pq   = [(0, source)]   # (distance, node)

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:    # stale entry — skip
            continue
        for v, weight in graph[u].items():
            new_dist = d + weight
            if new_dist < dist[v]:
                dist[v] = new_dist
                prev[v] = u
                heapq.heappush(pq, (new_dist, v))

    return dist, prev


def reconstruct_path(prev, source, target):
    """Reconstruct shortest path from prev dict."""
    path = []
    node = target
    while node and node != source:
        path.append(node)
        node = prev.get(node)
    if node == source:
        path.append(source)
    path.reverse()
    return path if path and path[0] == source else []


# ─── Floyd-Warshall Algorithm ──────────────────────────────────────────────────

def floyd_warshall(graph, nodes):
    dist      = {u: {v: float("inf") for v in nodes} for u in nodes}
    next_node = {u: {v: None         for v in nodes} for u in nodes}

    for u in nodes:
        dist[u][u] = 0
        for v, w in graph.get(u, {}).items():
            dist[u][v]      = w
            next_node[u][v] = v

    for k in nodes:
        for u in nodes:
            for v in nodes:
                if dist[u][k] + dist[k][v] < dist[u][v]:
                    dist[u][v]      = dist[u][k] + dist[k][v]
                    next_node[u][v] = next_node[u][k]

    return dist, next_node


# ─── Prim's Minimum Spanning Tree ─────────────────────────────────────────────

def prim_mst(graph, nodes):
    start    = nodes[0]
    visited  = {start}
    mst_edges= []
    total    = 0
    # (weight, from_node, to_node)
    edges = [(w, start, v) for v, w in graph[start].items()]
    heapq.heapify(edges)

    while edges and len(visited) < len(nodes):
        w, u, v = heapq.heappop(edges)
        if v in visited:
            continue
        visited.add(v)
        mst_edges.append((u, v, w))
        total += w
        for nbr, wt in graph[v].items():
            if nbr not in visited:
                heapq.heappush(edges, (wt, v, nbr))

    return mst_edges, round(total, 2)


# ─── Greedy TSP (Nearest Neighbour) ───────────────────────────────────────────

def greedy_tsp(graph, nodes, dist_matrix=None):
    if not nodes:
        return []
    
    # Precompute distances if not provided
    if dist_matrix is None:
        dist_matrix, _ = floyd_warshall(graph, nodes)

    unvisited = set(nodes)
    route     = [nodes[0]]
    unvisited.remove(nodes[0])

    while unvisited:
        current = route[-1]
        nearest = min(unvisited, key=lambda n: dist_matrix[current][n])
        route.append(nearest)
        unvisited.remove(nearest)

    route.append(route[0])  # return to start
    return route


# ─── 2-opt Improvement ────────────────────────────────────────────────────────

def two_opt(graph, route, dist_matrix=None):
    # Precompute distances if not provided
    if dist_matrix is None:
        nodes = list(set(route))
        dist_matrix, _ = floyd_warshall(graph, nodes)
    
    best = route[:]
    improved = True

    while improved:
        improved = False
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                # Cost of current edges
                old = dist_matrix[best[i-1]][best[i]] + \
                      dist_matrix[best[j]][best[j+1]]
                # Cost if we reverse segment [i..j]
                new = dist_matrix[best[i-1]][best[j]] + \
                      dist_matrix[best[i]][best[j+1]]
                if new < old - 1e-9:
                    best[i:j+1] = best[i:j+1][::-1]
                    improved = True

    return best


def route_total_cost(graph, route, dist_matrix=None):
    """Total cost of a TSP route."""
    if dist_matrix is None:
        nodes = list(set(route))
        dist_matrix, _ = floyd_warshall(graph, nodes)
    
    total = 0
    for i in range(len(route) - 1):
        total += dist_matrix[route[i]][route[i+1]]
    return round(total, 2)


# ─── 0/1 Knapsack DP ──────────────────────────────────────────────────────────

def knapsack_events(events, max_budget):
    n  = len(events)
    W  = max_budget
    dp = [[0] * (W + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        w = events[i-1]["budget"]
        v = events[i-1]["value"]
        for cap in range(W + 1):
            if w <= cap:
                dp[i][cap] = max(dp[i-1][cap], dp[i-1][cap-w] + v)
            else:
                dp[i][cap] = dp[i-1][cap]

    # Backtrack to find chosen items
    chosen = []
    cap = W
    for i in range(n, 0, -1):
        if dp[i][cap] != dp[i-1][cap]:
            chosen.append(events[i-1])
            cap -= events[i-1]["budget"]

    total_val  = sum(e["value"]  for e in chosen)
    total_cost = sum(e["budget"] for e in chosen)

    chosen_out = [{"id": e["id"], "name": e["name"],
                   "host": e["host"], "budget": e["budget"],
                   "value": e["value"]} for e in chosen]

    return chosen_out, total_val, total_cost, len(dp)


# ─── Activity Selection (Interval Scheduling) ─────────────────────────────────

def activity_selection(events):
    sorted_events = sorted(events, key=lambda e: e["end"])
    selected  = []
    timeline  = []
    last_end  = -1

    for event in sorted_events:
        if event["start"] >= last_end:
            selected.append(event)
            timeline.append({
                "id":    event["id"],
                "name":  event["name"],
                "host":  event["host"],
                "start": event["start"],
                "end":   event["end"],
                "status":"selected"
            })
            last_end = event["end"]
        else:
            timeline.append({
                "id":    event["id"],
                "name":  event["name"],
                "host":  event["host"],
                "start": event["start"],
                "end":   event["end"],
                "status":"skipped"
            })

    return [{"id": e["id"], "name": e["name"], "host": e["host"],
             "start": e["start"], "end": e["end"]} for e in selected], timeline