"""Tests for the Pydantic configuration schemas."""

import pytest
from pydantic import ValidationError

from main.utils import load_plot_config


def test_check_valid_spacecrafts(plots_config):
    """Test the validation for invalid spacecrafts in traces."""
    load_plot_config(plots_config)

    plots_config["plots"][1]["measurements"]["lon_gsm"]["traces"] = {
        "Unknown": "purple"
    }
    with pytest.raises(ValidationError):
        load_plot_config(plots_config)


def test_check_valid_default_spacecraft(plots_config):
    """Test validation of the default spacecraft."""
    load_plot_config(plots_config)

    plots_config["default_spacecraft"] = "Unknown"
    with pytest.raises(ValidationError):
        load_plot_config(plots_config)
