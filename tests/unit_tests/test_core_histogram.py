import numpy as np
import pytest

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram


def test_histogram_1d_ndim():
    axis = Axis(edges=np.array([0.0, 1.0, 2.0, 3.0]))
    hist = Histogram(
        axes=[axis],
        values=np.array([10.0, 20.0, 15.0]),
        variances=np.array([10.0, 20.0, 15.0]),
    )
    assert hist.ndim == 1


def test_histogram_2d_ndim():
    ax1 = Axis(edges=np.array([0.0, 1.0, 2.0]))
    ax2 = Axis(edges=np.array([0.0, 1.0, 2.0, 3.0]))
    hist = Histogram(
        axes=[ax1, ax2],
        values=np.zeros((2, 3)),
        variances=np.zeros((2, 3)),
    )
    assert hist.ndim == 2


def test_histogram_errors():
    axis = Axis(edges=np.array([0.0, 1.0, 2.0]))
    hist = Histogram(
        axes=[axis],
        values=np.array([4.0, 9.0]),
        variances=np.array([4.0, 9.0]),
    )
    np.testing.assert_allclose(hist.errors, np.array([2.0, 3.0]))


def test_axis_n_bins():
    axis = Axis(edges=np.array([0.0, 1.0, 3.0, 6.0]))
    assert axis.n_bins == 3


def test_axis_centers():
    axis = Axis(edges=np.array([0.0, 1.0, 3.0, 6.0]))
    np.testing.assert_allclose(axis.centers, np.array([0.5, 2.0, 4.5]))


def test_axis_widths():
    axis = Axis(edges=np.array([0.0, 1.0, 3.0, 6.0]))
    np.testing.assert_allclose(axis.widths, np.array([1.0, 2.0, 3.0]))


def test_histogram_overflow_stored():
    axis = Axis(edges=np.array([0.0, 1.0, 2.0]))
    overflow = np.array([5.0, 10.0, 20.0, 8.0])
    hist = Histogram(
        axes=[axis],
        values=np.array([10.0, 20.0]),
        variances=np.array([10.0, 20.0]),
        overflow=overflow,
    )
    assert hist.overflow is not None
    np.testing.assert_array_equal(hist.overflow, overflow)


def test_histogram_no_overflow_by_default():
    axis = Axis(edges=np.array([0.0, 1.0, 2.0]))
    hist = Histogram(
        axes=[axis],
        values=np.array([10.0, 20.0]),
        variances=np.array([10.0, 20.0]),
    )
    assert hist.overflow is None
