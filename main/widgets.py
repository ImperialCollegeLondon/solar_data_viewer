"""Widgets for interacting with Bokeh plots."""

from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models.widgets.groups import RadioButtonGroup
from bokeh.plotting import figure


def _copy_sources(sources: list[ColumnDataSource]) -> list[ColumnDataSource]:
    """Create new ColumnDataSources so they are not overwritten later on.

    Args:
        sources: A list of ColumnDataSources for the plots for each spacecraft.

    Returns:
        A new list of ColumnDataSources.
    """
    return [ColumnDataSource(data=source.data) for source in sources]


def radio_button(labels: list[str], default_index: int) -> RadioButtonGroup:
    """Create RadioButtonGroup.

    Args:
        labels: A list of names for the spacecraft.
        default_index: The index for which spacecraft data to display as default.

    Returns:
        A RadioButtonGroup widget for selecting the spacecraft.
    """
    button = RadioButtonGroup(labels=labels, active=default_index)
    return button


def add_callback_to_spacecraft_button(
    plots: figure,
    button: RadioButtonGroup,
    time_callback: CustomJS,
    sources: list[ColumnDataSource],
) -> None:
    """Enables the data in the plot to be updated depending on the radio button.

    The data sources have to be copied to prevent modifying their underlying data
    when the button is clicked. The x-range is also updated in case the date range
    is different.

    Args:
        plots: A Bokeh figure for a scatter plot.
        button: A radio button to select the spacecraft to display data for.
        time_callback: The callback to update the time range.
        sources: A list of ColumnDataSources for the plots for each spacecraft.
    """
    callback = CustomJS(
        args=dict(
            plots=plots,
            button=button,
            time_callback=time_callback,
            sources=_copy_sources(sources),
        ),
        code="""const selection = button.active;
        const orig_source = plots.renderers[0].data_source;
        const new_source = sources[selection];

        const n = new_source.data.index.length;
        for (let p of plots) {
            p.x_range.start = new_source.data.index[0];
            p.x_range.end = new_source.data.index[n-1];

        orig_source.data = new_source.data;""",
    )
    button.js_on_event("button_click", callback)


def add_spacecraft_callback(
    plots: list[figure],
    spacecraft_button: RadioButtonGroup,
    time_button: RadioButtonGroup,
    time_callback: CustomJS,
    sources: list[ColumnDataSource],
    shared_source: ColumnDataSource,
) -> CustomJS:
    """Enables the data in the plot to be updated depending on the radio button.

    The data sources have to be copied to prevent modifying their underlying data
    when the button is clicked. The x-range is also updated in case the date range
    is different.

    Args:
        plots: The list of Bokeh plots.
        spacecraft_button: A radio button to select the spacecraft to display data for.
        time_button: A radio button to select the time range to display data for.
        time_callback: The callback to update the time range.
        sources: A list of ColumnDataSources for the plots for each spacecraft.
        shared_source: The data source used by all plots. This is overwritten with
        the selected spacecrafts data.
    """
    callback = CustomJS(
        args=dict(
            plots=plots,
            spacecraft_button=spacecraft_button,
            shared_source=shared_source,
            sources=sources,
            time_callback=time_callback,
            time_button=time_button,
        ),
        code="""
        const selection = spacecraft_button.active;
        const new_source = sources[selection];

        shared_source.data = new_source.data;

        const xs = new_source.data.index;
        const start = xs[0];
        const end   = xs[xs.length - 1];

        for (let p of plots) {
            p.x_range.start = start;
            p.x_range.end   = end;
        }

        time_callback.args.df_start = start;
        time_callback.args.df_end   = end;

        // Re-apply the currently selected time window
        const active = time_button.active;
        time_callback.execute(time_button, {active: active});
        """,
    )

    return callback


def add_time_range_callback(plots, df):
    """Adds a time range callback to the plots.

    Args:
        plots: A list of Bokeh plots.
        df: The dataframe containing the data.

    Returns:
        A RadioButtonGroup and its associated CustomJS callback.
    """
    buttons = RadioButtonGroup(
        labels=["1 day", "3 days", "7 days"],
        active=1,
    )
    df_start = int(df.index.min().timestamp() * 1000)
    df_end = int(df.index.max().timestamp() * 1000)

    callback = CustomJS(
        args=dict(
            plots=plots,
            df_start=df_start,
            df_end=df_end,
        ),
        code="""
            const xs = plots[0].renderers[0].data_source.data.index;

            const now = xs[xs.length - 1];
            let start;

            switch (cb_obj.active) {
                case 0: start = now - 24*3600*1000; break;
                case 1: start = now - 3*24*3600*1000; break;
                case 2: start = now - 7*24*3600*1000; break;
                default: start = now - 3*24*3600*1000;
            }

            for (let p of plots) {
                p.x_range.start = start;
                p.x_range.end = now;
            }
        """,
    )

    buttons.js_on_change("active", callback)
    return buttons, callback


def bind_spacecraft_callback(plot, spacecraft_button, time_callback, sources):
    """Bind the spacecraft callback to the plot."""
    add_callback_to_spacecraft_button(plot, spacecraft_button, time_callback, sources)
