"""Settings for app deployment in production.

This module contains those settings that are not expected to vary between
deployments. This module is not intended to be used directly but imported into another
module where deployment specific settings are set.
"""

import os

from .settings import *  # noqa: F403

DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]
SECURE_BROWSER_XSS_FILTER = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 15552000
USE_X_FORWARDED_HOST = True
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
