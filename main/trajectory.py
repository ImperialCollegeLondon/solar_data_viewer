"""Plots for displaying trajectory data."""

from datetime import datetime
from typing import Literal

import numpy as np
from astropy.coordinates import SkyCoord
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
    spacecraft: str | int, time: datetime | tuple[datetime, datetime]
) -> SkyCoord | list[SkyCoord]:
    """Get the coordinate(s) of a spacecraft by querying JPL horizons.

    Args:
        spacecraft: The name or numerical identifier for the spacecraft.
        time: A datetime or tuple of start and end datetimes to retrieve
            coordinates for.

    Returns:
        The coordinate or list of coordinates as Astropy SkyCoord(s).
    """
    if isinstance(time, tuple):
        return get_horizons_coord(
            spacecraft, {"start": time[0], "stop": time[-1], "step": "1d"}
        )
    else:
        return get_horizons_coord(spacecraft, time)


def static_solar_orbiter_data(
    time: datetime,
    unit: Literal["AU", "angle"],
) -> dict[str, list[str | float]]:
    """Get the data for the static Solar Orbiter glyphs.

    Args:
        time: A datetime to retrieve coordinates for.
        unit: The units on the plot, either AU (astronomical units) or angle
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
    times: list[datetime],
    unit: Literal["AU", "angle"],
) -> dict[str, list[float]]:
    """Get the data for the trajectory Solar Orbiter glyphs.

    Args:
        times: A list of datetimes to retrieve coordinates for.
        unit: The units on the plot, either AU (astronomical units) or angle
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
