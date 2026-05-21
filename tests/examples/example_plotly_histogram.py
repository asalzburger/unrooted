"""Example: interactive Plotly histogram plots.

Run with:
    uv run python tests/examples/example_plotly_histogram.py
"""
from __future__ import annotations

from pathlib import Path

from unrooted.io.root import load
from unrooted.plot.plotly import HistogramStyle, StyleSet, overlay, plot

DATA = Path(__file__).parent.parent / "data" / "root" / "tests_input.root"


def main() -> None:
    hx = load(DATA, "hx")
    hy = load(DATA, "hy")
    hxy = load(DATA, "hxy")

    # --- 1D histogram with ODD style ---
    ss = StyleSet.load("odd")
    fig1 = plot(hx, style=ss[0])
    fig1.update_layout(title="hx — ODD style")
    fig1.show()

    # --- 2D histogram ---
    fig2 = plot(hxy)
    fig2.update_layout(title="hxy — 2D heatmap")
    fig2.show()

    # --- Overlay with ratio panel ---
    fig3 = overlay(
        [hx, hy],
        labels=["hx", "hy"],
        styles=[
            HistogramStyle(line_color="#1A4F8A", fill_alpha=0.10, error_display="bar"),
            HistogramStyle(line_color="#E8921A", line_style="--", error_display="band"),
        ],
        ratio=True,
    )
    fig3.update_layout(title="Overlay: hx vs hy with ratio")
    fig3.show()


if __name__ == "__main__":
    main()
