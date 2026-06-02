from pathlib import Path
import pickle

import boost_histogram as bh
import numpy as np
import pytest

from unrooted.io.boost.reader import load, load_efficiency

DATA_DIR = Path(__file__).parent.parent / "data" / "boost"


@pytest.fixture(scope="module")
def boost_data() -> dict:
    with open(DATA_DIR / "test_input_boost.pkl", "rb") as f:
        return pickle.load(f)  # type: ignore[no-any-return]


@pytest.fixture(scope="module")
def profile_hist(boost_data: dict) -> bh.Histogram:
    return boost_data["nMeasurements_vs_eta"]


@pytest.fixture(scope="module")
def eff_data(boost_data: dict) -> dict:
    return boost_data["trackeff_vs_eta"]


# ---------------------------------------------------------------------------
# load — Mean (profile) storage
# ---------------------------------------------------------------------------


def test_load_mean_ndim(profile_hist: bh.Histogram) -> None:
    hist = load(profile_hist, name="nMeasurements_vs_eta")
    assert hist.ndim == 1


def test_load_mean_name(profile_hist: bh.Histogram) -> None:
    hist = load(profile_hist, name="nMeasurements_vs_eta")
    assert hist.name == "nMeasurements_vs_eta"


def test_load_mean_axis_label(profile_hist: bh.Histogram) -> None:
    hist = load(profile_hist)
    assert hist.axes[0].label == "#eta"


def test_load_mean_shape(profile_hist: bh.Histogram) -> None:
    hist = load(profile_hist)
    n = hist.values.shape[0]
    assert len(hist.axes[0].edges) == n + 1
    assert hist.variances.shape == hist.values.shape


def test_load_mean_overflow_present(profile_hist: bh.Histogram) -> None:
    hist = load(profile_hist)
    assert hist.overflow is not None
    assert hist.overflow.shape[0] == hist.values.shape[0] + 2


def test_load_mean_spread_present(profile_hist: bh.Histogram) -> None:
    hist = load(profile_hist)
    assert hist.spread_min is not None
    assert hist.spread_max is not None


def test_load_mean_spread_shape(profile_hist: bh.Histogram) -> None:
    hist = load(profile_hist)
    assert hist.spread_min is not None
    assert hist.spread_max is not None
    assert hist.spread_min.shape == hist.values.shape
    assert hist.spread_max.shape == hist.values.shape


def test_load_mean_spread_ordering(profile_hist: bh.Histogram) -> None:
    """Filled bins must satisfy spread_min <= values <= spread_max."""
    hist = load(profile_hist)
    assert hist.spread_min is not None
    assert hist.spread_max is not None
    mask = ~np.isnan(hist.spread_min)
    assert np.all(hist.spread_min[mask] <= hist.values[mask] + 1e-12)
    assert np.all(hist.spread_max[mask] >= hist.values[mask] - 1e-12)


def test_load_mean_empty_bins_nan_spread(profile_hist: bh.Histogram) -> None:
    """Bins with count == 0 must have nan spread."""
    hist = load(profile_hist)
    assert hist.spread_min is not None
    view = profile_hist.view(flow=False)
    empty = np.asarray(view["count"]) == 0  # type: ignore[index]
    if empty.any():
        assert np.all(np.isnan(hist.spread_min[empty]))


def test_load_mean_no_spread_for_double_storage() -> None:
    """A regular Double-storage histogram must not get spread fields."""
    h = bh.Histogram(bh.axis.Regular(10, 0, 1), storage=bh.storage.Double())
    h.fill([0.1, 0.2, 0.5])
    hist = load(h)
    assert hist.spread_min is None
    assert hist.spread_max is None


# ---------------------------------------------------------------------------
# load — scalar (Double) storage
# ---------------------------------------------------------------------------


def test_load_double_ndim() -> None:
    h = bh.Histogram(bh.axis.Regular(10, 0, 1), storage=bh.storage.Double())
    h.fill([0.1, 0.2, 0.5])
    hist = load(h, name="test")
    assert hist.ndim == 1


def test_load_double_shape() -> None:
    h = bh.Histogram(bh.axis.Regular(10, 0, 1), storage=bh.storage.Double())
    h.fill([0.1, 0.2, 0.5])
    hist = load(h)
    n = hist.values.shape[0]
    assert len(hist.axes[0].edges) == n + 1
    assert hist.variances.shape == hist.values.shape


def test_load_double_poisson_variance() -> None:
    """For Double storage variances should equal values (Poisson)."""
    h = bh.Histogram(bh.axis.Regular(5, 0, 5), storage=bh.storage.Double())
    h.fill([0.5, 0.5, 1.5, 3.5])
    hist = load(h)
    assert np.allclose(hist.values, hist.variances)


def test_load_double_overflow_shape() -> None:
    h = bh.Histogram(bh.axis.Regular(10, 0, 1), storage=bh.storage.Double())
    h.fill([0.5])
    hist = load(h)
    assert hist.overflow is not None
    assert hist.overflow.shape[0] == hist.values.shape[0] + 2


# ---------------------------------------------------------------------------
# load — Weight storage
# ---------------------------------------------------------------------------


def test_load_weight_variances() -> None:
    """Weight storage should expose per-bin variance, not copy of values."""
    h = bh.Histogram(bh.axis.Regular(5, 0, 5), storage=bh.storage.Weight())
    h.fill([0.5, 0.5, 1.5], weight=[1.0, 2.0, 3.0])
    hist = load(h)
    # bin 0: weights 1+2=3, weight² = 1+4=5 → variance=5
    assert np.isclose(hist.values[0], 3.0)
    assert np.isclose(hist.variances[0], 5.0)


# ---------------------------------------------------------------------------
# load_efficiency
# ---------------------------------------------------------------------------


def test_load_efficiency_ndim(eff_data: dict) -> None:
    hist = load_efficiency(eff_data["accepted"], eff_data["total"], name="trackeff_vs_eta")
    assert hist.ndim == 1


def test_load_efficiency_name(eff_data: dict) -> None:
    hist = load_efficiency(eff_data["accepted"], eff_data["total"], name="trackeff_vs_eta")
    assert hist.name == "trackeff_vs_eta"


def test_load_efficiency_axis_label(eff_data: dict) -> None:
    hist = load_efficiency(eff_data["accepted"], eff_data["total"])
    assert hist.axes[0].label == "#eta"


def test_load_efficiency_shape(eff_data: dict) -> None:
    hist = load_efficiency(eff_data["accepted"], eff_data["total"])
    n = hist.values.shape[0]
    assert len(hist.axes[0].edges) == n + 1
    assert hist.variances.shape == hist.values.shape


def test_load_efficiency_values_range(eff_data: dict) -> None:
    hist = load_efficiency(eff_data["accepted"], eff_data["total"])
    valid = ~np.isnan(hist.values)
    assert np.all(hist.values[valid] >= 0.0)
    assert np.all(hist.values[valid] <= 1.0)


def test_load_efficiency_spread_present(eff_data: dict) -> None:
    hist = load_efficiency(eff_data["accepted"], eff_data["total"])
    assert hist.spread_min is not None
    assert hist.spread_max is not None


def test_load_efficiency_spread_clamped(eff_data: dict) -> None:
    hist = load_efficiency(eff_data["accepted"], eff_data["total"])
    assert hist.spread_min is not None
    assert hist.spread_max is not None
    valid = ~np.isnan(hist.spread_min)
    assert np.all(hist.spread_min[valid] >= 0.0)
    assert np.all(hist.spread_max[valid] <= 1.0)


def test_load_efficiency_spread_ordering(eff_data: dict) -> None:
    hist = load_efficiency(eff_data["accepted"], eff_data["total"])
    assert hist.spread_min is not None
    assert hist.spread_max is not None
    valid = ~np.isnan(hist.spread_min)
    assert np.all(hist.spread_min[valid] <= hist.values[valid] + 1e-12)
    assert np.all(hist.spread_max[valid] >= hist.values[valid] - 1e-12)


def test_load_efficiency_known_values() -> None:
    """Verify exact efficiency for a synthetic pair (2 accepted of 4 total)."""
    edges = np.linspace(0, 1, 6)
    acc = bh.Histogram(bh.axis.Variable(edges), storage=bh.storage.Double())
    tot = bh.Histogram(bh.axis.Variable(edges), storage=bh.storage.Double())
    acc.view()[:] = [2.0, 2.0, 2.0, 2.0, 2.0]
    tot.view()[:] = [4.0, 4.0, 4.0, 4.0, 4.0]
    hist = load_efficiency(acc, tot)
    assert np.allclose(hist.values, 0.5)


def test_load_efficiency_shape_mismatch() -> None:
    acc = bh.Histogram(bh.axis.Regular(10, 0, 1), storage=bh.storage.Double())
    tot = bh.Histogram(bh.axis.Regular(5, 0, 1), storage=bh.storage.Double())
    with pytest.raises(ValueError, match="Shape mismatch"):
        load_efficiency(acc, tot)


def test_load_efficiency_edge_mismatch() -> None:
    acc = bh.Histogram(bh.axis.Regular(5, 0, 1), storage=bh.storage.Double())
    tot = bh.Histogram(bh.axis.Regular(5, 0, 2), storage=bh.storage.Double())
    with pytest.raises(ValueError, match="Bin edges"):
        load_efficiency(acc, tot)
