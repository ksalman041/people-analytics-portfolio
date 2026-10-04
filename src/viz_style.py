"""
viz_style.py - one source of truth for colours and type in every Python-made visual.

Uses the same tokens as powerbi/theme.json, so a matplotlib chart in a memo looks like
it came from the same report as the Power BI pages. See docs/viz_style_guide.md for
the rules behind each token.

Usage:
    from viz_style import TOKENS, apply, message_title
    apply()
    fig, ax = plt.subplots()
    message_title(ax, "Operations loses 1 in 5 people a year", "Turnover, rolling 12 months, %")
"""

from __future__ import annotations

import matplotlib as mpl

TOKENS = {
    # Surfaces
    "page": "#f9f9f7",
    "card": "#ffffff",
    "card_border": "#e1e0d9",
    # Ink (text never wears a data colour)
    "ink": "#0b0b0b",  # titles, values - 19.7:1 on white
    "ink_2": "#52514e",  # axis labels, subtitles - 7.9:1
    "muted": "#898781",  # marks only (3.6:1) - never text
    "grid": "#e1e0d9",
    "baseline": "#c3c2b7",
    # Data
    "accent": "#2a78d6",  # the focus: actuals / the one series that matters
    "context": "#898781",  # previous year / the rest
    "series": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"],  # categorical, fixed order
    "sequential": ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"],
    # Status - only on variances, always with an arrow and a sign
    "good": "#0ca30c",
    "good_text": "#006300",
    "bad": "#d03b3b",
    "warning": "#fab219",
}

FONT = ["Segoe UI", "DejaVu Sans", "Arial", "sans-serif"]


def apply() -> None:
    """Set matplotlib defaults to the house style."""
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": FONT,
        "font.size": 10,
        "text.color": TOKENS["ink"],
        "axes.edgecolor": TOKENS["baseline"],
        "axes.labelcolor": TOKENS["ink_2"],
        "axes.titlecolor": TOKENS["ink"],
        "axes.facecolor": TOKENS["card"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.axisbelow": True,
        "axes.prop_cycle": mpl.cycler(color=TOKENS["series"]),
        "grid.color": TOKENS["grid"],
        "grid.linewidth": 0.8,
        "grid.linestyle": "-",
        "xtick.color": TOKENS["ink_2"],
        "ytick.color": TOKENS["ink_2"],
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "lines.linewidth": 2,
        "lines.solid_capstyle": "round",
        "legend.frameon": False,
        "figure.facecolor": TOKENS["card"],
        "savefig.facecolor": TOKENS["card"],
        "savefig.dpi": 200,
    })


def message_title(ax, title: str, subtitle: str = "") -> None:
    """IBCS 'Say': the title states the message; the subtitle names measure, unit and period."""
    ax.set_title("")
    ax.text(0, 1.12 if subtitle else 1.04, title, transform=ax.transAxes, fontsize=13,
            fontweight="semibold", color=TOKENS["ink"], ha="left", va="bottom")
    if subtitle:
        ax.text(0, 1.03, subtitle, transform=ax.transAxes, fontsize=9.5, color=TOKENS["ink_2"],
                ha="left", va="bottom")


def emphasis_colors(labels: list[str], focus: str | set[str]) -> list[str]:
    """Accent for the focus bar(s), context grey for the rest."""
    focus = {focus} if isinstance(focus, str) else set(focus)
    return [TOKENS["accent"] if label in focus else TOKENS["context"] for label in labels]
