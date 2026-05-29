"""Example: compare the three spread display modes — bar, band, continuous.

All three modes show the same spread_min / spread_max data on the same
histogram so the visual difference is clear side-by-side.

Run with:
    uv run python tests/examples/example_spread_modes.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from unrooted.io.root import load
from unrooted.plot.mpl import plot
from unrooted.plot.style import HistogramStyle
from unrooted.plot.style_set import StyleSet

DATA = Path(__file__).parent.parent / "data" / "root" / "tests_input.root"


def main() -> None:
    ss = StyleSet.load("odd")
    prof = load(DATA, "profX")

    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
    fig.suptitle("Spread display modes: bar / band / continuous")

    # ── "bar": error-bar style tick marks at bin centres ─────────────────────
    plot(
        prof,
        ax=axes[0],
        style=HistogramStyle.as_profile(spread_display="bar").with_color(ss.colors[0]),
    )
    axes[0].set_title('"bar" — ticks at bin centres')

    # ── "band": step-shaped fill following bin edges ──────────────────────────
    plot(
        prof,
        ax=axes[1],
        style=HistogramStyle.as_profile(spread_display="band").with_color(ss.colors[1]),
    )
    axes[1].set_title('"band" — step-shaped fill')

    # ── "continuous": smooth fill_between connecting bin centres ─────────────
    plot(
        prof,
        ax=axes[2],
        style=HistogramStyle.as_profile(spread_display="continuous").with_color(
            ss.colors[2]
        ),
    )
    axes[2].set_title('"continuous" — smooth envelope')

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
