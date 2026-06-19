from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

uproot = pytest.importorskip("uproot")

from unrooted.io.root.tree import load_branch, load_scatter  # noqa: E402

INPUT = Path(__file__).parent.parent / "data" / "root" / "tests_input.root"
JAGGED = Path(__file__).parent.parent / "data" / "root" / "tests_trees_jagged.root"


# ---------------------------------------------------------------------------
# Count histograms — scalar branch (tests_input.root / tree / x, 1 000 entries)
# ---------------------------------------------------------------------------


def test_count_scalar_ndim():
    h = load_branch(INPUT, "tree", "x")
    assert h.ndim == 1


def test_count_scalar_n_bins_default():
    h = load_branch(INPUT, "tree", "x")
    assert h.values.shape[0] == 100
    assert len(h.axes[0].edges) == 101


def test_count_scalar_custom_n_bins():
    h = load_branch(INPUT, "tree", "x", n_bins=50)
    assert h.values.shape[0] == 50
    assert len(h.axes[0].edges) == 51


def test_count_scalar_auto_range():
    import awkward as ak
    import uproot as _uproot

    h = load_branch(INPUT, "tree", "x")
    with _uproot.open(INPUT) as f:  # type: ignore[union-attr]
        data = np.asarray(ak.flatten(f["tree"]["x"].array(library="ak"), axis=None))  # type: ignore[union-attr,arg-type]
    assert h.axes[0].edges[0] == pytest.approx(float(data.min()))
    assert h.axes[0].edges[-1] == pytest.approx(float(data.max()))


def test_count_scalar_given_range():
    h = load_branch(INPUT, "tree", "x", range=(-3.0, 3.0))
    assert h.axes[0].edges[0] == pytest.approx(-3.0)
    assert h.axes[0].edges[-1] == pytest.approx(3.0)


def test_count_scalar_total_entries():
    # Auto-range covers all data → sum of bin counts == total entries.
    h = load_branch(INPUT, "tree", "x")
    assert int(h.values.sum()) == 1000


def test_count_scalar_variances_eq_values():
    h = load_branch(INPUT, "tree", "x")
    np.testing.assert_array_equal(h.variances, h.values)


def test_count_scalar_name():
    h = load_branch(INPUT, "tree", "x")
    assert h.name == "x"


def test_count_scalar_label_default():
    h = load_branch(INPUT, "tree", "x")
    assert h.axes[0].label == "x"


def test_count_scalar_label_custom():
    h = load_branch(INPUT, "tree", "x", label="position")
    assert h.axes[0].label == "position"


def test_count_scalar_no_spread():
    h = load_branch(INPUT, "tree", "x")
    assert h.spread_min is None
    assert h.spread_max is None


# ---------------------------------------------------------------------------
# Count histograms — vector and jagged branches (jagged_tree)
# ---------------------------------------------------------------------------


def test_count_vector_ndim():
    # scalar branch inside a jagged tree
    h = load_branch(JAGGED, "jagged_tree", "x")
    assert h.ndim == 1


def test_count_vector_total_entries():
    h = load_branch(JAGGED, "jagged_tree", "x")
    assert int(h.values.sum()) == 10


def test_count_jagged_ndim():
    h = load_branch(JAGGED, "jagged_tree", "xj")
    assert h.ndim == 1


def test_count_jagged_total_entries():
    # xj: 10 events, 24 values unrolled
    h = load_branch(JAGGED, "jagged_tree", "xj")
    assert int(h.values.sum()) == 24


def test_count_jagged_name():
    h = load_branch(JAGGED, "jagged_tree", "xj")
    assert h.name == "xj"


# ---------------------------------------------------------------------------
# Profile — Case 1: trivial x × trivial y  (tree/x vs tree/y, 1 000 events)
# ---------------------------------------------------------------------------


def test_profile_trivial_trivial_ndim():
    h = load_branch(INPUT, "tree", "x", "y")
    assert h.ndim == 1


def test_profile_trivial_trivial_name():
    h = load_branch(INPUT, "tree", "x", "y")
    assert h.name == "y"


def test_profile_trivial_trivial_label_default():
    h = load_branch(INPUT, "tree", "x", "y")
    assert h.axes[0].label == "x"


def test_profile_trivial_trivial_label_custom():
    h = load_branch(INPUT, "tree", "x", "y", label="x [mm]")
    assert h.axes[0].label == "x [mm]"


def test_profile_trivial_trivial_spread_set():
    h = load_branch(INPUT, "tree", "x", "y")
    assert h.spread_min is not None
    assert h.spread_max is not None
    assert h.spread_min.shape == h.values.shape
    assert h.spread_max.shape == h.values.shape


def test_profile_trivial_trivial_variances_nonneg():
    h = load_branch(INPUT, "tree", "x", "y")
    assert np.all(h.variances >= 0)


def test_profile_trivial_trivial_spread_min_le_max():
    h = load_branch(INPUT, "tree", "x", "y")
    assert h.spread_min is not None and h.spread_max is not None
    populated = ~np.isnan(h.spread_min)
    assert np.all(h.spread_min[populated] <= h.spread_max[populated])


def test_profile_trivial_trivial_empty_bins_nan():
    # Narrow range → outer bins empty → NaN spread
    h = load_branch(INPUT, "tree", "x", "y", range=(-1.0, 1.0), n_bins=200)
    assert np.any(np.isnan(h.spread_min))  # type: ignore[arg-type]
    assert np.any(np.isnan(h.spread_max))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Profile — Case 2: trivial x × vector y  (jagged_tree/x × jagged_tree/yj)
#
# x has 10 scalar entries; yj has 10 events × variable length (24 values
# total).  ak.broadcast_arrays replicates each x[i] once per yj[i] element,
# yielding 24 (x, y) pairs.
# ---------------------------------------------------------------------------


def test_profile_trivial_vector_ndim():
    h = load_branch(JAGGED, "jagged_tree", "x", "yj")
    assert h.ndim == 1


def test_profile_trivial_vector_spread_set():
    h = load_branch(JAGGED, "jagged_tree", "x", "yj")
    assert h.spread_min is not None and h.spread_max is not None


def test_profile_trivial_vector_variances_nonneg():
    h = load_branch(JAGGED, "jagged_tree", "x", "yj")
    assert np.all(h.variances >= 0)


def test_profile_trivial_vector_name():
    h = load_branch(JAGGED, "jagged_tree", "x", "yj")
    assert h.name == "yj"


# ---------------------------------------------------------------------------
# Profile — Case 3: trivial x × jagged y  (jagged_tree/x × jagged_tree/ykl)
#
# ykl is std::vector<std::vector<double>>.  x[i] broadcasts to all 79 values
# obtained by fully flattening ykl.
# ---------------------------------------------------------------------------


def test_profile_trivial_jagged_ndim():
    h = load_branch(JAGGED, "jagged_tree", "x", "ykl")
    assert h.ndim == 1


def test_profile_trivial_jagged_spread_set():
    h = load_branch(JAGGED, "jagged_tree", "x", "ykl")
    assert h.spread_min is not None and h.spread_max is not None


def test_profile_trivial_jagged_variances_nonneg():
    h = load_branch(JAGGED, "jagged_tree", "x", "ykl")
    assert np.all(h.variances >= 0)


def test_profile_trivial_jagged_name():
    h = load_branch(JAGGED, "jagged_tree", "x", "ykl")
    assert h.name == "ykl"


# ---------------------------------------------------------------------------
# Profile — Case 4: vector x × vector y  (jagged_tree/xj × jagged_tree/yj)
#
# xj and yj share identical per-event lengths [1,2,3,4,1,2,4,5,1,1] → 24
# element-by-element pairs after zipping.
# ---------------------------------------------------------------------------


def test_profile_vector_vector_ndim():
    h = load_branch(JAGGED, "jagged_tree", "xj", "yj")
    assert h.ndim == 1


def test_profile_vector_vector_spread_set():
    h = load_branch(JAGGED, "jagged_tree", "xj", "yj")
    assert h.spread_min is not None and h.spread_max is not None


def test_profile_vector_vector_variances_nonneg():
    h = load_branch(JAGGED, "jagged_tree", "xj", "yj")
    assert np.all(h.variances >= 0)


def test_profile_vector_vector_name():
    h = load_branch(JAGGED, "jagged_tree", "xj", "yj")
    assert h.name == "yj"


# ---------------------------------------------------------------------------
# Profile — Case 5: vector x × jagged y  (jagged_tree/xkl × jagged_tree/ykl)
#
# xkl and ykl are both std::vector<std::vector<double>> with identical nested
# shapes → 79 element-by-element pairs after zipping.
# ---------------------------------------------------------------------------


def test_profile_jagged_jagged_ndim():
    h = load_branch(JAGGED, "jagged_tree", "xkl", "ykl")
    assert h.ndim == 1


def test_profile_jagged_jagged_spread_set():
    h = load_branch(JAGGED, "jagged_tree", "xkl", "ykl")
    assert h.spread_min is not None and h.spread_max is not None


def test_profile_jagged_jagged_variances_nonneg():
    h = load_branch(JAGGED, "jagged_tree", "xkl", "ykl")
    assert np.all(h.variances >= 0)


def test_profile_jagged_jagged_name():
    h = load_branch(JAGGED, "jagged_tree", "xkl", "ykl")
    assert h.name == "ykl"


def test_profile_jagged_jagged_spread_min_le_max():
    h = load_branch(JAGGED, "jagged_tree", "xkl", "ykl")
    assert h.spread_min is not None and h.spread_max is not None
    populated = ~np.isnan(h.spread_min)
    assert np.all(h.spread_min[populated] <= h.spread_max[populated])


# ---------------------------------------------------------------------------
# Scatter — load_scatter (scalar × scalar)
# ---------------------------------------------------------------------------


def test_scatter_returns_scatter_data():
    from unrooted.core.scatter import ScatterData

    sd = load_scatter(INPUT, "tree", "x", "y")
    assert isinstance(sd, ScatterData)


def test_scatter_lengths_equal():
    sd = load_scatter(INPUT, "tree", "x", "y")
    assert len(sd.x) == len(sd.y)


def test_scatter_total_entries():
    # scalar × scalar → 1 000 pairs
    sd = load_scatter(INPUT, "tree", "x", "y")
    assert len(sd.x) == 1000


def test_scatter_name():
    sd = load_scatter(INPUT, "tree", "x", "y")
    assert sd.name == "y"


def test_scatter_labels_default():
    sd = load_scatter(INPUT, "tree", "x", "y")
    assert sd.x_label == "x"
    assert sd.y_label == "y"


def test_scatter_labels_custom():
    sd = load_scatter(INPUT, "tree", "x", "y", label_x="η", label_y="X₀")
    assert sd.x_label == "η"
    assert sd.y_label == "X₀"


def test_scatter_no_binning():
    # Values are raw floats, not histogram counts — no integer constraint.
    sd = load_scatter(INPUT, "tree", "x", "y")
    assert sd.x.dtype == float
    assert sd.y.dtype == float


# ---------------------------------------------------------------------------
# Scatter — load_scatter (trivial x × vector y via jagged tree)
# ---------------------------------------------------------------------------


def test_scatter_trivial_vector_total():
    # x is scalar (10 events), yj is vector → 24 pairs after broadcast
    sd = load_scatter(JAGGED, "jagged_tree", "x", "yj")
    assert len(sd.x) == 24


def test_scatter_trivial_vector_lengths_equal():
    sd = load_scatter(JAGGED, "jagged_tree", "x", "yj")
    assert len(sd.x) == len(sd.y)
