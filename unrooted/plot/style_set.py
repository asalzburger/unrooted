from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from unrooted.plot.style import HistogramStyle

_RESOURCES = Path(__file__).parent.parent.parent / "resources"

# Per-slot visual properties applied on top of each target's colors.
# Slots vary in line style and marker so up to 4 overlaid histograms remain
# distinguishable beyond color alone.
_STYLE_TEMPLATES: list[dict[str, Any]] = [
    {
        "line_style": "-",
        "line_width": 1.5,
        "marker": "o",
        "marker_size": 5.0,
        "fill_alpha": 0.15,
        "error_display": "bar",
    },
    {
        "line_style": "-",
        "line_width": 1.5,
        "marker": "s",
        "marker_size": 5.0,
        "fill_alpha": 0.15,
        "error_display": "bar",
    },
    {
        "line_style": "--",
        "line_width": 1.5,
        "marker": "^",
        "marker_size": 5.0,
        "fill_alpha": None,
        "error_display": "bar",
    },
    {
        "line_style": "--",
        "line_width": 1.5,
        "marker": "D",
        "marker_size": 5.0,
        "fill_alpha": None,
        "error_display": "bar",
    },
]


@dataclass
class StyleSet:
    """A coordinated set of four histogram styles tied to a resource target.

    Each style in *styles* is a fully configured :class:`HistogramStyle` whose
    color is taken from the target's ``colors.json`` palette and whose line
    style, marker, and fill settings come from the shared :data:`_STYLE_TEMPLATES`.

    Use :meth:`load` to build a ``StyleSet`` from a resource target name.
    Index with ``style_set[i]`` — indices wrap cyclically so you never run out
    of styles even when overlaying more than four histograms.
    """

    name: str
    description: str
    colors: list[str]             # 4 hex strings
    styles: list[HistogramStyle]  # 4 assembled HistogramStyle objects

    @classmethod
    def load(cls, target: str) -> StyleSet:
        """Load from ``resources/{target}/colors.json``.

        Raises:
            FileNotFoundError: When no ``colors.json`` exists for *target*.
        """
        path = _RESOURCES / target / "colors.json"
        data: dict[str, Any] = json.loads(path.read_text())
        colors: list[str] = data["colors"]
        styles = [
            HistogramStyle(
                line_color=c,
                marker_color=c,
                fill_color=c,
                error_color=c,
                spread_color=c,
                **tmpl,
            )
            for c, tmpl in zip(colors, _STYLE_TEMPLATES)
        ]
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
