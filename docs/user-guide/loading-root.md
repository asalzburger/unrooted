# Loading ROOT Data

## ROOT histograms

Use `load()` to read any `TH1`, `TH2`, or `TProfile` object directly from a
ROOT file.  No ROOT installation is needed — `unrooted` uses
[uproot](https://uproot.readthedocs.io/) under the hood.

```python
from unrooted.io.root import load

h = load("analysis.root", "hx")
```

The key can include or omit the ROOT cycle number:

```python
h = load("analysis.root", "hx")    # cycle stripped automatically
h = load("analysis.root", "hx;1")  # explicit cycle – same result
```

### What gets loaded

| Attribute | Content |
|-----------|---------|
| `h.values` | Bin contents as `np.ndarray` |
| `h.variances` | Bin variances (`sumw2` if stored, else `values`) |
| `h.axes` | One `Axis` per dimension with edges and label |
| `h.overflow` | Full array including flow bins |
| `h.name` | Key string (cycle stripped) |

### TProfile

When the loaded object is a `TProfile`, `load()` additionally populates:

| Attribute | Content |
|-----------|---------|
| `h.values` | Per-bin mean of the profiled quantity |
| `h.variances` | Per-bin squared standard error of the mean (SE²) |
| `h.spread_min` | Per-bin mean − σ_y (std-dev of profiled quantity) |
| `h.spread_max` | Per-bin mean + σ_y |

σ_y is derived as √(SE² × N) from the stored SE² and bin counts.
Empty bins carry `nan` for the spread fields.

```python
hp = load("analysis.root", "profX")

# hp.values      → per-bin mean
# hp.variances   → per-bin SE² (error bars via hp.errors)
# hp.spread_min  → mean − σ_y  (spread band)
# hp.spread_max  → mean + σ_y
```

Plot with a spread band:

```python
from unrooted.plot.mpl import plot
from unrooted.plot.style import HistogramStyle

style = HistogramStyle(
    line_color="#1A4F8A",
    error_display="bar",    # SE error bars
    spread_display="band",  # σ_y shaded band
)
plot(hp, style=style)
```

---

## Efficiency histograms

ROOT's `TEfficiency` class cannot currently be read by uproot.  Use
`load_efficiency()` with a **passed** and a **total** `TH1` stored as
separate keys — a common pattern in analysis frameworks:

```python
from unrooted.io.root import load_efficiency

eff = load_efficiency("analysis.root", "h_passed", "h_total")
```

| Attribute | Content |
|-----------|---------|
| `eff.values` | Per-bin efficiency = passed / total |
| `eff.variances` | Per-bin binomial variance = eff × (1 − eff) / total |
| `eff.spread_min` | eff − σ, clamped to 0 (Gaussian ±σ CI) |
| `eff.spread_max` | eff + σ, clamped to 1 |

Bins where total = 0 carry `nan` for all fields.

```python
from unrooted.plot.mpl import plot
from unrooted.plot.style import HistogramStyle

style = HistogramStyle(
    line_color="#1A4F8A",
    marker="o",
    error_display="bar",    # ±σ error bars
    spread_display="band",  # shaded ±σ CI
)
plot(eff, style=style)
```

The function validates that the two histograms have the same number of bins
and matching edges, raising `ValueError` otherwise.

---

## TTree branches

`load_branch()` reads one or two branches from a TTree and returns a histogram.

### Count histogram (one branch)

```python
from unrooted.io.root import load_branch

h = load_branch("data.root", "tree", "x")
# → Histogram with 100 bins, range auto-detected from data
```

Options:

```python
h = load_branch("data.root", "tree", "x",
                n_bins=50,
                range=(-5.0, 5.0),
                label="x [mm]")
```

Count and profile histograms use bins `[left, right)`, with the final right
edge included in the last bin. A value exactly on an internal edge belongs to
the bin on its right. Values outside the specified range are omitted.

### Profile histogram (two branches)

Provide `y_branch` to profile `y` values against `x`-axis bins.
Each x-bin stores the mean, standard error, and min/max of the
corresponding `y` values.

```python
hp = load_branch("data.root", "tree", "x", "y")
# hp.values     → per-bin mean of y
# hp.variances  → per-bin SE² of mean
# hp.spread_min → per-bin minimum of y
# hp.spread_max → per-bin maximum of y
```

For a bin with `N > 0` observations, define
`M2 = sum((y - mean(y))**2)`. Branch profiles use the **population convention**:

```text
values    = mean(y)
variances = M2 / N²
errors    = sqrt(variances)
```

This is the population variance of the observations divided by `N`; it does
not apply the sample correction `N / (N - 1)`. For observations `[1, 3]`, the
mean is `2`, the variance of the mean is `0.5`, and the spread bounds are
`[1, 3]`. The calculation centers values within each bin before accumulating
squared deviations, avoiding cancellation from a large common offset.

| Entries in a bin | Value | Variance | Spread bounds |
| --- | --- | --- | --- |
| 0 | `0` | `0` | both `nan` |
| 1 | observed value | `0` | both equal to the observation |
| 2 or more | mean | `M2 / N²` | observed minimum and maximum |

The zero variance for a single observation preserves the existing convention;
it does not establish that the underlying distribution has no uncertainty.
An entirely empty tree can be loaded with an explicit `range=(lo, hi)`;
automatic range detection needs at least one x-value.

The [boost-histogram Mean reader](loading-boost.md#profile-histograms-mean-storage)
retains its sample-corrected variance `M2 / (N * (N - 1))` for `N >= 2` and
mean ± standard deviation spread. Those uncertainty and spread definitions
differ from branch profiles even when the means and binning agree.

### Supported branch-pair types

`load_branch()` uses `awkward.broadcast_arrays` to align the two branches,
supporting all common branch-shape combinations:

| Case | x type | y type | Behaviour |
|------|--------|--------|-----------|
| 1 | scalar | scalar | event-by-event pairing |
| 2 | scalar | `std::vector<T>` | x broadcast to every y element per event |
| 3 | scalar | `std::vector<std::vector<T>>` | x broadcast after full flattening |
| 4 | `std::vector<T>` | `std::vector<T>` (same shape) | element-by-element zip |
| 5 | `std::vector<T>` | `std::vector<std::vector<T>>` | outer lengths must match |

Scalar, `std::vector<T>`, and `std::vector<std::vector<T>>` branches all work
for count histograms too — they are fully flattened before binning.

!!! note
    Incompatible branch shapes (e.g. different outer lengths) raise a
    `ValueError` from awkward-array.
