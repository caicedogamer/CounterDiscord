import io
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
from bot.charts.renderer import BACKGROUND, SURFACE2, TEXT, TEXT_DIM

DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

MIDNIGHT_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "midnight",
    ["#0a0e1a", "#0d2044", "#1a3a6e", "#2a5ba8", "#4f8ef7", "#7ab3ff"],
)

def _draw(rows, title):
    grid = np.zeros((7, 24))
    for row in rows:
        d = int(row["day_of_week"])
        h = int(row["hour_of_day"])
        grid[d][h] = row["msg_count"]

    max_val = grid.max()

    fig, ax = plt.subplots(figsize=(18, 6))
    fig.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)

    sns.heatmap(
        grid,
        ax=ax,
        cmap=MIDNIGHT_CMAP,
        linewidths=0.5,
        linecolor="#0a0e1a",
        yticklabels=DAYS,
        xticklabels=[f"{h:02d}h" for h in range(24)],
        cbar_kws={"shrink": 0.6, "pad": 0.02, "label": "Messages"},
        annot=True,           # show numbers inside cells
        fmt=".0f",            # no decimals
        annot_kws={
            "size": 7,
            "color": TEXT,
            "alpha": 0.9,
        },
        vmin=0,
    )

    # Hide zero annotations to reduce noise
    for text in ax.texts:
        if text.get_text() == "0":
            text.set_visible(False)

    # Highlight peak cell with a border
    if max_val > 0:
        peak = np.unravel_index(grid.argmax(), grid.shape)
        ax.add_patch(plt.Rectangle(
            (peak[1], peak[0]), 1, 1,
            fill=False, edgecolor="#ffffff", lw=2, zorder=5
        ))
        ax.text(
            peak[1] + 0.5, peak[0] - 0.15,
            "peak",
            ha="center", va="bottom",
            color="#ffffff", fontsize=7, fontweight="bold"
        )

    # Style colorbar
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(colors=TEXT, labelsize=8)
    cbar.ax.yaxis.label.set_color(TEXT)
    cbar.outline.set_edgecolor(SURFACE2)

    fig.suptitle(title, fontsize=14, fontweight="bold", color=TEXT, y=1.01)
    ax.set_xlabel("Hour (UTC)", color=TEXT_DIM, fontsize=9, labelpad=8)
    ax.set_ylabel("Day of Week", color=TEXT_DIM, fontsize=9, labelpad=8)
    ax.tick_params(colors=TEXT, labelsize=8)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)

    # Add a subtle legend note
    fig.text(
        0.01, 0.01,
        "Times are in UTC  •  White border = peak activity",
        color=TEXT_DIM, fontsize=7, ha="left"
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150, facecolor=BACKGROUND)
    buf.seek(0)
    plt.close(fig)
    return buf

async def activity_heatmap(rows, title):
    from bot.charts.renderer import run_in_executor
    return await run_in_executor(_draw, rows, title)