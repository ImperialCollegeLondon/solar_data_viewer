"""Task definitions for Huey."""

from datetime import datetime, timedelta

from django.core.cache import cache
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

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

    static_data, trajectory_data, arrow_data = l1_data(times)
    data = {"static": static_data, "trajectory": trajectory_data, "arrow": arrow_data}
    cache.set("l1_trajectory_data", data, timeout=None)

    # Record the time the data was generated
    cache.set("time_generated_l1", time.strftime("%Y-%m-%d %H:%M:%S"))


def set_so_trajectory_cache() -> None:
    """Retrieves the most recent SO trajectory data and adds it to the cache.

    Creates the trajectory data for the Solar Orbiter plots and adds this to
    Django's cache, together with the time that the data were generated.
    """
    static_data, traj_data, arrow_data = {}, {}, {}

    time = datetime.now()
    times = (time, time + timedelta(days=7))

    units = ["AU", "angle"]
    for unit in units:
        static_data[unit] = static_solar_orbiter_data(time, unit)
        traj_data[unit], arrow_data[unit] = trajectory_solar_orbiter_data(times, unit)

    cache.set(
        "trajectory_data",
        {"static": static_data, "trajectory": traj_data, "arrow": arrow_data},
        timeout=None,
    )

    # Record the time the data was generated
    cache.set("time_generated_so", time.strftime("%Y-%m-%d %H:%M:%S"))


@db_periodic_task(crontab(hour=10, minute=0))
def trajectory_cache_task() -> None:
    """Daily huey task to retrieve most recent trajectory data."""
    set_so_trajectory_cache()
    set_l1_trajectory_cache()
