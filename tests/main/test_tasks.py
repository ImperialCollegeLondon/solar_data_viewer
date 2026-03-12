"""Test suite for tasks."""

from datetime import datetime, timedelta
from unittest.mock import patch

from django.core.cache import cache


@patch("main.tasks.static_solar_orbiter_data")
@patch("main.tasks.trajectory_solar_orbiter_data")
@patch("main.tasks.datetime")
def test_set_so_trajectory_cache(datetime_mock, traj_data_mock, static_data_mock):
    """Test the set_so_trajectory_cache function."""
    from main.tasks import set_so_trajectory_cache

    time = datetime.now()
    times = (time, time + timedelta(days=8))
    datetime_mock.now.return_value = time
    traj_data_mock.return_value = "trajectory data"
    static_data_mock.return_value = "static data"

    expected_data = {
        "static": {"AU": "static data", "angle": "static data"},
        "trajectory": {"AU": "trajectory data", "angle": "trajectory data"},
    }

    cache.clear()
    set_so_trajectory_cache()

    for unit in ["AU", "angle"]:
        static_data_mock.assert_any_call(time, unit)
        traj_data_mock.assert_any_call(times, unit)

    cached_data = cache.get("trajectory_data")
    assert cached_data == expected_data

    time_gen = cache.get("time_generated_so")
    assert time_gen == time.strftime("%Y-%m-%d %H:%M:%S")

    cache.clear()


@patch("main.tasks.l1_data")
@patch("main.tasks.datetime")
def test_set_l1_trajectory_cache(datetime_mock, l1_data_mock):
    """Test the set_l1_trajectory_cache function."""
    from main.tasks import set_l1_trajectory_cache

    time = datetime.now()
    times = (time - timedelta(days=8), time)
    datetime_mock.now.return_value = time
    l1_data_mock.return_value = ("static data", "trajectory data")

    expected_data = {"static": "static data", "trajectory": "trajectory data"}

    cache.clear()
    set_l1_trajectory_cache()

    l1_data_mock.assert_called_once_with(times)

    cached_data = cache.get("l1_trajectory_data")
    assert cached_data == expected_data

    time_gen = cache.get("time_generated_l1")
    assert time_gen == time.strftime("%Y-%m-%d %H:%M:%S")

    cache.clear()
