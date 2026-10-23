"""Shared numerical contract for graphical histogram stacks."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from unrooted.core.histogram import Histogram
from unrooted.plot.style import HistogramStyle


@dataclass
class StackData:
    edges: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    errors: np.ndarray
    styles: list[HistogramStyle]


def prepare_stack(
    hists: list[Histogram],
    labels: list[str] | None,
    styles: list[HistogramStyle] | None,
    colors: list[str],
    uncertainty: bool,
) -> StackData:
    """Validate before drawing; accumulate copies in float64 without integer wrap."""
    if not hists:
        raise ValueError("hists must not be empty")
    if not isinstance(uncertainty, bool):
        raise ValueError("uncertainty must be a bool")
    if labels is not None and len(labels) != len(hists):
        raise ValueError("labels must have the same length as hists")
    if styles is not None and len(styles) != len(hists):
        raise ValueError("styles must have the same length as hists")
    for hist in hists:
        hist.validate()
        if hist.ndim != 1:
            raise ValueError("stack only supports 1D histograms")
        hists[0].require_compatible_binning(hist)
        if np.any(hist.values < 0):
            raise ValueError("stack requires nonnegative bin values")
        if hist.spread_min is not None:
            raise ValueError(
                "stack requires additive counts or yields, not profile/efficiency "
                "histograms with spread bounds"
            )

    resolved = []
    for i in range(len(hists)):
        style = styles[i] if styles is not None else HistogramStyle.as_stack()
        if style.line_style not in (None, "-", "--", ":", "-."):
            raise ValueError(
                "Unsupported stack line_style; use '-', '--', ':', or '-.'"
            )
        if style.fill_hatch not in (None, "", "/", "\\", "x", "-", "|", "+", "."):
            raise ValueError(
                "Unsupported stack fill_hatch; use /, \\, x, -, |, +, or ."
            )
        color = (
            style.line_color
            if style.line_color is not None
            else colors[i % len(colors)]
        )
        resolved.append(style.with_color(color))

    with np.errstate(over="ignore", invalid="ignore"):
        values = np.array([hist.values for hist in hists], dtype=float)
        upper = np.cumsum(values, axis=0)
        variances = np.sum(
            np.array([hist.variances for hist in hists], dtype=float), axis=0
        )
    if np.any(np.isinf(upper)) or np.any(np.isinf(variances)):
        raise ValueError("Stack values or summed variances exceed float64 range")
    # An unknown contribution makes the entire bin's composition unknown.
    upper[:, np.any(np.isnan(values), axis=0)] = np.nan
    lower = np.vstack([np.zeros_like(upper[0]), upper[:-1]])
    lower[:, np.isnan(upper[-1])] = np.nan
    return StackData(
        edges=hists[0].axes[0].edges.copy(),
        lower=lower,
        upper=upper,
        errors=np.sqrt(variances),
        styles=resolved,
    )


def finite_runs(*arrays: np.ndarray):
    """Yield slices that never connect a filled polygon across missing bins."""
    valid = np.logical_and.reduce([np.isfinite(array) for array in arrays])
    boundaries = np.flatnonzero(np.diff(np.r_[False, valid, False]))
    for start, stop in boundaries.reshape(-1, 2):
        yield slice(start, stop)
