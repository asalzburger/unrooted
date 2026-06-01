import pytest

from unrooted.cli._draw_spec import DrawSpec, parse_draw_spec


def test_hist_simple():
    s = parse_draw_spec("hist:hx")
    assert s.draw_type == "hist"
    assert s.keys == ["hx"]
    assert s.auto_style == "hist"


def test_hist_alias_th1():
    s = parse_draw_spec("th1:hx")
    assert s.draw_type == "hist"


def test_hist_alias_h1():
    s = parse_draw_spec("h1:hx")
    assert s.draw_type == "hist"


def test_th2():
    s = parse_draw_spec("th2:hxy")
    assert s.draw_type == "th2"
    assert s.keys == ["hxy"]
    assert s.auto_style == "hist"


def test_prof_simple():
    s = parse_draw_spec("prof:profX")
    assert s.draw_type == "prof"
    assert s.keys == ["profX"]
    assert s.auto_style == "profile"


def test_prof_colon_path():
    # colons inside the key are treated as path separators
    s = parse_draw_spec("prof:somedata:someref")
    assert s.draw_type == "prof"
    assert s.keys == ["somedata/someref"]


def test_prof_slash_path():
    s = parse_draw_spec("prof:somedata/someref")
    assert s.draw_type == "prof"
    assert s.keys == ["somedata/someref"]


def test_prof_alias_profile():
    s = parse_draw_spec("profile:profX")
    assert s.draw_type == "prof"


def test_eff_two_keys():
    s = parse_draw_spec("eff:h_passed:h_total")
    assert s.draw_type == "eff"
    assert s.keys == ["h_passed", "h_total"]
    assert s.auto_style == "efficiency"


def test_eff_wrong_key_count():
    with pytest.raises(ValueError, match="2 keys"):
        parse_draw_spec("eff:only_one")


def test_branch_count():
    s = parse_draw_spec("branch:myTree:x_col")
    assert s.draw_type == "branch"
    assert s.keys == ["myTree", "x_col"]
    assert s.auto_style == "hist"


def test_branch_profile():
    s = parse_draw_spec("branch:myTree:x_col:y_col")
    assert s.draw_type == "branch"
    assert s.keys == ["myTree", "x_col", "y_col"]


def test_branch_alias_tree():
    s = parse_draw_spec("tree:myTree:x_col")
    assert s.draw_type == "branch"


def test_branch_wrong_key_count():
    with pytest.raises(ValueError):
        parse_draw_spec("branch:myTree:x:y:z")


def test_unknown_type():
    with pytest.raises(ValueError, match="Unknown draw type"):
        parse_draw_spec("bogus:key")


def test_missing_colon():
    with pytest.raises(ValueError, match="Expected TYPE:KEY"):
        parse_draw_spec("hist")


def test_deep_path_joined():
    s = parse_draw_spec("hist:dir:subdir:hist_name")
    assert s.keys == ["dir/subdir/hist_name"]
