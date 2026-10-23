# unrooted production readiness roadmap

Prepare unrooted for dependable installation, analysis, and plotting while
preserving its I/O → core → plotting architecture. Work through the stages in
order, with focused changes, tests, and documentation at each stage.

The October 22, 2026 review found 370 passing tests and 79% line coverage on
macOS with Python 3.14.6. Package lint, type checking, distribution builds, and
a strict documentation build passed. Additional checks reproduced missing
wheel resources, incorrect profile binning, unstable variance calculations,
incompatible-bin ratios, invalid efficiency inputs, and CLI inconsistencies.

## Working together

- Implement one stage at a time. Split a stage into smaller pull requests when
  its changes can be reviewed independently.
- Keep tests and user-facing documentation with the behavior they describe.
- Bring statistical, compatibility, and release-policy decisions to the user
  with concrete options before implementing changes that depend on them.
- At each checkpoint, report the changed behavior, validation results,
  remaining limitations, and the next proposed step.
- Update this roadmap with completion evidence as work lands.

| Stage | Outcome | Status |
| --- | --- | --- |
| 1 | Installed distributions work outside the checkout | Complete |
| 2 | Profile calculations agree with numerical references | Complete |
| 3 | Data and statistical contracts are explicit and enforced | Complete |
| 4 | CLI and plotting backends honor their public contracts | Complete |
| 5 | Data loading has a tested resource envelope | Complete |
| 6 | CI and contributor setup reproduce supported configurations | Complete |
| 7 | A release candidate passes installation and documentation rehearsal | In validation |

## Stage 1 Installed distributions

- [x] Package palette files and required runtime assets; load them with
  `importlib.resources`.
- [x] Give stylesheet generation a writable output destination and make its
  tests use temporary directories.
- [x] Build an sdist, build a wheel from it, and install the wheel into a clean
  environment outside the checkout.
- [x] Add an installed-wheel CI check for both palettes, CLI help, terminal
  output, and a saved Matplotlib figure.
- [x] Fix the README plot and overlay examples and distinguish end-user
  installation from contributor setup.
- [x] Update the resource guide for the packaged asset layout and output paths.

**Completion:** a fresh wheel installation loads both palettes and runs the
documented basic workflows without depending on the repository or writing to
the installed package. The regression check runs in CI.

**Verification on October 22, 2026:** all 12 palette, logo, and preview files
retain their original contents and are present in the built wheel. Fresh
installations with only runtime dependencies passed the packaging smoke check
on macOS with Python 3.11.15 and 3.14.6. The README Python example passed
against the installed wheel. All 370 unit tests, package/changed-test lint,
package type checking, and a strict documentation build passed. The new
distribution and test CI jobs passed on
[PR 26](https://github.com/asalzburger/unrooted/pull/26), which was merged.

## Stage 2 Profile calculations

- [x] Align profile bin boundaries with the count-histogram convention,
  including the final right edge.
- [x] Replace subtraction of large second moments with a stable variance
  calculation.
- [x] Add reference calculations for boundary values, large offsets with small
  spread, empty bins, and bins with one observation.
- [x] Compare equivalent branch and boost-histogram profiles and account for
  any intended estimator differences.
- [x] Document the chosen variance estimator, standard error, and empty-bin
  behavior in the histogram and loading guides.

**Decision:** retain branch profiles' population variance convention and the
existing sparse-bin behavior: empty bins have value and variance zero with
NaN spread, and single-entry bins have the observed value, zero variance, and
equal spread bounds. This preserves uncertainty semantics while fixing bin
membership and numerical stability. Boost Mean conversion retains its sample
correction; the difference is documented and tested.

**Completion:** the reproduced boundary and cancellation failures have
regression tests, and profile values and uncertainties agree with the chosen
reference calculations within stated tolerances.

**Verification on October 22, 2026:** all 385 unit tests passed on Python
3.11.15 and 3.14.6, including 15 new profile calculation cases. The 80-digit
Decimal reference comparison uses variance relative tolerance `1e-12` and
mean absolute tolerance of one float64 spacing at `1e12`. A wheel built from
the sdist passed the runtime-only packaging smoke check and direct profile
regressions outside the checkout on Python 3.11. Package/changed-test Ruff,
package Pyright, strict documentation build, and `git diff --check` passed.
The test and distribution CI jobs passed on
[PR 27](https://github.com/asalzburger/unrooted/pull/27), which was merged.

## Stage 3 Data and statistical contracts

- [x] Validate numeric axis edges, histogram dimensionality, array shapes,
  variance signs, spread pairs, and scatter dimensions at public boundaries.
- [x] Define allowed NaNs, array ownership/mutation, and flow-bin semantics.
- [x] Require compatible bin edges for ratios in every backend; keep ordinary
  graphical overlay behavior explicit.
- [x] Validate efficiency inputs, including dimensions and accepted/total
  constraints; reject unsupported storage types with actionable errors.
- [x] Make supported boost storage and axis types explicit, including the
  policy for weighted profiles and categorical axes.
- [x] Document the independent-input assumption for ratio uncertainties and
  distinguish profile extrema, standard-deviation bands, and efficiency
  intervals.

**Decision:** use Wilson score intervals without continuity correction at
confidence level `0.6826894921370859` (68.27%) by default. Both readers accept
a keyword-only `confidence_level` in `(0, 1)`. Retain binomial variance
`p*(1-p)/N` separately from the interval bounds. Intervals have nonzero width
at zero and full acceptance; zero-total bins have NaN in all four arrays.
Require 1D unweighted integer counts with exactly matching edges and
accepted ≤ total. Weighted/fractional efficiencies, boost weighted profiles,
and categorical/Boolean axes remain explicitly unsupported.

**Completion:** invalid inputs fail with clear exceptions, incompatible bins
cannot produce ratios, and all supported statistical interpretations have
small numerical examples and tests.

**Verification on October 22, 2026:** 523 unit tests passed on Python 3.11.15
and 3.14.6, including analytic one-sigma Wilson bounds, a 95% reference,
invalid inputs, exact-edge ratios, large integer ratio uncertainties,
mutation, reader ownership, and multidimensional flow padding. A wheel built
from the sdist passed the runtime-only packaging smoke check outside the
checkout on Python 3.11, including Wilson endpoint bounds. Package and
changed-test Ruff, package Pyright, strict documentation build, and
`git diff --check` passed. The generated efficiency figure was inspected.
The test and distribution CI jobs passed on
[PR 28](https://github.com/asalzburger/unrooted/pull/28), which was merged.

## Stage 4 CLI and backend consistency

- [x] Apply Plotly axis-label overrides and single-histogram legend labels.
- [x] Respect ratio error-display and line-style settings across backends.
- [x] Give missing files, unsupported objects, invalid options, and export
  failures consistent messages and exit codes.
- [x] Check source prefixes, multi-file label defaults, and unsupported option
  combinations in command-level tests.
- [x] Establish public scatter exports and composition helpers so examples
  can use public APIs.
- [x] Document backend capabilities and optional static-image dependencies.

**Completion:** command-level tests exercise saved Matplotlib and Plotly
output, terminal rendering, labels, ratios, and representative failures.
User-visible settings either work or receive an explicit unsupported-option
error.

**Behavior:** graphical ratio panels use the numerator's line, marker, and
error settings, excluding main-panel fill and spread. CLI main/ratio labels
and ranges are applied separately. Filename stems label N-files/one-spec
overlays; other combinations use draw keys. `--source` prefixes histogram and
efficiency keys, while branch specs retain explicit tree paths. Public
`plot_scatter` and `overlay_scatter` are exported from both graphical
backends; Plotly scatter can compose into an existing figure or subplot.
Invalid arguments/combinations exit `2`; operational failures exit `1` with
an `unrooted:` message. Unsupported flags are rejected explicitly.

**Verification on October 22, 2026:** 609 unit tests passed on Python 3.11.15
and 3.14.6. New workflows use synthetic ROOT files, inspect saved Matplotlib
SVG and Plotly HTML output, and run CLI subprocesses for output and exit-code
checks. Regression tests cover ratio display modes, marker-only ratios,
disabled uncertainty calculations, labels/ranges, source prefixes, file/spec
combinations, scatter composition, and loading/export failures. Package and
changed-test Ruff, package Pyright, strict documentation build, and
`git diff --check` passed. The generated ratio example was inspected.
A runtime-only Python 3.11 installation of a wheel built from the sdist
passed the packaging smoke check outside the checkout, including scatter
exports and the missing-Plotly diagnostic. Successful Plotly static-image
export was not exercised: HTML export and the static-export failure path
were tested, and optional Kaleido/browser setup is documented.
The test and distribution CI jobs passed on
[PR 29](https://github.com/asalzburger/unrooted/pull/29), which was merged.

## Stage 5 Realistic workloads

- [x] Agree representative histogram and scatter workloads and measure the
  current runtime, peak memory, and output size.
- [x] Add entry selection and bounds for branch loading.
- [x] Implement chunked histogram/profile accumulation where needed for the
  agreed workloads, preserving the numerical contracts from stages 2 and 3.
- [x] Provide an explicit scatter point limit or sampling option, with
  reproducible sampling when enabled.
- [x] Document memory behavior, limits, and any sampling in the loading and
  CLI guides.

**Decision:** target 10 million flattened observations per histogram/profile,
under 1 GiB peak process RAM and 30 seconds per load on the local reference
workload. Scatter retains up to 100,000 points only when explicitly requested.
Use seeded uniform sampling without replacement over flattened pairs, with
retained/source counts and the seed available to the caller. The user accepted
these recommended targets on October 22, 2026.

**Behavior:** tree entry selection precedes broadcasting/flattening. Readers
use chunks of at most 100,000 entries by default; count accumulation uses one
pass and stable population-profile accumulation uses three. Automatic ranges
add an x-only pass. Scatter without a limit returns all selected pairs;
`max_points` defaults to an explicit overflow error, while `sampling="random"`
opts into a repeatable uniform sample. The CLI reports actual sampling on
stderr. Chunk size is an entry limit, not a byte/RSS guarantee for arbitrary
jagged events or ROOT baskets.

**Completion:** representative workloads meet the agreed resource budgets;
chunked results match reference results, and sampling is explicit and
reproducible.

**Verification on October 22, 2026:** 684 unit tests passed on Python 3.11.15
and 3.14.6. New tests cover event bounds, chunk-edge binning, all supported
nested branch pair shapes, an 80-digit Decimal profile reference (variance
relative tolerance `1e-12`, mean absolute tolerance one float64 spacing at
`1e12`), sparse/NaN bins, explicit limits, seeded pair sampling across chunk
sizes, and CLI behavior. Package/changed-test/benchmark Ruff, package Pyright,
strict documentation build, and `git diff --check` passed. A wheel built from
the sdist passed runtime-only installation checks outside the checkout,
including entry selection and sampling.

The reproducible benchmark uses seeded local scalar and jagged ROOT inputs,
10 observations per jagged event, 100 bins, and three fresh worker processes
per case on arm64 macOS / Python 3.14.6. All measured 10-million-observation
loads, including automatic ranges and explicitly sampled scatter, stayed
below 2.51 s and 252 MiB peak RSS. Jagged profile peak memory fell from
877.4 MiB to 238.3 MiB with an explicit range; median load time changed from
0.865 s to 2.315 s because of the extra passes. A 100,000-point scatter sample
from 10 million pairs produced 7.0 MiB HTML and used at most 318.7 MiB during
export. These are results for the recorded reference configuration, not a
universal guarantee. Raw reports, versions, source/input hashes, and before/
after measurements are in `benchmarks/results/`; the loading guide explains
how to reproduce them. Plotly static image export remains outside this check.
The test and distribution CI jobs passed on
[PR 30](https://github.com/asalzburger/unrooted/pull/30), which was merged.

## Stage 6 CI and contributor workflow

- [x] Consolidate development dependency definitions and adopt a committed
  lockfile for reproducible contributor and CI environments.
- [x] Define supported dependency bounds and test the oldest and newest
  supported Python versions, with Linux/macOS coverage.
- [x] Exercise the base installation separately from optional Plotly support;
  retain installed-wheel testing.
- [x] Build documentation strictly on pull requests and execute the key
  README/getting-started examples.
- [x] Extend lint to tests and documentation hooks; fix the existing findings.
- [x] Close test figures, keep generated files in temporary directories, and
  confirm checks leave the working tree clean.
- [x] Add contributor instructions and reconcile stale `CLAUDE.md` guidance.

**Behavior:** `dev` and `docs` dependency groups replace duplicated development
extras; Plotly remains an optional runtime extra. A committed `uv.lock` and
`uv sync --locked` select contributor/CI dependencies, including build tools.
Explicit runtime floors are NumPy 2.0, Uproot 5.6.0, Awkward 2.8.0,
Matplotlib 3.8.4, boost-histogram 1.7.2, and optional Plotly 5.24.1. NumPy 2
also matches the checked-in boost fixture's pickle format. Generated ROOT
fixtures use the explicit schema/extend API supported by the Uproot floor.
No runtime upper bounds are introduced.

CI covers CPython 3.11–3.15 on Linux and the 3.11/3.15 boundaries on macOS,
separating base and Plotly environments. A dedicated Python 3.11 job tests
the lowest allowed direct runtime/Plotly versions, with locked test tools
and resolver-selected transitive dependencies. Distribution checks build a
wheel from the sdist with locked build tools and exercise base/Plotly wheel
installations on Python 3.11 and 3.15. A PR quality job lints all Python
sources, type-checks the package, executes introductory examples, and builds
the docs strictly. Each CI job requires a clean working tree after checks.

Shared test cleanup closes all Matplotlib figures and restores plotting
settings; the open-figure resource warning is an error. Documentation gallery
outputs now live in temporary storage and are registered as generated MkDocs
files. README and Getting Started Python blocks are executed directly with
synthetic ROOT/boost inputs, temporary outputs, and browser display
intercepted; their loading, plotting, and export run normally. The contributor
guide documents the matrix, dependency updates, local checks, and wheel
rehearsal. `CLAUDE.md` uses that workflow and the current public APIs; the
shadowing Pyright JSON config was consolidated into `pyproject.toml`.

**Local verification on October 22, 2026:** all 684 unit tests passed with
locked Plotly environments on Python 3.11.15 and 3.15.1 and with the declared
minimum dependency stack on Python 3.11.15. The base Python 3.11 environment,
without Plotly, passed 594 tests with 43 optional skips. Upstream Matplotlib
deprecations remain visible in the minimum-stack run. All-source Ruff,
package Pyright, strict MkDocs, workflow YAML parsing, and whitespace checks
passed. The documentation smoke check executed 12 Python blocks and two CLI
examples successfully. A wheel built from the sdist passed runtime-only and
Plotly-enabled smoke checks outside the checkout on Python 3.11 and 3.15.

**Completion:** one documented local workflow reproduces the required checks,
and CI covers the declared support matrix, installed artifacts, and key
documentation examples.

The quality, supported-platform, minimum-dependency, and distribution CI jobs
passed on [PR 31](https://github.com/asalzburger/unrooted/pull/31), merged on
October 22, 2026.

## Stage 7 Release candidate

- [x] Choose and add a license; complete package description, README, and
  maintainer metadata.
- [x] Establish one version source, a changelog, compatibility policy, and
  release instructions.
- [x] Finish the architecture and API references for `ScatterData`,
  `load_scatter`, public plotting APIs, and the supported input types.
- [ ] Rehearse installation and documented workflows from candidate artifacts
  on the supported configurations.
- [ ] Inspect representative plots and generated documentation for layout,
  labels, uncertainty rendering, and broken links.
- [x] Add a release workflow that validates artifacts before publication.

**Decision on October 23, 2026:** the user accepted `0.1.0rc1`, MIT licensing,
support for the CI-tested CPython 3.11–3.15 Linux/macOS configurations, and
documented breaking changes in 0.x minor releases. GitHub Releases is the
initial artifact destination; PyPI is deferred. Publication still follows an
explicit release request. The [release guide](docs/releasing.md) defines the
policy and rehearsal procedure.

**Implementation:** Hatchling reads `unrooted/_version.py`; package metadata
and the public version agree. The sdist carries the package, license, README,
changelog, and build configuration. A candidate workflow validates a wheel
built from that sdist and tests the installed wheel on the supported matrix
and minimum stack. It retains distributions, checksums, release notes, and
rendered documentation. A separate write-enabled job can prepare a draft
only after those checks pass on an existing matching version tag. It never
publishes automatically.

**Local verification on October 23, 2026:** all 692 tests passed on Python
3.11.17. Ruff, package Pyright, actionlint, strict MkDocs, generated local
page/asset/fragment checks, and whitespace checks passed. Fresh runtime-only
and Plotly wheel installations outside the checkout passed on macOS with
Python 3.11.17 and 3.15.1. Both installed Plotly environments executed the
12 introductory Python blocks and two CLI examples. Supported-platform CI
and visual inspection are being completed before marking the stage complete.

**Completion:** the candidate artifacts pass the agreed checks, user examples
work from an installed package, documentation describes the actual behavior,
and release notes identify compatibility changes and remaining limitations.
