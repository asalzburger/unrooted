# I/O

Histogram readers return a [`Histogram`](core.md#histogram); `load_scatter`
returns [`ScatterData`](core.md#scatterdata). ROOT and boost-histogram readers
share the histogram type so their outputs are interchangeable downstream.

---

## ROOT backend (`unrooted.io.root`)

Functions for reading ROOT files via [uproot](https://uproot.readthedocs.io/).
No ROOT installation required.

All four functions below are public exports of `unrooted.io.root`.
`load` accepts TH1, TH2, and TProfile; `load_efficiency` accepts separate
unweighted passed/total TH1s. TH3, TProfile2D, and direct TEfficiency loading
are unsupported. Branch readers accept numeric scalars, vectors, and nested
jagged arrays; paired branches must be broadcast-compatible.
See [selection and memory behavior](../user-guide/loading-root.md).

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

Both functions are public exports of `unrooted.io.boost`. Numeric Regular,
Variable, and Integer axes are supported. `load` accepts count storages,
Weight, and Mean; efficiency conversion accepts only unweighted counts.
Categorical/Boolean axes and WeightedMean are rejected. See the
[storage table](../user-guide/loading-boost.md).

### load

::: unrooted.io.boost.reader.load

### load_efficiency

::: unrooted.io.boost.reader.load_efficiency
