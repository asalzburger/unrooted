from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Axis:
    edges: np.ndarray
    label: str = ""

    @property
    def n_bins(self) -> int:
        return len(self.edges) - 1

    @property
    def centers(self) -> np.ndarray:
        return 0.5 * (self.edges[:-1] + self.edges[1:])

    @property
    def widths(self) -> np.ndarray:
        return self.edges[1:] - self.edges[:-1]
