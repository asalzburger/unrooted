from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram
from unrooted.plot.style import HistogramStyle

plotly = pytest.importorskip("plotly")
go = pytest.importorskip("plotly.graph_objects")

from unrooted.plot.plotly.overlay import overlay  # noqa: E402

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


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------


def test_overlay_returns_figure():
    h = _hist([1.0, 2.0])
    fig = overlay([h])
    assert isinstance(fig, go.Figure)


def test_overlay_multiple_returns_figure():
    h1 = _hist([1.0, 2.0])
    h2 = _hist([3.0, 4.0])
    fig = overlay([h1, h2])
    assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# Ratio panel
# ---------------------------------------------------------------------------


def test_overlay_ratio_creates_subplots():
    h1 = _hist([1.0, 2.0])
    h2 = _hist([2.0, 4.0])
    fig = overlay([h1, h2], ratio=True)
    # make_subplots creates a second y-axis; verify via layout dict
    layout = fig.to_dict()["layout"]
    assert "yaxis2" in layout


def test_overlay_ratio_yaxis2_title():
    h1 = _hist([1.0, 2.0])
    h2 = _hist([2.0, 4.0])
    fig = overlay([h1, h2], ratio=True)
    assert fig.layout.yaxis2.title.text == "Ratio"


def test_overlay_ratio_values_correct():
    h1 = _hist([2.0, 4.0], variances=[2.0, 4.0])
    h2 = _hist([4.0, 8.0], variances=[4.0, 8.0])
    fig = overlay([h1, h2], ratio=True)
    # The first ratio trace is the step line for h2/h1.
    # Values should be 2.0 everywhere (within the step array).
    ratio_traces = [t for t in fig.data if t.yaxis == "y2"]
    step_trace = ratio_traces[0]
    finite = step_trace.y[~np.isnan(step_trace.y)]
    np.testing.assert_allclose(finite, 2.0)


def test_overlay_ratio_zero_denominator_is_nan():
    h1 = _hist([0.0, 4.0], variances=[0.0, 4.0])
    h2 = _hist([1.0, 8.0], variances=[1.0, 8.0])
    fig = overlay([h1, h2], ratio=True)
    ratio_traces = [t for t in fig.data if t.yaxis == "y2"]
    step_trace = ratio_traces[0]
    # First bin denominator is 0 → nan
    assert np.isnan(step_trace.y[0])


# ---------------------------------------------------------------------------
# Labels / legend
# ---------------------------------------------------------------------------


def test_overlay_labels_set_on_traces():
    h1 = _hist([1.0, 2.0])
    h2 = _hist([3.0, 4.0])
    fig = overlay([h1, h2], labels=["alpha", "beta"])
    names = [t.name for t in fig.data if t.showlegend]
    assert "alpha" in names
    assert "beta" in names


def test_overlay_no_labels_no_legend():
    h1 = _hist([1.0, 2.0])
    h2 = _hist([3.0, 4.0])
    fig = overlay([h1, h2])
    # No trace should have showlegend=True when labels not supplied
    assert not any(t.showlegend for t in fig.data)


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------


def test_overlay_with_styles():
    h1 = _hist([1.0, 2.0])
    h2 = _hist([3.0, 4.0])
    s1 = HistogramStyle(line_color="#1A4F8A", error_display=None)
    s2 = HistogramStyle(line_color="#E8921A", error_display=None)
    fig = overlay([h1, h2], styles=[s1, s2])
    assert isinstance(fig, go.Figure)


def test_overlay_styles_auto_color_when_none():
    h1 = _hist([1.0, 2.0])
    h2 = _hist([3.0, 4.0])
    fig = overlay([h1, h2])
    # Both histograms should contribute traces
    assert len(fig.data) >= 2


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_overlay_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        overlay([])


def test_overlay_2d_raises():
    ax1 = Axis(edges=np.array([0.0, 1.0]))
    ax2 = Axis(edges=np.array([0.0, 1.0]))
    h2d = Histogram(
        axes=[ax1, ax2], values=np.zeros((1, 1)), variances=np.zeros((1, 1))
    )
    with pytest.raises(ValueError, match="1D"):
        overlay([h2d])


def test_overlay_labels_mismatch_raises():
    h1 = _hist([1.0])
    h2 = _hist([2.0])
    with pytest.raises(ValueError, match="labels"):
        overlay([h1, h2], labels=["only_one"])


def test_overlay_styles_mismatch_raises():
    h1 = _hist([1.0])
    h2 = _hist([2.0])
    with pytest.raises(ValueError, match="styles"):
        overlay([h1, h2], styles=[HistogramStyle()])


# ---------------------------------------------------------------------------
# Integration (ROOT data)
# ---------------------------------------------------------------------------


def test_overlay_root_hx_hy():
    pytest.importorskip("uproot")
    from unrooted.io.root.reader import load

    hx = load(DATA_DIR / "tests_input.root", "hx")
    hy = load(DATA_DIR / "tests_input.root", "hy")
    fig = overlay([hx, hy], labels=["hx", "hy"])
    assert isinstance(fig, go.Figure)


def test_overlay_root_ratio():
    pytest.importorskip("uproot")
    from unrooted.io.root.reader import load

    hx = load(DATA_DIR / "tests_input.root", "hx")
    hy = load(DATA_DIR / "tests_input.root", "hy")
    fig = overlay([hx, hy], ratio=True, labels=["hx", "hy"])
    layout = fig.to_dict()["layout"]
    assert "yaxis2" in layout
