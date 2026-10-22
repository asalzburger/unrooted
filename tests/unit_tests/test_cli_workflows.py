"""CLI workflows with real ROOT input and saved figures, plus exit-code contracts."""

import json
import os
import subprocess
import sys

import matplotlib.pyplot as plt
import numpy as np
import pytest
import uproot

from unrooted.cli.main import main


@pytest.fixture
def inputs(tmp_path):
    paths = [tmp_path / "sample_a.root", tmp_path / "sample_b.root"]
    edges = np.array([0.0, 1.0, 2.0])
    for i, path in enumerate(paths):
        with uproot.recreate(path) as f:
            for prefix in ["", "data/"]:
                f[prefix + "h"] = (np.array([4.0, 8.0]) * (i + 1), edges)
                f[prefix + "other"] = (np.array([2.0, 4.0]), edges)
                f[prefix + "heat"] = (np.ones((2, 2)), edges, edges)
                f[prefix + "passed"] = (np.array([1.0, 2.0]), edges)
                f[prefix + "total"] = (np.array([4.0, 4.0]), edges)
                x_key, y_key = ("u", "v") if prefix else ("x", "y")
                tree = f.mktree(prefix + "tree", {x_key: "float64", y_key: "float64"})
                tree.extend(
                    {x_key: np.array([0.25, 1.25]), y_key: np.array([2.0, 4.0])}
                )
            f["data/only"] = (np.array([4.0, 8.0]), edges)
            f["data/passed_only"] = (np.array([1.0, 2.0]), edges)
            f["data/total_only"] = (np.array([4.0, 4.0]), edges)
            f["unsupported"] = "not a histogram"
    return paths


def read_html_figure(path):
    # Read the actual saved figure specification, independent of Plotly's
    # array serialization (plain lists in older versions, typed data in newer).
    remaining = path.read_text().rsplit("Plotly.newPlot(", 1)[1].lstrip()
    decoder = json.JSONDecoder()
    _, end = decoder.raw_decode(remaining)  # generated div id
    remaining = remaining[end:].lstrip().removeprefix(",").lstrip()
    data, end = decoder.raw_decode(remaining)
    remaining = remaining[end:].lstrip().removeprefix(",").lstrip()
    layout, _ = decoder.raw_decode(remaining)
    return data, layout


def plotly_output(tmp_path):
    pytest.importorskip("plotly")
    return tmp_path / "plot.HTML"


@pytest.mark.parametrize("backend", ["mpl", "plotly"])
def test_saved_single_histogram_honors_labels_and_axis_overrides(
    inputs, tmp_path, backend
):
    output = tmp_path / "plot.svg" if backend == "mpl" else plotly_output(tmp_path)
    main(
        [
            "--input",
            str(inputs[0]),
            "--draw",
            "hist:h",
            "--backend",
            backend,
            "--label",
            "Dataset A",
            "--xlabel",
            "Position",
            "--ylabel",
            "Events",
            "--title",
            "Selected data",
            "--output",
            str(output),
        ]
    )
    assert output.stat().st_size > 100
    if backend == "mpl":
        content = output.read_text()
        for text in ["Dataset A", "Position", "Events", "Selected data"]:
            assert text in content
    else:
        data, layout = read_html_figure(output)
        assert [t["name"] for t in data if t.get("showlegend")] == ["Dataset A"]
        assert layout["xaxis"]["title"]["text"] == "Position"
        assert layout["yaxis"]["title"]["text"] == "Events"
        assert layout["title"]["text"] == "Selected data"


def test_plotly_ratio_keeps_main_and_ratio_axis_settings_separate(inputs, tmp_path):
    output = plotly_output(tmp_path)
    main(
        [
            "--input",
            str(inputs[0]),
            "--draw",
            "hist:h",
            "hist:other",
            "--backend",
            "plotly",
            "--add",
            "ratio:error_none",
            "--xlabel",
            "Position",
            "--ylabel",
            "Events",
            "--xlim",
            "0",
            "2",
            "--ylim",
            "0",
            "20",
            "--ratio-range",
            ".2",
            "2",
            "--linestyle",
            "dashed",
            "--output",
            str(output),
        ]
    )
    data, layout = read_html_figure(output)
    assert layout["xaxis2"]["title"]["text"] == "Position"
    assert not layout["xaxis"].get("title")
    assert layout["yaxis"]["title"]["text"] == "Events"
    assert layout["yaxis2"]["title"]["text"] == "Ratio"
    assert layout["yaxis"]["range"] == [0, 20]
    assert layout["yaxis2"]["range"] == [0.2, 2]
    for trace in data:
        assert "error_y" not in trace
    ratio_lines = [t for t in data if t.get("yaxis") == "y2"]
    assert ratio_lines[0]["line"]["dash"] == "dash"


@pytest.mark.parametrize(
    "specs, expected",
    [
        (["hist:h"], ["sample_a", "sample_b"]),
        (["hist:h", "hist:other"], ["h", "other"]),
    ],
)
def test_multi_file_default_labels_follow_combination_rules(
    inputs, tmp_path, specs, expected
):
    output = plotly_output(tmp_path)
    main(
        [
            "--input",
            *map(str, inputs),
            "--draw",
            *specs,
            "--backend",
            "plotly",
            "--output",
            str(output),
        ]
    )
    data, _ = read_html_figure(output)
    assert [t["name"] for t in data if t.get("showlegend")] == expected


def test_efficiency_default_label_uses_passed_key(inputs, tmp_path):
    output = plotly_output(tmp_path)
    main(
        [
            "--input",
            str(inputs[0]),
            "--draw",
            "eff:passed:total",
            "--backend",
            "plotly",
            "--output",
            str(output),
        ]
    )
    data, _ = read_html_figure(output)
    assert [t["name"] for t in data if t.get("showlegend")] == ["passed"]


@pytest.mark.parametrize(
    "spec",
    [
        "hist:only",
        "eff:passed_only:total_only",
        "branch:tree:x",
        "branch:data/tree:scatter:u:v",
    ],
)
def test_source_prefix_and_explicit_tree_paths(inputs, tmp_path, spec):
    output = plotly_output(tmp_path)
    main(
        [
            "--input",
            str(inputs[0]),
            "--source",
            "/data/",
            "--draw",
            spec,
            "--backend",
            "plotly",
            "--output",
            str(output),
        ]
    )
    assert output.stat().st_size > 100


@pytest.mark.parametrize("backend", ["mpl", "plotly"])
def test_scatter_overlay_saves_using_public_composition(inputs, tmp_path, backend):
    output = tmp_path / "scatter.svg" if backend == "mpl" else plotly_output(tmp_path)
    main(
        [
            "--input",
            *map(str, inputs),
            "--draw",
            "branch:tree:scatter:x:y",
            "--backend",
            backend,
            "--marker",
            "s",
            "--xlabel",
            "Position",
            "--ylabel",
            "Momentum",
            "--output",
            str(output),
        ]
    )
    assert output.stat().st_size > 100
    if backend == "plotly":
        data, layout = read_html_figure(output)
        assert [t["name"] for t in data] == ["sample_a", "sample_b"]
        assert all(t["marker"]["symbol"] == "square" for t in data)
        assert layout["yaxis"]["title"]["text"] == "Momentum"


def test_terminal_applies_title_label_and_ratio(inputs, capsys):
    main(
        [
            "--input",
            str(inputs[0]),
            "--draw",
            "hist:h",
            "hist:other",
            "--backend",
            "terminal",
            "--title",
            "Selected data",
            "--xlabel",
            "Position",
            "--label",
            "Reference",
            "Alternative",
            "--max-lines",
            "10",
            "--add",
            "ratio",
        ]
    )
    output = capsys.readouterr().out
    for text in ["Selected data", "Position", "Reference", "Alternative"]:
        assert text in output


@pytest.mark.parametrize(
    "flags, message",
    [
        (["--add", "error_bar:error_band"], "Conflicting"),
        (["--add", "spread_none:spread_band"], "Conflicting"),
        (["--ratio-range", "0", "2"], "requires --add ratio"),
        (["--add", "ratio"], "at least two"),
        (["--xlim", "nan", "2"], "finite MIN < MAX"),
        (["--ylim", "2", "1"], "finite MIN < MAX"),
        (["--n-bins", "0"], "positive"),
        (["--n-bins", "2"], "require a count/profile branch"),
        (["--max-lines", "5"], "requires --backend terminal"),
        (["--backend", "terminal", "--max-lines", "2"], "at least 5"),
        (
            ["--backend", "terminal", "--output", "plot.png"],
            "does not support --output",
        ),
        (["--backend", "terminal", "--show"], "does not support --show"),
        (["--backend", "terminal", "--ylabel", "Events"], "does not support --ylabel"),
        (["--backend", "terminal", "--palette", "sd"], "does not support --palette"),
        (["--backend", "terminal", "--add", "error_band"], "error/spread display"),
        (["--backend", "terminal", "--linestyle", "dashed"], "--linestyle"),
        (["--backend", "plotly", "--output", "plot.unsupported"], "Plotly output"),
        (["--label", "one", "two"], "expected 1"),
    ],
)
def test_invalid_options_exit_two_without_tracebacks(inputs, capsys, flags, message):
    with pytest.raises(SystemExit) as error:
        main(["--input", str(inputs[0]), "--draw", "hist:h", *flags])
    assert error.value.code == 2
    stderr = capsys.readouterr().err
    assert "unrooted: error:" in stderr
    assert message in stderr
    assert "Traceback" not in stderr


@pytest.mark.parametrize(
    "flags",
    [
        ["--add", "ratio"],
        ["--add", "error_bar"],
        ["--style", "hist"],
        ["--linestyle", "dashed"],
        ["--backend", "terminal"],
        ["--n-bins", "2"],
    ],
)
def test_unsupported_scatter_options_exit_two(inputs, capsys, flags):
    with pytest.raises(SystemExit) as error:
        main(["--input", str(inputs[0]), "--draw", "branch:tree:scatter:x:y", *flags])
    assert error.value.code == 2
    assert "error:" in capsys.readouterr().err


@pytest.mark.parametrize(
    "flags",
    [
        ["--add", "error_none"],
        ["--style", "hist"],
        ["--label", "heatmap"],
        ["--backend", "terminal"],
    ],
)
def test_unsupported_heatmap_options_exit_two(inputs, flags):
    with pytest.raises(SystemExit) as error:
        main(["--input", str(inputs[0]), "--draw", "th2:heat", *flags])
    assert error.value.code == 2


@pytest.mark.parametrize("spec", ["hist:", "eff::total", "branch:tree:scatter:x:"])
def test_empty_draw_fields_exit_two(inputs, spec):
    with pytest.raises(SystemExit) as error:
        main(["--input", str(inputs[0]), "--draw", spec])
    assert error.value.code == 2


@pytest.mark.parametrize("spec", ["hist:missing", "hist:unsupported"])
def test_loading_errors_exit_one_with_consistent_prefix(inputs, capsys, spec):
    with pytest.raises(SystemExit) as error:
        main(["--input", str(inputs[0]), "--draw", spec])
    assert str(error.value.code).startswith("unrooted: error loading data:")
    assert "Traceback" not in str(error.value.code) + capsys.readouterr().err


def test_export_failure_is_contextual_and_closes_matplotlib_figure(inputs, tmp_path):
    with pytest.raises(SystemExit) as error:
        main(
            [
                "--input",
                str(inputs[0]),
                "--draw",
                "hist:h",
                "--output",
                str(tmp_path / "absent" / "plot.png"),
            ]
        )
    assert "unrooted: error: Cannot save figure" in str(error.value.code)
    assert plt.get_fignums() == []


def test_plotly_static_export_failure_explains_optional_requirements(
    inputs, tmp_path, monkeypatch
):
    go = pytest.importorskip("plotly.graph_objects")

    def unavailable(*args, **kwargs):
        raise ValueError("Kaleido unavailable")

    monkeypatch.setattr(go.Figure, "write_image", unavailable)
    with pytest.raises(SystemExit) as error:
        main(
            [
                "--input",
                str(inputs[0]),
                "--draw",
                "hist:h",
                "--backend",
                "plotly",
                "--output",
                str(tmp_path / "plot.png"),
            ]
        )
    message = str(error.value.code)
    assert message.startswith("unrooted: error: Cannot export Plotly")
    assert "Kaleido" in message and "Chrome" in message and ".html" in message


@pytest.mark.parametrize(
    "kind, expected_code",
    [("missing", 1), ("invalid", 2), ("mpl", 0), ("plotly", 0), ("terminal", 0)],
)
def test_cli_process_exit_codes_and_saved_output(inputs, tmp_path, kind, expected_code):
    if kind == "plotly":
        pytest.importorskip("plotly")
    args = ["--input", str(inputs[0]), "--draw", "hist:h"]
    output = None
    if kind == "missing":
        args[1] = str(tmp_path / "absent.root")
    elif kind == "invalid":
        args += ["--ratio-range", "0", "2"]
    elif kind == "terminal":
        args += ["--backend", "terminal"]
    else:
        output = tmp_path / ("process.html" if kind == "plotly" else "process.png")
        args += ["--backend", kind, "--output", str(output)]
    env = dict(os.environ, MPLBACKEND="Agg", MPLCONFIGDIR=str(tmp_path / "mpl"))
    result = subprocess.run(
        [sys.executable, "-I", "-m", "unrooted.cli.main", *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == expected_code, result.stderr
    assert "Traceback" not in result.stderr
    if output is not None:
        assert output.stat().st_size > 100
    if kind == "terminal":
        assert result.stdout.strip()


@pytest.mark.parametrize("spec", ["th2:h", "prof:h"])
def test_draw_type_mismatch_is_a_loading_error(inputs, spec):
    with pytest.raises(SystemExit) as error:
        main(["--input", str(inputs[0]), "--draw", spec])
    assert "error loading data" in str(error.value.code)
    assert "requires a" in str(error.value.code)


def test_mixed_scatter_and_histogram_specs_are_rejected(inputs):
    with pytest.raises(SystemExit) as error:
        main(["--input", str(inputs[0]), "--draw", "hist:h", "branch:tree:scatter:x:y"])
    assert error.value.code == 2


def test_incompatible_file_spec_counts_are_argument_errors(inputs):
    with pytest.raises(SystemExit) as error:
        main(["--input", *map(str, inputs), "--draw", "hist:h", "hist:h", "hist:other"])
    assert error.value.code == 2


@pytest.mark.parametrize("backend", ["mpl", "plotly"])
def test_saved_heatmap_honors_axis_and_title_overrides(inputs, tmp_path, backend):
    output = tmp_path / "heat.svg" if backend == "mpl" else plotly_output(tmp_path)
    main(
        [
            "--input",
            str(inputs[0]),
            "--draw",
            "th2:heat",
            "--backend",
            backend,
            "--xlabel",
            "Position",
            "--ylabel",
            "Momentum",
            "--title",
            "Density",
            "--output",
            str(output),
        ]
    )
    assert output.stat().st_size > 100
    if backend == "mpl":
        content = output.read_text()
        assert all(label in content for label in ["Position", "Momentum", "Density"])
    else:
        data, layout = read_html_figure(output)
        assert data[0]["type"] == "heatmap"
        assert layout["xaxis"]["title"]["text"] == "Position"
        assert layout["yaxis"]["title"]["text"] == "Momentum"
        assert layout["title"]["text"] == "Density"


@pytest.mark.parametrize(
    "spec", ["branch:tree:x", "branch:tree:prof:x:y", "branch:tree:scatter:x:y"]
)
def test_cli_entry_selection_is_forwarded_to_branch_readers(inputs, tmp_path, spec):
    output = plotly_output(tmp_path)
    main(
        [
            "--input",
            str(inputs[0]),
            "--draw",
            spec,
            "--backend",
            "plotly",
            "--entry-start",
            "1",
            "--entry-stop",
            "2",
            "--output",
            str(output),
        ]
    )
    data, layout = read_html_figure(output)
    assert output.stat().st_size > 100
    if ":scatter:" in spec:
        # One selected event, one point, rather than both source entries.
        x = data[0]["x"]
        if isinstance(x, list):
            assert len(x) == 1
        else:
            import base64

            assert (
                np.frombuffer(base64.b64decode(x["bdata"]), dtype=x["dtype"]).size == 1
            )


@pytest.mark.parametrize(
    "flags",
    [
        ["--entry-start", "-1"],
        ["--entry-start", "2", "--entry-stop", "1"],
        ["--entry-stop", "1"],
    ],
)
def test_cli_invalid_entry_options_are_argument_errors(inputs, flags):
    with pytest.raises(SystemExit) as error:
        main(["--input", str(inputs[0]), "--draw", "hist:h", *flags])
    assert error.value.code == 2


def test_cli_explicit_random_sampling_is_reported_and_saved(inputs, tmp_path, capsys):
    output = plotly_output(tmp_path)
    main(
        [
            "--input",
            str(inputs[0]),
            "--draw",
            "branch:tree:scatter:x:y",
            "--backend",
            "plotly",
            "--max-points",
            "1",
            "--sampling",
            "random",
            "--seed",
            "71",
            "--step-size",
            "1",
            "--output",
            str(output),
        ]
    )
    assert "sampled 1 of 2 points uniformly (seed=71)" in capsys.readouterr().err
    assert output.stat().st_size > 100


def test_cli_scatter_limit_does_not_silently_truncate(inputs):
    with pytest.raises(SystemExit) as error:
        main(
            [
                "--input",
                str(inputs[0]),
                "--draw",
                "branch:tree:scatter:x:y",
                "--max-points",
                "1",
            ]
        )
    assert str(error.value.code).startswith("unrooted: error loading data:")
    assert "max_points=1" in str(error.value.code)


@pytest.mark.parametrize(
    "flags",
    [
        ["--step-size", "0"],
        ["--step-size", "1"],
        ["--max-points", "0"],
        ["--max-points", "1"],
        ["--sampling", "random"],
        ["--seed", "0"],
    ],
)
def test_cli_resource_options_require_valid_sizes_and_branch_types(inputs, flags):
    with pytest.raises(SystemExit) as error:
        main(["--input", str(inputs[0]), "--draw", "hist:h", *flags])
    assert error.value.code == 2


def test_cli_scatter_random_mode_requires_an_explicit_limit(inputs):
    with pytest.raises(SystemExit) as error:
        main(
            [
                "--input",
                str(inputs[0]),
                "--draw",
                "branch:tree:scatter:x:y",
                "--sampling",
                "random",
            ]
        )
    assert error.value.code == 2
