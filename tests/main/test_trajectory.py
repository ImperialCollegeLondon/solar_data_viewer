"""Test suite for the trajectory plots."""

from datetime import datetime, timedelta

import numpy as np
from astropy.coordinates import SkyCoord
from sunpy.coordinates.frames import HeliographicStonyhurst

from main.trajectory import (
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
