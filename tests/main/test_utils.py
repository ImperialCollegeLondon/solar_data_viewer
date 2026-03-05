"""Test suite for the utils."""

import itertools

import pytest
from model_bakery import baker

from main.config import PlotsConfig
from main.utils import load_plot_config


def test_load_plot_config(plots_config):
    """Test the load_plot_config method."""
    config = load_plot_config(plots_config)
    assert isinstance(config, PlotsConfig)


@pytest.mark.django_db
@pytest.mark.parametrize("measurement", ["B_r", "B_t", "B_n"])
@pytest.mark.parametrize("days", [1, 3, 7])
def test_get_so_magnetic_field(measurement, days):
    """Test the get_so_magnetic_field function."""
    import pandas as pd
    from django.utils import timezone

    from main.models import SOMagneticField
    from main.utils import get_so_magnetic_field

    # Prepare the times
    num = days * 24
    now = timezone.now()
    times = pd.date_range(
        start=now - pd.Timedelta(days=10), end=now, freq="h"
    ).to_series()

    # Populate the database
    baker.make(SOMagneticField, time=itertools.cycle(times), _quantity=len(times))

    # Find the actual and expected values
    actual = get_so_magnetic_field(measurement, range_param=f"{days}d")
    expected_meas = list(
        SOMagneticField.objects.filter(time__in=times[-num:]).values_list(
            measurement, flat=True
        )
    )
    expected_dates = (times[-num:].astype("int64") // 10**6).to_list()

    assert list(actual.keys()) == ["measurement", "date"]
    assert len(actual["measurement"]) == num
    assert len(actual["date"]) == num
    assert expected_dates == actual["date"]
    assert expected_meas == actual["measurement"]
