from __future__ import annotations

from typing import cast

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes as MplAxes

from unrooted.core.histogram import Histogram
from unrooted.plot.mpl._range import _draw_range
from unrooted.plot.mpl.histogram import _plot_1d_styled
from unrooted.plot.style import HistogramStyle


def _default_style(color: str | tuple[float, ...]) -> HistogramStyle:
    return HistogramStyle(line_color=color)


def overlay(
    hists: list[Histogram],
    ax: MplAxes | None = None,
    ratio: bool = False,
    labels: list[str] | None = None,
    styles: list[HistogramStyle] | None = None,
    **kwargs,
) -> tuple[MplAxes, MplAxes | None]:
    if not hists or len(hists) == 0:
        raise ValueError("hists must not be empty")
    if any(h.ndim != 1 for h in hists):
        raise ValueError("overlay only supports 1D histograms")
    if labels is not None and len(labels) != len(hists):
        raise ValueError("labels must have the same length as hists")
    if styles is not None and len(styles) != len(hists):
        raise ValueError("styles must have the same length as hists")
    if ax is not None and ratio:
        raise ValueError("ax cannot be supplied when ratio=True")

    ax_ratio: MplAxes | None = None
    main_ax: MplAxes

    if ratio:
        _, subaxes = plt.subplots(
            2, 1, gridspec_kw={"height_ratios": [3, 1]}, sharex=True
        )
        main_ax = cast(MplAxes, subaxes[0])
        ax_ratio = cast(MplAxes, subaxes[1])
    elif ax is not None:
        main_ax = ax
    else:
        _, main_ax = plt.subplots()

    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    for i, hist in enumerate(hists):
        auto_color: str | tuple[float, ...] = colors[i % len(colors)]
        style = styles[i] if styles is not None else _default_style(auto_color)
        # Ensure a color is set so ratio panel can pick the same colour.
        if style.line_color is None:
            style = HistogramStyle(
                **{**style.__dict__, "line_color": auto_color}
            )
        label = labels[i] if labels is not None else None
        _plot_1d_styled(hist, main_ax, style, label=label, set_axis_labels=False)

    if hists[0].axes[0].label:
        xlabel_ax = ax_ratio if ax_ratio is not None else main_ax
        xlabel_ax.set_xlabel(hists[0].axes[0].label)

    if labels is not None:
        main_ax.legend()

    if ax_ratio is not None:
        _draw_ratio_panel(hists, ax_ratio, colors)

    return main_ax, ax_ratio


def _draw_ratio_panel(
    hists: list[Histogram],
    ax_ratio: MplAxes,
    colors: list[str],
) -> None:
    ref_values = hists[0].values
    ref_errors = hists[0].errors
    edges = hists[0].axes[0].edges
    centers = hists[0].axes[0].centers

    for i, hist in enumerate(hists[1:], start=1):
        color = colors[i % len(colors)]
        with np.errstate(invalid="ignore", divide="ignore"):
            r = np.where(ref_values != 0, hist.values / ref_values, np.nan)
            sigma_r = np.where(
                ref_values != 0,
                np.sqrt(
                    (hist.errors / ref_values) ** 2
                    + (hist.values * ref_errors / ref_values**2) ** 2
                ),
                np.nan,
            )
        ax_ratio.stairs(r, edges, color=color)
        _draw_range(
            ax_ratio,
            centers=centers,
            values=r,
            lo=r - sigma_r,
            hi=r + sigma_r,
            edges=edges,
            mode="bar",
            color=color,
            alpha=1.0,
            capsize=2.0,
        )

    ax_ratio.axhline(1.0, color="black", linestyle="--", linewidth=0.8)
    ax_ratio.set_ylabel("Ratio")
        ref_values = hists[0].values
        ref_errors = hists[0].errors
        edges = hists[0].axes[0].edges
        centers = hists[0].axes[0].centers

        for i, hist in enumerate(hists[1:], start=1):
            color = colors[i % len(colors)]
            with np.errstate(invalid="ignore", divide="ignore"):
                r = np.where(ref_values != 0, hist.values / ref_values, np.nan)
                sigma_r = np.where(
                    ref_values != 0,
                    np.sqrt(
                        (hist.errors / ref_values) ** 2
                        + (hist.values * ref_errors / ref_values**2) ** 2
                    ),
                    np.nan,
                )
            ax_ratio.stairs(r, edges, color=color)
            ax_ratio.errorbar(
                centers, r, yerr=sigma_r, fmt="none", color=color, capsize=2
            )

        ax_ratio.axhline(1.0, color="black", linestyle="--", linewidth=0.8)
        ax_ratio.set_ylabel("Ratio")

    return main_ax, ax_ratio
