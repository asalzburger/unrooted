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
    x_branch: str,
    y_branch: str | None = None,
    *,
    n_bins: int = 100,
    range: tuple[float, float] | None = None,  # noqa: A002
    label: str = "",
) -> Histogram:
    """Load a TTree branch (or branch pair) as a 1-D count or profile histogram.

    When called with only *x_branch*, every value in that branch is counted
    into a 1-D histogram.  Scalar, ``std::vector<T>``, and
    ``std::vector<std::vector<T>>`` branch types are all flattened first.

    When *y_branch* is also given, returns a **profile histogram**: *x_branch*
    drives the bin axis and in each x-bin the mean, standard error, and
    spread (min/max) of the corresponding *y_branch* values are stored.  The
    two branches are aligned with :func:`awkward.broadcast_arrays`, which
    supports:

    1. Trivial × Trivial — scalar × scalar, event-by-event pairing
    2. Trivial × Vector — scalar × ``std::vector<T>`` (each scalar x is
       broadcast to every element of the y-vector in the same event)
    3. Trivial × Jagged — scalar × ``std::vector<std::vector<T>>``
    4. Vector × Vector — same-shape ``std::vector<T>`` pairs, zipped per event
    5. Vector × Jagged — ``std::vector<T>`` × ``std::vector<std::vector<T>>``
       when the outer y-length matches x per event

    Incompatible branch shapes raise a ``ValueError`` from awkward-array.

    Args:
        path:     Path to the ROOT file.
        key:      Tree name inside the file.
        x_branch: Branch used for x-axis binning (and as the sole branch for
                  count histograms).
        y_branch: Branch whose values are profiled per x-bin.  When ``None``
                  (default) a count histogram of *x_branch* is returned.
        n_bins:   Number of bins (default 100).
        range:    ``(lo, hi)`` bin range; auto-detected from *x_branch* data
                  if ``None``.
        label:    X-axis label; defaults to *x_branch*.
    """
    with cast(Any, uproot.open(path)) as f:
        x_ak = f[key][x_branch].array(library="ak")
        y_ak: Any = (
            f[key][y_branch].array(library="ak") if y_branch is not None else None
        )

    # Range is always derived from the original x values (before broadcasting).
    x_orig = np.asarray(ak.flatten(x_ak, axis=None), dtype=float)  # type: ignore[arg-type]
    lo, hi = _resolve_range(x_orig, range)
    edges = np.linspace(lo, hi, n_bins + 1)
    axis_label = label or x_branch

    if y_ak is None or y_branch is None:
        return _count_histogram(x_orig, edges, x_branch, axis_label)

    # Broadcast x and y to a common shape, then flatten both in lockstep.
    x_bc, y_bc = ak.broadcast_arrays(x_ak, y_ak)  # type: ignore[misc]
    x_flat = np.asarray(ak.flatten(x_bc, axis=None), dtype=float)  # type: ignore[arg-type]
    y_flat = np.asarray(ak.flatten(y_bc, axis=None), dtype=float)  # type: ignore[arg-type]
    return _profile_histogram(x_flat, y_flat, edges, y_branch, axis_label)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_range(
    data: np.ndarray,
    range_arg: tuple[float, float] | None,
) -> tuple[float, float]:
    if range_arg is not None:
        return range_arg
    lo, hi = float(data.min()), float(data.max())
    if lo == hi:
        lo, hi = lo - 0.5, lo + 0.5
    return lo, hi


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
    x_data: np.ndarray,
    y_data: np.ndarray,
    edges: np.ndarray,
    name: str,
    label: str,
) -> Histogram:
    n_bins = len(edges) - 1
    lo, hi = edges[0], edges[-1]

    # Keep only (x, y) pairs whose x falls within [lo, hi].
    in_range = (x_data >= lo) & (x_data <= hi)
    x_valid = x_data[in_range]
    y_valid = y_data[in_range]

    # searchsorted on inner edges → 0-based bin index; values equal to hi
    # land in the last bin via clip.
    idx = np.searchsorted(edges[1:], x_valid)
    idx = np.clip(idx, 0, n_bins - 1)

    counts = np.zeros(n_bins, dtype=np.intp)
    sums = np.zeros(n_bins)
    sum_sq = np.zeros(n_bins)
    np.add.at(counts, idx, 1)
    np.add.at(sums, idx, y_valid)
    np.add.at(sum_sq, idx, y_valid**2)

    mins = np.full(n_bins, np.inf)
    maxs = np.full(n_bins, -np.inf)
    np.minimum.at(mins, idx, y_valid)
    np.maximum.at(maxs, idx, y_valid)

    has_data = counts > 0
    means = np.where(has_data, sums / np.where(has_data, counts, 1), 0.0)
    pop_var = np.where(
        has_data,
        sum_sq / np.where(has_data, counts, 1) - means**2,
        0.0,
    )
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
