# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

```bash
# Install with all dev extras
uv sync --extra dev --extra plotly

# Run all tests
uv run pytest tests/unit_tests/

# Run a single test file
uv run pytest tests/unit_tests/test_core_histogram.py

# Run a single test by name
uv run pytest tests/unit_tests/test_core_histogram.py::test_histogram_errors

# Lint
uv run ruff check unrooted/

# Type check
uv run pyright

# Run an example script
uv run python tests/examples/example_styled_histogram.py

# Regenerate stylesheet preview PNGs (after changing colors.json)
uv run python -c "from unrooted.plot.mpl.stylesheet import generate_stylesheet; generate_stylesheet('odd'); generate_stylesheet('sd')"
```

## Architecture

The library has three independent layers that compose through the `Histogram` dataclass:

**I/O → Core → Plot**

### Core (`unrooted/core/`)
- `Axis`: bin edges + label; computed properties `centers`, `widths`, `n_bins`
- `Histogram`: numpy-backed dataclass — `axes`, `values`, `variances`, `overflow`, and optional `spread_min`/`spread_max` (populated for TProfile and efficiency histograms)

### I/O (`unrooted/io/<backend>/`)
Every reader returns a `Histogram`. Currently only the ROOT backend exists:
- `reader.load(path, key)` — reads TH1/TH2/TProfile via uproot; TProfile populates `spread_min`/`spread_max` as mean ± σ_y
- `reader.load_efficiency(path, pass_key, total_key)` — computes binomial efficiency from two TH1s; uproot cannot read `TEfficiency` natively

### Plot (`unrooted/plot/`)
- `style.HistogramStyle` — single dataclass controlling line, fill, marker, error, and spread rendering
- `style_set.StyleSet` — loads `resources/{target}/colors.json` and combines four palette colors with four `_STYLE_TEMPLATES` (line style + marker combinations) into a ready-to-use `styles` list; index wraps cyclically
- `mpl/histogram.plot()` — dispatches to `_plot_1d`, `_plot_1d_styled`, or `_plot_2d`; `_plot_1d_styled` renders in five ordered layers: fill → line → markers → errors → spread
- `mpl/overlay.overlay()` — multi-histogram overlay with optional ratio panel
- `mpl/scatter.plot()` — renders a `ScatterData` point cloud; `_add_scatter_trace` is the composable primitive used by the CLI for multi-dataset overlays
- `mpl/_range._draw_range()` — shared primitive for both error bars and filled bands, used by both the histogram and overlay modules
- `mpl/stylesheet.generate_stylesheet()` — renders a palette preview PNG; called as part of resource updates
- `plotly/histogram.plot()` — plotly equivalent; `_MARKER_SYMBOL` and `DEFAULT_COLORS` are shared with `plotly/scatter.py`
- `plotly/scatter.plot()` — plotly scatter equivalent; `_add_scatter_trace` is the composable primitive used by the CLI
- `plotly/overlay.overlay()` — multi-histogram overlay returning a single `go.Figure`
- `terminal/` — alternative backend with the same `plot()` / `overlay()` entry points (histograms only; scatter not supported)

### Resources (`resources/<target>/`)
Each target (e.g. `odd`, `sd`) contains `colors.json` (4-color palette) and logo assets. `StyleSet.load(target)` is the only consumer of `colors.json`.

## Developer guide

**Always run `uv run ruff check unrooted/` and `uv run pyright` before committing. Fix all errors before creating a commit.**

Branch naming: `feat-<topic>`, `fix-<topic>`, `chore-<topic>`.

Test files follow: `test_core_<module>.py`, `test_io_<backend>_<module>.py`, `test_plot_<backend>_<module>.py`.

Coding style: PEP 8 enforced by Ruff; static types checked by pyright (Python 3.11+).
