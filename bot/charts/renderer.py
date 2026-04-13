import asyncio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

BACKGROUND = "#0a0e1a"
SURFACE    = "#0d1117"
SURFACE2   = "#161b27"
TEXT       = "#c9d1e0"
TEXT_DIM   = "#5a6a8a"
ACCENT     = "#4f8ef7"
ACCENT2    = "#7b5ea7"
GLOW       = "#3a6fd8"

def apply_theme(fig, ax):
    fig.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.xaxis.label.set_color(TEXT_DIM)
    ax.yaxis.label.set_color(TEXT_DIM)
    ax.title.set_color(TEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(SURFACE2)
        spine.set_linewidth(0.5)
    ax.grid(True, color=SURFACE2, linewidth=0.5, alpha=0.8)
    ax.set_axisbelow(True)

def glow_effect():
    return [
        pe.withStroke(linewidth=6, foreground=GLOW, alpha=0.3),
        pe.withStroke(linewidth=3, foreground=ACCENT, alpha=0.2),
        pe.Normal()
    ]

async def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args))