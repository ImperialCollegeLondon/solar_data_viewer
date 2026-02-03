"""Test suite for the utils."""

from main.config import PlotsConfig
from main.utils import load_plot_config


def test_load_plot_config(plots_config):
    """Test the load_plot_config method."""
    config = load_plot_config(plots_config)
    assert isinstance(config, PlotsConfig)
