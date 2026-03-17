"""Azure-specific settings for solar_data_viewer project."""

import os

from ._production import *  # noqa: F403

ALLOWED_HOSTS = [os.environ["WEBSITE_HOSTNAME"]]
EMAIL_HOST = os.environ["EMAIL_HOST"]
EMAIL_PORT = os.environ["EMAIL_PORT"]
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ["EMAIL_USER"]
EMAIL_HOST_PASSWORD = os.environ["EMAIL_PASSWORD"]
SERVER_EMAIL = os.environ["EMAIL_USER"]
DEFAULT_FROM_EMAIL = os.environ["EMAIL_USER"]
ADMINS = os.environ["ADMIN_EMAILS"].split(",")

DATABASES["imap"] = dict(  # noqa: F405
    ENGINE="django.db.backends.postgresql",
    NAME=os.environ["IMAP_DB_NAME"],
    USER=os.environ["IMAP_DB_USER"],
    PASSWORD=os.environ["IMAP_DB_PASSWORD"],
    HOST=os.environ["IMAP_DB_HOST"],
    PORT=os.environ["IMAP_DB_PORT"],
)

DATABASES["so"] = dict(  # noqa: F405
    ENGINE="django.db.backends.postgresql",
    NAME=os.environ["SO_DB_NAME"],
    USER=os.environ["SO_DB_USER"],
    PASSWORD=os.environ["SO_DB_PASSWORD"],
    HOST=os.environ["SO_DB_HOST"],
    PORT=os.environ["SO_DB_PORT"],
)
