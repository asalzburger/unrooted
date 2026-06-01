# Command-line interface

`unrooted` ships a `unrooted` command that lets you load and plot ROOT histograms
directly from the shell — no Python script required.

```bash
unrooted --input file.root --draw hist:hx --output plot.png
```

---

## Installation

The command is registered automatically when the package is installed:

```bash
pip install unrooted
# or
uv add unrooted
```

After installation `unrooted --help` should be available on your PATH.

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
  --draw branch:myTree:eta:pt \
  --add spread_band \
  --output eta_vs_pt.png
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
| `branch:tree:x:y_branch` | `load_branch(file, tree, x, y)` | `as_profile()` |

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

---

## Multi-file × multi-draw rules

| `--input` count | `--draw` count | Behaviour |
|-----------------|----------------|-----------|
| 1 | N | load N histograms from the single file |
| N | 1 | load the same key from every file; label = filename stem |
| N | N | zip: `(file_i, draw_i)` |
| N | M ≠ N, M > 1 | error |

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
| `ratio` | ratio panel below main plot (mpl / plotly) |
| `error_bar` | error display mode → bar caps at bin centres |
| `error_band` | error display mode → step-shaped filled band |
| `error_continuous` | error display mode → smooth filled band |
| `error_none` | suppress error display |
| `spread_bar` | spread display mode → bar caps |
| `spread_band` | spread display mode → step-shaped filled band |
| `spread_continuous` | spread display mode → smooth filled band |
| `spread_none` | suppress spread display |

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
| `plotly` | interactive HTML/image | `.html` for interactive; requires `pip install 'unrooted[plotly]'` |
| `terminal` | unicode to stdout | no output file; `--max-lines N` controls height |

---

## Output and display

| Flags | Behaviour |
|-------|-----------|
| `--output FILE` | save figure to file |
| `--show` | open interactive window even when `--output` is given |
| *(neither)* | open interactive window (equivalent to `--show`) |

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
