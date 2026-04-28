"""Fixtures for use throughout the test suite."""

from pathlib import Path
from tomllib import load
from typing import Any
from unittest.mock import Mock

import pytest
from bokeh.models import Range1d

from main.config import MeasurementConfig, PlotConfig
from main.plots import create_timeseries_plot


@pytest.fixture
def plots_config() -> dict[str, Any]:  # type: ignore[explicit-any]
    """Read the plots config file."""
    path = Path(__file__).parent.parent / "main" / "config" / "plots.toml"
    with path.open("rb") as f:
        config = load(f)
    return config


@pytest.fixture
def plot_context(process_data_mock: Mock):
    """Standard plot environment for widget tests."""
    # Mock the data processing function
    process_data_mock = process_data_mock.patch(
        "main.utils.process_data_from_test_csvs"
    )
    process_data_mock.return_value = {
        "measurement": [3.0, 4.0, 5.0],
        "date": [1767867720000, 1767867780000, 1767867840000],
    }

    plot_config = PlotConfig(
        title="Title",
        unit="Unit",
        measurements={
            "speed": MeasurementConfig(label="Speed", traces={"A": "red", "B": "blue"}),
            "density": MeasurementConfig(
                label="Density", traces={"A": "red", "B": "blue"}
            ),
        },
    )

    default_spacecraft = "A"
    x_range = Range1d(start=0, end=1)

    plot = create_timeseries_plot(
        plot_config,
        spacecrafts=["A", "B"],
        x_range=x_range,
        default_spacecraft=default_spacecraft,
    )

    return {
        "plot": plot,
        "config": plot_config,
        "x_range": x_range,
        "default_spacecraft": default_spacecraft,
    }


@pytest.fixture(autouse=True, scope="session")
def django_test_environment(django_test_environment):
    """Make unmanaged models, managed during tests."""
    from django.apps import apps

    get_models = apps.get_models

    for m in [m for m in get_models() if not m._meta.managed]:
        m._meta.managed = True
