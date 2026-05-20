from __future__ import annotations

import numpy as np

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram


def _make_hist(n: int = 3) -> Histogram:
    axis = Axis(edges=np.arange(n + 1, dtype=float))
    values = np.ones(n)
    return Histogram(axes=[axis], values=values, variances=values.copy())


def test_spread_defaults_to_none():
    h = _make_hist()
    assert h.spread_min is None
    assert h.spread_max is None


def test_spread_stored_correctly():
    h = _make_hist(3)
    lo = np.array([0.5, 1.5, 2.5])
    hi = np.array([1.5, 2.5, 3.5])
    h.spread_min = lo
    h.spread_max = hi
    np.testing.assert_array_equal(h.spread_min, lo)
    np.testing.assert_array_equal(h.spread_max, hi)


def test_spread_shape_consistent():
    h = _make_hist(5)
    h.spread_min = np.zeros(5)
    h.spread_max = np.ones(5) * 10.0
    assert h.spread_min.shape == h.values.shape
    assert h.spread_max.shape == h.values.shape


def test_spread_constructed_inline():
    axis = Axis(edges=np.array([0.0, 1.0, 2.0]))
    lo = np.array([0.2, 0.8])
    hi = np.array([1.8, 2.2])
    h = Histogram(
        axes=[axis],
        values=np.array([1.0, 1.5]),
        variances=np.array([1.0, 1.5]),
        spread_min=lo,
        spread_max=hi,
    )
    np.testing.assert_array_equal(h.spread_min, lo)
    np.testing.assert_array_equal(h.spread_max, hi)
