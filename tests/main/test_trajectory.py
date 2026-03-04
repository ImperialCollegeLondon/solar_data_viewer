"""Test suite for the trajectory plots."""

from datetime import datetime, timedelta
from unittest.mock import patch

import numpy as np
from astropy.coordinates import SkyCoord
from sunpy.coordinates.frames import HeliographicStonyhurst

from main.trajectory import (
    generate_solar_orbiter_statistics,
    get_earth_coordinates,
    get_JPL_spacecraft_coordinates,
    heliographic_to_cartesian,
    heliographic_to_earth_separation_angles,
)


def test_get_earth_coordinates():
    """Test the get_earth_coordinates function."""
    time = datetime.now()
    coord = get_earth_coordinates(time)
    assert isinstance(coord, HeliographicStonyhurst)

    times = [time + timedelta(days=i) for i in range(3)]
    coords = get_earth_coordinates(times)
    assert all(isinstance(coord, HeliographicStonyhurst) for coord in coords)


def test_get_JPL_spacecraft_coordinates():
    """Test the get_JPL_spacecraft_coordinates function."""
    # ACE id is -92
    time = datetime.now() - timedelta(days=1)
    coord = get_JPL_spacecraft_coordinates(-92, time)
    assert isinstance(coord, SkyCoord)

    times = (time, time + timedelta(days=3))
    coords = get_JPL_spacecraft_coordinates("DSCOVR", times)
    assert all(isinstance(coord, SkyCoord) for coord in coords)


def test_heliographic_to_cartesian():
    """Test the heliographic_to_cartesian function."""
    time = datetime.now()
    earth_coord = get_earth_coordinates(time)
    cart_coords = heliographic_to_cartesian(earth_coord)
    assert all(isinstance(coord, float) for coord in cart_coords)

    lon = earth_coord.lon.deg
    rad = earth_coord.radius.to_value("AU")
    theta = np.deg2rad(lon)

    assert cart_coords[0] == rad * np.cos(theta)
    assert cart_coords[1] == rad * np.sin(theta)


def test_heliographic_earth_separation_angles():
    """Test the heliographic_earth_separation_angles function."""
    time = datetime.now()
    earth_coord = get_earth_coordinates(time)
    coord = get_JPL_spacecraft_coordinates("IMAP", time)
    angles = heliographic_to_earth_separation_angles(coord, earth_coord)
    assert all(isinstance(angle, float) for angle in angles)
    assert angles[0] == coord.lon.deg - earth_coord.lon.deg
    assert angles[1] == coord.lat.deg - earth_coord.lat.deg


@patch("main.trajectory.get_earth_coordinates")
@patch("main.trajectory.get_JPL_spacecraft_coordinates")
@patch("main.trajectory.heliographic_to_earth_separation_angles")
@patch("main.trajectory.datetime")
def test_generate_solar_orbiter_statistics(
    datetime_mock, angles_mock, so_mock, earth_mock
):
    """Test the generate_solar_orbiter_statistics function."""
    earth_mock.return_value.radius.to_value.return_value = 1.0
    so_mock.return_value.radius.to_value.return_value = 0.2
    angles_mock.return_value = (10.0, 5.0)
    datetime_mock.now.return_value = datetime.now()

    stats = generate_solar_orbiter_statistics()
    assert stats["sun_earth_angle"] == 10
    assert stats["visibility"] == "GOOD"  # if > 5
    assert stats["dist_upstream_earth"] == 0.8  # 1 - 0.2
    assert stats["CME400time"] == round(0.8 * 150e6 / (400 * 3600))
    assert stats["CME1000time"] == round(0.8 * 150e6 / (1000 * 3600))
    assert stats["sun_spacecraft_distance"] == 0.2
    assert stats["lat_relative_to_earth"] == 5
    assert stats["lat_direction"] == "N"  # lat > 0
