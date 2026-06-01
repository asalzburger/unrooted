"""Example: drive unrooted from Python code via the CLI entry point.

This mirrors what you would type in a terminal but lets you call the same
logic from a script or notebook without spawning a subprocess.

Run with:
    uv run python tests/examples/example_cli.py
"""
from __future__ import annotations

from pathlib import Path

from unrooted.cli.main import main

DATA = str(Path(__file__).parent.parent / "data" / "root" / "tests_input.root")
EFF = str(Path(__file__).parent.parent / "data" / "root" / "tests_efficiency.root")


def run(*args: str) -> None:
    print(f"\n>>> unrooted {' '.join(args)}")
    main(list(args))


# --- 1. Single TH1 histogram, saved to a file ---
run(
    "--input", DATA,
    "--draw", "hist:hx",
    "--title", "Single TH1 — hx",
    "--output", "/tmp/cli_hx.png",
)

# --- 2. Overlay two histograms with a ratio panel ---
run(
    "--input", DATA,
    "--draw", "hist:hx", "hist:hy",
    "--label", "hx", "hy",
    "--add", "ratio",
    "--title", "Overlay with ratio",
    "--output", "/tmp/cli_overlay_ratio.png",
)

# --- 3. Profile histogram with continuous spread band ---
run(
    "--input", DATA,
    "--draw", "prof:profX",
    "--add", "spread_continuous",
    "--title", "TProfile — continuous spread",
    "--output", "/tmp/cli_profile.png",
)

# --- 4. Efficiency histogram ---
run(
    "--input", EFF,
    "--draw", "eff:h_passed:h_total",
    "--title", "Efficiency",
    "--output", "/tmp/cli_efficiency.png",
)

# --- 5. Overlay same key from two files (file-as-label) ---
run(
    "--input", DATA, DATA,
    "--draw", "hist:hx",
    "--add", "ratio",
    "--title", "Same key, two files",
    "--output", "/tmp/cli_two_files.png",
)

# --- 6. Terminal backend — printed to stdout ---
run(
    "--input", DATA,
    "--draw", "hist:hx",
    "--backend", "terminal",
)

print("\nAll CLI examples complete — PNGs written to /tmp/cli_*.png")
