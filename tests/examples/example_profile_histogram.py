"""Example: load a TProfile histogram and plot it with spread bands.

Run with:
    uv run python tests/examples/example_profile_histogram.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from unrooted.io.root import load
from unrooted.plot.mpl import overlay, plot
from unrooted.plot.style import HistogramStyle, LineStyle
from unrooted.plot.style_set import StyleSet

DATA = Path(__file__).parent.parent / "data" / "root" / "tests_input.root"


def main() -> None:
    ss = StyleSet.load("odd")

    prof_x = load(DATA, "profX")
    prof_y = load(DATA, "profY")

    print(f"profX: ndim={prof_x.ndim}, bins={prof_x.values.shape[0]}")
    print(f"  spread available: {prof_x.spread_min is not None}")

    # --- Single TProfile with spread band using as_profile() preset ---
    fig, ax = plt.subplots(figsize=(8, 5))
    plot(prof_x, ax=ax, style=HistogramStyle.as_profile().with_color(ss.colors[0]))
    ax.set_title("TProfile: mean per bin with σ_y spread band")
    fig.tight_layout()

    # --- Overlay two profiles — B's dashed style flows into the ratio panel ---
    sx = HistogramStyle.as_profile().with_color(ss.colors[0])
    sy = HistogramStyle.as_profile(line_style=LineStyle.DASHED).with_color(ss.colors[1])
    main_ax, _ = overlay(
        [prof_x, prof_y],
        labels=["profX", "profY"],
        styles=[sx, sy],
        ratio=True,
    )
    main_ax.set_title("TProfile overlay: profX (ref) vs profY")
    main_ax.get_figure().tight_layout()  # type: ignore[union-attr]

    plt.show()


if __name__ == "__main__":
    main()
