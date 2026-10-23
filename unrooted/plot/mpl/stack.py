from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

from unrooted.core.histogram import Histogram
from unrooted.plot._stack import prepare_stack
from unrooted.plot.style import HistogramStyle


def stack(
    hists: list[Histogram],
    ax: Axes | None = None,
    labels: list[str] | None = None,
    styles: list[HistogramStyle] | None = None,
    *,
    uncertainty: bool = True,
) -> Axes:
    """Stack additive 1D histograms in input order, first at the bottom.

    Requires exactly matching bin edges and nonnegative values. Profiles and
    efficiencies with spread bounds are rejected. A NaN value in any component
    leaves a gap in every layer of that bin; NaN variances leave gaps only in
    the total uncertainty band. Flow bins are not drawn. Inputs are not rebinned,
    normalized, or modified. Weighted yields are allowed when bins are nonnegative.

    Args:
        hists: Nonempty list of additive count/yield histograms.
        ax: Existing axes, or None to create a figure.
        labels: Optional legend labels in input order, one per component.
        styles: Per-component fill and line settings; defaults to as_stack().
            Marker, error, and spread settings do not apply to stack components.
            Supported hatches are /, backslash, x, -, |, +, and dot.
        uncertainty: Draw total ± sqrt(sum(variances)) as a gray band. This
            assumes independent components and includes no covariance. The band
            is not clipped at zero and is labeled when component labels are given.

    Returns:
        The Matplotlib axes, suitable for additional data overlays.

    Raises:
        ValueError: For incompatible bins, negative values, non-additive inputs,
            mismatched labels/styles, or nonrepresentable cumulative sums.
    """
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    data = prepare_stack(hists, labels, styles, colors, uncertainty)
    if ax is None:
        _, ax = plt.subplots()
    for i, style in enumerate(data.styles):
        label = labels[i] if labels is not None else None
        if style.fill_alpha is not None:
            ax.stairs(
                data.upper[i],
                data.edges,
                baseline=data.lower[i],
                fill=True,
                facecolor=style.fill_color,
                edgecolor=style.line_color,
                linewidth=0,
                alpha=style.fill_alpha,
                hatch=style.fill_hatch,
                label=label,
            )
            label = None
        if style.line_style is not None:
            ax.stairs(
                data.upper[i],
                data.edges,
                baseline=None,
                color=style.line_color,
                alpha=style.line_alpha,
                linewidth=style.line_width,
                linestyle=style.line_style,
                label=label,
            )
    if uncertainty:
        x = np.repeat(data.edges, 2)[1:-1]
        total = data.upper[-1]
        ax.fill_between(
            x,
            np.repeat(total - data.errors, 2),
            np.repeat(total + data.errors, 2),
            color="#303030",
            alpha=0.25,
            linewidth=0,
            label="Total ±1σ" if labels is not None else None,
        )
    if hists[0].axes[0].label:
        ax.set_xlabel(hists[0].axes[0].label)
    if hists[0].title:
        ax.set_title(hists[0].title)
    if labels is not None:
        ax.legend()
    return ax
