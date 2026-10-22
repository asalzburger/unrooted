from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import awkward as ak
import numpy as np
import uproot

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram
from unrooted.core.scatter import ScatterData


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

    Count and profile bins use the same convention: ``[left, right)``, except
    the last bin includes its right edge. Values outside the range are omitted.

    Profiles retain the population convention: for N entries, ``variances``
    is ``sum((y - mean)**2) / N**2``. Empty bins have value and variance zero
    and ``nan`` spread bounds; single-entry bins have variance zero and both
    spread bounds equal to the observation. Empty trees require an explicit
    *range* because the automatic range is derived from the data.

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


def load_scatter(
    path: str | Path,
    key: str,
    x_branch: str,
    y_branch: str,
    *,
    label_x: str = "",
    label_y: str = "",
) -> ScatterData:
    """Load two TTree branches as a raw (x, y) scatter point cloud.

    Both branches are broadcast to a common shape (supporting the same scalar,
    vector, and jagged combinations as :func:`load_branch`) and then fully
    flattened.  No binning is performed.

    Args:
        path:     Path to the ROOT file.
        key:      Tree name inside the file.
        x_branch: Branch used for the x-axis.
        y_branch: Branch used for the y-axis.
        label_x:  X-axis label; defaults to *x_branch*.
        label_y:  Y-axis label; defaults to *y_branch*.
    """
    with cast(Any, uproot.open(path)) as f:
        x_ak = f[key][x_branch].array(library="ak")
        y_ak = f[key][y_branch].array(library="ak")

    x_bc, y_bc = ak.broadcast_arrays(x_ak, y_ak)  # type: ignore[misc]
    x_flat = np.asarray(ak.flatten(x_bc, axis=None), dtype=float)  # type: ignore[arg-type]
    y_flat = np.asarray(ak.flatten(y_bc, axis=None), dtype=float)  # type: ignore[arg-type]

    return ScatterData(
        x=x_flat,
        y=y_flat,
        name=y_branch,
        x_label=label_x or x_branch,
        y_label=label_y or y_branch,
    )


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

    # Match np.histogram: internal edges belong to the bin on their right;
    # the final right edge is included in the last bin.
    idx = np.searchsorted(edges[1:], x_valid, side="right")
    idx = np.clip(idx, 0, n_bins - 1)

    counts = np.bincount(idx, minlength=n_bins)
    mins = np.full(n_bins, np.inf)
    maxs = np.full(n_bins, -np.inf)
    np.minimum.at(mins, idx, y_valid)
    np.maximum.at(maxs, idx, y_valid)

    has_data = counts > 0
    safe_counts = np.where(has_data, counts, 1)

    # Work relative to the minimum in each bin so a large common offset
    # cannot swamp the mean or its squared deviations. A centered second
    # pass avoids subtracting nearly equal raw second moments.
    shifted = y_valid - mins[idx]
    shifted_sums = np.bincount(idx, weights=shifted, minlength=n_bins)
    shifted_means = shifted_sums / safe_counts
    means = np.where(has_data, mins + shifted_means, 0.0)
    deviations = shifted - shifted_means[idx]
    sum_sq_deviations = np.bincount(
        idx, weights=deviations**2, minlength=n_bins,
    )
    # Preserve the population convention: Var(mean) = sum((y - mean)^2) / N^2.
    var_means = sum_sq_deviations / safe_counts / safe_counts
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
