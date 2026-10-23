"""Exercise an installed wheel with only its declared runtime dependencies.

Run with the wheel environment's Python in isolated mode, for example:
    /path/to/venv/bin/python -I /path/to/tests/packaging/smoke.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from contextlib import chdir
from importlib.metadata import metadata, version
from importlib.resources import files
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> None:
    sys.dont_write_bytecode = True
    import unrooted

    package_path = Path(unrooted.__file__).resolve()
    assert package_path.is_relative_to(Path(sys.prefix).resolve()), (
        f"Expected an installed wheel, imported {package_path}"
    )
    assert unrooted.__version__ == version("unrooted")
    package_metadata = metadata("unrooted")
    assert package_metadata["License-Expression"] == "MIT"
    assert package_metadata["License-File"] == "LICENSE"
    assert package_metadata["Summary"]
    assert package_metadata["Maintainer"]

    with TemporaryDirectory(prefix="unrooted-wheel-") as directory:
        workdir = Path(directory)
        os.environ["MPLBACKEND"] = "Agg"
        os.environ["MPLCONFIGDIR"] = str(workdir / "mpl-cache")
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

        import matplotlib.pyplot as plt
        import numpy as np
        import uproot

        from unrooted.io.root import load, load_efficiency, load_scatter
        from unrooted.plot import StyleSet
        from unrooted.plot.mpl import (
            generate_stylesheet,
            overlay,
            plot,
            plot_scatter,
            stack,
        )

        resources = files("unrooted").joinpath("resources")
        for target, logo_stem in [("odd", "odd_tech_light"), ("sd", "super_duper")]:
            palette = StyleSet.load(target)
            assert palette.name == target
            assert len(palette) == 4
            assets = resources.joinpath(target)
            for stem in [logo_stem, f"{logo_stem}_line"]:
                for extension in ["png", "svg"]:
                    assert assets.joinpath(f"{stem}.{extension}").read_bytes()
            preview = assets.joinpath("stylesheet.png").read_bytes()
            with chdir(workdir):
                output = generate_stylesheet(target)
                assert output == Path(f"{target}_stylesheet.png")
                assert output.stat().st_size > 0
            assert assets.joinpath("stylesheet.png").read_bytes() == preview

        explicit_output = workdir / "explicit-preview.png"
        assert generate_stylesheet("odd", explicit_output) == explicit_output
        assert explicit_output.stat().st_size > 0

        # Synthetic data keeps this check independent of repository/LFS fixtures.
        root_path = workdir / "data.root"
        edges = np.array([0.0, 1.0, 2.0, 3.0])
        with uproot.recreate(root_path) as root_file:
            root_file["hx"] = (np.array([2.0, 4.0, 3.0]), edges)
            root_file["hy"] = (np.array([3.0, 2.0, 5.0]), edges)
            root_file["passed"] = (np.array([0.0, 2.0, 4.0]), edges)
            root_file["total"] = (np.array([4.0, 4.0, 4.0]), edges)
            tree = root_file.mktree("tree", {"x": "float64", "y": "float64"})
            tree.extend({"x": np.array([0.0, 1.0]), "y": np.array([2.0, 3.0])})

        efficiency = load_efficiency(root_path, "passed", "total")
        np.testing.assert_allclose(
            efficiency.spread_min, [0, 0.5 - np.sqrt(5) / 10, 0.8]
        )
        np.testing.assert_allclose(
            efficiency.spread_max, [0.2, 0.5 + np.sqrt(5) / 10, 1]
        )
        np.testing.assert_allclose(efficiency.variances, [0, 0.0625, 0])

        h1, h2 = load(root_path, "hx"), load(root_path, "hy")
        ax = plot(h1)
        ax.figure.savefig(workdir / "api.png")
        plt.close(ax.figure)
        ax_main, ax_ratio = overlay([h1, h2], ratio=True)
        assert ax_ratio is not None
        ax_main.figure.savefig(workdir / "overlay.png")
        plt.close(ax_main.figure)
        ax_stack = stack([h1, h2], labels=["A", "B"])
        ax_stack.figure.savefig(workdir / "stack.png")
        plt.close(ax_stack.figure)

        points = load_scatter(root_path, "tree", "x", "y")
        selected = load_scatter(
            root_path, "tree", "x", "y", entry_start=1, entry_stop=2
        )
        np.testing.assert_array_equal(selected.x, [1.0])
        np.testing.assert_array_equal(selected.y, [3.0])
        sampled = load_scatter(
            root_path,
            "tree",
            "x",
            "y",
            max_points=1,
            sampling="random",
            seed=71,
            step_size=1,
        )
        assert sampled.sampled and sampled.source_points == 2 and len(sampled.x) == 1
        ax_scatter = plot_scatter(points, label="Points")
        ax_scatter.figure.savefig(workdir / "scatter.png")
        plt.close(ax_scatter.figure)

        cli_name = "unrooted.exe" if os.name == "nt" else "unrooted"
        cli = Path(sys.executable).parent / cli_name
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)

        def run_cli(*arguments: str, expected_code: int = 0) -> str:
            result = subprocess.run(
                [str(cli), *arguments],
                cwd=workdir,
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert result.returncode == expected_code, result.stderr
            assert "Traceback" not in result.stderr
            return result.stdout if expected_code == 0 else result.stderr

        assert "--input" in run_cli("--help")
        base_args = ["--input", str(root_path), "--draw", "hist:hx"]
        assert run_cli(*base_args, "--backend", "terminal").strip()
        assert run_cli(
            "--input",
            str(root_path),
            "--draw",
            "branch:tree:x",
            "--entry-start",
            "1",
            "--entry-stop",
            "2",
            "--backend",
            "terminal",
        ).strip()
        sampled_output = workdir / "sampled.png"
        run_cli(
            "--input",
            str(root_path),
            "--draw",
            "branch:tree:scatter:x:y",
            "--max-points",
            "1",
            "--sampling",
            "random",
            "--seed",
            "71",
            "--step-size",
            "1",
            "--output",
            str(sampled_output),
        )
        assert sampled_output.stat().st_size > 0
        assert "unrooted: error loading data:" in run_cli(
            "--input",
            str(workdir / "missing.root"),
            "--draw",
            "hist:hx",
            expected_code=1,
        )
        assert "--ratio-range requires --add ratio" in run_cli(
            *base_args,
            "--ratio-range",
            "0",
            "2",
            expected_code=2,
        )
        if find_spec("plotly") is None:
            assert "unrooted[plotly]" in run_cli(
                *base_args,
                "--backend",
                "plotly",
                "--output",
                str(workdir / "plot.html"),
                expected_code=1,
            )
        else:
            from unrooted.plot.plotly import plot as plot_interactive
            from unrooted.plot.plotly import plot_scatter as plot_points_interactive
            from unrooted.plot.plotly import stack as stack_interactive

            plot_interactive(h1).write_html(workdir / "api.html")
            stack_interactive([h1, h2], labels=["A", "B"]).write_html(
                workdir / "stack.html"
            )
            plot_points_interactive(sampled).write_html(workdir / "scatter.html")
            run_cli(
                *base_args, "--backend", "plotly", "--output", str(workdir / "cli.html")
            )
            for name in ["api.html", "scatter.html", "stack.html", "cli.html"]:
                assert (workdir / name).stat().st_size > 0
        for target in ["odd", "sd"]:
            args = [*base_args, "--palette", target]
            output = workdir / f"cli-{target}.png"
            run_cli(*args, "--output", str(output))
            assert output.stat().st_size > 0

        for name in ["api.png", "overlay.png", "scatter.png", "stack.png"]:
            assert (workdir / name).stat().st_size > 0

    print("Installed wheel smoke checks passed: palettes, assets, API, and CLI.")


if __name__ == "__main__":
    main()
