"""Ratio styles and public scatter composition across graphical backends."""

import importlib

import matplotlib.pyplot as plt
import numpy as np
import pytest

from unrooted.core import Axis, Histogram, ScatterData
from unrooted.plot.style import HistogramStyle


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def backend_module(backend):
    if backend == "plotly":
        pytest.importorskip("plotly")
    return importlib.import_module(f"unrooted.plot.{backend}")


def hist(values):
    return Histogram([Axis([0, 1, 2])], np.array(values), np.array(values))


def scatter():
    return ScatterData(
        [0, 1], [2, 4], x_label="Position", y_label="Momentum", title="First dataset"
    )


@pytest.mark.parametrize("backend", ["mpl", "plotly"])
@pytest.mark.parametrize("mode", [None, "bar", "band", "continuous"])
def test_ratio_uses_numerator_line_and_error_style(backend, mode):
    module = backend_module(backend)
    style = HistogramStyle(
        line_color="#ff0000",
        line_style="--",
        line_width=3,
        line_alpha=0.7,
        error_display=mode,
        error_color="#008000",
        error_alpha=0.25,
        error_capsize=6,
    )
    result = module.overlay(
        [hist([2, 4]), hist([4, 8])], styles=[HistogramStyle(), style], ratio=True
    )
    if backend == "mpl":
        _, ax = result
        assert ax.patches[0].get_linestyle() == "--"
        assert ax.patches[0].get_linewidth() == 3
        assert ax.patches[0].get_alpha() == 0.7
        assert len(ax.collections) == (0 if mode is None else 1)
        if mode is not None:
            assert ax.collections[0].get_alpha() == 0.25
            getter = "get_colors" if mode == "bar" else "get_facecolors"
            np.testing.assert_allclose(
                getattr(ax.collections[0], getter)()[0], [0, 128 / 255, 0, 0.25]
            )
    else:
        traces = [trace for trace in result.data if trace.yaxis == "y2"]
        line = traces[0]
        assert line.line.dash == "dash"
        assert line.line.width == 3
        assert line.line.color == "rgba(255,0,0,0.7)"
        error_traces = [trace for trace in traces if trace.error_y.array is not None]
        bands = [trace for trace in traces if trace.fill == "tonexty"]
        assert len(error_traces) == (1 if mode == "bar" else 0)
        assert len(bands) == (1 if mode in ("band", "continuous") else 0)
        if mode == "bar":
            assert error_traces[0].error_y.width == 6
            assert error_traces[0].error_y.color == "rgba(0,128,0,0.25)"
        if bands:
            assert bands[0].fillcolor == "rgba(0,128,0,0.25)"
            assert len(bands[0].x) == (4 if mode == "band" else 2)


@pytest.mark.parametrize("backend", ["mpl", "plotly"])
def test_marker_only_ratio_has_markers_without_a_step_line(backend):
    module = backend_module(backend)
    style = HistogramStyle.as_markers(
        error_display=None, marker="s", marker_color="#ff0000", marker_size=7
    )
    result = module.overlay(
        [hist([2, 4]), hist([4, 8])], styles=[style, style], ratio=True
    )
    if backend == "mpl":
        _, ax = result
        assert not ax.patches
        marker = ax.lines[0]
        assert marker.get_marker() == "s"
        np.testing.assert_allclose(marker.get_ydata(), [2, 2])
    else:
        traces = [trace for trace in result.data if trace.yaxis == "y2"]
        assert len(traces) == 2  # marker trace and ratio=1 reference
        assert traces[0].mode == "markers"
        assert traces[0].marker.symbol == "square"
        np.testing.assert_allclose(traces[0].y, [2, 2])


@pytest.mark.parametrize("backend", ["mpl", "plotly"])
def test_public_scatter_overlay_labels_styles_and_automatic_colors(backend):
    module = backend_module(backend)
    result = module.overlay_scatter([scatter(), scatter()], labels=["A", "B"])
    if backend == "mpl":
        assert result.get_xlabel() == "Position"
        assert result.get_ylabel() == "Momentum"
        assert result.get_title() == "First dataset"
        assert [text.get_text() for text in result.get_legend().texts] == ["A", "B"]
        assert result.lines[0].get_color() != result.lines[1].get_color()
    else:
        assert result.layout.xaxis.title.text == "Position"
        assert result.layout.yaxis.title.text == "Momentum"
        assert result.layout.title.text == "First dataset"
        assert [trace.name for trace in result.data] == ["A", "B"]
        assert result.data[0].marker.color != result.data[1].marker.color


@pytest.mark.parametrize("backend", ["mpl", "plotly"])
@pytest.mark.parametrize(
    "kwargs", [{"labels": ["one"]}, {"styles": [HistogramStyle()]}]
)
def test_public_scatter_overlay_rejects_mismatched_options(backend, kwargs):
    with pytest.raises(ValueError, match="same length"):
        backend_module(backend).overlay_scatter([scatter(), scatter()], **kwargs)


@pytest.mark.parametrize("backend", ["mpl", "plotly"])
def test_public_scatter_overlay_validates_before_drawing(backend):
    module = backend_module(backend)
    with pytest.raises(ValueError, match="empty"):
        module.overlay_scatter([])
    invalid = scatter()
    invalid.y = np.array([np.inf, 1])
    with pytest.raises(ValueError, match="finite"):
        module.overlay_scatter([scatter(), invalid])
    assert not plt.get_fignums()


def test_public_scatter_exports():
    from unrooted import ScatterData as TopLevelScatter
    from unrooted.io.root import load_scatter

    assert TopLevelScatter is ScatterData
    assert callable(load_scatter)


def test_matplotlib_scatter_composes_on_existing_axes():
    module = backend_module("mpl")
    _, ax = plt.subplots()
    assert module.overlay_scatter([scatter(), scatter()], ax=ax) is ax
    assert len(ax.lines) == 2
    assert len(plt.get_fignums()) == 1


def test_plotly_scatter_composes_in_existing_subplots_using_public_api():
    module = backend_module("plotly")
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=1, cols=2)
    result = module.plot_scatter(scatter(), fig=fig, row=1, col=2, label="A")
    assert result is fig
    assert fig.data[0].xaxis == "x2"
    assert fig.layout.xaxis2.title.text == "Position"
    assert not fig.layout.xaxis.title.text
    module.plot_scatter(scatter(), fig=fig, row=1, col=1, set_axis_labels=False)
    assert not fig.layout.xaxis.title.text


@pytest.mark.parametrize("kwargs", [{"row": 1}, {"col": 1}, {"row": 1, "col": 1}])
def test_plotly_scatter_requires_both_subplot_coordinates_and_a_figure(kwargs):
    with pytest.raises(ValueError, match="row and col"):
        backend_module("plotly").plot_scatter(scatter(), **kwargs)


def test_plotly_single_histogram_accepts_public_label_override():
    fig = backend_module("plotly").plot(hist([2, 4]), label="Dataset")
    assert [trace.name for trace in fig.data if trace.showlegend] == ["Dataset"]


@pytest.mark.parametrize("backend", ["mpl", "plotly"])
def test_disabled_ratio_errors_do_not_compute_unrepresentable_uncertainties(backend):
    reference = Histogram([Axis([0, 1])], [1e-200], [1])
    numerator = Histogram([Axis([0, 1])], [2e-200], [1])
    style = HistogramStyle.as_line()
    with np.errstate(all="raise"):
        result = backend_module(backend).overlay(
            [reference, numerator],
            styles=[style, style],
            ratio=True,
        )
    if backend == "mpl":
        _, ax = result
        np.testing.assert_allclose(ax.patches[0].get_data().values, [2])
    else:
        trace = [t for t in result.data if t.yaxis == "y2"][0]
        np.testing.assert_allclose(trace.y, [2, 2])
