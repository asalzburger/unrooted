# Plotting

`unrooted` ships two independent plotting backends that share the same
`Histogram`, `HistogramStyle`, and `StyleSet` objects.

| Backend | Import | Returns | Best for |
|---------|--------|---------|----------|
| **matplotlib** | `unrooted.plot.mpl` | `matplotlib.axes.Axes` | publication figures, scripts |
| **plotly** | `unrooted.plot.plotly` | `plotly.graph_objects.Figure` | interactive exploration |

---

## Matplotlib backend

```python
from unrooted.plot.mpl import plot, overlay
```

### `plot()` — single histogram

```python
ax = plot(h)
```

By default `plot()` creates a new figure.  Pass an existing `ax` to draw into it:

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
plot(h, ax=ax)
```

#### Unstyled (keyword-argument) mode

Any keyword is forwarded to the underlying matplotlib call.  This is the
"quick and dirty" path — convenient for exploration:

```python
ax = plot(h, color="steelblue", linewidth=2, label="data")
```

#### Styled mode

Pass a `HistogramStyle` (or get one from a `StyleSet`) for full control over
line, marker, fill, error bars, and spread display:

```python
from unrooted.plot import HistogramStyle

style = HistogramStyle(
    line_color="#1A4F8A",
    marker="o",
    fill_alpha=0.15,
    error_display="bar",
    spread_display="band",
)
ax = plot(h, style=style)
```

!!! note
    `style=` and `**kwargs` cannot be combined — pass one or the other.

### `overlay()` — multiple histograms

```python
(ax_main, ax_ratio) = overlay(
    [h1, h2, h3],
    labels=["signal", "background", "data"],
    styles=[ss[0], ss[1], ss[2]],
)
```

`overlay()` always returns a tuple `(ax_main, ax_ratio)`.  When `ratio=False`
(default), `ax_ratio` is `None`.

#### Ratio panel

```python
(ax, ax_r) = overlay([h1, h2], labels=["h1", "h2"], ratio=True)
```

The ratio panel shows `h_i / h_0` for each subsequent histogram.  Uncertainties
are propagated via Gaussian error propagation.  Bins where the reference is zero
are shown as `NaN` (no marker).

#### Passing an existing axes

`overlay()` accepts a single axes object and draws all histograms into it.
A ratio panel cannot be added when an external `ax` is supplied.

```python
fig, ax = plt.subplots()
overlay([h1, h2], ax=ax, labels=["h1", "h2"])
```

### 2D histograms

`plot()` detects `h.ndim == 2` automatically and renders via `pcolormesh`:

```python
h2 = load("data.root", "hxy")
ax = plot(h2)
```

---

## Plotly backend

```python
from unrooted.plot.plotly import plot, overlay
```

Install the optional dependency first:

```bash
uv add "unrooted[plotly]"
# or
pip install "unrooted[plotly]"
```

The plotly backend provides a similar high-level `plot()` / `overlay()` API to
the matplotlib backend, but the signatures are not identical.  In particular,
it returns a `plotly.graph_objects.Figure` instead of matplotlib axes, so
matplotlib-specific parameters such as `ax=` are not supported, and
`overlay(..., ratio=True)` returns a single figure rather than the
`(ax_main, ax_ratio)` tuple returned by the matplotlib backend.  Figures are
interactive by default: zoom, pan, hover tooltips, and legend toggling work
out of the box.

!!! note
    Matplotlib-style shorthand colors (`"C0"`, `"r"`, `"k"`) are not supported.
    Use hex strings (`"#1A4F8A"`) or RGBA tuples instead.

### `plot()` — single histogram

```python
fig = plot(h)
fig.show()                        # interactive browser window
fig.write_image("hx.png")        # static export (requires kaleido)
```

Styled:

```python
from unrooted.plot import HistogramStyle

fig = plot(h, style=HistogramStyle(
    line_color="#1A4F8A",
    fill_alpha=0.15,
    error_display="band",
))
fig.show()
```

### `overlay()` — multiple histograms

```python
from unrooted.plot.plotly import overlay
from unrooted.plot import StyleSet

ss = StyleSet.load("odd")
fig = overlay(
    [h1, h2],
    labels=["signal", "background"],
    styles=[ss[0], ss[1]],
)
fig.show()
```

With a ratio panel:

```python
fig = overlay([h1, h2], labels=["ref", "alt"], ratio=True)
fig.show()
```

### 2D histograms

```python
h2 = load("data.root", "hxy")
fig = plot(h2)   # renders as go.Heatmap with Viridis colorscale
fig.show()
```
