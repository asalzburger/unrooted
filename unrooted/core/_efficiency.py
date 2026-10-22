"""Binomial efficiency contract shared by the I/O backends."""

from statistics import NormalDist

import numpy as np

from unrooted.core.histogram import Histogram

DEFAULT_CONFIDENCE_LEVEL = 0.6826894921370859


def binomial_efficiency(
    accepted: Histogram,
    total: Histogram,
    *,
    name: str = "",
    confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
) -> Histogram:
    """Require unweighted event counts and return Wilson interval bounds."""
    if accepted.ndim != 1 or total.ndim != 1:
        raise ValueError("Efficiency inputs must be one-dimensional count histograms")
    accepted.require_compatible_binning(total)
    for label, hist in [("accepted", accepted), ("total", total)]:
        counts = hist.values
        if not np.all(np.isfinite(counts)):
            raise ValueError(f"Efficiency {label} counts must be finite")
        if np.any(counts < 0) or np.any(counts != np.floor(counts)):
            raise ValueError(f"Efficiency {label} counts must be nonnegative integers")
        if not np.allclose(hist.variances, counts, rtol=1e-12, atol=0.0):
            raise ValueError(
                "Efficiency inputs must have Poisson variances; "
                "weighted or unknown variances are unsupported"
            )
    if np.any(accepted.values > total.values):
        raise ValueError("Efficiency accepted counts must not exceed total counts")
    try:
        level = float(confidence_level)
    except (TypeError, ValueError) as exc:
        raise ValueError("confidence_level must be strictly between 0 and 1") from exc
    if not 0.0 < level < 1.0:
        raise ValueError("confidence_level must be strictly between 0 and 1")

    passed = np.asarray(accepted.values, dtype=float)
    counts = np.asarray(total.values, dtype=float)
    has_total = counts > 0
    efficiency = np.divide(
        passed,
        counts,
        out=np.full(counts.shape, np.nan),
        where=has_total,
    )
    inv_n = np.divide(
        1.0,
        counts,
        out=np.zeros(counts.shape),
        where=has_total,
    )
    variances = efficiency * (1.0 - efficiency) * inv_n
    # Using the lower tail avoids rounding (1 + level) / 2 up to 1.
    z = -NormalDist().inv_cdf((1.0 - level) / 2.0)
    adjustment = z**2 * inv_n
    denominator = 1.0 + adjustment
    center = (efficiency + adjustment / 2.0) / denominator
    radius = z * np.hypot(np.sqrt(variances), z * inv_n / 2.0) / denominator
    # Preserve the mathematically exact enclosure at 0 and 1 despite rounding.
    lower = np.minimum(efficiency, np.maximum(0.0, center - radius))
    upper = np.maximum(efficiency, np.minimum(1.0, center + radius))
    return Histogram(
        axes=accepted.axes,
        values=efficiency,
        variances=variances,
        name=name or accepted.name,
        spread_min=lower,
        spread_max=upper,
    )
