from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from unrooted.core.histogram import Histogram
from unrooted.plot.plotly._color import _to_rgba
from unrooted.plot.style import HistogramStyle

_LINE_DASH: dict[str, str] = {
    "-": "solid",
    "--": "dash",
    ":": "dot",
    "-.": "dashdot",
}

_MARKER_SYMBOL: dict[str, str] = {
    "o": "circle",
    "s": "square",
    "^": "triangle-up",
    "D": "diamond",
    "+": "cross",
    "x": "x",
}

# Plotly default qualitative color sequence.
DEFAULT_COLORS: list[str] = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA",
    "#FFA15A", "#19D3F3", "#FF6692", "#B6E880",
    "#FF97FF", "#FECB52",
]


def plot(
    hist: Histogram,
    style: HistogramStyle | None = None,
) -> go.Figure:
    """Plot a histogram as an interactive Plotly figure.

    Supports 1D and 2D histograms.  A :class:`~unrooted.plot.style.HistogramStyle`
    controls line, marker, fill, error bars, and spread display for 1D plots.

    Note:
        Matplotlib-style shorthand colors (``"C0"``, ``"r"``, ``"k"``) are not
        supported.  Use hex strings (``"#1A4F8A"``) or RGBA tuples instead.

    Args:
        hist:  Histogram to plot.
        style: Visual style.  A default :class:`~unrooted.plot.style.HistogramStyle`
               is used when ``None``.

    Returns:
        A :class:`plotly.graph_objects.Figure`.
    """
    fig = go.Figure()
    if hist.ndim == 1:
        eff_style = style if style is not None else HistogramStyle()
        color: str | tuple[float, ...] = (
            eff_style.line_color
            if eff_style.line_color is not None
            else DEFAULT_COLORS[0]
        )
        _add_1d_traces(fig, hist, eff_style, color, label=hist.name or None)
        if hist.axes[0].label:
            fig.update_xaxes(title_text=hist.axes[0].label)
        if hist.title:
            fig.update_layout(title=hist.title)
    elif hist.ndim == 2:
        _add_2d_trace(fig, hist)
    else:
        raise ValueError(f"Cannot plot {hist.ndim}D histogram")
    return fig


# ---------------------------------------------------------------------------
# Internal helpers (also imported by overlay.py)
# ---------------------------------------------------------------------------


def _staircase(
    edges: np.ndarray,
    values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return staircase x,y arrays for a step-function histogram.

    Given *edges* of length n+1 and *values* of length n, produces paired
    arrays of length 2n that trace the bin boundaries:
    ``x = [e0, e1, e1, e2, …, e_{n-1}, en]``,
    ``y = [v0, v0, v1, v1, …, v_{n-1}, v_{n-1}]``.
    NaN values in *values* propagate and appear as gaps in plotly.
    """
    x = np.repeat(edges, 2)[1:-1]
    y = np.repeat(values, 2)
    return x, y


def _add_1d_traces(
    fig: go.Figure,
    hist: Histogram,
    style: HistogramStyle,
    color: str | tuple[float, ...],
    label: str | None = None,
    row: int | None = None,
    col: int | None = None,
) -> None:
    """Add styled 1D histogram traces to *fig*.

    Args:
        fig:   Target figure (plain or subplot).
        hist:  1D histogram.
        style: Visual style.
        color: Resolved base color (hex or rgba tuple).
        label: Trace name shown in the legend; ``None`` hides the legend entry.
        row:   Subplot row (``None`` for non-subplot figures).
        col:   Subplot column (``None`` for non-subplot figures).
    """
    edges = hist.axes[0].edges
    values = hist.values
    centers = hist.axes[0].centers
    errors = hist.errors

    x_step, y_step = _staircase(edges, values)
    add_kw: dict = {"row": row, "col": col} if row is not None else {}
    labeled = False

    # 1. Fill (drawn first so it sits behind the line)
    if style.fill_alpha is not None:
        fill_color = style.fill_color if style.fill_color is not None else color
        fig.add_trace(
            go.Scatter(
                x=x_step,
                y=y_step,
                mode="lines",
                line=dict(width=0),
                fill="tozeroy",
                fillcolor=_to_rgba(fill_color, style.fill_alpha),
                showlegend=(label is not None and not labeled),
                name=label,
            ),
            **add_kw,
        )
        labeled = True

    # 2. Step line
    if style.line_style is not None:
        dash = _LINE_DASH.get(style.line_style, "solid")
        fig.add_trace(
            go.Scatter(
                x=x_step,
                y=y_step,
                mode="lines",
                line=dict(
                    color=_to_rgba(color, style.line_alpha),
                    width=style.line_width,
                    dash=dash,
                ),
                showlegend=(label is not None and not labeled),
                name=label,
            ),
            **add_kw,
        )
        labeled = True

    # 3. Markers at bin centres
    if style.marker is not None:
        marker_color = style.marker_color if style.marker_color is not None else color
        symbol = _MARKER_SYMBOL.get(style.marker, "circle")
        fig.add_trace(
            go.Scatter(
                x=centers,
                y=values,
                mode="markers",
                marker=dict(
                    symbol=symbol,
                    color=_to_rgba(marker_color, style.marker_alpha),
                    size=style.marker_size,
                ),
                showlegend=(label is not None and not labeled),
                name=label,
            ),
            **add_kw,
        )
        labeled = True

    # 4. Error display
    if style.error_display == "bar":
        error_color = style.error_color if style.error_color is not None else color
        fig.add_trace(
            go.Scatter(
                x=centers,
                y=values,
                mode="markers",
                marker=dict(size=0, color="rgba(0,0,0,0)"),
                error_y=dict(
                    type="data",
                    symmetric=True,
                    array=errors,
                    color=_to_rgba(error_color, style.error_alpha),
                    thickness=1.5,
                    width=style.error_capsize,
                ),
                showlegend=False,
                hoverinfo="skip",
            ),
            **add_kw,
        )
    elif style.error_display == "band":
        error_color = style.error_color if style.error_color is not None else color
        _, y_hi = _staircase(edges, values + errors)
        _, y_lo = _staircase(edges, values - errors)
        # Upper boundary (invisible line — required so fill='tonexty' has a target)
        fig.add_trace(
            go.Scatter(
                x=x_step,
                y=y_hi,
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            ),
            **add_kw,
        )
        # Lower boundary, filled up to the previous trace
        fig.add_trace(
            go.Scatter(
                x=x_step,
                y=y_lo,
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor=_to_rgba(error_color, style.error_alpha),
                showlegend=False,
                hoverinfo="skip",
            ),
            **add_kw,
        )

    # 5. Spread display
    if style.spread_display is not None:
        if hist.spread_min is None or hist.spread_max is None:
            raise ValueError(
                "spread_display is set but Histogram has no spread_min/spread_max"
            )
        spread_color = style.spread_color if style.spread_color is not None else color
        if style.spread_display == "bar":
            fig.add_trace(
                go.Scatter(
                    x=centers,
                    y=values,
                    mode="markers",
                    marker=dict(size=0, color="rgba(0,0,0,0)"),
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=hist.spread_max - values,
                        arrayminus=values - hist.spread_min,
                        color=_to_rgba(spread_color, style.spread_alpha),
                        thickness=1.5,
                        width=style.spread_capsize,
                    ),
                    showlegend=False,
                    hoverinfo="skip",
                ),
                **add_kw,
            )
        else:  # band
            _, y_hi_s = _staircase(edges, hist.spread_max)
            _, y_lo_s = _staircase(edges, hist.spread_min)
            fig.add_trace(
                go.Scatter(
                    x=x_step,
                    y=y_hi_s,
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo="skip",
                ),
                **add_kw,
            )
            fig.add_trace(
                go.Scatter(
                    x=x_step,
                    y=y_lo_s,
                    mode="lines",
                    line=dict(width=0),
                    fill="tonexty",
                    fillcolor=_to_rgba(spread_color, style.spread_alpha),
                    showlegend=False,
                    hoverinfo="skip",
                ),
                **add_kw,
            )


def _add_2d_trace(fig: go.Figure, hist: Histogram) -> None:
    fig.add_trace(
        go.Heatmap(
            x=hist.axes[0].centers,
            y=hist.axes[1].centers,
            z=hist.values.T,
            colorscale="Viridis",
        )
    )
    if hist.axes[0].label:
        fig.update_xaxes(title_text=hist.axes[0].label)
    if hist.axes[1].label:
        fig.update_yaxes(title_text=hist.axes[1].label)
    if hist.title:
        fig.update_layout(title=hist.title)
