"""Task definitions for Huey."""

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
    times = (time - timedelta(days=7), time)

    static_data, trajectory_data = l1_data(times)
    data = {"static": static_data, "trajectory": trajectory_data}
    cache.set("l1_trajectory_data", data, timeout=None)

    # Record the time the data was generated
    cache.set("time_generated_l1", time, timeout=None)


def set_so_trajectory_cache() -> None:
    """Retrieves the most recent SO trajectory data and adds it to the cache.

    Creates the trajectory data for the Solar Orbiter plots and adds this to
    Django's cache, together with the time that the data were generated.
    """
    static_data, traj_data = {}, {}

    time = datetime.now()
    times = (time, time + timedelta(days=7))

    units = ["AU", "angle"]
    for unit in units:
        static_data[unit] = static_solar_orbiter_data(time, unit)
        traj_data[unit] = trajectory_solar_orbiter_data(times, unit)

    cache.set(
        "trajectory_data",
        {"static": static_data, "trajectory": traj_data},
        timeout=None,
    )

    # Record the time the data was generated
    cache.set("time_generated_so", time, timeout=None)
