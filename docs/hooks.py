"""MkDocs pre-build hook — generates example outputs into docs/assets/examples/.

Matplotlib examples are saved as PNG; Plotly examples as self-contained HTML.
The build fails (raises RuntimeError) if any generation step errors out.
"""
from __future__ import annotations

from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent
_DATA = _PROJECT_ROOT / "tests" / "data" / "root" / "tests_input.root"
_OUT = Path(__file__).parent / "assets" / "examples"


def on_pre_build(config, **kwargs) -> None:  # noqa: ANN001
    _OUT.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for name, fn in [
        ("matplotlib examples", _gen_mpl),
        ("plotly examples", _gen_plotly),
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

    # Overlay with ratio panel
    main_ax, _ = overlay([hx, hy], labels=["hx", "hy"], styles=[ss[0], ss[1]], ratio=True)
    main_ax.set_title("Overlay: hx (ref) vs hy")
    fig = main_ax.get_figure()
    fig.tight_layout()
    fig.savefig(_OUT / "mpl_overlay_ratio.png", dpi=120, bbox_inches="tight")
    plt.close(fig)

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
            HistogramStyle(line_color=ss[0].line_color, fill_alpha=0.10, error_display="bar"),
            HistogramStyle(line_color=ss[1].line_color, line_style="--", error_display="band"),
        ],
        ratio=True,
    )
    fig.update_layout(title="Overlay: hx vs hy with ratio", height=560)
    _write_html(fig, "plotly_overlay_ratio.html")

    fig = plot(hxy)
    fig.update_layout(title="hxy — 2D heatmap", height=480)
    _write_html(fig, "plotly_hxy.html")


def _write_html(fig, filename: str) -> None:  # noqa: ANN001
    fig.write_html(
        str(_OUT / filename),
        include_plotlyjs="cdn",
        full_html=True,
        config={"responsive": True},
    )
