"""General utilities for Solar Data Viewer."""

import tomllib
from logging import getLogger
from pathlib import Path
from typing import Any

import pandas as pd
from django.utils import timezone

from . import models
from .config import PlotsConfig

logger = getLogger("django")


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


def get_data_as_segments(df: pd.DataFrame, measurement: str) -> dict:  # type: ignore
    """Find gaps in the data and split into segments.

    Args:
        df: Dataframe containing the measurements
        measurement: Name of the measurement to get data for.

    Returns:
        A dictionary containing the relevant datetimes in UNIX epoch time format and
            the measurements to plot.
    """
    df = df.set_index("date").sort_index()
    dt = df.index.to_series().diff()
    segment_ids = (dt > pd.Timedelta("1min")).cumsum()

    dates = []
    measurements = []

    for _, segment in df.groupby(segment_ids):
        segment = segment.dropna(subset=[measurement])

        if len(segment) > 1:
            # Convert to Unix
            dates_epoch = (segment.index.astype("int64") // 10**3).tolist()
            values = segment[measurement].astype(float).tolist()

            dates.append(dates_epoch)
            measurements.append(values)

    return {"measurement": list(measurements), "date": list(dates)}


def process_data_from_test_csvs(
    spacecraft: str, measurement: str, range_param: str
) -> dict[str, list[float]]:
    """This is a placeholder function for returning processed test data from csvs.

    Args:
        spacecraft: Name of the spacecraft to retrieve data for.
        measurement: Name of the measurement to get data for.
        range_param: The time range for which to retrieve data.

    Returns:
        A dictionary containing the relevant datetimes in UNIX epoch time format and
            the measurements to plot.
    """
    if (
        measurement in ("bx_gse", "by_gse", "bz_gse")
        and spacecraft in models.MAG_MODELS
    ):
        return get_gse_magnetic_field(spacecraft, measurement, range_param)

    csv_files = {
        "IMAP": Path(__file__).parent / "data" / "test_data1.csv",
        "SO": Path(__file__).parent / "data" / "test_data2.csv",
    }

    df = pd.read_csv(csv_files[spacecraft], parse_dates=True)

    df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"], utc=True)

    # Time range filtering
    latest = df["date"].max()
    ranges = {
        "1d": pd.Timedelta(days=1),
        "3d": pd.Timedelta(days=3),
        "7d": pd.Timedelta(days=7),
    }

    delta = ranges.get(range_param, pd.Timedelta(days=3))
    df = df[df["date"] >= latest - delta]

    df["date"] = pd.to_datetime(df["date"])

    # Split data in segments and return as dict
    data_dict = get_data_as_segments(df, measurement)

    return data_dict


def get_gse_magnetic_field(
    spacecraft: str, measurement: str, range_param: str
) -> dict[str, list[float]]:
    """Retrieves a component of the magnetic field data for the SO and IMAP missions.

    Args:
        spacecraft: Name of the spacecraft to retrieve data for.
        measurement: Name of the measurement to get data for.
        range_param: The time range for which to retrieve data.

    Returns:
        A dictionary containing the relevant datetimes in UNIX epoch time format and
            the measurements to plot.
    """
    if measurement not in ("bx_gse", "by_gse", "bz_gse"):
        raise ValueError(
            "Only GSE magnetic field components can be retrieved by this function."
        )

    if spacecraft not in models.MAG_MODELS:
        raise ValueError(
            f"Only {list(models.MAG_MODELS.keys())} spacecrafts are supported."
        )

    # Get the time range to display
    ranges = {
        "1d": pd.Timedelta(days=1),
        "3d": pd.Timedelta(days=3),
        "7d": pd.Timedelta(days=7),
    }
    delta = ranges.get(range_param, ranges["3d"])
    from_date = timezone.now() - delta

    # Get the relevant data from the DB
    start_time = timezone.now()
    data = pd.DataFrame(
        models.MAG_MODELS[spacecraft]  # type: ignore[attr-defined]
        .objects.filter(time__gte=from_date)
        .order_by("time")
        .values("time", measurement)
    )
    logger.info(
        f"Querying {spacecraft} {measurement} data from the DB took "
        f"{(timezone.now() - start_time).total_seconds():.2f} seconds to retrieve "
        f"{len(data)} records."
    )

    # Do some post processing to sanitize the data
    data = data.rename(columns={data.columns[0]: "date"})
    data["date"] = pd.to_datetime(data["date"], utc=True)

    # Split data in segments and return as dict
    data_dict = get_data_as_segments(data, measurement)
    return data_dict
