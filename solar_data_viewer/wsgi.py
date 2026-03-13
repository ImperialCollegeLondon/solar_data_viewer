"""WSGI config for solar_data_viewer project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from azure.monitor.opentelemetry import configure_azure_monitor
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "solar_data_viewer.settings")

APP_INSIGHTS_CONNECTION_STRING = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
if APP_INSIGHTS_CONNECTION_STRING:
    # note that this configures a handler on the root logger that forwards all errors
    # messages to the Application Insights workspace configured for the app.
    configure_azure_monitor(connection_string=APP_INSIGHTS_CONNECTION_STRING)


application = get_wsgi_application()
