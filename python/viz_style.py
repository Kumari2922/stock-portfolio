"""Shared chart styling.

One place for the palette and matplotlib defaults so every figure in
reports/figures/ reads as one system. Colour is assigned per ticker (identity
follows the entity, never its rank), so a stock keeps the same hue in every
chart regardless of how it sorts.
"""

from __future__ import annotations

import matplotlib as mpl

# Validated categorical palette, assigned in fixed slot order.
CATEGORICAL = [
    "#2a78d6",  # 1 blue
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 yellow
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 green
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 red
]

# Fixed ticker -> slot assignment, in portfolio-weight order.
TICKER_ORDER = ["AAPL", "MSFT", "NVDA", "AMZN", "TSLA", "RY", "TD", "SHOP"]
TICKER_COLOR = dict(zip(TICKER_ORDER, CATEGORICAL))

SECTOR_COLOR = {
    "Technology": CATEGORICAL[0],
    "Consumer Discretionary": CATEGORICAL[1],
    "Banking": CATEGORICAL[2],
}

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#8a8a84"
GRID = "#e4e3df"

# Diverging pair for correlation and signed returns: blue <-> red, gray midpoint.
DIVERGING = ["#0d366b", "#2a78d6", "#9ec5f4", "#f0efec", "#f3a3a2", "#e34948", "#9e2c2b"]
SEQUENTIAL_BLUE = "#2a78d6"


def apply_style() -> None:
    mpl.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": GRID,
            "axes.labelcolor": TEXT_SECONDARY,
            "axes.titlecolor": TEXT_PRIMARY,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.titlepad": 14,
            "axes.labelsize": 10,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "xtick.color": TEXT_SECONDARY,
            "ytick.color": TEXT_SECONDARY,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "legend.frameon": False,
            "legend.fontsize": 9,
            "lines.linewidth": 2.0,
            "font.size": 10,
            "figure.dpi": 130,
            "savefig.dpi": 130,
            "savefig.bbox": "tight",
        }
    )
    for spine in ("top", "right"):
        mpl.rcParams[f"axes.spines.{spine}"] = False


def caption(fig, text: str) -> None:
    """One-line source / interpretation note under a figure."""
    fig.text(0.0, -0.02, text, ha="left", va="top", fontsize=8.5, color=TEXT_MUTED, wrap=True)
