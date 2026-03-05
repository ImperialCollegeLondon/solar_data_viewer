"""Test suite for the widgets."""

from unittest.mock import patch

from bokeh.models import CustomJS, Select  # type: ignore[attr-defined]
from bokeh.models.widgets.groups import CheckboxButtonGroup, CheckboxGroup

from main.widgets import (
    add_callback_to_checkbox_button,
    add_passes_checkbox,
    add_time_range_callback,
    checkbox_button_group,
)


@patch("main.utils.process_data_from_test_csvs")
def test_add_callback_to_checkbox_button(plot_context):
    """Test the add_callback_to_checkbox_button function."""
    plot = plot_context["plot"]
    button = checkbox_button_group(labels=["A", "B"], default_spacecraft="A")
    pass_check = add_passes_checkbox([plot], default_spacecraft="A")
    with patch.object(CheckboxButtonGroup, "js_on_change") as js_mock:
        add_callback_to_checkbox_button(plot, button, pass_check)

        called_args = js_mock.call_args.args[1]
        assert called_args.args["button"] == button
        assert called_args.args["pass_checkbox"] == pass_check
        expected_legend = (
            plot.legend[0] if isinstance(plot.legend, list) else plot.legend
        )
        assert called_args.args["legend"] == expected_legend


@patch("main.utils.process_data_from_test_csvs")
def test_add_time_range_callback(plot_context):
    """Test the add_time_range_callback function."""
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
    """Test the add_passes_checkbox function."""
    plots = plot_context["plot"]

    # Test checkbox is hidden when IMAP is selected
    checkbox_imap = add_passes_checkbox(plots, default_spacecraft="IMAP")
    assert isinstance(checkbox_imap, CheckboxGroup)
    assert checkbox_imap.visible is False
    assert checkbox_imap.labels == ["Show Pass Data"]

    # Test checkbox is hidden when SO is selected
    checkbox_so = add_passes_checkbox(plots, default_spacecraft="SO")
    assert checkbox_so.visible is True
    assert "active" in str(checkbox_so.js_property_callbacks)
