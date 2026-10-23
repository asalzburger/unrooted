# Releases and compatibility

## Release policy

The first candidate is **0.1.0rc1**, licensed under MIT and maintained by
Andreas Salzburger. GitHub Releases is the initial distribution destination;
PyPI publication is deferred. Preparing a candidate or merging its pull
request does not authorize publication.

The support promise covers the CPython 3.11–3.15 Linux/macOS configurations
listed in the [contributor guide](contributing.md), including base and Plotly
installations and the declared minimum dependencies. It does not extend to
Windows, untested platform/interpreter combinations, future dependency
releases, long-term maintenance, or a response-time guarantee.

During `0.x`, minor releases may introduce breaking changes when documented
in the changelog. Patch releases preserve documented public APIs and CLI
syntax, except that correctness fixes may reject invalid inputs or correct
numerical results; such changes must be called out. Release candidates may
change before the final release. Names beginning with `_` and implementation
helpers are private. The API reference and user guides define the public
surface, including statistical semantics and CLI exit codes.

## Version and release notes

`unrooted/_version.py` is the only editable version source. Hatchling reads
it without importing runtime dependencies; `unrooted.__version__` imports
the same value. Distribution metadata is checked against it. Use a `v`
prefix for Git tags (for example `v0.1.0rc1`). Update `CHANGELOG.md` for every
candidate, including compatibility changes, validation, and known limits.
The lockfile records the project as dynamically versioned.

The sdist contains the package, license, README, changelog, and build
configuration. It intentionally excludes test fixtures and the documentation
build tree. Release tests and rendered documentation come from the same Git
revision as the candidate.

## Candidate rehearsal

Start from a clean checkout with LFS fixtures and the locked contributor
setup. Use a fresh output directory for each candidate; validation rejects
multiple wheels or sdists. These commands do not publish anything:

```bash
uv sync --locked --group docs --extra plotly
uv run --no-sync ruff check .
uv run --no-sync python -I -m pyright
uv run --no-sync python -I -m pytest -q
uv build --no-build-isolation --sdist --out-dir /tmp/unrooted-candidate
uv build --no-build-isolation --wheel /tmp/unrooted-candidate/*.tar.gz --out-dir /tmp/unrooted-candidate
uv run --no-sync python -I tools/release/validate.py /tmp/unrooted-candidate --checksums --notes /tmp/unrooted-candidate/RELEASE_NOTES.md
uv venv --python 3.11 /tmp/unrooted-candidate-env
uv pip install --python /tmp/unrooted-candidate-env/bin/python /tmp/unrooted-candidate/*.whl
/tmp/unrooted-candidate-env/bin/python -I tests/packaging/smoke.py
uv pip install --python /tmp/unrooted-candidate-env/bin/python 'unrooted[plotly]'
/tmp/unrooted-candidate-env/bin/python -I tests/packaging/smoke.py
/tmp/unrooted-candidate-env/bin/python -I tests/documentation/smoke.py --installed
uv run --no-sync python -I -m mkdocs build --strict --site-dir /tmp/unrooted-candidate-site
uv run --no-sync python -I tests/documentation/links.py /tmp/unrooted-candidate-site
```

Repeat the installed-wheel rehearsal at the newest supported Python boundary.
The **Release candidate** Actions workflow runs on pull requests and manual
dispatches. It builds a wheel from the sdist once, validates version, license,
README, dependencies, and every package file, then tests those same artifacts
on the supported matrix and minimum stack. Tests use isolated Python and
pytest's importlib mode to avoid importing the checkout. Plotly configurations
also execute the actual introductory examples against the installed wheel.
Checksums, release notes, distributions, and the built site are retained as
Actions artifacts. Ordinary CI separately checks runtime-only wheel installs.

Inspect the generated site on desktop and narrow screens, including API
signatures, tables, navigation, and example embeds. Inspect representative
1D/2D histograms, ratios, profiles, efficiencies, and scatter plots for labels,
clipping, and uncertainty rendering. The link checker checks local pages,
assets, and fragments; external links require a separate reachability check.
Plotly static export is outside this matrix and remains a documented limitation.

## Preparing a draft and publishing

Only after an explicit release request:

1. Review the candidate evidence and changelog, set the release date, and
   merge the reviewed changes. All required checks must pass for that revision.
2. Create and push an annotated `v<version>` tag at that exact commit. Never
   move an already published tag or replace published artifacts.
3. Run **Release candidate** manually on that tag with `prepare_draft=true`.
   It repeats validation and the installation matrix before creating a GitHub
   **draft** with the exact tested wheel, sdist, and SHA-256 manifest. A tag
   mismatch fails; an existing release is not overwritten. Pushing a tag alone
   does not publish or prepare a release.
4. Inspect the draft notes/assets and candidate documentation artifact. Check
   the prerelease flag for `rc` versions, then publish the draft through GitHub
   only when the release request authorizes publication.
5. Download the published artifacts into a fresh environment, verify their
   SHA-256 hashes, and repeat the installed-wheel smoke check. Record the
   release URL and validation outcome in the roadmap.

No package-index credentials or PyPI upload job are configured. Adding PyPI
is a separate release-policy change. Failed rehearsal runs never reach the
write-enabled draft job; normal PR/manual validation needs only read access.
