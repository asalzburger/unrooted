"""Headless plotting with figure cleanup shared by the complete test suite."""

import matplotlib
import pytest

matplotlib.use("Agg")


@pytest.fixture(autouse=True)
def close_figures():
    import matplotlib.pyplot as plt

    with matplotlib.rc_context():
        try:
            yield
        finally:
            plt.close("all")
