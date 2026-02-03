"""Test suite for the widgets."""

from unittest.mock import Mock, patch

from bokeh.models import Range1d
from bokeh.models.widgets.groups import CheckboxButtonGroup

from main.config import MeasurementConfig, PlotConfig


@patch("main.utils.process_data_from_test_csvs")
def test_add_callback_to_checkbox_button(process_data_mock: Mock):
    """Test the add_callback_to_checkbox_button function."""
    from main.plots import create_timeseries_plot
    from main.widgets import add_callback_to_checkbox_button, checkbox_button_group

    process_data_mock.return_value = {
        "measurement": [3.0, 4.0, 5.0],
        "date": [1767867720000, 1767867780000, 1767867840000],
    }

    button = checkbox_button_group(labels=["A", "B"], default_spacecraft="A")
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

    plot = create_timeseries_plot(plot_config, x_range, default_spacecraft)

    with patch.object(CheckboxButtonGroup, "js_on_event") as js_mock:
        add_callback_to_checkbox_button(plot, button)
        called_args = js_mock.call_args.args[1]
        assert called_args.args["button"] == button
        expected_legend = (
            plot.legend[0] if isinstance(plot.legend, list) else plot.legend
        )
        assert called_args.args["legend"] == expected_legend
