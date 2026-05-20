from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

uproot = pytest.importorskip("uproot")

from unrooted.io.root.tree import load_branch  # noqa: E402

INPUT = Path(__file__).parent.parent / "data" / "root" / "tests_input.root"
JAGGED = Path(__file__).parent.parent / "data" / "root" / "tests_trees_jagged.root"


# ---------------------------------------------------------------------------
# Trivial scalar branch: tests_input.root / tree / x  (1 000 entries)
# ---------------------------------------------------------------------------


def test_trivial_branch_ndim():
    h = load_branch(INPUT, "tree", "x")
    assert h.ndim == 1


def test_trivial_branch_n_bins_default():
    h = load_branch(INPUT, "tree", "x")
    assert h.values.shape[0] == 100
    assert len(h.axes[0].edges) == 101


def test_trivial_branch_custom_n_bins():
    h = load_branch(INPUT, "tree", "x", n_bins=50)
    assert h.values.shape[0] == 50
    assert len(h.axes[0].edges) == 51


def test_trivial_branch_auto_range():
    h = load_branch(INPUT, "tree", "x")
    import awkward as ak
    import uproot as _uproot

    with _uproot.open(INPUT) as f:
        data = np.asarray(ak.flatten(f["tree"]["x"].array(library="ak"), axis=None))
    assert h.axes[0].edges[0] == pytest.approx(float(data.min()))
    assert h.axes[0].edges[-1] == pytest.approx(float(data.max()))


def test_trivial_branch_given_range():
    h = load_branch(INPUT, "tree", "x", range=(-3.0, 3.0))
    assert h.axes[0].edges[0] == pytest.approx(-3.0)
    assert h.axes[0].edges[-1] == pytest.approx(3.0)


def test_trivial_branch_count_sum():
    # Auto-range covers all data → sum of bin counts == total entries.
    h = load_branch(INPUT, "tree", "x")
    assert int(h.values.sum()) == 1000


def test_trivial_branch_variances_eq_values():
    h = load_branch(INPUT, "tree", "x")
    np.testing.assert_array_equal(h.variances, h.values)


def test_trivial_branch_name():
    h = load_branch(INPUT, "tree", "x")
    assert h.name == "x"


def test_trivial_branch_label_default():
    h = load_branch(INPUT, "tree", "x")
    assert h.axes[0].label == "x"


def test_trivial_branch_label_custom():
    h = load_branch(INPUT, "tree", "x", label="position")
    assert h.axes[0].label == "position"


# ---------------------------------------------------------------------------
# Scalar branch in jagged tree: jagged_tree / x  (10 entries)
# ---------------------------------------------------------------------------


def test_vector_branch_ndim():
    h = load_branch(JAGGED, "jagged_tree", "x")
    assert h.ndim == 1


def test_vector_branch_count_sum():
    h = load_branch(JAGGED, "jagged_tree", "x")
    assert int(h.values.sum()) == 10


# ---------------------------------------------------------------------------
# Jagged vector branch: jagged_tree / xj  (10 events → 24 values unrolled)
# ---------------------------------------------------------------------------


def test_jagged_branch_ndim():
    h = load_branch(JAGGED, "jagged_tree", "xj")
    assert h.ndim == 1


def test_jagged_branch_count_sum():
    h = load_branch(JAGGED, "jagged_tree", "xj")
    assert int(h.values.sum()) == 24


def test_jagged_branch_name():
    h = load_branch(JAGGED, "jagged_tree", "xj")
    assert h.name == "xj"


# ---------------------------------------------------------------------------
# Profile histogram
# ---------------------------------------------------------------------------


def test_profile_trivial_ndim():
    h = load_branch(INPUT, "tree", "x", profile=True)
    assert h.ndim == 1


def test_profile_no_spread_for_count():
    h = load_branch(INPUT, "tree", "x")
    assert h.spread_min is None
    assert h.spread_max is None


def test_profile_spread_set():
    h = load_branch(INPUT, "tree", "x", profile=True)
    assert h.spread_min is not None
    assert h.spread_max is not None
    assert h.spread_min.shape == h.values.shape
    assert h.spread_max.shape == h.values.shape


def test_profile_values_are_means():
    h = load_branch(INPUT, "tree", "x", profile=True)
    import awkward as ak
    import uproot as _uproot

    with _uproot.open(INPUT) as f:
        data = np.asarray(ak.flatten(f["tree"]["x"].array(library="ak"), axis=None))
    lo, hi = float(data.min()), float(data.max())
    # Populated bins have means within the data range.
    populated = ~np.isnan(h.spread_min)
    assert np.all(h.values[populated] >= lo - 1e-9)
    assert np.all(h.values[populated] <= hi + 1e-9)


def test_profile_empty_bins_nan_spread():
    # Use a narrow given range so the outer bins are empty.
    h = load_branch(INPUT, "tree", "x", range=(-1.0, 1.0), n_bins=200, profile=True)
    # With 200 bins over [-1,1] and 1000 Gaussian entries many outer bins will be empty.
    assert np.any(np.isnan(h.spread_min))
    assert np.any(np.isnan(h.spread_max))


def test_profile_variances_nonneg():
    h = load_branch(INPUT, "tree", "x", profile=True)
    assert np.all(h.variances >= 0)


def test_profile_spread_min_le_max():
    h = load_branch(INPUT, "tree", "x", profile=True)
    assert h.spread_min is not None and h.spread_max is not None
    populated = ~np.isnan(h.spread_min)
    assert np.all(h.spread_min[populated] <= h.spread_max[populated])


def test_profile_jagged_unrolled():
    h = load_branch(JAGGED, "jagged_tree", "xj", profile=True)
    assert h.ndim == 1
    assert h.spread_min is not None
    assert h.spread_max is not None
