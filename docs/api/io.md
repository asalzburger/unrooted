# I/O

Histogram readers return a [`Histogram`](core.md#histogram); `load_scatter`
returns [`ScatterData`](core.md#scatterdata). ROOT and boost-histogram readers
share the histogram type so their outputs are interchangeable downstream.

---

## ROOT backend (`unrooted.io.root`)

Functions for reading ROOT files via [uproot](https://uproot.readthedocs.io/).
No ROOT installation required.

### load

::: unrooted.io.root.reader.load

### load_efficiency

::: unrooted.io.root.reader.load_efficiency

### load_branch

::: unrooted.io.root.tree.load_branch

### load_scatter

::: unrooted.io.root.tree.load_scatter

---

## boost-histogram backend (`unrooted.io.boost`)

Functions for converting in-memory
[`boost-histogram`](https://boost-histogram.readthedocs.io/) objects.

### load

::: unrooted.io.boost.reader.load

### load_efficiency

::: unrooted.io.boost.reader.load_efficiency
