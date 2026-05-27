from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram
from unrooted.plot.style import HistogramStyle

plotly = pytest.importorskip("plotly")  # noqa: F841
go = pytest.importorskip("plotly.graph_objects")  # noqa: F841

from unrooted.plot.plotly.histogram import _staircase, plot  # noqa: E402

DATA_DIR = Path(__file__).parent.parent / "data" / "root"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hist(values: list[float], variances: list[float] | None = None) -> Histogram:
    n = len(values)
    axis = Axis(edges=np.arange(n + 1, dtype=float))
    v = np.array(values, dtype=float)
    var = np.array(variances, dtype=float) if variances is not None else v.copy()
    return Histogram(axes=[axis], values=v, variances=var)


def _hist2d(nx: int = 3, ny: int = 4) -> Histogram:
    ax = Axis(edges=np.arange(nx + 1, dtype=float), label="x")
    ay = Axis(edges=np.arange(ny + 1, dtype=float), label="y")
    values = np.ones((nx, ny))
    return Histogram(axes=[ax, ay], values=values, variances=values.copy())


# ---------------------------------------------------------------------------
# _staircase
# ---------------------------------------------------------------------------


def test_staircase_shape():
    edges = np.array([0.0, 1.0, 2.0, 3.0])
    values = np.array([1.0, 2.0, 3.0])
    x, y = _staircase(edges, values)
    assert len(x) == 2 * len(values)
    assert len(y) == 2 * len(values)


def test_staircase_values():
    edges = np.array([0.0, 1.0, 2.0])
    values = np.array([5.0, 7.0])
    x, y = _staircase(edges, values)
    np.testing.assert_array_equal(x, [0.0, 1.0, 1.0, 2.0])
    np.testing.assert_array_equal(y, [5.0, 5.0, 7.0, 7.0])


def test_staircase_nan_propagates():
    edges = np.array([0.0, 1.0, 2.0])
    values = np.array([np.nan, 3.0])
    _, y = _staircase(edges, values)
    assert np.isnan(y[0]) and np.isnan(y[1])
    assert y[2] == 3.0


# ---------------------------------------------------------------------------
# plot() — return type
# ---------------------------------------------------------------------------


def test_plot_1d_returns_figure():
    h = _hist([1.0, 2.0, 3.0])
    fig = plot(h)
    assert isinstance(fig, go.Figure)


def test_plot_2d_returns_figure():
    h = _hist2d()
    fig = plot(h)
    assert isinstance(fig, go.Figure)


def test_plot_unsupported_ndim_raises():
    ax = Axis(edges=np.array([0.0, 1.0]))
    h = Histogram(
        axes=[ax, ax, ax],
        values=np.ones((1, 1, 1)),
        variances=np.ones((1, 1, 1)),
    )
    with pytest.raises(ValueError, match="3D"):
        plot(h)


# ---------------------------------------------------------------------------
# plot() — 2D
# ---------------------------------------------------------------------------


def test_plot_2d_uses_heatmap():
    h = _hist2d()
    fig = plot(h)
    assert isinstance(fig.data[0], go.Heatmap)


def test_plot_2d_axis_labels():
    h = _hist2d()
    fig = plot(h)
    assert fig.layout.xaxis.title.text == "x"
    assert fig.layout.yaxis.title.text == "y"


# ---------------------------------------------------------------------------
# plot() — 1D trace counts
# ---------------------------------------------------------------------------
# Default style: 1 step line + 1 error-bar trace = 2 total.


def test_plot_1d_default_trace_count():
    h = _hist([1.0, 4.0])
    fig = plot(h, style=HistogramStyle())
    assert len(fig.data) == 2  # type: ignore[arg-type]


def test_plot_1d_no_error_display():
    h = _hist([1.0, 4.0])
    fig = plot(h, style=HistogramStyle(error_display=None))
    assert len(fig.data) == 1  # type: ignore[arg-type]  # step line only


def test_plot_1d_fill_adds_trace():
    # fill + line + error bar = 3 traces
    h = _hist([1.0, 4.0])
    fig = plot(h, style=HistogramStyle(fill_alpha=0.2, error_display=None))
    assert len(fig.data) == 2  # type: ignore[arg-type]  # fill trace + step line


def test_plot_1d_error_band_adds_two_traces():
    h = _hist([4.0, 9.0])
    fig = plot(h, style=HistogramStyle(error_display="band"))
    # step line + upper boundary + lower fill = 3
    assert len(fig.data) == 3  # type: ignore[arg-type]


def test_plot_1d_marker_adds_trace():
    h = _hist([1.0, 2.0])
    # line + marker (no error display)
    fig = plot(h, style=HistogramStyle(marker="o", error_display=None))
    assert len(fig.data) == 2  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# plot() — spread
# ---------------------------------------------------------------------------


def test_plot_1d_spread_bar():
    h = _hist([4.0, 9.0])
    h.spread_min = np.array([2.0, 5.0])
    h.spread_max = np.array([6.0, 13.0])
    fig = plot(h, style=HistogramStyle(error_display=None, spread_display="bar"))
    assert len(fig.data) == 2  # type: ignore[arg-type]  # step line + spread bar


def test_plot_1d_spread_band():
    h = _hist([4.0, 9.0])
    h.spread_min = np.array([2.0, 5.0])
    h.spread_max = np.array([6.0, 13.0])
    fig = plot(h, style=HistogramStyle(error_display=None, spread_display="band"))
    assert len(fig.data) == 3  # type: ignore[arg-type]  # step line + upper + lower fill


def test_plot_1d_spread_missing_raises():
    h = _hist([4.0, 9.0])
    with pytest.raises(ValueError, match="spread_min/spread_max"):
        plot(h, style=HistogramStyle(spread_display="bar"))


# ---------------------------------------------------------------------------
# plot() — axis labels and title
# ---------------------------------------------------------------------------


def test_plot_1d_axis_label():
    axis = Axis(edges=np.array([0.0, 1.0, 2.0]), label="momentum [GeV]")
    h = Histogram(
        axes=[axis],
        values=np.array([1.0, 2.0]),
        variances=np.array([1.0, 2.0]),
    )
    fig = plot(h)
    assert fig.layout.xaxis.title.text == "momentum [GeV]"


def test_plot_1d_title():
    h = _hist([1.0, 2.0])
    h.title = "My Histogram"
    fig = plot(h)
    assert fig.layout.title.text == "My Histogram"


# ---------------------------------------------------------------------------
# Integration (ROOT data)
# ---------------------------------------------------------------------------


def test_plot_root_hx():
    pytest.importorskip("uproot")
    from unrooted.io.root.reader import load

    h = load(DATA_DIR / "tests_input.root", "hx")
    fig = plot(h)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1  # type: ignore[arg-type]


def test_plot_root_hxy_2d():
    pytest.importorskip("uproot")
    from unrooted.io.root.reader import load

    h = load(DATA_DIR / "tests_input.root", "hxy")
    fig = plot(h)
    assert isinstance(fig.data[0], go.Heatmap)
