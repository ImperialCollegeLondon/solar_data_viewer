"""Test suite for the plots."""

import math
from datetime import datetime
from unittest.mock import patch

from bokeh.models import (  # type: ignore
    AjaxDataSource,
    CrosshairTool,
    HoverTool,
    Legend,
    LegendItem,
    Span,
)
from bokeh.plotting import figure

from main.config import MeasurementConfig, PlotConfig
from main.plots import add_pass_contact_vstrip, add_pass_source


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
    assert len(plot.renderers) == 5  # 4 lines + 1 vstrip

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
            data_source_mock.call_count == 5


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


def test_get_now_vertical_line():
    """Test the get_now_vertical_line function."""
    from main.plots import get_now_vertical_line

    now = datetime.now().timestamp() * 1000
    line = get_now_vertical_line(now)

    assert isinstance(line, Span)
    assert line.location == now
    assert line.line_dash == [6]  # Bokeh maps 'dashed' to [6]
    assert line.line_color == "gray"


def test_get_now_label():
    """Test the get_now_label function."""
    from main.plots import get_now_label

    now = datetime.now()
    label = get_now_label(now)

    assert label.x == now.timestamp() * 1000
    assert label.text == "Now"
    assert label.angle == math.pi / 2
    assert label.y_units == "screen"
    assert label.name == "now_label"


def test_update_legend_hides_invisible_renderers():
    """Test that the update_legend_on_spacecraft_selection function hides legend items
    for invisible renderers.
    """  # noqa: D205
    from main.plots import update_legend_on_spacecraft_selection

    p = figure()
    # Create a renderer and set it to invisible
    r = p.line([0, 1], [0, 1], visible=False)

    # Build a legend structure
    item = LegendItem(label="Test", renderers=[r])
    legend = Legend(items=[item])
    p.add_layout(legend)

    update_legend_on_spacecraft_selection(p)

    assert item.visible is False


@patch("main.utils.process_data_from_test_csvs")
def test_add_pass_source(plot_context):
    """Test that add_pass_source adds an AjaxDataSource and a vstrip."""
    plot = plot_context["plot"]
    spacecraft = "SO"
    time_range = "7d"

    source = add_pass_source(plot, spacecraft, time_range)

    assert isinstance(source, AjaxDataSource)
    assert source.data_url == f"/data/passes/{spacecraft}?range={time_range}"


def test_add_pass_contact_vstrip():
    """Test add_pass_contact_vstrip function."""
    plot = figure()
    spacecraft = "SO"
    time_range = "7d"

    source = add_pass_source(plot, spacecraft, time_range)

    add_pass_contact_vstrip(source, plot)

    pass_renderers = [r for r in plot.renderers if r.name == "pass_data"]
    assert len(pass_renderers) == 1

    renderer = pass_renderers[0]
    assert renderer.data_source == source
    assert renderer.glyph.x0 == "start_time"
    assert renderer.glyph.x1 == "end_time"
