"""Add tests for the ACE data retrieval functionality."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.conf import settings
from django.utils import timezone

from main import ace

RECENT_START = timezone.now() - timedelta(hours=1)
OLD_START = timezone.now() - timedelta(hours=3)


@pytest.mark.parametrize(
    "measurement, start, expected",
    [
        (
            "bx_gsm",
            RECENT_START,
            settings.URL_ACE.format(dataset="mag", period="2-hour"),
        ),
        ("bx_gsm", OLD_START, settings.URL_ACE.format(dataset="mag", period="7-day")),
        (
            "density",
            RECENT_START,
            settings.URL_ACE.format(dataset="plasma", period="2-hour"),
        ),
        (
            "density",
            OLD_START,
            settings.URL_ACE.format(dataset="plasma", period="7-day"),
        ),
        ("unknown", RECENT_START, ""),
    ],
)
def test_build_url(measurement, start, expected):
    """Test _build_url function."""
    assert ace._build_url(measurement, start) == expected


@pytest.fixture
def mock_ace_response():
    """Build a mock return value that mimics requests.get(...).json()."""
    mock_data = [
        ["time_tag", "density", "speed", "temperature"],
        ["2024-01-01T00:00:00Z", 15.2, 1013.1, 42],
        ["2024-01-01T01:00:00Z", 14.8, 1012.8, 43],
        ["2024-01-01T02:00:00Z", 14.5, 1012.5, 44],
    ]

    # Build the mock chain: requests.get(...).json()
    mock_response = MagicMock()
    mock_response.json.return_value = mock_data

    return mock_response, mock_data


@patch("requests.get")
def test_get_ace_data(mock_get: Mock, mock_ace_response):
    """Test the get_ace_data function."""
    import pandas as pd
    from django.core.cache import cache

    from main import ace

    mock_response, mock_data = mock_ace_response
    mock_get.return_value = mock_response

    # Use the last date of the mock response as "now"
    now = datetime.fromisoformat(mock_data[-1][0].replace("Z", "+00:00"))
    start = now - timedelta(days=7)
    from_date = int(start.timestamp()) * 1000

    # Simulate the code under test
    df = pd.DataFrame(mock_data[1:], columns=mock_data[0])
    url = ace._build_url("density", start)

    # Initially there is no cache
    assert cache.get(url) is None

    # Data is requested and cached
    ace.get_ace_data("density", from_date)
    mock_get.assert_called_once()
    assert all(cache.get(url) == df)

    # New requests of the same dataset do not result in a new request
    result = ace.get_ace_data("speed", from_date)
    mock_get.assert_called_once()

    # The output is the expected one
    assert set(["date", "measurement"]) == set(result.keys())
    assert df["speed"].to_list() == result["measurement"]
