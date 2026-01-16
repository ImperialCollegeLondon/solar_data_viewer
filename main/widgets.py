"""Widgets for interacting with Bokeh plots."""

from copy import deepcopy

from bokeh.models import ColumnDataSource, CustomJS, Dropdown, RadioButtonGroup
from bokeh.plotting import figure


def _copy_sources(sources: list[ColumnDataSource]) -> list[ColumnDataSource]:
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
    button = RadioButtonGroup(labels=labels, active=default_index, name="Test")
    return button


def dropdown_button(label: str, items: list[tuple[str, str]]) -> Dropdown:
    """Create a Dropdown button.

    Args:
        label: A label displayed on the dropdown button.
        items: A list of tuples containing each item's text and value name.

    Returns:
        A Dropdown button for selecting time ranges.
    """
    dropdown = Dropdown(label=label, menu=items, button_type="default")
    return dropdown


def add_callback_to_button(
    plot: figure, button: RadioButtonGroup, sources: list[ColumnDataSource]
) -> None:
    """Enables the data in the plot to be updated depending on the radio button.

    The data sources have to be copied to prevent modifying their underlying data
    when the button is clicked.

    Args:
        plot: A Bokeh figure for a scatter plot.
        button: A radio button to select the spacecraft to display data for.
        sources: A list of ColumnDataSources for the plots for each spacecraft.
    """
    callback = CustomJS(
        args=dict(
            plot=plot,
            button=button,
            sources=_copy_sources(sources),
        ),
        code="""const selection = button.active;
        const orig_source = plot.renderers[0].data_source;
        const new_source = sources[selection];

        const n = new_source.data.index.length;
        plot.x_range.start = new_source.data.index[0];

        plot.x_range.end = new_source.data.index[n-1];
        orig_source.data = new_source.data;""",
    )
    button.js_on_event("button_click", callback)
