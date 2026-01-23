"""Widgets for interacting with Bokeh plots."""

from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models.widgets.groups import CheckboxButtonGroup, RadioButtonGroup
from bokeh.plotting import figure


def _copy_sources(sources: list[ColumnDataSource]) -> list[ColumnDataSource]:
    """Create new ColumnDataSources so they are not overwritten later on.

    Args:
        sources: A list of ColumnDataSources for the plots for each spacecraft.

    Returns:
        A new list of ColumnDataSources.
    """
    return [ColumnDataSource(data=source.data) for source in sources]


def checkbox_button_group(
    labels: list[str], default_indexes: list[int] = [0]
) -> CheckboxButtonGroup:
    """Create CheckboxButtonGroup.

    Args:
        labels: A list of names for the spacecraft.
        default_indexes: A list of indexes for which spacecraft to show as default.

    Returns:
        A RadioButtonGroup widget for selecting the spacecraft.
    """
    button = CheckboxButtonGroup(labels=labels, active=default_indexes)
    return button


def add_callback_to_checkbox_button(
    plot: figure,
    button: CheckboxButtonGroup,
) -> None:
    """Enables the data in the plot to be updated depending on the checkbox button.

    Args:
        plot: A Bokeh figure for a scatter plot.
        button: A checkbox button group to select the spacecraft to display data for.
    """
    callback = CustomJS(
        args=dict(plot=plot, button=button),
        code="""const selection = button.active;

        plot.renderers.forEach((renderer) => {
            const name = renderer.name;
            const index = button.labels.indexOf(name);
            renderer.visible = selection.includes(index);
        })""",
    )
    button.js_on_event("button_click", callback)


def add_callback_to_button(
    plot: figure, button: RadioButtonGroup, sources: list[ColumnDataSource]
) -> None:
    """Enables the data in the plot to be updated depending on the radio button.

    The data sources have to be copied to prevent modifying their underlying data
    when the button is clicked. The x-range is also updated in case the date range
    is different.

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
