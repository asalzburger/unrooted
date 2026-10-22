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
| `spread_min` | `ndarray \| None` | Optional lower spread bound; meaning depends on the reader |
| `spread_max` | `ndarray \| None` | Optional upper spread bound; meaning depends on the reader |

### Validation and missing data

Construction raises `ValueError` for invalid data. An axis must have at least
two finite, strictly increasing, one-dimensional numeric edges; edges are
converted to float64. A histogram needs at least one axis, and `values` and
`variances` must have shape `(axis_0.n_bins, axis_1.n_bins, ...)`. Variances
must be nonnegative. Boolean, complex, string, and object arrays are rejected.

Values may be negative, for example after a weighted fill. Histogram arrays
may contain NaN to mark missing data or uncertainty; infinity is rejected.
Spread bounds must be supplied together, match the values' shape, have paired
NaN positions, be ordered, and enclose the central values wherever both are
defined. Sparse profiles may therefore have a finite value and NaN spread.

`ScatterData(x, y)` follows the same numeric rules and requires flat arrays of
equal length. Empty arrays and NaN gaps are allowed.

Tree readers also attach scatter provenance: `source_points` is the selected
flattened count, `sample_seed` records an explicitly requested random sampler,
and the `sampled` property indicates whether fewer pairs were retained.
Manually created objects may leave those optional fields unset. See
[scatter limits and sampling](loading-root.md#scatter-limits-and-sampling).

### Ownership and mutation

Core constructors use `np.asarray`; they borrow arrays when conversion is
unnecessary. Mutating an input array can change the object, and axis objects
are shared. Use `.copy()` on your inputs when you need isolation. Readers
return independent snapshots of their source data. Histogram values,
variances, and flow arrays from readers do not share storage with each other.

Objects remain mutable. Call `h.validate()` or `scatter.validate()` after
editing their arrays or axes. Public plotting functions validate again before
drawing. Validation does not recompute variances, spread, or flow contents
after a value is changed; updating related quantities remains your responsibility.

### Flow bins

`values` and `variances` exclude flow bins. If present, `overflow` is a full
values array of shape `(n_0 + 2, n_1 + 2, ...)`: index `0` on each axis is
underflow, indices `1:-1` are ordinary bins, and the final index is overflow.
This includes multidimensional corner flows. It stores contents, not flow
variances, and plotting uses only `values`.

ROOT readers populate both flow slots per axis. Boost readers pad disabled
flow slots with NaN, distinguishing unavailable data from an observed zero.
Branch readers set `overflow=None` and omit out-of-range observations.
Flow arrays are snapshots and do not synchronize with later edits to `values`.

### Profile histograms

When `load_branch()` returns a profile histogram, `spread_min` and
`spread_max` hold the per-bin extreme values of the profiled quantity.
Empty bins have `np.nan` in both spread arrays.

For `N > 0` observations, branch-profile `variances` use
`sum((y - mean(y))**2) / N²`, retaining the population convention. Empty bins
have value and variance `0`; single-entry bins have the observed value and
variance `0`. The spread bounds distinguish an empty bin from a populated
bin whose values and variance happen to be zero.

Profiles loaded from ROOT `TProfile` or boost-histogram `Mean` storage instead
carry mean ± standard deviation in these fields. Efficiency readers use them
for interval bounds. These bands have different interpretations; consult the
[ROOT](loading-root.md) and [boost-histogram](loading-boost.md) loading guides
when comparing them.

Boost `Mean` profiles retain sample-corrected variance
`sum((y - mean(y))**2) / (N * (N - 1))` for `N >= 2`. Matching profile means
therefore do not imply matching error bars. ROOT `TProfile` variances are
read through uproot.

```python
from unrooted.io.root import load_branch

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
