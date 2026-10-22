from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral

import numpy as np

from unrooted.core._validation import real_array


@dataclass
class ScatterData:
    """Raw (x, y) point cloud read from two TTree branches.

    Unlike :class:`~unrooted.core.histogram.Histogram`, this type carries
    un-binned data and is rendered as a scatter plot rather than a step
    function.

    Attributes:
        x:       Flat array of x-values (already broadcast and flattened).
        y:       Flat array of y-values, same length as *x*.
        name:    Logical name (typically the y-branch name).
        x_label: Axis label for x (defaults to the x-branch name).
        y_label: Axis label for y (defaults to the y-branch name).
        title:   Optional figure title.
        source_points: Number of flattened pairs before optional sampling.
        sample_seed: RNG seed when random sampling was requested.
    """

    x: np.ndarray
    y: np.ndarray
    name: str = ""
    x_label: str = ""
    y_label: str = ""
    title: str = ""
    source_points: int | None = None
    sample_seed: int | None = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Require flat, equally sized real arrays; NaNs are retained as gaps."""
        self.x = real_array(self.x, "ScatterData.x")
        self.y = real_array(self.y, "ScatterData.y")
        if self.x.ndim != 1 or self.y.ndim != 1:
            raise ValueError("ScatterData x and y must be 1D arrays")
        if len(self.x) != len(self.y):
            raise ValueError(
                f"ScatterData x and y must have the same length, "
                f"got {len(self.x)} and {len(self.y)}"
            )
        for name, value in (
            ("source_points", self.source_points),
            ("sample_seed", self.sample_seed),
        ):
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, Integral) or value < 0
            ):
                raise ValueError(f"ScatterData.{name} must be a nonnegative integer")
        if self.source_points is not None and self.source_points < len(self.x):
            raise ValueError(
                "ScatterData.source_points must be at least the retained size"
            )
        if self.sample_seed is not None and self.source_points is None:
            raise ValueError("ScatterData.sample_seed requires source_points")

    @property
    def sampled(self) -> bool:
        """Whether the reader retained fewer pairs than its selected source."""
        return self.source_points is not None and len(self.x) < self.source_points
