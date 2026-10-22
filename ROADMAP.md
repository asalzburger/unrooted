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
| 1 | Installed distributions work outside the checkout | Complete locally |
| 2 | Profile calculations agree with numerical references | Next |
| 3 | Data and statistical contracts are explicit and enforced | Planned |
| 4 | CLI and plotting backends honor their public contracts | Planned |
| 5 | Data loading has a tested resource envelope | Planned |
| 6 | CI and contributor setup reproduce supported configurations | Planned |
| 7 | A release candidate passes installation and documentation rehearsal | Planned |

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
distribution job is configured in CI; its hosted result is pending a push.

## Stage 2 Profile calculations

- [ ] Align profile bin boundaries with the count-histogram convention,
  including the final right edge.
- [ ] Replace subtraction of large second moments with a stable variance
  calculation.
- [ ] Add reference calculations for boundary values, large offsets with small
  spread, empty bins, and bins with one observation.
- [ ] Compare equivalent branch and boost-histogram profiles and account for
  any intended estimator differences.
- [ ] Document the chosen variance estimator, standard error, and empty-bin
  behavior in the histogram and loading guides.

**Decision together:** choose the population/sample variance convention and
the treatment of bins with fewer than two observations. Record the rationale
and any compatibility change.

**Completion:** the reproduced boundary and cancellation failures have
regression tests, and profile values and uncertainties agree with the chosen
reference calculations within stated tolerances.

## Stage 3 Data and statistical contracts

- [ ] Validate numeric axis edges, histogram dimensionality, array shapes,
  variance signs, spread pairs, and scatter dimensions at public boundaries.
- [ ] Define allowed NaNs, array ownership/mutation, and flow-bin semantics.
- [ ] Require compatible bin edges for ratios in every backend; keep ordinary
  graphical overlay behavior explicit.
- [ ] Validate efficiency inputs, including dimensions and accepted/total
  constraints; reject unsupported storage types with actionable errors.
- [ ] Make supported boost storage and axis types explicit, including the
  policy for weighted profiles and categorical axes.
- [ ] Document the independent-input assumption for ratio uncertainties and
  distinguish profile extrema, standard-deviation bands, and efficiency
  intervals.

**Decision together:** choose the initial weighted-efficiency policy and
efficiency interval method. State confidence levels and the behavior at zero
and full acceptance. Prefer explicit unsupported cases until their statistical
meaning is implemented and tested.

**Completion:** invalid inputs fail with clear exceptions, incompatible bins
cannot produce ratios, and all supported statistical interpretations have
small numerical examples and tests.

## Stage 4 CLI and backend consistency

- [ ] Apply Plotly axis-label overrides and single-histogram legend labels.
- [ ] Respect ratio error-display and line-style settings across backends.
- [ ] Give missing files, unsupported objects, invalid options, and export
  failures consistent messages and exit codes.
- [ ] Check source prefixes, multi-file label defaults, and unsupported option
  combinations in command-level tests.
- [ ] Establish public scatter exports and composition helpers so examples
  can use public APIs.
- [ ] Document backend capabilities and optional static-image dependencies.

**Completion:** command-level tests exercise saved Matplotlib and Plotly
output, terminal rendering, labels, ratios, and representative failures.
User-visible settings either work or receive an explicit unsupported-option
error.

## Stage 5 Realistic workloads

- [ ] Agree representative histogram and scatter workloads and measure the
  current runtime, peak memory, and output size.
- [ ] Add entry selection and bounds for branch loading.
- [ ] Implement chunked histogram/profile accumulation where needed for the
  agreed workloads, preserving the numerical contracts from stages 2 and 3.
- [ ] Provide an explicit scatter point limit or sampling option, with
  reproducible sampling when enabled.
- [ ] Document memory behavior, limits, and any sampling in the loading and
  CLI guides.

**Decision together:** choose the dataset sizes and resource budgets needed
for the first release. Use those to determine the required streaming and
sampling scope.

**Completion:** representative workloads meet the agreed resource budgets;
chunked results match reference results, and sampling is explicit and
reproducible.

## Stage 6 CI and contributor workflow

- [ ] Consolidate development dependency definitions and adopt a committed
  lockfile for reproducible contributor and CI environments.
- [ ] Define supported dependency bounds and test the oldest and newest
  supported Python versions, with Linux/macOS coverage.
- [ ] Exercise the base installation separately from optional Plotly support;
  retain installed-wheel testing.
- [ ] Build documentation strictly on pull requests and execute the key
  README/getting-started examples.
- [ ] Extend lint to tests and documentation hooks; fix the existing findings.
- [ ] Close test figures, keep generated files in temporary directories, and
  confirm checks leave the working tree clean.
- [ ] Add contributor instructions and reconcile stale `CLAUDE.md` guidance.

**Completion:** one documented local workflow reproduces the required checks,
and CI covers the declared support matrix, installed artifacts, and key
documentation examples.

## Stage 7 Release candidate

- [ ] Choose and add a license; complete package description, README, and
  maintainer metadata.
- [ ] Establish one version source, a changelog, compatibility policy, and
  release instructions.
- [ ] Finish the architecture and API references for `ScatterData`,
  `load_scatter`, public plotting APIs, and the supported input types.
- [ ] Rehearse installation and documented workflows from candidate artifacts
  on the supported configurations.
- [ ] Inspect representative plots and generated documentation for layout,
  labels, uncertainty rendering, and broken links.
- [ ] Add a release workflow that validates artifacts before publication.

**Decision together:** choose the release version, license, support promise,
and publication destination. Publication follows an explicit release request.

**Completion:** the candidate artifacts pass the agreed checks, user examples
work from an installed package, documentation describes the actual behavior,
and release notes identify compatibility changes and remaining limitations.
