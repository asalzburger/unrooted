from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import numpy as np
import uproot

from unrooted.core._efficiency import DEFAULT_CONFIDENCE_LEVEL, binomial_efficiency
from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram


def _check_class(classname: str, key: str) -> None:
    if not (classname.startswith(("TH1", "TH2")) or classname == "TProfile"):
        raise ValueError(
            f"Unsupported ROOT object {classname} at {key!r}; "
            "use TH1, TH2, or TProfile, load_branch/load_scatter for trees, "
            "or load_efficiency with separate passed/total TH1 objects"
        )


def _from_root(obj: Any, key: str) -> Histogram:
    raw_variances = obj.variances(flow=False)
    if raw_variances is None:
        raise ValueError(f"ROOT histogram {key!r} does not provide variances")
    values = np.array(obj.values(flow=False), copy=True)
    variances = np.array(raw_variances, copy=True)
    overflow = np.array(obj.values(flow=True), copy=True)
    axes = [
        Axis(edges=np.array(ax.edges(), copy=True), label=ax.member("fTitle") or "")
        for ax in obj.axes
    ]
    spread_min: np.ndarray | None = None
    spread_max: np.ndarray | None = None
    if obj.classname == "TProfile":
        counts = np.asarray(obj.counts(flow=False))
        has_data = counts > 0
        # SE² = σ_y²/N  →  σ_y = sqrt(SE² * N)
        sigma_y = np.where(
            has_data, np.sqrt(np.maximum(0.0, variances * counts)), np.nan
        )
        spread_min = np.where(has_data, values - sigma_y, np.nan)
        spread_max = np.where(has_data, values + sigma_y, np.nan)
    return Histogram(
        axes=axes,
        values=values,
        variances=variances,
        name=key.split(";")[0],
        overflow=overflow,
        spread_min=spread_min,
        spread_max=spread_max,
    )


def load(path: str | Path, key: str) -> Histogram:
    """Load a ROOT TH1, TH2, or TProfile as an independent array snapshot.

    Values, variances, numeric edges, axis labels, and both flow bins per axis
    are extracted through uproot. TProfile spread bounds are mean ± σ_y,
    derived as sqrt(SE² * N); empty bins have NaN spread.

    Args:
        path: Path to the ROOT file.
        key: Object key, optionally including a cycle (e.g. ``hx;1``).

    Returns:
        A Histogram whose name is the key with its cycle stripped.

    Raises:
        KeyError: If the key is absent.
        ValueError: If the object type or its numerical data are unsupported.
    """
    with cast(Any, uproot.open(path)) as f:
        # Inspect metadata before deserializing unsupported objects such as
        # TEfficiency, which uproot may be unable to decode at all.
        _check_class(f.classname_of(key), key)
        return _from_root(f[key], key)


def load_efficiency(
    path: str | Path,
    pass_key: str,
    total_key: str,
    *,
    confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
) -> Histogram:
    """Compute a binomial efficiency from separate passed and total TH1 objects.

    Requires 1D unweighted, finite, nonnegative integer counts with passed <=
    total, Poisson-compatible variances, and exactly identical edges. Profiles,
    TH2, and TEfficiency objects are unsupported.

    Values are passed/total, variances retain p*(1-p)/total, and spread bounds
    are Wilson intervals without continuity correction (68.268949% by default).
    All four arrays contain NaN for bins with zero total. Endpoint intervals
    have nonzero width, even though the variance field is zero there.

    Args:
        path: Path to the ROOT file.
        pass_key: Key counting passing events.
        total_key: Key counting total events.
        confidence_level: Nominal Wilson confidence level, strictly between 0 and 1.

    Raises:
        KeyError: If either key is absent.
        ValueError: If inputs, binning, or confidence level are unsupported.
    """
    with cast(Any, uproot.open(path)) as f:
        if any(
            not f.classname_of(key).startswith("TH1") for key in (pass_key, total_key)
        ):
            raise ValueError(
                "Efficiency inputs must be one-dimensional TH1 count histograms"
            )
        return binomial_efficiency(
            _from_root(f[pass_key], pass_key),
            _from_root(f[total_key], total_key),
            confidence_level=confidence_level,
        )
