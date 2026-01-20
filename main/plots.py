"""Plots for displaying science data."""

from collections.abc import Callable
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
from bokeh.plotting import figure

from .widgets import (
    add_spacecraft_callback,
    add_time_range_callback,
    radio_button,
)


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
    source: list[ColumnDataSource],
    button_callouts: list[Callable[[figure], None]],
) -> list[figure]:
    """Create five plots to display solar weather data.

    Args:
        source: A list of ColumnDataSources for the plots for each spacecraft.
        button_callouts: A list of callouts to add to each plot for the spacecraft
            selection button.

    Returns:
        A list containing the five Bokeh plots for each measurement.
    """
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
        for button_callout in button_callouts:
            button_callout(plot)
        plots.append(plot)

    return plots


def create_layout(csv_files: tuple[Path, ...], labels: list[str], default_index: int):
    """Creates a layout object for the spacecraft data plots and widgets.

    Args:
        csv_files: A list of CSV files to read the processed test data from.
        labels: A list of names for the spacecraft.
        default_index: The index for which spacecraft data to display as default.

    Returns:
        A Column object containing the five Bokeh plots and widgets.
    """
    dfs = []
    sources = []
    for csv in csv_files:
        df = pd.read_csv(csv, index_col=0, parse_dates=True)
        dfs.append(df)
        sources.append(ColumnDataSource(df))

    shared_source = ColumnDataSource(dfs[default_index].copy())

    spacecraft_button = radio_button(labels, default_index)

    plots = create_plots(shared_source, [])

    time_button, time_callback = add_time_range_callback(plots, dfs[default_index])

    spacecraft_callback = add_spacecraft_callback(
        plots=plots,
        spacecraft_button=spacecraft_button,
        time_button=time_button,
        time_callback=time_callback,
        shared_source=shared_source,
        sources=sources,
    )

    spacecraft_button.js_on_event("button_click", spacecraft_callback)

    layout = column(
        row(spacecraft_button, time_button),
        *plots,
        sizing_mode="stretch_width",
    )

    return layout
