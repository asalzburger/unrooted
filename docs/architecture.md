# Architecture

unrooted converts ROOT files and boost-histogram objects into NumPy-backed
data, then renders that data with independent plotting backends. ROOT I/O
uses Uproot; no C++ ROOT installation is required.

```text
ROOT histograms / branches         boost-histogram objects
             │                              │
     unrooted.io.root                unrooted.io.boost
             └──────────────┬───────────────┘
                            ▼
       unrooted.core: Axis / Histogram / ScatterData
                            │
             ┌──────────────┼───────────────┐
             ▼              ▼               ▼
         plot.mpl       plot.plotly     plot.terminal
       Matplotlib Axes  Plotly Figure       str
       hist + scatter   hist + scatter  histograms only
```

## Data contracts

`Histogram` contains axes, values, variances, optional flow values, and
optional lower/upper spread bounds. Readers return independent snapshots;
directly constructed objects may share the supplied arrays. Arrays are
mutable, and public consumers validate them again. See the
[data contracts](user-guide/histograms.md) for shapes, NaNs, and ownership.

The interpretation of uncertainty depends on the reader:

| Input | Values | Variances | Spread bounds |
| --- | --- | --- | --- |
| Count histogram | Counts or weighted sums | Count/weight variance | None |
| ROOT TProfile | Mean | Squared standard error from Uproot | Mean ± reconstructed standard deviation |
| Branch profile | Mean | Population variance / count | Observed minimum and maximum |
| Boost Mean | Mean | Sample variance / count | Mean ± sample standard deviation |
| Efficiency | Passed / total | Binomial variance | Wilson confidence interval |

`ScatterData` holds equally sized, flat real `x`/`y` arrays and labels.
`source_points`, `sample_seed`, and `sampled` record optional sampling.
Selection happens on tree entries before broadcasting and flattening paired
branches. Without `max_points`, all selected pairs are retained. With
`sampling="random"`, a seeded uniform sample without replacement preserves
pairing and input order. The [ROOT guide](user-guide/loading-root.md) explains
chunking, multi-pass profiles, and memory limits.

## Supported input paths

| Public reader | Input | Output |
| --- | --- | --- |
| `unrooted.io.root.load` | TH1, TH2, TProfile | `Histogram` |
| `unrooted.io.root.load_efficiency` | Separate unweighted passed/total TH1 objects | `Histogram` |
| `unrooted.io.root.load_branch` | Numeric scalar, vector, or nested jagged branches | Count/profile `Histogram` |
| `unrooted.io.root.load_scatter` | Two broadcast-compatible numeric branches | `ScatterData` |
| `unrooted.io.boost.load` | Numeric Regular/Variable/Integer axes; Double/Int64/Unlimited/AtomicInt64/Weight/Mean storage | `Histogram` |
| `unrooted.io.boost.load_efficiency` | Compatible 1D unweighted count histograms | `Histogram` |

TH3, TProfile2D, direct TEfficiency objects, categorical/Boolean boost axes,
WeightedMean, and weighted efficiencies are unsupported. Histogram storage
can represent more dimensions than the plotting backends render. See the
[I/O API](api/io.md) and [boost guide](user-guide/loading-boost.md).

## Public plotting and composition

Import `plot` and `overlay` from `unrooted.plot.mpl`,
`unrooted.plot.plotly`, or `unrooted.plot.terminal`. Graphical backends also
export `stack`, `plot_scatter`, and `overlay_scatter`.

Matplotlib functions accept existing axes where documented. Its histogram
overlay returns `(main_axes, ratio_axes)`; the second value is `None` when no
ratio is requested. Plotly functions return figures; `plot_scatter` accepts
an existing figure and optional subplot row/column. Terminal functions
return text. Ratio panels are histogram-only, require identical bin edges,
and propagate uncertainties assuming independent inputs.

`stack` adds nonnegative 1D count/yield histograms with identical edges, in
input order. Both graphical backends share validation and accumulation in
`plot/_stack.py`. Layer thicknesses are the original values; the optional
total uncertainty is `sqrt(sum(variances))` for independent components.
Profiles/efficiencies with spread bounds are rejected. Missing values leave
gaps in the entire stack bin, and missing variances leave gaps in its total band.

`HistogramStyle` controls one dataset. `StyleSet` combines a packaged palette
with style templates. The [plotting guide](user-guide/plotting.md) and
[API reference](api/plot.md) describe arguments and backend capabilities.

## Module map

```text
unrooted/
├── _version.py          sole release version, read by Hatchling
├── core/                axis, histogram, scatter, shared validation/statistics
├── io/
│   ├── root/            object readers, chunked branch loading, sampling
│   └── boost/           in-memory histogram conversion
├── plot/
│   ├── style.py         per-dataset appearance and named presets
│   ├── style_set.py     packaged palettes and coordinated styles
│   ├── mpl/             histogram/scatter rendering and stylesheet generation
│   ├── plotly/          optional interactive histogram/scatter rendering
│   └── terminal/        histogram text rendering
├── cli/                 draw specifications, loading, validation, export
└── resources/           odd/sd palettes, PNG/SVG logos, previews
```

Runtime resources are read with `importlib.resources`. Stylesheet generation
writes to a caller-selected path or the current working directory. Adding a
resource target requires a packaged `colors.json` containing four colors;
logos are optional. See the [resource guide](user-guide/resources.md).
