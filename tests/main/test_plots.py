"""Test suite for the plots."""

from unittest.mock import patch

from bokeh.models import AjaxDataSource, CrosshairTool, HoverTool
from bokeh.plotting import figure


def test_create_timeseries_plot():
    """Test the create_timeseries_plot function."""
    from main.plots import create_timeseries_plot

    plot_config = {
        "title": "Title",
        "unit": "Unit",
        "measurements": {
            "speed": {"label": "Speed", "traces": {"A": "red", "B": "blue"}},
            "density": {"label": "Density", "traces": {"A": "red", "B": "blue"}},
        },
    }

    plot = create_timeseries_plot(plot_config)

    assert isinstance(plot, figure)

    # Check legend items added
    legend_items = [item.label.value for item in plot.legend.items]
    expected_legend = [
        f"{craft}: {label}" for craft in ["A", "B"] for label in ["Speed", "Density"]
    ]
    assert all(legend in legend_items for legend in expected_legend)

    # Check four traces have been plotted
    assert len(plot.renderers) == 4


def test_create_plots():
    """Test the create_plots function."""
    from main.plots import create_plots
    from main.widgets import checkbox_button_group

    plots_config = [
        {
            "title": "Title 1",
            "unit": "Unit",
            "measurements": {
                "speed": {"label": "Speed", "traces": {"A": "red", "B": "blue"}},
                "density": {"label": "Density", "traces": {"A": "red", "B": "blue"}},
            },
        },
        {
            "title": "Title 2",
            "unit": "Unit",
            "measurements": {
                "temperature": {
                    "label": "Temperature",
                    "traces": {"A": "red", "B": "blue"},
                },
            },
        },
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

            plots = create_plots(plots_config, button, default_spacecraft)
            assert len(plots) == 2
            assert all(isinstance(plot, figure) for plot in plots)

            # Check tools have been added
            tools = plots[0].tools
            assert any(isinstance(tool, HoverTool) for tool in tools)
            assert any(isinstance(tool, CrosshairTool) for tool in tools)

            # Check callback added to buttons
            data_source_mock.call_count == 6
