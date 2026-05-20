from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import numpy as np
import uproot

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram


def load(path: str | Path, key: str) -> Histogram:
    """Load a ROOT histogram object as a :class:`~unrooted.core.Histogram`.

    Supports ``TH1``, ``TH2``, and ``TProfile`` objects.  Bin values,
    variances, overflow, and axis labels are all extracted automatically.

    Args:
        path: Path to the ``.root`` file.
        key:  Histogram key inside the file, e.g. ``"hx"`` or ``"hx;1"``.
              The cycle number (``";1"``) is stripped from the returned
              histogram name.

    Returns:
        A :class:`~unrooted.core.Histogram` with ``values``, ``variances``,
        ``overflow``, and one :class:`~unrooted.core.Axis` per dimension.

    Raises:
        KeyError: If *key* is not found in the file.
    """
    with cast(Any, uproot.open(path)) as f:
        obj: Any = f[key]
        values = np.asarray(obj.values(flow=False))
        variances = np.asarray(obj.variances(flow=False))
        overflow = np.asarray(obj.values(flow=True))
        axes = [
            Axis(
                edges=np.asarray(ax.edges()),
                label=ax.member("fTitle") or "",
            )
            for ax in obj.axes
        ]
        name = key.split(";")[0]
        return Histogram(
            axes=axes,
            values=values,
            variances=variances,
            name=name,
            overflow=overflow,
        )
