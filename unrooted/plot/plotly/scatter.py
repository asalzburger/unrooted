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
    *,
    fig: go.Figure | None = None,
    row: int | None = None,
    col: int | None = None,
    set_axis_labels: bool = True,
) -> go.Figure:
    """Render a :class:`~unrooted.core.scatter.ScatterData` as a Plotly figure.

    Args:
        scatter: The point cloud to render.
        style:   Visual style; defaults to
                 :meth:`~unrooted.plot.style.HistogramStyle.as_scatter`.
        label:   Trace name shown in the legend.
        fig: Existing figure, or None to create one.
        row: Optional subplot row; supply together with col and an existing figure.
        col: Optional subplot column.
        set_axis_labels: Apply this dataset's labels and title when True.

    Returns:
        A :class:`plotly.graph_objects.Figure`.
    """
    scatter.validate()
    if (row is None) != (col is None) or (row is not None and fig is None):
        raise ValueError(
            "row and col require each other and an existing subplot figure"
        )
    eff_style = style if style is not None else HistogramStyle.as_scatter()
    color: str | tuple[float, ...] = (
        eff_style.marker_color
        if eff_style.marker_color is not None
        else DEFAULT_COLORS[0]
    )
    if fig is None:
        fig = go.Figure()
    _add_scatter_trace(fig, scatter, eff_style, color, label=label, row=row, col=col)
    axis_kw = {"row": row, "col": col} if row is not None else {}
    if set_axis_labels:
        if scatter.x_label:
            fig.update_xaxes(title_text=scatter.x_label, **axis_kw)
        if scatter.y_label:
            fig.update_yaxes(title_text=scatter.y_label, **axis_kw)
        if scatter.title:
            fig.update_layout(title=scatter.title)
    return fig


def overlay(
    scatters: list[ScatterData],
    labels: list[str] | None = None,
    styles: list[HistogramStyle] | None = None,
) -> go.Figure:
    """Overlay point clouds, using the first dataset's axis labels and title.

    Args:
        scatters: Nonempty list of point clouds.
        labels: Optional legend labels, one per dataset.
        styles: Optional styles, one per dataset; otherwise cycle marker colors.
    """
    if not scatters:
        raise ValueError("scatters must not be empty")
    if labels is not None and len(labels) != len(scatters):
        raise ValueError("labels must have the same length as scatters")
    if styles is not None and len(styles) != len(scatters):
        raise ValueError("styles must have the same length as scatters")
    for scatter in scatters:
        scatter.validate()
    fig = go.Figure()
    for i, scatter in enumerate(scatters):
        color = DEFAULT_COLORS[i % len(DEFAULT_COLORS)]
        style = (
            styles[i]
            if styles is not None
            else HistogramStyle.as_scatter().with_color(color)
        )
        if style.marker_color is None:
            style = style.with_color(color)
        plot(
            scatter,
            style=style,
            label=labels[i] if labels is not None else None,
            fig=fig,
            set_axis_labels=i == 0,
        )
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
