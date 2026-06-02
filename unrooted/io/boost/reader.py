from __future__ import annotations

from typing import Any

import boost_histogram as bh
import numpy as np

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram


def _axis_label(ax: Any) -> str:
    meta = ax.metadata
    return meta if isinstance(meta, str) else ""


def load(hist: bh.Histogram, name: str = "") -> Histogram:
    """Convert a boost-histogram :class:`~boost_histogram.Histogram` to an
    unrooted :class:`~unrooted.core.Histogram`.

    Supports any axis type that exposes ``.edges`` (``Variable``, ``Regular``,
    etc.) and the following storage types:

    * ``Mean`` — treated as a profile histogram; populates ``spread_min`` /
      ``spread_max`` as mean ± σ_y (standard deviation of individual
      measurements).  Empty bins (count = 0) get ``nan`` spread.
    * ``Weight`` — structured storage with ``value`` and ``variance`` fields.
    * All scalar storages (``Double``, ``Int64``, etc.) — Poisson assumption;
      ``variances`` equals ``values``.

    Axis metadata strings become axis labels.

    Args:
        hist: The boost-histogram histogram to convert.
        name: Name assigned to the returned histogram.

    Returns:
        A :class:`~unrooted.core.Histogram` populated from *hist*.
    """
    axes = [
        Axis(edges=np.asarray(ax.edges), label=_axis_label(ax))
        for ax in hist.axes
    ]

    if hist.storage_type == bh.storage.Mean:
        view: Any = hist.view(flow=False)
        count = np.asarray(view["count"])
        values = np.asarray(view["value"])
        sod2 = np.asarray(view["_sum_of_deltas_squared"])

        has_data = count > 0
        safe_count = np.where(count >= 2, count, 1.0)
        safe_count_m1 = np.where(count >= 2, count - 1, 1.0)

        # SE² = sod2 / (count * (count-1)); 0 for bins with 0 or 1 entries
        variances = np.where(
            count >= 2,
            np.maximum(0.0, sod2) / (safe_count * safe_count_m1),
            0.0,
        )

        # σ_y = std-dev of individual measurements; NaN for empty bins
        sigma_y = np.where(
            has_data,
            np.where(count >= 2, np.sqrt(np.maximum(0.0, sod2 / safe_count_m1)), 0.0),
            np.nan,
        )

        spread_min: np.ndarray | None = np.where(has_data, values - sigma_y, np.nan)
        spread_max: np.ndarray | None = np.where(has_data, values + sigma_y, np.nan)
        overflow_view: Any = hist.view(flow=True)
        overflow = np.asarray(overflow_view["value"])

        return Histogram(
            axes=axes,
            values=values,
            variances=variances,
            name=name,
            overflow=overflow,
            spread_min=spread_min,
            spread_max=spread_max,
        )

    raw: Any = hist.view(flow=False)
    raw_flow: Any = hist.view(flow=True)
    raw_arr = np.asarray(raw)

    if raw_arr.dtype.names is not None and "variance" in raw_arr.dtype.names:
        # Weight storage
        values = np.asarray(raw["value"], dtype=float)
        variances = np.asarray(raw["variance"], dtype=float)
        overflow = np.asarray(raw_flow["value"], dtype=float)
    else:
        values = np.asarray(raw, dtype=float)
        variances = values.copy()
        overflow = np.asarray(raw_flow, dtype=float)

    return Histogram(
        axes=axes,
        values=values,
        variances=variances,
        name=name,
        overflow=overflow,
    )


def load_efficiency(
    accepted: bh.Histogram,
    total: bh.Histogram,
    name: str = "",
) -> Histogram:
    """Compute per-bin efficiency from two boost-histogram histograms.

    The returned :class:`~unrooted.core.Histogram` contains:

    * ``values``    — efficiency = accepted / total per bin (``nan`` for empty)
    * ``variances`` — binomial variance = eff × (1 − eff) / total
    * ``spread_min``— efficiency − σ  (clamped to 0)
    * ``spread_max``— efficiency + σ  (clamped to 1)

    where σ = sqrt(variance).  Bins where *total* = 0 receive ``nan``.

    Args:
        accepted: Histogram counting accepted (passing) events.
        total:    Histogram counting all (total) events.
        name:     Name assigned to the returned histogram.

    Returns:
        A :class:`~unrooted.core.Histogram` representing the efficiency.

    Raises:
        ValueError: If the two histograms have incompatible shapes or bin edges.
    """
    passed = np.asarray(accepted.view(flow=False), dtype=float)
    tot = np.asarray(total.view(flow=False), dtype=float)

    if passed.shape != tot.shape:
        raise ValueError(
            f"Shape mismatch: accepted has {passed.shape} but total has {tot.shape}"
        )

    for i, (ax_a, ax_t) in enumerate(zip(accepted.axes, total.axes)):
        if not np.allclose(np.asarray(ax_a.edges), np.asarray(ax_t.edges)):
            raise ValueError(
                f"Bin edges of axis {i} do not match between accepted and total"
            )

    axes = [
        Axis(edges=np.asarray(ax.edges), label=_axis_label(ax))
        for ax in accepted.axes
    ]

    has_total = tot > 0
    eff = np.where(has_total, passed / np.where(has_total, tot, 1.0), np.nan)
    var = np.where(
        has_total,
        eff * (1.0 - eff) / np.where(has_total, tot, 1.0),
        np.nan,
    )
    sigma = np.where(has_total, np.sqrt(np.maximum(0.0, var)), np.nan)

    return Histogram(
        axes=axes,
        values=np.where(has_total, eff, np.nan),
        variances=np.where(has_total, var, np.nan),
        name=name,
        spread_min=np.where(has_total, np.maximum(0.0, eff - sigma), np.nan),
        spread_max=np.where(has_total, np.minimum(1.0, eff + sigma), np.nan),
    )
