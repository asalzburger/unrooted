"""Example: styled 1D histogram rendering including per-bin spread.

Run with:
    uv run python tests/examples/example_styled_histogram.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from unrooted.io.root import load
from unrooted.plot.mpl import overlay, plot
from unrooted.plot.style import HistogramStyle, LineStyle
from unrooted.plot.style_set import StyleSet

DATA = Path(__file__).parent.parent / "data" / "root" / "tests_input.root"


def _add_synthetic_spread(hist, rng: np.random.Generator) -> None:
    """Fill spread_min / spread_max with plausible per-bin ranges."""
    half_width = hist.errors * (1.5 + rng.uniform(0, 1, size=hist.values.shape))
    hist.spread_min = np.maximum(hist.values - half_width, 0)
    hist.spread_max = hist.values + half_width


def main() -> None:
    rng = np.random.default_rng(42)
    ss = StyleSet.load("odd")

    hx = load(DATA, "hx")
    hy = load(DATA, "hy")
    _add_synthetic_spread(hx, rng)

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    # ── Panel 1: as_hist preset (step fill + error bars) ─────────────────────
    plot(hx, ax=axes[0, 0], style=HistogramStyle.as_hist().with_color(ss.colors[0]))
    axes[0, 0].set_title("as_hist(): fill + error bars")

    # ── Panel 2: as_line + error band ────────────────────────────────────────
    plot(
        hx,
        ax=axes[0, 1],
        style=HistogramStyle.as_line(error_display="band").with_color(ss.colors[1]),
    )
    axes[0, 1].set_title("as_line(): step line + error band")

    # ── Panel 3: as_profile preset (line + spread band) ──────────────────────
    plot(
        hx,
        ax=axes[1, 0],
        style=HistogramStyle.as_profile(
            line_style=LineStyle.DASHED
        ).with_color(ss.colors[2]),
    )
    axes[1, 0].set_title("as_profile(): dashed line + spread band")

    # ── Panel 4: overlay with ratio — B inherits its own style ───────────────
    sx = HistogramStyle.as_hist().with_color(ss.colors[0])
    sy = HistogramStyle.as_line(
        line_style=LineStyle.DASHED, line_width=2.0, error_display="bar"
    ).with_color(ss.colors[1])
    main_ax, ratio_ax = overlay(
        [hx, hy],
        ratio=True,
        labels=["hx", "hy"],
        styles=[sx, sy],
    )
    main_ax.set_title("overlay(ratio=True): B's style in ratio panel")
    axes[1, 1].axis("off")
    axes[1, 1].text(
        0.5,
        0.5,
        "Ratio figure\ndisplayed separately",
        ha="center",
        va="center",
        transform=axes[1, 1].transAxes,
    )

    fig.tight_layout()
    main_ax.get_figure().tight_layout()  # type: ignore[union-attr]
    plt.show()


if __name__ == "__main__":
    main()
