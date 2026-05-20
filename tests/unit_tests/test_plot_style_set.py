from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pytest

from unrooted.plot.style import HistogramStyle
from unrooted.plot.style_set import StyleSet

# ---------------------------------------------------------------------------
# StyleSet.load — odd
# ---------------------------------------------------------------------------


def test_load_odd_name():
    assert StyleSet.load("odd").name == "odd"


def test_load_odd_description_nonempty():
    assert StyleSet.load("odd").description != ""


def test_load_odd_colors_count():
    assert len(StyleSet.load("odd").colors) == 4


def test_load_odd_colors_are_hex():
    hex_re = re.compile(r"^#[0-9A-Fa-f]{6}$")
    for color in StyleSet.load("odd").colors:
        assert hex_re.match(color), f"{color!r} is not a 7-char hex color"


def test_load_odd_styles_count():
    assert len(StyleSet.load("odd")) == 4


def test_styles_are_histogram_style():
    ss = StyleSet.load("odd")
    for i in range(4):
        assert isinstance(ss[i], HistogramStyle)


def test_styles_colors_match_palette():
    ss = StyleSet.load("odd")
    for i in range(4):
        assert ss[i].line_color == ss.colors[i]
        assert ss[i].marker_color == ss.colors[i]
        assert ss[i].fill_color == ss.colors[i]


# ---------------------------------------------------------------------------
# Cyclic index access
# ---------------------------------------------------------------------------


def test_cyclic_access_wraps():
    ss = StyleSet.load("odd")
    assert ss[4] is ss[0]
    assert ss[5] is ss[1]
    assert ss[7] is ss[3]


# ---------------------------------------------------------------------------
# StyleSet.load — sd
# ---------------------------------------------------------------------------


def test_load_sd_name():
    assert StyleSet.load("sd").name == "sd"


def test_load_sd_colors_count():
    assert len(StyleSet.load("sd").colors) == 4


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_missing_target_raises():
    with pytest.raises(FileNotFoundError):
        StyleSet.load("nonexistent_target_xyz")


# ---------------------------------------------------------------------------
# generate_stylesheet smoke tests
# ---------------------------------------------------------------------------


def test_generate_stylesheet_sd(tmp_path: Path) -> None:
    from unrooted.plot.mpl.stylesheet import generate_stylesheet

    out = generate_stylesheet("sd", tmp_path / "sd_stylesheet.png")
    assert out.exists()
    assert out.stat().st_size > 0


def test_generate_stylesheet_odd(tmp_path: Path) -> None:
    from unrooted.plot.mpl.stylesheet import generate_stylesheet

    out = generate_stylesheet("odd", tmp_path / "odd_stylesheet.png")
    assert out.exists()
    assert out.stat().st_size > 0


def test_generate_stylesheet_default_path_sd() -> None:
    from unrooted.plot.mpl.stylesheet import _RESOURCES, generate_stylesheet

    out = generate_stylesheet("sd")
    assert out == _RESOURCES / "sd" / "stylesheet.png"
    assert out.exists()
