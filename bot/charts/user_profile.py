import io
import textwrap
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import emoji as emoji_lib
import discord
from bot.charts.renderer import BACKGROUND, ACCENT, ACCENT2, TEXT, TEXT_DIM

PANEL_BG   = "#0e1525"
PANEL_EDGE = "#2a3a5e"
GRID_COLOR = "#182035"


def _add_panel(ax, title):
    ax.set_facecolor(PANEL_BG)
    for spine in ax.spines.values():
        spine.set_edgecolor(PANEL_EDGE)
        spine.set_linewidth(1.5)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.grid(True, color=GRID_COLOR, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    ax.set_title(title, color=TEXT, fontsize=12, fontweight="bold", pad=10)


def _bar(ax, rows, name_key, count_key, title, xlabel, c_start, c_end, format_name=None):
    _add_panel(ax, title)
    ax.set_xlabel(xlabel, color=TEXT_DIM, fontsize=9)

    if not rows:
        ax.text(0.5, 0.5, "No data yet", ha="center", va="center",
                color=TEXT_DIM, fontsize=10, transform=ax.transAxes)
        ax.axis("off")
        return

    names  = [textwrap.fill(format_name(r) if format_name else str(r[name_key]), width=18) for r in rows]
    counts = [r[count_key] for r in rows]
    n      = len(rows)
    cmap   = mcolors.LinearSegmentedColormap.from_list("g", [c_start, c_end])
    colors = [cmap(i / max(n - 1, 1)) for i in range(n)]

    bars = ax.barh(names[::-1], counts[::-1], color=colors, height=0.55, edgecolor="none")
    max_c = max(counts)
    for bar, lbl in zip(bars, [str(c) for c in counts[::-1]]):
        ax.text(
            bar.get_width() + max_c * 0.02,
            bar.get_y() + bar.get_height() / 2,
            lbl, va="center", color=TEXT, fontsize=9, fontweight="bold"
        )
    ax.margins(x=0.22)
    ax.tick_params(axis="y", labelsize=9)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))


def _fmt_emoji(guild, row):
    emoji_id   = row["emoji_id"]
    emoji_name = row["emoji_name"]
    if emoji_id and str(emoji_id).isdigit():
        ge = discord.utils.get(guild.emojis, id=int(emoji_id))
        if ge:
            return f":{ge.name}:"
        return f":{emoji_name}:" if emoji_name else f":custom_{str(emoji_id)[-4:]}:"
    try:
        name = emoji_lib.demojize(emoji_id).strip(":")
        if len(name) > 18:
            name = name[:16] + ".."
        return f":{name}:"
    except Exception:
        return str(emoji_id)


def _draw(display_name, avatar_url, stats, emoji_rows, sticker_rows, word_rows, days, guild, guild_name=None):
    fig = plt.figure(figsize=(18, 14), dpi=150)
    fig.patch.set_facecolor(BACKGROUND)

    gs = gridspec.GridSpec(
        2, 3, figure=fig,
        hspace=0.55, wspace=0.35,
        left=0.05, right=0.95,
        top=0.85, bottom=0.06,
    )

    ax_emoji   = fig.add_subplot(gs[0, 0])
    ax_sticker = fig.add_subplot(gs[0, 1])
    ax_words   = fig.add_subplot(gs[0, 2])
    ax_blank1  = fig.add_subplot(gs[1, 0])
    ax_blank2  = fig.add_subplot(gs[1, 1])
    ax_blank3  = fig.add_subplot(gs[1, 2])

    # Hide unused bottom row for now
    for ax in [ax_blank1, ax_blank2, ax_blank3]:
        ax.set_visible(False)

    _bar(ax_emoji, emoji_rows, "emoji_id", "count",
         f"Top Emojis ({days}d)", "Times Used",
         ACCENT2, ACCENT,
         format_name=lambda r: _fmt_emoji(guild, r))

    _bar(ax_sticker, sticker_rows, "sticker_name", "count",
         f"Top Stickers ({days}d)", "Times Used",
         "#6e4f1a", "#f7c44f",
         format_name=lambda r: r["sticker_name"] or f"Sticker {str(r['sticker_id'])[-4:]}")

    _bar(ax_words, word_rows, "word", "count",
         f"Top Tracked Words ({days}d)", "Times Used",
         "#1a6e4f", "#4ff7a0",
         format_name=lambda r: r["word"])

    # Summary stats header
    msg_count = stats["msg_count"]
    total_sec = stats["total_seconds"]
    hours     = total_sec // 3600
    minutes   = (total_sec % 3600) // 60
    vc_str    = f"{hours}h {minutes}m" if total_sec > 0 else "None"

    fig.suptitle(
        f"{display_name}  -  Last {days} Days" + (f"  ·  {guild_name}" if guild_name else ""),
        fontsize=18, color=TEXT, fontweight="bold", y=0.97
    )
    fig.text(
        0.5, 0.90,
        f"Messages: {msg_count}   •   VC Time: {vc_str}",
        ha="center", fontsize=13, color=TEXT_DIM
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150, facecolor=BACKGROUND)
    buf.seek(0)
    plt.close(fig)
    return buf


async def user_profile(display_name, avatar_url, stats, emoji_rows, sticker_rows, word_rows, days, guild, guild_name=None):
    from bot.charts.renderer import run_in_executor
    return await run_in_executor(_draw, display_name, avatar_url, stats, emoji_rows, sticker_rows, word_rows, days, guild, guild_name)
