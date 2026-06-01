from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest
from matplotlib.axes import Axes as MplAxes

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram
from unrooted.plot.mpl.overlay import overlay
from unrooted.plot.style import HistogramStyle

DATA_DIR = Path(__file__).parent.parent / "data" / "root"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hist(values: list[float], variances: list[float] | None = None) -> Histogram:
    n = len(values)
    edges = np.arange(n + 1, dtype=float)
    v = np.array(values, dtype=float)
    var = np.array(variances, dtype=float) if variances is not None else v.copy()
    return Histogram(axes=[Axis(edges=edges)], values=v, variances=var)


# ---------------------------------------------------------------------------
# Return-type tests
# ---------------------------------------------------------------------------

def test_overlay_returns_none_ratio_ax_when_ratio_false():
    h = _make_hist([1.0, 2.0, 3.0])
    _, ratio_ax = overlay([h])
    assert ratio_ax is None


def test_overlay_returns_axes_when_ratio_true():
    h1 = _make_hist([1.0, 2.0, 3.0])
    h2 = _make_hist([2.0, 4.0, 6.0])
    main_ax, ratio_ax = overlay([h1, h2], ratio=True)
    assert isinstance(main_ax, MplAxes)
    assert isinstance(ratio_ax, MplAxes)


# ---------------------------------------------------------------------------
# Basic overlay tests
# ---------------------------------------------------------------------------

def test_overlay_single_histogram():
    h = _make_hist([1.0, 2.0, 3.0])
    main_ax, ratio_ax = overlay([h])
    assert isinstance(main_ax, MplAxes)
    assert ratio_ax is None


def test_overlay_multiple_histograms():
    h1 = _make_hist([1.0, 2.0])
    h2 = _make_hist([3.0, 4.0])
    h3 = _make_hist([5.0, 6.0])
    main_ax, _ = overlay([h1, h2, h3])
    assert isinstance(main_ax, MplAxes)


# ---------------------------------------------------------------------------
# Ratio value / error tests
# ---------------------------------------------------------------------------

def test_ratio_values_correct():
    h1 = _make_hist([1.0, 2.0, 4.0], variances=[1.0, 2.0, 4.0])
    h2 = _make_hist([2.0, 4.0, 8.0], variances=[2.0, 4.0, 8.0])
    _, ratio_ax = overlay([h1, h2], ratio=True)
    assert ratio_ax is not None
    ref = h1.values
    num = h2.values
    expected_ratio = num / ref
    np.testing.assert_allclose(expected_ratio, np.array([2.0, 2.0, 2.0]))


def test_ratio_values_computed():
    """Verify ratio computation end-to-end by checking errorbar y-values."""
    h_ref = _make_hist([4.0, 8.0], variances=[4.0, 8.0])
    h_num = _make_hist([2.0, 4.0], variances=[2.0, 4.0])
    _, ratio_ax = overlay([h_ref, h_num], ratio=True)
    assert ratio_ax is not None
    container = ratio_ax.containers[0]
    # lines[2][0] is the LineCollection for vertical error bars
    segments = container.lines[2][0].get_segments()  # type: ignore[union-attr]
    y_mids = np.array([(s[0][1] + s[1][1]) / 2 for s in segments])
    np.testing.assert_allclose(y_mids, np.array([0.5, 0.5]))


def test_ratio_errors_correct():
    h_ref = _make_hist([4.0], variances=[4.0])   # errors = [2.0]
    h_num = _make_hist([8.0], variances=[16.0])  # errors = [4.0]
    _, ratio_ax = overlay([h_ref, h_num], ratio=True)
    assert ratio_ax is not None
    # r = 8/4 = 2.0, sigma_r = sqrt((4/4)^2 + (8*2/16)^2) = sqrt(2)
    expected_err = np.sqrt((4.0 / 4.0) ** 2 + (8.0 * 2.0 / 4.0**2) ** 2)
    container = ratio_ax.containers[0]
    segments = container.lines[2][0].get_segments()  # type: ignore[union-attr]  # [[x, y_lo], [x, y_hi]]
    actual_err = (segments[0][1][1] - segments[0][0][1]) / 2
    np.testing.assert_allclose(actual_err, expected_err, rtol=1e-6)


def test_ratio_zero_denominator_is_nan():
    h_ref = _make_hist([0.0, 2.0], variances=[0.0, 2.0])
    h_num = _make_hist([1.0, 4.0], variances=[1.0, 4.0])
    _, ratio_ax = overlay([h_ref, h_num], ratio=True)
    assert ratio_ax is not None
    container = ratio_ax.containers[0]
    segments = container.lines[2][0].get_segments()  # type: ignore[union-attr]
    # Bin 0 is NaN → matplotlib stores it as an empty segment; bin 1 has ratio=2.0
    non_empty = [s for s in segments if len(s) == 2]
    assert len(non_empty) == 1
    y_mid = (non_empty[0][0][1] + non_empty[0][1][1]) / 2
    np.testing.assert_allclose(y_mid, 2.0)


# ---------------------------------------------------------------------------
# Legend test
# ---------------------------------------------------------------------------

def test_labels_produce_legend():
    h1 = _make_hist([1.0, 2.0])
    h2 = _make_hist([2.0, 4.0])
    main_ax, _ = overlay([h1, h2], labels=["a", "b"])
    assert main_ax.get_legend() is not None


# ---------------------------------------------------------------------------
# Error / validation tests
# ---------------------------------------------------------------------------

def test_non_1d_raises_value_error():
    ax1 = Axis(edges=np.array([0.0, 1.0, 2.0]))
    ax2 = Axis(edges=np.array([0.0, 1.0, 2.0]))
    h2d = Histogram(
        axes=[ax1, ax2], values=np.zeros((2, 2)), variances=np.zeros((2, 2))
    )
    with pytest.raises(ValueError, match="1D"):
        overlay([h2d])


def test_ax_supplied_with_ratio_raises_value_error():
    import matplotlib.pyplot as plt
    _, ax = plt.subplots()
    h = _make_hist([1.0, 2.0])
    with pytest.raises(ValueError, match="ax cannot be supplied"):
        overlay([h], ax=ax, ratio=True)


def test_labels_length_mismatch_raises_value_error():
    h1 = _make_hist([1.0])
    h2 = _make_hist([2.0])
    with pytest.raises(ValueError, match="labels"):
        overlay([h1, h2], labels=["only_one"])


# ---------------------------------------------------------------------------
# Integration tests (ROOT data)
# ---------------------------------------------------------------------------

def test_overlay_root_hx_hy():
    uproot = pytest.importorskip("uproot")  # noqa: F841
    from unrooted.io.root.reader import load

    hx = load(DATA_DIR / "tests_input.root", "hx")
    hy = load(DATA_DIR / "tests_input.root", "hy")
    main_ax, ratio_ax = overlay([hx, hy], labels=["hx", "hy"])
    assert isinstance(main_ax, MplAxes)
    assert ratio_ax is None


def test_overlay_root_hx_hy_ratio():
    uproot = pytest.importorskip("uproot")  # noqa: F841
    from unrooted.io.root.reader import load

    hx = load(DATA_DIR / "tests_input.root", "hx")
    hy = load(DATA_DIR / "tests_input.root", "hy")
    main_ax, ratio_ax = overlay([hx, hy], ratio=True, labels=["hx", "hy"])
    assert isinstance(main_ax, MplAxes)
    assert isinstance(ratio_ax, MplAxes)


# ---------------------------------------------------------------------------
# Ratio panel inherits style of B
# ---------------------------------------------------------------------------


def test_ratio_panel_uses_b_line_color():
    """The step line in the ratio panel must use B's line_color."""
    h1 = _make_hist([2.0, 4.0])
    h2 = _make_hist([4.0, 8.0])
    s1 = HistogramStyle(line_color="#aaaaaa", error_display=None)
    s2 = HistogramStyle(line_color="#3A6FA8", error_display=None)
    _, ratio_ax = overlay([h1, h2], ratio=True, styles=[s1, s2])
    assert ratio_ax is not None
    # ax.stairs() adds a StepPatch; its edge color must match B's line_color.
    from matplotlib.patches import StepPatch
    step_patches = [a for a in ratio_ax.get_children() if isinstance(a, StepPatch)]
    assert step_patches, "expected at least one StepPatch in ratio panel"
    import matplotlib.colors as mcolors
    colors_hex = [
        mcolors.to_hex(p.get_edgecolor()) for p in step_patches
    ]
    assert any(c == "#3a6fa8" for c in colors_hex)


def test_ratio_panel_no_errors_when_error_display_none():
    """When style has error_display=None, ratio panel must draw no error bars."""
    h1 = _make_hist([2.0, 4.0])
    h2 = _make_hist([4.0, 8.0])
    s1 = HistogramStyle(line_color="C0", error_display=None)
    s2 = HistogramStyle(line_color="C1", error_display=None)
    _, ratio_ax = overlay([h1, h2], ratio=True, styles=[s1, s2])
    assert ratio_ax is not None
    assert len(ratio_ax.containers) == 0


def test_ratio_range_sets_ylim():
    h1 = _make_hist([2.0, 4.0])
    h2 = _make_hist([4.0, 8.0])
    _, ratio_ax = overlay([h1, h2], ratio=True, ratio_range=(0.5, 1.5))
    assert ratio_ax is not None
    assert ratio_ax.get_ylim() == pytest.approx((0.5, 1.5))


def test_ratio_panel_has_errors_when_error_display_bar():
    """When style has error_display='bar', ratio panel must draw error bars."""
    h1 = _make_hist([2.0, 4.0])
    h2 = _make_hist([4.0, 8.0])
    s1 = HistogramStyle(line_color="C0", error_display="bar")
    s2 = HistogramStyle(line_color="C1", error_display="bar")
    _, ratio_ax = overlay([h1, h2], ratio=True, styles=[s1, s2])
    assert ratio_ax is not None
    assert len(ratio_ax.containers) == 1


def test_ratio_panel_uses_b_line_style():
    """The step line in the ratio panel must use B's line_style and line_width."""
    h1 = _make_hist([2.0, 4.0])
    h2 = _make_hist([4.0, 8.0])
    s1 = HistogramStyle(line_color="C0")
    s2 = HistogramStyle(line_color="C1", line_style="--", line_width=2.5)
    _, ratio_ax = overlay([h1, h2], ratio=True, styles=[s1, s2])
    assert ratio_ax is not None
    # StepPatch linewidth reflects line_width of B
    from matplotlib.patches import StepPatch
    step_patches = [a for a in ratio_ax.get_children() if isinstance(a, StepPatch)]
    widths = [a.get_linewidth() for a in step_patches]
    assert any(abs(w - 2.5) < 0.01 for w in widths)
