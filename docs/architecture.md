# Architecture

## Philosophy

`unrooted` exists because ROOT histograms are the de-facto format for particle
physics data, but the ROOT software stack is large to install and not Pythonic.
`unrooted` bridges the gap: it reads ROOT files via
[uproot](https://uproot.readthedocs.io/) (pure Python, no ROOT needed) and
converts the data to `numpy`-backed objects that slot into the standard scientific
Python ecosystem.

```
ROOT file (.root)
      │
      ▼  unrooted.io.root  (uproot under the hood)
┌─────────────────────────┐
│  Histogram  /  Axis     │  ←  unrooted.core
└─────────────────────────┘
      │
      ▼  unrooted.plot.mpl  (matplotlib under the hood)
Publication-ready figures
```

---

## Design principles

**No ROOT dependency.**
File I/O is delegated entirely to [uproot](https://uproot.readthedocs.io/).
`uproot` is a pure-Python ROOT reader that requires no C++ ROOT installation.

**numpy-first.**
Every histogram is backed by `np.ndarray`.  The `Histogram` object is a thin
dataclass wrapper — no magic, no hidden state.  You can always reach into
`.values` and `.variances` directly.

**Separate concerns.**
I/O, the data model, and plotting are independent layers.  Swapping the plotting
backend (e.g. to Bokeh or Plotly) only requires a new `plot/` sub-package.

**Composable styling.**
`HistogramStyle` covers a single histogram; `StyleSet` coordinates a four-color
palette for a full overlay.  Styles are plain dataclasses — easy to construct,
copy, or override.

---

## Module map

```
unrooted/
├── __init__.py            Histogram, Histogram1D, Histogram2D, __version__
│
├── core/
│   ├── axis.py            Axis dataclass (edges, label, centers, widths)
│   └── histogram.py       Histogram dataclass (values, variances, spread)
│
├── io/
│   └── root/
│       ├── reader.py      load()        → TH1 / TH2 / TProfile
│       └── tree.py        load_branch() → TTree branch(es) as histogram
│
└── plot/
    ├── style.py           HistogramStyle — per-histogram visual config
    ├── style_set.py       StyleSet — coordinated 4-color palette from JSON
    └── mpl/               Matplotlib backend
        ├── histogram.py   plot()
        ├── overlay.py     overlay() + optional ratio panel
        └── stylesheet.py  generate_stylesheet() — palette preview PNG
```

---

## Data flow

The `Histogram` dataclass is the single currency that flows through the library.

```
┌──────────────────────────────────────────────────────────────────┐
│  I/O layer                                                       │
│                                                                  │
│  load("file.root", "hx")          → Histogram (TH1/TH2)         │
│  load_branch("file.root","t","x") → Histogram (count)           │
│  load_branch("file.root","t","x","y") → Histogram (profile)     │
└───────────────────────┬──────────────────────────────────────────┘
                        │  Histogram(axes, values, variances, …)
┌───────────────────────▼──────────────────────────────────────────┐
│  Core data model                                                 │
│                                                                  │
│  Histogram                                                       │
│    .axes       list[Axis]   — bin edges, label, centers, widths  │
│    .values     ndarray      — bin counts or profile means        │
│    .variances  ndarray      — Poisson counts or SE²              │
│    .spread_min ndarray|None — per-bin min  (profile only)        │
│    .spread_max ndarray|None — per-bin max  (profile only)        │
└───────────────────────┬──────────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────────┐
│  Plot layer (matplotlib backend)                                 │
│                                                                  │
│  plot(hist, style=HistogramStyle(…))                             │
│  overlay([h1,h2,…], styles=StyleSet.load("odd")[:])             │
└──────────────────────────────────────────────────────────────────┘
```

---

## Resource targets

Each detector or experiment can have its own *resource target* — a directory
under `resources/` containing logos and a color palette:

```
resources/
├── odd/
│   ├── odd_tech_light.png     full logo
│   ├── odd_tech_light_line.png
│   ├── colors.json            4-color palette
│   └── stylesheet.png         auto-generated palette preview
└── sd/
    ├── super_duper.png
    ├── super_duper_line.png
    ├── colors.json
    └── stylesheet.png
```

Adding a new target requires a `colors.json` with four hex codes; logo files
(PNG/SVG) are optional.  `StyleSet.load()` and `generate_stylesheet()` work
automatically once `colors.json` is present.
