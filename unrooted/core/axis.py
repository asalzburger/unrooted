from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from unrooted.core._validation import real_array


@dataclass
class Axis:
    """One axis of a histogram, described by its bin edges.

    Args:
        edges: Array of ``n_bins + 1`` monotonically increasing bin-edge
               values.  The first and last entries are the left edge of the
               first bin and the right edge of the last bin respectively.
        label: Human-readable axis label used as a plot axis title.
    """

    edges: np.ndarray
    label: str = ""

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Require finite, strictly increasing, one-dimensional float64 edges."""
        self.edges = real_array(self.edges, "Axis.edges", allow_nan=False, dtype=float)
        if self.edges.ndim != 1 or self.edges.size < 2:
            raise ValueError("Axis.edges must be 1D with at least two edges")
        if np.any(self.edges[1:] <= self.edges[:-1]):
            raise ValueError("Axis.edges must be strictly increasing")

    @property
    def n_bins(self) -> int:
        """Number of bins (``len(edges) - 1``)."""
        return len(self.edges) - 1

    @property
    def centers(self) -> np.ndarray:
        """Array of bin-centre coordinates, shape ``(n_bins,)``."""
        return 0.5 * self.edges[:-1] + 0.5 * self.edges[1:]

    @property
    def widths(self) -> np.ndarray:
        """Array of bin widths, shape ``(n_bins,)``."""
        return self.edges[1:] - self.edges[:-1]
