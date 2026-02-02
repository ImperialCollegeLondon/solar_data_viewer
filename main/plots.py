"""Plots for displaying science data."""

from pathlib import Path

from bokeh.layouts import column
from bokeh.models import AjaxDataSource, CrosshairTool, HoverTool
from bokeh.models.annotations.geometry import Span
from bokeh.models.layouts import Column
from bokeh.models.widgets.groups import CheckboxButtonGroup
from bokeh.plotting import figure

from .utils import PlotConfig, load_plot_config
from .widgets import add_callback_to_checkbox_button, checkbox_button_group


def create_timeseries_plot(
    plot_config: PlotConfig,
) -> figure:
    """Create a timeseries plot.

    Args:
        plot_config: A dictionary containing the title, unit, measurements (a nested
            dictionary for each measurement, including their label and colours for each
            spacecraft trace.

    Returns:
        Bokeh figure for the timeseries plot.
    """
    plot = figure(  # type: ignore[call-arg]
        x_axis_type="datetime",
        width=1200,
        height=300,
    )

    for measurement, args in plot_config["measurements"].items():
        for spacecraft, colour in args["traces"].items():
            # Create an AjaxDataSource for each spacecraft and measurement
            source = AjaxDataSource(
                data_url=f"/data/{measurement}/{spacecraft}",
                polling_interval=1000,
                method="GET",
            )

            plot.line(
                "date",
                "measurement",
                name=spacecraft,  # Enables selecting data in callback
                color=colour,
                source=source,
                legend_label=f"{spacecraft}: {args['label']}",
                visible=False,
            )

    plot.legend.click_policy = "hide"
    plot.legend.location = "bottom_right"

    return plot


def create_plots(
    plots_config: list[PlotConfig],
    button: CheckboxButtonGroup,
    default_spacecraft: str = "IMAP",
) -> list[figure]:
    """Create five plots to display solar weather data.

    Args:
        plots_config: A list of dictionaries containing the config arguments for each
            plot, as defined in the config TOML file.
        button: A checkbox button to select the spacecraft to display data for.
        default_spacecraft: The spacecraft data to display as default.

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

    plots = []
    for plot_config in plots_config:
        plot = create_timeseries_plot(plot_config)
        plot.add_tools(hover, crosshair)
        # Display data for one spacecraft as default
        plot.select(name=default_spacecraft).visible = True  # type: ignore[attr-defined]
        add_callback_to_checkbox_button(plot=plot, button=button)
        plot.yaxis.axis_label = f"{plot_config['title']} ({plot_config['unit']})"
        plots.append(plot)

    return plots


def create_layout() -> Column:
    """Creates a layout object for the spacecraft data plots and widgets.

    Returns:
        A Column object containing the five Bokeh plots and widgets.
    """
    plots_config, spacecrafts, default_spacecraft = load_plot_config(
        config_file=Path(__file__).parent / "config" / "plots.toml"
    )
    button = checkbox_button_group(spacecrafts, default_spacecraft)
    plots = create_plots(plots_config, button, default_spacecraft)
    layout = column([button, *plots], sizing_mode="stretch_width")

    return layout
