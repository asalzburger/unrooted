from pathlib import Path

import numpy as np
import pytest

from unrooted.io.root.reader import load, load_efficiency

DATA_DIR = Path(__file__).parent.parent / "data" / "root"


def test_load_th1d_ndim():
    hist = load(DATA_DIR / "tests_input.root", "hx")
    assert hist.ndim == 1


def test_load_th1d_shape():
    hist = load(DATA_DIR / "tests_input.root", "hx")
    n = hist.values.shape[0]
    assert len(hist.axes[0].edges) == n + 1
    assert hist.variances.shape == hist.values.shape


def test_load_th1d_name():
    hist = load(DATA_DIR / "tests_input.root", "hx")
    assert hist.name == "hx"


def test_load_th1d_overflow():
    hist = load(DATA_DIR / "tests_input.root", "hx")
    assert hist.overflow is not None
    assert hist.overflow.shape[0] == hist.values.shape[0] + 2


def test_load_th2d_ndim():
    hist = load(DATA_DIR / "tests_input.root", "hxy")
    assert hist.ndim == 2


def test_load_th2d_shape():
    hist = load(DATA_DIR / "tests_input.root", "hxy")
    nx, ny = hist.values.shape
    assert len(hist.axes[0].edges) == nx + 1
    assert len(hist.axes[1].edges) == ny + 1
    assert hist.variances.shape == hist.values.shape


def test_load_tprofile_ndim():
    hist = load(DATA_DIR / "tests_input.root", "profX")
    assert hist.ndim == 1


def test_load_tprofile_shape():
    hist = load(DATA_DIR / "tests_input.root", "profX")
    n = hist.values.shape[0]
    assert len(hist.axes[0].edges) == n + 1


def test_load_tprofile_variances_shape():
    hist = load(DATA_DIR / "tests_input.root", "profX")
    assert hist.variances.shape == hist.values.shape


def test_load_tprofile_spread_present():
    hist = load(DATA_DIR / "tests_input.root", "profX")
    assert hist.spread_min is not None
    assert hist.spread_max is not None


def test_load_tprofile_spread_shape():
    hist = load(DATA_DIR / "tests_input.root", "profX")
    assert hist.spread_min is not None
    assert hist.spread_max is not None
    assert hist.spread_min.shape == hist.values.shape
    assert hist.spread_max.shape == hist.values.shape


def test_load_tprofile_spread_ordering():
    """Non-empty bins must satisfy spread_min <= values <= spread_max."""
    hist = load(DATA_DIR / "tests_input.root", "profX")
    assert hist.spread_min is not None
    assert hist.spread_max is not None
    # Only check bins where data is present (non-nan spread)
    mask = ~np.isnan(hist.spread_min)
    assert np.all(hist.spread_min[mask] <= hist.values[mask] + 1e-12)
    assert np.all(hist.spread_max[mask] >= hist.values[mask] - 1e-12)


def test_load_tprofile_empty_bins_are_nan():
    """Bins with no entries should have nan spread, not 0."""
    hist = load(DATA_DIR / "tests_input.root", "profX")
    assert hist.spread_min is not None
    # At least some bins should be nan (sparse profiles are common)
    # values==0 and variances==0 together indicates an empty bin
    empty = (hist.values == 0.0) & (hist.variances == 0.0)
    if empty.any():
        assert np.all(np.isnan(hist.spread_min[empty]))


def test_load_tprofile_no_spread_for_th1():
    """Regular TH1 loads must not populate spread fields."""
    hist = load(DATA_DIR / "tests_input.root", "hx")
    assert hist.spread_min is None
    assert hist.spread_max is None


# ---------------------------------------------------------------------------
# load_efficiency
# ---------------------------------------------------------------------------

_EFF_FILE = DATA_DIR / "tests_efficiency.root"


def test_load_efficiency_ndim():
    hist = load_efficiency(_EFF_FILE, "h_passed", "h_total")
    assert hist.ndim == 1


def test_load_efficiency_values_range():
    hist = load_efficiency(_EFF_FILE, "h_passed", "h_total")
    valid = ~np.isnan(hist.values)
    assert np.all(hist.values[valid] >= 0.0)
    assert np.all(hist.values[valid] <= 1.0)


def test_load_efficiency_shape():
    hist = load_efficiency(_EFF_FILE, "h_passed", "h_total")
    n = hist.values.shape[0]
    assert len(hist.axes[0].edges) == n + 1
    assert hist.variances.shape == hist.values.shape


def test_load_efficiency_spread_present():
    hist = load_efficiency(_EFF_FILE, "h_passed", "h_total")
    assert hist.spread_min is not None
    assert hist.spread_max is not None


def test_load_efficiency_spread_clamped():
    hist = load_efficiency(_EFF_FILE, "h_passed", "h_total")
    assert hist.spread_min is not None
    assert hist.spread_max is not None
    valid = ~np.isnan(hist.spread_min)
    assert np.all(hist.spread_min[valid] >= 0.0)
    assert np.all(hist.spread_max[valid] <= 1.0)


def test_load_efficiency_spread_ordering():
    hist = load_efficiency(_EFF_FILE, "h_passed", "h_total")
    assert hist.spread_min is not None
    assert hist.spread_max is not None
    valid = ~np.isnan(hist.spread_min)
    assert np.all(hist.spread_min[valid] <= hist.values[valid] + 1e-12)
    assert np.all(hist.spread_max[valid] >= hist.values[valid] - 1e-12)


def test_load_efficiency_known_values():
    """Verify exact efficiency for the synthetic test file (passed/20 per bin)."""
    hist = load_efficiency(_EFF_FILE, "h_passed", "h_total")
    # All bins have total=20; efficiency = passed/20
    assert np.all(~np.isnan(hist.values)), "no bins should be empty"
    assert np.allclose(hist.values * 20.0, np.round(hist.values * 20.0), atol=1e-9)


def test_load_efficiency_shape_mismatch_files():
    """Mismatched bin counts raise ValueError."""
    import tempfile

    import numpy as np
    import uproot
    edges_a = np.linspace(0, 1, 11)   # 10 bins
    edges_b = np.linspace(0, 1, 6)    # 5 bins
    with tempfile.NamedTemporaryFile(suffix=".root", delete=False) as tmp:
        tmp_path = tmp.name
    with uproot.recreate(tmp_path) as f:
        f["ha"] = (np.ones(10), edges_a)
        f["hb"] = (np.ones(5),  edges_b)
    with pytest.raises(ValueError, match="Shape mismatch"):
        load_efficiency(tmp_path, "ha", "hb")
