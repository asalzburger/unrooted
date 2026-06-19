from __future__ import annotations

import numpy as np
import pytest

from unrooted.core.scatter import ScatterData

plotly = pytest.importorskip("plotly")  # noqa: F841
go = pytest.importorskip("plotly.graph_objects")  # noqa: F841

from unrooted.plot.plotly.scatter import _add_scatter_trace, plot  # noqa: E402
from unrooted.plot.style import HistogramStyle  # noqa: E402


def _make_scatter(n: int = 50) -> ScatterData:
    rng = np.random.default_rng(42)
    return ScatterData(
        x=rng.standard_normal(n),
        y=rng.standard_normal(n),
        name="y",
        x_label="x axis",
        y_label="y axis",
    )


def test_returns_figure():
    sd = _make_scatter()
    fig = plot(sd)
    assert isinstance(fig, go.Figure)


def test_default_style_single_trace():
    sd = _make_scatter()
    fig = plot(sd)
    assert len(fig.data) == 1  # type: ignore[arg-type]


def test_default_mode_is_markers():
    sd = _make_scatter()
    fig = plot(sd)
    assert fig.data[0].mode == "markers"  # type: ignore[union-attr]


def test_axis_labels_set():
    sd = _make_scatter()
    fig = plot(sd)
    assert fig.layout.xaxis.title.text == "x axis"
    assert fig.layout.yaxis.title.text == "y axis"


def test_title_set():
    sd = ScatterData(x=np.array([1.0]), y=np.array([2.0]), title="My Scatter")
    fig = plot(sd)
    assert fig.layout.title.text == "My Scatter"


def test_custom_marker_size():
    sd = _make_scatter()
    style = HistogramStyle.as_scatter(marker_size=8.0)
    fig = plot(sd, style=style)
    assert fig.data[0].marker.size == pytest.approx(8.0)  # type: ignore[union-attr]


def test_circle_symbol_for_dot_marker():
    # Default as_scatter() uses marker="." which maps to "circle" in plotly.
    sd = _make_scatter()
    fig = plot(sd)
    assert fig.data[0].marker.symbol == "circle"  # type: ignore[union-attr]


def test_custom_marker_symbol():
    sd = _make_scatter()
    style = HistogramStyle.as_scatter(marker="o")
    fig = plot(sd, style=style)
    assert fig.data[0].marker.symbol == "circle"  # type: ignore[union-attr]


def test_square_marker_symbol():
    sd = _make_scatter()
    style = HistogramStyle.as_scatter(marker="s")
    fig = plot(sd, style=style)
    assert fig.data[0].marker.symbol == "square"  # type: ignore[union-attr]


def test_color_applied():
    sd = _make_scatter()
    style = HistogramStyle.as_scatter().with_color("#ff0000")
    fig = plot(sd, style=style)
    assert fig.data[0].marker.color == "#ff0000"  # type: ignore[union-attr]


def test_label_appears():
    sd = _make_scatter()
    fig = plot(sd, label="dataset A")
    assert fig.data[0].name == "dataset A"  # type: ignore[union-attr]
    assert fig.data[0].showlegend is True  # type: ignore[union-attr]


def test_no_label_hides_legend():
    sd = _make_scatter()
    fig = plot(sd)
    assert fig.data[0].showlegend is False  # type: ignore[union-attr]


def test_overlay_two_scatters():
    import plotly.graph_objects as go

    from unrooted.plot.plotly.histogram import DEFAULT_COLORS

    sd1 = _make_scatter(30)
    sd2 = ScatterData(
        x=np.linspace(0, 1, 30),
        y=np.linspace(0, 1, 30),
        x_label="x",
        y_label="y",
    )
    fig = go.Figure()
    style = HistogramStyle.as_scatter()
    _add_scatter_trace(fig, sd1, style, DEFAULT_COLORS[0], label="A")
    _add_scatter_trace(fig, sd2, style, DEFAULT_COLORS[1], label="B")
    assert len(fig.data) == 2  # type: ignore[arg-type]
    assert fig.data[0].name == "A"  # type: ignore[union-attr]
    assert fig.data[1].name == "B"  # type: ignore[union-attr]
