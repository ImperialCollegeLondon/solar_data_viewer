"""Plots for displaying science data."""

import datetime
import math
from pathlib import Path
from typing import Literal

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
from bokeh.models.layouts import Column, Row
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
    current_time = datetime.datetime.now()
    # Add vertical line for current time
    plot.add_layout(get_now_vertical_line(current_time))
    # Add 'Now' label next to the vertical line
    plot.add_layout(get_now_label(current_time))
    # Update legend to show/hide selected spacecraft data
    update_legend_on_spacecraft_selection(plot)

    return plot


def create_timeseries_plots(
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
        add_callback_to_checkbox_button(plot=plot, button=button)
        plot.yaxis.axis_label = f"{plot_config.title} ({plot_config.unit})"
        plots.append(plot)

    return plots


def create_timeseries_layout() -> Column:
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
    plots = create_timeseries_plots(
        plots_config, button, default_spacecraft, time_dropdown.value
    )
    add_time_range_callback(time_dropdown, plots)

    widgets = row(button, time_dropdown, sizing_mode="stretch_width")
    layout = column([widgets, *plots], sizing_mode="stretch_width")

    return layout


def create_solar_orbiter_plot(
    title: str,
    x_axis_label: str,
    y_axis_label: str,
    unit: Literal["AU", "angle"],
    radii: list[float],
) -> figure:
    """Create a plot for the Solar Orbiter trajectory.

    Args:
        title: The plot title.
        x_axis_label: Label to display on the x-axis.
        y_axis_label: Label to display on the y-axis.
        unit: Whether to plot in AU (the fixed Earth frame) or angle (the Earth-Sun-
            spacecraft angle).
        radii: A list of radii for plotting dashed circles.

    Returns:
        A Bokeh figure containing the trajectory of Solar Orbiter in the fixed
            Earth frame.
    """
    plot = figure(  # type: ignore[call-arg]
        title=title,
        width=600,
        height=600,
        match_aspect=True,
        x_axis_label=x_axis_label,
        y_axis_label=y_axis_label,
    )

    # Create an AjaxDataSource for the spacecraft static position
    static_source = AjaxDataSource(
        data_url=f"/trajectory_data/{unit}/static",
        polling_interval=30000,
        method="GET",
    )
    objects = plot.scatter(
        "x", "y", color="colour", legend_field="name", size=15, source=static_source
    )

    # Create an AjaxDataSource for the trajectory data
    trajectory_source = AjaxDataSource(
        data_url=f"/trajectory_data/{unit}/trajectory",
        polling_interval=30000,
        method="GET",
    )
    plot.line(
        "x", "y", color="blue", source=trajectory_source, legend_label="Next 7 days"
    )

    for r in radii:
        plot.circle(
            x=0,
            y=0,
            radius=r,
            fill_alpha=0,
            line_color="gray",
            line_dash="dotted",
            line_width=1,
        )
    hover = HoverTool(tooltips=[("ID", "@name")], renderers=[objects])
    plot.add_tools(hover)

    return plot


def create_solar_orbiter_layout() -> Row:
    """Create a layout object for the Solar Orbiter trajectory plots.

    Returns:
        A Row object containing the two Bokeh plots.
    """
    layout = row(
        [
            create_solar_orbiter_plot(
                title="Fixed Earth frame",
                x_axis_label="AU",
                y_axis_label="AU",
                unit="AU",
                radii=[0.5, 0.75, 1.0],
            ),
            create_solar_orbiter_plot(
                title="Earth-Sun-spacecraft angle",
                x_axis_label="Longitude separation (deg)",
                y_axis_label="Latitude separation (deg)",
                unit="angle",
                radii=[10, 20],
            ),
        ]
    )
    return layout


def create_l1_plot(
    title: str = "L1 spacecraft",
    x_axis_label: str = "GSE y (Rᴇ)",
    y_axis_label: str = "GSE z (Rᴇ)",
) -> figure:
    """Create a plot for the L1 spacecraft trajectories.

    The plot shows blobs for the current spacecraft positions, lines showing
    their past 7 days and a circle for the magnetosphere.

    Args:
        title: The plot title.
        x_axis_label: Label to display on the x-axis.
        y_axis_label: Label to display on the y-axis.

    Returns:
        A Bokeh figure containing the trajectories of the L1 spacecraft in
            GSE coordinates.
    """
    plot = figure(  # type: ignore[call-arg]
        title=title,
        width=1000,
        height=500,
        match_aspect=True,
        x_axis_label=x_axis_label,
        y_axis_label=y_axis_label,
        x_range=Range1d(-110, 110),
        y_range=Range1d(-55, 55),
    )

    # Add circle representing magnetosphere
    plot.circle(
        x=16,  # GSE y
        y=0,  # GSE z
        radius=20,
        fill_alpha=0,
        line_color="gray",
        line_dash="dotted",
        line_width=1,
        legend_label="Magnetosphere",
    )

    # Create an AjaxDataSource for the spacecraft static position
    static_source = AjaxDataSource(
        data_url="/l1_data/static",
        polling_interval=30000,
        method="GET",
    )
    objects = plot.scatter(
        "y", "z", color="colour", legend_field="name", size=15, source=static_source
    )

    # Create an AjaxDataSource for the trajectory data
    trajectory_source = AjaxDataSource(
        data_url="/l1_data/trajectory",
        polling_interval=30000,
        method="GET",
    )
    plot.multi_line(
        "y", "z", color="colour", legend_field="name", source=trajectory_source
    )

    hover = HoverTool(tooltips=[("ID", "@name")], renderers=[objects])
    plot.add_tools(hover)

    return plot
