"""Numerical regression cases for profiles computed from TTree branches."""

from decimal import Decimal, localcontext
from pathlib import Path

import boost_histogram as bh
import numpy as np
import pytest
import uproot

from unrooted.io.boost import load as load_boost
from unrooted.io.root import load_branch


def _write_tree(path: Path, x: np.ndarray, **branches: np.ndarray) -> None:
    with uproot.recreate(path) as root_file:
        data = {"x": x, **branches}
        root_file.mktree("tree", {name: array.dtype for name, array in data.items()})
        root_file["tree"].extend(data)


def test_profile_bin_boundaries_match_count_histogram(tmp_path: Path) -> None:
    path = tmp_path / "boundaries.root"
    _write_tree(path, np.array([0.0, 1.0, 2.0]), y=np.array([10.0, 20.0, 30.0]))

    counts = load_branch(path, "tree", "x", n_bins=2, range=(0.0, 2.0))
    profile = load_branch(path, "tree", "x", "y", n_bins=2, range=(0.0, 2.0))

    np.testing.assert_array_equal(counts.values, [1.0, 2.0])
    np.testing.assert_allclose(profile.values, [10.0, 25.0])
    np.testing.assert_allclose(profile.spread_min, [10.0, 20.0])
    np.testing.assert_allclose(profile.spread_max, [10.0, 30.0])


def test_profile_values_adjacent_to_edges(tmp_path: Path) -> None:
    path = tmp_path / "adjacent.root"
    x = np.array([
        np.nextafter(0.0, -np.inf),
        0.0,
        np.nextafter(1.0, -np.inf),
        1.0,
        np.nextafter(1.0, np.inf),
        np.nextafter(2.0, -np.inf),
        2.0,
        np.nextafter(2.0, np.inf),
    ])
    y = np.array([999.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 999.0])
    _write_tree(path, x, y=y)

    profile = load_branch(path, "tree", "x", "y", n_bins=2, range=(0.0, 2.0))

    np.testing.assert_allclose(profile.values, [15.0, 45.0])
    np.testing.assert_allclose(profile.spread_min, [10.0, 30.0])
    np.testing.assert_allclose(profile.spread_max, [20.0, 60.0])


@pytest.mark.parametrize("offset", [1e8, 1e9, 1e12])
def test_profile_variance_is_invariant_under_large_offsets(
    tmp_path: Path, offset: float,
) -> None:
    path = tmp_path / "offset.root"
    x = np.full(4, 0.5)
    y = np.array([-1.0, 1.0, -2.0, 2.0])
    _write_tree(path, x, y=y, shifted=y + offset)

    reference = load_branch(path, "tree", "x", "y", n_bins=1, range=(0.0, 1.0))
    shifted = load_branch(
        path, "tree", "x", "shifted", n_bins=1, range=(0.0, 1.0),
    )

    assert reference.variances[0] > 0.0
    np.testing.assert_array_equal(shifted.values, reference.values + offset)
    np.testing.assert_allclose(shifted.variances, reference.variances, rtol=1e-12)


def test_profile_variance_stays_nonnegative_after_cancellation_case(
    tmp_path: Path,
) -> None:
    path = tmp_path / "cancellation.root"
    y = np.array([
        999999999.6834046, 999999999.6776109,
        1000000000.0971674, 999999998.4740696,
        1000000001.1921661, 999999999.3289104,
        1000000001.0002694, 1000000000.1363211,
    ])
    _write_tree(path, np.full(y.size, 0.5), y=y, centered=y - 1e9)

    profile = load_branch(path, "tree", "x", "y", n_bins=1, range=(0.0, 1.0))
    centered = load_branch(
        path, "tree", "x", "centered", n_bins=1, range=(0.0, 1.0),
    )

    assert np.all(profile.variances > 0.0)
    assert np.all(np.isfinite(profile.errors))
    np.testing.assert_allclose(profile.variances, centered.variances, rtol=1e-12)


@pytest.mark.parametrize("value", [1e12, 1e200])
def test_constant_profile_has_zero_variance(tmp_path: Path, value: float) -> None:
    path = tmp_path / "constant.root"
    _write_tree(path, np.full(4, 0.5), y=np.full(4, value))

    with np.errstate(over="raise", invalid="raise"):
        profile = load_branch(path, "tree", "x", "y", n_bins=1, range=(0.0, 1.0))

    np.testing.assert_array_equal(profile.values, [value])
    np.testing.assert_array_equal(profile.variances, [0.0])


def test_profile_accumulation_with_many_values_at_large_offset(tmp_path: Path) -> None:
    path = tmp_path / "many.root"
    y = 1e12 + np.tile([0.1, 0.2, 0.3, 0.4], 4096)
    _write_tree(path, np.full(y.size, 0.5), y=y, centered=y - 1e12)

    profile = load_branch(path, "tree", "x", "y", n_bins=1, range=(0.0, 1.0))
    centered = load_branch(
        path, "tree", "x", "centered", n_bins=1, range=(0.0, 1.0),
    )

    np.testing.assert_allclose(profile.variances, centered.variances, rtol=1e-12)


def test_profile_population_variance_and_sparse_bins(tmp_path: Path) -> None:
    path = tmp_path / "population.root"
    x = np.array([0.1, 0.2, 1.1, 1.2, 1.3, 2.1])
    y = np.array([1.0, 3.0, 2.0, 4.0, 6.0, 7.0])
    _write_tree(path, x, y=y)

    profile = load_branch(path, "tree", "x", "y", n_bins=4, range=(0.0, 4.0))

    # M2 is 2 and 8 in the populated multi-entry bins, with N = 2 and 3.
    np.testing.assert_array_equal(profile.values, [2.0, 4.0, 7.0, 0.0])
    np.testing.assert_allclose(profile.variances, [0.5, 8.0 / 9.0, 0.0, 0.0])
    np.testing.assert_allclose(profile.errors, np.sqrt([0.5, 8.0 / 9.0, 0.0, 0.0]))
    np.testing.assert_allclose(profile.spread_min, [1.0, 2.0, 7.0, np.nan])
    np.testing.assert_allclose(profile.spread_max, [3.0, 6.0, 7.0, np.nan])


@pytest.mark.parametrize("x", [np.array([]), np.array([-2.0, -1.0, 4.1])])
def test_profile_without_in_range_entries(tmp_path: Path, x: np.ndarray) -> None:
    path = tmp_path / "empty.root"
    _write_tree(path, x, y=np.ones(x.size))

    with np.errstate(divide="raise", invalid="raise"):
        profile = load_branch(path, "tree", "x", "y", n_bins=4, range=(0.0, 4.0))

    np.testing.assert_array_equal(profile.values, np.zeros(4))
    np.testing.assert_array_equal(profile.variances, np.zeros(4))
    assert np.all(np.isnan(profile.spread_min))
    assert np.all(np.isnan(profile.spread_max))


def test_populated_zero_profile_has_observed_spread(tmp_path: Path) -> None:
    path = tmp_path / "zero.root"
    _write_tree(path, np.array([0.1, 0.2]), y=np.zeros(2))

    profile = load_branch(path, "tree", "x", "y", n_bins=2, range=(0.0, 2.0))

    np.testing.assert_array_equal(profile.values, [0.0, 0.0])
    np.testing.assert_array_equal(profile.variances, [0.0, 0.0])
    np.testing.assert_allclose(profile.spread_min, [0.0, np.nan])
    np.testing.assert_allclose(profile.spread_max, [0.0, np.nan])


def test_branch_and_boost_profile_conventions(tmp_path: Path) -> None:
    path = tmp_path / "boost-reference.root"
    x = np.array([0.1, 0.2, 1.1, 1.2, 1.3, 2.1])
    y = np.array([1.0, 3.0, 2.0, 4.0, 6.0, 7.0])
    _write_tree(path, x, y=y)
    profile = load_branch(path, "tree", "x", "y", n_bins=4, range=(0.0, 4.0))

    histogram = bh.Histogram(bh.axis.Regular(4, 0.0, 4.0), storage=bh.storage.Mean())
    histogram.fill(x, sample=y)
    boost_profile = load_boost(histogram)

    np.testing.assert_array_equal(profile.values, boost_profile.values)
    np.testing.assert_allclose(boost_profile.variances, [1.0, 4.0 / 3.0, 0.0, 0.0])
    # Boost Mean uses M2/(N*(N-1)); branch profiles retain M2/N^2.
    counts = np.array([2.0, 3.0])
    np.testing.assert_allclose(
        profile.variances[:2],
        boost_profile.variances[:2] * (counts - 1.0) / counts,
    )
    # Boost spread is mean +/- sample standard deviation, rather than extrema.
    np.testing.assert_allclose(
        boost_profile.spread_min, [2.0 - np.sqrt(2.0), 2.0, 7.0, np.nan],
    )
    np.testing.assert_allclose(
        boost_profile.spread_max, [2.0 + np.sqrt(2.0), 6.0, 7.0, np.nan],
    )


def test_profile_matches_high_precision_reference(tmp_path: Path) -> None:
    path = tmp_path / "decimal-reference.root"
    rng = np.random.default_rng(71)
    x = rng.uniform(0.0, 4.0, 1000)
    y = 1e12 + rng.normal(size=x.size)
    _write_tree(path, x, y=y)
    profile = load_branch(path, "tree", "x", "y", n_bins=4, range=(0.0, 4.0))

    means, variances = [], []
    with localcontext() as context:
        context.prec = 80
        for left, right in zip(range(4), range(1, 5)):
            values = [Decimal.from_float(v) for v in y[(x >= left) & (x < right)]]
            mean = sum(values) / len(values)
            means.append(float(mean))
            variances.append(float(sum((v - mean)**2 for v in values) / len(values)**2))

    np.testing.assert_allclose(profile.values, means, rtol=0.0, atol=np.spacing(1e12))
    np.testing.assert_allclose(profile.variances, variances, rtol=1e-12)
