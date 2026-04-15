import io
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import networkx as nx
from bot.charts.renderer import BACKGROUND, SURFACE2, ACCENT, ACCENT2, TEXT, TEXT_DIM, run_in_executor


def _draw(edges, title):
    """
    edges: list of (from_label, to_label, count)
    """
    G = nx.Graph()
    for from_label, to_label, count in edges:
        if G.has_edge(from_label, to_label):
            G[from_label][to_label]["weight"] += count
        else:
            G.add_edge(from_label, to_label, weight=count)

    if len(G.nodes) == 0:
        return None

    fig, ax = plt.subplots(figsize=(16, 12))
    fig.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    ax.axis("off")

    pos = nx.spring_layout(G, k=2.5, iterations=100, seed=42)

    # --- Edge weights ---
    weights = np.array([G[u][v]["weight"] for u, v in G.edges()])
    max_w = weights.max() if len(weights) > 0 else 1
    norm_w = weights / max_w

    # Edge widths and alphas scaled to interaction count
    edge_widths = 0.5 + norm_w * 6
    edge_alphas = 0.2 + norm_w * 0.7

    # Draw edges individually so each can have its own alpha
    edge_cmap = mcolors.LinearSegmentedColormap.from_list("ec", ["#2a0a18", "#d03070"])
    for (u, v), width, alpha, nw in zip(G.edges(), edge_widths, edge_alphas, norm_w):
        color = edge_cmap(nw)
        nx.draw_networkx_edges(
            G, pos, edgelist=[(u, v)], ax=ax,
            width=width, alpha=alpha,
            edge_color=[color],
            style="solid",
        )

    # --- Node sizes scaled to total interactions ---
    node_strength = dict(G.degree(weight="weight"))
    max_strength = max(node_strength.values()) if node_strength else 1
    node_sizes = [300 + (node_strength[n] / max_strength) * 2200 for n in G.nodes()]

    # Node colors using a gradient: dark maroon (few) -> crimson -> hot pink (many)
    node_cmap = mcolors.LinearSegmentedColormap.from_list("nc", ["#1a0510", "#c0255a", "#ff7090"])
    node_colors = [node_cmap(node_strength[n] / max_strength) for n in G.nodes()]

    nodes = nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        linewidths=1.5,
        edgecolors=SURFACE2,
    )

    # Glow effect on nodes
    if nodes is not None:
        nodes.set_path_effects([
            pe.withStroke(linewidth=10, foreground="#ff2d55", alpha=0.15),
            pe.Normal(),
        ])

    # --- Labels ---
    nx.draw_networkx_labels(
        G, pos, ax=ax,
        font_size=8,
        font_color=TEXT,
        font_weight="bold",
        bbox=dict(
            boxstyle="round,pad=0.3",
            facecolor=BACKGROUND,
            edgecolor=SURFACE2,
            alpha=0.75,
            linewidth=0.8,
        ),
    )

    # --- Edge weight labels on strong connections only ---
    strong_edges = {(u, v): G[u][v]["weight"]
                    for u, v in G.edges()
                    if G[u][v]["weight"] >= max_w * 0.3}
    nx.draw_networkx_edge_labels(
        G, pos, ax=ax,
        edge_labels=strong_edges,
        font_size=7,
        font_color=TEXT_DIM,
        bbox=dict(facecolor=BACKGROUND, edgecolor="none", alpha=0.6),
    )

    fig.suptitle(title, fontsize=15, fontweight="bold", color=TEXT, y=1.01)

    fig.text(
        0.01, 0.01,
        "Node size = total interactions  •  Edge thickness = interaction count  •  Replies & mentions",
        color=TEXT_DIM, fontsize=7,
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150, facecolor=BACKGROUND)
    buf.seek(0)
    plt.close(fig)
    return buf


async def social_graph(edges, title):
    return await run_in_executor(_draw, edges, title)
