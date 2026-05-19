from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from unrooted.core.axis import Axis


@dataclass
class Histogram:
    axes: list[Axis]
    values: np.ndarray
    variances: np.ndarray
    name: str = ""
    title: str = ""
    overflow: np.ndarray | None = field(default=None)

    @property
    def ndim(self) -> int:
        return len(self.axes)

    @property
    def errors(self) -> np.ndarray:
        return np.sqrt(self.variances)


Histogram1D = Histogram
Histogram2D = Histogram
