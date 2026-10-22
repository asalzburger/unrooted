"""Public numerical data contracts, including mutation and missing data."""

import numpy as np
import pytest

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram
from unrooted.core.scatter import ScatterData


@pytest.mark.parametrize(
    "edges",
    [
        [],
        [1],
        [[0, 1]],
        [0, 0, 1],
        [1, 0],
        [0, np.nan],
        [0, np.inf],
        ["0", "1"],
        [False, True],
        [0j, 1j],
    ],
)
def test_axis_rejects_invalid_edges(edges):
    with pytest.raises(ValueError, match="Axis.edges"):
        Axis(edges)


def test_axis_converts_lists_and_avoids_overflow_in_centers():
    axis = Axis([1e308, 1.5e308])
    assert axis.edges.dtype == np.float64
    assert axis.centers[0] == pytest.approx(1.25e308)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"axes": []}, "nonempty"),
        ({"axes": [[0, 1, 2]]}, "Axis objects"),
        ({"values": [1]}, "shape"),
        ({"values": [[1, 2]]}, "shape"),
        ({"variances": [1]}, "shape"),
        ({"variances": [1, -1]}, "nonnegative"),
        ({"values": [1, np.inf]}, "finite"),
        ({"variances": [1, np.inf]}, "finite"),
        ({"values": ["1", "2"]}, "real numeric"),
        ({"values": [1j, 2j]}, "real numeric"),
        ({"spread_min": [0, 0]}, "together"),
        ({"spread_min": [0], "spread_max": [3]}, "shape"),
        ({"spread_min": [0, np.nan], "spread_max": [3, 3]}, "NaN"),
        ({"spread_min": [2, 0], "spread_max": [0, 3]}, "must not exceed"),
        ({"spread_min": [0, 3], "spread_max": [3, 4]}, "enclose"),
        ({"overflow": [0, 1, 2]}, "both flow"),
    ],
)
def test_histogram_rejects_invalid_data(changes, message):
    kwargs = dict(axes=[Axis([0, 1, 2])], values=[1, 2], variances=[1, 2])
    kwargs.update(changes)
    with pytest.raises(ValueError, match=message):
        Histogram(**kwargs)


def test_missing_data_negative_weights_and_sparse_spread_are_allowed():
    hist = Histogram(
        [Axis([0, 1, 2, 3])],
        [-2, np.nan, 0],
        [4, np.nan, 0],
        spread_min=[-3, np.nan, np.nan],
        spread_max=[-1, np.nan, np.nan],
    )
    assert hist.errors[0] == 2
    assert np.isnan(hist.errors[1])


def test_core_borrows_arrays_and_detects_later_invalid_mutation():
    edges, values, variances = np.array([0.0, 1.0, 2.0]), np.ones(2), np.ones(2)
    hist = Histogram([Axis(edges)], values, variances)
    assert hist.values is values
    assert hist.variances is variances
    assert hist.axes[0].edges is edges
    values[0] = 5
    assert hist.values[0] == 5
    variances[0] = -1
    with pytest.raises(ValueError, match="nonnegative"):
        hist.validate()
    variances[0] = 1
    edges[1] = edges[0]
    with pytest.raises(ValueError, match="increasing"):
        hist.validate()


@pytest.mark.parametrize(
    ("x", "y", "message"),
    [
        ([[1, 2]], [[1, 2]], "1D"),
        ([1], [1, 2], "same length"),
        ([np.inf], [1], "finite"),
        ([1], [1j], "real numeric"),
    ],
)
def test_scatter_rejects_invalid_coordinates(x, y, message):
    with pytest.raises(ValueError, match=message):
        ScatterData(x, y)


def test_scatter_allows_empty_arrays_and_nan_gaps():
    assert ScatterData([], []).x.shape == (0,)
    x = np.array([0.0, np.nan])
    scatter = ScatterData(x, [1, 2])
    assert scatter.x is x
    scatter.y = np.array([[1, 2]])
    with pytest.raises(ValueError, match="1D"):
        scatter.validate()
