"""General utilities for Solar Data Viewer."""

import tomllib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from django.utils import timezone

from . import models
from .config import PlotsConfig


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
    csv_files = {
        "IMAP": Path(__file__).parent / "data" / "test_data1.csv",
        "SO": Path(__file__).parent / "data" / "test_data2.csv",
    }

    df = pd.read_csv(csv_files[spacecraft], parse_dates=True)
    # Replace null values with nan to avoid Bokeh errors
    df = df.replace({np.nan: "nan"})

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

    # Format datetime as Unix epoch time
    df["date"] = df["date"].astype("int64") // 10**6

    # Create JSON response
    dates = df["date"].tolist()
    measurements = df[measurement].tolist()
    data = {"measurement": measurements, "date": dates}
    return data


def get_so_rtn_magnetic_field(
    measurement: str, range_param: str
) -> dict[str, list[float]]:
    """Retrieves the chosen component of the magnetic field data for the SO mission.

    Args:
        measurement: Name of the measurement to get data for.
        range_param: The time range for which to retrieve data.

    Returns:
        A dictionary containing the relevant datetimes in UNIX epoch time format and
            the measurements to plot.
    """
    if measurement not in ("B_r", "B_t", "B_n"):
        raise ValueError(
            "Only RTN magnetic field components can be retrieved by this function."
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
    data = pd.DataFrame(
        models.SORTNMagneticField.objects.filter(time__gte=from_date)
        .order_by("time")
        .values("time", measurement)
    )

    # Do some post processing to sanitize the data
    data = data.replace({np.nan: "nan"})
    data = data.rename(columns={data.columns[0]: "date"})
    data["date"] = pd.to_datetime(data["date"], utc=True)

    # Format datetime as Unix epoch time
    data["date"] = data["date"].astype("int64") // 10**6

    # Create JSON response
    dates = data["date"].tolist()
    measurements = data[measurement].tolist()
    return {"measurement": measurements, "date": dates}
