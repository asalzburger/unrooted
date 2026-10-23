# Plot

Style classes and plotting functions for all three backends. Import functions
from the backend package rather than its implementation modules.
`HistogramStyle` and `StyleSet` are exported from `unrooted.plot`.

| Backend package | Histograms | Point clouds | Return values |
| --- | --- | --- | --- |
| `unrooted.plot.mpl` | `plot`, `overlay` | `plot_scatter`, `overlay_scatter` | Axes; histogram overlay returns `(main, ratio)` |
| `unrooted.plot.plotly` | `plot`, `overlay` | `plot_scatter`, `overlay_scatter` | Figure |
| `unrooted.plot.terminal` | `plot`, `overlay` | Unsupported | str |

See [composition examples](../user-guide/plotting.md) and the
[CLI capability table](../user-guide/cli.md#backends). Plotly requires the
`plotly` extra; static export also requires Kaleido and a compatible browser.

## HistogramStyle

::: unrooted.plot.style.HistogramStyle

## StyleSet

::: unrooted.plot.style_set.StyleSet

---

## Matplotlib backend

### plot

::: unrooted.plot.mpl.histogram.plot

### overlay

::: unrooted.plot.mpl.overlay.overlay

### plot_scatter

Exported as `unrooted.plot.mpl.plot_scatter`.

::: unrooted.plot.mpl.scatter.plot

### overlay_scatter

Exported as `unrooted.plot.mpl.overlay_scatter`.

::: unrooted.plot.mpl.scatter.overlay

### generate_stylesheet

::: unrooted.plot.mpl.stylesheet.generate_stylesheet

---

## Plotly backend

### plot

::: unrooted.plot.plotly.histogram.plot

### overlay

::: unrooted.plot.plotly.overlay.overlay

### plot_scatter

Exported as `unrooted.plot.plotly.plot_scatter`.

::: unrooted.plot.plotly.scatter.plot

### overlay_scatter

Exported as `unrooted.plot.plotly.overlay_scatter`.

::: unrooted.plot.plotly.scatter.overlay

---

## Terminal backend

### plot

::: unrooted.plot.terminal.histogram.plot

### overlay

::: unrooted.plot.terminal.histogram.overlay
