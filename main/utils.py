"""General utilities for Solar Data Viewer."""

import tomllib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

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
    df["date"] = df["date"].astype("int64") // 10**3

    # Create JSON response
    dates = df["date"].tolist()
    measurements = df[measurement].tolist()
    data = {"measurement": measurements, "date": dates}
    return data


def process_pass_data_from_test_csvs(
    spacecraft: str, range_param: str
) -> dict[str, list[float]]:
    """Read pass data from csv files.

    Args:
        spacecraft: Name of the spacecraft to retrieve data for.
        range_param: The time range for which to retrieve data.

    Returns:
        A dictionary containing the start and end datetimes in UNIX epoch
        time format (milliseconds) for Bokeh to plot.
    """
    # for now we only want SO passes
    if spacecraft != "SO":
        return {
            "start_time": [],
            "end_time": [],
        }
    csv_file = Path(__file__).parent / "data" / f"passes_{spacecraft}.csv"

    df = pd.read_csv(csv_file)

    df = df.dropna(subset=["start_time", "end_time"])

    df["start_time"] = pd.to_datetime(df["start_time"], utc=True)
    df["end_time"] = pd.to_datetime(df["end_time"], utc=True)

    latest = pd.Timestamp.utcnow()
    ranges = {
        "1d": pd.Timedelta(days=1),
        "3d": pd.Timedelta(days=3),
        "7d": pd.Timedelta(days=7),
    }

    delta = ranges.get(range_param, pd.Timedelta(days=3))
    df = df[df["end_time"] >= latest - delta]

    df["start_time"] = df["start_time"].apply(lambda x: int(x.timestamp() * 1000))
    df["end_time"] = df["end_time"].apply(lambda x: int(x.timestamp() * 1000))

    return {
        "start_time": df["start_time"].tolist(),
        "end_time": df["end_time"].tolist(),
    }
