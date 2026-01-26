"""Plots for displaying science data."""

from pathlib import Path

import pandas as pd
from bokeh.layouts import column
from bokeh.models import (
    ColumnDataSource,
    CrosshairTool,
    HoverTool,
    Range1d,
)
from bokeh.models.annotations.geometry import Span
from bokeh.models.layouts import Column
from bokeh.models.widgets.groups import RadioButtonGroup
from bokeh.plotting import figure

from .widgets import add_callback_to_button, radio_button


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
    plot = figure(  # type: ignore[call-arg]
        x_axis_type="datetime",
        width=1200,
        height=300,
    )

    for trace in traces:
        plot.line(
            "index",
            trace["col_name"],
            color=trace["colour"],
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
    """Create five plots to display solar weather data.

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
            {"col_name": "bt", "name": "Bt", "unit": "nT", "colour": "black"},
            {"col_name": "bz_gsm", "name": "Bz GSM", "unit": "nT", "colour": "red"},
        ),
        (
            {
                "col_name": "lon_gsm",
                "name": "Phi GSM",
                "unit": "deg",
                "colour": "deepskyblue",
            },
        ),
        (
            {
                "col_name": "density",
                "name": "Density",
                "unit": "1/cm³",
                "colour": "orange",
            },
        ),
        (
            {
                "col_name": "speed",
                "name": "Speed",
                "unit": "km/s",
                "colour": "darkviolet",
            },
        ),
        (
            {
                "col_name": "temperature",
                "name": "Temperature",
                "unit": "K",
                "colour": "green",
            },
        ),
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
        plot.yaxis.axis_label = f"{traces[0]['name']} ({traces[0]['unit']})"
        add_callback_to_button(plot, button, sources)
        plots.append(plot)

    return plots


def create_layout(
    csv_files: tuple[Path, ...], labels: list[str], default_index: int
) -> Column:
    """Creates a layout object for the spacecraft data plots and widgets.

    Args:
        csv_files: A list of CSV files to read the processed test data from.
        labels: A list of names for the spacecraft.
        default_index: The index for which spacecraft data to display as default.

    Returns:
        A Column object containing the five Bokeh plots and widgets.
    """
    sources = []
    for csv in csv_files:
        df = pd.read_csv(csv, index_col=0, parse_dates=True)
        source = ColumnDataSource(df)
        sources.append(source)

    # Create button to select the spacecraft
    button = radio_button(labels, default_index)

    plots = create_plots(sources, button, default_index)
    layout = column([button, *plots], sizing_mode="stretch_width")

    return layout
