"""Plots for displaying science data."""

import datetime
import math
from pathlib import Path

from bokeh.layouts import column, row
from bokeh.models import (  # type: ignore
    AjaxDataSource,
    CrosshairTool,
    HoverTool,
    Label,
    LegendItem,
    Range1d,
    Span,
)
from bokeh.models.layouts import Column
from bokeh.plotting import figure

from .config import PlotConfig
from .utils import load_plot_config
from .widgets import (
    add_callback_to_checkbox_button,
    add_passes_checkbox,
    add_time_range_callback,
    checkbox_button_group,
    create_time_range_dropdown,
)


def get_now_vertical_line(current_time: datetime.datetime) -> Span:
    """Create a vertical line to indicate the current time on the plots.

    Args:
        current_time: The current timestamp to position the vertical line.

    Returns:
        A Span object representing the vertical line for the current time.
    """
    now_line = Span(
        location=current_time,
        dimension="height",
        line_color="gray",
        line_dash="dashed",
        line_width=1,
    )
    return now_line


def get_now_label(current_time: datetime.datetime) -> Label:
    """Create a label to indicate the current time on the plots.

    Args:
        current_time: The current timestamp to position the vertical line.

    Returns:
        A Label object representing the label for the current time.
    """
    now_label = Label(
        x=current_time.timestamp() * 1000,  # Convert to milliseconds,
        y=220,
        y_units="screen",  # use screen pixels
        text="Now",
        text_font_size="9pt",
        angle=math.pi / 2,  # rotate text
        text_align="left",
        text_baseline="middle",
        x_offset=7,  # small gap from the line
        name="now_label",
    )
    return now_label


def update_legend_on_spacecraft_selection(plot: figure) -> figure:
    """Update the legend to hide hidden spacecraft lines.

    Args:
        plot: A Bokeh figure for a timeseries plot.
    """
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

    plot.lod_threshold = None

    for measurement, args in plot_config.measurements.items():
        for spacecraft, colour in args.traces.items():
            # Create an AjaxDataSource for each spacecraft and measurement
            source = AjaxDataSource(
                data_url=f"/data/{measurement}/{spacecraft}?range={time_range}",
                polling_interval=300000,
                method="GET",
            )
            source.data = {"date": [], "measurement": []}
            plot.line(
                "date",
                "measurement",
                name=spacecraft,
                color=colour,
                source=source,
                legend_label=f"{spacecraft}: {args.label}",
                visible=spacecraft == default_spacecraft,
            )

            pass_source = AjaxDataSource(
                data_url=f"/data/passes/{spacecraft}?range={time_range}",
                polling_interval=None,
                method="GET",
            )

            plot.vstrip(
                x0="start_time",
                x1="end_time",
                source=pass_source,
                fill_color="grey",
                fill_alpha=0.1,
                line_color=None,
                name="pass_data",
                visible=False,
                legend_label="Passes",
            )

    current_time = datetime.datetime.now()
    plot.add_layout(get_now_vertical_line(current_time))
    plot.add_layout(get_now_label(current_time))
    update_legend_on_spacecraft_selection(plot)

    return plot


def create_plots(
    plots_config: list[PlotConfig],
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
    future_buffer = datetime.timedelta(days=1)
    current_time = datetime.datetime.now()
    end_time = current_time + future_buffer
    start_time = current_time - delta

    shared_x_range = Range1d(start=start_time, end=end_time)

    plots = []
    for plot_config in plots_config:
        plot = create_timeseries_plot(
            plot_config, shared_x_range, initial_time_range, default_spacecraft
        )
        plot.add_tools(hover, crosshair)
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
    plots = create_plots(plots_config, default_spacecraft, time_dropdown.value)
    add_time_range_callback(time_dropdown, plots)
    passes_button = add_passes_checkbox(plots)

    for plot in plots:
        add_callback_to_checkbox_button(
            plot=plot, button=button, pass_checkbox=passes_button
        )

    widgets = row(button, time_dropdown, sizing_mode="stretch_width")
    layout = column([widgets, passes_button, *plots], sizing_mode="stretch_width")

    return layout
