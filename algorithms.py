import heapq
from itertools import combinations


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
    pq   = [(0, source)]   

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:    
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


def route_total_cost(graph, route, dist_matrix=None):
    """Total cost of a TSP route."""
    if dist_matrix is None:
        nodes = list(set(route))
        dist_matrix, _ = floyd_warshall(graph, nodes)
    
    total = 0
    for i in range(len(route) - 1):
        total += dist_matrix[route[i]][route[i+1]]
    return round(total, 2)


# ─── TSP via Dynamic Programming (Held-Karp) ─────────────────────────────────

def tsp_dp(graph, nodes, dist_matrix=None):
    """Return an optimal TSP route using Held-Karp dynamic programming."""
    if not nodes:
        return [], 0

    if len(nodes) == 1:
        return [nodes[0], nodes[0]], 0

    if dist_matrix is None:
        dist_matrix, _ = floyd_warshall(graph, nodes)

    start = nodes[0]
    others = nodes[1:]
    index = {node: i for i, node in enumerate(others)}

    # dp[(mask, end)] = (cost, previous_node)
    dp = {}
    for node in others:
        mask = 1 << index[node]
        dp[(mask, node)] = (dist_matrix[start][node], start)

    for subset_size in range(2, len(others) + 1):
        for subset in combinations(others, subset_size):
            mask = 0
            for node in subset:
                mask |= 1 << index[node]

            for end in subset:
                end_mask = mask ^ (1 << index[end])
                best_cost = float("inf")
                best_prev = None

                for prev in subset:
                    if prev == end:
                        continue
                    prev_state = dp.get((end_mask, prev))
                    if prev_state is None:
                        continue
                    cost = prev_state[0] + dist_matrix[prev][end]
                    if cost < best_cost:
                        best_cost = cost
                        best_prev = prev

                if best_prev is not None:
                    dp[(mask, end)] = (best_cost, best_prev)

    full_mask = (1 << len(others)) - 1
    best_cost = float("inf")
    best_end = None

    for end in others:
        state = dp.get((full_mask, end))
        if state is None:
            continue
        cost = state[0] + dist_matrix[end][start]
        if cost < best_cost:
            best_cost = cost
            best_end = end

    if best_end is None:
        return [], float("inf")

    route = [start]
    mask = full_mask
    end = best_end
    stack = [end]

    while True:
        state = dp[(mask, end)]
        prev = state[1]
        mask ^= 1 << index[end]
        if prev == start:
            break
        stack.append(prev)
        end = prev

    route.extend(reversed(stack))
    route.append(start)
    return route, round(best_cost, 2)


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


# ─── Greedy Budget Optimization (Value/Cost Ratio) ────────────────────────────

def greedy_budget(events, max_budget):
    """Select events greedily by highest value/cost ratio"""
    # Calculate ratio for each event
    events_with_ratio = []
    for e in events:
        ratio = e["value"] / e["budget"] if e["budget"] > 0 else 0
        events_with_ratio.append((ratio, e))
    
    # Sort by ratio descending
    events_with_ratio.sort(reverse=True, key=lambda x: x[0])
    
    # Greedily pick events
    chosen = []
    total_cost = 0
    for ratio, event in events_with_ratio:
        if total_cost + event["budget"] <= max_budget:
            chosen.append(event)
            total_cost += event["budget"]
    
    total_val = sum(e["value"] for e in chosen)
    chosen_out = [{"id": e["id"], "name": e["name"],
                   "host": e["host"], "budget": e["budget"],
                   "value": e["value"], "ratio": round(e["value"]/e["budget"], 3)}
                  for e in chosen]
    
    return chosen_out, total_val, total_cost


# ─── Branch and Bound Knapsack ────────────────────────────────────────────────

def branch_and_bound_knapsack(events, max_budget):
    """Exact algorithm with pruning using upper bound (fractional knapsack)"""
    n = len(events)
    best_value = [0]
    best_selection = []
    
    # Sort by value/cost ratio for better pruning
    events_sorted = sorted(events, 
                          key=lambda e: e["value"]/e["budget"], 
                          reverse=True)
    
    def get_upper_bound(idx, remaining_budget, current_value):
        """Calculate upper bound using fractional knapsack on remaining items"""
        bound = current_value
        temp_budget = remaining_budget
        
        for i in range(idx, n):
            if temp_budget <= 0:
                break
            if events_sorted[i]["budget"] <= temp_budget:
                bound += events_sorted[i]["value"]
                temp_budget -= events_sorted[i]["budget"]
            else:
                # Take fraction of next item
                fraction = temp_budget / events_sorted[i]["budget"]
                bound += fraction * events_sorted[i]["value"]
                break
        
        return bound
    
    def branch_bound(idx, current_cost, current_value, selected):
        """Recursively explore with pruning"""
        if idx == n:
            if current_value > best_value[0]:
                best_value[0] = current_value
                best_selection[:] = selected[:]
            return
        
        # Pruning: if upper bound can't beat best, skip
        upper_bound = get_upper_bound(idx, max_budget - current_cost, current_value)
        if upper_bound <= best_value[0]:
            return
        
        # Try including event idx
        if current_cost + events_sorted[idx]["budget"] <= max_budget:
            selected.append(events_sorted[idx])
            branch_bound(idx + 1, 
                        current_cost + events_sorted[idx]["budget"],
                        current_value + events_sorted[idx]["value"],
                        selected)
            selected.pop()
        
        # Try excluding event idx
        branch_bound(idx + 1, current_cost, current_value, selected)
    
    branch_bound(0, 0, 0, [])
    
    # Format output
    total_cost = sum(e["budget"] for e in best_selection)
    chosen_out = [{"id": e["id"], "name": e["name"],
                   "host": e["host"], "budget": e["budget"],
                   "value": e["value"]} for e in best_selection]
    
    return chosen_out, best_value[0], total_cost


# ─── Backtracking Knapsack (Simple) ───────────────────────────────────────────

def backtrack_knapsack(events, max_budget):
    """Exact algorithm using simple backtracking (no upper bound)"""
    n = len(events)
    best_value = [0]
    best_selection = []
    
    def backtrack(idx, current_cost, current_value, selected):
        """Recursively try including/excluding each event"""
        
        # Pruning: if cost exceeds budget, stop exploring
        if current_cost > max_budget:
            return
        
        # Base case: all events considered
        if idx == n:
            if current_value > best_value[0]:
                best_value[0] = current_value
                best_selection[:] = selected[:]
            return
        
        # Try including event idx
        if current_cost + events[idx]["budget"] <= max_budget:
            selected.append(events[idx])
            backtrack(idx + 1,
                     current_cost + events[idx]["budget"],
                     current_value + events[idx]["value"],
                     selected)
            selected.pop()
        
        # Try excluding event idx
        backtrack(idx + 1, current_cost, current_value, selected)
    
    backtrack(0, 0, 0, [])
    
    # Format output
    total_cost = sum(e["budget"] for e in best_selection)
    chosen_out = [{"id": e["id"], "name": e["name"],
                   "host": e["host"], "budget": e["budget"],
                   "value": e["value"]} for e in best_selection]
    
    return chosen_out, best_value[0], total_cost


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