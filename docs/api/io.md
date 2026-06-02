# I/O

All I/O functions return a [`Histogram`](core.md#histogram).  Two backends are
available — they share the same output type so histograms from either source are
interchangeable downstream.

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

---

## boost-histogram backend (`unrooted.io.boost`)

Functions for converting in-memory
[`boost-histogram`](https://boost-histogram.readthedocs.io/) objects.

### load

::: unrooted.io.boost.reader.load

### load_efficiency

::: unrooted.io.boost.reader.load_efficiency
