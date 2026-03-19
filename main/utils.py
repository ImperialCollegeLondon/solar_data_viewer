"""General utilities for Solar Data Viewer."""

import tomllib
from logging import getLogger
from pathlib import Path
from typing import Any

import numpy as np
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
        measurement in ("bx_gse", "by_gse", "bz_gse", "phi_gse")
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
    delta = pd.Timedelta(range_param)
    df = df[df["date"] >= latest - delta]
    df = reindex_data(df)
    # Format datetime as Unix epoch time
    df.index = df.index.astype("int64") // 10**3

    # Create JSON response
    dates = df.index.tolist()
    measurements = df[measurement].tolist()
    data = {"measurement": measurements, "date": dates}
    return data


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
    if measurement not in ("bx_gse", "by_gse", "bz_gse", "phi_gse"):
        raise ValueError(
            "Only GSE magnetic field components can be retrieved by this function."
        )

    if spacecraft not in models.MAG_MODELS:
        raise ValueError(
            f"Only {list(models.MAG_MODELS.keys())} spacecrafts are supported."
        )

    # Get the time range to display
    delta = pd.Timedelta(range_param)
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
    if not len(data):
        return {"measurement": [], "date": []}

    # Do some post processing to sanitize the data
    data = data.rename(columns={data.columns[0]: "date"})
    data["date"] = pd.to_datetime(data["date"], utc=True)
    data = reindex_data(data)

    # Format datetime as Unix epoch time
    data.index = data.index.astype("int64") // 10**3

    # Create JSON response
    dates = data.index.tolist()
    measurements = data[measurement].tolist()
    return {"measurement": measurements, "date": dates}
