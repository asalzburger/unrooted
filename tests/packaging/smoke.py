"""Exercise an installed wheel with only its declared runtime dependencies.

Run with the wheel environment's Python in isolated mode, for example:
    /path/to/venv/bin/python -I /path/to/tests/packaging/smoke.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from contextlib import chdir
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> None:
    sys.dont_write_bytecode = True
    import unrooted

    package_path = Path(unrooted.__file__).resolve()
    assert package_path.is_relative_to(Path(sys.prefix).resolve()), (
        f"Expected an installed wheel, imported {package_path}"
    )

    with TemporaryDirectory(prefix="unrooted-wheel-") as directory:
        workdir = Path(directory)
        os.environ["MPLBACKEND"] = "Agg"
        os.environ["MPLCONFIGDIR"] = str(workdir / "mpl-cache")
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

        import matplotlib.pyplot as plt
        import numpy as np
        import uproot

        from unrooted.io.root import load
        from unrooted.plot import StyleSet
        from unrooted.plot.mpl import generate_stylesheet, overlay, plot

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

        h1, h2 = load(root_path, "hx"), load(root_path, "hy")
        ax = plot(h1)
        ax.figure.savefig(workdir / "api.png")
        plt.close(ax.figure)
        ax_main, ax_ratio = overlay([h1, h2], ratio=True)
        assert ax_ratio is not None
        ax_main.figure.savefig(workdir / "overlay.png")
        plt.close(ax_main.figure)

        cli_name = "unrooted.exe" if os.name == "nt" else "unrooted"
        cli = Path(sys.executable).parent / cli_name
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)

        def run_cli(*arguments: str) -> str:
            result = subprocess.run(
                [str(cli), *arguments],
                cwd=workdir,
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert result.returncode == 0, result.stderr
            return result.stdout

        assert "--input" in run_cli("--help")
        for target in ["odd", "sd"]:
            args = ["--input", str(root_path), "--draw", "hist:hx", "--palette", target]
            assert run_cli(*args, "--backend", "terminal").strip()
            output = workdir / f"cli-{target}.png"
            run_cli(*args, "--output", str(output))
            assert output.stat().st_size > 0

        for name in ["api.png", "overlay.png"]:
            assert (workdir / name).stat().st_size > 0

    print("Installed wheel smoke checks passed: palettes, assets, API, and CLI.")


if __name__ == "__main__":
    main()
