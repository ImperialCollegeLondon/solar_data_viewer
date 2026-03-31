"""Functions for setting data in the cache."""

from datetime import datetime, timedelta

from django.core.cache import cache

from .trajectory import (
    l1_data,
    static_solar_orbiter_data,
    trajectory_solar_orbiter_data,
)


def set_l1_trajectory_cache() -> None:
    """Retrieves the most recent L1 trajectory data and adds it to the cache.

    Creates the trajectory data for the L1 plots and adds this to Django's cache.
    """
    time = datetime.now()
    times = (time - timedelta(days=7), time + timedelta(days=7))

    static_data, trajectory_data, arrow_data = l1_data(times)
    data = {
        "static": static_data,
        "trajectory": trajectory_data,
        "arrow": arrow_data,
        "time": time,
    }
    cache.set(f"l1_trajectory_data-{time.strftime('%Y%m%d')}", data, timeout=86400)


def set_so_trajectory_cache() -> None:
    """Retrieves the most recent SO trajectory data and adds it to the cache.

    Creates the trajectory data for the Solar Orbiter plots and adds this to
    Django's cache, together with the time that the data were generated.
    """
    static_data, traj_data, arrow_data = {}, {}, {}

    time = datetime.now()
    times = (time - timedelta(days=7), time + timedelta(days=7))

    units = ["AU", "angle"]
    for unit in units:
        static_data[unit] = static_solar_orbiter_data(time, unit)
        traj_data[unit], arrow_data[unit] = trajectory_solar_orbiter_data(times, unit)

    cache.set(
        f"trajectory_data-{time.strftime('%Y%m%d')}",
        {
            "static": static_data,
            "trajectory": traj_data,
            "arrow": arrow_data,
            "time": time,
        },
        timeout=86400,
    )
