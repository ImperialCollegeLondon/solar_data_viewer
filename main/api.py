"""API module for the solar_data_viewer application."""

from django.http import HttpRequest
from ninja import Field, NinjaAPI, Path, Query, Schema, Status

from .utils import retrieve_batch_data, retrieve_data

api = NinjaAPI(title="Solar Data Viewer API docs")


class ScienceDataResponse(Schema):  # type: ignore[explicit-any]
    """Response schema for science data - mag or wind."""

    date: list[int] = Field(..., description="List of dates as timestamps in ms.")
    measurement: list[float] = Field(
        ..., description="Corresponding list of values for the requested measurement."
    )


class ErrorResponse(Schema):  # type: ignore[explicit-any]
    """Response in case of errors."""

    message: str = Field(
        ..., description="Explanation of what went wrong when retrieving the data."
    )


@api.get(
    "/data/field/{measurement}/{spacecraft}",
    response={200: ScienceDataResponse, 500: ErrorResponse},
)
def get_science_data(
    request: HttpRequest,
    measurement: str = Path(  # type: ignore[type-arg]
        ..., description="Name of the measurement of interest."
    ),
    spacecraft: str = Path(  # type: ignore[type-arg]
        ..., description="Name of the spacecraft to retrieve data for."
    ),
    from_date: int | None = Query(  # type: ignore[type-arg]
        None,
        description="The date to use as the starting point to get data (in ms format). "
        "If null, defaults to 7 days ago from the current time.",
    ),
) -> dict[str, list[float]] | Status[dict[str, str]]:
    """Get the science data - wind or mag - for the requested spacecraft."""
    error, data = retrieve_data(spacecraft.upper(), measurement, from_date)

    if error:
        return Status(500, {"message": error})

    return data


class ScienceMagDataResponse(Schema):  # type: ignore[explicit-any]
    """Response schema for mag science data."""

    date: list[int] = Field(..., description="List of dates as timestamps in ms.")
    bx_gsm: list[float] = Field(
        ..., description="X component of the magnetic field, in GSM coordinates."
    )
    by_gsm: list[float] = Field(
        ..., description="Y component of the magnetic field, in GSM coordinates."
    )
    bz_gsm: list[float] = Field(
        ..., description="Z component of the magnetic field, in GSM coordinates."
    )
    b_mag: list[float] = Field(..., description="Module of the magnetic field.")
    phi_gsm: list[float] = Field(
        ..., description="Phi angle of the magnetic field, in GSM coordinates."
    )
    theta_gsm: list[float] = Field(
        ..., description="Theta angle of the magnetic field, in GSM coordinates."
    )


class ScienceWindDataResponse(Schema):  # type: ignore[explicit-any]
    """Response schema for wind science data."""

    date: list[int] = Field(..., description="List of dates as timestamps in ms.")
    density: list[float] = Field(..., description="Density of the solar wind.")
    speed: list[float] = Field(..., description="Speed of the solar wind.")
    temperature: list[float] = Field(..., description="Temperature of the solar wind.")


@api.get(
    "/data/batch/mag/{spacecraft}",
    response={200: ScienceMagDataResponse, 500: ErrorResponse},
)
def get_mag_science_data(
    request: HttpRequest,
    spacecraft: str = Path(  # type: ignore[type-arg]
        ..., description="Name of the spacecraft to retrieve data for."
    ),
    from_date: int | None = Query(  # type: ignore[type-arg]
        None,
        description="The date to use as the starting point to get data (in ms format). "
        "If null, defaults to 7 days ago from the current time.",
    ),
) -> dict[str, list[int] | list[float | str | None]] | Status[dict[str, str]]:
    """Get all the mag science data for the requested spacecraft."""
    error, data = retrieve_batch_data(spacecraft.upper(), "mag", from_date)

    if error:
        return Status(500, {"message": error})

    return data


@api.get(
    "/data/batch/wind/{spacecraft}",
    response={200: ScienceWindDataResponse, 500: ErrorResponse},
)
def get_wind_science_data(
    request: HttpRequest,
    spacecraft: str = Path(  # type: ignore[type-arg]
        ..., description="Name of the spacecraft to retrieve data for."
    ),
    from_date: int | None = Query(  # type: ignore[type-arg]
        None,
        description="The date to use as the starting point to get data (in ms format). "
        "If null, defaults to 7 days ago from the current time.",
    ),
) -> dict[str, list[int] | list[float | str | None]] | Status[dict[str, str]]:
    """Get all the wind science data for the requested spacecraft."""
    error, data = retrieve_batch_data(spacecraft.upper(), "wind", from_date)

    if error:
        return Status(500, {"message": error})

    return data
