"""Chunk boundaries must preserve binning, stable profile moments, and sampling."""

from decimal import Decimal, localcontext

import awkward as ak
import numpy as np
import pytest
import uproot

from unrooted.core import ScatterData
from unrooted.io.root import load_branch, load_scatter
from unrooted.io.root._sampling import _smallest_priorities


@pytest.fixture
def streams(tmp_path):
    path = tmp_path / "streams.root"
    rng = np.random.default_rng(71)
    x = np.r_[np.linspace(0, 4, 101), [-1, 5, 0, 1, 2, 3, 4]]
    y = 1e12 + rng.normal(size=len(x))
    with uproot.recreate(path) as f:
        f.mktree("scalar", {"x": x, "y": y})
        f.mktree(
            "pairs",
            {
                "x": np.arange(105, dtype=float),
                "y": 10 * np.arange(105, dtype=float) + 1,
            },
        )
        f.mktree(
            "jagged",
            {
                "x": np.arange(5, dtype=float),
                "y": ak.Array([[1.0, 2.0], [], [3.0], [4.0, 5.0, 6.0], [7.0]]),
            },
        )
        f["hist"] = (np.ones(4), np.arange(5, dtype=float))
    return path, x, y


@pytest.mark.parametrize("step_size", [1, 7, 29, 1000])
def test_chunked_counts_match_numpy_at_internal_and_final_edges(streams, step_size):
    path, x, _ = streams
    result = load_branch(
        path, "scalar", "x", n_bins=4, range=(0, 4), step_size=step_size
    )
    expected, _ = np.histogram(x, np.linspace(0, 4, 5))
    np.testing.assert_array_equal(result.values, expected)
    np.testing.assert_array_equal(result.variances, expected)


@pytest.mark.parametrize("step_size", [1, 7, 29, 1000])
def test_chunked_profiles_match_decimal_reference_at_large_offset(streams, step_size):
    path, x, y = streams
    result = load_branch(
        path, "scalar", "x", "y", n_bins=4, range=(0, 4), step_size=step_size
    )
    means, variances, minima, maxima = [], [], [], []
    with localcontext() as context:
        context.prec = 80
        for i in range(4):
            mask = (x >= i) & ((x < i + 1) if i < 3 else (x <= 4))
            values = [Decimal.from_float(float(value)) for value in y[mask]]
            mean = sum(values) / len(values)
            means.append(float(mean))
            variances.append(
                float(sum((v - mean) ** 2 for v in values) / len(values) ** 2)
            )
            minima.append(float(min(values)))
            maxima.append(float(max(values)))
    np.testing.assert_allclose(result.values, means, rtol=0, atol=np.spacing(1e12))
    np.testing.assert_allclose(result.variances, variances, rtol=1e-12)
    np.testing.assert_array_equal(result.spread_min, minima)
    np.testing.assert_array_equal(result.spread_max, maxima)


@pytest.mark.parametrize("step_size", [1, 3, 1000])
def test_chunked_automatic_range_and_jagged_broadcasting(streams, step_size):
    path, _, _ = streams
    profile = load_branch(path, "jagged", "x", "y", n_bins=4, step_size=step_size)
    np.testing.assert_array_equal(profile.axes[0].edges, np.arange(5))
    np.testing.assert_array_equal(profile.values, [1.5, 0, 3, 5.5])
    np.testing.assert_allclose(profile.variances, [0.125, 0, 0, 0.3125])
    np.testing.assert_allclose(profile.spread_min, [1, np.nan, 3, 4])
    np.testing.assert_allclose(profile.spread_max, [2, np.nan, 3, 7])


@pytest.mark.parametrize("step_size", [1, 11, 1000])
def test_random_sampling_matches_uniform_priority_reference_and_keeps_pair_order(
    streams, step_size
):
    path, _, _ = streams
    result = load_scatter(
        path,
        "pairs",
        "x",
        "y",
        max_points=13,
        sampling="random",
        seed=71,
        step_size=step_size,
    )
    selected = np.sort(np.argsort(np.random.default_rng(71).random(105))[:13])
    np.testing.assert_array_equal(result.x, selected)
    np.testing.assert_array_equal(result.y, 10 * selected + 1)
    assert result.source_points == 105 and result.sample_seed == 71 and result.sampled


def test_sampling_selected_jagged_pairs_not_events(streams):
    path, _, _ = streams
    full = load_scatter(path, "jagged", "x", "y", entry_start=1, entry_stop=4)
    sampled = load_scatter(
        path,
        "jagged",
        "x",
        "y",
        entry_start=1,
        entry_stop=4,
        max_points=2,
        sampling="random",
        seed=3,
        step_size=1,
    )
    indices = np.sort(np.argsort(np.random.default_rng(3).random(4))[:2])
    np.testing.assert_array_equal(sampled.x, full.x[indices])
    np.testing.assert_array_equal(sampled.y, full.y[indices])
    assert sampled.source_points == 4


def test_seed_controls_repeatable_sampling_and_differs_between_seeds(streams):
    path, _, _ = streams

    def sample(seed):
        return load_scatter(
            path, "pairs", "x", "y", max_points=10, sampling="random", seed=seed
        )

    np.testing.assert_array_equal(sample(0).x, sample(0).x)
    assert not np.array_equal(sample(0).x, sample(1).x)


@pytest.mark.parametrize("sampling", ["error", "random"])
def test_limit_above_input_returns_all_points_without_claiming_sampling(
    streams, sampling
):
    path, _, _ = streams
    result = load_scatter(
        path, "pairs", "x", "y", max_points=105, sampling=sampling, step_size=7
    )
    np.testing.assert_array_equal(result.x, np.arange(105))
    assert result.source_points == 105 and not result.sampled


def test_scatter_limit_fails_explicitly_and_stops_reading_early(streams, monkeypatch):
    path, _, _ = streams
    original = uproot.behaviors.TBranch.HasBranches.iterate
    steps = []

    def track(*args, **kwargs):
        for arrays in original(*args, **kwargs):
            steps.append(len(arrays["x"]))
            yield arrays

    monkeypatch.setattr(uproot.behaviors.TBranch.HasBranches, "iterate", track)
    with pytest.raises(ValueError, match="max_points=10.*sampling='random'"):
        load_scatter(path, "pairs", "x", "y", max_points=10, step_size=4)
    assert steps == [4, 4, 4]


def test_priority_ties_choose_earlier_input_indices():
    keys = np.array([0.1, 0.2, 0.2, 0.2, 0.3])
    indices = np.array([9, 7, 1, 3, 0])
    selected = _smallest_priorities(keys, indices, 3)
    np.testing.assert_array_equal(np.sort(indices[selected]), [1, 3, 9])


def test_sampling_cannot_hide_invalid_coordinates(tmp_path):
    path = tmp_path / "infinity.root"
    with uproot.recreate(path) as f:
        f.mktree("tree", {"x": np.array([0.0, np.inf]), "y": np.array([1.0, 2.0])})
    with pytest.raises(ValueError, match="finite"):
        load_scatter(path, "tree", "x", "y", max_points=1, sampling="random", seed=7)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"step_size": 0},
        {"step_size": True},
        {"max_points": 0},
        {"max_points": 1.5},
        {"sampling": "random"},
        {"sampling": "unknown"},
        {"sampling": "random", "max_points": 1, "seed": -1},
        {"seed": 5},
    ],
)
def test_invalid_scatter_resource_options_fail_before_opening_file(kwargs):
    with pytest.raises(ValueError):
        load_scatter("not-opened.root", "tree", "x", "y", **kwargs)


@pytest.mark.parametrize("kwargs", [{"step_size": 0}, {"n_bins": 0}, {"n_bins": 0.5}])
def test_invalid_histogram_sizes_fail_before_opening_file(kwargs):
    with pytest.raises(ValueError):
        load_branch("not-opened.root", "tree", "x", **kwargs)


def test_missing_branches_and_non_trees_fail_even_for_empty_selection(streams):
    path, _, _ = streams
    with pytest.raises(KeyError):
        load_scatter(path, "pairs", "missing", "y", entry_stop=0)
    with pytest.raises(ValueError, match="must be a tree"):
        load_branch(path, "hist", "x", entry_stop=0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"source_points": 0},
        {"source_points": -1},
        {"sample_seed": 1},
        {"source_points": 1, "sample_seed": -1},
    ],
)
def test_scatter_sampling_metadata_is_validated(kwargs):
    with pytest.raises(ValueError, match="ScatterData"):
        ScatterData([0], [1], **kwargs)


@pytest.mark.parametrize(
    "x_branch,y_branch", [("x", "yj"), ("x", "ykl"), ("xj", "yj"), ("xkl", "ykl")]
)
def test_nested_branch_pair_shapes_survive_event_chunk_boundaries(x_branch, y_branch):
    from pathlib import Path

    path = Path(__file__).parent.parent / "data" / "root" / "tests_trees_jagged.root"
    full = load_branch(path, "jagged_tree", x_branch, y_branch)
    chunks = load_branch(path, "jagged_tree", x_branch, y_branch, step_size=1)
    np.testing.assert_array_equal(chunks.axes[0].edges, full.axes[0].edges)
    for name in ["values", "variances", "spread_min", "spread_max"]:
        np.testing.assert_allclose(
            getattr(chunks, name), getattr(full, name), rtol=1e-12
        )
    all_points = load_scatter(path, "jagged_tree", x_branch, y_branch)
    chunked_points = load_scatter(path, "jagged_tree", x_branch, y_branch, step_size=1)
    np.testing.assert_array_equal(chunked_points.x, all_points.x)
    np.testing.assert_array_equal(chunked_points.y, all_points.y)


def test_chunked_profile_retains_missing_data_semantics(tmp_path):
    path = tmp_path / "missing.root"
    with uproot.recreate(path) as f:
        f.mktree("tree", {"x": np.array([0.1, 0.2]), "y": np.array([1.0, np.nan])})
    profile = load_branch(path, "tree", "x", "y", n_bins=2, range=(0, 2), step_size=1)
    np.testing.assert_allclose(profile.values, [np.nan, 0])
    np.testing.assert_allclose(profile.variances, [np.nan, 0])
    assert np.isnan(profile.spread_min).all() and np.isnan(profile.spread_max).all()
