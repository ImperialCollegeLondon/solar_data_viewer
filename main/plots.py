"""Plots for displaying science data."""

from pathlib import Path

import pandas as pd
from bokeh.layouts import column, row
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

from .widgets import (
    add_spacecraft_callback,
    add_time_range_callback,
)


def create_scatter_plot(
    traces: tuple[dict[str, str], ...], source: ColumnDataSource, x_range: Range1d
) -> figure:
    """Create a timeseries scatter plot.

    Args:
        traces: A tuple of dictionaries for each trace to add to the plot, with keys
            for the col_name (in the dataframe), name (to use in legend) and colour.
        source: The ColumnDataSource containing the data.
        x_range: The shared Range1d object controlling the x-axis view.

    Returns:
        Bokeh figure for the scatter plot.
    """
    plot = figure(  # type: ignore[call-arg]
        x_axis_type="datetime", width=1200, height=300, x_range=x_range
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
    default_index: int = 0,
) -> tuple[list[figure], ColumnDataSource, Range1d]:
    """Create five plots to display solar weather data.

    Args:
        sources: A list of ColumnDataSources for the plots for each spacecraft.
        buttons: A list of buttons to add callbacks to.
        default_index: The index for which spacecraft data to display as default.

    Returns:
        A list containing the five Bokeh plots for each measurement.
    """
    source = dict(sources[default_index].data)

    # Create a shared data source and range to use across all plots
    shared_source = ColumnDataSource(data=source)
    shared_range = Range1d(
        shared_source.data["index"][0], shared_source.data["index"][-1]
    )

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

    plots = []
    for traces in plot_args:
        plot = create_scatter_plot(traces, shared_source, shared_range)
        plot.add_tools(hover)
        plot.add_tools(crosshair)
        plot.x_range = shared_range
        plots.append(plot)

    return plots, shared_source, shared_range


def create_layout(
    csv_files: tuple[Path, ...], labels: list[str], default_index: int
) -> Column:
    """Orchestrate the creation of plots, widgets, and layout.

    Args:
        csv_files: A tuple of Path objects pointing to the CSV data files.
        labels: A list of strings representing the spacecraft names.
        default_index: The integer index of the spacecraft to load by default.

    Returns:
        A Bokeh Column layout object containing the widgets and plots,
        ready to be added to a document.
    """
    sources = []
    dfs = []
    for csv in csv_files:
        df = pd.read_csv(csv, index_col=0, parse_dates=True)
        sources.append(ColumnDataSource(df))
        dfs.append(df)

    plots, shared_source, shared_range = create_plots(sources, default_index)

    time_button, time_callback = add_time_range_callback(
        shared_range, dfs[default_index]
    )
    spacecraft_button = RadioButtonGroup(labels=labels, active=default_index)

    add_spacecraft_callback(
        spacecraft_button,
        time_callback,
        time_button,
        sources,
        shared_source,
    )

    layout = column(
        [row(spacecraft_button, time_button), *plots],
        sizing_mode="stretch_width",
    )

    return layout
