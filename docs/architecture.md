# Architecture

## Philosophy

`unrooted` exists because particle physics data lives in ROOT files and
[`boost-histogram`](https://boost-histogram.readthedocs.io/) objects, but
consuming either format traditionally requires a heavy C++ ROOT installation or
tight coupling to a specific analysis framework.

`unrooted` breaks that coupling: it converts both sources into a single
numpy-backed `Histogram` object that slots directly into the scientific Python
ecosystem, then lets you plot it with whichever backend fits your workflow.

```
ROOT file (.root)        boost_histogram objects
       │                         │
       ▼  unrooted.io.root       ▼  unrooted.io.boost
┌──────────────────────────────────────────────────────┐
│                 Histogram  /  Axis                   │  ←  unrooted.core
└──────────────────────────────────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
  unrooted.plot.mpl  unrooted.plot.plotly  unrooted.plot.terminal
  matplotlib Axes    plotly Figure         str
  (publication)      (interactive)         (headless / CI)
```

---

## Design principles

**No ROOT dependency.**
File I/O is delegated entirely to [uproot](https://uproot.readthedocs.io/).
`uproot` is a pure-Python ROOT reader; no C++ ROOT installation is required.

**numpy-first.**
Every histogram is backed by `np.ndarray`.  The `Histogram` object is a thin
dataclass wrapper — no magic, no hidden state.  You can always reach into
`.values` and `.variances` directly.

**One representation layer.**
Both I/O backends produce the same `Histogram` type.  A histogram loaded from a
ROOT `TProfile` and one converted from a `boost_histogram.Histogram` with `Mean`
storage are structurally identical and can be passed to the same plot functions.

**Separate concerns.**
I/O, the data model, and plotting are independent layers.  Adding a new I/O
backend or a new plot backend only requires implementing the small interface of
that layer, with no changes elsewhere.

**Composable styling.**
`HistogramStyle` covers a single histogram; `StyleSet` coordinates a four-color
palette for a full overlay.  Styles are plain dataclasses — easy to construct,
copy, or override.

---

## Module map

```
unrooted/
├── __init__.py
│
├── core/
│   ├── axis.py            Axis dataclass (edges, label, centers, widths)
│   └── histogram.py       Histogram dataclass (values, variances, spread)
│
├── io/
│   ├── root/
│   │   ├── reader.py      load()          → TH1 / TH2 / TProfile
│   │   └── tree.py        load_branch()   → TTree branch(es) as histogram
│   └── boost/
│       └── reader.py      load()          → any bh.Histogram storage type
│                          load_efficiency()→ accepted/total → efficiency
│
└── plot/
    ├── style.py           HistogramStyle — per-histogram visual config
    ├── style_set.py       StyleSet — coordinated 4-color palette from JSON
    │
    ├── mpl/               Matplotlib backend
    │   ├── histogram.py   plot()   → matplotlib Axes
    │   ├── overlay.py     overlay() + optional ratio panel
    │   └── stylesheet.py  generate_stylesheet() — palette preview PNG
    │
    ├── plotly/            Plotly backend  (optional dep: plotly)
    │   ├── _color.py      _to_rgba() — color normalisation helper
    │   ├── histogram.py   plot()   → plotly Figure
    │   └── overlay.py     overlay() + optional ratio panel
    │
    └── terminal/          Terminal backend  (stdlib + numpy only)
        ├── _render.py     render() — core unicode rendering engine
        └── histogram.py   plot() / overlay() → str
```

---

## Data flow

The `Histogram` dataclass is the single currency that flows through the library.
Both I/O backends produce the same type; all plot backends consume it.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  I/O layer — ROOT backend                                                │
│                                                                          │
│  load("file.root", "hx")                 → Histogram (TH1/TH2)          │
│  load("file.root", "profX")              → Histogram (TProfile)          │
│  load_efficiency("file.root", "p", "t")  → Histogram (efficiency)        │
│  load_branch("file.root", "t", "x")      → Histogram (count)             │
│  load_branch("file.root", "t", "x", "y") → Histogram (profile)           │
├──────────────────────────────────────────────────────────────────────────┤
│  I/O layer — boost-histogram backend                                     │
│                                                                          │
│  load(bh_hist)                           → Histogram (any storage type)  │
│  load_efficiency(accepted, total)         → Histogram (efficiency)        │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │  Histogram(axes, values, variances, …)
┌──────────────────────────▼───────────────────────────────────────────────┐
│  Core data model                                                         │
│                                                                          │
│  Histogram                                                               │
│    .axes       list[Axis]   — bin edges, label, centers, widths          │
│    .values     ndarray      — bin counts or profile means                │
│    .variances  ndarray      — Poisson counts or SE²                      │
│    .overflow   ndarray|None — values with under/overflow bins            │
│    .spread_min ndarray|None — per-bin min (profile / efficiency only)    │
│    .spread_max ndarray|None — per-bin max (profile / efficiency only)    │
└──────────┬──────────────────────────────┬────────────────────────┬───────┘
           │                              │                        │
           ▼                              ▼                        ▼
┌──────────────────────┐   ┌─────────────────────────┐  ┌──────────────────┐
│  plot.mpl            │   │  plot.plotly             │  │  plot.terminal   │
│                      │   │                          │  │                  │
│  plot()              │   │  plot()                  │  │  plot()          │
│  overlay()           │   │  overlay()               │  │  overlay()       │
│                      │   │                          │  │                  │
│  → Axes              │   │  → go.Figure             │  │  → str           │
│  (publication)       │   │  (interactive)           │  │  (headless)      │
└──────────────────────┘   └─────────────────────────┘  └──────────────────┘
```

---

## Resource targets

Each detector or experiment can have its own *resource target* — a directory
under `resources/` containing logos and a color palette:

```
resources/
├── odd/
│   ├── odd_tech_light.png      full logo
│   ├── odd_tech_light_line.png
│   ├── colors.json             4-color palette
│   └── stylesheet.png          auto-generated palette preview
└── sd/
    ├── super_duper.png
    ├── super_duper_line.png
    ├── colors.json
    └── stylesheet.png
```

Adding a new target requires a `colors.json` with four hex codes; logo files
(PNG/SVG) are optional.  `StyleSet.load()` and `generate_stylesheet()` work
automatically once `colors.json` is present.
