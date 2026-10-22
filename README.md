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
| **I/O** | `unrooted.io.root` | Reads ROOT files via uproot; returns histograms or point clouds |
| **Core** | `unrooted.core` | `Axis`, `Histogram`, and `ScatterData` NumPy-backed dataclasses |
| **Plot** | `unrooted.plot` | Matplotlib, Plotly, and terminal backends |

### Core data structures

- **`Axis`** — bin edges + label; computed properties `centers`, `widths`, `n_bins`
- **`Histogram`** — holds `axes`, `values`, `variances`, `overflow`, and optional `spread_min`/`spread_max` for profiles and efficiency histograms
- **`ScatterData`** — flat x/y arrays, exported from `unrooted` and `unrooted.core`

### I/O backends

- `reader.load(path, key)` — reads TH1/TH2/TProfile via uproot
- `reader.load_efficiency(path, pass_key, total_key)` — binomial efficiency from two TH1s
- `load_scatter(path, tree, x_branch, y_branch)` — raw points from two branches

### Plot backends

- **matplotlib** (`unrooted.plot.mpl`) — 1D/2D histograms, styled overlays, ratio panels
- **Plotly** (`unrooted.plot.plotly`) — interactive browser plots
- **terminal** (`unrooted.plot.terminal`) — ASCII rendering in the console

Styling is controlled by `HistogramStyle` and `StyleSet`. The `odd` and `sd`
palettes and logos are bundled in `unrooted/resources/` and installed with the
package.

---

## Installation

Requires Python ≥ 3.11. Install the current source into your Python environment
with pip:

```bash
git clone https://github.com/asalzburger/unrooted
cd unrooted
python -m pip install .

# Optional interactive Plotly backend
python -m pip install ".[plotly]"
```

Alternatively, install a built wheel with
`python -m pip install /path/to/unrooted-<version>-py3-none-any.whl`.
Contributor setup with [uv](https://github.com/astral-sh/uv) is described under
[Development](#development).

---

## Usage

### Command-line interface

```bash
unrooted --help
unrooted --input data.root --draw hist:hx --output histogram.png
```

### Python API

For a ROOT file containing histograms named `hx` and `hy` with identical edges:

```python
from unrooted.io.root import load
from unrooted.plot.mpl import overlay, plot

h1 = load("data.root", "hx")
h2 = load("data.root", "hy")

# Plot it
ax = plot(h1)
ax.figure.savefig("histogram.png")

# Overlay multiple histograms with a ratio panel
ax_main, ax_ratio = overlay([h1, h2], labels=["hx", "hy"], ratio=True)
ax_main.figure.savefig("overlay.png")
```

Ratios require exactly matching bin edges and assume independent uncertainties.
Efficiency readers instead require unweighted integer passed/total counts and
return Wilson interval bounds (68.27% by default). See the
[data and statistical contracts](docs/user-guide/histograms.md) and
[efficiency guide](docs/user-guide/loading-root.md#efficiency-histograms).

For point clouds, import `load_scatter` from `unrooted.io.root` and
`plot_scatter` / `overlay_scatter` from either graphical backend. The
[plotting guide](docs/user-guide/plotting.md) covers public composition APIs;
the [CLI guide](docs/user-guide/cli.md#backends) lists backend capabilities
and optional Plotly static export requirements.

---

## Development

Production readiness work is organised in the [staged roadmap](ROADMAP.md).

Clone the repository and install the development tools with uv:

```bash
git clone https://github.com/asalzburger/unrooted
cd unrooted
uv sync --extra dev

# ROOT test fixtures are stored in Git LFS
git lfs install
git lfs pull
```

Then run the checks:

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

CI also builds a wheel from the source distribution and checks it in an
environment containing only the declared runtime dependencies:

```bash
uv build --sdist --out-dir dist
uv build --wheel dist/*.tar.gz --out-dir dist
uv venv /tmp/unrooted-wheel
uv pip install --python /tmp/unrooted-wheel/bin/python dist/*.whl
/tmp/unrooted-wheel/bin/python -I tests/packaging/smoke.py
```

The smoke check uses synthetic ROOT data and temporary output directories.

Branch naming: `feat-<topic>`, `fix-<topic>`, `chore-<topic>`.

Always run lint and type check before committing.
