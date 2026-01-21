"""Plots for displaying science data."""

from bokeh.layouts import column
from bokeh.models import (
    AjaxDataSource,
    CrosshairTool,
    HoverTool,
)
from bokeh.models.annotations.geometry import Span
from bokeh.models.layouts import Column
from bokeh.plotting import figure


def create_scatter_plot(traces, spacecrafts: dict[str, str]) -> figure:
    """Create a timeseries scatter plot.

    Args:
        traces: A tuple of dictionaries for each trace to add to the plot, with keys:
            "measurement", for measurement name; "name", to use in the legend,
            and "colours", a nested dictionary with spacecraft as keys and the colour
            to use for plotting.
        spacecrafts: A dictionary with the abbreviated spacecraft name to use in the
            data url and the display name as the value.

    Returns:
        Bokeh figure for the scatter plot.
    """
    plot = figure(  # type: ignore[call-arg]
        x_axis_type="datetime",
        width=1200,
        height=300,
    )

    for spacecraft in spacecrafts:
        for trace in traces:
            # Create an AjaxDataSource for each spacecraft and measurement
            display_name = spacecrafts[spacecraft]

            source = AjaxDataSource(
                data_url=f"/data/{trace['measurement']}/{spacecraft}",
                polling_interval=1000,
                method="GET",
            )

            plot.scatter(
                "date",
                "measurement",
                color=trace["colours"][spacecraft],
                size=2,
                source=source,
                legend_label=f"{display_name}: {trace['name']}",
            )

    plot.legend.click_policy = "hide"
    plot.legend.location = "bottom_right"

    return plot


def create_plots() -> list[figure]:
    """Create five plots to display solar weather data.

    Returns:
        A list containing the five Bokeh plots for each measurement.
    """
    # TODO: Move plot args into a config file
    plot_args = (
        (
            {
                "measurement": "bt",
                "name": "Bt",
                "colours": {"IMAP": "black", "SO": "gray"},
            },
            {
                "measurement": "bz_gsm",
                "name": "Bz GSM",
                "colours": {"IMAP": "darkred", "SO": "red"},
            },
        ),
        (
            {
                "measurement": "lon_gsm",
                "name": "Phi GSM (deg)",
                "colours": {"IMAP": "darkblue", "SO": "deepskyblue"},
            },
        ),
        (
            {
                "measurement": "density",
                "name": "Density (1/cm\u00b3)",
                "colours": {"IMAP": "orangered", "SO": "orange"},
            },
        ),
        (
            {
                "measurement": "speed",
                "name": "Speed (km/s)",
                "colours": {"IMAP": "darkviolet", "SO": "violet"},
            },
        ),
        (
            {
                "measurement": "temperature",
                "name": "Temperature (K)",
                "colours": {"IMAP": "darkgreen", "SO": "green"},
            },
        ),
    )

    spacecrafts = {"IMAP": "IMAP", "SO": "Solar Orbiter"}

    # Create tooltips and crosshair tool to use across all plots
    hover = HoverTool(
        tooltips=[("Time", "$x{%Y-%m-%d %H:%M:%S}"), ("Value", "$y{0.00}")],
        formatters={"$x": "datetime"},
    )
    height = Span(dimension="height", line_dash="dotted", line_width=2)
    crosshair = CrosshairTool(overlay=height, dimensions="height")

    plots = []
    for traces in plot_args:
        plot = create_scatter_plot(traces, spacecrafts)
        plot.add_tools(hover)
        plot.add_tools(crosshair)
        plots.append(plot)

    return plots


def create_layout() -> Column:
    """Creates a layout object for the spacecraft data plots and widgets.

    Returns:
        A Column object containing the five Bokeh plots and widgets.
    """
    plots = create_plots()
    layout = column(plots, sizing_mode="stretch_width")

    return layout
