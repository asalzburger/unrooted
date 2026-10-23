"""Reproduce the stacked histogram gallery and PR figure with the public API.

python -I tests/examples/example_stacked_histogram.py /tmp/stack-example --plotly
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from unrooted.core import Axis, Histogram
from unrooted.plot import HistogramStyle
from unrooted.plot.mpl import stack


def render(output_dir: Path, *, include_plotly: bool = False) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    edges = np.arange(40.0, 205.0, 5.0)
    centers = (edges[:-1] + edges[1:]) / 2
    # Synthetic expected yields; independent Poisson variances for each process.
    values = [
        105 * np.exp(-(centers - 40) / 65),
        46 * np.exp(-0.5 * ((centers - 90) / 18) ** 2),
        32 * np.exp(-0.5 * ((centers - 125) / 8) ** 2),
    ]
    hists = [
        Histogram(
            [Axis(edges, label="Mass [GeV]")], v, v.copy(), title="Stacked event yields"
        )
        for v in values
    ]
    labels = ["Continuum background", "Resonant background", "Signal"]
    colors = ["#356B9A", "#E5A044", "#438C70"]
    styles = [
        HistogramStyle.as_stack(fill_alpha=0.85, line_width=1).with_color(c)
        for c in colors
    ]
    fig, ax = plt.subplots(figsize=(8, 5.2))
    stack(hists, ax=ax, labels=labels, styles=styles)
    ax.set_ylabel("Events / 5 GeV")
    ax.set_xlim(edges[0], edges[-1])
    ax.set_ylim(0, 150)
    ax.set_title("Stacked event yields", loc="left", weight="bold", pad=14)
    ax.set_title("")  # Replace the inherited centered title with the left title.
    ax.text(
        1,
        1.02,
        "Synthetic example",
        transform=ax.transAxes,
        ha="right",
        color="#666666",
        fontsize=9,
    )
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#E5E7EB", linewidth=0.7)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    fig.tight_layout()
    fig.savefig(output_dir / "mpl_stack.png", dpi=160)
    plt.close(fig)

    if include_plotly:
        from unrooted.plot.plotly import stack as interactive_stack

        interactive = interactive_stack(hists, labels=labels, styles=styles)
        interactive.update_layout(
            template="plotly_white",
            yaxis_title="Events / 5 GeV",
            yaxis_range=[0, 150],
            xaxis_range=[40, 200],
            margin=dict(l=65, r=25, t=65, b=55),
        )
        interactive.write_html(output_dir / "plotly_stack.html", include_plotlyjs="cdn")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--plotly", action="store_true")
    args = parser.parse_args()
    render(args.output_dir, include_plotly=args.plotly)
