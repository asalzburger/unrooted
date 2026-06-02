# Loading boost-histogram Data

`unrooted` can convert
[`boost-histogram`](https://boost-histogram.readthedocs.io/) objects directly
into the common `Histogram` representation — no ROOT files involved.
This is the recommended path when your analysis pipeline already produces
`boost_histogram.Histogram` objects (e.g. from
[coffea](https://coffeateam.github.io/coffea/) or hand-filled histograms).

---

## Profile histograms (Mean storage)

A `boost_histogram.Histogram` with `Mean` storage is treated as a profile
histogram, exactly like a ROOT `TProfile`.

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

Pass a pair of `Double`-storage histograms (accepted, total) to
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
| `eff.spread_min` | eff − σ, clamped to 0 |
| `eff.spread_max` | eff + σ, clamped to 1 |

Bins where total = 0 carry `nan`.  The function validates that both histograms
have the same shape and matching bin edges, raising `ValueError` otherwise.

```python
from unrooted.plot.mpl import plot
from unrooted.plot.style import HistogramStyle

plot(eff, style=HistogramStyle.as_efficiency().with_color(ss.colors[1]))
```

![boost-histogram efficiency](../assets/examples/mpl_boost_efficiency.png)

---

## Scalar and Weight storage

`load()` handles all scalar storage types (`Double`, `Int64`) and `Weight`
storage in addition to `Mean`:

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
| `Double` / `Int64` | bin count | = values (Poisson) | `None` |
| `Weight` | Σw per bin | Σw² per bin | `None` |
| `Mean` | per-bin mean | SE² per bin | mean ± σ_y |

---

## Variable and Regular axes

Both axis types are supported; edges are extracted via the `.edges` property:

```python
# Variable bin widths
ax = bh.axis.Variable([-4, -3, -2, -1, 0, 1, 2, 3, 4], metadata="η")

# Uniform bins
ax = bh.axis.Regular(40, -4, 4, metadata="η")
```

The `metadata` field of each axis becomes the `Axis.label` string in the
returned `Histogram`.

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
