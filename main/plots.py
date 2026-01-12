"""Plots for displaying science data."""

from pathlib import Path

import pandas as pd
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, CrosshairTool, HoverTool, Range1d, Span
from bokeh.models.layouts import Column
from bokeh.plotting import figure


def create_scatter_plot(
    traces: tuple[dict[str, str], ...], source: ColumnDataSource
) -> figure:
    """Create a timeseries scatter plots.

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

    plot.legend.location = "bottom_right"

    return plot


def create_plots() -> Column:
    """Create plots for ACE data.

    Returns:
        A Column object containing the five Bokeh plots.
    """
    df = pd.read_csv(Path(__file__).parent / "data" / "test_data.csv")
    source = ColumnDataSource(df)

    plot_args = (
        (
            {"col_name": "bt", "name": "Bt", "colour": "black"},
            {"col_name": "bz_gsm", "name": "Bz GSM", "colour": "red"},
        ),
        ({"col_name": "lon_gsm", "name": "Phi GSM(deg)", "colour": "deepskyblue"},),
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

    range = Range1d(df.index[0], df.index[-1])

    plots = []
    for traces in plot_args:
        plot = create_scatter_plot(traces, source)
        plot.add_tools(hover)
        plot.add_tools(crosshair)
        plot.x_range = range
        plots.append(plot)

    layout = column(plots)
    return layout
