"""API module for the solar_data_viewer application."""

from ninja import Field, NinjaAPI, Path, Query, Schema, Status

from .utils import retrieve_data

api = NinjaAPI(title="Solar Data Viewer API docs")


class ScienceDataResponse(Schema):
    """Response schema for science data - mag or wind."""

    date: list[int] = Field(..., description="List of dates as timestamps in ms.")
    measurement: list[float] = Field(
        ..., description="Corresponding list of values for the requested measurement."
    )


class ErrorResponse(Schema):
    """Response in case of errors."""

    message: str = Field(
        ..., description="Explanation of what went wrong when retrieving the data."
    )


@api.get(
    "/data/{measurement}/{spacecraft}",
    response={200: ScienceDataResponse, 500: ErrorResponse},
)
def get_science_data(
    request,
    measurement: str = Path(..., description="Name of the measurement of interest."),
    spacecraft: str = Path(
        ..., description="Name of the spacecraft to retrieve data for."
    ),
    from_date: int | None = Query(
        None,
        description="The date to use as the starting point to get data (in ms format). "
        "If null, defaults to 7 days ago from the current time.",
    ),
):
    """Get the science data - wind or mag - for the requested spacecraft."""
    error, data = retrieve_data(spacecraft.upper(), measurement, from_date)

    if error:
        return Status(500, {"message": error})

    return data
