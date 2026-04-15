import io
import textwrap
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import networkx as nx
from bot.charts.renderer import BACKGROUND, TEXT, TEXT_DIM, run_in_executor

# Nodes: dark maroon (few connections) → deep red → hot pink (most connections)
NODE_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "social_red",
    ["#1a0510", "#6b0f35", "#c0255a", "#ff2d55", "#ff7090"],
)
# Edges: very dark → rose red
EDGE_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "edge_red",
    ["#2a0a18", "#7a1848", "#d03070"],
)

PANEL_BG   = (0.04, 0.06, 0.12, 0.85)
PANEL_EDGE = "#3a1a30"
MAX_NODES  = 40


def _trim(G, max_nodes):
    if len(G.nodes) <= max_nodes:
        return G
    strengths = dict(G.degree(weight="weight"))
    top = sorted(strengths, key=strengths.get, reverse=True)[:max_nodes]
    return G.subgraph(top).copy()


def _draw(edges, title):
    if not edges:
        return None

    # Directed graph — preserves who initiates interactions
    G = nx.DiGraph()
    for from_label, to_label, count in edges:
        if G.has_edge(from_label, to_label):
            G[from_label][to_label]["weight"] += count
        else:
            G.add_edge(from_label, to_label, weight=count)

    if len(G.nodes) == 0:
        return None

    # Use undirected copy for layout and degree metrics
    UG = _trim(G.to_undirected(reciprocal=False), MAX_NODES)
    G  = G.subgraph(UG.nodes).copy()

    # ── Figure layout ────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(22, 16), dpi=150)
    fig.patch.set_facecolor(BACKGROUND)

    ax       = fig.add_axes([0.0,  0.0,  0.80, 1.0])   # graph canvas
    ax_stats = fig.add_axes([0.815, 0.08, 0.165, 0.84]) # side panel

    ax.set_facecolor(BACKGROUND)
    ax.axis("off")

    ax_stats.set_facecolor(PANEL_BG)
    for spine in ax_stats.spines.values():
        spine.set_edgecolor(PANEL_EDGE)
        spine.set_linewidth(1.4)
    ax_stats.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

    # ── Layout ───────────────────────────────────────────────────────────────
    n = len(G.nodes)
    if n <= 12:
        pos = nx.kamada_kawai_layout(UG)
    else:
        k = 3.2 / np.sqrt(n)
        pos = nx.spring_layout(UG, k=k, iterations=150, seed=42)

    # ── Metrics ──────────────────────────────────────────────────────────────
    node_strength = dict(UG.degree(weight="weight"))
    max_strength  = max(node_strength.values()) if node_strength else 1
    node_norm     = {nd: node_strength[nd] / max_strength for nd in G.nodes()}

    all_weights = np.array([d["weight"] for _, _, d in G.edges(data=True)], dtype=float)
    max_w       = all_weights.max() if len(all_weights) > 0 else 1.0

    # ── Draw edges ───────────────────────────────────────────────────────────
    for u, v, data in G.edges(data=True):
        nw    = data["weight"] / max_w
        color = EDGE_CMAP(nw)
        width = 0.6 + nw * 5.5
        alpha = 0.18 + nw * 0.65
        # Curve more when both directions exist
        rad = 0.22 if G.has_edge(v, u) else 0.10
        nx.draw_networkx_edges(
            G, pos, ax=ax,
            edgelist=[(u, v)],
            width=width,
            alpha=alpha,
            edge_color=[color],
            arrows=True,
            arrowsize=int(10 + nw * 10),
            arrowstyle="-|>",
            connectionstyle=f"arc3,rad={rad}",
            min_source_margin=20,
            min_target_margin=20,
        )

    # ── Draw nodes (glow layer first, then solid) ─────────────────────────
    node_list   = list(G.nodes())
    node_sizes  = [350 + node_norm[nd] * 2800 for nd in node_list]
    node_colors = [NODE_CMAP(node_norm[nd]) for nd in node_list]

    # Soft glow behind each node
    glow_sizes  = [s * 2.6 for s in node_sizes]
    glow_colors = [(*mcolors.to_rgb(NODE_CMAP(node_norm[nd])), 0.10) for nd in node_list]
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        nodelist=node_list,
        node_size=glow_sizes,
        node_color=glow_colors,
        linewidths=0,
    )

    # Solid nodes
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        nodelist=node_list,
        node_size=node_sizes,
        node_color=node_colors,
        linewidths=1.8,
        edgecolors="#ffffff30",
    )

    # ── Labels ───────────────────────────────────────────────────────────────
    for nd in node_list:
        x, y   = pos[nd]
        label  = textwrap.shorten(nd, width=15, placeholder="..")
        fsize  = 7.5 + node_norm[nd] * 5.5   # bigger label = more connected
        fweight = "bold" if node_norm[nd] > 0.4 else "normal"
        ax.text(
            x, y, label,
            fontsize=fsize,
            fontweight=fweight,
            color="#ffffff",
            ha="center", va="center",
            zorder=10,
            path_effects=[
                pe.withStroke(linewidth=3.5, foreground="#000000"),
                pe.Normal(),
            ],
        )

    # ── Count labels on strongest edges (top 30%) ────────────────────────
    threshold = max_w * 0.35
    for u, v, data in G.edges(data=True):
        if data["weight"] >= threshold:
            mx = (pos[u][0] + pos[v][0]) / 2
            my = (pos[u][1] + pos[v][1]) / 2
            ax.text(
                mx, my, str(int(data["weight"])),
                fontsize=6.5, color=TEXT_DIM,
                ha="center", va="center",
                zorder=9,
                bbox=dict(facecolor=BACKGROUND, edgecolor="none", alpha=0.75, pad=1.5),
            )

    # ── Colorbar (bottom-left, horizontal) ───────────────────────────────
    sm = plt.cm.ScalarMappable(
        cmap=NODE_CMAP,
        norm=plt.Normalize(vmin=0, vmax=max_strength),
    )
    sm.set_array([])
    cbar_ax = fig.add_axes([0.02, 0.035, 0.36, 0.022])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.ax.tick_params(colors=TEXT_DIM, labelsize=7)
    cbar.set_label("Total interactions", color=TEXT_DIM, fontsize=7.5, labelpad=3)
    cbar.outline.set_edgecolor(PANEL_EDGE)

    # ── Side panel: top connectors ────────────────────────────────────────
    sorted_nodes = sorted(node_strength, key=node_strength.get, reverse=True)
    top_nodes    = [nd for nd in sorted_nodes if nd in G.nodes()][:12]

    ax_stats.text(
        0.5, 0.975, "Top Connectors",
        ha="center", va="top", color=TEXT,
        fontsize=9.5, fontweight="bold",
        transform=ax_stats.transAxes,
    )
    ax_stats.plot(
        [0.08, 0.92], [0.955, 0.955],
        color=PANEL_EDGE, linewidth=1.0, transform=ax_stats.transAxes,
    )

    row_h = 0.073
    for i, nd in enumerate(top_nodes):
        y    = 0.925 - i * row_h
        norm = node_norm[nd]
        dot_color = NODE_CMAP(norm)

        # rank
        ax_stats.text(
            0.07, y, f"{i+1}.",
            ha="right", va="center", color=TEXT_DIM,
            fontsize=7.5, transform=ax_stats.transAxes,
        )
        # colored dot
        ax_stats.text(
            0.13, y, "●",
            ha="center", va="center", color=dot_color,
            fontsize=10, transform=ax_stats.transAxes,
        )
        # name
        short_name = textwrap.shorten(nd, width=11, placeholder="..")
        ax_stats.text(
            0.20, y, short_name,
            ha="left", va="center", color=TEXT,
            fontsize=7.5, fontweight="bold" if norm > 0.5 else "normal",
            transform=ax_stats.transAxes,
        )
        # count
        ax_stats.text(
            0.97, y, str(node_strength[nd]),
            ha="right", va="center", color=TEXT_DIM,
            fontsize=7, transform=ax_stats.transAxes,
        )

    # Total interactions summary
    total_interactions = int(sum(d["weight"] for _, _, d in G.edges(data=True)))
    ax_stats.plot(
        [0.08, 0.92], [0.055, 0.055],
        color=PANEL_EDGE, linewidth=1.0, transform=ax_stats.transAxes,
    )
    ax_stats.text(
        0.5, 0.035,
        f"{total_interactions} total interactions",
        ha="center", va="center", color=TEXT_DIM,
        fontsize=7, transform=ax_stats.transAxes,
    )

    # ── Title & footer ────────────────────────────────────────────────────
    if len(G.nodes) < len(nx.DiGraph([(f, t, {"weight": c}) for f, t, c in edges]).nodes):
        subtitle = f"(showing top {MAX_NODES} users by activity)"
    else:
        subtitle = ""

    fig.suptitle(
        title + (f"\n{subtitle}" if subtitle else ""),
        fontsize=16, fontweight="bold", color=TEXT, y=0.98,
    )

    fig.text(
        0.01, 0.012,
        "Node size & color = total interactions  •  Arrow thickness = interaction count  "
        "•  Curved arrows = mutual interactions  •  Sources: replies & mentions",
        color=TEXT_DIM, fontsize=6.5,
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150, facecolor=BACKGROUND)
    buf.seek(0)
    plt.close(fig)
    return buf


async def social_graph(edges, title):
    return await run_in_executor(_draw, edges, title)
