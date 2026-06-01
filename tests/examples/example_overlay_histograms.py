"""Example: overlay multiple 1D histograms with and without a ratio panel.

Run with:
    uv run python tests/examples/example_overlay_histograms.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from unrooted.io.root import load
from unrooted.plot.mpl import overlay
from unrooted.plot.style import HistogramStyle, LineStyle
from unrooted.plot.style_set import StyleSet

DATA = Path(__file__).parent.parent / "data" / "root" / "tests_input.root"


def main() -> None:
    ss = StyleSet.load("odd")
    hx = load(DATA, "hx")
    hy = load(DATA, "hy")

    # --- Simple overlay (no ratio) ---
    _, ax = plt.subplots(figsize=(7, 5))
    overlay([hx, hy], ax=ax, labels=["hx", "hy"], styles=[ss[0], ss[1]])
    ax.set_title("Overlay: hx and hy")
    ax.get_figure().tight_layout()  # type: ignore[union-attr]

    # --- Overlay with ratio panel — B's style flows into the ratio panel ---
    sx = HistogramStyle.as_hist().with_color(ss.colors[0])
    sy = HistogramStyle.as_line(
        line_style=LineStyle.DASHED, line_width=2.0, error_display="bar"
    ).with_color(ss.colors[1])
    main_ax, ratio_ax = overlay(
        [hx, hy], ratio=True, labels=["hx", "hy"], styles=[sx, sy]
    )
    main_ax.set_title("Overlay with ratio: hx (ref) vs hy — B's line style in ratio")
    main_ax.get_figure().tight_layout()  # type: ignore[union-attr]

    # --- Overlay with ratio panel and fixed ratio y-axis range ---
    main_ax2, ratio_ax2 = overlay(
        [hx, hy],
        ratio=True,
        ratio_range=(0.5, 1.5),
        labels=["hx", "hy"],
        styles=[sx, sy],
    )
    main_ax2.set_title("Overlay with ratio range [0.5, 1.5]")
    main_ax2.get_figure().tight_layout()  # type: ignore[union-attr]

    plt.show()


if __name__ == "__main__":
    main()
