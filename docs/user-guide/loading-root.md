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

Direct `TEfficiency` loading is unsupported. Use
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
| `eff.spread_min` | Lower Wilson interval bound |
| `eff.spread_max` | Upper Wilson interval bound |

The default confidence level is `0.6826894921370859` (68.27%, equivalent to
the central Gaussian ±1σ probability). Pass `confidence_level=0.95` for 95%
intervals. The method is the [Wilson score interval without continuity
correction](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html).
It replaces the previous clamped Gaussian spread; the binomial variance field
is unchanged. No additional statistical dependency is required.

For `N > 0`, `p = passed/N`, and the standard-normal quantile `z` at
`(1 + confidence_level)/2`, the bounds are

```text
center = (p + z²/(2N)) / (1 + z²/N)
radius = z * sqrt(p*(1-p)/N + z²/(4N²)) / (1 + z²/N)
bounds = center ± radius
```

Bounds lie in `[0, 1]` and retain nonzero width at zero and full acceptance.
At the default confidence level, `0/4` has bounds `[0, 0.2]`, `2/4` has bounds
approximately `[0.276393, 0.723607]`, and `4/4` has bounds `[0.8, 1]`.
Bins where total = 0 carry `nan` for all four arrays; no inference is made
from an empty bin.

`errors = sqrt(variances)` still describes the Gaussian binomial standard
error and is zero at the endpoints. To show Wilson bounds, enable
`spread_display`; changing the confidence level affects only the bounds.

```python
from unrooted.plot.mpl import plot
from unrooted.plot.style import HistogramStyle

style = HistogramStyle(
    line_color="#1A4F8A",
    marker="o",
    error_display=None,
    spread_display="band",  # shaded Wilson interval
)
plot(eff, style=style)
```

Inputs must be one-dimensional TH1 count histograms with exactly identical
edges. Counts must be finite, nonnegative integers, with passed ≤ total in
every bin. Weighted and fractional efficiencies are unsupported. ROOT
variances must match counts (relative tolerance `1e-12`); a stored `Sumw2`
array with unit-weight Poisson variances is accepted. ROOT cannot always
establish the history of weights from aggregated counts, so callers must
supply unweighted event counts. Profiles and TH2 inputs are rejected.
Invalid data or a confidence level outside `(0, 1)` raises `ValueError`.
Flow bins are excluded from the efficiency calculation.

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

### Entry selection

Both `load_branch()` and `load_scatter()` accept a half-open tree-entry slice:

```python
from unrooted.io.root import load_branch, load_scatter

h = load_branch("data.root", "tree", "x", entry_start=1000, entry_stop=2000)
points = load_scatter("data.root", "tree", "x", "y",
                      entry_start=1000, entry_stop=2000)
```

`entry_start` defaults to `0`; `entry_stop=None` reads through the end of the
tree. Bounds must be nonnegative integers with stop ≥ start; bounds beyond
the tree's length are clipped. Selection happens before broadcasting and
flattening, so the bounds count events, not flattened points. All elements
of a selected jagged event are included. Automatic histogram ranges use only
the selected x values, before broadcasting. An empty selection needs an
explicit histogram range; it returns an empty scatter without a range.

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

### Chunking and memory

Branch readers process at most `step_size=100_000` tree entries per chunk.
Set a smaller positive integer to reduce temporary array sizes. Entry counts
are measured before broadcasting/flattening: one jagged event may contain
many points, and ROOT baskets also contribute memory. `step_size` is an
entry limit, not a hard limit on process RAM.

Count histograms accumulate one chunk at a time. Profiles use three passes
over the selection: extrema/counts, sums relative to a common per-bin origin,
and centered squared deviations. The extra I/O retains the population
estimator and large-offset stability while keeping working arrays bounded
by the chunk and bin count. Automatic range detection adds an x-only pass;
provide `range=(lo, hi)` to avoid that scan. Interpreted arrays are not cached
between passes.

For count/profile output, result memory depends on the number of bins.
Scatter output without `max_points` retains every selected pair, so its result
memory still grows with the selection. Use an explicit limit when that result
must be bounded.

### Scatter limits and sampling

```python
from unrooted.io.root import load_scatter

# A guard: raise ValueError if the selection exceeds 100,000 flattened pairs.
points = load_scatter("data.root", "tree", "x", "y", max_points=100_000)

# An explicit uniform sample without replacement, with a reproducible seed.
sample = load_scatter("data.root", "tree", "x", "y",
                      max_points=100_000, sampling="random", seed=71,
                      step_size=100_000)
print(len(sample.x), sample.source_points, sample.sampled, sample.sample_seed)
```

The default `max_points=None` returns all pairs. Setting a limit defaults to
`sampling="error"`; it never silently truncates. `sampling="random"` requires
a positive limit and uses seed `0` by default. A limit at or above the selected
pair count returns all pairs.

Sampling is uniform over flattened `(x, y)` pairs, including NaN gaps, rather
than over events. High-multiplicity events contribute more pairs. Coordinates
stay paired, selected points retain their original order, and the same
input/selection, seed, and software versions give the same sample across
chunk sizes. `source_points` records the selected flattened count;
`sampled` is true only when fewer pairs were retained. `sample_seed` records
the requested random seed. Working memory is proportional to a chunk plus
the retained limit; the complete source selection is still scanned.

### Reference workload measurements

The Stage 5 target is 10 million flattened observations per histogram/profile,
under 1 GiB peak process RAM and 30 seconds per load on the local reference
workload. Scatter sampling is explicitly requested, with 100,000 retained
points in the reference run. These targets are measured on synthetic local
ROOT data, rather than a universal limit for every file or machine.

On arm64 macOS / Python 3.14.6, using 100 bins, an explicit range, and three
fresh worker processes per case:

| 10-million-observation case | Whole-branch median load | Chunked median load | Whole-branch peak RAM | Chunked peak RAM |
| --- | --- | --- | --- | --- |
| Scalar count | 0.468 s | 0.534 s | 262.5 MiB | 74.0 MiB |
| Jagged count | 0.484 s | 0.490 s | 281.1 MiB | 106.9 MiB |
| Scalar profile | 0.834 s | 2.352 s | 820.0 MiB | 104.7 MiB |
| Jagged profile | 0.865 s | 2.315 s | 877.4 MiB | 238.3 MiB |

The jagged fixture has 10 observations per event. Profiles trade additional
passes for lower memory while staying within the agreed time budget.
Sampling 100,000 pairs from 10 million took median 0.52–0.61 s and at most
251.4 MiB during loading; self-contained Plotly HTML was 7.0 MiB. Rendering
raised peak process RAM to at most 318.7 MiB for that sampled workload.

Reproduce from the source checkout (with development/Plotly dependencies):

```bash
uv run python -I benchmarks/root_loading.py \
  --workdir /tmp/unrooted-benchmark --observations 10000000 --repeat 3 \
  --step-size 100000 --max-points 100000 --render \
  --report /tmp/unrooted-benchmark/report.json
```

Add `--auto-range` to include the preliminary range scan. The benchmark
generates seeded scalar/jagged fixtures and runs each load/export in a fresh
subprocess. Reports record dependency versions, input and reader hashes,
load/render time, result/output size, and peak RSS. Fixture generation is
excluded; filesystem caches are not cleared. Peak values include interpreter
and library memory. Raw before/after reports are in `benchmarks/results/`.
