from __future__ import annotations

from typing import cast

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes as MplAxes

from unrooted.core.histogram import Histogram


def overlay(
    hists: list[Histogram],
    ax: MplAxes | None = None,
    ratio: bool = False,
    labels: list[str] | None = None,
    **kwargs,
) -> tuple[MplAxes, MplAxes | None]:
    if any(h.ndim != 1 for h in hists):
        raise ValueError("overlay only supports 1D histograms")
    if labels is not None and len(labels) != len(hists):
        raise ValueError("labels must have the same length as hists")
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
        color = colors[i % len(colors)]
        label = labels[i] if labels is not None else None
        edges = hist.axes[0].edges
        centers = hist.axes[0].centers
        main_ax.stairs(hist.values, edges, color=color, label=label, **kwargs)
        main_ax.errorbar(
            centers,
            hist.values,
            yerr=hist.errors,
            fmt="none",
            color=color,
            capsize=2,
        )

    if hists[0].axes[0].label:
        xlabel_ax = ax_ratio if ax_ratio is not None else main_ax
        xlabel_ax.set_xlabel(hists[0].axes[0].label)

    if labels is not None:
        main_ax.legend()

    if ax_ratio is not None:
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
