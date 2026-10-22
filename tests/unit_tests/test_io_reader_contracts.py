"""Supported reader types, independent snapshots, and canonical flow arrays."""

from pathlib import Path

import boost_histogram as bh
import numpy as np
import pytest

from unrooted.io.boost.reader import load
from unrooted.io.root.reader import load as root_load


@pytest.mark.parametrize(
    "storage",
    [bh.storage.Double, bh.storage.Int64, bh.storage.Unlimited, bh.storage.AtomicInt64],
)
def test_scalar_storages_use_poisson_variances(storage):
    source = bh.Histogram(bh.axis.Regular(2, 0, 2), storage=storage())
    source.fill([0.5, 0.5, 1.5])
    result = load(source)
    np.testing.assert_array_equal(result.values, [2, 1])
    np.testing.assert_array_equal(result.variances, [2, 1])


@pytest.mark.parametrize(
    "axis",
    [bh.axis.IntCategory([1, 2]), bh.axis.StrCategory(["a", "b"]), bh.axis.Boolean()],
)
def test_categorical_and_boolean_axes_are_rejected(axis):
    with pytest.raises(ValueError, match="Unsupported boost axis"):
        load(bh.Histogram(axis))


def test_weighted_mean_storage_is_explicitly_unsupported():
    source = bh.Histogram(bh.axis.Regular(2, 0, 2), storage=bh.storage.WeightedMean())
    with pytest.raises(ValueError, match="WeightedMean is unsupported"):
        load(source)


@pytest.mark.parametrize(
    "axis",
    [
        bh.axis.Regular(2, 0, 2),
        bh.axis.Variable([0, 1, 2]),
        bh.axis.Integer(0, 2),
        bh.axis.Regular(2, 1, 100, transform=bh.axis.transform.log),
        bh.axis.Regular(2, 0, 2, growth=True),
        bh.axis.Regular(2, 0, 2, circular=True),
    ],
)
def test_numeric_axis_edges_are_snapshots(axis):
    source = bh.Histogram(axis)
    source.fill([1])
    result = load(source)
    np.testing.assert_array_equal(result.axes[0].edges, source.axes[0].edges)
    assert not np.shares_memory(result.axes[0].edges, source.axes[0].edges)


@pytest.mark.parametrize("underflow", [False, True])
@pytest.mark.parametrize("overflow", [False, True])
@pytest.mark.parametrize(
    "storage", [bh.storage.Double, bh.storage.Weight, bh.storage.Mean]
)
def test_missing_flow_slots_are_nan_not_zero(underflow, overflow, storage):
    source = bh.Histogram(
        bh.axis.Regular(2, 0, 2, underflow=underflow, overflow=overflow),
        storage=storage(),
    )
    kwargs = {"sample": [10, 20, 30, 40]} if storage == bh.storage.Mean else {}
    source.fill([-1, 0.5, 1.5, 3], **kwargs)
    result = load(source)
    assert result.overflow.shape == (4,)
    np.testing.assert_array_equal(result.overflow[1:-1], result.values)
    if underflow:
        assert result.overflow[0] == (10 if storage == bh.storage.Mean else 1)
    else:
        assert np.isnan(result.overflow[0])
    if overflow:
        assert result.overflow[-1] == (40 if storage == bh.storage.Mean else 1)
    else:
        assert np.isnan(result.overflow[-1])


def test_two_dimensional_mixed_flow_padding():
    source = bh.Histogram(
        bh.axis.Regular(2, 0, 2, underflow=False),
        bh.axis.Integer(0, 3, overflow=False),
    )
    source.fill([0.5, 3], [1, -1])
    result = load(source)
    assert result.overflow.shape == (4, 5)
    assert np.isnan(result.overflow[0, :]).all()
    assert np.isnan(result.overflow[:, -1]).all()
    np.testing.assert_array_equal(result.overflow[1:-1, 1:-1], result.values)
    assert result.overflow[-1, 0] == 1


@pytest.mark.parametrize(
    "storage", [bh.storage.Double, bh.storage.Weight, bh.storage.Mean]
)
def test_reader_arrays_do_not_alias_source_or_each_other(storage):
    source = bh.Histogram(bh.axis.Regular(2, 0, 2), storage=storage())
    kwargs = {"sample": [2, 4]} if storage == bh.storage.Mean else {}
    source.fill([0.5, 0.5], **kwargs)
    result = load(source)
    saved_values = result.values.copy()
    saved_variances = result.variances.copy()
    saved_flows = result.overflow.copy()
    source.reset()
    np.testing.assert_array_equal(result.values, saved_values)
    np.testing.assert_array_equal(result.variances, saved_variances)
    np.testing.assert_array_equal(result.overflow, saved_flows)
    result.values[0] = 999
    np.testing.assert_array_equal(result.variances, saved_variances)
    np.testing.assert_array_equal(result.overflow, saved_flows)


@pytest.mark.parametrize("key", ["tree", "eff_x"])
def test_root_rejects_unsupported_objects_with_actionable_error(key):
    path = Path(__file__).parent.parent / "data" / "root" / "tests_input.root"
    with pytest.raises(ValueError, match="Unsupported ROOT object.*load_efficiency"):
        root_load(path, key)


def test_zero_dimensional_boost_histogram_has_clear_error():
    with pytest.raises(ValueError, match="at least one numeric axis"):
        load(bh.Histogram())


def test_weight_storage_preserves_negative_contents_and_sumw2():
    source = bh.Histogram(bh.axis.Regular(1, 0, 1), storage=bh.storage.Weight())
    source.fill([0.5, 0.5], weight=[1, -3])
    result = load(source)
    np.testing.assert_array_equal(result.values, [-2])
    np.testing.assert_array_equal(result.variances, [10])
