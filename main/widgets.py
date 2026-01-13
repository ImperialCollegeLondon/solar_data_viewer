"""Widgets for interacting with Bokeh plots."""

from copy import deepcopy

from bokeh.models import ColumnDataSource, CustomJS, RadioButtonGroup
from bokeh.plotting import figure


def copy_sources(sources: list[ColumnDataSource]) -> list[ColumnDataSource]:
    """Copy the ColumnDataSource's so they are not overwritten later on.

    Args:
        sources: A list of ColumnDataSources for the plots for each spacecraft.

    Returns:
        A copied list of ColumnDataSources.
    """
    return [ColumnDataSource(data=deepcopy(source.data)) for source in sources]


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


def add_callback_to_button(
    plot: figure, button: RadioButtonGroup, sources: list[ColumnDataSource]
) -> None:
    """Enables the data in the plot to be updated depending on the radio button.

    Args:
        plot: A Bokeh figure for a scatter plot.
        button: A radio button to select the spacecraft to display data for.
        sources: A list of ColumnDataSources for the plots for each spacecraft.
    """
    callback = CustomJS(
        args=dict(
            plot=plot,
            button=button,
            sources=copy_sources(sources),
        ),
        code="""const selection = button.active;
        const orig_source = plot.renderers[0].data_source;
        const new_source = sources[selection];
        orig_source.data = new_source.data;""",
    )
    button.js_on_event("button_click", callback)
