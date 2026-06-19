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
