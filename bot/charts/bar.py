import io
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
from bot.charts.renderer import apply_theme, BACKGROUND, SURFACE2, ACCENT, ACCENT2, TEXT, TEXT_DIM

def _draw(labels, values, title, xlabel, bar_labels=None):
    fig, ax = plt.subplots(figsize=(11, max(5, len(labels) * 0.65)))
    apply_theme(fig, ax)

    n = len(labels)
    cmap = mcolors.LinearSegmentedColormap.from_list("glow", [ACCENT2, ACCENT])
    colors = [cmap(i / max(n - 1, 1)) for i in range(n)]

    bars = ax.barh(
        labels[::-1], values[::-1],
        color=colors[::-1],
        height=0.55,
        edgecolor="none",
    )

    for bar, color in zip(bars, colors[::-1]):
        bar.set_path_effects([
            pe.withStroke(linewidth=8, foreground=color, alpha=0.2),
            pe.Normal()
        ])

    display_labels = bar_labels[::-1] if bar_labels else [str(v) for v in values[::-1]]
    for bar, lbl in zip(bars, display_labels):
        ax.text(
            bar.get_width() + max(values) * 0.015,
            bar.get_y() + bar.get_height() / 2,
            lbl,
            va="center", color=TEXT, fontsize=9, fontweight="bold"
        )

    for i, label in enumerate(labels[::-1]):
        ax.text(
            -max(values) * 0.02, i,
            f"#{len(labels) - i}",
            va="center", ha="right",
            color=TEXT_DIM, fontsize=8
        )

    ax.set_title(title, fontsize=13, pad=12, loc="center")
    ax.set_xlabel(xlabel, color=TEXT_DIM)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.margins(x=0.18)
    ax.set_xlim(left=-max(values) * 0.06)

    fig.patch.set_linewidth(1)
    fig.patch.set_edgecolor(SURFACE2)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150, facecolor=BACKGROUND)
    buf.seek(0)
    plt.close(fig)
    return buf

async def horizontal_bar(labels, values, title, xlabel, bar_labels=None):
    from bot.charts.renderer import run_in_executor
    return await run_in_executor(_draw, labels, values, title, xlabel, bar_labels)