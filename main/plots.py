"""Plots for displaying science data."""

from bokeh.layouts import column
from bokeh.models import AjaxDataSource, CrosshairTool, HoverTool
from bokeh.models.annotations.geometry import Span
from bokeh.models.layouts import Column
from bokeh.models.widgets.groups import CheckboxButtonGroup
from bokeh.plotting import figure

from .widgets import add_callback_to_checkbox_button, checkbox_button_group


def create_scatter_plot(
    traces: tuple[dict[str, str], ...],
    spacecrafts: dict[str, str],
    default_spacecraft: str = "IMAP",
) -> figure:
    """Create a timeseries scatter plot.

    Args:
        traces: A tuple of dictionaries for each trace to add to the plot, with keys
            for the col_name (in the dataframe), name (to use in legend) and colour.
        spacecrafts: A dictionary mapping spacecraft to plot colours.
        default_spacecraft: The spacecraft data to display as default.

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
            source = AjaxDataSource(
                data_url=f"/data/{trace['col_name']}/{spacecraft}",
                polling_interval=1000,
                method="GET",
            )

            plot.line(
                "date",
                "measurement",
                name=spacecraft,  # Enables selecting data in callback
                color=spacecrafts[spacecraft],
                source=source,
                legend_label=f"{spacecraft}: {trace['name']}",
                visible=True if spacecraft == default_spacecraft else False,
            )

    plot.legend.click_policy = "hide"
    plot.legend.location = "bottom_right"

    if plot.legend:
        legend = plot.legend[0]
        plot.add_layout(legend, "right")
        legend.click_policy = "hide"
        # hide legend items for hidden spacecraft line
        for item in legend.items:
            if item.renderers and not item.renderers[0].visible:
                item.visible = False
    return plot


def create_plots(
    button: CheckboxButtonGroup,
    spacecrafts: dict[str, str],
    default_spacecraft: str = "IMAP",
) -> list[figure]:
    """Create five plots to display solar weather data.

    Args:
        button: A checkbox button to select the spacecraft to display data for.
        spacecrafts: A dictionary mapping spacecraft to plot colours.
        default_spacecraft: The spacecraft data to display as default.

    Returns:
        A list containing the five Bokeh plots for each measurement.
    """
    plot_args = (
        (
            {"col_name": "bt", "name": "Bt", "unit": "nT"},
            {"col_name": "bz_gsm", "name": "Bz GSM", "unit": "nT"},
        ),
        (
            {
                "col_name": "lon_gsm",
                "name": "Phi GSM",
                "unit": "deg",
            },
        ),
        (
            {
                "col_name": "density",
                "name": "Density",
                "unit": "1/cm³",
            },
        ),
        (
            {
                "col_name": "speed",
                "name": "Speed",
                "unit": "km/s",
            },
        ),
        (
            {
                "col_name": "temperature",
                "name": "Temperature",
                "unit": "K",
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

    plots = []
    for traces in plot_args:
        plot = create_scatter_plot(traces, spacecrafts, default_spacecraft)
        plot.add_tools(hover)
        plot.add_tools(crosshair)
        # Display data for one spacecraft as default
        plot.select(name=default_spacecraft).visible = True  # type: ignore[attr-defined]
        add_callback_to_checkbox_button(plot=plot, button=button)
        plot.yaxis.axis_label = f"{traces[0]['name']} ({traces[0]['unit']})"
        plots.append(plot)

    return plots


def create_layout() -> Column:
    """Creates a layout object for the spacecraft data plots and widgets.

    Returns:
        A Column object containing the five Bokeh plots and widgets.
    """
    spacecrafts = {
        "IMAP": "red",
        "SO": "blue",
    }
    default_spacecraft = "IMAP"
    button = checkbox_button_group([craft for craft in spacecrafts], default_spacecraft)
    plots = create_plots(button, spacecrafts, default_spacecraft)
    layout = column([button, *plots], sizing_mode="stretch_width")

    return layout
