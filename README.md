# Inter-College Event Travel Optimizer
### Design & Analysis of Algorithms — Mini Project

---

## Features
| Feature | Algorithm | Complexity |
|---|---|---|
| Shortest path between colleges | Dijkstra's Algorithm | O((V+E) log V) |
| Visit all colleges optimally | TSP: Greedy + 2-opt | O(n²) |
| All-pairs distance matrix | Floyd-Warshall | O(V³) |
| Minimum road network | Prim's MST | O(E log V) |
| Best events within budget | 0/1 Knapsack DP | O(n × W) |
| Non-overlapping event schedule | Activity Selection | O(n log n) |

---

## Project Structure
```
travel_optimizer/
├── app.py              ← Flask web server + API routes
├── algorithms.py       ← All DAA algorithms (pure Python)
├── visualizer.py       ← Graph visualization (matplotlib)
├── requirements.txt    ← Python dependencies
├── templates/
│   └── index.html      ← Main webpage
└── static/
    ├── css/style.css   ← Stylesheet
    └── js/main.js      ← Frontend logic
```

---

## Setup & Run

### Step 1: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the app
```bash
python app.py
```

### Step 3: Open in browser
```
http://127.0.0.1:5000
```

---

## Algorithms Explained

### 1. Dijkstra's Algorithm
- **Purpose**: Find shortest path between two colleges
- **Data Structure**: Min-heap (priority queue)
- **Time**: O((V + E) log V) | **Space**: O(V)

### 2. Floyd-Warshall
- **Purpose**: All-pairs shortest paths (full distance matrix)
- **Time**: O(V³) | **Space**: O(V²)

### 3. Prim's MST
- **Purpose**: Minimum spanning tree — minimum cost to connect all colleges
- **Time**: O(E log V) | **Space**: O(V + E)

### 4. Greedy TSP + 2-opt
- **Purpose**: Find near-optimal tour visiting all colleges
- **Greedy**: O(n²) — nearest neighbour heuristic
- **2-opt**: O(n²) per pass — local search improvement

### 5. 0/1 Knapsack (DP)
- **Purpose**: Select events with max value within budget
- **Time**: O(n × W) | **Space**: O(n × W)
- **Recurrence**: dp[i][w] = max(dp[i-1][w], dp[i-1][w-wt] + val)

### 6. Activity Selection (Greedy)
- **Purpose**: Schedule max non-overlapping events
- **Time**: O(n log n) | Sorted by finish time

---

## Viva Tips
- Be ready to explain the **recurrence relation** for Knapsack
- Know why TSP is **NP-Hard** and why we use heuristics
- Explain the difference between **Dijkstra** (single source) and **Floyd-Warshall** (all pairs)
- Explain **2-opt** as a local search that swaps edges to reduce tour length
