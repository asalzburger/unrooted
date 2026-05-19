from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.axes import Axes as MplAxes

from unrooted.core.histogram import Histogram


def plot(hist: Histogram, ax: MplAxes | None = None, **kwargs) -> MplAxes:
    if ax is None:
        _, ax = plt.subplots()
    if hist.ndim == 1:
        return _plot_1d(hist, ax, **kwargs)
    if hist.ndim == 2:
        return _plot_2d(hist, ax, **kwargs)
    raise ValueError(f"Cannot plot {hist.ndim}D histogram")


def _plot_1d(hist: Histogram, ax: MplAxes, **kwargs) -> MplAxes:
    edges = hist.axes[0].edges
    values = hist.values
    centers = hist.axes[0].centers

    stairs_kwargs = {k: v for k, v in kwargs.items() if k not in ("capsize",)}
    ax.stairs(values, edges, **stairs_kwargs)
    ax.errorbar(
        centers,
        values,
        yerr=hist.errors,
        fmt="none",
        color="black",
        capsize=kwargs.get("capsize", 2),
    )

    if hist.axes[0].label:
        ax.set_xlabel(hist.axes[0].label)
    if hist.title:
        ax.set_title(hist.title)
    return ax


def _plot_2d(hist: Histogram, ax: MplAxes, **kwargs) -> MplAxes:
    x_edges = hist.axes[0].edges
    y_edges = hist.axes[1].edges

    mesh = ax.pcolormesh(x_edges, y_edges, hist.values.T, **kwargs)
    plt.colorbar(mesh, ax=ax)

    if hist.axes[0].label:
        ax.set_xlabel(hist.axes[0].label)
    if hist.axes[1].label:
        ax.set_ylabel(hist.axes[1].label)
    if hist.title:
        ax.set_title(hist.title)
    return ax
