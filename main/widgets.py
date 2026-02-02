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
        plot: A Bokeh figure for a scatter plot.
        button: A checkbox button group to select the spacecraft to display data for.
    """
    legend = plot.legend[0] if isinstance(plot.legend, list) else plot.legend

    callback = CustomJS(
        args=dict(button=button, legend=legend),
        code="""
        const selection = button.active;
        const labels = button.labels;

        if (legend && legend.items) {

            legend.items.forEach((item) => {

                if (item.renderers.length > 0) {
                    const renderer = item.renderers[0];
                    const name = renderer.name;

                    // Find button index corresponding to this renderer's name
                    const index = labels.indexOf(name);

                    // if button found
                    if (index !== -1) {
                        const is_active = selection.includes(index);

                        // switch line visibility
                        renderer.visible = is_active;

                        // switch legend item visibility
                        item.visible = is_active;
                    }
                }
            });
        }
        """,
    )
    button.js_on_event("button_click", callback)
