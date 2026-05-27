from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from unrooted.plot.style import HistogramStyle

_RESOURCES = Path(__file__).parent.parent.parent / "resources"


@dataclass
class StyleTemplate:
    """Shape-related style properties for one histogram slot in a :class:`StyleSet`.

    A ``StyleTemplate`` captures everything *except* colour: line style,
    line width, marker shape/size, fill opacity, and error/spread display mode.
    Combine with a palette color via :meth:`StyleSet.load` to produce a full
    :class:`HistogramStyle`.

    Args:
        line_style:     Matplotlib line-style string or ``None`` for no line.
        line_width:     Stroke width in points.
        marker:         Matplotlib marker code or ``None`` for no marker.
        marker_size:    Marker size in points.
        fill_alpha:     Fill opacity under the step function; ``None`` → no fill.
        error_display:  ``"bar"``, ``"band"``, or ``None``.
        spread_display: ``"bar"``, ``"band"``, or ``None``.
    """

    line_style: str | None = "-"
    line_width: float = 1.5
    marker: str | None = None
    marker_size: float = 5.0
    fill_alpha: float | None = None
    error_display: Literal["bar", "band"] | None = "bar"
    spread_display: Literal["bar", "band"] | None = None


DEFAULT_STYLE_TEMPLATES: list[StyleTemplate] = [
    StyleTemplate(line_style="-",  marker="o", fill_alpha=0.15, error_display="bar"),
    StyleTemplate(line_style="-",  marker="s", fill_alpha=0.15, error_display="bar"),
    StyleTemplate(line_style="--", marker="^", fill_alpha=None, error_display="bar"),
    StyleTemplate(line_style="--", marker="D", fill_alpha=None, error_display="bar"),
]


@dataclass
class StyleSet:
    """A coordinated set of histogram styles tied to a resource target.

    Each style combines a color from the target's ``colors.json`` palette with
    shape properties from a :class:`StyleTemplate`.  Up to four styles are
    available by default; the index wraps cyclically so you never run out when
    overlaying more than four histograms.

    Use :meth:`load` to build a ``StyleSet`` from a resource target name.
    Index with ``style_set[i]``.
    """

    name: str
    description: str
    colors: list[str]             # 4 hex strings
    styles: list[HistogramStyle]  # assembled HistogramStyle objects

    @classmethod
    def load(
        cls,
        target: str,
        *,
        templates: list[StyleTemplate] | None = None,
        show_errors: bool = True,
        show_spread: bool = False,
    ) -> StyleSet:
        """Load from ``resources/{target}/colors.json``.

        Args:
            target:      Resource target name, e.g. ``"odd"`` or ``"sd"``.
            templates:   Override the default four :data:`DEFAULT_STYLE_TEMPLATES`.
                         The list length determines how many styles are created;
                         it must match the number of colors in the palette or be
                         shorter.
            show_errors: When ``False``, sets ``error_display=None`` on every
                         style regardless of the template setting.
            show_spread: When ``True``,  sets ``spread_display="band"`` on every
                         style regardless of the template setting.

        Raises:
            FileNotFoundError: When no ``colors.json`` exists for *target*.
        """
        path = _RESOURCES / target / "colors.json"
        data: dict[str, Any] = json.loads(path.read_text())
        colors: list[str] = data["colors"]

        tmpl_list = templates if templates is not None else DEFAULT_STYLE_TEMPLATES

        styles: list[HistogramStyle] = []
        for color, tmpl in zip(colors, tmpl_list):
            error_display = tmpl.error_display if show_errors else None
            spread_display = "band" if show_spread else tmpl.spread_display
            styles.append(
                HistogramStyle(
                    line_color=color,
                    line_style=tmpl.line_style,
                    line_width=tmpl.line_width,
                    marker=tmpl.marker,
                    marker_color=color,
                    marker_size=tmpl.marker_size,
                    fill_color=color,
                    fill_alpha=tmpl.fill_alpha,
                    error_color=color,
                    error_display=error_display,
                    spread_color=color,
                    spread_display=spread_display,
                )
            )

        return cls(
            name=data["name"],
            description=data["description"],
            colors=colors,
            styles=styles,
        )

    def __len__(self) -> int:
        return len(self.styles)

    def __getitem__(self, i: int) -> HistogramStyle:
        return self.styles[i % len(self.styles)]
