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
