"""Tests for the main module."""

from solar_data_viewer import __version__


def test_version():
    """Check that the version is acceptable."""
    assert isinstance(__version__, str)
