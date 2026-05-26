"""Functions to pull data from HAPI servers."""

from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
import requests
from uplink import Consumer, QueryMap, get, returns

url = "https://www.ncei.noaa.gov/"


class HapiServer(Consumer):
    """Main client to interact with the UKWSI API."""

    @returns.json("data")
    @get("/cloud-access/space-weather-portal/api/v1/hapi/data")
    def data(self, **options: QueryMap) -> requests.Response:  # type: ignore [empty-body]
        """Gets information concerning a specific job ID."""

    @get("/cloud-access/space-weather-portal/api/v1/hapi/catalog")
    def catalog(self) -> requests.Response:  # type: ignore [empty-body]
        """Gets information concerning a specific job ID."""


def get_DSCOVR_data(measurement, from_date, reindex_data):
    """Retrieve DSCOVR data from HAPI server."""
    server = HapiServer(base_url=url)
    start = (
        datetime.fromtimestamp(int(from_date) / 1000, tz=UTC)
        .isoformat()
        .replace("+00:00", "Z")
    )
    stop = datetime.now().isoformat().replace("+00:00", "Z")
    dataset = "m1m_dscovr"

    if measurement not in ("bx_gse", "by_gse", "bz_gse", "phi_gse", "theta_gse"):
        return {"measurement": [], "date": []}

    parameters = f"time,{measurement}"
    response = server.data(
        dataset=dataset, start=start, stop=stop, parameters=parameters, format="json"
    )
    data = pd.DataFrame(response["data"], columns=["date", "measurement"])

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


def get_SOLAR_1_data(measurement, from_date, reindex_data):
    """Retrieve SOLAR-1 data from HAPI server."""
    server = HapiServer(base_url=url)
    start = (
        datetime.fromtimestamp(int(from_date) / 1000, tz=UTC)
        .isoformat()
        .replace("+00:00", "Z")
    )
    stop = datetime.now().isoformat().replace("+00:00", "Z")

    dataset = "sci_mag-l3_solar1"
    par_map = dict(bx_gse="b_gse_min_x", by_gse="b_gse_min_y", bz_gse="b_gse_min_z")

    if measurement not in par_map:
        return {"measurement": [], "date": []}

    parameters = f"time,{par_map[measurement]}"
    response = server.data(
        dataset=dataset, start=start, stop=stop, parameters=parameters, format="json"
    )
    data = pd.DataFrame(response["data"], columns=["date", "measurement"])

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


if __name__ == "__main__":
    dataset = "sci_mag-l3_solar1"
    start = int((datetime.now() - timedelta(days=7)).timestamp()) * 1000
    stop = "2026-05-18T23:59:00.000Z"
    parameters = "time,b_gse_min_x,b_gse_min_y,b_gse_min_z"
    fmt = "json"

    # server = HapiServer(base_url=url)
    # response = server.catalog()
    # print(response)
    # response = server.data(
    #     dataset=dataset, start=start, stop=stop, parameters=parameters, format=fmt
    # )
    # print(response)
    # colnames = [p["name"] for p in response["parameters"]]
    # df = pd.DataFrame(response["data"], columns=colnames).set_index("time")

    data = get_DSCOVR_data("bx_gse", start, "")
    print(data)
