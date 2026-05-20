from pathlib import Path

from unrooted.io.root.reader import load

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
