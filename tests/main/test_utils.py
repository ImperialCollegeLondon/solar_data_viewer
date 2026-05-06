"""Test suite for the utils."""

import itertools
from contextlib import nullcontext as does_not_raise
from datetime import date, datetime, timedelta
from unittest.mock import mock_open, patch

import pandas as pd
import pytest
from model_bakery import baker

from main.config import PlotsConfig
from main.utils import (
    get_message_template,
    get_solar_orbiter_dates,
    load_plot_config,
    reindex_data,
)


def test_load_plot_config(plots_config):
    """Test the load_plot_config method."""
    config = load_plot_config(plots_config)
    assert isinstance(config, PlotsConfig)


@pytest.mark.parametrize("spacecraft", ["IMAP", "SO"])
@pytest.mark.parametrize(
    "measurement, raises",
    [
        ("bx_gse", does_not_raise()),
        ("by_gse", does_not_raise()),
        ("bz_gse", does_not_raise()),
        ("phi_gse", does_not_raise()),
        ("theta_gse", does_not_raise()),
        ("temperature", pytest.raises(ValueError)),
    ],
)
@pytest.mark.parametrize("days", [1, 3, 7])
@pytest.mark.django_db(databases=["imap", "so"])
def test_get_gse_magnetic_field(spacecraft, measurement, raises, days):
    """Test the get_gse_magnetic_field function."""
    import pandas as pd
    from django.utils import timezone

    from main.models import MAG_MODELS
    from main.utils import get_gse_magnetic_field

    model = MAG_MODELS[spacecraft]
    # Prepare the times
    num = days * 24
    now = timezone.now()
    times = (
        pd.date_range(start=now - pd.Timedelta(days=10), end=now, freq="h")
        .round("min")
        .to_series()
    )
    from_date = int((now - pd.Timedelta(days=days)).timestamp()) * 1000

    # Populate the database
    baker.make(model, time=itertools.cycle(times), _quantity=len(times))

    # Find the actual and expected values
    with raises:
        actual = get_gse_magnetic_field(spacecraft, measurement, from_date=from_date)
        expected_meas = list(
            model.objects.filter(time__in=times[-num:]).values_list(
                measurement, flat=True
            )
        )
        expected_dates = (times[-num:].astype("int64") // 10**3).to_list()

        assert list(actual.keys()) == ["measurement", "date"]
        assert len(actual["measurement"]) == num
        assert len(actual["date"]) == num
        assert expected_dates == actual["date"]
        assert expected_meas == actual["measurement"]


def test_reindex_data():
    """Test the reindex_data function."""
    start = datetime.now()
    dates = [start + timedelta(days=i) for i in range(10)]
    expected_dates = dates.copy()

    # Delete some data
    dates.pop(8)
    dates.pop(3)
    dates.pop(2)

    # Only one date will be missing
    expected_dates.pop(3)

    values = list(range(7))
    df = pd.DataFrame({"date": dates, "values": values})
    df = reindex_data(df, "1d")

    assert df.index.tolist() == expected_dates
    assert df["values"].tolist() == [0, 1, "nan", 2, 3, 4, 5, "nan", 6]


def test_get_solar_orbiter_dates():
    """Test the get_solar_orbiter_dates function."""
    so_dates = get_solar_orbiter_dates()
    for dates in so_dates:
        assert len(dates) == 2
        assert all(isinstance(d, date) for d in dates)


def test_get_message_template():
    """Test the get_message_template function."""
    date = "1 January 2026"
    expected_message = (
        "Until 1 January 2026, Solar Orbiter is going through superior conjunction "
        "and will not be transmitting MAG data.\n"
        "Real-time MAG space weather data will continue after this date."
    )
    with patch("os.path.exists") as exists_mock:
        exists_mock.return_value = False
        message = get_message_template(date)
        assert message == expected_message

    # No file exists (default message user)
    with patch("os.path.exists") as exists_mock:
        exists_mock.return_value = True
        # No contents in file (default message used)
        with patch("builtins.open", new_callable=mock_open, read_data=""):
            message = get_message_template(date)
            assert message == expected_message

        # With file contents
        with patch(
            "builtins.open",
            new_callable=mock_open,
            read_data="SO is not in communication until {{ end_date }}.",
        ):
            message = get_message_template(date)
            assert message == "SO is not in communication until 1 January 2026."
