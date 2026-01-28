"""Test suite for the plots."""

from unittest.mock import patch

from bokeh.models import AjaxDataSource, CrosshairTool, HoverTool
from bokeh.plotting import figure


def test_create_scatter_plot():
    """Test the create_scatter_plot function."""
    from main.plots import create_scatter_plot

    traces = (
        {"col_name": "speed", "name": "Speed"},
        {"col_name": "density", "name": "Density"},
    )
    spacecrafts = {"A": "red", "B": "blue"}

    plot = create_scatter_plot(traces, spacecrafts, time_range="7d")

    assert isinstance(plot, figure)

    # Check legend items added
    legend_items = [item.label.value for item in plot.legend.items]
    expected_legend = [
        f"{craft}: {trace['name']}" for craft in spacecrafts for trace in traces
    ]
    assert all(legend in legend_items for legend in expected_legend)

    # Check four traces have been plotted
    assert len(plot.renderers) == 4

    # Check that the URL includes the time range parameter
    first_source = plot.renderers[0].data_source
    assert isinstance(first_source, AjaxDataSource)
    assert "range=7d" in first_source.data_url


def test_create_plots():
    """Test the create_plots function."""
    from main.plots import create_plots
    from main.widgets import checkbox_button_group

    spacecrafts = {"Spacecraft A": "red", "Spacecraft B": "blue"}

    button = checkbox_button_group(["Spacecraft A", "Spacecraft B"], "Spacecraft A")
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

            plots = create_plots(button, spacecrafts)
            assert len(plots) == 5
            assert all(isinstance(plot, figure) for plot in plots)

            # Check tools have been added
            tools = plots[0].tools
            assert any(isinstance(tool, HoverTool) for tool in tools)
            assert any(isinstance(tool, CrosshairTool) for tool in tools)

            # Check callback added to buttons
            data_source_mock.call_count == 12
