"""Example: overlay multiple 1D histograms with and without a ratio panel.

Run with:
    uv run python tests/examples/example_overlay_histograms.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from unrooted.io.root import load
from unrooted.plot.mpl import overlay, stamp

DATA = Path(__file__).parent.parent / "data" / "root" / "tests_input.root"


def main() -> None:
    hx = load(DATA, "hx")
    hy = load(DATA, "hy")

    # --- Simple overlay (no ratio) ---
    _, ax = plt.subplots(figsize=(7, 5))
    overlay([hx, hy], ax=ax, labels=["hx", "hy"])
    stamp(ax, logo="sd", variant="line", loc="upper right", zoom=0.12)
    ax.set_title("Overlay: hx and hy")
    ax.get_figure().tight_layout()  # type: ignore[union-attr]

    # --- Overlay with ratio panel (creates its own figure) ---
    main_ax, ratio_ax = overlay([hx, hy], ratio=True, labels=["hx", "hy"])
    main_ax.set_title("Overlay with ratio: hx (ref) vs hy")
    main_ax.get_figure().tight_layout()  # type: ignore[union-attr]

    plt.show()


if __name__ == "__main__":
    main()
