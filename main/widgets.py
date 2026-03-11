"""Widgets for interacting with Bokeh plots."""

from datetime import timedelta

from bokeh.models import (  # type: ignore
    CheckboxGroup,
    ColumnDataSource,
    CustomJS,
    Select,
)
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
    pass_checkbox: CheckboxGroup = None,
) -> None:
    """Enables the data in the plot to be updated depending on the checkbox button.

    Args:
        plot: A Bokeh figure for a timeseries plot.
        button: A checkbox button group to select the spacecraft to display data for.
        pass_checkbox: An optional CheckboxGroup to show/hide pass data when "SO"
                is selected.
    """
    legend = plot.legend[0] if isinstance(plot.legend, list) else plot.legend

    # add pass checkbox to args if it exists, so we can use it in the callback
    js_args = dict(button=button, legend=legend, plot=plot)
    if pass_checkbox:
        js_args["pass_checkbox"] = pass_checkbox

    callback = CustomJS(
        args=js_args,
        code="""
            const { active: selection, labels } = button;

            //  Check if "SO" is selected
            const so_index = labels.indexOf("SO");
            // Check if 'show pass data' is selected
            const is_so_active = so_index !== -1 && selection.includes(so_index);

            //  Hide or show 'Show Pass Data' checkbox based on whether "SO" is selected
            if (typeof pass_checkbox !== 'undefined') {
                pass_checkbox.visible = is_so_active;
            }

            // Hide or show the pass data strips on plots
            for (const renderer of plot.renderers) {
                if (renderer.name === "pass_data") {
                    const is_pass_ticked = (typeof pass_checkbox !== 'undefined')
                                            ? pass_checkbox.active.includes(0)
                                            : false;
                    renderer.visible = (is_so_active && is_pass_ticked);
                }
            }
            if (!legend.items) return;

            legend.items.forEach(item => {
                const renderer = item.renderers[0];
                if (!renderer) return;

                const index = labels.indexOf(renderer.name);
                if (index === -1) return;

                const visible = selection.includes(index);
                renderer.visible = visible;
                item.visible = visible;
            });
            """,
    )

    button.js_on_change("active", callback)


def create_time_range_dropdown() -> Select:
    """Create a dropdown Select widget for choosing the time range."""
    return Select(
        value="3d",
        options=[("1d", "1 Day"), ("3d", "3 Days"), ("7d", "7 Days")],
    )


def add_time_range_callback(dropdown: Select, plots: list[figure]) -> None:
    """Add a callback to the time range dropdown to update the data source URLs.

    Args:
        dropdown: A Select widget for choosing the time range.
        plots: A list of Bokeh figures to update when the time range changes.
    """
    time_ranges = {
        "1d": timedelta(days=1).total_seconds() * 1000,
        "3d": timedelta(days=3).total_seconds() * 1000,
        "7d": timedelta(days=7).total_seconds() * 1000,
    }

    x_range = plots[0].x_range

    callback = CustomJS(
        args=dict(
            dropdown=dropdown,
            plots=plots,
            x_range=x_range,
            range_map=time_ranges,
        ),
        code="""
        const range_selection = dropdown.value;
        const now = Date.now();
        const future_buffer = 24 * 60 * 60 * 1000;

        // x-axis range
        const duration = range_map[range_selection] || range_map["3d"];

        // shared x-axis
        x_range.end = now + future_buffer;
        x_range.start = now - duration;

        for (const plot of plots) {

            for (const renderer of plot.renderers) {

                // Update line
                if (renderer.name === "now_line") {
                    renderer.location = now;
                }

                // Update now label
                if (renderer.name === "now_label") {
                    renderer.x = now;
                }
            }

            for (const renderer of plot.renderers) {

                // Only update renderers that have an AjaxDataSource
                if (renderer.data_source && renderer.data_source.data_url) {
                    const source = renderer.data_source;
                    const url = new URL(source.data_url, window.location.origin);

                    url.searchParams.set("range", range_selection);
                    url.searchParams.set("_ts", now);
                    source.data_url = url.pathname + url.search;

                    // Force AjaxDataSource to fetch new data immediately
                    const original_interval = source.polling_interval;
                    // Pause regular polling while manually fetching new data
                    // to sync the manual fetching with the scheduled polling.
                    // Ensures we don't have overlapping requests
                    source.polling_interval = null;

                    // Fetch the new data from the backend
                    fetch(source.data_url)
                        .then(response => response.json())
                        .then(data => {
                            source.data = data;
                            source.change.emit();
                            source.polling_interval = original_interval;
                        })
                        .catch(err => {
                            source.polling_interval = original_interval;
                        });

                }
            }
        }
        """,
    )

    dropdown.js_on_change("value", callback)


def add_passes_checkbox(
    plots: list[figure], default_spacecraft: str = "IMAP"
) -> CheckboxGroup:
    """Create a Checkbox to show/hide passes on the plots.

    Args:
        plots: A list of Bokeh figures to add the pass data to.
        default_spacecraft: The spacecraft to show the pass data for by default.

    Returns:
        A CheckboxGroup widget to show/hide pass data.
    """
    pass_data_checkbox = CheckboxGroup(
        labels=["Show Pass Data"], active=[], visible=(default_spacecraft == "SO")
    )

    callback = CustomJS(
        args=dict(plots=plots),
        code="""
        const show_data = cb_obj.active.includes(0);

        for (const plot of plots) {

            for (const renderer of plot.renderers) {

                if (renderer.name === "pass_data") {
                    renderer.visible = show_data;

                    if (renderer.data_source && show_data) {
                        const source = renderer.data_source;
                        // Manual fetch for a one-time update
                        fetch(source.data_url)
                            .then(response => response.json())
                            .then(data => {
                                source.data = data;
                                source.change.emit();
                            });
                    }
                }
            }
        }
        """,
    )

    pass_data_checkbox.js_on_change("active", callback)

    return pass_data_checkbox
