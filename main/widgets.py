"""Widgets for interacting with Bokeh plots."""

from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models.widgets.groups import CheckboxButtonGroup
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
    labels: list[str], default_spacecraft: str
) -> CheckboxButtonGroup:
    """Create CheckboxButtonGroup for selecting spacecraft data.

    Args:
        labels: A list of names for the spacecraft.
        default_spacecraft: The spacecraft data to display as default.

    Returns:
        A RadioButtonGroup widget for selecting the spacecraft.
    """
    default_idx = labels.index(default_spacecraft)
    button = CheckboxButtonGroup(labels=labels, active=[default_idx])
    return button


def add_callback_to_checkbox_button(
    plot: figure,
    button: CheckboxButtonGroup,
) -> None:
    """Enables the data in the plot to be updated depending on the checkbox button.

    Args:
        plot: A Bokeh figure for a timeseries plot.
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
