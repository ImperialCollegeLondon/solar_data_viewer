"""Fixtures for use throughout the test suite."""

import os
import subprocess
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
def test_db():
    """Create a test db with the right data tables.

    We use the 'so-db' command to create the database and then to destroy
    it once the tests are done.
    """
    from pathlib import Path

    path = Path(__file__).resolve().parent / "db.sqlite3"

    env = os.environ.copy()
    env["SOLO_SQLALCHEMY_URL"] = f"sqlite:///{path}"
    subprocess.run(
        "so-db create-db --with-schema",
        shell=True,
        env=env,
        capture_output=True,
        check=True,
    )
    yield path
    subprocess.run(
        "so-db drop-db",
        shell=True,
        env=env,
        capture_output=True,
        check=True,
    )


@pytest.fixture(scope="session")
def django_db_setup(test_db):
    """Forces the use of an existing DB rather than creating a test one."""
    from django.conf import settings

    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": test_db,
        "ATOMIC_REQUESTS": False,
    }
