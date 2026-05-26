from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram
from unrooted.plot.terminal import MAX_BINS, overlay, plot
from unrooted.plot.terminal._render import _COMBO, _SINGLE, render

DATA_DIR = Path(__file__).parent.parent / 'data' / 'root'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hist(values: list[float], label: str = '', title: str = '') -> Histogram:
    n = len(values)
    axis = Axis(edges=np.arange(n + 1, dtype=float), label=label)
    v = np.array(values, dtype=float)
    h = Histogram(axes=[axis], values=v, variances=v.copy())
    if title:
        h.title = title
    return h


# ---------------------------------------------------------------------------
# plot() — basic contract
# ---------------------------------------------------------------------------


def test_plot_returns_string():
    h = _hist([1.0, 2.0, 3.0])
    result = plot(h)
    assert isinstance(result, str)


def test_plot_output_is_non_empty():
    h = _hist([1.0, 2.0])
    assert len(plot(h)) > 0


def test_plot_line_count_matches_max_lines():
    h = _hist([1.0, 2.0, 3.0])
    result = plot(h, max_lines=20)
    lines = result.splitlines()
    # max_lines body rows + axis line + x-label row = max_lines + 2
    assert len(lines) >= 20 + 2


def test_plot_2d_raises():
    ax1 = Axis(edges=np.array([0.0, 1.0]))
    ax2 = Axis(edges=np.array([0.0, 1.0]))
    h2d = Histogram(
        axes=[ax1, ax2], values=np.zeros((1, 1)), variances=np.zeros((1, 1))
    )
    with pytest.raises(ValueError, match='1D'):
        plot(h2d)


def test_plot_too_many_bins_raises():
    h = _hist([1.0] * (MAX_BINS + 1))
    with pytest.raises(ValueError, match=str(MAX_BINS)):
        plot(h)


def test_plot_max_bins_ok():
    h = _hist([1.0] * MAX_BINS)
    result = plot(h)
    assert isinstance(result, str)


def test_plot_contains_base_marker():
    h = _hist([0.0, 5.0, 0.0])
    result = plot(h)
    # The tallest bin should produce at least one ○
    assert '○' in result


def test_plot_all_zeros_no_marker():
    h = _hist([0.0, 0.0, 0.0])
    result = plot(h)
    assert '○' not in result


def test_plot_title_appears():
    h = _hist([1.0, 2.0], title='My Histogram')
    result = plot(h)
    assert 'My Histogram' in result


def test_plot_x_label_appears():
    h = _hist([1.0, 2.0], label='momentum [GeV]')
    result = plot(h)
    assert 'momentum [GeV]' in result


def test_plot_min_lines_clamped():
    h = _hist([1.0, 2.0])
    result = plot(h, max_lines=1)  # clamped to 5
    assert isinstance(result, str)
    assert len(result.splitlines()) >= 7  # 5 body + axis + x-ticks


# ---------------------------------------------------------------------------
# overlay() — validation
# ---------------------------------------------------------------------------


def test_overlay_returns_string():
    h1 = _hist([1.0, 2.0])
    h2 = _hist([2.0, 1.0])
    result = overlay([h1, h2])
    assert isinstance(result, str)


def test_overlay_empty_raises():
    with pytest.raises(ValueError, match='empty'):
        overlay([])


def test_overlay_2d_raises():
    ax1 = Axis(edges=np.array([0.0, 1.0]))
    ax2 = Axis(edges=np.array([0.0, 1.0]))
    h2d = Histogram(
        axes=[ax1, ax2], values=np.zeros((1, 1)), variances=np.zeros((1, 1))
    )
    with pytest.raises(ValueError, match='1D'):
        overlay([h2d])


def test_overlay_too_many_raises():
    hists = [_hist([1.0, 2.0])] * 5
    with pytest.raises(ValueError, match='4'):
        overlay(hists)


def test_overlay_labels_mismatch_raises():
    h1 = _hist([1.0])
    h2 = _hist([2.0])
    with pytest.raises(ValueError, match='labels'):
        overlay([h1, h2], labels=['only_one'])


def test_overlay_different_bin_count_raises():
    h1 = _hist([1.0, 2.0])        # 2 bins
    h2 = _hist([1.0, 2.0, 3.0])   # 3 bins
    with pytest.raises(ValueError, match='bins'):
        overlay([h1, h2])


# ---------------------------------------------------------------------------
# overlay() — composite glyphs
# ---------------------------------------------------------------------------


def test_overlay_single_hist_uses_circle():
    h = _hist([0.0, 5.0, 0.0])
    result = overlay([h])
    assert '○' in result


def test_overlay_two_full_hists_uses_combo():
    # Both histograms fully fill every bin → every cell has both present
    h1 = _hist([10.0, 10.0, 10.0])
    h2 = _hist([10.0, 10.0, 10.0])
    result = overlay([h1, h2])
    # All cells should be the ⊕ combo (indices 0+1)
    assert '⊕' in result
    assert '○' not in result  # no cells with only hist 0


def test_overlay_three_hists_combo():
    h1 = _hist([10.0])
    h2 = _hist([10.0])
    h3 = _hist([10.0])
    result = overlay([h1, h2, h3])
    assert '⊛' in result


def test_overlay_four_hists_combo():
    h1 = _hist([10.0])
    h2 = _hist([10.0])
    h3 = _hist([10.0])
    h4 = _hist([10.0])
    result = overlay([h1, h2, h3, h4])
    assert '✳' in result


# ---------------------------------------------------------------------------
# overlay() — legend
# ---------------------------------------------------------------------------


def test_overlay_labels_appear_in_legend():
    h1 = _hist([1.0, 2.0])
    h2 = _hist([2.0, 1.0])
    result = overlay([h1, h2], labels=['alpha', 'beta'])
    assert 'alpha' in result
    assert 'beta' in result


def test_overlay_no_labels_no_legend():
    h1 = _hist([1.0, 2.0])
    h2 = _hist([2.0, 1.0])
    result = overlay([h1, h2])
    assert 'alpha' not in result


# ---------------------------------------------------------------------------
# render() — internal unit tests
# ---------------------------------------------------------------------------


def test_render_empty_bins_produce_spaces():
    vals = np.array([0.0, 0.0, 0.0])
    edges = np.array([0.0, 1.0, 2.0, 3.0])
    result = render([vals], edges, max_lines=10)
    # No marker character should appear in body lines
    for ch in _SINGLE:
        assert ch not in result


def test_render_full_bin_fills_column():
    vals = np.array([1.0, 0.0])
    edges = np.array([0.0, 1.0, 2.0])
    result = render([vals], edges, max_lines=5)
    # The first column should contain the base marker in every body row
    lines = result.splitlines()
    body_lines = [ln for ln in lines if '│' in ln]
    marker_col = [ln[ln.index('│') + 1] for ln in body_lines]
    assert all(ch == '○' for ch in marker_col)


def test_render_combo_table_complete():
    # Verify _COMBO covers all 2-element subsets of {0,1,2,3}
    from itertools import combinations
    for r in range(1, 5):
        for subset in combinations(range(4), r):
            assert frozenset(subset) in _COMBO, f'Missing combo: {subset}'


# ---------------------------------------------------------------------------
# Integration (ROOT data)
# ---------------------------------------------------------------------------


def test_plot_root_hx():
    pytest.importorskip('uproot')
    from unrooted.io.root.reader import load
    h = load(DATA_DIR / 'tests_input.root', 'hx')
    result = plot(h)
    assert isinstance(result, str)
    assert '│' in result


def test_overlay_root_hx_hy():
    pytest.importorskip('uproot')
    from unrooted.io.root.reader import load
    hx = load(DATA_DIR / 'tests_input.root', 'hx')
    hy = load(DATA_DIR / 'tests_input.root', 'hy')
    result = overlay([hx, hy], labels=['hx', 'hy'])
    assert 'hx' in result
    assert 'hy' in result
