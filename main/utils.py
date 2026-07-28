"""General utilities for Solar Data Viewer."""

import os
import tomllib
from datetime import UTC, date, datetime, timedelta
from logging import getLogger
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from django.db.models import Avg
from django.db.models.functions import TruncMinute
from django.template import Context, Template
from django.utils import timezone

from . import ace, hapi, models
from .config import L1Config, PlotsConfig

logger = getLogger("django")

IMAP_SWAPI_MEASUREMENTS = {
    "density": "proton_density",
    "speed": "proton_speed",
    "temperature": "proton_temperature",
}
"""Map generic measurement names to IMAP SWAPI model field names."""

BATCH_SIZE = 20000
"""Maximum numbers of data points to return per query.

This is used to avoid overloading the database and crashing the browser, as well as to
allow for a more responsive user experience."""


def load_plot_config(source: Path | dict[str, Any]) -> PlotsConfig:  # type: ignore[explicit-any]
    """Load the config details for the plots page from the TOML file.

    Args:
        source: The path or dictionary to load the config from.

    Returns:
        The validated config for the plots page.
    """
    if isinstance(source, Path):
        with open(source, "rb") as f:
            raw_config = tomllib.load(f)

    else:
        raw_config = source

    return PlotsConfig.model_validate(raw_config)


def load_l1_config(  # type: ignore[explicit-any]
    source: Path | dict[str, Any] = Path(__file__).parent / "config" / "l1_plot.toml",
) -> L1Config:
    """Load the config details for the L1 trajectory plot from the TOML file.

    Args:
        source: The path or dictionary to load the config from.

    Returns:
        The validated config for the L1 trajectory plot.
    """
    if isinstance(source, Path):
        with open(source, "rb") as f:
            raw_config = tomllib.load(f)

    else:
        raw_config = source

    return L1Config.model_validate(raw_config)


def reindex_data(df: pd.DataFrame, threshold: str = "1m") -> pd.DataFrame:
    """This function re-indexes a dataframe to add nans where there are large gaps.

    At gaps of >1 minute (as default), a new time point is added to the index within
    the gap. The resulting NaN values are converted to 'nan'.

    Args:
        df: The dataframe to reindex.
        threshold: The minimum threshold for a gap.

    Returns:
        A re-indexed data frame, where the dates are now the index column.
    """
    df = df.set_index("date").sort_index()
    index = df.index.copy()
    dt = index.to_series().diff()
    timestep = dt.min()

    # Check if min timestep is greater than threshold
    gap_threshold = pd.Timedelta(threshold)
    if timestep > gap_threshold:
        return df.replace({np.nan: "nan"})

    # Find gaps above specified threshold
    gaps = np.where(dt > gap_threshold)[0]
    # Insert new date (with NaN value) within gap
    new_dates = index[gaps - 1] + timestep
    new_index = df.index.append(new_dates).sort_values()
    df = df.reindex(new_index).replace({np.nan: "nan"})
    return df


def retrieve_data(
    spacecraft: str, measurement: str, from_date: int | None
) -> dict[str, list[float]]:
    """Selects between different retrieval functions, calls them and returns the data.

    Args:
        spacecraft: Name of the spacecraft to retrieve data for.
        measurement: Name of the measurement to get data for.
        from_date: The date to use as the starting point to get data (in ms format).
            If None, defaults to 7 days ago from the current time.

    Returns:
        A dictionary containing the relevant datetimes in UNIX epoch time format and
            the measurements to plot.
    """
    if from_date is None:
        from_date = int((timezone.now() - timedelta(days=7)).timestamp()) * 1000

    if (
        measurement in ("bx_gse", "by_gse", "bz_gse", "phi_gse", "theta_gse")
        and spacecraft in models.MAG_MODELS
    ):
        return get_gse_magnetic_field(spacecraft, measurement, from_date)

    if spacecraft == "IMAP" and measurement in IMAP_SWAPI_MEASUREMENTS:
        return get_imap_swapi_data(measurement, from_date)

    if spacecraft in hapi.SPACECRAFTS:
        return hapi.get_data_from_hapi(spacecraft, measurement, from_date)

    if spacecraft == "ACE":
        return ace.get_ace_data(measurement, from_date)

    return {"measurement": [], "date": []}


def get_pass_data(spacecraft: str) -> dict[str, list[float]]:
    """Read pass data from database.

    Args:
        spacecraft: Name of the spacecraft to retrieve data for.

    Returns:
        A dictionary containing the start and end datetimes in UNIX epoch
        time format (milliseconds) and the label text for Bokeh to plot.
    """
    from django.utils import timezone

    if spacecraft != "SO":
        return {
            "start_time": [],
            "end_time": [],
        }

    now = timezone.now()

    # Get the data from the DB
    data = pd.DataFrame(
        list(
            models.SOContactSchedule.objects.using("so")
            .filter(end_time__gte=now)  # only get future passes
            .order_by("start_time")
            .values("start_time", "end_time")
        )
    )

    if not len(data):
        return {"start_time": [], "end_time": []}

    # convert to Unix epoch milliseconds
    data["start_time"] = data["start_time"].apply(lambda x: int(x.timestamp() * 1000))
    data["end_time"] = data["end_time"].apply(lambda x: int(x.timestamp() * 1000))

    start_time_list = data["start_time"].tolist()
    end_time_list = data["end_time"].tolist()

    return {
        "start_time": start_time_list,
        "end_time": end_time_list,
        "label_text": [f"Pass {i + 1}" for i in range(len(start_time_list))],
    }


def get_gse_magnetic_field(
    spacecraft: str, measurement: str, from_date: int
) -> dict[str, list[float]]:
    """Retrieves a component of the magnetic field data for the SO and IMAP missions.

    Args:
        spacecraft: Name of the spacecraft to retrieve data for.
        measurement: Name of the measurement to get data for.
        from_date: The date to use as the starting point to get data (in ms format).

    Returns:
        A dictionary containing the relevant datetimes in UNIX epoch time format and
            the measurements to plot.
    """
    if measurement not in ("bx_gse", "by_gse", "bz_gse", "phi_gse", "theta_gse"):
        raise ValueError(
            "Only GSE magnetic field components can be retrieved by this function."
        )

    if spacecraft not in models.MAG_MODELS:
        raise ValueError(
            f"Only {list(models.MAG_MODELS.keys())} spacecrafts are supported."
        )

    # Get the relevant data from the DB
    most_recent = datetime.fromtimestamp(int(from_date) / 1000, tz=UTC)
    start_time = timezone.now()
    dataquery = (
        models.MAG_MODELS[spacecraft]  # type: ignore[attr-defined]
        .objects.filter(time__gt=most_recent)
        .annotate(date=TruncMinute("time"))
        .values("date")
        .annotate(average=Avg(measurement))
        .order_by("date")
    )
    data = pd.DataFrame(dataquery)
    logger.info(
        f"Querying {spacecraft} {measurement} data from the DB took "
        f"{(timezone.now() - start_time).total_seconds():.2f} seconds to retrieve "
        f"{len(data)} records. Start time is {most_recent}."
    )
    if not len(data):
        return {"measurement": [], "date": []}

    # Do some post processing to sanitize the data
    data["date"] = pd.to_datetime(data["date"], utc=True)
    data = reindex_data(data)

    # Format datetime as Unix epoch time
    data.index = data.index.astype("int64") // 10**3

    # Create JSON response
    dates = data.index.tolist()
    measurements = data["average"].tolist()
    return {"measurement": measurements, "date": dates}


def get_imap_swapi_data(measurement: str, from_date: int) -> dict[str, list[float]]:
    """Retrieves a component of the SWAPI data for the IMAP mission.

    Args:
        measurement: Name of the measurement to get data for - density, speed or
            temperature.
        from_date: The date to use as the starting point to get data (in ms format).

    Returns:
        A dictionary containing the relevant datetimes in UNIX epoch time format and
            the measurements to plot.
    """
    if measurement not in IMAP_SWAPI_MEASUREMENTS:
        raise ValueError(
            "Only IMAP SWAPI density, speed and temperature can be retrieved by "
            "this function."
        )

    measurement_field = IMAP_SWAPI_MEASUREMENTS[measurement]

    # Get the relevant data from the DB
    most_recent = datetime.fromtimestamp(int(from_date) / 1000, tz=UTC)
    start_time = timezone.now()
    dataquery = (
        models.IMAPSWAPI.objects.filter(time__gt=most_recent)
        .annotate(date=TruncMinute("time"))
        .values("date")
        .annotate(average=Avg(measurement_field))
        .order_by("date")
    )
    data = pd.DataFrame(list(dataquery))
    logger.info(
        f"Querying IMAP SWAPI {measurement} data from the DB took "
        f"{(timezone.now() - start_time).total_seconds():.2f} seconds to retrieve "
        f"{len(data)} records. Start time is {most_recent}."
    )
    if not len(data):
        return {"measurement": [], "date": []}

    data["date"] = pd.to_datetime(data["date"], utc=True)
    data = reindex_data(data)

    # Format datetime as Unix epoch time
    data.index = data.index.astype("int64") // 10**3

    # Create JSON response
    dates = [float(timestamp) for timestamp in data.index.tolist()]
    measurements = [
        float(value)
        for value in pd.to_numeric(data["average"], errors="coerce").tolist()
    ]
    return {"measurement": measurements, "date": dates}


def get_solar_orbiter_dates() -> list[tuple[date, date]]:
    """Get the dates Solar Orbiter is not in communication with Earth from file.

    Returns:
        A list of tuples of dates, representing periods where Solar Orbiter is not in
            communication with Earth.
    """
    dates_file = Path(__file__).parent / "data" / "solar_orbiter_dates.txt"
    so_dates = []
    with open(dates_file) as f:
        for line in f:
            start, end = line.strip().split(",")
            so_dates.append(
                (
                    datetime.strptime(start, "%Y-%m-%d").date(),
                    datetime.strptime(end, "%Y-%m-%d").date(),
                )
            )
    return so_dates


def get_message_template(end_date: str) -> str:
    """Get the formatted Solar Orbiter message template from file or default.

    Customized messages can be provided in main/data/solar_orbiter_message.txt.
    To include the end date for the superior conjunction window, use {{ end_date }}
    within the file text.

    Args:
        end_date: The end date (formatted) for the window that Solar Orbiter is not in
            communication.

    Returns:
        The rendered message template with the date added.
    """
    message = (
        "Until {{ end_date }}, Solar Orbiter is going through superior conjunction "
        "and will not be transmitting MAG data.\n"
        "Real-time MAG space weather data will continue after this date."
    )

    message_file = Path(__file__).parent / "data" / "solar_orbiter_message.txt"
    if os.path.exists(message_file):
        with open(message_file) as f:
            raw_message = f.read()
            if raw_message:
                message = raw_message

    message_template = Template(message)
    context = Context({"end_date": end_date})
    return message_template.render(context)
