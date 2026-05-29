from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest
from matplotlib.axes import Axes as MplAxes
from matplotlib.collections import PolyCollection

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram
from unrooted.plot.mpl._range import _draw_range
from unrooted.plot.mpl.histogram import plot
from unrooted.plot.mpl.overlay import overlay
from unrooted.plot.style import HistogramStyle, LineStyle

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


def _fresh_ax() -> MplAxes:
    import matplotlib.pyplot as plt

    _, ax = plt.subplots()
    return ax


# ---------------------------------------------------------------------------
# HistogramStyle defaults
# ---------------------------------------------------------------------------


def test_style_defaults():
    s = HistogramStyle()
    assert s.line_color is None
    assert s.line_style == "-"
    assert s.line_width == 1.5
    assert s.marker is None
    assert s.fill_alpha is None
    assert s.error_display == "bar"
    assert s.spread_display is None


# ---------------------------------------------------------------------------
# _draw_range
# ---------------------------------------------------------------------------


def test_draw_range_bar_adds_errorbar_container():
    ax = _fresh_ax()
    centers = np.array([0.5, 1.5, 2.5])
    values = np.array([3.0, 5.0, 4.0])
    lo = values - 1.0
    hi = values + 1.0
    edges = np.array([0.0, 1.0, 2.0, 3.0])
    _draw_range(ax, centers, values, lo, hi, edges, "bar", "blue", 1.0, capsize=2)
    assert len(ax.containers) == 1


def test_draw_range_band_adds_poly_collection():
    ax = _fresh_ax()
    centers = np.array([0.5, 1.5])
    values = np.array([2.0, 3.0])
    lo = values - 0.5
    hi = values + 0.5
    edges = np.array([0.0, 1.0, 2.0])
    _draw_range(ax, centers, values, lo, hi, edges, "band", "red", 0.3)
    poly_collections = [c for c in ax.collections if isinstance(c, PolyCollection)]
    assert len(poly_collections) == 1


def test_draw_range_continuous_adds_poly_collection():
    ax = _fresh_ax()
    centers = np.array([0.5, 1.5])
    values = np.array([2.0, 3.0])
    lo = values - 0.5
    hi = values + 0.5
    edges = np.array([0.0, 1.0, 2.0])
    _draw_range(ax, centers, values, lo, hi, edges, "continuous", "green", 0.3)
    poly_collections = [c for c in ax.collections if isinstance(c, PolyCollection)]
    assert len(poly_collections) == 1


def test_draw_range_continuous_uses_centers_not_edges():
    """The x-coordinates of the continuous band must match bin centres, not edges."""
    ax = _fresh_ax()
    centers = np.array([0.5, 1.5, 2.5])
    values = np.array([1.0, 2.0, 3.0])
    lo = values - 0.3
    hi = values + 0.3
    edges = np.array([0.0, 1.0, 2.0, 3.0])
    _draw_range(ax, centers, values, lo, hi, edges, "continuous", "blue", 0.2)
    poly = [c for c in ax.collections if isinstance(c, PolyCollection)][0]
    # fill_between with 3 centers produces a single polygon path with 3 unique x coords
    x_coords = np.unique(np.concatenate([path.vertices[:, 0] for path in poly.get_paths()]))
    assert len(x_coords) == len(centers)


def test_draw_range_bar_midpoints_correct():
    ax = _fresh_ax()
    centers = np.array([0.5, 1.5])
    values = np.array([4.0, 9.0])
    lo = values - 1.0
    hi = values + 1.0
    edges = np.array([0.0, 1.0, 2.0])
    _draw_range(ax, centers, values, lo, hi, edges, "bar", "black", 1.0)
    container = ax.containers[0]
    segments = container.lines[2][0].get_segments()  # type: ignore[union-attr]
    y_mids = np.array([(s[0][1] + s[1][1]) / 2 for s in segments])
    np.testing.assert_allclose(y_mids, values)


# ---------------------------------------------------------------------------
# plot() with style
# ---------------------------------------------------------------------------


def test_plot_styled_default_has_errorbar():
    h = _hist([4.0, 9.0])
    ax = _fresh_ax()
    plot(h, ax=ax, style=HistogramStyle())
    assert len(ax.containers) == 1  # error bars


def test_plot_styled_line_only_no_errorbar():
    h = _hist([4.0, 9.0])
    ax = _fresh_ax()
    plot(h, ax=ax, style=HistogramStyle(error_display=None))
    assert len(ax.containers) == 0


def test_plot_styled_error_band_adds_poly():
    h = _hist([4.0, 9.0])
    ax = _fresh_ax()
    plot(h, ax=ax, style=HistogramStyle(error_display="band"))
    poly = [c for c in ax.collections if isinstance(c, PolyCollection)]
    assert len(poly) == 1


def test_plot_styled_fill_adds_patch():
    h = _hist([1.0, 2.0, 3.0])
    ax = _fresh_ax()
    plot(h, ax=ax, style=HistogramStyle(fill_alpha=0.3, error_display=None))
    # ax.stairs(fill=True) adds a StepPatch; at least one patch beyond the axes border
    assert len(ax.patches) >= 1


def test_plot_styled_marker_adds_line():
    h = _hist([1.0, 2.0])
    ax = _fresh_ax()
    n_lines_before = len(ax.lines)
    plot(
        h, ax=ax, style=HistogramStyle(marker="o", line_style=None, error_display=None)
    )
    assert len(ax.lines) > n_lines_before


def test_plot_styled_spread_bar():
    h = _hist([4.0, 9.0])
    h.spread_min = np.array([2.0, 5.0])
    h.spread_max = np.array([6.0, 13.0])
    ax = _fresh_ax()
    plot(
        h,
        ax=ax,
        style=HistogramStyle(error_display=None, spread_display="bar"),
    )
    assert len(ax.containers) == 1


def test_plot_styled_spread_band():
    h = _hist([4.0, 9.0])
    h.spread_min = np.array([2.0, 5.0])
    h.spread_max = np.array([6.0, 13.0])
    ax = _fresh_ax()
    plot(
        h,
        ax=ax,
        style=HistogramStyle(error_display=None, spread_display="band"),
    )
    poly = [c for c in ax.collections if isinstance(c, PolyCollection)]
    assert len(poly) == 1


def test_plot_styled_spread_continuous():
    h = _hist([4.0, 9.0])
    h.spread_min = np.array([2.0, 5.0])
    h.spread_max = np.array([6.0, 13.0])
    ax = _fresh_ax()
    plot(
        h,
        ax=ax,
        style=HistogramStyle(error_display=None, spread_display="continuous"),
    )
    poly = [c for c in ax.collections if isinstance(c, PolyCollection)]
    assert len(poly) == 1


def test_plot_styled_error_continuous():
    h = _hist([4.0, 9.0])
    ax = _fresh_ax()
    plot(h, ax=ax, style=HistogramStyle(error_display="continuous"))
    poly = [c for c in ax.collections if isinstance(c, PolyCollection)]
    assert len(poly) == 1


def test_plot_styled_spread_missing_raises():
    h = _hist([4.0, 9.0])  # no spread_min / spread_max
    ax = _fresh_ax()
    with pytest.raises(ValueError, match="spread_min/spread_max"):
        plot(h, ax=ax, style=HistogramStyle(spread_display="bar"))


def test_plot_styled_combined():
    """Line + fill + markers + error band + spread band all together."""
    h = _hist([4.0, 9.0, 16.0])
    h.spread_min = np.array([2.0, 5.0, 10.0])
    h.spread_max = np.array([6.0, 14.0, 22.0])
    ax = _fresh_ax()
    plot(
        h,
        ax=ax,
        style=HistogramStyle(
            fill_alpha=0.2,
            marker="s",
            error_display="band",
            spread_display="band",
        ),
    )
    poly = [c for c in ax.collections if isinstance(c, PolyCollection)]
    assert len(poly) == 2  # error band + spread band


# ---------------------------------------------------------------------------
# overlay() with styles
# ---------------------------------------------------------------------------


def test_overlay_with_styles():
    h1 = _hist([1.0, 2.0])
    h2 = _hist([3.0, 4.0])
    s1 = HistogramStyle(line_color="red")
    s2 = HistogramStyle(line_color="blue", error_display=None)
    main_ax, ratio_ax = overlay([h1, h2], styles=[s1, s2])
    assert isinstance(main_ax, MplAxes)
    assert ratio_ax is None


def test_overlay_styles_length_mismatch_raises():
    h1 = _hist([1.0])
    h2 = _hist([2.0])
    with pytest.raises(ValueError, match="styles"):
        overlay([h1, h2], styles=[HistogramStyle()])


def test_overlay_with_styles_and_ratio():
    h1 = _hist([2.0, 4.0])
    h2 = _hist([4.0, 8.0])
    s1 = HistogramStyle(line_color="C0")
    s2 = HistogramStyle(line_color="C1", error_display="band")
    main_ax, ratio_ax = overlay([h1, h2], ratio=True, styles=[s1, s2])
    assert isinstance(main_ax, MplAxes)
    assert isinstance(ratio_ax, MplAxes)


def test_overlay_no_styles_uses_cycle():
    h1 = _hist([1.0, 2.0])
    h2 = _hist([3.0, 4.0])
    main_ax, _ = overlay([h1, h2])
    assert isinstance(main_ax, MplAxes)


# ---------------------------------------------------------------------------
# Integration tests (ROOT data)
# ---------------------------------------------------------------------------


def test_styled_plot_root_hx():
    pytest.importorskip("uproot")
    from unrooted.io.root.reader import load

    h = load(DATA_DIR / "tests_input.root", "hx")
    ax = _fresh_ax()
    plot(
        h,
        ax=ax,
        style=HistogramStyle(
            fill_alpha=0.15,
            error_display="band",
        ),
    )
    assert isinstance(ax, MplAxes)


def test_overlay_root_hx_hy_with_styles():
    pytest.importorskip("uproot")
    from unrooted.io.root.reader import load

    hx = load(DATA_DIR / "tests_input.root", "hx")
    hy = load(DATA_DIR / "tests_input.root", "hy")
    sx = HistogramStyle(line_color="C0", error_display="bar")
    sy = HistogramStyle(line_color="C1", error_display="band", error_alpha=0.3)
    main_ax, _ = overlay([hx, hy], styles=[sx, sy], labels=["hx", "hy"])
    assert isinstance(main_ax, MplAxes)


# ---------------------------------------------------------------------------
# LineStyle constants
# ---------------------------------------------------------------------------


def test_linestyle_solid():
    assert LineStyle.SOLID == "-"


def test_linestyle_dashed():
    assert LineStyle.DASHED == "--"


def test_linestyle_dotted():
    assert LineStyle.DOTTED == ":"


def test_linestyle_dashdot():
    assert LineStyle.DASHDOT == "-."


# ---------------------------------------------------------------------------
# Named constructors — structural properties
# ---------------------------------------------------------------------------


def test_as_hist_has_fill():
    s = HistogramStyle.as_hist()
    assert s.fill_alpha is not None and s.fill_alpha > 0


def test_as_hist_has_errors():
    assert HistogramStyle.as_hist().error_display == "bar"


def test_as_hist_no_spread():
    assert HistogramStyle.as_hist().spread_display is None


def test_as_hist_override():
    s = HistogramStyle.as_hist(line_color="red", fill_alpha=0.5)
    assert s.line_color == "red"
    assert s.fill_alpha == 0.5
    assert s.error_display == "bar"


def test_as_line_no_fill():
    assert HistogramStyle.as_line().fill_alpha is None


def test_as_line_no_marker():
    assert HistogramStyle.as_line().marker is None


def test_as_line_no_errors():
    assert HistogramStyle.as_line().error_display is None


def test_as_line_no_spread():
    assert HistogramStyle.as_line().spread_display is None


def test_as_line_has_step():
    assert HistogramStyle.as_line().line_style is not None


def test_as_line_dashed_override():
    s = HistogramStyle.as_line(line_style=LineStyle.DASHED, line_width=2.0)
    assert s.line_style == "--"
    assert s.line_width == 2.0


def test_as_markers_has_marker():
    assert HistogramStyle.as_markers().marker is not None


def test_as_markers_no_line():
    assert HistogramStyle.as_markers().line_style is None


def test_as_markers_has_errors():
    assert HistogramStyle.as_markers().error_display == "bar"


def test_as_markers_no_fill():
    assert HistogramStyle.as_markers().fill_alpha is None


def test_as_markers_custom_marker():
    assert HistogramStyle.as_markers(marker="s").marker == "s"


def test_as_efficiency_has_marker():
    assert HistogramStyle.as_efficiency().marker is not None


def test_as_efficiency_has_spread():
    assert HistogramStyle.as_efficiency().spread_display is not None


def test_as_efficiency_has_errors():
    assert HistogramStyle.as_efficiency().error_display is not None


def test_as_efficiency_no_line():
    assert HistogramStyle.as_efficiency().line_style is None


def test_as_efficiency_no_fill():
    assert HistogramStyle.as_efficiency().fill_alpha is None


def test_as_profile_has_line():
    assert HistogramStyle.as_profile().line_style is not None


def test_as_profile_has_spread():
    assert HistogramStyle.as_profile().spread_display is not None


def test_as_profile_no_fill():
    assert HistogramStyle.as_profile().fill_alpha is None


def test_as_profile_no_marker():
    assert HistogramStyle.as_profile().marker is None


# ---------------------------------------------------------------------------
# with_color
# ---------------------------------------------------------------------------


def test_with_color_fills_none_fields():
    s = HistogramStyle.as_line().with_color("#3A6FA8")
    color_fields = (
        "line_color", "marker_color", "fill_color", "error_color", "spread_color"
    )
    for field in color_fields:
        assert getattr(s, field) == "#3A6FA8"


def test_with_color_preserves_explicit():
    s = HistogramStyle(line_color="red").with_color("#3A6FA8")
    assert s.line_color == "red"
    assert s.marker_color == "#3A6FA8"


def test_with_color_override_explicit():
    s = HistogramStyle(line_color="red").with_color("#3A6FA8", override_explicit=True)
    assert s.line_color == "#3A6FA8"


def test_with_color_returns_new_instance():
    original = HistogramStyle.as_line()
    assert original.with_color("blue") is not original


def test_with_color_does_not_mutate():
    original = HistogramStyle.as_line()
    original.with_color("blue")
    assert original.line_color is None


def test_with_color_accepts_tuple():
    s = HistogramStyle.as_line().with_color((0.2, 0.4, 0.8, 1.0))
    assert s.line_color == (0.2, 0.4, 0.8, 1.0)


def test_with_color_chaining_preserves_other_fields():
    s = HistogramStyle.as_hist(line_width=2.0).with_color("#E8721A")
    assert s.line_color == "#E8721A"
    assert s.line_width == 2.0
    assert s.fill_alpha is not None


# ---------------------------------------------------------------------------
# Named constructors render without error
# ---------------------------------------------------------------------------


def test_as_hist_renders():
    h = _hist([4.0, 9.0])
    plot(h, ax=_fresh_ax(), style=HistogramStyle.as_hist())


def test_as_line_renders():
    h = _hist([4.0, 9.0])
    plot(h, ax=_fresh_ax(), style=HistogramStyle.as_line())


def test_as_markers_renders():
    h = _hist([4.0, 9.0])
    plot(h, ax=_fresh_ax(), style=HistogramStyle.as_markers())


def test_as_efficiency_renders():
    h = _hist([4.0, 9.0])
    h.spread_min = np.array([2.0, 5.0])
    h.spread_max = np.array([6.0, 13.0])
    plot(h, ax=_fresh_ax(), style=HistogramStyle.as_efficiency())


def test_as_profile_renders():
    h = _hist([4.0, 9.0])
    h.spread_min = np.array([2.0, 5.0])
    h.spread_max = np.array([6.0, 13.0])
    plot(h, ax=_fresh_ax(), style=HistogramStyle.as_profile())
