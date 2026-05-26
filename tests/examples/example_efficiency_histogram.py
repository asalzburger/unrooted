"""Example: load efficiency from pass/total TH1 histograms and plot it.

Run with:
    uv run python tests/examples/example_efficiency_histogram.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from unrooted.io.root import load_efficiency
from unrooted.plot.mpl import plot
from unrooted.plot.style import HistogramStyle
from unrooted.plot.style_set import StyleSet

DATA = Path(__file__).parent.parent / "data" / "root" / "tests_efficiency.root"


def main() -> None:
    ss = StyleSet.load("odd")

    eff = load_efficiency(DATA, "h_passed", "h_total")

    print(f"efficiency: ndim={eff.ndim}, bins={eff.values.shape[0]}")
    print(f"  values range: [{eff.values.min():.3f}, {eff.values.max():.3f}]")
    print(f"  spread available: {eff.spread_min is not None}")

    # Plot efficiency with Gaussian ±σ error bars and CI band
    style_bar = HistogramStyle(
        line_color=ss[0].line_color,
        marker="o",
        marker_size=5,
        fill_alpha=0.12,
        error_display="bar",
        spread_display="band",
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    plot(eff, ax=ax, style=style_bar)
    ax.set_ylim(0, 1.1)
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8)
    ax.set_title("Efficiency: passed / total with ±σ Gaussian CI")
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
