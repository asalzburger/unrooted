"""Example: styled 1D histogram rendering including per-bin spread.

Run with:
    uv run python tests/examples/example_styled_histogram.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from unrooted.io.root import load
from unrooted.plot.mpl import HistogramStyle, overlay, plot

DATA = Path(__file__).parent.parent / "data" / "root" / "tests_input.root"


def _add_synthetic_spread(hist, rng: np.random.Generator) -> None:
    """Fill spread_min / spread_max with plausible per-bin ranges."""
    half_width = hist.errors * (1.5 + rng.uniform(0, 1, size=hist.values.shape))
    hist.spread_min = np.maximum(hist.values - half_width, 0)
    hist.spread_max = hist.values + half_width


def main() -> None:
    rng = np.random.default_rng(42)
    hx = load(DATA, "hx")
    hy = load(DATA, "hy")
    _add_synthetic_spread(hx, rng)

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    # ── Panel 1: default style (step line + error bars) ──────────────────────
    plot(hx, ax=axes[0, 0], style=HistogramStyle())
    axes[0, 0].set_title("Default: line + error bars")

    # ── Panel 2: line + filled area + error band ──────────────────────────────
    plot(
        hx,
        ax=axes[0, 1],
        style=HistogramStyle(
            line_color="C0",
            fill_alpha=0.15,
            error_display="band",
            error_color="C0",
            error_alpha=0.4,
        ),
    )
    axes[0, 1].set_title("Line + fill + error band")

    # ── Panel 3: markers + error bars + spread band ───────────────────────────
    plot(
        hx,
        ax=axes[1, 0],
        style=HistogramStyle(
            line_color="C2",
            line_style="--",
            marker="o",
            marker_size=4,
            error_display="bar",
            spread_display="band",
            spread_color="C2",
            spread_alpha=0.20,
        ),
    )
    axes[1, 0].set_title("Markers + error bars + spread band")

    # ── Panel 4: overlay hx/hy with custom styles + ratio ────────────────────
    sx = HistogramStyle(
        line_color="C0",
        fill_alpha=0.10,
        error_display="bar",
    )
    sy = HistogramStyle(
        line_color="C1",
        line_style="--",
        error_display="band",
        error_alpha=0.30,
    )
    main_ax, ratio_ax = overlay(
        [hx, hy],
        ratio=True,
        labels=["hx", "hy"],
        styles=[sx, sy],
    )
    main_ax.set_title("Overlay with ratio: hx (ref) vs hy")
    # Move the ratio panel into the grid (it was created in its own figure).
    # For simplicity, just show the fourth subplot empty and display separately.
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
