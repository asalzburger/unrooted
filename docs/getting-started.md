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

## 1 — Load a ROOT histogram

```python
from unrooted.io.root import load

h = load("data.root", "hx")

print(h.name)               # "hx"
print(h.ndim)               # 1
print(h.values.shape)       # (n_bins,)
print(h.axes[0].centers)    # bin centres as numpy array
```

---

## 2 — Plot it

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

## 3 — Apply a detector style

```python
from unrooted.plot.mpl import plot
from unrooted.plot import StyleSet

ss = StyleSet.load("odd")   # or "sd"
ax = plot(h, style=ss[0])
ax.figure.savefig("hx_styled.png")
```

---

## 4 — Overlay multiple histograms

```python
from unrooted.io.root import load
from unrooted.plot.mpl import overlay
from unrooted.plot import StyleSet

ss = StyleSet.load("odd")
h1 = load("data.root", "hx")
h2 = load("data.root", "hy")

(ax, _) = overlay(
    [h1, h2],
    labels=["x", "y"],
    styles=[ss[0], ss[1]],
)
ax.figure.savefig("overlay.png")
```

Add `ratio=True` to draw a ratio panel beneath the main plot:

```python
(ax_main, ax_ratio) = overlay([h1, h2], labels=["x", "y"],
                               styles=[ss[0], ss[1]], ratio=True)
```

---

## 5 — Load a TTree branch

```python
from unrooted.io.root import load_branch

# Count histogram
h = load_branch("data.root", "tree", "x", n_bins=50, range=(-5, 5))

# Profile histogram: mean(y) vs x
hp = load_branch("data.root", "tree", "x", "y")
```

See [Loading ROOT Data](user-guide/loading-root.md) for all supported branch types.

---

## 6 — Interactive Plotly figure

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

## 7 — Quick terminal preview

No display needed — `unrooted.plot.terminal` renders directly to a unicode string:

```python
from unrooted.plot.terminal import plot, overlay

print(plot(h))
print(overlay([h1, h2], labels=["hx", "hy"]))
```

Useful for sanity-checking histograms in scripts, notebooks, SSH sessions, or CI logs.
