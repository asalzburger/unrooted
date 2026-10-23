# Core

Import `Axis` from `unrooted.core`, and `Histogram` / `ScatterData` from
`unrooted` or `unrooted.core`. Constructors validate inputs; arrays remain
mutable. See [data contracts](../user-guide/histograms.md) for NaNs, flow bins,
and ownership, and [architecture](../architecture.md) for uncertainty semantics.

## Histogram

::: unrooted.core.histogram.Histogram

## Axis

::: unrooted.core.axis.Axis

## ScatterData

Flat paired coordinates, labels, and sampling provenance. `source_points`
counts flattened pairs before sampling; `sample_seed` records the requested
random seed; `sampled` reports whether points were actually discarded.
Neither graphical backend silently samples this object.

::: unrooted.core.scatter.ScatterData
