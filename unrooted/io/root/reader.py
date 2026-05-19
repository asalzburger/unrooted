from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import numpy as np
import uproot

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram


def load(path: str | Path, key: str) -> Histogram:
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
