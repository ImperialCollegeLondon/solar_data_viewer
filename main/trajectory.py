"""Plots for displaying trajectory data."""

from datetime import datetime
from typing import cast

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from sunpy.coordinates import get_body_heliographic_stonyhurst, get_horizons_coord
from sunpy.coordinates.frames import GeocentricSolarEcliptic, HeliographicStonyhurst


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


def get_earth_coordinates(time: datetime) -> HeliographicStonyhurst:
    """Get the coordinates of the earth at a specific time.

    Args:
        time: A datetime to retrieve coordinates for.

    Returns:
        The coordinates of the Earth using the Stonyhurst Heliographic system.
    """
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
    unit: str,
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
    so = cast(SkyCoord, get_JPL_spacecraft_coordinates("Solar Orbiter", time))

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
    times: tuple[datetime, datetime],
    unit: str,
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


def get_visibility_status(angle: float) -> str:
    """Get the visibility status depending on the separation angle.

    Args:
        angle: The longitude separation angle from the Sun-Earth line.

    Returns:
        The visibility status.
    """
    if angle <= 5:
        status = "AMAZING"
    elif angle <= 10:
        status = "GOOD"
    elif angle <= 20:
        status = "USEFUL"
    elif angle <= 30:
        status = "POOR"
    else:
        status = "NOT USEFUL"
    return status


def generate_solar_orbiter_statistics() -> dict[str, str | float]:
    """Generate Solar Orbiter statistics to display in the dashboard.

    Returns:
        Dictionary containing statistics that can be accessed in the HTML
            template.
    """
    time = datetime.now()
    earth = get_earth_coordinates(time)
    so = cast(SkyCoord, get_JPL_spacecraft_coordinates("Solar Orbiter", time))

    # Angle from the Sun-Earth line
    angles = heliographic_to_earth_separation_angles(so, earth)
    sun_earth_angle = round(angles[0])

    # Visibility
    status = get_visibility_status(angles[0])

    # Distance upstream of Earth
    dist_upstream_earth = earth.radius.to_value("AU") - so.radius.to_value("AU")

    # CME warnings
    AU = 150e6
    CME400time = round(dist_upstream_earth * AU / (400 * 3600))
    CME1000time = round(dist_upstream_earth * AU / (1000 * 3600))

    # Sun-spacecraft distance
    sun_spacecraft_distance = round(so.radius.to_value("AU"), 1)

    # Latitude relative to Earth
    lat = round(abs(angles[1]))
    lat_dir = "S" if angles[1] < 0 else "N"

    data = {
        "sun_earth_angle": sun_earth_angle,
        "visibility": status,
        "dist_upstream_earth": round(dist_upstream_earth, 1),
        "CME400time": CME400time,
        "CME1000time": CME1000time,
        "sun_spacecraft_distance": sun_spacecraft_distance,
        "lat_relative_to_earth": lat,
        "lat_direction": lat_dir,
    }
    return data


def coord_to_gse(coord: SkyCoord) -> tuple[float, float]:
    """Convert a SkyCoord to GSE y and z-coordinates.

    Only y and z-coordinates are required for plotting.

    Returns:
        A tuple of the y and z GSE coordinates.
    """
    gse_coord = coord.transform_to(GeocentricSolarEcliptic)
    # Coords are given in Earth radii (u.R_earth)
    y = gse_coord.cartesian.y.to(u.R_earth).value
    z = gse_coord.cartesian.z.to(u.R_earth).value
    return y, z


def l1_data(
    times: tuple[datetime, datetime],
) -> tuple[dict[str, object], dict[str, object]]:
    """Get the data for the L1 spacecraft glyphs in GSE coordinates.

    Args:
        times: A datetime to retrieve coordinates for.

    Returns:
        A dictionary containing y and z-coordinates, spacecraft names
            and colours.
    """
    L1_IDS = [-43, -92, -8, -78, -231, -156]
    L1_CRAFTS = ["IMAP", "ACE", "WIND", "DSCOVR", "Solar-1", "Aditya-L1"]
    L1_COLOURS = [
        "rgb(255,143,0)",
        "rgb(204,0,204)",
        "rgb(0,204,204)",
        "rgb(0,102,204)",
        "rgb(230,0,0)",
        "rgb(19, 136, 8)",
    ]

    y_coords, z_coords = [], []
    for id in L1_IDS:
        trajectory = get_JPL_spacecraft_coordinates(id, times)
        gse_trajectory = [coord_to_gse(coord) for coord in trajectory]

        # Add to trajectory data
        y_coords.append([coord[0] for coord in gse_trajectory])
        z_coords.append([coord[1] for coord in gse_trajectory])

    static_data = {
        "name": L1_CRAFTS,
        "colour": L1_COLOURS,
        "y": [coords[-1] for coords in y_coords],
        "z": [coords[-1] for coords in z_coords],
    }

    trajectory_data = {
        "name": L1_CRAFTS,
        "colour": L1_COLOURS,
        "y": y_coords,
        "z": z_coords,
    }

    return static_data, trajectory_data
