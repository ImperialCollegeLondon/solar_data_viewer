"""Plots for displaying science data."""

import datetime
from pathlib import Path

from bokeh.layouts import column, row
from bokeh.models import (  # type: ignore
    AjaxDataSource,
    CrosshairTool,
    HoverTool,
    LegendItem,
    Range1d,
)
from bokeh.models.annotations.geometry import Span
from bokeh.models.layouts import Column
from bokeh.models.widgets.groups import CheckboxButtonGroup
from bokeh.plotting import figure

from .config import PlotConfig
from .utils import load_plot_config
from .widgets import (
    add_callback_to_checkbox_button,
    add_time_range_callback,
    checkbox_button_group,
    create_time_range_dropdown,
)


def create_timeseries_plot(
    plot_config: PlotConfig,
    x_range: Range1d,
    time_range: str = "3d",
    default_spacecraft: str = "IMAP",
) -> figure:
    """Create a timeseries plot.

    Args:
        plot_config: A Pydantic model containing fields for the title, unit and
            measurements. The measurements are Pydantic models containing their label
            and colours to be used for the traces for each spacecraft.
        x_range: The shared x-axis range for the plots.
        time_range: The initial time range for the data to display (default is 3 days).
        default_spacecraft: The spacecraft data to display as default.

    Returns:
        Bokeh figure for the timeseries plot.
    """
    plot = figure(  # type: ignore[call-arg]
        x_axis_type="datetime",
        width=1200,
        height=300,
        x_range=x_range,
    )

    # Disable level-of-detail downsampling to ensure the lines
    # are always fully rendered and not greyed out.
    plot.lod_threshold = None

    for measurement, args in plot_config.measurements.items():
        for spacecraft, colour in args.traces.items():
            # Create an AjaxDataSource for each spacecraft and measurement
            source = AjaxDataSource(
                data_url=f"/data/{measurement}/{spacecraft}?range={time_range}",
                polling_interval=300000,
                method="GET",
            )

            plot.line(
                "date",
                "measurement",
                name=spacecraft,  # Enables selecting data in callback
                color=colour,
                source=source,
                legend_label=f"{spacecraft}: {args.label}",
                visible=spacecraft == default_spacecraft,
            )

    plot.legend.click_policy = "hide"

    if not plot.legend:
        return plot

    legend = plot.legend[0]  # extract the first legend box from the list
    plot.add_layout(legend, "right")
    legend.click_policy = "hide"

    # Hide legend items for hidden spacecraft line
    # A legend item can control multiple glyphs so we need to check
    # the first renderer to see if the main line is visible.
    for item in legend.items:
        if (
            isinstance(item, LegendItem)
            and item.renderers
            and not item.renderers[0].visible
        ):
            item.visible = False
    return plot


def create_plots(
    plots_config: list[PlotConfig],
    button: CheckboxButtonGroup,
    default_spacecraft: str = "IMAP",
    initial_time_range: str = "3d",
) -> list[figure]:
    """Create five plots to display solar weather data.

    Args:
        plots_config: A list of PlotConfig objects containing the config arguments for
            each plot, as defined in the config TOML file.
        button: A checkbox button to select the spacecraft to display data for.
        default_spacecraft: The spacecraft data to display as default.
        initial_time_range: The initial time range for the data to display.

    Returns:
        A list containing the five Bokeh plots for each measurement.
    """
    # Create tooltips and crosshair tool to use across all plots
    hover = HoverTool(
        tooltips=[("Time", "$x{%Y-%m-%d %H:%M:%S}"), ("Value", "$y{0.00}")],
        formatters={"$x": "datetime"},
    )
    height = Span(dimension="height", line_dash="dotted", line_width=2)
    crosshair = CrosshairTool(overlay=height, dimensions="height")

    # Calculate start and end times
    delta = datetime.timedelta(days=3)
    end_time = datetime.datetime.now()
    start_time = end_time - delta

    shared_x_range = Range1d(start=start_time, end=end_time)

    plots = []
    for plot_config in plots_config:
        plot = create_timeseries_plot(
            plot_config, shared_x_range, initial_time_range, default_spacecraft
        )
        plot.add_tools(hover, crosshair)
        add_callback_to_checkbox_button(plot=plot, button=button)
        plot.yaxis.axis_label = f"{plot_config.title} ({plot_config.unit})"
        plots.append(plot)

    return plots


def create_layout() -> Column:
    """Creates a layout object for the spacecraft data plots and widgets.

    Returns:
        A Column object containing the five Bokeh plots and widgets.
    """
    config = load_plot_config(Path(__file__).parent / "config" / "plots.toml")
    plots_config = config.plots
    spacecrafts = config.spacecrafts
    default_spacecraft = config.default_spacecraft

    button = checkbox_button_group(spacecrafts, default_spacecraft)
    time_dropdown = create_time_range_dropdown()
    plots = create_plots(plots_config, button, default_spacecraft, time_dropdown.value)
    add_time_range_callback(time_dropdown, plots)

    widgets = row(button, time_dropdown, sizing_mode="stretch_width")
    layout = column([widgets, *plots], sizing_mode="stretch_width")

    return layout
