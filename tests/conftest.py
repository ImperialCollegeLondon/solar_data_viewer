"""Fixtures for use throughout the test suite."""

from pathlib import Path
from tomllib import load
from typing import Any

import pytest


@pytest.fixture
def plots_config() -> dict[str, Any]:  # type: ignore[explicit-any]
    """Read the plots config file."""
    path = Path(__file__).parent.parent / "main" / "config" / "plots.toml"
    with path.open("rb") as f:
        config = load(f)
    return config


@pytest.fixture(autouse=True, scope="session")
def django_test_environment(django_test_environment):
    """Make unmanaged models, managed during tests."""
    from django.apps import apps

    get_models = apps.get_models

    for m in [m for m in get_models() if not m._meta.managed]:
        m._meta.managed = True
