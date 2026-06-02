# Getting Started

## Installation

`unrooted` requires Python ≥ 3.11.

=== "pip"
    ```bash
    pip install unrooted
    ```

=== "uv"
    ```bash
    uv add unrooted
    ```

=== "from source"
    ```bash
    git clone https://github.com/asalzburger/unrooted
    cd unrooted
    uv sync
    ```

---

## The common representation layer

Regardless of how a histogram enters `unrooted`, it becomes the same
`Histogram` object:

```python
from unrooted.core.histogram import Histogram
from unrooted.core.axis import Axis
import numpy as np

h = Histogram(
    axes=[Axis(edges=np.linspace(0, 10, 11), label="x [cm]")],
    values=np.array([1, 3, 5, 8, 10, 9, 7, 4, 2, 1], dtype=float),
    variances=np.array([1, 3, 5, 8, 10, 9, 7, 4, 2, 1], dtype=float),
    name="my_hist",
)
```

All I/O functions produce a `Histogram`; all plot functions consume one.
Switching between I/O backends or plot backends requires no changes to the
code between them.

| Attribute | Meaning |
|-----------|---------|
| `h.axes` | One `Axis` per dimension — edges, label, centers, widths |
| `h.values` | Bin counts or profile means |
| `h.variances` | Per-bin variance (Poisson counts or SE²) |
| `h.errors` | `sqrt(variances)` — ready for error bars |
| `h.overflow` | Values including under/overflow bins (when loaded) |
| `h.spread_min/max` | Per-bin spread band (profile and efficiency histograms) |

---

## 1 — Load from a ROOT file

```python
from unrooted.io.root import load

h = load("data.root", "hx")

print(h.name)               # "hx"
print(h.ndim)               # 1
print(h.values.shape)       # (n_bins,)
print(h.axes[0].centers)    # bin centres as numpy array
```

See [Loading ROOT Data](user-guide/loading-root.md) for `TProfile`,
efficiency histograms, and TTree branches.

---

## 2 — Load from boost-histogram

`unrooted.io.boost` converts in-memory `boost_histogram.Histogram` objects
produced by coffea, hand-filled analysis code, or any other framework that
uses the boost-histogram API.

```python
import pickle
from unrooted.io.boost import load, load_efficiency

with open("histograms.pkl", "rb") as f:
    data = pickle.load(f)

# Regular or weighted histogram
h = load(data["counts"], name="counts")

# Profile histogram (Mean storage)
prof = load(data["profile"], name="profile")

# Efficiency from accepted / total pair
eff = load_efficiency(data["accepted"], data["total"], name="trackeff")
```

See [Loading boost-histogram Data](user-guide/loading-boost.md) for storage
type details and multi-dimensional histograms.

---

## 3 — Plot it

```python
from unrooted.plot.mpl import plot

ax = plot(h)
ax.figure.savefig("hx.png")
```

Pass a `label` to have it appear in the legend:

```python
ax = plot(h, label="x distribution")
ax.legend()
```

---

## 4 — Apply a detector style

```python
from unrooted.plot.mpl import plot
from unrooted.plot import StyleSet

ss = StyleSet.load("odd")   # or "sd"
ax = plot(h, style=ss[0])
ax.figure.savefig("hx_styled.png")
```

---

## 5 — Overlay multiple histograms

Histograms from different I/O backends can be overlaid directly — they share
the same `Histogram` type:

```python
from unrooted.io.root import load as load_root
from unrooted.io.boost import load as load_boost
from unrooted.plot.mpl import overlay
from unrooted.plot import StyleSet
import pickle

ss = StyleSet.load("odd")

h_root = load_root("data.root", "hx")
with open("histograms.pkl", "rb") as f:
    h_boost = load_boost(pickle.load(f)["hx"], name="hx_boost")

(ax, _) = overlay(
    [h_root, h_boost],
    labels=["ROOT", "boost"],
    styles=[ss[0], ss[1]],
)
ax.figure.savefig("overlay.png")
```

Add `ratio=True` to draw a ratio panel:

```python
(ax_main, ax_ratio) = overlay([h1, h2], labels=["ref", "alt"],
                               styles=[ss[0], ss[1]], ratio=True)
```

---

## 6 — Load a TTree branch

```python
from unrooted.io.root import load_branch

# Count histogram
h = load_branch("data.root", "tree", "x", n_bins=50, range=(-5, 5))

# Profile histogram: mean(y) vs x
hp = load_branch("data.root", "tree", "x", "y")
```

See [Loading ROOT Data](user-guide/loading-root.md) for all supported branch types.

---

## 7 — Interactive Plotly figure

```python
from unrooted.plot.plotly import plot, overlay

fig = plot(h)
fig.show()                         # opens in browser

fig2 = overlay([h1, h2], labels=["hx", "hy"], ratio=True)
fig2.show()
```

Plotly is an optional dependency:

```bash
uv add "unrooted[plotly]"
```

---

## 8 — Quick terminal preview

No display needed — `unrooted.plot.terminal` renders directly to a unicode string:

```python
from unrooted.plot.terminal import plot, overlay

print(plot(h))
print(overlay([h1, h2], labels=["hx", "hy"]))
```

Useful for sanity-checking histograms in scripts, notebooks, SSH sessions, or CI logs.
