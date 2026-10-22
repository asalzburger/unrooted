from __future__ import annotations

import dataclasses

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from unrooted.core.histogram import Histogram
from unrooted.plot.plotly.histogram import DEFAULT_COLORS, _add_1d_traces
from unrooted.plot.style import HistogramStyle


def overlay(
    hists: list[Histogram],
    labels: list[str] | None = None,
    styles: list[HistogramStyle] | None = None,
    ratio: bool = False,
    ratio_range: tuple[float, float] | None = None,
) -> go.Figure:
    """Overlay multiple 1D histograms in a single interactive Plotly figure.

    Args:
        hists:        1D histograms to overlay.
        labels:       Per-histogram legend labels.  Omit to hide the legend.
        styles:       Per-histogram visual styles.  When ``None``, styles are
                      assigned automatically from the default color sequence.
        ratio:        When ``True``, add a ratio panel (``h_i / h_0``) below
                      the main plot.
        ratio_range:  Optional ``(min, max)`` y-axis limits for the ratio panel.
                      Ignored when *ratio* is ``False``.

    Returns:
        A :class:`plotly.graph_objects.Figure`.
    """
    if not hists:
        raise ValueError("hists must not be empty")
    for hist in hists:
        hist.validate()
        if ratio:
            hists[0].require_compatible_binning(hist)
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
            vertical_spacing=0.025,
        )
    else:
        fig = go.Figure()

    resolved_styles: list[HistogramStyle] = []

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
        resolved_styles.append(style)

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
        _add_ratio_panel(fig, hists, resolved_styles, ratio_range=ratio_range)

    return fig


def _add_ratio_panel(
    fig: go.Figure,
    hists: list[Histogram],
    styles: list[HistogramStyle],
    ratio_range: tuple[float, float] | None = None,
) -> None:
    ref_values = np.asarray(hists[0].values, dtype=float)
    ref_errors = hists[0].errors
    edges = hists[0].axes[0].edges

    for i, hist in enumerate(hists[1:], start=1):
        style = styles[i]
        assert style.line_color is not None
        with np.errstate(invalid="ignore", divide="ignore"):
            r = np.where(ref_values != 0, hist.values / ref_values, np.nan)
            sigma_r = np.zeros_like(r)
            if style.error_display is not None:
                sigma_r = np.where(
                    ref_values != 0,
                    np.sqrt(
                        (hist.errors / ref_values) ** 2
                        + (hist.values * ref_errors / ref_values**2) ** 2
                    ),
                    np.nan,
                )
        ratio_hist = Histogram(
            axes=[hists[0].axes[0]],
            values=r,
            variances=sigma_r**2,
        )
        ratio_style = dataclasses.replace(style, fill_alpha=None, spread_display=None)
        _add_1d_traces(fig, ratio_hist, ratio_style, style.line_color, row=2, col=1)

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
    if ratio_range is not None:
        fig.update_yaxes(range=list(ratio_range), row=2, col=1)
