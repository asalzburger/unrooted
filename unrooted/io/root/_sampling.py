"""Bounded, reproducible uniform sampling over flattened point pairs."""

import numpy as np

from unrooted.core._validation import real_array


def _smallest_priorities(
    keys: np.ndarray, indices: np.ndarray, size: int
) -> np.ndarray:
    """Choose the smallest random keys, resolving boundary ties by input index."""
    boundary = np.partition(keys, size - 1)[size - 1]
    below = np.flatnonzero(keys < boundary)
    ties = np.flatnonzero(keys == boundary)
    needed = size - len(below)
    if len(ties) > needed:
        ties = ties[np.argsort(indices[ties], kind="stable")[:needed]]
    return np.concatenate((below, ties))


class ScatterAccumulator:
    def __init__(self, limit: int | None, sampling: str, seed: int) -> None:
        self.limit = limit
        self.sampling = sampling
        self.total = 0
        self.rng = np.random.default_rng(seed)
        self.x_parts: list[np.ndarray] = []
        self.y_parts: list[np.ndarray] = []
        self.x = np.array([], dtype=float)
        self.y = np.array([], dtype=float)
        self.keys = np.array([], dtype=float)
        self.indices = np.array([], dtype=np.int64)

    def add(self, x: np.ndarray, y: np.ndarray) -> None:
        # Sampling must not hide invalid coordinates that happen to be discarded.
        x = real_array(x, "ScatterData.x")
        y = real_array(y, "ScatterData.y")
        previous = self.total
        self.total += len(x)
        if self.sampling == "error":
            if self.limit is not None and self.total > self.limit:
                raise ValueError(
                    f"Scatter exceeds max_points={self.limit}; narrow the entry range "
                    "or explicitly use sampling='random'"
                )
            self.x_parts.append(x.copy())
            self.y_parts.append(y.copy())
            return
        assert self.limit is not None
        keys = np.concatenate((self.keys, self.rng.random(len(x))))
        indices = np.concatenate((self.indices, np.arange(previous, self.total)))
        x = np.concatenate((self.x, x))
        y = np.concatenate((self.y, y))
        if len(x) > self.limit:
            keep = _smallest_priorities(keys, indices, self.limit)
            keys, indices, x, y = keys[keep], indices[keep], x[keep], y[keep]
        self.keys, self.indices, self.x, self.y = keys, indices, x, y

    def finish(self) -> tuple[np.ndarray, np.ndarray]:
        if self.sampling == "error":
            if not self.x_parts:
                return np.array([], dtype=float), np.array([], dtype=float)
            return np.concatenate(self.x_parts), np.concatenate(self.y_parts)
        order = np.argsort(self.indices)
        return self.x[order], self.y[order]
