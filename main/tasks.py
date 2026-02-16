"""Task definitions for Huey."""

from datetime import datetime, timedelta

from django.core.cache import cache
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from .trajectory import static_solar_orbiter_data, trajectory_solar_orbiter_data


def set_trajectory_cache():
    """Retrieves the most recent trajectory data and adds it to the cache.

    Creates the trajectory data for the Solar Orbiter plots and adds this to
    Django's cache, together with the time that the data were generated.
    """
    trajectory_data = {"static": {}, "trajectory": {}}

    time = datetime.now()
    times = (time, time + timedelta(days=8))

    units = ["AU", "angle"]
    for unit in units:
        trajectory_data["static"][unit] = static_solar_orbiter_data(time, unit)
        trajectory_data["trajectory"][unit] = trajectory_solar_orbiter_data(times, unit)

    cache.set("trajectory_data", trajectory_data, timeout=None)

    # Record the time the data was generated
    cache.set("time_generated", time.strftime("%Y-%m-%d %H:%M:%S"))


@db_periodic_task(crontab(hour=10, minute=0))
def trajectory_cache_task():
    """Daily huey task to retrieve most recent trajectory data."""
    set_trajectory_cache()
