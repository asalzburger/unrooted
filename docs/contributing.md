# Contributing

## Supported configurations

The package requires Python 3.11 or newer. CI tests CPython 3.11–3.15 on
Linux, plus 3.11 and 3.15 on macOS. Both ends of that range exercise the base
installation without Plotly and a configuration with Plotly. Other Python
versions and platforms are not currently covered by CI.

| Dependency | Minimum supported version |
| --- | --- |
| NumPy | 2.0 |
| Uproot | 5.6.0 |
| Awkward Array | 2.8.0 |
| Matplotlib | 3.8.4 |
| boost-histogram | 1.7.2 |
| Plotly (optional) | 5.24.1 |

These floors are tested together on Python 3.11. Newer Python versions use
compatible versions from the lockfile; some minimum releases predate their
interpreter and have no matching wheels. No speculative upper bounds are
placed on runtime dependencies. Compatibility changes belong in release
notes and require the same numerical and plotting regression checks.
The NumPy floor also matches the NumPy 2 pickle format used by the checked-in
boost-histogram fixture. Minimum-stack tests may report upstream Matplotlib
deprecations; the open-figure resource warning is treated as an error.

## Setup

CI uses uv 0.13.5. Use that version to reproduce its environment and Python
downloads. Development tools are defined once in the `dev` dependency group;
the `docs` group includes it. Plotly remains a separate package extra.

```bash
git clone https://github.com/asalzburger/unrooted
cd unrooted
git lfs install
git lfs pull
uv sync --locked --python 3.11 --group docs --extra plotly
```

`uv.lock` is committed. `--locked` rejects dependency definitions that have
not been resolved into it. Package consumers can still use pip and the
declared dependency ranges; the lockfile is for contributors and CI.

## Required checks

Run from the checkout after the setup above. `--no-sync` keeps each command
in the environment that was just selected. Isolated Python execution avoids
imports from unrelated `PYTHONPATH` settings.

```bash
uv run --no-sync ruff check .
uv run --no-sync python -I -m pyright
uv run --no-sync python -I -m pytest -q
uv run --no-sync python -I tests/documentation/smoke.py
uv run --no-sync python -I -m mkdocs build --strict --site-dir /tmp/unrooted-docs-site
git diff --check
git status --short
```

Lint includes the package, tests, examples, benchmark harness, and docs hook.
Pyright checks the package. The documentation smoke check executes the
actual Python blocks in README and Getting Started, plus the README CLI
examples, against synthetic ROOT and boost-histogram inputs. Browser display
is intercepted; figures and HTML are exported. A strict documentation build
also runs the gallery examples and checks API references.

Unit tests close Matplotlib figures and restore plotting settings after each
test. Generated fixture/output files use temporary directories. Documentation
gallery assets are generated in temporary storage and copied directly into
the built site, leaving the source directory unchanged. CI requires an empty
`git status --porcelain` after its checks.

## Dependency and environment checks

For ordinary code changes, keep `uv.lock` unchanged. To update dependencies:

```bash
uv lock --upgrade-package numpy
# Or deliberately refresh the complete dependency set:
uv lock --upgrade
uv sync --locked --group docs --extra plotly
```

Review the lockfile diff and run the required checks. Test supported
interpreter boundaries and declared dependency floors before changing them.
CI resolves the lowest allowed direct runtime dependencies in a separate
environment while retaining its locked test tools. Transitive dependencies
remain resolver-selected, so that job is intentionally separate from the
reproducible locked matrix.

To reproduce that minimum-version job without altering your contributor
environment:

```bash
UV_PROJECT_ENVIRONMENT=/tmp/unrooted-minimum uv sync --locked --python 3.11
uv pip install --python /tmp/unrooted-minimum/bin/python \
  --resolution lowest-direct --upgrade -e '.[plotly]'
/tmp/unrooted-minimum/bin/python -I -m pytest -q
```

For a base environment, use a fresh `UV_PROJECT_ENVIRONMENT` and run
`uv sync --locked --python 3.11` without `--extra plotly`. Plotly tests skip
when the optional dependency is absent. The installed-wheel smoke check
also verifies the missing-Plotly CLI diagnostic.

## Distribution checks

The build backend is included in the locked development tools. Build an
sdist, then build the wheel from that sdist using those tools:

```bash
uv build --no-build-isolation --sdist --out-dir dist
uv build --no-build-isolation --wheel dist/*.tar.gz --out-dir dist
uv venv /tmp/unrooted-wheel
uv pip install --python /tmp/unrooted-wheel/bin/python dist/*.whl
/tmp/unrooted-wheel/bin/python -I tests/packaging/smoke.py
uv pip install --python /tmp/unrooted-wheel/bin/python 'unrooted[plotly]'
/tmp/unrooted-wheel/bin/python -I tests/packaging/smoke.py
```

The smoke script creates its own temporary working directory and data,
checks that imports come from the installed wheel, and covers assets,
statistical contracts, loading, Matplotlib export, and CLI behavior. With
Plotly installed it also checks API and CLI HTML export. Static-image export
requires the additional setup described in the [CLI guide](user-guide/cli.md).

## Changes and pull requests

The [release guide](releasing.md) defines versioning, compatibility promises,
candidate validation, and the separate publication procedure. The candidate
workflow also runs the suite against the installed wheel across the support
matrix, checks distribution metadata/assets, and validates generated links.

Use `feat-<topic>`, `fix-<topic>`, or `chore-<topic>` branches. Keep numerical
references and user-facing documentation with behavior changes. Preserve
the I/O → core → plotting separation, and use public APIs in examples.
Run lint and type checking before committing. Describe the resulting
behavior, validation, and any remaining limitations in the pull request.
