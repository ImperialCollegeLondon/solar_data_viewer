from pathlib import Path

from solar_data_viewer.settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(__file__).resolve().parent / "db.sqlite3",
    }
}
