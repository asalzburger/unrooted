"""MkDocs pre-build hook — generates example outputs into docs/assets/examples/.

Matplotlib examples are saved as PNG; Plotly examples as self-contained HTML;
terminal examples as plain .txt files (embedded via --8<-- snippets).
The build fails (raises RuntimeError) if any generation step errors out.
"""
from __future__ import annotations

from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent
_DATA = _PROJECT_ROOT / "tests" / "data" / "root" / "tests_input.root"
_EFF_DATA = _PROJECT_ROOT / "tests" / "data" / "root" / "tests_efficiency.root"
_BOOST_DATA = _PROJECT_ROOT / "tests" / "data" / "boost" / "test_input_boost.pkl"
_OUT = Path(__file__).parent / "assets" / "examples"


def on_pre_build(config, **kwargs) -> None:  # noqa: ANN001
    _OUT.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for name, fn in [
        ("matplotlib examples", _gen_mpl),
        ("plotly examples", _gen_plotly),
        ("terminal examples", _gen_terminal),
        ("profile examples", _gen_profile),
        ("efficiency examples", _gen_efficiency),
        ("style preset examples", _gen_style_presets),
        ("boost-histogram examples", _gen_boost),
    ]:
        try:
            fn()
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    if errors:
        raise RuntimeError(
            "Example generation failed:\n" + "\n".join(f"  • {e}" for e in errors)
        )


def _gen_mpl() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from unrooted.io.root import load
    from unrooted.plot.mpl import overlay, plot
    from unrooted.plot.style_set import StyleSet

    ss = StyleSet.load("odd")
    hx = load(_DATA, "hx")
    hy = load(_DATA, "hy")
    hxy = load(_DATA, "hxy")

    # 1D styled
    fig, ax = plt.subplots(figsize=(8, 5))
    plot(hx, ax=ax, style=ss[0])
    ax.set_title("hx — ODD style palette")
    fig.tight_layout()
    fig.savefig(_OUT / "mpl_hx_styled.png", dpi=120, bbox_inches="tight")
    plt.close(fig)

    # Overlay with ratio panel — B's style flows into the ratio panel
    sx = ss[0]
    sy = ss[1]
    main_ax, _ = overlay([hx, hy], labels=["hx", "hy"], styles=[sx, sy], ratio=True)
    main_ax.set_title("Overlay: hx (ref) vs hy")
    from matplotlib.figure import Figure as MplFigure  # noqa: PLC0415
    ratio_fig = main_ax.get_figure()
    assert isinstance(ratio_fig, MplFigure)
    ratio_fig.tight_layout()
    ratio_fig.savefig(_OUT / "mpl_overlay_ratio.png", dpi=120, bbox_inches="tight")
    plt.close(ratio_fig)

    # 2D heatmap
    fig, ax = plt.subplots(figsize=(6, 5))
    plot(hxy, ax=ax)
    ax.set_title("hxy — 2D heatmap")
    fig.tight_layout()
    fig.savefig(_OUT / "mpl_hxy.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def _gen_plotly() -> None:
    from unrooted.io.root import load
    from unrooted.plot.plotly import overlay, plot
    from unrooted.plot.style import HistogramStyle
    from unrooted.plot.style_set import StyleSet

    ss = StyleSet.load("odd")
    hx = load(_DATA, "hx")
    hy = load(_DATA, "hy")
    hxy = load(_DATA, "hxy")

    fig = plot(hx, style=ss[0])
    fig.update_layout(title="hx — ODD style palette", height=420)
    _write_html(fig, "plotly_hx_styled.html")

    fig = overlay(
        [hx, hy],
        labels=["hx", "hy"],
        styles=[
            HistogramStyle(
                line_color=ss[0].line_color, fill_alpha=0.10, error_display="bar"
            ),
            HistogramStyle(
                line_color=ss[1].line_color, line_style="--", error_display="band"
            ),
        ],
        ratio=True,
    )
    fig.update_layout(title="Overlay: hx vs hy with ratio", height=560)
    _write_html(fig, "plotly_overlay_ratio.html")

    fig = plot(hxy)
    fig.update_layout(title="hxy — 2D heatmap", height=480)
    _write_html(fig, "plotly_hxy.html")


def _gen_terminal() -> None:
    from unrooted.io.root import load
    from unrooted.plot.terminal import overlay, plot

    hx = load(_DATA, "hx")
    hy = load(_DATA, "hy")

    (_OUT / "terminal_hx.txt").write_text(plot(hx, max_lines=20), encoding="utf-8")
    (_OUT / "terminal_overlay.txt").write_text(
        overlay([hx, hy], labels=["hx", "hy"], max_lines=20), encoding="utf-8"
    )
    (_OUT / "terminal_overlay_ratio.txt").write_text(
        overlay([hx, hy], labels=["hx", "hy"], max_lines=20, ratio=True),
        encoding="utf-8",
    )


def _gen_profile() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from unrooted.io.root import load
    from unrooted.plot.mpl import overlay, plot
    from unrooted.plot.style import HistogramStyle, LineStyle
    from unrooted.plot.style_set import StyleSet

    ss = StyleSet.load("odd")
    prof_x = load(_DATA, "profX")
    prof_y = load(_DATA, "profY")

    # Single TProfile using as_profile() preset
    fig, ax = plt.subplots(figsize=(8, 5))
    plot(prof_x, ax=ax, style=HistogramStyle.as_profile().with_color(ss.colors[0]))
    ax.set_title("TProfile: profX mean ± σ_y spread")
    fig.tight_layout()
    fig.savefig(_OUT / "mpl_profile.png", dpi=120, bbox_inches="tight")
    plt.close(fig)

    # Overlay two profiles — B's dashed style flows into the ratio panel
    sx = HistogramStyle.as_profile().with_color(ss.colors[0])
    sy = HistogramStyle.as_profile(line_style=LineStyle.DASHED).with_color(ss.colors[1])
    main_ax, _ = overlay(
        [prof_x, prof_y], labels=["profX", "profY"], styles=[sx, sy], ratio=True
    )
    main_ax.set_title("TProfile overlay: profX vs profY")
    from matplotlib.figure import Figure as MplFigure  # noqa: PLC0415
    ratio_fig = main_ax.get_figure()
    assert isinstance(ratio_fig, MplFigure)
    ratio_fig.tight_layout()
    ratio_fig.savefig(_OUT / "mpl_profile_overlay.png", dpi=120, bbox_inches="tight")
    plt.close(ratio_fig)


def _gen_efficiency() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from unrooted.io.root import load_efficiency
    from unrooted.plot.mpl import plot
    from unrooted.plot.style import HistogramStyle
    from unrooted.plot.style_set import StyleSet

    ss = StyleSet.load("odd")
    eff = load_efficiency(_EFF_DATA, "h_passed", "h_total")

    # as_efficiency() preset: markers + error bars + spread band
    fig, ax = plt.subplots(figsize=(8, 5))
    plot(eff, ax=ax, style=HistogramStyle.as_efficiency().with_color(ss.colors[0]))
    ax.set_ylim(0, 1.1)
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8)
    ax.set_title("Efficiency: passed / total with ±σ CI")
    fig.tight_layout()
    fig.savefig(_OUT / "mpl_efficiency.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def _gen_style_presets() -> None:
    """Generate a panel showing all five named style presets side by side."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    from unrooted.core.axis import Axis
    from unrooted.core.histogram import Histogram
    from unrooted.plot.mpl.histogram import plot
    from unrooted.plot.style import HistogramStyle, LineStyle
    from unrooted.plot.style_set import StyleSet

    ss = StyleSet.load("odd")

    rng = np.random.default_rng(7)
    edges = np.linspace(-3, 3, 31)
    data = rng.normal(0, 1, 600)
    values, _ = np.histogram(data, bins=edges)
    values = values.astype(float)
    spread_half = np.sqrt(values) * 0.8
    h = Histogram(
        axes=[Axis(edges=edges, label="x")],
        values=values,
        variances=values.copy(),
        spread_min=np.maximum(values - spread_half, 0),
        spread_max=values + spread_half,
    )

    presets = [
        ("as_hist()", HistogramStyle.as_hist()),
        ("as_line()", HistogramStyle.as_line()),
        ("as_markers()", HistogramStyle.as_markers()),
        ("as_efficiency()", HistogramStyle.as_efficiency()),
        ("as_profile()", HistogramStyle.as_profile()),
    ]

    fig, axes = plt.subplots(1, 5, figsize=(18, 4), sharey=True)
    for ax, (title, style) in zip(axes, presets):
        plot(h, ax=ax, style=style.with_color(ss.colors[0]))
        ax.set_title(title, fontsize=10)
    fig.suptitle("Named style presets", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(_OUT / "mpl_style_presets.png", dpi=120, bbox_inches="tight")
    plt.close(fig)

    # Ratio panel showing B's style in the ratio panel
    from unrooted.io.root import load
    from unrooted.plot.mpl import overlay

    hx = load(_DATA, "hx")
    hy = load(_DATA, "hy")
    sx = HistogramStyle.as_hist().with_color(ss.colors[0])
    sy = HistogramStyle.as_line(
        line_style=LineStyle.DASHED, line_width=2.0, error_display="bar"
    ).with_color(ss.colors[1])
    main_ax, _ = overlay(
        [hx, hy], ratio=True, labels=["hx (ref)", "hy"], styles=[sx, sy]
    )
    main_ax.set_title("Ratio panel inherits B's line style and color")
    from matplotlib.figure import Figure as MplFigure  # noqa: PLC0415
    ratio_fig = main_ax.get_figure()
    assert isinstance(ratio_fig, MplFigure)
    ratio_fig.tight_layout()
    ratio_fig.savefig(_OUT / "mpl_ratio_styled.png", dpi=120, bbox_inches="tight")
    plt.close(ratio_fig)


def _gen_boost() -> None:
    import pickle

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from unrooted.io.boost import load, load_efficiency
    from unrooted.plot.mpl import plot
    from unrooted.plot.style import HistogramStyle
    from unrooted.plot.style_set import StyleSet

    ss = StyleSet.load("odd")

    with open(_BOOST_DATA, "rb") as f:
        boost_data = pickle.load(f)

    # Profile
    prof = load(boost_data["nMeasurements_vs_eta"], name="nMeasurements_vs_eta")
    fig, ax = plt.subplots(figsize=(8, 5))
    plot(prof, ax=ax, style=HistogramStyle.as_profile().with_color(ss.colors[0]))
    ax.set_xlabel(prof.axes[0].label)
    ax.set_title("boost-histogram profile: nMeasurements mean ± σ_y")
    fig.tight_layout()
    fig.savefig(_OUT / "mpl_boost_profile.png", dpi=120, bbox_inches="tight")
    plt.close(fig)

    # Efficiency
    eff_data = boost_data["trackeff_vs_eta"]
    eff = load_efficiency(eff_data["accepted"], eff_data["total"], name="trackeff_vs_eta")
    fig, ax = plt.subplots(figsize=(8, 5))
    plot(eff, ax=ax, style=HistogramStyle.as_efficiency().with_color(ss.colors[1]))
    ax.set_ylim(0, 1.1)
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.8)
    ax.set_xlabel(eff.axes[0].label)
    ax.set_title("boost-histogram efficiency: trackeff vs η")
    fig.tight_layout()
    fig.savefig(_OUT / "mpl_boost_efficiency.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def _write_html(fig, filename: str) -> None:  # noqa: ANN001
    fig.write_html(
        str(_OUT / filename),
        include_plotlyjs="cdn",
        full_html=True,
        config={"responsive": True},
    )
