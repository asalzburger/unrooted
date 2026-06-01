from __future__ import annotations

from pathlib import Path

from unrooted.core.histogram import Histogram
from unrooted.io.root.reader import load, load_efficiency
from unrooted.io.root.tree import load_branch

from ._draw_spec import DrawSpec


def _full_key(source: str, key: str) -> str:
    return f"{source}/{key}" if source else key


def _load_one(
    file: str,
    spec: DrawSpec,
    source: str,
    n_bins: int,
    branch_range: tuple[float, float] | None,
) -> Histogram:
    path = Path(file)
    if spec.draw_type == "eff":
        return load_efficiency(
            path,
            _full_key(source, spec.keys[0]),
            _full_key(source, spec.keys[1]),
        )
    if spec.draw_type == "branch":
        tree_key = spec.keys[0]
        x_branch = spec.keys[1]
        y_branch = spec.keys[2] if len(spec.keys) > 2 else None
        return load_branch(
            path,
            tree_key,
            x_branch,
            y_branch,
            n_bins=n_bins,
            range=branch_range,
        )
    return load(path, _full_key(source, spec.keys[0]))


def resolve_loads(
    files: list[str],
    specs: list[DrawSpec],
    source: str,
    n_bins: int = 100,
    branch_range: tuple[float, float] | None = None,
) -> list[tuple[Histogram, str]]:
    """Load histograms according to file/spec combination rules.

    Combining rules:

    * **1 file + N specs** — load each spec from the single file; label from spec key.
    * **N files + 1 spec** — load the same spec from every file; label from filename stem.
    * **N files + N specs** — zip ``(file_i, spec_i)``; label from spec key.

    Returns:
        List of ``(histogram, label_hint)`` pairs.

    Raises:
        ValueError: If the file/spec counts are incompatible.
    """
    n_f, n_s = len(files), len(specs)

    if n_f == 1 and n_s >= 1:
        pairs = [(files[0], s) for s in specs]
        label_fn = lambda f, s: s.keys[-1].split("/")[-1]  # noqa: E731
    elif n_f > 1 and n_s == 1:
        pairs = [(f, specs[0]) for f in files]
        label_fn = lambda f, s: Path(f).stem  # noqa: E731
    elif n_f == n_s:
        pairs = list(zip(files, specs))
        label_fn = lambda f, s: s.keys[-1].split("/")[-1]  # noqa: E731
    else:
        raise ValueError(
            f"Cannot combine {n_f} input file(s) with {n_s} draw spec(s). "
            "Valid combinations: 1 file + N specs, N files + 1 spec, N files + N specs."
        )

    return [
        (_load_one(f, s, source, n_bins, branch_range), label_fn(f, s))
        for f, s in pairs
    ]
