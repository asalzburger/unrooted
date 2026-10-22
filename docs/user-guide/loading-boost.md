# Loading boost-histogram Data

`unrooted` can convert
[`boost-histogram`](https://boost-histogram.readthedocs.io/) objects directly
into the common `Histogram` representation — no ROOT files involved.
This is the recommended path when your analysis pipeline already produces
`boost_histogram.Histogram` objects (e.g. from
[coffea](https://coffeateam.github.io/coffea/) or hand-filled histograms).

---

## Profile histograms (Mean storage)

A `boost_histogram.Histogram` with `Mean` storage is converted to the common
profile representation. Its sample-corrected uncertainties and spread are
described below.

```python
import pickle
from unrooted.io.boost import load

with open("histograms.pkl", "rb") as f:
    data = pickle.load(f)          # dict of bh.Histogram objects

prof = load(data["nMeasurements_vs_eta"], name="nMeasurements_vs_eta")
```

The `Mean` storage provides three fields per bin; `load()` derives the standard
quantities from them:

| `bh` field | Meaning | Maps to |
|---|---|---|
| `count` | number of fills | — |
| `value` | per-bin mean | `h.values` |
| `_sum_of_deltas_squared` | Σ(x − mean)² | → SE² and σ_y |

| Attribute | Content |
|-----------|---------|
| `h.values` | Per-bin mean |
| `h.variances` | Per-bin SE² = Σ(x−mean)² / (N(N−1)) |
| `h.errors` | √SE² — standard error of the mean |
| `h.spread_min` | mean − σ_y  (std-dev of individual measurements) |
| `h.spread_max` | mean + σ_y |
| `h.overflow` | mean values including under/overflow bins |

σ_y = √(Σ(x−mean)² / (N−1)).  Bins with count = 0 carry `nan` for the spread
fields; bins with count = 1 carry σ_y = 0.

The SE² formula applies for `N >= 2`. This reader retains variance `0` for
bins with zero or one observation; empty bins have value `0`.

Unlike [profiles computed from branches](loading-root.md#profile-histogram-two-branches),
which retain population SE² = Σ(x−mean)² / N², `Mean` storage uses the sample
correction. For observations `[1, 3]`, both readers return mean `2`, but the
branch variance is `0.5` and the boost variance is `1`. Branch spread records
observed extrema; boost spread is mean ± sample standard deviation.

Axis `metadata` strings (e.g. `bh.axis.Variable([...], metadata="#eta")`)
become axis labels automatically.

```python
from unrooted.plot.mpl import plot
from unrooted.plot.style import HistogramStyle
from unrooted.plot.style_set import StyleSet

ss = StyleSet.load("odd")
plot(prof, style=HistogramStyle.as_profile().with_color(ss.colors[0]))
```

![boost-histogram profile](../assets/examples/mpl_boost_profile.png)

---

## Efficiency histograms

Pass a pair of count-storage histograms (accepted, total) to
`load_efficiency()`.  This mirrors the ROOT `load_efficiency()` API, but
accepts in-memory objects rather than file paths.

```python
from unrooted.io.boost import load_efficiency

# data["trackeff_vs_eta"] is {"accepted": bh.Histogram, "total": bh.Histogram}
eff_entry = data["trackeff_vs_eta"]
eff = load_efficiency(eff_entry["accepted"], eff_entry["total"], name="trackeff")
```

| Attribute | Content |
|-----------|---------|
| `eff.values` | Per-bin efficiency = accepted / total |
| `eff.variances` | Binomial variance = eff × (1 − eff) / total |
| `eff.spread_min` | Lower Wilson interval bound |
| `eff.spread_max` | Upper Wilson interval bound |

Both inputs must be 1D, with exactly identical edges and finite nonnegative
integer counts satisfying accepted ≤ total. Supported count storages are
`Double`, `Int64`, `Unlimited`, and `AtomicInt64`. `Weight`, `Mean`, and
`WeightedMean` are rejected, including `Weight` filled with unit weights.
Scalar inputs whose boost variance information is unknown after a weighted
fill are also rejected. Manually assigned scalar contents cannot establish
the history of weights; callers must supply unweighted counts. Fractional or
weighted efficiencies are unsupported.

Bounds use the Wilson score interval without continuity correction, with
`confidence_level=0.6826894921370859` (68.27%) by default; pass
`confidence_level=0.95` for 95% intervals. This replaces the previous clamped
Gaussian spread and retains `p*(1-p)/N` in `variances`. Zero-total bins carry
NaN in all four arrays; flow bins are excluded. Invalid inputs or confidence
levels outside `(0, 1)` raise `ValueError`. The [ROOT efficiency guide](loading-root.md#efficiency-histograms)
gives the formula, endpoint examples, and the difference between Wilson
bounds and `errors`.

```python
from unrooted.plot.mpl import plot
from unrooted.plot.style import HistogramStyle

plot(eff, style=HistogramStyle.as_efficiency().with_color(ss.colors[1]))
```

![boost-histogram efficiency](../assets/examples/mpl_boost_efficiency.png)

---

## Scalar and Weight storage

`load()` supports the scalar storages `Double`, `Int64`, `Unlimited`, and
`AtomicInt64`, plus `Weight` and `Mean`. `WeightedMean` is explicitly
unsupported; its weighted profile uncertainty is not yet defined here.
Other storage types raise `ValueError`.

=== "Double / Int64 (count histogram)"

    ```python
    import boost_histogram as bh
    from unrooted.io.boost import load

    h = bh.Histogram(bh.axis.Regular(50, -5, 5))
    h.fill(data)

    hist = load(h, name="x_dist")
    # hist.variances == hist.values  (Poisson assumption)
    ```

=== "Weight storage"

    ```python
    h = bh.Histogram(bh.axis.Regular(50, -5, 5), storage=bh.storage.Weight())
    h.fill(data, weight=weights)

    hist = load(h, name="x_weighted")
    # hist.values    → Σw  per bin
    # hist.variances → Σw² per bin
    ```

| Storage type | `h.values` | `h.variances` | `spread_min/max` |
|---|---|---|---|
| `Double` / `Int64` / `Unlimited` / `AtomicInt64` | bin count | = values (Poisson) | `None` |
| `Weight` | Σw per bin | Σw² per bin | `None` |
| `Mean` | per-bin mean | SE² per bin | mean ± σ_y |

---

## Numeric axes

`Regular`, `Variable`, and `Integer` axes are supported; edges are extracted
via the `.edges` property. Categorical (`IntCategory`, `StrCategory`) and
`Boolean` axes raise `ValueError` because the core representation does not
preserve their category semantics. Numeric axes must yield finite, strictly
increasing edges. Transformed, growing, and circular numeric axes are stored
as a static snapshot of their current edges and contents; later growth or
wrapping behavior belongs to the original boost histogram.

```python
# Variable bin widths
ax = bh.axis.Variable([-4, -3, -2, -1, 0, 1, 2, 3, 4], metadata="η")

# Uniform bins
ax = bh.axis.Regular(40, -4, 4, metadata="η")
```

The `metadata` field of each axis becomes the `Axis.label` string in the
returned `Histogram`.

All returned arrays are independent snapshots. `overflow` always includes
both flow slots per axis; disabled flow slots are padded with NaN. See the
[core data contract](histograms.md#flow-bins) for shape and mutation semantics.

---

## Multi-dimensional histograms

`load()` handles any number of axes — a 2D histogram produces a `Histogram`
with `ndim = 2` and two `Axis` objects, just like a ROOT `TH2`:

```python
h2d = bh.Histogram(
    bh.axis.Regular(40, -4, 4, metadata="η"),
    bh.axis.Regular(60, -3.14, 3.14, metadata="φ"),
)
h2d.fill(eta, phi)

hist2d = load(h2d, name="eta_phi")
# hist2d.ndim == 2
# hist2d.values.shape == (40, 60)
```
