# unrooted

[![CI](https://github.com/asalzburger/unrooted/actions/workflows/ci.yml/badge.svg)](https://github.com/asalzburger/unrooted/actions/workflows/ci.yml)
[![docs](https://github.com/asalzburger/unrooted/actions/workflows/docs.yml/badge.svg)](https://github.com/asalzburger/unrooted/actions/workflows/docs.yml)

A Python library for loading, representing, and visualising histograms from HEP data formats.

**Documentation:** https://asalzburger.github.io/unrooted/

---

## Architecture

The library is organised into three independent layers:

```
I/O  →  Core  →  Plot
```

| Layer | Package | Description |
|-------|---------|-------------|
| **I/O** | `unrooted.io.root` | Reads ROOT files via uproot; returns `Histogram` objects |
| **Core** | `unrooted.core` | `Axis` and `Histogram` numpy-backed dataclasses |
| **Plot** | `unrooted.plot` | Matplotlib, Plotly, and terminal backends |

### Core data structures

- **`Axis`** — bin edges + label; computed properties `centers`, `widths`, `n_bins`
- **`Histogram`** — holds `axes`, `values`, `variances`, `overflow`, and optional `spread_min`/`spread_max` for profiles and efficiency histograms

### I/O backends

- `reader.load(path, key)` — reads TH1/TH2/TProfile via uproot
- `reader.load_efficiency(path, pass_key, total_key)` — binomial efficiency from two TH1s

### Plot backends

- **matplotlib** (`unrooted.plot.mpl`) — 1D/2D histograms, styled overlays, ratio panels
- **Plotly** (`unrooted.plot.plotly`) — interactive browser plots
- **terminal** (`unrooted.plot.terminal`) — ASCII rendering in the console

Styling is controlled by `HistogramStyle` and `StyleSet`, which loads 4-colour palettes from `resources/<target>/colors.json` (targets: `odd`, `sd`).

---

## Installation

Requires Python ≥ 3.11 and [uv](https://github.com/astral-sh/uv).

```bash
# Core + dev tools (lint, type check, tests)
uv sync --extra dev

# Include Plotly backend
uv sync --extra dev --extra plotly
```

---

## Usage

### Command-line interface

```bash
uv run unrooted --help
```

### Python API

```python
from unrooted.io.root import reader
from unrooted.plot.mpl import histogram, overlay

# Load a histogram from a ROOT file
h = reader.load("data.root", "my_histogram")

# Plot it
fig, ax = histogram.plot(h)
fig.savefig("histogram.png")

# Overlay multiple histograms with a ratio panel
fig, axes = overlay.overlay([h1, h2], ratio=True)
```

---

## Development

```bash
# Run all unit tests
uv run pytest tests/unit_tests/

# Lint
uv run ruff check unrooted/

# Type check
uv run pyright

# Run an example script
uv run python tests/examples/example_styled_histogram.py
```

Branch naming: `feat-<topic>`, `fix-<topic>`, `chore-<topic>`.

Always run lint and type check before committing.
