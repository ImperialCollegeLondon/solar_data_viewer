"""General utilities for Solar Data Viewer."""

import tomllib
from pathlib import Path
from typing import TypedDict

import numpy as np
import pandas as pd


class MeasurementConfig(TypedDict):
    """Configuration for measurement details."""

    label: str
    traces: dict[str, str]


class PlotConfig(TypedDict):
    """Configuration for plot details."""

    title: str
    unit: str
    measurements: dict[str, MeasurementConfig]


def load_plot_config(config_file: Path) -> tuple[list[PlotConfig], list[str], str]:
    """Load the config details for the plots from the TOML file.

    Returns:
        A tuple containing the plot config, the list of spacecrafts and
            the default spacecraft.
    """
    with open(config_file, "rb") as f:
        config = tomllib.load(f)

    plots_config = config["plots"]
    spacecrafts = config["spacecrafts"]["names"]
    default_spacecraft = config["spacecrafts"]["default"]
    return plots_config, spacecrafts, default_spacecraft


def process_data_from_test_csvs(
    spacecraft: str, measurement: str
) -> dict[str, list[str | float]]:
    """This is a placeholder function for returning processed test data from csvs.

    Args:
        spacecraft: Name of the spacecraft to retrieve data for.
        measurement: Name of the measurement to get data for.

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
    # Format datetime as Unix epoch time
    df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"], utc=True).astype("int64") // 10**6

    # Create JSON response
    dates = df["date"].tolist()
    measurements = df[measurement].tolist()
    data = {"measurement": measurements, "date": dates}
    return data
