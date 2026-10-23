from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from unrooted.core.histogram import Histogram
from unrooted.plot._stack import finite_runs, prepare_stack
from unrooted.plot.plotly._color import _to_rgba
from unrooted.plot.plotly.histogram import _LINE_DASH, DEFAULT_COLORS, _staircase
from unrooted.plot.style import HistogramStyle


def stack(
    hists: list[Histogram],
    labels: list[str] | None = None,
    styles: list[HistogramStyle] | None = None,
    *,
    uncertainty: bool = True,
) -> go.Figure:
    """Stack additive 1D histograms in input order, first at the bottom.

    Requires identical edges, nonnegative values, and no profile/efficiency
    spread bounds. Missing values make the whole bin a gap; missing variances
    make only the total band a gap. Flow bins are omitted. Inputs are not
    modified, normalized, or rebinned. Nonnegative weighted yields are supported.

    Args:
        hists: Nonempty list of additive count/yield histograms.
        labels: Optional legend labels in input order, one per component.
        styles: Per-component fill and line settings; defaults to as_stack().
            Marker/error/spread settings do not apply to components. Supported
            hatches are /, backslash, x, -, |, +, and dot. Use hex/RGBA colors
            for consistent opacity across backends.
        uncertainty: Draw total ± sqrt(sum(variances)), assuming independent
            components with no covariance. The band is not clipped at zero.

    Returns:
        A Plotly figure. Legend toggles hide a component's drawing; they do not
        recompute other layers or the uncertainty of the original full sum.

    Raises:
        ValueError: For incompatible bins, negative values, spread bounds,
            mismatched labels/styles, or nonrepresentable cumulative sums.
    """
    data = prepare_stack(hists, labels, styles, DEFAULT_COLORS, uncertainty)
    fig = go.Figure()
    for i, style in enumerate(data.styles):
        x, upper = _staircase(data.edges, data.upper[i])
        _, lower = _staircase(data.edges, data.lower[i])
        label = labels[i] if labels is not None else None
        group = f"stack-{i}"
        if style.fill_alpha is not None:
            assert style.fill_color is not None
            _add_fill(
                fig,
                x,
                lower,
                upper,
                _to_rgba(style.fill_color, style.fill_alpha),
                label,
                group,
                style.fill_hatch,
            )
            label = None
        if style.line_style is not None:
            assert style.line_color is not None
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=upper,
                    mode="lines",
                    name=labels[i] if labels is not None else f"Component {i + 1}",
                    legendgroup=group,
                    showlegend=label is not None,
                    connectgaps=False,
                    customdata=np.repeat(hists[i].values, 2),
                    hovertemplate=(
                        "%{x}<br>Component: %{customdata}<br>Cumulative: %{y}"
                        "<extra>%{fullData.name}</extra>"
                    ),
                    line=dict(
                        color=_to_rgba(style.line_color, style.line_alpha),
                        width=style.line_width,
                        dash=_LINE_DASH[style.line_style],
                    ),
                )
            )
    if uncertainty:
        total = data.upper[-1]
        x, upper = _staircase(data.edges, total + data.errors)
        _, lower = _staircase(data.edges, total - data.errors)
        _add_fill(
            fig,
            x,
            lower,
            upper,
            "rgba(48,48,48,0.25)",
            "Total ±1σ" if labels is not None else None,
            "stack-total",
        )
    fig.update_layout(
        xaxis_title=hists[0].axes[0].label or None,
        title=hists[0].title or None,
        legend=dict(traceorder="normal", groupclick="togglegroup"),
    )
    return fig


def _add_fill(
    fig: go.Figure,
    x: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    color: str,
    label: str | None,
    group: str,
    hatch: str | None = None,
) -> None:
    # Independent closed polygons remain correct when another trace is hidden.
    for segment in finite_runs(lower, upper):
        xs = x[segment]
        fig.add_trace(
            go.Scatter(
                x=np.r_[xs, xs[::-1], xs[0]],
                y=np.r_[upper[segment], lower[segment][::-1], upper[segment][0]],
                mode="lines",
                line=dict(width=0),
                fill="toself",
                fillcolor=color,
                fillpattern=dict(shape=hatch or ""),
                name=label,
                legendgroup=group,
                showlegend=label is not None,
                hoverinfo="skip",
            )
        )
        label = None
