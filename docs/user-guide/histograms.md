# Histograms & Axes

## The `Histogram` dataclass

`Histogram` is the central data structure.  It is a plain Python dataclass —
no magic, no hidden state — so you can always work with its arrays directly.

```python
from unrooted.core.histogram import Histogram
from unrooted.core.axis import Axis
import numpy as np

edges = np.linspace(0, 10, 11)   # 10 bins
values = np.array([1,3,5,8,10,9,7,4,2,1], dtype=float)

h = Histogram(
    axes=[Axis(edges=edges, label="x [cm]")],
    values=values,
    variances=values.copy(),   # Poisson: Var(N) = N
    name="my_hist",
)
```

### Key attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `axes` | `list[Axis]` | One per dimension |
| `values` | `ndarray` | Bin contents |
| `variances` | `ndarray` | Per-bin variance |
| `errors` | `ndarray` (property) | `sqrt(variances)` |
| `ndim` | `int` (property) | Number of dimensions |
| `name` | `str` | Optional identifier |
| `title` | `str` | Optional longer title |
| `overflow` | `ndarray \| None` | Values with flow bins |
| `spread_min` | `ndarray \| None` | Per-bin min (profile only) |
| `spread_max` | `ndarray \| None` | Per-bin max (profile only) |

### Profile histograms

When `load_branch()` returns a profile histogram, `spread_min` and
`spread_max` hold the per-bin extreme values of the profiled quantity.
Empty bins have `np.nan` in both spread arrays.

```python
hp = load_branch("data.root", "tree", "x", "y")

import numpy as np
populated = ~np.isnan(hp.spread_min)
print("populated bins:", populated.sum())
print("mean range:", hp.values[populated].min(), "…", hp.values[populated].max())
```

---

## The `Axis` dataclass

Each `Axis` stores the bin edges for one dimension.

```python
from unrooted.core.axis import Axis
import numpy as np

ax = Axis(edges=np.linspace(-3, 3, 61), label="η")

ax.n_bins    # 60
ax.centers   # array of 60 bin-centre coordinates
ax.widths    # array of 60 bin widths (uniform here: 0.1 each)
```

### Convenience aliases

```python
from unrooted.core.histogram import Histogram1D, Histogram2D
# Both are just Histogram — provided for type-annotation clarity.
```
