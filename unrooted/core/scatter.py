from __future__ import annotations

from dataclasses import dataclass

import numpy as np


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
    """

    x: np.ndarray
    y: np.ndarray
    name: str = ""
    x_label: str = ""
    y_label: str = ""
    title: str = ""

    def __post_init__(self) -> None:
        if len(self.x) != len(self.y):
            raise ValueError(
                f"ScatterData x and y must have the same length, "
                f"got {len(self.x)} and {len(self.y)}"
            )
