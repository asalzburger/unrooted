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

<span id="plot"></span>

::: unrooted.plot.mpl.histogram.plot
    options:
      heading_level: 3
      heading: plot
      toc_label: plot

<span id="overlay"></span>

::: unrooted.plot.mpl.overlay.overlay
    options:
      heading_level: 3
      heading: overlay
      toc_label: overlay

<span id="plot_scatter"></span>

Exported as `unrooted.plot.mpl.plot_scatter`.

::: unrooted.plot.mpl.scatter.plot
    options:
      heading_level: 3
      heading: plot_scatter
      toc_label: plot_scatter

<span id="overlay_scatter"></span>

Exported as `unrooted.plot.mpl.overlay_scatter`.

::: unrooted.plot.mpl.scatter.overlay
    options:
      heading_level: 3
      heading: overlay_scatter
      toc_label: overlay_scatter

<span id="generate_stylesheet"></span>

::: unrooted.plot.mpl.stylesheet.generate_stylesheet
    options:
      heading_level: 3
      heading: generate_stylesheet
      toc_label: generate_stylesheet

---

## Plotly backend

<span id="plot_1"></span>

::: unrooted.plot.plotly.histogram.plot
    options:
      heading_level: 3
      heading: plot
      toc_label: plot

<span id="overlay_1"></span>

::: unrooted.plot.plotly.overlay.overlay
    options:
      heading_level: 3
      heading: overlay
      toc_label: overlay

<span id="plot_scatter_1"></span>

Exported as `unrooted.plot.plotly.plot_scatter`.

::: unrooted.plot.plotly.scatter.plot
    options:
      heading_level: 3
      heading: plot_scatter
      toc_label: plot_scatter

<span id="overlay_scatter_1"></span>

Exported as `unrooted.plot.plotly.overlay_scatter`.

::: unrooted.plot.plotly.scatter.overlay
    options:
      heading_level: 3
      heading: overlay_scatter
      toc_label: overlay_scatter

---

## Terminal backend

<span id="plot_2"></span>

::: unrooted.plot.terminal.histogram.plot
    options:
      heading_level: 3
      heading: plot
      toc_label: plot

<span id="overlay_2"></span>

::: unrooted.plot.terminal.histogram.overlay
    options:
      heading_level: 3
      heading: overlay
      toc_label: overlay
