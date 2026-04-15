import io
import os
import textwrap
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import seaborn as sns
from bot.charts.renderer import BACKGROUND, ACCENT, ACCENT2, TEXT, TEXT_DIM

BACKGROUNDS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "backgrounds")

DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

MIDNIGHT_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "rose",
    ["#0a0e1a", "#2a0a20", "#6a1048", "#aa1868", "#e03088", "#ff60b0"],
)

PANEL_BG   = (0.055, 0.082, 0.145, 0.72)   # semi-transparent so bg image shows through
PANEL_EDGE = "#2a3a5e"
GRID_COLOR = "#182035"


def _add_panel(ax, title):
    """Style an axis as a frosted panel."""
    ax.set_facecolor(PANEL_BG)
    ax.patch.set_alpha(0.72)
    for spine in ax.spines.values():
        spine.set_edgecolor(PANEL_EDGE)
        spine.set_linewidth(1.5)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.grid(True, color=GRID_COLOR, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    ax.set_title(title, color=TEXT, fontsize=13, fontweight="bold", pad=12)

def _draw_bar_panel(ax, rows, title, xlabel, color_start, color_end):
    _add_panel(ax, title)
    ax.set_xlabel(xlabel, color=TEXT_DIM, fontsize=10)

    if not rows:
        ax.text(0.5, 0.5, "No data yet", ha="center", va="center",
                color=TEXT_DIM, fontsize=11, transform=ax.transAxes)
        ax.axis("off")
        return

    n = len(rows)
    cmap = mcolors.LinearSegmentedColormap.from_list("g", [color_start, color_end])
    colors = [cmap(i / max(n - 1, 1)) for i in range(n)]
    names  = [textwrap.fill(r["name"], width=18) for r in rows]
    counts = [r["count"] for r in rows]
    disp   = [r.get("label", str(r["count"])) for r in rows]

    bars = ax.barh(names[::-1], counts[::-1], color=colors, height=0.58, edgecolor="none")
    for bar, lbl in zip(bars, disp[::-1]):
        ax.text(
            bar.get_width() + max(counts) * 0.02,
            bar.get_y() + bar.get_height() / 2,
            lbl, va="center", color=TEXT, fontsize=10, fontweight="bold"
        )
    ax.margins(x=0.24)
    ax.tick_params(axis="y", labelsize=10)
    ax.tick_params(axis="x", labelsize=9)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

def _draw(leaderboard_rows, heatmap_rows, emoji_rows, vc_rows, sticker_rows, channel_rows, days, guild_id=None):
    FIG_W, FIG_H = 20, 20
    DPI = 150

    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=DPI)
    fig.patch.set_facecolor(BACKGROUND)

    # Custom background image
    if guild_id is not None:
        bg_file = os.path.join(BACKGROUNDS_DIR, f"{guild_id}.png")
        if os.path.exists(bg_file):
            from PIL import Image
            target_w, target_h = FIG_W * DPI, FIG_H * DPI
            pil_img = Image.open(bg_file).convert("RGBA")
            src_w, src_h = pil_img.size
            scale = max(target_w / src_w, target_h / src_h)
            new_w, new_h = int(src_w * scale), int(src_h * scale)
            pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - target_w) // 2
            top  = (new_h - target_h) // 2
            pil_img = pil_img.crop((left, top, left + target_w, top + target_h))
            bg_img = np.array(pil_img)
            bg_ax = fig.add_axes([0, 0, 1, 1], zorder=0)
            bg_ax.imshow(bg_img, aspect="auto", alpha=0.35)
            bg_ax.axis("off")

    gs = gridspec.GridSpec(
        4, 2, figure=fig,
        hspace=0.72, wspace=0.35,
        left=0.05, right=0.95,
        top=0.91, bottom=0.07,
        height_ratios=[1.3, 1, 1, 1.2]
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

    ax_heat.set_facecolor(PANEL_BG)
    ax_heat.patch.set_alpha(0.72)
    for spine in ax_heat.spines.values():
        spine.set_edgecolor(PANEL_EDGE)
        spine.set_linewidth(1.5)

    sns.heatmap(
        grid, ax=ax_heat, cmap=MIDNIGHT_CMAP,
        linewidths=0.5, linecolor="#0a0e1a",
        yticklabels=DAYS,
        xticklabels=[f"{h:02d}h" for h in range(24)],
        cbar_kws={"shrink": 0.5, "pad": 0.01},
        annot=True, fmt=".0f",
        annot_kws={"size": 8, "color": "#000000", "alpha": 0.85},
        vmin=0,
    )
    ax_heat.set_xlim(0, 24)
    ax_heat.set_ylim(7, 0)
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
            color="#ffffff", fontsize=9, fontweight="bold"
        )

    cbar = ax_heat.collections[0].colorbar
    cbar.ax.tick_params(colors=TEXT, labelsize=9)
    cbar.ax.yaxis.label.set_color(TEXT)
    ax_heat.set_title(f"Activity Heatmap — Last {days} days",
                  color=TEXT, fontsize=14, fontweight="bold", pad=12,
                  loc="center")
    ax_heat.tick_params(colors=TEXT, labelsize=9)
    plt.setp(ax_heat.get_xticklabels(), rotation=45, ha="right", fontsize=9)
    plt.setp(ax_heat.get_yticklabels(), rotation=0, fontsize=10)
    fig.text(0.06, 0.065, "UTC timezone  •  White border = peak activity",
             color=TEXT_DIM, fontsize=9)

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
        fontsize=20, color=TEXT, y=0.97, fontweight="bold"
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=DPI, facecolor=BACKGROUND)
    buf.seek(0)
    plt.close(fig)
    return buf

async def server_dashboard(leaderboard_rows, heatmap_rows, emoji_rows, vc_rows, sticker_rows, channel_rows, days, guild_id=None):
    from bot.charts.renderer import run_in_executor
    return await run_in_executor(_draw, leaderboard_rows, heatmap_rows, emoji_rows, vc_rows, sticker_rows, channel_rows, days, guild_id)