# Plotting

`unrooted` ships three independent plotting backends that share the same
`Histogram`, `HistogramStyle`, and `StyleSet` objects.

| Backend | Import | Returns | Best for |
|---------|--------|---------|----------|
| **matplotlib** | `unrooted.plot.mpl` | `matplotlib.axes.Axes` | publication figures, scripts |
| **plotly** | `unrooted.plot.plotly` | `plotly.graph_objects.Figure` | interactive exploration |
| **terminal** | `unrooted.plot.terminal` | `str` | quick inspection, headless environments, CI logs |

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
    spread_display="band",   # "bar", "band", or "continuous"
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

The ratio panel inherits the **style of B**: line color, line style, line width,
error display mode, and error color all come from the corresponding
`HistogramStyle`.  Set `error_display=None` to suppress error bars in the ratio
panel, or use `LineStyle.DASHED` to visually distinguish the ratio line from the
reference:

```python
from unrooted.plot.style import HistogramStyle, LineStyle
from unrooted.plot.style_set import StyleSet

ss = StyleSet.load("odd")
sx = HistogramStyle.as_hist().with_color(ss.colors[0])              # reference
sy = HistogramStyle.as_line(line_style=LineStyle.DASHED,
                             line_width=2.0,
                             error_display="bar").with_color(ss.colors[1])  # B
overlay([hx, hy], ratio=True, labels=["ref", "B"], styles=[sx, sy])
```

![Ratio panel with styled B](../assets/examples/mpl_ratio_styled.png)

#### Passing an existing axes

`overlay()` accepts a single axes object and draws all histograms into it.
A ratio panel cannot be added when an external `ax` is supplied.

```python
fig, ax = plt.subplots()
overlay([h1, h2], ax=ax, labels=["h1", "h2"])
```

### Scatter plots

```python
from unrooted.plot.mpl.scatter import plot as scatter_plot
from unrooted.core.scatter import ScatterData

sd = ScatterData(x=x_arr, y=y_arr, x_label="η", y_label="pT [GeV]")
ax = scatter_plot(sd)
```

Pass a `HistogramStyle` built with `HistogramStyle.as_scatter()` to control
marker shape, size, color, and opacity:

```python
from unrooted.plot.style import HistogramStyle

style = HistogramStyle.as_scatter(marker="o", marker_size=3.0)
ax = scatter_plot(sd, style=style, label="track candidates")
ax.legend()
```

To overlay multiple scatter datasets on the same axes, pass an existing `ax`:

```python
import matplotlib.pyplot as plt

_, ax = plt.subplots()
scatter_plot(sd1, ax=ax, label="A", set_axis_labels=False)
scatter_plot(sd2, ax=ax, label="B", set_axis_labels=False)
ax.set_xlabel("η")
ax.legend()
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
    error_display="band",   # "bar", "band", or "continuous"
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

### Scatter plots

```python
from unrooted.plot.plotly.scatter import plot as scatter_plot
from unrooted.core.scatter import ScatterData

sd = ScatterData(x=x_arr, y=y_arr, x_label="η", y_label="pT [GeV]")
fig = scatter_plot(sd)
fig.show()
```

With a custom style and label:

```python
from unrooted.plot.style import HistogramStyle

style = HistogramStyle.as_scatter(marker="o", marker_size=3.0).with_color("#1A4F8A")
fig = scatter_plot(sd, style=style, label="track candidates")
fig.show()
```

To overlay multiple datasets, use `_add_scatter_trace` directly:

```python
import plotly.graph_objects as go
from unrooted.plot.plotly.scatter import _add_scatter_trace
from unrooted.plot.plotly.histogram import DEFAULT_COLORS
from unrooted.plot.style import HistogramStyle

fig = go.Figure()
style = HistogramStyle.as_scatter()
_add_scatter_trace(fig, sd1, style, DEFAULT_COLORS[0], label="A")
_add_scatter_trace(fig, sd2, style, DEFAULT_COLORS[1], label="B")
fig.show()
```

### 2D histograms

```python
h2 = load("data.root", "hxy")
fig = plot(h2)   # renders as go.Heatmap with Viridis colorscale
fig.show()
```

---

## Terminal backend

```python
from unrooted.plot.terminal import plot, overlay
```

The terminal backend renders 1D histograms directly as a multi-line unicode
string — no display library, no GUI, no file I/O required.  Call `print()` on
the result to display it anywhere: a notebook cell, a CI log, an SSH session.

!!! note
    Requires a monospace font with unicode support in your terminal.
    The plot width equals the number of bins (maximum 100).

### `plot()` — single histogram

```python
result = plot(h, max_lines=40)
print(result)
```

Each bin occupies one character column; the height is proportional to the bin
value scaled to `max_lines` rows.  The y-axis shows four tick labels at
100 %, 75 %, 50 %, and 25 % of the global maximum; `0` appears on the axis
line itself.

Example output (30 rows, Gaussian-shaped histogram):

```
46.8 │                         ○                        
     │                       ○ ○○                       
35.1 │                     ○ ○ ○○○○                     
     │                    ○○○○○○○○○○                    
23.4 │                 ○ ○○○○○○○○○○○ ○                  
     │               ○○○○○○○○○○○○○○○○○○ ○               
11.7 │             ○○○○○○○○○○○○○○○○○○○○○○○ ○            
     │          ○○○○○○○○○○○○○○○○○○○○○○○○○○○○○           
   0 └──────────────────────────────────────────────────→ x
     -5   -4   -3   -2   -1    0    1    2    3    4    5
```

### `overlay()` — multiple histograms

Up to four histograms can be overlaid.  When two or more histograms are present
in the same cell, a composite glyph is used:

| Combination | Glyph | Unicode |
|-------------|-------|---------|
| ○ alone | ○ | U+25CB |
| ✚ alone | ✚ | U+271A |
| □ alone | □ | U+25A1 |
| · alone | · | U+00B7 |
| ○ + ✚ | ⊕ | U+2295 |
| ○ + · | ⊙ | U+2299 |
| ✚ + □ | ⊞ | U+229E |
| □ + · | ⊡ | U+22A1 |
| ○ + □ | ⊚ | U+229A |
| ✚ + · | ✢ | U+2722 |
| any 3 | ⊛ | U+229B |
| all 4 | ✳ | U+2733 |

```python
result = overlay([hx, hy], labels=["hx", "hy"], max_lines=30)
print(result)
```

The legend is printed below the plot when `labels` is supplied.

!!! note
    Error bars and spread bands are intentionally omitted in the terminal
    backend — the character-cell resolution makes them impractical to render.
