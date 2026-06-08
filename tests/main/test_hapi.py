"""Tests for the HAPI interface."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest


@pytest.mark.parametrize(
    argnames=["spacecraft", "measurement", "dataset", "specific", "variables"],
    argvalues=[
        pytest.param(
            "DSCOVR",
            "density",
            "f1m_dscovr",
            "proton_density",
            ["time", "proton_density", "proton_speed", "proton_temperature"],
            id="Variable exist in spacecraft",
        ),
        pytest.param(
            "DSCOVR",
            "colour",
            "",
            "",
            [],
            id="Variable not in spacecraft",
        ),
        pytest.param(
            "Voyager II",
            "bx_gse",
            "",
            "",
            [],
            id="No spacecraft",
        ),
    ],
)
def test_get_dataset(spacecraft, measurement, dataset, specific, variables):
    """Test the get_dataset function."""
    from main import hapi

    adataset, aspecific, avariables = hapi._get_dataset(spacecraft, measurement)
    assert dataset == adataset
    assert aspecific == specific
    assert avariables == variables


@pytest.fixture
def mock_cols():
    """Define the columns used in the request and DataFrame."""
    return ["time", "proton_density", "proton_speed", "proton_temperature"]


@pytest.fixture
def mock_hapi_response():
    """Build a mock return value that mimics requests.get(...).json()["data"]."""
    mock_data = [
        ["2024-01-01T00:00:00Z", 15.2, 1013.1, 42],
        ["2024-01-01T01:00:00Z", 14.8, 1012.8, 43],
        ["2024-01-01T02:00:00Z", 14.5, 1012.5, 44],
    ]

    # Build the mock chain: requests.get(...).json() -> dict with "data" key
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": mock_data}

    return mock_response, mock_data


@patch("requests.get")
def test_get_data_from_hapi(mock_get: Mock, mock_hapi_response, mock_cols, caplog):
    """Test the get_data_from_hapi function."""
    import pandas as pd
    from django.core.cache import cache

    from main import hapi

    from_date = int((datetime.now() - timedelta(days=7)).timestamp()) * 1000
    mock_response, mock_data = mock_hapi_response
    mock_get.return_value = mock_response

    # Simulate the code under test
    df = pd.DataFrame(mock_data, columns=mock_cols)

    # Initially there is no cache
    assert cache.get("f1m_dscovr") is None

    # Data is requested and cached
    hapi.get_data_from_hapi("DSCOVR", "density", from_date)
    mock_get.assert_called_once()
    assert all(cache.get("f1m_dscovr") == df)

    # New requests of the same dataset do not result in a new request
    result = hapi.get_data_from_hapi("DSCOVR", "speed", from_date)
    mock_get.assert_called_once()

    # The output is the expected one
    assert set(["date", "measurement"]) == set(result.keys())
    assert df["proton_speed"].to_list() == result["measurement"]

    # If there is a problem pulling data, the error is handled
    mock_response.status_code = 300
    result = hapi.get_data_from_hapi("DSCOVR", "bx_gse", from_date)
    assert result == {"measurement": [], "date": []}
    assert caplog.records[-1].levelname == "ERROR"
    assert "DSCOVR" in caplog.records[-1].message
    assert "m1m_dscovr" in caplog.records[-1].message
