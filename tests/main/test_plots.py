"""Test suite for the plots."""

from unittest.mock import patch

from bokeh.models import AjaxDataSource, CrosshairTool, HoverTool
from bokeh.plotting import figure

from main.config import MeasurementConfig, PlotConfig


def test_create_timeseries_plot():
    """Test the create_timeseries_plot function."""
    from main.plots import create_timeseries_plot

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

    x_range = figure(x_axis_type="datetime").x_range

    plot = create_timeseries_plot(plot_config, x_range, time_range="7d")

    assert isinstance(plot, figure)

    # Check legend items added
    legend_items = [item.label.value for item in plot.legend.items]
    expected_legend = [
        f"{craft}: {label}" for craft in ["A", "B"] for label in ["Speed", "Density"]
    ]
    assert all(legend in legend_items for legend in expected_legend)

    # Check four traces have been plotted
    assert len(plot.renderers) == 4

    # Check that the URL includes the time range parameter
    first_source = plot.renderers[0].data_source
    assert isinstance(first_source, AjaxDataSource)
    assert "range=7d" in first_source.data_url


def test_create_timeseries_plots():
    """Test the create_timeseries_plots function."""
    from main.plots import create_timeseries_plots
    from main.widgets import checkbox_button_group

    plots_config = [
        PlotConfig(
            title="Title 1",
            unit="Unit",
            measurements={
                "speed": MeasurementConfig(
                    label="Speed", traces={"A": "red", "B": "blue"}
                ),
                "density": MeasurementConfig(
                    label="Density", traces={"A": "red", "B": "blue"}
                ),
            },
        ),
        PlotConfig(
            title="Title 2",
            unit="Unit",
            measurements={
                "temperature": MeasurementConfig(
                    label="Temperature",
                    traces={"A": "red", "B": "blue"},
                ),
            },
        ),
    ]
    spacecrafts = ["A", "B"]
    default_spacecraft = "A"

    button = checkbox_button_group(spacecrafts, default_spacecraft)
    source = AjaxDataSource(
        data={
            "measurement": [3.0, 4.0, 5.0],
            "date": [1767867720000, 1767867780000, 1767867840000],
        },
        polling_interval=1000,
        method="GET",
    )

    with patch("main.views.DataView.get"):
        with patch("main.plots.AjaxDataSource") as data_source_mock:
            data_source_mock.return_value = source

            plots = create_timeseries_plots(plots_config, button, default_spacecraft)
            assert len(plots) == 2
            assert all(isinstance(plot, figure) for plot in plots)

            # Check tools have been added
            tools = plots[0].tools
            assert any(isinstance(tool, HoverTool) for tool in tools)
            assert any(isinstance(tool, CrosshairTool) for tool in tools)

            # Check callback added to buttons
            data_source_mock.call_count == 6


def test_create_solar_orbiter_plot():
    """Test the create_solar_orbiter_plot function."""
    from main.plots import create_solar_orbiter_plot

    create_solar_orbiter_plot(
        title="Fixed Earth frame",
        x_axis_label="AU",
        y_axis_label="AU",
        unit="AU",
        radii=[0.5, 0.75, 1.0],
    )

    source = AjaxDataSource(
        data={
            "name": ["Sun", "Earth", "SO"],
            "x": [1.0, 2.0, 3.0],
            "y": [3.0, 4.0, 5.0],
            "colour": ["black", "gold", "pink"],
        },
        polling_interval=None,
        method="GET",
    )

    with patch("main.views.DataView.get"):
        with patch("main.plots.AjaxDataSource") as data_source_mock:
            data_source_mock.return_value = source

            plot = create_solar_orbiter_plot(
                title="Test plot",
                x_axis_label="AU",
                y_axis_label="AU",
                unit="AU",
                radii=[0.5, 1.0],
            )
            assert isinstance(plot, figure)

            # 4 renderers for the points, traj, and 2 circles
            assert len(plot.renderers) == 4

            # Check hover has been added
            assert any(isinstance(tool, HoverTool) for tool in plot.tools)
