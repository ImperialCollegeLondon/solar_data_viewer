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


# Source - https://stackoverflow.com/a/50849037
# Posted by Randall, modified by community. See post 'Timeline' for change history
# Retrieved 2026-03-04, License - CC BY-SA 4.0


@pytest.fixture(autouse=True, scope="session")
def django_test_environment(django_test_environment):
    """Enable the use of not managed models."""
    from django.apps import apps

    get_models = apps.get_models

    for m in [m for m in get_models() if not m._meta.managed]:
        m._meta.managed = True
