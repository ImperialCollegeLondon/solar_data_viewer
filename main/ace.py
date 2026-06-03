"""Functions to pull data from HAPI servers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from logging import getLogger

import numpy as np
import pandas as pd
import requests
from django.core.cache import cache
from django.utils import timezone

log = getLogger(__name__)

URL_ACE = "https://services.swpc.noaa.gov/products/solar-wind/{dataset}-{period}.json"
"""URL for retrieving ACE data. Needs to be completted with dataset and period."""


def _build_url(measurement: str, start: datetime) -> str:
    """Builds the url to retrieve ACE data.

    Args:
        measurement: The measurement of interest.
        start: First datetime to get the data for as a datetime object.

    Returns:
        The URL to retrieve the data from.
    """
    period = "2-hour" if (timezone.now() - start) <= timedelta(hours=2) else "7-day"

    options = {
        "mag": ["bx_gsm", "by_gsm", "bz_gsm"],
        "plasma": ["density", "speed", "temperature"],
    }
    for dataset, variables in options.items():
        if measurement in variables:
            return URL_ACE.format(dataset=dataset, period=period)

    log.warning(f"Unknown measurement name for ACE: {measurement}")
    return ""


def get_ace_data(measurement: str, from_date: int) -> dict[str, list[float]]:
    """Get the requested ACE measurement from the server.

    If there was cached data, that one is used to pull the data from. Otherwise, the
    data is pulled from the server and then cached for 5 min.

    Args:
        measurement: The measurement of interest.
        from_date: First datetime to get the data for as a timestamp.

    Returns:
        Dictionary with "date" and "measurement" keys, and each a list with the
        requested values. If no data is found, the lists are empty.
    """
    from .utils import reindex_data

    # ACE only provides data in GSM coordinates. For now, using GSM data as is
    # TODO: Make proper coordinate conversion
    measurement = measurement.replace("gse", "gsm")

    # We build the URL to retrieve the data from
    start = datetime.fromtimestamp(int(from_date) / 1000, tz=UTC)
    url = _build_url(measurement, start)
    if not url:
        return {"measurement": [], "date": []}

    data = cache.get(url)
    if data is None:
        response = requests.get(url).json()
        data = pd.DataFrame(data=response[1:], columns=response[0])
        cache.set(url, data, timeout=300)  # Cache for 300 s (5 min)

    # Pick the right columns and normalize their names
    data = data.loc[:, ["time_tag", measurement]]
    data = data.rename(columns={"time_tag": "date", measurement: "measurement"})

    # Select the right time range
    data["date"] = pd.to_datetime(data["date"], utc=True)
    data = data[data["date"] > start]

    # Do some post processing to sanitize the data
    data.loc[(data["measurement"].astype(float) < -999).values, "measurement"] = np.nan
    data = reindex_data(data)

    # Format datetime as Unix epoch time
    data.index = data.index.astype("int64") // 10**3

    # Create JSON response
    dates = data.index.tolist()
    measurements = data["measurement"].tolist()
    return {"measurement": measurements, "date": dates}
