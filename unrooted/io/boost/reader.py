from __future__ import annotations

from typing import Any

import boost_histogram as bh
import numpy as np

from unrooted.core._efficiency import DEFAULT_CONFIDENCE_LEVEL, binomial_efficiency
from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram

_COUNT_STORAGES = (
    bh.storage.Double,
    bh.storage.Int64,
    bh.storage.Unlimited,
    bh.storage.AtomicInt64,
)


def _flow_values(hist: bh.Histogram, values: Any) -> np.ndarray:
    """Include both flow slots on each axis; unavailable flows are unknown."""
    padding = [
        (int(not ax.traits.underflow), int(not ax.traits.overflow)) for ax in hist.axes
    ]
    return np.pad(
        np.array(values, dtype=float, copy=True),
        padding,
        mode="constant",
        constant_values=np.nan,
    )


def _axis_label(ax: Any) -> str:
    meta = ax.metadata
    return meta if isinstance(meta, str) else ""


def load(hist: bh.Histogram, name: str = "") -> Histogram:
    """Convert a boost-histogram :class:`~boost_histogram.Histogram` to an
    unrooted :class:`~unrooted.core.Histogram`.

    Supports numeric ``Regular``, ``Variable``, and ``Integer`` axes and the
    following storage types:

    * ``Mean`` — treated as a profile histogram; populates ``spread_min`` /
      ``spread_max`` as mean ± σ_y (standard deviation of individual
      measurements).  Empty bins (count = 0) get ``nan`` spread.
    * ``Weight`` — structured storage with ``value`` and ``variance`` fields.
    * ``Double``, ``Int64``, ``Unlimited``, ``AtomicInt64`` — Poisson assumption;
      ``variances`` equals ``values``.

    Categorical/Boolean axes and ``WeightedMean`` storage are unsupported.
    Arrays are independent snapshots of the source. Missing flow slots are
    padded with NaN. Axis metadata strings become axis labels.

    Args:
        hist: The boost-histogram histogram to convert.
        name: Name assigned to the returned histogram.

    Returns:
        A :class:`~unrooted.core.Histogram` populated from *hist*.
    """
    if hist.ndim == 0:
        raise ValueError("Boost histogram must have at least one numeric axis")
    for ax in hist.axes:
        if not isinstance(ax, (bh.axis.Regular, bh.axis.Variable, bh.axis.Integer)):
            raise ValueError(
                f"Unsupported boost axis {type(ax).__name__}; "
                "use numeric Regular, Variable, or Integer axes"
            )
    if hist.storage_type not in (*_COUNT_STORAGES, bh.storage.Weight, bh.storage.Mean):
        raise ValueError(
            f"Unsupported boost storage {hist.storage_type.__name__}; "
            "use count, Weight, or Mean storage; WeightedMean is unsupported"
        )
    axes = [
        Axis(edges=np.array(ax.edges, copy=True), label=_axis_label(ax))
        for ax in hist.axes
    ]

    if hist.storage_type == bh.storage.Mean:
        view: Any = hist.view(flow=False)
        count = np.asarray(view["count"])
        values = np.array(view["value"], copy=True)
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
        overflow = _flow_values(hist, overflow_view["value"])

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
    if hist.storage_type == bh.storage.Weight:
        # Weight storage
        values = np.array(raw["value"], dtype=float, copy=True)
        variances = np.array(raw["variance"], dtype=float, copy=True)
        overflow = _flow_values(hist, raw_flow["value"])
    else:
        values = np.array(raw, dtype=float, copy=True)
        variances = values.copy()
        overflow = _flow_values(hist, raw_flow)

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
    *,
    confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
) -> Histogram:
    """Compute per-bin efficiency from two boost-histogram histograms.

    The returned :class:`~unrooted.core.Histogram` contains:

    * ``values``    — efficiency = accepted / total per bin (``nan`` for empty)
    * ``variances`` — binomial variance = eff × (1 − eff) / total
    * ``spread_min/max`` — Wilson interval without continuity correction

    The default confidence level is 68.268949%. Bins where *total* = 0
    receive ``nan`` for values, variances, and interval bounds. Only 1D,
    unweighted, finite, nonnegative integer counts with accepted <= total
    and exactly identical edges are supported.

    Args:
        accepted: Histogram counting accepted (passing) events.
        total:    Histogram counting all (total) events.
        name:     Name assigned to the returned histogram.
        confidence_level: Nominal Wilson confidence level, strictly between 0 and 1.

    Returns:
        A :class:`~unrooted.core.Histogram` representing the efficiency.

    Raises:
        ValueError: If inputs, storage, binning, or confidence level are unsupported.
    """
    for hist in (accepted, total):
        if hist.storage_type not in _COUNT_STORAGES:
            raise ValueError(
                "Efficiency inputs require unweighted count storage "
                "(Double, Int64, Unlimited, or AtomicInt64); "
                "Weight, Mean, and WeightedMean are unsupported"
            )
        if hist.variances(flow=False) is None:
            raise ValueError(
                "Efficiency inputs require known unweighted count variances; "
                "weighted scalar fills are unsupported"
            )
    return binomial_efficiency(
        load(accepted),
        load(total),
        name=name,
        confidence_level=confidence_level,
    )
