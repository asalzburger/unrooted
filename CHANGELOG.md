# Changelog

## 0.1.0rc1 — release candidate (unreleased)

First production-readiness candidate. Artifacts are prepared for GitHub
Releases; no PyPI publication is implied by this version.

### Added

- Matplotlib and Plotly `stack()` APIs and `HistogramStyle.as_stack()` for
  nonnegative additive 1D histograms, with independent total uncertainties,
  missing-bin gaps, executable examples, and installed-wheel coverage.
- Installable palettes and logos, public scatter plotting/composition APIs,
  and Matplotlib, optional Plotly, and terminal workflows.
- Entry selection, chunked ROOT branch loading, explicit scatter limits, and
  seeded uniform sampling with provenance.
- Linux/macOS CI across CPython 3.11–3.15, minimum dependency checks, installed
  artifact tests, executable introductory examples, and strict documentation.
- MIT license, a single version source, compatibility policy, and a release
  rehearsal that validates distributions before preparing a draft release.

### Corrected

- Plotly uncertainty bands split at missing values, including zero-denominator
  ratio bins, instead of drawing misleading filled polygons across gaps.
- Profile binning includes the final right edge. Branch profile variance uses
  stable centered accumulation instead of subtracting large second moments.
- Packaged resources work outside the checkout; generated previews go to a
  writable destination.
- Plot labels, ratio styles, CLI source prefixes and file labels, diagnostics,
  and exit codes now follow their documented contracts.

### Compatibility changes from earlier source snapshots

- Constructors and readers reject invalid shapes, numeric edges, negative
  variances, and inconsistent spread bounds. Ratios require identical edges.
- Efficiencies use Wilson intervals (68.27% by default), retain binomial
  variance separately, and use NaN for zero-total bins. Only unweighted 1D
  integer counts are accepted; unsupported inputs fail explicitly.
- Boost categorical/Boolean axes and WeightedMean storage are rejected.
- CLI invalid arguments exit 2; operational failures exit 1. Unsupported
  option combinations are errors. Sampling is never implicit.
- Runtime floors: NumPy 2.0, Uproot 5.6.0, Awkward 2.8.0, Matplotlib 3.8.4,
  boost-histogram 1.7.2, and optional Plotly 5.24.1; Python 3.11 or newer.
- Contributor dependencies use locked `dev`/`docs` groups; Plotly remains a
  runtime extra.

### Known limitations

- ROOT TH3, TProfile2D, and direct TEfficiency loading, weighted efficiencies,
  and weighted boost profiles are unsupported.
- Branch profiles use population variance and observed extrema; boost Mean
  profiles retain their sample correction and standard-deviation bands.
- Scatter without an explicit limit retains every selected pair. Entry chunk
  limits are not byte/RSS guarantees for arbitrary jagged events or baskets.
- Terminal plotting is histogram-only. Plotly HTML export is tested; static
  export additionally needs Kaleido and a compatible browser and is outside
  the release validation matrix.
- Windows, unlisted Python/platform combinations, and future dependencies
  are not covered by the support promise. No long-term support or response-time
  commitment is made.
