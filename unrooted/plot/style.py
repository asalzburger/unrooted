from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Literal


class LineStyle:
    """Named constants for matplotlib line-style strings."""

    SOLID = "-"
    DASHED = "--"
    DOTTED = ":"
    DASHDOT = "-."


@dataclass
class HistogramStyle:
    """Visual style for a single 1D histogram.

    All ``*_color`` fields accept matplotlib-style color spec (named string,
    hex, or RGBA tuple).  ``None`` means "inherit the automatic cycle color".
    ``*_alpha`` fields are applied on top of whatever alpha is encoded in the
    color itself.

    Prefer the named constructors over building this manually:

    * :meth:`as_hist`        — step fill + error bars (count histogram default)
    * :meth:`as_line`        — step line only, no fill, no errors
    * :meth:`as_markers`     — markers at bin centres + error bars
    * :meth:`as_efficiency`  — markers + error bars + spread band
    * :meth:`as_profile`     — line + spread band (TProfile)
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

    # --- Error display (bin ± sqrt(variance)) ---
    error_display: Literal["bar", "band"] | None = "bar"
    error_color: str | tuple[float, ...] | None = None  # None → same as line
    error_alpha: float = 0.4                            # opacity for "band"
    error_capsize: float = 2.0                          # cap size for "bar"

    # --- Spread display (Histogram.spread_min / spread_max) ---
    spread_display: Literal["bar", "band"] | None = None
    spread_color: str | tuple[float, ...] | None = None # None → same as line
    spread_alpha: float = 0.15
    spread_capsize: float = 2.0

    # ------------------------------------------------------------------
    # Named constructors
    # ------------------------------------------------------------------

    @classmethod
    def as_hist(cls, **overrides) -> HistogramStyle:
        """Step-function histogram with fill and error bars.

        The typical appearance for a count histogram: filled step area at low
        opacity with error bars at each bin centre.
        """
        return cls(**{
            "line_style": LineStyle.SOLID,
            "fill_alpha": 0.15,
            "error_display": "bar",
            "spread_display": None,
            **overrides,
        })

    @classmethod
    def as_line(cls, **overrides) -> HistogramStyle:
        """Step line only — no fill, no markers, no error display."""
        return cls(**{
            "line_style": LineStyle.SOLID,
            "fill_alpha": None,
            "marker": None,
            "error_display": None,
            "spread_display": None,
            **overrides,
        })

    @classmethod
    def as_markers(cls, **overrides) -> HistogramStyle:
        """Markers at bin centres with error bars, no step line."""
        return cls(**{
            "line_style": None,
            "marker": "o",
            "fill_alpha": None,
            "error_display": "bar",
            "spread_display": None,
            **overrides,
        })

    @classmethod
    def as_efficiency(cls, **overrides) -> HistogramStyle:
        """Markers + error bars + spread band — suited for efficiency histograms."""
        return cls(**{
            "line_style": None,
            "marker": "o",
            "fill_alpha": None,
            "error_display": "bar",
            "spread_display": "band",
            "spread_alpha": 0.15,
            **overrides,
        })

    @classmethod
    def as_profile(cls, **overrides) -> HistogramStyle:
        """Step line + spread band — suited for TProfile histograms."""
        return cls(**{
            "line_style": LineStyle.SOLID,
            "fill_alpha": None,
            "marker": None,
            "error_display": "bar",
            "spread_display": "band",
            "spread_alpha": 0.15,
            **overrides,
        })

    # ------------------------------------------------------------------
    # Copy helpers
    # ------------------------------------------------------------------

    def with_color(
        self,
        color: str | tuple[float, ...],
        *,
        override_explicit: bool = False,
    ) -> HistogramStyle:
        """Return a copy with *color* applied to all colour fields that are ``None``.

        By default only fields that are currently ``None`` are set, so any
        explicitly chosen colours are preserved.  Pass
        ``override_explicit=True`` to replace *all* colour fields regardless.

        Args:
            color:            Matplotlib color spec (hex string, named color,
                              or RGBA tuple).
            override_explicit: When ``True``, overwrite every ``*_color``
                              field unconditionally.
        """
        color_fields = (
            "line_color",
            "marker_color",
            "fill_color",
            "error_color",
            "spread_color",
        )
        updates: dict[str, str | tuple[float, ...]] = {}
        for f in color_fields:
            if override_explicit or getattr(self, f) is None:
                updates[f] = color
        return dataclasses.replace(self, **updates)
