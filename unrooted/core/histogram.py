from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from unrooted.core.axis import Axis


@dataclass
class Histogram:
    """N-dimensional histogram with values, variances, and optional spread.

    The central data structure of *unrooted*.  Every I/O function returns a
    ``Histogram`` and every plot function accepts one.  All numerical data is
    stored as ``numpy`` arrays so the object interops directly with the
    scientific Python ecosystem.

    Args:
        axes:       One :class:`Axis` per dimension, carrying bin edges and
                    an optional axis label.
        values:     Array of bin contents (counts or means for profile
                    histograms).  Shape: ``(n_bins,)`` for 1D,
                    ``(nx, ny)`` for 2D.
        variances:  Per-bin variance.  For count histograms this equals
                    *values* (Poisson); for profile histograms this is the
                    squared standard error of the mean.
        name:       Optional histogram name (used as plot label fallback).
        title:      Optional longer title.
        overflow:   Full values array *with* flow bins included, as returned
                    by uproot.  ``None`` if not loaded.
        spread_min: Per-bin minimum of the profiled quantity.  Set only for
                    profile histograms; ``None`` otherwise.
        spread_max: Per-bin maximum of the profiled quantity.  Set only for
                    profile histograms; ``None`` otherwise.
    """

    axes: list[Axis]
    values: np.ndarray
    variances: np.ndarray
    name: str = ""
    title: str = ""
    overflow: np.ndarray | None = field(default=None)
    spread_min: np.ndarray | None = field(default=None)
    spread_max: np.ndarray | None = field(default=None)

    @property
    def ndim(self) -> int:
        """Number of dimensions (1 for 1D, 2 for 2D, etc.)."""
        return len(self.axes)

    @property
    def errors(self) -> np.ndarray:
        """Per-bin uncertainty: ``sqrt(variances)``."""
        return np.sqrt(self.variances)


Histogram1D = Histogram
Histogram2D = Histogram
