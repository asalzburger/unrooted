"""Shared checks for the public NumPy-backed data containers."""

from typing import Any

import numpy as np


def real_array(
    value: Any,
    name: str,
    *,
    allow_nan: bool = True,
    dtype: Any = None,
) -> np.ndarray:
    """Normalize an array without a defensive copy and check its numeric domain."""
    array = np.asarray(value)
    if array.dtype.kind not in "iuf":
        raise ValueError(f"{name} must contain real numeric values")
    if dtype is not None:
        with np.errstate(over="ignore", invalid="ignore"):
            array = array.astype(dtype, copy=False)
    if np.any(np.isinf(array)) or (not allow_nan and np.any(np.isnan(array))):
        domain = "finite values" if not allow_nan else "finite values or NaN"
        raise ValueError(f"{name} must contain only {domain}")
    return array
