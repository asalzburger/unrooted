from __future__ import annotations

import numpy as np
import pytest

from unrooted.core.scatter import ScatterData


def test_basic_construction():
    sd = ScatterData(x=np.array([1.0, 2.0]), y=np.array([3.0, 4.0]))
    assert len(sd.x) == 2
    assert len(sd.y) == 2


def test_default_labels_empty():
    sd = ScatterData(x=np.array([1.0]), y=np.array([2.0]))
    assert sd.x_label == ""
    assert sd.y_label == ""
    assert sd.name == ""
    assert sd.title == ""


def test_custom_fields():
    sd = ScatterData(
        x=np.array([1.0]),
        y=np.array([2.0]),
        name="t_X0",
        x_label="η",
        y_label="X₀",
        title="Material scan",
    )
    assert sd.name == "t_X0"
    assert sd.x_label == "η"
    assert sd.y_label == "X₀"
    assert sd.title == "Material scan"


def test_mismatched_lengths_raise():
    with pytest.raises(ValueError, match="same length"):
        ScatterData(x=np.array([1.0, 2.0]), y=np.array([3.0]))


def test_arrays_are_preserved():
    x = np.array([0.1, 0.2, 0.3])
    y = np.array([1.1, 1.2, 1.3])
    sd = ScatterData(x=x, y=y)
    np.testing.assert_array_equal(sd.x, x)
    np.testing.assert_array_equal(sd.y, y)
