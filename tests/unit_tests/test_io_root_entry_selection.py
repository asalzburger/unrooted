"""Tree entry selection occurs before jagged broadcasting and flattening."""

import awkward as ak
import numpy as np
import pytest
import uproot

from unrooted.io.root import load_branch, load_scatter


@pytest.fixture
def selected_tree(tmp_path):
    path = tmp_path / "selected.root"
    with uproot.recreate(path) as f:
        f.mktree(
            "tree",
            {"x": "float64", "y": "float64", "vector": "var * float64"},
        ).extend(
            {
                "x": np.array([0.1, 1.1, 2.1, 3.1]),
                "y": np.array([10.0, 20.0, 30.0, 40.0]),
                "vector": ak.Array([[100.0], [2.0, 4.0], [], [999.0]]),
            },
        )
    return path


def test_count_entry_range_and_end_clipping(selected_tree):
    hist = load_branch(
        selected_tree, "tree", "x", n_bins=4, range=(0, 4), entry_start=1, entry_stop=3
    )
    np.testing.assert_array_equal(hist.values, [0, 1, 1, 0])
    tail = load_branch(
        selected_tree,
        "tree",
        "x",
        n_bins=4,
        range=(0, 4),
        entry_start=3,
        entry_stop=100,
    )
    np.testing.assert_array_equal(tail.values, [0, 0, 0, 1])


def test_profile_selects_events_before_broadcasting(selected_tree):
    hist = load_branch(
        selected_tree,
        "tree",
        "x",
        "vector",
        n_bins=4,
        range=(0, 4),
        entry_start=1,
        entry_stop=3,
    )
    np.testing.assert_array_equal(hist.values, [0, 3, 0, 0])
    np.testing.assert_array_equal(hist.variances, [0, 0.5, 0, 0])
    np.testing.assert_allclose(hist.spread_min, [np.nan, 2, np.nan, np.nan])
    np.testing.assert_allclose(hist.spread_max, [np.nan, 4, np.nan, np.nan])


def test_scatter_selects_events_before_broadcasting(selected_tree):
    points = load_scatter(
        selected_tree, "tree", "x", "vector", entry_start=1, entry_stop=3
    )
    np.testing.assert_array_equal(points.x, [1.1, 1.1])
    np.testing.assert_array_equal(points.y, [2, 4])


def test_automatic_range_uses_only_selected_entries(selected_tree):
    hist = load_branch(
        selected_tree, "tree", "x", entry_start=1, entry_stop=3, n_bins=2
    )
    np.testing.assert_allclose(hist.axes[0].edges[[0, -1]], [1.1, 2.1])
    np.testing.assert_array_equal(hist.values, [1, 1])


@pytest.mark.parametrize("start, stop", [(2, 2), (100, None)])
def test_empty_selection_preserves_sparse_bin_and_scatter_conventions(
    selected_tree, start, stop
):
    kwargs = dict(entry_start=start, entry_stop=stop)
    profile = load_branch(selected_tree, "tree", "x", "y", range=(0, 4), **kwargs)
    assert not profile.values.any() and not profile.variances.any()
    assert np.isnan(profile.spread_min).all()
    assert len(load_scatter(selected_tree, "tree", "x", "y", **kwargs).x) == 0
    with pytest.raises(ValueError, match="Automatic range"):
        load_branch(selected_tree, "tree", "x", **kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"entry_start": -1},
        {"entry_start": None},
        {"entry_stop": -1},
        {"entry_start": 0.5},
        {"entry_stop": True},
        {"entry_start": 3, "entry_stop": 2},
    ],
)
@pytest.mark.parametrize("reader", [load_branch, load_scatter])
def test_invalid_entry_bounds_fail_before_opening_a_file(reader, kwargs):
    branches = ["x"] if reader is load_branch else ["x", "y"]
    with pytest.raises(ValueError, match="entry_"):
        reader("not-opened.root", "tree", *branches, **kwargs)
