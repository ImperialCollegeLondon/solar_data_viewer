"""Plots for displaying science data."""

from pathlib import Path

import pandas as pd
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource,
    CrosshairTool,
    HoverTool,
    RadioButtonGroup,
    Range1d,
    Span,
)
from bokeh.models.layouts import Column
from bokeh.plotting import figure

from .widgets import add_callback_to_button, dropdown_button, radio_button


def create_scatter_plot(
    traces: tuple[dict[str, str], ...], source: ColumnDataSource
) -> figure:
    """Create a timeseries scatter plot.

    Args:
        traces: A tuple of dictionaries for each trace to add to the plot, with keys
            for the col_name (in the dataframe), name (to use in legend) and colour.
        source: The ColumnDataSource containing the data.

    Returns:
        Bokeh figure for the scatter plot.
    """
    plot = figure(
        x_axis_type="datetime",
        width=1200,
        height=300,
    )

    for trace in traces:
        plot.scatter(
            "index",
            trace["col_name"],
            color=trace["colour"],
            size=2,
            source=source,
            legend_label=trace["name"],
        )

    plot.legend.click_policy = "hide"
    plot.legend.location = "bottom_right"

    return plot


def create_plots(
    sources: list[ColumnDataSource],
    button: RadioButtonGroup,
    default_index: int = 0,
) -> list[figure]:
    """Create plots for ACE data.

    Args:
        sources: A list of ColumnDataSources for the plots for each spacecraft.
        button: A radio button to select the spacecraft to display data for.
        default_index: The index for which spacecraft data to display as default.

    Returns:
        A list containing the five Bokeh plots for each measurement.
    """
    source = sources[default_index]
    plot_args = (
        (
            {"col_name": "bt", "name": "Bt", "colour": "black"},
            {"col_name": "bz_gsm", "name": "Bz GSM", "colour": "red"},
        ),
        ({"col_name": "lon_gsm", "name": "Phi GSM (deg)", "colour": "deepskyblue"},),
        ({"col_name": "density", "name": "Density (1/cm\u00b3)", "colour": "orange"},),
        ({"col_name": "speed", "name": "Speed (km/s)", "colour": "darkviolet"},),
        ({"col_name": "temperature", "name": "Temperature (K)", "colour": "green"},),
    )

    # Create tooltips and crosshair tool to use across all plots
    hover = HoverTool(
        tooltips=[("Time", "$x{%Y-%m-%d %H:%M:%S}"), ("Value", "$y{0.00}")],
        formatters={"$x": "datetime"},
    )
    height = Span(dimension="height", line_dash="dotted", line_width=2)
    crosshair = CrosshairTool(overlay=height, dimensions="height")
    range = Range1d(source.data["index"][0], source.data["index"][-1])

    plots = []
    for traces in plot_args:
        plot = create_scatter_plot(traces, source)
        plot.add_tools(hover)
        plot.add_tools(crosshair)
        plot.x_range = range
        add_callback_to_button(plot, button, sources)
        plots.append(plot)

    return plots


def create_layout(
    csv_files: tuple[Path, ...], labels: list[str], default_index: int
) -> Column:
    """Creates a layout object for the spacecraft data plots.

    Args:
        csv_files: A list of CSV files to read the processed test ACE data from.
        labels: A list of names for the spacecraft.
        default_index: The index for which spacecraft data to display as default.

    Returns:
        A Column object containing the five Bokeh plots.
    """
    sources = []
    for csv in csv_files:
        df = pd.read_csv(csv, index_col=0, parse_dates=True)
        source = ColumnDataSource(df)
        sources.append(source)

    # Create button to select the spacecraft
    button = radio_button(labels, default_index)

    # Create dropdown to select the time range
    time_ranges = [("1 day", "days_1"), ("3 days", "days_3"), ("7 days", "days_7")]
    dropdown = dropdown_button(label="Select time range", items=time_ranges)

    plots = create_plots(sources, button, default_index)
    layout = column([row([dropdown, button]), *plots], sizing_mode="stretch_width")

    return layout
