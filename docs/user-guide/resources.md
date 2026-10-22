# Resources

Palettes and logos are bundled in `unrooted/resources/` and installed with the
package. They give plots a consistent, experiment-specific look without
requiring a resource directory in the current working directory.

---

## Available targets

### sd — Super Duper (sample detector)

Used in unit tests and examples.

<div style="display:flex; gap:3em; align-items:center; padding:1em 0;">
  <div style="text-align:center">
    <img src="../../assets/sd_logo.svg" alt="SD full logo" width="180"/>
    <p><em>full</em></p>
  </div>
  <div style="text-align:center">
    <img src="../../assets/sd_logo_line.svg" alt="SD line logo" width="180"/>
    <p><em>line</em></p>
  </div>
</div>

### odd — OpenDataDetector

Real detector logos from the [OpenDataDetector project](https://github.com/acts-project/OpenDataDetector).

<div style="display:flex; gap:3em; align-items:center; padding:1em 0;">
  <div style="text-align:center">
    <img src="../../assets/odd_logo.svg" alt="ODD full logo" width="220"/>
    <p><em>full</em></p>
  </div>
  <div style="text-align:center">
    <img src="../../assets/odd_logo_line.svg" alt="ODD line logo" width="220"/>
    <p><em>line</em></p>
  </div>
</div>

---

## Color palettes

`colors.json` defines a four-color palette that `StyleSet` reads automatically:

```json
{
  "name": "odd",
  "description": "OpenDataDetector — steel blue, vivid orange, teal/seafoam, dark crimson red",
  "colors": ["#3A6FA8", "#E8721A", "#5BB8A8", "#9B2020"]
}
```

Load it with:

```python
from unrooted.plot import StyleSet
from unrooted.plot.mpl import plot

ss = StyleSet.load("odd")   # reads the installed ODD palette
ax = plot(h, style=ss[0])   # first of the four coordinated styles
```

See [Styles & Themes](styling.md) for the full `StyleSet` API.

---

## Logo files

Each target ships PNG and SVG variants of both the full-colour and line-art logos.
They are available for use in post-processing workflows or custom plot annotations.

```
unrooted/resources/
├── sd/
│   ├── super_duper.png          full logo
│   ├── super_duper.svg
│   ├── super_duper_line.png     compact line-art variant
│   ├── super_duper_line.svg
│   ├── colors.json              four-color palette
│   └── stylesheet.png           auto-generated palette preview
└── odd/
    ├── odd_tech_light.png
    ├── odd_tech_light.svg
    ├── odd_tech_light_line.png
    ├── odd_tech_light_line.svg
    ├── colors.json
    └── stylesheet.png
```

---

## Reading installed logo files

Use `importlib.resources` to access assets in an installed package:

```python
from importlib.resources import as_file, files
import matplotlib.pyplot as plt

logo = files("unrooted").joinpath("resources", "odd", "odd_tech_light.png")
with as_file(logo) as logo_path:
    image = plt.imread(logo_path)
```

The `as_file` context provides a filesystem path for APIs that require one.
Use that path inside the context, since it may refer to a temporary file.

## Generating palette previews

```python
from unrooted.plot.mpl import generate_stylesheet

generate_stylesheet("odd")  # writes ./odd_stylesheet.png
generate_stylesheet("sd", "sd_preview.png")  # explicit destination
```

The default output is `<target>_stylesheet.png` in the current working
directory. This replaces the previous default of writing beside the palette
inside `resources/<target>/`. Packaged assets are read as inputs; preview
generation writes to the selected destination. Its parent directory must
already exist.

## Adding a new target

In a source checkout, create a sub-directory under `unrooted/resources/` and
add a `colors.json` with four hex codes:

```json
{
  "name": "my_detector",
  "description": "Short description",
  "colors": ["#hex1", "#hex2", "#hex3", "#hex4"]
}
```

`StyleSet.load("my_detector")` and `generate_stylesheet("my_detector")` will then
work in the editable development installation. Rebuild and reinstall the
package to distribute the new target. Logo files are optional.
