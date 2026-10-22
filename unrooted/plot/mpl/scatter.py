from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.axes import Axes as MplAxes

from unrooted.core.scatter import ScatterData
from unrooted.plot.style import HistogramStyle


def plot(
    scatter: ScatterData,
    ax: MplAxes | None = None,
    style: HistogramStyle | None = None,
    label: str | None = None,
    set_axis_labels: bool = True,
) -> MplAxes:
    """Render a :class:`~unrooted.core.scatter.ScatterData` onto *ax*.

    Args:
        scatter:         The point cloud to render.
        ax:              Matplotlib axes; created if ``None``.
        style:           Visual style; defaults to
                         :meth:`~unrooted.plot.style.HistogramStyle.as_scatter`.
        label:           Legend label for this dataset.
        set_axis_labels: When ``True`` (default), write *x_label* / *y_label*
                         and *title* onto the axes.
    """
    scatter.validate()
    if ax is None:
        _, ax = plt.subplots()
    if style is None:
        style = HistogramStyle.as_scatter()

    if style.marker_color is not None:
        color: str | tuple[float, ...] = style.marker_color
    else:
        color = ax._get_lines.get_next_color()  # type: ignore[attr-defined]

    ax.plot(
        scatter.x,
        scatter.y,
        marker=style.marker or ".",
        linestyle="none",
        color=color,
        alpha=style.marker_alpha,
        markersize=style.marker_size,
        label=label,
    )

    if set_axis_labels:
        if scatter.x_label:
            ax.set_xlabel(scatter.x_label)
        if scatter.y_label:
            ax.set_ylabel(scatter.y_label)
        if scatter.title:
            ax.set_title(scatter.title)

    return ax


def overlay(
    scatters: list[ScatterData],
    ax: MplAxes | None = None,
    labels: list[str] | None = None,
    styles: list[HistogramStyle] | None = None,
) -> MplAxes:
    """Overlay point clouds, using the first dataset's axis labels and title.

    Args:
        scatters: Nonempty list of point clouds.
        ax: Existing axes, or None to create a figure.
        labels: Optional legend labels, one per dataset.
        styles: Optional styles, one per dataset; defaults to scatter markers.
    """
    if not scatters:
        raise ValueError("scatters must not be empty")
    if labels is not None and len(labels) != len(scatters):
        raise ValueError("labels must have the same length as scatters")
    if styles is not None and len(styles) != len(scatters):
        raise ValueError("styles must have the same length as scatters")
    for scatter in scatters:
        scatter.validate()
    for i, scatter in enumerate(scatters):
        ax = plot(
            scatter,
            ax=ax,
            style=styles[i] if styles is not None else None,
            label=labels[i] if labels is not None else None,
            set_axis_labels=i == 0,
        )
    assert ax is not None
    if labels is not None:
        ax.legend()
    return ax
