from __future__ import annotations

from unrooted.core.histogram import Histogram
from unrooted.plot.terminal._render import MAX_BINS, render


def plot(hist: Histogram, max_lines: int = 40) -> str:
    """Render a 1D histogram as a unicode string for terminal output.

    Each bin occupies one character column and the plot height is
    ``max_lines`` rows.  Error bars and spread are intentionally omitted.

    Note:
        Requires a monospace / unicode-capable font in your terminal.
        The plot width equals the number of bins (≤ :data:`MAX_BINS`).

    Args:
        hist:      1D histogram to render.
        max_lines: Height of the plot area in terminal rows (minimum 5).

    Returns:
        A multi-line unicode string.  Pass it to ``print()`` to display.

    Raises:
        ValueError: If the histogram is not 1D or has more than
                    :data:`~unrooted.plot.terminal._render.MAX_BINS` bins.
    """
    if hist.ndim != 1:
        raise ValueError(
            f'Terminal backend only supports 1D histograms, got {hist.ndim}D'
        )
    n_bins = len(hist.axes[0].edges) - 1
    if n_bins > MAX_BINS:
        raise ValueError(
            f'Terminal backend supports at most {MAX_BINS} bins, got {n_bins}'
        )
    return render(
        values_list=[hist.values],
        edges=hist.axes[0].edges,
        max_lines=max_lines,
        title=hist.title or '',
        x_label=hist.axes[0].label or '',
    )


def overlay(
    hists: list[Histogram],
    labels: list[str] | None = None,
    max_lines: int = 40,
) -> str:
    """Overlay multiple 1D histograms and render as a unicode string.

    Cells where two or more histograms are present at the same height
    are rendered with a composite glyph (e.g. ○ + ✚ → ⊕).

    Args:
        hists:     1D histograms to overlay.  At most 4 are supported, and
                   all must have the same number of bins.
        labels:    Optional legend labels, one per histogram.
        max_lines: Height of the plot area in terminal rows (minimum 5).

    Returns:
        A multi-line unicode string.  Pass it to ``print()`` to display.

    Raises:
        ValueError: If any histogram is not 1D, the histograms have
                    different bin counts, more than 4 are supplied, or
                    ``labels`` length does not match.
    """
    if not hists:
        raise ValueError('hists must not be empty')
    if any(h.ndim != 1 for h in hists):
        raise ValueError('Terminal backend only supports 1D histograms')
    if len(hists) > 4:
        raise ValueError('Terminal backend supports at most 4 overlaid histograms')
    if labels is not None and len(labels) != len(hists):
        raise ValueError('labels must have the same length as hists')

    n_bins = len(hists[0].axes[0].edges) - 1
    if any(len(h.axes[0].edges) - 1 != n_bins for h in hists[1:]):
        raise ValueError('All histograms must have the same number of bins for overlay')
    if n_bins > MAX_BINS:
        raise ValueError(
            f'Terminal backend supports at most {MAX_BINS} bins, got {n_bins}'
        )

    return render(
        values_list=[h.values for h in hists],
        edges=hists[0].axes[0].edges,
        max_lines=max_lines,
        title=hists[0].title or '',
        x_label=hists[0].axes[0].label or '',
        labels=labels,
    )
