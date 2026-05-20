from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import awkward as ak
import numpy as np
import uproot

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram


def load_branch(
    path: str | Path,
    key: str,
    branch: str,
    *,
    n_bins: int = 100,
    range: tuple[float, float] | None = None,  # noqa: A002
    profile: bool = False,
    label: str = "",
) -> Histogram:
    """Load a TTree branch as a 1D count or profile histogram.

    Scalar, ``std::vector<T>`` and ``std::vector<std::vector<T>>`` branch
    types are all flattened to a 1D array before histogramming.

    Args:
        path:    Path to the ROOT file.
        key:     Tree name inside the file, e.g. ``"tree"`` or ``"jagged_tree"``.
        branch:  Branch name, e.g. ``"x"`` or ``"xj"``.
        n_bins:  Number of bins (default 100).
        range:   ``(lo, hi)`` bin range.  Auto-detected from data if ``None``.
        profile: If ``True`` return a profile histogram (per-bin mean ± SE,
                 with ``spread_min``/``spread_max`` set to per-bin min/max).
                 If ``False`` (default) return a count histogram.
        label:   Axis label; defaults to the branch name.
    """
    with cast(Any, uproot.open(path)) as f:
        arr = f[key][branch].array(library="ak")

    data = np.asarray(ak.flatten(arr, axis=None), dtype=float)  # type: ignore[arg-type]
    axis_label = label or branch

    lo: float
    hi: float
    if range is not None:
        lo, hi = range
    else:
        lo, hi = float(data.min()), float(data.max())
        if lo == hi:
            lo, hi = lo - 0.5, lo + 0.5

    edges = np.linspace(lo, hi, n_bins + 1)

    if not profile:
        return _count_histogram(data, edges, branch, axis_label)
    return _profile_histogram(data, edges, branch, axis_label)


# ---------------------------------------------------------------------------
# Internal builders
# ---------------------------------------------------------------------------


def _count_histogram(
    data: np.ndarray,
    edges: np.ndarray,
    name: str,
    label: str,
) -> Histogram:
    values, _ = np.histogram(data, bins=edges)
    values = values.astype(float)
    return Histogram(
        axes=[Axis(edges=edges, label=label)],
        values=values,
        variances=values.copy(),
        name=name,
    )


def _profile_histogram(
    data: np.ndarray,
    edges: np.ndarray,
    name: str,
    label: str,
) -> Histogram:
    n_bins = len(edges) - 1
    lo, hi = edges[0], edges[-1]

    # Assign each value to a 0-based bin index.
    # searchsorted on the inner edges gives the correct 0-based index for
    # values in [lo, hi].  Values equal to `hi` land in the last bin.
    in_range = (data >= lo) & (data <= hi)
    data_valid = data[in_range]
    idx = np.searchsorted(edges[1:], data_valid)          # 0 .. n_bins
    idx = np.clip(idx, 0, n_bins - 1)

    # Per-bin count and sum (for mean).
    counts = np.zeros(n_bins, dtype=np.intp)
    sums = np.zeros(n_bins)
    sum_sq = np.zeros(n_bins)
    np.add.at(counts, idx, 1)
    np.add.at(sums, idx, data_valid)
    np.add.at(sum_sq, idx, data_valid**2)

    # Per-bin min / max via ufunc.at.
    mins = np.full(n_bins, np.inf)
    maxs = np.full(n_bins, -np.inf)
    np.minimum.at(mins, idx, data_valid)
    np.maximum.at(maxs, idx, data_valid)

    # Finalise statistics.
    has_data = counts > 0
    means = np.where(has_data, sums / np.where(has_data, counts, 1), 0.0)
    # Population variance: E[X²] - (E[X])²
    pop_var = np.where(
        has_data,
        sum_sq / np.where(has_data, counts, 1) - means**2,
        0.0,
    )
    # Variance of the mean (SE²) = pop_var / n
    var_means = np.where(has_data, pop_var / np.where(has_data, counts, 1), 0.0)

    mins = np.where(has_data, mins, np.nan)
    maxs = np.where(has_data, maxs, np.nan)

    return Histogram(
        axes=[Axis(edges=edges, label=label)],
        values=means,
        variances=var_means,
        name=name,
        spread_min=mins,
        spread_max=maxs,
    )
