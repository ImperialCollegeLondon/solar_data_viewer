"""Test suite for the widgets."""

from unittest.mock import patch

from bokeh.models import ColumnDataSource
from bokeh.models.widgets.groups import RadioButtonGroup


def test_add_callback_to_button():
    """Test the add_callback_to_button function."""
    from main.plots import create_scatter_plot
    from main.widgets import add_callback_to_button, radio_button

    sources = [
        ColumnDataSource({"speed": [1, 2, 3], "density": [56, 67, 78]}),
        ColumnDataSource({"speed": [6, 8, 7], "density": [66, 44, 22]}),
    ]
    traces = (
        {"col_name": "speed", "name": "Speed", "colour": "black"},
        {"col_name": "density", "name": "Density", "colour": "red"},
    )

    button = radio_button(labels=["A", "B"], default_index=0)
    plot = create_scatter_plot(traces, sources[0])

    expected_code = """const selection = button.active;
        const orig_source = plot.renderers[0].data_source;
        const new_source = sources[selection];

        const n = new_source.data.index.length;
        plot.x_range.start = new_source.data.index[0];
        plot.x_range.end = new_source.data.index[n-1];

        orig_source.data = new_source.data;"""

    with patch.object(RadioButtonGroup, "js_on_event") as js_mock:
        add_callback_to_button(plot, button, sources)
        called_args = js_mock.call_args.args[1]
        assert called_args.args["plot"] == plot
        assert called_args.args["button"] == button
        assert all(
            isinstance(source, ColumnDataSource)
            for source in called_args.args["sources"]
        )
        assert called_args.code == expected_code
