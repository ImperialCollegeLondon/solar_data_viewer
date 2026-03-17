"""Test suite for the utils."""

import itertools
from contextlib import nullcontext as does_not_raise
from datetime import datetime, timedelta

import pandas as pd
import pytest
from model_bakery import baker

from main.config import PlotsConfig
from main.utils import load_plot_config, reindex_data


def test_load_plot_config(plots_config):
    """Test the load_plot_config method."""
    config = load_plot_config(plots_config)
    assert isinstance(config, PlotsConfig)


@pytest.mark.parametrize(
    "measurement, raises",
    [
        ("bx_gse", does_not_raise()),
        ("by_gse", does_not_raise()),
        ("bz_gse", does_not_raise()),
        ("temperature", pytest.raises(ValueError)),
    ],
)
@pytest.mark.parametrize("days", [1, 3, 7])
@pytest.mark.django_db(databases=["imap"])
def test_get_gse_magnetic_field(measurement, raises, days):
    """Test the get_so_magnetic_field function."""
    import pandas as pd
    from django.utils import timezone

    from main.models import IMAPGSEMagneticField
    from main.utils import get_gse_magnetic_field

    # Prepare the times
    num = days * 24
    now = timezone.now()
    times = pd.date_range(
        start=now - pd.Timedelta(days=10), end=now, freq="h"
    ).to_series()

    # Populate the database
    baker.make(IMAPGSEMagneticField, time=itertools.cycle(times), _quantity=len(times))

    # Find the actual and expected values
    with raises:
        actual = get_gse_magnetic_field("IMAP", measurement, range_param=f"{days}d")
        expected_meas = list(
            IMAPGSEMagneticField.objects.filter(time__in=times[-num:]).values_list(
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
    all_dates = [start + timedelta(days=i) for i in range(10)]
    dates = all_dates.copy()

    # Delete some data
    dates.pop(8)
    dates.pop(3)
    dates.pop(2)

    values = list(range(7))
    df = pd.DataFrame({"date": dates, "values": values})
    df = reindex_data(df, "1d")

    assert df.index.tolist() == all_dates
    assert df["values"].tolist() == [0, 1, "nan", "nan", 2, 3, 4, 5, "nan", 6]
