from __future__ import annotations

from collections.abc import Iterator
from numbers import Integral
from pathlib import Path
from typing import Any, cast

import awkward as ak
import numpy as np
import uproot

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram
from unrooted.core.scatter import ScatterData
from unrooted.io.root._sampling import ScatterAccumulator

DEFAULT_STEP_SIZE = 100_000


def load_branch(
    path: str | Path,
    key: str,
    x_branch: str,
    y_branch: str | None = None,
    *,
    n_bins: int = 100,
    range: tuple[float, float] | None = None,  # noqa: A002
    label: str = "",
    entry_start: int = 0,
    entry_stop: int | None = None,
    step_size: int = DEFAULT_STEP_SIZE,
) -> Histogram:
    """Load selected tree entries as a count or population-profile histogram.

    Scalars, vectors, and nested jagged branches are flattened. Profile pairs
    are aligned with awkward.broadcast_arrays within each chunk. Bins are
    [left, right), including the final right edge. Out-of-range x is omitted.

    Count histograms need one accumulation pass. Profiles use three passes:
    observed extrema/counts, sums shifted by the global per-bin minima, and
    centered squared deviations. This preserves numerical stability at large
    offsets without retaining all observations. Automatic ranges require an
    additional x-only pass before broadcasting.

    Profile variance is M2/N². Empty bins have value/variance zero and NaN
    extrema; single-entry bins have zero variance and equal extrema.

    Args:
        path: ROOT file path.
        key: Tree path inside the file.
        x_branch: Branch defining the bin axis.
        y_branch: Optional branch to profile against x.
        n_bins: Positive number of bins (default 100).
        range: Finite (lo, hi), lo < hi; None scans the selected x values.
        label: X-axis label; defaults to x_branch.
        entry_start: First entry included, nonnegative (default zero).
        entry_stop: First entry excluded; None reads to the end. Bounds beyond
                    the tree length are clipped. Selection precedes flattening.
        step_size: Maximum entries per chunk (default 100,000). This is not a
                   byte limit; jagged expansion and ROOT baskets affect memory.
    """
    _validate_entries(entry_start, entry_stop)
    _positive_integer(step_size, "step_size")
    _positive_integer(n_bins, "n_bins")
    with cast(Any, uproot.open)(path, array_cache=None) as root_file:
        tree = _get_tree(root_file, key, x_branch, y_branch)
        bounds = _range(tree, x_branch, range, entry_start, entry_stop, step_size)
        axis = Axis(np.linspace(*bounds, int(n_bins) + 1), label=label or x_branch)
        if y_branch is None:
            counts = np.zeros(axis.n_bins, dtype=np.int64)
            for x, _ in _chunks(
                tree, x_branch, None, entry_start, entry_stop, step_size
            ):
                counts += np.histogram(x, bins=axis.edges)[0]
            values = counts.astype(float)
            return Histogram([axis], values, values.copy(), name=x_branch)
        return _profile(
            tree, x_branch, y_branch, axis, entry_start, entry_stop, step_size
        )


def load_scatter(
    path: str | Path,
    key: str,
    x_branch: str,
    y_branch: str,
    *,
    label_x: str = "",
    label_y: str = "",
    entry_start: int = 0,
    entry_stop: int | None = None,
    step_size: int = DEFAULT_STEP_SIZE,
    max_points: int | None = None,
    sampling: str = "error",
    seed: int = 0,
) -> ScatterData:
    """Load point pairs in chunks, with an optional explicit limit or sample.

    Entry selection precedes awkward broadcasting and flattening. Without
    max_points all selected pairs are returned, so result memory grows with
    the selection. No sampling happens implicitly.

    Args:
        path: ROOT file path.
        key: Tree path inside the file.
        x_branch: Branch for x coordinates.
        y_branch: Branch for y coordinates.
        label_x: X-axis label; defaults to x_branch.
        label_y: Y-axis label; defaults to y_branch.
        entry_start: First entry included, nonnegative (default zero).
        entry_stop: First entry excluded; None reads to the end. Bounds beyond
                    the tree length are clipped.
        step_size: Maximum entries per chunk, not bytes (default 100,000).
        max_points: Positive maximum retained pairs, or None for all pairs.
        sampling: 'error' raises when max_points is exceeded. 'random' retains
                  a uniform sample without replacement over flattened pairs;
                  requires max_points. Returned points keep their input order.
        seed: Nonnegative RNG seed (default zero), used by random sampling.
              Results repeat for the same data/seed across chunk sizes.
    """
    _validate_entries(entry_start, entry_stop)
    _positive_integer(step_size, "step_size")
    if max_points is not None:
        _positive_integer(max_points, "max_points")
    if sampling not in ("error", "random"):
        raise ValueError("sampling must be 'error' or 'random'")
    if sampling == "random" and max_points is None:
        raise ValueError("sampling='random' requires max_points")
    if isinstance(seed, bool) or not isinstance(seed, Integral) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if sampling != "random" and seed != 0:
        raise ValueError("seed is only used with sampling='random'")
    accumulator = ScatterAccumulator(max_points, sampling, int(seed))
    with cast(Any, uproot.open)(path, array_cache=None) as root_file:
        tree = _get_tree(root_file, key, x_branch, y_branch)
        for x, y in _chunks(
            tree, x_branch, y_branch, entry_start, entry_stop, step_size
        ):
            assert y is not None
            accumulator.add(x, y)
    x, y = accumulator.finish()
    return ScatterData(
        x=x,
        y=y,
        name=y_branch,
        x_label=label_x or x_branch,
        y_label=label_y or y_branch,
        source_points=accumulator.total,
        sample_seed=int(seed) if sampling == "random" else None,
    )


def _positive_integer(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_entries(start: int, stop: int | None) -> None:
    for name, value in (("entry_start", start), ("entry_stop", stop)):
        if value is None and name == "entry_stop":
            continue
        if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
            raise ValueError(f"{name} must be a nonnegative integer")
    if stop is not None and stop < start:
        raise ValueError("entry_stop must be greater than or equal to entry_start")


def _get_tree(root_file: Any, key: str, x_branch: str, y_branch: str | None) -> Any:
    tree = root_file[key]
    if not hasattr(tree, "iterate") or not hasattr(tree, "num_entries"):
        raise ValueError(f"ROOT object {key!r} must be a tree with iterable branches")
    for branch in dict.fromkeys(
        [x_branch, *([y_branch] if y_branch is not None else [])]
    ):
        tree[branch]  # Check missing branches even for an empty entry selection.
    return tree


def _flat(values: Any) -> np.ndarray:
    # Awkward supports axis=None at runtime; its annotations omit it.
    return np.asarray(ak.flatten(values, axis=None), dtype=float)  # type: ignore[arg-type]


def _chunks(
    tree: Any,
    x_branch: str,
    y_branch: str | None,
    start: int,
    stop: int | None,
    step_size: int,
) -> Iterator[tuple[np.ndarray, np.ndarray | None]]:
    names = list(
        dict.fromkeys([x_branch, *([y_branch] if y_branch is not None else [])])
    )
    for arrays in tree.iterate(
        expressions=names,
        entry_start=int(start),
        entry_stop=stop,
        step_size=int(step_size),
        library="ak",
        how=dict,
    ):
        x = arrays[x_branch]
        if y_branch is None:
            yield _flat(x), None
        else:
            x, y = ak.broadcast_arrays(x, arrays[y_branch])
            yield (
                _flat(x),
                _flat(y),
            )


def _range(tree, x_branch, explicit, start, stop, step_size) -> tuple[float, float]:
    if explicit is not None:
        try:
            lo, hi = map(float, explicit)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "range must be a finite (lo, hi) pair with lo < hi"
            ) from exc
    else:
        lo, hi = np.inf, -np.inf
        for x, _ in _chunks(tree, x_branch, None, start, stop, step_size):
            if not np.isfinite(x).all():
                raise ValueError("Automatic range requires finite x values")
            if x.size:
                lo, hi = min(lo, float(x.min())), max(hi, float(x.max()))
        if lo == np.inf:
            raise ValueError(
                "Automatic range needs at least one x value; provide range=(lo, hi)"
            )
        if lo == hi:
            lo, hi = lo - 0.5, hi + 0.5
    if not np.isfinite([lo, hi]).all() or lo >= hi:
        raise ValueError("range must be a finite (lo, hi) pair with lo < hi")
    return lo, hi


def _binned_pairs(x, y, edges) -> tuple[np.ndarray, np.ndarray]:
    in_range = (x >= edges[0]) & (x <= edges[-1])
    x, y = x[in_range], y[in_range]
    indices = np.searchsorted(edges[1:], x, side="right")
    return np.clip(indices, 0, len(edges) - 2), y


def _profile(tree, x_branch, y_branch, axis, start, stop, step_size) -> Histogram:
    n_bins = axis.n_bins
    counts = np.zeros(n_bins, dtype=np.int64)
    minima, maxima = np.full(n_bins, np.inf), np.full(n_bins, -np.inf)
    # A common origin per bin keeps all arithmetic away from the large offset.
    for x, y in _chunks(tree, x_branch, y_branch, start, stop, step_size):
        indices, values = _binned_pairs(x, y, axis.edges)
        counts += np.bincount(indices, minlength=n_bins)
        np.minimum.at(minima, indices, values)
        np.maximum.at(maxima, indices, values)
    has_data = counts > 0
    safe_counts = np.where(has_data, counts, 1)
    shifted_sums = np.zeros(n_bins)
    for x, y in _chunks(tree, x_branch, y_branch, start, stop, step_size):
        indices, values = _binned_pairs(x, y, axis.edges)
        shifted_sums += np.bincount(
            indices, weights=values - minima[indices], minlength=n_bins
        )
    shifted_means = shifted_sums / safe_counts
    m2 = np.zeros(n_bins)
    for x, y in _chunks(tree, x_branch, y_branch, start, stop, step_size):
        indices, values = _binned_pairs(x, y, axis.edges)
        deviations = (values - minima[indices]) - shifted_means[indices]
        m2 += np.bincount(indices, weights=deviations**2, minlength=n_bins)
    return Histogram(
        [axis],
        np.where(has_data, minima + shifted_means, 0.0),
        m2 / safe_counts / safe_counts,
        name=y_branch,
        spread_min=np.where(has_data, minima, np.nan),
        spread_max=np.where(has_data, maxima, np.nan),
    )
