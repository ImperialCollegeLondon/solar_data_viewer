"""Widgets for interacting with Bokeh plots."""

import pandas as pd
from bokeh.models import ColumnDataSource, CustomJS, Range1d
from bokeh.models.widgets.groups import RadioButtonGroup


def _copy_sources(sources: list[ColumnDataSource]) -> list[ColumnDataSource]:
    """Create new ColumnDataSources so they are not overwritten later on.

    Args:
        sources: A list of ColumnDataSources for the plots for each spacecraft.

    Returns:
        A new list of ColumnDataSources.
    """
    return [ColumnDataSource(data=dict(source.data)) for source in sources]


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
    spacecraft_button: RadioButtonGroup,
    time_callback: CustomJS,
    time_button: RadioButtonGroup,
    sources: list[ColumnDataSource],
    shared_source: ColumnDataSource,
) -> None:
    """Enables the data in the plot to be updated depending on the radio button.

    The data sources have to be copied to prevent modifying their underlying data
    when the button is clicked. The x-range is also updated in case the date range
    is different.

    Args:
        spacecraft_button: A radio button to select the spacecraft to display data for.
        time_callback: A CustomJS callback for updating the time range.
        time_button: A radio button for selecting the time range.
        sources: A list of ColumnDataSources for the plots for each spacecraft.
        shared_source: The shared ColumnDataSource used by the plots.
    """
    callback = CustomJS(
        args=dict(
            sources=_copy_sources(sources),
            shared_source=shared_source,
            time_callback=time_callback,
            time_button=time_button,
        ),
        code="""
        const selection = cb_obj.active;
        const new_source = sources[selection];

        shared_source.data = new_source.data;
        shared_source.change.emit();

        const times = new_source.data['index'];
        const new_end = times[times.length - 1];

        time_callback.args.df_end = new_end;

        const current_time_selection = time_button.active;

        time_callback.execute(time_button, {'active': current_time_selection});
        """,
    )
    spacecraft_button.js_on_change("active", callback)


def add_time_range_callback(
    x_range: Range1d, initial_df: pd.DataFrame
) -> tuple[RadioButtonGroup, CustomJS]:
    """Create the time-range selection widget (1 day, 3 days, 7 days).

    Args:
        x_range: The shared Range1d object used by the plots.
        initial_df: The DataFrame of the initially selected spacecraft, used
            to calculate the initial 'end' timestamp.

    Returns:
        A tuple containing:
            1. The RadioButtonGroup widget for time selection.
            2. The CustomJS callback attached to it (returned so it can be
               updated by the spacecraft selector later).
    """
    buttons = RadioButtonGroup(
        labels=["1 day", "3 days", "7 days"],
        active=1,
    )

    df_end = int(initial_df.index.max().timestamp() * 1000)

    # Set initial plot range to 3 days
    now = df_end
    start = now - 3 * 24 * 3600 * 1000
    x_range.start = start
    x_range.end = now

    callback = CustomJS(
        args=dict(
            xr=x_range,  # Act on the shared range
            df_end=df_end,  # This variable will be updated by the spacecraft button
        ),
        code="""
            const now = df_end;
            let start;

            switch (cb_obj.active) {
                case 0: start = now - 24*3600*1000; break;
                case 1: start = now - 3*24*3600*1000; break;
                case 2: start = now - 7*24*3600*1000; break;
                default: start = now - 3*24*3600*1000;
            }

            xr.start = start;
            xr.end = now;
        """,
    )

    buttons.js_on_change("active", callback)
    return buttons, callback
