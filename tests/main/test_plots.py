"""Test suite for the plots."""

from unittest.mock import patch

import pandas as pd
from bokeh.models import ColumnDataSource, CrosshairTool, HoverTool, Range1d
from bokeh.plotting import figure


def test_create_scatter_plot():
    """Test the create_scatter_plot function."""
    from main.plots import create_scatter_plot

    source = ColumnDataSource({"speed": [1, 2, 3], "density": [56, 67, 78]})
    traces = (
        {"col_name": "speed", "name": "Speed", "colour": "black"},
        {"col_name": "density", "name": "Density", "colour": "red"},
    )

    plot = create_scatter_plot(traces, source)

    # Check legend items added
    legend_items = [item.label.value for item in plot.legend.items]
    assert traces[0]["name"] in legend_items
    assert traces[1]["name"] in legend_items

    # Check two traces have been plotted
    assert len(plot.renderers) == 2


def test_create_plots():
    """Test the create_plots function."""
    from main.plots import create_plots
    from main.widgets import radio_button

    data_A = pd.DataFrame(
        {
            "bt": [22, 33, 44],
            "bz_gsm": [13, 14, 15],
            "lon_gsm": [55, 66, 77],
            "density": [56, 67, 78],
            "speed": [1, 2, 3],
            "temperature": [40, 50, 60],
        }
    )
    data_B = pd.DataFrame(
        {
            "bt": [33, 44, 55],
            "bz_gsm": [17, 18, 19],
            "lon_gsm": [77, 66, 55],
            "density": [76, 65, 54],
            "speed": [2, 2, 2],
            "temperature": [50, 50, 50],
        }
    )
    sources = [ColumnDataSource(data_A), ColumnDataSource(data_B)]
    button = radio_button(["Spacecraft A", "Spacecraft B"], 0)

    with patch("main.plots.add_callback_to_button") as callback_mock:
        plots = create_plots(sources, button)
        assert len(plots) == 5
        assert all(isinstance(plot, figure) for plot in plots)

        # Check tools have been added
        tools = plots[0].tools
        assert any(isinstance(tool, HoverTool) for tool in tools)
        assert any(isinstance(tool, CrosshairTool) for tool in tools)

        # Check x_range added
        assert isinstance(plots[0].x_range, Range1d)

        # Check callback added to buttons
        assert callback_mock.call_count == 5
