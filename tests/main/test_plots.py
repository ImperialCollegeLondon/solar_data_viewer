"""Test suite for the plots."""

import pandas as pd
from bokeh.models import (
    ColumnDataSource,
    CustomJS,
)
from bokeh.models.widgets.buttons import Dropdown
from bokeh.plotting import figure

from main.plots import add_time_range_callback


def test_create_scatter_plot():
    """Test the create_scatter_plot function."""
    from main.plots import create_scatter_plot

    source = ColumnDataSource({"speed": [1, 2, 3], "density": [56, 67, 78]})
    traces = (
        {"col_name": "speed", "name": "Speed", "colour": "black"},
        {"col_name": "density", "name": "Density", "colour": "red"},
    )

    plot = create_scatter_plot(traces, source)

    assert isinstance(plot, figure)

    # Check legend items added
    legend_items = [item.label.value for item in plot.legend.items]
    assert traces[0]["name"] in legend_items
    assert traces[1]["name"] in legend_items

    # Check two traces have been plotted
    assert len(plot.renderers) == 2


# def test_create_plots():
#     from main.plots import create_plots
#     from main.widgets import radio_button

#     data_A = pd.DataFrame(
#         {
#             "index": [1, 2, 3],
#             "bt": [22, 33, 44],
#             "bz_gsm": [13, 14, 15],
#             "lon_gsm": [55, 66, 77],
#             "density": [56, 67, 78],
#             "speed": [1, 2, 3],
#             "temperature": [40, 50, 60],
#         }
#     )

#     shared_source = ColumnDataSource(data_A)
#     button = radio_button(["Spacecraft A", "Spacecraft B"], 0)

#     with patch("main.plots.add_spacecraft_callback") as callback_mock:
#         plots = create_plots(shared_source, button)

#         assert len(plots) == 5
#         assert all(isinstance(plot, figure) for plot in plots)

#         tools = plots[0].tools
#         assert any(isinstance(tool, HoverTool) for tool in tools)
#         assert any(isinstance(tool, CrosshairTool) for tool in tools)

#         assert isinstance(plots[0].x_range, Range1d)

#         assert callback_mock.call_count == 5


def test_add_time_range_callback():
    """Test the add_time_range_callback function."""
    # Create a simple dataframe with a datetime index
    df = pd.DataFrame(
        {
            "bt": [10, 20, 30],
            "bz_gsm": [1, 2, 3],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="H"),
    )

    from bokeh.plotting import figure

    plots = [figure() for _ in range(3)]

    # Run the function
    widget, callback = add_time_range_callback(plots, df)

    assert isinstance(widget, Dropdown)
    assert widget.label == "Time Range"
    assert len(widget.menu) == 3
    assert widget.menu[0][1] == "1d"

    assert isinstance(callback, CustomJS)
    assert "cb_obj.item" in callback.code
    assert "menu_item_click" in widget.js_event_callbacks

    # Ensure the callback is registered for the correct event
    events = widget.js_event_callbacks
    assert "menu_item_click" in events
    assert callback in events["menu_item_click"]

    # Ensure df_start and df_end were passed correctly
    assert "df_start" in callback.args
    assert "df_end" in callback.args
    assert callback.args["df_start"] < callback.args["df_end"]
