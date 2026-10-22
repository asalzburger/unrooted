from __future__ import annotations

from pathlib import Path

import numpy as np

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram
from unrooted.plot.style_set import StyleSet


def generate_stylesheet(
    target: str,
    output: Path | str | None = None,
) -> Path:
    """Render a style-palette preview PNG to a user-writable destination.

    Produces a single plot with four overlaid synthetic Gaussian histograms —
    one per style slot — so the color, line, marker, fill, and error-bar
    choices can be reviewed at a glance.

    Args:
        target: Resource target name, e.g. ``"odd"`` or ``"sd"``.
        output: Destination path. Defaults to ``{target}_stylesheet.png`` in
                the current working directory. The parent directory must exist.

    Returns:
        The output path, retaining a relative path when one was supplied.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from unrooted.plot.mpl.overlay import overlay

    style_set = StyleSet.load(target)

    hists = [_gaussian_histogram(i) for i in range(4)]
    labels = [
        f"Style {i + 1}  —  {style_set.colors[i]}" for i in range(4)
    ]
    styles = [style_set[i] for i in range(4)]

    fig, ax = plt.subplots(figsize=(10, 5))
    overlay(hists, ax=ax, labels=labels, styles=styles)
    ax.set_title(f"{target.upper()} style palette", fontsize=13, fontweight="bold")

    out = Path(output) if output is not None else Path(f"{target}_stylesheet.png")
    try:
        fig.savefig(out, dpi=150, bbox_inches="tight")
    finally:
        plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _gaussian_histogram(slot: int, n_bins: int = 60) -> Histogram:
    """Return a reproducible synthetic 1-D Gaussian histogram for *slot* 0-3."""
    rng = np.random.default_rng(slot * 17 + 3)
    center = -1.5 + slot * 1.0
    data = rng.normal(center, 0.6, 400)
    lo, hi = -4.0, 4.0
    edges = np.linspace(lo, hi, n_bins + 1)
    values, _ = np.histogram(data, bins=edges)
    values = values.astype(float)
    return Histogram(
        axes=[Axis(edges=edges, label="x")],
        values=values,
        variances=values.copy(),
        name=f"style_{slot}",
    )
