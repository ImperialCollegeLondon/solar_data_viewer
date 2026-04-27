"""Test suite for cache."""

from datetime import datetime, timedelta
from unittest.mock import patch

from django.core.cache import cache


@patch("main.cache.static_solar_orbiter_data")
@patch("main.cache.trajectory_solar_orbiter_data")
@patch("main.cache.datetime")
def test_set_so_trajectory_cache(datetime_mock, traj_data_mock, static_data_mock):
    """Test the set_so_trajectory_cache function."""
    from main.cache import set_so_trajectory_cache

    time = datetime.now()
    times = (time - timedelta(days=7), time + timedelta(days=7))
    datetime_mock.now.return_value = time
    traj_data_mock.return_value = ("trajectory data", "arrow data")
    static_data_mock.return_value = "static data"

    expected_data = {
        "static": {"AU": "static data", "angle": "static data"},
        "trajectory": {"AU": "trajectory data", "angle": "trajectory data"},
        "arrow": {"AU": "arrow data", "angle": "arrow data"},
        "time": time,
    }

    cache.clear()
    set_so_trajectory_cache()

    for unit in ["AU", "angle"]:
        static_data_mock.assert_any_call(time, unit)
        traj_data_mock.assert_any_call(times, unit)

    cached_data = cache.get(f"trajectory_data-{time.strftime('%Y%m%d')}")
    assert cached_data == expected_data

    cache.clear()


@patch("main.cache.l1_data")
@patch("main.cache.datetime")
def test_set_l1_trajectory_cache(datetime_mock, l1_data_mock):
    """Test the set_l1_trajectory_cache function."""
    from main.cache import set_l1_trajectory_cache

    time = datetime.now()
    times = (time - timedelta(days=7), time + timedelta(days=7))
    datetime_mock.now.return_value = time
    l1_data_mock.return_value = ("static data", "trajectory data", "arrow data")

    expected_data = {
        "static": "static data",
        "trajectory": "trajectory data",
        "arrow": "arrow data",
        "time": time,
    }

    cache.clear()
    set_l1_trajectory_cache()

    l1_data_mock.assert_called_once_with(times)

    cached_data = cache.get(f"l1_trajectory_data-{time.strftime('%Y%m%d')}")
    assert cached_data == expected_data

    cache.clear()
