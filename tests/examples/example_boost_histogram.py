"""Example: load profile and efficiency from a boost-histogram pickle file.

Run with:
    uv run python tests/examples/example_boost_histogram.py
"""
from __future__ import annotations

import pickle
from pathlib import Path

import matplotlib.pyplot as plt

from unrooted.io.boost import load, load_efficiency
from unrooted.plot.mpl import plot
from unrooted.plot.style import HistogramStyle
from unrooted.plot.style_set import StyleSet

DATA = Path(__file__).parent.parent / "data" / "boost" / "test_input_boost.pkl"


def main() -> None:
    ss = StyleSet.load("odd")

    with open(DATA, "rb") as f:
        boost_data = pickle.load(f)

    # --- Profile (Mean storage) ---
    prof = load(boost_data["nMeasurements_vs_eta"], name="nMeasurements_vs_eta")
    print(f"profile: ndim={prof.ndim}, bins={prof.values.shape[0]}")
    print(f"  axis label: {prof.axes[0].label!r}")
    print(f"  spread available: {prof.spread_min is not None}")

    fig, ax = plt.subplots(figsize=(8, 5))
    plot(prof, ax=ax, style=HistogramStyle.as_profile().with_color(ss.colors[0]))
    ax.set_xlabel(prof.axes[0].label)
    ax.set_title("boost-histogram profile: nMeasurements mean ± σ_y")
    fig.tight_layout()
    plt.show()

    # --- Efficiency ---
    eff_data = boost_data["trackeff_vs_eta"]
    eff = load_efficiency(eff_data["accepted"], eff_data["total"], name="trackeff_vs_eta")
    print(f"\nefficiency: ndim={eff.ndim}, bins={eff.values.shape[0]}")
    print(f"  values range: [{eff.values.min():.3f}, {eff.values.max():.3f}]")
    print(f"  spread available: {eff.spread_min is not None}")

    fig, ax = plt.subplots(figsize=(8, 5))
    plot(eff, ax=ax, style=HistogramStyle.as_efficiency().with_color(ss.colors[1]))
    ax.set_ylim(0, 1.1)
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8)
    ax.set_xlabel(eff.axes[0].label)
    ax.set_title("boost-histogram efficiency: trackeff vs η")
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
