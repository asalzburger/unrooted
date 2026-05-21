from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from unrooted.core.histogram import Histogram
from unrooted.plot.plotly._color import _to_rgba
from unrooted.plot.plotly.histogram import DEFAULT_COLORS, _add_1d_traces, _staircase
from unrooted.plot.style import HistogramStyle


def overlay(
    hists: list[Histogram],
    labels: list[str] | None = None,
    styles: list[HistogramStyle] | None = None,
    ratio: bool = False,
) -> go.Figure:
    """Overlay multiple 1D histograms in a single interactive Plotly figure.

    Args:
        hists:  1D histograms to overlay.
        labels: Per-histogram legend labels.  Omit to hide the legend.
        styles: Per-histogram visual styles.  When ``None``, styles are
                assigned automatically from the default color sequence.
        ratio:  When ``True``, add a ratio panel (``h_i / h_0``) below the
                main plot.

    Returns:
        A :class:`plotly.graph_objects.Figure`.
    """
    if not hists:
        raise ValueError("hists must not be empty")
    if any(h.ndim != 1 for h in hists):
        raise ValueError("overlay only supports 1D histograms")
    if labels is not None and len(labels) != len(hists):
        raise ValueError("labels must have the same length as hists")
    if styles is not None and len(styles) != len(hists):
        raise ValueError("styles must have the same length as hists")

    if ratio:
        fig = make_subplots(
            rows=2,
            cols=1,
            row_heights=[3, 1],
            shared_xaxes=True,
            vertical_spacing=0.05,
        )
    else:
        fig = go.Figure()

    resolved_colors: list[str | tuple[float, ...]] = []

    for i, hist in enumerate(hists):
        auto_color = DEFAULT_COLORS[i % len(DEFAULT_COLORS)]
        style = (
            styles[i] if styles is not None else HistogramStyle(line_color=auto_color)
        )
        color: str | tuple[float, ...] = (
            style.line_color if style.line_color is not None else auto_color
        )
        if style.line_color is None:
            style = HistogramStyle(**{**style.__dict__, "line_color": auto_color})
        resolved_colors.append(color)

        label = labels[i] if labels is not None else None
        row, col = (1, 1) if ratio else (None, None)
        _add_1d_traces(fig, hist, style, color, label=label, row=row, col=col)

    if hists[0].axes[0].label:
        x_label = hists[0].axes[0].label
        if ratio:
            fig.update_xaxes(title_text=x_label, row=2, col=1)
        else:
            fig.update_xaxes(title_text=x_label)

    if ratio:
        _add_ratio_panel(fig, hists, resolved_colors)

    return fig


def _add_ratio_panel(
    fig: go.Figure,
    hists: list[Histogram],
    colors: list[str | tuple[float, ...]],
) -> None:
    ref_values = hists[0].values
    ref_errors = hists[0].errors
    edges = hists[0].axes[0].edges
    centers = hists[0].axes[0].centers

    for i, hist in enumerate(hists[1:], start=1):
        color = colors[i]
        with np.errstate(invalid="ignore", divide="ignore"):
            r = np.where(ref_values != 0, hist.values / ref_values, np.nan)
            sigma_r = np.where(
                ref_values != 0,
                np.sqrt(
                    (hist.errors / ref_values) ** 2
                    + (hist.values * ref_errors / ref_values**2) ** 2
                ),
                np.nan,
            )

        x_step, r_step = _staircase(edges, r)
        color_str = _to_rgba(color, 1.0)
        fig.add_trace(
            go.Scatter(
                x=x_step,
                y=r_step,
                mode="lines",
                line=dict(color=color_str),
                showlegend=False,
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=centers,
                y=r,
                mode="markers",
                marker=dict(size=0, color="rgba(0,0,0,0)"),
                error_y=dict(
                    type="data",
                    symmetric=True,
                    array=sigma_r,
                    color=color_str,
                    thickness=1.5,
                    width=2,
                ),
                showlegend=False,
                hoverinfo="skip",
            ),
            row=2,
            col=1,
        )

    # Reference line at ratio = 1
    fig.add_trace(
        go.Scatter(
            x=[edges[0], edges[-1]],
            y=[1.0, 1.0],
            mode="lines",
            line=dict(color="black", dash="dash", width=0.8),
            showlegend=False,
            hoverinfo="skip",
        ),
        row=2,
        col=1,
    )
    fig.update_yaxes(title_text="Ratio", row=2, col=1)
