from __future__ import annotations

import argparse
import dataclasses
import math
import sys
from collections.abc import Callable
from pathlib import Path

from unrooted.core.histogram import Histogram
from unrooted.core.scatter import ScatterData
from unrooted.plot.style import HistogramStyle
from unrooted.plot.style_set import StyleSet

from ._draw_spec import AutoStyleHint, DrawSpec, parse_draw_spec
from ._load import resolve_loads

_LINESTYLE_MAP: dict[str, str] = {
    "solid": "-",
    "dashed": "--",
    "dotted": ":",
    "dashdot": "-.",
}

_STYLE_PRESETS: dict[str, Callable[..., HistogramStyle]] = {
    "hist": HistogramStyle.as_hist,
    "line": HistogramStyle.as_line,
    "markers": HistogramStyle.as_markers,
    "efficiency": HistogramStyle.as_efficiency,
    "profile": HistogramStyle.as_profile,
    "scatter": HistogramStyle.as_scatter,
}

_AUTO_STYLE_MAP: dict[AutoStyleHint, Callable[..., HistogramStyle]] = {
    "hist": HistogramStyle.as_hist,
    "profile": HistogramStyle.as_profile,
    "efficiency": HistogramStyle.as_efficiency,
    "scatter": HistogramStyle.as_scatter,
}

_VALID_ADD_TOKENS = {
    "ratio",
    "error_bar",
    "error_band",
    "error_continuous",
    "error_none",
    "spread_bar",
    "spread_band",
    "spread_continuous",
    "spread_none",
}


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
    for prefix in ("error_", "spread_"):
        modes = sorted(token for token in tokens if token.startswith(prefix))
        if len(modes) > 1:
            raise ValueError("Conflicting --add modes: " + ", ".join(modes))
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
            mode = token[len("error_") :]
            updates["error_display"] = None if mode == "none" else mode
        elif token.startswith("spread_"):
            mode = token[len("spread_") :]
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


def _finish_mpl(fig, args) -> None:
    import matplotlib.pyplot as plt

    try:
        fig.tight_layout()
        if args.output:
            try:
                fig.savefig(args.output)
            except Exception as exc:
                raise RuntimeError(
                    f"Cannot save figure to {args.output!r}: {exc}"
                ) from exc
        if args.show or not args.output:
            plt.show()
    finally:
        plt.close(fig)


def _run_mpl_scatter(args, scatters, labels, styles) -> None:
    from unrooted.plot.mpl import overlay_scatter

    ax = overlay_scatter(
        scatters, labels=labels if any(labels) else None, styles=styles
    )
    _apply_mpl_axes(ax, args.title, args.xlim, args.ylim)
    _apply_mpl_labels(ax, ax, args.xlabel, args.ylabel)
    _finish_mpl(ax.figure, args)


def _run_mpl(args, hists, labels, styles, ratio) -> None:
    from unrooted.plot.mpl import overlay as mpl_overlay
    from unrooted.plot.mpl import plot as mpl_plot

    ratio_range = tuple(args.ratio_range) if args.ratio_range else None
    if len(hists) == 1 and hists[0].ndim == 2:
        ax_main = mpl_plot(hists[0])
        ax_ratio = None
    else:
        ax_main, ax_ratio = mpl_overlay(
            hists,
            labels=labels if any(labels) else None,
            styles=styles,
            ratio=ratio,
            ratio_range=ratio_range,
        )
    _apply_mpl_axes(ax_main, args.title, args.xlim, args.ylim)
    _apply_mpl_labels(
        ax_main, ax_ratio if ax_ratio is not None else ax_main, args.xlabel, args.ylabel
    )
    _finish_mpl(ax_main.figure, args)


def _finish_plotly(fig, args, *, ratio: bool = False) -> None:
    if args.title:
        fig.update_layout(title_text=args.title)
    if ratio:
        if args.xlabel:
            fig.update_xaxes(title_text=args.xlabel, row=2, col=1)
        if args.ylabel:
            fig.update_yaxes(title_text=args.ylabel, row=1, col=1)
        if args.ylim:
            fig.update_yaxes(range=list(args.ylim), row=1, col=1)
    else:
        if args.xlabel:
            fig.update_xaxes(title_text=args.xlabel)
        if args.ylabel:
            fig.update_yaxes(title_text=args.ylabel)
        if args.ylim:
            fig.update_yaxes(range=list(args.ylim))
    if args.xlim:
        fig.update_xaxes(range=list(args.xlim))
    if args.output:
        try:
            if Path(args.output).suffix.lower() == ".html":
                fig.write_html(args.output)
            else:
                fig.write_image(args.output)
        except Exception as exc:
            hint = (
                " Static image export requires Kaleido and, with Kaleido 1+, "
                "a compatible Chrome/Chromium installation; use .html for "
                "interactive output."
                if Path(args.output).suffix.lower() != ".html"
                else ""
            )
            raise RuntimeError(
                f"Cannot export Plotly figure to {args.output!r}: {exc}.{hint}"
            ) from exc
    if args.show or not args.output:
        fig.show()


def _run_plotly_scatter(args, scatters, labels, styles) -> None:
    try:
        from unrooted.plot.plotly import overlay_scatter
    except ImportError as exc:
        raise RuntimeError(
            "Plotly is not installed. Install it with: pip install 'unrooted[plotly]'"
        ) from exc
    fig = overlay_scatter(
        scatters, labels=labels if any(labels) else None, styles=styles
    )
    _finish_plotly(fig, args)


def _run_plotly(args, hists, labels, styles, ratio) -> None:
    try:
        from unrooted.plot.plotly import overlay as plotly_overlay
        from unrooted.plot.plotly import plot as plotly_plot
    except ImportError as exc:
        raise RuntimeError(
            "Plotly is not installed. Install it with: pip install 'unrooted[plotly]'"
        ) from exc
    ratio_range = tuple(args.ratio_range) if args.ratio_range else None
    if len(hists) == 1:
        fig = plotly_plot(hists[0], style=styles[0], label=labels[0])
    else:
        fig = plotly_overlay(
            hists,
            labels=labels if any(labels) else None,
            styles=styles,
            ratio=ratio,
            ratio_range=ratio_range,
        )
    _finish_plotly(fig, args, ratio=ratio)


def _run_terminal(args, hists, labels, ratio) -> None:
    from unrooted.plot.terminal import overlay as term_overlay

    first = hists[0]
    if args.title or args.xlabel:
        axis = dataclasses.replace(
            first.axes[0], label=args.xlabel or first.axes[0].label
        )
        first = dataclasses.replace(first, axes=[axis], title=args.title or first.title)
        hists = [first, *hists[1:]]
    print(
        term_overlay(
            hists,
            labels=labels if any(labels) else None,
            max_lines=args.max_lines,
            ratio=ratio,
        )
    )


def _validate_options(args, specs, tokens, explicit) -> None:
    if len(args.input) != 1 and len(specs) != 1 and len(args.input) != len(specs):
        raise ValueError(
            "input/draw counts require 1 file + N specs, N files + 1 spec, "
            "or N files + N specs"
        )
    for name in ("xlim", "ylim", "ratio_range", "branch_range"):
        bounds = getattr(args, name)
        if bounds is not None and (
            not all(math.isfinite(value) for value in bounds) or bounds[0] >= bounds[1]
        ):
            raise ValueError(f"--{name.replace('_', '-')} requires finite MIN < MAX")
    if args.n_bins < 1:
        raise ValueError("--n-bins must be positive")
    if args.step_size < 1:
        raise ValueError("--step-size must be positive")
    if args.max_points is not None and args.max_points < 1:
        raise ValueError("--max-points must be positive")
    if args.seed < 0:
        raise ValueError("--seed must be nonnegative")
    if args.sampling == "random" and args.max_points is None:
        raise ValueError("--sampling random requires --max-points")
    if "--seed" in explicit and args.sampling != "random":
        raise ValueError("--seed requires --sampling random")
    if args.entry_start < 0 or (args.entry_stop is not None and args.entry_stop < 0):
        raise ValueError("--entry-start and --entry-stop must be nonnegative")
    if args.entry_stop is not None and args.entry_stop < args.entry_start:
        raise ValueError("--entry-stop must be greater than or equal to --entry-start")
    if explicit & {"--entry-start", "--entry-stop", "--step-size"} and not any(
        spec.draw_type == "branch" for spec in specs
    ):
        raise ValueError(
            "--entry-start, --entry-stop, and --step-size require a branch spec"
        )
    if args.max_lines < 5:
        raise ValueError("--max-lines must be at least 5")
    ratio = "ratio" in tokens
    if args.ratio_range and not ratio:
        raise ValueError("--ratio-range requires --add ratio")
    binned_branch = any(
        s.draw_type == "branch" and s.branch_sub_type != "scatter" for s in specs
    )
    if not binned_branch and ("--n-bins" in explicit or args.branch_range):
        raise ValueError(
            "--n-bins and --branch-range require a count/profile branch spec"
        )
    scatter_specs = [s.branch_sub_type == "scatter" for s in specs]
    if explicit & {"--max-points", "--sampling", "--seed"} and not all(scatter_specs):
        raise ValueError(
            "--max-points, --sampling, and --seed require scatter branch specs"
        )
    if any(scatter_specs) and not all(scatter_specs):
        raise ValueError("cannot mix scatter and histogram draw specs in one command")
    if all(scatter_specs):
        if ratio:
            raise ValueError("--add ratio is unsupported for scatter plots")
        if args.linestyle or (args.style and args.style != "scatter"):
            raise ValueError(
                "scatter plots support --style scatter and marker overrides"
            )
        if tokens - {"error_none", "spread_none"}:
            raise ValueError("scatter plots do not support error or spread display")
        if args.backend == "terminal":
            raise ValueError("scatter is unsupported by the terminal backend")
    if args.backend == "terminal":
        unsupported = []
        for name in (
            "output",
            "show",
            "ylabel",
            "xlim",
            "ylim",
            "ratio_range",
            "style",
            "marker",
            "linestyle",
        ):
            if getattr(args, name):
                unsupported.append(f"--{name.replace('_', '-')}")
        if "--palette" in explicit:
            unsupported.append("--palette")
        if tokens - {"ratio", "error_none", "spread_none"}:
            unsupported.append("error/spread display")
        if unsupported:
            raise ValueError(
                "terminal backend does not support " + ", ".join(unsupported)
            )
    elif "--max-lines" in explicit:
        raise ValueError("--max-lines requires --backend terminal")
    if args.backend == "plotly" and args.output:
        if Path(args.output).suffix.lower() not in {
            ".html",
            ".png",
            ".svg",
            ".pdf",
            ".jpg",
            ".jpeg",
            ".webp",
        }:
            raise ValueError(
                "Plotly output must be .html, .png, .svg, .pdf, .jpg, or .webp"
            )


def _validate_items(args, items, tokens) -> None:
    if "ratio" in tokens and len(items) < 2:
        raise ValueError("--add ratio requires at least two histograms")
    hists = [item for item in items if isinstance(item, Histogram)]
    if any(hist.ndim != 1 for hist in hists):
        if len(hists) != 1 or hists[0].ndim != 2:
            raise ValueError(
                "only a single 2D histogram or an overlay of 1D histograms is supported"
            )
        if args.backend == "terminal":
            raise ValueError("terminal backend only supports 1D histograms")
        if tokens or args.marker or args.linestyle or args.style or args.label:
            raise ValueError(
                "2D heatmaps do not support --add, --style, --marker, "
                "--linestyle, or --label"
            )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="unrooted",
        allow_abbrev=False,
        description="Plot histograms from ROOT files — no ROOT required.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
draw spec format
----------------
  TYPE:KEY[/path]              hist, th2, prof  (colons inside key act as path sep)
  eff:pass_key:total_key       efficiency from two TH1s
  branch:tree:x_branch         TTree count histogram
  branch:tree:prof:x:y         TTree profile histogram
  branch:tree:scatter:x:y      TTree scatter plot

  type aliases: hist=th1=h1, th2=h2, prof=profile=tprofile, eff=efficiency, branch=tree

  Examples:
    --draw hist:hx
    --draw prof:somedata/eta              (same as prof:somedata:eta)
    --draw eff:h_passed:h_total
    --draw branch:myTree:prof:eta:pt
    --draw branch:myTree:scatter:v_eta:t_X0

--add tokens (space- or colon-separated)
-----------------------------------------
  ratio                  ratio panel below main (all histogram backends)
  error_bar|band|continuous|none   error bar display mode
  spread_bar|band|continuous|none  spread-bound display mode

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
        "--input",
        "-i",
        nargs="+",
        required=True,
        metavar="FILE",
        help="ROOT input file(s)",
    )
    io_grp.add_argument(
        "--source",
        "-s",
        default="",
        metavar="KEY",
        help=(
            "Common path prefix inside the ROOT file(s),"
            " prepended to every histogram key"
        ),
    )
    io_grp.add_argument(
        "--draw",
        "-d",
        nargs="+",
        required=True,
        action="append",
        metavar="SPEC",
        dest="draw_specs",
        help="Draw spec(s); see below. Repeatable or space-separated.",
    )
    io_grp.add_argument(
        "--output",
        "-o",
        default="",
        metavar="FILE",
        help="Output file (.png/.svg/.pdf for mpl; .html/.png for plotly)",
    )

    plot_grp = p.add_argument_group("plot control")
    plot_grp.add_argument(
        "--add",
        "-a",
        nargs="+",
        action="append",
        default=None,
        metavar="OPT",
        dest="add_opts",
        help="Plot options (ratio, error_band, spread_continuous, …); repeatable",
    )
    plot_grp.add_argument(
        "--label",
        "-l",
        nargs="+",
        metavar="LABEL",
        help=(
            "Legend labels; one per dataset"
            " (default: draw key or, for N files + 1 spec, filename stem)"
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
        help="Graphical backend color palette (default: odd)",
    )
    plot_grp.add_argument(
        "--style",
        choices=list(_STYLE_PRESETS),
        default=None,
        metavar="PRESET",
        help="Style preset override: hist, line, markers, efficiency, profile, scatter "
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
        help="Graphical backends: show the figure even when --output is given",
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
        help="Graphical ratio y-axis limits (requires --add ratio)",
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
    branch_grp.add_argument(
        "--entry-start",
        type=int,
        default=0,
        metavar="N",
        help="First tree entry to include, before flattening (default: 0)",
    )
    branch_grp.add_argument(
        "--entry-stop",
        type=int,
        default=None,
        metavar="N",
        help="First tree entry to exclude (default: end of tree)",
    )
    branch_grp.add_argument(
        "--step-size",
        type=int,
        default=100_000,
        metavar="N",
        help="Maximum tree entries per chunk, not bytes (default: 100000)",
    )
    branch_grp.add_argument(
        "--max-points",
        type=int,
        default=None,
        metavar="N",
        help="Explicit scatter point limit per dataset (default: no limit)",
    )
    branch_grp.add_argument(
        "--sampling",
        choices=["error", "random"],
        default="error",
        help="Over-limit scatter policy: fail or sample uniformly (default: error)",
    )
    branch_grp.add_argument(
        "--seed",
        type=int,
        default=0,
        metavar="N",
        help="Random sampling seed, nonnegative (default: 0; "
        "requires --sampling random)",
    )

    p.add_argument(
        "--max-lines",
        type=int,
        default=40,
        metavar="N",
        help="Terminal backend: character rows, at least 5 (default: 40)",
    )

    return p


def main(argv: list[str] | None = None) -> None:
    """Run the CLI; invalid arguments exit 2 and operational failures exit 1."""
    parser = build_parser()
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(raw_argv)
    explicit = {token.split("=", 1)[0] for token in raw_argv if token.startswith("--")}
    raw_specs = [spec for group in args.draw_specs for spec in group]
    raw_add = [token for group in (args.add_opts or []) for token in group]
    try:
        specs = [parse_draw_spec(raw) for raw in raw_specs]
        add_tokens = _parse_add_tokens(raw_add)
        _validate_options(args, specs, add_tokens, explicit)
    except ValueError as exc:
        parser.error(str(exc))
    ratio = "ratio" in add_tokens
    branch_range = tuple(args.branch_range) if args.branch_range else None
    try:
        loaded = resolve_loads(
            args.input,
            specs,
            args.source,
            n_bins=args.n_bins,
            branch_range=branch_range,
            entry_start=args.entry_start,
            entry_stop=args.entry_stop,
            step_size=args.step_size,
            max_points=args.max_points,
            sampling=args.sampling,
            seed=args.seed,
        )
    except Exception as exc:
        sys.exit(f"unrooted: error loading data: {exc}")
    items = [item for item, _ in loaded]
    try:
        _validate_items(args, items, add_tokens)
        if args.label and len(args.label) != len(items):
            raise ValueError(
                f"--label: expected {len(items)} value(s), got {len(args.label)}"
            )
    except ValueError as exc:
        parser.error(str(exc))
    labels = args.label if args.label else [hint or item.name for item, hint in loaded]
    for item, label in zip(items, labels):
        if isinstance(item, ScatterData) and item.sampled:
            print(
                f"unrooted: {label}: sampled {len(item.x)} of {item.source_points} "
                f"points uniformly (seed={item.sample_seed})",
                file=sys.stderr,
            )
    all_scatter = all(isinstance(item, ScatterData) for item in items)
    try:
        styles = []
        if args.backend != "terminal":
            ss = StyleSet.load(args.palette)
            active_specs = (
                specs if len(specs) == len(items) else [specs[0]] * len(items)
            )
            raw_markers, raw_linestyles = args.marker or [], args.linestyle or []
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
        if args.backend == "mpl":
            if all_scatter:
                _run_mpl_scatter(args, items, labels, styles)
            else:
                _run_mpl(args, items, labels, styles, ratio)
        elif args.backend == "plotly":
            if all_scatter:
                _run_plotly_scatter(args, items, labels, styles)
            else:
                _run_plotly(args, items, labels, styles, ratio)
        else:
            _run_terminal(args, items, labels, ratio)
    except Exception as exc:
        sys.exit(f"unrooted: error: {exc}")


if __name__ == "__main__":
    main()
