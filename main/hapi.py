"""Functions to pull data from HAPI servers."""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pandas as pd
import requests
from django.core.cache import cache
from django.utils import timezone

NOAA_HAPI_URL = (
    "https://www.ncei.noaa.gov/cloud-access/space-weather-portal/api/v1/hapi/data"
)
"""URL of the NOAA HAPI server."""

SPACECRAFTS = {
    "DSCOVR": {
        "f1m_dscovr": {
            "date": "time",
            "density": "proton_density",
            "speed": "proton_speed",
            "temperature": "proton_temperature",
        },
        "m1m_dscovr": {
            "date": "time",
            "bx_gse": "bx_gse",
            "by_gse": "by_gse",
            "bz_gse": "bz_gse",
            "phi_gse": "phi_gse",
            "theta_gse": "theta_gse",
        },
    },
    "SOLAR-1": {
        "sci_mag-l3_solar1": {
            "date": "time",
            "bx_gse": "b_gse_min_x",
            "by_gse": "b_gse_min_y",
            "bz_gse": "b_gse_min_z",
        },
    },
}
"""Name of the spacecrafts handled by the HAPI server."""


def _get_dataset(spacecraft: str, measurement: str) -> tuple[str, str, list[str]]:
    """Provide the dataset associated with each spacecraft.

    Args:
        spacecraft: The name of the spacecraft to get the dataset for.
        measurement: The generic measurement name.

    Return:
        The name of the associated dataset, the specific variable name that
        we are asking for and a list of all the variables in the dataset that we might
        want, so we pull them just once.
    """
    options = SPACECRAFTS.get(spacecraft)
    if not options:
        return "", "", []

    for dataset, var_map in options.items():
        if specific := var_map.get(measurement):
            return dataset, specific, list(var_map.values())

    return "", "", []


def get_data_from_hapi(
    spacecraft: str, measurement: str, from_date: int
) -> dict[str, list[float]]:
    """Return the data for the selected spacecraft, measurement and initial time.

    If there was cached data, that one is used to pull the data from. Otherwise, the
    data is pulled from the HAPI server and then cached for 5 min.

    Args:
        spacecraft: Name of the spacecraft to get the data for.
        measurement: The measurement of interest.
        from_date: First datetime to get the data for as a timestamp.

    Returns:
        Dictionary with "date" and "measurement" keys, and each a list with the
        requested values. If no data is found, the lists are empty.
    """
    from .utils import reindex_data

    dataset, variable, cols = _get_dataset(spacecraft, measurement)
    if not dataset:
        return {"measurement": [], "date": []}

    data = cache.get(dataset)
    if data is None:
        start = (
            datetime.fromtimestamp(int(from_date) / 1000, tz=UTC)
            .isoformat()
            .replace("+00:00", "Z")
        )
        stop = timezone.now().isoformat().replace("+00:00", "Z")
        data = requests.get(
            NOAA_HAPI_URL,
            params=dict(
                dataset=dataset,
                start=start,
                stop=stop,
                parameters=",".join(cols),
                format="json",
            ),
        ).json()["data"]
        data = pd.DataFrame(data, columns=cols)
        cache.set(dataset, data, timeout=300)  # Cache for 300 s (5 min)

    # Pick the right columns and normalize their names
    data = data.loc[:, ["time", variable]]
    data = data.rename(columns={"time": "date", variable: "measurement"})

    # Do some post processing to sanitize the data
    data["date"] = pd.to_datetime(data["date"], utc=True)
    data.loc[(data["measurement"] < -999).values, "measurement"] = np.nan
    data = reindex_data(data)

    # Format datetime as Unix epoch time
    data.index = data.index.astype("int64") // 10**3

    # Create JSON response
    dates = data.index.tolist()
    measurements = data["measurement"].tolist()
    return {"measurement": measurements, "date": dates}
