"""Schema for the timeseries plots."""

from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator


class BaseConfig(BaseModel):
    """Base schema for all configuration models."""

    model_config = ConfigDict(extra="forbid", strict=True)
    """Pydantic configuration."""


class MeasurementConfig(BaseConfig):
    """Configuration schema for each measurement added to a timeseries plot."""

    label: str
    """The label to use in the legend for the measurement."""

    traces: dict[str, str]
    """A dictionary mapping the trace for each spacecraft to a Bokeh colour, e.g.
    {IMAP: 'blue', SO: 'red'}."""


class PlotConfig(BaseConfig):
    """Configuration schema for the timeseries plot."""

    title: str
    """The plot title."""

    unit: str
    """The unit to display in the y-axis."""

    measurements: dict[str, MeasurementConfig]
    """A dictionary mapping the measurement identifier (e.g. bx_gsm) to
    its configuration schema."""


class PlotsConfig(BaseConfig):
    """Configuration schema for the plots page."""

    spacecrafts: list[str]
    """The list of names of each spacecraft."""

    default_spacecraft: str
    """The spacecraft to display as default when the page is loaded."""

    plots: list[PlotConfig]
    """The list of plots to include on the page."""

    @model_validator(mode="after")
    def check_valid_spacecrafts(self) -> Self:
        """Check valid spacecraft names are provided."""
        # Check the default spacecraft is in the defined list
        if self.default_spacecraft not in self.spacecrafts:
            raise ValueError(
                f"Invalid default spacecraft provided: {self.default_spacecraft}."
            )

        # Check the names of spacecraft provided for each trace
        for plot in self.plots:
            for measurement_id, measurement in plot.measurements.items():
                invalid_spacecraft = [
                    craft
                    for craft in measurement.traces
                    if craft not in self.spacecrafts
                ]
                if invalid_spacecraft:
                    raise ValueError(
                        f"Invalid spacecraft(s) ({', '.join(invalid_spacecraft)}) "
                        f"provided for plot {plot.title} ({measurement_id})."
                    )

        return self
