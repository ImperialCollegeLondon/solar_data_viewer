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


@pytest.fixture(scope="session")
def django_db_setup():
    """Forces the use of an existing DB rather than creating a test one.

    See https://pytest-django.readthedocs.io/en/latest/database.html#using-an-existing-external-database-for-tests
    """
    from django.conf import settings

    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": settings.BASE_DIR / "db" / "db.sqlite3",
    }
