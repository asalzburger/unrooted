"""Tests for CLI argument parsing and style-building logic.

These tests exercise the parser and style builder in isolation — no ROOT files
are loaded, no matplotlib figures are rendered.
"""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from unrooted.cli._draw_spec import parse_draw_spec
from unrooted.cli.main import _build_style, _parse_add_tokens, build_parser
from unrooted.plot.style import HistogramStyle


# ---------------------------------------------------------------------------
# Parser smoke tests
# ---------------------------------------------------------------------------

def test_parser_minimal(tmp_path):
    dummy = tmp_path / "f.root"
    dummy.touch()
    p = build_parser()
    args = p.parse_args(["--input", str(dummy), "--draw", "hist:hx"])
    assert args.input == [str(dummy)]
    assert args.draw_specs == [["hist:hx"]]
    assert args.backend == "mpl"
    assert args.palette == "odd"
    assert args.output == ""


def test_parser_multi_draw():
    p = build_parser()
    args = p.parse_args(["--input", "f.root", "--draw", "hist:h1", "hist:h2"])
    flat = [s for g in args.draw_specs for s in g]
    assert flat == ["hist:h1", "hist:h2"]


def test_parser_repeated_draw():
    p = build_parser()
    args = p.parse_args(
        ["--input", "f.root", "--draw", "hist:h1", "--draw", "hist:h2"]
    )
    flat = [s for g in args.draw_specs for s in g]
    assert flat == ["hist:h1", "hist:h2"]


def test_parser_add_ratio():
    p = build_parser()
    args = p.parse_args(["--input", "f.root", "--draw", "hist:h1", "--add", "ratio"])
    assert args.add_opts == [["ratio"]]


def test_parser_add_colon_joined():
    p = build_parser()
    args = p.parse_args(
        ["--input", "f.root", "--draw", "hist:h1", "--add", "ratio:spread_continuous"]
    )
    raw = [tok for g in args.add_opts for tok in g]
    tokens = _parse_add_tokens(raw)
    assert "ratio" in tokens
    assert "spread_continuous" in tokens


def test_parser_xlim_ylim():
    p = build_parser()
    args = p.parse_args(
        ["--input", "f.root", "--draw", "hist:h", "--xlim", "-5", "5", "--ylim", "0", "100"]
    )
    assert args.xlim == [-5.0, 5.0]
    assert args.ylim == [0.0, 100.0]


def test_parser_ratio_range():
    p = build_parser()
    args = p.parse_args(
        ["--input", "f.root", "--draw", "hist:h", "--add", "ratio", "--ratio-range", "0.5", "1.5"]
    )
    assert args.ratio_range == [0.5, 1.5]


def test_parser_backend_choices():
    p = build_parser()
    for backend in ("mpl", "plotly", "terminal"):
        args = p.parse_args(["--input", "f.root", "--draw", "hist:h", "--backend", backend])
        assert args.backend == backend


# ---------------------------------------------------------------------------
# _parse_add_tokens
# ---------------------------------------------------------------------------

def test_add_tokens_ratio():
    assert "ratio" in _parse_add_tokens(["ratio"])


def test_add_tokens_colon():
    tokens = _parse_add_tokens(["ratio:spread_continuous"])
    assert tokens == {"ratio", "spread_continuous"}


def test_add_tokens_repeated():
    tokens = _parse_add_tokens(["ratio", "error_band"])
    assert tokens == {"ratio", "error_band"}


def test_add_tokens_unknown():
    with pytest.raises(ValueError, match="Unknown --add token"):
        _parse_add_tokens(["bogus_option"])


# ---------------------------------------------------------------------------
# _build_style
# ---------------------------------------------------------------------------

def test_build_style_hist_auto():
    spec = parse_draw_spec("hist:h")
    style = _build_style(spec, "#ff0000", set(), None)
    assert isinstance(style, HistogramStyle)
    assert style.line_color == "#ff0000"
    assert style.fill_alpha == 0.15  # as_hist default
    assert style.error_display == "bar"


def test_build_style_prof_auto():
    spec = parse_draw_spec("prof:p")
    style = _build_style(spec, "#00ff00", set(), None)
    assert style.spread_display == "band"  # as_profile default


def test_build_style_eff_auto():
    spec = parse_draw_spec("eff:p:t")
    style = _build_style(spec, "#0000ff", set(), None)
    assert style.marker == "o"
    assert style.spread_display == "band"  # as_efficiency default


def test_build_style_error_override():
    spec = parse_draw_spec("hist:h")
    style = _build_style(spec, "#000", {"error_band"}, None)
    assert style.error_display == "band"


def test_build_style_spread_override():
    spec = parse_draw_spec("prof:p")
    style = _build_style(spec, "#000", {"spread_continuous"}, None)
    assert style.spread_display == "continuous"


def test_build_style_none_suppresses():
    spec = parse_draw_spec("hist:h")
    style = _build_style(spec, "#000", {"error_none"}, None)
    assert style.error_display is None


def test_build_style_preset_override():
    spec = parse_draw_spec("hist:h")
    style = _build_style(spec, "#000", set(), "markers")
    assert style.marker == "o"
    assert style.line_style is None  # as_markers has no line


def test_build_style_profile_preset():
    spec = parse_draw_spec("hist:h")  # type would say hist but preset overrides
    style = _build_style(spec, "#000", set(), "profile")
    assert style.spread_display == "band"


# ---------------------------------------------------------------------------
# --marker flag
# ---------------------------------------------------------------------------

def test_build_style_marker_override():
    spec = parse_draw_spec("hist:h")
    style = _build_style(spec, "#000", set(), "markers", marker="s")
    assert style.marker == "s"


def test_build_style_marker_adds_to_hist():
    spec = parse_draw_spec("hist:h")
    style = _build_style(spec, "#000", set(), "hist", marker="*")
    assert style.marker == "*"


def test_build_style_marker_star():
    spec = parse_draw_spec("hist:h")
    style = _build_style(spec, "#000", set(), "markers", marker="*")
    assert style.marker == "*"


def test_parser_marker_single(tmp_path):
    dummy = tmp_path / "f.root"
    dummy.touch()
    p = build_parser()
    args = p.parse_args(["--input", str(dummy), "--draw", "hist:h", "--marker", "s"])
    assert args.marker == ["s"]


def test_parser_marker_multiple(tmp_path):
    dummy = tmp_path / "f.root"
    dummy.touch()
    p = build_parser()
    args = p.parse_args(
        ["--input", str(dummy), "--draw", "hist:h", "--marker", "*", "+", "^"]
    )
    assert args.marker == ["*", "+", "^"]


def test_parser_marker_invalid(tmp_path):
    dummy = tmp_path / "f.root"
    dummy.touch()
    p = build_parser()
    with pytest.raises(SystemExit):
        p.parse_args(["--input", str(dummy), "--draw", "hist:h", "--marker", "z"])


# ---------------------------------------------------------------------------
# --linestyle flag
# ---------------------------------------------------------------------------

def test_build_style_linestyle_override():
    spec = parse_draw_spec("hist:h")
    style = _build_style(spec, "#000", set(), "hist", linestyle="dashed")
    assert style.line_style == "--"


def test_build_style_linestyle_dotted():
    spec = parse_draw_spec("hist:h")
    style = _build_style(spec, "#000", set(), "line", linestyle="dotted")
    assert style.line_style == ":"


def test_build_style_linestyle_dashdot():
    spec = parse_draw_spec("hist:h")
    style = _build_style(spec, "#000", set(), "hist", linestyle="dashdot")
    assert style.line_style == "-."


def test_build_style_linestyle_solid():
    spec = parse_draw_spec("hist:h")
    style = _build_style(spec, "#000", set(), "hist", linestyle="solid")
    assert style.line_style == "-"


def test_parser_linestyle_single(tmp_path):
    dummy = tmp_path / "f.root"
    dummy.touch()
    p = build_parser()
    args = p.parse_args(
        ["--input", str(dummy), "--draw", "hist:h", "--linestyle", "dashed"]
    )
    assert args.linestyle == ["dashed"]


def test_parser_linestyle_multiple(tmp_path):
    dummy = tmp_path / "f.root"
    dummy.touch()
    p = build_parser()
    args = p.parse_args(
        ["--input", str(dummy), "--draw", "hist:h",
         "--linestyle", "solid", "dashed", "dotted"]
    )
    assert args.linestyle == ["solid", "dashed", "dotted"]


def test_parser_linestyle_invalid(tmp_path):
    dummy = tmp_path / "f.root"
    dummy.touch()
    p = build_parser()
    with pytest.raises(SystemExit):
        p.parse_args(["--input", str(dummy), "--draw", "hist:h", "--linestyle", "bold"])


# ---------------------------------------------------------------------------
# Per-histogram cycling (tested via _build_style directly)
# ---------------------------------------------------------------------------

def test_build_style_no_marker_when_none():
    spec = parse_draw_spec("hist:h")
    style = _build_style(spec, "#000", set(), "markers", marker=None)
    assert style.marker == "o"   # preset default unchanged


def test_build_style_marker_and_linestyle_combined():
    spec = parse_draw_spec("hist:h")
    style = _build_style(spec, "#000", set(), "hist", marker="D", linestyle="dashed")
    assert style.marker == "D"
    assert style.line_style == "--"
