"""Widgets for interacting with Bokeh plots."""

from bokeh.models import ColumnDataSource, CustomJS, Dropdown
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
        sources: The full dataset for each spacecraft (stored in a list,
            never used directly by plots)
        shared_source: The single active dataset that all plots read from
            (updated when spacecraft or time range changes)
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
    """Add a time range callback to the plots.

    Args:
        plots: A list of Bokeh plots.
        df: The dataframe containing the data.

    Returns:
        A Dropdown and its associated CustomJS callback.
    """
    buttons = Dropdown(
        label="Time Range",
        menu=[
            ("1 Day", "1d"),
            ("3 Days", "3d"),
            ("7 Days", "7d"),
        ],
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

            switch (cb_obj.item) {
                case "1d": start = now - 24*3600*1000; break;
                case "3d": start = now - 3*24*3600*1000; break;
                case "7d": start = now - 7*24*3600*1000; break;
                default: start = now - 3*24*3600*1000;
            }

            for (let p of plots) {
                p.x_range.start = start;
                p.x_range.end = now;
            }
            console.log("Dropdown clicked:", cb_obj.item);
        """,
    )

    buttons.js_on_event("menu_item_click", callback)

    return buttons, callback
