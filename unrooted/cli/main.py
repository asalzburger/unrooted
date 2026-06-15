from __future__ import annotations

import argparse
import dataclasses
import sys
from collections.abc import Callable
from typing import Literal

from unrooted.plot.style import HistogramStyle
from unrooted.plot.style_set import StyleSet

from ._draw_spec import AutoStyleHint, DrawSpec, parse_draw_spec
from ._load import resolve_loads

_LINESTYLE_MAP: dict[str, str] = {
    "solid":   "-",
    "dashed":  "--",
    "dotted":  ":",
    "dashdot": "-.",
}

_STYLE_PRESETS: dict[str, Callable[..., HistogramStyle]] = {
    "hist": HistogramStyle.as_hist,
    "line": HistogramStyle.as_line,
    "markers": HistogramStyle.as_markers,
    "efficiency": HistogramStyle.as_efficiency,
    "profile": HistogramStyle.as_profile,
}

_AUTO_STYLE_MAP: dict[AutoStyleHint, Callable[..., HistogramStyle]] = {
    "hist": HistogramStyle.as_hist,
    "profile": HistogramStyle.as_profile,
    "efficiency": HistogramStyle.as_efficiency,
}

_VALID_ADD_TOKENS = {
    "ratio",
    "error_bar", "error_band", "error_continuous", "error_none",
    "spread_bar", "spread_band", "spread_continuous", "spread_none",
}

_DISPLAY_MODE = Literal["bar", "band", "continuous"]


def _parse_add_tokens(raw: list[str]) -> set[str]:
    tokens: set[str] = set()
    for item in raw:
        for part in item.split(":"):
            part = part.strip()
            if part and part not in _VALID_ADD_TOKENS:
                known = ", ".join(sorted(_VALID_ADD_TOKENS))
                raise ValueError(f"Unknown --add token {part!r}. Valid: {known}")
            if part:
                tokens.add(part)
    return tokens


def _build_style(
    spec: DrawSpec,
    color: str,
    add_tokens: set[str],
    style_preset: str | None,
    marker: str | None = None,
    linestyle: str | None = None,
) -> HistogramStyle:
    base_fn = (
        _STYLE_PRESETS[style_preset]
        if style_preset
        else _AUTO_STYLE_MAP[spec.auto_style]
    )
    style = base_fn()

    updates: dict[str, object] = {}
    for token in add_tokens:
        if token.startswith("error_"):
            mode = token[len("error_"):]
            updates["error_display"] = None if mode == "none" else mode
        elif token.startswith("spread_"):
            mode = token[len("spread_"):]
            updates["spread_display"] = None if mode == "none" else mode

    if marker is not None:
        updates["marker"] = marker
    if linestyle is not None:
        updates["line_style"] = _LINESTYLE_MAP[linestyle]

    if updates:
        style = dataclasses.replace(style, **updates)
    return style.with_color(color)


def _apply_mpl_axes(ax, title: str, xlim, ylim) -> None:
    if title:
        ax.set_title(title)
    if xlim:
        ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)


def _apply_mpl_labels(main_ax, bottom_ax, xlabel: str, ylabel: str) -> None:
    if ylabel:
        main_ax.set_ylabel(ylabel)
    if xlabel:
        bottom_ax.set_xlabel(xlabel)


def _run_mpl(args, hists, labels, styles, ratio) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure

    from unrooted.plot.mpl import overlay as mpl_overlay
    from unrooted.plot.mpl import plot as mpl_plot

    xlim = tuple(args.xlim) if args.xlim else None
    ylim = tuple(args.ylim) if args.ylim else None
    ratio_range = tuple(args.ratio_range) if args.ratio_range else None

    if len(hists) == 1 and hists[0].ndim == 2:
        ax = mpl_plot(hists[0], style=styles[0])
        fig = ax.get_figure()
        _apply_mpl_axes(ax, args.title, xlim, ylim)
        _apply_mpl_labels(ax, ax, args.xlabel, args.ylabel)
    else:
        show_labels = labels if any(labels) else None
        ax_main, ax_ratio = mpl_overlay(
            hists,
            labels=show_labels,
            styles=styles,
            ratio=ratio,
            ratio_range=ratio_range,
        )
        fig = ax_main.get_figure()
        _apply_mpl_axes(ax_main, args.title, xlim, ylim)
        _apply_mpl_labels(
            ax_main, ax_ratio or ax_main, args.xlabel, args.ylabel
        )

    if isinstance(fig, Figure):
        fig.tight_layout()
        if args.output:
            fig.savefig(args.output)
    if args.show or not args.output:
        plt.show()


def _run_plotly(args, hists, labels, styles, ratio) -> None:
    try:
        from unrooted.plot.plotly import overlay as plotly_overlay
        from unrooted.plot.plotly import plot as plotly_plot
    except ImportError:
        sys.exit(
            "Plotly is not installed. Install it with: pip install 'unrooted[plotly]'"
        )

    ratio_range = tuple(args.ratio_range) if args.ratio_range else None

    if len(hists) == 1:
        fig = plotly_plot(hists[0], style=styles[0])
    else:
        show_labels = labels if any(labels) else None
        fig = plotly_overlay(
            hists,
            labels=show_labels,
            styles=styles,
            ratio=ratio,
            ratio_range=ratio_range,
        )

    if args.title:
        fig.update_layout(title_text=args.title)
    if args.xlim:
        fig.update_xaxes(range=list(args.xlim))
    if args.ylim:
        fig.update_yaxes(range=list(args.ylim))

    if args.output:
        if args.output.endswith(".html"):
            fig.write_html(args.output)
        else:
            fig.write_image(args.output)
    if args.show or not args.output:
        fig.show()


def _run_terminal(args, hists, labels, ratio) -> None:
    from unrooted.plot.terminal import overlay as term_overlay
    from unrooted.plot.terminal import plot as term_plot

    if len(hists) == 1:
        print(term_plot(hists[0], max_lines=args.max_lines))
    else:
        show_labels = labels if any(labels) else None
        print(
            term_overlay(
                hists, labels=show_labels, max_lines=args.max_lines, ratio=ratio
            )
        )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="unrooted",
        description="Plot histograms from ROOT files — no ROOT required.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
draw spec format
----------------
  TYPE:KEY[/path]          hist, th2, prof  (colons inside key act as path sep)
  eff:pass_key:total_key   efficiency from two TH1s
  branch:tree:x_branch     TTree count histogram
  branch:tree:x:y_branch   TTree profile histogram

  type aliases: hist=th1=h1, th2=h2, prof=profile=tprofile, eff=efficiency, branch=tree

  Examples:
    --draw hist:hx
    --draw prof:somedata/eta          (same as prof:somedata:eta)
    --draw eff:h_passed:h_total
    --draw branch:myTree:eta:pt

--add tokens (space- or colon-separated)
-----------------------------------------
  ratio                  ratio panel below main (mpl/plotly only)
  error_bar|band|continuous|none   error bar display mode
  spread_bar|band|continuous|none  spread (σ) display mode

  Examples:
    --add ratio
    --add spread_continuous
    --add ratio:spread_band            (colon-joined)
    --add error_band --add spread_none (repeated)

ratio panel
-----------
  --ratio-range MIN MAX  fix the ratio panel y-axis (requires --add ratio)

  Example:
    --add ratio --ratio-range 0.5 1.5

marker / line-style overrides
------------------------------
  --marker SHAPE [SHAPE ...]     one value → all histograms; multiple → per-histogram
                                 (wraps cyclically)
                                 shapes: o s ^ D + x *
  --linestyle STYLE [STYLE ...]  one value → all; multiple → per-histogram
                                 styles: solid dashed dotted dashdot

  Examples:
    --style markers --marker s              all histograms: square markers
    --marker "*" + ^                        1st=star 2nd=cross 3rd=triangle
    --linestyle dashed                      all histograms: dashed line
    --linestyle solid dashed dotted         per-histogram line styles
    --style efficiency --marker "^" D       1st=triangle 2nd=diamond
""",
    )

    io_grp = p.add_argument_group("input / output")
    io_grp.add_argument(
        "--input", "-i",
        nargs="+",
        required=True,
        metavar="FILE",
        help="ROOT input file(s)",
    )
    io_grp.add_argument(
        "--source", "-s",
        default="",
        metavar="KEY",
        help=(
            "Common path prefix inside the ROOT file(s),"
            " prepended to every histogram key"
        ),
    )
    io_grp.add_argument(
        "--draw", "-d",
        nargs="+",
        required=True,
        action="append",
        metavar="SPEC",
        dest="draw_specs",
        help="Draw spec(s); see below. Repeatable or space-separated.",
    )
    io_grp.add_argument(
        "--output", "-o",
        default="",
        metavar="FILE",
        help="Output file (.png/.svg/.pdf for mpl; .html/.png for plotly)",
    )

    plot_grp = p.add_argument_group("plot control")
    plot_grp.add_argument(
        "--add", "-a",
        nargs="+",
        action="append",
        default=None,
        metavar="OPT",
        dest="add_opts",
        help="Plot options (ratio, error_band, spread_continuous, …); repeatable",
    )
    plot_grp.add_argument(
        "--label", "-l",
        nargs="+",
        metavar="LABEL",
        help=(
            "Legend labels; one per histogram"
            " (default: histogram name or filename stem)"
        ),
    )
    plot_grp.add_argument(
        "--backend",
        choices=["mpl", "plotly", "terminal"],
        default="mpl",
        help="Plotting backend (default: mpl)",
    )
    plot_grp.add_argument(
        "--palette",
        choices=["odd", "sd"],
        default="odd",
        help="Color palette (default: odd)",
    )
    plot_grp.add_argument(
        "--style",
        choices=list(_STYLE_PRESETS),
        default=None,
        metavar="PRESET",
        help="Style preset override: hist, line, markers, efficiency, profile "
             "(default: auto from draw type)",
    )
    plot_grp.add_argument(
        "--marker",
        nargs="+",
        choices=["o", "s", "^", "D", "+", "x", "*"],
        default=None,
        metavar="SHAPE",
        help=(
            "Marker shape(s).  One value → all histograms; multiple → assigned in"
            " order (wraps cyclically).  o=circle  s=square  ^=triangle  D=diamond"
            "  +=cross  x=x  *=star"
        ),
    )
    plot_grp.add_argument(
        "--linestyle",
        nargs="+",
        choices=["solid", "dashed", "dotted", "dashdot"],
        default=None,
        metavar="STYLE",
        help=(
            "Line style(s).  One value → all histograms; multiple → assigned in order "
            "(wraps cyclically).  solid  dashed  dotted  dashdot"
        ),
    )
    plot_grp.add_argument(
        "--show",
        action="store_true",
        help="Open an interactive window even when --output is given",
    )
    plot_grp.add_argument(
        "--title",
        default="",
        metavar="TEXT",
        help="Figure title",
    )
    plot_grp.add_argument(
        "--xlabel",
        default="",
        metavar="TEXT",
        help="X-axis label override (placed on the ratio panel when --add ratio)",
    )
    plot_grp.add_argument(
        "--ylabel",
        default="",
        metavar="TEXT",
        help="Y-axis label override for the main panel",
    )
    plot_grp.add_argument(
        "--xlim",
        nargs=2,
        type=float,
        metavar=("MIN", "MAX"),
        help="X-axis limits",
    )
    plot_grp.add_argument(
        "--ylim",
        nargs=2,
        type=float,
        metavar=("MIN", "MAX"),
        help="Y-axis limits",
    )
    plot_grp.add_argument(
        "--ratio-range",
        nargs=2,
        type=float,
        metavar=("MIN", "MAX"),
        help="Y-axis limits for the ratio panel (requires --add ratio)",
    )

    branch_grp = p.add_argument_group("branch loading (branch: draw type only)")
    branch_grp.add_argument(
        "--n-bins",
        type=int,
        default=100,
        metavar="N",
        help="Number of bins when loading from a TTree branch (default: 100)",
    )
    branch_grp.add_argument(
        "--branch-range",
        nargs=2,
        type=float,
        metavar=("LO", "HI"),
        help="Explicit axis range for branch loading; auto-detected if omitted",
    )

    p.add_argument(
        "--max-lines",
        type=int,
        default=40,
        metavar="N",
        help="Terminal backend: maximum character rows (default: 40)",
    )

    return p


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``unrooted`` command-line tool."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Flatten draw specs (action=append + nargs=+ gives list of lists)
    raw_specs: list[str] = [s for group in args.draw_specs for s in group]
    specs: list[DrawSpec] = []
    for raw in raw_specs:
        try:
            specs.append(parse_draw_spec(raw))
        except ValueError as e:
            parser.error(str(e))

    # Flatten and validate --add tokens
    raw_add = [tok for group in (args.add_opts or []) for tok in group]
    try:
        add_tokens = _parse_add_tokens(raw_add)
    except ValueError as e:
        parser.error(str(e))

    ratio = "ratio" in add_tokens

    # Load histograms
    branch_range = tuple(args.branch_range) if args.branch_range else None
    try:
        loaded = resolve_loads(
            args.input,
            specs,
            args.source,
            n_bins=args.n_bins,
            branch_range=branch_range,
        )
    except (ValueError, KeyError) as e:
        sys.exit(f"unrooted: error loading histograms: {e}")

    hists = [h for h, _ in loaded]
    label_hints = [hint for _, hint in loaded]

    # Resolve labels
    if args.label:
        if len(args.label) != len(hists):
            parser.error(
                f"--label: expected {len(hists)} value(s), got {len(args.label)}"
            )
        labels = args.label
    else:
        labels = [h.name or hint for h, hint in zip(hists, label_hints)]

    # Build per-histogram styles
    ss = StyleSet.load(args.palette)
    active_specs = specs if len(specs) == len(hists) else [specs[0]] * len(hists)
    raw_markers = args.marker or []
    raw_linestyles = args.linestyle or []
    styles = [
        _build_style(
            spec,
            ss.colors[i % len(ss.colors)],
            add_tokens,
            args.style,
            raw_markers[i % len(raw_markers)] if raw_markers else None,
            raw_linestyles[i % len(raw_linestyles)] if raw_linestyles else None,
        )
        for i, spec in enumerate(active_specs)
    ]

    # Dispatch to backend
    try:
        if args.backend == "mpl":
            _run_mpl(args, hists, labels, styles, ratio)
        elif args.backend == "plotly":
            _run_plotly(args, hists, labels, styles, ratio)
        else:
            _run_terminal(args, hists, labels, ratio)
    except Exception as e:  # noqa: BLE001
        sys.exit(f"unrooted: {e}")


if __name__ == "__main__":
    main()
