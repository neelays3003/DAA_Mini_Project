import io, base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx


# ─── Shared Helpers ────────────────────────────────────────────────────────────

def _college_positions(colleges):
    """Convert college data to networkx-compatible pos dict (scaled)."""
    return {c: (d["x"], -d["y"]) for c, d in colleges.items()}


def _build_nx_graph(colleges, roads):
    G   = nx.Graph()
    pos = _college_positions(colleges)
    for c in colleges:
        G.add_node(c, label=colleges[c]["name"])
    for u, v, w in roads:
        G.add_edge(u, v, weight=w)
    return G, pos


def _fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return b64


def _style_ax(ax, title):
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12, color="#2c3e50")
    ax.set_facecolor("#f8f9fa")
    ax.axis("off")


# ─── Base Graph ────────────────────────────────────────────────────────────────

def draw_graph(colleges, roads, title="College Road Network"):
    G, pos = _build_nx_graph(colleges, roads)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    fig.patch.set_facecolor("#ffffff")
    _style_ax(ax, title)

    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=700,
                           node_color="#3498db", alpha=0.9)
    nx.draw_networkx_labels(G, pos, ax=ax, font_color="white",
                            font_size=11, font_weight="bold")
    nx.draw_networkx_edges(G, pos, ax=ax, width=1.8,
                           edge_color="#95a5a6", alpha=0.7)
    edge_labels = {(u, v): f"{d['weight']} km"
                   for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels, ax=ax,
                                 font_size=8, font_color="#555")

    # Node name labels below nodes
    name_pos = {c: (p[0], p[1] - 0.045 * max(abs(y) for _, y in pos.values()))
                for c, p in pos.items()}
    for c, (x, y) in pos.items():
        ax.text(x, y - 32, colleges[c]["name"], ha="center", va="top",
                fontsize=7.5, color="#555", style="italic")

    return _fig_to_b64(fig)


# ─── Route Highlight ───────────────────────────────────────────────────────────

def draw_route(colleges, roads, route, title="Optimal Route",
               highlight_color="#e74c3c"):
    G, pos = _build_nx_graph(colleges, roads)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    fig.patch.set_facecolor("#ffffff")
    _style_ax(ax, title)

    # Base graph
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=650,
                           node_color="#bdc3c7", alpha=0.6)
    nx.draw_networkx_edges(G, pos, ax=ax, width=1.2,
                           edge_color="#bdc3c7", alpha=0.4)

    # Route edges
    route_edges = [(route[i], route[i+1]) for i in range(len(route)-1)
                   if G.has_edge(route[i], route[i+1])]

    # Highlighted nodes
    route_nodes = list(dict.fromkeys(route))
    node_colors = []
    for n in G.nodes():
        if n == route[0]:
            node_colors.append("#2ecc71")    # start = green
        elif n in route_nodes:
            node_colors.append(highlight_color)
        else:
            node_colors.append("#bdc3c7")

    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=700,
                           node_color=node_colors, alpha=0.95)
    nx.draw_networkx_labels(G, pos, ax=ax, font_color="white",
                            font_size=11, font_weight="bold")
    nx.draw_networkx_edges(G, pos, edgelist=route_edges, ax=ax,
                           width=3.5, edge_color=highlight_color,
                           arrows=True, arrowsize=20, alpha=0.9)

    edge_labels = {(u, v): f"{d['weight']}" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels, ax=ax,
                                 font_size=8, font_color="#555")

    # Node names
    for c, (x, y) in pos.items():
        ax.text(x, y - 32, colleges[c]["name"], ha="center", va="top",
                fontsize=7.5, color="#444", style="italic")

    # Route order labels
    for i, node in enumerate(route):
        if node in pos:
            x, y = pos[node]
            ax.annotate(f" {i+1}", (x, y), fontsize=9,
                        color=highlight_color, fontweight="bold")

    # Legend
    patches = [
        mpatches.Patch(color="#2ecc71",       label="Start/End"),
        mpatches.Patch(color=highlight_color, label="Route nodes"),
        mpatches.Patch(color="#bdc3c7",       label="Not visited"),
    ]
    ax.legend(handles=patches, loc="lower right", fontsize=8)

    return _fig_to_b64(fig)


# ─── MST ───────────────────────────────────────────────────────────────────────

def draw_mst(colleges, roads, mst_edges, title="Minimum Spanning Tree"):
    G, pos = _build_nx_graph(colleges, roads)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    fig.patch.set_facecolor("#ffffff")
    _style_ax(ax, title)

    mst_set = {(u, v) for u, v, _ in mst_edges} | {(v, u) for u, v, _ in mst_edges}
    mst_edge_list = [(u, v) for u, v in G.edges() if (u, v) in mst_set]
    non_mst        = [(u, v) for u, v in G.edges() if (u, v) not in mst_set]

    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=700,
                           node_color="#9b59b6", alpha=0.85)
    nx.draw_networkx_labels(G, pos, ax=ax, font_color="white",
                            font_size=11, font_weight="bold")
    nx.draw_networkx_edges(G, pos, edgelist=non_mst, ax=ax,
                           width=1.2, edge_color="#bdc3c7", alpha=0.35, style="dashed")
    nx.draw_networkx_edges(G, pos, edgelist=mst_edge_list, ax=ax,
                           width=3.5, edge_color="#9b59b6", alpha=0.9)

    mst_labels = {(u, v): f"{w}" for u, v, w in mst_edges}
    all_labels  = {(u, v): f"{d['weight']}" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, all_labels, ax=ax,
                                 font_size=8, font_color="#555")

    for c, (x, y) in pos.items():
        ax.text(x, y - 32, colleges[c]["name"], ha="center", va="top",
                fontsize=7.5, color="#444", style="italic")

    patches = [
        mpatches.Patch(color="#9b59b6", label="MST edges"),
        mpatches.Patch(color="#bdc3c7", label="Non-MST edges"),
    ]
    ax.legend(handles=patches, loc="lower right", fontsize=8)

    return _fig_to_b64(fig)
