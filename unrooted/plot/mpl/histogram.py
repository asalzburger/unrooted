from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.axes import Axes as MplAxes

from unrooted.core.histogram import Histogram
from unrooted.plot.mpl._range import _draw_range
from unrooted.plot.style import HistogramStyle


def _resolve(
    color: str | tuple[float, ...] | None,
    fallback: str | tuple[float, ...],
) -> str | tuple[float, ...]:
    return color if color is not None else fallback


def plot(
    hist: Histogram,
    ax: MplAxes | None = None,
    style: HistogramStyle | None = None,
    **kwargs,
) -> MplAxes:
    if ax is None:
        _, ax = plt.subplots()
    if hist.ndim == 1:
        if style is not None:
            return _plot_1d_styled(hist, ax, style)
        return _plot_1d(hist, ax, **kwargs)
    if hist.ndim == 2:
        return _plot_2d(hist, ax, **kwargs)
    raise ValueError(f"Cannot plot {hist.ndim}D histogram")


def _plot_1d(hist: Histogram, ax: MplAxes, **kwargs) -> MplAxes:
    edges = hist.axes[0].edges
    values = hist.values
    centers = hist.axes[0].centers

    stairs_kwargs = {k: v for k, v in kwargs.items() if k not in ("capsize",)}
    ax.stairs(values, edges, **stairs_kwargs)
    ax.errorbar(
        centers,
        values,
        yerr=hist.errors,
        fmt="none",
        color="black",
        capsize=kwargs.get("capsize", 2),
    )

    if hist.axes[0].label:
        ax.set_xlabel(hist.axes[0].label)
    if hist.title:
        ax.set_title(hist.title)
    return ax


def _plot_1d_styled(
    hist: Histogram,
    ax: MplAxes,
    style: HistogramStyle,
    label: str | None = None,
    set_axis_labels: bool = True,
) -> MplAxes:
    edges = hist.axes[0].edges
    values = hist.values
    centers = hist.axes[0].centers
    errors = hist.errors

    # Resolve the base color from the style or the axes cycle.
    if style.line_color is not None:
        base_color: str | tuple[float, ...] = style.line_color
    else:
        base_color = ax._get_lines.get_next_color()  # type: ignore[attr-defined]

    labeled = False

    # 1. Fill (drawn first so it sits behind the line)
    if style.fill_alpha is not None:
        fill_color = _resolve(style.fill_color, base_color)
        fill_label = label if not labeled else None
        ax.stairs(
            values,
            edges,
            color=fill_color,
            fill=True,
            linewidth=0,
            alpha=style.fill_alpha,
            hatch=style.fill_hatch,
            label=fill_label,
        )
        labeled = True

    # 2. Step line
    if style.line_style is not None:
        line_label = label if not labeled else None
        ax.stairs(
            values,
            edges,
            color=base_color,
            alpha=style.line_alpha,
            linewidth=style.line_width,
            linestyle=style.line_style,
            label=line_label,
        )
        labeled = True

    # 3. Markers at bin centres
    if style.marker is not None:
        marker_color = _resolve(style.marker_color, base_color)
        marker_label = label if not labeled else None
        ax.plot(
            centers,
            values,
            marker=style.marker,
            linestyle="none",
            color=marker_color,
            alpha=style.marker_alpha,
            markersize=style.marker_size,
            label=marker_label,
        )
        labeled = True

    # 4. Error display
    if style.error_display is not None:
        error_color = _resolve(style.error_color, base_color)
        _draw_range(
            ax,
            centers=centers,
            values=values,
            lo=values - errors,
            hi=values + errors,
            edges=edges,
            mode=style.error_display,
            color=error_color,
            alpha=style.error_alpha,
            capsize=style.error_capsize,
        )

    # 5. Spread display
    if style.spread_display is not None:
        if hist.spread_min is None or hist.spread_max is None:
            raise ValueError(
                "spread_display is set but Histogram has no spread_min/spread_max"
            )
        spread_color = _resolve(style.spread_color, base_color)
        _draw_range(
            ax,
            centers=centers,
            values=values,
            lo=hist.spread_min,
            hi=hist.spread_max,
            edges=edges,
            mode=style.spread_display,
            color=spread_color,
            alpha=style.spread_alpha,
            capsize=style.spread_capsize,
        )

    if set_axis_labels:
        if hist.axes[0].label:
            ax.set_xlabel(hist.axes[0].label)
        if hist.title:
            ax.set_title(hist.title)
    return ax


def _plot_2d(hist: Histogram, ax: MplAxes, **kwargs) -> MplAxes:
    x_edges = hist.axes[0].edges
    y_edges = hist.axes[1].edges

    mesh = ax.pcolormesh(x_edges, y_edges, hist.values.T, **kwargs)
    plt.colorbar(mesh, ax=ax)

    if hist.axes[0].label:
        ax.set_xlabel(hist.axes[0].label)
    if hist.axes[1].label:
        ax.set_ylabel(hist.axes[1].label)
    if hist.title:
        ax.set_title(hist.title)
    return ax
