from __future__ import annotations

import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

from unrooted.core.scatter import ScatterData  # noqa: E402
from unrooted.plot.mpl.scatter import plot  # noqa: E402
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


def test_returns_axes():
    from matplotlib.axes import Axes

    sd = _make_scatter()
    ax = plot(sd)
    assert isinstance(ax, Axes)


def test_default_style_is_scatter():
    sd = _make_scatter()
    ax = plot(sd)
    line = ax.lines[0]
    assert line.get_marker() == "."
    assert line.get_linestyle() == "None"


def test_axis_labels_set():
    sd = _make_scatter()
    ax = plot(sd)
    assert ax.get_xlabel() == "x axis"
    assert ax.get_ylabel() == "y axis"


def test_axis_labels_skipped():
    sd = _make_scatter()
    ax = plot(sd, set_axis_labels=False)
    assert ax.get_xlabel() == ""
    assert ax.get_ylabel() == ""


def test_custom_style_respected():
    sd = _make_scatter()
    style = HistogramStyle.as_scatter(marker="o", marker_size=5.0)
    ax = plot(sd, style=style)
    line = ax.lines[0]
    assert line.get_marker() == "o"
    assert line.get_markersize() == pytest.approx(5.0)


def test_color_applied():
    sd = _make_scatter()
    style = HistogramStyle.as_scatter().with_color("#ff0000")
    ax = plot(sd, style=style)
    # Color is applied; line color should not be default blue
    color = ax.lines[0].get_color()
    assert color == "#ff0000"


def test_label_appears():
    sd = _make_scatter()
    ax = plot(sd, label="dataset A")
    handles, texts = ax.get_legend_handles_labels()
    assert "dataset A" in texts


def test_overlay_two_scatters():
    import matplotlib.pyplot as plt

    sd1 = _make_scatter(30)
    sd2 = ScatterData(
        x=np.linspace(0, 1, 30),
        y=np.linspace(0, 1, 30),
        x_label="x",
        y_label="y",
    )
    _, ax = plt.subplots()
    plot(sd1, ax=ax, label="A", set_axis_labels=False)
    plot(sd2, ax=ax, label="B", set_axis_labels=False)
    assert len(ax.lines) == 2


def test_existing_ax_reused():
    import matplotlib.pyplot as plt

    _, ax = plt.subplots()
    sd = _make_scatter()
    returned = plot(sd, ax=ax)
    assert returned is ax
