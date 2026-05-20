# Logos & Stamps

## Stamping a detector logo

`stamp()` overlays a detector logo on any matplotlib axes.

```python
from unrooted.plot.mpl import plot, stamp

ax = plot(h)
stamp(ax, "odd")   # OpenDataDetector logo, upper-right corner
```

### Available targets

| `logo` | Description |
|--------|-------------|
| `"odd"` | OpenDataDetector |
| `"sd"` | Super Duper sample detector |

### Logo variants

| `variant` | Description |
|-----------|-------------|
| `"full"` (default) | Full-colour logo with text |
| `"line"` | Compact line-art version |

### Placement

```python
stamp(ax, "odd", loc="upper right")   # default
stamp(ax, "odd", loc="upper left")
stamp(ax, "odd", loc="lower right")
stamp(ax, "odd", loc="lower left")
```

### Size and opacity

```python
stamp(ax, "odd", zoom=0.12)    # logo width as fraction of axes width
stamp(ax, "odd", alpha=0.6)    # semi-transparent
```

---

## Logo resources

Logos live in `resources/{target}/`.  Each target has:

| File | Description |
|------|-------------|
| `*_light.png` / `*.png` | Full logo |
| `*_light_line.png` / `*_line.png` | Line variant |
| `colors.json` | Four-color palette |
| `stylesheet.png` | Auto-generated palette preview |

---

## Generating palette previews

`generate_stylesheet()` renders all four styles on synthetic Gaussian histograms
and saves a PNG you can use to review the palette.

```python
from unrooted.plot.mpl import generate_stylesheet

path = generate_stylesheet("odd")          # → resources/odd/stylesheet.png
path = generate_stylesheet("sd", "/tmp/sd_preview.png")  # custom output
```

The function returns the path of the saved file.
