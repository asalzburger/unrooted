from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import numpy as np
import uproot

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram


def load(path: str | Path, key: str) -> Histogram:
    """Load a ROOT histogram object as a :class:`~unrooted.core.Histogram`.

    Supports ``TH1``, ``TH2``, and ``TProfile`` objects.  Bin values,
    variances, overflow, and axis labels are all extracted automatically.

    For ``TProfile`` objects the returned histogram carries ``spread_min`` and
    ``spread_max`` representing mean ± σ_y per bin, where σ_y is the standard
    deviation of the profiled quantity (derived from the stored SE²  and bin
    counts).  Empty bins are set to ``nan``.

    Args:
        path: Path to the ``.root`` file.
        key:  Histogram key inside the file, e.g. ``"hx"`` or ``"hx;1"``.
              The cycle number (``";1"``) is stripped from the returned
              histogram name.

    Returns:
        A :class:`~unrooted.core.Histogram` with ``values``, ``variances``,
        ``overflow``, and one :class:`~unrooted.core.Axis` per dimension.

    Raises:
        KeyError: If *key* is not found in the file.
    """
    with cast(Any, uproot.open(path)) as f:
        obj: Any = f[key]
        values = np.asarray(obj.values(flow=False))
        variances = np.asarray(obj.variances(flow=False))
        overflow = np.asarray(obj.values(flow=True))
        axes = [
            Axis(
                edges=np.asarray(ax.edges()),
                label=ax.member("fTitle") or "",
            )
            for ax in obj.axes
        ]
        name = key.split(";")[0]

        spread_min: np.ndarray | None = None
        spread_max: np.ndarray | None = None
        if obj.classname.startswith("TProfile"):
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
            name=name,
            overflow=overflow,
            spread_min=spread_min,
            spread_max=spread_max,
        )


def load_efficiency(
    path: str | Path,
    pass_key: str,
    total_key: str,
) -> Histogram:
    """Load a pair of TH1 histograms and return a per-bin efficiency histogram.

    This is the recommended way to load ROOT efficiency data with *unrooted*.
    ROOT's ``TEfficiency`` class cannot currently be read by *uproot*; store (or
    export) the passed and total histograms as separate ``TH1`` objects and
    point this function at them.

    The returned :class:`~unrooted.core.Histogram` contains:

    * ``values``    — efficiency = passed / total per bin (0 for empty bins)
    * ``variances`` — binomial variance = eff × (1 − eff) / total per bin
    * ``spread_min``— efficiency − σ  (Gaussian approximation, clamped to 0)
    * ``spread_max``— efficiency + σ  (Gaussian approximation, clamped to 1)

    where σ = sqrt(variance).  Bins where *total* is 0 receive ``nan`` for all
    four quantities.

    Args:
        path:      Path to the ``.root`` file.
        pass_key:  Key of the histogram counting *passing* events.
        total_key: Key of the histogram counting *total* events.

    Returns:
        A :class:`~unrooted.core.Histogram` representing the efficiency.

    Raises:
        KeyError:   If either key is not found in the file.
        ValueError: If the two histograms have incompatible binning.
    """
    with cast(Any, uproot.open(path)) as f:
        p_obj: Any = f[pass_key]
        t_obj: Any = f[total_key]

        passed = np.asarray(p_obj.values(flow=False), dtype=float)
        total = np.asarray(t_obj.values(flow=False), dtype=float)

        if passed.shape != total.shape:
            raise ValueError(
                f"Shape mismatch: {pass_key} has {passed.shape} but "
                f"{total_key} has {total.shape}"
            )

        p_edges = np.asarray(p_obj.axes[0].edges())
        t_edges = np.asarray(t_obj.axes[0].edges())
        if not np.allclose(p_edges, t_edges):
            raise ValueError(
                f"Bin edges of {pass_key} and {total_key} do not match"
            )

        has_total = total > 0
        eff = np.where(has_total, passed / np.where(has_total, total, 1.0), np.nan)
        var = np.where(
            has_total,
            eff * (1.0 - eff) / np.where(has_total, total, 1.0),
            np.nan,
        )
        sigma = np.where(has_total, np.sqrt(np.maximum(0.0, var)), np.nan)

        name = pass_key.split(";")[0]
        axis = Axis(edges=p_edges, label=p_obj.axes[0].member("fTitle") or "")
        return Histogram(
            axes=[axis],
            values=np.where(has_total, eff, np.nan),
            variances=np.where(has_total, var, np.nan),
            name=name,
            spread_min=np.where(has_total, np.maximum(0.0, eff - sigma), np.nan),
            spread_max=np.where(has_total, np.minimum(1.0, eff + sigma), np.nan),
        )
