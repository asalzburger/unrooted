from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class HistogramStyle:
    """Visual style for a single 1D histogram.

    All ``*_color`` fields accept matplotlib-style color spec (named string,
    hex, or RGBA tuple).  ``None`` means "inherit the automatic cycle color".
    ``*_alpha`` fields are applied on top of whatever alpha is encoded in the
    color itself.
    """

    # --- Line (step function) ---
    line_color: str | tuple[float, ...] | None = None  # None → auto cycle
    line_alpha: float = 1.0
    line_style: str | None = "-"    # None → no line; "-", "--", ":", "-."
    line_width: float = 1.5

    # --- Marker (at bin centres) ---
    marker: str | None = None                           # None → no marker
    marker_color: str | tuple[float, ...] | None = None # None → same as line
    marker_alpha: float = 1.0
    marker_size: float = 5.0

    # --- Fill (under the step function) ---
    fill_color: str | tuple[float, ...] | None = None   # None → same as line
    fill_alpha: float | None = None                     # None → no fill
    fill_hatch: str | None = None                       # e.g. "/", "x", "."

    # --- Error display (bin ± sqrt(variance)) — "band" only for 1D ---
    error_display: Literal["bar", "band"] | None = "bar"
    error_color: str | tuple[float, ...] | None = None  # None → same as line
    error_alpha: float = 0.4                            # opacity for "band"
    error_capsize: float = 2.0                          # cap size for "bar"

    # --- Spread display (Histogram.spread_min / spread_max) — "band" only 1D ---
    spread_display: Literal["bar", "band"] | None = None
    spread_color: str | tuple[float, ...] | None = None # None → same as line
    spread_alpha: float = 0.15
    spread_capsize: float = 2.0
