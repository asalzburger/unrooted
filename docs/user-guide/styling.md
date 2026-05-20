# Styles & Themes

## `HistogramStyle`

`HistogramStyle` is a dataclass that fully describes the visual appearance of a
single 1D histogram.  Every field has a sensible default so you only need to
specify what you want to change.

```python
from unrooted.plot import HistogramStyle

style = HistogramStyle(
    line_color="#1A4F8A",
    line_style="-",
    line_width=1.5,
    marker="o",
    marker_size=5.0,
    fill_alpha=0.15,     # None → no fill
    error_display="bar", # "bar" | "band" | None
    spread_display=None, # "bar" | "band" | None
)
```

### Color fields

All `*_color` fields accept any matplotlib color spec: named string (`"blue"`),
hex (`"#1A4F8A"`), or RGBA tuple (`(0.1, 0.31, 0.54, 1.0)`).
`None` means *inherit the automatic color-cycle color*.

### Line

| Field | Default | Effect |
|-------|---------|--------|
| `line_color` | `None` | Step-function color (`None` = auto cycle) |
| `line_style` | `"-"` | `"-"`, `"--"`, `":"`, `"-."`, or `None` (no line) |
| `line_width` | `1.5` | Line width in points |
| `line_alpha` | `1.0` | Opacity |

### Marker

| Field | Default | Effect |
|-------|---------|--------|
| `marker` | `None` | Marker at bin centres; `None` = no markers |
| `marker_color` | `None` | Defaults to `line_color` |
| `marker_size` | `5.0` | Marker size in points |

### Fill

| Field | Default | Effect |
|-------|---------|--------|
| `fill_alpha` | `None` | `None` = no fill; float = opacity of shaded area |
| `fill_color` | `None` | Defaults to `line_color` |
| `fill_hatch` | `None` | Hatch pattern, e.g. `"/"`, `"x"`, `"."` |

### Error bars / bands

| Field | Default | Effect |
|-------|---------|--------|
| `error_display` | `"bar"` | `"bar"` (±√var error bars), `"band"` (shaded), `None` |
| `error_color` | `None` | Defaults to `line_color` |
| `error_alpha` | `0.4` | Opacity for the band mode |
| `error_capsize` | `2.0` | Cap size (bar mode only) |

### Spread (profile histograms)

| Field | Default | Effect |
|-------|---------|--------|
| `spread_display` | `None` | `"bar"` or `"band"` to show `spread_min`/`spread_max` |
| `spread_color` | `None` | Defaults to `line_color` |
| `spread_alpha` | `0.15` | Opacity (band mode) |

---

## `StyleSet` — coordinated palettes

`StyleSet` loads a four-color palette from `resources/{target}/colors.json` and
assembles four ready-to-use `HistogramStyle` objects.

```python
from unrooted.plot import StyleSet

ss = StyleSet.load("odd")  # or "sd"

print(ss.name)        # "odd"
print(ss.colors)      # ['#1A4F8A', '#E8921A', '#5B9BD5', '#525C62']
print(len(ss))        # 4
```

Access styles by index — indices wrap cyclically:

```python
ss[0]   # primary   – solid line, circle marker, fill
ss[1]   # secondary – solid line, square marker, fill
ss[2]   # tertiary  – dashed,     triangle marker, no fill
ss[3]   # quaternary– dashed,     diamond marker,  no fill
ss[4]   # same as ss[0]
```

### Using with `overlay()`

```python
from unrooted.plot.mpl import overlay
from unrooted.plot import StyleSet

ss = StyleSet.load("odd")
overlay([h1, h2, h3, h4],
        labels=["sig", "bkg", "data", "MC"],
        styles=[ss[i] for i in range(4)])
```

### Available palettes

| Target | Primary | Secondary | Description |
|--------|---------|-----------|-------------|
| `"odd"` | `#1A4F8A` deep navy | `#E8921A` warm amber | OpenDataDetector |
| `"sd"` | `#BF1565` deep magenta | `#557A1C` forest green | Super Duper |

### Palette previews

=== "ODD"
    ![ODD stylesheet](../assets/odd_stylesheet.png)

=== "SD"
    ![SD stylesheet](../assets/sd_stylesheet.png)

### Generating stylesheet previews

```python
from unrooted.plot.mpl import generate_stylesheet

generate_stylesheet("odd")  # writes resources/odd/stylesheet.png
generate_stylesheet("sd")   # writes resources/sd/stylesheet.png
```
