"""Plots for displaying trajectory data."""

from datetime import datetime
from typing import Any, Literal

import numpy as np
from astropy.coordinates import SkyCoord
from bokeh.layouts import row
from bokeh.models import AjaxDataSource, HoverTool
from bokeh.models.layouts import Row
from bokeh.plotting import figure
from sunpy.coordinates import get_body_heliographic_stonyhurst, get_horizons_coord
from sunpy.coordinates.frames import HeliographicStonyhurst


def heliographic_to_cartesian(
    coord: HeliographicStonyhurst | SkyCoord,
) -> tuple[float, float]:
    """Convert the heliographic or SkyCoord coordinates to cartesian in AU.

    Args:
        coord: The HeliographicStonyhurst or SkyCoord coordinate.

    Returns:
        The x- and y-coordinates, representing the AU.
    """
    lon = coord.lon.deg
    rad = coord.radius.to_value("AU")
    theta = np.deg2rad(lon)

    return rad * np.cos(theta), rad * np.sin(theta)


def heliographic_to_earth_separation_angles(
    coord: SkyCoord, earth: HeliographicStonyhurst
) -> tuple[float, float]:
    """Compute the longitude and latitude separation angles from Earth.

    Args:
        coord: The coordinate to convert (i.e. of a spacecraft).
        earth: The HeliographicStonyhurst coordinate of the earth.

    Returns:
        The x- and y-coordinates, representing the longitude separation (deg) and
            latitude separation (deg), respectively.
    """
    return coord.lon.deg - earth.lon.deg, coord.lat.deg - earth.lat.deg


def get_earth_coordinates(
    time: datetime | list[datetime],
) -> HeliographicStonyhurst:
    """Get the coordinates of the earth at a specific time.

    Args:
        time: A datetime or list of datetimes to retrieve coordinates for.

    Returns:
        The coordinate or list of coordinates of the Earth using the Stonyhurst
            Heliographic system.
    """
    if isinstance(time, list):
        return [get_body_heliographic_stonyhurst("Earth", t) for t in time]
    else:
        return get_body_heliographic_stonyhurst("Earth", time)


def get_JPL_spacecraft_coordinates(
    spacecraft: str | int, time: datetime | list[datetime]
) -> SkyCoord | list[SkyCoord]:
    """Get the coordinate(s) of a spacecraft by querying JPL horizons.

    Args:
        spacecraft: The name or numerical identifier for the spacecraft.
        time: A datetime or list of datetimes to retrieve coordinates for.

    Returns:
        The coordinate or list of coordinates as Astropy SkyCoord(s).
    """
    if isinstance(time, list):
        return [get_horizons_coord(spacecraft, t) for t in time]
    else:
        return get_horizons_coord(spacecraft, time)


def static_solar_orbiter_data(time: datetime, unit: str) -> dict[str, Any]:  # type: ignore[explicit-any]
    """Get the data for the static Solar Orbiter glyphs.

    Args:
        time: A datetime to retrieve coordinates for.
        unit: The units on the plot, either AU (astronomical units) or angles
            (Earth separation angles).

    Returns:
        A data dictionary to be used by the data source.
    """
    # Get coordinates of Earth and Solar Orbiter
    earth = get_body_heliographic_stonyhurst("Earth", time)

    # Get coordinates of Solar Orbiter
    so = get_JPL_spacecraft_coordinates("Solar Orbiter", time)

    if unit == "AU":
        # Convert to Cartesian coordinates
        so_x, so_y = heliographic_to_cartesian(so)
        earth_x, earth_y = heliographic_to_cartesian(earth)

        return {
            "name": ["Sun", "Solar Orbiter", "Earth"],
            "x": [0.0, so_x, earth_x],
            "y": [0.0, so_y, earth_y],
            "colour": ["orange", "blue", "green"],
        }

    # Calculate separation angle using Earth coord
    so_x, so_y = heliographic_to_earth_separation_angles(so, earth)

    return {
        "name": ["Sun", "Solar Orbiter"],
        "x": [0.0, so_x],
        "y": [0.0, so_y],
        "colour": ["orange", "blue"],
    }


def trajectory_solar_orbiter_data(
    times: list[datetime], unit: str
) -> dict[str, list[float]]:
    """Get the data for the trajectory Solar Orbiter glyphs.

    Args:
        times: A list of datetimes to retrieve coordinates for.
        unit: The units on the plot, either AU (astronomical units) or angles
            (Earth separation angles).

    Returns:
        A data dictionary to be used by the data source.
    """
    # Get trajectory coords
    trajectory = get_JPL_spacecraft_coordinates("Solar Orbiter", times)

    # Convert coords
    if unit == "AU":
        coords = [heliographic_to_cartesian(coord) for coord in trajectory]

    else:
        earth = get_body_heliographic_stonyhurst("Earth", times[0])
        coords = [
            heliographic_to_earth_separation_angles(coord, earth)
            for coord in trajectory
        ]

    return {"x": [coord[0] for coord in coords], "y": [coord[1] for coord in coords]}


def solar_orbiter_plot(
    title: str,
    x_axis_label: str,
    y_axis_label: str,
    unit: Literal["AU", "angle"],
    radii: list[float],
) -> figure:
    """Create the Solar Orbiter plot using the fixed Earth frame.

    Returns:
        A Bokeh figure containing the trajectory of Solar Orbiter in the fixed
            Earth frame.
    """
    plot = figure(  # type: ignore[call-arg]
        title=title,
        width=600,
        height=600,
        match_aspect=True,
        x_axis_label=x_axis_label,
        y_axis_label=y_axis_label,
    )

    # Create an AjaxDataSource for the spacecraft static position
    static_source = AjaxDataSource(
        data_url=f"/trajectory_data/{unit}/static",
        polling_interval=None,
        method="GET",
    )
    objects = plot.scatter(
        "x", "y", color="colour", legend_field="name", size=15, source=static_source
    )

    # Create an AjaxDataSource for the trajectory data
    trajectory_source = AjaxDataSource(
        data_url=f"/trajectory_data/{unit}/trajectory",
        polling_interval=None,
        method="GET",
    )
    plot.line(
        "x", "y", color="blue", source=trajectory_source, legend_label="Next 7 days"
    )

    for r in radii:
        plot.circle(
            x=0,
            y=0,
            radius=r,
            fill_alpha=0,
            line_color="gray",
            line_dash="dotted",
            line_width=1,
        )
    hover = HoverTool(tooltips=[("ID", "@name")], renderers=[objects])
    plot.add_tools(hover)

    return plot


def create_solar_orbiter_layout() -> Row:
    """Create a layout object for the Solar Orbiter trajectory plots.

    Returns:
        A Row object containing the two Bokeh plots.
    """
    layout = row(
        [
            solar_orbiter_plot(
                title="Fixed Earth frame",
                x_axis_label="AU",
                y_axis_label="AU",
                unit="AU",
                radii=[0.5, 0.75, 1.0],
            ),
            solar_orbiter_plot(
                title="Earth-Sun-spacecraft angle",
                x_axis_label="Longitude separation (deg)",
                y_axis_label="Latitude separation (deg)",
                unit="angle",
                radii=[10, 20],
            ),
        ]
    )
    return layout
