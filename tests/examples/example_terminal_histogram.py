"""Example: unicode terminal histogram plots.

Run with:
    uv run python tests/examples/example_terminal_histogram.py
"""
from __future__ import annotations

from pathlib import Path

from unrooted.io.root import load
from unrooted.plot.terminal import overlay, plot

DATA = Path(__file__).parent.parent / 'data' / 'root' / 'tests_input.root'


def main() -> None:
    hx = load(DATA, 'hx')
    hy = load(DATA, 'hy')

    # --- single histogram ---
    print('=== hx — single histogram ===')
    print(plot(hx, max_lines=30))

    print()

    # --- overlay with legend ---
    print('=== hx vs hy — overlay ===')
    print(overlay([hx, hy], labels=['hx', 'hy'], max_lines=30))


if __name__ == '__main__':
    main()
