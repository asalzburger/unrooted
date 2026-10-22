"""Binning and validation rules shared by plotting backends."""

import importlib
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pytest

from unrooted.core.axis import Axis
from unrooted.core.histogram import Histogram
from unrooted.core.scatter import ScatterData


def histogram(edges):
    values = np.ones(len(edges) - 1)
    return Histogram([Axis(edges)], values, values.copy())


def backend_module(backend, module):
    if backend == "plotly":
        pytest.importorskip("plotly")
    return importlib.import_module(f"unrooted.plot.{backend}.{module}")


@pytest.fixture(autouse=True)
def close_test_figures():
    yield
    plt.close("all")


@pytest.mark.parametrize("backend", ["mpl", "plotly", "terminal"])
@pytest.mark.parametrize("edges", [[0, 1, 3], [0, 1, 2, 3], [1e12, 1e12 + 1, 1e12 + 3]])
def test_ratios_require_exactly_identical_edges(backend, edges):
    reference_edges = [1e12, 1e12 + 1, 1e12 + 2] if edges[0] else [0, 1, 2]
    module = backend_module(
        backend, "histogram" if backend == "terminal" else "overlay"
    )
    with pytest.raises(ValueError, match="Bin edges|Shape mismatch"):
        module.overlay([histogram(reference_edges), histogram(edges)], ratio=True)


@pytest.mark.parametrize("backend", ["mpl", "plotly"])
def test_graphical_overlays_allow_different_grids_without_ratios(backend):
    module = backend_module(backend, "overlay")
    module.overlay([histogram([0, 1, 2]), histogram([0, 2, 3, 4])])


def test_terminal_overlays_require_common_edges_even_without_ratios():
    module = backend_module("terminal", "histogram")
    with pytest.raises(ValueError, match="Bin edges"):
        module.overlay([histogram([0, 1, 2]), histogram([0, 1, 3])])


@pytest.mark.parametrize("backend", ["mpl", "plotly", "terminal"])
@pytest.mark.parametrize("entrypoint", ["plot", "overlay"])
def test_histogram_plotting_revalidates_mutated_data(backend, entrypoint):
    module = backend_module(
        backend,
        "overlay" if entrypoint == "overlay" and backend != "terminal" else "histogram",
    )
    hist = histogram([0, 1, 2])
    hist.variances[0] = -1
    with pytest.raises(ValueError, match="nonnegative"):
        getattr(module, entrypoint)([hist] if entrypoint == "overlay" else hist)


@pytest.mark.parametrize("backend", ["mpl", "plotly"])
def test_scatter_plotting_revalidates_mutated_data(backend):
    module = backend_module(backend, "scatter")
    scatter = ScatterData([0, 1], [1, 2])
    scatter.y = np.array([1])
    with pytest.raises(ValueError, match="same length"):
        module.plot(scatter)


@pytest.mark.parametrize("values", [[np.nan, 4], [np.nan, np.nan]])
def test_terminal_nan_gaps_do_not_poison_scale_or_emit_warnings(values):
    module = backend_module("terminal", "histogram")
    hist = Histogram([Axis([0, 1, 2])], values, [0, 0])
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        rendered = module.overlay([hist, histogram([0, 1, 2])], ratio=True)
        single = module.plot(hist)
    assert "nan" not in rendered.lower() + single.lower()


@pytest.mark.parametrize("entrypoint", ["plot", "overlay"])
def test_terminal_rejects_negative_values_instead_of_clipping(entrypoint):
    module = backend_module("terminal", "histogram")
    hist = Histogram([Axis([0, 1])], [-1], [1])
    with pytest.raises(ValueError, match="nonnegative bin values"):
        getattr(module, entrypoint)([hist] if entrypoint == "overlay" else hist)


@pytest.mark.parametrize("backend", ["mpl", "plotly"])
def test_ratio_uncertainties_use_independent_inputs_without_integer_overflow(backend):
    reference = Histogram([Axis([0, 1])], np.array([10**10]), np.array([10**10]))
    numerator = Histogram([Axis([0, 1])], np.array([5 * 10**9]), np.array([5 * 10**9]))
    module = backend_module(backend, "overlay")
    if backend == "mpl":
        _, ratio_ax = module.overlay([reference, numerator], ratio=True)
        segments = ratio_ax.collections[0].get_segments()
        lower, upper = segments[0][:, 1]
        np.testing.assert_allclose(
            [lower, upper], [0.5 - np.sqrt(7.5e-11), 0.5 + np.sqrt(7.5e-11)], rtol=1e-14
        )
    else:
        fig = module.overlay([reference, numerator], ratio=True)
        ratio_errors = [
            trace.error_y.array
            for trace in fig.data
            if trace.yaxis == "y2" and trace.error_y.array is not None
        ]
        assert len(ratio_errors) == 1
        np.testing.assert_allclose(ratio_errors[0], [np.sqrt(7.5e-11)], rtol=1e-14)
