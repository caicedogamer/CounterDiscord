import io
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import seaborn as sns
from scipy.ndimage import gaussian_filter
from bot.charts.renderer import BACKGROUND, SURFACE, SURFACE2, ACCENT, ACCENT2, TEXT, TEXT_DIM

DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

MIDNIGHT_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "midnight",
    ["#0a0e1a", "#0d2044", "#1a3a6e", "#2a5ba8", "#4f8ef7", "#7ab3ff"],
)

def _generate_background(width, height):
    """Generate a procedural nebula/space background."""
    rng = np.random.default_rng(42)

    # Base dark gradient
    bg = np.zeros((height, width, 3))
    for i in range(height):
        t = i / height
        bg[i, :, 0] = 0.04 + t * 0.02
        bg[i, :, 1] = 0.05 + t * 0.03
        bg[i, :, 2] = 0.10 + t * 0.08

    # Nebula clouds
    for _ in range(4):
        blob = rng.random((height, width)) * 0.12
        blob = gaussian_filter(blob, sigma=rng.integers(40, 120))
        cx = rng.integers(0, 3)  # color channel bias
        bg[:, :, cx] += blob * rng.uniform(0.3, 0.8)
        bg[:, :, 2]  += blob * 0.4

    # Stars
    num_stars = 300
    sy = rng.integers(0, height, num_stars)
    sx = rng.integers(0, width, num_stars)
    brightness = rng.uniform(0.4, 1.0, num_stars)
    for y, x, b in zip(sy, sx, brightness):
        bg[y, x, :] = [b * 0.9, b * 0.95, b]

    return np.clip(bg, 0, 1)

def _add_panel(fig, ax, title):
    """Style an axis as a frosted panel."""
    ax.set_facecolor((0.06, 0.08, 0.15, 0.85))
    for spine in ax.spines.values():
        spine.set_edgecolor("#2a3a5e")
        spine.set_linewidth(1.2)
    ax.tick_params(colors=TEXT, labelsize=8)
    ax.grid(True, color="#1a2540", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_title(title, color=TEXT, fontsize=11, fontweight="bold", pad=10)

def _draw_bar_panel(ax, rows, title, xlabel, color_start, color_end):
    _add_panel(ax, ax, title)
    ax.set_xlabel(xlabel, color=TEXT_DIM, fontsize=8)

    if not rows:
        ax.text(0.5, 0.5, "No data yet", ha="center", va="center",
                color=TEXT_DIM, fontsize=9, transform=ax.transAxes)
        ax.axis("off")
        return

    n = len(rows)
    cmap = mcolors.LinearSegmentedColormap.from_list("g", [color_start, color_end])
    colors = [cmap(i / max(n - 1, 1)) for i in range(n)]
    names  = [r["name"] for r in rows]
    counts = [r["count"] for r in rows]
    disp   = [r.get("label", str(r["count"])) for r in rows]

    bars = ax.barh(names[::-1], counts[::-1], color=colors, height=0.55, edgecolor="none")
    for bar, lbl in zip(bars, disp[::-1]):
        ax.text(
            bar.get_width() + max(counts) * 0.02,
            bar.get_y() + bar.get_height() / 2,
            lbl, va="center", color=TEXT, fontsize=8, fontweight="bold"
        )
    ax.margins(x=0.22)

def _draw(leaderboard_rows, heatmap_rows, emoji_rows, vc_rows, sticker_rows, channel_rows, days):
    FIG_W, FIG_H = 20, 20
    DPI = 150

    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=DPI)
    fig.patch.set_facecolor(BACKGROUND)

    # --- Background image ---
    bg_px_w = int(FIG_W * DPI)
    bg_px_h = int(FIG_H * DPI)
    bg = _generate_background(bg_px_w, bg_px_h)
    bg_ax = fig.add_axes([0, 0, 1, 1], zorder=0)
    bg_ax.imshow(bg, aspect="auto", extent=[0, 1, 0, 1],
                 transform=bg_ax.transAxes, origin="upper")
    bg_ax.axis("off")

    gs = gridspec.GridSpec(
        4, 2, figure=fig,
        hspace=0.58, wspace=0.32,
        left=0.04, right=0.95,
        top=0.91, bottom=0.06,
        height_ratios=[0.8, 1, 1, 0.8]
    )

    ax_heat     = fig.add_subplot(gs[0, :], zorder=2)
    ax_board    = fig.add_subplot(gs[1, 0], zorder=2)
    ax_emoji    = fig.add_subplot(gs[1, 1], zorder=2)
    ax_vc       = fig.add_subplot(gs[2, 0], zorder=2)
    ax_blank    = fig.add_subplot(gs[2, 1], zorder=2)
    ax_channels = fig.add_subplot(gs[3, :], zorder=2)

    # --- Heatmap panel ---
    grid = np.zeros((7, 24))
    for row in heatmap_rows:
        d = int(row["day_of_week"])
        h = int(row["hour_of_day"])
        grid[d][h] = row["msg_count"]

    ax_heat.set_facecolor((0.06, 0.08, 0.15, 0.85))
    for spine in ax_heat.spines.values():
        spine.set_edgecolor("#2a3a5e")
        spine.set_linewidth(1.2)

    sns.heatmap(
        grid, ax=ax_heat, cmap=MIDNIGHT_CMAP,
        linewidths=0.4, linecolor="#0a0e1a",
        yticklabels=DAYS,
        xticklabels=[f"{h:02d}h" for h in range(24)],
        cbar_kws={"shrink": 0.5, "pad": 0.01},
        annot=True, fmt=".0f",
        annot_kws={"size": 6, "color": TEXT, "alpha": 0.9},
        vmin=0,
    )
    for text in ax_heat.texts:
        if text.get_text() == "0":
            text.set_visible(False)

    max_val = grid.max()
    if max_val > 0:
        peak = np.unravel_index(grid.argmax(), grid.shape)
        ax_heat.add_patch(plt.Rectangle(
            (peak[1], peak[0]), 1, 1,
            fill=False, edgecolor="#ffffff", lw=2, zorder=5
        ))
        ax_heat.text(
            peak[1] + 0.5, peak[0] - 0.15, "peak",
            ha="center", va="bottom",
            color="#ffffff", fontsize=7, fontweight="bold"
        )

    cbar = ax_heat.collections[0].colorbar
    cbar.ax.tick_params(colors=TEXT, labelsize=7)
    cbar.ax.yaxis.label.set_color(TEXT)
    ax_heat.set_title(f"Activity Heatmap — Last {days} days",
                  color=TEXT, fontsize=13, fontweight="bold", pad=12,
                  loc="center")
    ax_heat.tick_params(colors=TEXT, labelsize=7)
    plt.setp(ax_heat.get_xticklabels(), rotation=45, ha="right")
    plt.setp(ax_heat.get_yticklabels(), rotation=0)
    fig.text(0.06, 0.065, "UTC timezone  •  White border = peak activity",
             color=TEXT_DIM, fontsize=7)

    # --- Bar panels ---
    _draw_bar_panel(ax_board, leaderboard_rows,
                    f"Top Senders ({days}d)", "Messages", ACCENT2, ACCENT)

    _draw_bar_panel(ax_emoji, emoji_rows,
                    f"Top Emojis ({days}d)", "Times Used", ACCENT, "#a78bfa")

    _draw_bar_panel(ax_vc, vc_rows,
                    f"Most Time in VC ({days}d)", "Hours", "#1a6e4f", "#4ff7a0")

    _draw_bar_panel(ax_blank, sticker_rows,
                    f"Top Stickers ({days}d)", "Times Used", "#6e4f1a", "#f7c44f")

    _draw_bar_panel(ax_channels, channel_rows,
                    f"Most Active Channels ({days}d)", "Messages", "#1a4e6e", "#4fb8f7")

    # --- Title ---
    fig.suptitle(
        f"✦  Server Dashboard  ✦  Last {days} Days",
        fontsize=17, color=TEXT, y=0.97, fontweight="bold"
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=DPI, facecolor=BACKGROUND)
    buf.seek(0)
    plt.close(fig)
    return buf

async def server_dashboard(leaderboard_rows, heatmap_rows, emoji_rows, vc_rows, sticker_rows, channel_rows, days):
    from bot.charts.renderer import run_in_executor
    return await run_in_executor(_draw, leaderboard_rows, heatmap_rows, emoji_rows, vc_rows, sticker_rows, channel_rows, days)