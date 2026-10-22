"""Execute the actual introductory Python/CLI examples against synthetic data.

Run in the contributor environment with Plotly installed:
    uv run --no-sync python -I tests/documentation/smoke.py
Only browser display is intercepted; loading, plotting, and export run normally.
"""

from __future__ import annotations

import io
import os
import pickle
import re
import shlex
import subprocess
import sys
from contextlib import chdir, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    with TemporaryDirectory(prefix="unrooted-doc-examples-") as directory:
        workdir = Path(directory)
        os.environ["MPLBACKEND"] = "Agg"
        os.environ.setdefault("MPLCONFIGDIR", str(workdir / "mpl"))

        import boost_histogram as bh
        import matplotlib.pyplot as plt
        import numpy as np
        import plotly.graph_objects as go
        import uproot

        edges = np.arange(4, dtype=float)
        with uproot.recreate(workdir / "data.root") as root_file:
            root_file["hx"] = (np.array([2.0, 4.0, 3.0]), edges)
            root_file["hy"] = (np.array([3.0, 2.0, 5.0]), edges)
            tree = root_file.mktree("tree", {"x": "float64", "y": "float64"})
            tree.extend(
                {"x": np.array([0.0, 1.0, 2.0]), "y": np.array([2.0, 3.0, 4.0])}
            )

        counts = bh.Histogram(bh.axis.Variable(edges))
        counts.view()[:] = [2, 4, 3]
        accepted = bh.Histogram(bh.axis.Variable(edges))
        accepted.view()[:] = [1, 2, 2]
        profile = bh.Histogram(bh.axis.Variable(edges), storage=bh.storage.Mean())
        profile.fill([0.5, 0.5, 1.5, 1.5, 2.5, 2.5], sample=[1, 3, 2, 4, 3, 5])
        with (workdir / "histograms.pkl").open("wb") as stream:
            pickle.dump(
                {
                    "hx": counts,
                    "counts": counts,
                    "profile": profile,
                    "accepted": accepted,
                    "total": counts,
                },
                stream,
            )

        blocks_run = 0
        with chdir(workdir), patch.object(go.Figure, "show") as show:
            for document in (ROOT / "README.md", ROOT / "docs/getting-started.md"):
                namespace = {"__name__": "__documentation__"}
                blocks = re.findall(
                    r"^```python\n(.*?)^```",
                    document.read_text(),
                    re.MULTILINE | re.DOTALL,
                )
                assert blocks, f"No Python examples found in {document}"
                for number, code in enumerate(blocks, 1):
                    try:
                        with redirect_stdout(io.StringIO()):
                            exec(
                                compile(code, f"{document}:block-{number}", "exec"),
                                namespace,
                            )
                    finally:
                        plt.close("all")
                    blocks_run += 1
                for name in ("fig", "fig2"):
                    if isinstance(namespace.get(name), go.Figure):
                        namespace[name].write_html(workdir / f"{name}.html")
            assert show.call_count == 2

            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            usage = (ROOT / "README.md").read_text().split("## Usage", 1)[1]
            commands = re.findall(r"^unrooted .+$", usage, re.MULTILINE)
            assert len(commands) == 2
            cli = Path(sys.executable).parent / "unrooted"
            for command in commands:
                result = subprocess.run(
                    [str(cli), *shlex.split(command)[1:]],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                assert result.returncode == 0, result.stderr

        for name in (
            "histogram.png",
            "overlay.png",
            "hx.png",
            "hx_styled.png",
            "fig.html",
            "fig2.html",
        ):
            assert (workdir / name).stat().st_size > 0
        assert not plt.get_fignums()
    print(
        f"Documentation smoke checks passed: {blocks_run} Python blocks "
        "and 2 CLI examples."
    )


if __name__ == "__main__":
    main()
