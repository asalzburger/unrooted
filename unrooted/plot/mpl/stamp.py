from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
from matplotlib.axes import Axes as MplAxes
from matplotlib.offsetbox import AnnotationBbox, OffsetImage

_RESOURCES = Path(__file__).parent.parent.parent.parent / "resources"

_LOGO_FILES: dict[str, dict[str, str]] = {
    "sd": {
        "full": "sd/super_duper.png",
        "line": "sd/super_duper_line.png",
    },
    "odd": {
        "full": "odd/odd_tech_light.png",
        "line": "odd/odd_tech_light_line.png",
    },
}

# Axes-fraction coordinates and box alignment per location name.
# box_alignment=(bx, by): which corner of the image box is pinned to xy.
_LOC: dict[str, tuple[tuple[float, float], tuple[float, float]]] = {
    "upper right": ((0.98, 0.98), (1.0, 1.0)),
    "upper left": ((0.02, 0.98), (0.0, 1.0)),
    "lower right": ((0.98, 0.02), (1.0, 0.0)),
    "lower left": ((0.02, 0.02), (0.0, 0.0)),
}


def stamp(
    ax: MplAxes,
    logo: Literal["sd", "odd"],
    variant: Literal["full", "line"] = "full",
    loc: str = "upper right",
    zoom: float = 0.15,
    alpha: float = 1.0,
) -> None:
    """Overlay a detector logo on *ax*.

    Args:
        ax: Target matplotlib axes.
        logo: ``"sd"`` for the sample detector, ``"odd"`` for the open data detector.
        variant: ``"full"`` (default) or ``"line"`` logo style.
        loc: Corner placement — ``"upper right"``, ``"upper left"``,
            ``"lower right"``, or ``"lower left"``.
        zoom: Logo width as a fraction of the axes width (default 0.15).
            The full-resolution image is used, so the result is always crisp.
        alpha: Opacity of the logo (default 1.0).
    """
    from PIL import Image

    logo_path = _RESOURCES / _LOGO_FILES[logo][variant]
    img = np.asarray(Image.open(logo_path))

    # Convert zoom (axes-width fraction) → OffsetImage scale factor.
    # Using the full-res image avoids any downsampling artefacts.
    from matplotlib.figure import Figure

    fig = ax.get_figure()
    assert isinstance(fig, Figure)
    axes_width_px = fig.get_figwidth() * fig.dpi * ax.get_position().width
    img_zoom = axes_width_px * zoom / img.shape[1]

    xy, box_alignment = _LOC.get(loc, _LOC["upper right"])
    imagebox = OffsetImage(img, zoom=img_zoom, alpha=alpha)
    ab = AnnotationBbox(
        imagebox,
        xy,
        xycoords="axes fraction",
        frameon=False,
        box_alignment=box_alignment,
    )
    ax.add_artist(ab)
