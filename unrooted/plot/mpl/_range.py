from __future__ import annotations

from typing import Literal

import numpy as np
from matplotlib.axes import Axes as MplAxes


def _draw_range(
    ax: MplAxes,
    centers: np.ndarray,
    values: np.ndarray,
    lo: np.ndarray,
    hi: np.ndarray,
    edges: np.ndarray,
    mode: Literal["bar", "band"],
    color: str | tuple[float, ...],
    alpha: float,
    capsize: float = 2.0,
) -> None:
    """Draw error bars or a filled band between *lo* and *hi*.

    Args:
        centers: Bin centre x-positions.
        values:  Bin y-values (midpoints for asymmetric bar errors).
        lo:      Absolute lower bound per bin.
        hi:      Absolute upper bound per bin.
        edges:   Bin edges (used to build the step shape for band mode).
        mode:    ``"bar"`` for error bars, ``"band"`` for a filled band.
        color:   Matplotlib color spec.
        alpha:   Opacity.
        capsize: Cap size in points (bar mode only).
    """
    if mode == "bar":
        ax.errorbar(
            centers,
            values,
            yerr=[values - lo, hi - values],
            fmt="none",
            color=color,
            alpha=alpha,
            capsize=capsize,
        )
    else:
        x_step = np.repeat(edges, 2)[1:-1]
        lo_step = np.repeat(lo, 2)
        hi_step = np.repeat(hi, 2)
        ax.fill_between(x_step, lo_step, hi_step, color=color, alpha=alpha)
