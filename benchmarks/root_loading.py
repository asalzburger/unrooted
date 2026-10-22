"""Measure ROOT loading in fresh processes, independently of fixture generation.

Run with an installed/editable unrooted environment in isolated mode, e.g.:
    python -I benchmarks/root_loading.py --workdir /tmp/unrooted-bench \
        --observations 1000000 --report /tmp/unrooted-bench/report.json

Peak RSS uses resource.getrusage (macOS/Linux). Generated ROOT data and plots
stay in the requested work directory; no repository fixtures are modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path
from time import perf_counter


def generate(path: Path, observations: int, layout: str) -> None:
    import awkward as ak
    import numpy as np
    import uproot

    rng = np.random.default_rng(71)
    schema = {
        name: "var * float64" if layout == "jagged" else "float64"
        for name in ("x", "y")
    }
    with uproot.recreate(path, compression=uproot.ZLIB(1)) as root_file:
        root_file["benchmark_metadata"] = json.dumps(
            {
                "observations": observations,
                "layout": layout,
                "seed": 71,
                "generator_version": 1,
            }
        )
        tree = root_file.mktree("tree", schema)
        for start in range(0, observations, 100_000):
            size = min(100_000, observations - start)
            x = rng.uniform(-5, 5, size)
            y = 1e12 + rng.normal(size=size)
            if layout == "jagged":
                counts = np.full((size + 9) // 10, 10)
                counts[-1] = size - 10 * (len(counts) - 1)
                tree.extend(
                    {"x": ak.unflatten(x, counts), "y": ak.unflatten(y, counts)}
                )
            else:
                tree.extend({"x": x, "y": y})


def peak_rss_bytes() -> int:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(rss if sys.platform == "darwin" else rss * 1024)


def worker(args) -> None:
    import numpy as np

    from unrooted.io.root import load_branch, load_scatter

    kwargs = {}
    if args.step_size is not None:
        kwargs["step_size"] = args.step_size
    start = perf_counter()
    if args.mode == "scatter":
        if args.max_points is not None:
            kwargs.update(max_points=args.max_points, sampling="random", seed=71)
        result = load_scatter(args.input, "tree", "x", "y", **kwargs)
        arrays = [result.x, result.y]
        points = len(result.x)
    else:
        result = load_branch(
            args.input,
            "tree",
            "x",
            "y" if args.mode == "profile" else None,
            n_bins=100,
            range=None if args.auto_range else (-5.0, 5.0),
            **kwargs,
        )
        arrays = [result.values, result.variances, result.axes[0].edges]
        if result.spread_min is not None:
            arrays += [result.spread_min, result.spread_max]
        points = None
    load_seconds = perf_counter() - start
    load_peak = peak_rss_bytes()
    output = None
    render_seconds = None
    if args.render:
        start = perf_counter()
        if args.mode == "scatter":
            from unrooted.plot.plotly import plot_scatter

            output = args.input.with_name(args.input.stem + "-scatter.html")
            plot_scatter(result).write_html(output)
        else:
            import matplotlib.pyplot as plt

            from unrooted.plot.mpl import plot
            from unrooted.plot.style import HistogramStyle

            output = args.input.with_name(args.input.stem + f"-{args.mode}.png")
            style = HistogramStyle.as_profile() if args.mode == "profile" else None
            ax = plot(result, style=style)
            ax.figure.savefig(output)
            plt.close(ax.figure)
        render_seconds = perf_counter() - start
    print(
        json.dumps(
            {
                "mode": args.mode,
                "load_seconds": load_seconds,
                "load_peak_rss_bytes": load_peak,
                "result_bytes": sum(
                    array.nbytes for array in arrays if array is not None
                ),
                "retained_points": points,
                "value_sum": float(np.sum(result.values)) if points is None else None,
                "render_seconds": render_seconds,
                "overall_peak_rss_bytes": peak_rss_bytes(),
                "plot_bytes": output.stat().st_size if output else None,
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--observations", type=int, default=1_000_000)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument(
        "--layouts",
        nargs="+",
        choices=["scalar", "jagged"],
        default=["scalar", "jagged"],
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=["count", "profile", "scatter"],
        default=["count", "profile", "scatter"],
    )
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--auto-range", action="store_true")
    parser.add_argument("--step-size", type=int)
    parser.add_argument("--max-points", type=int)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--input", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--mode", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args)
        return
    if args.workdir is None or args.report is None:
        parser.error("--workdir and --report are required")
    if args.observations < 1 or args.repeat < 1:
        parser.error("--observations and --repeat must be positive")
    args.workdir.mkdir(parents=True, exist_ok=True)
    from unrooted.io.root import tree as tree_module

    script = Path(__file__).resolve()
    env = dict(os.environ, MPLBACKEND="Agg", MPLCONFIGDIR=str(args.workdir / "mpl"))
    env.pop("PYTHONPATH", None)
    report = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "logical_cpus": os.cpu_count(),
        "versions": {name: version(name) for name in ["numpy", "uproot", "awkward"]},
        "observations_per_input": args.observations,
        "fixture_seed": 71,
        "jagged_observations_per_event": 10,
        "step_size": args.step_size,
        "max_points": args.max_points,
        "auto_range": args.auto_range,
        "render": args.render,
        "unrooted_version": version("unrooted"),
        "loader_sha256": hashlib.sha256(
            Path(tree_module.__file__).read_bytes()
        ).hexdigest(),
        "filesystem_cache": "not cleared; fixtures generated/read before timing",
        "results": [],
    }
    for layout in args.layouts:
        path = args.workdir / f"{layout}-{args.observations}.root"
        if not path.exists():
            generate(path, args.observations, layout)
        import uproot

        expected = {
            "observations": args.observations,
            "layout": layout,
            "seed": 71,
            "generator_version": 1,
        }
        with uproot.open(path) as root_file:
            if (
                "benchmark_metadata" not in root_file
                or json.loads(str(root_file["benchmark_metadata"])) != expected
            ):
                raise ValueError(
                    f"Fixture metadata mismatch: {path}; use a new workdir"
                )
        input_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        for mode in args.modes:
            for repeat in range(args.repeat):
                command = [
                    sys.executable,
                    "-I",
                    str(script),
                    "--worker",
                    "--input",
                    str(path),
                    "--mode",
                    mode,
                ]
                if args.render:
                    command.append("--render")
                if args.auto_range:
                    command.append("--auto-range")
                for option in ("step_size", "max_points"):
                    if getattr(args, option) is not None:
                        command += [
                            "--" + option.replace("_", "-"),
                            str(getattr(args, option)),
                        ]
                run = subprocess.run(
                    command, env=env, capture_output=True, text=True, timeout=300
                )
                if run.returncode:
                    raise RuntimeError(f"{layout}/{mode} failed: {run.stderr}")
                row = json.loads(run.stdout)
                row.update(
                    layout=layout,
                    repeat=repeat,
                    input_bytes=path.stat().st_size,
                    input_sha256=input_hash,
                )
                report["results"].append(row)
                print(json.dumps(row), flush=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
