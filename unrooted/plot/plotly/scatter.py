from __future__ import annotations

import plotly.graph_objects as go

from unrooted.core.scatter import ScatterData
from unrooted.plot.plotly._color import _to_rgba
from unrooted.plot.plotly.histogram import _MARKER_SYMBOL, DEFAULT_COLORS
from unrooted.plot.style import HistogramStyle


def plot(
    scatter: ScatterData,
    style: HistogramStyle | None = None,
    label: str | None = None,
) -> go.Figure:
    """Render a :class:`~unrooted.core.scatter.ScatterData` as a Plotly figure.

    Args:
        scatter: The point cloud to render.
        style:   Visual style; defaults to
                 :meth:`~unrooted.plot.style.HistogramStyle.as_scatter`.
        label:   Trace name shown in the legend.

    Returns:
        A :class:`plotly.graph_objects.Figure`.
    """
    eff_style = style if style is not None else HistogramStyle.as_scatter()
    color: str | tuple[float, ...] = (
        eff_style.marker_color
        if eff_style.marker_color is not None
        else DEFAULT_COLORS[0]
    )
    fig = go.Figure()
    _add_scatter_trace(fig, scatter, eff_style, color, label=label)
    if scatter.x_label:
        fig.update_xaxes(title_text=scatter.x_label)
    if scatter.y_label:
        fig.update_yaxes(title_text=scatter.y_label)
    if scatter.title:
        fig.update_layout(title=scatter.title)
    return fig


def _add_scatter_trace(
    fig: go.Figure,
    scatter: ScatterData,
    style: HistogramStyle,
    color: str | tuple[float, ...],
    label: str | None = None,
    row: int | None = None,
    col: int | None = None,
) -> None:
    """Add a single scatter trace to *fig*.

    Args:
        fig:     Target figure (plain or subplot).
        scatter: Point cloud.
        style:   Visual style.
        color:   Resolved base color (hex or rgba tuple).
        label:   Trace name shown in the legend; ``None`` hides the entry.
        row:     Subplot row (``None`` for non-subplot figures).
        col:     Subplot column (``None`` for non-subplot figures).
    """
    marker_color = style.marker_color if style.marker_color is not None else color
    # "." (matplotlib tiny dot) has no plotly equivalent; map to "circle".
    # Small marker_size (default 2.0 from as_scatter) gives the same visual.
    symbol = _MARKER_SYMBOL.get(style.marker or ".", "circle")
    add_kw: dict = {"row": row, "col": col} if row is not None else {}
    fig.add_trace(
        go.Scatter(
            x=scatter.x,
            y=scatter.y,
            mode="markers",
            marker=dict(
                symbol=symbol,
                color=_to_rgba(marker_color, style.marker_alpha),
                size=style.marker_size,
            ),
            showlegend=label is not None,
            name=label,
        ),
        **add_kw,
    )
