# Command-line interface

`unrooted` ships a `unrooted` command that lets you load and plot ROOT histograms
directly from the shell — no Python script required.

```bash
unrooted --input file.root --draw hist:hx --output plot.png
```

---

## Installation

The command is registered automatically when the package is installed. Follow
[Getting Started](../getting-started.md#installation), or run from a source
checkout:

```bash
python -m pip install .
# or
uv sync --no-dev
```

After a pip installation, `unrooted --help` should be available on your PATH.
With uv, use `uv run unrooted --help` and prefix the commands below with `uv run`.

---

## Quick examples

### Single histogram

```bash
unrooted \
  --input data.root \
  --draw hist:hx \
  --output hx.png
```

### Overlay with ratio panel

```bash
unrooted \
  --input data.root \
  --draw hist:hx hist:hy \
  --label "signal" "background" \
  --add ratio \
  --output overlay.svg
```

### Profile histogram from a subdirectory

```bash
unrooted \
  --input data.root \
  --source SeedingPerformance \
  --draw prof:nSeeds:eta \
  --add spread_continuous \
  --palette sd \
  --output profile.png
```

The `--source` prefix is prepended to every key, so the full ROOT path above
is `SeedingPerformance/nSeeds/eta`.  Colons inside the key path act as path
separators, so `prof:nSeeds:eta` and `prof:nSeeds/eta` are equivalent.

### Efficiency histogram

```bash
unrooted \
  --input eff.root \
  --draw eff:h_passed:h_total \
  --title "Track reconstruction efficiency" \
  --output eff.svg
```

### Overlay the same key from multiple files

When multiple `--input` files are given with a single `--draw` spec, each file
is loaded separately and overlaid.  The filename stem is used as the label.

```bash
unrooted \
  --input run1.root run2.root run3.root \
  --draw hist:hx \
  --add ratio \
  --output comparison.png
```

### TTree branch

```bash
unrooted \
  --input data.root \
  --draw branch:myTree:eta \
  --n-bins 50 \
  --output eta.png
```

Profile from two branches:

```bash
unrooted \
  --input data.root \
  --draw branch:myTree:prof:eta:pt \
  --add spread_band \
  --output eta_vs_pt.png
```

### Scatter plot from a TTree

```bash
unrooted \
  --input data.root \
  --draw branch:myTree:scatter:v_eta:t_X0 \
  --output scatter.png
```

The plotly backend is also supported for scatter plots, enabling interactive
zoom and hover:

```bash
unrooted \
  --input data.root \
  --draw branch:myTree:scatter:v_eta:t_X0 \
  --backend plotly \
  --output scatter.html
```

### Terminal backend

Useful for quick inspection in headless or SSH environments:

```bash
unrooted --input data.root --draw hist:hx --backend terminal
```

---

## Draw spec format

The `--draw` argument takes one or more *draw specs* separated by spaces or
repeated `--draw` flags.  Both forms are equivalent:

```bash
--draw hist:hx hist:hy
--draw hist:hx --draw hist:hy
```

### Spec syntax

| Spec | Loads via | Auto style |
|------|-----------|------------|
| `hist:key` | `load(file, key)` | `as_hist()` |
| `th2:key` | `load(file, key)` | `as_hist()` (2D heatmap) |
| `prof:key` | `load(file, key)` | `as_profile()` |
| `eff:pass_key:total_key` | `load_efficiency(file, pass, total)` | `as_efficiency()` |
| `branch:tree:x_branch` | `load_branch(file, tree, x)` | `as_hist()` |
| `branch:tree:prof:x:y` | `load_branch(file, tree, x, y)` | `as_profile()` |
| `branch:tree:scatter:x:y` | `load_scatter(file, tree, x, y)` | `as_scatter()` |

Type aliases: `hist` = `th1` = `h1`; `th2` = `h2`; `prof` = `profile` = `tprofile`;
`eff` = `efficiency`; `branch` = `tree`.

Path separators inside a key can be `/` (ROOT convention) or `:` — both are
converted to `/`:

```bash
--draw prof:dir/subdir/hist     # explicit slash
--draw prof:dir:subdir:hist     # colons → joined as dir/subdir/hist
```

### `--source`

`--source KEY` prepends a common path prefix to every histogram key.  Useful
when all objects live under the same ROOT directory:

```bash
unrooted --input f.root --source MyDir --draw hist:h1 hist:h2
# loads MyDir/h1 and MyDir/h2
```

`--source` is **not** prepended to the tree name in `branch:` specs.
Use an explicit path such as `branch:MyDir/tree:scatter:x:y` for a nested
tree. Leading and trailing slashes on the source prefix are normalized.

---

## Multi-file × multi-draw rules

| `--input` count | `--draw` count | Behaviour |
|-----------------|----------------|-----------|
| 1 | N | load N histograms from the single file |
| N | 1 | load the same key from every file; label = filename stem |
| N | N | zip: `(file_i, draw_i)` |
| N | M ≠ N, M > 1 | error |

For one file or zipped files/specs, labels use the final draw key component
(the passed key for efficiencies, the x branch for counts, or the y branch
for profiles/scatter). For multiple files and one spec, filename stems take
priority over the loaded histogram name. `--label` overrides these defaults
and must supply exactly one label per dataset, including single-dataset plots.

---

## `--add` options

`--add` tokens modify the plot after the auto-style is chosen.  They can be
space-separated, colon-joined, or spread across multiple `--add` flags:

```bash
--add ratio spread_continuous           # two tokens, one flag
--add ratio:spread_continuous           # colon-joined, identical result
--add ratio --add spread_continuous     # two flags, identical result
```

| Token | Effect |
|-------|--------|
| `ratio` | ratio panel below main plot (all histogram backends; at least two 1D histograms) |
| `error_bar` | error display mode → bar caps at bin centres |
| `error_band` | error display mode → step-shaped filled band |
| `error_continuous` | error display mode → smooth filled band |
| `error_none` | suppress error display |
| `spread_bar` | spread display mode → bar caps |
| `spread_band` | spread display mode → step-shaped filled band |
| `spread_continuous` | spread display mode → smooth filled band |
| `spread_none` | suppress spread display |

Choose at most one `error_*` mode and one `spread_*` mode. Conflicting modes
raise an argument error; order does not select a winner. Ratios require
exactly matching edges. Matplotlib and Plotly ratios inherit the numerator's
line, marker, and error settings; spread and main-panel fill are not propagated
to ratios. `--add error_none` suppresses ratio errors as well as main errors.
Scatter plots have no ratio, error, or spread display.

---

## Style and palette

### `--style PRESET`

Override the auto-selected style preset:

| Preset | Based on |
|--------|----------|
| `hist` | `HistogramStyle.as_hist()` — fill + error bars |
| `line` | `HistogramStyle.as_line()` — step line only |
| `markers` | `HistogramStyle.as_markers()` — markers + errors |
| `efficiency` | `HistogramStyle.as_efficiency()` — markers + spread band |
| `profile` | `HistogramStyle.as_profile()` — line + spread band |
| `scatter` | `HistogramStyle.as_scatter()` — tiny point markers |

### `--palette`

| Name | Description |
|------|-------------|
| `odd` (default) | OpenDataDetector: steel blue, orange, teal, crimson |
| `sd` | Super Duper: teal, purple, pink, yellow |

Colors cycle automatically across multiple histograms.

---

## Backends

| `--backend` | Output | Notes |
|-------------|--------|-------|
| `mpl` (default) | matplotlib figure | saved with `--output`; supports `.png/.svg/.pdf` |
| `plotly` | interactive HTML/image | `.html` for interactive; install the optional Plotly backend as described in Getting Started |
| `terminal` | unicode to stdout | no output file; `--max-lines N` controls height |

| Capability / option | Matplotlib | Plotly | Terminal |
| --- | --- | --- | --- |
| Single 1D histogram / overlay / ratio | Yes | Yes | Yes, up to 4 datasets and 100 bins |
| Single 2D heatmap | Yes | Yes | Unsupported |
| Scatter / scatter overlay | Yes | Yes | Unsupported |
| Error and spread display | Yes | Yes | Omitted; explicit display requests rejected |
| Title, x label, legend labels | Yes | Yes | Yes |
| Y label and axis limits | Yes | Yes | Unsupported |
| Style, palette, marker, line overrides | Yes | Yes | Unsupported |
| Fixed ratio y range | Yes | Yes | Unsupported |
| `--output` / `--show` | Yes | Yes | Unsupported; writes to stdout |
| `--max-lines` | Unsupported | Unsupported | Integer ≥ 5 |

Single 2D heatmaps accept title, axis labels, and limits, but do not accept
`--label`, `--add`, or 1D style overrides. Scatter supports `--style scatter`
and marker overrides; line styles and histogram style presets are rejected.
`--n-bins` and `--branch-range` require a count/profile branch spec. Ranges
must be finite with `MIN < MAX`, and `--n-bins` must be positive. Unsupported
combinations raise an error instead of silently discarding flags.

Plotly HTML output is self-contained and needs only the Plotly extra. Static
images additionally need Kaleido; Kaleido 1+ requires a compatible installed
Chrome or Chromium. See [Plotly's export setup](https://plotly.com/python/static-image-export/).
These optional tools are not installed by `unrooted[plotly]`. Export failures
identify the destination and suggest HTML when the static export setup fails.

---

## Output and display

| Flags | Behaviour |
|-------|-----------|
| `--output FILE` | save figure to file |
| `--show` | open interactive window even when `--output` is given |
| *(neither)* | open interactive window (equivalent to `--show`) |

These display rules apply to graphical backends. Terminal output always goes
to stdout; redirect it with your shell to save a text preview.

For branch draw specs, use `--entry-start N` and `--entry-stop N` to select
tree entries before broadcasting or flattening. The start is included and
the stop is excluded; defaults are zero and the end of the tree. Bounds are
nonnegative, ordered, and clipped to the tree length. The selection applies
independently to each input file. These flags are rejected when the command
has no branch spec; stored histograms are unaffected.

```bash
unrooted --input data.root --draw branch:tree:scatter:x:y \
  --entry-start 1000 --entry-stop 2000 --output selected.png
```

`--step-size N` sets the maximum tree entries per chunk (default `100000`);
it requires a branch spec and is not a byte limit. For scatter datasets,
`--max-points N` explicitly limits retained flattened pairs per dataset.
The default policy `--sampling error` fails on overflow. Select uniform
sampling explicitly, with a repeatable nonnegative seed:

```bash
unrooted --input data.root --draw branch:tree:scatter:x:y \
  --max-points 100000 --sampling random --seed 71 \
  --step-size 100000 --backend plotly --output sampled.html
```

`--sampling random` requires `--max-points`; `--seed` requires random sampling
and defaults to `0`. Sampling flags are rejected for histogram/profile specs.
No sampling happens without an explicit request. When points are removed,
the CLI reports retained/source pair counts and the seed on stderr. Point
counts are after event selection and broadcasting; returned points remain in
input order. See [loading memory and sampling](loading-root.md#chunking-and-memory)
for the memory model, statistical meaning, and reference measurements.

With ratios, `--xlabel` applies to the bottom axis and `--ylabel` / `--ylim`
apply to the main panel. `--ratio-range` controls only the ratio y-axis and
requires `--add ratio`. `--xlim` applies to the shared x range.

## Errors and exit codes

| Exit code | Meaning |
| --- | --- |
| `0` | Successful rendering/export, or `--help` |
| `2` | Invalid syntax, conflicting flags, or an unsupported option combination |
| `1` | Loading, plotting, optional dependency, display, or export failure |

Errors go to stderr with an `unrooted:` prefix and no traceback. Missing
files/keys and unsupported ROOT objects are loading errors. For example,
`th2:` with a 1D object or `prof:` with a plain count histogram fails clearly.
Invalid file/spec combinations and label counts are argument errors. Long
options must be spelled in full; the CLI does not accept abbreviations.

---

## All options

```
unrooted [-h] --input FILE [FILE ...] [--source KEY]
         --draw SPEC [SPEC ...] [--output FILE]
         [--add OPT [OPT ...]] [--label LABEL [LABEL ...]]
         [--backend {mpl,plotly,terminal}] [--palette {odd,sd}]
         [--style PRESET] [--show] [--title TEXT]
         [--xlim MIN MAX] [--ylim MIN MAX]
         [--n-bins N] [--branch-range LO HI]
         [--max-lines N]
```

Run `unrooted --help` for the full reference.

---

## Calling from Python

The same entry point is importable as a function, useful for notebooks or
scripted workflows:

```python
from unrooted.cli.main import main

main([
    "--input", "data.root",
    "--draw", "hist:hx", "hist:hy",
    "--label", "signal", "background",
    "--add", "ratio",
    "--output", "overlay.png",
])
```
