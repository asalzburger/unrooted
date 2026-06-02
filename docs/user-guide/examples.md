# Examples

!!! note "Auto-generated"
    Matplotlib and Plotly outputs are regenerated automatically each time the
    documentation is built.  The build fails if any example cannot be produced,
    ensuring the examples always reflect the current state of the library.
    Terminal output is rendered from the same ROOT data at build time.

The examples below use the **ODD** colour palette from
[`StyleSet`][unrooted.plot.style_set.StyleSet].  ROOT examples use
[`unrooted.io.root`][unrooted.io.root.reader.load]; boost-histogram examples
use [`unrooted.io.boost`][unrooted.io.boost.reader.load].  Both produce the
same [`Histogram`][unrooted.core.histogram.Histogram] type and are passed to
the same plot functions.

---

## 1D histogram

=== "Matplotlib"

    ![hx — ODD style palette](../assets/examples/mpl_hx_styled.png)

=== "Plotly (interactive)"

    <iframe
      src="../../assets/examples/plotly_hx_styled.html"
      width="100%"
      height="440"
      frameborder="0"
      scrolling="no">
    </iframe>

=== "Terminal"

    ```
    --8<-- "assets/examples/terminal_hx.txt"
    ```

---

## Overlay with ratio panel

=== "Matplotlib"

    ![Overlay hx vs hy with ratio](../assets/examples/mpl_overlay_ratio.png)

=== "Plotly (interactive)"

    <iframe
      src="../../assets/examples/plotly_overlay_ratio.html"
      width="100%"
      height="580"
      frameborder="0"
      scrolling="no">
    </iframe>

=== "Terminal"

    ```
    --8<-- "assets/examples/terminal_overlay_ratio.txt"
    ```

---

## 2D histogram

=== "Matplotlib"

    ![hxy — 2D heatmap](../assets/examples/mpl_hxy.png)

=== "Plotly (interactive)"

    <iframe
      src="../../assets/examples/plotly_hxy.html"
      width="100%"
      height="500"
      frameborder="0"
      scrolling="no">
    </iframe>

---

## TProfile with spread

Loaded from a ROOT `TProfile` object.  `values` are per-bin means; the shaded
band shows mean ± σ_y (standard deviation of the profiled quantity); error bars
show ±SE (standard error of the mean).

=== "Single profile"

    ![TProfile with spread band](../assets/examples/mpl_profile.png)

=== "Overlay with ratio"

    ![TProfile overlay](../assets/examples/mpl_profile_overlay.png)

---

## Efficiency histogram

Loaded via `load_efficiency()` from a pair of `TH1` histograms
(passed / total).  Values are per-bin efficiency; the shaded band and error
bars show the Gaussian ±σ confidence interval, clamped to [0, 1].

=== "Matplotlib"

    ![Efficiency with CI band](../assets/examples/mpl_efficiency.png)

---

## Named style presets

All five presets applied to the same histogram with the ODD primary color.

![Named style presets](../assets/examples/mpl_style_presets.png)

| Preset | Line | Marker | Fill | Errors | Spread |
|--------|------|--------|------|--------|--------|
| `as_hist()` | solid | – | ✓ | bar | – |
| `as_line()` | solid | – | – | – | – |
| `as_markers()` | – | ○ | – | bar | – |
| `as_efficiency()` | – | ○ | – | bar | band |
| `as_profile()` | solid | – | – | bar | band |

---

---

## boost-histogram: profile

Converted from a `boost_histogram.Histogram` with `Mean` storage via
[`unrooted.io.boost.load`][unrooted.io.boost.reader.load].  `values` are
per-bin means; the shaded band shows mean ± σ_y (standard deviation of
individual measurements); error bars show ±SE (standard error of the mean).

![boost-histogram profile](../assets/examples/mpl_boost_profile.png)

---

## boost-histogram: efficiency

Converted via
[`unrooted.io.boost.load_efficiency`][unrooted.io.boost.reader.load_efficiency]
from a pair of `Double`-storage histograms (accepted, total).  The shaded band
and error bars show the Gaussian ±σ confidence interval, clamped to [0, 1].

![boost-histogram efficiency](../assets/examples/mpl_boost_efficiency.png)

---

## Ratio panel with styled B

The ratio panel inherits the line color, line style, width, and error display
from B's `HistogramStyle`.  Here B is drawn with a dashed line.

![Ratio panel with styled B](../assets/examples/mpl_ratio_styled.png)
