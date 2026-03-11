"""Azure-specific settings for solar_data_viewer project."""

import logging
import os
import sys

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


# Below configuration splits console logging into stdout and stderr (for warnings or
# worse). This helps the Azure AppServiceConsoleLogs mechanism to distinguish between
# error and information messages in the log analytics workspace.
class InfoFilter(logging.Filter):
    """Filter to only pass INFO and DEBUG level log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Return True if the record level is DEBUG or INFO."""
        return record.levelno in (logging.DEBUG, logging.INFO)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {message}", "style": "{"},
    },
    "filters": {
        "info_filter": {
            "()": InfoFilter,
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console_stdout": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stdout,
            "level": "DEBUG",
            "filters": ["info_filter"],
        },
        "console_stderr": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stderr,
            "level": "WARNING",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "root": {"handlers": ["console_stdout", "console_stderr"]},
    "loggers": {
        "django": {
            "handlers": ["mail_admins"],
            "level": "INFO",
        },
    },
}

DATABASES["imap"] = dict(  # noqa: F405
    ENGINE="django.db.backends.postgresql",
    NAME=os.environ["IMAP_DB_NAME"],
    USER=os.environ["IMAP_DB_USER"],
    PASSWORD=os.environ["IMAP_DB_PASSWORD"],
    HOST=os.environ["IMAP_DB_HOST"],
    PORT=os.environ["IMAP_DB_PORT"],
)
