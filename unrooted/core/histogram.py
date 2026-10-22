from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from unrooted.core._validation import real_array
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
        overflow:   Full values array with both flow slots per axis, shape
                    ``(n_0 + 2, n_1 + 2, ...)``. Disabled flows are NaN.
                    ``None`` if not loaded; edits to values do not synchronize it.
        spread_min: Optional lower spread bound. Branch profiles use the
                    observed minimum; loaded profiles use mean minus standard
                    deviation; efficiency readers use an interval bound.
        spread_max: Optional upper spread bound, paired with ``spread_min``.
    """

    axes: list[Axis]
    values: np.ndarray
    variances: np.ndarray
    name: str = ""
    title: str = ""
    overflow: np.ndarray | None = field(default=None)
    spread_min: np.ndarray | None = field(default=None)
    spread_max: np.ndarray | None = field(default=None)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Check dimensions, numeric domains, spread bounds, and full flow shape.

        Arrays are borrowed when no conversion is needed. Call after editing
        arrays; public plotting functions also validate before drawing.
        """
        if not isinstance(self.axes, (list, tuple)) or not self.axes:
            raise ValueError(
                "Histogram.axes must be a nonempty sequence of Axis objects"
            )
        if any(not isinstance(axis, Axis) for axis in self.axes):
            raise ValueError("Histogram.axes must contain only Axis objects")
        self.axes = list(self.axes)
        for axis in self.axes:
            axis.validate()
        expected = tuple(axis.n_bins for axis in self.axes)
        self.values = real_array(self.values, "Histogram.values")
        self.variances = real_array(self.variances, "Histogram.variances")
        if self.values.shape != expected:
            raise ValueError(
                f"Histogram.values shape {self.values.shape} must match axes {expected}"
            )
        if self.variances.shape != expected:
            raise ValueError("Histogram.variances must have the same shape as values")
        if np.any(self.variances < 0):
            raise ValueError("Histogram.variances must be nonnegative or NaN")
        if (self.spread_min is None) != (self.spread_max is None):
            raise ValueError(
                "Histogram spread_min and spread_max must be supplied together"
            )
        if self.spread_min is not None and self.spread_max is not None:
            self.spread_min = real_array(self.spread_min, "Histogram.spread_min")
            self.spread_max = real_array(self.spread_max, "Histogram.spread_max")
            if self.spread_min.shape != expected or self.spread_max.shape != expected:
                raise ValueError(
                    "Histogram spread bounds must have the same shape as values"
                )
            if not np.array_equal(np.isnan(self.spread_min), np.isnan(self.spread_max)):
                raise ValueError(
                    "Histogram spread bounds must have matching NaN positions"
                )
            if np.any(self.spread_min > self.spread_max):
                raise ValueError("Histogram spread_min must not exceed spread_max")
            if np.any(self.spread_min > self.values) or np.any(
                self.spread_max < self.values
            ):
                raise ValueError("Histogram spread bounds must enclose finite values")
        if self.overflow is not None:
            self.overflow = real_array(self.overflow, "Histogram.overflow")
            flow_shape = tuple(n + 2 for n in expected)
            if self.overflow.shape != flow_shape:
                raise ValueError(
                    f"Histogram.overflow shape must be {flow_shape}, "
                    "including both flow bins"
                )

    def require_compatible_binning(self, other: Histogram) -> None:
        """Require identical dimensions and edges before a binwise operation."""
        self.validate()
        other.validate()
        if self.values.shape != other.values.shape:
            raise ValueError(
                f"Shape mismatch: histogram bins {self.values.shape} "
                f"versus {other.values.shape}"
            )
        for i, (left, right) in enumerate(zip(self.axes, other.axes)):
            if not np.array_equal(left.edges, right.edges):
                raise ValueError(f"Bin edges of axis {i} do not match")

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
