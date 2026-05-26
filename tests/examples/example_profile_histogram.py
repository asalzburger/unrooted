"""Example: load a TProfile histogram and plot it with spread bands.

Run with:
    uv run python tests/examples/example_profile_histogram.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from unrooted.io.root import load
from unrooted.plot.mpl import overlay, plot
from unrooted.plot.style import HistogramStyle
from unrooted.plot.style_set import StyleSet

DATA = Path(__file__).parent.parent / "data" / "root" / "tests_input.root"


def main() -> None:
    ss = StyleSet.load("odd")

    prof_x = load(DATA, "profX")
    prof_y = load(DATA, "profY")

    # TProfile: values = per-bin means, spread_min/max = mean ± σ_y
    print(f"profX: ndim={prof_x.ndim}, bins={prof_x.values.shape[0]}")
    print(f"  spread available: {prof_x.spread_min is not None}")

    # --- Single TProfile with spread band ---
    style_spread = HistogramStyle(
        line_color=ss[0].line_color,
        fill_alpha=0.15,
        error_display="bar",
        spread_display="band",
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    plot(prof_x, ax=ax, style=style_spread)
    ax.set_title("TProfile: mean per bin with σ_y spread band")
    fig.tight_layout()

    # --- Overlay two profiles ---
    style_x = HistogramStyle(
        line_color=ss[0].line_color, error_display="bar", spread_display="band"
    )
    style_y = HistogramStyle(
        line_color=ss[1].line_color, line_style="--",
        error_display="bar", spread_display="band",
    )
    main_ax, _ = overlay(
        [prof_x, prof_y],
        labels=["profX", "profY"],
        styles=[style_x, style_y],
        ratio=True,
    )
    main_ax.set_title("TProfile overlay: profX (ref) vs profY")
    main_ax.get_figure().tight_layout()  # type: ignore[union-attr]

    plt.show()


if __name__ == "__main__":
    main()
