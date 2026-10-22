"""Analytic Wilson references and identical efficiency rules for both readers."""

from pathlib import Path

import boost_histogram as bh
import numpy as np
import pytest
import uproot

from unrooted.io.boost import reader as boost_reader
from unrooted.io.root import reader as root_reader

DATA_DIR = Path(__file__).parent.parent / "data" / "root"


def count_hist(values, edges=None):
    if edges is None:
        edges = np.arange(len(values) + 1, dtype=float)
    hist = bh.Histogram(bh.axis.Variable(edges))
    hist.view()[:] = values
    return hist


@pytest.fixture(params=["boost", "root"])
def efficiency_reader(request, tmp_path):
    def read(accepted, total, *, edges=None, total_edges=None, **kwargs):
        passed = count_hist(accepted, edges)
        all_events = count_hist(
            total, total_edges if total_edges is not None else edges
        )
        if request.param == "boost":
            return boost_reader.load_efficiency(passed, all_events, **kwargs)
        path = tmp_path / "counts.root"
        with np.errstate(all="ignore"), uproot.recreate(path) as f:
            f["passed"] = passed
            f["total"] = all_events
        return root_reader.load_efficiency(path, "passed", "total", **kwargs)

    return read


def test_wilson_default_matches_analytic_one_sigma_reference(efficiency_reader):
    # At z=1, N=4: endpoint width 1/(N+1), central radius sqrt(5)/10.
    hist = efficiency_reader([0, 2, 4, 0], [4, 4, 4, 0])
    np.testing.assert_allclose(hist.values, [0, 0.5, 1, np.nan])
    np.testing.assert_allclose(hist.variances, [0, 0.0625, 0, np.nan])
    np.testing.assert_allclose(
        hist.spread_min, [0, 0.5 - np.sqrt(5) / 10, 0.8, np.nan], atol=1e-15
    )
    np.testing.assert_allclose(
        hist.spread_max, [0.2, 0.5 + np.sqrt(5) / 10, 1, np.nan], atol=1e-15
    )


def test_wilson_95_percent_known_reference_and_variance_unchanged(efficiency_reader):
    default = efficiency_reader([2], [4])
    wide = efficiency_reader([2], [4], confidence_level=0.95)
    # Wilson score interval for 2 successes in 4 trials, z=1.959963984540054.
    np.testing.assert_allclose(wide.spread_min, [0.15003898915214947], rtol=1e-13)
    np.testing.assert_allclose(wide.spread_max, [0.8499610108478506], rtol=1e-13)
    np.testing.assert_array_equal(default.variances, wide.variances)
    assert wide.spread_min[0] < default.spread_min[0]
    assert wide.spread_max[0] > default.spread_max[0]


@pytest.mark.parametrize("level", [0, 1, -1, np.nan, np.inf, "bad", None])
def test_efficiency_rejects_invalid_confidence(efficiency_reader, level):
    with pytest.raises(ValueError, match="confidence_level"):
        efficiency_reader([1], [2], confidence_level=level)


@pytest.mark.parametrize(
    ("passed", "total", "message"),
    [
        ([3], [2], "must not exceed"),
        ([0.5], [2], "integers"),
        ([1], [2.5], "integers"),
        ([-1], [2], "nonnegative"),
        ([0], [-1], "nonnegative"),
        ([np.nan], [2], "finite"),
        ([1], [np.nan], "finite"),
        ([np.inf], [2], "finite"),
    ],
)
def test_efficiency_rejects_invalid_counts(efficiency_reader, passed, total, message):
    with pytest.raises(ValueError, match=message):
        efficiency_reader(passed, total)


def test_efficiency_requires_exact_edges_even_at_large_offsets(efficiency_reader):
    with pytest.raises(ValueError, match="Bin edges"):
        efficiency_reader(
            [1], [2], edges=[1e12, 1e12 + 1], total_edges=[1e12, 1e12 + 2]
        )


@pytest.mark.parametrize(
    "storage", [bh.storage.Weight, bh.storage.Mean, bh.storage.WeightedMean]
)
def test_boost_efficiency_rejects_non_count_storage(storage):
    source = bh.Histogram(bh.axis.Regular(1, 0, 1), storage=storage())
    with pytest.raises(ValueError, match="unweighted count storage"):
        boost_reader.load_efficiency(source, source)


def test_both_readers_reject_multidimensional_efficiencies(tmp_path):
    source = bh.Histogram(bh.axis.Regular(1, 0, 1), bh.axis.Regular(1, 0, 1))
    with pytest.raises(ValueError, match="one-dimensional"):
        boost_reader.load_efficiency(source, source)
    path = tmp_path / "two_dimensions.root"
    with uproot.recreate(path) as f:
        f["counts"] = source
    with pytest.raises(ValueError, match="one-dimensional"):
        root_reader.load_efficiency(path, "counts", "counts")


def test_root_efficiency_rejects_weighted_variances_but_accepts_unit_weights(tmp_path):
    path = tmp_path / "weights.root"
    weighted = bh.Histogram(bh.axis.Regular(1, 0, 1), storage=bh.storage.Weight())
    weighted.fill([0.5], weight=[2])
    unit = bh.Histogram(bh.axis.Regular(1, 0, 1), storage=bh.storage.Weight())
    unit.fill([0.5, 0.5], weight=[1, 1])
    with uproot.recreate(path) as f:
        f["weighted"] = weighted
        f["unit"] = unit
    with pytest.raises(ValueError, match="Poisson variances"):
        root_reader.load_efficiency(path, "weighted", "weighted")
    assert root_reader.load_efficiency(path, "unit", "unit").values[0] == 1


def test_root_efficiency_rejects_profiles():
    with pytest.raises(ValueError, match="TH1 count"):
        root_reader.load_efficiency(DATA_DIR / "tests_input.root", "profX", "profX")


def test_float32_count_inputs_use_float64_arithmetic():
    from unrooted.core._efficiency import binomial_efficiency
    from unrooted.core.axis import Axis
    from unrooted.core.histogram import Histogram

    passed = Histogram(
        [Axis([0, 1])], np.array([1], dtype=np.float32), np.array([1], dtype=np.float32)
    )
    total = Histogram(
        [Axis([0, 1])], np.array([3], dtype=np.float32), np.array([3], dtype=np.float32)
    )
    result = binomial_efficiency(passed, total)
    assert result.values[0] == 1 / 3
    assert result.variances[0] == pytest.approx(2 / 27, rel=1e-15)


def test_boost_efficiency_rejects_integer_weighted_scalar_fills():
    source = bh.Histogram(bh.axis.Regular(1, 0, 1))
    source.fill([.5], weight=[2])
    with pytest.raises(ValueError, match="weighted scalar fills"):
        boost_reader.load_efficiency(source, source)
