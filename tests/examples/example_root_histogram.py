"""Example: load histograms from a ROOT file and plot them with detector logo stamps.

Run with:
    uv run python tests/examples/example_root_histogram.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from unrooted.io.root import load
from unrooted.plot.mpl import plot, stamp

DATA = Path(__file__).parent.parent / "data" / "root" / "tests_input.root"


def main() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # --- 1D histogram with sample detector logo ---
    h1d = load(DATA, "hx")
    plot(h1d, ax=axes[0])
    stamp(axes[0], logo="sd", variant="full", loc="upper right", zoom=0.15)

    # --- 2D histogram with open data detector logo (line variant) ---
    h2d = load(DATA, "hxy")
    plot(h2d, ax=axes[1])
    stamp(axes[1], logo="odd", variant="line", loc="upper right", zoom=0.15)

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
