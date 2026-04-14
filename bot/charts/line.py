import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patheffects as pe
from datetime import timedelta
from bot.charts.renderer import apply_theme, BACKGROUND, ACCENT, ACCENT2, TEXT, TEXT_DIM

def _draw(dates, values, title, ylabel):
    # Strip timezone info so matplotlib date handling works consistently
    dates = [d.replace(tzinfo=None) if getattr(d, "tzinfo", None) is not None else d for d in dates]

    fig, ax = plt.subplots(figsize=(13, 5))
    apply_theme(fig, ax)

    # Fix x-axis range to always show the full 30 day window
    if dates:
        x_min = min(dates) - timedelta(days=1)
        x_max = max(dates) + timedelta(days=1)
        ax.set_xlim(x_min, x_max)

    if len(dates) == 1:
        # Single point — just show a dot with a label
        ax.scatter(dates, values, color=ACCENT, s=100, zorder=5)
        ax.text(dates[0], values[0] + 0.1, str(values[0]),
                ha="center", color=TEXT, fontsize=10, fontweight="bold")
    else:
        line, = ax.plot(
            dates, values,
            color=ACCENT, linewidth=2.5,
            marker="o", markersize=5,
            markerfacecolor=ACCENT,
            markeredgecolor=BACKGROUND,
            markeredgewidth=1.5,
            zorder=5
        )
        line.set_path_effects([
            pe.withStroke(linewidth=8, foreground=ACCENT, alpha=0.2),
            pe.Normal()
        ])
        ax.fill_between(dates, values, alpha=0.08, color=ACCENT)
        ax.fill_between(dates, values, alpha=0.04, color=ACCENT2)

        if values:
            peak_idx = values.index(max(values))
            ax.annotate(
                f"Peak: {max(values)}",
                xy=(dates[peak_idx], values[peak_idx]),
                xytext=(10, 12), textcoords="offset points",
                color=ACCENT, fontsize=8,
                arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1),
            )

    # Always show clean date labels
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates) // 8)))
    plt.xticks(rotation=45, ha="right", fontsize=8)

    fig.suptitle(title, fontsize=14, fontweight="bold", color=TEXT, y=1.01)
    ax.set_ylabel(ylabel, color=TEXT_DIM)
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150, facecolor=BACKGROUND)
    buf.seek(0)
    plt.close(fig)
    return buf

async def line_chart(dates, values, title, ylabel):
    from bot.charts.renderer import run_in_executor
    return await run_in_executor(_draw, dates, list(values), title, ylabel)