"""Test suite for the widgets."""

from unittest.mock import Mock, patch

from bokeh.models import CustomJS, Range1d, Select  # type: ignore[attr-defined]
from bokeh.models.widgets.groups import CheckboxButtonGroup, CheckboxGroup

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

    spacecrafts = ["A", "B"]
    default_spacecraft = "A"

    x_range = Range1d(start=0, end=1)

    plot = create_timeseries_plot(plot_config, spacecrafts, x_range, default_spacecraft)

    with patch.object(CheckboxButtonGroup, "js_on_change") as js_mock:
        add_callback_to_checkbox_button(plot, button)
        called_args = js_mock.call_args.args[1]
        assert called_args.args["button"] == button
        expected_legend = (
            plot.legend[0] if isinstance(plot.legend, list) else plot.legend
        )
        assert called_args.args["legend"] == expected_legend


@patch("main.utils.process_data_from_test_csvs")
def test_add_time_range_callback(plot_context):
    """Test the add_time_range_callback function."""
    from main.widgets import add_time_range_callback

    plots = [plot_context["plot"]]
    dropdown = Select(value="3d", options=[("1d", "1 Day"), ("3d", "3 Days")])

    with patch.object(Select, "js_on_change") as js_mock:
        add_time_range_callback(dropdown, plots)
        assert js_mock.called
        attr, callback = js_mock.call_args.args

        assert attr == "value"
        assert isinstance(callback, CustomJS)

        assert callback.args["dropdown"] == dropdown
        assert callback.args["plots"] == plots
        assert callback.args["x_range"] == plots[0].x_range


@patch("main.utils.process_data_from_test_csvs")
def test_add_passes_checkbox(plot_context):
    """Test the add_passes_checkbox adds checkbox when SO is selected."""
    from main.widgets import add_passes_checkbox

    plots = plot_context["plot"]

    # Test checkbox is hidden when IMAP is selected
    checkbox_imap = add_passes_checkbox(plots, default_spacecraft="IMAP")
    assert isinstance(checkbox_imap, CheckboxGroup)
    assert checkbox_imap.visible is False
    assert checkbox_imap.labels == ["Show Contact Schedule Window (Pass)"]

    # Test checkbox is shown when SO is selected
    checkbox_so = add_passes_checkbox(plots, default_spacecraft="SO")
    assert checkbox_so.visible is True
    assert "active" in str(checkbox_so.js_property_callbacks)
