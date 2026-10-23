# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

```bash
# Install locked contributor tools, docs, and optional Plotly
uv sync --locked --group docs --extra plotly

# Run all tests
uv run --no-sync python -I -m pytest -q

# Run a single test file
uv run --no-sync python -I -m pytest tests/unit_tests/test_core_histogram.py

# Run a single test by name
uv run --no-sync python -I -m pytest tests/unit_tests/test_core_histogram.py::test_histogram_errors

# Lint
uv run --no-sync ruff check .

# Type check
uv run --no-sync python -I -m pyright

# Run an example script
uv run --no-sync python -I tests/documentation/smoke.py

# Generate stylesheet previews in the current directory (after changing colors.json)
uv run python -c "from unrooted.plot.mpl.stylesheet import generate_stylesheet; generate_stylesheet('odd'); generate_stylesheet('sd')"
```

The full setup, supported Python/dependency versions, minimum-version checks,
strict documentation build, and wheel rehearsal are documented in
[the contributor guide](docs/contributing.md). Keep `uv.lock` committed;
development tools use dependency groups, while `plotly` is a package extra.

## Architecture

The library has three independent layers that compose through `Histogram`
and `ScatterData`:

**I/O → Core → Plot**

### Core (`unrooted/core/`)
- `Axis`: bin edges + label; computed properties `centers`, `widths`, `n_bins`
- `Histogram`: numpy-backed dataclass — `axes`, `values`, `variances`, `overflow`, and optional `spread_min`/`spread_max` (populated for TProfile and efficiency histograms)
- `ScatterData`: paired coordinates and optional sampling provenance

### I/O (`unrooted/io/<backend>/`)
Histogram readers return `Histogram`; scatter readers return `ScatterData`.
ROOT readers use Uproot, and boost readers convert in-memory boost-histogram objects:
- `reader.load(path, key)` — reads TH1/TH2/TProfile via uproot; TProfile populates `spread_min`/`spread_max` as mean ± σ_y
- `reader.load_efficiency(path, pass_key, total_key)` — unweighted count efficiency with Wilson intervals and separate binomial variance
- `tree.load_branch(...)` — count or population-profile histogram with entry selection and chunked accumulation
- `tree.load_scatter(...)` — points with entry selection, an optional explicit limit, and opt-in seeded sampling

### Plot (`unrooted/plot/`)
- `style.HistogramStyle` — single dataclass controlling line, fill, marker, error, and spread rendering
- `style_set.StyleSet` — loads packaged `unrooted/resources/{target}/colors.json` through `importlib.resources` and combines four palette colors with four `_STYLE_TEMPLATES` (line style + marker combinations) into a ready-to-use `styles` list; index wraps cyclically
- `mpl/histogram.plot()` — dispatches to `_plot_1d`, `_plot_1d_styled`, or `_plot_2d`; `_plot_1d_styled` renders in five ordered layers: fill → line → markers → errors → spread
- `mpl/overlay.overlay()` — multi-histogram overlay with optional ratio panel
- `mpl.stack()` / `plotly.stack()` — nonnegative additive 1D stacks with shared validation/accumulation in `_stack.py` and an independent total uncertainty band
- `mpl.plot_scatter()` / `mpl.overlay_scatter()` — public point-cloud plotting and composition
- `mpl/_range._draw_range()` — shared primitive for both error bars and filled bands, used by both the histogram and overlay modules
- `mpl/stylesheet.generate_stylesheet()` — renders a palette preview PNG; called as part of resource updates
- `plotly/histogram.plot()` — plotly equivalent; `_MARKER_SYMBOL` and `DEFAULT_COLORS` are shared with `plotly/scatter.py`
- `plotly.plot_scatter()` / `plotly.overlay_scatter()` — public point-cloud plotting and figure/subplot composition
- `plotly/overlay.overlay()` — multi-histogram overlay returning a single `go.Figure`
- `terminal/` — alternative backend with the same `plot()` / `overlay()` entry points (histograms only; scatter not supported)

### Resources (`unrooted/resources/<target>/`)
Each target (e.g. `odd`, `sd`) contains `colors.json` (4-color palette) and logo assets. `StyleSet.load(target)` is the only consumer of `colors.json`.

`generate_stylesheet(target)` writes `<target>_stylesheet.png` in the current
working directory. Pass an explicit output path to update a preview asset.

## Developer guide

**Always run `uv run --no-sync ruff check .` and
`uv run --no-sync python -I -m pyright` before committing.
Fix all errors before creating a commit.**

Tests share a fixture in `tests/conftest.py` that closes all Matplotlib figures
and restores plotting settings after each case. Write generated files to
temporary directories. Documentation gallery assets are generated outside
the source tree.

Branch naming: `feat-<topic>`, `fix-<topic>`, `chore-<topic>`.

Test files follow: `test_core_<module>.py`, `test_io_<backend>_<module>.py`, `test_plot_<backend>_<module>.py`.

Coding style: PEP 8 enforced by Ruff; static types checked by pyright (Python 3.11+).
