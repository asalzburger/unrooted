"""The public stack contract, checked against actual rendered geometry."""

from dataclasses import asdict
from importlib import import_module

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.path import Path

from unrooted.core import Axis, Histogram
from unrooted.plot import HistogramStyle


def hist(values, variances=None, edges=None):
    values = np.asarray(values)
    return Histogram(
        [
            Axis(
                np.array([0.0, 1.0, 3.0, 6.0] if edges is None else edges), label="Mass"
            )
        ],
        values,
        values.copy() if variances is None else np.asarray(variances),
        title="Yields",
    )


@pytest.fixture(params=["mpl", "plotly"])
def backend(request):
    if request.param == "plotly":
        pytest.importorskip("plotly")
    return request.param, import_module(f"unrooted.plot.{request.param}").stack


def polygons(result, backend, group):
    """Return polygons in data coordinates, ignoring outlines."""
    if backend == "plotly":
        return [
            np.column_stack([t.x, t.y])
            for t in result.data
            if t.legendgroup == group and t.fill == "toself"
        ]
    if group == "stack-total":
        return [p.vertices for p in result.collections[0].get_paths()]
    patch = [p for p in result.patches if p.get_fill()][int(group.split("-")[1])]
    path = patch.get_path()
    starts = np.flatnonzero(path.codes == Path.MOVETO)
    return np.split(path.vertices, starts[1:]) if len(starts) else []


def bounds_at(polys, x):
    """Read lower/upper boundaries halfway through a bin."""
    intersections = []
    for poly in polys:
        for a, b in zip(poly, np.roll(poly, -1, axis=0)):
            if min(a[0], b[0]) < x < max(a[0], b[0]):
                intersections.append(a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    assert intersections, f"No polygon covers x={x}"
    return min(intersections), max(intersections)


def test_stack_layers_and_independent_total(backend):
    name, stack = backend
    first, second = (
        hist([2.0, 4.0, 1.0], [0.25, 1.0, 4.0]),
        hist([3.0, 1.0, 5.0], [1.0, 4.0, 9.0]),
    )
    result = stack([first, second], labels=["First", "Second"])
    for i, x in enumerate([0.5, 2.0, 4.5]):
        np.testing.assert_allclose(
            bounds_at(polygons(result, name, "stack-0"), x), [0, first.values[i]]
        )
        total = first.values[i] + second.values[i]
        np.testing.assert_allclose(
            bounds_at(polygons(result, name, "stack-1"), x), [first.values[i], total]
        )
        error = np.sqrt(first.variances[i] + second.variances[i])
        np.testing.assert_allclose(
            bounds_at(polygons(result, name, "stack-total"), x),
            [total - error, total + error],
        )
    if name == "mpl":
        assert result.get_xlabel() == "Mass" and result.get_title() == "Yields"
        labels = result.get_legend_handles_labels()[1]
    else:
        assert result.layout.xaxis.title.text == "Mass"
        assert result.layout.title.text == "Yields"
        labels = [t.name for t in result.data if t.showlegend]
        assert result.layout.legend.groupclick == "togglegroup"
        outline = next(
            t for t in result.data if t.legendgroup == "stack-1" and t.fill != "toself"
        )
        assert outline.name == "Second"
        np.testing.assert_array_equal(outline.customdata, np.repeat(second.values, 2))
    assert labels == ["First", "Second", "Total ±1σ"]


@pytest.mark.parametrize("reverse", [False, True])
def test_order_and_no_mutation(backend, reverse):
    name, stack = backend
    hists = [hist([2.0, 4.0, 1.0]), hist([3.0, 1.0, 5.0])][:: (-1 if reverse else 1)]
    style = HistogramStyle.as_stack(fill_color="#123456", fill_hatch="/")
    before_style = asdict(style)
    originals = []
    for h in hists:
        h.overflow = np.array([100.0, *h.values, 200.0])
        arrays = [h.values, h.variances, h.axes[0].edges, h.overflow]
        originals.append([a.copy() for a in arrays])
        for a in arrays:
            a.flags.writeable = False
    result = stack(hists, styles=[style, style], uncertainty=False)
    assert asdict(style) == before_style
    for h, arrays in zip(hists, originals):
        for actual, original in zip(
            [h.values, h.variances, h.axes[0].edges, h.overflow], arrays
        ):
            np.testing.assert_array_equal(actual, original)
    assert bounds_at(polygons(result, name, "stack-1"), 0.5) == (hists[0].values[0], 5)
    if name == "mpl":
        assert not result.collections
        assert result.get_legend() is None
        assert result.patches[0].get_hatch() == "/"
    else:
        assert not any(t.legendgroup == "stack-total" for t in result.data)
        assert not any(t.showlegend for t in result.data)
        assert result.data[0].fillpattern.shape == "/"
        assert result.data[0].fillcolor == "rgba(18,52,86,0.8)"


@pytest.mark.parametrize("missing", ["value", "variance"])
def test_nan_gaps_never_bridge(backend, missing):
    name, stack = backend
    a, b = hist([1.0, 2.0, 3.0]), hist([3.0, 2.0, 1.0])
    (b.values if missing == "value" else b.variances)[1] = np.nan
    result = stack([a, b], labels=["A", "B"])
    groups = ["stack-total"] + (["stack-0", "stack-1"] if missing == "value" else [])
    for group in groups:
        ps = polygons(result, name, group)
        assert len(ps) == 2
        assert all(p[:, 0].max() <= 1 or p[:, 0].min() >= 3 for p in ps)
    if missing == "variance":
        assert bounds_at(polygons(result, name, "stack-1"), 2) == (2, 4)


@pytest.mark.parametrize("values", [[0.0, 0.0, 0.0], [np.nan, np.nan, np.nan]])
def test_zero_or_missing_stack_renders(backend, values):
    _, stack = backend
    stack([hist(values)], labels=["Empty"])


def test_total_band_is_not_clipped_at_zero(backend):
    name, stack = backend
    result = stack([hist([0.0, 0.0, 0.0], [4.0, 4.0, 4.0])])
    assert bounds_at(polygons(result, name, "stack-total"), 0.5) == (-2, 2)


@pytest.mark.parametrize(
    "invalid",
    [
        "empty",
        "negative",
        "2d",
        "edges",
        "shape",
        "spread",
        "mutated",
        "labels",
        "styles",
        "hatch",
        "line",
        "overflow",
        "variance_overflow",
        "uncertainty",
    ],
)
def test_reject_invalid_inputs_before_drawing(backend, invalid):
    name, stack = backend
    hists = [hist([1.0, 2.0, 3.0]), hist([4.0, 5.0, 6.0])]
    options = {}
    if invalid == "empty":
        hists = []
    elif invalid == "negative":
        hists[1].values[1] = -1
    elif invalid == "2d":
        hists = [
            Histogram(
                [Axis(np.arange(3)), Axis(np.arange(3))],
                np.ones((2, 2)),
                np.ones((2, 2)),
            )
        ]
    elif invalid == "edges":
        hists[1].axes[0].edges[1] += 1e-10
    elif invalid == "shape":
        hists[1] = hist([1.0, 2.0], edges=[0.0, 1.0, 3.0])
    elif invalid == "spread":
        hists[1].spread_min = hists[1].values - 1
        hists[1].spread_max = hists[1].values + 1
    elif invalid == "mutated":
        hists[1].variances[0] = -1
    elif invalid in ("labels", "styles"):
        options[invalid] = []
    elif invalid in ("hatch", "line"):
        style = HistogramStyle.as_stack(
            **{f"{'fill_hatch' if invalid == 'hatch' else 'line_style'}": "unsupported"}
        )
        options["styles"] = [style, style]
    elif invalid in ("overflow", "variance_overflow"):
        for h in hists:
            (h.values if invalid == "overflow" else h.variances)[:] = 1e308
    else:
        options["uncertainty"] = "yes"
    if name == "mpl":
        _, ax = plt.subplots()
        options["ax"] = ax
        before = len(ax.get_children())
    with pytest.raises(ValueError):
        stack(hists, **options)
    if name == "mpl":
        assert len(ax.get_children()) == before


def test_large_integers_accumulate_without_wrapping(backend):
    name, stack = backend
    h = hist(np.full(3, 2**62, dtype=np.int64))
    result = stack([h, h, h])
    np.testing.assert_allclose(
        bounds_at(polygons(result, name, "stack-2"), 0.5), [2**63, 3 * 2**62]
    )


def test_line_only_and_fill_only_styles(backend):
    name, stack = backend
    result = stack(
        [hist([1.0, 2.0, 3.0]), hist([2.0, 3.0, 4.0])],
        labels=["Outline", "Fill"],
        styles=[
            HistogramStyle.as_line(line_style="--"),
            HistogramStyle.as_stack(line_style=None),
        ],
        uncertainty=False,
    )
    if name == "mpl":
        assert len(result.patches) == 2
        assert result.patches[0].get_linestyle() == "--"
        assert result.get_legend_handles_labels()[1] == ["Outline", "Fill"]
    else:
        assert len(result.data) == 2
        assert result.data[0].line.dash == "dash"
        assert [t.name for t in result.data if t.showlegend] == ["Outline", "Fill"]


def test_mpl_existing_axes_and_stack_preset():
    from unrooted.plot.mpl import stack

    _, ax = plt.subplots()
    assert stack([hist([1.0, 2.0, 3.0])], ax=ax) is ax
    style = HistogramStyle.as_stack(fill_alpha=0.6)
    assert style.fill_alpha == 0.6 and style.line_style == "-"
    assert style.marker is style.error_display is style.spread_display is None
